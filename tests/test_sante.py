"""Socle 0.9.0 : santé des tâches de fond (registre maison.Taches, contrat /health) et copie cohérente des bases
SQLite (maison.copier_bases, planifier_copie). Données inventées, aucune base réelle."""
import asyncio
import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import main, maison
from app.config import Config


class Horloge:
    def __init__(self, t=1_800_000_000.0):
        self.t = t

    def __call__(self):
        return self.t

    def avance(self, s):
        self.t += s


@pytest.fixture()
def h():
    return Horloge()


@pytest.fixture()
def registre(h):
    return maison.Taches(horloge=h)


@pytest.fixture(autouse=True)
def copie_neuve():
    """La dernière copie est un état du module : remise à zéro autour de chaque test."""
    maison._COPIE.update(dossier=None, dernier=None)
    yield
    maison._COPIE.update(dossier=None, dernier=None)


def etat(reg, nom, **kw):
    return next(t for t in reg.etat(**kw) if t["nom"] == nom)


# ================================================================ états d'une tâche régulière

def test_jamais_puis_en_retard_sans_aucun_tour(registre, h):
    registre.declarer("synchro-icloud", periode_s=3600)
    assert etat(registre, "synchro-icloud")["etat"] == "jamais"
    h.avance(3600 + 599)
    assert etat(registre, "synchro-icloud")["etat"] == "jamais"
    h.avance(2)
    assert etat(registre, "synchro-icloud")["etat"] == "en_retard"


def test_ok_puis_en_retard_apres_deux_periodes_et_dix_minutes(registre, h):
    registre.declarer("synchro-icloud", periode_s=3600)
    with registre.tour("synchro-icloud"):
        h.avance(5)
    e = etat(registre, "synchro-icloud")
    assert e["etat"] == "ok" and e["derniere_reussite"] and e["derniere_erreur"] is None
    assert e["type"] == "reguliere" and e["periode_s"] == 3600
    h.avance(2 * 3600 + 600 - 1)
    assert etat(registre, "synchro-icloud")["etat"] == "ok"
    h.avance(2)
    assert etat(registre, "synchro-icloud")["etat"] == "en_retard"


def test_erreur_d_une_reguliere_donne_en_retard_une_fois_la_marge_passee(registre, h):
    registre.declarer("collecte", periode_s=300)
    with pytest.raises(RuntimeError), registre.tour("collecte"):
        raise RuntimeError("service muet")
    # pas encore de réussite, mais un tour a fini : plus « jamais », directement « en retard »
    e = etat(registre, "collecte")
    assert e["etat"] == "en_retard" and e["derniere_erreur"] and e["dernier_essai"]
    with registre.tour("collecte"):
        pass
    assert etat(registre, "collecte")["etat"] == "ok"
    with pytest.raises(RuntimeError), registre.tour("collecte"):
        raise RuntimeError("service muet")
    assert etat(registre, "collecte")["etat"] == "ok"           # une erreur isolée ne suffit pas
    h.avance(2 * 300 + 601)
    assert etat(registre, "collecte")["etat"] == "en_retard"


def test_bloquee_si_un_tour_dure_plus_que_sa_periode(registre, h):
    registre.declarer("synchro-icloud", periode_s=3600)
    with registre.tour("synchro-icloud"):
        pass
    with registre.tour("synchro-icloud"):
        h.avance(3601)
        assert etat(registre, "synchro-icloud")["etat"] == "bloquee"
    assert etat(registre, "synchro-icloud")["etat"] == "ok"


def test_bloquee_plafonnee_a_deux_heures(registre, h):
    registre.declarer("copie-des-bases", periode_s=86400)
    with registre.tour("copie-des-bases"):
        h.avance(7199)
        assert etat(registre, "copie-des-bases")["etat"] != "bloquee"
        h.avance(2)
        assert etat(registre, "copie-des-bases")["etat"] == "bloquee"


def test_tour_async(registre, h):
    registre.declarer("veille", periode_s=60)

    async def boucle():
        async with registre.tour_async("veille"):
            await asyncio.sleep(0)
        with pytest.raises(ValueError):
            async with registre.tour_async("veille"):
                raise ValueError("mauvaise réponse")

    asyncio.run(boucle())
    e = etat(registre, "veille", avec_messages=True)
    assert e["derniere_reussite"] and e["derniere_erreur"]
    assert e["message"] == "ValueError: mauvaise réponse"


def test_annulation_n_est_pas_une_erreur(registre, h):
    registre.declarer("veille", periode_s=60)

    async def boucle():
        async with registre.tour_async("veille"):
            await asyncio.sleep(10)

    async def lancer():
        tache = asyncio.create_task(boucle())
        await asyncio.sleep(0)
        tache.cancel()
        with pytest.raises(asyncio.CancelledError):
            await tache

    asyncio.run(lancer())
    e = etat(registre, "veille")
    assert e["derniere_erreur"] is None and e["etat"] == "jamais"


# ================================================================ tâches à la demande

def test_demande_ok_erreur_jamais_sans_jamais_d_orange(registre, h):
    registre.declarer("import", type="demande")
    e = etat(registre, "import")
    assert e["etat"] == "jamais" and e["type"] == "demande" and e["periode_s"] is None
    h.avance(10 * 86400)
    assert etat(registre, "import")["etat"] == "jamais"
    with pytest.raises(OSError), registre.tour("import"):
        raise OSError("fichier illisible")
    assert etat(registre, "import")["etat"] == "erreur"
    h.avance(30 * 86400)
    assert etat(registre, "import")["etat"] == "erreur"         # jamais « en_retard »
    with registre.tour("import"):
        pass
    assert etat(registre, "import")["etat"] == "ok"


def test_tache_non_declaree_suivie_comme_demande(registre):
    with registre.tour("fabrication"):
        pass
    assert etat(registre, "fabrication")["type"] == "demande"


def test_declaration_mal_formee_refusee(registre):
    with pytest.raises(ValueError):
        registre.declarer("boucle")                  # régulière sans période
    with pytest.raises(ValueError):
        registre.declarer("boucle", 60, type="autre")


def test_format_du_contrat(registre):
    registre.declarer("synchro-icloud", periode_s=3600)
    e = registre.etat()[0]
    assert set(e) == {"nom", "type", "periode_s", "etat", "derniere_reussite", "dernier_essai", "derniere_erreur"}
    assert set(registre.etat(avec_messages=True)[0]) == set(e) | {"message"}
    json.dumps(registre.etat(avec_messages=True))


# ================================================================ messages : secrets masqués, 160 caractères

@pytest.mark.parametrize("texte, interdit", [
    ("échec https://alice:motdepasse-invente@exemple.invalid/dav/ refusé", "motdepasse-invente"),
    ("échec https://jeton-invente-123@exemple.invalid/api", "jeton-invente-123"),
    ("GET /api?token=abc123invente&page=2 : 401", "abc123invente"),
    ("en-tête Authorization: Bearer eyJinventeXYZ rejeté", "eyJinventeXYZ"),
    ("api_key=cle-inventee-42 refusée", "cle-inventee-42"),
    ("password: secret-invente", "secret-invente"),
])
def test_filtre_des_secrets(texte, interdit):
    m = maison.message_erreur(RuntimeError(texte))
    assert interdit not in m and "…" in m and m.startswith("RuntimeError: ")


def test_filtre_laisse_un_message_ordinaire():
    assert maison.masquer_secrets("délai dépassé vers http://carnet:8091/health") == \
        "délai dépassé vers http://carnet:8091/health"


def test_message_premiere_ligne_et_160_caracteres(registre):
    registre.declarer("collecte", periode_s=60)
    with pytest.raises(RuntimeError), registre.tour("collecte"):
        raise RuntimeError("x" * 500 + "\nseconde ligne cachée")
    m = etat(registre, "collecte", avec_messages=True)["message"]
    assert len(m) <= 160 and "seconde" not in m and m.startswith("RuntimeError: xxx")


def test_secret_masque_avant_la_coupure():
    # le secret est à cheval sur la limite : il ne doit pas en rester un bout
    m = maison.message_erreur(RuntimeError("a" * 140 + " token=ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    assert "ABCDEFGH" not in m


# ================================================================ /health : messages seulement avec le jeton

def requete(entetes=None):
    return SimpleNamespace(headers=entetes or {})


def test_sante_sans_jeton_sans_messages(monkeypatch):
    monkeypatch.setattr(maison, "TACHES", maison.Taches())
    maison.TACHES.declarer("synchro-icloud", 3600)
    with pytest.raises(RuntimeError), maison.TACHES.tour("synchro-icloud"):
        raise RuntimeError("refus du serveur")
    s = maison.sante(requete(), jeton_commun=("jeton-commun-invente",))
    assert s["version_socle"] == "0.10.0" and s["copie_base"] is None
    assert "message" not in s["taches"][0] and s["taches"][0]["derniere_erreur"]
    faux = maison.sante(requete({"authorization": "Bearer autre-jeton"}), jeton_commun=("jeton-commun-invente",))
    assert "message" not in faux["taches"][0]
    bon = maison.sante(requete({"authorization": "Bearer jeton-commun-invente"}), jeton_commun=("jeton-commun-invente",))
    assert bon["taches"][0]["message"] == "RuntimeError: refus du serveur"
    assert "message" in maison.sante(requete(), jeton_commun=(), session_ok=True)["taches"][0]
    assert "message" not in maison.sante(requete({"authorization": "Bearer "}), jeton_commun=())["taches"][0]


def test_sante_lit_le_jeton_commun_de_la_stack(monkeypatch):
    monkeypatch.setattr(maison, "TACHES", maison.Taches())
    maison.TACHES.declarer("boucle", 60)
    monkeypatch.setenv("MAISON_JETON", "jeton-de-stack-invente")
    assert "message" in maison.sante(requete({"Authorization": "Bearer jeton-de-stack-invente"}))["taches"][0]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("MAISON_JETON", "jeton-commun-invente")
    monkeypatch.setattr(maison, "TACHES", maison.Taches())
    maison.TACHES.declarer("demo", 60)
    with pytest.raises(RuntimeError), maison.TACHES.tour("demo"):
        raise RuntimeError("panne inventée")
    main.ETAT.clear()
    main.ETAT["cfg"] = Config(password="mot-de-passe-de-test", data=tmp_path, static=tmp_path / "static",
                              attente_connexion=False)
    with TestClient(main.app) as c:
        yield c
    main.ETAT.clear()


def test_health_du_socle(client):
    s = client.get("/health").json()
    assert s["ok"] is True and s["version"] and s["version_socle"] == "0.10.0" and s["copie_base"] is None
    assert s["taches"][0]["nom"] == "demo" and "message" not in s["taches"][0]
    avec = client.get("/health", headers={"Authorization": "Bearer jeton-commun-invente"}).json()
    assert avec["taches"][0]["message"] == "RuntimeError: panne inventée"
    client.post("/api/connexion", json={"mot_de_passe": "mot-de-passe-de-test"})
    assert "message" in client.get("/health").json()["taches"][0]


# ================================================================ copie cohérente des bases

def creer_base(chemin, lignes=100, wal=True):
    c = sqlite3.connect(chemin)
    if wal:
        c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE contacts (id INTEGER PRIMARY KEY, nom TEXT, groupe INTEGER)")
    c.executemany("INSERT INTO contacts (nom, groupe) VALUES (?, ?)", [(f"Personne {i}", i % 7) for i in range(lignes)])
    c.commit()
    c.close()


def test_copie_simple_et_copie_json(tmp_path):
    base = tmp_path / "donnees" / "carnet2.db"
    base.parent.mkdir()
    creer_base(base)
    autre = tmp_path / "donnees" / "journal.db"
    creer_base(autre, 10, wal=False)
    copies = tmp_path / "donnees" / "copies"
    r = maison.copier_bases([base, autre], copies)
    assert r["ok"] is True and r["bases"] == ["carnet2.db", "journal.db"] and r["le"]
    final = copies / "carnet2-derniere.db"
    assert r["taille"] == final.stat().st_size + (copies / "journal-derniere.db").stat().st_size
    assert sorted(p.name for p in copies.iterdir()) == ["carnet2-derniere.db", "copie.json", "journal-derniere.db"]
    c = sqlite3.connect(final)
    assert c.execute("SELECT count(*) FROM contacts").fetchone()[0] == 100
    assert c.execute("PRAGMA journal_mode").fetchone()[0] == "delete"      # un seul fichier, prêt à remettre
    c.close()
    assert json.loads((copies / "copie.json").read_text()) == r == maison.copie_base_etat()
    # une seconde nuit écrase la copie (une seule par base)
    maison.copier_bases([base, autre], copies)
    assert len(list(copies.glob("carnet2-*"))) == 1


def test_copie_coherente_pendant_une_ecriture(tmp_path):
    """Un écrivain ajoute des lots de 50 lignes dans une transaction ; chaque copie doit tomber entre deux lots
    (multiple de 50) et passer l'intégrité."""
    base = tmp_path / "carnet2.db"
    creer_base(base, 0)
    stop = threading.Event()
    erreurs = []

    def ecrivain():
        c = sqlite3.connect(base, timeout=30)
        try:
            while not stop.is_set():
                with c:
                    for i in range(50):
                        c.execute("INSERT INTO contacts (nom, groupe) VALUES (?, ?)", ("x" * 200, i))
        except Exception as exc:                                  # noqa: BLE001
            erreurs.append(exc)
        finally:
            c.close()

    fil = threading.Thread(target=ecrivain)
    fil.start()
    try:
        vus = []
        for _ in range(15):
            time.sleep(0.01)
            r = maison.copier_bases([base], tmp_path / "copies")
            assert r["ok"]
            c = sqlite3.connect(tmp_path / "copies" / "carnet2-derniere.db")
            vus.append(c.execute("SELECT count(*) FROM contacts").fetchone()[0])
            assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            c.close()
    finally:
        stop.set()
        fil.join()
    assert not erreurs
    assert all(n % 50 == 0 for n in vus) and max(vus) > 0


def test_integrite_ratee_copie_effacee(tmp_path, monkeypatch):
    base = tmp_path / "carnet2.db"
    creer_base(base)
    copies = tmp_path / "copies"
    bonne = maison.copier_bases([base], copies)
    avant = (copies / "carnet2-derniere.db").read_bytes()

    vrai_connect = sqlite3.connect

    class VerifAbimee:
        def __init__(self, c):
            self.c = c

        def execute(self, sql, *a):
            if "integrity_check" in sql:
                return self.c.execute("SELECT 'row 3 missing from index'")
            return self.c.execute(sql, *a)

        def close(self):
            self.c.close()

    # le partiel est ouvert deux fois : pour recevoir la copie (backup veut une vraie connexion) puis pour vérifier
    appels = {"n": 0}

    def connect_seconde(chemin, *a, **kw):
        if str(chemin).endswith(".partiel"):
            appels["n"] += 1
            if appels["n"] == 2:
                return VerifAbimee(vrai_connect(chemin, *a, **kw))
        return vrai_connect(chemin, *a, **kw)

    monkeypatch.setattr(maison.sqlite3, "connect", connect_seconde)
    with pytest.raises(sqlite3.DatabaseError, match="abîmée"):
        maison.copier_bases([base], copies)
    monkeypatch.setattr(maison.sqlite3, "connect", vrai_connect)
    assert not list(copies.glob("*.partiel"))                       # copie ratée effacée
    assert (copies / "carnet2-derniere.db").read_bytes() == avant   # la bonne copie d'avant reste
    e = maison.copie_base_etat()
    assert e["ok"] is False and e["bases"] == ["carnet2.db"] and e["le"] >= bonne["le"]
    assert json.loads((copies / "copie.json").read_text())["ok"] is False


def test_base_absente_aucune_base_vide_creee(tmp_path):
    with pytest.raises(FileNotFoundError):
        maison.copier_bases([tmp_path / "disparue.db"], tmp_path / "copies")
    assert not (tmp_path / "disparue.db").exists()
    assert maison.copie_base_etat()["ok"] is False


def test_toutes_les_bases_ou_aucune(tmp_path):
    a, b = tmp_path / "a.db", tmp_path / "b.db"
    creer_base(a)
    creer_base(b)
    maison.copier_bases([a, b], tmp_path / "copies")
    avant = (tmp_path / "copies" / "a-derniere.db").stat().st_mtime_ns
    b.unlink()
    with pytest.raises(FileNotFoundError):
        maison.copier_bases([a, b], tmp_path / "copies")
    assert (tmp_path / "copies" / "a-derniere.db").stat().st_mtime_ns == avant
    assert not list((tmp_path / "copies").glob("*.partiel"))


def test_copie_relue_apres_redemarrage(tmp_path):
    base = tmp_path / "carnet2.db"
    creer_base(base)
    r = maison.copier_bases([base], tmp_path / "copies")
    maison._COPIE.update(dossier=None, dernier=None)                 # « redémarrage »
    assert maison.copie_base_etat() is None                          # appli sans copie prévue : null
    maison._charger_copie(tmp_path / "copies", ["carnet2.db"])
    assert maison.copie_base_etat() == r
    maison._charger_copie(tmp_path / "rien", ["carnet2.db"])
    assert maison.copie_base_etat() == {"le": None, "ok": False, "bases": ["carnet2.db"], "taille": 0}


# ================================================================ heure de Paris, quel que soit TZ

@pytest.fixture()
def tz_utc(monkeypatch):
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.parametrize("paris", ["zoneinfo", None])
def test_heure_de_paris_avec_tz_utc(tz_utc, paris):
    zone = maison.PARIS if paris == "zoneinfo" else None
    if paris == "zoneinfo" and zone is None:
        pytest.skip("pas de données de fuseau ici")
    u = lambda *a: datetime(*a, tzinfo=timezone.utc)      # noqa: E731
    # hiver : 01:00 à Paris = 00:00 UTC
    assert maison.prochaine_copie("01:00", u(2026, 11, 18, 12, 0), paris=zone) == u(2026, 11, 19, 0, 0)
    assert maison.prochaine_copie("01:00", u(2026, 11, 18, 23, 59), paris=zone) == u(2026, 11, 19, 0, 0)
    assert maison.prochaine_copie("01:00", u(2026, 11, 19, 0, 0), paris=zone) == u(2026, 11, 20, 0, 0)
    # été : 01:30 à Paris = 23:30 UTC la veille
    assert maison.prochaine_copie("01:30", u(2026, 7, 1, 12, 0), paris=zone) == u(2026, 7, 1, 23, 30)
    assert maison.prochaine_copie("01:30", u(2026, 7, 1, 23, 45), paris=zone) == u(2026, 7, 2, 23, 30)
    # nuit du passage à l'heure d'été (28/03/2027) : 02:00 n'existe pas, la copie se fait à 03:00 (01:00 UTC)
    assert maison.prochaine_copie("02:00", u(2027, 3, 27, 12, 0), paris=zone) == u(2027, 3, 28, 1, 0)
    # nuit du retour à l'heure d'hiver (31/10/2027) : 01:00 encore en heure d'été
    assert maison.prochaine_copie("01:00", u(2027, 10, 30, 12, 0), paris=zone) == u(2027, 10, 30, 23, 0)
    assert maison.prochaine_copie("01:00", u(2027, 10, 31, 12, 0), paris=zone) == u(2027, 11, 1, 0, 0)


def test_heures_etalees():
    heures = list(maison.HEURES_COPIE.values())
    assert len(set(heures)) == len(heures) == 9
    assert all("01:00" <= x <= "02:50" for x in heures) and maison.HEURES_COPIE["carnet"] == "01:00"


def test_planifier_copie_dans_un_fil_sous_la_tache(tmp_path, monkeypatch):
    base = tmp_path / "carnet2.db"
    creer_base(base)
    monkeypatch.setattr(maison, "TACHES", maison.Taches())
    fils = []
    vraie_copie = maison.copier_bases

    def copie_espionne(chemins, dossier, ouvrir=None):
        fils.append(threading.current_thread() is threading.main_thread())
        return vraie_copie(chemins, dossier, ouvrir)

    monkeypatch.setattr(maison, "copier_bases", copie_espionne)
    async def dormir(s):
        raise AssertionError("ne doit pas attendre")

    # cible dans le passé immédiat : la boucle n'attend pas et copie tout de suite
    monkeypatch.setattr(maison, "prochaine_copie", lambda heure: datetime.now(timezone.utc))
    asyncio.run(maison.planifier_copie("carnet", [base], tmp_path / "copies", dormir=dormir, tours=1))
    assert fils == [False]                                         # jamais dans la boucle du serveur
    e = etat(maison.TACHES, "copie-des-bases")
    assert e["type"] == "reguliere" and e["periode_s"] == 86400 and e["etat"] == "ok"
    assert maison.copie_base_etat()["ok"] is True
    assert (tmp_path / "copies" / "carnet2-derniere.db").is_file()


def test_planifier_copie_attend_par_morceaux_et_survit_a_une_erreur(tmp_path, monkeypatch):
    monkeypatch.setattr(maison, "TACHES", maison.Taches())
    attentes = []
    debut = datetime.now(timezone.utc).timestamp()

    # l'attente « avance » l'horloge : on remplace datetime.now dans le module par une horloge qui suit les attentes
    temps = {"t": debut}

    class Dt(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromtimestamp(temps["t"], tz)

    async def dormir_avance(s):
        attentes.append(round(s))
        temps["t"] += s

    monkeypatch.setattr(maison, "datetime", Dt)
    def prochaine(heure):
        assert heure == "01:00"                                    # HEURES_COPIE["carnet"]
        return datetime.fromtimestamp(debut + 3 * 3600 + 5, timezone.utc)

    monkeypatch.setattr(maison, "prochaine_copie", prochaine)
    asyncio.run(maison.planifier_copie("carnet", [tmp_path / "absente.db"], tmp_path / "copies",
                                       dormir=dormir_avance, tours=1))
    assert attentes == [3600, 3600, 3600, 5]
    e = etat(maison.TACHES, "copie-des-bases", avec_messages=True)
    assert e["derniere_erreur"] and "FileNotFoundError" in e["message"]
    assert maison.copie_base_etat()["ok"] is False


def test_copie_avec_ouverture_propre_a_l_appli(tmp_path):
    """0.9.1 : une appli à base chiffrée passe sa propre ouverture ; elle sert à lire, écrire et vérifier la copie."""
    base = tmp_path / "chiffree.db"
    cx = sqlite3.connect(base); cx.execute("CREATE TABLE t(x)"); cx.execute("INSERT INTO t VALUES (1)"); cx.commit(); cx.close()
    appels = []

    def ouvrir(chemin, lecture_seule):
        appels.append((Path(chemin).name, lecture_seule))
        return sqlite3.connect(chemin)

    r = maison.copier_bases([base], tmp_path / "copies", ouvrir)
    assert r["ok"] is True
    assert ("chiffree.db", True) in appels and any(n.endswith(".partiel") and not ro for n, ro in appels)
    assert sqlite3.connect(tmp_path / "copies" / "chiffree-derniere.db").execute("SELECT x FROM t").fetchall() == [(1,)]

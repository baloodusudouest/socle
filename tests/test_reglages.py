"""0.6.0 : mot de passe commun seul, réglages dans l'appli, sauvegarde pour l'Anneau, restauration.

Aucun réseau : l'Anneau est remplacé par un faux (argument « lire » de maison.lire_sauvegarde, via ETAT).
"""
import dataclasses
import json
import urllib.error

import pytest
from fastapi.testclient import TestClient

from app import __version__, main
from app.config import Config, charger

MOT_DE_PASSE = "mot-de-passe-de-test"
JETON = "jeton-commun-de-test"


class FauxAnneau:
    """Imite GET /externe/sauvegardes/socle[?le=…] de l'Anneau ; relève chaque demande."""

    def __init__(self):
        self.demandes = []
        self.sauvegardes = {
            "2026-11-15": {"le": "2026-11-15", "version": "0.6.0",
                           "reglages": {"message_accueil": "Bonjour d'hier", "afficher_mesures": False,
                                        "jeton_glisse": "ne doit jamais entrer", "ancien_reglage": 4}},
            "2026-11-14": {"le": "2026-11-14", "version": "0.6.0",
                           "reglages": {"message_accueil": "", "afficher_mesures": "pas un oui/non"}},
        }
        self.panne = None

    def __call__(self, adresse, jeton):
        self.demandes.append((adresse, jeton))
        if self.panne:
            raise self.panne
        if "?le=" not in adresse:
            return {"dates": sorted(self.sauvegardes, reverse=True)}
        le = adresse.split("?le=")[1]
        if le not in self.sauvegardes:
            raise urllib.error.HTTPError(adresse, 404, "Not Found", {}, None)
        return self.sauvegardes[le]


@pytest.fixture()
def env(monkeypatch):
    for v in ("APP_MESSAGE_ACCUEIL", "MAISON_JETON", "MAISON_JETON_ANCIEN", "MAISON_ANNEAU_URL"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("MAISON_JETON", JETON)
    return monkeypatch


def demarrer(dossier, anneau=None):
    main.ETAT.clear()
    main.ETAT["cfg"] = Config(password=MOT_DE_PASSE, data=dossier, static=dossier / "static", attente_connexion=False)
    main.ETAT["lire_anneau"] = anneau
    return TestClient(main.app)


@pytest.fixture()
def anneau():
    return FauxAnneau()


@pytest.fixture()
def client(tmp_path, env, anneau):
    with demarrer(tmp_path, anneau) as c:
        assert c.post("/api/connexion", json={"mot_de_passe": MOT_DE_PASSE}).status_code == 200
        yield c
    main.ETAT.clear()


# ================================================================ mot de passe commun seul

def test_mot_de_passe_commun_seul(monkeypatch, tmp_path):
    monkeypatch.setenv("APP_DATA", str(tmp_path))
    monkeypatch.delenv("MAISON_PASSWORD", raising=False)
    monkeypatch.setenv("APP_PASSWORD", "ancien-mot-de-passe-long")       # l'ancien nom ne suffit plus
    with pytest.raises(SystemExit, match="MAISON_PASSWORD est absent ou trop court"):
        charger()
    monkeypatch.setenv("MAISON_PASSWORD", "court")
    with pytest.raises(SystemExit):
        charger()
    monkeypatch.setenv("MAISON_PASSWORD", "mot-de-passe-commun")
    assert charger().password == "mot-de-passe-commun"


def test_lecture_seule_forcee_par_l_appli(monkeypatch, tmp_path):
    monkeypatch.setenv("MAISON_PASSWORD", "mot-de-passe-commun")
    monkeypatch.setenv("MAISON_LECTURE_SEULE", "oui")
    monkeypatch.delenv("APP_LECTURE_SEULE", raising=False)
    c = charger()
    assert c.lecture_seule and c.origine_lecture_seule == "maison"
    monkeypatch.setenv("APP_LECTURE_SEULE", "non")
    assert not charger().lecture_seule
    monkeypatch.setenv("MAISON_LECTURE_SEULE", "")
    monkeypatch.setenv("APP_LECTURE_SEULE", "oui")
    assert charger().origine_lecture_seule == "appli"


# ================================================================ réglages

def test_reglages_defauts_et_session(client):
    assert client.get("/api/reglages").json() == {"reglages": {"message_accueil": "", "afficher_mesures": True}}
    assert client.get("/api/session").json()["origine_lecture_seule"] == ""


def test_reglages_fermes_sans_session(tmp_path, env):
    with demarrer(tmp_path) as c:
        assert c.get("/api/reglages").status_code == 401
        assert c.put("/api/reglages", json={"message_accueil": "x"}).status_code == 401
        assert c.get("/api/restaurer").status_code == 401
        assert c.post("/api/restaurer", json={"le": "2026-11-15"}).status_code == 401


def test_reprise_de_la_variable_au_premier_demarrage_puis_ignoree(tmp_path, env, caplog):
    env.setenv("APP_MESSAGE_ACCUEIL", "Repris de la stack")
    with demarrer(tmp_path) as c:
        c.post("/api/connexion", json={"mot_de_passe": MOT_DE_PASSE})
        assert c.get("/api/reglages").json()["reglages"]["message_accueil"] == "Repris de la stack"
    journal = caplog.text
    assert "message_accueil" in journal and "APP_MESSAGE_ACCUEIL" in journal
    assert "Repris de la stack" not in journal                                 # le nom au journal, pas la valeur
    env.setenv("APP_MESSAGE_ACCUEIL", "Changé dans la stack depuis")           # second démarrage : plus lue
    caplog.clear()
    with demarrer(tmp_path) as c:
        c.post("/api/connexion", json={"mot_de_passe": MOT_DE_PASSE})
        assert c.get("/api/reglages").json()["reglages"]["message_accueil"] == "Repris de la stack"
    assert "APP_MESSAGE_ACCUEIL" not in caplog.text
    main.ETAT.clear()


def test_put_reglages(client, tmp_path):
    r = client.put("/api/reglages", json={"message_accueil": "Salut", "afficher_mesures": False, "inconnu": 1})
    assert r.status_code == 200
    assert r.json()["reglages"] == {"message_accueil": "Salut", "afficher_mesures": False}
    assert json.loads((tmp_path / "reglages.json").read_text()) == r.json()["reglages"]
    assert r.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("corps", [{"afficher_mesures": "oui"}, {"afficher_mesures": 1},
                                   {"message_accueil": {"a": 1}}, ["pas", "un", "dict"]])
def test_put_reglages_mauvais_type(client, corps):
    r = client.put("/api/reglages", json=corps)
    assert r.status_code == 400 and r.json()["detail"]
    assert client.get("/api/reglages").json()["reglages"] == {"message_accueil": "", "afficher_mesures": True}


def test_reglages_permis_en_lecture_seule(client):
    main.ETAT["cfg"] = dataclasses.replace(main.ETAT["cfg"], lecture_seule=True)
    assert client.put("/api/reglages", json={"afficher_mesures": False}).status_code == 200
    assert client.post("/api/restaurer", json={"le": "2026-11-15"}).status_code == 200


# ================================================================ /externe/sauvegarde

def test_sauvegarde_jeton_requis(client):
    client.cookies.clear()
    assert client.get("/externe/sauvegarde").status_code == 401
    assert client.get("/externe/sauvegarde", headers={"Authorization": "Bearer faux"}).status_code == 401
    r = client.get("/externe/sauvegarde", headers={"Authorization": f"Bearer {JETON}"})
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    assert client.get("/externe/sauvegarde", headers={"X-Maison-Jeton": JETON}).status_code == 200


def test_sauvegarde_session_ne_suffit_pas(client):
    assert client.get("/externe/sauvegarde").status_code == 401           # connecté, mais sans jeton


def test_sauvegarde_porte_fermee_sans_jeton_commun(client, env):
    env.setenv("MAISON_JETON", "")
    assert client.get("/externe/sauvegarde", headers={"Authorization": "Bearer "}).status_code == 404
    assert client.get("/externe/sauvegarde", headers={"Authorization": f"Bearer {JETON}"}).status_code == 404


def test_sauvegarde_ancien_jeton_pendant_un_changement(client, env):
    env.setenv("MAISON_JETON", "jeton-neuf")
    env.setenv("MAISON_JETON_ANCIEN", JETON)
    assert client.get("/externe/sauvegarde", headers={"Authorization": f"Bearer {JETON}"}).status_code == 200


def test_sauvegarde_contenu(client, env, monkeypatch):
    env.setenv("MAISON_PASSWORD", "valeur-secrete-de-la-stack")
    monkeypatch.setattr(main, "EXCLUS_SAUVEGARDE", ("afficher_mesures",))
    client.put("/api/reglages", json={"message_accueil": "Bonjour"})
    s = client.get("/externe/sauvegarde", headers={"Authorization": f"Bearer {JETON}"}).json()
    assert s["contrat"] == 1 and s["appli"] == "socle" and s["version"] == __version__
    assert s["reglages"] == {"message_accueil": "Bonjour"}                  # clé exclue absente
    texte = json.dumps(s)
    for interdit in (JETON, MOT_DE_PASSE, "valeur-secrete-de-la-stack", "/tmp", "static"):
        assert interdit not in texte


def test_sauvegarde_sans_exclusion_rend_tous_les_reglages(client):
    s = client.get("/externe/sauvegarde", headers={"Authorization": f"Bearer {JETON}"}).json()
    assert set(s["reglages"]) == set(main.REGLAGES_DEFAUTS)
    assert set(s) == {"contrat", "appli", "version", "le", "reglages"}


# ================================================================ restaurer

def test_restaurer_liste_des_dates(client, anneau):
    r = client.get("/api/restaurer")
    assert r.status_code == 200 and r.json() == {"dates": ["2026-11-15", "2026-11-14"]}
    assert anneau.demandes == [("http://anneau:8094/externe/sauvegardes/socle", JETON)]


def test_restaurer_differences(client):
    r = client.get("/api/restaurer", params={"le": "2026-11-15"})
    assert r.status_code == 200
    assert r.json() == {"le": "2026-11-15", "version": "0.6.0", "differences": [
        {"cle": "afficher_mesures", "actuel": True, "sauve": False},
        {"cle": "message_accueil", "actuel": "", "sauve": "Bonjour d'hier"}]}     # ni secret ni clé disparue


def test_restaurer_applique(client, tmp_path, caplog):
    r = client.post("/api/restaurer", json={"le": "2026-11-15"})
    assert r.status_code == 200
    assert r.json()["reglages"] == {"message_accueil": "Bonjour d'hier", "afficher_mesures": False}
    assert sorted(r.json()["appliques"]) == ["afficher_mesures", "message_accueil"] and r.json()["ignores"] == []
    assert json.loads((tmp_path / "reglages.json").read_text()) == r.json()["reglages"]
    assert "jeton_glisse" not in (tmp_path / "reglages.json").read_text()
    assert "restaurés depuis la sauvegarde du 2026-11-15" in caplog.text
    assert client.get("/api/restaurer", params={"le": "2026-11-15"}).json()["differences"] == []


def test_restaurer_ignore_une_valeur_de_mauvais_type(client):
    client.put("/api/reglages", json={"message_accueil": "Aujourd'hui"})
    r = client.post("/api/restaurer", json={"le": "2026-11-14"}).json()
    assert r["appliques"] == ["message_accueil"] and r["ignores"] == ["afficher_mesures"]
    assert r["reglages"] == {"message_accueil": "", "afficher_mesures": True}


def test_restaurer_date_inconnue_ou_mal_ecrite(client):
    r = client.get("/api/restaurer", params={"le": "2026-01-01"})
    assert r.status_code == 404 and "aucune sauvegarde" in r.json()["detail"]
    assert client.post("/api/restaurer", json={"le": "2026-01-01"}).status_code == 404
    assert client.get("/api/restaurer", params={"le": "hier"}).status_code == 400
    assert client.post("/api/restaurer", json={}).status_code == 400


def test_restaurer_anneau_injoignable(client, anneau):
    anneau.panne = urllib.error.URLError("refusé")
    for r in (client.get("/api/restaurer"), client.get("/api/restaurer", params={"le": "2026-11-15"}),
              client.post("/api/restaurer", json={"le": "2026-11-15"})):
        assert r.status_code == 503 and "L'Anneau ne répond pas" in r.json()["detail"]
    assert client.get("/api/reglages").json()["reglages"]["afficher_mesures"] is True    # rien n'a bougé


def test_restaurer_rien_chez_l_anneau(client, anneau):
    anneau.sauvegardes = {}
    assert client.get("/api/restaurer").json() == {"dates": []}
    anneau.panne = urllib.error.HTTPError("x", 404, "Not Found", {}, None)              # appli jamais sauvegardée
    assert client.get("/api/restaurer").status_code == 404


def test_restaurer_anneau_reel_injoignable_sans_faux(client, env):
    """Sans faux Anneau : vraie demande HTTP vers une adresse qui ne répond pas → 503, pas d'erreur 500."""
    env.setenv("MAISON_ANNEAU_URL", "http://127.0.0.1:9")
    main.ETAT["lire_anneau"] = None
    assert client.get("/api/restaurer").status_code == 503

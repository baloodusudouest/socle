"""Module commun maison : contrat 1 (variables communes, jeton commun, lecture seule, annuaire) et contrat 2
(réglages d'usage, sauvegarde et restauration). Le module se copie tel quel dans chaque appli : ces tests sont la
référence de son comportement."""
import json

import pytest

from app import maison


def test_copie_non_retouchee():
    assert maison.empreinte_ecrite() and maison.empreinte_calculee() == maison.empreinte_ecrite()


def test_mot_de_passe_commun_puis_ancien(monkeypatch):
    monkeypatch.delenv("MAISON_PASSWORD", raising=False)
    monkeypatch.setenv("APPLI_PASSWORD", "ancien-mot-de-passe")
    assert maison.mot_de_passe("APPLI_PASSWORD") == "ancien-mot-de-passe"
    monkeypatch.setenv("MAISON_PASSWORD", "nouveau-mot-de-passe")
    assert maison.mot_de_passe("APPLI_PASSWORD") == "nouveau-mot-de-passe"
    monkeypatch.delenv("MAISON_PASSWORD")
    monkeypatch.delenv("APPLI_PASSWORD")
    assert maison.mot_de_passe("APPLI_PASSWORD") == ""


def test_lecture_seule_maison_et_forcage_par_appli(monkeypatch):
    for v in ("MAISON_LECTURE_SEULE", "APPLI_LECTURE_SEULE"):
        monkeypatch.delenv(v, raising=False)
    assert maison.lecture_seule("APPLI_LECTURE_SEULE") is False
    monkeypatch.setenv("MAISON_LECTURE_SEULE", "oui")
    assert maison.lecture_seule("APPLI_LECTURE_SEULE") is True
    assert maison.origine_lecture_seule("APPLI_LECTURE_SEULE") == "maison"
    monkeypatch.setenv("APPLI_LECTURE_SEULE", "non")             # l'appli écrit malgré la maison
    assert maison.lecture_seule("APPLI_LECTURE_SEULE") is False
    monkeypatch.setenv("MAISON_LECTURE_SEULE", "")
    monkeypatch.setenv("APPLI_LECTURE_SEULE", "oui")             # une seule appli en essai
    assert maison.lecture_seule("APPLI_LECTURE_SEULE") is True
    assert maison.origine_lecture_seule("APPLI_LECTURE_SEULE") == "appli"


def test_jeton_commun_ancien_et_rotation(monkeypatch):
    for v in ("MAISON_JETON", "MAISON_JETON_ANCIEN", "ANCIEN_JETON_PAIRE"):
        monkeypatch.delenv(v, raising=False)
    assert maison.jetons("ANCIEN_JETON_PAIRE") == ()
    assert not maison.jeton_valide("x", maison.jetons())               # porte fermée
    monkeypatch.setenv("ANCIEN_JETON_PAIRE", "jeton-de-la-paire")
    assert maison.jeton_valide("jeton-de-la-paire", maison.jetons("ANCIEN_JETON_PAIRE"))
    monkeypatch.setenv("MAISON_JETON", "jeton-commun-neuf")
    monkeypatch.setenv("MAISON_JETON_ANCIEN", "jeton-commun-vieux")
    ok = maison.jetons("ANCIEN_JETON_PAIRE")
    assert all(maison.jeton_valide(j, ok) for j in ("jeton-commun-neuf", "jeton-commun-vieux", "jeton-de-la-paire"))
    assert not maison.jeton_valide("autre", ok) and not maison.jeton_valide("", ok)
    assert maison.jeton_a_envoyer("ANCIEN_JETON_PAIRE") == "jeton-de-la-paire"     # transition : l'ancien d'abord
    monkeypatch.delenv("ANCIEN_JETON_PAIRE")
    assert maison.jeton_a_envoyer("ANCIEN_JETON_PAIRE") == "jeton-commun-neuf"
    assert maison.jeton_propose({"authorization": "Bearer abc"}) == "abc"
    assert maison.jeton_propose({"x-maison-jeton": "def"}) == "def"


def test_annuaire_adresses_et_repli():
    appels = []
    services = [{"nom": "Immich", "locale": "http://nas:2283", "privee": "https://nas.exemple.ts.net:2283"},
                {"nom": "Douze points", "locale": "http://nas:8088/", "privee": ""}]

    def lire():
        appels.append(1)
        return services
    a = maison.Annuaire(url="http://anneau", jeton="j", lire=lire)
    assert a.adresse("immich") == "http://nas:2283"
    assert a.adresse("Immich", prive=True) == "https://nas.exemple.ts.net:2283"
    assert a.adresse("Douze points", prive=True) == "http://nas:8088"           # pas d'adresse privée : la locale
    assert a.adresse("Inconnu", repli="http://repli") == "http://repli"
    assert len(appels) == 1                                                   # gardé dix minutes

    def panne():
        raise OSError("refusé")
    b = maison.Annuaire(url="http://anneau", jeton="j", lire=panne)
    assert b.adresse("Immich", repli="http://repli") == "http://repli" and "injoignable" in b.erreur
    c = maison.Annuaire(url="http://anneau", jeton="", lire=lire)               # sans jeton : on ne demande rien
    assert c.adresse("Immich", repli="r") == "r" and len(appels) == 1


def test_reseau_prive():
    assert maison.est_prive("nas.exemple.ts.net:8443") and maison.est_prive("100.101.2.3")
    assert not maison.est_prive("192.0.2.90:8090") and not maison.est_prive("100.200.1.1")


# ================================================================ contrat 2 : réglages d'usage

DEFAUTS = {"texte": "", "actif": True, "nombre": 3, "taux": 0.5, "liste": ["a"]}
VARIABLES = {"texte": "ESSAI_TEXTE", "actif": "ESSAI_ACTIF", "nombre": "ESSAI_NOMBRE", "taux": "ESSAI_TAUX",
             "liste": "ESSAI_LISTE"}


@pytest.fixture()
def sans_variables(monkeypatch):
    for v in VARIABLES.values():
        monkeypatch.delenv(v, raising=False)
    return monkeypatch


def test_contrats():
    assert maison.CONTRAT == 2 and maison.CONTRAT_SAUVEGARDE == 1


def test_reglages_defauts_au_premier_demarrage(tmp_path, sans_variables):
    r = maison.Reglages(tmp_path / "d" / "reglages.json", DEFAUTS, VARIABLES)
    assert r.tout() == DEFAUTS and r.repris == []
    assert json.loads((tmp_path / "d" / "reglages.json").read_text()) == DEFAUTS       # dossier créé, fichier écrit
    assert r.get("nombre") == 3


def test_reglages_reprise_de_la_variable_puis_ignoree(tmp_path, sans_variables):
    m = sans_variables
    m.setenv("ESSAI_TEXTE", "  bonjour  ")
    m.setenv("ESSAI_ACTIF", "non")
    m.setenv("ESSAI_NOMBRE", "12")
    m.setenv("ESSAI_TAUX", "0,75")                                  # virgule française acceptée
    m.setenv("ESSAI_LISTE", "x | y || z ")                          # « | » prioritaire, vides retirés
    chemin = tmp_path / "reglages.json"
    r = maison.Reglages(chemin, DEFAUTS, VARIABLES)
    assert r.tout() == {"texte": "bonjour", "actif": False, "nombre": 12, "taux": 0.75, "liste": ["x", "y", "z"]}
    assert sorted(r.repris) == sorted(DEFAUTS)
    # Second démarrage : la variable a changé (ou reste dans la stack), elle n'est plus lue
    m.setenv("ESSAI_TEXTE", "autre chose")
    m.setenv("ESSAI_NOMBRE", "99")
    r2 = maison.Reglages(chemin, DEFAUTS, VARIABLES)
    assert r2.get("texte") == "bonjour" and r2.get("nombre") == 12 and r2.repris == []
    # Ce qui a été changé dans l'écran survit au redémarrage
    r2.changer({"texte": "réglé dans l'appli"})
    assert maison.Reglages(chemin, DEFAUTS, VARIABLES).get("texte") == "réglé dans l'appli"


def test_reglages_liste_separee_par_virgules(tmp_path, sans_variables):
    sans_variables.setenv("ESSAI_LISTE", "un, deux ,trois,")
    assert maison.Reglages(tmp_path / "r.json", DEFAUTS, VARIABLES).get("liste") == ["un", "deux", "trois"]


@pytest.mark.parametrize("brut, attendu", [("oui", True), ("1", True), ("TRUE", True), ("vrai", True),
                                           ("non", False), ("faux", False), ("n'importe quoi", False)])
def test_reglages_reprise_oui_non(tmp_path, sans_variables, brut, attendu):
    sans_variables.setenv("ESSAI_ACTIF", brut)
    assert maison.Reglages(tmp_path / "r.json", DEFAUTS, VARIABLES).get("actif") is attendu


def test_reglages_variable_illisible_donne_le_defaut(tmp_path, sans_variables):
    sans_variables.setenv("ESSAI_NOMBRE", "douze")
    sans_variables.setenv("ESSAI_TAUX", "beaucoup")
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS, VARIABLES)
    assert r.get("nombre") == 3 and r.get("taux") == 0.5 and r.repris == []


def test_reglages_variable_vide_ou_sans_nom(tmp_path, sans_variables):
    sans_variables.setenv("ESSAI_TEXTE", "   ")                      # vide : pas une reprise
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)                 # aucune variable donnée
    assert r.tout() == DEFAUTS
    r = maison.Reglages(tmp_path / "s.json", DEFAUTS, VARIABLES)
    assert r.get("texte") == "" and r.repris == []


@pytest.mark.parametrize("contenu", ["{pas du json", "[1, 2, 3]", '"texte"', ""])
def test_reglages_fichier_abime_donne_les_defauts(tmp_path, sans_variables, contenu):
    chemin = tmp_path / "reglages.json"
    chemin.write_text(contenu)
    r = maison.Reglages(chemin, DEFAUTS, VARIABLES)
    assert r.tout() == DEFAUTS
    assert json.loads(chemin.read_text()) == DEFAUTS                  # réécrit propre


def test_reglages_fichier_valeur_de_mauvais_type_et_cles_inconnues(tmp_path, sans_variables):
    chemin = tmp_path / "reglages.json"
    chemin.write_text(json.dumps({"texte": "gardé", "actif": "peut-être", "nombre": "7", "vieux": 1}))
    r = maison.Reglages(chemin, DEFAUTS, VARIABLES)
    assert r.get("actif") is True                                     # mauvais type : défaut
    assert r.get("nombre") == 7 and r.get("texte") == "gardé"        # « 7 » se lit comme un entier
    assert "vieux" not in r.tout()                                    # clé disparue de l'appli : oubliée
    assert "vieux" not in json.loads(chemin.read_text())


def test_reglages_nouvelle_cle_reprise_meme_si_le_fichier_existe(tmp_path, sans_variables):
    """Un réglage ajouté dans une version suivante est repris de sa variable à son premier démarrage."""
    chemin = tmp_path / "reglages.json"
    chemin.write_text(json.dumps({"texte": "déjà là"}))
    sans_variables.setenv("ESSAI_NOMBRE", "5")
    r = maison.Reglages(chemin, DEFAUTS, VARIABLES)
    assert r.get("texte") == "déjà là" and r.get("nombre") == 5 and r.repris == ["nombre"]


def test_reglages_changer_types(tmp_path, sans_variables):
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)
    tout = r.changer({"texte": "salut", "actif": False, "nombre": "8", "taux": 2, "liste": ["p", " q ", ""]})
    assert tout == {"texte": "salut", "actif": False, "nombre": 8, "taux": 2.0, "liste": ["p", "q"]}
    assert r.changer({"liste": "m|n"})["liste"] == ["m", "n"]         # texte accepté pour une liste
    assert r.changer({"liste": "m, n"})["liste"] == ["m", "n"]
    assert r.changer({"texte": None})["texte"] == ""


def test_reglages_changer_ignore_les_cles_inconnues(tmp_path, sans_variables):
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)
    assert r.changer({"inconnue": 1, "texte": "ok"}) == {**DEFAUTS, "texte": "ok"}
    assert "inconnue" not in json.loads((tmp_path / "r.json").read_text())
    assert r.changer({}) == r.changer(None) == r.tout()


@pytest.mark.parametrize("cle, valeur", [("actif", "oui"), ("actif", 1), ("nombre", True), ("nombre", "douze"),
                                         ("nombre", 1.5j), ("taux", "beaucoup"), ("liste", 3), ("liste", {"a": 1}),
                                         ("texte", {"a": 1}), ("texte", ["a"])])
def test_reglages_changer_refuse_un_mauvais_type(tmp_path, sans_variables, cle, valeur):
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)
    avant = (tmp_path / "r.json").read_text()
    with pytest.raises((ValueError, TypeError)):
        r.changer({"texte": "ne doit pas passer", cle: valeur})
    assert r.tout() == DEFAUTS                                        # rien changé, même les clés valides
    assert (tmp_path / "r.json").read_text() == avant


def test_reglages_changer_entier_vide_leve_typeerror(tmp_path, sans_variables):
    """Fige le comportement actuel : None pour un entier lève TypeError (pas ValueError). Une route doit attraper
    les deux pour répondre 400 (voir PUT /api/reglages)."""
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)
    with pytest.raises(TypeError):
        r.changer({"nombre": None})


def test_reglages_ecriture_atomique(tmp_path, sans_variables, monkeypatch):
    chemin = tmp_path / "reglages.json"
    r = maison.Reglages(chemin, DEFAUTS)
    r.changer({"texte": "premier"})
    vus = []
    vrai_replace = maison.os.replace

    def replace(src, dst):
        vus.append((str(src), str(dst)))
        assert json.loads(chemin.read_text())["texte"] == "premier"   # l'ancien fichier reste entier jusqu'au bout
        vrai_replace(src, dst)
    monkeypatch.setattr(maison.os, "replace", replace)
    r.changer({"texte": "second"})
    assert vus == [(str(chemin) + ".tmp", str(chemin))]
    assert json.loads(chemin.read_text())["texte"] == "second"
    assert not (tmp_path / "reglages.json.tmp").exists()

    def panne(src, dst):
        raise OSError("disque plein")
    monkeypatch.setattr(maison.os, "replace", panne)
    with pytest.raises(OSError):
        r.changer({"texte": "troisième"})
    assert json.loads(chemin.read_text())["texte"] == "second"        # une écriture ratée ne casse pas le fichier


def test_reglages_tout_rend_une_copie(tmp_path, sans_variables):
    r = maison.Reglages(tmp_path / "r.json", DEFAUTS)
    r.tout()["liste"].append("modifié dehors")
    r.get("liste").append("modifié dehors")
    assert r.get("liste") == ["a"]


# ================================================================ contrat 2 : sauvegarde et restauration

@pytest.mark.parametrize("nom", ["DOUZE_POINTS_HA_WEBHOOK", "CARNET_ICLOUD_USER", "cle_publique", "MAISON_PASSWORD",
                                 "mot_de_passe", "api_token", "MAISON_JETON", "secret", "clé API", "hash",
                                 "identifiant", "login", "email", "courriel", "code_porte"])
def test_est_secret(nom):
    assert maison.est_secret(nom)


@pytest.mark.parametrize("nom", ["modele_album", "veille_heure", "emoji_groupes", "exclus", "cache_mo",
                                 "message_accueil", "afficher_mesures", "seuil", "langue"])
def test_n_est_pas_secret(nom):
    assert not maison.est_secret(nom)


def test_reglages_publics():
    reglages = {"seuil": 3, "api_token": "x", "Chemin_Perso": "/ailleurs", "objet": object(), "liste": ["a"]}
    assert maison.reglages_publics(reglages, exclus=["chemin perso"]) == {"seuil": 3, "liste": ["a"]}
    assert maison.reglages_publics({}) == maison.reglages_publics(None) == {}


def test_sauvegarde():
    s = maison.sauvegarde("essai", "1.2.0", {"seuil": 3, "webhook_ha": "x", "dossier": "/perso"}, exclus=("dossier",))
    assert s["contrat"] == 1 and s["appli"] == "essai" and s["version"] == "1.2.0"
    assert s["reglages"] == {"seuil": 3}
    assert s["le"][:4].isdigit() and "T" in s["le"]                    # date ISO avec fuseau
    json.dumps(s)                                                     # tout est sérialisable


def test_differences():
    actuels = {"seuil": 3, "langue": "fr", "liste": ["a"], "actif": True}
    sauves = {"seuil": 5, "langue": "fr", "liste": ["a", "b"], "disparu": 1, "jeton": "x", "actif": False}
    d = maison.differences(actuels, sauves, exclus=["actif"])
    assert d == [{"cle": "liste", "actuel": ["a"], "sauve": ["a", "b"]},
                 {"cle": "seuil", "actuel": 3, "sauve": 5}]              # trié, sans clé inconnue, secret ni exclue
    assert maison.differences(actuels, dict(actuels)) == []


def test_lire_sauvegarde_par_un_faux_anneau(monkeypatch):
    monkeypatch.setenv("MAISON_JETON", "jeton-commun")
    monkeypatch.delenv("MAISON_ANNEAU_URL", raising=False)
    demandes = []

    def faux(adresse, jeton):
        demandes.append((adresse, jeton))
        return {"dates": ["2026-11-15"]} if "?le=" not in adresse else {"le": "2026-11-15", "version": "1",
                                                                         "reglages": {"seuil": 1}}
    assert maison.lire_sauvegarde("douze-points", lire=faux) == {"dates": ["2026-11-15"]}
    assert maison.lire_sauvegarde("douze-points", "2026-11-15", lire=faux)["reglages"] == {"seuil": 1}
    assert demandes == [("http://anneau:8094/externe/sauvegardes/douze-points", "jeton-commun"),
                        ("http://anneau:8094/externe/sauvegardes/douze-points?le=2026-11-15", "jeton-commun")]
    monkeypatch.setenv("MAISON_ANNEAU_URL", "http://ailleurs:1/")
    maison.lire_sauvegarde("a b", "x&y", jeton="autre", lire=faux)
    assert demandes[-1] == ("http://ailleurs:1/externe/sauvegardes/a%20b?le=x%26y", "autre")   # tout est échappé
    assert maison.lire_sauvegarde("z", url="http://u", lire=faux) and demandes[-1][0] == "http://u/externe/sauvegardes/z"


def test_lire_sauvegarde_anneau_injoignable_leve(monkeypatch):
    def panne(adresse, jeton):
        raise OSError("refusé")
    with pytest.raises(OSError):
        maison.lire_sauvegarde("essai", lire=panne)

"""Module commun maison (contrat 1) : variables communes avec replis, jeton commun, lecture seule, annuaire."""
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

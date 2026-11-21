"""Client Paperless commun (socle 0.12.0) contre le faux Paperless de la sonde. Données inventées."""
from __future__ import annotations

import pytest

from app import maison, paperless
from tests.faux_paperless import FauxPaperless

URL = "http://paperless:8000"


class Horloge:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def dormir(self, s):
        self.t += s


@pytest.fixture
def faux():
    f = FauxPaperless(delai_traitement=1)
    f.compte("jeton-julien", 2).compte("jeton-gazette", 3).compte("jeton-dime", 4)
    return f


def client(faux, jeton="jeton-gazette", **k):
    return paperless.Paperless(URL, jeton, transport=faux.transport, **k)


def file_(tmp_path, c, sources=None, h=None, **k):
    h = h or Horloge()
    sources = sources if sources is not None else {"s1": b"%PDF-1.4 numero 1", "s2": b"%PDF-1.4 numero 2"}
    return paperless.FileEnvois(c, chemin=tmp_path / "envois.json", lire_source=sources.get, horloge=h,
                                dormir=h.dormir, **k)


def test_pas_relie_sans_jeton(faux, tmp_path):
    c = paperless.Paperless(URL, "", transport=faux.transport)
    assert not c.regle
    f = file_(tmp_path, c)
    f.ajouter(cle="a", source="s1", titre="Gazette — A — 01/01/2027")
    assert f.tour() == {"ranges": 0, "erreurs": 0}
    assert faux.envois == 0


def test_essai_lit_la_version(faux):
    ok, detail = client(faux).essai()
    assert ok and "3.5.1" in detail and "API 10" in detail


def test_jeton_refuse(faux):
    with pytest.raises(paperless.ErreurPaperless) as e:
        paperless.Paperless(URL, "faux", transport=faux.transport).essai()
    assert e.value.code == 401


def test_etiquette_creee_sans_appariement_et_reprise(faux):
    c = client(faux)
    i = c.etiquette("Prénom NOM")
    assert faux.tags[i]["matching_algorithm"] == 0
    assert c.etiquette("prénom nom") == i                     # cache et nom exact, sans doublon
    assert len(faux.tags) == 1
    t = c.type_document("Journal maison")
    assert faux.types[t]["matching_algorithm"] == 0


def test_etiquette_pas_creee_en_lecture_seule(faux):
    c = client(faux, lecture_seule=True)
    assert c.etiquette("Nouvelle") is None
    assert not faux.tags


def test_envoi_retrouve_par_le_titre(faux, tmp_path):
    c = client(faux)
    vus = []
    f = file_(tmp_path, c, apres_range=vus.append)
    f.ajouter(cle="g1", source="s1", titre="Gazette — Prénom NOM — 12/12/2026", type_nom="Journal maison",
              etiquettes=["Prénom NOM"], date="2026-12-12")
    assert f.tour() == {"ranges": 1, "erreurs": 0}
    e = f.element("g1")
    assert e["etat"] == "range" and e["document_id"]
    d = faux.documents[e["document_id"]]
    assert d["owner"] == 3 and d["created"] == "2026-12-12"
    assert vus and vus[0]["cle"] == "g1"
    assert faux.envois == 1


def test_jamais_deux_fois(faux, tmp_path):
    c = client(faux)
    f = file_(tmp_path, c)
    f.ajouter(cle="g1", source="s1", titre="T1")
    f.tour()
    f.tour()
    assert f.ajouter(cle="g1", source="s1", titre="T1")["etat"] == "range"   # même clé : rien de nouveau
    f.tour()
    assert faux.envois == 1


def test_titre_deja_present_pas_d_envoi(faux, tmp_path):
    faux.ajouter_document("Gazette — X — 01/01/2027", proprietaire=3)
    f = file_(tmp_path, client(faux))
    f.ajouter(cle="x", source="s1", titre="Gazette — X — 01/01/2027")
    f.tour()
    assert f.element("x")["etat"] == "range" and faux.envois == 0


def test_titres_uniques_exiges(faux, tmp_path):
    f = file_(tmp_path, client(faux))
    f.ajouter(cle="a", source="s1", titre="Même titre")
    with pytest.raises(ValueError):
        f.ajouter(cle="b", source="s2", titre="Même titre")


def test_traitement_lent_pas_de_renvoi(faux, tmp_path):
    faux.delai_traitement = 10**6                            # Paperless n'a jamais fini
    h = Horloge()
    f = file_(tmp_path, client(faux), h=h)
    f.ajouter(cle="lent", source="s1", titre="Lent")
    f.tour()
    assert f.element("lent")["etat"] == "parti"
    for _ in range(40):                                      # 40 tours, des heures plus tard
        h.t += 120
        f.tour()
    assert faux.envois == 1                                  # jamais renvoyé
    assert f.element("lent")["etat"] == "a_verifier"
    faux.delai_traitement = 0
    faux.en_traitement[0]["_attente"] = 0
    f.reprendre("lent")
    f.tour()
    assert f.element("lent")["etat"] == "range" and faux.envois == 1


def test_panne_reseau_reessai_plus_tard(faux, tmp_path):
    h = Horloge()
    f = file_(tmp_path, client(faux), h=h)
    f.ajouter(cle="p", source="s1", titre="Panne")
    faux.panne = True
    assert f.tour()["erreurs"] == 1
    faux.panne = False
    assert f.tour() == {"ranges": 0, "erreurs": 0}           # trop tôt : 10 min d'attente
    h.t += paperless.REESSAI_S + 1
    assert f.tour()["ranges"] == 1


def test_source_absente_pas_d_envoi(faux, tmp_path):
    f = file_(tmp_path, client(faux), sources={})
    f.ajouter(cle="s", source="introuvable", titre="Sans source")
    assert f.tour()["erreurs"] == 1 and faux.envois == 0


def test_un_envoi_a_la_fois_dans_l_ordre(faux, tmp_path):
    f = file_(tmp_path, client(faux))
    f.ajouter(cle="1", source="s1", titre="Premier")
    f.ajouter(cle="2", source="s2", titre="Second")
    assert f.tour()["ranges"] == 2
    ids = [f.element(k)["document_id"] for k in ("1", "2")]
    assert ids[0] < ids[1]


def test_lecture_seule_rien_n_est_envoye(faux, tmp_path):
    f = file_(tmp_path, client(faux, lecture_seule=lambda: True))
    f.ajouter(cle="l", source="s1", titre="Lecture seule")
    assert f.tour() == {"ranges": 0, "erreurs": 0} and faux.envois == 0


def test_dime_lit_les_papiers_impots(faux):
    impots = faux.ajouter_tag("Impôts", proprietaire=2, voir=(4,))
    a = faux.ajouter_document("avis fictif", proprietaire=2, tags=(impots,), contenu="Avis d'impôt fictif")
    faux.ouvrir(a, 4)
    faux.ajouter_document("santé fictive", proprietaire=2)
    d = client(faux, "jeton-dime")
    i = d.etiquette("Impôts", creer=False)
    assert i == impots
    docs = d.documents(i)
    assert [x["id"] for x in docs] == [a]
    assert d.texte(a) == "Avis d'impôt fictif"
    assert d.telecharger(a).startswith(b"%PDF")
    g = client(faux, "jeton-gazette")
    assert g.etiquette("Impôts", creer=False) is None          # gazette ne voit pas l'étiquette
    with pytest.raises(paperless.ErreurPaperless):
        g.document(a)


def test_stockage_par_fonctions(faux):
    memoire = []
    f = paperless.FileEnvois(client(faux), charger=lambda: memoire, sauver=lambda l: (memoire.clear(), memoire.extend(l)),
                             lire_source={"s": b"%PDF-1.4 x"}.get, dormir=lambda s: None)
    f.ajouter(cle="k", source="s", titre="Coffre")
    f.tour()
    assert memoire[0]["etat"] == "range"


def test_resume_et_fiche(faux, tmp_path):
    c = client(faux)
    f = file_(tmp_path, c)
    f.ajouter(cle="r", source="s1", titre="Résumé")
    services = maison.Services("essai")
    paperless.declarer_service(services, c, f, lit="Rien.", ecrit="Les numéros approuvés.", reglage="APP_PAPERLESS_JETON")
    fiche = services.verifier("paperless")
    assert fiche["etat"] == "repond" and "1 envoi(s) en attente" in fiche["detail"]
    f.tour()
    assert f.resume()["compte"]["range"] == 1


def test_fiche_pas_reliee(faux):
    services = maison.Services("essai")
    paperless.declarer_service(services, paperless.Paperless("", ""), None, lit="Rien.", ecrit="Rien.",
                               reglage="APP_PAPERLESS_JETON")
    assert services.liste()["services"][0]["etat"] == "pas_relie"

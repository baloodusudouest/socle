"""Audit du 17/11/2026 (R9) : sessions robustes."""
from app.auth import ESSAIS_MAX, Sessions


def nouvelle():
    import inspect
    if "appli" in inspect.signature(Sessions).parameters:
        return Sessions("essai", "mot-de-passe-de-test")
    return Sessions("mot-de-passe-de-test")


def test_cookie_non_ascii_refuse_sans_erreur():
    s = nouvelle()
    assert s.valide("0.9999999999.é") is False
    assert s.commun_valide("9999999999.é€") is False
    assert s.connecte({s.cookie if hasattr(s, "cookie") else "x": "0.1.ü", "maison_session": "1.ö"}) is False


def test_essais_en_parallele_freines():
    s = nouvelle()
    delais = [s.attente() for _ in range(ESSAIS_MAX + 2)]     # une rafale : tous arrivent avant la moindre réponse
    assert delais[0] == 1.0 and delais[-1] == 5.0
    assert s.verifier_mot_de_passe("mot-de-passe-de-test") is False   # au-delà du plafond : refus sans comparer


def test_cookie_commun_partage():
    a, b = nouvelle(), nouvelle()
    assert b.commun_valide(a.creer_commun())


def test_reglages_refusent_nan_et_inf(tmp_path):
    import pytest
    from app import maison
    r = maison.Reglages(tmp_path / "r.json", {"seuil": 1.5, "n": 3}, {})
    for mauvais in ({"seuil": "nan"}, {"seuil": float("inf")}, {"n": float("inf")}, {"n": 2.5}):
        with pytest.raises(ValueError):
            r.changer(mauvais)
    assert r.get("seuil") == 1.5 and r.get("n") == 3


def test_reglages_abimes_mis_de_cote(tmp_path):
    from app import maison
    (tmp_path / "r.json").write_text("{ abîmé", encoding="utf-8")
    maison.Reglages(tmp_path / "r.json", {"a": 1}, {})
    assert (tmp_path / "r.corrompu").read_text(encoding="utf-8") == "{ abîmé"

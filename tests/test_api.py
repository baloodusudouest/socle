"""Tests du socle : santé, garde des routes, connexion, déconnexion, synthèse."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import Config

MOT_DE_PASSE = "mot-de-passe-de-test"


@pytest.fixture()
def client(tmp_path):
    main.ETAT.clear()
    main.ETAT["cfg"] = Config(password=MOT_DE_PASSE, data=tmp_path, static=tmp_path / "static",
                              attente_connexion=False)
    with TestClient(main.app) as c:
        yield c
    main.ETAT.clear()


def connecter(client):
    r = client.post("/api/connexion", json={"mot_de_passe": MOT_DE_PASSE})
    assert r.status_code == 200


def test_sante_publique(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_api_fermee_sans_connexion(client):
    assert client.get("/api/synthese").status_code == 401
    assert client.get("/api/session").json()["connecte"] is False


def test_mauvais_mot_de_passe_refuse(client):
    r = client.post("/api/connexion", json={"mot_de_passe": "faux"})
    assert r.status_code == 401
    assert client.get("/api/synthese").status_code == 401


def test_connexion_puis_synthese(client):
    connecter(client)
    s = client.get("/api/synthese").json()
    assert len(s["appels_par_minute"]) == 12
    assert s["appels_total"] >= 2
    assert s["donnees_inscriptibles"] is True
    assert 0 <= s["disque"]["pourcentage"] <= 100
    assert r_no_store(client)


def r_no_store(client):
    return client.get("/api/session").headers["cache-control"] == "no-store"


def test_deconnexion_invalide_les_anciens_cookies(client, tmp_path):
    connecter(client)
    ancien = client.cookies.get("socle_session")
    assert client.post("/api/deconnexion").status_code == 200
    client.cookies.set("socle_session", ancien)
    assert client.get("/api/synthese").status_code == 401
    # La génération est écrite sur disque : elle survit à un redémarrage
    assert (tmp_path / "session_generation").read_text() == "1"


def test_cookie_falsifie_refuse(client):
    client.cookies.set("socle_session", "0.9999999999.deadbeef")
    assert client.get("/api/synthese").status_code == 401


def test_interface_non_compilee_signalee(client):
    r = client.get("/")
    assert r.status_code == 404 and "non compilée" in r.json()["detail"]

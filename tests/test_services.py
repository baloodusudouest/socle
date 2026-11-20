"""Contrat 3 (0.10.0) : fiches « Connexion » communes — registre maison.Services, routes /api/maison/services,
accès par session ou ANNEAU_CLE (jamais MAISON_JETON), essai léger limité à un toutes les 30 s, détail nettoyé,
empreintes des fichiers communs de l'interface."""
import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import maison
from tests.test_api import client, connecter  # noqa: F401 — fixture du socle

RACINE = Path(__file__).resolve().parent.parent
CLE = "cle-anneau-de-test-1234567890"


def test_liste_du_socle(client):  # noqa: F811
    connecter(client)
    r = client.get("/api/maison/services")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    corps = r.json()
    assert corps["contrat"] == 3 and corps["appli"] == "socle" and corps["simule"] is False
    (s,) = corps["services"]
    assert set(s) == {"id", "nom", "genre", "cible", "etat", "lit", "ecrit", "reglage", "detail", "verifie_le",
                      "derniere_ecriture", "gestes", "guide"}
    assert s["guide"] is None
    assert s["id"] == "anneau" and s["genre"] == "maison" and s["cible"] == "anneau"


def test_acces_session_ou_cle_anneau_seulement(client, monkeypatch):  # noqa: F811
    assert client.get("/api/maison/services").status_code == 401
    monkeypatch.setenv("MAISON_JETON", "jeton-commun-de-test-12345")
    assert client.get("/api/maison/services", headers={"Authorization": "Bearer jeton-commun-de-test-12345"}).status_code == 401
    assert client.get("/api/maison/services", headers={"Authorization": f"Bearer {CLE}"}).status_code == 401
    monkeypatch.setenv("ANNEAU_CLE", CLE)
    assert client.get("/api/maison/services", headers={"Authorization": f"Bearer {CLE}"}).status_code == 200
    assert client.get("/api/maison/services", headers={"Authorization": "Bearer mauvaise"}).status_code == 401
    # la clé n'ouvre rien d'autre
    assert client.get("/api/synthese", headers={"Authorization": f"Bearer {CLE}"}).status_code == 401
    assert client.get("/api/reglages", headers={"Authorization": f"Bearer {CLE}"}).status_code == 401


def test_service_inconnu_et_methode(client):  # noqa: F811
    connecter(client)
    assert client.post("/api/maison/services/inconnu/verifier").status_code == 404
    assert client.post("/api/maison/services").status_code == 404


def test_pas_relie_sans_jeton(client, monkeypatch):  # noqa: F811
    monkeypatch.delenv("MAISON_JETON", raising=False)
    connecter(client)
    s = client.post("/api/maison/services/anneau/verifier").json()
    assert s["etat"] == "pas_relie" and s["reglage"] == "MAISON_JETON" and s["verifie_le"] is None


# ---------------------------------------------------------------- registre seul

def _appli(registre, session=False):
    app = FastAPI()

    @app.middleware("http")
    async def garde(request, appel):          # garde d'une appli : tout /api/ fermé sans session
        if request.url.path.startswith("/api/") and not session:
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "fermé"}, status_code=401)
        return await appel(request)

    maison.monter_services(app, registre, lambda r: session)
    return TestClient(app)


def test_essai_limite_a_un_toutes_les_30_s():
    appels = []

    def essai():
        appels.append(1)
        return True, "Version 2.1."

    reg = maison.Services("essai").ajouter("immich", "Immich", lit="Les photos.", ecrit="Rien.", essai=essai)
    c = _appli(reg, session=True)
    assert c.get("/api/maison/services").json()["services"][0]["etat"] == "relie"     # le GET n'essaie rien
    assert appels == []
    a = c.post("/api/maison/services/immich/verifier").json()
    b = c.post("/api/maison/services/immich/verifier").json()
    assert appels == [1] and a["etat"] == b["etat"] == "repond" and a["detail"] == "Version 2.1." and a["verifie_le"]
    reg._dernier["immich"]["t"] -= 31
    c.post("/api/maison/services/immich/verifier")
    assert appels == [1, 1]


def test_essai_qui_echoue_et_detail_nettoye():
    def essai():
        raise ConnectionError("refus de http://user:motdepasse@192.168.1.20:2283/api?token=abc ; Bearer xyz")

    reg = maison.Services("essai").ajouter("immich", "Immich", lit="x", ecrit="", essai=essai)
    s = _appli(reg, session=True).post("/api/maison/services/immich/verifier").json()
    assert s["etat"] == "ne_repond_pas" and s["ecrit"] == "Rien."
    for fuite in ("motdepasse", "192.168", "abc", "xyz", "http"):
        assert fuite not in s["detail"]
    assert len(maison.nettoyer_detail("a" * 500)) == 160


def test_essai_asynchrone_et_delai():
    async def lent():
        await asyncio.sleep(5)
        return True

    async def vite():
        return {"ok": True, "detail": "ok"}

    reg = maison.Services("essai", duree_essai_s=0.2)
    reg.ajouter("lent", "Lent", lit="x", ecrit="x", essai=lent).ajouter("vite", "Vite", lit="x", ecrit="x", essai=vite)
    c = _appli(reg, session=True)
    assert c.post("/api/maison/services/lent/verifier").json()["etat"] == "ne_repond_pas"
    assert c.post("/api/maison/services/vite/verifier").json()["etat"] == "repond"


def test_pas_relie_jamais_essaye_et_geste():
    appels = []
    reg = maison.Services("essai", simule=True).ajouter(
        "icloud", "iCloud", lit="Les fiches.", ecrit="Les changements validés.", regle=False, reglage="ICLOUD_ID",
        essai=lambda: appels.append(1), geste={"id": "synchroniser", "nom": "Synchroniser"},
        derniere_ecriture=lambda: "2026-11-20T08:00:00+01:00")
    c = _appli(reg, session=True)
    s = c.post("/api/maison/services/icloud/verifier").json()
    assert appels == [] and s["etat"] == "pas_relie" and s["reglage"] == "ICLOUD_ID"
    corps = c.get("/api/maison/services").json()
    assert corps["simule"] is True and corps["services"][0]["gestes"] == [{"id": "synchroniser", "nom": "Synchroniser"}]
    assert corps["services"][0]["derniere_ecriture"] == "2026-11-20T08:00:00+01:00"


def test_garde_de_l_appli_contournee_seulement_pour_les_fiches():
    reg = maison.Services("essai").ajouter("a", "A", lit="x", ecrit="x")
    c = _appli(reg, session=False)
    assert c.get("/api/maison/services").status_code == 401
    assert c.get("/api/autre").status_code == 401


def test_noter_depuis_un_geste():
    reg = maison.Services("essai").ajouter("a", "A", lit="x", ecrit="x")
    reg.noter("a", False, "iCloud a refusé la synchro (https://p01.icloud.com)")
    s = reg.liste()["services"][0]
    assert s["etat"] == "ne_repond_pas" and "icloud.com" not in s["detail"]


@pytest.mark.parametrize("mauvais", ["", "Immich", "a b", "x" * 41])
def test_identifiants_refuses(mauvais):
    with pytest.raises(ValueError):
        maison.Services("essai").ajouter(mauvais, "X", lit="x", ecrit="x")


def test_un_seul_geste_et_genre_connu():
    with pytest.raises(ValueError):
        maison.Services("essai").ajouter("a", "A", lit="x", ecrit="x", geste={"id": "x"})
    with pytest.raises(ValueError):
        maison.Services("essai").ajouter("a", "A", lit="x", ecrit="x", genre="interne")


def test_empreintes_de_l_interface_commune():
    for nom in maison.FICHIERS_INTERFACE:
        ecrite, calculee = maison.empreinte_interface(RACINE / "frontend" / "src" / "lib" / "services" / nom)
        assert ecrite and ecrite == calculee, nom


def test_guide_relu_et_nettoye():
    guide = {"reglages": [{"nom": "Adresse appelée", "valeur": "http://192.0.2.5:8000"}, {"valeur": "sans nom"}],
             "allumer": ["Allumer le PC.", {"pas": "un texte"}],
             "pannes": [{"signe": "PC injoignable", "faire": ["Vérifier le pare-feu."], "commandes": ["ipconfig", "curl -H 'Authorization: Bearer abc123'"]}],
             "une_fois": [{"texte": "Ouvrir le port", "commande": "netsh …"}], "terminal": "PowerShell", "inconnu": "x"}
    reg = maison.Services("essai").ajouter("pc-calcul", "PC de calcul", lit="x", ecrit="x", guide=lambda: guide)
    g = reg.liste()["services"][0]["guide"]
    assert set(g) == {"reglages", "allumer", "pannes", "une_fois", "terminal", "note"}
    assert g["reglages"] == [{"nom": "Adresse appelée", "valeur": "http://192.0.2.5:8000"}]
    assert g["allumer"] == ["Allumer le PC."] and g["pannes"][0]["commandes"][0] == "ipconfig"
    assert "abc123" not in g["pannes"][0]["commandes"][1]
    assert maison.nettoyer_guide({}) is None and maison.nettoyer_guide("texte") is None
    reg2 = maison.Services("essai").ajouter("a", "A", lit="x", ecrit="x", guide=lambda: 1 / 0)
    assert reg2.liste()["services"][0]["guide"] is None

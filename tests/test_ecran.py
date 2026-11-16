"""Tests d'écran (0.6.0) : le socle ouvert dans un vrai navigateur, sur PC et iPhone.

À chaque écran : aucune erreur de page, aucun débordement horizontal. L'Anneau est un faux (aucun réseau).
Sautés si Playwright ou l'interface compilée manquent (la CI les installe : voir .github/workflows/tests.yml).
Le serveur est partagé entre les deux tailles : un test qui change un état le remet comme il l'a trouvé.
"""
from __future__ import annotations

import os
import shutil
import socket
import threading
import time
import urllib.error
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
STATIQUE = Path(__file__).resolve().parents[1] / "app" / "static"
pytestmark = pytest.mark.skipif(not (STATIQUE / "index.html").exists(),
                                reason="interface non compilée (cd frontend && npx vite build)")

MDP = "mot-de-passe-ecran"
TAILLES = {"pc": {"width": 1366, "height": 900}, "iphone": {"width": 390, "height": 844}}
SAUVEGARDES = {
    "2026-11-15": {"le": "2026-11-15", "version": "0.6.0",
                   "reglages": {"message_accueil": "Bonjour depuis la sauvegarde", "afficher_mesures": False}},
    "2026-11-14": {"le": "2026-11-14", "version": "0.6.0",
                   "reglages": {"message_accueil": "", "afficher_mesures": True}},
}
ANNEAU = {"panne": False}


def faux_anneau(adresse, jeton):
    if ANNEAU["panne"]:
        raise urllib.error.URLError("refusé")
    if "?le=" not in adresse:
        return {"dates": sorted(SAUVEGARDES, reverse=True)}
    return SAUVEGARDES[adresse.split("?le=")[1]]


@pytest.fixture(scope="module")
def adresse(tmp_path_factory):
    import httpx
    import uvicorn

    from app import main
    from app.config import Config
    main.ETAT.clear()
    main.ETAT["cfg"] = Config(password=MDP, data=tmp_path_factory.mktemp("ecran"), static=STATIQUE,
                              attente_connexion=False)
    main.ETAT["lire_anneau"] = faux_anneau
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    serveur = uvicorn.Server(uvicorn.Config(main.app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=serveur.run, daemon=True).start()
    for _ in range(200):
        try:
            if httpx.get(f"http://127.0.0.1:{port}/health", timeout=1).status_code == 200:
                break
        except httpx.HTTPError:
            time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    serveur.should_exit = True
    main.ETAT.clear()


@pytest.fixture(scope="module")
def navigateur():
    with pw.sync_playwright() as p:
        chrome = os.environ.get("CHROME") or shutil.which("google-chrome")
        b = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"]) if chrome else p.chromium.launch()
        yield b
        b.close()


def ouvrir(navigateur, adresse, taille, page_hash="reglages"):
    page = navigateur.new_page(viewport=TAILLES[taille])
    erreurs = []
    page.on("pageerror", lambda e: erreurs.append(str(e)))
    page.goto(adresse + "/#/" + page_hash)
    page.fill("#mot-de-passe", MDP)
    page.click("button[type=submit]")
    page.get_by_role("heading", level=1).wait_for()
    return page, erreurs


def sans_debordement(page):
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")


def remettre(page):
    page.evaluate("""fetch('/api/reglages', {method: 'PUT', headers: {'Content-Type': 'application/json'},
                     body: JSON.stringify({message_accueil: '', afficher_mesures: true})})""")


@pytest.mark.parametrize("taille", TAILLES)
def test_reglages_changer_puis_voir_dans_la_synthese(navigateur, adresse, taille):
    page, erreurs = ouvrir(navigateur, adresse, taille)
    tuile = page.get_by_role("region", name="Réglages", exact=True)
    tuile.wait_for()
    page.get_by_role("region", name="Restaurer les réglages").wait_for()
    enregistrer = tuile.get_by_role("button", name="Enregistrer")
    assert enregistrer.is_disabled()                                     # rien de changé : rien à enregistrer
    page.fill("#message-accueil", "Bonjour de l'écran")
    interrupteur = tuile.get_by_role("switch")
    assert interrupteur.get_attribute("aria-checked") == "true"
    interrupteur.click()
    assert interrupteur.get_attribute("aria-checked") == "false"
    enregistrer.click()
    tuile.get_by_text("Réglages enregistrés.").wait_for()
    sans_debordement(page)
    page.goto(adresse + "/#/synthese")
    page.get_by_text("Bonjour de l'écran").wait_for()
    page.get_by_text("Appels servis").wait_for()
    assert page.get_by_text("Appels à l'API, 12 dernières minutes").count() == 0     # graphique masqué
    sans_debordement(page)
    remettre(page)
    assert erreurs == []
    page.close()


@pytest.mark.parametrize("taille", TAILLES)
def test_restaurer_les_reglages(navigateur, adresse, taille):
    page, erreurs = ouvrir(navigateur, adresse, taille)
    tuile = page.get_by_role("region", name="Restaurer les réglages")
    choix = tuile.locator("#date-sauvegarde")
    choix.wait_for()
    assert choix.input_value() == "2026-11-15"                          # la plus récente d'abord
    differences = tuile.get_by_role("list", name="Différences")
    differences.wait_for()
    assert differences.locator("li").count() == 2
    assert "Bonjour depuis la sauvegarde" in differences.inner_text()
    choix.select_option("2026-11-14")
    tuile.get_by_text("Rien ne diffère des réglages actuels.").wait_for()
    choix.select_option("2026-11-15")
    differences.wait_for()
    sans_debordement(page)
    tuile.get_by_role("button", name="Restaurer").click()
    groupe = tuile.get_by_role("group", name="Confirmer la restauration")
    groupe.get_by_role("button", name="Annuler").click()                 # annuler : rien ne change
    assert page.input_value("#message-accueil") == ""
    tuile.get_by_role("button", name="Restaurer").click()
    groupe.get_by_role("button", name="Confirmer").click()
    tuile.get_by_text("2 réglages restaurés.").wait_for()
    assert page.input_value("#message-accueil") == "Bonjour depuis la sauvegarde"   # la tuile Réglages suit
    sans_debordement(page)
    remettre(page)
    assert erreurs == []
    page.close()


@pytest.mark.parametrize("taille", TAILLES)
def test_restaurer_anneau_injoignable(navigateur, adresse, taille):
    ANNEAU["panne"] = True
    try:
        page, erreurs = ouvrir(navigateur, adresse, taille)
        tuile = page.get_by_role("region", name="Restaurer les réglages")
        tuile.get_by_text("L'Anneau ne répond pas").wait_for()
        tuile.get_by_role("button", name="Réessayer").wait_for()
        page.get_by_role("region", name="Réglages", exact=True).get_by_role("button", name="Enregistrer").wait_for()
        sans_debordement(page)
        assert erreurs == []
        page.close()
    finally:
        ANNEAU["panne"] = False

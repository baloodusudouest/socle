"""socle : squelette commun des applis (FastAPI + interface Svelte compilée).

Routes : /health (publique), /api/session, /api/connexion, /api/deconnexion,
/api/synthese (mesures réelles du conteneur), puis l'interface.
"""
from __future__ import annotations

import asyncio
import platform
import shutil
import time
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from importlib.metadata import version as version_paquet
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from . import __version__
from .auth import DUREE, Sessions
from .config import APPLI, Config, charger

ETAT: dict = {}
PUBLIQUES = ("/api/connexion", "/api/session")


def _fichier_generation(cfg: Config) -> Path:
    return cfg.data / "session_generation"


def _lire_generation(cfg: Config) -> int:
    try:
        return int(_fichier_generation(cfg).read_text().strip())
    except (OSError, ValueError):
        return 0


def _inscriptible(dossier: Path) -> bool:
    essai = dossier / ".essai-ecriture"
    try:
        essai.write_text("ok")
        essai.unlink()
        return True
    except OSError:
        return False


@asynccontextmanager
async def cycle(app: FastAPI):
    cfg = ETAT.get("cfg") or charger()
    cfg.data.mkdir(parents=True, exist_ok=True)
    ETAT.update(cfg=cfg, sessions=Sessions(APPLI, cfg.password, _lire_generation(cfg)),
                demarrage=datetime.now().astimezone(), debut=time.monotonic(),
                total=0, minutes=Counter())
    yield


app = FastAPI(title=APPLI, version=__version__, lifespan=cycle, docs_url=None, redoc_url=None)


# ================================================================ sécurité

@app.middleware("http")
async def garde(request: Request, appel):
    chemin = request.url.path
    if chemin.startswith("/api/"):
        if chemin not in PUBLIQUES and not ETAT["sessions"].valide(request.cookies.get(ETAT["sessions"].cookie)):
            return JSONResponse({"detail": "Connexion nécessaire."}, status_code=401)
        # Compteur réel affiché dans la synthèse
        ETAT["total"] += 1
        ETAT["minutes"][datetime.now().strftime("%H:%M")] += 1
    reponse = await appel(request)
    if chemin.startswith("/api/"):
        reponse.headers["Cache-Control"] = "no-store"
    return reponse


class LectureSeule(Exception):
    """Écriture refusée : l'appli tourne en lecture seule (APP_LECTURE_SEULE)."""


def exiger_ecriture(quoi: str = "") -> None:
    """À appeler en tête de toute route, et de toute fonction, qui écrit chez un service extérieur
    (iCloud, Immich, fichiers d'une photothèque…). Le refus arrive avant toute trace dans un journal."""
    if ETAT["cfg"].lecture_seule:
        raise LectureSeule(f"Mode lecture seule : rien n'est écrit{' dans ' + quoi if quoi else ''}.")


@app.exception_handler(LectureSeule)
async def _lecture_seule(_: Request, exc: LectureSeule):
    return JSONResponse({"detail": str(exc)}, status_code=409)


# ================================================================ public

@app.get("/health")
def sante():
    return {"ok": True, "version": __version__}


# ================================================================ connexion

@app.get("/api/session")
def session(request: Request):
    s = ETAT["sessions"]
    return {"connecte": s.valide(request.cookies.get(s.cookie)), "version": __version__,
            "lecture_seule": ETAT["cfg"].lecture_seule}


@app.post("/api/connexion")
async def connexion(corps: dict = Body(...)):
    s = ETAT["sessions"]
    if ETAT["cfg"].attente_connexion:
        await asyncio.sleep(s.attente())
    if not s.verifier_mot_de_passe(str(corps.get("mot_de_passe", ""))):
        raise HTTPException(401, "Mot de passe incorrect.")
    r = JSONResponse({"ok": True})
    r.set_cookie(s.cookie, s.creer(), max_age=DUREE, httponly=True, samesite="strict")
    return r


@app.post("/api/deconnexion")
def deconnexion():
    s = ETAT["sessions"]
    s.generation += 1
    try:
        _fichier_generation(ETAT["cfg"]).write_text(str(s.generation))
    except OSError:
        pass  # volume en lecture seule : la déconnexion vaut jusqu'au prochain redémarrage
    r = JSONResponse({"ok": True})
    r.delete_cookie(s.cookie)
    return r


# ================================================================ exemple d'écriture gardée

@app.post("/api/essai-ecriture")
def essai_ecriture():
    """Modèle d'une route qui écrit : la garde d'abord, l'écriture ensuite. Ici, un simple fichier
    témoin dans /data (une vraie appli écrirait chez un service extérieur)."""
    exiger_ecriture("le dossier de données")
    (ETAT["cfg"].data / "temoin.txt").write_text(datetime.now().isoformat(timespec="seconds"))
    return {"ok": True}


# ================================================================ synthèse

@app.get("/api/synthese")
def synthese():
    cfg: Config = ETAT["cfg"]
    disque = shutil.disk_usage(cfg.data)
    maintenant = datetime.now()
    minutes = [(maintenant - timedelta(minutes=i)).strftime("%H:%M") for i in range(11, -1, -1)]
    compteur: Counter = ETAT["minutes"]
    for cle in [c for c in compteur if c not in minutes]:   # on ne garde que la fenêtre affichée
        del compteur[cle]
    return {
        "version": __version__,
        "demarrage": ETAT["demarrage"].isoformat(timespec="seconds"),
        "en_service_secondes": int(time.monotonic() - ETAT["debut"]),
        "appels_total": ETAT["total"],
        "appels_par_minute": [{"minute": m, "appels": compteur.get(m, 0)} for m in minutes],
        "disque": {"total": disque.total, "utilise": disque.used,
                   "pourcentage": round(100 * disque.used / disque.total, 1) if disque.total else 0},
        "donnees_inscriptibles": _inscriptible(cfg.data),
        "versions": [
            {"nom": APPLI, "version": __version__},
            {"nom": "Python", "version": platform.python_version()},
            {"nom": "FastAPI", "version": version_paquet("fastapi")},
            {"nom": "Uvicorn", "version": version_paquet("uvicorn")},
        ],
    }


# ================================================================ interface

@app.get("/{chemin:path}")
def interface(chemin: str):
    statique = ETAT["cfg"].static
    fichier = (statique / chemin).resolve() if chemin else None
    if fichier and fichier.is_file() and statique.resolve() in fichier.parents:
        return FileResponse(fichier)
    index = statique / "index.html"
    if index.is_file():
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
    return JSONResponse({"detail": "Interface non compilée."}, status_code=404)

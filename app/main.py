"""socle : squelette commun des applis (FastAPI + interface Svelte compilée).

Routes : /health (publique), /api/session, /api/connexion, /api/deconnexion,
/api/synthese (mesures réelles du conteneur), /api/reglages et /api/restaurer (0.6.0),
/externe/sauvegarde (jeton commun, pour l'Anneau), /api/maison/services et
/api/maison/services/{id}/verifier (0.10.0, contrat 3 : session ou ANNEAU_CLE, voir maison.monter_services),
puis l'interface.
"""
from __future__ import annotations

import asyncio
import logging
import platform
import re
import shutil
import time
from collections import Counter
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from importlib.metadata import version as version_paquet
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from . import __version__, maison
from .auth import COMMUN, DUREE, Sessions, en_https
from .config import APPLI, Config, charger

ETAT: dict = {}
PUBLIQUES = ("/api/connexion", "/api/session")
journal = logging.getLogger("socle")

# ---------------------------------------------------------------- réglages d'usage (0.6.0, contrat 2)
# Ce que l'utilisateur règle dans l'appli : jamais dans la stack. Le type de la valeur par défaut fixe le type.
REGLAGES_DEFAUTS = {
    "message_accueil": "",       # texte affiché en tête de la Synthèse
    "afficher_mesures": True,    # oui/non : le graphique des appels dans la Synthèse
}
# Anciennes variables de la stack, lues UNE fois (premier démarrage) pour reprendre la valeur, puis plus jamais.
REGLAGES_VARIABLES = {"message_accueil": "APP_MESSAGE_ACCUEIL"}
# Clés à ne jamais sortir de l'appli, en plus de ce que maison.est_secret() écarte déjà (un nom de secret).
# Liste explicite même vide : une appli y met un réglage qui contient un chemin personnel, un nom de proche…
EXCLUS_SAUVEGARDE: tuple[str, ...] = ()
JOUR = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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
    reglages = maison.Reglages(cfg.data / "reglages.json", REGLAGES_DEFAUTS, REGLAGES_VARIABLES)
    for k in reglages.repris:      # le nom seulement : la valeur peut être personnelle
        journal.warning("réglage « %s » repris de la variable %s (dernière lecture de cette variable)",
                        k, REGLAGES_VARIABLES[k])
    ETAT["reglages"] = reglages
    ETAT.setdefault("lire_anneau", None)     # les tests y mettent un faux Anneau (argument lire= de maison)
    yield


app = FastAPI(title=APPLI, version=__version__, lifespan=cycle, docs_url=None, redoc_url=None)


# ================================================================ sécurité

@app.middleware("http")
async def garde(request: Request, appel):
    # /externe/… n'est pas gardé ici : chaque route y vérifie le jeton commun elle-même.
    chemin = request.url.path
    if chemin.startswith("/api/"):
        if chemin not in PUBLIQUES and not ETAT["sessions"].connecte(request.cookies):
            return JSONResponse({"detail": "Connexion nécessaire."}, status_code=401)
        # Compteur réel affiché dans la synthèse
        ETAT["total"] += 1
        ETAT["minutes"][datetime.now().strftime("%H:%M")] += 1
    reponse = await appel(request)
    if chemin.startswith(("/api/", "/externe/")):
        reponse.headers["Cache-Control"] = "no-store"
    return reponse


class LectureSeule(Exception):
    """Écriture refusée : l'appli tourne en lecture seule (MAISON_LECTURE_SEULE, ou APP_LECTURE_SEULE pour elle seule)."""


def exiger_ecriture(quoi: str = "") -> None:
    """À appeler en tête de toute route, et de toute fonction, qui écrit chez un service extérieur
    (iCloud, Immich, fichiers d'une photothèque…). Le refus arrive avant toute trace dans un journal."""
    if ETAT["cfg"].lecture_seule:
        raise LectureSeule(f"Mode lecture seule : rien n'est écrit{' dans ' + quoi if quoi else ''}.")


# ================================================================ fiches « Connexion » (0.10.0, contrat 3)
# Une fiche par service extérieur : ce que l'appli y lit, ce qu'elle y écrit, la variable qui le relie, et un essai
# LÉGER (rien d'écrit, rien de payant, rien de réveillé). Le dossier de données n'est pas un service : il est dans
# Réglages. Le socle n'a qu'un service : l'Anneau (annuaire et sauvegardes, pour « Restaurer »).
SERVICES = maison.Services(APPLI)
SERVICES.ajouter(
    "anneau", "L'Anneau", genre="maison", cible="anneau",
    lit="L'annuaire des adresses des applis et les sauvegardes de nuit des réglages, pour « Restaurer ».",
    ecrit="Rien.",
    regle=lambda: bool(maison.jeton_a_envoyer()), reglage="MAISON_JETON",
    essai=lambda: maison.essai_http(maison.adresse_anneau()),
)
# Monté APRÈS la garde : le dernier middleware ajouté passe en premier (la garde ne voit pas ces deux routes).
maison.monter_services(app, SERVICES, lambda r: "sessions" in ETAT and ETAT["sessions"].connecte(r.cookies))


@app.exception_handler(LectureSeule)
async def _lecture_seule(_: Request, exc: LectureSeule):
    return JSONResponse({"detail": str(exc)}, status_code=409)


# ================================================================ public

@app.get("/health")
def sante(request: Request):
    # 0.9.0 : version_socle, taches, copie_base (maison.sante) ; messages d'erreur seulement avec le jeton commun
    # ou une session. Le socle n'a ni boucle ni base : taches vide, copie_base null.
    session_ok = "sessions" in ETAT and ETAT["sessions"].connecte(request.cookies)
    return {"ok": True, "version": __version__, **maison.sante(request, session_ok=session_ok)}


# ================================================================ connexion

@app.get("/api/session")
def session(request: Request):
    s = ETAT["sessions"]
    return {"connecte": s.connecte(request.cookies), "version": __version__,
            "lecture_seule": ETAT["cfg"].lecture_seule,
            "origine_lecture_seule": ETAT["cfg"].origine_lecture_seule}


@app.post("/api/connexion")
async def connexion(request: Request, corps: dict = Body(...)):
    s = ETAT["sessions"]
    if ETAT["cfg"].attente_connexion:
        await asyncio.sleep(s.attente())
    if not s.verifier_mot_de_passe(str(corps.get("mot_de_passe", ""))):
        raise HTTPException(401, "Mot de passe incorrect.")
    r = JSONResponse({"ok": True})
    r.set_cookie(s.cookie, s.creer(), max_age=DUREE, httponly=True, samesite="strict", secure=en_https(request))
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
    r.delete_cookie(COMMUN)      # « Se déconnecter » ferme aussi la connexion commune
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


# ================================================================ réglages (0.6.0)
# Réglages internes de l'appli : les changer ou les restaurer est permis même en lecture seule
# (la lecture seule ne protège que les services extérieurs).

@app.get("/api/reglages")
def lire_reglages():
    return {"reglages": ETAT["reglages"].tout()}


@app.put("/api/reglages")
def changer_reglages(corps=Body(...)):
    if not isinstance(corps, dict):
        raise HTTPException(400, "Réglages attendus sous la forme {clé: valeur}.")
    try:
        return {"reglages": ETAT["reglages"].changer(corps)}
    except (TypeError, ValueError) as exc:
        raise HTTPException(400, f"Valeur refusée : {exc}.") from exc


# ================================================================ sauvegarde (contrat de sauvegarde 1)

@app.get("/externe/sauvegarde")
def externe_sauvegarde(request: Request):
    """Lue chaque nuit par l'Anneau, avec le jeton commun. Réglages publics et version seulement."""
    acceptes = maison.jetons()
    if not acceptes:
        raise HTTPException(404, "Not Found")                 # MAISON_JETON vide : porte fermée
    if not maison.jeton_valide(maison.jeton_propose(request.headers), acceptes):
        raise HTTPException(401, "Jeton commun manquant ou invalide.")
    return maison.sauvegarde(APPLI, __version__, ETAT["reglages"].tout(), exclus=EXCLUS_SAUVEGARDE)


def _demander_anneau(le: str = "") -> dict:
    """Demande à l'Anneau ; ses pannes deviennent des messages clairs (404 rien à restaurer, 503 injoignable)."""
    if le and not JOUR.match(le):
        raise HTTPException(400, "Date attendue sous la forme AAAA-MM-JJ.")
    try:
        reponse = maison.lire_sauvegarde(APPLI, le, lire=ETAT.get("lire_anneau"))
    except Exception as exc:                                  # noqa: BLE001 — urllib, réseau, JSON…
        if getattr(exc, "code", None) == 404:
            raise HTTPException(404, "L'Anneau n'a aucune sauvegarde du socle"
                                     f"{' le ' + le if le else ''}.") from exc
        raise HTTPException(503, "L'Anneau ne répond pas : restauration impossible pour l'instant "
                                 f"({exc.__class__.__name__}).") from exc
    if not isinstance(reponse, dict):
        raise HTTPException(503, "Réponse de l'Anneau illisible.")
    if le and not isinstance(reponse.get("reglages"), dict):
        raise HTTPException(404, f"L'Anneau n'a aucune sauvegarde du socle le {le}.")
    return reponse


@app.get("/api/restaurer")
def restaurer_voir(le: str = ""):
    if not le:
        dates = _demander_anneau().get("dates") or []
        return {"dates": [d for d in dates if isinstance(d, str)]}
    sauve = _demander_anneau(le)
    return {"le": le, "version": sauve.get("version", ""),
            "differences": maison.differences(ETAT["reglages"].tout(), sauve["reglages"], EXCLUS_SAUVEGARDE)}


@app.post("/api/restaurer")
def restaurer(corps: dict = Body(...)):
    le = str(corps.get("le", ""))
    if not le:
        raise HTTPException(400, "Choisis la date de la sauvegarde à restaurer.")
    sauve = _demander_anneau(le)
    reglages = ETAT["reglages"]
    appliques, ignores = [], []
    for d in maison.differences(reglages.tout(), sauve["reglages"], EXCLUS_SAUVEGARDE):
        try:
            reglages.changer({d["cle"]: d["sauve"]})
            appliques.append(d["cle"])
        except (TypeError, ValueError):
            ignores.append(d["cle"])          # valeur d'une ancienne version qui n'a plus le bon type
    journal.warning("réglages restaurés depuis la sauvegarde du %s : %s", le, ", ".join(appliques) or "aucun")
    return {"le": le, "appliques": appliques, "ignores": ignores, "reglages": reglages.tout()}


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

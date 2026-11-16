"""Réglages lus dans l'environnement du conteneur. Aucune valeur personnelle dans le code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from . import maison

APPLI = "socle"


@dataclass(frozen=True)
class Config:
    password: str
    data: Path
    static: Path
    attente_connexion: bool = True   # délai anti-essais ; coupé dans les tests
    lecture_seule: bool = False      # 0.2.0 : l'appli lit tout mais n'écrit nulle part hors de chez elle


def charger() -> Config:
    # 0.5.0 : variables communes de la maison (app/maison.py), avec repli sur les anciennes
    mot_de_passe = maison.mot_de_passe("APP_PASSWORD")
    if len(mot_de_passe) < 12:
        raise SystemExit("MAISON_PASSWORD (ou APP_PASSWORD) est absent ou trop court (12 caractères au moins) : "
                         "le socle ne démarre pas.")
    return Config(
        password=mot_de_passe,
        data=Path(os.environ.get("APP_DATA", "/data")),
        static=Path(__file__).parent / "static",
        lecture_seule=maison.lecture_seule("APP_LECTURE_SEULE"),
    )

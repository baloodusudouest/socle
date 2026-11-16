"""Réglages lus dans l'environnement du conteneur. Aucune valeur personnelle dans le code.

0.6.0 : les variables de la stack ne servent plus qu'à ce qui touche à l'installation (mot de passe, dossier,
lecture seule). Les réglages d'usage vivent dans l'appli (écran Réglages, fichier reglages.json, voir main.py).
"""
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
    origine_lecture_seule: str = ""  # 0.6.0 : « maison » (MAISON_LECTURE_SEULE), « appli » (APP_LECTURE_SEULE) ou « »


def charger() -> Config:
    # 0.6.0 : MAISON_PASSWORD seul (l'ancien APP_PASSWORD n'est plus lu)
    mot_de_passe = maison.mot_de_passe()
    if len(mot_de_passe) < 12:
        raise SystemExit("MAISON_PASSWORD est absent ou trop court (12 caractères au moins) : "
                         "le socle ne démarre pas.")
    return Config(
        password=mot_de_passe,
        data=Path(os.environ.get("APP_DATA", "/data")),
        static=Path(__file__).parent / "static",
        # APP_LECTURE_SEULE reste : forçage pour cette appli seule (« oui » ou « non »), sinon MAISON_LECTURE_SEULE
        lecture_seule=maison.lecture_seule("APP_LECTURE_SEULE"),
        origine_lecture_seule=maison.origine_lecture_seule("APP_LECTURE_SEULE"),
    )

"""Réglages lus dans l'environnement du conteneur. Aucune valeur personnelle dans le code."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

APPLI = "socle"


@dataclass(frozen=True)
class Config:
    password: str
    data: Path
    static: Path
    attente_connexion: bool = True   # délai anti-essais ; coupé dans les tests
    lecture_seule: bool = False      # 0.2.0 : l'appli lit tout mais n'écrit nulle part hors de chez elle


def charger() -> Config:
    mot_de_passe = os.environ.get("APP_PASSWORD", "")
    if len(mot_de_passe) < 12:
        raise SystemExit("APP_PASSWORD est absent ou trop court (12 caractères au moins) : le socle ne démarre pas.")
    return Config(
        password=mot_de_passe,
        data=Path(os.environ.get("APP_DATA", "/data")),
        static=Path(__file__).parent / "static",
        lecture_seule=os.environ.get("APP_LECTURE_SEULE", "").strip().lower() in ("oui", "1", "true", "yes"),
    )

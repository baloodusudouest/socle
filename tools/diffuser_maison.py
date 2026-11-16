"""Signe app/maison.py (empreinte en dernière ligne) et, si on lui donne des dossiers d'applis, l'y copie tel quel.

  python tools/diffuser_maison.py                         # signe seulement
  python tools/diffuser_maison.py ../carnet ../millesime  # signe puis copie dans <appli>/app/maison.py
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "app" / "maison.py"
MARQUE = "\n# empreinte: "


def signer() -> str:
    texte = SOURCE.read_text(encoding="utf-8")
    corps = texte.rsplit(MARQUE, 1)[0].rstrip("\n")
    empreinte = hashlib.sha256(corps.encode("utf-8")).hexdigest()[:16]
    SOURCE.write_text(corps + MARQUE + empreinte + "\n", encoding="utf-8")
    return empreinte


if __name__ == "__main__":
    e = signer()
    print("empreinte", e)
    for dossier in sys.argv[1:]:
        cible = Path(dossier) / "app" / "maison.py"
        shutil.copyfile(SOURCE, cible)
        print("copié dans", cible)

"""Signe les fichiers communs du socle et, si on lui donne des dossiers d'applis, les y copie tels quels.

Fichiers communs :
  app/maison.py                                   empreinte en dernière ligne (« # empreinte: … »)
  frontend/src/lib/services/FicheService.svelte   0.10.0 : fiche d'un service (contrat 3)
  frontend/src/lib/services/Services.svelte       0.10.0 : écran « Connexion » commun
  (les deux .svelte portent « <!-- empreinte: … --> » en dernière ligne)

  python tools/diffuser_maison.py                         # signe seulement
  python tools/diffuser_maison.py ../carnet ../millesime  # signe puis copie dans chaque appli (mêmes chemins)
  python tools/diffuser_maison.py --sans-interface ../verif-dates-photos   # maison.py seul (appli sans Svelte commun)
  python tools/diffuser_maison.py --paperless ../gazette ../dime   # 0.12.0 : ajoute app/paperless.py (signé) et
                                                                   # tests/faux_paperless.py aux applis reliées à Paperless
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "app" / "maison.py"
MARQUE = "\n# empreinte: "
INTERFACE = [RACINE / "frontend" / "src" / "lib" / "services" / n for n in ("FicheService.svelte", "Services.svelte")]
MARQUE_INTERFACE = "\n<!-- empreinte: "
PAPERLESS = RACINE / "app" / "paperless.py"                     # 0.12.0 : client Paperless commun (même marque que maison.py)
FAUX_PAPERLESS = RACINE / "tests" / "faux_paperless.py"


def _empreinte(corps: str) -> str:
    return hashlib.sha256(corps.encode("utf-8")).hexdigest()[:16]


def signer(source: Path = SOURCE) -> str:
    texte = source.read_text(encoding="utf-8")
    corps = texte.rsplit(MARQUE, 1)[0].rstrip("\n")
    empreinte = _empreinte(corps)
    source.write_text(corps + MARQUE + empreinte + "\n", encoding="utf-8")
    return empreinte


def signer_interface(chemin: Path) -> str:
    texte = chemin.read_text(encoding="utf-8")
    corps = texte.rsplit(MARQUE_INTERFACE, 1)[0].rstrip("\n")
    empreinte = _empreinte(corps)
    chemin.write_text(corps + MARQUE_INTERFACE + empreinte + " -->\n", encoding="utf-8")
    return empreinte


if __name__ == "__main__":
    args = sys.argv[1:]
    avec_interface = "--sans-interface" not in args
    avec_paperless = "--paperless" in args
    dossiers = [a for a in args if a not in ("--sans-interface", "--paperless")]
    print("maison.py", signer())
    print("paperless.py", signer(PAPERLESS))
    for f in INTERFACE:
        print(f.name, signer_interface(f))
    for dossier in dossiers:
        cible = Path(dossier) / "app" / "maison.py"
        shutil.copyfile(SOURCE, cible)
        print("copié dans", cible)
        if avec_interface:
            rep = Path(dossier) / "frontend" / "src" / "lib" / "services"
            rep.mkdir(parents=True, exist_ok=True)
            for f in INTERFACE:
                shutil.copyfile(f, rep / f.name)
                print("copié dans", rep / f.name)
        if avec_paperless:
            shutil.copyfile(PAPERLESS, Path(dossier) / "app" / "paperless.py")
            (Path(dossier) / "tests").mkdir(exist_ok=True)
            shutil.copyfile(FAUX_PAPERLESS, Path(dossier) / "tests" / "faux_paperless.py")
            print("copié dans", Path(dossier) / "app" / "paperless.py", "et tests/faux_paperless.py")

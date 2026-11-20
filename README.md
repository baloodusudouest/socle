# socle

Squelette commun des applis auto-hébergées : **FastAPI** + **Svelte 5** + **Tailwind 4** + **shadcn-svelte**, servi par un seul conteneur Docker.

C'est un **modèle à copier** : une nouvelle appli part d'une copie de ce dépôt, puis change son nom, sa couleur et ses écrans.

Le format commun des applis (navigation, tuiles, Connexion, Réglages, couleurs, règles de sécurité, méthode) est décrit dans [`docs/format.md`](docs/format.md).

Avant de créer une appli : [`docs/format.md`](docs/format.md) (le format) et [`docs/lecons.md`](docs/lecons.md) (ce que les applis précédentes ont appris). Versions : [`CHANGELOG.md`](CHANGELOG.md).

## Ce que contient le socle

| Élément | Où | Rôle |
|---|---|---|
| API | `app/` | Santé, connexion par mot de passe, mesures réelles du conteneur, réglages et sauvegarde (0.6.0) |
| Interface | `frontend/` | Rail et pilule, écran de synthèse en tuiles, « Connexion » (une tuile par service), « Réglages », planche des composants |
| Module commun | `app/maison.py` | Copié tel quel dans chaque appli (contrat 2) : mot de passe et jeton communs, lecture seule, annuaire de l'Anneau, réglages d'usage, sauvegarde |
| Réglages | écran Réglages, `/api/reglages`, `/api/restaurer`, `/externe/sauvegarde` | Réglages d'usage dans l'appli (fichier `reglages.json`), copie nocturne chez l'Anneau, « Restaurer les réglages » |
| Lecture seule | `MAISON_LECTURE_SEULE=oui` (ou `APP_LECTURE_SEULE` pour le socle seul) | Modèle de route gardée (`exiger_ecriture`), bandeau dans l'interface |
| Composants | `frontend/src/lib/components/ui/` | Bouton, carte, pastille, avancement, graphique, séparateur (shadcn-svelte, style « nova ») |
| Thème | `frontend/src/app.css` | Minimalisme, toujours sombre |
| Tests | `tests/` | API, module commun, écrans sur PC et iPhone (Playwright) |
| Image | `Dockerfile` | Construction en 3 étapes, publiée sur ghcr.io par GitHub Actions |

## Déployer sur le NAS (Portainer)

1. Dans la stack `homelab.yml`, ajouter le service de `docker-compose.yml`.
2. Dans les variables de la stack : `MAISON_PASSWORD` (12 caractères au moins), `MAISON_JETON` (pour la sauvegarde des réglages par l'Anneau), `ANNEAU_CLE` (pour que l'Anneau lise les fiches « Connexion ») et `SOCLE_DATA_DIR` (voir `.env.example`).
3. Créer le dossier indiqué dans `SOCLE_DATA_DIR` avec File Station.
4. Mettre à jour la stack, puis ouvrir `http://<adresse du NAS>:8090`.

Vérification attendue : l'écran de connexion s'affiche, le mot de passe ouvre la synthèse, la tuile « Dossier de données » indique « Écriture possible ».

## Changer la couleur d'une appli

Dans `frontend/src/app.css`, modifier `--app` et `--app-contraste` (une valeur pour le sombre, une pour le clair). Tout le reste suit.

## Ajouter un composant shadcn-svelte

Depuis un poste qui atteint le registre officiel :

```sh
cd frontend && npx shadcn-svelte@latest add dialog
```

Sinon, depuis une copie locale du dépôt officiel :

```sh
git clone --depth 1 https://github.com/huntabyte/shadcn-svelte ../shadcn-svelte
node tools/shadcn-local.mjs ../shadcn-svelte nova dialog
```

## Développer

```sh
pip install -r requirements-dev.txt
MAISON_PASSWORD=un-mot-de-passe-long APP_DATA=./data uvicorn app.main:app --port 8090
cd frontend && npm ci && npm run dev      # interface sur http://localhost:5173
cd frontend && npx vite build && cd ..    # interface compilée : nécessaire aux tests d'écran
python -m playwright install chromium        # navigateur des tests d'écran
python -m pytest -q
```

## Sécurité

- Aucun secret ni donnée personnelle dans ce dépôt : tout passe par les variables de la stack.
- L'appli refuse de démarrer sans `MAISON_PASSWORD` d'au moins 12 caractères.
- `/externe/sauvegarde` ne s'ouvre qu'au jeton commun (`MAISON_JETON`) et ne rend que les réglages d'usage, jamais un secret ni une variable.
- `/api/maison/services` (fiches « Connexion », contrat 3) s'ouvre à la session ou à `ANNEAU_CLE`, jamais à `MAISON_JETON` ; « Vérifier » n'écrit rien, au plus un essai toutes les 30 s.
- Toutes les routes `/api/` exigent une session, sauf la connexion ; `/health` est publique et ne dit que la version.
- Versions épinglées (`requirements.txt`, `package.json`) ; retour arrière par l'étiquette de l'image (`SOCLE_VERSION`).

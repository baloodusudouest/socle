# socle

Squelette commun des applis auto-hébergées : **FastAPI** + **Svelte 5** + **Tailwind 4** + **shadcn-svelte**, servi par un seul conteneur Docker.

C'est un **modèle à copier** : une nouvelle appli part d'une copie de ce dépôt, puis change son nom, sa couleur et ses écrans.

Le format commun des applis (navigation, tuiles, Connexion, Réglages, couleurs, règles de sécurité, méthode) est décrit dans [`docs/format.md`](docs/format.md).

## Ce que contient la version 0.2.0

| Élément | Où | Rôle |
|---|---|---|
| API | `app/` | Santé, connexion par mot de passe, mesures réelles du conteneur |
| Interface | `frontend/` | Rail et pilule, écran de synthèse en tuiles, « Connexion » (une tuile par service), « Réglages », planche des composants |
| Lecture seule | `APP_LECTURE_SEULE=oui` | Modèle de route gardée (`exiger_ecriture`), bandeau dans l'interface |
| Composants | `frontend/src/lib/components/ui/` | Bouton, carte, pastille, avancement, graphique, séparateur (shadcn-svelte, style « nova ») |
| Thème | `frontend/src/app.css` | Minimalisme, sombre par défaut, clair si l'appareil le demande |
| Tests | `tests/` | 8 tests de l'API |
| Image | `Dockerfile` | Construction en 3 étapes, publiée sur ghcr.io par GitHub Actions |

## Déployer sur le NAS (Portainer)

1. Dans la stack `homelab.yml`, ajouter le service de `docker-compose.yml`.
2. Dans les variables de la stack, ajouter `APPS_PASSWORD` (12 caractères au moins) et `SOCLE_DATA_DIR` (voir `.env.example`).
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
APP_PASSWORD=un-mot-de-passe-long APP_DATA=./data uvicorn app.main:app --port 8090
cd frontend && npm ci && npm run dev      # interface sur http://localhost:5173
python -m pytest -q
```

## Sécurité

- Aucun secret ni donnée personnelle dans ce dépôt : tout passe par les variables de la stack.
- L'appli refuse de démarrer sans mot de passe d'au moins 12 caractères.
- Toutes les routes `/api/` exigent une session, sauf la connexion ; `/health` est publique et ne dit que la version.
- Versions épinglées (`requirements.txt`, `package.json`) ; retour arrière par l'étiquette de l'image (`SOCLE_VERSION`).

# Reprise — socle

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (14/11/2026)

- **0.4.0** (14/11/2026) : page « Documents » (`frontend/src/pages/Documents.svelte`) ; les .md sont importés en `?raw` au moment de compiler. Une appli partie du socle retire cette page, comme « Composants ».
- **0.3.2** (14/11/2026) : `docs/lecons.md` complété (§ 11 à 14), `docs/format.md` à jour (toujours sombre, couleurs des sept applis, adresses à jeton, relevé des écarts au § 7). Pas de changement de code.
- **0.3.1** (13/11/2026) : toujours sombre (blocs `prefers-color-scheme: light` retirés, variante `dark:` partout).
- **Version 0.3.0** (13/11/2026) : connexion commune (cookie `maison_session`, `Sessions.connecte`) ; [`docs/lecons.md`](docs/lecons.md), à lire avant de créer une appli ; `CHANGELOG.md`. La connexion commune est en service dans les sept applis maison (carnet, Millésime, vérification des dates, kit d'urgence, Transhumance, Sillage, l'Anneau).
- Le socle a un mot de passe depuis la 0.1.0 (`APP_PASSWORD`, douze caractères au moins). Dans la stack, il reçoit désormais le même mot de passe que les autres applis, sans quoi la connexion commune ne joue pas.
- **Version 0.2.0** (11/11/2026) : le format commun, éprouvé sur carnet, Millésime et la vérification des dates, est écrit dans [`docs/format.md`](docs/format.md) ; le squelette gagne « Connexion », « Réglages », le mode lecture seule et les neutres chauds. 8 tests verts.
- Version 0.1.0 : squelette de test, image construite par GitHub Actions et publiée sur ghcr.io.
- **Déployé sur le NAS le 11/11/2026** dans homelab.yml (port 8090, volume `${DOCKER_ROOT}/socle`, variable `APPS_PASSWORD`). Vérifié sur place : connexion, synthèse en tuiles avec graphique, écriture dans /data.
- Conclusion du test : Svelte 5 + Tailwind 4 + shadcn-svelte tient sur le DS1520+. shadcn-svelte est retenu pour Frise.

## Prochaine étape

1. Trancher les écarts restants du § 7 de `docs/format.md` à la réouverture de chaque appli (les trois ors : tranché le 14/11, l'or reste à l'Anneau).
2. Tenir `docs/lecons.md` à jour à la fin de chaque chantier, générique et anonymisé.

## Décisions tranchées

- Svelte 5 + Vite 6 sans SvelteKit, comme carnet et Millésime.
- shadcn-svelte, style « nova ». Les composants sont copiés dans le dépôt, pas installés.
- Sombre par défaut ; le clair suit le réglage de l'appareil, sans bouton dans l'appli.
- Un mot de passe commun à toutes les applis (`APPS_PASSWORD`), SSO plus tard avec l'Anneau unique.
- Connexion reprise de carnet (cookie signé, génération écrite dans /data).
- Animations : transitions natives de Svelte ; motion.dev seulement pour Frise.

## Pièges

- L'écran « Connexion » (les services) est `pages/Services.svelte` ; `pages/Connexion.svelte` est la page du mot de passe. Même piège dans carnet et Millésime.
- Les neutres du socle étaient froids (teinte 260) ; ils sont maintenant ceux de carnet. Ne pas revenir en arrière : le froid a été refusé.
- Le registre shadcn-svelte.com n'est pas joignable depuis l'environnement de Claude : utiliser `tools/shadcn-local.mjs`.
- Les sources shadcn-svelte utilisent des classes abstraites `cn-…` ; elles ne marchent pas copiées telles quelles, il faut passer par l'outil ou la commande officielle.
- Le graphique (LayerChart) pèse lourd : l'interface fait 562 Ko (172 Ko compressée), contre quelques dizaines sans lui. À charger à la demande dans une appli qui n'affiche pas de graphique dès l'accueil.
- `APP_PASSWORD` de moins de 12 caractères : le conteneur s'arrête au démarrage, voir ses journaux dans Portainer.

## Non-objectifs

- Pas de base de données dans le socle : chaque appli apporte la sienne.
- Pas de paquet partagé entre applis.

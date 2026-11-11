# Reprise — socle

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- Version 0.1.0 : squelette de test. 7 tests verts, image construite par GitHub Actions et publiée sur ghcr.io.
- **Déployé sur le NAS le 11/11/2026** dans homelab.yml (port 8090, volume `${DOCKER_ROOT}/socle`, variable `APPS_PASSWORD`). Vérifié par Julien : connexion, synthèse en tuiles avec graphique, écriture dans /data.
- Conclusion du test : Svelte 5 + Tailwind 4 + shadcn-svelte tient sur le DS1520+. shadcn-svelte est retenu pour Frise.

## Prochaine étape

1. Frise : étape 0, sonde d'Immich (dans le dépôt de Frise).
2. Après Frise : écrire ici le document du socle (stack, déploiement, design, connexion, sécurité) à partir de ce qui a marché, et la planche de couleurs.
3. Juger le design à l'usage : une semaine sur iPhone et tablette avant de le généraliser.

## Décisions tranchées

- Svelte 5 + Vite 6 sans SvelteKit, comme carnet et Millésime.
- shadcn-svelte, style « nova ». Les composants sont copiés dans le dépôt, pas installés.
- Sombre par défaut ; le clair suit le réglage de l'appareil, sans bouton dans l'appli.
- Un mot de passe commun à toutes les applis (`APPS_PASSWORD`), SSO plus tard avec l'Anneau unique.
- Connexion reprise de carnet (cookie signé, génération écrite dans /data).
- Animations : transitions natives de Svelte ; motion.dev seulement pour Frise.

## Pièges

- Le registre shadcn-svelte.com n'est pas joignable depuis l'environnement de Claude : utiliser `tools/shadcn-local.mjs`.
- Les sources shadcn-svelte utilisent des classes abstraites `cn-…` ; elles ne marchent pas copiées telles quelles, il faut passer par l'outil ou la commande officielle.
- Le graphique (LayerChart) pèse lourd : l'interface fait 562 Ko (172 Ko compressée), contre quelques dizaines sans lui. À charger à la demande dans une appli qui n'affiche pas de graphique dès l'accueil.
- `APP_PASSWORD` de moins de 12 caractères : le conteneur s'arrête au démarrage, voir ses journaux dans Portainer.

## Non-objectifs

- Pas de base de données dans le socle : chaque appli apporte la sienne.
- Pas de paquet partagé entre applis.

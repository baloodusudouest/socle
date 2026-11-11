# Reprise — socle

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (11/11/2026)

- Version 0.1.0 : squelette de test. API, interface et tests fonctionnent en local (7 tests verts, interface compilée, écrans vérifiés en sombre et clair, PC et iPhone).
- **Pas encore fait** : image Docker jamais construite (pas de Docker dans l'environnement de développement), jamais déployée sur le NAS.

## Prochaine étape

1. Pousser le dépôt sur GitHub, vérifier que les deux workflows passent (tests, image).
2. Déployer dans homelab.yml et faire la vérification du README.
3. Si le déploiement tient : shadcn-svelte est confirmé pour Frise. Sinon : le retirer du plan.

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

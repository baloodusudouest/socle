# Reprise — socle

Fichier à lire en premier dans une nouvelle session, et à mettre à jour à chaque fin de session, dans le même commit que le code.

## État (23/11/2026) — 0.12.2 : listes déroulantes lisibles en sombre (`app.css`, bloc « Listes déroulantes (socle 0.12.2) », leçon § 24), recopié dans les applis le même jour sauf Transhumance.

## État (22/11/2026) — 0.12.1 : barre d'onglets collée en bas sur iPhone (`App.svelte`, `format.md`, `lecons.md`), recopiée dans les applis le même jour.

## État (21/11/2026)

- **0.12.0** (21/11/2026) : client Paperless commun `app/paperless.py` (signé, diffusé par `tools/diffuser_maison.py --paperless`) et faux Paperless des tests `tests/faux_paperless.py`. Premières applis : Gazette, Dîme. `maison.py` inchangé. **Jamais essayé sur la vraie installation.**
- **0.11.1** (20/11/2026) : titre « Pour le relier » quand `reglage` parle de Réglages ; rediffusé aux applis.
- **0.11.0** (20/11/2026) : guide facultatif d'une fiche (`guide=`, `nettoyer_guide`), demandé par Julien pour que le calcul du PC ait les mêmes informations que l'IA du PC.
- **0.10.0** (20/11/2026, chantier « fiches Connexion », dossier et conseil `fiches-connexion-*.md` dans le projet Claude) : contrat 3 dans `maison.py` (registre `Services`, `monter_services`, `ANNEAU_CLE`), interface commune `frontend/src/lib/services/` (signée et diffusée comme `maison.py`). Diffusé aux applis dans le même chantier (ordre : Douze points, l'Anneau, puis les autres). **Jamais essayé sur la vraie installation.**
- **0.9.0** (18/11/2026, chantier « santé des tâches de fond (E2) et copie des bases (E3) », dossier `sante-et-copies-dossier.md` § 5) : `maison.py` gagne `VERSION_SOCLE`, le registre `TACHES` (`declarer`, `tour`, `tour_async`, `etat`), `masquer_secrets`/`message_erreur`, `copier_bases`, `copie_base_etat`, `prochaine_copie`, `planifier_copie`, `HEURES_COPIE` et `sante()` (champs `version_socle`, `taches`, `copie_base` de `/health`). `CONTRAT` reste 2 (les tests des applis le vérifient). Signé ; **pas encore diffusé** aux applis (le coordinateur le fait). Le `/health` du socle montre les nouveaux champs. Tests : `tests/test_sante.py`. Un seul worker uvicorn (déjà le cas, `entrypoint.sh`). **Jamais essayé sur la vraie installation** ; la restauration depuis une copie est à répéter sur carnet avant de dire E3 fini.
- **0.8.2** (18/11/2026) : `est_secret` par mots, `valeur_secrete` (adresse avec identifiant), champ `ecartes` dans la sauvegarde (audit M3). Diffusé aux 12 applis.
- **0.8.1** (18/11/2026) : cookies `Secure` en https (`auth.en_https`) ; `entrypoint.sh` refuse root (`MAISON_ROOT_ACCEPTE=oui` en dépannage). Même correctif dans les 12 applis (refus de root seulement là où il y a gosu : pas Millésime, Transhumance, Éphéméride).
- **0.8.0** (18/11/2026, audit du 17/11) : révocation du cookie commun. `maison_session` vaut « génération.expiration.signature » ; la génération est celle des sessions de l'Anneau, publiée dans `/externe/services` (`generation_commune`) ; `maison.generation_commune()` (relue au plus toutes les minutes, jamais bloquante ; `None` si l'Anneau ne répond pas → cookie accepté) ; l'Anneau se déclare par `maison.definir_generation_commune()`. Copié dans les 12 applis. Voir `docs/lecons.md` § 3.
- **0.7.0** (17/11/2026) : clés des cookies par PBKDF2, comparaisons en octets, 30 essais en 5 minutes au plus ; annuaire relu 30 s après un échec.
- **0.6.0** (16/11/2026) : chantier B « réglages dans l'appli, sauvegarde et restauration » et nettoyage des anciens noms.
  - `app/maison.py` passe au **contrat 2** (`Reglages`, `est_secret`, `reglages_publics`, `sauvegarde`, `differences`, `lire_sauvegarde`) ; signé par `python tools/diffuser_maison.py` (sans argument) ; déjà copié dans les applis.
  - Implémentation de référence : `app/main.py` (`REGLAGES_DEFAUTS`, `REGLAGES_VARIABLES`, `EXCLUS_SAUVEGARDE`, routes `/api/reglages`, `/externe/sauvegarde`, `/api/restaurer`), `frontend/src/pages/Reglages.svelte` (tuiles « Réglages » et « Restaurer les réglages »), `pages/Synthese.svelte` (les deux réglages de démonstration y jouent). Fichier `reglages.json` dans `/data`.
  - Réglages : `message_accueil` (texte, défaut vide, repris une fois de `APP_MESSAGE_ACCUEIL`), `afficher_mesures` (oui/non, défaut oui). Aucune clé exclue de la sauvegarde (`EXCLUS_SAUVEGARDE = ()`, liste explicite).
  - Variables lues : `MAISON_PASSWORD`, `MAISON_JETON`, `MAISON_JETON_ANCIEN`, `MAISON_LECTURE_SEULE`, `APP_LECTURE_SEULE` (forçage), `MAISON_ANNEAU_URL` (facultatif), `APP_DATA`, `APP_PORT` ; `APP_MESSAGE_ACCUEIL` au premier démarrage seulement. **`APP_PASSWORD` n'est plus lu.**
  - Tests : `tests/test_maison.py` (contrat 2 complet), `tests/test_reglages.py` (API), `tests/test_ecran.py` (Réglages et Restaurer sur PC et iPhone ; la CI compile l'interface et installe Chromium).
  - **Déploiement en deux temps** : d'abord la nouvelle image avec la stack actuelle (les réglages sont repris des anciennes variables au premier démarrage), vérifier Réglages, puis la nouvelle stack sans les anciennes lignes. Pour le socle : ajouter `MAISON_JETON` (sinon l'Anneau ne peut pas lire la sauvegarde) et vérifier que `MAISON_PASSWORD` est rempli **avant** de retirer la ligne `APP_PASSWORD` : sans lui, le conteneur ne démarre plus.
  - **Jamais essayé sur la vraie installation** : ni la reprise, ni la collecte par l'Anneau, ni Restaurer contre le vrai Anneau (seulement contre un faux, dans les tests).
- **0.5.0** (16/11/2026) : module commun `app/maison.py` (contrat 1 : `MAISON_PASSWORD`, `MAISON_JETON`, `MAISON_LECTURE_SEULE`, annuaire de l'Anneau) ; `tools/diffuser_maison.py` le signe et le copie dans les applis. Chantier « variables rationalisées » (dossier dans le projet Claude : `maison-variables-sauvegarde-dossier.md`).
- **0.4.3** (14/11/2026) : `docs/lecons.md` § 19, appris en construisant Scriptorium (gros fichiers, Tesseract, lecture en ligne, EPUB). Pas de changement de code.
- **0.4.0** (14/11/2026) : page « Documents » (`frontend/src/pages/Documents.svelte`) ; les .md sont importés en `?raw` au moment de compiler. Une appli partie du socle retire cette page, comme « Composants ».
- **0.3.2** (14/11/2026) : `docs/lecons.md` complété (§ 11 à 14), `docs/format.md` à jour (toujours sombre, couleurs des sept applis, adresses à jeton, relevé des écarts au § 7). Pas de changement de code.
- **0.3.1** (13/11/2026) : toujours sombre (blocs `prefers-color-scheme: light` retirés, variante `dark:` partout).
- **Version 0.3.0** (13/11/2026) : connexion commune (cookie `maison_session`, `Sessions.connecte`) ; [`docs/lecons.md`](docs/lecons.md), à lire avant de créer une appli ; `CHANGELOG.md`. La connexion commune est en service dans les sept applis maison (carnet, Millésime, vérification des dates, kit d'urgence, Transhumance, Sillage, l'Anneau).
- Le socle a un mot de passe depuis la 0.1.0 (`APP_PASSWORD` jusqu'à la 0.5.0, `MAISON_PASSWORD` seul depuis la 0.6.0, douze caractères au moins). Il reçoit le même mot de passe que les autres applis, sans quoi la connexion commune ne joue pas.
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
- Un mot de passe commun à toutes les applis (`MAISON_PASSWORD` depuis le 16/11/2026), connexion commune par le cookie de l'Anneau.
- Les réglages d'usage vivent dans l'appli (écran Réglages), pas dans la stack ; l'Anneau en garde une copie chaque nuit (16/11/2026).
- Connexion reprise de carnet (cookie signé, génération écrite dans /data).
- Animations : transitions natives de Svelte ; motion.dev seulement pour Frise.

## Pièges

- Paperless 3 (sonde du 21/11/2026) : doublons acceptés, tâches introuvables par `task_id`, un compte ne voit que ses envois et ce qu'une règle lui ouvre. D'où `FileEnvois` : titre unique, recherche avant et après l'envoi, jamais de renvoi automatique. Un renvoi voulu change de titre.

- `maison.TACHES` et la dernière copie vivent en mémoire du processus : jamais `--workers` > 1 dans `uvicorn`. Une copie prévue mais pas encore faite répond `copie_base: {"le": null, "ok": false, …}`.

- L'écran « Connexion » (les services) est `$lib/services/Services.svelte` (commun, signé : ne pas le retoucher dans une appli) ; `pages/Connexion.svelte` est la page du mot de passe.
- `maison.monter_services` doit être appelé **après** les autres `@app.middleware` : le dernier ajouté passe en premier. Appelé avant, la garde de l'appli refuse l'Anneau (401).
- Les neutres du socle étaient froids (teinte 260) ; ils sont maintenant ceux de carnet. Ne pas revenir en arrière : le froid a été refusé.
- Le registre shadcn-svelte.com n'est pas joignable depuis l'environnement de Claude : utiliser `tools/shadcn-local.mjs`.
- Les sources shadcn-svelte utilisent des classes abstraites `cn-…` ; elles ne marchent pas copiées telles quelles, il faut passer par l'outil ou la commande officielle.
- Le graphique (LayerChart) pèse lourd : l'interface fait 562 Ko (172 Ko compressée), contre quelques dizaines sans lui. À charger à la demande dans une appli qui n'affiche pas de graphique dès l'accueil.
- `MAISON_PASSWORD` absent ou de moins de 12 caractères : le conteneur s'arrête au démarrage, voir ses journaux dans Portainer. L'ancien `APP_PASSWORD` ne suffit plus (0.6.0).
- Retirer de la stack une variable de réglage **avant** le premier démarrage de la nouvelle image fait perdre sa valeur : déploiement en deux temps.
- `maison.est_secret` écarte aussi des noms innocents (`boucle`, `max_articles`, `user_agent`) : un réglage absent de la sauvegarde se renomme.

## Non-objectifs

- Pas de base de données dans le socle : chaque appli apporte la sienne.
- Pas de paquet partagé entre applis.

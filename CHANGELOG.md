# Journal des versions

## 0.12.1 — 22 novembre 2026 (barre d'onglets collée en bas)
- **iPhone : la barre d'onglets est collée au bord bas**, sur toute la largeur (choix de Julien, 22/11/2026, pour toutes les applis maison), au lieu de la pilule flottante. Le rail des PC ne change pas. `App.svelte`, `docs/format.md` (Navigation), leçon dans `docs/lecons.md`.
- Recopié à la main dans chaque appli (le gabarit de navigation n'est pas un fichier commun signé).

## 0.12.0 — 21 novembre 2026 (client Paperless commun)
- Nouveau fichier commun **`app/paperless.py`** (bibliothèque standard, signé comme `maison.py`), pour les applis qui rangent ou lisent des papiers dans Paperless-ngx (Gazette, Dîme ; carnet plus tard). Dossier « Paperless – Gazette et Dîme » v0.3 et sa sonde (coffre, 21/11/2026).
  - `Paperless(url, jeton, lecture_seule=, transport=)` : `regle`, `essai`, `etiquette`/`type_document` (retrouvés par le nom exact, créés avec l'appariement désactivé), `chercher_titre`, `envoyer_brut`, `documents(etiquette)` (toutes les pages), `texte` (champ `content`, jamais de nouvel OCR), `telecharger` (original). En-tête `Accept: application/json; version=10`. Aucune suppression.
  - `FileEnvois` : file locale (fichier JSON, ou `charger`/`sauver` fournis par l'appli), **un envoi à la fois**, titre unique exigé, recherche du titre avant d'envoyer, document **retrouvé par son titre** après l'envoi (les tâches de Paperless 3 sont introuvables par leur `task_id`), **jamais de renvoi** d'un envoi parti (Paperless 3 accepte les doublons) : « à vérifier » après 30 min, `reprendre` relance seulement la recherche ; panne réseau : nouvel essai 10 min plus tard ; la file ne garde jamais de PDF (l'appli fournit `lire_source`).
  - `declarer_service(services, client, file, lit=, ecrit=, reglage=)` : fiche « Connexion » `paperless` (contrat 3), détail avec les envois en attente et à vérifier.
- `tests/faux_paperless.py` : faux Paperless d'après les formes relevées par la sonde (propriétaire, droits, doublons acceptés, délai de traitement), copié dans les applis avec le client ; `tests/test_paperless.py` (18 tests).
- `tools/diffuser_maison.py --paperless <applis>` signe et copie `app/paperless.py` et `tests/faux_paperless.py`.
- `maison.py` inchangé (`VERSION_SOCLE` reste 0.11.1, contrat 3) : rien à rediffuser aux applis qui n'utilisent pas Paperless.
- **Jamais essayé sur la vraie installation** : seulement contre le faux Paperless (la sonde, elle, a tourné sur la vraie).

## 0.11.1 — 20 novembre 2026 (« Pour le relier » quand ce n'est pas la stack)
- `FicheService.svelte` : quand le champ `reglage` parle de Réglages (un réglage de l'appli : recherche Wikidata de Comptoir, Larousse de Gazette, adresse de la liseuse du kit, tags de Sillage), le titre devient « Pour le relier » au lieu de « Pour le relier, dans la stack ». Relevé par les applis passées au contrat 3 le même jour.

## 0.11.0 — 20 novembre 2026 (guide d'une fiche « Connexion »)
- Une fiche peut porter un **guide** (facultatif, `SERVICES.ajouter(..., guide=…)`) pour un service qu'on allume et répare soi-même (PC de calcul, IA du PC), au format de la fiche « IA du PC » de Gazette : réglages lus (adresse appelée, modèle…), « Allumer normalement », « En cas de problème » (signes dépliables, quoi faire, commandes avec « Copier »), « Installation (une seule fois) », une note. Relu et borné par `maison.nettoyer_guide` (secrets masqués) ; un guide illisible n'empêche pas la fiche.
- `FicheService.svelte` l'affiche sous les boutons ; l'Anneau le montre aussi dans sa fiche « État ».
- `VERSION_SOCLE = "0.11.0"` ; le contrat reste 3 (champ ajouté, facultatif).

## 0.10.0 — 20 novembre 2026 (fiches « Connexion » communes, contrat 3)
- **Contrat 3** dans `maison.py` (`CONTRAT = 3`, `VERSION_SOCLE = "0.10.0"`) : registre `Services` (`ajouter`, `liste`, `verifier`, `verifier_async`, `noter`), `monter_services(app, registre, session_ok)` qui branche `GET /api/maison/services` et `POST /api/maison/services/{id}/verifier` avant la garde de l'appli ; `cle_anneau`, `cle_anneau_valide`, `nettoyer_detail`, `adresse_anneau`, `essai_http`, `empreinte_interface`.
- Le GET ne lance aucun essai : il rend le dernier résultat et son âge. « Vérifier » : un essai léger, au plus un toutes les 30 s par service, arrêté au bout de 8 s, sans écriture (permis en lecture seule). Détail nettoyé (secrets, adresses, hôtes ; 160 caractères).
- **`ANNEAU_CLE`** (nouvelle variable) : clé de lecture de l'Anneau, n'ouvre que ces deux routes ; se change seule. `MAISON_JETON` n'ouvre pas les fiches.
- **Interface commune** `frontend/src/lib/services/` : `FicheService.svelte` (point, état en mots, Ce qui est lu, Ce qui est écrit, Pour le relier, âge de l'essai, Vérifier en contour, un geste plein) et `Services.svelte` (1 à 3 services : fiches dépliées ; 4 et plus : tuiles à voyant, fiche dessous, focus, Échap, `aria-expanded`, résultat annoncé). Signées et copiées par `tools/diffuser_maison.py` comme `maison.py`.
- Le socle : son écran « Connexion » passe à l'écran commun (un service : l'Anneau) ; la tuile « Dossier de données » va dans Réglages. `pages/Services.svelte` est retiré.
- Tests : `tests/test_services.py` (contrat, accès, limite, détail nettoyé, essais asynchrones, empreintes), `tests/test_ecran.py` (seuil de 3, tuiles, Échap, Vérifier, PC et iPhone).
- **Jamais essayé sur la vraie installation.**

## 0.9.1 — 18 novembre 2026 (copie d'une base chiffrée)
- `copier_bases` et `planifier_copie` acceptent `ouvrir(chemin, lecture_seule)` : une appli à base chiffrée (carnet, SQLCipher) passe sa propre ouverture ; la copie reste chiffrée avec la même clé. Par défaut, SQLite en clair comme en 0.9.0.

## 0.9.0 — 18 novembre 2026 (santé des tâches et copie des bases)
- **Santé des tâches de fond** (chantier E2) : module commun `maison.py` (socle 0.9.0, `VERSION_SOCLE`) : registre `maison.TACHES` (classe `Taches`, en mémoire, protégé par un verrou) ; `declarer(nom, periode_s, type="reguliere"|"demande")`, `tour(nom)` et `tour_async(nom)` marquent le début, la réussite ou l'erreur ; `etat(avec_messages)` donne chaque tâche au format du contrat (`ok`, `en_retard`, `bloquee`, `jamais`, et `erreur` pour une tâche à la demande). Les messages d'erreur gardent le type et la première ligne, 160 caractères au plus, et passent par un filtre qui masque tout ce qui ressemble à un secret (adresse avec identifiants, `token=…`, `Bearer …`).
- **`/health` gagne `version_socle`, `taches` et `copie_base`** (`maison.sante(request, jeton_commun, session_ok)`) ; rien d'existant ne change. Les messages n'y sont que si la requête porte le jeton commun (comparé en temps constant) ou une session valide. Le `/health` du socle les montre (pas de tâche ni de base : `taches` vide, `copie_base` null).
- **Copie cohérente des bases SQLite** (chantier E3) : `maison.copier_bases(chemins, dossier)` (API de sauvegarde de SQLite, `integrity_check` sur la copie, `<base>-derniere.db` écrasée chaque nuit, toutes les bases d'une appli ensemble, copie abîmée effacée) ; dernier résultat gardé en mémoire et dans `<dossier>/copie.json` (`maison.copie_base_etat()`). `maison.planifier_copie(appli, chemins, dossier)` : copie de nuit à l'heure de Paris de l'appli (`HEURES_COPIE`, 01:00 à 02:20), dans un fil à part, suivie par la tâche régulière `copie-des-bases`.
- Le module suppose **un seul worker uvicorn** (écrit dans son en-tête) : c'est le cas du socle et de ses applis.
- Tests : `tests/test_sante.py` (états avec une horloge injectable, filtre des secrets, copie pendant une écriture, intégrité ratée, heure de Paris avec `TZ=UTC`, messages absents sans jeton). `docs/lecons.md` § 22.
- **Jamais essayé sur la vraie installation** : ni la copie de nuit sur le NAS, ni une restauration depuis une copie.

## 0.8.2 — 18 novembre 2026 (constats moyens de l'audit)
- **Réglages secrets reconnus par mots** (audit M3) : `maison.est_secret` découpe le nom (`camelCase`, `_`, `-`, `.`) et reconnaît les mots qui trahissent un secret (password, pass, mdp, token, jeton, cle, key, code, login, email, webhook, session…), même collés (« motdepasse », « apikey ») ; quelques paires inoffensives restent publiques (code postal, mot-clé, clé de tri). Une valeur qui est une adresse avec identifiant (`https://nom:mot@…`) est écartée quel que soit son nom.
- La sauvegarde des réglages (`/externe/sauvegarde`) dit maintenant **ce qu'elle a écarté** : champ `ecartes` (noms seulement, jamais les valeurs), pour que l'Anneau montre qu'un réglage n'est pas sauvegardé.

## 0.8.1 — 18 novembre 2026 (cookies Secure)
- **Cookies `Secure` en https** (audit du 17/11/2026, même correctif dans toutes les applis maison) : ouverte en https (directement, derrière Tailscale Serve qui le dit par `X-Forwarded-Proto`, ou d'après l'origine de la page), l'appli pose ses cookies de session avec l'attribut `Secure` : ils ne partent jamais en clair. En http (adresse locale), rien ne change.
- `entrypoint.sh` refuse de lancer l'appli en root quand `/data` appartient à root (dossier créé par Docker) et dit le remède ; dépannage seulement : `MAISON_ROOT_ACCEPTE=oui`.

## 0.8.0 — 18 novembre 2026 (révocation du cookie commun)
- **« Se déconnecter » dans l'Anneau ferme vraiment la connexion commune** (audit du 17/11/2026, même correctif dans toutes les applis maison) : le cookie commun `maison_session` porte maintenant la génération tenue par l'Anneau (« génération.expiration.signature ») ; « Se déconnecter » l'augmente, et chaque appli la lit dans l'annuaire de l'Anneau (`/externe/services`, au plus une minute de retard) : un cookie commun d'avant la déconnexion ne vaut plus nulle part. Si l'Anneau ne répond pas, le cookie reste accepté comme avant (rien ne se bloque). **Toutes les applis doivent être à jour ensemble** ; une seule reconnexion est demandée après la mise à jour.
- Module commun `maison.py` (socle 0.8.0) : `generation_commune()`, `definir_generation_commune()` ; l'annuaire lit aussi `generation_commune` (une ancienne réponse de l'Anneau, liste seule, reste lue).

## 0.7.0 — 17 novembre 2026 (connexion plus sûre)
- **Connexion plus sûre** (audit du 17/11/2026, même correctif dans toutes les applis maison) :
  - un cookie portant un caractère non ASCII donnait une erreur 500 sur toute l'API ; il est maintenant simplement refusé ;
  - les clés qui signent les cookies (celui de l'appli et le cookie commun `maison_session` posé par l'Anneau) sont tirées du mot de passe par PBKDF2 : un cookie capté sur le réseau local ne permet plus de chercher le mot de passe à grande vitesse. **Toutes les applis doivent être à jour ensemble** ; une seule reconnexion est demandée après la mise à jour ;
  - des essais de mot de passe lancés en parallèle ne contournent plus le délai : au-delà de 30 essais en 5 minutes, tout est refusé sans comparer.
- Module commun `maison.py` (socle 0.7.0) : l'annuaire de l'Anneau est relu 30 s après un échec (avant : 10 min sans adresses après un redémarrage de la stack) ; un réglage `nan` ou infini est refusé ; un `reglages.json` abîmé est mis de côté (`.corrompu`) au lieu d'être écrasé.

## 0.6.0 — 16 novembre 2026
- **Module commun `app/maison.py`, contrat 2** : réglages d'usage (`Reglages` : fichier JSON dans le dossier de données, reprise de l'ancienne variable une seule fois au premier démarrage, écriture atomique), `est_secret`, `reglages_publics`, `sauvegarde`, `differences`, `lire_sauvegarde`, contrat de sauvegarde 1. Déjà copié dans les applis maison.
- **Réglages dans l'appli** (modèle pour toutes les applis) : deux réglages de démonstration, « Message d'accueil » (texte, repris une fois de `APP_MESSAGE_ACCUEIL`) et « Graphique des appels » (oui/non) ; ils changent la Synthèse. `GET`/`PUT /api/reglages` ; un mauvais type répond 400 avec un message clair.
- **Sauvegarde pour l'Anneau** : `GET /externe/sauvegarde`, ouverte seulement par le jeton commun (`MAISON_JETON`), fermée s'il est vide ; réglages et version seulement, jamais de secret.
- **Restaurer les réglages** : nouvelle tuile dans Réglages ; on choisit une date gardée par l'Anneau, on voit les différences (avant → sauvegardé), on confirme. Anneau injoignable : un message clair. Permis même en lecture seule (ce sont les réglages de l'appli).
- **Anciens noms retirés** : `APP_PASSWORD` n'est plus lu, seulement `MAISON_PASSWORD`. `APP_LECTURE_SEULE` reste (forçage pour le socle seul), à côté de `MAISON_LECTURE_SEULE`. L'écran dit d'où vient la lecture seule.
- `docs/format.md` § 8 (motif Réglages et Restaurer, routes, contrat de sauvegarde 1, déploiement en deux temps) ; `docs/lecons.md` § 21.
- Tests : 109, dont les tests d'écran sur PC et iPhone (Playwright), désormais lancés aussi par GitHub Actions.

## 0.5.0 — 16 novembre 2026
- **Module commun `app/maison.py` (contrat 1)**, copié tel quel dans chaque appli par `tools/diffuser_maison.py` (empreinte en dernière ligne, vérifiée par le test de chaque appli). Bibliothèque standard seulement.
  - `mot_de_passe(*anciens)` : `MAISON_PASSWORD`, sinon l'ancienne variable de l'appli.
  - `lecture_seule(propre)` : `MAISON_LECTURE_SEULE` pour toute la maison ; la variable de l'appli, si elle dit oui ou non, l'emporte (essai d'une seule appli). `origine_lecture_seule` pour l'écran Réglages.
  - `jetons(*anciens)`, `jeton_valide`, `jeton_propose`, `jeton_a_envoyer` (l'ancien jeton de la paire passe d'abord tant qu'il est dans la stack) : jeton commun `MAISON_JETON` entre applis maison, `MAISON_JETON_ANCIEN` pendant un changement, anciens jetons par paire acceptés pendant la transition ; comparaison en temps constant ; vide = porte fermée. Home Assistant et le PC de calcul gardent leurs propres jetons.
  - `Annuaire` : adresses des autres services lues dans l'Anneau (`GET /externe/services`, jeton commun, `MAISON_ANNEAU_URL`), gardées dix minutes, adresse privée (Tailscale) quand la page vient de là (`est_prive`), repli sinon.
- Le socle lui-même lit `MAISON_PASSWORD` et `MAISON_LECTURE_SEULE` (repli sur `APP_PASSWORD`, `APP_LECTURE_SEULE`).
- `docs/lecons.md` § 20 : variables communes. Tests : 15 (dont 6 pour le module).

## 0.4.4 — 15 novembre 2026
- `docs/format.md` § 7 : écart de Transhumance sur la navigation retiré (Transhumance 0.5.0 a la pilule en bas et sa page Réglages). Pas de changement de code.

## 0.4.3 — 14 novembre 2026
- `docs/lecons.md` § 19 : envoi d'un gros fichier par morceaux avec reprise, tâche de fond qui reprend après un redémarrage, chiffres lus par Tesseract (liste blanche trompeuse, lecture libre de confirmation), service de lecture en ligne (une seule fonction, sortie douteuse, lecture seule), EPUB (liste des pages, repère de page, fichiers qui commencent à un titre, contrat avec l'appli lectrice), faux service remis en place après les tests ; § 15 : la première vraie donnée bat les données inventées (appris en construisant Scriptorium). Pas de changement de code.

## 0.4.2 — 14 novembre 2026
- `docs/format.md` : couleurs de Scriptorium, Comptoir et Gazette ajoutées au tableau.
- `docs/lecons.md` § 16 à 18 : un document imprimé (aperçu et PDF par le même HTML, polices embarquées, débordements mesurés), une source publique limitée (User-Agent, pauses, cache, textes non libres, SPARQL en POST), port publié et port du conteneur (appris en construisant Gazette). Pas de changement de code.

## 0.4.1 — 14 novembre 2026
- `docs/lecons.md` : écran allumé seulement en HTTPS, carte du monde embarquée, page source écrasée par sa version compilée, icône du squelette à remplacer (appris en construisant Comptoir). Pas de changement de code.

## 0.4.0 — 14 novembre 2026
- **Page « Documents »** : le format commun, les leçons apprises, la reprise et ce journal, lisibles dans l'appli (onglets, sommaire sur PC). Ils sont lus dans le dépôt au moment de compiler l'interface : rien n'est cherché sur le réseau, et l'appli dit toujours ce que dit le dépôt de la version installée.
- Nouvelle dépendance : `marked` (mise en forme du Markdown). Le Dockerfile copie `docs/`, `REPRISE.md` et `CHANGELOG.md` dans l'étape qui compile l'interface.

## 0.3.2 — 14 novembre 2026
- **[`docs/lecons.md`](docs/lecons.md) complété** (§ 11 à 14) : comparer avec ce qu'un service a gardé (normalisation CardDAV), dater d'après un nom de dossier (lots écartés, fourchettes), regrouper un chemin de vie, relire sans tout relire, ce qu'une API de photos a appris ; un choix fait à la main contre les règles automatiques, réponses dans le désordre, gestes qui ne valent qu'une fois, page à jeton pour un écran mural, cartes de tableau de bord qui avalent les clics ; applis qui s'enchaînent sans jamais enchaîner une suppression ; tests sur un serveur de démonstration partagé.
- **[`docs/format.md`](docs/format.md) mis à jour** : toujours sombre, couleurs des sept applis, règle des adresses à jeton (§ 3.1), et un relevé des écarts de chaque appli en service (§ 7).
- Commentaire de `app.css` remis d'accord avec le thème toujours sombre. Aucun changement de code.

## 0.3.1 — 13 novembre 2026
- **Toujours sombre.** Le thème clair est retiré : l'appli est sombre partout, ouverte seule comme dans l'Anneau, quel que soit le réglage du téléphone.

## 0.3.0 — 13 novembre 2026
- **Connexion commune.** Le socle accepte le cookie « maison_session » posé par le portail de la maison : connecté au portail, on n'a plus à se connecter ici, quand l'appli est servie par la même adresse que lui et qu'elle a le même mot de passe. `Sessions.connecte(cookies)` remplace `Sessions.valide(cookie)` dans la garde ; `Sessions.creer_commun()` sert à l'appli qui pose le cookie. « Se déconnecter » retire aussi le cookie commun.
- **[`docs/lecons.md`](docs/lecons.md)** : ce que les applis construites depuis le socle ont appris — partir du socle, connexion, affichage dans un cadre, téléphone, services extérieurs, surveillance, tests, publication, erreurs de fabrication. Générique et anonymisé.
- Tests : 9.

## 0.2.1 — 12 novembre 2026
- Icône de l'appli (onglet du navigateur, écran d'accueil du téléphone) et manifeste.

## 0.2.0 — 11 novembre 2026
- Le format commun des applis, écrit dans [`docs/format.md`](docs/format.md).
- Écrans « Connexion » (une tuile par service extérieur) et « Réglages » (version, déconnexion).
- Mode lecture seule (`APP_LECTURE_SEULE`) et garde `exiger_ecriture()` à placer devant toute écriture extérieure.
- Neutres chauds, sombre par défaut ; une seule couleur à changer par appli (`--app`).

## 0.1.0 — 11 novembre 2026
- Squelette de test : FastAPI, Svelte 5, Vite 6, Tailwind 4, shadcn-svelte. Mot de passe unique (douze caractères au moins), session par cookie signé, `/health` public, image publiée à chaque envoi.

# Journal des versions

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

# Journal des versions

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

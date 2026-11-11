# Le format commun des applis

Écrit le 11/11/2026, après l'avoir appliqué trois fois le même jour : carnet (2.9 et 2.10), Millésime (2.0) et la vérification des dates (2.0). Ce document dit ce qui a marché, ce que les conseils ont corrigé, et ce qu'une nouvelle appli doit reprendre.

Il remplace le « document du socle » annoncé dans `REPRISE.md`.

## 1. Ce qu'on retrouve dans chaque appli

| Élément | Règle |
|---|---|
| **Navigation** | Rail à gauche sur PC (900 px et plus), avec les noms. Pilule d'icônes flottante en bas sur iPhone, sans noms : le nom de la section est le titre de l'écran |
| **Entrées** | Peu : entre quatre et six. Toujours **Connexion** et **Réglages** ; presque toujours **À traiter** |
| **À traiter** | Une grille de tuiles, une par type de chose à faire, avec son nombre. Une tuile ouvre sa liste. Le compteur de l'onglet ne compte que ce qui attend une décision |
| **Connexion** | Une tuile par service extérieur, avec un voyant. Le service ouvert dit ce que l'appli y lit et y écrit, et porte ses gestes : **Vérifier** (compare, n'écrit rien) et **Synchroniser** (écrit ce qui est sûr, envoie le reste dans À traiter) |
| **Réglages** | Ce qui n'est pas un service : règles, journal des écritures avec Annuler, version, déconnexion |
| **Habillage** | Fonds neutres chauds, filets fins, sombre par défaut et clair quand l'appareil le demande, sans bouton. Inter. Titres d'écran grands et fins |
| **Couleur** | Une par appli. Elle porte l'action attendue (un seul bouton plein par bloc), l'onglet actif, les compteurs |
| **Signature** | Chaque appli garde ce qui la distingue (l'anneau de progression de carnet, l'année en Bodoni de Millésime) |

### Couleurs attribuées

| Appli | Couleur | Sombre | Clair |
|---|---|---|---|
| carnet | ocre | `#d9a441` | `#96690c` |
| Millésime | lie-de-vin | `#b8405f` | `#8e2a48` |
| vérification des dates | bleu ardoise | `#7f9cc4` | `#3f5d86` |
| socle (modèle) | bleu-vert | `--app` dans `app.css` | |

Neutres communs (sombre, puis clair) : fond `#151311` / `#faf7f2`, surface `#1f1c19` / `#f1ece3`, filet `#312c27` / `#e3dbcd`, texte `#f2ece2` / `#1e1a16`, texte secondaire `#a89e91` / `#6f665b`. Un premier essai en neutres froids a été jugé trop froid.

## 2. La règle qui passe avant le format

**Le geste répété ne passe jamais derrière une tuile.** carnet trie des cas variés de temps en temps : sa grille de tuiles est son écran d'ouverture. Millésime répète un seul geste des centaines de fois : il s'ouvre sur « Dater », et sa grille est une entrée à part. Le format sert le travail de l'appli, pas l'inverse (avis du conseil, Millésime 2.0).

Sur iPhone, dans un écran où l'on valide à la chaîne, la pilule s'efface pour ne rien laisser entre le pouce et le bouton ; un lien en haut ramène à la navigation.

## 3. Sécurité : ce que toute appli qui écrit doit avoir

1. **Mot de passe commun**, obligatoire : sans la variable, le conteneur ne démarre pas. Une seule adresse répond sans session, celle qui reçoit le mot de passe (attention à la méthode : une lecture sur le même chemin doit rester fermée), plus `/health`.
2. **Mode lecture seule** par une variable de la stack. Le refus se fait deux fois : à l'adresse appelée, avant toute trace dans un journal, et au plus près de l'écriture (client du service, fonction qui touche au fichier). Modèle : `exiger_ecriture` dans `app/main.py`.
3. **Un test qui fige ce qui est écrit** chez le service extérieur pour le geste principal. Une refonte d'interface ne doit pas pouvoir le faire échouer.
4. **Chaque écriture est journalisée**, avec la valeur d'avant, et peut s'annuler quand c'est possible.
5. **Remplir, jamais écraser** : une écriture automatique ne remplace pas une valeur existante ; deux valeurs différentes deviennent une question dans À traiter.
6. **Watchtower désactivé** pour toute appli qui écrit ; l'image de chaque version reste publiée pour le retour arrière.
7. **Revenir à une ancienne image ne défait pas ce qui a été écrit.** Avant une version qui change les écritures : sauvegarde du service touché.
8. **Rien de personnel dans un dépôt public** : ni noms de proches, ni dates de naissance, ni adresse du réseau, ni chemin d'un dossier personnel, ni nom d'album ou de tag réel. Les valeurs réelles passent par les variables de la stack, sans valeur par défaut dans le code ; les personnes des tests sont inventées. Contrôler aussi l'historique et les images déjà publiées.

## 4. Méthode

- **Nouvelle appli** : questions (grill), dossier en six sections, conseil, puis code.
- **Appli en service** : dossier « tel que construit », liste des écarts avec ce document, un passage au conseil sur les écarts, puis go.
- **Service extérieur** : une sonde courte en lecture seule avant le conseil.
- **Chaque dépôt** : `REPRISE.md` (à lire en premier, mis à jour dans le même commit que le code), `CHANGELOG.md`, `docs/dossier.md`, copie dans le projet.
- **Livraisons séparées** : ce qui protège (données personnelles, lecture seule, tests) avant ce qui se voit.
- **Tests d'écran** sur PC et sur iPhone ; ne pas en écrire beaucoup sur une interface qu'on va refaire. Viser une grille par son nom, pas par sa classe : plusieurs écrans ont des tuiles.
- **Vérifier les deux contrôles du bon commit** sur GitHub avant d'annoncer que c'est vert.

## 5. Ce que les conseils ont appris

- Trois onglets partout n'était pas la bonne cible : Millésime en a quatre, carnet six.
- Réécrire le serveur d'un outil qui modifie des fichiers originaux, pour la seule cohérence, ne vaut pas le risque : on peut donner l'habillage et la navigation sans toucher aux adresses qui écrivent (vérification des dates 2.0).
- Les tests gardent les règles ; ils ne gardent pas le chemin entre un clic et l'écriture. Ce chemin se teste à part.
- Une tuile vide (« à venir ») ne se livre pas.

## 6. Partir du socle pour une nouvelle appli

1. Copier ce dépôt, changer `APPLI` (`app/config.py`), le nom affiché et la couleur `--app` (`frontend/src/app.css`).
2. Remplacer « Synthèse » par l'écran de travail ou par « À traiter » ; garder « Connexion » (`pages/Services.svelte`) et « Réglages ». Retirer « Composants ».
3. Une tuile par service dans Connexion ; chaque route qui écrit commence par `exiger_ecriture(...)`.
4. Écrire `docs/dossier.md`, `REPRISE.md`, `CHANGELOG.md`.

Note : carnet, Millésime et la vérification des dates n'utilisent pas shadcn-svelte (classes écrites à la main, mêmes valeurs). Le socle le garde pour les applis neuves ; les deux façons donnent le même rendu.

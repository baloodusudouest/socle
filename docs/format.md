# Le format commun des applis

Écrit le 11/11/2026, après l'avoir appliqué trois fois le même jour : carnet (2.9 et 2.10), Millésime (2.0) et la vérification des dates (2.0). Ce document dit ce qui a marché, ce que les conseils ont corrigé, et ce qu'une nouvelle appli doit reprendre.

Il remplace le « document du socle » annoncé dans `REPRISE.md`. Mis à jour le 14/11/2026 : toujours sombre, couleurs de toutes les applis, adresses à jeton, écarts relevés (§ 7).

## 1. Ce qu'on retrouve dans chaque appli

| Élément | Règle |
|---|---|
| **Navigation** | Rail à gauche sur PC (900 px et plus), avec les noms. Pilule d'icônes flottante en bas sur iPhone, sans noms : le nom de la section est le titre de l'écran |
| **Entrées** | Peu : entre quatre et six. Toujours **Connexion** et **Réglages** ; presque toujours **À traiter** |
| **À traiter** | Une grille de tuiles, une par type de chose à faire, avec son nombre. Une tuile ouvre sa liste. Le compteur de l'onglet ne compte que ce qui attend une décision |
| **Connexion** | Une tuile par service extérieur, avec un voyant. Le service ouvert dit ce que l'appli y lit et y écrit, et porte ses gestes : **Vérifier** (compare, n'écrit rien) et **Synchroniser** (écrit ce qui est sûr, envoie le reste dans À traiter) |
| **Réglages** | Ce qui n'est pas un service : règles, journal des écritures avec Annuler, version, déconnexion |
| **Habillage** | Fonds neutres chauds, filets fins, **toujours sombre** (depuis le 13/11/2026 : le thème clair est retiré, quel que soit le réglage de l'appareil, pour que toutes les applis se ressemblent ouvertes seules ou dans l'Anneau). Inter. Titres d'écran grands et fins |
| **Couleur** | Une par appli. Elle porte l'action attendue (un seul bouton plein par bloc), l'onglet actif, les compteurs |
| **Signature** | Chaque appli garde ce qui la distingue (l'anneau de progression de carnet, l'année en Bodoni de Millésime) |

### Couleurs attribuées

| Appli | Couleur | Valeur |
|---|---|---|
| carnet | ocre | `#d9a441` |
| Millésime | lie-de-vin | `#b8405f` |
| vérification des dates | bleu ardoise | `#7f9cc4` |
| kit d'urgence | rouge brique | `#c8553d` |
| Sillage | or chaud | `#e3b556` |
| Transhumance | vert de pré | `#8fae6b` |
| l'Anneau | or pâle | `#e2c98a` |
| socle (modèle) | bleu-vert | `--app` dans `app.css` |

⚠️ carnet, Sillage et l'Anneau sont trois ors voisins : côte à côte dans l'Anneau, on ne les distingue pas bien (§ 7).

Neutres communs : fond `#151311`, surface `#1f1c19`, filet `#312c27`, texte `#f2ece2`, texte secondaire `#a89e91`. Un premier essai en neutres froids a été jugé trop froid. Les valeurs claires (`#faf7f2`, `#1e1a16`…) ne servent plus.

## 2. La règle qui passe avant le format

**Le geste répété ne passe jamais derrière une tuile.** carnet trie des cas variés de temps en temps : sa grille de tuiles est son écran d'ouverture. Millésime répète un seul geste des centaines de fois : il s'ouvre sur « Dater », et sa grille est une entrée à part. Le format sert le travail de l'appli, pas l'inverse (avis du conseil, Millésime 2.0).

Sur iPhone, dans un écran où l'on valide à la chaîne, la pilule s'efface pour ne rien laisser entre le pouce et le bouton ; un lien en haut ramène à la navigation.

## 3. Sécurité : ce que toute appli qui écrit doit avoir

1. **Mot de passe commun**, obligatoire : sans la variable, le conteneur ne démarre pas. Une seule adresse répond sans session, celle qui reçoit le mot de passe (attention à la méthode : une lecture sur le même chemin doit rester fermée), plus `/health`. Le cookie commun `maison_session` posé par l'Anneau vaut session dans toutes les applis (voir `lecons.md` § 3).
   **Adresses à jeton** : une autre appli ou Home Assistant peut avoir sa porte, sous un préfixe à part (`/externe/…`, `/ha/…`, `/invite/<jeton>`), avec **son** jeton, réglé dans la stack ; jeton vide, porte fermée. Elle ne fait que ce qui est écrit pour elle, ne donne jamais accès au reste de l'API, et chaque jeton se compare en temps constant.
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

## 7. Écarts relevés le 14/11/2026

Comparaison des applis en service avec ce document. Rien n'est corrigé d'office : chaque écart se tranche à la réouverture de l'appli (un passage au conseil sur les écarts, § 4).

| Appli | Écart | Gravité |
|---|---|---|
| toutes | Le document disait « clair quand l'appareil le demande » ; toutes sont toujours sombres. **Corrigé ici.** | — |
| toutes | Plusieurs ont des adresses à jeton que le § 3.1 ne prévoyait pas. **Règle ajoutée ici.** | — |
| carnet, Sillage, l'Anneau | Trois ors voisins (`#d9a441`, `#e3b556`, `#e2c98a`). | à trancher : garder l'or pour une seule |
| Transhumance | Deux entrées seulement (Migrer, Connexion), pas de Réglages : version et déconnexion sont dans Connexion. Sur téléphone, barre en haut au lieu de la pilule flottante en bas. | faible : outil d'une seule fois, à retirer de la stack après la migration |
| Transhumance | Les demandes de Millésime arrivent dans Migrer, pas dans une tuile « À traiter ». | faible, même raison |
| Sillage | Pas d'« À traiter » ; ce qui attend une décision est la tuile « À vérifier » dans Sillages. Pas de journal des écritures : Sillage n'écrit que dans sa propre base (corrections, récits, hôtes). | conforme à l'esprit (§ 2) |
| l'Anneau | Pas de rail : l'écran d'ouverture est l'anneau lui-même ; pas d'écran « Connexion » des services, puisqu'il est lui-même la vue des services. Pas de mode lecture seule : il n'écrit chez aucun service. | voulu, écrit dans son dossier |
| Millésime | Le refus en lecture seule passe par une exception (`LectureSeule`) au lieu de `exiger_ecriture` : même effet, autre nom. | aucun |
| carnet, Millésime | Noms de variables de couleur propres (`--color-onglet`, `--color-lie`) au lieu de `--app` : même rendu. | aucun ; à harmoniser seulement si l'habillage est refait |
| vérification des dates | Page servie par Flask, sans Svelte : choix du conseil 2.0 (ne pas réécrire un serveur qui modifie des originaux). | voulu |

Ce qui est partout conforme : mot de passe commun et cookie commun (les sept applis), `/health`, Watchtower désactivé pour celles qui écrivent, `REPRISE.md`, `CHANGELOG.md`, `docs/dossier.md`, icône et manifeste, Inter, tests d'écran sur deux tailles.


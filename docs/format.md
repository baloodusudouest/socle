# Le format commun des applis

Écrit le 11/11/2026, après l'avoir appliqué trois fois le même jour : carnet (2.9 et 2.10), Millésime (2.0) et la vérification des dates (2.0). Ce document dit ce qui a marché, ce que les conseils ont corrigé, et ce qu'une nouvelle appli doit reprendre.

Il remplace le « document du socle » annoncé dans `REPRISE.md`. Mis à jour le 14/11/2026 : toujours sombre, couleurs de toutes les applis, adresses à jeton, écarts relevés (§ 7). Mis à jour le 16/11/2026 : réglages dans l'appli, sauvegarde et restauration (§ 8).

## 1. Ce qu'on retrouve dans chaque appli

| Élément | Règle |
|---|---|
| **Navigation** | Rail à gauche sur PC (900 px et plus), avec les noms. Barre d'icônes **collée au bord bas** sur iPhone, sur toute la largeur, sans noms : le nom de la section est le titre de l'écran (choix de Julien, 22/11/2026 ; avant : pilule flottante) |
| **Entrées** | Peu : entre quatre et six. Toujours **Connexion** et **Réglages** ; presque toujours **À traiter** |
| **À traiter** | Une grille de tuiles, une par type de chose à faire, avec son nombre. Une tuile ouvre sa liste. Le compteur de l'onglet ne compte que ce qui attend une décision |
| **Connexion** | Écran commun (0.10.0, contrat 3 : `frontend/src/lib/services/`, recopié tel quel). Une fiche par service extérieur : point et état en mots (Répond, Ne répond pas, Relié, Pas relié), **Ce qui est lu**, **Ce qui est écrit**, « Pour le relier, dans la stack » s'il n'est pas relié, âge du dernier essai. **De 1 à 3 services : fiches dépliées ; à partir de 4 : tuiles à voyant, la fiche s'ouvre dessous au toucher.** Gestes : **Vérifier** (contour, ne teste que ce service, essai léger sans écriture ni coût) et au plus un geste qui écrit (plein : Synchroniser, Livrer…). Le dossier de données n'est pas un service : il est dans Réglages. Données : `GET /api/maison/services` (session ou `ANNEAU_CLE`) |
| **Réglages** | Ce qui n'est pas un service : réglages d'usage, « Restaurer les réglages », règles, journal des écritures avec Annuler, version, déconnexion (motif au § 8) |
| **Habillage** | Fonds neutres chauds, filets fins, **toujours sombre** (depuis le 13/11/2026 : le thème clair est retiré, quel que soit le réglage de l'appareil, pour que toutes les applis se ressemblent ouvertes seules ou dans l'Anneau). Inter. Titres d'écran grands et fins |
| **Couleur** | Une par appli. Elle porte l'action attendue (un seul bouton plein par bloc), l'onglet actif, les compteurs |
| **Signature** | Chaque appli garde ce qui la distingue (l'anneau de progression de carnet, l'année en Bodoni de Millésime) |

### Couleurs attribuées

| Appli | Couleur | Valeur |
|---|---|---|
| carnet | argent (l'ocre jusqu'au 14/11/2026) | `#b7c0cc` |
| Millésime | lie-de-vin | `#b8405f` |
| vérification des dates | bleu ardoise | `#7f9cc4` |
| kit d'urgence | rouge brique | `#c8553d` |
| Sillage | lavande crépuscule (le miel doré jusqu'au 14/11/2026) | `#a98fd8` |
| Transhumance | vert de pré | `#8fae6b` |
| l'Anneau | or pâle — seule appli en or | `#e2c98a` |
| Scriptorium | parchemin | `#c4a07a` |
| Comptoir | ambre | `#e0884a` |
| Gazette | vert anis (signature : l'aperçu du journal, papier crème `#F7F3EA`) | `#b5c94f` |
| socle (modèle) | bleu-vert | `--app` dans `app.css` |

L'or est réservé à l'Anneau, la porte qui montre toutes les autres (décision du 14/11/2026 : carnet, Sillage et l'Anneau avaient trois ors voisins).

Neutres communs : fond `#151311`, surface `#1f1c19`, filet `#312c27`, texte `#f2ece2`, texte secondaire `#a89e91`. Un premier essai en neutres froids a été jugé trop froid. Les valeurs claires (`#faf7f2`, `#1e1a16`…) ne servent plus.

## 2. La règle qui passe avant le format

**Le geste répété ne passe jamais derrière une tuile.** carnet trie des cas variés de temps en temps : sa grille de tuiles est son écran d'ouverture. Millésime répète un seul geste des centaines de fois : il s'ouvre sur « Dater », et sa grille est une entrée à part. Le format sert le travail de l'appli, pas l'inverse (avis du conseil, Millésime 2.0).

Sur iPhone, dans un écran où l'on valide à la chaîne, la barre d'onglets s'efface pour ne rien laisser entre le pouce et le bouton ; un lien en haut ramène à la navigation.

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
2. Remplacer « Synthèse » par l'écran de travail ou par « À traiter » ; garder « Connexion » (`$lib/services/Services.svelte`, commun) et « Réglages ». Retirer « Composants » et « Documents ».
3. Déclarer chaque service extérieur dans `SERVICES` (`maison.Services`, voir `app/main.py`) avec un essai léger, puis `maison.monter_services(...)` après la garde ; chaque route qui écrit commence par `exiger_ecriture(...)`.
4. Remplacer les deux réglages de démonstration (`REGLAGES_DEFAUTS`, `REGLAGES_VARIABLES`, `EXCLUS_SAUVEGARDE` dans `app/main.py`, table `NOMS` dans `pages/Reglages.svelte`) par ceux de l'appli ; garder les routes de sauvegarde et de restauration telles quelles (§ 8).
5. Écrire `docs/dossier.md`, `REPRISE.md`, `CHANGELOG.md`.

Note : carnet, Millésime et la vérification des dates n'utilisent pas shadcn-svelte (classes écrites à la main, mêmes valeurs). Le socle le garde pour les applis neuves ; les deux façons donnent le même rendu.

## 7. Écarts relevés le 14/11/2026

Comparaison des applis en service avec ce document. Rien n'est corrigé d'office : chaque écart se tranche à la réouverture de l'appli (un passage au conseil sur les écarts, § 4).

| Appli | Écart | Gravité |
|---|---|---|
| toutes | Le document disait « clair quand l'appareil le demande » ; toutes sont toujours sombres. **Corrigé ici.** | — |
| toutes | Plusieurs ont des adresses à jeton que le § 3.1 ne prévoyait pas. **Règle ajoutée ici.** | — |
| carnet, Sillage, l'Anneau | Trois ors voisins. **Tranché le 14/11/2026** : l'Anneau garde l'or, carnet passe en argent (2.18.2), Sillage en lavande (0.10.1). | — |
| Transhumance | Les demandes de Millésime arrivent dans Migrer, pas dans une tuile « À traiter ». | faible, même raison |
| Sillage | Pas d'« À traiter » ; ce qui attend une décision est la tuile « À vérifier » dans Sillages. Pas de journal des écritures : Sillage n'écrit que dans sa propre base (corrections, récits, hôtes). | conforme à l'esprit (§ 2) |
| l'Anneau | Pas de rail : l'écran d'ouverture est l'anneau lui-même. Pas d'écran « Connexion » à lui ; depuis le 20/11/2026, sa fiche « État » d'une appli montre les fiches de cette appli (contrat 3, avec Vérifier). Pas de mode lecture seule : il n'écrit chez aucun service. | voulu, écrit dans son dossier |
| Millésime | Le refus en lecture seule passe par une exception (`LectureSeule`) au lieu de `exiger_ecriture` : même effet, autre nom. | aucun |
| carnet, Millésime | Noms de variables de couleur propres (`--color-onglet`, `--color-lie`) au lieu de `--app` : même rendu. | aucun ; à harmoniser seulement si l'habillage est refait |
| vérification des dates | Page servie par Flask, sans Svelte : choix du conseil 2.0 (ne pas réécrire un serveur qui modifie des originaux). | voulu |

Ce qui est partout conforme : mot de passe commun et cookie commun (les sept applis), `/health`, Watchtower désactivé pour celles qui écrivent, `REPRISE.md`, `CHANGELOG.md`, `docs/dossier.md`, icône et manifeste, Inter, tests d'écran sur deux tailles.

## 8. Réglages et Restaurer (16/11/2026, contrat de sauvegarde 1)

Choix du 16/11/2026 : les **réglages d'usage** (ce qu'on change en se servant de l'appli : un seuil, un nom d'album, une heure, une liste d'exclusions) quittent la stack pour l'écran Réglages. La stack ne garde que l'installation : mot de passe, jetons, dossiers, adresses, lecture seule. L'Anneau garde chaque nuit une copie des réglages de chaque appli ; chaque appli sait relire une copie et l'appliquer. Modèle complet dans le socle (0.6.0) : `app/main.py`, `pages/Reglages.svelte`, `tests/test_reglages.py`, `tests/test_ecran.py`.

### Où vivent les réglages

- Dans l'appli : `maison.Reglages(<données>/reglages.json, defauts, variables)`. Le **type de la valeur par défaut** fixe le type du réglage (oui/non, entier, décimal, liste, texte). Une appli qui a déjà sa table de réglages la garde et l'expose en dictionnaire.
- `variables` donne, pour chaque clé, l'**ancienne variable de la stack** : elle est lue une seule fois, au premier démarrage où la clé manque dans le fichier (reprise), puis plus jamais. Chaque reprise laisse une ligne au journal (le nom de la clé et de la variable, pas la valeur).
- Changer un réglage ou en restaurer un est **permis en lecture seule** : la lecture seule protège les services extérieurs, pas les réglages de l'appli.

### Écran

Deux tuiles dans Réglages, au-dessus de la version et de la déconnexion :

| Tuile | Contenu |
|---|---|
| **Réglages** | Un champ par réglage (texte, interrupteur `role="switch"` pour oui/non, nombre, liste). Un seul bouton plein, « Enregistrer », inactif tant que rien n'a changé. Message en ligne : « Réglages enregistrés. » ou la raison du refus |
| **Restaurer les réglages** | Une liste des dates gardées par l'Anneau (la plus récente choisie), la liste des différences « valeur actuelle → valeur sauvegardée » avec le nom affiché du réglage, puis « Restaurer » → « Remplacer N réglages ? Confirmer / Annuler ». Anneau injoignable ou rien de sauvegardé : une phrase claire et « Réessayer », jamais une erreur de page |

### Routes

| Route | Porte | Réponse |
|---|---|---|
| `GET /api/reglages` | session | `{"reglages": {…}}` |
| `PUT /api/reglages` | session | `{clé: valeur}` ; clés inconnues ignorées ; mauvais type → **400** avec un message clair, rien n'est changé |
| `GET /externe/sauvegarde` | **jeton commun** (`MAISON_JETON`, ou `MAISON_JETON_ANCIEN` pendant un changement) ; `MAISON_JETON` vide → **404** (porte fermée) ; mauvais jeton → 401. La session ne suffit pas | `maison.sauvegarde("<nom du dépôt>", __version__, reglages, exclus=…)` |
| `GET /api/restaurer` | session | `{"dates": ["AAAA-MM-JJ", …]}` |
| `GET /api/restaurer?le=AAAA-MM-JJ` | session | `{"le", "version", "differences": [{"cle", "actuel", "sauve"}]}` |
| `POST /api/restaurer` `{"le": …}` | session | applique les différences, une ligne au journal ; `{"le", "appliques", "ignores", "reglages"}` |

Le middleware de session ne garde que `/api/…` : `/externe/…` vérifie son jeton dans la route. Les erreurs de l'Anneau deviennent 404 (aucune sauvegarde ce jour-là) ou 503 (« L'Anneau ne répond pas »). Une valeur sauvegardée qui n'a plus le bon type (réglage changé de type entre deux versions) est ignorée et nommée, les autres s'appliquent.

### Contrat de sauvegarde 1

```
{"contrat": 1, "appli": "<nom du dépôt>", "version": "X.Y.Z", "le": "<date ISO avec fuseau>",
 "reglages": {<réglages d'usage publics>}}
```

- **Jamais de secret** : `maison.est_secret()` écarte tout nom qui contient un mot de secret (password, jeton, token, cle, key, code, webhook, user, email…) ; elle se trompe exprès dans le sens prudent (`boucle`, `max_articles` sont aussi écartés : choisir un autre nom de clé).
- **Exclusions explicites** : `EXCLUS_SAUVEGARDE`, une liste écrite même vide, pour un réglage qui contient un chemin personnel, un nom de proche, une adresse.
- Ni variable de la stack, ni chemin de dossier, ni valeur dérivée : seulement ce que l'utilisateur règle.
- L'Anneau lit `GET /externe/sauvegarde` chaque nuit et rend `GET /externe/sauvegardes/<appli>[?le=…]` ; l'appli le lit par `maison.lire_sauvegarde(appli, le)`. Pas de notification Home Assistant : un échec de collecte se voit dans la tuile « À traiter » de l'Anneau.

### Déploiement en deux temps

1. Nouvelle image **avec la stack actuelle** : au premier démarrage, chaque réglage est repris de son ancienne variable. Vérifier l'écran Réglages.
2. Nouvelle stack **sans les anciennes lignes** de réglage. Retirer une ligne avant le premier démarrage ferait perdre sa valeur (le réglage prendrait sa valeur par défaut).

## 9. Fiches « Connexion » (20/11/2026, contrat 3)

Choix du 20/11/2026 (dossier et conseil « fiches Connexion ») : le même écran dans toutes les applis, au format de Douze points 1.8.0.

- **Serveur** : `SERVICES = maison.Services(APPLI)` puis `SERVICES.ajouter(id, nom, lit=…, ecrit=…, regle=…, reglage=…, essai=…, genre=…, cible=…, geste=…, derniere_ecriture=…)` ; `maison.monter_services(app, SERVICES, session_ok)` **après** la garde. `id` vient de la liste fermée du coffre (immich, carnet, home-assistant, icloud…).
- **Essai léger, par règle** : une lecture courte (version, état) ; jamais d'écriture, d'appel payant ni de réveil (un PC en veille donne « ne répond pas »). Au plus un essai toutes les 30 s par service ; arrêté au bout de 8 s. `maison.essai_http(adresse)` sert pour les services HTTP.
- **Le GET ne lance aucun essai** : il rend le dernier résultat et son âge (`verifie_le`). Un geste de l'appli qui vient de joindre le service le note (`SERVICES.noter(id, ok, phrase)`).
- **Détail nettoyé** : secrets, adresses et hôtes retirés, une ligne, 160 caractères.
- **Accès** : la session de l'appli, ou `ANNEAU_CLE` (clé de lecture de l'Anneau, n'ouvre que ces deux routes). `MAISON_JETON` n'ouvre pas les fiches.
- **Interface** : `$lib/services/Services.svelte` (écran) et `FicheService.svelte` (fiche), recopiés et signés par `tools/diffuser_maison.py` ; le test de chaque appli recalcule l'empreinte (`maison.empreinte_interface`). L'appli passe `ongeste(service, geste)` pour son geste qui écrit. Classes Tailwind sur les jetons communs (`card`, `border`, `muted-foreground`, `primary`, `destructive`, `input`) et `.titre`, `.etiquette`.
- **Bac à sable** : `maison.Services(APPLI, simule=True)` : bandeau « Simulé » sur ses fiches.
- **Guide** (0.11.0) : un service qu'on allume et répare soi-même (PC de calcul, IA du PC) porte `guide={reglages, allumer, pannes, une_fois, terminal, note}`, au format de la fiche « IA du PC » de Gazette. Rien de secret : le guide s'affiche aussi dans l'Anneau.


# Ce que les applis ont appris au socle

Journal de ce qui a été construit, cassé et corrigé en partant du socle (novembre 2026), écrit pour qu'une nouvelle session puisse repartir d'ici et refaire une appli sans retomber dans les mêmes trous.

Tout est générique ou anonymisé : aucune adresse, aucun nom, aucune liste réelle de services. Les exemples d'adresses sont en `192.0.2.x` (plage réservée à la documentation). Le format visuel et la méthode sont dans [`format.md`](format.md) ; ce document les complète, il ne les répète pas.

## 1. La méthode, telle qu'elle a servi

1. **Grill** : des questions à choix, par tours, jusqu'à ce qu'il n'y ait plus rien de supposé. Les faits se cherchent (sonde, lecture du code), seules les décisions se demandent.
2. **Dossier en six sections** : besoin, technique, parcours des écrans, design, schéma de données, plan. Les décisions prises après coup s'ajoutent en fin de dossier, datées, sans réécrire le reste.
3. **Conseil** : cinq avis indépendants, relecture croisée anonyme, synthèse. Deux passages pour une grosse appli. Ce qui en sort le plus souvent : un périmètre plus petit, et une première version en lecture seule.
4. **Maquette avant le code** quand l'écran est le cœur de l'appli : plusieurs variantes à comparer, sur PC et sur téléphone, avec des états inventés.
5. **Sonde en lecture seule** sur les vraies données avant de figer la conception. Une première version en lecture seule peut tenir lieu de sonde.
6. **Code par étapes livrables**, chacune testée et publiée.
7. `REPRISE.md` et `CHANGELOG.md` tenus dans le même commit que le code. `REPRISE.md` dit toujours ce qui n'a **jamais été essayé sur la vraie installation**.

Règles qui ont évité des dégâts :

- Une appli qui écrit dans de vraies données a un mode lecture seule, un journal de ses écritures, et pas de mise à jour automatique.
- Une suppression définitive se confirme, se fait par lots, et montre son avancement.
- Un outil qui ne fait que lire n'a aucune fonction qui écrit, et un test le prouve (voir § 6).
- Dans les rapports et les journaux : pas de nom de personne.

## 2. Partir du socle : ce qu'il faut changer

Copier les fichiers suivis par git, sans la documentation ni les tests du socle :

```
cd socle && git ls-files | grep -v -E '^(docs/|README.md|REPRISE.md|\.gitignore|tests/|tools/)' | tar cf - -T - | (cd ../nouvelle-appli && tar xf -)
```

Puis renommer, partout où le mot « socle » ou le préfixe `APP_` apparaît :

| Fichier | Ce qui change |
|---|---|
| `app/config.py` | nom de l'appli, préfixe des variables (`MONAPPLI_PASSWORD`, `MONAPPLI_DATA`…), variables propres |
| `app/__init__.py` | version |
| `Dockerfile` | étiquettes, variables, port exposé, port du contrôle de santé |
| `entrypoint.sh` | variables et port |
| `docker-compose.yml`, `.env.example` | nom du service, image, port, variables ; aucune vraie valeur |
| `.github/workflows/docker.yml` | nom de l'image |
| `frontend/index.html`, `public/manifest.webmanifest` | titre, nom sur l'écran d'accueil |
| `frontend/public/icone.svg` et ses deux PNG | l'icône de l'appli |
| `frontend/src/app.css` | les deux valeurs de `--app` (sombre, clair) et `--app-contraste` |
| `frontend/package.json` | nom, version ; retirer les bibliothèques de graphique si l'appli n'en trace pas |
| `frontend/src/App.svelte`, `pages/Connexion.svelte`, `pages/Reglages.svelte`, `pages/Services.svelte` | nom affiché, entrées de navigation |

Pièges vus en le faisant :

- **Deux écrans portent presque le même nom** : `pages/Connexion.svelte` est la page du mot de passe, `pages/Services.svelte` est l'écran « Connexion » (les services extérieurs).
- **La version est écrite à plusieurs endroits** (`app/__init__.py`, `package.json`, parfois un test d'écran qui lit « Appli 0.1.0 », parfois le README). Les chercher tous avant de publier.
- **Les PNG de l'icône** se régénèrent depuis le SVG avec le navigateur des tests (capture à 180 et 512 pixels, fond transparent).
- **Les bibliothèques de graphique pèsent lourd** : les retirer divise le poids de l'interface par trois ou quatre.
- **Un choix de port** se vérifie contre la liste des ports déjà pris dans la stack.

## 3. Connexion

**Le mot de passe.** Une seule variable, douze caractères au moins ; sinon le conteneur s'arrête au démarrage avec un message clair dans ses journaux. Toutes les applis de la maison reçoivent la même valeur.

**La session.** Un cookie signé (HMAC du mot de passe), `HttpOnly`, `SameSite=Strict`, trente jours. Une « génération » écrite dans le dossier de données : « Se déconnecter » l'augmente et invalide tous les cookies émis avant. Changer le mot de passe déconnecte tout le monde. Délai avant réponse à chaque essai, allongé après cinq échecs.

**La garde.** Un seul filtre : toute route `/api/…` demande la session, sauf la liste courte des routes publiques. `/health` est public et ne dit que « ok » et la version. Les réponses d'API portent `Cache-Control: no-store`, **sauf les images**, à qui on laisse un cache privé (sinon chaque vignette est retéléchargée à chaque affichage).

**La connexion commune (0.3.0).** Le portail de la maison pose à sa connexion un second cookie, `maison_session`, que chaque appli accepte :

```
valeur = "<expiration en secondes>.<HMAC-SHA256(clé, expiration)>"
clé    = SHA256("maison-session|" + mot de passe commun)
```

- Le navigateur envoie un cookie à **tous les ports d'un même hôte** : c'est ce qui permet à un cookie posé par une appli d'être lu par les autres.
- Il ne porte pas de génération : il vaut trente jours, ou jusqu'au changement du mot de passe. « Se déconnecter » dans n'importe quelle appli le retire du navigateur.
- Une appli qui a un autre mot de passe le refuse, simplement, et demande le sien.
- Dans le socle : `Sessions.connecte(cookies)` (cookie de l'appli **ou** cookie commun), `Sessions.creer_commun()` pour l'appli qui le pose. Seul le portail le pose.
- Cela ne vaut que pour les applis maison. Un service qui a ses propres comptes ne peut être ouvert d'office que si le portail garde ses identifiants (refusé) ou par un fournisseur d'identité (chantier à part).

**Le piège du cookie dans un cadre.** Une appli affichée dans le cadre d'une autre page ne reçoit son cookie que si les deux sont « du même site », c'est-à-dire servies par le **même hôte** (le port ne compte pas). Symptôme : le mot de passe est accepté, puis la page de connexion revient, ou le service répond « non autorisé ». Cause vue : le portail ouvert par un nom ou une adresse (réseau privé), les services donnés par une autre (adresse locale). Remède : donner au navigateur les services sous l'hôte par lequel le portail est lui-même ouvert, port gardé. En HTTPS, il faut une adresse HTTPS par service.

## 4. Afficher une appli dans une autre (le cadre)

- **Qui refuse.** Un service interdit le cadre par l'en-tête `X-Frame-Options` (toute valeur) ou par `Content-Security-Policy: frame-ancestors` (sauf `*`). Le navigateur ne permet pas à la page de le savoir : c'est le **serveur** du portail qui lit les en-têtes de la page d'accueil du service, en suivant ses renvois, et décide. Relire de temps en temps, et à chaque rechargement de la configuration.
- **Trois états dans la configuration**, pas deux : forcer le cadre, l'interdire, ou laisser essayer (le défaut). Quand le cadre est refusé, l'écran dit pourquoi et propose d'ouvrir à côté.
- **Ouvrir à côté** : `window.open(adresse, 'nom-stable')` réutilise toujours la même fenêtre pour un service ; les onglets ne se multiplient pas.
- **Le bouton du milieu** ouvre un nouvel onglet : écouter `auxclick` (bouton 1), et annuler `mousedown` du même bouton, sinon le navigateur lance son défilement automatique.
- **Contenu mixte.** Une page en HTTPS ne peut pas afficher un cadre en HTTP : le prévoir, et le dire à l'écran plutôt que montrer un cadre blanc.
- **Ce que le cadre laisse passer.** Sans `allow="camera; fullscreen; clipboard-write"`, une appli qui utilise l'appareil photo s'affiche mais ne peut pas s'en servir. La caméra en direct demande en plus que **toute la chaîne** soit en HTTPS, la page qui contient le cadre comprise.
- **Un service éteint exprès** ou en panne ne s'affiche pas dans un cadre vide : montrer son état.
- **Certains services se comportent mal dans un cadre** sans l'interdire (page figée). Garder la possibilité de les sortir du cadre à la main.

## 5. Écran : ce que le téléphone a montré

- **Texte courbe et transparence.** Sur le navigateur du téléphone, un texte posé sur un chemin (`textPath`) rendu avec `opacity` est rogné à sa boîte : les grandes boucles d'une écriture cursive y perdent un morceau. Assombrir par la couleur (`fill`), pas par `opacity`. Même prudence avec `filter` sur ce genre de texte.
- **Mesurer un texte** (pour l'ajuster à un arc) se fait après `document.fonts.ready`, et se refait quand la police arrive.
- **Polices** : les embarquer (paquets de polices), ne pas compter sur un service de polices en ligne, injoignable en développement et inutile sur un réseau fermé.
- **Hauteur** : `100dvh`, et les marges de sécurité (`env(safe-area-inset-*)`) sur tout ce qui touche un bord.
- **Navigation** : rail à gauche sur PC, pilule d'icônes en bas sur téléphone, mêmes entrées dans le même ordre.
- **Deux mises en page pour un même moment** valent mieux qu'une mise en page qui se déforme : sur téléphone, ce qui est en panne passe avant le décor.
- **Animations** : toutes coupées par `prefers-reduced-motion`.
- **Une règle CSS écrite deux fois** : la seconde gagne en silence. Modifier le bloc d'origine, ne pas en ajouter un plus bas.
- **Noms** : première lettre en majuscule, jamais tout en capitales.

## 6. Parler à un service extérieur

- **Une clé par appli**, limitée à ce qu'elle fait. Lister les droits nécessaires dans `.env.example`. Un refus (401, 403) devient une phrase lisible dans l'écran « Connexion », pas une erreur brute.
- **La clé ne quitte jamais le serveur** : le navigateur parle à l'appli, l'appli parle au service. Les images passent par l'appli, derrière la session.
- **Ne servir que ce qu'on a montré** : une route d'image n'accepte que les identifiants d'un résultat déjà calculé, sinon l'appli devient une porte ouverte sur tout le service.
- **Respecter ce que le service cache** : corbeille, archives, éléments verrouillés ne sont pas montrés.
- **Vérifier le sens des paramètres dans le code du service**, pas de mémoire. Une demande où deux identifiants étaient inversés (celui de l'adresse et celui du corps) a tenu des semaines dans les tests, parce que le faux service avait la même erreur que le code. Le faux service doit être écrit d'après le vrai.
- **Une lecture peut être un POST** (une recherche) : la liste des POST permis est écrite en dur, tout autre POST est refusé par le client lui-même.
- **Prouver la lecture seule** par trois tests : le relevé des demandes reçues par le faux service ne contient que des lectures ; le client refuse d'envoyer autre chose ; et l'analyse du fichier du client ne trouve aucun appel d'écriture.
- **Pagination** : lire jusqu'à la dernière page, toujours.
- **Garder en mémoire** ce qui est long à lire, quelques minutes, avec un bouton pour relire. Les lectures unitaires nombreuses se font à plusieurs de front, et leur résultat se garde.
- **Tolérer le service muet** : garder la dernière réponse connue, dire de quand elle date.

## 7. Surveiller sans crier au loup

- Une réponse HTTP en dessous de 500 compte comme vivante, une page de connexion aussi.
- Trois échecs de suite ouvrent une panne, trois réussites la closent.
- Une machine qui tombe fait **une** panne, pas une par service qu'elle porte.
- Un service qu'on éteint exprès est « éteint », jamais « en panne ».
- Ce qu'un autre outil sait déjà (place disque, mises à jour) se **reçoit** de lui, avec un secret partagé ; son silence prolongé est lui-même une panne.
- Notifier une fois à l'ouverture, une fois à la clôture.
- N'écrire que de petits fichiers : sur un disque presque plein, pas d'historique de sondes.
- La configuration des services vit dans un fichier **hors du dépôt**, avec un exemple inventé dans le dépôt ; une ligne fausse est écartée et signalée, le reste sert.

## 8. Tests

- **Serveur** : un faux service par service extérieur, des données inventées, un relevé de ce qui lui est demandé.
- **Écran** : un serveur de démonstration lancé par les tests, puis le navigateur sur deux tailles (PC, téléphone). À chaque écran : aucune erreur de page, aucun débordement horizontal.
- **Attendre, ne pas constater** : `wait_for()` plutôt que `is_visible()` juste après une navigation.
- **SVG** : `text_content()`, pas `inner_text()`, sur les nœuds de texte d'un dessin.
- **L'hôte par défaut du client de test** n'est pas celui de la maison : un test qui dépend de l'hôte l'envoie explicitement.
- **Une route qui n'existe pas** répond 401 sans session et 404 avec : ne pas s'en servir pour vérifier une connexion.
- **Les états rares** (éteint, refus, vide, disque plein) ont chacun leur test : ce sont eux qui cassent quand on change un défaut.
- Rien n'est publié si les tests échouent : le flux de publication les lance d'abord, serveur puis écran.

## 9. Publier et déployer

- Image construite à chaque envoi sur la branche principale, étiquetée `latest`, numéro de version et empreinte du commit : on revient en arrière en changeant l'étiquette dans la stack.
- **Un service n'entre dans la stack qu'une fois son image publiée** : sinon le tirage échoue et toute la stack reste en plan.
- Les applis maison suivent `latest` ; la nouvelle version arrive quand la stack est redéployée en retéléchargeant les images.
- **Avant toute modification de la stack** : relire sa dernière version enregistrée, modifier, réenregistrer, et rendre le fichier complet.
- Une variable absente de la stack donne une erreur obscure au déploiement (« section vide entre deux-points ») : lister les variables nouvelles à chaque livraison.
- Un conteneur recréé peut rester longtemps « en démarrage » : vérifier qu'il répond, ne pas le supposer.
- Le conteneur adopte le propriétaire de son dossier de données : aucun identifiant d'utilisateur à configurer.

**Dans un dépôt public, jamais** : adresse, chemin, mot de passe, nom de personne, vraie liste de services, nom réel de dossier, d'album ou de tag. Ces valeurs passent par des variables de la stack ou par un fichier posé à la main dans le dossier de données.

## 10. Erreurs de fabrication, pour ne pas les refaire

| Ce qui s'est passé | Ce qu'il faut faire |
|---|---|
| Un fichier ouvert en écriture avant d'être lu : vidé | Lire, modifier en mémoire, écrire ; ou restaurer depuis git |
| Une modification par numéro de ligne tombée sur la mauvaise ligne | Remplacer par le contenu, et vérifier que le motif n'apparaît qu'une fois |
| Des méthodes ajoutées « à la fin du fichier » tombées après une fonction, hors de la classe | Ajouter à la fin de la classe, et lancer les tests de chaque dépôt touché |
| Un défaut changé (le cadre par défaut) a cassé un état rare (service éteint) | Chercher tous les états avant de changer un défaut |
| Une cause devinée d'après une capture, corrigée avant d'être confirmée | Demander le fait qui tranche (ici : par quelle adresse l'appli est ouverte), puis corriger |
| Un écran validé sur PC, rogné sur téléphone | Regarder sur un vrai téléphone avant de dire que c'est fini |
| Une dépendance entre deux applis découverte au déploiement | Une première version autonome ; le lien avec l'autre appli vient après |
| Un service ajouté à la stack avant d'avoir une image | Coder et publier d'abord, ajouter ensuite |

## 11. Ce qui reste vrai d'une appli à l'autre

- Une première version qui ne fait que lire se livre en une séance et apprend plus qu'une sonde.
- Le périmètre annoncé dit aussi ce qui **n'est pas** fait.
- Ce qui n'a tourné que contre de faux services est dit tel quel, à chaque livraison.
- Un réglage qui retire une protection (affichage dans un cadre, connexion sans mot de passe sur le réseau local) se propose, avec son prix, et ne se pose pas d'office.

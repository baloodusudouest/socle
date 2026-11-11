<script>
  // Planche des composants de base : ce que chaque appli reprend tel quel.
  import Tuile from '$lib/components/Tuile.svelte'
  import { Button } from '$lib/components/ui/button/index.js'
  import { Badge } from '$lib/components/ui/badge/index.js'
  import { Progress } from '$lib/components/ui/progress/index.js'
  import { Separator } from '$lib/components/ui/separator/index.js'

  let avancement = $state(40)
</script>

<header class="mb-5">
  <p class="etiquette">socle</p>
  <h1 class="titre">Composants</h1>
</header>

<div class="grid gap-3 md:grid-cols-2 md:gap-4">
  <Tuile etiquette="Boutons">
    <div class="flex flex-wrap gap-2">
      <Button>Valider</Button>
      <Button variant="outline">Voir</Button>
      <Button variant="secondary">Plus tard</Button>
      <Button variant="ghost">Annuler</Button>
      <Button variant="destructive">Supprimer</Button>
    </div>
    <p class="text-sm text-muted-foreground">Un seul bouton plein par écran : l'action attendue.</p>
  </Tuile>

  <Tuile etiquette="Pastilles">
    <div class="flex flex-wrap gap-2">
      <Badge>À traiter</Badge>
      <Badge variant="secondary">Validée</Badge>
      <Badge variant="outline">Brouillon</Badge>
      <Badge variant="destructive">Erreur</Badge>
    </div>
    <p class="text-sm text-muted-foreground">La couleur de l'appli marque ce qui demande ton attention, rien d'autre.</p>
  </Tuile>

  <Tuile etiquette="Avancement">
    <div class="flex items-baseline justify-between">
      <p class="chiffre text-4xl">{avancement} %</p>
      <div class="flex gap-2">
        <Button variant="outline" size="sm" onclick={() => (avancement = Math.max(0, avancement - 20))}>− 20</Button>
        <Button variant="outline" size="sm" onclick={() => (avancement = Math.min(100, avancement + 20))}>+ 20</Button>
      </div>
    </div>
    <Progress value={avancement} aria-label="Avancement" />
  </Tuile>

  <Tuile etiquette="Texte">
    <p class="titre">Titre d'écran</p>
    <Separator />
    <p>Texte courant, 15 px, pour les fiches et les listes.</p>
    <p class="text-sm text-muted-foreground">Texte secondaire pour les précisions.</p>
    <p class="etiquette">Étiquette de tuile</p>
  </Tuile>
</div>

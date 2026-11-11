<script>
  // « Connexion » : une tuile par service extérieur, avec son voyant. Toucher une tuile ouvre le
  // service : ce que l'appli y lit, ce qu'elle y écrit, et ses gestes (vérifier, synchroniser).
  // Le socle n'a qu'un « service » : son dossier de données. Une appli en met un par outil relié.
  // (pages/Connexion.svelte est la page du mot de passe : ne pas confondre.)
  import { onMount } from 'svelte'
  import HardDrive from '@lucide/svelte/icons/hard-drive'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'
  import { Badge } from '$lib/components/ui/badge/index.js'

  let { lectureSeule = false, ondeconnecte } = $props()
  let s = $state(null)
  let choisi = $state(null)
  let message = $state('')
  let attente = $state(false)

  async function lire() {
    try { s = await api.get('/api/synthese') } catch (err) { if (err.statut === 401) ondeconnecte?.(); else message = err.message }
  }
  async function ecrire() {
    attente = true
    try { await api.post('/api/essai-ecriture'); message = 'Fichier témoin écrit dans le dossier de données.' }
    catch (err) { message = err.message }
    attente = false
    lire()
  }
  onMount(lire)
</script>

<header class="mb-5">
  <p class="etiquette">socle</p>
  <h1 class="titre">Connexion</h1>
</header>

<div class="grid grid-cols-2 gap-3 md:grid-cols-4">
  <button type="button" aria-pressed={choisi === 'donnees'} onclick={() => (choisi = choisi === 'donnees' ? null : 'donnees')}
          class="flex min-h-28 flex-col gap-1 rounded-2xl border bg-card p-4 text-left transition-colors hover:border-primary aria-pressed:border-primary">
    <span class="flex items-start justify-between">
      <HardDrive class="size-6 text-primary" aria-hidden="true" />
      <span class="size-2.5 rounded-full {s?.donnees_inscriptibles ? 'bg-valide' : 'bg-muted-foreground/40'}" aria-hidden="true"></span>
    </span>
    <span class="font-medium">Dossier de données</span>
    <span class="text-sm text-muted-foreground">{s ? (s.donnees_inscriptibles ? 'écriture possible' : 'écriture refusée') : 'lecture…'}</span>
  </button>
</div>

{#if choisi === 'donnees'}
  <section class="mt-4 rounded-2xl border bg-card p-5" aria-label="Dossier de données">
    <h2 class="text-lg font-semibold">Dossier de données</h2>
    <p class="mt-1 text-sm text-muted-foreground">Le seul endroit où le socle écrit. Dans une appli, chaque service a ici ses deux gestes :
      « Vérifier » compare sans rien écrire ; « Synchroniser » écrit ce qui est sûr et envoie le reste dans « À traiter ».</p>
    <div class="mt-3 flex flex-wrap items-center gap-2">
      <Button variant="outline" onclick={lire}>Vérifier</Button>
      <Button onclick={ecrire} disabled={attente || lectureSeule}>Écrire le fichier témoin</Button>
      {#if lectureSeule}<Badge variant="outline">lecture seule : écriture refusée</Badge>{/if}
    </div>
    {#if message}<p class="mt-3 text-sm" role="status">{message}</p>{/if}
  </section>
{:else}
  <p class="mt-4 text-sm text-muted-foreground">Touche un service pour voir son état et ses gestes.</p>
{/if}

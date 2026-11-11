<script>
  // Écran de synthèse en tuiles bento. Toutes les valeurs viennent de /api/synthese :
  // ce sont les vraies mesures du conteneur, pas des exemples.
  import { onMount } from 'svelte'
  import { scaleBand } from 'd3-scale'
  import { BarChart } from 'layerchart'
  import { api } from '$lib/api.js'
  import Tuile from '$lib/components/Tuile.svelte'
  import { Badge } from '$lib/components/ui/badge/index.js'
  import { Progress } from '$lib/components/ui/progress/index.js'
  import * as Chart from '$lib/components/ui/chart/index.js'

  let { ondeconnecte } = $props()
  let s = $state(null)
  let erreur = $state('')

  const graphique = { appels: { label: 'Appels', color: 'var(--chart-1)' } }

  async function lire() {
    try {
      s = await api.get('/api/synthese')
      erreur = ''
    } catch (err) {
      if (err.statut === 401) ondeconnecte()
      else erreur = err.message
    }
  }

  onMount(() => {
    lire()
    const id = setInterval(lire, 15000)
    return () => clearInterval(id)
  })

  function duree(secondes) {
    const j = Math.floor(secondes / 86400), h = Math.floor((secondes % 86400) / 3600), m = Math.floor((secondes % 3600) / 60)
    if (j) return `${j} j ${h} h`
    if (h) return `${h} h ${String(m).padStart(2, '0')}`
    return `${m} min`
  }
  const go = (octets) => (octets / 1e9).toLocaleString('fr-FR', { maximumFractionDigits: 1 })
</script>

<header class="mb-5 flex items-end justify-between gap-3">
  <div>
    <p class="etiquette">socle</p>
    <h1 class="titre">Synthèse</h1>
  </div>
  {#if s}<Badge variant="outline">v{s.version}</Badge>{/if}
</header>

{#if erreur}
  <p class="rounded-xl border border-destructive/40 p-4 text-sm text-destructive" role="alert">
    Lecture impossible : {erreur} Nouvel essai dans 15 secondes.
  </p>
{:else if !s}
  <p class="text-sm text-muted-foreground">Lecture des mesures…</p>
{:else}
  <div class="grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-4">
    <Tuile etiquette="Appels à l'API, 12 dernières minutes" class="col-span-2 md:row-span-2">
      <Chart.Container config={graphique} class="aspect-auto h-44 w-full md:h-full md:min-h-56">
        <BarChart
          data={s.appels_par_minute}
          xScale={scaleBand().padding(0.3)}
          x="minute"
          axis="x"
          series={[{ key: 'appels', label: 'Appels', color: graphique.appels.color }]}
          props={{ xAxis: { format: (m) => (m.endsWith('0') || m.endsWith('5') ? m : '') } }}
        >
          {#snippet tooltip()}
            <Chart.Tooltip />
          {/snippet}
        </BarChart>
      </Chart.Container>
    </Tuile>

    <Tuile etiquette="Appels servis" accent>
      <p class="chiffre text-5xl">{s.appels_total.toLocaleString('fr-FR')}</p>
      <p class="text-sm text-primary-foreground/75">depuis le démarrage</p>
    </Tuile>

    <Tuile etiquette="En service depuis">
      <p class="chiffre text-4xl">{duree(s.en_service_secondes)}</p>
      <p class="text-sm text-muted-foreground">démarré le {new Date(s.demarrage).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })}</p>
    </Tuile>

    <Tuile etiquette="Dossier de données" class="col-span-2">
      <div class="flex items-baseline justify-between gap-3">
        <p class="chiffre text-4xl">{Math.round(s.disque.pourcentage)} %</p>
        <p class="text-sm text-muted-foreground">{go(s.disque.utilise)} Go sur {go(s.disque.total)} Go</p>
      </div>
      <Progress value={s.disque.pourcentage} aria-label="Espace utilisé" />
      <div class="flex flex-wrap gap-2">
        {#if s.donnees_inscriptibles}
          <Badge variant="secondary"><span class="size-1.5 rounded-full bg-valide"></span> Écriture possible</Badge>
        {:else}
          <Badge variant="destructive">Écriture refusée : vérifie le volume /data</Badge>
        {/if}
      </div>
    </Tuile>

    <Tuile etiquette="Versions" class="col-span-2 md:col-span-4">
      <dl class="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-4">
        {#each s.versions as v}
          <div class="min-w-0">
            <dt class="text-sm text-muted-foreground">{v.nom}</dt>
            <dd class="truncate font-medium tabular-nums">{v.version}</dd>
          </div>
        {/each}
      </dl>
    </Tuile>
  </div>
{/if}

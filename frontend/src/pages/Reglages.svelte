<script>
  // « Réglages » : ce qui n'est pas un service. Toujours en bas : la version et la déconnexion.
  // 0.6.0 (motif commun, docs/format.md § 8) :
  //  - tuile « Réglages » : les réglages d'usage de l'appli (GET/PUT /api/reglages). Ils ne sont plus dans la stack :
  //    la variable n'a servi qu'une fois, au premier démarrage, pour reprendre la valeur ;
  //  - tuile « Restaurer les réglages » : l'Anneau garde chaque nuit une copie des réglages de chaque appli
  //    (sans secret). On choisit une date, on voit ce qui changerait (avant → sauvegardé), on confirme.
  import { onMount } from 'svelte'
  import { api } from '$lib/api.js'
  import { Button } from '$lib/components/ui/button/index.js'

  let { session, deconnecter } = $props()

  // Nom affiché de chaque réglage (une appli remplace cette table par la sienne)
  const NOMS = { message_accueil: "Message d'accueil", afficher_mesures: 'Graphique des appels' }
  const nom = (cle) => NOMS[cle] ?? cle

  // ------------------------------------------------------------ réglages
  let reglages = $state(null)
  let brouillon = $state({ message_accueil: '', afficher_mesures: true })
  let messageReglages = $state('')
  let enregistrement = $state(false)
  const modifie = $derived(reglages && JSON.stringify(brouillon) !== JSON.stringify(reglages))

  async function lireReglages() {
    try {
      reglages = (await api.get('/api/reglages')).reglages
      brouillon = { ...reglages }
    } catch (err) {
      messageReglages = err.message
    }
  }

  async function enregistrer(e) {
    e.preventDefault()
    enregistrement = true
    try {
      reglages = (await api.put('/api/reglages', brouillon)).reglages
      brouillon = { ...reglages }
      messageReglages = 'Réglages enregistrés.'
    } catch (err) {
      messageReglages = err.message
    }
    enregistrement = false
  }

  // ------------------------------------------------------------ restaurer
  let dates = $state(null)          // null : pas encore lu
  let choisie = $state('')
  let apercu = $state(null)         // { le, version, differences }
  let confirmer = $state(false)
  let messageRestaurer = $state('')
  let attente = $state(false)

  async function lireDates() {
    messageRestaurer = ''
    try {
      dates = (await api.get('/api/restaurer')).dates
      if (dates.length && !choisie) choisir(dates[0])
    } catch (err) {
      dates = []
      messageRestaurer = err.message
    }
  }

  async function choisir(le) {
    choisie = le
    apercu = null
    confirmer = false
    messageRestaurer = ''
    if (!le) return
    try {
      apercu = await api.get('/api/restaurer?le=' + encodeURIComponent(le))
    } catch (err) {
      messageRestaurer = err.message
    }
  }

  async function restaurer() {
    attente = true
    try {
      const r = await api.post('/api/restaurer', { le: choisie })
      reglages = r.reglages
      brouillon = { ...reglages }
      messageRestaurer = `${r.appliques.length} réglage${r.appliques.length > 1 ? 's' : ''} restauré${r.appliques.length > 1 ? 's' : ''}`
        + (r.ignores.length ? ` ; ignoré${r.ignores.length > 1 ? 's' : ''} (valeur d'une autre version) : ${r.ignores.map(nom).join(', ')}.` : '.')
      apercu = { ...apercu, differences: [] }
    } catch (err) {
      messageRestaurer = err.message
    }
    confirmer = false
    attente = false
  }

  function valeur(v) {
    if (v === true) return 'oui'
    if (v === false) return 'non'
    if (v === '' || v === null || v === undefined) return '(vide)'
    if (Array.isArray(v)) return v.length ? v.join(', ') : '(vide)'
    return String(v)
  }

  const jour = (le) => new Date(le + 'T12:00:00').toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })

  onMount(() => {
    lireReglages()
    lireDates()
  })
</script>

<header class="mb-5">
  <p class="etiquette">socle</p>
  <h1 class="titre">Réglages</h1>
</header>

<div class="grid gap-3 md:grid-cols-2 md:gap-4">
  <section class="flex min-w-0 flex-col gap-4 rounded-2xl border bg-card p-5" aria-label="Réglages">
    <div>
      <h2 class="text-lg font-semibold">Réglages</h2>
      <p class="mt-1 text-sm text-muted-foreground">Ils se changent ici, plus dans la stack. L'Anneau en garde une copie chaque nuit.</p>
    </div>
    {#if !reglages}
      <p class="text-sm text-muted-foreground" role="status">{messageReglages || 'Lecture des réglages…'}</p>
    {:else}
      <form class="flex flex-col gap-4" onsubmit={enregistrer}>
        <label class="flex flex-col gap-1.5 text-sm">
          {nom('message_accueil')}
          <input
            id="message-accueil"
            type="text"
            maxlength="200"
            placeholder="Affiché en tête de la Synthèse"
            bind:value={brouillon.message_accueil}
            class="h-10 min-w-0 rounded-lg border border-input bg-transparent px-3 text-base outline-none focus:border-ring"
          />
        </label>
        <div class="flex items-center justify-between gap-3 text-sm">
          <span id="libelle-mesures">{nom('afficher_mesures')} dans la Synthèse</span>
          <button
            type="button"
            role="switch"
            aria-checked={brouillon.afficher_mesures}
            aria-labelledby="libelle-mesures"
            onclick={() => (brouillon.afficher_mesures = !brouillon.afficher_mesures)}
            class="relative inline-flex h-7 w-12 shrink-0 items-center rounded-full border transition-colors
                   {brouillon.afficher_mesures ? 'border-transparent bg-primary' : 'bg-muted'}"
          >
            <span class="inline-block size-5 rounded-full transition-transform
                         {brouillon.afficher_mesures ? 'translate-x-6 bg-primary-foreground' : 'translate-x-1 bg-foreground'}"></span>
          </button>
        </div>
        <div class="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={!modifie || enregistrement}>{enregistrement ? 'Enregistrement…' : 'Enregistrer'}</Button>
          {#if messageReglages}<p class="text-sm" role="status">{messageReglages}</p>{/if}
        </div>
      </form>
    {/if}
  </section>

  <section class="flex min-w-0 flex-col gap-4 rounded-2xl border bg-card p-5" aria-label="Restaurer les réglages">
    <div>
      <h2 class="text-lg font-semibold">Restaurer les réglages</h2>
      <p class="mt-1 text-sm text-muted-foreground">Reprendre les réglages d'un jour gardé par l'Anneau. Seuls les réglages de l'appli changent.</p>
    </div>
    {#if dates === null}
      <p class="text-sm text-muted-foreground" role="status">Lecture des sauvegardes…</p>
    {:else if dates.length === 0}
      <p class="text-sm text-muted-foreground" role="status">{messageRestaurer || "L'Anneau n'a encore aucune sauvegarde du socle."}</p>
      <div><Button variant="outline" onclick={lireDates}>Réessayer</Button></div>
    {:else}
      <label class="flex flex-col gap-1.5 text-sm">
        Sauvegarde du
        <select
          id="date-sauvegarde"
          value={choisie}
          onchange={(e) => choisir(e.currentTarget.value)}
          class="h-10 min-w-0 rounded-lg border border-input bg-card px-3 text-base outline-none focus:border-ring"
        >
          {#each dates as d}<option value={d}>{jour(d)}</option>{/each}
        </select>
      </label>
      {#if apercu}
        {#if apercu.differences.length === 0}
          <p class="text-sm text-muted-foreground">Rien ne diffère des réglages actuels.</p>
        {:else}
          <ul class="flex flex-col divide-y rounded-xl border" aria-label="Différences">
            {#each apercu.differences as d}
              <li class="flex min-w-0 flex-col gap-0.5 px-3 py-2 text-sm">
                <span class="font-medium">{nom(d.cle)}</span>
                <span class="min-w-0 break-words text-muted-foreground">
                  {valeur(d.actuel)} <span aria-hidden="true">→</span><span class="sr-only">devient</span> <span class="text-foreground">{valeur(d.sauve)}</span>
                </span>
              </li>
            {/each}
          </ul>
          {#if confirmer}
            <div class="flex flex-wrap items-center gap-2" role="group" aria-label="Confirmer la restauration">
              <span class="text-sm">Remplacer {apercu.differences.length} réglage{apercu.differences.length > 1 ? 's' : ''} ?</span>
              <Button onclick={restaurer} disabled={attente}>Confirmer</Button>
              <Button variant="outline" onclick={() => (confirmer = false)}>Annuler</Button>
            </div>
          {:else}
            <div><Button onclick={() => (confirmer = true)}>Restaurer</Button></div>
          {/if}
        {/if}
      {/if}
      {#if messageRestaurer}<p class="text-sm" role="status">{messageRestaurer}</p>{/if}
    {/if}
  </section>

  <section class="rounded-2xl border bg-card p-5 md:col-span-2" aria-label="Écriture">
    <h2 class="text-lg font-semibold">Écriture</h2>
    <p class="mt-1 text-sm text-muted-foreground">
      {#if session.lecture_seule}
        Lecture seule : l'appli lit tout mais n'écrit nulle part hors de chez elle
        ({session.origine_lecture_seule === 'appli' ? 'APP_LECTURE_SEULE, pour cette appli seule' : 'MAISON_LECTURE_SEULE, pour toute la maison'}).
        Les réglages ci-dessus restent modifiables : ils sont à l'appli.
      {:else}
        L'appli écrit normalement. Pour le premier jour d'une nouvelle version : APP_LECTURE_SEULE=oui dans la stack (cette appli seule) ou MAISON_LECTURE_SEULE=oui (toutes).
      {/if}
    </p>
  </section>
</div>

<p class="mt-6 flex items-center justify-between gap-3 text-sm text-muted-foreground">
  <span>socle {session.version}</span>
  <Button variant="outline" onclick={deconnecter}>Se déconnecter</Button>
</p>

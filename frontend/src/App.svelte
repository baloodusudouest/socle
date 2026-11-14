<script>
  // Navigation commune aux applis (0.2.0) : rail à gauche sur PC, pilule d'icônes en bas sur iPhone.
  // Les entrées attendues dans une appli : son écran de travail ou « À traiter » en tuiles,
  // « Connexion » (une tuile par service extérieur) et « Réglages » (ce qui n'est pas un service,
  // la version, la déconnexion). Voir docs/format.md.
  import { onMount } from 'svelte'
  import { fly } from 'svelte/transition'
  import LayoutGrid from '@lucide/svelte/icons/layout-grid'
  import Network from '@lucide/svelte/icons/network'
  import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal'
  import Shapes from '@lucide/svelte/icons/shapes'
  import BookOpen from '@lucide/svelte/icons/book-open'
  import { api } from '$lib/api.js'
  import Connexion from './pages/Connexion.svelte'
  import Synthese from './pages/Synthese.svelte'
  import Services from './pages/Services.svelte'
  import Reglages from './pages/Reglages.svelte'
  import Composants from './pages/Composants.svelte'
  import Documents from './pages/Documents.svelte'

  const onglets = [
    { page: 'synthese', nom: 'Synthèse', icone: LayoutGrid },
    { page: 'connexion', nom: 'Connexion', icone: Network },
    { page: 'documents', nom: 'Documents', icone: BookOpen },
    { page: 'reglages', nom: 'Réglages', icone: SlidersHorizontal },
    { page: 'composants', nom: 'Composants', icone: Shapes },
  ]

  let connecte = $state(null) // null : on ne sait pas encore
  let session = $state({ version: '', lecture_seule: false })
  let page = $state(lirePage())

  function lirePage() {
    const p = location.hash.replace('#/', '')
    return onglets.some((o) => o.page === p) ? p : 'synthese'
  }

  async function verifier() {
    try {
      const s = await api.get('/api/session')
      session = s
      connecte = s.connecte
    } catch {
      connecte = false
    }
  }

  async function deconnecter() {
    try { await api.post('/api/deconnexion') } catch { /* déjà déconnecté */ }
    connecte = false
  }

  onMount(verifier)
</script>

<svelte:window onhashchange={() => (page = lirePage())} />

{#if connecte === false}
  <Connexion onconnecte={verifier} />
{:else if connecte}
  <div class="md:pl-52">
    <!-- iPhone : pilule flottante en bas, icônes seules (le nom de la section est le titre de l'écran).
         PC : rail à gauche, avec les noms. Mêmes entrées, même ordre. -->
    <nav
      aria-label="Sections"
      class="fixed bottom-[calc(0.75rem+env(safe-area-inset-bottom))] left-1/2 z-20 flex -translate-x-1/2 items-center gap-1 rounded-full border bg-card/80 p-1.5 shadow-lg backdrop-blur-md
             md:inset-y-0 md:left-0 md:w-52 md:translate-x-0 md:flex-col md:items-stretch md:gap-1 md:rounded-none md:border-0 md:border-r md:bg-transparent md:p-4 md:shadow-none md:backdrop-blur-none"
    >
      <span class="mb-4 hidden px-2 text-xl font-light tracking-tight md:block">socle</span>
      {#each onglets as o}
        {@const Icone = o.icone}
        <a
          href={'#/' + o.page}
          aria-label={o.nom}
          aria-current={page === o.page ? 'page' : undefined}
          class="flex h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-muted-foreground transition-colors
                 hover:text-foreground aria-[current=page]:bg-foreground aria-[current=page]:text-background
                 md:h-10 md:rounded-lg md:px-3 md:aria-[current=page]:bg-secondary md:aria-[current=page]:text-foreground"
        >
          <Icone class="size-[1.15rem]" aria-hidden="true" />
          <span class="sr-only md:not-sr-only">{o.nom}</span>
        </a>
      {/each}
    </nav>

    <main
      class="mx-auto max-w-5xl px-[max(1rem,env(safe-area-inset-left))] pt-[calc(1.25rem+env(safe-area-inset-top))] pb-[calc(6rem+env(safe-area-inset-bottom))] md:px-8 md:pt-8 md:pb-10"
    >
      {#if session.lecture_seule}
        <p class="mb-4 rounded-xl border border-primary/50 px-4 py-2 text-sm" role="status">
          Mode lecture seule : l'appli lit tout mais n'écrit nulle part (APP_LECTURE_SEULE).
        </p>
      {/if}
      {#key page}
        <div in:fly={{ y: 6, duration: 180 }}>
          {#if page === 'documents'}
            <Documents />
          {:else if page === 'composants'}
            <Composants />
          {:else if page === 'connexion'}
            <Services lectureSeule={session.lecture_seule} ondeconnecte={() => (connecte = false)} />
          {:else if page === 'reglages'}
            <Reglages {session} {deconnecter} />
          {:else}
            <Synthese ondeconnecte={() => (connecte = false)} />
          {/if}
        </div>
      {/key}
    </main>
  </div>
{/if}

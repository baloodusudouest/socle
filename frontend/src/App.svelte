<script>
  import { onMount } from 'svelte'
  import { fly } from 'svelte/transition'
  import LayoutGrid from '@lucide/svelte/icons/layout-grid'
  import Shapes from '@lucide/svelte/icons/shapes'
  import LogOut from '@lucide/svelte/icons/log-out'
  import { api } from '$lib/api.js'
  import Connexion from './pages/Connexion.svelte'
  import Synthese from './pages/Synthese.svelte'
  import Composants from './pages/Composants.svelte'

  const onglets = [
    { page: 'synthese', nom: 'Synthèse', icone: LayoutGrid },
    { page: 'composants', nom: 'Composants', icone: Shapes },
  ]

  let connecte = $state(null) // null : on ne sait pas encore
  let page = $state(lirePage())

  function lirePage() {
    const p = location.hash.replace('#/', '')
    return onglets.some((o) => o.page === p) ? p : 'synthese'
  }

  async function verifier() {
    try {
      connecte = (await api.get('/api/session')).connecte
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
    <!-- iPhone : pilule flottante en bas. PC : rail à gauche. Mêmes onglets, même ordre. -->
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
          aria-current={page === o.page ? 'page' : undefined}
          class="flex h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-muted-foreground transition-colors
                 hover:text-foreground aria-[current=page]:bg-foreground aria-[current=page]:text-background
                 md:h-10 md:rounded-lg md:px-3 md:aria-[current=page]:bg-secondary md:aria-[current=page]:text-foreground"
        >
          <Icone class="size-[1.15rem]" aria-hidden="true" />
          <span class={page === o.page ? '' : 'sr-only md:not-sr-only'}>{o.nom}</span>
        </a>
      {/each}
      <button
        type="button"
        onclick={deconnecter}
        class="flex h-11 items-center gap-2 rounded-full px-4 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground md:mt-auto md:h-10 md:rounded-lg md:px-3"
      >
        <LogOut class="size-[1.15rem]" aria-hidden="true" />
        <span class="sr-only md:not-sr-only">Se déconnecter</span>
      </button>
    </nav>

    <main
      class="mx-auto max-w-5xl px-[max(1rem,env(safe-area-inset-left))] pt-[calc(1.25rem+env(safe-area-inset-top))] pb-[calc(6rem+env(safe-area-inset-bottom))] md:px-8 md:pt-8 md:pb-10"
    >
      {#key page}
        <div in:fly={{ y: 6, duration: 180 }}>
          {#if page === 'composants'}
            <Composants />
          {:else}
            <Synthese ondeconnecte={() => (connecte = false)} />
          {/if}
        </div>
      {/key}
    </main>
  </div>
{/if}

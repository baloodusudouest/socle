<script>
  // « Documents » : les documents du socle, lus dans le dépôt au moment de compiler l'interface
  // (format commun, leçons apprises, reprise, journal des versions). Rien n'est lu sur le réseau.
  import { marked } from 'marked'
  import format from '../../../docs/format.md?raw'
  import lecons from '../../../docs/lecons.md?raw'
  import reprise from '../../../REPRISE.md?raw'
  import journal from '../../../CHANGELOG.md?raw'

  const DOCS = [
    { cle: 'format', nom: 'Format commun', but: 'Ce que chaque appli maison reprend : navigation, sécurité, méthode, couleurs.', texte: format },
    { cle: 'lecons', nom: 'Leçons apprises', but: 'Ce qui a été construit, cassé et corrigé en partant du socle.', texte: lecons },
    { cle: 'reprise', nom: 'Reprise', but: 'Où en est le socle, à lire avant de le modifier.', texte: reprise },
    { cle: 'journal', nom: 'Journal des versions', but: 'Ce qui a changé, version par version.', texte: journal },
  ]
  const lire = () => {
    try { return sessionStorage.getItem('socle-doc') || 'format' } catch { return 'format' }
  }
  let choisi = $state(lire())
  const doc = $derived(DOCS.find((d) => d.cle === choisi) || DOCS[0])
  const ancre = (t) => t.toLowerCase().normalize('NFD').replace(/\p{Mn}/gu, '').replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
  // Titres de niveau 2 : sommaire du document et ancres
  const sommaire = $derived([...doc.texte.matchAll(/^## (.+)$/gm)].map((m) => ({ titre: m[1].replace(/[`*]/g, ''), id: ancre(m[1]) })))
  const html = $derived(marked.parse(doc.texte, {
    renderer: Object.assign(new marked.Renderer(), {
      heading({ tokens, depth }) { const t = this.parser.parseInline(tokens); return `<h${depth} id="${ancre(t.replace(/<[^>]+>/g, ''))}">${t}</h${depth}>` },
      link({ href, title, tokens }) { const t = this.parser.parseInline(tokens); return /^https?:/.test(href) ? `<a href="${href}" target="_blank" rel="noopener">${t}</a>` : `<span class="lien-interne">${t}</span>` },
    }),
  }))
  function choisir(cle) {
    choisi = cle
    try { sessionStorage.setItem('socle-doc', cle) } catch { /* sans stockage, on garde le choix en mémoire */ }
    window.scrollTo(0, 0)
  }
  function aller(e, id) {
    e.preventDefault()
    document.getElementById(id)?.scrollIntoView({ block: 'start', behavior: 'smooth' })
  }
</script>

<header class="mb-5">
  <p class="text-sm text-muted-foreground">socle</p>
  <h1 class="text-3xl font-light tracking-tight md:text-4xl">Documents</h1>
  <p class="mt-1 max-w-prose text-sm text-muted-foreground">Le modèle des applis maison, écrit : on repart d'ici pour en créer une nouvelle.</p>
</header>

<div class="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Documents">
  {#each DOCS as d}
    <button role="tab" aria-selected={choisi === d.cle} onclick={() => choisir(d.cle)}
            class="h-10 shrink-0 rounded-full border px-4 text-sm font-medium transition-colors aria-selected:border-foreground aria-selected:bg-foreground aria-selected:text-background">
      {d.nom}
    </button>
  {/each}
</div>
<p class="mt-2 text-sm text-muted-foreground">{doc.but}</p>

<div class="mt-5 grid gap-8 lg:grid-cols-[minmax(0,1fr)_14rem]">
  <article class="doc min-w-0" role="tabpanel" aria-label={doc.nom}>{@html html}</article>
  {#if sommaire.length > 2}
    <nav class="sommaire hidden lg:block" aria-label="Sommaire">
      <p class="mb-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">Sommaire</p>
      <ul class="space-y-1.5 text-sm">
        {#each sommaire as s}<li><a href={'#' + s.id} onclick={(e) => aller(e, s.id)} class="text-muted-foreground hover:text-foreground">{s.titre}</a></li>{/each}
      </ul>
    </nav>
  {/if}
</div>

<style>
  .sommaire { position: sticky; top: 2rem; align-self: start; max-height: calc(100dvh - 4rem); overflow-y: auto; }
  .doc { line-height: 1.65; font-size: 0.95rem; }
  .doc :global(h1) { display: none; }
  .doc :global(h2) { margin: 2rem 0 0.6rem; font-size: 1.3rem; font-weight: 600; letter-spacing: -0.01em; scroll-margin-top: 1rem; }
  .doc :global(h2:first-of-type) { margin-top: 0; }
  .doc :global(h3) { margin: 1.4rem 0 0.4rem; font-size: 1.05rem; font-weight: 600; }
  .doc :global(p), .doc :global(ul), .doc :global(ol) { margin: 0 0 0.8rem; max-width: 70ch; }
  .doc :global(ul), .doc :global(ol) { padding-left: 1.25rem; }
  .doc :global(ul) { list-style: disc; }
  .doc :global(ol) { list-style: decimal; }
  .doc :global(li) { margin: 0.25rem 0; }
  .doc :global(li::marker) { color: var(--color-muted-foreground); }
  .doc :global(code) { font-size: 0.85em; padding: 0.05rem 0.35rem; border-radius: 0.35rem; background: var(--color-muted); overflow-wrap: anywhere; }
  .doc :global(pre) { margin: 0 0 1rem; padding: 0.8rem 1rem; border-radius: 0.7rem; background: var(--color-muted); overflow-x: auto; font-size: 0.82rem; }
  .doc :global(pre code) { padding: 0; background: none; }
  .doc :global(table) { display: block; overflow-x: auto; border-collapse: collapse; margin: 0 0 1rem; font-size: 0.88rem; }
  .doc :global(th), .doc :global(td) { border-bottom: 1px solid var(--color-border); padding: 0.45rem 0.7rem; text-align: left; vertical-align: top; }
  .doc :global(th) { font-weight: 600; color: var(--color-muted-foreground); }
  .doc :global(blockquote) { margin: 0 0 1rem; padding-left: 0.9rem; border-left: 3px solid var(--color-primary); color: var(--color-muted-foreground); }
  .doc :global(a) { text-decoration: underline; text-underline-offset: 3px; }
  .doc :global(strong) { font-weight: 600; }
  .doc :global(hr) { margin: 1.5rem 0; border-color: var(--color-border); }
</style>

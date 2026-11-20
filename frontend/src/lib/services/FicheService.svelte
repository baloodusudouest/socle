<script>
  // Fiche d'un service extérieur (contrat 3 des applis maison, socle 0.10.0).
  // Fichier COMMUN : écrit dans baloodusudouest/socle (frontend/src/lib/services/), copié TEL QUEL dans chaque appli
  // par tools/diffuser_maison.py ; la dernière ligne porte une empreinte que les tests de l'appli recalculent.
  // Ne le modifier que dans le socle. Aucune dépendance : classes Tailwind sur les jetons communs
  // (card, border, muted-foreground, primary, destructive, input).
  //
  // service : une entrée de GET /api/maison/services
  //   { id, nom, etat (repond | ne_repond_pas | relie | pas_relie), lit, ecrit, reglage, detail,
  //     verifie_le, derniere_ecriture, gestes: [{ id, nom }] }
  // onverifier(service) : lance « Vérifier » (contour, ne teste que ce service, n'écrit rien)
  // ongeste(service, geste) : le geste qui écrit (Synchroniser, Livrer…), seul bouton plein de la fiche
  // enCours : « verifier », l'id du geste en cours, ou ''
  // simule : fiche du Bac à sable (bandeau « Simulé »)
  // message : phrase visible sous la fiche (erreur, résultat d'un geste) ; annonce : lue seulement par le lecteur d'écran
  let {
    service,
    onverifier = null,
    ongeste = null,
    enCours = '',
    lectureSeule = false,
    simule = false,
    message = '',
    annonce = '',
    titreNiveau = 2,
  } = $props()

  const MOTS = { repond: 'Répond', ne_repond_pas: 'Ne répond pas', relie: 'Relié', pas_relie: 'Pas relié' }
  const regle = $derived(service.etat !== 'pas_relie')
  const geste = $derived(service.gestes?.[0] ?? null)

  // « il y a 3 h » : l'âge d'une date ISO, en mots
  function age(iso) {
    if (!iso) return ''
    const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000)
    if (!Number.isFinite(s)) return ''
    if (s < 60) return "à l'instant"
    if (s < 3600) return `il y a ${Math.round(s / 60)} min`
    if (s < 86400) return `il y a ${Math.round(s / 3600)} h`
    const j = Math.round(s / 86400)
    return `il y a ${j} jour${j > 1 ? 's' : ''}`
  }
</script>

<article class="rounded-2xl border bg-card p-5 text-card-foreground" aria-labelledby={'service-' + service.id}>
  <div class="flex items-center gap-2.5">
    <span
      aria-hidden="true"
      class="size-2.5 shrink-0 rounded-full {service.etat === 'repond'
        ? 'bg-primary'
        : service.etat === 'ne_repond_pas'
          ? 'bg-destructive'
          : service.etat === 'relie'
            ? 'bg-muted-foreground'
            : 'border-2 border-muted-foreground'}"
    ></span>
    <svelte:element this={'h' + titreNiveau} id={'service-' + service.id} class="text-lg font-semibold leading-tight">
      {service.nom}
    </svelte:element>
    {#if simule}<span class="rounded-full border px-2 py-0.5 text-xs text-muted-foreground">Simulé</span>{/if}
    <span class="ml-auto text-sm {service.etat === 'ne_repond_pas' ? 'text-destructive' : 'text-muted-foreground'}">
      {MOTS[service.etat] ?? service.etat}
    </span>
  </div>

  <dl class="mt-4 grid gap-3 text-[0.95rem] leading-snug">
    <div>
      <dt class="text-sm text-muted-foreground">Ce qui est lu</dt>
      <dd class="mt-0.5">{service.lit}</dd>
    </div>
    <div>
      <dt class="text-sm text-muted-foreground">Ce qui est écrit</dt>
      <dd class="mt-0.5">{service.ecrit}</dd>
    </div>
    {#if !regle && service.reglage}
      <div>
        <dt class="text-sm text-muted-foreground">Pour le relier, dans la stack</dt>
        <dd class="mt-0.5 font-mono text-sm">{service.reglage}</dd>
      </div>
    {/if}
  </dl>

  {#if regle && (service.detail || service.verifie_le || service.derniere_ecriture)}
    <p class="mt-3 text-sm text-muted-foreground">
      {#if service.detail}<span class={service.etat === 'ne_repond_pas' ? 'text-destructive' : 'text-foreground'}>{service.detail}</span>{/if}
      {#if service.verifie_le}<span>{service.detail ? ' · ' : ''}Vérifié {age(service.verifie_le)}</span>{/if}
      {#if service.derniere_ecriture}<span>{service.detail || service.verifie_le ? ' · ' : ''}Dernière écriture {age(service.derniere_ecriture)}</span>{/if}
    </p>
  {/if}

  <p class="sr-only" aria-live="polite">{annonce || message || (enCours === 'verifier' ? 'Vérification en cours.' : '')}</p>
  {#if message}<p class="mt-3 text-sm" role="status">{message}</p>{/if}

  {#if regle && (onverifier || (geste && ongeste))}
    <div class="mt-4 flex flex-wrap items-center gap-2">
      {#if onverifier}
        <button
          type="button"
          class="inline-flex min-h-11 items-center rounded-xl border border-input px-4 text-[0.95rem] font-medium transition-colors hover:bg-foreground/5 disabled:opacity-60"
          aria-busy={enCours === 'verifier'}
          disabled={!!enCours}
          onclick={() => onverifier(service)}
        >{enCours === 'verifier' ? 'Vérification…' : 'Vérifier'}</button>
      {/if}
      {#if geste && ongeste}
        <button
          type="button"
          class="inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-[0.95rem] font-medium text-primary-foreground transition-opacity hover:opacity-90 disabled:opacity-60"
          aria-busy={enCours === geste.id}
          disabled={!!enCours || lectureSeule}
          title={lectureSeule ? 'Mode lecture seule : rien n\'est écrit.' : undefined}
          onclick={() => ongeste(service, geste)}
        >{enCours === geste.id ? geste.nom + '…' : geste.nom}</button>
        {#if lectureSeule}<span class="text-sm text-muted-foreground">Lecture seule : rien n'est écrit.</span>{/if}
      {/if}
    </div>
  {/if}
</article>
<!-- empreinte: 6a86c294c48baf9b -->

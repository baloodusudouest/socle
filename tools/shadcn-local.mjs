#!/usr/bin/env node
// Copie des composants shadcn-svelte depuis une copie locale du dépôt officiel
// (github.com/huntabyte/shadcn-svelte), quand le site du registre n'est pas joignable.
// Fait ce que fait la commande officielle : les classes abstraites « cn-… » des sources
// sont remplacées par les utilitaires Tailwind du style choisi.
//
//   node tools/shadcn-local.mjs <dépôt shadcn-svelte> <style> <composant> [composant…]
//   node tools/shadcn-local.mjs ../shadcn-svelte nova button card badge
//
// Quand le registre est joignable, préférer : npx shadcn-svelte@latest add <composant>
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const [depot, style, ...composants] = process.argv.slice(2)
if (!depot || !style || !composants.length) {
  console.error('Usage : node tools/shadcn-local.mjs <dépôt> <style> <composant…>')
  process.exit(1)
}
const registre = join(depot, 'docs/src/lib/registry')
const css = readFileSync(join(registre, 'styles', `style-${style}.css`), 'utf8')

// .cn-nom { @apply a b c; }  →  { 'cn-nom': 'a b c' }
const regles = {}
for (const m of css.matchAll(/\.(cn-[a-z0-9-]+)\s*\{\s*@apply\s+([^;]+);\s*\}/g)) regles[m[1]] = m[2].trim()

const sortie = join(dirname(fileURLToPath(import.meta.url)), '../frontend/src/lib/components/ui')
for (const nom of composants) {
  const source = join(registre, 'ui', nom)
  mkdirSync(join(sortie, nom), { recursive: true })
  for (const fichier of readdirSync(source)) {
    let texte = readFileSync(join(source, fichier), 'utf8')
    // Une classe « cn-… » sans règle dans ce style disparaît, comme avec la commande officielle
    texte = texte.replace(/(?<![\w-])(cn-[a-z0-9-]+)(?![\w-])( ?)/g, (_, c, espace) => (regles[c] ? regles[c] + espace : ''))
    writeFileSync(join(sortie, nom, fichier), texte)
  }
  console.log(`✓ ${nom}`)
}

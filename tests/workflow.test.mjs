// Control-flow tests for skills/metadump/scripts/index.workflow.js with mocked agents.
// Run: node --test tests/
import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SCRIPT = process.env.METADUMP_WORKFLOW || join(HERE, '..', 'skills', 'metadump', 'scripts', 'index.workflow.js')

function load() {
  const src = readFileSync(SCRIPT, 'utf8')
  const metaMatch = src.match(/export const meta = (\{[\s\S]*?\n\})\n/)
  assert.ok(metaMatch, 'script must start with export const meta = {...}')
  const meta = Function(`return (${metaMatch[1]})`)()
  const body = src.replace(metaMatch[0], '')
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  return { meta, run: new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'budget', body) }
}

// behaviour(label, prompt, opts) -> return value for that agent call
async function runWith(args, behaviour) {
  const { run } = load()
  const calls = []
  const phases = []
  const agent = async (prompt, opts = {}) => {
    calls.push({ label: opts.label, prompt, opts })
    return behaviour(opts.label || '', prompt, opts)
  }
  const parallel = async thunks => Promise.all(thunks.map(t => t().catch(() => null)))
  const pipeline = async () => { throw new Error('not used') }
  const result = await run(args, agent, parallel, pipeline, p => phases.push(p), () => {}, { total: null })
  return { result, calls, labels: calls.map(c => c.label), phases }
}

const TICKETS = [
  { id: '10-observe-r1', type: 'observe' },
  { id: '20-research-lineage', type: 'research' },
  { id: '30-composition', type: 'specialist' },
  { id: '31-palette', type: 'specialist' },
  { id: '70-lexicon', type: 'lexicon' },
  { id: '75-exclusion', type: 'exclusion' },
  { id: '01-prompt', type: 'prompt' },
]
const ARGS = { skill_dir: '/skill', work_dir: '/proj/metadumps/.work/demo', slug: 'demo', depth: 'standard', tickets: TICKETS }

function standard({ guessesByRound = { 1: 1, 2: 0 }, gapEntries = 20, synthOk = true } = {}) {
  return (label, prompt) => {
    const round = Number((prompt.match(/Round (\d+)/) || [0, 1])[1])
    if (label.startsWith('synthesis')) return synthOk ? { built: true, dump_path: '/proj/metadumps/demo.metadump.json', jobs: ['understand the task', 'write the image prompt', 'check an output'] } : { built: false, jobs: [], errors: ['unresolved_route_path'] }
    if (label.startsWith('verify')) return { job: label, guesses: Array.from({ length: guessesByRound[round] || 0 }, () => ({ decision: 'band order', tier: 1, section: 'palette' })), misses: [], lookups: 2 }
    if (label.startsWith('audit')) return { missing_clauses: [], demoted: [] }
    if (label.startsWith('gaps')) return { tickets: [{ id: '60-gap-palette-r2', type: 'specialist' }] }
    if (label.includes('gap')) return { id: label, path: 'x', n_entries: gapEntries }
    return { id: label, path: 'x', n_entries: 10 }
  }
}

test('meta is a pure literal with phases matching phase() titles', () => {
  const { meta } = load()
  assert.equal(meta.name, 'metadump-index')
  const src = readFileSync(SCRIPT, 'utf8')
  for (const p of meta.phases) assert.ok(src.includes(`'${p.title}'`), `phase ${p.title} used`)
})

test('runs evidence before specialists and skips the main-loop prompt ticket', async () => {
  const { labels } = await runWith(ARGS, standard())
  assert.ok(labels.indexOf('observe:10-observe-r1') < labels.indexOf('specialist:30-composition'))
  assert.ok(labels.indexOf('research:20-research-lineage') < labels.indexOf('lexicon:70-lexicon'))
  assert.ok(!labels.some(l => l.includes('01-prompt')))
})

test('tier-1 guesses trigger a gap round, then a second normalize/synthesis/verify', async () => {
  const { result, labels } = await runWith(ARGS, standard())
  assert.equal(result.rounds, 2)
  for (const l of ['normalize:r1', 'synthesis:r1', 'audit:r1', 'gaps:r1', 'specialist:60-gap-palette-r2', 'normalize:r2', 'synthesis:r2', 'audit:r2']) {
    assert.ok(labels.includes(l), `missing ${l}`)
  }
  assert.ok(labels.indexOf('specialist:60-gap-palette-r2') < labels.indexOf('normalize:r2'))
  assert.deepEqual(result.gap_tickets, ['60-gap-palette-r2'])
})

test('second-round normalize writes its own shard instead of overwriting round 1', async () => {
  const { calls } = await runWith(ARGS, standard())
  const n2 = calls.find(c => c.label === 'normalize:r2')
  assert.match(n2.prompt, /shards\/91-normalize-r2\.json/)
  const a2 = calls.find(c => c.label === 'audit:r2')
  assert.match(a2.prompt, /shards\/96-audit-r2\.json/)
})

test('lite depth never runs a gap round even with guesses', async () => {
  const { result, labels } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: { 1: 3 } }))
  assert.equal(result.rounds, 1)
  assert.ok(!labels.some(l => l.startsWith('gaps')))
})

test('lite depth verifies at most two jobs', async () => {
  const { labels } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: {} }))
  assert.equal(labels.filter(l => l.startsWith('verify')).length, 2)
})

test('a failed build stops before verify so the main loop can repair it', async () => {
  const { result, labels } = await runWith(ARGS, standard({ synthOk: false }))
  assert.equal(result.builds[0].built, false)
  assert.ok(!labels.some(l => l.startsWith('verify') || l.startsWith('audit')))
})

test('a gap round adding under 10% entries is synthesized but not verified again', async () => {
  const { result, labels } = await runWith(ARGS, standard({ gapEntries: 1 }))
  assert.equal(result.stop_reason, 'gap round added under 10% new entries')
  assert.ok(labels.includes('synthesis:r2'))
  assert.ok(!labels.includes('audit:r2'))
})

test('no guesses and no missing clauses stops after one round', async () => {
  const { result, labels } = await runWith(ARGS, standard({ guessesByRound: {} }))
  assert.equal(result.rounds, 1)
  assert.ok(!labels.some(l => l.startsWith('gaps')))
})

test('missing args throws a clear error', async () => {
  await assert.rejects(() => runWith({}, standard()), /needs args/)
})

test('workers are pointed at the briefs file and their own shard path', async () => {
  const { calls } = await runWith(ARGS, standard())
  const spec = calls.find(c => c.label === 'specialist:31-palette')
  assert.match(spec.prompt, /\/skill\/references\/briefs\.md/)
  assert.match(spec.prompt, /\/proj\/metadumps\/\.work\/demo\/shards\/31-palette\.json/)
  assert.equal(spec.opts.schema.required.includes('n_entries'), true)
})

test('lite depth skips normalize and audit to stay near five agents', async () => {
  const { labels } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: {} }))
  assert.ok(!labels.some(l => l.startsWith('normalize') || l.startsWith('audit')), labels.join(', '))
  assert.ok(labels.includes('synthesis:r1'))
})

test('every worker prompt states the depth and its entry budget', async () => {
  const { calls } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: {} }))
  const spec = calls.find(c => c.label === 'specialist:30-composition')
  assert.match(spec.prompt, /Depth: lite/)
  assert.match(spec.prompt, /Entry budget: 12-20 entries/)
  const research = calls.find(c => c.label === 'research:20-research-lineage')
  assert.match(research.prompt, /Entry budget: 8-12 entries/)
})

test('stopping with tier-1/2 guesses hands them to the main loop as remaining gaps', async () => {
  const { result } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: { 1: 2 } }))
  assert.equal(result.remaining_gaps.length, 4) // 2 guesses x 2 verified jobs
  assert.match(result.next, /open_questions/)
})

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

// ---------------------------------------------------------------- 0.2.0: pages, videos, images
const MEDIA = [
  { id: '15-scrape-docs', type: 'scrape' },
  { id: '16-watch-talk', type: 'watch' },
  { id: '17-moodboard', type: 'moodboard' },
  { id: '20-research-lineage', type: 'research' },
  { id: '30-composition', type: 'specialist' },
  { id: '75-exclusion', type: 'exclusion' },
]

test('scrape, watch and moodboard tickets run in the evidence phase before specialists', async () => {
  const { labels, calls } = await runWith({ ...ARGS, tickets: MEDIA }, standard({ guessesByRound: {} }))
  const spec = labels.indexOf('specialist:30-composition')
  for (const l of ['scrape:15-scrape-docs', 'watch:16-watch-talk', 'moodboard:17-moodboard']) {
    assert.ok(labels.includes(l), `missing ${l}`)
    assert.ok(labels.indexOf(l) < spec, `${l} should run before specialists`)
    assert.equal(calls.find(c => c.label === l).opts.phase, 'Evidence')
  }
})

test('moodboard tickets start after the scrape and watch tickets whose images they collect', async () => {
  const { labels } = await runWith({ ...ARGS, tickets: MEDIA }, standard({ guessesByRound: {} }))
  const mood = labels.indexOf('moodboard:17-moodboard')
  assert.ok(labels.indexOf('scrape:15-scrape-docs') < mood)
  assert.ok(labels.indexOf('watch:16-watch-talk') < mood)
  assert.ok(labels.indexOf('research:20-research-lineage') < mood)
})

test('media evidence tickets carry an entry budget for every depth', async () => {
  const want = {
    lite: { scrape: '8-15', watch: '8-15', moodboard: '6-12' },
    standard: { scrape: '15-25', watch: '15-30', moodboard: '10-20' },
    deep: { scrape: '25-40', watch: '25-45', moodboard: '15-30' },
  }
  for (const depth of Object.keys(want)) {
    const { calls } = await runWith({ ...ARGS, depth, tickets: MEDIA }, standard({ guessesByRound: {} }))
    for (const [type, budget] of Object.entries(want[depth])) {
      const call = calls.find(c => c.label.startsWith(`${type}:`))
      assert.match(call.prompt, new RegExp(`Entry budget: ${budget} entries`), `${depth} ${type}`)
      assert.match(call.prompt, new RegExp(`"${type}" section of /skill/references/briefs\\.md`))
    }
  }
})

test('a gap round may add scrape or watch evidence tickets', async () => {
  const behaviour = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [{ id: '61-gap-scrape-r2', type: 'scrape' }, { id: '62-gap-motion-r2', type: 'specialist' }] }
    return standard()(label, prompt)
  }
  const { labels } = await runWith(ARGS, behaviour)
  assert.ok(labels.includes('scrape:61-gap-scrape-r2'))
  assert.ok(labels.indexOf('scrape:61-gap-scrape-r2') < labels.indexOf('specialist:62-gap-motion-r2'))
})

test('meta phases describe the new evidence and review prompts', () => {
  const { meta } = load()
  const evidence = meta.phases.find(p => p.title === 'Evidence').detail
  for (const word of ['pages', 'videos', 'images']) assert.match(evidence, new RegExp(word))
  assert.match(meta.phases.find(p => p.title === 'Synthesis').detail, /review prompts/)
})

test('verify contradictions count as tier-1 gaps and reach the gap planner', async () => {
  const behaviour = (label, prompt) => {
    if (label.startsWith('verify')) {
      const round = Number((prompt.match(/Round (\d+)/) || [0, 1])[1])
      return { job: label, guesses: [], misses: [], lookups: 2,
        contradictions: round === 1 ? [{ value_id: 'p-tint-alpha', against_id: 'inv-color-inside', why: 'pale' }] : [] }
    }
    return standard({ guessesByRound: {} })(label, prompt)
  }
  const { result, calls } = await runWith({ ...ARGS, depth: 'lite' }, behaviour)
  assert.equal(result.remaining_gaps.length, 2) // one contradiction x 2 verified jobs
  assert.match(result.remaining_gaps[0].decision, /contradiction: p-tint-alpha/)
  assert.equal(result.remaining_gaps[0].tier, 1)
  const std = await runWith(ARGS, behaviour)
  const gaps = std.calls.find(c => c.label === 'gaps:r1')
  assert.ok(gaps, 'a contradiction alone should trigger a gap round')
  assert.match(gaps.prompt, /inv-color-inside/)
  assert.ok(calls.find(c => c.label.startsWith('verify')).opts.schema.properties.contradictions)
})

// ---------------------------------------------------------------- 0.3.0: discovery
const PICKS = {
  videos: [{ url: 'https://upload.wikimedia.org/x/demo.webm', slug: 'demo', answers: 'how long the open takes', take: 'timing 0-3s' }],
  pages: [{ url: 'https://maker.example/product', slug: 'maker', answers: 'what the shell is made of' }],
  images: [],
}
const DISCOVERY = [
  { id: '07-discover', type: 'discover' },
  { id: '29-moodboard', type: 'moodboard' },
  { id: '30-composition', type: 'specialist' },
]
const withDiscover = (picks, base = standard({ guessesByRound: {} })) => (label, prompt, opts) =>
  label.startsWith('discover') ? picks : base(label, prompt, opts)

test('a discover ticket returns picks; the watch and scrape tickets made for them run as evidence before the moodboard', async () => {
  const { labels, calls } = await runWith({ ...ARGS, tickets: DISCOVERY }, withDiscover(PICKS))
  const disc = calls.find(c => c.label === 'discover:07-discover')
  assert.ok(disc, 'discover ticket runs')
  assert.match(disc.prompt, /no shard/)
  assert.match(disc.prompt, /discovered\/07-discover\.json/)
  assert.ok(disc.opts.schema.properties.videos && disc.opts.schema.properties.pages && disc.opts.schema.properties.images)
  const mood = labels.indexOf('moodboard:29-moodboard')
  const spec = labels.indexOf('specialist:30-composition')
  for (const l of ['watch:19-watch-found-demo', 'scrape:28-scrape-found-maker']) {
    assert.ok(labels.includes(l), `missing ${l} in ${labels.join(', ')}`)
    assert.ok(labels.indexOf('discover:07-discover') < labels.indexOf(l))
    assert.ok(labels.indexOf(l) < mood, `${l} before moodboard`)
    assert.ok(labels.indexOf(l) < spec, `${l} before specialists`)
    assert.equal(calls.find(c => c.label === l).opts.phase, 'Evidence')
  }
})

test('found tickets carry their URL and question, say they are web-found, and write their own shard', async () => {
  const { calls } = await runWith({ ...ARGS, tickets: DISCOVERY }, withDiscover(PICKS))
  const watch = calls.find(c => c.label === 'watch:19-watch-found-demo')
  assert.match(watch.prompt, /https:\/\/upload\.wikimedia\.org\/x\/demo\.webm/)
  assert.match(watch.prompt, /how long the open takes/)
  assert.match(watch.prompt, /timing 0-3s/)
  assert.match(watch.prompt, /origin: web/)
  assert.match(watch.prompt, /researched/)
  assert.match(watch.prompt, /never .*--reference/)
  assert.match(watch.prompt, /shards\/19-watch-found-demo\.json/)
  const scrape = calls.find(c => c.label === 'scrape:28-scrape-found-maker')
  assert.match(scrape.prompt, /https:\/\/maker\.example\/product/)
  assert.match(scrape.prompt, /origin: web/)
  assert.match(scrape.opts.schema.required.join(), /n_entries/)
})

test('discovery caps videos, pages and images per depth, states the caps, and reports every drop by URL', async () => {
  const many = {
    videos: Array.from({ length: 7 }, (_, i) => ({ url: `https://v.example/${i}.mp4`, slug: `v${i}` })),
    pages: Array.from({ length: 7 }, (_, i) => ({ url: `https://p.example/${i}`, slug: `p${i}` })),
    images: Array.from({ length: 30 }, (_, i) => ({ url: `https://i.example/${i}.png` })),
  }
  const want = { lite: [1, 1, 6], standard: [3, 3, 12], deep: [5, 6, 24] }
  for (const [depth, [videos, pages, images]] of Object.entries(want)) {
    const { labels, calls, result } = await runWith({ ...ARGS, depth, tickets: DISCOVERY }, withDiscover(many))
    assert.equal(labels.filter(l => l.startsWith('watch:')).length, videos, `${depth} videos`)
    assert.equal(labels.filter(l => l.startsWith('scrape:')).length, pages, `${depth} pages`)
    assert.equal(result.discovery.images.length, images, `${depth} images`)
    assert.match(calls.find(c => c.label === 'discover:07-discover').prompt,
      new RegExp(`at most ${videos} videos, ${pages} pages and ${images} images`), depth)
    const dropped = result.discovery.dropped
    assert.equal(dropped.length, (7 - videos) + (7 - pages) + (30 - images), `${depth} dropped`)
    assert.ok(dropped.some(d => d.kind === 'video' && d.url === 'https://v.example/6.mp4' && d.by === '07-discover'))
    assert.ok(dropped.some(d => d.kind === 'image' && d.url === 'https://i.example/29.png'))
  }
})

test('found images reach the moodboard prompt, which is added if the chart planned none', async () => {
  const withImages = { ...PICKS, images: [{ url: 'https://upload.wikimedia.org/x/shell.jpg', page: 'https://commons.wikimedia.org/wiki/File:Shell.jpg', license: 'CC BY-SA 4.0' }] }
  const planned = await runWith({ ...ARGS, tickets: DISCOVERY }, withDiscover(withImages))
  const board = planned.calls.find(c => c.label === 'moodboard:29-moodboard')
  assert.match(board.prompt, /https:\/\/upload\.wikimedia\.org\/x\/shell\.jpg/)
  assert.match(board.prompt, /CC BY-SA 4\.0/)
  assert.match(board.prompt, /images\.py collect --work \S+ --found \S+\/images\/found-29-moodboard\.json/)
  assert.equal(planned.labels.filter(l => l.startsWith('moodboard:')).length, 1)

  const noBoard = DISCOVERY.filter(t => t.type !== 'moodboard')
  const added = await runWith({ ...ARGS, tickets: noBoard }, withDiscover(withImages))
  assert.ok(added.labels.includes('moodboard:29-moodboard'), added.labels.join(', '))
  assert.ok(added.labels.indexOf('watch:19-watch-found-demo') < added.labels.indexOf('moodboard:29-moodboard'))

  const none = await runWith({ ...ARGS, tickets: noBoard }, withDiscover(PICKS))
  assert.ok(!none.labels.some(l => l.startsWith('moodboard:')), 'no images found, no moodboard added')
})

test('only one discover ticket runs per wave; an extra one is reported, not run', async () => {
  const two = [...DISCOVERY, { id: '08-discover-more', type: 'discover' }]
  const { labels, result } = await runWith({ ...ARGS, tickets: two }, withDiscover(PICKS))
  assert.equal(labels.filter(l => l.startsWith('discover:')).length, 1)
  assert.ok(labels.includes('discover:07-discover'))
  assert.ok(result.discovery.dropped.some(d => d.kind === 'discover' && d.by === '08-discover-more'))
})

test('found ticket ids never collide with each other or with planned tickets', async () => {
  const same = { videos: [{ url: 'https://v.example/a.mp4', slug: 'demo' }, { url: 'https://v.example/b.mp4', slug: 'demo' }], pages: [], images: [] }
  const planned = [...DISCOVERY, { id: '19-watch-found-demo', type: 'watch' }]
  const { labels, result } = await runWith({ ...ARGS, tickets: planned }, withDiscover(same))
  assert.equal(labels.filter(l => l === 'watch:19-watch-found-demo').length, 1, labels.join(', '))
  assert.deepEqual(result.discovery.found, ['19-watch-found-demo-2', '19-watch-found-demo-3'])
})

test('a gap round may run discover: its tickets run before gap specialists, and its images get their own moodboard pass', async () => {
  const behaviour = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [{ id: '63-gap-motion-discover-r2', type: 'discover' }, { id: '64-gap-motion-r2', type: 'specialist' }] }
    if (label.startsWith('discover')) return { videos: [{ url: 'https://v.example/open.mp4', slug: 'open-timing' }], pages: [], images: [{ url: 'https://i.example/hinge.png' }] }
    return standard()(label, prompt)
  }
  const { labels, calls, result } = await runWith(ARGS, behaviour)
  assert.match(calls.find(c => c.label === 'gaps:r1').prompt, /specialist, research, scrape, watch or discover/)
  assert.ok(labels.includes('discover:63-gap-motion-discover-r2'), labels.join(', '))
  const watch = calls.find(c => c.label === 'watch:19-watch-found-open-timing')
  assert.equal(watch.opts.phase, 'Gaps')
  assert.ok(labels.indexOf('watch:19-watch-found-open-timing') < labels.indexOf('specialist:64-gap-motion-r2'))
  const board = calls.find(c => c.label === 'moodboard:29-moodboard-r2')
  assert.ok(board, 'gap-round images get a moodboard pass')
  assert.equal(board.opts.phase, 'Gaps')
  assert.match(board.prompt, /https:\/\/i\.example\/hinge\.png/)
  assert.match(board.prompt, /only for these new images/)
  assert.ok(labels.indexOf('moodboard:29-moodboard-r2') < labels.indexOf('normalize:r2'))
  assert.ok(result.discovery.found.includes('19-watch-found-open-timing'))
})

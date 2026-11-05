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

test('a gap round adding under 10% entries is synthesized and verified once more, with no audit or further round', async () => {
  const { result, labels, calls } = await runWith(ARGS, standard({ gapEntries: 1, guessesByRound: { 1: 1, 2: 2 } }))
  assert.equal(result.stop_reason, 'gap round added under 10% new entries')
  assert.ok(labels.includes('synthesis:r2'))
  assert.equal(calls.filter(c => c.label.startsWith('verify') && /Round 2/.test(c.prompt)).length, 3)
  assert.ok(labels.indexOf('synthesis:r2') < labels.lastIndexOf('verify:check-an-output'))
  assert.ok(!labels.includes('audit:r2'))
  assert.ok(!labels.includes('gaps:r2'))
  assert.equal(result.remaining_gaps.length, 6) // round 2's verify: 2 guesses x 3 jobs, handed to the main loop
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

test('every depth digests what it ingested before synthesis; lite still skips the audit', async () => {
  const { labels } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: {} }))
  assert.ok(labels.includes('normalize:r1'), labels.join(', '))
  assert.ok(labels.indexOf('exclusion:75-exclusion') < labels.indexOf('normalize:r1'))
  assert.ok(labels.indexOf('normalize:r1') < labels.indexOf('synthesis:r1'))
  assert.ok(!labels.some(l => l.startsWith('audit')), labels.join(', '))
})

test('every worker prompt states the depth and its entry budget', async () => {
  const { calls } = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: {} }))
  const spec = calls.find(c => c.label === 'specialist:30-composition')
  assert.match(spec.prompt, /Depth: lite/)
  assert.match(spec.prompt, /Entry budget: 4-8 entries/)
  assert.match(spec.prompt, /facets/)
  const research = calls.find(c => c.label === 'research:20-research-lineage')
  assert.match(research.prompt, /Entry budget: 4-8 entries/)
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
    lite: { scrape: '3-6', watch: '3-8', moodboard: '3-6' },
    standard: { scrape: '4-8', watch: '4-10', moodboard: '4-8' },
    deep: { scrape: '6-12', watch: '6-14', moodboard: '6-12' },
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
    pages: Array.from({ length: 12 }, (_, i) => ({ url: `https://p.example/${i}`, slug: `p${i}` })),
    images: Array.from({ length: 40 }, (_, i) => ({ url: `https://i.example/${i}.png` })),
  }
  const want = { lite: [1, 3, 8], standard: [3, 6, 16], deep: [5, 10, 32] }
  for (const [depth, [videos, pages, images]] of Object.entries(want)) {
    const { labels, calls, result } = await runWith({ ...ARGS, depth, tickets: DISCOVERY }, withDiscover(many))
    assert.equal(labels.filter(l => l.startsWith('watch:')).length, videos, `${depth} videos`)
    assert.equal(labels.filter(l => l.startsWith('scrape:')).length, pages, `${depth} pages`)
    assert.equal(result.discovery.images.length, images, `${depth} images`)
    assert.match(calls.find(c => c.label === 'discover:07-discover').prompt,
      new RegExp(`at most ${videos} videos, ${pages} pages and ${images} images`), depth)
    const dropped = result.discovery.dropped
    assert.equal(dropped.length, (7 - videos) + (12 - pages) + (40 - images), `${depth} dropped`)
    assert.ok(dropped.some(d => d.kind === 'video' && d.url === 'https://v.example/6.mp4' && d.by === '07-discover'))
    assert.ok(dropped.some(d => d.kind === 'image' && d.url === 'https://i.example/39.png'))
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

  // Pages alone earn a moodboard too: their screenshots go on it.
  const pagesOnly = await runWith({ ...ARGS, tickets: noBoard }, withDiscover({ videos: [], pages: PICKS.pages, images: [] }))
  assert.ok(pagesOnly.labels.includes('moodboard:29-moodboard'), pagesOnly.labels.join(', '))
  assert.ok(pagesOnly.labels.indexOf('scrape:28-scrape-found-maker') < pagesOnly.labels.indexOf('moodboard:29-moodboard'))

  const none = await runWith({ ...ARGS, tickets: noBoard }, withDiscover({ videos: [], pages: [], images: [] }))
  assert.ok(!none.labels.some(l => l.startsWith('moodboard:')), 'nothing found, no moodboard added')
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

test('found pages are screenshotted and interpreted, not copied', async () => {
  const { calls } = await runWith({ ...ARGS, tickets: DISCOVERY }, withDiscover(PICKS))
  const scrape = calls.find(c => c.label === 'scrape:28-scrape-found-maker')
  assert.match(scrape.prompt, /webpages\.py fetch \S+ --work \S+ --screenshot/)
  assert.match(scrape.prompt, /Interpret, don't copy/)
  const watch = calls.find(c => c.label === 'watch:19-watch-found-demo')
  assert.doesNotMatch(watch.prompt, /--screenshot/)
})

test('verify narrowings (the dump ruling out what the request plausibly includes) become tier-1 gaps', async () => {
  const behaviour = (label, prompt) => {
    if (label.startsWith('verify')) {
      const round = Number((prompt.match(/Round (\d+)/) || [0, 1])[1])
      return { job: label, guesses: [], misses: [], lookups: 2, contradictions: [],
        narrowings: round === 1 ? [{ entry_id: 'an-parts-minimal', rules_out: 'a cart review and checkout', why: 'a shopping component plausibly includes them' }] : [] }
    }
    return standard({ guessesByRound: {} })(label, prompt)
  }
  // Lite normally stops after one round, but a narrowing earns it one widening round.
  const lite = await runWith({ ...ARGS, depth: 'lite' }, behaviour)
  const liteGaps = lite.calls.find(c => c.label === 'gaps:r1')
  assert.ok(liteGaps, lite.labels.join(', '))
  assert.match(liteGaps.prompt, /narrowing: an-parts-minimal rules out a cart review and checkout/)
  assert.ok(lite.labels.includes('synthesis:r2'))
  assert.deepEqual(lite.result.remaining_gaps, [])
  assert.equal(lite.result.verify[0].narrowings, 1)
  const std = await runWith(ARGS, behaviour)
  const gaps = std.calls.find(c => c.label === 'gaps:r1')
  assert.ok(gaps, 'a narrowing alone should trigger a gap round')
  assert.match(gaps.prompt, /an-parts-minimal/)
})

test('a found page URL is shell-quoted in the fetch command', async () => {
  const odd = { videos: [], pages: [{ url: "https://x.example/p?a=1&b=it's", slug: 'odd' }], images: [] }
  const { calls } = await runWith({ ...ARGS, tickets: DISCOVERY }, withDiscover(odd))
  const scrape = calls.find(c => c.label === 'scrape:28-scrape-found-odd')
  assert.ok(scrape.prompt.includes("webpages.py fetch 'https://x.example/p?a=1&b=it'\\''s' --work"), scrape.prompt)
  assert.doesNotMatch(scrape.prompt, /--render/)
})

test('a lite widening round that adds little is digested and verified once more', async () => {
  const behaviour = (label, prompt) => {
    if (label.startsWith('verify')) {
      const round = Number((prompt.match(/Round (\d+)/) || [0, 1])[1])
      return { job: label, guesses: [], misses: [], contradictions: [],
        narrowings: round === 1 ? [{ entry_id: 'an-parts-minimal', rules_out: 'a cart' }] : [] }
    }
    return standard({ guessesByRound: {}, gapEntries: 1 })(label, prompt)
  }
  const { labels, result, calls } = await runWith({ ...ARGS, depth: 'lite' }, behaviour)
  assert.equal(result.stop_reason, 'gap round added under 10% new entries')
  assert.ok(labels.includes('normalize:r2'), labels.join(', '))
  assert.ok(labels.indexOf('normalize:r2') < labels.indexOf('synthesis:r2'))
  assert.equal(calls.filter(c => c.label.startsWith('verify') && /Round 2/.test(c.prompt)).length, 2) // the widening is checked
  assert.deepEqual(result.remaining_gaps, [])
})

test('every agent in the swarm runs on haiku, with no effort override', async () => {
  const gapsAndDiscovery = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [{ id: '63-gap-motion-discover-r2', type: 'discover' }, { id: '64-gap-motion-r2', type: 'specialist' }] }
    if (label.startsWith('discover')) return { videos: [{ url: 'https://v.example/a.mp4', slug: 'a' }], pages: [{ url: 'https://p.example/x', slug: 'x' }], images: [{ url: 'https://i.example/y.png' }] }
    return standard()(label, prompt)
  }
  const runs = [await runWith(ARGS, gapsAndDiscovery), await runWith({ ...ARGS, tickets: [...DISCOVERY, ...TICKETS] }, gapsAndDiscovery)]
  const calls = runs.flatMap(r => r.calls)
  const kinds = new Set(calls.map(c => c.label.split(':')[0]))
  for (const k of ['discover', 'watch', 'scrape', 'moodboard', 'observe', 'research', 'specialist', 'lexicon', 'exclusion', 'normalize', 'synthesis', 'audit', 'verify', 'gaps']) {
    assert.ok(kinds.has(k), `scenario covers ${k}`)
  }
  for (const c of calls) {
    assert.equal(c.opts.model, 'haiku', `${c.label} model`)
    assert.equal(c.opts.effort, undefined, `${c.label} effort`)
  }
})

// ---------------------------------------------------------------- 0.7.1: constraint findings, token budgets, gap tickets
const verifyFinds = findings => (label, prompt) => {
  if (label.startsWith('verify')) {
    const round = Number((prompt.match(/Round (\d+)/) || [0, 1])[1])
    return { job: label, guesses: [], misses: [], lookups: 2, contradictions: [], ...(round === 1 ? findings : {}) }
  }
  return standard({ guessesByRound: {} })(label, prompt)
}
const CONSTRAINT_ONLY = { narrowings: [{ entry_id: 'ak-loop-at-rest', kind: 'constraint', rules_out: 'looping motion at rest', why: 'a scoped not_wanted with an instead' }] }

test('a verify result whose narrowings are all constraint findings does not start a widening round', async () => {
  // Test 10: every lite build ran a widening round, mostly for scoped anti-keywords that already had an instead.
  for (const depth of ['lite', 'standard']) {
    const { result, labels } = await runWith({ ...ARGS, depth }, verifyFinds(CONSTRAINT_ONLY))
    assert.equal(result.rounds, 1, depth)
    assert.ok(!labels.some(l => l.startsWith('gaps')), `${depth}: ${labels.join(', ')}`)
    assert.deepEqual(result.remaining_gaps, [], depth)
  }
  const { calls } = await runWith({ ...ARGS, depth: 'lite' }, verifyFinds(CONSTRAINT_ONLY))
  const narrowing = calls.find(c => c.label.startsWith('verify')).opts.schema.properties.narrowings.items
  assert.deepEqual([...narrowing.properties.kind.enum].sort(), ['constraint', 'copy', 'definition', 'job', 'quality', 'scope'])
  assert.ok(narrowing.required.includes('kind'))
})

test('constraint findings never reach the gap planner, and the other narrowings arrive with their kind', async () => {
  const mixed = { narrowings: [...CONSTRAINT_ONLY.narrowings,
    { entry_id: 'q-dreamlike', kind: 'definition', rules_out: 'a slow drift that never settles', why: 'one reading only' }] }
  const { calls } = await runWith(ARGS, verifyFinds(mixed))
  const gaps = calls.find(c => c.label === 'gaps:r1')
  assert.ok(gaps, 'a definition narrowing starts a gap round')
  assert.match(gaps.prompt, /"kind":"definition","decision":"narrowing: q-dreamlike rules out a slow drift that never settles/)
  assert.doesNotMatch(gaps.prompt, /ak-loop-at-rest/)
})

test('every worker prompt states a token budget next to its facet count', async () => {
  // Test 10: lite dumps ran 30K to 47K tokens against a target of 8 to 15K.
  const want = { lite: '1,200', standard: '2,000', deep: '3,000' }
  for (const [depth, tokens] of Object.entries(want)) {
    const { calls } = await runWith({ ...ARGS, depth }, standard({ guessesByRound: {} }))
    for (const label of ['research:20-research-lineage', 'specialist:30-composition']) {
      assert.match(calls.find(c => c.label === label).prompt, new RegExp(`Entry budget: \\d+-\\d+ entries in about ${tokens} tokens`), `${depth} ${label}`)
    }
  }
  const { calls } = await runWith({ ...ARGS, depth: 'lite', tickets: MEDIA }, standard({ guessesByRound: {} }))
  assert.match(calls.find(c => c.label === 'scrape:15-scrape-docs').prompt, /Entry budget: 3-6 entries in about 900 tokens/)
})

test('a gap ticket in a gap round is spawned with the gap section of briefs.md and a specialist budget', async () => {
  // Test 10: gap shards typed specialist could not `_replace`, so every widening round needed an extra normalize agent.
  const behaviour = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [{ id: '60-gap-feel-r2', type: 'gap' }, { id: '61-gap-scrape-r2', type: 'scrape' }] }
    return standard()(label, prompt)
  }
  const { labels, calls, result } = await runWith(ARGS, behaviour)
  const gap = calls.find(c => c.label === 'gap:60-gap-feel-r2')
  assert.ok(gap, labels.join(', '))
  assert.equal(gap.opts.phase, 'Gaps')
  assert.match(gap.prompt, /"gap" section of \/skill\/references\/briefs\.md/)
  assert.match(gap.prompt, /shards\/60-gap-feel-r2\.json/)
  assert.match(gap.prompt, /Entry budget: 6-12 entries in about 2,000 tokens/)
  assert.ok(labels.indexOf('scrape:61-gap-scrape-r2') < labels.indexOf('gap:60-gap-feel-r2'), 'outside facts first')
  assert.ok(labels.indexOf('gap:60-gap-feel-r2') < labels.indexOf('normalize:r2'))
  assert.ok(result.gap_tickets.includes('60-gap-feel-r2'))
  assert.match(calls.find(c => c.label === 'gaps:r1').prompt, /type gap, specialist, research, scrape, watch or discover/)
})

test('verify can label a guess a research gap, and the label reaches the gap planner', async () => {
  // Test 10: the playlist dump's research reached only band-level sources, so its pool held no songs to pick from.
  const shortfall = { guesses: [{ decision: 'the pool holds 2 verified candidates; the task asks for 5', tier: 1, section: 'pool', kind: 'research' }] }
  const { calls } = await runWith(ARGS, verifyFinds(shortfall))
  const guess = calls.find(c => c.label.startsWith('verify')).opts.schema.properties.guesses.items
  assert.equal(guess.properties.kind.type, 'string')
  assert.match(calls.find(c => c.label === 'gaps:r1').prompt, /"kind":"research"/)
})

test('leftover contradictions go back to the main loop as anti-keywords, never as open-question defaults', async () => {
  // Test 10: verify found looping motion at rest pulling against the prompt's "hover state animations"; the main loop
  // filed it as an open_questions default, and no builder acted on it.
  const rest = { contradictions: [{ value_id: 'ex-halo-loop', against_id: 'us-hover-states', why: 'looping motion at rest' }] }
  const { result } = await runWith({ ...ARGS, depth: 'lite' }, verifyFinds(rest))
  assert.equal(result.remaining_gaps.length, 2) // lite: no round left for it
  assert.match(result.next, /user_stated entry as a scoped not_wanted anti-keyword with an instead/)
  assert.match(result.next, /never an open question/)
  const guessesOnly = await runWith({ ...ARGS, depth: 'lite' }, standard({ guessesByRound: { 1: 2 } }))
  assert.doesNotMatch(guessesOnly.result.next, /not_wanted/)
})

test('the gap planner notes the constraint findings it dropped, and its notes come back with the results', async () => {
  const note = 'dropped ak-glow-at-rest: a scoped not_wanted with an instead, a constraint and not a narrowing'
  const behaviour = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [], notes: note }
    return standard()(label, prompt)
  }
  const { result, calls } = await runWith(ARGS, behaviour)
  assert.deepEqual(result.gap_notes, [{ round: 1, notes: note }])
  const gaps = calls.find(c => c.label === 'gaps:r1')
  assert.equal(gaps.opts.schema.properties.notes.type, 'string')
  assert.match(gaps.prompt, /"notes"/)
})

test('a gap ticket the planner names without its round is spawned with one, and its brief names that shard file', async () => {
  // finalize merges shards in round order, so a gap shard without its -rN would sort into round 1, under the digest.
  const behaviour = (label, prompt) => {
    if (label.startsWith('gaps')) return { tickets: [{ id: '60-gap-look', type: 'gap' }] }
    return standard()(label, prompt)
  }
  const { labels, calls, result } = await runWith(ARGS, behaviour)
  const gap = calls.find(c => c.label === 'gap:60-gap-look-r2')
  assert.ok(gap, labels.join(', '))
  assert.match(gap.prompt, /Write exactly one file: \/proj\/metadumps\/\.work\/demo\/shards\/60-gap-look-r2\.json/)
  assert.match(gap.prompt, /Ticket file: \/proj\/metadumps\/\.work\/demo\/tickets\/60-gap-look\.md/) // the file the planner wrote
  assert.deepEqual(result.gap_tickets, ['60-gap-look-r2'])
})

test('at lite, a research gap (a pool short of verified candidates) earns the one widening round', async () => {
  // Test 10's playlist was lite: its pool held no verified songs, and no round went back to the catalogs.
  const shortfall = { guesses: [{ decision: 'the pool holds 3 verified candidates; the task asks for 5', tier: 2, section: 'pool', kind: 'research' }] }
  const { labels, calls } = await runWith({ ...ARGS, depth: 'lite' }, verifyFinds(shortfall))
  const gaps = calls.find(c => c.label === 'gaps:r1')
  assert.ok(gaps, labels.join(', '))
  assert.match(gaps.prompt, /"decision":"the pool holds 3 verified candidates; the task asks for 5","tier":2,"section":"pool","kind":"research"/)
  assert.ok(labels.includes('synthesis:r2'))
})

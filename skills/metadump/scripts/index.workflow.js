export const meta = {
  name: 'metadump-index',
  description: 'Fan out a meta dump build: evidence (references, research, pages, videos, images), specialists, normalize, synthesis + build, audit and dry-run verify, then gap rounds',
  whenToUse: 'Called by the metadump skill in create mode, after charting, with args {skill_dir, work_dir, slug, depth, max_rounds, tickets[]} (ticket types: observe, research, discover, scrape, watch, moodboard, inherit, specialist, lexicon, exclusion)',
  phases: [
    { title: 'Evidence', detail: 'observe references, research, discover videos, images and pages on the web, scrape pages, watch videos, collect images into a moodboard, inherit earlier dumps' },
    { title: 'Specialists', detail: 'one per section, plus lexicon and exclusion' },
    { title: 'Normalize', detail: 'digest: assimilate everything ingested into one body (merge across sources, resolve conflicts, cap tier 1)' },
    { title: 'Synthesis', detail: 'essence, routing, exports, review prompts; finalize build' },
    { title: 'Verify', detail: 'audit plus one dry-run consumer per routed job, with a contradiction pass' },
    { title: 'Gaps', detail: 'gap tickets for tier-1/2 guesses, then another round' },
  ],
}

// ---------------------------------------------------------------- args
const A = args || {}
if (!A.skill_dir || !A.work_dir || !Array.isArray(A.tickets)) {
  throw new Error('metadump-index needs args {skill_dir, work_dir, slug, depth, max_rounds, tickets: [{id, type, wave?}]}')
}
const SKILL = A.skill_dir
const WORK = A.work_dir
const DEPTH = A.depth || 'standard'
const MAX_ROUNDS = A.max_rounds || (DEPTH === 'lite' ? 1 : DEPTH === 'deep' ? 3 : 2)
const MAX_VERIFY = DEPTH === 'lite' ? 2 : DEPTH === 'deep' ? 8 : 6
const LITE = DEPTH === 'lite' // lite skips the audit (verify still traces); every depth digests (normalize)
const BRIEFS = `${SKILL}/references/briefs.md`
// Entries per shard by depth, and about how many tokens those entries take in all. Entries are facets (one object per
// area: a line of text plus lists of short phrases, behaviors and a principle), the shape of the hand-made dumps this
// skill grew out of (ADR 0009), so the counts are small. Without a budget, workers write everything they can think of;
// with a facet count alone, test 10's lite dumps still ran 30-47K tokens against 8-15K. Mirrors create.md.
const B = (facets, tokens) => ({ facets, tokens })
const BUDGETS = {
  lite: { research: B('4-8', 1200), specialist: B('4-8', 1200), gap: B('4-8', 1200), lexicon: B('4-8', 1200), exclusion: B('6-10', 1500),
    observe: B('4-8', 1200), inherit: B('as needed'), scrape: B('3-6', 900), watch: B('3-8', 1200), moodboard: B('3-6', 900) },
  standard: { research: B('6-10', 2000), specialist: B('6-12', 2000), gap: B('6-12', 2000), lexicon: B('6-10', 2000), exclusion: B('8-14', 2800),
    observe: B('6-12', 2000), inherit: B('as needed'), scrape: B('4-8', 1600), watch: B('4-10', 2000), moodboard: B('4-8', 1600) },
  deep: { research: B('8-14', 3000), specialist: B('10-16', 3000), gap: B('10-16', 3000), lexicon: B('8-14', 3000), exclusion: B('10-18', 3900),
    observe: B('8-16', 3000), inherit: B('as needed'), scrape: B('6-12', 2600), watch: B('6-14', 3000), moodboard: B('6-12', 2600) },
}
const budgetFor = type => (BUDGETS[DEPTH] || BUDGETS.standard)[type]
const thousands = n => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
const budgetLine = b => `   Entry budget: ${b.facets} entries${b.tokens ? ` in about ${thousands(b.tokens)} tokens` : ''}, written as facets (one object per area: a line of text, lists of short phrases, behaviors and a principle; see the opener in briefs.md)`
const SCHEMA = `${SKILL}/references/schema.md`
const FINALIZE = `python3 ${SKILL}/scripts/finalize.py`

const WAVE_OF = { inherit: 1, observe: 1, research: 1, scrape: 1, watch: 1, moodboard: 1, discover: 1, specialist: 2, lexicon: 2, exclusion: 2 }
// Moodboard tickets collect the images that scrape and watch tickets write, so they start once the rest of the evidence is in.
const COLLECTS_EVIDENCE = new Set(['moodboard'])
// Discover tickets search the web for videos and pages worth reading and write watch and scrape tickets for them (no shard).
const FINDS_EVIDENCE = new Set(['discover'])
// What one discover ticket may hand on, by depth: videos (watch jobs), pages (scrape jobs), images (moodboard). Mirrors create.md.
const DISCOVERY_CAPS = { lite: { videos: 1, pages: 3, images: 8 }, standard: { videos: 3, pages: 6, images: 16 }, deep: { videos: 5, pages: 10, images: 32 } }
const DISCOVERY_CAP = DISCOVERY_CAPS[DEPTH] || DISCOVERY_CAPS.standard
// Gap rounds may add evidence (facts from outside, or a discover ticket to find a video or page) as well as the build's
// own work: `gap` tickets widen or rewrite entries (they may `_replace` and `_delete`), `specialist` ones only add.
const GAP_EVIDENCE = new Set(['research', 'scrape', 'watch', 'discover'])
const GAP_WORK = new Set(['gap', 'specialist'])
const ENGINE = new Set(['prompt', 'normalize', 'synthesis', 'audit', 'verify', 'gaps'])
const work = A.tickets.filter(t => t && t.id && t.type && !ENGINE.has(t.type))
const wave1 = work.filter(t => (t.wave || WAVE_OF[t.type] || 2) === 1)
const wave2 = work.filter(t => (t.wave || WAVE_OF[t.type] || 2) !== 1)

// Every agent in the swarm runs on Haiku, at its default effort: the fan-out is many small, well-briefed jobs.
const SWARM_MODEL = 'haiku'
const swarm = (prompt, opts = {}) => agent(prompt, { ...opts, model: SWARM_MODEL })

// ---------------------------------------------------------------- schemas
const RECEIPT = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    path: { type: 'string' },
    n_entries: { type: 'number' },
    sections: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['id', 'path', 'n_entries'],
}
const SYNTH = {
  type: 'object',
  properties: {
    built: { type: 'boolean' },
    dump_path: { type: 'string' },
    jobs: { type: 'array', items: { type: 'string' } },
    errors: { type: 'array', items: { type: 'string' } },
  },
  required: ['built', 'jobs'],
}
// What verify's passes report, by kind. `constraint` is a finding about a constraint mechanism (a scoped anti-keyword with
// an instead, an invariant with its variable, a forbidden shortcut), which may exclude (ADR 0005): verify uses it when
// unsure, and it never starts a widening round (ADR 0011). `directive` is the head or an export reading as orders, or
// funnelling every consumer to the same pick (ADR 0012).
const NARROWING_KINDS = ['scope', 'quality', 'job', 'definition', 'copy', 'directive', 'tamed', 'constraint']   // tamed: ADR 0016
const VERIFY = {
  type: 'object',
  properties: {
    job: { type: 'string' },
    guesses: {
      type: 'array',
      items: {
        type: 'object',
        // kind "research": the gap is a fact from outside (a candidate pool with fewer verified candidates than the task asks for)
        properties: { decision: { type: 'string' }, tier: { type: 'number' }, section: { type: 'string' }, query: { type: 'string' }, kind: { type: 'string' } },
        required: ['decision', 'tier'],
      },
    },
    contradictions: {
      type: 'array',
      items: {
        type: 'object',
        properties: { value_id: { type: 'string' }, against_id: { type: 'string' }, why: { type: 'string' } },
        required: ['value_id', 'against_id'],
      },
    },
    narrowings: {
      type: 'array',
      items: {
        type: 'object',
        properties: { entry_id: { type: 'string' }, kind: { type: 'string', enum: NARROWING_KINDS }, rules_out: { type: 'string' }, why: { type: 'string' } },
        required: ['entry_id', 'kind', 'rules_out'],
      },
    },
    misses: { type: 'array', items: { type: 'string' } },
    lookups: { type: 'number' },
  },
  required: ['job', 'guesses'],
}
const AUDIT = {
  type: 'object',
  properties: {
    missing_clauses: { type: 'array', items: { type: 'string' } },
    demoted: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['missing_clauses'],
}
const PICK = (props, required) => ({ type: 'array', items: { type: 'object', properties: props, required } })
const DISCOVERED = {
  type: 'object',
  properties: {
    videos: PICK({ url: { type: 'string' }, slug: { type: 'string' }, answers: { type: 'string' }, take: { type: 'string' } }, ['url', 'slug']),
    pages: PICK({ url: { type: 'string' }, slug: { type: 'string' }, answers: { type: 'string' } }, ['url', 'slug']),
    images: PICK({ url: { type: 'string' }, page: { type: 'string' }, title: { type: 'string' }, license: { type: 'string' }, answers: { type: 'string' } }, ['url']),
    notes: { type: 'string' },
  },
  required: ['videos', 'pages', 'images'],
}
const GAPS = {
  type: 'object',
  properties: {
    tickets: {
      type: 'array',
      items: { type: 'object', properties: { id: { type: 'string' }, type: { type: 'string' } }, required: ['id', 'type'] },
    },
    notes: { type: 'string' },
  },
  required: ['tickets'],
}

// ---------------------------------------------------------------- prompts
const opener = (id, type, extra, file) => `You are resolving one ticket of a meta dump build.
Work dir:  ${WORK}
Skill dir: ${SKILL}
Ticket id: ${id}   Type: ${type}   Depth: ${DEPTH}${budgetFor(type) ? budgetLine(budgetFor(type)) : ''}
Ticket file: ${WORK}/tickets/${file || id}.md (read it first if it exists)
Context: ${WORK}/map.md (destination jobs, query log, senses, layers, section plan) and ${WORK}/manifest.json (verbatim prompt)
Instructions: follow the "Opener" section and the "${type}" section of ${BRIEFS} exactly. The format is ${SCHEMA}.
${extra || `Write exactly one file: ${WORK}/shards/${id}.json`}
Return only the receipt or result the brief asks for, never the entries themselves.`

// URLs come from web content: single-quote them for the shell, so & ; $ and quotes stay data.
const shellQuote = s => `'${String(s).replace(/'/g, "'\\''")}'`

const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'job'

const ticketCall = (t, phaseName) => () => swarm(opener(t.id, t.type, undefined, t.file), { label: `${t.type}:${t.id}`, phase: phaseName, schema: RECEIPT })
const runTickets = (list, phaseName) => parallel(list.map(t => ticketCall(t, phaseName)))

// ---------------------------------------------------------------- discovery
// A found job (a watch or scrape made from a discover pick) has no ticket file: its prompt is the whole ticket.
const foundCall = (t, phaseName) => () => swarm(opener(t.id, t.type, `This ticket was made by discovery (${t.by}); there is no ticket file.
URL: ${t.pick.url}
Answers: ${t.pick.answers || 'see the query log in map.md'}${t.pick.take ? `\nTake: ${t.pick.take}` : ''}
origin: web. It was found online, so its facts, frames and images are researched and every source it adds says origin: "web"; never pass --reference.${t.type === 'scrape' ? `
Fetch it with a screenshot: python3 ${SKILL}/scripts/webpages.py fetch ${shellQuote(t.pick.url)} --work ${WORK} --screenshot, then open the screenshot with the Read tool and look at it.
Interpret, don't copy: say what the page shows and what transfers to this task, in the task's own terms; quote only the facts you rely on.` : ''}
Write exactly one file: ${WORK}/shards/${t.id}.json`), { label: `${t.type}:${t.id}`, phase: phaseName, schema: RECEIPT })

// A moodboard told about the images discovery found (already within the caps), so it collects them as web-found.
const boardCall = (t, images, phaseName, scope) => () => swarm(opener(t.id, 'moodboard', `${scope || ''}Discovery found these images online (origin web, already within the caps). Save this JSON as ${WORK}/images/found-${t.id}.json, then run python3 ${SKILL}/scripts/images.py collect --work ${WORK} --found ${WORK}/images/found-${t.id}.json alongside your other collect commands:
${JSON.stringify(images)}
Write exactly one file: ${WORK}/shards/${t.id}.json`), { label: `moodboard:${t.id}`, phase: phaseName, schema: RECEIPT })

const discovery = { found: [], dropped: [], images: [] }
// Every ticket id in this build, so a found ticket never takes a planned ticket's shard.
const takenIds = new Set(A.tickets.filter(t => t && t.id).map(t => t.id))
const freshId = base => {
  let id = base
  for (let n = 2; takenIds.has(id); n += 1) id = `${base}-${n}`
  takenIds.add(id)
  return id
}
// One discover ticket per wave, so the caps are a real bound on what a wave fetches.
const oneFinder = list => {
  list.slice(1).forEach(t => discovery.dropped.push({ kind: 'discover', url: null, by: t.id }))
  if (list.length > 1) log(`one discover ticket per wave: not running ${list.slice(1).map(t => t.id).join(', ')}`)
  return list.slice(0, 1)
}
// The first picks of each kind up to the depth's cap, best first; the rest are reported, never silently cut.
const KIND_OF = { videos: 'video', pages: 'page', images: 'image' }
const keepWithinCaps = (out, by) => {
  const kept = {}
  const dropped = []
  for (const list of Object.keys(KIND_OF)) {
    const all = ((out && out[list]) || []).filter(x => x && x.url)
    kept[list] = all.slice(0, DISCOVERY_CAP[list])
    dropped.push(...all.slice(DISCOVERY_CAP[list]).map(x => ({ kind: KIND_OF[list], url: x.url, by })))
  }
  return { kept, dropped }
}
const foundJob = (type, prefix, by) => pick => ({ id: freshId(`${prefix}-${type}-found-${slug(pick.slug || pick.url)}`), type, pick, by })

// A discover ticket, then the found jobs made from its picks, as one chain: they start as soon as it
// returns, without waiting for the rest of the evidence.
const discoverThenRun = (t, phaseName) => async () => {
  const out = await swarm(opener(t.id, 'discover',
    `Write no shard and no ticket files. Record every candidate you considered in ${WORK}/discovered/${t.id}.json, then return your picks. Caps at depth ${DEPTH}: at most ${DISCOVERY_CAP.videos} videos, ${DISCOVERY_CAP.pages} pages and ${DISCOVERY_CAP.images} images.`, t.file),
    { label: `discover:${t.id}`, phase: phaseName, schema: DISCOVERED })
  const { kept, dropped } = keepWithinCaps(out, t.id)
  const jobs = [...kept.videos.map(foundJob('watch', '19', t.id)), ...kept.pages.map(foundJob('scrape', '28', t.id))]
  if (dropped.length) log(`discovery cap (depth ${DEPTH}) on ${t.id}: dropped ${dropped.length} (${dropped.map(d => d.url).join(', ')})`)
  discovery.dropped.push(...dropped)
  discovery.found.push(...jobs.map(j => j.id))
  discovery.images.push(...kept.images.map(x => ({ ...x, by: t.id })))
  return jobs.length ? parallel(jobs.map(j => foundCall(j, phaseName))) : []
}

// Evidence tickets plus at most one discover ticket (and the tickets it makes), all started together.
const runEvidence = async (list, phaseName) => {
  const finders = oneFinder(list.filter(t => FINDS_EVIDENCE.has(t.type)))
  const rest = list.filter(t => !FINDS_EVIDENCE.has(t.type))
  return (await parallel([...rest.map(t => ticketCall(t, phaseName)), ...finders.map(t => discoverThenRun(t, phaseName))])).flat()
}

const count = receipts => receipts.filter(Boolean).reduce((n, r) => n + (r.n_entries || 0), 0)

// ---------------------------------------------------------------- round 1 evidence + specialists
let total = 0
if (wave1.length) {
  phase('Evidence')
  const first = wave1.filter(t => !COLLECTS_EVIDENCE.has(t.type))
  const after = wave1.filter(t => COLLECTS_EVIDENCE.has(t.type))
  const r1 = await runEvidence(first, 'Evidence')
  if ((discovery.images.length || discovery.found.length) && !after.length) {
    after.push({ id: '29-moodboard', type: 'moodboard' })
    log(`discovery found ${discovery.found.length} pages/videos and ${discovery.images.length} images; the chart planned no moodboard, so 29-moodboard collects their screenshots, frames and images`)
  }
  const boards = after.map(t => (discovery.images.length ? boardCall(t, discovery.images, 'Evidence') : ticketCall(t, 'Evidence')))
  const r = [...r1, ...(boards.length ? await parallel(boards) : [])]
  total += count(r)
  log(`evidence: ${r.filter(Boolean).length}/${first.filter(t => !FINDS_EVIDENCE.has(t.type)).length + discovery.found.length + after.length} tickets (${discovery.found.length} found by discovery), ${count(r)} entries`)
}
if (wave2.length) {
  phase('Specialists')
  const r = await runTickets(wave2, 'Specialists')
  total += count(r)
  log(`specialists: ${r.filter(Boolean).length}/${wave2.length} tickets, ${count(r)} entries`)
}

const tier1Gaps = (verified, key, describe, kind) => verified.flatMap(v => (v[key] || []).map(x => ({
  job: v.job, ...((x.kind || kind) ? { kind: x.kind || kind } : {}), decision: `${describe(x)}${x.why ? ` (${x.why})` : ''}`, tier: 1,
})))
let maxRounds = MAX_ROUNDS

// Dry-run each routed job against a build (plus the audit when asked); what they find becomes remaining_gaps.
const verifyBuild = async (round, synth, withAudit) => {
  phase('Verify')
  const dump = synth.dump_path
  const jobs = (synth.jobs || []).slice(0, MAX_VERIFY)
  if ((synth.jobs || []).length > MAX_VERIFY) log(`verifying ${MAX_VERIFY} of ${synth.jobs.length} routed jobs (depth ${DEPTH} cap); the rest were not dry-run`)
  const auditId = `96-audit-r${round}`
  const auditCall = withAudit ? [() => swarm(opener(auditId, 'audit', `Round ${round}. The built dump is ${dump}. Write exactly one file: ${WORK}/shards/${auditId}.json`),
    { label: `audit:r${round}`, phase: 'Verify', schema: AUDIT })] : []
  const outcomes = await parallel([
    ...auditCall,
    ...jobs.map(job => () => swarm(opener(`verify-${slug(job)}`, 'verify',
      `Round ${round}. The built dump is ${dump}. Your job: "${job}". Write no shard; write ${WORK}/verify/r${round}-${slug(job)}.json`),
      { label: `verify:${slug(job)}`, phase: 'Verify', schema: VERIFY })),
  ])
  const audit = withAudit ? outcomes[0] : null
  const verified = outcomes.slice(auditCall.length).filter(Boolean)
    .map(v => ({ ...v, narrowings: (v.narrowings || []).filter(n => n.kind !== 'constraint') }))
  results.audits.push(audit)
  results.verify.push(...verified.map(v => ({ round, job: v.job, guesses: v.guesses.length, tier12: v.guesses.filter(g => g.tier <= 2).length, contradictions: (v.contradictions || []).length, narrowings: (v.narrowings || []).length, misses: (v.misses || []).length })))
  // Structural defects are tier-1 gaps: a concrete value pulling against a tier-1 objective entry (ADR 0003), and an
  // entry ruling out what the request plausibly includes (ADR 0005).
  const contradictions = tier1Gaps(verified, 'contradictions', c => `contradiction: ${c.value_id} pulls against ${c.against_id}`, 'contradiction')
  const narrowings = tier1Gaps(verified, 'narrowings', n => `narrowing: ${n.entry_id} rules out ${n.rules_out}`)
  const tier12 = [...contradictions, ...narrowings, ...verified.flatMap(v => v.guesses.filter(g => g.tier <= 2).map(g => ({ job: v.job, ...g })))]
  const missing = (audit && audit.missing_clauses) || []
  log(`round ${round}: ${tier12.length} tier-1/2 gaps (${contradictions.length} contradictions, ${narrowings.length} narrowings) across ${verified.length} jobs, ${missing.length} untraced prompt clauses`)
  results.remaining_gaps = [...tier12, ...missing.map(clause => ({ decision: `untraced prompt clause: ${clause}`, tier: 1 }))]
  // A candidate pool short of verified candidates is a fact to go and get, so at lite it earns the widening round too.
  const research = tier12.filter(g => g.kind === 'research')
  return { tier12, missing, narrowings, research }
}
const results = { rounds: 0, builds: [], verify: [], audits: [], gap_tickets: [], gap_notes: [], entries_from_receipts: total, discovery }
let round = 1
while (true) {
  results.rounds = round

  // Digest: everything ingested is broken down and assimilated into one body before synthesis (ADR 0007).
  phase('Normalize')
  const normId = round === 1 ? '90-normalize' : `9${round - 1}-normalize-r${round}`
  await swarm(opener(normId, 'normalize', `Round ${round}. Digest everything ingested so far. Write exactly one file: ${WORK}/shards/${normId}.json`),
    { label: `normalize:r${round}`, phase: 'Normalize', schema: RECEIPT })

  phase('Synthesis')
  const synth = await swarm(opener('95-synthesis', 'synthesis',
    `Round ${round}. Write (or rewrite) ${WORK}/shards/95-synthesis.json; any repair shard is ${WORK}/shards/97-repair-r${round}.json. Build with: ${FINALIZE} build ${WORK}`),
    { label: `synthesis:r${round}`, phase: 'Synthesis', schema: SYNTH })
  results.builds.push(synth)
  if (!synth || !synth.built) {
    log(`synthesis round ${round} did not produce a passing build; stopping so the main loop can repair it`)
    break
  }
  const { tier12, missing, narrowings, research } = await verifyBuild(round, synth, !LITE)
  if (LITE && round === 1 && (narrowings.length || research.length) && maxRounds < 2) {
    maxRounds = 2
    log(`lite: ${narrowings.length} narrowings and ${research.length} research gaps found, so one widening round runs`)
  }
  if (round >= maxRounds || (!tier12.length && !missing.length)) break

  phase('Gaps')
  const plan = await swarm(`${opener(`gaps-r${round}`, 'gaps', `Round ${round}. Write ticket files only (no shard), named ${WORK}/tickets/6<N>-gap-<section>-r${round + 1}.md with N 0-9 unused so far.`)}

Verify guesses at tier 1-2, contradictions and narrowings (JSON): ${JSON.stringify(tier12)}
Untraced prompt clauses (JSON): ${JSON.stringify(missing)}
Return {"tickets": [{"id", "type"}], "notes": "..."} for the tickets you wrote (type gap, specialist, research, scrape, watch or discover), or {"tickets": [], "notes": "..."}; notes name each finding you dropped and why.`,
    { label: `gaps:r${round}`, phase: 'Gaps', schema: GAPS })
  if (plan && plan.notes) results.gap_notes.push({ round, notes: plan.notes })
  // A gap ticket always carries the round it feeds (6N-gap-<section>-rN): finalize merges shards in round order, so
  // its edits land on the earlier rounds' digest. Its ticket file keeps the id the planner wrote it under.
  const withRound = t => (/-r\d+$/.test(t.id) ? t : { ...t, id: `${t.id}-r${round + 1}`, file: t.id })
  const gapTickets = ((plan && plan.tickets) || []).filter(t => t.id && (GAP_WORK.has(t.type) || GAP_EVIDENCE.has(t.type))).map(withRound)
  results.gap_tickets.push(...gapTickets.map(t => t.id))
  if (!gapTickets.length) break

  const evidence = gapTickets.filter(t => GAP_EVIDENCE.has(t.type))
  const special = gapTickets.filter(t => !GAP_EVIDENCE.has(t.type))
  let added = 0
  if (evidence.length) {
    const before = discovery.images.length
    added += count(await runEvidence(evidence, 'Gaps'))
    const fresh = discovery.images.slice(before)
    if (fresh.length) {
      added += count(await parallel([boardCall({ id: `29-moodboard-r${round + 1}` }, fresh, 'Gaps',
        'Gap round: write entries only for these new images (the earlier moodboard shard covers the rest), then rerun images.py moodboard so the page shows every image.\n')]))
    }
  }
  if (special.length) added += count(await runTickets(special, 'Gaps'))
  log(`gap round added ${added} entries (${total ? Math.round((100 * added) / total) : 0}% of ${total})`)
  total += added
  round += 1
  if (total && added < 0.1 * (total - added)) {
    // Still normalize + synthesize so the new entries are routed, then stop.
    results.stop_reason = 'gap round added under 10% new entries'
  }
  if (results.stop_reason) {
    const nId = `9${round - 1}-normalize-r${round}`
    await swarm(opener(nId, 'normalize', `Round ${round}. Digest what the gap round added into the existing body. Write exactly one file: ${WORK}/shards/${nId}.json`),
      { label: `normalize:r${round}`, phase: 'Normalize', schema: RECEIPT })
    const s2 = await swarm(opener('95-synthesis', 'synthesis',
      `Round ${round}. Rewrite ${WORK}/shards/95-synthesis.json; any repair shard is ${WORK}/shards/97-repair-r${round}.json. Build with: ${FINALIZE} build ${WORK}`),
      { label: `synthesis:r${round}`, phase: 'Synthesis', schema: SYNTH })
    results.builds.push(s2)
    results.rounds = round
    // Check the widened dump once more (no audit, no further round): what it still finds goes to the main loop.
    if (s2 && s2.built) await verifyBuild(round, s2, false)
    break
  }
}

results.entries_from_receipts = total
results.remaining_gaps = results.remaining_gaps || []
// A contradiction against the user's words becomes a constraint, never an open-question default (ADR 0011).
const contradicted = results.remaining_gaps.some(g => g.kind === 'contradiction')
results.next = (results.remaining_gaps.length
  ? `Main loop: write the ${results.remaining_gaps.length} remaining_gaps as open_questions (each with a default, impact and how to resolve) in ${WORK}/shards/98-open-questions.json${contradicted ? ', but write each contradiction against a tier-1 user_stated entry as a scoped not_wanted anti-keyword with an instead (inferred, in the same shard), never an open question' : ''}, then run `
  : 'Main loop: run ') + `${FINALIZE} build ${WORK} (audit demotions apply on rebuild), read ${WORK}/report.json, then present.`
return results

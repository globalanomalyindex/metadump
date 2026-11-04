export const meta = {
  name: 'metadump-index',
  description: 'Fan out a meta dump build: evidence (references, research, pages, videos, images), specialists, normalize, synthesis + build, audit and dry-run verify, then gap rounds',
  whenToUse: 'Called by the metadump skill in create mode, after charting, with args {skill_dir, work_dir, slug, depth, max_rounds, tickets[]} (ticket types: observe, research, discover, scrape, watch, moodboard, inherit, specialist, lexicon, exclusion)',
  phases: [
    { title: 'Evidence', detail: 'observe references, research, discover videos, images and pages on the web, scrape pages, watch videos, collect images into a moodboard, inherit earlier dumps' },
    { title: 'Specialists', detail: 'one per section, plus lexicon and exclusion' },
    { title: 'Normalize', detail: 'merge synonyms, resolve conflicts, cap tier 1' },
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
const LITE = DEPTH === 'lite' // lite skips normalize and audit (synthesis dedupes; verify still traces)
const BRIEFS = `${SKILL}/references/briefs.md`
// Entries per shard by depth. Without a budget, workers write everything they can think of
// (the first lite smoke test produced 212 entries, ~3x the plan). Mirrors create.md.
const BUDGETS = {
  lite: { research: '8-12', specialist: '12-20', lexicon: '10-15', exclusion: '10-15', observe: '10-20', inherit: 'as needed',
    scrape: '8-15', watch: '8-15', moodboard: '10-20' },
  standard: { research: '10-20', specialist: '20-35', lexicon: '15-30', exclusion: '15-25', observe: '20-35', inherit: 'as needed',
    scrape: '15-25', watch: '15-30', moodboard: '16-30' },
  deep: { research: '15-30', specialist: '30-50', lexicon: '25-45', exclusion: '20-35', observe: '30-50', inherit: 'as needed',
    scrape: '25-40', watch: '25-45', moodboard: '24-45' },
}
const budgetFor = type => (BUDGETS[DEPTH] || BUDGETS.standard)[type]
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
// Gap rounds may add evidence (facts from outside, or a discover ticket to find a video or page) as well as specialist work.
const GAP_EVIDENCE = new Set(['research', 'scrape', 'watch', 'discover'])
const ENGINE = new Set(['prompt', 'normalize', 'synthesis', 'audit', 'verify', 'gaps'])
const work = A.tickets.filter(t => t && t.id && t.type && !ENGINE.has(t.type))
const wave1 = work.filter(t => (t.wave || WAVE_OF[t.type] || 2) === 1)
const wave2 = work.filter(t => (t.wave || WAVE_OF[t.type] || 2) !== 1)

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
const VERIFY = {
  type: 'object',
  properties: {
    job: { type: 'string' },
    guesses: {
      type: 'array',
      items: {
        type: 'object',
        properties: { decision: { type: 'string' }, tier: { type: 'number' }, section: { type: 'string' }, query: { type: 'string' } },
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
        properties: { entry_id: { type: 'string' }, rules_out: { type: 'string' }, why: { type: 'string' } },
        required: ['entry_id', 'rules_out'],
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
  },
  required: ['tickets'],
}

// ---------------------------------------------------------------- prompts
const opener = (id, type, extra) => `You are resolving one ticket of a meta dump build.
Work dir:  ${WORK}
Skill dir: ${SKILL}
Ticket id: ${id}   Type: ${type}   Depth: ${DEPTH}${budgetFor(type) ? `   Entry budget: ${budgetFor(type)} entries (fewer, sharper entries beat more; merge near-synonyms into aliases)` : ''}
Ticket file: ${WORK}/tickets/${id}.md (read it first if it exists)
Context: ${WORK}/map.md (destination jobs, query log, senses, layers, section plan) and ${WORK}/manifest.json (verbatim prompt)
Instructions: follow the "Opener" section and the "${type}" section of ${BRIEFS} exactly. The format is ${SCHEMA}.
${extra || `Write exactly one file: ${WORK}/shards/${id}.json`}
Return only the receipt or result the brief asks for, never the entries themselves.`

// URLs come from web content: single-quote them for the shell, so & ; $ and quotes stay data.
const shellQuote = s => `'${String(s).replace(/'/g, "'\\''")}'`

const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 40) || 'job'

const ticketCall = (t, phaseName) => () => agent(opener(t.id, t.type), { label: `${t.type}:${t.id}`, phase: phaseName, schema: RECEIPT })
const runTickets = (list, phaseName) => parallel(list.map(t => ticketCall(t, phaseName)))

// ---------------------------------------------------------------- discovery
// A found job (a watch or scrape made from a discover pick) has no ticket file: its prompt is the whole ticket.
const foundCall = (t, phaseName) => () => agent(opener(t.id, t.type, `This ticket was made by discovery (${t.by}); there is no ticket file.
URL: ${t.pick.url}
Answers: ${t.pick.answers || 'see the query log in map.md'}${t.pick.take ? `\nTake: ${t.pick.take}` : ''}
origin: web. It was found online, so its facts, frames and images are researched and every source it adds says origin: "web"; never pass --reference.${t.type === 'scrape' ? `
Fetch it with a screenshot: python3 ${SKILL}/scripts/webpages.py fetch ${shellQuote(t.pick.url)} --work ${WORK} --screenshot, then open the screenshot with the Read tool and look at it.
Interpret, don't copy: say what the page shows and what transfers to this task, in the task's own terms; quote only the facts you rely on.` : ''}
Write exactly one file: ${WORK}/shards/${t.id}.json`), { label: `${t.type}:${t.id}`, phase: phaseName, schema: RECEIPT })

// A moodboard told about the images discovery found (already within the caps), so it collects them as web-found.
const boardCall = (t, images, phaseName, scope) => () => agent(opener(t.id, 'moodboard', `${scope || ''}Discovery found these images online (origin web, already within the caps). Save this JSON as ${WORK}/images/found-${t.id}.json, then run python3 ${SKILL}/scripts/images.py collect --work ${WORK} --found ${WORK}/images/found-${t.id}.json alongside your other collect commands:
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
  const out = await agent(opener(t.id, 'discover',
    `Write no shard and no ticket files. Record every candidate you considered in ${WORK}/discovered/${t.id}.json, then return your picks. Caps at depth ${DEPTH}: at most ${DISCOVERY_CAP.videos} videos, ${DISCOVERY_CAP.pages} pages and ${DISCOVERY_CAP.images} images.`),
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

const tier1Gaps = (verified, key, describe) => verified.flatMap(v => (v[key] || []).map(x => ({
  job: v.job, decision: `${describe(x)}${x.why ? ` (${x.why})` : ''}`, tier: 1,
})))
let maxRounds = MAX_ROUNDS
const results = { rounds: 0, builds: [], verify: [], audits: [], gap_tickets: [], entries_from_receipts: total, discovery }
let round = 1
while (true) {
  results.rounds = round

  if (!LITE) {
    phase('Normalize')
    const normId = round === 1 ? '90-normalize' : `9${round - 1}-normalize-r${round}`
    await agent(opener(normId, 'normalize', `Round ${round}. Write exactly one file: ${WORK}/shards/${normId}.json`),
      { label: `normalize:r${round}`, phase: 'Normalize', schema: RECEIPT })
  }

  phase('Synthesis')
  const synth = await agent(opener('95-synthesis', 'synthesis',
    `Round ${round}. Write (or rewrite) ${WORK}/shards/95-synthesis.json; any repair shard is ${WORK}/shards/97-repair-r${round}.json. Build with: ${FINALIZE} build ${WORK}`),
    { label: `synthesis:r${round}`, phase: 'Synthesis', schema: SYNTH, effort: 'high' })
  results.builds.push(synth)
  if (!synth || !synth.built) {
    log(`synthesis round ${round} did not produce a passing build; stopping so the main loop can repair it`)
    break
  }
  const dump = synth.dump_path

  phase('Verify')
  const jobs = (synth.jobs || []).slice(0, MAX_VERIFY)
  if ((synth.jobs || []).length > MAX_VERIFY) log(`verifying ${MAX_VERIFY} of ${synth.jobs.length} routed jobs (depth ${DEPTH} cap); the rest were not dry-run`)
  const auditId = `96-audit-r${round}`
  const auditCall = LITE ? [] : [() => agent(opener(auditId, 'audit', `Round ${round}. The built dump is ${dump}. Write exactly one file: ${WORK}/shards/${auditId}.json`),
    { label: `audit:r${round}`, phase: 'Verify', schema: AUDIT })]
  const outcomes = await parallel([
    ...auditCall,
    ...jobs.map(job => () => agent(opener(`verify-${slug(job)}`, 'verify',
      `Round ${round}. The built dump is ${dump}. Your job: "${job}". Write no shard; write ${WORK}/verify/r${round}-${slug(job)}.json`),
      { label: `verify:${slug(job)}`, phase: 'Verify', schema: VERIFY })),
  ])
  const audit = LITE ? null : outcomes[0]
  const verified = outcomes.slice(auditCall.length).filter(Boolean)
  results.audits.push(audit)
  results.verify.push(...verified.map(v => ({ round, job: v.job, guesses: v.guesses.length, tier12: v.guesses.filter(g => g.tier <= 2).length, contradictions: (v.contradictions || []).length, narrowings: (v.narrowings || []).length, misses: (v.misses || []).length })))

  // Structural defects are tier-1 gaps: a concrete value pulling against a tier-1 objective entry (ADR 0003), and an
  // entry ruling out what the request plausibly includes (ADR 0005).
  const contradictions = tier1Gaps(verified, 'contradictions', c => `contradiction: ${c.value_id} pulls against ${c.against_id}`)
  const narrowings = tier1Gaps(verified, 'narrowings', n => `narrowing: ${n.entry_id} rules out ${n.rules_out}`)
  if (LITE && round === 1 && narrowings.length && maxRounds < 2) {
    maxRounds = 2
    log(`lite: ${narrowings.length} narrowings found, so one widening round runs`)
  }
  const tier12 = [...contradictions, ...narrowings, ...verified.flatMap(v => v.guesses.filter(g => g.tier <= 2).map(g => ({ job: v.job, ...g })))]
  const missing = (audit && audit.missing_clauses) || []
  log(`round ${round}: ${tier12.length} tier-1/2 gaps (${contradictions.length} contradictions, ${narrowings.length} narrowings) across ${verified.length} jobs, ${missing.length} untraced prompt clauses`)
  results.remaining_gaps = [...tier12, ...missing.map(clause => ({ decision: `untraced prompt clause: ${clause}`, tier: 1 }))]
  if (round >= maxRounds || (!tier12.length && !missing.length)) break

  phase('Gaps')
  const plan = await agent(`${opener(`gaps-r${round}`, 'gaps', `Round ${round}. Write ticket files only (no shard), named ${WORK}/tickets/6<N>-gap-<section>-r${round + 1}.md with N 0-9 unused so far.`)}

Verify guesses at tier 1-2, contradictions and narrowings (JSON): ${JSON.stringify(tier12)}
Untraced prompt clauses (JSON): ${JSON.stringify(missing)}
Return {"tickets": [{"id", "type"}]} for the tickets you wrote (type specialist, research, scrape, watch or discover), or {"tickets": []}.`,
    { label: `gaps:r${round}`, phase: 'Gaps', schema: GAPS })
  const gapTickets = ((plan && plan.tickets) || []).filter(t => t.id && (t.type === 'specialist' || GAP_EVIDENCE.has(t.type)))
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
    if (!LITE) {
      const nId = `9${round - 1}-normalize-r${round}`
      await agent(opener(nId, 'normalize', `Round ${round}. Write exactly one file: ${WORK}/shards/${nId}.json`),
        { label: `normalize:r${round}`, phase: 'Normalize', schema: RECEIPT })
    }
    const s2 = await agent(opener('95-synthesis', 'synthesis',
      `Round ${round}. Rewrite ${WORK}/shards/95-synthesis.json; any repair shard is ${WORK}/shards/97-repair-r${round}.json. Build with: ${FINALIZE} build ${WORK}`),
      { label: `synthesis:r${round}`, phase: 'Synthesis', schema: SYNTH, effort: 'high' })
    results.builds.push(s2)
    results.rounds = round
    break
  }
}

results.entries_from_receipts = total
results.remaining_gaps = results.remaining_gaps || []
results.next = (results.remaining_gaps.length
  ? `Main loop: write the ${results.remaining_gaps.length} remaining_gaps as open_questions (each with a default, impact and how to resolve) in ${WORK}/shards/98-open-questions.json, then run `
  : 'Main loop: run ') + `${FINALIZE} build ${WORK} (audit demotions apply on rebuild), read ${WORK}/report.json, then present.`
return results

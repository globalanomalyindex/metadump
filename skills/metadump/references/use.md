# Use mode: working from an existing meta dump

For any skill, tool or session doing work in a project that has a meta dump. The point is to pull the few thousand tokens that matter for the step at hand, never the whole file, and to keep the dump true as decisions get made.

**Consult, don't obey.** The dump is a resource of objective information, not a rulebook. The user's prompt and your judgment decide; the dump supplies the specifics you would otherwise guess (exact values, real references, measurements, timings, transcripts, sourced facts). Prefer its objective, sourced entries over your guesses, treat its `proposed` entries as one option among others, and when you choose differently from an entry, say so where it matters to the user.

`F` below is the dump path, e.g. `metadumps/counter-carton.metadump.json`.

## 1. Locate

- A path was given → use it.
- Otherwise glob `metadumps/*.metadump.json` (and `**/*.metadump.json` if none). Several → pick by `manifest.slug` / `manifest.prompt` relevance to the current task; if two are plausible, say which you chose.
- Check `manifest.version` and `manifest.derived_from` so you use the newest dump in a lineage.

## 2. Read the head (about 2–4K tokens, always)

```bash
jq '{manifest, essence, routing}' F
```

or Read with `limit = manifest.head_lines`. The head tells you the verbatim prompt, what matters most (essence and signature), and which routes exist with their token cost.

## 3. Pick a route and pull its slice

**Reading lean works best: head → `routing[0]` → one route (plus its export, if there is one) → scoped anti-keywords and checks.** That is usually 3–5 `jq` calls and a few thousand tokens. Then do the work, and come back when you hit a term you can't resolve or a question the dump might answer. Reading every section costs time and tokens and dilutes attention without improving the result (the first A/B test averaged 21 reads per task for no gain over 5).

First pull the automatic route `routing[0]` (`always first: the defining tier-1 entries`, about 1–2K tokens): what the task is most about. Then match the job you are doing to a `routing[].job` (read `when` too) and run that route's `jq`:

```bash
jq '<routing[i].jq>' F
```

Add the anti-keywords and review prompts for your scope. For a consumer scope like `image`, `copy`, `code` or `search`:

```bash
jq --arg s image '.anti_keywords | with_entries(select((.value.scope // ["*"]) as $sc | ($sc|index("*")) != null or ($sc|index($s)) != null))' F
jq --arg s image '.checks | with_entries(select((.value.scope // ["*"]) as $sc | ($sc|index("*")) != null or ($sc|index($s)) != null))' F
```

Anti-keywords scoped to a section pointer (`"/packaging"`) apply when your slice includes that section. Pull them with the same filter using the pointer as `$s`.

No route fits? Look terms up instead of reading sections:

```bash
jq '.index["frosted glass"]' F          # hits (exact phrase), words (contains the word), not_meant (senses to avoid)
# fetch every entry a lookup points at, in one command:
jq --arg t opal '. as $d | [(.index[$t].hits + (.index[$t].words // []))[] | ltrimstr("/") | split("/") as $p | $d | getpath($p)]' F
jq '.index | keys[] | select(contains("aero"))' F   # partial key match when a lookup misses
grep -n 'frosted' F                     # every entry is one line, so grep returns whole entries
jq '[del(.index) | .. | objects | select(.tier == 1 and has("prov"))]' F   # the defining set
```

If the job is recurring and no route covers it, that is a gap: add a route in a write-back (step 6).

A small dump (head says total tokens under ~15K) can be read whole; anything bigger, slice it.

### Pages, videos and images

Dumps built with `scrape`, `watch` or `moodboard` tickets hold measured and transcribed entries. Find them by route first, then by index or shape:

```bash
jq '[.. | objects | select(.kind == "timeline")]' F                       # every measured timeline
jq '[.. | objects | select(.kind == "cue" and (.text | test("stagger")))]' F   # transcript passages on a topic
jq '[.. | objects | select(.method == "pixel-sample")]' F                 # measured palettes
jq '[.. | objects | select(.method == "scraped")] | .[0:5]' F              # facts taken from pages, with their `where`
jq '.index["ease out"]' F                                                 # or look the term up
```

The moodboard page sits beside the dump (`metadumps/<slug>.moodboard.html`, with a `.png` render when a browser was available): open or Read it when you need to see the references, then come back to the entries for the numbers. Timelines read as plus or minus one frame; easing names are the nearest standard curve. `exports.md` says how timelines, transcripts and palettes become animation parameters, copy and image prompts.

## 4. Apply

- **Tiers say relevance, not obligation.** Tier 1 is what the task is most about: read it for every job and let it shape the work. Tier 2 is relevant to most jobs, tier 3 is context, and tier 4 is a labeled pool of options to sample for variety. None of them is a requirement; the user's prompt is.
- **Objective first.** Prefer `user_stated`, `reference_observed` and `researched` entries (and anything with a `method` such as `measured`, `scraped`, `transcribed`, `frame-diff` or `pixel-sample`) over your own guesses. `inferred` entries are directions you may adapt; `proposed` entries in the options area are one option among others.
- **Keep both poles of every tension.** `essence.tensions` names the contradictions that define the work ("overexposed yet saturated", "measured indulgence"). Outputs that express both sides at once tend to be the strong ones: blown-out highlights *and* a saturated sky, not a pale washed-out compromise. Resolving a tension to one pole is the most common way a careful output ends up flat.
- **The user's words outrank the builder's choices.** `proposed`/`inferred` parameters (a safe palette, a token scale, a layout) are starting points. When one pulls against a tier-1 `user_stated` quality, the user's quality wins and the parameter adapts. If it guards a hard constraint like text contrast, look for a design that satisfies both, e.g. keep the saturated field and put text on a local scrim, rather than draining the whole design.
- **State as fact** only `user_stated`, `reference_observed`, `researched`. Never fill an `unknown` silently: use the `open_questions` default and say so.
- **Exclusions become rewrites:** each `not_wanted`'s `instead` is the positive way to say it. For `not_meant`, use the meant sense and avoid the excluded one.
- **Variables are free:** an invariant's `variable` field lists what may change.
- **Use exports when they exist** (`exports.image.*`, `exports.llm_brief`, `exports.briefs.*`), after checking `compiled_from_version == manifest.version`. A stale export should be recompiled from its `from` ids before use. An export is a starting point; adapt it to the job.
- Consumer-specific conversion rules (image models with and without negative fields, LLM briefs, subagent briefs, code, TDD, search metadata, timelines, transcripts, palettes) are in `exports.md`.

## 5. Review the output (optional)

`checks` are review prompts, not gates. When they help, run the ones in your scope as a self-review:

| `test.kind` | How |
|---|---|
| `regex` | run the pattern over the text output |
| `count` / `measure` | count or measure the property |
| `command` | run it (tests, lint) |
| `visual` | look at the image or render against the description |
| `judge` | judge against `text`, citing evidence |

If your output departs from one, that can be the right call: keep it when the user's words or the work justify it, and mention the deviation briefly when it matters to the user. There is no forced revision pass. Engineering checks that run real tests or lint (`command`) are worth running, since they report facts about the code.

## 6. Write back

The dump stays live: new decisions go into it with honest provenance.

- **User decides something** ("go matte", "unit conversion is never wanted"): add or edit an entry with `prov: "user_stated"`, `decided_in: "use-mode <date>: <short quote>"`. If it answers an open question, delete that question (or add `"resolved": "<entry id>"`).
- **You discover something** (an edge case, a library fact, a better term): add it as `inferred` (or `researched` with a source you fetched), tier 2–3, never tier 1 on your own authority.
- **Engineering:** mark test-list items `done` with `verified_by: "<test name>"`; add new edge cases as `todo` (`inferred`).

Edit with jq, then let finalize restore the layout, index, costs and version:

```bash
jq '.palette["c-matte"] = {"term":"matte finish","tier":1,"prov":"user_stated","anchor":"matte","decided_in":"use-mode 2026-11-05: user said go matte","text":"All carton faces matte; no specular hotspots."}' F > F.tmp && mv F.tmp F
python3 <SKILL>/scripts/finalize.py build F --bump
```

`--bump` increments `manifest.version`, so exports compiled from the old version now warn as stale: recompile the ones you use. If finalize exits 1, fix the reported error; nothing was written.

Only the main loop writes back. Subagents return what they relied on (`cites[]`) and their findings, and the orchestrator records them, so parallel agents never edit the file at once.

## 7. Orchestrating subagents from a dump

- Give each subagent the dump path and its brief (`exports.briefs.<role>` if one exists, else a route's paths). Tell it to read the head plus its `load` paths only.
- Ask for `cites[]` (dump ids relied on) in every result. A merge step can use the dump's review prompts to compare results for consistency, as a review, not a gate.
- In a Workflow script, put the brief in the agent prompt; agents can run `jq` themselves.

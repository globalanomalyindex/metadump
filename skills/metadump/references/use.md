# Use mode: working from an existing meta dump

For any skill, tool or session doing work in a project that has a meta dump. The point is to pull the few thousand tokens that matter for the step at hand, never the whole file, and to keep the dump true as decisions get made.

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

First pull the automatic route `routing[0]` (`always first: the defining tier-1 entries`, about 1–2K tokens): tier 1 must be expressed in every job. Then match the job you are doing to a `routing[].job` (read `when` too) and run that route's `jq`:

```bash
jq '<routing[i].jq>' F
```

Always add the constraints for your scope. For a consumer scope like `image`, `copy`, `code` or `search`:

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

## 4. Apply

- **Tier 1 must be expressed. Tier 2 should be. Tier 3 is context. Tier 4** is a labeled pool: sample at most two options, never treat them as constraints.
- **State as fact** only `user_stated`, `reference_observed`, `researched`. Treat `inferred`/`proposed` as directions you may adapt. Never fill an `unknown` silently: use the `open_questions` default and say so.
- **Exclusions become rewrites:** use each `not_wanted`'s `instead`. For `not_meant`, use the meant sense and avoid the excluded one.
- **Variables are free:** an invariant's `variable` field lists what you may change. Don't hard-code it.
- **Use exports when they exist** (`exports.image.*`, `exports.llm_brief`, `exports.briefs.*`), after checking `compiled_from_version == manifest.version`. A stale export should be recompiled from its `from` ids before use.
- Consumer-specific conversion rules (image models with and without negative fields, LLM briefs, subagent briefs, code, TDD, search metadata) are in `exports.md`.

## 5. Check the output

Run each check in your scope against what you produced:

| `test.kind` | How |
|---|---|
| `regex` | run the pattern over the text output |
| `count` / `measure` | count or measure the property |
| `command` | run it (tests, lint) |
| `visual` | inspect the image or render against the spec |
| `judge` | judge against `text`, citing evidence |

A failed `must` gets one revision pass. Anything still failing is reported to the user with its check id. Don't silently ship it, and don't loop forever.

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
- Ask for `cites[]` (dump ids relied on) in every result, and have the merge step run the dump's checks across all results for consistency.
- In a Workflow script, put the brief in the agent prompt; agents can run `jq` themselves.

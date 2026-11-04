# Create mode: full procedure

Read this when building a meta dump. `<SKILL>` is the skill's base directory; `<WORK>` is `metadumps/.work/<slug>/` under the project root.

Contents: 1. Setup · 2. Depth and cost · 3. Chart (map.md) · 4. Tickets · 5. Prompt shard · 6. Fan-out · 7. Build, verify, loop · 8. Present · 9. Resume and expand

---

## 1. Setup

- **Slug:** short kebab-case name for the task (`counter-carton`, `recipe-cli`, `luminous-translucency`).
- **Paths:** create `<WORK>/tickets/`, `<WORK>/shards/`, `<WORK>/verify/`. The finished dump goes to `metadumps/<slug>.metadump.json`. If the project uses git, add `metadumps/.work/` to `.gitignore` (the work dir is resumable scratch, not the deliverable).
- **References:** give each one an id `r1, r2, …` and add it to `manifest.references` and later to `sources` (kind `reference`, path or URL, short title). Don't copy large files; point at them.
- **manifest.json:** write `<WORK>/manifest.json` now:

```json
{"schema": "metadump/1", "slug": "<slug>", "version": 1, "created": "<today>",
 "prompt": "<the user's prompt, verbatim>", "references": [...], "consumers": [...], "depth": "standard",
 "derived_from": [], "built": ""}
```

The verbatim prompt matters: it anchors every `user_stated` entry, and the audit traces the dump back to it.

## 2. Depth and cost

| Depth | When | Roster | Rounds | Typical dump | Run cost (tokens processed, wall time) |
|---|---|---|---|---|---|
| `lite` | quick single-consumer tasks, small prompts, or the user asks for fast/cheap | prompt + 1–2 research + 2–3 specialists + exclusion + synthesis + 2 verify (no normalize, no audit) | 1 | 20–35K tokens | ~1–1.5M, 25–35 min (measured: 8 agents, 1.36M, 34 min) |
| `standard` (default) | most tasks | prompt + observe per 1–2 refs + 2–4 research + 4–8 specialists + lexicon + exclusion + normalize + synthesis + audit + up to 6 verify | up to 2 | 40–90K tokens | ~2–4M, 40–70 min (estimate) |
| `deep` | reference-heavy jobs (≥3 references), multi-consumer systems, or the user asks for exhaustive | as standard, more specialists (8–12) and research (4–6), up to 8 verify | up to 3 | 90–150K+ tokens, still routed | ~4–7M, 1–2 h (estimate) |

"Tokens processed" counts every agent re-reading its context across its tool calls. It is far more than the dump's own size.

**Entry budgets per shard** (the Workflow script puts these in each worker's prompt; give them to Agent-tool workers yourself):

| Type | lite | standard | deep |
|---|---|---|---|
| research | 8–12 | 10–20 | 15–30 |
| specialist | 12–20 | 20–35 | 30–50 |
| lexicon | 10–15 | 15–30 | 25–45 |
| exclusion | 10–15 | 15–25 | 20–35 |
| observe | 10–20 | 20–35 | 30–50 |

Without budgets, workers write everything they can think of: the first lite run produced 212 entries against a plan of about 80.

Pick the depth from the request. State one line before fan-out, e.g. "Standard depth: ~16 agents, roughly 2–4M tokens processed, about an hour." Then proceed. Don't wait for approval unless the user asked to be consulted. The user can say "lite" or "deep" any time.

## 3. Chart (write `<WORK>/map.md`)

Charting decides the dump's shape. Do it in the main loop, carefully: everything downstream is only as good as the plan.

```markdown
# Map: <slug>

## Destination: consumer jobs
<!-- 4–12 jobs the dump must serve. Infer from the prompt and the project (what tools/skills exist: image generation? a codebase? tests? a CMS?). Always include "understand the task" and "check an output". These become routing jobs. -->
- J1 understand the task: what it is and what matters most
- J2 write the image-generation prompt (FLUX.2)
- J3 lay out the packaging front
- J4 check an output against the dump

## Query log
<!-- 20–40 questions consumers will ask mid-work, each with the job and the tier its answer will have. This is what the dump is a search index for. -->
| # | Job | Question | Tier |
|---|---|---|---|
| 1 | J2 | What is the defining composition? | 1 |
| 2 | J3 | Which corner holds the brand mark? | 2 |

## Senses
<!-- ambiguous words in the prompt and the senses NOT meant -->
- "counter": brand, not countertop / tally counter

## Layers
<!-- the levels where properties could drift between each other -->
- scene / package / printed graphic / depicted food / evoked feeling

## Gaps
<!-- what the prompt leaves open that a consumer would otherwise guess -->

## Section plan
<!-- group questions + gaps into sections named in the task's own words; pick mechanisms from mechanisms.md; a section exists only if a job or query hits it -->
| Section | Answers queries | Mechanisms | Ticket |
|---|---|---|---|
| composition | 1, 4, 7 | invariant/variable, layers, exemplars | 30-composition |
| palette | 9–12 | lexicon, parameters (photo samples) | 31-palette |

## Roster
| Ticket | Type | Wave | Blocked by |
|---|---|---|---|
| 01-prompt | prompt | 0 (main loop) | |
| 10-observe-r1 | observe | 1 | |
| 20-research-lineage | research | 1 | |
| 30-composition | specialist | 2 | 10, 20 |
| 70-lexicon | lexicon | 2 | 10, 20 |
| 75-exclusion | exclusion | 2 | |
| 90-normalize | normalize | 3 | all of wave 2 |
| 95-synthesis | synthesis | 4 | 90 |

## Fog
<!-- questions you can tell are coming but can't state precisely yet; revisit after verify -->
```

How to choose the section plan for any domain:
1. Start from the destination jobs and the query log, never from a template. A REST API dump has no `palette`; a carton dump has no `error_model`.
2. For each cluster of questions, ask which mechanism answers it (see `mechanisms.md`). One section may use several.
3. Name sections the way a practitioner of that domain would (`verse_form`, `seams`, `macro_bands`, `subject_lines`).
4. Survival rule: drop any section no job or query needs. Breadth comes from the query log, not from symmetry.

`references/worked-plans.md` has three example plans (visual packaging, an engineering CLI with TDD, a short story) to calibrate against. They are illustrations, not templates.

## 4. Tickets

One file per ticket, `<WORK>/tickets/<NN-slug>.md`:

```markdown
# 31-palette: Palette and color roles
Type: specialist
Wave: 2
Blocked by: 10-observe-r1, 20-research-lineage
Writes: shards/31-palette.json
Load: map.md, manifest.json, draft.json sections: palette (if any), anti_keywords

## Question
Answer queries 9–12 from the query log: color roles, sampled values, relationships between bands, and what color must never imply.

## Returns
Section `palette`: lexicon entries for each color role (term, aliases), parameters for sampled values (status: photo sample),
bindings with never_implies, 2–4 not_wanted anti-keywords scoped to /palette, open questions for unmeasurable values.
```

Create all ticket files first, then fill in `Blocked by` (ids must exist before they can reference each other). A ticket is done when its shard exists; that is all the state resume needs.

## 5. Prompt shard (main loop, before fan-out)

Write `<WORK>/shards/01-prompt.json` yourself, following the `prompt` brief in `briefs.md`. It is cheap, it is the only source of `user_stated` entries, and having it on disk lets every worker build on the user's own words.

## 6. Fan-out

Workers write shards and return receipts, so the main context only sees ids, counts and notes.

### With the Workflow tool (preferred when available)

Calling Workflow is part of this skill's instructions, which counts as the user opting in.

```
Workflow({
  scriptPath: "<SKILL>/scripts/index.workflow.js",
  args: {
    skill_dir: "<SKILL>", work_dir: "<absolute WORK>", slug: "<slug>", depth: "standard", max_rounds: 2,
    tickets: [ {"id": "10-observe-r1", "type": "observe", "wave": 1}, ..., {"id": "95-synthesis", "type": "synthesis", "wave": 4} ]
  }
})
```

The script runs wave 1 (observe + research) → wave 2 (specialists, lexicon, exclusion) → normalize → synthesis (which builds) → audit + one verify per routed job → a gap round if tier-1/2 guesses remain (up to `max_rounds`). It returns the build result, verify summaries and gap tickets. Pass every ticket except `01-prompt` (already written).

### Without Workflow (plain subagents)

Run the same waves with the Agent tool, at most 8 calls per message. Each agent's prompt is the brief opener from `briefs.md` with `<WORK>`, `<SKILL>`, `<ID>`, `<TYPE>` filled in, plus "Follow the `<type>` section of `<SKILL>/references/briefs.md`." Wait for a wave's receipts before starting the next. Run `finalize.py merge <WORK>` between waves only if you want to look at the draft yourself; workers run it on their own.

## 7. Build, verify, loop

1. After synthesis: `python3 <SKILL>/scripts/finalize.py build <WORK>`. It merges, validates, fixes what it safely can, builds the index, measures each route and writes `metadumps/<slug>.metadump.json` plus `<WORK>/report.json`. Exit 1 means nothing was written: fix the listed errors (a `97-repair.json` synthesis shard, or edit the offending shard) and rerun.
2. Read the report's `fixes`. Many demotions from one ticket mean it over-claimed: check it.
3. Verify: one dry-run consumer per routed job (the `verify` brief) plus the `audit` brief. Their guesses are the dump's real gaps.
4. **Stop** when any of these holds:
   - no tier-1/2 guesses remain and no prompt clause is untraced;
   - a round added fewer than ~10% new entries;
   - `max_rounds` reached (lite 1, standard 2, deep 3).

   Otherwise write gap tickets (the `gaps` brief), run them as wave 2, then normalize (`91-normalize-r2`), synthesis again (it rewrites `95-synthesis.json`), build, verify.
5. Remaining gaps go to `open_questions` with defaults. Nothing is asked of the user during the build.
6. Fill `manifest.built` with a one-line process note (edit `<WORK>/manifest.json`, rebuild).

## 8. Present

Tell the user, briefly:
- the path, size (entries, ~tokens) and depth;
- the essence sentence and the tier-1 signature;
- the routing jobs (what any skill can now pull from it);
- provenance mix (how much is user_stated / observed / researched vs inferred / proposed), so they know how much is grounded;
- the top open questions with the defaults assumed. They can answer any time; answers become `user_stated` through use mode.

Don't paste the dump into the chat.

## 9. Resume and expand

- **Interrupted run:** tickets whose shard exists are done. Rerun only the missing ones, then continue from the first incomplete wave.
- **Expand an existing dump:** treat the old dump as a reference: add an `inherit` ticket (shard `05-inherit-<name>`), set `manifest.derived_from`, chart only the new jobs and gaps, and build into a new version. Inherited entries keep their provenance; the new prompt wins conflicts.
- **Rebuild a hand-made dump** (like a dump made before this skill existed): same as expand. Its entries come in as `inherited` with their original claims capped by what the old file can actually support; anything without provenance arrives as `inferred`.

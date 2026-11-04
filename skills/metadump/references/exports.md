# Export rules

How to compile `exports` (create mode, synthesis step) and how a consumer turns a slice into its own input (use mode). Exports exist only for consumers the dump declares in `manifest.consumers`; don't compile payloads nobody will use.

The dump stays JSON so it can be addressed by path. What reaches a target model is converted to whatever format that model reads best, usually prose. No study shows JSON braces beat prose at inference; the gains come from more specific, better-ranked content.

## General rules (all consumers)

1. **Order by tier.** Tier-1 content first (models weight early tokens more), tier 2 next, tier 3 only where the job touches it, tier 4 only as at most two labeled options.
2. **Facts vs choices.** Only `user_stated`, `reference_observed` and `researched` content may be phrased as fact. `inferred`/`proposed` content is phrased as a direction or choice. `unknown` is never filled silently: either use the `open_questions` default and say so, or leave it open.
3. **Exclusions become rewrites.** Every `not_wanted` reaches the target as its `instead`. A bare "no X" is reserved for real negative fields, because naming X puts X into the conditioning.
4. **Stamp it.** Every payload carries `compiled_from_version` and `from` (the entry ids it was compiled from).
5. **Keep it short.** An export is a slice, not a summary of the whole dump: an image prompt under ~120 words, an LLM brief under ~600 tokens.

## Image generation

| Model family | Negative field? | How to express exclusions |
|---|---|---|
| Stable Diffusion 1.x / SDXL / SD3.5 (ComfyUI, A1111) | Yes (CFG negative conditioning) | `negative`: `not_wanted` terms + variants as short nouns, ≤12. Negatives applied too early in denoising can *cause* the object (reverse activation, ECCV 2024: https://arxiv.org/abs/2406.02965v1), so keep the positive prompt carrying the `instead`. |
| Midjourney | `--no a, b` (weight −0.5) | Single words only: `--no modern clothing` is read as "no modern" + "no clothing" (https://docs.midjourney.com/docs/no). Put phrases in the positive prompt as rewrites. |
| Ideogram 3.0 | `negative_prompt` | Main prompt wins on conflict; still lead with the rewrite. |
| FLUX.1 dev/schnell | Effectively no (guidance-distilled) | Rewrites only. |
| FLUX.2 | No ("does not support negative prompts": https://docs.bfl.ai/guides/prompting_guide_flux2) | Rewrites only: "no blur" → "sharp focus throughout". Words placed first get more attention. |
| OpenAI gpt-image | No | Rewrites in the prose, plus one short `Constraints:` line ("State exclusions and invariants explicitly": https://developers.openai.com/cookbook/examples/multimodal/image-gen-1.5-prompting_guide). |
| Google Gemini image / Imagen 4 | No | "Semantic negative prompts": describe the desired absence positively ("an empty, deserted street"): https://developers.googleblog.com/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/. Optional `Constraints:` line for Gemini. |

**Default when no model is named** (`exports.image.generic`):

```json
{"compiled_from_version": 1, "from": ["..."],
 "positive": "Model-neutral prose: subject and composition (tier 1), then material, light, palette (tier 2), then context (tier 3). Every not_wanted folded in as its instead.",
 "constraints": "≤5 short items for LLM-backed models (gpt-image, Gemini): invariants and hard exclusions.",
 "negative": "SD-style comma list of not_wanted terms + variants (≤12 nouns); only for models with a negative field.",
 "params": {"aspect": "4:5"},
 "notes": "Which entries are choices (proposed) a user may want to vary."}
```

When the consumer names a model, compile `exports.image.<family>` in that family's own conventions (e.g. FLUX.2 drops `negative`; Midjourney turns it into `--no` single words; SD keeps it).

Tier 4 candidate pools: offer at most two as named variants (`"variants": [{"name": "dusk", "positive": "..."}]`), never blended into the main prompt.

## LLM brief (copy, writing, analysis, any text model)

`exports.llm_brief.text`, ≤600 tokens, in four labeled blocks:

```
Must: tier-1 entries as plain directives (each traceable to `from`).
Should: tier-2 entries relevant to text.
Say instead: each not_meant/not_wanted for text as "say X, not Y".
Unknowns: open questions with the default being assumed.
```

Copy consumers also turn `not_wanted` text phrases (and `noise` words) into lint patterns: a `regex` check per phrase.

## Subagent briefs (any orchestrator, including Workflow / Ultracode)

`exports.briefs.<role>`: one per recurring specialist job a downstream orchestrator will run (e.g. "palette variant designer", "endpoint implementer", "subject-line writer"):

```json
{"compiled_from_version": 1, "load": ["/palette", "/anti_keywords"], "question": "Design a dark-mode variant of the palette.",
 "returns": "palette entries in the dump's entry envelope, or a list of decisions with cites[]", "budget": "≤ 30K tokens"}
```

The orchestrator pastes the dump path and the brief; the subagent reads the head plus its `load` paths (never the whole file) and returns `cites[]`, the dump ids it relied on, so a merge step can check consistency across agents. In a Workflow script, put the brief text in the agent prompt and pass the dump path; agents can run `jq` themselves.

## Code and UI builds

- Pull `parameters`, `invariants`, domain vocabulary, API surface and the `checks` scoped to the build.
- Parameters become named constants or design tokens and keep their `status` (an `illustrative` radius is a starting value, not a spec).
- `variable` fields are free choices: don't hard-code them as requirements.
- Forbidden APIs/patterns (`not_wanted` with `scope: ["code"]`) become lint rules or negative tests (e.g. ESLint `no-restricted-imports`).
- Don't copy dump text into code comments; link tests to entries with `verified_by` instead.

## TDD loops

- Test list: take tier-1 items first, one per red-green cycle.
- Oracles: expected values only from `user_stated`, `reference_observed` or `researched` examples. If the only example is `inferred`, ask the user or mark the test blocked; don't grade the model's own guess.
- Invariants → property tests. Behavioral `not_wanted` → negative tests. Structural `not_wanted` → lint.
- After each green: re-pull tier-1 + `not_wanted` for the touched scope, check the diff, mark the item `done` with `verified_by`, add newly discovered edge cases as `todo` (`prov: "inferred"`) without writing those tests yet.

## Search and publishing metadata

`exports.search`: titles, descriptions, alt text, short/medium/long-tail phrases, and `negative_keywords` from `not_meant` terms (with `match`: exact/phrase/broad as in search-engine negative keywords). Mark all of it as candidate vocabulary: no volume or ranking is implied unless a researched source measured it.

## Other generators

Music, video, voice, 3D: same rules. Parameters (BPM, key, duration, aspect, frame rate) go in `params`; mood words come from cue → descriptor entries with their caveats; exclusions are rewrites unless the target has a real negative field.

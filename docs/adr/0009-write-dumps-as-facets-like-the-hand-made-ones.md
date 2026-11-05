# Write dumps as facets, the shape of the hand-made ones

Before this skill existed, the owner made meta dumps by hand by asking a model for one: `apple_rounded_ui_metadata.json` and `luminous_chromatic_translucency_metadata.json`, about 11 KB (3K tokens) each. A 0.6.0 dump of a shopping component was 205 KB (51K tokens, 195 entries), and 79 of its entries had prose too long to paste into a prompt. The owner wanted the dumps to be more like the hand-made ones.

What makes the hand-made files work:
1. **A thesis on top**, the one idea that explains the rest ("colors appear to exist inside materials rather than merely on their surfaces"), plus a one-line summary.
2. **Facets, not facts.** Each area (geometry, color, materials, motion) is one small object.
3. **Three layers per facet:** what it is (properties and keywords), how it behaves (cause and effect: "thicker transparent material looks darker"), and why (a principle).
4. **Short phrases.** List items run two to four words. Full sentences appear only for behaviors and principles.
5. **Many registers** for the same thing: technical, perceptual, emotional, cultural, search queries and vision signals.
6. **A formula with roles** ("blue: identity, white: luminosity"), **tensions** as pairs, **influences** with what each contributes, a **descriptor per reference**, and **numbers labeled as illustrative**.
7. **Anti-patterns, a ready prompt and a negative prompt.**
8. **Small enough to read whole.**

We decided that every entry is written as a facet: a line of `text` (40 words at most), `properties`, `keywords` and `descriptors` as short phrases, `behaviors`, a `principle`, `signals`, and `tokens` with a `status`. Dumps open with a thesis, a `summary` and a `formula` in the essence. Lexicon passes write a keyword taxonomy by register, influences with contributions and search queries by focus. Observe and moodboard passes write one descriptor per reference. The digest folds one-fact entries into facets. Budgets count facets, so they shrink: lite goes from 8–20 entries per worker to 3–10. finalize indexes the phrase lists and warns about prose that should be lists (`wordy_entry`: a `text` over 40 words or an `instead` over 20).

We kept what the hand-made files lacked and the A/B tests showed matters:
- **A tier and provenance on every facet.** In test 1 the hand-made luminous file's plain keywords (cyan, aqua, frosted glass, "Windows XP Bliss") pulled image prompts off course. The dump with tiers and scoped anti-keywords didn't drift.
- **Anti-keywords with an `instead`**, because FLUX.2, gpt-image and Gemini have no negative prompt.
- **Sources, the task ladder, the user's whole job, readings,** and the swarm's verify and widening passes. Test 7 showed a build without them narrows the request.

We rejected:
- copying the hand-made files' exact section names as a template, because the sections still come from the task;
- `avoid` lists inside facets, because an exclusion without a rewrite is useless to most image models;
- dropping provenance to get the hand-made look, for the drift reason above.

## Consequences

- Dumps are expected at about 8–15K tokens at lite, instead of 20–35K.
- Older dumps still validate. They just warn wherever their prose runs long.
- Measured once, in A/B test 8 (`ab-tests/2026-11-05-curves-haiku/`): the facet dump won presentation and craft by a wide margin, but it handed over one set of curves and every build copied it, and indexing every facet phrase made the index as big as the body. ADR 0010 records the fixes.

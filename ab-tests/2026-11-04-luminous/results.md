# A/B results: luminous chromatic translucency

Arms: **A** = prompt only; **C** = hand-made metadata file; **B** = metadump + skill

## Blind judge scores (0-10, mean of 2 judges x 2 runs per cell)

| task | arm | overall | fidelity | specificity | target fit | pitfalls avoided | mean rank (1-6) |
|---|---|---|---|---|---|---|---|
| t1-flux-headphones | A | **7.75** | 8.75 | 8 | 8.25 | 7.25 | 2.25 |
| t1-flux-headphones | C | **5.5** | 7 | 8 | 7.75 | 5.25 | 5 |
| t1-flux-headphones | B | **7** | 8.75 | 7.25 | 8 | 7.75 | 3.25 |
| t2-sdxl-busstop | A | **6.25** | 8 | 6.5 | 6 | 6.25 | 4 |
| t2-sdxl-busstop | C | **5.75** | 7.25 | 7.25 | 5.5 | 6.25 | 4.5 |
| t2-sdxl-busstop | B | **8** | 9 | 8.75 | 6.5 | 7.75 | 2 |
| t3-hero-html | A | **6.75** | 8 | 6.5 | 7.25 | 5 | 3.75 |
| t3-hero-html | C | **7.75** | 8.25 | 8.25 | 8.5 | 7.5 | 2.25 |
| t3-hero-html | B | **5.75** | 6.5 | 6.25 | 8.75 | 7.25 | 4.5 |
| t4-diagnose-render | A | **6.25** | 7.25 | 8.75 | 7.25 | 5.25 | 4.25 |
| t4-diagnose-render | C | **6.75** | 7 | 8.25 | 7.75 | 6.5 | 4 |
| t4-diagnose-render | B | **7.75** | 9 | 8.75 | 8 | 6.75 | 2.25 |
| all | A | **6.75** | 8 | 7.44 | 7.19 | 5.94 | 3.56 |
| all | C | **6.44** | 7.38 | 7.94 | 7.38 | 6.38 | 3.94 |
| all | B | **7.12** | 8.31 | 7.75 | 7.81 | 7.38 | 3 |

## Head to head (every output vs every output, same judge, overall score)

- **B vs A**: 18 wins, 12 losses, 2 ties (win rate 0.59)
- **B vs C**: 19 wins, 12 losses, 1 ties (win rate 0.61)
- **C vs A**: 12 wins, 18 losses, 2 ties (win rate 0.41)

Judge agreement: Pearson r = 0.24, mean |j1 - j2| = 1.54 points.

## Cost per run (subagent tokens, includes ~74K of system prompt every run)

| arm | runs | mean tokens | mean seconds | mean tool calls |
|---|---|---|---|---|
| A | 8 | 97284 | 251.3 | 5.1 |
| C | 8 | 108246 | 309.1 | 9.4 |
| B | 8 | 157985 | 430.0 | 21.4 |

## Objective metrics (means per arm)

```
{
 "t1-flux-headphones/A": {
  "words": 387,
  "clause_coverage": 1.0,
  "flux_prompt_words": 260.5,
  "negations_in_flux_prompt": 0
 },
 "t1-flux-headphones/C": {
  "words": 462,
  "clause_coverage": 0.86,
  "flux_prompt_words": 134,
  "negations_in_flux_prompt": 0
 },
 "t1-flux-headphones/B": {
  "words": 432.5,
  "clause_coverage": 1.0,
  "flux_prompt_words": 161.5,
  "negations_in_flux_prompt": 0
 },
 "t2-sdxl-busstop/A": {
  "words": 324,
  "clause_coverage": 1.0,
  "has_negative": [
   true,
   true
  ],
  "negative_terms": 49,
  "negations_in_positive": 0.5
 },
 "t2-sdxl-busstop/C": {
  "words": 337,
  "clause_coverage": 1.0,
  "has_negative": [
   true,
   true
  ],
  "negative_terms": 52,
  "negations_in_positive": 0
 },
 "t2-sdxl-busstop/B": {
  "words": 276.5,
  "clause_coverage": 0.93,
  "has_negative": [
   true,
   true
  ],
  "negative_terms": 12,
  "negations_in_positive": 0
 },
 "t3-hero-html/A": {
  "words": 20917,
  "clause_coverage": 0.64,
  "backdrop_filter_uses": 7,
  "reduced_motion": [
   true,
   true
  ],
  "bytes": 282223.5
 },
 "t3-hero-html/C": {
  "words": 3165,
  "clause_coverage": 0.86,
  "backdrop_filter_uses": 11,
  "reduced_motion": [
   true,
   true
  ],
  "bytes": 40887
 },
 "t3-hero-html/B": {
  "words": 18445.5,
  "clause_coverage": 0.86,
  "backdrop_filter_uses": 7,
  "reduced_motion": [
   true,
   true
  ],
  "bytes": 172726.5
 },
 "t4-diagnose-render/A": {
  "words": 1782,
  "clause_coverage": 1.0,
  "list_items": 39
 },
 "t4-diagnose-render/C": {
  "words": 1875,
  "clause_coverage": 0.93,
  "list_items": 40
 },
 "t4-diagnose-render/B": {
  "words": 2544.5,
  "clause_coverage": 1.0,
  "list_items": 43
 }
}
```

## What it means (read this before the averages)

**Headline:** the metadump arm (B) scored best overall (7.12 vs 6.75 prompt-only vs 6.44 hand-made file), won the head-to-heads (59% vs prompt-only, 61% vs the hand-made file), and was clearly best at avoiding mistakes ("pitfalls avoided" 7.38 vs 5.94 / 6.38). It won 2 of 4 tasks outright and lost 2.

**How much to trust it:** not much per task. Judge agreement was low (Pearson r = 0.24; the two judges differed by 1.5 points on average), and each cell is only 2 runs x 2 judges. Treat per-task differences under ~1.5 points as noise. The clearest signals:

| task | result | why (from the judges' notes) |
|---|---|---|
| SDXL bus stop | **B +1.75 over A** | B wrote a 12-term negative prompt; A and C wrote 49-52 term dumps of everything. B's positives were tighter and on-brief. |
| render diagnosis | **B +1.5 over A, +1.0 over C** | the dump's optics entries (thickness tint, transmission, blue-white bloom without haze) gave correct, prioritized fixes. |
| FLUX headphones | A +0.75 over B (noise range) | B's prompts were terse (132-191 words vs 229-292) because exports.md capped image prompts at ~120 words. FLUX.2 handles long prompts; the cap is wrong for it. |
| Tide hero page | **C +2.0 over B** | B followed the dump toward high-key: pale sky, navy type, very legible. Judges read that as "washed out, less Aero". The dump records the tension "overexposed yet saturated", and B resolved it to one pole instead of keeping both. C's file pushed saturated sky, PVC and caustics hard, and won here. |

**The hand-made file (C) helped on the web page and hurt on the image prompts.** On FLUX and SDXL it drifted to cyan/aqua, frosted silicone and naming the Windows XP Bliss wallpaper, because those appear in it as plain keywords with no scope or anti-keywords. That is the failure scoped anti-keywords and provenance are meant to stop, and B didn't make it.

**Cost:** B costs about 60% more tokens per run (158K vs 97K) and 70% more time (430 s vs 251 s), mostly from 21 tool calls reading the dump vs 5 for prompt-only. About 74K of every run is the session's system prompt, so the dump's own overhead is roughly 60K tokens per task.

## Fixes this test points at

1. **exports.md:** drop the ~120-word cap for FLUX.2, gpt-image and Gemini (they reward long, detailed prompts); keep short prompts only for CLIP-limited models (SD 1.x/SDXL ~77 tokens per chunk, Midjourney).
2. **use.md + SKILL.md:** keep both poles of every `essence.tensions` entry (e.g. "overexposed yet saturated"); never resolve a tension to one side. Proposed/inferred parameters (like an accessibility-safe palette) are adaptable and may not override tier-1 user_stated qualities: find a design that satisfies both.
3. **use mode cost:** consumers made ~21 tool calls. Point them at `routing[0]` + one route + exports first and stop there unless a check fails.

## Files

`runs/` raw outputs · `blind/` what judges saw · `key.json` unblinding map · `judgments/` raw judge JSON · `metrics.json` objective metrics · `timing.jsonl` tokens/time per run · `shots/` hero renders and `t3-contact-sheet.png` · `impeccable-hook-findings.jsonl` design-hook side data (hero files, attribution unknown) · `metrics.py`, `blind.py`, `aggregate.py`, `render.sh` to rerun.

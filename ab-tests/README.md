# A/B tests

Does a meta dump make downstream work better? Each test builds the same brief with and without a dump and has blind graders score the results, with labels shuffled so no grader knows which arm a build came from.

- **A**: prompt only
- **B**: prompt + a lite meta dump built by the plugin version named, read the way use mode describes
- **C** (the first two tests only): prompt + the hand-made luminous metadata file from before the skill existed

| Test | Builders / graders | Task | A | C | B | B vs A win rate | Grader agreement |
|---|---|---|---|---|---|---|---|
| [2026-11-04-luminous](2026-11-04-luminous/results.md) | Opus 5.5 / Opus 5.5, 2 graders | FLUX prompt, SDXL prompt, landing hero, render diagnosis (24 runs) | 6.75 | 6.44 | **7.12** | 0.59 | r = 0.24 |
| [2026-11-04-player-haiku](2026-11-04-player-haiku/results.md) | Haiku 5.5 medium / Haiku 5.5 medium, 3 graders | working mini music player (12 runs, all functional) | **6.42** | 5.33 | 5.58 | 0.29 | r = 0.63 |
| [2026-11-04-shop-haiku](2026-11-04-shop-haiku/results.md) | Haiku 5.5 for everything (dump build, builders, 3 graders), metadump 0.3.0 | compact shopping component (8 runs, all functional) | **7.04** | – | 6.33 | 0.29 | r = −0.09 (v2) |
| [2026-11-04-shop-haiku-v4](2026-11-04-shop-haiku-v4/design.md) | metadump 0.4.0 | the same shopping component | – | – | – | – | stopped before results |
| [2026-11-04-shop-haiku-v5](2026-11-04-shop-haiku-v5/results.md) | Haiku 5.5 for everything, metadump 0.5.0 (from scratch) | the same shopping component (8 runs, all functional) | 5.58 | – | **7.17** | **0.83** | r = 0.67 |
| [2026-11-04-shop-haiku-v6](2026-11-04-shop-haiku-v6/results.md) | Haiku 5.5 for everything, metadump 0.5.1 (from scratch) | the same shopping component (8 runs, all functional) | 6.42 | – | **7.50** | 0.75 | r = 0.60 |

Scores are 0–10 means across graders. The win rate counts every A×B pair the same grader scored in the same block.

## What the tests showed

- **Correct, specific knowledge helps.** Where the dump carried facts the model wouldn't have (SDXL negative-prompt behavior, the optics behind a bad render), B clearly won.
- **A wrong concrete value hurts, and the smaller model follows it.** In the music-player test, the dump's pale web tokens contradicted its own "color inside the material". Haiku followed the numbers over the prose and over the user's intent, and B lost. That led to ADR 0003: the dump is a resource, not a rulebook.
- **A dump that narrows the request hurts too.** In the first shopping test (0.3.0), the dump's own inferred entries said "compact" meant one product and nothing else, and it was mostly the build's guesses (16% collected, one source site). Every B build was a bare card with no cart, and B lost. That led to ADR 0005 (seed, don't narrow) and ADR 0006 (identify the task, ladder it from discipline to specifics, distill references).
- **After those fixes, the dump arm wins.** On 0.5.0 and 0.5.1, B won 83% and 75% of head-to-head pairs. Its dumps were wider (189 to 195 entries, sources from 8 to 13 websites, a task ladder, every reading kept). On 0.5.1 every B build covered the whole shopping job (variants, quantity, add, a bag to review, checkout), and B also beat A on usability (8.25 vs 7.0).
- **The meta dump beat the hand-made file** in both tests that had one (61% and 54% head to head). Scoped anti-keywords and provenance stopped the drift to cyan, aqua and frosted glass that the hand-made file caused.

## Caveats

- Small n: 4 runs per arm in the shopping tests, where the smallest possible two-sided p is 0.029. The 0.5.x results (p = 0.086 and 0.114) show a direction, not a settled result.
- One task per test, LLM graders, and one lite dump build per test.
- Each shopping test after test 3 rebuilt A from scratch, so A's quality varies from run to run (test 5's A had a CSS bug in one run).
- Fixed harness bugs, documented in each results file: cropped phone screenshots in test 3's first grading round, and a click test that read button labels after clicking in test 6.
- The impeccable design hook fired inside builder sessions in the first two tests; it applied to all arms alike.

## Not in this folder

- **Moodboard images:** screenshots and images of third-party sites, so they aren't published here. The dumps keep their sources and links.
- **The `blind/` copies:** regenerate them with each test's `blind.py`; `key.json` maps the labels back to runs.

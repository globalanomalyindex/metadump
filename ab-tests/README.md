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
| [2026-11-05-shop-haiku-v7](2026-11-05-shop-haiku-v7/results.md) | Haiku 5.5 for everything, a one-agent build (scrapped, never shipped) | the same shopping component (8 runs, all functional) | 6.17 | – | **6.92** | 0.69 | r = 0.60 |
| [2026-11-05-curves-haiku](2026-11-05-curves-haiku/results.md) | Haiku 5.5 for everything, metadump 0.7.0 (facets) | three "sticky and punchy" bezier curves as loops (8 runs, 7 working) | 4.83 (6.11 without its broken run) | – | **6.17** | 0.58 | r = 0.68 |
| [2026-11-05-curves-haiku-v2](2026-11-05-curves-haiku-v2/results.md) | Haiku 5.5 for everything, metadump 0.7.0 with ADR 0010 (rerun of test 8) | the same curves task (8 runs, all working) | 4.50 | – | **7.67** | **1.0** | r = 0.96 |
| [2026-11-05-four-tasks-haiku-low](2026-11-05-four-tasks-haiku-low/results.md) | Haiku 5.5 at **low effort** for everything (dumps, builders, graders), metadump 0.7.1 | four tasks, 32 runs: dreamlike button 6.42 vs **7.08**, physics sandbox 6.33 vs **6.83**, rare-cloud poem 5.17 vs **7.92**, Figma-style loop **5.67** vs 5.42 | 5.90 (mean of the four) | – | **6.81** | 0.70 | r = 0.20 to 0.88 |
| [2026-11-05-three-tasks-haiku-medium](2026-11-05-three-tasks-haiku-medium/results.md) | Haiku 5.5 at **medium effort** for everything, metadump 0.8.0 (ADR 0012, working tree) | three tasks, 24 runs: dreamlike button 6.58 vs **7.33**, rare-cloud haiku **7.42** vs 6.58, dark package toast 5.00 vs **8.58** | 6.33 (mean of the three) | – | **7.50** | 0.69 | r = 0.25 to 0.94 |
| [2026-11-05-three-tasks-haiku-medium-v2](2026-11-05-three-tasks-haiku-medium-v2/writeup.md) | Haiku 5.5 at medium effort for everything, metadump 0.8.1 (ADR 0013, spreads, not settings) | the same three tasks, 24 runs: button 6.58 vs **7.08**, haiku **7.42** vs 7.00, toast 6.08 vs **8.08** | 6.69 (mean of the three) | – | **7.39** | 0.64 | r = 0.41 to 0.76 |
| [2026-11-05-three-tasks-haiku-medium-v3](2026-11-05-three-tasks-haiku-medium-v3/writeup.md) | Haiku 5.5 at medium effort, metadump 0.9.0 (ADR 0014, the deal); test 13's dumps and A builds reused | the same three tasks, 12 new B runs: button 6.75 vs **7.00**, haiku **7.00** vs 6.50, toast 6.50 vs **8.08** | 6.75 (mean of the three) | – | **7.19** | 0.65 | r = 0.29 to 0.86 |
| [2026-11-05-three-tasks-sonnet-medium](2026-11-05-three-tasks-sonnet-medium/writeup.md) | **Sonnet 5.5** at medium effort (builders and graders; dumps are test 13's, Haiku-built), metadump 0.10.0 (ADR 0015, a hand, not the deck) | the same three tasks, 24 runs: button **7.83** vs 6.42, haiku 5.42 vs **7.75**, toast 7.33 vs 7.33 | 6.86 (mean of the three) | – | 7.17 | 0.49 | r = 0.74 to 0.87 |
| [2026-11-05-three-tasks-sonnet-medium-v2](2026-11-05-three-tasks-sonnet-medium-v2/writeup.md) | Sonnet 5.5 at medium (builders and graders), metadump 0.11.0 (ADR 0016, amplify the user's words), dumps rebuilt by the Haiku swarm; A reused from test 15 | the same three tasks, 12 new B runs: button **7.50** vs 7.33, haiku 5.33 vs **7.00**, toast **7.96** vs 5.83 | 6.93 (mean of the three) | – | 6.72 | 0.42 | r = 0.79 to 0.91 |
| [2026-11-05-three-tasks-sonnet-0.8.0](2026-11-05-three-tasks-sonnet-0.8.0/writeup.md) | Sonnet 5.5 at medium (builders and graders), **metadump 0.8.0** restored (ADR 0017), test 12's dumps | the same three tasks, 24 fresh runs: button **8.08** vs 5.75, haiku 5.25 vs **7.50**, toast **7.33** vs 6.62 | 6.89 (mean of the three) | – | 6.62 | 0.42 | r = 0.13 to 0.80 |
| [2026-11-05-three-tasks-sonnet-medium-v3](2026-11-05-three-tasks-sonnet-medium-v3/writeup.md) | Sonnet 5.5 at medium (builders and graders), **metadump 0.12.0** (0.11.0 plus the look, ADR 0018); test 16's dumps and prompt-only builds reused | the same three tasks, 12 new B runs: button 6.50 vs **8.25**, haiku 5.08 vs **8.00**, toast 6.83 vs **7.50** | 6.14 (mean of the three) | – | **7.92** | **0.84** | r = 0.79 to 0.90 |

Scores are 0–10 means across graders. The win rate counts every A×B pair the same grader scored in the same block.

## What the tests showed

- **Correct, specific knowledge helps.** Where the dump carried facts the model wouldn't have (SDXL negative-prompt behavior, the optics behind a bad render), B clearly won.
- **A wrong concrete value hurts, and the smaller model follows it.** In the music-player test, the dump's pale web tokens contradicted its own "color inside the material". Haiku followed the numbers over the prose and over the user's intent, and B lost. That led to ADR 0003: the dump is a resource, not a rulebook.
- **A dump that narrows the request hurts too.** In the first shopping test (0.3.0), the dump's own inferred entries said "compact" meant one product and nothing else, and it was mostly the build's guesses (16% collected, one source site). Every B build was a bare card with no cart, and B lost. That led to ADR 0005 (seed, don't narrow) and ADR 0006 (identify the task, ladder it from discipline to specifics, distill references).
- **After those fixes, the dump arm wins.** On 0.5.0 and 0.5.1, B won 83% and 75% of head-to-head pairs. Its dumps were wider (189 to 195 entries, sources from 8 to 13 websites, a task ladder, every reading kept). On 0.5.1 every B build covered the whole shopping job (variants, quantity, add, a bag to review, checkout), and B also beat A on usability (8.25 vs 7.0).
- **One agent is fast but narrows (test 7).** A single-agent build took 2.7 minutes instead of 32. Its dump dropped the bag review and checkout from the default reading, and B's usability fell below A's again, so that version was scrapped.
- **A dump that hands over one answer gets copied (test 8).** The curves dump defined "sticky" and "punchy" itself, then proposed one concrete set of three curves. All four B builds used it, so B's curves were near-identical (distinct 3.83 vs 6.67) and no more sticky or punchy than A's. B won presentation and craft by a wide margin, and only beat A overall because one A build was broken. 0.7.0 now keeps every reading of a quality word side by side, never proposes the deliverable itself, and has verify look for both (ADR 0010).
- **With those fixes, the dump arm won every pairing (test 9).** On the rerun, B scored 7.67 vs 4.50 and won all 24 head-to-head pairs (p = 0.029, the smallest possible at n = 4). It led every criterion, including distinct (7.08 vs 6.0). None of B's 12 curves was copied from the dump, and all 12 were different. Part of the gap is a weaker A arm than in test 8.
- **Across four new tasks at the cheapest settings, the dump arm was ahead on three (test 11).**
  - Every agent ran on Haiku at low effort, dumps included. Pooled, B won 61 of 96 head-to-heads, and an exact stratified permutation test gives p = 0.024.
  - The poem carries that result on its own: 23 of 24 head-to-heads, p = 0.029. Without the poem, the other three tasks lean B (+0.31 points) but give p = 0.45.
  - On the Figma-style loop, every prompt-only build rebuilt Figma's logo or came close, and no dump build did. B still lost that task narrowly, on motion and one CSS bug.
  - The test also turned up a milder form of test 8's copying. All four dump poems chose the same cloud (nacreous), following a "choose one formation" line in the dump's brief, and the dump's Figma builds shared motifs.
- **Material to play with, not orders (test 12, 0.8.0).**
  - After test 11's convergence, 0.8.0 made the dump talk differently. Its head offers several angles instead of one recipe, values are dials, pools have no order, and nothing in it but the user's words is an instruction (ADR 0012).
  - The dump side won the toast 24 of 24 (p = 0.029), led the button (7.33 vs 6.58) and lost the haiku (6.58 vs 7.42). Pooled, it won 45 of 72, p = 0.045.
  - Variety graders rated the dump side more varied on the button and the haiku and even on the toast. The dump haiku used four different rare clouds, while the prompt-only haiku mostly converged on nacreous.
  - Two failures remain. All four dump buttons pasted the four curves from the dump's CSS export (test 8's copying, through an export). And the dump offered "5-7-5 or short-long-short" as a dial, so three of four dump haiku dropped 5-7-5 and lost on form (5.58 vs 9.42). The user's own words carry their conventions, and a dial must not loosen them.
- **Spreads instead of settings fixed form and copying, but not sameness (test 13, 0.8.1).**
  - 0.8.1 showed every value as a spread (ADR 0013). Three of four dump haiku kept 5-7-5, and the dump buttons copied fewer values (2.5 per build, down from 4.25).
  - The dump side won the toast 21–0–3 (p = 0.029) and led the button. Pooled p = 0.087.
  - The prompt-only side was rated more varied on all three tasks: the dump builds started from whatever the dump listed first.
- **Dealing the dump didn't make the builds vary (test 14, 0.9.0).**
  - 0.9.0's use mode deals the dump first: a random hand and a reshuffled copy (ADR 0014). Only 5 of 12 builders dealt. The other seven opened the dump at the same time as SKILL.md and never went back to the deal.
  - All four toast builders dealt and got different hands, and their toasts still came out near-identical. Variety: prompt-only 5.67, dump 3.67.
  - Every dump button used the same two curves from the dump. The dump side still won the toast 21–1–2 (p = 0.029); pooled p = 0.29.
  - The lesson: order wasn't the lever. Every session reads all of the same material and converges on its strongest shape. 0.9.1 puts the deal at the top of every dump. Whether each session should get only part of the deck is the next open question.
- **A hand instead of the whole deck (test 15, 0.10.0, Sonnet 5.5).**
  - Each session now gets the user's words, tier 1, worn paths and review questions, plus a random half of the rest (ADR 0015). All 12 builders dealt.
  - The dump side was more varied on two of three tasks for the first time since test 12. It won the haiku 21–1–2: the prompt-only haiku were the same nacreous poem four times (variety 1.33 vs 5.33), and all four dump haiku were 5-7-5.
  - It lost the button 1–21–2. The dump's worn paths swap every classic dreamlike move for a tamer one, and a hand keeps all of them while halving the rest. The dump buttons came out practical and quiet (dreamlike 6.17 vs 8.25).
  - The toast tied, 7.33 each: Sonnet's prompt-only toasts are much stronger than Haiku's. Pooled p = 0.55.
- **Amplifying the user's words (test 16, 0.11.0, dumps rebuilt).**
  - 0.11.0 stops the build from calling a quality's own moves worn paths (ADR 0016). The rebuilt button dump's worn paths now ask for more glow, not less, and no dump has a tamed `instead`.
  - The dump side was more varied on all three tasks for the first time (8 of 9 variety graders).
  - The button went from 1–21–2 to 9–12–3 (7.33 vs 7.50), and the single best button was a dump build. Two dump buttons still came out quiet (a cold glow on a dark page).
  - The haiku won 18–6. The toast lost 0–21–3 on craft: every dump toast packed more into a compact pill and shipped clipping and overlap no builder looked for. Pooled p = 0.72.
- **Back to 0.8.0, retested on Sonnet (test 17).**
  - None of 0.8.1 to 0.11.0 beat 0.8.0's test 12 result, so the plugin went back to 0.8.0 (ADR 0017) and was retested with Sonnet 5.5.
  - The haiku won 20–2–2. The button lost 0–23–1: all four dump buttons reused the dump's curves and came out "polite rather than dreamlike". The toast lost 8–15–1. Pooled p = 0.65.
  - Across tests 15 to 17, no version beats Sonnet's prompt-only builds overall on these tasks, and every version wins the haiku by a wide margin. On Haiku builders (tests 12 to 14) the dump side won overall every time.
- **Look at what you built (test 18, 0.12.0).**
  - Use mode ends with `look.py`: a headless render, screenshots at desktop and phone widths, a hover and a click, and a list of clipping, overlap and overflow for the builder to read (ADR 0018). All 8 UI builders ran it; five edited between looks.
  - With test 16's dumps and prompt-only builds unchanged, the dump side went from 27–39–6 to **57–8–7** (p = 0.0002): button 23–0–1, haiku 23–1–0, toast 11–7–6. All nine variety graders picked the dump side.
  - The button graders' words went from "quiet" and "barely reads as ethereal" to "pointer-following bloom" and "aurora halo". The toast's craft score went from 5.17 to 7.58.
  - Caveat: graders score within a block of four, so the prompt-only side's absolute scores fell when the dump side stopped breaking; the head-to-heads are the comparison that holds.
- **The meta dump beat the hand-made file** in both tests that had one (61% and 54% head to head). Scoped anti-keywords and provenance stopped the drift to cyan, aqua and frosted glass that the hand-made file caused.

## Caveats

- Small n: 4 runs per arm in the shopping tests, where the smallest possible two-sided p is 0.029. The 0.5.x results (p = 0.086 and 0.114) show a direction, not a settled result.
- One task per test (four in test 11), LLM graders, and one lite dump build per task.
- Each shopping test after test 3 rebuilt A from scratch, so A's quality varies from run to run (test 5's A had a CSS bug in one run).
- Fixed harness bugs, documented in each results file:
  - cropped phone screenshots in test 3's first grading round;
  - a click test that read button labels after clicking in test 6;
  - blank loop frame sheets in test 11's first Figma grading round (a `data:` URL over Chrome's 2 MB limit). That round was voided and regraded.
- The impeccable design hook fired inside builder sessions in the first two tests; it applied to all arms alike.

## Not in this folder

- **Moodboard images:** screenshots and images of third-party sites, so they aren't published here. The dumps keep their sources and links.
- **The `blind/` copies:** regenerate them with each test's `blind.py`; `key.json` maps the labels back to runs.

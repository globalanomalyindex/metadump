# A/B test 19: three new tasks on metadump 0.12.0, Sonnet 5.5 at medium

Three tasks the 0.8 to 0.12 line was never tuned on, one per category: an imaginative one ("a recipe for mammoth steak"), a technical one ("a basic tic tac toe game") and a visual one ("a 3D model of a lemon"). Fresh dumps from 0.12.0's create mode on the Haiku swarm, fresh builds on both sides, blind Sonnet graders. Pre-registration: `design.md`. Tables: `results.md`.

## Results

| task | A overall | B overall | B vs A (won–lost–tied) | p | variety A | variety B |
|---|---|---|---|---|---|---|
| recipe | 4.92 | **7.00** | 22–0–2 | 0.029 | **2.17** | 1.67 |
| tic tac toe | 6.50 | **7.67** | 15–5–4 | 0.26 | 2.00 | **5.00** |
| lemon | 5.00 | **6.67** | 17–6–1 | 0.40 | **7.00** | 4.00 |

Pooled: **54 wins, 11 losses, 7 ties** (win rate 0.80; stratified permutation test p = 0.019). Grader agreement r = 0.87, 0.90, 0.95.

## Pre-registered hypotheses

1. **B ≥ A overall on at least 2 of 3 tasks. Yes: 3 of 3.**
2. **Pooled, B wins more than it loses. Yes: 54–11–7.**
3. **B's variety ≥ A's on at least 2 of 3. No: 1 of 3.** The dump games were more varied (all three graders); the dump recipes and lemons were less varied (two of three and three of three graders).
4. **All 12 B builders deal, and at least 7 of the 8 HTML builders run the look. Yes: 12 of 12 dealt, 8 of 8 looked.** The lemon builders looked 4 to 8 times and read 4 to 10 screenshots each; the game builders looked once and read none.
5. **On the game, B's `basic` is not below A's. No:** 7.42 vs 8.08. One dump game (B-r4) added a computer opponent, a scoreboard and a loser-starts rule, and every grader marked it overbuilt.
6. **The technical task is where the dump adds least. Yes:** the lead was 1.17 on the game, 1.67 on the lemon and 2.08 on the recipe.

## What happened

**The recipe won 22–0–2, on everything but variety.** The prompt-only recipes are a pan-seared bison or ribeye with juniper and a one-line "mammoths are extinct" note; graders called them "generic" with "almost no mammoth world". The dump recipes brought the mammoth's actual world: the Yuka carcass, sled dogs fed thawed mammoth, the lab-grown mammoth meatball, Yakutian horse and reindeer as stand-ins, elephant-meat permits. Imagination 6.08 vs 3.08, specificity 7.08 vs 3.17, recipe 8.92 vs 6.75. The cost: they run about 1,350 words against 575, and graders called several "long" or "padded". Three of the four are the same dish (a bone-in bison tomahawk, reverse-seared and carved at the table), which is why the variety score is lower. The dump's thesis is about thickness and its first angle is "the show plate", and the builds followed both.

**The game won 15–5–4 and was the most varied set.** The four prompt-only games are the same cream page with a 3×3 of white cells, a stats line and a dark "New game" button, with cell labels that only say "Cell n", so screen readers never hear the marks. The dump games include a blue full-bleed one, an outlined-glyph one with SVG marks, two plain ones with row and column labels that announce the mark, dark mode and focus rings. The two plain ones (B-r2, B-r3) scored about 9, the best in the test. Usability went from 5.83 to 8.33. Two dump games and two prompt-only games have rows that squash once marks land. The look never caught it, because it hovers and opens a page but never plays it.

**The lemon won 17–6–1, but the best single lemon was a prompt-only one.** Prompt-only A-r3 (9.0 from every grader) has a pointed nub, a stem and leaf, and fine pitting. The other three prompt-only lemons are a pale translucent blob, a glittery speckled egg and a plain egg, and on phones their panels cover the model. The dump lemons are more consistent: two strong ones (8.0, with nub, stem and calyx, pitted peel and a soft shadow), one round egg and one capsule. Presentation 7.42 vs 5.08. They also converge on one layout, a dark backdrop with a right-hand slider sidebar, so the variety graders called the prompt-only set more varied. Part of that variety is the broken builds.

## What it says about 0.12.0

- **Quality carries to new tasks.** Every task went the dump side's way, and pooled it holds (p = 0.019), on tasks the plugin was never tuned on.
- **Variety doesn't always come with it.** Test 18's rebuilt dumps were more varied on all three tasks. Here two of three fresh dumps pulled builds toward one answer: the recipe dump's thesis and first angle, and a lemon template the builders seem to have arrived at independently, since the dump holds no layout. The deal shuffles the angles, but four sessions reading the same strong thesis still land in the same place. This is the convergence from tests 13 and 14 again.
- **The look works when builders look.** The lemon builders, whose output is hard to judge from source, read their screenshots many times. The game builders trusted a clean findings list and never opened the screenshots, and the look can't see a bug that only shows up mid-game.
- **"Basic" was mostly amplified, not ignored.** Three of four dump games stayed basic; one overbuilt.

## Cost

| task | A tokens / time per build | B tokens / time per build | dump |
|---|---|---|---|
| recipe | 70k / 15 s | 111k / 50 s | 193k reported by the main loop, 31 min, 20 agents |
| tic tac toe | 75k / 15 s | 100k / 40 s | 202k, 27 min, 18 agents |
| lemon | 92k / 2.0 min | 147k / 5.7 min | 217k, 27 min, 22 agents |

## Caveats

- n = 4 per arm per task, one dump per task (Haiku-built while the builders are Sonnet), LLM graders.
- The look is part of the dump arm's use mode only.
- The lemon renders come from headless Chrome's software WebGL, the same for both arms; a GPU may render the shading differently.
- No libraries were allowed, so every lemon is hand-written WebGL; a real answer might use a library or a model file.
- Test 19 has no earlier baseline for these tasks; compare arm against arm within it.

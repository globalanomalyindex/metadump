# A/B test 16: amplify the user's words (metadump 0.11.0), dumps rebuilt, Sonnet 5.5 at medium

The three dumps were rebuilt from scratch with 0.11.0 (ADR 0016) by the Haiku swarm at medium effort:
- the user's quality moves are material to push further, not worn paths;
- an `instead` goes further;
- "practical" says what has to keep working.

The B builds and all graders are Sonnet 5.5 at medium. A is test 15's prompt-only builds, reused. Pre-registration: `design.md`. Tables: `results.md`.

## Results

| task | A overall | B overall | B vs A (won–lost–tied) | p | variety A | variety B |
|---|---|---|---|---|---|---|
| button | **7.50** | 7.33 | 9–12–3 | 1.0 | 3.00 | **4.33** |
| haiku | 5.33 | **7.00** | 18–6–0 | 0.11 | 1.33 | **6.33** |
| toast | **7.96** | 5.83 | 0–21–3 | 0.029 | 2.33 | **3.83** |

Pooled: 27 wins, 39 losses, 6 ties (p = 0.72). **The dump side was rated more varied on all three tasks**, which no earlier test managed: 8 of 9 variety graders picked it, and the ninth called it a tie.

## Pre-registered hypotheses

1. **No rebuilt dump tames the user's quality. Yes in spirit:** `tamed_instead` is 0 on all three dumps.
   - The button dump still has two worn paths with "glow" in the name, "neon glow" and "faint halo", but both now push toward more: "a glow that spreads visibly past the edge and reaches full strength on hover".
   - 66 of its material entries are about glow, bloom, halo, glass or float.
2. **On the button, B's dreamlike ≥ A's, and B ≥ A overall. No:** dreamlike 6.33 vs 7.92, overall 7.33 vs 7.50. The gap closed from test 15 (6.42 vs 7.83, 1–21–2) to a near tie (9–12–3). The best button of all eight was a dump build (B-r4, 9.0 from every grader: "luminous rim, cloud glow and floating plate").
3. **B ≥ A overall on at least 2 of 3 tasks. No:** the haiku only.
4. **B variety ≥ A on at least 2 of 3. Yes: 3 of 3.**
5. **At least 10 of 12 B builders deal. Yes: 12 of 12.**

## What happened

**The button dump turned around; two of four builds still came out quiet.**
- The 0.11.0 dump gives "dreamlike" readings from a slow float to a surreal drift, and "ethereal" readings from a glow past the edge to an eerie cold glow. Its worn paths now ask for more glow, not less.
- B-r4 and B-r1 used that: a luminous rim and floating plate, a warm glow with a slow drift.
- B-r2 and B-r3 both drew "eerie cold glow" and built moonlight-blue glass on dark navy pages. Graders called them "modest" and "barely reads as ethereal". A cold glow on a dark page is a quiet look even at full strength.

**The haiku won again.** The prompt-only haiku are the same nacreous mother-of-pearl poem four times (variety 1.33). The dump haiku cover:
- a palm shading the sun with an iridescent edge;
- pearl draining out of a nacreous cloud at dusk;
- cold hands catching the colour;
- a wave sky after a storm.

They won freshness 7.25 vs 4.58 and form 9.00 vs 7.33 (three of four are 5-7-5; one opens with six syllables).

**The toast lost on craft, not on ideas.**
- The rebuilt toast dump is richer: multi-parcel stacks, a "now" marker, carrier tabs, notify and snooze actions, failure modes.
- The dump toasts tried to fit more of it into a very compact pill, and none of the builders opened the page to look. All four shipped layout bugs: a timeline clipped mid-row, the close icon over the chevron, action rows wrapping, timestamps stranded under the dots. Craft scored 5.17 vs 7.83.
- Sonnet's prompt-only toasts are simpler and polished. The dump toasts were more varied (3.83 vs 2.33) and led on nothing else.

## Diagnosis

- **Amplifying works at the dump level.** Worn paths that asked for less now ask for more, and builds vary more on every task.
- **More material needs a look at the result.** The dump gives a build more to fit. In a compact UI that shows up as clipping and overlap the builder never saw. Use mode could end with a render check: screenshot the page in a headless browser (the skill ships `cdp.py` and `pixels.py`) and fix clipping or overlap before finishing.
- **One dump per task is a big confound.** Test 15's old toast dump tied with Sonnet, and this rebuilt one lost by two points. Some of that is the dump build's own randomness, not the 0.11.0 rules.

## Caveats

- n = 4 per arm per task, one dump per task (Haiku-built while the builders are Sonnet), LLM graders.
- A is reused from test 15.
- A rebuilt dump changes content as well as voice.
- The impeccable design hook commented on HTML files inside builder sessions in both arms; several B builders reported contrast flags they judged false positives.

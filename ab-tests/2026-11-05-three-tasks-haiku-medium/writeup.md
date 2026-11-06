## Pooled across the three tasks

- B is ahead on 2 of 3 tasks. The mean B−A gap is +1.17 points.
- An exact stratified permutation test gives p = 0.045, two-sided, over 343,000 relabelings within tasks (`pooled.json`).
- B won 45 of 72 blind head-to-heads, lost 18 and tied 9 (win rate 0.69).
- The toast drives most of the pooled result: B won all 24 of its head-to-heads. The button leans B, and the haiku goes to A.

## Variety (the outcome 0.8.0 targets)

| task | variety A | variety B | graders who found B more varied | other measure |
|---|---|---|---|---|
| button | 4.00 | **5.33** | 3 of 3 | curves: all 4 B builds share the same 4 cubic-beziers; A builds share some in pairs (7 distinct curves in A, 8 in B) |
| haiku | 4.00 | **4.67** | 2 of 3 | distinct clouds: A mostly nacreous (3 of 4; the 4th unnamed silver threads), B four types (nacreous, noctilucent, an iridescent edge, lenticular) |
| toast | 4.33 | 4.33 | 2 of 3 | – |

- Variety scores are 0–10, from three Haiku-medium graders per task. Each saw both arms as anonymous sets (`variety.json`).
- In test 11 (0.7.1), all four dump-built poems chose the same cloud. In test 12 the **prompt-only** haiku converge on nacreous, and the dump haiku spread across four clouds. The dump now widens what builds reach for, which is what ADR 0012 set out to do.

## Pre-registered hypotheses

1. **B ≥ A overall on at least 2 of 3 tasks: met** (button, toast).
2. **B's variety ≥ A's on at least 2 of 3 tasks: met** (button higher, haiku higher, toast equal).
3. **B's four haiku name at least 3 distinct cloud types: met** (four).

## What happened, task by task

**Toast (B 8.58 vs A 5.00, 24 wins and 0 losses, p = 0.029, the smallest possible at n = 4).**
- Graders agreed strongly (r = 0.94).
- B led every criterion: compact 8.42 vs 5.42, collapsible 8.92 vs 5.25, tracking 8.67 vs 5.17, usability 8.58 vs 5.50.
- Every B build is a single-parcel panel that starts collapsed (a 38–46 px pill or bar) and opens to a timeline with copy, carrier and dismiss controls.
- Every A build is a multi-package list that starts open, at 238–474 px tall. A-r4 throws a JavaScript error on render.
- All 8 surfaces are dark (luminance about 0.01).
- The dump's angles show up in the B builds: "the glance" (a status word on a pill) and "the ledger" (checkpoint wording).

**Button (B 7.33 vs A 6.58, win rate 0.71, p = 0.29).**
- B's lead is practical (8.42 vs 6.17) and motion (7.92 vs 6.33). A was more dreamlike (7.42 vs 6.58).
- All 8 builds pass the click tests: hover changes, custom curves, reduced motion.
- **The four B builds share the same four curves,** which are exactly the four in the dump's `css-implementation` export. Verify flagged that export as a copy risk in round 1. The widening round can't edit exports and the round-2 synthesis kept it, so it shipped. It is the test-8 failure (ADR 0010) again, through an export.
- Variety graders still rated B more varied (3 of 3), on surface, palette and page context. Measured by curves, though, B copied the dump.

**Haiku (A 7.42 vs B 6.58, win rate 0.35, p = 0.40).**
- The gap is form: 9.42 vs 5.58. All four A haiku are exact 5-7-5. Three of the four B haiku are not (6-8-6, 5-5-6, 5-8-6); the 5-7-5 lenticular haiku B-r4 scored 8.0, the best B run.
- The dump listed form as a dial: "English short-long-short or a 5-7-5 count". The builders took the looser option.
- B was ahead on imagery (7.33 vs 6.92) and freshness (6.50 vs 6.25), and roughly even on specificity and resonance.
- **Lesson:** a dial must never loosen what the user's own word carries. "Haiku" carries its form, the way "toast" carries "transient" and "dark mode" carries dark surfaces.

## The dumps

See `dumps.md` for each dump agent's report.
- Each dump was built by a Haiku-medium main loop with 19–21 Haiku-medium workers.
- Each took 25.6–26.9 minutes of main-loop time and 200–228K main-loop tokens.
- They hold 66–94 entries and 26–31K tokens, about twice the lite target.
- Grounding is 28–35% collected.
- All three heads now open with angles (4, 5 and 4), carry quality facets with 4–5 readings each and no default, and use the new LLM brief blocks. No `directive_voice` or `no_angles` warning survived the final build.
- Verify's new voice pass found `directive` narrowings in every dump. Each dump's widening round cleared some of them, and some remained at lite's one-round cap: the button's export, and the nacreous lean in the haiku brief.

## Follow-ups (not done; for 0.8.1)

1. **Exports must not package a value set as an implementation.** The button's `css-implementation` export carried four curves, and every build pasted them. Two options:
   - finalize could warn when an export holds concrete values drawn mostly from `proposed`/`inferred` entries;
   - a verify `copy` finding against an export could route to that round's synthesis, which owns exports.
2. **The user's own words keep their conventions.** A genre or form word ("haiku", "sonnet", "toast", "dark mode") carries its defining form as part of the request. A dial or reading may vary within it, never loosen it.

## Harness notes

- The toast click test, dark check and variety graders are new in this test. All were pre-registered in `design.md` before any run.
- A-r4 toast threw JavaScript errors in the click test (`works: false`). Graders saw it as built.
- The plugin ran from the working tree (0.8.0, unreleased); nothing was pushed for this test.

## Caveats

- n = 4 per arm per task, one dump per task, and Haiku graders at medium effort.
- Variety graders compared sets of four; they knew they were comparing sets, though not which arm made which.
- Medium effort changes builders, dumps and graders at once relative to test 11, so the two tests aren't a clean before and after for 0.8.0.
- The button's curve copying and the haiku's loosened form are real failures of this dump version, reported above.

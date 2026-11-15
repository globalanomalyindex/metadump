# What 24 tests found

Every mechanism metadump has had, what the A/B tests showed for it, and where it sits in the current version. That version has three depths: quick mode, the default since 1.1.0, where the model about to do the task writes the dump itself in one pass (ADRs 0021 and 0022), and the swarm's full build at `lite` or `heavy`. The tests themselves are in `ab-tests/` (one folder each, with the design written before the runs, the raw grades and a write-up). `ab-tests/README.md` is the log.

## How to read the evidence

Each row says how strong its evidence is.

- **Confirmed:** tested once on tasks the owner named after the skill was frozen, with the analysis fixed first and a threshold set in advance (test 24).
- **Held out:** tested on tasks the change was not written from, against an arm without it.
- **Before and after:** the same tasks rerun after the change, with everything else kept. Stronger when the other arm's builds were reused unchanged.
- **Post hoc:** found by reading results after the fact, such as scores broken down by angle. Suggestive.
- **Not isolated:** it shipped alongside other changes and no test separates it.

Every test has the same limits, listed at the end.

## What earned its place

| mechanism | what the tests showed | strength | in the final version |
|---|---|---|---|
| **Writing out what you know before the task** | The dump arm beat the prompt alone on new tasks in tests 19 (54–11–7), 22 (46–2–0) and 23. In test 23 the model doing the task wrote its own dump in one pass and beat the prompt alone 35–8–5 (p = 0.038). In the confirmation test the one-pass form beat it 65–25–6 (+1.12, p = 0.012), leaning on one task of four, and the swarm's dump beat it 49–23–24 (+0.58, p = 0.036), short of the 0.025 set in advance. | confirmed (the one-pass form); held out, and not confirmed (the swarm's dumps) | both: the full build and quick mode |
| **Looking at what you built** | Test 16 to 18, same dumps and same prompt-only builds: 27–39–6 became 57–8–7. In test 23's first round the look was mentioned but was not a numbered step, and only 3 of 8 builders looked. In test 24 all 32 dump-arm builders looked, and 17 of them changed the page afterwards. | before and after, other arm reused | the last step of use mode; step 3 of quick mode |
| **A size word bounds the build** | `simple` 5.67 to 8.17 (test 21), then `basic` 8.25 against 6.58 on a held-out task (test 22). When the rule sat in the wrong section, `basic` was 7.25 (test 23). | held out | a step of use mode; in quick mode a line of the build step, and what the word rules out goes in the dump |
| **The user's words are never narrowed; cover the whole job** | A dump that read "compact" as one product lost (test 3). Wider dumps that kept every reading won 83% and 75% (tests 5, 6). A dump whose default stopped before checkout put usability below the prompt alone (test 7). | before and after | readings and the whole job in a full dump; two lines in quick mode |
| **Values as ranges, never one setting; never the deliverable itself** | Every dump build copied the dump's one curve set (test 8: 11 of 12 curves). With readings side by side and no proposed answer, none did, and the dump arm won 24 of 24 (test 9). Spreads cut copied values from 4.25 to 2.5 per build (tests 12, 13). | before and after | in both |
| **Anti-keywords whose "instead" goes further** | Worn paths that swapped each dreamlike move for a tamer one lost the button 1–21–2 (test 15). Rewritten to ask for more, 9–12–3 (test 16) and 23–0–1 once builders also looked (test 18). | before and after | in both |
| **A resource, not a rulebook** | A dump with one wrong prescriptive value was obeyed and lost (test 2). A brief that said "choose one formation" produced four poems about the same cloud (test 11). After the head offered material instead of orders, the dump arm won 45 of 72 (test 12). | before and after | in both |
| **Kinds of the thing, the classic first** | Angles that removed a defining part or were camera shots lost (tests 20, 21). Angles that were kinds people make, classic first, won on held-out tasks (test 22). In every task where the most classic angle was built, it scored at or near the top. In test 24 one swarm dump listed five angles of one kind (a block world as a flat grid, five ways): its four builds were the narrowest set of the task and scored with the prompt alone, while quick mode's builders named a side view, a top-down grid and an isometric world and won 24–0–0. | held out for the bundle; post hoc for "classic first" and for test 24's reading | a full dump's angles and the order they are dealt in; a quick dump's `kinds` |
| **Collected facts the model lacks** | Where the dump carried facts the model would not have (how a negative prompt behaves, the optics behind a bad render), it clearly won (test 1). | one early test | the full build's research, scraping and video tools; in quick mode references are read first and kept apart from memory |

## What did not, or not yet

| mechanism | what the tests showed | strength | in the final version |
|---|---|---|---|
| **The swarm:** about twenty workers for research, discovery, scraping, a moodboard, specialists, exclusions, synthesis, verify passes and a widening round | With the same use mode and the same look, the swarm's dump scored 0.54 above a one-pass dump (14–27–7 for the one pass, p = 0.28). It costs about 25 minutes and, on one dump, 2.6 million worker tokens. An earlier one-agent build was weaker (test 7), but that was Haiku writing for Haiku with no look. In the confirmation test the one-pass dump was ahead instead, by 0.54 (p = 0.17) on the registered grades and 0.13 (p = 0.70) on the second grading pass, and each arm won two tasks. | two direct comparisons, opposite directions, neither significant | opt-in since 1.1.0, as `lite` and `heavy`: after test 24 the owner made quick mode the default (ADR 0022). Nothing measured so far shows the swarm's dump doing better than one written in a single pass |
| **Reordering the dump for each session** | All builders who dealt got different orders and built the same toast (test 14). | before and after | still part of the deal; not shown to matter by itself |
| **A hand (half the deck) and deals that rotate** | Sessions sharing one large dump became more varied (tests 15, 20 to 22), and rotation ended the collisions that gave three of four sessions the same angle. Both solve a problem that only a large shared dump has. In test 24 two of 16 sessions dealt with `--no-ledger` (their prompt said to write only one file) and each repeated an angle another session had. | before and after | kept for full dumps. A quick dump is read whole and keeps a `built` list, so a later session takes the next kind |
| **Provenance tiers and ceilings, validation, an index, routes** | Built after a wrong value was obeyed (test 2). They shipped with other changes and were never tested alone. A dump of two thousand tokens fits in context without an index. | not isolated | kept in full dumps. A quick dump has none of them |
| **The look's playing checks** | On 32 past builds they flagged exactly the five games graders had marked for squashed rows, and none of the three steady ones. In tests 20 to 24 no build had a behaviour bug for them to catch, and in test 24 no builder used the 20-second wait (the longest was 6 seconds). | post hoc | kept inside the look. Not yet shown to change an outcome |
| **Variety as a score to win** | Tests 12 to 22 counted any difference between builds as variety. In test 22 the "more varied" set included two lava lamps that read as a fishbowl. | measurement error, found in test 22 | graders are told what a task fixes and what it leaves open, and count breaks separately |

## What we got wrong along the way

- **Independent draws.** Each session drew its angle at random, and three of four often drew the same one. The write-up of test 19 blamed the dump's thesis. The transcripts showed the deal.
- **"Different finished things."** Asked for angles a stranger could tell apart, dumps wrote a snow globe with no base (test 20). Then, asked to keep every part, they wrote camera shots (test 21).
- **A contact sheet instead of the screenshots.** Builders read the small sheet and stopped opening the full-size shots (test 20).
- **A dry run that spent the first deal.** A verify worker dealt a finished dump, which took the classic angle before any real session (test 22).
- **An unnumbered step.** The first one-page skill mentioned the look in a paragraph, and most builders skipped it (test 23).
- **A resumed grader.** After a usage limit, a resumed grader skipped half its evidence. All nine grades of that round were discarded and rerun (test 21).
- **Graders who were not opening the evidence.** Fresh Sonnet graders also skipped it: counted from their transcripts in test 24, they opened 60 to 92% of the pictures and 0 to 28% of the sources in every test from 15 on. With three numbered steps in the prompt, 24 of 24 opened everything, and one task's order changed.
- **Tasks the designer chose.** On tasks the designer picked, the full build led the prompt alone by about two points (test 22). On four tasks the owner named after the freeze it led by 0.58 (test 24).

## Limits that apply to all of it

- **Graders are models,** from the same family as the builders, scoring screenshots, frame strips and source. No human graded anything. From test 15 on they scored without opening all of it (see above); only test 24 has a pass by graders who did.
- **Small samples.** Four builds per arm per task. One dump per task for the swarm's arms.
- **Tasks chosen by the designer** in every test before the confirmation test (test 24, four tasks from the owner), and mostly small self-contained web pages, with some short writing.
- **`lite` dumps only** for the swarm. `heavy`, the bigger swarm (once two depths, `standard` and `deep`), has never been A/B tested.
- **Two builder models.** Haiku 5.5 through test 14, Sonnet 5.5 from test 15. Nothing here says how a stronger or weaker model behaves.
- **Scores do not carry across tests.** Graders score within a block, so only comparisons inside one test hold.

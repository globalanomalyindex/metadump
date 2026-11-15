# Quick mode is one page

**Status, 2026-11-15:** the choice below to keep quick mode opt-in, with the swarm as the default, is replaced by ADR 0022: quick mode is the default from 1.1.0. Everything else here stands.

The plugin began as one request to a model before a task: write a structured JSON file of what you know (keywords in tiers, descriptions, tokens, anti-keywords), branching from the broad disciplines down to the specifics, with the steps, tricks and tests practitioners use. The idea behind it is that a model doesn't know what it knows until it writes it out. By 0.13.0, create mode was a swarm of about twenty workers with discovery, scraping, a moodboard, verify passes and a widening round. A lite dump took about 25 minutes, and one main loop reported 2.6 million tokens across its workers. The owner said it had become "a huge thing with steps and verifications" and asked to return to the roots.

No test had compared the swarm with the original idea done by the model that does the task. Test 7 tried a one-agent build with Haiku writing for Haiku, before the look existed, and it was weaker. Test 23 (`ab-tests/2026-11-13-roots-sonnet/writeup.md`) ran the original idea as a one-page skill on two tasks, with the same builder and the same look:

- It beat the prompt alone 35–8–5 (p = 0.038), about 70% of 0.13.0's gain, with no dump build.
- It trailed 0.13.0 with the swarm's dump 14–27–7 (p = 0.28): close on the lava lamp (7.25 against 7.58), behind on the calculator (7.75 against 8.50).
- The gap was in two places. Its calculators overbuilt against "basic", and two of its lava lamps ran down within seconds, which no look shows at load.
- In a first round, where the page mentioned the look in a paragraph, three of eight builders looked. As a numbered step, all eight did.

We decided:
- **Quick mode is the lightest depth, below `lite`.** The model about to do the task writes the dump itself in one pass and works from it (`references/quick.md`). No agents, about a minute.
- **It is opt-in.** The user asks for quick, fast or light. The default is unchanged: the full build, which scored higher in the one direct comparison. This was the owner's call.
- **It stays one page.** It carries the lessons of tests 2 to 22 as one line each (the user's words are never narrowed, cover the whole job, values as ranges, an instead that goes further, kinds with the classic first, a resource and not a rulebook), and what test 23 showed it lacked: what a size word rules out, written into the dump, and the size word as a line of the build step. A line is added only when a test shows it earns its place.
- **Steps that must happen are numbered.** The look is step 3.
- **Let it run.** For anything that keeps moving on its own, the builder looks once more after twenty seconds (`--play "wait 20000"`). Six lava lamps across tests 22 and 23 looked right at load and had run down within ten seconds. Run on the one graders marked hardest for it, the twenty-second look shows all the wax in one mass under the cap and nothing travelling. Use mode says the same.
- **A quick dump is its own small shape.** It opens with `request` and has no manifest, routes or index, and it is read whole. `deal.py` recognises one, says there is nothing to deal, and names the kind to build: the first one not in the dump's `built` list. `finalize.py check` reports what it holds and fails one that has lost the user's request. Both crashed on a quick dump before.
- **Rotation without a ledger.** A session adds the kind it built to `built`, and the next session takes the next kind. The dump is the user's own small file, so the record lives in it.

We rejected:
- replacing the swarm with the one page: the one direct comparison favours the swarm's dump, and the owner wants the latest full version as the default;
- making quick the default: it trailed 14–27–7;
- giving a quick dump the full schema (manifest, tiers per entry, provenance, routes): that is the weight the mode exists to shed, and a file of two thousand tokens needs no index;
- a separate skill for it: one skill with one more depth is less to learn.

## Consequences

- A user can have a meta dump in a minute, and the plugin's simplest path is again the idea it started from.
- Two shapes of dump exist. Tools that take a dump say which they were given instead of failing.
- Quick mode has been tested on two tasks, chosen before it was written but known to its author. The confirmation test runs it on tasks chosen by the owner after the skill is frozen.
- Not tested: a quick dump reused across sessions with `built`, and quick mode with references.

## What the confirmation test found (test 24, 2026-11-15)

Run on the frozen 1.0.0, on four tasks the owner named after the freeze (`ab-tests/2026-11-13-confirmation-sonnet/writeup.md`).

- **Confirmed against the prompt alone:** 65–25–6, +1.12 points, p = 0.012 against a threshold of 0.025 set in advance. The result leans on one task (a block world, 24–0–0); on the other three it is +0.55, p = 0.23.
- **All 16 builders wrote the dump first and all 16 looked.** Thirteen ran a scripted play. None was refused a tool.
- **The dumps came out at 1.0 to 1.9 thousand tokens,** under the 2 to 4 thousand the page asks for. Nothing measured says which size is right, so the page is unchanged.
- **Against the full build it was ahead, not behind:** +0.54 (p = 0.17) on the registered grades, +0.13 (p = 0.70) on a second pass by graders who opened every file. The first rejected option above rested on test 23's direction, which this test did not repeat. The default is still the owner's call.
- **Where it was weak:** it builds the classic kind first, so when the classic is obvious four sessions make the same thing as the prompt alone does (a pelican on a bike: 7.25 against 7.17; a bento menu: 6.82 against 7.50).
- Still not tested: a quick dump reused across sessions with `built`, and quick mode with references.

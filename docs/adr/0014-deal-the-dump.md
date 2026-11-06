# Deal the dump: real randomness decides where each session starts


A/B test 13 (`ab-tests/2026-11-05-three-tasks-haiku-medium-v2/results.md`) ran 0.8.1 (ADR 0013, spreads, not settings). It fixed what test 12 found:
- the dump haiku kept the user's 5-7-5 form (3 of 4, up from 1);
- the dump buttons copied fewer of the dump's values verbatim (2.5 per build, down from 4.25).

The dump side won the toast 21–0 and led the button. But the prompt-only side was rated more varied on all three tasks, because the dump builds converged on whatever came first:
- three of four dump haiku took the first angle (a lenticular cloud over a ridge);
- all four dump buttons used the first two curves of the dump's spreads, in two identical pairs;
- each dump toast reused 7–8 of the dump's colours.

A JSON file has a first item. Every session reads the same dump in the same order, and a model reading top to bottom starts from the top. ADR 0012 told the model that order means nothing. 0.8.0 told it to roll a dice when torn. Across tests 12 and 13, no builder ever did. What the builders reliably did was run the commands use mode prints.

The owner's aim: the dump should be used for more areas of exploration, not adhered to.

We decided:
- **Use mode's first step is a deal.** `scripts/deal.py <dump>` (stdlib, seam S13) does two things.
  - It writes a **dealt copy**: the same dump with every entry at the same pointer, but with its angles, scope readings, task-section entries, quality readings and illustrative spreads in a fresh random order. Measured and sourced values keep their order; they're facts.
  - It prints the **hand**: an angle to start from and two deep cuts from the task sections' outer tiers, all chosen by `random.SystemRandom`.
  - The session reads the dealt copy from then on. Write-backs still go to the original.
- **The randomness lives outside the model.** The deal is a printed command, the one lever the builders followed. It replaces "roll a dice when torn" as the main mechanism; that line stays for single choices.
- **The hand is a place to start, not a rule.** It says so in its own output. A session may follow the hand, combine it with something else, or leave it.

We rejected:
- shuffling at build time, because every session would still read the same order;
- more instructions about order, because tests 12 and 13 show they are read and not acted on;
- hiding the angles or showing one at a time, because the dump would then hold back material instead of putting more of it on the table;
- seeding the deal from the prompt or the dump, because every session would get the same hand. Only a seed in tests is fixed.

## Consequences

- Two sessions reading the same dump start from different corners of it. The set of material doesn't change, only where each session starts and what it meets first.
- A user who reruns a task gets a different take each time, which is the point. A user who wants one particular angle can still pick it.
- Test 14 checks this with the same tasks, the same graders and the same variety and copying measures.

## What test 14 found (2026-11-05)

- Only 5 of 12 builders dealt. The other seven opened the dump in the same batch as SKILL.md and never went back to the deal. 0.9.1 makes the deal the first field of every dump's manifest and the first step of `how_to_read`.
- All four toast builders dealt and got different hands, and their toasts still came out near-identical (variety: prompt-only 5.67, dump 3.67). The order a session reads the dump in was not the lever: every session still reads all of the same material and converges on its strongest shape.
- Still open: should each session get only part of the deck? This decision rejected that ("hold back material"), so changing it needs its own decision.

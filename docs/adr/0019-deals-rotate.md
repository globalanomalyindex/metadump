# Deals rotate

A/B test 19 (`ab-tests/2026-11-05-recipe-game-lemon-sonnet/writeup.md`) found the dump side less varied on two of three tasks: three of the four mammoth recipes were the same bone-in tomahawk. The write-up blamed the dump's thesis. The builders' transcripts say otherwise. Each session's hand names an angle to start from, and across tests 18 and 19 the dealt angles were:

| task | angles in the dump | angles the four sessions were dealt |
|---|---|---|
| recipe | 4 | the show plate ×3, the ice-age table |
| tic tac toe | 2 | the solved game ×2, the nine-cell round ×2 |
| lemon | 5 | size first ×3, close skin |
| button | 4 | one breath at rest ×3, the settle |
| haiku | 5 | the last colour ×3, the name as image |
| toast | 5 | timeline as the body ×2, parcels stacked, read at arm's length |

The three sessions dealt "the show plate" wrote the three tomahawks, and the one dealt "the ice-age table" wrote the other recipe. So sessions follow their angle, and the sameness came from the deal. `deal.py` is unbiased (1,500 deals per dump land evenly), but every session drew independently, and four independent draws from four angles are all different only 9% of the time (24 of 256); from five angles, 19%. ADR 0014 moved the choice of a starting place out of the model. It did not stop sessions from being handed the same one.

We decided:
- **Deals from one dump are drawn without replacement.** `deal.py` keeps a small ledger beside the dump (`.deals/<slug>.deals.json`) with how often each angle, entry, worn path and deep cut has been dealt. Every draw takes what has been dealt least. Ties break at random for entries, worn paths and deep cuts, and in the dump's own order for angles (see "What test 21 found"). Four sessions sharing a dump start from four different angles, and a fifth starts the second round.
- **Hands are complementary.** The half of each section a hand keeps (ADR 0015) is the least-dealt half, so the next hand holds what this one left out, and two hands cover the whole section between them. The same goes for the dump's own worn paths (ADR 0016) and for deep cuts.
- **One deal at a time.** Sessions started together would all read the same ledger, so a deal holds a lock file while it reads, deals and writes. A deal waits up to ten seconds for another to finish, takes over a lock older than thirty seconds, and deals independently if it can't get the ledger at all (a read-only folder, say).
- **The hand says so.** It prints which deal it is and that other sessions start from the dump's other angles, and that an angle is a kind of the thing while the request stays as the user wrote it. Nothing in it becomes a rule (ADR 0012).
- **A dump needs a round of angles, and every one has to be sound.** Finalize warns `few_angles` below four, and synthesis writes four to six. Rotation builds every angle, so an angle is a kind of the thing that people make: it varies what the request leaves open (the subject or scene, the style, the era, the palette, the mood) and keeps what makes the thing itself (every signature item, every step of the job, the named thing as the main thing). It is not a shot (a camera position, a lighting effect, a moment caught). It is not an order of work: three lemon sessions dealt "size first" and one dealt "close skin" could not have come out different. It stays inside the user's words and never grows the job past a size word such as "basic". Verify checks each angle against this (the angle pass).
- **A seeded deal keeps no ledger**, so it stays repeatable for tests. `--no-ledger` deals independently, and `--ledger PATH` names another file.

We rejected:
- dealing the angle from a session id or the clock, because sessions have no shared numbering, and independent draws are what failed;
- hiding the other angles from the dealt copy, because sessions already follow their own, and the others are material to combine with;
- rolling each decision point as well, because a rolled choice can step outside the default reading ("a wedge" for "a 3D model of a lemon"), and one change at a time keeps the next test readable;
- keeping the ledger inside the dump, because the dump is never changed by a deal (ADR 0014) and write-backs would race.

## What test 20 found (2026-11-12)

The first version of this decision asked for angles that were "different finished things" and had the hand say that the further a session took its angle, the more ground the sessions covered. Test 20 (`ab-tests/2026-11-12-three-arms-sonnet/writeup.md`) ran it against 0.12.0 on the same dumps.

- **Rotation worked.** Four sessions started from four angles on all three tasks (0.12.0's independent deals gave 3, 4 and 2), and variety went from 3.67, 4.67 and 4.0 to 5.33, 8.33 and 8.33.
- **Quality fell on both HTML tasks** (pooled 17–46–9 against 0.12.0). The dumps had written angles that removed what makes the thing itself: a snow globe with no base, one with no scene, a timer whose session count is bigger than its clock. Rotation built every one of them, and the hand's wording pushed sessions further out. 0.12.0's snow globe sessions had drawn only the two safest angles.

So the mechanism stays and the two sentences changed: what an angle is, and what the hand says about it. Test 21 checks the revision.

## What test 21 found (2026-11-13)

Test 21 (`ab-tests/2026-11-12-revision-sonnet/writeup.md`) reran the timer and the snow globe with angles rewritten as "different treatments that keep everything the request names".

- **The timer recovered.** 7.54 against 0.12.0's 7.21 (15–6–3), with `simple` up from 5.67 to 8.17. Its angles were kinds of timer face that people ship: a ring that fills, a full-bleed phase colour, a pause held between phases.
- **The snow globe did not.** 6.08 against 7.25 (3–20–1). Every build was a snow globe again, and every one was drawn worse than the plain globes beside it. The dump was built from photographs, and its angles were photographs: a close-up, a view across a room, one colour cast, a long exposure. None is a kind of snow globe anyone makes. Across tests 20 and 21 none of 0.13.0's eight snow globes scored above 7.0, and five of the eight others scored 7.33 or more.
- **A round scores its average angle.** With rotation only one session in a round can start from the strongest angle. 0.12.0's four snow globe sessions had drawn the two most classic angles twice each.

Two changes followed:

- **An angle is a kind of the thing, not a way of showing it.** The synthesis brief says so with the snow globe as the example, and the angle pass in verify reports a shot the way it reports a dropped part.
- **The first angle is the home angle, and it is dealt first.** Synthesis writes the kind a stranger pictures as the first angle, and `deal.py` goes through the angles in the dump's order. Someone who builds once gets the thing they pictured, made with the dump's material, and building again gives a different kind. ADR 0012's rule that the head recommends nothing still holds for what the dump says: the home angle is where the first session starts, and the dump doesn't call it better.

We rejected dealing the home angle to every session's first build without a ledger (sessions that can't share a ledger would all start from the same place, which is the collision this decision removed), and marking the home angle with a field (order already says it, and a field would read as a recommendation).

Test 22 checks both on a task no version has seen.

## What test 24 found (2026-11-15)

- **Fourteen of 16 sessions dealt through the ledger and got four different angles per dump.** Two dealt with `--no-ledger` and each landed on an angle another session already had. Their prompt said to write only one file, and the ledger is a second one. The deal does not say that the ledger is its own bookkeeping.
- **Rotation cannot fix angles that are one kind.** The block-world dump's five angles were a flat grid seen five ways. Its sessions were dealt different angles and built four empty grid editors, which scored with the prompt alone (6.17 against 5.92) while quick mode's builds scored 8.75. Every check passed on that dump: nothing tests that angles differ in kind.

## Consequences

- A deal writes a small file in the dump's folder. Deleting `.deals/` starts the rotation again; nothing else depends on it.
- The ledger is keyed by angle name and entry pointer. A write-back that re-finishes a dump (`finalize.py build F --bump`) keeps the ledger, so what still matches keeps its count and anything new is dealt first. A dump built from a work dir is a new deck and starts with no ledger: `finalize.py build <work dir>` removes one if it is there.
- Seam S13 covers the rotation, the ledger file, the lock and the fallbacks.
- Rotation costs nothing in expectation, since a session meets each angle as often as before, but within one round a weak angle goes from a risk to a certainty. Angle quality is now a create-mode responsibility.
- Create mode's dry runs must not spend the rotation. In test 22 a verify worker dealt the calculator dump nine minutes before its final build, and that one deal took the home angle. The verify brief now says not to deal (or to pass `--no-ledger`), and the build from the work dir clears any ledger left beside the dump.

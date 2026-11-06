# Go back to 0.8.0, retest it on Sonnet, then build forward from 0.11.0

ADR 0012 (0.8.0) made the dump hand over material instead of orders. On A/B test 12 (button, haiku about rare clouds, dark package toast; everything on Haiku 5.5 at medium effort) the dump side scored 7.50 against 6.33, won the toast 24 of 24, was rated more varied on all three tasks, and pooled at p = 0.045. That is the best result on these tasks so far.

Four later versions each fixed something a test found: 0.8.1 (spreads, ADR 0013), 0.9.0 (the deal, ADR 0014), 0.10.0 (a hand, ADR 0015) and 0.11.0 (amplify the user's words, ADR 0016). On Haiku builders none scored better overall than 0.8.0. The owner asked to go back to whatever scored best, stick with it, and retest it with Sonnet 5.5 at medium for the public numbers.

## First decision (2026-11-05): back to 0.8.0

The plugin was restored to 0.8.0 exactly, from the file-history snapshot taken right after test 12, and retested as test 17 (`ab-tests/2026-11-05-three-tasks-sonnet-0.8.0/writeup.md`) with Sonnet 5.5 building and grading both arms.

## What test 17 found

- The haiku won 20–2–2, as it has on every Sonnet test (21–1–2 on 0.10.0, 18–6 on 0.11.0).
- The button lost 0–23–1. All four dump buttons reused the dump's curves and came out "polite rather than dreamlike" (dreamlike 4.25 vs 8.50). That is the flaw 0.8.1 and 0.11.0 were built to fix, and on Sonnet 0.11.0's button was 9–12–3 with the best single button of its test.
- The toast lost 8–15–1 and was the least varied dump set of any Sonnet test (2.00 vs 4.00). 0.10.0's toast tied; 0.11.0's lost on layout bugs no builder looked at.
- Pooled: 28–40–4, p = 0.65. On Sonnet, no version has beaten prompt-only overall on these tasks; every version wins the haiku by a wide margin.

So 0.8.0's best score was a Haiku-builder result. On Sonnet its known flaws cost more than on Haiku, and the later versions were measurably closer on the button and on variety.

## Second decision (2026-11-05): build forward from 0.11.0

The owner asked to fix it. We decided:
- **The working tree returns to 0.11.0**, the version with the best Sonnet button and the most variety, and ADRs 0013 to 0016 are back in force.
- **The next fix is a look at the result** (ADR 0018), aimed at test 16's toast loss: layout bugs the builders never saw.
- **Test 18 retests 0.11.0 plus the look on Sonnet**, with test 16's rebuilt dumps and prompt-only builds reused.

## Consequences

- 0.8.0 stays the best Haiku-builder result on record, and test 12's showcase stands as that.
- The public Sonnet numbers come from the version that wins on Sonnet, or the write-up says that none did.

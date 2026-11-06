## Pooled across the three tasks

- B is ahead on 2 of 3 tasks. The mean B−A gap is +0.70 points.
- An exact stratified permutation test gives p = 0.087 two-sided (0.043 one-sided).
- B won 41 of 72 blind head-to-heads, lost 21 and tied 10 (win rate 0.64).

## Did 0.8.1 fix what test 12 found?

| | test 12 (0.8.0) | test 13 (0.8.1) |
|---|---|---|
| Dump buttons: dump curves reused verbatim per build | 4.25 (dump offered 5) | 2.5 (dump offered 10) |
| Dump buttons: curves all four share | 4 | 2 |
| Dump haiku that are exact 5-7-5 | 1 of 4 | **3 of 4** |
| Haiku overall, A vs B | 7.42 vs 6.58 | 7.42 vs **7.00** |
| `single_setting` warnings at the final build | (no check yet) | 0 in all three dumps |
| Creative `open_questions` defaults | haiku form defaulted away from 5-7-5 | none (only language, platform, stack) |

- **Both diagnosed failures are fixed.**
  - The haiku keep the user's form again. B's form score rose from 5.58 to 7.75, and the haiku gap narrowed from 0.84 to 0.42.
  - Verbatim copying of the dump's values fell.
- **But the builds still converge, now on whatever comes first.** The dump no longer settles values, yet every builder reads the same dump top to bottom and picks from the top.
  - **Haiku:** the first angle was "still in the wind" (a lenticular cloud). Three of four B haiku are lenticular-over-the-ridge poems, all in midwinter; the fourth is nacreous. Variety graders scored A higher, 3 of 3 (3.67 vs 2.33). A's four are all nacreous but from four different framings.
  - **Button:** all four B builds share the first two curves of the dump's spreads (an ease-out quint and an ease-out cubic). B-r1 and B-r2 have identical curve sets, and so do B-r3 and B-r4. Two of three variety graders found A more varied, describing B as "one blur-tail face/trail engine" reused four times.
  - **Toast:** each B build reuses 7–8 of the dump's colours verbatim (A builds 0–2). Three of four have an identical 54 px closed row. Two of three variety graders still found B more varied in layout and information, but A's mean variety is higher (5.00 vs 4.33).
- **No builder used the outside-chance step.** Use mode now says to let a shell `RANDOM` pick when torn. No transcript in tests 12 or 13 shows one. The builders did run the exact `jq` commands use mode prints.

## Pre-registered hypotheses

1. **B ≥ A overall on at least 2 of 3 tasks: met** (button 7.08 vs 6.58; toast 8.08 vs 6.08).
2. **The dump buttons don't converge on one set: met by the letter, not the spirit.** No build has the same curve set as all three others. But the four builds form two identical pairs, and all four share two curves.
3. **B haiku keep the form and reach at least 3 cloud types: half met.** 3 of 4 are 5-7-5, but they use only 2 cloud types.
4. **B's variety ≥ A's on at least 2 of 3 tasks: not met.** A's mean variety is higher on all three.

## What happened, task by task

**Toast (B 8.08 vs A 6.08, 21 wins and 0 losses, p = 0.029).**
- B led on compact (8.08 vs 5.75), collapsible (8.75 vs 5.50), usability (8.17 vs 6.42) and craft (8.25 vs 6.42). Tracking (7.83 vs 7.75) and dark (8.00 vs 8.00) were even.
- Grader agreement r = 0.76.
- All 8 builds are dark and toggle correctly.

**Button (B 7.08 vs A 6.58, win rate 0.60, p = 0.37).**
- B led on practical (8.25 vs 6.00) and craft (7.75 vs 6.67); A led on dreamlike (7.00 vs 6.33).
- B-r3 throws a JavaScript error in its curve picker.
- The hover check found no visible change on the largest button for A-r1, B-r1 and B-r3. The harness hovers the largest button, which isn't always the hero, and one grader said two hover strips missed the hovered button.

**Haiku (A 7.42 vs B 7.00, win rate 0.38, p = 0.66).**
- B led slightly on imagery, specificity and freshness. A led on form (8.83 vs 7.75) and resonance (7.25 vs 6.42).

## Diagnosis for the next fix

Every builder opens the same file and meets the same material in the same order. With a single reader, a JSON file always has a first item, and nothing in the dump's wording changes that. Asking the model to randomize didn't work either: it was read and never acted on.

The fix that fits is structural and outside the model. Use mode's first step would be one command that **deals** the material: it prints the head with the angles, pools and spreads in a fresh random order, and names a random starting angle and two deep cuts to try, using real randomness from the script, not the model. Every session then starts from a different corner of the same dump, which is what using the dump to explore should look like. The builders reliably ran the commands use mode printed, so a printed command is the lever that works. Not yet built; to be decided.

## Caveats

- n = 4 per arm per task, one dump per task, Haiku graders at medium effort.
- The dump-arm prompt changed (pre-registered), so its effect can't be separated from 0.8.1's.
- The A arm is rebuilt every test, and A's haiku were all nacreous this time.
- The haiku dump skipped its round-2 verify, and its readings include a 3–5 haiku sequence beyond the user's "a haiku". No B build wrote a sequence.
- Dumps ran 26–37K tokens, still over the lite target.

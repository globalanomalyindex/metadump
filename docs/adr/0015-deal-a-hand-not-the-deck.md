# Deal a hand, not the whole deck


A/B test 14 (`ab-tests/2026-11-05-three-tasks-haiku-medium-v3/writeup.md`) tested ADR 0014's deal: a fresh random order and a random starting angle for each session. All four toast builders dealt and got different hands, and their toasts still came out near-identical. Variety: prompt-only 5.67, dump 3.67. Every session still read every entry, so every session sat next to the same strongest material (an anatomy, a sampled palette, a curve pair) and built toward it. Reordering changed where a session started, not what was in front of it.

ADR 0014 rejected showing a session only part of the dump, because the dump would then hold back material. Test 14 shows the cost of the alternative: when every session reads the whole dump, the dump narrows the work across sessions even though it widens each one.

We decided:
- **The deal hands each session part of the deck.** The dealt copy keeps:
  - the spine (manifest, essence with all its angles, routing, exports, worn paths, review questions, open questions);
  - every tier-1 entry and every entry in the user's own words;
  - a random half of each task section's other entries, at least one per section.

  Routes and the index are pruned to the entries in the hand. Deep cuts come from the hand.
- **The deck stays whole.** Nothing is removed from the dump file. Across sessions every entry gets dealt, and a session can still look up one specific thing in the original. It builds from its hand.
- **The dealt copy says what it is.** Its manifest opens with a note that it's a hand, names the original, and its reading steps name the copy, so a builder doesn't deal again or drift back to the full file.

We rejected:
- dealing a fixed number of entries, because dumps range from about 80 to 200 entries and a share scales with them;
- dropping tier-1 entries or the user's words from a hand, because they carry the request itself;
- dealing the worn paths and review questions, because they push away from defaults and keep quality checks in reach; they don't pull builds together.

## Consequences

- Each session works from a different mix of the same deck. That should spread four builds across more of the dump than any one of them uses.
- A session may miss an entry that would have helped. The spine and tier 1 are there to carry quality, and test 15 checks whether they do.
- This supersedes ADR 0014's "Nothing is added or removed" for the dealt copy. It holds for the dump file itself.

## What test 15 found (2026-11-05, Sonnet 5.5 builders and graders)

- All 12 builders dealt. The dump side was more varied on the button (4.00 vs 3.00) and the haiku (5.33 vs 1.33), and won the haiku 21–1–2.
- Keeping the worn paths whole in every hand while halving the material roughly doubled their weight. The button dump's worn paths swap each classic dreamlike move for a tamer one, and the dump buttons lost 1–21–2 on dreamlike. Open: deal the worn paths too, and write their alternatives as spreads in both directions.

# Amplify the user's words; never tame them


In A/B test 15 (`ab-tests/2026-11-05-three-tasks-sonnet-medium/writeup.md`) the dump side lost the "dreamlike and ethereal, but practical" button 1–21–2. The prompt-only buttons went big: a blooming halo, an iridescent pill, a drifting light. The dump buttons came out careful and quiet, and graders rated them dreamlike 6.17 against 8.25.

The cause was the dump build, not the builders. The exclusion stage is told to list "what a model would most likely produce" as **worn paths** (`not_wanted`). For a quality the user asked for, what a model reaches for first is the quality's own vocabulary. So the button dump listed glow, glass, bounce, fade and idle drift as not wanted, and each `instead` was a tamer version ("a faint blurred halo", "a soft tinted glow only on hover, at low opacity"). "Practical" was read as a cap on "dreamlike". And a hand (ADR 0015) keeps every worn path while halving the material, so the avoid list's share roughly doubled.

The owner: the dump should encourage even more of what the user's adjectives ask for, never narrow them or call them unwanted. That is what the dump is for.

We decided:
- **The usual moves for the user's own quality words are material, not worn paths.** Glow and haze for "ethereal", grain for "vintage" go into the task sections with how to push each further: bigger, stranger, more of the quality. A worn path is only something that falls short of the user's words: a wrong reading, an empty filler word, a default that drops part of the request, or something that contradicts the user.
- **An `instead` goes further along the user's words, never back from them.** It's a spread with at least one move that is more of the quality than the worn path, and never only a quieter version. finalize warns when a worn path's `instead` only turns the quality down (`tamed_instead`).
- **A constraint word says what has to keep working, not how much quality to give.** "Dreamlike but practical" means as dreamlike as it gets while the label stays legible, the button stays focusable and the motion runs smoothly.
- **Each quality reading runs to its far end.** The dump gives the full-strength version of every reading too, and nothing in it marks that end as too much.
- **Verify reports taming.** A worn path or default that marks the user's quality as not wanted, an `instead` that only offers less, or a constraint read as a cap is a narrowing of kind `tamed`. The gap round moves those moves into the task sections as material and rewrites the `instead` as a spread that goes further.
- **The deal deals the dump's own worn paths too.** A hand keeps the user's own don'ts and the senses a word doesn't mean (`not_meant`), plus a random half of the build's own `not_wanted` worn paths. So a hand's share of avoid-lists stays the dump's. This changes ADR 0015, which kept every worn path in every hand.
- **Angles are ways into the whole request.** An angle about one sub-concern (a focus state, an empty state) belongs in a facet. Every angle carries the user's quality words.

We rejected:
- dropping worn paths altogether, because wrong readings and filler words still help a model past the first thing it reaches for;
- a list of banned "taming" words in the briefs, because the briefs then become a rulebook. The check is a warning, and verify judges in context.

## Consequences

- Dumps built after this push the user's adjectives further instead of steering away from them. Dumps built before it may still hold tamed worn paths: verify and `tamed_instead` flag them when they're rebuilt.
- A hand holds fewer worn paths, so a session sees about the same balance of "go further" and "watch out" as the whole dump.

## What test 16 found (2026-11-05)

- The rebuilt dumps hold no tamed worn paths, and the button dump's glow worn paths now ask for more. The dump side was more varied on all three tasks.
- The button gap closed from 1–21–2 to 9–12–3, and the best button of the eight was a dump build. The toast lost on craft: richer material packed into a compact UI with no look at the render. A render check at the end of use mode is the next candidate.

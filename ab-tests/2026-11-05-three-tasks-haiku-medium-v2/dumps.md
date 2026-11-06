# The three dumps (0.8.1 from the working tree, lite, Haiku 5.5 at medium effort for the main loop and every worker)

Taken from each dump agent's report and my read of each head and brief.

## t2-haiku: rare-clouds-haiku.metadump.json
- 87 entries, ~26K tokens (105 KB). Grounding 20/90 collected at the round-1 build (22%), 4 hosts.
- Final check: 0 errors, 0 warnings (no `directive_voice`, `no_angles` or `single_setting`).
- Thesis: "What makes a rare cloud interesting is the conditions the sky shows (cold, a standing wave, shear, a storm base, a short window of light), so its rarity can sit in what the eye sees rather than in the word rare."
- Angles: still in the wind; plain sketch; the watcher's first sky; twilight colour.
- The brief lays out six forms with their conditions (nacreous, noctilucent, lenticular, Kelvin-Helmholtz, mammatus, pileus) and three exemplars (Issa, Bashō ×2). It gives form as a spread: "the count runs from 5-7-5 syllables, through three measures of about eight beats, to a loose 12 to 17 syllables". The only `open_questions` default is the language (technical).
- **Leftover:** the readings now include "a season sequence of 3 to 5 haiku", which goes beyond the user's singular "a haiku". Verify reported that reading as a contradiction with the user's words in round 1, but the widening round kept it as a whole-job reading.
- Verify round 1 found narrowings of kind definition, scope, directive (the formula as a six-slot recipe, angle order, a worn-path verdict) and copy (one season word per form, a filled sheet). The widening round rewrote the count as a spread, gave several season words per form, and rewrote the synthesis. **Verify did not re-run after round 2.**
- Discovery: not run (a text task with no references).
- 13 agents.
- Main loop: 187,177 tokens, 1159 s (19.3 min).

## t3-toast: package-toast.metadump.json
- 88 entries, ~30K tokens. Grounding 34/88 collected (39%), 8 hosts.
- Final check: 0 errors, 0 warnings.
- Thesis: "A tracking toast is one surface in two states: the closed row already answers where the parcel is, and the open panel shows how it got there."
- Angles: the glance; the journey; quiet dark; the stack; the exception first. Default reading: one package's collapsed row that expands into the step list; four alternatives.
- `open_questions` defaults: the platform and the stack (both technical).
- Discovery: 3 pages (Emil Kowalski's toast article, two shadcn timeline blocks), 0 videos (a paid template left out). The moodboard holds 24 page images, 7 described.
- Verify round 1 found narrowings of kind definition, quality, directive, copy, job and scope, a contradiction, and a failing contrast value. The widening round fixed the contrast, added next steps for exceptions, and rewrote the formula as one combination. The main loop added a scoped `not_wanted` (a held exception against the user's word "toast").
- Verify round 2 left these unresolved, at lite's cap:
  - a closed-row size of 56–72 px fitted to one screenshot (verify: it narrows "very compact");
  - a dismiss time stated two ways;
  - review prompts that would pass a 72×360 row.
- 19 agents.
- Main loop: 216,776 tokens, 1426 s (23.8 min).

## t1-button: button-bezier-dreamlike.metadump.json
- 101 entries, ~37K tokens (149 KB). Grounding 28/101 collected (28%), 10 hosts.
- Final check: 0 errors, 0 warnings. Curves are now spreads; no `single_setting` survived.
- Thesis: "What makes a button dreamlike is what happens after the click lands: the face answers at once while its light keeps moving, so the control stays quick and still seems to float." (The dump agent says verify still read it as recipe-leaning.)
- Angles: settle with a light tail; float that settles; light at the rim; glass on one focal button; keyboard parity.
- Discovery: 3 pages (Comeau on CSS transitions, Heckel on cubic-bezier, a hover-effects article), no video. The moodboard holds 24 page images, 5 described.
- Two widening rounds. Round 2 dissolved the copied curve declarations into spreads, split the settle readings and added press feedback. After round 2, verify still found two contradictions with the user's words; the main loop wrote them as scoped anti-keywords. Some directive voice remains in the thesis and brief.
- 23 agents. Main loop: 206,192 tokens, 1776 s (29.6 min).

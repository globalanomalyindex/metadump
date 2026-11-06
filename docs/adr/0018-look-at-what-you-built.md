# Look at what you built

A/B test 16 (`ab-tests/2026-11-05-three-tasks-sonnet-medium-v2/writeup.md`) rebuilt the dumps with 0.11.0 and ran Sonnet 5.5 builders. The dump toasts lost 0–21–3, and the graders' notes were about rendering, not ideas: a timeline clipped mid-row, the close icon over the chevron, action rows wrapping, timestamps stranded under their dots. Every dump toast had packed more into a compact pill than fit, and none of the four builders opened the page. In test 17 the 0.8.0 dump toasts lost on craft too.

The dump gives a build more to fit. A builder that never looks at the result can't see when it doesn't fit, and a grader who does look marks it down. The prompt-only builds are simpler, so they fit by default.

Builders reliably run the commands use mode prints (the deal: 12 of 12 once it was in the dump's head). They don't reliably open a browser on their own.

We decided:
- **Use mode ends with a look.** `scripts/look.py <file.html>` renders the page in the local headless browser (through `cdp.py`, nothing installed), screenshots it at desktop and phone widths, hovers the main control and clicks the main toggle when it finds one, and runs a few layout checks on the DOM: horizontal overflow, content clipped by an ancestor, overlapping controls, and tiny targets. It prints the screenshot paths and the findings. The builder reads the screenshots and fixes what it sees before finishing.
- **The look is a question, not a gate.** Its findings are things to look at; the builder decides. The one question it puts beside the screenshots is the user's own: does this read as their words, at full strength?
- **The dump's reading steps name the look**, the way they name the deal, so a builder that opens the dump first still meets it.
- **It only runs where a Chromium-family browser is installed.** Without one it says so and the step is skipped; the skill installs nothing (CLAUDE.md).

We rejected:
- a pass/fail check that blocks finishing, because the dump is not a rulebook (ADR 0003, ADR 0012) and a layout warning can be a false positive;
- a visual grader agent, because it costs a second model call per build and the builder can look for itself;
- leaving it to the builder's judgment, because tests 16 and 17 show that judgment never opened the page.

## Consequences

- A dump-arm build costs one more command and two or three image reads.
- Seam S14 (`look.py`, real browser, skips without one) joins the agreed TDD seams.
- Test 18 checks whether the toast loss was craft: 0.11.0 plus the look, same dumps and prompt-only builds as test 16.

## What test 18 found (2026-11-05)

- All 8 UI builders ran the look, read the screenshots, and five edited between looks. With test 16's dumps and prompt-only builds unchanged, the dump side went from 27–39–6 to 57–8–7 (p = 0.0002), and the toast's craft score from 5.17 to 7.58.
- Two dump toasts still had a scrolling timeline whose last row was cut in half. The look treated `overflow: auto` as deliberate; it now reports `cut-off` when a child straddles the box's edge.

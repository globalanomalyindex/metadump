# A/B test 3: compact shopping component, Haiku, metadump 0.3.0 (2026-11-04)

Pre-registered before any run. Light and quick: two arms, small n, blind graders.

**Task (verbatim, the user's words):** "make a compact, minimal, modern shopping component."

**Arms**
- **A**: the task only.
- **B**: the task + a meta dump built for it by metadump 0.3.0 (installed plugin), lite depth, no references, so discovery is exercised. Builders consult it as use mode describes (head, routing[0], their route, scoped anti-keywords and checks), reading the skill files directly.

Both arms get the same delivery spec: one self-contained HTML file with realistic sample data, inline CSS/JS only, no external requests, interactions that actually update state, write only that file, invoke no skills.

**Models:** everything is Haiku 5.5: the dump build (a Haiku main loop running create mode with the plain-Agent path, every worker `model: haiku`), all 8 builders, all 6 graders. Effort is left at the default.

**Runs:** 4 per arm (8). A builds start alongside the dump build (they don't need it); B builds start when the dump is built.

**Grading:** two blocks of 4 (block b1 = runs 1-2 of each arm, b2 = runs 3-4). Each block is scored by 3 Haiku graders, each with its own label order (W/X/Y/Z), from a 1280x800 screenshot, a 390x844 screenshot and the source. Graders see only the task text, not the arms or the dump. Rubric, 0-10 each: compact, minimal, modern, usability, craft, overall. Plus a ranking within the block.

**Objective checks** (headless Chrome over CDP, `functional.mjs`): JS errors on load and while clicking; a primary shopping action (add / buy / cart / bag) is found and clicking it changes the page; a quantity control is found and changes a number; no horizontal overflow at 390 px; buttons without an accessible name. `works` = action found, click changes state, zero JS errors.

**Primary outcome:** mean overall score per arm and the B-vs-A win rate (same grader, same block, every A×B pair). **Secondary:** per-criterion means, functional pass rates, cost per run (tokens, seconds), grader agreement (mean pairwise Pearson of overall within a block).

**Hypothesis:** B ≥ A on overall, with the largest gains on "modern" and "craft" (where collected specifics replace defaults) and no loss on "compact"/"minimal". A null or negative result is reported as is.

**Known confounds:** n = 4 per arm; one task; LLM graders; the repo's CLAUDE.md is visible to all builders; the impeccable design hook may fire inside builder sessions on HTML writes (applies to both arms; logged if seen); the dump's quality depends on one lite build.

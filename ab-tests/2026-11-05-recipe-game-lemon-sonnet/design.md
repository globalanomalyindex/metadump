# A/B test 19: three new tasks on metadump 0.12.0, Sonnet 5.5 at medium (2026-11-05)

Pre-registered before any run. Test 18 showed 0.12.0 winning on the three tasks the whole 0.8–0.12 line was tuned against (button, haiku, toast). Test 19 asks whether that holds on tasks it has never seen, one per category the owner named:

1. **imaginative:** "a recipe for mammoth steak"
2. **technical:** "a basic tic tac toe game"
3. **visual:** "a 3D model of a lemon"

**Setup:**
- **Plugin:** 0.12.0 as released (`61de483`), unchanged during the test.
- **Dumps:** one per task, built fresh by 0.12.0's create mode at lite depth, the same way test 16's were: the create-mode main loop and every worker on Haiku 5.5 at medium effort, plain subagents, no Workflow. No references.
- **A arm:** the task alone. 4 fresh builds per task on Sonnet 5.5 at medium.
- **B arm:** the task plus the dump, used the way SKILL.md's use mode describes (deal first, look last). 4 fresh builds per task on Sonnet 5.5 at medium.
- **Prompts:** the same harness wording as tests 13–18. The recipe is a markdown reply, like the haiku. The game and the lemon are one self-contained HTML file each: inline CSS and JS only, no external requests (no CDNs or libraries, so no three.js; any way of drawing 3D is allowed), working from disk. Both arms get identical delivery lines.
- **Grading:** blind Sonnet 5.5 graders at medium, the same blocks (runs 1–2 and 3–4 of each arm), label orders and three graders per block as tests 13–18, so 6 per task. Plus 3 variety graders per task (P = A, B, A).

**What graders see:**
- recipe: the four markdown replies.
- game: desktop and phone at rest, a strip of a scripted game played by clicking cells (moves, the end state, then restart), the end state on desktop, and the source.
- lemon: desktop and phone at rest, a strip of frames over time and while dragging across the model, and the source.

**Rubrics (0–10 each):**
- recipe: imagination; recipe (works as a recipe: ingredients with amounts, clear steps, times and temperatures, honest about sourcing or stand-ins); specificity (true to mammoths and their world); voice; freshness; overall.
- game: basic (a basic tic tac toe game, complete and simple, not overbuilt); correctness (turns, all eight lines, draws, no moves on taken cells or after the end, restart); usability (whose turn and who won are clear, keyboard and screen reader, phone); craft; code (small, clear, readable source); overall.
- lemon: likeness (unmistakably a lemon: the oval with its pointed nub and stem end, pitted peel, lemon yellow); form (real 3D that holds up as it turns: geometry, depth, shading); surface (peel texture, colour, light and highlights); presentation (staging, interaction, polish, phone); overall.

**Measures:** quality per task and pooled (stratified permutation test); variety; copying (`copying.py`); whether each B builder dealt and, for the two HTML tasks, ran the look (from transcripts); functional checks (game: marks appear, a win is announced, restart clears the board, no JS errors; lemon: the canvas or scene is not blank, it moves when dragged or on its own, which renderer it uses); the recipe's length.

**Hypotheses:**
1. B ≥ A overall on at least 2 of 3 tasks.
2. Pooled, B wins more head-to-heads than it loses.
3. B's variety ≥ A's on at least 2 of 3 tasks.
4. All 12 B builders deal, and at least 7 of the 8 HTML B builders run the look.
5. The dump amplifies "basic" instead of piling features on: on the game, B's `basic` score is not below A's.
6. The technical task is where the dump adds least: B's overall lead over A is smallest on the game.

Any other result is reported as is.

**Confounds:**
- n = 4 per arm per task; one dump per task, built by Haiku while the builders are Sonnet; LLM graders.
- The look is part of the B arm's use mode and A doesn't get one, so a B gain is "dump plus look" against "prompt alone".
- The no-external-requests rule makes the lemon a hand-drawn 3D task in both arms; a real-world answer might reach for a library or a model file.
- New tasks have no earlier baseline, so test 19 is compared arm against arm within itself only.

# A/B test 11: four example tasks, Haiku 5.5 at low effort for everything, metadump 0.7.1 (2026-11-05)

Pre-registered before any run. This is the first test on 0.7.1 (ADR 0011):
- verified candidate pools for "recommend N things" tasks;
- verify no longer treats scoped constraints as narrowings;
- size budgets per shard and fewer moodboard images;
- contradictions against the user's words become scoped anti-keywords;
- quotes are checked against the page cache;
- gap shards can edit.

It is also the cheapest configuration so far: every agent runs on Haiku 5.5 at low effort. The runs feed the side-by-side previews on GitHub and a recorded version for LinkedIn. Test 10 (Sonnet builders) was scrapped at the owner's request before publication, and its files are not part of this record.

**Tasks (verbatim):**
1. `t1-button`: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website. The owner added this task back before any run, to compare with test 10 (scrapped).
2. `t2-sandbox`: a 2D physics sandbox where you can drag boxes around
3. `t3-poem`: a short poem about rare clouds, ending with a question
4. `t4-figma`: a 5 second looping animation in the style of Figma brand visuals

**Delivery:**
- Tasks 1, 2 and 4: one self-contained HTML file. Inline CSS and JS, no external requests, works from disk.
- Task 3: a markdown file holding exactly what the writer would reply to the user.

**Harness hook:** both arms of task 2 must expose `window.boxes()`, returning the boxes' current centers and sizes as `[{x, y, w, h}]` in page CSS pixels. That lets the harness drag a box and the recorder show it. Both arms get the same requirement.

**Arms:**
- **A:** task only.
- **B:** task plus a lite dump of that task, consulted the way use mode describes. The builder prompts are the same as in earlier tests, with paths updated.

**Models, all at low effort:**
- **Builders**, both arms: Haiku 5.5.
- **Dumps:** one per task. The main loop is Haiku 5.5 running 0.7.1 create mode from the installed plugin (plain subagents, no Workflow tool), and every worker is Haiku 5.5.
- **Graders:** Haiku 5.5.

**Per task:** 4 runs per arm, both arms from scratch. Two blind blocks of 4, 3 graders each, with the same label orders as earlier tests.

**What graders see:**
- **Button:** desktop and phone shots, a frame strip of hover in and out cropped around the button, and the source.
- **Sandbox:** desktop and phone shots, a frame strip of a box being dragged and released, and the source.
- **Animation:** a strip of frames across the loop, and the source.
- **Poem:** the markdown.

**Rubrics (0–10, each ends with overall):**
- **button** (the same as test 10): dreamlike (dreamlike and ethereal), practical (works on a real website: legible, clear affordance, focus state, reduced motion, cheap to render), motion (hover in and out, custom bezier timing), craft.
- **sandbox:**
  - physics: believable gravity, collisions, stacking, friction, no tunnelling;
  - interaction: drag feels direct, throwing works, works with touch;
  - stability: no jitter, explosions or boxes escaping;
  - clarity: what to do is obvious, with controls such as add or reset;
  - craft: look, layout, performance, phone.
- **poem:**
  - imagery;
  - specificity: rare clouds, named or accurately evoked;
  - question: it ends with a question that earns its place;
  - freshness: avoids cliché;
  - resonance.
- **animation:**
  - style: reads as Figma's brand visual language without copying its logo or assets;
  - motion: timing, easing, choreography;
  - loop: seamless at 5 seconds;
  - craft: polish, composition, color, performance;
  - originality.

**Click tests (headless Chrome):**
- **Button:** hover changes the button, custom `cubic-bezier` used, `prefers-reduced-motion` handled, JS errors, overflow at 390 px.
- **Sandbox:** `window.boxes()` works, dragging moves a box, the box falls after release, JS errors, overflow at 390 px.
- **Animation:**
  - a loop-seam difference: the mean absolute pixel difference between frames 5 s apart, where lower means a cleaner loop;
  - the animation is running;
  - JS errors.
- **Poem:** whether the poem ends with a question mark, and its line count.

**Featured runs:** run 1 of each arm per task, chosen now, before grading.

**Primary outcome, per task and pooled:**
- the mean overall per arm;
- the B-vs-A win rate;
- an exact permutation test per task, and a stratified one pooled.

**Secondary outcomes:**
- per-criterion means;
- the click tests;
- dump size against the lite target (8–15K tokens), build time, and whether a widening round ran (0.7.1 should need fewer);
- warnings, including the new `quote_not_in_page`;
- whether the Figma dump distills the style without carrying logo or trademark copying into builds.

**Hypothesis:**
- B ≥ A on at least 3 of the 4 tasks.
- Dumps closer to the size target than test 10's (30–47K tokens).
- Fewer widening rounds than in tests 9 and 10.

Any other result is reported as is.

**Known confounds:**
- n = 4 per arm per task;
- LLM graders judging motion and physics from frames;
- low effort may limit how much of the dump a builder reads;
- one dump per task;
- the `window.boxes()` hook shapes both arms equally;
- "Figma brand visuals" names a real brand, so graders judge style resemblance, not brand authorship.

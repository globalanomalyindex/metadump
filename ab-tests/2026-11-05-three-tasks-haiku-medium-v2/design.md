# A/B test 13: the same three tasks, Haiku 5.5 at medium effort, metadump 0.8.1 (2026-11-05)

Pre-registered before any run. Test 13 reruns test 12 (`../2026-11-05-three-tasks-haiku-medium/`) on 0.8.1 (ADR 0013: spreads, not settings).

Test 12's diagnosis: the dump still settled choices, and the builders took whatever it settled.
- Every curve facet held one curve, so the four dump buttons pasted the same four.
- An open-question default and one-sided facets steered "haiku" away from 5-7-5, and three of four dump haiku dropped it.
- None of the eight dump builds ran a play step.

0.8.1's changes:
- Values come as spreads, never single settings; finalize warns on a single curve or colour (`single_setting`).
- No defaults on creative choices, and no sides where practitioners disagree.
- The user's words stay as wide as written: never narrowed, never loosened.
- Use mode says to explore from the dump, never match it: move off whatever you take, and leave the review questions until after the work.
- Verify gets a settings pass, and its definition pass covers the user's form words.

The owner's aim, in their words: get the benefits of the meta dump without restricting the model. The dump should help the model expand on things it might otherwise miss, not make it play by a rulebook.

**Tasks (verbatim, as in test 12):**
1. `t1-button`: a button with custom bezier curve hover state animations that makes it feel dreamlike and ethereal, but practical for a website
2. `t2-haiku`: a haiku about rare clouds
3. `t3-toast`: a dark mode, very compact collapsible toast UI menu for tracking a package

**Delivery, arms, models and grading:** as in test 12.
- **Models:** every agent runs on Haiku 5.5 at medium effort. Both arms are rebuilt from scratch, and each task gets a fresh dump from the working tree (0.8.1).
- **Grading:** 4 runs per arm, two blind blocks of 4, 3 graders each, with the same label orders and the same rubrics.
- **Variety:** the same graders (3 per task, sets P and Q, P = A, B, A).
- **Featured runs:** run 1 of each arm.

**One change to the dump-arm prompt (ADR 0013):** it now says only "use it the way SKILL.md 'Use mode' describes (details in references/use.md)". Tests 10 to 12 also summarised an older reading order: "read the head, routing[0], the route for your job, and the scoped anti-keywords and checks". That summary put the review questions up front and overrode the skill's own text.

**New measures, the outcomes 0.8.1 targets:**
- **Copying.** For each dump build, I count the illustrative curves and colours in the dump (`tokens` of `inferred`/`proposed` entries) that appear verbatim in its source. For the button I also count builds that share a curve with every other build in their arm (test 12: B 4 of 4, all on the dump's 4 curves).
- **Form.** I count the haiku in each arm that are exact 5-7-5, checked by hand. In test 12: A 4 of 4, B 1 of 4.
- **The dumps' own settings.** I log the `single_setting` warnings at each dump's final build, and whether any `open_questions` default picks a creative choice.

**Hypotheses:**
1. B ≥ A overall on at least 2 of 3 tasks.
2. The dump buttons no longer converge on one set: at most 1 of the 4 shares the same curve set with the other three.
3. B's haiku keep the user's form, with at least 3 of 4 exact 5-7-5, and still reach at least 3 distinct cloud types.
4. B's variety ≥ A's on at least 2 of 3 tasks.

Any other result is reported as is.

**Known confounds:**
- n = 4 per arm per task, one dump per task, and LLM graders.
- The dump-arm prompt changed (above), so its effect isn't separable from 0.8.1's.
- The A arm is rebuilt and will differ from test 12's.

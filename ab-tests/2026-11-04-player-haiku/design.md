# A/B test 2: mini music player prototype, Haiku (2026-11-04)

Follows test 1 (../2026-11-04-luminous/). Same three arms, same aesthetic text (the user's luminous prompt, verbatim), after applying test 1's three fixes to the skill (prompt length per model family; keep both poles of every tension and let user_stated outrank proposed parameters; lean use-mode reading).

- A: prompt only, no files, no skills
- C: prompt + hand-made luminous_chromatic_translucency_metadata.json
- B: prompt + examples/metadumps/luminous-translucency.metadump.json + the fixed skill, read from the repo (the installed plugin is the older 0.1.0)

Task: one self-contained HTML file, a working mini music player for "Tide" (artwork, title/artist, seekable progress, times, prev/play-pause/next, volume, 3-4 track queue; simulated playback, no audio).

Models: every builder and grader is Haiku at medium effort.
Runs: 4 per arm (12). Judging: two blocks of 6 (runs 1-2, runs 3-4); each block scored blind by 3 Haiku graders with different label orders, from a 1280x800 screenshot plus the source, on the same rubric as test 1.
Objective checks: inline JS parses (node --check), presence of required controls, reduced-motion, backdrop-filter count, file size; tokens/time per run.
Confounds: same as test 1 (CLAUDE.md visible to all arms; lite dump; small n). Fix 1 (image prompt length) isn't exercised by a UI task.

Observed confound (during the run): the impeccable design hook also fires inside builder subagents and shows them design findings on their own file (e.g. A-r1 saw 10 contrast/glow issues and chose not to fix them). It applies to every arm alike, but it means some builders may revise toward the hook's rules.

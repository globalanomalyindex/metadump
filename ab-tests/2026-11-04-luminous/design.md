# A/B test: luminous chromatic translucency (2026-11-04)

Question: does a meta dump make downstream work better than the bare prompt, and better than the hand-made metadata file?

Arms (every arm gets the same aesthetic text: the user's original prompt, verbatim):
- A: prompt only, no files, no skills
- C: prompt + the hand-made luminous_chromatic_translucency_metadata.json (pre-skill)
- B: prompt + examples/metadumps/luminous-translucency.metadump.json (lite build) + the metadump skill's use mode

Tasks: t1 FLUX.2 product prompt (headphones) · t2 SDXL positive+negative (bus stop) · t3 landing-page hero HTML for "Tide" · t4 diagnose a flat, grey render.
2 runs per arm per task (24 runs). Model: the session model (Opus 5.5) for every run.

Judging: blind. Outputs copied to blind/<task>/<letter> with arm hidden; 2 independent judges per task score every output 1-10 on a rubric written from the user's prompt and the task only (never from either dump), with different label orders. t3 judged from rendered screenshots plus code.
Objective metrics: prompt-clause coverage, negation words in FLUX positive prompts, negative prompt present for SDXL, backdrop-filter use and reduced-motion support in HTML, length, tokens and time per run.

Known confounds: subagents see this repo's CLAUDE.md (mentions metadump) in every arm; B's dump is a lite build from the same prompt; n=2 per cell, so treat differences under ~1 point as noise.

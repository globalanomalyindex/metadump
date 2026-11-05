# A/B test 7: the shopping test from scratch on a one-agent build (an unshipped draft, scrapped) (2026-11-05)

Pre-registered before any run. Test 6 (`../2026-11-04-shop-haiku-v6/`, 0.5.1) had B ahead: 7.50 vs 6.42, win rate 0.75, every B build covering the whole shopping job. But its dump took 32 minutes to build: one Haiku main loop and 20 Haiku workers, tickets in waves, verify and a widening round. A draft labelled 0.7.0 at the time (never shipped; scrapped after this test, along with its ADR) replaced all of that with one agent that eats, digests and dumps in a single pass. It may send up to four Haiku helpers for heavy reading. The question is whether the one-agent dump is much faster and still helps.

**Same as test 6:**
- the task ("make a compact, minimal, modern shopping component.") and the delivery spec;
- Haiku 5.5 for everything at default effort;
- 4 runs per arm, both arms built from scratch;
- two blind blocks of 4, 3 graders each, with the same label orders;
- the same rubric (compact, minimal, modern, usability, craft, overall);
- the same click test, 1280x800 desktop shots and true 390x844 phone shots;
- the same builder and grader prompts, with paths updated. B's builders follow use mode from the draft skill.

**What changes:**
- The B dump is built by one Haiku agent following the draft's create mode, with no references and no extra hints beyond "follow the skill".
- The skill comes from the working tree (the uncommitted draft on top of 02d3221), so its text is exactly what would ship.

**Primary outcome:** mean overall per arm and the B-vs-A win rate.

**Secondary outcomes:**
- the dump build's wall time and tokens, against test 6's 32 minutes;
- how many helpers the agent sent;
- the dump's size, grounding line and warnings;
- whether it records `essence.task.job` and a default reading that covers the job;
- B's usability against A's;
- how many B builds cover the whole job (a way to review the bag and check out).

**Hypothesis:** the dump builds in 15 minutes or less, and B ≥ A overall. B's margin may shrink from test 6's because the one-agent dump is likely smaller and less grounded. Any other result is reported as is.

**Known confounds:**
- n = 4 per arm, and one task;
- LLM graders;
- one dump build;
- a fresh A arm whose quality varies from run to run;
- graders differ from test 6's graders, so compare directions, not decimals.

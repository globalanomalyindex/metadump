# Quick mode is the default; lite and heavy run the swarm

ADR 0021 added quick mode as the lightest depth and kept it opt-in. The swarm's full build stayed the default, because in the one direct comparison at the time (test 23) the swarm's dump scored half a point higher, though not significantly.

The confirmation test (test 24, `ab-tests/2026-11-13-confirmation-sonnet/writeup.md`) ran the frozen 1.0.0 on four tasks the owner named after the freeze, with the analysis fixed first:

- **Quick mode passed.** It beat the prompt alone 65–25–6, +1.12 of 10, p = 0.012 against a threshold of 0.025. The result leans on one task of four.
- **The full build did not pass.** +0.58, 49–23–24, p = 0.036. On a second grading pass, by graders made to open every file, it was +1.03 (p = 0.0008); by a rule written before unblinding, that pass confirms nothing by itself.
- **Neither dump beat the other.** The full build was 0.54 behind quick mode on the registered grades (p = 0.17) and 0.13 behind on the second pass (p = 0.70). In test 23 it had been 0.54 ahead (p = 0.28).
- **Cost.** A quick build used 14% more tokens than the prompt alone. The swarm's `lite` dump took 19 to 40 minutes and 17 to 23 agents before the build could start.

On 2026-11-15 the owner decided: quick mode is the default, and the other modes are lite and heavy.

We decided:

- **A request for a meta dump with no size word gets quick mode.** The model writes the dump itself and works from it (`references/quick.md`).
- **The swarm runs only when asked,** at one of two depths. `lite` is unchanged. `heavy` is the roster that was called `deep`.
- **`standard` is gone.** It was the old default, it sat between lite and deep with a roster only a little larger than lite's, and no A/B test ever ran at it. Three sizes are easier to hold than four.
- **The old names still work.** `standard` and `deep` are read as `heavy`, in the skill text and in the Workflow script, so old habits and old manifests keep working.
- **A request for what only the swarm does** (research across the web, scraped pages, watched videos, a moodboard, an old dump rebuilt) that names no size runs at `lite`. The Workflow script also runs lite when the depth is missing or one it does not know: the cheaper swarm is the safer guess.

We rejected:

- keeping four depths with a new default: the user-facing choice was already quick, lite or "everything";
- giving `heavy` the old `standard` roster: someone who asks for the heavy one wants the exhaustive build, and lite already covers the modest swarm;
- removing the swarm: it does what one pass cannot (facts collected from outside, one dump that several sessions build different kinds from), its sets were the most varied on two of four tasks, and the second grading pass says it is probably better than the registered grades showed;
- moving from quick to lite automatically when a request has references: that spends millions of tokens the user did not ask for.

## Consequences

- The default costs about a minute and no agents, and it is the one depth a confirmation test has passed.
- The default's weak spot is quick mode's: it builds the classic kind first, so where the classic is obvious the first build is close to what the prompt alone gives (the pelican and the bento menu in test 24).
- The docs now say which features belong to every dump and which only to a lite or heavy dump (provenance, tiers, routes, the index, the deal, research, pages, videos, images, verify).
- Not tested: `heavy` at all (neither `standard` nor `deep` ever was); a quick dump reused across sessions through `built`; quick mode with references.
- Released as 1.1.0.

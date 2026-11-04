# A meta dump seeds the work; it never narrows the request

ADR 0003 made the dump a resource, not a rulebook. The third A/B test (`ab-tests/2026-11-04-shop-haiku/results.md`) showed a different failure that ADR didn't cover. The task was "make a compact, minimal, modern shopping component". The dump was 99 entries, only 16% of them collected: 12 researched entries from one scraped docs page, 4 from the user's words, and the rest the build's own thinking. Two of its tier-1 entries were the build's *inferred* reading that "compact" meant one product with four parts and "nothing else". All four builders that used it built sparse product cards with no cart or checkout. They lost to builders with no dump (6.33 vs 7.04; head-to-head win rate 0.29). Discovery had picked one page and the scrape restated it. Nothing was screenshotted or looked at, and no research covered human descriptors of minimalism, exemplar brands, UX principles or shoppers' needs.

We decided the dump is a brain dump that seeds the work: what was collected plus what a model knows around the task, written down so the work can draw on it, and never a narrower task than the user asked for.
- **Tier 1 is collected only.** Only `user_stated`, `reference_observed` and `researched` entries can sit at tier 1. finalize demotes the build's own derived entries (`inferred`, `unknown`) to tier 2 (`tier1_needs_collected`) and drops them from `essence.signature`, which every consumer reads first (`signature_not_tier1`). The prompt shard restates the user's words without glossing them; a definition of a quality ("compact means few elements") is the build's thinking and goes in a derived entry.
- **Readings stay side by side.** When the request's scope allows several readings, `essence.readings` keeps them all with a default, and consumers choose or combine.
- **Decision points, not answers.** A choice nobody has made is recorded with its options, tradeoffs and sources; the dump doesn't pick.
- **Wide collection.** Research covers facets: vocabulary and human descriptors, principles, exemplars, patterns, needs, specifics, decision points. Discovery spreads across them with higher caps. Found pages are screenshotted and interpreted, not copied. A lexicon pass doubles as the associations pass.
- **Someone looks.** Every collected image, screenshot and frame is opened and described by a ticket. finalize warns about any one no `visual` entry describes (`image_not_viewed`).
- **Visible checks.** finalize reports grounding (`manifest.stats.grounding`: collected share and distinct source hosts) and prints it after every build. It warns when under a fifth of a 20+ entry dump was collected (`low_grounding`), when its sources sit on fewer than three hosts (`narrow_sources`, one page restated), and when the build's own entries other than constraint mechanisms use narrowing words like "must", "never" or "nothing else" (`narrowing_language`). Verify runs a narrowing pass. Its findings become tier-1 gaps that a gap round widens; at lite, a narrowing earns one widening round that lite otherwise skips.

We rejected:
- keeping inferred tier 1 and relying on wording, because the smaller model follows tier 1 however it's worded;
- banning the build's own thinking, because associations, readings and decision points are the seed;
- raising lite's depth only, because breadth of facets, not more entries, was what was missing.

## Consequences

- Dumps lose tier-1 entries they had only by the build's say-so. Existing dumps report `tier1_needs_collected` fixes when rebuilt.
- Lite runs cost more (two research tickets, higher discovery caps); the cost line says so.
- The same rules apply to any domain. A TDD dump seeds TDD decisions (which test first, where the seam goes, when to refactor) with options and sources from the practice. A design dump seeds visual ones the same way.

# Worked plans (illustrations, not templates)

Three charted plans across very different tasks, to calibrate how a section plan grows out of the destination jobs and query log. Copying a plan's section names onto an unrelated task is exactly the failure this skill exists to avoid: derive each plan from its own jobs.

---

## A. Visual, reference-heavy: "make a meta dump of this frozen-meal packaging" + 4 shelf photos

**Depth:** deep (four references, several consumers).

**Task and ladder:** packaging design, graphic design, typography, food photography and retail shelf design → frozen-food packaging → this brand's carton system → one flavor's front → band hexes, type sizes, photo crop. The primer covers shelf legibility at distance, hierarchy on a pack face, and food-photo conventions; the photos are distilled into brand-agnostic bands, proportions and type behavior, not copied.

**Destination jobs:** understand the design system · write image prompts for new flavors in the same system · lay out a new carton front · write on-pack copy in the same voice · produce search/alt-text metadata · check a new design against the system.

**Query log (excerpt):** What sits above what on a meal front? (1) · Which corner holds the brand mark, and is it fixed? (2) · How many color bands, and do their widths mean anything? (2) · What colors are the bands per flavor, as photographed? (2) · Is the carton glossy or matte? (2) · What type style is the product name? (1) · What must a new flavor keep, and what may change? (1) · Which words does the copy use for protein/calories? (2) · What does "Counter" not mean? (1)

**Senses:** "Counter" = brand, not countertop or tally counter.
**Layers:** retail scene / package / printed graphic / depicted food / evoked feeling. A printed sticker-like badge is not proof of a physical sticker.

| Section | Mechanisms | Why it exists |
|---|---|---|
| `composition` | invariant/variable, layers, exemplars | jobs 1, 2, 3 |
| `macro_bands` | parameters (photo-sampled hex, status), forbidden shortcuts (band width ≠ quantity) | jobs 2, 3 |
| `typography_identity` | lexicon, bindings with never_implies | jobs 2, 3, 4 |
| `food_photography` | cue → descriptor, lexicon | job 2 |
| `materials` | lexicon, anti-keywords scoped to `/materials` | job 2 |
| `flavor_catalog` | variant catalog with null rule | jobs 2, 3 |
| `copy_voice` | lexicon, exemplars, conditional grammar (front vs side panel) | job 4 |
| `search_vocabulary` | search vocabulary, not_meant as negative keywords | job 5 |
| `influences` | motif vs transferable relationship (tier 3–4) | jobs 2, 3 (keep new work original) |

**Roster:** prompt · 2 observe (2 photos each) · 1 scrape (the brand's own product pages, screenshotted) · 3 research (packaging-design lineage and exemplars, human descriptors and search vocabulary, shoppers' needs at the freezer aisle) · 1 discover (competitor cartons and shelf photos, screenshotted) · 1 moodboard (the shelf photos plus the scraped product shots, with measured band palettes) · 9 specialists · lexicon · exclusion · 2 normalize · synthesis · audit · 6 verify.
**Exports:** `image.generic` + `image.flux2` (declared), `llm_brief` for copy, `search`.

---

## B. Engineering, test-first: "build a CLI that converts Markdown recipes into a shopping list, TDD"

**Depth:** standard. No references.

**Task and ladder:** software design, testing practice and CLI design → test-driven development → this tool's test plan and seams → its cases, oracles and exit codes. The primer covers red-green-refactor, test lists, one behavior per test, fakes at boundaries, and CLI conventions (stdout for data, stderr for errors, nonzero exits).

**Destination jobs:** understand the task · write the spec/ticket list · implement a ticket · pick the next test · get a test's expected value (oracle) · check a diff after green.

**Query log (excerpt):** Which Markdown lines are ingredient lines? (1) · Do "2 cups flour" and "1 cup flour" merge? (1) · Do "2 cups" and "200 g" merge? (1) · What happens to unparseable lines? (1) · What's the CLI shape and exit codes? (2) · Which Markdown parser, and what is its real API? (2) · What must never happen (network, silent drops)? (1) · Where can tests attach? (1)

**Senses:** "convert" = turn recipes into a list, not metric/imperial unit conversion.
**Readings:** a pure library with a thin CLI (default) / a CLI that also aggregates several recipe files / a watch-mode tool. All three kept; the user decides.
**Layers:** input grammar / domain model / CLI surface.
**Research facets:** TDD practice from its originators and current practitioners (red-green-refactor, test lists, outside-in vs inside-out); Markdown parsing libraries and their real APIs (Context7); how shopping lists are actually grouped in recipe apps (exemplars); unit-merging pitfalls (patterns and anti-patterns); what home cooks need from a list (needs).
**Decision points:** which test first (degenerate empty input / simplest happy path / the riskiest merge rule); where the first seam goes (pure `buildShoppingList` vs the CLI boundary); fake or real filesystem in tests; when to refactor (each green vs once the list is done). Each with tradeoffs and sources, none decided unless the user decides.

| Section | Mechanisms | Why it exists |
|---|---|---|
| `domain_vocabulary` | lexicon + `code_name` | every job |
| `input_grammar` | conditional grammar | implement, oracle |
| `invariants` | invariant/variable → property tests | next test, check diff |
| `examples` | examples (in → out); only grounded ones are oracles | oracle |
| `seams` | seams (catches / misses) | next test, implement |
| `test_list` | test list (queue, status) | next test |
| `api_surface` | API surface, error taxonomy | spec, implement |
| `library_facts` | library facts (researched only, version null until checked) | implement |
| `prior_art` | motif vs transferable relationship | spec |
| `decisions` | decision points (options, tradeoffs, sources) | next test, implement |

**Anti-keywords:** `ak-convert` (not_meant, unit conversion), `ak-silent-drop` (not_wanted, instead "an Unparsed section", check: negative test), `ak-network` (not_wanted, scope code, check: lint `no-restricted-imports node:http,node:https`).

**Routes:** `explore_options` → `/decisions`, `essence.readings`, `/prior_art` · `tdd_next_test` → `/seams`, `/test_list`, `/decisions` · `tdd_oracle` → `/examples` (consumers keep only grounded prov) · `implement_ticket` → `/domain_vocabulary`, `/api_surface`, `/library_facts`, `/input_grammar` · `after_green` → `/invariants`, `/anti_keywords`, `/checks`.

Before any user decision, every example is `inferred`, so the oracle route has nothing to grade against: the consuming TDD loop has to ask the user (or mark the test blocked). The dump makes that need visible instead of letting the model grade its own guess.

---

## C. Writing, non-visual: "a 2,000-word literary short story about a lighthouse keeper's last night, in the spirit of Raymond Carver"

**Depth:** standard. No references.

**Task and ladder:** fiction craft → literary minimalism → this story's arc and scenes → its sentences and dialogue. The primer covers scene and summary, show and tell, omission, and point of view; Carver is distilled into transferable relationships (compression, omission, plain diction), not imitated.

**Destination jobs:** understand the story · draft a scene · write dialogue · revise a paragraph · check a draft against the dump.

**Query log (excerpt):** What POV and tense? (1) · What does "in the spirit of Carver" carry over, and what not? (1) · What is the story's central tension? (1) · What details make the lighthouse concrete without cliché? (2) · How do characters talk? (2) · What endings are off-limits? (1) · What register words are noise? (3)

**Senses:** "spirit of Carver" = compression, omission, working-class plainness; not imitation of his plots or sentences (copyright and originality).
**Layers:** premise / plot / narration / interiority / theme.

| Section | Mechanisms | Why it exists |
|---|---|---|
| `narration` | invariant/variable (POV, tense invariant; scene order variable), bindings ("terse" → dialogue, never implies cold character) | draft, revise |
| `influence` | motif vs transferable relationship (omission, not plots), researched sources on minimalism | every job |
| `concrete_details` | cue → descriptor, candidate pools (tier 4) | draft a scene |
| `dialogue` | exemplars (≥3, illustrative), lexicon of speech patterns | dialogue |
| `arc` | tensions, conditional grammar per scene | draft, check |
| `exclusions` | anti-keywords: not_wanted "it was all a dream", "storm as metaphor for grief" (instead: a specific mundane task), noise words | check |

**Exports:** `llm_brief` (Core / Also relevant / Say instead / Open / Options) and `briefs.scene_writer` for a multi-agent drafting workflow.

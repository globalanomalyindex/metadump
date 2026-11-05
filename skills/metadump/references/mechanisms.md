# Mechanisms menu

A meta dump has no fixed template. During charting you group the consumers' questions into sections named in the task's own words, then pick a **mechanism** for each section: the shape its entries take and the job it does for whoever reads it. This file is the menu. Most dumps use 5–10 mechanisms; none uses all of them.

Pick a mechanism by the question it answers, not by the domain. "What words should I use, and which mean the same thing?" is a lexicon whether the task is a carton, a REST API or a jingle.

Prefer mechanisms that hold objective, specific data (measured parameters, scraped facts, timelines, transcripts, observed exemplars, verified candidates, library facts) over ones that only hold the builder's opinions, and mechanisms that widen (readings, decision points, associations, exemplars, candidate pools) over ones that narrow. A dump seeds the work: it gives the consumer more to draw on, never a smaller task. Where a section needs a choice nobody has made, put it in the section's options area (`schema.md` §3), labeled as an option, or make it a decision point.

Contents: Facet · Keyword taxonomy · Formula · Reference descriptors · Task ladder · Discipline primer · Distillation · Lexicon · Senses · Readings · Decision points · Associations · Bindings · Invariant/variable contract · Conditional grammar · Forbidden shortcuts · Motif vs transferable relationship · Cue → descriptor · Parameters · Exemplars · Tensions · Influences and analogies · Candidate pools · Layers · Variant catalog · Search vocabulary · Detectable signals · Scraped facts · Timeline · Transcript · Moodboard · Engineering set (seams, test list, examples, API surface, error taxonomy, library facts, budgets, environment) · Prompt recipes

---

### Facet (the default shape of every entry)

**Answers:** "what is this area like, how does it behave, and why?" **Every section is written in facets**, the shape of the hand-made dumps this skill grew out of: one object per area or quality, with a line of `text`, `properties` (short phrases), `behaviors` (cause and effect), a `principle`, `signals`, and `tokens` with a `status`. Format in `schema.md` §3. Behaviors carry the most weight: "thin edges catch and transmit more light" or "a malformed line lands in Unparsed" is what lets a consumer recreate a feel or a design rather than copy it. Most other mechanisms below are facets with extra fields.

### Keyword taxonomy (many words for the same thing)

**Answers:** "what are all the ways to say it?" One entry per register, each a `keywords` list: core words, technical, perceptual, emotional and atmosphere, cultural and lineage, and the domain's own objects (materials, components, test kinds). The hand-made dumps had more of this than anything else: luminous, translucent, subsurface scattering, halation, summer nostalgia and Frutiger Aero all describe one look from different directions. Associations and lineage sit at tier 3–4, so a consumer draws on them without naming them in the output.

### Formula (the recipe, with roles)

**Answers:** "what's the whole thing in one line, and what does each part do?" Lives in `essence.formula`: `full` ("extremely saturated color + high-key illumination + translucent materials + minimal compositions"), `essential` (the shortest version) and `roles` (`{"blue": "identity", "white": "luminosity", "green": "surreal vitality"}`). For TDD: "one failing test + the smallest change + refactor on green", with roles such as the test list as the plan and the seam as the place tests attach.

### Reference descriptors (one per reference)

**Answers:** "what is in each reference?" One facet per image, page or video: `kind: "reference"`, `term` (what it shows, in a few words), `signals` (what you can see), `method: "visual"`, and its source. "Transparent cyan vinyl on a white record player: translucent blue vinyl, thickness variation, blue light transmission, white reflections." finalize counts a descriptor as someone having looked at the image.

### Task ladder (from the disciplines down to the specifics)

**Answers:** "what kind of work is this, and what does each level of it know?" **Every dump has one.** It lives in `essence.task` (`is`, `disciplines`, `ladder`), and the sections follow it from the top rung to the bottom, with entries tagged by `rung`. A shopping component: UX and UI design → e-commerce interfaces → product cards, carts and quick add → a compact, minimal, modern shopping component → its spacing, type, color, states and timing. A REST endpoint: API design → HTTP and REST conventions → this resource's endpoints → status codes, payloads and errors. A short story: fiction craft → literary minimalism → this story's scenes → sentences and dialogue. The top rungs are where a practitioner's knowledge enters the dump; the bottom rungs are where the specifics live. A consumer working on any detail can climb back up for the principle behind it.

### Discipline primer

**Answers:** "what would a senior practitioner of this discipline bring?" For each discipline at the top of the ladder: named principles, laws and heuristics, each with what it says and how it applies to this task; the discipline's vocabulary; its standards; its common mistakes; and dos and don'ts. For UI and UX: Fitts's law (bigger, closer targets for the primary action), Hick's law (fewer choices, faster decisions), Jakob's law (people expect your interface to work like the ones they know), Gestalt proximity and similarity, the usability heuristics (visibility of status, error prevention, recognition over recall), WCAG contrast (4.5:1 body text) and target size. For TDD: red-green-refactor, the test list, one behavior per test, fakes at boundaries, refactor on green. From the model's own knowledge (`inferred`), with the load-bearing parts confirmed against fetched sources (`researched`). This is what lets a dump replace a separate rule-based skill: the applicable knowledge is written down for this task, with sources, every time.

### Distillation (brand-agnostic look, feel and behavior)

**Answers:** "how do I get the feel of that reference without copying it?" When the user names a brand, product, site or body of work ("Apple's UI") or supplies screenshots, distill it: measured values (spacing scale, radii, type sizes and weights, contrast, durations), proportions, materials and surfaces, motion character, density, tone of voice, the recurring patterns, the principles that explain them, and what to do and not do to land the same feel. Descriptions are brand-agnostic ("large, quiet product imagery on near-white; one accent color reserved for the primary action"), so another agent can understand, recreate and imagine from them without copying assets, layouts or trade dress. Brand names stay in `sources` and Influences. Pair with Motif vs transferable relationship.

### Lexicon (tiered keywords with aliases)

**Answers:** what to call things, which words are central, which mean the same. **Every dump has one**, usually per major area.

```json
"c-photo-over-bands": {"term": "photo-above / information-below composition", "aliases": ["stacked image-and-band layout"],
  "keywords": ["serving photograph", "macro bands"], "tier": 1, "prov": "reference_observed", "src": ["r1", "r2"], "anchor": "r1",
  "text": "An upper serving photograph sits above a lower field of colored information bands."}
```

Merge near-synonyms into one entry's `aliases` (finalize indexes them). Separate entries that differ in meaning even if they share words. Near-synonym clutter is the biggest cause of long-context degradation, so one canonical term per concept.

### Senses (disambiguation)

**Answers:** which reading of an ambiguous prompt word is meant. Write as `not_meant` anti-keywords (see `schema.md` §6), one per wrong sense, plus the meant sense as the entry's `term`.

Examples: "Counter" (brand, not countertop); "glass" (physical glass, not glassmorphism UI); "REST" (resource-oriented HTTP, not RPC-over-POST); "noir" (lighting mood, not crime genre); "convert" (format to list, not unit conversion).

### Readings (scope senses, kept side by side)

**Answers:** "what could this request be?" When the request's scope allows several readings, each one with what it includes, and which is the default. Lives in `essence.readings` (`{"reading", "includes", "default"}`), with detail entries if needed. "Shopping component": a product card with quick add (default), a mini cart with quantity and checkout, a product list with filters, a checkout summary. "Add auth": session cookies, JWT, OAuth via a provider. Keeping every reading is what stops a dump from narrowing a request; a consumer picks or combines them. Readings the build thought of are `inferred`, tier 2. **Quality words get readings too.** For each quality word in the prompt, a facet with `kind: "quality"` and `readings` side by side, with no default: "sticky" in motion is a slow start that grips, an early settle that holds, an overshoot that snaps back, or a magnetic pull. Each reading says what it looks like in practice and gets an exemplar in the pool. Test 8's dump defined "sticky" once and fitted its curves to that; every build copied them.

### Decision points (choices with options, tradeoffs and signals)

**Answers:** "what will I have to decide, and what are my options?" Each decision the work will face, with two or more options, the tradeoff of each, signals for when each fits, and sources where practitioners discuss it: `{"decision": "which test first", "options": [{"option": "simplest happy path", "fits_when": "the interface is still unknown"}, {"option": "degenerate case (empty input)", "fits_when": "the core shape is obvious"}, {"option": "riskiest behavior", "fits_when": "one unknown could sink the design"}], "src": [...]}`. Design: density vs breathing room, one product vs a list, where the accent goes. Engineering: outside-in vs inside-out, where the seam goes, when to refactor, mock or real. The dump never answers a decision point unless the user did (then it is `user_stated`); it seeds the consumer's own decision.

### Associations (the brain dump)

**Answers:** "what does this bring to mind?" What the model knows around the task, written down so the work can draw on it: human descriptors of each key quality (how people, not specs, talk about it), sensory and emotional words, metaphors, moods, adjacent concepts, related movements and practices, and brands, products, works or people commonly associated with it, each with what it contributes. "Minimal" in shopping: calm, quiet, considered, airy, honest, Muji, Aesop, Apple Store, Everlane, lots of white space, one accent, product-first. Tier 3–4 seed material: `inferred` from the model's own knowledge, `researched` where a fetched source backs it. Pair with Influences (what to borrow) and Motif vs transferable relationship (what not to copy).

### Bindings (adjective → object, with `never_implies`)

**Answers:** what each descriptive word attaches to, and what it must not leak into.

```json
"b-vivid-bands": {"text": "'vivid', 'saturated-looking', 'flat' describe the printed color bands only.",
  "adjectives": ["vivid", "saturated-looking", "flat"], "modifies": ["printed color bands"],
  "never_implies": ["fluorescent ink", "physically flat surface"], "tier": 2, "prov": "inferred"}
```

Also for verbs: `{"verb": "overlaps", "subject": "pale panel", "target": "image/band boundary"}`. In engineering: "fast" binds to startup time and never implies a streaming parser.

### Invariant / variable contract

**Answers:** what must hold across every variant or output, and what is free to change. This is the strongest generalizer: it is how a consumer makes something *new* that still belongs.

```json
"inv-zone-order": {"invariant": "photograph above colored information field", "variable": "crop, bowl scale, food arrangement",
  "scope": "all meal fronts", "tier": 1, "prov": "reference_observed", "src": ["r1", "r3"], "anchor": "r1", "text": "..."}
```

Engineering: invariants become property tests; `variable` states what the implementation may choose. Writing: POV and tense invariant, scene order variable.

### Conditional grammar

**Answers:** "in situation X, which rules apply?" when one template would be wrong for some cases.

```json
"g-side-panel": {"when": {"surface": "carton side"}, "then": ["stacked nutrition table", "no photograph"], "tier": 2, "prov": "reference_observed", "src": ["r2"], "text": "..."}
```

Also: email campaign by send (teaser / launch / reminder), API by resource × method, CLI input lines by classification.

### Forbidden shortcuts

**Answers:** which tempting inferences are invalid. `{"from": "band width", "to": "nutrient quantity", "why": "bands are decorative proportions, not charts"}`. Engineering: "numeric id → sequential and guessable", "HTTP 200 → business success".

### Motif vs transferable relationship

**Answers:** what to carry over from an influence without copying it. Keeps derivative work original and IP-safe.

```json
"m-corner-mark": {"motif": "Counter's corner-turn wordmark", "relationship": "a compact high-contrast brand anchor separated from the product-name block",
  "translation": "use a distinct original mark; keep only the role separation", "tier": 2, "prov": "inferred", "text": "..."}
```

Writing: borrow Carver's omission, not his plots. Code: borrow CookCLI's aisle grouping, not Cooklang syntax.

### Cue → descriptor (evocative words tied to observable triggers)

**Answers:** where each mood or sensory word comes from, so it is never free-floating.

```json
"d-chromatic-punch": {"term": "chromatic punch", "aliases": ["visually punchy"], "cues": ["saturated full-width bands"],
  "modality": "visual", "caveat": "an impression, not a measured response", "tier": 2, "prov": "inferred", "text": "..."}
```

Cross-modal entries (imagined taste, sound, texture) must carry `modality` and `caveat`.

### Parameters (values with units, ranges and status)

**Answers:** the numbers a builder pastes in.

```json
"p-radius-card": {"term": "card corner radius", "v": 22, "unit": "px", "range": [20, 28], "status": "illustrative", "tier": 2, "prov": "proposed", "text": "..."}
```

Covers design tokens, sampled hex values (`status: "photo sample"`, `method: "pixel-sample"`), BPM and bar counts, word counts, status codes, timeouts, performance budgets. `status` says where the number came from and how firm it is (`measured`, `photo sample`, `illustrative`). A measured or sourced value is a fact to consult; an `illustrative` one is a starting point that lives in the options area.

### Exemplars

**Answers:** "show me." Short good/bad snippets per tier-1 concept: `"ex": {"good": ["Garlic Alfredo, 10 oz"], "bad": ["GARLIC ALFREDO!!!"]}`. Most valuable for non-visual work: a line of dialogue, an endpoint, a subject line, an ingredient line. Give at least three diverse good examples, labeled illustrative, so consumers don't anchor on one.

### Tensions

**Answers:** what productive contradiction defines the thing. Lives in `essence.tensions`, with detail entries if needed. "Measured indulgence", "nostalgic futurism", "tender cruelty". Generic outputs flatten tensions; naming them preserves them.

### Influences and analogies

**Answers:** what lineage this draws on and what each influence contributes. `{"name": "Frutiger Aero", "contributes": ["blue skies", "glossy materials", "optimism"]}`. Analogies carry `transfer` and `do_not_infer`. Research these (web sources), don't assume them: a named movement is a factual claim. Usually tier 3–4.

### Candidate pools (candidates and exemplars to pick from)

**Answers:** "give me options to pick from." Labeled alternatives the consumer composes from. Never constraints, and never a finished set of N called the default: the dump never produces the deliverable, and a set a consumer could paste is the dump doing the task. This counters the pull toward the most typical output. Two shapes, by what the task asks for:
- **N existing items** (a 5-song playlist, a reading list, three tools): **candidates**, real items each confirmed by a fetched source and labeled with the quality reading it serves, as `kind: "candidate"` facets (`term`, `by`, `year` or `version`, `reading`, `src`, `text`; `schema.md` §3). The pool holds more than N, at least 2N where the catalogs allow, spread across the readings, and the consumer picks the N. Research and scrape collect them from the catalogs that list such items (discographies, databases, bibliographies, package registries), each with a quote that confirms it. A candidate no fetched source confirms is `status: "unverified"`, `prov: "inferred"`, tier 4: a lead to check, never a recommendation. Test 10's playlist pool named bands and no songs, so every build that used it recommended acts instead of songs; the prompt-only builds named songs that were famous or made up.
- **N things to make** (three curves, a palette, title options, metaphors): one or two exemplars per reading of each quality, labeled with the reading each serves, at tier 4, which a consumer may sample (at most two) for variety.

### Layers

**Answers:** which level a property belongs to, so it doesn't drift between levels. Counter separates retail scene, package, printed graphic, depicted food and evoked feeling: "a printed sticker-like form is not proof of a physical sticker." REST: transport, resource, domain, auth. Story: premise, plot, narration, interiority, theme. Usually a section `_about` note plus a `layer` field on entries.

### Variant catalog

**Answers:** what instances exist and which values belong to which. Products, flavors, sizes, screens, endpoints, characters. Include a null rule: a missing value is `unknown`, never filled from a sibling variant.

### Search vocabulary (SEO and retrieval)

**Answers:** how people would search for this, and what metadata to publish. Short terms, medium phrases, long-tail phrases, natural-language titles/descriptions/alt text, plus `not_meant` terms as negative keywords. Mark search terms as candidate vocabulary: there is no measured volume unless a researched source says so.

### Detectable signals

**Answers:** how to recognize the style or requirement in an output. "High prevalence of rounded rectangles and capsules", "subject line ≤ 45 characters", "no network imports". These feed the review prompts in `checks`, which a consumer may run as a self-review.

### Scraped facts (quote + where)

**Answers:** "what does this page actually say?" Facts, numbers, names, dates and definitions taken from a fetched page, each with a short quote and the place it came from, so a consumer can trust it and find it again. Built by the `scrape` ticket from `webpages.py` chunks.

```json
"lf-pmma-transmission": {"term": "PMMA light transmission", "tier": 2, "prov": "researched", "src": ["s-optics-guide"], "method": "scraped",
  "where": {"url": "https://optics.example/guides/acrylic-light", "heading_path": ["Acrylic light guides", "Measured transmission"], "chunk": 2},
  "v": 92, "unit": "% at 3 mm", "text": "Cast acrylic transmits about 92% of visible light at 3 mm thickness."}
```

The source record carries the URL, title, fetched date and a quote of 25 words or fewer from that chunk. Paraphrased opinion from a page is `inferred`, not `researched`.

### Timeline

**Answers:** "how long, how fast, and with what curve?" Timed motion segments and holds measured from a video or animation: timecodes, frame numbers, fps and where it came from (`fps_source`), durations in frames and milliseconds, stepped timing (on ones, twos, threes) and the closest named easing with a fit error. Built by the `watch` ticket from `video.py timing`.

```json
"tl-logo-reveal": {"kind": "timeline", "term": "logo reveal timing", "tier": 2, "prov": "reference_observed", "src": ["r2"], "method": "frame-diff",
  "window": {"start_tc": "00:00:03.000", "end_tc": "00:00:05.000"}, "fps": 24, "fps_source": "declared",
  "segments": [{"kind": "motion", "start_tc": "00:00:03.125", "end_tc": "00:00:03.792", "frames": 16, "duration_ms": 667, "stepped": "on twos",
                "easing": {"best": "ease-in-out", "fit_error": 0.021}},
               {"kind": "hold", "start_tc": "00:00:03.792", "end_tc": "00:00:04.500", "frames": 17, "duration_ms": 708}],
  "text": "The logo eases in over 16 frames, animated on twos, then holds for about 0.7 s."}
```

Read durations as plus or minus one frame. Easing is an estimate from cumulative frame change; say so when you pass it on.

### Transcript

**Answers:** "what does the video say, and when?" A clean transcript (paragraphs with start and end timecodes, speaker when known) and the cues behind it, with rolling auto-caption repeats removed. In the dump, keep a `transcript` entry (language, track kind, length, a summary) plus `cue` entries for the passages the query log needs, each with a quote of 25 words or fewer; the full text stays in the work dir.

```json
"tr-talk": {"kind": "transcript", "term": "talk transcript", "tier": 3, "prov": "researched", "src": ["v-talk"], "method": "transcribed",
  "language": "en", "track": "manual", "duration": 1260.0, "words": 2900,
  "text": "A 21-minute talk on motion design; the timing advice is in 00:04:10-00:09:30."},
"cue-stagger": {"kind": "cue", "term": "stagger interval", "tier": 2, "prov": "researched", "src": ["v-talk"], "method": "transcribed",
  "start_tc": "00:06:02.400", "end_tc": "00:06:07.100", "speaker": null, "quote": "we stagger each card by about fifty milliseconds",
  "text": "The speaker staggers list items by roughly 50 ms."}
```

### Moodboard (image manifest + palette + what-I-see notes)

**Answers:** "what do the references look like, in measurable terms?" Collected images (from references, scraped pages and video frames) with where each came from, measured palettes, and what an agent saw looking at it. Built by the `moodboard` ticket from `images.py`, which also writes `metadumps/<slug>.moodboard.html` beside the dump.

```json
"mb-shelf-1": {"kind": "media", "media": "image", "term": "freezer shelf photo", "tier": 2, "prov": "reference_observed", "src": ["i-shelf"],
  "method": "pixel-sample", "width": 4032, "height": 3024,
  "palette": [{"hex": "#1E64C8", "share": 0.41}, {"hex": "#F0C814", "share": 0.12}],
  "text": "Saturated cobalt carton faces with a warm yellow price band; measured, not printed values."},
"mb-shelf-1-seen": {"term": "cartons read matte", "tier": 3, "prov": "reference_observed", "src": ["i-shelf"], "method": "visual",
  "text": "Soft diffuse highlights on the carton faces; no specular hotspots."}
```

Measured palette values get `method: "pixel-sample"`; what an agent sees with the Read tool gets `method: "visual"`. A user-supplied image is `reference_observed`; one found on the web is `researched`.

---

## Engineering set

For coding, TDD and engineering dumps. Add these alongside the general mechanisms. Never put file paths or code into the dump: it goes stale against the repo. Link entries to tests (`verified_by`) instead.

| Mechanism | Answers | Entry shape |
|---|---|---|
| **Domain vocabulary** | what things are called in code | lexicon entry + `code_name` (`"ShoppingList"`); aliases for search only, never for naming |
| **Seams** | where tests can attach and what each catches | `{"seam": "buildShoppingList(markdown[]) -> ShoppingList", "catches": "parse + merge", "misses": "argv, exit codes"}` |
| **Test list** | which behaviors to test, in which order | `{"behaviour": "same unit merges", "seam": "s1", "from": ["ex-flour"], "status": "todo"}`. Tier 1 first; one item per red-green cycle |
| **Examples** | literal input → expected output | `{"in": ["2 cups flour", "1 cup flour"], "out": ["3 cups flour"]}`. Only `user_stated`/`reference_observed`/`researched` examples may serve as test oracles; an `inferred` example used as an oracle is the model grading its own guess |
| **API surface** | the shape callers see | argv, stdin/stdout, endpoints, exit codes, status codes |
| **Error taxonomy** | what can fail and how it is reported | `{"error": "file unreadable", "exit": 1, "message_shape": "..."}` |
| **Library facts** | how a dependency actually behaves | `prov: "researched"` only, with a docs source (Context7 id or URL), fetched date, and `version: null` until checked against the registry. Never mint library facts as `inferred` |
| **Budgets** | performance or size limits | parameter with metric, threshold, how it is measured |
| **Environment** | runtime, OS, network policy | `{"runtime": "node 22", "network": "none in v1"}` |
| **Decision points** | the engineering choices ahead and their options | `{"decision": "where the first seam goes", "options": [{"option": "the CLI boundary", "fits_when": "the I/O contract is the risk"}, {"option": "the pure parse function", "fits_when": "the parsing rules are the risk"}], "src": [...]}`. For TDD: which test next, outside-in vs inside-out, fake or real collaborator, when to refactor. Sourced from the practice's canonical texts and current practitioners |
| **Forbidden APIs/patterns** | what code must not do | `not_wanted` anti-keyword with `scope`, `instead`, and a `check` (`{"kind": "command", "spec": "eslint no-restricted-imports node:http"}`) |

---

### Prompt recipes

**Answers:** "give me a ready brief for intent X." Per intent: `must` / `should` / `can` / `avoid`, plus a composed brief with `[slots]` for new subjects. In this format they mostly live in `exports` (compiled per consumer) rather than as a section; keep a section only when several intents need different recipes (faithful description vs derivative generation vs search metadata).

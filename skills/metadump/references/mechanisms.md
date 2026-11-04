# Mechanisms menu

A meta dump has no fixed template. During charting you group the consumers' questions into sections named in the task's own words, then pick a **mechanism** for each section: the shape its entries take and the job it does for whoever reads it. This file is the menu. Most dumps use 5–10 mechanisms; none uses all of them.

Pick a mechanism by the question it answers, not by the domain. "What words should I use, and which mean the same thing?" is a lexicon whether the task is a carton, a REST API or a jingle.

Contents: Lexicon · Senses · Bindings · Invariant/variable contract · Conditional grammar · Forbidden shortcuts · Motif vs transferable relationship · Cue → descriptor · Parameters · Exemplars · Tensions · Influences and analogies · Candidate pools · Layers · Variant catalog · Search vocabulary · Detectable signals · Engineering set (seams, test list, examples, API surface, error taxonomy, library facts, budgets, environment) · Prompt recipes

---

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

Covers design tokens, sampled hex values (`status: "photo sample"`), BPM and bar counts, word counts, status codes, timeouts, performance budgets. `status` says how binding the number is.

### Exemplars

**Answers:** "show me." Short good/bad snippets per tier-1 concept: `"ex": {"good": ["Garlic Alfredo, 10 oz"], "bad": ["GARLIC ALFREDO!!!"]}`. Most valuable for non-visual work: a line of dialogue, an endpoint, a subject line, an ingredient line. Give at least three diverse good examples, labeled illustrative, so consumers don't anchor on one.

### Tensions

**Answers:** what productive contradiction defines the thing. Lives in `essence.tensions`, with detail entries if needed. "Measured indulgence", "nostalgic futurism", "tender cruelty". Generic outputs flatten tensions; naming them preserves them.

### Influences and analogies

**Answers:** what lineage this draws on and what each influence contributes. `{"name": "Frutiger Aero", "contributes": ["blue skies", "glossy materials", "optimism"]}`. Analogies carry `transfer` and `do_not_infer`. Research these (web sources), don't assume them: a named movement is a factual claim. Usually tier 3–4.

### Candidate pools (tier 4)

**Answers:** "give me options." Labeled alternatives a consumer may sample (at most two) for variety: alternative palettes, title options, metaphors. Never constraints. This counters the pull toward the most typical output.

### Layers

**Answers:** which level a property belongs to, so it doesn't drift between levels. Counter separates retail scene, package, printed graphic, depicted food and evoked feeling: "a printed sticker-like form is not proof of a physical sticker." REST: transport, resource, domain, auth. Story: premise, plot, narration, interiority, theme. Usually a section `_about` note plus a `layer` field on entries.

### Variant catalog

**Answers:** what instances exist and which values belong to which. Products, flavors, sizes, screens, endpoints, characters. Include a null rule: a missing value is `unknown`, never filled from a sibling variant.

### Search vocabulary (SEO and retrieval)

**Answers:** how people would search for this, and what metadata to publish. Short terms, medium phrases, long-tail phrases, natural-language titles/descriptions/alt text, plus `not_meant` terms as negative keywords. Mark search terms as candidate vocabulary: there is no measured volume unless a researched source says so.

### Detectable signals

**Answers:** how to recognize the style or requirement in an output. "High prevalence of rounded rectangles and capsules", "subject line ≤ 45 characters", "no network imports". These feed `checks`.

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
| **Forbidden APIs/patterns** | what code must not do | `not_wanted` anti-keyword with `scope`, `instead`, and a `check` (`{"kind": "command", "spec": "eslint no-restricted-imports node:http"}`) |

---

### Prompt recipes

**Answers:** "give me a ready brief for intent X." Per intent: `must` / `should` / `can` / `avoid`, plus a composed brief with `[slots]` for new subjects. In this format they mostly live in `exports` (compiled per consumer) rather than as a section; keep a section only when several intents need different recipes (faithful description vs derivative generation vs search metadata).

# Meta dump format (`metadump/1`)

The exact shape `scripts/finalize.py` enforces. Read this before writing shards, a synthesis spine, or a use-mode write-back.

Contents: 1. File and top-level order · 2. Spine · 3. Task sections and entries · 4. Provenance · 5. Tiers · 6. Anti-keywords · 7. Checks · 8. Exports · 9. Sources · 10. Index · 11. Layout · 12. Shards · 13. What finalize fixes vs rejects

---

## 1. File and top-level order

One file: `metadumps/<slug>.metadump.json` at the project root. Top-level keys, in this order (finalize reorders for you):

```
manifest, essence, routing, exports, anti_keywords, checks, open_questions   ← spine (the head)
<task sections, named in the task's own words>                                ← the body
index, sources                                                                ← lookups (never read in order)
```

Spine first because it is what every consumer reads; lookups last because nobody reads them top to bottom.

## 2. Spine

### `manifest`

```json
{"schema": "metadump/1", "slug": "counter-carton", "version": 1, "created": "2026-11-04",
 "prompt": "<the user's prompt, verbatim, never paraphrased>",
 "references": [{"id": "r1", "kind": "image", "path": "refs/IMG_3200.JPG", "note": "shelf view"}],
 "consumers": ["image generation", "packaging layout", "copy"],
 "depth": "standard",
 "derived_from": [],
 "built": "chart → 2 observe, 3 research, 6 specialists, lexicon, exclusion → normalize → synthesis → verify (4 jobs) → 1 gap round",
 "how_to_read": ["... filled by finalize ..."], "head_lines": 0, "stats": {}}
```

- `prompt` is required and verbatim. It is the anchor every `user_stated` entry quotes.
- `built` is a one-line process note (≤ ~300 tokens). Do not reproduce agent handshakes, receipts or per-claim contributor lists: a consumer cannot act on them.
- `how_to_read`, `head_lines`, `stats` are written by finalize; don't hand-maintain them.
- `derived_from`: paths of earlier meta dumps this one builds on.

### `essence`

```json
{"one_sentence": "Generous food photography above vivid macro bands, organized by a pale panel and heavy black type.",
 "signature": ["c-photo-over-bands", "c-pale-panel", "c-heavy-title"],
 "tensions": [{"text": "measured indulgence", "poles": ["macro labels and counts", "sauce-coated abundance"], "prov": "inferred"}]}
```

`signature` lists up to 8 ids of tier-1 entries: the fastest way to the defining set. `tensions` records the productive contradiction a generic output would flatten.

### `routing`

The search interface. One route per consumer job:

```json
[{"job": "write the image-generation prompt", "when": "before any render",
  "paths": ["/exports/image/generic", "/composition", "/palette"],
  "jq": "(finalize)", "tokens": 0, "lines": []}]
```

- `paths` are RFC 6901 JSON Pointers that must resolve. Finalize fills `jq` (a ready command fragment), `tokens` (≈ bytes/4 of the slice) and `lines` (line spans in the file).
- Keep each route under ~8K tokens. If finalize warns `route_over_cap`, split the route or point at sub-paths.
- Finalize adds an automatic first route, `always first: the defining tier-1 entries` (`"auto": true`), pointing at every tier-1 entry; it is rebuilt on every build, so don't write it yourself.
- Every task section should be reachable from at least one route (the survival rule). An unrouted section is either unneeded or a missing route.
- Name jobs by what a consumer is doing ("implement the parser", "pick colors for a dark-mode variant", "write subject lines"), not by section names.

### `exports`, `anti_keywords`, `checks`, `open_questions`

See sections 6–8. `open_questions` holds what the prompt and evidence leave open:

```json
{"q-size": {"text": "Poster size and orientation?", "default": "A2 portrait", "impact": "composition and type scale", "resolve": "ask the user, or infer from the print brief"}}
```

Finalize gives open questions `prov: "unknown"` and `tier: 3` if absent. Use mode records answers as `user_stated` entries with `decided_in`, then deletes or keeps the question as resolved.

## 3. Task sections and entries

Everything that is not spine or lookup is a task section, named in the domain's own language (`palette`, `composition`, `error_model`, `seams`, `verse_form`, `subject_lines`). A section is a map of entries keyed by id; it may contain one level (or more) of groups, i.e. maps whose members are all entries:

```json
"palette": {
  "_about": "Colors as photographed; hex values are image samples, not print specs.",
  "roles": {
    "c-amber": {"term": "amber key light", "tier": 1, "prov": "user_stated", "anchor": "amber light", "text": "Warm amber key light from upper left.", "hex": "#D78700"}
  }
}
```

Keys starting with `_` are section notes, not entries.

### Entry envelope

| Field | Required | Meaning |
|---|---|---|
| id (the key) | yes | Readable slug with a type prefix (`c-`, `ak-`, `inv-`, `t-`, `ex-`…). Unique across the whole dump. |
| `tier` | yes | 1–4, see §5 |
| `prov` | yes | see §4 |
| `text` | yes (convention) | The entry in plain language. Write it so it can be pasted into a prompt or brief as-is. |
| `term` / `name` / `canonical` / `label` | optional | The keyword(s) this entry is about. Indexed. |
| `aliases`, `variants`, `keywords` | optional | Lists of alternative strings. Indexed. Aliases are for search; consumers name things by `term`. |
| `src` | required for `researched` / `reference_observed` | Source ids (see §9) |
| `anchor` | required at tier 1 | A short quote of the prompt, or a source id, that justifies the entry |
| `never_implies` | optional | Inferences this entry must not leak ("vivid" bands never imply fluorescent ink) |
| `ex` | optional | `{"good": [...], "bad": [...]}` short exemplars |
| `inherited` | set by inherit shards | Copied from an earlier dump; keeps its original prov |
| `decided_in` | use-mode write-back | Where the user decided it (`"use-mode 2026-11-05: user chose matte"`) |
| `verified_by` | optional | For engineering dumps: the test name that pins this entry |
| `status` | optional | Free state such as `todo` / `done` / `superseded` (test lists, parameters) |

Any other field is allowed when the mechanism needs it (`hex`, `bpm`, `invariant`/`variable`, `in`/`out`, `seam`, `catches`/`misses`, `range`, `unit`…). See `mechanisms.md`.

## 4. Provenance (`prov`)

Ranked strongest first; when two entries conflict the stronger wins, then the lower tier number.

| prov | Means | Must have |
|---|---|---|
| `user_stated` | The prompt (or the user in use mode) said it | `anchor` that is a verbatim span of `manifest.prompt` (case/space-insensitive), or `decided_in` |
| `reference_observed` | Seen in a supplied reference (image, file, URL, earlier dump) | `src` naming a source of kind `reference` or `dump` |
| `researched` | Found in a page/doc fetched during this build | `src` naming a source of kind `web` or `doc` with url and fetched date |
| `inferred` | Reasoned from the above | — |
| `proposed` | A choice the builder made where nothing decides it | — never tier 1 |
| `unknown` | Not established; never filled in silently | — |

Finalize demotes entries that claim more than their evidence supports (to `inferred`) and records each demotion as a fix. Treat a pile of demotions as a sign a ticket over-claimed.

There is no `confidence` field. `prov` says how we know; `tier` says how much it matters.

## 5. Tiers (editorial relevance, not confidence or search volume)

| tier | name | Consumer obligation |
|---|---|---|
| 1 | defining | Must be expressed. Capped at ~12 entries; each needs an anchor. |
| 2 | supporting | Should be expressed when relevant. |
| 3 | contextual | Use when the job touches it. |
| 4 | exploratory | A labeled pool of options (analogies, alternatives, cross-modal metaphors). Sample at most two; never treat as a constraint or a fact. |

## 6. Anti-keywords

The opposite of keywords: what is not meant, and what is not wanted. One map, keyed by id:

```json
"ak-countertop": {"term": "counter", "kind": "not_meant", "excluded_sense": "kitchen countertop; tally counter",
                  "instead": "Counter-brand frozen-meal carton", "variants": ["countertop", "tally counter"],
                  "scope": ["search", "image"], "match": "phrase", "tier": 1, "prov": "inferred", "anchor": "Counter"},
"ak-gloss": {"term": "glossy", "kind": "not_wanted", "instead": "matte paperboard with soft diffuse highlights",
             "variants": ["shiny", "lacquered"], "scope": ["/packaging"], "tier": 2, "prov": "inferred"},
"ak-noise-stunning": {"term": "stunning", "kind": "not_wanted", "class": "noise", "scope": ["*"], "tier": 3, "prov": "inferred"}
```

| Field | Notes |
|---|---|
| `kind` | `not_meant` (disambiguates a reading: the word means X here, not Y) or `not_wanted` (excludes something from the output) |
| `term` | The word or phrase |
| `instead` | Required for `not_wanted` unless `class` is `noise` or scope is only `["search"]`: models without a negative-prompt field (FLUX.2, gpt-image, Gemini) can only express the rewrite. For `not_meant`, `instead` names the meant sense. |
| `excluded_sense` | For `not_meant`: the sense being ruled out |
| `variants` | Spellings and near-forms; negative matching does not catch them on its own |
| `scope` | `["*"]` (default), consumer names (`"image"`, `"search"`, `"copy"`, `"code"`), section pointers (`"/packaging"`), or entry ids. A restriction on carton finish does not suppress glossy sauce. |
| `match` | `exact`, `phrase` (default) or `broad`, as in search-engine negative keywords |
| `class` | Optional: `noise` for filler words that add nothing ("masterpiece", "robust", "seamless") |
| `trigger` | Optional: when a model tends to reach for the term ("brand name without 'packaging'") |

The user's own don'ts go in verbatim as `user_stated` tier 1. Factual disclaimers ("no nutrition analysis was done") are not anti-keywords: put them in `open_questions` or a section `_about` note.

## 7. Checks

Testable statements a consumer runs on its output. Derived, so they carry `from` instead of `prov`:

```json
"k-no-gloss": {"text": "Packaging surfaces read matte, not glossy.", "from": ["ak-gloss"], "scope": ["image"],
               "severity": "must", "test": {"kind": "visual", "spec": "no specular hotspots on the carton faces"}}
```

`test.kind`: `regex`, `count`, `measure`, `visual`, `judge`, `command` (e.g. a test or lint run). Generate checks only from tier-1 entries, `user_stated` entries, invariants and `not_wanted` anti-keywords: about 20 at most. `from` ids must exist.

## 8. Exports

Ready-to-paste payloads for declared consumers, each stamped with the dump version it was compiled from:

```json
"exports": {
  "image": {"generic": {"compiled_from_version": 1, "from": ["c-photo-over-bands", "ak-gloss"],
                        "positive": "...", "constraints": "...", "negative": "...", "params": {"aspect": "4:5"}}},
  "llm_brief": {"compiled_from_version": 1, "from": [], "text": "Must: ... Should: ... Say instead: ... Unknowns: ..."},
  "briefs": {"palette-specialist": {"compiled_from_version": 1, "load": ["/palette", "/anti_keywords"], "question": "...", "returns": "..."}}
}
```

Any dict holding `compiled_from_version` is an export payload. Finalize warns `stale_export` when it doesn't match `manifest.version`; recompile before handing it on. Rules per consumer are in `exports.md`.

## 9. Sources

```json
"sources": {
  "r1": {"kind": "reference", "path": "refs/IMG_3200.JPG", "title": "Freezer shelf, four cartons"},
  "s-bfl-flux2": {"kind": "web", "url": "https://docs.bfl.ai/guides/prompting_guide_flux2", "title": "FLUX.2 prompting guide",
                  "fetched": "2026-11-04", "quote": "≤25 words copied from the page that supports the claim", "supports": ["ak-gloss"]},
  "d-counter-v1": {"kind": "dump", "path": "metadumps/counter.metadump.json", "title": "earlier dump"}
}
```

`kind`: `reference` (user-supplied), `web`, `doc` (library docs, e.g. a Context7 id), `dump` (an earlier meta dump). Keep quotes short (≤25 words): they prove the claim, they are not a copy of the page.

## 10. Index (built by finalize)

An inverted index, like a search engine's. Keys are lowercased:

```json
"acrylic": {"hits": ["/material_light/materials/mat-acrylic"],
            "words": ["/material_light/us-blue-acrylic-vinyl", "/material_light/materials/mat-opal-acrylic"],
            "not_meant": ["ak-acrylic-paint"]}
```

- `hits`: entries whose `term`/`name`/`canonical`/`label`, alias, variant or keyword is exactly this phrase.
- `words`: entries whose phrases contain this word (stopwords dropped, plurals also indexed singular). Words found in more than 25 entries are not word-indexed: too common to discriminate.
- `not_meant`: anti-keyword ids for senses of this term to avoid, so an ambiguous lookup shows the wrong sense in the same hop.
- Both lists are JSON Pointers ranked by tier (tier 1 first).

## 11. Layout (written by finalize)

Containers are indented; every entry, route, source, index record and export payload sits on one line. So `grep -n frosted F` returns whole entries, a ranged Read of a route's `lines` returns exactly its slice, and the file stays valid JSON. Never hand-format a dump; run `finalize.py build` after editing.

## 12. Shards (create mode only)

Each ticket writes `metadumps/.work/<slug>/shards/<NN-ticket>.json`:

```json
{"ticket": {"id": "30-palette", "type": "specialist"},
 "sections": {"palette": {"_about": "...", "c-amber": {...}}},
 "anti_keywords": {}, "open_questions": {}, "sources": {},
 "spine": {}}
```

- `type` sets the provenance ceiling: `prompt` may mint `user_stated`; `observe` may mint `reference_observed`; `research` may mint `researched`; `specialist`, `lexicon`, `exclusion`, `normalize`, `synthesis`, `audit` may mint only `inferred`/`proposed`/`unknown`; `inherit` keeps whatever the earlier dump said and flags `inherited`.
- Same id in two shards: the stronger entry wins and `aliases`/`variants`/`keywords`/`src` are unioned.
- `normalize`, `synthesis` and `audit` shards may set `"_replace": true` on an entry (replaces it, cannot raise its prov) or write `{"_delete": true}` (removes it).
- Only `synthesis` shards may carry `spine` (`essence`, `routing`, `exports`, `checks`).
- Shards apply in filename order. Numbering: `01` prompt · `05` inherit · `10–19` observe · `20–29` research · `30–69` specialists (`60–69` gap round) · `70` lexicon · `75` exclusion · `90–91` normalize · `95` synthesis · `96` audit · `97` repair.

## 13. What finalize fixes vs rejects

Rejects (exit 1, dump not written): missing manifest fields or essence, bad tier/prov values, duplicate ids, `src` naming a missing source, checks/exports/signature citing unknown ids, routes that don't resolve, anti-keywords with a bad kind or a `not_wanted` with no `instead`.

Fixes (and reports): prov above its evidence → `inferred`; prov above its ticket's ceiling → capped; `user_stated` without a prompt anchor → `inferred`; tier 1 that is `proposed` or has no valid anchor → tier 2; replaces that try to raise prov → blocked.

Warns: more than 12 tier-1 entries, unrouted sections, routes over ~8K tokens, stale exports, `not_meant` without `instead`, loose non-entry values, layout drift after hand edits (`check`).

# Meta dump format (`metadump/1`)

The exact shape `scripts/finalize.py` enforces. Read this before writing shards, a synthesis spine, or a use-mode write-back.

A meta dump is a resource to consult, not a source of truth to obey: it records objective, specific information (exact values, real references, measurements, timings, transcripts, sourced facts) so the model does not have to guess them. The format keeps that honest: provenance says who stands behind each entry, `method` says how its specifics were taken, and tiers say how relevant it is, never that it must be applied.

Contents: 1. File and top-level order · 2. Spine · 3. Task sections and entries · 4. Provenance and method · 5. Tiers · 6. Anti-keywords · 7. Checks (review prompts) · 8. Exports · 9. Sources · 10. Index · 11. Layout · 12. Shards · 13. What finalize fixes vs rejects · 14. Media entries (pages, videos, images)

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
 "tensions": [{"text": "measured indulgence", "poles": ["macro labels and counts", "sauce-coated abundance"], "prov": "inferred"}],
 "task": {"is": "a frozen-meal carton front (packaging design)",
          "disciplines": ["packaging design", "graphic design", "typography", "food photography", "retail shelf design"],
          "ladder": ["packaging and graphic design", "frozen-food packaging", "this brand's carton system", "one flavor's front", "band hexes, type sizes, photo crop"]},
 "readings": [{"reading": "one flavor's carton front", "includes": ["photo", "bands", "title"], "default": true},
              {"reading": "the whole flavor range as a system", "includes": ["variant rules", "shelf view"], "default": false}]}
```

`signature` lists up to 8 ids of tier-1 entries: the fastest way to the defining set. `tensions` records the productive contradiction a generic output would flatten. `task` identifies the task: what it is, the disciplines it belongs to, and the ladder from those disciplines down to this task's specifics; sections follow the ladder and entries may carry a `rung`. finalize warns when it's missing (`no_task_ladder`). `readings` (optional) keeps every plausible reading of the request's scope side by side, with what each includes and which is the default, so the dump never narrows the request to one reading; consumers choose or combine.

### `routing`

The search interface. One route per consumer job:

```json
[{"job": "write the image-generation prompt", "when": "before any render",
  "paths": ["/exports/image/generic", "/composition", "/palette"],
  "jq": "(finalize)", "tokens": 0, "lines": []}]
```

- `paths` are RFC 6901 JSON Pointers that must resolve. Finalize fills `jq` (a ready command fragment), `tokens` (≈ bytes/4 of the slice) and `lines` (line spans in the file).
- Keep each route under ~8K tokens. If finalize warns `route_over_cap`, split the route or point at sub-paths.
- Finalize adds an automatic first route, `always first: the defining tier-1 entries` (`"auto": true`), pointing at every tier-1 entry: what the task is most about, pulled first for relevance, not as rules. It is rebuilt on every build, so don't write it yourself.
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

**Options area.** `proposed` entries (the builder's choices where nothing decides it) live apart from collected facts: in a section or group named `options` or `ideas`, or under a section whose `_about` says "options, not requirements". They are never tier 1 (finalize enforces that) and exports phrase them as choices.

```json
"palette": {
  "c-amber": {"term": "amber key light", "tier": 1, "prov": "user_stated", "anchor": "amber light", "text": "..."},
  "options": {"_about": "options, not requirements: builder choices where the prompt and evidence are silent",
              "opt-dusk-variant": {"term": "dusk variant", "tier": 4, "prov": "proposed", "text": "..."}}
}
```

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
| `method` | optional | How the specifics were obtained, one of the values in §4. Unknown token-like values only warn. |
| `where` | optional | Where in a source the entry came from: `{"url", "heading_path", "chunk"}` for a page, `{"timecode", "frame"}` for a video |

Any other field is allowed when the mechanism needs it (`hex`, `bpm`, `invariant`/`variable`, `in`/`out`, `seam`, `catches`/`misses`, `range`, `unit`…). See `mechanisms.md`.

## 4. Provenance (`prov`) and method

Ranked strongest first; when two entries conflict the stronger wins, then the lower tier number. Consumers prefer the objective, sourced kinds (`user_stated`, `reference_observed`, `researched`) over guesses; `proposed` is one option among others.

| prov | Means | Must have |
|---|---|---|
| `user_stated` | The prompt (or the user in use mode) said it | `anchor` that is a verbatim span of `manifest.prompt` (case/space-insensitive), or `decided_in` |
| `reference_observed` | Seen in something the user supplied (image, video, file, URL, earlier dump) | `src` naming a source of kind `reference`, `dump`, `video` or `image` (video/image with `origin: "user"`) |
| `researched` | Found in a page, doc, video or image the build fetched | `src` naming a source of kind `web`, `doc`, `video` or `image` with url and fetched date |
| `inferred` | Reasoned from the above | — |
| `proposed` | A choice the builder made where nothing decides it | — never tier 1; lives in the options area |
| `unknown` | Not established; never filled in silently | — |

A user-supplied video or image is `reference_observed`; one found on the web is `researched`. Finalize demotes entries that claim more than their evidence supports (to `inferred`, or from `reference_observed` to `researched` when every backing video/image source has `origin: "web"`) and records each demotion as a fix. Treat a pile of demotions as a sign a ticket over-claimed.

`method` (optional) says how an entry's specifics were taken:

| method | Meaning |
|---|---|
| `scraped` | Extracted from a fetched page's chunk (`webpages.py`); `where` holds the heading path and chunk index |
| `transcribed` | From a caption track or transcript (`video.py captions`) |
| `frame-diff` | Measured from frame differences (`video.py timing`): durations, holds, stepped timing, easing |
| `pixel-sample` | Measured pixel values, e.g. a palette (`images.py`) |
| `visual` | What an agent saw looking at an image or frame |
| `measured` | Any other direct measurement (counts, sizes, timings taken by hand) |
| `researched-doc` | Read in library or product documentation (e.g. through Context7) |

There is no `confidence` field. `prov` says who stands behind it, `method` says how it was taken, `tier` says how relevant it is.

## 5. Tiers (relevance, not obligation)

Tiers rank how much an entry bears on the task. They are not confidence, search volume or a list of requirements.

| tier | name | Relevance, and how a consumer uses it |
|---|---|---|
| 1 | defining | Most relevant: what the task is most about. Read first for any job. Capped at ~12 entries; each needs an anchor and must be collected (`user_stated`, `reference_observed`, `researched`): the build's own derived entries (`inferred`, `proposed`, `unknown`) are tier 2 at most, so they can't redefine the task. |
| 2 | supporting | Relevant to most jobs; consult when the job touches it. |
| 3 | contextual | Background; pull it when the job needs that detail. |
| 4 | exploratory | A labeled pool of options (analogies, alternatives, cross-modal metaphors). Sample a couple for variety; never a fact. |

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

## 7. Checks (review prompts)

Optional review prompts a consumer may run on its own output as a self-review. They are not gates: no forced revision, and a consumer may deviate and say why. Derived, so they carry `from` instead of `prov`:

```json
"k-no-gloss": {"text": "Packaging surfaces read matte, not glossy.", "from": ["ak-gloss"], "scope": ["image"],
               "severity": "must", "test": {"kind": "visual", "spec": "no specular hotspots on the carton faces"}}
```

The key stays `checks` and `severity` stays for compatibility; read `severity` as how directly the prompt follows from the evidence (`must`: from the user's own words or a tier-1 objective entry; `should`: from supporting evidence), not as an obligation. `test.kind`: `regex`, `count`, `measure`, `visual`, `judge`, `command` (e.g. a test or lint run). Write review prompts from objective entries: `user_stated`, `reference_observed` and `researched` entries, tier-1 entries, invariants and `not_wanted` anti-keywords. Never from `proposed` entries. About 20 at most; `from` ids must exist.

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

`kind`: `reference` (user-supplied file or URL), `web`, `doc` (library docs, e.g. a Context7 id), `dump` (an earlier meta dump), `video`, `image`. Video and image sources say who supplied them in `origin` (`"user"` or `"web"`):

```json
"v-talk": {"kind": "video", "url": "https://www.youtube.com/watch?v=...", "title": "Easing in practice", "fetched": "2026-11-04",
           "origin": "web", "engine": "http", "supports": ["tl-card-enter"]},
"i-shelf": {"kind": "image", "path": "metadumps/.work/carton/images/3fa9c2d1e5b7a8c0.jpg", "title": "shelf photo", "origin": "user", "image_id": "img-3fa9c2d1e5"}
```

Keep quotes short (≤25 words): they prove the claim, they are not a copy of the page. A scraped page's source may also carry `where` (heading path and chunk index).

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

- `type` sets the provenance ceiling: `prompt` may mint `user_stated`; `observe` may mint `reference_observed`; `research` may mint `researched`; `scrape`, `watch` and `moodboard` may mint `researched` (found on the web) or `reference_observed` (supplied by the user); `specialist`, `lexicon`, `exclusion`, `normalize`, `synthesis`, `audit` may mint only `inferred`/`proposed`/`unknown`; `discover` writes no shard; the found jobs made from its picks (ids containing `-found-`) may mint only `researched` and derived provenance, and their sources are relabeled as found online (`kind: web`, media `origin: web`); `inherit` keeps whatever the earlier dump said and flags `inherited`.
- Same id in two shards: the stronger entry wins and `aliases`/`variants`/`keywords`/`src` are unioned.
- `normalize`, `synthesis` and `audit` shards may set `"_replace": true` on an entry (replaces it, cannot raise its prov) or write `{"_delete": true}` (removes it).
- Only `synthesis` shards may carry `spine` (`essence`, `routing`, `exports`, `checks`).
- Shards apply in filename order. Numbering: `01` prompt · `05` inherit · `07` discover (no shard) · `10–19` observe, watch (`19-watch-found-*` from discovery) · `20–28` research, scrape (`28-scrape-found-*` from discovery) · `29` moodboard (`29-moodboard-rN` for images found in a gap round) · `30–69` specialists (`60–69` gap round) · `70` lexicon · `75` exclusion · `90–91` normalize · `95` synthesis · `96` audit · `97` repair.

## 13. What finalize fixes vs rejects

Rejects (exit 1, dump not written): missing manifest fields or essence, bad tier/prov values, duplicate ids, `src` naming a missing source, checks/exports/signature citing unknown ids, routes that don't resolve, anti-keywords with a bad kind or a `not_wanted` with no `instead`.

Fixes (and reports): prov above its evidence → `inferred`; `reference_observed` backed only by web-found video/image → `researched`; prov above its ticket's ceiling → capped; `user_stated` without a prompt anchor → `inferred`; tier 1 that isn't collected (`proposed`, `inferred`, `unknown`) or has no valid anchor → tier 2; signature ids that didn't stay tier 1 → dropped from the signature; replaces that try to raise prov → blocked.

Warns: no task ladder (`essence.task` without disciplines and at least two rungs), low grounding (20+ entries and under a fifth collected; `manifest.stats.grounding` gives the mix and `build` prints it), sources on fewer than three hosts (`narrow_sources`), the build's own entries other than constraint mechanisms (invariants with a `variable`, forbidden shortcuts, anti-keywords) using narrowing words ("must", "must not", "never", "always", "the only", "no other", "nothing else"; `narrowing_language`), collected images no `visual` entry describes by `image_id` or by the page, video and timecode, or url they came from (`image_not_viewed`), more than 12 tier-1 entries, unrouted sections, routes over ~8K tokens, stale exports, `not_meant` without `instead`, loose non-entry values, an unknown `method` token, layout drift after hand edits (`check`).

## 14. Media entries (pages, videos, images)

The `scrape`, `watch` and `moodboard` tickets turn script output (under the work dir) into ordinary entries in task sections. The entry carries `kind` for its shape, plus the usual envelope. Script records stay in the work dir; entries hold the compact part a consumer needs, with short quotes only.

| kind | From | Shape (beyond the envelope) |
|---|---|---|
| `media` | `video.py info`, `images.py` manifest | `media` (`video`/`image`), `duration`, `fps`, `fps_source` (`declared`/`estimated`/`assumed`), `width`, `height`, `chapters` (short), `src` |
| `timeline` | `video.py timing` | `window` (`start_tc`, `end_tc`), `fps`, `fps_source`, `segments`: `[{kind: motion/hold, start_tc, end_tc, frames, duration_ms, stepped, easing}]`; `method: "frame-diff"` |
| `transcript` | `video.py captions` | `language`, `track` (`manual`/`auto`/`file`), `duration`, `words`, `summary` in `text`; `method: "transcribed"` |
| `cue` | `video.py captions` | `start_tc`, `end_tc`, `speaker` (if known), `quote` (≤25 words), `text` (paraphrase or point); `method: "transcribed"` |
| `frame` | `video.py frames` | `timecode`, `frame`, `fps`, `fps_source`, `file` (work-dir path), `text` (what is visible); `method: "visual"` |

```json
"motion": {
  "_about": "Measured from the reference video; durations are frame counts / fps, read them as +/- one frame.",
  "tl-card-enter": {"kind": "timeline", "term": "card entrance timing", "tier": 2, "prov": "researched", "src": ["v-talk"], "method": "frame-diff",
                    "window": {"start_tc": "00:01:12.000", "end_tc": "00:01:13.600"}, "fps": 60, "fps_source": "declared",
                    "segments": [{"kind": "motion", "start_tc": "00:01:12.100", "end_tc": "00:01:12.433", "frames": 20, "duration_ms": 333,
                                  "stepped": "on ones", "easing": {"best": "ease-out", "fit_error": 0.018}},
                                 {"kind": "hold", "start_tc": "00:01:12.433", "end_tc": "00:01:13.000", "frames": 34, "duration_ms": 567}],
                    "text": "Cards slide in over about 333 ms with an ease-out, then hold for about 570 ms."},
  "cue-why-ease": {"kind": "cue", "term": "why ease out", "tier": 3, "prov": "researched", "src": ["v-talk"], "method": "transcribed",
                   "start_tc": "00:01:05.200", "end_tc": "00:01:09.800", "quote": "things entering the screen should decelerate",
                   "text": "The speaker recommends decelerating curves for entering elements."}
}
```

Timecodes are always `HH:MM:SS.mmm`. Frame numbers count from 0 at the start of the video. A scraped fact is an ordinary entry with `method: "scraped"`, a `where` (`{"url", "heading_path", "chunk"}`) and a source whose `quote` (≤25 words) comes from that chunk.

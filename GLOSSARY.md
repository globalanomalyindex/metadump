# Metadump

A plugin/skill that turns a prompt (plus optional references) into a meta dump: a brain dump of structured task knowledge that models, tools and subagents draw on like a search index while the work is done. The dump seeds the work; it is not a source of truth to obey.

## Language

### The artifact

**Meta dump**:
One self-contained JSON file holding everything a model could usefully know about one task, built from a prompt and drawn on repeatedly while the work is done: the model's stream of consciousness about the task, put on paper. It holds what was collected (the user's words, references, researched facts, screenshots, measurements, timings, transcripts) and what a model knows or can think of around the task (keywords, anti-keywords, readings, associations, exemplars, patterns, needs, options, decision points), each labeled for what it is. It seeds the work: it widens what the model can draw on and pins down specifics it would otherwise guess, and it never narrows the request. The user's prompt sets the scope and the model's judgment decides. Apart from its spine, its shape is designed for the task, which can be design, coding, TDD or any other work.
_Avoid_: metadata file, spec, brief, style guide, mood board, source of truth, rulebook

**Spine**:
The few parts every meta dump shares (manifest, essence, routing table, anti-keywords, and provenance plus tier on every entry). Everything outside the spine is designed for the task.
_Avoid_: schema, template, core

**Manifest**:
The spine section recording the verbatim prompt, the creation date and the list of sources.
_Avoid_: header, metadata block

**Essence**:
The short opening section stating in a few lines what the task is and what matters most.
_Avoid_: summary card, essence card, TL;DR

**Routing table**:
The spine section at the top of a meta dump that maps each consumer job to the JSON paths holding what that job needs.
_Avoid_: index, table of contents, readme

**Slice**:
The part of a meta dump a consumer pulls for one job, addressed by JSON path.
_Avoid_: chunk, excerpt

**Entry**:
A single item in a meta dump that carries its own provenance and tier.
_Avoid_: record, item, field

**Provenance**:
The tag on every entry saying where it came from: `user_stated`, `reference_observed`, `researched`, `inferred`, `proposed`, or `unknown`, ranked in that order when entries conflict. A user-supplied video or image gives `reference_observed`; something found on the web gives `researched`.
_Avoid_: evidence class, source tag, confidence

**Method**:
The optional tag on an entry saying how it was obtained: `scraped`, `transcribed`, `frame-diff`, `pixel-sample`, `visual`, `measured` or `researched-doc`. Provenance says who stands behind an entry; method says how the specifics were taken.
_Avoid_: technique, source, confidence

**Tier**:
An entry's editorial relevance to the task: 1 defining (most relevant), 2 supporting, 3 contextual, 4 exploratory. Relevance, not obligation: a tier says how much an entry bears on the task, never that a consumer must apply it. Tier 1 holds only collected entries (the user's words, references, researched facts); the build's own derived entries (`inferred`, `proposed`, `unknown`) reach tier 2 at most. Not confidence, frequency or search volume; exploratory entries are never promoted to fact.
_Avoid_: priority, rank, weight, importance, requirement level

**Keyword**:
A word or phrase naming something the task is or wants.
_Avoid_: tag, term

**Anti-keyword**:
The opposite of a keyword: a word or phrase telling the model "this is not what I mean" or "this is not what we want." Each is one of two kinds, may be limited to a scope, and may name what to use instead.
_Avoid_: negative prompt (one export format of anti-keywords), banned word, stop word

**Not-meant**:
The anti-keyword kind that disambiguates a reading, e.g. "glass" does not mean "glassmorphism UI".
_Avoid_: disambiguator

**Not-wanted**:
The anti-keyword kind that excludes something from the output, e.g. "no stock-photo people".
_Avoid_: ban, blocklist entry

**Check**:
An optional review prompt derived from objective entries ("highlights read white, not tinted") that a consumer may run on its own output as a self-review. Kept under the `checks` key, with its `severity`, for compatibility; a check never forces a revision, and a consumer may deviate and say why.
_Avoid_: gate, requirement, must-pass test

**Collected entry**:
An entry the build gathered rather than thought up: the user's words (`user_stated`), what references show (`reference_observed`) or what a fetched source says (`researched`). Everything else is derived: the build's own `inferred` and `proposed` thinking, and `unknown`. Only collected entries reach tier 1.
_Avoid_: fact, ground truth, verified

**Reading**:
One plausible interpretation of the request's scope, with what it includes ("shopping component" read as a product card, a mini cart or a product list). A meta dump keeps every reading side by side with a default, so the consumer chooses or combines; collapsing to one is narrowing.
_Avoid_: interpretation, scope, sense (a sense is the meaning of one word)

**Decision point**:
A choice the work will face, recorded with its options, their tradeoffs, signals for when each fits, and sources (which test first, where the seam goes, density vs breathing room). It seeds the consumer's decision; it doesn't make it unless the user did.
_Avoid_: recommendation, rule, default

**Association**:
Something a model knows around the task, written down as seed material: a human descriptor, an adjacent concept, a metaphor, a mood, or a brand, work or person commonly associated with a quality, with what it contributes.
_Avoid_: vibe, tag

**Research facet**:
One angle research covers for each key quality and object in the prompt: vocabulary and human descriptors, principles and heuristics, exemplars, patterns and anti-patterns, needs, specifics, decision points. Research goes wide across facets before deep on any one.
_Avoid_: topic, category

**Grounding**:
The share of a meta dump's entries that were collected rather than thought up by the build. A dump with low grounding is mostly the build's own thinking, and finalize says so.
_Avoid_: confidence, accuracy

**Options area**:
The section or group (named `options` or `ideas`, or marked by an `_about` note saying "options, not requirements") where `proposed` entries live, so the builder's choices sit apart from the collected facts.
_Avoid_: recommendations, defaults, suggestions

### Inputs and sources

**Reference**:
An optional input supplied alongside the prompt (an image, URL, video, file or earlier meta dump) whose contents become evidence with `reference_observed` provenance.
_Avoid_: attachment, example

**Source**:
Any origin an entry is cited to: a reference, a researched web page or doc, a video or an image, recorded inside the meta dump with its link and, for video and image, whether the user supplied it or the build found it.
_Avoid_: citation, link

### Pages, videos and images

**Timeline**:
Timed motion segments and holds measured from a video or animation, each with timecode, frame number, fps, duration, stepped timing and an easing estimate.
_Avoid_: keyframes, motion spec, animation curve

**Transcript**:
The clean, timed text of what a video says: paragraphs with start and end timecodes (and a speaker when known), built from its cues with rolling auto-caption repeats removed.
_Avoid_: script, subtitles, captions

**Cue**:
One timed caption unit (start, end, text), as read from a caption file; the raw material of a transcript.
_Avoid_: subtitle line, caption line

**Frame**:
One still taken from a video at a timecode, recorded with its frame number and fps.
_Avoid_: screenshot, still, thumbnail

**Discovery**:
The create-mode step that searches the web for videos, images and pages worth watching, collecting or scraping when the prompt and references leave something to be seen or heard (how it looks, how it moves, how long that takes). What it finds is a source with `researched` provenance, never a reference.
_Avoid_: auto-references, reference search, crawling

**Moodboard**:
The HTML page beside a meta dump that shows the collected images with their sources, provenance labels and measured palettes.
_Avoid_: mood board, gallery, collage

### Use

**Consumer**:
Any skill, tool or subagent that reads a meta dump to do work, such as image generation, a UI build, a coding or TDD loop, a copywriting pass or a multi-agent workflow.
_Avoid_: client, reader, downstream

**Create mode**:
Building a meta dump autonomously from a prompt and optional references, without interviewing the user; what the prompt leaves open is recorded as `unknown` entries, not asked.
_Avoid_: generate, dump mode

**Use mode**:
Working from an existing meta dump: consulting slices before each step for the specifics the work would otherwise guess, optionally reviewing output against the dump's checks, and writing new decisions back with their provenance. Consult, don't obey: the user's prompt and the model's judgment decide.
_Avoid_: query mode, read mode, compliance

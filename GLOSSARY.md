# Metadump

A plugin/skill that turns a prompt (plus optional references) into a meta dump: a chest of structured task knowledge that models, tools and subagents consult like a search index while the work is done. The dump is a resource to consult, not a source of truth to obey.

## Language

### The artifact

**Meta dump**:
One self-contained JSON file holding everything a model could usefully know about one task (keywords, anti-keywords, descriptions, references, palettes, patterns, measurements, timings, transcripts, sources), built from a prompt and consulted repeatedly while the work is done. It is a resource, not a source of truth: it puts objective, specific information on paper so the model does not have to guess it, while the user's prompt and the model's judgment still decide. Apart from its spine, its shape is designed for the task, which can be design, coding, testing or any other engineering work.
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
An entry's editorial relevance to the task: 1 defining (most relevant), 2 supporting, 3 contextual, 4 exploratory. Relevance, not obligation: a tier says how much an entry bears on the task, never that a consumer must apply it. Not confidence, frequency or search volume; exploratory entries are never promoted to fact.
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

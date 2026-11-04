# Metadump

A plugin/skill that turns a prompt (plus optional references) into a meta dump: a chest of structured task knowledge that models, tools and subagents consult like a search index while the work is done.

## Language

### The artifact

**Meta dump**:
One self-contained JSON file holding everything a model could usefully know about one task (keywords, anti-keywords, descriptions, references, palettes, patterns, sources), built from a prompt and consulted repeatedly while the work is done. Apart from its spine, its shape is designed for the task, which can be design, coding, testing or any other engineering work.
_Avoid_: metadata file, spec, brief, style guide, mood board

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
The tag on every entry saying where it came from: `user_stated`, `reference_observed`, `researched`, `inferred`, `proposed`, or `unknown`, ranked in that order when entries conflict.
_Avoid_: evidence class, source tag, confidence

**Tier**:
An entry's editorial relevance to the task: 1 defining, 2 supporting, 3 contextual, 4 exploratory. Not confidence, frequency or search volume; exploratory entries are never promoted to fact.
_Avoid_: priority, rank, weight, importance

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

### Inputs and sources

**Reference**:
An optional input supplied alongside the prompt (an image, URL, file or earlier meta dump) whose contents become evidence with `reference_observed` provenance.
_Avoid_: attachment, example

**Source**:
Any origin an entry is cited to, either a reference or a researched web page, recorded inside the meta dump with its link.
_Avoid_: citation, link

### Use

**Consumer**:
Any skill, tool or subagent that reads a meta dump to do work, such as image generation, a UI build, a coding or TDD loop, a copywriting pass or a multi-agent workflow.
_Avoid_: client, reader, downstream

**Create mode**:
Building a meta dump autonomously from a prompt and optional references, without interviewing the user; what the prompt leaves open is recorded as `unknown` entries, not asked.
_Avoid_: generate, dump mode

**Use mode**:
Working from an existing meta dump: pulling slices before each step, checking output against tier-1 keywords and anti-keywords, and writing new decisions back with their provenance.
_Avoid_: query mode, read mode

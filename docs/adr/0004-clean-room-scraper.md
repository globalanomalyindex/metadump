# The web extraction script is a clean-room implementation

Create mode needed a deterministic, dependency-free way to turn web pages into clean text, metadata, links, images and chunks that an agent can cite. An existing open-source, LLM-driven extraction library showed a useful shape (fetch, clean, chunk, then a model extracts per chunk), but its code is not ours to copy, and we wanted no third-party packages, no model calls inside the script, and nothing in this repository that derives from that project's code, names or prompts.

We decided to use a two-room process. The orchestrating agent (the dirty room) read only that project's public README and public documentation pages, never its source, and wrote `docs/clean-room/scraper-spec.md`: behaviors, inputs and outputs, stages, options and failure modes, in its own words, with no identifiers, prompt text or project name. A separate builder agent (the clean room) implemented `skills/metadump/scripts/webpages.py`, its tests and fixtures from that spec and this repository only, with plain names of its own, and was forbidden to visit, search for, read, import or install the original. The deterministic stages (polite fetch, cleaning, chunking, crawling) live in the script; the semantic stage (turning chunks into entries with sources and quotes) is the `scrape` ticket. Search-driven, spoken and code-generating variants were left out. Each room's attestation is in `docs/clean-room/README.md`, and the repository is searched for the original's identifiers before release.

We rejected depending on the original library (a heavy third-party install, model calls inside a build script, and its own provider configuration), porting its code (licensing and provenance), and writing the script without a spec (we would lose the record of what was and was not seen).

## Consequences

- The script is stdlib-only Python 3.9 and degrades gracefully: rendered fetches and screenshots use an installed Chromium-family browser when there is one, and fall back to plain HTTP when there is not.
- Future changes to `webpages.py` keep the separation: improvements come from our own requirements and the spec, not from reading the original project.

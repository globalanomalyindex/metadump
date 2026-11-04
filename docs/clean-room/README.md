# Clean-room process for the web extraction script

The page-fetching, cleaning, chunking and crawling script under `skills/metadump/scripts/` is a clean-room implementation. It was built from a functional specification only, by an agent that never saw the project the specification describes.

## Why

The design is informed by an existing open-source, LLM-driven web extraction library. Our version must be independently written, standard-library-only, and free of that project's names, structure and prompt text, so that nothing in this repository derives from its code. This file records how the separation was kept. The ADR is `docs/adr/0004-clean-room-scraper.md`.

## The two rooms

| Room | Who | Allowed to read | Produced |
|---|---|---|---|
| Dirty room | the orchestrating agent (Fable 5.1), 2026-11-04 | the original project's public README and public documentation pages (never its source code) | `docs/clean-room/scraper-spec.md`: behaviors, inputs and outputs, pipeline stages, options, failure modes, in its own words |
| Clean room | the builder agent (Opus), 2026-11-04 | `scraper-spec.md` and this repository only | the script, its tests, fixtures and docs |

## Separation rules

1. The spec contains no code, no class, function, module, parameter or file names from the original, no prompt text, and does not name the project, its authors or its package. It describes behaviors generically.
2. The builder was forbidden to visit, fetch, search for, import or install the original project, its documentation or its package, and to use any names from it. It chose plain descriptive names of its own.
3. Before finishing, the repository is searched for the original's name and for identifiers the dirty room saw in its docs; there must be no hits.
4. Nothing outside the spec passed from the dirty room to the clean room about the original's design. Review feedback from the dirty room was limited to our own requirements (stdlib-only, graceful degradation, tests, docs).

## Attestations

**Dirty room, 2026-11-04.** I, the orchestrating agent, read the original project's public README (the repository front page and its raw Markdown) and two pages of its public documentation site. I did not open any source file, notebook, or the docs folder of its repository beyond what the README itself rendered. I wrote `scraper-spec.md` from that reading in my own words, then checked it for code, identifiers, prompt text and the project's name before handing it over. The builder's brief carried the prohibition in rule 2 verbatim. The first version of the brief also listed four pipeline names from the original's README as words to avoid; that was a small leak of identifiers (never of design), and after the build I reworded the brief so it names no identifiers at all. The builder's attestation below describes the brief as it read it.

**Clean room.** (The builder appends its own dated attestation below.)

**Clean room, 2026-11-04.** I am the builder agent (Opus). For the web extraction design I read only `docs/clean-room/scraper-spec.md` and this repository (its README, CLAUDE.md, glossary, ADRs, skill references, scripts, tests and the A/B results), plus the builder brief, which named a few identifiers of the original project solely as words to avoid. I did not visit, fetch, search for, read, import or install the original project, its documentation site, its package, its source, or any article about it; I ran no web searches at all during this work and did not try to identify the project. My only network use was an opt-in live fetch of https://example.com/, pages served from a local 127.0.0.1 server, and video metadata requests to YouTube for the video script, none of them related to the original. I wrote `skills/metadump/scripts/webpages.py`, `tests/test_webpages.py` and the fixtures in `tests/fixtures/pages/` from section 3 of the spec, with plain names of my own (fetch, clean, chunk, crawl, page record, element); I renamed my HTML tree class from `Node` to `Element` so no stage or structure carries that word. The identifier search in the release checklist (the original's name and the pipeline names the dirty room saw; excluding `.git`, `.playwright-mcp`, `ab-tests`) finds nothing in anything I wrote or in any tracked file; its only matches are in the gitignored `.scratch/upgrade/builder-brief.md`, where the brief lists those names as forbidden.

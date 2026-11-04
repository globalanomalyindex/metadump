# Meta dumps are self-indexing; no separate query tool

A meta dump can reach 400 KB (~100K tokens), too large to load whole without diluting the model's attention, so consumers must read it in slices. We decided the dump itself is the interface: a thin spine (manifest, essence, routing table, anti-keywords) at the top maps each consumer job to JSON paths, and consumers pull those slices with `jq` or a ranged Read. We rejected a bundled query script and a separate essence-card file to keep the artifact single-file and usable by any tool that can read JSON.

## Consequences

- The routing table is load-bearing: a dump whose routing table is missing or stale is effectively unsearchable, so create mode must validate every routed path resolves.
- Ordering matters: sections are written most-important-first so a partial read still gets tier-1 entries.

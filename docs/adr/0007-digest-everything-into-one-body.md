# Digest everything ingested into one body, at every depth

The owner's analogy for a meta dump: eat a bunch of food, digest it, take a dump. Everything goes in (the prompt, references, research, scraped pages, video, images, the model's own associations), gets broken down and absorbed, and comes out as one new thing. Nothing passes through whole. Until 0.6.0, lite builds had no digest step: they skipped the normalize pass and went straight from per-ticket shards to synthesis. Undigested chunks reached the final file. The 0.3.0 shopping dump had a whole section (`product_card_api`) that was one scraped docs page restated, and nothing flagged it.

We decided that digestion is a named pass that runs at every depth, lite included. The `normalize` ticket does it. It merges the same idea from different sources into one entry that cites all of them, breaks source-shaped sections up into the task's own sections along the task ladder, and writes the patterns that sources share without dropping the collected entries underneath. finalize warns about a section of five or more entries that all cite one single source (`undigested_source`).

We rejected leaving lite without a digest to save one agent, because lite is the depth people use most and the one that failed; letting synthesis dedupe on the side, because synthesis writes the spine and builds and doesn't break sections up; and merging automatically in finalize, because deciding that two entries are the same idea needs judgment.

## Consequences

- Lite costs one more agent per round.
- Entries end up organized by concept, not by where they came from, with many sources each. Provenance is unchanged: a merged entry keeps its strongest provenance, and finalize still caps it.

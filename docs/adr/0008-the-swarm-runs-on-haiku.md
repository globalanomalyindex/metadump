# The create-mode swarm runs on Haiku, at its default effort

The Workflow script asked for high effort on the synthesis agent and let every other agent inherit the session's model, which is often a large one. Every A/B test from the third on ran the whole pipeline on Haiku: the dump build, the builders and the graders. On 0.5.0 and 0.5.1, the Haiku-built dumps won 83% and 75% of blind head-to-head pairs.

We decided that every agent in the create-mode swarm runs on Haiku at its default effort. `index.workflow.js` routes every agent call through one helper that sets `model: 'haiku'`, and the plain-subagent path tells the main loop to pass `model: "haiku"` on every Agent call. The quality comes from small, well-briefed jobs, the checks in finalize, and the verify and widening rounds, not from a bigger model per worker.

We rejected keeping high effort for synthesis, because nothing showed it helped and the owner asked for it gone; and inheriting the session model, because it made cost and behavior depend on whatever model the session happened to run.

## Consequences

- Builds are much cheaper and the cost estimates assume Haiku.
- The main loop (charting, the prompt shard) still runs on whatever model the session uses.

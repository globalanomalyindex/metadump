# The dump surfaces material to play with; nothing in it is an instruction

A/B test 11 (`ab-tests/2026-11-05-four-tasks-haiku-low/results.md`, unpublished) ran four tasks on 0.7.1 with every agent on Haiku at low effort. The dump side was ahead on three of them and won 61 of 96 blind head-to-heads. The way it won the poem showed what was wrong with how dumps read:

- The poem dump's head was a recipe. The thesis: "a rare cloud earns a short poem when one named formation and its light carry the turn". The formula: "one rare formation named by its shape and light + a turn + a closing question about a visible detail". The LLM brief began "Core: … Choose one rare formation and its light or edge … Put a turn before the last stanza". Nacreous clouds came first in the brief and had the most detail. All four builds that read the dump wrote about nacreous clouds, each with a turn and a closing question. They scored well, because each grader saw only four poems and never all eight together, but they were one poem written four times.
- The dump-built Figma loops shared motifs taken from the dump (a selection-handle square and a starburst).
- Earlier ADRs fixed the visible symptoms: 0003 (a resource, not a rulebook), 0005 (don't narrow the scope), 0010 (quality words keep their readings, and the dump never produces the deliverable). Use mode already said "draw on it, don't obey it". The dump's own register still said the opposite. Its first route was "always first: the defining tier-1 entries". Its brief template started "Must: … Should: …", later "Core:". Its review prompts carried `severity: must`. A small model reads the register, not the disclaimer.

The owner put the goal this way: less like a bible or a strict set of facts, more like "here's some stuff to work with". The dump brings things up from the depths of the model to the surface, where they can be tinkered with and played with.

We decided:
- **The dump surfaces; it doesn't instruct.** It brings up what was collected and what the model knows but wouldn't say first (deep cuts, odd corners, exact numbers, other ways of seeing the thing) and puts it on the table. The user's words are the only requirements in it. Everything else is material: observations, options side by side, dials with ranges, questions.
- **The head opens with ways in, not a recipe.**
  - The thesis (`essence.one_sentence`) says what is interesting about the subject ("colors appear to exist inside materials rather than on their surfaces"). It never says how to make the deliverable.
  - The formula names ingredients, as one combination among several.
  - `essence.angles` holds 2 to 5 contrasting ways in. Each angle has a name, a line saying the move, and the entries it draws on. None is the default. finalize warns when there are fewer than two (`no_angles`).
- **The head, the exports and the review prompts speak in material voice.**
  - finalize warns about rule words (must, never, always, the only, choose one…) and the old `Core:`/`Must:`/`Should:` labels in the essence, each export's text and each review prompt (`directive_voice`). It joins `narrowing_language`, which already covers the build's own entries.
  - The LLM brief's blocks become **On the table** (material, mixed, with deep cuts), **Ways in** (the angles), **Dials** (values with ranges and what turning them does), **Worn paths** (the generic move, then a fresher one), and **Open**.
  - Review prompts are phrased as questions.
  - The automatic first route reads "start here: what the task is most about".
- **Pools have no order, and no item gets star billing.** The head and the brief give pool items equal weight. Use mode says order means nothing. When a consumer keeps landing on the first item or is torn, it lets something outside the model choose (a dice roll in the shell), because a model left alone picks the most typical item.
- **Use mode becomes a play loop.**
  1. Your own take first.
  2. Spread the material out.
  3. Play: pick what sparks something, put together two pieces that don't obviously go together, turn the dials, and sketch two or three quick variations.
  4. Make your own thing.
  5. Look back with the review questions.
  Nothing in the dump decides for the consumer.
- **Verify gets a voice pass.** An entry or export that reads as an order, or a head that funnels every consumer to the same pick (one exemplar described far more than the rest, a single recipe, an ordered pool led by one item), is a narrowing of kind `directive`. Like any narrowing it earns lite its widening round. The gap round rewrites it as material: options side by side with equal weight, angles instead of one road.

We rejected:
- dropping the thesis and formula, because the hand-made dumps had them and they carry the idea behind the look. Recast as an insight and ingredients, they help.
- shuffling pools at build time, because consumers would still take whatever came first. The fix is in how pools are written and read.
- making one angle the default, because that is a recipe again under another name.
- dropping anti-keywords, because the user's own don'ts are real constraints (ADR 0005). The build's own are worn paths, written with a fresher move in `instead`.
- renaming `checks.severity`, because it would break existing dumps for little gain. Use mode already reads it as evidence strength, and the review prompts become questions.

## Consequences

- Builds that read the same dump should spread out across a pool instead of converging on its first item. Test 12 checks this with the same graders, plus a look at how varied each arm's outputs are.
- A synthesis agent has two more warnings to clear, and verify one more pass to run.
- The dump's facts don't change. Collected entries are still the most trustworthy specifics; only the way they are offered changes.

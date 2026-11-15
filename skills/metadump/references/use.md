# Use mode: working from an existing meta dump

For any skill, tool or session doing work in a project that has a meta dump. The point is to pull the few thousand tokens that matter for the step at hand, never the whole file, and to keep the dump true as decisions get made.

**Play with it, don't obey it.** The dump is a brain dump brought up to the surface: what was collected about the task (the user's words, references, researched facts, screenshots, measurements, timings, transcripts) plus what a model knows around it but wouldn't say first (deep cuts, readings, associations, exemplars, patterns, numbers, other ways of seeing the thing). It's a pile of stuff to work with, laid out on the table to be picked up, combined, bent and tried, not a spec and not a set of facts to comply with. Apart from the user's own words, nothing in it is an instruction (ADR 0012), and nothing in it settles a choice for you (ADR 0013). **Use it to go further, not to match it:** it's there to show you corners you'd otherwise miss, so the work ends up somewhere the bare prompt wouldn't have reached, not somewhere the dump already described. The user's prompt sets the scope and your judgment decides. Prefer its collected entries over your guesses when you need a real specific, treat everything else as material for your own choices, and when you go a different way from an entry, say so where it matters to the user. **It never shrinks the task:** if an entry would rule out something the user's request plausibly includes, the request wins.

**Your own take comes first.** Before you pull anything, write two or three lines of your own approach from the user's prompt alone. Then read the dump to widen and specify it: new pieces, exact values, references to look at, odd corners worth trying. That way the dump adds to your thinking instead of replacing it.

`F` below is the dump path, e.g. `metadumps/counter-carton.metadump.json`.

## 1. Locate

- A path was given → use it.
- Otherwise glob `metadumps/*.metadump.json` (and `**/*.metadump.json` if none). Several → pick by `manifest.slug` / `manifest.prompt` relevance to the current task; if two are plausible, say which you chose.
- Check `manifest.version` and `manifest.derived_from` so you use the newest dump in a lineage.

### Deal it (always, before reading)

```bash
python3 <SKILL>/scripts/deal.py F     # <SKILL> is the folder SKILL.md is in
```

It prints your **hand**: an angle to start from and two deep cuts from the outer tiers. It also writes a **dealt copy** that holds the hand: the user's words and don'ts, every tier-1 entry and the review questions, plus half of every task section's other entries and of the dump's own worn paths, each at its own pointer, in a fresh random order. Routes and the index in the copy point only at what's in the hand. Use the dealt copy as `F` from here on and build from it. Reach into the original only to look up one specific thing; write-backs (step 6) edit the original too.

**A quick dump is not dealt.** A dump written in one pass (`quick.md`) opens with `request` and has no manifest, routes or index. `deal.py` says so, tells you to read the whole file, and names the kind to build: the first one not in the dump's `built` list. Follow `quick.md` from its step 2; the rest of this guide is for full dumps.

**Deals rotate.** A small ledger beside the dump (`.deals/<slug>.deals.json`) remembers how often each angle and entry has been dealt, and every deal takes what has been dealt least. So your angle is one the other sessions didn't start from, and your half of the material is the half the last hand left out. Angles are dealt in the dump's own order: the first deal starts from the home angle, the kind of the thing a stranger pictures, and later deals move outward. The hand says which deal it is. `--no-ledger` deals independently and writes nothing; a seeded deal (`--seed`) keeps no ledger either.

Why: a model reading a file top to bottom starts from whatever comes first, so every session reading the same dump converged on its first angle and first values (tests 12 and 13). Reordering alone wasn't enough either. In test 14, four sessions dealt different starting angles, read every entry anyway, and built the same toast. So each session works from a different part of the deck (ADRs 0014, 0015). In tests 18 and 19 every hand drew its angle independently, and in four of six tasks three of the four sessions were dealt the same one; those three built the same thing (three bone-in tomahawks from "the show plate"). Sessions follow their angle, so the deal now hands out different ones (ADR 0019). The hand is still a place to start, not a rule: combine it with something else, or leave it if it fights the request. An angle is a kind of the thing: it says which one you're making. It never changes what the user asked for or how much of it: in test 20, sessions told to take their angle far built a snow globe with no base and a timer whose clock was the small print, and lost to builds that stayed recognisable.

## 2. Read the head (about 2–4K tokens, always)

```bash
jq '{manifest, essence, routing}' F
```

or Read with `limit = manifest.head_lines`. The head tells you the verbatim prompt, what matters most (essence and signature), and which routes exist with their token cost.

## 3. Pick a route and pull its slice

**Reading lean works best: head → `routing[0]` → one route (plus its export, if there is one) → scoped anti-keywords and checks.** That is usually 3–5 `jq` calls and a few thousand tokens. Then do the work, and come back when you hit a term you can't resolve or a question the dump might answer. Reading every section costs time and tokens and dilutes attention without improving the result (the first A/B test averaged 21 reads per task for no gain over 5).

First pull the automatic route `routing[0]` (`start here: what the task is most about`, about 1–2K tokens). Once, at the start, also pull the spread: `essence.angles` (kinds of the thing, the home angle first), `essence.readings` (every reading of the request) and the "explore options" route if there is one (decision points, exemplars, associations, pools). This replaces reading around, it doesn't add to it: head, `routing[0]`, the spread, then one route per step. Then match the job you are doing to a `routing[].job` (read `when` too) and run that route's `jq`:

```bash
jq '<routing[i].jq>' F
```

Add the worn paths (anti-keywords) for your scope: places not to stop, each with moves that go further. A worn path is never a reason to do less of what the user asked for: if one seems to turn a quality word down (calls glow worn for "ethereal"), read it as a push past the obvious version, bigger or stranger, not back from it (ADR 0016). A constraint word in the prompt ("practical", "compact") says what has to keep working, not how much of the quality to give. Leave the review questions (`checks`) for after the work (step 5): read up front, they turn into a checklist to satisfy. For a consumer scope like `image`, `copy`, `code` or `search`:

```bash
jq --arg s image '.anti_keywords | with_entries(select((.value.scope // ["*"]) as $sc | ($sc|index("*")) != null or ($sc|index($s)) != null))' F
jq --arg s image '.checks | with_entries(select((.value.scope // ["*"]) as $sc | ($sc|index("*")) != null or ($sc|index($s)) != null))' F
```

Anti-keywords scoped to a section pointer (`"/packaging"`) apply when your slice includes that section. Pull them with the same filter using the pointer as `$s`.

No route fits? Look terms up instead of reading sections:

```bash
jq '.index["frosted glass"]' F          # hits (exact phrase), words (contains the word), not_meant (senses to avoid)
# fetch every entry a lookup points at, in one command:
jq --arg t opal '. as $d | [(.index[$t].hits + (.index[$t].words // []))[] | ltrimstr("/") | split("/") as $p | $d | getpath($p)]' F
jq '.index | keys[] | select(contains("aero"))' F   # partial key match when a lookup misses
grep -n 'frosted' F                     # every entry is one line, so grep returns whole entries
jq '[del(.index) | .. | objects | select(.tier == 1 and has("prov"))]' F   # the defining set
```

If the job is recurring and no route covers it, that is a gap: add a route in a write-back (step 6).

A small dump (head says total tokens under ~15K) can be read whole; anything bigger, slice it.

### Pages, videos and images

Dumps built with `scrape`, `watch` or `moodboard` tickets hold measured and transcribed entries. Find them by route first, then by index or shape:

```bash
jq '[.. | objects | select(.kind == "timeline")]' F                       # every measured timeline
jq '[.. | objects | select(.kind == "cue" and (.text | test("stagger")))]' F   # transcript passages on a topic
jq '[.. | objects | select(.method == "pixel-sample")]' F                 # measured palettes
jq '[.. | objects | select(.method == "scraped")] | .[0:5]' F              # facts taken from pages, with their `where`
jq '.index["ease out"]' F                                                 # or look the term up
```

**Look at the images yourself.** For any visual job, open the moodboard render (`metadumps/<slug>.moodboard.png`) with the Read tool, then the images and screenshots that matter (their paths are in `sources` of kind `image`, and in `metadumps/<slug>.moodboard/`). Descriptions and palettes tell you what someone saw; looking tells you what is there. Then come back to the entries for the numbers. Timelines read as plus or minus one frame; easing names are the nearest standard curve. `exports.md` says how timelines, transcripts and palettes become animation parameters, copy and image prompts.

## 4. Play

Before you build, play with what you pulled. A few minutes here is where the dump pays off: a model left alone takes the most typical road, and the dump is there to put other roads on the table.

1. **Spread it out.** Look at the angles, the pool, the exemplars, the associations and the dials side by side. **Order means nothing:** the first item in a list is not the best one, and no item is the answer.
2. **Pick what sparks something,** not what comes first or what's described at most length. Deep cuts (the less obvious exemplar, the odd corner, the specialist's term) are the point of the dump.
3. **Let a size word bound it.** If the request says simple, basic, minimal, small, short, quick or compact, that word caps the build. The dump offers more than fits, and its worn paths often point at one more feature (a setting, a saved state, a confirm step). Leave out whatever the person wouldn't miss. In tests 19 and 20 the dump builds lost points for being overbuilt against "basic" and "simple", and the prompt-only builds did not.
4. **Put things together.** Two pieces that don't obviously go together (an angle with an unlikely exemplar, a measured timing with an association) often make the strongest work. Borrow a relationship from an exemplar rather than its surface.
5. **Move off whatever you take.** Illustrative values come as spreads: a range, or several values far apart. A value from the dump is where you start turning the dial, not where you stop, and a set you find there (curves, colours, lines) is one sample of a space: make your own. If you notice you're copying a value or an option verbatim, that's the sign to go further. Only `measured` and `sourced` values are facts about the world, so use those as they are.
6. **Sketch two or three quick variations** (a line each, from different angles), then build the one you like most, or a blend.
7. **When you're torn, or keep landing on the first item, let something outside you choose:** the deal already did this once for the whole dump; for a single choice, `echo $((RANDOM % 4))` picks from four. A model picking by itself reaches for the most typical option every time.

Then make your own thing. The notes below say how to read each kind of material.

- **Entries are facets.** Each is one area of the task: `text` says what it is, `properties`, `keywords` and `descriptors` are the vocabulary, `behaviors` say how it acts (recreate those, not the reference), `principle` says why, `signals` say how to recognize it, and `tokens` carry numbers with their `status` (only `measured` and `sourced` ones are facts). The thesis (`essence.one_sentence`) says what's interesting about the subject, and `essence.formula` names its ingredients: one combination among several, not the steps of the deliverable. Tier 3–4 vocabulary (associations, lineage, influences) shapes the work, but don't name it in the output.
- **Tiers say relevance, not obligation.** Tier 1 is what the task is most about: read it for every job and let it shape the work. Tier 2 is relevant to most jobs, tier 3 is context, and tier 4 is a labeled pool of options to sample for variety. None of them is a requirement; the user's prompt is.
- **Read the ladder from the top.** `essence.task` names the disciplines and the rungs down to this task. The primer sections at the top (principles, laws, heuristics, standards) apply to every step, so pull them when a decision touches them. The bottom rungs hold the specifics. When a detail is unclear, climb a rung for the principle behind it.
- **Cover the whole job.** `essence.task.job` lists what the people using your result do, end to end. Before you build, check your plan covers every step; where the default reading leaves one out, combine readings (a product card plus a bag you can review and a way to check out). Compact and minimal shape how each step looks, not whether it exists.
- **Readings and decision points are yours.** `essence.readings` lists every reading of the request; the default only marks where the user's whole job is covered, and combining readings is often best (a product card *with* a small cart). Decision points list options and tradeoffs; pick per the user's words and your situation, and say which you picked when it matters. A `kind: "quality"` facet lists the ways a quality word can be read, with no default: pick one or combine them, and take the pool's exemplars as material for your own values, not as the set to paste. If the dump seems to hand you the finished answer, treat it as one option.
- **Pick from verified candidates.** When the task asks for N existing items (five songs, a reading list, three tools), the pool's `kind: "candidate"` entries are real items, each confirmed by a fetched source and labeled with the reading it serves: compose the N from them, across the readings the user's words point to. A candidate with `status: "unverified"` is a lead: check it before you use it. When the pool holds fewer than N verified candidates, say so to the user and offer what is verified, instead of inventing the rest.
- **Riff.** Associations, exemplars and tier-4 pools are there to widen what you consider: combine two, borrow a relationship from an exemplar, push past the first idea. They're never quotas, and you're free to go outside them.
- **Objective first.** Prefer `user_stated`, `reference_observed` and `researched` entries (and anything with a `method` such as `measured`, `scraped`, `transcribed`, `frame-diff` or `pixel-sample`) over your own guesses. `inferred` entries are directions you may adapt; `proposed` entries in the options area are one option among others.
- **Keep both poles of every tension.** `essence.tensions` names the contradictions that define the work ("overexposed yet saturated", "measured indulgence"). Outputs that express both sides at once tend to be the strong ones: blown-out highlights *and* a saturated sky, not a pale washed-out compromise. Resolving a tension to one pole is the most common way a careful output ends up flat.
- **The user's words outrank the builder's choices.** `proposed`/`inferred` parameters (a safe palette, a token scale, a layout) are starting points. When one pulls against a tier-1 `user_stated` quality, the user's quality wins and the parameter adapts. If it guards a hard constraint like text contrast, look for a design that satisfies both, e.g. keep the saturated field and put text on a local scrim, rather than draining the whole design.
- **State as fact** only `user_stated`, `reference_observed`, `researched`. Never fill an `unknown` silently: use the `open_questions` default (they're technical: language, framework) and say so.
- **The user's words are as wide as they wrote them.** The dump explores around them, never instead of them: when the user names a form (a sonnet, a landing page, a limerick), its common convention is part of what they asked for, and the dump's variations are material, not a way out of it.
- **Exclusions become rewrites:** each `not_wanted`'s `instead` is the positive way to say it. For `not_meant`, use the meant sense and avoid the excluded one.
- **Variables are free:** an invariant's `variable` field lists what may change.
- **Use exports when they exist** (`exports.image.*`, `exports.llm_brief`, `exports.briefs.*`), after checking `compiled_from_version == manifest.version`. A stale export should be recompiled from its `from` ids before use. An export is a starting point; adapt it to the job.
- Consumer-specific conversion rules (image models with and without negative fields, LLM briefs, subagent briefs, code, TDD, search metadata, timelines, transcripts, palettes) are in `exports.md`.

## 5. Look at it

When you've built something that renders (a page, a component, a poster), look at it before you finish:

```bash
python3 <SKILL>/scripts/look.py <your file.html>
```

It opens the file in the local headless browser (nothing installed; it says so and steps aside when there isn't one) and does three things.

**It looks.** Screenshots at desktop and phone widths, the pointer resting on the main control, the main toggle opened, and a layout pass at each: content running off the screen, content clipped by an ancestor, a scrolling box whose last row is cut in half, controls that overlap, targets too small to hit, a hover that changes nothing.

**It plays** (ADR 0020). From a fresh load at each width it acts on everything a person could: it clicks buttons, cells and toggles, types into fields, moves sliders to their far end, picks the next option, drags a canvas, with reset-like controls last. Then it tabs through the page. After every action it checks what should hold for any page:

| finding | what happened |
|---|---|
| `js-error` | the page threw when something was used |
| `uneven` | siblings that matched in size stopped matching (a board whose rows squash once marks land) |
| `clipped`, `cut-off`, `overlap`, `overflow` | the same layout pass, on a state only an action reaches |
| `dead` | several controls were tried and nothing on the page responded |
| `washed-out` | a label that can't be read partway through its hover, or once hovered |
| `focus-static` | keyboard focus shows nothing (or an outline is set and an ancestor clips it) |
| `focus-hidden` | the Tab key lands on controls nobody can see, such as inside a collapsed panel |
| `no-keyboard` | something answers a click that Tab never reaches |
| `covered` | a panel beside the main visual on a laptop sits on top of it on a phone |
| `no-reduced-motion` | motion that never stops, on a page that never asks `prefers-reduced-motion` |

Each one names the action that brought it out, so you can reproduce it.

**It tells you what happened.** The walk prints a short account in words:

```
Played it at desktop and phone width, 10 actions:
  1. clicked 7 of the 9 matching controls in #board: the page said "O to move", "X to move", ... "X wins"
  2. clicked 2 more: nothing changed
  3. clicked "New game": the page said "X to move"
```

Read it against the user's whole `job` (`essence.task.job`): did every step happen, and did the page say what it should? A control that did nothing may be right in that state; you decide.

**Run the dump's own plays.** Review questions about behaviour often give steps ("Play X 0, O 1, X 2, O 4, X 3, O 5, X 7, O 6, X 8; the status reads a draw"). You know your page's selectors, so run them:

```bash
python3 <SKILL>/scripts/look.py game.html --play "click #c0; click #c1; click #c2; click #c4; click #c3; click #c5; click #c7; click #c6; click #c8; expect draw"
```

Steps are split by `;`: `click SEL`, `hover SEL`, `type TEXT into SEL`, `press KEY`, `drag SEL by DX,DY`, `wait MS`, `expect TEXT` (the page says it), `expect SEL says TEXT`, `expect no TEXT`. A play starts from a fresh load, is held to the same checks as the walk, and a failed `expect` says what the page said instead. Repeat `--play` for several; `--no-walk` skips the automatic walk. Use a play to reach a state the walk can't: a drawn game, the third step of a form, a panel that only opens after a choice.

**Let it run.** For anything that keeps moving on its own, look once more after it has run a while: `--play "wait 20000"` waits twenty seconds and saves `play-1.png`. Is it still doing what it did at the start? Every other shot shows a page in its first seconds. In tests 22 and 23 six lava lamps looked right at load and had run down within ten seconds (wax pooled at the bottom or stuck at the top), and their builders had looked two to five times.

**Then fix, and read the shots.** Fix what's listed first. In test 19 the builders who got a clean list stopped there, and the list was clean only because the old look never played the page. Then read the desktop and phone shots at full size with the Read tool. The sheet is one labelled image of every state, good for a quick pass over what the walk reached, and too small to judge the drawing by: in test 20 the builders who read only the sheet opened one to three images on a visual task, and the ones who read full-size shots opened four to seven and built better. Ask two things of what you see. Would a stranger who saw it for one second name what the user asked for, or something else (an egg, where a lemon was wanted)? And does it read as the user's words, at full strength? Fix what you see and look again. A dump gives you more to fit than a bare prompt does, and the builds that lost in tests 16 to 19 lost on things nobody had looked at or used (ADR 0018). The findings are things to look at, not rules; you decide.

`checks` are review questions, not gates. When they help, ask the ones in your scope of your own output:

| `test.kind` | How |
|---|---|
| `regex` | run the pattern over the text output |
| `count` / `measure` | count or measure the property |
| `command` | run it (tests, lint) |
| `visual` | look at the image or render against the description |
| `judge` | judge against `text`, citing evidence |

If your output departs from one, that can be the right call: keep it when the user's words or the work justify it, and mention the deviation briefly when it matters to the user. There is no forced revision pass. Engineering checks that run real tests or lint (`command`) are worth running, since they report facts about the code.

**When the user's words name a practical constraint** (practical, accessible, compact, performant, cheap), run the checks scoped to it before you finish. They are still review prompts, not gates (ADR 0003), but don't skip them. In test 10 the dump-built buttons ran an infinite animation on a blurred layer even at rest, the cost the dump's "practical" reading was there to prevent, and the graders marked it down.

## 6. Write back

Write back to the original dump, never the dealt copy (it's a reordered view for this session). Below, `F` is the original.

The dump stays live: new decisions go into it with honest provenance.

- **User decides something** ("go matte", "unit conversion is never wanted"): add or edit an entry with `prov: "user_stated"`, `decided_in: "use-mode <date>: <short quote>"`. If it answers an open question, delete that question (or add `"resolved": "<entry id>"`).
- **You discover something** (an edge case, a library fact, a better term): add it as `inferred` (or `researched` with a source you fetched), tier 2–3, never tier 1 on your own authority.
- **Engineering:** mark test-list items `done` with `verified_by: "<test name>"`; add new edge cases as `todo` (`inferred`).

Edit with jq, then let finalize restore the layout, index, costs and version:

```bash
jq '.palette["c-matte"] = {"term":"matte finish","tier":1,"prov":"user_stated","anchor":"matte","decided_in":"use-mode 2026-11-05: user said go matte","text":"All carton faces matte; no specular hotspots."}' F > F.tmp && mv F.tmp F
python3 <SKILL>/scripts/finalize.py build F --bump
```

`--bump` increments `manifest.version`, so exports compiled from the old version now warn as stale: recompile the ones you use. If finalize exits 1, fix the reported error; nothing was written.

Only the main loop writes back. Subagents return what they relied on (`cites[]`) and their findings, and the orchestrator records them, so parallel agents never edit the file at once.

## 7. Orchestrating subagents from a dump

- Give each subagent the dump path and its brief (`exports.briefs.<role>` if one exists, else a route's paths). Tell it to read the head plus its `load` paths only.
- Ask for `cites[]` (dump ids relied on) in every result. A merge step can use the dump's review prompts to compare results for consistency, as a review, not a gate.
- In a Workflow script, put the brief in the agent prompt; agents can run `jq` themselves.

# metadump

a claude code plugin that takes a prompt and turns it into a meta dump.

## what's a meta dump

a meta dump is what i call one big JSON file that's basically a giant chest of information for the model to use. it's filled with everything about whatever you're making: keywords, tiered keywords, associated words, anti-keywords, natural language descriptions, SEO and search vocabulary, inspiration, colors, patterns, references, sources, anything at all like that. you make it once from a prompt (plus reference photos or files if you have them) and then the model, or any other skill, tool or subagent, can go back to it whenever it needs to.

## where the idea came from

people keep saying "AI is a glorified search engine." so i turned it on its head and asked myself "what if we actually treated AI like a search engine?" search engines work because everything is indexed with structured metadata, so give the model that.

i also believe that at its simplest AI is a prediction engine. it takes an input and predicts an output. a short prompt is a tiny input, so the model fills every gap with the most typical guess it can make. a meta dump makes the input way bigger and way more specific, so the prediction gets better.

before this i was making meta dumps by just asking an agent to make one from a text prompt (and sometimes photos). this skill does that, but better, and it isn't only for design. it works for actual development too: coding, TDD, engineering, writing, whatever you're doing.

## what makes it actually work

- **every entry says where it came from.** `user_stated` > `reference_observed` > `researched` > `inferred` > `proposed`, plus `unknown`. so the model can tell the difference between what i actually asked for and what it made up. a build script enforces it too: a subagent can't claim it researched something it didn't, and anything marked user_stated has to quote my actual prompt.
- **tiers.** 1 is defining (12 max, so it doesn't drown in rules), 2 supporting, 3 contextual, 4 exploratory ideas it can pull from but doesn't have to follow.
- **anti-keywords.** the opposite of a keyword. something to tell the model "this is not what i mean" (like "acrylic" means clear plastic here, not acrylic paint) or just stuff we don't want. every one comes with an `instead`, because a lot of image models (FLUX.2, gpt-image, Gemini) don't even have negative prompts, so the only way to say no is to say what to do instead.
- **it indexes itself.** there's a routing table at the top that maps each job ("write the image prompt", "pick the next test", "build the landing page") to the exact JSON paths it needs, with token costs. there's a word index like a real search engine has, and every entry is on one line so grep works. the model never loads the whole thing. loading a 100K token file all at once actually makes the output worse, so it only pulls the slice it needs for the step it's on.
- **no template.** the sections get designed for whatever you're making. a REST API dump doesn't get a color palette and a packaging dump doesn't get an error model.
- **ticket-driven.** it charts a map of what the dump needs to answer, then hands out tickets (research, specialists, anti-keywords, cleanup, synthesis, dry-run checks) to subagents, either through the Workflow tool (works with ultracode) or regular subagents. then a script validates everything, builds the index and writes the final file.

## install

```bash
claude plugin marketplace add globalanomalyindex/metadump
claude plugin install metadump@metadump
```

## use

just ask for one: "make a metadump for ..." and attach photos or files if you have them. say "lite" if you want it fast or "deep" if you want everything.

heads up, it isn't cheap. my first lite run took about 1.36M tokens and 34 minutes because every subagent reads a lot. standard is probably 2–4M tokens and about an hour.

it saves to `metadumps/<slug>.metadump.json` in your project (scratch work goes in `metadumps/.work/`, you can delete that whenever).

once a dump exists you don't have to do anything. any skill working in that project reads the top of the dump, pulls the slice for the step it's on, checks its work against it, and writes new decisions back into it.

## example

[`examples/metadumps/luminous-translucency.metadump.json`](examples/metadumps/luminous-translucency.metadump.json) is a lite run on my luminous chromatic translucency prompt: 217 entries, 43 anti-keywords, 16 researched facts with real links, a ready-to-paste image prompt, and open questions with defaults for the stuff the prompt didn't decide.

## what's in here

```
.claude-plugin/              plugin + marketplace manifest
skills/metadump/
  SKILL.md                   how the skill works (create mode + use mode)
  references/                the full procedure, worker briefs, format, mechanisms, export rules
  scripts/finalize.py        builds and checks the dump (python 3.9+, no installs)
  scripts/index.workflow.js  the subagent fan-out for the Workflow tool
  evals/                     test prompts
tests/                       tests for finalize.py and the workflow script
examples/metadumps/          dumps made with this
GLOSSARY.md, docs/adr/       the words and decisions behind it
```

## dev

```bash
python3 -m unittest discover -s tests
node --test tests/workflow.test.mjs
claude plugin validate .
```

## license

MIT

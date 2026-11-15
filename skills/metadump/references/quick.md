# Quick mode: a meta dump in one pass

The lightest way to make a meta dump, and the idea the skill started from. A model doesn't know what it knows until it writes it out. So before the task, you write it out yourself: one JSON file of what you know that bears on this task, from the broad down to the specific. Then you do the task with that file in front of you.

No agents and no research: it takes about a minute and a few thousand tokens. Use it when the user asks for a quick, fast or light meta dump. The full build (`create.md`) collects from the web, references and video, and checks itself; in test 23 a quick dump kept about 70% of the full build's gain over the prompt alone (ADR 0021). `<SKILL>` is the folder SKILL.md is in.

## 1. Write the dump, in one go

Before anything else, write `metadumps/<slug>.metadump.json` in the project. One pass, straight through, the way you'd empty your head onto paper. No helpers, no second draft. Lists of short phrases, not prose. About 2 to 4 thousand tokens.

If the user gave you references (a page, an image, a video, a file), read them first and put what you observe under `collected`, with where each thing came from, apart from what you write from memory.

Branch downward, three levels:

1. **The disciplines** the task belongs to (for a button: interaction design, visual design, motion, accessibility, front-end code), and for each one what its practitioners work by.
2. **The thing itself:** what kind of thing it is, the parts that make it that thing, what people expect of it.
3. **This task's specifics**, area by area in the domain's own words (shape, colour, material, motion, states, copy; or seams, data, errors, edge cases).

At each level, write what someone good at this would know:

- **keywords** in tiers: 1 is the user's own words and what the task can't do without, 2 is what a good version has, 3 is the specialist's term and the unexpected.
- **descriptions:** properties, behaviours (what causes what), and the principle behind them.
- **steps** they take, **tricks** they've learned that beginners haven't, and **tests** they use to check their own work.
- **tokens:** concrete values, each as a range or a few options ("radius 12 to 20 px", "settle in 300 to 600 ms"). Never one setting, and never the finished thing itself.
- **anti_keywords:** the worn defaults and the ways this goes wrong, each with what to do instead. The instead goes further in the user's direction, never tamer.

A shape to start from. Rename and add sections wherever the domain has better words:

```json
{
  "request": "the user's words, verbatim",
  "thesis": "one sentence: what is interesting about this thing",
  "job": ["every step the person using the result goes through, end to end"],
  "disciplines": {"<discipline>": {"principles": [], "steps": [], "tricks": [], "tests": []}},
  "the_thing": {"parts": [], "expectations": [], "kinds": [{"name": "", "what": ""}]},
  "specifics": {"<area>": {"keywords": {"1": [], "2": [], "3": []}, "descriptions": [], "behaviors": [], "tokens": {}}},
  "anti_keywords": [{"not": "", "instead": ""}],
  "checks": ["a test from above, as something you can run or ask of the finished work"],
  "built": []
}
```

Four things the dump must not get wrong:

- **The user's words stay as they wrote them.** Nothing in the dump narrows or redefines the request. If the request has a size word (simple, basic, minimal, small, short), write what that word rules out as anti-keywords: a basic calculator has no history, no memory keys, no scientific functions.
- **Cover the whole job.** `job` lists everything the person does with the result from start to finish.
- **`kinds` are versions of the thing that people make** (a ring timer, a bare-number timer), the classic one first. Not camera angles, not moods.
- **It is a resource, not a rulebook.** It holds more than you'll use. Nothing in it is an order except the user's words.

## 2. Do the task with it

Build the classic kind, made with the best of what you wrote, unless the user asked for something else. If the dump already has kinds in `built`, take the first kind that isn't there. Add the kind you built to `built`.

A size word caps the build. The dump holds more than fits, so leave out whatever the person wouldn't miss. Cover every step of `job`, and nothing past it.

Then ask your own `checks` of what you made, and fix what fails.

## 3. Look at what you made

This step is part of the task. If the result renders in a browser, run the look:

```bash
python3 <SKILL>/scripts/look.py <your file.html>
```

It opens the page in a headless browser, screenshots it at desktop and phone widths, uses it the way a person would (clicks, types, drags, tabs through it), and prints what broke and what the page said. Fix what it lists. Then read the desktop and phone screenshots it names with the Read tool: would a stranger name what the user asked for at a glance, and does it read as their words at full strength? Fix what you see and look again.

Two more looks, when they apply:

- **Behaviour:** run a check as a scripted play. `--play "click #k7; click #plus; click #k8; click #equals; expect 15"` presses the keys and tells you what the page said instead if it wasn't 15.
- **Anything that runs on its own:** look once more after it has run a while. `--play "wait 20000"` waits twenty seconds and saves `play-1.png`. Is it still doing what it did at the start? A page looks fine in its first second and can run down by its twentieth.

If there is no browser the look says so; carry on.

## 4. Reuse it

If a quick dump for this task already exists, read it instead of writing a new one. `python3 <SKILL>/scripts/deal.py <dump>` tells you which kind to build next: the first one not in `built`. Add what you learn to the file: a trick that worked, a check that caught something, the kind you built.

A quick dump has no manifest, routes or index, so the rest of use mode (the hand, the routes, `jq` slices) does not apply to it: it is small enough to read whole. `python3 <SKILL>/scripts/finalize.py check <dump>` says what it holds.

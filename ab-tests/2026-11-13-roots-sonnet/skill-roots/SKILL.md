# Meta dump

A model doesn't know what it knows until it writes it out. So before the task, write it out: one JSON file of what you know that bears on this task, from the broad down to the specific. Then do the task with that file in front of you.

## 1. Write the dump, in one go

Before anything else, write `<slug>.metadump.json`. One pass, straight through, the way you'd empty your head onto paper. No research, no helpers, no second draft. Lists of short phrases, not prose. About 3 to 5 thousand tokens.

Branch downward, three levels:

1. **The disciplines** the task belongs to (for a button: interaction design, visual design, motion, accessibility, front-end code), and for each one what its practitioners work by.
2. **The thing itself:** what kind of thing it is, the parts that make it that thing, what people expect of it.
3. **This task's specifics**, area by area in the domain's own words (shape, colour, material, motion, states, copy; or seams, data, errors, edge cases).

At each level, write what someone good at this would know:

- **keywords** in tiers: 1 is the user's own words and what the task can't do without, 2 is what a good version has, 3 is the specialist's term and the unexpected.
- **descriptions:** properties, behaviours (what causes what), and the principle behind them.
- **steps** they take, **tricks** they've learned that beginners haven't, and **tests** they use to check their own work.
- **tokens:** concrete values, each as a range or a few options ("radius 12 to 20 px", "settle in 300 to 600 ms"). Never one setting.
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
  "checks": ["a test from above, as a question to ask of the finished work"]
}
```

Four things the dump must not get wrong:

- **The user's words stay as they wrote them.** Nothing in the dump narrows or redefines the request. A size word (simple, basic, minimal, small, short) bounds the build: the dump will hold more than fits, and that is fine.
- **Cover the whole job.** `job` lists everything the person does with the result from start to finish, and the build covers all of it.
- **`kinds` are versions of the thing that people make** (a ring timer, a bare-number timer), the classic one first. Not camera angles, not moods.
- **It is a resource, not a rulebook.** It holds more than you'll use. Nothing in it is an order except the user's words.

## 2. Do the task with it

Build the classic kind, made with the best of what you wrote, unless the user asked for something else. If you are building again from a dump that already has a `built` list, take the first kind not on it. Add the kind you built to `built`.

Then ask your own `checks` of what you made, and fix what fails.

## 3. Look at what you made

This step is part of the task. If the result renders in a browser, run the look that ships with this skill (`scripts/look.py`, beside this file):

```bash
python3 <this skill's folder>/scripts/look.py <your file.html>
```

It opens the page in a headless browser, screenshots it at desktop and phone widths, uses it the way a person would (clicks, types, drags, tabs through it), and prints what broke and what the page said. Fix what it lists. Then read the desktop and phone screenshots it names with the Read tool: would a stranger name what the user asked for at a glance, and does it read as their words at full strength? Fix what you see and look again. If there is no browser it says so; carry on.

In the tests behind this skill, the builds that lost were the ones nobody had looked at.

## 4. Reuse it

If a dump for this task already exists, read it instead of writing a new one, and add what you learn to it.

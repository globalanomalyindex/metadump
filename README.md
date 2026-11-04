# metadump

a claude code plugin that takes a prompt and turns it into a meta dump.

## what's a meta dump

a meta dump is what i call one big JSON file that's basically a giant chest of information for the model to use. it's filled with everything about whatever you're making: keywords, tiered keywords, associated words, anti-keywords, natural language descriptions, SEO and search vocabulary, inspiration, colors, patterns, references, sources, measurements, timings, transcripts, anything at all like that. you make it once from a prompt (plus reference photos, files, links or videos if you have them) and then the model, or any other skill, tool or subagent, can go back to it whenever it needs to.

it's not a rulebook though. the model doesn't have to obey it. it's a resource: the actual facts written down (exact values, real references, measurements, timings, stuff with sources) so the model has them on hand instead of guessing. my prompt and the model's own judgment still make the calls. making the dump is honestly half the point too, because it forces everything into structure and specifics.

i learned that one from my own A/B tests. the dump helped a lot when it had real facts in it, and it hurt when it had a wrong made-up number in it that the model followed instead of what i actually asked for.

## where the idea came from

people keep saying "AI is a glorified search engine." so i turned it on its head and asked myself "what if we actually treated AI like a search engine?" search engines work because everything is indexed with structured metadata, so give the model that.

i also believe that at its simplest AI is a prediction engine. it takes an input and predicts an output. a short prompt is a tiny input, so the model fills every gap with the most typical guess it can make. a meta dump makes the input way bigger and way more specific, so the prediction gets better.

before this i was making meta dumps by just asking an agent to make one from a text prompt (and sometimes photos). this skill does that, but better, and it isn't only for design. it works for actual development too: coding, TDD, engineering, writing, whatever you're doing.

## what makes it actually work

- **every entry says where it came from.** `user_stated` > `reference_observed` > `researched` > `inferred` > `proposed`, plus `unknown`. so the model can tell the difference between what i actually asked for and what it made up, and it reaches for the real stuff first. a build script enforces it too: a subagent can't claim it researched something it didn't, and anything marked user_stated has to quote my actual prompt. entries can also say how they were gotten (scraped, transcribed, measured from frames, sampled pixels).
- **tiers.** they're about relevance, not rules. 1 is what the task is most about (12 max), 2 supporting, 3 contextual, 4 exploratory ideas it can pull from. the builder's own guesses go in an options area so they don't get mistaken for requirements.
- **anti-keywords.** the opposite of a keyword. something to tell the model "this is not what i mean" (like "acrylic" means clear plastic here, not acrylic paint) or just stuff we don't want. every one comes with an `instead`, because a lot of image models (FLUX.2, gpt-image, Gemini) don't even have negative prompts, so the only way to say no is to say what to do instead.
- **it indexes itself.** there's a routing table at the top that maps each job ("write the image prompt", "pick the next test", "build the landing page") to the exact JSON paths it needs, with token costs. there's a word index like a real search engine has, and every entry is on one line so grep works. the model never loads the whole thing. loading a 100K token file all at once actually makes the output worse, so it only pulls the slice it needs for the step it's on.
- **no template.** the sections get designed for whatever you're making. a REST API dump doesn't get a color palette and a packaging dump doesn't get an error model.
- **ticket-driven.** it charts a map of what the dump needs to answer, then hands out tickets (research, finding videos and images online, scraping pages, watching videos, moodboards, specialists, anti-keywords, cleanup, synthesis, dry-run checks) to subagents, either through the Workflow tool (works with ultracode) or regular subagents. the dry runs also look for numbers in the dump that fight with what i asked for. then a script validates everything, builds the index and writes the final file.

## pages, videos and images

new in 0.2.0. when it's making a dump it can go get the specifics itself, with nothing to install:

- **pages.** give it a link and it fetches the page, cleans it into text with the headings kept, chops it into chunks and pulls facts out with a short quote and exactly where it found it. it checks robots.txt and waits between requests so it isn't rude.
- **videos.** give it a video link or a video file and it grabs the title, length, fps, chapters and caption tracks, turns captions into a clean transcript with timecodes, pulls frames at whatever times you want, and can measure animation timing: how long each move takes, where it holds, if it's animated on twos, and roughly what easing it uses.
- **images.** it collects my reference photos plus images from pages and video frames, samples the actual colors, and makes a moodboard page right next to the dump.
- **finding stuff on its own.** new in 0.3.0. if i don't give it references (or mine don't cover something, like how a thing moves or how long an animation takes), it goes and looks for videos, images and pages that would show it, then watches, scrapes and collects the best few. there's a cap so it doesn't go crazy (lite grabs 1 video, 1 page and 6 images, standard 3, 3 and 12, deep 5, 6 and 24), it tells you what it skipped because of the cap, and anything it found itself is marked as found online, not as mine. the build script enforces that part, so a subagent can't pass something it found off as my reference. if you only want it to use your stuff, just say so.

it all runs on plain python plus the chrome (or chromium, edge, brave) you already have, driven headless. if you happen to have yt-dlp or ffmpeg it'll use them, but you don't need them. `python3 skills/metadump/scripts/tools.py` shows what it found.

it won't get around logins, age gates, paywalls or anything like that, and downloading from places like youtube can be against their terms, so it sticks to metadata, captions and sampled frames. heads up: right now youtube won't give captions or play past the first few seconds for a headless browser, so for youtube it tells you that and you can install yt-dlp or hand it a caption file. local video files work fine. when it's finding videos on its own it goes for ones it can actually read (direct video files, like the originals on wikimedia commons, or the maker's own site) over youtube.

## install

```bash
claude plugin marketplace add globalanomalyindex/metadump
claude plugin install metadump@metadump
```

## use

just ask for one: "make a metadump for ..." and attach photos or files, or paste links to pages or videos, if you have them. say "lite" if you want it fast or "deep" if you want everything.

heads up, it isn't cheap. my first lite run took about 1.36M tokens and 34 minutes because every subagent reads a lot. standard is probably 2–4M tokens and about an hour.

it saves to `metadumps/<slug>.metadump.json` in your project (scratch work goes in `metadumps/.work/`, you can delete that whenever).

once a dump exists you don't have to do anything. any skill working in that project reads the top of the dump, pulls the slice for the step it's on, uses what helps, and writes new decisions back into it.

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
  scripts/webpages.py        fetches and cleans pages
  scripts/video.py           video info, captions, frames and timing
  scripts/images.py          collects images, samples colors, makes the moodboard
  scripts/tools.py           shows which optional tools you have
  scripts/cdp.py, pixels.py  the headless chrome driver and png decoder (plain python)
  evals/                     test prompts
tests/                       tests for all of it (one of them drives your chrome if you have it)
examples/metadumps/          dumps made with this
GLOSSARY.md, docs/adr/       the words and decisions behind it
docs/clean-room/             how the page scraper got written without copying anyone
```

## dev

```bash
python3 -m unittest discover -s tests
node --test tests/workflow.test.mjs
claude plugin validate .
METADUMP_LIVE=1 python3 -m unittest discover -s tests   # also hits the real internet
```

## license

MIT

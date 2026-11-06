# Spreads, not settings: the dump never settles a choice


A/B test 12 (`ab-tests/2026-11-05-three-tasks-haiku-medium/results.md`, unpublished) ran 0.8.0 (ADR 0012) on three tasks with every agent on Haiku at medium effort. The dump side won the toast 24 of 24 and led the button. Its builds were more varied, and the dump haiku spread across four different clouds. Two failures came from one cause.

- **The buttons pasted the dump's curves.** All four dump builds used the same four `cubic-bezier` values.
  - The builders never opened the export verify had flagged. They read the `motion` section.
  - Its curve facets said "several curves can carry it", but each one's `tokens.curve` held exactly one value. With one facet per role (drift, bloom, lift, leave), the section was a filled-in sheet.
  - Durations came as ranges, and the builders varied them. Curves came as single values, and the builders copied them.
- **The haiku dropped 5-7-5.** Three of four dump haiku broke the form and lost on form 5.58 vs 9.42.
  - The dump's `open_questions` gave the form a default ("English short-long-short lines with one cut").
  - Its facets argued one side ("a strict 5-7-5 in English tends to pad or cram the lines"; "the count is a choice").
  - Verify flagged the default as a narrowing; lite's one widening round didn't reach it. The builders took the dump's side.
- **Nobody played.** The 0.8.0 use mode says to roll a die when torn and to sketch variations. None of the eight dump builds ran a random pick or sketched anything. They read the sections and wrote. The dump's shape steers; its instructions barely do.

The owner's principle: the dump should help the model expand on what it would otherwise miss, throwing more into the pot to play with. The model shouldn't want to adhere to it; it should want to use it for more areas of exploration.

We decided:
- **The dump never settles a choice the work has to make.** It lays out the space, and the consumer makes the choice.
  - **Values come as spreads.** A creative value (a curve, a colour, a duration, a size, a count, a form) is offered as a range or as several values spread far apart across the space, each with what it does. It's never one value. Measured and sourced values are facts and stay exact. finalize warns when a build's own illustrative token holds one curve or one colour (`single_setting`).
  - **No defaults on creative choices.** `open_questions` defaults are for technical parameters the work can't proceed without (language, framework, currency). They never pick a form, a style, a subject, a reading, or anything the user's words already name. ADR 0010 said this for the deliverable and quality readings; it now covers everything creative.
  - **No sides.** Where practitioners disagree (5-7-5 or free count in English haiku), the dump gives both views with who holds them, not a verdict.
- **The user's words stay exactly as wide as the user wrote them.** The dump explores around them. It never narrows them (ADR 0005) or loosens them. A form word carries its common convention as material: "haiku" usually means three lines of 5-7-5 in English, with known variations. A dump that defaults away from that convention has redefined the user's word. Verify's definition pass reports it as a narrowing of kind `definition`.
- **Use mode: explore from the dump, never match it.**
  - The dump is there to show corners you'd otherwise miss.
  - A value you take from it is where you start turning the dial, not where you stop.
  - A set you find in it is one sample of a space, so make your own.
  - Copying a value or an option verbatim is the sign to go further.
  - The review questions come after the work, not before it.
  - Worn paths are places not to stop, not rules.
- **The test harness leaves the reading order to the skill.** Test 13's dump-arm prompt says only "use it the way Use mode describes". Tests 10 to 12 summarised the old reading order ("anti-keywords and checks"), which put the review questions up front.

We rejected:
- dropping concrete values from dumps, because exact specifics (a researched curve family, a measured timing, a contrast ratio) are much of the dump's value. They come as spreads instead.
- leaving it to use mode alone, because test 12 showed the instructions to play were read and not followed. The dump's shape has to make copying impossible: there has to be no single value to copy.
- making the convention of a form word a rule, because that would be the dump settling it the other way. It's material: the convention and its variations, with no default.
- removing scope readings' default (ADR 0005), because it covers the user's whole job (test 5) rather than a creative choice. The default reading stays, written as where the whole job is covered.

## Consequences

- Dumps get slightly bigger (a few values where there was one) and a little harder to write. finalize names every single setting.
- Builds that read the same dump should vary their values as well as their subjects. Test 13 counts how many dump builds reuse a dump value verbatim.

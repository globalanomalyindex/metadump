# The look plays the page

ADR 0018 ended use mode with a look: render the page, screenshot it, list what a reviewer would see. It turned test 16's 27–39 loss into test 18's 57–8, the largest single gain in this project's tests. It only ever saw a page at rest, with one control hovered and one toggle opened.

Test 19 showed what that misses. Five of the eight tic tac toe games had rows that changed height once marks landed. The look reported none of them, the four dump builders ran it once and opened none of its screenshots, and two of those games shipped with the bug. Reading every grader note from tests 18 and 19, most of the points lost on either side were of this kind, defects that only show once someone uses the page or opens it on a phone:

- cells that change size during play (five games);
- a label that washes out partway through its hover (test 18's buttons);
- a timeline clipped only once the toast is opened;
- a control panel that sits beside the model on a laptop and on top of it on a phone (test 19's lemons);
- focus rings that exist in the CSS and never show.

The dumps were already describing the behaviour. The tic tac toe dump's review questions include "Play X 0, O 1, X 2, O 4, X 3, O 5, X 7, O 6, X 8; the status reads a draw". Nothing ran them.

We decided:
- **The look plays the page.** After the screenshots, `look.py` walks the page at desktop and phone widths from a fresh load (`play.py`): it finds what a person could act on (buttons, links to anchors, inputs, sliders, selects, anything with a pointer cursor, a canvas to drag), acts on each once in page order with reset-like controls last, and tabs through the page.
- **It checks invariants, not expectations.** After every action it checks things that hold for any page: no script error; siblings that matched in size still match unless the one acted on opened; nothing newly clipped, cut off or overlapping; the label of the hovered control stays readable through the transition; keyboard focus shows and never lands on something hidden; what answers a click can be reached with Tab; the main visual isn't covered on a phone when it wasn't on a laptop; endless motion asks about reduced motion. A page where nothing responds at all is reported; one control that does nothing is not, since it can be right in that state.
- **Every finding names the action that brought it out**, so the builder can reproduce it.
- **It tells what happened in words.** The walk prints a short account ("clicked 7 of the 9 matching controls in #board: the page said …, "X wins"") so a builder can check the user's job against it without opening an image. Builders act on the printed list far more reliably than on screenshots.
- **One sheet, as an overview.** Every state is laid out on one labelled image, composed by the browser. The look still tells the builder to read the desktop and phone shots at full size: the sheet shows what the walk reached, and it is too small to judge a drawing by.
- **Scripted plays.** `--play "click SEL; type TEXT into SEL; press KEY; expect TEXT"` runs steps from a fresh load, holds them to the same invariants, and reports an `expect` that fails with what the page said instead. A review question that gives steps can now be run. Synthesis writes two or three such questions for anything a person uses.
- **Findings stay things to look at** (ADR 0018). Nothing gates finishing.

We rejected:
- reporting every control that changes nothing: on test 18's toasts that flagged a pager dot for the parcel already showing and a "bring back" button with nothing to bring back;
- scanning the output for the dump's worn paths: across 40 past builds the scan found one hit;
- printing the dump's signals beside the screenshots: the dumps that needed them most (the lemon's) had none that applied to the rendered page;
- counting syllables for verse: without a pronunciation dictionary the count is wrong often enough to break a correct line;
- judging "does it look like a lemon" mechanically. The look asks instead whether a stranger would name what the user asked for.

## What it finds on past builds

Run over the 32 pages of tests 18 and 19 (no model involved):

- `uneven` on exactly the five tic tac toe games the graders marked for squashed rows, and on none of the three with a steady board;
- `covered` on two prompt-only lemons whose panels the graders said hide the model on phones;
- `washed-out` on a prompt-only button whose label the graders said washes out;
- `focus-static` on toasts that set a focus outline an ancestor's `overflow: hidden` clips away, which graders reading the code had praised, and `focus-hidden` on toasts whose collapsed panel still takes keyboard focus.

## What test 20 found (2026-11-12)

- **Nothing for or against the playing checks.** On test 20's timer and snow globe, 0.13.0's look found no playing defect in any timer of any arm and two in one 0.12.0 snow globe. All twelve timers worked. The builds that lost did so on what they were, not on what broke, and no check here judges that. The evidence for the playing checks is still the past builds above.
- **The sheet had replaced reading.** The first version told builders to read the sheet. On the snow globe, 0.13.0's builders opened one to three images where 0.12.0's opened one to seven full-size shots, and scored lower on visuals. The closing line now sends them to the full-size shots.
- **A gap:** in test 21 a timer shipped with its clock shrunk to body-text size by one inherited CSS rule. The builder looked twice and read three screenshots. No check asks whether the thing the request names is the main thing on the page.

## Consequences

- A look takes 10 to 30 seconds instead of 5.
- `play.py` joins the scripts; it is used through `look.py` and stays standard library only.
- Seam S14 covers the walk, the checks, scripted plays and the sheet, against the real local browser.
- A task with behaviour to get wrong is still needed to measure what the playing checks add.

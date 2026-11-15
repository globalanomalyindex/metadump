#!/usr/bin/env python3
"""Every prompt this test sends, so each agent is launched from recorded text.
Usage: python3 prompts.py build <task> <run> | grade <task> <block> <judge> | variety <task> <grader> | dump <task>"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = {"B": os.path.join(HERE, "skill-prev", "skills", "metadump"), "C": os.path.normpath(os.path.join(HERE, "..", "..", "skills", "metadump"))}
TASKS = {"t1-fieldguide": "a field guide entry for a dragon", "t2-pomodoro": "a simple pomodoro timer", "t3-snowglobe": "a snow globe"}
EXT = {"t1-fieldguide": "md", "t2-pomodoro": "html", "t3-snowglobe": "html"}


def dump_path(task, arm):
    folder = os.path.join(HERE, task, "metadumps" if arm == "C" else os.path.join("prev", "metadumps"))
    found = glob.glob(os.path.join(folder, "*.metadump.json"))
    assert len(found) == 1, (folder, found)
    return found[0]


def build(task, run):
    arm, out = run[0], os.path.join(HERE, task, "runs", "%s.%s" % (run, EXT[task]))
    if EXT[task] == "md":
        first = "Task: %s\n\nWrite your answer as markdown to %s: exactly what you would reply to the user, nothing else. Write only that file." % (TASKS[task], out)
    else:
        first = ("Task: %s\n\nDeliver it as one self-contained HTML file at %s. Inline CSS and JS only; no external requests (no CDNs, libraries, "
                 "web fonts or remote images); it must work when opened from disk. Interactions must actually update state. Write only that file." % (TASKS[task], out))
    if arm == "A":
        return first + " Don't invoke any skills and don't read other files in this repo: work from the task alone. When done, reply with one line: the file path."
    return first + ("\n\nA meta dump for this task is at %s (one large JSON file of collected specifics for this task). Use it the way %s/SKILL.md "
                    "\"Use mode\" describes (details in references/use.md next to it). Don't invoke any skills; read those files directly, and read "
                    "no other files in this repo. When done, reply with one line: the file path." % (dump_path(task, arm), SKILL[arm]))


RUBRIC = {
    "t1-fieldguide": [("imagination", "inventive and playful; it takes the idea somewhere"),
                      ("fieldguide", "it works as a field guide entry: how to identify it, range and habitat, behaviour, similar species, status; compact and usable"),
                      ("specificity", "concrete, consistent natural history (anatomy, ecology, measurements), true to the lore it draws on"),
                      ("voice", "a pleasure to read; the tone fits the form"),
                      ("freshness", "avoids the obvious jokes and stock phrasing"),
                      ("overall", "holistic quality as a response to the task, including its length (helpful or padding)")],
    "t2-pomodoro": [("simple", "it is a simple pomodoro timer, as asked: complete and simple, not overbuilt or padded"),
                    ("correctness", "it counts down accurately, start, pause and reset work, it moves between work and break when a session ends, no drift or double timers"),
                    ("usability", "the time and the current mode are clear at a glance; keyboard and screen reader; works on a phone"),
                    ("craft", "polish, hierarchy, colour, type, spacing, feedback, phone layout"),
                    ("code", "small, clear, readable source"),
                    ("overall", "holistic quality as a response to the task")],
    "t3-snowglobe": [("likeness", "unmistakably a snow globe: a glass dome on a base, a scene inside, snow"),
                     ("visuals", "the glass, light and depth, and the scene inside; the craft of the drawing"),
                     ("motion", "snow that falls and settles believably; a shake or other interaction that feels right"),
                     ("presentation", "staging, polish, restraint, phone layout"),
                     ("overall", "holistic quality as a response to the task")],
}
SEES = {
    "t2-pomodoro": ("For each label U, V, W, X, Y, Z there are: <label>-desktop.png (1280x800) and <label>-mobile.png (390x844), the page at rest; "
                    "<label>-use.png, frames of a scripted use (at rest, 2 s and 4 s after pressing start, just after pressing pause, 1.6 s later, after "
                    "pressing reset); and <label>.html, the source. Look at all the images with the Read tool and read the source (check the countdown, "
                    "pause and reset, what happens when a session ends, keyboard and screen-reader support)."),
    "t3-snowglobe": ("For each label U, V, W, X, Y, Z there are: <label>-desktop.png (1280x800) and <label>-mobile.png (390x844), the page at rest; "
                     "<label>-shake.png, frames over 1.4 s untouched, then just after three quick drags across the globe (a shake), 0.4 s and 1.5 s "
                     "later, and after a click on it; and <label>.html, the source. Look at all the images with the Read tool and skim the source "
                     "(how the globe, the scene and the snow are drawn; what the interaction does)."),
}


def grade(task, block, judge):
    folder = os.path.join(HERE, task, "blind", block, judge)
    out = os.path.join(HERE, task, "judgments", "%s-%s.json" % (block, judge))
    crit = RUBRIC[task]
    fields = ", ".join('"%s": n' % c for c, _ in crit)
    if EXT[task] == "md":
        head = ("You are grading six responses blind. Writers were given this task: \"%s\". Each delivered a markdown reply.\n\nFolder: %s\n"
                "Read U.md, V.md, W.md, X.md, Y.md and Z.md. Judge each on its own merits; labels are random." % (TASKS[task], folder))
    else:
        head = ("You are grading six designs blind. Designers were given this task: \"%s\". Each delivered one self-contained HTML file "
                "(no libraries allowed).\n\nFolder: %s\n%s Judge each on its own merits; labels are random." % (TASKS[task], folder, SEES[task]))
    return (head + "\n\nScore each 0-10 on:\n" + "\n".join("- %s: %s" % c for c in crit) +
            "\n\nWrite exactly one file, %s, as:\n{\"block\": \"%s\", \"judge\": \"%s\", \"scores\": {\"U\": {%s, \"note\": \"one sentence\"}, \"V\": {...}, "
            "\"W\": {...}, \"X\": {...}, \"Y\": {...}, \"Z\": {...}}, \"ranking\": [\"best label\", \"...\", \"...\", \"...\", \"...\", \"worst label\"]}\n"
            "Don't invoke skills and don't read anything outside that folder. Reply with one line: the file path." % (out, block, judge, fields))


DIFFERS = {"t1-fieldguide": "different species or kinds of dragon, framings, structures, registers, tones",
           "t2-pomodoro": "different layouts, visual treatments, ways of showing time and mode, sets of controls, interaction",
           "t3-snowglobe": "different scenes inside, drawing or rendering approaches, compositions, moods, interactions"}


def variety(task, grader):
    folder = os.path.join(HERE, task, "variety", grader)
    out = os.path.join(HERE, task, "judgments-variety", "%s.json" % grader)
    if EXT[task] == "md":
        what, see = "responses", "Set P is P1.md to P4.md, set Q is Q1.md to Q4.md and set R is R1.md to R4.md. Read all twelve."
        made = "one response written four times"
    else:
        strip = "use" if task == "t2-pomodoro" else "shake"
        what = "designs"
        see = ("Set P is P1 to P4, set Q is Q1 to Q4 and set R is R1 to R4. For each there is <label>-desktop.png (the page at rest), <label>-%s.png "
               "(frames of it in use) and <label>.html (the source). Look at all the images with the Read tool and skim the sources." % strip)
        made = "one design made four times"
    return ("You are comparing three sets of four %s for variety. %s were given this task: \"%s\". Each set came from one process, and the three "
            "sets came from different processes.\n\nFolder: %s\n%s\n\nJudge only how varied each set is, not how good the %s are: are these four "
            "genuinely different takes (%s), or %s? Score each set 0-10 for variety (10 = four genuinely different takes; 0 = the same thing four "
            "times).\n\nWrite exactly one file, %s, as:\n{\"grader\": \"%s\", \"variety\": {\"P\": n, \"Q\": n, \"R\": n}, \"most_varied\": \"P\" or \"Q\" "
            "or \"R\" or \"tie\", \"note\": \"one or two sentences on what repeats or differs within each set\"}\n"
            "Don't invoke skills and don't read anything outside that folder. Reply with one line: the file path."
            % (what, "Writers" if EXT[task] == "md" else "Designers", TASKS[task], folder, see, what, DIFFERS[task], made, out, grader))


if __name__ == "__main__":
    kind = sys.argv[1]
    print({"build": build, "grade": grade, "variety": variety}[kind](*sys.argv[2:]))

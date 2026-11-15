#!/usr/bin/env python3
"""Every prompt this test sends, so each agent is launched from recorded text.
Usage: python3 prompts.py build <task> <run> | grade <task> <block> <judge> | variety <task> <grader> | dump <task>"""
import glob, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOTS = os.path.join(HERE, "skill-roots", "SKILL.md")
TASKS = {"t1-lavalamp": "a lava lamp", "t2-calculator": "a basic calculator"}
EXT = {"t1-lavalamp": "html", "t2-calculator": "html"}


def build(task, run):
    """Only the R arm is built here; A and C are test 22's files."""
    arm, out = run[0], os.path.join(HERE, task, "runs", "%s.%s" % (run, EXT[task]))
    assert arm == "R", run
    dump = os.path.join(HERE, task, "dumps", "%s.metadump.json" % run)
    first = ("Task: %s\n\nDeliver it as one self-contained HTML file at %s. Inline CSS and JS only; no external requests (no CDNs, libraries, "
             "web fonts or remote images); it must work when opened from disk. Interactions must actually update state." % (TASKS[task], out))
    return first + ("\n\nBefore you build, follow %s, every step (the scripts folder beside it is part of the skill): write your meta dump to %s "
                    "first, then do the task with it. Write only those two files. Don't invoke any skills; read that file directly, and read "
                    "no other files in this repo. When done, reply with one line: the HTML file path." % (ROOTS, dump))


RUBRIC = {
    "t1-lavalamp": [("likeness", "unmistakably a lava lamp: a glass vessel on a base with a cap, blobs of wax in liquid, lit from below"),
                    ("visuals", "the glass, the glow, the wax and the liquid; the craft of the drawing"),
                    ("motion", "wax that rises, stretches, merges, splits and sinks believably, slow and organic; any interaction feels right"),
                    ("presentation", "staging, polish, restraint, phone layout"),
                    ("overall", "holistic quality as a response to the task")],
    "t2-calculator": [("basic", "it is a basic calculator, as asked: complete and basic, not overbuilt or padded"),
                      ("correctness", "the arithmetic is right; chained operations, decimals, dividing by zero and long numbers are handled; clear works"),
                      ("usability", "the keys and the display are clear at a glance; keyboard and screen reader; works on a phone"),
                      ("craft", "polish, hierarchy, colour, type, spacing, feedback, phone layout"),
                      ("code", "small, clear, readable source"),
                      ("overall", "holistic quality as a response to the task")],
}
SEES = {
    "t1-lavalamp": ("For each label U, V, W, X, Y, Z there are: <label>-desktop.png (1280x800) and <label>-mobile.png (390x844), the page at rest; "
                    "<label>-motion.png, frames of it untouched at 0, 2, 4 and 6 s, then 0.5 s and 2.5 s after a click on the lamp, then 0.5 s and "
                    "2.5 s after pressing its first control (if it has one); and <label>.html, the source. Look at all the images with the Read "
                    "tool and skim the source (how the lamp, the wax and the glow are drawn; how the wax moves; what the interaction does)."),
    "t2-calculator": ("For each label U, V, W, X, Y, Z there are: <label>-desktop.png (1280x800) and <label>-mobile.png (390x844), the page at rest; "
                      "<label>-use.png, frames of a scripted use (12 + 7 =, then 0.1 + 0.2 =, then 8 ÷ 0 =, then clear and the 9 key pressed 20 times, "
                      "then clear), each captioned with what was pressed; and <label>.html, the source. Look at all the images with the Read tool "
                      "and read the source (check chained operations, decimals, dividing by zero, long numbers, clear, keyboard and screen-reader "
                      "support)."),
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


OPEN = {"t1-lavalamp": "the kind of lamp, its colours and mood, how it is drawn, the staging, the interaction",
        "t2-calculator": "the visual style, the layout's details, how the display reads, small extras that stay within basic"}
FIXED = {"t1-lavalamp": "it is unmistakably a lava lamp: a glass vessel on a base with a cap, blobs of wax moving in liquid, lit from below",
         "t2-calculator": "it is a basic calculator: digits, the four operations, equals, clear and a display, laid out the way calculators are, "
                          "with correct arithmetic, and no more than basic"}


def variety(task, grader):
    """Variety in what the task leaves open, and separately how many builds break what it fixes (the owner's point, 2026-11-13:
    where a task has rules or standards, builds agreeing on them is a benefit, not sameness)."""
    folder = os.path.join(HERE, task, "variety", grader)
    out = os.path.join(HERE, task, "judgments-variety", "%s.json" % grader)
    strip = "use" if task == "t2-calculator" else "motion"
    see = ("Set P is P1 to P4, set Q is Q1 to Q4 and set R is R1 to R4. For each there is <label>-desktop.png (the page at rest), <label>-%s.png "
           "(frames of it in use) and <label>.html (the source). Look at all the images with the Read tool and skim the sources." % strip)
    return ("You are comparing three sets of four designs. Designers were given this task: \"%s\". Each set came from one process, and the three "
            "sets came from different processes.\n\nFolder: %s\n%s\n\nA task fixes some things and leaves others open.\n- Fixed by this task: %s.\n"
            "- Left open: %s.\n\nJudge two things per set, and not how good the designs are otherwise.\n1. variety (0-10): how different the four "
            "are from each other in what the task leaves open (10 = four genuinely different takes; 0 = one design made four times). A difference "
            "that breaks what the task fixes is not variety: leave it out of this score.\n2. breaks (0-4): how many of the four break what the task "
            "fixes.\n\nWrite exactly one file, %s, as:\n{\"grader\": \"%s\", \"variety\": {\"P\": n, \"Q\": n, \"R\": n}, \"breaks\": {\"P\": n, "
            "\"Q\": n, \"R\": n}, \"most_varied\": \"P\" or \"Q\" or \"R\" or \"tie\", \"note\": \"one or two sentences on what repeats or differs "
            "within each set, and which designs break what is fixed and how\"}\n"
            "Don't invoke skills and don't read anything outside that folder. Reply with one line: the file path."
            % (TASKS[task], folder, see, FIXED[task], OPEN[task], out, grader))


if __name__ == "__main__":
    kind = sys.argv[1]
    print({"build": build, "grade": grade, "variety": variety}[kind](*sys.argv[2:]))

"""Tests for skills/metadump/scripts/look.py, seam S14 (run: python3 -m unittest discover -s tests).
The look renders a built page in the local headless browser and reports what a grader would see (ADR 0018).
Skipped when no Chromium-family browser is installed or it cannot be launched here."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
sys.path.insert(0, SCRIPTS)

import cdp  # noqa: E402
import look  # noqa: E402
import pixels  # noqa: E402
import tools  # noqa: E402

LOOK = os.path.join(SCRIPTS, "look.py")

# Test 16's dump toasts: a timeline clipped mid-row, a close icon over the chevron, rows that wrap.
BROKEN_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;font:14px sans-serif}
#card{position:fixed;right:16px;bottom:16px;width:280px;background:#222;color:#eee;padding:12px}
#list{height:40px;overflow:hidden}
#list p{margin:0;line-height:20px}
#head{position:relative;height:32px}
#chevron,#close{position:absolute;top:4px;right:8px;width:24px;height:24px;border:0;background:#555;color:#fff}
#wide{width:600px;height:10px;background:#444}
</style></head><body>
<div id="card">
  <div id="head"><button id="chevron" aria-expanded="false">v</button><button id="close">x</button></div>
  <div id="list"><p>Ordered</p><p>Packed</p><p>Handed to the carrier</p><p>Out for delivery</p></div>
  <div id="wide"></div>
</div></body></html>"""

# Test 16's B-r2 toast: a scrolling timeline whose last visible row was cut in half at the box's edge.
SCROLLING_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;font:14px sans-serif}
#log{width:200px;max-height:50px;overflow:auto;margin:20px;padding:0;list-style:none}
#log li{height:20px;line-height:20px;margin:0}
#tidy{width:200px;max-height:40px;overflow:auto;margin:20px;padding:0;list-style:none}
#tidy li{height:20px;line-height:20px;margin:0}
</style></head><body>
<ol id="log"><li>Ordered</li><li>Packed</li><li>Handed over</li><li>Out for delivery</li></ol>
<ol id="tidy"><li>One</li><li>Two</li><li>Three</li><li>Four</li></ol>
</body></html>"""

CLEAN_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;font:14px sans-serif;background:#fff}
#card{position:fixed;right:16px;bottom:16px;width:240px;background:#222;color:#eee;padding:12px}
#toggle{display:block;width:100%;height:40px;border:0;background:#2a6;color:#fff}
#toggle:hover{background:#e60}
#panel{display:none;padding-top:8px}
#card.open #panel{display:block}
</style></head><body>
<div id="card"><button id="toggle" aria-expanded="false">Track</button><div id="panel"><p>Out for delivery</p></div></div>
<script>document.getElementById('toggle').onclick=function(){var c=document.getElementById('card');
c.classList.toggle('open');this.setAttribute('aria-expanded',c.classList.contains('open'))}</script>
</body></html>"""


class Look(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        found = tools.find_browser()
        if not found["found"]:
            raise unittest.SkipTest("no Chromium-family browser found (searched %d paths)" % len(found["searched"]))
        cls.tmp = tempfile.mkdtemp(prefix="metadump-look-")
        cls.broken = os.path.join(cls.tmp, "broken.html")
        cls.clean = os.path.join(cls.tmp, "clean.html")
        cls.scrolling = os.path.join(cls.tmp, "scrolling.html")
        for path, body in ((cls.broken, BROKEN_PAGE), (cls.clean, CLEAN_PAGE), (cls.scrolling, SCROLLING_PAGE)):
            with open(path, "w") as f:
                f.write(body)
        try:
            with cdp.Browser(width=320, height=200) as b:
                b.version()
        except (cdp.BrowserUnavailable, cdp.CDPError, OSError) as exc:
            shutil.rmtree(cls.tmp, ignore_errors=True)
            raise unittest.SkipTest("browser could not be launched here: %s" % exc)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, "tmp", ""), ignore_errors=True)

    def test_a_look_reports_clipped_content_and_overlapping_controls(self):
        out = look.look(self.broken, os.path.join(self.tmp, "out-broken"))
        kinds = {(f["kind"], f["selector"]) for f in out["findings"]}
        self.assertIn(("clipped", "#list"), kinds)
        self.assertTrue(any(k == "overlap" and "#close" in s for k, s in kinds), kinds)
        self.assertTrue(any(k == "overflow" for k, _s in kinds), kinds)

    def test_a_scrolling_box_whose_last_visible_row_is_cut_in_half_is_reported(self):
        out = look.look(self.scrolling, os.path.join(self.tmp, "out-scrolling"))
        cut = {f["selector"] for f in out["findings"] if f["kind"] == "cut-off"}
        self.assertIn("#log", cut)      # 50px box, 20px rows: the third row straddles the edge
        self.assertNotIn("#tidy", cut)  # 40px box, 20px rows: the edge falls between rows

    def test_a_clean_page_has_no_findings_and_its_hover_and_toggle_are_seen(self):
        out = look.look(self.clean, os.path.join(self.tmp, "out-clean"))
        self.assertEqual([f for f in out["findings"] if f["kind"] != "truncated"], [])
        self.assertEqual(out["hover"]["selector"], "#toggle")   # the one button is also the toggle
        self.assertTrue(out["hover"]["changed"])
        self.assertEqual((out["toggle"]["before"], out["toggle"]["after"]), ("false", "true"))
        shots = {s["name"]: s for s in out["shots"]}
        self.assertEqual(set(shots), {"desktop", "hover", "open", "phone", "phone-open", "desktop-played", "phone-played"})
        with open(shots["desktop"]["path"], "rb") as f:
            desk = pixels.decode_png(f.read())
        with open(shots["phone"]["path"], "rb") as f:
            phone = pixels.decode_png(f.read())
        self.assertEqual((desk.width, desk.height), (1280, 800))
        self.assertEqual((phone.width, phone.height), (390, 844))

    def test_the_command_prints_the_shots_and_the_question_to_ask(self):
        out_dir = os.path.join(self.tmp, "out-cli")
        run = subprocess.run([sys.executable, LOOK, self.broken, "--out", out_dir], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(os.path.join(out_dir, "desktop.png"), run.stdout)
        self.assertIn("clipped", run.stdout)
        self.assertIn("does it read as the user's words", run.stdout)


# Test 19: five of the eight tic tac toe games had rows that changed height once marks landed. The look never
# played a page, so it never saw it, and the builders trusted its clean list (ADR 0020).
SQUASHING_GAME = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif}
#board{display:grid;grid-template-columns:repeat(3,100px);gap:4px;width:308px}
#board button{min-height:40px;font-size:60px;line-height:1;padding:8px;border:1px solid #333;background:#fff}
</style></head><body>
<p id="status">X to move</p>
<div id="board"><button></button><button></button><button></button><button></button><button></button><button></button><button></button><button></button><button></button></div>
<script>var turn='X';document.querySelectorAll('#board button').forEach(function(b){b.onclick=function(){
if(b.textContent)return;b.textContent=turn;turn=turn==='X'?'O':'X';document.getElementById('status').textContent=turn+' to move'}})</script>
</body></html>"""

# The same game with cells of a fixed size: marks land and nothing moves.
STEADY_GAME = SQUASHING_GAME.replace("min-height:40px;", "height:100px;")

# Opening one of three matching sections makes that one taller on purpose; the other two stay as they were.
ACCORDION = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif}
details{width:300px;border:1px solid #333;margin:0}
summary{height:40px;line-height:40px;padding:0 8px}
details p{margin:0;padding:8px;height:60px}
</style></head><body>
<div id="faq"><details><summary>Shipping</summary><p>Two days.</p></details><details><summary>Returns</summary><p>Thirty days.</p></details><details><summary>Sizing</summary><p>True to size.</p></details></div>
</body></html>"""


# A page whose second button throws when it is used, and whose third is wired to nothing.
BROKEN_CONTROLS = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif} button{height:44px;padding:0 16px;margin-right:12px}
</style></head><body>
<p id="count">0 saved</p>
<button id="save">Save</button><button id="share">Share</button><button id="export">Export</button>
<script>var n=0;document.getElementById('save').onclick=function(){n++;document.getElementById('count').textContent=n+' saved'};
document.getElementById('share').onclick=function(){undefinedShareSheet.open()};</script>
</body></html>"""

# A finished game: the two cells left over rightly stop responding once someone has won.
ENDING_GAME = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif}
#board{display:grid;grid-template-columns:repeat(3,80px);grid-auto-rows:80px;gap:4px}
#board button{font-size:40px}
</style></head><body>
<p id="status">X to move</p>
<div id="board"><button></button><button></button><button></button><button></button><button></button><button></button><button></button><button></button><button></button></div>
<button id="again">New game</button>
<script>var cells=[].slice.call(document.querySelectorAll('#board button')),turn='X',over=false,
lines=[[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]],say=document.getElementById('status');
cells.forEach(function(b){b.onclick=function(){if(over||b.textContent)return;b.textContent=turn;
if(lines.some(function(l){return l.every(function(i){return cells[i].textContent===turn})})){over=true;say.textContent=turn+' wins';return}
turn=turn==='X'?'O':'X';say.textContent=turn+' to move'}});
document.getElementById('again').onclick=function(){cells.forEach(function(b){b.textContent=''});turn='X';over=false;say.textContent='X to move'};</script>
</body></html>"""


# Three buttons and no script: nothing a person does here has any effect.
UNWIRED_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif} button{height:44px;padding:0 16px;margin-right:12px}
</style></head><body><p>0 saved</p><button>Save</button><button>Share</button><button>Export</button></body></html>"""

# A panel that only appears after a click, and whose text is cut off by its own box when it does.
LATE_CLIP = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif} button{height:44px;padding:0 16px}
#details{display:none;height:30px;overflow:hidden;width:260px}
#details p{margin:0;line-height:20px}
</style></head><body>
<button id="more">Show details</button>
<div id="details"><p>Ordered Monday</p><p>Packed Tuesday</p><p>Handed to the carrier</p><p>Out for delivery</p></div>
<script>document.getElementById('more').onclick=function(){document.getElementById('details').style.display='block'}</script>
</body></html>"""


# Keyboard: one button whose focus ring was removed and not replaced, one left alone, and a clickable div that
# the Tab key never reaches.
KEYBOARD_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif} button{height:44px;padding:0 16px;margin-right:12px}
#bare:focus,#bare:focus-visible{outline:none}
#tile{width:120px;height:44px;line-height:44px;margin-top:12px;background:#ddd;cursor:pointer;text-align:center}
</style></head><body>
<p id="count">0</p>
<button id="ringed">Ringed</button><button id="bare">Bare</button>
<div id="tile">Tile</div>
<script>var n=0;function bump(){n++;document.getElementById('count').textContent=String(n)+' taps'}
document.getElementById('ringed').onclick=bump;document.getElementById('bare').onclick=bump;
document.getElementById('tile').addEventListener('click',bump);</script>
</body></html>"""

# Test 18's buttons: the page darkens under the label before the label turns light, so mid-hover it can't be read.
WASHING_BUTTON = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:40px;font:16px sans-serif;background:#fff}
#go{width:200px;height:60px;border:0;font-size:22px;font-weight:700;color:#111;background:#f2f2f2;
transition:background-color .2s linear, color .1s linear .7s}
#go:hover{background:#151515;color:#fff}
</style></head><body><button id="go">Continue</button></body></html>"""

# Test 19's lemons: a viewer whose control panel sits beside the model on a laptop and on top of it on a phone.
COVERING_PANEL = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><style>
html,body{margin:0;height:100%;font:14px sans-serif}
#stage{position:fixed;inset:0;width:100%;height:100%;background:#234}
#panel{position:fixed;top:16px;right:16px;width:240px;height:300px;background:#111;color:#eee}
@media (max-width:600px){#panel{top:auto;left:0;right:0;bottom:0;width:auto;height:62%}}
</style></head><body><canvas id="stage"></canvas><div id="panel">Ripeness</div></body></html>"""

# The same viewer done right for phones: the model keeps the top half and the panel takes the rest.
STACKED_PANEL = COVERING_PANEL.replace("@media (max-width:600px){#panel{top:auto;left:0;right:0;bottom:0;width:auto;height:62%}}",
                                       "@media (max-width:600px){#stage{height:50%}#panel{top:50%;left:0;right:0;bottom:0;width:auto;height:auto}}")

# Something that pulses forever, and a page that never asks whether the person wants less motion.
ENDLESS_MOTION = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:40px;font:16px sans-serif}
#dot{width:40px;height:40px;border-radius:50%;background:#c33;animation:pulse 1.2s ease-in-out infinite}
@keyframes pulse{50%{transform:scale(1.3)}}
</style></head><body><div id="dot"></div><p>Live</p></body></html>"""

CALMED_MOTION = ENDLESS_MOTION.replace("</style>", "@media (prefers-reduced-motion: reduce){#dot{animation:none}}</style>")


# Test 18's toasts: a collapsed panel whose buttons still take keyboard focus, where nobody can see them.
HIDDEN_FOCUS = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:20px;font:16px sans-serif} button{height:44px;padding:0 16px}
#panel{max-height:0;overflow:hidden}
</style></head><body>
<button id="head">Parcel</button>
<div id="panel"><button id="copy">Copy number</button><button id="notify">Notify me</button></div>
</body></html>"""

# The same panel taken out of the tab order while it is shut.
TIDY_FOCUS = HIDDEN_FOCUS.replace('<div id="panel">', '<div id="panel" hidden>')


class LookPlays(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        found = tools.find_browser()
        if not found["found"]:
            raise unittest.SkipTest("no Chromium-family browser found (searched %d paths)" % len(found["searched"]))
        cls.tmp = tempfile.mkdtemp(prefix="metadump-look-play-")
        try:
            with cdp.Browser(width=320, height=200) as b:
                b.version()
        except (cdp.BrowserUnavailable, cdp.CDPError, OSError) as exc:
            shutil.rmtree(cls.tmp, ignore_errors=True)
            raise unittest.SkipTest("browser could not be launched here: %s" % exc)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(getattr(cls, "tmp", ""), ignore_errors=True)

    def page(self, name, body):
        path = os.path.join(self.tmp, name + ".html")
        with open(path, "w") as f:
            f.write(body)
        return path, os.path.join(self.tmp, "out-" + name)

    def test_cells_that_change_size_once_marks_land_are_reported_as_uneven(self):
        out = look.look(*self.page("squashing", SQUASHING_GAME))
        uneven = [f for f in out["findings"] if f["kind"] == "uneven"]
        self.assertEqual({f["selector"] for f in uneven}, {"#board"})
        self.assertIn("after", uneven[0]["detail"])           # it says which action did it

    def test_a_board_whose_cells_keep_their_size_through_play_is_not_reported(self):
        out = look.look(*self.page("steady", STEADY_GAME))
        self.assertEqual([f for f in out["findings"] if f["kind"] == "uneven"], [])

    def test_a_script_error_thrown_while_the_page_is_used_is_reported_with_the_action(self):
        out = look.look(*self.page("broken-controls", BROKEN_CONTROLS))
        errors = [f for f in out["findings"] if f["kind"] == "js-error"]
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("undefinedShareSheet", errors[0]["detail"])
        self.assertIn('clicked "Share"', errors[0]["detail"])

    def test_a_page_where_no_control_responds_is_reported_as_dead(self):
        out = look.look(*self.page("unwired", UNWIRED_PAGE))
        dead = [f for f in out["findings"] if f["kind"] == "dead"]
        self.assertEqual([f["selector"] for f in dead], ["body"])
        self.assertIn("3", dead[0]["detail"])           # how many controls were tried

    def test_one_control_that_changes_nothing_on_a_working_page_is_told_not_reported(self):
        # Test 18's toasts: a pager dot for the parcel already showing, a "bring back" button with nothing to bring
        # back. A control can rightly do nothing in the state the walk found it in.
        out = look.look(*self.page("broken-controls-2", BROKEN_CONTROLS))
        self.assertEqual([f for f in out["findings"] if f["kind"] == "dead"], [])
        told = {s["label"]: s["changed"] for s in out["played"]["desktop"]}
        self.assertEqual(told, {"Save": True, "Share": False, "Export": False})

    def test_the_account_of_the_walk_says_what_the_page_said_after_each_action(self):
        out = look.look(*self.page("ending", ENDING_GAME))
        steps = out["played"]["desktop"]
        self.assertEqual([s["said"] for s in steps[:7]],
                         [["O to move"], ["X to move"], ["O to move"], ["X to move"], ["O to move"], ["X to move"], ["X wins"]])
        self.assertEqual((steps[-1]["label"], steps[-1]["said"]), ("New game", ["X to move"]))   # resets go last
        self.assertEqual([f for f in out["findings"] if f["kind"] == "dead"], [])

    def test_the_command_prints_the_account_of_the_walk(self):
        path, out_dir = self.page("ending-cli", ENDING_GAME)
        run = subprocess.run([sys.executable, LOOK, path, "--out", out_dir], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Played it", run.stdout)
        self.assertIn('clicked 7 of the 9 matching controls in #board', run.stdout)
        self.assertIn('"X wins"', run.stdout)
        self.assertIn("clicked 2 more: nothing changed", run.stdout)
        self.assertIn('clicked "New game": the page said "X to move"', run.stdout)

    def test_a_control_whose_keyboard_focus_shows_nothing_is_reported_and_a_ringed_one_is_not(self):
        out = look.look(*self.page("keyboard", KEYBOARD_PAGE))
        self.assertEqual({f["selector"] for f in out["findings"] if f["kind"] == "focus-static"}, {"#bare"})

    def test_keyboard_focus_landing_on_controls_nobody_can_see_is_reported(self):
        out = look.look(*self.page("hidden-focus", HIDDEN_FOCUS), walk=False)
        hidden = [f for f in out["findings"] if f["kind"] == "focus-hidden"]
        self.assertEqual([f["selector"] for f in hidden], ["#copy"])
        self.assertIn("2 controls", hidden[0]["detail"])
        self.assertEqual([f for f in out["findings"] if f["kind"] == "focus-static"], [])
        out = look.look(*self.page("tidy-focus", TIDY_FOCUS), walk=False)
        self.assertEqual([f for f in out["findings"] if f["kind"] in ("focus-hidden", "focus-static")], [])

    def test_a_clickable_element_the_tab_key_cannot_reach_is_reported(self):
        out = look.look(*self.page("keyboard-2", KEYBOARD_PAGE))
        self.assertEqual({f["selector"] for f in out["findings"] if f["kind"] == "no-keyboard"}, {"#tile"})

    def test_a_label_that_cannot_be_read_partway_through_its_hover_is_reported(self):
        out = look.look(*self.page("washing", WASHING_BUTTON))
        washed = [f for f in out["findings"] if f["kind"] == "washed-out"]
        self.assertEqual([f["selector"] for f in washed], ["#go"])

    def test_a_panel_that_covers_the_main_visual_only_on_a_phone_is_reported(self):
        out = look.look(*self.page("covering", COVERING_PANEL))
        covered = [f for f in out["findings"] if f["kind"] == "covered"]
        self.assertEqual([(f["selector"], f["state"]) for f in covered], [("#stage", "phone")])
        self.assertIn("#panel", covered[0]["detail"])
        out = look.look(*self.page("stacked", STACKED_PANEL))
        self.assertEqual([f for f in out["findings"] if f["kind"] == "covered"], [])

    def test_endless_motion_on_a_page_that_never_asks_about_reduced_motion_is_reported(self):
        out = look.look(*self.page("endless", ENDLESS_MOTION))
        self.assertEqual([f["kind"] for f in out["findings"] if f["kind"] == "no-reduced-motion"], ["no-reduced-motion"])
        out = look.look(*self.page("calmed", CALMED_MOTION))
        self.assertEqual([f for f in out["findings"] if f["kind"] == "no-reduced-motion"], [])

    # The tic tac toe dump's own review question: "Play X 0, O 1, X 2, O 4, X 3, O 5, X 7, O 6, X 8; the status reads
    # a draw and names no winner." Nothing ran it. ENDING_GAME has that very bug: it never notices a full board.
    DRAWN_GAME = "; ".join("click #board button:nth-of-type(%d)" % (i + 1) for i in (0, 1, 2, 4, 3, 5, 7, 6, 8))

    def test_a_scripted_play_whose_expectation_fails_is_reported_with_what_the_page_said_instead(self):
        path, out_dir = self.page("play-draw", ENDING_GAME)
        out = look.look(path, out_dir, plays=[self.DRAWN_GAME + "; expect draw"])
        failed = [f for f in out["findings"] if f["kind"] == "expect"]
        self.assertEqual(len(failed), 1, out["findings"])
        self.assertIn("draw", failed[0]["detail"])
        self.assertIn("O to move", failed[0]["detail"])       # what it said instead, after the ninth mark
        self.assertEqual(out["plays"][0]["actions"], 9)

    def test_a_scripted_play_whose_expectations_hold_reports_nothing(self):
        path, out_dir = self.page("play-win", ENDING_GAME)
        steps = "; ".join("click #board button:nth-of-type(%d)" % n for n in (1, 4, 2, 5, 3))   # X takes the top row
        out = look.look(path, out_dir, plays=[steps + "; expect #status says X wins; expect no O wins"])
        self.assertEqual([f for f in out["findings"] if f["kind"] in ("expect", "play")], [])
        self.assertEqual([e["ok"] for e in out["plays"][0]["expects"]], [True, True])

    def test_a_scripted_play_stops_at_a_step_that_matches_nothing_and_says_which(self):
        path, out_dir = self.page("play-missing", ENDING_GAME)
        out = look.look(path, out_dir, plays=["click #board button:nth-of-type(1); click #undo; click #again"])
        stopped = [f for f in out["findings"] if f["kind"] == "play"]
        self.assertEqual(len(stopped), 1, out["findings"])
        self.assertIn("#undo", stopped[0]["detail"])
        self.assertEqual(out["plays"][0]["actions"], 1)

    def test_a_scripted_play_is_held_to_the_same_invariants_as_the_walk(self):
        path, out_dir = self.page("play-squash", SQUASHING_GAME.replace("repeat(3,100px)", "repeat(3,90px)"))
        out = look.look(path, out_dir, plays=["click #board button:nth-of-type(5); type hello into #nothing-here"], walk=False)
        self.assertEqual({f["selector"] for f in out["findings"] if f["kind"] == "uneven"}, {"#board"})
        self.assertEqual(out["played"], {})                   # the walk itself was switched off

    def test_the_look_lays_every_state_out_on_one_labelled_sheet(self):
        # Test 19: the game builders ran the look and opened none of its five screenshots.
        path, out_dir = self.page("ending-sheet", ENDING_GAME)
        run = subprocess.run([sys.executable, LOOK, path, "--out", out_dir, "--play", "click #again; expect X to move"],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        sheet = os.path.join(out_dir, "sheet.png")
        self.assertIn(sheet, run.stdout)
        with open(sheet, "rb") as f:
            image = pixels.decode_png(f.read())
        self.assertEqual(image.width, 1300)
        self.assertGreater(image.height, 800)             # six shots don't fit one window's height
        # the sheet's ground is dark all the way down: a capture that stopped at the window's edge leaves white below it
        self.assertLess(max(image.pixel(4, image.height - 4)[:3]), 60)
        for name in ("desktop-played.png", "phone-played.png", "play-1.png"):
            self.assertTrue(os.path.isfile(os.path.join(out_dir, name)), name)
        self.assertIn("Would a stranger", run.stdout)
        # Test 20: with only the sheet to read, builders opened one to three images on a visual task where the older
        # look's builders opened four to seven full-size ones. The sheet is the overview, not the reading.
        self.assertIn("Read the desktop and phone shots", run.stdout)

    def test_content_clipped_only_after_an_action_is_reported_with_that_action(self):
        out = look.look(*self.page("late-clip", LATE_CLIP))
        clipped = [f for f in out["findings"] if f["kind"] == "clipped" and f["selector"] == "#details"]
        self.assertEqual(len(clipped), 1, out["findings"])
        self.assertIn('after the look clicked "Show details"', clipped[0]["state"])

    def test_a_section_that_opens_among_matching_ones_is_not_uneven(self):
        out = look.look(*self.page("accordion", ACCORDION))
        self.assertEqual([f for f in out["findings"] if f["kind"] == "uneven"], [])


class LookWithoutABrowser(unittest.TestCase):
    def test_the_command_says_to_skip_the_step_and_exits_cleanly(self):
        env = dict(os.environ, METADUMP_DISABLE="browser")
        run = subprocess.run([sys.executable, LOOK, os.path.join(HERE, "fixtures", "nothing.html")],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("skip this step", run.stdout)


if __name__ == "__main__":
    unittest.main()

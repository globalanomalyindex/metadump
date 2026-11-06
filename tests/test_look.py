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
        self.assertEqual(set(shots), {"desktop", "hover", "open", "phone", "phone-open"})
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


class LookWithoutABrowser(unittest.TestCase):
    def test_the_command_says_to_skip_the_step_and_exits_cleanly(self):
        env = dict(os.environ, METADUMP_DISABLE="browser")
        run = subprocess.run([sys.executable, LOOK, os.path.join(HERE, "fixtures", "nothing.html")],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("skip this step", run.stdout)


if __name__ == "__main__":
    unittest.main()

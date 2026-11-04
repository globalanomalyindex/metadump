"""One real-browser integration test: headless Chrome over our stdlib CDP client, no network.

A temp dir is served on 127.0.0.1 (random port) with a canvas animation driven by a deterministic clock
(a square moves for 0.4 s, holds 0.5 s, moves again for 0.4 s) and a CSS keyframe animation. The test
captures dense frame windows through cdp.py, runs the pure-Python timing analysis, and checks that the
motion segments and holds come out with plausible durations; it also screenshots a page and decodes the PNG.
Skipped when no Chromium-family browser is installed or it cannot be launched here.
"""
import functools
import http.server
import os
import shutil
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
sys.path.insert(0, SCRIPTS)

import cdp  # noqa: E402
import pixels  # noqa: E402
import tools  # noqa: E402
import video  # noqa: E402

CANVAS_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;background:#000}</style></head><body>
<canvas id="stage" width="160" height="90" style="display:block"></canvas>
<script>
const c = document.getElementById('stage'), x = c.getContext('2d');
function pos(t) {
  if (t < 0.4) return 10 + 60 * (t / 0.4);
  if (t < 0.9) return 70;
  if (t < 1.3) return 70 + 60 * ((t - 0.9) / 0.4);
  return 130;
}
window.drawAt = (t) => { x.fillStyle = '#202020'; x.fillRect(0, 0, 160, 90); x.fillStyle = '#f0f0f0'; x.fillRect(Math.round(pos(t)), 35, 20, 20); };
window.drawAt(0);
</script></body></html>"""

CSS_PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#202020} #stage{position:relative;width:160px;height:90px;overflow:hidden}
#box{position:absolute;left:10px;top:35px;width:20px;height:20px;background:#f0f0f0;
     animation:slide 1s linear both}
@keyframes slide{0%{transform:translateX(0)} 40%{transform:translateX(60px)} 70%{transform:translateX(60px)} 100%{transform:translateX(120px)}}
</style></head><body><div id="stage"><div id="box"></div></div></body></html>"""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class BrowserIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        found = tools.find_browser()
        if not found["found"]:
            raise unittest.SkipTest("no Chromium-family browser found (searched %d paths)" % len(found["searched"]))
        cls.tmp = tempfile.mkdtemp(prefix="metadump-it-")
        for name, body in (("canvas.html", CANVAS_PAGE), ("css.html", CSS_PAGE)):
            with open(os.path.join(cls.tmp, name), "w") as f:
                f.write(body)
        handler = functools.partial(_Quiet, directory=cls.tmp)
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        cls.base = "http://127.0.0.1:%d/" % cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        try:
            with cdp.Browser(width=320, height=200) as b:
                b.version()
        except (cdp.BrowserUnavailable, cdp.CDPError, OSError) as exc:
            cls.tearDownClass()
            raise unittest.SkipTest("browser could not be launched here: %s" % exc)

    @classmethod
    def tearDownClass(cls):
        server = getattr(cls, "server", None)
        if server is not None:
            server.shutdown()
            server.server_close()
        shutil.rmtree(getattr(cls, "tmp", ""), ignore_errors=True)

    def check_timeline(self, tl, label):
        self.assertTrue(tl.get("ok"), tl)
        segs = tl["segments"]
        motion = [s for s in segs if s["kind"] == "motion"]
        self.assertGreaterEqual(len(motion), 2, "%s: %s" % (label, [(s["kind"], s["frames"]) for s in segs]))
        first = motion[0]
        self.assertAlmostEqual(first["duration"], 0.4, delta=0.07, msg=label)
        hold = segs[segs.index(first) + 1]
        self.assertEqual(hold["kind"], "hold")
        return first, hold, motion[1]

    def test_canvas_animation_motion_and_hold(self):
        tl = video.timing(self.base + "canvas.html", (0.0, 1.6), fps=30, seek="hook:drawAt", selector="#stage")
        first, hold, second = self.check_timeline(tl, "canvas")
        self.assertAlmostEqual(hold["duration"], 0.5, delta=0.07)
        self.assertAlmostEqual(second["duration"], 0.4, delta=0.07)
        self.assertEqual(first["easing"]["best"], "linear")
        self.assertEqual(tl["engine"], "browser")
        self.assertEqual(tl["frames"], 49)

    def test_css_animation_through_web_animations_seek(self):
        tl = video.timing(self.base + "css.html", (0.0, 1.0), fps=30, seek="animations", selector="#stage")
        first, hold, second = self.check_timeline(tl, "css")
        self.assertAlmostEqual(hold["duration"], 0.3, delta=0.07)
        self.assertAlmostEqual(second["duration"], 0.3, delta=0.07)

    def test_screenshot_decodes_with_stdlib_png(self):
        with cdp.Browser(width=320, height=200) as browser:
            page = browser.new_page()
            page.navigate(self.base + "canvas.html")
            img = pixels.decode_png(page.screenshot())
            rect = page.element_rect("#stage")
            crop = pixels.decode_png(page.screenshot(clip=rect))
        self.assertEqual((img.width, img.height), (320, 200))
        self.assertEqual((crop.width, crop.height), (160, 90))
        self.assertEqual(crop.pixel(15, 40)[:3], (240, 240, 240))  # the square at t=0 starts at x=10
        self.assertEqual(crop.pixel(100, 10)[:3], (32, 32, 32))


if __name__ == "__main__":
    unittest.main()

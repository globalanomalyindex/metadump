"""Tests for skills/metadump/scripts/video.py: captions, transcripts, chapters, player data, timing analysis,
frame records and engine fallback. No network and no browser: engines are injected fakes, frames are
synthetic grayscale sequences built here. METADUMP_LIVE=1 adds one real YouTube metadata/captions run.
"""
import json
import math
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
FIX = os.path.join(HERE, "fixtures", "video")
sys.path.insert(0, SCRIPTS)

import video  # noqa: E402


def read(name):
    with open(os.path.join(FIX, name), encoding="utf-8") as f:
        return f.read()


class Timecodes(unittest.TestCase):
    def test_format(self):
        self.assertEqual(video.timecode(0), "00:00:00.000")
        self.assertEqual(video.timecode(3723.4567), "01:02:03.457")
        self.assertEqual(video.timecode(59.9996), "00:01:00.000")
        self.assertEqual(video.timecode(-1), "00:00:00.000")

    def test_parse(self):
        self.assertEqual(video.parse_timestamp("1:02:03.5"), 3723.5)
        self.assertEqual(video.parse_timestamp("02:03"), 123.0)
        self.assertEqual(video.parse_timestamp("00:00:01,250"), 1.25)
        self.assertEqual(video.parse_timestamp("90"), 90.0)
        self.assertEqual(video.parse_window("1.0-2.5"), (1.0, 2.5))
        self.assertEqual(video.parse_window("00:01-00:03.5"), (1.0, 3.5))
        with self.assertRaises(ValueError):
            video.parse_window("3-1")


class Captions(unittest.TestCase):
    def test_vtt_settings_voices_markup_and_multiline(self):
        cues = video.parse_vtt(read("sample.vtt"))
        self.assertEqual(len(cues), 4)
        c1, c2, c3, c4 = cues
        self.assertEqual((c1["start"], c1["end"]), (1.0, 4.0))
        self.assertEqual(c1["id"], "intro")
        self.assertEqual(c1["settings"], "align:start position:10% line:0")
        self.assertEqual(c1["speaker"], "Roger Bingham")
        self.assertEqual(c1["text"], "We are in New York City & it is cold.")
        self.assertEqual((c2["start"], c2["end"]), (4.5, 6.25))
        self.assertEqual(c2["speaker"], "Neil")
        self.assertEqual(c2["text"], "Two lines here,\nand markup to strip.")
        self.assertEqual(c3["text"], "Words with inline times <3")
        self.assertEqual(c4["text"], "Final cue here.")
        self.assertEqual(c4["start_tc"], "00:01:00.000")

    def test_srt_numbering_comma_millis_and_tags(self):
        cues = video.parse_srt(read("sample.srt"))
        self.assertEqual([(c["start"], c["end"]) for c in cues], [(1.0, 4.0), (5.25, 7.0), (3723.456, 3725.0)])
        self.assertEqual(cues[0]["text"], "Hello there,\ngeneral.")
        self.assertEqual(cues[2]["text"], "Late line.")

    def test_json_timed_text(self):
        cues = video.parse_json3(read("timedtext.json3.json"))
        self.assertEqual([c["text"] for c in cues], ["so today we're", "looking at easing", "after a pause"])
        self.assertEqual((cues[0]["start"], cues[0]["end"]), (0.16, 3.2))
        self.assertEqual(cues[2]["start_tc"], "00:00:09.000")

    def test_xml_timed_text(self):
        cues = video.parse_xml_timedtext(read("timedtext.srv3.xml"))
        self.assertEqual([(c["start"], c["end"], c["text"]) for c in cues], [(1.0, 3.5, "first line"), (4.0, 5.0, "second & last")])

    def test_format_detection(self):
        self.assertEqual(video.detect_caption_format(read("sample.vtt")), "vtt")
        self.assertEqual(video.detect_caption_format(read("sample.srt")), "srt")
        self.assertEqual(video.detect_caption_format(read("timedtext.json3.json")), "json3")
        self.assertEqual(video.detect_caption_format(read("timedtext.srv3.xml")), "xml")
        self.assertEqual(len(video.parse_captions(read("sample.srt"))), 3)

    def test_xml_with_doctype_is_refused(self):
        self.assertEqual(video.parse_xml_timedtext('<!DOCTYPE x [<!ENTITY a "b">]><timedtext><p t="1">&a;</p></timedtext>'), [])


class Transcript(unittest.TestCase):
    def test_rolling_auto_captions_collapse_into_clean_paragraphs(self):
        segs = video.collapse_rolling(video.parse_vtt(read("rolling-auto.vtt")))
        self.assertEqual([s["text"] for s in segs], ["so today we're", "looking at easing", "curves in motion", "new topic"])
        self.assertEqual(segs[1]["start"], 2.02)
        paras = video.build_transcript(segs)
        self.assertEqual([p["text"] for p in paras], ["so today we're looking at easing curves in motion", "new topic"])
        self.assertEqual(paras[0]["start_tc"], "00:00:00.160")
        self.assertEqual(paras[0]["end_tc"], "00:00:08.000")
        self.assertEqual(paras[1]["start_tc"], "00:00:12.000")

    def test_word_by_word_growth_keeps_only_the_new_words(self):
        cues = [{"start": 0.0, "end": 1.0, "text": "hello"}, {"start": 1.0, "end": 2.0, "text": "hello world"},
                {"start": 2.0, "end": 3.0, "text": "hello world again"}]
        segs = video.collapse_rolling(cues)
        self.assertEqual(" ".join(s["text"] for s in segs), "hello world again")

    def test_speaker_changes_start_new_paragraphs(self):
        cues = [{"start": 0.0, "end": 1.0, "text": "Hi.", "speaker": "A"}, {"start": 1.0, "end": 2.0, "text": "Hello.", "speaker": "B"}]
        paras = video.build_transcript(video.collapse_rolling(cues))
        self.assertEqual([(p["speaker"], p["text"]) for p in paras], [("A", "Hi."), ("B", "Hello.")])

    def test_transcript_record_shape(self):
        cues = video.parse_json3(read("timedtext.json3.json"))
        rec = video.transcript_record(cues, source={"url": "https://youtu.be/x"}, track={"language": "en", "kind": "auto"}, engine="http")
        for key in ("kind", "engine", "source", "track", "language", "cues", "transcript", "stats"):
            self.assertIn(key, rec)
        self.assertEqual(rec["kind"], "transcript")
        self.assertEqual(rec["stats"]["cues"], 3)
        self.assertEqual(rec["transcript"][1]["text"], "after a pause")


class PlayerData(unittest.TestCase):
    def test_extract_json_var_handles_braces_inside_strings(self):
        page = read("watch-page.html")
        pr = video.extract_json_var(page, "ytInitialPlayerResponse")
        self.assertEqual(pr["videoDetails"]["videoId"], "abcDEF12345")
        data = video.extract_json_var(page, "ytInitialData")
        chapters = video.chapters_from_initial_data(data, 212)
        self.assertEqual(chapters[0]["title"], 'Intro {with braces} "quoted"')
        self.assertEqual([c["start"] for c in chapters], [0.0, 45.0, 90.0, 170.0])
        self.assertEqual(chapters[-1]["end"], 212.0)

    def test_chapter_records_win_over_duplicate_marker_items(self):
        data = {"a": [{"chapterRenderer": {"title": {"simpleText": "Quest"}, "timeRangeStartMillis": 93132}},
                      {"chapterRenderer": {"title": {"simpleText": "Intro"}, "timeRangeStartMillis": 0}}],
                "b": [{"macroMarkersListItemRenderer": {"title": {"simpleText": "Quest"}, "timeDescription": {"simpleText": "1:33"}}},
                      {"macroMarkersListItemRenderer": {"title": {"simpleText": "Intro"}, "timeDescription": {"simpleText": "0:00"}}}]}
        chapters = video.chapters_from_initial_data(data, 300)
        self.assertEqual([(c["start"], c["title"]) for c in chapters], [(0.0, "Intro"), (93.132, "Quest")])
        only_macro = {"b": data["b"]}
        self.assertEqual([c["start"] for c in video.chapters_from_initial_data(only_macro, 300)], [0.0, 93.0])

    def test_media_record_from_player_response(self):
        rec = video.media_from_player_response(json.loads(read("player-response.json")))
        self.assertEqual(rec["title"], "Easing curves explained")
        self.assertEqual(rec["duration"], 212.0)
        self.assertEqual(rec["duration_tc"], "00:03:32.000")
        self.assertEqual((rec["fps"], rec["fps_source"]), (60, "declared"))
        self.assertEqual((rec["width"], rec["height"]), (1920, 1080))
        self.assertEqual(rec["published"], "2024-05-01")
        self.assertEqual([(c["language"], c["kind"]) for c in rec["captions"]], [("en", "auto"), ("en-GB", "manual"), ("de", "manual")])
        self.assertEqual(rec["chapters_source"], "description")
        self.assertEqual(rec["chapters"][1]["title"], "Linear motion")
        self.assertNotIn("_url", json.dumps(rec["captions"]))

    def test_chapters_from_description(self):
        chapters = video.chapters_from_description("Intro text\n0:00 Start\n(1:05) Middle part\nEnd bit - 2:10\nnot a chapter", 200)
        self.assertEqual([(c["start"], c["end"], c["title"]) for c in chapters],
                         [(0.0, 65.0, "Start"), (65.0, 130.0, "Middle part"), (130.0, 200.0, "End bit")])
        self.assertEqual(video.chapters_from_description("1:00 no zero start\n2:00 b", 300), [])

    def test_choose_track_prefers_manual_then_auto(self):
        tracks = video.media_from_player_response(json.loads(read("player-response.json")))["captions"]
        self.assertEqual(video.choose_track(tracks, "en")["language"], "en-GB")
        self.assertEqual(video.choose_track(tracks, "en", kind="auto")["language"], "en")
        self.assertEqual(video.choose_track(tracks, None)["language"], "en-GB")
        self.assertIsNone(video.choose_track(tracks, "fr"))

    def test_youtube_ids(self):
        for url in ("https://www.youtube.com/watch?v=abcDEF12345&t=10", "https://youtu.be/abcDEF12345",
                    "https://www.youtube.com/shorts/abcDEF12345", "https://www.youtube-nocookie.com/embed/abcDEF12345",
                    "https://m.youtube.com/watch?feature=share&v=abcDEF12345"):
            self.assertEqual(video.youtube_id(url), "abcDEF12345", url)
        self.assertIsNone(video.youtube_id("https://vimeo.com/123"))

    def test_login_required_is_reported_not_bypassed(self):
        pr = json.loads(read("player-response.json"))
        pr["playabilityStatus"] = {"status": "LOGIN_REQUIRED", "reason": "Sign in to confirm your age"}
        rec = video.media_from_player_response(pr)
        self.assertEqual(rec["playability"], {"status": "LOGIN_REQUIRED", "reason": "Sign in to confirm your age"})

    def test_same_record_shape_from_every_engine(self):
        from_http = video.media_from_player_response(json.loads(read("player-response.json")))
        from_ytdlp = video.media_from_ytdlp({"id": "abcDEF12345", "title": "T", "duration": 212, "fps": 30, "width": 1920,
                                             "height": 1080, "uploader": "U", "upload_date": "20240430", "description": "d",
                                             "chapters": [{"start_time": 0, "end_time": 100, "title": "A"}],
                                             "subtitles": {"en": [{"ext": "vtt", "name": "English"}]},
                                             "automatic_captions": {"de": [{"ext": "json3"}]}, "webpage_url": "https://youtu.be/abcDEF12345"})
        from_probe = video.media_from_ffprobe({"format": {"duration": "12.5", "tags": {"title": "clip"}},
                                               "streams": [{"codec_type": "video", "width": 640, "height": 360, "avg_frame_rate": "30000/1001"},
                                                           {"codec_type": "subtitle", "tags": {"language": "eng"}}],
                                               "chapters": []}, "/x/clip.mp4")
        for rec in (from_http, from_ytdlp, from_probe):
            self.assertEqual(set(rec), set(from_http), rec.get("engine"))
        self.assertEqual(from_ytdlp["published"], "2024-04-30")
        self.assertEqual(from_ytdlp["chapters"][0]["end"], 100.0)
        self.assertEqual([c["kind"] for c in from_ytdlp["captions"]], ["manual", "auto"])
        self.assertAlmostEqual(from_probe["fps"], 29.97, places=2)
        self.assertEqual(from_probe["fps_source"], "declared")


# ---------------------------------------------------------------- synthetic frames

W, H = 96, 48


def render_square(x, side=12, y=18, noise=0, rng=None):
    """Gray frame with a bright square whose left edge is at fractional x (edges anti-aliased)."""
    px = bytearray(W * H)
    for row in range(y, y + side):
        for col in range(W):
            cover = max(0.0, min(col + 1, x + side) - max(col, x))
            v = 20 + int(round(200 * cover))
            if noise:
                v += rng.randint(-noise, noise)
            px[row * W + col] = max(0, min(255, v))
    if noise:
        for i in range(W * H):
            if not (y * W <= i < (y + side) * W):
                px[i] = max(0, min(255, 20 + rng.randint(-noise, noise)))
    return bytes(px)


def sequence(positions, noise=3, seed=7):
    rng = random.Random(seed)
    return [render_square(x, noise=noise, rng=rng) for x in positions]


# ---------------------------------------------------------------- independent easing reference
# Control points written out from their published definitions, not read from video.py:
# CSS Easing Functions Level 1 keywords: ease-in = cubic-bezier(0.42, 0, 1, 1), ease-out = cubic-bezier(0, 0, 0.58, 1),
# ease-in-out = cubic-bezier(0.42, 0, 0.58, 1); linear is the identity. The overshoot curve is the widely used
# "easeOutBack" cubic-bezier(0.34, 1.56, 0.64, 1) (easings.net).
REFERENCE_CURVES = {
    "linear": (0.0, 0.0, 1.0, 1.0),
    "ease-in": (0.42, 0.0, 1.0, 1.0),
    "ease-out": (0.0, 0.0, 0.58, 1.0),
    "ease-in-out": (0.42, 0.0, 0.58, 1.0),
    "overshoot": (0.34, 1.56, 0.64, 1.0),
}


def reference_bezier(x1, y1, x2, y2):
    """A deliberately different evaluator from video.py's: plain bisection on the curve parameter, no Newton steps."""
    def coord(u, a, b):
        return 3 * a * u * (1 - u) ** 2 + 3 * b * u ** 2 * (1 - u) + u ** 3

    def at(t):
        lo, hi = 0.0, 1.0
        for _ in range(80):
            mid = (lo + hi) / 2
            if coord(mid, x1, x2) < t:
                lo = mid
            else:
                hi = mid
        return coord((lo + hi) / 2, y1, y2)
    return at


def reference_cumulative_change(values):
    """Running total of absolute steps, scaled to end at 1 (what summed frame differences measure)."""
    steps = [abs(b - a) for a, b in zip(values, values[1:])]
    total = sum(steps)
    out, acc = [0.0], 0.0
    for step in steps:
        acc += step
        out.append(acc / total)
    return out


class TimingAnalysis(unittest.TestCase):
    def scripted_positions(self):
        pos = [4.0] * 5                                  # frames 0-4 still
        for _ in range(12):                              # 12 frames of linear motion, 2 px per frame
            pos.append(pos[-1] + 2)
        pos += [pos[-1]] * 10                            # 10-frame hold
        for k in range(16):                              # 16 frames on twos: move 4 px every other frame
            pos.append(pos[-1] + (4 if k % 2 == 0 else 0))
        pos += [pos[-1]] * 9                             # trailing hold
        return pos

    def test_noise_floor_estimate(self):
        diffs = video.frame_diffs(sequence([4.0] * 20))
        floor, spread = video.noise_floor(diffs)
        self.assertAlmostEqual(floor, 2.0, delta=0.3)
        self.assertLess(spread, 0.2)

    def test_motion_holds_and_stepped_timing(self):
        tl = video.analyze_timing(sequence(self.scripted_positions()), W, H, fps=30, start=10.0, fps_source="declared")
        kinds = [s["kind"] for s in tl["segments"]]
        self.assertEqual(kinds, ["hold", "motion", "hold", "motion", "hold"])
        m1, hold, m2 = tl["segments"][1], tl["segments"][2], tl["segments"][3]
        self.assertEqual(m1["frames"], 12)
        self.assertAlmostEqual(m1["duration"], 0.4, places=3)
        self.assertEqual(m1["duration_ms"], 400)
        self.assertEqual(m1["start_tc"], "00:00:10.133")
        self.assertEqual(m1["start_frame"], 304)
        self.assertEqual(m1["stepped"]["on"], 1)
        self.assertEqual(m1["easing"]["best"], "linear")
        self.assertEqual(hold["frames"], 10)
        self.assertIn(m2["frames"], (15, 16))
        self.assertEqual(m2["stepped"]["on"], 2)
        self.assertGreaterEqual(m2["stepped"]["confidence"], 0.9)
        self.assertEqual(tl["kind"], "timeline")
        self.assertEqual(tl["fps"], 30)
        self.assertEqual(len(tl["diffs"]), len(self.scripted_positions()))
        self.assertGreater(tl["threshold"], tl["noise_floor"])

    def test_still_sequence_has_no_motion(self):
        tl = video.analyze_timing(sequence([4.0] * 15), W, H, fps=24)
        self.assertEqual([s["kind"] for s in tl["segments"]], ["hold"])
        self.assertEqual(tl["summary"]["motion_segments"], 0)

    def test_eased_motion_in_frames_reads_as_ease_out(self):
        f = reference_bezier(*REFERENCE_CURVES["ease-out"])
        pos = [4.0] * 4 + [4.0 + 30 * f(k / 18.0) for k in range(1, 19)] + [34.0] * 6
        tl = video.analyze_timing(sequence(pos, noise=1), W, H, fps=30)
        motion = [s for s in tl["segments"] if s["kind"] == "motion"]
        self.assertEqual(len(motion), 1)
        self.assertEqual(motion[0]["easing"]["best"], "ease-out")


class Easing(unittest.TestCase):
    def curve(self, name, n=25):
        f = reference_bezier(*REFERENCE_CURVES[name])
        ts = [k / float(n - 1) for k in range(n)]
        return ts, [f(t) for t in ts]

    def test_reference_evaluator_meets_known_identities(self):
        # Sanity check of the test's own helper, from properties that need no evaluator at all.
        self.assertAlmostEqual(reference_bezier(*REFERENCE_CURVES["ease-in-out"])(0.5), 0.5, places=9)  # symmetric curve
        self.assertAlmostEqual(reference_bezier(*REFERENCE_CURVES["linear"])(0.3), 0.3, places=9)
        ease_in, ease_out = reference_bezier(*REFERENCE_CURVES["ease-in"]), reference_bezier(*REFERENCE_CURVES["ease-out"])
        for t in (0.2, 0.5, 0.8):  # ease-out is ease-in rotated 180 degrees about (0.5, 0.5)
            self.assertAlmostEqual(ease_out(t), 1 - ease_in(1 - t), places=9)

    def test_named_curves_classify_as_themselves(self):
        for name in ("linear", "ease-in", "ease-out", "ease-in-out"):
            ts, ps = self.curve(name)
            res = video.classify_easing(ts, ps)
            self.assertEqual(res["best"], name, res)
            self.assertLess(res["fit_error"], 0.01)

    def test_overshoot_signed_and_as_cumulative_change(self):
        ts, ps = self.curve("overshoot")
        self.assertEqual(video.classify_easing(ts, ps)["best"], "overshoot")
        self.assertGreater(video.classify_easing(ts, ps)["overshoot"], 0.05)
        tv = reference_cumulative_change(ps)
        self.assertEqual(video.classify_easing(ts, tv)["best"], "overshoot")

    def test_half_progress_descriptor(self):
        ts, ps = self.curve("ease-out")
        self.assertGreater(video.classify_easing(ts, ps)["half_progress"], 0.6)
        ts, ps = self.curve("ease-in")
        self.assertLess(video.classify_easing(ts, ps)["half_progress"], 0.4)

    def test_too_few_samples(self):
        self.assertIsNone(video.classify_easing([0, 1], [0, 1])["best"])


class FrameRecords(unittest.TestCase):
    def test_frame_record_fields(self):
        rec = video.frame_record(3, 12.345, 30, "declared", file="f_000012345.png", requested=12.3)
        self.assertEqual(rec["timecode"], "00:00:12.345")
        self.assertEqual(rec["frame"], 370)
        self.assertEqual((rec["fps"], rec["fps_source"]), (30, "declared"))
        self.assertEqual(rec["index"], 3)
        self.assertEqual(rec["requested"], 12.3)

    def test_sampling_plans(self):
        self.assertEqual(video.plan_times(at="1,2.5,00:00:04"), [1.0, 2.5, 4.0])
        self.assertEqual(video.plan_times(every=2.0, duration=7.0), [0.0, 2.0, 4.0, 6.0])
        self.assertEqual(video.plan_times(every_frames=15, fps=30, duration=2.0), [0.0, 0.5, 1.0, 1.5])
        dense = video.plan_times(dense=(1.0, 1.1), fps=30)
        self.assertEqual(len(dense), 4)  # frames 30, 31, 32, 33
        self.assertAlmostEqual(dense[0], 1.0)
        self.assertAlmostEqual(dense[1] - dense[0], 1 / 30.0)

    def test_mid_frame_offset_for_video_seeks(self):
        self.assertAlmostEqual(video.seek_time(1.0, 30, mid_frame=True), 1.0 + 0.5 / 30)
        self.assertEqual(video.seek_time(1.0, 30, mid_frame=False), 1.0)


def fake(result=None, error=None):
    def run(*a, **kw):
        if error:
            raise video.EngineError(error)
        return dict(result)
    return run


NOTHING = {"browser": {"found": False, "searched": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"], "hint": "install Chrome"},
           "yt-dlp": {"found": False, "hint": "pipx install yt-dlp"}, "ffmpeg": {"found": False, "hint": "brew install ffmpeg"},
           "ffprobe": {"found": False, "hint": "ships with ffmpeg"}, "sips": {"found": False}}
EVERYTHING = {k: {"found": True, "path": "/x/" + k} for k in ("browser", "yt-dlp", "ffmpeg", "ffprobe", "sips")}


class Engines(unittest.TestCase):
    def test_chain_falls_through_in_order_and_records_attempts(self):
        res = video.run_chain([("http", fake(error="consent page")), ("browser", fake({"ok": True, "title": "T"})),
                               ("yt-dlp", fake({"ok": True, "title": "never"}))])
        self.assertEqual(res["engine"], "browser")
        self.assertEqual(res["title"], "T")
        self.assertEqual(res["attempts"], [{"engine": "http", "ok": False, "reason": "consent page"}, {"engine": "browser", "ok": True}])

    def test_all_engines_failing_is_a_structured_failure(self):
        res = video.run_chain([("http", fake(error="offline"))])
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "all_engines_failed")

    def test_engine_order_by_target_and_tools(self):
        yt = "https://www.youtube.com/watch?v=abcDEF12345"
        self.assertEqual(video.engine_names("info", yt, EVERYTHING), ["http", "browser", "yt-dlp"])
        self.assertEqual(video.engine_names("info", "/x/clip.mp4", EVERYTHING), ["ffprobe", "browser"])
        self.assertEqual(video.engine_names("captions", yt, EVERYTHING), ["http", "browser", "yt-dlp"])
        self.assertEqual(video.engine_names("frames", "/x/clip.mp4", EVERYTHING), ["ffmpeg", "browser"])
        self.assertEqual(video.engine_names("frames", yt, EVERYTHING), ["browser"])
        self.assertEqual(video.engine_names("info", yt, NOTHING), ["http"])
        self.assertEqual(video.engine_names("frames", yt, NOTHING), [])

    def test_frames_without_browser_says_what_is_needed(self):
        res = video.frames("https://www.youtube.com/watch?v=abcDEF12345", at="1,2", work=None, tools=NOTHING)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "needs_browser")
        self.assertIn("Chromium-family browser", res["message"])
        self.assertTrue(res["searched"])

    def test_scenes_without_ffmpeg_says_so(self):
        res = video.frames("/x/clip.mp4", scenes=True, work=None, tools=dict(EVERYTHING, ffmpeg={"found": False}))
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "needs_ffmpeg")
        self.assertIn("scene detection needs ffmpeg", res["message"])

    def test_local_info_without_any_tool(self):
        res = video.info("/x/clip.mp4", tools=NOTHING)
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "needs_tool")
        self.assertIn("ffprobe", res["message"])

    def test_captions_still_work_over_http_without_any_tool(self):
        page = read("watch-page.html")
        vtt = read("rolling-auto.vtt")

        def http_get(url, **kw):
            if "timedtext" in url:
                return {"ok": True, "status": 200, "body": vtt.encode(), "final_url": url}
            return {"ok": True, "status": 200, "body": page.encode(), "final_url": url}
        rec = video.captions("https://youtu.be/abcDEF12345", lang="en", tools=NOTHING, http=http_get)
        self.assertTrue(rec["ok"], rec)
        self.assertEqual(rec["engine"], "http")
        self.assertEqual(rec["track"]["language"], "en-GB")
        self.assertEqual(rec["transcript"][0]["text"], "so today we're looking at easing curves in motion")

    def test_empty_caption_files_explain_the_token_gate_and_the_options(self):
        page = read("watch-page.html")

        def http_get(url, **kw):
            body = b"" if "timedtext" in url else page.encode()
            return {"ok": True, "status": 200, "body": body, "final_url": url}
        rec = video.captions("https://youtu.be/abcDEF12345", lang="en", tools=NOTHING, http=http_get)
        self.assertFalse(rec["ok"])
        self.assertEqual(rec["reason"], "no_captions")
        self.assertIn("yt-dlp", rec["hint"])
        self.assertIn(".vtt", rec["hint"])
        self.assertEqual([t["language"] for t in rec["tracks"]], ["en", "en-GB", "de"])

    def test_player_error_screens_are_not_captured_as_frames(self):
        with self.assertRaises(video.EngineError) as ctx:
            video.check_prepared({"width": 0, "height": 0, "error": "Video player configuration error"})
        self.assertIn("configuration error", str(ctx.exception))
        with self.assertRaises(video.EngineError):
            video.check_prepared({"width": 640, "height": 360, "ad": True})
        self.assertEqual(video.check_prepared({"width": 640, "height": 360, "duration": 10.0})["width"], 640)

    def test_a_player_that_breaks_after_seeking_fails_fast_with_its_message(self):
        with self.assertRaises(video.EngineError) as ctx:
            video.check_seek({"time": 0, "ready": 0, "error": "Something went wrong. Refresh or try again later."}, 95.0)
        self.assertIn("Something went wrong", str(ctx.exception))
        self.assertIn("yt-dlp", str(ctx.exception))
        with self.assertRaises(video.EngineError):
            video.check_seek({"time": 0, "ready": 0}, 95.0)
        self.assertEqual(video.check_seek({"time": 95.02, "ready": 4}, 95.0)["time"], 95.02)

    def test_prepare_hides_native_media_controls_before_capture(self):
        self.assertIn("v.controls = false", video.PREPARE_JS)
        self.assertIn("-webkit-media-controls", video.PREPARE_JS)

    def test_page_scripts_never_wait_on_play_without_a_timeout(self):
        for js in (video.PREPARE_JS, video.FPS_JS, video.CAPTIONS_ON_JS):
            self.assertNotIn("await v.play()", js)

    def test_local_caption_sidecar_needs_no_tools(self):
        rec = video.captions(os.path.join(FIX, "sample.srt"), tools=NOTHING)
        self.assertTrue(rec["ok"])
        self.assertEqual(rec["engine"], "file")
        self.assertEqual(len(rec["cues"]), 3)


@unittest.skipUnless(os.environ.get("METADUMP_LIVE") == "1", "set METADUMP_LIVE=1 for network tests")
class Live(unittest.TestCase):
    URL = os.environ.get("METADUMP_LIVE_VIDEO", "https://www.youtube.com/watch?v=aqz-KE-bpKQ")

    def test_real_info_and_captions(self):
        rec = video.info(self.URL)
        self.assertTrue(rec["ok"], rec)
        self.assertGreater(rec["duration"], 0)
        cap = video.captions(self.URL)
        self.assertIn("attempts", cap)


if __name__ == "__main__":
    unittest.main()

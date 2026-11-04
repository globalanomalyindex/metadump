"""Tests for pixels.py (stdlib PNG codec) and images.py (collection, palettes, moodboards).

PNGs are built here with an independent forward encoder (all five filter types,
sub-byte depths, palettes with tRNS, 16-bit, Adam7) so the decoder is not tested
against itself. tests/fixtures/images/ holds small files made by real encoders
(Chrome's canvas encoder, macOS sips).
"""
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
FIX = os.path.join(HERE, "fixtures", "images")
sys.path.insert(0, SCRIPTS)

import pixels  # noqa: E402


# ---------------------------------------------------------------- independent forward PNG encoder (test helper)

def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def filter_row(ft, row, prev, bpp):
    out = bytearray()
    for i, x in enumerate(row):
        a = row[i - bpp] if i >= bpp else 0
        b = prev[i]
        c = prev[i - bpp] if i >= bpp else 0
        pred = [0, a, b, (a + b) // 2, _paeth(a, b, c)][ft]
        out.append((x - pred) & 0xFF)
    return bytes([ft]) + bytes(out)


def chunk(kind, data):
    return struct.pack("!I", len(data)) + kind + data + struct.pack("!I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def make_png(width, height, color_type, bit_depth, rows, filters=(0,), plte=None, trns=None):
    """rows: list of packed scanline bytes (no filter byte). Filters cycle per row."""
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
    bpp = max(1, channels * bit_depth // 8)
    prev = bytes(len(rows[0]))
    raw = b""
    for y, row in enumerate(rows):
        raw += filter_row(filters[y % len(filters)], row, prev, bpp)
        prev = row
    out = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, bit_depth, color_type, 0, 0, 0))
    if plte:
        out += chunk(b"PLTE", b"".join(bytes(c) for c in plte))
    if trns is not None:
        out += chunk(b"tRNS", trns)
    out += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    return out


def make_adam7_rgb(width, height, pixel):
    """Adam7-interlaced 8-bit RGB PNG; pixel(x, y) -> (r, g, b)."""
    passes = [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]
    raw = b""
    for x0, y0, dx, dy in passes:
        xs = list(range(x0, width, dx))
        ys = list(range(y0, height, dy))
        if not xs or not ys:
            continue
        prev = bytes(3 * len(xs))
        for k, y in enumerate(ys):
            row = b"".join(bytes(pixel(x, y)) for x in xs)
            raw += filter_row([1, 2, 3, 4, 0][k % 5], row, prev, 3)
            prev = row
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 1))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def rgb_rows(w, h, channels=3):
    return [bytes(((x * 37 + y * 91 + c * 53) % 256) for x in range(w) for c in range(channels)) for y in range(h)]


class PngDecode(unittest.TestCase):
    def test_rgb_all_filter_types(self):
        rows = rgb_rows(4, 5)
        img = pixels.decode_png(make_png(4, 5, 2, 8, rows, filters=(0, 1, 2, 3, 4)))
        self.assertEqual((img.width, img.height, img.channels), (4, 5, 3))
        self.assertEqual(bytes(img.pixels), b"".join(rows))

    def test_rgba_4x4(self):
        rows = rgb_rows(4, 4, channels=4)
        img = pixels.decode_png(make_png(4, 4, 6, 8, rows, filters=(4, 3, 2, 1)))
        self.assertEqual(img.channels, 4)
        self.assertEqual(bytes(img.pixels), b"".join(rows))

    def test_wide_rows_exercise_fast_paths(self):
        rows = rgb_rows(301, 3)
        img = pixels.decode_png(make_png(301, 3, 2, 8, rows, filters=(2, 1, 2)))
        self.assertEqual(bytes(img.pixels), b"".join(rows))

    def test_palette_with_transparency_expands_to_rgba(self):
        plte = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (10, 20, 30)]
        rows = [bytes([0, 1, 2, 3]), bytes([3, 2, 1, 0]), bytes([0, 0, 1, 1]), bytes([2, 2, 3, 3])]
        img = pixels.decode_png(make_png(4, 4, 3, 8, rows, filters=(0, 1), plte=plte, trns=bytes([255, 128])))
        self.assertEqual(img.channels, 4)
        self.assertEqual(img.pixel(0, 0), (255, 0, 0, 255))
        self.assertEqual(img.pixel(1, 0), (0, 255, 0, 128))
        self.assertEqual(img.pixel(3, 0), (10, 20, 30, 255))  # entries past tRNS are opaque

    def test_palette_two_bit_indices(self):
        plte = [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)]
        # 4 pixels per byte: indices 0,1,2,3 -> 0b00011011
        rows = [bytes([0b00011011]), bytes([0b11100100])]
        img = pixels.decode_png(make_png(4, 2, 3, 2, rows, plte=plte))
        self.assertEqual(img.channels, 3)
        self.assertEqual([img.pixel(x, 0) for x in range(4)], [(0, 0, 0), (85, 85, 85), (170, 170, 170), (255, 255, 255)])
        self.assertEqual(img.pixel(0, 1), (255, 255, 255))

    def test_one_bit_gray_scales_to_full_range(self):
        rows = [bytes([0b10100000]), bytes([0b01010000])]
        img = pixels.decode_png(make_png(4, 2, 0, 1, rows))
        self.assertEqual(img.channels, 1)
        self.assertEqual(list(img.pixels), [255, 0, 255, 0, 0, 255, 0, 255])

    def test_gray_alpha_8bit(self):
        rows = [bytes([10, 255, 20, 0]), bytes([30, 128, 40, 64])]
        img = pixels.decode_png(make_png(2, 2, 4, 8, rows, filters=(1, 2)))
        self.assertEqual(img.channels, 2)
        self.assertEqual(bytes(img.pixels), b"".join(rows))

    def test_sixteen_bit_rgb_keeps_high_byte(self):
        rows = [struct.pack("!6H", 0x1234, 0xABCD, 0xFF00, 0x0001, 0x8080, 0x7FFF)]
        img = pixels.decode_png(make_png(2, 1, 2, 16, rows, filters=(1,)))
        self.assertEqual(list(img.pixels), [0x12, 0xAB, 0xFF, 0x00, 0x80, 0x7F])

    def test_adam7_interlaced(self):
        def px(x, y):
            return ((x * 40) % 256, (y * 50) % 256, (x * y * 7) % 256)
        img = pixels.decode_png(make_adam7_rgb(9, 7, px))
        for y in range(7):
            for x in range(9):
                self.assertEqual(img.pixel(x, y), px(x, y))

    def test_real_chrome_png_fixture(self):
        with open(os.path.join(FIX, "quadrants-6x4-chrome.png"), "rb") as f:
            img = pixels.decode_png(f.read())
        self.assertEqual((img.width, img.height), (6, 4))
        self.assertEqual(img.pixel(0, 0)[:3], (255, 0, 0))
        self.assertEqual(img.pixel(5, 0)[:3], (0, 255, 0))
        self.assertEqual(img.pixel(1, 3)[:3], (0, 0, 255))
        self.assertEqual(img.pixel(5, 3)[3], 0)

    def test_bad_signature_and_truncation_raise_png_error(self):
        with self.assertRaises(pixels.PNGError):
            pixels.decode_png(b"GIF89a....")
        good = make_png(4, 4, 2, 8, rgb_rows(4, 4))
        with self.assertRaises(pixels.PNGError):
            pixels.decode_png(good[:40])

    def test_png_size_reads_ihdr_only(self):
        self.assertEqual(pixels.png_size(make_png(7, 3, 2, 8, rgb_rows(7, 3))), (7, 3))
        self.assertIsNone(pixels.png_size(b"nope"))


class PngEncodeAndConvert(unittest.TestCase):
    def test_encode_roundtrip_for_each_channel_count(self):
        for ch in (1, 2, 3, 4):
            data = bytes((i * 13) % 256 for i in range(5 * 3 * ch))
            img = pixels.decode_png(pixels.encode_png(5, 3, ch, data))
            self.assertEqual((img.width, img.height, img.channels), (5, 3, ch))
            self.assertEqual(bytes(img.pixels), data)

    def test_to_rgb_composites_alpha_on_white(self):
        img = pixels.Image(2, 1, 4, bytes([0, 0, 0, 0, 0, 0, 0, 255]))
        rgb = pixels.to_rgb(img)
        self.assertEqual(rgb.channels, 3)
        self.assertEqual(list(rgb.pixels), [255, 255, 255, 0, 0, 0])

    def test_to_gray_uses_luma_weights(self):
        img = pixels.Image(3, 1, 3, bytes([255, 0, 0, 0, 255, 0, 255, 255, 255]))
        g = pixels.to_gray(img)
        self.assertEqual(g.channels, 1)
        self.assertEqual(list(g.pixels), [76, 150, 255])

    def test_downscale_box_averages(self):
        g = pixels.Image(4, 2, 1, bytes([0, 10, 100, 200, 20, 30, 0, 100]))
        small = pixels.downscale(g, 2)
        self.assertEqual((small.width, small.height), (2, 1))
        self.assertEqual(list(small.pixels), [15, 100])
        same = pixels.downscale(g, 10)
        self.assertEqual(same.width, 4)



import images  # noqa: E402


def blocks_png():
    """8x6 RGB: a 4x3 yellow block (25%) on blue (75%)."""
    px = bytearray()
    for y in range(6):
        for x in range(8):
            px += bytes((240, 200, 20)) if (x < 4 and y < 3) else bytes((30, 100, 200))
    return pixels.encode_png(8, 6, 3, bytes(px))


class Formats(unittest.TestCase):
    def read(self, name):
        with open(os.path.join(FIX, name), "rb") as f:
            return f.read()

    def test_sniff_formats_from_magic_bytes(self):
        self.assertEqual(images.sniff_format(blocks_png()), "png")
        self.assertEqual(images.sniff_format(self.read("blocks-8x6.jpg")), "jpeg")
        self.assertEqual(images.sniff_format(self.read("blocks-8x6.webp")), "webp")
        self.assertEqual(images.sniff_format(self.read("blocks-8x6.gif")), "gif")
        self.assertEqual(images.sniff_format(b"\x00\x00\x00\x1cftypavif\x00\x00\x00\x00"), "avif")
        self.assertEqual(images.sniff_format(b"<?xml version='1.0'?><svg xmlns='http://www.w3.org/2000/svg'></svg>"), "svg")
        self.assertIsNone(images.sniff_format(b"hello world"))

    def test_dimensions_without_decoding(self):
        for name in ("blocks-8x6.jpg", "blocks-8x6.webp", "blocks-8x6.gif"):
            self.assertEqual(images.image_size(self.read(name)), (8, 6), name)
        self.assertEqual(images.image_size(blocks_png()), (8, 6))
        self.assertIsNone(images.image_size(b"nope"))


class Palette(unittest.TestCase):
    def test_top_colors_with_proportions_and_hex(self):
        pal = images.palette(pixels.decode_png(blocks_png()), top=4)
        self.assertEqual([c["hex"] for c in pal], ["#1E64C8", "#F0C814"])
        self.assertAlmostEqual(pal[0]["share"], 0.75, places=3)
        self.assertAlmostEqual(pal[1]["share"], 0.25, places=3)
        self.assertEqual(pal[0]["rgb"], [30, 100, 200])

    def test_near_colors_merge_and_transparent_pixels_are_ignored(self):
        px = bytearray()
        for i in range(100):
            if i < 50:
                px += bytes((200, 10, 10, 255)) if i % 2 else bytes((204, 14, 12, 255))
            elif i < 90:
                px += bytes((0, 0, 0, 0))
            else:
                px += bytes((10, 10, 200, 255))
        pal = images.palette(pixels.Image(10, 10, 4, bytes(px)), top=5)
        self.assertEqual(len(pal), 2)
        self.assertAlmostEqual(pal[0]["share"], 50 / 60.0, places=3)
        self.assertTrue(pal[0]["hex"].startswith("#C"))

    def test_png_palette_needs_no_converter(self):
        pal, engine, note = images.palette_for_bytes(blocks_png(), converters=[])
        self.assertEqual(engine, "png")
        self.assertEqual(pal[0]["hex"], "#1E64C8")
        self.assertIsNone(note)


class Conversion(unittest.TestCase):
    def test_fallback_order_uses_first_converter_that_works(self):
        calls = []

        def broken(data, fmt, max_size):
            calls.append("browser")
            raise images.ConversionError("canvas refused")

        def works(data, fmt, max_size):
            calls.append("sips")
            return blocks_png()
        png, engine, attempts = images.to_png(b"\xff\xd8\xff...", "jpeg", [("browser", broken), ("sips", works), ("ffmpeg", works)])
        self.assertEqual(engine, "sips")
        self.assertEqual(calls, ["browser", "sips"])
        self.assertEqual(attempts[0], {"engine": "browser", "ok": False, "reason": "canvas refused"})
        self.assertEqual(pixels.png_size(png), (8, 6))

    def test_no_converter_means_palette_unavailable_with_reason(self):
        pal, engine, note = images.palette_for_bytes(b"\xff\xd8\xff\xe0 fake jpeg", converters=[])
        self.assertIsNone(pal)
        self.assertIsNone(engine)
        self.assertTrue(note.startswith("palette unavailable:"))
        self.assertIn("jpeg", note)

    def test_default_chain_follows_detected_tools(self):
        names = [n for n, _fn in images.default_converters(
            {"browser": {"found": True, "path": "/x/chrome"}, "sips": {"found": True, "path": "/usr/bin/sips"},
             "ffmpeg": {"found": False, "path": None}})]
        self.assertEqual(names, ["browser", "sips"])
        self.assertEqual(images.default_converters({"browser": {"found": False}, "sips": {"found": False}, "ffmpeg": {"found": False}}), [])


class Manifest(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.work, ignore_errors=True)

    def test_add_image_writes_file_and_dedupes_by_hash(self):
        man = images.load_manifest(self.work)
        src1 = {"kind": "file", "path": "/refs/a.png"}
        rec, new = images.add_image(man, self.work, blocks_png(), src1, origin="user", converters=[], alt="blue field")
        self.assertTrue(new)
        self.assertTrue(rec["id"].startswith("img-"))
        self.assertEqual(rec["format"], "png")
        self.assertEqual(rec["decoded"], {"width": 8, "height": 6})
        self.assertEqual(rec["prov_hint"], "reference_observed")
        self.assertEqual(rec["palette"][0]["hex"], "#1E64C8")
        self.assertTrue(os.path.exists(os.path.join(self.work, "images", rec["file"])))
        again, new2 = images.add_image(man, self.work, blocks_png(), {"kind": "url", "url": "https://x.example/a.png"},
                                       origin="web", converters=[])
        self.assertFalse(new2)
        self.assertEqual(again["id"], rec["id"])
        self.assertEqual(len(man["images"]), 1)
        self.assertEqual(again["also_from"][0]["url"], "https://x.example/a.png")
        images.save_manifest(man, self.work)
        with open(os.path.join(self.work, "images", "manifest.json")) as f:
            on_disk = json.load(f)
        self.assertEqual(on_disk["schema"], "metadump-images/1")
        for key in ("id", "file", "sha256", "bytes", "format", "declared", "decoded", "source", "alt", "origin",
                    "prov_hint", "palette", "added"):
            self.assertIn(key, on_disk["images"][0])

    def test_web_images_are_researched_and_keep_page_license(self):
        man = images.load_manifest(self.work)
        rec, _ = images.add_image(man, self.work, blocks_png(), {"kind": "page", "url": "https://x.example/i.png",
                                                                 "page": "https://x.example/post"},
                                  origin="web", converters=[], license="https://creativecommons.org/licenses/by/4.0/",
                                  declared={"width": 800, "height": 600})
        self.assertEqual(rec["prov_hint"], "researched")
        self.assertEqual(rec["license"], "https://creativecommons.org/licenses/by/4.0/")
        self.assertEqual(rec["declared"], {"width": 800, "height": 600})

    def test_page_records_yield_image_candidates(self):
        page = {"url": "https://x.example/post", "user_supplied": False, "metadata": {"title": "Post", "license": "CC-BY"},
                "images": [{"src": "https://x.example/big.jpg", "alt": "big", "width": 900, "height": 600, "in_main": True, "caption": "cap"},
                           {"src": "https://x.example/icon.png", "alt": "", "width": 16, "height": 16, "in_main": False},
                           {"src": None, "data_uri": {"media_type": "image/png", "bytes": 70}, "in_main": True},
                           {"src": "https://x.example/side.jpg", "alt": "side", "in_main": False}]}
        cands = images.page_image_candidates(page, max_per_page=5, min_size=64)
        self.assertEqual([c["url"] for c in cands], ["https://x.example/big.jpg", "https://x.example/side.jpg"])
        self.assertEqual(cands[0]["origin"], "web")
        self.assertEqual(cands[0]["license"], "CC-BY")
        self.assertEqual(cands[0]["source"]["page"], "https://x.example/post")


class PageImageNoise(unittest.TestCase):
    """0.5.1: images from scraped pages skip logos, icons and blank single-color images."""

    def test_logos_icons_and_sprites_are_not_candidates(self):
        page = {"url": "https://kit.example/cards", "user_supplied": False, "metadata": {"title": "Cards"},
                "images": [{"src": "https://kit.example/img/kendo-ui-logo.svg", "alt": "Kendo UI for Angular", "in_main": True},
                           {"src": "https://kit.example/img/a.png", "alt": "Telerik logo", "in_main": True},
                           {"src": "https://kit.example/icons/cart.svg", "alt": "", "in_main": True},
                           {"src": "https://kit.example/ui-sprite.png", "alt": "", "in_main": True},
                           {"src": "https://kit.example/shots/card-grid.jpg", "alt": "compact product card grid", "width": 900, "in_main": True}]}
        cands = images.page_image_candidates(page, max_per_page=12, min_size=64)
        self.assertEqual([c["url"] for c in cands], ["https://kit.example/shots/card-grid.jpg"])

    def test_blank_single_color_page_images_are_skipped_with_a_reason(self):
        work = tempfile.mkdtemp()
        os.makedirs(os.path.join(work, "pages"))
        white = make_png(8, 8, 2, 8, [bytes([255, 255, 255] * 8)] * 8)
        record = {"schema": "metadump-page/1", "key": "k1", "url": "https://kit.example/cards", "user_supplied": False,
                  "outcome": {"ok": True}, "metadata": {"title": "Cards"},
                  "images": [{"src": "https://kit.example/blank.png", "alt": "placeholder", "width": 400, "in_main": True},
                             {"src": "https://kit.example/grid.png", "alt": "card grid", "width": 400, "in_main": True}]}
        with open(os.path.join(work, "pages", "k1.json"), "w") as f:
            json.dump(record, f)

        class Net:  # the network boundary
            def fetch(self, u):
                return {"ok": True, "body": white if u.endswith("blank.png") else blocks_png(), "content_type": "image/png"}

        summary = images.collect(work, from_pages=True, fetcher=Net(), converters=[])
        self.assertEqual(summary["added"], 1)
        self.assertEqual([r["source"]["url"] for r in images.load_manifest(work)["images"]], ["https://kit.example/grid.png"])
        reasons = {s["input"]: s["reason"] for s in summary["skipped"]}
        self.assertIn("single color", reasons["https://kit.example/blank.png"])


class FoundImages(unittest.TestCase):
    """0.3.0: images that discovery found online, collected from a found-images file."""

    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.work, ignore_errors=True)

    def test_found_images_are_web_found_and_keep_page_title_and_license(self):
        url = "https://upload.wikimedia.org/x/shell.png"
        found = os.path.join(self.work, "found.json")
        with open(found, "w") as f:
            json.dump([{"url": url, "page": "https://commons.wikimedia.org/wiki/File:Shell.png", "title": "Shell",
                        "license": "CC BY-SA 4.0", "answers": "what the shell looks like"}], f)

        class Net:  # the network boundary: serves one known PNG
            def fetch(self, u):
                return {"ok": True, "body": blocks_png(), "content_type": "image/png"} if u == url else {"ok": False, "reason": "http 404"}

        summary = images.collect(self.work, found=found, origin="user", fetcher=Net(), converters=[])
        man = images.load_manifest(self.work)
        self.assertEqual(len(man["images"]), 1)
        rec = man["images"][0]
        self.assertEqual(rec["origin"], "web")  # found online, whatever --origin says
        self.assertEqual(rec["prov_hint"], "researched")
        self.assertEqual(rec["license"], "CC BY-SA 4.0")
        self.assertEqual(rec["source"], {"kind": "url", "url": url, "page": "https://commons.wikimedia.org/wiki/File:Shell.png",
                                         "title": "Shell"})
        self.assertEqual(rec["palette"][0]["hex"], "#1E64C8")
        self.assertEqual(summary["added"], 1)

    def test_found_file_may_wrap_the_list_and_bad_urls_are_skipped_with_a_reason(self):
        found = os.path.join(self.work, "found.json")
        with open(found, "w") as f:
            json.dump({"images": [{"url": "https://x.example/gone.png"}, {"page": "no url here"}]}, f)

        class Net:
            def fetch(self, u):
                return {"ok": False, "reason": "http 404"}

        summary = images.collect(self.work, found=found, fetcher=Net(), converters=[])
        self.assertEqual(summary["added"], 0)
        self.assertEqual([s["input"] for s in summary["skipped"]], ["https://x.example/gone.png"])
        self.assertIn("404", summary["skipped"][0]["reason"])


class PageScreenshots(unittest.TestCase):
    """0.4.0: screenshots of visited pages go on the moodboard."""

    def setUp(self):
        self.work = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.work, "pages"))

    def tearDown(self):
        import shutil
        shutil.rmtree(self.work, ignore_errors=True)

    def test_collect_from_pages_includes_each_pages_screenshot(self):
        with open(os.path.join(self.work, "pages", "abc123.png"), "wb") as f:
            f.write(blocks_png())
        record = {"schema": "metadump-page/1", "key": "abc123", "url": "https://shop.example/minimal", "user_supplied": False,
                  "outcome": {"ok": True}, "metadata": {"title": "Minimal shop"}, "images": [], "screenshot": "abc123.png"}
        with open(os.path.join(self.work, "pages", "abc123.json"), "w") as f:
            json.dump(record, f)
        summary = images.collect(self.work, from_pages=True, converters=[])
        self.assertEqual(summary["added"], 1)
        rec = images.load_manifest(self.work)["images"][0]
        self.assertEqual(rec["source"], {"kind": "screenshot", "page": "https://shop.example/minimal", "title": "Minimal shop"})
        self.assertEqual(rec["origin"], "web")
        self.assertEqual(rec["prov_hint"], "researched")
        self.assertEqual(rec["caption"], "Screenshot of Minimal shop")
        self.assertEqual(rec["palette"][0]["hex"], "#1E64C8")


class Moodboard(unittest.TestCase):
    def manifest(self):
        return {"schema": "metadump-images/1", "images": [
            {"id": "img-aaa", "file": "aaa.png", "format": "png", "alt": "blue <field> & sun", "caption": "Edge-lit sheet",
             "source": {"kind": "page", "url": "https://x.example/i.png", "page": "https://x.example/post", "page_title": "Post"},
             "origin": "web", "prov_hint": "researched", "decoded": {"width": 8, "height": 6},
             "palette": [{"hex": "#1E64C8", "rgb": [30, 100, 200], "share": 0.75}, {"hex": "#F0C814", "rgb": [240, 200, 20], "share": 0.25}]},
            {"id": "img-bbb", "file": "bbb.jpg", "format": "jpeg", "alt": "<script>alert(1)</script>", "caption": None,
             "source": {"kind": "video", "video": "https://video.example/watch?v=1", "timecode": "00:00:12.345", "frame": 370, "fps": 30},
             "origin": "user", "prov_hint": "reference_observed", "decoded": None, "palette": None,
             "palette_note": "palette unavailable: no converter"}]}

    def test_html_has_captions_sources_chips_provenance_and_relative_paths(self):
        html = images.moodboard_html(self.manifest(), "luminous", href_for=lambda r: "luminous.moodboard/" + r["file"])
        self.assertIn("Edge-lit sheet", html)
        self.assertIn("blue &lt;field&gt; &amp; sun", html)
        self.assertIn('href="https://x.example/post"', html)
        self.assertIn('href="https://video.example/watch?v=1"', html)
        self.assertIn("00:00:12.345", html)
        self.assertIn("#1E64C8", html)
        self.assertIn("75%", html)
        self.assertIn("researched", html)
        self.assertIn("reference_observed", html)
        self.assertIn('src="luminous.moodboard/aaa.png"', html)
        self.assertIn("palette unavailable", html)
        self.assertNotIn("<script", html)
        self.assertNotIn("<link", html)
        import re
        for src in re.findall(r'src="([^"]+)"', html):
            self.assertFalse(re.match(r"^(https?:|//|/)", src), src)

    def test_screenshots_and_found_images_link_to_the_page_they_came_from(self):
        man = {"images": [
            {"id": "img-s", "file": "s.png", "source": {"kind": "screenshot", "page": "https://shop.example/minimal", "title": "Minimal shop"},
             "origin": "web", "prov_hint": "researched", "palette": [], "caption": "Screenshot of Minimal shop"},
            {"id": "img-f", "file": "f.png", "source": {"kind": "url", "url": "https://upload.wikimedia.org/x/shell.jpg",
                                                         "page": "https://commons.wikimedia.org/wiki/File:Shell.jpg", "title": "Shell"},
             "origin": "web", "prov_hint": "researched", "palette": []}]}
        html = images.moodboard_html(man, "shop")
        self.assertIn('<a href="https://shop.example/minimal">Minimal shop</a> (screenshot)', html)
        self.assertIn('<a href="https://commons.wikimedia.org/wiki/File:Shell.jpg">Shell</a>', html)

    def test_build_moodboard_copies_images_beside_the_html(self):
        root = tempfile.mkdtemp()
        work = os.path.join(root, "metadumps", ".work", "demo")
        man = images.load_manifest(work)
        images.add_image(man, work, blocks_png(), {"kind": "file", "path": "/refs/a.png"}, origin="user", converters=[])
        images.save_manifest(man, work)
        res = images.build_moodboard(work, render_png=False)
        self.assertEqual(res["html"], os.path.join(root, "metadumps", "demo.moodboard.html"))
        with open(res["html"]) as f:
            html = f.read()
        rec = man["images"][0]
        self.assertIn('src="demo.moodboard/%s"' % rec["file"], html)
        self.assertTrue(os.path.exists(os.path.join(root, "metadumps", "demo.moodboard", rec["file"])))
        self.assertIsNone(res["png"])


if __name__ == "__main__":
    unittest.main()

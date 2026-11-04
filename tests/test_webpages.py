"""Tests for skills/metadump/scripts/webpages.py (clean-room page fetch, clean, chunk, crawl).

No network: HTTP is replaced by injected fakes, files come from tests/fixtures/pages/.
Set METADUMP_LIVE=1 to also run one real fetch of https://example.com/.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
FIX = os.path.join(HERE, "fixtures", "pages")
sys.path.insert(0, SCRIPTS)

import webpages  # noqa: E402

BASE = "https://optics.example/guides/acrylic-light?ref=1"


def fixture(name):
    with open(os.path.join(FIX, name), "rb") as f:
        return f.read()


def article(use_main=True):
    html = fixture("article.html").decode("utf-8")
    return webpages.process_html(html, BASE, use_main=use_main)


class CleanText(unittest.TestCase):
    def setUp(self):
        self.rec = article()
        self.text = self.rec["text"]

    def test_headings_keep_their_levels(self):
        self.assertIn("# Acrylic light guides", self.text)
        self.assertIn("\n## Why the edges glow\n", self.text)
        self.assertIn("\n### Measured transmission\n", self.text)

    def test_paragraphs_drop_inline_emphasis_and_keep_link_text(self):
        self.assertIn("Cast acrylic (PMMA) carries light by total internal reflection, so a sheet lit from one edge glows at the far edge. "
                      "See the physics or our fiber guide.", self.text)

    def test_nested_and_ordered_lists(self):
        self.assertIn("- Polished edges: bright line of light\n- Frosted edges: soft glow\n  - Sanded at 400 grit\n  - Flame polished", self.text)
        self.assertIn("1. Cut the sheet\n2. Polish the edge", self.text)

    def test_table_becomes_pipe_rows_with_header_separator(self):
        self.assertIn("| Thickness | Transmission |\n| --- | --- |\n| 3 mm | 92% |\n| 10 mm | 90% |", self.text)

    def test_pre_keeps_line_breaks_and_blockquote_is_marked(self):
        self.assertIn("```\nedge_lux = source_lux\n    * 0.92\n```", self.text)
        self.assertIn("> Light goes where the surface lets it.", self.text)

    def test_images_in_flow_become_alt_placeholders(self):
        self.assertIn("[image: A lit acrylic edge]", self.text)
        self.assertIn("Edge-lit sheet, 10 mm.", self.text)

    def test_boilerplate_hidden_and_junk_removed(self):
        for gone in ("Guides", "Copyright Optics Notes", "Related post", "hidden", "Also hidden", "Decorative text",
                     "Template text", "svg text", "Enable JavaScript", "tracker", "color: red"):
            self.assertNotIn(gone, self.text, gone)

    def test_article_header_and_footer_are_content_not_chrome(self):
        self.assertIn("By Sam Example", self.text)
        self.assertIn("Filed under optics.", self.text)

    def test_outline_matches_text_offsets(self):
        outline = self.rec["outline"]
        self.assertEqual([(h["level"], h["text"]) for h in outline],
                         [(1, "Acrylic light guides"), (2, "Why the edges glow"), (3, "Measured transmission")])
        for h in outline:
            self.assertTrue(self.text[h["offset"]:].startswith("#" * h["level"] + " " + h["text"]))

    def test_word_count_and_content_hash(self):
        self.assertGreater(self.rec["word_count"], 60)
        self.assertTrue(self.rec["content_hash"].startswith("sha256:"))
        self.assertEqual(self.rec["content_hash"], article()["content_hash"])

    def test_main_method_reports_main_element(self):
        self.assertEqual(self.rec["main"]["method"], "main element")


class Metadata(unittest.TestCase):
    def setUp(self):
        self.m = article()["metadata"]

    def test_title_description_lang_canonical_favicon_license(self):
        self.assertEqual(self.m["title"], "Acrylic Light Guides & Edge Glow")
        self.assertEqual(self.m["description"], "How cast acrylic carries light to its edges.")
        self.assertEqual(self.m["lang"], "en-GB")
        self.assertEqual(self.m["canonical"], "https://optics.example/guides/acrylic-light")
        self.assertEqual(self.m["favicon"], "https://optics.example/static/favicon.png")
        self.assertEqual(self.m["license"], "https://creativecommons.org/licenses/by/4.0/")
        self.assertEqual(self.m["author"], "Sam Example")

    def test_open_graph_and_twitter_fields(self):
        og = self.m["open_graph"]
        self.assertEqual(og["title"], "Acrylic light guides")
        self.assertEqual(og["image"], "https://optics.example/img/og-edge.jpg")
        self.assertEqual(og["site_name"], "Optics Notes")
        self.assertEqual(og["type"], "article")
        tw = self.m["twitter"]
        self.assertEqual(tw["card"], "summary_large_image")
        self.assertEqual(tw["image"], "https://cdn.optics.example/tw.jpg")

    def test_json_ld_valid_and_invalid_blocks(self):
        blocks = self.m["json_ld"]
        self.assertEqual(len(blocks), 2)
        self.assertTrue(blocks[0]["valid"])
        self.assertEqual(blocks[0]["data"]["@type"], "Article")
        self.assertFalse(blocks[1]["valid"])
        self.assertIn("not json", blocks[1]["raw"])

    def test_dates_from_meta_and_json_ld(self):
        self.assertEqual(self.m["published"], "2025-03-02T10:00:00Z")
        self.assertEqual(self.m["modified"], "2025-04-11")


class Links(unittest.TestCase):
    def setUp(self):
        self.links = {l["url"]: l for l in article()["links"]}

    def test_relative_links_resolve_against_the_page(self):
        self.assertIn("https://optics.example/guides/fiber", self.links)
        self.assertIn("https://optics.example/guides", self.links)

    def test_same_host_and_nofollow_flags(self):
        wiki = self.links["https://en.wikipedia.org/wiki/Total_internal_reflection"]
        self.assertFalse(wiki["same_host"])
        self.assertTrue(wiki["nofollow"])
        self.assertTrue(self.links["https://optics.example/guides/fiber"]["same_host"])
        self.assertFalse(self.links["https://optics.example/guides/fiber"]["nofollow"])

    def test_mail_and_tel_kept_fragment_and_script_links_dropped(self):
        self.assertIn("mailto:hello@optics.example", self.links)
        self.assertIn("tel:+15550100", self.links)
        self.assertFalse(any(u.startswith("javascript:") or "#" in u for u in self.links))

    def test_local_file_keeps_file_links_resolved_against_its_path(self):
        rec = webpages.process_html(fixture("article.html").decode(), "file:///docs/site/article.html")
        urls = [l["url"] for l in rec["links"]]
        self.assertIn("file:///guides/fiber", urls)
        self.assertIn("https://en.wikipedia.org/wiki/Total_internal_reflection", urls)

    def test_in_main_flag_and_link_text(self):
        self.assertTrue(self.links["https://optics.example/guides/fiber"]["in_main"])
        self.assertFalse(self.links["https://optics.example/about"]["in_main"])
        self.assertEqual(self.links["https://optics.example/guides/fiber"]["text"], "fiber guide")


class Images(unittest.TestCase):
    def setUp(self):
        self.images = article()["images"]

    def test_srcset_first_candidate_alt_dimensions_caption(self):
        edge = [i for i in self.images if i.get("alt") == "A lit acrylic edge"][0]
        self.assertEqual(edge["src"], "https://optics.example/img/edge.jpg")
        self.assertEqual(edge["srcset_first"], "https://optics.example/img/edge-800.jpg")
        self.assertEqual((edge["width"], edge["height"]), (800, 533))
        self.assertEqual(edge["caption"], "Edge-lit sheet, 10 mm.")
        self.assertTrue(edge["in_main"])

    def test_dimensions_from_inline_style(self):
        inline = [i for i in self.images if (i.get("src") or "").endswith("/img/inline.png")][0]
        self.assertEqual((inline["width"], inline["height"]), (320, 200))
        self.assertEqual(inline["alt"], "")

    def test_data_uri_is_recorded_not_inlined(self):
        d = [i for i in self.images if i.get("data_uri")][0]
        self.assertIsNone(d["src"])
        self.assertEqual(d["data_uri"]["media_type"], "image/png")
        self.assertGreater(d["data_uri"]["bytes"], 50)
        self.assertNotIn("iVBOR", json.dumps(self.images))


class MainContent(unittest.TestCase):
    def test_density_heuristic_finds_content_on_nav_heavy_page(self):
        rec = webpages.process_html(fixture("nav-heavy.html").decode(), "https://shop.example/aero")
        self.assertEqual(rec["main"]["method"], "text density")
        self.assertIn("## The Aero collection", rec["text"])
        self.assertIn("glow from within the material", rec["text"])
        for gone in ("Alpha products", "Sale", "Terms", "We use cookies"):
            self.assertNotIn(gone, rec["text"])
        self.assertTrue(rec["flags"]["consent_banner_removed"])
        self.assertFalse(rec["flags"]["consent_wall"])

    def test_heuristic_off_renders_the_whole_body_minus_banners(self):
        rec = webpages.process_html(fixture("nav-heavy.html").decode(), "https://shop.example/aero", use_main=False)
        self.assertEqual(rec["main"]["method"], "whole body")
        self.assertIn("Alpha products and accessories", rec["text"])
        self.assertIn("glow from within the material", rec["text"])
        self.assertNotIn("We use cookies", rec["text"])

    def test_article_page_with_heuristic_off_still_drops_site_chrome(self):
        text = article(use_main=False)["text"]
        self.assertIn("Cast acrylic (PMMA)", text)
        self.assertNotIn("Copyright Optics Notes", text)


class Robustness(unittest.TestCase):
    def test_malformed_html_never_raises_and_keeps_text(self):
        res = webpages.process_document({"ok": True, "url": "file:///x/malformed.html", "final_url": "file:///x/malformed.html",
                                         "status": None, "content_type": "text/html", "charset": None,
                                         "body": fixture("malformed.html")})
        self.assertTrue(res["outcome"]["ok"])
        self.assertIn("First para bold both italic?", res["text"])
        self.assertIn("Second para without close", res["text"])
        self.assertIn("| cell one | cell two |", res["text"])
        self.assertIn("- one\n- two", res["text"])
        self.assertIn("&bogus; entity & done", res["text"])
        self.assertEqual(res["images"][0]["width"], 12)

    def test_garbage_inputs_never_raise(self):
        for junk in ("", "<", "<<<>>>", "</p></div>", "<table><td>", "<!--", "<script>", "\x00\x01\x02", "<a href=>x</a>",
                     "<img srcset=', , ,'>", "<meta property=og:image content>", "<p>" * 2000,
                     "<div>" * 3000 + "deep", "<b>" * 3000 + "deep", "<ul><li>" * 1500 + "x"):
            rec = webpages.process_html(junk, "https://x.example/")
            self.assertIn("text", rec)

    def test_thin_page_and_consent_wall_flags(self):
        html = ("<html><body><div class='wall'><h1>Before you continue</h1><p>We use cookies and data to deliver our services. "
                "Accept all or reject all, or manage privacy settings.</p></div></body></html>")
        rec = webpages.process_html(html, "https://news.example/")
        self.assertTrue(rec["flags"]["thin_content"])
        self.assertTrue(rec["flags"]["consent_wall"])

    def test_login_wall_flag(self):
        html = "<form><h1>Sign in</h1><input name=u><input type=password name=p><a href=/forgot>Forgot password?</a> <button>Log in</button></form>"
        rec = webpages.process_html(html, "https://app.example/login")
        self.assertTrue(rec["flags"]["login_wall"])


class ContentTypeGate(unittest.TestCase):
    def doc(self, ctype, body):
        return webpages.process_document({"ok": True, "url": "https://x.example/f", "final_url": "https://x.example/f", "status": 200,
                                          "content_type": ctype, "charset": None, "body": body})

    def test_html_and_xhtml_parse(self):
        self.assertIn("# Hi", self.doc("application/xhtml+xml", b"<html><body><h1>Hi</h1></body></html>")["text"])

    def test_plain_text_and_markdown_pass_through(self):
        md = self.doc("text/markdown", b"# Title\n\nSome *words* here.\n\n## Part\n\nMore.")
        self.assertIn("Some *words* here.", md["text"])
        self.assertEqual([h["text"] for h in md["outline"]], ["Title", "Part"])
        self.assertEqual(self.doc("text/plain", b"just text")["text"], "just text")

    def test_json_is_pretty_printed_block(self):
        rec = self.doc("application/json", b'{"b": 1, "a": [1, 2]}')
        self.assertTrue(rec["text"].startswith("```json\n{\n"))
        self.assertIn('"a": [', rec["text"])

    def test_pdf_and_binary_are_unsupported_not_parsed(self):
        rec = self.doc("application/pdf", b"%PDF-1.7 ...")
        self.assertFalse(rec["outcome"]["ok"])
        self.assertEqual(rec["outcome"]["reason"], "unsupported_type")
        self.assertEqual(rec["text"], "")
        self.assertEqual(rec["fetch"]["bytes"], 12)

    def test_charset_from_meta_tag(self):
        body = '<html><head><meta charset="iso-8859-1"></head><body><p>caf\xe9</p></body></html>'.encode("latin-1")
        self.assertIn("café", self.doc("text/html", body)["text"])


class Chunking(unittest.TestCase):
    def make_text(self):
        parts = []
        for s in range(3):
            parts.append("## Section %d" % s)
            for p in range(4):
                parts.append(" ".join("word%d_%d_%d." % (s, p, w) if w % 9 == 8 else "word%d_%d_%d" % (s, p, w) for w in range(60)))
        return "\n\n".join(parts)

    def outline_of(self, text):
        return webpages.markdown_outline(text)

    def test_empty_page_has_no_chunks(self):
        self.assertEqual(webpages.chunk_text("", []), [])

    def test_short_page_is_one_chunk_with_full_span(self):
        chunks = webpages.chunk_text("# T\n\nshort body", self.outline_of("# T\n\nshort body"), url="u", fetched="f")
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0]["span"], [0, len("# T\n\nshort body")])
        self.assertEqual(chunks[0]["heading_path"], ["T"])
        self.assertEqual(chunks[0]["url"], "u")
        self.assertEqual(chunks[0]["fetched"], "f")

    def test_spans_index_the_clean_text_and_sizes_respect_target(self):
        text = self.make_text()
        chunks = webpages.chunk_text(text, self.outline_of(text), target_tokens=200, overlap_tokens=20)
        self.assertGreater(len(chunks), 3)
        for i, c in enumerate(chunks):
            self.assertEqual(c["index"], i)
            self.assertEqual(text[c["span"][0]:c["span"][1]], c["text"])
            self.assertLessEqual(c["tokens"], 200 + 25)
            self.assertEqual(c["tokens"], -(-len(c["text"]) // 4))

    def test_no_cut_inside_a_word(self):
        text = self.make_text()
        for c in webpages.chunk_text(text, self.outline_of(text), target_tokens=120, overlap_tokens=15):
            s, e = c["span"]
            self.assertTrue(s == 0 or not (text[s - 1].isalnum() and text[s].isalnum()), text[s - 5:s + 5])
            self.assertTrue(e == len(text) or not (text[e - 1].isalnum() and text[e].isalnum()), text[e - 5:e + 5])

    def test_cuts_prefer_heading_boundaries_and_carry_heading_paths(self):
        text = self.make_text()
        chunks = webpages.chunk_text(text, self.outline_of(text), target_tokens=450, overlap_tokens=20)
        starts = [c["text"].split("\n", 1)[0] for c in chunks]
        self.assertIn("## Section 1", starts)
        self.assertIn("## Section 2", starts)
        sec2 = [c for c in chunks if c["text"].startswith("## Section 2")][0]
        self.assertEqual(sec2["heading_path"], ["Section 2"])

    def test_overlap_repeats_text_within_a_section(self):
        text = "\n\n".join("Sentence number %d is here." % i for i in range(80))
        chunks = webpages.chunk_text(text, [], target_tokens=100, overlap_tokens=20)
        self.assertGreater(len(chunks), 2)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLess(b["span"][0], a["span"][1])  # overlapping spans
            self.assertGreater(b["span"][1], a["span"][1])


class UrlsAndCrawl(unittest.TestCase):
    def test_normalize_url(self):
        self.assertEqual(webpages.normalize_url("HTTP://Example.COM:80/a/b/?utm_source=x&b=2&a=1&fbclid=z#frag"),
                         "http://example.com/a/b?a=1&b=2")
        self.assertEqual(webpages.normalize_url("https://example.com"), "https://example.com/")
        self.assertEqual(webpages.normalize_url("https://example.com:8443/x/"), "https://example.com:8443/x")

    def test_host_allowlist_patterns(self):
        self.assertTrue(webpages.host_allowed("docs.example.com", ["*.example.com"]))
        self.assertTrue(webpages.host_allowed("example.com", ["*.example.com"]))
        self.assertFalse(webpages.host_allowed("example.com.evil.net", ["*.example.com"]))
        self.assertTrue(webpages.host_allowed("Example.com", ["example.com"]))

    def fake_site(self):
        pages = {
            "https://site.example/": ["/a", "/b", "https://other.example/x", "/a#frag", "/a?utm_campaign=q"],
            "https://site.example/a": ["/a/deep", "/b"],
            "https://site.example/b": ["/private/secret", "/c.pdf"],
            "https://site.example/a/deep": ["/never"],
            "https://site.example/c.pdf": None,  # unsupported type
            "https://site.example/private/secret": "robots",
        }
        calls = []

        def fetch_page(url):
            calls.append(url)
            spec = pages.get(webpages.normalize_url(url).rstrip("/") or url, pages.get(url, "missing"))
            if spec == "robots":
                return {"url": url, "outcome": {"ok": False, "reason": "robots_disallowed"}, "links": [], "fetch": {"bytes": 0}}
            if spec is None:
                return {"url": url, "outcome": {"ok": False, "reason": "unsupported_type"}, "links": [], "fetch": {"bytes": 10}}
            if spec == "missing":
                return {"url": url, "outcome": {"ok": False, "reason": "http_status", "detail": "404"}, "links": [], "fetch": {"bytes": 0}}
            links = [{"url": webpages.urljoin_clean(url, h)} for h in spec]
            return {"url": url, "outcome": {"ok": True, "reason": "ok"}, "links": links, "fetch": {"bytes": 100}}
        return fetch_page, calls

    def test_depth_limit_allowlist_dedupe_and_skip_reasons(self):
        fetch_page, calls = self.fake_site()
        res = webpages.crawl(["https://site.example/"], fetch_page, depth=1, max_pages=20)
        visited = sorted(webpages.normalize_url(p["url"]) for p in res["pages"])
        self.assertEqual(visited, ["https://site.example/", "https://site.example/a", "https://site.example/b"])
        reasons = {webpages.normalize_url(s["url"]): s["reason"] for s in res["skipped"]}
        self.assertEqual(reasons["https://other.example/x"], "outside_allowlist")
        self.assertEqual(reasons["https://site.example/a/deep"], "over_depth")
        self.assertEqual(reasons["https://site.example/private/secret"], "over_depth")
        self.assertEqual(len([c for c in calls if webpages.normalize_url(c) == "https://site.example/a"]), 1)
        self.assertEqual(res["summary"]["pages"], 3)
        self.assertEqual(res["summary"]["bytes"], 300)

    def test_deeper_crawl_reports_robots_and_unsupported_and_page_limit(self):
        fetch_page, _ = self.fake_site()
        res = webpages.crawl(["https://site.example/"], fetch_page, depth=3, max_pages=4)
        reasons = {webpages.normalize_url(s["url"]): s["reason"] for s in res["skipped"]}
        self.assertEqual(len(res["pages"]), 4)
        self.assertIn("over_page_limit", reasons.values())
        res2 = webpages.crawl(["https://site.example/"], fetch_page, depth=3, max_pages=20)
        r2 = {webpages.normalize_url(s["url"]): s["reason"] for s in res2["skipped"]}
        self.assertEqual(r2["https://site.example/private/secret"], "robots_disallowed")
        self.assertEqual(r2["https://site.example/c.pdf"], "unsupported_type")
        self.assertEqual(r2["https://site.example/never"], "fetch_error")

    def test_include_exclude_and_prefix(self):
        fetch_page, _ = self.fake_site()
        res = webpages.crawl(["https://site.example/"], fetch_page, depth=2, exclude=[r"^/b"])
        reasons = {webpages.normalize_url(s["url"]): s["reason"] for s in res["skipped"]}
        self.assertEqual(reasons["https://site.example/b"], "excluded_pattern")
        res = webpages.crawl(["https://site.example/"], fetch_page, depth=2, prefixes=["/a"])
        visited = sorted(webpages.normalize_url(p["url"]) for p in res["pages"])
        self.assertIn("https://site.example/", visited)  # start pages are always fetched
        self.assertIn("https://site.example/a", visited)
        self.assertNotIn("https://site.example/b", visited)


class FakeHttp(object):
    def __init__(self, responses):
        self.responses = responses  # url -> (status, body) or Exception
        self.calls = []

    def __call__(self, url, **kw):
        self.calls.append(url)
        spec = self.responses.get(url, (404, b""))
        if isinstance(spec, str):
            return {"ok": False, "url": url, "status": None, "reason": spec, "body": b""}
        status, body = spec
        ok = 200 <= status < 300
        return {"ok": ok, "url": url, "final_url": url, "status": status, "body": body, "headers": {"content-type": "text/html"},
                "content_type": "text/html", "charset": "utf-8", "bytes": len(body), "truncated": False,
                "fetched": "2026-11-04T00:00:00Z", "reason": "ok" if ok else "http_status"}


class Robots(unittest.TestCase):
    def policy(self, robots_spec):
        http = FakeHttp({"https://site.example/robots.txt": robots_spec})
        return webpages.RobotsPolicy(http), http

    def test_rules_from_fixture(self):
        pol, http = self.policy((200, fixture("robots.txt")))
        self.assertEqual(pol.check("https://site.example/blog/post")[0], True)
        self.assertEqual(pol.check("https://site.example/private/x")[0], False)
        self.assertEqual(pol.check("https://site.example/private/ok")[0], True)
        self.assertEqual(pol.crawl_delay("https://site.example/"), 2)
        self.assertEqual(len(http.calls), 1)  # fetched once per host

    def test_missing_robots_allows_and_forbidden_disallows(self):
        pol, _ = self.policy((404, b""))
        self.assertTrue(pol.check("https://site.example/anything")[0])
        pol, _ = self.policy((403, b""))
        self.assertFalse(pol.check("https://site.example/anything")[0])

    def test_server_error_disallows_but_network_error_defers_to_page_fetch(self):
        pol, _ = self.policy((503, b""))
        self.assertFalse(pol.check("https://site.example/a")[0])
        pol, _ = self.policy("network_unreachable")
        ok, detail = pol.check("https://site.example/a")
        self.assertTrue(ok)
        self.assertEqual(detail, "robots_unreachable")

    def test_fetcher_refuses_disallowed_page_with_structured_reason(self):
        http = FakeHttp({"https://site.example/robots.txt": (200, fixture("robots.txt")),
                         "https://site.example/private/x": (200, b"<p>secret</p>")})
        f = webpages.Fetcher(raw_fetch=http, delay=0)
        res = f.fetch("https://site.example/private/x")
        self.assertFalse(res["ok"])
        self.assertEqual(res["reason"], "robots_disallowed")
        self.assertNotIn("https://site.example/private/x", http.calls)


class CacheAndRate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_cache_hit_miss_and_max_age(self):
        now = [1000.0]
        cache = webpages.Cache(self.tmp, max_age=60, clock=lambda: now[0])
        url = "https://site.example/a"
        self.assertIsNone(cache.get(url))
        cache.put(url, {"ok": True, "url": url, "final_url": url, "status": 200, "body": b"<p>x</p>", "headers": {},
                        "content_type": "text/html", "charset": "utf-8", "bytes": 8, "truncated": False, "fetched": "t"})
        hit = cache.get(url)
        self.assertTrue(hit["from_cache"])
        self.assertEqual(hit["body"], b"<p>x</p>")
        self.assertTrue(os.path.exists(os.path.join(self.tmp, webpages.url_key(url) + ".raw")))
        now[0] += 61
        self.assertIsNone(cache.get(url))

    def test_fetcher_uses_cache_and_skips_network(self):
        http = FakeHttp({"https://site.example/robots.txt": (404, b""), "https://site.example/a": (200, b"<p>hello</p>")})
        f = webpages.Fetcher(cache_dir=self.tmp, raw_fetch=http, delay=0)
        first = f.fetch("https://site.example/a")
        second = f.fetch("https://site.example/a")
        self.assertFalse(first["from_cache"])
        self.assertTrue(second["from_cache"])
        self.assertEqual(http.calls.count("https://site.example/a"), 1)
        f2 = webpages.Fetcher(cache_dir=self.tmp, raw_fetch=http, delay=0, use_cache=False)
        self.assertFalse(f2.fetch("https://site.example/a")["from_cache"])

    def test_rate_limiter_spaces_requests_per_host(self):
        t = [0.0]
        slept = []

        def sleep(d):
            slept.append(round(d, 3))
            t[0] += d
        rl = webpages.HostRateLimiter(delay=1.0, clock=lambda: t[0], sleep=sleep)
        rl.wait("a.example")
        rl.wait("b.example")
        t[0] += 0.25
        rl.wait("a.example")
        rl.set_delay("b.example", 2.0)
        rl.wait("b.example")
        self.assertEqual(slept, [0.75, 1.0])


class LocalFilesAndOutput(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    def test_local_file_record_and_manifest_on_disk(self):
        path = os.path.join(FIX, "article.html")
        rec = webpages.fetch_and_process(path, work=self.work, fetcher=webpages.Fetcher(delay=0), user_supplied=True)
        self.assertTrue(rec["outcome"]["ok"])
        self.assertEqual(rec["source"]["kind"], "file")
        self.assertTrue(rec["user_supplied"])
        self.assertGreater(len(rec["chunks"]), 0)
        pages = os.path.join(self.work, "pages")
        self.assertTrue(os.path.exists(os.path.join(pages, rec["key"] + ".json")))
        self.assertTrue(os.path.exists(os.path.join(pages, rec["key"] + ".raw")))
        with open(os.path.join(pages, "manifest.json")) as f:
            man = json.load(f)
        entry = man["pages"][0]
        for k in ("url", "title", "word_count", "chunks", "ok", "robots", "record"):
            self.assertIn(k, entry)
        self.assertEqual(entry["title"], "Acrylic Light Guides & Edge Glow")

    def test_missing_local_file_is_structured_failure(self):
        rec = webpages.fetch_and_process(os.path.join(self.work, "nope.html"), fetcher=webpages.Fetcher(delay=0))
        self.assertFalse(rec["outcome"]["ok"])
        self.assertEqual(rec["outcome"]["reason"], "file_not_found")

    def test_cli_fetch_local_file_prints_record_without_work_dir(self):
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = webpages.main(["fetch", os.path.join(FIX, "article.html")])
        self.assertEqual(code, 0)
        rec = json.loads(buf.getvalue())
        self.assertEqual(rec["metadata"]["title"], "Acrylic Light Guides & Edge Glow")

    def test_user_agent_names_only_the_tool(self):
        self.assertTrue(webpages.USER_AGENT.startswith("metadump/"))
        self.assertNotIn("@", webpages.USER_AGENT)


@unittest.skipUnless(os.environ.get("METADUMP_LIVE") == "1", "set METADUMP_LIVE=1 for network tests")
class Live(unittest.TestCase):
    def test_real_fetch_of_example_com(self):
        rec = webpages.fetch_and_process("https://example.com/", fetcher=webpages.Fetcher(delay=0))
        self.assertTrue(rec["outcome"]["ok"], rec["outcome"])
        self.assertIn("Example Domain", rec["metadata"]["title"])


if __name__ == "__main__":
    unittest.main()

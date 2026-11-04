"""Tests for skills/metadump/scripts/finalize.py (run: python3 -m unittest discover -s tests)."""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
sys.path.insert(0, SCRIPTS)

import finalize  # noqa: E402

FINALIZE = os.path.join(SCRIPTS, "finalize.py")


def base_dump():
    return {
        "manifest": {
            "schema": "metadump/1",
            "slug": "demo",
            "version": 1,
            "created": "2026-11-04",
            "prompt": "Make a calm matte poster with amber light",
            "references": [],
            "consumers": ["image"],
            "depth": "lite",
        },
        "essence": {"one_sentence": "A calm matte poster lit by amber light.", "signature": ["c-amber"]},
        "routing": [{"job": "image prompt", "when": "before rendering", "paths": ["/palette", "/anti_keywords"]}],
        "exports": {},
        "anti_keywords": {
            "ak-gloss": {
                "term": "glossy",
                "kind": "not_wanted",
                "instead": "matte paper surface",
                "scope": ["image"],
                "tier": 1,
                "prov": "inferred",
                "anchor": "matte",
            }
        },
        "checks": {},
        "open_questions": {},
        "palette": {
            "c-amber": {
                "term": "amber light",
                "tier": 1,
                "prov": "user_stated",
                "anchor": "amber light",
                "text": "Warm amber key light.",
            }
        },
        "sources": {},
    }


class LayoutAndOrdering(unittest.TestCase):
    def test_build_orders_spine_then_task_sections_then_lookups(self):
        d = base_dump()
        # scramble input order
        scrambled = {k: d[k] for k in ["sources", "palette", "checks", "manifest", "routing", "anti_keywords", "essence", "exports", "open_questions"]}
        out, report = finalize.build_dump(scrambled)
        self.assertEqual(report["errors"], [])
        self.assertEqual(
            list(out.keys()),
            ["manifest", "essence", "routing", "exports", "anti_keywords", "checks", "open_questions", "palette", "index", "sources"],
        )

    def test_layout_puts_each_entry_on_its_own_line(self):
        out, _ = finalize.build_dump(base_dump())
        text, _ = finalize.serialize(out)
        amber_lines = [ln for ln in text.splitlines() if '"c-amber": {' in ln]
        self.assertEqual(len(amber_lines), 1)
        entry = json.loads("{" + amber_lines[0].strip().rstrip(",") + "}")
        self.assertEqual(entry["c-amber"]["term"], "amber light")

    def test_serialized_output_is_valid_json_equal_to_dump(self):
        out, _ = finalize.build_dump(base_dump())
        text, _ = finalize.serialize(out)
        self.assertEqual(json.loads(text), out)


def codes(items):
    return [i["code"] for i in items]


class Validation(unittest.TestCase):
    def test_base_dump_has_no_errors_or_fixes(self):
        _, report = finalize.build_dump(base_dump())
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["fixes"], [])

    def test_missing_verbatim_prompt_is_error(self):
        d = base_dump()
        del d["manifest"]["prompt"]
        _, report = finalize.build_dump(d)
        self.assertIn("manifest_field_missing", codes(report["errors"]))

    def test_invalid_tier_is_error(self):
        d = base_dump()
        d["palette"]["c-amber"]["tier"] = 7
        _, report = finalize.build_dump(d)
        self.assertIn("bad_tier", codes(report["errors"]))

    def test_invalid_prov_is_error(self):
        d = base_dump()
        d["palette"]["c-amber"]["prov"] = "vibes"
        _, report = finalize.build_dump(d)
        self.assertIn("bad_prov", codes(report["errors"]))

    def test_proposed_entry_at_tier_1_is_demoted_to_tier_2(self):
        d = base_dump()
        d["palette"]["c-amber"]["prov"] = "proposed"
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-amber"]["tier"], 2)
        self.assertIn("proposed_not_tier1", codes(report["fixes"]))

    def test_tier_1_entry_without_anchor_is_demoted_to_tier_2(self):
        d = base_dump()
        d["palette"]["c-amber"]["prov"] = "inferred"
        del d["palette"]["c-amber"]["anchor"]
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-amber"]["tier"], 2)
        self.assertIn("tier1_needs_anchor", codes(report["fixes"]))

    def test_user_stated_anchor_not_in_prompt_is_demoted_to_inferred(self):
        d = base_dump()
        d["palette"]["c-amber"]["anchor"] = "neon magenta"
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-amber"]["prov"], "inferred")
        self.assertIn("user_stated_needs_prompt_anchor", codes(report["fixes"]))

    def test_user_stated_anchor_matches_prompt_ignoring_case_and_spacing(self):
        d = base_dump()
        d["palette"]["c-amber"]["anchor"] = "Amber   LIGHT"
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-amber"]["prov"], "user_stated")

    def test_user_stated_from_write_back_is_kept_without_prompt_anchor(self):
        d = base_dump()
        d["palette"]["c-amber"]["anchor"] = "neon magenta"
        d["palette"]["c-amber"]["decided_in"] = "use-mode 2026-11-05: user said keep amber"
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-amber"]["prov"], "user_stated")

    def test_researched_entry_without_web_source_is_demoted_to_inferred(self):
        d = base_dump()
        d["palette"]["c-teal"] = {"term": "teal", "tier": 2, "prov": "researched", "text": "x"}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-teal"]["prov"], "inferred")
        self.assertIn("prov_needs_source", codes(report["fixes"]))

    def test_researched_entry_with_web_source_is_kept(self):
        d = base_dump()
        d["sources"]["s-bfl"] = {"kind": "web", "url": "https://docs.bfl.ai/x", "title": "BFL", "fetched": "2026-11-04"}
        d["palette"]["c-teal"] = {"term": "teal", "tier": 2, "prov": "researched", "src": ["s-bfl"], "text": "x"}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-teal"]["prov"], "researched")
        self.assertEqual(report["errors"], [])

    def test_reference_observed_needs_reference_source(self):
        d = base_dump()
        d["sources"]["r1"] = {"kind": "reference", "path": "refs/a.jpg", "title": "photo"}
        d["palette"]["c-teal"] = {"term": "teal", "tier": 2, "prov": "reference_observed", "src": ["r1"], "text": "x"}
        d["palette"]["c-rust"] = {"term": "rust", "tier": 2, "prov": "reference_observed", "text": "x"}
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-teal"]["prov"], "reference_observed")
        self.assertEqual(out["palette"]["c-rust"]["prov"], "inferred")

    def test_src_pointing_at_missing_source_is_error(self):
        d = base_dump()
        d["palette"]["c-amber"]["src"] = ["s-nope"]
        _, report = finalize.build_dump(d)
        self.assertIn("missing_source", codes(report["errors"]))

    def test_not_wanted_without_instead_is_error(self):
        d = base_dump()
        del d["anti_keywords"]["ak-gloss"]["instead"]
        _, report = finalize.build_dump(d)
        self.assertIn("not_wanted_needs_instead", codes(report["errors"]))

    def test_not_wanted_noise_or_search_only_needs_no_instead(self):
        d = base_dump()
        d["anti_keywords"]["ak-noise"] = {"term": "stunning", "kind": "not_wanted", "class": "noise", "scope": ["*"], "tier": 3, "prov": "inferred"}
        d["anti_keywords"]["ak-seo"] = {"term": "countertop", "kind": "not_wanted", "scope": ["search"], "tier": 3, "prov": "inferred"}
        _, report = finalize.build_dump(d)
        self.assertEqual(report["errors"], [])

    def test_bad_anti_keyword_kind_is_error(self):
        d = base_dump()
        d["anti_keywords"]["ak-gloss"]["kind"] = "banned"
        _, report = finalize.build_dump(d)
        self.assertIn("bad_anti_keyword_kind", codes(report["errors"]))

    def test_duplicate_entry_ids_across_sections_is_error(self):
        d = base_dump()
        d["lighting"] = {"c-amber": {"term": "amber", "tier": 3, "prov": "inferred", "text": "dup"}}
        d["routing"][0]["paths"].append("/lighting")
        _, report = finalize.build_dump(d)
        self.assertIn("duplicate_id", codes(report["errors"]))

    def test_check_citing_unknown_id_is_error(self):
        d = base_dump()
        d["checks"]["k-matte"] = {"from": ["ak-gloss", "c-ghost"], "severity": "must", "test": {"kind": "judge", "spec": "surface reads matte"}}
        _, report = finalize.build_dump(d)
        self.assertIn("unknown_id", codes(report["errors"]))

    def test_unresolved_routing_path_is_error(self):
        d = base_dump()
        d["routing"][0]["paths"].append("/typography")
        _, report = finalize.build_dump(d)
        self.assertIn("unresolved_route_path", codes(report["errors"]))

    def test_essence_signature_must_name_tier_1_entries(self):
        d = base_dump()
        d["essence"]["signature"] = ["c-ghost"]
        _, report = finalize.build_dump(d)
        self.assertIn("unknown_id", codes(report["errors"]))

    def test_stale_export_warns(self):
        d = base_dump()
        d["manifest"]["version"] = 3
        d["exports"]["image"] = {"generic": {"compiled_from_version": 2, "positive": "calm amber poster"}}
        d["routing"].append({"job": "paste image prompt", "paths": ["/exports/image/generic"]})
        _, report = finalize.build_dump(d)
        self.assertIn("stale_export", codes(report["warnings"]))

    def test_more_than_twelve_tier_1_entries_warns(self):
        d = base_dump()
        for i in range(13):
            d["palette"]["c-%d" % i] = {"term": "t%d" % i, "tier": 1, "prov": "inferred", "anchor": "calm", "text": "x"}
        _, report = finalize.build_dump(d)
        self.assertIn("tier1_over_cap", codes(report["warnings"]))

    def test_section_no_route_reaches_warns(self):
        d = base_dump()
        d["lighting"] = {"c-key": {"term": "key light", "tier": 3, "prov": "inferred", "text": "x"}}
        _, report = finalize.build_dump(d)
        self.assertIn("unrouted_section", codes(report["warnings"]))

    def test_open_questions_default_to_unknown_prov(self):
        d = base_dump()
        d["open_questions"]["q-size"] = {"text": "Poster size?", "default": "A2 portrait"}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["open_questions"]["q-size"]["prov"], "unknown")
        self.assertEqual(report["errors"], [])


class IndexAndRouting(unittest.TestCase):
    def test_index_maps_terms_aliases_and_variants_in_lowercase(self):
        d = base_dump()
        d["palette"]["c-amber"]["aliases"] = ["Honey Glow"]
        d["anti_keywords"]["ak-gloss"]["variants"] = ["shiny"]
        out, _ = finalize.build_dump(d)
        idx = out["index"]
        self.assertEqual(idx["amber light"]["hits"], ["/palette/c-amber"])
        self.assertEqual(idx["honey glow"]["hits"][0], "/palette/c-amber")
        self.assertEqual(idx["shiny"]["hits"][0], "/anti_keywords/ak-gloss")

    def test_index_links_ambiguous_term_to_its_not_meant_anti_keyword(self):
        d = base_dump()
        d["palette"]["c-glass"] = {"term": "glass", "tier": 2, "prov": "inferred", "text": "physical glass"}
        d["anti_keywords"]["ak-glassmorph"] = {
            "term": "glass", "kind": "not_meant", "excluded_sense": "glassmorphism UI",
            "instead": "physical glass object", "variants": ["glassmorphism"], "tier": 2, "prov": "inferred",
        }
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["index"]["glass"]["not_meant"], ["ak-glassmorph"])
        self.assertEqual(out["index"]["glass"]["hits"], ["/palette/c-glass"])
        self.assertEqual(out["index"]["glassmorphism"]["hits"][0], "/anti_keywords/ak-glassmorph")

    def test_routes_get_jq_tokens_and_line_spans(self):
        text, out, report = finalize.finish(base_dump())
        self.assertEqual(report["errors"], [])
        route = [r for r in out["routing"] if r["job"] == "image prompt"][0]
        self.assertEqual(route["jq"], '.["palette"], .["anti_keywords"]')
        self.assertGreater(route["tokens"], 0)
        lines = text.splitlines()
        (s1, e1), (s2, e2) = route["lines"]
        self.assertTrue(lines[s1 - 1].strip().startswith('"palette": {'))
        self.assertTrue(lines[s2 - 1].strip().startswith('"anti_keywords": {'))
        self.assertEqual(lines[e1 - 1].strip().rstrip(","), "}")

    def test_head_lines_cover_manifest_essence_and_routing(self):
        text, out, _ = finalize.finish(base_dump())
        n = out["manifest"]["head_lines"]
        head = "\n".join(text.splitlines()[:n])
        self.assertIn('"routing": [', head)
        self.assertEqual(text.splitlines()[n - 1].strip().rstrip(","), "]")
        self.assertNotIn('"exports"', head)

    def test_manifest_gets_how_to_read_commands_naming_the_file(self):
        _, out, _ = finalize.finish(base_dump())
        joined = " ".join(out["manifest"]["how_to_read"])
        self.assertIn("demo.metadump.json", joined)
        self.assertIn(".index[", joined)

    def test_manifest_stats_count_entries_by_tier_and_prov(self):
        _, out, _ = finalize.finish(base_dump())
        stats = out["manifest"]["stats"]
        self.assertEqual(stats["entries"], 2)
        self.assertEqual(stats["by_prov"], {"inferred": 1, "user_stated": 1})
        self.assertEqual(stats["by_tier"], {"1": 2})
        self.assertGreater(stats["tokens"], 0)

    def test_route_over_slice_cap_warns(self):
        d = base_dump()
        for i in range(400):
            d["palette"]["c-x%d" % i] = {"term": "filler %d" % i, "tier": 3, "prov": "inferred", "text": "word " * 20}
        _, _, report = finalize.finish(d)
        self.assertIn("route_over_cap", codes(report["warnings"]))


def manifest():
    return copy.deepcopy(base_dump()["manifest"])


def write_work(root, shards, with_manifest=True):
    os.makedirs(os.path.join(root, "shards"), exist_ok=True)
    if with_manifest:
        with open(os.path.join(root, "manifest.json"), "w") as f:
            json.dump(manifest(), f)
    for name, content in shards.items():
        with open(os.path.join(root, "shards", name), "w") as f:
            json.dump(content, f)


def entry(term, tier=2, prov="inferred", **kw):
    e = {"term": term, "tier": tier, "prov": prov, "text": term}
    e.update(kw)
    return e


class MergeShards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def merge(self, shards, **kw):
        write_work(self.tmp, shards, **kw)
        return finalize.merge_workdir(self.tmp)

    def test_merge_combines_shards_with_manifest(self):
        draft, report = self.merge({
            "10-palette.json": {"ticket": {"id": "t10", "type": "specialist"}, "sections": {"palette": {"c-teal": entry("teal")}}},
            "11-light.json": {"ticket": {"id": "t11", "type": "specialist"}, "sections": {"lighting": {"l-key": entry("key light")}}},
        })
        self.assertEqual(report["errors"], [])
        self.assertEqual(draft["manifest"]["slug"], "demo")
        self.assertEqual(draft["palette"]["c-teal"]["term"], "teal")
        self.assertEqual(draft["lighting"]["l-key"]["term"], "key light")

    def test_missing_manifest_is_error(self):
        _, report = self.merge({}, with_manifest=False)
        self.assertIn("missing_manifest", codes(report["errors"]))

    def test_specialist_cannot_mint_researched_and_is_demoted(self):
        draft, report = self.merge({
            "10-palette.json": {"ticket": {"id": "t10", "type": "specialist"}, "sections": {"palette": {"c-teal": entry("teal", prov="researched")}}},
        })
        self.assertEqual(draft["palette"]["c-teal"]["prov"], "inferred")
        self.assertIn("prov_over_ceiling", codes(report["fixes"]))

    def test_prompt_ticket_may_mint_user_stated(self):
        draft, _ = self.merge({
            "01-prompt.json": {"ticket": {"id": "t01", "type": "prompt"}, "sections": {"palette": {"c-amber": entry("amber light", 1, "user_stated", anchor="amber light")}}},
        })
        self.assertEqual(draft["palette"]["c-amber"]["prov"], "user_stated")

    def test_conflict_keeps_stronger_prov_and_unions_aliases_and_src(self):
        draft, report = self.merge({
            "20-research.json": {"ticket": {"id": "t20", "type": "research"},
                                 "sources": {"s1": {"kind": "web", "url": "https://x.test", "title": "x"}},
                                 "sections": {"palette": {"c-teal": entry("teal", prov="researched", src=["s1"], aliases=["sea green"])}}},
            "30-spec.json": {"ticket": {"id": "t30", "type": "specialist"},
                             "sections": {"palette": {"c-teal": entry("teal", prov="inferred", aliases=["aqua"])}}},
        })
        e = draft["palette"]["c-teal"]
        self.assertEqual(e["prov"], "researched")
        self.assertEqual(e["aliases"], ["sea green", "aqua"])
        self.assertEqual(e["src"], ["s1"])
        self.assertIn("merge_conflict", codes(report["warnings"]))

    def test_normalize_replace_applies_but_cannot_upgrade_prov(self):
        draft, _ = self.merge({
            "30-spec.json": {"ticket": {"id": "t30", "type": "specialist"}, "sections": {"palette": {"c-teal": entry("teal", tier=1)}}},
            "90-norm.json": {"ticket": {"id": "t90", "type": "normalize"},
                             "sections": {"palette": {"c-teal": dict(entry("teal", tier=3, prov="user_stated"), _replace=True)}}},
        })
        e = draft["palette"]["c-teal"]
        self.assertEqual(e["tier"], 3)
        self.assertEqual(e["prov"], "inferred")
        self.assertNotIn("_replace", e)

    def test_normalize_delete_removes_entry(self):
        draft, _ = self.merge({
            "30-spec.json": {"ticket": {"id": "t30", "type": "specialist"}, "sections": {"palette": {"c-teal": entry("teal"), "c-aqua": entry("aqua")}}},
            "90-norm.json": {"ticket": {"id": "t90", "type": "normalize"}, "sections": {"palette": {"c-aqua": {"_delete": True}}}},
        })
        self.assertNotIn("c-aqua", draft["palette"])
        self.assertIn("c-teal", draft["palette"])

    def test_synthesis_shard_supplies_spine(self):
        draft, _ = self.merge({
            "30-spec.json": {"ticket": {"id": "t30", "type": "specialist"}, "sections": {"palette": {"c-teal": entry("teal")}}},
            "95-synth.json": {"ticket": {"id": "t95", "type": "synthesis"},
                              "spine": {"essence": {"one_sentence": "Teal."}, "routing": [{"job": "colors", "paths": ["/palette"]}]}},
        })
        self.assertEqual(draft["essence"]["one_sentence"], "Teal.")
        self.assertEqual(draft["routing"][0]["job"], "colors")

    def test_inherit_ticket_keeps_prov_and_flags_inherited(self):
        draft, _ = self.merge({
            "05-inherit.json": {"ticket": {"id": "t05", "type": "inherit"},
                                "sources": {"d-old": {"kind": "dump", "path": "old.metadump.json", "title": "old"}},
                                "sections": {"palette": {"c-blue": entry("cobalt", prov="reference_observed", src=["d-old"])}}},
        })
        e = draft["palette"]["c-blue"]
        self.assertEqual(e["prov"], "reference_observed")
        self.assertTrue(e["inherited"])

    def test_groups_inside_sections_merge_by_entry(self):
        draft, _ = self.merge({
            "30-a.json": {"ticket": {"id": "t30", "type": "specialist"}, "sections": {"palette": {"roles": {"c-a": entry("a")}}}},
            "31-b.json": {"ticket": {"id": "t31", "type": "specialist"}, "sections": {"palette": {"roles": {"c-b": entry("b")}}}},
        })
        self.assertEqual(sorted(draft["palette"]["roles"]), ["c-a", "c-b"])


def run_cli(*args):
    return subprocess.run([sys.executable, FINALIZE] + list(args), capture_output=True, text=True)


def good_shards():
    return {
        "01-prompt.json": {"ticket": {"id": "t01", "type": "prompt"},
                           "sections": {"palette": {"c-amber": entry("amber light", 1, "user_stated", anchor="amber light")}}},
        "40-excl.json": {"ticket": {"id": "t40", "type": "exclusion"},
                         "anti_keywords": {"ak-gloss": {"term": "glossy", "kind": "not_wanted", "instead": "matte paper", "tier": 2, "prov": "inferred"}}},
        "95-synth.json": {"ticket": {"id": "t95", "type": "synthesis"},
                          "spine": {"essence": {"one_sentence": "Calm amber poster.", "signature": ["c-amber"]},
                                    "routing": [{"job": "image prompt", "paths": ["/palette", "/anti_keywords"]}]}},
    }


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.work = os.path.join(self.root, "metadumps", ".work", "demo")

    def test_build_workdir_writes_dump_beside_work_and_exits_0(self):
        write_work(self.work, good_shards())
        res = run_cli("build", self.work)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        out_path = os.path.join(self.root, "metadumps", "demo.metadump.json")
        with open(out_path) as f:
            dump = json.load(f)
        self.assertEqual(dump["palette"]["c-amber"]["prov"], "user_stated")
        self.assertTrue(os.path.exists(os.path.join(self.work, "report.json")))

    def test_build_with_errors_exits_1_and_writes_no_dump(self):
        shards = good_shards()
        shards["95-synth.json"]["spine"]["routing"][0]["paths"].append("/missing")
        write_work(self.work, shards)
        res = run_cli("build", self.work)
        self.assertEqual(res.returncode, 1)
        self.assertIn("unresolved_route_path", res.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.root, "metadumps", "demo.metadump.json")))

    def test_build_existing_dump_in_place_with_bump(self):
        path = os.path.join(self.root, "demo.metadump.json")
        with open(path, "w") as f:
            json.dump(base_dump(), f)
        res = run_cli("build", path, "--bump")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        with open(path) as f:
            self.assertEqual(json.load(f)["manifest"]["version"], 2)

    def test_check_exit_code_follows_errors(self):
        path = os.path.join(self.root, "demo.metadump.json")
        with open(path, "w") as f:
            json.dump(base_dump(), f)
        self.assertEqual(run_cli("check", path).returncode, 0)
        broken = base_dump()
        del broken["manifest"]["prompt"]
        with open(path, "w") as f:
            json.dump(broken, f)
        self.assertEqual(run_cli("check", path).returncode, 1)

    def test_check_flags_hand_edited_layout_as_stale(self):
        path = os.path.join(self.root, "demo.metadump.json")
        with open(path, "w") as f:
            json.dump(base_dump(), f, indent=2)
        res = run_cli("check", path)
        self.assertIn("layout_stale", res.stdout)

    def test_merge_command_writes_laid_out_draft_even_before_spine_exists(self):
        shards = good_shards()
        del shards["95-synth.json"]
        write_work(self.work, shards)
        res = run_cli("merge", self.work)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        with open(os.path.join(self.work, "draft.json")) as f:
            text = f.read()
        draft = json.loads(text)
        self.assertEqual(draft["palette"]["c-amber"]["term"], "amber light")
        self.assertEqual(len([ln for ln in text.splitlines() if '"c-amber": {' in ln]), 1)
        self.assertIn("amber light", draft["index"])


class SearchIndexWords(unittest.TestCase):
    def test_single_words_of_terms_are_indexed_without_stopwords(self):
        d = base_dump()
        d["palette"]["c-mat"] = entry("transparent blue acrylic and vinyl")
        out, _ = finalize.build_dump(d)
        self.assertIn("/palette/c-mat", out["index"]["acrylic"]["words"])
        self.assertIn("/palette/c-mat", out["index"]["vinyl"]["words"])
        self.assertNotIn("and", out["index"])

    def test_word_matches_are_kept_apart_from_exact_phrase_hits(self):
        d = base_dump()
        d["palette"]["c-acr"] = entry("acrylic")
        d["palette"]["c-mat"] = entry("cast acrylic block")
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["index"]["acrylic"]["hits"], ["/palette/c-acr"])
        self.assertEqual(out["index"]["acrylic"]["words"], ["/palette/c-mat"])

    def test_hits_are_ranked_by_tier(self):
        d = base_dump()
        d["palette"]["c-low"] = entry("light leak", tier=3)
        d["palette"]["c-high"] = entry("light leak", tier=2, aliases=["leak"])
        out, _ = finalize.build_dump(d)
        self.assertEqual(out["index"]["light leak"]["hits"], ["/palette/c-high", "/palette/c-low"])

    def test_plural_words_also_index_their_singular(self):
        d = base_dump()
        d["palette"]["c-c"] = entry("bright caustics")
        out, _ = finalize.build_dump(d)
        self.assertIn("caustic", out["index"])
        self.assertIn("caustics", out["index"])

    def test_words_in_too_many_entries_are_not_word_indexed(self):
        d = base_dump()
        for i in range(30):
            d["palette"]["c-b%d" % i] = entry("blue thing %d" % i)
        out, _ = finalize.build_dump(d)
        self.assertNotIn("blue", out["index"])

    def test_not_meant_terms_are_not_split_into_words(self):
        d = base_dump()
        d["anti_keywords"]["ak-paint"] = {"term": "acrylic paint", "kind": "not_meant", "excluded_sense": "artist paint",
                                          "instead": "clear acrylic plastic", "tier": 2, "prov": "inferred"}
        out, _ = finalize.build_dump(d)
        self.assertNotIn("paint", out["index"])


class AutoTier1Route(unittest.TestCase):
    def test_build_adds_a_first_route_to_every_tier_1_entry(self):
        out, report = finalize.build_dump(base_dump())
        self.assertEqual(report["errors"], [])
        auto = out["routing"][0]
        self.assertTrue(auto["auto"])
        self.assertEqual(sorted(auto["paths"]), ["/anti_keywords/ak-gloss", "/palette/c-amber"])

    def test_rebuilding_replaces_the_auto_route_instead_of_duplicating_it(self):
        out, _ = finalize.build_dump(base_dump())
        out2, _ = finalize.build_dump(out)
        self.assertEqual(len([r for r in out2["routing"] if r.get("auto")]), 1)
        self.assertEqual(len(out2["routing"]), len(out["routing"]))


class MediaTicketsAndSources(unittest.TestCase):
    """0.2.0: scrape/watch/moodboard tickets, video/image sources, the method field, consult-not-obey wording."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def merge(self, shards):
        write_work(self.tmp, shards)
        return finalize.merge_workdir(self.tmp)

    def test_evidence_tickets_may_mint_researched_and_reference_observed_only(self):
        for ttype in ("scrape", "watch", "moodboard"):
            draft, report = self.merge({
                "15-%s.json" % ttype: {"ticket": {"id": "t", "type": ttype},
                                       "sections": {"motion": {"m-a-%s" % ttype: entry("a", prov="researched"),
                                                               "m-b-%s" % ttype: entry("b", prov="reference_observed"),
                                                               "m-c-%s" % ttype: entry("c", prov="user_stated")}}}})
            sec = draft["motion"]
            self.assertEqual(sec["m-a-%s" % ttype]["prov"], "researched", ttype)
            self.assertEqual(sec["m-b-%s" % ttype]["prov"], "reference_observed", ttype)
            self.assertEqual(sec["m-c-%s" % ttype]["prov"], "reference_observed", ttype)
            self.assertIn("prov_over_ceiling", codes(report["fixes"]))
            self.assertNotIn("unknown_ticket_type", codes(report["warnings"]))

    def test_video_and_image_sources_back_both_evidence_provenances(self):
        d = base_dump()
        d["sources"]["v1"] = {"kind": "video", "url": "https://www.youtube.com/watch?v=abcDEF12345", "title": "talk",
                              "fetched": "2026-11-04", "origin": "web"}
        d["sources"]["i1"] = {"kind": "image", "path": "refs/shelf.jpg", "title": "shelf", "origin": "user"}
        d["palette"]["c-web"] = {"term": "ease out", "tier": 2, "prov": "researched", "src": ["v1"], "text": "x", "method": "frame-diff"}
        d["palette"]["c-ref"] = {"term": "shelf blue", "tier": 2, "prov": "reference_observed", "src": ["i1"], "text": "x", "method": "pixel-sample"}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-web"]["prov"], "researched")
        self.assertEqual(out["palette"]["c-ref"]["prov"], "reference_observed")
        self.assertEqual(report["errors"], [])
        self.assertNotIn("unknown_method", codes(report["warnings"]))

    def test_web_found_media_cannot_be_reference_observed(self):
        d = base_dump()
        d["sources"]["v1"] = {"kind": "video", "url": "https://video.example/x", "title": "found", "origin": "web"}
        d["palette"]["c-x"] = {"term": "x", "tier": 2, "prov": "reference_observed", "src": ["v1"], "text": "x"}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-x"]["prov"], "researched")
        self.assertIn("prov_origin_mismatch", codes(report["fixes"]))

    def test_unknown_method_warns_but_does_not_block(self):
        d = base_dump()
        d["palette"]["c-amber"]["method"] = "vibes"
        out, report = finalize.build_dump(d)
        self.assertEqual(report["errors"], [])
        self.assertIn("unknown_method", codes(report["warnings"]))
        self.assertEqual(out["palette"]["c-amber"]["method"], "vibes")

    def test_free_text_method_from_older_dumps_is_left_alone(self):
        d = base_dump()
        d["palette"]["c-amber"]["method"] = "multiply the layer colors channel by channel"
        _, report = finalize.build_dump(d)
        self.assertNotIn("unknown_method", codes(report["warnings"]))

    def test_known_methods_are_accepted(self):
        for m in ("scraped", "transcribed", "frame-diff", "pixel-sample", "visual", "measured", "researched-doc"):
            d = base_dump()
            d["palette"]["c-amber"]["method"] = m
            _, report = finalize.build_dump(d)
            self.assertNotIn("unknown_method", codes(report["warnings"]), m)

    def test_head_reads_as_relevance_not_obligation(self):
        _, out, _ = finalize.finish(base_dump())
        head = json.dumps(out["routing"][0]) + json.dumps(out["manifest"]["how_to_read"])
        self.assertNotIn("must be expressed", head)
        self.assertNotIn("constrains", head)
        self.assertIn("relevan", out["routing"][0]["when"])


if __name__ == "__main__":
    unittest.main()

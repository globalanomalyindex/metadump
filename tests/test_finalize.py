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
                "tier": 2,  # inferred from "matte": the build's reading, so tier 2 at most
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

    def test_tier_1_holds_only_collected_entries(self):
        d = base_dump()
        d["palette"]["c-scope"] = {"term": "one product only", "tier": 1, "prov": "inferred", "anchor": "calm",
                                   "text": "Calm means a single product and nothing else."}
        d["palette"]["c-unknown"] = {"term": "paper stock", "tier": 1, "prov": "unknown", "anchor": "matte", "text": "Paper stock is undecided."}
        out, report = finalize.build_dump(d)
        self.assertEqual(out["palette"]["c-scope"]["tier"], 2)
        self.assertEqual(out["palette"]["c-unknown"]["tier"], 2)
        self.assertEqual(out["palette"]["c-amber"]["tier"], 1)  # user_stated stays
        self.assertEqual(codes(report["fixes"]).count("tier1_needs_collected"), 2)

    def test_the_builds_own_entries_that_narrow_the_task_warn(self):
        d = base_dump()
        d["palette"]["c-narrow"] = {"term": "parts", "tier": 2, "prov": "inferred", "text": "Four parts; nothing else is needed."}
        d["palette"]["c-gate"] = {"term": "button", "tier": 3, "prov": "proposed", "text": "The button must be blue."}
        d["palette"]["c-user"] = {"term": "calm", "tier": 2, "prov": "user_stated", "anchor": "calm", "text": "It must feel calm."}
        d["palette"]["c-open"] = {"term": "grain", "tier": 3, "prov": "inferred", "text": "A fine paper grain could suit it."}
        _, report = finalize.build_dump(d)
        flagged = sorted(w["path"] for w in report["warnings"] if w["code"] == "narrowing_language")
        self.assertEqual(flagged, ["/palette/c-gate", "/palette/c-narrow"])

    def test_signature_keeps_only_entries_that_stayed_tier_1(self):
        d = base_dump()
        d["palette"]["c-scope"] = {"term": "one product", "tier": 1, "prov": "inferred", "anchor": "calm", "text": "One product."}
        d["essence"]["signature"] = ["c-amber", "c-scope"]
        out, report = finalize.build_dump(d)
        self.assertEqual(out["essence"]["signature"], ["c-amber"])
        self.assertIn("signature_not_tier1", codes(report["fixes"]))

    def test_constraints_and_negations_are_not_narrowing(self):
        d = base_dump()
        d["palette"]["inv-logo"] = {"term": "logo corner", "tier": 2, "prov": "inferred", "variable": ["size"],
                                    "text": "The logo always sits top-left."}
        d["palette"]["fs-band"] = {"term": "band width", "tier": 3, "prov": "inferred", "kind": "forbidden_shortcut",
                                   "text": "Band width never means quantity."}
        d["palette"]["ak-neon"] = {"term": "neon", "tier": 2, "prov": "inferred", "kind": "not_wanted", "instead": "amber",
                                   "text": "Never neon."}
        d["palette"]["c-list"] = {"term": "layout", "tier": 2, "prov": "inferred", "text": "A grid is not the only option; a list also works."}
        _, report = finalize.build_dump(d)
        self.assertNotIn("narrowing_language", codes(report["warnings"]))

    def test_rule_words_in_the_head_exports_and_review_prompts_warn(self):
        # Test 11: the poem dump's brief said "Core: ... Choose one rare formation", and all four builds wrote about the
        # same cloud. The head and the exports are what every consumer reads first, so they hand over material, not orders.
        d = base_dump()
        d["essence"]["one_sentence"] = "Every poster must keep to one light."
        d["exports"]["llm_brief"] = {"compiled_from_version": 1, "from": ["c-amber"], "text": "Core: Choose one lamp and its light."}
        d["checks"]["k-gloss"] = {"text": "The poster never shows gloss.", "from": ["c-amber"], "severity": "should",
                                  "test": {"kind": "visual", "spec": "no gloss"}}
        _, report = finalize.build_dump(d)
        flagged = sorted(w["path"] for w in report["warnings"] if w["code"] == "directive_voice")
        self.assertEqual(flagged, ["/checks/k-gloss/text", "/essence/one_sentence", "/exports/llm_brief/text"])

    def test_material_written_as_observations_and_questions_does_not_warn(self):
        d = base_dump()
        d["essence"]["one_sentence"] = "Amber light makes matte paper feel warm and slow."
        d["exports"]["llm_brief"] = {"compiled_from_version": 1, "from": ["c-amber"],
                                     "text": "On the table: amber key light, matte stock. Ways in: a dusk window; a lamp-lit desk."}
        d["checks"]["k-gloss"] = {"text": "Does any surface read as glossy?", "from": ["c-amber"], "severity": "should",
                                  "test": {"kind": "visual", "spec": "gloss"}}
        _, report = finalize.build_dump(d)
        self.assertNotIn("directive_voice", codes(report["warnings"]))

    def test_a_head_with_a_single_way_in_warns(self):
        # One thesis and one formula read as the recipe; every consumer takes the same road in (ADR 0012).
        _, report = finalize.build_dump(base_dump())
        self.assertIn("no_angles", codes(report["warnings"]))

    def test_a_head_with_several_angles_does_not_warn(self):
        d = base_dump()
        d["essence"]["angles"] = [{"angle": "dusk window", "text": "Amber spills across a sill at the end of the day.", "draws_on": ["c-amber"]},
                                  {"angle": "lamp-lit desk", "text": "A small warm pool of light on paper at night.", "draws_on": ["c-amber"]}]
        _, report = finalize.build_dump(d)
        self.assertNotIn("no_angles", codes(report["warnings"]))

    def test_one_curve_or_one_colour_offered_by_the_build_warns(self):
        # Test 12: each curve facet held one value in tokens.curve, one facet per role; all four builds pasted the set (ADR 0013).
        d = base_dump()
        d["palette"]["mo-bloom"] = {"term": "bloom curve", "tier": 2, "prov": "inferred", "text": "A soft ease-out for the glow.",
                                    "tokens": {"status": "illustrative", "curve": "cubic-bezier(0.165, 0.84, 0.44, 1)", "ms": "250 to 500"}}
        d["palette"]["c-accent"] = {"term": "accent", "tier": 3, "prov": "proposed", "text": "A cool accent.",
                                    "tokens": {"status": "illustrative", "accent": "#7aa2f7"}}
        _, report = finalize.build_dump(d)
        flagged = sorted(w["path"] for w in report["warnings"] if w["code"] == "single_setting")
        self.assertEqual(flagged, ["/palette/c-accent", "/palette/mo-bloom"])

    def test_spreads_ranges_and_collected_values_do_not_warn(self):
        d = base_dump()
        d["palette"]["mo-bloom"] = {"term": "bloom curves", "tier": 2, "prov": "inferred", "text": "Soft ease-outs for the glow.",
                                    "tokens": {"status": "illustrative", "curves": ["cubic-bezier(0.165, 0.84, 0.44, 1)",
                                               "cubic-bezier(0.33, 1, 0.68, 1)", "cubic-bezier(0.5, 0, 0.1, 1)"], "ms": "250 to 500"}}
        d["palette"]["mo-standard"] = {"term": "standard curve", "tier": 2, "prov": "inferred", "text": "The platform's standard ease.",
                                       "tokens": {"status": "sourced", "curve": "cubic-bezier(0.2, 0, 0, 1)"}}
        d["sources"]["s-brand"] = {"kind": "web", "url": "https://brand.example/colours", "title": "Brand colours"}
        d["palette"]["c-brand"] = {"term": "brand blue", "tier": 2, "prov": "researched", "src": ["s-brand"], "text": "The brand's blue.",
                                   "tokens": {"status": "illustrative", "blue": "#1a5cff"}}
        _, report = finalize.build_dump(d)
        self.assertNotIn("single_setting", codes(report["warnings"]))

    def test_a_group_left_with_only_its_note_is_still_a_group(self):
        d = base_dump()
        d["palette"]["options"] = {"_about": "options, not requirements"}
        out, report = finalize.build_dump(d)
        self.assertEqual(report["errors"], [])
        self.assertEqual(out["palette"]["options"], {"_about": "options, not requirements"})

    def test_a_dump_that_never_identified_its_task_warns(self):
        _, report = finalize.build_dump(base_dump())
        self.assertIn("no_task_ladder", codes(report["warnings"]))

    def test_a_task_with_disciplines_and_a_ladder_does_not_warn(self):
        d = base_dump()
        d["essence"]["task"] = {"is": "a poster (print graphic design)",
                                "disciplines": ["graphic design", "typography", "print production"],
                                "ladder": ["graphic design", "poster design", "calm matte amber poster", "palette and paper values"],
                                "job": ["notice it across a room", "read the title", "take in the mood"]}
        _, report = finalize.build_dump(d)
        self.assertNotIn("no_task_ladder", codes(report["warnings"]))
        self.assertNotIn("no_task_job", codes(report["warnings"]))

    def test_a_task_without_the_users_whole_job_warns(self):
        d = base_dump()
        d["essence"]["task"] = {"is": "a poster", "disciplines": ["graphic design"], "ladder": ["graphic design", "this poster"]}
        _, report = finalize.build_dump(d)
        self.assertIn("no_task_job", codes(report["warnings"]))
        self.assertNotIn("no_task_ladder", codes(report["warnings"]))

    def test_a_ladder_needs_disciplines_and_more_than_one_rung(self):
        d = base_dump()
        d["essence"]["task"] = {"is": "a poster", "disciplines": [], "ladder": ["poster"]}
        _, report = finalize.build_dump(d)
        self.assertIn("no_task_ladder", codes(report["warnings"]))

    def test_a_section_that_is_one_source_passed_through_warns(self):
        d = base_dump()
        d["sources"]["s-docs"] = {"kind": "web", "url": "https://docs.example/product-card", "title": "ProductCard docs"}
        d["sources"]["s-guide"] = {"kind": "web", "url": "https://guide.example/cards", "title": "Card guide"}
        d["product_card_api"] = {"api-%d" % i: {"term": "prop %d" % i, "tier": 3, "prov": "researched", "src": ["s-docs"], "text": "x"}
                                 for i in range(6)}
        d["card_patterns"] = {"pat-%d" % i: {"term": "pattern %d" % i, "tier": 3, "prov": "researched",
                                             "src": ["s-docs"] if i % 2 else ["s-guide", "s-docs"], "text": "x"} for i in range(6)}
        d["ideas"] = {"idea-%d" % i: {"term": "idea %d" % i, "tier": 4, "prov": "inferred", "text": "x"} for i in range(6)}
        d["routing"].append({"job": "everything", "paths": ["/product_card_api", "/card_patterns", "/ideas"]})
        _, report = finalize.build_dump(d)
        flagged = [w["path"] for w in report["warnings"] if w["code"] == "undigested_source"]
        self.assertEqual(flagged, ["/product_card_api"])

    def test_tier_1_entry_without_anchor_is_demoted_to_tier_2(self):
        d = base_dump()
        d["sources"]["s-web"] = {"kind": "web", "url": "https://example.com/amber", "title": "Amber light"}
        d["palette"]["c-amber"].update({"prov": "researched", "src": ["s-web"]})
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
            d["palette"]["c-%d" % i] = {"term": "t%d" % i, "tier": 1, "prov": "user_stated", "anchor": "calm", "text": "x"}
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

    def test_the_first_lines_of_every_dump_say_to_deal_it_before_reading_on(self):
        # Test 14: builders that opened the dump alongside SKILL.md never reached use mode's deal step (7 of 12).
        text, out, _ = finalize.finish(base_dump())
        top = "\n".join(text.splitlines()[:4])
        self.assertIn("deal.py", top)
        self.assertIn("demo.metadump.json", top)
        self.assertIn("deal.py", out["manifest"]["how_to_read"][0])

    def test_the_reading_steps_end_with_a_look_at_what_was_built(self):
        # Tests 16 and 17: dump builds shipped clipping and overlap no builder saw; builders run the commands the dump names.
        _, out, _ = finalize.finish(base_dump())
        self.assertIn("look.py", out["manifest"]["how_to_read"][-1])

    def test_manifest_stats_count_entries_by_tier_and_prov(self):
        _, out, _ = finalize.finish(base_dump())
        stats = out["manifest"]["stats"]
        self.assertEqual(stats["entries"], 2)
        self.assertEqual(stats["by_prov"], {"inferred": 1, "user_stated": 1})
        self.assertEqual(stats["by_tier"], {"1": 1, "2": 1})
        self.assertGreater(stats["tokens"], 0)

    def thin(self, said, guessed):
        d = base_dump()  # 1 user_stated + 1 inferred already
        for i in range(said - 1):
            d["palette"]["c-said-%d" % i] = {"term": "s%d" % i, "tier": 2, "prov": "user_stated", "anchor": "calm", "text": "x"}
        for i in range(guessed - 1):
            d["palette"]["c-guess-%d" % i] = {"term": "g%d" % i, "tier": 3, "prov": "inferred", "text": "x"}
        return d

    def test_stats_report_grounding_and_under_a_fifth_collected_warns(self):
        _, out, report = finalize.finish(self.thin(5, 21))   # 5 of 26 = 19%
        self.assertEqual(out["manifest"]["stats"]["grounding"],
                         {"collected": 5, "derived": 21, "unknown": 0, "collected_share": 0.19, "hosts": 0})
        self.assertIn("low_grounding", codes(report["warnings"]))

    def test_exactly_a_fifth_collected_does_not_warn(self):
        _, out, report = finalize.finish(self.thin(6, 24))   # 6 of 30 = 20%
        self.assertNotIn("low_grounding", codes(report["warnings"]))

    def test_a_small_dump_does_not_warn(self):
        _, out, report = finalize.finish(base_dump())
        self.assertEqual(out["manifest"]["stats"]["grounding"]["collected_share"], 0.5)
        self.assertNotIn("low_grounding", codes(report["warnings"]))
        self.assertNotIn("narrow_sources", codes(report["warnings"]))

    def test_sources_from_fewer_than_three_hosts_warn(self):
        d = self.thin(10, 10)
        d["sources"] = {"s1": {"kind": "web", "url": "https://shopify.dev/a", "title": "a"},
                        "s2": {"kind": "web", "url": "https://shopify.dev/b", "title": "b"},
                        "s3": {"kind": "doc", "url": "https://www.nngroup.com/c", "title": "c"}}
        _, out, report = finalize.finish(d)
        self.assertEqual(out["manifest"]["stats"]["grounding"]["hosts"], 2)
        self.assertIn("narrow_sources", codes(report["warnings"]))
        d["sources"]["s4"] = {"kind": "image", "url": "https://upload.wikimedia.org/x.png", "title": "x", "origin": "web"}
        _, out, report = finalize.finish(d)
        self.assertEqual(out["manifest"]["stats"]["grounding"]["hosts"], 3)
        self.assertNotIn("narrow_sources", codes(report["warnings"]))

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

    def test_a_gap_shard_is_a_known_ticket_type_that_mints_only_derived_provenance(self):
        draft, report = self.merge({
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"},
                                    "sections": {"feel": {"g-calm": entry("calm", prov="researched")}}},
        })
        self.assertEqual(draft["feel"]["g-calm"]["prov"], "inferred")
        self.assertIn("prov_over_ceiling", codes(report["fixes"]))
        self.assertNotIn("unknown_ticket_type", codes(report["warnings"]))

    def test_a_gap_shard_may_replace_without_raising_provenance_and_may_delete(self):
        # Test 10: gap shards typed specialist could not edit, so `_replace` edits were silently ignored.
        draft, report = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"},
                             "sections": {"feel": {"q-calm": entry("calm", kind="quality", readings=[{"reading": "slow motion"}]),
                                                   "o-set": entry("the default set", tier=3, prov="proposed")}}},
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"},
                                    "sections": {"feel": {"q-calm": dict(entry("calm", tier=3, prov="user_stated", kind="quality",
                                                                               readings=[{"reading": "slow motion"}, {"reading": "few elements"}]),
                                                                         _replace=True),
                                                          "o-set": {"_delete": True}}}},
        })
        q = draft["feel"]["q-calm"]
        self.assertEqual([r["reading"] for r in q["readings"]], ["slow motion", "few elements"])
        self.assertEqual(q["tier"], 3)
        self.assertEqual(q["prov"], "inferred")
        self.assertIn("prov_upgrade_blocked", codes(report["fixes"]))
        self.assertNotIn("o-set", draft["feel"])
        self.assertNotIn("delete_not_allowed", codes(report["warnings"]))

    def test_a_round_2_gap_replace_of_an_entry_the_round_1_digest_replaced_wins(self):
        # In filename order 60-gap-* sorts before 90-normalize, so round 1's digest overwrote the gap round's widening.
        draft, _ = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"},
                             "sections": {"feel": {"q-sticky": entry("sticky", kind="quality", readings=[{"reading": "early settle"}])}}},
            "90-normalize.json": {"ticket": {"id": "90-normalize", "type": "normalize"},
                                  "sections": {"feel": {"q-sticky": dict(entry("sticky", kind="quality", aliases=["grippy"],
                                                                               readings=[{"reading": "early settle"}]), _replace=True)}}},
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"},
                                    "sections": {"feel": {"q-sticky": dict(entry("sticky", kind="quality", aliases=["grippy"],
                                                                                 readings=[{"reading": "early settle"}, {"reading": "slow grip"}]),
                                                                           _replace=True)}}},
        })
        self.assertEqual([r["reading"] for r in draft["feel"]["q-sticky"]["readings"]], ["early settle", "slow grip"])

    def test_a_round_2_gap_delete_of_a_lexicon_entry_stays_deleted(self):
        draft, _ = self.merge({
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"}, "sections": {"feel": {"q-calm": {"_delete": True}}}},
            "70-lexicon.json": {"ticket": {"id": "70-lexicon", "type": "lexicon"},
                                "sections": {"feel": {"q-calm": entry("calm", kind="quality", readings=[{"reading": "slow motion"}]),
                                                      "q-warm": entry("warm", kind="quality", readings=[{"reading": "amber light"}])}}},
        })
        self.assertNotIn("q-calm", draft["feel"])
        self.assertIn("q-warm", draft["feel"])

    def test_the_round_2_digest_applies_after_the_round_2_gap_shards(self):
        draft, _ = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"},
                             "sections": {"feel": {"q-sticky": entry("sticky", kind="quality", readings=[{"reading": "early settle"}])}}},
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"},
                                    "sections": {"feel": {"q-sticky": dict(entry("sticky", kind="quality",
                                                                                 readings=[{"reading": "early settle"}, {"reading": "slow grip"}]),
                                                                           _replace=True)}}},
            "91-normalize-r2.json": {"ticket": {"id": "91-normalize-r2", "type": "normalize"},
                                     "sections": {"feel": {"q-sticky": dict(entry("sticky", kind="quality", aliases=["grippy"],
                                                                                  readings=[{"reading": "early settle"}, {"reading": "slow grip"}]),
                                                                            _replace=True)}}},
        })
        self.assertEqual(draft["feel"]["q-sticky"]["aliases"], ["grippy"])

    def test_95_synthesis_still_applies_after_every_round_and_supplies_the_spine(self):
        # Synthesis rewrites 95-synthesis.json each round, so it lands after the latest round's digest.
        draft, _ = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"}, "sections": {"feel": {"c-note": entry("note")}}},
            "91-normalize-r2.json": {"ticket": {"id": "91-normalize-r2", "type": "normalize"},
                                     "sections": {"feel": {"c-note": dict(entry("note", tier=3), _replace=True)}}},
            "95-synthesis.json": {"ticket": {"id": "95-synthesis", "type": "synthesis"},
                                  "spine": {"essence": {"one_sentence": "Round two's thesis."}, "routing": [{"job": "feel", "paths": ["/feel"]}]},
                                  "sections": {"feel": {"c-note": dict(entry("note", tier=4), _replace=True)}}},
        })
        self.assertEqual(draft["essence"]["one_sentence"], "Round two's thesis.")
        self.assertEqual(draft["feel"]["c-note"]["tier"], 4)

    def test_a_repair_shard_applies_after_95_synthesis_whose_build_it_repairs(self):
        draft, _ = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"}, "sections": {"feel": {"c-note": entry("note")}}},
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"}, "sections": {"feel": {"c-more": entry("more")}}},
            "95-synthesis.json": {"ticket": {"id": "95-synthesis", "type": "synthesis"},
                                  "spine": {"essence": {"one_sentence": "A thesis whose routes don't resolve."},
                                            "routing": [{"job": "feel", "paths": ["/fele"]}]}},
            "97-repair-r2.json": {"ticket": {"id": "97-repair-r2", "type": "synthesis"},
                                  "spine": {"essence": {"one_sentence": "The repaired thesis."},
                                            "routing": [{"job": "feel", "paths": ["/feel"]}]}},
        })
        self.assertEqual(draft["essence"]["one_sentence"], "The repaired thesis.")
        self.assertEqual(draft["routing"], [{"job": "feel", "paths": ["/feel"]}])

    def test_a_round_1_repair_does_not_override_the_synthesis_a_later_round_rewrote(self):
        # Synthesis rewrites 95-synthesis.json in the latest round, so it belongs to that round: a repair of round 1's
        # build is superseded by round 2's rewrite, while round 2's own repair still applies after it.
        draft, _ = self.merge({
            "30-feel.json": {"ticket": {"id": "30-feel", "type": "specialist"}, "sections": {"feel": {"c-note": entry("note")}}},
            "60-gap-feel-r2.json": {"ticket": {"id": "60-gap-feel-r2", "type": "gap"}, "sections": {"feel": {"c-more": entry("more")}}},
            "95-synthesis.json": {"ticket": {"id": "95-synthesis", "type": "synthesis"},
                                  "spine": {"essence": {"one_sentence": "The round-2 thesis."},
                                            "routing": [{"job": "feel", "paths": ["/feel"]}]}},
            "97-repair-r1.json": {"ticket": {"id": "97-repair-r1", "type": "synthesis"},
                                  "spine": {"essence": {"one_sentence": "The round-1 repaired thesis."}}},
        })
        self.assertEqual(draft["essence"]["one_sentence"], "The round-2 thesis.")

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

    def test_summary_labels_each_report_line_by_its_bucket(self):
        d = base_dump()
        d["palette"]["c-amber"]["prov"] = "proposed"  # one fix: proposed_not_tier1
        path = os.path.join(self.root, "d.metadump.json")
        with open(path, "w") as f:
            json.dump(d, f)
        res = run_cli("check", path)
        fix_lines = [ln for ln in res.stdout.splitlines() if "proposed_not_tier1" in ln]
        self.assertEqual(len(fix_lines), 1)
        self.assertTrue(fix_lines[0].lstrip().startswith("fix "), fix_lines[0])

    def test_build_workdir_writes_dump_beside_work_and_exits_0(self):
        write_work(self.work, good_shards())
        res = run_cli("build", self.work)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        out_path = os.path.join(self.root, "metadumps", "demo.metadump.json")
        with open(out_path) as f:
            dump = json.load(f)
        self.assertEqual(dump["palette"]["c-amber"]["prov"], "user_stated")
        self.assertTrue(os.path.exists(os.path.join(self.work, "report.json")))

    def test_build_prints_the_grounding_mix(self):
        write_work(self.work, good_shards())   # 1 user_stated, 1 inferred, no web sources
        res = run_cli("build", self.work)
        self.assertIn("grounding: 1 of 2 collected (50%), 0 source hosts", res.stdout)

    def test_build_counts_oversized_entries_by_shard_so_the_main_loop_knows_which_worker_to_send_back(self):
        # Test 10: oversized_entry fired 2 to 23 times per dump, and the summary shows only the first 12 warnings.
        many = ["phrase %03d" % i for i in range(120)]   # about 360 tokens of properties
        shards = good_shards()
        shards["30-look.json"] = {"ticket": {"id": "30-look", "type": "specialist"},
                                  "sections": {"palette": {"c-big": entry("big facet", properties=many),
                                                           "c-big2": entry("big facet two", properties=many)}}}
        shards["70-lexicon.json"] = {"ticket": {"id": "70-lexicon", "type": "lexicon"},
                                     "sections": {"palette": {"c-words": entry("many words", properties=many)}}}
        write_work(self.work, shards)
        res = run_cli("build", self.work)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("oversized_entry by shard: 30-look 2 (c-big, c-big2); 70-lexicon 1 (c-words)", res.stdout.splitlines())

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

    def test_merge_names_every_oversized_entry_by_shard_for_the_digest(self):
        # The digest (normalize) reads merge's output to split oversized facets; before synthesis writes routes,
        # unrouted_section alone can fill the 12 warning lines the summary shows.
        many = ["phrase %03d" % i for i in range(120)]
        shards = good_shards()
        del shards["95-synth.json"]
        shards["30-look.json"] = {"ticket": {"id": "30-look", "type": "specialist"},
                                  "sections": {"look_%d" % i: {"c-look-%d" % i: entry("look %d" % i)} for i in range(12)}}
        shards["30-look.json"]["sections"]["look_0"]["c-big"] = entry("big facet", properties=many)
        write_work(self.work, shards)
        res = run_cli("merge", self.work)
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertIn("oversized_entry by shard: 30-look 1 (c-big)", res.stdout.splitlines())

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


class FacetObjects(unittest.TestCase):
    """0.7.0: dumps are written as facets of short phrases, the way the hand-made files were."""

    def test_facet_phrases_stay_out_of_the_index_so_it_does_not_double_the_file(self):
        # Test 8's dump: indexing every facet phrase made the index 25K tokens against a 24K body. grep finds
        # a phrase anyway (one entry per line); the index keeps terms, aliases, variants and keywords.
        d = base_dump()
        d["color"] = {"c-blue": entry("blue", keywords=["electric cyan"], properties=["subsurface glow"],
                                      descriptors=["self-illuminated"], signals=["dominant cyan hues"])}
        d["routing"][0]["paths"].append("/color")
        out, _ = finalize.build_dump(d)
        self.assertIn("/color/c-blue", out["index"]["electric cyan"]["hits"])
        for phrase in ("subsurface glow", "self-illuminated", "dominant cyan hues", "subsurface"):
            self.assertNotIn(phrase, out["index"], phrase)

    def test_a_quality_facet_with_one_reading_warns(self):
        # Test 8: the dump defined "sticky" once, inferred, and every build copied the curves tuned to it.
        d = base_dump()
        d["feel"] = {"q-calm": entry("calm", kind="quality", readings=[{"reading": "low contrast and slow motion"}])}
        d["routing"][0]["paths"].append("/feel")
        _, report = finalize.build_dump(d)
        self.assertEqual([w["path"] for w in report["warnings"] if w["code"] == "quality_one_reading"], ["/feel/q-calm"])

    def test_a_quality_facet_with_two_readings_does_not_warn(self):
        d = base_dump()
        d["feel"] = {"q-calm": entry("calm", kind="quality", readings=[{"reading": "low contrast and slow motion"},
                                                                       {"reading": "few elements and lots of air"}])}
        d["routing"][0]["paths"].append("/feel")
        _, report = finalize.build_dump(d)
        self.assertNotIn("quality_one_reading", codes(report["warnings"]))

    def test_a_section_left_with_only_notes_is_dropped(self):
        # Test 8: normalize merged three sections away but could only leave `_about` stubs behind, which then
        # warned as unrouted. A section with no entries is nothing a consumer can use.
        d = base_dump()
        d["feel"] = {"_about": "merged into /palette"}
        out, report = finalize.build_dump(d)
        self.assertNotIn("feel", out)
        self.assertEqual([f["path"] for f in report["fixes"] if f["code"] == "empty_section_dropped"], ["/feel"])
        self.assertNotIn("unrouted_section", codes(report["warnings"]))

    def test_an_oversized_facet_warns_but_a_timeline_may_be_long(self):
        # Test 8's facets ran to 400-500 tokens; the hand-made ones are 100-200. Measured timelines are long by nature.
        d = base_dump()
        many = ["phrase %03d" % i for i in range(120)]   # about 360 tokens of properties
        d["palette"]["c-big"] = entry("big facet", properties=many)
        d["palette"]["c-tl"] = entry("a timeline", kind="timeline", properties=many)
        _, report = finalize.build_dump(d)
        self.assertEqual([w["path"] for w in report["warnings"] if w["code"] == "oversized_entry"], ["/palette/c-big"])

    def test_long_prose_warns_so_entries_stay_lists_of_short_phrases(self):
        d = base_dump()
        d["palette"]["c-amber"]["text"] = " ".join(["word"] * 41)                    # 41 words: over the 40-word limit
        d["anti_keywords"]["ak-gloss"]["instead"] = " ".join(["matte"] * 21)        # 21 words: over the 20-word limit
        _, report = finalize.build_dump(d)
        wordy = sorted(w["path"] for w in report["warnings"] if w["code"] == "wordy_entry")
        self.assertEqual(wordy, ["/anti_keywords/ak-gloss", "/palette/c-amber"])

    def test_prose_within_the_limits_does_not_warn(self):
        d = base_dump()
        d["palette"]["c-amber"]["text"] = " ".join(["word"] * 40)
        d["anti_keywords"]["ak-gloss"]["instead"] = " ".join(["matte"] * 20)
        _, report = finalize.build_dump(d)
        self.assertNotIn("wordy_entry", codes(report["warnings"]))


class Candidates(unittest.TestCase):
    """0.7.1: a task that asks for N items gets a pool of candidates, each confirmed by a fetched source (ADR 0011)."""

    def pool_dump(self, pool):
        d = base_dump()
        d["sources"]["s-label"] = {"kind": "web", "url": "https://label.example/catalog", "title": "Label catalog",
                                   "fetched": "2026-11-05", "quote": "a 1983 single"}
        d["pool"] = pool
        d["routing"][0]["paths"].append("/pool")
        return d

    def test_a_candidate_no_fetched_source_confirms_becomes_an_unverified_lead_at_tier_4(self):
        # Test 10: the playlist dump's pools named bands and no songs; the prompt-only builds invented titles.
        d = self.pool_dump({
            "cand-listed": entry("listed song", kind="candidate", by="a band", year=1983, reading="obscure",
                                 prov="researched", src=["s-label"]),
            "cand-recalled": entry("recalled song", tier=3, kind="candidate", by="a band", reading="melodic riff"),
        })
        out, report = finalize.build_dump(d)
        self.assertEqual(out["pool"]["cand-recalled"]["status"], "unverified")
        self.assertEqual(out["pool"]["cand-recalled"]["tier"], 4)
        self.assertNotIn("status", out["pool"]["cand-listed"])
        self.assertEqual(out["pool"]["cand-listed"]["tier"], 2)
        self.assertEqual([f["path"] for f in report["fixes"] if f["code"] == "candidate_unverified"], ["/pool/cand-recalled"])

    def test_every_candidate_that_is_not_collected_ends_unverified_at_tier_4_whatever_it_claimed(self):
        d = self.pool_dump({
            "cand-flagged": entry("flagged song", kind="candidate", by="a band", status="unverified"),        # tier 2
            "cand-claimed": entry("claimed song", tier=3, kind="candidate", by="a band", status="verified"),
            "cand-settled": entry("settled song", tier=4, kind="candidate", by="a band", status="unverified"),
        })
        out, report = finalize.build_dump(d)
        for cid in ("cand-flagged", "cand-claimed", "cand-settled"):
            self.assertEqual((out["pool"][cid]["status"], out["pool"][cid]["tier"]), ("unverified", 4), cid)
        self.assertEqual(sorted(f["path"] for f in report["fixes"] if f["code"] == "candidate_unverified"),
                         ["/pool/cand-claimed", "/pool/cand-flagged"])

    def test_a_candidate_pool_with_fewer_than_five_verified_candidates_warns(self):
        pool = {"cand-%d" % i: entry("listed song %d" % i, kind="candidate", by="a band", reading="obscure",
                                     prov="researched", src=["s-label"]) for i in range(4)}
        pool["cand-lead"] = entry("recalled song", tier=4, kind="candidate", by="a band", status="unverified")
        _, report = finalize.build_dump(self.pool_dump(pool))   # five candidates, four verified
        self.assertIn("candidate_pool_thin", codes(report["warnings"]))
        pool["cand-4"] = entry("listed song 4", kind="candidate", by="a band", reading="melodic riff",
                               prov="researched", src=["s-label"])
        _, report = finalize.build_dump(self.pool_dump(pool))   # five verified
        self.assertNotIn("candidate_pool_thin", codes(report["warnings"]))
        _, report = finalize.build_dump(base_dump())             # no candidates at all
        self.assertNotIn("candidate_pool_thin", codes(report["warnings"]))


class QuotesAgainstPages(unittest.TestCase):
    """0.7.1: a source's quote is checked against the page webpages.py cached, when there is one."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def cache_page(self, url, text, key="k1", final_url=None):
        # The shapes webpages.py writes: <WORK>/pages/manifest.json and one record per page with its clean `text`.
        pages = os.path.join(self.tmp, "pages")
        os.makedirs(pages, exist_ok=True)
        final = final_url or url
        with open(os.path.join(pages, key + ".json"), "w") as f:
            json.dump({"schema": "metadump-page/1", "key": key, "url": url, "outcome": {"ok": True, "reason": "ok"},
                       "fetch": {"final_url": final}, "text": text,
                       "chunks": [{"index": 0, "heading_path": [], "span": [0, len(text)], "url": final, "text": text}]}, f)
        with open(os.path.join(pages, "manifest.json"), "w") as f:
            json.dump({"schema": "metadump-pages/1", "pages": [{"key": key, "url": url, "final_url": final, "ok": True,
                                                                "record": key + ".json"}]}, f)

    def merge_sources(self, sources):
        write_work(self.tmp, {"20-research.json": {"ticket": {"id": "20-research", "type": "research"}, "sources": sources,
                                                   "sections": {"pool": {"c-a": entry("a", prov="researched", src=sorted(sources))}}}})
        return finalize.merge_workdir(self.tmp)

    def test_a_quote_its_cached_page_does_not_contain_warns(self):
        # Test 10: three dump builders said many `researched` quotes came from WebFetch summaries or search snippets.
        self.cache_page("https://label.example/catalog", "The 1983 single was pressed in a run of 500 copies.")
        _, report = self.merge_sources({
            "s-label": {"kind": "web", "url": "https://label.example/catalog", "title": "Catalog", "quote": "pressed in a run of 5,000 copies"},
            "s-elsewhere": {"kind": "web", "url": "https://elsewhere.example/p", "title": "Not cached", "quote": "anything at all"},
        })
        flagged = [w for w in report["warnings"] if w["code"] == "quote_not_in_page"]
        self.assertEqual([w["path"] for w in flagged], ["/sources/s-label"])
        self.assertIn("https://label.example/catalog", flagged[0]["msg"])

    def test_a_quote_matches_its_cached_page_whatever_its_case_spacing_and_curly_quotes(self):
        self.cache_page("https://label.example/catalog", "Its “warm, ringing” lead guitar\n   defined the label’s sound.")
        _, report = self.merge_sources({
            "s-label": {"kind": "web", "url": "https://label.example/catalog", "title": "Catalog",
                        "quote": "its \"warm, ringing\" lead guitar defined the LABEL'S sound"},
        })
        self.assertNotIn("quote_not_in_page", codes(report["warnings"]))

    def test_a_source_that_cites_the_page_it_was_redirected_to_is_checked_too(self):
        self.cache_page("http://label.example/catalog", "The 1983 single was pressed in a run of 500 copies.",
                        final_url="https://www.label.example/catalog")
        _, report = self.merge_sources({
            "s-label": {"kind": "web", "url": "https://www.label.example/catalog", "title": "Catalog", "quote": "a run of 5,000 copies"},
        })
        self.assertEqual([w["path"] for w in report["warnings"] if w["code"] == "quote_not_in_page"], ["/sources/s-label"])

    def test_an_unreadable_page_cache_neither_crashes_merge_nor_blocks_the_build(self):
        source = {"s-label": {"kind": "web", "url": "https://label.example/catalog", "title": "Catalog", "quote": "a 1983 single"}}
        self.cache_page("https://label.example/catalog", "x")
        with open(os.path.join(self.tmp, "pages", "k1.json"), "w") as f:
            f.write("{not json")                                   # a record cut off mid-write
        _, report = self.merge_sources(source)
        self.assertEqual(report["errors"], [])
        self.assertNotIn("quote_not_in_page", codes(report["warnings"]))
        with open(os.path.join(self.tmp, "pages", "manifest.json"), "w") as f:
            f.write("[1, 2")                                      # a manifest cut off mid-write
        _, report = self.merge_sources(source)
        self.assertEqual(report["errors"], [])


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
        self.assertEqual(sorted(auto["paths"]), ["/palette/c-amber"])

    def test_the_first_route_offers_material_rather_than_rules(self):
        # "always first: the defining tier-1 entries" read as the rules to apply; consumers followed it (ADR 0012).
        out, _ = finalize.build_dump(base_dump())
        self.assertEqual(out["routing"][0]["job"], "start here: what the task is most about")
        self.assertNotRegex(out["routing"][0]["when"], r"(?i)\b(always|defining|must)\b")

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

    def test_found_tickets_cannot_mint_reference_observed(self):
        draft, report = self.merge({
            "19-watch-found-demo.json": {"ticket": {"id": "19-watch-found-demo", "type": "watch"},
                                         "sections": {"motion": {"m-found-a": entry("a", prov="reference_observed"),
                                                                 "m-found-b": entry("b", prov="researched")}}},
            "11-watch-r2.json": {"ticket": {"id": "11-watch-r2", "type": "watch"},
                                 "sections": {"motion": {"m-user-a": entry("c", prov="reference_observed")}}}})
        sec = draft["motion"]
        self.assertEqual(sec["m-found-a"]["prov"], "researched")
        self.assertEqual(sec["m-found-b"]["prov"], "researched")
        self.assertEqual(sec["m-user-a"]["prov"], "reference_observed")
        self.assertIn("prov_over_ceiling", codes(report["fixes"]))

    def test_found_tickets_sources_are_relabeled_as_found_online(self):
        draft, report = self.merge({
            "28-scrape-found-maker.json": {"ticket": {"id": "28-scrape-found-maker", "type": "scrape"},
                                           "sources": {"s-maker": {"kind": "reference", "url": "https://maker.example/p", "user_supplied": True},
                                                       "v-demo": {"kind": "video", "url": "https://v.example/a.mp4", "origin": "user"}},
                                           "sections": {"material": {"mat-a": entry("a", prov="researched", src=["s-maker"])}}}})
        self.assertEqual(draft["sources"]["s-maker"]["kind"], "web")
        self.assertFalse(draft["sources"]["s-maker"].get("user_supplied"))
        self.assertEqual(draft["sources"]["v-demo"]["origin"], "web")
        self.assertIn("found_source_relabeled", codes(report["fixes"]))

    def test_an_options_group_with_an_about_note_is_a_group_not_an_entry(self):
        draft, report = self.merge({
            "30-style.json": {"ticket": {"id": "30-style", "type": "specialist"},
                              "sections": {"style": {"options": {"_about": "options, not requirements",
                                                                 "o-radius": entry("radius 8px", tier=4, prov="proposed"),
                                                                 "o-hairline": entry("1px hairline", tier=4, prov="proposed")}}}}})
        self.assertEqual(draft["style"]["options"]["o-radius"]["prov"], "proposed")
        self.assertEqual(draft["style"]["options"]["_about"], "options, not requirements")
        ids = [eid for eid, _p, _e, _h in finalize.iter_entries(draft)]
        self.assertEqual(sorted(ids), ["o-hairline", "o-radius"])

    def test_collected_images_nobody_looked_at_warn(self):
        os.makedirs(os.path.join(self.tmp, "images"), exist_ok=True)
        with open(os.path.join(self.tmp, "images", "manifest.json"), "w") as f:
            json.dump({"schema": "metadump-images/1", "images": [{"id": "img-seen", "file": "a.png"}, {"id": "img-unseen", "file": "b.png"}]}, f)
        draft, report = self.merge({
            "29-moodboard.json": {"ticket": {"id": "29-moodboard", "type": "moodboard"},
                                  "sources": {"i-a": {"kind": "image", "path": "images/a.png", "origin": "web", "image_id": "img-seen"},
                                              "i-b": {"kind": "image", "path": "images/b.png", "origin": "web", "image_id": "img-unseen"}},
                                  "sections": {"look": {"v-a": entry("hairline cards", prov="researched", src=["i-a"], method="visual"),
                                                        "p-b": entry("#F4F1EC", prov="researched", src=["i-b"], method="pixel-sample")}}}})
        unseen = [w["msg"] for w in report["warnings"] if w["code"] == "image_not_viewed"]
        self.assertEqual(len(unseen), 1)
        self.assertIn("img-unseen", unseen[0])

    def test_an_image_counts_as_seen_when_a_visual_entry_cites_where_it_came_from(self):
        os.makedirs(os.path.join(self.tmp, "images"), exist_ok=True)
        with open(os.path.join(self.tmp, "images", "manifest.json"), "w") as f:
            json.dump({"images": [
                {"id": "img-shot", "file": "s.png", "source": {"kind": "screenshot", "page": "https://shop.example/p"}},
                {"id": "img-frame", "file": "f.png", "source": {"kind": "video", "video": "https://v.example/a.mp4", "timecode": "00:00:01.000"}},
                {"id": "img-url", "file": "u.png", "source": {"kind": "url", "url": "https://i.example/x.png"}},
                {"id": "img-lost", "file": "l.png", "source": {"kind": "url", "url": "https://i.example/lost.png"}}]}, f)
        _, report = self.merge({
            "28-scrape-found-shop.json": {"ticket": {"id": "28-scrape-found-shop", "type": "scrape"},
                "sources": {"s-page": {"kind": "web", "url": "https://shop.example/p", "title": "p"}},
                "sections": {"look": {"v-shot": entry("hairline grid", prov="researched", src=["s-page"], method="visual")}}},
            "19-watch-found-a.json": {"ticket": {"id": "19-watch-found-a", "type": "watch"},
                "sources": {"v-a": {"kind": "video", "url": "https://v.example/a.mp4", "title": "a", "origin": "web"}},
                "sections": {"motion": {"fr-1": entry("lid half open", prov="researched", src=["v-a"], method="visual", timecode="00:00:01.000")}}},
            "29-moodboard.json": {"ticket": {"id": "29-moodboard", "type": "moodboard"},
                "sources": {"i-x": {"kind": "image", "url": "https://i.example/x.png", "title": "x", "origin": "web"}},
                "sections": {"look": {"v-x": entry("soft daylight", prov="researched", src=["i-x"], method="visual")}}}})
        unseen = [w for w in report["warnings"] if w["code"] == "image_not_viewed"]
        self.assertEqual([w["path"] for w in unseen], ["images/manifest.json:/img-lost"])

    def test_an_image_the_moodboard_lists_as_skipped_with_a_reason_counts_as_handled(self):
        # Test 10: the button dump described 31 moodboard images, mostly page screenshots and off-topic thumbnails.
        os.makedirs(os.path.join(self.tmp, "images"), exist_ok=True)
        with open(os.path.join(self.tmp, "images", "manifest.json"), "w") as f:
            json.dump({"images": [{"id": "img-card", "file": "c.png"}, {"id": "img-logo", "file": "l.png"},
                                  {"id": "img-thumb", "file": "t.png"}]}, f)
        _, report = self.merge({
            "29-moodboard.json": {"ticket": {"id": "29-moodboard", "type": "moodboard"},
                                  "sources": {"i-card": {"kind": "image", "path": "images/c.png", "origin": "web", "image_id": "img-card"}},
                                  "sections": {"look": {"v-card": entry("hairline cards", prov="researched", src=["i-card"], method="visual"),
                                                        "v-skipped": entry("images not described", tier=4, method="visual",
                                                                           skipped=[{"id": "img-logo", "reason": "site logo"}])}}}})
        unseen = [w["path"] for w in report["warnings"] if w["code"] == "image_not_viewed"]
        self.assertEqual(unseen, ["images/manifest.json:/img-thumb"])

    def test_a_malformed_images_manifest_does_not_crash_merge(self):
        os.makedirs(os.path.join(self.tmp, "images"), exist_ok=True)
        with open(os.path.join(self.tmp, "images", "manifest.json"), "w") as f:
            json.dump(["not", "a", "manifest"], f)
        _, report = self.merge({"30-a.json": {"ticket": {"id": "30-a", "type": "specialist"}, "sections": {"look": {"c-a": entry("a")}}}})
        self.assertNotIn("image_not_viewed", codes(report["warnings"]))

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

    def test_a_worn_path_whose_instead_only_turns_the_quality_down_warns(self):
        # Test 15: "neon glow" became "a soft tinted glow only on hover, at low opacity", and the dump buttons came out quiet.
        d = base_dump()
        d["anti_keywords"]["ak-glow"] = {"term": "neon glow", "kind": "not_wanted", "tier": 2, "prov": "inferred",
                                         "instead": "a faint tinted glow only on hover, at low opacity"}
        _, report = finalize.build_dump(d)
        self.assertIn("tamed_instead", codes(report["warnings"]))

    def test_a_worn_path_whose_instead_also_goes_further_does_not_warn(self):
        d = base_dump()
        d["anti_keywords"]["ak-glow"] = {"term": "neon glow", "kind": "not_wanted", "tier": 2, "prov": "inferred",
                                         "instead": "a faint halo, or a bloom that fills the whole card"}
        d["anti_keywords"]["ak-users"] = {"term": "loud colour", "kind": "not_wanted", "tier": 1, "prov": "user_stated",
                                          "anchor": "amber", "instead": "a subdued amber"}
        _, report = finalize.build_dump(d)
        self.assertNotIn("tamed_instead", codes(report["warnings"]))

    def test_head_reads_as_relevance_not_obligation(self):
        _, out, _ = finalize.finish(base_dump())
        head = json.dumps(out["routing"][0]) + json.dumps(out["manifest"]["how_to_read"])
        self.assertNotIn("must be expressed", head)
        self.assertNotIn("constrains", head)
        self.assertIn("relevan", out["routing"][0]["when"])


if __name__ == "__main__":
    unittest.main()

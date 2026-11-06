"""Tests for skills/metadump/scripts/deal.py, seam S13 (run: python3 -m unittest discover -s tests).
Dealing gives each session the same dump in a fresh random order, plus a random place to start (ADR 0014)."""
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
sys.path.insert(0, SCRIPTS)

import deal  # noqa: E402
import finalize  # noqa: E402

DEAL = os.path.join(SCRIPTS, "deal.py")


def dump():
    return {
        "manifest": {"schema": "metadump/1", "slug": "demo", "version": 1, "created": "2026-11-05",
                     "prompt": "a calm poster lit by amber light", "references": [], "consumers": ["image"], "depth": "lite"},
        "essence": {"one_sentence": "Amber light makes paper feel slow.",
                    "angles": [{"angle": "dusk window", "text": "Light spills across a sill."},
                               {"angle": "lamp-lit desk", "text": "A warm pool on paper."},
                               {"angle": "street glow", "text": "Sodium light through a blind."},
                               {"angle": "candle edge", "text": "One flame, a dark room."}]},
        "routing": [{"job": "make the image", "when": "rendering", "paths": ["/light"]}],
        "exports": {}, "anti_keywords": {}, "checks": {}, "open_questions": {},
        "light": {
            "l-amber": {"term": "amber light", "tier": 1, "prov": "user_stated", "anchor": "amber light", "text": "Warm amber key."},
            "l-warmth": {"term": "warmth", "tier": 2, "prov": "inferred", "text": "Warm tones.",
                         "tokens": {"status": "illustrative", "kelvin": ["1800 K", "2200 K", "2700 K", "3000 K"]}},
            "l-measured": {"term": "measured fall-off", "tier": 2, "prov": "inferred", "text": "From the reference.",
                           "tokens": {"status": "measured", "stops": ["0 m", "1 m", "2 m", "3 m"]}},
            "l-sodium": {"term": "sodium vapour", "tier": 3, "prov": "inferred", "text": "Mono-orange street light."},
            "l-purkinje": {"term": "Purkinje shift", "tier": 4, "prov": "inferred", "text": "Blues brighten at dusk."},
        },
        "sources": {},
    }


def entry_pointers(d):
    return sorted(ptr for _eid, ptr, _e, _h in finalize.iter_entries(d))


DECK = ["/light/l-amber", "/light/l-measured", "/light/l-purkinje", "/light/l-sodium", "/light/l-warmth"]


def bigger_dump():
    d = dump()
    d["light"].update({"l-x%d" % i: {"term": "extra light %d" % i, "tier": 2, "prov": "inferred", "text": "More light %d." % i}
                       for i in range(6)})
    return d


class DealKeepsTheDump(unittest.TestCase):
    def test_every_entry_in_a_hand_is_the_decks_own_entry_at_the_same_pointer(self):
        d = dump()
        for seed in range(10):
            dealt, _hand = deal.deal(d, random.Random(seed))
            for ptr in entry_pointers(dealt):
                self.assertIn(ptr, DECK)
                self.assertEqual(finalize.resolve(dealt, ptr)[1]["term"], finalize.resolve(d, ptr)[1]["term"])
        self.assertEqual(dealt["manifest"]["prompt"], "a calm poster lit by amber light")
        self.assertEqual(sorted(a["angle"] for a in dealt["essence"]["angles"]),
                         ["candle edge", "dusk window", "lamp-lit desk", "street glow"])


class DealAHand(unittest.TestCase):
    # Test 14: four toast builders dealt different hands and still built the same toast; each had read every entry.
    def test_a_hand_holds_part_of_a_section_and_every_entry_gets_dealt_sometime(self):
        seen = set()
        for seed in range(40):
            dealt, _ = deal.deal(bigger_dump(), random.Random(seed))
            hand = set(entry_pointers(dealt))
            self.assertLess(len(hand), 11)
            seen |= hand
        self.assertEqual(len(seen), 11)

    def test_every_hand_keeps_the_users_words_tier_1_their_donts_word_senses_and_review_questions(self):
        d = bigger_dump()
        d["light"]["l-users-calm"] = {"term": "calm", "tier": 2, "prov": "user_stated", "anchor": "calm", "text": "The user said calm."}
        d["anti_keywords"]["ak-users-no-neon"] = {"term": "neon", "kind": "not_wanted", "instead": "a named lamp", "tier": 1,
                                                  "prov": "user_stated", "anchor": "no neon"}
        d["anti_keywords"]["ak-sense"] = {"term": "warm", "kind": "not_meant", "excluded_sense": "friendly",
                                          "instead": "warm in colour temperature", "tier": 2, "prov": "inferred"}
        d["checks"]["ck-warm"] = {"text": "Does the light read warm at a glance?"}
        for seed in range(30):
            dealt, _ = deal.deal(d, random.Random(seed))
            for ptr in ("/light/l-amber", "/light/l-users-calm", "/anti_keywords/ak-users-no-neon", "/anti_keywords/ak-sense"):
                self.assertTrue(finalize.resolve(dealt, ptr)[0], ptr)
            self.assertIn("ck-warm", dealt["checks"])

    def test_the_dumps_own_worn_paths_are_dealt_like_the_rest(self):
        # Test 15: a hand kept every worn path and half the material, so "avoid this" doubled its share and the
        # dreamlike buttons came out quiet (ADR 0016).
        d = bigger_dump()
        worn = ["ak-w%d" % i for i in range(4)]
        for k in worn:
            d["anti_keywords"][k] = {"term": "worn %s" % k, "kind": "not_wanted", "instead": "further", "tier": 2, "prov": "inferred"}
        seen = set()
        for seed in range(40):
            dealt, _ = deal.deal(d, random.Random(seed))
            held = {k for k in worn if k in dealt["anti_keywords"]}
            self.assertLess(len(held), 4)
            seen |= held
        self.assertEqual(seen, set(worn))

    def test_routes_and_the_index_point_only_at_entries_in_the_hand(self):
        d = bigger_dump()
        every = sorted(DECK + ["/light/l-x%d" % i for i in range(6)])
        d["routing"].append({"job": "pick the light", "when": "choosing", "paths": every})
        d["index"] = {"light": {"hits": every}, "warm": {"hits": [], "words": ["/light/l-warmth", "/light/l-amber"]}}
        for seed in range(20):
            dealt, _ = deal.deal(d, random.Random(seed))
            pointers = [p for r in dealt["routing"] for p in r["paths"]]
            pointers += [p for v in dealt["index"].values() for p in v.get("hits", []) + v.get("words", [])]
            for ptr in pointers:
                self.assertTrue(finalize.resolve(dealt, ptr)[0], ptr)
            self.assertIn("/light/l-amber", dealt["index"]["warm"]["words"])

class DealShufflesWhereSessionsStart(unittest.TestCase):
    # Test 13: three of four builds took the dump's first angle; a model alone always starts from the top.
    def test_the_first_angle_differs_from_deal_to_deal(self):
        firsts = {deal.deal(dump(), random.Random(seed))[0]["essence"]["angles"][0]["angle"] for seed in range(30)}
        self.assertGreaterEqual(len(firsts), 3)

    def test_the_hand_starts_from_one_of_the_dumps_own_angles(self):
        names = {"candle edge", "dusk window", "lamp-lit desk", "street glow"}
        starts = {deal.deal(dump(), random.Random(seed))[1]["start_angle"]["angle"] for seed in range(30)}
        self.assertTrue(starts <= names)
        self.assertGreaterEqual(len(starts), 3)


class DealShufflesSpreadsNotFacts(unittest.TestCase):
    # Test 13: every toast reused the dump's palette and the buttons the first two curves of each spread.
    def test_an_illustrative_spread_starts_somewhere_new_from_deal_to_deal(self):
        hands = [deal.deal(dump(), random.Random(seed))[0]["light"] for seed in range(40)]
        firsts = {h["l-warmth"]["tokens"]["kelvin"][0] for h in hands if "l-warmth" in h}
        self.assertGreaterEqual(len(firsts), 3)

    def test_measured_values_keep_their_order(self):
        for seed in range(30):
            dealt, _ = deal.deal(dump(), random.Random(seed))
            if "l-measured" in dealt["light"]:
                self.assertEqual(dealt["light"]["l-measured"]["tokens"]["stops"], ["0 m", "1 m", "2 m", "3 m"])

    def test_the_entries_in_a_section_come_in_a_new_order(self):
        firsts = {next(iter(deal.deal(dump(), random.Random(seed))[0]["light"])) for seed in range(30)}
        self.assertGreaterEqual(len(firsts), 3)

class TheHand(unittest.TestCase):
    def test_the_hand_deals_up_to_two_deep_cuts_from_the_outer_tiers_it_holds(self):
        for seed in range(10):
            dealt, hand = deal.deal(dump(), random.Random(seed))
            held = [p for p in entry_pointers(dealt) if p in ("/light/l-purkinje", "/light/l-sodium")]
            self.assertEqual(sorted(c["ptr"] for c in hand["deep_cuts"]), sorted(held))

    def test_worn_paths_and_review_questions_are_never_dealt_as_deep_cuts(self):
        # A real dump dealt the noise word "ethereal" (an anti-keyword at tier 4) as something to play with.
        d = dump()
        d["anti_keywords"]["ak-ethereal"] = {"term": "ethereal", "kind": "not_wanted", "instead": "a named light",
                                             "tier": 4, "prov": "inferred", "class": "noise"}
        for seed in range(20):
            _, hand = deal.deal(d, random.Random(seed))
            self.assertNotIn("ethereal", [c["term"] for c in hand["deep_cuts"]])

    def test_a_deep_cut_always_has_something_to_play_with(self):
        # Test 14 dealt a research query with no text ("haiku cloud search") as a deep cut.
        d = dump()
        d["queries"] = {"q-search": {"term": "poster light search", "tier": 4, "prov": "researched"}}
        for seed in range(20):
            _, hand = deal.deal(d, random.Random(seed))
            self.assertNotIn("poster light search", [c["term"] for c in hand["deep_cuts"]])

    def test_a_dump_without_angles_or_outer_tiers_still_deals(self):
        d = dump()
        del d["essence"]["angles"]
        d["light"] = {"l-amber": d["light"]["l-amber"]}
        dealt, hand = deal.deal(d, random.Random(1))
        self.assertEqual(entry_pointers(dealt), ["/light/l-amber"])
        self.assertEqual(hand.get("deep_cuts"), [])

class TheCommand(unittest.TestCase):
    def test_the_command_writes_a_dealt_copy_and_points_the_session_at_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = os.path.join(tmp, "demo.metadump.json"), os.path.join(tmp, "dealt.json")
            with open(src, "w") as f:
                json.dump(dump(), f)
            run = subprocess.run([sys.executable, DEAL, src, "--out", out, "--seed", "3"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn(out, run.stdout)
            self.assertTrue(any(name in run.stdout for name in ("candle edge", "dusk window", "lamp-lit desk", "street glow")))
            with open(out) as f:
                self.assertTrue(set(entry_pointers(json.load(f))) <= set(DECK))

    def test_the_dealt_copy_says_it_is_a_hand_and_reads_from_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            src, out = os.path.join(tmp, "demo.metadump.json"), os.path.join(tmp, "dealt.json")
            with open(src, "w") as f:
                f.write(finalize.finish(bigger_dump())[0])
            subprocess.run([sys.executable, DEAL, src, "--out", out, "--seed", "5"], capture_output=True, text=True, check=True)
            with open(out) as f:
                text = f.read()
            copy = json.loads(text)
            man = copy["manifest"]
            self.assertIn("hand", man["deal"])
            self.assertIn(src, man["deal"])
            steps = " ".join(man["how_to_read"])
            self.assertIn(out, steps)
            self.assertNotIn("deal.py", steps)
            self.assertEqual(text.splitlines()[man["head_lines"] - 1].strip().rstrip(","), "]")
            self.assertEqual(man["stats"]["entries"], len(entry_pointers(copy)))


if __name__ == "__main__":
    unittest.main()

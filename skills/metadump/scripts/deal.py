#!/usr/bin/env python3
"""Deal a meta dump: a hand of its material in a fresh random order for this session, and a random place to start.

A model reading a dump top to bottom starts from whatever comes first, so every session that reads the same dump
converges on its first angle, its first values and its first palette (tests 12 and 13). Dealing moves that choice
out of the model (ADR 0014): real randomness reorders the dump's lists and sections and picks a starting angle and
a few deep cuts, so each session explores a different corner of the same dump. Since test 14 showed order alone is not enough, the
hand also holds only part of the deck (ADR 0015): the request, tier 1, worn paths and review questions, plus a random
half of the rest. The dump file itself is never changed.

Usage: python3 deal.py <dump.json> [--out <dealt copy path>] [--seed N]
Prints the hand and writes the dealt copy (default: a temp file); read the copy for the rest of the session.
Python 3.9+, standard library only.
"""
import argparse
import copy
import json
import math
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finalize  # noqa: E402


DEEP_CUTS = 2   # outer-tier entries the hand puts on top: the less obvious material a session starts beside
SHARE = 0.5     # of each task section's entries dealt into a hand (ADR 0015); the deck itself stays whole


def deal(dump, rng):
    """Return (dealt dump, hand). The dealt dump holds exactly the same entries at the same pointers."""
    dealt = copy.deepcopy(dump)
    hand = {}
    essence = dealt.get("essence") or {}
    angles = essence.get("angles")
    if isinstance(angles, list) and angles:
        rng.shuffle(angles)
        hand["start_angle"] = rng.choice(angles)
    if isinstance(essence.get("readings"), list):
        rng.shuffle(essence["readings"])
    for name in [k for k in dealt if k not in finalize.SPINE_KEYS and k not in finalize.LOOKUP_KEYS]:
        if isinstance(dealt[name], dict):
            dealt[name] = _shuffled_mapping(dealt[name], rng)
    _deal_hand(dealt, rng)
    outer = []
    for _eid, ptr, entry, _h in finalize.iter_entries(dealt):
        _shuffle_entry(entry, rng)
        in_task_section = ptr.split("/")[1] not in finalize.SPINE_KEYS   # not a worn path, review question or open question
        if entry.get("tier") in (3, 4) and in_task_section and entry.get("text"):   # a deep cut needs something to play with
            outer.append({"ptr": ptr, "term": entry.get("term"), "text": entry.get("text")})
    hand["deep_cuts"] = rng.sample(outer, min(DEEP_CUTS, len(outer)))
    return dealt, hand


def _deal_hand(dealt, rng):
    """Leave out a random share of each task section's entries (ADR 0015): every session works from a different hand."""
    by_section = {}
    for _eid, ptr, entry, _h in finalize.iter_entries(dealt):
        section = ptr.split("/")[1]
        if section in finalize.SPINE_KEYS:
            continue
        ptrs = by_section.setdefault(section, [])
        if entry.get("tier") != 1 and entry.get("prov") != "user_stated":   # the request itself is in every hand
            ptrs.append(ptr)
    for section, ptrs in by_section.items():
        keep = min(len(ptrs), max(1, math.ceil(len(ptrs) * SHARE)))
        for ptr in rng.sample(ptrs, len(ptrs) - keep):
            _remove(dealt, ptr)
    for section in by_section:
        _drop_empty_groups(dealt[_unescape(section)])
    _deal_worn_paths(dealt, rng)
    _point_at_the_hand(dealt)


def _deal_worn_paths(dealt, rng):
    """The build's own worn paths are dealt like the rest, so a hand's share of avoid-lists stays the dump's (ADR 0016).
    The user's own don'ts and the senses a word doesn't mean are in every hand."""
    worn = dealt.get("anti_keywords")
    if not isinstance(worn, dict):
        return
    dealable = [k for k, ak in worn.items() if isinstance(ak, dict) and ak.get("kind") == "not_wanted"
                and ak.get("prov") != "user_stated" and ak.get("tier") != 1]
    keep = min(len(dealable), max(1, math.ceil(len(dealable) * SHARE)))
    for key in rng.sample(dealable, len(dealable) - keep):
        del worn[key]


def _point_at_the_hand(dealt):
    """Routes and the index lose pointers to entries left out of the hand."""
    def held(ptr):
        return finalize.resolve(dealt, ptr)[0]
    routes = dealt.get("routing")
    if isinstance(routes, list):
        for route in routes:
            if isinstance(route, dict) and isinstance(route.get("paths"), list):
                route["paths"] = [p for p in route["paths"] if held(p)]
        dealt["routing"] = [r for r in routes if not (isinstance(r, dict) and r.get("paths") == [])]
    index = dealt.get("index")
    if isinstance(index, dict):
        for term in list(index):
            hits = index[term]
            if not isinstance(hits, dict):
                continue
            for kind in ("hits", "words"):
                if isinstance(hits.get(kind), list):
                    hits[kind] = [p for p in hits[kind] if held(p)]
            if not hits.get("hits") and not hits.get("words") and not hits.get("not_meant"):
                del index[term]


def _unescape(tok):
    return tok.replace("~1", "/").replace("~0", "~")


def _remove(doc, ptr):
    toks = [_unescape(t) for t in ptr[1:].split("/")]
    parent = doc
    for tok in toks[:-1]:
        parent = parent[tok]
    del parent[toks[-1]]


def _drop_empty_groups(container):
    """A group whose entries were all left out goes too; an empty dict would read as an entry."""
    for key in [k for k in container if not str(k).startswith("_")]:
        val = container[key]
        if isinstance(val, dict) and "tier" not in val and "prov" not in val:
            _drop_empty_groups(val)
            if not [k for k in val if not str(k).startswith("_")]:
                del container[key]


def _shuffled_mapping(mapping, rng):
    """The same keys in a new order (notes like `_about` stay first); groups inside are shuffled too."""
    notes = [k for k in mapping if k.startswith("_")]
    keys = [k for k in mapping if not k.startswith("_")]
    rng.shuffle(keys)
    out = {k: mapping[k] for k in notes}
    for k in keys:
        v = mapping[k]
        out[k] = _shuffled_mapping(v, rng) if finalize._is_group(v) else v
    return out


def _shuffle_entry(entry, rng):
    """Spreads and readings come in a new order; measured and sourced values are facts and keep theirs."""
    tokens = entry.get("tokens")
    if isinstance(tokens, dict) and tokens.get("status") not in ("measured", "sourced"):
        for v in tokens.values():
            if isinstance(v, list):
                rng.shuffle(v)
    if isinstance(entry.get("readings"), list):
        rng.shuffle(entry["readings"])


def _hand_file(dealt, src, out):
    """Serialize the hand with its routes, head and stats measured on the hand itself, reading steps that name the copy."""
    text, spans = finalize.serialize(dealt)
    for _ in range(5):
        finalize._measure(dealt, spans)
        man = dealt["manifest"]
        man["deal"] = ("This is your hand, dealt from %s: the user's words and don'ts, every tier-1 entry and the review "
                       "questions, plus a random half of everything else, the dump's own worn paths included, in a fresh "
                       "order (ADRs 0015, 0016). Build from what's here. "
                       "The rest of the deck stays in that file for looking up one specific thing, and write-backs go there." % src)
        steps = finalize._how_to_read(out, man["head_lines"])[1:]   # no second deal
        man["how_to_read"] = ["%d. %s" % (i, step.split(". ", 1)[1]) for i, step in enumerate(steps, 1)]
        man["stats"]["tokens"] = (len(text.encode("utf-8")) + 3) // 4
        new_text, spans = finalize.serialize(dealt)
        if new_text == text:
            break
        text = new_text
    return text


def _hand_text(hand, out_path):
    lines = ["Your hand (dealt at random, so every session works from a different part of the dump):"]
    start = hand.get("start_angle")
    if start:
        lines.append("- Start from the angle \"%s\": %s" % (start.get("angle"), start.get("text", "")))
    for cut in hand.get("deep_cuts", []):
        lines.append("- A deep cut to play with: %s (%s): %s" % (cut.get("term"), cut.get("ptr"), cut.get("text") or ""))
    lines.append("Nothing here is a rule: take it further, combine it, or go somewhere else entirely.")
    lines.append("For the rest of this session, work from the dealt copy: your hand, part of the deck in a fresh order:")
    lines.append(out_path)
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deal a meta dump: a fresh random order and a random place to start.")
    ap.add_argument("dump")
    ap.add_argument("--out", help="where to write the dealt copy (default: a temp file)")
    ap.add_argument("--seed", type=int, help="repeatable deal, for tests")
    args = ap.parse_args(argv)
    with open(args.dump, encoding="utf-8") as f:
        dump = json.load(f)
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    dealt, hand = deal(dump, rng)
    out = args.out
    if not out:
        fd, out = tempfile.mkstemp(prefix="dealt-", suffix=".metadump.json")
        os.close(fd)
    with open(out, "w", encoding="utf-8") as f:
        f.write(_hand_file(dealt, os.path.abspath(args.dump), out))
    print(_hand_text(hand, out))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Deal a meta dump: a hand of its material in a fresh order for this session, and a place to start that other
sessions didn't get.

A model reading a dump top to bottom starts from whatever comes first, so every session that reads the same dump
converges on its first angle, its first values and its first palette (tests 12 and 13). Dealing moves that choice
out of the model (ADR 0014): real randomness reorders the dump's lists and sections and picks a starting angle and
a few deep cuts, so each session explores a different corner of the same dump. Since test 14 showed order alone is not enough, the
hand also holds only part of the deck (ADR 0015): the request, tier 1, worn paths and review questions, plus half of
the rest. Independent draws still collided: in tests 18 and 19 three of four sessions were dealt the same angle in
four of six tasks, and built the same thing. So deals rotate (ADR 0019): a ledger beside the dump counts what earlier
hands held, and each deal takes what has been dealt least. Angles go in the dump's own order, so the first session
starts from the home angle, the kind of the thing a stranger pictures (test 21). The dump file itself is never changed.

Usage: python3 deal.py <dump.json> [--out <dealt copy path>] [--ledger PATH | --no-ledger] [--seed N]
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
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finalize  # noqa: E402


DEEP_CUTS = 2   # outer-tier entries the hand puts on top: the less obvious material a session starts beside
SHARE = 0.5     # of each task section's entries dealt into a hand (ADR 0015); the deck itself stays whole


def deal(dump, rng, ledger=None):
    """Return (dealt dump, hand). The dealt dump holds exactly the same entries at the same pointers.
    `ledger` is the dump's record of what its earlier hands held (a dict, updated in place). With one, deals rotate:
    each draw takes what has been dealt least, so sessions sharing a dump start from different angles (ADR 0019)."""
    dealt = copy.deepcopy(dump)
    hand = {}
    essence = dealt.get("essence") or {}
    angles = essence.get("angles")
    if isinstance(angles, list) and angles:
        counts, in_dump_order = _counts(ledger, "angles"), list(angles)
        rng.shuffle(angles)
        if counts is None:
            hand["start_angle"] = angles[_draw(range(len(angles)), 1, rng, None)[0]]
        else:   # least dealt first, and among equals the dump's own order: its first angle is the home angle
            start = min(in_dump_order, key=lambda a: counts.get(_angle_name(a), 0))
            counts[_angle_name(start)] = counts.get(_angle_name(start), 0) + 1
            hand["start_angle"] = start
    if isinstance(essence.get("readings"), list):
        rng.shuffle(essence["readings"])
    for name in [k for k in dealt if k not in finalize.SPINE_KEYS and k not in finalize.LOOKUP_KEYS]:
        if isinstance(dealt[name], dict):
            dealt[name] = _shuffled_mapping(dealt[name], rng)
    _deal_hand(dealt, rng, ledger)
    outer = []
    for _eid, ptr, entry, _h in finalize.iter_entries(dealt):
        _shuffle_entry(entry, rng)
        in_task_section = ptr.split("/")[1] not in finalize.SPINE_KEYS   # not a worn path, review question or open question
        if entry.get("tier") in (3, 4) and in_task_section and entry.get("text"):   # a deep cut needs something to play with
            outer.append({"ptr": ptr, "term": entry.get("term"), "text": entry.get("text")})
    hand["deep_cuts"] = _draw(outer, min(DEEP_CUTS, len(outer)), rng, _counts(ledger, "deep_cuts"), key=lambda c: c["ptr"])
    if ledger is not None:
        ledger["deals"] = ledger.get("deals", 0) + 1
    return dealt, hand


def _counts(ledger, pool):
    """The ledger's tally for one pool (angles, entries, worn paths, deep cuts), or None when deals are independent."""
    return None if ledger is None else ledger.setdefault(pool, {})


def _draw(pool, n, rng, counts, key=str):
    """`n` items of `pool`. With a tally, the least-dealt come first and ties break at random, so everything in the
    pool is dealt once before anything is dealt twice; without one, a plain random sample."""
    pool = list(pool)
    if counts is None:
        return rng.sample(pool, n)
    rng.shuffle(pool)
    pool.sort(key=lambda item: counts.get(key(item), 0))   # a stable sort keeps the shuffle as the tie-break
    drawn = pool[:n]
    for item in drawn:
        counts[key(item)] = counts.get(key(item), 0) + 1
    return drawn


def _angle_name(angle):
    return str(angle.get("angle") or angle.get("text") or "") if isinstance(angle, dict) else str(angle)


def _deal_hand(dealt, rng, ledger=None):
    """Leave out a share of each task section's entries (ADR 0015): every session works from a different hand.
    With a ledger the share kept is the least-dealt one, so the next hand holds what this one left out (ADR 0019)."""
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
        kept = set(_draw(ptrs, keep, rng, _counts(ledger, "entries")))
        for ptr in ptrs:
            if ptr not in kept:
                _remove(dealt, ptr)
    for section in by_section:
        _drop_empty_groups(dealt[_unescape(section)])
    _deal_worn_paths(dealt, rng, ledger)
    _point_at_the_hand(dealt)


def _deal_worn_paths(dealt, rng, ledger=None):
    """The build's own worn paths are dealt like the rest, so a hand's share of avoid-lists stays the dump's (ADR 0016).
    The user's own don'ts and the senses a word doesn't mean are in every hand."""
    worn = dealt.get("anti_keywords")
    if not isinstance(worn, dict):
        return
    dealable = [k for k, ak in worn.items() if isinstance(ak, dict) and ak.get("kind") == "not_wanted"
                and ak.get("prov") != "user_stated" and ak.get("tier") != 1]
    keep = min(len(dealable), max(1, math.ceil(len(dealable) * SHARE)))
    kept = set(_draw(dealable, keep, rng, _counts(ledger, "worn")))
    for key in dealable:
        if key not in kept:
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


def _hand_file(dealt, src, out, rotating=False):
    """Serialize the hand with its routes, head and stats measured on the hand itself, reading steps that name the copy."""
    text, spans = finalize.serialize(dealt)
    half = ("the half of everything else that earlier hands from this dump held least" if rotating
            else "a random half of everything else")
    for _ in range(5):
        finalize._measure(dealt, spans)
        man = dealt["manifest"]
        man["deal"] = ("This is your hand, dealt from %s: the user's words and don'ts, every tier-1 entry and the review "
                       "questions, plus %s, the dump's own worn paths included, in a fresh "
                       "order (ADRs 0015, 0016, 0019). Build from what's here. "
                       "The rest of the deck stays in that file for looking up one specific thing, and write-backs go there." % (src, half))
        steps = finalize._how_to_read(out, man["head_lines"])[1:]   # no second deal
        man["how_to_read"] = ["%d. %s" % (i, step.split(". ", 1)[1]) for i, step in enumerate(steps, 1)]
        man["stats"]["tokens"] = (len(text.encode("utf-8")) + 3) // 4
        new_text, spans = finalize.serialize(dealt)
        if new_text == text:
            break
        text = new_text
    return text


def _hand_text(hand, out_path, ledger=None):
    if ledger:
        lines = ["Your hand (deal %d from this dump; deals rotate, so each session starts where the others didn't):"
                 % ledger.get("deals", 1)]
    else:
        lines = ["Your hand (dealt at random, so every session works from a different part of the dump):"]
    start = hand.get("start_angle")
    if start:
        lines.append("- Start from the angle \"%s\": %s" % (start.get("angle"), start.get("text", "")))
    for cut in hand.get("deep_cuts", []):
        lines.append("- A deep cut to play with: %s (%s): %s" % (cut.get("term"), cut.get("ptr"), cut.get("text") or ""))
    if ledger and start:
        lines.append("Other sessions start from the dump's other angles. An angle is a kind of the thing, and says which one "
                     "you're making; what the user asked for, and how much of it, stays as they wrote it.")
    lines.append("Nothing here is a rule: take it further, combine it, or go somewhere else entirely.")
    lines.append("For the rest of this session, work from the dealt copy: your hand, part of the deck in a fresh order:")
    lines.append(out_path)
    return "\n".join(lines)


LEDGER_SCHEMA = "metadump-deals/1"


ledger_path = finalize.ledger_path


def _read_ledger(path):
    try:
        with open(path, encoding="utf-8") as f:
            ledger = json.load(f)
    except (OSError, ValueError):
        return {}
    return ledger if isinstance(ledger, dict) and ledger.get("schema") == LEDGER_SCHEMA else {}


def _write_ledger(path, ledger):
    ledger["schema"] = LEDGER_SCHEMA
    tmp = "%s.%d.tmp" % (path, os.getpid())
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=1, sort_keys=True)
    os.replace(tmp, path)


LOCK_WAIT = 10.0    # seconds a deal waits for another session's deal to finish before dealing independently
LOCK_STALE = 30.0   # a lock older than this was left by a session that died mid-deal


class _LedgerLock(object):
    """One deal at a time per ledger, so sessions started together still get different hands. A lock file made
    with O_EXCL works on every platform the skill runs on, with no extra modules."""

    def __init__(self, ledger):
        self.path = ledger + ".lock"

    def __enter__(self):
        deadline = time.monotonic() + LOCK_WAIT
        while True:
            try:
                os.close(os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
                return self
            except FileExistsError:
                try:
                    if time.time() - os.path.getmtime(self.path) > LOCK_STALE:
                        os.remove(self.path)
                        continue
                except OSError:
                    continue                       # released between the two calls: try again
                if time.monotonic() > deadline:
                    raise TimeoutError("another session has held %s for %d seconds" % (self.path, LOCK_WAIT))
                time.sleep(0.05)

    def __exit__(self, *exc):
        try:
            os.remove(self.path)
        except OSError:
            pass


def deal_with_ledger(dump, rng, path):
    """Deal against the ledger file at `path`, creating it if needed. Returns (dealt, hand, ledger)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _LedgerLock(path):
        ledger = _read_ledger(path)
        dealt, hand = deal(dump, rng, ledger)
        _write_ledger(path, ledger)
    return dealt, hand, ledger


def _quick_text(dump):
    """What a session is told about a quick dump: there is nothing to deal, and which kind to build."""
    tokens = len(json.dumps(dump, ensure_ascii=False)) // 4
    lines = ["This is a quick dump, written in one pass (about %d tokens). There is nothing to deal: read the whole file." % tokens]
    kinds = finalize.quick_kinds(dump)
    built = [str(b) for b in dump.get("built") or []]
    left = [k for k in kinds if k[0] not in built]       # the dump's own order: its first kind is the classic one
    if left:
        name, what = left[0]
        lines.append('Build the kind "%s"%s' % (name, ": " + what if what else ""))
    elif kinds:
        lines.append("Every kind in the dump has been built. Add a new kind to it and build that, or build one again differently.")
    if built:
        lines.append("Already built: %s." % ", ".join(built))
    lines.append("Then follow references/quick.md from step 2: build, ask the dump's checks, look, and add the kind you built to `built`.")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deal a meta dump: a hand of its material and a place to start, "
                                             "rotating so sessions that share a dump start in different places.")
    ap.add_argument("dump")
    ap.add_argument("--out", help="where to write the dealt copy (default: a temp file)")
    ap.add_argument("--seed", type=int, help="repeatable deal, for tests; keeps no ledger unless --ledger names one")
    ap.add_argument("--ledger", help="the deal ledger to rotate against (default: .deals/<slug>.deals.json beside the dump)")
    ap.add_argument("--no-ledger", action="store_true", help="deal independently of every other session and write no ledger")
    args = ap.parse_args(argv)
    with open(args.dump, encoding="utf-8") as f:
        dump = json.load(f)
    if finalize.is_quick(dump):
        print(_quick_text(dump))
        return 0
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    path = None if args.no_ledger else args.ledger or (ledger_path(args.dump) if args.seed is None else None)
    ledger = None
    if path:
        try:
            dealt, hand, ledger = deal_with_ledger(dump, rng, path)
        except OSError:
            path = None   # a read-only folder: deal independently, as before 0.13
    if not path:
        dealt, hand = deal(dump, rng)
    out = args.out
    if not out:
        fd, out = tempfile.mkstemp(prefix="dealt-", suffix=".metadump.json")
        os.close(fd)
    with open(out, "w", encoding="utf-8") as f:
        f.write(_hand_file(dealt, os.path.abspath(args.dump), out, rotating=bool(path)))
    print(_hand_text(hand, out, ledger if path else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())

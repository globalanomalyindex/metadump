#!/usr/bin/env python3
"""Build-time finisher for meta dumps.

Consumers never run this. Create mode (and use-mode write-back) runs it to turn
shards or an edited dump into a valid, self-indexing *.metadump.json.
Standard library only; Python 3.9+.
"""
import argparse
import copy
import json
import os
import re
import sys

SPINE_KEYS = ["manifest", "essence", "routing", "exports", "anti_keywords", "checks", "open_questions"]
LOOKUP_KEYS = ["index", "sources"]
SCHEMA = "metadump/1"

# Strongest first. `unknown` is never asserted as fact.
PROV_RANK = {
    "user_stated": 5,
    "reference_observed": 4,
    "researched": 3,
    "inferred": 2,
    "proposed": 1,
    "unknown": 0,
}
TIERS = (1, 2, 3, 4)
TIER1_CAP = 12
MANIFEST_REQUIRED = ["schema", "slug", "version", "created", "prompt"]
# Which source kinds can back which provenance. Video and image sources back either one: a video or image
# the user supplied is reference_observed, one found on the web is researched (sources say which in `origin`).
PROV_SOURCE_KINDS = {
    "researched": {"web", "doc", "video", "image"},
    "reference_observed": {"reference", "dump", "video", "image"},
}
MEDIA_SOURCE_KINDS = {"video", "image"}
# How an entry was obtained. Free-ish: unknown values only warn.
METHODS = {"scraped", "transcribed", "frame-diff", "pixel-sample", "visual", "measured", "researched-doc"}
ANTI_KINDS = ("not_meant", "not_wanted")


def _new_report():
    return {"errors": [], "warnings": [], "fixes": []}


def _note(report, bucket, code, path, msg):
    report[bucket].append({"code": code, "path": path, "msg": msg})


def _norm(text):
    return " ".join(str(text).lower().split())


def resolve(doc, ptr):
    """Resolve an RFC 6901 JSON Pointer. Returns (found, value)."""
    if ptr == "":
        return True, doc
    if not isinstance(ptr, str) or not ptr.startswith("/"):
        return False, None
    cur = doc
    for tok in ptr[1:].split("/"):
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and tok in cur:
            cur = cur[tok]
        elif isinstance(cur, list) and tok.isdigit() and int(tok) < len(cur):
            cur = cur[int(tok)]
        else:
            return False, None
    return True, cur


def _is_group(value):
    return (isinstance(value, dict) and value and "tier" not in value and "prov" not in value
            and all(isinstance(v, dict) and v for v in value.values()))


def iter_entries(dump, report=None):
    """Yield (id, pointer, entry, holder) for every knowledge entry.

    Holders are task sections plus anti_keywords and open_questions. Inside a task
    section, a dict with no tier/prov whose members are all dicts is a group and
    is walked; keys starting with "_" are section notes, not entries.
    """
    holders = [k for k in dump if k not in SPINE_KEYS and k not in LOOKUP_KEYS]
    holders += ["anti_keywords", "open_questions"]

    def walk(container, ptr, holder, top):
        for key, val in container.items():
            p = ptr + "/" + _esc(key)
            if str(key).startswith("_"):
                continue
            if top and holder in ("anti_keywords", "open_questions"):
                if isinstance(val, dict):
                    yield key, p, val, holder
                continue
            if _is_group(val):
                for item in walk(val, p, holder, False):
                    yield item
            elif isinstance(val, dict):
                yield key, p, val, holder
            elif report is not None:
                _note(report, "warnings", "loose_value", p, "non-entry value in a section; prefix the key with '_' if it is a note")

    for holder in holders:
        val = dump.get(holder)
        if isinstance(val, dict):
            for item in walk(val, "/" + _esc(holder), holder, True):
                yield item


def _source_kinds(entry, sources):
    return {sources[s].get("kind") for s in entry.get("src", []) or [] if isinstance(sources.get(s), dict)}


def _web_found_media_only(entry, sources):
    """True when every source that could back reference_observed is a video/image the build found on the web."""
    backing = [sources[s] for s in entry.get("src", []) or []
               if isinstance(sources.get(s), dict) and sources[s].get("kind") in PROV_SOURCE_KINDS["reference_observed"]]
    return bool(backing) and all(b.get("kind") in MEDIA_SOURCE_KINDS and b.get("origin") == "web" for b in backing)


def _in_prompt(text, prompt):
    t = _norm(text)
    return bool(t) and t in _norm(prompt)


def _valid_anchor(anchor, prompt, sources):
    if not isinstance(anchor, str) or not anchor.strip():
        return False
    return anchor in sources or _in_prompt(anchor, prompt)


def _validate_entries(out, report):
    prompt = out["manifest"].get("prompt", "") or ""
    sources = out["sources"]
    seen = {}
    tier1 = []
    for eid, ptr, entry, holder in list(iter_entries(out, report)):
        if eid in seen:
            _note(report, "errors", "duplicate_id", ptr, "id '%s' already used at %s" % (eid, seen[eid]))
        seen[eid] = ptr
        if holder == "open_questions":
            entry.setdefault("prov", "unknown")
            entry.setdefault("tier", 3)
        if entry.get("tier") not in TIERS:
            _note(report, "errors", "bad_tier", ptr, "tier must be one of 1-4")
            continue
        if entry.get("prov") not in PROV_RANK:
            _note(report, "errors", "bad_prov", ptr, "prov must be one of %s" % ", ".join(PROV_RANK))
            continue
        for s in entry.get("src", []) or []:
            if s not in sources:
                _note(report, "errors", "missing_source", ptr, "src '%s' is not in sources" % s)
        prov = entry["prov"]
        # Provenance must be earned by its evidence.
        needed = PROV_SOURCE_KINDS.get(prov)
        if needed and not (_source_kinds(entry, sources) & needed):
            entry["prov"] = "inferred"
            _note(report, "fixes", "prov_needs_source", ptr,
                  "%s needs a src of kind %s; demoted to inferred" % (prov, "/".join(sorted(needed))))
        if entry["prov"] == "reference_observed" and _web_found_media_only(entry, sources):
            entry["prov"] = "researched"
            _note(report, "fixes", "prov_origin_mismatch", ptr,
                  "reference_observed needs a user-supplied source; its video/image sources have origin 'web'; set to researched")
        method = entry.get("method")
        # Token-like values are provenance methods; older dumps used `method` for free-text procedures, left alone.
        if isinstance(method, str) and method not in METHODS and re.match(r"^[A-Za-z][\w.-]*$", method):
            _note(report, "warnings", "unknown_method", ptr,
                  "method '%s' is not one of %s (kept as is)" % (method, ", ".join(sorted(METHODS))))
        if entry["prov"] == "user_stated":
            inherited_ok = entry.get("inherited") and "dump" in _source_kinds(entry, sources)
            if not (_in_prompt(entry.get("anchor", ""), prompt) or entry.get("decided_in") or inherited_ok):
                entry["prov"] = "inferred"
                _note(report, "fixes", "user_stated_needs_prompt_anchor", ptr,
                      "user_stated needs an anchor quoting the prompt (or decided_in); demoted to inferred")
        if entry["tier"] == 1:
            if entry["prov"] == "proposed":
                entry["tier"] = 2
                _note(report, "fixes", "proposed_not_tier1", ptr, "proposed entries are never tier 1; set to tier 2")
            elif not _valid_anchor(entry.get("anchor"), prompt, sources):
                entry["tier"] = 2
                _note(report, "fixes", "tier1_needs_anchor", ptr,
                      "tier 1 needs an anchor quoting the prompt or naming a source; set to tier 2")
            else:
                tier1.append(eid)
        if holder == "anti_keywords":
            _validate_anti_keyword(entry, ptr, report)
    if len(tier1) > TIER1_CAP:
        _note(report, "warnings", "tier1_over_cap", "",
              "%d tier-1 entries (cap %d): too many to read as the most relevant; demote the least defining" % (len(tier1), TIER1_CAP))
    return seen


def _validate_anti_keyword(ak, ptr, report):
    if ak.get("kind") not in ANTI_KINDS:
        _note(report, "errors", "bad_anti_keyword_kind", ptr, "kind must be not_meant or not_wanted")
        return
    if not isinstance(ak.get("term"), str) or not ak["term"].strip():
        _note(report, "errors", "anti_keyword_needs_term", ptr, "anti-keyword needs a term")
    scope = ak.get("scope", ["*"])
    if isinstance(scope, str):
        scope = [scope]
    ak["scope"] = scope
    if not ak.get("instead"):
        if ak["kind"] == "not_wanted" and ak.get("class") != "noise" and scope != ["search"]:
            _note(report, "errors", "not_wanted_needs_instead", ptr,
                  "not_wanted needs an 'instead' (models without negative prompts can only express the rewrite)")
        elif ak["kind"] == "not_meant":
            _note(report, "warnings", "not_meant_needs_instead", ptr, "not_meant should say which sense is meant")


def _validate_spine(out, report):
    man = out["manifest"]
    for field in MANIFEST_REQUIRED:
        if field not in man or man[field] in (None, ""):
            _note(report, "errors", "manifest_field_missing", "/manifest/" + field, "manifest needs '%s'" % field)
    if man.get("schema") not in (None, SCHEMA):
        _note(report, "warnings", "schema_mismatch", "/manifest/schema", "expected %s" % SCHEMA)
    if not isinstance(man.get("version", 1), int):
        _note(report, "errors", "manifest_field_missing", "/manifest/version", "version must be an integer")
    if not out["essence"].get("one_sentence"):
        _note(report, "errors", "essence_field_missing", "/essence/one_sentence", "essence needs one_sentence")
    if not isinstance(out["routing"], list):
        _note(report, "errors", "bad_routing", "/routing", "routing must be a list of routes")
        out["routing"] = []
    for i, route in enumerate(out["routing"]):
        if not isinstance(route, dict) or not route.get("job") or not route.get("paths"):
            _note(report, "errors", "bad_routing", "/routing/%d" % i, "each route needs job and paths")


def _validate_refs(out, ids, report):
    for cid, check in (out["checks"] or {}).items():
        for ref in check.get("from", []) or []:
            if ref not in ids:
                _note(report, "errors", "unknown_id", "/checks/" + _esc(cid), "from cites unknown id '%s'" % ref)
    for ref in out["essence"].get("signature", []) or []:
        if ref not in ids:
            _note(report, "errors", "unknown_id", "/essence/signature", "signature cites unknown id '%s'" % ref)
    version = out["manifest"].get("version")

    def walk_exports(node, ptr):
        if not isinstance(node, dict):
            return
        if "compiled_from_version" in node:
            if node["compiled_from_version"] != version:
                _note(report, "warnings", "stale_export", ptr,
                      "compiled from v%s but dump is v%s; recompile" % (node["compiled_from_version"], version))
            for ref in node.get("from", []) or []:
                if ref not in ids:
                    _note(report, "errors", "unknown_id", ptr, "export cites unknown id '%s'" % ref)
            return
        for k, v in node.items():
            walk_exports(v, ptr + "/" + _esc(k))

    walk_exports(out["exports"], "/exports")


def _validate_routes(out, sections, report):
    reached = set()
    for i, route in enumerate(out["routing"]):
        for p in route.get("paths", []) or []:
            found, _ = resolve(out, p)
            if not found:
                _note(report, "errors", "unresolved_route_path", "/routing/%d" % i, "path '%s' does not resolve" % p)
            for s in sections:
                if p == "/" + _esc(s) or p.startswith("/" + _esc(s) + "/"):
                    reached.add(s)
    for s in sections:
        if s not in reached:
            _note(report, "warnings", "unrouted_section", "/" + _esc(s),
                  "no route reaches this section; route it or drop it (survival rule)")


TERM_FIELDS = ("term", "name", "canonical", "label")
STOPWORDS = {"a", "an", "and", "or", "the", "of", "in", "on", "at", "to", "for", "with", "without", "by", "from",
             "into", "onto", "over", "under", "as", "is", "are", "be", "not", "no", "its", "it", "this", "that",
             "vs", "via", "per", "than", "then", "yet"}
WORD_MAX_ENTRIES = 25


def _words(text):
    """Searchable words of a phrase: lowercased, no stopwords, plus a naive singular for plurals."""
    for w in re.findall(r"[a-z0-9][a-z0-9'+-]*", _norm(text)):
        w = w.strip("'-+")
        if len(w) < 2 or w in STOPWORDS or w.isdigit():
            continue
        yield w
        if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
            yield w[:-1]
TERM_LIST_FIELDS = ("aliases", "variants", "keywords")
SLICE_CAP_TOKENS = 8000


def _build_index(out):
    """Search index: lowercased term, alias, variant or word -> JSON Pointers ranked by tier.

    index[key] = {"hits": [exact phrase matches], "words": [entries containing the word],
                  "not_meant": [anti-keyword ids for senses to avoid]}
    """
    phrase, words, not_meant = {}, {}, {}
    order = {}

    def add(bucket, key, tier, ptr):
        if key:
            order.setdefault(key, len(order))
            lst = bucket.setdefault(key, [])
            if ptr not in [p for _t, _n, p in lst]:
                lst.append((tier if isinstance(tier, int) else 9, len(lst), ptr))

    for eid, ptr, entry, holder in iter_entries(out):
        tier = entry.get("tier")
        variants = [v for f in TERM_LIST_FIELDS for v in (entry.get(f) or []) if isinstance(v, str)]
        if holder == "anti_keywords" and entry.get("kind") == "not_meant":
            key = _norm(entry.get("term", ""))
            if key:
                order.setdefault(key, len(order))
                if eid not in not_meant.setdefault(key, []):
                    not_meant[key].append(eid)
            for v in variants:
                add(phrase, _norm(v), tier, ptr)
            continue
        terms = [entry[f] for f in TERM_FIELDS if isinstance(entry.get(f), str)] + variants
        for t in terms:
            add(phrase, _norm(t), tier, ptr)
        for w in {w for t in terms for w in _words(t)}:
            add(words, w, tier, ptr)

    idx = {}
    for key in sorted(order):
        hits = [p for _t, _n, p in sorted(phrase.get(key, []))]
        rec = {"hits": hits}
        word_list = words.get(key, [])
        if 0 < len(word_list) <= WORD_MAX_ENTRIES:  # too-common words don't discriminate (no idf)
            w = [p for _t, _n, p in sorted(word_list) if p not in hits]
            if w:
                rec["words"] = w
        if key in not_meant:
            rec["not_meant"] = not_meant[key]
        if len(rec) > 1 or hits:
            idx[key] = rec
    return idx


def _tokens(value):
    """Rough token estimate (bytes / 4) of a slice as a consumer would receive it."""
    return (len(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")) + 3) // 4


def _jq_expr(doc, ptr):
    cur = doc
    expr = ""
    for tok in ptr[1:].split("/") if ptr else []:
        tok = tok.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            expr += "[%s]" % tok
            cur = cur[int(tok)]
        else:
            expr += "[%s]" % json.dumps(tok, ensure_ascii=False)
            cur = cur[tok]
    return "." + expr if expr else "."


def _stats(out):
    by_tier, by_prov, by_section = {}, {}, {}
    n = 0
    for _eid, _ptr, entry, holder in iter_entries(out):
        n += 1
        t = str(entry.get("tier"))
        by_tier[t] = by_tier.get(t, 0) + 1
        p = entry.get("prov")
        by_prov[p] = by_prov.get(p, 0) + 1
        by_section[holder] = by_section.get(holder, 0) + 1
    return {
        "entries": n,
        "by_tier": dict(sorted(by_tier.items())),
        "by_prov": dict(sorted(by_prov.items())),
        "by_section": by_section,
    }


def _how_to_read(fname, head_lines):
    return [
        "1. Read the head first: the first %d lines hold manifest, essence and routing (Read limit=%d, or jq '{manifest, essence, routing}' %s)." % (head_lines, head_lines, fname),
        "2. Pick the route for your job and run its jq: jq '<routing[i].jq>' %s" % fname,
        "3. Also pull the anti-keywords and review prompts (checks) for your scope: jq '.anti_keywords, .checks' %s" % fname,
        "4. Look up any term (lowercase): jq '.index[\"<term>\"]' %s  -> hits give id + path; not_meant lists senses to avoid." % fname,
        "5. Grep works too: every entry is one line, so grep -n '<word>' %s returns whole entries." % fname,
    ]


def _measure(out, spans):
    """Fill route jq/tokens/lines and manifest head/how_to_read/stats. Returns True if anything changed."""
    before = json.dumps([out["routing"], out["manifest"]], sort_keys=True)
    for route in out["routing"]:
        paths = [p for p in route.get("paths", []) if resolve(out, p)[0]]
        route["jq"] = ", ".join(_jq_expr(out, p) for p in paths)
        route["tokens"] = sum(_tokens(resolve(out, p)[1]) for p in paths)
        route["lines"] = [list(spans[p]) for p in paths if p in spans]
    man = out["manifest"]
    head = spans.get("/routing", (0, 0))[1]
    man["head_lines"] = head
    man["how_to_read"] = _how_to_read("%s.metadump.json" % man.get("slug", "dump"), head)
    stats = _stats(out)
    stats["tokens"] = man.get("stats", {}).get("tokens", 0)
    man["stats"] = stats
    return json.dumps([out["routing"], out["manifest"]], sort_keys=True) != before


def finish(dump):
    """build_dump + measure + serialize. Returns (text, finished_dump, report)."""
    out, report = build_dump(dump)
    text, spans = serialize(out)
    if report["errors"]:
        return text, out, report
    for _ in range(5):
        changed = _measure(out, spans)
        text, spans = serialize(out)
        total = (len(text.encode("utf-8")) + 3) // 4
        if out["manifest"]["stats"].get("tokens") != total:
            out["manifest"]["stats"]["tokens"] = total
            changed = True
            text, spans = serialize(out)
        if not changed:
            break
    for i, route in enumerate(out["routing"]):
        if route.get("tokens", 0) > SLICE_CAP_TOKENS:
            _note(report, "warnings", "route_over_cap", "/routing/%d" % i,
                  "route '%s' costs ~%d tokens (cap %d); split it into narrower routes" % (route.get("job"), route["tokens"], SLICE_CAP_TOKENS))
    return text, out, report


# ---------------------------------------------------------------- shards

_DERIVED_ONLY = {"inferred", "proposed", "unknown"}
# The strongest provenance each ticket type may mint. A specialist can reason
# (inferred/proposed) but cannot claim it read a page or heard the user.
TICKET_PROVS = {
    "prompt": _DERIVED_ONLY | {"user_stated"},
    "observe": _DERIVED_ONLY | {"reference_observed"},
    "research": _DERIVED_ONLY | {"researched"},
    # Evidence from pages, videos and images: researched when found on the web, reference_observed when the user supplied it.
    "scrape": _DERIVED_ONLY | {"researched", "reference_observed"},
    "watch": _DERIVED_ONLY | {"researched", "reference_observed"},
    "moodboard": _DERIVED_ONLY | {"researched", "reference_observed"},
    "specialist": _DERIVED_ONLY,
    "lexicon": _DERIVED_ONLY,
    "exclusion": _DERIVED_ONLY,
    "normalize": _DERIVED_ONLY,
    "synthesis": _DERIVED_ONLY,
    "audit": _DERIVED_ONLY,
    "inherit": set(PROV_RANK),
}
EDITOR_TYPES = {"normalize", "synthesis", "audit"}
UNION_FIELDS = ("aliases", "variants", "keywords", "src")
FLAT_HOLDERS = ("anti_keywords", "open_questions")


def _cap_prov(prov, allowed):
    if prov in allowed or prov not in PROV_RANK:
        return prov
    rank = PROV_RANK[prov]
    candidates = [p for p in allowed if PROV_RANK[p] <= rank]
    return max(candidates, key=PROV_RANK.get) if candidates else "unknown"


def _flatten(container, flat, gpath=()):
    for key, val in container.items():
        if str(key).startswith("_") or not isinstance(val, dict):
            continue
        if flat or "tier" in val or "prov" in val or val.get("_delete") or not _is_group(val):
            yield gpath, key, val
        else:
            for item in _flatten(val, flat, gpath + (key,)):
                yield item


def _rank_key(e):
    return (PROV_RANK.get(e.get("prov"), 0), -(e.get("tier") or 9))


def _load_json(path, report, code):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        _note(report, "errors", code, path, str(exc))
        return None


def merge_workdir(workdir):
    """Merge <workdir>/manifest.json and <workdir>/shards/*.json into a draft dump."""

    report = _new_report()
    man_path = os.path.join(workdir, "manifest.json")
    if os.path.exists(man_path):
        manifest = _load_json(man_path, report, "bad_manifest") or {}
    else:
        manifest = {}
        _note(report, "errors", "missing_manifest", man_path, "create mode writes manifest.json before fan-out")
    shard_dir = os.path.join(workdir, "shards")
    names = sorted(n for n in os.listdir(shard_dir) if n.endswith(".json")) if os.path.isdir(shard_dir) else []

    order = []          # task sections, first-seen order
    holders = {}        # holder -> {"notes": {}, "items": {id: (gpath, entry)}}
    where = {}          # id -> holder
    sources = {}
    spine = {}

    def holder_slot(name):
        if name not in holders:
            holders[name] = {"notes": {}, "items": {}}
            if name not in FLAT_HOLDERS:
                order.append(name)
        return holders[name]

    for name in names:
        shard = _load_json(os.path.join(shard_dir, name), report, "bad_shard")
        if not isinstance(shard, dict):
            continue
        ttype = (shard.get("ticket") or {}).get("type", "specialist")
        if ttype not in TICKET_PROVS:
            _note(report, "warnings", "unknown_ticket_type", name, "type '%s' treated as specialist" % ttype)
            ttype = "specialist"
        allowed = TICKET_PROVS[ttype]
        for sid, s in (shard.get("sources") or {}).items():
            if sid in sources and sources[sid] != s:
                _note(report, "warnings", "source_conflict", name, "source '%s' differs from an earlier shard; kept the first" % sid)
            sources.setdefault(sid, s)
        if ttype == "synthesis":
            for k, v in (shard.get("spine") or {}).items():
                if k in ("essence", "routing", "exports", "checks"):
                    spine[k] = v
        parts = list((shard.get("sections") or {}).items())
        parts += [(h, shard.get(h)) for h in FLAT_HOLDERS]
        for hname, content in parts:
            if not isinstance(content, dict):
                continue
            slot = holder_slot(hname)
            for k, v in content.items():
                if str(k).startswith("_") and hname not in FLAT_HOLDERS:
                    slot["notes"][k] = v
            for gpath, eid, raw in _flatten(content, hname in FLAT_HOLDERS):
                ptr = "%s:/%s/%s" % (name, hname, eid)
                e = {k: v for k, v in raw.items() if k not in ("_replace", "_delete")}
                is_editor = ttype in EDITOR_TYPES
                if raw.get("_delete"):
                    if is_editor and eid in where:
                        del holders[where.pop(eid)]["items"][eid]
                    elif not is_editor:
                        _note(report, "warnings", "delete_not_allowed", ptr, "only normalize/synthesis/audit shards may delete")
                    continue
                if ttype == "inherit":
                    e["inherited"] = True
                if raw.get("_replace") and is_editor and eid in where:
                    old_holder = where[eid]
                    old = holders[old_holder]["items"][eid][1]
                    if PROV_RANK.get(e.get("prov"), 0) > PROV_RANK.get(old.get("prov"), 0):
                        e["prov"] = old.get("prov")
                        _note(report, "fixes", "prov_upgrade_blocked", ptr, "a replace cannot raise provenance; kept '%s'" % old.get("prov"))
                    del holders[old_holder]["items"][eid]
                    slot["items"][eid] = (gpath, e)
                    where[eid] = hname
                    continue
                if "prov" in e:
                    capped = _cap_prov(e["prov"], allowed)
                    if capped != e["prov"]:
                        _note(report, "fixes", "prov_over_ceiling", ptr,
                              "%s ticket cannot mint '%s'; demoted to '%s'" % (ttype, e["prov"], capped))
                        e["prov"] = capped
                if eid in where:
                    old_holder = where[eid]
                    old_gpath, old = holders[old_holder]["items"][eid]
                    winner, loser = (e, old) if _rank_key(e) > _rank_key(old) else (old, e)
                    for f in UNION_FIELDS:
                        merged = list(winner.get(f) or [])
                        merged += [x for x in (loser.get(f) or []) if x not in merged]
                        if merged:
                            winner[f] = merged
                    holders[old_holder]["items"][eid] = (old_gpath, winner)
                    _note(report, "warnings", "merge_conflict", ptr, "id '%s' also in an earlier shard; kept the stronger entry" % eid)
                else:
                    slot["items"][eid] = (gpath, e)
                    where[eid] = hname

    def rebuild(hname):
        slot = holders.get(hname, {"notes": {}, "items": {}})
        d = dict(slot["notes"])
        for eid, (gpath, e) in slot["items"].items():
            node = d
            for g in gpath:
                node = node.setdefault(g, {})
            node[eid] = e
        return d

    draft = {"manifest": manifest}
    draft["essence"] = spine.get("essence", {})
    draft["routing"] = spine.get("routing", [])
    draft["exports"] = spine.get("exports", {})
    draft["anti_keywords"] = rebuild("anti_keywords")
    draft["checks"] = spine.get("checks", {})
    draft["open_questions"] = rebuild("open_questions")
    for hname in order:
        draft[hname] = rebuild(hname)
    draft["sources"] = sources
    return draft, report


AUTO_TIER1_JOB = "always first: the defining tier-1 entries"


def _add_tier1_route(out):
    """Tier 1 is what the task is most about, so it gets a route of its own, rebuilt on every build."""
    out["routing"] = [r for r in out["routing"] if not (isinstance(r, dict) and r.get("auto"))]
    paths = [ptr for _eid, ptr, entry, _h in iter_entries(out) if entry.get("tier") == 1]
    if paths:
        out["routing"].insert(0, {"job": AUTO_TIER1_JOB, "when": "pull first for any job: the most relevant entries (relevance, not rules)",
                                  "auto": True, "paths": paths})


def build_dump(dump):
    """Validate and finish a dump. Returns (finished_dump, report)."""
    src = copy.deepcopy(dump)
    report = _new_report()
    sections = [k for k in src if k not in SPINE_KEYS and k not in LOOKUP_KEYS]
    out = {}
    for k in SPINE_KEYS:
        default = [] if k == "routing" else {}
        out[k] = src.get(k) if src.get(k) is not None else default
    for k in sections:
        out[k] = src[k]
    out["index"] = {}
    out["sources"] = src.get("sources") or {}
    _validate_spine(out, report)
    ids = _validate_entries(out, report)
    _add_tier1_route(out)
    _validate_refs(out, ids, report)
    out["index"] = _build_index(out)
    _validate_routes(out, sections, report)
    return out, report


# ---------------------------------------------------------------- layout

def _esc(key):
    return str(key).replace("~", "~0").replace("/", "~1")


def _inline(value):
    return json.dumps(value, ensure_ascii=False, separators=(", ", ": "))


def _expands(value, depth):
    if depth == 0:
        return True
    if not isinstance(value, (dict, list)) or not value:
        return False
    if isinstance(value, list):
        return depth == 1 and all(isinstance(v, dict) for v in value)
    if depth == 1:
        return True
    # deeper dicts expand only when they are groups of entries/payloads
    return "tier" not in value and all(isinstance(v, dict) and v for v in value.values())


def serialize(dump):
    """One entry per line: containers indented, each entry minified on its own line.

    Returns (text, spans) where spans maps a JSON Pointer to its (first, last) 1-based line.
    """
    lines = []
    spans = {}

    def emit(s):
        lines.append(s)
        return len(lines)

    def write(value, ptr, depth, prefix, suffix):
        indent = "  " * depth
        if _expands(value, depth):
            if isinstance(value, dict):
                start = emit(prefix + "{")
                items = list(value.items())
                for i, (k, child) in enumerate(items):
                    write(child, ptr + "/" + _esc(k), depth + 1,
                          "  " * (depth + 1) + json.dumps(k, ensure_ascii=False) + ": ",
                          "," if i < len(items) - 1 else "")
                end = emit(indent + "}" + suffix)
            else:
                start = emit(prefix + "[")
                for i, child in enumerate(value):
                    write(child, ptr + "/" + str(i), depth + 1, "  " * (depth + 1),
                          "," if i < len(value) - 1 else "")
                end = emit(indent + "]" + suffix)
            spans[ptr] = (start, end)
        else:
            n = emit(prefix + _inline(value) + suffix)
            spans[ptr] = (n, n)

    write(dump, "", 0, "", "")
    return "\n".join(lines) + "\n", spans


# ---------------------------------------------------------------- CLI

def _summary(report, limit=12):
    lines = ["errors: %d  fixes: %d  warnings: %d" % (len(report["errors"]), len(report["fixes"]), len(report["warnings"]))]
    for bucket in ("errors", "fixes", "warnings"):
        items = report[bucket]
        for item in items[:limit]:
            lines.append("  %-8s %-32s %s  %s" % (bucket[:-1], item["code"], item["path"], item["msg"]))
        if len(items) > limit:
            lines.append("  ... %d more %s (see the full report)" % (len(items) - limit, bucket))
    return "\n".join(lines)


def _combine(*reports):
    out = _new_report()
    for r in reports:
        for k in out:
            out[k].extend(r[k])
    return out


def _write(path, text):
    tmp = "%s.tmp.%d" % (path, os.getpid())  # unique: parallel workers may merge at once
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="finalize.py", description="Build-time finisher for meta dumps (consumers never need it).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="merge a work dir (manifest.json + shards/) or re-finish an existing dump")
    b.add_argument("src", help="work dir metadumps/.work/<slug>/ or a *.metadump.json file")
    b.add_argument("-o", "--out", help="output path (default: metadumps/<slug>.metadump.json for a work dir; in place for a file)")
    b.add_argument("--bump", action="store_true", help="increment manifest.version (use-mode write-back)")
    b.add_argument("--report", help="write the full JSON report here (default: <work dir>/report.json for a work dir)")
    c = sub.add_parser("check", help="validate a finished dump without writing it")
    c.add_argument("dump")
    m = sub.add_parser("merge", help="merge a work dir into <work dir>/draft.json for normalizers and synthesis to read (no validation gate)")
    m.add_argument("workdir")
    args = ap.parse_args(argv)

    if args.cmd == "merge":
        draft, merge_report = merge_workdir(args.workdir)
        out, built = build_dump(draft)
        text, _spans = serialize(out)
        _write(os.path.join(args.workdir, "draft.json"), text)
        report = _combine(merge_report, built)
        stats = _stats(out)
        print(_summary(report))
        print("wrote %s  (%d entries; by section %s). Validation errors are expected until synthesis writes the spine." % (
            os.path.join(args.workdir, "draft.json"), stats["entries"], json.dumps(stats["by_section"])))
        return 1 if any(e["code"] in ("missing_manifest", "bad_manifest") for e in merge_report["errors"]) else 0

    if args.cmd == "check":
        report = _new_report()
        dump = _load_json(args.dump, report, "bad_json")
        if dump is None:
            print(_summary(report))
            return 1
        text, _out, built = finish(dump)
        report = _combine(report, built)
        with open(args.dump, encoding="utf-8") as f:
            if f.read() != text and not report["errors"]:
                _note(report, "warnings", "layout_stale", args.dump,
                      "file differs from the canonical layout/index/costs; run: finalize.py build %s" % args.dump)
        print(_summary(report))
        return 1 if report["errors"] else 0

    src = args.src
    if os.path.isdir(src):
        draft, merge_report = merge_workdir(src)
        slug = draft.get("manifest", {}).get("slug") or os.path.basename(os.path.normpath(src))
        out_path = args.out or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(src))), slug + ".metadump.json")
        report_path = args.report or os.path.join(src, "report.json")
    else:
        merge_report = _new_report()
        draft = _load_json(src, merge_report, "bad_json")
        out_path = args.out or src
        report_path = args.report
    if draft is None:
        print(_summary(merge_report))
        return 1
    if args.bump:
        man = draft.setdefault("manifest", {})
        man["version"] = int(man.get("version", 0) or 0) + 1
    text, out, built = finish(draft)
    report = _combine(merge_report, built)
    if report_path:
        _write(report_path, json.dumps(report, indent=1, ensure_ascii=False) + "\n")
    if report["errors"]:
        if os.path.isdir(src):
            _write(os.path.join(src, "draft.json"), text)
        print(_summary(report))
        print("NOT WRITTEN: fix the errors above, then rerun build.")
        return 1
    _write(out_path, text)
    stats = out["manifest"].get("stats", {})
    print(_summary(report))
    print("wrote %s  (v%s, %s entries, ~%s tokens, head = first %s lines)" % (
        out_path, out["manifest"].get("version"), stats.get("entries"), stats.get("tokens"), out["manifest"].get("head_lines")))
    return 0


if __name__ == "__main__":
    sys.exit(main())

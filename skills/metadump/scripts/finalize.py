#!/usr/bin/env python3
"""Build-time finisher for meta dumps.

Consumers never run this. Create mode (and use-mode write-back) runs it to turn
shards or an edited dump into a valid, self-indexing *.metadump.json.
Standard library only; Python 3.9+.
"""
import argparse
import copy
import json
import urllib.parse
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
# Words that turn the build's own thinking into a rule. The user's words and constraint mechanisms (invariants with
# their `variable`, forbidden shortcuts, anti-keywords) may narrow; the build's other entries seed.
NARROWING = re.compile(r"\b(must(?: not)?|never|always|nothing else|(?<!not )the only|no other)\b", re.I)
CONSTRAINT_KINDS = {"not_wanted", "not_meant", "forbidden_shortcut", "invariant", "budget"}


def _narrowing_word(entry):
    """The narrowing word in a derived, non-constraint entry's text, or None."""
    if entry.get("prov") not in ("inferred", "proposed") or "variable" in entry or entry.get("kind") in CONSTRAINT_KINDS:
        return None
    m = NARROWING.search(str(entry.get("text", "")))
    return m.group(0) if m else None
# A dump of 20+ entries where under a fifth was collected, or whose sources sit on fewer than 3 hosts,
# is mostly the build's own thinking or one page restated: say so.
LOW_GROUNDING_PARTS = 5
LOW_GROUNDING_MIN_ENTRIES = 20
MIN_SOURCE_HOSTS = 3
# A section of this many entries that all cite one single source is that source passed through whole.
UNDIGESTED_MIN_ENTRIES = 5
# What the build collected rather than thought up: the user's words, observed references, researched sources.
COLLECTED_PROVS = {"user_stated", "reference_observed", "researched"}
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
    """A dict with no tier/prov whose members are all dicts; "_"-prefixed notes (like `_about`) don't count."""
    if not isinstance(value, dict) or not value or "tier" in value or "prov" in value or "_delete" in value or "_replace" in value:
        return False   # entries and edit markers aren't groups
    members = [v for k, v in value.items() if not str(k).startswith("_")]
    return all(isinstance(v, dict) and v for v in members)   # a group of notes only (all options deleted) is still a group


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
            elif entry["prov"] not in COLLECTED_PROVS:
                entry["tier"] = 2
                _note(report, "fixes", "tier1_needs_collected", ptr,
                      "tier 1 holds only what was collected (user_stated, reference_observed, researched); "
                      "a derived '%s' entry is tier 2 at most, so the build's own thinking can't redefine the task" % entry["prov"])
            elif not _valid_anchor(entry.get("anchor"), prompt, sources):
                entry["tier"] = 2
                _note(report, "fixes", "tier1_needs_anchor", ptr,
                      "tier 1 needs an anchor quoting the prompt or naming a source; set to tier 2")
            else:
                tier1.append(eid)
        if holder == "anti_keywords":
            _validate_anti_keyword(entry, ptr, report)
        else:
            word = _narrowing_word(entry)
            if word:
                _note(report, "warnings", "narrowing_language", ptr,
                      "the build's own entry narrows the task ('%s'); say what it adds or offers instead, so it seeds the work rather than limiting it" % word)
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
    task = out["essence"].get("task") or {}
    if not (isinstance(task, dict) and task.get("disciplines") and len(task.get("ladder") or []) >= 2):
        _note(report, "warnings", "no_task_ladder", "/essence/task",
              "identify the task first: essence.task needs `is`, the `disciplines` it belongs to, and a `ladder` from those "
              "disciplines down to this task's specifics, so the dump carries what practitioners know, not just the artifact")
    elif len(task.get("job") or []) < 2:
        _note(report, "warnings", "no_task_job", "/essence/task/job",
              "list the user's whole job end to end in essence.task.job (shopping: find, compare, choose, add, review the bag, "
              "check out), so the default reading and every build can cover all of it")
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
    tier1 = {eid for eid, _p, e, _h in iter_entries(out) if e.get("tier") == 1}
    kept = []
    for ref in out["essence"].get("signature", []) or []:
        if ref not in ids:
            _note(report, "errors", "unknown_id", "/essence/signature", "signature cites unknown id '%s'" % ref)
        elif ref not in tier1:
            _note(report, "fixes", "signature_not_tier1", "/essence/signature",
                  "'%s' is not tier 1 (after validation); dropped from the signature, which every consumer reads first" % ref)
            continue
        kept.append(ref)
    if "signature" in out["essence"]:
        out["essence"]["signature"] = kept
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
TERM_LIST_FIELDS = ("aliases", "variants", "keywords")   # facet phrases (properties, descriptors, signals) are found by grep, not indexed: the index would double the file
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
    collected = sum(by_prov.get(p, 0) for p in COLLECTED_PROVS)
    unknown = by_prov.get("unknown", 0)
    return {
        "entries": n,
        "by_tier": dict(sorted(by_tier.items())),
        "by_prov": dict(sorted(by_prov.items(), key=lambda kv: str(kv[0]))),
        "by_section": by_section,
        "grounding": {"collected": collected, "derived": n - collected - unknown, "unknown": unknown,
                      "collected_share": round(collected / n, 2) if n else 0.0, "hosts": len(_source_hosts(out))},
    }


def _source_hosts(out):
    """Distinct hosts behind the dump's web, doc, video and image sources: how widely it actually looked."""
    hosts = set()
    for src in (out.get("sources") or {}).values():
        if isinstance(src, dict) and src.get("kind") in ("web", "doc", "video", "image") and src.get("url"):
            host = urllib.parse.urlsplit(str(src["url"])).hostname or ""
            if host:
                hosts.add(host[4:] if host.startswith("www.") else host)
    return hosts


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
    g, n = out["manifest"]["stats"]["grounding"], out["manifest"]["stats"]["entries"]
    if n >= LOW_GROUNDING_MIN_ENTRIES and g["collected"] * LOW_GROUNDING_PARTS < n:   # under 1/5, compared on counts
        _note(report, "warnings", "low_grounding", "/manifest/stats/grounding",
              "only %d of %d entries were collected (user_stated, reference_observed, researched); the rest is the build's own "
              "thinking. Widen the evidence (research facets, discovery, screenshots) before relying on it" % (g["collected"], n))
    if n >= LOW_GROUNDING_MIN_ENTRIES and g["hosts"] < MIN_SOURCE_HOSTS:
        _note(report, "warnings", "narrow_sources", "/sources",
              "sources come from %d host(s); research covers facets across several kinds of source, not one site" % g["hosts"])
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
# Tickets that discovery made (ids like 19-watch-found-<slug>) read what the build found online,
# so nothing they write can be reference_observed, whatever the agent claimed.
FOUND_TICKET_PROVS = _DERIVED_ONLY | {"researched"}
EDITOR_TYPES = {"normalize", "synthesis", "audit"}
UNION_FIELDS = ("aliases", "variants", "keywords", "src")
FLAT_HOLDERS = ("anti_keywords", "open_questions")


def _is_found_shard(name, shard):
    tid = str((shard.get("ticket") or {}).get("id") or "")
    return "-found-" in name or "-found-" in tid


def _relabel_found_sources(shard, name, report):
    """Everything a found ticket cites was found online: no user-supplied references, media origin web."""
    for sid, src in (shard.get("sources") or {}).items():
        if not isinstance(src, dict):
            continue
        changed = False
        if src.get("kind") == "reference":
            src["kind"], changed = "web", True
        if src.get("user_supplied"):
            src["user_supplied"], changed = False, True
        if src.get("kind") in MEDIA_SOURCE_KINDS and src.get("origin") != "web":
            src["origin"], changed = "web", True
        if changed:
            _note(report, "fixes", "found_source_relabeled", name, "source '%s' came from a found ticket; relabeled as found online" % sid)


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


def _group_notes(container, gpath=()):
    """Yield (group path, key, value) for "_" notes at any group depth (e.g. an options group's `_about`)."""
    for key, val in container.items():
        if str(key).startswith("_"):
            yield gpath, key, val
        elif _is_group(val):
            for item in _group_notes(val, gpath + (key,)):
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
        if _is_found_shard(name, shard):
            allowed = allowed & FOUND_TICKET_PROVS
            _relabel_found_sources(shard, name, report)
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
            if hname not in FLAT_HOLDERS:
                for gpath, k, v in _group_notes(content):
                    slot["notes"][(gpath, k)] = v
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
        d = {}
        for (gpath, k), v in slot["notes"].items():
            node = d
            for g in gpath:
                node = node.setdefault(g, {})
            node[k] = v
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
    _check_images_viewed(workdir, draft, report)
    return draft, report


def _check_images_viewed(workdir, draft, report):
    """Warn about collected images (images/manifest.json) that no `visual` entry describes: someone has to look.

    An image counts as seen when a visual entry cites a source with its `image_id`, or the place it came from:
    the page a screenshot shows, the video and timecode a frame was taken at, or the image's own url or file.
    """
    path = os.path.join(workdir, "images", "manifest.json")
    if not os.path.exists(path):
        return
    man = _load_json(path, report, "bad_images_manifest")
    if not isinstance(man, dict):
        return
    seen = set()
    for _eid, _ptr, entry, _h in iter_entries(draft):
        if entry.get("method") != "visual":
            continue
        for sid in entry.get("src") or []:
            src = draft["sources"].get(sid)
            if not isinstance(src, dict):
                continue
            if src.get("image_id"):
                seen.add(("id", src["image_id"]))
            for key in ("url", "path"):
                if src.get(key):
                    seen.add(("at", os.path.basename(str(src[key])) if key == "path" else str(src[key])))
            if src.get("kind") == "video" and src.get("url"):
                seen.add(("frame", str(src["url"]), str(entry.get("timecode") or entry.get("start_tc") or "")))
    for img in man.get("images") or []:
        if not isinstance(img, dict) or not img.get("id"):
            continue
        origin = img.get("source") or {}
        keys = {("id", img["id"])}
        if origin.get("kind") == "screenshot" and origin.get("page"):
            keys.add(("at", str(origin["page"])))
        if origin.get("kind") == "video" and origin.get("video"):
            keys.add(("frame", str(origin["video"]), str(origin.get("timecode") or "")))
        if origin.get("url"):
            keys.add(("at", str(origin["url"])))
        if origin.get("path"):
            keys.add(("at", os.path.basename(str(origin["path"]))))
        if not keys & seen:
            _note(report, "warnings", "image_not_viewed", "images/manifest.json:/%s" % img["id"],
                  "%s (%s) was collected but no visual entry describes it: open it with Read and write what you see, "
                  "citing a source with image_id %s or the page, video or url it came from" % (img["id"], img.get("file", ""), img["id"]))


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
    for k in list(sections):   # a section left with only `_` notes (normalize merged it away) is nothing a consumer can use
        holder = out[k]
        if isinstance(holder, dict) and not any(h == k for _e, _p, _en, h in iter_entries({k: holder})):
            _note(report, "fixes", "empty_section_dropped", "/" + _esc(k), "section had no entries, only notes; dropped")
            del out[k]
            sections.remove(k)
    out["index"] = {}
    out["sources"] = src.get("sources") or {}
    _validate_spine(out, report)
    ids = _validate_entries(out, report)
    _add_tier1_route(out)
    _validate_refs(out, ids, report)
    out["index"] = _build_index(out)
    _validate_routes(out, sections, report)
    _check_digested(out, sections, report)
    _check_wordy(out, report)
    _check_quality_readings(out, report)
    return out, report


QUALITY_MIN_READINGS = 2


def _check_quality_readings(out, report):
    """A quality word from the prompt keeps its readings side by side. One definition, tuned against, is how a dump
    narrows a creative task (test 8: every build copied the curves fitted to the dump's own idea of "sticky")."""
    for _eid, ptr, entry, _h in iter_entries(out):
        if entry.get("kind") != "quality":
            continue
        readings = entry.get("readings")
        n = len(readings) if isinstance(readings, list) else 0
        if n < QUALITY_MIN_READINGS:
            _note(report, "warnings", "quality_one_reading", ptr,
                  "a quality facet needs at least %d `readings` side by side (it has %d): the ways '%s' can be read for this task, "
                  "each with what it looks like in practice, so the consumer chooses or combines instead of copying one definition"
                  % (QUALITY_MIN_READINGS, n, entry.get("term", "?")))


WORDY_TEXT_WORDS = 40      # a facet's prose is a line or two; the rest belongs in lists of short phrases
WORDY_INSTEAD_WORDS = 20   # an `instead` is pasted into prompts as a rewrite, so it stays a phrase
ENTRY_MAX_TOKENS = 300     # a facet is 100-200 tokens in the hand-made dumps; past this it has become a section
LONG_KINDS = {"timeline", "transcript", "media"}   # measured data is long by nature


def _check_wordy(out, report):
    """Warn about prose that should have been lists, and facets that grew into sections: the hand-made dumps this
    format follows were short phrases in small objects."""
    for _eid, ptr, entry, _h in iter_entries(out):
        size = _tokens(entry)
        if size > ENTRY_MAX_TOKENS and entry.get("kind") not in LONG_KINDS:
            _note(report, "warnings", "oversized_entry", ptr,
                  "entry is ~%d tokens (limit %d): split it into facets of one area each, or move detail into other entries"
                  % (size, ENTRY_MAX_TOKENS))
        for field, limit in (("text", WORDY_TEXT_WORDS), ("instead", WORDY_INSTEAD_WORDS)):
            n = len(str(entry.get(field) or "").split())
            if n > limit:
                _note(report, "warnings", "wordy_entry", ptr,
                      "`%s` runs %d words (limit %d): keep it to a line and move the rest into lists of short phrases "
                      "(properties, keywords, behaviors)" % (field, n, limit))
                break


def _check_digested(out, sections, report):
    """Warn about a task section that is one source passed through whole, not digested into the task's own sections."""
    for name in sections:
        holder = out.get(name)
        if not isinstance(holder, dict):
            continue
        entries = [e for _eid, _ptr, e, h in iter_entries({name: holder}) if h == name]
        cited = [set(e.get("src") or []) for e in entries]
        if len(entries) >= UNDIGESTED_MIN_ENTRIES and all(cited) and len(set().union(*cited)) == 1:
            sid = next(iter(cited[0]))
            _note(report, "warnings", "undigested_source", "/" + _esc(name),
                  "all %d entries come from one source ('%s'): that's the source passed through, not digested. Break it "
                  "down into the task's own sections and merge it with what other sources and the model say" % (len(entries), sid))


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
    for bucket, label in (("errors", "error"), ("fixes", "fix"), ("warnings", "warning")):
        items = report[bucket]
        for item in items[:limit]:
            lines.append("  %-8s %-32s %s  %s" % (label, item["code"], item["path"], item["msg"]))
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
    g = stats.get("grounding") or {}
    print("grounding: %s of %s collected (%d%%), %s source hosts" % (
        g.get("collected", 0), stats.get("entries", 0), round(100 * g.get("collected_share", 0)), g.get("hosts", 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

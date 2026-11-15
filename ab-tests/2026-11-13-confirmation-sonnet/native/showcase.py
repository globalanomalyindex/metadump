#!/usr/bin/env python3
"""Copy the confirmation test's 48 builds into docs/showcase/round-3/<task>/ for the public showcase (GitHub Pages).

Each copy gets one line put first in its <head>, the same shim gallery_server.py injects at serve time: it prefixes the
build's localStorage and sessionStorage keys with its own path. Seven block worlds save under one key ("blocks32"), and on
one origin they would load each other's worlds; in the test every build ran in a fresh browser. The copies are for
viewing only. The test evidence stays in <task>/runs/, untouched. Usage: python3 native/showcase.py
"""
import os, re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "showcase", "round-3"))
TASKS = ["t1-pelican", "t2-ascii", "t3-bento", "t4-blocks"]
SHIM = ("<script>/* showcase copy: storage keys prefixed per build */(function(){var p=%s+':',S=Storage.prototype,g=S.getItem,s=S.setItem,r=S.removeItem;"
        "S.getItem=function(k){return g.call(this,p+k)};S.setItem=function(k,v){return s.call(this,p+k,v)};"
        "S.removeItem=function(k){return r.call(this,p+k)};})();</script>")


def main():
    n = 0
    for slug in TASKS:
        src, dst = os.path.join(HERE, slug, "runs"), os.path.join(OUT, slug)
        os.makedirs(dst, exist_ok=True)
        for f in sorted(os.listdir(src)):
            if not re.match(r"^[AFQ]-r\d\.html$", f):
                continue
            html = open(os.path.join(src, f), encoding="utf-8").read()
            shim = SHIM % ('"%s/%s"' % (slug, f[:-5]))
            head = re.search(r"<head[^>]*>", html, re.I)
            html = html[:head.end()] + shim + html[head.end():] if head else shim + html
            open(os.path.join(dst, f), "w", encoding="utf-8").write(html)
            n += 1
    print("copied", n, "builds to", OUT)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Serves this folder for gallery.html. Every build is served as it is on disk, except for one line put first in its <head>:
it gives the build's localStorage and sessionStorage keys a prefix of its own path. Seven block worlds save under the same
key ("blocks32"), and on one origin they would load each other's worlds; in the test each build ran in a fresh browser.
The files on disk are never changed. Usage: python3 gallery_server.py [port]   (default 8137, bound to 127.0.0.1)"""
import functools, http.server, os, re, sys, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = re.compile(r"^/(t\d-[a-z]+/runs/[AFQ]-r\d)\.html$")
SHIM = ("<script>(function(){var p=%s+':',S=Storage.prototype,g=S.getItem,s=S.setItem,r=S.removeItem;"
        "S.getItem=function(k){return g.call(this,p+k)};S.setItem=function(k,v){return s.call(this,p+k,v)};"
        "S.removeItem=function(k){return r.call(this,p+k)};})();</script>")


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        m = BUILD.match(path)
        if not m:
            return super().do_GET()
        try:
            html = open(os.path.join(HERE, m.group(1) + ".html"), encoding="utf-8").read()
        except OSError:
            return self.send_error(404)
        shim = SHIM % ('"%s"' % m.group(1))
        head = re.search(r"<head[^>]*>", html, re.I)
        html = html[:head.end()] + shim + html[head.end():] if head else shim + html
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8137
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(Handler, directory=HERE))
    print("serving http://localhost:%d/gallery.html" % port, flush=True)
    server.serve_forever()

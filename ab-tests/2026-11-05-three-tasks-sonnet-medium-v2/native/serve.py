"""Serve a showcase directory at / and this native/ folder at /__native/ on one origin (stdlib only).

Same origin matters: the Chrome window page (/__native/window.html) reaches into the scene iframe and its
build iframes to find targets and read the cursor style under the pointer.
Usage: python3 serve.py <showcase_dir> <port>
"""
import functools, http.server, os, sys

SHOWCASE, PORT = os.path.abspath(sys.argv[1]), int(sys.argv[2])
NATIVE = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith('/__native/'):
            rel = path[len('/__native/'):].split('?', 1)[0].split('#', 1)[0]
            return os.path.join(NATIVE, os.path.normpath('/' + rel).lstrip('/'))
        return super().translate_path(path)

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *a):
        pass


http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Handler, directory=SHOWCASE)).serve_forever()

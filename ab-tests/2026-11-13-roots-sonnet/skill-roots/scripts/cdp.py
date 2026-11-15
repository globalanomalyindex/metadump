#!/usr/bin/env python3
"""Drive an already-installed Chromium-family browser headless over the Chrome DevTools Protocol.

Python 3.9 standard library only. The standard library has no WebSocket client,
so this module carries a minimal one (RFC 6455 client side: upgrade handshake,
masking, 7/16/64-bit lengths, fragmented messages, ping/pong, close), which is
all CDP needs. The browser is launched with a throwaway profile, talks only to
127.0.0.1, and is always shut down and its profile removed on exit, including
on exceptions.

Library use (from the other metadump scripts):

    with cdp.Browser() as browser:          # raises BrowserUnavailable if none is installed
        page = browser.new_page()
        page.navigate("https://example.com/")
        png = page.screenshot(full_page=True)
        title = page.evaluate("document.title")

CLI:
    python3 cdp.py probe                         launch, print the browser version, exit
    python3 cdp.py screenshot URL OUT.png        screenshot a page (viewport or --full-page)
    python3 cdp.py eval URL EXPRESSION           print the JSON value of a JS expression

Exit codes: 0 ok, 2 usage, 3 no Chromium-family browser available.
"""
import argparse
import atexit
import base64
import collections
import hashlib
import json
import math
import os
import select
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tools  # noqa: E402

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OP_CONT, OP_TEXT, OP_BINARY, OP_CLOSE, OP_PING, OP_PONG = 0x0, 0x1, 0x2, 0x8, 0x9, 0xA
EXIT_NO_TOOL = 3


class WebSocketError(Exception):
    pass


class ConnectionClosed(WebSocketError):
    def __init__(self, code=None, reason=""):
        WebSocketError.__init__(self, "websocket closed (code %s) %s" % (code, reason))
        self.code = code
        self.reason = reason


class CDPError(Exception):
    pass


class CDPTimeout(CDPError):
    pass


class JSError(CDPError):
    pass


class NavigationError(CDPError):
    pass


class BrowserUnavailable(Exception):
    """No Chromium-family browser could be found or launched."""

    def __init__(self, message, searched=None, hint=None):
        Exception.__init__(self, message)
        self.searched = searched or []
        self.hint = hint or tools.BROWSER_HINT

    def as_dict(self):
        return {"ok": False, "reason": "needs_browser", "message": str(self), "searched": self.searched, "hint": self.hint}


# ---------------------------------------------------------------- WebSocket (RFC 6455, client side)

def accept_key(key):
    return base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")


def handshake_request(host, port, path, key):
    lines = [
        "GET %s HTTP/1.1" % path,
        "Host: %s:%d" % (host, port),
        "Upgrade: websocket",
        "Connection: Upgrade",
        "Sec-WebSocket-Key: %s" % key,
        "Sec-WebSocket-Version: 13",
    ]
    # No Origin header: Chrome only accepts DevTools connections without one (or with an allowed origin).
    return ("\r\n".join(lines) + "\r\n\r\n").encode("ascii")


def check_handshake_response(data, key):
    text = data.decode("latin-1")
    head = text.split("\r\n\r\n", 1)[0].split("\r\n")
    status = head[0].split(" ", 2)
    if len(status) < 2 or status[1] != "101":
        raise WebSocketError("handshake refused: %s" % head[0])
    headers = {}
    for line in head[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            headers[k.strip().lower()] = v.strip()
    if headers.get("upgrade", "").lower() != "websocket":
        raise WebSocketError("handshake: missing Upgrade: websocket")
    if headers.get("sec-websocket-accept") != accept_key(key):
        raise WebSocketError("handshake: bad Sec-WebSocket-Accept")


def apply_mask(data, key):
    """XOR data with the repeating 4-byte key (masking and unmasking are the same operation)."""
    n = len(data)
    if not n:
        return b""
    reps = (key * (n // 4 + 1))[:n]
    return (int.from_bytes(data, "big") ^ int.from_bytes(reps, "big")).to_bytes(n, "big")


def encode_frame(opcode, payload, fin=True, mask=True, mask_key=None):
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    b0 = (0x80 if fin else 0) | (opcode & 0x0F)
    mbit = 0x80 if mask else 0
    n = len(payload)
    if n < 126:
        header = struct.pack("!BB", b0, mbit | n)
    elif n < 65536:
        header = struct.pack("!BBH", b0, mbit | 126, n)
    else:
        header = struct.pack("!BBQ", b0, mbit | 127, n)
    if not mask:
        return header + payload
    key = mask_key or os.urandom(4)
    return header + key + apply_mask(payload, key)


class FrameReader(object):
    """Parse one frame at a time from a read_exact(n) callable."""

    def __init__(self, read_exact):
        self.read_exact = read_exact

    def _need(self, n):
        data = self.read_exact(n)
        if len(data) < n:
            raise ConnectionClosed(None, "connection lost mid-frame")
        return data

    def read_frame(self):
        b0, b1 = self._need(2)
        fin = bool(b0 & 0x80)
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        n = b1 & 0x7F
        if n == 126:
            n = struct.unpack("!H", self._need(2))[0]
        elif n == 127:
            n = struct.unpack("!Q", self._need(8))[0]
        key = self._need(4) if masked else None
        payload = self._need(n) if n else b""
        if key:
            payload = apply_mask(payload, key)
        return fin, opcode, payload


class WebSocket(object):
    def __init__(self, sock, leftover=b""):
        self.sock = sock
        self._buf = bytearray(leftover)
        self.closed = False
        self.reader = FrameReader(self._read_exact)

    @classmethod
    def connect(cls, url, timeout=10):
        u = urllib.parse.urlparse(url)
        if u.scheme != "ws":
            raise WebSocketError("only ws:// URLs (a local DevTools endpoint) are supported: %s" % url)
        host, port = u.hostname, u.port or 80
        path = (u.path or "/") + ("?" + u.query if u.query else "")
        sock = socket.create_connection((host, port), timeout=timeout)
        try:
            key = base64.b64encode(os.urandom(16)).decode("ascii")
            sock.sendall(handshake_request(host, port, path, key))
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    raise WebSocketError("handshake: connection closed")
                data += chunk
                if len(data) > 65536:
                    raise WebSocketError("handshake: response too large")
            head, _sep, rest = data.partition(b"\r\n\r\n")
            check_handshake_response(head + b"\r\n\r\n", key)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.settimeout(120)  # per-frame read timeout; waiting for a message uses select()
        except Exception:
            sock.close()
            raise
        return cls(sock, rest)

    def _read_exact(self, n):
        out = bytearray(n)
        have = min(len(self._buf), n)
        if have:
            out[:have] = self._buf[:have]
            del self._buf[:have]
        view = memoryview(out)
        pos = have
        while pos < n:
            got = self.sock.recv_into(view[pos:], n - pos)
            if not got:
                raise ConnectionClosed(None, "connection lost")
            pos += got
        return bytes(out)

    def _send(self, opcode, payload):
        self.sock.sendall(encode_frame(opcode, payload, mask=True))

    def send_text(self, text):
        self._send(OP_TEXT, text.encode("utf-8"))

    def send_binary(self, data):
        self._send(OP_BINARY, data)

    def ping(self, payload=b""):
        self._send(OP_PING, payload)

    def recv(self, timeout=None):
        """Return the next whole message (str for text, bytes for binary). Answers pings on the way."""
        if timeout is not None and not self._buf:
            ready, _w, _x = select.select([self.sock], [], [], max(0.0, timeout))
            if not ready:
                raise socket.timeout("no message within %.1fs" % timeout)
        parts = []
        msg_op = None
        while True:
            fin, op, payload = self.reader.read_frame()
            if op == OP_PING:
                self._send(OP_PONG, payload)
                continue
            if op == OP_PONG:
                continue
            if op == OP_CLOSE:
                code = struct.unpack("!H", payload[:2])[0] if len(payload) >= 2 else None
                reason = payload[2:].decode("utf-8", "replace")
                if not self.closed:
                    self.closed = True
                    try:
                        self._send(OP_CLOSE, payload[:2])
                    except OSError:
                        pass
                raise ConnectionClosed(code, reason)
            if op in (OP_TEXT, OP_BINARY):
                msg_op = op
                parts = [payload]
            elif op == OP_CONT:
                if msg_op is None:
                    raise WebSocketError("continuation frame without a starting frame")
                parts.append(payload)
            else:
                raise WebSocketError("unknown opcode %d" % op)
            if fin:
                data = b"".join(parts)
                return data.decode("utf-8") if msg_op == OP_TEXT else data

    def close(self, code=1000, reason=""):
        if not self.closed:
            self.closed = True
            try:
                self._send(OP_CLOSE, struct.pack("!H", code) + reason.encode("utf-8")[:120])
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass


# ---------------------------------------------------------------- DevTools endpoints

def parse_version(text):
    d = json.loads(text)
    return {"browser": d.get("Browser"), "protocol": d.get("Protocol-Version"),
            "user_agent": d.get("User-Agent"), "ws_url": d.get("webSocketDebuggerUrl")}


def parse_targets(text):
    out = []
    for t in json.loads(text) or []:
        if isinstance(t, dict) and t.get("type") == "page":
            out.append({"id": t.get("id"), "type": "page", "url": t.get("url"), "title": t.get("title"),
                        "ws_url": t.get("webSocketDebuggerUrl")})
    return out


def parse_active_port(text):
    """Parse <profile>/DevToolsActivePort: port on line 1, browser websocket path on line 2."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines or not lines[0].isdigit():
        return None
    return int(lines[0]), (lines[1] if len(lines) > 1 else "")


def launch_args(path, profile, width=1280, height=800, headless=True, extra=()):
    args = [path]
    if headless:
        args.append("--headless=new")
    args += [
        "--remote-debugging-port=0",
        "--user-data-dir=" + profile,
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-sync",
        "--disable-extensions",
        "--disable-default-apps",
        "--disable-features=Translate,MediaRouter,DialMediaRouteProvider,OptimizationHints",
        "--deny-permission-prompts",
        "--metrics-recording-only",
        "--mute-audio",
        "--hide-scrollbars",
        "--password-store=basic",
        "--use-mock-keychain",
        "--autoplay-policy=no-user-gesture-required",
        "--window-size=%d,%d" % (width, height),
    ]
    if sys.platform.startswith("linux") and hasattr(os, "geteuid") and os.geteuid() == 0:
        args.append("--no-sandbox")  # Chrome refuses to start sandboxed as root (containers)
    args += list(extra)
    args.append("about:blank")
    return args


def _http_get(url, timeout=5):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # never route 127.0.0.1 via a proxy
    with opener.open(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


# ---------------------------------------------------------------- CDP messages

class MessageRouter(object):
    """Match command results to their ids; queue events until someone waits for them."""

    def __init__(self, max_events=10000):
        self._id = 0
        self.results = {}
        self.events = collections.deque(maxlen=max_events)

    def next_id(self):
        self._id += 1
        return self._id

    def add(self, msg):
        if not isinstance(msg, dict):
            return
        if "id" in msg:
            self.results[msg["id"]] = msg
        elif "method" in msg:
            self.events.append(msg)

    def has_result(self, i):
        return i in self.results

    def take_result(self, i):
        msg = self.results.pop(i, None)
        if msg is None:
            return None
        if "error" in msg:
            err = msg["error"] or {}
            raise CDPError("%s (code %s)%s" % (err.get("message"), err.get("code"),
                                               ": " + str(err["data"]) if err.get("data") else ""))
        return msg.get("result") or {}

    def take_event(self, method, predicate=None):
        for idx, ev in enumerate(self.events):
            if ev.get("method") == method:
                params = ev.get("params") or {}
                if predicate is None or predicate(params):
                    del self.events[idx]
                    return params
        return None

    def clear(self, method=None):
        if method is None:
            self.events.clear()
        else:
            keep = [e for e in self.events if e.get("method") != method]
            self.events.clear()
            self.events.extend(keep)


class Connection(object):
    """One CDP websocket (a page or the browser). send() blocks for the result; events queue up."""

    def __init__(self, ws, timeout=30):
        self.ws = ws
        self.router = MessageRouter()
        self.timeout = timeout

    def _pump(self, deadline, waiting_for):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CDPTimeout("timed out waiting for %s" % waiting_for)
        try:
            text = self.ws.recv(timeout=remaining)
        except socket.timeout:
            raise CDPTimeout("timed out waiting for %s" % waiting_for)
        except ConnectionClosed as exc:
            raise CDPError("browser connection closed while waiting for %s (%s)" % (waiting_for, exc))
        try:
            self.router.add(json.loads(text))
        except ValueError:
            pass

    def send(self, method, params=None, timeout=None):
        i = self.router.next_id()
        self.ws.send_text(json.dumps({"id": i, "method": method, "params": params or {}}))
        deadline = time.monotonic() + (timeout or self.timeout)
        while not self.router.has_result(i):
            self._pump(deadline, method)
        return self.router.take_result(i)

    def wait_event(self, method, predicate=None, timeout=None):
        deadline = time.monotonic() + (timeout or self.timeout)
        while True:
            ev = self.router.take_event(method, predicate)
            if ev is not None:
                return ev
            self._pump(deadline, method)

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


class Page(object):
    """Helpers for one page target."""

    def __init__(self, conn, target_id=None, browser=None):
        self.conn = conn
        self.target_id = target_id
        self.browser = browser
        self._enabled = set()

    def _enable(self, domain, params=None):
        if domain not in self._enabled:
            self.conn.send(domain + ".enable", params)
            self._enabled.add(domain)

    def navigate(self, url, wait="load", timeout=30, settle=0.0):
        """Navigate and wait for 'load', 'domcontentloaded', 'networkidle' or nothing (None)."""
        self._enable("Page")
        if wait == "networkidle" and "lifecycle" not in self._enabled:
            self.conn.send("Page.setLifecycleEventsEnabled", {"enabled": True})
            self._enabled.add("lifecycle")
        for m in ("Page.loadEventFired", "Page.domContentEventFired", "Page.lifecycleEvent"):
            self.conn.router.clear(m)
        res = self.conn.send("Page.navigate", {"url": url}, timeout=timeout)
        if res.get("errorText"):
            raise NavigationError("%s: %s" % (url, res["errorText"]))
        if wait == "load":
            self.conn.wait_event("Page.loadEventFired", timeout=timeout)
        elif wait == "domcontentloaded":
            self.conn.wait_event("Page.domContentEventFired", timeout=timeout)
        elif wait == "networkidle":
            loader = res.get("loaderId")
            try:
                self.conn.wait_event("Page.lifecycleEvent",
                                     lambda p: p.get("name") == "networkIdle" and (not loader or p.get("loaderId") == loader),
                                     timeout=timeout)
            except CDPTimeout:
                pass  # busy pages never go idle; carry on with what has rendered
        if settle:
            time.sleep(settle)
        return res

    def evaluate(self, expression, await_promise=True, timeout=None):
        res = self.conn.send("Runtime.evaluate", {"expression": expression, "awaitPromise": await_promise,
                                                  "returnByValue": True, "userGesture": True}, timeout=timeout)
        if res.get("exceptionDetails"):
            d = res["exceptionDetails"]
            desc = (d.get("exception") or {}).get("description") or d.get("text") or "JavaScript error"
            raise JSError(desc)
        return (res.get("result") or {}).get("value")

    def set_viewport(self, width, height, scale=1, mobile=False):
        self.conn.send("Emulation.setDeviceMetricsOverride",
                       {"width": int(width), "height": int(height), "deviceScaleFactor": scale, "mobile": mobile})

    def element_rect(self, selector):
        """Document-relative CSS-pixel rect of the first element matching selector, or None."""
        js = ("(() => { const el = document.querySelector(%s); if (!el) return null;"
              " const r = el.getBoundingClientRect();"
              " return {x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height}; })()"
              % json.dumps(selector))
        return self.evaluate(js)

    def screenshot(self, clip=None, full_page=False, scale=1.0, fmt="png", fast=False, timeout=60):
        params = {"format": fmt, "fromSurface": True}
        if full_page:
            m = self.conn.send("Page.getLayoutMetrics")
            size = m.get("cssContentSize") or m.get("contentSize") or {"width": 1280, "height": 800}
            clip = {"x": 0, "y": 0, "width": math.ceil(size["width"]), "height": min(math.ceil(size["height"]), 16384)}
            params["captureBeyondViewport"] = True
        if clip:
            c = {k: float(clip[k]) for k in ("x", "y", "width", "height")}
            c["scale"] = float(clip.get("scale", scale))
            params["clip"] = c
        if fast:
            params["optimizeForSpeed"] = True
        data = self.conn.send("Page.captureScreenshot", params, timeout=timeout)["data"]
        return base64.b64decode(data)

    def enable_network(self):
        self._enable("Network", {"maxTotalBufferSize": 100000000, "maxResourceBufferSize": 20000000})

    def wait_response(self, predicate, timeout=None):
        """Wait for a Network.responseReceived whose response dict satisfies predicate; returns the event params."""
        return self.conn.wait_event("Network.responseReceived", lambda p: predicate(p.get("response") or {}), timeout=timeout)

    def response_body(self, request_id, timeout=None):
        """Body of a finished request as bytes (waits for loadingFinished)."""
        self.conn.wait_event("Network.loadingFinished", lambda p: p.get("requestId") == request_id, timeout=timeout)
        res = self.conn.send("Network.getResponseBody", {"requestId": request_id}, timeout=timeout)
        body = res.get("body", "")
        return base64.b64decode(body) if res.get("base64Encoded") else body.encode("utf-8")

    def close(self):
        if self.browser is not None and self.target_id:
            try:
                self.browser.conn.send("Target.closeTarget", {"targetId": self.target_id}, timeout=5)
            except Exception:
                pass
        self.conn.close()


# ---------------------------------------------------------------- browser process

_LIVE = set()


def _cleanup_all():
    for b in list(_LIVE):
        b.close()


atexit.register(_cleanup_all)


def install_signal_cleanup():
    """Turn SIGTERM/SIGHUP into SystemExit so `finally` blocks shut the browser down."""
    for name in ("SIGTERM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is not None and signal.getsignal(sig) in (signal.SIG_DFL, None):
            signal.signal(sig, lambda signum, frame: sys.exit(128 + signum))


class Browser(object):
    """A headless Chromium-family browser with a throwaway profile. Use as a context manager."""

    def __init__(self, path=None, width=1280, height=800, headless=True, extra_args=(), timeout=20):
        if path is None:
            found = tools.find_browser()
            if not found["found"]:
                raise BrowserUnavailable("no Chromium-family browser found", found["searched"], found["hint"])
            path = found["path"]
        self.path = path
        self.width, self.height = width, height
        self.headless = headless
        self.extra_args = tuple(extra_args)
        self.timeout = timeout
        self.proc = None
        self.profile = None
        self.port = None
        self.conn = None
        self._log = None

    def __enter__(self):
        return self.start()

    def __exit__(self, *exc):
        self.close()
        return False

    def _log_tail(self):
        try:
            with open(os.path.join(self.profile, "chrome-stderr.log"), "rb") as f:
                return f.read()[-600:].decode("utf-8", "replace").strip()
        except (OSError, TypeError):
            return ""

    def start(self):
        self.profile = tempfile.mkdtemp(prefix="metadump-browser-")
        self._log = open(os.path.join(self.profile, "chrome-stderr.log"), "wb")
        args = launch_args(self.path, self.profile, self.width, self.height, self.headless, self.extra_args)
        try:
            self.proc = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=self._log,
                                         start_new_session=(os.name == "posix"))
        except OSError as exc:
            self.close()
            raise BrowserUnavailable("could not start %s: %s" % (self.path, exc), [self.path])
        _LIVE.add(self)
        try:
            port_file = os.path.join(self.profile, "DevToolsActivePort")
            deadline = time.monotonic() + self.timeout
            parsed = None
            while parsed is None:
                if self.proc.poll() is not None:
                    raise BrowserUnavailable("browser exited during startup (code %s): %s" % (self.proc.returncode, self._log_tail()), [self.path])
                if os.path.exists(port_file):
                    with open(port_file) as f:
                        parsed = parse_active_port(f.read())
                if parsed is None:
                    if time.monotonic() > deadline:
                        raise BrowserUnavailable("browser gave no DevTools port within %ss: %s" % (self.timeout, self._log_tail()), [self.path])
                    time.sleep(0.05)
            self.port, ws_path = parsed
            self.conn = Connection(WebSocket.connect("ws://127.0.0.1:%d%s" % (self.port, ws_path), timeout=10))
        except Exception:
            self.close()
            raise
        return self

    def version(self):
        return parse_version(_http_get("http://127.0.0.1:%d/json/version" % self.port))

    def targets(self):
        return parse_targets(_http_get("http://127.0.0.1:%d/json/list" % self.port))

    def new_page(self, width=None, height=None):
        res = self.conn.send("Target.createTarget", {"url": "about:blank"})
        tid = res["targetId"]
        ws = WebSocket.connect("ws://127.0.0.1:%d/devtools/page/%s" % (self.port, tid), timeout=10)
        page = Page(Connection(ws), target_id=tid, browser=self)
        page.set_viewport(width or self.width, height or self.height)
        return page

    def close(self):
        _LIVE.discard(self)
        if self.conn is not None:
            try:
                self.conn.send("Browser.close", timeout=3)
            except Exception:
                pass
            self.conn.close()
            self.conn = None
        if self.proc is not None:
            try:
                self.proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._kill(signal.SIGTERM)
                try:
                    self.proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._kill(getattr(signal, "SIGKILL", signal.SIGTERM))
                    try:
                        self.proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        pass
            self.proc = None
        if self._log is not None:
            try:
                self._log.close()
            except OSError:
                pass
            self._log = None
        if self.profile:
            shutil.rmtree(self.profile, ignore_errors=True)
            self.profile = None

    def _kill(self, sig):
        try:
            if os.name == "posix":
                os.killpg(self.proc.pid, sig)
            else:
                self.proc.kill()
        except (OSError, ProcessLookupError):
            pass


# ---------------------------------------------------------------- CLI

def _print_unavailable(exc):
    print(json.dumps(exc.as_dict(), indent=1))
    sys.stderr.write("%s\n%s\n" % (exc, exc.hint))
    return EXIT_NO_TOOL


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cdp.py", description="Drive an installed Chromium-family browser headless over the DevTools Protocol (stdlib only).",
                                 epilog="Exit codes: 0 ok, 2 usage, 3 no Chromium-family browser available.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe", help="launch the browser, print its version, shut it down")
    s = sub.add_parser("screenshot", help="screenshot a page")
    s.add_argument("url")
    s.add_argument("out")
    s.add_argument("--width", type=int, default=1280)
    s.add_argument("--height", type=int, default=800)
    s.add_argument("--full-page", action="store_true")
    e = sub.add_parser("eval", help="print the JSON value of a JavaScript expression on a page")
    e.add_argument("url")
    e.add_argument("expression")
    args = ap.parse_args(argv)
    install_signal_cleanup()
    try:
        with Browser(width=getattr(args, "width", 1280), height=getattr(args, "height", 800)) as browser:
            if args.cmd == "probe":
                v = browser.version()
                v.pop("ws_url", None)
                v["path"] = browser.path
                print(json.dumps(v, indent=1))
                return 0
            page = browser.new_page()
            page.navigate(args.url)
            if args.cmd == "screenshot":
                data = page.screenshot(full_page=args.full_page)
                with open(args.out, "wb") as f:
                    f.write(data)
                print(json.dumps({"ok": True, "out": args.out, "bytes": len(data)}))
            else:
                print(json.dumps(page.evaluate(args.expression), indent=1))
            return 0
    except BrowserUnavailable as exc:
        return _print_unavailable(exc)
    except CDPError as exc:
        sys.stderr.write("browser error: %s\n" % exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

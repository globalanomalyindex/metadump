"""Tests for skills/metadump/scripts/cdp.py (stdlib WebSocket + DevTools Protocol) and tools.py (detection).

No browser is needed: sockets are in-process socketpairs or a local fake server thread.
"""
import json
import os
import socket
import struct
import sys
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "metadump", "scripts")
sys.path.insert(0, SCRIPTS)

import cdp  # noqa: E402
import tools  # noqa: E402


def server_reader(sock):
    def read_exact(n):
        buf = b""
        while len(buf) < n:
            chunk = sock.recv(n - len(buf))
            if not chunk:
                raise EOFError
            buf += chunk
        return buf
    return cdp.FrameReader(read_exact)


class Handshake(unittest.TestCase):
    def test_accept_key_matches_rfc_6455_example(self):
        self.assertEqual(cdp.accept_key("dGhlIHNhbXBsZSBub25jZQ=="), "s3pPLMBiTxaQ9kYGzzhZRbK+xOo=")

    def test_request_has_upgrade_headers_and_no_origin(self):
        req = cdp.handshake_request("127.0.0.1", 9222, "/devtools/page/X", "abc=").decode("ascii")
        self.assertTrue(req.startswith("GET /devtools/page/X HTTP/1.1\r\n"))
        for h in ("Host: 127.0.0.1:9222", "Upgrade: websocket", "Connection: Upgrade",
                  "Sec-WebSocket-Key: abc=", "Sec-WebSocket-Version: 13"):
            self.assertIn(h + "\r\n", req)
        self.assertNotIn("Origin", req)
        self.assertTrue(req.endswith("\r\n\r\n"))

    def test_response_with_wrong_accept_is_rejected(self):
        bad = b"HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: nope\r\n\r\n"
        with self.assertRaises(cdp.WebSocketError):
            cdp.check_handshake_response(bad, "dGhlIHNhbXBsZSBub25jZQ==")

    def test_non_101_response_is_rejected(self):
        with self.assertRaises(cdp.WebSocketError):
            cdp.check_handshake_response(b"HTTP/1.1 403 Forbidden\r\n\r\n", "x")

    def test_connect_against_fake_server(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        port = srv.getsockname()[1]
        got = {}

        def serve():
            conn, _ = srv.accept()
            data = b""
            while b"\r\n\r\n" not in data:
                data += conn.recv(4096)
            key = [ln.split(":", 1)[1].strip() for ln in data.decode().split("\r\n") if ln.lower().startswith("sec-websocket-key")][0]
            conn.sendall(("HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                          "Sec-WebSocket-Accept: %s\r\n\r\n" % cdp.accept_key(key)).encode())
            fin, op, payload = server_reader(conn).read_frame()
            got["msg"] = payload.decode()
            conn.sendall(cdp.encode_frame(cdp.OP_TEXT, b"pong-text", mask=False))
            conn.close()

        t = threading.Thread(target=serve, daemon=True)
        t.start()
        ws = cdp.WebSocket.connect("ws://127.0.0.1:%d/devtools/browser/abc" % port, timeout=5)
        ws.send_text("hello")
        self.assertEqual(ws.recv(), "pong-text")
        ws.sock.close()
        t.join(5)
        srv.close()
        self.assertEqual(got["msg"], "hello")


class Framing(unittest.TestCase):
    def roundtrip(self, n, mask):
        payload = bytes((i * 7) % 256 for i in range(n))
        frame = cdp.encode_frame(cdp.OP_BINARY, payload, mask=mask, mask_key=b"\x01\x02\x03\x04")
        pos = [0]

        def read_exact(k):
            chunk = frame[pos[0]:pos[0] + k]
            pos[0] += k
            return chunk
        fin, op, got = cdp.FrameReader(read_exact).read_frame()
        self.assertTrue(fin)
        self.assertEqual(op, cdp.OP_BINARY)
        self.assertEqual(got, payload)
        return frame

    def test_small_payload_uses_7_bit_length(self):
        frame = self.roundtrip(125, mask=True)
        self.assertEqual(frame[1] & 0x7F, 125)
        self.assertEqual(frame[1] & 0x80, 0x80)  # client frames are masked
        self.assertEqual(len(frame), 2 + 4 + 125)

    def test_medium_payload_uses_16_bit_length(self):
        for n in (126, 65535):
            frame = self.roundtrip(n, mask=True)
            self.assertEqual(frame[1] & 0x7F, 126)
            self.assertEqual(struct.unpack("!H", frame[2:4])[0], n)

    def test_large_payload_uses_64_bit_length(self):
        frame = self.roundtrip(65536, mask=False)
        self.assertEqual(frame[1] & 0x7F, 127)
        self.assertEqual(struct.unpack("!Q", frame[2:10])[0], 65536)

    def test_empty_payload(self):
        self.roundtrip(0, mask=True)

    def test_mask_xors_payload_with_key(self):
        frame = cdp.encode_frame(cdp.OP_TEXT, b"abcd", mask=True, mask_key=b"\xff\x00\xff\x00")
        self.assertEqual(frame[2:6], b"\xff\x00\xff\x00")
        self.assertEqual(frame[6:], bytes([ord("a") ^ 0xFF, ord("b"), ord("c") ^ 0xFF, ord("d")]))

    def test_apply_mask_is_its_own_inverse(self):
        data = os.urandom(1001)
        key = os.urandom(4)
        self.assertEqual(cdp.apply_mask(cdp.apply_mask(data, key), key), data)


class MessageLevel(unittest.TestCase):
    def setUp(self):
        self.client_sock, self.server_sock = socket.socketpair()
        self.client_sock.settimeout(5)
        self.server_sock.settimeout(5)
        self.ws = cdp.WebSocket(self.client_sock)
        self.server = server_reader(self.server_sock)

    def tearDown(self):
        self.client_sock.close()
        self.server_sock.close()

    def test_fragmented_text_with_interleaved_ping_is_reassembled_and_ping_answered(self):
        s = self.server_sock
        s.sendall(cdp.encode_frame(cdp.OP_TEXT, b"Hel", fin=False, mask=False))
        s.sendall(cdp.encode_frame(cdp.OP_PING, b"are-you-there", mask=False))
        s.sendall(cdp.encode_frame(cdp.OP_CONT, "lo wö".encode("utf-8")[:4], fin=False, mask=False))
        s.sendall(cdp.encode_frame(cdp.OP_CONT, "lo wö".encode("utf-8")[4:] + b"rld", fin=True, mask=False))
        self.assertEqual(self.ws.recv(), "Hello wörld")
        fin, op, payload = self.server.read_frame()
        self.assertEqual(op, cdp.OP_PONG)
        self.assertEqual(payload, b"are-you-there")

    def test_close_frame_is_answered_and_raises_closed(self):
        self.server_sock.sendall(cdp.encode_frame(cdp.OP_CLOSE, struct.pack("!H", 1000) + b"bye", mask=False))
        with self.assertRaises(cdp.ConnectionClosed) as ctx:
            self.ws.recv()
        self.assertEqual(ctx.exception.code, 1000)
        fin, op, payload = self.server.read_frame()
        self.assertEqual(op, cdp.OP_CLOSE)
        self.assertEqual(struct.unpack("!H", payload[:2])[0], 1000)

    def test_client_close_sends_close_frame(self):
        self.ws.close()
        fin, op, payload = self.server.read_frame()
        self.assertEqual(op, cdp.OP_CLOSE)

    def test_large_server_message_is_read_whole(self):
        big = json.dumps({"id": 1, "result": {"data": "x" * 300000}})
        t = threading.Thread(target=lambda: self.server_sock.sendall(cdp.encode_frame(cdp.OP_TEXT, big.encode(), mask=False)))
        t.start()
        self.assertEqual(self.ws.recv(), big)
        t.join(5)


class Endpoints(unittest.TestCase):
    def test_parse_version(self):
        text = json.dumps({"Browser": "HeadlessChrome/131.0.0.0", "Protocol-Version": "1.3",
                           "User-Agent": "Mozilla/5.0 HeadlessChrome/131", "webSocketDebuggerUrl": "ws://127.0.0.1:5555/devtools/browser/abc"})
        v = cdp.parse_version(text)
        self.assertEqual(v["browser"], "HeadlessChrome/131.0.0.0")
        self.assertEqual(v["ws_url"], "ws://127.0.0.1:5555/devtools/browser/abc")

    def test_parse_targets_keeps_pages_with_ws_urls(self):
        text = json.dumps([
            {"id": "P1", "type": "page", "url": "about:blank", "webSocketDebuggerUrl": "ws://127.0.0.1:5/devtools/page/P1"},
            {"id": "W1", "type": "service_worker", "url": "https://x", "webSocketDebuggerUrl": "ws://127.0.0.1:5/devtools/page/W1"},
            {"id": "P2", "type": "page", "url": "https://y"},
        ])
        pages = cdp.parse_targets(text)
        self.assertEqual([p["id"] for p in pages], ["P1", "P2"])
        self.assertEqual(pages[0]["ws_url"], "ws://127.0.0.1:5/devtools/page/P1")
        self.assertIsNone(pages[1]["ws_url"])

    def test_parse_active_port_file(self):
        self.assertEqual(cdp.parse_active_port("53211\n/devtools/browser/uuid-1\n"), (53211, "/devtools/browser/uuid-1"))
        self.assertIsNone(cdp.parse_active_port(""))
        self.assertIsNone(cdp.parse_active_port("not-a-port\n"))

    def test_launch_args_are_headless_isolated_and_quiet(self):
        args = cdp.launch_args("/bin/chrome", "/tmp/profile", width=800, height=600)
        self.assertEqual(args[0], "/bin/chrome")
        for a in ("--headless=new", "--remote-debugging-port=0", "--user-data-dir=/tmp/profile",
                  "--no-first-run", "--window-size=800,600"):
            self.assertIn(a, args)
        self.assertEqual(args[-1], "about:blank")


class Router(unittest.TestCase):
    def test_results_match_ids_out_of_order_and_events_queue(self):
        r = cdp.MessageRouter()
        a, b = r.next_id(), r.next_id()
        r.add({"method": "Page.loadEventFired", "params": {"timestamp": 1}})
        r.add({"id": b, "result": {"v": "b"}})
        r.add({"id": a, "result": {"v": "a"}})
        self.assertEqual(r.take_result(a), {"v": "a"})
        self.assertEqual(r.take_result(b), {"v": "b"})
        self.assertIsNone(r.take_result(a))
        ev = r.take_event("Page.loadEventFired")
        self.assertEqual(ev["timestamp"], 1)
        self.assertIsNone(r.take_event("Page.loadEventFired"))

    def test_error_response_raises_cdp_error(self):
        r = cdp.MessageRouter()
        i = r.next_id()
        r.add({"id": i, "error": {"code": -32000, "message": "No node"}})
        with self.assertRaises(cdp.CDPError) as ctx:
            r.take_result(i)
        self.assertIn("No node", str(ctx.exception))

    def test_take_event_with_predicate_leaves_other_events(self):
        r = cdp.MessageRouter()
        r.add({"method": "Network.responseReceived", "params": {"requestId": "1", "response": {"url": "a"}}})
        r.add({"method": "Network.responseReceived", "params": {"requestId": "2", "response": {"url": "timedtext"}}})
        ev = r.take_event("Network.responseReceived", lambda p: "timedtext" in p["response"]["url"])
        self.assertEqual(ev["requestId"], "2")
        self.assertEqual(r.take_event("Network.responseReceived")["requestId"], "1")


class FakeWS(object):
    """Scripted socket stand-in: answers each command with the queued replies."""

    def __init__(self, script):
        self.script = script  # method -> list of messages to deliver after that command
        self.sent = []
        self.inbox = []

    def send_text(self, text):
        msg = json.loads(text)
        self.sent.append(msg)
        for m in self.script.get(msg["method"], [{"result": {}}]):
            m = dict(m)
            if "result" in m or "error" in m:
                m["id"] = msg["id"]
            self.inbox.append(json.dumps(m))

    def recv(self, timeout=None):
        if not self.inbox:
            raise cdp.CDPTimeout("nothing queued")
        return self.inbox.pop(0)

    def close(self):
        pass


class ConnectionTests(unittest.TestCase):
    def test_send_returns_result_and_queues_events(self):
        ws = FakeWS({"Page.navigate": [{"method": "Page.frameStartedLoading", "params": {}},
                                       {"result": {"frameId": "F"}},
                                       {"method": "Page.loadEventFired", "params": {"timestamp": 2}}]})
        conn = cdp.Connection(ws)
        self.assertEqual(conn.send("Page.navigate", {"url": "about:blank"}), {"frameId": "F"})
        self.assertEqual(conn.wait_event("Page.loadEventFired", timeout=1)["timestamp"], 2)
        self.assertEqual(ws.sent[0]["params"], {"url": "about:blank"})

    def test_evaluate_exception_raises_js_error(self):
        ws = FakeWS({"Runtime.evaluate": [{"result": {"result": {"type": "object"},
                                                      "exceptionDetails": {"text": "Uncaught", "exception": {"description": "ReferenceError: nope"}}}}]})
        page = cdp.Page(cdp.Connection(ws))
        with self.assertRaises(cdp.JSError) as ctx:
            page.evaluate("nope")
        self.assertIn("ReferenceError", str(ctx.exception))

    def test_evaluate_returns_value(self):
        ws = FakeWS({"Runtime.evaluate": [{"result": {"result": {"type": "number", "value": 42}}}]})
        page = cdp.Page(cdp.Connection(ws))
        self.assertEqual(page.evaluate("6*7"), 42)
        self.assertTrue(ws.sent[0]["params"]["awaitPromise"])
        self.assertTrue(ws.sent[0]["params"]["returnByValue"])

    def test_navigation_error_text_raises(self):
        ws = FakeWS({"Page.enable": [{"result": {}}], "Page.navigate": [{"result": {"frameId": "F", "errorText": "net::ERR_NAME_NOT_RESOLVED"}}]})
        page = cdp.Page(cdp.Connection(ws))
        with self.assertRaises(cdp.NavigationError):
            page.navigate("http://nope.invalid/")


class BrowserDetection(unittest.TestCase):
    CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    def test_finds_macos_chrome_by_path(self):
        found = tools.find_browser(env={}, exists=lambda p: p == self.CHROME, which=lambda n: None,
                                   platform="darwin", home="/Users/x")
        self.assertTrue(found["found"])
        self.assertEqual(found["path"], self.CHROME)
        self.assertEqual(found["name"], "Google Chrome")

    def test_falls_back_to_path_lookup(self):
        found = tools.find_browser(env={}, exists=lambda p: False,
                                   which=lambda n: "/usr/local/bin/chromium" if n == "chromium" else None,
                                   platform="linux", home="/home/x")
        self.assertTrue(found["found"])
        self.assertEqual(found["path"], "/usr/local/bin/chromium")
        self.assertEqual(found["via"], "PATH")

    def test_env_override_wins_when_it_exists(self):
        found = tools.find_browser(env={"METADUMP_BROWSER": "/opt/edge/msedge"}, exists=lambda p: p == "/opt/edge/msedge",
                                   which=lambda n: None, platform="linux", home="/home/x")
        self.assertEqual(found["path"], "/opt/edge/msedge")
        self.assertEqual(found["via"], "env")

    def test_nothing_found_lists_searched_paths_and_hint(self):
        found = tools.find_browser(env={}, exists=lambda p: False, which=lambda n: None, platform="darwin", home="/Users/x")
        self.assertFalse(found["found"])
        self.assertIn(self.CHROME, found["searched"])
        self.assertTrue(any("PATH:" in s for s in found["searched"]))
        self.assertIn("Chrom", found["hint"])

    def test_disable_env_hides_a_present_tool(self):
        env = {"METADUMP_DISABLE": "browser,ffmpeg"}
        self.assertFalse(tools.find_browser(env=env, exists=lambda p: True, which=lambda n: "/x/" + n,
                                            platform="darwin", home="/Users/x")["found"])
        self.assertFalse(tools.find_tool("ffmpeg", env=env, which=lambda n: "/x/ffmpeg")["found"])
        self.assertTrue(tools.find_tool("ffprobe", env=env, which=lambda n: "/x/ffprobe")["found"])

    def test_detect_reports_every_tool_and_capabilities(self):
        rep = tools.detect(env={}, exists=lambda p: False, which=lambda n: "/usr/bin/sips" if n == "sips" else None,
                           platform="darwin", home="/Users/x")
        for name in ("browser", "yt-dlp", "ffmpeg", "ffprobe", "sips"):
            self.assertIn(name, rep["tools"])
        self.assertFalse(rep["tools"]["yt-dlp"]["found"])
        self.assertIn("hint", rep["tools"]["yt-dlp"])
        caps = rep["capabilities"]
        self.assertTrue(caps["video metadata and captions"])
        self.assertFalse(caps["video frames and timing"])
        self.assertTrue(caps["page fetch and clean"])


if __name__ == "__main__":
    unittest.main()

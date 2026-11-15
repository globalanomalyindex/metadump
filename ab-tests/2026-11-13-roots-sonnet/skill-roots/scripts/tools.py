#!/usr/bin/env python3
"""Report which optional tools metadump can use on this machine.

metadump never installs anything. The page, image and video scripts run on the
Python 3.9 standard library plus, when one is already installed, a
Chromium-family browser driven headless. yt-dlp and ffmpeg/ffprobe are optional
accelerators: used when present, never required.

Environment:
  METADUMP_BROWSER=/path/to/chrome   use this browser binary
  METADUMP_DISABLE=browser,ffmpeg     pretend these tools are absent (for testing the fallbacks)

Usage:
  python3 tools.py           human-readable report
  python3 tools.py --json    the same as JSON
"""
import argparse
import json
import os
import shutil
import sys

TOOL_NAMES = ("browser", "yt-dlp", "ffmpeg", "ffprobe", "sips")

BROWSER_HINT = ("No Chromium-family browser found. Install Google Chrome (https://www.google.com/chrome/) or Chromium "
                "(macOS: brew install --cask chromium; Debian/Ubuntu: sudo apt install chromium), or Microsoft Edge or Brave, "
                "or set METADUMP_BROWSER to an existing Chrome/Chromium binary. metadump only uses one that is already there.")
HINTS = {
    "yt-dlp": "Optional accelerator for video metadata, captions and segment reads. macOS: brew install yt-dlp; elsewhere: pipx install yt-dlp. Everything works without it.",
    "ffmpeg": "Optional accelerator for frame-exact extraction and scene detection. macOS: brew install ffmpeg; Debian/Ubuntu: sudo apt install ffmpeg. Frames and timing also work through the browser.",
    "ffprobe": "Optional, ships with ffmpeg. Reads duration and fps of local video files exactly.",
    "sips": "Built into macOS (image format conversion). Not available elsewhere; the browser or ffmpeg is used instead.",
}

# (name, path) in search order, per platform. "~" is expanded against `home`.
_MAC_APPS = [
    ("Google Chrome", "Google Chrome.app/Contents/MacOS/Google Chrome"),
    ("Chromium", "Chromium.app/Contents/MacOS/Chromium"),
    ("Microsoft Edge", "Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
    ("Brave", "Brave Browser.app/Contents/MacOS/Brave Browser"),
    ("Google Chrome Canary", "Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"),
]
_LINUX_PATHS = [
    ("Google Chrome", "/usr/bin/google-chrome"),
    ("Google Chrome", "/usr/bin/google-chrome-stable"),
    ("Google Chrome", "/opt/google/chrome/chrome"),
    ("Chromium", "/usr/bin/chromium"),
    ("Chromium", "/usr/bin/chromium-browser"),
    ("Chromium", "/snap/bin/chromium"),
    ("Microsoft Edge", "/usr/bin/microsoft-edge"),
    ("Microsoft Edge", "/usr/bin/microsoft-edge-stable"),
    ("Brave", "/usr/bin/brave-browser"),
    ("Brave", "/opt/brave.com/brave/brave"),
]
_WIN_PATHS = [
    ("Google Chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ("Google Chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ("Microsoft Edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ("Microsoft Edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    ("Brave", r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ("Chromium", r"C:\Program Files\Chromium\Application\chrome.exe"),
]
PATH_NAMES = [
    ("Google Chrome", "google-chrome"), ("Google Chrome", "google-chrome-stable"), ("Google Chrome", "chrome"),
    ("Chromium", "chromium"), ("Chromium", "chromium-browser"),
    ("Microsoft Edge", "microsoft-edge"), ("Microsoft Edge", "microsoft-edge-stable"), ("Microsoft Edge", "msedge"),
    ("Brave", "brave-browser"), ("Brave", "brave"),
]


def _disabled(env):
    raw = (env or {}).get("METADUMP_DISABLE", "")
    return {p.strip().lower() for p in raw.split(",") if p.strip()}


def browser_candidates(platform, home):
    """Install paths to try, in order, for this platform."""
    if platform == "darwin":
        out = [(n, "/Applications/" + p) for n, p in _MAC_APPS]
        out += [(n, os.path.join(home or "~", "Applications", p)) for n, p in _MAC_APPS]
        return out
    if platform.startswith("win"):
        local = os.path.join(home or "", "AppData", "Local")
        return _WIN_PATHS + [("Google Chrome", os.path.join(local, "Google", "Chrome", "Application", "chrome.exe"))]
    return list(_LINUX_PATHS)


def find_browser(env=None, exists=None, which=None, platform=None, home=None):
    """Find a Chromium-family browser. Returns {found, path, name, via, searched, hint}."""
    env = os.environ if env is None else env
    exists = exists or os.path.exists
    which = which or shutil.which
    platform = platform or sys.platform
    home = home if home is not None else os.path.expanduser("~")
    searched = []
    result = {"found": False, "path": None, "name": None, "via": None, "searched": searched, "hint": BROWSER_HINT}
    if "browser" in _disabled(env):
        searched.append("(disabled by METADUMP_DISABLE)")
        return result
    override = env.get("METADUMP_BROWSER")
    if override:
        searched.append(override)
        if exists(override):
            result.update(found=True, path=override, name=os.path.basename(override), via="env")
            return result
    for name, path in browser_candidates(platform, home):
        searched.append(path)
        if exists(path):
            result.update(found=True, path=path, name=name, via="path")
            return result
    for name, exe in PATH_NAMES:
        searched.append("PATH:" + exe)
        hit = which(exe)
        if hit:
            result.update(found=True, path=hit, name=name, via="PATH")
            return result
    return result


def find_tool(name, env=None, which=None):
    """Find an optional command-line tool on PATH. Returns {found, path, hint}."""
    env = os.environ if env is None else env
    which = which or shutil.which
    if name.lower() in _disabled(env):
        return {"found": False, "path": None, "hint": HINTS.get(name, ""), "note": "disabled by METADUMP_DISABLE"}
    path = which(name)
    return {"found": bool(path), "path": path, "hint": HINTS.get(name, "")}


def detect(env=None, exists=None, which=None, platform=None, home=None):
    """Full report: every tool plus which metadump capabilities are available."""
    platform = platform or sys.platform
    found = {"browser": find_browser(env=env, exists=exists, which=which, platform=platform, home=home)}
    for name in ("yt-dlp", "ffmpeg", "ffprobe", "sips"):
        found[name] = find_tool(name, env=env, which=which)
    has = {k: v["found"] for k, v in found.items()}
    converter = has["browser"] or has["sips"] or has["ffmpeg"]
    caps = {
        "page fetch and clean": True,
        "rendered page fetch and screenshots": has["browser"],
        "video metadata and captions": True,
        "video frames and timing": has["browser"] or has["ffmpeg"],
        "video scene detection": has["ffmpeg"],
        "palette from PNG": True,
        "palette from JPEG, WebP, AVIF, GIF": converter,
        "moodboard HTML": True,
        "moodboard PNG render": has["browser"],
    }
    return {"python": "%d.%d.%d" % sys.version_info[:3], "platform": platform, "tools": found, "capabilities": caps}


def format_report(rep):
    lines = ["metadump optional tools (python %s, %s). Nothing is ever installed." % (rep["python"], rep["platform"]), ""]
    for name in TOOL_NAMES:
        t = rep["tools"][name]
        if t["found"]:
            label = t.get("name") or name
            lines.append("  [x] %-8s %s%s" % (name, t["path"], "  (%s)" % label if name == "browser" else ""))
        else:
            lines.append("  [ ] %-8s not found. %s" % (name, t["hint"]))
    lines.append("")
    lines.append("capabilities:")
    for cap, ok in rep["capabilities"].items():
        lines.append("  [%s] %s" % ("x" if ok else " ", cap))
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tools.py", description="Report which optional tools (Chromium-family browser, yt-dlp, ffmpeg, ffprobe, sips) metadump can use. Nothing is installed.")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args(argv)
    rep = detect()
    print(json.dumps(rep, indent=1) if args.json else format_report(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())

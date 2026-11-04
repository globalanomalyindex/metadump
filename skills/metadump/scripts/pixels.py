#!/usr/bin/env python3
"""PNG decode/encode and small pixel helpers on the Python 3.9 standard library.

Decodes every PNG color type (gray, RGB, palette, gray+alpha, RGBA) at 1, 2, 4,
8 and 16 bits (16-bit samples keep their high byte), with or without Adam7
interlacing and tRNS transparency. Output is always 8 bits per channel:
1 (gray), 2 (gray+alpha), 3 (RGB) or 4 (RGBA) channels. The image scripts use
this so palette sampling and frame-difference timing stay pure Python; other
formats are converted to PNG first (browser canvas, sips, or ffmpeg).

CLI:
    python3 pixels.py info FILE.png      width, height, channels, mean color
"""
import argparse
import itertools
import json
import operator
import struct
import sys
import zlib

SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
ADAM7 = [(0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8), (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2)]


class PNGError(ValueError):
    pass


class Image(object):
    """8-bit pixels, row-major, `channels` bytes per pixel."""

    __slots__ = ("width", "height", "channels", "pixels")

    def __init__(self, width, height, channels, pixels):
        self.width, self.height, self.channels = width, height, channels
        self.pixels = pixels

    def pixel(self, x, y):
        i = (y * self.width + x) * self.channels
        return tuple(self.pixels[i:i + self.channels])

    def __repr__(self):
        return "Image(%dx%d, %d ch)" % (self.width, self.height, self.channels)


# ---------------------------------------------------------------- filters

_MASKS = {}


def _masks(n):
    m = _MASKS.get(n)
    if m is None:
        m = (int.from_bytes(b"\x7f" * n, "little"), int.from_bytes(b"\x80" * n, "little"))
        if len(_MASKS) < 64:
            _MASKS[n] = m
    return m


def add_bytes(a, b):
    """Bytewise (a + b) mod 256 using big-int arithmetic (no carries between bytes)."""
    n = len(a)
    lo, hi = _masks(n)
    x = int.from_bytes(a, "little")
    y = int.from_bytes(b, "little")
    return (((x & lo) + (y & lo)) ^ ((x ^ y) & hi)).to_bytes(n, "little")


def _sub(line, bpp):
    out = bytearray(len(line))
    for c in range(bpp):
        sums = itertools.accumulate(line[c::bpp])
        out[c::bpp] = bytes(map(operator.and_, sums, itertools.repeat(255)))
    return out


def _avg(line, prev, bpp):
    cur = bytearray(line)
    for i in range(min(bpp, len(cur))):
        cur[i] = (cur[i] + (prev[i] >> 1)) & 255
    for i in range(bpp, len(cur)):
        cur[i] = (cur[i] + ((cur[i - bpp] + prev[i]) >> 1)) & 255
    return cur


def _paeth(line, prev, bpp):
    cur = bytearray(line)
    for i in range(min(bpp, len(cur))):
        cur[i] = (cur[i] + prev[i]) & 255
    for i in range(bpp, len(cur)):
        a = cur[i - bpp]
        b = prev[i]
        c = prev[i - bpp]
        pa = b - c if b >= c else c - b
        pb = a - c if a >= c else c - a
        pc = a + b - c - c
        if pc < 0:
            pc = -pc
        if pa <= pb and pa <= pc:
            pr = a
        elif pb <= pc:
            pr = b
        else:
            pr = c
        cur[i] = (cur[i] + pr) & 255
    return cur


def _unfilter(raw, pos, stride, rows, bpp):
    """Reconstruct `rows` scanlines starting at raw[pos]. Returns (bytes, new_pos)."""
    out = bytearray(stride * rows)
    prev = bytes(stride)
    for y in range(rows):
        if pos + 1 + stride > len(raw):
            raise PNGError("image data is truncated")
        ft = raw[pos]
        line = raw[pos + 1:pos + 1 + stride]
        pos += 1 + stride
        if ft == 0:
            cur = line
        elif ft == 1:
            cur = _sub(line, bpp)
        elif ft == 2:
            cur = add_bytes(line, prev)
        elif ft == 3:
            cur = _avg(line, prev, bpp)
        elif ft == 4:
            cur = _paeth(line, prev, bpp)
        else:
            raise PNGError("unknown filter type %d" % ft)
        out[y * stride:(y + 1) * stride] = cur
        prev = cur
    return out, pos


def _unpack(data, width, rows, stride, depth, channels, scale_gray):
    """Packed scanlines -> one 8-bit sample per channel."""
    if depth == 8:
        return data if stride == width * channels else b"".join(data[y * stride:y * stride + width * channels] for y in range(rows))
    if depth == 16:
        out = bytearray()
        for y in range(rows):
            out += data[y * stride:y * stride + width * channels * 2:2]
        return out
    per_byte = 8 // depth
    mask = (1 << depth) - 1
    mult = 255 // mask if scale_gray else 1
    n = width * channels
    out = bytearray()
    for y in range(rows):
        row = data[y * stride:(y + 1) * stride]
        vals = []
        for byte in row:
            for k in range(per_byte - 1, -1, -1):
                vals.append(((byte >> (k * depth)) & mask) * mult)
        out += bytes(vals[:n])
    return out


def png_size(data):
    """(width, height) from the IHDR chunk, or None if this is not a PNG."""
    if len(data) < 24 or data[:8] != SIGNATURE or data[12:16] != b"IHDR":
        return None
    return struct.unpack("!II", data[16:24])


def decode_png(data):
    """Decode PNG bytes into an 8-bit Image. Raises PNGError on anything malformed."""
    if data[:8] != SIGNATURE:
        raise PNGError("not a PNG file")
    pos = 8
    ihdr = None
    plte = None
    trns = None
    idat = []
    try:
        while pos + 8 <= len(data):
            length, kind = struct.unpack("!I4s", data[pos:pos + 8])
            body = data[pos + 8:pos + 8 + length]
            if len(body) < length:
                raise PNGError("chunk %r is truncated" % kind)
            pos += 12 + length
            if kind == b"IHDR":
                ihdr = struct.unpack("!IIBBBBB", body[:13])
            elif kind == b"PLTE":
                plte = body
            elif kind == b"tRNS":
                trns = body
            elif kind == b"IDAT":
                idat.append(body)
            elif kind == b"IEND":
                break
    except struct.error:
        raise PNGError("malformed chunk structure")
    if not ihdr or not idat:
        raise PNGError("missing IHDR or IDAT")
    width, height, depth, ctype, _comp, _filt, interlace = ihdr
    if ctype not in CHANNELS or depth not in (1, 2, 4, 8, 16) or width == 0 or height == 0:
        raise PNGError("unsupported color type %d / bit depth %d" % (ctype, depth))
    try:
        raw = zlib.decompress(b"".join(idat))
    except zlib.error as exc:
        raise PNGError("bad image data: %s" % exc)
    ch = CHANNELS[ctype]
    bits = ch * depth
    bpp = max(1, bits // 8)
    scale_gray = ctype in (0, 4)

    def stride_for(w):
        return (w * bits + 7) // 8

    if not interlace:
        rows, _pos = _unfilter(raw, 0, stride_for(width), height, bpp)
        samples = _unpack(rows, width, height, stride_for(width), depth, ch, scale_gray)
    else:
        samples = bytearray(width * height * ch)
        pos = 0
        for x0, y0, dx, dy in ADAM7:
            pw = (width - x0 + dx - 1) // dx if width > x0 else 0
            ph = (height - y0 + dy - 1) // dy if height > y0 else 0
            if not pw or not ph:
                continue
            rows, pos = _unfilter(raw, pos, stride_for(pw), ph, bpp)
            sub = _unpack(rows, pw, ph, stride_for(pw), depth, ch, scale_gray)
            for j in range(ph):
                y = y0 + j * dy
                for i in range(pw):
                    x = x0 + i * dx
                    s = (j * pw + i) * ch
                    d = (y * width + x) * ch
                    samples[d:d + ch] = sub[s:s + ch]
    return _apply_palette_and_trns(width, height, ctype, depth, ch, samples, plte, trns)


def _apply_palette_and_trns(width, height, ctype, depth, ch, samples, plte, trns):
    if ctype == 3:
        if not plte:
            raise PNGError("palette image without PLTE")
        n = len(plte) // 3
        alpha = list(trns or b"")
        if alpha:
            table = [bytes(plte[3 * i:3 * i + 3]) + bytes([alpha[i] if i < len(alpha) else 255]) for i in range(n)]
            out_ch = 4
        else:
            table = [bytes(plte[3 * i:3 * i + 3]) for i in range(n)]
            out_ch = 3
        blank = bytes(out_ch)
        return Image(width, height, out_ch, b"".join(table[i] if i < n else blank for i in samples))
    if trns and ctype in (0, 2):
        # One transparent color: expand to gray+alpha / RGBA.
        if ctype == 0:
            key = struct.unpack("!H", trns[:2])[0]
            key = key >> 8 if depth == 16 else key * (255 // ((1 << depth) - 1)) if depth < 8 else key
            out = bytearray()
            for v in samples:
                out += bytes((v, 0 if v == key else 255))
            return Image(width, height, 2, out)
        r, g, b = struct.unpack("!3H", trns[:6])
        if depth == 16:
            r, g, b = r >> 8, g >> 8, b >> 8
        key = bytes((r, g, b))
        out = bytearray()
        for i in range(0, len(samples), 3):
            px = bytes(samples[i:i + 3])
            out += px + (b"\x00" if px == key else b"\xff")
        return Image(width, height, 4, out)
    return Image(width, height, ch, bytes(samples))


# ---------------------------------------------------------------- encode

def _chunk(kind, body):
    return struct.pack("!I", len(body)) + kind + body + struct.pack("!I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def encode_png(width, height, channels, pixels, level=6):
    """8-bit gray/gray+alpha/RGB/RGBA bytes -> PNG bytes (filter 0 on every row)."""
    ctype = {1: 0, 2: 4, 3: 2, 4: 6}[channels]
    stride = width * channels
    raw = b"".join(b"\x00" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height))
    return (SIGNATURE + _chunk(b"IHDR", struct.pack("!IIBBBBB", width, height, 8, ctype, 0, 0, 0))
            + _chunk(b"IDAT", zlib.compress(raw, level)) + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- conversions

def to_rgb(img, background=(255, 255, 255)):
    """Drop alpha by compositing on `background`; expand gray to RGB."""
    ch = img.channels
    p = img.pixels
    if ch == 3:
        return img
    if ch == 1:
        return Image(img.width, img.height, 3, bytes(v for v in p for _ in range(3)))
    out = bytearray()
    br, bg, bb = background
    if ch == 2:
        for i in range(0, len(p), 2):
            v, a = p[i], p[i + 1]
            out += bytes(((v * a + br * (255 - a)) // 255,) * 3)
    else:
        for i in range(0, len(p), 4):
            r, g, b, a = p[i], p[i + 1], p[i + 2], p[i + 3]
            if a == 255:
                out += bytes((r, g, b))
            else:
                out += bytes(((r * a + br * (255 - a)) // 255, (g * a + bg * (255 - a)) // 255, (b * a + bb * (255 - a)) // 255))
    return Image(img.width, img.height, 3, bytes(out))


def to_gray(img):
    """Luma (ITU-R 601 weights) as a 1-channel image; alpha is composited on white first."""
    if img.channels == 1:
        return img
    if img.channels == 2:
        img = to_rgb(img)
    if img.channels == 4:
        img = to_rgb(img)
    p = img.pixels
    rs = p[0::3]
    gs = p[1::3]
    bs = p[2::3]
    return Image(img.width, img.height, 1, bytes((299 * r + 587 * g + 114 * b + 500) // 1000 for r, g, b in zip(rs, gs, bs)))


def downscale(img, max_width):
    """Box-average a 1-channel image by an integer factor so width <= max_width."""
    if img.channels != 1:
        img = to_gray(img)
    f = -(-img.width // max_width) if max_width else 1
    if f <= 1:
        return img
    ow, oh = img.width // f, img.height // f
    w = img.width
    p = img.pixels
    out = bytearray()
    n = f * f
    for oy in range(oh):
        acc = [0] * (ow * f)
        for k in range(f):
            row = p[(oy * f + k) * w:(oy * f + k) * w + ow * f]
            acc = list(map(operator.add, acc, row))
        for ox in range(ow):
            out.append((sum(acc[ox * f:(ox + 1) * f]) + n // 2) // n)
    return Image(ow, oh, 1, bytes(out))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="pixels.py", description="Stdlib PNG decoder: print basic facts about a PNG file.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("info", help="width, height, channels and mean RGB of a PNG")
    i.add_argument("file")
    args = ap.parse_args(argv)
    with open(args.file, "rb") as f:
        try:
            img = decode_png(f.read())
        except PNGError as exc:
            print(json.dumps({"ok": False, "reason": "png_error", "message": str(exc)}))
            return 1
    rgb = to_rgb(img)
    n = rgb.width * rgb.height
    mean = [sum(rgb.pixels[c::3]) // n for c in range(3)]
    print(json.dumps({"ok": True, "width": img.width, "height": img.height, "channels": img.channels,
                      "mean_hex": "#%02X%02X%02X" % tuple(mean)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())

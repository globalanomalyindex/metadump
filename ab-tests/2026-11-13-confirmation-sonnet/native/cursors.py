"""Turn the system's own macOS cursor art (vector PDFs in HIServices) into SVGs for the recorder.

Python 3.9 stdlib only. Reads each cursor.pdf content stream, replays its fill paths (m l c v y h re,
q/Q/cm, rg/g) into SVG paths in the PDF's point space, and copies hotspot and shadow from info.plist.
The plain arrow has no folder of its own (WindowServer keeps it as a raw bitmap), so it is taken from
the `contextualmenu` cursor, whose first two fills are the arrow (white rim, black body) before the menu
badge. Usage: python3 cursors.py [out_dir]   ->  arrow.svg, pointinghand.svg, ibeam.svg, cursors.json
"""
import base64, json, plistlib, re, sys, zlib
from pathlib import Path

SRC = Path('/System/Library/Frameworks/ApplicationServices.framework/Versions/A/Frameworks/'
           'HIServices.framework/Versions/A/Resources/cursors')


def page_and_content(pdf):
    b = pdf.read_bytes()
    objs = {int(m.group(1)): m.group(2) for m in re.finditer(rb'(\d+) 0 obj\s*(.*?)endobj', b, re.S)}
    page = next(v for v in objs.values() if b'/Type/Page' in v and b'/Contents' in v)
    box = [float(x) for x in re.search(rb'/MediaBox\[([^\]]*)\]', page).group(1).split()]
    cid = int(re.search(rb'/Contents (\d+) 0 R', page).group(1))
    m = re.match(rb'\s*<<(.*?)>>\s*stream\r?\n(.*)endstream', objs[cid], re.S)
    d, s = m.group(1), m.group(2)
    if b'ASCII85' in d:
        s = base64.a85decode(s.strip().rstrip(b'~>').replace(b'\r', b'').replace(b'\n', b''))
    if b'Flate' in d:
        s = zlib.decompress(s)
    return box, s.decode('latin1')


def fills(content, height):
    """Yield (svg_path_d, '#rrggbb') for every filled path, in paint order."""
    toks = re.findall(r'/[^\s/\[\]<>()]+|\[|\]|<<|>>|-?\d*\.?\d+(?:e-?\d+)?|[A-Za-z*\'"]+', content)
    ctm, stack, nums, d, color = [1, 0, 0, 1, 0, 0], [], [], [], '#000000'
    cur = (0, 0)

    def pt(x, y):
        a, b_, c, dd, e, f = ctm
        X, Y = a * x + c * y + e, b_ * x + dd * y + f
        return f'{X:.3f} {height - Y:.3f}'
    for t in toks:
        if re.fullmatch(r'-?\d*\.?\d+(?:e-?\d+)?', t):
            nums.append(float(t)); continue
        n = nums; nums = []
        if t == 'q': stack.append(ctm[:])
        elif t == 'Q': ctm = stack.pop()
        elif t == 'cm':
            a, b_, c, dd, e, f = n; A = ctm
            ctm = [a * A[0] + b_ * A[2], a * A[1] + b_ * A[3], c * A[0] + dd * A[2], c * A[1] + dd * A[3],
                   e * A[0] + f * A[2] + A[4], e * A[1] + f * A[3] + A[5]]
        elif t == 'm': d.append('M' + pt(*n)); cur = n
        elif t == 'l': d.append('L' + pt(*n)); cur = n
        elif t == 'c': d.append('C' + pt(n[0], n[1]) + ' ' + pt(n[2], n[3]) + ' ' + pt(n[4], n[5])); cur = n[4:]
        elif t == 'v': d.append('C' + pt(*cur) + ' ' + pt(n[0], n[1]) + ' ' + pt(n[2], n[3])); cur = n[2:]
        elif t == 'y': d.append('C' + pt(n[0], n[1]) + ' ' + pt(n[2], n[3]) + ' ' + pt(n[2], n[3])); cur = n[2:]
        elif t == 'h': d.append('Z')
        elif t == 're':
            x, y, w, h = n
            d.append('M' + pt(x, y) + 'L' + pt(x + w, y) + 'L' + pt(x + w, y + h) + 'L' + pt(x, y + h) + 'Z')
        elif t == 'rg': color = '#%02x%02x%02x' % tuple(round(v * 255) for v in n)
        elif t == 'g': color = '#%02x%02x%02x' % ((round(n[0] * 255),) * 3)
        elif t in ('f', 'f*', 'F', 'B', 'b'):
            yield ''.join(d), color, ('evenodd' if t == 'f*' else 'nonzero'); d = []
        elif t in ('n', 'S', 's'): d = []


def convert(name, keep=None):
    box, content = page_and_content(SRC / name / 'cursor.pdf')
    w, h = box[2] - box[0], box[3] - box[1]
    ps = list(fills(content, h))
    if keep: ps = ps[:keep]
    info = plistlib.loads((SRC / name / 'info.plist').read_bytes())
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">'
           + ''.join(f'<path d="{d}" fill="{c}" fill-rule="{r}"/>' for d, c, r in ps) + '</svg>')
    return svg, {'w': w, 'h': h, 'hotx': info['hotx'], 'hoty': info['hoty'], 'blur': info.get('blur', 0),
                 'shadow': info.get('shadowcolor', [0, 0, 0, 0]), 'shadowy': info.get('shadowoffsety', 0),
                 'source': str(SRC / name / 'cursor.pdf')}


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent)
    meta = {}
    for key, name, keep in [('arrow', 'contextualmenu', 2), ('pointinghand', 'pointinghand', None), ('ibeam', 'ibeamhorizontal', None)]:
        svg, m = convert(name, keep)
        (out / f'{key}.svg').write_text(svg)
        meta[key] = m
    (out / 'cursors.json').write_text(json.dumps(meta, indent=1))
    print(json.dumps({k: {x: v[x] for x in ('w', 'h', 'hotx', 'hoty')} for k, v in meta.items()}))

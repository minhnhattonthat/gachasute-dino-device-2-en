"""Condensed VWF font for names that overflow their menu window (asm/vwf.asm [narrow] mode).

Hand-drawn: caps 6 px tall (rows 1-6), x-height 4 (rows 3-6), descenders on row 7. '#' = ink.
Width = drawn width + 1 gap column. Keys are the same characters vwf_font.CHARMAP maps.

    python -X utf8 tools/narrow_font.py render -> work/narrow_font.png
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

_ART = r"""
A
.#.
#.#
#.#
###
#.#
#.#
B
##.
#.#
##.
#.#
#.#
##.
C
.##
#..
#..
#..
#..
.##
D
##.
#.#
#.#
#.#
#.#
##.
E
###
#..
##.
#..
#..
###
F
###
#..
##.
#..
#..
#..
G
.##
#..
#..
#.#
#.#
.##
H
#.#
#.#
###
#.#
#.#
#.#
I
###
.#.
.#.
.#.
.#.
###
J
..#
..#
..#
..#
#.#
.#.
K
#.#
#.#
##.
#.#
#.#
#.#
L
#..
#..
#..
#..
#..
###
M
#...#
##.##
#.#.#
#...#
#...#
#...#
N
#..#
##.#
#.##
#..#
#..#
#..#
O
.##.
#..#
#..#
#..#
#..#
.##.
P
##.
#.#
#.#
##.
#..
#..
Q
.##.
#..#
#..#
#..#
#.#.
.#.#
R
##.
#.#
#.#
##.
#.#
#.#
S
.##
#..
.#.
..#
..#
##.
T
###
.#.
.#.
.#.
.#.
.#.
U
#.#
#.#
#.#
#.#
#.#
.#.
V
#.#
#.#
#.#
#.#
.#.
.#.
W
#...#
#...#
#...#
#.#.#
##.##
#...#
X
#.#
#.#
.#.
.#.
#.#
#.#
Y
#.#
#.#
.#.
.#.
.#.
.#.
Z
###
..#
.#.
.#.
#..
###
a
...
...
.##
#.#
#.#
.##
b
#..
#..
##.
#.#
#.#
##.
c
...
...
.##
#..
#..
.##
d
..#
..#
.##
#.#
#.#
.##
e
...
...
.#.
###
#..
.##
f
.#
#.
##
#.
#.
#.
g
...
...
.##
#.#
.##
..#
##.
h
#..
#..
##.
#.#
#.#
#.#
i
#
.
#
#
#
#
j
.#
..
.#
.#
.#
.#
#.
k
#..
#..
#.#
##.
#.#
#.#
l
#
#
#
#
#
#
m
.....
.....
####.
#.#.#
#.#.#
#.#.#
n
...
...
##.
#.#
#.#
#.#
o
...
...
.#.
#.#
#.#
.#.
p
...
...
##.
#.#
#.#
##.
#..
q
...
...
.##
#.#
#.#
.##
..#
r
..
..
.#
#.
#.
#.
s
...
...
.##
##.
..#
##.
t
.#.
.#.
###
.#.
.#.
..#
u
...
...
#.#
#.#
#.#
.##
v
...
...
#.#
#.#
#.#
.#.
w
.....
.....
#...#
#.#.#
#.#.#
.#.#.
x
...
...
#.#
.#.
.#.
#.#
y
...
...
#.#
#.#
.##
..#
##.
z
...
...
###
.#.
#..
###
0
.#.
#.#
#.#
#.#
#.#
.#.
1
.#
##
.#
.#
.#
.#
2
##.
..#
..#
.#.
#..
###
3
##.
..#
.#.
..#
..#
##.
4
#.#
#.#
###
..#
..#
..#
5
###
#..
##.
..#
..#
##.
6
.##
#..
##.
#.#
#.#
.#.
7
###
..#
..#
.#.
.#.
.#.
8
.#.
#.#
.#.
#.#
#.#
.#.
9
.#.
#.#
#.#
.##
..#
##.
-
..
..
..
##
..
..
.
.
.
.
.
.
#
'
#
#
.
.
.
.
!
#
#
#
#
.
#
?
##.
..#
.#.
.#.
...
.#.
&
.#..
#.#.
.#..
#.##
#.#.
.#.#
/
..#
..#
.#.
.#.
#..
#..
+
...
.#.
###
.#.
...
...
(
.#
#.
#.
#.
#.
.#
)
#.
.#
.#
.#
.#
#.
"""

SPACE_W = 1  # + the previous glyph's gap column = 2 px between words (letters get 1)


def glyphs() -> dict[str, tuple[list[int], int]]:
    """char -> (8 row bitmasks, MSB = left; width incl. gap)."""
    out = {}
    lines = _ART.strip('\n').split('\n')
    i = 0
    while i < len(lines):
        ch = lines[i]
        n = 7 if ch in 'gjpqy' else 6  # descender letters have a 7th row
        art = lines[i + 1:i + 1 + n]
        assert all(r and set(r) <= {'.', '#'} for r in art), (ch, art)
        i += 1 + n
        rows = [0] + [sum(0x80 >> x for x, c in enumerate(r) if c == '#') for r in art]
        rows = (rows + [0] * 8)[:8]
        out[ch] = (rows, max(len(r) for r in art) + 1)
    out[' '] = ([0] * 8, SPACE_W)
    return out


def build(normal_glyphs: bytes, normal_widths: bytes) -> tuple[bytes, bytes]:
    """256-glyph tables in VWF code order; codes without a narrow drawing reuse the normal glyph."""
    from vwf_font import CHARMAP
    g, w = bytearray(normal_glyphs), bytearray(normal_widths)
    for ch, (rows, width) in glyphs().items():
        if ch in CHARMAP:
            c = CHARMAP[ch][-1]
            g[c * 8:c * 8 + 8] = bytes(rows)
            w[c] = width
    return bytes(g), bytes(w)


def px(s: str) -> int:
    """Visible width of plain English text in the narrow font (tags ignored; the last glyph's blank gap column,
    which only ever holds shadow, is not counted)."""
    import re
    g = glyphs()
    w = sum(g[ch][1] if ch in g else 8 for ch in re.sub(r'\[[^\]]*\]', '', s))
    return max(w - 1, 0)


def render(text: str, out: Path, zoom: int = 4):
    from PIL import Image
    g = glyphs()
    w = sum(g[c][1] for c in text)
    im = Image.new('L', (w + 2, 10), 255)
    x = 1
    for c in text:
        rows, cw = g[c]
        for y, r in enumerate(rows):
            for dx in range(cw):
                if r & (0x80 >> dx):
                    im.putpixel((x + dx, y + 1), 0)
        x += cw
    im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save(out)
    return w


if __name__ == '__main__':
    import sys
    if sys.argv[1:2] == ['render']:
        s = 'Kite Core Grosso Napalm Chain Gun Elb Meta Body F Thunder Shoulder Earth Ray Shield 1234567890 ' \
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz Urchin Bomber! (D-Burst) x20 +10 & ?/.\''
        print(render(s, ROOT / 'work/narrow_font.png'), 'px')

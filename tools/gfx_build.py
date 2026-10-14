"""Graphics text in English (docs/re/graphics.md): title logo, title OBJ sheet, intro logo, name-entry buttons.

    python -X utf8 tools/gfx_build.py draw   -> regenerate gfx/*.png from rom/orig.gba (lettering drawn in code)
    build.py: apply(rom) reads gfx/*.png -> tiles -> ECD blocks at GFX_BASE.., archive entries repointed

gfx/*.png are indexed PNGs in the game's own palette (index = colour number; index 0 = transparent):
  title_logo.png  240x160, 8bpp BG2 (1/2982 IMG, 1/2984 SCR; palette 1/2983)
  title_obj.png   256x152, OBJ sheet 1/2995, 4bpp; pixel = palette bank * 16 + colour (bank only for viewing)
  intro_logo.png  512x160, BG0 maps 1/3021 (left half) + 1/3022 (right half), tiles 1/3019 (4bpp, shared with 1/3020)
  ui_sheet.png    256x64, UI sheet 1/2966 (4bpp, shown in bank 1); name-entry button bars 1/2972-2974 widened in code
  catalog_sheet.png 2/1260 (My Catalog / Catalog Order side tabs), shop_sheet.png 2/1282 (SELECT footer),
  setdev_glyphs.png 1/3119 (Set Devices slot-name letters; PAT 1/3120 spells the names)
Editing a PNG by hand is fine (keep the palette, no dithering); `draw` overwrites them.
"""
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gfxcodec as G  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GFX = ROOT / 'gfx'
GFX_BASE, GFX_END = 0x7E3000, 0x800000  # build.py: text 0x400000-0x7DFFFF, fonts/VWF code 0x7E0000-0x7E2FFF

# ---------------------------------------------------------------- tiles, palettes, masks

def tiles4(data: bytes) -> list[bytes]:
    return [bytes(v for b in data[k:k + 32] for v in (b & 15, b >> 4)) for k in range(0, len(data), 32)]


def pack4(t: bytes) -> bytes:
    return bytes(t[i] | t[i + 1] << 4 for i in range(0, 64, 2))


def plt_rgb(p: bytes) -> list[tuple]:
    n = struct.unpack_from('<H', p, 4)[0]
    return [((c & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31, (c >> 10 & 31) * 255 // 31)
            for c in struct.unpack_from(f'<{n}H', p, 8)]


def palette_flat(rgb: list[tuple]) -> list[int]:
    return [v for c in (rgb + [(0, 0, 0)] * 256)[:256] for v in c]


def tile_at(im: Image.Image, tx: int, ty: int) -> bytes:
    return bytes(im.getpixel((tx * 8 + x, ty * 8 + y)) for y in range(8) for x in range(8))


def flip(t: bytes, h: bool, v: bool) -> bytes:
    return bytes(t[(7 - y if v else y) * 8 + (7 - x if h else x)] for y in range(8) for x in range(8))


def render_map(tiles, entries, w, h, base=0) -> Image.Image:
    im = Image.new('P', (w * 8, h * 8))
    for ty in range(h):
        for tx in range(w):
            e = entries[ty * w + tx]
            k = (e & 0x3FF) - base
            t = flip(tiles[k], e & 0x400, e & 0x800) if 0 <= k < len(tiles) else bytes(64)
            for i, c in enumerate(t):
                im.putpixel((tx * 8 + i % 8, ty * 8 + i // 8), c)
    return im


def dilate(m: set, n: int = 1) -> set:
    for _ in range(n):
        m = {(x + dx, y + dy) for x, y in m for dx in (-1, 0, 1) for dy in (-1, 0, 1)}
    return m


def shear(m: set, h: int, k: int) -> set:
    """Italic: row y moves right by (h - 1 - y) // k."""
    return {(x + (h - 1 - y) // k, y) for x, y in m}


def scale(m: set, s: int) -> set:
    return {(x * s + i, y * s + j) for x, y in m for i in range(s) for j in range(s)}


def text_mask(text: str, font: dict, gap: int, space: int) -> tuple[set, int, int]:
    """'#' art glyphs -> pixel set; letters `gap` apart, ' ' = `space` px. Returns (mask, width, height)."""
    h = len(next(iter(font.values())))
    m, x = set(), 0
    for i, ch in enumerate(text):
        if ch == ' ':
            x += space
            continue
        if i and text[i - 1] != ' ':
            x += gap
        rows = font[ch]
        m |= {(x + c, y) for y in range(h) for c, v in enumerate(rows[y]) if v == '#'}
        x += len(rows[0])
    return m, x, h


def paint(im: Image.Image, m, c: int, ox: int = 0, oy: int = 0) -> None:
    for x, y in m:
        if 0 <= x + ox < im.width and 0 <= y + oy < im.height:
            im.putpixel((x + ox, y + oy), c)


def poly(pts) -> set:
    t = Image.new('1', (256, 256))
    ImageDraw.Draw(t).polygon(pts, fill=1)
    return {(x, y) for x in range(256) for y in range(256) if t.getpixel((x, y))}


def art(s: str) -> dict:
    """'X:' header lines followed by '#'/'.' rows -> {char: rows}."""
    out, key = {}, None
    for line in s.strip().splitlines():
        line = line.strip()
        if line.endswith(':') and len(line) == 2:
            key = line[0]
            out[key] = []
        elif line:
            out[key].append(line)
    return out

# ---------------------------------------------------------------- fonts

# Title logo upper line, DRAGON / PHOENIX sprites: 12 rows, 2 px stems, 3 px counters.
BOLD12 = art('''
G:
.######
#######
##.....
##.....
##.....
##..###
##..###
##...##
##...##
##...##
#######
.######
A:
.#####.
#######
##...##
##...##
##...##
#######
#######
##...##
##...##
##...##
##...##
##...##
C:
.######
#######
##.....
##.....
##.....
##.....
##.....
##.....
##.....
##.....
#######
.######
H:
##...##
##...##
##...##
##...##
##...##
#######
#######
##...##
##...##
##...##
##...##
##...##
S:
.######
#######
##.....
##.....
##.....
######.
.######
.....##
.....##
.....##
#######
######.
U:
##...##
##...##
##...##
##...##
##...##
##...##
##...##
##...##
##...##
##...##
#######
.#####.
T:
######
######
..##..
..##..
..##..
..##..
..##..
..##..
..##..
..##..
..##..
..##..
E:
######
######
##....
##....
##....
#####.
#####.
##....
##....
##....
######
######
!:
##
##
##
##
##
##
##
##
..
..
##
##
D:
######.
#######
##...##
##...##
##...##
##...##
##...##
##...##
##...##
##...##
#######
######.
R:
######.
#######
##...##
##...##
##...##
#######
######.
##.##..
##..##.
##..##.
##...##
##...##
O:
.#####.
#######
##...##
##...##
##...##
##...##
##...##
##...##
##...##
##...##
#######
.#####.
N:
##...##
###..##
###..##
####.##
##.#.##
##.#.##
##.#.##
##.####
##..###
##..###
##...##
##...##
P:
######.
#######
##...##
##...##
##...##
#######
######.
##.....
##.....
##.....
##.....
##.....
I:
##
##
##
##
##
##
##
##
##
##
##
##
X:
##...##
##...##
##...##
.##.##.
.##.##.
..###..
..###..
.##.##.
.##.##.
##...##
##...##
##...##
''')


def bold16() -> dict:
    """Title logo lower line: 16 rows, 3 px stems and bars, 11 px wide round letters."""
    h, w, s = 16, 11, 3

    def grid(width):
        return [['.'] * width for _ in range(h)]

    def box(g, x0, x1, y0, y1):
        for y in range(y0, y1):
            for x in range(x0, x1):
                g[y][x] = '#'
    out = {}
    g = grid(w); box(g, 0, s, 0, h); box(g, 0, w - 2, 0, s); box(g, 0, w - 2, h - s, h); box(g, w - s, w, 2, h - 2)
    box(g, w - 2, w - 1, 1, h - 1); out['D'] = g
    g = grid(w); box(g, 0, s, 0, h); box(g, w - s, w, 0, h); box(g, 0, w, 0, s); box(g, 0, w, h - s, h)
    for x, y in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        g[y][x] = '.'
    out['O'] = g
    mid = (h - s) // 2
    g = grid(w - 2); box(g, 0, s, 0, h); box(g, 0, w - 2, 0, s); box(g, 0, w - 2, h - s, h); box(g, 0, w - 4, mid, mid + s)
    out['E'] = g
    g = grid(w - 2); box(g, 0, s, 0, h); box(g, 0, w - 2, 0, s); box(g, 0, w - 2, h - s, h)
    g[0][0] = g[h - 1][0] = '.'
    out['C'] = g
    out['I'] = [['#'] * s for _ in range(h)]
    g = grid(w); box(g, 0, s, 0, h); box(g, w - s, w, 0, h)
    for y in range(h):  # diagonal from the top-left stem to the bottom-right stem
        x = s - 1 + (y * (w - 2 * s + 1)) // (h - 1)
        box(g, x, min(w, x + s), y, y + 1)
    out['N'] = g
    g = grid(w)
    for y in range(h):  # two stems meeting in a point
        o = max(0, (y - 6) * (w // 2 - s // 2 - 1) // (h - 7))
        box(g, o, o + s, y, y + 1); box(g, w - o - s, w - o, y, y + 1)
    out['V'] = g
    return {k: [''.join(r) for r in v] for k, v in out.items()}


# Title menu (device screen): 1 px strokes like the original kana, caps 7 rows, x-height 5 (rows 2-6).
MENU = art('''
N:
#...#
##..#
##..#
#.#.#
#..##
#..##
#...#
G:
.###.
#...#
#....
#.###
#...#
#...#
.####
C:
.###.
#...#
#....
#....
#....
#...#
.###.
L:
#...
#...
#...
#...
#...
#...
####
e:
....
....
.##.
#..#
####
#...
.###
w:
.....
.....
#...#
#...#
#.#.#
#.#.#
.#.#.
a:
....
....
.##.
...#
.###
#..#
.###
m:
.....
.....
####.
#.#.#
#.#.#
#.#.#
#.#.#
o:
....
....
.##.
#..#
#..#
#..#
.##.
n:
....
....
###.
#..#
#..#
#..#
#..#
t:
...
.#.
###
.#.
.#.
.#.
..#
i:
#
.
#
#
#
#
#
u:
....
....
#..#
#..#
#..#
#..#
.###
k:
#...
#...
#..#
#.#.
##..
#.#.
#..#
''')

# Name-entry button labels: 5 rows like the original "ABC".
LABEL = art('''
H:
#.#
#.#
###
#.#
#.#
I:
#
#
#
#
#
R:
##.
#.#
##.
#.#
#.#
A:
.#.
#.#
###
#.#
#.#
G:
.##
#..
#.#
#.#
.##
N:
#..#
##.#
#.##
#..#
#..#
K:
#.#
#.#
##.
#.#
#.#
T:
###
.#.
.#.
.#.
.#.
S:
.##
#..
.#.
..#
##.
E:
###
#..
##.
#..
###
L:
#..
#..
#..
#..
###
C:
.##
#..
#..
#..
.##
U:
#.#
#.#
#.#
#.#
.##
::
.
#
.
#
.
''')

# My Catalog / Catalog Order side tabs: 6 rows, 1 px strokes, white on the tab's dark box (18 px inside).
TAB = art('''
D:
##.
#.#
#.#
#.#
#.#
##.
I:
#
#
#
#
#
#
N:
#..#
##.#
##.#
#.##
#.##
#..#
O:
.#.
#.#
#.#
#.#
#.#
.#.
H:
#.#
#.#
###
#.#
#.#
#.#
E:
###
#..
##.
#..
#..
###
A:
.#.
#.#
#.#
###
#.#
#.#
R:
##.
#.#
#.#
##.
#.#
#.#
G:
.##
#..
#..
#.#
#.#
.##
T:
###
.#.
.#.
.#.
.#.
.#.
L:
#..
#..
#..
#..
#..
###
F:
###
#..
##.
#..
#..
#..
B:
##.
#.#
##.
#.#
#.#
##.
Y:
#.#
#.#
.#.
.#.
.#.
.#.
''')

# Set Devices slot name (OBJ, typed one 8x8 glyph tile per letter): 5x6 caps, colour 1.
SLOT = art('''
H:
#...#
#...#
#####
#...#
#...#
#...#
E:
#####
#....
####.
#....
#....
#####
A:
.###.
#...#
#...#
#####
#...#
#...#
D:
####.
#...#
#...#
#...#
#...#
####.
B:
####.
#...#
####.
#...#
#...#
####.
O:
.###.
#...#
#...#
#...#
#...#
.###.
Y:
#...#
#...#
.#.#.
..#..
..#..
..#..
N:
#...#
##..#
#.#.#
#..##
#...#
#...#
R:
####.
#...#
#...#
####.
#..#.
#...#
I:
.###.
..#..
..#..
..#..
..#..
.###.
L:
#....
#....
#....
#....
#....
#####
F:
#####
#....
####.
#....
#....
#....
G:
.###.
#....
#.###
#...#
#...#
.###.
T:
#####
..#..
..#..
..#..
..#..
..#..
''')

# Title "© 2003 ROCKET COMPANY": letters missing from the sheet's PUSH START BUTTON font (7x6 fill, shared outline).
CHUNKY_NEW = art('''
C:
#######
###.###
###....
###....
###.###
#######
K:
###.###
###.##.
#####..
#####..
###.##.
###.###
E:
#######
###....
######.
######.
###....
#######
M:
##...##
###.###
#######
##.#.##
##...##
##...##
Y:
###.###
###.###
#######
.#####.
..###..
..###..
''')
CHUNKY_ROWS = [0xF, 0xF, 0xE, 0x9, 0xF, 0xF]       # fill colour per row (bank 2), as PUSH START BUTTON
CHUNKY_SHEET_X = {'P': 7, 'U': 15, 'S': 23, 'H': 31, 'T': 55, 'A': 63, 'R': 71, 'B': 95, 'O': 127, 'N': 135}

# ---------------------------------------------------------------- drawing

def draw_line(im, text, font, ox, oy, k, fills, outline, bands=(), gap=2, space=8, s=1):
    """Silver/white letters (fill colour per row), 1 px outline, then halo bands (inner first)."""
    m, w, h = text_mask(text, font, gap, space)
    m = shear(scale(m, s), h * s, k)
    for i, c in reversed(list(enumerate(bands))):
        paint(im, dilate(m, i + 2), c, ox, oy)
    paint(im, dilate(m, 1), outline, ox, oy)
    for x, y in m:
        im.putpixel((x + ox, y + oy), fills[y * len(fills) // (h * s)])
    return m


def logo_index(rom) -> Image.Image:
    tiles = [bytes(G.load(rom, 1, 2982)[8 + i:8 + i + 64]) for i in range(0, 16384, 64)]
    scr = G.load(rom, 1, 2984)
    return render_map(tiles, struct.unpack_from('<600H', scr, 8), 30, 20)


def draw_title_logo(rom) -> Image.Image:
    im = logo_index(rom)
    for x in range(91, 107):  # ガ's dakuten above the upper plate -> plain plate top rim
        for y in range(46, 53):
            im.putpixel((x, y), 0)
        im.putpixel((x, 53), 0x1A)
        im.putpixel((x, 54), 0x3A)
    for x in range(40, 167):  # lower plate bottom rim without the old letters' tails
        for y, c in ((96, 0x51), (97, 0x58), (98, 0x69)):
            im.putpixel((x, y), c)
    paint(im, poly([(83, 55), (173, 55), (164, 71), (75, 71)]), 0x13)            # upper plate: red
    for x in range(76, 165):                                                     # its bottom rim
        im.putpixel((x, 72), 0x0B)
        im.putpixel((x, 73), 0x3A)
    paint(im, poly([(41, 77), (76, 77), (76, 74), (164, 74), (170, 77), (168, 95), (37, 95)]), 0x1A)  # lower plate
    for y in range(99, 106):  # the small romanised "DINO DEVICE" strip: the big line now says it
        for x in range(60, 161):
            im.putpixel((x, y), 0x1B if y == 99 else 0x1A)
    up_fill = [0x3A] * 5 + [0x38, 0x38, 0x37, 0x35, 0x35, 0x33, 0x33]
    lo_fill = [0x3A] * 6 + [0x38, 0x38, 0x37, 0x37, 0x35, 0x33, 0x31, 0x30, 0x2F, 0x2E]
    draw_line(im, 'GACHASUTE!', BOLD12, 80, 58, 2, up_fill, 0x1B, gap=2)
    draw_line(im, 'DINO DEVICE', bold16(), 45, 79, 3, lo_fill, 0x1A, (0x57, 0x6D), gap=2)
    im.putpalette(palette_flat(plt_rgb(G.load(rom, 1, 2983))))
    return im

# -- title OBJ sheet


def pat_parse(p: bytes) -> list[list[list[int]]]:
    n = struct.unpack_from('<H', p, 4)[0]
    offs = struct.unpack_from(f'<{n}I', p, 8)
    out = []
    for o in offs:
        cnt = struct.unpack_from('<H', p, o)[0]
        out.append([list(struct.unpack_from('<Hhhh', p, o + 2 + 8 * i)) for i in range(cnt)])
    return out


def pat_build(pats) -> bytes:
    head = 8 + 4 * len(pats)
    body, offs = b'', []
    for pat in pats:
        offs.append(head + len(body))
        body += struct.pack('<H', len(pat)) + b''.join(struct.pack('<HhhH', c, x, y, t & 0xFFFF) for c, x, y, t in pat)
    out = b'PAT\0' + struct.pack('<HH', len(pats), 0) + struct.pack(f'<{len(pats)}I', *offs) + body
    return out + bytes(-len(out) % 4)


OBJ_ROWS = 19   # original 17 + 2 new rows for the © line and "Continue"
SPR = {0x00: (8, 8), 0x15: (16, 16), 0x2A: (32, 32), 0x3F: (64, 64), 0x41: (16, 8), 0x52: (32, 8), 0x66: (32, 16),
       0x7B: (64, 32), 0x84: (8, 16), 0x98: (8, 32), 0xA9: (16, 32)}


def obj_patterns(rom) -> list:
    """Title PAT 1/2997 with the © line (pattern 3) and "Continue" (pattern 6) moved to the new sheet rows."""
    pats = pat_parse(G.load(rom, 1, 2997))
    pats[3] = [[0x2052, -86 + 32 * i, -8, 0x2000 | (17 * 32 + 4 * i)] for i in range(6)]
    pats[6] = [[0x2066, -24, -8, 0x2000 | (17 * 32 + 24)], [0x2015, 8, -8, 0x2000 | (17 * 32 + 28)]]
    return pats


def obj_banks(pats) -> dict:
    banks = {}
    for pat in pats:
        for code, _x, _y, t in pat:
            w, h = SPR.get(code & 0xFF, (8, 8))
            for dy in range(h // 8):
                for dx in range(w // 8):
                    banks[(t & 0x3FF) + dy * 32 + dx] = (t >> 12) & 3
    return banks


def draw_title_obj(rom) -> Image.Image:
    sheet = tiles4(G.load(rom, 1, 2995)[8:])
    pats = obj_patterns(rom)
    banks = obj_banks(pats)
    im = Image.new('P', (256, OBJ_ROWS * 8))
    for k, t in enumerate(sheet):
        for i, c in enumerate(t):
            im.putpixel((k % 32 * 8 + i % 8, k // 32 * 8 + i // 8), c)

    def clear(c0, r0, c1, r1):
        for y in range(r0 * 8, r1 * 8):
            for x in range(c0 * 8, c1 * 8):
                im.putpixel((x, y), 0)
    src = im.copy()
    # DRAGON (bank 0, rows 13-15 cols 10-16) and PHOENIX (bank 1, rows 13-15 cols 0-8): italic, gradient, outline
    clear(10, 13, 17, 16)
    draw_line(im, 'DRAGON', BOLD12, 81, 110, 2, [0x1, 0x1, 0xF, 0xF, 0xE, 0xE, 0xD, 0xD, 0xC, 0xC, 0x9, 0xA], 0x7, gap=1)
    clear(0, 13, 10, 16)
    draw_line(im, 'PHOENIX', BOLD12, 10, 110, 2, [0x2, 0x2, 0x8, 0x8, 0x9, 0x9, 0xB, 0xB, 0xE, 0xE, 0x3, 0x3], 0x1, gap=2)
    # © 2003 ROCKET COMPANY -> row 17 (6 sprites of 32x8); old row 16 text cleared
    for x in range(0, 48):
        for y in range(8):
            im.putpixel((x, 136 + y), src.getpixel((x, 128 + y)))
    x = 55
    for word in ('ROCKET', 'COMPANY'):
        for ch in word:
            if ch in CHUNKY_SHEET_X:
                sx = CHUNKY_SHEET_X[ch]
                for dy in range(8):
                    for dx in range(9):
                        c = src.getpixel((sx + dx, 96 + dy))
                        if c:
                            im.putpixel((x + dx, 136 + dy), c)
            else:
                m = {(i, j) for j, r in enumerate(CHUNKY_NEW[ch]) for i, v in enumerate(r) if v == '#'}
                paint(im, dilate(m), 1, x + 1, 137)
                for i, j in m:
                    im.putpixel((x + 1 + i, 137 + j), CHUNKY_ROWS[j])
            x += 8
        x += 8
    clear(0, 16, 17, 17)
    # menu items (bank 2, 48x16 each): text left edge at x+5, caps on rows 2-8 of the cell
    clear(26, 12, 32, 14)  # はじめから
    clear(23, 14, 32, 16)  # つうしん, つづき

    def menu(text, c0, r0):
        m, _w, _h = text_mask(text, MENU, 1, 3)
        paint(im, dilate(m), 1, c0 * 8 + 7, r0 * 8 + 2)
        paint(im, m, 0xF, c0 * 8 + 7, r0 * 8 + 2)
    menu('New Game', 26, 12)
    menu('Continue', 24, 17)
    menu('Link', 23, 14)
    for k in range(OBJ_ROWS * 32):  # view in the bank each tile is drawn with
        b = banks.get(k, 3 if k < 384 else 2)
        for y in range(8):
            for x in range(8):
                p = (k % 32 * 8 + x, k // 32 * 8 + y)
                c = im.getpixel(p)
                if c:
                    im.putpixel(p, b * 16 + (c & 15))
    im.putpalette(palette_flat(plt_rgb(G.load(rom, 1, 2996))))
    return im

# -- intro logo


def intro_tiles(rom):
    return [t for t in tiles4(G.load(rom, 1, 3019)[8:])]


def intro_index(rom, i: int) -> Image.Image:
    return render_map(intro_tiles(rom), struct.unpack_from('<640H', G.load(rom, 1, i), 8), 32, 20)


def draw_intro(rom) -> Image.Image:
    orig = Image.new('P', (512, 160))
    orig.paste(intro_index(rom, 3021), (0, 0))
    orig.paste(intro_index(rom, 3022), (256, 0))
    band = intro_index(rom, 3020)  # the plain silver band (tile-periodic rows)
    im = Image.new('P', (512, 160))
    for y in range(160):
        for x in range(512):
            im.putpixel((x, y), band.getpixel((x % 256, y)))
    # keep the big "2" (every changed pixel right of x=364, the old katakana end before it)
    diff = {(x, y) for y in range(160) for x in range(512) if orig.getpixel((x, y)) != im.getpixel((x, y))}
    seen, keep = set(), set()
    for p in sorted(diff):
        if p in seen:
            continue
        comp, todo = set(), [p]
        while todo:
            q = todo.pop()
            if q in comp or q not in diff:
                continue
            comp.add(q)
            todo += [(q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]
        seen |= comp
        if min(x for x, _ in comp) >= 360:
            keep |= comp
    for p in keep:
        im.putpixel(p, orig.getpixel(p))
    # cut-out letters (colour 0 shows the scene behind), 1 px dark outline, same lettering as the title logo
    for text, font, ox, oy, k in (('GACHASUTE!', BOLD12, 136, 22, 2), ('DINO DEVICE', bold16(), 30, 68, 3)):
        m, w, h = text_mask(text, font, 1, 8)
        m = shear(scale(m, 3), h * 3, k)
        paint(im, dilate(m), 1, ox, oy)
        paint(im, m, 0, ox, oy)
    im.putpalette(palette_flat(plt_rgb(G.load(rom, 1, 3023))))
    return im

# -- name-entry button labels


UI_LABELS = {'HIRAGANA': (6, 252), 'KATAKANA': (9, 254)}   # label: (old 3-tile column in row 4, 2 new tiles in row 7)
# Birthday labels centred over the fields (year cells 8-11, month 14-15, day 18-19) on map row 6;
# cell -> sheet tile: the old 年月日 tiles and the sheet's empty tiles (rows 6-7), unused by the 2966 screens.
BDAY = (('Year', 80), ('Month', 120), ('Day', 152))
BDAY_ROW = 6
BDAY_TILES = dict(zip([8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20], [84, 85, 86, 207, 208, 209] + list(range(244, 250))))


def label_cells(old_col: int, new: int) -> list[int]:
    """Top-row tile ids of a 5-cell label: the 3 old cells, then the 2 new ones."""
    return [128 + old_col, 128 + old_col + 1, 128 + old_col + 2, new, new + 1]


def draw_ui(rom) -> Image.Image:
    sheet = tiles4(G.load(rom, 1, 2966)[8:])
    im = Image.new('P', (256, 64))
    for k, t in enumerate(sheet):
        for i, c in enumerate(t):
            im.putpixel((k % 32 * 8 + i % 8, k // 32 * 8 + i // 8), c)
    for text, (col, new) in UI_LABELS.items():
        bg = im.getpixel((col * 8, 32))
        cells = label_cells(col, new)
        strip = Image.new('P', (40, 8), bg)
        d = ImageDraw.Draw(strip)
        d.rectangle([1, 3, 38, 7], fill=5)                    # grey box with a dark border, round corners
        d.line([2, 2, 37, 2], fill=2)
        d.line([1, 3, 1, 7], fill=2)
        d.line([38, 3, 38, 7], fill=2)
        m, w, _h = text_mask(text, LABEL, 1, 3)
        ox = (40 - w) // 2
        paint(strip, {(x, y) for x, y in dilate(m) if y <= 4}, 1, ox, 3)   # outline (not on the bottom border)
        paint(strip, m, 0xF, ox, 3)
        for i, t in enumerate(cells):
            for y in range(8):
                for x in range(8):
                    im.putpixel((t % 32 * 8 + x, t // 32 * 8 + y), strip.getpixel((i * 8 + x, y)))
        for c in range(3):  # bottom row: box border without the old text's outline pixels
            for x in range(8):
                p = ((col + c) * 8 + x, 40)
                if im.getpixel(p) == 1:
                    im.putpixel(p, 2)
    # ビット (tiles 240-241, no 2966 screen found that shows it; status uses BIT at 242-243): same "BIT" art
    for y in range(56, 64):
        for x in range(128, 144):
            im.putpixel((x, y), im.getpixel((x + 16, y)))
    # birthday screen: 年 月 日 after the fields -> "Year" "Month" "Day" above them (game font, white like the kanji)
    import vwf_font
    glyphs, widths = vwf_font.build(rom)
    strip = Image.new('P', (240, 8))
    for text, centre in BDAY:
        w = vwf_font.text_width(text, widths) - 1
        x = centre - w // 2
        for ch in text:
            c = vwf_font.CHARMAP[ch][-1]
            for y in range(8):
                for dx in range(widths[c]):
                    if glyphs[c * 8 + y] & (0x80 >> dx):
                        strip.putpixel((x + dx, y), 0xF)
            x += widths[c]
    ink = {x // 8 for x in range(240) for y in range(8) if strip.getpixel((x, y))}
    assert ink == set(BDAY_TILES), sorted(ink)
    for cell, t in BDAY_TILES.items():
        for y in range(8):
            for x in range(8):
                im.putpixel((t % 32 * 8 + x, t // 32 * 8 + y), strip.getpixel((cell * 8 + x, y)))
    for y in range(64):  # view in bank 1 (the buttons' bank)
        for x in range(256):
            c = im.getpixel((x, y))
            if c:
                im.putpixel((x, y), 16 + c)
    im.putpalette(palette_flat(plt_rgb(G.load(rom, 1, 2967))))
    return im


def ui_maps(rom) -> dict:
    """SCR 1/2972-2974 (one per input mode): a kana label takes its 3 cells + the 2 plain cells beside it.
    SCR 1/2970 (birthday): the 年 月 日 cells blank, the labels on row BDAY_ROW."""
    p = bytearray(G.load(rom, 1, 2970))
    for cell in (12, 16, 20):
        assert struct.unpack_from('<H', p, 8 + 2 * (9 * 30 + cell))[0] in (0x54, 0x55, 0x56)
        struct.pack_into('<H', p, 8 + 2 * (9 * 30 + cell), 0)
    for cell, t in BDAY_TILES.items():
        struct.pack_into('<H', p, 8 + 2 * (BDAY_ROW * 30 + cell), t)
    out = {2970: bytes(p)}
    for i in (2972, 2973, 2974):
        p = bytearray(G.load(rom, 1, i))
        e = list(struct.unpack_from('<52H', p, 8))
        for col, new in UI_LABELS.values():
            first = 128 + col
            if first not in [v & 0x3FF for v in e[:26]]:
                continue
            x = [v & 0x3FF for v in e[:26]].index(first)
            x0 = x if x < 13 else x - 2          # left button grows right, right button grows left
            top = label_cells(col, new)
            bot = [160 + col, 160 + col + 1, 160 + col + 1, 160 + col + 1, 160 + col + 2]
            for j in range(5):
                e[x0 + j] = (e[x0 + j] & 0xF000) | top[j]
                e[26 + x0 + j] = (e[26 + x0 + j] & 0xF000) | bot[j]
        struct.pack_into('<52H', p, 8, *e)
        out[i] = bytes(p)
    return out

# -- shared 4bpp UI sheets: catalog tabs, shop footer, Set Devices slot glyphs

SHEETS = {  # png: (group, index, PLT entry for viewing, bank)
    'catalog_sheet.png': (2, 1260, (2, 1261), 0),
    'shop_sheet.png': (2, 1282, (2, 1283), 2),
    'setdev_glyphs.png': (1, 3119, None, 0),
    'catalog_obj.png': (2, 1268, (2, 1269), 0),
}
TAB_OVERLAYS = {(2, 8): 'DINO', (2, 12): 'HEAD', (3, 8): 'RIGHT', (3, 12): 'LEFT', (4, 8): 'BODY', (5, 8): 'RIDE'}
TABS = {(0x149, 0x14A, 0x14B): 'DINO', (0x119, 0x11A, 0x11B): 'HEAD', (0x11C, 0x11D, 0x11E): 'RIGHT',
        (0x11F, 0x120, 0x121): 'LEFT', (0x122, 0x123, 0x124): 'BODY', (0x125, 0x126, 0x127): 'RIDE'}
# "SELECTボタン=ステータス" footer: two tile runs sharing the middle six tiles (shop menus / Catalog Order)
FOOTERS = ([249, 206, 207, 208, 209, 210, 211, 250], [205, 206, 207, 208, 209, 210, 211, 212])
SLOTS = [(1, 'HEAD'), (5, 'BODY'), (9, 'END'), (13, 'RIDE'), (17, 'LEFT'), (21, 'RIGHT')]  # first PAT 1/3120 pattern
SLOT_LETTERS = 'HEADBOYNRILFGT'   # glyph tiles 1.. of 1/3119 (tile 0 = the typing cursor)


def sheet_image(rom, g, i, plt, bank) -> Image.Image:
    p = G.load(rom, g, i)
    w = p[5]
    im = Image.new('P', (w * 8, p[6] * 8))
    for k, t in enumerate(tiles4(p[8:])):
        for j, c in enumerate(t):
            if c:
                im.putpixel((k % w * 8 + j % 8, k // w * 8 + j // 8), bank * 16 + c)
    rgb = plt_rgb(G.load(rom, *plt)) if plt else [(0, 0, 0), (255, 255, 255)]
    im.putpalette(palette_flat(rgb))
    return im


def put_strip(im, strip, cells, bank) -> None:
    w = im.width // 8
    for n, t in enumerate(cells):
        for y in range(8):
            for x in range(8):
                im.putpixel((t % w * 8 + x, t // w * 8 + y), bank * 16 + strip[y][n * 8 + x])


def get_strip(im, cells) -> list[list[int]]:
    w = im.width // 8
    return [[im.getpixel((t % w * 8 + x, t // w * 8 + y)) & 15 for t in cells for x in range(8)] for y in range(8)]


def tab_text(text: str) -> set:
    """Tab label pixels in its 24x8 strip: centred in the 18 px box, rows 2-7."""
    m, w, _h = text_mask(text, TAB, 1, 3)
    return {(3 + (18 - w) // 2 + x, y + 2) for x, y in m}


def draw_catalog_obj(rom) -> Image.Image:
    """Selected-tab blink overlay (OBJ 1/... sheet 2/1268, 15 tiles wide): the label's text pixels in colour 14."""
    g, i, plt, bank = SHEETS['catalog_obj.png']
    im = sheet_image(rom, g, i, plt, bank)
    for (r, c), text in TAB_OVERLAYS.items():
        s = [[0] * 24 for _ in range(8)]
        for x, y in tab_text(text):
            s[y][x] = 0xE
        put_strip(im, s, [r * 15 + c + k for k in range(3)], bank)
    return im


def draw_catalog(rom) -> Image.Image:
    g, i, plt, bank = SHEETS['catalog_sheet.png']
    im = sheet_image(rom, g, i, plt, bank)
    for cells, text in TABS.items():
        s = get_strip(im, cells)
        for y in range(8):
            for x in range(2, 22):  # box: '6' border columns 2 and 21 (some kana ran over them), dark inside
                s[y][x] = 6 if x in (2, 21) else 1
        for x, y in tab_text(text):
            s[y][x] = 0xF
        put_strip(im, s, cells, bank)
    # Catalog Order footer "SELECTボタン=ステータス": tiles 229-236, text rows 3-7 on scanline stripes
    cells = list(range(229, 237))
    s = get_strip(im, cells)
    m, w, _h = text_mask('SELECT: STATUS', LABEL, 1, 3)
    for y in range(3, 8):
        for x in range(64):
            s[y][x] = 6 if y % 2 else 3
    for x, y in m:
        s[y + 3][(62 - w) // 2 + x] = 0xF
    put_strip(im, s, cells, bank)
    return im


def draw_shop(rom) -> Image.Image:
    g, i, plt, bank = SHEETS['shop_sheet.png']
    im = sheet_image(rom, g, i, plt, bank)
    m, w, _h = text_mask('SELECT: STATUS', LABEL, 1, 3)
    done = {}
    for cells in FOOTERS:
        s = get_strip(im, cells)
        for y in range(6):  # scanline-striped background, text rows 0-4
            for x in range(63 if cells[-1] == 212 else 64):  # 212 ends in the frame column
                s[y][x] = 6 if y % 2 == 0 else 3
        for x, y in m:
            s[y][(62 - w) // 2 + x] = 0xF
        put_strip(im, s, cells, bank)
        for n, t in enumerate(cells):
            tile = [s[y][n * 8 + x] for y in range(8) for x in range(8)]
            assert done.setdefault(t, tile) == tile, f'footer tile {t} differs between the two runs'
    return im


def draw_setdev(rom) -> Image.Image:
    g, i, plt, bank = SHEETS['setdev_glyphs.png']
    im = sheet_image(rom, g, i, plt, bank)
    for x in range(8, 128):
        for y in range(8):
            im.putpixel((x, y), 0)
    for n, ch in enumerate(SLOT_LETTERS):
        for y, row in enumerate(SLOT[ch]):
            for x, v in enumerate(row):
                if v == '#':
                    im.putpixel(((n + 1) * 8 + 1 + x, 1 + y), 1)
    return im


# Battle effect sheets (1/2583..2655, plain IMG 16x4): the katakana sound effect is a 16x16 sprite at cols 14-15,
# rows 0-1 (left / upper word half, tile 14) and rows 2-3 (right / lower half, tile 78), shown side by side.
SFX = {2583: ('POP',), 2601: ('BL', 'AM'), 2619: ('ZA', 'P!'), 2637: ('BO', 'OM'), 2655: ('ZI', 'NG')}
SFX_FONT = art('''
B:
####.
##.##
##.##
##.##
####.
##.##
##.##
##.##
##.##
####.
L:
##...
##...
##...
##...
##...
##...
##...
##...
#####
#####
A:
.###.
##.##
##.##
##.##
##.##
#####
##.##
##.##
##.##
##.##
M:
##..##
######
######
##..##
##..##
##..##
##..##
##..##
##..##
##..##
O:
.###.
##.##
##.##
##.##
##.##
##.##
##.##
##.##
##.##
.###.
Z:
#####
#####
...##
..##.
..##.
.##..
.##..
##...
#####
#####
I:
##
##
##
##
##
##
##
##
##
##
N:
##..##
###.##
###.##
######
######
##.###
##.###
##..##
##..##
##..##
G:
.####
##...
##...
##...
##.##
##.##
##.##
##.##
##.##
.####
P:
####.
##.##
##.##
##.##
####.
##...
##...
##...
##...
##...
!:
##
##
##
##
##
##
##
..
##
##
p:
###.
##.#
##.#
##.#
###.
##..
##..
##..
##..
##..
o:
.##.
##.#
##.#
##.#
##.#
##.#
##.#
##.#
##.#
.##.
''')
SFX_FILL = [0xF, 0xF, 0xF, 0xF, 0xE, 0xE, 0xD, 0xD, 0xC, 0xB]  # white to grey like the kana, outline 1


def draw_sfx(rom) -> Image.Image:
    im = Image.new('P', (16 * len(SFX), 32))
    for k, words in enumerate(SFX.values()):
        for half, word in enumerate(words):
            font = SFX_FONT if len(word) < 3 else {'P': SFX_FONT['p'], 'O': SFX_FONT['o']}  # 3 letters: 4 px wide
            m, w, _h = text_mask(word, font, 1, 3)
            ox, oy = k * 16 + (16 - w) // 2, half * 16 + 3
            paint(im, dilate(m), 1, ox, oy)
            for x, y in m:
                im.putpixel((ox + x, oy + y), SFX_FILL[y])
    im.putpalette(palette_flat([(255, 0, 255)] + [(i * 17, i * 17, i * 17) for i in range(1, 16)]))
    return im


def sfx_payload(rom, png: Image.Image, k: int, i: int) -> bytes:
    p = bytearray(G.load(rom, 1, i))
    for r in range(4):
        for c in range(2):
            t = bytes(png.getpixel((k * 16 + c * 8 + x, r * 8 + y)) & 15
                      for y in range(8) for x in range(8))
            p[8 + 32 * (r * 16 + 14 + c):8 + 32 * (r * 16 + 15 + c)] = pack4(t)
    return bytes(p)


def setdev_patterns(rom) -> list:
    """PAT 1/3120: the slot name typed in (4 patterns per slot: 3 typing steps with cursor tile 0 after the
    letters, the last one = the whole word; the game blinks the cursor by alternating patterns 3 and 4)."""
    pats = pat_parse(G.load(rom, 1, 3120))
    for first, word in SLOTS:
        n = len(word)
        x0 = -4 - 3 * n  # 6 px pitch, centred where the 3 kana were
        tiles = [1 + SLOT_LETTERS.index(c) for c in word]
        for step, k in enumerate((max(1, round(n / 3)), round(2 * n / 3), n)):
            pats[first + step] = [[0x2000, x0 + 6 * k, -8, 0]] + [[0x2000, x0 + 6 * j, -8, tiles[j]] for j in range(k)]
        pats[first + 3] = [[0x2000, x0 + 6 * j, -8, tiles[j]] for j in range(n)]
    return pats

# ---------------------------------------------------------------- import (build)


def load_png(name: str) -> Image.Image:
    im = Image.open(GFX / name)
    assert im.mode == 'P', f'{name}: save as an indexed PNG in the game palette'
    return im


def img_payload(tiles: list[bytes], bpp: int, w: int = 32) -> bytes:
    """IMG header [5] = w tiles wide, [6] = rows of 32-byte units (an 8bpp tile counts as two)."""
    data = b''.join(tiles) if bpp == 8 else b''.join(pack4(t) for t in tiles)
    data += bytes(-len(data) % (32 * w))
    return b'IMG\0' + bytes([0, w, len(data) // (32 * w), 0]) + data


def sheet_tiles(im: Image.Image) -> list[bytes]:
    """4bpp sheet PNG -> tiles in row-major order (colour = pixel & 15)."""
    return [bytes(c & 15 for c in tile_at(im, k % (im.width // 8), k // (im.width // 8)))
            for k in range(im.width // 8 * im.height // 8)]


def tileize(im: Image.Image, w: int, h: int, x0: int, tiles: list, index: dict, mask: int, flips: bool) -> list[int]:
    """Cut a w x h tile area into `tiles` (deduplicated through `index`); returns map entries."""
    ents = []
    for ty in range(h):
        for tx in range(w):
            t = bytes(c & mask for c in tile_at(im, x0 // 8 + tx, ty))
            for hf, vf in ((0, 0), (1, 0), (0, 1), (1, 1)) if flips else ((0, 0),):
                f = flip(t, hf, vf)
                if f in index:
                    ents.append(index[f] | hf << 10 | vf << 11)
                    break
            else:
                index[t] = len(tiles)
                tiles.append(t)
                ents.append(index[t])
    return ents


def blocks(rom: bytes) -> dict:
    """(group, index) -> new payload."""
    out = {}
    logo = load_png('title_logo.png')
    tiles, index = [], {}
    ents = tileize(logo, 30, 20, 0, tiles, index, 0xFF, False)
    assert len(tiles) <= 448, f'title logo: {len(tiles)} 8bpp tiles, BG2 has room for 448 (maps at 0x0600F000)'
    out[1, 2982] = img_payload(tiles, 8)
    out[1, 2984] = G.load(rom, 1, 2984)[:8] + struct.pack('<600H', *ents)

    obj = load_png('title_obj.png')
    assert obj.size == (256, OBJ_ROWS * 8)
    out[1, 2995] = img_payload([bytes(c & 15 for c in tile_at(obj, k % 32, k // 32)) for k in range(OBJ_ROWS * 32)], 4)
    out[1, 2997] = pat_build(obj_patterns(rom))

    intro = load_png('intro_logo.png')
    tiles, index = [], {}
    maps = {3020: tileize(intro_index(rom, 3020), 32, 20, 0, tiles, index, 15, True)}
    maps[3021] = tileize(intro, 32, 20, 0, tiles, index, 15, True)
    maps[3022] = tileize(intro, 32, 20, 256, tiles, index, 15, True)
    assert len(tiles) <= 512, f'intro logo: {len(tiles)} tiles, VRAM 0x0600A000-0x0600DFFF holds 512'
    out[1, 3019] = img_payload(tiles, 4)
    for i, ents in maps.items():
        out[1, i] = G.load(rom, 1, i)[:8] + struct.pack('<640H', *ents)

    ui = load_png('ui_sheet.png')
    out[1, 2966] = img_payload([bytes(c & 15 for c in tile_at(ui, k % 32, k // 32)) for k in range(256)], 4)
    for i, p in ui_maps(rom).items():
        out[1, i] = p

    for name, (g, i, _plt, _bank) in SHEETS.items():
        im = load_png(name)
        head = G.load(rom, g, i)
        assert im.size == (head[5] * 8, head[6] * 8), name
        out[g, i] = img_payload(sheet_tiles(im), 4, head[5])
    out[1, 3120] = pat_build(setdev_patterns(rom))
    sfx = load_png('battle_sfx.png')
    for k, i in enumerate(SFX):
        out[1, i] = sfx_payload(rom, sfx, k, i)
    return out


def apply(rom: bytearray) -> None:
    """Write every English graphics block into GFX_BASE.. and repoint its archive entry."""
    pos = GFX_BASE
    for (g, i), payload in blocks(bytes(rom)).items():
        old = G.entry_offset(rom, g, i)
        data = G.compress(payload) if rom[old:old + 3] == b'ECD' else payload
        if pos + len(data) > GFX_END:
            raise SystemExit(f'graphics overflow free space at {pos:#x}')
        rom[pos:pos + len(data)] = data
        G.repoint(rom, g, i, pos)
        assert G.load(rom, g, i)[:len(payload)] == payload  # a plain entry's size runs to the next entry
        pos = (pos + len(data) + 3) & ~3


def draw() -> None:
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    GFX.mkdir(exist_ok=True)
    for name, fn in (('title_logo.png', draw_title_logo), ('title_obj.png', draw_title_obj),
                     ('intro_logo.png', draw_intro), ('ui_sheet.png', draw_ui), ('catalog_sheet.png', draw_catalog),
                     ('shop_sheet.png', draw_shop), ('setdev_glyphs.png', draw_setdev),
                     ('catalog_obj.png', draw_catalog_obj), ('battle_sfx.png', draw_sfx)):
        fn(rom).save(GFX / name)
        print(GFX / name)


if __name__ == '__main__':
    if sys.argv[1:] == ['draw']:
        draw()
    else:
        sys.exit(__doc__)

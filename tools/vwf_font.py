"""VWF font (asm/vwf.asm): 256 glyphs, 1bpp ink = 1, MSB left, + 1-byte widths (incl. 1 trailing blank column).

Derived from the game font (tools/font.py): Latin letters, digits and punctuation are trimmed to their ink;
kana keep the full 8 px cell. CHARMAP maps English text characters to script bytes.

    python -X utf8 tools/vwf_font.py render -> work/vwf_font.png (glyph strip at true widths)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SPACE_W = 3

LATIN = list(range(0x01, 0x0B)) + list(range(0xAC, 0xE0)) + list(range(0xE0, 0x100))

# hand-drawn replacements (8 rows, '#' = ink); width = drawn width + 1
OVERRIDE = {
    0xEC: ['', '', '', '', '###', '', '', ''],              # '-' hyphen (was ー)
    0xF1: ['', '', '', '', '', '', '#', ''],                # '.'
    0xF2: ['', '', '', '', '', '', '#', '#'],               # ','
    0xEE: ['', '', '', '#', '', '', '#', ''],               # ':'
    0xEF: ['', '', '', '', '', '', '#.#.#', ''],            # '…'
    0xE7: ['', '#', '#', '', '', '', '', ''],               # "'"
    0xE4: ['', '#.#', '#.#', '', '', '', '', ''],           # '"'
    0xF3: ['', '', '', '#', '', '', '#', '#'],              # ';' (was 。)
}

# English word space = F0 F9 (narrow); glyph 00 (JP full-width space) stays a full 8 px cell, so the JP padding
# that menus rely on to overwrite older, longer strings still clears whole cells.
SPACE = 0xF9
CHARMAP = {' ': bytes([0xF0, SPACE]), '　': b'\x00'}  # '　' = clearing/alignment cell
for _i, _c in enumerate('0123456789'):
    CHARMAP[_c] = bytes([0x01 + _i])
for _i, _c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'):
    CHARMAP[_c] = bytes([0xAC + _i])
for _c, _g in {'?': 0xE2, '!': 0xE3, '"': 0xE4, '%': 0xE5, '&': 0xE6, "'": 0xE7, '(': 0xE8, ')': 0xE9,
               '-': 0xEC, '~': 0xED, ':': 0xEE, '…': 0xEF, '.': 0xF1, ',': 0xF2, ';': 0xF3, '@': 0xF4,
               '—': 0xF5, '+': 0xF6, '=': 0xF7, '/': 0xF8, '▼': 0xE0, '▶': 0xE1}.items():
    CHARMAP[_c] = bytes([0xF0, _g])


def build(rom: bytes) -> tuple[bytes, bytes]:
    glyphs = bytearray()
    widths = bytearray()
    for c in range(256):
        rows = [(~b) & 0xFF for b in font.glyph(rom, c)]
        if c in OVERRIDE:
            art = OVERRIDE[c]
            rows = [sum(0x80 >> x for x, ch in enumerate(r) if ch == '#') for r in art]
            w = max(len(r) for r in art) + 1
        elif c == SPACE:
            rows, w = [0] * 8, SPACE_W
        elif c == 0x00:
            rows, w = [0] * 8, 8
        elif c in LATIN and any(rows):
            ink = 0
            for r in rows:
                ink |= r
            left = next(x for x in range(8) if ink & (0x80 >> x))
            right = max(x for x in range(8) if ink & (0x80 >> x))
            rows = [(r << left) & 0xFF for r in rows]
            w = min(right - left + 2, 8)  # full-width symbols (©, ®) keep no gap
        else:
            w = 8
        assert 1 <= w <= 8, (hex(c), w)
        glyphs += bytes(rows)
        widths.append(w)
    return bytes(glyphs), bytes(widths)


def text_width(s: str, widths: bytes) -> int:
    """Pixel width of plain English text (no tags) under CHARMAP."""
    return sum(widths[CHARMAP[ch][-1]] for ch in s)


def render_strip(glyphs: bytes, widths: bytes, text: str, out: Path, zoom: int = 4):
    from PIL import Image
    w = text_width(text, widths)
    im = Image.new('L', (w + 2, 10), 255)
    x = 1
    for ch in text:
        c = CHARMAP[ch][-1]
        for y in range(8):
            for dx in range(widths[c]):
                if glyphs[c * 8 + y] & (0x80 >> dx):
                    im.putpixel((x + dx, y + 1), 0)
        x += widths[c]
    im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save(out)


if __name__ == '__main__':
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    g, w = build(rom)
    if sys.argv[1:2] == ['render']:
        sample = ('The quick brown fox jumps over the lazy dog! 0123456789 '
                  'THE QUICK BROWN FOX: "Dino Battle?" (Yes/No) 100% & more... it\'s fine; well-done.')
        render_strip(g, w, sample, ROOT / 'work/vwf_font.png', zoom=3)
        print('work/vwf_font.png', text_width(sample, w), 'px')

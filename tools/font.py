"""Dialogue font: 1bpp 8x8, 8 bytes/glyph at ROM 0x1D5A38, glyph code = index (renderer 0x0800BD70).

    python -X utf8 tools/font.py render [N] -> work/font.png (16 glyphs per row, row labels in hex)
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FONT = 0x1D5A38


def glyph(rom: bytes, code: int) -> list[int]:
    return list(rom[FONT + code * 8: FONT + code * 8 + 8])


def render(rom: bytes, n: int, out: Path, zoom: int = 3):
    rows = (n + 15) // 16
    im = Image.new('L', (16 * 9 + 1, rows * 9 + 1), 128)
    for c in range(n):
        g = glyph(rom, c)
        ox, oy = (c % 16) * 9 + 1, (c // 16) * 9 + 1
        for y, b in enumerate(g):
            for x in range(8):
                im.putpixel((ox + x, oy + y), 0 if b & (0x80 >> x) else 255)
    im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save(out)


if __name__ == '__main__':
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    if sys.argv[1:2] == ['render']:
        n = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x200
        (ROOT / 'work').mkdir(exist_ok=True)
        render(rom, n, ROOT / 'work/font.png')
        print('work/font.png')

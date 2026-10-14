"""Japanese codec for this game: 1-byte font codes 00-DF (+F0-FF), F0 xx = glyph xx (E0-FF row), other E0-FF = control.

Control-code argument counts are provisional until the renderer is disassembled (docs/re/text.md).
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_font() -> dict[int, str]:
    t = {}
    for line in (ROOT / 'tbl/font.tbl').read_text(encoding='utf-8').splitlines():
        k, v = line.split('=', 1)
        t[int(k, 16)] = v
    return t


FONT = load_font()
REV = {}
for k, v in sorted(FONT.items()):
    REV.setdefault(v, k)


def encode_plain(s: str) -> bytes:
    """Encode Japanese text (no control codes) for byte searches."""
    out = bytearray()
    for ch in s:
        c = REV[ch]
        if c >= 0xE0:
            out.append(0xF0)
        out.append(c)
    return bytes(out)


def find_all(rom: bytes, s: str) -> list[int]:
    return [m.start() for m in re.finditer(re.escape(encode_plain(s)), rom)]


if __name__ == '__main__':
    import sys
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    for w in sys.argv[1:]:
        print(w, encode_plain(w).hex(' '), [hex(a) for a in find_all(rom, w)][:20])

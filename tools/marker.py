"""Marker text: keep every control code of the jp field, replace each plain text run with English filler that
fills the same pixel width (JP glyphs are 8 px), the first run prefixed with the entry id."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwf_font import CHARMAP  # noqa: E402

FILLER = 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen jugs! '
RUN = re.compile(r'(\[[^\]]*\]|\n)')


def fit(prefix: str, px: int, widths: bytes) -> str:
    out, w = '', 0
    for ch in (prefix + FILLER * 4):
        cw = widths[CHARMAP[ch][-1]]
        if w + cw > px:
            break
        out += ch
        w += cw
    return out.rstrip()


def marker(entry: dict, widths: bytes) -> str:
    parts = RUN.split(entry['jp'])
    first = True
    out = []
    for p in parts:
        if not p or RUN.fullmatch(p):
            out.append(p)
            continue
        out.append(fit(f"{entry['ids'][0]} " if first else '', len(p) * 8, widths))
        first = False
    return ''.join(out)

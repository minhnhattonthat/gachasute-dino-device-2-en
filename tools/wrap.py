"""Word-wrap English to the dialogue width. Hand-written line breaks stay; text between them is wrapped greedily
at spaces, each line against its own budget (160 px; 152 px on every box's 3rd line, where the page arrow sits).
The game pages automatically when a box is full, so wrapping never needs to add [p].
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwf_font import CHARMAP  # noqa: E402

VAR_PX = {'[player]': 48, '[partner]': 48}  # 6-letter name, widest letters; overflow leaves stale cells
HARD = re.compile(r'(\n|\[p\]|\[half\]|\[close\]|\[end\]|\[ret\])')
TOKEN = re.compile(r'\[[^\]]*\]|.', re.S)
WORD_SPACE = re.compile(r' (?![^\[]*\])')  # spaces outside [tags]


def px(s: str, widths: bytes) -> int:
    n = 0
    for t in TOKEN.findall(s):
        if t in VAR_PX:
            n += VAR_PX[t]
        elif not t.startswith('['):
            n += widths[CHARMAP[t][-1]]
    return n


LAST_PX = 152  # the page arrow sits in the last cell of every box's 3rd line
PAGE_LINES = 3


def wrap(en: str, widths: bytes, limit: int = 160) -> str:
    out, n = [], 0
    for p in HARD.split(en):
        if p in ('[p]', '[close]', '[end]', '[ret]'):
            n = 0
            out.append(p)
        elif p in ('\n', '[half]'):
            n += 1
            out.append(p)
        elif p:
            # greedy, each line against its own budget (3rd line of a box is shorter)
            fixed, cur = [], ''
            for w in ([p] if '[opt]' in p else WORD_SPACE.split(p)):
                budget = LAST_PX if (n + len(fixed)) % PAGE_LINES == PAGE_LINES - 1 else limit
                cand = f'{cur} {w}' if cur else w
                if cur and px(cand, widths) > budget:
                    fixed.append(cur)
                    cur = w
                else:
                    cur = cand
            fixed.append(cur)
            n += len(fixed) - 1
            out.append('\n'.join(fixed))
    return ''.join(out)


def budgets(laid_out: str, limit: int = 160):
    """Yield (line, budget) for already-wrapped text (lint)."""
    n = 0
    for p in HARD.split(laid_out):
        if p in ('[p]', '[close]', '[end]', '[ret]'):
            n = 0
        elif p in ('\n', '[half]'):
            n += 1
        elif p:
            yield p, LAST_PX if n % PAGE_LINES == PAGE_LINES - 1 else limit


if __name__ == '__main__':
    import vwf_font
    w = vwf_font.build((Path(__file__).resolve().parents[1] / 'rom/orig.gba').read_bytes())[1]
    s = wrap("[face:01]We're cousins, but this is the first time we've ever met, huh?[p]Short.", w)
    assert s.count('\n') == 1 and all(px(x, w) <= 160 for x in s.split('[p]')[0].split('\n')), s
    print(s)

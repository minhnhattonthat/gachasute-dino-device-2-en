"""UI strings (menu printer): single-line entries. Menus overwrite an old string with a new one in the same cells
and the JP strings are space-padded so the new one covers the old. VWF English is narrower, so the build pads it
with full-width spaces (glyph 00, 8 px each) up to the JP cell width, and lint holds it to that width.
"""
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
END = re.compile(r'(\[close\]|\[end\])$')
NOT_UI = re.compile(r'\n|\[p\]|\[half\]|\[face|\[noface\]|\[E0 0[0-3] ')


def is_ui(e: dict) -> bool:
    """Menu-printer strings: misc tables, bank 0 and banks 10+ (story banks 1-8 are dialogue-box text)."""
    eid = e.get('id') or e['ids'][0]
    if '.' not in eid and 0x01 <= int(eid, 16) >> 8 <= 0x08:
        return False
    return bool(END.search(e['jp'])) and not NOT_UI.search(e['jp'])


def jp_cells(jp: str) -> int:
    """Visible JP cells of a single-line string (name variables count 6 cells, other tags 0)."""
    return len(re.sub(r'\[[^\]]*\]', '', jp)) + 6 * len(re.findall(r'\[(?:player|partner)\]', jp))


def budget(e: dict) -> int:
    over = overrides().get(e.get('id') or e['ids'][0])
    return over if over else jp_cells(e['jp']) * 8


def pad(e: dict, en: str, widths: bytes) -> str:
    """Append full-width spaces before the terminator until English covers the JP cells."""
    m = END.search(en)
    if not m or not is_ui(e):
        return en
    body = en[:m.start()]
    k = math.ceil((jp_cells(e['jp']) * 8 - wrap.px(body, widths)) / 8)
    return body + '　' * max(k, 0) + m.group(1)


_OVER = None


def overrides() -> dict:
    """data/ui_budgets.json: {id: px} for windows measured wider than their JP string."""
    global _OVER
    if _OVER is None:
        p = ROOT / 'data/ui_budgets.json'
        _OVER = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    return _OVER

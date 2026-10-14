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
    """Menu-printer strings: misc tables and bank 0 (banks 1+ go through the dialogue interpreter: they use
    choices, FE/FC and other codes the menu printer can't handle)."""
    eid = e.get('id') or e['ids'][0]
    if '.' not in eid and int(eid, 16) >> 8 != 0:
        return False
    return bool(END.search(e['jp'])) and not NOT_UI.search(e['jp'])


BOXES = (15, 20, 22)  # dialogue window text widths in cells (window structs: width field - 2), docs/re/text.md


def box_px(e: dict) -> int:
    """Dialogue-box line width for an entry: story banks 01-07 use the 20-cell box; system banks 10-12 use the
    smallest real window that holds the entry's longest JP line (Gachasute Park screens use a 15-cell box)."""
    eid = e.get('id') or e['ids'][0]
    if '.' in eid or int(eid, 16) >> 8 < 0x10:
        return 160
    longest = max((jp_cells(ln) for ln in re.split(r'\n|\[p\]|\[half\]|\[close\]|\[end\]', e['jp'])), default=0)
    return 8 * next((b for b in BOXES if b >= longest), BOXES[-1])


def jp_cells(jp: str) -> int:
    """Visible JP cells of a single-line string (name variables count 6 cells, other tags 0)."""
    return len(re.sub(r'\[[^\]]*\]', '', jp)) + 6 * len(re.findall(r'\[(?:player|partner)\]', jp))


def budget(e: dict) -> int:
    """Measured override, else for name tables (one shared field) the table's longest JP name, else own JP width."""
    eid = e.get('id') or e['ids'][0]
    over = overrides().get(eid) or overrides().get(eid.split('.')[0] + '.*')
    if over:
        return over
    table = eid.split('.')[0]
    if '.' in eid and not table.startswith('word_'):
        return table_cells()[table] * 8
    return jp_cells(e['jp']) * 8


_TABLE = None


def table_cells() -> dict:
    global _TABLE
    if _TABLE is None:
        _TABLE = {}
        for m in json.loads((ROOT / 'script/misc.json').read_text(encoding='utf-8')):
            t = m['id'].split('.')[0]
            _TABLE[t] = max(_TABLE.get(t, 0), jp_cells(m['jp']))
    return _TABLE


THIN = ' '  # 1 px word space for the condensed font, used only when normal spaces don't fit


def fit(e: dict, en: str, widths: bytes) -> tuple[str, int]:
    """(text, advance px). Normal font if it fits (the last glyph's blank gap column may hang over), else the
    condensed [narrow] font, with thin spaces as a last step. A name table that needs the condensed font for
    any entry uses it for all entries, so lists don't mix fonts."""
    import narrow_font
    if re.search(r'\[(?:player|partner|E0 1[0-9A-F])', en):
        return en, wrap.px(en, widths)
    b = budget(e)
    w = wrap.px(en, widths)
    if w - 1 <= b and not table_narrow(e, widths):
        return en, w
    w = narrow_font.advance(en)
    if w - 1 > b and ' ' in en:
        en = en.replace(' ', THIN)
        w = narrow_font.advance(en)
    return '[narrow]' + en, w


_NARROW = {}


def table_narrow(e: dict, widths: bytes) -> bool:
    """True if e is in a misc table where some entry needs the condensed font."""
    eid = e.get('id') or e['ids'][0]
    if '.' not in eid:
        return False
    table = eid.split('.')[0]
    if table not in _NARROW:
        _NARROW[table] = False
        for m in json.loads((ROOT / 'script/misc.json').read_text(encoding='utf-8')):
            if m['id'].split('.')[0] == table and m['en'] and END.search(m['en']):
                body = m['en'][:END.search(m['en']).start()]
                if wrap.px(body, widths) - 1 > budget(m):
                    _NARROW[table] = True
                    break
    return _NARROW[table]


def pad(e: dict, en: str, widths: bytes) -> str:
    """Narrow font if needed, then full-width spaces before the terminator until English covers the JP cells."""
    m = END.search(en)
    if not m or not is_ui(e):
        return en
    body, w = fit(e, en[:m.start()], widths)
    # 8 px blank cells up to the slot width, never past it: one cell too many lands on the next string's tiles
    k = (pad_cells(e) * 8 - w) // 8
    return body + '　' * max(k, 0) + m.group(1)


def pad_cells(e: dict) -> int:
    """Cells the original string covered: the slot width for name tables, the JP string's own cells otherwise."""
    return budget(e) // 8


_OVER = None


def overrides() -> dict:
    """data/ui_budgets.json: {id: px} for windows measured wider than their JP string."""
    global _OVER
    if _OVER is None:
        p = ROOT / 'data/ui_budgets.json'
        _OVER = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    return _OVER

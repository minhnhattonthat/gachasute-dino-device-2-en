"""Text lint over script/*.json `en` fields. Exit 1 on any error.

Checks: control codes match jp (as a multiset; layout codes \\n [p] [half] [opt] may differ, choice cursor args are
rebuilt), every character encodable, line width <= LINE_PX (VWF widths; [player]/[partner] count NAME_PX),
no Japanese left, glossary 'Avoid' spellings, no ordinal suffix glued to a variable.

    python -X utf8 tools/lint.py
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import choices  # noqa: E402
import uipad  # noqa: E402
import vwf_font  # noqa: E402
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LINE_PX = 160
NAME_PX = 42          # 6-letter English name, wide letters
VAR_PX = {'[player]': NAME_PX, '[partner]': NAME_PX}
LAYOUT = {'\n', '[p]', '[half]', '[opt]'}
TOKEN = re.compile(r'\[[^\]]*\]|\n')
JP = re.compile(r'[぀-ヿ一-鿿]')  # '　' is allowed: an 8 px alignment/clearing cell
CHOICE_TAG = re.compile(r'\[E0 0([0-3])((?: [0-9A-F]{2})+)\]')


def codes(s: str) -> collections.Counter:
    out = collections.Counter()
    for t in TOKEN.findall(s):
        if t in LAYOUT or t.startswith('[tab:'):
            continue
        m = CHOICE_TAG.fullmatch(t)
        if m:  # cursor cells are rebuilt by tools/choices.py; compare subcommand + target ids
            n = 3 if m.group(1) == '2' else 2
            t = f'[E0 0{m.group(1)} *' + ''.join(' ' + a for a in m.group(2).split()[n:]) + ']'
        out[t] += 1
    return out


def avoid_terms() -> list[tuple[str, str]]:
    out = []
    for line in (ROOT / 'glossary.md').read_text(encoding='utf-8').splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) == 5 and cells[4] and cells[0] not in ('JP', '---'):
            for bad in cells[4].split(','):
                if bad.strip():
                    out.append((bad.strip(), cells[1]))
    return out


def line_widths(en: str, widths: bytes):
    """Yield (px, budget, line text) per visual line of the laid-out English."""
    s = choices.layout(wrap.wrap(en, widths, LINE_PX), widths)
    for line, budget in wrap.budgets(s, LINE_PX):
        px = 0
        for t in re.findall(r'\[[^\]]*\]|.', line, re.S):
            if t.startswith('[tab:'):
                px = int(t[5:-1], 16) * 8
            elif t in VAR_PX:
                px += VAR_PX[t]
            elif t.startswith('['):
                continue
            else:
                px += widths[vwf_font.CHARMAP[t][-1]]
        yield px, budget, line


def lint_entry(e: dict, widths: bytes, avoid) -> list[str]:
    en = e['en']
    if not en:
        return []
    errs = []
    if codes(en) != codes(e['jp']):
        a, b = codes(e['jp']), codes(en)
        errs.append(f'codes differ: missing {dict(a - b)} extra {dict(b - a)}')
    if JP.search(en):
        errs.append('Japanese left: ' + ''.join(sorted(set(JP.findall(en)))))
    plain = TOKEN.sub('', en)
    bad = sorted({ch for ch in plain if ch not in vwf_font.CHARMAP})
    if bad:
        errs.append(f'not encodable: {bad}')
        return errs
    if uipad.is_ui(e):
        if '\n' in en or '[p]' in en:
            errs.append('UI string must stay on one line')
        w, b = wrap.px(en, widths), uipad.budget(e)
        if w > b:
            errs.append(f'UI {w}px > {b} (JP cell width; measured exceptions in data/ui_budgets.json)')
        return errs + glossary_errs(en, avoid)
    try:
        for px, budget, line in line_widths(en, widths):
            if px > budget:
                errs.append(f'line {px}px > {budget}: {line!r}')
    except ValueError as ex:
        errs.append(str(ex))
    return errs + glossary_errs(en, avoid)


def glossary_errs(en: str, avoid) -> list[str]:
    errs = []
    for wrong, right in avoid:
        if re.search(rf'\b{re.escape(wrong)}\b', en):
            errs.append(f'glossary: {wrong!r} -> {right!r}')
    if re.search(r'\](st|nd|rd|th)\b', en):
        errs.append('ordinal suffix glued to a variable')
    return errs


def main() -> int:
    widths = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]
    avoid = avoid_terms()
    n_err = n_done = n_all = 0
    for p in sorted((ROOT / 'script').glob('*.json')):
        for e in json.loads(p.read_text(encoding='utf-8')):
            n_all += 1
            n_done += bool(e['en'])
            for err in lint_entry(e, widths, avoid):
                n_err += 1
                print(f'{p.name} {e.get("id") or e["ids"][0]}: {err}')
    print(f'lint: {n_err} errors; {n_done}/{n_all} entries translated')
    return 1 if n_err else 0


if __name__ == '__main__':
    sys.exit(main())

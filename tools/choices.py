"""Choice lines: translators write `[opt]Yes[opt]No[E0 00 r1 r2 ids..]`; the build turns each [opt] into a VWF tab
and rewrites the cursor-cell args (r1 r2 [r3]) so the cursor (drawn in cell r) sits right before its option.

E0 00/01/03 take 2 cursor cells, E0 02 takes 3. Option 1 starts at cell 2 (cursor at 1); each next option starts
two cells after the previous option's last used cell.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vwf_font import CHARMAP  # noqa: E402

CHOICE = re.compile(r'((?:\[opt\](?:(?!\[opt\]|\[E0 0[0-3] )[^\n])*)+)\[E0 0([0-3])((?: [0-9A-F]{2})+)\]')


def _px(s: str, widths: bytes) -> int:
    return sum(widths[CHARMAP[ch][-1]] for ch in re.sub(r'\[[^\]]*\]', '', s))


def layout(en: str, widths: bytes, box_cells: int = 20) -> str:
    def fix(m):
        opts = m.group(1).split('[opt]')[1:]
        sub, args = int(m.group(2)), m.group(3).split()
        nrows = 3 if sub == 2 else 2
        if len(opts) != nrows:
            raise ValueError(f'choice E0 0{sub} needs {nrows} [opt] options, got {len(opts)}: {m.group(0)!r}')
        out, cells, cell = '', [], 2
        for o in opts:
            cells.append(cell - 1)
            out += f'[tab:{cell:02X}]{o}'
            cell += (_px(o, widths) + 7) // 8 + 2
        if cell - 2 > box_cells:
            raise ValueError(f'choice line wider than the {box_cells}-cell box: {m.group(0)!r}')
        args[:nrows] = [f'{c:02X}' for c in cells]
        return out + f'[E0 0{sub} ' + ' '.join(args) + ']'
    return CHOICE.sub(fix, en)


if __name__ == '__main__':
    import vwf_font
    _g, w = vwf_font.build((Path(__file__).resolve().parents[1] / 'rom/orig.gba').read_bytes())
    r = layout('Is that OK?\n[opt]Yes[opt]No[E0 00 01 05 00 3B 00 3C]', w)
    assert r == 'Is that OK?\n[tab:02]Yes[tab:07]No[E0 00 01 06 00 3B 00 3C]', r
    print(r)

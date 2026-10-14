"""Dry-run fitter: show how English will wrap in the dialogue box, with pixel widths.

    python -X utf8 tools/fit.py "[face:01]Some English text...[p]Next page."
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import choices  # noqa: E402
import vwf_font  # noqa: E402
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    widths = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]
    s = choices.layout(wrap.wrap(sys.argv[1], widths), widths)
    for line, budget in wrap.budgets(s):
        w = wrap.px(line, widths)
        print(f'{w:3d}/{budget} {"OVER " if w > budget else ""}{line}')

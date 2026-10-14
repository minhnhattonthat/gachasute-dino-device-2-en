import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import choices  # noqa: E402
import lint  # noqa: E402
import text  # noqa: E402
import vwf_font  # noqa: E402
import wrap  # noqa: E402

WIDTHS = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]


def test_lint_clean():
    assert lint.main() == 0


def test_wrap_respects_budgets_and_hard_breaks():
    s = wrap.wrap('[face:01]' + 'word ' * 40 + 'end.\nHand break.[p]Next page.', WIDTHS)
    for line, budget in wrap.budgets(s):
        assert wrap.px(line, WIDTHS) <= budget, line
    assert 'end.\nHand break.' in s


def test_choice_layout():
    r = choices.layout('Is that OK?\n[opt]Yes[opt]No[E0 00 01 05 00 3B 00 3C]', WIDTHS)
    assert r == 'Is that OK?\n[tab:02]Yes[tab:07]No[E0 00 01 06 00 3B 00 3C]'


def test_english_encodes_tab_and_glyphs():
    b = text.encode('[tab:02]Hi!', vwf_font.CHARMAP)
    assert b == bytes([0xF1, 0x02, 0xB3, 0xCE, 0xF0, 0xE3])

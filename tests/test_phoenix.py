import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import phoenix as P  # noqa: E402

if not (P.DRAGON.is_file() and P.PHOENIX.is_file()):
    pytest.skip('needs both Japanese dumps in rom/', allow_module_level=True)

DRAGON = P.DRAGON.read_bytes()
PHOENIX = P.PHOENIX.read_bytes()


def test_variants_differ_only_in_header():
    # if a different Phoenix dump ever differs elsewhere, the shared translation no longer covers it
    assert P.diff_ranges(DRAGON, PHOENIX) == [(0xA6, 0xBE), (0x1D6EBE, 0x1D6ED6)]


def test_phoenix_build_is_english_plus_header():
    en = bytearray(len(DRAGON) * 2)  # stand-in for the 8 MiB build: original bytes first, then anything
    en[:len(DRAGON)] = DRAGON
    en[0x1000:0x1004] = b'ENGL'  # an edit outside the variant bytes survives
    out = P.make(bytes(en), DRAGON, PHOENIX)
    assert out[0xA0:0xB0] == PHOENIX[0xA0:0xB0] and out[0x1D6EBE:0x1D6ED6] == PHOENIX[0x1D6EBE:0x1D6ED6]
    assert out[0x1000:0x1004] == b'ENGL' and out[len(DRAGON):] == bytes(len(DRAGON))

import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / 'rom/orig.gba').is_file():
    pytest.skip('needs rom/orig.gba', allow_module_level=True)
sys.path.insert(0, str(ROOT / 'tools'))

ROM = (ROOT / 'rom/orig.gba').read_bytes()


def test_orig_rom_hash():
    assert hashlib.sha1(ROM).hexdigest() == '8bb322121ca889ed8a7b22a907cd835e23fd4449'


def test_font_tbl_matches_rom():
    import mktbl
    m = mktbl.font_map(ROM)
    lines = (ROOT / 'tbl/font.tbl').read_text(encoding='utf-8').splitlines()
    assert lines == [f'{k:02X}={v}' for k, v in sorted(m.items())]


def test_known_string_encodes():
    import jpenc
    assert jpenc.find_all(ROM, 'まかせといて') == [0x4C015]

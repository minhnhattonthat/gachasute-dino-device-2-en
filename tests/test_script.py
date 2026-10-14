import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tools'))

import build  # noqa: E402
import extract  # noqa: E402
import text  # noqa: E402

ROM = (ROOT / 'rom/orig.gba').read_bytes()


def test_identity_build_is_byte_identical():
    assert bytes(build.build_identity()) == ROM


def test_jp_fields_match_rom():
    """Every jp field re-encodes to the original bytes (catches hand edits to jp and table changes)."""
    segs = {s['addr']: s for s in extract.segments(ROM)}
    entries = build.load_script()
    assert len(entries) == len(segs)
    for e in entries:
        s = segs[int(e['addr'], 16)]
        assert text.encode(e['jp']) == ROM[s['addr']:s['end']], e['addr']


def test_gaps_are_padding_or_dead_scripts():
    """Bytes in the script region no pointer reaches: padding, or the 6 known dead scripts."""
    dead = {0x4B628, 0x4FB7B, 0x58547, 0x58980, 0x58D60, 0x59216}
    for lo, hi in extract.gaps(ROM, extract.segments(ROM)):
        assert lo in dead or not set(ROM[lo:hi]) - {0x00, 0xFF}, hex(lo)


def test_reloc_layout_keeps_fallthrough_adjacent():
    rom = build.build_reloc()
    entries = build.load_script()
    import banks
    where = {tid: tgt for tid, _s, tgt in banks.slots(bytes(rom))}
    for a, b in zip(entries, entries[1:]):
        if a['fall']:
            assert where[int(b['ids'][0], 16)] == where[int(a['ids'][0], 16)] + len(text.encode(a['jp']))


def test_script_json_is_lf_and_sorted():
    for p in (ROOT / 'script').glob('bank_*.json'):
        raw = p.read_bytes()
        assert b'\r\n' not in raw
        addrs = [int(e['addr'], 16) for e in json.loads(raw)]
        assert addrs == sorted(addrs)

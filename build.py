"""Build entry point.

    python -X utf8 build.py identity   -> build/identity.gba  (script re-packed in place; must equal the original)
    python -X utf8 build.py reloc      -> build/reloc.gba     (Japanese script moved to 0x400000, ROM 8 MiB)
"""
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import banks  # noqa: E402
import text  # noqa: E402

ORIG = ROOT / 'rom/orig.gba'
BUILD = ROOT / 'build'
TEXT_BASE = 0x400000  # relocated script (ROM expanded to 8 MiB)
ROM_SIZE = 0x800000


def load_script() -> list[dict]:
    entries = []
    for p in sorted((ROOT / 'script').glob('bank_*.json')):
        entries += json.loads(p.read_text(encoding='utf-8'))
    entries.sort(key=lambda e: int(e['addr'], 16))
    return entries


def encode_entry(e: dict, lang: str) -> bytes:
    if lang == 'en' and e['en']:
        return text.encode(e['en'])
    return text.encode(e['jp'])


def write_banks(rom: bytearray, entries: list[dict], blobs: list[bytes], place) -> None:
    """place(entry, blob) -> file offset. Rewrites every bank pointer slot to its entry's new offset."""
    new = {}
    for e, b in zip(entries, blobs):
        off = place(e, b)
        rom[off:off + len(b)] = b
        for tid in e['ids']:
            new[int(tid, 16)] = off
    for tid, slot, _tgt in banks.slots(bytes(rom)):
        struct.pack_into('<I', rom, slot, 0x08000000 + new[tid])


def build_identity() -> bytearray:
    rom = bytearray(ORIG.read_bytes())
    entries = load_script()
    blobs = [encode_entry(e, 'jp') for e in entries]
    write_banks(rom, entries, blobs, lambda e, b: int(e['addr'], 16))
    return rom


def layout_sequential(entries, blobs, base, limit):
    pos = base

    def place(e, b):
        nonlocal pos
        off = pos
        pos += len(b)
        if pos > limit:
            raise SystemExit(f'script overflows free space at {off:#x}')
        return off
    return place


def build_reloc(lang: str = 'jp') -> bytearray:
    rom = bytearray(ORIG.read_bytes()) + b'\xff' * (ROM_SIZE - ORIG.stat().st_size)
    entries = load_script()
    blobs = [encode_entry(e, lang) for e in entries]
    write_banks(rom, entries, blobs, layout_sequential(entries, blobs, TEXT_BASE, ROM_SIZE))
    return rom


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'identity'
    BUILD.mkdir(exist_ok=True)
    rom = {'identity': build_identity, 'reloc': build_reloc}[cmd]()
    out = BUILD / f'{cmd}.gba'
    out.write_bytes(rom)
    print(out)


if __name__ == '__main__':
    main()

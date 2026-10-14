"""Build entry point.

    python -X utf8 build.py identity   -> build/identity.gba  (script + misc re-packed in place; == original)
    python -X utf8 build.py reloc      -> build/reloc.gba     (Japanese script moved to 0x400000, ROM 8 MiB)
    python -X utf8 build.py marker     -> build/marker.gba    (VWF engine, every script line = id + filler)
    python -X utf8 build.py english    -> build/dino2_en.gba  (VWF engine, en fields; jp where en is empty)
"""
import functools
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'tools'))
import banks  # noqa: E402
import text  # noqa: E402

ORIG = ROOT / 'rom/orig.gba'
BUILD = ROOT / 'build'
ARMIPS = ROOT / 'tools/armips/armips.exe'
ROM_SIZE = 0x800000
TEXT_BASE = 0x400000     # relocated script + misc strings (ROM expanded to 8 MiB)
TEXT_END = 0x7E0000
VWF_FONT = 0x7E0000      # 256 x 8 bytes
VWF_WIDTHS = 0x7E0800    # 256 bytes
CODE_BASE = 0x7E1000     # VWF code (< 4 KB)
NARROW_FONT = 0x7E2000   # condensed name font, 256 x 8 bytes
NARROW_WIDTHS = 0x7E2800


def load_script() -> list[dict]:
    entries = []
    for p in sorted((ROOT / 'script').glob('bank_*.json')):
        entries += json.loads(p.read_text(encoding='utf-8'))
    entries.sort(key=lambda e: int(e['addr'], 16))
    return entries


def load_misc() -> list[dict]:
    return json.loads((ROOT / 'script/misc.json').read_text(encoding='utf-8'))


@functools.cache
def font_widths() -> bytes:
    import vwf_font
    return vwf_font.build(ORIG.read_bytes())[1]


def layout_en(e: dict, en: str) -> str:
    """English text as the game gets it: UI strings padded to their JP cells, dialogue wrapped + choices laid out."""
    import choices
    import uipad
    import wrap
    if uipad.is_ui(e):
        return uipad.pad(e, en, font_widths())
    box = uipad.box_px(e)
    return choices.layout(wrap.wrap(en, font_widths(), box), font_widths(), box // 8)


def encode_en(e: dict, en: str | None) -> bytes:
    import vwf_font
    if not en:
        return text.encode(e['jp'])
    return text.encode(layout_en(e, en), vwf_font.CHARMAP)


def write_banks(rom: bytearray, entries: list[dict], blobs: list[bytes], place) -> None:
    """place(blob) -> file offset. Rewrites every bank pointer slot to its entry's new offset."""
    new = {}
    for e, b in zip(entries, blobs):
        off = place(e, b)
        rom[off:off + len(b)] = b
        for tid in e['ids']:
            new[int(tid, 16)] = off
    for tid, slot, _tgt in banks.slots(bytes(rom)):
        struct.pack_into('<I', rom, slot, 0x08000000 + new[tid])


def write_misc(rom: bytearray, entries: list[dict], blobs: list[bytes], place) -> None:
    for e, b in zip(entries, blobs):
        off = place(e, b)
        rom[off:off + len(b)] = b
        struct.pack_into('<I', rom, int(e['slot'], 16), 0x08000000 + off)


def in_place(e, b):
    return int(e['addr'], 16)


def sequential(base: int, limit: int):
    pos = base

    def place(e, b):
        nonlocal pos
        off = pos
        pos += len(b)
        if pos > limit:
            raise SystemExit(f'text overflows free space at {off:#x}')
        return off
    return place


def build_identity() -> bytearray:
    rom = bytearray(ORIG.read_bytes())
    entries, misc = load_script(), load_misc()
    write_banks(rom, entries, [text.encode(e['jp']) for e in entries], in_place)
    write_misc(rom, misc, [text.encode(e['jp']) for e in misc], in_place)
    return rom


def expanded() -> bytearray:
    return bytearray(ORIG.read_bytes()) + b'\xff' * (ROM_SIZE - ORIG.stat().st_size)


def build_reloc() -> bytearray:
    rom = expanded()
    entries = load_script()
    write_banks(rom, entries, [text.encode(e['jp']) for e in entries], sequential(TEXT_BASE, TEXT_END))
    return rom


def apply_engine(rom: bytearray, out: Path) -> bytearray:
    """VWF font + asm/vwf.asm into the expanded area; armips patches the file in place."""
    import narrow_font
    import vwf_font
    glyphs, widths = vwf_font.build(bytes(rom[:ORIG.stat().st_size]))
    rom[VWF_FONT:VWF_FONT + len(glyphs)] = glyphs
    rom[VWF_WIDTHS:VWF_WIDTHS + len(widths)] = widths
    nglyphs, nwidths = narrow_font.build(glyphs, widths)
    rom[NARROW_FONT:NARROW_FONT + len(nglyphs)] = nglyphs
    rom[NARROW_WIDTHS:NARROW_WIDTHS + len(nwidths)] = nwidths
    out.write_bytes(rom)
    res = subprocess.run([str(ARMIPS), str(ROOT / 'asm/vwf.asm'), '-strequ', 'ROM', str(out),
                          '-definelabel', 'CodeBase', hex(0x08000000 + CODE_BASE),
                          '-definelabel', 'VwfFont', hex(0x08000000 + VWF_FONT),
                          '-definelabel', 'VwfWidths', hex(0x08000000 + VWF_WIDTHS),
                          '-definelabel', 'NarrowFont', hex(0x08000000 + NARROW_FONT),
                          '-definelabel', 'NarrowWidths', hex(0x08000000 + NARROW_WIDTHS)],
                         capture_output=True, text=True, cwd=ROOT)
    if res.returncode:
        raise SystemExit('armips failed:\n' + res.stdout + res.stderr)
    return bytearray(out.read_bytes())


def build_lang(out: Path, mode: str) -> bytearray:
    """mode 'english': en fields (jp where empty); 'marker': every script entry replaced by marker filler."""
    import marker
    rom = expanded()
    entries, misc = load_script(), load_misc()
    place = sequential(TEXT_BASE, TEXT_END)
    if mode == 'marker':
        blobs = [encode_en(e, marker.marker(e, font_widths())) for e in entries]
    else:
        blobs = [encode_en(e, e['en']) for e in entries]
    write_banks(rom, entries, blobs, place)
    write_misc(rom, misc, [encode_en(e, e['en']) for e in misc], place)
    if mode == 'english':
        import gfx_build
        gfx_build.apply(rom)
    return apply_engine(rom, out)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'identity'
    BUILD.mkdir(exist_ok=True)
    out = BUILD / {'english': 'dino2_en.gba'}.get(cmd, f'{cmd}.gba')
    if cmd in ('english', 'marker'):
        rom = build_lang(out, cmd)
    else:
        rom = {'identity': build_identity, 'reloc': build_reloc}[cmd]()
    out.write_bytes(rom)
    print(out)


if __name__ == '__main__':
    main()

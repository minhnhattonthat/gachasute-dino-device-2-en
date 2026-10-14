"""UI/data strings outside the 12 script banks: every pointer table the game reads them through.

Catalog and code references: docs/re/misc_text.md. All strings use the script encoding (tools/text.py),
end in FF, and are drawn by the menu printer 0x0800D394 or inserted into dialogue by E0 12/13/18/19/1A.

TABLES rows:
  kind 'ptr'  : count u32 pointers at addr + i*stride + offset -> relocate (slots/strings below)
  kind 'skip' : catalog only, never relocated (name-entry layout, passwords, Latin model codes, charsets)
  jp          : False when every entry is fullwidth Latin/digits (already readable; English font keeps AC-DF)

Empty entries (target byte FF) are not yielded: the 256-slot word tables are mostly empty placeholders.

    python -X utf8 tools/misc_tables.py   -> counts + self-check
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import banks  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _t(name, addr, count, kind='ptr', stride=4, offset=0, jp=True, note=''):
    return dict(name=name, kind=kind, addr=addr, count=count, stride=stride, offset=offset, jp=jp, note=note)


TABLES = [
    # locations (E0 19 -> f_800D48C, E0 1A -> f_800D49C via town meta 0x080614D8)
    _t('town', 0x6105C, 5, note='town names; f_800D48C (E0 19), 0x0801B310'),
    _t('place_dyna', 0x610D8, 21, note='Dyna City places; meta 0x614D8[0], f_800D49C (E0 1A)'),
    _t('place_sancarlo', 0x61170, 21, note='meta 0x614D8[1]'),
    _t('place_atacamara', 0x61210, 21, note='meta 0x614D8[2]; 0x0800C8A0 loads 0x614E0'),
    _t('place_daostaville', 0x612AC, 21, note='meta 0x614D8[3] and [4] (both Daostaville towns share it)'),
    # people
    _t('person', 0x6143C, 37, note='opponent/NPC names, E0 18; 0x0800C458, 0x0801F8BC, 0x08026D94 (D394 0x08026DBA);'
                                   ' entries 9-32 are ＣＯＭ０９-１６ x3 (Latin)'),
    # Dino parts: E0 12 meta 0x080739B4[cat] (cat 5 -> 0x080753B4), D394 callers 0x0800D85A 0x080235F8 ...
    _t('part_head', 0x70248, 33, note='E0 12 cat 0; entry 32 is the placeholder −−−−−−−−'),
    _t('part_body', 0x707B8, 132, note='E0 12 cat 1'),
    _t('part_ride', 0x70B84, 47, note='E0 12 cat 2'),
    _t('part_corpo', 0x711E4, 157, note='E0 12 cat 3 (…コルポ, guns)'),
    _t('part_grosso', 0x71A54, 157, note='E0 12 cat 4 (…グロソ/グロッソ)'),
    _t('dino', 0x753B4, 15, note='Dino device names, E0 12 cat 5'),
    # menu word tables, index = byte id, 256 slots each (empty slots point at single FF bytes)
    _t('word_gacha', 0x74DD4, 256, note='gacha/device menu words + prices; D394 0x0802B6B2 0x08038896 0x080388F8'
                                        ' 0x0803E7D8 0x0803E840'),
    _t('word_shop', 0x757F8, 256, note='shop/medal words + prices; D394 0x0802EA5A 0x0802FFA2 0x08031ABA'
                                       ' 0x08033AD2 0x080351A2'),
    _t('word_charger', 0x799F0, 256, note='birthday/charger screen; D394 0x08040810 0x08042DAC; entry 0 = [player]'),
    # catalog only
    _t('code_head', 0x71E08, 32, kind='skip', jp=False, note='E0 13 meta 0x080739C8[0]; ＨＥＬＢ−０１Ｆ...'),
    _t('code_body', 0x723B0, 132, kind='skip', jp=False, note='E0 13 cat 1'),
    _t('code_ride', 0x72798, 47, kind='skip', jp=False, note='E0 13 cat 2'),
    _t('code_corpo', 0x72E78, 157, kind='skip', jp=False, note='E0 13 cat 3'),
    _t('code_grosso', 0x73710, 157, kind='skip', jp=False, note='E0 13 cat 4'),
    _t('code_dino', 0x752E4, 15, kind='skip', jp=False, note='E0 13 cat 5'),
    _t('passwords', 0x6ECF8, 26, kind='skip', jp=False, note='ＣＨＡＲＯ６３１...; compared with player input, keep'),
    _t('name_entry', 0x6E2C4, 300, kind='skip', stride=1, note='name entry layout: 3 pages x 5 rows x 20 glyph bytes,'
                                                                 ' no FF; 0x0801DE0C'),
]


def _ptr(rom: bytes, off: int) -> int:
    v = struct.unpack_from('<I', rom, off)[0] - 0x08000000
    assert 0 <= v < len(rom), hex(off)
    return v


def slots(rom: bytes) -> list[tuple[int, int]]:
    """(slot_offset, target_offset) for every non-empty pointer of every 'ptr' table."""
    out = []
    for t in TABLES:
        if t['kind'] != 'ptr':
            continue
        for i in range(t['count']):
            s = t['addr'] + i * t['stride'] + t['offset']
            v = _ptr(rom, s)
            if rom[v] != 0xFF:
                out.append((s, v))
    return out


def end_of(rom: bytes, a: int) -> int:
    toks = list(text.walk(rom, a))
    return toks[-1][0] + toks[-1][1]


def strings(rom: bytes) -> list[tuple[int, int]]:
    """Unique (target_offset, end_offset) in address order; end is exclusive (after the FF/FE)."""
    return [(v, end_of(rom, v)) for v in sorted({v for _, v in slots(rom)})]


if __name__ == '__main__':
    import re
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    sl, st = slots(rom), strings(rom)
    errs = []
    jp_chars = 0
    for a, e in st:
        s = text.decode(rom, a, e)
        if '[G' in s or rom[e - 1] not in (0xFE, 0xFF):
            errs.append(f'{a:06X} bad decode {s!r}')
        if a < banks.REGION[1] and e > banks.REGION[0]:
            errs.append(f'{a:06X}-{e:06X} overlaps bank region')
        jp_chars += len(re.findall(r'[ぁ-んァ-ヴー]', s))
    for (a, e), (b, _) in zip(st, st[1:]):
        if e > b:
            errs.append(f'{a:06X}-{e:06X} overlaps next string {b:06X}')
    for t in TABLES:  # table bodies must not sit inside the bank region either
        lo, hi = t['addr'], t['addr'] + t['count'] * t['stride']
        if lo < banks.REGION[1] and hi > banks.REGION[0]:
            errs.append(f"table {t['name']} overlaps bank region")
    print(f"{sum(t['kind'] == 'ptr' for t in TABLES)} ptr tables ({len(TABLES)} catalogued), {len(sl)} slots, "
          f'{len(st)} unique strings, {sum(e - a for a, e in st)} bytes, {jp_chars} kana chars')
    for t in TABLES:
        if t['kind'] == 'ptr':
            n = [v for s, v in sl if t['addr'] <= s < t['addr'] + t['count'] * t['stride']]
            print(f"  {t['name']:18s} {t['addr']:06X} slots {len(n):3d} unique {len(set(n)):3d}")
    print('\n'.join(errs) or 'self-check ok')
    sys.exit(1 if errs else 0)

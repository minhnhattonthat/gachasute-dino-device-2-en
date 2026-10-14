"""Find u32 pointers (outside the script banks) whose targets decode as FF/FE-terminated strings.

    python -X utf8 tools/scan_ptrs.py [--min-run 1] -> work/ptr_scan.txt (runs of consecutive pointer slots)
"""
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import banks  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
JP = re.compile(r'[ぁ-んァ-ヴー]')


def valid_string(rom: bytes, a: int) -> str | None:
    if not (0 < a < 0x400000):
        return None
    try:
        toks = list(text.walk(rom, a))
    except (ValueError, IndexError, KeyError):
        return None
    end = toks[-1][0] + toks[-1][1]
    if end - a > 400 or rom[toks[-1][0]] not in (0xFF, 0xFE):
        return None
    s = text.decode(rom, a, end)
    if re.search(r'\[(G|F[1-9A-F] |ret|half)', s):
        return None
    plain = re.sub(r'\[[^\]]*\]|\n', '', s)
    kana = len(JP.findall(plain)) + plain.count('　') + plain.count('・')
    if kana < 2 or kana < 0.7 * len(plain):
        return None
    return s


def scan(rom: bytes):
    skip = set()
    for lo, hi in banks.table_ranges(rom):
        skip.update(range(lo, hi, 4))
    hits = {}
    for off in range(0, len(rom) - 3, 4):
        if off in skip:
            continue
        v = struct.unpack_from('<I', rom, off)[0]
        if 0x08000000 <= v < 0x08400000:
            t = v - 0x08000000
            if banks.REGION[0] <= t < banks.REGION[1]:
                continue
            s = valid_string(rom, t)
            if s is not None:
                hits[off] = (t, s)
    runs, cur = [], []
    for off in sorted(hits):
        if cur and off != cur[-1] + 4:
            runs.append(cur)
            cur = []
        cur.append(off)
    if cur:
        runs.append(cur)
    return hits, runs


if __name__ == '__main__':
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    hits, runs = scan(rom)
    lines = []
    for r in runs:
        t0, s0 = hits[r[0]]
        lines.append(f'{r[0]:06X} n={len(r):3d} -> {t0:06X} {s0[:50]!r}')
    (ROOT / 'work').mkdir(exist_ok=True)
    (ROOT / 'work/ptr_scan.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(len(hits), 'pointers in', len(runs), 'runs -> work/ptr_scan.txt')

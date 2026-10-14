"""Dump the script banks to script/bank_BB.json (never clobbers: refuses if a file exists, unless --force).

Segments: every distinct bank-pointer target starts one; a segment runs to its end code, or to the next target
when the string falls through into it (`fall`: true). Insertion lays segments out in this same address order.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import banks  # noqa: E402
import text  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def segments(rom: bytes):
    """Return list of dicts {addr, end, ids, fall} in address order, plus gaps [(lo, hi)] not covered by text."""
    by_addr = {}
    for tid, _slot, tgt in banks.slots(rom):
        by_addr.setdefault(tgt, []).append(tid)
    starts = sorted(by_addr)
    segs = []
    for k, a in enumerate(starts):
        nxt = starts[k + 1] if k + 1 < len(starts) else banks.REGION[1]
        end = a
        fall = True
        for i, n in text.walk(rom, a):
            if i >= nxt:
                break
            end = i + n
        else:
            fall = False
        if end > nxt:
            raise ValueError(f'segment {a:#x} overruns next start {nxt:#x}')
        if fall and end != nxt:
            raise ValueError(f'segment {a:#x} falls through but stops at {end:#x} != {nxt:#x}')
        segs.append({'addr': a, 'end': end, 'ids': sorted(by_addr[a]), 'fall': fall})
    return segs


def gaps(rom: bytes, segs) -> list[tuple[int, int]]:
    covered = [(s['addr'], s['end']) for s in segs] + banks.table_ranges(rom)
    covered.sort()
    out, pos = [], banks.REGION[0]
    for lo, hi in covered:
        if lo > pos:
            out.append((pos, lo))
        pos = max(pos, hi)
    if pos < banks.REGION[1]:
        out.append((pos, banks.REGION[1]))
    return out


def dump(rom: bytes, force: bool):
    segs = segments(rom)
    files = {}
    for s in segs:
        bank = s['ids'][0] >> 8
        files.setdefault(bank, []).append({
            'addr': f"{s['addr']:05X}",
            'ids': [f'{t:04X}' for t in s['ids']],
            'fall': s['fall'],
            'jp': text.decode(rom, s['addr'], s['end']),
            'en': '',
        })
    out = ROOT / 'script'
    out.mkdir(exist_ok=True)
    for bank, entries in files.items():
        p = out / f'bank_{bank:02X}.json'
        if p.exists() and not force:
            raise SystemExit(f'{p} exists; refusing to clobber (use --force)')
        p.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
    print(len(segs), 'segments in', len(files), 'files')


if __name__ == '__main__':
    dump((ROOT / 'rom/orig.gba').read_bytes(), '--force' in sys.argv)

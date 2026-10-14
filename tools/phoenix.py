"""Phoenix variant: the Phoenix ROM differs from Dragon only in the header (title, game code, checksum byte)
and its embedded copy at 0x1D6EBE, so the Phoenix English build is the Dragon English build with those bytes.

    python -X utf8 tools/phoenix.py   -> build/dino2_en_phoenix.gba   (run build.py english first)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAGON = ROOT / 'rom/orig.gba'
PHOENIX = ROOT / 'rom/Gachasute! Dino Device 2 - Phoenix (Japan).gba'
EN = ROOT / 'build/dino2_en.gba'
OUT = ROOT / 'build/dino2_en_phoenix.gba'


def diff_ranges(a: bytes, b: bytes):
    """Byte-diff ranges of two equal-length images (gaps <= 16 merged)."""
    runs, i = [], 0
    while i < len(a):
        if a[i] != b[i]:
            j = last = i
            while j < len(a) and j - last <= 16:
                if a[j] != b[j]:
                    last = j
                j += 1
            runs.append((i, last + 1))
            i = last + 1
        else:
            i += 1
    return runs


def make(en: bytes, dragon: bytes, phoenix: bytes) -> bytes:
    assert len(dragon) == len(phoenix)
    out = bytearray(en)
    for a, b in diff_ranges(dragon, phoenix):
        assert en[a:b] == dragon[a:b], f'English build changed {a:#x}-{b:#x}; cannot swap the variant bytes'
        out[a:b] = phoenix[a:b]
    return bytes(out)


if __name__ == '__main__':
    OUT.write_bytes(make(EN.read_bytes(), DRAGON.read_bytes(), PHOENIX.read_bytes()))
    print('wrote', OUT)

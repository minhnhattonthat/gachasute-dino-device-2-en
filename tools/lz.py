"""GBA BIOS LZ77 (type 0x10): decompress, compress (VRAM-safe: no displacement 1), scan a ROM for blocks.

    python -X utf8 tools/lz.py scan [OUTDIR]   -> every pointer-referenced block that decompresses cleanly,
                                                  written as OUTDIR/<offset>.bin (default work/gfx/blocks)
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def decompress(data: bytes, off: int = 0) -> tuple[bytes, int]:
    """-> (output, end offset of the compressed stream). Raises ValueError on a malformed stream."""
    if data[off] != 0x10:
        raise ValueError('not LZ77')
    size = struct.unpack_from('<I', data, off)[0] >> 8
    out = bytearray()
    i = off + 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[i], data[i + 1]
                i += 2
                n = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError('displacement before start')
                for _ in range(n):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size]), i


def compress(src: bytes) -> bytes:
    """Greedy LZ77 with displacement >= 2 (safe for 16-bit VRAM writes)."""
    out = bytearray(struct.pack('<I', 0x10 | len(src) << 8))
    i = 0
    while i < len(src):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= len(src):
                break
            best_n, best_d = 0, 0
            for d in range(2, min(i, 0x1000) + 1):
                n = 0
                while n < 18 and i + n < len(src) and src[i + n] == src[i + n - d]:
                    n += 1
                if n > best_n:
                    best_n, best_d = n, d
                    if n == 18:
                        break
            if best_n >= 3:
                flags |= 0x80 >> bit
                v = (best_n - 3) << 12 | (best_d - 1)
                out += bytes([v >> 8, v & 0xFF])
                i += best_n
            else:
                out.append(src[i])
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def scan(rom: bytes):
    """Yield (offset, decompressed) for every u32 pointer target that is a clean LZ77 block."""
    seen = set()
    for p in range(0, len(rom) - 3, 4):
        v = struct.unpack_from('<I', rom, p)[0]
        t = v - 0x08000000
        if not (0 <= t < len(rom) - 4) or t in seen or rom[t] != 0x10:
            continue
        seen.add(t)
        size = struct.unpack_from('<I', rom, t)[0] >> 8
        if not (32 <= size <= 0x40000):
            continue
        try:
            out, _end = decompress(rom, t)
        except (ValueError, IndexError):
            continue
        yield t, out


if __name__ == '__main__':
    if sys.argv[1:2] == ['scan']:
        rom = (ROOT / 'rom/orig.gba').read_bytes()
        outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'work/gfx/blocks'
        outdir.mkdir(parents=True, exist_ok=True)
        n = 0
        for t, out in scan(rom):
            (outdir / f'{t:06X}.bin').write_bytes(out)
            n += 1
        print(n, 'blocks ->', outdir)

"""Graphics archive + "ECD" LZSS codec (docs/re/graphics.md).

    python -X utf8 tools/gfxcodec.py list [--group G]        -> every archive entry: id, offset, size, type
    python -X utf8 tools/gfxcodec.py dump G I OUT.bin        -> decompressed payload of entry (G, I)
    python -X utf8 tools/gfxcodec.py selftest                -> decompress(compress(x)) == x on real blocks

Archive: u32 table at ROM 0x08048288 -> 3 group bases; a group starts with u32 offsets (relative to the group base),
count = first offset / 4. The game's lookup is 0x08003784 (group, index) -> base + offs[index].
Entry: 4-byte magic (b'ECD\\x01' = compressed, else a plain payload such as b'IMG\\x00').
ECD header (16 bytes, big-endian): magic, u32 raw-prefix length, u32 stored length (prefix + LZSS stream),
u32 decompressed length. Then the raw prefix (copied as is), then Okumura LZSS: N=1024 ring zero-filled, start
0x3BE, flag byte LSB first, 1 = literal byte, 0 = 2 bytes b1 b2: ring pos b1 | (b2 & 0xC0) << 2, length (b2 & 0x3F) + 3.
Decoder: 0x0800639C (src, dst).
"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP_TABLE = 0x48288  # file offset of the u32 group pointer table
N_GROUPS = 3
N, F, R0 = 1024, 66, 0x3BE


def decompress(data: bytes, off: int = 0) -> bytes:
    """ECD block at data[off] -> payload. Raises ValueError on a malformed block."""
    if data[off:off + 3] != b'ECD':
        raise ValueError('not ECD')
    prefix, stored, size = struct.unpack_from('>III', data, off + 4)
    if data[off + 3] == 0:
        return bytes(data[off + 16:off + 16 + size])
    out = bytearray(data[off + 16:off + 16 + prefix])
    i, end = off + 16 + prefix, off + 16 + stored
    ring, r = bytearray(N), R0
    while i < end:
        flags = data[i]
        i += 1
        for bit in range(8):
            if i >= end:
                break
            if flags >> bit & 1:
                c = data[i]
                i += 1
                out.append(c)
                ring[r] = c
                r = (r + 1) & (N - 1)
            else:
                if i + 1 >= end:  # the game stops on a lone trailing byte too
                    i = end
                    break
                b1, b2 = data[i], data[i + 1]
                i += 2
                pos = b1 | (b2 & 0xC0) << 2
                for k in range((b2 & 0x3F) + 3):
                    c = ring[(pos + k) & (N - 1)]
                    out.append(c)
                    ring[r] = c
                    r = (r + 1) & (N - 1)
    if len(out) != size:
        raise ValueError(f'size {len(out)} != header {size}')
    return bytes(out)


def compress(src: bytes) -> bytes:
    """payload -> ECD block (greedy, hash chains; matches only reach bytes already output)."""
    body = bytearray()
    chains: dict[bytes, list[int]] = {}
    i, n = 0, len(src)
    while i < n:
        flag_pos = len(body)
        body.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_n, best_j = 0, 0
            if i + 3 <= n:
                cand = chains.get(src[i:i + 3], ())
                for j in reversed(cand):
                    if i - j > N - 1:  # shortcut: chains are never pruned, fine for blocks up to ~100 KB
                        break
                    m = 3
                    while m < F and i + m < n and src[j + m] == src[i + m]:
                        m += 1
                    if m > best_n:
                        best_n, best_j = m, j
                        if m == F:
                            break
            step = best_n if best_n >= 3 else 1
            if best_n >= 3:
                pos = (R0 + best_j) & (N - 1)
                body += bytes((pos & 0xFF, (pos >> 2) & 0xC0 | (best_n - 3)))
            else:
                flags |= 1 << bit
                body.append(src[i])
            for k in range(i, i + step):
                if k + 3 <= n:
                    chains.setdefault(src[k:k + 3], []).append(k)
            i += step
        body[flag_pos] = flags
    return b'ECD\x01' + struct.pack('>III', 0, len(body), len(src)) + bytes(body)


def groups(rom: bytes) -> list[int]:
    """-> file offset of each group base."""
    return [struct.unpack_from('<I', rom, GROUP_TABLE + 4 * g)[0] - 0x08000000 for g in range(N_GROUPS)]


def entries(rom: bytes):
    """Yield (group, index, file offset, stored size, magic). Stored size = to the next entry (or ECD length)."""
    bases = groups(rom)
    for g, base in enumerate(bases):
        cnt = struct.unpack_from('<I', rom, base)[0] // 4
        offs = struct.unpack_from(f'<{cnt}I', rom, base)
        for idx, o in enumerate(offs):
            off = base + o
            magic = rom[off:off + 4]
            if magic[:3] == b'ECD':
                size = 16 + struct.unpack_from('>I', rom, off + 8)[0]
            else:
                later = [base + x for x in offs if base + x > off] + [b for b in bases if b > off]
                size = (min(later) if later else len(rom)) - off
            yield g, idx, off, size, magic


def entry_offset(rom: bytes, group: int, index: int) -> int:
    base = groups(rom)[group]
    return base + struct.unpack_from('<I', rom, base + 4 * index)[0]


def load(rom: bytes, group: int, index: int) -> bytes:
    """Payload of an entry as the game sees it (IMG/SCR/PLT/... with its 8-byte header)."""
    off = entry_offset(rom, group, index)
    return decompress(rom, off) if rom[off:off + 3] == b'ECD' else rom[off:off + 16]  # plain: header only here


def repoint(rom: bytearray, group: int, index: int, new_off: int) -> None:
    """Point entry (group, index) at file offset new_off (anywhere after the group base)."""
    base = groups(rom)[group]
    assert new_off > base
    struct.pack_into('<I', rom, base + 4 * index, new_off - base)


def payload_type(p: bytes) -> str:
    t = p[:3].decode('latin1')
    if t in ('IMG', 'SCR'):
        return f'{t} {"8" if p[4] else "4"}bpp {p[5]}x{p[6]}' if t == 'IMG' else f'SCR {p[5]}x{p[6]} {"1" if p[4] else "2"}B'
    if t == 'PLT':
        return f'PLT {struct.unpack_from("<H", p, 4)[0]} colours'
    return t


def _selftest(rom: bytes, every: int = 1) -> None:
    n = tested = 0
    for g, i, off, size, magic in entries(rom):
        if magic[:3] != b'ECD':
            continue
        n += 1
        if n % every:
            continue
        x = decompress(rom, off)
        assert decompress(compress(x)) == x, (g, i)
        tested += 1
    for x in (b'', b'a', b'\0' * 300, bytes(range(256)) * 9):
        assert decompress(compress(x)) == x
    print(f'selftest ok: {tested} real blocks (of {n}) roundtrip')


def main(argv: list[str]) -> None:
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    cmd = argv[0] if argv else 'list'
    if cmd == 'list':
        only = int(argv[2]) if len(argv) > 2 and argv[1] == '--group' else None
        for g, i, off, size, magic in entries(rom):
            if only is not None and g != only:
                continue
            desc = magic[:3].decode('latin1')
            if magic[:3] == b'ECD':
                try:
                    desc = 'ECD ' + payload_type(decompress(rom, off))
                except ValueError as e:
                    desc = f'ECD bad ({e})'
            elif magic[:3] in (b'IMG', b'SCR', b'PLT'):
                desc = payload_type(rom[off:off + 8])
            print(f'{g} {i:4d} 0x{off:06X} 0x{size:05X} {desc}')
    elif cmd == 'dump':
        g, i = int(argv[1]), int(argv[2])
        Path(argv[3]).write_bytes(load(rom, g, i))
    elif cmd == 'selftest':
        _selftest(rom, int(argv[1]) if len(argv) > 1 else 1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])

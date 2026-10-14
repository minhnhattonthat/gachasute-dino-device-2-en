"""Script banks: text id 0xBBII -> table at 0x08061300[BB] -> u32 string pointer [II] (lookup 0x0800D468)."""
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK_TABLE = 0x61300
# bank -> entry count (tables end where the next bank's strings begin)
BANKS = {0: 144, 1: 256, 2: 256, 3: 256, 4: 256, 5: 16, 6: 27, 7: 48, 8: 5, 16: 256, 17: 256, 18: 256}
# script region (strings + interleaved tables); everything outside is untouched by the bank writer
REGION = (0x4AB10, 0x61038)


def table_off(rom: bytes, bank: int) -> int:
    return struct.unpack_from('<I', rom, BANK_TABLE + bank * 4)[0] - 0x08000000


def slots(rom: bytes):
    """Yield (text_id, slot_offset, target_offset) for every bank pointer."""
    for bank, n in BANKS.items():
        t = table_off(rom, bank)
        for i in range(n):
            v = struct.unpack_from('<I', rom, t + i * 4)[0]
            assert 0x08000000 <= v < 0x08000000 + len(rom), (bank, i, hex(v))
            yield (bank << 8) | i, t + i * 4, v - 0x08000000


def table_ranges(rom: bytes) -> list[tuple[int, int]]:
    return [(table_off(rom, b), table_off(rom, b) + 4 * n) for b, n in BANKS.items()]

"""Convert a player's .srm (EEPROM saved as byte-reversed 8-byte words, e.g. "2veDoniD") to the layout Mesen reads
("DinoDev2"), for `emu.py --sav`.

    python -X utf8 tools/savefix.py "saves/X.srm" work/saves/X.sav
"""
import sys
from pathlib import Path


def swap8(b: bytes) -> bytes:
    assert len(b) % 8 == 0
    return b''.join(b[i:i + 8][::-1] for i in range(0, len(b), 8))


if __name__ == '__main__':
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    data = src.read_bytes()
    out = swap8(data) if data[1:8] == b'veDoniD' else data  # already normal: copy
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(out)
    print(dst, 'DinoDev' in out[:16].decode('latin1') and 'header ok' or 'HEADER NOT FOUND')

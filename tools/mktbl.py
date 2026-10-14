"""Build tbl/jp.tbl from the game's font map at ROM 0x618A4 (16 rows x (16 SJIS chars + 2 pad), last row = codes 00-0F)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTMAP = 0x618A4
ROWS = 16


def font_map(rom: bytes) -> dict[int, str]:
    out = {}
    for row in range(ROWS):
        base = FONTMAP + row * 36
        for col in range(16):
            ch = rom[base + col * 2: base + col * 2 + 2].decode('shift_jis')
            out[(ROWS - 1 - row) * 16 + col] = ch
    return out


if __name__ == '__main__':
    rom = (ROOT / 'rom/orig.gba').read_bytes()
    m = font_map(rom)
    assert m[0x01] == '０' and m[0x0B] == 'あ', 'font map moved'
    lines = [f'{k:02X}={v}' for k, v in sorted(m.items())]
    (ROOT / 'tbl').mkdir(exist_ok=True)
    (ROOT / 'tbl/font.tbl').write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    print(len(lines), 'entries')

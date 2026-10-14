"""Leftover-Japanese scan of the English build: every bank + misc pointer slot the build writes, through
$SKILL/scripts/jp_left.py --slots. Exit code = jp_left's (1 if any Japanese is reachable).

    python -X utf8 tools/jpcheck.py [build/dino2_en.gba]
"""
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import banks  # noqa: E402

SKILL = ROOT / '.claude/skills/translate-retro-game/scripts'

if __name__ == '__main__':
    built = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'build/dino2_en.gba'
    rom = built.read_bytes()
    lines = [f'{slot:X}' for _tid, slot, _t in banks.slots(rom)]
    for e in json.loads((ROOT / 'script/misc.json').read_text(encoding='utf-8')):
        lines.append(e['slot'])
    out = ROOT / 'work/slots.txt'
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    # scan table: 1-byte font codes + 2-byte F0 xx glyphs (punctuation in English text) as non-Japanese symbols
    import vwf_font
    tbl = (ROOT / 'tbl/font.tbl').read_text(encoding='utf-8').splitlines()
    tbl += [f'F0{b[-1]:02X}={ch}' for ch, b in vwf_font.CHARMAP.items() if len(b) == 2]
    scan = ROOT / 'work/scan.tbl'
    scan.write_text('\n'.join(tbl) + '\n', encoding='utf-8')
    sys.exit(subprocess.call([sys.executable, '-X', 'utf8', str(SKILL / 'jp_left.py'), str(built),
                              '--tbl', str(scan), '--slots', str(out), '--min', '2']))

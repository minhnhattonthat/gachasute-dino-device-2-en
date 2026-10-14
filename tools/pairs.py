"""Reviewer input: JP/EN pairs of translated entries with visible text, in script order.

    python -X utf8 tools/pairs.py ID_FROM ID_TO OUT.txt   (inclusive bank-id range, e.g. 0100 01FF)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    lo, hi, out = int(sys.argv[1], 16), int(sys.argv[2], 16), Path(sys.argv[3])
    rows = []
    for p in sorted((ROOT / 'script').glob('bank_*.json')):
        for e in json.loads(p.read_text(encoding='utf-8')):
            tid = int(e['ids'][0], 16)
            if lo <= tid <= hi and re.search(r'[぀-ヿ]', e['jp']):
                rows.append(f">> {e['ids'][0]}\nJP: {e['jp']}\nEN: {e['en']}\n")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(rows), encoding='utf-8', newline='\n')
    print(len(rows), 'pairs ->', out)

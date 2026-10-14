"""Translation batches.

    python -X utf8 tools/batches.py make [--size 6000]   -> work/batches/bNN.json (untranslated entries, in script
                                                            order, ~size JP chars each; never overwrites existing)
    python -X utf8 tools/batches.py apply FILE.json..    -> merge {"<first id>": "<en>"} into script/*.json;
                                                            entries failing lint are reported and NOT applied
    python -X utf8 tools/batches.py status
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint  # noqa: E402
import vwf_font  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work/batches'


def load():
    files = {}
    for p in sorted((ROOT / 'script').glob('*.json')):
        files[p] = json.loads(p.read_text(encoding='utf-8'))
    return files


def save(p: Path, entries):
    p.write_text(json.dumps(entries, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')


def make(size: int):
    OUT.mkdir(parents=True, exist_ok=True)
    batch, chars, n = [], 0, len(list(OUT.glob('b[0-9][0-9].json')))
    pending = [e for es in load().values() for e in es if not e['en']]
    pending.sort(key=lambda e: int(e['addr'], 16))

    def flush():
        nonlocal batch, chars, n
        if batch:
            p = OUT / f'b{n:02d}.json'
            assert not p.exists(), p
            p.write_text(json.dumps(batch, ensure_ascii=False, indent=1) + '\n', encoding='utf-8', newline='\n')
            n += 1
        batch, chars = [], 0

    for e in pending:
        batch.append({'id': e['ids'][0], 'jp': e['jp']})
        chars += len(e['jp'])
        if chars >= size:
            flush()
    flush()
    print(n, 'batch files in', OUT)


def apply(paths):
    widths = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]
    avoid = lint.avoid_terms()
    files = load()
    by_id = {e['ids'][0]: (p, e) for p, es in files.items() for e in es}
    ok = bad = 0
    for path in paths:
        for tid, en in json.loads(Path(path).read_text(encoding='utf-8')).items():
            p, e = by_id[tid]
            errs = lint.lint_entry({**e, 'en': en}, widths, avoid)
            if errs:
                bad += 1
                for err in errs:
                    print(f'{Path(path).name} {tid}: {err}')
                continue
            e['en'] = en
            ok += 1
    for p, es in files.items():
        save(p, es)
    print(f'applied {ok}, rejected {bad}')
    return 1 if bad else 0


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'make':
        make(int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 6000)
    elif cmd == 'apply':
        sys.exit(apply(sys.argv[2:]))
    elif cmd == 'status':
        es = [e for v in load().values() for e in v]
        print(sum(bool(e['en']) for e in es), '/', len(es), 'translated')

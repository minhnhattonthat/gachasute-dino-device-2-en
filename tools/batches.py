"""Translation batches.

    python -X utf8 tools/batches.py make [--size 3500]   -> work/batches/bNN.json (untranslated entries, in script
                                                            order, ~size JP chars each; never overwrites existing)
    python -X utf8 tools/batches.py apply FILE.json..    -> merge {"<first id>": "<en>"} into script/*.json;
                                                            entries failing lint are reported and NOT applied
    python -X utf8 tools/batches.py check bNN            -> validate work/batches/bNN.out.json against bNN.json
    python -X utf8 tools/batches.py autofill             -> entries with no visible text get en = jp
    python -X utf8 tools/batches.py status
"""
import re
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


def eid(e: dict) -> str:
    return e.get('id') or e['ids'][0]


def has_text(jp: str) -> bool:
    return bool(re.sub(r'\[[^\]]*\]|\n', '', jp))


def has_kana(jp: str) -> bool:
    return bool(re.search(r'[぀-ヿ一-鿿]', jp))


def autofill():
    """No visible text: en = jp. No kana (numbers, Latin codes): en = ASCII form without padding."""
    import unicodedata
    files = load()
    n = 0
    for p, es in files.items():
        for e in es:
            if e['en']:
                continue
            if not has_text(e['jp']):
                e['en'] = e['jp']
            elif not has_kana(e['jp']):
                e['en'] = unicodedata.normalize('NFKC', e['jp'].replace('　', '')).replace('−', '-')
            else:
                continue
            n += 1
        save(p, es)
    print('autofilled', n)


def check(name: str) -> int:
    src = json.loads((OUT / f'{name}.json').read_text(encoding='utf-8'))
    out_p = OUT / f'{name}.out.json'
    if not out_p.exists():
        print(f'missing {out_p}')
        return 1
    try:
        out = json.loads(out_p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as ex:
        print(f'{out_p.name}: invalid JSON: {ex}')
        return 1
    widths = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]
    avoid = lint.avoid_terms()
    want = [e['id'] for e in src]
    errs = []
    if sorted(out) != sorted(want):
        errs.append(f'id set differs: missing {sorted(set(want) - set(out))} extra {sorted(set(out) - set(want))}')
    for e in src:
        en = out.get(e['id'])
        if en is None:
            continue
        if not en.strip():
            errs.append(f"{e['id']}: empty")
        for err in lint.lint_entry({'jp': e['jp'], 'en': en}, widths, avoid):
            errs.append(f"{e['id']}: {err}")
    for err in errs:
        print(err)
    print('OK' if not errs else f'{len(errs)} problems')
    return 1 if errs else 0


def make(size: int):
    OUT.mkdir(parents=True, exist_ok=True)
    batch, chars, n = [], 0, len(list(OUT.glob('b[0-9][0-9].json')))
    pending = [e for es in load().values() for e in es if not e['en'] and has_text(e['jp'])]
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
        batch.append({'id': eid(e), 'jp': e['jp']})
        chars += len(e['jp'])
        if chars >= size:
            flush()
    flush()
    print(n, 'batch files in', OUT)


def apply(paths):
    widths = vwf_font.build((ROOT / 'rom/orig.gba').read_bytes())[1]
    avoid = lint.avoid_terms()
    files = load()
    by_id = {eid(e): (p, e) for p, es in files.items() for e in es}
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
        make(int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 3500)
    elif cmd == 'apply':
        sys.exit(apply(sys.argv[2:]))
    elif cmd == 'check':
        sys.exit(check(sys.argv[2]))
    elif cmd == 'autofill':
        autofill()
    elif cmd == 'status':
        es = [e for v in load().values() for e in v]
        print(sum(bool(e['en']) for e in es), '/', len(es), 'translated')

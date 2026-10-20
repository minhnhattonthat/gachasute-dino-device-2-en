"""Release gate + package: check -> build -> leftover-JP scan -> smoke -> BPS (re-applied and verified) -> zip.

    python -X utf8 tools/release.py [--version 1.0]   -> release/Gachasute_Dino_Device_2_{Dragon,Phoenix}_EN_v<ver>.zip
Stops at the first failure. Never publishes anything.
"""
import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# newest installed copy of the translate-retro-game plugin
SKILL = max((Path.home() / '.claude/plugins/cache/retro-translation/translate-retro-game').glob('*/skills/translate-retro-game/scripts'),
           key=lambda p: p.stat().st_mtime)
PY = [sys.executable, '-X', 'utf8']
# (name, original ROM, English build): the Phoenix build is the Dragon build with the Phoenix header (tools/phoenix.py)
VARIANTS = [('Dragon', 'rom/orig.gba', 'build/dino2_en.gba'),
            ('Phoenix', 'rom/Gachasute! Dino Device 2 - Phoenix (Japan).gba', 'build/dino2_en_phoenix.gba')]


def run(*args):
    print('>', ' '.join(str(a) for a in args[2:]))
    if subprocess.call(list(args), cwd=ROOT):
        sys.exit(f'release stopped: {args[2:]} failed')


def hashes(b: bytes) -> str:
    return (f'CRC32 {zlib.crc32(b):08X}, MD5 {hashlib.md5(b).hexdigest()}, SHA-1 {hashlib.sha1(b).hexdigest()}, '
            f'{len(b)} bytes')


def main():
    ver = sys.argv[sys.argv.index('--version') + 1] if '--version' in sys.argv else '1.0'
    run(*PY, 'tools/check.py')
    run(*PY, 'build.py', 'english')
    run(*PY, 'tools/jpcheck.py')
    run(*PY, 'tools/phoenix.py')
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    for name, base, build in VARIANTS:
        run(*PY, str(SKILL / 'emu.py'), build, '--out', f'work/qa/release_smoke_{name}',
            '--route', 'tools/routes/boot.txt', '--smoke')
        pkg = f'Gachasute_Dino_Device_2_{name}_EN_v{ver}'
        bps = out / f'{pkg}.bps'
        run(*PY, str(SKILL / 'bps.py'), 'make', base, build, str(bps))
        check = ROOT / 'work/release_check.gba'
        run(*PY, str(SKILL / 'bps.py'), 'apply', base, str(bps), str(check))
        built = (ROOT / build).read_bytes()
        if check.read_bytes() != built:
            sys.exit(f'release stopped: re-applied {name} patch differs from the build')
        orig = (ROOT / base).read_bytes()
        readme = (ROOT / 'docs/README_release.txt').read_text(encoding='utf-8')
        readme = (readme.replace('{VERSION}', ver).replace('{NAME}', name)
                  .replace('{ORIG}', hashes(orig)).replace('{PATCHED}', hashes(built)))
        with zipfile.ZipFile(out / f'{pkg}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
            z.write(bps, bps.name)
            z.writestr('README.txt', readme.replace('\n', '\r\n'))
        print('release ok:', out / f'{pkg}.zip')


if __name__ == '__main__':
    main()

"""Release gate + package: check -> build -> leftover-JP scan -> smoke -> BPS (re-applied and verified) -> zip.

    python -X utf8 tools/release.py [--version 1.0]   -> release/Gachasute_Dino_Device_2_Dragon_EN_v<ver>.zip
Stops at the first failure. Never publishes anything.
"""
import hashlib
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.claude/skills/translate-retro-game/scripts'
PY = [sys.executable, '-X', 'utf8']


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
    run(*PY, str(SKILL / 'emu.py'), 'build/dino2_en.gba', '--out', 'work/qa/release_smoke',
        '--route', 'tools/routes/boot.txt', '--smoke')
    out = ROOT / 'release'
    out.mkdir(exist_ok=True)
    name = f'Gachasute_Dino_Device_2_Dragon_EN_v{ver}'
    bps = out / f'{name}.bps'
    run(*PY, str(SKILL / 'bps.py'), 'make', 'rom/orig.gba', 'build/dino2_en.gba', str(bps))
    check = ROOT / 'work/release_check.gba'
    run(*PY, str(SKILL / 'bps.py'), 'apply', 'rom/orig.gba', str(bps), str(check))
    built = (ROOT / 'build/dino2_en.gba').read_bytes()
    if check.read_bytes() != built:
        sys.exit('release stopped: re-applied patch differs from the build')
    orig = (ROOT / 'rom/orig.gba').read_bytes()
    readme = (ROOT / 'docs/README_release.txt').read_text(encoding='utf-8')
    readme = readme.replace('{VERSION}', ver).replace('{ORIG}', hashes(orig)).replace('{PATCHED}', hashes(built))
    with zipfile.ZipFile(out / f'{name}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(bps, bps.name)
        z.writestr('README.txt', readme.replace('\n', '\r\n'))
    print('release ok:', out / f'{name}.zip')


if __name__ == '__main__':
    main()

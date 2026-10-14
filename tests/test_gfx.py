import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import gfx_build as GB  # noqa: E402
import gfxcodec as G  # noqa: E402

ROM = (ROOT / 'rom/orig.gba').read_bytes()


def test_pat_roundtrip():
    for i in (2997, 3120):
        p = G.load(ROM, 1, i)  # a plain entry: its size runs into the padding before the next entry
        q = GB.pat_build(GB.pat_parse(p))
        assert p[:len(q)] == q and not any(p[len(q):])


def test_applied_maps_show_the_pngs():
    rom = bytearray(ROM) + b'\xff' * (0x800000 - len(ROM))
    GB.apply(rom)
    logo = [G.load(rom, 1, 2982)[8 + i:8 + i + 64] for i in range(0, len(G.load(rom, 1, 2982)) - 8, 64)]
    shown = GB.render_map(logo, struct.unpack_from('<600H', G.load(rom, 1, 2984), 8), 30, 20)
    assert shown.tobytes() == GB.load_png('title_logo.png').tobytes()
    intro = GB.tiles4(G.load(rom, 1, 3019)[8:])
    png = GB.load_png('intro_logo.png')
    for i, x in ((3021, 0), (3022, 256)):
        shown = GB.render_map(intro, struct.unpack_from('<640H', G.load(rom, 1, i), 8), 32, 20)
        assert shown.tobytes() == bytes(c & 15 for c in png.crop((x, 0, x + 256, 160)).tobytes())
    assert GB.intro_index(rom, 3020).tobytes() == GB.intro_index(ROM, 3020).tobytes()

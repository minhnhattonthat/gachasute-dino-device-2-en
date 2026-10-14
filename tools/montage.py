"""Zoomed contact sheet of chosen frames: 2 columns at 2x (960 px wide), labelled.

    python -X utf8 tools/montage.py DIR OUT.png f000060 f000180 ...     (frame names without .png)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d, out, names = Path(sys.argv[1]), sys.argv[2], sys.argv[3:]
rows = (len(names) + 1) // 2
sheet = Image.new('RGB', (960, rows * 320), (60, 0, 60))
for i, n in enumerate(names):
    im = Image.open(d / f'{n}.png').convert('RGB').resize((480, 320), Image.NEAREST)
    ImageDraw.Draw(im).text((3, 3), n, fill=(255, 255, 0))
    sheet.paste(im, ((i % 2) * 480, (i // 2) * 320))
sheet.save(out)

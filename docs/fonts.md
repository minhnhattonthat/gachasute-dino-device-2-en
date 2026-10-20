# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| tools/vwf_font.py (generated) | the game's own 8x8 font, read from the user's dump at build time | game's | yes: not stored here, rebuilt from the dump | dialogue and menu VWF | Latin glyphs trimmed to their ink, per-glyph widths |
| tools/narrow_font.py | drawn for this project (pixel art as text) | MIT, same as repo | yes | condensed font for names over their slot | - |
| gfx/*.png | the game's graphics, English lettering drawn for this project | game art: (c) Rocket Company; lettering MIT | as a patch only (diff against the dump) | title logo, menus, catalog tabs, battle SFX | Japanese lettering redrawn in English |

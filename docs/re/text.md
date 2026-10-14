# Text system

## Encoding
- 1 byte per glyph, codes 00-DF = font glyph index. Table `tbl/font.tbl` built by `tools/mktbl.py` from the
  game's own SJIS font map at ROM 0x618A4 (16 rows of 16 SJIS chars + 4 pad bytes, row 0 in memory = codes F0-FF,
  last row = codes 00-0F). Used by name entry too (to be confirmed).
- 00 = full-width space, 01-0A = digits, 0B.. hiragana, katakana, A-Z (C4..), a-z, E0-EF row = ▼▶？！"％＆’（）「」ー〜：…,
  F0-FF row = ・．、。＠−＋＝／ etc.
- Glyphs >= E0 are written `F0 xx` in text (prefix F0-F7/FA/FB: glyph = ((c&0xF)<<8)|next byte, up to 0xFFF).

## Interpreter (dialogue)
- State struct 0x0200471C: +0x14 text pointer, +0x1C current char, +0x30 map position, +0x34 tile index counter.
- Main loop 0x0800D274; dispatch table 0x0800D2A8 for E0-FF:
  E0 cmd (subcmd table, docs/re/ctrl_codes.md), F8 newline (0x0800BFC4), F9 (0x0800BF80), FC page/wait (0x0800BF34),
  FD (0x0800BF04), FE (0x0800BEAC), FF (0x0800BE9C).
- Glyph draw 0x0800D210 -> 0x0800BE08 -> 0x0800BD70: 1 glyph = one 8x8 4bpp tile, DMA'd to VRAM, one map entry.

## Font
- 1bpp 8x8, 8 bytes/glyph at ROM 0x1D5A38, 256 glyphs used (0x100-0x1BF blank, then other data).
  Pixel colours: bit set/clear chooses bg / fg with a shadow colour (renderer 0x0800BD70).
- Dialogue box: 3 lines x 20 cells (8 px each), 16 px line pitch. English needs a VWF (phase 4).

## Text locations
- Script text is uncompressed in ROM around 0x4A000-0x62000 (+ more elsewhere, e.g. 0x7571F). Opening scene
  0x4BE9D.. (pointer at word targets 0x4BE9D / 0x4C0DE). Comm-mode messages: pointer table 0x4B3DC.. (~u32 each).

## Routes
- Title at ~f1450: `1450 -;6 start;200 -;6 start;200 -;6 a` then mash A 60 -> opening dialogue (~f2000),
  name entry at ~f3800 (state work/states/name_entry.mss). Start on name entry jumps to けってい.

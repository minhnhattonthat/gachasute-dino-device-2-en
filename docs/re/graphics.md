# Graphics: archive, ECD compression, title logo

Tool: `tools/gfxcodec.py` (`list`, `dump G I OUT`, `selftest`; `decompress`, `compress`, `entries`, `load`,
`repoint` for build code). All 570 ECD blocks in the ROM roundtrip (`decompress(compress(x)) == x`).

## Archive

- u32 table at ROM `0x08048288`: 3 group base pointers (file 0x1D8604, 0x1DDC44, 0x3619C4).
- A group starts with a u32 offset table, offsets relative to the group base; count = first offset / 4
  (group 0: 40, group 1: 3180, group 2: 1496 entries). Offset 0 = empty slot. Entries have no size field;
  the size comes from the ECD header or the payload header.
- Game lookup: `0x08003784 (group, index) -> base + offs[index]`. Entry ids below are `group/index`.
- Entry = ECD-compressed payload (`ECD\x01`) or a plain payload. Payload types (8-byte header, data at +8):
  - `IMG`: raw GBA tiles, [5] = w, [6] = h tiles of 32 B ([4] = 0) or 64 B. The BG/OBJ mode decides the bpp:
    the 8bpp title logo has [4] = 0 and 16 KB = 512x32 B = 256 8bpp tiles.
  - `SCR`: tilemap [5] x [6], 2-byte GBA text-BG entries when [4] = 0, copied as rows into the screen block.
  - `PLT`: u16 LE colour count at [4], BGR555 at +8.
  - `PAT`, `TIM`: sprite animation (patterns, timing), `TON`: sound, plain (never compressed).
- Loaders: `0x0800379C` (decompress straight to a buffer), `0x080038C8` / `0x080039D8` / `0x08003AD4`
  (IMG / PLT / SCR: lookup, decompress to a heap buffer, then the rect copier `0x08002700` writes VRAM/palette
  with CPU `strh`, no DMA, no BIOS SWI). The VRAM destination comes from the scene code, not the archive.

## ECD format (decoder `0x0800639C (src, dst)`)

16-byte header, big-endian: `"ECD"`, u8 1 = compressed, u32 raw-prefix length, u32 stored length (prefix +
LZSS stream), u32 decompressed length (the loader allocates only the low 16 bits: keep payloads < 64 KB).
Then the raw prefix (copied as is; every block in the ROM has prefix 0), then Okumura LZSS:
ring N = 1024 bytes zero-filled, write position starts at 0x3BE; flag byte read LSB first; bit 1 = literal
byte; bit 0 = 2 bytes `b1 b2`: ring position `b1 | (b2 & 0xC0) << 2`, length `(b2 & 0x3F) + 3` (3..66).
Decoding stops when the stored length is used up. Output goes through a byte writer (`0x08006334`) into RAM.
The game decodes slowly (16 KB takes ~14 frames).

`compress()` is greedy with hash chains and only matches bytes already output; its output size is within
1% of the original (logo tiles: 8370 vs 8382 bytes).

## Title screen (cold boot, no input: attract intro, title fully shown from ~f3260; dump at f3400)

DISPCNT 0x1C00: mode 0, BG2 + BG3 + OBJ (2D OBJ mapping).

| What | Entry | ROM (file) | Stored | Goes to |
|---|---|---|---|---|
| Logo tiles ガチャステ！ダイナデバイス 2 / DINO DEVICE | 1/2982 IMG 32x16 | 0x2CABC4 | 0x20BE | BG2 tiles 0x06008000, **8bpp** (256 tiles), BG2CNT 0x1E8A |
| Logo palette | 1/2983 PLT 112 | 0x2CCC84 | 0x114 | BG palette 0-111 |
| Logo map | 1/2984 SCR 30x20 | 0x2CCDA4 | 0x22A | BG2 screen block 30 (0x0600F000), no tile offset added |
| Dragon background (no text) | 1/2985 IMG, 1/2986 SCR, 1/2989 PLT, 0/2 PLT | 0x2CCFD4.. | | BG3 4bpp tiles 0x06000000, map 0x0600F800, pal banks 10, 15 |
| OBJ sheet: ドラゴン, PUSH START BUTTON, © 2003 ロケットカンパニー, menu はじめから / つうしん / つづき, フェニックス (other version) | 1/2995 IMG 32x17 | 0x2DA434 | 0x1AB2 | OBJ tiles 0x06010000, 4bpp, 2D map (32 tiles wide) |
| OBJ palette | 1/2996 PLT 64 | 0x2DBEF4 | 0x94 | OBJ palette banks 0-3 (text uses bank 2) |
| OBJ animation | 1/2997 PAT, 1/2998 TIM | 0x2DBF94, 0x2DC414 | plain | sprite layout (ドラゴン = OAM tiles 426.., © line = tiles 512..) |

So "© 2003 ロケットカンパニー" and "PUSH START BUTTON" are graphics (OBJ), not font text.

## Repointing and free space

The 4 MiB ROM is full (data to 0x3FF3FC). Expand to 8 MiB (pad 0xFF) and put new blocks at 0x400000+.
Repoint = rewrite the entry's u32 in its group table: `offs[index] = new_off - group_base`
(`gfxcodec.repoint(rom, group, index, new_off)`). Nothing else references the block. Proven:
logo tiles with palette indices 1..111 reversed, recompressed, written at 0x700000 in `build/gfxtest.gba`,
entry 1/2982 repointed -> the title shows the recoloured logo, rest of the screen intact.

Free-space needs for the title: ~8.4 KB (logo tiles) + 0.6 KB (map) + ~7 KB (OBJ sheet), more if the English
logo needs more tiles. Not tested: a bigger IMG than 256 8bpp tiles (the copy size follows the IMG header;
BG2 tiles must stay below the maps at 0x0600F000, i.e. at most 448 8bpp tiles).

## Graphics-text survey (stub)

| Screen | Text | Source | How to reach |
|---|---|---|---|
| Title | logo ガチャステ！ダイナデバイス 2, ドラゴン, © 2003 ロケットカンパニー | 1/2982-2984 (BG2), 1/2995-2998 (OBJ) | cold boot, ~f3260 |
| Title menu | はじめから / つうしん / つづき | OBJ sheet 1/2995 | Start on the title |
| Intro | big scrolling logo (silver band) | 1/3019 IMG, maps 1/3020-3022 (plain SCR), PLT 1/3023 | cold boot ~f2600-2720 |
| Name entry and status UI | かな / カナ / ABC buttons, 年月日, ビット (BIT); EXP, LV, NEXT, STATUS, INPUT A NAME already English | UI sheet 1/2966 (IMG 32x8, BG tiles at 0x06004000) | `work/states/name_entry.mss` |
| Name entry | L / R arrow buttons (no Japanese) | OBJ 1/2978 | same |
| Name entry | grid kana, もどる / けってい, STARTボタンでしゅうりょうします | font (391 tiles not in any IMG) | text work, not graphics |
| Battle / other menus | not surveyed yet | dump VRAM, then `vramfind.py VRAM imgs/` with every IMG payload extracted | |

Finding the source of any screen: extract every IMG payload (`gfxcodec.entries` + `load`, strip 8 bytes) to a
directory, dump VRAM on the screen (`probes/ppudump.lua`), run `vramfind.py VRAM DIR --fmt gba4`. To see which
entries a scene loads: exec hook on `0x08003784`, log r0/r1.

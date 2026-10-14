# UI and data text outside the script banks

Every Japanese string the game can show that is not in the 12 script banks (0x4AB10-0x61038). Machine-readable list:
`tools/misc_tables.py` (`TABLES`, `slots(rom)`, `strings(rom)`; `python -X utf8 tools/misc_tables.py` self-checks).
Addresses are file offsets (ROM address - 0x08000000). Code addresses are full ROM addresses.

## Summary

- 15 pointer tables to relocate, all plain `u32` arrays (stride 4, offset 0). There are no struct-embedded or
  fixed-length text fields: every string is reached through a pointer and ends in FF.
- 767 non-empty slots, 767 unique strings (no two slots share a target), 6577 bytes, 5500 glyphs, 4704 kana.
- All strings sit in 0x61038-0x614D0, 0x7010C-0x71CC8, 0x74B94-0x74DD4, 0x7524C-0x753B2, 0x755A0-0x757F6 and
  0x79894-0x799EF. Layout pattern: a block of strings, then the pointer table that indexes it.
- All of them are drawn through the menu printer `0x0800D394` (struct +0 = text pointer), or inserted into dialogue
  by E0 12/13/18/19/1A (interpreter mode 7, same VWF path). None goes through a fixed-cell drawer.
- Encoding = script encoding (tools/text.py). The only control code is `[player]` (E0 14), in word_charger[0].
  `ー` is `F0 EC`.

## Tables to relocate (`kind='ptr'`)

| name | table | n | non-empty | strings | content | referenced by (literal at -> D394 call) |
|---|---|---|---|---|---|---|
| town | 0x6105C | 5 | 5 | 0x61038-0x6105B | town names ダイナシティ, サンカルロ, アタカマラ, ダオスタヴィル x2 | f_800D48C (E0 19, literal 0x0800D498); map label 0x0801B310 |
| place_dyna | 0x610D8 | 21 | 15 | 0x61070-0x610D6 | places in town 0 (みさりのいえ, ゆうびんきょく...) | town meta 0x080614D8[0] -> f_800D49C (E0 1A, literal 0x0800D4E0); 0x0801B342 |
| place_sancarlo | 0x61170 | 21 | 9 | 0x6112C-0x6116E | places in town 1 | meta 0x614D8[1] |
| place_atacamara | 0x61210 | 21 | 9 | 0x611C4-0x6120F | places in town 2 | meta 0x614D8[2]; 0x0800C8A0 loads 0x080614E0 (= meta+8) |
| place_daostaville | 0x612AC | 21 | 9 | 0x61264-0x612AB | places in towns 3 and 4 | meta 0x614D8[3] **and** [4] (one table, two towns) |
| person | 0x6143C | 37 | 36 | 0x6134C-0x6143B | opponent/NPC names; [0] empty (E0 18 falls back to E0 14); [9-32] = ＣＯＭ０９-ＣＯＭ１６ x3 | E0 18 (0x0800C458); 0x0801F8BC -> 0x0801F91C (battle roster); 0x08026D94/0x08026DC8 -> 0x08026DBA |
| part_head | 0x70248 | 33 | 33 | 0x7010C-0x70247 | …コアヘッド etc.; [32] = placeholder −−−−−−−− | part meta 0x080739B4[0] |
| part_body | 0x707B8 | 132 | 132 | 0x702CC-0x707B7 | …ボディ, …Ｆ/Ｗ/Ｔ/Ｅ/Ｓ | meta 0x739B4[1] |
| part_ride | 0x70B84 | 47 | 47 | 0x709C8-0x70B82 | …ライド, デュオ… | meta 0x739B4[2] |
| part_corpo | 0x711E4 | 157 | 157 | 0x70C40-0x711E1 | …コルポ, ヒート…ガン | meta 0x739B4[3] |
| part_grosso | 0x71A54 | 157 | 157 | 0x71458-0x71A53 | …グロソ/グロッソ | meta 0x739B4[4] |
| dino | 0x753B4 | 15 | 15 | 0x75320-0x753B2 | Dino device names (エルフェーン, ガルザイン, チラザフェルト...) | part code path "cat 5" (see below) |
| word_gacha | 0x74DD4 | 256 | 87 | 0x74B94-0x74DD3 | gacha/device menu words (ねだん, しゅつげん, ヘッド, つかうメダルを / えらんでください, パスワード...) + price strings | 0x0802B6C0 -> 0x0802B6B2; 0x080388A4 -> 0x08038896; 0x08038904 -> 0x080388F8 (index via byte map 0x080785C8); 0x0803E7E4 -> 0x0803E7D8; 0x0803E84C -> 0x0803E840 |
| word_shop | 0x757F8 | 256 | 46 | 0x755A0-0x757F5 | medals, Ｄバースト, prizes (ブロンズメダル３まい...), prices, かう/うる/カタログはんばい/バッテリーチャージ, shop + town names | 0x0802EA68 -> 0x0802EA5A; 0x0802FFB0 -> 0x0802FFA2; 0x08031AC8 -> 0x08031ABA; 0x08033AE0 -> 0x08033AD2; 0x080351B0 -> 0x080351A2 |
| word_charger | 0x799F0 | 256 | 10 | 0x79894-0x799EF | birthday / Dyna Charger screen (たんじょうびを…, Ａボタンで…, カードポイント, うまれ); [0] = `[player]` | 0x0804081C -> 0x08040810; 0x08042DB8 -> 0x08042DAC |

**Part/Dino names.** E0 12 and the part menus index the meta table 0x080739B4 (5 words: head, body, ride, corpo,
grosso tables) with a category byte; category 5 uses 0x080753B4 (dino) instead. Literals for 0x739B4 / 0x753B4:
0x0800C324/0x0800C340 (E0 12), 0x0800D84C/0x0800D86C (-> D394 0x0800D85A), 0x080235C4/0x0802360C (-> 0x080235F8),
0x080236E4/0x08023718 (-> 0x08023704), 0x0802CE34/0x0802CE44/0x0802CE8C (-> 0x0802CE64), 0x08033B8C/0x08033B9C/
0x08033BE4 (-> 0x08033BBC), 0x0803BCB0/0x0803BC68 (-> 0x0803BC9A), 0x080448FC/0x080448B8 (-> 0x080448E6). Meta
words also appear as data at 0x0806143C+0x94/+0x98 (0x614D0 = 0x080739C8, 0x614D4 = 0x080739B4). The meta tables
stay put; only the 15 tables above need repointing.

**Town meta 0x080614D8** = {0x610D8, 0x61170, 0x61210, 0x612AC, 0x612AC}, indexed by town; f_800D49C picks the
place via per-town (flag, index) lists at 0x0806E034.

## Catalog only (`kind='skip'`, not relocated)

| name | table | n | strings | why |
|---|---|---|---|---|
| code_head / body / ride / corpo / grosso | 0x71E08 / 0x723B0 / 0x72798 / 0x72E78 / 0x73710 | 32/132/47/157/157 | 0x71CC8-0x73983 | part model codes ＨＥＬＢ−０１Ｆ…, fullwidth Latin (English font keeps AC-DF). E0 13 meta 0x080739C8 (literals 0x0800C368, 0x0800D814 -> 0x0800D826, 0x080234E8 -> 0x0802351C, 0x08023698 -> 0x080236CC, 0x0802CE0C, 0x08033B64, 0x0803BC7C, 0x080448CC). Original typo: two codes use ー instead of − (ＨＳＥＲー０１Ｗ, ＢＳＥＲー０１Ｗ) |
| code_dino | 0x752E4 | 15 | 0x7524C-0x752E2 | dino codes ＣＥＬＢ−０１Ｆ…; E0 13 cat 5 (0x0800C384, 0x0800D848, 0x08023530, 0x080236E0, 0x0802CE1C, 0x08033B74, 0x0803BC54, 0x080448A8) |
| passwords | 0x6ECF8 | 26 | 0x6EC0C-0x6ECF6 | ＣＨＡＲＯ６３１…; compared with player input (literal 0x08024530). Do not translate |
| name_entry | 0x6E2C4 | 300 bytes | - | **name entry layout**: 3 pages (hiragana, katakana, Latin+digits) x 5 rows x 20 glyph bytes, FE/FF = blank cells, no terminators. Drawn as a raw tilemap (glyph byte = tile, 8 px cells) by 0x0801DD10; cursor lookup 0x0801DE0C; 0x0801DDF0 uploads all 256 glyphs as tiles |

Also present but not text to translate: password character/scramble tables 0x73A4C-0x73DA2 (used by 0x08027788..
0x08028C64), 0x746F6-0x748FF, the kana grid 0x74AA0-0x74ACC (0x0802A008..0x0802A068), digit+kana charsets 0x75F08,
0x79EB8, 0x7A5B4, 0x7A69C. They hold kana bytes but are lookup data; changing them would break passwords.

## Drawing paths and risks

- **Non-VWF drawers.** The direct calls to the cell drawer 0x0800BE08 draw single glyphs, not strings:
  0x0800DD46, 0x08010932 and 0x0801B614 draw ▶ (glyph E1); 0x08010948 draws a blank (00); 0x0801B4FA draws glyph FA
  inside a number printer; 0x0801DDF0 is the name-entry font upload. The only fixed-8px text is the name-entry grid
  above. No table string bypasses D394/dialogue.
- **Other D394 sources** (no ROM strings): script ids via 0x0800D468 (bank text, e.g. 0x0801006C, 0x08010904,
  0x0801B5F8, 0x080243B2-0x080243E2, 0x08025xxx), bank 0 table 0x4B3DC (inside the bank region), and RAM buffers:
  name-entry buffer 0x020046A8 (0x0801DE8E, 0x0801DF2C, 0x080244AC), player name copy 0x02004760 (0x08026D58,
  0x0801F91C). 0x0801F27A prints the 7-char ASCII build code '031019C' at 0x4A288, converted through the
  ASCII->glyph map 0x0806E4CC (Latin/digits only, nothing to translate).
- **No fixed-length fields** in ROM: no string is embedded in a struct, every one is FF-terminated, so English can
  grow freely once repointed.
- **Fixed-width padding / window widths.** Names are padded with fullwidth spaces to 8 cells (dino names, part
  names max 8 glyphs, person max 8, word_shop town names 'ダイナシティ　　'), and word_charger[2] is centred with spaces.
  The menu windows are sized by the callers' D394 structs (+8/+A/+C halfwords) for 8-cell names. Longer English
  names need the window widths checked in-game (width gate) or VWF-measured limits per table.
- **Player/partner names** live in 8-byte save fields 0x0200495E / 0x02004966 (name entry limit 8 glyph bytes).
- **Index-keyed tables.** word_gacha/word_shop/word_charger are indexed by byte id (0x080785C8 maps some ids):
  keep all 256 slots. Empty slots point at single FF bytes and are left alone (`slots()` skips them).
- **Duplicate text, not shared pointers.** No two slots point at the same string, but texts repeat (town[3]/[4]
  ダオスタヴィル, person ＣＯＭ０９-１６ three times, word_shop Ｄバースト x5, prices in word_gacha). A relocator may
  deduplicate. place_daostaville is one table used for two towns.
- **Duplicated terms across tables:** town names appear in `town` and again in word_shop[81-85]; medal names in
  word_shop, word_charger and word_gacha (ゴールド/シルバー/ブロンズ). Keep translations in sync via glossary.md.

## How this was checked

- Pointer scan of every aligned word in the ROM against FF/FE-terminated decodable strings (tools/scan_ptrs.py,
  plus a run detector over 0x61038-0x80000): every clean multi-kana string in the data area is either in one of the
  tables above, in the name-entry/password data, or random bytes (map/graphics data at 0x62000-0x6DFFF and
  0x7B000-0x80000). Nothing past 0x80000 is text (graphics); code below 0x4AB10 only has ASCII debug strings.
- Vocabulary search (メダル, ガチャ, デバイス, パスワード, バッテリー, ヘッド, ボディ, ...): every hit lies in the banks or
  in these tables.
- Code xrefs for each table base: `disasm.py xref rom/orig.gba 0x08074DD4` etc. The 70 D394 callers were
  checked for the literal/call that feeds the text pointer (table, script id or RAM buffer); callers that reuse a
  pointer set by an earlier call (0x08011798, 0x0801B1E6, 0x0802B90C, 0x080302FC, 0x08038F70, 0x0803E8B4) were
  not traced individually.
- Unverified: the exact meaning of the 0x614D0/0x614D4 data words and of 0x0800C8A0's use of meta+8; neither
  affects relocation.

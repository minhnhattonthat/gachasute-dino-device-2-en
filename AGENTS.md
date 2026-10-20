# Gachasute! Dino Device 2 - Dragon (GBA) English translation

Skill: translate-retro-game (plugin translate-retro-game@retro-translation).
Read it before ROM, text or QA work. `$SKILL` below = that directory.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py english` -> build/dino2_en.gba (8 MiB). Also `identity` (== original), `marker`, `reloc`.
- Check:    `python -X utf8 tools/check.py` (pytest: identity, roundtrip, lint, tools; the pre-commit hook runs it)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/dino2_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- JP scan:  `python -X utf8 tools/jpcheck.py` (every bank + name-table pointer slot; must print 0 runs)
- Text:     batches `tools/batches.py make|check|apply|status`; dry-run wrap `tools/fit.py "text"`; review pairs `tools/pairs.py`.
- Release:  `python -X utf8 tools/release.py --version X.Y` -> release/*.zip, one per variant (gate + BPS + verify; never publish without the user)
- Phoenix:  `python -X utf8 tools/phoenix.py` -> build/dino2_en_phoenix.gba. The Phoenix ROM (rom/Gachasute! ... Phoenix (Japan).gba,
  SHA-1 a209ab6e216a1054961bb25c26aef79c749e2d67) differs from Dragon only in the header + a copy at 0x1D6EBE, so it reuses the
  Dragon build with those bytes swapped (tests/test_phoenix.py guards that). Saves for both in saves/ (Dragon: late game at Daostaville Fortress; Phoenix: Dino City, 51000 bits).

## Paths
- Original ROM: `rom/orig.gba` (gitignored; SHA-1 8bb322121ca889ed8a7b22a907cd835e23fd4449, CRC32 A63DFD2C, EEPROM_V124).
- Emulator `tools/mesen2/Mesen.exe` (+Firmware/gba_bios.bin); armips `tools/armips/armips.exe`.
- Script: `script/bank_BB.json` (dialogue, ids BBII) + `script/misc.json` (name tables). Briefs: docs/translator-brief.md,
  docs/reviewer-brief.md, docs/style-reference.md. Glossary + rulings: glossary.md.
- RE: docs/re/text.md, ctrl_codes.md, misc_text.md, graphics.md (ECD/LZSS archive, tools/gfxcodec.py).
- Engine: asm/vwf.asm (VWF for dialogue 0x0800D210 + menu printer 0x0800BE60; [tab:NN], [mono], [narrow] modes),
  fonts tools/vwf_font.py + tools/narrow_font.py. ROM map: text 0x400000+, fonts/code 0x7E0000-0x7E2FFF, gfx 0x7E3000+.
- States: work/states/ (en_name_entry, en_map, en_status) - regenerate after any build change (cold boot routes in docs/re/text.md).

## Rulings (user, 2026-10-14) - details in glossary.md
- Drop honorifics, Western name order. Credits English. All graphics text in scope (title logo too).
- Full names/terms, engine work before abbreviation. Pre-approved: keep going, report at milestones.
- Edit source files only with the file-edit tool. ダイナ = "Dino" (game's own romanization).

## Gotchas
- Savestates from an older build show garbage (text moved): always cold boot after rebuilding.
- UI (fixed-window) strings = misc tables + bank 00 only; banks 01+ go through the dialogue box (wrap 160 px,
  152 px on each box's 3rd line, auto-page after 3 lines). Name-table budget = longest JP name in the table.
- Font strips printed once and reused as tiles (digits: 0000/0020/0069) need [mono].

## Status (2026-10-15)
- Done: all 2798 entries translated, reviewed (7 slices) and polished; VWF + condensed name font; per-window box
  widths (15/20/22 cells); graphics text (title logo/sprites/menu, intro logo, name entry, birthday, catalog tabs,
  Set Devices, shop footer, battle SFX); QA tour of map, menus, park, shop, catalog, tournaments, save/continue.
  Release gate passes; local v1.0 packages (Dragon + Phoenix) in release/ (not published). Phoenix: title/menus/dialogue
  checked from its save; subtitle logo already shows PHOENIX.
- Dragon save QA (2026-10-15): late game (Daostaville), Link menu, status/catalog/setup, ending dialogue + credits seen.
  Fixed: Link menu row 3 overflowed the 30-tile ring ("Link: Chobigurumi"), credits "Sound FX & Sound" clipped at x=240.
- Open: battle SFX sprites not watched live (2 Practice battles played 2026-10-20, no SFX word ever shown);
  cable Link screens unvisited; no static check for dialogue-window tile-ring overflow (use tilewrap.lua).
- Agent playtest 2026-10-20 (docs/playtester-brief.md, sessions work/playtest/s1-s4): new game to partner name entry,
  all field menus + My Gachasute, 2 battles, Phoenix Dino City. Fixed: save-overwrite question pushed off its page,
  text touching the page arrow (ARROW_PX 10), " Born" spacing, こしょう = "Broken", page splits. Left as original art:
  "YouLose" banner, "bolt on" boost label, status "BIT:". User rulings: ボーガ = "Voga";
  name/partner entry opens on the ABC page (asm/vwf.asm patch at 0x0801EB06, page byte 0x020046B2).
- User .srm saves have each 8-byte EEPROM word reversed: `tools/savefix.py "saves/X.srm" work/saves/X.sav` before `emu.py --sav`.
  Title menu with a save = New Game/Continue/Link, cursor starts on Continue (no `down`).
- QA helpers: tools/lua/tilewrap.lua (ring overflow), dlglog.lua (glyph calls), forcetext.lua (jump to a text id, e.g. the
  ending 0x0379 -> credits), tools/montage.py (zoomed frame sheet), tools/routes/fortress_entry.txt.
- QA states in work/states/qa_*.mss (made by a QA pass; regenerate after text-layout changes); RAM pokes in
  tools/lua/poke.lua (battle HP 0x020044D2 / opponent 0x0200454E).
- Name-table slots are fixed 8 tiles (VS screen: player tiles 0x10-0x17, opponent 0x18-0x1F): never exceed.

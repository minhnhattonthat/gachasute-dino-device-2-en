# Gachasute! Dino Device 2 - Dragon (GBA) English translation

Skill: translate-retro-game (H:/translation/gachasute-dino-device-2-dragon/.claude/skills/translate-retro-game/SKILL.md).
Read it before ROM, text or QA work. `$SKILL` below = that directory.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py english` -> build/dino2_en.gba (`identity`, `marker` also) [not written yet]
- Check:    `python -X utf8 tools/check.py` (pytest over tests/; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/dino2_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user) [not written yet]
- Font:     `python -X utf8 tools/font.py render` -> work/font.png; table: `python -X utf8 tools/mktbl.py` -> tbl/font.tbl

## Paths
- Original ROM: `rom/orig.gba` (copy of `rom/Gachasute! Dino Device 2 - Dragon (Japan).gba`, gitignored;
  SHA-1 8bb322121ca889ed8a7b22a907cd835e23fd4449, CRC32 A63DFD2C, 4 MiB, EEPROM_V124, code A4XJ).
- Emulator: `tools/mesen2/Mesen.exe` + `Firmware/gba_bios.bin` (from rom/); assembler `tools/armips/armips.exe`.
  emu.py `--emu` needs an absolute path (or omit it; tools/** is searched).
- RE notes: `docs/re/text.md` (encoding, renderer, font), `docs/re/ctrl_codes.md` (E0 subcommands).
- States: `work/states/` (name_entry.mss = INPUT A NAME screen, from cold-boot route in docs/re/text.md).

## Rulings (user, 2026-10-14) - details in glossary.md
- Drop honorifics, Western name order. Credits English. All graphics text in scope (title logo too).
- Full names/terms, engine work before abbreviation. Pre-approved: keep going, report at milestones.
- Edit source files only with the file-edit tool. Dialogue uses ダイナ = "Dino" (game's own romanization).

## Status (2026-10-14)
- Done: Step 0 setup, original boots (smoke ok). Recon: text is uncompressed 1-byte codes, font map found.
- Next: control-code table, pointer/text coverage, identity + extract, VWF spike.

# Gachasute! Dino Device 2 - Dragon / Phoenix (GBA) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py english` -> build/dino2_en.gba (8 MiB; checks the dump against `rom.sha1` first). Also `identity` (== original), `marker`, `reloc`.
- Phoenix:  `python -X utf8 tools/phoenix.py` -> build/dino2_en_phoenix.gba (Dragon build with the Phoenix header bytes swapped in; tests/test_phoenix.py guards that).
- Check:    `python -X utf8 tools/check.py` (pytest: identity, roundtrip, lint, tools; the pre-commit hook runs it)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/dino2_en.gba --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- JP scan:  `python -X utf8 tools/jpcheck.py` (every bank + name-table pointer slot; must print 0 runs)
- Text:     batches `tools/batches.py make|check|apply|status`; dry-run wrap `tools/fit.py "text"`; review pairs `tools/pairs.py`.
- Playtest: subagents with docs/playtester-brief.md (`$SKILL/scripts/play.py`); file reports into docs/status.md.
- Release:  `python -X utf8 tools/release.py --version X.Y` -> release/*.zip, one per variant (gate + BPS + verify; never publish without the user)

## Paths
- Original ROMs (gitignored): `rom/orig.gba` (Dragon, SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`; EEPROM_V124) and
  `rom/Gachasute! Dino Device 2 - Phoenix (Japan).gba` (SHA-1 checked by tools/phoenix.py). User saves in saves/ (gitignored).
- Emulator `tools/mesen2/Mesen.exe` (+Firmware/gba_bios.bin); armips v0.11.0 `tools/armips/armips.exe` (both gitignored).
- Text: `script/bank_BB.json` (dialogue, ids BBII) + `script/misc.json` (name tables). Glossary: glossary.md. Briefs:
  docs/translator-brief.md, reviewer-brief.md, style-reference.md. RE notes index: docs/re/README.md. Fonts: docs/fonts.md.
- Engine: asm/vwf.asm (VWF for dialogue 0x0800D210 + menu printer 0x0800BE60; [tab:NN], [mono], [narrow] modes; name entry
  opens on ABC at 0x0801EB06). ROM map: text 0x400000+, fonts/code 0x7E0000-0x7E2FFF, gfx 0x7E3000+ (tools/gfx_build.py, gfx/).

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/` (.srm: run
  `tools/savefix.py` first), reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Savestates from an older build show garbage (text moved): cold boot after rebuilding.
- UI (fixed-window) strings = misc tables + bank 00 only; banks 01+ go through the dialogue box (wrap 160 px, 150 px on each
  box's 3rd line for the page arrow, auto-page after 3 lines). Name-table budget = longest JP name in the table.
- Name-table slots are fixed 8 tiles (VS screen: player 0x10-0x17, opponent 0x18-0x1F): never exceed.
- Font strips printed once and reused as tiles (digits: 0000/0020/0069) need [mono].

## Status
`docs/status.md`: done, next, open bugs, QA notes. Update it at the end of every session.

# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 (release). Last build: see `git log -1` (2026-10-20).
- **Done:**
  - All 2798 entries translated, reviewed (7 slices) and polished. VWF + condensed name font; per-window box widths
    (15/20/22 cells); name entry opens on the ABC page.
  - Graphics text: title logo/sprites/menu, intro logo, name entry, birthday, catalog tabs, Set Devices, shop
    footer, battle SFX.
  - QA: tour of map, menus, park, shop, catalog, tournaments, save/continue. Dragon save QA (2026-10-15): late game
    at Daostaville, Link menu, ending dialogue + credits. Phoenix: title/menus/dialogue from its save.
  - Agent playtest 2026-10-20 (docs/playtester-brief.md, sessions work/playtest/s1-s4): new game to the partner's
    name entry, every field menu + My Gachasute, 2 Practice battles, Phoenix Dino City. Fixes committed.
  - Repo set up from fan-translation-template (README, LICENSE, issue form, rom.sha1 check, docs).
- **Next:** create the GitHub repo and publish v1.0 (Dragon + Phoenix zips from `tools/release.py`) when the user
  says so.
- **Open bugs:**
  - Battle SFX sprites never seen live (2 Practice battles, no SFX word shown); may need a specific weapon.
  - Cable Link screens unvisited (need a link partner).
  - No static check for dialogue-window tile-ring overflow (use tools/lua/tilewrap.lua).
  - Some long boxes end with one short line on a new page (game auto-pages).
  - Original English art left as is: "YouLose" result banner, "bolt on" boost label, status "BIT:".
- **Waiting on the user:** nothing.

## QA notes
- User .srm saves have each 8-byte EEPROM word reversed: `tools/savefix.py "saves/X.srm" work/saves/X.sav` before
  `emu.py --sav`. Saves: Dragon = late game at Daostaville Fortress; Phoenix = Dino City, 51000 Bits. Title menu with a
  save = New Game/Continue/Link, cursor starts on Continue.
- Helpers: tools/lua/tilewrap.lua (ring overflow), dlglog.lua (glyph calls), forcetext.lua (jump to a text id, e.g.
  the ending 0x0379 -> credits), poke.lua (battle HP 0x020044D2 / opponent 0x0200454E), tools/montage.py,
  tools/routes/fortress_entry.txt. States in work/states/qa_*.mss: regenerate after text-layout changes.

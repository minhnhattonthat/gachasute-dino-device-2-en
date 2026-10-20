# Reverse-engineering notes

One file per subsystem. Mark every finding with how far it is proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| text.md | encoding, script banks, pointer tables, dialogue windows, cold-boot routes | verified (identity + roundtrip tests) |
| ctrl_codes.md | E0 control codes and their arguments | verified for the codes the script uses |
| misc_text.md | name tables and UI string tables, name entry layout, save fields | verified (identity test) |
| graphics.md | ECD/LZSS archive, image/map/pattern formats, graphics-text survey | verified (tests/test_gfx.py) |

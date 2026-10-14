Gachasute! Dino Device 2 - Dragon - English translation patch v{VERSION}
=========================================================================

An unofficial fan translation of the Game Boy Advance game
"Gachasute! Dino Device 2 - Dragon" (Rocket Company, 2003, Japan only).

What is translated
- All story dialogue, menus, shops, battle and system messages, names of
  Dinos, Devices (parts), people and places, and the staff credits.
- A variable-width font was added so English fits the original windows;
  long Device names use a condensed font.
- Text drawn as graphics (title logo, title menu, name-entry buttons):
  see "Known issues" for anything still in Japanese.

How to apply
1. You need your own dump of the Japanese cartridge. Expected file:
   Gachasute! Dino Device 2 - Dragon (Japan).gba
   {ORIG}
2. Apply the .bps patch with Flips, beat or RomPatcher.js
   (https://www.marcrobledo.com/RomPatcher.js/).
3. Patched result: {PATCHED}
The patched ROM is 8 MiB (the original is 4 MiB); the extra space holds
the English text and font. Saving (EEPROM) works as in the original.

Play notes
- Tested in Mesen 2 (headless runs) with a real GBA BIOS. Other accurate
  emulators (mGBA, NanoBoyAdvance) and flash carts should work.
- Start a new game, or start the patched ROM from a cold boot: savestates
  made with the Japanese ROM or an older patch version will show garbage.
- Name entry has an ABC mode (L button) for English names.

Known issues
- Not yet seen in testing: My Gachasute, Link (cable) screens, the late
  game and the ending/credits; battle sound-effect words were redrawn in
  English but not yet watched in a live battle. Reports welcome.
- Some long boxes end with one short line on a new page; the game pages
  automatically when a box is full.
- One Device name is squeezed to fit its slot: "NapalmMachineGun".
- Staff names in the credits are written in hiragana in the original;
  the romanizations are best guesses.
- The element chart in the tutorial (Fire beats Water...) is as written
  in the original game.

Credits
- Translation, engine work and tools: fan translation project, made with
  AI assistance (Claude by Anthropic) under human direction.
- Original game: Rocket Company. This patch is not affiliated with or
  endorsed by the rights holders. Do not distribute pre-patched ROMs.

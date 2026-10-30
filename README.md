# Gachasute! Dino Device 2 English translation

Unofficial English fan translation of **Gachasute! Dino Device 2 - Dragon** and **- Phoenix** (Game Boy Advance,
Rocket Company, 2003, Japan only): the source text and tools that build the patches. One translation covers both
versions.

**Just want to play?** Download the patch for your version from [Releases](../../releases) and follow its README. This
repository holds no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Dialogue / story | Translated (ending checked in Dragon) |
| Menus, shops, battle and system messages, Dino/Device/people/place names | Translated |
| Title logo and graphics with text (title menu, intro logo, catalog tabs, Set Devices, shop footer) | Translated (the original's own English art, e.g. "YouLose", kept) |
| Battle sound effects | Translated, not checked in play |
| Name entry | Translated (opens on an ABC page; kana pages one L/R press away) |
| Cable Link screens | Not checked in play |
| Staff credits | Translated (hiragana staff names romanised as best guesses) |

Known issues: some long boxes end with one short line on a new page; one Device name is squeezed
("NapalmMachineGun").

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `build.py`, `tools/` | Python build chain: extract, insert, lint, graphics, release. |
| `asm/` | Engine changes (armips): variable-width font for dialogue and menus, condensed name font, name entry on ABC. |
| `gfx/`, `tbl/` | Graphics with English lettering, and the game's character table. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |

## Build your own patched ROM

Needs Python 3.12+ with Pillow and pytest (`pip install pillow pytest`), [armips](https://github.com/Kingcom/armips)
v0.11.0 at `tools/armips/armips.exe` (Windows build), and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/gachasute-dino-device-2-en
cd gachasute-dino-device-2-en
# copy your Dragon dump to: rom/orig.gba
#   (4,194,304 bytes, SHA-1 8bb322121ca889ed8a7b22a907cd835e23fd4449; the build refuses any other dump, see rom.sha1)
python -X utf8 build.py english                        # -> build/dino2_en.gba
python -X utf8 tools/check.py                          # tests + text lint
# Phoenix: also copy your Phoenix dump to "rom/Gachasute! Dino Device 2 - Phoenix (Japan).gba"
#   (4,194,304 bytes, SHA-1 a209ab6e216a1054961bb25c26aef79c749e2d67), then:
python -X utf8 tools/phoenix.py                        # -> build/dino2_en_phoenix.gba
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. The original Japanese text in `script/` and the game art in `gfx/` are Rocket
Company's and are included only so the translation can be checked and built against them. Gachasute! Dino Device 2
is (c) 2003 Rocket Company; this project is not affiliated with them. Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.

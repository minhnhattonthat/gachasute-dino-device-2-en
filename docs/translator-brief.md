# Translator brief - Gachasute! Dino Device 2 - Dragon (GBA, 2003)

You translate part of the Japanese script of Gachasute! Dino Device 2 - Dragon into English for a fan patch. It is
a kids' RPG: a boy arrives in Dino City to become a Dino Battler, builds "Dino" robot toys from parts, pulls capsule
toys at "Gachasute" machines and battles other kids. Tone: bright, energetic, simple sentences for young players.
Work only on the batch named in your dispatch. Do all translation yourself; do not dispatch subagents.
Repo root: H:/translation/gachasute-dino-device-2-dragon (run commands from there).

## Read first
1. `docs/style-reference.md` - who each portrait is, character voices, approved example pairs. Match this voice.
2. `glossary.md` - binding names and terms (use them exactly, including capitalisation).

## Input: `work/batches/<batch>.json`
A list of `{"id": "0103", "jp": "..."}` in story order (neighbouring entries are often the same scene).
Japanese uses control tags; what they mean:
- `[face:NN]` / `[face2:NN]` portrait on screen = who speaks next (see the portrait table); `[noface]` = narration.
- `\n` line break, `[p]` wait for a key and start a new box, `[half]` half-height line break, `[close]` / `[end]` end.
- `[player]` the player's name, `[partner]` the partner's name. `[c:08]Place[/c]`, `[c:0A]Item[/c]` = coloured
  text: put the colour tags around the English for the same term.
- Anything else in brackets, e.g. `[E0 31 00 59 01 07]`, `[E0 8B 00]`, `[E0 11 00]` (a number), `[E0 12]`/`[E0 13]`/
  `[E0 18]` (an inserted name), is game logic: copy it exactly, in the same order relative to the text it sits in.

## Output: `work/batches/<batch>.out.json`, written with your file-write tool (never a shell heredoc)
A JSON object `{"id": "English", ...}` with every input id exactly once. Each value is the full English for that
entry, **including every non-layout tag from the Japanese** (all `[E0 ..]`, `[face..]`, `[noface]`, `[c:..]`, `[/c]`,
`[player]`, `[close]`, `[end]`...). Plain ASCII plus `…` if you like: straight quotes, no Japanese or fullwidth
characters, no `\uXXXX` escapes for normal letters (JSON `\n` for line breaks is fine).

### Layout rules (the build wraps text for you)
- Do NOT hand-wrap. Write each box as running text; the build word-wraps to the box (160 px per line, about
  28-32 characters) and the game opens a new box by itself when 3 lines are full.
- Keep the `[p]` box breaks where the Japanese has them (you may add a `[p]` to split a very long box at a sentence
  end). Keep a `\n` only where the Japanese breaks a line on purpose: a heading, a name on its own line
  (`[c:0A]Misari Hiiragi[/c]`), a question followed by its choice line.
- **Choices**: the line before `[E0 00 ..]`, `[E0 01 ..]`, `[E0 02 ..]`, `[E0 03 ..]` lists the options with
  spaces (`　　はい　　いいえ[E0 00 01 05 ...]`). Write it as `[opt]Yes[opt]No[E0 00 01 05 ...]` - one `[opt]` before
  each option, nothing else on that line, and copy the `[E0 0x ..]` tag unchanged (the build moves the cursor).
  E0 00/01/03 have 2 options, E0 02 has 3. Keep options short (all on one 20-cell line).
- `[half]` lines (system messages) count as lines too; keep them where they are.

## Validate
`python -X utf8 tools/batches.py check <batch>` - fix every reported id until it prints OK. The only problems you
may leave are `UI ...px > N` lines where no natural full wording fits; list each as `LONG: id` in your report.
`python -X utf8 tools/fit.py "<english>"` shows how one entry wraps (width/budget per line) if you want to look.

## Style
- Faithful: keep the information and order of ideas; adapt idiom, not meaning. Don't add details the Japanese
  doesn't state; don't summarise or skip. Adapt wordplay so the joke still lands (no translator notes).
- Names and terms exactly as in the glossary; never abbreviate. Honorifics dropped (`[player]くん` -> `[player]`),
  Western name order (Misari Hiiragi). ダイナ is "Dino" (Dino Battle, Dino Battler, Dino City...).
- Punctuation: 「」 -> "...", 『』 -> '...', ・・・ -> `...`, ！？ -> `?!`, 〜 (drawl) -> drop or `~` sparingly.
- Kids' game: natural, lively English; contractions; no slang that will date badly; no swearing.
- Placeholders: no suffixes glued to a variable (`[E0 11 00] bits`, never `[E0 11 00]th`); no a/an right before a
  name variable; `[player]`/`[partner]` may be any name, so avoid gendered pronouns for `[partner]` unless the
  Japanese makes it clear.
- Currency ビット = "Bits" after the number: `500 Bits`, `[E0 11 00] Bits`.
- Single-line entries that end in `[close]` with no portrait (menu labels, names, short system words) are drawn in
  fixed menu windows: they must fit the JP width (the check reports `UI ...px > N`). Keep them short and natural
  ("Back", "OK", "Save"), never abbreviated words; if a full term can't fit, keep it and report `LONG: id`.
- Debug/test strings (entries 0000-0009, 0069) are never shown to players: translate them plainly and briefly.
- System lines: てにいれた -> "Got X!" / "[player] got X!"; keep them short.

## Notes from earlier batches
- Item-get lines: `[player] got [E0 43 xx][c:0A]200 Bits[/c]![E0 44 14]` - sound/wait tags stay right before/after the
  item as in the JP, the colour tags hug the item name.
- `[E0 17 nn]０ビット`: the number variable is followed by a literal 0 in the JP; keep it: `[E0 17 nn]0 Bits`.
- Kabira speaks mock-archaic ("thou", "I shall"); Master (Bay Cafe) is used like a name: "Thank you, Master!".
- A `\n` followed by a new `[face..]` changes speaker mid-box in the JP; you may put `[p]` there instead.
- Sound effects: short and punchy (`Vrrrrr...`, `Snip!`).

## Name tables (ids like `part_head.03`, `town.00`, `word_shop.44`)
These are names and menu words shown in fixed menu windows. Each must fit its JP width (the check prints the
budget); trailing full-width spaces in the JP are padding the build re-adds, don't copy them.
- Towns/places/people: glossary forms (Dino City, Misari's House, Post Office...). Opponent names: keep puns
  (ウニボンバー -> Urchin Bomber), Hepburn for Japanese names, Western order (よざくら かずき -> Kazuki Yozakura).
- Dinos (`dino.*`): romanize to a pronounceable fantasy name (エルフェーン Elfeen, チラザフェルト Chirazafelt...).
- Parts (`part_*`): one consistent scheme. Series prefixes: エルブ Elb, ガルサ Galsa, フォラ Fora, サーク Sark,
  カイト Kite, ゴルガ Golga, チラサ Chirasa, ボーガ Boga, ジール Zeal, ヴァス Vas, メイカ Meika, シータ Theta,
  トラー Tra, ダンサ Dansa, ネイガ Neiga; grades コア Core, パウ Pow, メタ Meta; slots ヘッド Head, ボディ Body,
  ライド Ride, コルポ Corpo, グロソ/グロッソ Grosso. Element prefixes: ヒート Heat, フレム Flame, ナパム Napalm,
  ファイ Fire, ミスト Mist, アクア Aqua, マリン Marine, ウワラ Uwara, エレク Elec, スパク Spark, ブリツ Blitz,
  サンダ Thunder, ペブル Pebble, テッラ Terra, ランド Land, アース Earth, スペル Spell, レバリ Revali. Weapon words
  in full English (チェンガン Chain Gun, レイシルド Ray Shield, バスター Buster, ピストル Pistol, ライフル Rifle).
  Body suffix letters Ｆ/Ｗ/Ｔ/Ｅ/Ｓ stay as F/W/T/E/S. Use the full words even when over budget: write the full name
  and report it as `LONG: id` - the controller will fix those windows in the engine. Do not abbreviate.
- `−−−−−−−−` placeholders and Latin codes are already done (autofilled).

## Consistency
Never edit `glossary.md` or any file other than your output. For a recurring name or term not in the glossary,
pick a form, use it consistently, and report it.

## Report (reply with only this)
Files written and entry count; then any lines: `NEW TERM: jp -> en`, `UNSURE: id - note`.

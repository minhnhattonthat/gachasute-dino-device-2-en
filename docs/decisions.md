# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-14 | Honorifics and name order | keep (-kun, -chan), drop; JP or Western order | Drop honorifics, Western order: natural English for a kids' game. |
| D2 | 2026-10-14 | Romanization source for names | official art, earlier patch, Hepburn | The game's own English first (title logo "Dino Device", boot screen "DINO CHARGE", "Dinomo"), else Hepburn; ダイナ = "Dino"; pun names localized. |
| D3 | 2026-10-14 | Credits | stay Japanese, translate | English. Staff names written in hiragana are best-guess romanizations. |
| D4 | 2026-10-14 | Abbreviations | engine work first (default), abbreviate | Full names and terms; VWF, wider boxes, condensed name font before shortening. One squeezed Device name remains ("NapalmMachineGun"). |
| D5 | 2026-10-14 | Graphics text left in Japanese | none (default), list | None: all graphics text in scope, title logo included. |
| D6 | 2026-10-14 | Specs and plans | need approval, pre-approved | Pre-approved: keep going, report at milestones. |
| D7 | 2026-10-15 | Phoenix version | Dragon only, both | Both: Phoenix differs only in header bytes, so one translation serves both (tools/phoenix.py). |
| D8 | 2026-10-20 | ボーガ Device series spelling | Boga (Hepburn), Voga | Voga: matches the game's own style code FVOG. |
| D9 | 2026-10-20 | Name entry for English players | keep hiragana first, open on ABC | Open on the ABC page (asm/vwf.asm patch at 0x0801EB06); kana pages stay one L/R press away. |
| D10 | 2026-10-20 | Player bug reports | email, GitHub issues | GitHub issues with the bug form (savestate attached); fix commits say `Fixes #N`. |

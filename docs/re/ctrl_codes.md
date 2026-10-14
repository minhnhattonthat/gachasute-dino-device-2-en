# Text-script control codes

Static RE of the text interpreter (Thumb). The state struct `T` is at `0x0200471C`. `T+0x14` is the text pointer, which is the same word as `[0x02004700+0x30]`. The main loop is at `0x0800D274`, the byte-dispatch table at `0x0800D2A8`, and the E0 sub-table rows at `0x0804AA34`. Interpreter modes `T+0x24` dispatch through the `{mode, fn}` table at `0x0804AA98`.

**Text ID** = 16-bit **big-endian** `BBII`, resolved by `0x0800D468`: `ptr = [[0x08061300 + BB*4] + II*4]`. There are 9 banks and 1263 strings, at file 0x4AB10-0x5E534. Every "jump" argument below is a text ID. ID `0000` means "none": the choice code closes the window, and the E0 8x codes continue.

"args" = bytes consumed after the subcommand byte (after the code byte for the F8-FF codes).

## Single-byte codes

| code | args | variable? | effect | handler addr |
|---|---|---|---|---|
| 00-DF, E1-EF | 0 | no | 1-byte glyph | 0800D210 |
| F0-F7, FA, FB | 1 | no | 2-byte glyph `((c&0xF)<<8)\|next` | 0800D356 -> 0800D210 |
| F8 | 0 | no | newline, +2 tile rows (16 px). Automatic page-wait (as FC) if the window is full or the next bytes are `E0 60`/`E0 62` | 0800BFC4 |
| F9 | 0 | no | half newline, +1 tile row (8 px). Same auto page-wait | 0800BF80 |
| FC | 0 | no | page break: wait for A/B (mode 1), clear the window, continue | 0800BF34 |
| FD | 0 | no | **return**: if a saved pointer `T+0x9C` exists (set by E0 80/82/83/85-8E), restore pointer and line and page-wait; otherwise acts as FF | 0800BF04 |
| FE | 0 | no | **end now**: no key wait. Stops the interpreter and launches the pending subsystem `T+0x98` (if any) via `0x08003578` | 0800BEAC |
| FF | 0 | no | **end**: wait for key (mode 2), then close the window. If `T+0xA2`≠0, resume at the saved `T+0x9C` | 0800BE9C |

## E0 subcommands (`E0 ss args…`)

| code | args | variable? | effect | handler addr |
|---|---|---|---|---|
| E0 00 | 6 | no | 2-way choice: `r1 r2` cursor rows (+ current row), then `id0 id1` (BE). Default cursor 0; B picks 1. Jumps to the chosen id (0000 = close). **Never falls through** | 0800C008 |
| E0 01 | 6 | no | same as E0 00, default cursor 1 | 0800C08C |
| E0 02 | 9 | no | 3-way choice: `r1 r2 r3 id0 id1 id2`. B picks 2. Never falls through | 0800C110 |
| E0 03 | 8 | no | 2 rows shown, 3 targets: `r1 r2 id0 id1 idB` (B = cancel → idB). Never falls through | 0800C1A4 |
| E0 04 | 0 | no | set flag 0xA3, which makes the next choice ignore B | 0800C228 |
| E0 0F | 0 | no | alias of E0 04 (remapped in 0800D1D8) | 0800C228 |
| E0 10 | 1 | no | insert string from pointer slot `[0x0200470C + n*4]` | 0800C234 |
| E0 11 | 1 | no | insert decimal number `[0x02004700 + n*4]`, up to 7 digits, no leading zeros | 0800C2E8 |
| E0 12 | 0 | no | insert name from table 080739B4 [cat][idx]; cat/idx set by E0 23 (cat 5 → 080753B4) | 0800C300 |
| E0 13 | 0 | no | same, other table 080739C8 (cat 5 → 080752E4) | 0800C344 |
| E0 14 | 0 | no | insert name string from save 0x0200495E (likely the player name) | 0800C388 |
| E0 15 | 0 | no | insert name string from save 0x02004966 (second name: partner or rival) | 0800C3AC |
| E0 16 | 1 | no | insert number = f_801D6E4(n) (byte) | 0800C3D0 |
| E0 17 | 1 | no | insert number = f_801D6FC(n) (halfword) | 0800C3FC |
| E0 18 | 0 | no | insert name 0806143C[[0x0200471B]]; falls back to E0 14 if 0 | 0800C428 |
| E0 19 | 0 | no | insert string f_800D48C(byte 0x02004977) | 0800C45C |
| E0 1A | 0 | no | insert string f_800D49C(…) | 0800C488 |
| E0 20 | 2 | no | set flag (BE16) | 0800C4BC |
| E0 21 | 2 | no | clear flag (BE16) | 0800C4E0 |
| E0 22 | 2 | no | toggle flag (BE16) | 0800C504 |
| E0 23 | 2 | no | set name category/index `[0x02004718]=a, [0x02004719]=b` (for E0 12/13/51/70) | 0800C538 |
| E0 30 | 2 | no | **jump** to text id (unconditional) | 0800C55C |
| E0 31 | 4 | no | `flag16 id`: jump if flag set, else continue | 0800C57C |
| E0 32 | 4 | no | `flag16 id`: jump if flag clear | 0800C5B0 |
| E0 33 | 4 | no | `a b id`: jump if f_801D4B4(a,b)≠0 (item/inventory check?) | 0800C5E4 |
| E0 34 | 1+3n | **yes** | random branch: `n {pct id}×n`. r=rand%100; for each entry r-=pct; the first entry where r<0 jumps. If none, continue after the list | 0800C614 |
| E0 35 | 3 | no | `a id`: jump if a > f_801D510() | 0800C668 |
| E0 36 | 3 | no | `a id`: jump if a > [0x02004974]+1 | 0800C694 |
| E0 37 | 4 | no | `a b id`: jump if f_801D8F8(a) < b | 0800C6CC |
| E0 38 | 2 | no | `id`: jump if f_801DC60()≠0 | 0800C700 |
| E0 40 | 1 | no | text colour on (T+0x7E = colour) | 0800C728 |
| E0 41 | 0 | no | text colour off/reset | 0800C740 |
| E0 42 | 1 | no | play sound n (0x08046360) | 0800C750 |
| E0 43 | 1 | no | play sound n+0x1E; clears flag 0x10000 | 0800C768 |
| E0 44 | 1 | no | wait n frames | 0800C790 |
| E0 45 | 0 | no | clear the window and home the cursor (no key wait) | 0800C7B4 |
| E0 46 | 0 | no | f_8046494 (sound or BGM control?) | 0800C7D0 |
| E0 47 | 0 | no | f_80464CC (pair of E0 46) | 0800C7DC |
| E0 50 | 1 | no | open UI box / picture n (T+0x80=n, 0800DCC4) | 0800C7E8 |
| E0 51 | 0 | no | same, n taken from [0x02004718] (E0 23) | 0800C818 |
| E0 60 | 1 | no | show portrait n, side A (re-executes itself while the old portrait slides out) | 0800C95C |
| E0 61 | 0 | no | hide portrait | 0800CA10 |
| E0 62 | 1 | no | show portrait n, side B | 0800CA54 |
| E0 63 | 0 | no | no-op | 0800CB08 |
| E0 70 | 4, or 3 if 1st byte = 06 | **yes** | `a b id`: jump if f_801D3C0(a,b)≠0. If a==06 the form is `06 id` and (a,b) come from [0x02004718/9] | 0800CB0C |
| E0 71 | 2 | no | f_801D5C8(BE16) and set a flag in 0x020046F0 | 0800CB54 |
| E0 72 | 2 | no | f_801D930(BE16) | 0800CB88 |
| E0 73 | 2 | no | f_801D608(a,b) (give/set item?) | 0800CBAC |
| E0 74 | 4 | no | `a b id`: jump if f_801D680(a,b)≠0 | 0800CBCC |
| E0 75 | 1 | no | f_801D7D4(n) | 0800CBFC |
| E0 76 | 1 | no | f_801D788(n) | 0800CC18 |
| E0 77 | 1 | no | f_801DA68(n) | 0800CC34 |
| E0 78 | 0 | no | f_801D444() | 0800CC4C |
| E0 79 | 4 | no | `v16 id`: jump if f_801D5E8(v)≠0 (v≤2 → value from slot [0x02004700+v*4]) | 0800CC58 |
| E0 7A | 4 | no | `a b id`: jump if f_801D638(a,b)≠0 | 0800CC9C |
| E0 7B | 2 | no | f_801D6B8(a,b) | 0800CCCC |
| E0 7C | 1 | no | f_801D800(n) | 0800CCEC |
| E0 7D | 3 | no | `a id`: jump if f_801D83C(a)≠0 | 0800CD04 |
| E0 7E | 3 | no | `a id`: jump if f_801D88C(a)≠0 | 0800CD34 |
| E0 80 | 2 | no | **call subsystem** 0x28 (pointer saved in T+0x9C). On return, `id`: jump if result==0, continue if result==1, otherwise close. 0000 = no jump | 0800CD64 |
| E0 81 | 1 | no | set [0x02004977]=n, queue subsystem 7, **end script** (FF-style). The arg is not consumed (the script ends) | 0800CDF0 |
| E0 82 | 0 | no | call subsystem 0x0A, then continue | 0800CE34 |
| E0 83 | 0 | no | call subsystem 0x0F, then continue | 0800CE88 |
| E0 84 | 2 | no | `id`: jump if f_800B630()≠0 | 0800CED0 |
| E0 85 | 0 | no | call subsystem 0x15, then continue | 0800CEF4 |
| E0 86 | 2 | no | call subsystem 0x1B; on return `id` jump if id≠0 and [0x0200471B]==0, else continue | 0800CF48 |
| E0 87 | 2 | no | call subsystem 0x28 (after f_8016B3C); return `id` as E0 80 (no "close" case) | 0800CF90 |
| E0 88 | 0 | no | call subsystem 0x0A (other variant), then continue | 0800CFE8 |
| E0 89 | 2 | no | call subsystem 0x28 (after f_8016B98); return `id` as E0 87 | 0800D038 |
| E0 8A | 0 | no | f_801CD98() (no call) | 0800D090 |
| E0 8B | 1 | no | call subsystem 0x21 with [0x0200444C]=n; resumes after the arg | 0800D09C |
| E0 8C | 0 | no | queue subsystem 0x25, **end script** | 0800D0F8 |
| E0 8D | 2 | no | call subsystem 0x28 (after f_8016BF8); return `id` as E0 87 | 0800D118 |
| E0 8E | 0 | no | call subsystem 0x17, then continue | 0800D170 |

## Notes

- **E0 0F** is remapped to 4 before the lookup, so it is the same as E0 04. The raw byte is kept in `[0x02004738]`. Rows 9-F of `0x0804AA34` are not E0 rows: the `0x0804AA5C` table is the per-code "return from subsystem" handler table, indexed by the low nibble of the E0 8x byte. Subcommands outside the listed rows would crash.
- **The E0 8x "call" codes** save the pointer, which points just past the subcommand, before reading any args. They close the window (mode 9). When the subsystem finishes, mode 0xA runs the return handler from `0x0804AA5C[ss&0xF]`. That handler is the one that consumes the trailing `id` (E0 80/86/87/89/8D) or skips the arg (E0 81/8B). If the next byte is FF, the window stays closed. In the data, E0 83/85/8E are almost always followed by FF.
- **Choice codes E0 00-03** consume their cursor-row bytes in the handler. Mode 3/4/5 then advances the pointer by `2*cursor` and mode 6 reads the BE id there. Execution never continues past the id list.
- **Text-variable inserts:** E0 10 (string slot), E0 11/16/17 (numbers), E0 12/13 (name tables, needing E0 23 first), E0 14/15 (save-RAM names, likely player and partner), E0 18/19/1A. Inserted text uses mode 7 (string up to FF, 2-byte F0-FB glyphs allowed) or mode 8 (digit buffer at T+0x44).
- **String ends:** FF (key wait + close), FE (no wait), FD (return or end), E0 30 (unconditional jump), E0 00-03 (choice, always branches away), E0 81 and E0 8C (end + launch subsystem). Strings may also fall through into the next table entry: 33 do so, and the walk stays aligned.
- **Flags:** f_800BBA8/BBCC/BBF0/BC14 are set/clear/toggle/test on a bit array (flag id BE16). Flag 0xA3 is the "no B-cancel" flag, cleared automatically after a choice.

## Validation

`walk` over all 1263 table strings (`0x0804AB10..0x0805E534`) with the counts above (scratch script, not committed):
- 0 invalid E0 subcommands and 0 desyncs. Every fall-through lands exactly on the next string start.
- Every jump, choice and return id resolves to a ROM string, except the intended 0000 ids.
- Endings: FF 975, FE 86, E0 30 94, choices 98, E0 81 9, E0 8C 1. Leftover gaps are FF/00 padding.
- The sample at 0x4BEE0-0x4C140 (`E0 40 08 … E0 41`, `E0 60 01`, `E0 62 00`, F0 xx glyphs, F8/FC) walks cleanly.
- The first pass had E0 00-03 and E0 80/86/87/89/8D wrong (choice ids and return ids not counted). It desynced at id 0x1FC (`E0 80 01 FB`), which is how those were caught.

Not seen in the data (counts from code only): E0 02, 04, 0F, 16, 1A, 22, 35, 37, 50, 63, 72, 75, 79, 7B, 7C, 7E.

Unresolved or guessed: what each subsystem is (0x0A/0x0F/0x15/0x17/0x1B/0x21/0x25/0x28/7, probably battle, shop, naming and so on), which side E0 60 and E0 62 put the portrait on, the exact meaning of E0 46/47/50/71-7E (game-state helpers in 0x0801Dxxx), and when `T+0xA2` is set for FF-return. None of these affect the arg counts.

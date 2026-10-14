# Translation reviewer brief - Gachasute! Dino Device 2 - Dragon

You review one slice of a JP->EN fan translation of a kids' GBA RPG. Read-only: no edits to repo files, no git, no
subagents. Mechanical validity (control codes, ASCII, width, wrapping) is enforced by tools - judge translation quality.

## Inputs (paths in your dispatch)
- Pairs file: `>> id` / `JP:` / `EN:` blocks in story order. Read ALL of it, in passes if large.
- `glossary.md` (rulings at the top), `docs/style-reference.md` (portrait -> speaker table, voices).
- Tags: `[face:NN]`/`[face2:NN]` = who speaks next (see the portrait table), `[noface]` narration, `[p]` new box,
  `[player]`/`[partner]` names, `[c:..]..[/c]` coloured terms, `[opt]` choice options, `[E0 ..]` game logic.

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; voices match the style reference (Misari cheerful, partner cocky,
  Kabira mock-archaic...).
- Things players catch: jokes/wordplay losing their punch; "1th"-style suffixes after variables; abbreviated terms;
  awkward stock phrases ("... GET!"); gendered pronouns for [partner]/[player] where English would read wrong.
- Naturalness for a young English-speaking player.

## Report (your final message; write nothing else)
### Critical (meaning reversed, broken grammar around a variable, wrong speaker)
### Important (clear mistranslation, glossary inconsistency, abbreviation)
### Minor (style; deferred to a polish pass)
Each finding: `id - JP gist - problem - suggested full EN for the entry` (for Critical/Important give the complete
replacement English of the entry, all tags included, so it can be applied directly).
### Assessment
Approved | Needs fixes - one sentence.

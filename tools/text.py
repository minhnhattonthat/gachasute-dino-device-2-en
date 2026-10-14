"""Script codec: bytes <-> editable text. Control codes per docs/re/ctrl_codes.md.

Text form:
  newline F8 -> real '\n'.  Tags: [half] F9, [p] FC, [ret] FD, [end] FE, [close] FF,
  [c:NN] E0 40 NN (colour on), [/c] E0 41, [player] E0 14, [partner] E0 15,
  [face:NN] E0 60 NN, [face2:NN] E0 62 NN, [noface] E0 61, [tab:NN] F1 NN (English only, VWF tab to cell NN),
  any other control: [E0 xx aa bb ..] / 2-byte glyph [F1 xx]; unknown-duplicate glyphs as [Gxx] / [F0 xx].
Glyph bytes 00-DF (+ E1-EF single byte) decode through tbl/font.tbl; F0 xx through the same table (row E0-FF).
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from jpenc import FONT  # noqa: E402

# E0 subcommand -> argument byte count (None = variable, handled in e0_len)
E0_ARGS = {
    0x00: 6, 0x01: 6, 0x02: 9, 0x03: 8, 0x04: 0, 0x0F: 0,
    0x10: 1, 0x11: 1, 0x12: 0, 0x13: 0, 0x14: 0, 0x15: 0, 0x16: 1, 0x17: 1, 0x18: 0, 0x19: 0, 0x1A: 0,
    0x20: 2, 0x21: 2, 0x22: 2, 0x23: 2,
    0x30: 2, 0x31: 4, 0x32: 4, 0x33: 4, 0x34: None, 0x35: 3, 0x36: 3, 0x37: 4, 0x38: 2,
    0x40: 1, 0x41: 0, 0x42: 1, 0x43: 1, 0x44: 1, 0x45: 0, 0x46: 0, 0x47: 0,
    0x50: 1, 0x51: 0, 0x60: 1, 0x61: 0, 0x62: 1, 0x63: 0,
    0x70: None, 0x71: 2, 0x72: 2, 0x73: 2, 0x74: 4, 0x75: 1, 0x76: 1, 0x77: 1, 0x78: 0, 0x79: 4,
    0x7A: 4, 0x7B: 2, 0x7C: 1, 0x7D: 3, 0x7E: 3,
    0x80: 2, 0x81: 1, 0x82: 0, 0x83: 0, 0x84: 2, 0x85: 0, 0x86: 2, 0x87: 2, 0x88: 0, 0x89: 2, 0x8A: 0,
    0x8B: 1, 0x8C: 0, 0x8D: 2, 0x8E: 0,
}
# codes after which the interpreter never continues in this string
E0_ENDS = {0x00, 0x01, 0x02, 0x03, 0x30, 0x81, 0x8C}
ENDS = {0xFE, 0xFF}  # FD also ends when no return pointer is saved; treated as continuing

SINGLE = {0xF8: '\n', 0xF9: '[half]', 0xFC: '[p]', 0xFD: '[ret]', 0xFE: '[end]', 0xFF: '[close]'}
NAMED = {(0x41,): '[/c]', (0x14,): '[player]', (0x15,): '[partner]', (0x61,): '[noface]'}
NAMED1 = {0x40: 'c', 0x60: 'face', 0x62: 'face2'}

REV = {}
for _k, _v in sorted(FONT.items()):
    REV.setdefault(_v, _k)


def e0_len(b: bytes, i: int) -> int:
    """Total length of the E0 command starting at b[i] (== 0xE0)."""
    sub = b[i + 1]
    if sub not in E0_ARGS:
        raise ValueError(f'unknown E0 {sub:02X} at {i:#x}')
    n = E0_ARGS[sub]
    if sub == 0x34:
        n = 1 + 3 * b[i + 2]
    elif sub == 0x70:
        n = 3 if b[i + 2] == 0x06 else 4
    return 2 + n


def walk(b: bytes, i: int, stop: int | None = None):
    """Yield (pos, length) tokens from i until an end code (inclusive) or stop."""
    while stop is None or i < stop:
        c = b[i]
        if c == 0xE0:
            n = e0_len(b, i)
            yield i, n
            i += n
            if b[i - n + 1] in E0_ENDS and stop is None:
                return
        elif (c & 0xF0) == 0xF0 and c not in SINGLE:
            yield i, 2
            i += 2
        else:
            yield i, 1
            i += 1
            if c in ENDS and stop is None:
                return


def decode(b: bytes, start: int, stop: int) -> str:
    out = []
    for i, n in walk(b, start, stop):
        c = b[i]
        if c == 0xE0:
            sub, args = b[i + 1], b[i + 2:i + n]
            if (sub,) in NAMED and not args:
                out.append(NAMED[(sub,)])
            elif sub in NAMED1:
                out.append(f'[{NAMED1[sub]}:{args[0]:02X}]')
            else:
                out.append('[' + ' '.join(f'{x:02X}' for x in b[i:i + n]) + ']')
        elif c in SINGLE:
            out.append(SINGLE[c])
        elif n == 2:
            g = b[i + 1]
            ch = FONT[g] if c == 0xF0 else None
            out.append(ch if ch is not None and REV[ch] == g and g >= 0xE0 and ch not in '[]' else f'[{c:02X} {g:02X}]')
        else:
            ch = FONT[c]
            out.append(ch if REV[ch] == c and c < 0xE0 and ch not in '[]\n' else f'[G{c:02X}]')
    return ''.join(out)


TAG = re.compile(r'\[([^\]]*)\]|\n|.', re.S)
SINGLE_REV = {v: k for k, v in SINGLE.items()}


def encode(s: str, charmap: dict[str, bytes] | None = None) -> bytes:
    """Text form -> bytes. charmap overrides glyph encoding (English font); default = Japanese font table."""
    out = bytearray()
    for m in TAG.finditer(s):
        t = m.group(0)
        if t in SINGLE_REV:
            out.append(SINGLE_REV[t])
        elif m.group(1) is not None:
            body = m.group(1)
            named = {v: k for k, v in NAMED.items()}
            if t in named:
                out += bytes([0xE0, *named[t]])
            elif body.startswith('tab:'):  # VWF: continue at cell NN of the line (asm/vwf.asm glyph 0x1NN)
                out += bytes([0xF1, int(body[4:], 16)])
            elif ':' in body:
                name, val = body.split(':', 1)
                sub = {v: k for k, v in NAMED1.items()}[name]
                out += bytes([0xE0, sub, int(val, 16)])
            elif body.startswith('G'):
                out.append(int(body[1:], 16))
            else:
                out += bytes(int(x, 16) for x in body.split())
        elif charmap is not None and t in charmap:
            out += charmap[t]
        else:
            g = REV[t]
            out += bytes([0xF0, g]) if g >= 0xE0 else bytes([g])
    return bytes(out)

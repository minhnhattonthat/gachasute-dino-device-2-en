-- Log every dialogue-printer glyph call (VwfDialog at HOOK_PC, default 0x087E1000): glyph, map index, tile, line start,
-- and the VWF state (after, afterT, shift) from frame FROM on.
--   emu.py ... --script tools/lua/dlglog.lua [--var FROM=2300] [--var MAX=300]
local pc, from, max, n = HOOK_PC or 0x087E1000, FROM or 0, MAX or 300, 0
local T, DLG = 0x0200471C, 0x0203FF00
local mem = emu.memType.gbaMemory or emu.memType.cpuMemory
local function u32(a) return emu.read32(a, mem) end
L.on_exec(pc, pc + 1, function()
  if L.frame < from or n >= max then return end
  n = n + 1
  L.log(string.format("f%d glyph=%04X map=%d tile=%d line=%d | after=%d afterT=%d shift=%d", L.frame,
    emu.read16(T + 0x1C, mem), u32(T + 0x30), u32(T + 0x34), u32(T + 0x20), u32(DLG), u32(DLG + 4), u32(DLG + 8)))
end)

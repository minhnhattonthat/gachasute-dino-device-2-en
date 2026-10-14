-- Log each distinct dialogue window config W = [0x0200471C + 0x8C] (32 bytes) the first time a glyph is drawn
-- with it, plus the text pointer [T+0x14] at that moment.
--   emu.py ... --script tools/lua/winlog.lua
local mem = emu.memType.gbaMemory or emu.memType.cpuMemory
local function r32(a) return emu.read(a, mem) | (emu.read(a + 1, mem) << 8) | (emu.read(a + 2, mem) << 16) | (emu.read(a + 3, mem) << 24) end
local seen = {}
L.on_exec(0x0800D210, 0x0800D211, function()
  local w = r32(0x0200471C + 0x8C)
  if seen[w] then return end
  seen[w] = true
  local b = {}
  for i = 0, 31 do b[#b + 1] = string.format("%02X", emu.read(w + i, mem)) end
  L.log(string.format("f%d W=%08X text=%08X line=%04X [W]=%s", L.frame, w, r32(0x0200471C + 0x14),
    r32(0x0200471C + 0x20), table.concat(b, " ")))
end)

-- Report dialogue-window tile-ring overflow: within one page (map index not going back up the window) a tile index
-- is handed to a second map cell, so the later glyphs overwrite pixels that are still on screen (a list menu whose
-- rows need more tiles than the window's ring, e.g. "Dino Battle" losing its D to the end of the last row).
--   emu.py ... --script tools/lua/tilewrap.lua    (VwfDialog at HOOK_PC, default 0x087E1000; log lines "WRAP ...")
local pc = HOOK_PC or 0x087E1000
local T = 0x0200471C
local mem = emu.memType.gbaMemory or emu.memType.cpuMemory
local owner, last_map, last_line = {}, -1, -1
L.on_exec(pc, pc + 1, function()
  if emu.read16(T + 0x1C, mem) >= 0x100 then return end
  local map, tile, line = emu.read32(T + 0x30, mem), emu.read32(T + 0x34, mem), emu.read32(T + 0x20, mem)
  if line < last_line or map < last_map then owner = {} end  -- new page or new window: tiles are free again
  last_map, last_line = map, line
  local o = owner[tile]
  if o and o ~= map then
    L.log(string.format("WRAP f%d tile %d: map cell %d overwrites cell %d (line start %d)", L.frame, tile, map, o, line))
  end
  owner[tile] = map
end)

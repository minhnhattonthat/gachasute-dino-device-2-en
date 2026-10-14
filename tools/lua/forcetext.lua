-- Replace the text id of the first script lookup (0x0800D468, id in r0) after frame FROM with FORCE_ID, to reach scenes
-- a save is far from (the ending/credits: 0x0379 ends with E0 8C, which launches them).
--   emu.py ... --script tools/lua/forcetext.lua --var FORCE_ID=0x0379 --var FROM=160
local done = false
L.on_exec(0x0800D468, 0x0800D469, function()
  if done or L.frame < (FROM or 0) then return end
  done = true
  local s = emu.getState()
  L.log(string.format("force text id %04X -> %04X at frame %d", s["cpu.r0"] & 0xFFFF, FORCE_ID, L.frame))
  s["cpu.r0"] = FORCE_ID
  emu.setState(s)
end)

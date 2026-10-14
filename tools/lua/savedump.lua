-- Dump the cartridge save memory (EEPROM) to <out>/save.sav at frame DUMP_AT, so a savestate taken after an in-game
-- save can be turned into a battery file for a cold boot (--sav) to test the title Continue path.
--   emu.py ROM --out DIR --state-in S --route-str "10 -" --script tools/lua/savedump.lua
local done = false
L.on_frame(function(n)
  if done or n < (DUMP_AT or 5) then return end
  done = true
  local t = emu.memType.gbaSaveRam
  local size = emu.getMemorySize(t)
  local f = io.open(OUT .. "save.sav", "wb")
  for i = 0, size - 1 do f:write(string.char(emu.read(i, t))) end
  f:close()
  L.log("save bytes " .. size)
end)

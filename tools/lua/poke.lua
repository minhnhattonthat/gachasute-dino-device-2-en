-- Pin a 16-bit value every frame (god mode / cheats for QA routes).
--   emu.py ... --script tools/lua/poke.lua --var POKE_ADDR=0x02018298 --var POKE_VAL=80 [--var POKE_FROM=0]
-- Optional second value: --var POKE_ADDR2=.. --var POKE_VAL2=..
local mem = emu.memType.gbaMemory or emu.memType.cpuMemory
local function w16(a, v)
  emu.write(a, v & 0xFF, mem)
  emu.write(a + 1, (v >> 8) & 0xFF, mem)
end
local poked = false
L.on_frame(function(n)
  if n < (POKE_FROM or 0) or (POKE_ONCE and poked) then return end  -- --var POKE_ONCE=true: write once only
  poked = true
  w16(POKE_ADDR, POKE_VAL)
  if POKE_ADDR2 then w16(POKE_ADDR2, POKE_VAL2) end
end)

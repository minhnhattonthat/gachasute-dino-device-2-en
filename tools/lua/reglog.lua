-- Log registers (r0-r3) and 16 bytes at r1 each time PC hits HOOK_PC, from frame FROM on.
--   emu.py ... --script tools/lua/reglog.lua --var HOOK_PC=0x087E112C [--var FROM=600] [--var MAX=400]
local pc, from, max, n = assert(HOOK_PC), FROM or 0, MAX or 400, 0
local mem = emu.memType.gbaMemory or emu.memType.cpuMemory
local function reg(s, i)
  return s["cpu.r" .. i] or s["cpu.r[" .. i .. "]"] or s["cpu.R" .. i] or -1
end
L.on_exec(pc, pc + 1, function()
  if L.frame < from or n >= max then return end
  n = n + 1
  local s = emu.getState()
  if n == 1 then
    local keys = {}
    for k, _ in pairs(s) do if k:sub(1, 5) == "cpu.r" then keys[#keys + 1] = k end end
    L.log("keys " .. table.concat(keys, " "))
  end
  local r1 = reg(s, 1)
  local b = {}
  for i = 0, 15 do b[#b + 1] = string.format("%02X", emu.read(r1 + i, mem)) end
  L.log(string.format("f%d r0=%08X r1=%08X r2=%08X r3=%08X [r1]=%s", L.frame, reg(s, 0), r1, reg(s, 2), reg(s, 3),
    table.concat(b, " ")))
end)

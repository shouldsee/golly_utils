-- Simulate odd Wolfram rules from W1 to W127
local g = golly()
local n = tonumber(g.getstring("W", "1"))
local rule = "@RULE W"..n.."\n@TABLE\nn_States:3\nneighborhood:Moore\nsymmetries:none\n"
local temp
local s1 = ""
local s2 = ""
for i = 6, 1, -1 do
  temp = i
  for j = 2, 0, -1 do
    if temp >= 2^j then
      temp = temp - 2^j
      s1 = "0"..s1
    else s1 = "1"..s1 end
  end
  temp = i
  for k = 2, 0, -1 do
    if 7 - temp >= 2^k then
      temp = temp + 2^k
      s2 = "2"..s2
    else s2 = "0"..s2 end
  end
  if n > 2^i then
    rule = rule.."0"..s1:sub(2,3).."00000"..s1:sub(1,1).."2\n"
    rule = rule.."0"..s2:sub(2,3).."00000"..s2:sub(1,1).."1\n"
    n = n - 2^i
  end
end
g.setclipstr(rule)
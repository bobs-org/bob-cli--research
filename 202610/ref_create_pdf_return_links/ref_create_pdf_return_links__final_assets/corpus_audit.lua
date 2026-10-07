-- Audit local links: count, resolution under pandoc ids vs GFM ids, contexts.
local function gfm_id(text)
  local d = pandoc.read("# " .. text, "gfm")
  return d.blocks[1] and d.blocks[1].identifier or ""
end
function Pandoc(doc)
  local ids, gfm, dups = {}, {}, {}
  local gfm_seen = {}
  doc:walk({
    Header = function(h)
      if h.identifier ~= "" then
        if ids[h.identifier] then dups[h.identifier] = true end
        ids[h.identifier] = "Header"
      end
      local g = gfm_id(pandoc.utils.stringify(h.content))
      local n = gfm_seen[g]
      gfm_seen[g] = (n or -1) + 1
      if n then g = g .. "-" .. (n + 1) end
      gfm[g] = h.identifier
    end,
    Div = function(d) if d.identifier ~= "" then ids[d.identifier] = "Div" end end,
    Span = function(s) if s.identifier ~= "" then ids[s.identifier] = "Span" end end,
    CodeBlock = function(c) if c.identifier ~= "" then ids[c.identifier] = "CodeBlock" end end,
  })
  local total, ok_p, ok_g, dead, dead_both, fanin = 0, 0, 0, {}, 0, {}
  local in_header, in_table, in_list_only = 0, 0, 0
  local function count_link(l, ctx)
    if l.target:sub(1,1) ~= "#" then return end
    total = total + 1
    local t = l.target:sub(2)
    local dec = t:gsub("%%(%x%x)", function(h) return string.char(tonumber(h,16)) end)
    local key
    if ids[t] then ok_p = ok_p + 1; key = t
    elseif ids[dec] then ok_p = ok_p + 1; key = dec
    elseif gfm[t] or gfm[dec] then ok_g = ok_g + 1; key = gfm[t] or gfm[dec]
    else dead_both = dead_both + 1; table.insert(dead, l.target) end
    if key then fanin[key] = (fanin[key] or 0) + 1 end
    if ctx == "Header" then in_header = in_header + 1 end
    if ctx == "Table" then in_table = in_table + 1 end
    if ctx == "nav" then in_list_only = in_list_only + 1 end
  end
  local function is_nav_item(item)
    local f = item[1]
    return #item >= 1 and f and (f.t == "Plain" or f.t == "Para") and #f.content == 1 and f.content[1].t == "Link" and f.content[1].target:sub(1,1) == "#"
  end
  local function walk(blocks)
    for _, b in ipairs(blocks) do
      if b.t == "Header" then b:walk({Link = function(l) count_link(l, "Header") end})
      elseif b.t == "Table" then b:walk({Link = function(l) count_link(l, "Table") end})
      elseif b.t == "BulletList" or b.t == "OrderedList" then
        for _, item in ipairs(b.content) do
          if is_nav_item(item) then
            count_link(item[1].content[1], "nav")
            local rest = {}
            for i = 2, #item do table.insert(rest, item[i]) end
            walk(rest)
          else walk(item) end
        end
      elseif b.t == "Div" or b.t == "BlockQuote" then walk(b.content)
      else b:walk({Link = function(l) count_link(l, "prose") end}) end
    end
  end
  walk(doc.blocks)
  local maxf = 0
  for _, v in pairs(fanin) do if v > maxf then maxf = v end end
  local ntargets = 0 for _ in pairs(fanin) do ntargets = ntargets + 1 end
  local dupn = 0 for _ in pairs(dups) do dupn = dupn + 1 end
  local fh = io.open(os.getenv("AUDIT_OUT"), "a"); fh:write(PANDOC_STATE.input_files[1] .. "\t" .. string.format("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n", total, ok_p, ok_g, dead_both, maxf, ntargets, in_header, in_table, in_list_only, table.concat(dead, " "))); fh:close()
  return doc
end

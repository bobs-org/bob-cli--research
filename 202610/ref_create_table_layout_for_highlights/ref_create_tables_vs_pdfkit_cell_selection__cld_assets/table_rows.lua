-- Prototype: post-process pandoc's longtable to separate body rows.
-- BOB_TABLE_ROWS = space | hairline | grid | zebra
local style = os.getenv("BOB_TABLE_ROWS") or "space"
local SEP = {
  space = "\\addlinespace[4pt]",
  hairline = "\\BobRowRule",
  grid = "\\hline",
  zebra = "",
}
function Table(tbl)
  if not FORMAT:match("latex") then return nil end
  local tex = pandoc.write(pandoc.Pandoc({ tbl }), "latex")
  local head, body, tail = tex:match("^(.-\\endlastfoot\n)(.-)(\\end{longtable}.*)$")
  if not head then return nil end
  local rows = {}
  for row in body:gmatch("(.-\\\\)\n") do table.insert(rows, row) end
  local sep = SEP[style]
  if style == "grid" then
    -- vertical rules between columns, full box, \hline instead of booktabs rules
    head = head:gsub("@{}\n", "|", 1):gsub("@{}}", "|}", 1)
    head = head:gsub("(\n  >{)", "|%1"):gsub("^(.-){|", "%1{", 1)
    head = head:gsub("\\toprule\\noalign{}", "\\hline"):gsub("\\midrule\\noalign{}", "\\hline"):gsub("\\bottomrule\\noalign{}", "\\hline")
  end
  local out = {}
  for i, row in ipairs(rows) do
    table.insert(out, row .. ((i < #rows and sep ~= "") and (" " .. sep) or ""))
  end
  local pre = style == "zebra" and "\\rowcolors{1}{BobZebra}{white}\n" or ""
  return pandoc.RawBlock("latex", pre .. head .. table.concat(out, "\n") .. "\n" .. tail)
end

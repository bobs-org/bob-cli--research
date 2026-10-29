-- Prototype: each body row becomes a hanging-indent paragraph group. The first cell sits
-- in a left gutter (bold); every other cell is an ordinary paragraph to its right, prefixed
-- by its column header in small caps-ish italics when the table has more than two columns.
local GUTTER = "0.24\\linewidth"
local function latex(inl) return pandoc.write(pandoc.Pandoc({ pandoc.Plain(inl) }), "latex") end
function Table(tbl)
  if not FORMAT:match("latex") then return nil end
  local heads = {}
  if #tbl.head.rows > 0 then
    for i, c in ipairs(tbl.head.rows[1].cells) do heads[i] = pandoc.utils.stringify(c.contents) end
  end
  local n = #tbl.colspecs
  local parts = { "\\par\\medskip" }
  for _, b in ipairs(tbl.bodies) do
    for _, r in ipairs(b.body) do
      local label = latex(pandoc.utils.blocks_to_inlines(r.cells[1].contents))
      for i = 2, #r.cells do
        local value = latex(pandoc.utils.blocks_to_inlines(r.cells[i].contents))
        local prefix = (n > 2 and heads[i] and heads[i] ~= "") and ("\\emph{" .. latex({ pandoc.Str(heads[i] .. ":") }) .. "} ") or ""
        local lead = (i == 2) and ("\\makebox[" .. GUTTER .. "][l]{\\parbox[t]{\\dimexpr" .. GUTTER .. "-1em\\relax}{\\raggedright\\textbf{" .. label .. "}}}") or ("\\hspace*{" .. GUTTER .. "}")
        table.insert(parts, "\\par\\noindent\\hangindent=" .. GUTTER .. "\\hangafter=1 " .. lead .. prefix .. value .. "\\par")
      end
      table.insert(parts, "\\vspace{4pt}")
    end
  end
  table.insert(parts, "\\medskip")
  return pandoc.RawBlock("latex", table.concat(parts, "\n"))
end

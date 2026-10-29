-- Prototype: render each body row as a block ("record" layout): the first cell is a
-- bold lead-in and every other cell follows as "Header: value" on its own line.
function Table(tbl)
  local heads = {}
  if #tbl.head.rows > 0 then
    for i, c in ipairs(tbl.head.rows[1].cells) do heads[i] = pandoc.utils.stringify(c.contents) end
  end
  local out = {}
  for _, b in ipairs(tbl.bodies) do
    for _, r in ipairs(b.body) do
      local first = pandoc.utils.blocks_to_inlines(r.cells[1].contents)
      table.insert(out, pandoc.Para({ pandoc.Strong(first) }))
      local items = {}
      for i = 2, #r.cells do
        local inl = pandoc.utils.blocks_to_inlines(r.cells[i].contents)
        local label = heads[i] and heads[i] ~= "" and (heads[i] .. ": ") or ""
        local para = { pandoc.Emph({ pandoc.Str(label) }) }
        for _, x in ipairs(inl) do table.insert(para, x) end
        table.insert(items, { pandoc.Plain(para) })
      end
      table.insert(out, pandoc.BulletList(items))
    end
  end
  return out
end

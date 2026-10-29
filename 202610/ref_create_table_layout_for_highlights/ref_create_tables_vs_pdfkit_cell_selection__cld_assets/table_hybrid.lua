-- Prototype hybrid: prose tables (some non-first cell >= PROSE_WORDS words) render as row
-- records; everything else stays a grid with content-aware widths (table_widths.lua runs first).
local PROSE_WORDS = tonumber(os.getenv("BOB_TABLE_PROSE_WORDS") or "12")
local function words(blocks) local n = 0; for _ in pandoc.utils.stringify(blocks):gmatch("%S+") do n = n + 1 end; return n end
local function is_prose(tbl)
  for _, b in ipairs(tbl.bodies) do for _, r in ipairs(b.body) do
    for i, c in ipairs(r.cells) do if i > 1 and words(c.contents) >= PROSE_WORDS then return true end end
  end end
  return false
end
function Table(tbl)
  if not is_prose(tbl) then return nil end
  local heads = {}
  if #tbl.head.rows > 0 then for i, c in ipairs(tbl.head.rows[1].cells) do heads[i] = pandoc.utils.stringify(c.contents) end end
  local ncol = #tbl.colspecs
  local out = {}
  for _, b in ipairs(tbl.bodies) do for _, r in ipairs(b.body) do
    table.insert(out, pandoc.Para({ pandoc.Strong(pandoc.utils.blocks_to_inlines(r.cells[1].contents)) }))
    local items = {}
    for i = 2, #r.cells do
      local inl = pandoc.utils.blocks_to_inlines(r.cells[i].contents)
      if ncol > 2 and heads[i] and heads[i] ~= "" then
        table.insert(inl, 1, pandoc.Space()); table.insert(inl, 1, pandoc.Emph({ pandoc.Str(heads[i] .. ":") }))
      end
      table.insert(items, { pandoc.Plain(inl) })
    end
    if ncol > 2 then table.insert(out, pandoc.BulletList(items))
    else for _, it in ipairs(items) do table.insert(out, pandoc.BlockQuote({ pandoc.Para(it[1].content) })) end end
  end end
  return out
end

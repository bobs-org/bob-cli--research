-- Lead prototype: paired return links for same-document links (pandoc 3.1, LaTeX only).
local MOD = { a="ᵃ", b="ᵇ", c="ᶜ", d="ᵈ", e="ᵉ", f="ᶠ", g="ᵍ", h="ʰ", i="ⁱ", j="ʲ",
  k="ᵏ", m="ᵐ", n="ⁿ", p="ᵖ", r="ʳ", s="ˢ", t="ᵗ", u="ᵘ", v="ᵛ", w="ʷ", x="ˣ", y="ʸ", z="ᶻ" }
local ALPHABET = "abcdefghijkmnprstuvwxyz" -- no q (no glyph), l (reads as 1), o (reads as degree sign)
local N = #ALPHABET
local function letters(n)
  local out = ""
  while n > 0 do
    local r = (n - 1) % N
    out = ALPHABET:sub(r + 1, r + 1) .. out
    n = (n - 1 - r) // N
  end
  return out
end
local function glyphs(tag) return (tag:gsub("%a", MOD)) end

local function gfm_slug(inlines)
  local d = pandoc.read("# " .. pandoc.utils.stringify(inlines), "gfm")
  return d.blocks[1] and d.blocks[1].identifier or ""
end

local function is_nav_list(list)
  for _, item in ipairs(list.content) do
    local first = item[1]
    if not first or (first.t ~= "Plain" and first.t ~= "Para") or #first.content ~= 1
      or first.content[1].t ~= "Link" or first.content[1].target:sub(1, 1) ~= "#" then
      return false
    end
    for k = 2, #item do
      if not ((item[k].t == "BulletList" or item[k].t == "OrderedList") and is_nav_list(item[k])) then
        return false
      end
    end
  end
  return #list.content > 0
end

function Pandoc(doc)
  if not FORMAT:match("latex") then return nil end
  local flag = doc.meta["bob-return-links"]
  if flag ~= nil and (flag == false or pandoc.utils.stringify(flag) == "false") then return nil end

  -- 1. Index identifiers; build GitHub-slug aliases with pandoc's own gfm reader.
  local ids, alias, alias_seen, ambiguous = {}, {}, {}, {}
  local function add_id(el) if el.identifier and el.identifier ~= "" then ids[el.identifier] = true end end
  doc:walk({ Div = add_id, Span = add_id, CodeBlock = add_id, Table = add_id, Figure = add_id,
    Header = function(h)
      add_id(h)
      local g = gfm_slug(h.content)
      if g ~= "" then
        local n = alias_seen[g]; alias_seen[g] = (n or -1) + 1
        if n then g = g .. "-" .. (n + 1) end
        if alias[g] and alias[g] ~= h.identifier then ambiguous[g] = true end
        alias[g] = h.identifier
      end
    end })
  local function resolve(target)
    local raw = target:sub(2)
    if raw == "" then return nil end
    if ids[raw] then return raw end
    local decoded = raw:gsub("%%(%x%x)", function(h) return string.char(tonumber(h, 16)) end)
    if ids[decoded] then return decoded end
    if alias[decoded] and not ambiguous[decoded] then return alias[decoded] end
    return nil
  end

  -- 2. Tag eligible occurrences in reading order.
  local inbound, order, counter, dead, untagged = {}, {}, 0, {}, 0
  local function mark(skip)
    return function(link)
      if link.target:sub(1, 1) ~= "#" then return nil end
      local id = resolve(link.target)
      if not id then
        table.insert(dead, { target = link.target, text = pandoc.utils.stringify(link.content) })
        return pandoc.Span(link.content) -- plain text: do not promise a jump
      end
      link.target = "#" .. id
      if skip then untagged = untagged + 1; return link end
      counter = counter + 1
      local anchor, tag = "bob:ret:" .. counter, letters(counter)
      if not inbound[id] then inbound[id] = {}; table.insert(order, id) end
      table.insert(inbound[id], { anchor = anchor, tag = tag })
      link.content:insert(pandoc.RawInline("latex", "\\BobTag{" .. glyphs(tag) .. "}"))
      return { pandoc.RawInline("latex", "\\BobReturnAnchor{" .. anchor .. "}"), link }
    end
  end
  local tag_links, skip_links = { Link = mark(false) }, { Link = mark(true) }
  local walk_blocks
  local function walk_table(t)
    local function cells(rows, f)
      for _, row in ipairs(rows) do for _, cell in ipairs(row.cells) do cell.contents = f(cell.contents) end end
    end
    local skip = function(bs) return bs:walk(skip_links) end
    t.caption.long = skip(t.caption.long)
    cells(t.head.rows, skip)
    for _, body in ipairs(t.bodies) do cells(body.head, skip); cells(body.body, walk_blocks) end
    cells(t.foot.rows, walk_blocks)
    return t
  end
  walk_blocks = function(blocks)
    local out = pandoc.Blocks({})
    for _, b in ipairs(blocks) do
      if b.t == "Header" or (b.t == "BulletList" and is_nav_list(b)) or (b.t == "OrderedList" and is_nav_list(b)) then
        b = b:walk(skip_links)
      elseif b.t == "Table" then b = walk_table(b)
      elseif b.t == "Figure" then b.caption.long = b.caption.long:walk(skip_links); b.content = walk_blocks(b.content)
      elseif b.t == "Div" or b.t == "BlockQuote" then b.content = walk_blocks(b.content)
      elseif b.t == "BulletList" or b.t == "OrderedList" then
        local items = pandoc.List()
        for _, item in ipairs(b.content) do items:insert(walk_blocks(item)) end
        b.content = items
      else b = b:walk(tag_links) end
      out:insert(b)
    end
    return out
  end
  doc.blocks = walk_blocks(doc.blocks)

  -- 3. Attach one return row per target, in reading order of the sources.
  local function row(id)
    local list = inbound[id]
    if not list then return nil end
    local parts = {}
    for _, e in ipairs(list) do table.insert(parts, "\\BobBack{" .. e.anchor .. "}{" .. glyphs(e.tag) .. "}") end
    return table.concat(parts, "\\BobBackSep{}")
  end
  doc.blocks = doc.blocks:walk({
    Blocks = function(blocks)
      local out = pandoc.Blocks({})
      for _, b in ipairs(blocks) do
        out:insert(b)
        if b.t == "Header" and row(b.identifier) then
          local nxt = blocks[_ + 1]
          if nxt and nxt.t == "Table" then
            out:insert(#out, pandoc.RawBlock("latex", "\\needspace{16\\baselineskip}"))
          end
          out:insert(pandoc.RawBlock("latex", "\\BobBacklinks{" .. row(b.identifier) .. "}"))
        elseif b.t == "Div" and b.identifier ~= "" and row(b.identifier) then
          b.content:insert(1, pandoc.RawBlock("latex", "\\BobBacklinks{" .. row(b.identifier) .. "}"))
        end
      end
      return out
    end,
    Span = function(s)
      if s.identifier ~= "" and row(s.identifier) then
        return { s, pandoc.RawInline("latex", "\\BobBackInline{" .. row(s.identifier) .. "}") }
      end
    end,
  })

  -- 4. Machine-readable report for bob.
  for _, d in ipairs(dead) do
    io.stderr:write(string.format("bob-return-links: dead %s %q\n", d.target, d.text))
  end
  io.stderr:write(string.format("bob-return-links: summary paired=%d targets=%d untagged=%d dead=%d\n",
    counter, #order, untagged, #dead))
  return doc
end

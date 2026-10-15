-- Spike filter: map the projection's classes (.st, .chip, .label, .muted) to
-- LaTeX, Typst, or HTML. Task lists become lists whose marker is the status glyph.
local fmt = FORMAT

local function is_latex() return fmt:match("latex") ~= nil end
local function is_typst() return fmt:match("typst") ~= nil end

local function raw(s)
  if is_latex() then return pandoc.RawInline("latex", s) end
  if is_typst() then return pandoc.RawInline("typst", s) end
  return nil
end

local function write_inlines(inlines)
  local doc = pandoc.Pandoc({pandoc.Plain(inlines)})
  local out = pandoc.write(doc, is_latex() and "latex" or "typst")
  return (out:gsub("%s+$", ""))
end

local EMOJI = "[\240][\159][\128-\191][\128-\191]"  -- 4-byte U+1F000..U+1FFFF

function Str(el)
  if not is_latex() then return nil end
  if el.text:find(EMOJI) then
    local pieces = {}
    local rest = el.text
    while true do
      local s, e = rest:find(EMOJI)
      if not s then break end
      if s > 1 then table.insert(pieces, pandoc.Str(rest:sub(1, s - 1))) end
      table.insert(pieces, pandoc.RawInline("latex", "{\\BobEmoji " .. rest:sub(s, e) .. "}"))
      rest = rest:sub(e + 1):gsub("^\239\184\143", "")  -- drop VS16
    end
    if #rest > 0 then table.insert(pieces, pandoc.Str(rest)) end
    return pieces
  end
end

local function wrapped(open, content, close)
  local out = {raw(open)}
  for _, x in ipairs(content) do table.insert(out, x) end
  table.insert(out, raw(close))
  return out
end

function Span(el)
  if not (is_latex() or is_typst()) then return nil end
  if el.classes:includes("chip") then
    return wrapped(is_latex() and "\\BobChip{" or "#chip[", el.content, is_latex() and "}" or "]")
  elseif el.classes:includes("label") then
    return wrapped(is_latex() and "\\BobLabel{" or "#lab[", el.content, is_latex() and "}" or "]")
  elseif el.classes:includes("muted") then
    return wrapped(is_latex() and "\\BobMuted{" or "#muted[", el.content, is_latex() and "}" or "]")
  elseif el.identifier ~= "" and el.identifier:match("^t%-") and is_typst() then
    return wrapped("#box[", el.content, "]<" .. el.identifier .. ">")
  end
end

local function status_of(item)
  local first = item[1]
  if not first or (first.t ~= "Plain" and first.t ~= "Para") then return nil end
  local lead = first.content[1]
  if lead and lead.t == "Span" and lead.classes:includes("st") then
    for _, c in ipairs(lead.classes) do
      local s = c:match("^st%-(.+)$")
      if s then return s end
    end
  end
  return nil
end

local function strip_status(item)
  local first = item[1]
  table.remove(first.content, 1)
  while first.content[1] and first.content[1].t == "Space" do table.remove(first.content, 1) end
  return item
end

function BulletList(el)
  local any = false
  for _, item in ipairs(el.content) do if status_of(item) then any = true end end
  if not any then return nil end
  if is_latex() then
    local parts = {"\\begin{itemize}"}
    for _, item in ipairs(el.content) do
      local st = status_of(item)
      if st then strip_status(item) end
      local body = pandoc.write(pandoc.Pandoc(item), "latex")
      local label = st and ("[\\BobSt{" .. st .. "}]") or ""
      table.insert(parts, "\\item" .. label .. " " .. body)
    end
    table.insert(parts, "\\end{itemize}")
    return pandoc.RawBlock("latex", table.concat(parts, "\n"))
  elseif is_typst() then
    local parts = {}
    for _, item in ipairs(el.content) do
      local st = status_of(item) or "none"
      if st ~= "none" then strip_status(item) end
      local body = pandoc.write(pandoc.Pandoc(item), "typst")
      table.insert(parts, "task(\"" .. st .. "\")[" .. body .. "]")
    end
    return pandoc.RawBlock("typst", "#tasks(" .. table.concat(parts, ", ") .. ")")
  end
end


local function meta_str(meta, key)
  local v = meta[key]
  if v == nil then return nil end
  return v
end

local function as_inlines(v)
  if v == nil then return {} end
  if type(v) == "string" then return {pandoc.Str(v)} end
  if v.t == "MetaInlines" or pandoc.utils.type(v) == "Inlines" then return v end
  return {pandoc.Str(pandoc.utils.stringify(v))}
end

function Pandoc(doc)
  if not (is_latex() or is_typst()) then return nil end
  local m = doc.meta
  -- "In this note" line from level-1 headings
  local nav = {}
  for _, b in ipairs(doc.blocks) do
    if b.t == "Header" and b.level == 1 then
      if #nav > 0 then table.insert(nav, raw(is_latex() and "\\BobDot{}" or " · ")) end
      table.insert(nav, pandoc.Link(b.content, "#" .. b.identifier))
    end
  end
  local function wrap(cmd, v)
    local il = (type(v) == "table" and v.t == nil and pandoc.utils.type(v) == "table") and v or as_inlines(v)
    if #il == 0 then return {} end
    local out = {raw(cmd .. (is_latex() and "{" or "["))}
    for _, x in ipairs(il) do table.insert(out, x) end
    table.insert(out, raw(is_latex() and "}" or "]"))
    return out
  end
  local blocks = {}
  local prefix = is_latex() and "\\Bob" or "#mast"
  local function add(name, v)
    local il = wrap(prefix .. name, v)
    if #il > 0 then table.insert(blocks, pandoc.Plain(il)) end
  end
  add("Kicker", m.kicker)
  add("Title", m.title)
  add("Goal", m.goal)
  add("GoalMeta", m.goalmeta)
  add("Stats", m.stats)
  if #nav > 0 then add("Nav", nav) end
  add("Snapshot", m.snapshot)
  table.insert(blocks, pandoc.RawBlock(is_latex() and "latex" or "typst", is_latex() and "\\BobRule" or "#mastrule"))
  for _, b in ipairs(doc.blocks) do table.insert(blocks, b) end
  doc.blocks = blocks
  doc.meta.title = nil
  return doc
end

return {{Str = Str, Span = Span}, {BulletList = BulletList}, {Pandoc = Pandoc}}

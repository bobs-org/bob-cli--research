local targets, counts, incoming = {}, {}, {}
local next_label = 0
local function register(el)
  if el.identifier and el.identifier ~= '' then
    counts[el.identifier] = (counts[el.identifier] or 0) + 1
    targets[el.identifier] = el.t
  end
end
local function strip(id)
  local entries = incoming[id]
  if not entries then return nil end
  local inlines = {pandoc.RawInline('latex', '\\BobReturnStart{}')}
  for i, e in ipairs(entries) do
    if i > 1 then table.insert(inlines, pandoc.RawInline('latex', '\\BobReturnSep{}')) end
    table.insert(inlines, pandoc.Link({pandoc.Str(e.label)}, '#' .. e.source))
  end
  table.insert(inlines,pandoc.RawInline('latex','\\BobReturnEnd{}'))
  return pandoc.Para(inlines)
end
function Pandoc(doc)
  if not FORMAT:match('latex') then return doc end
  doc.blocks:walk{Header=register,Span=register,Div=register,CodeBlock=register,Link=register}
  doc.blocks=doc.blocks:walk{traverse='topdown',Link=function(link)
    if link.attributes['data-bob-visit'] then return nil end
    link.attributes['data-bob-visit']='1'
    local id=link.target:match('^#(.+)$')
    if not id or counts[id] ~= 1 or targets[id] ~= 'Header' then return nil end
    next_label=next_label+1
    local label='R' .. tostring(next_label)
    local source='bob-return-' .. label
    while counts[source] do source=source .. 'x' end
    counts[source]=1
    incoming[id]=incoming[id] or {}
    table.insert(incoming[id],{label=label,source=source})
    table.insert(link.content,pandoc.RawInline('latex','\\BobVisit{' .. label .. '}'))
    return pandoc.Span({link},pandoc.Attr(source))
  end}
  doc.blocks=doc.blocks:walk{Header=function(h)
    local panel=strip(h.identifier)
    if panel then return {h,panel} end
  end}
  return doc
end

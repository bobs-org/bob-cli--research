-- Replace mermaid CodeBlocks with a pre-rendered PDF keyed by sha1(text).
local dir
function Meta(m) dir = pandoc.utils.stringify(m["bob-diagrams-dir"] or "") end
function CodeBlock(cb)
  if not cb.classes:includes("mermaid") then return nil end
  local path = dir .. "/" .. pandoc.utils.sha1(cb.text) .. ".pdf"
  local f = io.open(path, "rb")
  if not f then
    return {pandoc.Para{pandoc.Emph{pandoc.Str("Mermaid diagram not rendered.")}}, cb}
  end
  f:close()
  return pandoc.Para{pandoc.Image({}, path)}
end
return {{Meta = Meta}, {CodeBlock = CodeBlock}}

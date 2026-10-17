local items = {}
return {{CodeBlock = function(cb)
  if cb.classes:includes("mermaid") then
    items[#items + 1] = {sha1 = pandoc.utils.sha1(cb.text), text = cb.text}
  end
end}, {Pandoc = function(doc)
  local f = io.open(os.getenv("MANIFEST"), "w"); f:write(pandoc.json.encode(items)); f:close()
end}}

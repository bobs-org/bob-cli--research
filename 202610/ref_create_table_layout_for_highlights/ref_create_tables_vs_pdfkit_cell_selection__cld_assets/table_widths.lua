-- Prototype: content-aware column widths (CSS "auto" table layout, in characters).
-- min = longest word, max = longest cell. If every column fits at max, let pandoc
-- use natural-width columns; otherwise give each column its min and share the
-- remaining line in proportion to (max - min).
local LINE = tonumber(os.getenv("BOB_TABLE_LINE_CHARS") or "92")
local function len(s) return utf8.len(s) or #s end
local function scan(tbl)
  local n = #tbl.colspecs
  local mn, mx = {}, {}
  for i = 1, n do mn[i], mx[i] = 1, 1 end
  local function row(r)
    for i, cell in ipairs(r.cells) do
      if i <= n and cell.col_span == 1 then
        local s = pandoc.utils.stringify(cell.contents)
        mx[i] = math.max(mx[i], len(s))
        for w in s:gmatch("%S+") do mn[i] = math.max(mn[i], math.min(len(w), 24)) end
      end
    end
  end
  for _, r in ipairs(tbl.head.rows) do row(r) end
  for _, b in ipairs(tbl.bodies) do for _, r in ipairs(b.body) do row(r) end end
  return n, mn, mx
end
function Table(tbl)
  local n, mn, mx = scan(tbl)
  local gutter = 3 * n
  local summax, summin = 0, 0
  for i = 1, n do summax = summax + mx[i]; summin = summin + mn[i] end
  if summax + gutter <= LINE then
    for i = 1, n do tbl.colspecs[i] = { tbl.colspecs[i][1], pandoc.ColWidthDefault } end
    return tbl
  end
  local avail = math.max(LINE - gutter, summin)
  local slack, spread = avail - summin, summax - summin
  local w, tot = {}, 0
  for i = 1, n do
    w[i] = mn[i] + (spread > 0 and slack * (mx[i] - mn[i]) / spread or slack / n)
    tot = tot + w[i]
  end
  for i = 1, n do tbl.colspecs[i] = { tbl.colspecs[i][1], w[i] / tot } end
  return tbl
end

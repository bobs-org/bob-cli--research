# Research prototype, cdx

This is an experiment, not a proposed production patch. `backlinks.lua` instruments
unique heading targets only; it intentionally does not implement the full scope,
URI normalization, diagnostics, context exclusions, or page-boundary behavior
recommended in the accompanying report. Do not install it as bob's shipping filter.

`demo.pdf` is the output of the installed `bob ref create` Markdown route with this
filter injected using `BOB_PANDOC_COMMAND`, including the Highlights scan marker.
`preview.png` is a raster of the equivalent directly compiled PDF's first page.
`verification.json` records PDF structure assertions before and after stamping.
No macOS or iPad viewer was available for a real interaction test.

To reproduce the rendering, run from this directory with Pandoc and XeLaTeX:

```sh
pandoc demo.md -o demo.tex --standalone --toc --toc-depth=3 \
  --number-sections --pdf-engine=xelatex --highlight-style=tango \
  --lua-filter backlinks.lua --include-in-header navigation.tex \
  -V colorlinks=true -V geometry:margin=0.85in -V fontsize=10pt \
  -V linestretch=1.08 -V 'mainfont=DejaVu Serif' \
  -V 'sansfont=DejaVu Sans' -V 'monofont=DejaVu Sans Mono'
xelatex -interaction=nonstopmode -halt-on-error demo.tex
xelatex -interaction=nonstopmode -halt-on-error demo.tex
```

The second XeLaTeX pass resolves forward references and the TOC. These commands
write local build products and replace `demo.pdf`; copy the bundle to scratch first
when preserving the registered snapshot. The production path lets Pandoc manage
its necessary TeX passes.

Inspection used Pandoc 3.1.11.1, Lua 5.4, XeTeX from TeX Live 2025/dev/Debian,
DejaVu fonts, Poppler for the raster, and pypdf for structural checks.

The stress example has 23 link occurrences, 23 distinct source anchors, and 21
return entries under Design rationale. One forward link wraps across lines, so
50 semantic links occupy 51 physical `/Link` annotations. All destinations exist,
all actions are `/GoTo`, the four outline entries survive stamping, and the first
page's first annotation is bob's `/Text` marker. The output has no tagged-PDF
structure tree; it does not establish assistive-technology accessibility.

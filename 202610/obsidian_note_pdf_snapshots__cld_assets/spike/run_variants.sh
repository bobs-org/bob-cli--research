#!/usr/bin/env bash
# Usage: run_variants.sh <note.md> <outdir> <short title>
set -uo pipefail
NOTE=$1; OUT=$2; SHORT=$3
S=/tmp/cld_pdfresearch/scripts
mkdir -p "$OUT"
NAME=$(basename "$NOTE" .md)
python3 -I $S/project_note.py "$NOTE" > "$OUT/$NAME.projected.md"
COMMON_OLD=(--standalone --toc --toc-depth=3 --number-sections --pdf-engine=xelatex -V colorlinks=true -V geometry:margin=0.85in -V fontsize=10pt -V linestretch=1.08 -V "mainfont=DejaVu Serif" -V "sansfont=DejaVu Sans" -V "monofont=DejaVu Sans Mono" -V 'header-includes=\usepackage{fvextra}\DefineVerbatimEnvironment{Highlighting}{Verbatim}{breaklines,breakanywhere,commandchars=\\\{\}}')
t() { local s=$(date +%s.%N); "$@" 2> "$OUT/err.$$" ; local rc=$?; local e=$(date +%s.%N); printf "%6.2fs rc=%d\n" $(echo "$e - $s" | bc) $rc; [ $rc -ne 0 ] && tail -5 "$OUT/err.$$"; }
echo -n "A0 current (raw note):        "; t pandoc "$NOTE" -o "$OUT/A0_current_raw.pdf" "${COMMON_OLD[@]}" --resource-path="$(dirname $NOTE)" --metadata title="$NAME"
echo -n "A1 current (projected note):  "; t pandoc "$OUT/$NAME.projected.md" -o "$OUT/A1_current_projected.pdf" "${COMMON_OLD[@]}"
printf '\\newcommand{\\BobShortTitle}{%s}\n' "$SHORT" > "$OUT/short.tex"
echo -n "C  xelatex note template:     "; t pandoc "$OUT/$NAME.projected.md" -o "$OUT/C_xelatex_note.pdf" --standalone --pdf-engine=xelatex --lua-filter $S/note.lua -H $S/note-header.tex -H "$OUT/short.tex" -V colorlinks=true -V linkcolor=BobLinkInk -V urlcolor=BobLinkInk -V geometry:margin=1in -V fontsize=10.5pt -V title-meta="$SHORT"
sed "s|SHORTTITLE|$SHORT|" $S/note-template.typ > "$OUT/tmpl.typ"
echo -n "D  typst (pandoc->typst):     "; t bash -c "pandoc '$OUT/$NAME.projected.md' -t typst --lua-filter $S/note.lua -o '$OUT/body.typ' && cat '$OUT/tmpl.typ' '$OUT/body.typ' > '$OUT/D_typst.typ' && typst compile --font-path /usr/share/texlive/texmf-dist/fonts/opentype/adobe '$OUT/D_typst.typ' '$OUT/D_typst.pdf' --root /"
echo -n "E  html + chrome:             "; t bash -c "pandoc '$OUT/$NAME.projected.md' -t html5 --template $S/html-template.html -o '$OUT/E.html' && TMPDIR=/tmp google-chrome --headless=new --no-sandbox --user-data-dir=/tmp/cld_chrome_prof --disable-gpu --no-pdf-header-footer --allow-file-access-from-files --generate-pdf-document-outline --print-to-pdf='$OUT/E_chrome.pdf' 'file://$OUT/E.html' 2>/dev/null"
rm -f "$OUT/err.$$"
for f in "$OUT"/*.pdf; do printf "%-28s %3s pages %8s bytes\n" "$(basename $f)" "$(pdfinfo $f | awk '/^Pages/{print $2}')" "$(stat -c %s $f)"; done

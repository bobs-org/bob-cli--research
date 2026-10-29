# Assets for `ref_create_tables_vs_pdfkit_cell_selection__cld.md`

These are research artifacts, not a production patch.

| File | What it is |
| --- | --- |
| `cells_probe.swift`, `cells_probe_Info.plist` | The macOS probe behind the PDFView findings. It is a background-only (`LSUIElement`) app. It loads a PDF into an invisible PDFView (alpha 0, `ignoresMouseEvents`), waits for PDFKit's document analysis, and sends synthesized drags only to its own window, never through the system event queue. It reports whether each drag produced a text selection, a private table-cell selection (`isTableCellSelection`), or nothing. Modes: `on` (macOS defaults), `off` (private `documentAnalysisEnabled`/`formDetectionEnabled` set to `false`), and `markup` (public `isInMarkupMode`). An optional 6th argument sends a modifier (`option`, `shift`, `command`, `control`). |
| `test.md` | The three-table fixture: a 3-column comparison, a 2-column decision table, and a numeric table, with prose before and after. |
| `table_widths.lua` | Prototype content-aware column widths, after the CSS "auto" table layout: the minimum is the longest word, the maximum is the longest cell, and slack is shared in proportion to (max − min). |
| `table_rows.lua`, `rows_header.tex` | Prototype row separators that post-process pandoc's longtable (`space`, `hairline`, `grid`). The header must load `longtable,booktabs,array,calc` itself, because pandoc's template only loads them when the AST still contains a `Table`. |
| `table_stacked.lua` | Prototype "record" layout: each row becomes a bold lead-in followed by `Header: value` items. |
| `table_hybrid.lua` | Prototype of the recommended policy. Prose tables (any non-first cell of 12 or more words) become records; all other tables stay grids. |
| `table_hanging.lua` | Prototype hanging-indent key/value layout. PDFKit still sometimes classifies it as a table, so it is not recommended. |
| `corpus_table_kinds.py` | Classifies every table in `~/bob/.bob/ref-sources/*/*/source.md` as prose, mixed, or data. |
| `compare_current.png`, `compare_grid_widths_hairlines.png`, `compare_records_hybrid.png` | Page 2 of `now_tag_vs_in_progress_status` rendered three ways with bob's pandoc flags: the current output, content-aware widths with hairline rules, and the hybrid records layout. The tomato emoji shows as a missing glyph in all three renders; that is a separate bug (see the report). |

How the probe ran: on the MacBook (macOS 26.5, build 25F71), `swiftc -O -o Cells.app/Contents/MacOS/Cells cells_probe.swift`, then ad-hoc codesign and `open -W -n -g ./Cells.app --args OUT on 8 file.pdf targets.json`. The targets file is a JSON list of `{"kind": "cell"|"prose"|"phrase", "text": "..."}`. Renders were made on athena with pandoc 3.1.3, XeTeX (TinyTeX), and Playwright's chromium-headless-shell 1248 for the Chrome variants.

# Lead prototype and probes (final report)

These are research artifacts, not a production patch.

| File | What it is |
| --- | --- |
| `return_links.lua` | The merged prototype filter. It runs as a second `--lua-filter` after bob's existing code-break/listen filter. It resolves pandoc ids, then percent-decoded ids, then GitHub-style aliases computed with pandoc's own `gfm` reader. It tags eligible links with Unicode modifier letters and attaches a pill row under each target. Dead links become plain text. It prints `bob-return-links:` summary and dead-link lines on stderr. |
| `return_links.tex` | The TeX macros used with the filter: tag, pill, raised `/XYZ null y null` return destination, and row layout. It also includes the `\@afterheading` keep-with-next and the `needspace` package. |
| `source_tags.png` | Page 2 of `retire_now_sticky_lanes_ledger_today.md` (202609), rendered with bob's exact pandoc arguments plus the filter. |
| `target_pill_row.png` | Page 5 of the same render: a heading with fan-in 8, its pill row, and the table that follows. |
| `pdfkit_probe.md`, `pdfkit_probe.swift` | The probe that showed Apple PDFKit (macOS 26.5) ignores `/ActualText` and `/Alt` when extracting text. |
| `corpus_audit.lua` | The audit filter behind the corpus numbers (489 local links in 39 reports). |

How the render was made: bob's `render_temp_pdf` arguments, plus
`--lua-filter return_links.lua`, `-V linkcolor=BobLinkInk -V urlcolor=BobLinkInk`, and
the contents of `return_links.tex` appended to bob's `header-includes`. Tools: Pandoc
3.1.11.1 and XeTeX from TeX Live 2025/dev on athena.

The PDFKit probe ran on the MacBook through `swift pdfkit_probe.swift probe.pdf`. It ran
in a temporary directory that was deleted afterwards.

# Acceptance: highlight-friendly table layout

**Run date:** 2026-10-30  
**Scope:** Six preserved Markdown chat reports, the current Markdown fixture, and the current web-clip fixture.

The baseline release binary was built from the clean base worktree at `b8bcc78a6a5218d5075b6efeef892685fdb79fbf` (pre-epic; renders every table as a grid). The current release binary was built from the working tree with the landing-tale pack-branch record layout (run-in lead-in, `PACK_WORDS = 3` field packing, zero in-record `\parskip`, 6 pt record gap). The acceptance runner compared extracted cell text in order and checked per-document page counts. The vault's status was empty before and after (`[]`), so it remained unchanged.

## Corpus results

| Document | Pages baseline → current | Source tables | Current records / grids | Ordered text baseline → current | Current render warnings |
| --- | ---: | ---: | ---: | ---: | --- |
| `sase_goals_epic_roadmap` | 23 → 18 | 18 | 15 / 3 | 382/382 → 382/382 | None |
| `sase_core_maintainability_audit` | 19 → 17 | 14 | 7 / 7 | 297/298 → 298/298 | None |
| `memory_built_instruction_migration_epics` | 34 → 23 | 13 | 13 / 0 | 376/376 → 376/376 | None |
| `bob_daily_stats` | 28 → 22 | 13 | 9 / 4 | 286/286 → 286/286 | None |
| `agents_tab_inbox_and_history_views` | 28 → 28 | 13 | 8 / 5 | 325/325 → 325/325 | None |
| `now_tag_vs_in_progress_status` | 4 → 4 | 2 | 2 / 0 | 36/36 → 36/36 | None |
| `table-layout-fixture` (Markdown) | 2 → 2 | 3 | 2 / 1 | 36/36 → 36/36 | None |
| `web-tables-fixture` (HTML) | 2 → 2 | 3 | 1 / 2 | 13/13 → 13/13 | Guard + sandbox only (see below) |
| **Total** | **140 → 116** | **79** | **57 / 22** | **1,751/1,752 → 1,752/1,752** | **—** |

The current render has exact ordered text for all 1,752 checked cells. The runner excluded 29 symbol-only cells from text comparison (4 in `bob_daily_stats`, 25 in `agents_tab_inbox_and_history_views`). The baseline missed one occurrence in `sase_core_maintainability_audit` (`One leaf module in sase_core → cargo build --workspace`); the current render contains it in order. All current `kept_grid_warnings` lists are empty. The only current-render warning lines beyond the known listen-card and Mermaid-scale warnings are pre-existing lines also present in earlier runs: the web fixture's complex-table guard note (`table 3 stayed a grid: row or column spans`) and the environmental `browser sandbox unavailable` line (present in both baseline and current logs).

The per-document page limit **passes**: every document renders at or under its baseline page count (`agents_tab` 28 → 28, `sase_core` 19 → 17, roadmap 23 → 18, memory 34 → 23, daily_stats 28 → 22, now_tag 4 → 4, both fixtures 2 → 2). Text remains at body size, records keep a 6 pt gap with zero in-record paragraph spacing, and the corpus total fell by 24 pages. The record-layout change that closed the gap: the bold lead-in runs into the record's first field, consecutive short labeled fields (three words or fewer) share one line separated by `\BobFieldSep{}`, `\parskip` is 0 inside `BobTableRecords`, and records are separated by a 6 pt gap.

## Current Mac PDFKit probe

Probe not run on the new pack-branch PDFs: the Mac (`kellys-macbook-pro.tail297af1.ts.net`, user `bbugyi`) was unreachable over Tailscale SSH at landing time (two connection timeouts). The latest probe evidence therefore remains the prior run's `on`-mode `cells_probe` results on the 2 pt-spacing record PDFs, which were clean on every drag with no `TABLECELL` selections:

| Fixture | Cell drag | Phrase drag | Public page / document selection | `TABLECELL` |
| --- | --- | --- | --- | --- |
| Markdown `table-layout-fixture.pdf` | Clean | Clean | 2 / 2 clean | None |
| Web `web-tables-fixture.pdf` | Clean | Clean | 2 / 2 clean | None |

Each probe's tally was one clean cell drag, one clean phrase drag, two clean public page selections, and two clean public document-granularity selections. The private table-selection query returned no selection for the tested record text. No packed short-field line and no run-in lead line has been probed yet; per the landing tale, if a future probe finds a packed line detected as a table cell, the layout falls back to `stack` (no packing, 4 pt gap) and re-verifies.

## 12-word threshold evidence

The latest corpus sensitivity run examined 1,010 tables. At the default 12-word threshold, 680 tables (67%) become records, covering 89% of table text. At 8 words the result is 79% of tables and 94% of table text; at 15 words it is 58% and 83%. The default keeps the intended prose-table coverage while leaving short-cell data tables as grids. Raising it solely to reduce page counts would change that coverage and needs Bryan's review.

## Bryan's manual checklist

- In Highlights, open a generated fixture reference and one real report.
- Select a word, a phrase, a wrapped passage, and a whole former cell. Save each, close and reopen the PDF, and confirm every annotation has non-zero `/QuadPoints`.
- In a packed record, select across a whole run-in lead line (for example `**R1**  Count: …`) and across a packed short-field line, and confirm Highlights saves visible annotations with non-zero `/QuadPoints` (these packed lines have not yet been machine-probed).
- Run `bob ref scan` and compare each imported quote with the intended selection.
- At normal zoom, review two or three real reports: find a fact, compare it across rows, and identify the source table from the quote. Record any tables that should stay grids or should become records.
- For a remaining grid, use rectangle selection or a per-table `records` override. Adjust `highlights.table_prose_words` only if this review shows the 12-word rule classifies a comparison table incorrectly.

The automated text-fidelity and page-count checks pass on the pack-branch layout; the Mac probe of the new packed lines and Bryan's manual review are still needed. The epic declined a decision-memory record, so no decision was edited.

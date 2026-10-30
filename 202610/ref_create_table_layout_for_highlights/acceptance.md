# Acceptance: highlight-friendly table layout

**Run date:** 2026-10-30  
**Scope:** Six preserved Markdown chat reports, the current Markdown fixture, and the current web-clip fixture.

The baseline release binary was built from the clean base worktree at `b8bcc78a6a5218d5075b6efeef892685fdb79fbf`. The current release binary was built from checkout `a984ec5755138c678842aa2fd39ce6c38c8863e7` with the in-progress 2 pt `\BobRecordStart` spacing change. The acceptance runner compared extracted cell text in order and checked per-document page counts. The vault's status was empty before and after (`[]`), so it remained unchanged.

## Corpus results

| Document | Pages baseline → current | Source tables | Current records / grids | Ordered text baseline → current | Current render warnings |
| --- | ---: | ---: | ---: | ---: | --- |
| `sase_goals_epic_roadmap` | 23 → 22 | 18 | 15 / 3 | 382/382 → 382/382 | None |
| `sase_core_maintainability_audit` | 19 → 20 | 14 | 7 / 7 | 297/298 → 298/298 | None |
| `memory_built_instruction_migration_epics` | 34 → 28 | 13 | 13 / 0 | 376/376 → 376/376 | None |
| `bob_daily_stats` | 28 → 25 | 13 | 9 / 4 | 286/286 → 286/286 | None |
| `agents_tab_inbox_and_history_views` | 28 → 31 | 13 | 8 / 5 | 325/325 → 325/325 | None |
| `now_tag_vs_in_progress_status` | 4 → 4 | 2 | 2 / 0 | 36/36 → 36/36 | None |
| `table-layout-fixture` (Markdown) | 2 → 2 | 3 | 2 / 1 | 36/36 → 36/36 | None |
| `web-tables-fixture` (HTML) | 2 → 2 | 3 | 1 / 2 | 13/13 → 13/13 | None |
| **Total** | **140 → 134** | **79** | **57 / 22** | **1,751/1,752 → 1,752/1,752** | **None** |

The current render has exact ordered text for all 1,752 checked cells. The runner excluded 29 symbol-only cells from text comparison (4 in `bob_daily_stats`, 25 in `agents_tab_inbox_and_history_views`). The baseline missed one occurrence in `sase_core_maintainability_audit` (`One leaf module in sase_core → cargo build --workspace`); the current render contains it in order. All current `kept_grid_warnings` lists are empty, and no warning lines appeared in the baseline or current render logs.

The per-document page limit **does not pass**: `sase_core_maintainability_audit` grew by 1 page and `agents_tab_inbox_and_history_views` by 3. The corpus total fell by 6 pages because the other documents shortened. Text remains at body size, and the current record gap is 2 pt. No further spacing reduction was made because this run does not establish that a smaller gap would retain visibly separated rows. This leaves the per-document page-count requirement unresolved for the two reports above.

## Current Mac PDFKit probe

Both latest PDFs were copied to the Mac and probed with `cells_probe.swift` in `on` mode, an 8-second analysis wait, and document analysis enabled. The saved logs are `probe_markdown.log` and `probe_web.log` in the acceptance run directory.

| Fixture | Cell drag | Phrase drag | Public page / document selection | `TABLECELL` |
| --- | --- | --- | --- | --- |
| Markdown `table-layout-fixture.pdf` | Clean | Clean | 2 / 2 clean | None |
| Web `web-tables-fixture.pdf` | Clean | Clean | 2 / 2 clean | None |

Each probe's tally was one clean cell drag, one clean phrase drag, two clean public page selections, and two clean public document-granularity selections. The private table-selection query returned no selection for the tested record text. These outcomes are from the current 2 pt-spacing PDFs.

## 12-word threshold evidence

The latest corpus sensitivity run examined 1,010 tables. At the default 12-word threshold, 680 tables (67%) become records, covering 89% of table text. At 8 words the result is 79% of tables and 94% of table text; at 15 words it is 58% and 83%. The default keeps the intended prose-table coverage while leaving short-cell data tables as grids. Raising it solely to reduce page counts would change that coverage and needs Bryan's review.

## Bryan's manual checklist

- In Highlights, open a generated fixture reference and one real report.
- Select a word, a phrase, a wrapped passage, and a whole former cell. Save each, close and reopen the PDF, and confirm every annotation has non-zero `/QuadPoints`.
- Run `bob ref scan` and compare each imported quote with the intended selection.
- At normal zoom, review two or three real reports: find a fact, compare it across rows, and identify the source table from the quote. Record any tables that should stay grids or should become records.
- For a remaining grid, use rectangle selection or a per-table `records` override. Adjust `highlights.table_prose_words` only if this review shows the 12-word rule classifies a comparison table incorrectly.

The automated text-fidelity and Mac selection checks pass, but the per-document page limit remains open for two reports and Bryan's manual review is still needed. The epic declined a decision-memory record, so no decision was edited.

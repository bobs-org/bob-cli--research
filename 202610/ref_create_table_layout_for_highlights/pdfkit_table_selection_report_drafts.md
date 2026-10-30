# PDFKit table-selection report drafts

These are drafts for Bryan to send. No report has been sent or filed.

## Email to the Highlights developer

**Subject:** macOS 26 PDFKit table selection can save invisible Highlights annotations

Hi,

I tracked down a table-highlighting failure in Highlights 2026.1.2 on macOS 26.5 (25F71). The behavior appears to come from PDFKit's document analysis in `PDFView`, rather than from the PDF text layer or a particular table style.

After PDFKit's asynchronous page analysis detects a table visually, a drag over a cell can return a private `PDFSelection` for the whole table cell (`isTableCellSelection`) instead of a text selection. In my probe that selection had infinite bounds and no usable per-line rectangles. Some drags returned `nil`. The cell selection also sometimes omitted characters at line ends. The public `PDFPage.selection(from:to:)` API likewise returned `nil` for 20 of 22 tested table cells after analysis had run.

This matches a PDF in my library: table highlights created before analysis had real geometry, while later attempts produced annotations with all-zero `/QuadPoints` (or did not produce a useful selection). Those zero-geometry annotations are invisible. In an offscreen `PDFView` probe on macOS 26.5, disabling the private `documentAnalysisEnabled` switch restored ordinary text selection for all 22 tested cells; with analysis enabled, grid variants consistently produced table-cell selections or no selection. A single-column row-record rendering selected all 22 cells and all 7 phrase drags as text.

Would you consider adding a user preference to disable PDFKit's table/document-analysis selection behavior if a supported route is feasible? If it is not feasible to opt out, could Highlights refuse to save a text highlight or underline when the selection has no finite, non-empty geometry (for example, no usable line rectangles or zero `/QuadPoints`)? A clear message would be much better than silently saving an annotation that cannot be seen.

I can provide the small probe and PDFs if useful. The probe uses synthesized drags in an offscreen `PDFView`, so it is not a full UI automation of Highlights, but the zero-geometry annotations in my own document independently match the failure mode.

Thanks,
Bryan

## Apple Feedback Assistant: PDFKit table detection prevents text selection and creates geometry-less annotations

**Product:** PDFKit / Preview  
**Title:** macOS 26 PDFKit table detection prevents text selection inside table cells  
**Environment:** macOS 26.5 (25F71); Preview and Highlights 2026.1.2; PDFKit-backed `PDFView`

### Summary

After PDFKit analyzes a PDF page and identifies a visual table, ordinary drags over text inside its cells may stop returning text selections. In a PDFView probe, the drag returned a whole-cell `PDFSelection` marked `isTableCellSelection` with infinite bounds and no useful line rectangles, or it returned `nil`. The same issue can affect the public `PDFPage.selection(from:to:)` API. Apps that treat the returned selection as text can save annotations with zero `/QuadPoints`, which are invisible.

### Steps to reproduce

1. Open a PDF containing a normal text table with multiple rows and columns in Preview, or load it into a `PDFView` on macOS 26.5.
2. Wait several seconds for the page to finish appearing and for background document analysis to run.
3. Drag across a word or phrase inside a table cell, then try selecting the full cell's text.
4. Repeat on nearby prose outside the table.
5. In a PDFKit test app, inspect the selection returned for the drag, including `isTableCellSelection`, `bounds(for:)`, `selectionsByLine()`, and the result of `PDFPage.selection(from:to:)`.
6. If testing in an annotation app, save a highlight and inspect its `/QuadPoints` to see whether they contain non-zero geometry.

### Expected behavior

Dragging across text in a table cell selects the text under the pointer, including a phrase or wrapped passage. The selection has finite geometry, and an annotation made from it contains valid, non-zero quad points. The public page selection API should continue to return the text after page analysis.

### Actual behavior

Once analysis has run, drags in visually detected tables can return a whole-cell table selection with infinite bounds and no usable line rectangles, or no selection. In the probe, `PDFPage.selection(from:to:)` returned `nil` for 20 of 22 tested cells after analysis. Applications may then fail to highlight the text or save an invisible annotation with zero `/QuadPoints`. Prose outside the table remains selectable.

The failure can be timing-dependent: selection sometimes works before analysis completes and fails afterward. Restyling the grid does not appear to avoid detection. The issue reproduced across booktabs, full-grid, spaced, hairline, tagged Chrome, and CSS-grid presentations in the probe. A single-column row-record presentation retained ordinary text selection.

### Additional evidence

- Highlights 2026.1.2 on macOS 26.5 (25F71) showed the issue in an offscreen `PDFView` probe after allowing approximately eight seconds for analysis.
- With analysis enabled, 22 cell drags on the row-record PDF returned text selections and all 7 phrase drags selected text. Grid presentations commonly returned table-cell selections or nothing.
- Turning off the private `documentAnalysisEnabled` switch in the probe restored ordinary text selection for all 22 cells. This is diagnostic evidence only; it is a private API and should not be treated as an app workaround.
- The public `PDFPage.selection(from:to:)` API returned `nil` for 20 of 22 table cells after analysis, so this is not limited to the `PDFView` interaction path.
- Similar reports appear in Apple Community discussions [256257514](https://discussions.apple.com/thread/256257514) and [256139925](https://discussions.apple.com/thread/256139925).

### Request

Please provide a supported public way for an app or user to disable table-cell takeover/document analysis for text selection, or change PDFKit so that ordinary text selection remains available inside detected tables. If table-cell selection remains available, it should expose finite selection geometry and a reliable text range so apps can create valid annotations. At minimum, the public text-selection API should not return `nil` for ordinary text merely because the page analysis classified its containing region as a table.

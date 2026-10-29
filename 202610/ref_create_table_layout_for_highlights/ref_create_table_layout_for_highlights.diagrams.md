# Diagram proposals: Tables in `bob ref create` PDFs vs. Highlights annotation: consolidated recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/ref_create_table_layout_for_highlights/ref_create_table_layout_for_highlights__final.md
producer: research.2u.image
check: "Mermaid CLI 12.0.0 (npx pinned, Puppeteer --no-sandbox) with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## pdfkit-selection-takeover

```yaml
anchor: |-
  **The failure is time-dependent.** Analysis runs asynchronously per page.
question: |-
  Why can table highlighting work initially and fail later?
illustrates: |-
  Asynchronous per-page analysis changes grid drags into a whole-cell selection with no geometry or nothing, while row records keep normal selection in the Mac probe.
caption: Background analysis can turn working grid drags into selections without geometry; row records retained normal selection in the Mac probe.
review: "772.3x764 px, fit 84.5%; question, source trace, labels, arrowheads, crossings, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Why can table highlighting work, then fail?"
accTitle: "Asynchronous PDFKit analysis changes table selection"
accDescr: "Before analysis, text drags can work. Background PDFKit analysis detects grids, after which a drag can return a geometry-less cell selection or nothing. Highlights has saved the geometry-less selections as invisible annotations. Row records retained ordinary selection in the Mac probe."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 14
    wrappingWidth: 220
---
flowchart TD
  BEFORE["`**Before analysis**<br/>Text drags can work`"]
  DETECT{{"`**Visual grid detected?**`"}}
  CELL["`**Whole-cell selection**<br/>No usable geometry`"]
  NONE["`**No selection**<br/>Nothing to highlight`"]
  GHOST["`**Invisible annotation**<br/>Saved with zero QuadPoints`"]
  RECORD["`**Row records**<br/>22/22 cells selectable in probe`"]
  BEFORE -->|"PDFKit analyzes page<br/>asynchronously"| DETECT
  DETECT -->|"Yes: cell selection"| CELL
  DETECT -->|"Yes: returns nothing"| NONE
  DETECT -->|"No: record layout"| RECORD
  CELL -->|"Highlights saves"| GHOST
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  class BEFORE,RECORD focus
  class DETECT decision
  class CELL,NONE,GHOST risk
```

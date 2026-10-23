# Diagram proposals: `bob ref scan` vs. PDFs open in Highlights: save first, reload in place

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/highlights_open_pdf_coordinated_marker_writes/highlights_open_pdf_coordinated_marker_writes__final.md
producer: research.56.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## coordinated-v2-scope

```yaml
anchor: |-
  The accessor wraps that PDF's existing write sequence.
question: |-
  How can a hold leave the reading task untouched when v2 writes it before the marker?
illustrates: |-
  Entering coordination before the first per-PDF write encloses v2's reading task and routed intents, marker, assets, and note in the accessor, so a pre-accessor cancellation writes nothing for that PDF.
caption: For PDFs needing marker updates, coordination protects the whole v2 sync sequence; cancellation before access leaves even the reading task untouched.
review: "633.688×895 px, fit 99.8%; question, source, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: coordination protects every v2 write"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 18
    wrappingWidth: 240
---
flowchart TD
  ACCESS{{"`**Coordination grants access?**`"}}
  HOLD["`**Hold this PDF**<br/>No writes; retry next scan`"]
  subgraph PROTECTED["Coordinated accessor — existing v2 order"]
    TASK["`**Reading task**<br/>And routed intents`"]
    MARKER["`**PDF marker**<br/>Write after task`"]
    ASSETS["`**Assets**<br/>Write after marker`"]
    NOTE["`**Note**<br/>Write last`"]
    TASK -.->|then| MARKER
    MARKER -.->|then| ASSETS
    ASSETS -.->|then| NOTE
  end
  ACCESS -.->|"Cancelled before accessor starts"| HOLD
  ACCESS -.->|"Granted: begin writes"| PROTECTED
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class ACCESS decision
  class HOLD muted
  class TASK,MARKER,ASSETS,NOTE focus
  class ACCESS,HOLD,TASK,MARKER,ASSETS,NOTE proposed
  style PROTECTED fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

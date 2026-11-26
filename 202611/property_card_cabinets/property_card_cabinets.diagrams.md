# Diagram proposals: Property Card Cabinets

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/property_card_cabinets/property_card_cabinets__final.md
producer: research.6m.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox; malformed-source rejection verified"
```

## live-preview-source-visibility

```yaml
anchor: |-
  selection moves **strictly inside** the region
question: |-
  When does Live Preview reveal a catalog's stored Markdown?
illustrates: |-
  Live Preview keeps a valid original catalog visible without a working cabinet representation, and reveals raw Markdown on selection strictly inside rather than boundary contact.
caption: "A working cabinet can hide catalog source; invalid ownership or selection strictly inside reveals it, while boundary contact alone does not."
review: "639.714×658 px, fit 100.0%; reader question answered from PNG; labels, branches, arrowheads and source trace checked; 0 revisions"
```

```mermaid
---
title: "Proposed: when does Live Preview reveal catalog source?"
accTitle: "Catalog source visibility in Live Preview"
accDescr: "Without a working cabinet and valid ownership, keep source visible. With both, reveal raw Markdown only when selection moves strictly inside the catalog, not when it touches the boundary."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  OWN{{"`**Working cabinet + valid claim?**`"}}
  RAW["`**Stored source visible**<br/>Fail open`"]
  INSIDE{{"`**Selection strictly inside?**`"}}
  REVEAL["`**Reveal raw Markdown**<br/>Selection enters the region`"]
  HIDE["`**Owned callout hidden**<br/>Working cabinet stays visible`"]
  OWN -.->|No| RAW
  OWN -.->|Yes| INSIDE
  INSIDE -.->|Yes| REVEAL
  INSIDE -.->|"No, including boundary contact"| HIDE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class OWN,INSIDE decision
  class RAW,REVEAL focus
  class HIDE outcome
```

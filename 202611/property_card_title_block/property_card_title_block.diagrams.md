# Diagram proposals: Property cards as the note's title block: consolidated design and recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/property_card_title_block/property_card_title_block__final.md
producer: research.5i.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; broken-input rejection verified"
```

## title-ownership

```yaml
anchor: |-
  embeds, popovers, Source mode, and mobile keep native rendering.
question: |-
  How does title ownership hide duplication without preventing editing or native fallback?
illustrates: |-
  The proposed title-ownership lifecycle reveals raw Markdown on selection-touch in Live Preview and restores native rendering through either loss-of-ownership path.
caption: Any loss of title ownership restores native rendering; selection-touch in Live Preview reveals raw Markdown for editing.
review: "496.654x566 px, fit 100.0%; question, label, arrow, source-trace and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed title ownership: hide, reveal, restore"
accTitle: "Title ownership and editing fallback"
accDescr: "An eligible card owns the title. In Live Preview, selection touching the hidden heading reveals Markdown for editing. Losing ownership restores native rendering."
config:
  flowchart:
    rankSpacing: 28
    nodeSpacing: 24
    wrappingWidth: 200
---
flowchart TD
  N["`**Native rendering**<br/>Inline title, H1, Properties`"]
  O["`**Card owns title**<br/>Recognized source heading hidden`"]
  E["`**Editing reveal**<br/>Raw Markdown visible`"]
  N -.->|"Eligible card owns title"| O
  O -.->|"Selection touches<br/>(Live Preview)"| E
  E -.->|"Selection no longer touches"| O
  O -.->|"Ownership lost"| N
  E -.->|"Ownership lost"| N
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class N muted
  class O focus
  class E outcome
  class N,O,E proposed
```

## title-slot

```yaml
anchor: |-
  the record sheet mounts in the note body, **below** native Properties, and Bryan
question: |-
  What changes in page order if the title-slot spike succeeds, and what happens if it fails?
illustrates: |-
  The proposed title slot places the property card above native Properties only when reliable, while body placement remains the fallback.
caption: A reliable title slot puts the card above native Properties; failure keeps the existing body placement.
review: "567.094x361 px, fit 100.0%; question, label, arrow, source-trace and visual checks passed; 1 revision to put today on the left"
```

```mermaid
---
title: "Where will the card title sit?"
accTitle: "Current and conditional proposed card placement"
accDescr: "Native Properties currently sit above the card. A reliable title-slot spike moves the card above Properties. If the spike fails, the current body placement remains."
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 26
    wrappingWidth: 180
---
flowchart TB
  subgraph PROPOSAL["Proposed / if spike passes"]
    direction TB
    PC["`**Property card**<br/>Title in the header slot`"]
    PP["`**Native Properties**`"]
    PC -.->|"above"| PP
  end
  subgraph TODAY["Today / fallback if spike fails"]
    direction TB
    TP["`**Native Properties**`"]
    TC["`**Property card**<br/>Title in the note body`"]
    TP -->|"above"| TC
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class TC,PC focus
  class TP,PP muted
  class PC,PP proposed
  style TODAY fill:none,stroke:#6B7280
  style PROPOSAL fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

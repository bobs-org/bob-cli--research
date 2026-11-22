# Diagram proposals: Task requirements display redesign: one diamond, every depth

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/task_reqs_display_redesign/task_reqs_display_redesign__final.md
producer: research.5u.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 1 of 1 Mermaid diagrams"
```

## mac-editor-geometry

```yaml
anchor: |-
  The overlay is a `ZStack` sibling *outside* the editor's internal scroll view
question: |-
  Why does native Mac editor styling avoid the overlay's wrap and scroll failures?
illustrates: |-
  The proposed native AttributedString chip deletes the overlay and concealment, avoiding wrap drift and scroll desync from two mismatched rendering geometries.
caption: Native styling keeps requirement bytes in the editor, eliminating the separate wrapping and scrolling geometry that can misplace today's overlay.
review: "608.141x994 px, fit 89.8%; question, visual, source-trace, and unique-anchor checks passed; 1 layout revision across 2 visual review rounds; today's convergence means both geometries differ"
```

```mermaid
---
title: "Why replace the Mac editor overlay?"
accTitle: "Mac requirement rendering, today versus proposed"
accDescr: "Today, requirement text is inside the editor scroll view while a sibling overlay uses separate wrapping and scrolling geometry. Proposed native styling keeps visible requirement bytes in the editor and removes that overlay."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 200
---
flowchart TB
  subgraph TODAY["Today: two rendering geometries"]
    direction TB
    subgraph SCROLL1["Editor scroll view"]
      BYTES1["`**Requirement bytes**<br/>Hidden; word-wrapped`"]
    end
    OVERLAY["`**Sibling glyph overlay**<br/>Character-wrap; outside scroll view`"]
    DRIFT["`**Placement errors**<br/>Wrap drift; scroll desync`"]
    BYTES1 -->|"both geometries differ"| DRIFT
    OVERLAY -->|"both geometries differ"| DRIFT
  end
  subgraph PROPOSAL["Proposed: native styling"]
    direction TB
    subgraph SCROLL2["Editor scroll view"]
      BYTES2["`**Requirement bytes**<br/>Visible; native background wash`"]
    end
    ALIGNED["`**Placement stays aligned**<br/>Separate overlay removed`"]
    BYTES2 -.->|"eliminates geometry mismatch"| ALIGNED
  end
  TODAY ~~~ PROPOSAL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class BYTES1,OVERLAY focus
  class DRIFT risk
  class BYTES2,ALIGNED outcome
  class BYTES2 proposed
  class ALIGNED proposed
  style TODAY fill:none,stroke:#3B78C2
  style SCROLL1 fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
  style SCROLL2 fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

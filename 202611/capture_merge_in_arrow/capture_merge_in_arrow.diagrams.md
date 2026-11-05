# Diagram proposals: Capture `<`: merge existing tasks into the task you are creating

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/capture_merge_in_arrow/capture_merge_in_arrow__final.md
producer: research.3f.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; pinned CLI with Puppeteer no-sandbox flag"
```

## dependency-directions

```yaml
anchor: |-
  A source's prerequisites are *not* inherited. They stay on the
question: |-
  Which dependencies follow the new task, and which stay on the cancelled source?
illustrates: |-
  Open dependents re-point to T while source prerequisites stay on the tombstone, so the new task inherits none of them.
caption: "Dependents follow the new task; the cancelled source keeps its prerequisites, which the new task does not inherit."
review: "773.491x577 px, fit 84.4%; question, source-trace, labels, arrowheads, reading order, and visual checks passed; 1 revision across 2 look rounds"
```

This illustrative case has one open dependent and one source prerequisite. Arrows show
labelled task relations, not execution order. Both incoming relations to the new task
coexist; dashed edges and outlines mark the proposed result.

```mermaid
---
title: "Proposed merge: what happens to dependencies?"
accTitle: "Dependencies before and after a proposed task merge"
accDescr: "An illustrative source has one dependent and one prerequisite. After merging, the dependent waits on the new task. The cancelled source retains its prerequisite and records a merged-into relation to the new task. The new task inherits no prerequisite."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 125
---
flowchart LR
  subgraph BEFORE["Before: example"]
    direction TB
    D1["`**Open dependent**<br/>Waits on source`"]
    S1["`**Source**<br/>Still open`"]
    P1["`**Prerequisite**<br/>Required by source`"]
    D1 -->|depends on| S1
    S1 -->|depends on| P1
  end
  subgraph AFTER["After: proposed merge"]
    direction TB
    D2["`**Open dependent**<br/>Waits on new task`"]
    S2["`**Source**<br/>Cancelled`"]
    T["`**New task**<br/>Own prerequisites only`"]
    P2["`**Prerequisite**<br/>Required by source`"]
    D2 -.->|depends on| T
    S2 -.->|merged into| T
    S2 -.->|still depends on| P2
  end
  BEFORE ~~~ AFTER
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class D1,S1,D2 focus
  class T outcome
  class P1,S2,P2 muted
  class D2,S2,T,P2 proposed
  style BEFORE fill:none,stroke:#3B78C2
  style AFTER fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

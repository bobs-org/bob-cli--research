# Diagram proposals: Cmd+Y as a keyed Copy card

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/cmd_y_copy_card/cmd_y_copy_card__final.md
producer: research.48.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## snapshot-preserves-preview

```yaml
anchor: |-
  Freeze everything into an immutable model. A key or `↵` copies that model's string
question: |-
  If the active file changes, what gets copied?
illustrates: |-
  Freezing everything into an immutable model keeps the preview and copied value
  together, even when the active file switches from A to B before activation.
caption: >-
  If the active file changes from A to B after opening, today's copy can drift; the proposed snapshot keeps preview and clipboard on A.
review: "860x421 px, fit 75.9%; question, source, and visual checks passed; 1 revision across 2 look rounds; unique anchor; broken-source probe returned nonzero"
```

```mermaid
---
title: "If the active file changes, what gets copied?"
accTitle: "Current reads versus proposed frozen Copy card"
accDescr: "Example: the active file changes from A to B after opening the card. Today the preview reads A but copy reads B. The proposal supplies both preview and clipboard from frozen model A. Arrows mean supplies the value."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 120
    padding: 10
---
flowchart TD
  subgraph PROPOSAL["Proposed: one frozen model"]
    P_MODEL["`**Frozen model**<br/>A at open`"]
    P_PREVIEW["`**Preview**<br/>A`"]
    P_CLIP["`**Clipboard**<br/>A`"]
    P_MODEL -.->|supplies| P_PREVIEW
    P_MODEL -.->|supplies| P_CLIP
  end
  subgraph TODAY["Today: two live reads"]
    T_OPEN["`**Active file**<br/>A at open`"]
    T_LATE["`**Active file**<br/>B at activation`"]
    T_PREVIEW["`**Preview**<br/>A`"]
    T_CLIP["`**Clipboard**<br/>B`"]
    T_OPEN -->|supplies| T_PREVIEW
    T_LATE -->|supplies| T_CLIP
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class T_OPEN,T_LATE,T_PREVIEW,P_MODEL,P_PREVIEW focus
  class T_CLIP risk
  class P_CLIP outcome
  class P_MODEL,P_PREVIEW,P_CLIP proposed
  style TODAY fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

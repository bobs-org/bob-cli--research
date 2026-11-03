# Diagram proposals: Move bullets: bringing parent tasks into a new project note at capture time

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/parent_task_move_bullets/parent_task_move_bullets__final.md
producer: research.35.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox"
```

## interrupted-move-copies

```yaml
anchor: |-
  process death between renames then leaves a duplicate, not a loss.
question: |-
  If the process dies between writes, where is the moved task?
illustrates: |-
  Replacing the parent last leaves a duplicate rather than a loss if a process dies between renames.
caption: Parent-last order leaves a duplicate instead of a loss if the process dies between the destination and parent renames.
review: "616x409 px, fit 100.0%; question, source-trace and PNG visual checks passed; 0 revisions; batch check passed; invalid-source control failed as expected"
```

```mermaid
---
title: "If a move is interrupted, where is the task?"
accTitle: "Task copies during interrupted project capture writes"
accDescr: "Reusing today's first-touch order can remove the task from the parent before the new note exists. The proposed parent-last order keeps both copies until the parent is replaced."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 28
    wrappingWidth: 200
---
flowchart TB
  subgraph CURRENT["Today's order, if reused"]
    C1["`**Parent replaced**<br/>Task removed; new note unwritten`"]
    C2["`**Task lost**<br/>Neither note holds it`"]
    C1 -->|"Process dies before<br/>new-note rename"| C2
  end
  subgraph PROPOSAL["Proposed: parent last"]
    P1["`**New note written**<br/>Parent still holds the task`"]
    P2["`**Duplicate remains**<br/>Both notes hold it`"]
    P1 -.->|"Process dies before<br/>parent rename"| P2
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class C1,P1 focus
  class C2 risk
  class P2 outcome
  class P1,P2 proposed
  style CURRENT fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

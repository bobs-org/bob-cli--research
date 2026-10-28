# Diagram proposals: Cancel labels: relation labels that cancel their source task

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/cancel_labels_for_task_relations/cancel_labels_for_task_relations__final.md
producer: research.2r.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; malformed-input check exited nonzero"
```

## transfer-cycle

```yaml
anchor: |-
  while `^intro-v1` depends on `^v1-draft`. Re-pointing would have
question: |-
  Why would transferring dependents create a cycle?
illustrates: |-
  Moving dependents onto the survivor would have created a cycle in the `^v1-draft` / `^intro-v1` case.
caption: "Transferring the full draft's prerequisite to its replacement would create a cycle; standard cancellation recovery avoids that transfer."
review: "729.047x505 px, fit 89.5%; reader question, arrow directions, labels, and source checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Why would transferring dependents create a cycle?"
accTitle: "An observed dependency chain and the rejected transfer"
accDescr: "The replacement introduction depends on the full draft, which depends on the old introduction. Moving the draft's prerequisite to the replacement would create a two-task cycle. Arrows mean depends on."
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 22
    wrappingWidth: 210
---
flowchart TD
  subgraph REJECTED["Rejected transfer: would create a cycle"]
    T2["`**Introduction v1**<br/>Replacement task`"]
    D2["`**Full v1 draft**<br/>Dependent task`"]
    T2 -->|"depends on"| D2
    D2 -.->|"would depend on"| T2
  end
  subgraph EXISTING["Observed dependencies before cancellation"]
    T1["`**Introduction v1**<br/>Replacement task`"]
    D1["`**Full v1 draft**<br/>Dependent task`"]
    S1["`**Write introduction**<br/>Source to cancel`"]
    T1 -->|"depends on"| D1
    D1 -->|"depends on"| S1
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class T1,D1 focus
  class S1 muted
  class T2,D2 risk
  style EXISTING fill:none,stroke:#3B78C2
  style REJECTED fill:none,stroke:#C0392B
```

## cancel-ownership

```yaml
anchor: |-
  Keep the JS planner and do not route Obsidian through `bob capture`:
question: |-
  Who plans cancellation, who writes it, and who only renders it?
illustrates: |-
  bob owns capture while Obsidian keeps its JS planner and local editor writes, with shared CX vectors keeping both engines' cancel bytes identical.
caption: "bob owns Mac capture; Obsidian keeps its local editor writer, and shared CX vectors test both cancellation engines against identical bytes."
review: "423.523x1125.69 px, fit 79.3%; reader question, ownership, data arrows, shared-test line, labels, and source checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: who owns each cancel write?"
accTitle: "Cancel planning across Mac, bob-cli, and Obsidian"
accDescr: "Mac submits drafts and renders bob's consequences. Rust plans capture and stages disk writes. Obsidian keeps a JavaScript planner and local editor write. Both planners are tested against shared CX expected bytes. Arrows carry runtime data; the line without arrows is the shared test contract."
config:
  flowchart:
    rankSpacing: 8
    nodeSpacing: 12
    wrappingWidth: 260
---
flowchart TB
  subgraph MAC["Mac Capture · Swift"]
    APP["`**Thin client**<br/>Submit drafts; render results`"]
  end
  subgraph BOB["bob-cli · Rust"]
    RUST["`**Capture cancel plan**<br/>New task_cancel engine`"]
    DISK["`**Capture batch**<br/>Guarded staged writes`"]
    RUST -.->|"planned note content"| DISK
  end
  subgraph NAV["Obsidian nav · JavaScript"]
    JS["`**Local cancel plan**<br/>Compose relation and cancel`"]
    EDITOR["`**Source editor write**<br/>LINKS + status together`"]
    JS -.->|"source content"| EDITOR
  end
  APP -.->|"capture draft"| RUST
  RUST -.->|"effect fields"| APP
  RUST -.-|"Shared CX tests:<br/>identical cancel bytes"| JS
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class RUST,JS focus
  class DISK,EDITOR outcome
  class APP muted
  class APP,RUST,DISK,JS,EDITOR proposed
  style MAC fill:none,stroke:#6B7280
  style BOB fill:none,stroke:#3B78C2
  style NAV fill:none,stroke:#3B78C2
```

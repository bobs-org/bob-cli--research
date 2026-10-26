# Diagram proposals: A `:` bob command mode inside Obsidian

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/bob_colon_command_mode/bob_colon_command_mode__final.md
producer: research.5c.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## reload-safety

```yaml
anchor: |-
  This removes the EPIPE half-run (F5), and logs survive a reload.
question: |-
  Why does file-backed output matter when Obsidian reloads?
illustrates: |-
  File-backed output removes the EPIPE half-run and preserves logs across reloads, while unfinished records become outcome unknown and are never replayed automatically.
caption: "After reload, pipes can stop bob silently; proposed file-backed output preserves logs, marks unfinished records unknown, and never replays them automatically."
review: "612.5×697 px, fit 100.0%; question and visual checks passed in two look rounds; two revisions (layout and automatic-only replay wording); broken-syntax probe rejected"
```

```mermaid
---
title: "Why write bob output to files?"
accTitle: "Why does file-backed output matter when Obsidian reloads?"
accDescr: "Piped output can close during reload, causing the next print to unwind bob with a silent exit zero. The proposed detached file-backed run preserves output and marks an unfinished record unknown without replaying it."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 170
---
flowchart LR
  subgraph PIPES["Piped output: reload risk"]
    direction TB
    P0["`**Obsidian reloads**<br/>Piped bob run`"]
    P1["`**Output pipe**<br/>Reader disconnects`"]
    P2["`**Broken pipe (EPIPE)**<br/>Whole command unwinds`"]
    P3["`**Partial run**<br/>Silent exit 0`"]
    P0 -->|closes| P1
    P1 -->|next print| P2
    P2 -->|exits| P3
  end
  subgraph FILES["Proposed: detached run, files"]
    direction TB
    F0["`**Obsidian reloads**<br/>File-backed bob run`"]
    F1["`**Log survives reload**<br/>No EPIPE half-run`"]
    F2["`**Unfinished record**<br/>Unknown; no auto-replay`"]
    F0 -.->|preserves| F1
    F0 -.->|marks record| F2
    F1 ~~~ F2
  end
  PIPES ~~~ FILES
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class P0,P1,P2,P3 risk
  class F0,F2 focus
  class F1 outcome
  class F0,F1,F2 proposed
  style PIPES fill:none,stroke:#C0392B
  style FILES fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

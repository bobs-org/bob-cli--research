# Diagram proposals: `bob bank import -D|--delete`: consolidated design for success-gated source cleanup

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_import_delete_flag/bank_import_delete_flag__final.md
producer: research.5j.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; SVG and PNG reviewed; invalid input rejected"
```

## mid-import-arrival

```yaml
anchor: |-
  and the re-expanded `rm` glob can delete a file
question: |-
  Which files can cleanup remove if another matching export arrives during import?
illustrates: |-
  The re-expanded `rm` glob can delete a file that arrived mid-import, while the new flag deletes exactly the files it parsed.
caption: A second shell glob can delete a mid-import arrival; proposed cleanup targets only unchanged prepared sources.
review: "656x673 px, fit 99.5%; question, source trace, labels, arrowheads, reading direction and PNG visual checks passed; 1 revision"
```

```mermaid
---
title: "How does cleanup handle a mid-import arrival?"
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 24
    wrappingWidth: 220
---
flowchart TD
  subgraph PROPOSAL["Proposed: bob bank import -D"]
    direction TB
    P1["`**Import**<br/>Bob expands once`"]
    P2["`**Matching export**<br/>Arrives during import`"]
    P3["`**Cleanup**<br/>Unchanged prepared files only`"]
    P4["`**New download**<br/>Stays untouched`"]
    P1 -.->|while importing| P2
    P2 -.->|after import succeeds| P3
    P3 -.->|excludes the arrival| P4
  end
  subgraph TODAY["Today: shell import then rm"]
    direction TB
    T1["`**Import**<br/>First glob's files`"]
    T2["`**Matching export**<br/>Arrives during import`"]
    T3["`**rm**<br/>Glob expands again`"]
    T4["`**Deletion**<br/>Includes unimported arrival`"]
    T1 -->|while importing| T2
    T2 -->|after import succeeds| T3
    T3 -->|selects for deletion| T4
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class T1,T2,T3,P1,P2 focus
  class T4 risk
  class P3,P4 outcome
  class P1,P2,P3,P4 proposed
  style TODAY fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

## preview-apply-drift

```yaml
anchor: |-
  The glob re-expands at apply; a file arriving between
question: |-
  Can Apply include an export that was absent from preview?
illustrates: |-
  The glob re-expands at apply, so a file arriving between Enter and Ctrl+Enter can be imported and deleted without having been previewed.
caption: Successful Apply may record and delete an export that arrived after preview; it re-expands the pattern.
review: "515x754 px, fit 100.0%; question, source trace, labels, arrowheads, reading direction and PNG visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: preview can drift"
config:
  sequence:
    actorMargin: 35
    diagramMarginX: 12
    messageMargin: 18
    noteMargin: 8
    width: 140
    mirrorActors: false
    wrap: true
---
sequenceDiagram
  autonumber
  participant CM as Command Mode
  participant BOB as bob
  participant FILES as Downloads
  CM->>BOB: Enter: preview the pattern
  BOB->>FILES: Expand and read
  FILES-->>BOB: Current source files
  BOB-->>CM: Diffs and would-delete list
  Note over FILES: A new export<br/>may arrive
  CM->>BOB: Ctrl+Enter: apply the pattern
  BOB->>FILES: Re-expand and read
  FILES-->>BOB: Current files, including arrival
  BOB->>BOB: Parse, plan,<br/>verify, commit
  BOB->>FILES: Delete eligible prepared files
```

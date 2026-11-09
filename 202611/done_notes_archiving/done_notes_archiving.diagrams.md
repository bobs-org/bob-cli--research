# Diagram proposals: Done notes: keep `done/<stem>_done.md`, fix the rule that feeds it

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/done_notes_archiving/done_notes_archiving__final.md
producer: research.3w.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; PNGs visually reviewed; Puppeteer --no-sandbox"
```

## archive-rename-history

```yaml
anchor: |-
  When a source has been renamed, rename its archive to the canonical name
question: |-
  How does archive history change after a source rename?
illustrates: |-
  With resolving and agreeing metadata links, the proposed pairing resolver finds and renames the existing archive in the same transaction, preventing the split history caused by filename pairing.
caption: "After a source rename, filename pairing splits history; the proposed resolver finds and renames the existing archive in one transaction."
review: "737.453x577 px, fit 88.5%; reader question, source trace, labels, arrowheads and visual checks passed; 0 revisions"
```

```mermaid
---
title: "What happens to history after a source rename?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 170
---
flowchart TB
  subgraph TODAY["Today: filename pairing"]
    direction TB
    S1["`**Source note**<br/>Renamed`"]
    A1["`**Original archive**<br/>Orphaned history`"]
    B1["`**Second archive**<br/>History splits`"]
    S1 -->|"next run creates;<br/>repoints done_tasks"| B1
  end
  subgraph PROPOSAL["Proposed: metadata links agree"]
    direction TB
    S2["`**Source note**<br/>Renamed`"]
    A2["`**Original archive**<br/>Existing history`"]
    B2["`**Renamed archive**<br/>Same file, canonical name`"]
    S2 -.->|"metadata pairing<br/>finds archive"| A2
    A2 -.->|"transaction renames;<br/>repairs inbound links"| B2
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class S1,S2,A2 focus
  class A1,B1 risk
  class B2 outcome
  class S2,A2,B2 proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

## restore-versus-reopen

```yaml
anchor: |-
  Restore moves the whole block, reverses the link repair, and keeps the
question: |-
  How does restoring an archived task differ from reopening it in place?
illustrates: |-
  For supported tasks, proposed restore returns the whole block to its bound source and optionally reopens it, respecting blockers and lanes, while reopening inside done/ leaves a task invisible.
caption: "For supported tasks, proposed restore returns the block to its bound source; reopening in done/ today leaves it invisible."
review: "758x445 px, fit 86.1%; reader question, source trace, labels, arrowheads and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why restore instead of reopening inside done/?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 170
---
flowchart TB
  subgraph TODAY["Today: reopen inside done/"]
    direction TB
    A1["`**Archived task**<br/>Closed`"]
    B1["`**Archived task**<br/>Open, invisible to lanes`"]
    A1 -->|"reopen in place"| B1
  end
  subgraph PROPOSAL["Proposed: restore supported tasks"]
    direction TB
    A2["`**Archived task**<br/>Closed`"]
    B2["`**Source task**<br/>Still closed`"]
    C2["`**Source task**<br/>Reopened; blockers and lanes apply`"]
    A2 -.->|"restore whole block"| B2
    A2 -.->|"restore whole block;<br/>optionally reopen"| C2
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class A1,A2 focus
  class B1 risk
  class B2,C2 outcome
  class A2,B2,C2 proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

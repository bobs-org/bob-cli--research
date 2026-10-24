# Diagram proposals: Relation card: completion that works, hidden labels, and global rename

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/relation_card_label_vocabulary/relation_card_label_vocabulary__final.md
producer: research.2e.image
check: "mmdc 12.0.0 (pinned npx; Puppeteer --no-sandbox) with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## selection-by-key

```yaml
anchor: |-
  Typing clears the selection and refreshes.
question: |-
  When do navigation, typing, and refreshed results preserve or clear selection?
illustrates: |-
  In the proposed card, navigation changes only the selected key and sentence pill, typing clears selection, and a refresh preserves the selected key unless it disappears.
caption: Navigation leaves the query unchanged; typing clears selection; reordered results retain the same key, while missing keys clear it.
review: "751.422×326 px, fit 86.9%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: when does selection stay or clear?"
accTitle: "Proposed relation chooser selection lifecycle"
accDescr: "Navigation changes selection without editing the query. Typing clears selection. Reordered results preserve the selected key, but results that drop it clear selection."
---
stateDiagram-v2
  direction TB
  state "Field<br/>No selection" as FIELD
  state "List<br/>Selection by key" as SELECTED
  FIELD --> SELECTED: Ctrl+N/P: first / last
  SELECTED --> SELECTED: Navigate: move highlight
  SELECTED --> SELECTED: Reorder: keep key
  SELECTED --> FIELD: Type: clear + refresh
  SELECTED --> FIELD: Key disappears: clear
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class FIELD focus
  class SELECTED outcome
  class FIELD proposed
  class SELECTED proposed
```

## rename-failure-boundaries

```yaml
anchor: |-
  Snapshot every target and compare right before writing
question: |-
  When do coverage, snapshot, verification, and sync failures stop or preserve a global rename?
illustrates: |-
  The proposed rename refuses incomplete coverage and stale notes, restores before-images after failed verification, and reports renamed locally separately from sync pending.
caption: Coverage or snapshot failures refuse before writing; failed verification restores files; failed post-sync preserves the local rename.
review: "664.484×914 px, fit 97.7%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: rename failure boundaries"
accTitle: "Proposed relation-label rename failure boundaries"
accDescr: "Incomplete planning and changed notes refuse before writes. Verification failure restores before-images. A committed rename remains local when post-sync fails."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 260
---
flowchart TD
  SAFE{{"`**Safe to write?**`"}}
  REFUSE["`**Refuse before writing**<br/>Incomplete coverage or stale note`"]
  WRITE["`**Write atomically**<br/>Then append rename event`"]
  CHECK{{"`**Rescan passes?**`"}}
  RESTORE["`**Restore**<br/>Before-images`"]
  COMMIT["`**Commit locally**<br/>Then post-sync`"]
  PENDING["`**Sync pending**<br/>Local rename kept`"]
  SAFE -.->|No| REFUSE
  SAFE -.->|Yes| WRITE
  WRITE -.->|verify labels and counts| CHECK
  CHECK -.->|No| RESTORE
  CHECK -.->|Yes| COMMIT
  COMMIT -.->|post-sync fails| PENDING
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class WRITE,COMMIT focus
  class SAFE,CHECK decision
  class REFUSE,RESTORE,PENDING risk
  class WRITE,COMMIT,SAFE,CHECK,REFUSE,RESTORE,PENDING proposed
```

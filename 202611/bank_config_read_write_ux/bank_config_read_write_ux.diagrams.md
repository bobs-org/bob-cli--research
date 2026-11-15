# Diagram proposals: Make bank.md’s bank mapping readable and writable from Obsidian

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_config_read_write_ux/bank_config_read_write_ux__final.md
producer: research.4r.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; selected CLI retained Puppeteer --no-sandbox; malformed-diagram control exited nonzero"
```

## apply-recovery

```yaml
anchor: |-
  shared vault lock, flushes open `bank.md` editors, re-checks the `expect`
question: |-
  How does applying an edit handle stale previews and sync failure?
illustrates: |-
  The proposed writer re-checks the expect fingerprint before one scoped commit, while a post-apply sync failure keeps the local save and offers sync-only Retry.
caption: A stale fingerprint stops the write; a sync failure leaves the commit saved and retries only synchronization.
review: "551.359x938 px, fit 95.2%; question, source trace and visual checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed apply: conflict or sync failure?"
accTitle: "Stale previews stop writes; sync failures retry only sync"
accDescr: "Control-flow arrows distinguish a fingerprint conflict before the scoped commit from a synchronization failure after the commit."
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  APPLY["`**Apply requested**<br/>Lock vault; flush editors`"]
  MATCH{{"`**Fingerprint still matches?**`"}}
  STALE["`**Stale preview**<br/>Preserve draft; explicitly re-preview`"]
  SAVE["`**Preserve authored style**<br/>One scoped commit`"]
  SYNC{{"`**Sync succeeds?**`"}}
  DONE["`**Saved**<br/>Sync complete`"]
  RETRY["`**Saved locally**<br/>Retry sync only`"]
  APPLY -.->|"re-check"| MATCH
  MATCH -.->|"No: conflict"| STALE
  MATCH -.->|"Yes: write"| SAVE
  SAVE -.->|"then sync"| SYNC
  SYNC -.->|"Yes"| DONE
  SYNC -.->|"No: sync failed"| RETRY
  RETRY -.->|"retry sync"| SYNC
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class APPLY,SAVE,DONE focus
  class MATCH,SYNC decision
  class STALE,RETRY risk
  class APPLY,MATCH,STALE,SAVE,SYNC,DONE,RETRY proposed
```

## add-then-file

```yaml
anchor: |-
  card from the writer's returned categories, then files the row through the card's
question: |-
  When does creating a category file the waiting transaction row?
illustrates: |-
  The proposed Category card applies one bank.md config commit before filing the row through its existing single editor transaction, while failed applies file nothing.
caption: Category creation commits configuration before filing the row in a separate editor transaction; a failed apply leaves the row unfiled.
review: "614x956 px, fit 93.4%; question, source trace and visual checks passed; 1 visual revision to prevent title clipping and reduce height"
```

```mermaid
---
title: "Proposed: commit, then file"
accTitle: "Creating a category commits the configuration before filing the row"
accDescr: "A dry-run supplies the stored key and hotkey. Enter applies configuration first. A successful apply repaints and files the row in a separate editor transaction; a failed apply files nothing."
config:
  sequence:
    actorMargin: 24
    width: 130
    diagramMarginX: 10
    diagramMarginY: 10
    messageMargin: 16
    mirrorActors: false
    noteMargin: 8
    wrap: true
---
sequenceDiagram
  autonumber
  participant USER as User
  participant CARD as Category card
  participant BOB as bob writer
  participant EDITOR as Month-note editor
  USER->>CARD: +: label, group, key
  CARD->>BOB: Settled draft: dry-run category.add
  BOB-->>CARD: Derived stored key and keycap
  USER->>CARD: Enter
  CARD->>BOB: Apply config op
  alt Apply succeeds
    BOB->>BOB: Scoped bank.md commit
    BOB-->>CARD: Return categories
    CARD->>CARD: Repaint
    CARD->>EDITOR: File row: single editor transaction
    CARD->>CARD: Advance
  else Apply fails
    BOB-->>CARD: Failure reason
    CARD-->>USER: Inline reason, nothing filed
  end
```

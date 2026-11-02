# Diagram proposals: Google Calendar descriptions as Event Task bullets: consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gcal_event_description_notes/gcal_event_description_notes__final.md
producer: research.5o.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## journal-carry-forward

```yaml
anchor: |-
  On the next run the row would look pre-feature and get its bullets
question: |-
  Why must every later row record carry the description state?
illustrates: |-
  A title or root update that omits description state replaces the folded row record and makes the next sync treat it as pre-feature, while required carry-forward keeps the block tracked.
caption: Every row update must retain description state; omitting it can make the next sync insert duplicate bullets.
review: "770x807 px, fit 84.8%; question, source tracing, arrow and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: carry description state"
accTitle: "Why every row update must carry description state"
accDescr: "A title or root update that omits description state replaces the last journal record, so the next sync treats the row as pre-feature and inserts duplicate bullets. Carrying state forward keeps the block tracked."
config:
  sequence:
    actorMargin: 18
    width: 126
    diagramMarginX: 12
    messageMargin: 24
    boxMargin: 8
    noteMargin: 10
---
sequenceDiagram
  autonumber
  participant UPDATE as Title or root update
  participant RECORD as Latest row record
  participant SYNC as Next sync
  participant TASK as Event Task
  alt Failure: description state omitted
    UPDATE->>RECORD: Write row without<br/>description state
    Note over RECORD: New record replaces<br/>prior state
    SYNC->>RECORD: Read description state
    RECORD-->>SYNC: Absent: treat as<br/>pre-feature
    SYNC->>TASK: Insert bullets again
  else Proposed: state carried forward
    UPDATE->>RECORD: Write row with<br/>description state
    SYNC->>RECORD: Read description state
    RECORD-->>SYNC: Retained hash<br/>and line count
    Note over SYNC,TASK: Existing block remains<br/>tracked
  end
```

## description-output-routes

```yaml
anchor: |-
  Render at most `description_lines` lines, the last of
question: |-
  When does sync write full bullets, an overflow link, a fallback link, or nothing?
illustrates: |-
  With description bullets enabled for Event Tasks, the 64 KiB input bound, empty filtered result, and configurable eight-line default choose different outputs at different stages.
caption: Oversized input yields one source link; empty content yields nothing; capped output includes an overflow link within the configured line limit.
review: "761.4x1008 px, fit 85.7%; question, source tracing, arrow and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when do bullets give way to a link?"
accTitle: "Description output bounds and empty results"
accDescr: "Input over 64 KiB yields a single source-link fallback. Otherwise filtered and sanitized content produces no children when empty, all lines within the configured cap, or a capped block including an overflow link."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 185
---
flowchart TD
  SIZE{{"`**Input above 64 KiB?**`"}}
  FALLBACK["`**Single fallback bullet**<br/>Link to Google Calendar`"]
  CONVERT["`**Convert description**<br/>Filter, outline, sanitize, guard`"]
  EMPTY{{"`**Any lines remain?**`"}}
  NOTHING["`**No child bullets**<br/>No header or placeholder`"]
  CAP{{"`**Above configured line cap?**`"}}
  ALL["`**Render all lines**<br/>Within configured cap`"]
  OVERFLOW["`**Capped block**<br/>Last line links to overflow`"]
  SIZE -.->|"Yes"| FALLBACK
  SIZE -.->|"No"| CONVERT
  CONVERT -.->|"Check converted result"| EMPTY
  EMPTY -.->|"No"| NOTHING
  EMPTY -.->|"Yes"| CAP
  CAP -.->|"No"| ALL
  CAP -.->|"Yes"| OVERFLOW
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class SIZE,EMPTY,CAP decision
  class CONVERT focus
  class FALLBACK,NOTHING,ALL,OVERFLOW outcome
```


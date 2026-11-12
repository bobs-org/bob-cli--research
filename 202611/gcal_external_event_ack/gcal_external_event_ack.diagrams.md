# Diagram proposals: Ack external Google Calendar events

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gcal_external_event_ack/gcal_external_event_ack__final.md
producer: research.4h.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; --no-sandbox; SVG and PNG visually reviewed"
```

## review-evidence

```yaml
anchor: |-
  Deleting travel instructions does not undo having reviewed the event
question: |-
  Does clearing a note or an explicit ack erase review?
illustrates: |-
  Historical nonempty note evidence survives clearing current text, while clearing the sole explicit ack returns an event with no other review evidence to unacked.
caption: "Historical nonempty notes preserve review after text is cleared; clearing the sole explicit ack reopens review only when no note evidence remains."
review: "453.185x758 px, fit 100.0%; question, source-trace and visual checks passed; 0 revisions; either incoming action suffices; scoped to one applicable event/series with no other evidence."
```

```mermaid
---
title: "Proposed: what survives clearing a review?"
---
stateDiagram-v2
  direction TB
  state "Unacked<br/>No review evidence" as UNREVIEWED
  state "Acked<br/>Explicit receipt only" as RECEIPT
  state "Acked<br/>Nonempty note present" as NOTED
  state "Acked<br/>Note cleared; history retained" as HISTORY
  UNREVIEWED --> RECEIPT: Ack event or series
  RECEIPT --> UNREVIEWED: Clear sole ack
  UNREVIEWED --> NOTED: Save nonempty note
  RECEIPT --> NOTED: Save nonempty note
  NOTED --> HISTORY: Clear note text
  HISTORY --> NOTED: Save nonempty note
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class UNREVIEWED risk
  class RECEIPT focus
  class NOTED,HISTORY outcome
  class UNREVIEWED,RECEIPT,NOTED,HISTORY proposed
```

## journal-reader-compatibility

```yaml
anchor: |-
  `gcal.ack` line is a per-line warning *and* a bogus freshness signal.
question: |-
  Why must ack-aware readers ship with ack writers?
illustrates: |-
  Older readers count gcal.ack as malformed and advance newest, while the proposed load_state skip prevents ack receipts from becoming occurrence state or a bogus last-sync signal.
caption: "Ship ack-aware readers with writers, upgrading the writer Mac first: older readers turn ack receipts into malformed warnings and bogus freshness."
review: "771.766x781 px, fit 84.6%; question, source-trace and visual checks passed; 1 revision; scoped to occurrence loading, with separate ack validation outside the figure."
```

```mermaid
---
title: "Why must ack readers ship with writers?"
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 12
    wrappingWidth: 160
---
flowchart TB
  subgraph NEW["Proposed ack-aware reader"]
    direction TB
    NR["`**gcal.ack**<br/>New receipt kind`"]
    NS["`**Skip the receipt**<br/>Newest unchanged`"]
    NR -.->|load_state| NS
  end
  subgraph OLD["Older reader"]
    direction TB
    OR["`**gcal.ack**<br/>New receipt kind`"]
    ON["`**Newest timestamp**<br/>Advanced before parse`"]
    OP["`**Parse failure**<br/>Unknown journal kind`"]
    OW["`**Warning**<br/>Counted as malformed`"]
    OF["`**Last-sync fallback**<br/>False freshness`"]
    OR -->|loads| ON
    ON -->|then parses| OP
    OP -->|counts as| OW
    ON -->|feeds| OF
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class OR,NR focus
  class ON,OP,OW,OF risk
  class NS outcome
  class NR,NS proposed
  style OLD fill:none,stroke:#C0392B
  style NEW fill:none,stroke:#2E7D4F
```

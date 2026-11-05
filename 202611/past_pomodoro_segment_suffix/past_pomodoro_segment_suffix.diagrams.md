# Diagram proposals: Placing a past Pomodoro on today's timeline: the `x=` segment suffix

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/past_pomodoro_segment_suffix/past_pomodoro_segment_suffix__final.md
producer: research.3e.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; SVG and PNG reviewed"
```

## guard-union

```yaml
anchor: |-
  item independently, with unsuffixed items still packing from `T`.
question: |-
  Why does one pin per run preserve the overlap guard?
illustrates: |-
  A run hanging from one pin remains one contiguous interval, so the unchanged continuous-union overlap guard does not trim minutes nobody named.
caption: Keeping each run contiguous lets the existing overlap guard cover exactly the recorded time, without trimming unnamed gaps.
review: "673.8×529 px, fit 96.9%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Why keep one pin per run?"
accTitle: "Proposed contiguous runs preserve the overlap guard"
accDescr: "Rejected independent inserts cause the continuous-union guard to include unnamed minutes. The proposed single pinned run is continuous, so its occupied interval agrees with that guard."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 240
---
flowchart TB
  subgraph REJECTED["Rejected: independent placement"]
    direction TB
    SEPARATE["`**Inserted windows**<br/>At 08:00 and 08:50`"]
    WIDE["`**Continuous-union guard**<br/>Uses 08:00–09:00`"]
    HARM["`**Unnamed minutes**<br/>Included in the trim`"]
    SEPARATE -->|guard reads| WIDE
    WIDE -->|therefore| HARM
  end
  subgraph PROPOSAL["Proposed: one pinned run"]
    direction TB
    CONTIGUOUS["`**Inserted windows**<br/>Continuous, in typed order`"]
    EXACT["`**Continuous-union guard**<br/>Matches the occupied interval`"]
    SAFE["`**Existing guard**<br/>Stays unchanged`"]
    CONTIGUOUS -.->|guard reads| EXACT
    EXACT -.->|therefore| SAFE
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class SEPARATE,WIDE,CONTIGUOUS,EXACT focus
  class HARM risk
  class SAFE outcome
  class CONTIGUOUS,EXACT,SAFE proposed
  style REJECTED fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F
```

## preview-mismatch

```yaml
anchor: |-
  synced edit or a session closed elsewhere can renumber `~1`
question: |-
  What prevents a moved segment number from carving the wrong session after preview?
illustrates: |-
  The Mac passes its previewed windows on submit; bob refuses differing resolved windows and the Mac re-previews after a timeline change.
caption: If resolved windows move after preview, bob refuses the submit and the Mac re-previews before recording.
review: "466×740 px, fit 100.0%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: reject stale windows"
accTitle: "Preview mismatch refusal and recovery"
accDescr: "The Mac submits its previewed windows to bob. If a timeline edit has moved the resolved windows, bob refuses and the Mac requests a new preview."
config:
  sequence:
    actorMargin: 65
    messageMargin: 24
    noteMargin: 12
    wrap: true
---
sequenceDiagram
  autonumber
  participant APP as Mac capture
  participant BOB as bob
  APP->>BOB: Preview draft (dry run)
  BOB-->>APP: Resolved windows
  Note over BOB: A close or sync edit<br/>can renumber ~1
  APP->>BOB: Submit draft + expected windows
  BOB->>BOB: Resolve windows again
  opt Resolved windows differ
    BOB-->>APP: Refuse: timeline changed
    APP->>BOB: Preview draft again
    BOB-->>APP: Updated windows
  end
```

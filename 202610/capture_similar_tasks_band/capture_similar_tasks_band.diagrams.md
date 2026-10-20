# Diagram proposals: Similar tasks in Bob Mac Capture's preview: consolidated research

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/capture_similar_tasks_band/capture_similar_tasks_band__final.md
producer: research.27.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 3 of 3 Mermaid diagrams; prescribed Puppeteer no-sandbox fallback; malformed-input test exited nonzero"
```

## matching-ownership

```yaml
anchor: |-
  Bob parses the draft and keeps only task-creating items that pass the
question: |-
  Which side owns matching, and when does a draft avoid a vault scan?
illustrates: |-
  Bob returns either empty items without walking the vault or per-item matches, while the app owns timing and pixels.
caption: "Bob owns eligibility and matching; the app owns timing and display, and nonqualifying drafts return without a vault walk."
review: "635.586x1019.22 px, fit 87.6%; question and visual checks passed; all nodes and edges traced to source; 0 revisions"
```

```mermaid
---
title: "Proposed: bob owns matching; the app owns display"
accTitle: "Ownership of task suggestions"
accDescr: "The app schedules a settled draft. Bob returns either an empty result without walking the vault, or per-item matches after discovering candidates once."
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 20
    wrappingWidth: 200
---
flowchart TB
  subgraph APP["Mac app: timing and display"]
    PAUSE["`**Typing pause**<br/>Schedule related lane`"]
    VIEW["`**Band view**<br/>Matches or no band`"]
  end
  subgraph BOB["bob: read-only matching"]
    ELIG{{"`**Qualifying new tasks?**`"}}
    EMPTY["`**Empty result**<br/>No vault walk`"]
    SCAN["`**Candidate discovery**<br/>Once per call`"]
    SCORE["`**Per-item matching**<br/>Bob-owned tokens and bands`"]
    ELIG -.->|No| EMPTY
    ELIG -.->|Yes| SCAN
    SCAN -.->|"Score each item"| SCORE
  end
  PAUSE -.->|"Pass draft"| ELIG
  EMPTY -.->|"Empty items"| VIEW
  SCORE -.->|"Matches by item index"| VIEW
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PAUSE,VIEW focus
  class ELIG decision
  class EMPTY,SCAN,SCORE outcome
  class PAUSE,VIEW,ELIG,EMPTY,SCAN,SCORE proposed
  style APP fill:none,stroke:#3B78C2
  style BOB fill:none,stroke:#2E7D4F
```

## discard-late-results

```yaml
anchor: |-
  the next keystroke cancels it, and a late result is discarded by the
question: |-
  What happens if an old search finishes after another keystroke?
illustrates: |-
  The next keystroke cancels the related lane, and the draft generation check discards a late result without delaying the preview or Return.
caption: "A keystroke cancels the related request; the draft generation check discards any late reply while preview and Return remain independent."
review: "828.5x718 px, fit 78.8%; question and visual checks passed; conditional late reply and all exchanges traced to source; 0 revisions"
```

```mermaid
---
title: "Proposed: discard stale task suggestions"
accTitle: "Cancellation and stale-result rejection"
accDescr: "After a settled-draft search starts, another keystroke cancels it. If an old reply still arrives, the app rejects it by checking the draft generation."
---
sequenceDiagram
  autonumber
  participant U as User
  participant A as Mac app
  participant B as bob related lane
  U->>A: Enter new-task draft
  A-->>B: After ~350 ms without edits:<br/>search this draft
  U->>A: Next keystroke edits draft
  A-->>B: Cancel related request
  Note over A: Typing, preview and Return<br/>never wait on this lane
  opt Old request replies late
    B-->>A: Previous draft's result
    A->>A: Generation mismatch:<br/>discard result
  end
```

## explicit-block-id-write

```yaml
anchor: |-
  is minting a block ID when you act on an ID-less row
question: |-
  Can choosing a suggestion write before Return?
illustrates: |-
  Link actions use an existing replacement or explicitly mint a missing block ID, then bob validates and previews the draft edit before capture.
caption: "Link actions may explicitly create a missing block identifier before Return; bob still previews the capture consequence."
review: "464.172x1116 px, fit 80.0%; question and visual checks passed; alternative ID paths and pre-Return write traced to source; 0 revisions"
```

```mermaid
---
title: "Proposed: when a link action writes before Return"
accTitle: "Explicit block-ID creation before capture"
accDescr: "An action needing a task reference uses an existing bob replacement or explicitly mints a missing block ID. The resulting draft edit is then previewed before capture."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 220
---
flowchart TD
  ACT["`**Choose a link action**<br/>Relate, note, needs or blocks`"]
  HAS{{"`**Task has block ID?**`"}}
  MINT["`**Explicit ID creation**<br/>Writes before Return`"]
  EDIT["`**Draft edit**<br/>Use bob's replacement`"]
  PREVIEW["`**Normal dry-run**<br/>Preview actual consequence`"]
  SUBMIT["`**Return in editor**<br/>Submit capture`"]
  ACT -.->|"Check selected task"| HAS
  HAS -.->|"Yes: replacement available"| EDIT
  HAS -.->|No| MINT
  MINT -.->|"Replacement from capture-task-id"| EDIT
  EDIT -.->|"Validate draft"| PREVIEW
  PREVIEW -.->|"Later: submit draft"| SUBMIT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class ACT,EDIT,PREVIEW,SUBMIT focus
  class HAS decision
  class MINT risk
  class ACT,HAS,MINT,EDIT,PREVIEW,SUBMIT proposed
```

# Diagram proposals: Type lead words in the capture panel

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/capture_type_lead_words/capture_type_lead_words__final.md
producer: research.6p.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## older-mac-fallback

```yaml
anchor: |-
  submission proceeds with `#fix ` and bob's existing "needs a task" refusal.
question: |-
  Why does a separate lead field prevent one-word tasks when an older Mac accepts and submits?
illustrates: |-
  With a separate lead field, an older Mac submits the bare marker and preserves the existing needs-a-task refusal; baking in the lead captures Fix.
caption: "On older Macs, a separate lead field preserves the existing refusal; baking the lead into replacement can capture a one-word task."
review: "603.016x673 px, fit 100%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why keep the lead separate on older Macs?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 230
---
flowchart TB
  subgraph BAKED["Rejected: lead inside replacement"]
    direction TB
    BP["`**Replacement**<br/>#fix Fix plus space`"]
    BM["`**Old Mac**<br/>Accepts replacement`"]
    BD["`**Submitted draft**<br/>#fix Fix`"]
    BO["`**Captured task**<br/>Title: Fix`"]
    BP -->|"accept"| BM
    BM -->|"Command-Return submits"| BD
    BD -->|"has task body"| BO
  end
  subgraph SEPARATE["Proposed: optional lead field"]
    direction TB
    SP["`**Replacement**<br/>#fix plus separate lead`"]
    SM["`**Old Mac**<br/>Accepts replacement`"]
    SD["`**Submitted draft**<br/>#fix plus space`"]
    SO["`**Existing refusal**<br/>needs a task`"]
    SP -.->|"accept; ignores lead"| SM
    SM -.->|"Command-Return submits"| SD
    SD -.->|"no task body"| SO
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class BP,BM,BD,SP,SM,SD focus
  class BO risk
  class SO outcome
  class SP,SM,SD,SO proposed
  style BAKED fill:none,stroke:#C0392B
  style SEPARATE fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

## acceptance-paths

```yaml
anchor: |-
  Acceptance stays bound to the exact draft/caret snapshot the response was computed for
question: |-
  For an eligible #f response carrying a lead, how does proposed acceptance branch on snapshot validity and gesture?
illustrates: |-
  Snapshot-bound acceptance applies the marker before a native lead edit; accept-then-capture skips the lead and preserves the existing refusal.
caption: "For an offered lead on #f, stale responses never apply; ordinary acceptance inserts undoable text, while accept-and-capture preserves the existing refusal."
review: "620.324x762 px, fit 100%; question and visual checks passed; 1 revision to clarify the title"
```

```mermaid
---
title: "Proposed: how is a type lead accepted?"
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 18
    wrappingWidth: 230
---
flowchart TD
  SNAP{{"`**Same draft and caret?**`"}}
  STALE["`**Stale response**<br/>Do not apply`"]
  GESTURE{{"`**Accept-and-capture gesture?**`"}}
  MARKER["`**Existing marker edit**<br/>#fix plus space`"]
  LEAD["`**Native lead edit**<br/>Fix; own undo group`"]
  SUBMIT["`**Submit bare marker**<br/>Skip lead`"]
  REFUSE["`**Existing refusal**<br/>Panel stays open`"]
  SNAP -.->|"No"| STALE
  SNAP -.->|"Yes"| GESTURE
  GESTURE -.->|"No: Tab, Return, click"| MARKER
  MARKER -.->|"then insert lead"| LEAD
  GESTURE -.->|"Yes: Control/Command-Return"| SUBMIT
  SUBMIT -.->|"needs a task"| REFUSE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class SNAP,GESTURE decision
  class MARKER,SUBMIT focus
  class STALE,LEAD,REFUSE outcome
  class SNAP,GESTURE,MARKER,SUBMIT,STALE,LEAD,REFUSE proposed
```

# Diagram proposals: Get the most out of Bob Gmail

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bob_gmail_everyday_guide/bob_gmail_everyday_guide__final.md
producer: research.5s.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## capture-fallback

```yaml
anchor: |-
  If anything goes wrong (offline, signed out, or not the writer machine)
question: |-
  What happens to a captured email URL when linking succeeds or fails?
illustrates: |-
  The task saves instantly; an already saved thread links instantly, while a new thread links after capture or leaves its URL for later conversion if linking fails.
caption: Planned capture saves the task immediately; linking either replaces its URL or leaves it intact for later conversion on the Mac.
review: "508.992×964 px, fit 92.6%; question and visual checks passed; source trace checked; 0 revisions"
```

```mermaid
---
title: "Coming: what happens to a captured Gmail URL?"
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  TASK["`**Capture submitted**<br/>Task saved instantly`"]
  SAVED{{"`**Thread already saved?**`"}}
  TRY["`**Save thread**<br/>Link after capture`"]
  LINK["`**Named mail link**<br/>Replaces the URL`"]
  URL["`**URL stays**<br/>Nothing is lost`"]
  RETRY["`**Convert later on Mac**<br/>bob gmail link &lt;note&gt;`"]
  TASK -.->|"Email linking"| SAVED
  SAVED -.->|"Yes: instantly"| LINK
  SAVED -.->|"No"| TRY
  TRY -.->|"Success: about two seconds"| LINK
  TRY -.->|"Offline, signed out,<br/>or wrong writer"| URL
  URL -.->|"Later conversion"| RETRY
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class TASK,TRY,URL,RETRY focus
  class SAVED decision
  class LINK outcome
  class TASK,SAVED,TRY,LINK,URL,RETRY proposed
```

## send-safeguards

```yaml
anchor: |-
  If you edit after previewing, Bob shows you the new version
question: |-
  What keeps a previewed reply from being sent unexpectedly or twice?
illustrates: |-
  For planned replies, edits trigger a new preview, confirmation starts the Undo countdown, and an unknown send outcome calls for checking Gmail's Sent folder.
caption: Planned replies require confirmation; edits trigger another preview, Undo stops delivery, and an unknown outcome calls for checking Gmail Sent before retrying.
review: "677.234×614 px, fit 96.4%; question and visual checks passed; source trace checked; 0 revisions"
```

```mermaid
---
title: "Coming: what happens after choosing Send?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 175
---
flowchart TD
  PREVIEW["`**Exact message preview**<br/>Recipients, subject, body, attachments`"]
  WAIT["`**Undo countdown**<br/>Length is a plugin setting`"]
  CANCEL["`**Canceled**<br/>Nothing leaves`"]
  SENT["`**Sent**<br/>New card; Reply section removed`"]
  CHECK["`**Check Gmail Sent**<br/>Before trying again`"]
  PREVIEW -.->|"Edited: show new version"| PREVIEW
  PREVIEW -.->|"You confirm"| WAIT
  WAIT -.->|"Undo before sending"| CANCEL
  WAIT -.->|"Sent after countdown"| SENT
  WAIT -.->|"Outcome unknown:<br/>no automatic resend"| CHECK
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class PREVIEW,WAIT focus
  class CANCEL,SENT outcome
  class CHECK risk
  class PREVIEW,WAIT,CANCEL,SENT,CHECK proposed
```

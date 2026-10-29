# Diagram proposals: `bob gcal`: Google Calendar events as daily-note Event Tasks

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/bob_gcal_daily_events/bob_gcal_daily_events__final.md
producer: research.2w.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox"
```

## sync-write-gates

```yaml
anchor: |-
  On a stale file, retry once, then exit 1 and let the next tick try again.
question: |-
  After the daily note exists, what must succeed before sync can write the note and then the journal?
illustrates: |-
  After the day's note exists, a complete snapshot and changed plan reach the preimage-checked staged write, a stale file gets one retry, and the journal follows note-write success.
caption: A failed fetch or exhausted retry stops writes; an unchanged plan writes nothing; the journal follows a successful note write.
review: "695.920×1158 px, fit 77.1%; question, source-trace and visual checks passed; 1 revision, 2 looks; failure arrows are alternatives"
```

```mermaid
---
title: "Proposed: what permits a Calendar sync write?"
accTitle: "Calendar synchronization write gates"
accDescr: "After the daily note exists, an incomplete fetch writes nothing. A changed plan must pass a preimage check; a stale file gets one replan. The journal is appended only after the note write succeeds."
config:
  flowchart:
    rankSpacing: 8
    nodeSpacing: 12
    wrappingWidth: 220
---
flowchart TD
  FETCH["`**Fetch one day**<br/>All pages + lookups`"]
  COMPLETE{{"`**Complete snapshot?**`"}}
  STOP["`**No writes**<br/>Failed run`"]
  PLAN["`**Plan edits**<br/>Note snapshot`"]
  CHANGE{{"`**Changed bytes?**`"}}
  NOOP["`**No writes**<br/>No journal append`"]
  PRE{{"`**Preimage matches?**`"}}
  RETRIED{{"`**Retry used?**`"}}
  WRITE["`**Staged note write**<br/>Vault lock`"]
  JOURNAL["`**Append journal**<br/>After note succeeds`"]
  FETCH -.-> COMPLETE
  COMPLETE -.->|"Any failure"| STOP
  COMPLETE -.->|"All calls pass"| PLAN
  PLAN -.-> CHANGE
  CHANGE -.->|"No"| NOOP
  CHANGE -.->|"Yes"| PRE
  PRE -.->|"No: stale file"| RETRIED
  RETRIED -.->|"No: replan once"| PLAN
  RETRIED -.->|"Yes"| STOP
  PRE -.->|"Yes"| WRITE
  WRITE -.->|"write succeeds"| JOURNAL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class FETCH,PLAN focus
  class COMPLETE,CHANGE,PRE,RETRIED decision
  class STOP,NOOP,WRITE,JOURNAL outcome
  class FETCH,PLAN,COMPLETE,CHANGE,PRE,RETRIED,STOP,NOOP,WRITE,JOURNAL proposed
```

# Diagram proposals: Rotten Log: a task-local history of rotten keeps

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/rotten_log_keep_history/rotten_log_keep_history__final.md
producer: research.55.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## keep-commit-safety

```yaml
anchor: |-
  Capture the preimage, local day, and eligibility before the async prompt.
question: |-
  How does a proposed keep avoid a stale or half-written result?
illustrates: |-
  For one counted keep that needs no decay decision, capturing and revalidating the preimage, local day, and eligibility before the combined write keeps cancellation and failed checks from committing a stamp without its entry.
caption: For an eligible keep without a decay decision, cancellation or failed checks write nothing; stamp, streak and log commit together before navigation.
review: "741.966x1002 px, fit 88.0%; question and visual checks passed; source trace passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when does a counted keep commit?"
accTitle: "Proposed single-task keep with cancellation and write safety"
accDescr: "For one eligible counted keep that needs no decay decision, capture the preimage, day and eligibility before the reason prompt; revalidate after Enter and plan the entry before one combined commit. Escape or either failed check writes nothing. After commit, Alt+F stays and Ctrl+Alt+F advances once."
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  CAPTURE["`**Capture target**<br/>Preimage, day, eligibility`"]
  PROMPT["`**Reason prompt**<br/>Text is optional`"]
  CANCEL["`**Cancel**<br/>No write or advance`"]
  VALID{{"`**Target and day valid?**`"}}
  REFUSE["`**Refuse keep**<br/>Write nothing`"]
  PLAN{{"`**Entry can be planned?**`"}}
  COMMIT["`**One transaction**<br/>Stamp, streak, log`"]
  STAY["`**Stay**<br/>Same source row`"]
  ADVANCE["`**Advance once**<br/>Existing gesture lock`"]
  CAPTURE -.-> PROMPT
  PROMPT -.->|Escape| CANCEL
  PROMPT -.->|"Enter: text or blank"| VALID
  VALID -.->|No| REFUSE
  VALID -.->|Yes| PLAN
  PLAN -.->|No| REFUSE
  PLAN -.->|Yes| COMMIT
  COMMIT -.->|Alt+F| STAY
  COMMIT -.->|Ctrl+Alt+F| ADVANCE
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class CAPTURE,PROMPT,CANCEL,REFUSE muted
  class VALID,PLAN decision
  class COMMIT,STAY,ADVANCE outcome
  class CAPTURE,PROMPT,CANCEL,REFUSE,VALID,PLAN,COMMIT,STAY,ADVANCE proposed
```

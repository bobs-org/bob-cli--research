# Diagram proposals: Record Card: a value card for record notes, under the H1

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/record_card/record_card__final.md
producer: research.55.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## save-guards

```yaml
anchor: |-
  rebuilt in the same `write_staged_files_guarded` batch, preimage guards on both files,
question: |-
  Why does saving need both an expected fingerprint and file preimage guards?
illustrates: |-
  The proposed expect fingerprint and existing preimage-guarded batch have separate refusal paths before the record and album index are written together.
caption: The proposed fingerprint rejects stale frontmatter/schema edits; existing preimage guards reject changed files before writing the record and album index together.
review: "575.266x986 px, fit 90.5%; reader-question, source-trace, labels, arrowheads, crossings, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed Record Card: what stops a conflicting save?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 180
---
flowchart TD
  APPLY["`**Apply with expect**<br/>Frontmatter + album schema`"]
  SEM{{"`**Fingerprint still matches?**`"}}
  STALE["`**stale_record**<br/>Repaint; keep draft`"]
  PREP["`**Prepare edits**<br/>Record YAML + album index`"]
  FILES{{"`**Files match read snapshots?**`"}}
  RETRY["`**Refuse raced write**<br/>Enter retries`"]
  WRITE["`**Write together**<br/>Record + album index`"]
  APPLY -.->|check| SEM
  SEM -.->|No| STALE
  SEM -.->|Yes| PREP
  PREP -.->|before installation| FILES
  FILES -.->|No| RETRY
  FILES -.->|Yes| WRITE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class APPLY,PREP focus
  class SEM,FILES,STALE,RETRY decision
  class WRITE outcome
  class APPLY,SEM,STALE proposed
```

## apply-paths

```yaml
anchor: |-
  for discrete picks** (choice pick, `t` today, clear, undo) with previews only for typed
question: |-
  Which Record Card edits need a preview before applying?
illustrates: |-
  The proposed Record Card directly applies discrete picks and previews typed stages, with either path guarded by expect for one gesture per write.
caption: Discrete actions apply directly; typed changes need a current valid preview. Either route sends an expected frontmatter/schema fingerprint.
review: "616.76x962 px, fit 92.8%; reader-question, source-trace, labels, arrowheads, crossings, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed Record Card: which edits need a preview?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 180
---
flowchart TD
  KIND{{"`**Which edit?**`"}}
  PICK["`**Discrete action**<br/>Choice, today, clear, undo`"]
  PREVIEW["`**Debounced dry run**<br/>Validate typed field`"]
  CURRENT{{"`**Current valid preview?**`"}}
  STAY["`**Stay in stage**<br/>Wait or correct value`"]
  ENTER["`**Enter**<br/>Save staged value`"]
  APPLY["`**Apply with expect**<br/>Either route; one write`"]
  KIND -.->|Discrete| PICK
  KIND -.->|Typed| PREVIEW
  PREVIEW -.->|check result| CURRENT
  CURRENT -.->|Pending or invalid| STAY
  CURRENT -.->|Yes| ENTER
  PICK -.->|apply directly| APPLY
  ENTER -.->|apply after preview| APPLY
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PICK,PREVIEW,ENTER focus
  class KIND,CURRENT,STAY decision
  class APPLY outcome
  class PICK,PREVIEW,ENTER,APPLY proposed
```

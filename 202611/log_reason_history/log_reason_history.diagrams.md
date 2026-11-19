# Diagram proposals: Reason Recall: log-entry history for Ctrl+N/P in Bob's log prompts

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/log_reason_history/log_reason_history__final.md
producer: research.5h.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; invalid-source rejection verified"
```

## vault-owned-history

```yaml
anchor: |-
  the log write *is* the history write. A journal is a second copy
question: |-
  How does recall stay current without a second durable phrase database?
illustrates: |-
  The log write is the history write, while the in-session overlay makes immediate reuse exact and prompt-open revalidation reads the current per-kind catalog.
caption: Successful writes feed immediate session recall; vault-derived history respects note edits and deletions without a second durable phrase database.
review: "760x719 px, fit 85.9%; question, source tracing, labels, arrowheads, crossings and reading direction passed; 0 visual revisions; 1 pre-render syntax correction"
```

```mermaid
---
title: "Proposed: how does recall stay current?"
accTitle: "Vault-owned history and immediate session recall"
accDescr: "A successful task-log write updates the vault and then the recall store's in-session overlay. On prompt open the store revalidates through bob, whose scanner reads current vault entries and serves a per-kind catalog. The vault remains the only durable phrase history."
config:
  sequence:
    actorMargin: 20
    width: 125
    messageMargin: 24
    noteMargin: 8
---
sequenceDiagram
  autonumber
  participant W as Shared log<br/>writer
  participant V as Vault<br/>task logs
  participant R as Recall<br/>store
  participant B as bob<br/>scanner
  W->>V: Write log entry
  V-->>W: Write succeeds
  W->>R: noteUsed(kind, text)
  Note over R: Session overlay:<br/>immediate reuse
  opt Prompt opens
    R->>B: bob logs list
    B->>V: Stat-walk and<br/>read changed notes
    Note over V,B: Edits and deletions<br/>change the derived history
    B-->>R: Per-kind phrase catalog
  end
```

## capture-completion-routing

```yaml
anchor: |-
  existing completion popup supplies keys (`Ctrl+N/P` cycle, Tab/Return accept),
question: |-
  When does Mac inline Work Log history own Ctrl+N/P?
illustrates: |-
  Within inline Work Log text, history is eligible outside wikilinks after a typed character, and Ctrl+N/P navigate candidates only while the completion popup is open.
caption: Within inline Work Log text, history needs free text and a typed character; an open popup owns navigation, otherwise caret motion stays native.
review: "677.924x808 px, fit 96.3%; question, source tracing, labels, arrowheads, crossings and reading direction passed; 1 visual revision clarified caret motion; converging No branches mean either"
```

```mermaid
---
title: "Proposed: when does Mac Work Log history own keys?"
accTitle: "Inline Work Log history eligibility and key routing"
accDescr: "Within inline Work Log text, wikilinks keep existing completion. Free text requires a typed character before history is eligible. Ctrl+N and Ctrl+P cycle an open completion popup; without it they retain Emacs line motion."
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 22
    wrappingWidth: 200
---
flowchart TD
  FREE{{"`**Free text outside links?**`"}}
  TYPED{{"`**Typed a character?**`"}}
  OPEN{{"`**History popup open?**`"}}
  WIKI["`**Wikilink completion**<br/>Keep existing behavior`"]
  NATIVE["`**No popup**<br/>Ctrl+N/P move caret`"]
  POP["`**Completion popup**<br/>Ctrl+N/P cycle<br/>Tab/Return accept phrase`"]
  FREE -->|"No: inside wikilink"| WIKI
  FREE -.->|"Yes"| TYPED
  TYPED -.->|"No"| NATIVE
  TYPED -.->|"Yes: history eligible"| OPEN
  OPEN -.->|"No"| NATIVE
  OPEN -.->|"Yes"| POP
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class FREE,TYPED,OPEN decision
  class WIKI,NATIVE focus
  class POP outcome
  class POP proposed
```

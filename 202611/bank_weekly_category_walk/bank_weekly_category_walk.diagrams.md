# Diagram proposals: Bank, weekly: one Monday chore, one keypress per row, and the cleaning fix that makes it cheap

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_weekly_category_walk/bank_weekly_category_walk__final.md
producer: research.4i.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; the deliberately broken chart exited nonzero"
```

## safe-commit

```yaml
anchor: |-
  capture row text + `^bank-` ID at card open; at commit, re-resolve
question: |-
  How does a category choice avoid overwriting a changed row?
illustrates: |-
  The proposed write path re-resolves the row, refuses changed rows or duplicate category fields, commits tick and category together, and advances only after a successful write.
caption: The proposed write requires an unchanged row without duplicate category fields; advancement waits for a successful transaction.
review: "510.118x1114 px, fit 80.1%; question answered from PNG; labels, arrows, source trace and PDF fit passed; either refusal condition suffices; 0 revisions"
```

```mermaid
---
title: "Proposed: when is a category edit safe to commit?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 220
---
flowchart TD
  OPEN["`**Card opens**<br/>Capture row text and bank ID`"]
  RESOLVE["`**Commit attempt**<br/>Re-resolve row identity`"]
  SAME{{"`**Row unchanged?**`"}}
  DUP{{"`**Duplicate category fields?**`"}}
  REFUSE["`**Refuse edit**<br/>No write or advance`"]
  WRITE["`**One editor transaction**<br/>Tick and category together`"]
  NEXT["`**Advance**<br/>Next waiting bank row`"]
  OPEN -.->|At commit| RESOLVE
  RESOLVE -.->|Compare captured text| SAME
  SAME -.->|No: show notice| REFUSE
  SAME -.->|Yes| DUP
  DUP -.->|Yes| REFUSE
  DUP -.->|No| WRITE
  WRITE -.->|Only after success| NEXT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OPEN,RESOLVE focus
  class SAME,DUP,REFUSE decision
  class WRITE,NEXT outcome
  class OPEN,RESOLVE,SAME,DUP,REFUSE,WRITE,NEXT proposed
```

## availability

```yaml
anchor: |-
  unreachable, offer only `Space` (tick, no category) and `Esc` — acknowledging is
question: |-
  What remains usable when ledger-tools or bob/config is unavailable?
illustrates: |-
  The proposed delegation keeps the plain checkbox flip when ledger-tools is absent, while unreachable bob/config restricts the card to Space and Esc.
caption: Missing ledger-tools preserves the checkbox flip; unreachable bob/config still offers Space to acknowledge without a category or Esc to cancel.
review: "752.072x762 px, fit 86.8%; question answered from PNG; labels, branch conditions, arrowheads, source trace and PDF fit passed; 0 revisions"
```

```mermaid
---
title: "Proposed: what works when a dependency is missing?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TD
  API{{"`**Ledger-tools API present?**`"}}
  OLD["`**Plain checkbox flip**<br/>Existing behavior`"]
  CONFIG{{"`**Bob/config reachable?**`"}}
  FULL["`**Full Category card**<br/>Choose or accept category`"]
  LIMITED["`**Restricted card**<br/>Only Space or Esc`"]
  TICK["`**Space**<br/>Tick without category`"]
  CANCEL["`**Esc**<br/>Cancel without writing`"]
  API -.->|No| OLD
  API -.->|Yes| CONFIG
  CONFIG -.->|Yes| FULL
  CONFIG -.->|No| LIMITED
  LIMITED -.->|Press Space| TICK
  LIMITED -.->|Press Esc| CANCEL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class API,CONFIG decision
  class FULL,LIMITED focus
  class OLD,TICK,CANCEL outcome
  class API,CONFIG,OLD,FULL,LIMITED,TICK,CANCEL proposed
```

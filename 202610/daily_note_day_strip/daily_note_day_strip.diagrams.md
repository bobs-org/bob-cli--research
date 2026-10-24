# Diagram proposals: The Day strip: a compact daily-stats footer for Bob daily notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/daily_note_day_strip/daily_note_day_strip__final.md
producer: research.2f.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; smoke render used --no-sandbox; malformed input correctly failed"
```

## fetch-waiter-preservation

```yaml
anchor: |-
  Replace the single pending slot with a per-key in-flight map and
question: |-
  Why must the fetch service change before several daily notes consume it?
illustrates: |-
  The current single pending slot loses B when C arrives, while the proposed per-key map and FIFO preserve distinct pending keys until each waiter settles.
caption: A first-in, first-out queue preserves pending keys so each waiter receives its own result or an explicit cancellation instead of hanging.
review: "668.844×787 px, fit 97.6%; question and visual checks passed; 1 revision; every node and edge traced to F8a and section 5.7; unique body anchor"
```

```mermaid
---
title: "Why fix the fetch service before adding Day strips?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
---
flowchart TD
  REQUESTS["`**A running**<br/>B, then C requested`"]
  subgraph CURRENT["Current: one pending slot"]
    B["`**B pending**<br/>Waiting request`"]
    C["`**C pending**<br/>B replaced`"]
    HANG["`**B never settles**<br/>Request hangs`"]
    B -->|"C replaces B"| C
    C -->|"leaves B unresolved"| HANG
  end
  subgraph PROPOSAL["Proposed: per-key map + FIFO queue"]
    QUEUE["`**Distinct pending keys**<br/>One run at a time`"]
    RESULT["`**Each waiter settles**<br/>Its own key's result`"]
    CANCEL["`**Each waiter settles**<br/>Explicit cancellation`"]
    QUEUE -.->|"with result"| RESULT
    QUEUE -.->|"or cancellation"| CANCEL
  end
  REQUESTS -->|"B waits"| B
  REQUESTS -.->|"proposed: preserve B and C"| QUEUE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class REQUESTS,B,C focus
  class HANG risk
  class QUEUE,RESULT,CANCEL outcome
  class QUEUE,RESULT,CANCEL proposed
  style CURRENT fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

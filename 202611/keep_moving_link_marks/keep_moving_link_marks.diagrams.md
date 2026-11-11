# Diagram proposals: Keep-moving marks on ledger Task Links

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/keep_moving_link_marks/keep_moving_link_marks__final.md
producer: research.44.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## cache-count-lifecycle

```yaml
anchor: |-
  Never show a stale positive
question: |-
  When must a visible count disappear while fresh inputs are loading?
illustrates: |-
  Unknown and known-zero stay distinct internally while both render as nothing, and invalidation prevents stale positive numbers from remaining visible.
caption: After invalidation, hide the mark until current inputs support a new count; unknown and known zero remain distinct.
review: "538.531x370 px, fit 100.0%; reader question, labels, arrowheads, crossings, source trace and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: when must a count disappear?"
accTitle: "Proposed keep-moving cache lifecycle"
accDescr: "Unknown and known-zero both hide the mark. A current eligible positive result shows it. Invalidating either known state returns to unknown, so a stale positive never stays visible."
---
stateDiagram-v2
  direction TB
  state "Unknown: cold or invalidated" as UNKNOWN
  state "Known zero: no mark" as ZERO
  state "Known positive: show N" as POSITIVE
  UNKNOWN --> ZERO: Current: zero
  UNKNOWN --> POSITIVE: Current: eligible N ≥ 1
  ZERO --> UNKNOWN: Invalidated
  POSITIVE --> UNKNOWN: Invalidated
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class UNKNOWN muted
  class ZERO focus
  class POSITIVE outcome
  class UNKNOWN proposed
  class ZERO proposed
  class POSITIVE proposed
```

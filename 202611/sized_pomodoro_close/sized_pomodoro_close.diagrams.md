# Diagram proposals: `<N>x`: close the running Pomodoro at a stated size

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/sized_pomodoro_close/sized_pomodoro_close__final.md
producer: research.3s.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## same-span-different-clock

```yaml
anchor: |-
  The chain cannot fix this: the `x` item does not know that
question: |-
  Why can the same recorded span close different meetings?
illustrates: |-
  A sized close uses the sized end as its close clock in the two-meeting example, so the same recorded span completes Design review and carries Vendor sync instead of completing both at the wall clock.
caption: "Without explicit picks, a sized close carries Vendor sync; today's chain completes it despite recording the same 09:00–09:30 span."
review: "656×721 px, fit 99.5%; question, source trace, labels, arrows, and visual checks passed; 1 visual revision; batch rendered 1/1; broken-diagram control exited nonzero"
```

```mermaid
---
title: "Why can the same span close different meetings?"
accTitle: "Current and proposed close clocks for the same recorded span"
accDescr: "Without explicit task picks, the current minus-six-blocks then close chain completes both meetings using the 10:15 wall clock. The proposed six-block sized close records the same 09:00 to 09:30 span but uses 09:30, completing Design review and carrying the not-started Vendor sync."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  subgraph PROPOSAL["Proposed: close at a stated size"]
    direction TB
    P["`**6x at 10:15**<br/>Session planned 09:00–10:00`"]
    Q["`**Recorded span**<br/>09:00–09:30`"]
    R["`**Close clock**<br/>09:30 sized end`"]
    S["`**Vendor sync carried**<br/>Not started; Design review completes`"]
    P -.->|records| Q
    Q -.->|then classifies tasks at| R
    R -.->|classifies| S
  end
  subgraph TODAY["Today: relative adjust, then close"]
    direction TB
    A["`**-6 x at 10:15**<br/>Session planned 09:00–10:00`"]
    B["`**Recorded span**<br/>09:00–09:30`"]
    C["`**Close clock**<br/>10:15 wall time`"]
    D["`**Both meetings complete**<br/>Including Vendor sync, 09:30–10:00`"]
    A -->|records| B
    B -->|then classifies tasks at| C
    C -->|classifies| D
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class A,B,P,Q focus
  class C,D risk
  class R,S outcome
  class P,Q,R,S proposed
  style TODAY fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

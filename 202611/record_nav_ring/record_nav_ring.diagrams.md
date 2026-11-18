# Diagram proposals: Record nav ring

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/record_nav_ring/record_nav_ring__final.md
producer: research.5b.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; invalid syntax correctly exited nonzero"
```

## first-match-placement

```yaml
anchor: |-
  A bottom-of-body nav line loses to any earlier authored link whose alias
question: |-
  Why does putting navigation first prevent a detour?
illustrates: |-
  First-match-wins scanning makes a bottom-of-body nav line lose to an earlier authored ‹ Detour link, while first-body placement makes the managed walk win.
caption: "For [n (Previous), an earlier matching link hijacks bottom navigation; putting the managed line first keeps the jump inside the album."
review: "730.484x672 px, fit 89.4%; PNG question, labels, arrowheads, crossings, reading direction and source checks passed; 0 revisions; unique body-paragraph anchor verified"
```

```mermaid
---
title: "Why put record navigation first?"
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 20
    wrappingWidth: 180
---
flowchart TB
  subgraph BAD["Rejected placement: navigation last"]
    direction LR
    DETOUR["`**Earlier authored link**<br/>‹ Detour`"]
    BOTTOM["`**Later body line**<br/>Managed record navigation`"]
    WRONG["`**Unrelated note**<br/>Wrong destination`"]
    DETOUR -->|"first match opens"| WRONG
    DETOUR -.-|"later match ignored"| BOTTOM
  end
  subgraph GOOD["Proposed placement: navigation first"]
    direction LR
    FIRST["`**First body line**<br/>Managed record navigation`"]
    LATER["`**Later authored link**<br/>‹ Detour`"]
    RIGHT["`**Album neighbour**<br/>Intended destination`"]
    FIRST -.->|"first match opens"| RIGHT
    FIRST -.-|"later match ignored"| LATER
  end
  BAD ~~~ GOOD
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class DETOUR,WRONG risk
  class BOTTOM,FIRST,LATER focus
  class RIGHT outcome
  class FIRST,LATER,RIGHT proposed
  style BAD fill:none,stroke:#C0392B
  style GOOD fill:none,stroke:#2E7D4F
```

# Diagram proposals: Checklist stages and period-review prep for the morning GTD walk

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gtd_checklist_stages_and_period_prep/gtd_checklist_stages_and_period_prep__final.md
producer: research.3h.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## january-overlap-dependencies

```yaml
anchor: |-
  2027-01-04 is the weekly plus quarterly Monday. The just-ended week,
question: |-
  On January overlap days, which period comes first?
illustrates: |-
  On January 4 one agent drafts W53 then Q4; on January 11 the W01 draft is independent, while the year draft can read the Q4 Review either immediately if finished or after completing the still-open Quarterly review.
caption: "Proposed: draft week 53 before quarter four; start the year draft once Q4 Review is finished. Week 1 is independent."
review: "626.996x930 px, fit 96.0%; question, source trace and visual checks passed; 1 revision across 2 look rounds; batch check passed; broken-diagram negative check exited nonzero"
```

```mermaid
---
title: "Proposed: what comes first on January review days?"
accTitle: "Two January period-draft overlap cases"
accDescr: "On January 4 one agent drafts week 53 before quarter 4. On January 11 the week 1 draft is independent, but the year draft waits for quarter 4 review if it remains open."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  subgraph JAN4["4 January 2027 · week + quarter"]
    W53["`**2026-W53 draft**<br/>Week in Q4`"]
    Q4["`**2026-Q4 draft**<br/>Week informs quarter`"]
    W53 -.->|"then · same agent"| Q4
  end
  subgraph JAN11["11 January 2027 · week + year"]
    W1["`**2027-W01 draft**<br/>Independent of year draft`"]
    OPEN{{"`**Q4 review still open?**`"}}
    REVIEW["`**Review Q4**<br/>Finish before year draft`"]
    YEAR["`**2026 year draft**<br/>Reads the Q4 Review`"]
    OPEN -.->|"Yes · first"| REVIEW
    OPEN -.->|"No · proceed"| YEAR
    REVIEW -.->|"then"| YEAR
  end
  JAN4 ~~~ JAN11
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class W53,W1 focus
  class OPEN decision
  class Q4,REVIEW,YEAR outcome
  class W53,W1,OPEN,Q4,REVIEW,YEAR proposed
  style JAN4 fill:none,stroke:#3B78C2
  style JAN11 fill:none,stroke:#3B78C2
```

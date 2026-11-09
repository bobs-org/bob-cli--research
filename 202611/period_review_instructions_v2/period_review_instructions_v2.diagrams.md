# Diagram proposals: Period-note reviews: keep the setup, and make v2 record what the period produced

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/period_review_instructions_v2/period_review_instructions_v2__final.md
producer: research.3u.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; deliberately invalid syntax exited nonzero"
```

## live-pilot-gates

```yaml
anchor: |-
  Open bead **bob-cli-gp** (Monday athena job) should wait
question: |-
  What permits Monday automation, and when should Reviews shrink?
illustrates: |-
  The Monday job waits for four live v2 drafts Bryan would keep, while no corrections, reflection, or answers after about six v2 weeks calls for Headline + Shipped.
caption: Automate only after four acceptable live drafts; without human engagement after about six weeks, shorten the Review to Headline + Shipped.
review: "864.654×455 px, fit 75.5%; source tracing, reader-question, labels, arrowheads, crossings, and visual checks passed; 1 revision across 2 visual checks"
```

```mermaid
---
title: "Proposed weekly Review gates: automate or shorten?"
accTitle: "Separate conditions for automation and Review length"
accDescr: "Automation waits for four live v2 drafts Bryan would keep, excluding backfill. If Bryan never corrects, reflects, or answers after about six v2 weeks, shorten to Headline and Shipped. The two gates are independent."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 12
    wrappingWidth: 190
---
flowchart TB
  subgraph AUTO["Proposed automation · no backfill"]
    A{{"`**Four live v2 drafts**<br/>Bryan would keep?`"}}
    JOB["`**Monday job**<br/>Eligible to automate`"]
    WAIT["`**Monday job**<br/>Keep waiting`"]
    A -.->|Yes| JOB
    A -.->|No| WAIT
  end
  subgraph LENGTH["Proposed length · about six v2 weeks"]
    Q{{"`**No human engagement?**<br/>Never corrects, reflects, or answers`"}}
    SHORT["`**Headline + Shipped**<br/>About 80 words`"]
    Q -.->|If so, shorten| SHORT
  end
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class A,Q decision
  class JOB,SHORT outcome
  class WAIT muted
  class A,Q,JOB,WAIT,SHORT proposed
  style AUTO fill:none,stroke:#C77C02
  style LENGTH fill:none,stroke:#C77C02
```

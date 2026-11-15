# Diagram proposals: Bank subscriptions album: consolidated design and seed review

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_subscriptions_feature_design/bank_subscriptions_feature_design__final.md
producer: research.4s.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox"
```

## journal-attribution

```yaml
anchor: |-
  Because rule 2 covers `before_start` journal events,
question: |-
  How can journal-only history count without creating bank rows?
illustrates: |-
  Read-time attribution uses an explicit subscription link first and otherwise resolves eligible masked journal descriptions, so before_start history counts without creating bank rows.
caption: "Proposed read-time attribution uses explicit links first, then eligible journal matches, without creating bank rows; either exclusion or no winning match prevents inference."
review: "705.555x832 px, fit 92.5%; question, labels, arrowheads, crossings, direction and source checks passed; 0 revisions; 1 visual look round"
```

```mermaid
---
title: "Proposed: how does journal-only history count?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 16
    wrappingWidth: 220
---
flowchart TD
  ROW{{"`**Explicit subscription link?**`"}}
  LINK["`**Link attribution**<br/>Row link wins`"]
  SKIP{{"`**Transfer, income or zero?**`"}}
  MATCH{{"`**Masked description resolves?**`"}}
  ATTR["`**Pattern attribution**<br/>Includes journal-only charges`"]
  NONE["`**No inferred subscription**`"]
  ROW -.->|"Yes: use linked record"| LINK
  ROW -.->|"No: includes journal-only"| SKIP
  SKIP -.->|"Yes: never infer"| NONE
  SKIP -.->|"No: resolve patterns"| MATCH
  MATCH -.->|"Winner"| ATTR
  MATCH -.->|"No winner"| NONE
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class ROW,SKIP,MATCH decision
  class LINK,ATTR outcome
  class NONE muted
```

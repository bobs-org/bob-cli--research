# Diagram proposals: Bank period charts: transaction visualizations for period notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_period_charts/bank_period_charts__final.md
producer: research.4m.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; broken-source control exited nonzero"
```

## coverage-for-started-buckets

```yaml
anchor: |-
  in exact cents; states derive from `coverage`
question: |-
  How is coverage classified once a bucket has started?
illustrates: |-
  For buckets whose start is no later than today, the proposed coverage-envelope rules distinguish untracked, awaiting_import, partial, and tracked without treating missing imports as zero.
caption: For buckets starting by today, tracking and imported-through bounds distinguish untracked, awaiting-import, partial, and tracked; the envelope does not prove continuous coverage.
review: "752.571x832 px, fit 86.7%; question, source tracing, labels, arrowheads, reading direction and visual checks passed; 1 revision, 2 look rounds; future branch excluded by the stated non-future scope"
```

```mermaid
---
title: "Proposed: coverage for non-future buckets"
accTitle: "Proposed bank chart coverage classification"
accDescr: "For a bucket starting no later than today, three conditional checks assign a state using tracking and imported-through bounds. Tracked describes an envelope, not proof of gap-free history."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 170
---
flowchart TD
  PRE{{"`**Ends before tracking began?**`"}}
  IMP{{"`**Starts past import bound?**`"}}
  CROSS{{"`**Crosses either bound?**`"}}
  U["`**Untracked**<br/>Before tracking began`"]
  A["`**Awaiting import**<br/>Beyond imported-through`"]
  P["`**Partial**<br/>Straddles a coverage bound`"]
  T["`**Tracked**<br/>Inside coverage envelope`"]
  PRE -.->|Yes| U
  PRE -.->|No| IMP
  IMP -.->|Yes| A
  IMP -.->|No| CROSS
  CROSS -.->|Yes| P
  CROSS -.->|No| T
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PRE,IMP,CROSS decision
  class U,A,P muted
  class T outcome
  class PRE,IMP,CROSS,U,A,P,T proposed
```

## chart-navigation

```yaml
anchor: |-
  Click/Enter/Space on a column: week → that day's heading in the bank month note
question: |-
  What happens when I activate a chart mark?
illustrates: |-
  Cashflow columns navigate to a day's heading in the bank month note on weeks and to a child period note on larger periods, while category rows remain non-links with tooltips.
caption: Cashflow columns open bank month day headings on weeks and child period notes on larger periods; category rows provide tooltips without navigation.
review: "644.49x538 px, fit 100.0%; question, source tracing, labels, arrowheads, reading direction and visual checks passed; 0 revisions, 1 look round"
```

```mermaid
---
title: "Proposed: how do chart marks navigate?"
accTitle: "Proposed bank chart activation destinations"
accDescr: "Category rows provide tooltips without navigation. Cashflow columns open the bank month's day heading on week notes and a child period note on larger periods."
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 20
    wrappingWidth: 220
---
flowchart TD
  CHART{{"`**Which chart mark?**`"}}
  CATEGORY["`**Category row**<br/>Tooltip only; no navigation`"]
  PERIOD{{"`**Which note period?**`"}}
  DAY["`**Bank month note**<br/>Selected day's heading`"]
  CHILD["`**Child period note**<br/>Selected bucket`"]
  CHART -.->|Category| CATEGORY
  CHART -.->|Cashflow column| PERIOD
  PERIOD -.->|Week| DAY
  PERIOD -.->|Quarter, year, all time| CHILD
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class CHART,PERIOD decision
  class CATEGORY muted
  class DAY,CHILD outcome
  class CHART,PERIOD,CATEGORY,DAY,CHILD proposed
```

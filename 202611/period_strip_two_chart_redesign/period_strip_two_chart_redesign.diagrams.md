# Diagram proposals: Period stats strips: a Roots chart, a Types chart, and a switch that works

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/period_strip_two_chart_redesign/period_strip_two_chart_redesign__final.md
producer: research.41.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 1 of 1 Mermaid diagrams; deliberately broken input exited nonzero"
```

## switch-ownership

```yaml
anchor: |-
  All period strips (week, quarter, year, all time) share it.
question: |-
  Why does today's period switch affect daily notes, and how would separate state fix that?
illustrates: |-
  Period strips keep their own device key and repaint from cache, so a period view change no longer silently flips the Day strips.
caption: A separate period-view key would repaint period strips from cache while daily notes retain their own view.
review: "478.773x1016 px, fit 87.9%; reader question, labels, arrowheads, crossings, reading direction and source trace passed; 1 revision, 2 visual look rounds; batch parse passed"
```

```mermaid
---
title: "Proposed: isolate period-strip view changes"
accTitle: "Current and proposed chart-switch ownership"
accDescr: "Today a period control changes the shared daily view, repainting daily strips while period strips wait for a refetch. The proposal gives period strips a separate device key and cached repaint, leaving daily strips on their existing key."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TB
  subgraph TODAY["Today: one shared view"]
    direction TB
    CLICK["`**Period control**<br/>Click changes view`"]
    SHARED["`**Shared daily view**<br/>One device key`"]
    DAY["`**Day strips**<br/>Repaint immediately`"]
    PERIOD["`**Period strips**<br/>Wait for refetch`"]
    CLICK -->|sets| SHARED
    SHARED -->|repaints| DAY
    SHARED -->|applies at next refetch| PERIOD
  end
  subgraph PROPOSED["Proposed: independent daily and period views"]
    direction TB
    PCLICK["`**Period control**<br/>Click changes view`"]
    PKEY["`**Period view**<br/>Separate device key`"]
    PPERIOD["`**All period strips**<br/>Repaint from cache`"]
    DKEY["`**Daily view**<br/>Existing device key`"]
    PDAY["`**Day strips**<br/>Keep their own view`"]
    PCLICK -.->|sets| PKEY
    PKEY -.->|repaints| PPERIOD
    DKEY -->|governs| PDAY
  end
  TODAY ~~~ PROPOSED
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class CLICK,SHARED,DKEY,PDAY focus
  class DAY,PERIOD risk
  class PCLICK,PKEY,PPERIOD outcome
  class PCLICK,PKEY,PPERIOD proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSED fill:none,stroke:#2E7D4F
```

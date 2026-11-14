# Diagram proposals: Bank badge for the whole stats-strip family

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_badge_strip_family/bank_badge_strip_family__final.md
producer: research.4l.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## period-routing

```yaml
anchor: |-
  keeps its calendar meaning for statements, and help text must name the
question: |-
  Which calendar and history should each bank-report selector use?
illustrates: |-
  The proposed -p option reuses PeriodId::parse for stats-strip periods, retains the calendar meaning of -y, and gives all-time the bank universe instead of the daily-note tree.
caption: Year-strip badges use ISO week-years, while -y keeps calendar years; all-time uses bank history.
review: "613.906x762 px, fit 100.0%; question, source, and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: which dates does a bank badge count?"
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 22
    wrappingWidth: 210
---
flowchart TD
  SELECT{{"`**Which report selector?**`"}}
  CAL["`**Calendar year**<br/>Jan 1 through Dec 31`"]
  PARSE["`**PeriodId parser**<br/>Stats-strip calendar`"]
  ALL{{"`**All-time period?**`"}}
  SPAN["`**Strip span**<br/>Day / ISO week / quarter / year`"]
  HISTORY["`**Bank history**<br/>Earliest account start / row<br/>through today`"]
  SELECT -->|"existing -y YEAR"| CAL
  SELECT -.->|"proposed -p PERIOD"| PARSE
  PARSE -.->|"resolve period kind"| ALL
  ALL -.->|"No"| SPAN
  ALL -.->|"Yes"| HISTORY
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class SELECT,ALL decision
  class PARSE focus
  class CAL,SPAN,HISTORY outcome
  class PARSE,ALL,SPAN,HISTORY proposed
```

## shared-rendering

```yaml
anchor: |-
  and the period-strip fence (badge host appended after the strip root).
question: |-
  What does bob own, and how does one plugin painter serve every host?
illustrates: |-
  bob emits semantics and the plugin derives presentation, with one painter placing sibling badge hosts after the daily-plan Day strip, bob-day-stats, and period-strip fences.
caption: bob supplies values and metadata; one plugin model and painter serve sibling badge hosts after daily-plan, day-stats, and period strips.
review: "683.062x994 px, fit 89.8%; question, source, and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: who supplies and paints every bank badge?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 16
    wrappingWidth: 170
---
flowchart TB
  subgraph BOB["bob CLI owns values"]
    TOTALS["`**Accounting**<br/>Shared totals routine`"]
    REPORT["`**Bank report**<br/>Values / coverage / navigation`"]
    TOTALS -.->|"period totals"| REPORT
  end
  subgraph PLUGIN["Plugin owns presentation"]
    MODEL["`**Shared model**<br/>Visibility / tone / copy`"]
    PAINT["`**Shared painter**<br/>All badge hosts`"]
    DAILY["`**Daily plan**<br/>After Day strip`"]
    DAY["`**Day-stats fence**<br/>After Day strip`"]
    PERIOD["`**Period-strip fence**<br/>After period strip`"]
    MODEL -.->|"render model"| PAINT
    PAINT -.->|"paints sibling badge"| DAILY
    PAINT -.->|"paints sibling badge"| DAY
    PAINT -.->|"paints sibling badge"| PERIOD
  end
  REPORT -.->|"semantic JSON"| PLUGIN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class TOTALS,REPORT focus
  class MODEL,PAINT,DAILY,DAY,PERIOD outcome
  class TOTALS,REPORT,MODEL,PAINT,DAILY,DAY,PERIOD proposed
  style BOB fill:none,stroke:#3B78C2
  style PLUGIN fill:none,stroke:#2E7D4F
```

# Diagram proposals: Day strip vs the previous week: a quiet "typical" line under each number

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/day_strip_vs_previous_week/day_strip_vs_previous_week__final.md
producer: research.5d.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; deliberately broken input exited nonzero"
```

## reference-report-routing

```yaml
anchor: |-
  reuse the cached default report only when
question: |-
  Which report can supply the proposed reference line, and what happens with older bob?
illustrates: |-
  The proposed Day strip reuses only a day-grouped report covering D−7…D, otherwise fetches daily points, and renders bob's supplied reference or keeps a blank reserved line when older bob omits the field.
caption: "For selected day D, reuse requires daily grouping and D−7…D coverage; either route paints bob's fields or reserves a blank line."
review: "527.344x960 px, fit 93.0%; question, source-trace and visual checks passed; 0 revisions; either report route supplies the four numeric facts; dashed paths mark proposed behavior"
```

```mermaid
---
title: "Proposed Day strip: which report supplies the reference?"
accTitle: "Proposed Day strip report selection and older-bob fallback"
accDescr: "A cached report must be daily and cover D minus seven through D. Otherwise fetch a daily report. Either report route uses bob's typical field; if absent, reserve a blank line."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 210
---
flowchart TD
  GROUP{{"`**Cached report day-grouped?**`"}}
  COVER{{"`**Covers D−7 … D?**`"}}
  CACHE["`**Use cached report**<br/>Window already covered`"]
  FETCH["`**Fetch daily report**<br/>D−7 … D`"]
  HAS{{"`**typical field present?**`"}}
  PAINT["`**Paint supplied reference**<br/>No local calculation`"]
  BLANK["`**Keep blank line**<br/>Reserve its space`"]
  GROUP -.->|Yes| COVER
  GROUP -.->|No| FETCH
  COVER -.->|Yes| CACHE
  COVER -.->|No| FETCH
  CACHE -.->|Inspect numeric point| HAS
  FETCH -.->|Inspect numeric point| HAS
  HAS -.->|Yes| PAINT
  HAS -.->|No: older bob| BLANK
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class GROUP,COVER,HAS decision
  class CACHE,FETCH focus
  class PAINT,BLANK muted
  class GROUP,COVER,CACHE,FETCH,HAS,PAINT,BLANK proposed
```

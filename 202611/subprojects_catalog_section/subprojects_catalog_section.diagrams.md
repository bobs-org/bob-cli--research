# Diagram proposals: Sub-projects as a host catalog section — consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/subprojects_catalog_section/subprojects_catalog_section__final.md
producer: research.4j.image
check: "mmdc 12.0.0 via pinned npx, with Puppeteer --no-sandbox and the PDF-mirroring config, rendered 2 of 2 Mermaid diagrams; SVG/PNG reviewed; broken-input check exited nonzero"
```

## cache-selection

```yaml
anchor: |-
  region has an unstruck wikilink row; else fall back to the legacy marker; if both
question: |-
  Which local source can determine whether a parent still has open child projects?
illustrates: |-
  Proposed SUBOPEN readers prefer the catalog over the legacy marker, keep warning rows open, and never let a damaged region imply an empty child set.
caption: Proposed readers prefer the catalog, fall back when absent, and never treat damage or warning rows as proof of completion.
review: "627.072x1008 px, fit 88.6%; question, source trace and visual checks passed; alternative paths converge; 0 revisions"
```

```mermaid
---
title: "Proposed: which child cache can readers trust?"
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 14
    wrappingWidth: 185
---
flowchart TD
  PRESENT{{"`**Projects callout present?**`"}}
  VALID{{"`**Region valid?**`"}}
  LEGACY["`**Legacy marker**<br/>Read child state`"]
  CATALOG["`**Projects callout**<br/>Overrides legacy marker`"]
  DAMAGE["`**Refuse host**<br/>Never infer empty`"]
  OPEN{{"`**Open or warning row?**`"}}
  HOLD["`**Children remain**<br/>Suppress finished offer`"]
  RULES["`**No open children**<br/>Existing eligibility rules apply`"]
  PRESENT -.->|Yes| VALID
  PRESENT -.->|No| LEGACY
  VALID -.->|Yes| CATALOG
  VALID -.->|No| DAMAGE
  CATALOG -.->|Read rows| OPEN
  LEGACY -.->|Read rows| OPEN
  OPEN -.->|Yes| HOLD
  OPEN -.->|No| RULES
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class PRESENT,VALID,OPEN decision
  class LEGACY,CATALOG,HOLD,RULES focus
  class DAMAGE risk
  class PRESENT,VALID,OPEN,LEGACY,CATALOG,DAMAGE,HOLD,RULES proposed
```

## task-to-catalog

```yaml
anchor: |-
  A clean lifecycle task again: criterion, dependencies, logs.
question: |-
  What moves out of the parent lifecycle task, and what stays?
illustrates: |-
  The proposed host catalog moves direct child links out of the lifecycle task into a bob-owned callout beneath a Bryan-owned heading while dependencies stay with the task.
caption: Child links move to a bob-owned callout; dependencies stay under the lifecycle task, and Bryan owns the heading.
review: "474.875x944 px, fit 94.6%; question, source trace and visual checks passed; arrows mean containment; 1 revision to stack the comparison"
```

```mermaid
---
title: "Where do child links move?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 170
---
flowchart TB
  subgraph TODAY["Today: parent note"]
    direction TB
    OLD_TASK["`**Lifecycle task**<br/>Parent outcome`"]
    OLD_DEPS["`**Dependencies**`"]
    OLD_LINKS["`**Child links**<br/>Legacy sub-project bullet`"]
    OLD_TASK -->|Contains| OLD_DEPS
    OLD_TASK -->|Contains| OLD_LINKS
  end
  subgraph PROPOSED["Proposed: parent note"]
    direction TB
    NEW_TASK["`**Lifecycle task**<br/>Parent outcome`"]
    NEW_DEPS["`**Dependencies**`"]
    HEADING["`**Projects heading**<br/>Bryan owns position and prose`"]
    NEW_LINKS["`**Child links**<br/>bob owns projects callout`"]
    CLOSED["`**Closed group**<br/>Folded within callout`"]
    NEW_TASK -.->|Contains| NEW_DEPS
    HEADING -.->|Section contains| NEW_LINKS
    NEW_LINKS -.->|Contains| CLOSED
  end
  TODAY ~~~ PROPOSED
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OLD_TASK,OLD_DEPS,OLD_LINKS,NEW_TASK,NEW_DEPS muted
  class HEADING focus
  class NEW_LINKS,CLOSED outcome
  class NEW_TASK,NEW_DEPS,HEADING,NEW_LINKS,CLOSED proposed
  style TODAY fill:none,stroke:#6B7280
  style PROPOSED fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

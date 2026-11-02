# Diagram proposals: `#off` / `#on` tags and inherited `offclock:` areas

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/off_on_tags_and_offclock_areas/off_on_tags_and_offclock_areas__final.md
producer: research.31.image
check: mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; deliberately broken input
  exited nonzero
```

## explicit-effective

```yaml
anchor: |-
  sent neither, **even if the root inherits off-clock**.
question: |-
  Why must calendar rendering and session planning use different clock facts?
illustrates: |-
  The Google-owned badge span mirrors only explicit tags, while past closed clusters and created running MEETs use the Google tag followed by the chosen or current root's chain.
caption: "Proposed sync renders only explicit Google tags; session planning uses those tags first, then either the chosen or current root\u2019s default."
review: 808.815x788 px, fit 80.7%; question, source, arrow, label and visual checks passed; 1 revision, 2 look rounds; root branches are alternatives, tag
  has priority
```

```mermaid
---
title: "Proposed: which clock facts does calendar sync use?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 190
---
flowchart TB
  GOOGLE["`**Google clock**<br/>Explicit tag or none`"]
  BADGE["`**Task badge**<br/>#off, #on, or none`"]
  NEWQ{{"`**New Event Task?**`"}}
  CHOSEN["`**Chosen root**<br/>New row's note chain`"]
  CURRENT["`**Current root**<br/>Existing row's note chain`"]
  EFFECTIVE["`**Effective clock**<br/>Tag, then root default`"]
  PLAN["`**Session planning**<br/>Group and stamp meeting sessions`"]
  GOOGLE -.->|"renders only explicit intent"| BADGE
  GOOGLE -.->|"first priority"| EFFECTIVE
  NEWQ -.->|"Yes"| CHOSEN
  NEWQ -.->|"No"| CURRENT
  CHOSEN -.->|"note default"| EFFECTIVE
  CURRENT -.->|"note default"| EFFECTIVE
  EFFECTIVE -.->|"determines session clock"| PLAN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class GOOGLE,CHOSEN,CURRENT focus
  class NEWQ,EFFECTIVE decision
  class BADGE,PLAN outcome
  class GOOGLE,CHOSEN,CURRENT,NEWQ,EFFECTIVE,BADGE,PLAN proposed
```

## warning-visibility

```yaml
anchor: |-
  When the daily auto-sync result has a non-empty
question: |-
  How will a deprecation warning reach the user during automatic sync?
illustrates: |-
  Automatic sync currently ignores warnings, while the proposed deprecations[] result raises an Obsidian Notice once per day when non-empty.
caption: Proposed structured deprecations reach a daily Obsidian Notice, making warnings visible when automatic sync runs quietly.
review: 596x577 px, fit 100.0%; question, source, arrow, label and visual checks passed; 1 revision, 2 look rounds; today is left, proposed is right
```

```mermaid
---
title: "How will automatic sync make deprecations visible?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 22
    wrappingWidth: 190
---
flowchart TB
  subgraph PROPOSAL["Proposed: daily-note auto-sync"]
    direction TB
    NEW_SYNC["`**bob gcal sync**<br/>Quiet JSON output`"]
    DEPRECATIONS["`**deprecations[]**<br/>Added alongside warnings[]`"]
    NOTICE["`**Obsidian Notice**<br/>Run bob gcal list`"]
    NEW_SYNC -.->|"returns structured diagnostics"| DEPRECATIONS
    DEPRECATIONS -.->|"non-empty; once per day"| NOTICE
  end
  subgraph TODAY["Today: daily-note auto-sync"]
    direction TB
    OLD_SYNC["`**bob gcal sync**<br/>Quiet JSON output`"]
    OLD_WARN["`**warnings[]**<br/>Warning strings`"]
    IGNORE["`**Obsidian ignores warnings**<br/>Only failures raise Notices`"]
    OLD_SYNC -->|"returns"| OLD_WARN
    OLD_WARN -->|"no warning delivery"| IGNORE
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OLD_SYNC,OLD_WARN,NEW_SYNC,DEPRECATIONS focus
  class IGNORE risk
  class NOTICE outcome
  class NEW_SYNC,DEPRECATIONS,NOTICE proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

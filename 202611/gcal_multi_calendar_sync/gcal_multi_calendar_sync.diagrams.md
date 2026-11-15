# Diagram proposals: Multi-calendar `bob gcal sync`, starting with Birthdays

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gcal_multi_calendar_sync/gcal_multi_calendar_sync__final.md
producer: research.4q.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; batch exit 0; both SVG files measured above 75%"
```

## title-mark-compatibility

```yaml
anchor: |-
  It lost on reliability and blast radius:
question: |-
  Why does a named badge require more coordinated changes than a title mark?
illustrates: |-
  The named badge changes four parse sites across three repos, while the title mark reaches existing title displays without plugin or Mac changes.
caption: Title marks reuse existing displays; named badges require parser changes in all three repositories.
review: "681x696 px, fit 95.9%; question, source trace, labels, arrows and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why put the calendar mark in the title?"
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 16
    wrappingWidth: 190
---
flowchart LR
  subgraph MARKS["Recommended proposal: title marks"]
    direction LR
    TITLE["`**Marked title**<br/>Existing title span`"]
    DISPLAY["`**Existing title displays**<br/>Note, list, Mac agenda`"]
    TITLE -.->|"uses unchanged"| DISPLAY
  end
  subgraph BADGES["Rejected alternative: named badge"]
    direction LR
    BADGE["`**Named badge**<br/>Changed link text`"]
    CLI["`**bob-cli parsers**<br/>Span split; agenda URL`"]
    PLUGIN["`**Obsidian plugin**<br/>Live Preview badge parser`"]
    MAC["`**Mac Capture**<br/>iconLinkEnd parser`"]
    BADGE -.->|"requires changes"| CLI
    BADGE -.->|"requires changes"| PLUGIN
    BADGE -.->|"requires changes"| MAC
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class TITLE focus
  class DISPLAY outcome
  class BADGE,CLI,PLUGIN,MAC risk
  class TITLE,DISPLAY,BADGE,CLI,PLUGIN,MAC proposed
  style MARKS fill:none,stroke:#2E7D4F
  style BADGES fill:none,stroke:#C0392B
```

## removed-calendar-history

```yaml
anchor: |-
  means "stop managing this source" — prior rows and journals stay;
question: |-
  How does the proposed freeze prevent a removed calendar from losing history?
illustrates: |-
  Removing a calendar from config freezes prior rows and journals without a lookup, and re-adding it resumes the same identities instead of losing history to the current false-Moved or Deleted paths.
caption: Freezing a removed calendar preserves rows and journal identities; re-adding it resumes management without the current lookup hazards.
review: "841.578x661 px, fit 77.6%; question, source trace, labels, arrows and visual checks passed after 1 layout revision; second look passed"
```

```mermaid
---
title: "How should removing a calendar affect old rows?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 160
---
flowchart TD
  subgraph TODAY["Today: removed from config"]
    direction TB
    OLD["`**Removed calendar**<br/>Row remains journaled`"]
    LOOKUP["`**Remote event lookup**<br/>Still performed`"]
    MOVED["`**False Moved verdict**<br/>Row removed`"]
    DELETED["`**Deleted verdict**<br/>Calendar unavailable`"]
    OLD -->|"still queries"| LOOKUP
    LOOKUP -->|"day 2+ all-day;<br/>starts != day"| MOVED
    LOOKUP -->|"404 response"| DELETED
  end
  subgraph FUTURE["Proposed: stop managing the source"]
    direction TB
    NEW["`**Removed calendar**<br/>Row remains journaled`"]
    FREEZE["`**Frozen history**<br/>Rows and journal retained`"]
    RESUME["`**Resume management**<br/>Same identities`"]
    NEW -.->|"no lookup"| FREEZE
    FREEZE -.->|"re-add calendar"| RESUME
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class OLD,LOOKUP,NEW focus
  class MOVED,DELETED risk
  class FREEZE,RESUME outcome
  class NEW,FREEZE,RESUME proposed
  style TODAY fill:none,stroke:#C0392B
  style FUTURE fill:none,stroke:#2E7D4F
```

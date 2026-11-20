# Diagram proposals: Explicit micro tasks: consolidated design and recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/explicit_micro_tasks/explicit_micro_tasks__final.md
producer: research.5n.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 3 of 3 Mermaid diagrams; Puppeteer --no-sandbox; deliberately broken input exited nonzero"
```

## keep-open-subtree

```yaml
anchor: |-
  children travel byte for byte, nested micro tasks become the
question: |-
  What moves and what links remain when a micro task is kept open?
illustrates: |-
  Keep open runs Task Split: children travel byte for byte into a new task while the closed parent and carried work retain two-way provenance.
caption: Keep open moves children unchanged into a new task, leaving a carried stub in the owner and a generated backlink in the new task.
review: 676.328x745 px, fit 96.5%; question, labels, arrowheads, reading order and source checks passed; 1 layout revision; 2 visual look rounds
```

```mermaid
---
title: "Proposed: what moves when a step stays open?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 14
    wrappingWidth: 180
---
flowchart TB
  subgraph AFTER["After Keep open and close"]
    direction TB
    AOWNER["`**Owner task**<br/>Closed`"]
    STUB["`**Carried stub**<br/>Stored as #91;>#93;`"]
    NEW["`**New task**<br/>Own identity`"]
    ACHILD["`**Same children**<br/>Micro tasks now top-level`"]
    AOWNER -.->|contains| STUB
    STUB -.->|links to| NEW
    NEW -.->|LINKED FROM| AOWNER
    NEW -.->|contains| ACHILD
  end
  subgraph BEFORE["Before Keep open"]
    direction TB
    BOWNER["`**Owner task**<br/>Still open`"]
    BMICRO["`**Micro task**<br/>Chosen to stay open`"]
    BCHILD["`**Children**<br/>Nested micro tasks + notes`"]
    BOWNER -.->|contains| BMICRO
    BMICRO -.->|contains| BCHILD
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class BOWNER,BMICRO,BCHILD focus
  class NEW,ACHILD outcome
  class AOWNER,STUB muted
  style BEFORE fill:none,stroke:#3B78C2
  style AFTER fill:none,stroke:#2E7D4F
```

## close-card-routing

```yaml
anchor: |-
  closing tree contains a task with ≥ 1 **open top-level** micro task
question: |-
  Which closes produce a micro-task review card, and which use reader fallback?
illustrates: |-
  Managed Done gestures put open top-level micro tasks first on the existing successor card, while bypasses leave micro states unwritten and use the reader rule.
caption: Managed Done gestures audit open top-level micro tasks; other exits leave micro bytes untouched and use the reader rule.
review: 705.944x832 px, fit 92.5%; question, labels, arrowheads, branches and source checks passed; 0 revisions; 1 visual look round
```

```mermaid
---
title: "Proposed: when does the close card appear?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 160
---
flowchart TD
  DONE{{"`**Managed Done gesture?**`"}}
  OPEN{{"`**Open top-level micro tasks?**`"}}
  OTHER{{"`**Other offers exist?**`"}}
  MICRO["`**Existing card**<br/>Micro tasks first`"]
  OFFERS["`**Existing card**<br/>Resolved micros fold away`"]
  NOCARD["`**No card**`"]
  BYPASS["`**No micro-state writes**<br/>Bypass the card`"]
  READER["`**Reader rule**<br/>Resolved parent supplies state`"]
  DONE -.->|Yes| OPEN
  DONE -.->|No| BYPASS
  BYPASS -.->|read without writing| READER
  OPEN -.->|Yes| MICRO
  OPEN -.->|No| OTHER
  OTHER -.->|Yes| OFFERS
  OTHER -.->|No| NOCARD
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class DONE,OPEN,OTHER decision
  class MICRO,OFFERS outcome
  class BYPASS,READER,NOCARD muted
```

## capture-dot-contexts

```yaml
anchor: |-
  currently literal at bullet-body starts. Two exceptions stand: sealed project-note
question: |-
  When do typed dots create a micro task, and when are dots kept or handled by existing aliases?
illustrates: |-
  The .. micro alias applies at eligible bullet-body starts, while sealed project-note Move, item-start escape, paste, templates and bob capture retain their existing behavior.
caption: Only eligible bullet-body typing gains the micro alias; project Move, item-start escape, and non-typed dots keep existing behavior.
review: 643.857x658 px, fit 100.0%; question, labels, arrowheads, contexts and source checks passed; 0 revisions; 1 visual look round
```

```mermaid
---
title: "Proposed: which dot contexts change?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 14
    wrappingWidth: 150
---
flowchart TD
  TYPED{{"`**Typing in the editor?**`"}}
  CONTEXT{{"`**Which caret context?**`"}}
  LITERAL["`**Literal dots**<br/>Paste, templates, CLI`"]
  MICRO["`**Micro alias**<br/>.. becomes #91; #93;`"]
  MOVE["`**Existing Move alias**<br/>- . becomes - ^`"]
  ESCAPE["`**Existing dot escape**<br/>.. keeps .bashrc literal`"]
  TYPED -.->|No| LITERAL
  TYPED -.->|Yes| CONTEXT
  CONTEXT -.->|eligible micro<br/>bullet body| MICRO
  CONTEXT -.->|sealed project-note<br/>first-level bullet| MOVE
  CONTEXT -.->|item start| ESCAPE
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class TYPED,CONTEXT decision
  class MICRO outcome
  class LITERAL,MOVE,ESCAPE muted
```

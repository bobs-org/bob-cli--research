# Diagram proposals: Better o / Ctrl+Shift+O and gesture-settled task structure

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/better_o_gesture_settle/better_o_gesture_settle__final.md
producer: research.66.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox"
```

## settle-timing

```yaml
anchor: |-
  rapid `Alt+]`/`Alt+[` cycling so a double-tap never mutates the wrong line or yanks
question: |-
  When should regrouping run immediately, and when should rapid cycling wait?
illustrates: |-
  The two-tier regroup policy separates immediate atomic regroup on discrete commits from settle-on-idle for rapid cycling, with cursor-leave, note-leave, or the next command flushing the wait.
caption: Proposed regrouping runs immediately for discrete commits; rapid cycling waits for idle or an early flush, with one undo for gesture and regroup.
review: "624.714×986 px, fit 90.5%; question and visual checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed: when does regrouping run?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  KIND{{"`**Which gesture?**`"}}
  NOW["`**Discrete commit**<br/>Close, answer, move, or card`"]
  CYCLE["`**Rapid status cycling**<br/>Alt+] / Alt+[`"]
  IMMEDIATE["`**Regroup immediately**<br/>Atomic with gesture`"]
  TRIGGER{{"`**What ends the wait?**`"}}
  PAUSE["`**Idle pause**<br/>About 500 ms`"]
  LEAVE["`**Flush early**<br/>Cursor/note leave or next command`"]
  SETTLE["`**Apply regroup**<br/>One undo with gesture`"]
  KIND -.->|Discrete| NOW
  KIND -.->|Rapid cycling| CYCLE
  NOW -.->|Commit| IMMEDIATE
  CYCLE -.->|Wait for either trigger| TRIGGER
  TRIGGER -.->|Idle| PAUSE
  TRIGGER -.->|Leave or command| LEAVE
  PAUSE -.->|Either trigger| SETTLE
  LEAVE -.->|Either trigger| SETTLE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class KIND,TRIGGER decision
  class NOW,CYCLE,PAUSE,LEAVE focus
  class IMMEDIATE,SETTLE outcome
  class KIND,TRIGGER,NOW,CYCLE,PAUSE,LEAVE,IMMEDIATE,SETTLE proposed
```

## mirror-race

```yaml
anchor: |-
  edit but never checks that the editor still shows `snapshot.parentPath`. During the
question: |-
  How can a delayed mirror callback corrupt another note and poison the baseline cache?
illustrates: |-
  The delayed mention mirror can read an editor that has moved to another note, write phantom LINKED FROM mentions, and cache the new note’s bytes under the old path.
caption: Without a note-path check, a delayed mirror can write phantom mentions and cache the new note’s bytes under the old path.
review: "547×740 px, fit 100.0%; question and visual checks passed; 1 visual revision to keep the title inside the canvas; 1 parse correction"
```

```mermaid
---
title: "Why can the mirror corrupt?"
config:
  sequence:
    actorMargin: 16
    diagramMarginX: 8
    diagramMarginY: 8
    messageMargin: 24
    noteMargin: 8
    width: 120
    wrap: true
---
sequenceDiagram
  autonumber
  participant EDITOR as Shared editor
  participant MIRROR as Mirror callback
  participant VAULT as Vault notes
  participant CACHE as Baseline cache
  EDITOR->>MIRROR: Edit note A and arm 400 ms timer
  EDITOR->>EDITOR: Walk switches to note B
  MIRROR->>EDITOR: Timer fires with no note-path check
  EDITOR-->>MIRROR: Current bytes are from note B
  MIRROR->>VAULT: Writes phantom LINKED FROM mentions
  MIRROR->>CACHE: Re-arm / finally: store B bytes under A path
  Note over MIRROR,CACHE: Poisoned baseline also affects the dependency mirror
```

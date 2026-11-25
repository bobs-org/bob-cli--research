# Diagram proposals: Snoozed Task Links (`^snoozed-tasks`)

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/snoozed_task_links/snoozed_task_links__final.md
producer: research.67.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 3 of 3 Mermaid diagrams; malformed-input control exited nonzero"
```

## snoozed-task-lifecycle

```yaml
anchor: |-
  execution APIs must not grow fake membership. gem's two real concerns are solved
question: |-
  What changes when a task is snoozed, wakes, or remains unwoken overnight?
illustrates: |-
  Snoozed is not Today until wake, while yesterday's unwoken rows remain history and sticky Next tasks resurface in the normal review walk.
caption: Snoozing commits the task without making it Today; wake links it, while missed-day tasks return through review.
review: "540×814 px, fit 100.0%; question, source trace, labels, arrows, and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when is a snoozed task Today?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  GESTURE["`**Human snooze**<br/>Ready becomes Next; stamp freshness`"]
  PARKED["`**Snoozed today**<br/>Not Today; excluded from review`"]
  TODAY["`**Today**<br/>Untimed open Pomodoro link`"]
  HISTORY["`**Yesterday's row**<br/>History; no automatic carry`"]
  REVIEW["`**Normal review walk**<br/>Sticky Next task resurfaces`"]
  GESTURE -.->|"parks the link"| PARKED
  PARKED -.->|"eligible automatic wake;<br/>no fresh stamp"| TODAY
  PARKED -.->|"still unwoken at midnight"| HISTORY
  HISTORY -.->|"today-only exclusion expires"| REVIEW
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class GESTURE,PARKED focus
  class TODAY,REVIEW outcome
  class HISTORY muted
  class GESTURE,PARKED,TODAY,HISTORY,REVIEW proposed
```

## automatic-wake-placement

```yaml
anchor: |-
  on a plain `x` close, every unstruck plain link in the closing entry is
question: |-
  Why must automatic wake bypass a running session?
illustrates: |-
  Automatic wake bypasses the running entry because a plain x close would record an untouched woken link as worked.
caption: Automatic wake uses untimed destinations so a plain x close cannot falsely record untouched tasks as worked.
review: "679.031×577 px, fit 96.1%; question, source trace, labels, arrows, and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "Why must automatic wake bypass a running session?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  subgraph SAFE["Proposed: untimed-only automatic wake"]
    direction TB
    S1["`**Woken task link**<br/>Bypass running Pomodoro`"]
    S2["`**Untimed open destination**<br/>Matching entry or new placeholder`"]
    S1 -.->|"seek matching destination"| S2
  end
  subgraph UNSAFE["Risk: reuse running-first placement"]
    direction TB
    R1["`**Woken task link**<br/>Placed in running Pomodoro`"]
    R2["`**Plain x close**<br/>Records every unstruck plain link`"]
    R3["`**False worked record**<br/>Untouched task marked in progress`"]
    R1 -->|"a later close includes it"| R2
    R2 -->|"awards recorded time"| R3
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class R1,R2 focus
  class R3 risk
  class S1,S2 outcome
  class S1,S2 proposed
  style UNSAFE fill:none,stroke:#C0392B
  style SAFE fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

## release-cleanup-parity

```yaml
anchor: |-
  released/completed tasks at wake (plugin gestures only clean `## Pomodoros`), or
question: |-
  Why must gesture cleanup cover Snoozed as well as Pomodoros?
illustrates: |-
  Gesture cleanup must prune snoozed rows in the same release as authoring, or a released task can be revived by a timer.
caption: Extend gesture cleanup to Snoozed before authoring ships, or a released task can be revived by a later wake.
review: "730.484×577 px, fit 89.4%; question, source trace, labels, arrows, and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "Why must release cleanup include Snoozed?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  subgraph FIX["Proposed: same-release cleanup parity"]
    direction TB
    N1["`**Release gesture**<br/>Shared helper includes Snoozed`"]
    N2["`**Snoozed row pruned**<br/>No timer entry remains`"]
    N3["`**Release stays effective**<br/>Wake cannot revive this row`"]
    N1 -.->|"removes the queued link"| N2
    N2 -.->|"prevents later timer revival"| N3
  end
  subgraph GAP["Risk: authoring ships before cleanup parity"]
    direction TB
    O1["`**Release gesture**<br/>Cleanup scans only Pomodoros`"]
    O2["`**Snoozed row remains**<br/>Outside the cleanup boundary`"]
    O3["`**Timer revival risk**<br/>Released task can return`"]
    O1 -->|"misses the snoozed row"| O2
    O2 -->|"a later wake sees it"| O3
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class O1,O2 focus
  class O3 risk
  class N1,N2,N3 outcome
  class N1,N2,N3 proposed
  style GAP fill:none,stroke:#C0392B
  style FIX fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

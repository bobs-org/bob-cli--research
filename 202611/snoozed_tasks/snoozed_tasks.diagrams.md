# Diagram proposals: Snoozed Tasks: consolidated design for the modified feature

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/snoozed_tasks/snoozed_tasks__final.md
producer: research.69.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 3 of 3 Mermaid diagrams"
```

## timed-wake-lifecycle

```yaml
anchor: |-
  Concurrent callers are safe through the vault lock plus idempotency; contention returns
question: |-
  Why can a snoozed task stay due, or never wake today?
illustrates: |-
  A passed target is due until eligible placement commits; blocked or busy wakes retry, released or completed tasks leave the queue, and unwoken rows become history at midnight.
caption: "Timed wakes wait for safe placement; released or completed tasks leave the queue, while unwoken rows become history at midnight."
review: "640.609x619 px, fit 100.0%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: why can a snoozed task stay due?"
---
stateDiagram-v2
  direction TB
  state "Unwoken today" as WAITING {
    state "Sleeping until target" as SLEEPING
    state "Due: placement pending" as DUE
    SLEEPING --> DUE: Target time passes
    DUE --> DUE: Blocked or busy: retry
  }
  state "Ready: placed in today's ledger" as WOKEN
  state "Removed from queue" as REMOVED
  state "History: no automatic carry" as HISTORY
  DUE --> WOKEN: Eligible and write committed
  WAITING --> REMOVED: Task released or completed
  WAITING --> HISTORY: Midnight, still unwoken
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef boundary fill:none,stroke:#6B7280,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class SLEEPING,REMOVED,HISTORY muted
  class DUE decision
  class WOKEN outcome
  class WAITING boundary
  class WAITING proposed
```

## wake-provenance

```yaml
anchor: |-
  the struck row preserves **both** times — the bold target
question: |-
  What moves at wake, and what retains the wake time?
illustrates: |-
  The link and its child notes move into an untimed entry while the struck Snoozed history retains the target and actual wake time that drives the display-only Task Link pill.
caption: "Wake moves the link and notes into an untimed Pomodoro session entry; retained Snoozed history supplies the display-only wake-time pill."
review: "808.75x902.5 px, fit 80.7%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: what moves when a task wakes?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 190
---
flowchart TD
  subgraph SLEEP["Sleeping: Snoozed section"]
    ROW["`**Live row**<br/>Target time + task link`"]
    NOTES["`**Child notes**<br/>Beneath the row`"]
  end
  subgraph WAKE["After committed wake"]
    HISTORY["`**Snoozed history**<br/>Struck: target + actual wake time`"]
    subgraph LEDGER["Untimed Pomodoro entry"]
      LINK["`**Canonical task link**<br/>No inline wake marker`"]
      MOVED["`**Child notes**<br/>Beneath the link`"]
    end
    PILL["`**Task-link pill**<br/>Actual wake time; display-only`"]
  end
  ROW -.->|retain target; record wake| HISTORY
  ROW -.->|move link to entry top| LINK
  NOTES -.->|move with link| MOVED
  HISTORY -.->|provides time for| PILL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class ROW,NOTES focus
  class LINK,MOVED,PILL outcome
  class HISTORY muted
  style SLEEP fill:none,stroke:#3B78C2
  style WAKE fill:none,stroke:#2E7D4F
  style LEDGER fill:none,stroke:#2E7D4F
```

## snooze-write-ownership

```yaml
anchor: |-
  conformance vectors, writing through the live editor transaction when the note is open
question: |-
  Which snooze write path preserves Obsidian undo while other clients use bob?
illustrates: |-
  Alt+Z uses a pure JavaScript planner with an editor transaction for open notes and preimage-checked vault.process for closed notes, while capture and scripts use bob snooze add against the same conformance vectors.
caption: "Obsidian preserves undo through its JavaScript planner; other clients use bob, with both implementations tested against shared conformance vectors."
review: "761.109x869 px, fit 85.8%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: which snooze writer preserves undo?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 165
---
flowchart TD
  subgraph OBS["Obsidian gesture"]
    JS["`**Alt+Z**<br/>Pure JavaScript planner`"]
    OPEN{{"`**Note open?**`"}}
    EDITOR["`**Live editor transaction**<br/>One-step undo`"]
    CLOSED["`**vault.process**<br/>Preimage checked`"]
    JS -.->|selects write path| OPEN
    OPEN -.->|Yes| EDITOR
    OPEN -.->|No| CLOSED
  end
  subgraph CLI["Capture, scripts, other hosts"]
    RUST["`**bob snooze add**<br/>Rust writer`"]
  end
  VECTORS["`**Shared conformance vectors**<br/>Same snooze contract`"]
  VECTORS -.->|tests| JS
  VECTORS -.->|tests| RUST
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class JS,RUST,VECTORS focus
  class OPEN decision
  class EDITOR,CLOSED outcome
  style OBS fill:none,stroke:#3B78C2
  style CLI fill:none,stroke:#3B78C2
```

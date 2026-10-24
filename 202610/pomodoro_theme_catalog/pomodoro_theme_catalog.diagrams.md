# Diagram proposals: Pomodoro themes: a shared catalog with today-first suggestions, hiding, safe rename, and stable colors

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/pomodoro_theme_catalog/pomodoro_theme_catalog__final.md
producer: research.2c.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## hide-lifecycle

```yaml
anchor: |-
  On failure it restores the row and reports in the status
question: |-
  What happens after hiding a history suggestion, including undo and write failure?
illustrates: |-
  The hidden ghost row supports Ctrl+D undo and write-failure recovery, while using a hidden name never silently unhides it.
caption: "Hiding supports undo and failure recovery; using the name keeps it hidden from history suggestions, while today's entries stay visible."
review: "620.776x802 px, fit 100.0%; question, arrows, labels, crossings, and source checks passed; 1 revision across 2 visual look rounds; unique body anchor confirmed"
```

```mermaid
---
title: "Proposed: what happens after hiding a theme?"
config:
  state:
    padding: 12
---
stateDiagram-v2
  direction TB
  state "Visible history suggestion" as VISIBLE
  state "Hidden ghost row<br/>Ctrl+D undo" as GHOST
  state "Hidden theme<br/>Absent from history suggestions" as HIDDEN
  state "Hidden-name create row" as CREATE
  VISIBLE --> GHOST: Ctrl+D / request hide
  GHOST --> VISIBLE: Ctrl+D / undo
  GHOST --> VISIBLE: Hide fails / restore row, report error
  GHOST --> HIDDEN: Next keystroke / re-query
  HIDDEN --> CREATE: Type creatable name / no exact Today match
  CREATE --> VISIBLE: Ctrl+D / unhide
  CREATE --> HIDDEN: Use the name / stays hidden
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class VISIBLE focus
  class GHOST,HIDDEN,CREATE muted
  class VISIBLE,GHOST,HIDDEN,CREATE proposed
```

# Diagram proposals: Task theme suggestions: inherit a default, explain it, remember the exceptions

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/task_theme_suggestions_and_overrides/task_theme_suggestions_and_overrides__final.md
producer: research.2s.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## cross-note-link-failure

```yaml
anchor: |-
  Cross-note links keep the existing order
question: |-
  How does a cross-note link prevent stale writes and expose partial failure?
illustrates: |-
  Cross-note links keep the task-note-first order, while guards, changed inputs, and failed daily-note writes lead to different visible outcomes.
caption: "For an eligible theme change, guards and stale inputs stop writes; a failed daily-note write must explicitly report the saved theme."
review: "844.867x714 px, fit 77.3%; question, source tracing, arrowheads, labels, reading direction, and visual checks passed; 1 spacing/label revision; 1 visual look round"
```

```mermaid
---
title: "Proposed: can a theme save without its link?"
accTitle: "Cross-note linking checks and partial failure"
accDescr: "For an eligible theme change, a guarded link writes nothing, changed inputs require another Enter, and a successful task-note edit precedes the daily-note link. If that second write fails, the notice must report the saved theme and failed link."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 200
---
flowchart TD
  GATE{{"`**Allowed and current?**`"}}
  STOP["`**Guard refuses**<br/>No link; no field change`"]
  REFRESH["`**Inputs changed**<br/>Refresh; Enter again`"]
  TASK["`**Save task note**<br/>Include theme edit`"]
  DAILY{{"`**Daily write succeeds?**`"}}
  OK["`**Confirm link**<br/>Name theme change`"]
  FAIL["`**Partial failure**<br/>Theme saved; link failed`"]
  GATE -.->|"Guard refuses"| STOP
  GATE -.->|"Inputs changed"| REFRESH
  GATE -.->|"Allowed + unchanged"| TASK
  TASK -.->|"Then write daily link"| DAILY
  DAILY -.->|"Yes"| OK
  DAILY -.->|"No"| FAIL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class STOP,REFRESH,TASK,OK focus
  class GATE,DAILY decision
  class FAIL risk
  class GATE,STOP,REFRESH,TASK,DAILY,OK,FAIL proposed
```

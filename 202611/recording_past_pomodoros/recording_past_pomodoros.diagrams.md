# Diagram proposals: Recording past Pomodoros with `x=`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/recording_past_pomodoros/recording_past_pomodoros__final.md
producer: research.38.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; deliberate invalid syntax exited nonzero"
```

## explicit-past-entry

```yaml
anchor: |-
  Run the existing close engine on an **explicit entry** at clock `C`. Today the
question: |-
  Why must the close engine take an explicit past entry?
illustrates: |-
  An explicit entry at clock C avoids the global lookup that would report two open timed entries beside an adjacent running session.
caption: "Global lookup sees both timed rows; passing the past row explicitly closes at min(window end, now) while protecting the running session."
review: "718×481 px, fit 90.9%; question and visual checks passed; 0 revisions; both global-lookup inputs are considered; source trace checked"
```

```mermaid
---
title: "Why pass the past row directly to the close engine?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 14
    wrappingWidth: 180
---
flowchart TB
  subgraph GLOBAL["Global lookup, if reused"]
    direction TB
    GP["`**Past row**<br/>Timed, staged`"]
    GL["`**Running row**<br/>Timed, open`"]
    LOOKUP["`**Global lookup**<br/>Sees both timed rows`"]
    GP -->|considers| LOOKUP
    GL -->|considers| LOOKUP
  end
  subgraph EXPLICIT["Explicit entry (proposed)"]
    direction TB
    EP["`**Past row**<br/>Timed, staged`"]
    EL["`**Running row**<br/>Protected; not selected`"]
    CLOSE["`**Close engine**<br/>C = min(end, now)`"]
    EP -.->|uses this handle| CLOSE
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class GP,GL,EP focus
  class LOOKUP risk
  class EL,CLOSE outcome
  class EP,EL,CLOSE proposed
  style GLOBAL fill:none,stroke:#C0392B
  style EXPLICIT fill:none,stroke:#2E7D4F
```

## whole-stack-repair

```yaml
anchor: |-
  Checking the whole stack at once matters. Take `x=build@2! x=fix@3!` against PLAN
question: |-
  Why can a safe stack look like a forbidden split when checked one token at a time?
illustrates: |-
  Checking the whole stack trims PLAN's tail to 0855–0900, whereas checking BUILD alone would look like a split of PLAN.
caption: "For `x=build@2! x=fix@3!`, whole-stack validation trims PLAN to 08:55–09:00; checking BUILD alone falsely suggests a split."
review: "527.25×553 px, fit 100.0%; question and visual checks passed; 1 revision to keep each time range on one line; source trace checked"
```

```mermaid
---
title: "Why validate the whole stack before trimming?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 14
    wrappingWidth: 200
---
flowchart TB
  subgraph ISOLATED["Isolated token (wrong check)"]
    direction TB
    IP["`**Closed PLAN**<br/>08:55–09:20`"]
    IW["`**BUILD only**<br/>09:00–09:10`"]
    IR["`**Two PLAN pieces**<br/>08:55–09:00<br/>09:10–09:20<br/>Refuse: split`"]
    IP -->|subtract window| IW
    IW -->|leaves| IR
  end
  subgraph STACK["Whole stack (proposed)"]
    direction TB
    SP["`**Closed PLAN**<br/>08:55–09:20`"]
    SW["`**BUILD + FIX**<br/>09:00–09:25`"]
    SR["`**One PLAN piece**<br/>08:55–09:00<br/>Allowed: edge trim`"]
    SP -.->|subtract both windows| SW
    SW -.->|leaves| SR
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class IP,IW,SP,SW focus
  class IR risk
  class SR outcome
  class SP,SW,SR proposed
  style ISOLATED fill:none,stroke:#C0392B
  style STACK fill:none,stroke:#2E7D4F
```

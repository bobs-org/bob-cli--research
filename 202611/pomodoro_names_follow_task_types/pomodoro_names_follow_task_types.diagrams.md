# Diagram proposals: Pomodoro names follow task types

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/pomodoro_names_follow_task_types/pomodoro_names_follow_task_types__final.md
producer: research.5q.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## carried-task-lookup

```yaml
anchor: |-
  writes the field anyway, which creates I1 drift.
question: |-
  Why does the Task Card miss a carried task's live link, and what changes in the fix?
illustrates: |-
  A carried task's closed entry and open continuation make the current lookup return multiple, while the proposed lookup searches open entries by note and block ID to find the live link.
caption: Closed-session links create false ambiguity; the proposed lookup excludes them and identifies the live link by note plus block ID.
review: "741.438x565 px, fit 88.0%; question and visual checks passed; 1 revision; unique anchor verified"
```

```mermaid
---
title: "Why does the Task Card miss a carried link?"
accTitle: "Current lookup versus proposed open-entry lookup"
accDescr: "Today both a closed-session link and its open continuation match by block ID, so lookup returns multiple and skips relocation. The proposed fix excludes closed entries and searches by note and block ID, finding the live link."
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 12
    wrappingWidth: 180
---
flowchart TB
  subgraph CURRENT["Today: both entries count"]
    direction TB
    CH["`**Closed entry**<br/>Worked link`"]
    CL["`**Open entry**<br/>Live link`"]
    CM["`**Block ID only**<br/>Multiple matches`"]
    CS["`**Type mismatch**<br/>Field changes;<br/>relocation skipped`"]
    CH -->|counted| CM
    CL -->|counted| CM
    CM -->|causes| CS
  end
  subgraph PROPOSAL["Proposed: closed entries excluded"]
    direction TB
    PL["`**Open entry**<br/>Live link`"]
    PM["`**Note + block ID**<br/>Finds live link`"]
    PS["`**Relocation available**<br/>Update live ledger`"]
    PL -.->|searched by| PM
    PM -.->|permits| PS
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class CH,CL,PL focus
  class CM,CS risk
  class PM,PS outcome
  class PL,PM,PS proposed
  style CURRENT fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

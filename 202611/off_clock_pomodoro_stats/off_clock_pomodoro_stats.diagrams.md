# Diagram proposals: Off-Clock Pomodoros: record the time, count it apart

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/off_clock_pomodoro_stats/off_clock_pomodoro_stats__final.md
producer: research.2z.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## off-clock-write-gate

```yaml
anchor: |-
  until the P3 writers are deployed with `bob plugins sync`.
question: |-
  When may new off-clock writes begin?
illustrates: |-
  P1 must not write `[off::]` until P3 writers are deployed, and P1 readers accept bare and `[off::]` rows.
caption: New off-clock writes wait for compatible readers and deployed plugin writers; both prerequisites are required.
review: "548.809x764 px, fit 100.0%; question, visual, source-trace and unique-anchor checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed rollout: when may off-clock writes begin?"
accTitle: "Compatibility gate for off-clock ledger writes"
accDescr: "Both compatibility prerequisites are required. Bob readers must accept bare and off-key rows, and compatible plugin writers must be deployed with bob plugins sync. Until both are ready, hold off-key writes; when both are ready, enable them."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 22
    wrappingWidth: 220
---
flowchart TD
  READ["`**P1 readers**<br/>Accept bare and [off::] rows`"]
  PLUGIN["`**P3 plugin writers**<br/>Preserve the clock key`"]
  SYNC["`**Deploy plugin writers**<br/>bob plugins sync`"]
  GATE{{"`**Both prerequisites ready?**`"}}
  HOLD["`**Hold [off::] writes**<br/>Compatibility incomplete`"]
  WRITE["`**Enable [off::] writes**<br/>Compatible readers and writers`"]
  PLUGIN -.->|"deploy with"| SYNC
  READ -.->|"reader prerequisite"| GATE
  SYNC -.->|"writer prerequisite"| GATE
  GATE -.->|"No"| HOLD
  GATE -.->|"Yes: both"| WRITE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class READ,PLUGIN,SYNC focus
  class GATE,HOLD decision
  class WRITE outcome
  class READ,PLUGIN,SYNC,GATE,HOLD,WRITE proposed
```

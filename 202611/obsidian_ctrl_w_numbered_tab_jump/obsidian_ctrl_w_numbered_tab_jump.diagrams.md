# Diagram proposals: `Ctrl+W N`: numbered tab hints and an in-place jump for the Obsidian window prefix

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/obsidian_ctrl_w_numbered_tab_jump/obsidian_ctrl_w_numbered_tab_jump__final.md
producer: research.4y.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox; broken syntax correctly rejected"
```

## delayed-focus-safety

```yaml
anchor: |-
  A canceled or superseded async load must never apply late focus
question: |-
  How does a delayed tab load avoid stealing focus, and what happens if focus checks fail?
illustrates: |-
  The executor loads the original leaf before focusing, prevents canceled or superseded loads from applying late focus, and refocuses the source on failed active-target, parent, source-selection or leaf-count checks.
caption: Only a current session may apply focus after loading; failed focus or layout checks restore source focus and show one notice.
review: "552.27×906 px, fit 98.5%; question, source tracing and PNG visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed jump: what makes delayed focus safe?"
accTitle: "Delayed tab-load and focus-failure safeguards"
accDescr: "After loading a deferred tab, only the current session may focus it. The executor checks that the target is active and that its parent, the source split selection and the main-area leaf count are unchanged. On failure it refocuses the source and shows a notice."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 170
---
flowchart TD
  LOAD["`**Load original tab**<br/>If deferred`"]
  SESSION{{"`**Session still current?**`"}}
  SKIP["`**Skip late focus**<br/>Canceled or superseded`"]
  FOCUS["`**Focus original tab**<br/>In its own split`"]
  CHECK{{"`**All invariants hold?**`"}}
  KEEP["`**Target active**<br/>Parent, source selection,<br/>leaf count unchanged`"]
  RESTORE["`**Refocus source**<br/>Show one notice`"]
  LOAD -.-> SESSION
  SESSION -.->|No| SKIP
  SESSION -.->|Yes| FOCUS
  FOCUS -.-> CHECK
  CHECK -.->|Yes| KEEP
  CHECK -.->|No| RESTORE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class LOAD,FOCUS,KEEP focus
  class SESSION,CHECK decision
  class SKIP,RESTORE risk
  class LOAD,SESSION,SKIP,FOCUS,CHECK,KEEP,RESTORE proposed
```

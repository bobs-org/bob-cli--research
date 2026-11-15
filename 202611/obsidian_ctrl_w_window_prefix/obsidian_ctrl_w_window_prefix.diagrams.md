# Diagram proposals: A Ctrl+W window prefix for Obsidian vertical splits

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/obsidian_ctrl_w_window_prefix/obsidian_ctrl_w_window_prefix__final.md
producer: research.4v.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox"
```

## move-safeguards

```yaml
anchor: |-
  The unofficial surface needed is small
question: |-
  What prevents an unsafe tab move from silently losing editor state?
illustrates: |-
  The spike gates lossless reparenting, the upgrade canary disables H/L when internals are missing, and failed move invariants restore the source tab.
caption: After a successful spike, missing layout APIs (application programming interfaces) disable moves; failed post-move checks restore the source tab.
review: "849.072x938 px, fit 76.9%; question, source trace and visual checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed safeguards for lossless tab moves"
accTitle: "Lossless tab move safeguards"
accDescr: "The spike gates release, missing layout APIs disable moves, and failed move invariants restore the tab to its source."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 220
---
flowchart TD
  SPIKE{{"`**Spike proves lossless moves?**`"}}
  WAIT["`**Focus and duplicate only**<br/>Move keys wait`"]
  API{{"`**Layout APIs available?**`"}}
  DISABLE["`**Disable H / L**<br/>Explain layout API change`"]
  MOVE["`**Reparent the same tab**<br/>Keep its live editor`"]
  CHECK{{"`**Move invariants hold?**`"}}
  DONE["`**Moved tab focused**<br/>Content count unchanged`"]
  RESTORE["`**Restore tab to source**<br/>Show one notice`"]
  SPIKE -.->|Yes: release moves| API
  SPIKE -.->|No: defer moves| WAIT
  API -.->|Available: perform move| MOVE
  API -.->|Missing: block moves| DISABLE
  MOVE -.->|Verify after every move| CHECK
  CHECK -.->|Yes: keep result| DONE
  CHECK -.->|No: recover| RESTORE
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class SPIKE,API,CHECK decision
  class MOVE,DONE outcome
  class WAIT,DISABLE,RESTORE risk
  class SPIKE,API,CHECK,MOVE,DONE,WAIT,DISABLE,RESTORE proposed
```

## arming-contexts

```yaml
anchor: |-
  arms the prefix when either: focus is in a Markdown editor
question: |-
  When should a qualifying Ctrl+W arm instead of passing through?
illustrates: |-
  The prefix arms in normal or visual Markdown editors or non-editable views, while blocked contexts and pending Vim operators or counts pass through untouched.
caption: For qualifying keypresses, either eligible view may arm; overlays, pending Vim operators/counts, and other text entry pass through.
review: "661.507x852 px, fit 98.7%; question, source trace and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "Proposed Ctrl+W focus gate"
accTitle: "Proposed Ctrl+W focus gate"
accDescr: "For a qualifying Ctrl+W keypress, blocked interactions pass through. Normal or visual Markdown Vim editors and non-editable views may arm the prefix."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 220
---
flowchart TD
  BLOCK{{"`**Blocked interaction?**<br/>Overlay or pending Vim operator/count`"}}
  EDITOR{{"`**Focused Markdown editor?**`"}}
  MODE{{"`**Vim normal or visual?**`"}}
  VIEW{{"`**Non-editable focus?**`"}}
  ARM["`**Arm prefix**<br/>Either eligible view`"]
  PASS["`**Pass through**<br/>Any exclusion passes through`"]
  BLOCK -.->|Yes| PASS
  BLOCK -.->|No| EDITOR
  EDITOR -.->|Yes| MODE
  EDITOR -.->|No| VIEW
  MODE -.->|Yes| ARM
  MODE -.->|No| PASS
  VIEW -.->|Yes| ARM
  VIEW -.->|No| PASS
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class BLOCK,EDITOR,MODE,VIEW decision
  class ARM outcome
  class PASS muted
  class BLOCK,EDITOR,MODE,VIEW,ARM,PASS proposed
```

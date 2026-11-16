# Diagram proposals: Schema Editors: Emoji Completion and Multi-Slot Reorder — Consolidated Design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/schema_editor_emoji_and_multislot_reorder/schema_editor_emoji_and_multislot_reorder__final.md
producer: research.51.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer no-sandbox rendered 3 of 3 Mermaid diagrams; deliberately broken input exited nonzero"
```

## reorder-draft

```yaml
anchor: |-
  model and `session.setDraft([op])` **replaces** the draft; the chips are painted from
question: |-
  Why do repeated nudges restage the same move today, and what changes with a projected draft?
illustrates: |-
  Today's chips and nudges use the server model, while the proposed projected model accumulates pending moves and repaints the chips.
caption: "Projected drafts accumulate moves and repaint chips; today's nudges keep replacing a move calculated from the unchanged saved order."
review: "674.125x577 px, fit 96.8%; question, source-trace, labels, arrows, and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Why does reorder need a projected draft?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 150
---
flowchart TD
  subgraph TODAY["Today: saved order"]
    direction TB
    TS["`**Saved order**<br/>Before Apply`"]
    TN["`**Nudge**<br/>One-slot move`"]
    TD["`**Draft**<br/>Replaces move`"]
    TC["`**Chips**<br/>Saved order`"]
    TS -->|supplies order| TN
    TN -->|replaces| TD
    TS -->|paints| TC
  end
  subgraph FUTURE["Proposed: projected order"]
    direction TB
    PN["`**Nudge**<br/>Projected order`"]
    PD["`**Draft**<br/>Pending moves`"]
    PC["`**Chips**<br/>Projected order`"]
    PN -.->|updates| PD
    PD -.->|next nudge| PN
    PD -.->|paints| PC
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class TS,TN,TD,TC muted
  class PN,PD focus
  class PC outcome
  class PN,PD,PC proposed
  style TODAY fill:none,stroke:#6B7280
  style FUTURE fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

## save-gate

```yaml
anchor: |-
  the preview for the current revision is still in flight, Enter applies the moment it
question: |-
  When does Enter save the arrangement, require confirmation, or restore the order?
illustrates: |-
  The Enter latch waits for a successful preview of the exact envelope, then quiet previews auto-apply, loud previews ask for a second Enter, and refusals restore the order.
caption: "An exact preview gates every save; quiet changes need one Enter, loud changes need another, and refusals restore the order."
review: "504.06x1114 px, fit 80.1%; question, source-trace, labels, arrows, and visual checks passed; 1 revision, 2 look rounds; scoped to validation, confirmation, and refusal"
```

```mermaid
---
title: "Proposed: when does Enter save?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 180
---
flowchart TD
  ENTER["`**Enter**<br/>Latch if preview pending`"]
  VALID{{"`**Exact preview OK?**`"}}
  HOLD["`**Save gated**<br/>No write`"]
  QUIET{{"`**Quiet preview?**`"}}
  CONFIRM["`**Amber consequence**<br/>Confirm again`"]
  SAVE["`**Saving**<br/>Keep projected order`"]
  REFUSAL["`**Refusal**<br/>Restore; explain inline`"]
  ENTER -.->|once preview available| VALID
  VALID -.->|No| HOLD
  VALID -.->|Yes| QUIET
  QUIET -.->|Yes| SAVE
  QUIET -.->|No: loud| CONFIRM
  CONFIRM -.->|second Enter| SAVE
  SAVE -.->|if writer refuses| REFUSAL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class ENTER,SAVE focus
  class VALID,QUIET,CONFIRM decision
  class HOLD,REFUSAL risk
  class ENTER,VALID,HOLD,QUIET,CONFIRM,SAVE,REFUSAL proposed
```

## emoji-focus

```yaml
anchor: |-
  Search text and chosen glyph are **separate state**: typing `rocket` can never become
question: |-
  How does choosing an emoji avoid accidentally saving the schema edit?
illustrates: |-
  The Emoji Slot keeps search text separate from the chosen glyph, so Enter selects a highlighted result without applying the schema edit and the first Escape closes only the panel.
caption: "Enter chooses without saving; Escape closes only the emoji panel, and paste or the operating system picker sets glyphs directly."
review: "437.469x807 px, fit 100%; question, source-trace, labels, arrows, and visual checks passed; 0 revisions, 1 look round"
```

```mermaid
---
title: "Proposed: Enter picks an emoji without saving"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 175
---
flowchart TD
  SLOT["`**Emoji Slot**<br/>Chosen glyph in schema draft`"]
  subgraph PANEL["In-card emoji panel: separate query state"]
    direction TB
    QUERY["`**Search query**<br/>Typing filters live`"]
    PICK["`**Highlighted result**<br/>Candidate glyph`"]
    QUERY -.->|filters| PICK
  end
  SLOT -.->|"Tab from label,<br/>click, or Ctrl+E"| QUERY
  PICK -.->|"Enter picks glyph;<br/>never also saves"| SLOT
  QUERY -.->|"first Esc closes<br/>only the panel"| SLOT
  DIRECT["`**Paste or OS picker**<br/>Glyph input`"]
  DIRECT -.->|sets directly| SLOT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class QUERY,PICK,DIRECT focus
  class SLOT outcome
  class QUERY,PICK,DIRECT,SLOT proposed
  style PANEL fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

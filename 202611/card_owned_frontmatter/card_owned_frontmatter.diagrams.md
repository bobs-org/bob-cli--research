# Diagram proposals: Property cards own the frontmatter

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/card_owned_frontmatter/card_owned_frontmatter__final.md
producer: research.5v.image
check: "mmdc 12.0.0 (pinned npx, Puppeteer --no-sandbox) with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; exit 0, both SVGs present, broken-diagram probe rejected"
```

## equals-shortcut-dispatch

```yaml
anchor: |-
  second `=` at capture phase while the operator is pending
question: |-
  When do =-, =+, and == intercept Vim, and when do they fall through?
illustrates: |-
  The proposed extension to the existing capture-phase gate dispatches the second key only in normal Live Preview with an empty operator buffer, no count or register, no input-method composition (IME), and no repeat, with =+ available on any Markdown note and =- requiring a mounted card.
caption: The guarded = shortcuts preserve Vim fallback, open =+ on any Markdown note, and require a mounted card for =-.
review: "856.43×1026 px, fit 76.2%; reader question, source trace, labels and arrow checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed: how do the = shortcuts dispatch?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 200
---
flowchart TD
  MODE{{"`**Normal Live Preview?**`"}}
  GATE{{"`**Clean pending =?**<br/>Empty buffer; no count/register/IME/repeat`"}}
  KEY{{"`**Second key?**`"}}
  CARD{{"`**Card mounted?**`"}}
  VIM["`**Vim**<br/>Keep the key`"]
  SPECIES["`**Existing ==**<br/>Card editor dispatch`"]
  PROPS["`**=+ editor**<br/>Any Markdown note`"]
  DRAWER["`**=- drawer**<br/>Toggle read-only properties`"]
  MODE -->|No| VIM
  MODE -.->|Yes| GATE
  GATE -->|No| VIM
  GATE -.->|Yes| KEY
  KEY -->|=| SPECIES
  KEY -.->|+| PROPS
  KEY -.->|-| CARD
  CARD -.->|Yes| DRAWER
  CARD -->|No| VIM
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class MODE,GATE,KEY,CARD decision
  class PROPS,DRAWER outcome
  class VIM,SPECIES muted
  class PROPS,DRAWER,CARD proposed
```

## guarded-typed-property-write

```yaml
anchor: |-
  Write discipline is the record session verbatim: debounced dry-run, Enter
question: |-
  How does a typed edit reach disk without losing a stale draft?
illustrates: |-
  For ordinary typed values, the proposed bob props editor reuses the guarded session so a current preview and saved open panes precede apply, stale refusal keeps the draft, and inverse operations support per-path Undo.
caption: Typed edits preview first and save open panes before apply; stale refusal keeps the draft, while successful writes supply per-path Undo.
review: "842×803 px, fit 77.5%; reader question, source trace, labels and arrow checks passed; 0 visual revisions; one sequence syntax fix before the passing batch"
```

```mermaid
---
title: "Proposed: how does a typed property edit reach disk?"
---
sequenceDiagram
  autonumber
  participant EDIT as Editor + guarded session
  participant PANES as Open panes
  participant BOB as bob props
  Note over EDIT,BOB: Ordinary typed values, 250 ms preview debounce
  EDIT->>BOB: Dry-run typed value
  BOB-->>EDIT: Current preview
  EDIT->>EDIT: Enter latches on current preview
  EDIT->>PANES: Save every open pane
  PANES-->>EDIT: Saved before apply
  EDIT->>BOB: Apply with current fingerprint
  alt Stale fingerprint
    BOB-->>EDIT: Refuse, keep the draft
  else Successful write
    BOB-->>EDIT: Applied, inverse operations for Undo
    Note over EDIT: Undo survives reopening this path
  end
```

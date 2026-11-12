# Diagram proposals: Walker footers: the status bar follows the active bracket walk

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bracket_walk_footers/bracket_walk_footers__final.md
producer: research.4e.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## link-preview-safety

```yaml
anchor: |-
  click revalidates note, revision, and destination before opening
question: |-
  How do link previews avoid stale navigation and accidental note creation?
illustrates: |-
  Generation-checked link previews paint only for the current family, source file, and editor revision; direction clicks revalidate context before the existing command may create a note.
caption: "Preview reads cannot create notes; only a context-validated explicit click may invoke the existing creation route."
review: "652.453x1010 px, fit 88.4%; question, visual, and source-trace checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when may a links preview open a note?"
accTitle: "Two checks separate read-only preview from explicit navigation"
accDescr: "A link-preview response must still match the selected family, source note, and editor revision before it paints. A later explicit click rechecks mode, note, revision, and destination before invoking the existing command, which may create a missing note. A failed check permits no paint or navigation, respectively."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 20
    wrappingWidth: 200
---
flowchart TD
  READ["`**Read link preview**<br/>Mode, note, editor revision`"]
  FRESH{{"`**Preview still current?**`"}}
  DISCARD["`**Ignore stale response**<br/>Do not paint`"]
  SHOW["`**Paint links compass**<br/>Read-only; no note creation`"]
  VALID{{"`**Click still valid?**<br/>Mode, note, revision, target`"}}
  STOP["`**Reject stale activation**<br/>Do not open or create`"]
  ACT["`**Existing link command**<br/>May create missing note`"]
  READ -.->|"response arrives"| FRESH
  FRESH -.->|"No"| DISCARD
  FRESH -.->|"Yes"| SHOW
  SHOW -.->|"only an explicit click"| VALID
  VALID -.->|"No"| STOP
  VALID -.->|"Yes"| ACT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class READ,SHOW,ACT focus
  class FRESH,VALID decision
  class DISCARD,STOP muted
```

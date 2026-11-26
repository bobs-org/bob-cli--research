# Diagram proposals: Renaming `article` to `prose`: section extraction and the road to reversible projects

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/prose_rename_and_section_extraction/prose_rename_and_section_extraction__final.md
producer: research.6i.image
check: "mmdc 12.0.0 (pinned npx, Puppeteer --no-sandbox) with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## extraction-placement

```yaml
anchor: |-
  heading preserves the structural slot, document order, and a landing for inbound links
question: |-
  After extraction, where do the writing and its links live?
illustrates: |-
  Extraction keeps the heading and a single bullet stub in the source while repairing source-local links, subtree links back to the source, and third-party inbound links.
caption: Extraction keeps a heading and bullet stub in the source while repairing links to moved writing, back to source, and from other notes.
review: "460.953x494 px, fit 100.0%; question, source trace and visual checks passed; 2 revisions; 2 look rounds"
```

```mermaid
---
title: "Proposed: where do extracted text and links live?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TB
  OTHER["`**Other note**<br/>Inbound links repaired`"]
  SOURCE["`**Source note**<br/>Heading + bullet stub`"]
  PROSE["`**New prose note**<br/>Moved writing`"]
  SOURCE -.->|"links to moved writing"| PROSE
  PROSE -.->|"links back to source"| SOURCE
  OTHER -.->|"heading / block links"| PROSE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class SOURCE focus
  class PROSE outcome
  class OTHER muted
  class OTHER,SOURCE,PROSE proposed
```

## re-adoption

```yaml
anchor: |-
  the task block whose current `parent` is the source note are offered in an explicit
question: |-
  When may task promotion re-adopt a prose note?
illustrates: |-
  On task-to-project promotion, the direct-sibling rule limits which linked prose notes reach the explicit consent picker, and accepted notes reparent under the new project.
caption: Task-to-project promotion re-adopts a linked prose note only when its parent is the task’s residence and the user accepts.
review: "497.609x914 px, fit 97.7%; question, source trace and visual checks passed; 0 revisions; 1 look round"
```

```mermaid
---
title: "Proposed: when may promotion re-adopt prose?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  NOTE["`**Linked prose note**<br/>Mentioned in the task block`"]
  PARENT{{"`**Parent is source note?**`"}}
  PICK["`**Consent picker**<br/>Offer re-adoption`"]
  ACCEPT{{"`**Accepted?**`"}}
  KEEP["`**Keep current parent**<br/>Either rejection path`"]
  ADOPT["`**New project**<br/>Reparent the prose note`"]
  NOTE -.->|"check current parent"| PARENT
  PARENT -.->|"Yes"| PICK
  PARENT -.->|"No"| KEEP
  PICK -.->|"ask the user"| ACCEPT
  ACCEPT -.->|"Yes"| ADOPT
  ACCEPT -.->|"No"| KEEP
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class NOTE,PICK focus
  class PARENT,ACCEPT decision
  class KEEP,ADOPT outcome
  class NOTE,PARENT,PICK,ACCEPT,KEEP,ADOPT proposed
```

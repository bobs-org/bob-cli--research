# Diagram proposals: Undirected task relations: a plain link has no direction; a label gives it one

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/undirected_task_relations/undirected_task_relations__final.md
producer: research.29.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## plain-to-labelled-move

```yaml
anchor: |-
  labelled record first. If the follow-up removal fails, the leftover plain record is subsumed
question: |-
  Why does a failed plain-to-labelled move still display the correct relation?
illustrates: |-
  In the plugin, a cross-note move writes the new labelled record first, so a leftover plain record is subsumed if removal fails and the next writable touch cleans it up.
caption: "For Obsidian plain-to-labelled moves, subsumption preserves the display after failed removal; either removal or a later writable edit completes cleanup."
review: "456.891x892 px, fit 100.0%; question, visual, and source checks passed; 1 revision; 2 look rounds"
```

```mermaid
---
title: "Proposed plain-to-labelled move: why write first?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 24
    wrappingWidth: 260
---
flowchart TD
  WRITE["`**Write labelled record**<br/>On the new source`"]
  REMOVE{{"`**Did removal succeed?**`"}}
  CLEAN["`**Labelled record only**<br/>At the new source`"]
  LEFT["`**Leftover plain record**<br/>Hidden by label`"]
  WARN["`**Reconcile warns**<br/>Keeps authored records`"]
  WRITE -.->|"remove other task's plain record"| REMOVE
  REMOVE -.->|"Yes"| CLEAN
  REMOVE -.->|"No"| LEFT
  LEFT -.->|"reconcile"| WARN
  WARN -.->|"next writable touch"| CLEAN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class WRITE,WARN focus
  class REMOVE,LEFT decision
  class CLEAN outcome
  class WRITE,REMOVE,CLEAN,LEFT,WARN proposed
```

## reverse-capture-card

```yaml
anchor: |-
  Return with an empty label on a `~~` token
question: |-
  How does Mac reverse capture require a label yet offer a plain link?
illustrates: |-
  The Mac reverse picker opens the label card, whose live sentence previews either a labelled statement by the other task or the visible empty-label choice of a plain link.
caption: "The Mac card previews both choices: Return keeps a labelled reverse statement or explicitly converts an empty label to a plain link."
review: "468.672x916 px, fit 97.5%; question, visual, and source checks passed; 0 revisions; 1 look round"
```

```mermaid
---
title: "Proposed Mac reverse capture: label or plain link?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 24
    wrappingWidth: 220
---
flowchart TD
  PICK["`**Reverse picker**<br/>Choose task T`"]
  CARD["`**Label card opens**<br/>Completion inserts ~~T|`"]
  LABEL{{"`**Is the label empty?**`"}}
  DIRECTED["`**Directed preview**<br/>T — label → this task`"]
  PLAIN["`**Plain preview**<br/>This task — T`"]
  SAVE_DIRECTED["`**Keep reverse syntax**<br/>~~T|label`"]
  SAVE_PLAIN["`**Choose plain link**<br/>Rewrite token to ~T`"]
  PICK -.->|"Return selects T"| CARD
  CARD -.->|"preview follows label field"| LABEL
  LABEL -.->|"No"| DIRECTED
  LABEL -.->|"Yes"| PLAIN
  DIRECTED -.->|"Return accepts label"| SAVE_DIRECTED
  PLAIN -.->|"Return accepts plain preview"| SAVE_PLAIN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PICK,CARD,DIRECTED,PLAIN focus
  class LABEL decision
  class SAVE_DIRECTED,SAVE_PLAIN outcome
  class PICK,CARD,LABEL,DIRECTED,PLAIN,SAVE_DIRECTED,SAVE_PLAIN proposed
```

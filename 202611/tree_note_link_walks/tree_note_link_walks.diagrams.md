# Diagram proposals: Tree-note link walks

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says. Placement remains the linker's decision.

```yaml
source: research:202611/tree_note_link_walks/tree_note_link_walks__final.md
producer: research.6o.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; pinned CLI with Puppeteer --no-sandbox"
```

## sibling-eligibility

```yaml
anchor: |-
  A note joins the walk when its `propertyCardNoteSpecies` is `area`, `project`,
question: |-
  Which notes may join a derived sibling ring?
illustrates: |-
  Supported tree notes form same-type sibling rings by canonical parent path, while excluded paths stay outside the walk and invalid parents produce explicit none reasons.
caption: Supported notes with valid immediate parents form rings by type and parent path; project rings also separate open and closed lanes.
review: "739.398x810 px, fit 88.3%; reader question answered from the PNG; labels, arrowheads, reading order, and source trace passed; 0 revisions"
```

```mermaid
---
title: "Proposed: which notes join a sibling ring?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  NOTE["`**Tree note**<br/>Area, project, notebook, or prose`"]
  PATH{{"`**Excluded path?**`"}}
  OUT["`**Outside this walk**<br/>Archive, template, conflict, or hub`"]
  PARENT{{"`**Valid immediate parent?**`"}}
  NONE["`**No derived ring**<br/>Explain the parent problem`"]
  RING["`**Sibling ring**<br/>Same type and canonical parent path`"]
  NOTE -.->|"check path"| PATH
  PATH -.->|"yes"| OUT
  PATH -.->|"no"| PARENT
  PARENT -.->|"no: missing, list,<br/>unresolved, self, or cycle"| NONE
  PARENT -.->|"yes: one link<br/>to an existing note"| RING
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class NOTE focus
  class PATH,PARENT,OUT,NONE decision
  class RING outcome
  class NOTE,PATH,PARENT,OUT,NONE,RING proposed
```

## authored-step-eligibility

```yaml
anchor: |-
  Authored links keep winning per role, which lets a prose series
question: |-
  Which authored step links remain eligible to override the derived walk?
illustrates: |-
  Authored step links win per role outside inline code, but derived routes additionally require link-only nav lines while notes without derived routes keep anywhere-in-body matching.
caption: Either eligible path lets authored steps win their role; derived routes require link-only nav lines, and inline code never qualifies.
review: "557.455x784 px, fit 100.0%; reader question answered from the PNG; labels, arrowheads, crossings, and source trace passed; 0 revisions"
```

```mermaid
---
title: "Proposed: which authored step links can win?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 20
    wrappingWidth: 210
---
flowchart TD
  CODE{{"`**Inside inline code?**`"}}
  IGNORE["`**Ignore candidate**<br/>Cannot override this step`"]
  ROUTE{{"`**Derived route available?**`"}}
  LINE{{"`**Link-only nav line?**`"}}
  ALLOW["`**Authored step eligible**<br/>Wins for its navigation role`"]
  CODE -.->|"yes"| IGNORE
  CODE -.->|"no"| ROUTE
  ROUTE -.->|"yes"| LINE
  ROUTE -.->|"no: retain<br/>body-wide matching"| ALLOW
  LINE -.->|"no"| IGNORE
  LINE -.->|"yes"| ALLOW
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class CODE,ROUTE,LINE decision
  class IGNORE muted
  class ALLOW outcome
  class CODE,ROUTE,LINE,IGNORE,ALLOW proposed
```

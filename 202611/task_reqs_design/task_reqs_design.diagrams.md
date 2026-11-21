# Diagram proposals: Task requirements for Bob: consolidated design and recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/task_reqs_design/task_reqs_design__final.md
producer: research.5p.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 3 of 3 Mermaid diagrams; pinned CLI, Puppeteer --no-sandbox"
```

## audit-trigger

```yaml
anchor: |-
  with pending reqs; the req group alone suffices to open the card and is placed first
question: |-
  When does closing a task show a requirements audit?
illustrates: |-
  A managed Done gesture adds a requirements group first per eligible owner, while cancelled, automated, raw, recurring, and req-less cases follow the bypass branches.
caption: Only managed Done with a non-recurring owner and pending requirements adds an audit group; bypass closes rely on derived state.
review: "638.078×658 px, fit 100.0%; question, source trace, labels, arrowheads, crossings, and visual checks passed; 1 revision, 2 looks"
```

```mermaid
---
title: "Proposed: when does closing show a requirements audit?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 20
    wrappingWidth: 200
---
flowchart TD
  MANAGED{{"`**Managed Done gesture?**`"}}
  ELIGIBLE{{"`**Non-recurring owner<br/>with pending reqs?**`"}}
  BYPASS["`**No audit card**<br/>Derived state applies`"]
  AUDIT["`**Requirements audit**<br/>First group per owner`"]
  EXISTING["`**No requirements group**<br/>Existing behavior continues`"]
  MANAGED -.->|"Yes"| ELIGIBLE
  MANAGED -.->|"No: cancel, automated<br/>close, or raw edit"| BYPASS
  ELIGIBLE -.->|"Yes, in closing set"| AUDIT
  ELIGIBLE -.->|"No"| EXISTING
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class MANAGED,ELIGIBLE decision
  class AUDIT outcome
  class BYPASS,EXISTING muted
  class MANAGED,ELIGIBLE,BYPASS,AUDIT,EXISTING proposed
```

## escape-timing

```yaml
anchor: |-
  defaults write nothing, so Esc and Return produce identical req outcomes, only explicit
question: |-
  What does Esc with untouched defaults leave behind in Obsidian and Mac capture?
illustrates: |-
  Obsidian keeps the post-close card and same-day reopen, while Mac capture keeps the pre-write card and Esc-returns-to-draft.
caption: With untouched defaults, Obsidian’s Esc leaves the owner closed; Mac capture’s Esc returns to the draft before writing.
review: "584.688×529 px, fit 100.0%; question, source trace, labels, arrowheads, crossings, and visual checks passed; 1 revision, 2 looks"
```

```mermaid
---
title: "Proposed: what does Esc do with unchanged defaults?"
config:
  flowchart:
    rankSpacing: 25
    nodeSpacing: 25
    wrappingWidth: 210
---
flowchart TB
  subgraph OBS["Obsidian · proposed v1"]
    O1["`**Card after close**<br/>Owner already closed`"]
    O2["`**Owner stays closed**<br/>No requirement writes`"]
    O3["`**Owner reopened**<br/>Unchecked requirements pending`"]
    O1 -.->|"Untouched Esc or Return"| O2
    O2 -.->|"Same-day reopen"| O3
  end
  subgraph MAC["Mac capture · proposed v1"]
    M1["`**Card before write**<br/>Close not written`"]
    M2["`**Back to draft**<br/>Close not written`"]
    M1 -.->|"Esc"| M2
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class O1,M1 focus
  class O2 muted
  class O3,M2 outcome
  class O1,O2,O3,M1,M2 proposed
  style OBS fill:none,stroke:#3B78C2
  style MAC fill:none,stroke:#3B78C2
```

## notes-write-boundary

```yaml
anchor: |-
  one-undo write; later note captures to a req-owning task file into the drawer
question: |-
  Which actions organize notes automatically, and which leave hand edits alone?
illustrates: |-
  The first-req gesture gathers loose notes and later note captures file into NOTES, while hand edits stay in place until an explicit tidy.
caption: Bob organizes notes during first-req and later capture writes; hand edits wait for explicit tidy.
review: "748×469 px, fit 87.3%; question, source trace, labels, arrowheads, crossings, and visual checks passed; 1 revision, 2 looks"
```

```mermaid
---
title: "Proposed: which note edits does Bob organize?"
config:
  flowchart:
    rankSpacing: 30
    nodeSpacing: 12
    wrappingWidth: 150
---
flowchart TB
  subgraph HAND["Hand edits · proposed"]
    EDIT["`**Hand edits**<br/>No automatic reshuffle`"]
    TIDY["`**Explicit tidy**<br/>Fix layout drift`"]
    EDIT -.->|"Only on request"| TIDY
  end
  subgraph WRITES["Bob writes · proposed"]
    CAPTURE["`**Later note capture**<br/>Owner has requirements`"]
    FIRST["`**First requirement**<br/>Preview + one undo`"]
    NOTES["`**NOTES drawer**<br/>Either write files here`"]
    FIRST -.->|"Gathers loose notes"| NOTES
    CAPTURE -.->|"Files new note"| NOTES
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class FIRST,CAPTURE focus
  class NOTES,TIDY outcome
  class EDIT muted
  class FIRST,CAPTURE,NOTES,EDIT,TIDY proposed
  style WRITES fill:none,stroke:#3B78C2
  style HAND fill:none,stroke:#6B7280
```

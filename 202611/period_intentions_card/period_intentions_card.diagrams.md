# Diagram proposals: Period intentions and property cards: consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/period_intentions_card/period_intentions_card__final.md
producer: research.5f.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; pinned CLI with --no-sandbox; broken-diagram rejection passed"
```

## property-visibility

```yaml
anchor: |-
  while the card is cleanly mounted, never in embeds or Source mode
question: |-
  When can an intention card hide native properties?
illustrates: |-
  A property card owns exactly the rows it shows and fails open, so native YAML access survives unsupported views, malformed values, or mount failure.
caption: |-
  Intention cards hide owned properties only when supported and mounted safely; empty notes remain editable, and failure preserves native access.
review: "630.449x832 px, fit 100.0%; question and visual checks passed; all nodes and edges traced to sections 3.1 and 5.5; 1 revision; eligibility branches, not runtime check order"
```

```mermaid
---
title: "Proposed: when can intention cards hide properties?"
accTitle: "Proposed intention-card visibility and fallback"
accDescr: "On canonical daily and period notes, the card hides its owned rows only in a supported desktop view with content and a valid clean mount. Other cases preserve native YAML access; an empty note can still open the editor."
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 18
    wrappingWidth: 230
---
flowchart TD
  VIEW{{"`**Supported desktop view?**<br/>Reading/Live Preview, no embeds`"}}
  CONTENT{{"`**Any content?**<br/>intentions, summary, reflection`"}}
  MOUNT{{"`**Valid, clean card mount?**`"}}
  EMPTY["`**No display card**<br/>== still opens editor`"]
  NATIVE["`**Native YAML access**<br/>Keep properties accessible`"]
  CARD["`**Display intention card**<br/>Hide only owned rows`"]
  VIEW -.->|"Yes"| CONTENT
  VIEW -.->|"No"| NATIVE
  CONTENT -.->|"Yes"| MOUNT
  CONTENT -.->|"No"| EMPTY
  MOUNT -.->|"Yes"| CARD
  MOUNT -.->|"No: malformed or failed"| NATIVE
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class VIEW,CONTENT,MOUNT decision
  class CARD outcome
  class EMPTY,NATIVE muted
```

## reflection-before-summary

```yaml
anchor: |-
  PRE completes when the agent is *launched*, not when it finishes; POST reflection
question: |-
  Can Bryan reflect before the summary agent finishes?
illustrates: |-
  PRE completes when the agent is launched, so POST reflection stays available if the agent is slow and never blocks the first summary draft.
caption: |-
  Bryan can reflect before the agent finishes: reflection allows a first summary but requires explicit redo for a re-draft.
review: "789x750 px, fit 82.7%; question and visual checks passed; actors and messages traced to sections 4 item 9 and 5.3-5.5; 0 revisions; one allowed interleaving, not compulsory chronology"
```

```mermaid
---
title: "Proposed: reflection need not wait for the agent"
accTitle: "Proposed first summary after reflection"
accDescr: "One allowed morning interleaving: Bryan launches the summary agent, continues the review walk and saves a reflection before the agent submits. A first summary is allowed despite reflection; a redraft requires explicit redo."
config:
  sequence:
    actorMargin: 35
    messageMargin: 24
    noteMargin: 8
---
sequenceDiagram
  autonumber
  participant B as Bryan
  participant A as Summary agent
  participant W as bob
  B->>A: PRE: launch summary
  A->>W: brief yesterday
  W-->>A: Instructions + day evidence
  Note over B,A: Example: reflection arrives first
  B->>B: Commitment walk
  B->>W: POST: save reflection via card
  A->>W: draft yesterday
  alt First summary
    W-->>A: Allow despite reflection
  else Summary already exists
    W-->>A: Reflection requires explicit redo
  end
```

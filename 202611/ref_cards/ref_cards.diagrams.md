# Diagram proposals: Ref Cards: consolidated design, `==` editor, and parallel delivery beside `bob-cli-qm`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/ref_cards/ref_cards__final.md
producer: research.6l.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; pinned CLI with Puppeteer no-sandbox; negative syntax check returned nonzero"
```

## capability-fallbacks

```yaml
anchor: |-
  without `props_ref_contract_v1`, `==` falls back to focus-or-add on
question: |-
  Which capability enables card takeover, and which enables the full Reference editor?
illustrates: |-
  The card mounts on props_v1 alone, while == opens the Reference editor with props_ref_contract_v1 and otherwise falls back to focus-or-add on title.
caption: "Takeover needs props_v1; a missing reference contract keeps the card and routes == to the title fallback."
review: "558.941×962 px, fit 92.8%; question, source trace, labels and visual checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed: which capabilities enable the card and editor?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 210
---
flowchart TD
  REF["`**Eligible reference**<br/>Ref preview enabled`"]
  PROPS{{"`**props_v1 evidence valid?**`"}}
  NATIVE["`**Native Properties**<br/>Restore on uncertainty`"]
  CARD["`**Ref Card**<br/>Title shell mounts`"]
  CONTRACT{{"`**Reference contract available?**`"}}
  EDITOR["`**Reference editor**<br/>Typed citation settings`"]
  FALLBACK["`**Title fallback**<br/>Focus or add title`"]
  REF -.->|"check takeover"| PROPS
  PROPS -.->|"No"| NATIVE
  PROPS -.->|"Yes"| CARD
  CARD -.->|"== pressed"| CONTRACT
  CONTRACT -.->|"props_ref_contract_v1 present"| EDITOR
  CONTRACT -.->|"capability absent"| FALLBACK
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class REF,CARD focus
  class PROPS,CONTRACT decision
  class NATIVE,EDITOR,FALLBACK outcome
```

## passive-report-service

```yaml
anchor: |-
  a scan rewrite or embed heal while the note is open must patch chips
question: |-
  How do reading-state chips update without spawning bob during painting, folding or scrolling?
illustrates: |-
  One shared, debounced, stale-while-revalidate report supplies reading-state chips, while identity paints local-first and painting, folding, and scrolling never spawn bob.
caption: "The shared service runs bob; cards keep local identity and patch reading chips without spawning or writing during paint."
review: "868×938 px, fit 75.2%; question, source trace, labels and visual checks passed; 1 visual revision tried, original retained because the narrower revision clipped its title"
```

```mermaid
---
title: "Proposed: reading updates without paint-time spawns"
---
sequenceDiagram
  autonumber
  participant C as Ref Cards
  participant S as Shared report service
  participant B as bob CLI
  Note over C: Identity paints from<br/>local metadata
  C->>S: First mount subscribes lazily
  alt Snapshot available, even stale
    S-->>C: Deliver shared snapshot
    Note over C: Paint reading chips
  else No snapshot
    Note over C: Omit reading-state chips
  end
  Note over S: Debounce, share one<br/>in-flight request
  S->>B: bob ref list -A -R all -f json
  B-->>S: Reading-state snapshot
  S-->>C: Patch chips in place
  Note over C: Stale data keeps<br/>the valid title shell
  Note over C: Paint, fold, scroll:<br/>no bob spawns or writes
```

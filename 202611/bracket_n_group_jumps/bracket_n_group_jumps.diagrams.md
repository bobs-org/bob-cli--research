# Diagram proposals: `[N` / `]N` group jumps for days, periods, and records

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bracket_n_group_jumps/bracket_n_group_jumps__final.md
producer: research.5l.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## double-arrow-classification

```yaml
anchor: |-
  Check doubles before singles so
question: |-
  How can double-arrow aliases avoid hijacking lowercase navigation?
illustrates: |-
  Checking doubles before singles keeps the four roles disjoint, while link-only nav lines limit where authored group-link candidates are recognized.
caption: "`<<` / `>>` bypass lowercase navigation; only link-only nav lines can supply uppercase group-link candidates."
review: "838x611 px, fit 77.9%; question, label, arrow, source and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "Proposed: double arrows cannot take single steps"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart LR
  subgraph TODAY["Today"]
    direction TB
    OLD["`**Doubled-arrow link**<br/>In a body label`"]
    WRONG["`**Lowercase step**<br/>Wrongly claims group alias`"]
    OLD -->|Prefix claims first arrow| WRONG
  end
  subgraph PROPOSAL["Proposed classification"]
    direction TB
    NEW["`**Doubled-arrow link**<br/>Excluded from lowercase`"]
    NAV{{"`**Link-only nav line?**`"}}
    GROUP["`**Group-link candidate**<br/>Uppercase role`"]
    IGNORE["`**Ignore group role**<br/>Ordinary body content`"]
    NEW -.->|Check group scope| NAV
    NAV -.->|Yes| GROUP
    NAV -.->|No| IGNORE
  end
  TODAY ~~~ PROPOSAL
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class OLD,NEW,GROUP,IGNORE focus
  class NAV decision
  class WRONG risk
  class NEW,NAV,GROUP,IGNORE proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#3B78C2
```

## preview-to-activation

```yaml
anchor: |-
  the footer all consume one resolved answer; rail/footer clicks re-validate
question: |-
  For existing or create-eligible targets, how do displayed stops become safe jumps?
illustrates: |-
  Rail/footer clicks re-validate role, target, and source revision before invoking the same command the keyboard uses, separating read-only display from target creation and opening.
caption: "For existing or create-eligible targets, clicks revalidate before the shared command creates if needed, opens, and records jump history."
review: "823x816 px, fit 79.3%; question, label, arrow, source and visual checks passed; 1 visual revision and 1 syntax repair"
```

```mermaid
---
title: "Proposed: from preview to an eligible jump"
---
sequenceDiagram
  autonumber
  participant UI as Rail / footer
  participant NAV as Navigation Hotkeys
  participant WRITER as Existing writer
  Note over UI,NAV: Scope: existing or create-eligible targets
  NAV-->>UI: Resolved stop for display
  Note over UI: Display never creates files
  UI->>UI: On activation, revalidate<br/>role, target, source revision
  UI->>NAV: Invoke shared group command
  Note over NAV: Keys and repeat keys<br/>use this command too
  opt Missing and create-eligible
    NAV->>WRITER: Create target
    WRITER-->>NAV: Created target
  end
  NAV->>NAV: Open target and<br/>record jump history
```

# Diagram proposals: Schema card field jumps

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/schema_card_field_jump_design/schema_card_field_jump_design__final.md
producer: research.57.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## painted-order

```yaml
anchor: |-
  `schemaTargets()` reads raw `model.fields` while
question: |-
  Why can a pending reorder make keyboard navigation disagree with the screen, and what changes?
illustrates: |-
  One shared painted-order helper fixes navigation, numbering, and today's j/k drift together.
caption: "The proposed shared painted order keeps navigation and field numbers aligned with the visible fields while a reorder is pending."
review: "591.969x772.594 px, fit 100%; question, source, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Why must field jumps use painted order?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 240
---
flowchart TD
  subgraph TODAY["Today: after moving Claim below Section"]
    SAVED["`**Saved order**<br/>Status · Claim · Section`"]
    PROJECTED["`**Projected order**<br/>Status · Section · Claim`"]
    T_NAV["`**Navigation**<br/>j / k walk`"]
    T_BODY["`**Body**<br/>Visible fields`"]
    SAVED -->|supplies order| T_NAV
    PROJECTED -->|supplies order| T_BODY
  end
  subgraph PROPOSED["Proposed: the same pending reorder"]
    PAINTED["`**Shared painted order**<br/>Status · Section · Claim`"]
    P_NAV["`**Navigation**<br/>Fine walk and field jumps`"]
    P_BODY["`**Body**<br/>Visible fields and numbers`"]
    PAINTED -.->|supplies order| P_NAV
    PAINTED -.->|supplies order| P_BODY
  end
  TODAY ~~~ PROPOSED
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class SAVED,PROJECTED,T_BODY focus
  class T_NAV risk
  class PAINTED,P_NAV,P_BODY outcome
  class PAINTED,P_NAV,P_BODY proposed
  style TODAY fill:none,stroke:#3B78C2
  style PROPOSED fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

## shifted-digits

```yaml
anchor: |-
  AZERTY produces digits *with* Shift held.
question: |-
  Why do Shift-produced digits jump while US Shift+1 still toggles required?
illustrates: |-
  Matching event.key rather than shiftKey lets AZERTY digits work while US Shift+1 remains ! and keeps the required toggle.
caption: "The proposed test ignores Shift: either example supplies event.key, so AZERTY digits navigate and US Shift+1 keeps required toggling."
review: "587.516x623 px, fit 100%; question, source, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Why test the character instead of Shift?"
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 18
    wrappingWidth: 240
---
flowchart TD
  subgraph SCOPE["Proposed: browse mode; no Ctrl, Meta, or Alt"]
    AZERTY["`**AZERTY shifted digit**<br/>Produces 1–9`"]
    US["`**US Shift+1**<br/>Produces !`"]
    MATCH{{"`**event.key is 1–9?**`"}}
    JUMP["`**Field-number handling**<br/>Jump or announce missing field`"]
    REQUIRED["`**Existing ! handling**<br/>Toggle required`"]
    AZERTY -.->|character to test| MATCH
    US -.->|character to test| MATCH
    MATCH -.->|Yes: digit| JUMP
    MATCH -.->|No: !| REQUIRED
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class AZERTY,US focus
  class MATCH decision
  class JUMP,REQUIRED outcome
  class MATCH,JUMP proposed
  style SCOPE fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

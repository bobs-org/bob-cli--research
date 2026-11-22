# Diagram proposals: True-case task drawers: bold headers, one place resolver, a gated cutover

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/true_case_drawers/true_case_drawers__final.md
producer: research.5x.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## import-escape

```yaml
anchor: |-
  wrapping them in `**…**` — under the bold marker, that exact branch would
question: |-
  Why must calendar escaping change with bold drawers?
illustrates: |-
  The calendar defuser's double-star wrapper would manufacture drawers under the bold marker; the proposed double-underscore escape keeps imported bold text a note.
caption: The proposed double-underscore import escape preserves bold appearance without turning imported text into a drawer.
review: "582.484×916 px, fit 97.5%; question answered from PNG; labels, arrowheads, source trace and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "Why must calendar escaping change with bold drawers?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 16
    wrappingWidth: 260
---
flowchart TD
  OLD["`**Today's calendar writer**<br/>Bold-wraps ALL-CAPS`"]
  BOLD["`**Imported bold line**<br/>Double-star escape`"]
  Q{{"`**Escape updated?**`"}}
  BAD["`**Accidental drawer**<br/>Imported text becomes structure`"]
  ESC["`**Updated import writer**<br/>Uses double underscores`"]
  NOTE["`**Ordinary bold note**<br/>Appearance preserved`"]
  OLD -->|writes| BOLD
  BOLD -.->|with proposed recognition| Q
  Q -.->|No: unchanged escape| BAD
  Q -.->|Yes: rewrite bold| ESC
  ESC -.->|preserves text as| NOTE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OLD,BOLD,Q focus
  class BAD risk
  class ESC,NOTE outcome
  class Q,BAD,ESC,NOTE proposed
```

## rollout-gates

```yaml
anchor: |-
  so no vault migration until every host is current.
question: |-
  When may drawer migration and cutover proceed?
illustrates: |-
  In the proposed rollout, every host must run a drawer-aware release before vault migration, and ALL-CAPS recognition is removed only once the legacy inventory reads zero.
caption: Command-line, Obsidian and Mac readers must be current before migration; legacy recognition ends only when the inventory reaches zero.
review: "686.672×914 px, fit 95.1%; question answered from PNG; labels, arrowheads, source trace and visual checks passed; 1 visual revision"
```

```mermaid
---
title: "When may drawer migration and cutover proceed?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 16
    wrappingWidth: 260
---
flowchart TD
  RELEASE["`**Proposed dual-read release**<br/>CLI, plugins, Mac`"]
  HOSTS{{"`**Every host current?**`"}}
  HOLD["`**Hold migration**<br/>No vault migration yet`"]
  MIGRATE["`**Approved migration**<br/>Dry-run; user-chosen spellings`"]
  ZERO{{"`**Legacy inventory zero?**`"}}
  KEEP["`**Hold cutover**<br/>Keep legacy recognition`"]
  CUT["`**Cutover release**<br/>Remove ALL-CAPS recognition`"]
  RELEASE -.->|before vault migration| HOSTS
  HOSTS -.->|No| HOLD
  HOSTS -.->|Yes| MIGRATE
  MIGRATE -.->|inventory legacy drawers| ZERO
  ZERO -.->|No| KEEP
  ZERO -.->|Yes| CUT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class RELEASE,HOLD,KEEP focus
  class HOSTS,ZERO decision
  class MIGRATE,CUT outcome
  class RELEASE,HOSTS,HOLD,MIGRATE,ZERO,KEEP,CUT proposed
```

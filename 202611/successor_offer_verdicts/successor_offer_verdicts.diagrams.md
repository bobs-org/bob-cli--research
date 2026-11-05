# Diagram proposals: Close and cancel tasks from successor cards

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/successor_offer_verdicts/successor_offer_verdicts__final.md
producer: research.3g.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## eligibility-gates

```yaml
anchor: |-
  The cycler attaches eligibility only when nav reports v4 or later.
question: |-
  How do compatibility and row eligibility gate Done and Cancel?
illustrates: |-
  The cycler requires nav v4 or later and Mac Capture feature-detects bob support, after which either surface uses the requested action’s per-row eligibility.
caption: Either supported surface must also pass bob’s per-row eligibility check before Done or Cancel can be staged.
review: "777.089×588 px, fit 84.0%; question, visual and source-trace checks passed; 1 revision across 2 look rounds"
```

```mermaid
---
title: "Proposed: how are Done and Cancel enabled?"
accTitle: "Compatibility and per-row action gates"
accDescr: "Obsidian requires nav API version 4 or later. Mac Capture requires bob close support. Either supported route then checks the requested action's per-row eligibility; unsupported versions retain old behavior."
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  NAV{{"`**Obsidian**<br/>nav API v4+?`"}}
  OLDNAV["`**Earlier API**<br/>Today's pull-in-only card`"]
  BOB{{"`**Mac Capture**<br/>bob supports closes?`"}}
  OLDBOB["`**Older bob**<br/>No close hints; chords beep`"]
  NAV -.->|No| OLDNAV
  BOB -.->|No| OLDBOB
  ROW{{"`**Row allows action?**`"}}
  STAGE["`**Stage Done or Cancel**<br/>Apply writes later`"]
  REFUSE["`**Refuse action**<br/>Show bob's reason`"]
  NAV -.->|Yes| ROW
  BOB -.->|Yes| ROW
  ROW -.->|Yes| STAGE
  ROW -.->|No| REFUSE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class NAV,BOB,ROW decision
  class STAGE focus
  class OLDNAV,OLDBOB,REFUSE muted
```

## apply-failure-paths

```yaml
anchor: |-
  After a timeout with an unknown outcome, re-read the state before retrying.
question: |-
  What happens on changed targets or an uncertain timeout?
illustrates: |-
  Obsidian refuses only changed rows, while Capture aborts stale-target batches and re-reads state after a timeout with an unknown outcome before retrying.
caption: Changed targets cause per-row refusals in Obsidian and batch aborts in Capture; unknown Capture outcomes require re-reading state before retrying.
review: "833.367×491 px, fit 78.3%; question, visual and source-trace checks passed; 1 revision across 2 look rounds"
```

```mermaid
---
title: "Proposed: what if Apply fails or times out?"
accTitle: "Successor verdict refusal and uncertain outcomes"
accDescr: "Obsidian refuses a changed row and applies the others, preserving the predecessor close. Capture aborts a stale-target batch and reopens the card with choices intact. If a timeout leaves the outcome unknown, re-read state before retrying."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  subgraph OBS["Obsidian: predecessor stays closed"]
    CHANGED["`**Changed target**<br/>Since the card opened`"]
    PARTIAL["`**Refuse that row**<br/>Other rows still apply`"]
    CHANGED -.->|Refuse individually| PARTIAL
  end
  subgraph MAC["Mac Capture: inspect the failure"]
    FAILURE{{"`**Which Capture failure?**`"}}
    ABORT["`**Abort batch**<br/>Reopen card; keep choices`"]
    READ["`**Re-read state**<br/>Before any retry`"]
    FAILURE -.->|Stale target| ABORT
    FAILURE -.->|Timeout; outcome unknown| READ
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  class CHANGED,PARTIAL,ABORT risk
  class FAILURE decision
  class READ focus
  style OBS fill:none,stroke:#C0392B
  style MAC fill:none,stroke:#3B78C2
```

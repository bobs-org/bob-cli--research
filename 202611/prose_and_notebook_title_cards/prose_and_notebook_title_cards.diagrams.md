# Diagram proposals: Prose and Notebook Title Cards

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/prose_and_notebook_title_cards/prose_and_notebook_title_cards__final.md
producer: research.6k.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## prose-data-ownership

```yaml
anchor: |-
  The provider owns request bounding and
question: |-
  Who supplies prose identity and outline data, and who owns requests?
illustrates: |-
  The read-only api.prose seam lets the Prose Card paint local YAML identity and Bob Prose's outline snapshot while the provider owns request bounding and rejects late responses.
caption: Local identity paints immediately; optional outline snapshots come from Bob Prose, which owns requests and rejects late responses.
review: 408.062x814 px, fit 100.0%; question, source-trace and visual checks passed; 2 revisions
```

```mermaid
---
title: "Proposed prose data path: who owns what?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TB
  subgraph PROVIDER["Bob Prose: request owner"]
    direction TB
    SNAP["`**Outline snapshot**<br/>Off-paint; late responses rejected`"]
    API["`**Proposed read-only API**<br/>Snapshot and subscription`"]
    SNAP -.->|"exposes data"| API
  end
  subgraph CONSUMER["Bob Ledger Tools: card owner"]
    direction TB
    YAML["`**Local YAML**<br/>Identity fields`"]
    CARD["`**Proposed Prose Card**<br/>Identity and outline chips`"]
    YAML -.->|"supplies identity immediately"| CARD
  end
  API -.->|"supplies optional outline"| CONSUMER
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class SNAP,YAML focus
  class API,CARD outcome
  class API,CARD proposed
  style PROVIDER fill:none,stroke:#3B78C2
  style CONSUMER fill:none,stroke:#2E7D4F
```

## takeover-versus-data-freshness

```yaml
anchor: |-
  a stale count hides or quietly updates; it never unmounts the
question: |-
  When do native Properties return, and when do only derived metrics disappear?
illustrates: |-
  Separating card-shell validity from derived-number freshness restores native Properties when takeover is unsafe while unavailable derived values leave a valid title mounted.
caption: Unsafe takeover restores native Properties; unavailable derived data leaves a valid card shell mounted.
review: 575.426x738 px, fit 100.0%; question, source-trace and visual checks passed; 0 revisions
```

```mermaid
---
title: "Proposed cards: what survives missing data?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TD
  GATE{{"`**Safe card takeover?**`"}}
  NATIVE["`**Native Properties**<br/>Retained or restored`"]
  SHELL["`**Card shell**<br/>Title remains mounted`"]
  DATA{{"`**Fresh report available?**`"}}
  QUIET["`**Derived chips**<br/>Omit or quietly refresh`"]
  METRICS["`**Derived chips**<br/>Paint cached values`"]
  GATE -.->|"No"| NATIVE
  GATE -.->|"Yes"| SHELL
  SHELL -.->|"check data separately"| DATA
  DATA -.->|"No"| QUIET
  DATA -.->|"Yes"| METRICS
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class GATE,DATA decision
  class NATIVE,QUIET focus
  class SHELL,METRICS outcome
```

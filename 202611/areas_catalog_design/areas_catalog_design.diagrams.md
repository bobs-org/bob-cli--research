# Diagram proposals: A generated `## Areas` catalog: consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/areas_catalog_design/areas_catalog_design__final.md
producer: research.4o.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; SVG and PNG reviewed"
```

## catalog-ownership

```yaml
anchor: |-
  It is display-only: it styles the stored rows, reads
question: |-
  Who writes the proposed Areas catalog, and who supplies its visual polish?
illustrates: |-
  Bob owns exactly the callout bytes, while the display-only card combines the stored rows and JSON report and ordinary Markdown remains readable without the plugin.
caption: Bob writes the callout; the display-only card combines rows and JSON, while plain Markdown remains readable without the plugin.
review: "606.287x817 px, fit 100.0%; question, source, and visual checks passed; 1 revision, 2 visual rounds"
```

```mermaid
---
title: "Proposed Areas: who writes, who renders?"
config:
  flowchart:
    rankSpacing: 28
    nodeSpacing: 22
    wrappingWidth: 180
---
flowchart TB
  SYNC["`**bob areas sync**<br/>Guarded catalog writer`"]
  DATA["`**bob areas list**<br/>Versioned JSON report`"]
  subgraph NOTE["Vault note: ownership boundary"]
    direction TB
    USER["`**Bryan owns**<br/>Heading, position, other bytes`"]
    ROWS["`**Bob owns**<br/>Area callout rows`"]
    USER ~~~ ROWS
  end
  CARD["`**Display-only card**<br/>Both rows and JSON`"]
  PLAIN["`**Plain Markdown readers**<br/>Mobile, git, agents, PDFs`"]
  SYNC -.->|writes only| ROWS
  ROWS -.->|stored rows| CARD
  DATA -.->|titles and report data| CARD
  ROWS -.->|readable without plugin| PLAIN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class SYNC,DATA focus
  class ROWS outcome
  class USER,CARD,PLAIN muted
  class SYNC,DATA,USER,ROWS,CARD,PLAIN proposed
  style NOTE fill:none,stroke:#6B7280
```

## damage-and-cleanup

```yaml
anchor: |-
  An empty host loses the callout; the heading goes only when its section is
question: |-
  When does proposed sync update, remove, or preserve an existing Areas region?
illustrates: |-
  For existing regions on non-excluded notes, malformed openers leave the host untouched, eligible hosts with eligible descendants keep their callout, and cleanup removes the heading only when its section is blank.
caption: Malformed regions stay untouched; eligible hosts keep updated callouts, and cleanup removes headings only when their sections become blank.
review: "727.847x1032 px, fit 86.5%; question, source, and visual checks passed; 1 revision, 2 visual rounds"
```

```mermaid
---
title: "Proposed Areas sync: keep, update, or remove?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 170
---
flowchart TD
  DAMAGE{{"`**Malformed opener?**`"}}
  HOLD["`**Preserve host**<br/>Damage requires attention`"]
  HOST{{"`**Eligible host with descendants?**`"}}
  UPDATE["`**Update callout**<br/>Keep heading and prose`"]
  REMOVE["`**Remove callout**<br/>Stale or empty host`"]
  BLANK{{"`**Section now blank?**`"}}
  DROP["`**Remove heading**<br/>Blank section only`"]
  KEEP["`**Keep heading**<br/>Preserve authored prose`"]
  DAMAGE -.->|Yes| HOLD
  DAMAGE -.->|No| HOST
  HOST -.->|Yes| UPDATE
  HOST -.->|No| REMOVE
  REMOVE -.->|then check| BLANK
  BLANK -.->|Yes| DROP
  BLANK -.->|No| KEEP
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class DAMAGE,HOST,BLANK decision
  class UPDATE,REMOVE,DROP,KEEP outcome
  class HOLD risk
  class DAMAGE,HOST,BLANK,UPDATE,REMOVE,DROP,KEEP,HOLD proposed
```

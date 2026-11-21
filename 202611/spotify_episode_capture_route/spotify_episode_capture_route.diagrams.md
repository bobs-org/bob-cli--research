# Diagram proposals: Smarter `bob ref create` for Spotify URLs

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/spotify_episode_capture_route/spotify_episode_capture_route__final.md
producer: research.5r.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; deliberate parse failure exited nonzero"
```

## enrichment-gates

```yaml
anchor: |-
  if Spotify and RSS durations agree
question: |-
  Why can a verified transcript still have plain timestamps?
illustrates: |-
  A unique feed-item match agreeing on at least two signals permits publisher-transcript enrichment, while Spotify and RSS duration agreement separately determines whether timestamps become clickable links.
caption: For an available publisher transcript, a proven match permits attachment; a separate duration check decides whether timestamps are clickable.
review: "656.621x986 px, fit 90.5%; question, source trace, labels, arrowheads, crossings and reading direction passed visual checks; 0 revisions"
```

```mermaid
---
title: "Proposed: When are transcript timestamps clickable?"
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 18
    wrappingWidth: 230
---
flowchart TD
  EVIDENCE["`**Feed-item evidence**<br/>Title, release time, duration`"]
  MATCH{{"`**Unique match, ≥2 signals?**`"}}
  DOSSIER["`**Dossier only**<br/>Warn: no proven match`"]
  TEXT["`**Available publisher transcript**<br/>Attach verified text`"]
  CLOCK{{"`**Durations within ~10 seconds?**`"}}
  LINKS["`**Clickable timestamps**<br/>Link to Spotify moments`"]
  PLAIN["`**Plain timestamps**<br/>Keep labels without links`"]
  EVIDENCE -.->|Evaluate match| MATCH
  MATCH -.->|No| DOSSIER
  MATCH -.->|Yes; transcript available| TEXT
  TEXT -.->|Compare Spotify and feed| CLOCK
  CLOCK -.->|Yes| LINKS
  CLOCK -.->|No| PLAIN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class EVIDENCE focus
  class MATCH,CLOCK decision
  class DOSSIER,TEXT,LINKS,PLAIN outcome
  class EVIDENCE,MATCH,CLOCK,DOSSIER,TEXT,LINKS,PLAIN proposed
```

## capture-paths

```yaml
anchor: |-
  Today's broken capture is largely self-inflicted: the headless browser's
question: |-
  Why replace browser clipping with a dedicated episode route?
illustrates: |-
  Bob's own HTTP client retrieves structured episode metadata for Bob-owned Markdown, avoiding the Chrome user-agent shell while retaining the Chromium reader template for the episode dossier PDF.
caption: Browserless metadata fetch avoids Chrome's degraded shell; Bob-owned Markdown still prints through Chromium into the episode dossier PDF.
review: "670.469x673 px, fit 97.4%; question, source trace, labels, arrowheads, crossings and reading direction passed visual checks; 1 revision to place today before proposed"
```

```mermaid
---
title: "Why does the proposed episode route bypass browser clipping?"
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 24
    wrappingWidth: 230
---
flowchart TB
  subgraph FUTURE["Proposed — dedicated episode route"]
    direction TB
    HTTP["`**Metadata extraction**<br/>Bob's HTTP client`"]
    RICH["`**Rich page**<br/>Structured episode metadata`"]
    MARKDOWN["`**Bob-owned Markdown**<br/>Write-once source store`"]
    DOSSIER["`**Reference PDF**<br/>Episode dossier`"]
    HTTP -.->|Receives| RICH
    RICH -.->|Assemble| MARKDOWN
    MARKDOWN -.->|Chromium prints| DOSSIER
  end
  subgraph TODAY["Today — browser clipping"]
    direction TB
    BROWSER["`**Metadata extraction**<br/>Chrome user agent`"]
    SHELL["`**Degraded page**<br/>Empty app shell`"]
    STUB["`**Reference PDF**<br/>~56 words; truncated notes`"]
    BROWSER -->|Receives| SHELL
    SHELL -->|Defuddle clips| STUB
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class BROWSER,HTTP focus
  class SHELL,STUB risk
  class RICH,MARKDOWN,DOSSIER outcome
  class HTTP,RICH,MARKDOWN,DOSSIER proposed
  style TODAY fill:none,stroke:#C0392B
  style FUTURE fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

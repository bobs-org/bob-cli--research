# Diagram proposals: bob gmail — save the threads you choose as mail notes, send through Gmail drafts

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bob_gmail_design/bob_gmail_design__final.md
producer: research.3d.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 1 of 1 Mermaid diagrams; invalid-input check exited nonzero"
```

## sender-content-inertness

```yaml
anchor: |-
  Everything from the sender is data:
question: |-
  How do HTML and plain-text bodies become inert mail cards?
illustrates: |-
  The proposed renderer routes HTML through a sanitizing pre-pass and HTML-to-Markdown conversion, or falls back to plain text, before the required inert pass.
caption: Either body path must neutralize vault syntax before becoming a mail card; Phase 0 fixtures will confirm the HTML preference.
review: "448.914x892 px, fit 100%; reader question, labels, arrows, source trace and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: how is sender content made inert?"
accTitle: "Both body paths require the inert pass"
accDescr: "Useful HTML is cleaned and converted to Markdown; otherwise Bob falls back to plain text. Either path must then neutralize vault syntax before becoming a mail card. HTML preference remains subject to the renderer fixture spike."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 260
---
flowchart TD
  BODY{{"`**Useful HTML available?**`"}}
  CLEAN["`**HTML cleanup**<br/>Remove unsafe markup`"]
  CONVERT["`**HTML to Markdown**<br/>Preserve readable structure`"]
  PLAIN["`**Plain-text fallback**`"]
  INERT["`**Required inert pass**<br/>Neutralize vault syntax`"]
  CARD["`**Mail card**<br/>Sender content stays data`"]
  BODY -.->|"Yes"| CLEAN
  BODY -.->|"Absent or same text"| PLAIN
  CLEAN -.->|"convert"| CONVERT
  CONVERT -.->|"neutralize"| INERT
  PLAIN -.->|"neutralize"| INERT
  INERT -.->|"render"| CARD
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class BODY,INERT decision
  class CLEAN,CONVERT,PLAIN focus
  class CARD outcome
  class BODY,CLEAN,CONVERT,PLAIN,INERT,CARD proposed
```

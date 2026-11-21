# Diagram proposals: Wikilink completion in Bob's prose prompts — consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/prose_prompt_wikilink_completion/prose_prompt_wikilink_completion__final.md
producer: research.5o.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; retained Puppeteer --no-sandbox flags"
```

## controller-ownership

```yaml
anchor: |-
  arbiter (the recall band) lives in nav-hotkeys. One controller owning both
question: |-
  How do existing and new prompts share completion, recall and candidate data while retaining a plain-typing fallback?
illustrates: |-
  One proseField controller in bob-navigation-hotkeys owns both band modes, serves existing recall and explicit card consumers, and reads Obsidian metadata for link candidates.
caption: One controller owns recall and link modes; existing prompts use a wrapper, new cards feature-detect it, and missing support preserves plain typing.
review: "536.316×1119 px, fit 79.8%; question, source and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: who owns prose-field completion?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 260
---
flowchart TB
  subgraph HOSTS["Prompt hosts"]
    OLD["`**Recall prompts**<br/>Existing consumers`"]
    NEW["`**Intention / Record**<br/>Explicit consumers`"]
    PLAIN["`**Plain typing**<br/>Prompt still works`"]
  end
  subgraph NAV["Proposed · bob-navigation-hotkeys"]
    API["`**proseField v1**<br/>Keyboard owner`"]
    RECALL["`**USED BEFORE**<br/>Recall mode`"]
    LINK["`**LINK**<br/>Suppresses recall`"]
  end
  subgraph OBS["Obsidian · in-memory data"]
    DATA["`**Vault + cache**<br/>Link candidates`"]
  end
  OLD -.->|"recall wrapper"| API
  NEW -.->|"API present"| API
  NEW -.->|"API absent"| PLAIN
  API -.->|"owns"| RECALL
  API -.->|"owns"| LINK
  LINK -.->|"reads"| DATA
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class OLD,NEW,DATA muted
  class API,RECALL,LINK focus
  class API,RECALL,LINK proposed
  class PLAIN outcome
  style HOSTS fill:none,stroke:#6B7280
  style NAV fill:none,stroke:#3B78C2,stroke-dasharray:5 3
  style OBS fill:none,stroke:#6B7280
```

## band-lifecycle

```yaml
anchor: |-
  does not re-pop until a meaningful edit or caret re-entry. No cooldown
question: |-
  How does the link band return control without submitting a query or immediately reopening a dismissed token?
illustrates: |-
  The link band inserts without submitting, consumes zero-match Enter, and remembers an Esc-dismissed token until a meaningful edit or caret re-entry.
caption: Link acceptance keeps the prompt open; Esc remembers the dismissed token, and meaningful editing or caret re-entry can reopen completion.
review: "582.609×710 px, fit 100.0%; question, source and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: how does the link band hand control back?"
---
stateDiagram-v2
  direction TB
  state "Band closed<br/>Recall / host keys" as CLOSED
  state "LINK band open<br/>Recall suppressed" as OPEN
  state "Token dismissed<br/>Unchanged token stays closed" as DISMISSED
  CLOSED --> OPEN: Eligible [[ typed
  OPEN --> CLOSED: Enter / Tab accepts row<br/>Insert only, keep prompt open
  OPEN --> CLOSED: Backspace removes [[<br/>or Enter finds no matches<br/>No submission
  OPEN --> DISMISSED: Esc / Ctrl+[<br/>Remember this token
  DISMISSED --> OPEN: Meaningful edit<br/>or caret re-entry
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class OPEN focus
  class CLOSED outcome
  class DISMISSED muted
  class OPEN,CLOSED,DISMISSED proposed
```

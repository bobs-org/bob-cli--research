# Diagram proposals: Meeting notes become event-linked references: consolidated design

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/meeting_notes_event_refs/meeting_notes_event_refs__final.md
producer: research.65.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 3 of 3 Mermaid diagrams; Puppeteer --no-sandbox; deliberate parse failure returned nonzero"
```

## matching-fallback

```yaml
anchor: |-
  candidates and per-row evidence otherwise, exit 2 off a TTY.
question: |-
  When can Bob select an event, and when must it ask?
illustrates: |-
  Matching prioritizes explicit ref/URL and title queries, auto-selects only on a sole strong signal (recording-window overlap when present or ≥75% of title content words in the notes), and otherwise shows ranked candidates with evidence or exits 2 off a TTY.
caption: "Proposed auto-selection needs one strong match: recording-window overlap or ≥75% of title content words in notes; otherwise choose from evidence or exit 2 noninteractively."
review: "684.5×984 px, fit 90.7%; question, source, arrow, label, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: when does event matching ask?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 20
    wrappingWidth: 180
---
flowchart TD
  EXPLICIT{{"`**Event ref or URL?**`"}}
  STRONG{{"`**Sole strong signal?**`"}}
  TERMINAL{{"`**Interactive?**`"}}
  PICK["`**Ranked candidates**<br/>Show evidence; user chooses`"]
  SELECT["`**Selected event**<br/>Any one selection path`"]
  EXIT["`**Exit 2**<br/>No automatic selection`"]
  EXPLICIT -.->|"Yes: ref or URL"| SELECT
  EXPLICIT -.->|"No: query words<br/>against event titles"| STRONG
  STRONG -.->|"Yes: select automatically"| SELECT
  STRONG -.->|"No"| TERMINAL
  TERMINAL -.->|"Yes"| PICK
  TERMINAL -.->|"No"| EXIT
  PICK -.->|"chosen event"| SELECT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class EXPLICIT,STRONG,TERMINAL decision
  class PICK,EXIT focus
  class SELECT outcome
```

## review-dependency

```yaml
anchor: |-
  The reading task **is** the review — that is the insight
question: |-
  How does the proposed review remove the build dependency from follow-up?
illustrates: |-
  The reading task replaces the manual review chore that is blocked on a bob build task, so the Derrick follow-up email can proceed after skimming the TL;DR while feature work stays open.
caption: "Replacing the build-blocked chore with the reading task lets the Derrick follow-up proceed after a skim while feature work stays open."
review: "722×553 px, fit 90.4%; question, source, arrow, label, and visual checks passed; 1 revision"
```

```mermaid
---
title: "How does the proposed review free the follow-up?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 18
    wrappingWidth: 150
---
flowchart TB
  subgraph TODAY["Today: build blocks review"]
    direction TB
    BUILD["`**Feature work**<br/>Bob build task`"]
    CHORE["`**Review**<br/>Manual meeting-notes chore`"]
    EMAIL1["`**Follow-up email**<br/>Waiting on the review`"]
    BUILD -->|"blocks"| CHORE
    CHORE -->|"blocks"| EMAIL1
  end
  subgraph PROPOSAL["Proposed: independent review"]
    direction TB
    FEATURE["`**Feature work**<br/>Phases 1–2 stay open`"]
    READING["`**Review**<br/>Reading task born Next`"]
    EMAIL2["`**Follow-up email**<br/>Can proceed after a skim`"]
    READING -.->|"skim TL;DR permits"| EMAIL2
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class BUILD,CHORE,EMAIL1 risk
  class FEATURE,READING focus
  class EMAIL2 outcome
  class FEATURE,READING,EMAIL2 proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#3B78C2
```

## recap-ownership

```yaml
anchor: |-
  stays in the write-once store and the PDF; the recap is deliberately compact.
question: |-
  How does a searchable recap preserve the original record and user edits?
illustrates: |-
  The compact recap makes meeting text available to Obsidian search and hover while the verbatim source stays in the PDF and write-once store, and the digest guard prevents Bob from overwriting user-edited recap text.
caption: "The recap makes meeting text searchable while the PDF and write-once store preserve the source; the digest guard protects user edits."
review: "853×845 px, fit 76.5%; question, source, arrow, label, and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: searchable recap, protected record"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 185
---
flowchart TD
  SOURCE["`**Meeting source**<br/>Both destinations receive text`"]
  subgraph RECORD["Preserved original"]
    ARCHIVE["`**PDF + write-once store**<br/>Verbatim source`"]
  end
  subgraph NOTE["Reference note: recap above Highlights"]
    RECAP["`**Compact recap**<br/>Search and hover can read it`"]
    EDITED{{"`**User edited recap?**`"}}
    BOB["`**Bob-managed recap**<br/>Protected by digest check`"]
    USER["`**User-edited recap**<br/>Never overwritten by Bob`"]
    RECAP -.->|"digest checks ownership"| EDITED
    EDITED -.->|"No"| BOB
    EDITED -.->|"Yes"| USER
  end
  SOURCE -.->|"preserve verbatim"| ARCHIVE
  SOURCE -.->|"seed compact, inert prose"| RECAP
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class SOURCE,RECAP,BOB focus
  class EDITED decision
  class ARCHIVE,USER outcome
  style RECORD fill:none,stroke:#2E7D4F
  style NOTE fill:none,stroke:#3B78C2
```

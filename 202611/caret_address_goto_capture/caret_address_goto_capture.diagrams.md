# Diagram proposals: `@foo^bar` as an exact Go To address in Bob Capture

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/caret_address_goto_capture/caret_address_goto_capture__final.md
producer: research.6d.image
check: "mmdc 12.0.0 (Puppeteer --no-sandbox) with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## acceptance-keeps-draft

```yaml
anchor: |-
  Resolution is re-run at accept time (fresh parse before dispatch)
question: |-
  What prevents a stale preview or failed dispatch from consuming the draft?
illustrates: |-
  Accept-time resolution and the shared URI dispatch path preserve the draft on failure and discard without stashing after successful dispatch.
caption: Proposed acceptance re-resolves the address before dispatch; resolution or dispatch failures preserve the draft, while success discards without stashing.
review: "640.957×914 px, fit 97.7%; question, source-trace and visual checks passed; 0 revisions"
```

```mermaid
---
title: "How does address acceptance protect the draft?"
accDescr: "Proposed acceptance re-resolves the current address, preserves the draft on resolution or dispatch failure, and discards without stashing after successful dispatch."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 220
---
flowchart TD
  PARSE["`**Proposed acceptance**<br/>Fresh capture-parse`"]
  FOUND{{"`**Address still resolves?**`"}}
  UNRESOLVED["`**Keep draft**<br/>Explain resolution problem`"]
  URI["`**Dispatch Go To URI**<br/>Guard against double Return`"]
  SENT{{"`**Dispatch succeeds?**`"}}
  FAILED["`**Keep draft**<br/>Couldn't open Obsidian`"]
  DONE["`**Discard and hide**<br/>No stash`"]
  PARSE -.->|"recheck current draft"| FOUND
  FOUND -.->|"No"| UNRESOLVED
  FOUND -.->|"Yes"| URI
  URI -.->|"attempt dispatch"| SENT
  SENT -.->|"No"| FAILED
  SENT -.->|"Yes"| DONE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PARSE,URI focus
  class FOUND,SENT,UNRESOLVED,FAILED decision
  class DONE outcome
  class PARSE,FOUND,UNRESOLVED,URI,SENT,FAILED,DONE proposed
```

## non-task-landing-fallback

```yaml
anchor: |-
  `findTaskLineByBlockId` only re-finds **task** lines; when a non-task block shifts
question: |-
  Where does the optional block fallback improve landing when a non-task block moves?
illustrates: |-
  The optional findAnyLineByBlockId fallback extends re-finding to non-task blocks after task-line search returns null, while keeping the existing landing ladder.
caption: Optional hardening inserts an any-block lookup after task-only lookup misses, retaining the existing digest and clamped-line fallbacks.
review: "818×635 px, fit 79.8%; question, source-trace and visual checks passed; 1 layout revision"
```

```mermaid
---
title: "What changes after task-only block lookup misses?"
accDescr: "Today's handler continues through digest and clamped-line fallback. The optional proposal first tries a unique block on any non-fenced line, then retains existing fallbacks on a miss."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TD
  subgraph PROPOSAL["Proposed optional hardening"]
    P["`**Task-only lookup**<br/>No matching task`"]
    ANY{{"`**Unique block on any line?**`"}}
    LAND["`**Re-find block**<br/>Land at its line`"]
    PF["`**Existing fallback**<br/>Unique digest, then clamped line`"]
    P -.->|"scan outside fenced code"| ANY
    ANY -.->|"Yes"| LAND
    ANY -.->|"No"| PF
  end
  subgraph TODAY["Today"]
    T["`**Task-only lookup**<br/>No matching task`"]
    TF["`**Existing fallback**<br/>Unique digest, then clamped line`"]
    T -->|"continue"| TF
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class T,TF,P,PF focus
  class ANY decision
  class LAND outcome
  class ANY,LAND proposed
  style TODAY fill:none,stroke:#3B78C2
  style PROPOSAL fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

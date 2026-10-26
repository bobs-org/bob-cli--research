# Diagram proposals: Copying Code Blocks from the Bob Refs Copy Card, and ⌘Y in Highlights

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/ref_code_block_copy/ref_code_block_copy__final.md
producer: research.5b.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## protect-saved-sources

```yaml
anchor: |-
  a nightly archive or a task move could
question: |-
  Why must task walkers skip .bob before Markdown sources are stored?
illustrates: |-
  Excluding .bob prevents task archive and link repair from silently editing write-once sources and failing the digest check.
caption: "Either walker can silently edit saved Markdown; the proposed .bob exclusion protects sources from both."
review: "860x613 px, fit 75.9%; question, source-trace, and visual checks passed; 2 revisions, 2 visual look rounds; unique anchor verified"
```

```mermaid
---
title: "Why must task walkers skip .bob?"
accTitle: "Protect saved Markdown from task walkers"
accDescr: "Without exclusion, either task archive or link repair can silently edit a saved source and fail its digest check. The proposed .bob exclusion makes both walkers skip the source."
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 8
    wrappingWidth: 120
---
flowchart LR
  subgraph RISK["Without exclusion: either walker"]
    direction TB
    A["`**Task archive**<br/>Removes done tasks`"]
    L["`**Link repair**<br/>Rewrites note links`"]
    S["`**Saved source**<br/>May be edited`"]
    D["`**Digest check**<br/>Fails after edits`"]
    A -->|"can modify"| S
    L -->|"can modify"| S
    S -->|"invalidates"| D
  end
  subgraph SAFE["Proposed: exclude .bob"]
    direction TB
    A2["`**Task archive**<br/>Excludes .bob`"]
    L2["`**Link repair**<br/>Excludes .bob`"]
    S2["`**Saved source**<br/>Stays unchanged`"]
    A2 -.->|"skips"| S2
    L2 -.->|"skips"| S2
  end
  RISK ~~~ SAFE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class A,L,A2,L2 focus
  class S,D risk
  class S2 outcome
  class A2,L2,S2 proposed
  style RISK fill:none,stroke:#C0392B
  style SAFE fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

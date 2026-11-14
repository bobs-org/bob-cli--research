# Diagram proposals: Bank walk family `b`: `]b` / `[b` / `]B` / `[B` with a fourth walker-footer panel

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_walk_family_b/bank_walk_family_b__final.md
producer: research.4n.image
check: "mmdc 12.0.0 (Puppeteer --no-sandbox) with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## landing-retry

```yaml
anchor: |-
  on failure, re-snapshot and re-plan **once**, then refuse with
question: |-
  When does a failed bank-row landing retry, and when does it refuse?
illustrates: |-
  Identity-based landing gets a single re-plan, then an explicit refusal, so the walk never lands on a guess.
caption: The proposed walk retries failed identity resolution once, then refuses; it never guesses a landing.
review: "665.954×738 px, fit 98.0%; question, source, and visual checks passed; 0 visual revisions"
```

```mermaid
---
title: "Proposed: retry a changed row once, then refuse"
accTitle: "Bounded bank-row landing recovery"
accDescr: "Resolve a row by identity. An unambiguous match lands at the payee start. A failure triggers one fresh snapshot and re-plan; a repeated failure refuses the landing. Dashed arrows show the proposed control flow."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  RESOLVE["`**Resolve row**<br/>ID, then exact text`"]
  MATCH{{"`**Unambiguous match?**`"}}
  LAND["`**Land at payee start**<br/>One jump-history entry`"]
  TRIED{{"`**Already retried?**`"}}
  RETRY["`**Fresh snapshot**<br/>Re-plan once`"]
  REFUSE["`**Refuse landing**<br/>Bank rows changed — try again`"]
  RESOLVE -.->|"check result"| MATCH
  MATCH -.->|"Yes"| LAND
  MATCH -.->|"Missing or ambiguous"| TRIED
  TRIED -.->|"No"| RETRY
  RETRY -.->|"resolve new plan"| RESOLVE
  TRIED -.->|"Yes"| REFUSE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class RESOLVE,LAND,RETRY focus
  class MATCH,TRIED decision
  class REFUSE risk
  class RESOLVE,MATCH,LAND,TRIED,RETRY,REFUSE proposed
```

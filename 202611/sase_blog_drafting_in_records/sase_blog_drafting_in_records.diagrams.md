# Diagram proposals: Drafting the SASE blog post in record notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/sase_blog_drafting_in_records/sase_blog_drafting_in_records__final.md
producer: research.4f.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; Puppeteer --no-sandbox"
```

## album-trial-fallback

```yaml
anchor: |-
  or if after Wave 1 most pieces feel
question: |-
  When should the album experiment give way to article-only writing?
illustrates: |-
  Article-only is the fallback when album setup exceeds one Pomodoro or, after Wave 1, most pieces feel inseparable and file-switching hurts more than it helps.
caption: Either fallback trigger leads to article-only writing; after Wave 1, the trigger requires inseparable pieces and file-switching that hurts more than helps.
review: "609.766x786 px, fit 100%; reader-question, source-trace, and visual checks passed; 1 visual revision, 0 parse repairs; unique body anchor confirmed"
```

```mermaid
---
title: "When should the proposed album trial stop?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 22
    wrappingWidth: 260
---
flowchart TD
  SETUP{{"`**Setup within one Pomodoro?**`"}}
  WAVE["`**Wave 1**<br/>Dictate four zero-drafts`"]
  FRICTION{{"`**Both conditions?**<br/>Most pieces inseparable;<br/>switching hurts more than helps`"}}
  KEEP["`**Continue album workflow**<br/>Claim-sized records`"]
  ARTICLE["`**Continue in the article**<br/>Keep only reusable examples as records`"]
  SETUP -.->|"Yes"| WAVE
  SETUP -.->|"No: timebox exceeded"| ARTICLE
  WAVE -.->|"After Wave 1"| FRICTION
  FRICTION -.->|"No"| KEEP
  FRICTION -.->|"Yes: both"| ARTICLE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class SETUP,FRICTION decision
  class WAVE focus
  class KEEP,ARTICLE outcome
  class SETUP,FRICTION,WAVE,KEEP,ARTICLE proposed
```

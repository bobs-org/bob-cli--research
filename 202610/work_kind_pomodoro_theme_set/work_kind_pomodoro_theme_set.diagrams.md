# Diagram proposals: Work-kind Pomodoro themes: what six months of work supports

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/work_kind_pomodoro_theme_set/work_kind_pomodoro_theme_set__final.md
producer: research.2q.image
check: "mmdc 12.0.0 (Puppeteer --no-sandbox) with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## planning-estimates

```yaml
anchor: |-
  That happens even when the session also lists the implementation tasks you were
question: |-
  Why does the same morning work produce different planning estimates?
illustrates: |-
  Bob sends a qualifying mixed session wholly to the review bucket, while cld splits its minutes evenly across units, so neither total is pure planning time.
caption: For mixed sessions qualifying as review, Bob counts every minute; even unit splits undercount review. Neither method isolates planning time.
review: "562.922x542 px, fit 100.0%; question and visual checks passed; 1 revision; every node and edge traced to the evidence-base passage; anchor unique"
```

```mermaid
---
title: "Why do planning estimates differ?"
accTitle: "Two ways to count a mixed morning session"
accDescr: "For a mixed review and implementation-dispatch session that qualifies for Bob's review bucket, Bob counts all minutes as review. The cld researcher splits minutes evenly across units, assigning only review units to planning. Neither isolates pure planning time."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 18
    wrappingWidth: 240
---
flowchart TD
  MIXED["`**Qualifying mixed session**<br/>Review and task dispatch`"]
  WHOLE["`**Bob Stats**<br/>Whole session becomes review`"]
  HIGH["`**Review total**<br/>Includes implementation dispatch`"]
  SPLIT["`**Researcher's unit split**<br/>Even minutes per unit`"]
  LOW["`**Planning total**<br/>Undercounts review here`"]
  MIXED -->|Bob method| WHOLE
  MIXED -->|cld method| SPLIT
  WHOLE -->|counts| HIGH
  SPLIT -->|counts only review units| LOW
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  class MIXED focus
  class WHOLE,SPLIT,HIGH,LOW muted
```

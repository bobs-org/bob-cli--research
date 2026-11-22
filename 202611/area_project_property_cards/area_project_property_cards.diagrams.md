# Diagram proposals: Area and project property cards: consolidated research

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/area_project_property_cards/area_project_property_cards__final.md
producer: research.5y.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## count-writer-retirement

```yaml
anchor: |-
  every task edit, race `bob props` fingerprints
question: |-
  Why can task-count updates invalidate an open property draft, and what does retiring that writer remove?
illustrates: |-
  Retiring the bob-project-tasks count writer removes count-triggered staleness refusals from open =+ drafts while retaining bob props fingerprint checks and byte-preserving updates.
caption: Retiring the count writer removes count-triggered draft invalidation; ordinary fingerprint checks still protect edits.
review: 664.656 × 553 px, fit 98.2%; reader-question, source, arrow, label and visual checks passed; 1 visual revision
```

```mermaid
---
title: "Why retire the project count writer?"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 28
    wrappingWidth: 220
---
flowchart TB
  subgraph PROPOSAL["Proposed default: count writer retired"]
    direction TB
    NEW["`**Open =+ draft**<br/>Fingerprint still checked`"]
    PROPS["`**bob props update**<br/>Validated, byte-preserving writer`"]
    YAML["`**YAML block**<br/>Untouched bytes preserved`"]
    NEW -.->|"applies through"| PROPS
    PROPS -.->|"writes"| YAML
  end
  subgraph TODAY["Today: count writer remains"]
    direction TB
    TASK["`**Task edit**<br/>Triggers metadata change`"]
    COUNT["`**Count writer**<br/>Re-serializes the YAML block`"]
    OLD["`**Open =+ draft**<br/>Stale refusal; draft kept`"]
    TASK -->|"triggers"| COUNT
    COUNT -->|"invalidates fingerprint"| OLD
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class TASK,NEW,PROPS focus
  class COUNT,OLD risk
  class YAML outcome
  class NEW,PROPS,YAML proposed
  style TODAY fill:none,stroke:#C0392B
  style PROPOSAL fill:none,stroke:#2E7D4F
```

## bank-foot-ownership

```yaml
anchor: |-
  (restoring it if the Area mount fails); `==` keeps opening the bank editor
question: |-
  Who owns bank.md's title and foot row when the Area mount works or fails?
illustrates: |-
  While the Area owner is active it owns the single foot row and frontmatter takeover; if mounting fails, native chrome and bank_foot return.
caption: The Area card owns the foot row only while active; mount failure restores native chrome and the bank card’s temporary foot.
review: 560 × 564 px, fit 100.0%; reader-question, source, arrow, label and visual checks passed; 0 revisions
```

```mermaid
---
title: "Who owns bank.md's foot row? (Proposed)"
config:
  flowchart:
    rankSpacing: 22
    nodeSpacing: 28
    wrappingWidth: 220
---
flowchart TD
  OWNER{{"`**Area owner active?**`"}}
  AREA["`**Area title card**<br/>Owns foot and frontmatter takeover`"]
  HIDDEN["`**Bank body card**<br/>Temporary bank_foot suppressed`"]
  NATIVE["`**Native chrome**<br/>Title, H1, Properties restored`"]
  RESTORED["`**Bank body card**<br/>Temporary bank_foot restored`"]
  OWNER -.->|"Yes"| AREA
  OWNER -.->|"No: mount fails"| NATIVE
  AREA -.->|"paired with"| HIDDEN
  NATIVE -.->|"paired with"| RESTORED
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OWNER decision
  class AREA,HIDDEN focus
  class NATIVE,RESTORED outcome
  class OWNER,AREA,HIDDEN,NATIVE,RESTORED proposed
```

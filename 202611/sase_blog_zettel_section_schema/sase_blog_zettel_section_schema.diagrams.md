# Diagram proposals: A `section` field for the SASE Blog Zettel album: consolidated recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/sase_blog_zettel_section_schema/sase_blog_zettel_section_schema__final.md
producer: research.4w.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; no-sandbox Puppeteer flag; SVG and PNG inspected"
```

## targeting-and-assembly

```yaml
anchor: |-
  The spine has none, and Obsidian Bases cannot see
question: |-
  Why add section targeting if the spine can link to records?
illustrates: |-
  A section field supports usage counts and grouping that heading-level spine links cannot supply to Bases, while spine wikilinks remain the assembly mechanism for placed material.
caption: "Section fields make coverage visible; the spine keeps assembly and article order."
review: "688.516x601 px, fit 94.8%; question, source-trace and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why add section targeting alongside spine links?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 16
    wrappingWidth: 180
---
flowchart TB
  subgraph PRIOR["Prior plan: spine links only, never adopted"]
    direction TB
    OLD["`**Spine**<br/>Heading links to records`"]
    BACK["`**Bases backlinks**<br/>Files, not individual headings`"]
    GAP["`**Coverage gap**<br/>Cannot identify empty sections`"]
    OLD -->|"exposes only"| BACK
    BACK -->|"cannot answer coverage"| GAP
  end
  subgraph PROPOSED["Proposed: targeting plus assembly"]
    direction TB
    SPINE["`**Spine**<br/>Order, wording and transitions`"]
    FIELD["`**Records**<br/>Capture a section key`"]
    COVER["`**Section coverage**<br/>Usage counts and grouped views`"]
    SPINE -.->|"links records for assembly"| FIELD
    FIELD -.->|"enables section-based views"| COVER
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class OLD,BACK,SPINE,FIELD focus
  class GAP risk
  class COVER outcome
  class SPINE,FIELD,COVER proposed
  style PRIOR fill:none,stroke:#3B78C2
  style PROPOSED fill:none,stroke:#2E7D4F,stroke-dasharray:5 3
```

## guarded-migration-order

```yaml
anchor: |-
  Removing `part` from the schema while the record still carries
question: |-
  How does edit order affect guarded cleanup of part?
illustrates: |-
  Removing part from the schema while a record still carries it makes the guarded cleanup refuse the field, so Path B clears the record value before removing the unused schema field.
caption: "In the guarded route, clear the record's part value before removing the schema field; removing the schema first blocks cleanup."
review: "500x1036 px, fit 86.2%; question, source-trace and visual checks passed; 0 revisions"
```

```mermaid
---
title: "How does edit order affect guarded cleanup?"
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 16
    wrappingWidth: 190
---
flowchart TD
  START["`**Existing record**<br/>part: why`"]
  FIRST{{"`**Which schema edit first?**`"}}
  BAD["`**Remove part first**<br/>Record still carries part`"]
  BLOCK["`**Cleanup refused**<br/>Unknown field; guarded update blocked`"]
  ADD["`**Proposed: add section**<br/>Keep part in schema`"]
  UPDATE["`**Update the record**<br/>Set section=macros; clear part`"]
  REMOVE["`**Remove unused part**<br/>Then validate album and records`"]
  START -->|"schema edit choice"| FIRST
  FIRST -->|"remove part"| BAD
  BAD -->|"checking and cleanup fail"| BLOCK
  FIRST -.->|"proposed guarded route"| ADD
  ADD -.->|"then run guarded update"| UPDATE
  UPDATE -.->|"after the value is cleared"| REMOVE
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class START,FIRST decision
  class BAD,BLOCK risk
  class ADD,UPDATE,REMOVE outcome
  class ADD,UPDATE,REMOVE proposed
```

# Diagram proposals: Album notes: give every record collection an owner area

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/album_and_record_notes/album_and_record_notes__final.md
producer: research.43.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; broken-input nonzero check passed"
```

## schema-failure

```yaml
anchor: |-
  With `[[record]]`, records are recognized structurally, and a
question: |-
  What changes when a record schema breaks?
illustrates: |-
  Records are recognized structurally with `[[record]]`, so a broken album fails validation without changing record membership.
caption: "With proposed record typing, schema errors block the affected capture route without erasing record membership."
review: "860.422x577 px, fit 75.9%; question, source-trace, labels, arrows, crossings, and visual checks passed; 1 revision"
```

```mermaid
---
title: "What changes when a record schema breaks?"
accTitle: "Record recognition before and after album schemas"
accDescr: "Today a swallowed config error empties the configured kind set and records become ordinary notes. Proposed record types preserve structural membership while a broken album refuses its own capture route."
config:
  flowchart:
    rankSpacing: 20
    nodeSpacing: 16
    wrappingWidth: 180
---
flowchart TB
  subgraph NEXT["Proposed: separate recognition and validation"]
    direction TB
    TYPE["`**Record type**<br/>Structural membership`"]
    MEMBER["`**Records recognized**<br/>Independent of schema health`"]
    BAD["`**Album schema error**<br/>One claimed kind`"]
    REFUSE["`**Capture refuses**<br/>Album diagnostic`"]
    TYPE -.->|"preserves"| MEMBER
    BAD -.->|"blocks its route"| REFUSE
  end
  subgraph TODAY["Today: recognition depends on config"]
    direction TB
    CFG["`**Config error**<br/>Host-global schema file`"]
    IDS["`**Empty record-id set**<br/>Snapshot swallows error`"]
    ORD["`**Records misclassified**<br/>Ordinary notes`"]
    CFG -->|"empties"| IDS
    IDS -->|"reclassifies records as"| ORD
  end
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class CFG,IDS,ORD,BAD,REFUSE risk
  class TYPE focus
  class MEMBER outcome
  class TYPE,MEMBER,BAD,REFUSE proposed
  style TODAY fill:none,stroke:#C0392B
  style NEXT fill:none,stroke:#3B78C2,stroke-dasharray:5 3
```

## schema-cutover

```yaml
anchor: |-
  The vault and chezmoi are separate repositories, so this cannot be one atomic
question: |-
  How can the release precede the schema move safely?
illustrates: |-
  The transition rule makes the gap harmless because an album-aware bob ignores any config kind that an album claims.
caption: "After every host upgrades, albums take precedence during the gap between the vault cutover and config deletion."
review: "498.484x868 px, fit 100.0%; question, source-trace, labels, arrows, crossings, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed cutover: when can schemas move?"
accTitle: "Proposed schema-source lifecycle during the cutover"
accDescr: "Album-aware bob can use legacy config for unclaimed kinds while hosts upgrade. All three hosts must upgrade before the vault cutover. Albums then own their kinds while old config is still present, and config can be removed separately."
config:
  flowchart:
    rankSpacing: 14
    nodeSpacing: 20
    wrappingWidth: 260
---
flowchart TD
  RELEASE["`**Album-aware release**<br/>Unclaimed kinds use config`"]
  HOSTS{{"`**All three hosts upgraded?**`"}}
  HOLD["`**Wait for upgrades**<br/>Vault stays on config`"]
  CUT["`**Vault cutover**<br/>Albums claim four kinds`"]
  GAP["`**Old config present**<br/>Albums are authoritative`"]
  CLEAN["`**Delete chezmoi config**<br/>Album schemas stay in vault`"]
  RELEASE -.->|"cutover gate"| HOSTS
  HOSTS -.->|"No"| HOLD
  HOSTS -.->|"Yes: reviewed commit"| CUT
  CUT -.->|"before config deletion"| GAP
  GAP -.->|"separate config edit"| CLEAN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class RELEASE,CUT,GAP focus
  class HOSTS,HOLD decision
  class CLEAN outcome
  class RELEASE,HOSTS,HOLD,CUT,GAP,CLEAN proposed
```

# Diagram proposals: bank.md Is a Bank Hub, Not an Area

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_hub_demotion/bank_hub_demotion__final.md
producer: research.6h.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 3 of 3 Mermaid diagrams"
```

## type-edit-residue

```yaml
anchor: |-
  an untyped hub still receives the full eight-setting area contract from `bob props`
question: |-
  Why does untyping remove a card but leave area settings?
illustrates: |-
  Untyping stops the Area Card from mounting, but the path-keyed Bank contract still exposes the eight area settings.
caption: "A type-only edit removes the Area Card; removing the residual area settings also requires changing the Bank contract."
review: "703.156×770 px, fit 92.8%; question and visual checks passed; 1 revisions"
```

```mermaid
---
title: "Why does a type edit leave area settings?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 260
---
flowchart TD
  subgraph TODAY["Today: area-typed hub"]
    direction LR
    T["`**bank.md**<br/>Area type present`"]
    TB["`**Bank Card**<br/>Path-owned`"]
    TA["`**Area Card**<br/>Type-owned`"]
    TS["`**Area settings**<br/>Eight settings`"]
    T -->|"path enables"| TB
    T -->|"area type enables"| TA
    T -->|"Bank contract enables"| TS
  end
  subgraph UNTYPED["Observed after only removing type"]
    direction LR
    U["`**bank.md**<br/>Untyped hub`"]
    UB["`**Bank Card**<br/>Path-owned`"]
    US["`**Area settings**<br/>Eight settings remain`"]
    U -->|"path still enables"| UB
    U -->|"Bank contract still enables"| US
  end
  TODAY ~~~ UNTYPED
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  class T,U,TB,UB focus
  class TA,TS,US risk
  style TODAY fill:none,stroke:#C0392B
  style UNTYPED fill:none,stroke:#3B78C2
```

## album-parent-failure

```yaml
anchor: |-
  albums must parent to an area or project (`albums/registry.rs::analyze_direct_parent` →
question: |-
  Why can the wrong parent silently disable subscription matching?
illustrates: |-
  An invalid album parent disables subscription matching with a warning even though albums list still exits 0.
caption: "Reparenting subscriptions to cash preserves matching; leaving an untyped bank parent causes errors that exit codes alone can hide."
review: "583.039×788 px, fit 100.0%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "How can a parent error hide subscription loss?"
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 22
    wrappingWidth: 200
---
flowchart TD
  A["`**subscriptions.md**<br/>Subscription album`"]
  Q{{"`**Parent is area/project?**`"}}
  GOOD["`**Proposed: cash parent**<br/>Matching preserved`"]
  BAD["`**Album parent error**<br/>Both effects below`"]
  LOST["`**Subscription noun invalid**<br/>Matching disabled; warning`"]
  ZERO["`**albums list**<br/>Still exits 0`"]
  A -->|"parent validation"| Q
  Q -.->|"Yes: proposed cash"| GOOD
  Q -->|"No: untyped bank"| BAD
  BAD -->|"effect"| LOST
  BAD -->|"also"| ZERO
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class A,Q decision
  class GOOD outcome
  class GOOD proposed
  class BAD,LOST,ZERO risk
```

## capture-picker-bypass

```yaml
anchor: |-
  `bank.md`: `bob capture-targets` no longer lists `bank` (type-keyed, confirmed),
question: |-
  Why can a hidden @bank route still write a task?
illustrates: |-
  After demotion, capture-targets no longer lists bank, but direct @bank capture still writes a task because the write path ignores frontmatter.
caption: "The picker filters by type while direct capture accepts the root filename; hiding bank therefore does not prevent task writes."
review: "459.117×494 px, fit 100.0%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why can a hidden bank route still write tasks?"
config:
  flowchart:
    rankSpacing: 32
    nodeSpacing: 28
    wrappingWidth: 215
---
flowchart TD
  HUB["`**Untyped bank.md**<br/>Existing vault-root file`"]
  PICK["`**capture-targets**<br/>Filters by type`"]
  WRITE["`**Direct @bank capture**<br/>Ignores frontmatter`"]
  HIDDEN["`**Picker result**<br/>bank omitted`"]
  TASK["`**Write result**<br/>#task added to bank.md`"]
  HUB -->|"picker lookup"| PICK
  HUB -->|"explicit @bank request"| WRITE
  PICK -->|"observed result"| HIDDEN
  WRITE -->|"observed result"| TASK
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  class HUB,PICK focus
  class HIDDEN outcome
  class WRITE,TASK risk
```

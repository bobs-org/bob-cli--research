# Diagram proposals: One tie per pair: dependencies and plain links

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/plain_link_dependency_exclusivity/plain_link_dependency_exclusivity__final.md
producer: research.6f.image
check: "mmdc 12.0.0 (Puppeteer --no-sandbox) with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## release-confirmation

```yaml
anchor: |-
  commit on one press with the consequence strip
question: |-
  When does a release commit, and when does Escape keep the dependency?
illustrates: |-
  A proposed release commits on one Ctrl+L press or a second Enter press, while Escape keeps an armed dependency release from landing.
caption: "Ctrl+L commits the previewed release; Enter arms a second press, and Escape keeps the dependency."
review: "557.078x740 px, fit 100%; question, source trace, labels, arrows and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: when does a dependency release commit?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 220
---
flowchart TD
  PREVIEW["`**Consequence strip**<br/>Shows the planned result`"]
  KEY{{"`**Release key?**`"}}
  ARMED["`**Armed release**<br/>Names dependency and status change`"]
  COMMIT["`**Commit release**<br/>Apply the planned tie change`"]
  KEEP["`**Keep dependency**<br/>Escape cancels the release`"]
  PREVIEW -.->|"before the key"| KEY
  KEY -.->|"Ctrl+L"| COMMIT
  KEY -.->|"Enter"| ARMED
  ARMED -.->|"Enter again"| COMMIT
  ARMED -.->|"Escape"| KEEP
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class PREVIEW focus
  class KEY,ARMED decision
  class COMMIT,KEEP outcome
  class PREVIEW,KEY,ARMED,COMMIT,KEEP proposed
```

## cross-note-failures

```yaml
anchor: |-
  **Cross-note conversions** write the **dependency side first** through the existing
question: |-
  What remains if a cross-note conversion only partly succeeds?
illustrates: |-
  Proposed cross-note conversions write the dependency side first; a failed link-side write then leaves either a plain link for reconcile or a valid untied pair with a notice.
caption: "Failure paths only: dependency-write failure stops; later link-write failure leaves redundancy for reconcile or an untied pair with a notice."
review: "592.102x938 px, fit 95.2%; question, source trace, labels, arrows and visual checks passed; 1 revision, 2 look rounds"
```

```mermaid
---
title: "Proposed: what if a cross-note write fails?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  DEP{{"`**Dependency write succeeds?**`"}}
  STOP["`**Stop**<br/>No link-side write`"]
  FAIL["`**Link-side failure**<br/>Dependency change already landed`"]
  KIND{{"`**Adding or releasing?**`"}}
  LEFT["`**Dependency + plain link**<br/>Redundant link remains`"]
  HEAL["`**Reconcile**<br/>Removes leftover plain link`"]
  UNTIED["`**Valid untied pair**<br/>Notice: link not added`"]
  DEP -.->|"No"| STOP
  DEP -.->|"Yes; link write fails"| FAIL
  FAIL -.->|"by conversion type"| KIND
  KIND -.->|"Adding dependency"| LEFT
  KIND -.->|"Releasing dependency"| UNTIED
  LEFT -.->|"later repair"| HEAL
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class DEP,KIND decision
  class STOP,FAIL,LEFT risk
  class HEAL,UNTIED outcome
  class DEP,STOP,FAIL,KIND,LEFT,HEAL,UNTIED proposed
```

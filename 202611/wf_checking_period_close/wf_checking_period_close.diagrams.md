# Diagram proposals: WF Checking closing balance on period notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/wf_checking_period_close/wf_checking_period_close__final.md
producer: research.50.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; the deliberately broken probe exited nonzero"
```

## historical-balance-proof

```yaml
anchor: |-
  Every other anchor in the span must reproduce from the canonical
question: |-
  How does a covered span support a trustworthy historical balance?
illustrates: |-
  The proposed resolver requires agreement among the span's bank anchors and no overlapping CSV window, then reconstructs the historical posted balance from the canonical anchor and journal cents using the matching target-date branch.
caption: With matching bank anchors and no overlapping comma-separated values (CSV) imports, use the matching date branch to reconstruct a historical balance.
review: "748.857x1078 px, fit 82.8%; question, visual, claim-trace, and unique-anchor checks passed; 0 visual revisions; matching-branch convergence means any one branch"
```

```mermaid
---
title: "How is a historical balance proved? (Proposed)"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 180
---
flowchart TD
  COVERED["`**Covered target date**<br/>Within a bank-statement span`"]
  CHECK{{"`**All anchors agree?**<br/>No CSV overlap?`"}}
  FAIL["`**Unverified**<br/>No number; give reason`"]
  DATE{{"`**Target date versus anchor?**`"}}
  BACK["`**Canonical anchor**<br/>Subtract later non-CSV postings`"]
  SAME["`**Anchor balance**<br/>Use the same-day amount`"]
  FORWARD["`**Canonical anchor**<br/>Add subsequent non-CSV postings`"]
  BALANCE["`**Historical posted balance**<br/>Pre-tracking journal history included`"]
  COVERED -.->|requires both checks| CHECK
  CHECK -.->|Either fails| FAIL
  CHECK -.->|Both hold| DATE
  DATE -.->|Before| BACK
  DATE -.->|Same date| SAME
  DATE -.->|After| FORWARD
  BACK -.->|Matching branch gives| BALANCE
  SAME -.->|Matching branch gives| BALANCE
  FORWARD -.->|Matching branch gives| BALANCE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class COVERED,BACK,SAME,FORWARD focus
  class CHECK,DATE,FAIL decision
  class BALANCE outcome
  class COVERED,CHECK,FAIL,DATE,BACK,SAME,FORWARD,BALANCE proposed
```

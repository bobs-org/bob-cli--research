# Diagram proposals: The jump pin: Ctrl+J on the successor card

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/successor_jump_pin/successor_jump_pin__final.md
producer: research.5m.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; no-sandbox Puppeteer flag; negative parser test passed"
```

## pin-lifetime

```yaml
anchor: |-
  The pin dies with the card. Esc discards it with everything else
question: |-
  When is the jump pin kept, moved, or cleared?
illustrates: |-
  The pin survives verdict and mark changes, filtering and folding, and the Mac's Back and refusal reopens, while reset events and card closure discard it.
caption: A pin survives verdicts, filtering, and Mac Back or refusal reopens, but explicit resets and card closure discard it.
review: "511.391×670 px, fit 100%; question and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: When is the jump pin kept or cleared?"
---
stateDiagram-v2
  direction TB
  state "No jump pin" as CLEAR
  state "One task pinned" as PIN
  state "Card closed; pin discarded" as CLOSED
  CLEAR --> PIN: Ctrl+J on a keyed row
  PIN --> PIN: Ctrl+J elsewhere moves pin<br/>Verdict / mark / filter / fold keep it<br/>Mac Back / refusal keep it
  PIN --> CLEAR: Ctrl+J again clears pin<br/>New draft / preview clears it<br/>Refresh loses key: clear visibly
  PIN --> CLOSED: Commit: request jump<br/>OR Esc: discard without jump
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class PIN focus
  class CLEAR,CLOSED muted
  class PIN,CLEAR,CLOSED proposed
```

## failure-boundary

```yaml
anchor: |-
  refuses and the card reopens with its staged state
question: |-
  How does Mac Capture handle stale selectors before commit versus a lost target afterwards?
illustrates: |-
  Mac Capture refuses stale offer selectors before any writes, while post-commit resolution failure leaves writes in place and skips the jump.
caption: Stale selectors stop Mac Capture before writes; losing the target after commit skips navigation and never replays the close.
review: "614.172×786 px, fit 100%; question and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: When does Mac Capture refuse or continue?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 12
    wrappingWidth: 200
---
flowchart TD
  VALID{{"`**Offer selectors current?**`"}}
  REFUSE["`**Refuse without writes**<br/>Reopen staged card`"]
  COMMIT["`**Capture commits**<br/>Writes stand`"]
  FOUND{{"`**Target found after writes?**`"}}
  JUMP["`**Jump once**<br/>Focus the target`"]
  LOST["`**Skip the jump**<br/>Notice; never replay close`"]
  VALID -.->|"No: stale selector"| REFUSE
  VALID -.->|"Yes"| COMMIT
  COMMIT -.->|"Resolve target"| FOUND
  FOUND -.->|"Yes"| JUMP
  FOUND -.->|"No: target lost"| LOST
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class VALID,FOUND decision
  class COMMIT,JUMP outcome
  class REFUSE,LOST risk
  class VALID,FOUND,COMMIT,JUMP,REFUSE,LOST proposed
```

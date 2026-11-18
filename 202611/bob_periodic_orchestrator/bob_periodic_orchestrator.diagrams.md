# Diagram proposals: One command for Bob's frequent Mac work: build `bob tick`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bob_periodic_orchestrator/bob_periodic_orchestrator__final.md
producer: research.5c.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## refs-admission

```yaml
anchor: |-
  The `refs` step's scheduled gate: run only when
question: |-
  Which conditions admit a scheduled PDF library scan?
illustrates: |-
  The proposed refs gate admits a scheduled scan when the listing fingerprint changes, a pre-scan hook is configured, or the full-scan safety ceiling has elapsed.
caption: "A changed library listing, configured pre-scan hook, or elapsed full-scan ceiling admits a scheduled reference scan; otherwise it is skipped."
review: "559.813x760 px, fit 100.0%; question, source, and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when would a scheduled refs scan run?"
accTitle: "Scheduled reference scan admission"
accDescr: "Any one of three conditions admits a scheduled scan: the library listing fingerprint differs from the last successful scan, a pre-scan hook is configured, or the full-scan safety ceiling has elapsed. If none holds, skip this scan."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 20
    wrappingWidth: 260
---
flowchart TD
  CHANGED{{"`**Fingerprint changed?**<br/>Since last successful scan`"}}
  HOOK{{"`**Pre-scan hook configured?**`"}}
  AGE{{"`**Full-scan ceiling exceeded?**`"}}
  SCAN["`**Run reference scan**<br/>Any one condition suffices`"]
  SKIP["`**Skip scheduled scan**<br/>No condition holds`"]
  CHANGED -.->|Yes| SCAN
  CHANGED -.->|No| HOOK
  HOOK -.->|Yes| SCAN
  HOOK -.->|No| AGE
  AGE -.->|Yes| SCAN
  AGE -.->|No| SKIP
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class CHANGED,HOOK,AGE decision
  class SCAN outcome
  class SKIP muted
  class CHANGED,HOOK,AGE,SCAN,SKIP proposed
```

## rollout

```yaml
anchor: |-
  Then the crontab skill's workflow:
question: |-
  When can the cron swap happen, and what if application is pending or rollback is needed?
illustrates: |-
  The proposed two-phase rollout keeps the cron swap behind the shipped binary and Mac help check, reports pending application honestly, and preserves rollback through commit 2.
caption: "Verify bob tick --help on the Mac before swapping cron; report sleep as pending, and roll back only the schedule commit."
review: "688.914x1092 px, fit 81.8%; question, source, and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Proposed: when is the Mac cron swap ready?"
accTitle: "Gated Mac rollout and rollback"
accDescr: "Cadence configuration can land immediately. Replace the four jobs only after the release ships and bob tick help works on the Mac. Validate and deploy with cronctl, reporting in_sync or pending when the Mac sleeps. Rollback reverts commit 2 and re-applies."
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 18
    wrappingWidth: 260
---
flowchart TD
  CONFIG["`**Commit 1: cadence config**<br/>Safe before the binary ships`"]
  READY{{"`**Release and Mac help ready?**`"}}
  HOLD["`**Keep existing cron jobs**<br/>Binary verification still required`"]
  SWAP["`**Commit 2: cron swap**<br/>Four jobs become one`"]
  APPLY["`**Deploy schedule**<br/>check → diff → push → apply → status`"]
  ACTIVE["`**in_sync**<br/>Mac schedule verified`"]
  PENDING["`**pending**<br/>Mac asleep; not applied`"]
  REVERT["`**Rollback**<br/>Revert commit 2; re-apply`"]
  CONFIG -.->|Before the cron swap| READY
  READY -.->|No| HOLD
  READY -.->|Yes| SWAP
  SWAP -.->|cronctl workflow| APPLY
  APPLY -.->|status reports in_sync| ACTIVE
  APPLY -.->|Mac asleep| PENDING
  ACTIVE -.->|If rolling back| REVERT
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class CONFIG,SWAP,APPLY focus
  class READY,HOLD,PENDING decision
  class ACTIVE,REVERT outcome
  class CONFIG,READY,HOLD,SWAP,APPLY,ACTIVE,PENDING,REVERT proposed
```

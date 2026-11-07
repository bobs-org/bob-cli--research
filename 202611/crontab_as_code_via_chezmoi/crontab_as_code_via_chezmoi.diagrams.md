# Diagram proposals: Crontabs as code through chezmoi, with first-class agent access

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/crontab_as_code_via_chezmoi/crontab_as_code_via_chezmoi__final.md
producer: research.5w.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; broken-input negative control passed"
```

## watchdog-survival

```yaml
anchor: |-
  whole-table replacement deletes the line, nothing ever runs the watchdog again, so it
question: |-
  Why must the watchdog line survive an update?
illustrates: |-
  The watchdog adds its line only on its one-time install action, so whole-table replacement stops future watchdog runs and self-reinstallation, while the proposed marked block preserves that line.
caption: Whole-table replacement stops the watchdog that cannot reinstall itself; the proposed marked block preserves its cron line.
review: "551.625x1012 px, fit 88.2%; question, source trace, labels, arrows and visual checks passed; 0 revisions"
```

```mermaid
---
title: "Why must the watchdog line survive?"
accTitle: "A one-time watchdog installer cannot repair deletion"
accDescr: "The watchdog installs its cron line once. Whole-table replacement deletes the line and stops future watchdog runs. The proposed marked block preserves the line outside its boundary."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  INSTALL["`**One-time install**<br/>Adds the watchdog line`"]
  LINE["`**Watchdog cron line**<br/>Schedules future watchdog runs`"]
  POLICY{{"`**How is crontab updated?**`"}}
  LOST["`**Watchdog line deleted**<br/>Whole table replaced`"]
  STOPPED["`**Future watchdog runs stop**<br/>Cannot add its line back`"]
  KEPT["`**Watchdog line preserved**<br/>Outside the proposed block`"]
  RUNS["`**Future watchdog runs**<br/>Remain scheduled`"]
  INSTALL -->|adds once| LINE
  LINE -->|update policy determines survival| POLICY
  POLICY -->|whole-table replacement| LOST
  LOST -->|no remaining trigger| STOPPED
  POLICY -.->|proposed marked block| KEPT
  KEPT -.->|trigger preserved| RUNS
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class INSTALL,LINE,POLICY focus
  class LOST,STOPPED risk
  class KEPT,RUNS outcome
  class KEPT,RUNS proposed
```

## sync-triggers

```yaml
anchor: |-
  The hook then re-runs exactly when *this machine's* block or the reconciler changes.
question: |-
  When does a full update or targeted remote apply actually run sync?
illustrates: |-
  The run_onchange_after_ hook responds to local block or reconciler changes and retries failures, while remote targeted apply explicitly calls the same cronctl sync.
caption: Full updates conditionally run the after-hook; remote targeted applies call sync explicitly. Either path uses the same reconciler.
review: "675.26x764 px, fit 96.7%; question, source trace, labels, arrows and visual checks passed; converging arrows mean either path; 0 revisions"
```

```mermaid
---
title: "Proposed: when does crontab sync run?"
accTitle: "Two apply paths share one explicit reconciler"
accDescr: "A full chezmoi update runs its after-hook when the local block or reconciler changes, or retries a failed hook. Remote targeted apply runs no hooks and must call cronctl sync explicitly. Either path can invoke the same reconciler."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  LOCAL["`**Full local update**<br/>chezmoi update -a`"]
  REMOTE["`**Remote apply**<br/>cronctl apply`"]
  FILES["`**Write target files**<br/>Before the after-hook`"]
  TARGET["`**Targeted cron apply**<br/>Does not run hooks`"]
  DUE{{"`**After-hook due?**`"}}
  SKIP["`**No sync**<br/>Unchanged, previously successful hook`"]
  SYNC["`**cronctl sync**<br/>Reconcile this machine's block`"]
  LOCAL -.->|proposed full apply| FILES
  FILES -.->|check hook state| DUE
  DUE -.->|local block or reconciler changed,<br/>or previous hook failed| SYNC
  DUE -.->|neither condition| SKIP
  REMOTE -.->|proposed remote path| TARGET
  TARGET -.->|explicit sync call| SYNC
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class LOCAL,REMOTE,FILES,TARGET focus
  class DUE,SKIP decision
  class SYNC outcome
  class LOCAL,REMOTE,FILES,TARGET,DUE,SKIP,SYNC proposed
```

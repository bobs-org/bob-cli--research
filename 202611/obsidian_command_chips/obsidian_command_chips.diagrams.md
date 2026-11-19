# Diagram proposals: Command chips: one-gesture bob runs from Obsidian notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/obsidian_command_chips/obsidian_command_chips__final.md
producer: research.5k.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 2 of 2 Mermaid diagrams"
```

## activation-integrity

```yaml
anchor: |-
  activation the source is re-resolved and compared with what the widget represents; a
question: |-
  What prevents stale or invalid chip text from starting a run?
illustrates: |-
  At activation, stale widgets refresh and require a fresh gesture, whole-chip validation refuses invalid steps before step 1, and accepted runs keep an immutable argv sequence.
caption: "Stale widgets require a fresh gesture; invalid chips refuse before step 1; accepted command arguments stay fixed while Command Mode applies execution policy."
review: "659.1x938 px, fit 95.2%; question, labels, arrowheads, reading order, source trace and visual checks passed; 1 visual revision; no parse fixes"
```

```mermaid
---
title: "Proposed: can a command chip run?"
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 220
---
flowchart TD
  INPUT["`**Run gesture**<br/>Recheck source text`"]
  MATCH{{"`**Matches displayed chip?**`"}}
  STALE["`**Refresh widget**<br/>Require a fresh gesture`"]
  VALID{{"`**Every step valid?**`"}}
  REFUSE["`**Refuse before step 1**<br/>Show bob's reason`"]
  SNAP["`**Frozen commands**<br/>Note rewrites cannot change them`"]
  ENGINE["`**Command Mode**<br/>Apply execution policy`"]
  INPUT -.->|Compare| MATCH
  MATCH -.->|No| STALE
  MATCH -.->|Yes| VALID
  VALID -.->|No| REFUSE
  VALID -.->|Yes| SNAP
  SNAP -.->|Dispatch| ENGINE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class INPUT,SNAP,ENGINE focus
  class MATCH,VALID decision
  class STALE,REFUSE risk
  class INPUT,MATCH,STALE,VALID,REFUSE,SNAP,ENGINE proposed
```

## sequence-recovery

```yaml
anchor: |-
  Partial success is visible and honest: completed steps stay committed; Resume and
question: |-
  How does a command-chip sequence proceed or recover after a step outcome?
illustrates: |-
  Command Mode sequences continue on needs-attention, halt on failed, unknown or stopped, and keep completed steps committed while Resume and Rerun remain distinct explicit choices.
caption: "Failed, unknown, or stopped steps halt; completed work remains, and Resume or Rerun requires an explicit choice even after reload."
review: "676.1x764 px, fit 96.5%; question, labels, arrowheads, reading order, source trace and visual checks passed; 1 visual revision; no parse fixes"
```

```mermaid
---
title: "Proposed: how does a bob sequence recover?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 220
---
flowchart TD
  RESULT{{"`**Step k outcome?**`"}}
  CONTINUE["`**Continue the sequence**<br/>Needs-attention also continues`"]
  HALT["`**Halt the sequence**<br/>Completed steps stay committed`"]
  SUMMARY["`**Summary card**<br/>No automatic retry, even after reload`"]
  RESUME["`**Resume from step k**<br/>Explicit recovery choice`"]
  RERUN["`**Rerun**<br/>Explicit recovery choice`"]
  RESULT -.->|"Success or<br/>needs-attention"| CONTINUE
  RESULT -.->|"Failed, unknown<br/>or stopped"| HALT
  HALT -.->|Show| SUMMARY
  SUMMARY -.->|"Choose Resume"| RESUME
  SUMMARY -.->|"Choose Rerun"| RERUN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class CONTINUE,SUMMARY,RESUME,RERUN focus
  class RESULT decision
  class HALT risk
  class RESULT,CONTINUE,HALT,SUMMARY,RESUME,RERUN proposed
```


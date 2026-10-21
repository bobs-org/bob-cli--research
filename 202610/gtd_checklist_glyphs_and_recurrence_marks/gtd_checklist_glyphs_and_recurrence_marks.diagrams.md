# Diagram proposals: PRE/POST checklist glyphs and compact `repeat` marks

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/gtd_checklist_glyphs_and_recurrence_marks/gtd_checklist_glyphs_and_recurrence_marks__final.md
producer: research.28.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer --no-sandbox rendered 1 of 1 Mermaid diagrams"
```

## recurrence-display-confidence

```yaml
anchor: |-
  the charset check is a necessary condition for a valid rule, not a sufficient one.
question: |-
  Does a recurrence mark prove that Tasks can parse the rule?
illustrates: |-
  The occurrence and canonical-form gates, Tasks charset check, and checklist guard retain repair pills, while the label grammar can produce verbatim marks that Tasks rejects.
caption: Outside code, display checks and the morning checklist guard preserve repair pills; even a readable mark can still fail Tasks parsing.
review: "636.588x760 px, fit 100%; question, source-trace and visual checks passed; 0 revisions; batch rendered 1 of 1; malformed probe rejected"
```

```mermaid
---
title: "Proposed recurrence marks: what do they guarantee?"
accTitle: "Recurrence presentation checks do not prove Tasks validity"
accDescr: "For repeat fields outside code, failed display checks or a checklist without when done retain a repair pill. Eligible rules get a known cadence label or a verbatim mark, which may still fail Tasks parsing. Arrows describe presentation choices, not execution order."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 16
    wrappingWidth: 220
---
flowchart TD
  FORM{{"`**Display checks pass?**`"}}
  GUARD{{"`**Checklist lacks when done?**`"}}
  KNOWN{{"`**Known label pattern?**`"}}
  PILL["`**Repair pill**<br/>Raw field stays visible`"]
  LABEL["`**Cadence mark**<br/>daily, Mondays, monthly`"]
  RAW["`**Verbatim mark**<br/>May fail Tasks parsing`"]
  FORM -.->|No| PILL
  FORM -.->|Yes| GUARD
  GUARD -.->|Yes| PILL
  GUARD -.->|No| KNOWN
  KNOWN -.->|Yes| LABEL
  KNOWN -.->|No| RAW
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class FORM,GUARD,KNOWN decision
  class LABEL focus
  class PILL,RAW risk
  class FORM,GUARD,KNOWN,PILL,LABEL,RAW proposed
```

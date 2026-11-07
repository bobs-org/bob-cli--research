# Diagram proposals: `+N` later offsets in Pomodoro start timing

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/start_timing_later_offset/start_timing_later_offset__final.md
producer: research.5x.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## later-offset-compatibility

```yaml
anchor: |-
  A separate `later_units` keeps every existing reader correct: an older reader
question: |-
  How does later_units prevent older readers from reversing the start offset?
illustrates: |-
  A separate later_units keeps offset_units meaning earlier, while bob's resolved start/end stays authoritative for Mac Capture.
caption: "The additive later_units preserves earlier units; older readers miss the new offset while Mac Capture displays Bob's resolved span."
review: "836.094x565 px, fit 78.1%; question, visual, and source checks passed; 0 revisions; independent branches show interpretation and display"
```

```mermaid
---
title: "How does later_units avoid reversing the offset?"
accTitle: "Compatibility of later-start JSON fields"
accDescr: "Reusing offset_units would make an older reader interpret a later start as earlier. The proposed later_units field leaves the old field unchanged. Older readers do not know about the new offset, while Mac Capture displays Bob's authoritative resolved start and end."
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TB
  subgraph REUSE["Rejected: reuse the earlier field"]
    BAD["`**Later start**<br/>offset_units: 3`"]
    WRONG["`**Older reader**<br/>15 minutes earlier`"]
    BAD -->|"interprets as"| WRONG
  end
  subgraph ADD["Proposed: add a later field"]
    GOOD["`**Later start**<br/>offset_units: 0<br/>later_units: 3`"]
    UNKNOWN["`**Older reader**<br/>Later offset unknown`"]
    TIMES["`**Bob resolves**<br/>Authoritative start / end`"]
    MAC["`**Mac Capture**<br/>Renders resolved span`"]
    GOOD -.->|"new field unknown"| UNKNOWN
    GOOD -.->|"Bob computes times"| TIMES
    TIMES -->|"app displays"| MAC
  end
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class BAD,WRONG risk
  class UNKNOWN muted
  class GOOD,TIMES,MAC outcome
  class GOOD proposed
  style REUSE fill:none,stroke:#C0392B
  style ADD fill:none,stroke:#2E7D4F
```

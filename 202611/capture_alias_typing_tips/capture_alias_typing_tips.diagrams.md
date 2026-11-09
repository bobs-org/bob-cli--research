# Diagram proposals: Capture alias typing tips: teach the shortcut where the eye already is

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/capture_alias_typing_tips/capture_alias_typing_tips__final.md
producer: research.3y.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## candidate-alias-proof

```yaml
anchor: |-
  **The candidate list is not the truth.** It only proposes substitutions.
question: |-
  How does bob prove one candidate alias key would recreate the typed edit?
illustrates: |-
  For one candidate key after the lexical checks, the whole rewrite pipeline must produce an allowed alias and exactly recreate the draft and caret before bob collects that key under its lesson ID.
caption: After lexical checks, a candidate key qualifies only when the full rewrite produces an allowed alias and recreates the original draft and caret.
review: "494.136x1088 px, fit 82.1%; reader question, source trace, labels, branches, arrowheads, and visual checks passed; 1 revision"
```

```mermaid
---
title: "Proposed: what makes an alias tip true?"
accTitle: "Proposed proof for one candidate alias key"
accDescr: "After lexical checks, bob substitutes a candidate key and runs the entire rewrite pipeline. It keeps that candidate only when the alias rule fired, the draft and caret exactly match, and the lesson is not excluded. Any failed check rejects the candidate."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 12
    wrappingWidth: 260
---
flowchart TD
  C["`**Try candidate key**<br/>Replace the typed sigil`"]
  R["`**Run whole rewrite**<br/>Honor rule precedence`"]
  A{{"`**Alias rule fired?**`"}}
  E{{"`**Exact draft and caret?**`"}}
  L{{"`**Lesson allowed?**`"}}
  K["`**Keep candidate key**<br/>Group by lesson ID`"]
  X["`**Reject candidate key**<br/>Any failed check`"]
  C -.->|rewrite| R
  R -.->|check result| A
  A -.->|Yes| E
  A -.->|No| X
  E -.->|Yes| L
  E -.->|No| X
  L -.->|Yes| K
  L -.->|No| X
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef muted fill:#F3F4F6,stroke:#6B7280,stroke-width:1.5px,color:#1F2937
  classDef proposed stroke-dasharray:5 3
  class C,R,K focus
  class A,E,L decision
  class X muted
  class C,R,A,E,L,K,X proposed
```

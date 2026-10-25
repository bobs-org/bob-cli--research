# Diagram proposals: `bob ref create` recapture modes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202610/ref_create_recapture_modes/ref_create_recapture_modes__final.md
producer: research.2g.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## reading-family

```yaml
anchor: |-
  After that, the index reads it rather than re-deriving
question: |-
  How does Bob distinguish intentional rereads from unrelated duplicates?
illustrates: |-
  References sharing a source identity key form a reading family through explicit `earlier:` links, so the family avoids `duplicate_identity` warnings and its newest reading becomes primary.
caption: "Explicit earlier links distinguish intentional rereads from unrelated duplicates; the newest family reading becomes primary."
review: "644.5x788 px, fit 100%; question, source trace and PNG visual checks passed; 0 visual revisions; PNG succeeded on one permitted connection-failure retry"
```

```mermaid
---
title: "Proposed reading families: when is a duplicate intentional?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 14
    wrappingWidth: 200
---
flowchart TD
  MATCH["`**Same source key**<br/>References share source identity`"]
  Q{{"`**Linked through earlier?**`"}}
  FAMILY["`**Reading family**<br/>Intentional duplicate source`"]
  WARN["`**Unrelated duplicates**<br/>doctor still warns`"]
  ACCEPT["`**doctor accepts family**<br/>No duplicate_identity warning`"]
  PRIMARY["`**find and show**<br/>Newest primary; others also`"]
  MATCH -.->|check explicit lineage| Q
  Q -.->|Yes| FAMILY
  Q -.->|No| WARN
  FAMILY -.->|duplicate check| ACCEPT
  FAMILY -.->|lookup| PRIMARY
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class MATCH focus
  class Q,WARN decision
  class FAMILY,ACCEPT,PRIMARY outcome
  class MATCH,Q,FAMILY,WARN,ACCEPT,PRIMARY proposed
```

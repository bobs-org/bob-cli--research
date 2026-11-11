# Diagram proposals: Your first bank acknowledgment (Thu Nov 12) and an end-to-end test of `bob-cli-kd`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/bank_first_ack_and_kd_e2e_guide/bank_first_ack_and_kd_e2e_guide__final.md
producer: research.49.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; pinned CLI with Puppeteer --no-sandbox"
```

## sandbox-isolation

```yaml
anchor: |-
  It's a synthetic vault with its own bare remote and
question: |-
  How are bank write tests isolated from the real vault?
illustrates: |-
  The Appendix sandbox has its own bare remote, sync lock, and state, so write tests
  use separate destinations instead of touching the real vault or blocking real sync.
caption: A dedicated terminal loads sandbox paths so bank write tests use their own vault, remote, sync lock, and state.
review: "481.875x723 px, fit 100.0%; reader question, labels, arrows, source tracing and unique anchor checks passed; 1 revision across 2 visual looks"
```

```mermaid
---
title: "Where do sandbox bank writes and sync go?"
accTitle: "Isolated bank test paths"
accDescr: "A dedicated terminal sources the sandbox environment. BOB_DIR selects the synthetic vault, separate sync paths select its lock and state, and the vault has its own bare remote."
config:
  flowchart:
    rankSpacing: 28
    nodeSpacing: 24
    wrappingWidth: 220
---
flowchart TB
  ENV["`**Sandbox environment**<br/>Load its environment`"]
  CMD["`**Bank write tests**<br/>Dedicated terminal`"]
  subgraph SB["Synthetic sandbox"]
    VAULT["`**Test vault**<br/>BOB_DIR`"]
    SYNC["`**Sync coordination**<br/>Own lock and state`"]
    REMOTE["`**Git remote**<br/>Own bare repository`"]
  end
  ENV -->|configures destinations| CMD
  CMD -->|BOB_DIR selects| VAULT
  CMD -->|sync paths select| SYNC
  VAULT -->|origin selects| REMOTE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  class ENV,CMD focus
  class VAULT,SYNC,REMOTE outcome
  style SB fill:none,stroke:#2E7D4F
```

# Diagram proposals: Stop SASE agents blocking on `bob plugins sync`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/plugin_sync_unblocking/plugin_sync_unblocking__final.md
producer: research.53.image
check: "mmdc 12.0.0 with --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## mutual-deploy-deadlock

```yaml
anchor: |-
  each held its own commit until its sync passed
question: |-
  Why did two plugin agents deadlock on November 16?
illustrates: |-
  Each workspace held its own commit until its sync passed, while each uncommitted deployed build blocked the other's sync.
caption: "Each agent held its commit until sync passed; each protected build blocked the other agent. Arrows show blocking dependencies."
review: "509.141x872 px, fit 100.0%; question and visual checks passed; all entities and edges traced to sections 1.2 and 2.1; 0 revisions"
```

```mermaid
---
title: "Why did two plugin agents deadlock on November 16?"
accTitle: "Circular wait between two plugin workspaces"
accDescr: "Each workspace held its commit until sync passed, while its protected uncommitted deployment blocked the other workspace's sync. Arrows show blocking dependencies."
config:
  flowchart:
    rankSpacing: 24
    nodeSpacing: 24
    wrappingWidth: 240
---
flowchart TB
  subgraph W10["Workspace 10: bob-cli-mf.6"]
    direction TB
    A["`**Sync refused**<br/>Workspace 14 stamp`"]
    AC["`**Commit held**<br/>Until sync passes`"]
    A -->|"refusal blocks commit"| AC
  end
  subgraph W14["Workspace 14: ei"]
    direction TB
    B["`**Sync refused**<br/>Workspace 10 stamp`"]
    BC["`**Commit held**<br/>Until sync passes`"]
    B -->|"refusal blocks commit"| BC
  end
  AC -->|"protected build blocks sync"| B
  BC -->|"protected build blocks sync"| A
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  class A,B risk
  class AC,BC focus
  style W10 fill:none,stroke:#3B78C2
  style W14 fill:none,stroke:#3B78C2
```

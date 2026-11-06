# Diagram proposals: `just install-all`: a wait worth sitting through

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/install_all_wait_and_whats_new/install_all_wait_and_whats_new__final.md
producer: research.3j.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams; Puppeteer --no-sandbox; malformed-diagram control exited nonzero"
```

## retry-watermark

```yaml
anchor: |-
  From the `installed.json` watermark to the post-pull HEAD;
question: |-
  Why do retries still show changes that were not installed?
illustrates: |-
  For a valid stored watermark, installed.json advances only after a successful install or drift-free plugin sync, so a failed build leaves its changes visible on the next retry.
caption: "With a valid baseline, failed installs preserve the digest on retry; successful installs or drift-free plugin syncs advance it."
review: "524.531x892 px, fit 100.0%; question and visual checks passed; all nodes and edges traced to source; 0 visual revisions"
```

```mermaid
---
title: "Proposed: why do retries still show uninstalled changes?"
config:
  flowchart:
    rankSpacing: 16
    nodeSpacing: 20
    wrappingWidth: 220
---
flowchart TD
  BASE["`**Baseline A**<br/>Last successful install`"]
  HEAD["`**New HEAD B**<br/>After the pull`"]
  DIGEST["`**What's new**<br/>Commits in A..B`"]
  RESULT{{"`**Install succeeds?**`"}}
  SAVE["`**Save baseline B**<br/>Next digest starts here`"]
  KEEP["`**Keep baseline A**<br/>Changes remain uninstalled`"]
  BASE -.->|"pull reaches B"| HEAD
  HEAD -.->|"compare with baseline A"| DIGEST
  DIGEST -.->|"run installation"| RESULT
  RESULT -.->|"yes"| SAVE
  RESULT -.->|"no"| KEEP
  KEEP -.->|"next user retry;<br/>HEAD still B"| DIGEST
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class BASE,HEAD,DIGEST focus
  class RESULT,KEEP decision
  class SAVE outcome
  class BASE,HEAD,DIGEST,RESULT,SAVE,KEEP proposed
```

## quiet-output-routing

```yaml
anchor: |-
  Lines that are recognizably Cargo or SwiftPM status
question: |-
  Where do output, notices, and errors go during a quiet build?
illustrates: |-
  The helper saves full output to a log while hiding only known compiler chatter, passing every other line above the live line, and showing an excerpt with the log path on failure.
caption: "All output reaches the log; only known chatter is hidden, every other line stays visible, and failures add an excerpt and log path."
review: "815.788x564 px, fit 80.0%; question and visual checks passed; all nodes and edges traced to source; 0 visual revisions"
```

```mermaid
---
title: "Proposed: where does quiet-build output go?"
config:
  flowchart:
    rankSpacing: 18
    nodeSpacing: 18
    wrappingWidth: 200
---
flowchart TD
  HELPER["`**Python helper**<br/>Drains child output continuously`"]
  LOG["`**Full log**<br/>All output preserved`"]
  KIND{{"`**Known compiler chatter?**`"}}
  LIVE["`**Live status line**<br/>Chatter stays in log`"]
  NOTICE["`**Every other line**<br/>Print above live line`"]
  ERROR["`**Failure excerpt**<br/>Show error and log path`"]
  HELPER -.->|"save all output"| LOG
  HELPER -.->|"also classify each line"| KIND
  HELPER -.->|"on build failure"| ERROR
  KIND -.->|"yes"| LIVE
  KIND -.->|"no: pass through"| NOTICE
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef outcome fill:#E7F5EC,stroke:#2E7D4F,stroke-width:1.5px,color:#123D24
  classDef proposed stroke-dasharray:5 3
  class HELPER focus
  class KIND decision
  class LOG,LIVE,NOTICE,ERROR outcome
  class HELPER,LOG,KIND,LIVE,NOTICE,ERROR proposed
```


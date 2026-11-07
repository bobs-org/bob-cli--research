# Diagram proposals: Watching Gmail threads from Bob

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gmail_sync_reply_watch/gmail_sync_reply_watch__final.md
producer: research.3m.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams"
```

## sync-concurrent-edits

```yaml
anchor: |-
  re-read every touched file and confirm
question: |-
  How does sync protect a task edited or closed during a Gmail fetch?
illustrates: |-
  Sync fetches outside the vault lock, then re-reads touched files under the vault maintenance lock so a task closed during the run wins over a fetched reply.
caption: "Sync rechecks task state under lock: closure wins, conflicts replan or defer, and journal events follow durable writes."
review: "695x1065 px, fit 83.8%; question, source-trace and visual checks passed; 0 revisions; batch rendered 1 of 1; deliberately broken chart exited nonzero"
```

```mermaid
---
title: "Proposed sync protects concurrent task edits"
config:
  sequence:
    actorMargin: 25
    diagramMarginX: 10
    messageMargin: 28
    noteMargin: 8
---
sequenceDiagram
  autonumber
  participant G as Gmail
  participant S as Sync
  participant V as Vault
  Note over S,V: Fetch outside the vault lock<br/>You may edit or close the task
  S->>G: Read new or watched<br/>thread metadata
  G-->>S: Message metadata
  S->>S: Plan task changes<br/>and note refresh
  critical Apply under the vault maintenance lock
    S->>V: Re-read every touched file
    V-->>S: Current task state
    alt Task was closed
      Note over S,V: Closure wins over the fetched reply
    else Task line changed
      S->>S: Replan or defer the conflict
    else Still open and unchanged
      S->>V: Write task and note changes
      S->>V: Append body-free journal events<br/>after durable writes
    end
  end
  Note over S,V: Crash before journal update:<br/>replay sets the same tag and date
```

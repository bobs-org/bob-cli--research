# Diagram proposals: Gmail archive on task close: consolidated design and recommendation

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/gmail_archive_on_task_close/gmail_archive_on_task_close__final.md
producer: research.4d.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; retained Puppeteer --no-sandbox; negative parse check passed"
```

## reply-race-boundary

```yaml
anchor: |-
  preflight and the write simply isn't in the ID list and keeps the thread in the Inbox
question: |-
  What happens when a reply arrives just before versus just after preflight?
illustrates: |-
  An unsaved Inbox message at preflight keeps the whole thread in place, while a reply between preflight and the write stays outside the frozen ID list and remains in the Inbox.
caption: "Unsaved mail before preflight holds the thread; a reply after preflight stays in the Inbox because the write uses frozen saved IDs."
review: "643.5×866 px, fit 100.0%; question, source trace and visual checks passed; 0 visual revisions; 1 parse correction"
```

```mermaid
---
title: "Proposed: what if a reply races with archiving?"
accTitle: "Reply timing and frozen message IDs"
accDescr: "If unsaved reply C is present at preflight, the whole thread stays in the inbox. If C arrives after preflight, only frozen saved IDs A and B are archived, and C remains in the inbox."
config:
  sequence:
    actorMargin: 18
    boxMargin: 8
    messageMargin: 18
    noteMargin: 8
    width: 90
    height: 40
---
sequenceDiagram
  autonumber
  participant S as Sender
  participant G as Gmail
  participant B as Bob sync
  Note over S,B: Proposed behavior: A and B saved, tasks closed.<br/>Other archive checks assumed to pass.
  alt C arrives before preflight
    S->>G: New reply C
    B->>G: Read live metadata
    G-->>B: Inbox: saved A, B<br/>and unsaved C
    Note over G,B: Hold whole thread.<br/>A, B and C stay in Inbox.
  else C arrives after preflight
    B->>G: Read live metadata
    G-->>B: Inbox: saved A, B only
    Note over B: Freeze IDs: A, B
    S->>G: New reply C
    B-->>G: Proposed: batchModify A, B<br/>remove INBOX, add bob/closed
    Note over G,B: A and B archived.<br/>C stays in Inbox.
  end
```

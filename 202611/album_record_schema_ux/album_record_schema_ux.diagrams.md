# Diagram proposals: The album `record` property: hide the row, read it in the header, edit it through bob

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/album_record_schema_ux/album_record_schema_ux__final.md
producer: research.4b.image
check: "mmdc 12.0.0 with Puppeteer --no-sandbox and the PDF-mirroring config rendered 1 of 1 Mermaid diagrams; broken-input check exited nonzero"
```

## reversible-schema-edit

```yaml
anchor: |-
  Safe ops commit on Enter, one gesture = one scoped commit, with an Undo toast backed
question: |-
  How does a schema edit become a preview, a guarded commit, and a reversible change?
illustrates: |-
  For schema edits requiring an index rebuild, the Schema Card shows dry-run consequences before Enter, bob guards the scoped commit, and inverse ops keep Undo on the normal edit path.
caption: "When an edit needs an index rebuild, bob guards the commit and Undo uses the same edit path."
review: "691x974 px, fit 91.7%; question, source trace, labels, arrowheads, reading direction, and visual checks passed; 1 visual revision, 1 syntax fix; 2 look rounds"
```

```mermaid
---
title: "Proposed: preview, apply, and undo"
config:
  sequence:
    actorMargin: 22
    width: 120
    diagramMarginX: 8
    diagramMarginY: 8
    messageMargin: 18
    noteMargin: 8
    boxMargin: 8
    mirrorActors: false
---
sequenceDiagram
  autonumber
  participant CARD as Schema Card<br/>(plugin)
  participant BOB as bob albums<br/>update
  participant FILES as Album +<br/>records index
  CARD-->>BOB: Dry-run JSON operations
  BOB-->>CARD: Diff, counts, consequence
  Note over CARD,BOB: Preview or cancel: no vault writes
  opt User confirms safe edit with Enter
    CARD-->>BOB: Apply ops + expect fingerprint
    alt Stale fingerprint
      BOB-->>CARD: Refuse: stale-note error
    else Index cannot be safely rebuilt
      BOB-->>CARD: Refuse: keep draft + reason
    else Guards pass for a changed edit
      Note over BOB,FILES: Rust validates post-image<br/>Commit holds maintenance lock
      BOB-->>FILES: One scoped commit:<br/>album + rebuilt index
      BOB-->>CARD: Saved + inverse operations
      Note over CARD: Stay open<br/>repaint from<br/>refreshed report
      opt User presses u (Undo)
        CARD-->>BOB: Undo: inverse ops as normal edit
        Note over CARD,BOB: Same edit path<br/>Linear history
      end
    end
  end
```

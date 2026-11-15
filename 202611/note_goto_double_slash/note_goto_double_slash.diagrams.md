# Diagram proposals: `//` in Bob Mac Capture: Go To Notes

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/note_goto_double_slash/note_goto_double_slash__final.md
producer: research.4t.image
check: "mmdc 12.0.0 with the PDF-mirroring config and Puppeteer no-sandbox rendered 1 of 1 Mermaid diagrams; the deliberately broken diagram returned nonzero"
```

## note-goto-grammar-handoff

```yaml
anchor: |-
  router (focus is in the filter field); fast typing and paste go through the grammar.
question: |-
  How do typing and paste keep bob in charge of syntax?
illustrates: |-
  Normal-cadence typing and fast typing or paste converge on the draft, while bob advertises the continuation key and reports the note_goto need that selects Notes.
caption: Normal typing and paste converge on the draft; bob reports note_goto before the Mac app opens Notes.
review: "429x813 px, fit 100%; question, label, arrowhead, reading-order, source, and unique-anchor checks passed; 2 revisions, replacing an over-wide ownership flowchart and shortening the clipped sequence title"
```

Either entry branch can be used. Dashed arrows show the proposed information flow.

```mermaid
---
title: "Proposed: bob owns //"
config:
  sequence:
    actorMargin: 40
    width: 180
    messageMargin: 22
    diagramMarginX: 10
    diagramMarginY: 10
    wrap: true
---
sequenceDiagram
  autonumber
  participant APP as Mac app
  participant BOB as bob-cli
  alt Normal typing: empty Tasks filter
    BOB-->>APP: Bare / advertises / continuation
    APP-->>APP: Real / extends<br/>draft to //
  else Fast typing or paste
    APP-->>APP: Draft becomes //query
  end
  APP-->>BOB: Parse the whole draft
  BOB-->>APP: Report note_goto need
  APP-->>APP: Show Notes from bob's need
```

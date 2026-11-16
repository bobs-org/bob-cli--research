# Diagram proposals: Video embeds in task captures, viewed with `Z`

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says.

```yaml
source: research:202611/task_video_capture_z_viewer/task_video_capture_z_viewer__final.md
producer: research.63.image
check: "mmdc 12.0.0 with the PDF-mirroring config rendered 2 of 2 Mermaid diagrams"
```

## source-integrity

```yaml
anchor: |-
  commit streams source → temp file while re-hashing and aborts if
question: |-
  What prevents a changed source from being saved after planning?
illustrates: |-
  The proposed save compares the planned hash with the streamed-copy hash, requiring both to match before finishing the existing copy and aborting when the source changed.
caption: "The proposed save requires both hashes to match; changed source bytes abort the save before the existing copy finishes."
review: "467.16x716 px, fit 100.0%; question, source tracing and visual checks passed; 1 revision, 2 visual look rounds."
```

```mermaid
---
title: "Proposed: verify source bytes before saving"
accTitle: "Planned and copied bytes must have matching hashes"
accDescr: "Planning records a streamed hash. Saving streams the source into a temporary file and hashes it again. Both hashes must agree before the existing copy can finish."
config:
  flowchart:
    rankSpacing: 12
    nodeSpacing: 20
    wrappingWidth: 230
---
flowchart TD
  RECORD["`**Plan source**<br/>Descriptor + streamed SHA-256`"]
  COPY["`**Copy to temporary file**<br/>Stream bytes + fresh hash`"]
  MATCH{{"`**Both hashes match?**`"}}
  ABORT["`**Abort save**<br/>Source changed`"]
  FINISH["`**Finish existing copy**<br/>fsync + rename`"]
  RECORD -.->|source descriptor| COPY
  RECORD -.->|planned hash| MATCH
  COPY -.->|fresh hash| MATCH
  MATCH -.->|No| ABORT
  MATCH -.->|Yes| FINISH
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class RECORD,COPY,FINISH focus
  class MATCH decision
  class ABORT risk
  class RECORD,COPY,MATCH,ABORT proposed
```

## viewer-lifecycle

```yaml
anchor: |-
  pause, clear `src`, call `load()` to release the decoder, detach
question: |-
  How does the proposed viewer start playback, handle failure, and close?
illustrates: |-
  Either playing or paused video can fail into an in-place card, while closing or plugin unloading from any open state releases the decoder and restores editor state.
caption: "Proposed: errors stay visible (o opens the default app; y copies the path); closing releases the decoder and restores the editor."
review: "455.312x1063 px, fit 84.0%; question, source tracing and visual checks passed; 2 revisions, 2 visual look rounds; scope excludes native-fullscreen Esc."
```

```mermaid
---
title: "Proposed: the video viewer stays open on failure"
accTitle: "Video viewer lifecycle"
accDescr: "Audio or reduced motion starts paused; otherwise silent clips autoplay and loop. Space toggles playback. Failure keeps the modal open. Closing or unloading releases media and restores the editor."
config:
  flowchart:
    rankSpacing: 8
    nodeSpacing: 20
    wrappingWidth: 260
---
flowchart TD
  subgraph VIEWER["Proposed video viewer · open"]
    POLICY{{"`**Start paused?**`"}}
    PAUSED["`**Paused**<br/>Space to play`"]
    PLAYING["`**Playing**<br/>Silent autoplay loops`"]
    FAILURE["`**Failure card**<br/>Stay open; o / y available`"]
    POLICY -.->|"Audio or<br/>reduced motion"| PAUSED
    POLICY -.->|"Otherwise: silent clip"| PLAYING
    PAUSED <-.->|Space| PLAYING
    PAUSED -.->|"Media error"| FAILURE
    PLAYING -.->|"Media error"| FAILURE
  end
  CLEAN["`**Close and restore**<br/>Pause; clear src; load<br/>Detach listeners; restore editor`"]
  VIEWER -.->|"Close or plugin unload<br/>(any open state)"| CLEAN
  classDef focus fill:#E8F1FB,stroke:#3B78C2,stroke-width:1.5px,color:#0F2E52
  classDef decision fill:#FFF7E6,stroke:#C77C02,stroke-width:1.5px,color:#4A3000
  classDef risk fill:#FDECEC,stroke:#C0392B,stroke-width:1.5px,color:#5F1414
  classDef proposed stroke-dasharray:5 3
  class PAUSED,PLAYING,CLEAN focus
  class POLICY decision
  class FAILURE risk
  class POLICY,PAUSED,PLAYING,FAILURE,CLEAN proposed
  style VIEWER fill:none,stroke:#3B78C2
```

# Diagram proposals: Task relations: LINKS, LINKED FROM, and capture

Proposals for the swarm linker, not a report. Each diagram restates only what the source
report says. All three depict the recommended design, not implemented behaviour.

```yaml
source: research:202610/task_relation_links/task_relation_links__final.md
producer: research.53.image
check: "mmdc 12.0.0 rendered 3 of 3 Mermaid diagrams"
```

## missed-mirror-recovery

```yaml
anchor: |-
  A cross-note mirror write can fail after the authored edit succeeds
illustrates: |-
  A cross-note mirror write can fail after the authored edit succeeds, while chips render from the live index and reconcile preserves previous entries for an unreadable source.
caption: Proposed recovery preserves authored edges when a writable target's mirror update fails.
```

```mermaid
flowchart TD
  A["Authored LINKS edit"] -->|"mirror write fails"| B["Stale stored mirror"]
  A -->|"live index"| C["Live chips"]
  A -->|"next reconcile"| D["Reconcile projection"]
  D -->|"readable sources"| E["Canonical LINKED FROM"]
  D -->|"unreadable source"| F["Keep entries + warn"]
```

## capture-relation-card

```yaml
anchor: |-
  **⇧↩ opens the relation card,** which reuses the `TaskIDPromptCard` pattern
illustrates: |-
  In either picker direction, Shift+Enter opens the relation card, Escape returns to the picker, and typing `|` after an accepted token also opens the card.
caption: Proposed relation-card navigation supports direct acceptance, optional labels, pipe re-entry, and Escape.
```

```mermaid
flowchart TD
  P["Task picker"] -->|"Enter"| T["Accepted token"]
  P -->|"Shift+Enter"| L["Relation card"]
  T -->|"type pipe"| L
  L -->|"insert labelled token"| T
  L -->|"Escape"| P
```

## incoming-edit-ownership

```yaml
anchor: |-
  Toggling a row adds or removes *this* task on the
illustrates: |-
  The Linked-from stage adds or removes this task on the other task's LINKS line, leaving LINKED FROM as a generated projection.
caption: Proposed incoming edits change the selected source's LINKS; the target mirror follows.
```

```mermaid
flowchart LR
  T["Task Card at T"] -->|"Shift+L"| L["Choose source S"]
  L -->|"add/remove T"| S["Source S LINKS"]
  S -->|"projection"| M["T LINKED FROM"]
```

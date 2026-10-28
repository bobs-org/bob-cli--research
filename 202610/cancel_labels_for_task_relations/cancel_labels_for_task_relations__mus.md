# Relation auto-cancel: design research (`duplicate of` / `superseded by`)

Research date: 2026-10-28. Researcher: `mus`.
Question: should configured relation descriptions auto-cancel the source task,
starting with `duplicate of` and `superseded by` in the chezmoi repo, with a
clear user indication and daily-ledger cleanup like other cancels?

Short answer and recommendation are at the top. Evidence and the full design
follow.

## TL;DR and recommended solution

**Do not implement silent label-match auto-cancel as specified. Implement an
explicit, previewed "link + cancel" gesture instead, with the label list as
its default menu — not as a hidden trigger.**

Concretely, I recommend:

1. Add an opt-in config `relations.cancels_source_labels` (list of label
   keys, default empty) in `home/dot_config/bob/config.yml` (chezmoi). Ship
   it with `["duplicate of", "superseded by"]` in Bryan's chezmoi config, not
   as a bob-cli built-in default.
2. When the user picks a configured label in an **explicit relation gesture**
   (capture `~` / `~~`, Mac relation card, Obsidian Links stage), show a calm
   amber `will cancel S` indication **before** commit, and on accept do one
   atomic transaction: write the LINKS edge + mirror, cancel S with a Cancel
   Log entry naming the surviving task, then run the existing
   canceled-reference ledger cleanup for today.
3. Never trigger from background writes: hand edits, `bob relations rename`,
   `reconcile`, or relabels of an already-linked edge must not cancel. Only
   the gesture that creates the edge cancels, and only once, with full
   dry-run parity and one-undo semantics.
4. Keep the inertness contract for everything else. Amend
   [task-relations.md](../../../../docs/task-relations.md) narrowly: relations
   are inert *except* this one explicit, configured, previewed cancel.

Why this shape: the request as written breaks the strongest guarantee in the
relations contract (§2, §14: "Relations are history; nothing changes"), makes
a common label spelling silently destructive, and has a direction trap in `~~`
that would cancel the canonical task instead of the duplicate. The adjusted
design keeps the user's goal (one step to mark a duplicate) while staying
intuitive (explicit + previewed), reliable (atomic, idempotent, undoable),
and beautiful (one calm amber line, existing vocabulary, no new palette).

If Bryan insists on fully automatic cancel on any write carrying those labels,
gate it behind `relations.auto_cancel_mode: "prompt" | "auto"` defaulting to
`prompt`, and read the "fully automatic" variant section below as the fallback
— but I advise against shipping `auto`.

## Background: what exists today

### 1. Relations are deliberately inert

`docs/task-relations.md` is the contract every implementation cites (Rust
`src/native/task_relations/`, JS twins in navigation-hotkeys, ledger-tools,
cycler, block-id-prompt):

- A relation is a directed, optionally labelled, inert edge S → T, authored
  on S's `🪢 **LINKS:**` line and mirrored on T's generated
  `🪢 **LINKED FROM:**` line (§1).
- §2 "What relations never do" is absolute: a relation write, line, or
  gesture never blocks, promotes, consumes, stamps, or changes status, lane,
  schedule, priority, `[id::]`, or `[dependsOn::]`. The only task-line edit a
  relation writer may make is minting a `^block-id`.
- §8 table: "Closes, cancels, reopens — None." §14 lifecycle: "Close, cancel,
  reopen S or T. None. Relations are history; nothing changes."
- Guarantee LR18/LX13/LG13: adding, removing, or relabelling any relation
  leaves every status, lane, field, schedule, and Pomodoro section
  byte-identical apart from a minted id.

Any auto-cancel is therefore not an additive feature: it amends a
load-bearing guarantee and must update the doc, all four parsers' shared
vectors (LK/LW/LR/LX/LP/LD/LG/LC), and both Rust and JS twins together, or the
implementations will disagree.

Glossary (via `sase memory read glossary:task-relation`): a
**task relation** is distinct from a Pomodoro **task link** and from a
**task dependency link** (the managed `⛓️ **DEPENDS ON:**` line). Decisions
`task-deps-are-depends-on-links`, `task-lanes-are-sticky`,
`relation-label-hide-is-suggestions-only`, `relation-label-rename-rewrites-history`,
and `relation-label-prefs-live-in-per-host-journal` all assume labels are
non-destructive metadata.

### 2. How cancel works today

- Nav Task Card Cancel closes a task as Cancelled (`[-]`) with an optional
  reason kept in a first-child `❌ **CANCEL LOG**` child (see
  `docs/reference/plugins/bob-navigation-hotkeys.md` description column).
  The Cancel Log slot is first direct child (§4 slot order in both
  `docs/task-relations.md` and `docs/task-dependencies.md`).
- Capture `x` closes (completes), it does not cancel; cancel is a nav/cycler
  path. `src/native/task_complete/` owns the close engine; cancelled closes
  recover dependents only and never offer successors
  (`docs/task-dependencies.md` §§ on successors: cancelled close → recover
  only, never offer — SO28, and `plan.link_unblocked` only affects managed
  Done closes).
- Freshness never stamps a cancelled line; decay cancel goes through the
  cancel row, never silently (`docs/freshness.md`).
- `src/native/capture_task_toggle/task_update.rs` (`plan_task_link`,
  `set_task_line_status`) shows the status-toggle planner pattern to mirror:
  pure `&str` postimage planners, tested directly.

### 3. Daily-ledger cleanup for canceled tasks already exists — reuse it

`docs/task-status-hooks.md` ("Canceled Task References") is the authority:

- Every surviving block-link occurrence under an **open Pomodoro** in the
  selected daily note is checked against the Tasks status registry. When it
  resolves only to `CANCELLED` (including custom single-character symbols
  whose Tasks type is CANCELLED), its complete Markdown list-item subtree is
  removed — dedicated bullet goes with subtree, otherwise only the token
  (Ctrl+Shift+P Cancel row uses the deferral-prune token semantics).
- Struck, embedded, aliased, and Pomodoro-marked forms qualify; closed
  Pomodoros, other days' notes, top-level lines, and fenced examples are
  untouched. Ambiguous mixed duplicates warn and stay.
- After duplicate, canceled, blocked-consumption, completed-reference, and
  marker repairs, childless Pomodoro entries are removed with their full
  entry block.

So requirement 3 ("remove task links in the current daily file just like
other cancels") needs no new ledger algorithm — the relation-cancel path
should call into this exact cleanup (or run `bob task reconcile` right after)
rather than inventing a second remover.

### 4. Config and label machinery

- CLI reads one YAML file (`BOB_CONFIG_FILE`, else
  `$XDG_CONFIG_HOME/bob/config.yml`, else `~/.config/bob/config.yml`); see
  `docs/reference/configuration.md` and `src/native/config/relations.rs`.
  Today `relations:` holds exactly one key: `linked_from_lines: bool`
  (default `true`, invalid falls back to `true` with a warning).
- Bryan's live file is `home/dot_config/bob/config.yml` in the chezmoi repo
  (104 lines today: `timezone`, `properties`, `highlights`, `gkeep`,
  `freshness`, `plan` — no `relations:` block yet).
- Label identity is `relation_label_key` in `src/native/relation_labels/mod.rs`:
  writer normalization (trim, collapse whitespace, strip one trailing `:`)
  then Unicode `to_lowercase`. The catalog counts every accepted LINKS entry
  (open, closed, `done/`, dailies); hide is suggestions-only; `||` hides a
  label after commit; rename rewrites spans in one previewed commit
  (`docs/task-relations.md` §16 RV2–RV8, `tests/fixtures/relation_labels/vectors.json`).
- Capture execution stages LINKS + mirror in one batch
  (`src/native/capture/relations.rs`: `plan_relation_label_hides`,
  `plan_relation_writes`, `append_committed_relation_label_hides`).
  Completion contexts are `relation_to` / `relation_from`
  (`DependencyCandidate` shape + `already_linked`, `existing_label`,
  `also_prerequisite`, `disabled_reason`) and `relation_label` (catalog
  suggestions with `replacement` / `hide_replacement`, `hidden_count`).
  `schema_version` stays 1, additive only.
- Mac Capture is a thin client (`decisions:mac-capture-is-a-thin-client`):
  it never parses grammar or writes the vault; it renders what bob returns.
  Any "will cancel" indication must therefore come from bob's JSON, never
  from app-side label matching.

## Critique of the request as written

Is it a good idea? The goal is sound (deduping is real work; one step beats
two), but the mechanism as specified — any selection of a configured
description silently cancels — has four problems. I keep the goal and change
the mechanism; adjustments are marked **[ADJUSTMENT]**.

### C1. Silent destructiveness on a common spelling [ADJUSTMENT: preview + explicit accept]

`duplicate of` and `superseded by` are ordinary English a user can type while
exploring ("maybe this is a duplicate?"). Today typing them is provably safe
(LR18). Under the request, the same keystroke cancels a task, writes a Cancel
Log, strips today's ledger links, and recovers dependents. That violates the
no-silent-state rule that governs hides (`relation-label-hide-is-suggestions-only`),
themes, and freshness decay (which asks an explicit approved-decision question
after N keeps rather than decaying silently).

**[ADJUSTMENT]:** the label match only *arms* a preview. The gesture still
needs one explicit accept with the cancel visible (amber `will cancel` line +
dry-run text). No background or relabel path ever cancels silently.

### C2. The `~~` direction trap [ADJUSTMENT: cancel S, but confirm which S]

Labels read "S ‹label› T" from the source's side (§3.2). In `~`, S is usually
the new draft task — canceling S is what the user means ("this new thing is a
duplicate of that"). In `~~`, S is the *existing* task the user named
(LX2: `Write outline ~~sase_blog:prj|"next step"` puts the edge on
`sase_blog`'s `^prj` LINKS). Typing `~~old:task|"duplicate of"` therefore
reads "old is a duplicate of new" and would cancel the canonical task,
keeping the throwaway. Users will absolutely do this by accident because `~`
vs `~~` is already the subtlest part of the grammar (LP1–LP2, LG7).

**[ADJUSTMENT]:** the preview must name the task that will cancel in plain
words ("Cancel ‹S text› — it stays in history; ‹T› survives"), and the
`~~`-onto-new-task shape should carry an extra confirm or refuse with a
teaching error suggesting swapping direction. Never infer "cancel the newer
task" — cancel the source, but say which one loudly.

### C3. Scope creep: every writer becomes a cancel writer [ADJUSTMENT: narrow the trigger]

"When the relation description they are selecting would result in
cancelation" sounds like the picker, but implemented as "any LINKS write with
that key cancels," the trigger fires from: capture `~`/`~~`, nav Links and
Linked-from stages (§8), hand-edit mirror follow-ups (LG10), counted
`N Ctrl+Shift+L` batches (LG12), `bob relations rename` (LR7 rewrites spans in
`done/` + previous daily), and reconcile courtesy mints. Rename is the sharp
edge: renaming `see` → `duplicate of` would cancel every source carrying the
old label — a bulk destructive rewrite from a vocabulary operation.

**[ADJUSTMENT]:** only the edge-*creating* gesture cancels, and only when the
source is open and unblocked-safe (see § below). Relabels, renames, hand-edit
bursts, reconcile, and `done/`/previous-daily sources never cancel. A counted
batch cancels each source only with per-source preview rows, not one blanket
flag.

### C4. Inertness, vectors, and cross-client agreement cost

This is the expensive part, not the ledger cleanup. Every LK/LW/LR/LX/LG/LC
vector that asserts "status byte-identical apart from minted id" needs a
`*_with_cancel` twin; Rust and all three JS twins (grammar, live index, chip
model, cycler/block-id recognisers) must copy the new vectors; `docs/plan.md`,
`docs/task-status-hooks.md`, and `docs/reference/configuration.md` need
matching edits; `just docs-check` gates it. If any twin lags, chips will show
open while the line is `[-]`, or reconcile will fight the cancel. The design
below isolates the blast radius to one new config key + one new planner +
additive JSON so the twins can adopt it in one pass.

## Recommended design (explicit link + cancel)

### D1. Config: `relations.cancels_source_labels` (chezmoi-owned)

```yaml
relations:
  linked_from_lines: true
  cancels_source_labels: ["duplicate of", "superseded by"]
```

- Location: `home/dot_config/bob/config.yml` in chezmoi (the only writer is
  Bryan via chezmoi; bob only reads, like `linked_from_lines`).
- Semantics: list of **label keys** (matched with `relation_label_key`, so
  `Duplicate  OF:` still matches, but `dup of` does not). Empty/absent =
  feature off. Unknown/empty strings refused at parse with the existing
  config-warning pattern; invalid type falls back to empty + warning (never a
  hard exit outside `bob plan`-style gates, per `configuration.md`).
- Why not booleans per label or a map: a list is the smallest thing that
  survives rename (rename should also offer to update this list — see D7),
  sorts stably, and renders trivially in `bob relations list -f json` as
  `cancels_source: true` per row.
- CLI rules (`cli_rules.md`): no new subcommand; this is config, not
  `bob capture` children (frozen) nor `bob task` verbs (this does not rewrite
  the whole vault, only S + mirror + ledger).

Alternative considered and rejected: storing the flag in the per-host journal
(`.bob/relations/<host>.jsonl`, the hide/rename home). Journals are for
per-host prefs (hide/unhide/rename), synced via union merge; a cancel policy
is a deliberate user-owned rule that should be versioned, reviewed, and
identical on every host — chezmoi config, not a last-writer-wins journal.

### D2. Matching: key, not spelling; creation, not presence

- Match on `relation_label_key(typed label) ∈ set(keys(cancels_source_labels))`.
  Display spelling, case drift, and `spellings[]` never matter.
- Fire only when the edge is **created** (`added`), not `relabeled` or
  `unchanged`. Re-adding the same edge is a no-op and must not re-cancel or
  duplicate the Cancel Log.
- Never fire from: `bob relations rename`, hand-edit bursts, reconcile
  passes, `LINKED FROM` edits, or any write whose source is in `done/`, the
  previous daily note, `_templates`, or fenced code (the LX7 refusal set).
  Those keep today's "None" behavior.
- Source must be open and completable-adjacent: ` `, `*`, `/` (and `?` only
  via the Explicit whole-item policy in `task_complete/tree.rs`). Done `x`,
  cancelled `-`, and recurring lines refuse with the existing teaching errors
  instead of canceling. A `^prj` source cancels like any task but must surface
  the project-blocking consequence (every open resident is Blocked while its
  `^prj` is Blocked — `projects-block-from-prj-line`); the preview must say so.

### D3. What one accept writes (atomic, one undo)

Order inside the single staged batch / single transaction:

1. Validate + mint block ids exactly as today (target needs id; source minted
   silently once for the mirror when mirrors are enabled).
2. Write S's LINKS edge + T's LINKED FROM courtesy mirror (today's planner,
   unchanged).
3. Cancel S: `[-]` + `❌ **CANCEL LOG**` first-child entry naming T, e.g.
   `- *2026-10-28* — duplicate of [[sase#^retry-design]]`. (Copy below.)
4. Ledger: run the existing canceled-reference cleanup against today's daily
   note for S's block id (dedupe → canceled-subtree removal → empty-Pomodoro
   removal), same semantics as the Ctrl+Shift+P Cancel row. Do not reimplement.
5. Dependents: cancelled close recovers only, never offers successors (reuse
   SO28 path). No successor picker opens — a duplicate must not sprout
   successor offers pointing at the dead task.

Failure atomicity: any refusal (malformed LINKS, duplicate block id,
stale note, quiet-deferred mirror BR5, lock busy) aborts the whole batch and
leaves the vault byte-identical, exactly like LX8–LX10 today. A dry run
previews all four steps and writes nothing (LX12 parity).

Undo: same-note = one Ctrl+Z (nav) / one capture transaction; cross-note =
S commits, then best-effort T mirror follow-up with the existing
`· 🪢 LINKED FROM not updated` suffix on failure — but the cancel of S never
rolls back because the mirror failed. The notice must distinguish "linked +
canceled; mirror pending" from "nothing happened."

### D4. Indication: calm, explicit, in bob's words (beautiful, not loud)

Clients render only what bob returns; no app-side label lists (thin-client
rule). Additive JSON, `schema_version` unchanged:

- `capture-complete relation_label`: each suggestion gains
  `cancels_source: true|false`. The typed row carries it too. `hidden_count`
  pattern is the model (`hidden_count` present, possibly 0).
- `capture-complete relation_to/from`: each candidate gains
  `cancels_source_with_label: {label, key} | null` once a label is typed —
  so the picker can show "will cancel" next to the *pair*, not just the label.
- `capture --dry-run` + live per-item: `cancellation_previews[]`
  (`{source, target, label, key, action: cancel_source|refused, reason?}`) and
  the existing `relation_updates[]` / `linked_from_line_updates[]` /
  `mirror_skipped[]` stay unchanged. A `cancels_source` warning object
  (`{code: "cancels_source", label, source_text, message}`) carries the
  bob-authored sentence clients display verbatim.

Human copy (amber `🪢`, existing accent only; no new palette, no emoji beyond
the relation glyph):

```text
🪢 duplicate of [[sase#^retry-design]] · will cancel "Fix flaky retries"
   Cancel "Fix flaky retries" — it stays in history; "Design a retry policy" survives.
```

Mac relation card: live `S — label → T` sentence gains one amber subline
`Cancels S` plus the same sentence as a tooltip; `↩` still inserts, `Esc`
still cancels to a reopen chip (task-pickers contract). Obsidian Links stage:
CURRENT rows with a configured label show a muted `will cancel` pill; `⇧↵`
opens the label field with the pill visible before `↵` commits; `Ctrl+D`
(clear all outgoing) with any configured edge shows a confirm listing each
source that would cancel — or refuses bulk-cancel and asks to cancel
one-by-one (safer default; see open questions).

### D5. Ledger cleanup detail (requirement 3, no new code)

After S cancels, the same invocation runs the `task-status-hooks` canceled
pass scoped to S's `(path, block-id)`: remove S's list-item subtree under open
Pomodoros in today's daily note, then drop newly childless Pomodoros. This is
byte-for-byte the Ctrl+Shift+P Cancel behavior, so chips (live index, LC8),
`removed_canceled_references` JSON, and the human `🪢` group all agree.
Closed Pomodoros, previous dailies, and `done/` are untouched by this step —
same as today.

### D6. Beautiful edge wording (examples)

Same-note cancel (`~`):

```text
Fix flaky retries ~sase:retry-design|"duplicate of"
→ 🪢 would link to "Design a retry policy" · duplicate of · will cancel this task
```

Reverse (`~~`) — the dangerous one, made loud:

```text
Write the migration note ~~sase_blog:prj|"duplicate of"
→ ⚠ "sase_blog — duplicate of → Write the migration note" will cancel sase_blog's ^prj
  (a project task; its open residents stay Blocked while it is Blocked).
  Swap direction? Use ~ to cancel the new task instead.
```

Cancel Log entry (first child, existing slot):

```markdown
- [-] #task Fix flaky retries ^fix-flaky-retries
  - ❌ **CANCEL LOG**
    - *2026-10-28* — duplicate of [[sase#^retry-design]]
  - 🪢 **LINKS:** duplicate of [[sase#^retry-design]]
```

LINKED FROM on the survivor stays history-only, exactly as today:
`🪢 **LINKED FROM:** [[mac_inbox#^fix-flaky-retries]] (duplicate of)`.

### D7. Rename, hide, and catalog interplay

- `bob relations rename OLD NEW` never cancels, even when NEW is configured.
  Preview lists whether OLD/NEW is in `cancels_source_labels` and offers
  `--update-config` (or prints the exact chezmoi edit) so Bryan can move the
  policy in the same breath. Without the flag, config is untouched.
- Hiding a configured label (`||`, Ctrl+D, `bob relations hide`) keeps working:
  hidden still cancels when typed exactly (hide is suggestions-only,
  `relation-label-hide-is-suggestions-only`). The typed row shows both
  `hidden: true` and `cancels_source: true` — two pills, no conflation.
- `bob relations list -f json` gains `cancels_source` per row so the policy
  is discoverable without opening chezmoi.

### D8. Vectors, docs, and rollout

- Contract: amend `docs/task-relations.md` §§2, 8, 12, 14 with one exception
  block ("configured link+cancel") plus new vectors
  `LW15_with_cancel`, `LX17_with_cancel`, `LG16_with_cancel`, `LC15_with_cancel`;
  update `docs/task-status-hooks.md` (cancel now reachable from relations),
  `docs/reference/configuration.md` (`relations.cancels_source_labels`), and
  `docs/guides/link-related-tasks.md` (fix the unquoted-label gotcha noted in
  prior research while touching it).
- Tests: extend `src/native/config/relations.rs` parse tests (list shape,
  key normalization, invalid-type fallback), `capture_complete/tests/relations.rs`
  (suggestion flags), `capture` batch tests (atomicity, dry-run parity,
  `~~` refusal copy), and `task_status_hooks/tests/structure.rs` (ledger
  removal after relation-cancel). JS twins copy
  `tests/fixtures/relation_labels/vectors.json` additions byte-for-byte.
- Rollout: land config support with empty default (no behavior change), then
  add the chezmoi lines, then enable each client surface. No migration: old
  `duplicate of` edges stay history and never retro-cancel (reconcile must
  not backfill cancels — state that explicitly).

## Fully automatic variant (not recommended)

If Bryan wants zero-confirm cancel, add
`relations.auto_cancel_mode: "prompt" (default) | "auto"`. In `auto`, the same
planner runs without the accept step, but keep every other guard (creation-only,
open-source-only, atomic, dry-run-visible). Cost: the `~~` trap and silent
bulk-rename risk return, and `just docs-check` + JS-twin lag become
release-blockers rather than polish. I would ship `prompt` for a month first
and only add `auto` if the prompt is consistently accepted without edits.

## Alternatives considered

| Option | Shape | Verdict |
| --- | --- | --- |
| A. Magic label match (request as written) | Any write with a configured key cancels S silently | Reject: breaks inertness, silent, `~~` trap, rename bulk-cancel |
| B. Explicit link + cancel (recommended) | Configured label arms a previewed accept; one atomic link+cancel+ledger write | Ship: intuitive, reliable, beautiful |
| C. Separate "close as duplicate" command | `bob task cancel-as-duplicate S T` / Task Card row that writes both | Worthy follow-up, but more CLI surface than needed for two labels |
| D. Keep relations inert; suggest cancel | Relation writes a notice "consider canceling S" with a one-key cancel | Safest, but two steps forever; keep as fallback if B proves too magical |

## Open questions for Bryan

1. Should `~~` onto a new task refuse (teaching error) or double-confirm?
   I lean double-confirm with the swapped-direction hint, because refusal
   breaks the symmetric grammar.
2. Should counted `N Ctrl+Shift+L` with a configured label cancel N sources
   in one accept, or force one-by-one? I lean one-by-one preview rows in one
   gesture (one undo), never a blanket flag.
3. Should a relabel *to* a configured label on an already-linked edge cancel?
   I say no (creation-only), but say so explicitly if you disagree.
4. Cancel Log reason free-text: prompt for an optional reason like the nav
   Cancel row, or always write the `— duplicate of [[T]]` pointer? I recommend
   the pointer always + optional reason only in nav (capture has no prompt).

## Sources checked

- `docs/task-relations.md` §§1–16 (vocabulary, inertness, grammar, slot,
  identity, reconcile, writers, gestures, chips, kill switch, lifecycle,
  label vocabulary RV1–RV9).
- `docs/task-status-hooks.md` (Canceled Task References, empty-Pomodoro
  cleanup, guard rails), `docs/task-dependencies.md` (Cancel Log slot,
  successor SO28/cancelled-close-recovers-only, `~~` vs `&`/`*`).
- `docs/reference/configuration.md` (`relations`, `plan`, `freshness`),
  `docs/reference/plugins/bob-navigation-hotkeys.md` (Cancel row, Links
  stages, successor picker), `docs/capture.md` + prior research
  `202610/task_relation_labels.md` (four ways to add a labelled relation).
- Code: `src/native/config/relations.rs`, `src/native/relation_labels/mod.rs`
  (`relation_label_key`), `src/native/capture/relations.rs`
  (`plan_relation_writes`, `plan_relation_label_hides`),
  `src/native/capture_complete/model.rs` + `candidates.rs` + `render.rs` +
  `shell.rs` (relation contexts), `src/native/task_complete/tree.rs`
  (RootPolicy), `src/native/capture_task_toggle/task_update.rs`
  (pure-postimage planner pattern), `src/native/task_relations/`
  (parse/plan/format).
- Memory: `glossary:task-relation`, `glossary:task-link`,
  `glossary:task-dependency-link`; decisions `task-deps-are-depends-on-links`,
  `relation-label-hide-is-suggestions-only`,
  `relation-label-prefs-live-in-per-host-journal`,
  `relation-label-rename-rewrites-history`, `mac-capture-is-a-thin-client`;
  reference `cli_rules.md`, `docs.md`.
- Chezmoi: `home/dot_config/bob/config.yml` (104 lines, no `relations:` block
  yet — policy lands there).
- Deliberately unread: any `202610/*__cdx.md`, `*__cld.md`, `*__grk.md`,
  `*__gem.md` swarm peer reports (filenames only checked for collision).

# Inferring a Default Pomodoro Theme per Task — Research

## Problem statement

Bryan wants `bob` to suggest which Pomodoro theme (the ` — NAME` tail
component, per `docs/pomodoro-themes.md` PT1) a task belongs with, instead of
relying on memory and manual consistency. The proposal has five parts:

1. New `theme:` frontmatter on area/project notes sets the default theme for
   their resident tasks (and sub-projects). Seed values: `theme: BUILD` on
   `dev.md`, `theme: CHORE` on `love.md`, `theme: WRITE` on `job.md` and
   `sase_blog.md`.
2. Ref (`#ref`) tasks default to `READ`, overriding any area/project default.
3. Completion menus explain *why* a theme is suggested.
4. A per-task override via a new `[theme::<THEME>]` inline property.
5. Auto-stamp `[theme::X]` when a task is linked under a Pomodoro whose theme
   differs from the suggestion (e.g. a `Ctrl+Enter`-family gesture), so the
   override persists across rollover.

This report evaluates whether that is the right shape, grounds each piece in
the current architecture, and recommends an adjusted design.

## Current architecture (what constrains the design)

### Themes are ledger-derived, never task-derived

- Identity: one `+`-separated component of a ` — NAME` tail, keyed by
  `normalize_component` (`src/native/plan_budget`, `src/native/pomodoro_themes/split.rs`).
  Decision `decisions:pomodoro-theme-is-one-component`.
- Source of truth is canonical daily notes only, via `capture_pomodoros::scan`.
  Task text and homes are explicitly excluded as identity sources (PT2). The
  completion ranking (PT7) is Today → Recent → create → substring → utility,
  implemented in `src/native/capture_complete/theme_menu.rs::compose`.
- Every named completion row already carries `themes: ThemeRef[]`
  (`key/name/hue/hue_source`), and `bob plan` returns `theme_refs` beside
  `theme_names`. So the pipe for "which themes does this row mean" exists; the
  pipe for "which theme does this *task* want" does not.
- Preferences (hide/color/rename) live in `.bob/themes/<host>.jsonl`,
  last-writer-wins, bob-only writer (PT4, `decisions:theme-prefs-live-in-per-host-journal`).
  Anything new that is a *preference* should live there; anything that is a
  *task fact* belongs on the task line or the note.

### Hue already couples areas to themes — and deliberately so

PT5 resolves hue as pin → exempt-mute → matching top-level area stem →
stable hash. So `JOB` already wears aqua because an area note exists, without
any `theme:` frontmatter. The proposed `theme: WRITE` on `job.md` is therefore
*not* a hue change; it is a new *suggestion* edge. Keep the two concepts
separate in all UI copy: hue answers "what color is WRITE", suggestion answers
"why is WRITE pre-selected for this task".

### Frontmatter parsing is line-based and cheap to extend

`src/native/projects/scan.rs::parse_frontmatter` + `frontmatter_value` do
prefix matching (`line.strip_prefix(key)` + `:`), with `trim_yaml_scalar` for
quotes. `type`/`parent`/`status`/`project_name_aliases` all flow through it.
A scalar `theme: WRITE` fits the same parser with no YAML dependency. It is
additive: unknown keys are ignored today, so old binaries stay safe.

Area/project hierarchy: `parent_notes.rs` resolves root-level areas and project
`parent:` targets; `projects/scan.rs` records `parent_target` per project. A
sub-project default therefore has a natural resolution order already:
task note → parent project chain → top-level area. No new graph is needed.

### Inline task fields have a shared scanner and an ownership table

`src/native/task_fields.rs` (`inline_fields(key)`, `has_any_field`) is the
single scanner for `[key:: value]` / `(key:: value)`, shared by capture,
task-toggle, task-move, ref follow-ups, and randomize. `docs/reference/vault-format.md`
documents the ownership split: `scheduled`/`priority`/`due` are authored,
`created`/`completion`/`id`/`dependsOn` are machine-derived, freshness fields
have their own writers. Any new `[theme::]` field must take a row in that
table, with an explicit writer set, or reconcile loops and the Task Card will
fight over it.

Rendering precedent: `bob-ledger-tools` already hides raw fields and paints
marks — `[priority::]` becomes signal bars, dates become compact date-family
marks, `#task` becomes a teal hash, themes in Ledger/plan/Stats become tinted
pills (PT6: 16%/24% tint, 4px radius, `+` stays neutral, never an area ● dot).
A `[theme::]` pill has a ready-made visual language; there is no need to
invent one.

### Task Link creation is split across three writers

- **Obsidian plugins** own the interactive gestures: Task Status Cycler owns
  `Ctrl+Enter` (complete/recover), `bob-navigation-hotkeys` owns the review
  walk and the `Ctrl+Shift+Enter` link-to-today picker (plan picker with the
  `plan 2/3 · 6/10` footer), Task Card owns lane/label commits.
- **`bob capture`** owns the headless path (`:note:block`, `=name`, `x`
  closes, successor offers gated by `plan.link_unblocked`).
- **Bob Mac Capture is a thin client** (`decisions:mac-capture-is-a-thin-client`):
  it never computes previews; it renders what `bob capture --dry-run` returns.

Any "auto-stamp on link" behavior must therefore be specified once in Rust
(a pure resolver both callers share) and surfaced in both the plugin picker
and `bob capture`, or the two writers will diverge exactly the way the thin-client
record was written to prevent.

### Ref tasks are recognizable but the signal is textual

`src/native/ref_tasks/line.rs` detects `#ref` tasks by whitespace-token match
(`has_ref_token`, case-insensitive; `#references`/`#ref/x` excluded). The
`task_kind` plumbing in `capture_complete` candidates already distinguishes
task kinds per row. So "ref task → READ" is implementable as a rule over data
bob already scans — no new index required.

## Critique of the plan as written

**The core idea is sound and worth building.** Bryan's vault already has the
two halves of the mapping: notes are organized by area/project, and work is
logged by theme. Stating the intended mapping once (on the note) instead of
re-deciding it per Pomodoro removes a daily micro-decision, and persisting the
exception (`[theme::]`) instead of re-deciding it after every rollover is the
right persistence. The direction — suggest, explain, allow override, remember
the override — matches how hide (suggestions-only) and rename (previewed,
revertible) were designed.

That said, four parts of the plan need adjustment, and one needs a scope cut.

### 1. `theme:` frontmatter: good, but scope it to one component and define inheritance

Agreed with one tightening: `theme` must be a **single valid theme component**,
not a `+` composite and not free text. Rationale:

- A task links under one Pomodoro entry at a time; a composite default cannot
  be pre-selected without inventing multi-place semantics.
- Validation reuses the existing `invalid_name` rule from `themes rename/split`
  (blank or contains `+` → refuse). Warn, do not crash, on unknown-but-valid
  values: the theme may simply not exist in the ledger yet (same posture as
  typing an unknown name — neutral until committed, PT6).
- Inheritance must be explicit: explicit `[theme::]` on the task wins; else the
  task's own resident note `theme:`; else walk the `parent:` chain to the
  top-level area's `theme:`; else no suggestion. Sub-projects inherit from
  their parent project unless they set their own. Document that area `theme:`
  and area hue are independent (an area can lend its hue to a same-named theme
  per PT5 while suggesting a differently-named default per `theme:`).

Seed values (`BUILD`/`CHORE`/`WRITE`) are fine as data, but land them as vault
content edits, not as part of the binary change, so the release-train rule
(no manual version bumps; CLI/JSON breaks marked with `!`) stays clean.

### 2. Ref `READ` default: good, but make it the *lowest* note-level tier, not an override over everything

The plan says READ "should override any area/project theme default". That
ordering is backwards for the override field: the correct precedence is

1. explicit `[theme::X]` on the task (highest),
2. ref-task rule → `READ`,
3. resident note / parent-chain `theme:`,
4. none.

i.e. READ beats the note default but loses to an explicit per-task stamp.
Otherwise a reading task that Bryan deliberately re-themes (say a `BOB`
maintenance read) could never stick — the ref rule would clobber the authored
override on every suggestion. The plan's intent ("refs default to READ even in
a WRITE project") is preserved; only the interaction with `[theme::]` is
corrected.

One more consideration: `#ref` detection is textual and task-local. A task
nested under a ref note without its own `#ref` token, or a `#ref` task
transcluded elsewhere, should follow the token on the *task line*, not the
note. State that explicitly; otherwise the rule will surprise on embeds.

### 3. "Why" explanation: required, and keep it to one short provenance chip

Agreed — an unexplained pre-selection will read as a bug the first time it
disagrees with Recency. But keep the vocabulary to the existing menu language
(Today / Recent / history carry `origin: "history"` already). Recommended
provenance values (one per row, never stacked):

- `task field` — explicit `[theme::X]`.
- `ref default · READ` — ref rule.
- `note default · <NOTE>` — resident note or inherited parent (name the note
  that supplied it, e.g. `dev`, so inheritance is auditable).
- No chip when there is no suggestion (do not invent `recent` chips on rows
  that already have `origin: history`; the two systems are orthogonal).

Render as a muted suffix in the row description (`zsh` descriptions already do
`recent · Oct 21 · 3 days`), and as a `suggested_theme` object in JSON
(`{theme, source, note?}`, additive, schema stays 1). Do not reorder PT7 groups
for suggestions: a suggested theme that is also Today/Recent keeps its PT7
position and gains a chip + default-cursor affordance. Re-ranking by suggestion
would break the shared `rank` vectors and the muscle memory PT7 protects.

### 4. `[theme::X]`: good, but treat it as authored-readable state with a narrow writer set

Agreed on the field, with three constraints:

- **Validation at write time, tolerance at read time.** Writers (capture,
  Task Card, link gesture) validate single-component, non-blank. Readers
  (menus, reconcile) ignore malformed values with a bounded warning rather
  than failing the row — same posture as malformed journal lines (PT4).
- **Placement follows the existing field order.** Vault-format puts authored
  fields before derived ones and the block ID last. `[theme::]` is authored;
  put it adjacent to `[priority::]` (both are "how to work this task" signals),
  never inside the trailing `id/dependsOn` suffix that reconcile projects.
- **Rendering: hide the raw field, show the theme pill.** In Live Preview /
  reading view / Tasks rows, ledger-tools should replace `[theme:: WRITE]`
  with the standard theme pill (PT6 tint, hue from bob). Keep the raw text in
  source mode so it stays greppable and Dataview-addressable. Do not render it
  as a ● area dot — themes wear tints, places wear dots, and conflating them
  reintroduces the confusion PT6 settled.

Do *not* also mirror the override into `.bob/themes/<host>.jsonl`. The journal
is per-host synced preferences about the catalog; `[theme::]` is a per-task
fact that must travel with the task line across hosts. Mixing them would make
an override host-local until sync, which is exactly the failure mode PT4's
union-merge design avoids for hides.

### 5. Auto-stamp on non-suggested selection: build it, but narrow the trigger

The plan's trigger — "when a theme other than the suggested theme is selected
when adding a task link" — is the riskiest sentence, because "adding a task
link" spans at least three gestures (link-to-today picker, capture
`:note:block` under a named session, Mac Capture submit) and "selected theme"
is only well-defined when the gesture names exactly one Pomodoro. Recommended
narrowing:

- Fire **only** when (a) the task had a suggestion, (b) the gesture links it
  under exactly one named Pomodoro session, and (c) that session's single
  theme component (first component if composite? — refuse composites, see
  below) differs by key from the suggestion. Then append `[theme:: CHOSEN]`
  to the task line (or replace the existing value), in the same atomic
  vault-rewrite transaction as the link, so a mid-write failure rolls back
  both halves.
- **Do not fire** on composite Pomodoro names (`— BOB + DECKS`): suggesting one
  component and stamping another from a two-theme session is ambiguous. Leave
  the task unstamped and let the next suggestion explain. Do not fire on
  unnamed sessions, on closes (`x`), or on successor-offer link insertions
  (those are recovery, not choice — stamping them would launder machine
  decisions into authored fields, the same concern that keeps `unblocked::`
  a machine WRITE and `fresh::` human-only).
- Surface it in the preview: capture `--dry-run` and the picker's confirm
  footer must show `theme WRITE → BOB · stamped` before write, with undo via
  the normal `git revert` of that commit (same runbook as `themes rename`).

The `Ctrl+Enter` example in the request is likely a mislabel: `Ctrl+Enter`
today *completes* (closes) rather than links — the link gesture is
`Ctrl+Shift+Enter` (link-to-today picker) plus capture tokens. Specify the
trigger by gesture contract, not by key name, and cover the headless capture
path identically or Mac Capture will stamp what CLI preview did not.

## Edge cases and interactions to specify

1. **No suggestion, non-matching choice:** no stamp. Absence of a default is
   not a default; stamping every link would spray `[theme::]` across the vault
   and defeat the "only remember exceptions" economy.
2. **Suggestion equals choice:** no stamp, and actively *remove nothing*.
   A task carrying a stale `[theme::]` equal to the current suggestion is
   harmless; auto-cleaning it would create write churn on every link.
3. **Note default changes after tasks were stamped:** stamped tasks keep their
   explicit value (that is the point of the override). Unstamped tasks pick up
   the new default immediately since suggestion is read-time. No migration.
4. **Ref task in a themed note with explicit `[theme::]`:** explicit wins
   (precedence above). The menu chip says `task field`, not `ref default`.
5. **Blocked / future-scheduled / Done tasks:** suggestion still computes
   (it is a read-time hint), but no writer fires on recovery/close paths —
   only on the explicit link gestures above.
6. **`plan.max_themes` / `strict`:** a suggestion never creates a theme and
   never counts against the budget. Only accepting a *new* name does (existing
   `plan_themes_after`/`plan_themes_cap` plumbing, PT7/`capture.md`). Say this
   loudly: suggestions must be free, or users will distrust them on heavy days.
7. **Multi vault / `BOB_DIR` mismatch:** suggestion resolution requires the
   same vault-match discipline as `themes rename` (online writes refuse on
   mismatch; previews do not). Offline preview shows the suggestion with a
   `vault_mismatch`-style refusal only for the write half.
8. **Dataview/Tasks queries:** `[theme::]` is a first-class inline field, so
   `WHERE theme = "WRITE"` works for free. Document one query recipe; do not
   build a new index.

## Alternatives considered

- **Per-task `theme` frontmatter instead of inline field.** Rejected: tasks are
  lines, not notes; frontmatter cannot address one task among many. Inline
  field is the established per-task channel.
- **Journal-stored overrides instead of `[theme::]`.** Rejected: journal is
  per-host and keyed by theme, not by task; overrides must travel with the
  task line and be visible in source.
- **ML/clustered inference ("tasks like this usually go with BOB").**
  Rejected for now: the vault already has authored structure (areas, projects,
  `#ref`) that covers the requested seeds exactly. Ship deterministic rules
  first; log suggestion-accept/reject as future training signal if ever wanted.
  History-derived themes must stay ledger-only (PT2) — task-text mining would
  reopen that decision.
- **Auto-creating missing suggested themes.** Rejected: suggestion ≠ creation.
  Unknown suggestions render neutral (PT6) and only materialize if accepted,
  preserving the theme-cap budget semantics.

## Recommended solution

### Data model (precedence order, read at suggestion time)

```
suggested(task) =
  1. [theme::X] on the task line (malformed → ignore + warn), else
  2. #ref token on the task line → READ, else
  3. resident note `theme:` frontmatter, else nearest ancestor
     via parent: chain with a theme: (project → parent project → area), else
  4. none
```

`theme:` is a single validated component. Validation (`blank` / contains `+`
→ `invalid_name`, mirroring `themes rename/split`) happens at note-scan and at
every writer; readers are tolerant.

### Behavior changes

1. **Note scan:** `projects/scan.rs` + `parent_notes.rs` read scalar `theme:`
   via `frontmatter_value` + `trim_yaml_scalar`, validate with
   `normalize_component`, emit one bounded warning per bad value. Expose
   `note_theme(note) -> Option<ThemeRef-ish>` for menus, capture, and the
   plugin API. Area and project notes share the code path; sub-project
   inheritance walks `parent_target`.
2. **Suggestion resolver (new, pure, shared):** `suggested_theme(task_line,
   note_path, note_chain) -> {key, name, source, note?}` in Rust, covered by
   shared vectors (extend `tests/fixtures/pomodoro_themes/vectors.json` with a
   `suggest` section, mirroring the `menu`/`literal` precedent so JS/Swift
   conformance follows). Both `bob capture` and the Obsidian pickers call it;
   Mac Capture consumes it through `capture --dry-run` JSON per the
   thin-client rule.
3. **Menus:** PT7 order unchanged. Each candidate gains additive
   `suggested: bool` + `suggestion_source` (human: muted `· suggested —
   note default · dev` / `· suggested — ref default · READ` /
   `· suggested — task field`); JSON gains `suggested_theme` on the relevant
   context object, schema stays 1. Default cursor moves to the suggested row
   *within its existing PT7 group*; nothing re-sorts.
4. **`[theme::]` field:** new authored field next to `[priority::]`; writers
   are capture, Task Card, and the link-stamp path only — reconcile never
   invents it (same boundary as `fresh::` vs `unblocked::`). Ledger-tools
   renders it as the standard theme pill and hides the raw span outside
   source mode.
5. **Auto-stamp:** only on explicit single-named-session link gestures with a
   prior suggestion and a key mismatch; atomic with the link write; previewed
   in `--dry-run` and the picker footer; undo is `git revert`. Explicitly out
   of scope: composites, unnamed sessions, closes, successor-offer inserts,
   recovery paths.

### Contracts to update

- `docs/pomodoro-themes.md`: new PT12 (suggestion precedence, `theme:`
  frontmatter, ref rule, `[theme::]`, menu chips, auto-stamp trigger).
- `docs/reference/vault-format.md`: `[theme::]` row in the field tables +
  ownership row (authored) + placement rule.
- `docs/plan.md`, `docs/capture.md`, `docs/reference/cli/*`: additive JSON
  fields, picker footer copy, `--dry-run` stamp preview, one Dataview recipe.
- `docs/reference/plugins/*`: Task Card writer + ledger-tools pill rendering
  + `api.themes` suggestion extension.
- Shared vectors + CLI goldens for every new row/field (the repo's established
  conformance mechanism).

### Rollout

1. Rust: frontmatter scan + resolver + menu chips + `[theme::]` read path
   (suggest-only; no writes). Ship behind no flag — suggestions are read-only.
2. Rendering: ledger-tools pill for `[theme::]`.
3. Writers: Task Card editor + auto-stamp in the link gestures + capture
   stamp path with `--dry-run` preview. Seed the four `theme:` values as vault
   content edits in the same window so the feature is demonstrable on day one.
4. Docs + vectors + goldens; `just docs-check` gate.

## Verdict

Build it, with the adjustments above: single-component `theme:`, precedence
`[theme::]` > `READ`-for-refs > note/parent default, explain with one
provenance chip without re-ranking PT7, render `[theme::]` as the standard
theme pill, and auto-stamp only on explicit single-theme link choices with a
previewed atomic write. That keeps themes ledger-sourced (PT2 intact),
preferences in the journal (PT4 intact), hue independent (PT5 intact), menus
stable (PT7 intact), and the thin-client boundary intact — while removing the
exact daily friction Bryan described: decide once per note, override once per
task, never re-decide after rollover.

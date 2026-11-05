# Conditional off-clock by task type (`offclock_types`): research

**Question.** Add a new area/project frontmatter key `offclock_types`
(list of task type names) that works like `offclock` but applies only to
tasks whose type is in the list. First use-case: migrate the vault's area
notes that currently use `offclock` to `offclock_types: [MEET]`.

**Verdict (TL;DR).** The plan is directionally sound but underspecified
in exactly the places that will cause bugs. The single most important
finding: **"the task's type" cannot mean "the `[type::]` field on the
line"** — gcal sync deliberately omits `[type:: MEET]` when the
suggestion is already MEET (`src/native/gcal/render.rs:needs_meet_type`),
so an explicit-field-only check would misclassify precisely the synced
meetings this feature is for. The check must use the *effective* type
(field → reading → note default → global default, per PT13), computed
without a catalog. With that correction, plus a pinned walk-precedence
rule for notes that declare both keys and a gcal probe-line fix, the
feature is a clean, additive change. Do **not** blanket-migrate every
`offclock` area to `[MEET]` without auditing each one: any area whose
non-meeting tasks (lunch, gym, errands) rely on the blanket default
would silently flip to on-clock for all future writes.

---

## 1. How `offclock` works today

- **Parsing** (`src/native/pomodoro_homes/facts.rs:108-123`).
  `offclock:` is a strict scalar tristate: `true` / `false`
  (ASCII-case-insensitive, quotes honored) or `Invalid(anything else)`.
  Absent and blank inherit (`None`). Non-scalars (lists, mappings)
  are `Invalid`. Unit-pinned in
  `src/native/pomodoro_homes/tests.rs:208-239`.
- **Resolution** (`src/native/pomodoro_homes/clock.rs:150-222`).
  `effective_clock(resolver, residence_path, line)`:
  1. explicit `#on` wins (even over `#off`, with conflict flag);
  2. else explicit `#off` / deprecated alias (`#offclock`, `#off-clock`,
     `#untracked`);
  3. else the **nearest** area/project `offclock:` value on the shared
     PT13 root walk (a valid `[root:: NOTE]` starts the walk, else the
     residence note; 16-note, cycle-safe chain). `false` stops the walk
     and resolves on-clock; an invalid nearer value stops the walk and
     resolves on-clock with `ClockSource::InvalidNote` (parent's `true`
     is *not* inherited past it — fail toward Worked);
  4. else on-clock (`ClockSource::Default`).
  Daily notes contribute no default unless `[root::]` retargets the walk.
- **Health** (`src/native/pomodoro_homes/resolve.rs:140-160,231-255`).
  `note_offclock_invalid` (bad value on area/project) and
  `note_offclock_ignored` (key on a non-area/project note), each
  deduped per path. Surfaced in stats/plan diagnostics.
- **Decision lock-in.** `decisions:off-clock-follows-tag-then-note-default`
  (accepted 2026-11-03): writers stamp the effective clock into
  `[t::]` / `[off::]` at write time; **closed rows are history** and
  later default edits surface as drift, never as rewrites. Mixed
  lineups stay Worked in full.
- **Callers of `effective_clock`** (all take only `resolver + path + line`
  and would all inherit conditional behavior automatically):
  `src/native/stats/homes.rs` (`task_off_clock`, `resolve_link_clock`,
  drift via `session_drifted`), `src/native/event_task.rs`
  (`enrich_event_clocks`), `src/native/gcal/clock.rs`
  (`resolve_listed_clock` via synthetic `probe_line`),
  `src/native/gcal/plan.rs` (`apply_effective_clocks`),
  `src/native/capture_pomodoro_close/linked_tasks.rs`
  (`close_fact_from_task`), `src/native/capture_pomodoro_start.rs`
  (`resolve_clock_fact`), plus the Obsidian chip mirror
  (`docs/off-clock-link-chips.md`, which re-resolves on
  `offclock:`/`type:`/`parent:` edits — a contract change must update
  the plugin mirror too; see §6).

## 2. How "a task's type" resolves today (PT13)

`docs/task-types.md` PT13 + `src/native/pomodoro_themes/suggest.rs:81-200`:
first match wins —

1. task field `[type:: X]` / `(type:: X)` (legacy `[theme::]` read;
   `src/native/task_theme.rs:parse_task_theme`);
2. reading task (`#ref` / `^ref*`, uses `plan.reading_theme`, default `READ`);
3. note default `task_type:` / legacy `theme:` on the residence chain
   (scalar single-component name, `off` stops the walk;
   `src/native/pomodoro_homes/facts.rs:208-244`);
4. global default `plan.default_type`;
5. else none.

Canonicalization is pure: `canonical_theme_name` → `canonicalize_pomodoro_name`
→ `normalize_component` (whitespace-collapsed, lowercased key). No vault
I/O beyond the already-loaded `NoteFacts`; the `Catalog` is only needed
for display spellings, **not** for key matching.

Gcal's writer closes the loop: `needs_meet_type`
(`src/native/gcal/render.rs:170-189`) runs `suggest_for_task` on a probe
line and **omits** `[type:: MEET]` when the suggestion is already MEET.
Consequences (§4.1): synced event lines carry the field exactly when the
type is *not* otherwise derivable, and lack it exactly when it *is*.
Any `offclock_types` check must therefore reproduce the suggestion walk,
not just read the line field.

## 3. Critique: is this a good idea?

**Yes, with corrections.** Area-scoped conditional clock is the right
shape for the stated reality (personal-area meetings are off-clock;
work meetings are not — a global "MEET is off-clock" rule cannot express
that, and per-task `#off` tags on every synced event don't scale).
It reuses the existing walk, health, drift, and frozen-history machinery,
so it is additive: no JSON breakage, no closed-row backfill.

**Risks that must be designed out, not discovered later:**

1. **Type-source ambiguity.** "Tasks which have one of the types" must
   mean *effective* type (PT13 walk), not line field. Field-only is
   cheaper but wrong for default-sourced MEETs (see §4.1).
2. **Blanket-migration hazard.** Today `offclock: true` covers *every*
   task in the area. If an area's non-MEET tasks (meal prep, workouts,
   errands filed under a personal area) depend on that default, migrating
   to `[MEET]` flips all their future sessions to Worked and pollutes
   Worked metrics. Each area needs an individual verdict, not a sed script.
3. **Drift noise on migration.** Old closed `[off::]` rows stay valid
   history, but `session_drifted` recomputes from current defaults: every
   old off-clock session whose links are non-MEET tasks will newly report
   drift after migration. Expected and harmless, but the migration runbook
   must say so or it will read as breakage.
4. **Probe-line gap.** Gcal list/sync probes (`probe_line` in
   `src/native/gcal/clock.rs:36-46`, `needs_meet_type` probe in
   `src/native/gcal/sync.rs:677-689`) synthesize lines with **no**
   `[type::]` field. Under a conditional default these probes resolve
   on-clock while the written row (with `[type:: MEET]`, or a task-row
   that *is* MEET by construction) resolves off-clock. Previews would
   disagree with writes. The gcal path must evaluate task rows as MEET.
5. **Hot-path cost.** `effective_clock` runs per task line per scan
   (stats, drift, capture). A catalog-loading type check inside it would
   be a significant regression. The type-key check must be catalog-free
   (field + already-in-hand facts + cached plan config; §5.3).
6. **Hand-written events.** A hand-typed `## Events` row with no
   `[type:: MEET]` and no MEET default has effective type *none* and stays
   on-clock under `[MEET]`. That is arguably correct (typeless ≠ MEET),
   but Bryan should confirm — the alternative (Events-section membership
   implies MEET for clock purposes) conflates grammar with type and I
   recommend against it.

## 4. Alternatives considered

| Alternative | Verdict |
|---|---|
| Global "MEET is always off-clock" (no per-note key) | Rejected: cannot keep work meetings on-clock. Only viable if *every* area migrates to `[MEET]`, at which point collapse to this — don't keep N copies of `[MEET]` forever. |
| Keep `offclock: true`, tag non-MEET tasks `#on` | Rejected: materializes tags onto ordinary tasks; fights the note-default design (decision record explicitly rejected materializing inherited tags). |
| `onclock_types` exception list alongside `offclock: true` | Equivalent expressiveness for the migration case (`offclock: true` + `onclock_types: [everything except MEET]` is worse). Only worth it if areas need "all off except these N types" — not the stated need. Defer. |
| Per-type clock in config (`types: {MEET: {clock: off}}`) | Wrong scope: config is global, but the need is per-area. Rejected. |
| Event-grammar matching (timed `## Events` rows ignore type) | Tempting for robustness, but silently redefines type membership by section; breaks the "type means type" contract. Rejected; document the hand-written-event edge instead. |
| `task_type: off` as the switch | Settled against by the decision record (vocabulary is `[off::]`/JSON `off_clock`). Rejected. |

## 5. Adjustments to the requirements (proposed, for approval)

1. **Match on effective type key, not line field.** Normalize both sides
   with `normalize_component`; compare keys (so `meet`, `MEET`,
   `"Meet"` all match). Covers field-, reading-, note-, and
   global-default-sourced types.
2. **Single-walk precedence.** The clock walk visits each note once;
   the *nearest* note declaring a valid `offclock:` **or**
   `offclock_types:` decides. On one note, a valid `offclock:` wins over
   `offclock_types:` (blanket beats conditional; document it). An
   *invalid* `offclock:` keeps today's behavior (stop, on-clock,
   `note_offclock_invalid`) and the same note's `offclock_types:` is
   not consulted (fail closed). Absent/blank `offclock:` falls through
   to `offclock_types:` on the same note, then to the parent.
3. **Strict list validation, whole-key invalid.** Accept YAML flow lists
   (`[MEET, READ]`), block lists, and — leniently — a single scalar
   (`offclock_types: MEET` ≡ one-element list). Every element must be a
   valid single type name (`canonical_theme_name` accepts; rejects `+`
   composites, blanks, `off`). One bad element invalidates the whole key
   (on-clock + `note_offclock_types_invalid` lint naming the bad entry),
   mirroring the strict `offclock` tristate: a typo must fail loudly,
   never silently narrow. Empty list ≡ invalid (matches nothing by
   accident otherwise).
4. **Non-area/project notes: ignore + lint** (`note_offclock_types_ignored`),
   mirroring `offclock`. Daily notes contribute no default.
5. **No JSON/ClockSource change.** Conditional matches keep
   `source: Note` with the declaring note path — it *is* a note default.
   Additive health vectors only. No `!` contract break.
6. **Explicit tags keep absolute precedence.** `#on`/`#off` on the line
   still beat any note default, conditional or not. No change to the
   counted-links "every link off-clock" rule or mixed-lineup behavior.

## 6. Recommended solution

**Spec.**

- `NoteFacts += offclock_types: Option<NoteOffClockTypes>` with
  `Valid(BTreeSet<String> /* normalized keys, display map kept for lints */)`
  / `Invalid(String)`. Parse in `facts.rs` beside `parse_note_offclock`
  using `frontmatter_scalar` for the absent/blank/scalar shapes plus a
  small list-reader for flow and block sequences (reuse the `type:`-list
  helpers' approach in `src/native/projects/scan.rs`; note
  `frontmatter_scalar` reports non-scalars as `NonScalar`, so the list
  reader keys off that + direct line inspection).
- `resolve_note_default` (`clock.rs:171-222`): at each chain note, read
  `offclock` first (existing semantics incl. lints), then
  `offclock_types`. On a `Valid(set)` entry, compute the task's effective
  type key via a **catalog-free** helper
  (`effective_type_key(resolver, start, line, plan_config)`):
  `parse_task_theme` field → reading-task check (`plan.reading_theme`)
  → note-default walk reusing the already-resolved chain facts →
  `plan.default_type`. If the key ∈ set → off-clock `Note`; else
  **continue the walk** (a parent's blanket `offclock: true` still
  applies — conditional is "no opinion on non-matching types," not
  "force on-clock"). Cache `PlanConfig` per resolver refresh; never load
  `Catalog` in this path.
- **Gcal fix (required, not optional).** `resolve_listed_clock` and
  `needs_meet_type` probes concern rows that are MEET by construction
  (`task == true`): evaluate them with forced effective type MEET (or,
  equivalently, append `[type:: MEET]` to the probe when `task`). Same
  for `apply_effective_clocks` on MEET entries. Without this, list
  previews and sync writes disagree.
- **Health/UX.** New `note_offclock_types_invalid` /
  `note_offclock_types_ignored` vectors + stats/plan surfacing beside the
  existing pair; `capture_warning_code` gains the invalid-code arm;
  Obsidian `bob-plugins` chip mirror updated to the same rule (coordinate,
  since it re-resolves on frontmatter edits); `bob-mac-capture` unaffected
  (thin client). Docs: `docs/reference/vault-format.md` clock table +
  walk rule, `docs/task-types.md` PT13 clock paragraph, decision record
  addendum (new record; the 2026-11-03 record is immutable — link, don't edit).
- **Tests.** Unit: list-shape parsing (flow/block/scalar/quoted/case/
  empty/invalid-element/mixed-valid-invalid/non-scalar-mapping);
  precedence matrix (both-keys, invalid-boolean + valid-list,
  child-`false` over parent-list, parent-blanket under child-list
  non-match, non-area note, daily note, `[root::]` retarget); type-source
  matrix (field, note default, global default, reading task, none).
  Integration: gcal probe-vs-write agreement; stats drift unchanged for
  closed rows; capture close stamps `[off::]` for a MEET task and `[t::]`
  for a sibling BUILD task under one `[MEET]`-conditional area (the
  headline behavior test).
- **Migration runbook (per area, not blanket).** For each `offclock`
  area: (1) list resident non-MEET open tasks that would flip
  (dry-run/preview command — worth building as `bob plan` lint or a
  one-shot preview flag); (2) confirm none rely on the blanket default;
  (3) replace `offclock: true` with `offclock_types: [MEET]` in one
  commit; (4) expect new drift reports on old non-MEET off-clock sessions
  (history stays frozen — no backfill); (5) re-run stats/drift before vs
  after. Keep genuinely whole-area-off-clock notes (if any — e.g. an area
  where even errands are personal time) on `offclock: true`. If *all*
  areas end up `[MEET]`, follow up by collapsing to a global MEET rule
  and deleting the field.

**Rollout order.** Facts parsing + lints → catalog-free type-key
helper → `resolve_note_default` conditional arm → gcal probe fix →
unit/integration tests → docs + decision addendum → plugin-mirror
coordination → per-area migration previews → migrate.

## 7. Open questions for Bryan

1. Confirm effective-type (not field-only) matching, including the
   reading-task and global-default steps, or scope v1 narrower?
2. Which current `offclock` areas are truly MEET-only vs
   whole-area-off-clock? (Determines whether any area keeps `offclock: true`.)
3. Should a hand-written typeless `## Events` row count as MEET for clock
   purposes, or stay on-clock until typed?
4. Accept single-scalar `offclock_types: MEET`, or require list syntax?

---

*Evidence base: `src/native/pomodoro_homes/{facts,clock,resolve}.rs`,
`src/native/pomodoro_homes/tests.rs:208-368`,
`src/native/pomodoro_themes/suggest.rs`, `src/native/task_theme.rs`,
`src/native/projects/scan.rs:431-520`, `src/native/gcal/{clock,render,sync}.rs`,
`src/native/event_task.rs:enrich_event_clocks`,
`src/native/stats/homes.rs`, `docs/reference/vault-format.md`,
`docs/task-types.md` PT13, `decisions:off-clock-follows-tag-then-note-default`.
No vault access performed; area-by-area migration verdicts need the live
vault and are left to the implementation phase.*

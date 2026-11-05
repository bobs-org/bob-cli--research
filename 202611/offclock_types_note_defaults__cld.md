---
title: "offclock_types: per-type off-clock defaults on area and project notes"
researcher: cld
date: 2026-11-05
scope: bob-cli (Rust), bob-plugins (bob-ledger-tools, task-status-cycler), Bob vault (love.md, body.md)
---

# `offclock_types`: per-type off-clock defaults on area and project notes

## TL;DR

- **Build it, and keep it close to your sketch.** A list key on the area or
  project note, read on the same root walk as `offclock:`, is the right shape.
  It covers the case you care about: off-clock time is decided by area and task
  type together. Only life-area meetings are off the clock; meetings under
  `job` stay Worked. No global or type-side setting can express that.
- **Migrating love and body is safe for your history.** Since the feature
  shipped there have been 10 closed `[off::]` rows (Oct 31 to Nov 5). Every one
  is a MEET session, and every Task Link under them resolves to a
  `[type:: MEET]` Event Task. Switching to `offclock_types: [MEET]` creates no
  `clock_drift` on closed rows. What changes is future and open rows: love and
  body CHORE work, such as the open `() — CHORE` placeholder linking
  `body#^jenika-note`, becomes Worked. Your `bob#^off-meets` task ("Start only
  marking [[love]] and [[body]] MEET tasks with `#off`!", typed FIX) says that
  is what you want.
- **I recommend six requirement changes. Each is flagged ⚠️ below.**
  1. Match the task's **effective** type (the PT13 rule), not only a literal
     `[type::]` field.
  2. The **nearest declaration wins**: a type that does not match stops the
     walk on-clock and does not fall through to a parent's `offclock: true`.
  3. If one note has both keys, **`offclock_types` wins** and a lint is raised.
     This also allows a zero-risk rolling migration.
  4. Pin down the rules for blank, scalar, and invalid values.
  5. Any write that **changes a linked task's type** while its session runs
     should restamp the running row's clock.
  6. Fix the `bob gcal list` probe line so it carries `[type:: MEET]`.
- **The cost is mostly parity work.** The Rust resolver change is small
  (`pomodoro_homes/facts.rs` + `clock.rs`). The real work is the JavaScript
  mirror in bob-ledger-tools, the shared `pomodoro_clock` vectors, the docs,
  and a decision record that partly supersedes
  `decisions:off-clock-follows-tag-then-note-default`.

---

## 1. What exists today

### 1.1 The rule

From `decisions:off-clock-follows-tag-then-note-default`,
`docs/reference/vault-format.md` § "Task clock tags and note defaults", and
`docs/capture.md` § "Which clock a session is on", the first match decides:

1. A standalone `#on` on the task line means on-clock. It also wins a conflict
   with an off spelling.
2. `#off`, or a deprecated alias (`#offclock`, `#off-clock`, `#untracked`),
   means off-clock.
3. Otherwise the nearest area or project note with `offclock: true|false` on
   the task's **PT13 root walk** decides. The walk starts at a valid
   `[root:: X]` target, otherwise at the task's residence note, and follows
   `parent:` up to 16 notes, cycle-safe. `false` stops the walk. An invalid
   nearer value stops the walk and resolves on-clock, raising
   `note_offclock_invalid`. Defaults on other note kinds are ignored with
   `note_offclock_ignored`, but those notes are still walked through.
4. Otherwise the task is on-clock.

A session's clock comes from the counted-links rule. A session is off-clock
only when it keeps at least one counted link and every link resolves
off-clock. Mixed or unresolved lineups stay Worked. Writers stamp
`[t::]` / `[off::]` at start, close, gcal sync, settling, and running-lineup
edits. Closed rows are frozen. Later changes show up as `clock_drift` in
`bob stats` health.

### 1.2 Where it lives in code

| Concern | Location |
| --- | --- |
| Parse `offclock:` | `src/native/pomodoro_homes/facts.rs`: `NoteOffClock {True, False, Invalid}`, `parse_note_offclock` (via `frontmatter_scalar`) |
| Resolve the effective clock | `src/native/pomodoro_homes/clock.rs`: `effective_clock` → `resolve_note_default` walks `home.residence_chain` and returns `ClockResolution {off_clock, source, note, conflict}` |
| Lints | `pomodoro_homes/resolve.rs` (`lint_note_offclock_invalid` / `_ignored`), messages in `stats/homes.rs:1126-1145`, capture warning mapping in `capture_pomodoro_close/linked_tasks.rs:1487` |
| Writers and readers that call `effective_clock` | capture start (`capture_pomodoro_start.rs:486`), close (`capture_pomodoro_close/linked_tasks.rs:1444`), Event Task enrichment (`event_task.rs:729`), stats drift and homes (`stats/homes.rs:800,872`), gcal plan (`gcal/plan.rs:2341-2405` via `ClockLookup`), gcal list (`gcal/clock.rs`) |
| Effective task type (PT13) | `src/native/pomodoro_themes/suggest.rs`: field → reading rule (`plan.reading_type`) → nearest `task_type:`/`theme:` → `plan.default_type`. Needs a `Catalog` only for display names, and returns **no suggestion for closed tasks** |
| JavaScript clock mirror | bob-plugins `plugins/bob-ledger-tools/src/036-pomodoro-clock.js` `taskEffectiveClockResolution`, used by `273-plugin-pomodoro-home-chips.js`, `291c-plugin-gcal-event-clock.js`, the off-clock link chips, and task-status-cycler `062-pomodoro-clock.js` (through the `taskEffectiveOffClock` API, with a tag-only fallback) |
| JavaScript PT13 mirror | `bob-ledger-tools/src/279-plugin-task-theme-suggest.js` (`pomodoroThemeResolveWithoutTaskField`, `pomodoroThemeTaskFieldState`) and `279-plugin-task-theme-home-facts.js` |
| Shared vectors | bob-cli `tests/fixtures/pomodoro_clock/vectors.json` (23 cases), copied byte-for-byte to bob-plugins; plus the OC/OR/OV tables in `docs/off-clock-link-chips.md` |

Two facts shape the design:

- **Event Tasks already carry MEET.** `gcal/render.rs::needs_meet_type`
  writes `[type:: MEET]` whenever the PT13 suggestion for the rooted row would
  be anything else. love and body rows therefore always carry an explicit
  `[type:: MEET]`, because love's default is `theme: CHORE` and body falls
  back to `plan.default_type: CHORE`. Rows rooted at `meet` inherit MEET from
  `meet.md`'s `task_type: MEET` and carry no field.
- **The two walks start in the same place.** The clock walk and the type walk
  both start at `root_walk_start` and use the same `residence_chain`, so one
  resolver and one fact cache can serve both.

### 1.3 Vault evidence (read-only scan, 2026-11-05)

- Only **`love.md`** (`offclock: true`, `theme: CHORE`) and **`body.md`**
  (`offclock: true`, no type default, so `plan.default_type: CHORE` applies)
  declare `offclock`. About 28 notes inherit through them, including `abby`,
  `kelly`, `dog`, `fun`, `gym`, `dentist`, and `outlive`. `.obsidian/types.json`
  has no entry for `offclock`.
- The configured `types:` are BUILD, CHORE, FIX, MEET, PLAN, READ, and WRITE.
  MEET is in the vocabulary.
- **Closed off-clock rows:** 10, all `— MEET`. Every counted link is an Event
  Task with `[type:: MEET]`. Five are off through an explicit `#off` and five
  through love or body inheritance. **None would drift** under
  `offclock_types: [MEET]`.
- **Rows that will change:** open or planned placeholders that link
  non-MEET love or body tasks, such as `2026/20261103.md`
  `- [ ] () — CHORE` → `[[body#^jenika-note]]`. Today it would start as
  `[off::]`. After the migration it starts as `[t::]`, which is the intended
  fix.
- **Your intent:** `bob.md` `^off-meets`: "Start only marking [[love]] and
  [[body]] MEET tasks with `#off`!" `[type:: FIX]`. A sibling task,
  `^no-off-task-limit` ("Stop counting `#off` tasks as a part of task limit!"),
  is in flight. It must use the same effective-clock resolver, or the two
  features will disagree about which tasks are off-clock.

---

## 2. Is this a good idea?

**Yes, with the clarifications below.**

What it gets right:

- **The axis is area × type, and only a note-scoped key can express it.**
  "Meetings are off-clock" is wrong for `job`. "Everything in love is
  off-clock" is wrong for the chores you do in a focused Pomodoro. Neither a
  global type rule nor an area-only rule can say "MEET, but only in love and
  body".
- **It keeps everything already decided.** Tags still win. Closed rows stay
  frozen. Nothing is materialized onto task lines. The mixed-lineup rule is
  unchanged. Event Tasks that inherit off-clock still settle. This adds one
  key and one comparison to a walk that already exists.
- **Types are visible and editable.** You see MEET as a pill on the row and
  can retype a row, or tag it `#on` / `#off`, to override it. That beats an
  invisible structural rule.
- **It is cheap at runtime.** Type resolution runs only when the walk lands on
  an `offclock_types` note, and it reuses facts the resolver already caches.

What to be careful about:

1. **Type writes now change the clock.** Retyping a task, naming or renaming a
   running Pomodoro (which retypes its open linked tasks), and the MEET landing
   rule ("D is MEET: take the retype path") can each flip a linked task's
   clock. Close already restamps from the kept lineup, so closed history is
   right. A running row's key would be stale until close, though. See
   adjustment 5.
2. **Body time that is not a meeting becomes Worked.** A Pomodoro linked to an
   untyped `gym` or `body` task (CHORE through `default_type`) will now stamp
   `[t::]`. Your FIX task suggests that is intended. If you ever want, say,
   workouts off the clock, the escape hatches are `#off` on that task or
   adding its type to the list (`offclock_types: [MEET, GYM]`). Both compose.
3. **Two keys can contradict each other on one note.** That needs a rule (see
   adjustment 3).
4. **Parity work.** The resolver now needs the PT13 type, and PT13 needs
   `plan.reading_type` and `plan.default_type`. The Rust clock resolver and the
   JS `taskEffectiveClockResolution` don't currently read plan config. Both
   need it, or the rule must deliberately skip those steps (I recommend
   against skipping; see adjustment 1).

---

## 3. Alternatives considered

| # | Approach | Verdict | Why |
| --- | --- | --- | --- |
| A | **`offclock_types: [MEET]` list key on area/project notes** (your proposal) | **Recommended** | Scoped by area, composes with tags and the existing walk, and adds no Obsidian property type conflict. |
| B | Overload the existing key: `offclock: [MEET]` (bool or list) | Rejected | One key, but Obsidian assigns one property type per name across the vault, so mixing checkbox and list values gives "type mismatch" in Properties. Every parser (Rust line-based, JS metadataCache) would also need to handle bool, string, and list. |
| C | Type-side config: `types: {MEET: {offclock_in: [love, body]}}` in `config.yml` | Rejected | Moves area knowledge out of the vault into per-host config, names areas by string (fragile under renames), and means the JS mirror reads config to resolve a vault fact. |
| D | Event-based: `offclock: events` (only Event Tasks under the note) | Rejected, but closest runner-up | Needs no type resolution. But it misses hand-captured MEET tasks, ignores your type vocabulary, and keeps a hand-retyped event off the clock. Type is the concept you actually reason with. |
| E | gcal writes `#off` on events routed to love/body | Rejected | This is the "materialize inherited tags" option already rejected in the decision record: it fights Google titles and rewrites history when routing changes. |
| F | Keep `offclock: true` and add an inverse `onclock_types: [CHORE, …]` | Rejected | Wrong polarity for this case. You would list every type except MEET, and any new type would default to off-clock. |
| G | No code: remove `offclock: true` and type `#off` in family calendar titles | Fallback only | Works today, but brings back the per-event friction `offclock:` was built to remove. |

---

## 4. Requirement adjustments (⚠️ = I'm changing or tightening your spec)

**⚠️ Adjustment 1: match the effective type (PT13), not the literal field.**
A task matches when its *effective* type key, compared with
`normalize_component`, is in the list. Use the full PT13 order: the task's
`[type::]` / `[theme::]` field, then the reading rule, then the nearest note
`task_type:` / `theme:` default, then `plan.default_type`. The one change from
PT13 suggestion: **closed tasks resolve too.** Use the field if one is set,
otherwise inherit, because clocks are computed for `[x]` rows at close, sync,
and drift time (`suggest_for_task` currently returns `None` for closed tasks).
*Why:* `meet`-rooted events carry no field, and "type" in Bob means the
effective type everywhere else. A field-only rule would quietly diverge from
the pill you see.

**⚠️ Adjustment 2: the nearest declaration decides.** The walk stops at the
first area or project note that declares either `offclock` or
`offclock_types`. Under `offclock_types`, a task whose type is not listed
resolves **on-clock with source `note`**. It does **not** keep walking to a
parent's `offclock: true`.
*Why:* this matches `offclock: false` and `task_type:` (nearest wins). It also
lets a sub-area narrow a parent: `kelly.md` with `offclock_types: [MEET]`
under a love that says `offclock: true` puts Kelly chores on the clock. With
fall-through, `offclock_types` could only ever add off-clock tasks, never
narrow.

**⚠️ Adjustment 3: if one note has both keys, `offclock_types` wins and a lint
is raised.** Raise `note_offclock_shadowed` (code name open) in stats health
only, not as a per-capture warning.
*Why:* this follows the `task_type:`-over-`theme:` precedent (the more
specific key wins, with a warning). It also enables a **zero-risk rolling
migration**: write `offclock_types: [MEET]` next to the existing
`offclock: true`. Old binaries and plugins ignore the unknown key and keep
today's behavior. Upgraded ones narrow to MEET. Delete `offclock: true` once
every host has upgraded.

**⚠️ Adjustment 4: value rules.**

- Accept a YAML list in flow (`[MEET]`) or block (`- MEET`) form. Also accept
  a scalar string as a one-item list (`offclock_types: MEET`), since that is
  the natural hand-typed form beside scalar `task_type:`.
- Canonicalize each item with `canonical_theme_name` and compare with
  `normalize_component`, so `meet` matches MEET. Composite (`A + B`), mapping,
  and unparseable items are **invalid**.
- If any item is invalid, the whole declaration is invalid. It stops the walk,
  resolves **on-clock**, and raises the existing `note_offclock_invalid` code
  (with the message naming the key). *Why:* the established "fail toward
  Worked" direction, and one diagnostic path.
- A blank value or an empty list (`offclock_types:`, `[]`) behaves like an
  absent key and inherits. *Why:* Obsidian's Properties UI leaves those shapes
  when you delete the last item. `offclock: false` already means "nothing off
  here".
- On notes that are not areas or projects the key is ignored with
  `note_offclock_ignored`, and the walk continues through, same as `offclock`.
- A valid name outside the configured `types:` still applies. Optionally add a
  quiet stats lint, the same way `default_type_not_configured` works.

**⚠️ Adjustment 5: type changes restamp a running row.** Add "a write that
changes the effective type of a task linked under the running entry" to the
running-lineup-edit restamp set in `docs/capture.md`. That covers retype,
naming or renaming a running entry, and the MEET landing retype. *Why:* the
Now card and `capture-pomodoros --tasks` must stay honest. Close would
otherwise be the first write to notice. If this proves invasive, document
close-time correction as the explicit rule instead. Open rows never count
toward stats, so this is about honesty, not totals.

**⚠️ Adjustment 6: the gcal preview probe carries the type.**
`gcal/clock.rs::probe_line` builds `- [ ] #task Event [root:: X]` with no
type. Under `offclock_types` that probe resolves to CHORE through love's
default, and `bob gcal list` would show love events as on-clock even though
sync will write them off. The deprecated-tag "already off the clock via love"
advice (`gcal/diagnostics.rs`, `root_only_*`) would break the same way. The
probe must add `[type:: MEET]`, since Event Tasks are MEET by construction.

**Not changed:** the name. `offclock_types` matches `bob types` and the
`types:` config. `offclock_task_types` would line up more strictly with the
`task_type:` key, which exists to avoid confusion with the frontmatter
`type: [[area]]`. That's your call; I'd keep the shorter name.

---

## 5. Proposed semantics (contract text)

> The first matching rule decides a task's clock:
>
> 1. `#on` on the task line: on-clock (wins a same-line conflict).
> 2. `#off` or a deprecated alias: off-clock, including under
>    `offclock: false` or a non-matching `offclock_types`.
> 3. Otherwise, the nearest area or project note on the root walk that
>    declares a clock default decides:
>    - `offclock_types: [T, …]`: off-clock iff the task's effective type
>      (PT13; closed tasks use their field, else inherit) is one of the
>      listed types; otherwise on-clock. When the same note also has
>      `offclock:`, `offclock_types` wins (`note_offclock_shadowed`).
>    - `offclock: true|false`: as today.
>    - An invalid value for either key stops the walk on-clock
>      (`note_offclock_invalid`).
> 4. With no declaration, the task is on-clock.

JSON and labels: keep `clock_source: "note"` and `clock_note` exactly as they
are, so `data-clock-source="note"` chips and existing `capture-pomodoros
--tasks` consumers stay valid. Bob Mac Capture never reads `clock_source`. I
checked `Sources/` in bob-mac-capture. Add **optional** `clock_type` (the
matched type name) wherever `clock_note` is emitted. Human copy stays
`off-clock via love`. The Obsidian chip tooltip may grow to
`Off-clock · MEET from love`.

---

## 6. Implementation sketch

### 6.1 bob-cli (Rust)

1. **`pomodoro_homes/facts.rs`:** add `offclock_types: Option<NoteOffClockTypes>`
   to `NoteFacts`, where `NoteOffClockTypes` is `Keys(BTreeSet<String>)` or
   `Invalid(String)`. Generalize the line-based list reader behind
   `projects/scan.rs::project_name_aliases` into a
   `frontmatter_string_list(frontmatter, key)` helper (flow and block shapes,
   with blank handling consistent with `frontmatter_scalar`).
2. **Key-only PT13 resolver.** Extract from `pomodoro_themes/suggest.rs` a
   catalog-free `effective_type_key(resolver, rules, residence, line) ->
   Option<String>`, where `rules` holds `reading` and `default` keys. Base it
   on `resolve_without_task_field` + `note_default`, with the field read even
   for closed rows. `suggest_for_task` then uses it, so there is one rule.
3. **Type rules on the resolver.** Put a lazily loaded `TypeRules` (from
   `bob_config::load_plan_config(config_path())`, the same pattern
   `gcal/render.rs::needs_meet_type` uses) on `HomeResolver`. Give it a setter
   so stats and tests can inject rules. This avoids changing roughly 8
   `effective_clock` call sites and 30 `HomeResolver::new` sites.
4. **`pomodoro_homes/clock.rs::resolve_note_default`.** For each chain note,
   check `offclock_types` first (which shadows `offclock`), then `offclock`.
   On an `offclock_types` hit, resolve the type key **from the original root
   start** and return `ClockResolution { off_clock: matched, source: Note,
   note, conflict: false, clock_type }`. This needs a new `clock_type:
   Option<String>` field.
5. **Lints.** Add `note_offclock_shadowed` next to the existing lints in
   `ResolverHealth`. Extend the invalid and ignored lint messages in
   `stats/homes.rs` to name the key.
6. **gcal.** Add `[type:: MEET]` to `probe_line` (adjustment 6). Add a test
   that `bob gcal list` and `sync` agree for a love-rooted event under
   `offclock_types: [MEET]`, and for a hypothetical non-MEET rooted probe.
7. **Running-lineup restamp** on type-changing writes (adjustment 5): the
   capture retype and naming paths, and Task Card retypes routed through bob.
8. **Vectors.** Add `pomodoro_clock/vectors.json` cases:
   - love `offclock_types: [MEET]` with an Event Task (off) and a CHORE task
     (on)
   - a mixed MEET + CHORE lineup (Worked, `pomodoro_clock_mixed`)
   - a sub-area narrowing a parent `offclock: true`
   - both keys on one note (types wins, plus lint)
   - an invalid item (on-clock, invalid lint)
   - `[]` inherits
   - a scalar `MEET`
   - an inherited type via `meet` root
   - `#on` and `#off` overrides
   - a closed task without a field
   - `default_type` matching (needs a `config` member in the vector schema)

### 6.2 bob-plugins (JavaScript)

- `036-pomodoro-clock.js::taskEffectiveClockResolution`: read
  `frontmatter.offclock_types` (an array or string from metadataCache) with the
  same rules. On a hit, compute the type key with a new closed-aware helper
  built on `pomodoroThemeTaskFieldState` + `pomodoroThemeResolveWithoutTaskField`
  (fragments share one script scope, so the 036 → 279 order is fine). Pass the
  same plan config the type marks receive (`caps.defaultType` / `reading_type`).
- The off-clock link chips, home chips, gcal event clock, and the
  task-status-cycler `se<X>` path pick this up through the shared resolver.
  Add OR rows to `docs/off-clock-link-chips.md` (a MEET event under love gets a
  chip; a CHORE task under love gets none; a sub-area narrows) and refresh the
  chips on `metadataCache` `changed` for `offclock_types` too. That trigger
  already covers any frontmatter change.
- Copy the updated vectors byte-for-byte, run `npm run build`,
  `npm run build:check`, and `npm test`, then `bob plugins sync` **on each
  host**.

### 6.3 Docs, decisions, and memory

- Docs to update: `docs/reference/vault-format.md` (clock section and
  table), `docs/capture.md` ("Which clock a session is on" and the
  running-lineup-edit table), `docs/off-clock-link-chips.md`
  (Resolution + vectors), `docs/task-types.md` PT13 cross-reference,
  `docs/gcal.md` (inherited clock wording), `docs/stats.md` (lints and drift
  on toggling), `docs/task-status-hooks.md` (settled events wording), and the
  JSON outputs table (`clock_type`).
- A new decision record, for example "Off-Clock Note Defaults Can Filter By
  Task Type", that **partly supersedes**
  `decisions:off-clock-follows-tag-then-note-default`. Glossary edits for
  `area-note`, `project-note`, and `off-clock-pomodoro`. Do these through
  `/sase_memory_write`; I did not edit memory.

---

## 7. Migration plan for the vault

The bob-cli release train and per-host `bob plugins sync` mean athena, apollo,
and the Mac will run different versions for a day or more. The Mac is the gcal
`writer` and will be one of them. Sequence the migration so no host ever
treats a love or body MEET as Worked:

1. Ship bob-cli and bob-plugins with the feature.
2. **Dual-key phase** (enabled by adjustment 3): add
   `offclock_types: [MEET]` to `love.md` and `body.md`, and **keep**
   `offclock: true`. Old hosts keep today's behavior. Upgraded hosts narrow
   to MEET and show `note_offclock_shadowed` in stats health.
3. Confirm `bob --version` and the plugin sync on athena, apollo, and the Mac.
4. Remove `offclock: true` from both notes. Optionally add
   `"offclock_types": "multitext"` to `.obsidian/types.json` so Properties
   shows a list editor.
5. Verify:
   - `bob stats` health shows `clock_drift` unchanged. I expect 0 new.
   - `bob gcal list` shows love events as `· off-clock`.
   - starting the `() — CHORE` row linking `body#^jenika-note` stamps
     `[t::]`.
   - an off chip appears on the MEET links and not on love chores.

If you skip the dual-key phase, the gap between the vault edit and the Mac
upgrade would make any MEET cluster created by Mac-side `bob gcal sync`
stamp `[t::]`, freezing those rows as Worked.

---

## 8. Risks and open questions

- **Coupling to `^no-off-task-limit`.** If that work lands first using
  `line_clock_tag` (tags only), it will disagree with inherited and type-scoped
  clocks. It should call `effective_clock`.
- **Type-change restamp (adjustment 5).** Its scope is a judgment call. The
  minimum is to document close-time correction.
- **Plan config inside the clock resolver.** This is the first time the clock
  depends on `config.yml` (only through `reading_type` and `default_type`, and
  only on an `offclock_types` hit). If you want the clock to stay config-free,
  the fallback is "field, then note default only". I don't recommend it,
  because it would diverge from the type pill for untyped body tasks.
- **Archived tasks.** Drift recomputation for tasks that `bob task archive`
  moved to `done/*_done.md` depends on those notes' `parent:` reaching love or
  body. That is unchanged from today, but worth one vector.

---

## 9. Recommended solution

Ship **`offclock_types`** as a list-valued area and project frontmatter key on
the existing clock root walk, with these semantics:

1. **Tags first.** `#on` / `#off` still win.
2. **Nearest declaration wins.** On an `offclock_types` note the task is
   off-clock iff its **effective PT13 type** (closed tasks: field, else
   inherited) is listed, and on-clock otherwise. No fall-through to parents.
3. **`offclock_types` shadows `offclock`** on the same note, with a stats-only
   `note_offclock_shadowed` lint.
4. **Value rules:** a list or scalar, canonicalized names, any invalid item →
   on-clock plus `note_offclock_invalid`, blank or `[]` → inherit, ignored on
   other note kinds.
5. **Output:** `clock_source` stays `note`. Add an optional `clock_type`.
   Human copy is unchanged.
6. **Shared logic:** implement once in `pomodoro_homes/clock.rs` on top of a
   catalog-free `effective_type_key` extracted from PT13, with type rules
   cached on `HomeResolver`. Mirror it in bob-ledger-tools'
   `taskEffectiveClockResolution` and pin it with new shared
   `pomodoro_clock` vectors.
7. **Two fixes alongside:** the `bob gcal list` probe gains
   `[type:: MEET]`, and type-changing writes restamp a running row's clock.
8. **Migrate in two steps:** dual-key, then remove `offclock: true` once every
   host runs the new bob and plugins.
9. **Record it:** add a decision record that partly supersedes
   `off-clock-follows-tag-then-note-default`, and update the glossary.

This gives you exactly "only love and body meetings are off the clock" today.
It leaves room for `offclock_types: [MEET, GYM]`-style growth, rewrites no
closed history, and keeps one resolver behind every surface: capture, close,
gcal, stats, Obsidian chips, and the status cycler.

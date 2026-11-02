# `#off` / `#on` tags and inherited `offclock:` areas: research, critique, and a recommended design

_Researcher: cld · 2026-11-02 · context: epic `bob-cli-fl` (Off-Clock Pomodoros),
`plan:202611/off_clock_pomodoros.md`, and the vault task `bob#^off-tag`._

## TL;DR

The request is a good idea, and now is the cheapest time to do it. No bob-cli release
has shipped since `v0.4.0` (2026-10-27), so `#offclock` as the canonical tag has never
been in a release. The vault holds exactly **4** Event Task rows that use a deprecated
tag. And the accepted decision `decisions:off-clock-pomodoros-count-apart` already lists
this change as its reopen condition: _"Reopens when … off-clock time should come from an
area property instead of a task tag."_

Recommended shape:

1. **Effective clock = a task's own tag, then an inherited note default.** Precedence is
   `#on` > `#off` (and deprecated aliases) > the nearest area/project `offclock:` on the
   task's root walk > on-clock. This is the same pattern as `task_type:` inheritance.
2. **Compute it only where the clock is already decided**: at start, close, sync, and
   settle. Never store it on tasks. Closed `[t::]`/`[off::]` rows stay frozen history,
   as the existing decision requires.
3. **Keep Google tags faithful.** `bob gcal sync` renders only the explicit tag Google
   carries (` #off` or ` #on`) and never writes an area-inherited `#off` onto a row. Its
   planning (past clusters, created MEETs) still uses the effective clock, through the
   chosen root's note chain.
4. **Deprecation warnings** for `#offclock`, `#untracked`, **and `#off-clock`** go
   through sync's existing `warnings` channel and a new structured `deprecations[]` JSON
   array. `bob gcal list` warns the same way.
5. **Rename only the tag.** The concept (Off-Clock Pomodoro), the ledger key
   `[off:: Nm]`, and the JSON key `off_clock` stay as they are.
6. **Migrate the 4 vault rows only after** every host runs the new bob and plugins.
   Leave write-once ref-sources and prose in closed tasks untouched.

There are three adjustments you should decide on explicitly (§6): deprecate `#off-clock`
too; let area-inherited events **auto-settle** (a real behavior expansion); and make
capture accept `#off`/`#on` at an item edge. Today `bob capture "Walk the dog #off"`
**fails** with `type_not_configured`.

---

## 1. What exists today (verified in code)

### 1.1 The tag scanner and its copies

The alias list `["#offclock", "#off-clock", "#untracked"]` is hard-coded in **five Rust
places** and **three JS places**:

| Where                                                                | What it does                                                                                                                                  |
| -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/native/event_task.rs:941` `line_has_off_clock_tag`              | The vault-side scanner: standalone, case-insensitive, outside code spans and Markdown links, not nested. Used for every task line, not only events. |
| `src/native/event_task.rs:1073` `strip_trailing_off_clock`           | Cleans event titles.                                                                                                                          |
| `src/native/gcal/model.rs:415` `is_off_clock_token`, `:425` `strip_off_clock_tokens` | Google title and description directive parsing.                                                                               |
| `src/native/gcal/lifecycle.rs:210` `strip_trailing_off_clock_token`  | Splits the Google-owned badge run on rows that have no 📅 badge.                                                                              |
| `src/native/gcal/render.rs:56,207`                                   | Renders the canonical ` #offclock` into the badge run.                                                                                        |
| bob-plugins `task-status-cycler/src/062-pomodoro-clock.js:17`        | `POMODORO_CLOCK_TAGS` (Ctrl+Enter closes).                                                                                                    |
| bob-plugins `bob-ledger-tools/src/035-meet-event-run.js:276`         | `eventTaskLineIsOffClock` (`se<X>` starts, event runs).                                                                                       |
| bob-plugins `bob-ledger-tools/src/291-plugin-gcal-events.js`         | The Event painter's off-clock tag range and chip.                                                                                             |

One spelling table (with canonical, deprecated, and `on` entries) should replace all of
these in each repo.

### 1.2 The clock rule consumes a per-link boolean

`clock_verdict(&[LinkFact])` (`event_task.rs:309`) is already pure. Each caller builds
`LinkFact { off_clock: Option<bool> }` by resolving a counted Task Link and calling
`line_has_off_clock_tag(line)` on the task's line:

- capture starts: `capture_pomodoro_start.rs:404-417` (`clock_fact_from_task`), plus the
  same-note Event Task branch that reads `event.off_clock`;
- capture closes: `capture_pomodoro_close/linked_tasks.rs:1231,1260`;
- stats drift: `stats/homes.rs:783`;
- MEET event runs: `capture/meet_event_run.rs` (via `EventTask.off_clock`);
- settling: `task_status_hooks/settle.rs:85` (`if !event.off_clock`);
- gcal planning: `gcal/plan.rs:1645,1725,1985` (cluster clocks) and `:530-565`
  (`kept_off_clock` flip reports);
- the agenda and Mac JSON: `capture_pomodoros_agenda.rs:142,214`, and
  `capture/event_conflict.rs`.

`EventTask.off_clock` is computed from the line alone, in `event_task_from_line`
(`event_task.rs:562`). That is the one structural problem: **an inherited clock cannot
be computed from the line alone.**

### 1.3 The inheritance walk already exists

`pomodoro_homes::HomeResolver` (`pomodoro_homes/resolve.rs`) already:

- honors a task's `[root:: NOTE]` as the start of the walk (`home_for_task` →
  `apply_root_state`, `:237-323`);
- walks `parent:` with a depth cap and a cycle guard (`resolve_note`, `:325`);
- caches `NoteFacts` per note (`facts.rs:39`). `NoteFacts` already parses `root:`,
  `color:`, and `task_type:` (with a `NoteTheme::Off` opt-out, which is exactly the
  `offclock: false` pattern);
- collects lints in `ResolverHealth` (`area_color_invalid`, `root_field_invalid`, …).

Stats drift already has a `HomeResolver` in hand (`stats/homes.rs:798`).

bob-ledger-tools has a **pure JS mirror** of this walk: `pomodoroHomeResolve` in
`142-pomodoro-home-chips.js:487`, which reads frontmatter from Obsidian's
`metadataCache`. task-status-cycler already calls into the ledger-tools `api` from other
features (`170-plugin-pomodoro.js:4`, `085c-successor-theme-write.js:391`). So the
plugins already have the parts they need.

### 1.4 gcal sync warnings

`SyncReport.warnings: Vec<String>` is printed to stderr as `warning: …` (`sync.rs:1342`)
and emitted as JSON `warnings` (`sync.rs:1207`). There is no structured warning type.

The Obsidian auto-sync on daily-note creation (`291-plugin-gcal-events.js:423`) runs
`bob gcal sync -q -f json` and shows nothing on success. As things stand, **deprecation
warnings would be invisible unless you run sync or list in a terminal.**

### 1.5 Capture already collides with `#off`

`#` at a capture item edge is a task-type marker. A dry run on today's vault:

```text
$ bob capture --dry-run -f json "Walk the dog #off"
{"code":"type_not_configured","error":"capture item 1 …: `#off` is not one of your task
types; add OFF under `types:` … or write `\\#off` to keep it as a tag","ok":false}
```

Mid-line `#off` stays prose. `tests/cli/capture/lists.rs:1254` relies on this with
`Walk the dog #offclock now`. The same limitation exists today for `#offclock`, but a
short `#off` is exactly what you will type at the end of a draft.

## 2. Vault survey (apollo, 2026-11-02)

| Finding                                         | Data                                                                                                                                                                                                                                                                                                      |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Event Task rows with a deprecated tag           | **4**, all `#offclock`: `2026/20261031.md:27` Halloween (`[root:: family]`); `2026/20261101.md:27` Grocery Store (`[root:: abby]`); `2026/20261102.md:27` Swings! (`[root:: abby]`); `2026/20261102.md:28` Lincoln Park (`[root:: abby]`, still open). **Every one of them is rooted in love's subtree.** |
| Other standalone deprecated tags                | `bob.md:374`, a **closed** task whose prose reads "Add support for #untracked event tag…". It is a scanner false positive; leave it as history. Also `.bob/ref-sources/chat/**`: write-once preserved sources (`decisions:reference-sources-are-preserved-write-once`). **Do not touch.**              |
| Existing `#off` / `#on` usage                   | **None** standalone. The only hit is `bob.md:99`, inside a code span (`` `#off` ``). No collision.                                                                                                                                                                                                         |
| love's subtree                                  | `love` (area) → `abby`, `family` (created today, `parent: "[[love.md\|love]]"`), `kelly`, `fun` (areas); `dog`, `word_of_day` (untyped) → `lenard`, `rocky`, `surf`, `music`, … Tasks: 25 in `love.md`, 1 in `fun.md`.                                                                                     |
| gcal routes to love's subtree                   | Journal roots: `@love` ×5, `@abby` ×3, `@family` ×1, `@dad` ×2 (`dad.md` does not exist, so it would not inherit), `default meet` ×7.                                                                                                                                                                       |
| Worked time historically attributed to love's subtree | `bob stats show worked -r 1y`: **13 of 41,340 worked minutes**. Off-clock over the same window: 1,495 minutes, mostly 30 unstamped bare spans. Current `clock_drift`: 1.                                                                                                                             |

The last row matters. Making love off-clock **does not create a meaningful discontinuity
in Worked history**, so no re-clocking migration is needed (§4.7).

## 3. Is this a good idea?

**Yes, with caveats.** Four reasons:

- **It fixes the right layer.** The off-clock rule asks "is every kept link an
  off-clock task?" Today the only way to answer "yes" is to tag every task and every
  Google event. Your off-clock life already has a structural home: love and its
  sub-areas. An inherited note default turns "remember to tag it" into "route it where
  it belongs". You already route Google events with `@love`/`@abby`/`@family`, and with
  this change routing alone does the job.
- **It follows an accepted precedent.** `task_type:` is "the nearest area/project
  default; a task field stores only an exception", with an explicit `Off` opt-out. The
  vault already teaches that mental model, so `offclock:` + `#on` is the same model.
- **The decision record expects it.** The reopen condition quoted above is explicit.
- **`#off` is better for the place you actually type it.** That place is a Google
  Calendar title on a phone. Since nothing has shipped and only 4 rows need migrating,
  the rename costs almost nothing now and more every week after.

Caveats you should accept knowingly:

1. **The clock is less visible.** Today the tag on the row is the whole story. After
   this change, an untagged "Lunch @love" row is off-clock because of a frontmatter
   field two notes away. Mitigate by naming the source in the start and close summaries
   (`60m · off-clock via love`) and in the Obsidian painter (§4.9).
2. **Two implementations of inheritance** (Rust, plus the JS mirror in ledger-tools)
   must agree. Mitigate with shared vectors that include frontmatter notes. The
   `pomodoro_clock` vectors already exist for this.
3. **Settling expands.** Every ended, unstarted, love-routed Event Task will
   auto-settle into a closed `[off::]` MEET and be **marked done**, not only the ones
   you tagged (§4.6).
4. **`#off`/`#on` are short, generic tags**, so the risk of false positives is a bit
   higher than with `#offclock`. The boundary rules (standalone token, not nested, not
   in code or links) keep this small, and the vault has zero collisions today.
5. **Churn on the canonical tag.** It changed from `#untracked` to `#offclock`
   yesterday and changes to `#off` today. That's fine now, but the vocabulary should
   then be declared settled in the new decision record.

## 4. Design questions and recommendations

### 4.1 Tag vocabulary

| Spelling                                | Status after this change                          | Vault readers | gcal sync         |
| --------------------------------------- | ------------------------------------------------- | ------------- | ----------------- |
| `#off`                                  | **canonical** off-clock tag                       | accepted      | accepted, rendered |
| `#on`                                   | **new** on-clock override                         | accepted      | accepted, rendered |
| `#offclock`, `#untracked`, `#off-clock` | deprecated aliases of `#off`                      | accepted silently | accepted **with a deprecation warning**; rendered as `#off` |

- Keep accepting the aliases in vault readers indefinitely. It costs nothing and keeps
  old rows, `_conflicts/`, and hand-typed lines correct. Warn only at the Google
  boundary, which is the one place you can't fix with a vault edit, because bob's
  Google grant is read-only (`decisions:bob-gcal-is-read-only-and-proposes-once`).
- **Rename only the tag.** "Off-Clock Pomodoro", `[off:: Nm]`, `off_clock` JSON keys,
  `◌`, and the dashed visuals all stay. Another vocabulary sweep would churn three repos
  for no gain.
- Matching rules: reuse today's scanner rules unchanged (standalone, case-insensitive,
  trailing `])}:.,;!?` allowed, not nested, not inside code spans or Markdown links).
  `#off` must not match `#offclock` or `#off-clock` as a prefix. The existing right-hand
  boundary check already guarantees that.

### 4.2 The precedence rule

A resolved task counts as off-clock when the **first** matching row below applies:

| # | Source                                                                                                         | Result                                   |
| - | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| 1 | The task's own line has `#on` (if it also has `#off`, lint `clock_tag_conflict`)                                | **on-clock** (fail toward worked)        |
| 2 | The task's own line has `#off` or a deprecated alias                                                           | **off-clock**                            |
| 3 | The nearest **area or project** note on the task's root walk with a valid `offclock: true\|false`               | that value                               |
| 4 | Nothing set                                                                                                    | **on-clock**                             |

Definitions:

- **Root walk.** Start at the task's valid `[root:: NOTE]` target, else at its residence
  note. Then follow `parent:`. This is exactly `HomeResolver::home_for_task`'s walk. It
  matches the glossary: `[root::]` "attributes Pomodoro time … as if the checkbox lived
  in the named note", and off-clock is a time-attribution question. Event Tasks reside in
  daily notes, so `[root::]` is their only connection to an area. An invalid or missing
  root falls back to the daily note, which means on-clock, with the existing
  `root_field_invalid` lint.
- **Area/project notes only.** This mirrors `task_type:`. An `offclock:` on an untyped
  note (for example `dog.md`) is ignored and linted (`note_offclock_ignored`). Its tasks
  still inherit from `love` through it, because the walk passes through untyped notes.
- **Values.** Accept `true`/`false`, case-insensitive. Anything else lints once per note
  (`note_offclock_invalid`) and counts as unset, so inheritance continues upward. This
  is the `ready_cap` pattern. Do not accept `yes`/`no`/`on`/`off`: YAML 1.1 and 1.2
  disagree on them, and Obsidian's Properties UI writes a boolean checkbox anyway.
- **Unchanged:** an unresolved link is still `None` (worked), the verdict over K is
  unchanged, a mixed lineup is worked in full, and an unlinked session is worked. A tag
  on a **parent task** still does not inherit. Only notes inherit.

### 4.3 Where to compute inheritance: derive at stamp time (recommended) vs. materialize

| Option | How | Pros | Cons |
| --- | --- | --- | --- |
| **A. Derive at stamp time** (recommended) | Writers resolve the effective clock when they stamp `[t::]`/`[off::]`: start, close, sync, settle. Readers only read the stamp. | Nothing new is stored. Takes effect immediately. A task moved to another note is right on its next session. Fits the "writers decide, closed rows are history" decision. | Every writer needs the note chain: Rust has it (`HomeResolver`), and the JS mirror exists. |
| B. Reconcile writes a derived tag on every open task in an off-clock subtree (like `#prj_is_blocked`) | Rust is the only implementation. Other engines read the proxy tag. | One implementation. | Tag noise on dozens of love tasks. Can't tell an inherited `#off` from an authored one, so `#on` semantics get murky. Stale for up to 15 minutes after a move. The `#prj_is_blocked` precedent exists because Dataview needs block state; here the ledger stamp `[off::]` is already the Dataview-visible fact, so no proxy is needed. |
| C. gcal sync writes `#off` on rows whose chosen root is off-clock | Event rows describe themselves. | Simple for events. | Doesn't cover ordinary tasks, so option A is still required. Puts derived state into the Google-owned badge span. Goes stale when you hand-edit `[root::]`. |

**Implementation sketch for A (bob-cli):**

- New `src/native/clock_tag.rs` (or inside `event_task.rs`):
  `enum ClockTag { Off { deprecated: Option<&'static str> }, On, None, Conflict }`,
  `fn line_clock_tag(line) -> ClockTag`, plus one spelling table. Delete the five
  hard-coded lists.
- `NoteFacts` gains `off_clock: Option<NoteOffClock>` (`True`/`False`/`Invalid(raw)`).
  `Home` gains `off_clock: Option<(bool, PathBuf)>`: the nearest explicit value and
  which note set it. Compute it in `resolve_note`, where the chain is already built.
- `fn effective_off_clock(tag: ClockTag, home: Option<&Home>) -> (bool, ClockSource)`,
  where `ClockSource = Tag | OnTag | Note(path) | Default`.
- `EventTask`/`EventNoteRow` keep `clock_tag` from the line. Add **one enrichment
  pass**, `apply_note_clock(&mut [EventTask], day_path, &mut HomeResolver)`, that
  overwrites `off_clock` with the effective value at every entry point that has vault
  access: capture start/close, the agenda, gcal plan, reconcile settle, and stats. Code
  downstream of those entry points (event runs, clustering, settling) then keeps reading
  `event.off_clock` unchanged. Entry points without vault access keep tag-only
  semantics, which fails toward worked.
- Ordinary-task facts (`clock_fact_from_task`, `linked_tasks.rs`, `stats/homes.rs`)
  call `effective_off_clock(line_clock_tag(line), resolver.home_for_task(path, line_no,
  line))`.

### 4.4 gcal sync and list

1. **Parse.** `model.rs` produces `clock_tag: ClockTag` from title tokens and
   description directive lines. Add `#on` to `is_directive_token`, so a line like
   `@love #on` routes and overrides. Strip `#on` from displayed titles as well. Record
   every deprecated spelling that was seen, and where (title or description).
2. **Render** (`render.rs`). Write ` #off` or ` #on` for an explicit tag, and nothing
   otherwise. `lifecycle.rs` `split_trailing_google_run` must accept `#off`, `#on`, and
   the aliases. Rows written as `#offclock` that are untouched **migrate in place** on
   the next sync, because their title and badge spans still match the journal. This is
   the same mechanism that carried rows from `#untracked` to `#offclock`.
3. **Plan with the effective clock.** Past closed clusters (`plan.rs:1645`), the created
   running MEET (`:1725`), and cluster grouping (`:1985`) use the effective value: tag
   first, then the **chosen root's** chain for new rows, or the **row's current
   `[root::]`** for existing rows, since your root edits win.
4. **Flip reports** (`plan.rs:530-565`). Compare the explicit tags (tri-state) of the
   vault row and Google, not effective booleans. Otherwise every untagged row in a
   love-routed day looks like a flip. The copy changes `#offclock` to `#off`, and an
   `#on` variant is added.
5. **Deprecation warning** (as requested). Emit one line per event per run:

   ```text
   warning: Swings!: #offclock is deprecated in Google Calendar; write #off (or drop it — @abby is already off the clock via love.md)
   ```

   The parenthetical appears only when the effective clock would be off without the
   tag. This tells you that for love-routed events the best fix is deleting the tag,
   not renaming it. JSON keeps `warnings[]` (the existing contract) and adds
   `deprecations: [{event_id, title, token, replacement: "#off", where}]`. Recurring
   events will repeat daily until you edit Google, which is the point of a deprecation
   warning.
6. **`#on` + `#off` on the same Google event** warns `clock_tag_conflict` and is treated
   as `#on`, failing toward worked.
7. **`bob gcal list`** prints the same deprecation warnings. List is where you go to
   inspect events. `list -f json` adds `deprecations` plus
   `clock_source: "tag"|"on_tag"|"note"|"default"` and `clock_note: "love.md"`.
   `off_clock` now means the **effective** clock, and `task · MEET · off-clock` appears
   for inherited rows too.
8. **Optional:** `bob gcal doctor` lists upcoming events that use deprecated tags. The
   ledger-tools auto-sync shows one Notice per day when `deprecations` is non-empty.
   Without that, the warnings never reach Obsidian (§1.4).

### 4.5 Capture, agenda, and the Mac

- `capture-pomodoros --tasks` JSON (`events.rows[].off_clock`, `items[].event.off_clock`)
  must report the **effective** value. Bob Mac Capture is a thin client
  (`decisions:mac-capture-is-a-thin-client`) that decodes `off_clock` and parses no tags
  (verified: the only `#untracked` strings in the Mac repo are test fixtures and
  rendered row text). So **the Mac needs no code change**; refreshing the fixtures is
  cosmetic.
- Start and close summaries name the source when it is inherited:
  `started LUNCH 1200-1300 (60m · off-clock via love)`. The `pomodoro_clock_mixed`
  notice is unchanged.

### 4.6 Settling: inherited events will auto-complete

`settle.rs:85` settles every open, ended, off-clock Event Task still parked under an
unstarted placeholder. It writes a closed `[off:: Nm]` MEET and **completes the row**
(`settled_status = done`). Once this rule uses the effective clock, every ended
`@love`/`@abby`/`@family` event you didn't start is recorded as off-clock time and
marked done, including ones you skipped. Today only explicitly tagged events behave
this way.

**Recommendation:** settle inherited events too. That's the point of off-clock life
"needing no gestures", and a split rule ("only tagged events settle") would be a
surprising inconsistency. Record it as an explicit decision, because it expands a cost
the `ended-off-clock-events-settle` record already accepts ("the calendar is not proof
of attendance"). The escape hatch is unchanged: cancel the row before it ends.

### 4.7 History, drift, and no re-clocking

- Closed rows stay frozen (`decisions:off-clock-pomodoros-count-apart`). Setting
  `offclock: true` on love never rewrites a stamp.
- Stats `clock_drift` (`stats/homes.rs:798`) must use the **same** effective rule, or
  it will disagree with the writers. Past love-rooted `[t::]` sessions will then show as
  drift. That's a handful, given 13 worked minutes in the last year. Document that
  toggling a note's `offclock:` surfaces as drift for earlier sessions, by design.
- **No re-clock migration is needed.** The data shows love time was almost never
  Pomodoro'd on the work clock.

### 4.8 Capture edge `#off` / `#on` (an adjustment, see §6)

Today `Walk the dog #off` is refused (§1.5). Options:

- (a) Leave it. Use `\#off`, a mid-line tag, or route `@love` and let inheritance do the
  work. Zero grammar change.
- (b) **Reserve `#off` and `#on`** (case-insensitive) as clock tags at item edges. They
  stay on the task line instead of becoming type markers, and `bob types` refuses `OFF`
  and `ON` as type names. This is a small, explicit exception to
  `decisions:capture-sigils-say-where-what-how` ("free `#` names a type"), so it needs a
  short decision record.

I recommend (b), in its own small phase. The whole point of `#off` is that it's quick
to type, and capture is where you create most tasks. If you'd rather not touch the
capture grammar now, (a) is acceptable, because routing to a love area covers the main
use case.

### 4.9 Plugins (bob-plugins)

- **One spelling table** in each plugin, mirroring Rust: ledger-tools
  `035-meet-event-run.js` and `291-plugin-gcal-events.js`; cycler
  `062-pomodoro-clock.js`.
- **Inheritance.** Extend `pomodoroHomeResolve` (`142-pomodoro-home-chips.js:487`) to
  read `frontmatter.offclock` along the chain it already walks. Accept boolean
  `true`/`false` and the strings `"true"`/`"false"`. Export
  `taskEffectiveOffClock(lineText, file)` on the ledger-tools `api`.
  - `036-pomodoro-clock.js` (`pomodoroClockLinkFacts`) and cycler
    `planPomodoroCloseClock` call it.
  - If the API is missing (ledger-tools disabled), the cycler falls back to tag-only,
    which fails toward worked.
- **Painter.** Draw inherited off-clock Event Tasks with the dashed chip and the
  tooltip "Off-clock · from love". Tagged rows keep their tag highlight, and `#on` gets
  a neutral "on the clock (override)" tooltip.
- **Vectors.** Extend `tests/fixtures/pomodoro_clock/vectors.json` with notes that
  carry frontmatter. Cases:
  - `love.md` with `offclock: true`;
  - `abby.md` as its child area;
  - `fun.md` with `offclock: false`;
  - an untyped `dog.md`;
  - a `#on` task;
  - an `#on`+`#off` conflict;
  - an Event Task with `[root:: abby]`;
  - an invalid `[root::]`;
  - `offclock: maybe`.

  Copy the vectors byte-for-byte into both plugins with README pins, as the epic does.
- **Sequencing.** `bob-cli-fl.6` (plugins stats clock) is still IN_PROGRESS in
  bob-ledger-tools. Start the plugin phase after it lands, because both rebuild
  ledger-tools' generated output.

### 4.10 Vault migration (the 4 rows) and love.md

- **Order matters.** Old bob binaries and old plugins don't recognize `#off`: they
  would read a migrated row as on-clock, and old sync would see the badge span as your
  edit and report `kept_edit`. bob-cli ships only on the daily release train
  (`decisions:bob-cli-releases-ride-a-daily-train`). So:
  1. ship bob-cli and run `bob plugins sync`;
  2. confirm athena, apollo, and the Mac run the new bob;
  3. then rewrite.
- **Scope of the rewrite.** Only Event Task rows inside `## Events` of canonical daily
  notes, using the scanner's own token rules. Today that is exactly the four rows in
  §2. Exclude `.bob/ref-sources/**` (write-once), `_conflicts/**`, and prose in closed
  tasks (`bob.md:374`). A 20-line scripted rewrite plus a `git diff` review is enough.
  A permanent `bob` migrate command isn't justified for 4 rows.
- **Rename, don't delete.** Rewrite to `#off`, as you asked. Don't strip the tags just
  because love now covers them: those badge spans mirror Google, and Google still says
  `#offclock`. A row with no tag would read as your edit (`kept_edit`) until Google
  changes. After you remove the tags in Google, untouched rows (the open Lincoln Park
  row) lose them in place on the next sync.
- **`offclock: true` in `love.md`** is inert until bob understands it, so it can land
  any time. Put it in the frontmatter next to `color: yellow`.
- **After the deprecation warnings fire:** edit the recurring Google events. For
  `@love`/`@abby`/`@family` events, delete the tag rather than renaming it.

### 4.11 Memory and docs

- **Decision record** (via `/sase_memory_write`, authorized in the plan): add
  `decisions:off-clock-follows-tag-then-note` (title along the lines of "Off-Clock
  Follows A Task Tag, Then The Nearest Note Default"). It **partly supersedes**
  `off-clock-pomodoros-count-apart` (the "own line has the tag" clause) and records:
  - the precedence table;
  - the walk definition;
  - stamp-time-only evaluation;
  - the deprecated spellings;
  - the settled vocabulary.

  If you take §4.6 and §4.8, add one more record each, or a clause in this one, for
  settle scope and the capture reserved tags.
- **Glossary.** Update `off-clock-pomodoro` and `event-task` (`#offclock` → `#off`, add
  `#on` and `offclock:`). Consider a sentence each in `area-note` and `project-note`.
- **Docs.**
  - `docs/reference/vault-format.md`: the tag table, plus `offclock:` under Area and
    Project notes beside `ready_cap`/`task_refresh`.
  - `docs/capture.md`: "Which clock a session is on", plus the edge tags if §4.8 lands.
  - `docs/gcal.md`: "Off-clock events", Root selection, the JSON output, and a
    deprecation note.
  - `docs/task-status-hooks.md`: the settle scope.
  - `docs/stats.md`: the drift explanation.
  - Then run `just docs-gen` / `just docs-check`.

## 5. Alternatives considered and rejected

- **A stats-only area filter** (Worked excludes `in: [love]`). This would only change
  stats. The Day strip, `bob pomodoro --worked`, the agenda summary, the menu bar, home
  chips, and settling all key off the stamped clock. The `[off::]` stamp is the right
  lever.
- **`clock: off|on` frontmatter.** YAML 1.1 parses `on`/`off` as booleans, and `clock:`
  already means `worked|off-clock|total` on stats metrics. `offclock: true|false` is
  unambiguous and shows as a checkbox in Obsidian Properties. (`off_clock:` would match
  the snake_case JSON key, but the difference is cosmetic, so keep your `offclock:`.)
- **Keeping `#offclock` canonical and adding `#off` as an alias.** This misses the
  phone-typing benefit for the canonical form. Since nothing has shipped, switch now.
- **Re-clocking past love sessions.** That's 13 minutes in a year, and it contradicts
  frozen history.
- **Session-level `#off` on the Pomodoro headline** (overriding the link rule). It's
  plausible for unlinked sessions, but nobody asked for it and it adds a third source of
  truth. Not now.
- **Materialized tags** (options B and C in §4.3).

## 6. Adjustments to the requirements (clearly called out)

| # | Adjustment | Why |
| - | - | - |
| A1 | **Deprecate `#off-clock` too**, not only `#offclock` and `#untracked`. | It is the third alias today. Leaving it silently accepted is inconsistent and keeps a spelling you never type. |
| A2 | **Deprecation warnings also appear in `bob gcal list`**, plus a structured `deprecations[]` in both JSON outputs (and optionally a once-a-day Obsidian Notice). | The Obsidian auto-sync hides warnings today, and list is the inspection surface. |
| A3 | **The warning suggests deleting the tag when the root's area is already off-clock.** | For love-routed events the right fix is removal, not renaming. |
| A4 | **Inheritance starts at the task's `[root::]`** (else residence) and honors `offclock:` **only on area/project notes**, walking through untyped notes. | "Belongs to" needs a precise definition. This matches root-parent and `task_type:` semantics, and Event Tasks only connect to areas through `[root::]`. |
| A5 | **`#on` beats `#off` on the same line**, with a lint. | Fail toward worked, like every other ambiguity in the rule. |
| A6 | **Area-inherited off-clock events auto-settle and complete** (recommended; needs your explicit yes). | It is the consistent reading, but it widens an accepted cost. |
| A7 | **Capture accepts edge `#off`/`#on` as tags** (recommended; needs your yes; separate phase). | Otherwise `Walk the dog #off` is refused today. |
| A8 | **The vault rewrite waits until all hosts run the new code**, and is scoped to Event Task rows. Ref-sources, `_conflicts/`, and closed-task prose stay untouched. | This avoids old readers flipping rows to on-clock, and it respects write-once sources. |
| A9 | **Rename only the tag.** The concept, the `[off::]` key, and the `off_clock` JSON keys keep their names. | This avoids a third vocabulary sweep across three repos. |

## 7. Risks

- **JS/Rust divergence on inheritance.** Mitigated by the shared vectors with
  frontmatter.
- **`off_clock` JSON meaning broadens** from "has a tag" to "effective clock". Every
  client wants the effective value, and the key hasn't shipped in a release. Still, mark
  the commit `!` if you're unsure (release-train rule), and add `clock_source` so clients
  can explain the value.
- **False positives from short tags.** Today there are zero in the vault. Prose such as
  `bob.md:374` already shows that any standalone tag in task text counts, and the docs
  should say so.
- **A missing root note** (for example the old `@dad` route: `dad.md` does not exist)
  silently means no inheritance. The existing `root_field_invalid` lint covers rows. If
  you want, the gcal warning for an unresolved route could mention that it also blocks
  off-clock inheritance.

## 8. Recommended solution

Create **one new epic** (do not reopen `bob-cli-fl`) with these phases:

1. **bob-cli: clock tags and note inheritance (core).**
   - Add the `ClockTag` spelling table (`#off` canonical, `#on`, three deprecated
     aliases) and delete the hard-coded lists.
   - `NoteFacts`/`Home` gain `offclock:` with nearest-explicit-wins, area/project-only,
     and the `note_offclock_invalid` / `note_offclock_ignored` lints.
   - Add `effective_off_clock(tag, home) -> (bool, ClockSource)` and the Event Task
     enrichment pass.
   - Wire it into capture start/close/link edits, the agenda JSON, the start/close
     summaries ("via love"), reconcile settling (decision A6), and stats drift.
   - Extend the `pomodoro_clock` vectors with frontmatter cases.
   - Docs (vault-format, capture, task-status-hooks, stats), the new decision record,
     and the glossary updates.
2. **bob-cli: gcal `#off`/`#on` and deprecations.**
   - Tri-state parsing in titles and description directives, with `#on` added.
   - Render the explicit tag only, with in-place migration of untouched rows.
   - Effective clock for clusters and created MEETs, from the chosen or current root.
   - Tri-state flip reports.
   - Deprecation warnings in sync and list (A1–A3), with `deprecations[]`,
     `clock_source`, and `clock_note` in JSON.
   - Docs (`docs/gcal.md`) and `tests/gcal_lifecycle.rs` / `tests/gcal_sync.rs` cases:
     an alias migrates to `#off`; `#on` overrides an off-clock root; an untagged
     `@love` event makes an off-clock past cluster; a deprecation warning fires once
     per event per run.
3. **bob-cli: capture edge `#off`/`#on`** (A7; optional, only if you approve). Reserve
   the slugs, refuse `OFF`/`ON` as types, and write a short decision record.
4. **bob-plugins: spelling table, inheritance, and painter.**
   - Ledger-tools chain walker plus the exported `taskEffectiveOffClock`; the cycler
     calls it for closes.
   - The painter handles inherited, `#off`, and `#on` rows.
   - Copy the vectors byte-for-byte.
   - Optional once-a-day deprecation Notice.
   - Starts after `bob-cli-fl.6` lands. Ship with `npm test`, `build:check`, `validate`,
     `docs:check`, then `bob plugins sync`.
5. **Vault rollout** (a manual checklist, not code):
   1. Add `offclock: true` to `~/bob/love.md`. This can happen any time, because it is
      inert until phase 1 ships.
   2. After phases 1, 2, and 4 are live on athena, apollo, and the Mac, rewrite the
      four `#offclock` Event Task rows to `#off` (§4.10).
   3. Run `bob gcal list` for the next week and fix the Google events it names. For
      events routed to love, delete the tag.
   4. Check `bob stats -k off-clock` groups the time under `love`/`abby`/`family`.
   5. Check `bob stats` `clock_drift` shows only the expected few.

The Mac needs no phase: it reads bob's effective `off_clock`. Refresh its fixtures
opportunistically.

**Verification, end to end** (scratch vault, `BOB_NOW`, fake `BOB_GCAL_GOG`):

1. Sync `Lunch @love` with no tag. The row has no tag, `list` shows
   `task · MEET · off-clock`, and `clock_source: note`.
2. `=` on the MEET writes `[off:: 60m]`, and the summary says `off-clock via love`.
3. Sync `Planning @love #on`. The row renders `#on` and the session stamps `[t::]`.
4. Sync `Gym #offclock`. The row renders `#off` and sync warns `#offclock is
   deprecated`.
5. A task in `fun.md` with `offclock: false` stamps `[t::]`. A task in `abby.md` stamps
   `[off::]`.
6. A session linking a love task and a work task stays worked and warns
   `pomodoro_clock_mixed`.
7. An ended, unstarted `@abby` event settles on `bob task reconcile`.
8. The same vectors pass in bob-cli, bob-ledger-tools, and task-status-cycler.

# Per-note READY cap ("crowded notes"): critique, design, and recommendation

- **Researcher:** cld (one of five independent researchers; written without reading the peer reports)
- **Date:** 2026-10-01 (live vault numbers taken the same afternoon)
- **Request:** During the morning GTD review, no area or project note should hold more than N READY tasks.
  N is configurable and defaults to 5. Make violators obvious in Obsidian (toasts on keymaps, plus a badge or
  diagnostics in `dash.md` and/or the notes) and on the command line. Critique the idea, adjust the
  requirements where that is justified, and recommend a solution.
- **Existing vault task:** `bob_gtd#^prj-task-count-warn` ("Show warnings when projects contain >5 ready
  tasks!", `[*]`, linked in today's ledger). Its predecessor `^diagnostics` was closed today with the
  sub-bullet "project/area files have >=5 ready tasks!".

---

## 0. Bottom line

1. **Yes, build it, but as a *shape* limit, not a second volume limit.**
   - The global `plan.max_ready: 100` already bounds how much is ready.
   - A per-note limit bounds *where* it piles up. That is a different and more actionable signal: it names
     the exact note that needs a scope drawn or a deferral.
   - This is Shape Up's "chowder" rule: "If it gets longer than three to five items, something is fishy and
     there's probably a scope to be drawn somewhere."
   - It is also a per-swimlane WIP limit on Kanban's ready queue.
2. **The live data makes the case on its own.** At N = 5, with inboxes and recurring tasks set aside, 4 notes
   are over and 3 are exactly at the limit.
   - **65 tasks are over the limit, and 55 of them are in `sase.md` alone** (60 READY).
   - Two notes, `gkeep_inbox` (65) and `sase` (60), hold about 60% of today's ~210 READY tasks.
   - The global READY chip says "too much"; the per-note view says "here".
3. **Keep one definition, the dash's own READY, grouped by the note that contains each task.** Don't count
   raw `[ ]` checkboxes.
   - "Note READY" is the freshness-gated READY predicate (visible TODO, not Blocked, not Today, bucket not
     NEW/ROTTEN) grouped by path, minus recurring tasks, applied to area and non-terminal project notes.
   - Ctrl+Shift+M and Alt+N already **stamp freshness on the tasks they touch**, so a moved or released task
     counts as READY the moment it lands. Projections are therefore exact.
   - New captures arrive NEW and do not count until confirmed. So the moment a note actually becomes crowded
     is usually *during the morning review* (Alt+Shift+F confirming a task). That is exactly when you are
     positioned to defer or route it instead.
4. **Soft limit everywhere, consistent with every other Bob cap.** Nothing is refused, nothing is written to
   task lines or frontmatter, and everything is computed at read time.
5. **Recommended surfaces** (§9 is the full recommendation):

   | Where | What | Why |
   | --- | --- | --- |
   | CLI | **`bob ready`** (new, read-only): bar chart grouped CROWDED / FULL / ROOM; `bob ready <note>` lists one note's READY tasks; `-f json` | "Which ones, by how much", headless |
   | `bob plan` | `READY n/100 · CROWDED k` in the meter line, plus one summary lint | The daily CLI glance |
   | `dash.md` | **`CROWDED k↗` chip** after READY → `crowded.md` | "How many" |
   | `crowded.md` | A live ranked bar widget (`bob-ready-notes` block) plus the crowded notes' READY tasks | "Which ones" |
   | Each area/project note | A live **`READY 7/5` chip on the `## Tasks` heading** | In-place awareness |
   | Toasts | Destination chip on **Ctrl+Shift+M** and **Alt+N**; progress chip on **Ctrl+Shift+P**; plus an **active-note watcher** for every other gesture (Alt+F review stamps, cycler, hand edits) | Exactly when it happens, including positive "✓ back to 5/5" feedback |
   | Ctrl+Shift+M picker | Each destination row shows its `READY n/5` | Prevention beats notification |

6. **Requirement changes I'm making** are called out in §4. The biggest:
   - exempt inbox notes, by explicit `ready_cap: off` frontmatter;
   - don't count recurring tasks;
   - add a per-note `ready_cap:` override;
   - add an "at the limit" (FULL) state;
   - celebrate fixes, not just violations;
   - add prevention in the move picker;
   - add a native Rust READY evaluator, which reverses `docs/plan.md`'s "no native READY count" stance and
     needs a new decision record.

---

## 1. What already exists (grounding)

### 1.1 Definitions and contracts

- **READY** (`docs/plan.md` "READY backlog"; decision `ready-is-freshness-gated`):
  - It is the visible TODO pool minus the NEW and ROTTEN freshness buckets.
  - It excludes Today, `#hide`, `_templates`/`_conflicts`, `dash.md` itself, dependency-blocked tasks, and
    future-scheduled tasks.
  - It is computed **only in JavaScript** (bob-ledger-tools `readyBudget()`, top-level api v3, freshness
    namespace v3). `docs/plan.md` states that `bob plan` has no READY count.
  - The cap is `plan.max_ready: 100`, a soft limit: red only on strict excess.
- **Buckets** (`docs/freshness.md` §4): `new` (never stamped), `rotten` (resurfaced or expired), or null.
  READY uses `bucket !== "new" && bucket !== "rotten"`.
- **Who stamps** (`docs/freshness.md` §5):
  - Ctrl+Shift+M stamps "each open task moved".
  - Alt+N commit and release stamp.
  - Ctrl+Shift+P priority/scheduled/lane rows stamp.
  - Alt+F and Alt+Shift+F stamp.
  - Creation never stamps (capture, gkeep, Ctrl+Shift+] promotion).
  - This is the key fact that makes keymap projections exact (§5.7).
- **Lane notices** already set the pattern for budget suffixes.
  - Example: `→ Ready · 2 tasks · unlinked 1 from today · NEXT 11/15 · PENDING 7/10`, plus
    `🔴 · prune at the weekly review` when over.
  - Code: `buildLaneToggleNotice` / `readLaneBudgets` in bob-navigation-hotkeys `main.js` ~15805–15930.
  - Budgets are read synchronously *before* the write and adjusted by the change count, because the Tasks
    cache lags behind the write.

### 1.2 Per-note things that already exist

| Thing | Where | Why it doesn't already solve this |
| --- | --- | --- |
| `bob projects list` OPEN / SHOWN columns | `src/native/projects` | SHOWN counts `[ ]`+`[*]`+`[/]`, isn't freshness-gated, and areas aren't listed |
| Hooks badge row `⚪ 11 open · 🔵 1 next/wip · 🔴 2 blocked · 🟢 8 done/canceled` | written under `## Tasks` by `bob task-status-hooks` (`task_status_groups`) | A *written snapshot* ("can be stale until the next hooks run"); counts the `[ ]` intake, not gated READY; no cap |
| `task_count` / `open_task_count` frontmatter | bob-project-tasks plugin | Projects only, ungated, written state |
| dash READY section grouped by file | `dash.md` frontmatter `TQ_extra_instructions: group by path` | Grouped, but no counts and no limit on the headings |
| `isAreaOrProjectNote(file)` | bob-navigation-hotkeys `main.js` ~36059 | A reusable type check for the plugin side |
| Ctrl+Shift+M destinations | `collectTaskMoveDestinations` ~16864: areas plus wip/waiting projects | The picker shows no counts today |
| Notice cards with chips (`.bob-nh-notice`, tones `warn/ok/info/muted`) | nav `buildPriorityNoticeModel`, `buildCancelNoticeModel`, styles.css 1135–1358 | No red tone yet; Ctrl+Shift+M still uses a plain text notice |
| Rust pieces: `dataview::READY_QUERY`, Today membership, freshness `evaluate` and bucket, frontmatter parsing | `src/native/{dataview,freshness,plan_budget,projects}` | Everything a native note-READY evaluator needs already exists; it just isn't assembled |

The Rust side is close. `freshness::scan` already queries `READY_QUERY` rows, attaches Today membership and
each note's `task_refresh`, and evaluates buckets. A native per-note READY count is "those rows, minus
Today, minus bucket new/rotten, minus `dash.md`, grouped by path."

---

## 2. Live numbers (vault at 2026-10-01 afternoon)

**Method.**
- `bob query --format json --origin dash.md --tasks` with the `READY_QUERY` filters gave the visible TODO
  pool: 211 tasks in 29 files.
- Today keys came from `bob plan -f json`, and NEW/ROTTEN buckets from `bob freshness list -f json`.
- Today's seed stamped almost everything (`✓ 393 today`), so only 1 task is NEW and 0 are ROTTEN. READY ≈ 210.
- `isRecurring` flags recurring tasks.

| Note | Type | READY | Recurring among them | At N = 5 |
| --- | --- | ---: | ---: | --- |
| `gkeep_inbox` | area (parent `[[inbox]]`) | 65 | 0 | inbox, should be exempt |
| `sase` | project | 60 | 0 | **CROWDED +55** |
| `sase_remote` | project | 11 | 0 | **CROWDED +6** |
| `sase_pager` | project | 7 | 0 | **CROWDED +2** |
| `sase_usage` | project | 7 | 0 | **CROWDED +2** |
| `gtd_daily` | area | 7 | 7 | 0 once recurring is excluded |
| `cash` | area | 6 | 1 | FULL (5) once recurring is excluded |
| `bob` | project | 5 | 0 | FULL |
| `sase_bug_bash` | project | 5 | 0 | FULL |
| `dev`, `sase_memory` | area, project | 4 each | 0 | ROOM |
| 17 more notes | — | 1–3 | `recur`: 3 of 3 | ROOM |

**Sensitivity**, excluding inboxes and recurring tasks: 134 READY in 26 capped notes.

| N | Crowded | Full | Excess over the cap | Crowded notes |
| ---: | ---: | ---: | ---: | --- |
| 3 | 9 | 2 | 81 | sase, sase_remote, sase_pager, sase_usage, bob, cash, sase_bug_bash, dev, sase_memory |
| **5** | **4** | **3** | **65** | sase, sase_remote, sase_pager, sase_usage |
| 7 | 2 | 2 | 57 | sase, sase_remote |
| 10 | 2 | 0 | 51 | sase, sase_remote |

**Takeaways.**
- N = 5 is a good default. It flags a manageable 4 notes, and the 3 FULL notes are the ones a careless move
  would tip over. N = 3 would flag a third of the notes, which reads as noise.
- **`sase.md` is the elephant**: one "project" with 60 READY tasks and roughly 40 `sase_*` child projects. It
  behaves like an area whose `## Tasks` is a chowder list. Expect the CROWDED chip to stay at ≥ 1 until one
  dedicated triage session routes or defers those tasks. That is the feature working, but it is also the
  main alarm-fatigue risk (§3.2).
- Without inbox and recurring exemptions, `gkeep_inbox` (65), `gtd_daily` (7, all recurring) and `cash`
  would be permanently red for reasons the remedies (split or defer) can't address.
- A related fact for the optional floor (§4, A11): `bob projects list` shows **17 of 41 active projects with
  SHOWN = 0**, meaning nothing currently actionable (everything deferred, blocked, or hidden). A naive
  "stalled project" alarm would be noisier than the cap itself.

---

## 3. Critique: is this a good idea?

### 3.1 Why it is good

- **It turns a vague signal into a located one.**
  - READY 210/100 is red, but the fix it implies is "do less," which can't be acted on directly.
  - "`sase_remote` 11/5" implies a concrete move: draw a scope (create `sase_remote_fleet_ux` and Ctrl+Shift+M
    four tasks into it), or roll two tasks with Ctrl+Shift+P.
- **It is backed by established practice.**
  - *Shape Up*, "Map the Scopes": the chowder list for loose tasks "gets longer than three to five items,
    something is fishy." A scope that gets "too big, with too many tasks … becomes like its own project with
    all the faults of a long master to-do list." The proposed default of 5 is literally the top of Singer's
    range.
  - *Kanban*: WIP limits are set per column, per swimlane, per person, or per class of service. A low limit
    on a queue is the signal that drives replenishment decisions. A per-note READY limit is a per-swimlane
    limit on the ready queue.
  - *GTD*: the weekly review checks projects "one by one, ensuring at least one current action item on each."
    That is a floor, not a ceiling. GTD itself has no ceiling, which is why this is a deliberate Bob-specific
    choice. It fits Bob, because READY here means a *pullable, confirmed* backlog, not "all next actions."
- **It complements the global cap rather than duplicating it.**
  - 52 capped notes × 5 = 260, which is more than `max_ready: 100`.
  - So the per-note cap only bounds concentration; the global cap still bounds volume.
  - Gaming one (spreading tasks thin across junk-drawer projects) shows up in the other.
- **It is cheap and low-risk with this architecture.** Read-time evaluation, one predicate, and two engines
  with shared vectors are the established Bob pattern. Every input already exists in both languages.
- **It strengthens the morning ritual at the right step.** Confirming NEW tasks is the main inflow into a
  note's READY (§5.7). A toast at that keystroke ("`sase_pager` is crowded · READY 6/5") arrives while the
  task is under the cursor and Ctrl+Shift+P or Ctrl+Shift+M is one chord away.

### 3.2 Risks and how the design handles each

| Risk | Why it is real | Mitigation in this design |
| --- | --- | --- |
| **Chronic red from one note** (`sase` 60/5) causes alarm fatigue, and the chip becomes wallpaper | It will take at least one dedicated session to fix | Show the **excess** (`+55`) so progress is visible. Add **positive feedback** chips (`sase READY 58/5 ↓2`, `✓ back to 5/5`). Allow an honest, visible **`ready_cap:` override** for a deliberate exception. Recommend a one-time triage session before the trial. Toasts are throttled. |
| **Gaming by deferral**: rolling P-levels just to get under the cap | Rolls push tasks into Blocked/hidden | That *is* deprioritizing, the remedy you named. A deferral returns RESURFACED (rotten bucket, not READY) and must be re-confirmed, at which point the watcher asks again. The decay ladder eventually cancels repeat rolls. |
| **Gaming by junk-drawer projects** (`sase_misc_2`) | Splitting is the other remedy | The global READY cap still bounds volume. `bob ready` shows the parent of each note so a pile of thin siblings is visible. Shape Up's "name isn't unique to the project, like 'bugs'" warning goes in the docs, not in code. |
| **Freshness gating hides pressure**: NEW/ROTTEN tasks in a note aren't counted | Skipping review lowers READY (a documented cost of `ready-is-freshness-gated`) | Every surface shows a muted **`+k in review`** next to the count. Review clears NEW then ROTTEN *before* the crowded check in the ritual. |
| **Two engines drift** (Rust and JS) | They already exist twice for Today, freshness, and lanes | Shared conformance vectors N1–N10 (§5.1), copied verbatim into the ledger-tools tests, the same as Today T1–T9 |
| **Toast spam during review**: confirming ten NEW tasks in one crowded note | The watcher sees ten increments | A crossing (≤cap → >cap) always toasts. Further growth while over is throttled to one per note per 15 minutes. Gestures that already show a chip *claim* the note, so there's no double toast. |
| **Tasks cache lag**: a toast computed from a stale cache | The cache updates after save and parse | Gesture chips compute *before-count + exact delta* (the existing `readLaneBudgets` pattern). The watcher runs after the post-write cache update. |
| **Performance** | `bob plan` takes 2.1 s and `bob freshness list` 3.3 s; ledger-tools re-reads `config.yml` on every caps call | Native: one shared rich-task scan, no extra `OPEN_QUERY` or full scan. JS: one O(tasks) pass memoized on the existing freshness memo keys. Cache `loadPlanCaps` by mtime like the freshness config. |

### 3.3 Verdict

The idea is sound and the timing is right: READY just became a confirmed backlog, so asking "where is it
piling up?" is the natural next question. I'd change two framing details.

- **Make the unit "a note," not "a project."** Areas are included by your own requirement. "Note READY" also
  matches how every other Bob count is keyed: by residence, like `task_refresh`.
- **Treat "at the limit" as its own visible state.** Your keymap requirement ("moving a task to a note that
  already has ≥ N") is about the FULL state. Make it visible before the move, not only after.

---

## 4. Requirement adjustments (explicitly called out)

| # | Original requirement | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | "ready tasks" | **ADJ:** count the dash's freshness-gated **READY** predicate, grouped by the note that contains the task. Show `+k in review` (NEW + ROTTEN in that note) beside it. | It matches what you see in dash's READY section, which is already grouped by path. One predicate, one meaning. Moves and releases stamp, so projections stay exact. |
| A2 | "area/project note file" | **ADJ:** scope is notes whose frontmatter `type` is `[[area]]` or a non-terminal `[[project]]` (the same set `bob capture-targets` and Ctrl+Shift+M offer). Daily notes and untyped notes aren't capped; their READY tasks are reported as one "outside capped notes" total so nothing disappears. | These are the notes you route tasks into. A daily note's READY is a different problem. |
| A3 | — | **ADJ:** inbox notes are exempt through an explicit frontmatter **`ready_cap: off`**, set once on `gkeep_inbox` and `inbox`. (`mac_inbox` has no type, so it is already out of scope.) | An inbox is unprocessed by definition, so "split or defer" doesn't apply. An explicit property beats a name or parent heuristic: it survives renames and is visible in Properties. |
| A4 | — | **ADJ:** **recurring tasks don't count** toward a note's READY (shown as `↻ k`). | Routines (`gtd_daily` 7, `recur` 3) can't be split into a project, and deferring them is wrong. Freshness already treats recurring tasks as out of scope. |
| A5 | N configurable, default 5 | Config `plan.max_ready_per_note: 5` in `~/.config/bob/config.yml`. **ADJ:** plus a per-note override `ready_cap: <1–999 \| off>` in frontmatter, resolved by residence like `task_refresh`. Invalid values are linted and fall back to the default. | Some areas are legitimately bigger. An override is an honest, visible exception rather than a silent exemption. |
| A6 | "more than N" is a violation; warn when moving into a note that "already has ≥ N" | Kept as stated and made precise: **CROWDED** when `count > cap` (red), **FULL** when `count == cap` (amber), **ROOM** when `count < cap` (muted). Exactly at the limit is fine, as with every Bob cap. | The FULL state is what makes your "≥ N before the move" requirement visible *before* the move. |
| A7 | Toast when a keymap would cause a violation | **ADJ:** toasts are soft and never refuse. They fire on the gesture that pushes a note over **and** they confirm progress (`↓1`, `✓ back to 5/5`) when a gesture brings a crowded note down. | Every Bob cap is soft. Positive feedback makes the Ctrl+Shift+P remedy loop satisfying instead of nagging. |
| A8 | — | **ADJ: prevention.** The Ctrl+Shift+M destination picker shows each note's `READY n/5` (amber when FULL, red when CROWDED). | Choosing a non-full destination beats being told afterwards. |
| A9 | Badge in dash and/or notes | **ADJ:** both, each with a distinct job. dash gets a `CROWDED k↗` chip linking to a `crowded.md` view (how many / which ones). Each note gets a live chip on its `## Tasks` heading (this note). The hooks-written badge row is left alone. | Separate live counts from written snapshots so two numbers never sit side by side and disagree. |
| A10 | CLI view | **ADJ:** a new read-only `bob ready` command, plus a one-line summary in `bob plan`. **This adds a native READY evaluator in Rust**, reversing "`bob plan` has no READY count." It needs a new decision record. | A plugin-free surface that needs gating is the documented reopen condition of `ready-is-freshness-gated`. |
| A11 | — | **Optional, informational:** `bob ready --all` lists **IDLE** active projects (no READY, NEXT, or PENDING). Never a chip or toast. | GTD's floor rule. Kept informational because 17 of 41 active projects are idle today, often legitimately parked. |
| A12 | — | **Out of scope:** capture-time enforcement. `bob capture` / Mac Capture may show an advisory "`sase_remote` already has 11/5 READY" on the destination, but a new capture is NEW and doesn't count until confirmed. | Keeps capture fast (5 ms dry runs per the Mac Capture decision) and honest about what counts. |

---

## 5. Design

### 5.1 The contract: "note READY"

Add a section **"READY per note"** to `docs/plan.md`, next to "READY backlog".

```text
note_ready(t)  = READY(t)                       # docs/plan.md READY backlog, unchanged:
                                                #   TODO ∧ lane-visible ∧ ¬Today ∧ bucket ∉ {new, rotten}
                                                #   ∧ path ≠ dash.md
                 ∧ ¬recurring(t)                # A4
note(t)        = the vault path of the file containing t (residence, not parent links)
capped(n)      = type(n) ∈ {area, project} ∧ status(n) ∉ {done, canceled} ∧ ¬daily(n)
cap(n)         = frontmatter ready_cap (1–999) | off  →  exempt
                 else plan.max_ready_per_note  (default 5)
count(n)       = |{ t : note(t) = n ∧ note_ready(t) }|
review(n)      = |{ t : note(t) = n ∧ TODO ∧ lane-visible ∧ ¬Today ∧ bucket ∈ {new, rotten} ∧ ¬recurring }|
state(n)       = exempt   if cap(n) = off
               | crowded  if count(n) > cap(n)
               | full     if count(n) = cap(n)
               | room     otherwise
crowded_total  = |{ n : capped(n) ∧ state(n) = crowded }|
excess         = Σ max(0, count(n) − cap(n))
```

**Conformance vectors** (shared Rust ⇄ bob-ledger-tools, copied verbatim like Today T1–T9):

| # | Fixture | Expected |
| --- | --- | --- |
| N1 | Project with 6 stamped `[ ]` tasks, default cap | `count 6, cap 5, crowded, excess 1` |
| N2 | 5 stamped tasks | `full`, not crowded, no lint |
| N3 | `[ ]` with `#hide`, future `scheduled`, `[?]`, dependency-blocked `[ ]`, `[*]`, `[/]`, `[x]`, `[-]` | none count |
| N4 | One unstamped task (NEW), one stamped 8 days ago at interval 7 (ROTTEN), one RESURFACED | `count 0, review 3` |
| N5 | A `[ ]` task with a dedicated Task Link under today's open Pomodoro | not counted (Today) |
| N6 | `[repeat:: every day]` and `🔁` tasks | not counted; `recurring 2` reported |
| N7 | READY tasks in `2026/20261001.md`, an untyped note, `_templates/x.md`, and `dash.md` | absent from the per-note list; the first two go to `outside` |
| N8 | `ready_cap: 8` / `ready_cap: off` / `ready_cap: 0` / `ready_cap: lots` | cap 8 (source `note`) / exempt / lint `note_ready_cap_invalid` and default / same |
| N9 | A parent `[ ]` task with 2 nested child `[ ]` tasks, all stamped | `count 3` (each task line counts) |
| N10 | A `status: done` project with 2 stamped `[ ]` tasks | not capped; listed under a lint `note_ready_in_terminal_project` |

N9 is deliberate. A task with many child tasks is exactly what Alt+Ctrl+Shift+N ("Create project note from
task") exists to promote, so counting the children nudges you toward it.

### 5.2 Config

```yaml
plan:
  max_ready: 100           # soft limit for dashboard READY tasks, excluding Today
  max_ready_per_note: 5    # soft limit per area/project note; `ready_cap:` frontmatter overrides (docs/plan.md)
```

- Rust `PlanConfig` and ledger-tools `coercePlanCaps` both gain the key: an integer ≥ 1, default 5.
- Invalid values follow the existing plan-config rules: `bob plan` / `bob ready` exit 2; every other surface
  falls back to defaults and says so once.
- Frontmatter, by residence:

  ```yaml
  ready_cap: 8      # this note may hold 8 READY tasks
  ready_cap: off    # exempt (inboxes)
  ```

### 5.3 CLI

#### `bob ready` (new top-level, read-only command)

It sits next to `bob plan` and `bob freshness` and follows `cli_rules.md`: sorted options, a short alias for
every long option, colored output on a TTY, `NO_COLOR` respected.

```text
Usage: bob ready [OPTIONS] [NOTE]

Show READY tasks per area/project note against the per-note cap.

Arguments:
  [NOTE]  Show one note's READY tasks (route name, basename, or vault path)

Options:
  -a, --all               Also list notes with no READY tasks, idle projects, and exempt notes
  -b, --bob-dir <DIR>     Bob vault root; defaults to BOB_DIR or ~/bob
  -c, --cap <N>           Preview a different per-note cap for this run only
  -f, --format <FORMAT>   human or json [default: human]
  -h, --help              Print help

Examples:
  bob ready
  bob ready sase_remote
  bob ready -c 3
  bob ready -f json
```

**Human output.** This mock uses today's real numbers. Bars are one cell per task, a dim `│` marks the cap,
cells past the cap are red, a FULL row is yellow, a ROOM row is green, and rows longer than 36 cells end in
`…`.

```text
bob ready · Thu 2026-10-01 · cap 5 per note

  CROWDED 4 · +65 over · FULL 3       READY 210/100 = 134 in notes + 65 inbox + 11 recurring

  CROWDED
    sase             60/5  ■■■■■│■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■…   +55   project · dev
    sase_remote      11/5  ■■■■■│■■■■■■                               +6   project · sase
    sase_pager        7/5  ■■■■■│■■                                   +2   project · sase
    sase_usage        7/5  ■■■■■│■■                                   +2   project · sase
  FULL
    bob               5/5  ■■■■■│                                          project · gtd
    cash              5/5  ■■■■■│                                          area · ↻ 1
    sase_bug_bash     5/5  ■■■■■│                                          project · sase
  ROOM
    dev               4/5  ■■■■·│                                          area
    sase_memory       4/5  ■■■■·│                                          project · sase
    … 17 more with 1–3 ready · 26 with none                               (-a/--all)

  Make room: `bob ready sase_remote` lists its tasks · split with Ctrl+Shift+N, then
  N<Ctrl+Shift+M> · defer with Ctrl+Shift+P → priority.
```

- A note with NEW/ROTTEN tasks gets a muted `+2 in review` after its bar.
- With nothing crowded, the header reads `CROWDED 0 ✓` in green and the CROWDED group is omitted.

**`bob ready sase_remote`** prints one note as a worklist, in file order, with `path:line` you can jump to:

```text
bob ready · sase_remote · 11/5 · 6 over · project (parent sase)

     1  sase_remote.md:21  Add full support for machines across the TUI and CLI!       fresh 1d  ^machines
     2  sase_remote.md:28  Implement follow-up memory changes recommended by `0gq`…    fresh 1d  ^memory
     3  sase_remote.md:29  The "Machines" SAC tab should provide a much better …      fresh 1d
     …
    11  sase_remote.md:38  Share prompt history and PIW / LSP completions with fleet!  fresh 1d

  also here: 1 pending · 2 blocked · 0 in review
  Make room for 6: defer (Ctrl+Shift+P → priority) or split (Ctrl+Shift+N, then N<Ctrl+Shift+M>).
```

**JSON** (`schema_version: 1`, `ok: true`) is additive-friendly for a future Mac Capture or tmux consumer:

```json
{
  "date": "2026-10-01",
  "cap": { "default": 5, "source": "config" },
  "totals": { "ready": 210, "in_notes": 134, "outside": 0, "exempt": 65, "recurring": 11,
              "notes": 52, "crowded": 4, "full": 3, "excess": 65 },
  "notes": [
    { "path": "sase_remote.md", "name": "sase_remote", "kind": "project", "status": "wip",
      "parent": "sase", "count": 11, "cap": 5, "cap_source": "default", "state": "crowded",
      "over_by": 6, "review": { "new": 0, "rotten": 0 }, "recurring": 0, "next": 0, "pending": 1 }
  ],
  "warnings": [],
  "ok": true,
  "schema_version": 1
}
```

Exit codes: 0 for a report (crowded notes don't fail it: it's a soft limit), 1 for I/O, 2 for usage or an
invalid plan config.

#### `bob plan` (additive)

- The meter line gains READY and CROWDED, for parity with the daily `bob-plan` block, which already shows
  READY:

  ```text
    PLAN  3/3 themes · 7/10 links      TODAY 7 · PENDING 8/10 · NEXT 12/15 · READY 210/100 · CROWDED 4
  ```

- It gains one summary lint, never one per note:
  `4 notes over their READY cap: sase 60/5, sase_remote 11/5, sase_pager 7/5, sase_usage 7/5 — see bob ready`
  with code `note_ready_cap_exceeded`.
- JSON adds `ready` (`count/cap/over`) and `crowded` (`count, excess, notes[]`). The schema stays additive.
  `ready_cap_exceeded` becomes a native lint too, so the CLI and the daily block finally agree.

**Performance budget.**
- Assemble from **one** shared rich-task scan: the native engine already scans for the lanes. Filter
  READY rows in memory instead of issuing more queries; skip the freshness seed's `OPEN_QUERY` and full scan.
- Baselines today: `bob plan` 2.1 s, `bob freshness list` 3.3 s, `bob projects list` 0.12 s.
- Target: `bob ready` ≤ `bob plan`, and `bob plan` no more than about 10% slower than today.

### 5.4 Obsidian engine: `api.noteReady` in bob-ledger-tools

This is a new namespace, `api.noteReady.version = 1`. The top-level api stays v3 and the change is additive,
following the freshness-namespace precedent. Every consumer feature-detects it and degrades to `–`.

| Member | Shape | Used by |
| --- | --- | --- |
| `budgets()` | `{available, cap, totals, notes: [{path, name, kind, count, cap, capSource, state, overBy, review, recurring}]}`, sorted CROWDED → FULL → ROOM, then by count | dash chip, `crowded.md` widget |
| `budget(path)` | one note's entry, or `{available: false}` | heading chip, gesture chips |
| `countsTask(task)` | does this task count *now* | gesture deltas (source note) |
| `eligible(task)` | would it count once stamped: the same predicate minus the freshness bucket | gesture deltas (destination; moves and releases stamp) |
| `claim(paths, ttlMs = 10000)` | marks notes whose change a gesture already reported | watcher dedupe |
| `renderCrowdedChip(el, opts)`, `renderNoteChip(el, {path, component})` | lifecycle-owned live badges, the same pattern as `renderReadyBadge` | dash, heading chip |

**Implementation notes.**
- Compute in **one pass** over `planBlockTasks` with the existing `readyTaskVisible` / `planTaskIsBlocked` /
  `isTodayTask` / freshness-bucket helpers, grouping by `planTaskPath`.
- Memoize on the freshness memo's keys: Tasks array identity, `tasksGen`, local date, frontmatter generation,
  config key, Today stamp.
- Read note `type`/`status`/`ready_cap` frontmatter with `metadataCache.getFileCache(file)`, cached per path
  and invalidated on `changed`. Do **not** copy the current `getCache({path})` call (bug `bob-cli-3e`).
- Refresh through the existing 150 ms debounced `cache-update` path and the 60 s tick.
- **Cache `loadPlanCaps` by mtime.** Today it does a synchronous read and parse per call; this feature
  multiplies the callers.
- Availability is exactly `readyBudget()`'s: Tasks Warm, Today cache current. When it isn't available, show
  `–`, never 0.

### 5.5 `dash.md`: the CROWDED chip, and `crowded.md`

**Chip.**
- Order becomes NEW, PENDING, NEXT, READY, **CROWDED↗**, BLOCKED, ROTTEN, TODAY. CROWDED sits next to READY
  because it describes how READY is distributed.
- The value is the crowded-note count:
  - **`0` uses a calm purple accent with a `✓`** (positive reinforcement);
  - **> 0 uses the existing `task-count-over` red**;
  - `–` when unavailable.
- Tooltip: `4 notes over 5 READY: sase 60, sase_remote 11, sase_pager 7, sase_usage 7 · 3 full · +65 over the cap. Open Crowded Notes.`
- Click opens `crowded.md`, with the `↗` external arrow like BLOCKED and ROTTEN.
- Rendered through `renderCrowdedChip`, with a guarded inline fallback (`–`) as the other chips have.
- Adding a chip changes the chip contract in decision `ready-is-freshness-gated`, so a new decision record
  supersedes it for the chip list (§7).

**`crowded.md`** (aliases `Crowded`, `Crowded Notes`) is a live view, not stored data.

```text
┌ READY by note · cap 5 · CROWDED 4 · +65 over · 3 full ─────────────────────────────┐
│ CROWDED                                                                               │
│  sase           ▰▰▰▰▰┃▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰…   60/5  [+55]   project · dev      │
│  sase_remote    ▰▰▰▰▰┃▰▰▰▰▰▰                       11/5  [+6]    project · sase     │
│  sase_pager     ▰▰▰▰▰┃▰▰                            7/5  [+2]                       │
│  sase_usage     ▰▰▰▰▰┃▰▰                            7/5  [+2]                       │
│ FULL                                                                                  │
│  bob            ▰▰▰▰▰┃                               5/5  full                       │
│  cash           ▰▰▰▰▰┃                               5/5  full · ↻1                  │
│  sase_bug_bash  ▰▰▰▰▰┃                               5/5  full                       │
│ ROOM  dev 4 · sase_memory 4 · sase_art 3 · sase_better_installs 3 · … (17)           │
│ NOT CAPPED  gkeep_inbox 65 (ready_cap: off) · recurring 11                           │
│ Split: Ctrl+Shift+N, then N<Ctrl+Shift+M>   ·   Defer: Ctrl+Shift+P → priority       │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

- It is a ` ```bob-ready-notes``` ` code block that ledger-tools renders. Rows are links with hover previews.
- The bar uses the same segmented-chip styling as the dash chips: overflow segments in red, the FULL accent
  amber, the ROOM row compressed to one wrapped line of `name count` pills.
- Below it, a Tasks query lists the READY tasks of crowded notes, grouped by note
  (`filter by function …api.noteReady?.budget(task.file.path)?.state === "crowded"` plus the READY filters).
  Clicking a task jumps to its source line, where Ctrl+Shift+P and Ctrl+Shift+M work. This matches how
  `rotten.md` works.

The same `bob-ready-notes` block can be dropped into the weekly-review note.

### 5.6 In each area/project note: the `## Tasks` heading chip

A small live chip sits at the end of the `## Tasks` heading line.

- Live Preview: a CM6 widget decoration, the same mechanism as the freshness marks' ViewPlugin.
- Reading view: a markdown post-processor.
- It applies only to capped and exempt area/project notes.

```text
## Tasks                                                      READY 11/5 · +6
[⚪ 11 open] · [🔵 1 next/wip] · [🔴 2 blocked] · [🟢 8 done/canceled]      ← hooks row, untouched
```

| State | Look |
| --- | --- |
| ROOM | muted text, no accent: `READY 3/5` |
| FULL | amber accent: `READY 5/5 · full` |
| CROWDED | red accent: `READY 11/5 · +6` |
| exempt | muted: `READY 65 · no cap` |
| in review | an extra muted segment: `· +2 in review` |

- The tooltip spells it out: `11 READY · cap 5 (default) · 6 over · 0 in review. Split (Ctrl+Shift+N, then Ctrl+Shift+M) or defer (Ctrl+Shift+P).`
- Clicking opens `crowded.md`.
- The chip sits on the heading, not appended to the hooks row, so a live count never shares a row with the
  written `⚪ open` snapshot. Those two numbers legitimately differ by NEW/ROTTEN and by hooks staleness.
- Six notes have no `## Tasks` heading: the two inboxes, `gtd_daily`, `recur`, `job`, `needs_attn_tasks`.
  They simply show no inline chip. `bob ready`, `crowded.md`, and the toasts still cover them.

### 5.7 Notifications

**Which gestures can raise a note's READY count.** The plugin inventory below came from a code survey of all
six plugins.

| Gesture | Effect on note READY | Coverage |
| --- | --- | --- |
| **Ctrl+Shift+M** move (single and `N<C-S-M>`) | +k at the destination (moved open TODO tasks are stamped), −k at the source | **Gesture chip** (projection) |
| **Alt+N release** (Next/Pending → Ready), on task lines or Task Links | +k in each affected note (released tasks are stamped) | **Gesture chip** |
| **Ctrl+Shift+P** priority / scheduled / Ctrl+Enter roll / cancel | usually −1 (deferral or cancel), which is your named remedy | **Progress chip** when the note was FULL or CROWDED |
| Ctrl+Shift+P `scheduled` → today/past or Ctrl+D; `^prj` project schedule set/delete | + (Blocked → Ready recovery, sometimes note-wide) | watcher (active note) |
| **Alt+F / Alt+Shift+F / `]s` review** confirming NEW or ROTTEN | +1 (bucket → READY); **the main inflow** | watcher (the review jump makes the note active) |
| task-status-cycler Alt+] / Alt+[ into `[ ]`, Ctrl+Enter reopen, Ctrl+Shift+] promote, `ta<Tab>` snippet | +1 | watcher |
| Cancel or close that recovers dependents in other notes (`recoverBlockedDependents`) | + elsewhere | watcher if active; otherwise silent badges (phase 5: claim + chip) |
| Create project from task / restore project to task / Ctrl+Shift+N | the new or parent note gains tasks | watcher plus the new note's heading chip |
| Background: hooks, Obsidian Sync, `bob` CLI writes, mobile edits | any | **silent**: chips and counts update, no toast |

**Gesture chips** follow the existing lane-suffix pattern.
- Read `api.noteReady.budget(path)` synchronously before the write.
- Compute the delta from the plan: `eligible()` for tasks arriving, `countsTask()` for tasks leaving.
- Show the after-count and `claim()` the notes.
- Ctrl+Shift+M graduates from its plain text notice to the existing `.bob-nh-notice` card:

```text
┌ ⤵  Moved 2 tasks → sase_pager ──────────────────────────────┐
│  [ sase_pager READY 7/5 · +2 ]   [ sase READY 58/5 ↓2 ]       │
│  Split it (Ctrl+Shift+N, then Ctrl+Shift+M) or defer (Ctrl+Shift+P)
└───────────────────────────────────────────────────────────────┘
```

- Chip tones:
  - destination CROWDED: **new `is-over` red tone** (the existing tones stop at orange `warn`);
  - destination FULL: amber `warn`, e.g. `sase_pager READY 5/5 · full`;
  - destination ROOM: muted `READY 3/5`, always shown, because it teaches the number at routing time the way
    link notices always show `plan 1/3 · 2/10`;
  - source progress: `info`, shown only when the source was FULL or CROWDED.
- The card stays 8 s when over, otherwise the default.
- Plain-text fallback: `Moved 2 tasks to sase_pager · 🔴 sase_pager READY 7/5 · split or defer`.
- Alt+N release (text notice, existing style):
  `→ Ready · 1 task · NEXT 11/15 · PENDING 7/10 · 🔴 sase_remote READY 12/5 · split or defer`.
- Ctrl+Shift+P on a task in a crowded note adds a progress chip to the existing priority or cancel card:
  - `sase_remote READY 11 → 10/5`;
  - at the cap: `✓ sase_remote back to 5/5`, in the `ok` tone.

**The watcher** in ledger-tools is the reliability backbone. It is one implementation for every gesture that
edits the note you're in.

1. Keep the last per-note snapshot. Ignore the first snapshot after load, the midnight rollover (counts only
   fall then), and any recompute while Tasks isn't Warm.
2. When a note's count **rises** and the note is now CROWDED: toast **only if** it is the active file, or it
   was claimed for "watch" by a gesture. Never for background changes.
3. A crossing (≤cap → >cap) always toasts. Further growth while over toasts at most once per note per
   15 minutes. Notes already claimed by a gesture chip are skipped.
4. A crowded note that drops to ≤ cap in the active file gets `✓ sase_remote back to 5/5` once per crossing.

Watcher toast:

```text
🔴 sase_pager is crowded · READY 6/5
Split it (Ctrl+Shift+N, then Ctrl+Shift+M) or defer (Ctrl+Shift+P).
```

### 5.8 Prevention: counts in the Ctrl+Shift+M destination picker

Each destination row gets a right-aligned `READY n/5` pill. The pill is muted for ROOM, amber with `full` for
FULL, and red with `+k` for CROWDED, and the tooltip shows the projected after-count. Order and filtering are
unchanged; this is information, not steering. The same field can later reach `bob capture-targets -f json`
and Mac Capture's destination rows (A12). That native path needs the scan cached, because today
`capture-targets` costs 0.12 s and a full Tasks scan costs about 2 s.

### 5.9 One visual language everywhere

| State | Meaning | CLI | Obsidian |
| --- | --- | --- | --- |
| ROOM | count < cap | green bar, dim count | muted chip, no accent |
| FULL | count = cap: the next confirmed task tips it | yellow bar, `5/5` | amber accent, `· full` |
| CROWDED | count > cap | red overflow cells, `+k` | red accent (`--task-status-blocked`), `+k` pill |
| EXEMPT | `ready_cap: off` | dim, `no cap` | muted, `no cap` |
| in review | NEW/ROTTEN in the note | dim `+k in review` | muted `· +k in review` |
| fixed | crowded → ≤ cap | `CROWDED 0 ✓` | green `ok` chip `✓ back to 5/5`; purple calm CROWDED chip |

The words are the same everywhere: a note is **crowded**, **full**, or has **room**. The remedies are always
named the same two ways: **split** or **defer**.

### 5.10 Ritual update (`docs/freshness.md` §6)

The morning sequence becomes:

1. `bob gkeep pull`.
2. Clear NEW to 0.
3. Clear ROTTEN to 0 or until the budget is met.
4. **New step: clear CROWDED to 0.**
   - Open `crowded.md`, or run `bob ready`.
   - For each crowded note, split or defer until it shows FULL or ROOM.
   - A note you consciously keep large gets a `ready_cap:`.
5. PENDING → NEXT.

The weekly prune adds one line: "check `bob ready -a` for idle projects."

---

## 6. Alternatives considered and rejected

| Alternative | Why not |
| --- | --- |
| **Count raw `[ ]` checkboxes per note** (or SHOWN from `bob projects list`) | It disagrees with dash READY, includes unconfirmed NEW tasks, and makes projections disagree with the stamping rules. Simpler, but it would be a second meaning of "ready." |
| **Count the ungated pool (READY + NEW + ROTTEN)** as the capped number | Defensible ("skipping review must not hide pressure"), but it diverges from what dash shows. Kept as the visible `+k in review` segment instead. |
| **Store counts** (`ready_count` frontmatter via bob-project-tasks, or a hooks badge chip) so `projects.base` can sort | Freshness makes READY time-varying without edits (ROTTEN at day boundaries), so stored counts go stale. It adds write churn and covers projects only. The decisions consistently prefer read-time evaluation. |
| **Refuse moves into a crowded note** (`strict` mode) | Every Bob cap is soft. A refused move during triage is worse than a crowded note, because it blocks the very routing that fixes crowding. Revisit only if the soft trial fails. |
| **Roll up a parent's count over its children** | The requirement is per file, and a rollup hides exactly the chowder in the parent. Showing the parent name in `bob ready` gives the hierarchy hint without double counting. |
| **Annotate dash READY group headings** (`group by function` with `%%`-sorted `sase_remote · 11/5 ▲6`) | Feasible: Tasks renders group headings as Markdown and documents `%%…%%` sort keys. But the global `TQ_extra_instructions: group by path` would have to move into each block. Good optional polish (phase 5), not the primary "which ones" surface. |
| **Fold CROWDED into the READY badge** (`READY 210/100 · 4▲`) | It overloads one chip with two dimensions, volume and shape, and makes "red" ambiguous. |
| **A CROWDED section inside dash** | dash sections are a mutually exclusive partition of tasks, and a table of notes breaks that contract. A separate `crowded.md` follows the BLOCKED and ROTTEN pattern. |
| **Watcher only, no gesture chips** | It can't attribute a move to its destination when the destination isn't the active file, and it gives no projection at decision time. |
| **Gesture chips only, no watcher** | About 15 call sites across 3 plugins, and hand edits and review stamps would be missed. The hybrid covers everything with two small mechanisms. |
| **Also cap NEXT per project** | A different problem: commitment, not backlog. NEXT and PENDING already have global caps and a sticky-lane release ritual. |

---

## 7. Implementation plan

The work spans bob-cli, bob-plugins (ledger-tools and nav), and the vault, so it is an epic. Each phase is
independently shippable.

| Phase | Repo | Deliverable | Tests |
| --- | --- | --- | --- |
| **1. contract** | bob-cli docs + memory | `docs/plan.md` "READY per note" with N1–N10; config key; `ready_cap` frontmatter; lints `note_ready_cap_exceeded`, `note_ready_cap_invalid`, `note_ready_in_terminal_project`. **New decision record**: "Per-note READY is a read-time soft cap; native READY exists". It supersedes in part `ready-is-freshness-gated` (chip list; "no native READY / `bob plan` lint") and records the rejected alternatives above. It goes through `/sase_memory_write`, since records are immutable. | doc vector review |
| **2. native** | bob-cli | `src/native/note_ready/` (evaluate + scan reusing freshness/dataview rows); `bob ready` (human, json, `[NOTE]`, `-a`, `-c`); `bob plan` meter, lint, and JSON additions; `PlanConfig.max_ready_per_note` | N1–N10 unit vectors, CLI snapshot tests, perf check against `bob plan` |
| **3. ledger-tools** | bob-plugins | `api.noteReady` v1; watcher; `renderCrowdedChip` / `renderNoteChip`; the `bob-ready-notes` block; the `## Tasks` heading chip (ViewPlugin + post-processor); `loadPlanCaps` mtime cache; a red notice-chip tone shared via CSS; daily `bob-plan` lint line `note_ready_cap_exceeded` | N1–N10 copied verbatim; watcher throttle, claim, and active-file tests; badge lifecycle tests (assert classes; see `bob-cli-3d`) |
| **4. vault** | bob (vault) | dash CROWDED chip (shared renderer, inline `–` fallback); `crowded.md`; `ready_cap: off` on `gkeep_inbox` and `inbox`; ritual line in the weekly-prune chore | manual live check; `bob query --tasks-note crowded.md` |
| **5. nav** | bob-plugins | Ctrl+Shift+M card + picker pills; Alt+N release suffix; Ctrl+Shift+P progress chip; `claim()` at each | extend `test-navigation-hotkeys.cjs` lane-notice tests |
| 6. optional | all | capture advisory (`bob capture` output, `capture-targets` field, Mac destination row); IDLE group; READY group headings in dash; cycler and dependent-recovery chips | — |

**Sequencing.**
- Phases 2 and 4 can ship read-only surfaces right away.
- The freshness-gated READY trial runs **2026-10-05 → 2026-10-18**. To avoid confounding its keep rule, ship
  the toasts (phases 3 and 5) after it, or at least say in the trial log that per-note pressure is now
  visible.

**Trial and keep rule** (two weeks after the toasts land):
- crowded notes other than `sase` reach 0 on ≥ 10 of 14 mornings;
- `sase` excess falls by ≥ 50%;
- toasts you would call noise stay at ≤ 1 per day.

If it fails, tune N, add overrides, or reduce toasts to crossings only before considering removal.

**Before the trial:** spend one GTD block on `sase.md`. Route its 60 READY tasks into the roughly 40 existing
`sase_*` projects with N<Ctrl+Shift+M>, create two or three new scopes where clusters appear, and defer the
rest. Otherwise CROWDED starts as permanent wallpaper.

---

## 8. Open questions for Bryan

These are short and don't block the recommendation.

1. **`sase.md`:** fix it in one triage session (my recommendation), or give it a dated transitional
   `ready_cap: 20`? Separately, is it really an area? Re-typing doesn't dodge the cap, since areas are capped
   too.
2. **Same default for areas and projects?** I recommend yes, with per-note overrides for legitimately broad
   areas.
3. **The name "CROWDED".** It reads naturally ("4 crowded notes", "sase_pager is crowded") and pairs with
   FULL and ROOM. Rename freely before the chip ships.

---

## 9. Recommended solution

Build **"note READY"**: the dash's freshness-gated READY predicate, grouped by the area or non-terminal
project note that contains each task.
- Recurring tasks are excluded.
- Inboxes are exempt through `ready_cap: off`.
- The limit is `plan.max_ready_per_note: 5`, with an optional per-note `ready_cap:`.
- A note is **CROWDED** above its cap, **FULL** at it, and has **ROOM** below it.
- The limit is soft and read-time. Nothing is refused or written to tasks.

Implement it twice with shared conformance vectors:
- natively in Rust, a new evaluator assembled from the existing READY query, Today, and freshness pieces;
- in bob-ledger-tools as `api.noteReady` v1.

Surface it six ways, each with a distinct job:

1. **`bob ready`:** a colored, bar-chart terminal view grouped CROWDED / FULL / ROOM, with
   `bob ready <note>` as a worklist and `-f json`. `bob plan` gains `READY n/100 · CROWDED k` and one
   summary lint.
2. **`dash.md` CROWDED↗ chip**, after READY: purple `0 ✓` when clean, red count when not. It opens
   **`crowded.md`**, a live ranked bar widget plus the crowded notes' READY tasks.
3. **A live `READY n/5` chip on every area/project note's `## Tasks` heading**, kept separate from the
   hooks-written badge row.
4. **Gesture-aware toasts:**
   - destination and source chips on Ctrl+Shift+M (as a proper notice card) and Alt+N release;
   - progress chips (`↓1`, `✓ back to 5/5`) on Ctrl+Shift+P;
   - an active-note **watcher** in ledger-tools for every other gesture, notably Alt+F / Alt+Shift+F review
     confirmations, the main inflow. It is throttled, deduplicated through `claim()`, and silent for
     background changes.
5. **Prevention:** `READY n/5` pills in the Ctrl+Shift+M destination picker.
6. **Ritual:** a "clear CROWDED to 0" step after NEW and ROTTEN, and a one-time `sase.md` triage before the
   trial.

Record it as a new decision record. It partly supersedes `ready-is-freshness-gated` (the chip list, and
"no native READY count"), and it is the documented reopen condition of that record: a plugin-free surface
that needs gating.

---

## Appendix A: issues discovered during this research (filed as task beads)

- **`bob-cli-3d`:** the dash PENDING/NEXT badges lose their lane class.
  - `renderDashboardLaneBadge` → `setReadyAnchorContent` overwrites `class` with `bob-plan-chip bob-plan-ready…`
    and nothing restores it.
  - Result: PENDING and NEXT render with READY's blue accent.
  - Tests use stubs and never assert the class.
- **`bob-cli-3e`:** ledger-tools reads `task_refresh` with `metadataCache.getCache({ path })` /
  `getCache(file)` instead of a path string or `getFileCache(file)`.
  - Result: note-level freshness intervals never apply in Obsidian, while Rust honors them.
  - Latent: no top-level note sets `task_refresh` yet.
  - Relevant here because the `ready_cap` read must not copy that pattern.

Smaller observations, not filed:
- ledger-tools `loadPlanCaps()` re-reads and parses `config.yml` on every call. This is folded into phase 3.
- The daily `bob-plan` READY count skips the Warm and Today-ready checks that `readyBudget()` applies, so at
  startup the daily badge can show a number while dash shows `–`.
- The ledger-tools README still says freshness namespace v2.

## Appendix B: sources

- Bob contracts: `docs/plan.md` (READY backlog, Lanes, Config, Surfaces), `docs/freshness.md` §§2, 4–8,
  `docs/projects.md`, `docs/task-status-hooks.md` (Status Grouping and the badge row).
- Decision records `ready-is-freshness-gated`, `task-lanes-are-sticky`, `today-is-read-from-the-ledger`,
  `task-status-is-derived`, `mac-capture-is-a-thin-client`, and `cli_rules.md` (via `sase memory read`).
- Code surveyed:
  - bob-ledger-tools `main.js` (`readyBudget` ~6384, `readyCountFromTasks` ~3250, `renderReadyBadge` ~6859,
    `loadPlanCaps` ~10462, the freshness memo ~7483);
  - bob-navigation-hotkeys `main.js` (`buildLaneToggleNotice` ~15805, `commitTaskMoveSession` ~34179,
    `collectTaskMoveDestinations` ~16864, `isAreaOrProjectNote` ~36059, notice cards ~19405–19893);
  - task-status-cycler;
  - bob-cli `src/native/{freshness/scan.rs, dataview/tasks/mod.rs, plan_budget, config/plan.rs, capture_targets.rs}`.
- Live vault data: `bob query` (READY filters), `bob plan -f json`, `bob freshness list -f json`,
  `bob projects list`, `bob capture-targets`, and timings, all run 2026-10-01.
- Prior research (context only): `research:202609/ready_task_freshness_review/ready_task_freshness_review__final.md`
  and `research:202610/freshness_gated_ready_dash/freshness_gated_ready_dash__mus.md`. The latter listed
  `^prj-task-count-warn` as "a small additive hooks/plan lint, independent of this proposal."
- External:
  - Ryan Singer, *Shape Up*, ch. "Map the Scopes" (Chowder, and the signs a scope should be redrawn):
    <https://basecamp.com/shapeup/3.3-chapter-12>
  - Obsidian Tasks, Custom Grouping (headings rendered as Markdown; `%%…%%` sort keys):
    <https://publish.obsidian.md/tasks/Scripting/Custom+Grouping>
  - Kanban WIP limits per column, swimlane, person, or class of service; queue replenishment:
    <https://www.linkedin.com/pulse/kanban-wip-limits-faq-dimitar-karaivanov>,
    <https://kanban.university/patterns-of-kanban-maturity/>,
    <https://leantime.io/kanban-swimlanes/>
  - GTD Weekly Review checklist ("ensuring at least one current action item on each"):
    <https://gettingthingsdone.com/wp-content/uploads/2014/10/Weekly_Review_Checklist.pdf>

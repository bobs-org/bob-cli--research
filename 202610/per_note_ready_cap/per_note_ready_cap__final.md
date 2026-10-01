# Per-note Ready cap ("crowded notes"): consolidated design and recommendation

- **Lead researcher:** final consolidation of five independent reports (`__cdx`, `__cld`, `__grk`,
  `__mus`, `__gem` in this directory) plus the lead's own verification against code and the live vault.
- **Date:** 2026-10-01. All live numbers were measured this afternoon on `~/bob`.
- **Request:** During morning GTD, no area or project note should hold more than N ready tasks. N is
  configurable and defaults to 5. Violations should be obvious in Obsidian (a toast from keymaps that cause
  one, plus badges or diagnostics in `dash.md` and/or the notes) and on the command line. The design should
  be intuitive, reliable, and beautiful. The request also asks for a critique, any justified requirement
  changes (clearly marked), and a recommended solution.
- **Existing vault task:** `bob_gtd#^prj-task-count-warn`, "Show warnings when projects contain >5 ready
  tasks!" It is Next and linked in today's ledger. This request is that task.

---

## 0. Bottom line

1. **Build it.** It is a good idea, but it is a *concentration* signal, not a second volume cap.
   - `plan.max_ready: 100` already bounds *how much* is ready.
   - A per-note cap bounds *where* ready work piles up, and it names the note that needs a decision.
   - All five researchers agree on this, and the live vault shows why (§2): four notes are over, and one
     of them (`sase.md`) holds 85% of the excess.
2. **Count the note's whole Ready lane, not the freshness-gated READY section.** This is the one real
   disagreement among the five reports. cdx, cld, and mus said gated; grk and gem said ungated.
   - The lead's simulation settles it (§3). Gated per-note counts fall to zero within a week by
     themselves: `sase` goes 60 → 34 → 22 → 12 → 0 by 2026-10-08 with no action taken, because stamps
     expire on the 7-day interval.
   - With a gated count, ignoring a crowded note makes it look fixed, and confirming tasks during review
     makes it look worse. Both incentives are backwards.
   - The lane count, `[ ]` tasks that are visible and pullable whatever their freshness, avoids both. It
     also matches the words "ready tasks", the in-note `⚪ open` badge Bryan already sees, and Bob's
     existing rule that cap warnings use the whole lane.
3. **Keep it soft, read-time, and consistent with every other Bob cap.**
   - Strictly over is red; exactly at the cap is fine.
   - Nothing is refused, nothing is written to tasks or frontmatter, and an unavailable count shows `–`,
     never `0`.
4. **Surfaces.** Each one has a distinct job (§5):

   | Where | What | Job |
   | --- | --- | --- |
   | CLI | **`bob ready`**: a colored bar view grouped CROWDED / FULL / ROOM; `bob ready <note>` is a worklist; `-f json` | "Which notes, by how much", without Obsidian |
   | `dash.md` | **`CROWDED k ↗`** chip between READY and BLOCKED, opening `crowded.md` | "How many", at a glance |
   | `crowded.md` | A live ranked bar widget plus the crowded notes' tasks, which click through to their source lines | "Which ones", then act |
   | Area/project notes | A live **`ready 11/5 · +6`** chip on the `## Tasks` heading | "Is *this* note over?" |
   | Ctrl+Shift+M picker | A `n/5` pill on every destination, plus a projection on the highlighted row | **Prevention**, before choosing |
   | Bob command notices | One consolidated capacity chip per command that worsens a crowded note, plus `✓ back to 5/5` progress | Feedback at the moment of the change |

5. **Requirement changes**, all called out in §4.
   - Count the lane.
   - Exempt inboxes with `ready_cap: off`.
   - Don't count recurring tasks.
   - Add a per-note `ready_cap:` override.
   - "Any keymap" becomes "any Bob command that makes a crowded note worse".
   - Add picker prevention and positive feedback.
   - Name four remedies instead of two.
   - Do one `sase.md` triage before the toasts ship.

---

## 1. Is this a good idea? (merged critique)

### 1.1 Why it is good

- **It turns a vague signal into a located one.**
  - `READY 87/100`, or a red global chip, implies "do less", which you can't act on directly.
  - `sase_remote 11/5` implies a concrete move: draw a scope and move four tasks into it, or defer two.
  - Concentration and volume fail independently. 90 READY tasks spread over 30 notes is healthy; 61 of them
    in one note is not.
- **Established practice supports it, if it is framed honestly.**
  - *Shape Up*, "Map the Scopes": when a chowder list "gets longer than three to five items, something is
    fishy and there's probably a scope to be drawn". The default of 5 is the top of that range.
  - *Kanban* sets limits per column or swimlane. A per-note limit is a per-swimlane limit on the ready
    queue.
  - *GTD* has a **floor** (at least one next action per project), not a ceiling. Allen allows parallel next
    actions and keeps sequential steps in project support.
  - So this cap is a deliberate Bob convention, not GTD doctrine. gem's claim that GTD projects
    "typically have only 1 to 2 next actions" overstates the sources; cdx and grk cite them correctly.
- **The live data supports N = 5** (§2).
  - The healthy notes cluster at 1–4, and 5 sits at the edge of that cluster.
  - At N = 5, four notes light up and three are exactly at the limit.
  - At N = 3, nine notes would be flagged, a third of all non-empty notes. That reads as noise.
- **Bob already has every input.** The lane predicate exists in both Rust and JavaScript. So do the area and
  project classifiers, the soft-cap visual language, the notice cards, and the picker row geometry. The new
  work is *signal*, not a new editing verb.

### 1.2 Where the original plan needs care

| Risk | Why it is real | How the design handles it |
| --- | --- | --- |
| **The word "ready" is ambiguous** | Bob now has a gated READY section, a whole Ready lane, `⚪ open` (hooks), and OPEN/SHOWN (`bob projects list`), all with different numbers | One definition, the note's Ready lane (§3), with its NEW/ROTTEN make-up shown beside it |
| **One elephant turns the signal into wallpaper** | `sase.md` is 61/5, and no single session clears it | Show excess (`+56`) so progress is visible. Give positive feedback. Do one triage session before toasts ship (§7). An explicit, visible override is allowed but discouraged |
| **Toast fatigue** | "Any keymap" includes a lot of gestures | Notify only when a Bob command makes a note worse *and* the note ends over its cap. One notice per command. Background changes are silent. Review stamps never trigger it (§5.5) |
| **Gaming by cosmetic splitting** (`sase_misc_2`) | Splitting is a named remedy | The global READY cap still bounds volume, and `bob ready` shows each note's parent so thin sibling piles are visible. The docs say the counter is a cue, not proof that a split is needed |
| **Gaming by deferral** | Ctrl+Shift+P rolls make tasks disappear | Deferral *is* the de-prioritizing remedy. The P-level decay ladder (P1 → P2 → P3 → cancel) eventually forces a real decision. A deferred task comes back, and with the lane definition it counts again |
| **Areas and inboxes aren't projects** | `gkeep_inbox` (65), `inbox`, and `mac_inbox` are typed `[[area]]` | Inboxes are exempt through `ready_cap: off`. Recurring habits are excluded. Ordinary areas share the default (no area is over 5 once those are excluded) |
| **Hard blocking** | It is tempting for a "constraint" | Rejected by all five reports. Every Bob cap is soft (`plan.strict` refuses only extra Pomodoro themes), and a refused move would block the very routing that fixes crowding |

### 1.3 Would I take a different approach?

Not a different approach, but a different emphasis than the request implies:

- **Prevention and the morning glance matter more than toasts.**
  - The highest-value surfaces are `bob ready` and the `CROWDED` chip (the review ritual) and the
    Ctrl+Shift+M picker pills (the routing decision).
  - Post-hoc toasts are the least important surface and the riskiest for noise, so they ship last.
- **There are four remedies, not two.** Pick by what is true of the work:

  | Remedy | When it fits | Gesture |
  | --- | --- | --- |
  | **Split** | A cluster is its own outcome | Ctrl+Shift+N (new project), then `N`Ctrl+Shift+M; or Ctrl+Alt+Shift+N from a parent task with children |
  | **Sequence** | B can't start until A is done | Ctrl+Shift+P → `dependsOn`, or the `!` toggle. B becomes Blocked and leaves the lane |
  | **Defer** | Not now, revisit later | Ctrl+Shift+P → P1–P4 roll (future `scheduled`, so it leaves the lane immediately) |
  | **Drop** | No longer wanted | Ctrl+Shift+P → cancel |

  The request named only split and defer. Sequence is GTD-correct, since sequential steps belong in project
  support. Drop is often the honest answer for stale `sase.md` ideas.

---

## 2. Ground truth (lead-verified, 2026-10-01)

### 2.1 Live distribution

The method was the native visible-TODO pool:

- `bob query --tasks` with the exact `READY_QUERY`: TODO type, not done, not dependency-blocked, no
  `#hide`, not `_templates`/`_conflicts`, not future-scheduled.
- Grouped by file, with recurring and `^prj` rows separated out.
- That gives 211 rows in 29 files, and 0 nested rows (every row is a root task).

| Note | Kind | Lane count | Recurring (excluded) | At N = 5 |
| --- | --- | ---: | ---: | --- |
| `gkeep_inbox` | area (inbox) | 65 | 0 | **exempt** (`ready_cap: off`) |
| `sase` | project | **61** | 0 | CROWDED +56 (1 of them NEW) |
| `sase_remote` | project | **11** | 0 | CROWDED +6 |
| `sase_pager` | project | **7** | 0 | CROWDED +2 |
| `sase_usage` | project | **7** | 0 | CROWDED +2 |
| `bob`, `sase_bug_bash` | project | 5 each | 0 | FULL |
| `cash` | area | 5 | 1 | FULL |
| `gtd_daily`, `recur` | area | 0 | 7, 3 | — (habits only) |
| `dev`, `sase_memory` | area, project | 4 each | 0 | room |
| 15 more notes | — | 1–3 | — | room |

**Eligible notes:** 51 (10 areas + 41 active projects; the 3 inbox notes are exempt).

- 4 are CROWDED, 3 FULL, 17 have room, and 27 are empty.
- 133 lane tasks sit in capped notes; **66 are over their cap, and 56 of those are in `sase.md`.**
- The hooks-written `⚪ open` badges already agree with these counts: `sase` ⚪ 61, `sase_remote` ⚪ 11,
  `cash` ⚪ 6 (including its 1 recurring task).

**Sensitivity**, over the same 51 notes:

| N | Crowded | Full | Excess |
| ---: | ---: | ---: | ---: |
| 3 | 9 | 2 | 82 |
| **5** | **4** | **3** | **66** |
| 7 | 2 | 2 | 58 |
| 10 | 2 | 0 | 52 |

**Corrections to individual reports:**
- gem's counts (62/12/8/8/6/6) are each one too high. The measured values are 61/11/7/7/5/5.
- cld said `mac_inbox` has no type. It does have `type: "[[area]]"` with `parent: "[[inbox]]"`, so all three
  inboxes need the exemption.
- mus's SHOWN-based fallback (`sase` 124) is the wrong denominator, because it includes Next and Pending.

### 2.2 What already exists (and what doesn't)

| Piece | Where | Relevance |
| --- | --- | --- |
| Lane visibility predicate | Rust `dataview::READY_QUERY`; ledger-tools `readyTaskVisible` + `planTaskIsBlocked` | **Exactly the counting predicate.** Native per-note counts are "group these rows by path" |
| Whole-lane composition | ledger-tools already computes `lane = {total, new, rotten, ready}` for the READY tooltip (`READY n/cap · lane T = a new + b rotten + c ready`) | Per-note composition is the same computation grouped by file |
| "Cap warnings use the whole lane" | `docs/plan.md` § Lanes: NEXT/PENDING caps count the whole lane, Today included, "so those counts don't swing during the day" | The precedent for counting the lane, not a gated section |
| Freshness buckets, natively | `bob freshness list -f json` (2.1 s) | Composition (new/rotten) in the CLI with no new gating engine |
| Area/project classifiers | Rust `projects/scan.rs`; nav `isAreaOrProjectNote` / `getChildNoteInfo` | They differ on list-form and bare `type` values (cdx), so pin them with shared vectors |
| Soft-cap language | READY badge: red only on strict excess, "no intermediate warning color" (`docs/plan.md`) | The style rule this feature follows |
| Notice cards | nav `.bob-nh-notice` with `warn`/`ok`/`info`/`muted` chips; lane notices append `NEXT 11/15 · PENDING 7/10` from a *before-read + delta* (`readLaneBudgets`) | The pattern for capacity chips, and it already sidesteps Tasks-cache lag |
| Ctrl+Shift+M | Destinations are areas plus open projects (`collectTaskMoveDestinations`). The success notice is **plain text** today (`Moved N tasks to X`) | The picker rows and notice need upgrading |
| External dash chips | `{ key: "blocked", target: "blocked", external: true }` with `↗` linking to `blocked.md` and `rotten.md` | `CROWDED ↗` → `crowded.md` follows this exactly |
| Hooks badge row | `⚪ open · 🔵 next/wip · 🔴 blocked · 🟢 done/canceled`, a **written snapshot** from the Mac cron every 15 min | Equal to the lane count except for recurring. Stale for up to 15 minutes, or longer while the Mac sleeps |
| Keymaps | Ctrl+Shift+N creates a project note; Ctrl+Alt+Shift+N creates a project from a task (vault `hotkeys.json`); Ctrl+Shift+P priority rolls (P1 2–7 days … P4) | The remedies |

---

## 3. The decisive question: what counts as "ready"?

### 3.1 The candidates

| Definition | Advocates | Problem |
| --- | --- | --- |
| Freshness-gated READY per note (lane minus NEW and ROTTEN) | cdx, cld, mus | Collapses when stamps expire, and fights the review ritual (below) |
| Raw `[ ]` / OPEN / SHOWN | — (rejected by all) | Includes hidden, blocked, Next, and Pending tasks (`sase` OPEN 262 / SHOWN 124) |
| **The note's Ready lane:** visible, pullable `[ ]` tasks whatever their freshness, minus recurring and `^prj` | grk, gem (lead adopts) | Doesn't add up to the dash READY chip; the composition display closes that gap |

### 3.2 Evidence: the rot cliff

`BOB_NOW=<day> bob freshness list -f json` was run against today's vault with **no review in between**.
This is the "Bryan skips the sase notes for a week" scenario.

| Morning | sase | sase_remote | sase_pager | bob | Gated notes over | Lane notes over |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 10-01 | 60 | 11 | 7 | 5 | 4 | 4 |
| 10-04 | 34 | 11 | 7 | 5 | 4 | 4 |
| 10-05 | 22 | 11 | 7 | 5 | 4 | 4 |
| 10-07 | 12 | 0 | 7 | 0 | 3 | 4 |
| 10-08 | **0** | **0** | **0** | 0 | **0 ("✓ all clear")** | **4** |

`sase.md`'s 60 confirmed tasks carry stamps from 09-27 (26), 09-28 (12), 09-30 (10), and 10-01 (12). With
the default 7-day interval, they rot in waves. A gated cap would report **"CROWDED 0 ✓" on 2026-10-08**
although nothing was split, sequenced, deferred, or dropped. That lands in the middle of the 10-05 → 10-18
freshness trial.

### 3.3 Why the lane definition wins

1. **Neglect can't satisfy it.** Only the four real remedies (split, sequence, defer, drop) lower the
   count. Moving tasks to Next also lowers it; §5.5 says the UI never suggests that.
2. **It doesn't fight review.** Alt+F, Alt+Shift+F, and `]s` change freshness, not the lane, so confirming a
   task never "worsens" a note. Under gating, every confirmation inside a crowded note would raise its
   count. cdx flagged this ("the diagnostic must never teach 'stop reviewing'") and grk named it the core
   problem. The freshness ritual (is this still wanted?) and the concentration ritual (is this note
   crowded?) stay independent.
3. **It matches Bob's own cap semantics.** The NEXT and PENDING caps already use the whole lane. The READY
   docs already admit that "skipping review can lower READY without lowering total lane pressure
   (`NEW + ROTTEN + READY`)".
4. **It matches what Bryan sees and says.** The note's `⚪ 61 open` badge, the decision records' "Ready `[ ]`"
   status, and `bob freshness`'s own help ("Review Ready tasks") all use "Ready" for this ungated set.
5. **It is cheaper and more reliable.**
   - The native count is the existing `READY_QUERY` scan grouped by path, with no new gating engine. So
     there is no need to reopen `ready-is-freshness-gated` ("reopens when a required plugin-free surface
     needs gating").
   - Gesture projections become exact arithmetic. A move adds the moved eligible rows, and stamps and
     per-note refresh overrides are irrelevant. Much of cdx's overlay and receipt machinery isn't needed.

**What it costs:** per-note counts don't add up to the dash `READY` chip, and the note chip for `sase` says
61 while the READY section lists 60 `sase` tasks. Showing the make-up everywhere fixes this:
`ready 61/5 · 60 ready + 1 new`. The ROTTEN pile stays visible and actionable, and dropping stale tasks
during review lowers both piles.

**Today:** whole-lane semantics include Today, as the NEXT/PENDING caps do. In practice this is close to
zero, because linking raises `[ ]` to `[*]`, which leaves the lane. It also means the native count needs no
Today evaluation. **Nested tasks:** each task row counts, for parity with the dash. This is moot today, since
the live pool has 0 nested rows. A parent with many child tasks is exactly what Ctrl+Alt+Shift+N exists to
promote.

---

## 4. Requirement adjustments (explicitly called out)

| # | Original requirement | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | "ready tasks" | **ADJ:** count the note's **Ready lane**: visible, unblocked, not future-scheduled `[ ]` (TODO-type) tasks, whatever their freshness. Show the make-up (`ready + new + rotten`) next to it. | §3: immune to neglect, independent of review, consistent with whole-lane caps |
| A2 | "area/project note file" | Notes whose frontmatter `type` is `[[area]]` or a non-terminal `[[project]]`, anywhere in the vault (scalar, quoted, list, and legacy bare forms), counted by the **file that physically holds the task**. No `parent` rollups. | Residence is how every Bob count is keyed. A rollup would hide the chowder list in the parent |
| A3 | — | **ADJ: inboxes are exempt** through explicit frontmatter `ready_cap: off`, set once on `inbox`, `gkeep_inbox`, and `mac_inbox`. They still appear, dimmed, in `bob ready -a`. | Their remedy is "process to zero", not split or defer. An explicit property is visible in Properties and survives renames, unlike a name or parent heuristic |
| A4 | — | **ADJ: recurring tasks don't count**; they are shown as `↻ k`. `^prj` lifecycle tasks don't count either. | Habits (`gtd_daily` 7, `recur` 3) can't be split or deferred. `^prj` is lifecycle, not work |
| A5 | N configurable, default 5 | `plan.max_ready_per_note: 5`, plus a per-note `ready_cap: <1–999 \| off>` override. Invalid values are linted (`note_ready_cap_invalid`) and fall back to the default. **No separate area default.** | Live data: no area is over 5 once inboxes and recurring are excluded. mus and gem's area defaults of 8/7 would add a knob the data doesn't need |
| A6 | Violation = more than N; warn when moving into a note that "already has ≥ N" | Over means `count > cap` (red). `count == cap` is **FULL**: a neutral text label, never a warning color, matching the READY badge's no-amber rule. The picker colors the **projected** result, so moving into a FULL note shows `5/5 → 6/5` in red before you choose. | Keeps the at-limit case visible at decision time without a second alarm color |
| A7 | Toast on "any keymap" that causes a violation | **ADJ:** any successful **Bob command** (keymap or command palette) that *raises* a note's count *and* leaves it over its cap gets one consolidated capacity chip in that command's notice. Hand edits, sync, hooks, the CLI, and mobile refresh badges silently. Review stamps never trigger it. | Keystrokes aren't a reliable boundary, and typing a task line must not toast mid-word |
| A8 | — | **ADJ: prevention.** Every Ctrl+Shift+M destination row shows `n/5`, and the highlighted row shows the projected after-count. | Choosing well beats being told afterwards (cld, grk, gem) |
| A9 | — | **ADJ: positive feedback.** Commands that lower a crowded note show `▼` progress and `✓ back to 5/5`. | Makes the remedy loop satisfying instead of nagging (cld) |
| A10 | Badge in dash and/or notes | **Both, each with a distinct job:** a dash `CROWDED` chip that opens `crowded.md`, and a live chip on each note's `## Tasks` heading. The hooks badge row is left unchanged. | A live count must not share a row with a 15-minute written snapshot |
| A11 | CLI view | A new read-only **`bob ready`**. **Optional later:** a one-line summary in `bob plan`, and an advisory `note_ready` field in `bob capture` JSON for Mac Capture. | Areas aren't projects, so this doesn't belong under `bob projects` |
| A12 | "de-prioritize or split" | **ADJ:** name four remedies: split, sequence, defer, drop (§1.3). | Sequence and drop are often the honest answer |

---

## 5. Design

### 5.1 Contract: "ready lane per note"

Add a section to `docs/plan.md` next to "READY backlog". The **Ready lane** is the visible TODO pool already
used by `READY_QUERY` and `readyTaskVisible`.

```text
counted(t)    = lane(t) ∧ ¬recurring(t) ∧ ¬prj(t)
note(t)       = the vault file containing t        (residence; not parent, heading, embed, or backlink)
eligible(n)   = type(n) ∈ {area, project} ∧ status(n) ∉ {done, canceled} ∧ ¬templates/conflicts/done/
cap(n)        = ready_cap (integer 1–999) | off → exempt | else plan.max_ready_per_note | else 5
count(n)      = |{ t : note(t) = n ∧ counted(t) }|          (freshness bucket and Today are NOT filters)
make_up(n)    = { ready, new, rotten }  over the same rows   (rotten includes resurfaced; display only)
state(n)      = exempt | unavailable | crowded (count > cap) | full (= cap) | room (0 < count < cap) | empty
crowded_total = |{ n : state(n) = crowded }|      excess = Σ max(0, count(n) − cap(n))
```

**Shared conformance vectors** (Rust and ledger-tools, copied verbatim like Today T1–T9):

| # | Fixture | Expected |
| --- | --- | --- |
| R1 | 6 `[ ]` tasks, default cap | `count 6, crowded, excess 1` |
| R2 | 5 `[ ]` tasks | `full`, no lint |
| R3 | `#hide`/`#Hide`/`#hide/x`, future `scheduled`, dependency-blocked, `[?]`, `[*]`, `[/]`, `[x]`, `[-]` | none count |
| R4 | 3 tasks: one unstamped (NEW), one stamped 8 days ago (ROTTEN), one fresh | `count 3`, make-up `1 ready + 1 new + 1 rotten` |
| R5 | `[repeat:: every day]` and `🔁` tasks | not counted; `recurring 2` |
| R6 | `^prj` task visible on dash | not counted |
| R7 | Tasks in a daily note, an untyped note, `_templates/`, `dash.md` | absent from the per-note list |
| R8 | `ready_cap: 8` / `off` / `0` / `lots` | cap 8 (source `note`) / exempt / lint, then default / lint, then default |
| R9 | A parent `[ ]` with 2 child `[ ]` tasks | `count 3` |
| R10 | `status: done` project with 2 `[ ]` tasks | not capped; lint `note_ready_in_terminal_project` |
| R11 | `type: "[[project]]"`, `type: [[project]]` (bare), list `type: ["[[area]]"]`, nested folder | all eligible; Rust and JS agree |
| R12 | Alt+Shift+F on a NEW task in a note at 5 | count unchanged (5), **no notice** |

### 5.2 Config

```yaml
plan:
  max_ready: 100          # existing global READY volume cap
  max_ready_per_note: 5   # soft cap per area/project note; frontmatter `ready_cap:` overrides
```

```yaml
# per-note frontmatter (residence only, never inherited through parent)
ready_cap: 8     # this note may hold 8 lane tasks
ready_cap: off   # exempt (inboxes)
```

Validation mirrors `plan:`. `bob ready` exits 2 on an invalid global value, and every other surface falls
back to the default and says so once in a tooltip. Tooltips and JSON expose the cap's source ("cap 8 from
this note" or "cap 5 from Bob config").

**Mobile caveat (cdx):** the global config lives outside the vault, so a customized N reads as the default 5
on the phone, and the tooltip says so. Per-note overrides live in the vault and work everywhere.

### 5.3 CLI: `bob ready`

A top-level, read-only command next to `bob plan` and `bob freshness`. It follows `cli_rules.md`: sorted
options, a short alias for each, color on a TTY, and `NO_COLOR` honored.

```text
Usage: bob ready [OPTIONS] [NOTE]

Show ready tasks per area/project note against the per-note cap.

Arguments:
  [NOTE]  List one note's ready tasks (route name, basename, or vault path)

Options:
  -a, --all              Also list empty, exempt, and terminal-project notes
  -b, --bob-dir <DIR>    Bob vault root; defaults to BOB_DIR or ~/bob
  -c, --check            Exit 3 when any note is crowded (for scripts and tmux)
  -f, --format <FORMAT>  human or json [default: human]
  -h, --help             Print help
  -n, --cap <N>          Preview a different per-note cap for this run only
```

**Human view.** This mock uses today's real numbers.
- One `■` cell per task. A dim `│` marks the cap, and cells past it are red.
- A FULL row stops exactly at the bar.
- Long bars end in `…` at 30 cells.
- Columns are display-width aware.

```text
bob ready · Thu 2026-10-01 · cap 5 per note

  CROWDED 4 · 66 over · 3 full · 51 notes (10 areas · 41 projects)

  CROWDED
    sase            61/5  ■■■■■│■■■■■■■■■■■■■■■■■■■■■■■■■…  +56   project · dev · 1 new
    sase_remote     11/5  ■■■■■│■■■■■■                       +6   project · sase
    sase_pager       7/5  ■■■■■│■■                           +2   project · sase
    sase_usage       7/5  ■■■■■│■■                           +2   project · sase
  FULL
    bob              5/5  ■■■■■│                                  project · gtd
    cash             5/5  ■■■■■│                                  area · ↻ 1
    sase_bug_bash    5/5  ■■■■■│                                  project · sase
  ROOM
    dev 4 · sase_memory 4 · sase_art 3 · sase_better_installs 3 · love 2 · … 12 more
  27 empty · not capped: gkeep_inbox 65 (ready_cap: off) · ↻ 11 recurring        (-a for all)

  Make room → bob ready sase_remote
  split Ctrl+Shift+N · sequence / defer / drop Ctrl+Shift+P
```

- When nothing is crowded, the header reads `CROWDED 0 ✓` in green and the CROWDED group disappears.
- Celebrating is legitimate here because, unlike a gated count, the lane count can't reach zero through
  neglect.

**`bob ready sase_remote`** prints a worklist in file order. Each `path:line` is jumpable.

```text
bob ready · sase_remote · 11/5 · 6 over · project (parent sase) · 11 ready

     1  sase_remote.md:21  Add full support for machines across the TUI and CLI!      fresh 1d  ^machines
     2  sase_remote.md:28  Implement follow-up memory changes recommended by `0gq`…   fresh 1d  ^memory
     …
    11  sase_remote.md:38  Share prompt history and PIW / LSP completions with fleet! fresh 1d

  also here: 1 pending · 2 blocked
  Make room for 6: split · sequence · defer · drop
```

**JSON** (`schema_version: 1`) is additive-friendly for Mac Capture and tmux:

```json
{
  "ok": true, "schema_version": 1, "date": "2026-10-01",
  "definition": "ready_lane",
  "cap": { "default": 5, "source": "config" },
  "totals": { "notes": 51, "crowded": 4, "full": 3, "room": 17, "empty": 27, "exempt": 3,
              "counted": 133, "excess": 66, "recurring": 11 },
  "notes": [
    { "path": "sase_remote.md", "name": "sase_remote", "kind": "project", "status": "wip",
      "parent": "sase", "count": 11, "cap": 5, "cap_source": "default", "state": "crowded",
      "over_by": 6, "make_up": { "ready": 11, "new": 0, "rotten": 0 }, "recurring": 0 }
  ],
  "warnings": []
}
```

**Exit codes:**
- 0 means the report succeeded. Crowded notes don't fail it, because it is a soft cap.
- 1 means a read or runtime failure.
- 2 means a usage or global-config error.
- 3 is returned only with `--check` when anything is crowded.

**Performance:** build on the shared rich-task scan that `bob freshness` already uses (2.1 s today). The
target is `bob ready` ≤ `bob plan`, with no extra full-vault scan per note.

### 5.4 `dash.md`: the `CROWDED` chip and `crowded.md`

**Chip.**
- New chip order: NEW, PENDING, NEXT, READY, **CROWDED ↗**, BLOCKED, ROTTEN, TODAY. It sits next to READY
  because it describes how the Ready lane is distributed.
- The primary number is a count of **notes**, not tasks, so it never reads as a second READY.
- States:
  - `CROWDED 4` uses the existing `task-count-over` red;
  - `CROWDED 0 ✓` is calm and muted;
  - `CROWDED –` means unavailable.
- Tooltip and accessible label:
  `4 notes over their ready cap: sase 61/5, sase_remote 11/5, sase_pager 7/5, sase_usage 7/5 · 3 full · 66
  over. Open Crowded Notes.`
- Rendering goes through `renderCrowdedChip`, with a guarded inline `–` fallback like the other chips.
- Adding a chip changes the chip list pinned by `ready-is-freshness-gated`, so a **new decision record**
  supersedes that list in part (§7).

**`crowded.md`** follows the `rotten.md` and `blocked.md` pattern, which keeps dash's sections a clean task
partition. Its body is:
1. A ` ```bob-ready-notes``` ` block rendered by ledger-tools: the same ranked bars as the CLI, with linked
   rows and hover previews. ROOM notes compress to one line of `name n` pills, and exempt notes appear
   dimmed.
2. A Tasks query of the crowded notes' lane tasks, grouped by note, through
   `filter by function app.plugins.plugins["bob-ledger-tools"]?.api?.noteReady?.forNote(task.file.path)?.state === "crowded"`.
   Clicking a task jumps to its source line, where Ctrl+Shift+P and Ctrl+Shift+M work.
3. A one-line footer with the four remedies.

The same block can be dropped into the weekly-review note.

### 5.5 In each area/project note: a live chip on `## Tasks`

ledger-tools adds a small chip at the end of the `## Tasks` heading line. In Live Preview it is a CM6 widget
decoration, the same mechanism as the freshness marks; in Reading view it is a markdown post-processor.

```text
## Tasks                                                     ready 11/5 · +6
[⚪ 11 open] · [🔵 1 next/wip] · [🔴 2 blocked] · [🟢 8 done/canceled]     ← hooks row, unchanged
```

| State | Look |
| --- | --- |
| room | muted, `ready 3/5` |
| full | muted with a label, `ready 5/5 · full` |
| crowded | red accent with an excess pill, `ready 11/5 · +6` |
| exempt | muted, `ready 65 · no cap` |
| unavailable | `ready –` |

- The tooltip spells out the count:
  `11 ready-lane tasks = 11 ready + 0 new + 0 rotten · cap 5 (Bob config) · 6 over · split, sequence, defer,
  or drop.`
- Clicking it opens `crowded.md`.
- Six notes have no `## Tasks` heading (`inbox`, `mac_inbox`, `gtd_daily`, `recur`, `job`,
  `needs_attn_tasks`). They get no inline chip; the CLI, `crowded.md`, and notices still cover them.
  Exempt `gkeep_inbox` does have one, so it shows the `no cap` chip.
- Rejected alternatives:
  - **Appending `/5` to the hooks badge row** (grk, gem): it is up to 15 minutes stale, runs only while the
    Mac is awake, and changing N would rewrite 84 notes.
  - **A `bob-ready` code block per note** (cdx, mus): it only reaches notes created from a template unless
    every existing note is rewritten.

### 5.6 Gesture feedback: prevention first, then one honest notice

**Prevention in the Ctrl+Shift+M picker.**
- Every area/project row gets a right-aligned, tabular-numeral pill: muted `3/5`, muted `5/5 full`, or red
  `11/5 +6`.
- The highlighted row adds the projection, `5/5 → 6/5`, in red if the move would land over the cap. The
  increment is the number of *counted* rows in the moved task trees, not the number of selected roots.
- Order, filtering, and fuzzy ranking are unchanged: the pill is information, not steering.
- Counts come from one cached snapshot per picker open.

**The notification rule** (cdx's precise rule, adopted). For each eligible note `p` touched by a successful
Bob command:

```text
warn      if after[p] > cap[p] ∧ after[p] > before[p]        (crossing or worsening)
progress  if before[p] > cap[p] ∧ after[p] < before[p]        (▼, or ✓ back to cap/cap when ≤ cap)
```

- `5 → 6` warns, `7 → 8` warns, `7 → 6` shows progress, and rewording a task at 7 does nothing.
- There is **no daily dedupe**. Under the lane definition only real lane changes can worsen a note, so the
  volume is naturally low, and each worsening deserves its feedback.
- Each command yields one composed notice, never one per note.
- Nothing appears after a cancel or rollback. After a partial apply, only the applied result counts.

**Which commands can change a note's count:**

| Command | Effect | Mechanism |
| --- | --- | --- |
| Ctrl+Shift+M and `N`Ctrl+Shift+M | +k at the destination, −k at the source | Synchronous projection: the before-snapshot plus the planned eligible rows. The plain-text notice becomes a `.bob-nh-notice` card |
| Alt+N release, or the Ctrl+Shift+P lane row (Next/Pending → Ready) | +k in each owning note | Projection, appended to the existing `NEXT 11/15 · PENDING 7/10` suffix |
| Ctrl+Shift+P priority or `scheduled` roll, cancel, `dependsOn` add | −1 (defer, drop, sequence) | Projection, with a progress chip |
| Ctrl+Shift+P / Ctrl+D clearing `scheduled` or `dependsOn` | +1 | Projection |
| Ctrl+Alt+Shift+N create project from task | −k in the source, +k in the new note | Projection; warns if the **new** note starts over its cap |
| Cycler Alt+]/Alt+[ into `[ ]`, Ctrl+Enter reopen, Ctrl+Shift+] promote bullet to task, completions that unblock dependents | ±k, possibly in other notes | `api.noteReady.watch(paths)` receipt: compare the before-snapshot with the first post-write snapshot for those paths, then emit |
| **Alt+F, Alt+Shift+F, `]s` (review)** | **0** | none, by definition |
| Hand edits, Obsidian Sync, hooks, `bob` CLI writes, mobile | any | **silent**: chips and counts update live |

**Copy and look.** These reuse existing notice tones and add one new `is-over` red chip tone.

```text
┌ ⤵ Moved 2 tasks → sase_pager ─────────────────────────────────┐
│  [ sase_pager ready 9/5 · +4 ▲2 ]   [ sase ready 59/5 ▼2 ]      │
│  split · sequence · defer · drop                                │
└──────────────────────────────────────────────────────────────────┘

→ Ready · 1 task · NEXT 11/15 · PENDING 7/10 · 🔴 sase_remote ready 12/5
Scheduled P2 · in 17 days   [ ✓ sase_remote back to 5/5 ]
```

- The plain-text fallback is
  `Moved 2 tasks to sase_pager · 🔴 sase_pager ready 9/5 · split, sequence, defer, or drop`.
- An over card stays 8 s. Notices announce without moving focus (WCAG status messages); verify that in the
  real Obsidian build.
- **The UI never offers "promote to Next" as a fix**, because that only relabels the load as commitment
  (cdx).

### 5.7 One visual language everywhere

| State | Meaning | CLI | Obsidian |
| --- | --- | --- | --- |
| room | `0 < count < cap` | dim cells | muted chip or pill |
| full | `count = cap` | cells up to `│`, `full` label | muted, `· full` text (**no amber**, per the READY badge rule) |
| crowded | `count > cap` | red overflow cells, `+k` | `task-count-over` red, `+k` pill |
| projected over | the picker's highlighted row would exceed | — | red `→ 6/5` |
| exempt | `ready_cap: off` | dim, `no cap` | muted, `no cap` |
| make-up | NEW or ROTTEN inside the count | dim `· 1 new` | tooltip and dim suffix |
| fixed | crowded → ≤ cap | `CROWDED 0 ✓` | `ok` chip `✓ back to 5/5` |

The words are the same everywhere: a note is **crowded**, **full**, or has **room**. The verbs are always
**split, sequence, defer, drop**.
- Numbers use tabular numerals with a fixed minimum width, so `4/5` → `11/5` doesn't make rows jump.
- Color always comes with text, for accessibility.
- Labels use theme variables, so light and dark themes both work.
- Motion respects reduced-motion settings.

### 5.8 Architecture

```text
config.yml plan.max_ready_per_note ─┐      ┌─ note frontmatter ready_cap / type / status
                                    ▼      ▼
           ┌─────────────────────────────────────────────────────┐
           │ ready-lane-per-note evaluator   (vectors R1–R12)     │
           │  Rust: src/native/note_ready/  ⇄  JS: api.noteReady │
           └───────┬───────────────────────────────┬─────────────┘
          bob ready (human/json/--check)    dash CROWDED chip · crowded.md block
          [later] bob plan line, capture    heading chip · picker pills · notices
```

**bob-cli:**
- `src/native/note_ready/` filters the shared `READY_QUERY` rich-task rows in memory and classifies notes
  with the projects scanner (extended to list and bare `type` forms).
- It attaches the make-up from the existing freshness bucket evaluation, and adds
  `PlanConfig.max_ready_per_note`.
- The command is `bob ready`. Docs go in `docs/plan.md` § "Ready cap per note".

**bob-ledger-tools:**
- Adds `api.noteReady` (namespace v1; the top-level api stays v3, additive). Consumers feature-detect it and
  degrade to `–`.
- Members:
  - `snapshot()`: `{available, cap, totals, notes[]}`;
  - `forNote(path)`;
  - `project(path, delta)` and `eligible(task)`;
  - `watch(paths)`;
  - `renderCrowdedChip`, `renderNoteChip`, and the `bob-ready-notes` processor.
- Build the result in **one O(tasks) pass**, memoized on the existing freshness memo keys: Tasks generation,
  local date, frontmatter generation, config, and Today stamp. That makes `forNote` an O(1) lookup.
- Refresh through the existing 150 ms debounced `cache-update` and the 60 s tick.
- **Gotchas found by the researchers:**
  - read `ready_cap` with `metadataCache.getFileCache(file)`, not the `getCache({path})` pattern that broke
    `task_refresh` (cld's bead `bob-cli-3e`);
  - cache `loadPlanCaps()` by mtime, because it re-reads `config.yml` on every call and this feature
    multiplies the callers.

**bob-navigation-hotkeys:** picker pills and projection; the Ctrl+Shift+M notice card; capacity chips for
Alt+N, Ctrl+Shift+P, and create-from-task.

**task-status-cycler:** `watch()` calls only.

**Vault:**
- the dash chip;
- `crowded.md`;
- `ready_cap: off` on the three inboxes;
- one line in the weekly prune chore: "check `bob ready -a`".

---

## 6. Alternatives considered and rejected

| Alternative | Verdict |
| --- | --- |
| Count gated READY per note (cdx, cld, mus) | Rejected. The rot cliff (§3.2) and the review incentive inversion (§3.3) |
| Count OPEN or SHOWN (`bob projects list`) | Rejected. Mixes Next, Pending, and hidden tasks (`sase` 262/124) |
| Separate area default (8 or 7; mus, gem) | Rejected for v1. No area exceeds 5 once inboxes and recurring are excluded. Use `ready_cap` if one ever does |
| Store `ready_task_count` in frontmatter via bob-project-tasks (gem) | Rejected. Time-varying (scheduled dates mature, deferrals return), write churn, and the decisions prefer read-time evaluation |
| Put `/5` in the hooks badge row (grk, gem) | Rejected as the primary in-note surface. A 15-minute Mac-only snapshot, and policy changes would rewrite 84 notes |
| Hard-refuse moves or confirmations | Rejected unanimously. It blocks the routing that fixes crowding, and Bob caps are soft |
| Auto-defer the overflow, or auto-split projects | Rejected. Makes Bryan's priority and outcome decisions for him and hides work |
| Show only the first five tasks per note | Rejected. Hides the work that needs review |
| Roll a parent's count up over its children | Rejected. Double counts and hides the parent's chowder list. `bob ready` shows the parent as context instead |
| A CROWDED Tasks section inside `dash.md`, or a callout above READY (gem, mus) | Rejected. Dash sections are a mutually exclusive task partition; `crowded.md` follows the BLOCKED and ROTTEN pattern |
| Fold the information into the READY chip (`READY 87/100 · 4▲`) | Rejected. One chip carrying two dimensions (volume and shape) makes "red" ambiguous |
| `bob projects load` or `bob backlog list` (grk, gem) | Rejected. Areas aren't projects, and `bob ready` is the user's own word |
| An active-note watcher that toasts on any edit (cld) | Narrowed to a `watch(paths)` receipt that only Bob commands request, so typing never toasts |
| Daily or 15-minute notice dedupe (mus, cld) | Rejected. A later `7 → 8` still deserves feedback, and the lane definition keeps volume low |
| An amber "at limit" color (cld) | Rejected. Bob's cap style has no intermediate warning color. The picker projection carries the at-limit case |
| A new Obsidian setting for N | Rejected. It would drift from the CLI; one config key plus vault-local overrides is enough |

---

## 7. Rollout, trial, and the `sase.md` question

The work spans bob-cli, bob-plugins, and the vault, so it is one epic. Each phase can ship on its own.

| Phase | Repo | Deliverable |
| --- | --- | --- |
| **1. Contract and CLI** | bob-cli | `docs/plan.md` "Ready cap per note" with R1–R12; `plan.max_ready_per_note`; the `ready_cap` frontmatter; lints `note_ready_cap_invalid` and `note_ready_in_terminal_project`; `src/native/note_ready/`; `bob ready`. **New decision record**, written through `/sase_memory_write`: "Per-note ready cap counts the note's Ready lane". It records the rejected alternatives above and partly supersedes `ready-is-freshness-gated` for the chip list only. Useful the next morning |
| **2. Read-only Obsidian** | bob-plugins (ledger-tools) + vault | `api.noteReady` v1; dash `CROWDED` chip; `crowded.md`; heading chip; `ready_cap: off` on the three inboxes; the `loadPlanCaps` mtime cache; deploy with `bob plugins sync` |
| **3. Gesture feedback** | bob-plugins (nav, cycler) | picker pills and projection; Ctrl+Shift+M notice card; Alt+N, Ctrl+Shift+P, and create-from-task chips; `watch()` in the cycler |
| 4. Optional | all | `bob plan` summary line `CROWDED k`; `note_ready` advisory in `bob capture` / `capture-targets` JSON for Mac Capture (a thin client, so it only renders the field); an IDLE-projects list under `bob ready -a` (GTD's floor rule; 17 of 41 active projects are idle today, so it stays informational) |

**Sequencing against the freshness trial (2026-10-05 → 10-18).** Phases 1–2 are read-only and can ship
anytime, with a line in the trial log. Phase 3 changes behavior: crowding nudges deferrals, which lowers
READY and could confound the trial's "red on ≤ 3 mornings" keep rule. Ship it after 10-18 unless Bryan
accepts the confound.

**`sase.md` first.** Without a triage pass, `CROWDED` starts as permanent wallpaper (`sase` is 56 of the 66
excess).
- Spend one GTD block on `bob ready sase`.
- Route clusters into the ~40 existing `sase_*` children with `N`Ctrl+Shift+M; the picker pills from phase 3,
  or `bob ready` before then, keep that from crowding the children.
- Create 2–3 new scopes where clusters appear, drop the stale ideas, and defer the rest.
- A dated transitional `ready_cap: 20` is acceptable only as a visible, temporary exception.

**Keep rule** (two weeks after phase 3):
- crowded notes other than `sase` reach 0 on ≥ 10 of 14 mornings;
- `sase`'s excess falls by ≥ 50%;
- notices Bryan would call noise stay at ≤ 1 per day;
- ≤ 3 notes carry a numeric `ready_cap` override. More than that means N is wrong, not the notes.

If it fails, tune N first, then the notice scope, before considering removal.

**Ritual change** (`docs/freshness.md` §6). The morning sequence becomes:
1. `bob gkeep pull`.
2. Clear NEW to 0.
3. Clear ROTTEN to 0 or the budget.
4. **New step: clear CROWDED to 0** with split, sequence, defer, or drop.
5. PENDING → NEXT.

Because the lane count ignores freshness, step 4 doesn't depend on how far step 3 got.

---

## 8. How the five reports were reconciled

| Question | Positions | Resolution |
| --- | --- | --- |
| What counts | Gated READY: cdx, cld, mus (mus with a SHOWN fallback). Ungated: grk (root `[ ]` intake), gem (`[ ]` including NEW) | **The Ready lane**, with the make-up shown. Lead's evidence: the rot-cliff simulation and the whole-lane precedent (§3) |
| Recurring | cdx counts it (exempt READY); the others exclude it | Exclude it and show `↻ k` |
| Nested rows | cdx and cld count each row; grk counts roots | Count each row, for dash parity. Moot today (0 nested rows) |
| Today | cdx, cld, and mus exclude it | Include it (whole lane). Effectively 0, because linking promotes to `[*]` |
| Inboxes | cld: frontmatter `off`; grk: config list; gem: route, pattern, or frontmatter; mus: scope; cdx: unaddressed | `ready_cap: off` on all three inbox notes (`mac_inbox` included; cld was wrong that it is untyped) |
| Area default | mus 8, gem 7; cdx, cld, and grk use the same default | The same 5. Measured: no area is over once inboxes and recurring are excluded |
| Config names | `plan.max_ready_per_note` (cdx, cld), `plan.note_ready.cap` (grk), `ready.max_per_project_note` (mus), `projects.max_ready_tasks` (gem) | `plan.max_ready_per_note`, sitting next to `max_ready`, `max_next`, and `max_pending`. Override key `ready_cap` (cld, gem) |
| CLI | `bob ready` (cdx, cld, mus); `bob projects load` (grk); `bob backlog list` / `projects list -o` (gem) | `bob ready` |
| Dash | chip → `crowded.md` (cld); LOAD chip → dash list (grk); OVERCAP chip and callout (gem); section (mus); summary strip (cdx) | `CROWDED ↗` chip → `crowded.md` |
| In-note | hooks row (grk, gem); live heading chip (cld); code block (cdx, mus) | Live heading chip; hooks row unchanged |
| Notice rule | crossing-only with daily dedupe (mus); every increase (cdx); a 15-minute throttle plus a watcher (cld); an allow-list (grk) | cdx's rule over every Bob command; projections for planned commands; a `watch()` receipt for the rest; silent for edits and background changes; positive progress (cld) |
| Cache lag | cdx: operation overlay or receipts; cld: before + delta | Before + exact delta, which is exact under the lane definition. A receipt only where no plan exists |
| `bob plan` | cld adds it; grk declines | Optional, phase 4 |
| Remedies | split and defer (the request); cdx adds dependencies and cancel | Four named verbs: split, sequence, defer, drop |

---

## 9. Open questions for Bryan

1. **`sase.md`:** one triage session before phase 3 (recommended), or a dated `ready_cap: 20` while you
   work it down?
2. **The name `CROWDED`.** It pairs with FULL and ROOM and reads naturally ("sase_pager is crowded").
   Alternatives are `LOAD` and `OVERCAP`. Rename freely before the chip ships.
3. **Phase 3 timing:** wait until the freshness trial ends on 2026-10-18 (recommended), or accept the
   confound and ship sooner?
4. **Is five right for areas over time?** The data says yes today. The keep rule's "≤ 3 overrides" check
   will tell.

---

## 10. Recommended solution

Build **ready-lane-per-note**: for every area note and non-terminal project note, count the Ready `[ ]`
tasks that are visible and pullable (not hidden, not blocked, not future-scheduled), **whatever their
freshness**, by the file that holds them.
- Recurring and `^prj` tasks are excluded.
- Inboxes are exempt through `ready_cap: off`.
- The cap is `plan.max_ready_per_note: 5`, with an optional per-note `ready_cap:`.
- A note is **crowded** above its cap, **full** at it, and has **room** below it.
- The limit is soft and evaluated at read time. Nothing is refused, written to tasks, or stored, and
  "unavailable" is never shown as zero.

Implement it twice, natively in Rust and as `api.noteReady` in bob-ledger-tools, pinned by shared vectors
R1–R12.

Surface it at the moments that matter, in this order:

1. **`bob ready`**: a colored bar view (CROWDED / FULL / ROOM), a per-note worklist, JSON, and `--check`.
2. **The `dash.md` `CROWDED k ↗` chip** opening **`crowded.md`**, plus a live **`ready n/5`** chip on every
   area/project `## Tasks` heading.
3. **Prevention and feedback:**
   - `n/5` pills with a projection in the Ctrl+Shift+M picker;
   - one consolidated capacity chip in the notice of any Bob command that makes a crowded note worse;
   - `▼` / `✓ back to 5/5` progress when a command makes one better;
   - review stamps and hand edits never toast.

Name the four remedies everywhere: **split, sequence, defer, drop**. Add "clear CROWDED to 0" to the morning
ritual after NEW and ROTTEN. Triage `sase.md` once before turning the notices on. Record the choice in a new
decision record that partly supersedes `ready-is-freshness-gated` for the chip list.

---

## Sources

- **Researcher reports** (this directory):
  - `per_note_ready_cap__cdx.md`: counting contract, notification rule, accessibility, cache lag;
  - `per_note_ready_cap__cld.md`: live data, CROWDED/FULL/ROOM vocabulary, `crowded.md`, heading chip,
    rollout;
  - `per_note_ready_cap__grk.md`: the ungated intake argument, the whole-vault histogram, the in-note badge;
  - `per_note_ready_cap__mus.md`: soft-limit framing, toast fatigue, phasing;
  - `per_note_ready_cap__gem.md`: area/inbox distinctions, picker-first prevention.
- **Lead verification (2026-10-01):**
  - `bob query --tasks` with `READY_QUERY` grouped by path (211 rows, 0 nested);
  - `BOB_NOW=… bob freshness list -f json` for 10-01, 10-02, 10-04, 10-05, 10-07, and 10-08 (the rot-cliff
    simulation);
  - vault frontmatter scan (51 eligible notes; inbox typing);
  - hooks `⚪ open` badges;
  - `~/bob/.obsidian/hotkeys.json` (Ctrl+Shift+N, Ctrl+Alt+Shift+N);
  - `dash.md` chip definitions;
  - `bob --help`.
- **bob-cli:**
  - `docs/plan.md` § Lanes (whole-lane caps), § READY backlog (no intermediate color; lane pressure);
  - `docs/freshness.md` §§4–6;
  - `docs/projects.md` (priority rolls, create project from task);
  - `docs/task-status-hooks.md` § Status Grouping (snapshot badge row);
  - `docs/vault-git-sync.md` (15-minute Mac cron);
  - `src/native/dataview/tasks/mod.rs` (`READY_QUERY`);
  - `src/native/capture_targets.rs`.
- **bob-plugins @ 4744607:**
  - ledger-tools `readyTaskVisible`, `readyCountFromTasks`, `readyBadgeModel` (lane tooltip);
  - navigation-hotkeys `readLaneBudgets`, `collectTaskMoveDestinations`, and the plain-text move notice at
    `commitTaskMoveSession`.
- **Decisions:** `ready-is-freshness-gated`, `task-lanes-are-sticky`, `today-is-read-from-the-ledger`; the
  glossary entry for freshness; `cli_rules.md`.
- **External:**
  - Ryan Singer, *Shape Up*, "Map the Scopes" (<https://basecamp.com/shapeup/3.3-chapter-12>);
  - David Allen Company, "Managing projects with GTD"
    (<https://gettingthingsdone.com/2017/05/managing-projects-with-gtd/>);
  - The Kanban Guide (<https://kanbanguides.org/the-kanban-guide/>);
  - W3C WCAG 2.2 Understanding: Use of Color and Status Messages.

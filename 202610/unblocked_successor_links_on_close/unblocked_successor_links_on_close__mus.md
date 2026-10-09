# Auto-creating task links for dependents of closed tasks

Research report — researcher `mus`. Date: 2026-10-09.

Request: when a task is closed, automatically create Task Links (Pomodoro
ledger links in today's daily file) for the tasks that depend on it, with
a toast naming what was added and why, working from both `<Ctrl+Enter>` in
Obsidian and `bob capture`'s `=x!` / `=!` syntax, placed in the closed
task's Pomodoro (or a newly created one), fast enough to keep
bob-mac-capture blazing fast.

Verdict up front: **yes, build it, but narrowed**. Link only the
newly-unblocked dependents (not every dependent), never auto-start a timed
session, and reuse the closed entry's name for any created entry. The
un-narrowed version — link every dependent, mint fresh Pomodoros freely —
would fight the plan budget, the sticky-lane discipline, and the tiered
review walk. Details and the full recommendation are in §7.

## 1. What exists today

### 1.1 Three close paths, two post-close behaviors

There are three ways to close a task, and they do not all do the same
cleanup afterwards:

| Close path | Engine | Ledger retirement | Blocked-dependent recovery |
|---|---|---|---|
| `<Ctrl+Enter>` in Obsidian (task-status-cycler plugin, JS) | plugin-local | scoped, plugin-local | yes, narrow + immediate (to Ready) |
| `bob capture '!note:id'` (`=!`-family whole-item completion) | shared Rust engine `src/native/task_complete/` | scoped (`retire_completed_links`) | yes (`recover_blocked_dependents`, same rule as the cycler) |
| `bob capture '=x!N'` (Pomodoro close with completion selection) | `src/native/capture/pomodoro_close.rs` + `src/native/capture_pomodoro_close/linked_tasks.rs` | its own logic | **no** — this path never calls the shared engine's recovery |

The shared engine is explicitly documented as "the single home for what
completing a task writes: the embedded tree close, the scoped ledger
retirement, and the Blocked-dependent recovery" (`src/native/task_complete/mod.rs`).
The `=x!` path predates it (or was never ported) and closes linked tasks
through its own code. Any auto-link feature that only hooks the shared
engine will therefore behave differently depending on how the user closed
the task — exactly the inconsistency this feature must not ship with.

### 1.2 Dependent recovery already defines the candidate set

`recover_blocked_dependents` (`src/native/task_complete/recovery.rs`)
reuses reconcile's `FileScan`/`TaskLine` types and one definition of "open
dependency". A dependent recovers (Blocked `[?]` → Ready `[ ]`) only when
it directly names a completed task's `[id::]`, has **no other open
dependency** in the post-completion snapshot, and has **no strictly future
`scheduled` date**. This is the same rule the cycler's `<Ctrl+Enter>`
recovery implements in JS (`docs/task-status-hooks.md`, "Ctrl+Enter
recovery"). The capture `!` path already reports these as `unblocked` in
its JSON (`docs/capture.md` dry-run example shows `"unblocked": []`).

So the hardest sub-problem — "which dependents just became actionable?" —
already has one agreed-upon answer in both Rust and JS. The new feature
should reuse that set, not invent a second definition.

### 1.3 The ledger model constrains placement

The ledger is the lines of today's daily note from `## Pomodoros…` to the
next `##` heading (`docs/plan.md`). Only block links (`[[target#^id]]`)
on indented lines below an **open** entry count; links under completed
entries are history. `bob task reconcile` owns Blocked recovery,
completed-reference retirement, de-duplication across open Pomodoros, and
promotion of Pomodoro roots' prerequisites to Next/In Progress. Lanes are
sticky: linking raises Ready/Blocked to Next, and only an explicit release
returns them (`decisions:task-lanes-are-sticky`). Today is read from the
ledger at read time, never written to tasks
(`decisions:today-is-read-from-the-ledger`).

Consequences: (a) inserting a link under a completed entry is silently
meaningless — placement must target an open entry; (b) every inserted link
has downstream effects (Today membership, Next promotion, plan-budget
counts against 3 themes / 10 links); (c) reconcile already promotes
*prerequisites of roots*, so linking a still-blocked dependent would
cascade-promote its remaining prerequisites — a reason to link only
fully-unblocked dependents.

### 1.4 The thin-client contract dictates the toast path

Per `decisions:mac-capture-is-a-thin-client`, bob-cli owns all grammar,
preview, and mutation; bob-mac-capture renders what `bob capture
--format json` returns and submits each draft as one aggregate call
(~5 ms spawn measured; 20 s timeout). JSON grows additively; the app
decodes new fields with `decodeIfPresent`. So the mac toast content must
arrive as additive JSON fields on the existing `task_complete` /
`pomodoro_close` results — no Swift-side vault logic, no second
implementation. In Obsidian, surfaces use `Notice` (established pattern in
the vault's plugins); the cycler already emits recovery notices and must
extend that copy.

## 2. Critique of the plan as stated

1. **"Tasks that depend on tasks that we close" is too broad.** A
   foundational task can have many dependents, several still blocked on
   other prerequisites or future-scheduled. Auto-linking all of them
   floods the ledger, blows the plan budget, and puts still-`[?]`
   tasks into Today where they cannot be worked. The meaningful event
   is not "dependent exists" but "dependent just became actionable".
2. **"In the current daily file" needs disambiguation.** Tasks almost
   never live in the daily file; their *links* do. The sane reading is:
   trigger on closing a task that holds a Task Link in today's ledger,
   search dependents vault-wide (a dependent in a project note is the
   normal case), and write only to the day file. If the intent was
   literally "only dependents defined in the daily file", say so — it
   would make the feature nearly useless, since dependents live in area
   and project notes.
3. **"Or the newly created pomodoro" is the riskiest clause.** Creating
   an entry implicitly raises naming, timing, and budget questions: what
   name (a new theme?), timed or queued, and does it steal highlight /
   running status? Auto-starting a timed session as a side effect of
   closing work is surprising and corrupts time tracking. This clause
   needs a conservative form (see §7).
4. **The `=x!` path is silently out of scope of the shared engine.**
   As §1.1 shows, hooking only the engine leaves `=x!`/`=!` — the exact
   syntax the request names — without the feature. The request's two
   syntaxes live in two different engines today.
5. **`<Ctrl+Enter>` is JS, not Rust.** The cycler recovers dependents
   plugin-locally (reading open buffers, preserving the cursor). There
   is no documented `bob` subcommand that inserts ledger links from
   Obsidian today; either the plugin shells to a new bob command and
   applies structured edits, or it reimplements link-form selection in
   JS against the dependency contract (the codebase already accepts
   mirrored JS logic: the Depends-On grammar lives in
   bob-navigation-hotkeys, the chip model in bob-ledger-tools).
   Either way it is a second implementation to keep in sync — the cost
   center of this feature.
6. **"Beautiful" toasts need copy design, not just plumbing.** The
   toast must answer *why* ("unblocked by closing X"), name each added
   link's destination entry, and stay quiet when nothing qualified.
   A toast per closed task during a bulk `=x!` close is notification
   spam; bulk closes need one aggregated toast.

## 3. Proposed requirement adjustments

1. **Link only newly-unblocked dependents** — the exact set that
   `recover_blocked_dependents` (Rust) / the cycler recovery (JS)
   flips to Ready in the same operation. Dependents that stay Blocked
   are never linked. This bounds the blast radius and makes the toast's
   "why" truthful: *these tasks are now actionable because you closed X*.
2. **Deduplicate before inserting**: skip a dependent that already has
   a live link under any open entry (same `(target, block-id)` identity
   reconcile uses), and report it as `already_linked`, not as added.
3. **Never auto-start a timed session.** Placement order: (a) the
   closed task's own entry if still open; (b) the running entry;
   (c) the next open entry in file order; (d) only if none is open,
   create one new **untimed, queued** entry reusing the closed entry's
   name (same theme — no plan-budget surprise), holding the new links.
   No time range, never highlight-stealing beyond normal first-open
   rules.
4. **One aggregated toast per operation**, in both surfaces, with a
   stable copy shape: `Unblocked N task(s) by closing “X” — linked under
   ENTRY: a, b` plus a quiet `No newly-actionable dependents` absence
   (log-only, no toast) when the set is empty. Bulk `=x!` closes group
   by entry.
5. **Dry-run parity**: `bob capture --dry-run -f json` reports the
   planned links byte-identically to the real run's plan, like
   `task_blocks`/`pomodoro_blocks` do today. The Obsidian path previews
   in its existing confirmation surfaces where they exist.
6. **Cap and refuse gracefully**: a configurable cap (default 5 links
   per operation, mirroring the per-note Ready-cap spirit in
   `decisions:note-ready-cap-counts-the-lane`) with overflow reported
   as `deferred_over_cap` rather than silently dropped or ledger-flooding.

## 4. Design sketch

**Rust (source of truth).** Add a pure planner, e.g.
`task_complete::plan_dependent_links`, taking the staged post-completion
snapshot (already built for recovery — no new vault scan), the
`RecoveredDependent` set, and the parsed ledger; returning link insertions
as (entry, `[[form#^id]]` line, anchor) triples plus a report struct
(`linked`, `already_linked`, `deferred_over_cap`). Link form follows the
dependency contract's shortest-unambiguous rule (§3 of
`docs/task-dependencies.md`). Wire it into **both** `capture/task_complete.rs`
(`!` path) and `capture/pomodoro_close.rs` (`=x!` path — this also closes
the recovery gap in §1.1 by routing `=x!` completions through the shared
engine's recovery + retirement, the cleanup the engine's module docs say
is its job). Insertion reuses the staged batch writer, so the whole
capture stays atomic with rollback.

**JSON (toast fuel).** Additive objects next to `unblocked`, e.g.
`"dependent_links": {"entry": "CAPTURE", "created_entry": false,
"linked": [{"text": "…", "block_link": "[[sase#^id]]"}],
"already_linked": […], "deferred_over_cap": […]}`. New `pomodoro_blocks`
roles cover the created-entry diff. Mac renders the toast from this and
nothing else.

**Obsidian (`<Ctrl+Enter>`).** Extend the cycler's post-close step: after
its local recovery set is known, call a new read-only-then-write bob
entry point (preferred: `bob task link-dependents --json` taking completed
ids + day file, emitting the same insertion triples the plugin applies to
open buffers with cursor preservation), falling back to the mirrored-JS
insertion only if spawning bob from the plugin proves infeasible — to be
settled by prototype, since it determines the sync cost of this feature.
Toast via the existing `Notice` row renderer.

## 5. Performance

The binding constraint is real but narrow. The `!` path already pays for
a vault-wide note resolution plus a staged snapshot scan for recovery;
the reverse-dependency index (`[id::]` → open dependents) is a single
linear pass over that same `FileScan` set, and link-form resolution
touches only the few recovered dependents, not the vault. Marginal cost
per close should be sub-millisecond on top of work already done — the
existing ~5 ms spawn budget is undisturbed, and no new scan means
bob-mac-capture stays blazing fast. Rules to keep it that way: never
rescan the vault for this feature (reuse the batch snapshot); resolve
shortest-form links only for inserted dependents; cap insertions (§3.6)
so pathological fan-out cannot turn a close into a write storm. The risk
is concentrated in the Obsidian path: if the cycler must spawn bob once
per `<Ctrl+Enter>`, measure that spawn on the Mac before committing to
it; the fallback (JS-local insertion over already-open buffers) exists
precisely to protect keypress latency.

## 6. Edge cases that must be specified before implementation

- Dependent already linked under another open entry → skip as
  `already_linked` (reconcile's dedupe would remove a double-insert
  anyway; don't create churn it has to clean).
- Dependent closed or cancelled between scan and write → skip
  (snapshot staleness guard, same quiet-interval ethos as the hooks'
  2 s deferral).
- Closed task had no ledger link (e.g. closed in its home note, `!`
  with no link) → fall back to running → next-open → create-queued (§3.3).
- Entire entry closed by `=x!` with several completed tasks sharing
  dependents → aggregate per destination entry, one toast.
- Unresolvable/unencodable link targets and `done/`-archived
  prerequisites → follow the existing warning taxonomy
  (`unresolved_dependency_link`, archive-target rules); never block the
  close on link planning.
- Recurring tasks refuse completion already; their dependents are
  unaffected — keep that.
- Plan-budget overflow caused by insertions → insertions still land
  (refusing user-meaningful links over a soft budget cap would be
  wrong), but `plan_budget.status: over` plus the toast must say so.

## 7. Recommended solution

Ship it in three slices:

1. **Rust core + `!` path** (small, self-contained): pure
   `plan_dependent_links` planner with unit vectors copied from the
   dependency contract, wired into `capture/task_complete.rs`, additive
   `dependent_links` JSON, dry-run parity, cap default 5. This alone
   delivers mac-app toasts end to end, since the app only renders JSON.
2. **`=x!` convergence**: route pomodoro-close completions through the
   shared engine's recovery + retirement + the new planner. This fixes
   a latent inconsistency (closes via `=x!` currently skip dependent
   recovery entirely) and is arguably a bug fix wearing a feature's
   coat — call it out as such in the plan.
3. **Obsidian `<Ctrl+Enter>`**: prototype the `bob task
   link-dependents --json` entry point against keypress-latency
   measurement; ship whichever of bob-spawn or mirrored-JS insertion
   measures under ~50 ms p95 on Bryan's vault, with the `Notice` copy
   from §3.4.

Do not ship a version that links still-blocked dependents, mints timed
Pomodoros, or bypasses dry-run parity — each converts a delightful
"your next task is queued" moment into ledger spam Bryan must manually
undo, which is exactly what the sticky lanes and the tiered review walk
exist to prevent.

## 8. Open questions for Bryan

1. Should the created queued entry reuse the closed entry's name (§3.3),
   or a fixed name like `FOLLOW-UP` (a new theme, but greppable)?
2. Default cap 5 per operation — higher, lower, or uncapped with only
   a toast warning?
3. Should dependents that are still Blocked on *other* prerequisites
   ever be linked (my recommendation: no), or previewed somewhere for
   planning purposes?

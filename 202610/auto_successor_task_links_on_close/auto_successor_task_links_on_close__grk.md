# Auto-queue successor Task Links when a today-ledger task is completed

*Researcher: grk · 2026-10-09 · independent swarm report*

**Verdict.** Yes — this is a good idea if it is a *flow continuation*, not a
second Today-inference engine. Implement it as one shared **Successor Queue**
step in bob-cli's existing task-completion engine, with a fast reverse-dep
lookup, a Tasks-cache mirror in Obsidian, and additive JSON so Bob Mac Capture
stays a thin, preview-first client. Auto-link only *fully unblocked* dependents
of a task whose dedicated Task Link in *today's* daily file was just completed.

---

## 1. Recommendation in one page

When Bryan completes a task that is on today's Pomodoro ledger — via
Ctrl+Enter on that Task Link, or via `bob capture` `=x!` / `=!` — Bob should
immediately queue the work that was waiting on it.

**Do this:**

1. Treat the trigger as *a dedicated Task Link in today's daily file was
   completed*, not "any task close anywhere."
2. Find **direct** dependents that name the completed identity, and that have
   **no remaining open prerequisite** and **no future `scheduled` date**.
3. Recover those Blocked `[?]` rows to an open lane (existing Ctrl+Enter /
   `!note:id` recovery), then insert a dedicated Task Link for each eligible
   successor into the **same open Pomodoro** that held the completed link, or
   into the **next session** the close already creates/selects when that
   Pomodoro is closed.
4. Raise Ready (and recovered-from-Blocked) successors to Next with the same
   rule `@route:block-id` already uses. Leave Next / In Progress as they are.
5. Tell Bryan *which* links were added and *why*, in one beautiful surface:
   an Obsidian notice card, and Mac Capture's close preview + notification.
6. Keep Mac Capture blazing fast by **never** cloning the whole vault on an
   `=x` preview. Scan only notes that already contain a Depends-On line or
   `[dependsOn::]`, and only when the close actually completes at least one
   numbered link.

**Do not do this:** dump every remaining-blocked dependent onto Today (that
silently promotes leftover prerequisites to Next); auto-link inbox /
`#hide` / recurring / already-today rows; walk the whole vault on every
keystroke of `=x!`; invent a new capture subcommand; or implement the
policy twice with two different eligibility rules.

---

## 2. Is this a good idea?

**Yes, with a tight trigger.** The current system already understands
"finishing a blocker unblocks a dependent" (Ctrl+Enter recovery, `!note:id`
unblocked rows, cancel-notice `unblocked N dependents` chips). What it does
*not* do is put that newly freed work onto the only surface that means
"I'm doing this now": a dedicated Task Link under an open Pomodoro
(`decisions:today-is-read-from-the-ledger`).

That gap is real. After `=x!1` or Ctrl+Enter on `[[sase#^fix-flaky]]`, the
dependent becomes Ready `[ ]` (or waits for `bob task reconcile`) and then
sits in the Ready/NEW pool until Bryan remembers to link it. The
dependency graph said "this is next"; Today never heard.

The idea is *not* a rerun of the failed `#now` automation
(`decisions:now-tag-is-user-owned`, later superseded). That inferred a
weekly bet from leftover activity, silently, on a hook. This fires on an
**explicit complete gesture**, only for tasks Bryan already put on today's
ledger, and it shows a toast. The closest ancestor is review-walk auto-advance:
a completing keystroke does one extra, visible, undo-aware thing.

**The real cost is sticky Next.** Linking a Ready task raises it to Next,
and nothing but Alt+N releases it (`decisions:task-lanes-are-sticky`). A
wrong successor is not a cosmetic extra bullet; it is a lane commitment.
The design below exists to keep that cost small: fully-unblocked only, skip
inbox, cap against `plan.max_links`, preview before capture submit, and a
toast that names every queued task.

I would still build this. I would not build the naive version ("every
dependent of everything we close, always, vault-wide").

---

## 3. Requirement adjustments

Each item is a change to the stated request. The rest of the report assumes
these.

### A1. Trigger is "a today Task Link was completed," not "Ctrl+Enter anywhere"

The request names Ctrl+Enter and `=x!` / `=!`. Those are the two gestures
that complete a **numbered / dedicated Task Link on today's ledger**.

**Keep:** Ctrl+Enter on a Pomodoro Task Link in today's daily file;
`bob capture '=x!…'` / `'=!'` completing numbered lineup rows.

**Also include (recommended):** whole-item `!note:block-id` completion
*when that task currently has a dedicated Task Link under today's open
Pomodoros*. It already closes "exactly as `=x!N` would" (`docs/capture.md`),
already retires the ledger link, and already recovers dependents. Leaving
it out would make Mac Capture's `!` picker and `=x!` disagree.

**Exclude:** Ctrl+Enter on a source `#task` line in a project note that is
*not* linked today; Ctrl+Enter on a Depends-On line (root-only close of a
*prerequisite*, by contract); park (`=*`), drop (`=~`), plain `=x`
(starts remaining links, does not complete them); Cancel `[-]`. Cancelling
a blocker unblocks dependents, but it is not "I finished this, pull the
next work into the session."

### A2. Queue only *fully unblocked* successors

Do not link a dependent that still waits on another open task or a future
`scheduled` date.

Linking a still-Blocked task under today's Pomodoros **raises its remaining
open prerequisites to Next** (`docs/task-dependencies.md` §5, "Promotion").
That is a silent second automation, and it is the wrong one: Bryan finished
A, and Bob would start promoting C, D, E because B still waits on them.

Fully unblocked is the only rule that matches the toast copy "because X
finished."

### A3. Close-path recovery is in scope for `=x!`

Ctrl+Enter and `!note:id` already recover Blocked dependents to Ready.
**Pomodoro close does not.** `src/native/capture_pomodoro_close/linked_tasks.rs`
runs `complete_embedded_trees` and never calls `recover_blocked_dependents`.
Hooks later derive Blocked away, but that is not immediate and not in the
close JSON Mac Capture already knows how to show (`unblocked` rows exist
only on `task_complete`).

Successor Queue should run *after* the same recovery the other two complete
paths use. Folding recovery into `=x!` is a correctness fix the new
feature needs, not a drive-by.

### A4. Skip inbox, `#hide`, recurring, missing block id, already-today

Inbox files await triage (`glossary:inbox-file`). Auto-linking an unrouted
inbox dependent skips the route picker that every other inbox gesture uses.

`#hide`, recurring (`[repeat::]` / `🔁` — capture already refuses to
complete those), tasks with no `^block-id` (cannot form a Task Link), and
tasks already present as a dedicated link under *any* of today's **open**
Pomodoros are skipped and, when the skip is surprising, named on the toast.

### A5. Respect the plan-link cap; do not invent a second Today

`plan.max_links` defaults to 10 distinct open Task Links
(`docs/plan.md`). Auto-queue must stop at the remaining slots and report
overflow (`+2 unblocked, not queued · 10/10 links`). Being *over* is a
lint, not a refusal, for hand links; for *automation* it should refuse
further inserts. A separate hard successor cap of 5 (same default as
`max_ready_per_note`) is a backstop against one popular blocker waking a
fan-out.

### A6. Destination is the owning session, with one close-path clarification

**Ctrl+Enter (session stays open):** insert into the *same* Pomodoro that
owns the completed Task Link, immediately after the struck bullet, so the
chain is readable:

```markdown
- [ ] (**0920-0950**) — CAPTURE
  - ~~[[sase#^fix-flaky]]~~
  - [[travel#^book-flights]]
  - [[sase#^still-running]]
```

**`=x!` (session closes):** the closed entry is history. Queue into the
session the close planner already chose as `next_pomodoro`:
- the newly created named/unnamed placeholder when the close creates one
  (`should_create = !carried_lines.is_empty() || later_entry.is_none()` in
  `ledger.rs`);
- otherwise the next already-open entry.

If the close creates a placeholder whose only child is the empty
`- ` sub-bullet, *replace* that placeholder child with the successor
links. After carried In-Progress links, append successors (carried work
stays first).

This is a small clarification of "newly created pomodoro if the entire
pomodoro … was closed": when a later open Pomodoro already exists and
nothing is carried, Bob does not create a new one today, and successors
should follow that existing next session rather than invent a second
placeholder.

### A7. No new `bob capture` subcommand; JSON stays schema 1 additive

`sase/memory/cli_rules.md`: never add a subcommand under `bob capture`.
Mac Capture is a thin client of `bob` (`decisions:mac-capture-is-a-thin-client`).
The feature is a new *step* inside existing complete/close execution, plus
additive `successors` / `successors_skipped` on `pomodoro_close` and
`task_complete`. Older clients ignore the fields.

### A8. Do not spawn `bob` from Ctrl+Enter

Shelling out to `bob capture '!note:id'` from the keymap would serialize
behind a process start and a vault walk, and it would fight the open
editor buffer. Obsidian already has the Tasks cache, open buffers, and
`planExplicitPomodoroLinkInsertion` in block-id-prompt. Mirror the
engine there with shared vectors, the same way Depends-On already works.

---

## 4. What the system does today

### 4.1 Vocabulary

A **Task Link** is a block link to a task. When it is the only content of
a depth-1 bullet under a Pomodoro, it is a ledger row
(`glossary:task-link`). Today is those dedicated links under **open**
Pomodoros (`docs/plan.md` §Today).

A **Task Dependency Link** is a Task Link on a managed
`⛓️ **DEPENDS ON:**` first-child line. It is a prerequisite, never a
Pomodoro Task Link, and closing the dependent never closes the targets
(`glossary:task-dependency-link`, `decisions:task-deps-are-depends-on-links`).

The feature is the reverse of today's "forward promotion": not "linking a
dependent raises its prerequisites," but "completing a prerequisite queues
its dependents."

### 4.2 Three complete paths, three different aftermaths

| Path | Completes tree | Retires today links | Recovers `[?]` dependents | Queues successors |
| --- | --- | --- | --- | --- |
| Ctrl+Enter on a Task Link (task-status-cycler `handleActiveTaskBlockLinkOpenDone`) | yes (embedded tree under a Pomodoro) | strikes the active link; `finalizeClosedTasks` retires others | yes, to Ready | **no** |
| `bob capture '!note:id'` (`src/native/capture/task_complete.rs`) | yes, shared `task_complete` engine | yes, `retire_completed_links` | yes, `recover_blocked_dependents` | **no** |
| `bob capture '=x!…'` / `'=!'` (`capture_pomodoro_close`) | yes, `complete_embedded_trees` | struck in the closed entry | **no** | **no** |

The shared engine comment in `src/native/task_complete/mod.rs` is explicit:
it owns "the embedded tree close, the scoped ledger retirement, and the
Blocked-dependent recovery." Successor Queue is the missing fourth step.

Recovery's rule (Rust and JS, kept in sync by
`docs/task-status-hooks.md`): only Blocked dependents that *directly* name
a completed `[id::]`, have no other open dependency in the post-close
snapshot, and have no strictly future `scheduled` date; they recover to
Ready. Unresolved ids never block. This is the right eligibility core;
Successor Queue should use it and then *also* accept dependents that were
already open (hand-unblocked, or hooks not yet run) if they still name the
completed id and are fully unblocked after this close.

### 4.3 How a Task Link is inserted today

bob-cli: `plan_pomodoro_link_ledger` /
`insert_link_into_entry` (`capture_task_toggle`). Idempotent: skip if the
destination entry already contains the wikilink. Ready/Blocked rise to
Next; Next/In Progress keep their lane (`capture/task_toggle.rs`).

Obsidian: `planPomodoroLinkInsertion` /
`planExplicitPomodoroLinkInsertion` (block-id-prompt). The explicit-target
variant is what Successor Queue needs: "insert into *this* entry,"
including a just-created placeholder.

Reuse these writers. Do not invent a third insertion grammar.

### 4.4 Toasts and Mac Capture already have an "unblocked" language

- Cancel notice cards already chip `unblocked N dependents`
  (`bob-navigation-hotkeys` `buildCancelNoticeModel`).
- Ctrl+Enter completion itself is mostly silent on success, except the
  review-walk landing toast (`continueReviewWalkAfter` composes `outcome.notice`
  into one toast). Failure notices exist ("blocked dependents could not be
  checked").
- Mac Capture `CaptureTaskCompletePresentation` already renders unblocked
  rows as `[?] → [ ]  Waiter` and appends `unblocked Waiter` to the
  notification body. Close cards (`CapturePomodoroClosePresentation`) already
  show numbered outcomes, a next-session line, and a notification.
- Capture JSON is schema version 1, additive-only; Mac Capture decodes
  missing fields as empty.

The UX problem is not "we have nowhere to say this." It is "Ctrl+Enter
says nothing when it succeeds, and `=x!` does not even recover."

### 4.5 Performance as it stands

`recoverBlockedDependentsNow` (Obsidian) reads **every markdown file**
through `vault.cachedRead` on every close. That is already the slow path
Ctrl+Enter pays. Do not copy it into `=x!` live preview.

`DependencyContext::recovery_base_snapshot` (bob-cli `!` complete) walks
`task_status_hooks::markdown_files` and clones the vault into a
`BTreeMap` **once per capture batch**. Fine for a single `!note:id`.
Fatal if it runs on every Mac Capture keystroke of `=x`.

Mac Capture's close preview is `bob capture --dry-run --no-clip --format json`
on each draft change (`CapturePomodoroClosePresentation` docs). Today's
close planner reads the daily note plus the few linked task notes. That
is the budget Successor Queue must keep.

The Depends-On stage already proves a fast reverse lookup is possible:
Tasks plugin cache (`getTasks()` when Warm), open buffers override, no
disk read on a keystroke (`docs/task-dependencies.md` §6.2).

---

## 5. Recommended design: Successor Queue

Name the step **Successor Queue** in docs, JSON, and toasts. "Auto task
links" is the mechanism; "successors" is the user-facing why.

### 5.1 Engine (bob-cli)

Add `src/native/task_complete/successors.rs`, called from the shared
completion engine after tree-close + retirement + recovery.

**Inputs**

- completed identities: `(path, block_id, id_field)` for every task this
  gesture actually closed (root *and* closed embedded subtasks);
- the post-close staged snapshot, or a *filtered* note set (see §6);
- today's daily note post-image and the destination Pomodoro
  (owning open entry, or `next_pomodoro` from the close plan);
- `today`, Tasks settings, `plan.max_links`.

**Outputs** (pure plan, then the caller stages)

- `queued`: each successor with `block_link`, destination line/name,
  previous and new status, `because` (the completed task's display text
  and id);
- `skipped`: `{ reason, text, locator }` for inbox / hidden / still-blocked /
  already-linked / no-id / over-cap / recurring;
- day-file post-image and any task-line status promotions.

**Eligibility (all of)**

1. Direct dependent: the completed id is on the Depends-On line or in
   `[dependsOn::]` (same set recovery uses, including R8 legacy children).
2. After treating this gesture's completed ids as closed, **no open
   prerequisite remains** (unresolved ids do not block).
3. No strictly future `scheduled`.
4. Open completable status after recovery (` `, `*`, `/`, and recovered
   from `?`). Not done, not cancelled.
5. Has a unique `^block-id` in its note.
6. Not an inbox file (`api.inboxRoute.isInboxNote` / capture's inbox
   classification).
7. Not `#hide`.
8. Not recurring.
9. Not already a dedicated Task Link under any of today's **open**
   Pomodoros.
10. Fits in remaining `plan.max_links` slots and the successor cap (5).

**Status write.** Reuse the link-toggle rule: `' '` or `'?'` → `'*'`;
`'*'` and `'/'` unchanged. Stamp `[fresh:: today]` the way
`plan_task_link` already does, so the successor does not look NEW.

**Idempotence.** A second Ctrl+Enter, a dry-run then a real run, or a
batch that completes A and C when B depends on both, queues B once.

### 5.2 Call sites

**Pomodoro close.** After `complete_embedded_trees` and the ledger
rewrite (so `next_pomodoro` exists), recover dependents over a *filtered*
snapshot, then queue into `next_pomodoro`. Only run when at least one
numbered row has outcome `complete`. Parked/dropped/in-progress rows do
not queue.

**`!note:id`.** After existing recovery, queue only if retirement struck
or moved a today Task Link (the `ledger` object is the tell). Destination:
the running open Pomodoro that held the link if it is still open; else
the same `next_pomodoro` rule.

**Ctrl+Enter (JS).** After `finalizeClosedTasks`, if the active line was
a Pomodoro Task Link in today's daily file (`api.taskLinkLane.matches` is
already the shared recogniser), queue into that owning entry using
`planExplicitPomodoroLinkInsertion`. Prefer the Tasks cache for the
reverse lookup; fall back to the recovery documents *already in memory*
if the cache is cold. Do not start a second vault walk.

### 5.3 JSON (schema 1, additive)

On `pomodoro_close` and `task_complete`:

```json
"successors": [
  {
    "note_path": "travel.md",
    "block_id": "book-flights",
    "text": "Book flights",
    "block_link": "[[travel#^book-flights]]",
    "because": {
      "text": "Fix flaky gkeep test",
      "note_path": "sase.md",
      "block_id": "fix-flaky"
    },
    "destination": {
      "name": "CAPTURE",
      "line": 14,
      "created": true
    },
    "previous_status_symbol": "?",
    "previous_status_name": "Blocked",
    "status_symbol": "*",
    "status_name": "Next"
  }
],
"successors_skipped": [
  {
    "reason": "still_blocked",
    "text": "File the claim",
    "note_path": "cash.md",
    "block_id": "file-claim"
  }
]
```

Omit both keys when empty so older clients see today's JSON. Human CLI:

```text
  queued [[travel#^book-flights]]  Book flights
    because Fix flaky gkeep test finished · Next
  skipped File the claim  still blocked
```

`pomodoro_blocks[].roles` may add `"linked"` (already in the vocabulary)
for the destination session; do not add a role clients must understand.

`task_blocks` gains role `"successor"` for each promoted dependent, next
to today's `"unblocked"`.

### 5.4 Dry-run is the Mac Capture UX

Live preview of `=x!` / `=!` must show the successor rows *before*
Return. That is how the feature stays honest: Bryan sees "Close CAPTURE
will queue Book flights" and can drop the `!` if that is wrong.

Presentation (thin client only):

- Close card: a **Next up** strip under the numbered task rows, chain
  glyph `⛓`, one row per successor (`Book flights · travel.md ^book-flights`),
  caption `because Fix flaky gkeep test finished`, destination
  `under CAPTURE (new)`.
- Overflow: `+2 unblocked, not queued`.
- Notification title stays `Closed CAPTURE` (or `Completed: …` for `!`).
  Body appends ` · queued Book flights (unblocked)`.
- Clicking the notification still opens the daily note (existing
  `open-note` category). No new category required.

Do not add a Swift-side dependency parser. If `successors` is missing
(old bob), the strip is absent.

---

## 6. Performance

This is the constraint that decides the architecture.

### 6.1 What would be too slow

- Full `markdown_files` + parse on every `=x` dry-run (Mac Capture
  keystroke).
- Cloning `recovery_base_snapshot` for close.
- `bob` subprocess from Ctrl+Enter.
- Re-reading every note in Obsidian when the Tasks cache is Warm.

### 6.2 bob-cli: filter, then parse, and only on complete

1. If the close selection completes nobody (`=x`, `=*`, empty lineup),
   **return immediately**. Zero extra I/O.
2. Collect the completed `[id::]` values and `note__blockid` canonical
   ids from the *already-resolved* numbered rows (close already looked
   those tasks up).
3. Walk vault paths but `continue` before parse unless the file bytes
   contain `dependsOn` or `DEPENDS ON` (and, cheap second check, one of
   the completed ids / block ids). Depends-On lines are rare; this is
   the difference between "every note" and "a handful."
4. Parse only those hits with the existing `parse_tasks` /
   `task_dependency_states` helpers so "open dependency" has one
   definition.
5. Cache the filtered set on `DependencyContext` for the batch, the way
   `recovery_base` is cached for `!`. Close drafts that never complete
   a link never build it.

Do not maintain a persistent reverse-dep sidecar. The filtered walk is
enough, and a sidecar would go stale next to open editors and capture's
own staged snapshot.

### 6.3 Obsidian: Tasks cache is the reverse index

When `getState() === "Warm"`, build `id → dependents[]` from
`getTasks()` (`task.dependsOn` is on the cache since Tasks 8.4.0; the
Depends-On stage already trusts it). Open Markdown buffers override,
same as §6.2 of the dependency contract.

Cold cache: reuse the documents `recoverBlockedDependentsNow` already
loaded in this `finalizeClosedTasks` turn. Do not walk twice. A later
cleanup (out of this feature's critical path) should *replace* that
full walk with the cache for recovery too.

Insertion is a daily-note edit. If the cursor is on that daily note,
apply the successor bullets in the **same editor transaction as the
strike** so one Ctrl+Z undoes close + queue together. Cross-note status
promotions use `vault.process` with a preimage check, matching Depends-On
"prepare targets first, then one transaction on the dependent."

### 6.4 Mac Capture stays a renderer

No extra `bob` process. The dry-run JSON already in flight grows by a
small array. Notification scheduling is already signposted
(`notification-schedule`); do not add a second notification for
successors — one body, one sound.

---

## 7. Beautiful, reliable, intuitive

### 7.1 Intuitive rule Bryan can say out loud

> "When I finish something that was on today's tomato, Bob pulls in
> whatever that unblocked, into this tomato — or the next one if I just
> closed it — and tells me."

That sentence should match every toast.

### 7.2 Obsidian notice card

Reuse the cancel-card chrome (`bob-nh-notice`), not a raw `new Notice`
string. Ctrl+Enter success is currently silent; this is the moment to
give completion a card equal to Cancel.

```
✓  Closed → queued
   Fix flaky gkeep test
   ⛓ unblocked
   Book flights
   under CAPTURE
   [+1 Task Link]  [Next]  [9/10 links]
```

Several successors: list up to three titles, then `+N more`. Skips as
muted chips (`2 still blocked`, `1 already today`). Aria-label / plain
fallback is the ` · `-joined string, same as cancel.

On a review-walk landing, compose into the single walk toast
(`outcome.notice`), per `decisions:answering-advances-the-walk` ("each
advance shows one toast"). Do not stack a second Notice.

### 7.3 Placement is the other half of beauty

Putting the new bullet *under* the struck predecessor makes the ledger
a story. Putting it at the bottom of a new session, after carried
In-Progress links, keeps "still working" above "newly unblocked." No
prose annotations, no extra managed-log child — Depends-On already
taught us not to grow unbounded children.

### 7.4 Reliability

- Shared vectors in `docs/task-dependencies.md` (new § Successor Queue)
  copied into Rust and JS tests, same as R1–R10 / DP vectors.
- Quiet interval: daily-note writes from capture already go through the
  staged batch; Obsidian uses the open editor. Do not fight
  `bob task reconcile`'s 2s structural quiet interval by also writing
  the dependent's Depends-On line (we do not touch that line).
- Failure policy: a successor insert that fails after the close landed
  **does not roll back the close**. Toast `Closed, but successors could
  not be queued` (mirror today's recovery failure). Close is the user's
  intent; queue is a gift.
- Dry-run JSON equals real-run JSON except `dry_run`, as every other
  capture kind already promises.

---

## 8. Alternatives considered

### Auto-link every dependent, including still-blocked

Matches a literal reading of "tasks that depend on tasks that we close."
Rejected: it promotes leftover prerequisites to Next and puts `[?]` rows
on Today. Today already allows Blocked links, but *automation* should
not create them.

### Prompt when N ≠ 1; auto only for a single successor

Safer for sticky Next. I would ship this if Bryan would rather choose.
It is worse at the "keep going" feeling, and Mac Capture would need a
new interactive close picker (the app currently confirms the preview
with Return). **Recommended default is auto-all-eligible with cap +
preview**, because `=x!` already has a preview and Return is the
confirm. Reopen if fan-out toasts appear most days.

### Raise to Next only, do not insert a Task Link

Would unblock the lane without claiming Today. Then the work is still
not on the tomato, which is the whole request. Rejected.

### Second keystroke ("pull next")

More GTD-pure (Today stays a bet you make). Rejected as the default
because the request is automatic and the complete gesture *is* the bet:
the finished task was already on Today.

### Implement only in Obsidian, have capture shell into the same JS

Inverted. Mac Capture cannot run the plugin, and bob-cli is already the
source of truth for close. Engine in Rust; JS mirror for the keymap.

### Persistent reverse-dep index / Dataview dump

Too much machinery, stale vs open buffers. Filtered walk + Tasks cache
are enough.

### `=x!` token to suppress queue

Not needed for v1. The preview is the suppressor: delete the `!` or
complete a different number. A suppressor suffix would collide with the
already-dense `=x[<N>][*<P>][!<M>][~<K>]` grammar. Reopen if preview
is not enough.

---

## 9. Critique of the plan as stated

The request is directionally right and incomplete in four ways that
would hurt if implemented literally.

1. **"Tasks that depend on tasks that we close"** without "fully
   unblocked" would auto-promote leftover prerequisites. That fights
   `decisions:task-deps-are-depends-on-links` (linking a dependent
   raises open prerequisites) and would surprise Bryan every time a
   task has two blockers.

2. **Ctrl+Enter is many commands.** It closes checklists, takes Task
   Card rolls, reopens done tasks, and completes Task Links. Only the
   last of those is this feature. The implementation must gate on
   `api.taskLinkLane` / a today-ledger dedicated link, or review-walk
   PRE rows will start growing tomatoes.

3. **`=x!` is a live-preview path.** Adding a vault-wide dependent scan
   to `plan_pomodoro_close` would be the first time close preview does
   more than "daily note + a few targets." That is how Mac Capture
   stops feeling instant. The filter in §6 is not optional polish.

4. **Toasts without preview** would teach capture users after the
   write. Mac Capture's whole design is "the card is the truth before
   Return." Successors belong on that card.

The request is also *under*-scoped in one way worth taking: `=x!`
should recover dependents the way the other complete paths already do.
Otherwise the queue step has nothing honest to queue, or it queues
`[?]` tasks.

---

## 10. Would I take a different approach?

The only different approach I would still respect is **auto-queue iff
exactly one successor, else show the names and wait**. That is the
right design if Bryan's graph is bushy (one closed task regularly
unblocks four). From the Depends-On contract and the worked examples in
`docs/task-dependencies.md`, edges look sparse — one or two
prerequisites, not a fan-out. Sparse graphs make auto-all-eligible
feel like flow; bushy graphs make it feel like a stampede.

Ship auto-all-eligible with a cap, and reopen for the chooser if the
overflow chip shows up in daily use.

I would **not** put this in `bob task reconcile`. Hooks run on a timer,
write many notes, and must not invent Today. Successor Queue is a
gesture aftermath, like recovery and link retirement.

---

## 11. Implementation sequence

One contract doc, then the engine, then the two clients. Dual JS/Rust
is already how this repo survives; do not wait on WASM.

1. **Contract.** New § in `docs/task-dependencies.md` (Successor Queue):
   trigger, eligibility, placement, status, JSON keys, toast copy,
   vectors (one successor; two with one still blocked; already today;
   inbox; cap overflow; close-creates-placeholder; close-uses-later-entry;
   `!` with a today link; `!` without; Ctrl+Enter on a Depends-On line
   does nothing; park does nothing).
2. **Rust engine** + close / `task_complete` call sites + human/JSON
   output. Tests in `task_complete/tests` and
   `capture_pomodoro_close/selection_tests.rs`.
3. **Mac Capture** decode + close/complete presentation + notification
   body + design fixtures. No process-client changes.
4. **Obsidian:** cycler piggybacks recovery; block-id-prompt explicit
   insert into the owning entry; navigation-hotkeys notice card (and
   walk-toast compose). Version-bump cycler `api` only if other plugins
   need `queueSuccessors`; otherwise keep it internal to the close
   path.
5. **Perf tests:** close dry-run with zero completes does not read
   extra notes; close with completes reads only Depends-On candidates;
   Obsidian Warm-cache path does no `vault.cachedRead` of the whole
   vault for the queue step.

No new CLI verb. Help text for `=x!` / `=!` grows one sentence:
completing a numbered Task Link queues fully unblocked dependents into
the same / next Pomodoro.

---

## 12. Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Sticky Next from a bad queue | Alt+N is the only release | Preview on capture; toast names each task; cap; skip inbox |
| Fan-out blows `max_links` | Plan budget turns red mid-session | Stop at remaining slots; overflow chip |
| `=x!` preview latency | Mac Capture's reason to exist | Complete-only filtered walk; never clone the vault |
| Dual-implementation drift | Depends-On already pays this cost | Shared vectors in the contract doc first |
| Undo split on Ctrl+Enter | Strike in editor, status in vault.process | Same-transaction insert when the daily note is active |
| Review-walk double toast | `answering-advances-the-walk` wants one | Compose into `outcome.notice` |
| Close without recovery | `=x!` would queue `[?]` or miss Ready-already dependents | A3: recover first, then queue |
| Quiet-interval races with hooks | Structural writes deferred 2s | Do not rewrite Depends-On lines; daily note is the user's open editor / capture batch |

---

## 13. Recommended solution

**Build Successor Queue as the fourth step of the shared task-completion
engine** (close tree → retire today links → recover Blocked dependents →
queue fully unblocked successors), with:

- **Trigger:** a dedicated Task Link in *today's* daily file was
  completed (Ctrl+Enter on that link; `=x!` / `=!`; and `!note:id` when
  it retires such a link).
- **Who:** direct, fully unblocked, non-inbox, non-hidden, non-recurring
  dependents with a block id, not already on today's open ledger, up to
  remaining `plan.max_links` and a 5-successor cap.
- **Where:** same open Pomodoro, immediately under the struck link; on
  session close, the close plan's `next_pomodoro`, after carried links,
  replacing a lone empty placeholder child.
- **Lane:** same as `@route:block-id` (Ready/Blocked → Next).
- **Tell Bryan:** one Obsidian notice card (composed into the walk toast
  when advancing); Mac Capture Next-up strip on the close/complete
  preview plus one notification body line. Additive schema-1 JSON.
- **Speed:** no whole-vault clone on close preview; filter to
  Depends-On notes; Obsidian uses the Warm Tasks cache.

That is the version I would lead. It is automatic where the graph is
unambiguous, visible before and after the write, and cheap enough that
Bob Mac Capture can keep showing the close card on every keystroke.

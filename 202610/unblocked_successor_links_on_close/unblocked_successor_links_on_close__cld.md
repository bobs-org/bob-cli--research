# Linking Unblocked Dependents When a Planned Task Closes — research (cld)

**Question.** When a task that is planned in today's daily file closes, should Bob
automatically add Task Links for the tasks that depended on it? The closes in scope are
Obsidian `Ctrl+Enter` and `bob capture`'s `!note:id`, `=x!`, and `=!`. If yes, how should
it work so it stays fast (especially in Bob Mac Capture), reliable, intuitive, and good
to look at?

**Short answer.** Yes, build it. I would frame it as *"a successor takes its
predecessor's slot"* and add a few guardrails:

- Link only the dependents this close **fully** unblocked.
- Put each link **right where the predecessor's link was**.
- Explain every link in one compact toast ("🔓 unblocked by …").
- Preview it in Bob Mac Capture before submit.
- Use Alt+N (release) as the undo.
- Use a future `scheduled` date as the per-task opt-out.

There is also a prerequisite I did not expect: **today, every `bob capture` already
reads the whole vault before doing anything.** That is about 0.25 s per Mac live preview
on apollo, and roughly 95% of it is wasted. Fix that first (filed as `bob-cli-5v`). The
feature can then be added *and* capture will end up about 6× faster than it is now,
rather than slower.

---

## 0. TL;DR — recommended solution

1. **Trigger.** A Bob close gesture completes a task that was **planned in today's
   ledger**, meaning a live Task Link under an open Pomodoro, or under the Pomodoro being
   closed. This applies no matter where the key was pressed (adjustment **A1**). The
   gestures are:
   - Obsidian Ctrl+Enter on the link, on the task line, or on the Pomodoro line;
   - `bob capture` `!note:id`;
   - `=x…!M`, `=!`, and `![[…]]` embeds closed by `=x`.
2. **Candidates.** Open tasks whose `[dependsOn::]` names a task closed by this gesture,
   that now have **no other open prerequisite** and **no future `scheduled` date** (A2).
   Excluded:
   - transitive dependents;
   - `^prj` lifecycle tasks;
   - tasks already linked under an open Pomodoro today. These still recover, to Next.
3. **Placement** (A3):
   - The successor goes into the open Pomodoro that owned the predecessor's live link
     *before* the close, on the line **immediately after** that link's bullet subtree
     (its vacated slot).
   - If that Pomodoro is the one being closed, it goes into the carry placeholder
     `- [ ] () — NAME`. The placeholder is created when needed, and successors count as
     carried. They are appended after the carried links.
   - If the owner was already a completed Pomodoro, the normal "running, else first
     open" target is used.
4. **Lane.** A linked successor becomes Next `[*]` in the same write. This is already
   the invariant for "linked under today's open Pomodoros" (A5).
   - Unlinked unblocked dependents recover to Ready, as they do today.
   - No `[fresh::]` stamp, because no human confirmed the task.
   - A missing `^block-id` is minted automatically (A6). 22 of the vault's 50
     dependents lack one.
5. **Budget.**
   - Link all candidates, and show the plan meter in the toast (red when over).
   - Under `plan.strict: true`, automation may not grow the link count past
     `max(max_links, count before the close)`. In other words, the successor inherits
     the predecessor's slot (A4).
   - A circuit breaker stops linking when one close would add more than 5 links. No
     close in the vault's history comes close to that.
6. **Feedback.** Stay quiet when nothing unblocks. Otherwise show **one** toast that
   lists each successor, where it went, and why, plus a muted "still waits" line for any
   dependent this close did *not* unblock:
   - Obsidian: an `Unblocked` card in nav's existing notice-card family.
   - Bob Mac Capture: unblocked rows in the dry-run preview card, plus one line in the
     macOS notification.
   - CLI: a `🔓 linked` row.
7. **Speed.**
   - bob-cli: build one lazily created, batch-shared, parallel vault snapshot with a
     `memchr` prefilter (`dependsOn`, `id::`). Target `!`/`=x!` dry runs ≲ 60 ms on
     apollo (today 0.38 s) and plain captures ≲ 40 ms (today 0.25 s).
   - Obsidian: find dependents from the Tasks plugin cache plus open buffers, instead of
     the cycler's current sequential `cachedRead` of every note on every close.
8. **Contract.** One spec section with shared vectors (`UL1…UL17`, §6.8), implemented in
   Rust (capture) and in task-status-cycler (Ctrl+Enter). The Mac app only decodes and
   presents, per `decisions:mac-capture-is-a-thin-client`.

---

## 1. Scope and method

What I examined:

- bob-cli `master` @ `b566ba4`.
- bob-plugins `master`, with task-status-cycler 1.27.0, bob-navigation-hotkeys 2.14.0,
  block-id-prompt 1.24.0, and bob-ledger-tools 1.36.1.
- Bob Mac Capture (opened as an external checkout).
- The memory decisions `task-deps-are-depends-on-links`, `task-lanes-are-sticky`,
  `task-status-is-derived`, `today-is-read-from-the-ledger`,
  `answering-advances-the-walk`, and `mac-capture-is-a-thin-client`.
- The glossary terms Task Link, Task Dependency Link, Pomodoro, Work Log, Project Task,
  Reference Task, and Inbox File.

What I ran:

- A census of dependencies in the live vault (read-only).
- Release builds of bob-cli `master`, plus a throwaway prototype in `/tmp`, timed against
  a `/tmp` copy of the vault on apollo.
- `strace` to attribute file reads.

All measurements were taken on **apollo** (Linux, 16 cores, warm page cache), not on the
MacBook. The relative numbers carry over; absolute Mac numbers must be re-measured with
the app's existing `preview` and `submit` signposts.

---

## 2. What exists today

### 2.1 The close paths and what they write

| Gesture | Where the closed task's link ends up | Pomodoro closed? | Dependents recovered now? | Feedback today |
| --- | --- | --- | --- | --- |
| Obsidian Ctrl+Enter on a Task Link under an open Pomodoro (cycler `160-plugin-completion.js:394-526`) | Struck **in place** (`~~[[…]]~~`); never moved | no | yes → always Ready `[ ]` (`130-plugin-references.js:123-259`) | **none** (no success toast) |
| Ctrl+Enter on the Pomodoro line (`completeActivePomodoroTask`, `170-plugin-pomodoro.js:274-368`) | Embedded `![[…]]` targets close; plain links go `[/]` and are carried into `- [ ] () — NAME` (`060-pomodoro.js:789`, created only if something is carried or this is the last entry, `:862-890`) | yes | yes, for the closed embeds | none |
| Ctrl+Enter on the task line in its own note (`160:306-341`) | Retirement strikes `![[…]]` embeds vault-wide; a plain ledger link is left for the hooks | no | yes → Ready | none |
| `bob capture '!note:id'` (`src/native/capture/task_complete.rs`) | Struck, **and moved** to the running entry (else the last completed one) by the reconcile structural planner (`task_status_hooks.md` §Pomodoro Marker) | no | yes → always Ready (`task_complete/recovery.rs`, `set_task_line_status(line, ' ')`) | CLI row `unblocked [?] → [ ] …`; Mac card rows and notification text |
| `bob capture '=x…!M'` / `'=!'` (`capture_pomodoro_close/*`) | Completed links retire; worked and deferred links are carried into a new placeholder (`ledger.rs:345-346`, `should_create = carried ∨ no later entry`) | yes | **no** — left to `bob task reconcile` (`capture.md:1776`) | close card and notification; nothing about dependents |

I verified the `=x!` gap against the live-vault copy:

```text
$ bob capture --dry-run -- '^sase:fix-apollo=x!5'
  5 [*] → [x] Fix apollo machine! sase.md ^fix-apollo
  next: BOB (created) at line 37 · carries 4 links
```

The JSON has no `unblocked` key. Meanwhile `!sase:fix-apollo` does report
`unblocked [?] → [ ] Re-launch all failed agents on apollo!`.

### 2.2 Three dependent-recovery implementations, slightly divergent

| Implementation | Data source | Recovers to | Returns the list? |
| --- | --- | --- | --- |
| cycler `recoverBlockedDependentsNow` | `await vault.cachedRead(file)` of **every** Markdown file, sequentially, on every close (`130:123-160`) | always Ready | **no**: returns only `{reopened, failures}` |
| capture `recover_blocked_dependents` | whole-vault snapshot (a second full read; §2.6) | always Ready | yes: `RecoveredDependent{path,line,block_id,text}` |
| hooks (`bob task reconcile`) | whole-vault scan every 15 min on the MacBook | **derived rank**: Next if linked or recent today, else Ready (`task-status-hooks.md` §Derived Blocked Status) | n/a |

nav's dependency writer also uses the derived rank (ADJ-8,
`080-dependency-identity.js:429-500`). So "always Ready" in the cycler and in capture is
already a known, tolerated divergence that the hooks repair. **This feature removes it:**
a successor that ends up linked today recovers straight to Next.

Related open bugs:

- `bob-cli-3k`: Alt+]/Alt+[ closes skip `finalizeClosedTasks`, so they do not recover
  dependents at all.
- `bob-cli-3p`: a Reverse "Blocks…" stage. It is related UI that also needs a
  dependents index.

### 2.3 Feedback surfaces

- **Obsidian.**
  - A plain Ctrl+Enter close shows no toast at all.
  - Rich notice cards exist only in nav (`280-notices-and-dates.js:298-593`: header
    icon, level pill, count pill, receipt, body, tone chips; CSS
    `styles.css:1140-1368`). The cancel card already carries an
    `unblocked N dependent(s)` chip.
  - On a review-walk landing, nav composes one multi-line toast through
    `reviewWalk.continue(origin, {notice})`.
  - There is no shared toast component across plugins. Plugins communicate only through
    frozen, versioned `api` objects.
- **Bob Mac Capture.**
  - The panel **hides immediately on success** (`CapturePanelModel.completeSubmit
    :4507-4572`). An in-panel success toast is therefore impossible.
  - After submit the only feedback surfaces are:
    - the macOS notification (`NotificationService.swift`);
    - a 420 ms pulse of the menu-bar glyph.
  - Before submit, the live dry-run preview cards are the rich surface. The `!` card
    already renders `lock.open.fill` rows for `unblocked[]`
    (`CapturePanelView.swift:2958-2974`), and the close card has no dependents section
    (`PomodoroCloseSummary` has no such field).
  - The "Open Note(s)" action treats the daily note as changed only when `ledger != nil`
    (`NotificationService.swift:664-666`). It would miss links added by this feature.
- **CLI.** Human rows such as `ledger  Task Link struck in FIX · …`.

### 2.4 Vault census (live vault, 2026-10-09, read-only)

| Measure | Value |
| --- | --- |
| Tasks with `[dependsOn::]` (dependents) | 50 (20 currently `[?]`, 24 `[x]`, 6 `[-]`) |
| `⛓️ DEPENDS ON:` lines | 39 |
| Distinct prerequisites referenced | 38 |
| Fan-out (dependents per prerequisite) | 1 → 29, 2 → 5, 3 → 3, **4 → 1** (`cash__unemployment`) |
| Fan-in (prerequisites per dependent) | 1 → 48, 2 → 2 |
| Edges within the same note vs. across notes | **46 vs. 6** |
| Dependents without a `^block-id` | **22 of 50** (44%) |
| Dependents living in daily notes | 0 |
| Closed prerequisites that have dependents | 20; **9** of them were linked in that day's daily note when they closed |
| Closed prerequisites whose dependent stays Blocked only because of a future `scheduled` date | 2 (`^e2e-sase-8v` → "Start adding `sase--<name>` badges", scheduled 2026-10-13; `^epic-notify` → "Start creating a PR for every epic", scheduled 2026-11-09) |

What these numbers mean for the design:

- Same-note edges dominate (88%). The successor is almost always in the same project as
  its predecessor, so "same Pomodoro" usually means "same theme". That is the right
  default.
- Block-ID minting is mandatory. Skipping ID-less dependents would make the feature skip
  almost half of them.
- Fan-out above 1 is real (9 of 38 prerequisites), so the toast must handle several rows.
- "Prerequisite closed but dependent still Blocked by its schedule" already happens. The
  toast should explain it ("stays Blocked until Oct 13") rather than leave Bryan
  wondering why nothing was linked.

**Live example in today's ledger:**

```markdown
- [ ] (**1000-1025** [t:: 25m]) — BOB
	- [[bob#^better-refs]]
	- [[bob#^double-equals]]
	- [[bob#^mac-cmd]]
	- [[bob#^auto-dep-task-link]]
- [ ] () — FIX
	- [[sase_agent_history#^launch-agent-archive-view]]
	- [[sase#^just-install-venv]]
	- [[sase#^fix-apollo]]          ← sase.md:82 "Re-launch all failed agents on apollo!" [?] depends on it
	- [[sase#^fix-muse-reply]]
- [ ] () — SASE
	- [[sase#^dynamic-agents-md]]   ← 3 dependents (gkeep_inbox: no block id; sase_memory ^memory-beads; a ref/chat ^ref task)
	- [[sase_goals#^epic-roadmap]]
```

This is the canonical motivating case. "Fix apollo" → "Re-launch failed agents on
apollo" is a textbook immediate follow-up.

### 2.5 Performance today (apollo; vault copy of 6,207 `.md` files, 13.4 MB)

Release build of `b566ba4`; `bob capture --dry-run --format json -- <draft>`:

| Draft | HEAD | Prototype with eager discovery skipped | Tiny 5-note vault |
| --- | --- | --- | --- |
| `hello` | **0.22–0.27 s** | **0.04 s** | < 0.01 s |
| `=x` | 0.28 s | 0.04 s | 0.01 s |
| `!sase:fix-apollo` | **0.37–0.41 s** | (needs the resolver) | 0.02 s |

| Raw I/O | Time |
| --- | --- |
| sequential `cat` of every note | 0.19 s |
| directory walk + `stat` only | 0.03 s |
| parallel `rg -l -F dependsOn` (24 files match) | 0.03 s |
| parallel `rg -l -F '[id::'` (41 files match) | 0.03 s |

How the time is spent:

- `strace -e openat`: `hello` opens **5,071** notes; `!` opens **10,125**, because the
  vault is read twice.
- `strace -k` puts the reads in `capture_dependency_tasks::discover`. The cause is
  `src/native/capture/plan.rs:84`: every batch eagerly builds
  `DependencyContext::new(..)` (`dependencies.rs:43-61`), which reads and task-scans
  every note and computes block-ID suggestions for every ID-less task.
- `!` then rebuilds a second full snapshot through `recovery_base_snapshot`
  (`dependencies.rs:65-86`).
- The eager scan was introduced on 2026-10-03 (`6718111`).

Bob Mac Capture spawns `capture --dry-run` after every 50 ms typing pause
(`CapturePanelModel.swift:249`). Its thin-client decision assumed a dry-run spawn costs
"~5 ms". **That premise has silently broken.** I filed this as **`bob-cli-5v`** (bug,
medium) with the evidence above.

Conclusion for this feature: *never add a second vault read.* Make the existing one lazy,
shared, parallel, and prefiltered, and finding dependents becomes nearly free.

---

## 3. Critique — is this a good idea?

**Verdict: yes, with guardrails.** A dependency edge is the one place in the vault where
Bryan has already written down "B comes after A". When A is finished *inside today's
plan*, pulling B into A's slot:

- keeps momentum;
- removes a context switch (navigating to B's note, Ctrl+Shift+Enter, picking a
  Pomodoro);
- makes the plan match reality.

It is also the missing half of a symmetry that already exists. **Linking a dependent pulls
its prerequisites to Next** (`task-dependencies.md` §5 Promotion). **Closing a
prerequisite should push its dependent into the plan.**

The tensions I would design around:

1. **"Blocked by" is not "do right after".** "Apply to OpenAI/Anthropic roles" depends on
   "Update GOOG end date", but probably isn't an immediate next step. The system already
   has a precise way to say "not right after": a future `scheduled` date keeps the
   dependent Blocked, and it is exactly the condition the vault already uses (§2.4).
   Recommend that as the per-edge opt-out instead of inventing new grammar. Revisit only
   if auto-links are frequently released (§8).
2. **Sticky lanes plus automation.** Linking raises a task to Next, and lanes are sticky.
   Only release (Alt+N) lowers it, and unlinking never does
   (`decisions:task-lanes-are-sticky`). An unwanted auto-link therefore has to be
   undone with **Alt+N**, not by deleting the line. That is acceptable because Alt+N on
   a Task Link *is* exactly "remove link + Next → Ready". Teach it in the toast hint and
   in docs, and make reopen-the-predecessor undo it too (phase 5).
3. **Plan inflation.** Fan-out up to 4, and today's ledger already sits at the 10/10 link
   cap. The plan meter belongs in the toast, and `plan.strict` should bind automation
   (A4).
4. **Writes the user didn't type.** These include cross-note status writes and minted
   block IDs in other notes. Mitigations:
   - capture previews everything before submit;
   - Obsidian explains everything after the fact;
   - all writes are preimage-checked;
   - a single config switch turns the feature off.
5. **Two implementations.** Rust capture and JS cycler must agree on candidates,
   placement, and ordering. That is the established pattern (dependency, plan, and Today
   contracts with shared vectors), and it works.
6. **Performance.** Both clients currently pay for whole-vault reads on every close. Done
   naively, this feature would add more. Done right (§6.5), it pays for a speedup.

**How often it will fire.** Historically about 9 qualifying closes in ~4 months, but
first-class Depends-On lines only shipped on 2026-10-03 and 20 dependents are Blocked
right now. Expect a few per week. The feature is rare enough that its toast must be
self-explanatory every time (no habituation), and common enough to be worth one careful
implementation.

---

## 4. Alternatives considered

| Approach | Pros | Cons | Verdict |
| --- | --- | --- | --- |
| **A. Push on close** (link successors at close time) — requested | Immediate; works in Obsidian, the CLI, and the Mac app; previewable in capture | Automated writes; two implementations | **Recommended**, with the guardrails in §5 |
| B. Suggest only (toast lists unblocked tasks; Bryan links them) | Zero surprise writes, no lane residue | Defeats the request; Obsidian notices can't take keystrokes, so it would be a mouse click or a trip to each note | Reject as default; it is what happens for leftovers under strict budget |
| C. Read-time "ghost rows" (ledger-tools draws unblocked successors under the struck link) | No writes at all | Invisible to Today, the plan budget, the CLI, and Mac; more decoration machinery | Reject; keep only as a polish idea (a 🔓 glyph on real links, §6.4) |
| D. Let `bob task reconcile` add the links | One Rust implementation | Up to 15 min late, no toast, writes appear "by themselves" — the worst kind of surprise | Reject |
| E. Explicit successor edges (a `⏭️ THEN:` line, or a marker on the dep link) | Separates "blocked by" from "do next" | New grammar, new parsers in four repos, migration; `scheduled` already covers "not now" | Defer; reopen criterion in §8 |
| F. Obsidian shells out to `bob` for the plan | Single implementation | Ignores unsaved editor buffers and the cursor; adds subprocess latency to Ctrl+Enter | Reject |

---

## 5. Adjustments to the requirements (called out)

Each item states what the request says, what I recommend, and why.

- **A1 — The trigger is "planned today", not "pressed in the daily file".**
  - *Request:* links for dependents of tasks closed "in the current daily file", via
    Ctrl+Enter on a Task Link, `!`, `=x!`, or `=!`.
  - *Recommend:* fire whenever a Bob close gesture completes a task that has a live
    Task Link under an open Pomodoro in today's ledger, or under the Pomodoro being
    closed. That covers:
    - Ctrl+Enter on the link;
    - Ctrl+Enter on the task line in its project note (Case C);
    - Ctrl+Enter on the Pomodoro line (closing its `![[…]]` embeds);
    - `!note:id`;
    - every `=x…` close that completes links (`!M`, `=!`, embeds).

    Not covered:
    - Cancel (Ctrl+Shift+P). A cancelled prerequisite unblocks its dependents, but "won't
      do" is no reason to plan the follow-up.
    - Raw Tasks-plugin checkbox clicks and hooks runs (not Bob gestures).
    - Alt+] closes until `bob-cli-3k` routes them through `finalizeClosedTasks`; then
      they inherit this for free.
  - *Why:* the same close should produce the same plan regardless of which line the
    cursor was on. A task that wasn't planned today has no "slot" to hand over, so it
    only reports "unblocked (Ready)".
- **A2 — Only fully unblocked, direct dependents.**
  - Candidates are open dependents that name a just-closed id, have no other open
    prerequisite, and have no strictly-future `scheduled` date.
  - Transitive dependents never get linked: they are still blocked by the successor.
  - Excluded from *linking*, though still recovered:
    - `^prj` project lifecycle tasks, which capture never links;
    - dependents already linked under any open entry today. These recover straight to
      Next (`not_linked: already_planned`).
  - Dependents that remain blocked are reported, not linked.
- **A3 — "Same Pomodoro" means the predecessor's planned slot.**
  - `!` capture moves the struck link from a queued entry into the *running* one, for
    credit. Successors should **not** follow it there. They go into the entry where the
    predecessor was planned, on the vacated line.
  - This keeps themes coherent and avoids silently growing the running session.
  - Obsidian (strike in place) and capture (strike and move) then put the successor on
    the **same line**.
- **A4 — Budget: soft by default, binding under `plan.strict`.**
  - Default: link every candidate, and show `plan T/Tc · L/Lc` in the toast (red when
    over). This matches how every other writer treats caps.
  - With `plan.strict: true`, automation may not grow the link count past
    `max(max_links, links before the close)`. Leftovers stay Ready and are listed as
    "plan full". Selection order: Tasks priority, then same note as the predecessor,
    then path and line.
  - A fixed **circuit breaker**: if one close would add more than 5 links, add none and
    report them all. The historical maximum is 4.
- **A5 — Linked successors become Next in the same write, with no freshness stamp.**
  - Next is the existing invariant for linked tasks; the hooks would promote them
    anyway.
  - Freshness means "a human confirmed this task still matters as written", and
    automation must not claim that. A stale successor will still surface in the review
    walk, which is the right outcome.
- **A6 — Mint block IDs automatically.** Use the existing suggester:
  - Rust: `capture_block_ids::suggest_ids_with_used`.
  - JS: `suggestBlockIdFromTask`.

  Uniqueness is checked against the dependent's own note. Without this, 44% of
  dependents could never be linked.
- **A7 — `=x!` and `=!` must recover dependents.** This is a gap today (§2.1) and a
  prerequisite for the feature.
- **A8 — Quiet by default.** No new toast when nothing unblocks. Ctrl+Enter stays silent,
  as today.
- **A9 — One kill switch.** `plan.link_unblocked: true` (default) in
  `~/.config/bob/config.yml`, read by both Rust and ledger-tools/cycler config loaders.
  The review-walk record rejected a config switch, but that feature only moved the
  cursor. This one writes across notes autonomously, and an off-switch is cheap
  insurance.
- **A10 — The performance groundwork is part of the feature** (`bob-cli-5v` plus a
  Tasks-cache index in the cycler). "Blazing fast" is a requirement *today's* code
  already misses.

---

## 6. Design

### 6.1 Vocabulary

- **Predecessor**: a task this gesture closed.
- **Successor**: an open dependent the close fully unblocked.
- **Unblocked link**: the Task Link the close adds for a successor. Proposed glossary
  term "Unblocked Link (successor link)", to be added via `/sase_memory_write`.
- **Slot**: the line position of the predecessor's live link in its owning open entry,
  captured *before* any write.

### 6.2 The rule (shared by Rust and JS)

```text
inputs: closed = tasks this gesture closed (root + closed embedded subtrees),
        anchors = for each closed task: its owning open entry + link line BEFORE the close
                  (or "closing" when its entry is the Pomodoro being closed),
        ledger = today's daily note text after close/retirement,
        index  = dependents index (tasks whose dependsOn intersects closed ids; plus id→status)

1. closed_ids = each closed task's [id::] and canonical dependency_id(path, blockId)
2. for each open task D with D.dependsOn ∩ closed_ids ≠ ∅:
     if any other id in D.dependsOn resolves to an open task → still_blocked(waits_on n)
     elif D.scheduled > today                                 → still_blocked(scheduled)
     elif D is ^prj                                           → unblocked, not_linked(project_task)
     elif D linked under an open entry of today's ledger      → unblocked → Next, not_linked(already_planned)
     elif no closed predecessor of D had an anchor            → unblocked → Ready, not_linked(not_planned_today)
     else → successor(D, anchor = anchor of D's first predecessor in ledger order)
3. order successors: by anchor ledger order, then path, then line
4. budget: strict → keep while count ≤ max(cap, before); >5 per gesture → link none (breaker)
5. placement:
     anchor entry still open      → insert after the predecessor link's subtree (or at the vacated
                                    line when retirement moved it), at that entry's child indent
     anchor entry = closing entry → append after carried lines in its placeholder; create
                                    "- [ ] () — NAME" if the close would not have created one
     anchor entry already closed  → running entry, else first open entry; none → not_linked(no_open_pomodoro)
6. writes (one batch): D's note: mint ^id if missing, status → [*];
                       daily note: "<indent>- [[<shortest link>#^<id>]]"
```

- Anchor timing: anchors are taken *after* any explicit link step in the same item
  (`^route:id=x…`, `@route:id=x…`, because Bryan chose that session) and *before* the
  close and the retirement relocation (which Bryan did not choose).
- Link form: the shortest unambiguous form, the same rules as dep links
  (`task-dependencies.md` §3): `[[note#^id]]` when the basename is unique, else
  `[[dir/note#^id]]`.
- Idempotence: a re-run finds the successor already linked, so `already_planned` and
  nothing is written.

### 6.3 Ledger walk-throughs (real vault)

**(a) Ctrl+Enter on `[[sase#^fix-apollo]]` in FIX.** The cycler strikes it in place, and
the successor appears on the next line:

```markdown
- [ ] () — FIX
	- [[sase_agent_history#^launch-agent-archive-view]]
	- [[sase#^just-install-venv]]
	- ~~[[sase#^fix-apollo]]~~
	- [[sase#^re-launch-apollo-agents]]
	- [[sase#^fix-muse-reply]]
```

`sase.md:82` becomes
`- [*] #task Re-launch all failed agents on apollo! … ^re-launch-apollo-agents`; it was
`[?]`. Its `⛓️ DEPENDS ON:` chip now shows a ✓ predecessor. The ledger reads like a
hand-off and needs no marker.

**(b) `bob capture '!sase:fix-apollo'` while BOB is running.** Retirement moves the struck
link into BOB as today. The successor takes the vacated FIX slot, so the final FIX block
is identical to (a) minus the struck line:

```markdown
- [ ] (**1000-1025** [t:: 25m]) — BOB
	…
	- ~~[[sase#^fix-apollo]]~~
- [ ] () — FIX
	- [[sase_agent_history#^launch-agent-archive-view]]
	- [[sase#^just-install-venv]]
	- [[sase#^re-launch-apollo-agents]]
	- [[sase#^fix-muse-reply]]
```

**(c) `bob capture '^sase:fix-apollo=!'` (link into BOB, close BOB completing every
link).** Nothing is carried and FIX follows, so today no placeholder is created. With
successors, one is:

```markdown
- [x] (**1000-1020** [t:: 20m]) — BOB
	- ~~[[bob#^better-refs]]~~
	…
	- ~~[[sase#^fix-apollo]]~~
- [ ] () — BOB
	- [[sase#^re-launch-apollo-agents]]
- [ ] () — FIX
	…
```

**(d) Closing `[[sase#^dynamic-agents-md]]` in SASE** unblocks three dependents (fan-out
3). Whether each is linked depends on budget mode:

| Mode | Result |
| --- | --- |
| Default | All three are linked after the struck link. The `#ref` task's reading status becomes `next`. The inbox task gets a minted `^no-codex-agents-md`-style ID. The plan meter reads `10 → 12/10` in red. |
| `plan.strict: true` | One is linked (it inherits the slot). Two are listed "Ready · plan full". |

### 6.4 Feedback design

**Copy principles.**

- One toast per gesture.
- *What* goes first (the successor's text), then *where* (`→ FIX`), then *why*
  (`unblocked by ✓ Fix apollo machine!`).
- Existing glyph vocabulary: 🔓 for unblocked (cycler Schedule Log, Mac `lock.open.fill`),
  ⛓ for dependency, ✓ for done.
- Statuses use the existing `--task-status-*` tokens.
- Rows are capped at 4, then `+N more`.

**Obsidian — the `Unblocked` card.** It extends nav's notice-card family with an
`is-unblock` modifier, so there is no new visual language:

```text
┌──────────────────────────────────────────────────────────────┐
│ 🔓  Unblocked   1 → FIX                    ✓ Fix apollo machine! │
│  ＋ Re-launch all failed agents on apollo!            [ Next ] │
│ ─────────────────────────────────────────────────────────────  │
│  (plan 3/3 · 10/10)   (Alt+N on a link releases it)           │
└──────────────────────────────────────────────────────────────┘
```

Card structure:

| Part | Content |
| --- | --- |
| Header | icon `lock-open`; level pill `Unblocked`; count pill `N → <ENTRY>`; receipt = the predecessor's text, struck and muted |
| Body rows | `＋` + successor text (cut at ~48 characters) + `↗ note` when cross-note + a status pill. Muted `○ … Ready · plan full` rows for leftovers. Muted `🔒 … stays Blocked · scheduled Oct 13` / `· waits on 1` rows for dependents this close did not free (at most 2, then `+N`). |
| Chips | `plan T/Tc · L/Lc` (info, or warn when over); `minted ^id` (info) when an ID was created; the release hint (muted) |

Behavior:

- Accessibility: `aria-label` is the plain-text form, and the card also degrades to that
  text when nav (or its `api.notice`) is absent:

  ```text
  Unblocked 1 → FIX after ✓ Fix apollo machine!: Re-launch all failed agents on apollo! (Next) · plan 3/3 · 10/10
  ```

- Duration: 6 s, plus 1 s per extra row.
- Clicking a row opens that task, the same as chips do.
- On a review-walk landing, the card's text form becomes `outcome.notice` for
  `reviewWalk.continue`, so the walk's single combined toast stays single:

  ```text
  ✓ Done · Fix apollo machine!
  🔓 Next in FIX: Re-launch all failed agents on apollo!
  → <landing line>
  ```

- Optional polish: ledger-tools draws a faint 🔓 after any live ledger link whose task
  had a prerequisite completed today. This is derived at read time, never stored, and is
  a factual statement rather than a provenance claim.

**Bob Mac Capture.**

- **Preview, before submit.** This is the most valuable surface, because it explains
  *before* anything is written.
  - The `!` card's existing unblocked rows become `[?] → [*]  Re-launch all failed agents
    on apollo!` with a trailing caption `→ FIX`.
  - Not-linked rows keep `[?] → [ ]` with a reason caption (`Ready · not planned today`,
    `Ready · plan full`).
  - Still-blocked rows are muted (`lock.fill`, `stays Blocked · Oct 13`).
  - The `=x` close card gains the same "Unblocked" section under its task rows, with
    `→ next BOB`.
  - In the Pomodoro block diff, inserted lines are already `change: "added"`. A new
    optional per-line `reason: "unblocked"` lets the app add a small 🔓 to those rows.
    The successor then visibly sits under its struck predecessor.
- **Notification, after submit.** One extra body line, nothing else:

  | Situation | Body line |
  | --- | --- |
  | One successor (`!`) | `🔓 Next in FIX: Re-launch all failed agents on apollo!` |
  | Several | `🔓 2 linked → FIX: Re-launch…, Review and close all memory beads` |
  | Mixed | `🔓 1 linked → FIX · 2 stay Ready (plan full)` |
  | Close | `🔓 Next BOB: Re-launch all failed agents on apollo!` after the existing `N tasks · K completed` line |

  - Add `🔓` lines to the batch notification for every completion item.
  - "Open Note(s)" must count the daily note when any link was added (fix the
    `ledger != nil` heuristic).

**CLI (`bob capture` human output):**

```text
✓ completed [*] → [x] Fix apollo machine!  sase.md ^fix-apollo
  ledger  Task Link struck in FIX · Task Link moved FIX → BOB (struck) · 2026/20261009.md
  🔓 linked [?] → [*] Re-launch all failed agents on apollo!  sase.md ^re-launch-apollo-agents  → FIX
  🔒 still blocked  Start adding `sase--<name>` badges…  sase_agents_repo.md  scheduled 2026-10-13
plan 3/3 themes · 10/10 links
```

**JSON (additive).** `bob capture` has no `schema_version`, and the app decodes with
`decodeIfPresent`.

```json
"unblocked": [{
  "note_path": "sase.md", "block_id": "re-launch-apollo-agents", "line": 82,
  "text": "Re-launch all failed agents on apollo!",
  "previous_status_symbol": "?", "previous_status_name": "Blocked",
  "status_symbol": "*", "status_name": "Next",
  "unblocked_by": [{ "note_path": "sase.md", "block_id": "fix-apollo", "text": "Fix apollo machine!" }],
  "link": { "day_file": "2026/20261009.md", "entry_line": 37, "entry_name": "FIX",
            "entry_status": "queued", "line": 40,
            "block_link": "[[sase#^re-launch-apollo-agents]]", "block_id_created": false },
  "not_linked": null
}],
"still_blocked": [{ "note_path": "sase_agents_repo.md", "block_id": null, "line": 21,
  "text": "Start adding `sase--<name>` badges…", "reason": "scheduled",
  "scheduled": "2026-10-13", "open_prerequisites": 0 }]
```

- Placement: on `task_complete` and, new, on `pomodoro_close`.
- `not_linked` is one of `already_planned`, `not_planned_today`, `plan_full`,
  `breaker`, `no_open_pomodoro`, `project_task`, or `disabled`.
- The existing `unblocked[]` fields keep their meaning, so older app builds render
  `[?] → [*]` correctly with no change.

### 6.5 Performance design

**bob-cli** (do `bob-cli-5v` first):

1. **A lazy batch `VaultSnapshot`.**
   - It is built on first need: an `&` item, a `!` item, or a close whose selection
     completes something.
   - Plain captures, starts, adjustments, and closes that complete nothing never read
     the vault. The prototype puts them at 0.04 s, against 0.25 s today.
2. **One read, shared.** `&` discovery, `!` resolution, recovery, and the successor
   index all use the same snapshot. The second read in `!` disappears.
3. **Parallel and prefiltered.**
   - Read files across `std::thread::scope` workers as bytes.
   - `memchr::memmem` for `dependsOn` and `id::` decides which notes are parsed for the
     dependents index (24 and 41 notes today).
   - The proxy (`rg`) suggests about 30 ms for the full pass on apollo.
   - Discovery for the `&` picker still parses everything, but only when `&` is present.
4. **Budget.**

   | Draft | Target on apollo | Today |
   | --- | --- | --- |
   | `!` / `=x!` dry run | ≤ 60 ms | 0.38 s |
   | plain capture | ≤ 40 ms | 0.25 s |

   Re-measure on the Mac via the existing `preview` signposts. If the Mac misses these,
   the next lever is an mtime-keyed dependents-index cache under `~/.cache/bob/` (one
   `stat` walk, about 30 ms, plus re-reads of only the changed notes). That is still
   not a daemon, so the thin-client decision stays closed.

**Obsidian (cycler):**

- Find successors from the Tasks plugin cache:
  - `getTasks()` when `getState() === "Warm"`, with the closed ids forced closed and
    open buffers overriding the cache. This is the pattern nav's dependency stage
    already uses (`590-plugin-dependency-stage.js:188-260`).
  - Then read only the few candidate notes to preimage-check and write.
- This replaces the current sequential `await vault.cachedRead` over every note on every
  close (`130:142-160`). Keep that scan only as the fallback when the cache is cold.
- The visible close stays synchronous. The successor pass runs in the existing
  `referenceMutationQueue` right after recovery. Target: toast within ~50 ms of the
  keypress.

### 6.6 Reliability

- **Atomicity.**
  - Capture: everything joins the existing staged batch, so the close, recovery, minted
    IDs, status changes, and links commit or roll back together.
  - Obsidian: the close lands first, as today. The successor pass is best-effort and
    preimage-checked.
  - A failure leaves the successor recovered but unlinked, and the card says so
    (`⚠ couldn't link 1 — <reason>`). The hooks never add links, so there is no silent
    later write.
- **Ordering inside the cycler.** Steps, in order:
  1. capture the anchors (pre-write);
  2. close;
  3. recover and link, as one planned pass. This replaces "Ready, then Next" with a
     single status write.
  4. retire embeds;
  5. show the notice.
- **Concurrency.**
  - Open editors are written through `editor.replaceRange` as one transaction per note.
  - Closed notes go through `vault.process` with a staleness check.
  - A capture from the Mac while Obsidian is open is the existing file-change path.
- **Interaction with the hooks.**
  - Successors are linked once, under the owning entry. Hooks deduplication would remove
    later duplicates anyway.
  - The hooks promote linked tasks to Next, which agrees with what was written.
  - Derived Blocked stays authoritative. If the predecessor is reopened, the successor
    re-blocks (Blocked overrides lanes), and Pomodoro promotion then lifts the reopened
    prerequisite to Next.
- **Contract tests.**
  - The vectors in §6.8 run in Rust (`task_complete` tests) and in cycler JS tests.
  - Add a capture integration test that a plain capture opens no unrelated notes, which
    guards the perf fix.

### 6.7 Undo

- **Per successor:** Alt+N on its link releases it. That removes the link and lowers
  Next to Ready. It is the exact inverse of what was written, uses an existing gesture,
  and is taught in the card's hint chip.
- **Whole gesture:** reopen the predecessor (Ctrl+Enter on its struck link). In phase 5,
  reopen also removes the unblocked links that the same session added for it, if they
  are still untouched (unchanged line, successor still `[*]` with no Work Log). The
  successor is then re-blocked. This uses an in-memory receipt; nothing is stored in
  Markdown.
- **Not an undo:** editor `u` in the daily note. It removes the inserted lines but leaves
  the successor's sticky Next in its own note. Document this, as it is the general
  sticky-lane cost.

### 6.8 Conformance vectors (UL)

| # | Situation | Outcome |
| --- | --- | --- |
| UL1 | Predecessor linked in the running entry; one dependent, sole prerequisite | Link inserted after the struck link's subtree; dependent `[?]`→`[*]`; `unblocked_by` names the predecessor |
| UL2 | Predecessor in a queued entry; `!` moves the struck link to running | Successor at the vacated line of the queued entry |
| UL3 | Dependent has a second open prerequisite | Not linked; `still_blocked{waits_on:1}` |
| UL4 | Dependent's only other blocker is a future `scheduled` date | Not linked; `still_blocked{scheduled}` |
| UL5 | Dependent already linked under another open entry | Not linked (`already_planned`); status → Next |
| UL6 | `=!` closes the entry, nothing carried, a later entry exists | Placeholder `- [ ] () — NAME` created holding only the successor |
| UL7 | `=x` with carried links | Successor appended after the carried lines in the placeholder |
| UL8 | `!` on a task with no live link today | Recovers to Ready; `not_planned_today`; ledger untouched |
| UL9 | `plan.strict`, before = 10 = cap, 3 successors | One linked (priority, then same note, then path/line); two `plan_full` |
| UL10 | Dependent has no `^block-id` | `^id` minted, unique in its note; link uses it; `block_id_created: true` |
| UL11 | Dependent is `^prj` | Not linked (`project_task`); recovery as today |
| UL12 | Two predecessors in one gesture share a dependent | Linked once, after the first predecessor in ledger order; `unblocked_by` lists both |
| UL13 | Dependent in a note whose basename is ambiguous | Link uses `[[dir/note#^id]]` |
| UL14 | `plan.link_unblocked: false` | Today's behavior (Ready); `not_linked: disabled` |
| UL15 | Predecessor's link was under a completed entry | Successor goes to running, else the first open entry; neither → `no_open_pomodoro` |
| UL16 | Same close re-applied (already done) | No writes |
| UL17 | One gesture would add 6 links | None added (`breaker`); all reported |

---

## 7. Implementation plan (one epic, five phases)

| Phase | Repo | Content | Depends on |
| --- | --- | --- | --- |
| P0 `snapshot` | bob-cli | `bob-cli-5v`: lazy, shared, parallel, prefiltered vault snapshot; `!` reads the vault once; a "plain capture opens no notes" test | — |
| P1 `contract` | bob-cli | New `docs/task-dependencies.md` §5.1 "Unblocked links" (rule, placement, budget, vectors UL1–17); `plan.md` budget clause; `capture.md` rows; via `/sase_memory_write`: decision record "A closed planned task hands its slot to its unblocked dependents" (rejected: B–F above), glossary term, and amend `task-status-is-derived` (recovery to derived rank) | — |
| P2 `capture` | bob-cli | `task_complete::successors` engine; wire into `!` and close (adds recovery to `=x!`, A7); JSON and human output; config switch | P0, P1 |
| P3 `mac` | bob-mac-capture | Decode `unblocked[].link/unblocked_by/not_linked`, `still_blocked`, `pomodoro_close.unblocked`; preview rows plus the close-card section; 🔓 diff-row badge; notification line; Open Notes fix; render fixtures | P2 |
| P4 `obsidian` | bob-plugins | cycler: anchors in every Ctrl+Enter branch; Tasks-cache dependents index; port the planner with the UL vectors; single recover-and-link write; minting. nav: additive `api.notice` v1 (`show(model)` with the `is-unblock` card) and walk composition. ledger-tools: config key. `bob plugins sync`. | P1 |
| P5 `polish` (optional) | bob-plugins | Reopen removes untouched unblocked links (receipt); ledger-tools 🔓 read-time glyph; route Alt+] closes through `finalizeClosedTasks` (`bob-cli-3k`) | P4 |

P3 and P4 can run in parallel once P2's JSON is final. P0 is worth landing even if the
feature never ships.

---

## 8. Open questions for Bryan (with my defaults)

1. **The "same Pomodoro" anchor** when `!` completes a task planned in a *queued* entry
   while another session runs. My default is the planned slot (A3). The alternative is
   the running session, for momentum.
2. **The budget default.** My default is soft (link all, red meter) and binding only
   under `plan.strict` (A4). The alternative is always enforcing
   `max(cap, before)` — "the successor inherits the slot" — which suits a ledger that
   lives at 10/10.
3. **Inbox and `#ref` successors.** My default links them: the dependency was
   deliberate. I do not trigger inbox routing prompts, because automation never prompts.
4. **The kill switch.** My default is to add `plan.link_unblocked` (A9).
5. **Reopen criterion for this decision.** If more than about a third of unblocked links
   are released or unlinked the same day, revisit with explicit successor edges
   (alternative E). Counting this needs the cycler to log link and release pairs. A
   cheap way: a `🔓` entry in a debug log, or by diffing ledgers in `bob plan`.

---

## 9. Recommended solution

Build **"a successor takes its predecessor's slot"**:

- When a Bob close gesture completes a task that was planned in today's ledger, every
  open dependent that this close *fully* unblocked is linked into the predecessor's
  planned slot. That is either the line right after the predecessor's link, or the carry
  placeholder `- [ ] () — NAME` when that Pomodoro closed.
- The successor becomes Next in the same atomic write. A block ID is minted if missing.
  No freshness stamp is written.
- Dependents that stay blocked, or that weren't planned today, are reported but never
  linked. A future `scheduled` date is the per-task "not right after" switch.
- Explain it once, beautifully:
  - Obsidian: a nav `Unblocked` card (what → where → why, plan meter, release hint),
    folded into the walk toast on landings.
  - Bob Mac Capture: the same story in the live preview before submit, and one 🔓 line
    in the notification after.
  - CLI: a 🔓 row.
- Undo is Alt+N per link (the exact inverse); later, reopening the predecessor undoes
  the whole gesture.
- Specify it once (`task-dependencies.md` §5.1, vectors UL1–17) and implement it twice:
  Rust capture and task-status-cycler. The Mac app only decodes.
- Ship the performance groundwork first: one lazy, shared, parallel, prefiltered vault
  snapshot in bob-cli (`bob-cli-5v`), and a Tasks-cache dependents index in the cycler.
  The feature then *reduces* close and preview latency instead of adding to it.

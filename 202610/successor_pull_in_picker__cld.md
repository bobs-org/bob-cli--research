# Successor Offers: replacing automatic successor links with an explicit pull-in picker

**Researcher:** cld (one of five independent reports). **Date:** 2026-10-13.

**Baselines:** bob-cli `c32143ea`, bob-plugins `4f0cc94` (task-status-cycler 1.37.0,
bob-navigation-hotkeys 2.31.0 with nav `api` v3, block-id-prompt 1.30.0, bob-ledger-tools
1.49.1), and bob-mac-capture `eed300d`. The vault was read-only at its state of
2026-10-13 ~08:15, including its git history.

**Request (paraphrased).** Stop auto-adding successor Task Links when a close unblocks
tasks. Instead, when a close completes a task that blocks others (by any supported
method), ask which unblocked tasks, if any, to pull in as successor links:

- one or more new selection panels, plus probably a separate solution for Bob Mac
  Capture (verify whether that is needed);
- drop the "at most 5 successors" limit;
- when the close unblocks a project's `^prj`, the panel offers every open task in that
  project. You expected closing `sase.md ^bar` to pull in `sase_foo.md`'s tasks, and it
  did not;
- the same applies to the `^prj` / parent `^prj` pull-ins that happen when a close
  empties a project.

---

## 0. Bottom line

**Yes, build it. The picker is the right model, and the vault already shows why.** At
07:59 this morning, a Pomodoro close completed `sase ^post-blog-prj`, which had 11
dependents. The breaker linked none of them. Within 3½ minutes you hand-linked two of
the 11, **one under JOB and one under SASE**, and moved several more into
`sase_post_blog.md` (§1.3). That is the workflow a picker serves: pick a few out of
many, sometimes into different sessions. Automatic linking can't do that, and the
breaker gives up entirely.

My recommended design is **Successor Offers**: *closing still unblocks immediately; you
choose what joins today's plan*.

1. **One rule in both engines.** The close commits recovery exactly as today:
   - Blocked → Ready;
   - `#prj_is_blocked` stripped;
   - `[unblocked::]` ticklers written;
   - `#hide` removed from an emptied project's `^prj`.

   What used to be auto-linked becomes an **offer**. Only offers you pick get linked.
   Doing nothing is always safe, because the TICKLER and NEW review tiers already
   resurface every unblocked task the next morning.
2. **The offer set grows to match your mental model:**
   - direct dependents this close fully unblocked (as today);
   - every open, visible, now-unblocked task of a project whose `^prj` this close
     unblocked (this is new, and it is the `^bar` → `sase_foo` case);
   - the project-empty `^prj` pull-ins (triggers a, b, c).
3. **No limit.** The 5-successor breaker is deleted from both engines.
4. **Three thin surfaces over one model.**
   - **Obsidian:** a multi-select picker modal opens *after* the close commits. It
     reuses nav's Depends-on convention (`⇥ mark · ↵ apply N · esc dismiss`). Walk
     landings defer it.
   - **Bob Mac Capture:** it needs its own SwiftUI picker, but **not a separate
     mechanism**. The dry-run already computes the offers before Return. Your choice
     travels in bob's draft grammar (`!sase:bar>1,3`), so the write stays one atomic
     `bob capture`.
   - **CLI:** the same `>` grammar, plus numbered offer rows in the output.
5. **A pick is a human choice, so it uses manual-link semantics:** Next, a minted block
   ID if missing, and a `[fresh::]` stamp, like Ctrl+Shift+Enter. A pick can also choose
   its Pomodoro, because the default slot was wrong for one of the two tasks you
   hand-linked this morning.

Section 3 lists the requirement adjustments, and §6 gives the recommended solution with
a phased plan.

---

## 1. What exists today (verified)

### 1.1 The current rule in one paragraph

When a Bob close gesture completes a task P, both engines run one planner
(`docs/task-dependencies.md` §12.2):

- Rust: `src/native/task_complete/successors.rs:544` `plan_successors`.
- JS: `task-status-cycler/src/085-successor-plan.js:585` `planSuccessors`.

For each open dependent D whose last blocker this gesture removed, the verdict ladder
(`successors.rs:702-748`, `085-successor-plan.js:771-928`) is:

1. still blocked: `waits_on`, then `scheduled`, then `project`;
2. `^prj` → recover only (`project_task`);
3. `#hide` → recover only (`hidden`);
4. already live-linked → recover only (`already_planned`);
5. no predecessor planned today → recover only (`not_planned_today`);
6. kill switch → recover only (`disabled`);
7. otherwise **SUCCESSOR**: link D right after P's bullet, or into the closing
   session's same-name continuation, and raise D to Next.

On top of that:

- When a `^prj` recovers, its `[?]` residents recover **recover-only**, as
  `project_member` (`project_close.rs:224-292`, `085-successor-plan.js:868-885`).
- When a close empties a project, its `^prj` is pulled in (§12.10, triggers a/b/c).
- If more than 5 successors qualify in one gesture, **none** are linked (the breaker).

### 1.2 Why closing `^bar` didn't pull in `sase_foo.md`'s tasks

This is not a bug: the code did exactly what the spec says. The vault history shows each
step:

| Time (Oct 13) | Vault commit | State |
| --- | --- | --- |
| 08:04:54 | `39b35d80` | `sase_foo.md` converted to a project: `^prj` `[ ]` `#hide`, plus two `[ ]` residents |
| 08:05:11 | `d6e117b8` | `^prj` gets `⛓️ DEPENDS ON: [[sase#^bar]]` → `[?]`; both residents → `[?] … #prj_is_blocked` |
| 08:06:34 | `1cb0f4ba` | `^bar` (`[*]`, linked in the running BOB session) closes → `[x]`, link struck. `^prj` → `[ ]` (still `#hide`); both residents → `[ ]`, tag stripped. **No successor bullets inserted.** |

Why nothing was linked:

1. **`^prj` (R).** `sase_foo` still had two open residents, so it was not "emptied" and
   no §12.10 pull-in applies. §12.2 step 4 then says *"D's block id is prj → recover;
   not_linked: project_task"*.
2. **Residents.** §12.2 PROJECT RECOVERY (`task-dependencies.md:846-853`) says residents
   recover *"recover-only, never successor-linked"*. In Rust, `recover_project_members`
   (`project_close.rs:269-289`) even downgrades an existing `Successor` verdict to
   `Recover("project_member")` with `anchor: None`.
3. **This was a decision, not an oversight.** The `unblocked-tasks-resurface-as-ticklers`
   record lists **"Successor-linking residents"** as a rejected alternative: *"Residents
   recover recover-only."* So "I thought we did this already" is a memory mismatch. Doing
   it now means writing a new decision record that partly supersedes that one (§6.9).
4. **No `[unblocked::]` on the residents.** They carry no `[fresh::]`, so the WRITE skip
   applied. As unstamped tasks they surface in tomorrow's NEW tier instead.

Both engines implement the same ladder, so the result would have been the same from
Obsidian or from Mac capture.

### 1.3 The "limit of 5" is a breaker, and it fired this morning

The limit is not "pull in at most 5". It is **"more than 5 → pull in none"**, and
pull-ins are exempt from it. It lives in four places:

- Rust: `MAX_SUCCESSORS_PER_GESTURE = 5` (`successors.rs:54`), applied at `:788-804`.
- JS: `SUCCESSOR_BREAKER_LIMIT = 5` (`085-successor-plan.js:7`), applied at
  `089-successor-project.js:890`.
- Copy: `not linked, more than 5` / `not linked · more than 5` (Rust `capture/output.rs:2331`,
  nav `285-unblocked-notice.js:7-17`, Mac `CaptureSuccessorPresentation.swift:222`).
- Tests: SL17 and PP15.

**Live evidence.** One prerequisite in the vault has a fan-out of 11
(`sase__post-blog-prj`):

| Time | Commit | What happened |
| --- | --- | --- |
| 07:59:36 | `abd4ca6b` | The SASE session `0750-0815` closed as `0750-0800`, completing `[[sase#^post-blog-prj]]`. This was a plain link completed by a close, so it came from the `=x!`/`=!` capture family. All 11 dependents went `[?]` → `[ ]`, with `[unblocked:: 2026-10-13]` where `[fresh::]` existed. The day file changed only by the close: **the breaker linked nothing.** |
| 08:00–08:02 | `eb1d5a3b`, `3bed7e4c`, `a37e66d9`, `a2fcc6ae` | Several of the unblocked tasks were moved into `sase_post_blog.md`. |
| 08:02:55 | `59f8ba60` | `[[sase_goals#^ref-2026-goals-as-first-class-abstractions]]` was hand-linked under **JOB**. |
| 08:03:12 | `b87c4e7f` | `[[sase_memory#^ref-memory-built-instruction-migration-epics]]` was hand-linked under **SASE** (the closed session's same-name successor entry). |

Lessons from this morning:

- A real close fanned out past the breaker on the feature's fourth day.
- You wanted **2 of 11**, so neither "all" nor "none" was right.
- **One of the two belonged in a different session** from the predecessor's slot.

### 1.4 Close paths and code sites

| Surface | Close gestures that run successor/pull-in logic | Entry point |
| --- | --- | --- |
| bob-cli capture | `!note:id`; `=x…`/`=x!M`/`=!`; `^route:id=x…` and `@route:id=x…`; `<text> @route:id=x…` | `capture/task_complete.rs:13`, then `engine::plan_successors` (`:259`); `capture/pomodoro_close.rs:621` `plan_close_successors` (callers at `:1415`, `:2032`, `:2305`). The batch net pass is at `capture/plan.rs:156-165`. |
| Obsidian cycler | Ctrl+Enter on a Task Link, the task line, or a Pomodoro line (closed embeds); walk Ctrl+Enter; Alt+] into Done (single or counted) | One choke point: `finalizeClosedTasks` (`130-plugin-references.js:52`), then `planAndApplySuccessorsNow` (`137-plugin-successor-project.js:11`), then `presentSuccessorModel` (`135-plugin-successors.js:663`). |
| Nav notice | The `Unblocked` card | `285-unblocked-notice.js` (`showUnblocked`, `api.notice` v1) |
| Mac | Renders the `!` card and `=x` card Unblocked sections; the notification line | `CaptureSuccessorPresentation.swift`, `CapturePanelView.swift:2229-2310`, `CapturePanelView.swift:3246-3316` |

Two corrections to things that are easy to assume:

- **There is no `bob task complete` command.** `bob task` has only `archive`,
  `reconcile` and `reroll` (`src/runner.rs:149-176`). "task-complete" is the shared
  engine module.
- **No Task Card commit triggers successors.** The Task Card has no Done path; its
  cancel ends in `api.recoverBlockedDependents` (recover only).
- **Never triggers successors:** cancel, reopen, raw checkbox clicks, and
  `bob task reconcile`. These stay out of scope (§3, A9).

### 1.5 Vault numbers (2026-10-13)

| Measure | Value | Why it matters |
| --- | --- | --- |
| Open `#task` lines outside `done/` | 468 | — |
| Open tasks carrying `[id::]` (the only possible unblockers) | 27 (≈6%) | The `[id::]` gate still makes ~94% of closes free, and the picker stays rare. |
| Open dependents | 31 (19 `[?]`, 10 `[ ]`, 2 `[*]`) | — |
| Prerequisite fan-out | 14 × 1, 2 × 3, **1 × 11** | The breaker is a real constraint, not a theory. |
| Active projects with an open `^prj` | 35 | — |
| Open residents per project | median 2, p90 8, **max 222** (`sase.md`), then 31 (`bob.md`) | A project offer can be large, so the picker needs grouping, a filter, and "mark all". |
| Open `^prj` lines with a Depends-On | 1 (the `sase_foo` test) | Project blocking shipped this week, so the resident case will grow from zero. |

---

## 2. Critique: is this a good idea?

### 2.1 Why yes

1. **Fan-out is where automatic linking fails, and projects make fan-out normal.** A
   project unblock releases every resident: 2 at the median, 8 at p90, 222 at worst.
   Auto-linking them all would wreck the plan budget (`max_links: 12`), and auto-linking
   none is what happens now. Choosing is the only correct answer for this case, and the
   breaker already concedes that for more than 5.
2. **A wrong auto-link is expensive.** A link raises the task to sticky Next, and only
   Alt+N lowers it (`task-lanes-are-sticky`). A wrong pick costs nothing, because you
   never make it.
3. **The rules are hard to predict.** Even you expected different behavior from
   `^bar`. The ladder has nine steps and a breaker. An explicit list that shows
   "here is what this close unblocked" replaces prediction with a choice you can see.
4. **Destinations differ.** This morning's two picks went to two sessions. Auto-linking
   can only use one heuristic slot.
5. **It is rare.** Only ~6% of open tasks can unblock anything, so the prompt appears a
   few times a week. The interruption cost is small, and the decision it asks for is
   real.

### 2.2 What it costs

1. **The zero-keystroke hand-off is gone.** For the classic one-to-one case (fix X, then
   relaunch Y), you now press one key (↵) that you didn't need before. The design keeps
   that to exactly one key (§6.4).
2. **A modal at the moment of completion.** Obsidian needs care so it never steals focus
   mid-walk, and never fires when nothing was offered.
3. **Two writes in Obsidian.** The close commits first, and the pick is a second queued
   pass. That pass must re-validate, and undo must cover both.
4. **The grammar grows.** `>` selection becomes a new capture part, and four parsers
   (Rust parse/plan and the Mac spans) must agree.
5. **Two UIs to build:** an Obsidian modal and a SwiftUI picker. The planner, contract
   and vectors stay shared.
6. **Decision churn.** Successor linking shipped on 10-09 and pull-in on 10-12/13. This
   reverses part of a 4-day-old design and a rejected alternative in
   `unblocked-tasks-resurface-as-ticklers`. That is acceptable, because the new evidence
   (§1.3) is exactly the "reopen if breaker notices become routine" condition the
   successor research set for this choice.

### 2.3 Where the request needs tightening

1. **"Instead of automatically adding" must not mean "instead of unblocking".** Recovery
   (Blocked → Ready, tag strip, `[unblocked::]`, `#hide` removal) is derived truth that
   the hooks would write within 15 minutes anyway. It stays automatic. **Only the link
   becomes a choice.**
2. **"All open tasks that belong to that project"** should mean visible, unblocked,
   unplanned residents:
   - leave out `#hide` residents;
   - show residents with their own open prerequisite or a future date as muted 🔒 rows,
     not as choices;
   - leave out residents already linked today.

   It should also include residents that were `[ ]` rather than `[?]`, for example ones
   added since the last reconcile. Today's `recover_project_members` only looks at `[?]`
   residents (`project_close.rs:251`).
3. **Sub-project descendants are not "unblocked" by the close today.** Under
   `close_recovers_subprojects = no`, they stay `[?]` and tagged until reconcile.
   Offering them would mean linking Blocked tasks, which is forbidden. They stay out of
   v1 (§3, A6).
4. **"Via any supported method" includes closes of tasks that are not planned today.**
   Today those link nothing (`not_planned_today`), because there was no slot to hand
   over. With an explicit pick, they can be offered with a fallback destination (A5).
5. **On the Mac, the panel hides on success** (`CapturePanelModel.swift:5275`). A picker
   shown *after* submit would need new lifecycle state and a second, non-atomic write.
   A picker *before* submit needs neither (§4.2).

---

## 3. Requirement adjustments (called out)

| # | Request | My adjustment | Why |
| --- | --- | --- | --- |
| **A1** | Prompt instead of auto-linking | The close still **commits recovery automatically**. Only the Task Link and the Next raise are chosen. Dismissing = nothing linked. | Recovery is derived state the hooks would write anyway. The TICKLER and NEW tiers make dismissal safe. |
| **A2** | Remove the 5 limit | Delete the breaker entirely (Rust, JS, copy, SL17, PP15). Large lists get a filter and "mark all", not a cap. | Picking is explicit. The breaker was all-or-nothing, not "at most 5", and it fired on a real 11-way close. |
| **A3** | Include all of an unblocked project's open tasks | Offer every open, **visible**, unblocked, unplanned resident, `[?]` or `[ ]`, grouped under the project. Residents still blocked by their own reasons are muted 🔒 rows. Hidden residents are left out. The non-empty `^prj` itself is the group header, not a choice. | Matches the intent without offering hidden or Blocked work. |
| **A4** | Apply to project-empty pull-ins (triggers a/b/c) | Same rule: R becomes an offer. `#hide` removal still happens unpicked, as sync would within 15 minutes. | Matches the request, and keeps sync and the pull-in predicate aligned. |
| **A5** | "Any supported method" | Offer even when no predecessor was planned today. Destination = the entry `@route:block-id` would pick (the task's open entry, else the implicit current/next one). | A deliberate pick needs no slot to hand over. Without this, a close outside the ledger prompts for nothing. |
| **A6** | (implied) sub-project tasks | **Out of v1.** Descendants of an unblocked project stay `[?]` + tag until reconcile, as today. The picker shows a muted line, `N sub-projects recover at next reconcile`, read from R's `🧩 Sub-projects:` marker. | Offering them needs immediate descendant recovery on close, which `subprojects-inherit-project-blocking` rejected. Reopen it separately if wanted. |
| **A7** | (unstated) freshness | **A pick stamps `[fresh::]`** and clears `[unblocked::]`/`[keeps::]`, like Ctrl+Shift+Enter. This reverses §12.4 "freshness never touched" for picked rows only. | A pick is a human confirmation by the glossary's definition, not automation. It also resolves an ordering wrinkle: Obsidian's pass 1 writes `[unblocked::]` before the pick lands the task in Next. |
| **A8** | (unstated) destination | Each pick may target a different Pomodoro. The default is the predecessor's slot (§12.3), with an override per row. | One of this morning's two hand-links went to a different session. |
| **A9** | "Any supported method" | **Cancels stay recover-only** (no picker), as do reconcile, raw checkbox clicks and reopen. | "Won't do" seldom means "do the follow-up next". The cancel surfaces (Task Card, Alt+[) have their own UI. Easy to add later. |
| **A10** | (unstated) kill switch | `plan.link_unblocked` becomes `ask` (default) or `off`. `true` reads as `ask` and `false` as `off`. **No `auto` mode in v1.** | Keeps one code path, and `off` keeps the honest recovery half. An `auto_single` mode is the obvious future addition if every prompt turns out to be "↵". |
| **A11** | "Separate solution for the Mac app" | The Mac gets its own **UI** but no separate **mechanism**: picks ride in bob's grammar (`>S`), with one atomic `bob capture`. | `mac-capture-is-a-thin-client`. Details in §4.2. |

---

## 4. Design questions and how I resolved them

### 4.1 Pick before the write, or after it?

| Surface | Before (selection is part of the close's write) | After (close commits; pick is a second write) | Choice |
| --- | --- | --- | --- |
| Rust / CLI | Natural. Capture plans the whole batch before writing, and the anchors keep today's exact semantics, including the vacated-slot rule for `!`. | Needs a "pull in for an already-Done P" mode, with anchors re-derived after retirement moved the struck link. | **Before** (grammar) |
| Mac | The dry-run already shows the offers before Return. The pick goes into the draft, and one atomic call follows. | The panel must stay open after success, needs a multi-select step, and needs a second `bob` call with a new linking contract. `@route` can't target slots, can't mint IDs, and only resolves root notes (`capture/plan.rs:1588-1600`). | **Before** |
| Obsidian | Ctrl+Enter would wait on a modal while holding the reference-mutation queue, Esc would become ambiguous ("cancel the close?"), and buffer edits in between would race. | The close is instant and unchanged. The picker is an optional follow-up, Esc is harmless, and the second queued pass re-validates. | **After** |

The model stays the same even though the timing differs. Both engines compute the same
offer rows, with the same numbering and destinations. Rust applies a selection carried
in the item. JS applies a selection returned by the modal.

### 4.2 Does Bob Mac Capture need a custom solution? Verified: a custom UI, but not a custom mechanism

Facts:

- **The panel hides unconditionally after success.** `completeSubmit` clears the draft,
  sets `previewState = .idle`, posts the notification and calls `panelDismisser()`
  (`CapturePanelModel.swift:5213-5282`, hide at `:5275`).
- **Nothing in the capture UI is multi-select.** `CapturePickerState` holds one
  `selectedRowID`, there is no `Toggle`, and there is no `Set`-based selection.
- **Notifications can't host a list.** Their action categories are fixed per category,
  for example "Open Note" (`NotificationService.swift:285-292`).
- **A pre-submit inline-prompt pattern already exists.** `taskIDPrompt` and
  `pomodoroNamePrompt` set `inlinePromptVisible` (`:677`), which blocks `submit`
  (`:1408`). The `⌘↩` "accept & capture" picker flow already chains *prompt → splice the
  text bob returned → `followUp: .submit`* (`CapturePanelModel.swift:3306-3336`).
- **Numbered-row grammar in a live card is an established Mac idiom.** Examples are
  `=x1,2` and `=x!2`, and `=~2` with the card hint "Type ~2 to drop task 2" (README
  `:956`, `:1681`).
- **Current Mac gaps.** The app doesn't decode `trigger`, `hide_removed` or
  `project_empty`, and it has no copy for `project_member`. `notLinkedReasonText` falls
  through to the raw string, so `^bar`-style rows read "Ready · project_member"
  (`CaptureSuccessorPresentation.swift:214-237`).

Conclusion:

- The Mac needs a **SwiftUI multi-select picker**. Obsidian's modal obviously can't run
  there, and a notification can't hold N checkboxes.
- It needs **no separate mechanism**. Bob reports numbered offers in the dry-run, and
  the picker writes `>1,3` into the draft.
- Submit stays one atomic `bob capture`, as `mac-capture-is-a-thin-client` requires.
- A post-submit panel would be **more** custom work (new lifecycle state, a second write,
  a new contract) for a **worse** result (non-atomic, harder undo).

### 4.3 Obsidian picker: reuse what already exists

- **Base.** Nav's `FilteredPickerModal` (`200-filtered-picker-modals.js:1`) provides
  filter, ↑↓ and ↵.
- **Multi-select.** The only multi-select precedent in the plugins is the Depends-on
  stage:
  - ⇥ toggles a mark (`450-picker-keydown.js:134-142`, `400-picker-local-task.js:210`);
  - ↵ reads `apply N` when anything is marked, else it acts on the highlighted row
    (footer at `400-picker-local-task.js:158-169`);
  - Esc dismisses.

  Reuse the convention so muscle memory transfers. One offer then costs one ↵, and none
  costs Esc.
- **Ownership.** Nav owns modals and the notice family, and the cycler owns planning and
  writes. Add an additive nav API next to `api.notice`:
  `api.successors.pick(model) → Promise<{picks:[{key, destination?}]} | null>`. Nav
  stays at `api` v3 and gains a new member at v1.
- **Destination override.** Ctrl+Shift+Enter in the picker retargets the marked rows
  (or the highlighted one). It opens block-id-prompt's existing `PomodoroLinkPickerModal`
  (`085-pomodoro-link-picker-modal.js:151`), which already supports "create new named
  session" with ⇧↵. This is the same key you already use for "link to a Pomodoro".
- **Without nav.** Today's plain `Notice`, listing the offers with "not pulled in".
  Recovery has already happened.

### 4.4 Walk landings

The walk demands a **single toast and no second advance**
(`answering-advances-the-walk`). `continueReviewWalkAfter` yields a macrotask so focus
returns after a modal submit (`536-plugin-review-advance.js:340-361`). The cycler
already knows it is on a landing (`successorNoticeTarget: "return"`, from
`completeTaskAtCursor` and the vim walk branch).

So **on a walk landing, don't open the picker**:

1. Compose `🔓 3 unblocked · ⌥U to pull in` into `outcome.notice`. The key is
   illustrative; bind it to a new nav command.
2. Hold the offer set in memory for the day, using the same store pattern as the reopen
   receipt (`136-plugin-successor-receipt.js`).
3. The command **Pull in unblocked tasks…** reopens the picker over the held offers,
   re-validated.

The same command also rescues an accidental Esc. Most walk Ctrl+Enters are PRE/POST
checklist rows, which rarely unblock anything.

### 4.5 Default selection

Two options:

- **Preselect** the old auto-link set (anchored dependents and pull-ins), so that ↵
  repeats yesterday's behavior.
- **Preselect nothing.** ↵ acts on the highlighted row, ⇥ marks several, and
  Ctrl+A marks all (or the highlighted group).

**I recommend nothing preselected.** It matches the Depends-on stage, so ↵ with one
offer is still one key. Esc means "nothing" everywhere. It also avoids silently
re-creating auto-link behavior that you are asking to remove.

On the Mac and the CLI:

- `>` alone means **all**, following the `=x!` precedent where an empty part means
  "every remaining".
- `>1,3` picks rows 1 and 3.
- `>0` picks none.

### 4.6 Ordering and grouping

Offers are numbered in display order, and the numbers are stable between dry-run and
real run:

1. **Hand-offs:** direct dependents plus project-empty `^prj` pull-ins, in §12.2 ORDER
   (anchor ledger position, then note path, then line). Unanchored offers come after the
   anchored ones.
2. **One group per unblocked project:** residents in note-line order, under a header
   with the project's `^prj` text and `↗ note`. Muted 🔒 resident rows and the
   sub-project note sit at the end of the group, unnumbered.

---

## 5. Alternatives considered

| Approach | Verdict |
| --- | --- |
| **Keep auto-linking; only lift or raise the breaker** | **Reject.** Auto-linking 11 or 222 tasks is worse than none, and it still can't pick the session. |
| **Auto-link when exactly one anchored hand-off; ask otherwise** (the respected alternative from the successor research) | **Defer, as `link_unblocked: auto_single`.** It saves one keystroke in the common one-to-one case, but it adds a second behavior and goes against "start prompting". Add it only if you find yourself answering ↵ every time. |
| **Ask before the close in Obsidian** | **Reject.** It holds the mutation queue on a modal, delays the close, and makes Esc ambiguous. |
| **Post-submit picker panel on the Mac** | **Reject.** It needs new lifecycle state, a second non-atomic write, and a new contract for linking after the fact. Pre-submit picking via grammar is atomic and fits existing idioms. |
| **No modal: a persistent "Unblocked today" tray** (a dash section or Mac agenda row) | **Reject as primary.** It loses the hand-off moment and adds another list to tend. The TICKLER and NEW tiers already guarantee next-morning review. The in-memory "Pull in unblocked tasks…" command covers misses cheaply. |
| **Let reconcile or hooks offer** | **Reject.** Hooks can't prompt, and they must not invent Today. |
| **Swift computes offers, or Obsidian shells out to `bob` for them** | **Reject.** Swift would violate the thin-client rule. Shelling out ignores unsaved buffers and adds a spawn per close; bob-ledger-tools' read-only `bob stats` spawn is no precedent for a write path. |
| **Offer sub-project descendants by recovering them on close** | **Defer.** It reverses a rejected alternative in `subprojects-inherit-project-blocking`. Revisit with evidence. |
| **Offer on cancel** | **Defer.** It is harmless with an explicit pick, but cancel surfaces have their own UI and "won't do" rarely means "do the follow-up". |
| **Keep §12.4's "never stamp freshness" for picks** | **Reject.** A pick is a human choice, the same as Ctrl+Shift+Enter. Not stamping leaves the `[unblocked::]` tickler on a task you just put in Next. |

---

## 6. Recommended solution: Successor Offers

### 6.1 The shared rule (replaces §12.2's SUCCESSOR, PROJECT RECOVERY and BREAKER clauses)

```text
C, GATE, ANCHORS, CANDIDATES      : unchanged (§12.2)

Ladder for each dependent D       : unchanged through step 6 (still-blocked rows,
                                    ^prj → project_task, #hide, already_planned)
  7'. kill switch off             → recover; not_linked: disabled (no offers)
  8'. otherwise                   → OFFER{group: dependency,
                                          destination: anchor ?? implicit(D)}

PROJECT OFFERS (replaces PROJECT RECOVERY):
  when a ^prj R recovers and its project N has no remaining own or inherited reason:
    every open resident T of N:
      own open prerequisite / future date → still_blocked (muted; unnumbered)
      #hide                               → recover only; not offered
      live link today                     → recover to derived rank; not offered
      otherwise                           → recover ('?' → ' ', strip #prj_is_blocked,
                                            [unblocked::] per WRITE rule) AND
                                            OFFER{group: project_member, project: N,
                                                  destination: anchor(preds(R)) ?? implicit}
    (T may be '[ ]' or '[?]': A3)

PULL-INS (§12.10)                 : steps 1–4 unchanged (#hide removed at step 4);
                                    steps 5–9 → OFFER{group: project_empty} unless
                                    already_planned / disabled / cancelled

BREAKER                           : deleted

SELECTION S (per gesture)          : Rust: the item's `>` part; JS: the picker result.
  for each offer o in S (re-validated in JS pass 2):
      status ' ' / '?' → '*'   ('*' and '/' unchanged)
      mint ^block-id if missing (§12.4 SB rule)
      stamp [fresh:: today] (clears [unblocked::], [keeps::])          (A7)
      insert "<indent>- [[link]]" at o.destination (§12.3 slot / closing rules,
        or a named entry chosen by the override, created like `@route:id#name`)
  each unpicked offer: stays at its recovered rank; row not_linked: not_selected
```

Notes:

- **No recursion.** Picking D still doesn't complete D (SL13 is unchanged).
- **Rust anchors are unchanged.** Selection happens inside the same staged item, so the
  vacated-slot rule for `!` (SL2) and the closing-continuation rules (SL7, SL24) still
  hold.
- **JS pass 2 re-resolves anchors by meaning, not line number.** It finds P's (now
  struck) link and the closed entry's continuation or same-name entry, the same way the
  reopen receipt finds untouched bullets. If an anchor is gone, it falls back to
  `implicit` and reports that in the confirmation notice.
- **Net batch reporting (SL20) extends to offers.** A later item in the same draft that
  links, completes or re-blocks an offered task removes its offer row.

### 6.2 JSON contract (additive under capture schema v1)

The offers stay in `unblocked[]`, so old clients still render them, as recovered rows
with a raw reason. Each offered row gains an `offer` object:

```json
{
  "note_path": "sase_foo.md", "block_id": "", "line": 7,
  "text": "Some subtask",
  "previous_status_symbol": "?", "status_symbol": " ", "status_name": "Ready",
  "trigger": "dependency",
  "unblocked_by": [{"note_path": "sase.md", "block_id": "bar", "text": "bar boom bam"}],
  "link": null,
  "not_linked": "not_selected",
  "offer": {
    "n": 2,
    "group": "project_member",
    "project": "sase_foo.md",
    "destination": {"day_file": "2026/20261013.md", "entry_name": "BOB",
                    "entry_line": 41, "entry_created": false, "next_up": false,
                    "fallback": false},
    "selected": false,
    "block_id_needed": true
  }
}
```

The fields:

- `group` is `dependency`, `project_member` or `project_empty`.
- `trigger` keeps its existing meaning.
- A picked row has `selected: true`, a non-null `link`, no `not_linked`, and `*` status.
- Each item that has offers carries `"offer_choice": {"present": false, "count": 3,
  "insert_at": <utf8 byte offset>}`. The Mac uses `insert_at` to splice `>S` without
  parsing the grammar.
- New `not_linked` values: `not_selected`. The Mac copy is "not pulled in", and old Mac
  builds show the raw string.
- `unblocked[]` row semantics widen from "rows this gesture changed or linked" to "rows
  this gesture changed, linked, **or offered**". A `[ ]` resident that was offered and
  not picked now appears.
- Removed values: `breaker` is no longer emitted. Keep the Mac and nav copy for older
  `bob` builds.

### 6.3 Grammar (bob-cli owns it)

`>` is unused anywhere in the capture grammar. I checked `src/native` for `'>'`: it only
appears in URL `<…>` handling and in non-capture modules. The new part is
`>[<pick>[,<pick>…]]`, where `<pick>` = `<n>[#<pomodoro>]`:

| Draft | Meaning |
| --- | --- |
| `!sase:bar>` | Close `^bar` and pull in **every** offer |
| `!sase:bar>1,3` | Pull in offers 1 and 3 |
| `!sase:bar>2#job` | Pull in offer 2 under the JOB session (whole slug, then prefix; created like `@route:id#job`) |
| `!sase:bar>0` | Explicitly none. This suppresses the Mac prompt. |
| `=x!>1` | Close the session, complete every remaining link, and pull in offer 1 (`>` joins `*`, `!`, `~` as a close part, in any order) |
| `^sase:fix=x>` | Link into the running session, close, and pull in all offers |

Rules:

- **No whitespace.** `=x >1` stays Work Log text, which keeps the existing close-line
  entry grammar intact.
- **Errors.** An out-of-range number is an error, mirroring `=x` lineup numbers. `>` on
  an item with no offers is a harmless no-op, and `>N` with `link_unblocked: off` is a
  teaching error.
- **Spans and completion.** `capture-parse` gains a span kind (`successor_choice`).
  `capture-complete` can later list offers after `>`.
- **No new subcommand.** `cli_rules.md` forbids subcommands under `bob capture`. The
  help text for `!` and `=x` gains one line each.

### 6.4 Obsidian UX

```text
┌ 🔓 Pull in unblocked · 3 offers ─────────────────── ✓ bar boom bam ┐
│ filter…                                                            │
│ HAND-OFFS                                                          │
│ ▸ 1  Re-launch all failed agents on apollo!        → BOB   ↗ sase  │
│ PROJECT  foo bar baz                                ↗ sase_foo     │
│   2  Some subtask                                  → BOB           │
│   3  Some other subtask                            → BOB           │
│   🔒 Draft the launch post · waits on 1 more                       │
│   · 2 sub-projects recover at next reconcile                       │
│ ────────────────────────────────────────────────────────────────── │
│ ↑↓ navigate · ⇥ mark · ⌃A mark all · ⌃⇧↵ session · ↵ pull in · esc none │
│ (plan 3/3 · 10/12 → 12/12)                                         │
└────────────────────────────────────────────────────────────────────┘
```

Behavior:

- **When it opens.** After pass 1, only when there is at least one offer. With only
  recovered or still-blocked rows, the existing `Unblocked` card shows instead, minus
  its breaker variant.
- **Footer meter.** It live-updates as you mark rows (the ledger-tools plan meter on the
  projected daily text). Over budget is a warning, not a refusal.
- **Pass 2.** It runs as a new queued mutation:
  1. re-read the target notes and the day file;
  2. drop picks that are no longer open, now Blocked, already linked, or changed beyond
     a block-ID/text match;
  3. mint, set Next, stamp freshness, and insert at the destination;
  4. extend the reopen receipt.
- **Confirmation.** `🔓 2 pulled in → BOB · Alt+N releases`. Esc shows nothing.
- **Large groups.** With more than about 12 rows, project groups start collapsed with
  `+N more`; typing a filter expands them. The 222-resident `sase.md` case stays usable.
- **Same picker for every close.** Counted Alt+] batches and Pomodoro-line closes are
  one gesture, so they get one picker.

### 6.5 Bob Mac Capture UX

1. **Preview.** The `!` card and the `=x` close card number their offer rows, sharing
   one row view instead of today's duplicated markup (`CapturePanelView.swift:2229-2310`
   and `:3246-3316`). They teach `Type >1 to pull in · > for all` until a choice is typed.
   This mirrors "Type ~2 to drop task 2".
2. **Submit gate.**
   - If the item has offers and no `>` part (`offer_choice.present == false`), Return
     doesn't submit. It opens a **multi-select variant of the existing capture picker**
     with a new `.successors` source. It reuses `CapturePickerCard` and
     `CapturePickerRowView`, and adds a `Set` of selected IDs.
   - Keys: ↑↓ move, Space toggles, ⌘A marks all, ↵ confirms (the marked rows, else the
     highlighted one), ⇧↵ skips (writes `>0`), Esc goes back to the draft.
   - Confirm splices `>S` at `offer_choice.insert_at` and continues with
     `followUp: .submit`, the same chain ⌘↩ already uses with the task-ID prompt.
3. **Freshness of the offers.** `⌘↩` from the `!` picker can submit before a preview
   exists. Two options:
   - **Recommended:** a hidden internal flag, `bob capture --require-unblocked-choice`.
     Bob plans the batch, and if any item has offers but no `>` part, it writes nothing
     and returns `ok: false` with the offers. This is race-free, and it adds no extra
     spawn when nothing is offered.
   - App-only alternative: run an explicit dry-run on the existing `preview-explicit`
     lane before submitting a `!` or close draft whose preview is stale.
4. **Notification.** `🔓 Next in BOB: Some subtask (+1)` for picks. For explicit
   skips: `🔓 3 unblocked · none pulled in`.
5. **Fix in passing.** Decode `trigger`, `hide_removed` and `offer`. Add copy for
   `project_member` ("project unblocked") and `not_selected` ("not pulled in").

### 6.6 CLI human output

```text
✓ completed [*] → [x] bar boom bam  sase.md ^bar
  ledger  Task Link struck in BOB · 2026/20261013.md
  offer 1 [?] → [ ] Re-launch all failed agents on apollo!  sase.md ^relaunch → BOB
  offer 2 [?] → [ ] Some subtask  sase_foo.md · project foo bar baz → BOB · needs ^id
  offer 3 [?] → [ ] Some other subtask  sase_foo.md · project foo bar baz → BOB · needs ^id
  pull in with >1,3 · > for all · >2#sase for another session
```

With `>1,3`, rows 1 and 3 print as `linked [?] → [*] … → BOB · added ^some-other-subtask`.

### 6.7 Configuration

`plan.link_unblocked`:

- `ask` is the default. `off` means recover only, with no offers and no links.
- Accept `true` → `ask` and `false` → `off`, so existing configs keep working. Your
  config doesn't set the key today.
- Invalid values fall back to `ask` through the existing invalid-plan-config warning
  paths.
- Both the Rust config (`src/native/config/plan.rs:15,30,71,229-240`) and the cycler
  loader (`087-successor-place.js:622`) change.

### 6.8 Undo

- **One pick:** Alt+N on its link, unchanged.
- **The whole gesture (Obsidian):** a same-day Ctrl+Enter reopen of P takes back the
  picked links and restores each picked row's pre-pass line (status, freshness). The
  receipt now spans pass 1 and pass 2.
- **Rust:** no reopen take-back, as today.

### 6.9 Documentation, decisions and glossary

- **`docs/task-dependencies.md` §12:** rename it "Successor offers" and rewrite §12.2,
  §12.4 (freshness for picks), §12.5 (the `offer` object, `not_selected`), §12.6 (picker
  copy; delete the breaker copy), and §12.8 (the tri-state). Update §12.10 steps 5–9.
- **Vectors:** replace SL17 and PP15, and add **SO** (successor-offer) vectors covering:
  - the `^bar` → `sase_foo` case;
  - the 11-way `post-blog-prj` close;
  - destination override;
  - `>`, `>0` and out-of-range input;
  - pass-2 re-validation;
  - walk deferral;
  - SL20 net drops.
- **`docs/capture.md`:** the grammar table rows and `!`/`=x` help. While there, fix the
  `not_linked` list at `:3485`, which is missing `project_member`.
- **New decision record** (through `/sase_memory_write`): *"Unblocked tasks are offered,
  never auto-linked."* It partly supersedes `unblocked-tasks-resurface-as-ticklers`
  (the "successor-linking residents" rejection). It records the rejected alternatives
  from §5 and cites §1.3 as evidence.
- **Glossary:** "Successor Offer". There is no "Successor Link" term today.

### 6.10 Phased plan (one epic)

| Phase | Repo | Scope | Depends on |
| --- | --- | --- | --- |
| **P1 contract** | bob-cli | The §12 rewrite, SO vectors, the grammar rows in `docs/capture.md`, the `docs/plan.md` tri-state, and the decision record and glossary drafts. | — |
| **P2 Rust** | bob-cli | Offer verdicts and project offers in `successors.rs`, `project_close.rs` and `project_pull_in.rs`. Delete `MAX_SUCCESSORS_PER_GESTURE`. Parse and plan `>` for `!`, `=x…` and `^/@route:id=x…`. JSON `offer`/`offer_choice`, human output, the hidden `--require-unblocked-choice`, and the config tri-state. Tests. | P1 |
| **P3 plugins** | bob-plugins | Cycler: pass 1 offers only, pass 2 apply with re-validation, receipt, walk hold, delete `SUCCESSOR_BREAKER_LIMIT`. Nav: `api.successors.pick` modal, the "Pull in unblocked tasks…" command, card updates. Then `bob plugins sync`. | P1 (runs in parallel with P2) |
| **P4 Mac** | bob-mac-capture | Decode, numbered rows and hint, the multi-select successor picker as a submit gate, notification copy, the `project_member`/`trigger` fixes. macOS CI only. | P2 JSON frozen |

**Mixed-version window.**

- New bob with an old Mac: offers show as "Ready · not_selected". Nothing is linked
  unless you type `>`, which bob accepts but the old Mac can't highlight.
- New plugins before new bob: Obsidian prompts while capture still auto-links.

Ship P2 and P3 together to keep the window short.

**Rough size.** This is smaller than the original successor epic, because placement,
minting, anchors, receipts and the gate already exist. The new work is the two pickers,
the `>` grammar and Obsidian's pass 2.

---

## 7. Risks and open questions

1. **Prompt fatigue.** This is low at today's rates (about 6% of tasks can unblock
   anything), but project blocking will raise it. Watch whether ↵ on the first row
   becomes reflexive; if so, add `auto_single` (§5).
2. **Pass-2 races in Obsidian.** You can edit the day note while the picker is open; the
   modal blocks the editor, but sync can still land. Re-validation must drop stale picks
   loudly (`⚠ couldn't pull in 1 · daily note changed`). This reuses the existing
   `failed` row.
3. **Freshness stamp on picks (A7).** If you prefer picks to stay unstamped, so they
   surface in tomorrow's NEW tier, keep §12.4. Pass 2 must then clear `[unblocked::]`
   by hand, because a Next landing skips it.
4. **Destination UX on the Mac.** Typed `>2#job` covers the override in v1. A row-level
   session cycler in the Mac picker can come later.
5. **Large project groups.** Is a collapsed group with a filter enough for the
   222-resident area-style projects? Alternatively, cap the visible rows per group and
   require a filter to see more.
6. **Should the hand-off group be preselected after all?** I recommend no (§4.5). This
   is the one preference worth a quick gut check from you.

---

## 8. Incidental findings

- **Mac:** `project_member` has no copy and falls through to the raw string. `trigger`,
  `hide_removed` and `project_empty` are never decoded, so surfaced pull-in rows render
  as plain recovered rows. `docs/task-dependencies.md` §12.10 claims "Bob Mac Capture
  needs no change", which holds only for *linked* pull-ins.
- **Rust edge:** a resident of a recovering project that is `[ ]` rather than `[?]`, and
  has its own dependency on C, keeps a `Successor` verdict. It can be linked while its
  `[?]` siblings can't. Successor Offers removes this inconsistency.
- **Docs drift:**
  - `docs/task-dependencies.md:1012` shows `"not_linked": null`, but serde omits the key.
  - `docs/capture.md:3485` leaves `project_member` out of the `not_linked` list.
  - bob-ledger-tools now spawns `bob stats` (`236-plugin-stats-data.js:448-509`), so the
    successor research's "no plugin spawns a subprocess" is stale. That doesn't change
    the write-path recommendation.
- **Not bugs:** the `^bar`/`sase_foo` outcome (§1.2) and the post-blog breaker outcome
  (§1.3) are both exactly what the spec says.

I did not file task beads for these. Each one is either absorbed by the recommended
change or a one-line doc fix belonging to P1, and five parallel researchers filing them
would create duplicates.

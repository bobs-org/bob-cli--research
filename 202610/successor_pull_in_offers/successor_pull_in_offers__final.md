# Successor Offers: choose which unblocked tasks to pull in after a close

**Consolidated report**, 2026-10-13. It merges five independent reports (`__cdx`, `__cld`,
`__grk`, `__mus`, `__gem`) with lead-researcher verification. That verification covered
the disagreements between the reports, the claims that rested on only one report, and
the vault evidence. Baselines: bob-cli `1de9e03`, bob-plugins `4f0cc94`, bob-mac-capture
`eed300d`, and the Bob vault's git history for 2026-10-13. Nothing in code or the vault
was changed.

**Request (paraphrased).** Stop auto-adding successor Task Links when a close unblocks
tasks. Instead, when a close completes a task that blocks others (by any supported
method), ask which unblocked tasks, if any, to pull in. The requested details:

- one or more new panels, plus possibly a separate solution for Bob Mac Capture (verify
  whether that is needed);
- drop the "at most 5" limit;
- when the close unblocks a project's `^prj`, offer all open tasks of that project (the
  `sase.md ^bar` → `sase_foo.md` case did not do this);
- apply the same treatment to the `^prj` / parent `^prj` pull-ins that happen when a
  close empties a project.

---

## 0. Bottom line

**Build it. It is a good idea, and this morning's vault history shows why.** All five
reports agree on the core. My verification resolves the places where they did not.

The recommended design, **Successor Offers**, in one sentence: *closing still unblocks
everything immediately; only the Task Link (and its sticky Next raise) becomes a choice
you make in one grouped picker.*

1. **Recovery stays automatic.** These writes keep happening on every close, exactly as
   today:
   - Blocked → Ready;
   - `#prj_is_blocked` stripped;
   - `[unblocked::]` ticklers written;
   - `#hide` removed from an emptied project's `^prj`.

   What used to be auto-linked becomes an **offer**. Only picked offers get linked.
   Picking nothing is always safe, because the TICKLER and NEW review tiers resurface
   unpicked work.
2. **One offer set, three sources, one picker per gesture:**
   - direct dependents this close fully unblocked;
   - **every available open resident of a project whose `^prj` this close unblocked**
     (new; this is the `sase_foo` case);
   - the project-empty `^prj` / parent `^prj` pull-ins.
3. **The breaker is deleted** in Rust and JS. Large lists get a filter and grouping, not
   a cap.
4. **Selection is an input to the existing single write pass, in both engines.** The
   choice is made after planning and before applying:
   - **Obsidian** awaits the picker *inside* the cycler's current pass, between
     `planSuccessors` and the apply step.
   - **Bob Mac Capture** collects the choice *before* submit and passes it to
     `bob capture` as a flag.

   Both keep §12.4's "one gesture, one write set" and today's anchor semantics. This
   resolves the biggest disagreement between the reports (§4).
5. **Bob Mac Capture needs custom UI but no custom mechanism.** Return opens an in-panel
   multi-select step. Bob computes the offers and does the write; the app stays a thin
   client.
6. **A pick behaves like a manual link** (Ctrl+Shift+Enter):
   - it raises the task to Next and mints a block ID if one is missing;
   - it stamps `[fresh:: today]` and clears `[unblocked::]`.

   That matches what you did by hand this morning (§1.3).

---

## 1. What happens today (verified)

### 1.1 The rule

Two engines implement one rule (`docs/task-dependencies.md` §12):

- **Rust:** `src/native/task_complete/successors.rs` `plan_successors`, plus
  `project_close.rs` and `project_pull_in.rs`.
- **JS:** `task-status-cycler/src/085-successor-plan.js` `planSuccessors`, plus `087`,
  `088`, `089` and the plugin mixins `135`, `136` and `137`.

For each open dependent D whose last blocker this gesture closed, the verdict is one of
the following:

- **still blocked:** `waits_on`, `scheduled` or `project`;
- **recover only:** `project_task` (D is a `^prj`), `hidden`, `already_planned`,
  `not_planned_today` (the predecessor has no live Task Link today), or `disabled` (kill
  switch);
- **otherwise SUCCESSOR:** link D into the predecessor's slot (or the closing session's
  same-name continuation) and raise it to Next.

Two further rules apply:

- When a `^prj` recovers, its `[?]` residents recover as `project_member`. This is
  "recover-only, never successor-linked, outside the breaker" (`project_close.rs:217-292`).
  If a resident's own Successor verdict exists, it is downgraded to `project_member` with
  `anchor: None`.
- When a close empties a project, its `^prj` is pulled in as Next (§12.10 triggers
  a/b/c).

### 1.2 Why closing `^bar` did not pull in `sase_foo.md`'s tasks: by design, not a bug

All five reports agree, and the vault history confirms it:

| Vault commit (Oct 13) | State |
| --- | --- |
| `39b35d80` 08:04:54 | `sase_foo.md` created as a project: `^prj` with `#hide`, two residents |
| `d6e117b8` 08:05:11 | `^prj` gets `⛓️ DEPENDS ON: [[sase#^bar]]` → `[?]`. Residents → `[?] … #prj_is_blocked` |
| `1cb0f4ba` 08:06:34 | `^bar` `[*]` → `[x]`. `^prj` → `[ ]` (still `#hide`). Residents → `[ ]`, tag stripped. **No successor bullets.** |

Why nothing was linked:

1. `sase_foo` still had two open residents, so it was not "emptied" and no §12.10
   pull-in applied. The `^prj` recovered as `project_task`.
2. The residents have no `[dependsOn::]` of their own, so they were never direct
   dependents of `^bar`. They recovered through PDC2 as `project_member`, which never
   links.
3. This was a recorded decision. `decisions:unblocked-tasks-resurface-as-ticklers` lists
   **"Successor-linking residents"** as a rejected alternative.
4. They got no `[unblocked::]` because they carry no `[fresh::]` (the WRITE skip), so
   they resurface in the NEW tier instead.

**The design implication (from `__mus`) matters most:** the residents are not dependents
of the closed task at all. A picker fed only by "unblocked dependents" would still show
nothing for this exact gesture. Project-member offers must be sourced from project
recovery, by enumerating the project note.

### 1.3 The "limit of 5" is an all-or-nothing breaker, and it fired this morning

- **The rule.** More than 5 direct successors in one gesture links **none** of them.
  Pull-ins are exempt.
- **Where it lives:**
  - Rust: `MAX_SUCCESSORS_PER_GESTURE = 5` (`successors.rs:54`), applied at `:788-804`.
  - JS: `SUCCESSOR_BREAKER_LIMIT = 5` (`085-successor-plan.js:7`), applied at
    `089-successor-project.js:890`.
  - Copy: nav `285-unblocked-notice.js:10,146` and Mac.
  - Vectors: SL17 and PP15.
- **What this morning's history shows** (`__cld` found it; I re-verified):

| Commit | What happened |
| --- | --- |
| `abd4ca6b` 07:59:36 | The SASE session closed, completing `[[sase#^post-blog-prj]]`. Its ~11 dependents (8 in `sase.md`, the rest in `sase_goals.md`, `sase_memory.md` and `sase_remote.md`) went `[?]` → `[ ]` with `[unblocked:: 2026-10-13]`. **No links: the breaker fired.** |
| `59f8ba60` 08:02:55 | You hand-linked `sase_goals#^ref-2026-goals-…` under **JOB**. The line went `[ ]` → `[*]`, **`[fresh:: 2026-10-12]` → `[fresh:: 2026-10-13]`, and `[unblocked::]` was removed.** |
| `b87c4e7f` 08:03:12 | You hand-linked `sase_memory#^ref-memory-built-instruction-…` under **SASE** (the closed session's continuation). |

Three lessons:

- You wanted **2 of ~11**, so neither "all" nor "none" was right.
- **One of the two went to a different session** from the predecessor's slot.
- **Both picks were `#ref` tasks**, so offers must include `#ref` work.

The manual link also shows what a pick should write (§5.1).

### 1.4 Close paths that run the successor pass

| Surface | Gestures | Entry point |
| --- | --- | --- |
| bob-cli capture | `!note:id`; `=x…`, `=x!M`, `=!`; `^/@route:id=x…` | `capture/task_complete.rs`, `capture/pomodoro_close.rs`; batch post-pass in `capture/plan.rs` |
| Obsidian cycler | Ctrl+Enter on a Task Link, task line, embed or Pomodoro line; walk Ctrl+Enter (`completeTaskAtCursor`); Alt+] into Done | One choke point: `finalizeClosedTasks` (`130-plugin-references.js:52`) → `planAndApplySuccessorsNow` (`137`) |
| Bob Mac Capture | Submits the capture forms above | Thin client. Previews with `bob capture --dry-run`, then submits once |

These never link and should never prompt: cancel (recover only), reopen, raw checkbox
clicks, `bob task reconcile` and hooks. "Any supported method" means the managed close
gestures above. Raw checkbox clicks have no managed gesture, and a vault watcher cannot
tell a human close from a sync.

---

## 2. Is this a good idea?

**Yes.** All five reports agree, for these reasons:

- **A link is a sticky commitment, not a notification.** It raises the task to Next, and
  only Alt+N lowers it (`task-lanes-are-sticky`). Auto-linking spends lane capital on
  your behalf. The breaker spends nothing exactly when the most work unblocked.
- **Projects make fan-out normal.** `__cld`'s census found the following:
  - open residents per project: median 2, p90 8, max 222 (`sase.md`);
  - there is no honest automatic answer for "a project just unblocked": linking all of
    it floods Today, and linking none is today's miss;
  - only an explicit choice works.
- **Destinations differ.** One of this morning's two picks went to a different session.
  Auto-linking only knows one heuristic slot.
- **It is rare.** Only tasks carrying `[id::]` can unblock anything: about 6% of open
  tasks per `__cld`, and the `[id::]` gate already makes the other ~94% of closes free.
  The prompt appears only when something is actually offered.

**What it costs.** These come from the reports and are confirmed:

- The zero-keystroke 1:1 hand-off becomes one keystroke (↵).
- A modal appears at the moment of completion, so it must never fire with nothing
  offered and must never double-advance the review walk.
- Two UIs must be built: an Obsidian modal and a Mac in-panel step. The rule, contract
  and vectors stay shared.
- It reverses part of a 4-day-old design and one rejected alternative in a decision
  record. That is legitimate: the breaker evidence in §1.3 is exactly the "reopen if
  breaker notices become routine" condition the 2026-10-09 successor research set.

**What I would not do:**

- **Keep auto-linking with a higher cap.** Auto-linking 11 or 222 tasks is worse than
  none, and it still cannot choose the session.
- **Rely on TICKLER resurfacing alone.** That is what happens today, and it is the miss
  you hit.

---

## 3. Requirement adjustments (called out)

| # | You asked | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | Prompt instead of auto-linking | Recovery stays automatic: status, tag strip, `[unblocked::]`, `#hide` removal on an emptied `^prj`. **Only the link and the Next raise are chosen.** Picking none never undoes the unblock. | Recovery is derived truth that reconcile would write anyway. The review tiers make "none" safe. |
| **A2** | "One or more new panels" | **One picker per gesture**, grouped: Hand-offs / Project ‹note› / Project finished. Never a sequence of panels. | Sequential modals train Esc-mashing. A Pomodoro close or multi-item draft can unblock several projects at once. |
| **A3** | Remove the 5 limit | Delete the breaker in both engines, its copy, SL17 and PP15. **No replacement cap.** Use a filter, collapsed groups and a soft `plan.max_links` meter instead. Keep the unrelated embedded-completion safeguards (25 levels / 250 targets). | Selection is explicit. The breaker was all-or-nothing, and it fired on a real close. |
| **A4** | "All open tasks that belong to that project" | Offer every open resident of the unblocked project's note that is **available after this gesture**: no own open prerequisite, no future date, not `#hide`, not already linked today. Include `#ref` and inbox tasks, and `[ ]` residents as well as `[?]` ones. Show still-blocked residents as **muted, unselectable** rows with their reason. Fold hidden and already-planned residents into one count line. The non-empty project's `^prj` is the **group header, not a choice**. | Linking a Blocked task is forbidden: it would raise that task's prerequisites instead. A `#hide` row would be re-hidden by sync. A project with remaining work is not itself "next". |
| **A5** | (implied) sub-project tasks | **Out of v1.** Descendant projects stay `[?]` and tagged until reconcile (`close_recovers_subprojects = no`; `project_close.rs` PDC5). The picker shows one muted line: "N tasks in sub-projects recover at next reconcile". | They are still Blocked at close time, and offering them would reopen `subprojects-inherit-project-blocking`. Revisit only if you want immediate descendant recovery on close. |
| **A6** | Same for project-empty pull-ins (a/b/c) | Yes. The emptied `^prj` or parent `^prj` becomes an offer. `#hide` is still removed **whether or not it is picked**, as sync would do anyway. An unpicked `^prj` stays Ready. | This removes the last automatic link, and keeps sync and the pull-in predicate aligned. |
| **A7** | "Via any supported method" | Prompt on **managed Done gestures** (§1.4) only, and only when the offer set is non-empty. Cancels, reopen, reconcile, hooks and raw checkbox clicks never prompt. **Also offer when the predecessor was not planned today**, using the implicit destination (the running timed entry, else the first open entry). With no open Pomodoro, show today's notice and no picker. | Explicit choice removes the reason `not_planned_today` existed, because no hand-off slot is needed. This is a deliberate widening (3 of 5 reports). |
| **A8** | (unstated) what a pick writes | A pick = manual-link semantics: Next, a minted ID if missing, **`[fresh:: today]`, and clearing `[unblocked::]` / `[keeps::]`**. This changes §12.4's "freshness never touched" **for picked rows only**. | A pick is a human confirmation. Your own hand-link this morning wrote exactly this (§1.3). |
| **A9** | (unstated) destination | Default to today's §12.3 slot: the predecessor's slot, or the closing continuation. Project residents use the anchor of the task that unblocked their `^prj`. **The contract carries a per-pick destination from day one.** Obsidian gets a per-row override in v1; the Mac gets it later. | One of this morning's two picks went to another session. |
| **A10** | (unstated) defaults | **Nothing pre-checked.** ↵ applies the marked rows, or the highlighted row if none are marked. Esc means none. | One key for the 1:1 case, and no silent re-creation of auto-linking (§4). |
| **A11** | (unstated) CLI and agents | `bob capture` **never prompts and never auto-links.** Without a pick flag, it recovers and reports the offers. | Agents and scripts must not hang, and must not plan your day. |
| **A12** | "Separate solution for the Mac" | **Verified: custom UI, same mechanism.** An in-panel choice step on Return, with picks passed to the one atomic `bob capture`. Not a post-submit panel, and no Swift eligibility logic. | `mac-capture-is-a-thin-client`; details in §5.4. |

---

## 4. Where the reports disagreed, and the resolution

| Question | Positions | Resolution and evidence |
| --- | --- | --- |
| **When does Obsidian ask?** | **After**, as a second queued pass: `__cdx`, `__cld`. **Inside** the current pass, before link writes: `__grk`, `__mus`, `__gem`. | **Inside: plan → ask → apply.** The case for it, from the code: <br>• **The close is already committed.** `finalizeClosedTasks` runs after the Tasks `[x]` write (`160-plugin-completion.js:234-253`). Esc therefore can never mean "cancel the close". <br>• **Apply already guards stale lines.** `applySuccessorNoteEdits` fails any row whose line changed (`current !== edit.before`, `135-plugin-successors.js:~397`). The daily-insertion path has its own "daily note changed" fallback, so a stale plan fails safe. <br>• **Holding the queue is harmless.** `referenceMutationQueue` (`130:44-48`) is held while the modal is open. Every caller of that queue is user-initiated: cycler close, reopen, strike and unstrike gestures, plus `api.recoverBlockedDependents`, which the Task Card's cancel uses. The modal blocks all of those gestures anyway. <br>• **Anchors survive.** They stay valid because retirement still runs after linking, as today. A post-pass would have to re-derive anchors after the predecessor's link was struck or moved. <br>• **No extra freshness write.** With an after-pass, a picked task gets a stray `[unblocked::]` from pass 1 (the WRITE skip only covers *landing* in Next). <br>• **Parity with Rust.** It keeps §12.4's "one planned pass in Obsidian", so both engines treat selection as a planner input. <br>`__cdx`'s caution about holding the queue is noted and judged acceptable. |
| **Mac transport** | Post-submit offer state and a second apply endpoint: `__cdx`. A `>1,3` draft grammar: `__cld`. Checkboxes on the preview and a `--successors` flag: `__grk`, `__mus`, `__gem`. | **Pre-submit, with a flag carrying identity keys.** <br>• **Pre-submit keeps it to one write.** It keeps one atomic `bob capture` and Rust's in-plan anchors (the vacated-slot rule for `!`, and the closing continuations), so there is no "link for an already-Done predecessor" mode. <br>• **Identity keys beat positional `>N`.** Live preview re-plans every 50 ms debounce (`CapturePanelModel.swift:641`), and the vault can change between preview and submit. Opaque keys fail closed; positions silently pick the wrong row. <br>• **The flag name needs care.** `-S` is already `--task-section` on `bob capture` (verified in `bob capture --help`), so `__grk`/`__mus`'s `-S, --successors` collides. <br>• **Adopt `__cld`'s race guard.** It covers a submit that lands before a fresh preview (§5.4). |
| **Default selection** | Pre-check today's auto-set and leave residents off: `__grk`, `__mus`, `__gem`. Nothing pre-checked: `__cdx`, `__cld`. `__grk` also proposes auto-linking a lone pre-selected offer without asking. | **Nothing pre-checked; ↵ acts on the highlighted row when nothing is marked** (nav's existing Depends-on convention: Tab marks, `apply N` footer, `450-picker-keydown.js:134-142`, `400-picker-local-task.js:161-167`). <br>• The 1:1 case still costs one key, and Esc is "none" everywhere. <br>• **Reject the auto-single skip.** It contradicts "start prompting". Keep it only as a possible later opt-in, if every prompt turns out to be ↵. |
| **CLI default** | Keep auto-linking by default: `__grk`, `__mus`. Link none and report offers: `__cdx`, `__cld`, `__gem`. | **Link none.** Keeping auto would leave two behaviors and an *unbounded* automatic mode once the breaker is gone (`__mus` itself flags this). Agents must not plan your day. |
| **Review walk** | Never prompt in the walk: `__gem`. Defer to a toast plus a "Pull in…" command: `__cld`. Prompt, then advance once: `__grk`, `__mus`. Advance, then prompt: `__cdx`. | **Prompt, then advance exactly once after the picker settles.** <br>• **The walk already expects modals.** `continueReviewWalkAfter` yields a macrotask "so a modal submit has closed and focus has returned" (`536-plugin-review-advance.js:~359-361`). Ctrl+Shift+Enter and Task Card answers already open modals mid-walk. <br>• **Most walk closes never prompt.** They are `#gtd #pre/#post` rows without dependents. <br>• A blocker closed during morning review is a planning moment. <br>• The pull-in result composes into the walk's single toast (`successorNoticeTarget: "return"`). <br>`__cld`'s "Pull in unblocked tasks…" rescue command is a good phase-2 addition. |
| **Freshness on picks** | Stamp like a manual link: `__cld`. Keep §12.4 (no stamp): `__cdx`, `__grk`, `__mus`. | **Stamp.** <br>• The vault shows your manual link stamped `[fresh::]` and cleared `[unblocked::]` (§1.3). <br>• The glossary defines freshness as human confirmation, and only *automation* is barred from stamping. <br>• A small, deliberate doc change. |
| **Unplanned predecessor** | Offer with the implicit destination: `__cdx`, `__cld`, `__gem`. Stay quiet: `__grk`, `__mus`. | **Offer** (A7). There is no picker when no open Pomodoro exists. |
| **Resident scope** | Only rows this gesture recovered: `__grk`. Every available resident: the others. | **Every available resident**, evaluated on the final state. <br>• The two scopes coincide in practice: a blocked project's residents are all `[?]`. <br>• Enumerating the note also catches stale `[ ]` residents, which `recover_project_members` skips (`task.status != '?'`). <br>• `__grk`'s concern about the 222-row `sase.md` is real. It is handled by grouping, the filter and no pre-checks, not by trimming. |

---

## 5. Recommended design

### 5.1 Shared rule (one definition, two engines)

```text
C, GATE, CANDIDATES      : unchanged (§12.2)
Ladder for dependent D   : unchanged through the still-blocked, ^prj, #hide and
                           already_planned steps
  not_planned_today      → no longer a reason: offer with the implicit destination
                           (no open Pomodoro → recover, not_linked: no_destination)
  kill switch off        → recover; not_linked: disabled; no offers
  otherwise              → OFFER{group: hand_off, destination: anchor ?? implicit}

PROJECT OFFERS (replaces PROJECT RECOVERY when a ^prj R recovers and N has no own or
inherited reason left):
  every open resident T of N ([?] or [ ]):
    own open prereq / future date → still_blocked (muted row, unselectable)
    #hide                         → recover only (count line)
    live-linked today             → recover to derived rank (count line)
    otherwise                     → recover AND OFFER{group: project, project: N,
                                     destination: anchor(preds(R)) ?? implicit}
  R itself (N non-empty)          → recover; group header, not an offer
  descendant projects             → untouched (PDC5); muted count line

PULL-INS (§12.10)        : steps 1–4 unchanged (#hide removed). The link step becomes
                           OFFER{group: project_finished}
BREAKER                  : deleted
DEDUP                    : one row per task identity; causes merged; a later item in
                           the same draft that links, completes, re-blocks or explicitly
                           drops a task (=x~K) removes its offer; a later item that adds
                           project work removes a project_finished offer

SELECTION S              : Rust: --pull-in; JS: the picker result
  each picked offer      → ' '/'?' → '*' ('*', '/' unchanged); mint ^id if missing;
                           [fresh:: today], clear [unblocked::] and [keeps::]; insert
                           "- [[link]]" at its destination (§12.3 slot/closing rules,
                           or an override created like @route:id#name)
  each unpicked offer    → recovered rank as today, including the [unblocked::] WRITE
                           rule; not_linked: not_selected
```

**Invariants:**

- No recursion: picking D never completes D.
- No minting for unpicked rows. Most residents have no block ID.
- A picked row that became Blocked or was linked meanwhile is refused per row. It is
  never satisfied by linking that task's prerequisites instead.

### 5.2 Contract (additive)

**JSON.** `unblocked[]` rows keep their meaning for committed changes, and offered rows
gain an `offer` object:

```json
"offer": {
  "key": "sase_foo.md@3f9a…",
  "n": 2,
  "group": "project",
  "project": "sase_foo.md",
  "destination": {"day_file": "2026/20261013.md", "entry_name": "BOB", "fallback": false},
  "selected": false,
  "block_id_needed": true
}
```

- **`key`.** For rows that have a block ID, the key is `note_path#^block_id`. Otherwise
  it is the note path plus a digest of the cleaned description. Duplicate text in one
  note is ambiguous: refuse and re-plan rather than guess.
- **Capability and choice state.** A top-level `pull_in: {offers, choice, supported:
  true}` advertises the capability, so the Mac only sends the flag to a bob that
  understands it.
- **`not_linked` values.**
  - New: `not_selected`; `no_destination` (an unplanned close with no open Pomodoro).
  - `breaker` is never emitted again, but the Mac and nav keep its copy for older builds.
- **Dry-run.** With the same flags, dry-run JSON still equals real-run JSON.
- **Versioning.** `bob capture` JSON has no `schema_version` envelope (`__cdx`). Grow it
  additively and gate on `pull_in.supported`.

**CLI.** The names are illustrative: `-p, --pull-in <all|none|N,…|KEY,…>` on
`bob capture`.

- **Usage.** It is sorted with the other options and has a short alias (`cli_rules.md`).
  `-p` is free; `-S` is not.
- **Numbers.** Positional `N` is accepted for terminal convenience and validated against
  the same plan.
- **Errors.** An unknown or stale key is a teaching error, never a silent skip.
- **No flag.** Without the flag, bob recovers, reports numbered offers and links none.
- **Mac guard.** A hidden internal argument, `--require-pull-in-choice`, makes bob write
  nothing and return `pull_in_choice_required` with the offers whenever offers exist and
  no `--pull-in` was given.

**Config.** `plan.link_unblocked` keeps its boolean spelling:

- `true` (default) now means **offer**;
- `false` means recover only: no offers and no links;
- there is no `auto` mode. If one is ever wanted, the boolean becomes an enum at that
  point.

### 5.3 Obsidian

**Where it hooks in.** In `planAndApplySuccessorsNow` (`137`), compute the plan, then
`await` the picker when `offers.length > 0`. Re-run the pure planner with the selection,
then apply with the existing per-line checks, then retire and present, exactly as today.

**The picker.**

- Nav owns the modal and exposes it as an additive API member next to `api.notice` (for
  example `api.successors.pick(model) → Promise<{picks:[{key, destination?}]} | null>`).
- The cycler owns planning and writes.
- Without nav, show today's plain notice, listing the offers as "not pulled in". Never
  auto-link.

```text
┌ 🔓 Pull in · 4 unblocked ─────────────────────────── ✓ bar boom bam ┐
│ filter…                                                             │
│ HAND-OFFS                                                           │
│ ▸ 1  Re-launch failed agents on apollo!         → BOB    ↗ sase     │
│ PROJECT  foo bar baz                                     ↗ sase_foo │
│   2  Some subtask                               → BOB   needs ^id   │
│   3  Some other subtask                         → BOB   needs ^id   │
│   🔒 Draft the launch post · waits on 1 more                        │
│   · 2 sub-project tasks recover at next reconcile                   │
│ ─────────────────────────────────────────────────────────────────── │
│ ↑↓ move · ⇥ mark · ⌃A mark group · ⌃⇧↵ session · ↵ pull in 1 · esc none │
│ plan 10/12 → 11/12                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

**Keys:**

- Tab marks a row. ↵ applies the marked rows, or the highlighted row if none are marked;
  the footer always states the count.
- Esc, or a click outside, means none.
- ⌃⇧↵ chains block-id-prompt's existing `PomodoroLinkPickerModal` to retarget the marked
  or highlighted rows.

**Guard against a double press.** Ignore Enter carrying modifiers, and ignore repeats or
presses within ~350 ms of opening. The second half of a double Ctrl+Enter must not apply
the picker.

**Scale.**

- With more than ~12 rows, project groups start collapsed (`+N more`), and typing a
  filter expands them.
- The plan meter warns but never refuses.

**Walk landings.**

- The picker opens, then the walk advances once after it settles (including Esc). The
  result composes into the single walk toast.
- Implementation must test the nav-owned `completeTaskAtCursor` path separately, and
  confirm that the modal does not stale the walk origin (`reviewGestureSeq` /
  `reviewLandingEpoch`).

**Batch gestures.** A Pomodoro-line close or a counted Alt+] is one gesture, so it gets
one picker over the union of its offers.

### 5.4 Bob Mac Capture

These facts make a custom UI necessary:

- `completeSubmit` hides the panel on success (`CapturePanelModel.swift:5213-5275`).
- `CapturePickerState` is single-select (`selectedRowID`).
- Notifications cannot host a list.
- Nothing in the app does multi-select today.

**What to build.** All of it stays inside the thin-client rule:

1. **Preview.** The `!` and `=x` cards already show Unblocked rows. Number the offer
   rows and add a hint: `↩ choose what to pull in`.
2. **Choice step.** On Return, if the latest preview has offers, open an in-panel
   multi-select step that gates submit like `taskIDPrompt` / `pomodoroNamePrompt`
   (`inlinePromptVisible`, `:677`, `:1408`).
   - Keys: ↑↓ move, Space toggles, ⌘A marks all, ↩ confirms (marked rows, else the
     highlighted one), ⇧↩ closes and pulls in none.
   - **Esc returns to the draft with nothing written.** This deliberately differs from
     Obsidian, because on the Mac the close has not happened yet.
3. **Submit.** Append `--pull-in <keys|none>` before `--` in `BobProcessClient.capture`
   (`:283-303`), only when the dry-run advertised `pull_in.supported`.
4. **Race guard.** When submitting without a fresh preview, send
   `--require-pull-in-choice`. A `pull_in_choice_required` reply opens the choice step
   from the returned offers. This adds no extra spawn when nothing is offered.
5. **Fixes in passing.**
   - Decode `trigger`, `hide_removed` and `offer`.
   - Add copy for `project_member`, which is missing today and falls through to the raw
     string in `CaptureCore/CaptureSuccessorPresentation.swift:218-232`.
   - Add copy for `not_selected` ("not pulled in").
   - The notification line reports what was pulled in.

**Mixed versions:**

- An old Mac with a new bob gets no links (offers render as recovered rows). That is
  consistent with the request.
- A new Mac with an old bob sees no `pull_in.supported`, sends no flag and shows a
  capability note.

### 5.5 CLI

There is no TTY prompt in v1:

- Agents and pipes must never block.
- Obsidian and the Mac cover interactive use.
- A third interactive implementation is where parity breaks.

Human output prints numbered offer rows plus a hint:

```text
✓ completed [*] → [x] bar boom bam  sase.md ^bar
  offer 1 [?] → [ ] Some subtask        sase_foo.md · project foo bar baz → BOB · needs ^id
  offer 2 [?] → [ ] Some other subtask  sase_foo.md · project foo bar baz → BOB · needs ^id
  pull in: rerun as a dry run, then -p 1,2 · -p all
```

From a terminal, the flow is `bob capture -d '!sase:bar'`, then
`bob capture -p 1 '!sase:bar'`. A TTY picker can come later and would also be
pre-commit.

### 5.6 Undo

- **One pick:** Alt+N on its link, unchanged.
- **The whole gesture (Obsidian):** the same-day reopen receipt takes back the picked
  links. It also restores the pre-pass lines it owns: status, `#hide` on a pulled-in
  `^prj`, and now the freshness fields of picked rows. One pass means one receipt.
- **Rust:** no reopen take-back, as today.

### 5.7 Docs, vectors and memory

- **`docs/task-dependencies.md` §12.** Rename it "Successor offers". Rewrite:
  - §12.2: offers, project offers and the breaker deletion;
  - §12.4: freshness for picks;
  - §12.5: the `offer` / `pull_in` objects and the new `not_linked` values;
  - §12.6: copy;
  - §12.8: the kill switch;
  - §12.10: steps 5–9;
  - PDC2.

  While editing, fix the drift `__cld` found:
  - §12.10's claim that the Mac needs no change;
  - the `project_member` gap in `docs/capture.md`'s `not_linked` list;
  - `"not_linked": null` in the docs vs. serde omitting the key.
- **Vectors.** Replace SL17, PP15 and PDC2. Add SO vectors for:
  - the `^bar` → `sase_foo` case;
  - an 11-way fan-out;
  - pick all / none / subset / stale key;
  - a resident that is also a direct dependent (one row);
  - `=x~K` drop wins;
  - later-item invalidation of an offer;
  - a destination override;
  - an unplanned predecessor, with and without an open Pomodoro;
  - walk advance-once;
  - freshness bytes of a pick.

  Run them against both engines.
- **Decision record.** When implemented, add (via `/sase_memory_write`) a record:
  *"Unblocked tasks are offered, never auto-linked."*
  - It partly supersedes `unblocked-tasks-resurface-as-ticklers`: the rejected
    "successor-linking residents" becomes an explicit offer.
  - It satisfies the "re-linking on unblock" reopen condition of
    `projects-block-from-prj-line`.
  - Do not edit those records in place.
- **Glossary.** Consider a "Successor Offer" entry.

---

## 6. Alternatives considered

| Approach | Verdict |
| --- | --- |
| Keep auto-linking and raise or remove the breaker | **Reject.** It is unbounded, can't choose the session, and doesn't fix `sase_foo`. |
| Keep auto for direct dependents; prompt only for project expansion | **Reject.** Two behaviors; you asked to stop auto-adding. |
| Auto-link a lone pre-selected offer; ask otherwise (`__grk` A3) | **Defer** as a possible opt-in, if the picker proves to be "↵ every time". |
| Post-commit chooser plus a second write (`__cdx` everywhere, `__cld` for Obsidian) | **Reject.** It needs anchor re-derivation after retirement, leaves a stray `[unblocked::]` on picks, and breaks §12.4's single write set. Rust would need a new "link for an already-Done predecessor" mode. |
| `>1,3` draft grammar as the Mac/CLI transport (`__cld`) | **Defer.** Positional choices are fragile against live re-planning, and the grammar grows. Identity keys on a flag are safer. A typed grammar could later sugar the flag for the terminal. |
| Checkboxes directly on the Mac preview card (`__grk`, `__mus`, `__gem`) | **Reject as primary.** Focus stays in the text field, so toggling needs extra chords. Return is ambiguous about whether the defaults were reviewed. The choice step makes the decision explicit and keyboard-native. |
| Never prompt in the review walk (`__gem`) | **Reject.** It hides the feature on a common closing gesture. The walk already supports modal answers. |
| A persistent "Unblocked today" tray instead of a modal | **Reject as primary.** It loses the hand-off moment, and the review tiers already guarantee next-day review. |
| Swift computes offers, or the plugin shells out to `bob` | **Reject.** It breaks the thin client, and spawning ignores unsaved buffers. |
| Immediate descendant recovery so sub-project tasks can be offered | **Defer.** It reopens `subprojects-inherit-project-blocking` and turns each close into a tree write. |
| Offer on cancel | **Defer.** "Won't do" rarely means "do the follow-up now". |

---

## 7. Implementation plan (one epic)

| Phase | Repo | Scope | Depends on |
| --- | --- | --- | --- |
| **P1 contract** | bob-cli | §12 rewrite and vectors; `docs/capture.md` (flag, JSON, `pull_in_choice_required`); `docs/plan.md` (kill switch meaning); `docs/freshness.md` (pick stamps); decision record and glossary drafts | — |
| **P2 Rust** | bob-cli | Offer verdicts and project offers (`successors.rs`, `project_close.rs`, `project_pull_in.rs`); delete `MAX_SUCCESSORS_PER_GESTURE`; selection input; pick writes including freshness; batch net-offer pass in `capture/plan.rs`; `--pull-in` and the hidden guard; human/JSON output; tests | P1 |
| **P3 plugins** | bob-plugins | Cycler: plan → await picker → apply; delete `SUCCESSOR_BREAKER_LIMIT`; pick freshness; receipt. Nav: picker modal API, keys, walk integration, notice copy (drop the breaker variant for new output). Then `bob plugins sync` | P1 (parallel with P2) |
| **P4 Mac** | bob-mac-capture | Decode `offer` / `pull_in` / `trigger`; numbered rows; choice step; `--pull-in` on submit; race guard; copy fixes. macOS CI | P2 JSON frozen |
| **P5 polish** | all | "Pull in unblocked tasks…" rescue command (held offers, revalidated); Mac per-row destination; optional TTY picker | P3, P4 |

Ship P2 and P3 together. A new plugin paired with an old bob would prompt in Obsidian
while capture still auto-links.

**Acceptance highlights:**

- **Fan-out:** 1, 6 or 20 offers are all accessible with zero pre-checked, and any
  subset links exactly that subset.
- **Esc or Skip:** recovery stands, with no minted IDs and no successor-only
  placeholders.
- **`^bar` → `sase_foo`:** both subtasks are offered under the project group and `^prj`
  is the header. Picking one mints its ID, sets `[*]`, stamps freshness and links it
  under BOB.
- **Project-empty / parent pull-in:** `#hide` comes off unpicked; the link happens only
  if picked.
- **Review walk:** a walk-landing close advances once, including the PRE/POST boundary
  rule. A double Ctrl+Enter does not apply the picker.
- **Concurrency:** a stale line or daily note fails that row loudly; nothing is written
  to the wrong place.
- **Callers that must not prompt:** JSON, pipes, agents and old clients never prompt and
  never auto-link.

---

## 8. Open questions for Bryan (with my defaults)

1. **Freshness on picks (A8).** Default: stamp, as your manual link did. The alternative
   keeps §12.4, so picks surface in tomorrow's NEXT review unstamped.
2. **Pre-checks (A10).** Default: none, with ↵ acting on the highlighted row. The
   alternative pre-checks direct hand-offs and pull-ins, so ↵ equals today's
   auto-linking.
3. **Unplanned closes (A7).** Default: offer into the running or next open Pomodoro. The
   alternative stays quiet, as today.
4. **Sub-project tasks (A5).** Default: out of v1, shown as a count. Say if you want
   immediate descendant recovery on close; that is a separate decision change.
5. **Alt+] into Done.** Default: prompts like any Done gesture. If a modal mid-cycling
   proves jarring, exempt it rather than adding per-gesture config (`__mus`).

---

## 9. Recommended solution

Replace automatic successor linking with **Successor Offers**:

- **What happens on every close.** Every managed Done gesture still performs all
  recovery and un-hiding immediately.
- **What gets offered.** One grouped, filterable picker with nothing pre-checked:
  - direct dependents the close unblocked;
  - every available resident of any project whose `^prj` it unblocked;
  - the emptied-project and parent-project `^prj` pull-ins.
- **What a pick does.** Only picked tasks are linked: Next, a minted ID if missing, and
  a freshness stamp, like your manual link. They go to the predecessor's slot by
  default, with a per-row override.
- **The breaker** is deleted in both engines.
- **How selection is wired.** Selection is an input to each engine's existing single
  write pass:
  - **Obsidian** awaits the modal between plan and apply. The review walk advances once
    after the modal settles.
  - **Bob Mac Capture** adds an in-panel choice step on Return. It passes identity-keyed
  `--pull-in` picks to the one atomic `bob capture`, with a bob-side guard for submits
  that beat the preview.
  - **The CLI** never prompts and never auto-links.
- **What stays out of v1.** Sub-project descendants stay out until reconcile, and
  cancels never prompt.

This gives you the control you asked for, fixes the `sase_foo` expectation explicitly,
and turns this morning's breaker dead-end (2 hand-links out of ~11) into one picker
interaction. The Mac stays a thin client, and the rule is still specified once and
implemented twice.

---

### Provenance

- **Researcher reports:** `successor_pull_in_offers__{cdx,cld,grk,mus,gem}.md` in this
  directory.
- **Lead verification (code):**
  - bob-cli: `successors.rs:50-54,780-804`, `project_close.rs:215-292`,
    `docs/task-dependencies.md` §§12.4/12.8/12.9, and `bob capture --help` (the `-S`
    collision).
  - bob-plugins: `130-plugin-references.js:44-125`, `137-plugin-successor-project.js`
    (plan → apply seam), `135-plugin-successors.js:354-420`,
    `160-plugin-completion.js:234-260,355-385`, nav `536-plugin-review-advance.js:337-361`,
    `450-picker-keydown.js:134-142`, `400-picker-local-task.js:161-167`,
    `085-successor-plan.js:7`, `089-successor-project.js:890`,
    `285-unblocked-notice.js:10,146`.
  - bob-mac-capture: `CapturePanelModel.swift:641,677,1407-1450,5213-5275`,
    `BobProcessClient.swift:283-303`,
    `CaptureCore/CaptureSuccessorPresentation.swift:218-232`.
- **Lead verification (vault):** `~/bob` commits `abd4ca6b`, `59f8ba60`, `b87c4e7f`,
  `39b35d80`, `d6e117b8`, `1cb0f4ba`, and the current `sase_foo.md`.
- **Memory (audited):** decisions `unblocked-tasks-resurface-as-ticklers`,
  `task-lanes-are-sticky`, `answering-advances-the-walk`, `mac-capture-is-a-thin-client`,
  `subprojects-inherit-project-blocking`, `projects-block-from-prj-line`; glossary
  `freshness`, `task link`; `cli_rules.md`.

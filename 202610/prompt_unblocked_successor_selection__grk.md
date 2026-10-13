# Prompt which unblocked tasks to pull in as successor links

*Researcher: grk · 2026-10-13 · independent swarm report*

**Verdict.** Yes — stop auto-linking, and ask. Keep the existing successor
*planner* (who is eligible, where the bullet goes, how status and minting
work). Change only the *commit* step: recover always, link only what Bryan
ticks. That is the design the 2026-10-09 Successor Links research deferred
as "right for a bushy graph"; offering project residents now makes the graph
bushy on purpose.

Do **not** auto-link every open resident of an unblocked project. Put those
rows on a picker, default **off**. Keep the 1:1 direct-dependent hand-off
fast by skipping the picker when there is exactly one pre-selected offer
and nothing extra to consider.

---

## 1. Recommendation in one page

When a Bob close gesture fully unblocks other work, Bob should still
recover that work in the same pass it does today. It should **not** insert
Task Links until Bryan names which recovered rows become successors.

**Do this:**

1. Split the §12 successor pass into **offers** vs **links**. Recovery,
   `[unblocked::]`, `#prj_is_blocked` stripping, and `#hide` removal on an
   emptied `^prj` stay automatic. Linking becomes an explicit selection.
2. Offer three classes in one grouped picker:
   - **Direct** dependents this close fully unblocked (today's SUCCESSOR
     set, including rows the breaker currently drops).
   - **Project members** recovered because this close unblocked their
     `^prj` (today's `not_linked: project_member` rows).
   - **Project-empty pull-ins** — the emptied project's `^prj`, and the
     parent `^prj` from §12.10 trigger (c).
3. One picker per gesture, grouped by class and project note. Not a stack
   of sequential panels.
4. Drop the 5-successor breaker. Show the soft `plan.max_links` meter.
   Linking 6+ is fine when Bryan picked them.
5. **Obsidian:** a blocking `bob-key-card` successor picker in the
   Unblocked-notice family, awaited inside `finalizeClosedTasks` after
   recovery writes and before link writes. Esc = link none, then the walk
   may advance.
6. **Bob Mac Capture:** checkboxes on the existing Unblocked preview
   section, submitted as `bob capture --successors … -- <draft>`. No
   second panel after Return. Eligibility stays in bob
   (`decisions:mac-capture-is-a-thin-client`).
7. **CLI / agents:** no TTY prompt. Default `--successors auto` keeps
   today's direct + pull-in auto-link so scripts do not change. Interactive
   clients always send an explicit id list.

**Do not do this:** auto-link residents of `sase.md`-scale notes; prompt
when the close has no ledger anchor; walk the sub-project tree on close
(PDC6 / `close_recovers_subprojects = no`); invent a `bob capture`
subcommand; let Swift or the plugin decide eligibility.

---

## 2. Is this a good idea?

**Yes, with the skip-for-single-direct adjustment in §5 A3.** The request
is a correction of a cost the 2026-10-09 research already named and then
accepted:

> Linking is a sticky commitment, not a notification. A wrong successor
> costs a lane, not a bullet.

That research chose auto-link anyway because Bryan's live graph was
sparse (20 open dependents, max fan-out 4, 19 of 20 with one
prerequisite) and because a toast-only "suggest" path "defeats the
request." It explicitly **deferred** "auto-link only when exactly one
successor, else ask" until breaker or `+N` notices became routine.

Two things have changed:

1. Bryan is now asking to pick. The deferred alternative is the request.
2. He also wants **project residents** on the same surface. That is a new
   candidate class the original design rejected. `decisions:unblocked-tasks-resurface-as-ticklers`
   records the rejection in so many words: "Successor-linking residents.
   Residents recover recover-only." Offering them without a picker would
   dump a project's Ready pool onto Today. Offering them *with* a picker,
   default off, is the only safe way to honor the `sase_foo` expectation.

The idea is still a flow continuation, not a second Today engine. The
close is the explicit gesture. The picker is the "which of these is
actually next" question the dependency edge cannot answer — especially
once the edge is "this project is unblocked," which is not the same as
"do every resident right after this."

I would not keep auto-link for residents. I would not replace successor
links with "just recover and let the TICKLER walk surface them" either:
that is what already happens, and it is exactly the miss Bryan hit.

### Where the request as written goes wrong

1. **"One or more new panels" as a stack.** Two unblocked projects in one
   gesture should not open two modals. One grouped list is faster and
   matches the existing one-notice-per-gesture rule (§12.6).
2. **"All open tasks that belong to that project."** Taken literally this
   includes work that was already Ready, hidden `#hide` rows, `#ref`
   tasks, and (for a parent like `sase.md`) hundreds of Blocked residents
   that this close did not recover. The honest set is **rows this gesture
   already puts in `unblocked[]` as recovered or pull-in**, plus any
   still-blocked siblings shown muted and untoggleable.
3. **Always prompt, even for a single direct dependent.** Ctrl+Enter is a
   walk answer (`decisions:answering-advances-the-walk`). A modal on every
   1:1 hand-off taxes the common case the original feature was built for.
   Skip the picker when the only offer is one pre-selected direct
   successor. Prompt as soon as a project member, a pull-in, a second
   direct, or a deselectable extra appears.
4. **A separate Mac panel after submit.** That fights the thin-client
   contract: one `bob capture`, panel hides on success, preview is the
   truth. Selection belongs *in* the existing Unblocked section of the
   dry-run card.
5. **Removing the breaker without a budget surface.** The breaker existed
   because auto-link had no ranking. Once Bryan picks, the breaker is
   wrong — but `plan.max_links` (default 10) is still the ledger's soft
   cap. Show it. Do not refuse the write.

---

## 3. What exists today

Verified against bob-cli `docs/task-dependencies.md` §12–§13.16, the
Rust planner (`src/native/task_complete/{recovery,project_close,project_pull_in}.rs`),
the cycler mirror (`task-status-cycler/src/085-successor-plan.js` and
`088`/`089`/`135`/`136`/`137`), nav's Unblocked card
(`bob-navigation-hotkeys/src/285-unblocked-notice.js`), and Bob Mac
Capture's `SuccessorRows` / Unblocked preview.

### Close paths that already run the successor pass

| Gesture | Engine | Recovers? | Auto-links? |
| --- | --- | --- | --- |
| Ctrl+Enter on a Task Link, task line, embed, or Pomodoro line | cycler `finalizeClosedTasks` | yes | yes, §12 rule |
| Alt+] Done (and Tasks Done/Cancelled via the cycler API) | same pass | yes | Done yes; Cancel recovers only |
| `bob capture '!note:id'` | Rust `task_complete` | yes | yes |
| `=x!M` / `=!` / embed close | Rust `pomodoro_close` | yes | yes |
| Bob Mac Capture submitting those drafts | thin client of the rows above | preview of the write | auto, then one 🔓 notification |
| Raw Tasks checkbox, hooks, reopen | — | hooks / reopen take-back | never (SL21) |

Cancel never links today (`136-plugin-successor-receipt.js`). Keep that.

### The rule, compressed

```text
CANDIDATES = open dependents of C
then still_blocked (own deps, future scheduled, still-blocked project)
then recover-only: ^prj (unless §12.10 pull-in), #hide,
                   already planned, not planned today, kill switch
then SUCCESSOR, unless more than 5 → all breaker, link none

PROJECT RECOVERY (PDC2): unblocked ^prj recovers as project_task;
residents recover as project_member — never linked, outside the breaker.

PULL-IN (§12.10): emptied project's ^prj (triggers a/b) or parent ^prj
(trigger c) links as Next, never counts toward the breaker.
```

`plan.link_unblocked: false` already kills linking and minting only.
Recovery still runs. That kill switch stays.

### Feedback today

- **Obsidian:** a 6–10 s `bob-nh-notice is-unblock` toast. Rows are
  clickable to *open* the task, not to link it. Walk landings fold the
  copy into the walk toast and **show no card**.
- **Mac:** Unblocked section on the `!` card and the `=x` close card,
  rendered from dry-run JSON. Checkboxes do not exist. Submit is
  `bob capture --format json -- <draft>` with no successor flag
  (`BobProcessClient.capture`).
- **CLI:** word-led `linked` / `unblocked` / `still blocked` / `surfaced`
  rows.

There is **no multi-select picker** in bob-plugins. Task Link, Pomodoro,
Depends-on, inbox-route, and demotion pickers are all single-select.
The closest decision surfaces are the freshness decay key-card
(`bob-decay-card-modal`, keys 1–4 / Esc) and the lane-release summary
modal. The successor picker should join that family, not the fuzzy
single-pick family.

### The 5-cap

`SUCCESSOR_BREAKER_LIMIT = 5` in the cycler; SL17 / PP15 in the docs and
Rust tests. More than 5 **direct** successors → link none, report
`not_linked: breaker`. Pull-ins and `project_member` recoveries sit
outside it. The original census said live fan-out never exceeded 4, so
the breaker was insurance, not a ranking. Once selection is explicit it
has no job.

---

## 4. The `^bar` / `sase_foo` miss is by design

Bryan closed `^bar` in `~/bob/sase.md` and expected the ordinary tasks in
`~/bob/sase_foo.md` to land as successors. They did not. Current vault
state after that close:

```text
sase.md
  - [x] #task bar boom bam  [id:: sase__bar] ^bar

sase_foo.md  (type project, parent: [[sase]])
  - [ ] #task #prj foo bar baz #hide [id:: sase_foo__prj]
        [dependsOn:: sase__bar] ^prj
      - ⛓️ **DEPENDS ON:** [[sase#^bar]]
  - [ ] #task Some subtask
  - [ ] #task Some other subtask
```

What §12 actually does on that close:

1. `sase_foo`'s `^prj` is a direct dependent of `sase__bar`. The project
   still has two open unhidden residents, so EMPTY(N) is false and
   **pull-in does not fire**. The `^prj` recovers as
   `not_linked: project_task` (SL11 / PDC2). `#hide` stays (only pull-in
   removes it).
2. "Some subtask" and "Some other subtask" have **no** `[dependsOn::]`
   and **no** `[id::]`. They were blocked only through project
   inheritance. PDC2 recovers them as `project_member`, strips
   `#prj_is_blocked`, writes `[unblocked::]` when the freshness WRITE
   rule allows, and **never links them**. They sit outside the breaker
   on purpose, so a fat project cannot trip SL17.
3. They then surface on tomorrow's TICKLER walk
   (`decisions:unblocked-tasks-resurface-as-ticklers`) — the designed
   substitute for successor-linking residents.

So this is not a planner bug. The original feature treated "the project
is unblocked" as a *review* event, not a *Today* event. Bryan's new
request is to offer those recovered residents as optional successors.
That is a contract change to PDC2 and to the tickler decision's rejected
alternative, not a fix.

If the close had emptied `sase_foo` (no remaining unhidden residents),
§12.10 trigger (b) would already auto-link `^prj` as Next. That is the
other half of the request: those automatic pull-ins should go through
the same picker.

PDC6 still applies: a close that unblocks parent `sase` does **not**
immediately recover `sase_foo`'s residents. Tags wait for reconcile.
The picker must only offer rows this gesture recovered in the same
write. Expanding close into a sub-project tree walk was rejected in
`decisions:subprojects-inherit-project-blocking`
(`close_recovers_subprojects = no`).

---

## 5. Requirement adjustments

Called out explicitly. Each row is a deliberate change to, or
clarification of, the request.

| # | The request says | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | Prompt which unblocked tasks to pull in, via any supported close | Recover always; prompt only for **linking**, and only when the close has a ledger **anchor** (a live Task Link under today's open Pomodoros, or under the entry being closed). Unanchored closes recover and stay quiet on linking. | A successor still needs a slot. Asking "which Pomodoro?" on an unplanned close is a second feature. |
| **A2** | Include all open tasks of an unblocked project | Include residents **this gesture recovered** (`project_member` / pull-in / unblocked `^prj`), grouped under that note. Exclude already-Ready work this close did not touch, `#hide` residents, still-blocked own-dep rows (muted), and descendant projects (PDC6). | Literal "all open tasks" on `sase.md` is hundreds of rows, most of them not what this close freed. |
| **A3** | Always prompt | **Skip the picker** when there is exactly one pre-selected offer and no other linkable offer. Auto-link that one, same as today. Prompt otherwise. | Protects the 1:1 hand-off and the review-walk Ctrl+Enter. Reopen if Bryan still finds the skip surprising. |
| **A4** | One or more new panels | **One** picker per gesture, sections Direct / Project \<note\> / Parent pull-in. | Sequential modals are slower than a grouped list; the current notice is already one card. |
| **A5** | Custom / separate Mac solution | Custom **rendering** in the existing Unblocked preview (checkboxes). Not a post-submit panel, not a Swift eligibility engine. | Thin client + "preview is the truth" + one capture call. |
| **A6** | Remove the 5-successor limit | Remove the breaker. Keep the soft `plan.max_links` meter on the picker. Do not refuse over-budget writes. | Ranking is Bryan. Caps elsewhere are advisory. |
| **A7** | Same picker for last-task / last-subproject pull-ins | Yes. A pull-in `^prj` is a pre-selected offer in the same picker (or auto-linked under A3 when it is the only offer). `#hide` still comes off before linking, same bytes as PP22. | Stops the last remaining auto-link that can surprise. Empty projects have no residents, so the extra section is usually one row. |
| **A8** | (unstated) default selection | Direct successors and empty-project / parent pull-ins **on**. Project members **off**. Non-empty `^prj` (`project_task`) **off**. | Direct and empty-`^prj` are today's auto-link set. Residents are the new, dangerous class. Linking a still-busy `^prj` was rejected for a reason. |
| **A9** | (unstated) CLI | No TTY prompt. `bob capture --successors auto\|none\|<id>,…` (short `-S`). Default `auto` = today's direct + pull-in auto-link, still no residents. Interactive clients always pass an explicit list. | `cli_rules.md`: never add a subcommand under `bob capture`; flags before `--` are fine. Agents must not hang. |
| **A10** | (unstated) walk | Await the picker **before** walk-advance. Esc = no links, then advance. Compose nothing into the walk toast until the picker settles. | Walk landings currently suppress the Unblocked card. A picker that never appears on `]s` would hide the feature on the gesture that closes blockers most often. Decay-card already blocks a walk answer. |

---

## 6. UX

### 6.1 Obsidian — one successor picker card

Reuse the Unblocked notice visual language (`bob-nh-notice is-unblock` /
`bob-key-card`), but make it a **Modal** that returns a selection, in
the decay-card shape:

```text
┌──────────────────────────────────────────────────────────────────┐
│ 🔓  Pull in next          2 of 4 → FIX        ✓ bar boom bam     │
│                                                                  │
│ Direct                                                           │
│  ☑  Re-launch failed agents                         [ Next ]     │
│                                                                  │
│ Project sase_foo                                                 │
│  ☐  Some subtask                                    [ Ready ]    │
│  ☐  Some other subtask                              [ Ready ]    │
│  ☐  foo bar baz  · project task                     [ Ready ]    │
│                                                                  │
│ 🔒  Start adding badges · waits until Oct 13                     │
│ ──────────────────────────────────────────────────────────────── │
│  (plan 3/3 · 9/10)  Space toggles · Enter links · Esc none       │
└──────────────────────────────────────────────────────────────────┘
```

Keys (match decay-card density, no mouse required):

| Key | Action |
| --- | --- |
| `j` / `k` / arrows | move the highlight |
| Space | toggle the highlight |
| `a` | toggle all **direct** rows |
| `p` | toggle all rows in the current project section |
| Enter | link the checked set (empty set = none) |
| Esc | link none; close still stands |
| click a row | toggle |
| click the title | open that note (optional, same as today's card) |

Timing relative to writes:

1. The predecessor is already `[x]` (Tasks / cycler write, today's
   order).
2. Run today's planner with linking forced off. Apply **recovery**
   edits now (status, `[unblocked::]`, tag strip, pull-in `#hide`
   removal so the row is visible in the picker).
3. If A3 says skip, apply the one link and show the existing toast.
4. Otherwise await the picker. Then apply only the selected link
   inserts + Next raises + block-id mints.
5. Then walk-advance, if this close was a walk answer.

Two write sets are the cost of a prompt. Close is never rolled back if
linking fails (already true). If the daily note changes while the picker
is open, fail the link writes with today's `couldn't link` copy and
leave recoveries in place.

Do not extend the 6–10 s toast into a picker. It cannot take keystrokes
on walk landings, and it disappears. The "suggest only" alternative was
rejected in 2026-10-09 for that reason; a real modal is what makes
suggest viable.

### 6.2 Bob Mac Capture — verify, then stay in-panel

**A custom Mac UI is required. A separate post-submit panel is not.**

Facts:

- Mac never parses grammar or writes the vault
  (`decisions:mac-capture-is-a-thin-client`).
- Submit is one `bob capture` of the draft; the panel hides on success
  (`CapturePanelModel.submit` / `completeSubmit`).
- Dry-run JSON currently **equals** real-run JSON except `dry_run`
  (`docs/task-dependencies.md` §12.5). The Unblocked section is already
  the preview of what will be written.
- The app already has in-panel pickers (stash, `:` / `!` task picker)
  and inline prompts (`taskIDPrompt`, `pomodoroNamePrompt`) that block
  submit via `inlinePromptVisible`. Checkboxes on Unblocked are smaller
  than those.
- Live preview re-spawns bob on a debounce. Selection state must be
  **client-side**, keyed by `note_path + block_id` (or line for
  unminted rows), merged onto each fresh offer list so a refresh does
  not wipe toggles.

What to build:

1. bob dry-run returns every offer with `offer`, `proposed` (A8), and
   an `offer_link` placement even when `link` is null.
2. The Unblocked section renders a checkbox per linkable row. Space
   toggles the highlighted row; click toggles. Unchecking a
   `proposed` direct successor is how Bryan opts out of a 1:1 hand-off
   on Mac (there is no A3 skip on Mac: the preview *is* the prompt, and
   Return is the confirm).
3. Submit adds `--successors id,id` (or `--successors none`) before
   `--`. Old bob without the flag: treat as `unsupportedOption` and
   fall back to submitting without it only if there is nothing to
   select; otherwise show a teaching error. Old Mac against new bob:
   default `auto` keeps today's links, so mixed-version does not
   silently drop the hand-off.
4. Do not re-spawn bob on every toggle. Locally flip `proposed` and
   the destination capsule from `offer_link`.
5. After Return, keep today's one 🔓 notification line for what was
   actually linked. No second panel.

Mac therefore needs Swift UI work, a `BobProcessClient.capture`
argument, and additive JSON. It does **not** need a new window, a
post-submit flow, or any vault logic.

### 6.3 CLI

`bob capture '!sase:bar'` and `=x!1` stay non-interactive. `--successors
auto` (default) preserves current direct + pull-in auto-link so agent
scripts and muscle-memory shell use do not change. `--successors none`
is the script-friendly "just recover." `--successors sase_foo#^sub-1,…`
is the explicit form the GUI clients send.

Human output already has `would link` / `linked` / `unblocked` /
`surfaced`. Add `offered` for a linkable row that this run did not
select.

---

## 7. Candidate set (the planner change)

Keep the graph-transition test. Change only who may receive a `link`.

```text
OFFER  = recovered-or-pulled rows that have an anchor, are not
         already planned, not hidden (except a pull-in ^prj after
         #hide removal), and not kill-switched

LINK   = the subset the client selected
         (or A3's single pre-selected offer; or --successors auto)

proposed(row):
  direct fully-unblocked dependent            → on
  §12.10 pull-in ^prj (empty or parent)       → on
  project_member                              → off
  non-empty ^prj (today's project_task)       → off
```

Mint a missing `^block-id` **only for selected rows**, on the link
write. Do not mint for an unchecked resident: that was the cost of
auto-link, and most residents have no id (the two `sase_foo` subtasks
have none).

Still-blocked rows stay in the picker as muted context. They are not
toggles. Linking a still-blocked task would raise its remaining
prerequisites to Next (§5 promotion) — the original research's first
rejected literal.

Inbox offers stay offered, with the existing `inbox` chip. Hidden
`#hide` residents stay recover-only. Recurring tasks stay out (capture
already refuses to complete them).

### Project expansion, precisely

When this close fully unblocks a `^prj` R of project N:

- If EMPTY(N): R is a pull-in offer (proposed on). There are no
  unhidden residents to list. Hidden residents are not offers.
- If not EMPTY(N): R is a `project_task` offer (proposed off). Every
  resident this pass recovered as `project_member` is an offer
  (proposed off), grouped under N.
- Residents that remain Blocked on their own deps (PDC3) appear in
  `still_blocked`, not as offers.
- Descendants of N are not recovered (PDC6) and do not appear.

When this close empties N because it closed N's last ordinary task
(trigger a) or last open child project (trigger c): the emptied `^prj`
(and/or parent `^prj`) is a pull-in offer in the same picker. That is
A7. There is usually nothing else in that section.

Do not also dump N's already-Ready work that this close did not
recover. That is the A2 trim. It is what keeps unblocking `sase.md`'s
`^prj` from listing 200+ historical rows — only the residents this
pass actually moved off `[?]` appear.

---

## 8. Contract

Specify once in `docs/task-dependencies.md` §12, implement twice (Rust
planner, cycler mirror). Mac only decodes.

Additive JSON, schema still 1:

```json
"unblocked": [{
  "trigger": "dependency" | "project_empty" | "project_member",
  "offer": "direct" | "project_member" | "project_task" | "project_empty",
  "proposed": true,
  "link": null,
  "offer_link": { "day_file": "…", "entry_name": "FIX", "…": "…" },
  "not_linked": null
}]
```

- `offer` present ⇒ the row is linkable this run.
- `proposed` is the A8 default the client may flip.
- `offer_link` is the placement that will be used if selected.
  Always populated for offers, so Mac can render destination capsules
  without a second spawn.
- `link` non-null ⇒ this run **will** (dry-run) or **did** (real)
  insert that bullet. Dry-run equals real-run **only when**
  `--successors` matches the proposed set. That is a documented
  exception to today's "dry-run JSON equals real-run JSON."
- `not_linked` gains no `breaker`. Retired values stay decoded so old
  notices do not crash. New runs never emit `breaker`.
- `trigger: "project_member"` is new and optional; old clients treat
  those rows as recovered.

CLI flag on `bob capture` (alphabetically with the others, short alias
required by `cli_rules.md`):

```text
-S, --successors auto|none|<note#^id>,…
```

`auto` = link every `proposed` offer (today's directs + pull-ins, not
residents). `none` = recover only. A list = exactly those ids, which
must be offers; unknown ids are a teaching error, not a silent skip.

`plan.link_unblocked: false` still wins over `--successors` and over
the picker: offers exist for copy, `proposed` is false, linking
refuses.

Vectors to rewrite, not just add:

- SL17: six directs → all offered, none auto-broken; `--successors auto`
  links all six; picker clients send the list.
- PDC2: residents become `offer: project_member`, `proposed: false`.
- PP15: six directs + a pull-in → six direct offers plus a pre-selected
  pull-in; no breaker.
- New: `sase_foo` close of `^bar` → `^prj` offered as `project_task`
  (off), two residents offered as `project_member` (off).

Undo: the reopen receipt already stores inserted bullets and pre-edit
lines (`136-plugin-successor-receipt.js`, §12.9 / §12.10). It continues
to take back only links this pass actually wrote.

---

## 9. Alternatives considered

| Approach | Verdict |
| --- | --- |
| Keep auto-link; picker only when the breaker would fire | **Reject.** Does not fix `sase_foo`, and Bryan asked to stop auto-adding. |
| Keep auto-link for directs; picker only for project expansion | **Respectable hybrid.** I would ship this if A3's skip feels too clever. Worse than A3+A8 because two directs would still auto-link without a chance to drop one. |
| Always prompt, including the 1:1 case | **Literal request.** Honest, slightly worse for `]s` + Ctrl+Enter. Accept if Bryan rejects A3. |
| Sticky toast with click-to-link, walk continues | **Reject.** Notices cannot take keystrokes; walk landings already suppress the card; a 10 s toast is how the 2026-10-09 "suggest only" option failed. |
| Post-submit Mac panel | **Reject.** Breaks one-shot capture and "preview is the truth." |
| Swift or plugin computes residents | **Reject.** Thin-client / no-plugin-subprocess rules. |
| Prompt on unanchored closes, and ask which Pomodoro | **Defer.** Real feature, different question. |
| Recover descendants immediately so the picker lists the whole subtree | **Reject.** Reopens `close_recovers_subprojects = no`. Reconcile + TICKLER already cover them. |
| TTY prompt in `bob capture` | **Reject.** Agents and Mac would hang or need a new protocol anyway. |
| Keep the breaker as a display cap | **Reject.** The picker already groups and can search; a hard 5 would hide offers Bryan asked to see. A *display* fold (`+N more` with filter) is fine above ~12 visible rows. |
| Default-select project members | **Reject.** That recreates auto-link for the dangerous class. `sase.md` would put a crowd into Next. |
| Link the unblocked `^prj` instead of its residents | **Reject as default** (A8 off). A project with remaining work is not next; its first Ready resident might be. Bryan can tick `^prj` if he wants the outcome line on Today. |

---

## 10. Implementation sketch

One epic, three repos. Contract first.

| Phase | Repo | Content |
| --- | --- | --- |
| **P1 contract** | bob-cli | Rewrite §12: offers vs links, retire breaker, PDC2/PP15/SL17, JSON, `--successors`, copy. `docs/capture.md` and `docs/plan.md` one-liners. |
| **P2 planner** | bob-cli | Pure planner returns offers + placements with linking suppressed; apply-selected helper. Wire `!` and close. Tests for `sase_foo`, empty pull-in, parent trigger (c), six directs. |
| **P3 Obsidian** | bob-plugins | Cycler: recover now, picker, then link. Nav: successor picker card (new fragment next to `285-unblocked-notice.js` / `060-decay-card-modal.js`). Walk awaits it. Receipt stores selected links only. Then `bob plugins sync`. |
| **P4 Mac** | bob-mac-capture | Decode `offer` / `proposed` / `offer_link`. Checkbox Unblocked section. Selection merge across preview refreshes. `--successors` on submit. Notification uses the committed list. macOS CI. |
| **P5 polish** | all | Search/filter when offers > 12; plan meter warn tone; reopen-undo; kill switch; mixed-version tests. |

P3 and P4 start when P2's JSON is frozen. Do not have the plugin spawn
`bob`.

After shipping, a new decision: "A close offers its unblocked work;
Bryan picks the successors." It supersedes the auto-link reading of
§12, amends PDC2, and records that the tickler decision's rejected
"successor-link residents" alternative is now an *optional picker
offer*, not an automatic link. Do not edit the tickler record in place.

---

## 11. Risks

| Risk | Mitigation |
| --- | --- |
| Picker on every 1:1 close slows the walk | A3 skip; Esc is always "none + continue"; decay-card already trained the blocking-decision muscle |
| `sase.md`-scale offer lists | A2 (recovered-only); A8 (members off); fold + filter above 12; never default-select the crowd |
| Two-write race (daily note changed during picker) | Today's `failed` / `couldn't link`; recoveries stand |
| Mixed-version Mac | `--successors` unknown → `unsupportedOption`; default `auto` on old clients |
| Dry-run ≠ submit after toggles | Documented; Mac does not re-spawn on toggle; submit sends the list |
| Sticky Next on a bad pick | Alt+N remains the per-link undo; reopen take-back remains the whole-gesture undo; footer still teaches Alt+N |
| Minting IDs into notes Bryan only ticked | Mint only selected rows; chip `added ^id` as today |
| Subproject residents missing from the picker | PDC6, called out; they keep the tickler guarantee |
| Live preview wipes Mac checkboxes | Client-side selection keyed by identity, merged onto new offers |

---

## 12. Open questions for Bryan

Each question gives my default.

1. **Skip the picker for a single pre-selected direct successor (A3)?**
   Default: yes. Alternative: always prompt (literal request).
2. **Default ticks (A8)?** Default: directs and empty-`^prj` pull-ins
   on; residents and busy `^prj` off. Alternative: everything off, so
   even a 1:1 needs Enter (then A3 cannot skip).
3. **CLI default `auto`?** Default: yes, so `!sase:bar` in a terminal
   still hands off. Alternative: CLI also links none unless `-S` is
   passed.
4. **Include `#ref` residents** of an unblocked project as offers?
   Default: yes if this close recovered them; they are open work. The
   inbox chip already exists for inbox files.
5. **Filter box from the first row, or only above 12 offers?**
   Default: only above 12, so the `sase_foo` case is three naked rows.

---

## 13. Recommended solution

Build **Successor Offers: recover always, link what Bryan ticks.**

- **Trigger.** Any Bob close that already runs §12 (Ctrl+Enter, Alt+]
  Done, `!note:id`, `=x!` / `=!`, Mac submitting those). Cancel, reopen,
  raw checkbox, and hooks still never link.
- **Recover.** Unchanged, including PDC2 residents, `[unblocked::]`,
  tag strip, and pull-in `#hide` removal. This close still unblocks
  `sase_foo`'s subtasks even if Bryan picks nothing.
- **Offer.** Direct fully-unblocked dependents; recovered project
  members of a `^prj` this close unblocked; emptied-project and parent
  `^prj` pull-ins. One grouped picker. Still-blocked rows muted.
- **Select.** Directs and empty pull-ins on; members and busy `^prj`
  off. No 5-breaker. Soft plan meter. Esc / `--successors none` = link
  nothing.
- **Skip.** One pre-selected offer and no extras → auto-link, existing
  toast (A3). Mac never skips: the preview is the prompt.
- **Where.** Same placement as §12.3 (predecessor slot, or same-name
  continuation). Same minting, same Next raise, no freshness stamp.
- **Tell.** Obsidian: blocking Unblocked picker, then the existing
  notice copy for what was linked. Mac: checkboxes on the Unblocked
  preview, `--successors` on submit, one 🔓 notification. CLI: `-S`.
- **Specify once, implement twice,** Mac decodes. New decision after
  ship; do not silently rewrite PDC2 or the tickler record.

That is the smallest change that (a) stops surprise sticky Next, (b)
makes the `sase_foo` close able to pull in "Some subtask" / "Some other
subtask" without dumping `sase.md` onto Today, (c) puts last-task and
last-subproject pull-ins on the same rails, and (d) leaves Bob Mac
Capture a thin client of bob.

---

## About this report

**Date:** 2026-10-13. Independent swarm report (`__grk`). Did not read
peer reports from this swarm.

**Baselines.** bob-cli workspace tree (docs + Rust successor planner);
bob-plugins after `sase repo open` (cycler successor fragments, nav
Unblocked notice, decay card); bob-mac-capture after `sase repo open`
(`SuccessorRows`, `CapturePanelView` Unblocked section,
`BobProcessClient.capture`); live vault `~/bob/sase.md` and
`~/bob/sase_foo.md` as of this close of `^bar`.

**Prior research used (unrelated swarm, allowed):**
`research:202610/unblocked_successor_links_on_close/unblocked_successor_links_on_close.md`
(auto-link design, breaker rationale, deferred "ask when >1", rejected
"suggest only").

**Memory (audited):** `decisions:mac-capture-is-a-thin-client`,
`task-lanes-are-sticky`, `projects-block-from-prj-line`,
`subprojects-inherit-project-blocking`,
`unblocked-tasks-resurface-as-ticklers`, `answering-advances-the-walk`,
`task-deps-are-depends-on-links`, `today-is-read-from-the-ledger`,
`idle-capture-shows-ledger-agenda`; glossary Task Link, Task Dependency
Link, Project Task, Project Note, Pomodoro; `cli_rules.md`;
`sase_artifacts.md`.

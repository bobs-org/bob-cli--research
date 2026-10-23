# A Keep Log for counted rotten refreshes

> **Research query:** Add a "rotten log" that works like the Work Log, with an
> optional prompt when a rotten task is refreshed with Alt+F or Ctrl+Alt+F, so
> there is a visual indication and an audit trail of how many times (and when
> and why) a task has been manually refreshed. Critique the plan, call out
> justified requirement changes, and recommend a solution. Include a glossary
> entry for the new term.

## Bottom line

**Build a Keep Log. Do not prompt on every rotten keep, and do not use the log
as a second counter.**

The goal is right: counted keeps currently remember a streak (`[keeps:: N]`)
and a last-confirmed date (`[fresh::]`), and they ask *why* only at the decay
card. There is no in-note history of the keeps in between. A child log modeled
on `🛠️ **WORK LOG**` is the right storage for that history.

The plan as written overshoots in three places that would fight decisions
already on the books:

1. **Alt+F is supposed to stay a one-key honest keep.** Pending already pays
   for a Work Log modal because "what did you get done?" is a work question.
   ROTTEN is optional upkeep over the whole Ready pool. A modal on every
   rotten keep turns the cheapest review answer into two keys (chord, then
   Enter) and will train `]s` skips.
2. **"How many times" is already visual.** The freshness mark folds
   `[keeps:: N]` into faint pips and a leaf at the keep limit
   (`docs/freshness.md` §11). `docs/freshness.md` §2a forbids a second
   lifetime counter. The log must be an audit trail, not a parallel count
   that decay, marks, or `bob freshness` start reading.
3. **"Rotten log" names a transient bucket.** After a successful keep the
   row is FRESH. Counted eligibility already includes TICKLER as well as
   ROTTEN. The log then sits on a fresh task. Call it a **Keep Log**, with
   **Rotten Log** as a glossary alias.

Recommended shape:

- New managed child `⟳ **KEEP LOG**`, newest-first dated entries, same
  insert/prepend rules as the Work Log.
- Writers fire only on **counted** Alt+F / Ctrl+Alt+F keeps: exact
  due-Ready `rotten`/`tickler` rows, the same `keepLine` eligibility that
  increments `[keeps::]`.
- Prompt like the Pending Work Log modal, but **starting at the second
  consecutive keep** (pre-write `keeps >= 1`). Blank Enter still stamps
  and writes no entry. Escape cancels the stamp and the Ctrl+Alt+F
  advance. At the keep limit the decay card is the only extra UI.
- Once a Keep Log exists, a later blank keep writes `🤷 no reason given`
  so that history has no gaps (Schedule Log completeness), without forcing
  a log onto tasks that were only ever one-key kept.
- Pips stay the count. The child log is the when/why trail. The mark
  tooltip may show the newest reason; it must not grow a second numeral.

## Is this a good idea?

**Yes, as a sparse why-trail. No, as "Work Log but for every rotten Alt+F".**

### What is actually missing

Three questions were asked. Two are already answered on the task line:

| Question | Already stored | Visible today |
| --- | --- | --- |
| How many times (this streak)? | `[keeps:: N]`, saturating 1–999 | Faint pips after the freshness mark; `kept N×` on the Fresh notice and on `bob freshness list`; tooltip `Kept N reviews in a row · Bob asks at L` |
| When (last keep)? | `[fresh:: YYYY-MM-DD]` | Mark label `today` / `Nd`; tooltip `Confirmed {date}` |
| When (each keep)? | nowhere | git history only |
| Why (this keep)? | nowhere until the decay card | Decay outcomes write `· kept N×` into the Schedule Log or Cancel Log; **Keep** and dismissals write no log (`docs/projects.md`, Approved-decay decision planner) |

The gap is **per-keep when/why between first keep and the card**. That gap is
real. Reword, Less often, Not now, and Drop already leave a dated sentence.
A bare keep does not. If you later wonder "why did I keep this for three
reviews?", the vault cannot tell you.

### What the request would disturb

- **`decisions/answering-advances-the-walk`.** Alt+F is the one stay
  answer; Ctrl+Alt+F stamps and advances. A modal in front of every
  rotten keep makes Ctrl+Alt+F a chord-plus-dialog, and Escape (which
  already cancels the Pending Work Log prompt and refuses the stamp)
  becomes a footgun in a fast ROTTEN sweep.
- **`decisions/rotten-keeps-use-priority-decay` and
  `docs/freshness.md` §2a.** Keeps is a streak, not a lifetime total.
  "Do not introduce a second lifetime counter or alias." A rotten log
  whose length is treated as the count reopens that record.
- **`decisions/ready-is-freshness-gated`.** Classification stays
  read-time; stamps remain the human confirmation. A child log is
  history, which is allowed, as long as nothing classifies from it.
- **Closed managed-child registry.** Machine-owned direct children are
  a closed set (`docs/task-dependencies.md` §2.4,
  `docs/reference/vault-format.md`). A new log kind is a
  cross-engine change, not a plugin-only convenience. Cancel Log got
  to be plugin-only because capture is taught to land *below* a
  first-child Cancel Log without parsing it. Work/Schedule logs append
  last, so capture, Task Link scanners, Pomodoro scanners, highlight
  snapshots, and the MC vectors must all recognize a Keep Log or they
  will treat it as user prose or a Task Link.

### Prior art that already rejected a sibling of this idea

The keep-streak research
(`research:202610/rotten_keep_streak_and_approved_decay/rotten_keep_streak_and_approved_decay.md`)
called a "lifetime count + sparse dated REVIEW LOG" the strongest
rejected alternative for v1: structural multi-line writes on a one-key
gesture, a new log grammar, and a mark that would have to read child
blocks. Counting, pips, and the decay card shipped instead, with
decision-time Schedule/Cancel Log entries as the audit trail.

That rejection still holds **for using a log as the counter**. It does
not hold for a **sparse, optional-reason Keep Log** now that the counter
exists and the remaining hole is qualitative. Revisit is justified;
replaying the rejected design as the counter is not.

### Live vault (2026-10-23)

`bob freshness list -f json` (schema 14): `due 0`, `rotten 0`,
`tickler 0`, `refreshed_today 41`, `upkeep_today 34`, `fresh 5`,
`decay.keeps 3`, decay on. Morning review for the day is done.

A column-0 `#task` census of `~/bob` (excluding `.git` / `.obsidian`):

| Stock | Count |
| --- | --- |
| Open Ready `[ ]` | 42 |
| Open tasks (`[ ]` / `[*]` / `[/]` / `[?]`) | 485 |
| Open tasks with `[keeps::]` | 3 (two Ready at 1, one Blocked at 2) |
| `🛠️ **WORK LOG**` markers | 166 |
| `🗓️ **SCHEDULE LOG**` markers | 558 |
| `❌ **CANCEL LOG**` markers | 75 |

`upkeep_today` is every non-lane stamp dated today, including NEW and
PROJECTS, so 34 is **not** 34 counted rotten keeps. Counted keep
streaks are currently rare. Steady-state, a 42-task Ready pool on a
7-day interval is about **six counted ROTTEN keeps per day** if the
walk clears the tier. That is the prompt tax to plan for, not today's
zero queue.

Decay cards are not firing in this vault right now. A Keep Log would
be sparse and useful on the few tasks that actually get kept, which is
an argument for building it *and* an argument against prompting on the
first keep.

## Requirement adjustments

Each change to the request as written is called out here.

| # | You asked for | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | Name and marker **Rotten Log** | Canonical **Keep Log**, marker `⟳ **KEEP LOG**`. Glossary alias **Rotten Log**. | After the stamp the task is no longer rotten. Counted eligibility includes TICKLER. `🍂` already means decay/cancel. `⟳` is the due glyph the mark already uses. |
| **A2** | Prompt whenever a rotten task is refreshed with Alt+F / Ctrl+Alt+F | Prompt only on **counted** keeps (exact due-Ready `rotten`/`tickler`, same as `keepLine`), and only from the **second** consecutive keep (pre-write `keeps >= 1`). First keep stays one-key. | First keep is "still right, first time due." The interesting why is the repeat. Uncounted Alt+F (NEW, FRESH/early, PROJECTS, lanes, unblocked ticklers, cache misses) must not prompt. |
| **A3** | Work-log-like optional entry | Same modal contract as Pending: Enter on empty still keeps, Escape cancels the whole refresh including Ctrl+Alt+F advance. **Once a Keep Log exists**, a blank keep writes `🤷 no reason given` (Schedule Log completeness). | Work Log skip-on-blank is right until the task has opted into history. After that, gaps are worse than a shrug. |
| **A4** | Log shows how many times | **Do not.** Count stays `[keeps:: N]` + pips. Log length is not a counter, not a mark input, not a `bob freshness` field. | `docs/freshness.md` §2a: no second lifetime counter. Streak and lifetime diverge on every Reword / Less often / Not now / generic stamp. |
| **A5** | Visual indication of the count | Keep the existing pips and leaf. Optional polish: tooltip line with the newest Keep Log reason. No second widget, no `×N` badge, no history glyph beside the mark. | "Loud only when actionable." Pips already do count. A second numeral on a dense line is the rejected standalone-icon design from the keep-streak research. |
| **A6** | Same as Work Log | Clone **insert/prepend and prompt machinery**, not the Work Log itself. New `ManagedTaskLogKind::Keep`. | Work Log means work performed (unlink, Alt+N release, Pending refresh, scheduling). Mixing "what I did" with "why I kept a stale Ready task" poisons both prompts. |
| **A7** | Rotten only | Counted **ROTTEN and TICKLER**, excluding `returned_by: unblocked` (those keeps neither increment nor decide). | Matches `docs/freshness.md` §2a. A scheduled tickler keep is a bare keep; an unblock tickler is not. |
| **A8** | Prompt on Ctrl+Alt+F the same as Alt+F | Yes, one prompt path, then stamp, then the existing advance tail. At-limit **skips the Keep Log prompt** and opens the decay card only. | Stacking modal then card is unusable. Decay Keep (⌥F) writes no extra prompt; if a Keep Log already exists, prepend a machine `⟳ keep · kept N×` so the trail stays complete. Other card outcomes already log to Schedule/Cancel Log; if a Keep Log exists, prepend a matching machine line there too. |
| **A9** | (implicit) Capture / CLI | No capture grammar, no new `bob` subcommand, no freshness JSON schema bump in v1. | Writers are nav-only, like the Pending Work Log path. Parsers in bob-cli exist so scanners isolate the marker. |

## What exists today (verified)

### Work Log (the template)

Glossary and `docs/reference/glossary.md`: a `🛠️ **WORK LOG**` direct
child, newest-first `*YYYY-MM-DD* — summary` entries. Blank summary
writes nothing.

Plugin writer: `planWorkLogInsertion` in block-id-prompt
(`plugins/block-id-prompt/src/040-editor-pomodoro-and-logs.js`) and
`insertLaneWorkLogEntry` in navigation-hotkeys
(`plugins/bob-navigation-hotkeys/src/220-property-targets.js`). Prepend
under an existing direct-child marker; otherwise append marker + entry
at the end of the task's child block. Independent copies; plugins do
not import each other.

Pending Alt+F / Ctrl+Alt+F already prompts
(`docs/freshness.md` §5, `FreshnessRefreshSummaryModal` in
`plugins/bob-navigation-hotkeys/src/190-summary-modals.js`):

- Header "Refresh task" / "Refresh N tasks".
- Placeholder "What did you get done? (optional · ↵ to skip)".
- Preview: dated entry, or "Refresh only; no Work Log entry".
- Enter submits (possibly empty). Escape / Cancel closes with
  `onDone(null)`, which **refuses the stamp**.
- Counted and Task Link batches share one summary; only `[/]` targets
  receive it (`isPendingWorkLogTargetRawLine`).
- Planner `planFreshStampBatchWithWorkLogs` stamps first, then inserts
  bottom-up so later lines stay valid.

Tests: `scripts/test-navigation-refresh-modal.cjs`,
`scripts/test-navigation-keep-counting.cjs` (stubs
`requestFreshnessRefreshSummary`).

### Schedule Log (completeness and machine reasons)

Blank reason: no marker yet → write the date only, create no log; marker
already present → `🤷 no reason given`. Machine rolls use `🎲`. Decay
Less often / Reword write Schedule Log `other` entries with `· kept N×`.
Drop writes Cancel Log `🍂 dropped after 3 keeps`. Decay **Keep writes
no log**. That last fact is exactly the hole a Keep Log fills.

### Keep streak and marks (the count you already have)

- `[keeps:: N]` after `fresh`/`refresh`.
- Sole increment helper `api.freshness.keepLine`.
- Exact eligibility: pre-write queue row with matching path, 1-based
  line, raw text, `lane === 'ready'`, `tier in {'rotten','tickler'}`.
- Pips cap at 3 (or the threshold if 1–2), overflow `+N`.
- Leaf + `Alt+F to decide` at limit when decay and the card capability
  are on.

### Walk and child inserts

`docs/freshness.md` §6: the walk follows note path + line text of the
**task row**. A Work Log or Schedule Log insert must not make an answer
or `]s` skip. Ctrl+Alt+F after a Keep Log insert reuses that contract.
Advance still happens after the modal resolves, with the existing ~350 ms
gesture lock.

### Managed-child isolation

`ManagedTaskLogKind` is `{Schedule, Work}` in
`src/native/capture/sub_bullet.rs`. Highlight snapshots map those plus
Cancel Log (`src/native/highlights_ref/note_snapshot/visibility.rs`).
Task Link / Pomodoro scanners reject every registry row. A Keep Log that
is not on that list will be seen as a user child.

## Recommended design

### Grammar

```markdown
- [ ] #task Rename queue input [fresh:: 2026-10-23] [refresh:: 7] [keeps:: 2] ^rq
	- ⟳ **KEEP LOG**
		- *2026-10-23* — still waiting on the API review
		- *2026-10-16* — 🤷 no reason given
```

- Marker: `⟳ **KEEP LOG**` (optional matching emoji, optional colon,
  legacy none). A present emoji must agree with the label, same rule as
  Work/Schedule (`🗓️ **WORK LOG**` is not a marker).
- Entry: `*YYYY-MM-DD* — <reason>`, newest first, one level under the
  marker. Emphasis and em dash match Work Log (`*` and `U+2014`).
- Machine reasons, when written: `⟳ keep · kept N×`,
  `🎲 not now · kept N×`, `🎲 less often · every 7 → 14 days · kept N×`,
  `🎲 reword · kept N×`. Drop continues to own the Cancel Log; it may
  also prepend `🍂 dropped after N keeps` here if the Keep Log already
  exists.
- Slot: last among direct children, like Work/Schedule. Existing managed
  lines are never moved. First creation appends at the child-block end;
  later entries prepend under the existing marker.
- Not a Task Link, not a section title, not a tree-close target.

### When the prompt appears

On Alt+F / Ctrl+Alt+F, after exact-eligibility resolution and **after**
the at-limit decay-card short-circuit, **before** any write:

1. At-limit counted target, single press → decay card. No Keep Log
   prompt.
2. Else any target that is counted **and** whose pre-write
   `[keeps::] >= 1` (this press will make 2, 3, …) → one Keep Log
   modal. Copy: "Why keep this?" / placeholder "Optional · ↵ to skip"
   / preview under `⟳ **KEEP LOG**`.
3. Else any Pending `[/]` target → existing Work Log modal (unchanged).
4. A counted batch that mixes Pending and Keep Log eligibles can open
   both, Work Log first then Keep Log. That mix is rare; do not invent
   a combined prompt. Single-row morning review never hits it.

Uncounted targets never qualify, even if the cursor is on a task that
*looks* rotten in the mark but failed exact match (stale cache, line
shift, wrong lane). Truthful or skip, never a guessed prompt.

### What a blank Enter does

```
no Keep Log yet, blank reason  → stamp only (fast path, first or later)
Keep Log exists, blank reason  → stamp + prepend `*today* — 🤷 no reason given`
nonblank reason                → stamp + prepend `*today* — {reason}`
Escape                         → write nothing, do not advance
```

This is A3. It is the one place I would not copy Work Log blindly:
Work Log skip-on-blank is correct for "no work to record." A keep
with no words still happened; once you have asked the vault to remember
keeps on this task, remember the day.

Do **not** auto-create a Keep Log on the first one-key keep. That would
put a growing child on every Ready task that ever rots, about six new
blocks per day in the current pool, and would make the log a de facto
lifetime counter.

### Display

- Task line: existing pips / leaf only.
- Task body: the Keep Log child, foldable like any list.
- Tooltip (follow-up in the same epic if cheap, else a fast follow-up):
  if a newest Keep Log entry exists, one extra line with its reason,
  never containing `::`. Counting-only wording unchanged when no log.
- `bob freshness list` human/JSON: **no new fields in schema 14**. The
  streak is already there as `keeps`.

### Decay card

Leave the card's writers alone for Schedule/Cancel Log. Add a Keep Log
append only when the marker already exists, so a task you have been
annotating gets the decision in the same list:

| Card row | Keep Log (only if marker exists) |
| --- | --- |
| ⌥F Keep | `*today* — ⟳ keep · kept N×` |
| ↵ Not now | `*today* — 🎲 not now · kept N×` |
| L Less often | `*today* — 🎲 less often · every A → B days · kept N×` |
| E Reword | `*today* — 🎲 reword · kept N×` |
| D Drop | `*today* — 🍂 dropped after N keeps` |
| Esc | nothing |

### Counted / Task Link batches

Same as Pending Work Log: one shared reason, applied only to eligible
targets, bottom-up inserts. At-limit targets still skip without
stamping (`N needs a decision`). A skipped at-limit row must not
receive a Keep Log entry.

## Implementation map

Cross-repo, contract-first. No new public CLI verb (`cli_rules.md`:
read-only reports stay top-level; this is not a report). Docs route:
behavior contract in `docs/freshness.md` §5 plus the closed registry in
`docs/task-dependencies.md` §2.4 and `docs/reference/vault-format.md`;
guide touch-up only where `docs/guides/run-morning-review.md` and
`docs/getting-started.md` describe Alt+F (`docs.md`).

### bob-cli

1. `ManagedTaskLogKind::Keep` and labels `KEEP LOG` in
   `src/native/capture/sub_bullet.rs` (emoji `⟳`, no VS16). Assembly
   tests next to the Work/Schedule cases in
   `src/native/capture/tests/assembly.rs`.
2. Isolation: Task Link / Pomodoro / section-title / R8 / MC vectors
   (`docs/task-dependencies.md` §11.8). Treat Keep Log like Work Log
   in every "recognisers that reject it" cell.
3. Highlight snapshots: `log_kind_for_item` plus a condensed `KEPT`
   row (newest entry + `older_count`), sibling of `WORKED`.
4. Glossary: new strand **Keep Log** (alias Rotten Log) via
   `/sase_memory_write` at implementation time; mirror
   `docs/reference/glossary.md`. Update the Task Freshness strand to
   mention the log as history that never drives decay.
5. New decision record: "Keep logs are a sparse reason trail." Claim:
   counted keeps may record an optional dated reason under
   `⟳ **KEEP LOG**`; the streak and pips remain the only count; the
   log never classifies, never decays, never stamps. Amends nothing
   about freshness writes other than adding a child. Does not
   supersede `rotten-keeps-use-priority-decay`.

No `stamp_fresh` / `keepLine` Rust increment path is required. Rust
does not increment keeps today; it should not write Keep Log entries
either. Parsers only.

### bob-plugins

1. **bob-navigation-hotkeys** (writer + prompt):
   - Clone `WORK_LOG_PARENT_RE` / `insertLaneWorkLogEntry` /
     `formatLaneWorkLogEntry` as Keep Log helpers next to them in
     `src/010-requires-and-config.js` and `src/220-property-targets.js`.
   - Clone `FreshnessRefreshSummaryModal` as
     `FreshnessKeepLogModal` (different copy, same Enter/Escape
     contract) in `src/190-summary-modals.js`.
   - Wire in `refreshTaskFreshnessOnTasks` and
     `refreshTaskFreshnessOnLinks` (`src/520-plugin-lane-links-and-review.js`,
     `src/530-plugin-freshness-refresh-and-decay.js`) using the
     pre-write `counted` flag plus parsed keeps, **after** the decay-card
     short-circuit, **before** `planFreshStampBatchWithWorkLogs`.
   - Extend `planFreshStampBatchWithWorkLogs` or add
     `planFreshStampBatchWithKeepLogs` that inserts bottom-up after
     the stamp plan, sharing the all-or-nothing refusal.
   - Decay-card commit adapters: if `findKeepLogParent` hits, prepend
     the machine line.
2. **bob-ledger-tools**: reject Keep Log in Task Link / tree scanners;
   optional tooltip reader. No pip change. Freshness namespace bump
   only if the tooltip reader ships in the same release (otherwise nav
   can write with no namespace change).
3. **task-status-cycler** and **block-id-prompt**: copy the parent
   regex so their Work Log planners never adopt a Keep Log marker, and
   so R8/legacy-child isolation stays honest. They should not write
   Keep Log entries (they do not run Alt+F).

### Tests to clone, not invent

- `scripts/test-navigation-keep-counting.cjs` — counted vs uncounted,
  Escape refuses, blank first keep writes no marker, second keep with
  blank on an existing marker writes 🤷, Ctrl+Alt+F advance after
  insert, at-limit skips prompt.
- `scripts/test-navigation-refresh-modal.cjs` — Keep Log modal copy
  and preview bytes.
- Decision-card handler suite — machine Keep Log lines only when the
  marker exists.
- CLI assembly + MC vectors — marker isolation.
- Highlight snapshot tests next to current Work Log hiding.

### Rollout

One epic, two layers:

1. **Parser + isolation + writer + prompt** (the product).
2. **Tooltip last-reason** if it fits; otherwise a follow-up bead, not
   a blocker.

Ship behind the existing `freshness.decay` off-switch? No. The log is
not decay. If decay is off, counted keeps still increment pips and
should still be allowed to record a why. A separate
`freshness.keep_log: false` is unnecessary for v1; blank Enter already
opts out per gesture, and never creating the marker opts out per task.

Mixed versions: old nav never writes the marker, which is fine. New
nav with old ledger: the child is visible as markdown even if scanners
in an old plugin mis-see it — **that is the mixed-version risk**, and
why the parser copies in cycler / block-id-prompt / ledger-tools have
to land in the same plugin train as nav. Do not ship the writer a
week before the recognisers.

## Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Prompt on every counted rotten keep (request as written) | Rejected as default | Two keys on optional upkeep; first keep is low-value why; trains `]s` skip. Offered as a one-line config later if the second-keep default feels too quiet. |
| Silent dated entry on every counted keep | Rejected | Completeness of *when* without a prompt, but it auto-creates a growing child on every Ready task that rots (~six/day here) and becomes a lifetime counter in disguise. |
| Reuse Work Log | Rejected | Different question, different prompt copy, different readers (Pomodoro close copies Work Log trees). |
| Reuse Schedule Log | Rejected | Roll-streak classification and "opt-in completeness" are about dates and priority. Bare keeps would drown both. |
| `[kept_why::]` field on the task line | Rejected | Loses history, extends the non-Tasks run, fights "loud only when actionable." |
| Lifetime `refresh_count` plus this log | Rejected | Forbids a second counter; pips already show the streak. |
| Plugin-only marker, like Cancel Log | Rejected | Keep Log appends last. Capture and scanners must parse it. |
| Prompt from keep 0 (first keep) with blank skip | Acceptable fallback | Same machinery; drop the `keeps >= 1` gate. Use this if Bryan wants a why on the first rotten pass. |
| Git history as the audit trail | Rejected as the only trail | Invisible in Obsidian during review, which is when the why matters. |
| New DECIDE tier / dash chip / rotten.md group | Out of scope | Tiers and chips are settled. |

## Critique of the plan in general

The instinct — "I keep pressing Alt+F on the same stale tasks and the
vault forgets the conversation" — is correct. The keep streak closed
the *count* loophole; it did not close the *narrative* loophole. A
Work-Log-shaped child is how Bob already stores narratives (work,
schedule, cancel). Cloning that shape is much better than a new field,
a new mark, or a new tier.

The plan is too broad in trigger and too vague in what "visual
indication of how many times" adds on top of pips. If those two stay
as written, I would not take this on: you would pay a closed-registry
migration and a morning-review tax to duplicate a number the mark
already shows, while most entries would be empty "still right" lines.

With A1–A9, I would take it. It is a small, honest sibling of the
Pending Work Log prompt, aimed at the one review answer that still
leaves no sentence behind.

## Glossary entry (proposed)

Canonical term **Keep Log**. Alias **Rotten Log**. Implementation
writes this through `/sase_memory_write` (new `glossary/keep-log.md`
strand, `docs/reference/glossary.md` mirror). Not written in this
research turn.

```markdown
# Keep Log

*Requested · project*

aka rotten log

A task-local history of counted due-Ready keeps, stored as a
`⟳ **KEEP LOG**` direct child with newest-first dated sub-bullets
(`*YYYY-MM-DD* — reason`). Alt+F / Ctrl+Alt+F on an exact due Ready
ROTTEN or TICKLER row (the same eligibility that increments
`[keeps::]`) may ask for an optional reason starting at the second
consecutive keep. A nonblank reason is prepended; a blank Enter still
stamps, and once the marker exists a blank keep records
`🤷 no reason given`. Escape cancels the refresh. The log is an audit
trail of when and why a task was kept. It never drives decay, lanes,
freshness, or the pip count; `[keeps:: N]` and the freshness mark
remain the streak. Unblocked ticklers, NEW, lanes, PROJECTS, and
other uncounted stamps do not write it. See [[work-log]],
[[keep-streak]], [[task-freshness]], and
[[decisions/rotten-keeps-use-priority-decay]].
```

## Open questions for Bryan

1. **Second-keep gate (A2) or first-keep prompt?** Recommendation:
   second keep. First-keep + blank skip is the faithful reading of the
   request.
2. **Blank-on-existing-log writes 🤷 (A3) or stays skip-forever like
   Work Log?** Recommendation: 🤷, so a log you started stays complete.
3. **Marker spelling:** `⟳ **KEEP LOG**` (recommended) vs
   `🍂 **ROTTEN LOG**` vs `🔁 **KEEP LOG**`.
4. **Decay Keep (⌥F) machine line** when a log already exists, or leave
   Keep silent in both logs as today?
5. **Tooltip last-reason in v1**, or parser/writer only?

## Recommended solution

Ship a **Keep Log**: a Work-Log-shaped managed child that records
optional reasons for **counted** Alt+F / Ctrl+Alt+F keeps, prompted
like the Pending Work Log modal **from the second consecutive keep**,
with Schedule-Log completeness once the marker exists, and with the
decay card remaining the only extra UI at the keep limit.

Do not prompt on every rotten refresh. Do not count from the log. Do
not add a second mark widget. Do not name the marker Rotten Log. Do
not put this in capture or in `bob freshness` JSON for v1.

That gives the visual (pips for how many, child list for when/why) and
the audit trail, without taking Alt+F away from the one-key keep that
the last freshness epic was built to preserve.

## Sources

Researcher `research.55.grk` · 2026-10-23 · independent of the other
four swarm reports. Checked against bob-cli `docs/freshness.md` §§2a/5/6/11
(schema 14), `docs/projects.md` (Approved-decay decision planner,
Schedule-log reason prompt), `docs/task-dependencies.md` §2.4,
`docs/reference/vault-format.md`, `src/native/capture/sub_bullet.rs`,
`src/native/highlights_ref/note_snapshot/visibility.rs`; bob-plugins
navigation-hotkeys `FreshnessRefreshSummaryModal`,
`insertLaneWorkLogEntry`, `planFreshStampBatchWithWorkLogs`,
`matchFreshStampExactEntry`, `refreshTaskFreshnessOnTasks`; audited
memory `glossary:work-log`, `glossary:task-freshness`,
`glossary:keep-streak`, `decisions:rotten-keeps-use-priority-decay`,
`decisions:answering-advances-the-walk`,
`decisions:review-walk-is-tiered`,
`decisions:ready-is-freshness-gated`,
`decisions:decay-decisions-are-available-immediately`; prior
`research:202610/rotten_keep_streak_and_approved_decay/rotten_keep_streak_and_approved_decay.md`;
live `bob freshness list -f json` and a column-0 `#task` census of
`~/bob` on 2026-10-23.

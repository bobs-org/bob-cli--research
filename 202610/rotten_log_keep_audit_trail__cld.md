# A Rotten Log: recording when and why a stale task was kept

> **Research query:** Add a "rotten log" that works like the Work Log. When a rotten task
> is refreshed with Alt+F or Ctrl+Alt+F (during the morning GTD review, for example),
> prompt for an optional Rotten Log entry. The goal is a visual indication and an audit
> trail of how many times, when, and why a task was manually refreshed. Critique the
> plan, call out any justified requirement changes, add a glossary entry, and recommend
> a solution.

## Bottom line

**Build it. It is a good idea, and cheaper than it looks.** Bob already has a nearly
identical flow: Alt+F / Ctrl+Alt+F on a Pending (`[/]`) task opens an optional Work Log
prompt, then stamps the task and prepends a `🛠️ **WORK LOG**` entry in one editor
transaction. A Rotten Log is that same flow, aimed at the keep that the keep-streak
design already treats as the one worth questioning.

Four changes to the request are worth making. They are summarized here and explained
under [Requirement adjustments](#requirement-adjustments):

1. **Trigger on exactly the keeps that increment `[keeps:: N]`.** These are exact,
   due Ready ROTTEN *or TICKLER* rows (not unblock ticklers), plus **Keep** on the
   approved-decay card. Each Rotten Log entry and each streak increment are then the
   same event, and the two can never disagree about what a "refresh" is.
2. **Always write the entry; make only the reason optional.** A blank Enter logs
   `🤷 no reason given`, and Escape cancels the keep. This differs from the Work Log,
   where a blank summary writes nothing. Here the count is the point, and the blank
   keep is the rubber stamp you most want to see.
3. **The "visual indication" is the log itself plus the prompt, not a new mark.**
   Rotten keeps happen about once every two mornings (see [data](#live-data)). The
   most useful place to see a task's history is the prompt you answer at that moment,
   which should list the previous entries. On surfaces that already count log
   entries, add a count chip: the Mac agenda shows `⚒ 3` / `🗓 2` today, and the note
   snapshot shows `moved N×`. Keep the freshness mark's pips as the only on-line
   indicator. A tooltip line is an optional later phase.
4. **Record a new decision first.** The accepted record
   `decisions:rotten-keeps-use-priority-decay` explicitly rejects "a new REVIEW LOG
   structure" and says "Keep anyway leaves only the line increment".
   `docs/freshness.md` §2a also says "Do not introduce a second lifetime counter or
   alias." The Rotten Log reverses the first two, so it needs a superseding-in-part
   record. It honors the third: it is a history, `[keeps::]` stays the only counter
   field, and neither is ever derived from the other.

Marker and entry grammar (recommended):

```markdown
- [ ] #task Email the vendor about the SSO renewal [fresh:: 2026-10-23] [keeps:: 3] ^sso
	- 🥀 **ROTTEN LOG**
		- *2026-10-23* — waiting on their legal review; still mine · kept 3×
		- *2026-10-16* — 🤷 no reason given · kept 2×
		- *2026-10-09* — still needed before the Q4 audit · kept 1×
```

## What exists today

Every row below was checked against the source. Paths are repo-relative.

| Fact | Why it matters | Evidence |
| --- | --- | --- |
| Alt+F is `refresh-task-freshness`; Ctrl+Alt+F is `refresh-task-freshness-and-advance` (same handler, `advance: true`). | A single entry point serves both keys. | bob-plugins `plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js` (~L207–220); `520-plugin-lane-links-and-review.js` `refreshTaskFreshness` |
| **Precedent:** before stamping a Pending target, Alt+F/Ctrl+Alt+F open `FreshnessRefreshSummaryModal` ("What did you get done? (optional · ↵ to skip)"). Blank Enter refreshes with no entry; Escape cancels and Ctrl+Alt+F does not advance. Batches share one summary across their Pending targets. | The Rotten Log prompt can reuse the modal, the prompt plumbing, the batch handling, and the one-transaction write. | `190-summary-modals.js` (~L662); `520-…` `requestFreshnessRefreshSummary`; `480-review-jump-and-nav-api.js` `planFreshStampBatchWithWorkLogs`; `docs/freshness.md` §5 |
| A keep is counted only for an exact pre-write queue match: `lane === 'ready'` and tier `rotten`/`tickler` (`matchFreshStampExactEntry`). `api.freshness.keepLine` is the sole increment helper, and it internally leaves unblock ticklers (`returned_by: unblocked`) unchanged. | The eligibility predicate already exists, and a post-write check (`countFreshStampKept`: after = before + 1) tells which targets actually incremented. | `480-…` (~L805–842, ~L690); ledger-tools `080-freshness-placement.js` `freshnessReturnedByFromLine`; `docs/freshness.md` §2a |
| At the keep limit (default 3), a single press opens the decay card (Not now / Less often / Reword / Drop / Keep). Its **Keep** is a one-line `replaceEditorLine` and writes no log. Less often and Reword write Schedule Log entries (`🎲 less often · …`, `🎲 reword · kept 3×`); Drop writes a Cancel Log entry. | Card Keep is the most important keep to explain and currently leaves no trace. It must become a multi-line transaction. | `540-plugin-decay-picker-and-cancel.js` `applyFreshnessDecayCardKeep`; `docs/projects.md` "Review-decision entries" ("Keep and dismissals write no log") |
| Managed task logs are a **closed registry**, duplicated in Rust (`ManagedTaskLogKind {Schedule, Work}`, `MANAGED_TASK_LOG_LABELS`) and in nav (`parseManagedTaskLogParentBullet`: schedule, work, cancel). | A new marker must be registered in both, or other features misread it (see the next row). | bob-cli `src/native/capture/sub_bullet.rs` (~L282–370); nav `010-requires-and-config.js` (~L315–400), `030-bullet-blocks-and-logs.js` (~L120–160); `docs/reference/vault-format.md` ("closed registry") |
| Rust consumers of the registry: the capture insertion anchor (`first_direct_managed_log_start`), task sections, the idle-capture agenda (`AgendaLog` serialized as `"work"`/`"schedule"`), and the note snapshot (`moved N×` chip, condensed `WORKED` row). Nav uses it in project conversion: any direct child that is not a managed log or a section becomes a top-level task. | An unregistered `🥀 **ROTTEN LOG**` would turn into a **task** when the task is converted to a project. That is the one consumer that would actually corrupt data; the others are cosmetic. | `capture_pomodoros_agenda.rs` (~L69–85, ~L907, ~L971); `highlights_ref/note_snapshot/visibility.rs` (~L126, ~L300–370); nav `100-yank-and-paths.js` (~L885–900) |
| The Mac agenda decodes an unknown log kind to `.other(raw)`, so it degrades gracefully. It renders `⚒ N` / `🗓 N` entry-count chips. | Adding `"rotten"` to the agenda JSON is additive, and a matching `🥀 N` chip is a small Swift change. | bob-mac-capture `Sources/CaptureCore/CaptureAgendaModels.swift` (~L384–402), `CaptureAgendaPresentation.swift` (~L940–1035) |
| A machine review journal already exists: `.bob/stats/review/YYYY-MM.<host>.jsonl` records `{day, tier, outcome, key}` for answers on walk landings, with `key = path:line`. | It cannot replace a per-task log: it is invisible in notes, has no reason, and its key changes whenever lines shift. It is useful for sizing the friction. | nav `545-plugin-review-journal.js`; ledger-tools `235-plugin-stats-journal.js` |
| The freshness mark shows the streak as pips, plus a leaf when a decision is due. Its tooltip already has a "Kept N reviews in a row" line. It is computed line-locally from the Tasks cache. | The mark cannot see child bullets in Tasks query results (`rotten.md`, `dash`), so a lifetime count there would need an index. | ledger-tools `130-freshness-marks.js` (~L559–815); `110-freshness-queue.js` |
| Schedule and Cancel Logs use an "opt-in marker" rule: a blank reason writes nothing on a task without a log and `🤷 no reason given` on a task that already keeps one. Work Log blank = nothing. | Bob has two blank-reason conventions already; the Rotten Log needs a deliberate choice (adjustment A2). | `docs/projects.md` "Schedule-log reason prompt", Cancel Log paragraph |

## Live data

From the review journal (2026-10-12 → 10-23, twelve mornings, landed-row answers only,
so these are lower bounds) and a vault grep on 2026-10-23:

| Measure | Value |
| --- | --- |
| ROTTEN + TICKLER answers on landings | 310 (≈26 per morning) |
| …of which **keeps** | **7** (rotten 3, tickler 4), about 2%, or ≈0.6 per morning |
| TICKLER **defers** (priority rolls → Schedule Log) | 240 |
| Next-lane keeps / Pending keeps / NEW keeps | 56 / 7 / 5 |
| Tasks carrying `[keeps:: N]` now | 4 (three at 1, one at 2) |
| `kept N×` decision tails anywhere in the vault | 0 (the decay card has never logged a decision) |
| Existing log markers | Schedule 558 · Work 166 · Cancel 75 |
| `🥀` anywhere in the vault | unused |

What this says:

- **Friction is negligible.** One extra Enter about every other morning.
- **The Rotten Log will be sparse and high-signal.** "Not now" is overwhelmingly
  answered with a roll, and the Schedule Log already records those. The keep is the
  rare answer that leaves no trail today. That is the right gap to fill.
- **"Manually refreshed", read literally, is dominated by lane keeps** (56 Next keeps
  against 7 rotten keeps). Logging every Alt+F would bury the signal. Your trigger
  ("a rotten task") is already the right scope. Only the goal statement needs
  narrowing to match it.

## Critique: is this a good idea?

### What it adds that nothing else records

- **Why a stale task survived.** `[fresh::]` keeps only the last date and `[keeps::]`
  only the current run. Both reset on any other human stamp. Decisions (defer, less
  often, reword, drop) are already logged; the bare keep is not.
- **A deliberate speed bump at the rubber-stamp point.** The tiered-walk decision lists
  "the rubber-stamp risk" as a cost. A one-line "why keep it?" turns the cheapest
  answer into a micro-decision. If no reason comes to mind, that is a hint to defer or
  drop instead.
- **The calibration data the keep-decay record says it lacks.** The record's "Reopens
  when" relies on "a lightweight human tally" of decay-card outcomes. A Rotten Log
  makes that tally a grep: dated, per task, with reasons and `kept N×` tails.

### Where the request as written goes wrong

1. **"Rotten" is ambiguous.** The machine tier `rotten` means age-expired only. The
   bucket `rotten`, `rotten.md`, and the dash ROTTEN chip all include TICKLER. The keep
   streak counts both. If the log fires only on tier `rotten`, a scheduled tickler
   kept four times in a row gets a streak but no log. Bucket semantics fix that (A1).
2. **"Optional entry" fights "how many times".** With Work Log semantics, a blank
   Enter writes nothing. The count then misses exactly the unexplained keeps, and a
   task kept only with blank Enters never shows a log at all. Make the reason
   optional, not the entry (A2).
3. **"Like the Work Log" is the right mechanics but the wrong blank rule and the wrong
   place for the count.** The Work Log is a summary log, where "nothing to say" means
   no entry. The Rotten Log is an event log, closer to the Schedule Log's "a kept
   history has no gaps".
4. **The at-limit keep is missed.** At `[keeps:: 3]`, Alt+F opens the decay card, not a
   stamp, so a prompt wired only into the stamp path would skip the keeps that matter
   most (A3).
5. **A "visual indication" on the task line already exists** (pips) for the streak.
   A second widget for the same concept was rejected last time, and a lifetime count
   cannot be computed in Tasks query results without a new index (A4).

### The strongest objection, and the answer

The keep-streak research rejected "lifetime count + sparse dated REVIEW LOG" because
"it adds structural multi-line writes to a one-key gesture, makes the mark read child
blocks, and needs a new log grammar". All three have weakened or can be avoided:

- **Multi-line writes on Alt+F already ship.** The Pending Work Log prompt does exactly
  this, and the walk follows rows by note and line text, so log inserts never make
  `]s` skip rows (`docs/freshness.md` §6).
- **The mark does not need to read child blocks.** Under this design the pips stay
  line-local. Count chips appear only where children are already parsed (Mac agenda,
  note snapshot), and an optional tooltip line is limited to source-note views.
- **No new grammar.** Entries reuse the Work/Cancel Log shape
  `*YYYY-MM-DD* — <text>` and the decay card's ` · kept N×` tail. Only a marker is new.

The remaining real cost is governance: this reverses part of an accepted record, so it
needs a new record (Bryan asking for it is a legitimate reason to reopen). The other
cost is a second registry entry in two languages.

### Would I take a different approach?

Not fundamentally. I considered and rejected these alternatives (details in the
[table](#alternatives-considered)): logging keeps inside the Schedule Log, extending
the stats journal, a lifetime counter field, and a daily-note keep journal. Each one
loses either the per-task view, the "why", or an invariant another log depends on. The
design I recommend is tighter than the request: one event (the counted keep) drives
both the streak and the log entry.

## Requirement adjustments

Each change to the request as written:

| # | You asked for | I recommend | Why |
| --- | --- | --- | --- |
| **A1** | Prompt when a **rotten** task is refreshed | Prompt when the press is a **counted keep**: exact due Ready row in tier `rotten` **or `tickler`**, excluding `returned_by: unblocked` ticklers. Not NEW, Pending/Next lanes, early (FRESH) confirms, PROJECTS trackers, checklist or recurring rows. | Matches the bucket meaning of "rotten" (`rotten.md`, the dash chip) and the keep streak exactly, so one event both increments `[keeps::]` and writes one entry. Unblock-tickler keeps are already streak-neutral by decision. Lanes are daily and sticky, and Pending already has its Work Log prompt. |
| **A2** | An **optional** entry | **Always write the entry; the reason is optional.** Blank Enter → `*date* — 🤷 no reason given · kept N×`. Escape cancels the whole keep (task stays due, Ctrl+Alt+F does not advance). | Needed for "how many times". Uses the existing `🤷` convention for an unexplained but real event. Escape semantics match the Pending Work Log prompt. |
| **A3** | (implicit) Alt+F / Ctrl+Alt+F stamp path only | Also the **decay card's Keep** (Alt+F inside the card). Keep → the same reason prompt → stamp + log in one transaction. | At-limit keeps are the ones most worth a reason. The card is a key card (L, E, D, 1–4), so the reason cannot be an inline text field without stealing keys; chaining is the honest option. |
| **A4** | A visual indication | (a) The log bullet itself in the source note. (b) The prompt shows the count and the last 2–3 entries. (c) `🥀 N` chip in the Mac agenda and `kept N×` chip in the note snapshot, next to the existing `⚒ N` / `🗓 N` / `moved N×`. (d) *Later, optional:* a mark tooltip line in source-note views. No new on-line mark. | Puts the history where the decision is made. Follows existing count-chip precedents. Keeps "one mark per concept" and avoids an index for Tasks query results. |
| **A5** | (implicit) Count "manual refreshes" | The log counts **rotten keeps** (lifetime); `[keeps::]` stays the **streak**. The log never drives decay, schedule, priority, lane, Today, or freshness. | Keeps `docs/freshness.md` §2a's "no second lifetime counter" rule true as a *field* rule. Decay keeps its fair, resetting signal. |
| **A6** | (implicit) Batches | Counted `N<Alt+F>` and Task Link sessions ask **once**. The reason is shared by every counted target. When Pending targets are also present, the same modal shows a second field (Work summary), as the Schedule review modal already does. At-limit targets still skip. | Mirrors today's shared-summary batch rule. A batch can never bypass the decay card. |
| **A7** | Name "rotten log" | Keep it: `🥀 **ROTTEN LOG**` (U+1F940 WILTED FLOWER, one code point, no VS16, like `❌`). Glossary alias "keep log". | Pairs with `rotten.md` and the rotten bucket. Avoids `🍂`, which already marks decay cancels, and the decision leaf. Unused in the vault today. |
| **A8** | — | **Write a decision record before code**, superseding in part `decisions:rotten-keeps-use-priority-decay` (its "new REVIEW LOG structure" rejection and "Keep anyway leaves only the line increment"). | Records are immutable; the docs and the glossary must not contradict an accepted record. |

## Design

### Trigger rule

Pre-write, for each resolved target:
`match.ok && match.entry.returnedBy !== "unblocked"` (the existing
`matchFreshStampExactEntry`). If any target qualifies, open the prompt before writing.

Post-write, log only the targets whose stamp **actually incremented**: counted, and
`keeps(after) === min(keeps(before) + 1, 999)`, which is the existing
`countFreshStampKept` rule applied per entry. A stale-cache mismatch therefore never
writes an entry without an increment. The tail `kept N×` uses `keeps(after)`.

The decay-card Keep calls `keepLine(..., { counted: true })` and saturates at 999, so
it always increments below the cap, and `kept 4×` on a limit-3 task reads plainly as
"kept past the card".

### Marker, placement, and entry grammar

- **Marker:** `🥀 **ROTTEN LOG**`. The parser also accepts the emoji-less
  `**ROTTEN LOG**` and `**Rotten log**`, like the other logs. A present emoji must
  agree with the label.
- **Placement:** appended as the task's **last direct child** the first time, then
  reused in place and never moved or duplicated (Schedule/Work Log behavior, not the
  Cancel Log's first-child verdict rule). It never displaces the first-child
  Depends-On line.
- **Entries:** newest first, one level under the marker:
  `*YYYY-MM-DD* — <reason> · kept N×`. Blank: `*YYYY-MM-DD* — 🤷 no reason given · kept N×`.
  The reason is whitespace-normalized like a work summary, and the `::` warning
  (Dataview inline field) carries over.
- **Never cleared by automation.** Reword, lane changes, close, and cancel all leave
  it. It travels with the task through Ctrl+Shift+M, `bob task move`, archive, and
  project conversion (the last one requires nav to register the marker).

### Prompt UX

Reuse `FreshnessRefreshSummaryModal` and add a keep-reason mode. Sketch:

```
🥀  Keep task as written                     ROTTEN · 14d · kept 2 in a row
    [ Why keep it as written?  (optional · ↵ logs 🤷)                      ]
    ✓ *2026-10-23* — waiting on legal review · kept 3×
      Prepends under 🥀 ROTTEN LOG · 4th keep logged · next review asks
    Earlier: 10-16 🤷 no reason given · 10-09 still needed before Q4 (+1 older)
    ↵ Keep & log      esc Cancel
```

- Focus is in the field. Ctrl+Alt+F → (type) → ↵ → stamp + log → advance, with one
  composed toast ending `· Rotten Log updated`.
- **History is shown in the prompt** (count plus the newest 2–3 entries), read from the
  note content the handler already holds. This is where a repeated excuse becomes
  visible.
- Decay card → Keep → this prompt with the subtitle "kept 3 reviews in a row". Escape
  closes both and writes nothing (the anchor is kept). The card's own subtitle can
  also show "N keeps logged" (display only).
- Mixed batch (Pending + rotten): two fields. Reason first, then Work summary; Tab
  moves between them; one ↵ submits both.

### What does not change

The `[keeps::]` contract and shared vectors (K1–K13), the decide flag, the decay card's
choices and their Schedule/Cancel Log writers, buckets, tiers, chips, the
`B = NEW ∪ TICKLER ∪ ROTTEN ∪ READY` partition, walk advance and lock rules, Alt+F as
the stay answer, `bob capture` (a generic stamp; it never writes the Rotten Log), and
Rust's no-increment rule.

### Edge cases

- **Same-day repeat Alt+F:** the task is no longer due, so there is no prompt and the
  write is byte-identical.
- **Undo:** in-note keeps are one editor transaction (one Ctrl+Z). Task Link sessions
  write other notes through the existing guarded commit, exactly as the Work Log does.
- **Quote/callout tasks and CRLF:** handled by reusing `insertLaneWorkLogEntry`'s
  marker and indent discovery (generalize it to take a marker kind).
- **Git sync:** multi-line inserts under a task carry the same conflict profile as the
  other logs.
- **Mixed versions:** with an older ledger (no counted keeps) there is no prompt. With
  new nav and older bob-cli, capture inserts children after the log, the agenda shows
  entries as plain children, and the snapshot shows the raw log. All of that is
  cosmetic, so ship bob-cli first anyway.

## Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Rotten Log written only on a nonblank reason (pure Work Log semantics) | Rejected (fallback if you prefer less clutter) | Undercounts exactly the rubber-stamp keeps, and a blank-only task shows no log. |
| Schedule-Log "opt-in marker" blank rule | Rejected | The first unexplained keeps vanish, so the count starts at the first explained one. |
| Put keep entries in the existing Schedule Log | Rejected | Breaks its invariant ("the top entry always answers why the task is scheduled where it is now"). The roll classifier reads any typed or `🤷` entry as `other` and would reset the roll streak on a non-scheduling event. |
| Lifetime counter field (`[refreshes:: N]`, `refresh_count`) | Rejected (again) | Line clutter, no "when/why", contradicts §2a, and the log's entry count already gives the number. |
| Derive `[keeps::]` from the log (like the roll streak from the Schedule Log) | Rejected | Resets come from *other* stamps, which the log does not see. It would also reopen the settled K1–K13 contract. |
| Extend the `.bob/stats/review` journal with reasons | Rejected as the store; fine as a side channel | Hidden from notes; `path:line` keys are unstable; per host. |
| Daily-note "kept today" journal | Rejected | Gives a per-day audit, but you asked for per-task counts. |
| Log every Alt+F ("manually refreshed") | Rejected | Dominated by daily lane keeps (56 vs 7); NEW is triage, not a refresh. |
| New on-line glyph or numeral next to the mark | Rejected | A second widget for one concept; impossible to keep truthful in Tasks results without an index. |
| Lifetime count in the mark via a vault index (like the relation index) | Deferred | Feasible, but heavy for an event that happens about every other day. Reopen if the source-note tooltip proves insufficient. |
| A config switch (`freshness.rotten_log: false`) | Not in v1 | Friction is ~0.6 prompts per morning. Bob has avoided kill switches where a rollback suffices (`answering-advances-the-walk`). |

## Implementation plan and rollout

**Phase 0: governance (no code).**
- New decision record (proposed `decisions:rotten-keeps-are-logged`): the claim is the
  adjustments above, plus rejected alternatives, cost, and reopen conditions. Mark
  `rotten-keeps-use-priority-decay` superseded in part. Use `/sase_memory_write` for
  the record and the glossary strand.
- New glossary strand `rotten-log` (text below). Cross-link it from `keep-streak`,
  `work-log`, and `task-freshness`.
- Docs: `docs/freshness.md` §2a (clarify that the log is not a counter field), §5
  (prompt), §6 (ritual step), §14 (rollout); `docs/projects.md` (Keep now writes a
  Rotten Log entry); `docs/reference/vault-format.md` (closed registry);
  `docs/reference/glossary.md`; the nav plugin reference in bob-plugins `docs/`.

**Phase 1: bob-cli registry (daily train, additive, no `!`).**
- `src/native/capture/sub_bullet.rs`: `ManagedTaskLogKind::Rotten`, `ROTTEN_LOG_EMOJI`,
  labels `ROTTEN LOG` / `Rotten log`. Update the match arms in
  `capture_pomodoros_agenda.rs` (`AgendaLog::Rotten` → `"rotten"`) and
  `highlights_ref/note_snapshot/{visibility,transclusion}.rs` (`kept N×` chip; full
  `KEPT` rows when `include_closed`).
- Tests: the marker table in `capture/tests/assembly.rs`, agenda tagging, snapshot
  chips, and the section exclusion in `capture_task_sections.rs`.

**Phase 2: bob-plugins (nav; one release, so writer and parser land together).**
- `010-requires-and-config.js` / `030-bullet-blocks-and-logs.js`: marker constants and
  `parseManagedTaskLogParentBullet` kind `rotten`.
- `100-yank-and-paths.js` (project conversion): carry the Rotten Log as a managed log
  under `^prj`, never as a task.
- `220-property-targets.js`: generalize `insertLaneWorkLogEntry` to take a marker kind
  and an entry formatter.
- `480-review-jump-and-nav-api.js`: extend `planFreshStampBatchWithWorkLogs` to write
  Rotten Log entries for the entries that actually incremented.
- `190-summary-modals.js`, `520-…`, `530-…`: keep-reason mode, history panel,
  two-field batch, and the `· Rotten Log updated` notice tail.
- `540-…` `applyFreshnessDecayCardKeep`: prompt, then a multi-line transaction instead
  of `replaceEditorLine`; add the "N keeps logged" subtitle to the card.
- Then extend the existing `scripts/test-navigation-*.cjs` suites, run
  `npm run build` and `npm test`, bump the version, and run `bob plugins sync`.

**Phase 3: optional surfaces.**
- bob-mac-capture: `CaptureAgendaLog.rotten`, a `🥀 Rotten log` header, a `🥀 N` chip,
  and an accessibility label. Unknown kinds already decode safely, so this can lag.
- ledger-tools: a tooltip line `🥀 Rotten Log · N keeps since <date>` in Live Preview
  and Reading view of the source note only. It must stay neutral elsewhere so mark
  consensus holds.
- `bob freshness list -f json`: an additive per-row `rotten_log {entries, last}`, if
  headless review needs it.

**Order:** Phase 0 → Phase 1 installed → Phase 2. Phase 3 can come at any time.

## Open questions for Bryan

1. **TICKLER keeps:** include scheduled-tickler keeps (recommended) and exclude
   unblock-tickler keeps (recommended)?
2. **Blank Enter:** always log `🤷` (recommended), or Work-Log style "blank writes
   nothing"?
3. **Tail:** keep ` · kept N×` on each entry (recommended; it shows runs and
   card overrides), or date + reason only?
4. **Name/emoji:** `🥀 **ROTTEN LOG**` (recommended) or `KEEP LOG`?
5. **Phase 3:** which surfaces do you actually look at: the Mac agenda chip, the mark
   tooltip, or JSON?

## Recommended solution

Build a **Rotten Log written by the counted keep itself**:

1. **One event, two records.** Every Alt+F / Ctrl+Alt+F (or decay-card Keep) that
   increments `[keeps:: N]` on an exact due Ready ROTTEN/TICKLER row (not an unblock
   tickler) first asks "Why keep it as written?" and then, in the same transaction,
   stamps, increments, and prepends one entry under `🥀 **ROTTEN LOG**`.
2. **Always an entry, optionally a reason.** Blank ↵ logs `🤷 no reason given`; Esc
   writes nothing and leaves the task due. Entries read
   `*YYYY-MM-DD* — <reason> · kept N×`, newest first, and are never cleared by
   automation.
3. **Visibility where it pays off.** The prompt shows the count and the latest entries.
   The log sits under the task in the note. The Mac agenda and note snapshot add count
   chips beside the existing log chips. Pips remain the only on-line mark.
4. **Nothing else moves.** Streak semantics, decay, buckets, tiers, the walk, the
   Schedule/Cancel/Work Logs, and `bob capture` are unchanged. The log is display and
   audit only.
5. **Ship in order:** decision record, glossary, and docs → bob-cli marker registry →
   nav writer, parser, and project-conversion fix in one plugin release → optional
   surfaces.

## Proposed glossary entry

### Rotten Log {#rotten-log}

aka keep log

A task-local, newest-first history of the times a stale task was kept as written,
stored as a `🥀 **ROTTEN LOG**` direct child with dated entry sub-bullets
(`*YYYY-MM-DD* — <reason> · kept N×`). An entry is written by exactly the Alt+F /
Ctrl+Alt+F keep that increments the [[keep-streak]]: an exact due Ready ROTTEN or
TICKLER row (never an unblock tickler), including Keep on the approved-decay card.
Before the write, an optional "why keep it?" prompt appears. A blank reason still logs
`🤷 no reason given`, and Escape cancels the keep. The entry count is the task's
lifetime number of rotten keeps. Unlike `[keeps:: N]` it never resets, and it never
changes decay, schedule, priority, lane, Today, or freshness. NEW, Pending/Next lane,
early, and PROJECTS keeps never write it. Pending summaries stay in the [[work-log]],
and deferrals, Less often, and Reword stay in the [[schedule-log]]. See
[[task-freshness]].

## Sources

- **Memory (audited reads):** glossary `work-log`, `keep-streak`, `task-freshness`,
  `schedule-log`, `morning-gtd-review-footer`; decisions
  `rotten-keeps-use-priority-decay`, `decay-decisions-are-available-immediately`,
  `ready-is-freshness-gated`, `review-walk-is-tiered`, `answering-advances-the-walk`,
  `unblocked-tasks-resurface-as-ticklers`; reference notes `obsidian.md`, `docs.md`.
- **Prior research (artifact read):**
  `research:202610/rotten_keep_streak_and_approved_decay/rotten_keep_streak_and_approved_decay.md`
  (the A8 "no lifetime history" adjustment; the REVIEW LOG alternative it rejected).
- **bob-cli:** `docs/freshness.md` §§2a/5/6; `docs/projects.md` (Schedule-log
  reason prompt, Cancel Log, approved-decay entries);
  `docs/reference/vault-format.md`; `src/native/capture/sub_bullet.rs`;
  `src/native/capture_pomodoros_agenda.rs`;
  `src/native/highlights_ref/note_snapshot/{visibility,transclusion}.rs`;
  `src/native/capture_task_sections.rs`.
- **bob-plugins (nav 2.50.4, ledger-tools 1.63.3):** nav `src/010`, `030`, `060`, `100`,
  `190`, `220`, `480`, `490`, `520`, `530`, `540`, `545`; ledger-tools `src/080`,
  `110`, `130`, `235`.
- **bob-mac-capture:** `Sources/CaptureCore/CaptureAgendaModels.swift`,
  `CaptureAgendaPresentation.swift`.
- **Vault data (read-only):** `.bob/stats/review/2026-10.*.jsonl`; greps for
  `[keeps::]`, log markers, `kept N×`, and `🥀`.

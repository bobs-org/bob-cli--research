# Rotten Log: a task-local history of rotten keeps

> **Research query:** Add a "rotten log" (with a good glossary entry) that works like
> the Work Log, but whose optional entry prompt appears when a rotten task is refreshed
> with `<alt+f>` or `<ctrl+alt+f>` (during the GTD morning review, for example). The
> goal is a visual indication and an audit trail of how many times, when, and why a
> task was manually refreshed. Critique the plan, call out justified requirement
> changes, and end with a recommended solution.

**Consolidated report.** 2026-10-23. Lead-researcher merge of the five swarm reports in
this directory (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`). I re-checked their
disputed claims against bob-cli `f2c24531`, bob-plugins `477af35`, audited memory, and
the vault's review journal. No product code, memory note, or vault file was changed.

## Bottom line

**Build it. Keep the name "Rotten Log". Make "refresh" mean one specific event.**

A bare keep is the only review answer that leaves no written trail. Defer, Less often,
and Reword write Schedule Log entries, and Drop writes a Cancel Log entry. The keep
only rewrites the task line. `[keeps:: N]` remembers the current run and forgets it on
the next generic stamp. The decay card's Keep rewrites one line and logs nothing
(`docs/projects.md`: "Keep and dismissals write no log"). A Work-Log-shaped child
under the task fills exactly that gap. Bob already ships a nearly identical flow:
Alt+F on a Pending task asks for an optional Work Log summary, then writes the stamp
and the entry in one transaction.

All five reports say build it. They split on five design questions. The resolutions
below become the requirement changes in §3:

1. **A "refresh" is a counted keep.** That is Alt+F / Ctrl+Alt+F on an exact due
   Ready ROTTEN or *scheduled* TICKLER row, which are the rows `rotten.md` and the
   dashboard ROTTEN chip already call rotten. The decay card's **Keep** also counts.
   A plain Alt+F anywhere else does not.
2. **The reason is optional; the entry is not.** A blank Enter logs
   `🤷 no reason given`, and Escape cancels the keep. This is a deliberate departure
   from the Work Log's blank rule, because "how many times" needs every keep.
3. **The log holds the count.** No new task-line field and no second on-line widget.
   `[keeps:: N]` stays the streak, and its pips stay the only mark on the line.
4. **History appears where the decision is made.** The prompt shows the logged
   count and the latest reasons. The review walk lands in the source note, so the log
   is also visible right under the task.
5. **Governance comes first.** An accepted decision record explicitly rejected "a new
   REVIEW LOG structure", so this needs a new record that supersedes it in part.

Measured prompt load is about **0.6 per morning** (§1.1), so the "review velocity
collapse" two reports feared does not apply. The real cost is the closed managed-log
registry in two languages. One unregistered consumer corrupts data: project conversion
would turn an unknown marker into a **task** (§1.2, row 7).

## 1. Evidence

### 1.1 What the vault says about frequency

Source: `.bob/stats/review/2026-10.*.jsonl`, 12 mornings (2026-10-12 → 10-23), plus a
read-only grep of the vault. The journal only records answers given on walk landings,
so these numbers are lower bounds.

| Measure | Value |
| --- | --- |
| ROTTEN-tier answers | 17: defer 6, drop 3, keep 3, today 3, done 2 |
| TICKLER-tier answers | 293: defer 240, done 27, drop 12, today 5, **keep 4**, other 5 (one was a decay card) |
| **Counted-keep candidates** (rotten + tickler keeps) | **7**, about 0.6 per morning, never more than 2 in a day |
| …of which landed on `#ref` reading tasks | **5 of 7** |
| Next-lane keeps / Pending keeps / NEW keeps | 56 / 7 / 5 |
| Open tasks with `[keeps:: N]` now | 4 (three at 1, one at 2) |
| Existing log markers | Schedule 558 · Work 166 · Cancel 75 |
| Candidate glyphs | `🥀` unused in the vault and plugin source. `🍂` already marks decay cancels and drops (`PRIORITY_DECAY_CANCEL_EMOJI`). `⟳` is the freshness footer/queue glyph. `↻` is the recurring count in Ready notes. |

What this settles:

- **Prompt fatigue is not a reason to gate the prompt.** gem's estimate of "15–30
  modals per morning" read `refreshed_today: 41` as rotten keeps. That figure counts
  every stamp, including lane and NEW answers. grk's "about six per day" is a ceiling
  that assumes every due Ready row gets kept. In practice you defer about 35 times
  more often than you keep (246 vs 7).
- **The log will be sparse and high-signal.** Defers already reach the Schedule Log.
  The keep is the rare answer with no trail.
- **"Manually refreshed", taken literally, would be dominated by Next-lane keeps**
  (56 vs 7). The trigger you named ("a rotten task") is the right scope. Only the
  goal sentence needs narrowing.
- **New finding: most keeps are on reading tasks.** Expect reasons like "still the
  primer for the memory epic". References follow ordinary freshness rules
  (`docs/freshness.md` "Reference conformance"), so they qualify without special
  cases. `bob ref` task migration copies child blocks, so the log moves with the
  task.

### 1.2 Verified system facts

| # | Fact | Consequence | Evidence |
| --- | --- | --- | --- |
| 1 | Alt+F / Ctrl+Alt+F on a Pending `[/]` target opens `FreshnessRefreshSummaryModal`. Blank Enter refreshes with no entry; Escape cancels and Ctrl+Alt+F does not advance. Batches share one summary. `planFreshStampBatchWithWorkLogs` stamps, then prepends entries bottom-up in one editor transaction. | Reuse the modal, planner, and batch plumbing. Only the copy and the blank rule differ. | nav `190-summary-modals.js`, `480-review-jump-and-nav-api.js:606`, `520-…:394/669`; `docs/freshness.md` §5 |
| 2 | A keep counts only on an exact pre-write queue match with `lane === 'ready'` and tier `rotten`/`tickler`. `api.freshness.keepLine` is the only helper that increments. A keep on an unblock tickler leaves the streak unchanged. | The trigger predicate already exists (`matchFreshStampExactEntry`). | `docs/freshness.md` §2a; nav `480-…:807` |
| 3 | Bucket `rotten` contains every tickler. The dashboard ROTTEN chip folds TICKLER and ROTTEN together, and `rotten.md` has both groups. | In your UI vocabulary, a "rotten task" includes ticklers. | `docs/freshness.md` (~L458, L501, L834) |
| 4 | The decay card's Keep (`applyFreshnessDecayCardKeep`) is a single `replaceEditorLine`. The card is a single-key card (Enter, L, E, D/X, ⌥F). | Keep must become a multi-line transaction. A reason cannot be typed inline without stealing keys, so it needs a chained stage. | nav `540-plugin-decay-picker-and-cancel.js:204–238`, `060-decay-card-modal.js` |
| 5 | When the card cannot render, the source-note path falls back to plain `planFreshStampBatch`. | A second write path that would skip the log unless rerouted. | nav `520-…` fallback branch (cdx, confirmed) |
| 6 | Managed logs are a closed registry. Rust has `ManagedTaskLogKind {Schedule, Work}` with exhaustive matches in `capture_pomodoros_agenda.rs` (`AgendaLog` → `"work"`/`"schedule"`), `capture_work_log.rs`, and the note-snapshot `transclusion.rs`/`visibility.rs`. JS has `parseManagedTaskLogParentBullet` (schedule, work, cancel). | A new kind is a cross-engine change, and the compiler flags each Rust consumer. | bob-cli `src/native/capture/sub_bullet.rs:292`; nav `030-bullet-blocks-and-logs.js:121` |
| 7 | On project conversion, a direct child becomes a top-level task unless it is a registered managed log or an ALL-CAPS section. `🥀 **ROTTEN LOG**` fails `PROJECT_SECTION_TITLE_RE`. | **An unregistered marker would become a task.** Registration is a correctness requirement, not polish. | nav `110-project-seed.js:162`, `010-requires-and-config.js:116` |
| 8 | The freshness mark is computed from the task line alone (Tasks cache). It cannot see child bullets in query results (`rotten.md`, dash). | A lifetime count cannot be shown truthfully on the mark in query views without a new index. | ledger-tools `130-freshness-marks.js` (cld) |
| 9 | The walk lands on the task row in its source note and follows note path plus line text. Child inserts below the row never make `]s` skip. | The log is visible under the task during review. Ctrl+Alt+F can advance after an insert. | `docs/freshness.md` §6 |
| 10 | `decisions:rotten-keeps-use-priority-decay` rejects "a new REVIEW LOG structure… Keep anyway leaves only the line increment" and "a second alias counter". §2a says "Do not introduce a second lifetime counter or alias". The prior final rejected the review log **for v1** because it added multi-line writes to a one-key gesture, made the mark read child blocks, and needed new grammar. | Needs a new record. Each of those objections has weakened (§2.1). | audited memory; `research:202610/rotten_keep_streak_and_approved_decay/…__final.md` |

## 2. Critique

### 2.1 Is this a good idea? Yes.

- **It fills the one answer with no trail.** Today the vault cannot tell you why a
  stale task survived three reviews. A dated reason next to the task can.
- **It survives streak resets.** `[keeps::]` clears on any other human stamp. The log
  keeps the full history.
- **It adds a small speed bump at the rubber-stamp point.** The tiered-walk record
  names the rubber-stamp risk as a cost. If no reason comes to mind, that is a hint to
  defer or drop. Alt+P (one-key recommended roll, epic `bob-cli-aq`, in progress) will
  make deferring one key while a logged keep costs two. That nudges toward a decision,
  which is the intended direction.
- **It supplies the calibration data the keep-decay record says it lacks.** That
  record reopens on "a lightweight human tally" of card outcomes. With dated `kept N×`
  entries, the tally becomes a grep.
- **The prior objections no longer bind.** Alt+F already does multi-line writes for
  Pending tasks. Under this design the mark stays line-local. Only the marker is new;
  entries reuse the Work/Cancel shape `*YYYY-MM-DD* — text`.

### 2.2 Where the request as written goes wrong

1. **"Manually refreshed" is too broad.** Logging every Alt+F would bury 7 rotten
   keeps under 56 Next keeps, plus NEW triage and early confirms.
2. **"Rotten" is ambiguous.** The machine tier `rotten` means expired by age only.
   Your bucket, `rotten.md`, the chip, and the keep streak all include ticklers. With
   tier-only wiring, 4 of the 7 observed keeps would be missed, and a repeatedly kept
   scheduled tickler would gain a streak but no log.
3. **An "optional entry" contradicts "how many times".** With Work Log semantics a
   blank Enter writes nothing, so the count misses exactly the unexplained keeps.
4. **Wiring only the stamp path misses the most important keep.** At the limit,
   Alt+F opens the decay card, and its Keep (plus the card-unavailable fallback)
   bypasses the stamp-and-log planner.
5. **The task line already shows the streak.** A second on-line widget was rejected
   last time, and it could not be truthful in Tasks query views (fact 8).

### 2.3 Real costs

- **Registry surface.** Rust plus three or four plugin parsers, MC vectors, snapshot
  code, and four doc pages. This is most of the work.
- **Two numbers.** The streak resets; the log count only grows from rollout. Always
  label them differently: "kept N in a row" vs "N keeps logged". Never add them.
- **Growth.** A reading task kept weekly gains about four lines a month. Folding and
  snapshot condensing contain it, and the decay card asks a question every third
  consecutive keep.
- **No backfill.** On rollout day, `keeps:: 2` with an empty log is expected, not a
  bug.
- **Editable, not tamper-proof.** It is Markdown that you can edit, undo, or lose in
  a sync conflict. The count describes retained entries.
- **Concurrent work.** `bob-cli-aq` is changing the same navigation landing code
  (`520`/`530`) right now. Start the plugin phase after it lands.

## 3. Requirement adjustments

| # | You asked for | Adjusted requirement | Why |
| --- | --- | --- | --- |
| **R1** | Prompt when a **rotten** task is refreshed | Prompt on a **counted keep**: an exact due Ready row in tier `rotten` or `tickler`, excluding unblock ticklers (`returned_by: unblocked`). This applies from any Alt+F / Ctrl+Alt+F route (single, counted `N<Alt+F>`, Task Link), inside or outside the walk. NEW, early/FRESH, Pending (keeps its Work Log prompt), Next, PROJECTS, recurring, checklist, and closed rows do not prompt. | One event drives both the streak increment and one entry. Matches what your UI already calls rotten. Unblock-tickler keeps are streak-neutral by decision. |
| **R2** | (implicit) the stamp path only | Also the **decay card's Keep** (⌥F): Keep → reason stage in the same modal shell → stamp, increment, and entry in one transaction. The other card outcomes keep their existing Schedule/Cancel entries and write no Rotten Log entry. | The at-limit keep is the one most worth a reason. Mirroring the other outcomes would double-log them. |
| **R3** | An **optional** entry, like the Work Log | **Always an entry, optionally a reason.** Blank Enter writes `*date* — 🤷 no reason given · kept N×`. Escape writes nothing: no stamp, no entry, no advance. | Needed for "how many times". Uses Bob's existing `🤷` convention for a real but unexplained event. The Escape behavior matches the Pending prompt. |
| **R4** | (implicit) prompt every time | Keep it: prompt on **every** counted keep, with no keep-2 gate. | About 0.6 prompts per morning. Revisit only with evidence, and the log itself is the evidence: if a month of entries is more than 80% `🤷`, or keeps exceed about 5 per morning, consider grk's and gem's from-the-second-keep gate. |
| **R5** | A count of manual refreshes | The count is the **number of log entries** (lifetime since rollout). No new field. `[keeps::]` stays the streak. Nothing reads the log to change decay, buckets, tiers, lanes, Today, schedule, priority, or freshness. | Keeps §2a's no-second-counter-field rule true. Decay keeps its fair, resetting signal. |
| **R6** | A visual indication | v1 shows the log in the note, history in the prompt, and "N keeps logged · last: …" on the decay card. No new glyph or numeral on the task line. Later and optional: a tooltip line in source-note views, a `🥀 N` chip in the Mac agenda, a snapshot chip. | Puts the history where the decision is made. Follows the existing count-chip precedents. Avoids an index for query views. |
| **R7** | Name "rotten log" | Keep it, with the marker `🥀 **ROTTEN LOG**` and the alias "keep log". | It is your term and pairs with `rotten.md`. `🥀` is unused, while `🍂` and `⟳` already mean something. |
| **R8** | — | **A decision record before code**, superseding in part `rotten-keeps-use-priority-decay`. | Records are immutable, and docs and the glossary must not contradict an accepted record. |

## 4. Where the reports disagreed

| Question | cdx | cld | grk | mus | gem | **Resolution** |
| --- | --- | --- | --- | --- | --- | --- |
| Name / marker | `♻️ ROTTEN LOG` | `🥀 ROTTEN LOG` | `⟳ KEEP LOG` | `🥀 ROTTEN LOG` | `🍂 ROTTEN LOG` | **`🥀 ROTTEN LOG`.** The only candidate glyph with no existing meaning. grk's "it is FRESH after the keep" would equally rename the Work Log; the log records past rot events. |
| Scope | ROTTEN tier only | counted (rotten + tickler, no unblock) | counted | rotten + tickler | ROTTEN only, excludes TICKLER | **Counted keeps.** Tier-only misses 4 of 7 observed keeps and disagrees with the streak. |
| Blank Enter | always `🤷` | always `🤷` | nothing until a log exists, then `🤷` | nothing | nothing | **Always `🤷`.** grk's hybrid drops the first unexplained keeps, so the count would start late (the Schedule Log opt-in problem). The bloat concern assumed a frequency the data refutes. |
| Prompt gate | every keep | every keep | from the 2nd keep | every keep | from the 2nd keep, or Alt+F only | **Every keep.** The gate was sized against a misread rate. Gating plus always-write would also mean writing "no reason given" without asking. |
| Decay card Keep | logs, reason in a card stage | logs, chained prompt | machine line, only if a log exists | excluded | prompt and append | **Logs, via a chained reason stage.** mus assumed card outcomes already log; Keep does not. |
| Other card outcomes | their own logs | their own logs | also mirrored into the Keep Log | their own logs | their own logs | **Their own logs only.** |
| Count display | `↻ N` by the mark + tooltip | prompt history + agenda/snapshot chips | pips + optional tooltip | `· logged` notice | tooltip with last reason | **Prompt history + card subtitle**; tooltip and chips later. `↻` already means recurring, and a numeral by the mark was rejected before. |
| `· kept N×` tail | no (`Kept —` prefix) | yes | machine lines only | no | no | **Yes.** It costs nothing, matches the decay-card tails, and shows where streaks reset. Optional (Q4). |
| Decision record | supersede in part | supersede in part | "does not supersede" | amend | — | **Supersede in part.** The record names the REVIEW LOG rejection and the line-only Keep explicitly. |
| Placement | last child | last child | last child | after Schedule/Work | before the Work Log | **Appended last on creation, never moved.** Existing managed lines are never reordered. |

## 5. Recommended design

### 5.1 Event rule

Before writing, for each resolved target: `matchFreshStampExactEntry(...)` is `ok`,
`entry.returnedBy !== "unblocked"`, and no decision is required. Write an entry if and
only if the combined write commits.

- Do not key on a numeric increment, since the streak saturates at 999.
- Do not key on a bucket label, a file name, or the presence of `[keeps::]`.
- A same-day repeat is no longer due, so there is no prompt and the write is
  byte-identical.
- If queue and source disagree after the prompt, refuse with a retry notice. Never log
  a guessed keep.

### 5.2 Storage grammar

```markdown
- [ ] #task Read "Agentic software engineering" #ref [fresh:: 2026-10-23] [refresh:: 7] [keeps:: 3] ^ref-ase
	- 🥀 **ROTTEN LOG**
		- *2026-10-23* — still the primer for the memory epic; read it this weekend · kept 3×
		- *2026-10-16* — 🤷 no reason given · kept 2×
		- *2026-10-09* — waiting for the weekend reading block · kept 1×
```

- **Marker.** `🥀 **ROTTEN LOG**` (U+1F940, one code point, no VS16). The parser also
  accepts emoji-less `**ROTTEN LOG**` / `**Rotten log**`. As with the other logs, a
  present emoji must agree with the label.
- **Entry.** `*YYYY-MM-DD* — <reason> · kept N×`, newest first, where N is the streak
  after the write. Normalize whitespace like a work summary, keep the `::`
  inline-field warning, and record the actual local review date.
- **Placement.** Appended as the task's last direct child the first time, then reused
  in place. Never moved or duplicated, and never displaces the Depends-On line or a
  first-child Cancel Log.
- **Lifetime.** Automation never clears it. It travels with the block through
  Ctrl+Shift+M, `bob task move`, archive, ref migration, and project conversion (once
  registered).
- **Counting.** Count only valid dated direct children of one marker. With duplicate or
  ambiguous markers, writers refuse with a notice and readers report no count rather
  than a wrong one.

### 5.3 Prompt

Add a keep-reason mode to `FreshnessRefreshSummaryModal`. Do not build a new modal
family.

```text
🥀  Keep as written?               TICKLER · 9d · kept 2 in a row · 3 logged
    [ Why keep it as written?  (optional · ↵ logs 🤷)                    ]
    ✓ *2026-10-23* — <your text> · kept 3×
    Earlier: 10-16 🤷 no reason given · 10-09 waiting for the weekend block
    ↵ Keep & log      esc Cancel
```

- Focus starts in the field. Ctrl+Alt+F → type → Enter writes, then advances exactly
  once through the existing advance tail and gesture lock.
- History comes from note content the handler already holds; no extra read.
- Use neutral copy ("Why keep it as written?"), not "why haven't you done this?".
  Do not prefill the previous reason.
- The notice gains the tail `· Rotten Log updated`.

### 5.4 Decay card

1. An at-limit single press opens the card first, as today. No Rotten Log prompt
   appears in front of a card that might defer or drop.
2. ⌥F **Keep** opens the same reason stage, subtitled "kept 3 reviews in a row".
   Enter commits stamp, increment, and entry together. Escape writes nothing and
   keeps the walk anchor.
3. Not now, Less often, Reword, and Drop are unchanged. They write their existing
   Schedule/Cancel entries and no Rotten Log entry.
4. The card subtitle shows "N keeps logged · last: <reason>" (display only).
5. The card-unavailable fallback goes through the same combined planner.

### 5.5 Batches

- Counted `N<Alt+F>` and Task Link sessions open **one** modal. It shows a Keep
  reason field when counted keep targets are present and a Work summary field when
  Pending targets are present. Tab moves between the fields, and one Enter submits.
- The shared reason gives each counted target its own entry with its own `kept N×`.
  A work summary never goes into a Rotten Log, and a reason never goes into a Work
  Log.
- At-limit targets still skip ("N needs a decision"), unstamped and unlogged.
- Deduplicate several links that point at the same source task before planning.

### 5.6 Write safety

- Plan the stamp and the entry as one postimage: one editor transaction, one undo.
- Capture the preimage, local day, and eligibility before the async prompt. After it,
  revalidate them, because a tab switch, midnight rollover, concurrent edit, or stale
  cache must not attach a reason to the wrong row.
- If the entry cannot be planned, refuse the keep. Never write a stamp without its
  entry.
- Linked files go through the existing grouped commit with preimage checks. Do not
  claim atomicity across notes.
- Keep child writes out of `keepLine`, which is a pure single-line helper shared with
  the counting vectors.
- Inserts land below the answered row, so the known bug class `bob-cli-94` (a BLOCKS
  insert above the row shifts the settle index) does not apply. Still cover
  Ctrl+Alt+F after an insert in the advance tests.

### 5.7 What does not change

The `[keeps::]` contract and its shared vectors, the decide flag, the card's choices
and writers, buckets, tiers, chips, the `NEW ∪ TICKLER ∪ ROTTEN ∪ READY` partition,
walk advance and lock rules, Alt+F as the one stay answer, `bob capture` (a generic
stamp that never writes this log), Rust's no-increment rule, and the Mac thin-client
contract.

## 6. Implementation map

**Phase 0: governance.** Memory edits go through `/sase_memory_write`; docs follow the
`docs.md` routing.

- New record, proposed `decisions:rotten-keeps-are-logged`, superseding in part
  `rotten-keeps-use-priority-decay`: the REVIEW LOG rejection and "Keep anyway leaves
  only the line increment". It must state that the log count is display-only history:
  never a counter field, never read by decay, no backfill.
- Glossary strand `rotten-log` (§8), cross-linked from `keep-streak`, `work-log`, and
  `task-freshness`, and mirrored in `docs/reference/glossary.md`.
- Docs: `docs/freshness.md` §2a (the log is not a counter field), §5 (prompt), and §6
  (ritual); `docs/projects.md` (Keep now logs; the line "Keep and dismissals write no
  log"); `docs/reference/vault-format.md` and `docs/task-dependencies.md` §2.4/§11.8
  (closed registry, recognisers, MC vectors); the plugin hotkey reference. Run
  `just docs-check`.

**Phase 1: bob-cli registry.** Additive, rides the daily train, and does not touch
`Cargo.toml` or `CHANGELOG.md`.

- `src/native/capture/sub_bullet.rs`: add `ROTTEN_LOG_EMOJI`, the labels, and
  `ManagedTaskLogKind::Rotten`, plus vectors in `capture/tests/assembly.rs`.
- Resolve every exhaustive match:
  - `capture_pomodoros_agenda.rs`: map `AgendaLog::Rotten` to `"rotten"`. This is
    additive JSON; per cld the Mac client decodes unknown kinds to `.other`.
  - `capture_work_log.rs`.
  - Note snapshot `transclusion.rs` and `visibility.rs`: a `kept N×` chip and a
    condensed row.
  - `capture_task_sections.rs` exclusion.
- Every recogniser listed in the registry must reject the new marker.

**Phase 2: bob-plugins.** One release, so parsers and writer ship together. Start after
`bob-cli-aq` lands.

- nav `010`/`030`: constants and `parseManagedTaskLogParentBullet` kind `rotten`.
- nav `110-project-seed.js` and project conversion: carry the log under `^prj`, never
  as a task. This fixes fact 7.
- nav `220`: generalize `insertLaneWorkLogEntry` to take a kind and an entry
  formatter.
- nav `480`: generalize `planFreshStampBatchWithWorkLogs` into a planner that takes
  typed Work Log and Rotten Log inputs.
- nav `190`/`520`/`530`: keep-reason mode, history panel, two-field batch, notice
  tail, and rerouting the card-unavailable fallback.
- nav `540` (`applyFreshnessDecayCardKeep`) and `060`: the reason stage, the combined
  transaction, and the card subtitle.
- block-id-prompt, task-status-cycler, and ledger-tools scanners: parser copies, so
  none of them reads the marker as user prose or a Task Link.
- Then run `npm run build` and `npm test`, bump versions, and run `bob plugins sync`.
- Baseline: cdx ran the relevant suites and saw 238 of 239 pass. The one failure (a
  notice assertion in the 999-saturation test) predates this work and is tracked as
  `bob-cli-6w`.

**Phase 3: optional surfaces.** Ship any of these whenever you want them.

- ledger-tools tooltip line in source-note views: `🥀 3 keeps logged · last 10-23: …`.
- bob-mac-capture `🥀 N` agenda chip.
- `bob freshness list -f json` per-row `rotten_log {entries, last}` (a schema bump).

**Tests that separate the semantics** (merged from cdx, cld, grk):

1. A reason writes one entry. A blank still writes `🤷`. Escape leaves the document and
   walk untouched. A same-day repeat or double submit writes nothing new.
2. Eligibility: rotten and scheduled tickler log. Unblock tickler, NEW, Pending, Next,
   PROJECTS, recurring, checklist, and early-confirm rows do not. A reference task that
   evaluates ROTTEN does. A saturated streak still logs.
3. At-limit card: opening or cancelling writes nothing, Keep logs once, other outcomes
   write only their own logs, and the fallback cannot bypass the planner.
4. Batches: mixed Pending and rotten fields, Task Link dedup, skipped decision rows,
   and honest partial failure without duplicate entries on retry.
5. Grammar: parent ownership, nested tasks, log-like prose, CRLF, missing final newline,
   duplicate markers, and quote/callout tasks.
6. Prompt-time races: a document or day change causes no stale commit. One undo
   restores the line, streak, and log. Ctrl+Alt+F after an insert lands on the right
   successor.
7. Survival: the log remains after a generic stamp clears `keeps`. Project conversion
   keeps it as a log, not a task.
8. Live Obsidian check, which Node stubs cannot cover: focus, IME, Enter/Escape,
   folding, and navigation after inserts.

## 7. Alternatives considered

| Alternative | Verdict | Why |
| --- | --- | --- |
| Nonblank-only entries (pure Work Log semantics) | Rejected; fallback if you prefer less text | Undercounts exactly the rubber-stamp keeps. If chosen, the UI must say "explained keeps", not "keeps". |
| Schedule Log opt-in blank rule (`🤷` only once a log exists) | Rejected | The first unexplained keeps vanish, so the count starts late. |
| Prompt only from the second keep (grk, gem) | Deferred | Sized against a misread rate. Revisit with the log's own `🤷` rate as evidence. |
| Ctrl+Alt+F silent, Alt+F prompts (gem) | Rejected | Splits one answer into two semantics and breaks "advance = the same answer, then move". |
| Put keep entries in the Schedule Log | Rejected | Breaks "the top entry explains the current schedule", and the roll classifier would read a keep as `other` and reset the roll streak. |
| Put keep entries in the Work Log | Rejected | Mixes "what I did" with "why it still matters" and pollutes work counts and Pomodoro copies. |
| Lifetime `[refreshes:: N]` field | Rejected again | No when or why, adds clutter to the line, and contradicts §2a. The entry count already gives the number. |
| Derive `[keeps::]` from the log | Rejected | Resets come from other stamps the log never sees, and it would reopen the settled vectors. |
| Review journal (`.bob/stats/review`) as the store | Rejected as the store | Invisible in notes, no reasons, unstable `path:line` keys, one file per host. Still useful for sizing. |
| Log every Alt+F ("Refresh Log") | Rejected | Dominated by lane keeps (56 vs 7). Needs a taxonomy for many writers. |
| Prompt only at the decay card | Rejected as the default | Misses the keeps before the limit, and it is not what you asked for. |
| Numeral or glyph by the freshness mark (cdx `↻ N`) | Rejected for v1 | `↻` already means recurring, it would be a second widget for one concept, and it cannot be truthful in query views without an index. |
| `freshness.rotten_log: false` switch | Not in v1 | Rollback is enough at about 0.6 prompts per morning. |

## 8. Proposed glossary entry

Publish it in Phase 0 through `/sase_memory_write` as `sase/memory/glossary/rotten-log.md`,
mirror it in `docs/reference/glossary.md`, and create the decision record first so the
link resolves.

```markdown
# Rotten Log

*Requested · project*

aka keep log, rotten keep history

A task-local history of the times a due Ready task was kept as written, stored as a
`🥀 **ROTTEN LOG**` direct child with newest-first `*YYYY-MM-DD* — <reason> · kept N×`
sub-bullets. Alt+F or Ctrl+Alt+F on an exact due Ready ROTTEN or scheduled TICKLER row
(the same keep that increments the [[keep-streak]]) and Keep on the approved-decay card
first ask an optional "why keep it?" reason; a blank reason still records
`🤷 no reason given`, and Escape cancels the keep. The entry count is the number of
rotten keeps logged since rollout: unlike `[keeps:: N]` it never resets, and nothing
reads it to change decay, lane, Today, schedule, priority, or [[task-freshness]]. NEW,
Pending, Next, PROJECTS, early, and unblock-tickler keeps never write it; Pending
summaries stay in the [[work-log]] and deferrals in the [[schedule-log]]. See
[[decisions/rotten-keeps-are-logged]].
```

## 9. Open questions for Bryan

1. **Scheduled ticklers:** include them and exclude unblock ticklers? Recommended: yes.
   This is the biggest scope choice. If you mean strictly the ROTTEN tier, cdx's
   narrower rule works, but 4 of the 7 observed keeps would go unlogged.
2. **Blank Enter:** always `🤷` (recommended), or Work Log style "blank writes
   nothing"?
3. **Prompt gate:** every counted keep (recommended), or from the second consecutive
   keep?
4. **Tail:** keep ` · kept N×` on each entry (recommended)?
5. **Phase 3:** which do you actually look at: a mark tooltip, the Mac agenda chip, or
   JSON?

## 10. Recommended solution

Build a **Rotten Log, written by the counted keep itself**:

1. **One event, two records.** Every Alt+F / Ctrl+Alt+F on an exact due Ready ROTTEN
   or scheduled TICKLER row, and every decay-card Keep, asks "Why keep it as
   written?". Then, in one transaction, it stamps, increments `[keeps::]`, and
   prepends one entry under `🥀 **ROTTEN LOG**`.
2. **Always an entry, optionally a reason.** A blank Enter logs `🤷 no reason given`.
   Escape writes nothing and leaves the task due. Entries read
   `*YYYY-MM-DD* — <reason> · kept N×`, newest first, and automation never clears
   them.
3. **Visible where it matters.** The prompt and the decay card show the logged count
   and the latest reasons. The log sits under the task in the note where the walk
   lands. Pips remain the only mark on the task line, and tooltip or agenda chips can
   come later.
4. **Nothing else moves.** Streak semantics, decay, buckets, tiers, the walk, the
   other logs, `bob capture`, and the Mac contract stay as they are. The log is audit
   and display only.
5. **Ship in order:** decision record, glossary, and docs → bob-cli registry →
   bob-plugins parsers, writer, card Keep, fallback reroute, and project-conversion fix
   in one release, after `bob-cli-aq` lands → optional surfaces.

## Sources

- **Swarm reports (this directory):** `__cdx` (event contract, write safety, card
  fallback, test baseline), `__cld` (journal sizing, project-conversion risk, counted
  scope, prompt-with-history), `__grk` (registry surface, mixed-version risk, Keep Log
  naming), `__mus` (touch list, Rust/JS file map, glossary draft), `__gem` (velocity
  concern, modal sketch, tooltip idea).
- **Audited memory:** `decisions:rotten-keeps-use-priority-decay`,
  `decisions:review-walk-is-tiered`; `glossary:keep-streak`, `work-log`,
  `schedule-log`; reference `obsidian.md`.
- **Prior research:**
  `research:202610/rotten_keep_streak_and_approved_decay/rotten_keep_streak_and_approved_decay__final.md`
  (REVIEW LOG rejected for v1; second widget rejected).
- **bob-cli `f2c24531`:** `docs/freshness.md` §2a and L458/L501/L777/L834;
  `docs/projects.md:914`; `src/native/capture/sub_bullet.rs:292`;
  `src/native/capture_pomodoros_agenda.rs:70–84`;
  `src/native/ref_library/migrate_tasks/plan.rs` (child blocks copied).
- **bob-plugins `477af35`:** nav `010-requires-and-config.js:116/361`,
  `030-bullet-blocks-and-logs.js:121`, `060-decay-card-modal.js`,
  `110-project-seed.js:162`, `480-review-jump-and-nav-api.js:606/682/807`,
  `520-plugin-lane-links-and-review.js:293–445` and the fallback branch,
  `530-plugin-freshness-refresh-and-decay.js`,
  `540-plugin-decay-picker-and-cancel.js:204`; ledger-tools `110`, `120`, `210`
  (glyph uses).
- **Beads:** `bob-cli-aq` (Alt+P, in progress, same nav landing code), `bob-cli-6w`
  (pre-existing test failure), `bob-cli-94` (insert-above settle bug class),
  `bob-cli-5q`/`bob-cli-3y` (stale tier roster in memory, already tracked).
- **Vault (read-only, 2026-10-23):** `.bob/stats/review/2026-10.*.jsonl` tallies, a
  `[keeps::]` census, and glyph greps.

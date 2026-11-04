# Bob task beads worth working next — independent cdx assessment

Researcher: `research.3b.cdx`  
Evidence date: 2026-11-04 UTC; final two-host agent snapshot: approximately 20:20 UTC.  
Scope: task beads in the Bob project, including linked-repository and infrastructure work tracked there.

I recommend **ten existing task beads**, ranked at the end. The strongest work protects recorded time and authored notes, gets completed plugin fixes into the running vault, makes silent operational failures visible, and removes reproducible verification failures. I would not start another broad capture or Mac UI change while the current epics finish.

This is an independent assessment. I did not read the other four researchers' reports, transcripts, or findings. I screened the inventory of **174 unclosed tasks** (169 ready, five snoozed), audited the full details of 36 task candidates, read the three live Bob epic plans, checked agents on both hosts, inspected current source, and ran focused plugin tests. I did not launch workers, change bead state, deploy plugins, or modify the vault.

## How I ranked the work

The ordering weighs severity, frequency, breadth, evidence that the problem remains, implementation cost, and whether another worker already owns the relevant surface. A high corroboration count establishes repeated cost; it is not a vote. `ready` is a tracker state, not proof that a defect survives on today's source. Older `in_progress` plans without live agents are not automatically active conflicts.

The ten selected beads were still ready and unassigned when checked; their audited full records showed no explicit dependencies. Two need a deliberate behavior choice before implementation (`g4`, `7q`), and the monitoring tasks need an agreed alert contract. Those choices are part of working the beads, not reasons to fill the list with lower-value cosmetic work.

## Running-agent conflict audit

I used `sase agent list -j` locally and `ssh athena 'sase agent list -j'`, then inspected relevant non-research agent prompts and audited the corresponding beads/plans. Running, queued, and waiting members all reserve scope: a waiting lander does not mean its epic is available for unrelated work.

| Host | Active or reserved work | Consequence for this ranking |
| --- | --- | --- |
| apollo | `bob-cli-h0.8` queued; `h0.land` waiting. Epic `h0`: parent-task `- ^^` Move card, selection, project-note capture, and submit chaining. | Avoid capture routing, project-note grammar, and Mac submit/card work. |
| apollo | `bob-cli-h2.4` running; `.5`, `.6`, and `.land` waiting. Epic `h2`: past Pomodoros with `x=`, overlap repair, ledger recording, preview blocks, docs, and Mac card. | Defer the midnight-start bug `h1` and tracker bug `dq` until this settles; both are real candidates but too close to this work. |
| athena | `bob-cli-h4.1`, `.2`, `.3` running; `.4`–`.6` and `.land` waiting. Epic `h4`: transfer records, landing blocks, incomplete-transfer preview, and Mac cards. | Avoid transfer/capture preview infrastructure and broad fixture churn. |
| athena | `185--3` running, plus reserved `185.f0` / `185.f0.f1` continuation work. The inspected prompt identifies capture alias expansion; `185.f0` explicitly extends `.` / `;` as aliases for `^` / `:` in project-note bullets, and `185.f0.f1` proposes `,` → `+` expansion. | Treat capture alias grammar and its Mac integration as occupied. Do not casually fold `6g` into that work: project-name routing aliases are a separate issue. |
| apollo | `cd--code` in SASE, implementing `codex_exec_final_answer_integrity.md`. | Avoid using this Bob triage to start overlapping provider/finalization repairs. |
| athena | SASE epics `1qz` (agent hijack and work custody), `1r8` (publication blocking), `1r2` and `1n6.11` (CI/release train), with additional standalone SASE agents. | Runtime/finalizer incidents need cross-project revalidation and ownership checks; they are not clean Bob implementation starts. |

The `research.3b` and `research.3a` swarms were also visible. I used their presence only as scheduling metadata and did not consult their research.

Plan evidence, read through `sase artifact read`: `plan:202611/move_choice.md`, `plan:202611/past_pomodoro_recording.md`, and `plan:202611/transfer_previews.md`. Cross-project scope evidence came from audited reads of `sase-1qz`, `sase-1r8`, `sase-1r2`, and `sase-1n6.11`.

**None of the ten recommendations duplicates a live agent's stated deliverable.** Keep `g4` and `7q` sequential because they both concern ledger retention. Keep the three plugin test repairs together operationally but retain their separate bead identities. For `7q`, limit implementation to reconcile/retirement/plugin consumption; rebase and run capture compatibility tests after `h2`/`h4` land instead of expanding into their record/transfer planners. Agent status is a snapshot: refresh both hosts immediately before launching workers.

## Evidence and limits

The inspected revisions were:

- bob-cli: `87eecb1a9e3ce7dd9616aacd117c062094066e2c`.
- bob-plugins, opened through `sase repo open`: `b9f47f3fb45a042301abdcbb7f723c07d3bfb78d`.
- bob-mac-capture, opened the same way: `5960b31bc80f1b4339c0fea7457c642b414d8c01`.

Useful source anchors, all inspected locally:

| Evidence | Source |
| --- | --- |
| Dirty deploy from another checkout is refused even when its old HEAD is an ancestor; exact clean incoming bundles already have an exception. | [deploy.rs, guard](https://github.com/bobs-org/bob-cli/blob/87eecb1a9e3ce7dd9616aacd117c062094066e2c/src/native/plugins/deploy.rs#L829) |
| Deferred-only Ctrl+Enter close removes the timed row. | [060-pomodoro.js](https://github.com/bobs-org/bob-plugins/blob/b9f47f3fb45a042301abdcbb7f723c07d3bfb78d/plugins/task-status-cycler/src/060-pomodoro.js#L838) |
| The existing shared-vector test explicitly expects no closed row for the affected case. | [pomodoro-clock test](https://github.com/bobs-org/bob-plugins/blob/b9f47f3fb45a042301abdcbb7f723c07d3bfb78d/scripts/test-task-status-cycler-pomodoro-clock.cjs#L96) |
| Reconcile's default consumption deletes a link's subtree; capture has optional preservation. | [structure.rs](https://github.com/bobs-org/bob-cli/blob/87eecb1a9e3ce7dd9616aacd117c062094066e2c/src/native/task_status_hooks/structure.rs#L464) |
| Completion retirement invokes unrestricted empty-entry cleanup. | [retirement.rs](https://github.com/bobs-org/bob-cli/blob/87eecb1a9e3ce7dd9616aacd117c062094066e2c/src/native/task_complete/retirement.rs#L168) |
| Repeated interrupted merge sets halt state and returns a fatal error. | [vault_sync.rs](https://github.com/bobs-org/bob-cli/blob/87eecb1a9e3ce7dd9616aacd117c062094066e2c/src/native/vault_sync.rs#L760) |
| Brief attribution compares only original source paths; output links also use original source paths. | [brief.rs](https://github.com/bobs-org/bob-cli/blob/87eecb1a9e3ce7dd9616aacd117c062094066e2c/src/native/periods/brief.rs#L273) |
| Screenshot CDP calls have no deadline, and browser cleanup waits on only the launched process. | [preview-task-link-marks.cjs](https://github.com/bobs-org/bob-plugins/blob/b9f47f3fb45a042301abdcbb7f723c07d3bfb78d/scripts/preview-task-link-marks.cjs#L84) |

Focused verification on apollo:

```text
node --test scripts/test-ledger-tools-note-ready.cjs \
  scripts/test-ledger-tools-relation-index.cjs \
  scripts/test-ledger-tools-gcal-events.cjs \
  scripts/test-ledger-tools-freshness-namespace.cjs \
  scripts/test-navigation-hotkeys-schedule-work-log.cjs
104 tests: 100 passed, 4 failed (about 3.2 seconds)
```

The failures were both `eh` startup tests, `et`'s freshness reload test, and `ff`'s future-scheduling test. **The calendar-create test also named by `et` passed**: that bead now needs a narrower fix than its original report. A separate run of `close-defers-not-started-off-clock` passed its current assertion that the closed row disappears. That is direct reproduction of the unwanted behavior, not evidence that `g4` is fixed.

For `8r`, a read-only query of athena's live Prometheus `/api/v1/rules` returned only `athena.apt` (eight rules) and `athena.disk-space` (five rules), all healthy. There were no service-account CPU, temporary-executable, or mining-egress rules in that Prometheus instance. The independently read prior incident report, `research:202610/athena_plex_compromise_incident_report.md`, documents the October 17 miner/bot incident and delayed detection. The bead's subsequent integration note identifies an already working Alertmanager/email route. This does not establish that no other security monitoring exists, or that there is a current compromise.

I did not rerun full Rust/Mac suites, reproduce the intermittent Chromium hang, or exercise changes on the live vault. The report distinguishes direct tests, current source inspection, and historical evidence accordingly.

## Why several tempting candidates are absent

| Bead(s) | Disposition |
| --- | --- |
| `8a` — unknown flags become task text | Likely closure audit, not a fresh implementation project. Its October 24 note describes the guard, CLI regression tests, and Mac capability gating. Current source contains `capture_flag_guard.rs`; do not prioritize the old scary title without re-reproduction. |
| `f3`, `fu` — old Mac XCTest failures | The original blanket claim that master never gets through Test is stale. [Run 41888215951](https://github.com/bobs-org/bob-mac-capture/actions/runs/41888215951) at `4906d94` passed Test, Bundle, signature verification, launch, and install. [Run 41900858873](https://github.com/bobs-org/bob-mac-capture/actions/runs/41900858873) at `5960b31` failed with five assertions in Go To tests, rather than the old baseline set. Audit closure/reclassification first; do not spend two top-ten slots repairing already-cleared lists. This does not claim today's Mac CI is green. |
| `e4` — stale protected plugin deployment | A recurring operational symptom of `fy`. Use its history and verify its deployed plugins during `fy` acceptance; avoid a second independent worker applying force-sync as a competing fix. |
| `h1`, `dq` | Current midnight arithmetic and block-tracker concerns are credible, but `h2` owns adjacent recording/preview machinery. Revisit on its landed result. |
| `ge`, `6g`, `9n` | Broad capture fixtures, routing, and unnamed-session surfaces intersect active capture/Mac work. Useful later, less clean to start now. |
| `e0`, `ei`, `gy` | Serious SASE/vault ownership incidents. Current instructions already require staged handoffs to finalize, so the old mechanism in `e0` cannot simply be assumed current. Verify prevention/recovery status in SASE with its active custody/finalizer work before commissioning another Bob-side repair. No claim that all three are solved. |
| `gt`, `gu`, `gw` | Real period-brief quality problems, but `gs` is the first repair: without correct archived identity and links, later ranking and quote work rests on broken references. Share a subsequent brief review, not simultaneous edits to `brief.rs`. |
| `f8`, `gc` | Worth performance work after correctness. Their evidence deserves real profiling, not inflated budgets; `gc` also has later catalog optimizations whose impact on Done remains unmeasured. |
| `30`, `5g` | Valuable Mac scheduling work, but older live-state evidence and a Mac Terminal installation constraint reduce immediate certainty. Verify the current schedule before choosing this over the directly confirmed issues. |
| `3r`, cosmetic affordances, memory-only notes, snoozed evaluations | Do not manufacture urgency: `3r` explicitly reports no affected active note; the other items have less demonstrated user impact or an intended revisit condition. |

## Ranked task beads to work

### 1. [bob-cli-g4 — Preserve timed Pomodoros on deferred-only Ctrl+Enter closes](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-g4/README.md)

**Why first:** a normal close can erase 60 recorded minutes, making history and Stats depend on whether Bryan used Obsidian or capture. The affected source and test remain present, and the focused test reproduced deletion. Stored size: **small**; confidence: **high**.

**Recommended solution:** choose preservation of a timed closed row as the canonical result, matching `bob capture x` and the existing policy that closed time is history. Restrict empty-placeholder cleanup so it cannot remove a row carrying recorded time. Keep deferring the future Event Task into its next placeholder. The bead explicitly leaves a policy choice open; resolve that choice before changing the expectation.

**Acceptance:** the shared vector retains `0800-0900` and its 60-minute clock field; both writers preserve equivalent ledger history. Cover worked and off-clock rows, notes, and a genuinely empty untimed placeholder. Replace the test's deliberate divergence with an assertion of the preserved row. No active worker owns this plugin close branch. Coordinate sequentially with `7q`.

### 2. [bob-cli-fy — Let safely landed plugin builds escape dirty-deploy protection](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-fy/README.md)

**Why:** completed fixes are of little use while the vault keeps an older build. This repeatedly burdens plugin epics with manual proofs and force-syncs, and `e4` documents missing shipped behavior. The source still refuses a non-identical dirty deployment from another checkout. Stored size: **large**; confidence: **high for the mechanism**, with current live deployment state unmeasured.

**Recommended solution:** extend the guard with conservative content provenance: recognize the **entire stamped managed bundle** as one coherent committed revision reachable from the incoming clean HEAD, then allow advancement. Validate that the vault still matches the stamp. The current exact-bundle clean restamp already works; the missing case is a previously dirty bundle followed by newer legitimate commits. Never accept “each file hash exists somewhere” as proof, mix unrelated historical blobs, or disable protection for genuinely uncommitted work. A clean post-commit restamp can complement this, but a broad SASE finalizer redesign is unnecessary for the Bob-side repair.

**Acceptance:** dirty deploy → committed matching bundle → later commit → sync succeeds; divergent, modified, unverifiable, or pending deployments still refuse. Exercise two checkouts and the recorded `e4` class. No blanket `--force` recovery. The selected implementation surface is `src/native/plugins/deploy.rs`, outside the live capture epics.

### 3. [bob-cli-7q — Preserve notes and unrelated entries during link consumption](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-7q/README.md)

**Why:** authored child notes or unrelated placeholders can disappear depending on which writer consumes a blocked link. Current reconcile uses the old defaults, and completion retirement still calls unrestricted empty-entry cleanup. This is broader data preservation than a display improvement. Stored size: **large**; confidence: **high from current source and the documented contract**, without a new end-to-end reproduction.

**Recommended solution:** settle the retention contract, then apply capture's note-preserving, only-emptied, resolved-identity behavior to reconcile, task completion retirement, and plugin dependency consumption. Preserve child notes as prose and remove only entries that this operation actually emptied, subject to `g4`'s timed-history rule. Keep scope separate from the accepted decision that capture may drop prerequisites while plugin gestures retain consumption; preserving notes does not authorize changing that dependency policy.

**Acceptance:** cross-writer vectors cover nested notes, aliased links resolving to one task, untouched empty placeholders, timed rows, and reported removals. Run the reconciler twice to show stability. Start the design now; implement the three named consumption paths without editing active `x=`/transfer planners, and integrate after their landing if shared helpers changed.

### 4. [bob-cli-8r — Detect hostile service-account activity on athena](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-8r/README.md)

**Why:** this follows a documented compromise, not a speculative feature request. The live Prometheus inspection confirms that the requested detection rules are still absent from that instance. Protecting the machine that runs the development workload has high impact even though this is infrastructure work tracked in Bob. Stored size: **large**; confidence: **high for the monitored gap**.

**Recommended solution:** add service-account CPU and suspicious-executable telemetry, with mining-port egress as a supplementary signal. Reuse the established Alertmanager/email route described in the bead's integration note. Scope and tune the rules against legitimate Plex/transcoding and development workloads; host load alone is inadequate, and common ports are indicators rather than a complete detector. Include collector freshness so missing telemetry is visible.

**Acceptance:** synthetic test inputs produce the expected firing and resolved states through the existing delivery path, legitimate workloads remain tolerable, and configuration survives restart. No containment action or second notification stack is required by this task. No monitoring epic appeared in either host's live roster.

### 5. [bob-cli-9x — Alert when a host's vault sync halts](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-9x/README.md)

**Why:** the sync breaker correctly stops repeated merge attempts, but a headless halt can leave hosts diverged unnoticed. The halt branch still records state and returns an error without cross-host delivery. Stored size: **large**; confidence: **high for the missing code path**; I did not claim any host is presently halted.

**Recommended solution:** expose persisted halt/last-success state to the established monitoring route. Deduplicate by host, vault identity, and halted merge SHA; retry delivery durably and emit a recovery transition. Use one agreed delivery path that Bryan already receives. Preserve the breaker's manual conflict-recovery behavior.

**Acceptance:** repeated attempts at the same halt yield one incident, a new halt is distinguishable, transient delivery failure retries, recovery resolves, and an unavailable collector does not look healthy. Implement the Bob status/export contract separately from `8r`'s host rules, then coordinate their shared infrastructure configuration. It has no capture-epic overlap.

### 6. [bob-cli-eh — Repair the layout-ready callback test fakes](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-eh/README.md)

**Why:** two deterministic failures keep recurring across otherwise unrelated plugin landings; the bead has 24 corroborations, and both failures reproduced on the inspected revision. A small harness fix restores useful startup verification. Stored size: **small**; confidence: **high**.

**Recommended solution:** model `onLayoutReady` as an ordered collection of callbacks, run each registered callback once, and preserve unload behavior. Fix the fakes rather than removing Calendar startup registration or weakening scan-count assertions. Check other copies of this particular fake for the same single-slot assumption.

**Acceptance:** note-ready again observes its eligibility scan plus the relation-index prefilter; relation-index completes after layout readiness; unload prevents late registration. Run the two suites plus the Calendar startup suite. These test files are outside the active capture/Mac epics.

### 7. [bob-cli-et — Make freshness tests independent of the real date](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-et/README.md)

**Why:** the freshness reload failure remains reproducible and repeatedly consumes verification effort. The original bead's Calendar failure now passes, so repair the remaining defect rather than redoing that branch. Stored size: **small**; confidence: **high**.

**Recommended solution:** use one controlled clock for the initial freshness memo and the later changed-file refresh. The current test starts at October 8 but refreshes against the real day, when an October 1 stamp with a 30-day interval is due again. Do not merely advance fixture dates to postpone failure.

**Acceptance:** the due-set transition still fires exactly one reload, an unrelated edit fires none, and results hold under dates before and after the original October 31 boundary. Keep the already-passing Calendar tests green and narrow the bead's remaining scope in its closeout evidence. No live owner overlaps this harness.

### 8. [bob-cli-ff — Give the scheduling test a coherent clock](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-ff/README.md)

**Why:** another independently reproduced permanent-red test, cheaply repairable. It still calls November 2 a future date while executing in November 4; changing only the Work Log timestamp did not pin the scheduling decision. Stored size: **small**; confidence: **high**.

**Recommended solution:** have the scheduling review and log-writing harness share the same fixed time, or derive the requested future date from an injected harness clock. Retain a real test that future scheduling changes Pending to Blocked and writes the summary. This is distinct from `et` because it is a different harness and decision path.

**Acceptance:** retain the status and log assertions and add meaningful today/future boundary coverage using the controlled clock. Running on a later real date must not change results. Work alongside `eh`/`et` in one verification pass while closing each bead on its own evidence.

### 9. [bob-cli-fz — Bound screenshot RPCs and clean up browser processes](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-fz/README.md)

**Why:** an intermittent screenshot failure can become an indefinitely hung harness with orphaned processes, wasting capacity on a host already running many agents. Current CDP calls have no deadline; cleanup waits on the main browser process without the stronger lifecycle handling the bead requests. Stored size: **large**; confidence: **high for the missing bounds**, historical rather than newly reproduced for the Chromium stall itself.

**Recommended solution:** share a CDP client with connect/call deadlines, reject pending requests on disconnect, and make shutdown bounded on success, error, and signals. Track and terminate the browser process group where supported, escalating only for that owned group; remove its temporary profile. Investigate the renderer/host cause separately after the harness cannot hang forever.

**Acceptance:** deliberately stalled/disconnected CDP calls fail with a useful method name within a limit, aborted runs leave no owned browser children, and normal previews still render. Preserve screenshot checks instead of accepting a timeout as a pass. No active Bob epic owns these preview scripts.

### 10. [bob-cli-gs — Resolve archived task identity in period briefs](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-gs/README.md)

**Why:** archived work is normal historical data. Current `linked_minutes` matches only `source_path`, and `task_link` emits the old source location, so the brief loses attribution and gives dead links precisely when reviewing completed work. This is the most foundational of the period-brief defects. Stored size: **medium**; confidence: **high from current source and prior multi-week observations**.

**Recommended solution:** resolve both original and archive locations to the same canonical task identity, count a session/task match once, and render the actual archive residence when present. Preserve full vault-relative paths and block IDs; do not use block ID alone or collapse directory-distinct notes. Share the resolver between attribution, ranking inputs, and output links.

**Acceptance:** fixtures cover archived tasks, original-path historical links, archive-path links, equal block IDs in different notes, and deduplication when aliases identify one task. Both JSON and Markdown preserve the task's linked minutes and emit a resolvable archive target. Keep `gt`'s minute-allocation policy and `gu`'s historical-state policy out of this repair. No running agent on either host was working on period briefs at the final check.

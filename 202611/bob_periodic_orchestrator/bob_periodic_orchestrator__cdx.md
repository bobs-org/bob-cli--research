# Bob refresh: a dependable periodic maintenance command

Independent research by **cdx**, 2026-11-18.

**Recommendation:** build `bob refresh`: one finite, sequential pass over a small registry of existing Bob operations, each with its own interval. Run it from one Mac cron job every five minutes. Keep most work at 15-minute intervals, Gmail hourly, and Calendar hourly. Enforce Calendar's hourly minimum inside `bob gcal sync`, so the daily-note plugin and manual calls share it too.

This is design research, not an implementation or deployment. I inspected the current code, chezmoi source, and live Mac scheduling state; I have not changed application code, configuration, or the Mac crontab. The concrete configuration and migration below are proposed changes. I used the requested [earlier task review](bob_sync_task_review.md), independently checked its important premises, and did not consult another report or researcher from this swarm.

## What the evidence establishes

The earlier review is persuasive about the operational need. It reports roughly 1,700 runs over nine days, with 50 missing-daily-note failures and ten lock-contention failures among 78 failures. Those historical measurements belong to that review; I did not remeasure the nine-day log corpus. They support reducing false alarms, not a promise that the new command eliminates every contention failure.

I independently checked these current facts:

| Observation | Evidence and implication |
| --- | --- |
| Four Mac cron jobs, not five, are currently installed | `cronctl status mac --all-schedulers` returned `in_sync`, no unmanaged lines, and the four jobs below. Calendar is a proposed fifth operation. |
| Calendar has no periodic job | Neither chezmoi's cron data nor the live Bob scheduler inventory contains one. |
| Vault transport remains separate | The Mac has the loaded `com.bbugyi.bob-vault-sync` LaunchAgent. This fast transport loop must remain outside the new periodic pass. |
| Daily-note creation invokes both Calendar and Gmail | Ledger Tools' `291g-plugin-gmail-sync.js` awaits the Calendar trigger, then runs Gmail. Cron is not the only source of these commands. |
| `sync` carries an old meaning | `docs/develop/migration-notes.md` says `bob sync`, `bob bulk-git-commit`, and `bob_sync` were retired in favor of `bob vault-sync`. Reassigning the spelling would make stale scripts do different work. |
| `nightly` is a presentation precedent, not a safe implementation template | `src/native/nightly.rs` holds the shared maintenance lock across its entire sequence and calls functions in process. Frequent refresh should not copy either choice unquestioningly. |
| Scans already have structured, nuanced outcomes | Ref scan JSON distinguishes failures and held PDFs. A successful process exit can still mean that some PDFs were held. A no-work scan can leave the previous `last-scan.json` untouched. |
| Existing retry budgets are not total deadlines | Task reconcile's retry loop explicitly lets an active attempt finish even after its retry budget expires. `--retry-timeout 120` does not prove a two-minute total run bound. |
| Standalone project sync owns a transaction | It performs identity checks, locking, pre-sync, guarded application, a scoped commit, and post-sync. Replacing it with a convenient inner function can bypass these guarantees. |
| Calendar currently fetches before checking daily-note readiness | `gcal::sync` fetches selected days before `sync_day` reports missing/unrendered notes. A wrapper that merely notices exit zero can misclassify a network-consuming wait as completed work. |

Current schedule from chezmoi at `002760c3a9155d98f28645cfdf3bf1b1b8dcd378`, independently confirmed live:

| Job | Local-time schedule | Command |
| --- | --- | --- |
| `bob-highlights-sync` | `0,15,30,45 * * * *` | `maybe_bob_highlights_sync -w` |
| `bob-projects-sync` | `5,20,35,50 * * * *` | `bob projects sync` |
| `bob-task-reconcile` | `10,25,40,55 * * * *` | `bob task reconcile --retry-timeout 120` |
| `bob-gmail-sync` | `7 * * * *` | `bob gmail sync -q` |

The live status reported successful latest runs at 16:30Z, 16:35Z, 16:40Z, and 16:07Z respectively. The Mac reported `Kellys-MacBook-Pro.local` and `bob 0.5.0`. Its cron timezone is America/New_York. The expected Bob hostname slug is `kellys-macbook-pro-local`, derived from the actual hostname and Bob's normalization; verify it in the cron and GUI environments before pinning it, because Bob checks the `HOSTNAME` environment variable first.

## Is this a good idea?

Yes, provided the product is **one maintenance pass with due-work selection**, rather than a new daemon or a general workflow system.

The valuable change is not reducing four lines to one. It is making a reliable order, giving Calendar an explicit cadence, showing why something did not run, and preserving a usable health history. A sequence removes collisions between its own children. It cannot remove collisions with interactive edits, reference creation, plugin calls, or vault transport; the existing locks and guarded writes still matter.

There is a real cost. Four independent jobs currently have separate failure domains. A unified pass introduces shared scheduler state and can make a stuck scan delay mail and task repair. The earlier review understates the work when it suggests in-process calls plus simple per-step timeouts: arbitrary synchronous Rust work cannot safely be stopped by abandoning a thread or timing out an await. Correct supervision and honest outcomes are core requirements, not finishing touches.

A small shell script would suffice if the task were only sequencing commands. Once it needs persisted cadence, manual/cron overlap protection, typed outcomes, configurable selection, and an hourly invariant across callers, keeping it in bob-cli is justified. Do not add editable dependency graphs, arbitrary shell commands, plugin-defined jobs, parallel vault writers, distributed leases, or background workers in the first version.

Do not fold this into `bob task reconcile`. That command has a specific task/ledger repair contract. Network imports, PDF coordination, Gmail archive consent, and calendar ownership should retain their existing owners.

## Naming: prefer `bob refresh`

The useful user sentence is: **“Refresh Bob's notes and task state.”** It describes bringing the local working view up to date without promising that the entire vault has been pushed successfully.

| Candidate | Assessment |
| --- | --- |
| **`refresh`** | Best balance of familiarity, brevity, and meaning. Seven letters; communicates bringing derived/imported state current. Help must explicitly mention writes and enabled integrations. |
| `sync` | Short and familiar, but overloaded with Git transport and individual integrations, and has a retired meaning in this exact CLI. Reject reuse for a different operation. |
| `upkeep` | Semantically broad and accurate. A good runner-up, but a noun invites `upkeep run`/`upkeep status`; the project's CLI rules disallow a mutating default for a new command group. |
| `tend` | Four letters and pleasant for a personal vault. Less discoverable, sounds like an interactive task review, and needs explanation before users know what it does. |
| `maintain` | Accurate, but administrative and longer. Suggests full nightly maintenance, cleanup, or repair. |
| `update` | Familiar, but easily confused with upgrading Bob, plugins, or software. |
| `pulse` / `tick` | Good internal names for a scheduler invocation; poor descriptions of a human command's effects. |
| `daily` / `routine` | The first misstates the frequency; the second says little about what changes. |

Use one verb command, not a group whose bare form secretly mutates. Proposed help opening:

> Run due maintenance to refresh reference notes, projects, mail, calendar events, and task state.

Immediately explain that enabled steps can update notes/PDF markers and perform already-configured Gmail actions. Do not imply this is a read-only screen refresh. Do not introduce `bob sync` as an alias for it. Existing standalone commands remain available.

## Product contract and configuration

The allowlist should initially contain exactly five stable step IDs:

| ID | Existing operation | Initial interval | Why included |
| --- | --- | --- | --- |
| `refs` | `bob ref scan -w -f json` | 15m | Preserve annotation import, intake, and marker writes currently requested by `-w`. |
| `projects` | `bob projects sync -f json` | 15m | Preserve catalog/lifecycle reconciliation and its standalone transaction. |
| `gmail` | `bob gmail sync -q -f json` | 1h | Preserve filing, watches, and existing archive policy; do not auto-confirm an archive backlog. |
| `gcal` | `bob gcal sync -n 2 -q -f json` | 1h | Yesterday and today, respecting existing Google/vault ownership rules. |
| `tasks` | `bob task reconcile -r 120 -f json` | 15m | Final repair pass over the state the preceding operations produced. |

Execution order is **refs → projects → gmail → gcal → tasks**, regardless of YAML key order or selector order. Most of these are ordering preferences, not success dependencies: a Gmail fetch failure must not prevent Calendar or task repair. A failure that leaves uncertain mutation/recovery state is different and may stop the pass until the integrity check succeeds.

One built-in follow-up rule is worth adding: when an earlier step reports safe, committed/applied vault changes, schedule enabled task reconciliation once at the end of the pass even if its periodic interval has not elapsed. Otherwise independent clocks can make an hourly Gmail run miss the final cleanup this feature is meant to provide. `tasks.after_changes: true` makes this explicit; `every: 15m` remains its periodic backstop. This is one coalesced follow-up, not a configurable dependency graph. Persist a `needs_reconcile` marker until successful task reconciliation so a crash or missing daily note cannot lose it. A selector that excludes tasks leaves the marker for the next ordinary pass; it does not silently broaden the selected scope.

Do not include Git transport, nightly archiving, plugin deployment, or self-updates. They have separate purposes and lifecycles. Do not include Google Keep in v1. Keep's current docs actually specify a noninteractive parent-selection fallback, so “it always prompts” is not a sound exclusion argument. The stronger reasons are webpage clipping, optional narration, imports and recovery behavior, and the need for a separately reviewed unattended policy. Consequently, this feature does **not** replace every action in the morning chore if that chore still includes Keep.

Proposed additions to chezmoi's existing `home/dot_config/bob/config.yml`:

```yaml
# Proposed schema; these keys do not exist yet.
refresh:
  writer: kellys-macbook-pro-local
  steps:
    refs:
      every: 15m
    projects:
      every: 15m
    gmail:
      every: 1h
    gcal:
      every: 1h
      days: 2
    tasks:
      every: 15m
      after_changes: true

# Merge these keys into the existing gcal mapping; do not replace it.
gcal:
  writer: kellys-macbook-pro-local
  min_interval: 1h
```

`refresh.steps.gcal.every` is the runner's desired cadence. `gcal.min_interval` is the lower-level admission limit shared by all `gcal sync` callers. These two settings answer different questions; status should display both. Existing account, calendar list, `gog`, root, and ownership configuration stay in their current sections.

Keep the schema explicit and small:

- An absent `refresh` block enables nothing. A present `steps` map is the allowlist: omitted steps are disabled, and `enabled: false` is an optional convenient off switch. Shipping an upgrade must not silently enable authenticated integrations.
- `every` accepts positive whole-unit durations such as `5m`, `15m`, `1h`, or `2h`, with documented bounds. Reject zero, negative values, unknown units, and impractically short intervals. No cron expressions, calendar-time scheduling, or overloaded `off`/`manual` strings inside this block.
- Validate the complete refresh section before starting any child. Reject unknown step IDs and unknown keys *inside this section*; do not make unrelated existing config sections globally strict.
- Require an explicit `refresh.writer` for enabled mutating work in this shared config. Display a clear `wrong_host` skip elsewhere, never silently substitute a dry run. Continue honoring each integration's writer checks as a second boundary.
- Support per-step bounded `timeout` overrides once the adapters implement their termination contract. Ship registry defaults and document them; changing frequency must not implicitly change timeout.
- Limit per-step options to typed capabilities, initially Calendar's bounded `days` value and task reconciliation's `after_changes` boolean. No arbitrary command strings or argument arrays. The registry owns executable arguments and noninteractive behavior.
- Respect the existing configuration precedence: `BOB_CONFIG_FILE`, then XDG config, then `~/.config/bob/config.yml`. No second refresh configuration file and no config-writing wizard in v1.

The five-minute cron heartbeat is separate from each operation's interval. It checks cheaply for eligible work; it does not run every operation every five minutes. It also bounds the normal wait after the Mac wakes or Templater finishes to the next five-minute tick, plus any earlier running steps. This is a polling bound, not a promise to wake a sleeping Mac.

## Calendar: make “no more than hourly” a real invariant

Interpret the user's requirement literally: on the Mac, **admitted `bob gcal sync` attempts begin at least 60 minutes apart**, including failures, manual calls, plugin calls, multi-day syncs, and calls through refresh. A command invocation during that window may return a typed wait result; it must not start another sync fetch. This limits sync attempts, not individual HTTP requests: a successful multi-calendar snapshot naturally makes several requests.

A cron entry at minute zero does not establish this invariant. Neither does “60 minutes since last success”: failures could retry every five minutes, and the daily-note plugin could run seconds after cron. A new date must not reset the limit, either.

Implement a host-local Calendar admission guard in the `gcal sync` entry point:

1. Validate arguments, config, host, and cheap local readiness before admission. For the scheduled `-n 2` pass, defer the whole Calendar step until **today's** note is ready, even if yesterday exists. Otherwise a 07:25 fetch for yesterday could consume the hour just before today's note is created at 07:30.
2. Under a dedicated host/account guard, read and validate the persisted attempt reservation. If it is too early, return existing `status: "waiting"` with a new `waiting.reason: "interval"`, `next_eligible_at`, and a precise message. Do not clear a prior error or pretend this is a successful sync.
3. Durably reserve the start time before the first sync network operation. Then execute the existing snapshot and ownership logic. A failed attempt consumes the interval too. Keep an in-flight exclusion so a very long attempt cannot overlap another even after an hour.
4. Record completion separately from admission. Never reset the cooldown just because the parent runner was killed or received malformed JSON.

The cooldown should be keyed by host and resolved account, not day, selected calendar subset, or vault path; changing `-D`, `-n`, or `BOB_DIR` must not accidentally bypass it. Keep the record in local state, outside the vault. The outer refresh state is separate and keyed by canonical vault identity.

The existing `-F` means “reset the day's Google-owned projection,” not “ignore scheduling limits.” It must not bypass this new configured floor. Do not invent a generic refresh `--force` that can slip `-F` through. Under this policy, an urgent manual reset may need to wait; show the exact earliest time. If Bryan later wants a manual exception, explicitly change the requirement to “automatic syncs at most hourly” instead of silently weakening it now.

A network-fetching `gcal sync --dry-run` also needs admission under the literal rule. Its only permitted new write would be the documented host-local quota reservation; no vault or Google mutation. This is an explicit behavior adjustment and must be documented and contract-tested. In contrast, `bob refresh --dry-run` should remain completely local and write nothing: it previews *scheduling*, not each integration's remote diff. `gcal list` and doctor are separate read operations, outside the requested sync-attempt limit; this feature is not a universal Calendar API quota manager.

The plugin already accepts Calendar `waiting` reports and its Templater notice checks specifically for `note_unrendered`. An additive `interval` reason can therefore fit the existing shape without falsely saying Templater is slow. Add a compatibility test for that exact decoder. Avoid introducing a new top-level status such as `throttled`: the current decoder has a closed status allowlist.

There are honest limits. A durable local limiter assumes its state is retained and the clock is sensible. Reject corrupt/unsupported state for the Calendar step rather than treating it as “never run.” Handle a backward clock conservatively; use a suspend-aware elapsed clock where available, with persisted UTC timestamps for display/restart. A large clock anomaly should hold and report, not release a burst. Destructive state loss cannot preserve a historical guarantee; document it as an explicit reset, not an ordinary troubleshooting instruction. Do not use `BOB_NOW`—which can intentionally backdate vault operations—as the production scheduler clock.

Hourly polling is a user preference, not a Google-mandated quota. Google documents per-minute quotas and bounded exponential backoff for rate errors. Keep transport retries bounded within the admitted attempt; never layer an unlimited whole-command retry loop over them. [Google Calendar usage limits](https://developers.google.com/workspace/calendar/api/guides/quota)

## Runtime design: serialization without monopolizing the vault

Use a finite controller in bob-cli with a registry, a pure due-work planner, per-command adapters, a state store, and a renderer. The controller should execute the **current Bob executable** with explicit argument vectors and each command's JSON mode. Do not resolve an unrelated `bob` from PATH and do not invoke a shell to interpret user configuration.

This is preferable to directly calling today's `run(...) -> i32` functions: they print their own output, return insufficient outcome information, and cannot provide a clean process-termination boundary. Existing command JSON is already a useful interface. If later refactoring exposes typed, cancellable internal cores, adapters can switch without changing the product contract.

Each child receives the same vault/config context and noninteractive stdin. Capture stdout and stderr separately, drain them concurrently, and bound retained output. Parse that child's fresh stdout, not a shared “last result” file; the latter may be stale or belong to another caller. Do not collapse nonzero exit plus partial results into a generic string, and do not parse English stderr to decide whether an operation succeeded.

Hold a new per-vault **refresh-run lock** across the pass. Do **not** hold `bob_sync.lock` across the pass and do not pass an invented “maintenance lock already held” environment switch to children. Each standalone child retains its current locking, pre-sync, guarded-write, and commit behavior. The scan must retain `bob_sync.lock → scan.lock` ordering. Use an OS-backed lock rather than an orphanable mkdir lock for the new controller. Cronrun already serializes its own job name, but the Bob lock is still needed for manual-vs-cron races.

A second refresh invocation should return `already_running` without overwriting the active run's receipt. Locks must release after process death; ensure an orphan child cannot keep mutating after the controller admits a new pass. This requires process-group/supervisor handling and tests, not just a PID file. The Calendar guard and each command's existing locks are still necessary because callers outside refresh do not hold the refresh lock.

Persist state atomically after admission and after each result, not just at the end of the pass. Use a private local directory such as `$XDG_STATE_HOME/bob/refresh/<vault-key>/` with 0700 directories and 0600 files. Keep an explicit schema version and a bounded last-run receipt. A useful per-step record contains `last_started_at`, `last_finished_at`, `last_success_at`, `next_eligible_at`, outcome/reason, and whether work was held or partially applied. Keep raw mail content and calendar descriptions out of the aggregated receipt.

For ordinary steps, `every` means **minimum spacing between admitted starts**, not an exact wall-clock appointment. Tasks have the explicitly configured `after_changes` exception: producer writes can bring their one final pass forward, then reset the periodic clock. The Calendar minimum has no such exception. Reserve before starting; a failure or crash consumes that slot, and the next regular interval retries. Preflight skips such as “disabled,” “wrong host,” and “today's note absent” do not consume it. Known no-work contention outcomes can remain eligible for the next heartbeat, provided the adapter proves no work started. Calendar's lower-level reservation always wins after any sync fetch began. Track last success independently so a broken operation running regularly still looks broken.

Recalculate the due decision at each actual step start; do not stamp every child with the tick's original timestamp. After sleep, run each overdue step once and advance from that attempt. Never replay one job for every missed interval. Changing an interval recomputes eligibility from the existing last start, and disabling/re-enabling a step does not erase the Calendar floor. Changing a step's options should show that the settings changed, without secretly clearing cooldowns.

This is at-least-once maintenance under crashes, relying on existing idempotent/recovery-aware commands. There is no all-pass transaction or exactly-once promise.

### Timeouts need a truthful safety boundary

Start with provisional whole-step budgets such as refs 5m, projects 2m, Gmail 3m, Calendar 3m, tasks 3m, then calibrate against awake-machine measurements. The prior review's scan p90 of 133 seconds makes a blanket one-minute cutoff inappropriate; its very long tails may include sleep and do not establish a safe hard cap. These numbers are proposed tuning, not measured guarantees.

Use bounded transport calls and command-level cooperative stopping at safe boundaries wherever possible. A supervised child deadline may terminate a process group, but a timeout is **a failure with potentially partial work**, never an innocuous `waiting` result. After termination, reap descendants and use the command's recovery/integrity evidence before starting another mutator. If that cannot establish a safe state, stop the pass and report recovery needed. Ordinary independent failures continue to later steps; unknown write state does not.

“Reconcile always runs last” means last among safely executable operations, not permission to overlap a still-running or half-terminated writer. A future that returns on timeout while its child keeps running is a release blocker. If an adapter cannot yet meet safe termination and recovery tests, do not claim the unified pass has bounded isolation. This is the main reason I would estimate this as a medium feature with integration work, not a tiny wrapper.

## Outcomes, observability, and the interface

The interface should tell the truth about three different questions: **did it run, did it succeed, and is it fresh?** Exit zero alone answers none of these completely.

Proposed CLI:

```text
bob refresh                    run configured steps that are due
bob refresh gmail tasks        consider only these enabled steps, in registry order
bob refresh -d                 preview eligibility and reasons; no network or writes
bob refresh -s                 show stored results, last success, and next eligibility
bob refresh -f json            emit one versioned aggregate receipt
bob refresh -q                 show failures/actionable attention only
```

Long names are `--dry-run`, `--status`, `--format`, `--quiet`, and `--help`; all have the short aliases above or `-h`. Sort flags alphabetically in help. `--status` and `--dry-run` are mutually exclusive read modes. Selectors filter the configured set, never enable a disabled job. Unknown IDs are errors before any work.

Omit `--all` and an interval-bypassing option in v1. The earlier proposal made `--all` both override cadence and include Keep; that is too much hidden behavior for a convenience flag. Users can run existing standalone commands when they intentionally need an operation now; the Calendar limit remains enforced there. A later explicit `--run-now` could bypass soft refresh intervals while preserving the Calendar floor, but it is not necessary to ship.

A human run should fit on one screen, with restrained existing Bob colors, aligned columns, and readable plain-text output when redirected. Example, not captured output:

```text
Bob refresh · Mac · 10:20

  ✓ References   2 updated; 1 held                  42s
  ✓ Projects     current                           5s
  · Gmail        due in 37m
  · Calendar     hourly limit; next 11:07
  ✓ Tasks        3 repaired                        12s

3 checked · 2 deferred · 1 reference needs attention
```

Avoid an overall green “everything synced” when some work is held. Color supplements text; it never carries the outcome alone. Show one line while each step runs so a 90-second scan is visibly alive. Expand only actionable details, using the existing child command as the recovery instruction. Do not show fake percentage progress when the work size is unknown.

The JSON receipt should separate `outcome` from `reason`, with stable values for success, partial/held, skipped, failed, and interrupted; reasons can include `not_due`, `wrong_host`, `already_running`, `note_missing`, `note_unrendered`, `lock_busy`, and `interval`. Include actual times, duration, next eligibility, last success, child exit status, and bounded summary counts. `ok: true` means the pass had no fatal/runtime failure, not that all steps ran or every held item resolved.

Treat errors carefully:

| Situation | Recommended treatment |
| --- | --- |
| Disabled, not due, wrong host, fresh lock contention | Explicit skip/defer; no false success timestamp; normally exit 0. |
| Missing today's note or a genuinely pending template | Scheduled wait, not an immediate cron error. Do not create a daily note behind Templater's back. |
| An existing stable note is malformed or has conflicting running sessions | Failure/attention, not an endlessly excused “not ready.” |
| Ref scan held PDFs but no write failures | Partial/held details remain visible; successful checks may advance cadence, but unresolved work cannot disappear into a green full-success record. |
| Gmail archive needs consent | Show the existing actionable confirmation path; never auto-confirm or generate a consent digest on the user's behalf. |
| API/auth failure, invalid JSON, partial write, timeout, unsafe recovery | Failure, preserve evidence; continue independent steps only if mutation has safely stopped. |
| Invalid refresh configuration | Exit 2 before doing any work. |

For a valid pass, exit 1 when a runtime failure or actionable required intervention warrants cron mail; exit 0 for healthy completion and ordinary waits. Preserve the child's specific code in the receipt rather than returning whichever child happened to fail first. Do not suppress Gmail's existing two-hour stale-busy failure. Add per-step staleness visibility and an actionable alert policy for persistent deferrals; silence must not conceal starvation. A newly created day's missing note should not itself become a 00:05 alarm.

Cronrun already logs runs, rotates output, and mails failures. Reuse it rather than creating another mailer or unbounded log store. `-q` hides routine waits but retains actionable failures and can print one concise diagnostic summary. `--status` is the place for all per-step clocks. A Mac Capture health display can consume this receipt later; adding that UI is not required now.

## The exact chezmoi and Mac scheduling change

Once a compatible Bob binary is actually installed on the Mac, replace the four jobs above with this one entry under `cron.jobs` in `home/.chezmoidata.yaml`:

```yaml
- name: bob-refresh
  machines: [mac]
  schedule: "*/5 * * * *"
  description: Run due Bob maintenance with per-step cadence
  command: bob refresh -q
```

Update the nearby comments, which currently describe staggering. Do not add another standalone `bob gcal sync` cron line. Keep the existing vault-sync LaunchAgent and athena nightly job. The config and cron changes belong in the same reviewed chezmoi change, but enabling the new job must follow binary availability.

Use the established cron workflow: validate with `cronctl check --source <checkout>`, inspect `cronctl diff mac --source <checkout>`, and stream that checkout's cronrun to the Mac with `--dry-run bob-refresh 'bob refresh -q'` to check its resolved environment. Also run the installed binary's local-only `bob refresh -d` in that environment, since merely resolving `bob` does not prove the installed version knows the new command or configuration.

Honor the daily release train. Do not manually bump Cargo.toml or CHANGELOG.md to hurry this through. Verify the installed command/capabilities and the compatibility tests, then remove the old jobs and enable the new one together. Before convergence, confirm no old maintenance process is still active: changing crontab does not terminate an existing job. A temporary union of old jobs and refresh defeats the ordering benefit and can create duplicate attempts.

After the change is committed and pushed, converge using the checkout's `cronctl apply mac` in the prescribed SASE post-commit monitor, including the chezmoi-required apply/update workflow. Then inspect `cronctl status mac --all-schedulers`. Completion evidence must say `in_sync`, or honestly report `pending` if the Mac is asleep/unreachable. Never use raw `crontab -e` or `crontab -` for this migration.

The Mac was reachable for this research; that does not guarantee reachability at rollout. Keep failure and pending results distinct. If crontab installation is rejected by macOS permissions, resolve that deployment issue explicitly; do not report it as applied.

Apple recommends launchd for timed jobs and documents missed cron runs during sleep. A `StartCalendarInterval` launchd job can run after wake. Nevertheless, staying with managed cron is the right first implementation here because it matches the explicit request and existing cross-host deployment/logging system. A frequent heartbeat with coalesced due work handles missed maintenance without replacing the scheduler. Consider launchd later only if measured post-wake latency is unacceptable. [Apple, Scheduling Timed Jobs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)

Rollback restores the four prior cron definitions after ensuring refresh is stopped. The newly configured Calendar floor can remain in place to preserve the user's limit. If rolling back to a binary that predates the floor, it may ignore that YAML key; then daily-note/manual callers are no longer covered. Do not claim the hourly guarantee survives an arbitrary binary downgrade.

## What should prove the design before deployment?

Use fake clocks and fake child adapters for scheduler tests, plus real temporary-vault subprocess tests for locking and failure recovery. No production Google account is needed to prove most of the scheduler contract.

| Acceptance case | Required evidence |
| --- | --- |
| Repeated five-minute ticks | Refs/projects respect configured intervals; tasks obey the periodic interval plus their documented coalesced after-changes rule; Gmail/Calendar preserve their own scheduled cadence. |
| Producer writes between task intervals | Tasks run once at the end when enabled/selected, and a persisted follow-up survives a crash or readiness wait. |
| Clock and sleep boundaries | Midnight, DST, restart, late ticks, and a long sleep do not reset the Calendar floor or replay a backlog of missed runs. |
| Calendar competing callers | Cron, the existing plugin-style call, manual sync, `-F`, dry-run, and `-n 2` compete for one admission; failed attempts also count. |
| Daily-note race | No scheduled Calendar quota is consumed before today's note is ready; structured waiting survives a readiness race after preflight. |
| Overlapping refresh invocations | One runner starts children; the other reports busy without corrupting the active receipt. |
| Parent death and timeout | No writer continues unnoticed after a new pass starts; partial/recovery states prevent unsafe continuation. |
| Child error isolation | A normal Gmail network failure does not prevent safe Calendar/task work; unsafe partial writes are reported accurately. |
| JSON result fidelity | No-work, held PDFs, stale receipts, partial failure, malformed output, and missing-note reasons are distinguished. |
| Configuration errors | Unknown IDs/options, empty intervals, invalid hosts, and invalid day counts fail before mutation. |
| Read-only surfaces | Refresh preview/status do not call Google, spawn mutating children, or change scheduling timestamps. |
| Existing callers | Ledger Tools accepts the additive Calendar wait reason; direct commands preserve their documented behavior apart from the explicit configured floor. |
| Deployment | The Mac has the new command before the cron swap; all four old jobs are gone, only one replacement exists, and live state is `in_sync`. |

The missing-note adapter must use structured error reasons or a shared readiness API. Today's reconcile missing-note error has only a message with no reason code. Add a stable reason to that path rather than matching the English sentence. Preserve a real failure for malformed settled notes. Also retain ref scan's clean no-work path and PDF coordination; do not replace them with a filesystem mtime heuristic copied from the old shell wrapper.

Perform existing CLI/help/completion and docs checks alongside relevant integration tests. The project requires generated CLI docs for new flags and `just docs-check`; register the command in the same daily-workflow help/completion grouping. The Calendar policy adds an observable configured behavior change; assess CLI/JSON contract compatibility and use the project's required breaking-change notation if applicable.

## Explicit adjustments to the original idea and earlier review

1. **Name:** use `bob refresh`, not repurposed `bob sync`.
2. **Frequency:** use a five-minute scheduling heartbeat, while preserving 15-minute local work and hourly remote work. The heartbeat is not the work interval. Enabled task reconciliation also runs once after producer changes, an explicit configurable exception to its periodic interval.
3. **Calendar:** its hourly floor applies to failed and direct/plugin attempts, not merely successful orchestrator runs. No implicit manual/force bypass.
4. **Execution:** use supervised, structured subprocess adapters initially rather than assuming in-process functions can be timed out safely.
5. **Failures:** a timeout is a failure; unresolved mutation may stop the pass. “Always reconcile last” is subordinate to safe termination.
6. **Configuration:** enable a fixed allowlist explicitly; do not expose arbitrary commands, user ordering, or a workflow language.
7. **Scope:** Keep remains outside v1. This means the full morning chore is not automatically retired.
8. **Missing daily note:** wait in unattended scheduling, while retaining errors for malformed settled inputs; do not globally turn every reconcile input error into success.
9. **Rollout:** deployment is incomplete until the released/installed binary is compatible and the actual Mac cron state is verified. Configuration edits alone are insufficient.

## Source record and limits

- Requested input: `research:202611/bob_sync_task_review.md`, consumed through `sase artifact read`. Its historical run counts and timing measurements are attributed above, not reproduced as newly collected data.
- bob-cli checkout: `41b1dab3fc95fd0617392e91bed8637834640bf1`. Principal inspected files: `src/native/nightly.rs`; `src/native/config/mod.rs`; `src/native/ob.rs`; `src/native/vault_sync.rs`; `src/native/projects/sync_engine.rs`; `src/native/highlights_ref/scan_apply.rs` and `scan_json.rs`; `src/native/task_status_hooks/{mod,sync,retry,output}.rs`; `src/native/gcal/{sync,snapshot,config,gog}.rs`; `src/native/gmail/sync/{command,health,report}.rs`; `docs/{vault-git-sync,gcal,gkeep,highlights-ref-sync}.md`; `docs/develop/migration-notes.md`.
- chezmoi checkout: `002760c3a9155d98f28645cfdf3bf1b1b8dcd378`. Principal inspected files: `home/.chezmoidata.yaml`; `home/dot_config/bob/config.yml`; `home/bin/executable_cronrun`; `home/bin/executable_maybe_bob_highlights_sync`; `home/Library/LaunchAgents/com.bbugyi.bob-vault-sync.plist`.
- bob-plugins checkout: `b2a6d2bf56963702af02d45da362db0141c1295b`. Inspected Ledger Tools fragments `291-plugin-gcal-events.js`, `291a-plugin-gcal-readiness.js`, `291c-plugin-gcal-event-clock.js`, and `291g-plugin-gmail-sync.js`.
- Live evidence: `cronctl status mac --all-schedulers`, plus read-only SSH hostname/version checks on 2026-11-18. I did not run mutating Bob maintenance commands to gather timings or test credentials.
- Audited memory: `crontab.md`, `tailnet.md`, `sase_artifacts.md`, `cli_rules.md`, `docs.md`, and decisions for read-only Calendar ownership, forced day reset, reference ingestion at birth, and the Bob release train.
- External primary sources: [Apple's timed-job documentation](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html) and [Google's Calendar quota guidance](https://developers.google.com/workspace/calendar/api/guides/quota). Apple’s page is archived; the live Mac inventory is the evidence for this machine's actual scheduler setup.

No claim here establishes a universal hard runtime bound for today's child commands. That requires the timeout/recovery work described above. The report intentionally does not promise that wrapping commands alone creates transactions, removes all contention, guarantees freshness during sleep, or enforces an hourly cap after deliberate local-state deletion.

## Recommended solution

Build **`bob refresh` as a small, finite maintenance controller**, with five explicit steps, persisted per-step admission times, structured results, and one sequential execution order with coalesced task cleanup after producer changes. Preserve each command's own data ownership and locks. Give the user one calm status view that distinguishes successful work, ordinary deferral, and actionable trouble.

Adopt the proposed chezmoi settings: refs/projects/tasks every 15 minutes; Gmail every hour; Calendar every hour for yesterday and today, with **`gcal.min_interval: 1h` enforced inside Calendar sync across all callers**. Replace the four Mac cron jobs with one `bob refresh -q` tick every five minutes only after the compatible binary and safe supervision behavior are verified. Keep vault transport, nightly maintenance, and Keep separate.

Proceed with this scope. It addresses a demonstrated operational problem and makes the system easier to understand. The right investment is trustworthy cadence, outcomes, and recovery—not a more powerful scheduler.

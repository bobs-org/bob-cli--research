# Google Keep in the Obsidian footer: two counts, two refresh speeds

Independent research by **cdx**, 2026-10-31. No other swarm research report or peer findings were consulted. This is a design recommendation, not an implementation or a live-account test.

## Decision in brief

**Build it.** A small indicator can close a real gap between capturing something on a phone and processing it in Obsidian. Show two separately labeled values:

```text
[lightbulb] Keep 3  │  [inbox] Inbox 7
```

“Keep” means **notes eligible for the default pull at the last successful check**. “Inbox” means **non-closed Bob tasks currently resident in the configured inbox note**. They represent different stages and different units; never add them together or imply that three Keep notes will become three inbox tasks.

Put this in `bob-ledger-tools` as an independent status-bar item beside the existing review footer. Let Bob own Google authentication, eligibility, cache, throttling, and errors. Let Obsidian use its existing Tasks cache for the local count. Refresh remotely every **30 minutes with a backlog, 60 minutes when empty**, only while Obsidian is active; provide an explicit Check now action. Local updates should appear within **two seconds** of a saved change, normally much faster.

The important adjustments to the request are: remote “current” must mean timestamped last observation; authentication cannot guarantee a future pull succeeds; and the local inbox count should remain useful even if remote authentication stops working. These are explained below.

## What the existing code establishes

I inspected bob-cli at `061824f8928be73e7756311a370fb508a05da1c5` and bob-plugins at `2ebd58c4ae7b3465c96490210eb8f1ad85870ca1`. References below are pinned to those revisions. I opened the upstream gkeepapi repository through SASE; its inspected revision `1a94b25c18a7abfdc23d1412091129cd63652877` declares version `0.17.1`, matching Bob's dependency version. No credential command, live Keep request, or vault mutation was run.

| Finding | Why it changes the design |
| --- | --- |
| Bob already classifies notes as new, pending, revised, empty, pinned, shared, or archived. | Count default-pull eligibility, not all visible Keep notes. |
| Pending means archive-only; eligible URL-only notes can create references. | The remote number is a count of source notes to process, not future inbox tasks. |
| `list -s vault` avoids Google but still calls `read_vault`, which scans legacy history, import receipts, and the journal. | Do not launch that command every few seconds for a single-file count. |
| `read_target_tasks_with_imports` filters to unindented tasks. | Its array length is not the requested count of all genuine tasks resident in the note. |
| `read_token` invokes a shell command with inherited input/error streams; the default uses `pass`. | A background call can trigger pinentry or block. A no-prompt credential mode is a prerequisite. |
| The adapter restores a state file and authenticates with `sync=True`; its state contains the sync version. | Keep the incremental cache. There is still authentication, network traffic, Python work, and cache serialization per check. |
| `connect` retries without cached state after any non-auth error when state was present. | A temporary network failure or rate limit can currently trigger a second, potentially full synchronization attempt. Background checking needs narrower recovery. |
| Real pulls have a per-host pull lock; ordinary list/snapshot calls do not share that transaction guard. | A new status consumer needs coordination with all users of the adapter state. |
| The review footer is a desktop status item with responsive fitting, tabular digits, keyboard focus styles, and separate lifecycle code. | Extend the established visual system, but keep Keep visibility independent of whether a review queue exists. |

Evidence: [GKeep workflow and configuration](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/docs/gkeep.md), [list and local reads](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/gkeep/list.rs#L30), [task extraction](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/gkeep/ledger.rs#L445), [credential execution](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/gkeep/config.rs#L214), [adapter connection](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/scripts/gkeep_adapter.py#L317), and [footer lifecycle](https://github.com/bobs-org/bob-plugins/blob/2ebd58c4ae7b3465c96490210eb8f1ad85870ca1/plugins/bob-ledger-tools/src/240-plugin-freshness-status.js).

Google's public Keep API is described as an enterprise API, and its `notes.list` response is a page of notes plus a pagination token, not a lightweight total. It is not a drop-in count service for Bob's existing personal-account integration. The supported implementation here remains Bob's pinned, unofficial mobile-API adapter. Do not assume quotas published for Google's enterprise API apply to it. [Google Keep overview](https://developers.google.com/workspace/keep), [official notes.list contract](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes/list), [gkeepapi documentation](https://gkeepapi.readthedocs.io/en/latest/).

## Define the numbers before building the widget

### Keep: default-pull candidates

Define:

```text
Keep count = number of distinct, live notes accepted by the default pull's
             archived → empty → pinned → shared eligibility checks
           = new + revised + pending
```

Use no `--all`, `--include-pinned`, `--include-shared`, explicit selection, or limit. Trashed/deleted notes are already excluded by the adapter. An attachment-only note may be eligible; “empty” must use Bob's existing normalization and attachment rules, not a JavaScript approximation. Count a checklist note once, regardless of its number of items. A source note routed into references still counts once. A pending note still counts because a normal pull has work left to do: archive it.

**A useful simplification:** at this revision, history changes the action but does not change whether a note is actionable after those four skip checks. Therefore the total needs neither a legacy-marker scan nor receipt/journal reconciliation. Extract a pure shared eligibility helper from the planner, use it in both planner and status, and test the equivalence against full plans. Do not copy four predicates into the plugin. This is an inference directly from [the classifier's control flow](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/gkeep/plan.rs#L211).

The tooltip should say “3 notes eligible for the default pull · checked 12 minutes ago.” It can show excluded-note counts derived from the same snapshot. Detailed new/revised/archive-only/reference breakdowns belong in the existing list view, invoked explicitly, because those require more work.

Do not say “3 notes will successfully sync.” A candidate can fail later because a URL cannot be fetched, a reference route needs input, the target is missing, Git cannot commit, a receipt needs recovery, or the note changes mid-pull. The count is a preview of eligibility at an observation time, not a reservation or a transaction guarantee.

### Inbox: resident non-closed tasks

Use the active vault and resolved `gkeep.target`, defaulting to `gkeep_inbox.md`; do not hard-code the absolute `~/bob` path. This preserves what the user asked for in the default setup while following the destination the actual pull uses.

Count every genuine Bob/Tasks task in that file, at any indentation, whose raw status symbol is not `x`, `X`, or `-`. Include blocked, scheduled, Next, Pending, hidden, and custom-symbol tasks. Do not borrow Ready, review, global dashboard-query, freshness, or dependency filters. Count manually added tasks as well as imported ones; source attribution is irrelevant to residence. Moving a task elsewhere removes it from this number even if it remains open elsewhere.

Interpret “task” using the vault's existing task-recognition/global-filter convention (normally `#task`), not every Markdown checkbox. Imported Keep checklist children are not automatically separate Bob tasks. Nested children explicitly authored as real tasks do count. Code examples and frontmatter must not inflate the count.

Treat uppercase `[X]` as closed, consistent with existing GKeep list behavior. This is a small explicit extension of the request's literal `[x]`/`[-]` wording. A custom status mapped to a closed category but bearing another symbol still counts under the requested raw-symbol rule; do not silently switch to status-type filtering.

The plugin already exposes the raw Tasks cache through `planBlockTasks`, so the first implementation can filter that cache by exact normalized file path and status. Missing/unready Tasks data is `Inbox —`, never zero. A missing file is “Inbox missing,” not an empty success. Do not create a file from an indicator. [Existing Tasks cache accessor](https://github.com/bobs-org/bob-plugins/blob/2ebd58c4ae7b3465c96490210eb8f1ad85870ca1/plugins/bob-ledger-tools/src/340-dashboard-views-and-plan-block.js#L726), [existing local status predicate](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/gkeep/list.rs#L304).

## Authentication and honest failure states

“Has a config file,” “has a token,” “token has the expected prefix,” and “Python starts” do not prove Google accepts the credentials. Conversely, a network timeout does not prove the credentials are invalid. Authentication, connectivity, credential-store availability, and pull readiness need separate fields.

Show a numeric remote segment only after a successful authenticated snapshot for the current account/config identity. Persist that evidence so reopening Obsidian does not require an immediate check. A successful existing list, doctor Keep check, login validation, or pull snapshot should also publish it through the same backend path.

| State | Remote display and behavior | Local display |
| --- | --- | --- |
| Never configured or configuration removed | No Keep segment; no network activity | Inbox remains if the note exists |
| Configured, never verified | No numeric Keep segment; setup/check available in commands/settings | Independent count |
| Verified, fresh | `Keep 3`; time in tooltip | `Inbox 7` |
| Verified, stale or transient network failure | `Keep 3 ◷`; tooltip says last checked time and reason | Continues updating |
| No usable observation, or observation older than 24 hours | `Keep —`; last known number only in details | Continues updating |
| Google explicitly rejects credentials | Hide numeric Keep segment; pause automatic checks until explicit recovery/config change | Continues updating |
| Secret store is locked or background retrieval is unsupported | Preserve age-marked last observation if available; explain “Check requires unlocking” in details | Continues updating |
| Known local pull setup problem | State it in details; any pull action is unavailable or directs to setup | Show count or missing-file state truthfully |

Do not silently hide the entire feature when Wi-Fi drops; that would make a forgotten remote backlog disappear precisely when the indicator is least certain. Do not replace failures with zero. If authentication is explicitly rejected, expose the reason in a command/settings diagnostic and optionally one deduplicated notice after a previously working connection fails. No periodic error toasts.

**Requirement adjustments:** retain a clearly stale remote observation through transient failures, and retain the local count independently of Google authentication. A literal “visible only while a pull would actually work right now” cannot be guaranteed without continually executing the operation, and even a successful check cannot guarantee the next write. The practical promise is “authenticated at the stated check time, with no subsequently known credential rejection.”

### Make background credential access safe before enabling polling

The current `token_command` is arbitrary shell code and may invoke a graphical pinentry. Closing stdin alone does not prevent that. Give background status a separate, bounded credential-provider mode. For the default `pass` integration, use a provider path that enforces noninteractive GPG behavior; `--batch`, `--no-tty`, and `--pinentry-mode error` are relevant primitives, with locked-store behavior verified in tests. GnuPG documents that `error` returns a pinentry error instead of invoking a prompt. [GnuPG options](https://www.gnupg.org/documentation/manuals/gnupg26/gpg.1.html).

Do not pretend to make an arbitrary configured command noninteractive by setting an environment variable it may ignore. Require an explicitly supported background provider or an explicitly configured background-safe command. Otherwise use observations published by manual commands and make Check now an explicit foreground action. Bound the credential subprocess tree, scrub error text, and never cache the master token in plugin data or the count document. This is the principal implementation prerequisite, not a cosmetic refinement.

## Refresh policy: spend work where the result can be used

### Local updates

Subscribe to relevant vault/metadata changes, including create, modify, delete, and rename both from and to the configured target. Recount after the Tasks cache reflects the change; use a short coalescing debounce (about 250 ms) and, if needed, a bounded retry for cache lag. Revalidate on startup, focus, configuration change, and successful pull completion. Accept up to two seconds after a saved local or externally synchronized edit, and measure that target on the Mac.

There should be no recurring CLI call, Python process, Google call, or vault scan to update this count. Unrelated note edits should not trigger a recount. Pending editor text may be reflected if the existing cache provides it, but the guaranteed count is of saved content; do not add a second ad hoc parser merely for a keystroke-level preview. If a fallback becomes necessary for deployments without Tasks, add a dedicated single-note parser path in Bob rather than reuse `gkeep list -s vault`.

Obsidian recommends `cachedRead()` for display-only file reads, and Apple recommends change notifications instead of timers for file changes. These support an event-driven local path; they are not measurements of this plugin's performance. [Obsidian Vault guidance](https://docs.obsidian.md/Plugins/Vault), [Apple timer guidance](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/Timers.html).

### Remote updates

Recommended defaults are design choices, not claimed Google quotas:

| Trigger | Policy |
| --- | --- |
| Obsidian startup | Paint the cached observation immediately; after layout settles, check only if due and background credentials are usable |
| Foreground/focus return | Check only if due; focus is not permission to bypass the cooldown |
| Active session with positive backlog | One check every 30 minutes, with 0–3 minutes of positive jitter |
| Active session after a verified zero | One check every 60 minutes, with positive jitter |
| Hidden, unfocused, sleeping, or closed | No scheduled remote checks; recompute a due time on return, with no catch-up burst |
| Explicit Check now | Bypass normal age interval, but deduplicate an in-flight check and enforce a 60-second manual debounce plus any server backoff |
| Local task edit | No remote call |
| Existing successful Keep command | Reuse its observation and reset the due time; do not immediately fetch again |
| A pull finishes | Publish its known outcome/invalidate its prior observation; never blindly set the remote count to zero |

At most roughly 8–16 routine checks fit into an eight-hour continuously active session, plus explicitly requested operations. A check is not one HTTP request: authentication and pagination/full recovery can add requests. Actual traffic, latency, and energy cost need measurement. The 60-minute empty interval deliberately accepts slower discovery of the first new capture; Check now covers immediate use. If that delay proves annoying, use a fixed 30-minute interval before considering anything faster.

Use a one-shot due timer instead of a heartbeat. Persist `next_check_at`, failure state, and last attempt so reloads and multiple Obsidian windows do not defeat throttling. One focused-window owner schedules; the backend still enforces eligibility to check under a cross-process lock. Keep status host-local; do not put it in Git-synced vault JSON or create a server daemon just for this feature.

On transient network/server failures, back off approximately 5, 15, 30, then 60 minutes, adding jitter and capping retries. A known rate limit should start at a longer delay (for example 60 minutes), honor server retry guidance if available, and remain non-bypassable from repeated clicks. Credential rejection pauses automatic attempts until explicit recovery. A locked secret store is a distinct recoverable state, with bounded retries or a foreground-unlock event, not a reason to run login repeatedly.

The current adapter's broad retry-without-state behavior should be narrowed for background checks: only a genuine invalid-state/resync condition merits one full refresh. Do not discard an otherwise useful cache on timeout, 429, or ordinary network errors. The adapter currently does not expose a structured Retry-After field, so honoring it would require protocol work; meanwhile use conservative persisted backoff. Account/config changes invalidate both the status observation and any incompatible adapter state.

## Small backend contract, independent footer component

Add a read-only `bob gkeep status` contract rather than repeatedly invoking list, doctor, or pull dry-run. A proposed public form is `bob gkeep status -f json`; an explicit `-r/--refresh` asks for a due background-safe refresh. The default is cache-only and must not invoke credentials or network. An explicit force/check mechanism can be added with a documented short alias; exact option names should follow the repository's CLI rules and command-catalog conventions.

An illustrative response is:

```json
{
  "schema_version": 1,
  "ok": true,
  "configured": true,
  "target": "gkeep_inbox.md",
  "auth": {"state": "verified", "verified_at": "2026-10-31T10:00:00Z"},
  "keep": {
    "count": 3,
    "observed_at": "2026-10-31T10:00:00Z",
    "state": "fresh",
    "next_check_at": "2026-10-31T10:31:00Z"
  },
  "last_error": null
}
```

`ok` means the status request was handled, not that a pull is guaranteed. Unknown count is `null`, not `0`. Include a stable typed reason for stale, unavailable, locked, rejected, setup, protocol, and rate-limit states. Do not send note bodies, titles, account credentials, or token commands to Obsidian. The plugin computes the local count separately; backend availability must not gate that count.

Store only the aggregate observation, relevant identity/schema version, attempt timestamps, and scheduling/error state in a private host-local document. Keep the existing private gkeepapi state for incremental synchronization. Identity must include account/device context and config generation without logging secrets. Invalidate on account switch and reject obsolete results that complete after switching accounts or vaults. Preserve the last successful document atomically when a request fails.

Coordinate every adapter-state user, including list, doctor, login validation, pull, and new status. Use a narrow account-state lock around adapter operations; status should return cached/busy rather than wait behind a long foreground operation. Define a consistent lock order and a generation/transaction marker so a status result cannot overwrite a newer pull outcome. Do not hold the vault maintenance lock across a network check.

The underlying gkeepapi synchronization method uploads dirty local nodes as well as downloading changes. A read-only status operation must restore clean synchronized state, make no note mutations, and never use a cache containing uncommitted local edits. Keep archive mutations confined to the existing guarded operation. This is why directly parsing or manipulating the Python cache from the plugin is the wrong boundary. [Upstream synchronization implementation](https://github.com/kiwiz/gkeepapi/blob/1a94b25c18a7abfdc23d1412091129cd63652877/src/gkeepapi/__init__.py#L1064).

Reuse successful observations from existing commands. After a real pull, derive a residual only from confirmed archive outcomes and clearly preserve the time represented by that observation. Partial, ambiguous, interrupted, or changed-during-pull results should leave an invalidated/uncertain count, never an optimistic zero. `--no-archive` legitimately leaves eligible notes in Keep and therefore can leave the remote count unchanged. The next due check reconciles server truth; a partial failure need not cause an immediate extra full sync.

## Visual and interaction design

Use one calm, two-segment status item with native outline icons, a hairline divider, and tabular numerals:

```text
Healthy:       [bulb] Keep 3     │ [tray] Inbox 7
Stale remote:  [bulb] Keep 3 ◷   │ [tray] Inbox 7
Remote unknown:[bulb] Keep —    │ [tray] Inbox 7
Local only:                       [tray] Inbox 7
All clear:     [bulb] Keep 0     │ [tray] Inbox 0
```

These are wireframes; implement the bulb/tray/clock with Obsidian's icon API rather than platform-dependent emoji. Give the bulb and positive remote count a restrained warm accent, and the local tray/count the normal theme foreground. Text and icon shape distinguish the counts without color. Use the current footer's interface font, roughly 12 px sizing, and focus styling. No bouncing badges, red urgency, continuous spinners, or success confetti. Positive numbers indicate available work, not overdue obligations.

Keep authenticated zeroes visible but subdued. Otherwise a disappearing item could mean either “all clear” or “broken.” Keep layout stable while checking; do not reset digits to dashes on every refresh. Updating status should repaint only when values or states change; compute detailed age text on hover/focus rather than running a second-by-second clock.

Click **Inbox** to open the configured note, ideally its first non-closed task. Click **Keep** to open a small accessible menu/popover showing the cached count, last checked time, Check now, View Keep list, and Pull from Keep. Opening the menu itself must not contact Google. Pull should enter the existing Command Mode preview/execute flow, not start a write on a single footer click. That flow already catalogs `gkeep-pull` as `PreviewFirst` with task/reference invalidation. [Command catalog](https://github.com/bobs-org/bob-cli/blob/061824f8928be73e7756311a370fb508a05da1c5/src/native/catalog/table.rs#L915).

Both segments need keyboard activation, clear accessible names, focus-visible styling, and tooltips available on focus as well as hover. Do not make a hover tooltip the only place to discover stale status. Avoid a live-region announcement every refresh. If Command Mode is unavailable, retain navigation/check functionality and show the CLI command as the fallback action.

Place the item beside, not inside, the review footer: it should survive an empty review queue or a temporarily unavailable review engine. Test narrow windows and popouts with the existing review footer. Prefer dropping secondary labels at the narrowest width while retaining both icons, counts, and full accessible names; never collapse them into an ambiguous `3/7`. Use a minimum compact width and the review footer's existing fitting behavior, not a new overlay. Validate light/dark themes, high contrast, and 200% zoom. Desktop only for the first version.

## Critique and alternatives

This is a good feature if it helps decide between **collecting from Keep** and **processing what is already here**. It becomes a bad feature if the remote badge is treated as a live operational guarantee or another demand to keep all counters at zero.

| Approach | Assessment |
| --- | --- |
| Full list/doctor every few seconds | Reject: unnecessary credential prompts, network work, whole-vault history reads, and confusing error semantics. |
| Poll pull dry-run | Reject as the routine backend: it performs far more planning than an aggregate count requires, even though it avoids committing tasks. |
| Automatic pulling on a timer | Reject for this request: changes the workflow and can clip references, write tasks, commit, and archive source notes. Observation should not become ingestion. |
| Plugin talks directly to Google | Reject: duplicates authentication and private API logic, scatters secrets, and risks disagreement with Bob's pull rules. |
| Permanent server-side poller/notifications | Defer: more scheduling, credentials, and cache distribution than one desktop footer warrants. |
| Manual-only remote observations | Good low-risk first increment, but stale after phone captures unless the user explicitly checks. Label it honestly. |
| Morning-review-only reminder | Simpler and lower noise if the user finds the always-visible counts distracting; it is a valid fallback product choice. |
| Cached remote observation plus event-driven local count | Recommended balance of usefulness, predictable cost, and maintainability. |

Avoid expanding v1 into a source-note browser, synchronization dashboard, generalized inbox service, or fresh authentication UI. The existing CLI/Command Mode remains the place for detailed reconciliation and repair.

## Verification and delivery shape

These are proposed acceptance checks, not tests already run against an implementation:

1. **Semantic equivalence:** for ordinary, revised, pending, URL-only, image-only, blank/zero-width, pinned, shared, archived, trashed, and deleted fixtures, the status total equals default planner actionable count. Include overlapping skips and one checklist with many items.
2. **Local semantics:** mixed and custom statuses, uppercase X, nested genuine tasks, untagged checkbox children, hidden/scheduled/blocked tasks, code examples, frontmatter, task moves, and target override. Missing file/cache and read errors never become zero.
3. **Authentication:** fresh setup, revoked token, changed account, locked `pass`, unsupported custom token command, missing uv, cold dependency environment, and failed recovery. No background prompt; no secret in JSON, logs, process arguments, or cache.
4. **Scheduling with a fake clock and adapter:** repeated focus, reload, multiple windows, sleep/resume, rapid Check now clicks, zero-to-nonzero transition, rate limit, network failure, full-resync demand, and clock jumps. Verify no Google calls on local edits and no catch-up storm.
5. **Concurrency/crash behavior:** status versus list/pull/doctor, cache replacement, old response after account switch, partial archive, `--no-archive`, and process termination. Foreground pull wins; stale count publication cannot clobber a newer result.
6. **Mac usability/performance:** saved local changes visible within two seconds; remote work off the UI thread; stable status layout during loading; no Python startup in the local path. Measure warm/cold remote duration, bytes, process count, and library-size effect before claiming the chosen interval is cheap.
7. **Presentation:** zero/unknown/stale/rejected/missing states in light/dark themes, keyboard and screen-reader names, narrow footer beside review, popouts, and zoom. A click cannot accidentally import/archive notes.

Implement first the shared eligibility helper and versioned status/cache contract, with background credential and adapter-state safeguards. Then add the separate plugin footer and event-driven local count. Initially shipping cache-only remote observations is acceptable if noninteractive credentials are not yet robust, provided it is explicitly labeled as that reduced first increment. Enable the active-session scheduler only when its no-prompt and backoff tests pass. Follow the plugin repository's fragment build, validation, and `bob plugins sync` deployment workflow when implementation actually occurs.

No live credentials or personal note contents were needed for this research. CPU/battery impact, the personal API's practical request tolerance, and exact theme behavior remain unmeasured. The proposed defaults should be adjusted from observed use, not presented as externally guaranteed limits.

## Recommended solution

Ship a **two-segment Keep/Inbox footer in bob-ledger-tools**. Compute the local count from existing recognized tasks in the configured note, updated on relevant events within two seconds. Add a small Bob-owned status API that counts default-pull eligibility through a shared planner helper, persists a timestamped aggregate, and reuses manual-command observations. Check Google only while Obsidian is active, at 30 minutes for a backlog and 60 minutes for an empty inbox, with an explicit Check now action, persisted backoff, safe noninteractive credentials, and coordinated adapter access.

Keep the remote number honest about age and uncertainty, keep the local count useful during remote outages, and route ingestion through the existing previewed pull workflow. That delivers the useful part of the request with a quiet visual design and a bounded cost, without pretending that a cached count guarantees a future synchronization will succeed.

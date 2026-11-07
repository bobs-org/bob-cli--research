# Gmail follow-up tracking in Bob: one thread, one task, an explicit wait

Independent research by **cdx**, 2026-11-07. This report uses the supplied request,
the current implementation, the approved crontab plan, and primary public
documentation. I did not consult the other researchers or their reports.

**Recommendation.** Add `bob gmail sync` as a read-only Gmail reconciler: the
`bob` label enrolls a thread, an optional prefixed label chooses its task's
initial home, and one durable watch follows that task until it is completed or
canceled. A sent message starts a three-calendar-day follow-up wait; a qualifying
incoming message ends that wait and resurfaces the task for review. Use Bob's
existing Blocked checkbox with a new envelope mark, not another task status.
Keep ordinary user scheduling separate from the email follow-up date.

This is a good feature for a deliberately selected set of conversations. Its value
is removing repeated remembering and checking. Its danger is pretending that message
traffic proves a human obligation was satisfied. Bob should report **“Reply
arrived”**, not **“Resolved”**, and should never decide that a conversation is done.

This is research, not an implementation change. Configuration and cron snippets below
are proposals; I have not changed the live vault, Gmail, configuration, or schedules.

**1. What the existing system already gives us**

The checked-out Bob CLI revision is
`30841c2912519dace8d8bd75d2909f6f044a99e1`; bob-plugins is
`2563c7898644d1f784c13f3eefa698285ae4a381`; the inspected chezmoi revision is
`102e8238aa24840afa0783d5d497e1bbbde4f66e`. These are research snapshots, not
claims about the latest deployed binaries.

| Existing behavior | Design consequence |
| --- | --- |
| `gmail pull` searches the configured label, saves a thread, and adds one task to an inbox. It skips identities in `gmail.pulled`. | This is enrollment machinery, not ongoing synchronization. |
| Pull defaults to 20 results and allows at most 500 per invocation; its current path calls a single search. | Do not inherit that bounded search as a complete watcher. Old labeled threads can otherwise starve behind already-imported results. |
| Mail notes are keyed by account and thread ID. Refresh appends new message cards and preserves authored material. | Reuse the note renderer and merge logic; keep the conversation separate from its action task. |
| The Gmail adapter already exposes thread metadata, paginated search, label names/IDs, and full thread reads. | A modest polling implementation needs no new service or OAuth write capability. |
| A per-host vault-synced Gmail journal already exists. | Extend its schema and fold; do not make a host cache the only record of enrollment or closure. |
| Task blocking has explicit dependency, project, and schedule reasons. | Email waiting belongs in that reason model, not a direct checkbox rewrite. |
| Plugins already paint blocking reasons inside the checkbox. | Extend the established rendering API, precedence, and conformance tests. |
| Freshness distinguishes NEW, scheduled returns, automatic unblocks, and daily lane reviews. | New mail needs a deliberate review signal; changing the saved note alone is insufficient. |

Evidence: [pull implementation](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/pull.rs),
[Gmail adapter](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/gog.rs),
[mail merge](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/note/merge.rs),
[Gmail journal](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/journal.rs),
[blocking model](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/project_dependencies/blocking.rs),
[freshness evaluator](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/freshness/state.rs),
[blocked-mark contract](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/docs/blocked-marks.md).

The accepted decision `decisions:task-lanes-are-sticky`, read through audited memory,
explicitly rejected a separate Waiting/Submitted status and a hidden previous lane.
`decisions:unblocked-tasks-resurface-as-ticklers` preserves human freshness stamps;
`decisions:unblocked-tasks-are-offered` keeps recovery separate from planning work
into today's ledger. The design below follows those boundaries. In particular, a
reply does not automatically make a task Next, restore its former lane, or link it
to a Pomodoro.

The audited `bob-cli-ib` epic was still in progress: phases 1–4 were closed, while
documentation and fleet cutover were in progress. Its approved
`plan:202611/crontab_as_code.md` makes
`home/.chezmoidata.yaml → cron.jobs` the scheduler source of truth.
The inspected checkout already contains the schema, renderer, `cronrun`, and
`cronctl`, but `jobs: []` at that revision. Merge against the epic's eventual
landed configuration instead of overwriting this placeholder.
The source Bob config currently contains no active `gmail:` block; that does not
prove the deployed Mac lacks local Gmail settings.
See [cron data](https://github.com/bbugyi200/dotfiles/blob/102e8238aa24840afa0783d5d497e1bbbde4f66e/home/.chezmoidata.yaml),
[runner](https://github.com/bbugyi200/dotfiles/blob/102e8238aa24840afa0783d5d497e1bbbde4f66e/home/bin/executable_cronrun),
and [Bob configuration](https://github.com/bbugyi200/dotfiles/blob/102e8238aa24840afa0783d5d497e1bbbde4f66e/home/dot_config/bob/config.yml).

**2. Gmail constraints that materially change the design**

Labels belong to messages. A thread's labels are the union across its messages,
and later messages do not inherit labels applied earlier. Therefore, use `bob`
to discover enrollment, then fetch watched thread IDs whether or not the latest
message has either label. A filter for “new messages carrying bob” is insufficient.
Removing `bob` after enrollment should not silently abandon an open task.
[Google's label semantics](https://developers.google.com/workspace/gmail/api/guides/labels).

Do not require `bob` and `#/job` on the same individual message. Discover with the
enrollment label, fetch the thread, then examine the union of message label IDs.
Google documents differences between UI and API searches, including alias expansion
and thread-wide search. Avoid encoding the whole routing policy in one Gmail search
expression. [Search behavior](https://developers.google.com/workspace/gmail/api/guides/filtering).

Use message IDs for deduplication and Gmail `internalDate` for ordinary chronology,
not message counts, the sender-authored Date header, or unread status. Equal times
need a deterministic tie policy and reply-header evidence. Imported mail can have
special timestamp behavior; malformed or ambiguous chronology must not silently
reset a wait. [Message resource](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages).

A paginated enrollment scan must follow `nextPageToken` to completion.
The API's maximum page size of 500 is not a mailbox limit.
[Thread listing](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.threads/list).

Automatic replies deserve different handling. `Auto-Submitted` provides a
standard signal that a message was generated automatically. It is evidence, not
a universal detector: absence does not prove a human wrote the message.
[RFC 3834, section 5](https://www.rfc-editor.org/rfc/rfc3834).

**3. Routing: one initial home, exact matching, useful errors**

Configure the prefixes as literal strings `["#", "+"]`. Match
`prefix + "/"` exactly; strip that prefix and separator once. The result is a
note stem. Thus `#/job` routes to `<vault>/job.md`, where the vault comes from
Bob's normal configuration, including `BOB_DIR`, rather than a hard-coded home
directory. Either prefix can address either an area or a project. The request did
not assign different semantics to `#` and `+`.

Use these rules:

| Labels and target | Result |
| --- | --- |
| `bob`, `#/job`; `job.md` is an area | Create or adopt one watch task in `job.md`. |
| `bob`, `+/launch`; `launch.md` is an open project | File in `launch.md`. |
| `bob`, `#/job`, `+/job` | One resolved destination, one task. |
| `bob`, `#/job`, `+/launch` | Ambiguous destination: reject enrollment and list both choices. |
| `bob` alone | Use the configured Gmail inbox area, preserving today's simple filing gesture. |
| Routing label without `bob` | No enrollment. |
| Recognized route points to missing/wrong-type note | Loud per-thread error; no inbox fallback or success marker. |
| Recognized route points to a closed/canceled project | Reject by default; do not silently put open work into a completed project. |

“Loud” should mean a typed error containing the label, expected path, and reason,
a nonzero run result, a doctor entry, and visibility through cron logs. Other valid
threads can still reconcile; one typo must not freeze every wait.

Validate actual frontmatter through Bob's normal note-type resolver:
`type: "[[area]]"` or `type: "[[project]]"`. Do not guess from the filename,
heading, or prefix. Use the existing task insertion/grouping path under
`## Tasks`, with a stable block ID. Do not create an area/project for a misspelled
label. The special fallback inbox can retain its existing supported creation rule.

For v1, accept root note stems only. Reject empty stems, path separators remaining
after the prefix, dot traversal, control characters, and symlink escapes. Do not
interpret `#/work/job` as either `job.md` or `work/job.md` silently. Case and
Unicode matching must follow the vault's resolver and reject ambiguity consistently
across Linux and macOS. Gmail nesting is a naming convention here, not a trusted
filesystem path.

**Adjustment: an empty prefix list disables label-based routing**, leaving enrollment
into the configured inbox. I would not inspect all arbitrary user labels as routing
instructions by default. A label named “Receipts” should not unexpectedly start
writing to a coincidentally matching project, and “fail loudly for invalid routes”
would become noisy if every organizational label were treated as a route. An
explicit future bare-label mode is possible, but unnecessary for your `#`/`+`
workflow.

Routing controls the initial home. Once created or adopted, the task's current
residence is authoritative. Moving the task in Obsidian must work; later label
renames or additions must not move it back. Report a route discrepancy in a
read-only preview and leave any relocation to an explicit move. This intentionally
avoids a second automatic filing authority.

**4. The lifecycle: distinguish waiting, action, and closure**

There are two layers: watch lifecycle (`active`, `closed`, `orphaned`) and
conversation condition (`action`, `waiting`, `follow_up_due`). These are mail
integration facts, not additional Tasks statuses.

| Event | Watch and mail condition | Task result |
| --- | --- | --- |
| New enrollment; latest relevant message inbound | Active / action | New unstamped task with mail-note link. |
| New enrollment; latest relevant message is a real outbound send | Active / waiting, or already due | Follow-up date is based on that send, even if it predates enrollment. |
| New outbound send to external recipients | Active / waiting | Set reply follow-up date to send date + configured days; derive Blocked while future. |
| Repeated poll, same outbound message | Unchanged | Never slide the follow-up date forward. |
| Additional real outbound follow-up | New waiting cycle | Restart from the new send date. |
| Qualifying inbound response | Active / action | Remove email wait only; append mail card and surface “Reply arrived.” |
| Follow-up date arrives without a response | Active / follow_up_due | Email hold expires; return to review if other blockers allow it. |
| User chooses “Wait 3 more days” | Active / waiting | Set a new explicit follow-up date from today. |
| User completes or cancels task | Closed | Record terminal state; stop automatic refresh and never recreate it from the label. |
| Task cannot be found | Orphaned | Report and preserve state; do not interpret deletion as completion or create another task. |
| User explicitly reopens the canonical task | New active generation | Resume after a current remote snapshot; old events cannot resurrect an earlier generation. |

Examples use the configured `America/New_York` date: sent November 7 means
follow up November 10, not 72 hours after the next cron tick. Calendar days are
predictable and match Bob's date-based review. Business-day rules can come later;
there is no need for a holiday calendar in v1. A six-day outage must not grant a
fresh three-day grace period.

No-response expiry does not mean someone replied. The task should say “Follow up
due · no reply since Nov 7.” It is now actionable even though the conversation is
still awaiting a response. Leaving it Blocked indefinitely would prevent the exact
GTD behavior requested.

A human can read and acknowledge the task without sending. That acknowledges the
review signal, but does not close the watch. Normal freshness then applies. The
task card should offer Open mail, Wait until, and the existing Done/Cancel actions.
There is no automatic follow-up email, draft creation, or inferred abandonment.

**5. Waiting must not take ownership of the user's ordinary schedule**

There are three credible storage approaches:

| Approach | Benefit | Cost |
| --- | --- | --- |
| New Waiting checkbox status | Immediately recognizable in raw Markdown | Expands every parser and query; conflicts with accepted lane design. Reject. |
| Reuse `scheduled`, record Bob's last written value | Small implementation; existing date machinery works | Reply cleanup must distinguish human dates, email snoozes, priority rolls, project propagation, and equal-value edits. |
| Separate email follow-up date, added to blocking/review engines | Each fact has one owner; reply clears only email waiting | Requires coordinated CLI, freshness, task-card, and plugin changes. Recommend. |

The second approach can be a bounded prototype, but equality with the last value
Bob wrote does not prove the user still delegates that date to Bob. A user can
choose the same date intentionally. A hidden saved prior schedule also invites
stale restoration. This feature will be more trustworthy with distinct inputs.

Use a task field such as `[mail_wait_until:: 2026-11-10]` as the proposed email
follow-up input. Naming is provisional; the semantic contract is the recommendation.
Keep normal `[scheduled:: ...]` entirely user/ordinary-task owned. The effective
blocking predicate becomes:

```text
open dependency
OR blocked project/ancestor
OR scheduled > today
OR mail_wait_until > today
```

The displayed effective earliest return is the latest applicable date, qualified
when non-date blockers remain. “Wait until” in the mail section edits
`mail_wait_until`; the ordinary schedule picker continues editing `scheduled`.
This is an intentional interpretation of “schedule the task”: it creates a
follow-up hold and review date without overwriting the task's other scheduling
intent.

On inbound mail, remove `mail_wait_until` but preserve ordinary schedule,
dependencies, project blocking, title, priority, authored children, and freshness.
If another blocker remains, the task stays Blocked and the pending reply signal
waits until the task is eligible. Make that visible: “Reply arrived · scheduled
for Nov 15.” No promise that mail overrides every other reason.

Local reconcile must understand and expire the field without Gmail access. That
means a network outage cannot keep an already-due wait blocked forever. Email hold
activation must also use the existing blocked-task link-consumption rules rather
than leave a Blocked task in today's open Pomodoros. Do not restore a hidden prior
Next/Pending lane on arrival; use the accepted recovery policy.

This costs more than adding a cron script. It is the principal implementation
scope adjustment, and it should be accepted explicitly during design review.

**6. A reply should cause a review event, not merely an unblock**

When a qualifying message arrives:

1. Append its card through the existing mail-note merge, preserving Notes, Reply
   drafts, attachments, and hand edits.
2. Clear the mail wait associated with the superseded outgoing cycle.
3. Record one pending mail-update event tied to the message ID.
4. Recompute all blockers and the existing recovery status.
5. Surface the task with “Reply arrived · Alex · today,” linking to the conversation.
6. Stop there: no freshness stamp, automatic priority increase, completion, or
   addition to today's ledger.

Keep the main task title stable. A useful generated starting title is “Handle
[subject]”; a human's replacement is theirs. Updating a compact managed child
summary or rendered annotation is safer than replacing task text on every message.
Never generate an obligation or summary with an LLM in the synchronization path.

**The difficult review edge case:** the task may already have become Ready because
the deadline passed, or it may have been reviewed earlier the same day. In either
case there may be no Blocked → Ready transition. Simply reusing `[unblocked::]`
therefore misses replies; stamping `[fresh:: today]` would hide them.

Add a pending mail-event input to the shared freshness evaluator. A possible
line-local projection is `[mail_update:: YYYY-MM-DD]`, with the actual applied
message IDs in the watch journal. Its presence means “unacknowledged new mail”;
the date is display information, not a unique event identity. Human review
acknowledges and removes the projection. Applying a distinct later message
reintroduces it even on the same date.

For confirmed Ready tasks, use TICKLER with an explicit `returned_by: mail`
reason. Unstamped tasks remain NEW. For Next/Pending tasks, preserve the lane but
make an unacknowledged mail event due in that lane even if today's stamp would
normally suppress it. Explicitly disabled lane walks, `#hide`, future ordinary
schedules, and other blockers remain respected and must be reported as suppression,
not silently overruled. Multiple unreviewed incoming messages coalesce into one
task notification with a count. Reviewing clears the event without incrementing a
Rotten keep streak or opening a decay card.

Expiry of `mail_wait_until` must likewise be a return input in the freshness
model. A human stamp after the expiry acknowledges that return, as with existing
scheduled ticklers. Do not depend solely on observing a checkbox transition:
recovery may have occurred on another host or through another writer.

These are additive review semantics, not behavior already present in the inspected
evaluator. Implement the Rust and JavaScript rules from shared conformance vectors,
including two replies separated by a review on the same calendar day.

**7. Determining whether a message is ours, a reply, or just noise**

Start with deterministic metadata, not unread status or text classification.

- Ignore DRAFT messages; saving a draft or scheduling a future Gmail send is not
  evidence that the message was sent.
- A non-draft SENT message with external recipients is strong outbound evidence.
  Supplement it with configured own addresses and the account's send-as aliases.
  Explicitly exclude self-mail from reply detection.
- Compare message identity, `internalDate`, RFC Message-ID, In-Reply-To, References,
  and participant addresses. Prefer a direct reference to the awaited outbound
  message; otherwise accept a later non-self human message in the same Gmail
  thread as “New mail,” without claiming a particular question was answered.
- Default to **any external human response in the watched conversation** ending
  the wait. This matches thread-level tracking. A future per-person requirement
  should be an explicit option; “all To/Cc people must respond” is unsuitable as
  the default.
- A new send to only a changed audience, or an unrelated forwarded branch, does
  not prove the earlier recipient responded. Treat a clearly separate branch as
  context and flag ambiguous cases for review. One task cannot reliably model
  several independent outstanding asks; create separate tasks/threads for those.
- Auto-replies and receipts append context without clearing or extending the
  wait. Never parse an out-of-office return date into a new deadline automatically.
- Delivery failures are actionable exceptions: surface “Delivery failed” for
  review and end the mail hold on that failed send; do not call them replies.
  Use structured delivery-report MIME/header evidence. An unclear error-shaped
  message should be visible for review without claiming delivery status.
- If metadata cannot establish direction or order, retain the last safe wait,
  append available context, and expose a diagnostic. Never guess that all is well.

Gmail's send-as listing supports the readonly scope, so aliases need not require a
new write grant. The current Bob adapter needs an explicitly allowed read method
for this; do not assume it already exposes one.
[Send-as API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.sendAs/list).

The current mail-card renderer identifies “You” by comparing From with the account
address. Share the improved identity classifier with it so alias sends do not
appear as received mail while the watcher treats them as ours.
[Current card classification](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/note/layout.rs).

If inbound A and outbound B both arrive between polls, fold them chronologically
and apply the resulting current condition once. B generally means a new wait.
Do not briefly unblock, consume review signals, and reblock through several writes.
Historical newly discovered messages older than the active cycle may extend the
archive but must not restart or resolve that cycle.

No metadata heuristic proves a “Thanks!” requires an answer. Under this design,
any explicit real send in a still-open watched conversation starts the default
wait. If that send ended the conversation, completing the task is the clear
opt-out. This is the main behavioral tradeoff to test in daily use.

**8. Durable state and safe reconciliation**

Reuse `.bob/gmail/<host>.jsonl` for body-free watch events and maintain the existing
mail-note identity index. Recommended durable information:

| Record | Purpose |
| --- | --- |
| Account + Gmail thread ID | Stable conversation identity; never subject or Gmail URL alone. |
| Watch token + generation | Stable task association and deliberate reopen boundary. |
| Canonical task block ID and last known note path | Move recovery; path is a hint, not sole identity. |
| Enrollment and closure/orphan events | Prevent recreation and distinguish missing from closed. |
| Applied message IDs / cycle's outbound ID | Replay safety; restarting the CLI does not reset a timer. |
| Follow-up date and its source send | Explain a wait and recover interrupted projection writes. |
| Last successful remote observation | Show stale data truthfully; never imply a failed poll succeeded. |
| Pending/acknowledged mail-event identity | Prevent repeat review signals for the same message. |

A task-local opaque `[mail_watch:: ...]` token makes moves and recovery explicit;
the mail note retains account/thread identity. Project only the fields needed for
local blocking/review onto the task. Put Bob-only fields before the trailing
Tasks-format fields, so an unknown field does not break Tasks' right-to-left field
parser. Use ordinary block IDs and preserve them across task moves.

One canonical watch task per account/thread is the default. Plain backlinks from
other notes are references, not extra watches. Duplicate tokens, duplicate mail
identities, or multiple plausible owner tasks are conflicts to report, not an
invitation to pick the first row.

The journal is event history, while the current task is authoritative for human
closure and current residence. Human changes to a wait date override a projection
until a genuinely newer send starts a new cycle. Use versioned operation IDs and
generation checks; do not resolve everything with last-writer-wins wall-clock
timestamps.

A poll should work as follows:

1. Validate configuration, writer identity, and vault readiness. Acquire a short
   process/account sync guard so manual invocation and cron cannot race.
2. Read the task/watch index, including archived closed tasks, before any remote
   update. Fold closures first and omit them from active fetching.
3. Discover new enrollments using paginated label search; fetch labels once and
   route only candidates. Refresh active thread IDs directly regardless of labels.
4. Fetch metadata outside the vault maintenance lock. Fetch bodies only for new
   message IDs or a requested repair. Apply `never_save` policy on refresh as
   well as initial import; policy failure pauses that thread visibly.
5. Compute deterministic per-thread plans with expected task/mail-note bytes.
6. Take the existing vault lock; re-read touched files and revalidate task closure,
   identity, residence, and expected contents. Replan or defer conflicts.
7. Persist a recoverable operation record, apply the staged note/task changes, and
   record the applied IDs. Commit changed vault paths together when possible.
8. Release locks and emit a compact report. A successful unchanged poll is a true
   no-op; do not create a vault commit or journal heartbeat every 15 minutes.

“Together” is not a claim of an atomic multi-file filesystem transaction. Recovery
must recognize each crash boundary: intent recorded, mail appended, task written,
event applied, commit failed. Existing message markers and the watch token provide
idempotent evidence. Do not advance applied state past an uncommitted operation
unless the operation retains enough durable evidence to finish safely.

A successful observation heartbeat can stay in private host state; durable
semantic events belong in the vault. Keep bodies, snippets, OAuth credentials,
MIME, and recipient lists out of logs/journals. Expose counts and opaque identities.
Respect user-authored mail sections and fail visibly if managed markers are damaged.

A single configured writer is the practical concurrency model. It prevents two
cron hosts from independently filing the same conversation, but does not eliminate
a human editing an unsynced vault elsewhere. Follow existing vault synchronization
and conflict checks; refuse conflicted targets and document the offline consistency
boundary. A closed task seen during the final re-read always wins over a fetched
reply.

Remote deletion, trash, label removal, auth failure, and a missing local task must
never synthesize completion. Preserve the archived content and report distinct
conditions. Skip spam/trash for new enrollment by default; make the handling of an
already-watched trashed thread visible.

**9. Polling is the right first transport**

Start with metadata polling of active watches every 15 minutes, plus a complete
paged `bob` enrollment scan. Reuse the adapter's existing metadata and
`search_page` support. The active set is explicitly selected by the user, so this
is simpler to explain and recover than mailbox-wide history from day one.

Fetch changed bodies only. Add bounded concurrency, exponential backoff with
jitter for transient failures, and per-thread retries. If a run budget is exhausted,
report partial progress and use fair traversal so the same leading threads cannot
starve the rest. Record last complete discovery separately from partial per-thread
success. Never claim the mailbox is caught up just because one page succeeded.

For scale, add mailbox history as an optimization later, not as the only source of
truth. History can expire; Google specifies full resynchronization after an
out-of-range cursor returns 404. A future history implementation should observe
mailbox changes, intersect with active watches, and still do enrollment discovery
and periodic audits. Filtering history solely to `bob` repeats the label
inheritance mistake. Advance a cursor only after every relevant page has been
durably applied. [Synchronization guide](https://developers.google.com/workspace/gmail/api/guides/sync).

Cloud Pub/Sub push is unnecessary for a 15-minute personal workflow. It adds cloud
configuration and watch renewal; Google's watch must be renewed at least every
seven days, with daily renewal recommended. A later push signal can trigger the
same reconciler, but does not replace reconciliation.
[Push guide](https://developers.google.com/workspace/gmail/api/guides/push).

Budget from the current quota table, not remembered historical values. The page
currently lists metadata/default `threads.get` at 40 units and full at 120, and
notes quota changes for newer projects. Fifty active threads would therefore cost
about 2,000 units per metadata sweep before discovery and changed-body reads
(arithmetic estimate, not a measurement of Bryan's account). Verify the actual
project's limits and pace requests; this example is not a measured active count.
[Current quota documentation](https://developers.google.com/workspace/gmail/api/reference/quota).

The exact supported gog version and metadata-header coverage need an adapter
contract test, especially In-Reply-To, References, Auto-Submitted, alias listing,
and structured delivery reports. Source inspection establishes the available
seams, not those live wire guarantees.

**10. The interface should be quiet and legible**

Keep stored Markdown `[?]`. While email is the effective date-based reason, draw
a small monochrome envelope inside the existing hollow waiting box. Use the current
ink tokens and shape language; do not add another status color or an animated badge.
The envelope replaces the existing generic date question mark, not the task's
leading mail-note link.

```text
Waiting:      [✉] Handle interview scheduling
                  Waiting for Alex · follow up Tue Nov 10

No reply yet: [ ] Handle interview scheduling
                  Follow up due · no reply since Nov 7

Reply:        [ ] Handle interview scheduling
                  Reply arrived · Alex · today
```

These are render sketches, not literal new Markdown checkbox values.

Preserve the established precedence: own dependency first, project blocking next.
Within date-based reasons, show the reason that determines the effective later
return; a separate later user schedule should not be hidden by an earlier mail
wait. List the remaining mail/date reasons through the existing corner pip and
tooltip. On equal mail/user dates, the envelope can lead while the tooltip names
both holds. Unknown higher-priority reasons retain the neutral fallback.

The main tooltip should read “Waiting for a reply from Alex. Follow up Tue Nov 10
if none arrives.” If another blocker dominates, say “Also waiting for a reply,”
not “Available Nov 10.” Include an accessible text label; shape, not hue, carries
the distinction.

Extend the same block-mark model across Live Preview, Reading View, Tasks query
results, task card, and task/link picker miniatures. Without the plugin, the
ordinary Blocked box and readable wait date still work. At expiry or on a reply,
the task becomes an ordinary actionable checkbox when eligible; do not keep a
blocked-looking envelope after it is actionable.

The managed child summary should update in place. Put full history in the mail
note, not a growing stream of task child bullets. No notification per poll.
`gmail list` can add watch state and freshness of observation; `gmail doctor`
should show route errors, missing/duplicate task identities, paused watches,
unsupported contract versions, and stale synchronization.

**11. Proposed configuration and cron deployment**

In chezmoi's `home/dot_config/bob/config.yml`, merge a block along these lines.
New `sync` keys below are proposed, not currently supported:

```yaml
gmail:
  account: bryanbugyi34@gmail.com
  writer: kellys-macbook-pro
  pull:
    label: bob
    inbox: gmail_inbox.md
  sync:
    label_prefixes: ["#", "+"]
    follow_up_days: 3
```

Retain `gmail.pull.label` and `gmail.pull.inbox` as shared enrollment settings
initially, despite the historic name, rather than creating competing values.
Document that `sync` uses them. Missing/empty enrollment label keeps enrollment
disabled; it should not erase existing watches or silently stop their monitoring.
A separate explicit disable/paused control should govern whether active watches
run. Validate days as a positive integer and prefixes as distinct safe strings.
A custom wait chosen on a task remains until the next real send, reply, or user edit;
changing the global default does not retroactively reschedule every watch.

In the eventual `cron.jobs` list in `home/.chezmoidata.yaml`, append:

```yaml
- name: bob-gmail-sync
  machines: [mac]
  schedule: "7,22,37,52 * * * *"
  description: Refresh watched Gmail threads and reply follow-ups
  command: bob gmail sync --quiet
```

This is every 15 minutes, offset from the documented 0/5/10-minute maintenance
jobs. The runner handles PATH, overlap protection, logs, status, and failure output;
do not embed another cron wrapper or absolute home paths.
The cron machine alias `mac` and Bob writer slug `kellys-macbook-pro` are different
names by design. Confirm the normalized writer slug with doctor before enabling.

Use the Mac initially because Bob's existing Gmail write guidance selects it and
its vault participates in the existing maintenance flow. This is an operational
recommendation, not verified evidence that its token is currently healthy.
A sleeping Mac does not meet a continuous 15-minute service guarantee. It catches
up at the next successful run; local date expiry remains available independently.
Display “Last checked …” and encourage a manual sync before review when stale.
If continuous response detection is essential, choose one always-on writer with
readonly Gmail credentials and a verified vault-sync setup. Do not schedule both
hosts as an availability workaround.

Stage deployment: ship CLI and all affected plugin semantics, migrate/adopt
existing tasks with dry-run review, apply config, run doctor and a real sync,
then enable the cron job. Keep old clients from stripping unknown holds: capability
checks should block enabling automatic waits until the installed plugin/reconcile
versions understand the field. Treat a new JSON block-reason variant as a contract
change and version it according to the established client contract.

After the crontab epic lands, use its `cronctl check`, render/diff, apply, status,
and logs workflow. Apply the Bob config as well: the epic's targeted cron apply
does not deploy arbitrary `~/.config/bob/config.yml` changes.
Verify the exact deployed binary exposes `sync` before cron starts calling it.
This report does not install the proposed job.

**12. Preserve pull and migrate without duplicates**

Keep `bob gmail pull` as the existing one-shot import command. Add `sync` as a
separate canonical action with `-d/--dry-run`, `-f/--format`, and
`-q/--quiet`, following Bob's CLI conventions. Do not turn pull into a broader
mutating alias: that would not preserve its behavior. It need not be removed or
emit deprecation warnings.

Both commands should share enrollment identity checks. A sync-created task should
also satisfy pull's already-filed logic; otherwise running pull afterward can
produce another task. Conversely, an existing pull marker is not evidence of an
active watch. Migration must find and inspect the corresponding task.

For already-pulled, currently labeled threads:

- One unambiguous open owner task: adopt it with a stable ID/token and retain its
  current residence. Show any different label-derived route as a proposed move.
- A closed/canceled owner, including an archived task: record/retain closure and
  do not reenroll.
- Multiple plausible owners or no recoverable owner: diagnose and require an
  explicit repair; do not create a new task just because the old inbox changed.
- A saved mail note without a prior pulled identity or owner: create a task only
  when current enrollment rules authorize it.

Newly adopted watches initialize from the current thread snapshot. Old inbound
messages already saved do not all become fresh reply notifications; an outstanding
latest outbound can establish a wait whose deadline is already due. A dry run
should distinguish these cases.

An explicit task reopen resumes the canonical watch with a new generation.
Leaving `bob` on a closed conversation does nothing. Removing and reapplying
the Gmail label alone should not override a terminal Obsidian decision; the task
card can explain how to resume. This prevents endless resurrection.

**13. Verification and implementation seams**

Implement this as a coordinated feature, not a shell script around pull. Suggested
work boundaries are routing/configuration, durable watch/reconcile core,
blocking/freshness contracts, plugin presentation/actions, and migration/deployment.
These are engineering work areas, not new beads or an approved implementation plan.

Relevant source seams include `src/native/gmail/{cli,config,gog,pull,journal}.rs`,
`src/native/config/gmail.rs`, the `gmail/note` prepare/merge machinery,
`gmail/compose/finalize.rs`,
`src/native/project_dependencies/blocking.rs`, task-status parsing/reconcile,
and `src/native/freshness`. In bob-plugins, extend the source fragments
`142c-block-marks-model.js`, related block-mark render/editor/reading modules,
the freshness evaluator/queue, and task-card consumers. Build generated plugin
entrypoints through the repository tooling.

Reuse the post-send acknowledged-message evidence to invoke the same watch reducer
immediately after `bob gmail send`; never start a wait from a preview or unresolved
send attempt. Polling remains the recovery path for Gmail web/mobile sends and
failed local finalization.
[Existing acknowledged-send finalization](https://github.com/bobs-org/bob-cli/blob/30841c2912519dace8d8bd75d2909f6f044a99e1/src/native/gmail/compose/finalize.rs).

The following acceptance cases should block release:

| Area | Essential cases |
| --- | --- |
| Routing | Both prefixes; co-located vs different-message labels; same-destination dedup; conflicting routes; invalid/missing/closed destination; traversal and case ambiguity. |
| Discovery | More than one page; old labeled threads behind imported ones; partial failure; no starvation; active thread whose newest reply has no label. |
| Timeline | Outbound from account and alias; draft; self-mail; same-count changed message set; two sends; inbound then outbound between polls; old imported mail; equal/missing timestamps. |
| Semantics | Auto-reply and receipt retain wait; bounce surfaces action; group reply; unrelated forward; reply after deadline; send long before enrollment. |
| Review | Three calendar days over DST; same-day acknowledge then second reply; NEW vs TICKLER; disabled lane; dependency/project/user schedule survives arrival; no automated fresh stamp or Today link. |
| Human ownership | Edited title and children survive; explicit wait changes persist; ordinary scheduled value is untouched even when equal to the mail date. |
| Lifecycle | Done/canceled before fetch and during write; task move; note rename; archived owner; missing/duplicated token; explicit reopen; label toggle cannot resurrect closure. |
| Recovery | Crash after each durable step; commit failure; duplicate event replay; concurrent cron/manual run; stale vault conflict; corrupt journal or managed markers. |
| UX | Checkbox glyph across all surfaces; light/dark contrast; keyboard action; screen-reader label; mixed-version refusal; plugin-off fallback. |
| Deployment | Quiet no-op creates no vault changes; cron failure is observable; writer mismatch; sleeping/offline host; stale last-success indicator; never-save policy retained. |

Use synthetic Gmail fixtures and the existing fake-gog test style. This research
did not run the proposed implementation, poll a real mailbox, measure the active
thread count, or validate the installed Mac toolchain. Those are rollout checks,
not facts to assume.

**14. Requirement adjustments and alternatives**

| Adjustment | Why I recommend it |
| --- | --- |
| Use `bob` for enrollment, not continued eligibility | Labels do not reliably describe future replies; an open task is the user's durable commitment. |
| Empty prefixes mean inbox routing only | Arbitrary Gmail labels should not become write instructions by accident. |
| Exactly one canonical task, reject ambiguous destinations | One closure authority makes the loop predictable; multiple full task copies create contradictory state. |
| Routing fixes the initial home | Explicit Obsidian moves remain authoritative. |
| Separate email wait date from ordinary schedule | A reply must never erase a deliberate independent defer date. |
| Keep the existing Blocked status and paint an envelope | Meets the visual requirement without proliferating task lanes. |
| Explicit pending-mail review event | Handles replies after expiry and replies after a same-day review. |
| Qualifying human conversation reply ends the wait | Auto-replies, receipts, and delivery failures are not successful responses. |
| Completion/cancellation is terminal until explicit reopen | Persistent labels must not recreate abandoned work. |
| Keep pull as-is; add sync | Preserves a useful existing contract and avoids a surprising behavior change. |
| Fifteen minutes means while the chosen writer is available | A laptop cron schedule is not an always-on guarantee. |

A Gmail-only snooze workflow is smaller, but it leaves reply-follow-up state outside
the area/project task system you actually review. A separate “Waiting For” note
would be simple, but duplicates task ownership and loses the requested project
context. A push service improves latency at substantially greater operational
cost. A full two-way Gmail/Obsidian sync adds competing completion/archive/label
authorities without helping the core workflow. I would choose none of these for
the initial implementation.

The legitimate reason to defer this feature is scope: safe reply review touches
task semantics and multiple clients. A small initial release can deliver routing,
durable enrollment, and mail refresh first. Automatic waiting should only enable
once blocking, freshness, and checkbox rendering agree; an MVP that silently hides
new replies is worse than the current manual workflow.

**Recommended solution**

Build a single-writer, read-only Gmail watcher around one canonical Obsidian task
per account/thread. Enroll through `bob`; route new tasks through the explicit
`#/` and `+/` prefixes with strict area/project validation. Keep the saved mail
note as the conversation archive. Track sent-message cycles durably, use a distinct
three-calendar-day reply follow-up date, and derive the ordinary Blocked status
with an envelope inside its checkbox. On real incoming mail, clear only that
email hold and create one review event; on expiry, return the task for follow-up;
on completion or cancellation, stop permanently until explicit reopen.

Poll with `bob gmail sync` every 15 minutes through the new chezmoi cron data,
preserve `pull`, and make replay, human edits, review acknowledgment, and partial
failure first-class contracts. This gives the requested back-and-forth workflow
without turning Gmail traffic into an unreliable substitute for the user's
judgment.

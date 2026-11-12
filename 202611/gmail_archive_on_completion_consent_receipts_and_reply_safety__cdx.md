# Gmail archiving after task closure: a deliberate, recoverable completion action

Independent research by **cdx**, 2026-11-12. This report uses the shared request, independently inspected source code, and primary external documentation. No swarm peer report, transcript, summary, or findings were consulted. This is a design recommendation; no Gmail account, production vault, configuration, or application code was changed.

**The idea is good if task closure authorizes one bounded archive action.** It is dangerous if “task is closed” becomes a permanent instruction to keep a conversation out of Gmail’s Inbox. I recommend an explicit opt-in, prospective automation that archives the known, still-`bob`-labelled messages once, records a durable receipt, and offers Restore to Inbox. A new message, missing task, unresolved merge, or uncertain recovery should leave the conversation visible and explain why.

This gives Bob a useful end-to-end workflow: label an email, work from its task, close the task, and have the Inbox reflect that decision. It removes duplicate cleanup without introducing a second completion gesture for every ordinary email. But it changes a documented read-only Gmail integration into a mailbox writer, so consent, identity, crash recovery, and user-visible results are part of the feature’s minimum scope.

**The current implementation provides useful foundations, but closing a watcher is not an archive trigger yet.** I inspected bob-cli at `de5c0e56d041af61aa0a4dd3d433a228754e66af`, bob-plugins at `2f02824e2858c01109ddb50501a66a9eda860ada`, and upstream gogcli at `6f910fffac0a359c30430b71a1037f2ccf07453a` (`v0.48.0-2-g6f910fff`). The minimum documented gog version in Bob is 0.44.0; I also checked relevant files at that tag. These are source inspections, not live mailbox experiments.

| Existing behavior | Consequence for this feature |
| --- | --- |
| Sync discovers `gmail.sync.label`, default `bob`, and files one task per `(account, thread_id)`. The label is configurable. | Resolve the configured label to its actual Gmail ID; do not hard-code `bob`, use subjects as identity, or assume account selectors in Gmail URLs select Bob’s account. |
| `gmail.filed`, `gmail.adopted`, and legacy `gmail.pulled` enrollments persist after label removal, closure, movement, and deletion. Adoption can occur without the label. | Enrollment proves Bob knows a thread. It does not prove permission to modify its current messages. |
| The watcher scan recognizes open task rows and mail links on the task line or a direct link-only child. One thread can have several tasks, and one task several threads. | Require all relevant owners to be positively closed; closing any one owner is insufficient. Preserve existing link semantics rather than finding arbitrary mentions. |
| Closed, cancelled, and deleted tasks all stop watching. The vault walk excludes top-level `done/`. | “No watchers” conflates completion, deletion, archival, and scan failures. Build an explicit closure inventory; do not archive by subtraction. |
| Live sync takes a host-local account guard, then revalidates local state under the vault maintenance lock. Remote reads finish before local application. | Reuse the locking and snapshot discipline, but introduce a separate remote-write protocol. The existing local transaction cannot roll back Gmail. |
| The writer pin is optional today. | Require one named writer before enabling automatic remote changes; the account lock is not a distributed lock. |
| `-l 0` skips new discovery but still watches and recovers. Dry-run writes nothing. | Archive work needs its own bounded queue; it must not disappear behind the new-filing limit or make dry-run persist state. |
| Human quiet mode suppresses ordinary successful rows. Ledger Tools runs `gmail sync -q -f json -r 30` on daily-note creation and returns immediately on success. | Adding a success field or a CLI line alone will not inform the Obsidian user. Ship a receipt consumer with the writer. |

Evidence: [sync contract][c1], [watcher scanner][c2], [enrollment fold][c3], [vault walk][c4], [sync orchestration][c5], [local transaction/recovery][c6], [report renderer][c7], and [Ledger Tools caller][p1]. The lifecycle integration test explicitly asserts that closed watchers do not fetch thread metadata; that expectation must remain true with archive automation off and change narrowly for pending archive candidates. [Lifecycle tests][c8]

**Gmail’s actual unit of mutation matters more than the word “archive.”** Gmail describes archiving as removing a message from the Inbox while retaining it in All Mail; a later reply normally brings the conversation back to the Inbox. Recoverability does not eliminate the attention risk: an email can remain stored and still be missed. [Gmail archive help](https://support.google.com/mail/answer/6576?hl=en)

Labels exist on messages. A thread’s labels are the union of labels on its messages; a label displayed for a thread need not be present on every message. Thread-level label changes affect every existing message, while later messages do not inherit a previously applied label. Therefore an old `bob` label on message A is not evidence that new reply B was selected for Bob. [Google’s label model](https://developers.google.com/workspace/gmail/api/guides/labels)

The implementation should remove only `INBOX` from explicit message IDs. `messages.modify` addresses one message; `messages.batchModify` accepts an explicit list of up to 1,000 IDs and returns an empty successful response. A thread-wide `threads.modify` call can include a reply that arrives between the eligibility read and the write. It is the wrong primitive for this automation. These are API facts; the choice to freeze IDs is my safety recommendation. [Message modification](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/modify), [batch modification](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/batchModify), [thread modification](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.threads/modify)

For ordinary user OAuth, message modification requires `gmail.modify` or the broader full-mail scope. `gmail.labels` manages label definitions and does not satisfy these message-mutation endpoints. Google describes `gmail.modify` as also allowing reading, composing, and sending, excluding immediate permanent deletion that bypasses Trash. Do not describe the Google grant as “archive-only.” The newer `gmail.modify.restricted` endpoint documentation describes an administrator/service-account scenario; it is not a substitute for this personal CLI’s normal consent flow. [Scope definitions](https://developers.google.com/workspace/gmail/api/auth/scopes), [message endpoint authorization](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/modify)

**I would adjust the requested requirements explicitly as follows.** These adjustments intentionally favor a visible Inbox over aggressive cleanup.

| Original ambiguity or requirement | Recommended interpretation or change | Reason |
| --- | --- | --- |
| Archive “iff” labelled and task closed | These are necessary conditions for a Bob-initiated action, together with consent and safety checks. They are not an invariant describing the whole mailbox. | Users can archive anything themselves; Undo must remain effective while a task stays closed. |
| “Was labelled bob” | Require the configured enrollment label on every message Bob will change at final preflight. Historical enrollment alone is insufficient. Removing the label revokes archive eligibility without ending existing reply watching. | A visible Gmail gesture can stop automatic archiving. |
| “The corresponding task” | All known corresponding task owners must be closed, with none missing or unresolved. | A shared conversation may support several independent actions. |
| “Closed” | Respect the vault’s canonical Done and Cancelled status types. Normal cancellation counts as “out of sight”; merge retirement does not count as completion. | This matches the request while avoiding cancelled merge tombstones. |
| Existing closed tasks | Do not archive them automatically at activation. Offer a separately reviewed backlog. | An upgrade must not silently clear months of mail. |
| Continuous sync | Archive once per observed completion episode, using a frozen message set. | Future replies and manually restored messages must stay visible. |
| Visibility | Require durable receipts plus a usable Obsidian/CLI presentation and Restore action. A transient toast or cron log is insufficient. | Users are often absent when sync runs. |
| Any host may sync unless pinned | Automatic archive requires a named writer and local activation for the selected account and vault. | A synced journal and host-local locks do not serialize independent machines. |

The rule should not automatically exempt all unread mail. Reading a saved message in Obsidian does not necessarily clear Gmail’s `UNREAD` label, so that rule would defeat this workflow and create pressure to mark mail read. Preserve unread, starred, important, routing, and enrollment labels. A changed message set is the useful warning signal; `UNREAD` is not proof that the user did or did not process the task. Stars and importance can be shown in review, without silently acquiring a new veto meaning.

**The clearest user promise is a short, concrete policy.** At activation, show the selected Gmail account and label, the writer host, and this copy:

> When all linked tasks are completed or cancelled, Bob can archive the labelled messages already known to Bob. New messages and uncertain cases stay in your Inbox. You can restore any Bob archive from Mail activity. Tasks already closed today will stay unchanged unless you review them.

Offer **Keep manual**, **Review candidates**, and **Enable automatic archiving**. Default existing installations to off. Review mode makes no Gmail mutations and requires no permission upgrade. Automatic mode requires explicit product consent separately from OAuth consent, with the policy version, account, vault, writer, label ID, and activation boundary recorded. Do not silently activate because a token already happens to have `gmail.modify`.

A proposed configuration shape is `gmail.sync.archive.mode: off | review | automatic`, default `off`; retain `gmail.sync.label` and `gmail.writer` as the existing sources of truth. Naming is illustrative, not a claim that these settings exist. Keep activation local to the writer rather than allowing a vault-synced flag to enable another host. Account or label changes invalidate pending actions; a label deleted and recreated with the same name is a different ID and needs an explicit policy update. Disabling stops new dispatch, but keeps activity and recovery information available.

There is no need for a blocking confirmation on every ordinary close after opt-in. Recurring dialogs dilute attention and recreate the duplicate work this feature is intended to remove. Apple’s guidance discourages alerts for common undoable actions; NN/g emphasizes visible, discoverable ways to reverse actions. Those principles support explicit setup, quiet routine execution, and accessible recovery—not invisible operation. [Apple alerts guidance](https://developer.apple.com/design/human-interface-guidelines/alerts), [NN/g user control and freedom](https://www.nngroup.com/articles/user-control-and-freedom/)

**The eligibility engine should use positive evidence and an explicit completion episode.** A useful conceptual predicate is:

```text
may_archive(thread, episode) =
    automatic_consent_matches(account, vault, label_id, writer, policy_version)
    AND episode_was_armed_while_linked_work_was_open
    AND every_recorded_owner_is_resolved_and_terminal
    AND no_current_owner_is_open_or_ambiguous
    AND closure_is_not_an_unresolved_merge_or_recurring_template
    AND live_non_draft_message_ids_match_the_frozen_known_set
    AND each_target_still_has(INBOX, enrollment_label_id)
    AND targets_have_no(TRASH, SPAM, DRAFT)
    AND episode_has_not_been_settled_or_suppressed
    AND durable_intent_and_receipt_storage_are_healthy
```

The frozen set should be the full set of non-draft message IDs successfully saved while at least one linking task was positively observed open, not merely the latest “counted turn.” Bob’s turn fold intentionally ignores some automated messages; those messages still matter when deciding whether mail has changed. A message being saved is not proof it was read. The user’s closing gesture is the decision; the snapshot bounds what that gesture can affect.

Recommended lifecycle:

1. **Observe open work.** After activation, record an episode for a labelled thread with resolved open owners. Persist their stable identities, the full saved message-ID set, and the current candidate Inbox IDs. Update this baseline only following a successful refresh and local revalidation while work remains open. Never include messages fetched after observing the final closure in the old authorization snapshot.
2. **Observe closure.** Resolve every recorded owner and every current corresponding link. Require explicit terminal rows or trustworthy closure evidence. A deleted row, removed link, unreadable note, absent mail note, or unknown custom status is an explained hold. At least one previously observed open owner must have become terminal; empty owner sets never qualify.
3. **Check Gmail.** Fetch current metadata, validate account/thread/message identities, and compare the full non-draft message set. If a message arrived, hold the whole candidate for review. Do not expand the operation to include it, even if a Gmail filter also applied `bob` to it.
4. **Bound the target.** Select the previously known Inbox messages that still carry both `INBOX` and the configured label. In v1, if the conversation has other Inbox messages outside this set, hold the conversation rather than perform confusing partial cleanup. Already-archived messages need no mutation and are not owned by a new Bob receipt.
5. **Persist and apply.** Store the exact intent before sending any write, revalidate task and Gmail conditions, then remove `INBOX` only from those IDs. Read back and settle the receipt. An entirely successful operation consumes this episode.
6. **Stay settled.** Further syncs do not enforce archive state. A later reply, manual Move to Inbox, or Restore is left alone. An explicitly observed reopened/new owner can establish a fresh episode; open-and-close activity entirely between polls cannot safely be reconstructed and needs review.

This prospective design necessarily misses some eligible closures that occur before Bob ever observes the task open. That is an intentional limitation, not a reason to infer authority from a date-only completion stamp. A reviewed command can authorize an exact current snapshot for those cases. Keep automatic execution under `bob gmail sync`; do not make a particular Obsidian hotkey the only source of truth. Managed close hooks may later improve immediacy and supply stronger evidence, but sync must still handle direct Markdown edits conservatively.

**Task identity and task archival need specific work.** The existing watcher scanner is useful for links, but its open-only filter and exclusions are unsuitable as the complete closure detector. Build a separate inventory, or generalize the parsing layer while preserving the existing watch projection. Use canonical `note_tasks` status interpretation, which the collection engine already uses, instead of implementing “anything not open means closed.” Capture unreadable-file and ambiguous-link conditions as incompleteness; today’s shared walk can skip unreadable text, which is acceptable for some discovery but unsafe as proof that no owner remains. [Task scanner][c2], [vault walk][c4], [closed-status handling][c9]

Follow recorded task identity through moves and collection into `done/`, with existing link repair and task-resolution facilities. Paths and line numbers are display locators, not durable identity. Newly filed managed tasks should receive stable block IDs through existing machinery. Adopted tasks without stable IDs need an explicit local identity assignment during enrollment or should remain review-only; do not match them to a vaguely similar closed title. Archive collection can deduplicate block IDs, so use move/repair evidence and verify the resolved mail association rather than assuming an ID is globally unique forever. [Task locator][c10], [archive contract][c11]

Merges are a particularly important blocker. Bob retires a source with `[-]`, preserves its notes, and may copy its mail link deeper inside the target’s body than the watcher scan recognizes. Simply requiring “no open watchers” would then archive active work. Follow a source’s merge relation to its live owner where reliably resolvable; otherwise show “Merged task—review.” For the first release, holding merged sources for manual review is preferable to shipping a half-correct ownership graph. Section/drawer merges and recurring occurrences should likewise stay review-only until their semantics are tested. Ordinary cancellation without transfer remains eligible. [Merge contract][c12]

**Keep the execution protocol small, explicit, and crash-aware.** Suggested internal modules are `sync/archive_scan`, `archive_plan`, `archive_state`, and `archive_apply`; the exact layout can follow repository conventions. The planner should be pure over typed local and remote snapshots. Its result includes candidates and reason codes such as `new_message`, `open_owner`, `owner_missing`, `label_removed`, `merge_unresolved`, `already_outside_inbox`, and `needs_review`. Neither plugin JavaScript nor a shell script should independently decide what to archive.

The durable operation key should include account, vault identity, thread ID, policy version, and completion-episode ID. Store exact target message IDs, owner identities, prior Inbox membership, snapshot fingerprint, request/verification states, and timestamps. Preserve the existing body-free journal discipline: no body, snippet, subject, or task title in operation logs. Render descriptive text from saved mail metadata in trusted user-facing views. The source already has strict saved-message markers, so a new archive snapshot can use parsed message identities without re-parsing email prose. [Mail-note parser][c13], [watch-state journal][c14]

Use the host-local account guard for dispatch and restore, and require the writer pin. Under the vault lock, revalidate owners and durably store the intent. Release the broad vault lock for network I/O, with a short final local preflight immediately before dispatch; do not hold the vault hostage through retry sleeps. Record dispatch state before sending, read back afterward, and finish the receipt under a short local lock. If local state changed during the operation, surface a conflict; a verified reopen detected in that in-flight window can trigger a narrowly recorded restore of the messages this operation removed, never a whole-thread reset.

There is no transaction spanning an Obsidian edit and Gmail, and the documented message-label request has no expected-history-ID field. The design cannot promise atomicity against an independent Gmail user changing labels in the last milliseconds. Frozen IDs prevent newly arriving messages from joining the request. Preflight checks, bounded execution, one-time consumption, and Restore reduce the remaining race. Explain that residual limitation in engineering acceptance criteria rather than claiming “exactly once.” [Message request contract](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/modify)

Recovery must be more conservative than retrying a read:

| Failure boundary | Required behavior |
| --- | --- |
| Before durable intent | No remote call. Report the storage failure. |
| Intent exists, dispatch definitely not started | Revalidate every condition before executing. |
| Request times out or process dies after dispatch began | Fetch only the frozen IDs and reconcile. Do not blindly issue another removal. |
| Targets are now outside Inbox but outcome was unobserved | Record “Inbox removal observed; prior response lost,” distinct from confirmed attribution. Offer an explicitly described Restore for those intent IDs. |
| Some targets remain in Inbox after an uncertain dispatch | Hold ambiguous IDs for review. A manual restoration could have occurred; repeated removal would defeat user intent. |
| Remote mutation succeeds but local receipt append fails | Recover from the already durable intent; alert on unresolved recovery and stop further automatic archives until bookkeeping is healthy. |
| Some independent operations succeeded before another failed | Preserve confirmed receipts and report partial success. A nonzero exit must not imply nothing changed. |
| Authentication fails | Stop further remote writes and explain reauthorization; do not log tokens or raw response bodies. |
| Journal is missing/corrupt after prior activation | Suspend automatic archiving and rebuild a reviewed baseline; do not treat state loss as first use and replay old closed tasks. |

State-based `INBOX` removal is idempotent in isolation. It is not harmless to repeat after the user has moved the same message back. This distinction is why uncertain dispatch should be held rather than endlessly retried. Reuse pacing/backoff for safe reads and definitive pre-dispatch rejections, but audit gog’s underlying HTTP retry behavior before selecting the mutation path. A transport’s automatic replay can undermine an otherwise careful Bob state machine.

Gmail history can help identify mailbox changes later, but it should not be a prerequisite for v1 or its only recovery evidence. Google says history retention is variable and a stale `startHistoryId` can return 404, requiring full synchronization. Exact message metadata is enough for a small archive queue. [Gmail synchronization guidance](https://developers.google.com/workspace/gmail/api/guides/sync)

**The transport boundary should remain tightly constrained.** Add a typed `archive_messages`/`restore_messages` interface that accepts validated IDs and hard-codes the sole change to `INBOX`. Keep all existing reads under their read-only flags. For the mutation child, omit `--readonly` only there, retain `--gmail-no-send`, the isolated `--client bob-gmail`, explicit account, `--no-input`, and an exact allowlist.

Upstream gog already has `gmail batch modify` backed by `Users.Messages.BatchModify`, and its Discovery no-send guard recognizes send endpoints while allowing other methods. A first-class invocation restricted to `gmail.batch.modify` with only `--remove INBOX` is a practical starting point; a Discovery call restricted to exactly `gmail.users.messages.modify` or `batchModify` is another. Do not grant a wildcard allowlist or expose arbitrary add/remove labels to the planner. Choose between these after verifying error and retry behavior at Bob’s supported minimum version. [gog batch implementation][g1], [gog API policy][g2], [Bob transport guards][c15]

Request `gmail.modify` only during explicit archive setup; do not request `https://mail.google.com/`. Keep the current compose/send confirmation path intact. The CLI currently offers readonly/compose scope choices, and its shared Gmail scope predicate recognizes readonly specifically. Update capability checks, doctor output, partial-consent handling, and reauthorization so a modify-capable grant is recognized correctly, while automatic archiving still requires its separate activation. A broader OAuth token is not a new permission for Bob to send. Preserve exact-grant checks rather than substring assumptions. [Login scope enum][c16], [Google profile][c17], [login flow][c18]

**Make the result beautiful through clear hierarchy and useful actions.** The primary surface should be a compact Mail activity card in Obsidian, owned by Bob Mail, backed by Bob’s receipts. Ledger Tools can announce that receipts changed; Bob Mail renders and acknowledges them. Poll or refresh that feed on app open and relevant journal changes so archives performed while Obsidian was closed are still visible.

A text sketch of the card:

```text
Mail activity                                         Today

Archived 2 conversations                              09:42
Their linked tasks were completed or cancelled.

Lease renewal · Dana               3 messages     [Restore]
Interview scheduling · Amira        2 messages     [Restore]

1 conversation stayed in your Inbox
Offer details · A new message arrived             [Review]

[View activity]                             [Pause automation]
```

This is a layout sketch, not a claim that the underlying objects already exist. Each row should offer Open in Gmail, Open task, and a reason in its details. Use the existing mail typography and restrained archive glyph; reserve warning color for held/error states, and never rely on color alone. Show full context on focus, keyboard-accessible actions, screen-reader status text, and correct singular/plural counts. Avoid celebratory animations for removing mail from view.

At a managed task close, a small contextual indication may say “Gmail archive pending” when eligibility is known, or “1 linked task still open.” Do not say “Archived” until verification succeeds. A batch toast can say “Archived 2 Gmail conversations · View activity · Restore,” but the durable card must survive the toast. An OS notification should be an optional summary without subjects on the lock screen. Persist an unacknowledged receipt separately from its current mailbox state; dismissed notifications are not proof that the action was understood.

The current Ledger Tools decoder turns `ok: false` into an error object before presenting a report. Extend it to preserve completed archive receipts even when the overall run fails. Otherwise precisely the partial-failure cases most needing explanation would lose their useful results. Keep JSON stdout machine-readable. Human `-q` may suppress routine refresh chatter, but archive changes and unresolved outcomes should still produce a short actionable summary; JSON should always include the receipt IDs. [Current caller][p1], [current report output][c7]

A minimal proposed CLI surface is a noun group `bob gmail archives`, defaulting to a read-only activity list, with `review` for candidates and `restore RECEIPT` for explicit recovery. This follows the project’s rule that bare groups default only to read-only members. An explicit reviewed apply can use an existing-style preview digest, with `-c|--confirm` bound to the account, candidate set, and policy; the digest is never authority to include newly fetched IDs. Support `-d|--dry-run` and `-f|--format` where appropriate, with short aliases for all public options. Final spelling should be settled with help design, rather than proliferating archive-related flags on `sync`.

Extend sync JSON additively with `archive: {mode, results, summary}` and per-result receipt, action, reason, thread ID, task locators, and message counts. Retain existing `pulled`/`watching` meanings and schema compatibility where additive. Separate `archived`, `already_outside_inbox`, `held`, `failed`, `uncertain`, and `would_archive`. A no-op is not an archive, and a held candidate is not evidence of a remote failure. Make doctor show mode, writer, grant capability, unresolved recovery, and notification/activity support.

**Restore should reverse only Bob’s action and should not be temporary.** The receipt records which messages actually had `INBOX` before the operation. Restore adds `INBOX` only to those IDs that Bob removed, retaining all other current labels. It never restores entire label snapshots, revives deleted messages, clears Spam/Trash, reopens tasks, or changes read status. Missing/deleted/trashed messages are skipped with an explanation. New replies are untouched. A second Restore is a no-op. An uncertain receipt uses clearly labelled “Move these messages to Inbox” recovery rather than claiming a perfectly attributed Undo.

Mark the completion episode suppressed before dispatching Restore, so a failed or delayed restore cannot race the next sync back into archiving. Retain suppression for that episode. Reopening a task after a settled archive should show an offer to Restore, without automatically forcing mail into the Inbox on every task edit. An already settled episode never archives again merely because Gmail shows `INBOX`. Do not expire receipt recovery after a five-second toast window. Disabling automation must leave Restore usable while the grant remains valid.

No extra Gmail “Bob archived” label is required in v1. It adds label clutter and another remote side effect, and cannot replace an exact operation receipt. Likewise do not remove `bob` to signal completion: that overloads enrollment, complicates user control, and does not solve new-reply safety.

**A staged release makes this a manageable feature rather than a mailbox rewrite.** I would deliver:

1. Read-only eligibility and activity design, with reason codes and fixture-driven scenarios. Preserve default sync behavior and all existing read-only guarantees. Show which historical closed tasks would require separate review.
2. Explicitly reviewed, frozen-ID archiving with full receipts, recovery, and Restore. This exercises the remote-write boundary before it runs unattended. Deploy the Obsidian presentation at the same time.
3. Prospective automatic mode using observed open-to-closed episodes, gated by explicit consent, a named writer, and healthy bookkeeping. Start with ordinary non-recurring, non-merged tasks; explain held exceptions rather than guessing.

Do not add a mandatory sleep to every sync as the main safety mechanism. A grace period can help accidental clicks but does not prevent a reply race, and the inspected automatic caller runs at daily-note creation rather than continuously. Promise “on a subsequent sync,” not “within seconds.” A short close-action debounce is optional; a reliable receipt and restore path is essential. The actual deployed sync schedule was not inspected in this research.

As an initial bulk safeguard, hold a newly discovered batch above a small explicit threshold for review instead of silently draining a large backlog in repeated capped chunks. Ten conversations is a reasonable starting hypothesis, not a measured optimum. Keep this separate from `sync -l`, whose existing contract limits new filings. Test the threshold against real usage before exposing more knobs. Do not silently resume old held batches after a policy upgrade or long outage without revalidation.

Required acceptance scenarios are concentrated on harmful failures, not on reproducing the implementation:

| Scenario | Expected result |
| --- | --- |
| Normal labelled thread; last observed open task closes | Frozen eligible Inbox IDs archived once; verified receipt and visible Restore. |
| Cancellation without transfer | Same as completion, with an accurate reason. |
| Two owners, only one closes | No archive. |
| One task owns two threads | Evaluate each separately; preserve and show partial success. |
| Label removed, renamed ambiguously, or recreated | No unintended authorization from an old name or enrollment event. |
| New incoming, outgoing, or ignored automated message appears before final preflight | Hold; new bytes never silently join the closure snapshot. |
| Reply arrives after preflight but before mutation | New ID is absent from the request and stays unaffected. |
| User reads in Obsidian but Gmail remains unread | Eligible known messages can archive; `UNREAD` remains unchanged. |
| Task deleted, link removed, note unreadable, or duplicate identity | Hold; no “zero watchers therefore done.” |
| Task moved or collected into `done/` | Resolve positive closure through stable identity/repair; otherwise hold. |
| Merge source cancelled while target is open or link moved deeper | Hold/follow ownership; never archive solely from source cancellation. |
| Unknown custom status or recurring occurrence | Explicit review until supported. |
| Already-archived messages | No mutation, no falsely owned Restore. |
| Restore, manual Move to Inbox, then repeated sync | No rearchive for the same settled/suppressed episode. |
| Crash before request, after request, and before receipt append | Correct bounded recovery; no blind removal replay. |
| Expired grant, 429, server error, ambiguous timeout, partial operation result | Bounded handling; preserve true successes; expose uncertainty. |
| Two hosts, two overlapping processes, writer change | One dispatch authority; no stale pending intents inherited without reconciliation. |
| `-d`, automatic mode off, `-l 0`, hidden `pull` alias | Dry-run zero writes; off preserves current behavior; watch-only mode handles archive queue; alias stays equivalent. |
| Obsidian closed during archive; later opened; whole sync returned failure | Completed receipts still appear with functioning recovery. |
| Hostile mail subject or task text | Inert display; never enters argv as shell code, executable UI, or body-bearing logs. |

Use the existing fake-gog infrastructure for deterministic failures and recorded mutation requests. Add transport assertions that only the exact intended IDs and `INBOX` delta can be sent, plus negative assertions that send, trash, delete, and unread changes are unavailable. Cover receipt fold/recovery, malformed journal state, archived-task resolution, and the plugin’s partial-success display. A final live check should use a deliberately chosen disposable test conversation only after separate authorization; this research did not perform one. Update contracts, generated CLI help, doctor, and plugin documentation along with the feature. No version or changelog edits are part of this research.

**The alternatives are useful, but none remove the need for visibility.**

| Approach | Assessment |
| --- | --- |
| Every sync archives all labelled threads with no open watcher | Reject. Cheapest code, highest risk: deletion, merged tasks, historical closures, and future replies all become disappearance triggers. |
| Archive immediately when filing the task | A coherent “Bob becomes my Inbox” workflow, but changes the user’s requested moment of consent and hides mail before the task is done. Offer only as a separate future policy if desired. |
| Add a second `bob/archive` label | Stronger per-thread intent, but extra Gmail work defeats much of the convenience. Reasonable alternative for someone unwilling to opt in globally; unnecessary as the default. |
| Always review an archive digest | Safest useful initial release; adds one batch decision instead of per-email dialogs. Keep as a permanent mode. |
| Ask on every task close | Clear but repetitive; also misses direct edits, mobile editing, and CLI closure. Not the primary mechanism. |
| Opt-in, one-time completion episodes with receipts | Best long-term fit: one ordinary task gesture, bounded remote effect, future replies preserved, recovery available. |

Remaining uncertainties are implementation checks, not hidden assumptions: gog mutation retry behavior at the supported version; the coverage and cost of stable-owner tracking through collection and merges; actual writer/sync cadence; and whether the proposed activity card is noticeable without feeling noisy. Test the card with a concrete scenario—“you closed a recruiter task yesterday; what happened to the email, and how would you bring it back?”—rather than judging appearance alone. The stricter current-label and prospective-only rules deserve explicit product agreement because they intentionally archive fewer messages than a literal retrospective `iff` implementation.

Source links below pin the repository evidence used above. They were inspected in SASE-opened local checkouts; no repository files were fetched over the web. External factual claims use the primary Google documentation and the original UX guidance linked inline.

[c1]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/docs/gmail.md
[c2]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/scan.rs
[c3]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/enroll.rs
[c4]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/vault_walk.rs
[c5]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/command.rs
[c6]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/file.rs
[c7]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/report.rs
[c8]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/tests/gmail_sync.rs
[c9]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/collect_done/transform.rs
[c10]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/task_locator.rs
[c11]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/docs/task-archive.md
[c12]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/docs/task-merge.md
[c13]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/note/parse.rs
[c14]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/sync/watch_state.rs
[c15]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/gog.rs
[c16]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/cli.rs
[c17]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/google/profile.rs
[c18]: https://github.com/bobs-org/bob-cli/blob/de5c0e56d041af61aa0a4dd3d433a228754e66af/src/native/gmail/login.rs
[p1]: https://github.com/bobs-org/bob-plugins/blob/2f02824e2858c01109ddb50501a66a9eda860ada/plugins/bob-ledger-tools/src/291g-plugin-gmail-sync.js
[g1]: https://github.com/openclaw/gogcli/blob/6f910fffac0a359c30430b71a1037f2ccf07453a/internal/cmd/gmail_batch.go
[g2]: https://github.com/openclaw/gogcli/blob/6f910fffac0a359c30430b71a1037f2ccf07453a/internal/cmd/api.go

**Recommended solution:** implement a reviewed archive-and-restore path first, then enable prospective automation by explicit account-specific consent. Let `bob gmail sync` archive a frozen set of still-labelled messages once when all positively identified owners close. Preserve the Inbox whenever messages, ownership, consent, or outcomes are uncertain. Ship the durable Mail activity receipt, Obsidian presentation, and Restore action as part of the initial writer. This delivers the intended cleanup while keeping a new recruiter reply—and the user’s ability to change their mind—outside the reach of an old task closure.

# Gmail sync auto-archive on task close: research (`__mus`)

Date: 2026-11-12. Scope: should `bob gmail sync` automatically archive a
Gmail thread when its Obsidian task is closed, how to make that safe and
visible, and what to build instead if the raw proposal is too blunt.

Short version: the raw rule ("labeled `bob` + task closed => archive") is
almost right but underspecified in exactly the places that cause harm. Ship
it as an explicit opt-in that archives only when **every** open linking task
is gone, requires a live `INBOX` membership check, previews loudly, journals
everything, and never runs silently under the hourly cron until the user has
seen it work. Details below.

## 1. What was asked

- `bob gmail sync` gains an archiving step: a thread labeled `bob` whose
  corresponding Obsidian task is closed gets archived in Gmail.
- Archiving must be unmissable when it happens, because silent archiving can
  hide a live email (the recruiter example).
- The lead is asked to own the design and make it intuitive, reliable, and
  beautiful; this report researches the implementation choice and critiques
  the plan.

## 2. How sync works today (the ground truth)

`bob gmail sync` is documented in `docs/gmail.md`
(sections Sync, Watch, Where it runs, Security) and implemented under
`src/native/gmail/sync/`:

- Orchestration: `src/native/gmail/sync/command.rs` (`run`, `run_inner`).
  Reads, routing, and body preparation finish before the vault lock; the
  scan plus `FilingOutcome` is the extension point for watch work.
- Module map: `src/native/gmail/sync/mod.rs` (discover, enroll, scan,
  watch_state, watch, guard, retry, health, command, report).
- Discovery: `src/native/gmail/sync/discover.rs` pages
  `label:<enrollment-label>` through the IDs-only `threads.list` Discovery
  call, dedupes, caps at 5,000 ids, and selects at most `-l` new filings
  (default 50, max 500; `-l 0` is watch/adopt-only).
- Enrollment: `src/native/gmail/sync/enroll.rs` (`EnrollmentFold`,
  `Membership`, `CandidateDecision`, `AdoptionIntent`). Identity is
  `ThreadKey { account, thread_id }` (`src/native/gmail/sync/mod.rs`).
  Enrollment is durable: removing the Gmail label, or closing, moving,
  merging, or deleting the task, never un-enrolls a thread. An open task
  that links an unenrolled mail note is adopted without needing the label.
- Watching: `src/native/gmail/sync/scan.rs` (`WatchScan`, `WatchingTask`,
  `WatchTarget`, `LinkPlacement`, `OPEN_STATUSES = [' ', '*', '/', '?']`).
  A task watches a thread only when its box is open, its line carries the
  exact `#task` token, and it links the indexed mail note on its own line or
  in a direct link-only child bullet. Closed rows, mentions elsewhere,
  frontmatter, and fenced code never watch. The walk shares `link -a`
  exclusions (`src/native/gmail/vault_walk.rs`).
- Turn/hold/lift: `src/native/gmail/sync/watch.rs`,
  `watch_apply.rs`, `hold.rs`, `watch_state.rs`, plus
  `src/native/gmail/turn.rs` (message classification: your move, their move,
  bounce, automated, ignored, self, DRAFT-ignored; ordered by
  `internalDate`). Hold inserts exact `#awaiting_reply` plus one
  `[scheduled::]` nudge (`reply_wait_days`, default 3); lift removes the tag
  then the date and may run `freshness::placement::mark_unblocked`.
  Closed rows are untouched by hold/lift (`watch_apply.rs`, H15).
- Report: `src/native/gmail/sync/report.rs` (`SyncReport`, `SyncResult`,
  `SyncProblem`). JSON schema 1 keeps `ok`, `dry_run`, `pulled`,
  `results`, `warnings` and adds `watch`, `problems`,
  `summary: {watching, awaiting}`. Exit 0/1/2 semantics live here and in
  `docs/gmail.md` (0 success/no-op/quiet-skip, 1
  runtime/deferred/first-seen-route-problem, 2 setup).
- Journal: per-host `.bob/gmail/<host>.jsonl`
  (`src/native/gmail/journal.rs`, `NAMESPACE`), with body-free
  `gmail.filed` / `gmail.adopted` / `gmail.turn` / `gmail.gone` /
  `gmail.save` events. Enrollment folds every host journal.
- Cron placement: the Mac runs `bob gmail sync -q` hourly at `:07`
  (`docs/gmail.md`, Where it runs). Agent hosts stay
  read-only through the `gmail.writer` pin; dry-run (`-d`) is allowed on a
  non-writer host.

The load-bearing sentence for this feature is in the Sync docs: "The label
stays in Gmail: sync uses read-only access and never unlabels, archives,
marks read, or changes a message." Auto-archive reverses that guarantee, so
it is a contract break in the everyday sense even if no `!`-style CLI break
is declared. Treat it like one.

## 3. What "archive" actually means in Gmail (and in gog)

- Archive = remove the `INBOX` label. The thread stays under All Mail and
  search, keeps every other label (including `bob` and routing labels
  unless separately removed), and stays reachable by id/URL. It is
  recoverable, not deletion and not trash. `gog gmail archive --help`
  (v0.44.0, observed this session) says: "Archive messages or explicit
  threads (remove from inbox)", with `--thread` to treat ids as thread ids,
  plus `--query`/`--max` batch forms. `gog gmail thread modify --help`
  exposes `--add`/`--remove` (`--add-label`/`--remove-label` literal forms)
  for the same label operation at thread granularity.
- New mail re-inboxes: a new message in an archived thread puts the thread
  back in the inbox under Gmail's default settings. That is the recovery
  path if we archive too early, and also a reason the "archived" state can
  flap if watch later refreshes the note.
- Thread vs message: sync is thread-oriented (`thread get`, thread identity
  in the mail-note index). Archive should therefore be thread-scoped
  (`archive --thread <threadId>` or `thread modify --remove INBOX`), never
  per-message, or one late message in a thread stays buried while siblings
  leave.
- The `bob` label is orthogonal to `INBOX`. Today sync never adds or removes
  either label. Archiving must decide both bits explicitly: remove `INBOX`
  (the archive itself) and keep vs remove `bob`. Keeping `bob` preserves
  enrollment discoverability and the phone-filing story; removing it looks
  "done" but destroys the re-discovery signal and fights the durable
  enrollment rule. Recommendation in section 8: keep `bob`, remove only
  `INBOX`, at least in v1.
- gog capability is present: `archive` and `thread modify` exist in the
  installed v0.44.0. What is missing is permission, not a subcommand.

## 4. The permission cliff: readonly today, modify tomorrow

This is the largest implementation cost and it is easy to underestimate:

- Today every Gmail read goes through `src/native/gmail/gog.rs`
  (`Gog::thread_get`, attachment fetch, `threads.list`) with
  `--readonly --gmail-no-send --enable-commands <read-only allowlists>` and
  the explicit readonly OAuth scope
  `https://www.googleapis.com/auth/gmail.readonly`
  (`READONLY_SCOPE`, `READ_COMMANDS`, `ATTACHMENT_API_COMMANDS`,
  `THREADS_LIST_API_COMMANDS`). Drafts/sends use a separate compose-scoped
  path (`gmail.compose` extra scope, Mac-only grant, digest-bound confirm).
- Archiving needs `https://www.googleapis.com/auth/gmail.modify` (remove
  `INBOX` is a modify call however it is spelled). Consequences:
  - `bob gmail login` needs a third scope tier (readonly, readonly+compose,
    readonly+compose+modify or readonly+modify), a re-consent flow, and new
    copy: the consent screen must name "Archive email you chose" rather than
    hiding modify inside compose. `src/native/google/profile.rs` (`GMAIL`,
    `gmail_scope`) and `src/native/google/signin.rs` / `gog.rs` scope
    plumbing all change.
  - `doctor` needs new rows: granted scopes (`readonly` vs
    `readonly+modify`), an archive-readiness verdict, and the same kind of
    honest labeling login already does for compose ("also permits sending").
    Today `doctor` prints `scopes: readonly|readonly+compose`; add the
    modify dimension.
  - Every archive call must omit `--readonly` while keeping
    `--gmail-no-send`, `--no-input --json --color never`, the isolated
    `--client bob-gmail`, the account flag, and a tightened
    `--enable-commands` / `--enable-commands-exact` allowlist covering only
    the archive/modify verbs. The read path stays exactly as it is.
  - The `gmail.writer` pin becomes load-bearing for writes to Gmail, not
    just the vault: only the writer host may call archive. Agent hosts stay
    read-only (the compose grant already stays off agent hosts; modify must
    follow the same rule). Non-writer `sync` must skip archiving cleanly,
    say so in the report, and keep `-d` available everywhere.
  - Tests never touch Google (`BOB_GMAIL_GOG` fake). A modify path needs the
    same fake-transport treatment the read path already has, plus refusal
    tests for insufficient scope, plus `--readonly` regression tests proving
    reads never gain write flags by accident.

Do not ship archive on the readonly grant by widening scopes silently or by
shelling out to a second credential. The re-consent moment is itself part of
the "super clear to the user" requirement: it is the one place Google forces
the user to notice the new power.

## 5. What "closed" means, and why "the corresponding task" is ambiguous

- Closed in the vault is not one checkbox. `OPEN_STATUSES` in `scan.rs` is
  `[' ', '*', '/', '?']`; everything else the status settings recognize is
  closed for watching purposes. Concretely that includes `x`/`X` (Done) and
  `-` (Cancelled) under `src/native/task_status_hooks/settings.rs`
  (`TaskStatusType::Done`, `TaskStatusType::Cancelled`), with custom
  statuses possible via settings. `TaskStatusType::is_open` is the
  authority; `collect_done` / `task archive` has its own eligibility layer
  on top (area/project notes, keep windows, `done/` pairing), which sync
  must not import wholesale.
- "The corresponding task" does not exist as a single row. One thread is
  routinely linked from several tasks (filing row plus hand-added links,
  project rows, daily-note rows), and one task can link several threads
  (`watch.rs` computes one effect per task after gathering every linked
  watched thread). Enrollment outlives all of them: close, move, merge, or
  delete never un-enrolls.
- So the naive rule has four live ambiguities:
  1. Any-closed vs all-closed: thread T linked from tasks A (closed) and B
     (open). Archiving on any-closed hides B's email. This is the recruiter
     scenario in miniature.
  2. Cancelled vs done: a `-` cancel usually means "won't do", which argues
     for archiving, but cancels also happen on duplicates and mistakes where
     the thread still matters elsewhere.
  3. Deleted/moved rows: a task deleted from the vault is not "closed", yet
     the email may still need action. A Ctrl+Shift+M move preserves the
     watch; archive must follow the moved row, not the stale path.
  4. Done-archive: `bob task archive` later moves closed blocks into
     `done/`; scan already excludes `done/` from watching. Archive
     eligibility must be computed against live notes plus the journal, not
     against whatever `done/` happens to hold today.

The only safe reading: a thread is archive-eligible when it is enrolled AND
it currently has zero open linking tasks anywhere in the live vault scan.
That is the all-closed rule, with deletion counting as "no longer open" and
reopen/link-again counting as "open again". Section 8 makes cancelled count
as closed for this purpose but calls that out as the adjustment it is.

## 6. Critique: is auto-archive a good idea?

Yes, with the enthusiasm dialed from "automatic" to "opt-in automatic".
The core loop is genuinely valuable: the inbox is a to-do list with no done
state, the vault already holds the done state, and sync already visits every
enrolled thread on a schedule. Closing the loop removes the second triage
pass (close task, then remember to archive) that busy people skip. The
`bob`-label enrollment gate is also well chosen: only threads the user
deliberately labeled are ever candidates, so random newsletters and cold
mail can never be archived no matter how many tasks close.

But the raw proposal has five hazards that the design must absorb, not
document around:

1. Silent destructive-adjacent action. Archive is recoverable, but "check
   All Mail" is not a recovery path anyone uses under time pressure. A
   missed recruiter reply or a school email archived on a mistaken close is
   a real miss even if the bytes survive. Running this inside the hourly
   `sync -q` cron makes it maximally silent at exactly the cadence where
   nobody is watching. Verdict: auto-archive must default off, announce
   loudly when on, and be trivially reversible from the report itself.
2. The single-task fiction. As section 5 shows, threads fan out to many
   tasks. Any-closed archiving will strand open work. This is the most
   likely source of a "bob hid my email" incident, and it is a logic bug,
   not a UX gap. Verdict: all-closed is the only defensible predicate.
3. Close is not done-with-email. People close tasks for "replied, waiting",
   "moved to call", "duplicate", "oops". The watch model already knows the
   difference between a turn (`turn: yours/theirs`, `turn_since`) and a
   checkbox; archive should consult the turn when it can. A thread whose
   newest counted move is theirs (ball in Bryan's court) deserves more
   skepticism than one whose turn is theirs-waiting or already replied.
   Verdict: do not block v1 on turn-awareness, but never archive a thread
   with unread/new counted moves the same run, and surface the turn in the
   archive preview row.
4. Label-presence vs enrollment confusion. The request says "labeled with
   bob", but enrollment survives label removal by design, and the scan does
   not require the label. If archive requires the live `bob` label, users
   who unlabel-by-hand to "file away" will never get archiving; if it
   requires only enrollment, threads long past their labeling moment get
   archived years later on a reopen-close cycle. Both are defensible, but
   the choice must be stated. Verdict: gate on enrollment + live `INBOX`
   membership, not on the live `bob` label; report the label state but do
   not require it (section 8).
5. Scope creep into a mail client. Archive invites mark-read, snooze,
   un-archive-on-reopen, per-label retention, and "archive the filing task
   too". Each is reasonable; together they turn a filing helper into a mail
   client with vault side effects. Verdict: ship the smallest reversible
   step (archive on all-closed, keep `bob` label, no mark-read, no
   auto-unarchive beyond what Gmail already does on new mail), and put the
   rest behind explicit follow-ups.

A rejected alternative worth naming: removing the `bob` label instead of
archiving. It is quieter and permission-free (still a modify, so no), and it
ends future filings, but it leaves the inbox untouched, which defeats the
stated goal. Keep it rejected. Another: mark-read instead of archive. Same
verdict: it hides the bold but keeps the row, satisfying nobody.

## 7. What "super clear" has to mean in practice

Beauty here is not decoration; it is the audit trail being legible at 11pm
under the hourly cron. Concretely:

- Human output: one archive section per run with inert subject/who (the
  same inert-title rule watch rows already follow), the vault note path,
  the closed-task count, the Gmail thread id tail, and the undo line
  (`gog gmail ... unarchive` or the Gmail search that finds it). New action
  name alongside the existing watch verbs (`held`, `lifted`, `bounced`,
  `resurfaced`, `refreshed`, `unchanged`): `archived`, plus `archive_skipped`
  / `archive_deferred` states that stay out of the quiet path only when
  nothing else needs attention. Follows the CLI rule: beautiful colored
  output where color aids scanning, `-q` keeps failures/warnings/deferrals
  only.
- JSON: extend the schema-1 sync document the same additive way watch did:
  an `archive[]` array (thread_id, note, tasks_closed_count, turn,
  turn_since, action, labels_before/after) plus
  `summary.archived`/`archive_skipped` counts. Never reuse `watch[]` action
  strings for archive outcomes; consumers already switch on those verbs.
- Dry-run: `sync -d` must preview archive candidates with the same
  labels-before/after a live run would apply, and touch nothing (no guard,
  no lock, no Gmail call). This is the review gate before anyone enables
  the cron form.
- Journal: append a body-free `gmail.archived` event per archived thread
  (account, thread id, note path, closed-task count, resulting labels) plus
  `gmail.archive_skipped`/`gmail.archive_deferred` evidence where the
  reason is durable (scope missing, non-writer host, budget exhausted).
  The fold must treat `gmail.archived` as idempotency evidence: never
  re-archive a thread already recorded archived unless a new incoming
  counted move arrived after it (which Gmail will usually have re-inboxed
  anyway).
- Doctor: add archive readiness (scope present, writer host, config value,
  last archive run, enrolled-but-eligible backlog count). The existing
  `sync` doctor row already reports watching/awaiting counts; add
  archived/eligible the same way.
- Undo: every archive row names its reversal. Gmail has no unarchive verb;
  the reversal is re-adding `INBOX` (`thread modify --add INBOX`). Print it.
  If a dedicated `bob gmail unarchive`/restore helper is ever added, it
  belongs as a separate explicit command, not as sync magic.

Also decide the `-q` behavior up front: archived rows are changes, so they
print even under `-q` (like filings and first-seen gone threads), while
`unchanged`/already-archived rows stay silent. The hourly cron at `:07`
must therefore produce exactly one line per newly archived thread and
nothing otherwise. That is the whole "beautiful" requirement for the cron
case: silence means nothing happened, one line means one decision.

## 8. Recommended solution (the adjustments, called out)

Adjusted requirement: archive an enrolled thread during `bob gmail sync`
iff the user opted in AND the thread still carries live `INBOX` AND zero
open linking tasks remain. Everything else is conservatism around that
predicate.

1. Opt-in, default off. New config (name TBD by the implementer; the shape
   that fits `gmail.sync.*` is `sync.archive: never|closed`, default
   `never`):
   - `never` (default): today's behavior byte-for-byte. No scope needed, no
     Gmail writes, no report changes beyond an archive-readiness hint.
   - `closed`: archive enrolled threads with no open linking tasks.
   Changing the value never rewrites history (same rule as
   `reply_wait_days`). CLI override flags `--archive` / `--no-archive` for
   one-shot runs, following the `gkeep pull --no-archive` precedent; the
   flag wins over config for that run. `-d` previews either way.
   This is adjustment #1 to the request: automatic becomes opt-in
   automatic. Justification: silent inbox mutation under an hourly cron
   without a consent-and-preview trail is the incident; an explicit switch
   plus re-consent is the cheapest prevention.
2. All-closed predicate. Archive T iff: enrolled in `EnrollmentFold`, live
   `labelIds` contain `INBOX`, the revalidated apply-time scan finds zero
   open (`TaskStatusType::is_open`) linking tasks for T, and no new counted
   incoming move for T arrived in this same run. Cancelled (`-`) counts as
   closed (adjustment #2; a cancelled duplicate that still has an open
   sibling task elsewhere is still protected by the all-closed rule).
   Deleted tasks count as gone, not open. Reopened or newly linked tasks
   re-arm eligibility. Never archive on a recovered-closed snapshot taken
   before this run's Gmail fetch; recompute at the apply boundary the way
   `report.rs` already revalidates watchers.
3. Keep the `bob` label; remove only `INBOX` (adjustment #3). The request
   says "labeled with bob" as the trigger; the durable-enrollment design
   means the trigger should be enrollment, with the live `bob` label
   reported but not required. Keeping `bob` preserves phone filing,
   discovery, and the audit story ("why did this archive? because it was
   enrolled and everything closed").
4. Verify before mutating (gkeep precedent). Per candidate: refetch live
   `labelIds`, confirm `INBOX` still present, confirm zero open linkers
   against the post-lock snapshot, then call exactly one thread-scoped
   archive (`archive --thread` or `thread modify --remove INBOX`), then
   re-read to confirm `INBOX` is gone before journaling
   `gmail.archived`. Any mismatch defers with `archive_deferred` and a
   warning; budget exhaustion (`-r` shared budget in `retry.rs`) defers the
   remainder rather than half-archiving. This is the content-guarded archive
   from `gkeep pull` ported to Gmail.
5. Order inside the run. Discovery, filing/adoption, watch prepare/apply
   first; archive last, after the vault commit is durable, with its own
   journal append after each confirmed archive (same durability order as
   `gmail.filed`). A failed archive never fails the filings or the watch
   that already committed; it adds a warning and a non-zero exit per the
   existing 0/1/2 contract (first-seen archive failure => 1, setup/scope
   problems => 2).
6. Scope and host gating. Archive requires the modify grant AND the writer
   host AND the same guard/lock discipline as the rest of sync. Missing
   scope or non-writer host => skip all archiving, emit one warning plus
   per-candidate `archive_skipped`, keep exit 0 unless the existing
   staleness rules say otherwise. Login/doctor copy must state the modify
   power plainly, mirroring the compose "also permits sending" honesty.
7. No extras in v1. No mark-read, no label removal beyond `INBOX`, no
   auto-unarchive command (Gmail re-inboxes on new mail; reopening the task
   does not need to un-archive), no per-label retention, no snooze. Each
   gets its own proposal after v1 proves the predicate.

Why this shape and not the alternatives:

- Manual `bob gmail archive <thread>` first, auto later: worth doing as the
  week-one slice (it exercises scope, gog verbs, journal, and undo without
  the predicate risk), but manual-only does not satisfy the request; the
  cron loop is the payoff.
- Any-closed: rejected (section 6.2). It optimizes one triage click and
  buys the worst incident class.
- Unlabel-`bob`-instead-of-archive: rejected (section 6). Wrong outcome for
  the stated goal and still a modify.
- Archive-on-`done/`-move (`bob task archive` drives Gmail): rejected as
  the trigger. `done/` timing follows keep windows (`keep_days`/`keep_max`)
  and would delay archiving by days; worse, it couples two independent
  lifecycles. Sync-time all-closed is prompt and local.

## 9. Edge cases the implementation must cover (checklist)

- Multi-task threads (A closed, B open): skip; report eligible-needs-B.
- All linkers closed but in different notes (inbox + project): archive;
  count every closed linker in the row.
- Reopen after archive: no auto-unarchive; next new mail re-inboxes via
  Gmail; a new open link re-enrolls watch without needing the label.
- New incoming counted move in the same run: watch applies first, archive
  skips (turn changed under us).
- Already archived (no live `INBOX`): no-op, silent in `-q`, no journal.
- Gone/trashed thread: existing `gmail.gone` path owns it; archive never
  runs for it.
- `never_save` / refused / failed-fetch threads: never candidates.
- Route-problem inbox rows: closing the inbox row counts like any other
  task close; the `GMAIL ROUTE` child does not special-case.
- Close-during-preparation: the apply-boundary rescan (cf.
  `file.rs` recovered-closed handling, `report.rs` snapshot rule) decides,
  not the pre-fetch scan.
- Running-session deferral: an archive whose thread has a live Task Link
  under today's open timed Pomodoro defers like a hold does; the marker
  does not advance for that thread.
- Budget/guard contention: `-r 0` means one attempt per archive op, no
  backoff; exhaustion defers with a warning, never partial-writes.
- Multi-account: `ThreadKey` account scoping already isolates; archive uses
  the run's resolved account only.
- Idempotency: `gmail.archived` journal + live `INBOX` check make reruns
  safe; `sync -l 0` still archives (watch/adopt path runs archiving too).

## 10. Test and doc plan (so "reliable" is checkable)

- Unit (fake `BOB_GMAIL_GOG`): all-closed archives; any-open skips; cancel
  counts closed; deleted counts gone; reopen re-arms; already-archived is a
  silent no-op; same-run new-incoming skips; `bob`-label-absent but
  enrolled still archives (with label state reported); `never` default
  changes nothing; `--archive`/`--no-archive` override; `-d` previews
  without Gmail calls; insufficient scope and non-writer skips with typed
  warnings; journal `gmail.archived` written only after confirmed
  `INBOX` removal; rerun does not duplicate journal.
- Transport: `--readonly` absent only on archive calls; `--gmail-no-send`
  always present; allowlist covers exactly the archive/modify verbs; no
  bodies/snippets in journals, errors, or JSON.
- Docs: update `docs/gmail.md` Sync/Watch/Where-it-runs/
  Security/doctor sections, the `sync --help` long text (alphabetical flags
  per CLI rules, new `--archive`/`--no-archive` with short aliases only if
  free), `just docs-gen` + `just docs-check`, JSON-outputs reference, and
  the phone-filing guide's "what happens after close" note. Keep the old
  "never archives" sentence as the `never` default description, not as a
  global claim.
- Rollout: land scope/login/doctor first; then manual archive slice behind
  the flag; then auto-archive default-off; enable on the Mac only after a
  week of `-d` previews in the real vault; hourly `-q` cron stays silent
  until the first real `archived` line proves the predicate.

## 11. Open questions for Bryan

1. Should cancelled (`-`) tasks really archive, or should only `x`/`X`
   done close? I recommend yes (cancelled + all-closed), but a "done-only"
   config value costs one enum arm if you disagree.
2. Keep-`bob`-label vs remove-`bob`-on-archive: I recommend keep. Removing
   looks tidy but burns the discovery signal; say the word if tidy wins.
3. Turn-awareness in v1: I recommend shipping without blocking on it
   (except the same-run-new-mail skip), then considering "don't archive
   while `turn == yours`" as the first tightening if early runs feel hasty.
4. Backlog: on first enable, potentially dozens of long-closed threads
   become eligible at once. Cap the per-run archive count (reuse the `-l`
   spirit with a separate archive cap, default small) and let the cron
   drain it, or require one manual `--archive` run to drain the backlog
   visibly? I recommend the cap + visible drain.

## 12. Sources consulted (session evidence)

- `docs/gmail.md` Sync/Watch/Where-it-runs/Security/doctor/JSON sections;
  `src/native/gmail/sync/{command,mod,discover,enroll,scan,watch,watch_apply,watch_state,report,guard,retry,health,hold}.rs`;
  `src/native/gmail/{gog,cli,config,login,journal}.rs`;
  `src/native/google/{profile,signin,gog}.rs`;
  `src/native/task_status_hooks/settings.rs`,
  `src/native/gmail/sync/scan.rs` (`OPEN_STATUSES`),
  `docs/task-archive.md` (eligibility/keep-window context, not imported).
- Live tool output this session: `gog --help`, `gog gmail --help`,
  `gog gmail archive --help` ("remove from inbox", `--thread`),
  `gog gmail thread modify --help` (`--add`/`--remove`), `sase repo list`,
  `sase memory read` (cli_rules, sase_artifacts, decisions
  `gmail-reply-wait-is-a-tagged-hold`, docs, glossary task-link/freshness/
  event-task).
- Memory rules applied: `cli_rules.md` (help quality, alphabetical flags,
  hidden-alias preservation, capture-protocol freeze, no new capture
  subcommand); `docs.md` (contract/guide split, `just docs-check`);
  `sase_artifacts.md` (explicit snapshot + label registration, used below).

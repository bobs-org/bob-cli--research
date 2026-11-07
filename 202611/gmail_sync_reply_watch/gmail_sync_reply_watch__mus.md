# Watching `bob`-labeled Gmail threads: routed sync, reply waits, and a 15-minute cron

**Report suffix:** `__mus` · **Date:** 2026-11-07 · **Question:** how should `bob gmail sync`
watch threads I label with `bob`, route them to area/project notes, and track
reply waits until I close the task?

## TL;DR (recommended solution)

Build a new **`bob gmail sync`** command and keep **`bob gmail pull`** unchanged as the
one-shot bootstrap. `sync` is an idempotent read-only reconciler that runs every 15
minutes on the single configured Gmail writer host:

1. Search `label:bob`, hydrate each thread, re-save/refresh its mail note through the
   existing save path.
2. Read that thread's Gmail label list, match labels of the form `<prefix>/<stem>` for a
   configured prefix set (chezmoi-configured to `["#", "+"]`), and route each match to
   `~/bob/<stem>.md` **only if that file exists and its frontmatter says area or
   project**; otherwise record a loud per-thread warning and continue.
3. Maintain **one task per (account, thread, area note)**, keyed by the mail-note link.
   New threads file a task; threads I have replied to become **future-scheduled Blocked
   tasks** (`[?]` + `[scheduled:: +N days]`), which render with the existing hollow
   **waiting** mark; a reply from the other side clears the sync-owned schedule so the
   task unblocks. Closing/cancelling the task ends the watch. Gmail is never written:
   no unlabel, no mark-read, no archive.
4. Ship it on the new chezmoi cron-data path (`cron:` block, `cronrun` overlap guard,
   state-dir logs) at a staggered `*/15` slot with `--dry-run` parity, colored human
   output, and JSON for agents.

The rest of this report justifies that shape, critiques the original sketch, and calls
out every place I deliberately deviate from it. **Deviations from the request are marked
`(ADJUSTMENT)`** so the lead can spot them.

## What exists today (verified in-tree)

- `bob gmail pull` (`src/native/gmail/pull.rs`) searches `label:<gmail.pull.label>`
  (default `label:bob`, limit 20 default / 500 max), saves each unpulled thread through
  the normal save path (`save::run_internal`), and appends one `- [ ] #task [[link]]`
  row under `## Tasks` in `gmail.pull.inbox` (default `gmail_inbox.md`, created as an
  inbox area note when missing). Identity is `(account-lowercased, thread-id)`.
  Idempotence comes from two layers: `.bob/gmail/*.jsonl` `gmail.pulled` events plus a
  re-check for an existing task link (recovers when the inbox write landed but the
  journal append did not). Gmail stays read-only: pull never unlabels, archives, or
  marks read. `-d` plans without writing. A `writer` pin (`gmail.writer`) restricts
  writes to one host slug; other hosts get a setup error.
- Config (`src/native/config/gmail.rs`, `src/native/gmail/config.rs`) is the `gmail:`
  block in `~/.config/bob/config.yml`: `account`, `body`, `folder` (default `mail`),
  `link_label` (default `✉️ {subject} · {who}`, must contain `{subject}`), `never_save`
  from/labels denylists, `pull.inbox` / `pull.label` (empty label disables pull),
  `signature`, `timeout_secs`, `writer`. Unknown keys are ignored; wrong types are exit-2
  setup errors naming the key.
- Save (`src/native/gmail/save.rs`, `note/layout.rs`, `resolve.rs`, `prepare.rs`) confirms
  thread/message IDs, refuses `never_save` matches, renders bodies through the inert
  boundary (no wikilinks/tags/checkboxes survive senders' bytes), and writes mail notes
  under `gmail.folder` with frontmatter (`gmail_thread_id`, `gmail_url`, `messages`,
  `who`, `started`/`updated`). `resolve_account` picks the configured, sole, or TTY-chosen
  account. All network work finishes before the vault lock is taken.
- Reads go through `gog` with a locked-down read flag set (`--readonly --gmail-no-send
  --enable-commands gmail.thread.get,gmail.get,gmail.messages,gmail.search,gmail.url,
  gmail.labels.list`), plus `labels_list` and paged `search_page` in the resolver. The
  isolated `--client bob-gmail` token bucket keeps Gmail consent separate from Calendar.
- Blocked display (`docs/blocked-marks.md`) is **display-only**: stored Markdown keeps
  `[?]`; reconcile derives it; only the rendered checkbox changes (solid `held` for
  prerequisite/project blocks, hollow `waiting` for date/recurring/priority deferrals,
  dashed `stale` when no reason is provable). A row must be `#task` with stored `[?]`
  to earn any mark. There is **no stored per-reason checkbox symbol**.
- Blocked derivation (`docs/task-status-hooks.md`): a recognized open task is Blocked
  when it has an open dependency or a **strictly future `[scheduled:: YYYY-MM-DD]`**
  date (project `^prj` dates/schedules propagate to residents). Every automatic
  Blocked→Ready recovery is recorded; a Blocked dependent with a still-future schedule
  stays Blocked. Freshness (`docs/freshness.md`) records recoveries with
  `[unblocked:: today]` so the row resurfaces as TICKLER in the next morning review.
- Parents (`src/native/parent_notes.rs`, `capture_targets`) resolve area/project/inbox
  notes by stem or alias with unknown/ambiguous/terminal/not-parent errors. `save -P`
  already reuses this resolver.
- Cron is moving to code: the in-progress `bob-cli-ib` epic makes one committed `cron:`
  block in chezmoi the single source of truth, rendered per machine, executed via
  `~/bin/cronrun` (overlap guard, state-dir logs, failure-only mail, `--dry-run`), with
  `cronctl` list/render/check/status/diff/apply/logs/run/edit. Mac jobs are documented
  as staggered (`:00/:05/:10`-style) with `--retry-timeout 120`.
- CLI rules (`sase/memory/cli_rules.md`, always in force): excellent `-h`, alphabetical
  options, new subcommand needs a short alias for every long option, no hard renames
  (old spelling becomes a permanent hidden alias), `bob task <verb>` is reserved for
  vault-wide task rewriters (read-only reports stay top-level — `gmail sync` is fine
  where it is), never add under `bob capture`.

## Is this a good idea? (critique)

Yes — with the scope tightened. The core loop is sound: labeling is already the fastest
triage gesture in Gmail (and the phone-filing guide already teaches `label:bob`), and a
vault task that stays alive until I close it is exactly the right "watch" semantic.
Pull proves the plumbing works. But the sketch as written has seven sharp edges:

1. **Routing by label is the best part — keep it, but bound it.** Per-area filing beats
   one global inbox once more than a handful of threads are watched. The risk is
   unbounded label→file creation. The sketch already guards this ("only if the file
   exists and is area/project"), which is the single most important safety rule in the
   whole feature. Keep it.
2. **A new stored checkbox glyph would break the vault contract. (ADJUSTMENT)** The
   request asks for a "unique blocked icon inside the checkbox square brackets" for
   awaiting-reply. Stored task checkboxes are a closed set the Tasks plugin, reconcile,
   freshness, and every client parse (`" "`, `*`, `/`, `?`, `x`, `-`, plus a few more).
   A new stored symbol (e.g. `[A]`, `[M]`) would be invisible to all of them: reconcile
   would not derive it, freshness would not rank it, mobile would show a plain box, and
   Dataview/Tasks queries filtering on `?` would silently drop waiting threads. The
   blocked-marks contract exists precisely to solve "same storage, distinct face."
   So: **store `[?]` + future `[scheduled::]` (the standard waiting-for-a-date shape)
   and let the render layer show the hollow waiting mark.** If a dedicated envelope-ish
   glyph is wanted, add it as a new `waiting`-family mark key (e.g. `mail`) in
   `docs/blocked-marks.md` + `bob-ledger-tools` `api.blockMarks` with conformance
   vectors — a real but separate piece of plugin work, not a storage change.
3. **"Check all labels when no prefix is configured" is too broad as stated.
   (ADJUSTMENT)** Enumerating the whole Gmail label universe on every run (personal
   labels, system labels like `CATEGORY_UPDATES`, `STARRED`, mailing-list labels) and
   treating each as a routing candidate invites surprise filing and extra `labels_list`
   + search fan-out. The bounded reading — check **all labels on the already-fetched
   `bob` threads**, not all labels in the account — is cheap (labels arrive with
   `thread.get`) and sufficient. Concretely: when `prefixes` is empty/unset, treat every
   non-`bob` label on each watched thread as a candidate stem and route it iff it names
   an existing area/project note. Never create notes from labels, never scan the account
   label list for routing.
4. **Reply handling needs a direction oracle, not heuristics on snippets.** The only
   reliable "did I reply last?" signal is per-message authorship: compare each message's
   `From` (and `SENT` label id) against the resolved Gmail account, newest message wins.
   Snippet matching, subject `Re:` counting, and "I sent from my phone" guesses all
   rot. gog's `thread.get` already returns the per-message `labelIds` and headers the
   model layer parses — use them.
5. **Scheduling the wait as a future `scheduled` date reuses the whole GTD machine for
   free.** A `[scheduled:: +3d]` task is Blocked today (hollow waiting mark), then
   automatically resurfaces (TICKLER/READY) in the morning review when the date arrives
   — no new queue, no new review section, no daemon. That is the elegant consequence of
   building on derived-Blocked instead of inventing a "waiting" status.
6. **Unblocking must only clear what sync itself set.** If sync blindly strips any
   future `scheduled` date when a reply arrives, it will eat hand-set deferrals ("don't
   look at this until after the offsite"). Sync must track ownership of the date it set
   (journal event or a narrow marker) and clear only its own.
7. **15 minutes is fine, but only on one host with an overlap guard.** Gmail quotas are
   generous for `search` + `thread.get` on ≤500 threads, but two hosts syncing at once
   risks duplicate tasks and journal interleaving even with the lock. The `writer` pin
   plus `cronrun`'s overlap guard already solve this — the design below leans on both.
   Do not run sync on athena *and* the Mac.

## Recommended design

### Command shape: add `sync`, keep `pull` (ADJUSTMENT)

- New `bob gmail sync [-b] [-d] [-f human|json] [-l N] [-q]` alongside `pull`.
- Keep `pull` exactly as-is (single-inbox bootstrap/backfill). Rationale: pull's contract
  (file everything into one inbox) differs from sync's (route per area/project, maintain
  state over time), so pull is **not** byte-identical and must not become a hidden alias
  of sync per the no-rename rule. Document pull as "first run / repair"; document sync
  as "the every-15-minutes watcher". If the lead later decides pull should go away, the
  old spelling must survive as a permanent hidden alias.
- Sync is read-only in Gmail (same gog read flags as pull) and vault-scoped in writes
  (mail notes, routed task lines, journal). It honors `gmail.writer` and `never_save`.
- `--dry-run` previews saves + task creates/updates/schedule changes without writing;
  `-f json` emits `{schema_version, ok, dry_run, checked, filed, updated, blocked,
  unblocked, warnings, errors, results[]}` for agents.

### Configuration (chezmoi-managed `~/.config/bob/config.yml`)

```yaml
gmail:
  pull: { inbox: gmail_inbox.md, label: bob }   # unchanged
  sync:
    label: bob                 # the watch label; empty disables sync
    prefixes: ["#", "+"]       # (ADJUSTMENT) was "configure # and +": ship exactly this
    wait_days: 3               # days to wait after my reply before resurfacing
    limit: 50                  # threads per run (≤500); paging, not a bigger hammer
    inbox: gmail_inbox.md      # fallback when a thread has no routable label
```

Notes:

- **(ADJUSTMENT) `prefixes` defaults to `["#", "+"]`, not "check everything."** An
  explicitly emptied list (`prefixes: []`) selects the bounded fallback (§critique-3):
  every extra label on a `bob` thread is a candidate stem. There is no mode that
  enumerates the account's label list for routing.
- Label syntax is `<prefix>/<stem>`: `#/job` → stem `job` → `job.md`; `+/hiring` →
  `hiring.md`. Take the text after the **first** `/`; stems must be safe vault stems
  (no `..`, no `/`, must resolve to `<stem>.md` at vault root the way the request's
  `~/bob/<label>.md` examples do). Nested remainder (`#/a/b`) is rejected as ambiguous
  rather than guessed into a folder.
- Gmail technically allows `#`, `+`, `/` in label names (`/` renders as nesting in the
  Gmail UI), so `#/job` is creatable in Gmail settings or via `gog labels`-family
  helpers; document the two labels to create. Case-insensitive stem match, exact file
  otherwise.
- **Routing validation ("fail loudly"):** the target must exist, be a regular file, and
  parse as area or project frontmatter (`type: [[area]]` / `[[project]]`, same predicates
  `save -P` uses). Anything else — missing file, inbox note, daily note, reference
  note, terminal/closed project — is a **loud per-thread warning surfaced in human
  output (red), JSON (`warnings[]` + per-result `status: bad_route`), and the run's exit
  code**, while the rest of the run still completes. (ADJUSTMENT: per-thread loudness +
  partial success instead of aborting the whole run on the first bad label. Aborting
  punishes ten good threads for one typo'd label.)
- `wait_days` is an integer ≥ 1 (default 3). `limit` caps `label:bob` search results per
  run; runs are newest-first and journals make repeats cheap, so a modest default with
  frequent runs beats a 500-thread mega-run.

### Sync algorithm (one run, idempotent)

```text
resolve config + writer pin (non-writer prints pinned-host note, exit 0 on --dry-run else 2)
search `label:<sync.label>` (limit N) → thread ids            [gog search]
for each thread: thread.get → messages, labelIds, headers     [gog thread.get]
  save/refresh mail note via save path (new messages appended as cards; rerender keeps
    authored text) — honors never_save; refused threads are skipped with reason
  route: candidate labels = thread labels starting with a configured prefix
         (or all non-watch labels when prefixes == [])
         → stems → first stem whose <stem>.md exists and is area/project wins;
           ties (two routable labels) → file in each? NO — file in the first in
           Gmail label order and warn `ambiguous_route` (ADJUSTMENT: deterministic
           single-home beats multi-filing the same thread into N areas)
         → no candidate → fallback inbox (gmail_inbox.md), status `filed_inbox`
  reconcile the ONE task for (account, thread, note):
    find by mail-note link target in that note's task lines (index-assisted, not grep)
    - none, thread open (task not closed/cancelled elsewhere): append
      `- [ ] #task [[mail/....|label]]` (+ optional `[scheduled::]` per state below)
    - exists and task closed/cancelled: DO NOTHING to the task (watch over), but still
      refresh the mail note so the archive stays complete
    - exists and open: update schedule/blocked per reply state machine (below);
      never touch text the user edited, never move the line, never dedupe aggressively
journal `gmail.synced` per thread (account, thread_id, note, state, message_count,
  last_message_id, schedule_owned flag) — the ownership record for §critique-6
commit vault paths + journal under the vault lock (same staged-write pattern as pull)
```

Why one task per (thread, note), not per message: message volume would spam the area
note and break the "close the task to stop watching" mental model. The mail note already
carries per-message cards; the task is the watch handle.

Why refresh the mail note even after the task is closed: the vault stays a complete
archive of threads I cared about, and re-opening (labeling again / re-tasking) resumes
cleanly from a fresh note rather than a stale one.

### Reply state machine (the heart of the feature)

Per thread, let `last` = newest importable message, `mine(last)` = From/SENT says I sent
it:

| Observed | Task update |
| --- | --- |
| Thread first seen, `last` is theirs | `- [ ] #task [[link]]`, no schedule. Normal READY/NEXT candidate — I owe a reply. |
| Thread first seen, `last` is mine (I labeled after replying) | `- [?] #task [[link]] [scheduled:: <today+N>]`, journal marks `schedule_owned: true`. Waiting on them from birth. |
| Open task, new message from **them** arrives | Clear the sync-owned `[scheduled::]` **only if** `schedule_owned` is set (leave hand-set dates alone), keep `- [ ]`, refresh link label if subject/counters changed. Task unblocks via reconcile and re-enters my lanes. Do **not** stamp freshness (a stamp would hide it as NEW). |
| Open task, new message from **me** (I replied in Gmail/Mac/sync window) | Set/replace sync-owned `[scheduled:: <today+N>]`, stored `[?]` (reconcile re-derives it anyway). This is the "waiting for reply" state: Blocked + hollow waiting mark + `Also scheduled …` tooltip. |
| No new messages, schedule date arrives | Nothing for sync to do — the date is now past, reconcile/freshness surface the row (TICKLER) in review. I decide: nudge, wait longer (keep/stamp), or abandon (complete/cancel). |
| Task closed/cancelled by me (any client) | Watch ends. Sync never reopens, never re-schedules, never re-files that thread while the close stands. If the thread later gets new mail, the note still refreshes (archive), but no task returns unless I re-task it by hand. |

"Best task updates when they reply" (the request's hard question): the minimal correct
set is **unblock + refresh**, nothing more. Concretely: drop my owned schedule, leave
the checkbox to reconcile (it flips `[?]`→`[ ]` on its own), update the link label if
the subject/counter changed, and do not append chatter ("they replied!") to the task
line — that would dirty every area note four times a day and fight the user's own words.
The new message itself is already in the refreshed mail note one click away. A
`[unblocked:: today]` tickler write is unnecessary here (that marker is for automatic
Blocked→Ready recoveries that would otherwise vanish; a fresh inbound email is its own
salience).

Multiple rapid exchanges between runs collapse to the newest message — correct, because
only the latest direction matters.

Edge cases: I reply to myself / newsletter (last is mine, no human counterpart) → still
schedules a resurface, which is the desired "did anything happen?" check. Same-day
self-send + their instant reply → unblocked, no flapping, because state derives from
`last` each run rather than toggling. Drafts (`DRAFT` messages) are never imported by
the body layer, so unsent drafts never flip direction. Mailing-list/bulk threads obey
`never_save` as today.

### Scheduling: every 15 minutes via chezmoi cron data (ADJUSTMENT on "you pick")

15 minutes is the right interval; the mechanism should be the new `cron:` data path,
not a hand-edited crontab line:

```yaml
# chezmoi cron data (illustrative; exact keys per crontab_as_code schema)
cron:
  jobs:
    - name: bob-gmail-sync
      schedule: "7,22,37,52 * * * *"   # every 15 min, staggered off :00/:05/:10
      command: bob gmail sync --retry-timeout 120
      host: mac                         # the Gmail writer host only
```

- Stagger (`7,22,37,52`) keeps sync off the documented vault-sync slots; exact minutes
  defer to the `bob-cli-ib` schema, but the principle (never `:00`, never colliding
  with git-sync) should be recorded in the plan.
- `cronrun` supplies the overlap guard (a 14-minute `thread.get` storm must never stack
  two syncs), state-dir logs (`~/.local/state/cron/bob-gmail-sync.log`, read via
  `cronctl logs`), failure-only mail, and `--dry-run` for the skill docs.
- Writer pin does double duty: even if the job file lands on two machines, only the
  writer executes; the other exits before touching Gmail. Run it on the Mac (Gmail docs
  already recommend the Mac as writer; athena sleeps less but the Mac holds the grant).
- Cost: 96 runs/day × (1 search + ≤50 thread.get) is trivial against Gmail quotas; the
  per-run `limit: 50` bounds the tail. Missed runs (lid closed) are harmless — the next
  run reconciles from `last` and journals, same as pull's crash recovery.

### Beauty (the "last but not least" requirement)

- Human lines mirror pull's (`filed · <thread> → <note>`, `waiting · … until <date>`,
  `replied · unblocked …`), colored: cyan for filed, dim for already-watched, red for
  bad routes. Quiet mode for cron; failures mailed by `cronrun`, not printed.
- The waiting task itself stays one clean line:
  `- [?] #task [[mail/2026/…_job|✉️ …]] [scheduled:: 2026-11-10]` — no bot chatter, no
  emoji in storage. The hollow waiting mark + `until <date>` tooltip (blocked-marks
  family) is the beauty; keep storage austere and let the render layer glow.
- If the dedicated-glyph itch persists, spec it as `docs/blocked-marks.md` follow-up
  (`mail` waiting key, envelope-ish outline glyph in the level ink, `Also awaiting reply
  …` tooltip line, contrast ≥ 4.5:1 per the existing node test, conformance vectors
  BM-new). Do not block sync on it.
- Docs: extend `docs/gmail.md` (Pull → Pull + Sync), the phone-filing guide (how to
  create `#/job`-style nested labels), `docs/reference/cli/gmail.md`, and the command
  catalog; `bob gmail sync -h` shows routed examples (`#/job`, `+/hiring`, fallback
  inbox, `-d` preview).

### What I would explicitly not build

1. No Gmail writes (no unlabel-on-close, no mark-read, no archive-on-file). Every one of
   those needs the `gmail.modify` scope — a re-consent, a bigger blast radius, and an
   irreversible action taken by a cron job. The watch already ends vault-side when the
   task closes; unlabeling is optimization, not semantics. Revisit only with an explicit
   `--unlabel-on-close` opt-in and its own decision record.
2. No new stored checkbox, no new task status, no new Dataview field for "waiting".
   Derived-Blocked + `scheduled` already express it; freshness already resurfaces it.
3. No multi-homing one thread into N area notes. One deterministic home + loud
   `ambiguous_route` warning. Multi-filing duplicates the watch and doubles the close
   gestures.
4. No per-message tasks, no auto-complete when a thread "looks done" (a "thanks!" reply
   is not consent to close), no auto-bump of `wait_days` (that decision belongs in GTD
   review, per the decay ladder's consent principle).
5. No second scheduler while `bob-cli-ib` is in flight: register the job in `cron:` data
   from day one; a hand-added crontab line becomes migration debt the cutover must then
   retire.

## Alternatives considered

| Option | Verdict |
| --- | --- |
| Extend `pull` in place to do all of this | Rejected: different contract (one inbox vs routed + stateful). Keep `pull`, add `sync`. |
| Watch via Gmail push notifications / Cloud Pub/Sub | Rejected: needs a public endpoint, service account, and always-on infra for a 15-min-latency feature. Polling wins. |
| One task per message | Rejected: area-note spam; breaks close-to-stop-watching. |
| `superhuman`-style snooze (remove label, re-add later) | Rejected: Gmail writes + modify scope + silent thread hiding. Vault-side schedule is reversible and visible. |
| Derive waits from sent-mail search (`in:sent`) instead of thread direction | Rejected: fragile across clients and aliases; thread-local `From`/`SENT` comparison is exact. |
| File first into inbox, then `task-move` into areas | Rejected: two hops, two failure modes, and the move never advances the walk anyway — route directly. |

## Build sketch (for the implementer, not a commitment)

1. Config: `GmailSyncSettings` (`label`, `prefixes`, `wait_days`, `limit`, `inbox`) in
   `src/native/config/gmail.rs` with the same key-naming setup errors; resolve in
   `src/native/gmail/config.rs` with `["#", "+"]` defaults.
2. Labels: reuse `Gog::labels_list` + per-thread `labelIds`; add `sync.rs` routing
   (`strip prefix → stem → <stem>.md → frontmatter area/project check`) returning
   `Routed | FallbackInbox | BadRoute(reason)`.
3. Tasks: index-assisted lookup of the mail-link target per candidate note; staged
   append vs. surgical schedule-line edit under the vault lock; `gmail.synced` journal
   events carrying `schedule_owned`.
4. Direction: `mine(message)` = From-address ∈ account aliases ∨ `SENT` ∈ labelIds;
   state from newest importable message only.
5. CLI: `sync_command()` (+ tests mirroring the existing `cli.rs` pin tests), report
   printer, JSON schema v1. Wire into `docs/gmail.md`, `reference/cli/gmail.md`,
   command catalog, phone-filing guide.
6. Cron: `cron:` job entry + `cronctl` verification on the writer host; document in the
   crontab memory note per `bob-cli-ib` decisions.
7. Tests: golden routing table (`#/job`→`job.md`, bad stems, missing files, inbox
   targets, ambiguous pairs); direction oracle unit tests (SENT vs From, drafts
   excluded); idempotence replays (crash between inbox write and journal append);
   ownership tests (hand-set schedule survives their reply; owned schedule clears).

## Recommendation restated

Approve the feature with the adjustments above: **`bob gmail sync` as a new read-only
reconciler, routed per `<prefix>/<stem>` labels onto existing area/project notes with
loud per-thread failures, reply waits expressed as owned future `scheduled` dates on
`[?]` tasks (existing waiting render, no new stored glyph), close-to-stop-watching,
handled entirely by a staggered 15-minute `cron:`/`cronrun` job on the Gmail writer
host.** The plan is intuitive (label it, it follows you; close it, it stops), reliable
(idempotent, single-homed, single-writer, overlap-guarded), and beautiful (one clean
task line; the glow lives in the render layer where it belongs).

# Loopable high-value work for a 48-hour near-infinite token window

- **Researcher:** `research.31.grk` (Grok 4.6)
- **Date:** 2026-09-30
- **Project context:** bob-cli current; enabled siblings sase (heavy) and actstat (idle)
- **Question:** Given near-infinite tokens for the next 48 hours only, what high-value work is worth running in a loop with the same or a similar prompt (for example via `/sase_handoff` / `sase pipe`)?

This report is independent. It does not consult peer swarm reports.

---

## Bottom line

Do **not** spend the window pouring more implementation agents into sase. The live system is already over-committed: 97 in-progress sase epics, 49 of them older than 14 days, 161 unblocked ready task beads, and 19 live sase agents at the time of this survey. That is the bottleneck. Infinite tokens spent starting more sase epics make the next six months more expensive.

Spend the window on three serial, same-prompt loops that write durable artifacts and then stop:

1. **Make the sase backlog honest** — a read-only verdict loop over stale in-progress epics and the refilled ready queue. Highest leverage. Tokens uniquely buy the thorough reads.
2. **Drain bob-cli's 17 ready beads**, starting with clippy (`bob-cli-v`, +6). Completable in 48 hours. Ships. Stops the landing tax.
3. **Read the ten SASE-paper follow-ups already on today's plan**, one paper per hop, with implication notes that can become decisions. This is the luxury purchase tokens are for.

A GKeep-idea triage loop and a NEXT/PENDING lane-hygiene loop are the right fourth and fifth if (1)–(3) are already running in other sessions.

The rest of this report is the evidence, the loop kit you need because `max_agent_pipe_chain` is 8, and a ranked list I would actually run.

---

## 1. What "good" means for this window

A recommendation has to clear all five:

| Filter | Why it matters in the next 48 hours |
| --- | --- |
| **Same-prompt loopable** | One hop does one bounded unit. The successor prompt is the same template plus a pointer at durable state. `/sase_handoff` (`sase pipe`) is the example mechanism. |
| **Durable checkpoint every hop** | Pipe chains die. Context windows die. The window ends. Work that lives only in a chat is lost work. |
| **High value after tokens become scarce** | Prefer artifacts that make later cheap-token work better: an honest backlog, an empty ready queue, decision candidates, data that is actually backed up. |
| **Token-expensive on purpose** | The scarce resource is a 48-hour burst. Spend it on thorough reading, clustering, and synthesis you would skip later. Do not spend it on work a small model can do next week. |
| **Does not fight the live machine** | Athena is the fleet hub. Historical bead `sase-14x` recorded 39 duplicate `sase service`/`scheduler` copies and load ~70. This survey still sees load ~29 with one service and one scheduler. Serial handoff is the right shape. More parallel sase implementation is the wrong one. |

Work that needs Bryan at every gate, needs a quiet host for visual goldens, or starts a new sase epic on top of 97 in-progress ones fails the filter.

---

## 2. Live constraints (checked, not guessed)

### 2.1 The handoff mechanism is bounded

Merged config: `max_agent_pipe_chain: 8`.

A `/sase_handoff` loop is at most eight session members, including the root. Hop 8 cannot pipe. If the prompt says "always hand off," the eighth member fails and the queue stalls.

Design every loop as **batches of 7 work hops + 1 synthesis hop**, then relaunch the same prompt against the same queue file. Fresh context (`sase pipe -f`) is the default; inherited chat is how loops rot.

`sase pipe` is serial and keeps one runner slot. `sase run` / `#research_swarm` / `sase bead work` are how you fan out. Fan-out is how athena got to load 70. Use pipe for the loops in this report. Use a second *session* only when you are running a second *loop*, not a second copy of the same queue.

### 2.2 The work already in flight

| Surface | Count | What it means |
| --- | --- | --- |
| sase beads | 5691 total · 162 ready · 174 in progress · 5329 closed | Ready refilled after the 2026-09-20 drain epic `sase-14n` closed on 2026-09-22. |
| sase `bead ready` | **161 unblocked** task beads | Of 312 ready-status tasks (95 bug / 89 flake / 67 ci / 44 feature / 6 memory / 11 untyped; 173 large / 83 small / 55 medium). Many ready beads are blocked; 161 are not. |
| sase in-progress **epics** | **97** | Age: 49 are 14d+, 31 are 7–13d, 9 are 3–6d, 8 are 0–2d. Oldest still in progress: `sase-j7` (50d, flake-class root cause). |
| bob-cli ready | **17** unblocked | 11 small, 3 medium, 3 large. Clippy `bob-cli-v` has +6. |
| bob-cli in progress | 3 epics (`bob-cli-28`, `31`, `32`) | Capture routing, task freshness, Work Log bullets. Do not collide with those. |
| Live agents at survey | 30 (19 sase, 11 bob-cli) | Includes this research swarm, `sase-1c1` (v0.18.0), `sase-1dq`, freshness/Work Log phases, doc refresh. |
| Today's Bob plan (2026-09-30) | 3/3 themes, **TODAY 5**, **NEXT 28/15**, **PENDING 49/10** | Caps are already blown. Themes: BOB, READ, MEMORY. |
| `gkeep_inbox.md` | **65** open `#task` lines | Pull is already happening (each task has a Keep `Source:` / `%%gkeep:%%` marker). Remaining work is triage, not building `bob gkeep`. |
| Host | athena, load 29.07 / 21.13 / 17.60, 1× `sase service run`, 1× `sase scheduler run` | `sase-14x` (39 duplicates, load 70) is still READY and large. Treat host headroom as fragile. |

Cached provider usage at survey (not the same thing as "infinite," but it is the live budget picture): Claude weekly 37% left (reset ~2d); Grok weekly 57% left (reset ~34h); Muse weekly 48% left (reset ~3d); Codex 91% left; AGY 3p weekly 100% left. Whatever is supplying the 48-hour burst, the loops below remain correct if that burst is real.

### 2.3 What is already spoken for today

Do not invent a second owner for work that already has one:

- **`^memory-file-versions`** is In Progress; work log says `apollo.3o` was launched to epic it from `memory_and_instruction_file_history`.
- **`^release-v18`** is In Progress via `sase-1c1` (live clan members at survey).
- **`bob-cli-31`** (Ready-task freshness leases) and **`bob-cli-32`** (Work Log bullets) are landing now.
- **`bob-cli-28`** owns the capture `|| true` clippy-deny; clippy *warnings* in `bob-cli-v` are a separate ready bead.
- **`sase-126`** (restore Master Gate / Full CI) is still in progress. Mass visual-golden loops collide with it.
- **`sase-14n`** already drained the 2026-09-20 bug/CI cohort and closed. Implementing "whatever is still ready" without a new triage is how you get a fourth overlapping epic.

The paper-followup task `^sase-paper-followup-reading` is **Next**, not started. GTD morning review `^prj` is In Progress (work log: `apollo.research.v`). Those two are fair game for the loops below.

---

## 3. The loop kit (use this, or the window leaks)

A good loop is a queue plus a stop rule, not a vibe.

### 3.1 Durable state

Keep a single markdown ledger in the research sidecar, for example:

`research:202609/loopable_high_value_48h_token_window/queue.md`

Columns that have to exist:

- `id` (bead id, paper slug, Keep marker, or vault block id)
- `status` (`pending` / `in_hop` / `done` / `skip` / `needs_bryan`)
- `verdict` (one line)
- `artifact` (the `research:` or `file:explicit:` ref this hop registered)
- `hop` (agent name)

The successor reads **only** this file plus the next item's source. It does not inherit a 200k-token chat.

### 3.2 Hop contract

Each hop, in order:

1. Claim the first `pending` row (`in_hop`, write the agent name).
2. Do **one** unit. Not two. Not "and also I noticed."
3. Write the verdict and artifact ref. Set `done` / `skip` / `needs_bryan`.
4. Commit (host finalizer) or register an explicit snapshot (`sase artifact create`).
5. If pending rows remain **and** this is not hop 7 of the chain, `sase pipe -f` with the **same** prompt.
6. If this is hop 7, write a synthesis section at the top of the ledger ("what changed, what's next, relaunch command") and **stop**.
7. If the queue is empty, stop. Do not invent work.

Discovered follow-ups go on the current item as `needs_bryan` or, for code, through `/sase_new_task`. They do not get silently pushed onto the front of the queue.

### 3.3 Restart prompt (the thing you paste after hop 8)

The relaunch is the original prompt plus one paragraph:

> Continue the same loop. The queue is `research:202609/loopable_high_value_48h_token_window/queue.md`. Skip every non-`pending` row. If the queue is empty, stop and report yield. If you are hop 7 of this chain, synthesize and stop.

That is the whole trick. The prompt does not change. The ledger does.

### 3.4 When *not* to use `sase pipe`

| Job | Mechanism |
| --- | --- |
| One bounded unit, same prompt, serial | `sase pipe -f` (this report) |
| Already-planned epic with phases | `sase bead work <epic>` |
| Parallel helpers / a research swarm | `sase run` / LaunchApproval, `max_slots` honest |
| Long command, CI, sleep | `/sase_monitor`, not pipe |
| Map-reduce over traces | bundled `learn-traces` workflow, not a handoff chain |

---

## 4. Ranked recommendations

I would run these in this order. Rank is "do this with the burst," not "this is the most important thing in the universe." Host saturation, the 97-epic pile, and today's plan all beat abstract elegance.

### 1. Sase backlog honesty pass (stale epics + refilled ready queue)

**Why this is #1.** 97 in-progress epics, 49 older than two weeks, 161 unblocked ready tasks after a drain epic that already closed. The machine is generating work faster than it can land it. A 48-hour implementation binge on sase adds to 174 in-progress beads. A 48-hour *reading* binge produces a kill / keep / drain / snooze ledger that makes every later agent cheaper.

The 2026-09-20 triage (`sase-14n`) proved the shape: classify, then epic only the survivors. That epic closed 2026-09-22. The ready queue is full again. The missing piece is a **fresh honesty pass**, not another implement-everything epic.

**Loop.** Two queues, same prompt template:

- Queue A: in-progress epics older than 7 days, oldest first (`sase-j7`, `sase-kp`, `sase-jx`, `sase-lh`, …).
- Queue B: unblocked ready tasks, `+N` descending, then small/medium bugs before flakes.

One hop = one epic or three ready beads (ready beads are shorter). Verdict allowed values:

- `keep` — live, has a runner or a clear next action
- `relaunch` — stranded, `sase bead work` would recover
- `close-candidate` — done in the tree, or superseded; do **not** close from the loop
- `snooze-candidate` — stale flake, no live `selection_health` hit
- `duplicate-of <id>` — +1 the survivor instead
- `drain-now` — small/medium, diagnosed, unblocked, not owned by a live epic

Write the next proposed drain epic as a markdown draft (phases, sizes, exclusions). Do not launch it from the loop. Bryan launches it.

**Stop.** Both queues empty, or hop-7 synthesis, or 48 hours.

**48-hour yield.** A ranked `close-candidate` list for the 49 stale epics; a clustered ready-queue; a draft drain epic that is the successor to `sase-14n`. That is worth more than 20 more half-landed phases.

**Risks.** Closing the wrong epic. Mitigation: the loop never closes, never `bead rm`s, never launches. It only writes verdicts. Visual/flake beads get `snooze-candidate` unless `selection_health` still names the node.

**Prompt stem.** "You are the honesty-pass worker. Open the sase repo. Read the queue file. Take the next pending id. Read the bead with `sase bead read`. Check live agents with `sase agent list -j` so you do not mark a running clan `close-candidate`. Write a verdict. Update the queue. Pipe if pending remains and you are not hop 7."

---

### 2. Drain bob-cli ready S/M beads, clippy first

**Why this is #2.** Seventeen unblocked ready beads on the current project. Eleven are small. Clippy (`bob-cli-v`, +6) has grown from 3 warnings to ~19 locations; every land agent still diffs clippy by hand to prove it added none (`bob-cli-2f`, `2k`, `2n`, `2o`, `2y` all said so in the last 48 hours). That tax hits *this* project's every epic, including the ones landing tonight.

This queue actually fits the window. Two or three pipe batches of 7 clear the S/M set. The three larges (`bob-cli-1q` PDF policy, `bob-cli-21` artifact-link `operation_id`, `bob-cli-2i` / `2l` picker and relocation) are skip-or-plan, not hop work.

**Suggested hop order** (skip anything still owned by `bob-cli-28/31/32`):

1. `bob-cli-v` clippy warnings (one hop can take several idiomatic fixes; do not flip `-D warnings` until `bob-cli-28` has landed the deny-level `|| true` issue it owns).
2. `bob-cli-2q` — tomorrow's daily note after 8pm EDT on apollo (UTC vs America/New_York). User-facing, every evening.
3. `bob-cli-2e`, `bob-cli-2t`, `bob-cli-2m` — test isolation / close-summary / gkeep_auth panic. Small, diagnosed.
4. `bob-cli-30` — Mac crontab vs `docs/vault-git-sync.md`.
5. `bob-cli-2x` — Cancel Log glossary term. Tiny.
6. `bob-cli-1x` — document watching bob-mac-capture CI.
7. `bob-cli-22` if still reproducible; else skip with evidence.
8. `bob-cli-20` UX copy — needs the running Mac app; mark `needs_bryan` if this hop is headless.
9. `bob-cli-2j` / `bob-cli-2u` medium features if time remains and they do not overlap `bob-cli-28`.
10. Leave `bob-cli-1g`/`1q` for recommendation 6. Leave `bob-cli-21` for a plan.

**Loop.** `sase bead ready` is the queue. One bead per hop. `sase bead work <id>` is allowed *inside* the hop if TaskTriage already approved it; otherwise the hop implements in this session, verifies with `just check` (or the named tool), and closes with a verification note.

**Stop.** No S/M ready beads remain, or a hop fails `just check` on an unrelated red — then write the red into the ledger and stop rather than "fix CI" as a side quest.

**48-hour yield.** Clippy baseline gone; 8–12 ready beads closed; landings stop paying the warning-diff tax.

**Risks.** Colliding with `bob-cli-28` on capture files. Mitigation: skip any bead whose files are in that epic's open phases. Do not touch visual PNG goldens.

---

### 3. Ten-paper follow-up reading loop (already on today's plan)

**Why this is #3.** Today's READ theme is literally this: `[*] Collect and read papers from [[ref/chat/sase_paper_followup_reading_list]]`. The list is already curated (Oct 2025 – Sep 2026), with a suggested order, and the bottom line of that list is the playbook for *this* 48-hour window: durable state beats conversational memory; verification is the bottleneck; resets with a handoff artifact beat compaction.

This is the one recommendation that *only* makes sense because tokens are briefly cheap. Next week you will not spend a frontier model on MAGE plus Tang's 20,574-session failure study. This week you should.

The ten, in the list's own order:

1. OpenAI (Lopopolo), *Harness engineering* (2026-02-11)
2. Anthropic, *Effective harnesses for long-running agents* + sequel (2025-11-26 / 2026-03-24)
3. METR, *Many SWE-bench-Passing PRs Would Not Be Merged* (2026-03-10) — with Spotify Honk
4. Tang et al., *How Coding Agents Fail Their Users* (2026-05-28)
5. He et al. (CMU), *Speed at the Cost of Quality* (MSR '26)
6. Gorinova et al., *Coding Benchmarks Are Misaligned with Agentic SE* (KDD '26)
7. Enemy / sabotage detection paper (#10 on the list)
8. Wang et al., *Humans are Missing from AI Coding Agent Research* (2026-07-04)
9. *Ask or Assume* (#9)
10. Davis et al., *MAGE* (2026-08-25) last, as synthesis

**Loop.** One paper per hop. Output is a research note in this same month directory: what the paper claims, what it measured, what it would change in sase or bob (memory, beads, ACE, MRP, handoff artifacts, verifier gates), and whether a `decisions:` strand should be drafted. Register the note. Do not implement.

Hop 7 of chain 1 synthesizes papers 1–6 against current sase behavior (pipe chain 8, bead honesty, visual flakes). Chain 2 does 7–10 plus a "what we should change this quarter" page.

**Stop.** Ten notes + one synthesis, or the 48 hours end.

**48-hour yield.** A cited implication set you can turn into decisions after the window, when tokens are scarce again. Directly feeds recommendation 1's "what good landing looks like."

**Risks.** Reading without writing implications is tourism. The hop contract requires 3–5 concrete sase/bob changes or an explicit "no change." Skipping Anthropic's pair would be a mistake: it is the design doc for the loop kit in §3.

---

### 4. GKeep 65-idea triage (the inbox is already pulled)

**Why this is #4.** `gkeep_inbox.md` has 65 open `#task` lines with Keep source markers, last touched 2026-10-01. The 2026-09-28 research (`bob_gkeep_inbox_drain`) was about *building* `bob gkeep pull`. That pull is in use. The remaining job is GTD: each note is a product idea, a personal errand, or noise.

Examples already in the file: `%tab` directive, merge `N`/`w` into `d`, `/fleet` Telegram uptime, rename runners→load, `%wait` targeting xprompt swarms, live tool output in the tools panel, xprompts bundling referenced files, bead confidence by model tier, "Download Batman: Nightfall," "Pirate T25."

Dumping all 65 into `sase bead create` would refill the ready queue that recommendation 1 is trying to make honest. The loop's job is **triage**, with a hard cap of new beads per hop (I would cap at 1, size required, `/sase_new_task` first).

**Loop.** One Keep task per hop (or a batch of 5 with the same verdict type if they are clearly skip). Verdicts: `file-bead` / `already-exists <id>` / `schedule` / `do-now` (only if it is a 2-minute personal action) / `drop`. Archive-in-Keep is out of scope for the hop unless `bob gkeep` already has a safe archive path and the vault write is verified.

**Stop.** 65 rows done, or hop-7 synthesis with remaining count.

**48-hour yield.** Empty Keep-inbox task list; a handful of well-sized sase beads; personal items scheduled instead of living as fake engineering work.

**Risks.** Creating 65 ready beads. Mitigation: cap, duplicate check, no features without a size and a why.

---

### 5. NEXT / PENDING lane hygiene (today's GTD morning review)

**Why this is #5.** `bob plan` on 2026-09-30: NEXT 28/15, PENDING 49/10. Those warnings are the daily-driver friction. Today's BOB theme includes `[/] #prj Improve GTD morning review process!` (already launched `apollo.research.v` — coordinate, do not fork a competing design).

`bob-cli-31` is shipping *freshness leases* for Ready tasks. This loop is the complementary **human-lane** pass: which of the 77 overflowing Next/Pending tasks should Bryan Alt+N back to Ready, and which are correctly on the board.

**Loop.** One hop reviews 5 overflowing tasks. Output is a checklist: keep / release-with-reason / convert-to-scheduled / already-done. The hop does **not** change task status. Sticky-lane policy (`decisions:task-lanes-are-sticky`) says only Bryan's Alt+N release lowers Next/Pending.

**Stop.** All 77 reviewed, or Bryan has a one-page "release these 20" list and walks it in a single sitting.

**48-hour yield.** Plan caps honored tomorrow morning. The morning-review project gets an evidence pack instead of another theory.

**Risks.** An agent that "helpfully" strips Next. Forbidden. Read `decisions:task-lanes-are-sticky` and `decisions:today-is-read-from-the-ledger` before the first hop.

---

### 6. Vault durability: untracked files (`bob-cli-1g`) + PDF policy (`bob-cli-1q`)

**Why this is #6.** After the Obsidian Sync cutover, 86–96 vault files (~24 MB) — `.xmind`, `.zot`, `_meta/migration` TSV/JSON, helper `.py` — have **no off-machine copy**. `bob-cli-1n.land`'s +1 said Sync is disabled and git still ignores them. That is a data-loss bug, not a tidy-up.

`bob-cli-1q` (large) is the PDF-policy decision that has to be written before a blind `.gitignore` rewrite: `lit_review/` (~430 MB) out of band, `xlib/` rsynced, `lib/**` PDFs as D3's bounded exception, 23 already-tracked PDFs that must not vanish from the MacBook on the next pull.

**Loop.** This is a **research-then-plan** loop, not an implement loop.

- Hops 1–3: per-extension allowlist decisions for `bob-cli-1g` (keep `.pyc` out; decide `.zot`/`.xmind`/`.tsv`/`.py`/`.puml`).
- Hops 4–6: PDF regimes and a migration that does not delete MacBook files.
- Hop 7: a plan file, not a commit to `~/bob/.gitignore`.

**Stop.** One plan Bryan can approve. Implementation is a later epic, possibly after the window.

**48-hour yield.** A written policy and a sequenced gitignore change. The files still exist on disk either way; the burst is spent on the decision that has been deferred since D3.

**Risks.** A hop that `git add`s 430 MB of `lit_review/`. The hop contract forbids vault-git mutations without an approved plan.

---

### 7. Clippy-to-clean as a dedicated micro-loop (only if #2 is too wide)

If you want the smallest possible same-prompt loop that still pays rent: `bob-cli-v` alone.

One hop: run `cargo clippy --all-targets --all-features --message-format short`, pick the next warning location, apply the idiomatic fix, run the focused test, commit. ~19 locations → 3 batches of 7. Last hop enables `-D warnings` **only if** `bob-cli-28` has already taken the deny-level `|| true` error off the table.

This is a subset of #2. Prefer #2. Use #7 if you want a loop you can leave running overnight with almost no product-judgment.

---

### 8. Decision-web mining from agent transcripts (only after #1 and #3)

The `decisions` web already has five records and a strict "immutable once accepted, cite checkable evidence, ask Bryan rather than infer" rule. Mining chats for more records is token-expensive and compounding.

It is **eighth** because unconstrained mining writes bad law. Run it only with a queue of *named* questions produced by #1 and #3 ("should freshness leases apply to beads?", "is pipe-chain 8 the right long-running harness?"). One candidate strand per hop, left as a draft, never auto-accepted.

---

## 5. What I would not spend the window on

| Idea | Why it fails the filter |
| --- | --- |
| Mass-update ACE PNG goldens (`sase-10u` ~120, `sase-x5` 29) | Collides with `sase-126`. Visuals are load-sensitive. Athena is not a quiet host. |
| Implementing the 161 sase ready beads | That is how you get 97 in-progress epics. Classify first (#1). |
| Starting a new sase product epic (sidebar, sub-tabs, index.lock, v0.18 leftovers) | Those already have in-progress owners (`^better-sidebar`, `^agents-sub-tabs`, `^no-more-index-lock`, `sase-1c1`). |
| Flake-whack-a-mole under the full parallel lane | The ready queue is 89 flakes, many with close/reopen history (see `sase-cx`, +6 and still ready). Needs `selection_health`, not a hop that reruns `just test`. |
| Building `bob gkeep pull` | Already researched 2026-09-28 and in use. Triage the 65 tasks (#4). |
| Re-doing task-freshness product design | `bob-cli-31` is in progress. Lane hygiene (#5) is the complementary pass. |
| actstat | 0 claims, not on today's plan. |
| Horizon-3 `100_cl_goal` (work CLs) | Wrong repo, wrong confidentiality boundary. |
| `/learn` over all Grok traces | Token-heavy and useful, but it is a Grok-harness tuner, not a sase/bob lever, and it wants an interactive curation step. Run it after the window if at all. |
| Parallel `sase run` fan-out of the same queue | Fights athena. Two *different* loops in two sessions is the max I would run at once. |

---

## 6. A 48-hour portfolio if you run more than one session

If you only start **one** loop: **#1 honesty pass**.

If you start **two** (recommended):

- Session A, bob-cli, serial pipe: **#2 ready drain** (clippy first).
- Session B, sase, serial pipe, **read-only**: **#1 honesty pass**.

If the burst is truly unlimited and you can stand a third:

- Session C, research sidecar: **#3 paper loop**.

Do #4 and #5 in the morning GTD sitting, not as overnight agents, unless session B has already finished. Do #6 as a planned follow-up once #1 has a drain epic draft.

Handoff vs launch, in one line: **pipe for the loop; `sase bead work` for the drain epic that #1 proposes; do not launch that epic from the honesty-pass agent.**

---

## 7. Example same-prompt (honesty pass)

Paste this, then paste it again after each chain of 8. Only the queue file has to change.

```text
You are the sase backlog honesty-pass worker.

Open the sase repo with /sase_repo. Read the queue ledger
research:202609/loopable_high_value_48h_token_window/queue.md
(create it from the in-progress epics older than 7d plus
`sase bead ready` if it does not exist).

Take the first row with status pending. Claim it (in_hop, your agent name).
Read that bead with `sase bead read <id> -r "honesty pass"`.
Check `sase agent list -j` so a live clan is never close-candidate.

Write exactly one verdict: keep | relaunch | close-candidate |
snooze-candidate | duplicate-of <id> | drain-now.
Update the ledger. Register any long write-up as an artifact.
Do not close, rm, launch, or implement.

If pending rows remain and this chain has used fewer than 7 pipes,
`sase pipe -f` with this same prompt. If you are hop 7, write a
synthesis at the top of the ledger (counts, proposed drain epic,
relaunch command) and stop. If the queue is empty, stop.
```

Swap the middle paragraph for #2 (one bob-cli ready S/M bead, implement, `just check`, close) or #3 (one paper, implication note, no code).

---

## 8. Confidence and gaps

| Claim | Confidence | Gap |
| --- | --- | --- |
| Pipe chain cap is 8 | High | Merged config `max_agent_pipe_chain: 8` |
| 97 in-progress sase epics, 49 aged 14d+ | High | `sase bead list --status in_progress -t plan -r epic` on 2026-09-30 |
| 161 unblocked sase ready | High | `sase bead ready` summary line; JSON `ready` listing was 312 including blocked |
| bob-cli 17 ready, clippy +6 ~19 locations | High | `sase bead read bob-cli-v` +1 trail through 2026-09-30 |
| Keep inbox already pulled, 65 tasks left | High | `gkeep_inbox.md` source markers; 2026-09-28 drain design is a different job |
| Paper list is today's READ work | High | `bob plan` today_tasks + `sase.md` `^sase-paper-followup-reading` |
| Host no longer has 39 duplicate daemons | Medium | This survey: 1 service, 1 scheduler, load 29. `sase-14x` still READY. Could be intermittent. |
| "Near-infinite tokens" source | Low | Usage cache still shows finite weekly windows. Recommendations do not depend on which provider is bursting. |
| `apollo.research.v` scope vs #5 | Medium | GTD morning-review project is already launched; #5 should attach, not compete. I did not read that agent's live reply. |

I did not read this swarm's peer reports. I did not open live `live_reply.md` drafts for running implementation agents beyond `sase agent list` snippets.

---

## Ranked list (the thing to consider)

1. **Sase backlog honesty pass** — stale in-progress epics + refilled ready queue, verdicts only, draft the next drain epic.
2. **bob-cli ready S/M drain** — clippy first (`bob-cli-v`), then timezone, tests, crontab, glossary; skip the three larges.
3. **Ten-paper follow-up reading loop** — already on today's plan; implication notes, not code.
4. **GKeep 65-idea triage** — pull already exists; file few beads, drop the rest.
5. **NEXT/PENDING hygiene checklist** — 28/15 and 49/10; Bryan still hits Alt+N.
6. **Vault durability plan** — `bob-cli-1g` / `bob-cli-1q`; decide, then later implement.
7. **Clippy-only micro-loop** — use only if #2 feels too wide.
8. **Decision-web mining** — only from questions #1 and #3 produced.

If I had to pick one hop to start before this turn ends: create the honesty-pass queue from the 49 epics older than 14 days and the 161 unblocked ready beads, then pipe. That is the work the burst is for.

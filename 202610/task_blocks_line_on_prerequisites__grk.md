# A machine-owned Blocks line on every task that others wait on

> **Research query:** Automatically add a sub-bullet on tasks that other tasks
> depend on, so a prerequisite shows that it blocks one or more dependents.
> The existing Depends-On line stays on the dependent. The write should happen
> when a dependency is added (Ctrl+Shift+P, for example), and `bob task
> reconcile` should keep every such line present and consistent. Lead the
> design: intuitive, reliable, beautiful. Critique the plan, call out justified
> requirement adjustments, and recommend a solution.

## Bottom line

**Build the reverse view. Do not build a second source of truth, and do not
add one sub-bullet per dependent.**

The request is right about the gap: a task that other tasks wait on is
invisible as a bottleneck until you close it. Successor linking already
answers "what did this unblock?" at close time. Nothing in the note answers
"what will this unblock?" while the task is still open. Live on 2026-10-13,
that gap is small and sharp: **15** open tasks are `is blocking`, against
**473** open tasks and **20** open `is blocked` dependents. One of them,
`cash.md` `^unemployment`, silently holds up four cash tasks. Looking at that
row today, you cannot see any of the four.

The format that fits Bob is the same managed link-row the vault already
speaks, as a **projection** of the Depends-On graph:

```markdown
- [ ] #task Did enrolling for unemployment work! ^unemployment
  - 🚧 **BLOCKS:** [[#^call-north-face]] • [[#^save-verizon-router-pwd]] • [[#^budget]] • [[#^audit]]
```

**Depends-On remains the only authored edge.** Blocks is the dual of
Sub-projects: machine-owned, rewritten from the graph, deleted when empty.
Live writers (Ctrl+Shift+P, capture `&`, chip `×`) update it in the same
gesture that already touches the target for `[id::]`. `bob task reconcile`
rebuilds every Blocks line from the reconciled Depends-On set and is the
authority when a writer skips a target.

I make eight requirement adjustments, **ADJ-1…ADJ-8**, in
[Requirement adjustments](#requirement-adjustments). The full recommendation
is in [Recommended solution](#recommended-solution).

---

## Is this a good idea

**Yes, with the adjustments below.** The evidence:

1. **The question the Depends-On line cannot answer is real.** Depends-On
   tells a blocked task *why it is waiting*. It does not tell a Ready, Next,
   or Pending task *why it matters*. Nine of the fifteen current blockers are
   themselves Blocked; two (`^rahway`, `^save-verizon-router-pwd`) are both
   blocked and blocking. Those chain nodes already carry a Depends-On child.
   Adding the reverse child is how a review landing on unemployment reads as
   a bottleneck instead of an isolated chore.
2. **Close-time successor linking does not cover this.** `docs/task-dependencies.md`
   §12 links dependents into today's ledger only when a planned predecessor
   *fully* unblocks them. That is the right close gesture. It is silent for
   the whole life of the edge, and silent when a close leaves the dependent
   still blocked (SL3, still waits on Q).
3. **Read-time `is blocking` already exists and is unused in the note.**
   Obsidian Tasks computes `Task.isBlocking()` from `[id::]` plus others'
   `[dependsOn::]`. Bob's native engine ports that (`apply_dependencies` in
   `src/native/dataview/tasks/index.rs`). Dashboards can filter `is blocking`
   today. Bryan does not see that filter when the cursor is on the task in
   source, vim, or the review walk.
4. **The graph is tiny.** 15 blockers, max fan-in 4, 21 open edges, 12 of 15
   blockers have a single waiter. A second managed line on those 15 tasks is
   cheap. One child per waiter would already be four extra bullets under
   unemployment, stacked with Schedule Log and notes — the same bloat
   `decisions:task-deps-are-depends-on-links` rejected on the dependent side.
5. **Jira's lesson is bidirectional *labels* on one stored edge, not two
   stored edges.** A Jira "Blocks" link is one record with outward "blocks"
   and inward "is blocked by". Teams that store both directions as separate
   records spend their lives unscrewing inversions (Atlassian KBs on inverted
   Blocks / Is blocked by; Tasks issue #3605 on modal inversion). Obsidian
   Tasks shipped a stored `blockedBy` field and **renamed it to `dependsOn`**
   in 6.1.0 specifically "to fix blocked by ambiguity" (PR #2568 / #2639).
   Bob already paid that tax once: the Task Card's `b` row is labelled
   **Blocked by…** and writes the Depends-On line.

**What the request leaves out** (each item is handled below):

- Which copy is authoritative if both ends store links.
- One managed line versus one bullet per dependent.
- Closed dependents, project inheritance, and `^prj`.
- A Tasks `[blockedBy::]` field.
- Editing the reverse line by hand, Ctrl+D, and chip `×`.
- Parser collision with Task Links, R8 legacy children, Sub-projects, and
  logs.
- Immediate write versus waiting for the MacBook's 15-minute reconcile.

---

## Critique of the plan as stated

The plan as given is: *when a dependency is added, automatically add a
sub-bullet on the prerequisite; reconcile keeps those bullets consistent.*

That sentence is directionally right and underspecified in the places that
caused the last dependency redesign.

**"A new sub-bullet"** will be read as one child per waiter. That is the
option the Depends-On decision already rejected: "One bullet per dependency.
Unbounded children bloat the task block and collide with logs and notes."
The reverse is worse, because fan-in concentrates: unemployment is one
task, four waiters, plus its own logs. A single ` • `-separated line is the
format the vault already uses for Depends-On and Sub-projects.

**"Automatically when dependencies are added"** is the right *moment* and the
wrong *authority* if it means every writer dual-updates two authored lines.
Depends-On has eight write paths (Task Card / stage, chip `＋`/`×`, capture
`&`, hand-edit debounce, Ctrl+D, project conversion, move, archive). The
whole point of R1–R10 was that those paths drifted when two copies were
co-equal. A reverse line that is also authored recreates that drift on
every add, remove, move, and close.

**"`bob task reconcile` should ensure consistency"** is the load-bearing
clause, and it should be stronger than the live writers: reconcile *rebuilds*
the reverse from the Depends-On graph. Live writers may write it early for
feedback, the way keymaps already apply Blocked early. They must not be a
second graph.

**Beauty is not a coat of paint on a second bullet list.** The Depends-On
redesign already learned that a bare `[[note#^id]]` in Live Preview renders
as `note > ^id`, and that without chips the format swings back to embeds.
A Blocks line that is not chipped will look like a worse Depends-On line
pointing the wrong way.

**I would not skip the in-note line** in favour of chips-only or a dashboard
query. Bryan reads tasks in source, vim, and git. Agents read the same
Markdown. A decoration that dies with the plugin fails the "reliable" test
the same way a field-only dependency did. The line is the human copy; chips
are the Live Preview of that copy.

---

## Requirement adjustments

| # | You asked | I recommend | Why |
| --- | --- | --- | --- |
| **ADJ-1** | "A new sub-bullet" on the prerequisite | **One** managed first-class child line listing every open waiter, same grammar as Depends-On. Never one bullet per dependent. | Unbounded children collide with Schedule Log, Work Log, Sub-projects, and notes. Fan-in is already 4 on one live task. The vault's visual language for "several related links" is ` • ` on one labelled line. |
| **ADJ-2** | The reverse bullet is added "automatically" as if it were a peer of Depends-On | Depends-On stays the **only source of truth**. Blocks is a **machine-owned projection**, fully rewritten like `🧩 **Sub-projects:**`. | Dual-authored edges invert (Jira, Tasks modal #3605). Bob already chose "line is truth, field is derived" for Depends-On. A second authored line would be a third copy of the same edge. |
| **ADJ-3** | (implicit: store whatever Tasks needs) | **No `[blockedBy::]` field.** Tasks already computes `is blocking` from `[id::]` + others' `[dependsOn::]`. | Tasks renamed stored `blockedBy` to `dependsOn` to end the direction clash. A reverse field is a third drift surface and a CSS-hiding chore with no query gain. |
| **ADJ-4** | "Indicate that the task blocks one or more other tasks" | Show **open dependents only**. Drop a waiter when it closes, cancels, or leaves the graph. Delete the line when the last open waiter is gone. Never strike, never keep a closed-task ledger on the blocker. | Closed history already lives on the *dependent's* Depends-On line and in the Pomodoro successor link. A growing strike-ledger on a popular blocker is unbounded and contradicts the "no stored strikes" Depends-On rule. |
| **ADJ-5** | Happen when deps are added via Ctrl+Shift+P | Live writers that already prepare the target (`[id::]`, `^block-id`) **also upsert the Blocks line in that same target write**. Reconcile backfills, heals, and is the authority. A reverse failure never rolls back the Depends-On write. | Waiting up to 15 minutes would make the feature feel broken, the same reason ADJ-8 of the Depends-On research unblocked immediately. Nav already has a prepare-target phase. |
| **ADJ-6** | (implicit: the new line is editable) | Hand-editing Blocks is **not an edit of the graph**. Reconcile rewrites it. Chip `×` and any future Blocks stage write **through** to the waiter's Depends-On line. Ctrl+D on Blocks is **refused**. | Otherwise deleting a chip on the blocker silently disagrees with the dependent, and Ctrl+D would rewrite every waiter in one chord. |
| **ADJ-7** | (implicit: include project blocking) | Blocks lists **Depends-On waiters only**. Inherited `#prj_is_blocked` residents and Sub-projects children are not Blocks chips. | Project membership already has a machine-owned line. Mixing inheritance into Blocks would make every `^prj` list the whole note. |
| **ADJ-8** | (implicit: Task Card grows a row) | **No new Task Card row in v1.** `b` stays "Blocked by…" / Depends-On. The reverse appears because that gesture already ran. A `k` "Blocks…" stage that adds waiters by writing *their* Depends-On lines is a later additive. | v1 is "the graph becomes visible both ways." A second picker is a second product. The card is already dense (`Enter`, `b`, `f`, `Alt+N`, `x`). |

---

## Live vault evidence (2026-10-13)

Native Tasks query `(not done)`, deduped on `(path, line, id, description)`:

| Quantity | Count |
| --- | --- |
| Open tasks | 473 |
| Open with `[dependsOn::]` | 33 |
| Open `is blocked` (unfinished prerequisite) | 20 |
| Open `is blocking` (would gain a Blocks line) | 15 |
| Both blocked and blocking (chain nodes) | 2 |
| Open Depends-On edges | 21 |
| Fan-out of blocked tasks | 19 wait on 1, 1 waits on 2 |
| Fan-in of blockers | 12 have 1 waiter, one has 2, one has 3, one has 4 |

Highest fan-in, the motivating picture:

```text
cash.md ^unemployment   "Did enrolling for unemployment work!"
  blocks 4
    cash.md  Dispute North Face jacket delivery!
    cash.md  Get access to all of your money!
    cash.md  Save Verizon Router password…
    cash.md  Audit monthly subscriptions
```

Cross-note waiters already exist (`gkeep_inbox.md` waits on
`sase_post_blog#^dynamic-agents-md`; `job.md` waits on a goals ref;
`sase_foo.md` `^prj` waits on `sase#^bar`). The reverse line has to use the
same shortest-link rules as Depends-On (`[[#^id]]` / `[[basename#^id]]` /
`[[dir/note#^id]]`, explicit `done/` never needed here because waiters are
open).

Thirteen open tasks carry `[dependsOn::]` and are *not* `is blocked`: their
prerequisites are already done and remain as Depends-On history. Those
thirteen must **not** appear on a closed prerequisite's Blocks line
(ADJ-4).

---

## What already exists

Bob is closer to this feature than the request implies. The missing piece is
an in-note reverse *copy*, not a reverse *graph*.

| Piece | Where it lives | What it gives us |
| --- | --- | --- |
| Authored edge | `⛓️ **DEPENDS ON:**` first child; `[dependsOn::]` / `[id::]` derived | R1–R10, chips, stage, capture `&` |
| Read-time reverse | Tasks `is blocking` / `Task.isBlocking()`; Bob `apply_dependencies` | Dashboard filter, no Markdown |
| Close-time reverse | Successor links, `unblocked_by`, Unblocked card (§12) | Ledger placement when the last blocker falls |
| Machine-owned sibling line | `🧩 **Sub-projects:**` after Depends-On on `^prj` | Rewrite-in-place, delete-when-empty, ` • ` links, closed ledger (which Blocks should **not** copy) |
| Target prepare write | Nav §6.6 step 1: add `^id` and `[id::]` on the prerequisite first | The exact I/O slot for a Blocks upsert |
| Reverse index at close | Capture dependents snapshot; cycler Tasks-cache `id → dependents` | Reconcile can build the same map every run |
| Label already taken | Task Card `b` = **Blocked by…** | Do not name the reverse line "Blocked by" |
| Rejected shape | `decisions:task-deps-are-depends-on-links`: one bullet per dependency | Bind the reverse to the same rejection |
| Quiet interval | Structural writes defer notes modified < 2 s | Nav's immediate Blocks write may win; reconcile heals on the next run |

Managed-marker roster today, all unique, all first-class children:

```text
❌ **CANCEL LOG**          first slot when present
⛓️ **DEPENDS ON:**         first, or second after Cancel Log
🧩 **Sub-projects:**       ^prj only, after the Depends-On subtree
🗓️ **SCHEDULE LOG**
🛠️ **WORK LOG**
```

Blocks slots in as the outbound twin of Depends-On, before Sub-projects.

---

## Alternatives

### A. One child bullet per waiter (literal reading of the request)

```markdown
- [ ] #task Did enrolling for unemployment work!
  - [[#^call-north-face]]
  - [[#^save-verizon-router-pwd]]
  - [[#^audit]]
```

Rejected. Collides with R8 (a sole block-link child is still a legacy
dependency during the legacy window), with Task Link recognisers, with
logs, and with the "one line" rule that just shipped. Four waiters is
already noisy; a popular `^prj` would be worse if anyone later weakened
ADJ-7.

### B. Dual-authored Depends-On + Blocks (two sources of truth)

Every add writes both ends; a hand edit of either is honoured. This is
Jira-without-a-database. The last redesign's entire R-table exists because
Bob cannot keep two authored copies honest across nav, capture, hooks, vim,
and the Tasks modal. Rejected.

### C. Chips or a Task Card badge, no Markdown child

A Live Preview decoration on the task line, `🚧 4`, sourced from the Tasks
cache. Beautiful in Obsidian, invisible in vim, git, and agent context, and
gone if ledger-tools is off. The Depends-On fallback without the plugin is
still a readable line; Blocks should be too. Rejected as the *only* surface.
Chips remain mandatory *on* the line (see below).

### D. Dashboard / `is blocking` query only

Already possible. Does not help the review walk, the Task Card, or a vim
session on `cash.md`. Complementary, not sufficient.

### E. Store `[blockedBy::]` on the waiter or the blocker

Tasks does not have this field. Adding it fights the 6.1.0 rename and
creates a third copy. Rejected.

### F. Read-time reverse only inside reconcile, no live write

Correct authority, 15-minute hole after Ctrl+Shift+P. Feels broken on the
gesture the user named. Rejected as the *only* writer; kept as the healer.

### G. Recommended: projection line + live upsert + chips (this report)

One machine-owned `🚧 **BLOCKS:**` line, regenerated from the Depends-On
graph, upserted early by the writers that already touch the target, chipped
like Depends-On.

---

## Recommended design

### Grammar

Writer form, mirroring `docs/task-dependencies.md` §2.1:

```text
<indent>- 🚧 **BLOCKS:** [[#^a]] • [[note#^b]]
```

- Emoji `🚧` (U+1F6A7). Distinct from `⛓️` Depends-On, `🧩` Sub-projects,
  `🗓️` Schedule, `🛠️` Work, `❌` Cancel. Tasks' `⛔` stays on the
  *dependent* field in Tasks' own rendering; do not reuse it here.
- Label `**BLOCKS:**`, always uppercase, always with the colon, same
  `**…:**` shape as Depends-On.
- Links: shortest unambiguous block links, no aliases, no embeds, no
  strikes. Separator ` • `.
- Empty list: **delete the line**. No placeholder.
- Reader tolerance: missing emoji, optional VS16, `BLOCKING` as a legacy
  label, `·` / `,` / whitespace separators, aliases / strikes / `!` (all
  canonicalised away). Lowercase `blocks` is not a line (same as DP27).

Share the Depends-On link scanner. Do not split on separators. Malformed
residue still makes a *parse* of `malformed` — and unlike Depends-On R10,
a malformed Blocks line is **rewritten** (ADJ-2: it is not user-owned).

### Position

Direct child of the **prerequisite** `#task`:

1. `❌ **CANCEL LOG**` if present.
2. `⛓️ **DEPENDS ON:**` if present.
3. `🚧 **BLOCKS:**` — after Depends-On, or in the Depends-On slot when the
   blocker has no prerequisites of its own.
4. `🧩 **Sub-projects:**` on `^prj` (sync's "after the Depends-On subtree"
   becomes "after Depends-On and Blocks").
5. Schedule Log, Work Log, user notes.

Reuse the task's existing child indent; otherwise parent indent plus one
tab. Preserve line endings and final-newline state. Never move user-owned
children. Duplicate Blocks lines collapse to one.

A chain node (the two live examples) then reads as a pair:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! ^rahway
  - ⛓️ **DEPENDS ON:** [[#^hospital-swarm]]
  - 🚧 **BLOCKS:** [[#^doctor-followup]]
  - 🗓️ **SCHEDULE LOG**
```

Inbound chain, then outbound chain, then logs. That is the intuitive order.

### Authority and the B-table

Depends-On R1–R10 run first. Then, on the reconciled graph of **open**
tasks:

| # | Situation | Resolution |
| --- | --- | --- |
| B1 | Open task T is `is blocking`: set of open dependents D whose Depends-On set contains T | Upsert a canonical Blocks line whose links are exactly those D, in stable order. |
| B2 | Open T has a Blocks line and is no longer blocking | Delete the line. |
| B3 | Closed / cancelled T still has a Blocks line | Delete the line (the one exception to "never touch closed dependents" — closed tasks are not dependents here; they are stale *owners* of a projection). |
| B4 | Duplicate Blocks lines | Keep the first in document order, remove the rest. |
| B5 | Malformed or non-canonical Blocks | Rewrite to writer form from the graph. Prose on the line is discarded. |
| B6 | Existing well-formed Blocks | Keep waiters that still belong, in current order; append newly discovered waiters (path, then line); drop the rest. No re-sort of survivors. |
| B7 | Waiter has no `^block-id` | Same as today: the Depends-On writer already mints / requires one before the edge exists. Blocks never points at a waiter that the forward line could not name. |
| B8 | Cycle | Both ends may carry both lines. No extra warning; R7 already warned on the forward graph. |
| B9 | Project-inherited Blocked residents with no Depends-On edge to this task | Not listed (ADJ-7). |
| B10 | Second reconcile over a settled vault | Zero Blocks edits (idempotent, sibling of DR22). |

Stable order (B6) avoids noisy diffs. A brand-new line (no survivors) is
emitted in path-then-line order.

Reconcile reports `blocks_projection_updates` with kinds `line_written`,
`line_removed`, `canonicalized`, and `duplicates_removed`.

### Live writers

Nav §6.6 already:

1. Prepares cross-note targets (`^id`, `[id::]`) via open editor or
   preimage-checked `vault.process`.
2. Commits the dependent in one editor transaction.
3. Consumes Pomodoro links on `^prj` block.

**Step 1 grows a Blocks upsert** for each added target (append this
dependent's shortest link) and a Blocks rewrite/delete for each removed
target. Same-note targets fold into step 2's transaction so one Ctrl+Z
still undoes a same-note add. Cross-note undo stays two-notes, as `[id::]`
stamping already is.

Capture `&` already stamps `[id::]` on named prerequisites in the staged
batch. The same batch writes their Blocks lines.

Hand-edit debounce of a Depends-On line (nav applies R1/R9 when the cursor
leaves) should schedule a Blocks upsert on each added/removed target. If
that extra write is too much for the debounce, skip it: reconcile heals
within one hooks interval. Document the delay.

Ctrl+D on Depends-On already deletes the forward line and recovers the
dependent; it must also drop this dependent from each target's Blocks line.

`bob capture` close, cycler Ctrl+Enter, and Alt+] into Done **do not** have
to rewrite Blocks in v1 if B3/B2 run on the next reconcile. Prefer dropping
the closer from its predecessors' Blocks lines in the same close write when
the predecessor note is already being read for successor linking — the
dependents snapshot is sitting in memory. Cheap, and the unemployment row
loses waiters as they complete instead of 15 minutes later.

### What the line is not allowed to be

Extend `docs/task-dependencies.md` §2.4: every Task Link, Pomodoro-link,
section-title, R8-legacy-child, and managed-log recogniser in Rust, nav,
ledger-tools, cycler, and block-id-prompt must reject a Blocks line the
same way they reject Depends-On. A labelled multi-link line is already not
a "sole contents is one block link" Task Link; still pin vectors so a
future parser does not get clever.

`projects sync` treats only a direct Depends-On child of `^prj` as the
Depends-On subtree. It must skip Blocks the same way it skips user-owned
wikilink children, and it must insert Sub-projects *after* Blocks when both
exist.

### Chips (beauty)

Reuse the ledger-tools Depends-On chip pipeline. Prefilter on `BLOCKS` as
well as `DEPENDS ON`. Same miniature checkbox, 40-character text, `↗ note`,
tooltip, click-to-open, hover preview, wrap-between-chips, no line-height
change, colour from `--task-status-*`.

```text
[ ] Did enrolling for unemployment work!
    🚧 blocks  ( ○ Dispute North Face jacket delivery )  ( ○ Get access to all of your money )  ( / Save Verizon Router password ↗ )  ( ○ Audit monthly subscriptions )   unlocking 4
```

| Depends-On | Blocks |
| --- | --- |
| label `depends on` | label `blocks` |
| summary `waiting on N` / `✓ all clear` | summary `unlocking N` / delete the line when N = 0 |
| chip `×` removes a **prerequisite** from this task | chip `×` removes **this task** from that waiter's Depends-On (write-through, ADJ-6) |
| trailing `＋` opens the Depends-On stage | **no `＋` in v1** (ADJ-8) |

Done waiters are not on the line (ADJ-4), so there is no `✓×N` collapse to
design. If a waiter is itself Blocked, the chip uses the Blocked colour —
that is the chain signal.

Without the plugin, source still reads:

```text
🚧 BLOCKS: ^call-north-face • cash > ^save-verizon-router-pwd
```

Cursor on the line reveals raw Markdown, same as Depends-On. Source mode
stays raw.

Ship chips before reconcile starts emitting lines, for the same reason the
Depends-On rollout did: a vault full of unchipped `[[note#^id]]` rows is
how the format dies.

### Gestures that must not happen

| Gesture | Behaviour |
| --- | --- |
| Ctrl+D on the Blocks line | Refused. Notice: *This line is a projection. Remove a waiter from its Depends-On line.* |
| `!` on the Blocks line | Refused, same notice as Depends-On, pointing at Ctrl+Shift+P. |
| Ctrl+Shift+Enter on the Blocks line | Refused. |
| Ctrl+Enter on a link on the Blocks line | Closes the **waiter** (the link target), root-only, then B2/B6 drop it if it is now closed. Same as Ctrl+Enter on a Depends-On link closing the prerequisite. |
| Alt+] / Alt+[ on the line | Cycle the waiter under the cursor. Never reformat. |
| Hand prose on the line | Next reconcile discards it (B5). |
| Tasks modal | Still not an editor of Bob edges. |

### Identity, close, move, archive

- Matching uses `[id::]`, the same identity successor linking uses. A waiter
  whose Depends-On names only a canonical id the target does not yet carry
  is R1's problem, not Blocks'.
- Closing the blocker deletes its Blocks line in the close write when cheap,
  else B3 on reconcile. Successor linking continues to own ledger placement.
- `Ctrl+Shift+M` moves the Blocks line with the task, as it does Depends-On.
  Reconcile rebuilds links on the other end (waiters that still point here;
  this task's Blocks links to waiters that moved).
- `task archive` of a blocker: B3. Archive of a waiter: B2 on each
  predecessor.
- Freshness is never stamped by Blocks writes. Automation never stamps.

### Performance

Fifteen target notes today. The dependents snapshot already built for `!`
and close is the same index (~30 ms when the `[id::]` gate passes; 96% of
closes skip it). Reconcile already walks every open dependent. Projecting
the reverse is an extra map invert plus at most one child rewrite per
blocker. No daemon, no new cache, no Mac-side logic
(`decisions:mac-capture-is-a-thin-client`): capture JSON stays additive
with a `blocks_updates` list of notes the batch touched.

Quiet interval: a Blocks upsert is structural. If nav wrote the target 1 s
ago, hooks defer that note and try again next run. Idempotence makes that
safe.

### Rollout

1. **Contract.** New § in `docs/task-dependencies.md` (grammar, position,
   B-table, chip model, BL vectors). Sub-projects insertion wording in
   `docs/projects.md`.
2. **Recognisers.** Shared "managed link row" parse; every consumer that
   currently calls `is_dependency_line` also ignores Blocks. Vectors first.
3. **Chips** in ledger-tools, feature-detecting nav write-through for `×`.
4. **Reconcile B1–B10.** One hooks run backfills the vault. No separate
   migration script: the forward graph already exists.
5. **Nav prepare-target + capture `&` + Ctrl+D.** Immediate writes.
6. **Close-path drop** (optional in the same epic if the dependents snapshot
   is already in hand).
7. **Glossary + decision.** New decision: *Blocks is a projection of
   Depends-On.* Amend `glossary:task-dependency-link` with one sentence that
   the reverse view is the Blocks line on the prerequisite. Do not invent a
   second glossary term unless the line becomes a gesture target.

Fleet the way Depends-On did: plugins that chip and refuse, then hooks that
write, then live writers. An old hooks runner ignores the new child (it is
not a Depends-On label, not an R8 sole link). An old nav leaves a
reconcile-written line in place. Safe.

### Tests to pin

Copy tables into Rust and JS, citing the section, same discipline as DP / DW
/ DR / DC:

- **BP** parse (accept / empty / malformed / not-a-line), including "Depends-On
  parser returns not-a-line on a Blocks line" and the reverse.
- **BW** write: insert after Depends-On, after Cancel Log with no Depends-On,
  indent, CRLF, delete-when-empty, append-new-waiter, drop-closed-waiter.
- **BR** reconcile B1–B10, including closed-owner cleanup and idempotence.
- **BC** chip model: `unlocking N`, Blocked waiter colour, write-through `×`,
  no `＋`.
- **BG** guards: Task Link / R8 / log / Sub-projects insertion / grouping
  never claim the line.

---

## Naming, because this is how the last one broke

| Surface | Word | Direction |
| --- | --- | --- |
| Task Card `b` | **Blocked by…** | This task waits on others (Depends-On) |
| Managed line on the dependent | **DEPENDS ON** | Same |
| Managed line on the prerequisite | **BLOCKS** | Others wait on this |
| Chip summary on the prerequisite | **unlocking N** | How many open waiters |
| Tasks filter | `is blocking` | Read-time, no field |
| Jira | outward *blocks* / inward *is blocked by* | One stored edge |
| Tasks 6.1.0 | renamed stored `blockedBy` → `dependsOn` | Do not un-rename it |

Never label the reverse line "Blocked by". Never add a Task Card row named
"Blocked by" for the other direction. "Blocks" / "unlocking" is the pair
that does not collide with `b`.

---

## Would I take a different approach

I would still put a child line in the note. I would not:

- treat it as authored,
- emit one bullet per waiter,
- store a reverse Tasks field,
- fold project residents into it,
- wait for reconcile as the only writer,
- ship the line before chips,
- add a Task Card row until the projection has been lived with.

If the feature ever feels noisy, the kill is "stop writing Blocks lines"
(`plan.blocks_line: false` or equivalent), not a second graph. Recovery and
`is blocking` keep working because they never needed the line.

A later Blocks stage (`k`) is attractive: fuzzy-pick a task that should
*wait on this one*, and write *its* Depends-On line. That is Jira's "Link →
blocks". It is also easy to invert in the UI, which is why v1 should teach
the pair with a projection first.

---

## Recommended solution

**Add one machine-owned `🚧 **BLOCKS:**` child on every open task that at
least one open task Depends-On. Keep Depends-On as the only edge. Chip it
like Depends-On. Let Ctrl+Shift+P keep doing what it does, and write the
reverse in the target prepare step it already runs. Let `bob task reconcile`
rebuild the reverse from the graph until it is byte-identical.**

1. **Format (ADJ-1, ADJ-4).** One line, `🚧 **BLOCKS:**` plus shortest
   plain block links joined by ` • `, open waiters only, deleted when
   empty, placed after Depends-On and before Sub-projects.
2. **Authority (ADJ-2, ADJ-3, ADJ-6).** Projection. No `[blockedBy::]`.
   Hand edits lose. Chip `×` writes the waiter's Depends-On. Ctrl+D on
   Blocks is refused.
3. **When (ADJ-5).** Nav / capture / Ctrl+D upsert immediately on targets
   they already touch. Reconcile B1–B10 is the vault-wide healer and the
   backfill. Reverse failure never undoes a forward write.
4. **Scope (ADJ-7, ADJ-8).** Depends-On waiters only. No Task Card row in
   v1. No project-resident dump.
5. **Beauty.** Same chip anatomy as Depends-On, label `blocks`, summary
   `unlocking N`, status colour, `↗ note`, wrap between chips. Most tasks
   stay visually unchanged: only the ~15 current bottlenecks grow a second
   chain line.
6. **Reliability.** Recognisers first, chips second, reconcile third, live
   writers fourth. Shared vectors. Idempotent. Quiet interval respected.
   Four parsers stay in lockstep by extending the existing managed-row
   grammar rather than forking a fifth.

That is the design I would implement.

---

## About this report

- **Researcher:** `research.4d.grk` (independent swarm report).
- **Snapshot:** bob-cli workspace with `docs/task-dependencies.md` as the
  live contract; bob-plugins navigation-hotkeys Task Card `b` = Blocked
  by… / Depends-On; ledger-tools Depends-On chips; vault `~/bob` queried
  2026-10-13 via `bob query --tasks "(not done)"`.
- **Memory read:** `decisions:task-deps-are-depends-on-links`,
  `decisions:projects-block-from-prj-line`,
  `decisions:subprojects-inherit-project-blocking`,
  `glossary:task-dependency-link`, `glossary:task-link`,
  `glossary:project-task`, `cli_rules.md`, `sase_artifacts.md`.
- **Prior research (this sidecar, not this swarm):**
  `research:202610/task_dep_link_depends_on_line/task_dep_link_depends_on_line.md`.
- **Scope:** research only. No code, vault note, config, or memory file was
  changed.

## Sources

**bob-cli**

- `docs/task-dependencies.md` §§2–8, 12, 13.2 (grammar, R1–R10, chips,
  successor links, Sub-projects placement)
- `docs/projects.md` (machine-owned Sub-projects line, Task Card table)
- `src/native/task_dependencies/{mod,parse,format}.rs`
- `src/native/task_status_hooks/reconcile.rs` and `reconcile/apply.rs`
  (child slot after Cancel Log, quiet-interval structural writes)
- `src/native/dataview/tasks/index.rs` `apply_dependencies` (`is_blocking`)
- `src/native/dataview/tasks/parse.rs` (`is blocking` filter)
- `src/native/task_complete/successors.rs` (close-time reverse index)

**bob-plugins**

- `plugins/bob-navigation-hotkeys/src/310-task-card-previews.js`
  (`TASK_CARD_ROW_ORDER`, shortcut `b`)
- `plugins/bob-navigation-hotkeys/src/320-task-card-header.js`
  (label **Blocked by…**)
- `plugins/bob-navigation-hotkeys/src/590-plugin-dependency-stage.js`
  (prepare-target `vault.process`)
- `plugins/bob-ledger-tools/src/140-dependency-model.js` (chip model)
- `plugins/bob-ledger-tools/styles.css` `.bob-dep-chip*`

**Vault**

- Native Tasks `(not done)` / `(not done) AND (is blocked)` /
  `(not done) AND (is blocking)` against `~/bob` on 2026-10-13

**Memory**

- `decisions:task-deps-are-depends-on-links` (one-bullet-per-dep rejected;
  line is source of truth)
- `glossary:task-dependency-link`
- `decisions:mac-capture-is-a-thin-client`

**Upstream**

- [Obsidian Tasks: Task Dependencies](https://publish.obsidian.md/tasks/Getting+Started/Task+Dependencies)
  (`is blocking` / `is blocked` are search relationships; only `id` and
  `dependsOn` are stored)
- Tasks 6.1.0: `dependsOn` rename to fix "blocked by" ambiguity
  ([PR #2568](https://github.com/obsidian-tasks-group/obsidian-tasks/pull/2568),
  [#2639](https://github.com/obsidian-tasks-group/obsidian-tasks/pull/2639))
- Tasks [#3605](https://github.com/obsidian-tasks-group/obsidian-tasks/issues/3605)
  inverted dependencies through the modal
- Jira default link type: outward *blocks*, inward *is blocked by* (one
  stored edge; inverted-label KBs on Cloud and Data Center)

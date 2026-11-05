# Capture `<`: merge existing tasks into the task you are creating

> **Research query.** Add a `< @foo+f` capture syntax that complements the existing
> `> @foo+f`. It is valid only where a capture creates a new task, and it merges each named
> task into the new task with the existing "merged into" relation. Several tasks may follow
> the `<`, for example `Some great new task! @foo^great < @foo+f @bar+b`. The Bob Mac
> Capture preview should be excellent, useful, and concise. Lead the design: critique the
> plan, adjust the requirements where justified (called out clearly), and end with a
> recommended solution that is intuitive, reliable, and beautiful.
>
> **Researcher:** cld · **Date:** 2026-11-05 · **Repos read:** bob-cli `58e98558`
> (master), bob-mac-capture (linked checkout, fast-forwarded to `origin/master` today).
> **Live probes** used the installed `bob 0.4.0`, built 2026-11-05 10:37. No task-merge,
> transfer, relation-merge, or task-block source has changed since that build. Its
> `capture-parse` reports grammar 12, while `docs/capture.md` at HEAD says 13. Probes ran
> in a throwaway vault under `/tmp`; Bryan's vault was never touched.

---

## 0. Summary

**Verdict: build it.** The user-facing idea is right, and `<` is the right spelling. The
semantics already exist in two clumsy forms, so this is mostly about giving them one clean
spelling and one good preview:

1. **`Umbrella ~~foo:f|"merged into" ~~bar:b|"merged into"`.** This works today because
   `merge_labels: [merged into]` is set in Bryan's `~/.config/bob/config.yml`. But it depends
   on that config, repeats the label for every source, uses a different source spelling
   (`note:id`), and its preview reads like a *relation*, not a *merge*. The Mac shows no
   merge card, and the CLI prints `🪢 … now links here · merged into` and then a bare
   `-p 1 · -p all` that never says what offer 1 is.
2. **A two-item draft: `Umbrella @foo^great` ⏎⏎ `@foo+f @bar+b > @foo+great`.** This also
   works today, atomically, with the proper `⤵` merge output and a `created: true`
   merge-target task block. But you must invent the new task's ID and then type it again.

**The key implementation insight: `T < S₁ S₂` desugars exactly to "create T, then
`S₁ S₂ > T`" inside the same capture transaction.** It also lands on fresh ground: epic
`bob-cli-h4` ("Transfer previews") shipped the `>` merge card and landing cards this
week. Build `<` on the explicit `>` merge
path (`MergeGesture::Explicit`), not on the `~~` label path. Every guarantee `>` already
has then carries over unchanged: atomic all-or-nothing writes, destination-first write
order, dry-run parity, rollback, re-pointed dependents, today's-link offers, task blocks,
and the `⤵` human output. The work that is genuinely new is small:

- a lexical claim for `<`;
- a "this item creates exactly one open task" gate with teaching refusals;
- two or three additive JSON facts;
- a Mac card layout that reads in the order you typed it.

**Must-know risk.** `<` is not free syntax today. Bryan's own example
`Some great new task! @foo^great < @foo+f @bar+b` **is valid right now**. It writes the
literal note `Some great new task! @foo^great <` under *both* `^f` and `^b`, because a
trailing `@a+x @b+y` run fans out as sub-bullets. Claiming `<` is therefore a grammar
break. It needs a grammar revision bump, a `!` on the release-train commit, a `\<` escape,
and a ship order (bob first, then the Mac raises its minimum grammar) so that a stale `bob`
can never silently turn a merge into junk notes.

**Adjustments to the request** are in §3 (A1–A11). The most important:

- A1: the `<` clause comes last on its line, and everything about the new task goes
  before it.
- A3: the "creates a new task" rule is spelled out precisely, and an existing-task line
  gets a refusal that offers the exact `>` rewrite.
- A5: `:id` plus `<` puts the new task's link in the Pomodoro slot the sources gave up.
- A6: `<` pickers include ID-less inbox tasks through the existing *Add block ID* flow.
- A9: a later phase adds a `<` "merge in" action to the Similar tasks band.

---

## 1. What exists today (evidence)

### 1.1 `>` transfer lines

`docs/capture.md` §"Moving and merging tasks with `>`" (line 6348) and
`docs/task-merge.md` define the existing syntax. The relevant rules:

- `@a+x @b+y > @c` **moves**. `@c+id`, `@c+id#drawer`, or `@c#section` **merges**.
- The scanner is `scan_transfer_line` (`src/native/capture_language/transfer.rs:146`). It
  claims a line only when **every token before `>` is source-like**. It is recognised
  before target-run fan-out, so a claimed line never falls through to ordinary capture.
- A `>` line carries nothing else. Body text, children, `s:`, `$`, `#`, `%`, `&`, `*`, `~`,
  and `!` all fail with `transfer_extra_text` or `transfer_children`.
- `> +query` opens the vault-wide task picker. `transfer_pending` gives the Mac a calm card
  while the destination is unfinished.
- Execution runs `plan_task_merge` with Explicit gesture semantics and writes the first
  configured merge label, falling back to `merged into`. Writes go target first, then
  dependents, link repairs, the daily note, and the sources last.
- The merge engine contract (`docs/task-merge.md` §§1–7) covers the rest:
  - **Sources:** each source becomes a title bullet with its notes cut beneath. The source
    is cancelled with `🪢 LINKS: merged into [[T]]`.
  - **Target and dependents:** T gains `LINKED FROM … (merged into)`, and open dependents
    re-point to T.
  - **Today's links:** today's links are pruned, and T is offered once at the first slot a
    source vacated.
  - **Refusals:** closed, recurring, `^prj`, open-subtask sources, and cycles refuse the
    whole operation.

### 1.2 Merge labels already merge into a *new* task

`docs/task-relations.md` §21 (ML3/ML6) lists `Umbrella ~~old:id|"merged into"` as "the new
umbrella task folds the picked task into it". It is implemented in
`src/native/capture/relations_merge.rs`, and the opposite direction is refused as
`relation_merges_new_task` (line 77). It is tested by
`tests/cli/capture/relations_merge.rs::from_relation_merges_a_picked_task_into_a_new_capture_task`.
Bryan's deployed config enables it:

```yaml
relations:
  merge_labels: [merged into]
```

Probe: a real run of
`Some great new task! @foo^great #fix ~~foo:f|"merged into" ~~bar:b|"merged into"`
against a fixture vault gives exactly the postimage the request describes:

```markdown
- [-] #task Fix the flaky login test [created:: 2026-10-20] [cancelled:: 2026-11-05] ^f
	- 🪢 **LINKS:** merged into [[#^great]]
- [?] #task Waits on f [created:: 2026-10-20] [dependsOn:: foo__great] ^w
	- ⛓️ **DEPENDS ON:** [[#^great]]
- [ ] #task Some great new task! [type:: FIX] [created::2026-11-05] [id:: foo__great] ^great
	- 🧱 **BLOCKS:** [[#^w]]
	- 🪢 **LINKED FROM:** [[#^f]] (merged into) • [[bar#^b]] (merged into)
	- Fix the flaky login test
		- saw it fail twice on CI
			- trace in gist
	- Login test timeout is too short
		- bump to 30s?
```

`bar.md`'s `^b` became `[-] … 🪢 **LINKS:** merged into [[foo#^great]]`. The daily note's
`[[foo#^f]]` link was pruned, and the offer to link `^great` in its place went unpicked.

### 1.3 A two-item draft also does it today

```text
Some great new task! @foo^great

@foo+f @bar+b > @foo+great
```

A dry run prints the proper merge rendering:

```text
⤵ would merge 2 tasks into “Some great new task!” · foo.md
  ⊘ Fix the flaky login test  foo.md:1 · Next → Cancelled · 1 notes moved
  ⛓ “Waits on f” now waits on “Some great new task!”
  ◌ BUILD link removed · offer 1: link “Some great new task!” under BUILD (-p 1)
  ⊘ Login test timeout is too short  bar.md:1 · Todo → Cancelled · 1 notes moved
```

It also emits a `task_blocks` entry for `^great` with `created: true` and
`roles: ["merge_target"]`. **This is the reference behaviour `<` should reproduce
byte-for-byte**, minus having to type the target twice.

### 1.4 Gaps and defects found on the way

The `>` preview this design builds on is brand new. Epic `bob-cli-h4`, "Transfer
previews" (`plan:202611/transfer_previews.md`), closed all six phases on 2026-11-04/05 and
is landing now. It added:

- the Mac merge card and landing blocks;
- `merge_offers`, including for label merges;
- `transfer_pending` and the refusal cards;
- a reviewer decision, **`tombstones = cards`**: merged sources render as their own
  landing cards, with every run of `removed` rows folded to `⤵ N lines moved to the
  target`.

That plan's non-goals keep `message` strings byte-identical and leave grammar and
completion alone, so `<` is the natural next step on top of it.

These gaps are worth fixing whether or not `<` ships. Each was verified in source at HEAD.

| # | Observation | Where |
| --- | --- | --- |
| G1 | `~~ \| merged into` into a new task gets **no merge card** on the Mac. `CaptureTransferPresentation` returns nil unless `kind` is `task_move`/`task_merge`, but a label merge's item is `kind: task`. The new target also gets no task block; only the tombstones show. | Mac `CaptureTransferPresentation.swift:366`; probe JSON |
| G2 | The human output for a label merge lists only relation lines, then `-p 1 · -p all` with no offer row naming what `1` is. | probe |
| G3 | `MergeRecord.target.created` is `false` for a capture-born target, while that batch's `task_blocks` entry says `created: true`. The Mac already draws a dashed **new** capsule when `target.created == true`, so this one bit hides it. | probe; Mac `CaptureTransferCardView.swift:178` |
| G4 | The copy says `1 notes moved` because the plural is never singularised. The Mac computes its own wording; the CLI and `message` do not. (h4 deliberately kept `message` byte-identical.) | `src/native/task_merge/plan.rs:656` |
| G5 | The merge Pull-In title counts **merged records**, not sources that lost a link. Two merges with one lost link print `Link “T” in place of 2 merged tasks` when it should be `in place of “Fix the flaky login test”`. This follows h4 plan §E literally ("for more than one" merged source), so it is a copy refinement, not a regression. | `src/native/capture/pull_in_copy.rs:611–618` |
| G6 | A merge-source task block pairs the first moved-out note with the new LINKS line as one `changed` row (`- saw it fail…` → `- 🪢 LINKS: merged into…`). h4 plan §A specifies the LINKS line as `added` and cut children as `removed`. The pairing reads as an edit, and it leaves the first cut note outside the `tombstones = cards` "N lines moved" fold. | probe (`task_blocks`, roles `merge_source`); `plan:202611/transfer_previews.md` §A |
| G7 | `>` source pickers drop every ID-less row ("a source needs `+id`"). Plain captures such as `Buy milk` get **no** block ID, so the most natural merge candidates, inbox tasks, cannot be picked. | `src/native/capture_complete/transfer_assist.rs:71–110`; probe |

Where each gap went:

- **G2, G4, G5** are filed as task bead `bob-cli-hi` (bug, medium, related to `bob-cli-h4`).
- **G6** is recorded as a `DISCOVERED ISSUE` note on epic `bob-cli-h4`, which owns that
  contract.
- **G1, G3, G7** belong to the `<` work itself (§6).

### 1.5 What `<` means in today's grammar

These drafts were probed against the installed `bob`:

| Draft | Today |
| --- | --- |
| `Some great new task! @foo^great < @foo+f @bar+b` | **2 sub-bullets**: the note `Some great new task! @foo^great <` under `^f` *and* under `^b` |
| `Fold these < @foo+f @bar+b` | 2 sub-bullets, `Fold these <` |
| `Ship it @foo:great < @foo+f` | sub-bullet `Ship it @foo:great <` under `^f` |
| `Remind me < @work` | task `Remind me <` in `work.md` |
| `@foo+t < @bar+b` | refused: "at opposite ends of the line" |
| `Latency < 200ms check`, `Compare a < b`, `a<@foo+f` | plain task text |

The first three rows are the danger. Each produces a plausible-looking write that is wrong
under the new meaning. §4.8 covers how to ship safely.

---

## 2. Is this a good idea? Critique

### 2.1 Yes, for four reasons

1. **It is a real, frequent GTD move.** "These three inbox scraps are one task" is the most
   common inbox-triage consolidation there is. `>` handles *fold into an existing task*.
   Nothing first-class handles *fold into the task I am naming right now*, which is how the
   thought arrives: you notice the umbrella while you type it.
2. **The capture item is the right home.** The new task keeps the *whole* new-task grammar:
   route, `^id`/`:id`, `#type`, `s:N`, `$N`, `&`, `*`, `~`, authored child bullets, and
   drawers. A `>` line can carry none of these (`transfer_extra_text`). That rules out
   "extend `>` with a new-task destination" as the main design (§2.3).
3. **`<` is the honest mirror of `>`.** In both, the arrow points from the tasks that
   disappear toward the task that grows, and the sources use the same `@route+id` spelling.
   One lexical source grammar and one set of source errors serve both arrows.
4. **The engine work is done.** `plan_task_merge`, its refusals, offers, write order, task
   blocks, and Mac merge card exist and are tested (MG1–MG20). `<` is a parser feature plus
   a gate, not a new engine.

### 2.2 Risks and how to contain them

| Risk | Containment |
| --- | --- |
| Merging is destructive: sources are cancelled and their notes move. | Claim `<` only as a standalone token followed by a source-like token. Show the Mac card before every submit; dry-run equals the real run. Sources that are closed, recurring, `^prj`, or have open subtasks are refused. A failure after T is written leaves the sources intact (a visible duplicate, never a loss). The vault is in git. |
| Grammar break (§1.5) | Grammar revision bump, `\<` escape, `!` release-train commit, bob-first ship order, and a Mac minimum-grammar bump (§4.8). |
| Three spellings of one outcome (`<`, `~~\|merged into`, two-item draft) | Document `<` as **the** capture spelling. `~~\|merged into` stays as the relation/Obsidian-parity path. Make both render through one preview (fixing G1/G3 gives `~~` the new card for free). |
| The new task silently loses source state (Next/In Progress lane, prerequisites, type) | The merge contract says T owns its fields. Keep that, and make each loss **visible**: status transitions on source rows, offer rows, and a prerequisite warning with a one-key fix (A7). |
| Shell users | Unquoted `bob capture X < @foo+f` is an input redirect. zsh fails with "no such file". If a stray `@foo+f` file *does* exist, bob would capture `X` and drop the merge, so add a cheap guard (A11). |

### 2.3 Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Do nothing; teach `~~src\|"merged into"`.** | No. It depends on config, repeats the label per source, uses a second source spelling (`note:id`), and its preview and output are relation-flavoured (G1, G2). Keep it as the relation path. |
| **Extend `>` with a new-task destination** (`@foo+f @bar+b > @foo^great Some great new task!`) | No. It breaks the clean "a `>` line takes one destination and nothing else" contract. The new task's text, modifiers, and children would sit after the sources, and the subject of the item (the new task) would be buried. |
| **A per-source sigil in the modifier family** (`New task <foo:f <bar:b`) | No. A glued `<word` looks like HTML (`<br`, `<div`) and brushes against `<https://…>` autolinks, and it loses the mirror symmetry with `>`. |
| **Accept `<` on existing-task lines too** (`@foo+t < @bar+b` ≡ `@bar+b > @foo+t`) | No, and Bryan's restriction is right. One spelling per operation keeps docs, previews, and muscle memory single-valued. Refuse with the exact `>` rewrite instead (A3). |
| **A Mac-only "merge into new" button** | No. It would break the thin-client decision (`decisions:mac-capture-is-a-thin-client`). |
| **The user's `< @a+x @b+y` arrow-and-run form** | **Yes**, with the adjustments in §3. |

---

## 3. Requirement adjustments (explicitly called out)

Each item is marked **Clarified** (it pins down something the request left open),
**Adjusted** (it changes the request), or **Added** (it goes beyond the request).

**A1. Clarified: the `<` clause is last on its line.** The line is
`<new-task part> < <source> [<source>…]`. Everything about the new task (route, `^id` or
`:id`, `#type`, `s:N`, `$N`, `&`, `*`, `~`, and prose) goes **before** `<`. Only complete
`@route+id` sources may follow. Anything else after the run fails as `merge_in_extra_text`:
"everything about the new task goes before `<`; only `@note+id` tasks follow it". This
mirrors `>`, keeps errors local, and means the left side parses *exactly* as the same line
would without `<`, so no existing new-task behaviour changes. The item's trailing `#type`
edge is the last token before `<`.

**A2. Clarified: sources use the `>` spelling and its lexical rules.** Only `@route+id`
counts as a source. These existing codes are reused unchanged, because their messages
never mention the arrow:

- `transfer_source_suffix` covers `#drawer` or `!` on a source.
- `transfer_source_marker` covers `:id`, `^id`, and `^route:id`.
- `duplicate_capture_target` covers a repeated source.

**A3. Adjusted: "a context that would create a new task" is defined precisely.** `<` is
valid on any line that creates **exactly one ordinary task that is still open when the
capture commits**:

| Item | `<` |
| --- | --- |
| plain text, `@route text`, `@@`-inherited, `@route^id text` | ✅ |
| `@route:id text`, `:id#pomo`, `:id=` (start) | ✅ (see A5) |
| first-level bullets under a `@route` task-list header (each one creates a task) | ✅ (`~~` already works there; probed) |
| `%t` template rows | ✅ (as the expansion) |
| `@route:id=x…` (born and closed in one item) | ❌ `merge_in_closing_task`: "the new task closes as it is born, so it can't take in other tasks; close it in a later item" |
| project-note creation `@route^id@` / `@route:id@` and their bullets | ❌ `merge_in_project_note`: "a new project keeps tasks as tasks: list them as `- ^id` bullets to move them in" |
| existing-task lines (`@foo+t`, `@foo:t`, `^foo:t`, target runs, sub-bullets) | ❌ `merge_in_needs_new_task`, with the rewrite, e.g. "`<` merges into the task this line creates; ^t already exists. Write `@bar+b > @foo+t`" |
| section bullets, Pomodoro notes, URLs/refs, every Pomodoro operator, `!` completions, `>` lines | ❌ `merge_in_needs_new_task` ("this line creates no task") |

The rewrite in the refusal is the key to "intuitive": a misuse teaches the right arrow with
copy-pasteable text. The refusal should also ship it as a structured `rewrite`
(`{range, replacement}`) so the Mac can offer **Use `>`** as a one-key fix.

**A4. Adjusted: build on the explicit merge, not the label merge.** `<` always merges,
even with `merge_labels: []`, and writes the first configured label (fallback
`merged into`), exactly like `>`. An already-closed source is **refused**
(`merge_source_closed`), as `>` does, rather than getting `~~`'s link-only
`already_closed`. Add one improvement to that refusal's copy: name where the source went
when its LINKS line already says so, e.g. "“Fix the flaky login test” is already merged
into “Some great new task!” (foo.md)". That turns an accidental double submit into a
self-explaining no-op.

**A5. Added: `:id` with `<` links the new task in place of what it absorbed.** With plain
composition, `@foo:great …` would link T where its *type* places it, and the merge would
then empty the source's slot (MG10 suppresses the offer). The new task would be in one
Pomodoro and a hole in another. The rule instead:

- If an item both creates a linked task (`:id`, no explicit `#pomodoro`) and has `<`
  sources that vacated a link today, the new task takes **the merge offer's slot**: the
  earliest entry, at the first removed bullet. This reuses the offer's existing placement
  and pick path, so Pomodoro-name agreement already holds.
- A typed `#pomodoro` wins.
- With no vacated slot, ordinary type placement applies.
- A task this capture creates is never stamped fresh (the existing Successor Offer rule).

The user typed `:`, so this is explicit linking and does not conflict with
`decisions:unblocked-tasks-are-offered`. It is still a new placement rule and needs its own
decision record.

**A6. Added: ID-less sources are pickable.** The `< +query` and `< @route+…` pickers keep
ID-less mergeable rows with `requires_block_id` and suggested IDs. Clients run the
existing **Add block ID** flow (`bob capture-task-id … --route`, which returns
`parent_replacement: "@route+id"`) and splice the result. Without this, `<` cannot pick
the inbox scraps it exists to consolidate (G7). Recommend the same change for `>` sources
in the same phase.

**A7. Added: a source's own prerequisites are surfaced, not inherited.** The merge
contract leaves S's open prerequisites behind (`prerequisites_left[]`). That is right: an
automatic carry-over would make a newborn task Blocked. With `<`, though, the user is
authoring T in this very line, so the warning can be actionable:

```text
⚠ “Login test timeout…” waited on “Upgrade CI runners”; the new task doesn't · add &ci:runners
```

The warning should carry Bob-authored insert data (`{at, text: "&ci:runners"}`, placed
before `<`) so the Mac can offer **Add** as an explicit draft edit. That mirrors how the
Similar-tasks actions work.

**A8. Added: item modifiers may not name a source.** A modifier on a `<` item that names
one of its sources is refused with `merge_in_source_also_marked`:

- `&foo:f` (T depends on a task it absorbs);
- `*foo:f` (the absorbed task depends on T);
- `~foo:f` / `~~foo:f` (a redundant relation).

The copy is "“Fix the flaky login test” merges into the new task; it can't also be its
prerequisite".

**A9. Added (later phase): a `<` "merge in" action in the Similar tasks band.** When a
new-task draft looks like an open task, the band already offers sigil-keyed draft edits
(`~ + & * / ⌫`). Add `<` ("merge in"). Bob authors the splice: append ` < @route+id`, or
append ` @route+id` to an existing `<` run. For ID-less rows it uses the same
`requires_block_id` flow. "Possible duplicate" then offers both directions: `+` (file my
draft under the old task) and `<` (keep my new task and absorb the old one). This amends
`decisions:similar-tasks-are-a-settled-heads-up`, whose key list is explicit, so it needs a
new decision record.

**A10. Rejected: inferring the route from the sources.** It is tempting to put T in the
sources' note when they share one and no `@route` is typed. But that adds a hidden second
"where" that `decisions:capture-sigils-say-where-what-how` exists to prevent, and CLI users
see no preview. Instead, T routes like any new task (`@route`, then `@@`, then
`mac_inbox`), and the Mac card shows the destination note on T's row. Merging inbox scraps
lands T in the inbox anyway. Revisit only if Bryan finds himself adding `@area` to most
`<` captures.

**A11. Added: two small safety nets.**

- **Shell guard.** If stdin is a regular file whose basename starts with `@` and the draft
  arguments are non-empty, refuse with `shell_ate_merge_arrow`: "your shell read `<` as a
  redirect: quote the draft (`bob capture 'X < @a+x'`)". This mirrors
  `shell_ate_transfer_arrow`.
- **One `<` per item.** A second `<` is refused with `merge_in_extra_text`.

**Not adjusted.** Multiple sources, a single source (a "re-scope" merge), sources in the
same note as T, and sources nested inside other tasks (their tombstones stay in place) are
all allowed, exactly as with `>`.

---

## 4. Design

### 4.1 Grammar

The scan runs **before** target-run fan-out, like `scan_transfer_line`, on parent lines and
on task-list bullet lines only. It never runs on authored child lines.

| Shape (standalone `<` = whitespace on both sides) | Result |
| --- | --- |
| `<` followed by one or more complete `@route+id` to end of line | **Valid** merge-in |
| `<` then `+` or `+query` as the final token | **Incomplete**, need `task_parent` with the merge-in role (vault picker) |
| `<` then `@`, `@ro`, `@route`, or `@route+` as the final token | **Incomplete**, need `route` or `block_id` (note-scoped picker) |
| `<` as the final token of a line with text before it | **Incomplete**, need `merge_source`, hint "type + to pick tasks to merge in". `bob capture` refuses: "pick tasks to merge in after <, or write \\< to keep it" |
| `<` then a source-like but malformed token (`@a+x#d`, `@a:x`, `^a:x`) | **Invalid**, with the reused `transfer_source_*` codes |
| `<` then complete sources, then anything else | **Invalid** `merge_in_extra_text`, span over the extra tokens |
| `text<@a+x`, `text <@a+x`, `text< @a+x` (glued to a complete source) | **Invalid** `merge_in_arrow_spacing`: "put spaces around <: New task < @a+x" |
| `<` then a non-source token (`a < b`, `latency < 200ms`) | **Unclaimed**: prose, unchanged |
| `\<` at the arrow position | Literal `<` with the backslash dropped (as with `\>`) |
| `<` inside `` `code` ``, `[[links]]`, or `<https://…>` | Unclaimed (shared protected-markup ranges) |
| Line-initial `< @a+x …` (nothing before the arrow) | **Invalid** `merge_in_needs_new_task`: "name the new task before <" |

Implementation shape:

- Add `capture_language/merge_in.rs`. Factor the source-token helpers out of
  `transfer.rs` (`parse_source_token`, `parse_complete_source_text`, the duplicate check,
  and protected-markup checks) so both arrows share them.
- Split the parent line at the claimed arrow. The **left slice** is fed to the ordinary
  item resolver unchanged, so `ParsedCaptureText` gains
  `merge_in: Option<MergeInClause { arrow, sources }>`. The A3 gate then runs on the
  resolved `kind`. The editor resolver (`editor_parse.rs`) calls the same scanner, so
  highlighting can never disagree with execution.

### 4.2 Semantics

`T < S₁ … Sₙ` executes as one capture item in this order:

1. **Plan T** exactly as the left slice alone would. Mint a block ID if none was typed,
   using the same minting as `~~` (probe: `Consolidate login test flakiness` →
   `^consolidate-login`), and stage T's creation, children, and modifiers.
2. **Run `plan_task_merge`** against the staged snapshot with:
   - `sources = [S₁ … Sₙ]` in typed order;
   - `target = MergeContainer::Task(T)` at T's plain-child anchor;
   - `gesture = Explicit`;
   - `label` = the first configured merge label, falling back to `merged into`.

   Stage the result through the same `stage_merge_plan` that transfers and label merges
   use.
3. **Apply A5** if T is `:id`-linked: pick the merge offer instead of using type placement.
4. **Report** with the merge record (A4/G3) and the task blocks.

The resulting fate of each part:

- **T's children:** T's authored children are written with T, so the merged groups land
  after them in typed order (MG20). The note reads as "my fresh notes first, then the
  absorbed history".
- **T's fields:** T's status, type, priority, and schedule come only from the left slice
  (the merge contract: T owns them). Nothing is inherited.
- **Dependents:** each source's open dependents re-point to T. A cycle through T's own
  `&` refuses the whole draft (`merge_dependency_cycle`).
- **Today's links:**
  - Sources' live links under today's open Pomodoros are pruned.
  - T is offered once at the first vacated slot when T is open and not Blocked. With
    `s:N` or `&`, T is born Blocked, so no offer is made; the prune still lands and the
    card says so.
  - With `:id`, A5 applies.
- **Same note:** T and a source in the same note give one staged write
  (`transfer_merge_same_note_stages_one_file` already covers this).
- **Bulk drafts:** later items see the staged merge. A second item naming an
  already-absorbed source is refused before any write.
- **Equivalence (the core property):** `T @n^t < @a+x @b+y` produces vault bytes identical
  to the two-item draft `T @n^t` ⏎⏎ `@a+x @b+y > @n+t` (A5 aside).

### 4.3 Refusals and copy

Bob authors every string, and clients render them verbatim.

| Code | When | Copy |
| --- | --- | --- |
| `merge_in_needs_new_task` | the line creates no task, or names an existing one | "< merges into the task this line creates; ^t already exists — write `@bar+b > @foo+t`" / "this line creates no task" / "name the new task before <" |
| `merge_in_closing_task` | `:id=x…` | "the new task closes as it is born, so it can't take in other tasks; close it in a later item" |
| `merge_in_project_note` | `@r^id@` / `@r:id@` items | "a new project keeps tasks as tasks: list them as `- ^id` bullets to move them in" |
| `merge_in_extra_text` | anything after the sources, or a second `<` | "everything about the new task goes before <; only @note+id tasks follow it" |
| `merge_in_arrow_spacing` | glued arrow next to a complete source | "put spaces around <: New task < @a+x" |
| `merge_in_source_also_marked` | `&`/`*`/`~`/`~~` naming a source | "“S” merges into the new task; it can't also be its {prerequisite \| dependent \| relation}" |
| `shell_ate_merge_arrow` | stdin is an `@…` file | "your shell read “<” as a redirect: quote the draft (bob capture 'X < @a+x')" |
| *reused* | `transfer_source_suffix`, `transfer_source_marker`, `duplicate_capture_target`, `merge_source_closed` (A4 copy), `merge_source_recurring`, `merge_source_project`, `merge_source_open_subtasks`, `merge_dependency_cycle` | unchanged |

### 4.4 Editor contracts (`capture-parse`, `capture-complete`, `capture-rewrite`)

**`capture-parse`** keeps the item's own `mode` (`task` / `pomodoro_task`) and adds these
fields, all additive and omitted when absent:

```json
"merge_in": {
  "arrow":   {"start": 32, "end": 33},
  "sources": [
    {"start": 34, "end": 40, "marker": "@foo+f", "route": "foo", "block_id": "f"},
    {"start": 41, "end": 47, "marker": "@bar+b", "route": "bar", "block_id": "b"}
  ]
}
```

- New span kinds are `merge_in_arrow` and `merge_in_source`. Do not reuse `transfer_*`:
  the Mac keys transfer-only picker logic on `transfer_source`.
- The new need is `merge_source`.
- Bump the grammar revision (14 if nothing else lands first).

**`capture-complete`:**

- `< +query` and terminal `<` use the vault-wide `task_parent` context with a new
  `MergeInSource` role in `transfer_assist.rs`. Rows are narrowed to *mergeable* tasks
  (`mergeable_source_ids`): open, not `^prj`, not recurring, no open subtasks. They exclude
  T's own typed sources and keep ID-less rows per A6.
- Each row carries `consequence: "⤵ merge in · N notes"`.
- A row that the A8 rule would refuse is listed with a `disabled_reason`.
- The response returns `continuation: " +"`, so typing `,` after an accepted row opens the
  picker for the next source. The multi-pick flow therefore already exists:
  `New task < +fla⏎,+time⏎`.
- `< @route+` uses the note-scoped task context with the same narrowing.

**`capture-rewrite`:** in a `<` source slot, typing `+` right after `@route:id` or
`@route^id` toggles to `@route+id`, exactly as on a `>` line.

### 4.5 The Bob Mac Capture preview

There are two design principles:

- **The card reads like what you typed.** For `S > T` the card is sources, then
  `↓ into`, then T (today's card). For `T < S` it is T, then `↑ merging in`, then the
  sources. The new task is the item's subject, so it is on top. The connector arrow
  matches the arrow you typed.
- **Reuse, don't fork, the `>` preview.** Epic `bob-cli-h4` just shipped the merge card
  and landing cards, and its reviewer chose **`tombstones = cards`**. So `<` keeps that
  decision: below the card come T's landing card, then one compact tombstone card per
  source. Each tombstone card shows its headline, its LINKS line, and a single
  `⤵ N lines moved to the target` fold. That fold is only fully compact once G6 is
  fixed.

**State 1: arrow typed, nothing picked.** `Some great new task! @foo^great <` (incomplete
`merge_source`).

```text
┌ editor ───────────────────────────────────────────────────────────┐
│ Some great new task! @foo^great <▏                                │   “<” in merge purple
└───────────────────────────────────────────────────────────────────┘
  ⤵ type + to pick tasks to merge in                                     (calm hint, no error red)
  ○ Some great new task!                     → foo.md                    (the ordinary new-task row stays)
```

**State 2: picker open.** `… < +fla`

```text
  ⤵ Merge into “Some great new task!”                       ⌘↩ pick · , pick another
  ● Fix the flaky login test        Next · BUILD        foo.md   ⤵ merge in · 2 notes
  ○ Flaky auth e2e on Safari        Todo                inbox    Add block ID
  ◌ Flaky screenshot diff           repeats — merge it by hand first           (disabled)
```

**State 3: complete.** `Some great new task! @foo^great < @foo+f @bar+b`. Today's purple
merge card is reused with a target-first layout:

```text
┃ ⤵  Merge 2 tasks into a new task
┃ ◌  Some great new task!    Todo  ┆new┆                          foo.md
┃ │  ↑ merging in
┃ ●  Fix the flaky login test          Next → Cancelled          foo.md:1
┃      2 notes
┃ ○  Login test timeout is too short   Todo → Cancelled          bar.md:1
┃      1 note
┃    ⛓ “Waits on f” now waits on “Some great new task!”
┃    ◌ “Fix the flaky login test” leaves BUILD
┃    ⚠ “Login test timeout…” waited on “Upgrade CI runners”; the new task doesn't   [Add &ci:runners]
┃    ☀ TODAY 3/10
┃    [Pull in]  Link “Some great new task!” in place of “Fix the flaky login test”
```

Notes on State 3:

- **Already supported:** the dashed `new` capsule, status transitions, locators,
  consequence rows, the TODAY badge, and the Pull-In slot all exist in
  `CaptureTransferCardView`.
- **New in the view:**
  - a `layout: .targetFirst` flag (the connector moves above the sources and reads
    `↑ merging in`);
  - the header string;
  - the optional **Add** button on a prerequisite warning (A7).
- **Below the card**, T's own task block (from `task_blocks`, `created: true`,
  `merge_target`) shows the exact bytes Bob will write. It wears h4's pink `New` capsule.
  A created block is *all* `added` rows, so the existing quiet-run folds never trigger.
  To stay concise, each merged group folds to one row
  (`⤵ Fix the flaky login test · 2 notes ▸`) through an additive per-line `origin` key
  (`"foo.md#^f"`) on task-block lines. That mirrors the tombstone fold on the other side.
  Authored lines and the managed LINKED FROM / BLOCKS lines stay visible.
- **Tombstone cards** follow h4's `tombstones = cards` decision unchanged.
- **Pomodoro blocks** appear only when a link was pruned (today's behaviour).

**When the card renders:** the Mac's `CaptureTransferPresentation.init` accepts
`kind ∈ {task, pomodoro_task}` when `merges` is non-empty and `merges[0].target.created`
is true (the G3 fix). Two consequences follow from that one condition:

- The same card also renders for `Umbrella ~~old:a|"merged into"`, which closes G1.
- An older Mac paired with a newer `bob` degrades gracefully. It shows the ordinary task
  preview plus the task blocks, because every field is additive.

**Refusal state:** for example `@foo+t < @bar+b`:

```text
  ⤵ < merges into the task this line creates; ^t already exists        [Use > instead]
     write @bar+b > @foo+t
```

The button applies Bob's `rewrite` (A3). It is an explicit draft edit; Return never
changes.

**Other copy:**

| Surface | Text |
| --- | --- |
| Status line | `Would create “Some great new task!” and merge 2 tasks into it` |
| Notification after commit | `Created “Some great new task!” · merged 2 tasks` |
| Notification body | one line per source: `Fix the flaky login test · Next → Cancelled · 2 notes` |
| VoiceOver | "New task Some great new task!, foo.md, new. Merging in: Fix the flaky login test, Next to Cancelled, foo.md line 1, 2 notes; …" |
| Submit hint | `Capture & merge 2 tasks` (already in ML7's copy table) |

### 4.6 CLI output

The human output reuses the merge renderer, plus the G4/G5 fixes:

```text
✓ captured  foo.md
  - [ ] #task Some great new task! [created::2026-11-05] ^great
⤵ merged 2 tasks into “Some great new task!” (new) · foo.md
  ⊘ Fix the flaky login test         foo.md:1 · Next → Cancelled · 2 notes moved
  ⛓ “Waits on f” now waits on “Some great new task!”
  ◌ BUILD link removed · offer 1: link “Some great new task!” under BUILD (-p 1)
  ⊘ Login test timeout is too short  bar.md:1 · Todo → Cancelled · 1 note moved
git  committed 1a2b3c4 · synced
```

JSON (`bob capture -f json`):

- The item keeps its kind, adds `merges[]` (MergeRecord with `target.created: true`),
  `merge_offers`, and `repaired_files[]`, and joins top-level `pull_in`.
- `task_blocks` carries T (`created: true`, `merge_target`) and each tombstone
  (`merge_source`).
- Everything is additive; `schema_version` stays 1.

### 4.7 Docs, decisions, memory

- **`docs/capture.md`:** a new subsection, "Merging tasks into a new task with `<`",
  directly after the `>` section, plus marker-table rows.
- **`docs/task-merge.md`:** list `<` among the gestures that compose `plan_task_merge`,
  and add vectors MI1–MI16 (§5).
- **`docs/reference/compatibility.md`:** the grammar revision entry.
- **`docs/task-relations.md` ML6:** add the equivalence `T ~~a:x|"merged into"` ≡
  `T < @a+x` (when configured).
- **After acceptance:** write a new decision record ("Capture `<` merges existing tasks
  into the new task"; covers A3, A4, A5, A10) and, in phase 5, a superseding note for the
  Similar-tasks key list (A9). Also extend the `glossary:task-merge` strand. All memory
  edits go through `/sase_memory_write`.

### 4.8 Shipping safely across the grammar break

1. bob ships `<` with the grammar bump and a `feat(capture)!:` commit.
2. The Mac ships the decode and card changes **and raises `CaptureGrammarGate`'s minimum to
   the new revision**. A Mac paired with a stale `bob` then shows the existing "update
   bob" copy instead of letting `<` drafts become sub-bullets under the sources.
3. The CLI has no gate. The daily release train keeps the window short, and the changelog
   line should say plainly that `X < @a+x` used to file a note.

---

## 5. Reliability: guarantees and conformance vectors

These are inherited unchanged from the merge engine and capture:

- validate-then-write over one plan;
- guarded commit, so a note changed since planning aborts;
- destination-first write order;
- all-or-nothing rollback;
- dry run equals the real run except for `dry_run`;
- `bob task reconcile` is a no-op afterwards;
- every block link that resolved before still resolves.

`<` adds these properties:

- **Desugaring equivalence (property test).** A `<` item and its two-item expansion
  produce identical vault bytes. This one test pins most of the semantics.
- **Re-submit is a refusal, not a duplicate.** The sources are closed, so the whole draft
  is refused before any write, and the copy names where they went (A4).
- **Config independence.** `merge_labels: []` still merges and writes `merged into`.

| ID | Covers |
| --- | --- |
| MI1 | `T @n^t < @a+x`: T created; x's title bullet and notes land under T; x is `[-]` with `merged into [[n#^t]]`; T has LINKED FROM |
| MI2 | several sources keep typed order after T's authored children and drawers |
| MI3 | the same-note source stages one file write |
| MI4 | dependents re-point to T; a cycle through T's own `&` refuses the batch |
| MI5 | closed / recurring / `^prj` / open-subtask sources refuse; the vault is byte-identical |
| MI6 | A3 contexts: every ❌ row refuses with its code; `@n+t < @a+x` carries a `rewrite` to `@a+x > @n+t` |
| MI7 | lexical: prose `<`, glued `<`, `\<`, terminal `<`, `< +q`, `< @r`, suffix/marker errors, extra text, a second `<`, duplicates, protected markup |
| MI8 | offers: plain T is offered at the first vacated slot; `s:N`/`&` T gets no offer while the prune lands; the offer title names the single link-losing source (G5) |
| MI9 | A5: `:id` T takes the vacated slot; `:id#pomo` wins; no vacated slot uses type placement; never stamped fresh |
| MI10 | desugaring equivalence with the two-item draft (A5 cases excluded) |
| MI11 | re-submit refuses with the "already merged into …" copy and zero writes |
| MI12 | `merge_labels: []` still merges and writes `merged into` |
| MI13 | task-list bullets: `@n` header + `- T < @a+x` works per bullet |
| MI14 | A8: an `&`/`*`/`~` modifier naming a source is refused |
| MI15 | an ID-less T mints an ID; the preview and record show it |
| MI16 | bulk: a later item naming a source an earlier item absorbed is refused before any write |

---

## 6. Implementation plan

Each phase ships independently and keeps `schema_version` at 1.

1. **Contract.** Update the docs listed in §4.7 and add the vector index (§5).
2. **bob grammar.** `capture_language/merge_in.rs`; source helpers shared with
   `transfer.rs`; `ParsedCaptureText.merge_in`; the A3 gate on the resolved kind;
   `editor_parse` spans, needs, and the `merge_in` object; `capture-complete`'s
   `MergeInSource` role (mergeable narrowing, ID-less rows, consequence, continuation); the
   `capture-rewrite` toggle. Bump the grammar and use a `!` commit.
3. **bob execution.** `capture/merge_in.rs`: stage T, then call the shared merge staging
   (lift the common part of `transfer.rs` and `relations_merge.rs`); A5 offer-pick; A8
   checks; A11 shell guard; `target.created` for capture-born targets (G3); the human
   renderer path (also fixes G2 for `~~`); copy fixes G4 and G5; the merge-source diff
   pairing fix (G6); A4 refusal copy; tests MI1–MI16 plus the equivalence property.
4. **Mac.** Decode `merge_in` and the new span kinds (merge purple / route family); the
   `merge_source` hint; the `< +` / `< @r+` pickers with the Add-block-ID splice; the
   transfer card's `targetFirst` layout and header; the `origin` group folds in T's
   created landing card (tombstone cards stay as h4 shipped them); the `rewrite` and **Add** buttons;
   status, notification, and VoiceOver copy; the `CaptureGrammarGate` minimum bump. Watch
   the macOS CI run to green.
5. **Similar tasks `<` action (A9).** In `capture-related`: a `merge_in` action, splice
   anchor, `linked.link = "merge_in"`, and ID-less handling. In the Mac: the strip key
   `<`. Write a new decision record first.
6. **Optional, same window:** let `>` source pickers keep ID-less rows too (G7/A6).

---

## 7. Open questions for Bryan

1. **A5 (link in place).** Do you want `@foo:great … < @foo+f` to take `^f`'s Pomodoro slot?
   I recommend yes. The alternative is today's naive composition: type placement plus an
   emptied slot.
2. **Should `=x` be allowed later?** "I just did X, which also covered a and b" is real.
   But when work was *done*, the honest outcome is usually completing the sources
   (`implemented by`), not cancelling them. I recommend keeping the refusal until there is
   demand.
3. **Project notes.** Should `@proj^p@ < @inbox+a` ever fold tasks into a new `^prj`? I
   recommend not: move-in bullets keep the tasks as tasks.
4. **Is the preview concise enough at three or more sources?** This report keeps h4's
   `tombstones = cards` decision. If a three-source `<` preview feels long in practice
   (card, target card, three tombstone cards), the reopen is h4's rejected
   `tombstones = rows_only` branch: a muted `→ tombstone keeps LINKS` caption on each
   source row instead of cards. That would apply to both arrows, so it needs a new
   decision rather than a `<`-only exception.

---

## 8. Recommended solution

Ship `<` as the **capture spelling of "merge these existing tasks into the task I'm
creating"**, defined as an exact desugaring onto the existing `>` explicit-merge path:

- **Grammar.** A standalone `<` followed by one or more `@route+id` sources ends the line
  (A1, A2). It is claimed before target-run fan-out, prose comparisons are untouched, and
  `\<` escapes it. It is valid only on lines that create exactly one ordinary task that is
  still open at commit (A3). Every other context is refused with teaching copy, and an
  existing-task line gets a one-key **Use `>`** rewrite.
- **Semantics.**
  - Create T exactly as the left side says, then run `plan_task_merge(Explicit)` into T
    in typed order (A4).
  - The result is byte-identical to the two-item draft that already works today.
  - T owns its fields.
  - Sources retire as `merged into` tombstones, and their dependents re-point to T.
  - Today's lost links offer T in their place. If the line also links T with `:id`, T
    simply takes that place (A5).
  - Sources may be ID-less inbox tasks via Add block ID (A6).
  - Modifiers naming a source are refused (A8).
- **Preview.** One purple merge card that **reads like what you typed**: the new task on
  top with its dashed `new` capsule and destination note, then `↑ merging in`, then each
  source with its `Next → Cancelled · N notes` transition and locator, then Bob's
  consequence rows. Those rows cover re-pointed dependents, the link that leaves a
  Pomodoro, a prerequisite warning with an **Add** fix-it (A7), the TODAY badge, and a
  single Pull-In offer. T's exact final block sits underneath with merged groups folded,
  and h4's compact tombstone cards follow. The same card renders for
  `~~ | merged into`.
- **Reliability.** Every merge-engine guarantee is inherited. Add a desugaring-equivalence
  property test, config independence, refuse-not-duplicate on re-submit, the shell
  redirect guard (A11), and a bob-first ship order with a Mac minimum-grammar bump across
  the grammar break.
- **Fix along the way:** G1–G7. These make the existing `>` and `~~` merge previews more
  honest too.
- **Later:** a `<` "merge in" action in the Similar tasks band (A9). It turns "you already
  have this task" from a heads-up into a one-key consolidation.

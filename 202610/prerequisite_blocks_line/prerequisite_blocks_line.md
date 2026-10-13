# A machine-owned `🧱 BLOCKS` line: showing on a prerequisite what waits on it

> **Research query:** What is the best way to automatically add a sub-bullet to tasks that other
> tasks depend on, showing that they block one or more other tasks (the counterpart of the existing
> "Depends On" sub-bullet on dependent tasks), written when dependencies are added (for example via
> the `<ctrl+shift+p>` keymap) and kept present and consistent by `bob task reconcile`, so that the
> feature is intuitive, reliable, and beautiful? Is this plan a good idea, would a different approach be
> better, and which requirement adjustments are justified?

![Infographic: a generated, read-only BLOCKS line on a prerequisite mirrors its dependents' DEPENDS ON
links and marks the last blocker with a key; a measured vault snapshot of 15 blocking tasks, 21
dependency edges, and 6 block ids to mint; the rules that keep it reliable; and a five-step rollout from
contract to immediate updates](prerequisite_blocks_line_infographic.png)

## Bottom line

**Build it as a derived mirror: written from the dependency graph and never read back into it.**
`⛓️ DEPENDS ON` on the dependent remains the only place a dependency is authored. The new line on the
prerequisite is a *projection* of those edges, kept current the way `bob projects sync` keeps the
`🧩 **Sub-projects:**` line current. Designed this way, the feature is small and self-healing, and it can be
removed losslessly. If the line were instead a second editable copy of the graph, it would bring back the
drift that the Depends-On redesign just removed.

```markdown
- [?] #task Did enrolling for unemployment work! [id:: cash__unemployment] [scheduled:: 2026-10-14] ^unemployment
	- 🧱 **BLOCKS:** [[#^audit-subscriptions]] • [[#^call-north-face]] • [[#^get-access-money]] • [[#^save-verizon-router-pwd]]
	- Kelly just needs 2 pay stubs and/or my W2!
```

In Live Preview and Reading view, the line renders as chips that mirror the Depends-On chips. A 🔑 marks
each dependent for which this task is the *last* thing in the way:

```text
[?] Did enrolling for unemployment work!
    🧱 blocks  ( ? Audit monthly subscriptions 🔑 )  ( ? Dispute North Face jacket… 🔑 )  ( ? Get access to all of… 🔑 )  ( ? Save Verizon Router… 🔑 )   frees 4
```

*(`^audit-subscriptions` and `^get-access-money` are illustrative minted ids; those two dependents have no
block id today.)*

[Three of the five researchers](#where-the-researchers-disagreed) (cdx, cld, grk) recommended a stored projection. Two (mus, gem) recommended
render-only chips, with a stored line only as an opt-in fallback. I side with the stored projection. Bryan
asked for Markdown that reconcile maintains, the line has to be readable in vim, git, and by agents, and
the measured cost is tiny: [**15 lines and 6 minted block ids**](#the-live-vault) across the whole vault today. Every hazard
the render-only camp raised is real, and each one is neutralised by [a specific rule below](#why-not-render-only-chips). Their
contribution survives as the rendering layer: [chips](#chips) draw from a live reverse index, so the stored line can
lag without ever *looking* wrong in Obsidian.

---

## Critique of the plan

*Is this a good idea?*

### Why yes

1. **It answers a question nothing in the note answers.** Depends-On tells a blocked task *why it waits*.
   Nothing tells a Ready or Next task *why it matters*. Looking at "Did enrolling for unemployment work!"
   today, you cannot see that four cash tasks wait on it. That is exactly what you need when choosing
   between two Ready tasks, or when deciding whether to cancel, decay, or Alt+N-release a task.
2. **Successor linking covers only the moment of closing.** §12 of `docs/task-dependencies.md` reacts when a prerequisite closes. It is
   silent for the whole life of the edge before that.
3. **Plain-text parity.** Bryan edits in vim, the vault is git-synced, and SASE agents read notes as text.
   The forward edge is visible there and the reverse edge is not. `rg BLOCKS` and `gf` on a link should
   work.
4. **Every mature tracker shows both ends.** Linear (Blocks / Blocked by), GitHub issues (Mark as blocking /
   blocked by), Jira (blocks / is blocked by), and Tasks' `is blocking` filter all do. They store **one**
   edge and render it twice. A plugin-free plain-text vault cannot "just render", which is why a stored
   mirror is justified here. That mirror must still *behave* like a rendering.
5. **Trying it is nearly free.** A pure projection can be deleted with no information lost.

### What the plan as stated gets wrong or leaves open

- **"A new sub-bullet"** invites one bullet per dependent, which the decision record already rejected. The
  reverse direction concentrates fan-in, so it is worse there.
- **"Automatically when dependencies are added"** is only half the job. Adds without removes leave phantom
  entries. Every writer of the forward line has to keep the mirror current for the targets it removes as
  well as the ones it adds.
- **The plan does not say which copy wins.** If both lines are authored, Bob gets two sources of truth. Jira
  teams fight inverted links; Obsidian Tasks renamed its stored `blockedBy` field to `dependsOn` in 6.1.0
  to fix exactly this direction ambiguity (grk).
- **The plan does not say when the reverse relationship ends.** If a closed task keeps "BLOCKS", or a
  closed dependent stays listed, the line becomes false or grows without bound (mus, gem).
- **Dependents need an address.** A dependent does not need a `^block-id` today, and 6 of 20 live ones lack
  one (grk's claim that they always have one is wrong).
- **The new line also has to be ignored correctly.** Task Link, Pomodoro, R8-legacy-child, and managed-log
  recognisers in four codebases must not claim it ([cld's compatibility audit](#compatibility-guards)). This is where the bugs would
  actually come from, more than from the reconciler.

### Why not render-only chips

*This was the mus/gem recommendation.*

That approach is the strongest alternative, and its strengths are adopted: chips render from a live index,
dependents that have closed vanish from the view immediately, and nothing on a closed task is ever
rewritten. On its own, it fails the request. Vim, git, agents, and a vault without the plugin see nothing,
and `bob task reconcile` has nothing to ensure. The accepted decision record rejected the same shape for the
forward direction ("nothing readable … in the note"). The specific hazards mus and gem raised are handled
as follows:

| Hazard raised | Resolution |
| --- | --- |
| Dual source of truth (mus, gem) | The line is a projection. Nothing reads it, and hand edits never change the graph ([Authority](#authority-and-the-reconcile-pass)). |
| Write amplification and git churn (gem) | 15 lines, 21 edges, and fan-in of at most 4 today. Closing in the normal order (prerequisite first) writes nothing, because the owner's line freezes ([Membership](#membership)). |
| Broken cross-note undo (gem) | 76% of live edges are same-note and share the dependent's one-undo transaction. Cross-note writes reuse the existing follow-up-write pattern, and undo re-arms the mirror ([Immediate writers](#immediate-writers)). |
| Immutability of historical notes (gem) | The contract protects only the *previous daily note snapshot* and `done/`. Gem's "all historical daily notes are read-only" overgeneralises it. Under the freeze rule, closed and archived tasks are never written anyway. |
| Unbounded fan-in or "thousands of lines" (mus) | Refuted by measurement. The line lists open dependents only, so it shrinks as work completes. |

### Would I take a different approach

Same deliverable, different emphasis:

- **The projection is one pure function, `blocks_lines(edges) → lines`.** Conformance vectors specify it,
  and it is implemented once in Rust and once in JS. Reconcile applies it to the whole vault. Each gesture
  applies it to the old ∪ new targets it touched. No writer has private rules.
- **Show leverage, not just a backlink list.** The genuinely new information is "finishing this frees X",
  which is the [🔑 badge](#chips). Build the reverse index as shared infrastructure so the review walk, decay cards,
  and the close preview can reuse it later (cld, mus).
- **Ship the guards before any writer**, the same order the Depends-On rollout used.

---

## Requirement adjustments

*Each adjustment to the request is called out below.*

| # | You asked | Adjusted to | Why |
| --- | --- | --- | --- |
| RA1 | "a new sub-bullet" | **One** managed child line per prerequisite listing all its dependents, never one bullet per dependent. | The decision record already rejected per-item bullets, and fan-in concentrates. |
| RA2 | (implicit) both lines are peers | **Depends-On stays the only source of truth. BLOCKS is a read-only projection.** Hand edits never add or remove edges, and reconcile restores the canonical line. | One authority. An accidental `dd` on the prerequisite must never delete dependencies in other notes. |
| RA3 | "tasks that other tasks depend on" | **Open** tasks with at least one **open** direct dependent. A closed or cancelled dependent drops off. A closed owner's line **freezes** as history. | Matches Tasks' `is blocking` and Linear's live "Blocks", and keeps `docs/task-dependencies.md` §4.1 intact. |
| RA4 | "when dependencies are added" | **Every forward-edge change (add *and* remove) by every writer** keeps the mirror current. Closes are handled by reconcile. | Adds without removes leave phantoms. Close paths stay free of new cross-note writes. |
| RA5 | (implicit) one undo | One Ctrl+Z covers **same-note** pairs. A cross-note mirror write is a best-effort follow-up that never rolls back the dependency, and reconcile repairs it. | Obsidian has no multi-note transaction. This matches the existing `docs/task-dependencies.md` §6.6 pattern. |
| RA6 | (new) | **Dependents without a `^block-id` get one minted** (SB policy, silent, no `[id::]`, no freshness stamp). | A link needs an anchor. 6 dependents need one today. |
| RA7 | (implicit) project blocking | **Explicit direct edges only.** Inherited `#prj_is_blocked` residents and transitive chains are not listed. A `^prj` dependent appears once, as `[[note#^prj]]`. | Copying project dependencies onto residents was already rejected, and the same reasoning applies to reverse copies. |
| RA8 | (implicit) reconcile is a second writer | Reconcile is **the authority**: it inserts, rewrites, deduplicates, deletes, and mints. Gestures are early courtesy writes. | Closes, vim edits, agent edits, and moves are only ever repaired by reconcile. |
| RA9 | (new) | **No new Tasks field and no new CLI.** | `is blocking` already exists. A `[blockedBy::]` field would be a third copy of the edge. |
| RA10 | (new) | A **kill switch**, `blocks_lines: false`, makes reconcile *remove* every BLOCKS line on open tasks. | A reversible trial. A stopped mirror that stays present would rot. |
| RA11 | (new) | **Guards in every engine ship before any writer.** | The compatibility audit found real misreads ([Compatibility guards](#compatibility-guards)). |
| RA12 | (new) | Editing from the prerequisite side (chip `×`, `＋`, a Blocks… stage) is **phase 2**, not v1. | v1 makes the graph visible both ways. A second picker is a second product (grk). |

---

## Verified facts that shape the design

Bare `§` references in this report point to sections of `docs/task-dependencies.md`, the dependency
contract.

| Fact | Source | Consequence |
| --- | --- | --- |
| One managed `⛓️ **DEPENDS ON:**` first-child line is authoritative; `[dependsOn::]`/`[id::]` are projections (R1–R10). | `docs/task-dependencies.md` §§2–4; `decisions:task-deps-are-depends-on-links` | Reverse lines must be generated *from* accepted forward edges. They never feed them. |
| The decision record rejected "one bullet per dependency" (bloat) and "fields only with a virtual line" (nothing readable in the note). | `decisions:task-deps-are-depends-on-links` | Both rejections apply to the reverse direction: use one line, and make it a real line. |
| Reconcile touches only *open* dependents; "closed tasks are never touched"; the previous daily note snapshot is never written; the hooks never move lines. | §4.1, §4.3 | A rule that leaves closed tasks alone ([Membership](#membership)) keeps these invariants with no carve-out. |
| A machine-owned derived child already exists: Sub-projects is fully rewritten, deduplicated, and anchored after the Depends-On subtree. It also keeps closed children as a struck ledger. | `docs/projects.md` (Sub-projects rules); `projects/sync.rs:911` `subprojects_anchor_child` | This is the precedent to copy for ownership. Do not copy the struck ledger: the Depends-On writer form forbids strikes. |
| Reconcile regroups task blocks between status sections on every run. | `task_status_hooks/compose.rs` (`grouped_task_sections`, `structural_regrouping`) | Document order is unstable, so entry order must not depend on it. |
| Nav's Depends on stage already writes cross-note target notes before the dependent commits, and follow-up Pomodoro cleanup writes are "never rolled back; reconcile repairs". | §6.6 steps 1 and 3; nav `prepareDependencyTargetNote` (4 call sites) | Cross-note writes in a gesture are an existing, accepted pattern, not a new hazard class. |
| The Task Card `b` row is labelled **Blocked by…** and edits the *forward* line. | nav `src/320-task-card-header.js:243` | The reverse line must never be called "Blocked by". |
| `🚧` is nav's WIP *project status* emoji. `🧱` is unused in every plugin. | nav `src/010-requires-and-config.js:166`; grep across `plugins/*/src` | grk's `🚧 BLOCKS` collides with an existing meaning. |
| Bob's native Tasks engine already supports `is blocking`. | `src/native/dataview/tasks/{index.rs:395, parse.rs:1474}` | Read-only "what is blocking?" queries need no new CLI. |
| Only the cycler has a reverse index (`buildDependentsIndex`, used for successor links). Ledger-tools has none. | `task-status-cycler/src/085-successor-plan.js` | The chips need a new shared reverse index, which is a port of the cycler's. |
| `capture_completable_tasks.rs:329` skips only `is_dependency_line`. The Pomodoro scanner counts *any* block link on a bullet under a Pomodoro entry. | Rust source | A BLOCKS line would be misread as a Task Link sighting unless guards ship first. |
| `mint_block_id(description, used)` exists and successor linking uses it. | `capture_block_ids.rs:619` | Dependents without a `^block-id` can get one through the existing policy. |

### The live vault

*Native Tasks query, 2026-10-13.*

| Measure | Value |
| --- | ---: |
| Open tasks that are `is blocking`, i.e. lines to write | **15** |
| Open `is blocked` dependents | 20 |
| Open dependent → open prerequisite edges | 21 (16 same-note, 5 cross-note) |
| Fan-in: dependents per blocker | 12 blockers × 1, then one each with 2, 3, and 4 |
| Largest line | `cash#^unemployment`, 4 dependents |
| Chain nodes (both blocked and blocking) | 2 (`body#^rahway`, `cash#^save-verizon-router-pwd`) |
| Open dependents with **no** `^block-id`, i.e. ids to mint | **6** |
| Open dependents whose status is `[?]` | **20 of 20** |
| `^prj` dependents | 1 (`sase_foo#^prj` waits on `sase#^bar`) |

The last two rows decide the chip design. **Every live dependent is Blocked by construction**, so on a
BLOCKS line each chip's status colour is always the Blocked colour and tells you nothing (see [Chips](#chips)). The scale
rows refute two claims in the render-only reports: the migration is not "potentially thousands of lines"
(mus), and the line does not cause "extreme churn" (gem). The largest closed fan-in, `sase#^post-blog-prj`
with 11 dependents, gets **no** line, because its owner is closed.

---

## Where the researchers disagreed

*Each row gives the positions and how I resolved it.*

| Question | Positions | Resolution | Why |
| --- | --- | --- | --- |
| Store a line at all? | Stored projection: cdx, cld, grk. Render-only first: mus, gem. | **Stored projection plus live chips** | [The critique](#critique-of-the-plan): the request, the vim/agent readers, the decision record's own reasoning, and the measured cost. |
| Glyph | `⛓️` cdx, gem, mus · `🧱` cld · `🚧` grk | **`🧱`** | `🚧` already means a WIP project in nav (verified). Every managed child line has its own glyph (❌ ⛓️ 🧩 🗓️ 🛠️). The feature exists to make bottlenecks *visible while scrolling*, and a second `⛓️` forces you to read the label to see the direction. `🧱` is one code point with no VS16, which avoids the DP11/DP24 class of variant bugs. `⛓️` is an acceptable second choice ([question 1](#questions-for-bryan)). |
| A closed prerequisite's line | Freeze as history: cld. Delete: cdx, grk (B3), gem. | **Freeze** | It keeps §4.1's "closed tasks are never touched" without an exception. Closing in the normal order writes nothing. It matches Depends-On, which also keeps closed history. Deleting would need every close path, or reconcile plus archive stripping (cdx), to edit closed tasks. The chip renders the past tense `✓ freed N`, so the frozen line reads as a record. |
| Entry order | Document order, then path: cdx · sorted link text: cld · stable append: grk, mus | **Sort by canonical link text, case-folded** | A pure function lets nav and Rust emit identical bytes. Reconcile regroups task blocks every run, so document order churns. Same-note `[[#^…]]` entries sort first naturally. Sub-projects already sorts. |
| Position | After Sub-projects: cdx · before Sub-projects: cld, grk, gem | **After the Depends-On subtree, before Sub-projects** | The order reads upstream, then downstream, then structure. It needs a one-line anchor change in `projects sync`. |
| Dependent block ids | Mint: cdx, cld · already present: grk | **Mint with the successor (SB) policy** | 6 of 20 live dependents have none (verified). Never add `[id::]` for this purpose. |
| When a cross-note gesture writes | In the prepare step, before commit: grk · after commit: cdx, cld · reconcile only: gem | **After the dependent commits, best-effort** | A reverse entry written before the edge exists becomes a false claim if the commit fails or is escaped. Reconcile-only lags until the MacBook cron, the only hooks runner, next runs. |
| Chip `×` / `＋` in v1 | `×` write-through: cld, grk · navigation-only: cdx | **Navigation-only in v1.** `×`, `＋`, and a Blocks… stage ship together in phase 2. | v1 keeps a single edit surface while Bryan lives with the line. The cross-note undo story for prerequisite-side edits is designed once, with the inverse stage. |
| Malformed hand edits | Leave alone and warn: cdx, cld · rewrite: grk | **Leave alone, warn, insert no duplicate** | Same rule as R10: machine-owned lines still never destroy typed text. |
| Summary copy | `frees N of M` plus 🔑: cld · `unlocking N`: grk · no counts: cdx | **🔑 plus `frees N` / `frees N of M`** | Status colour is constant here, so "last blocker" is the honest leverage signal. "Unlocking 4" overclaims when a dependent also waits elsewhere. |
| New CLI | `bob task dependents` (mus), `bob task blockers` (gem) | **None** | `bob query --tasks "(not done) AND (is blocking)"` already works. `cli_rules` reserves `bob task <verb>` for whole-vault task-line rewriters, and read-only reports stay top-level. |
| A dependent that closes while its prerequisite is open | Reconcile only: cld · in the close write when cheap: grk | **Reconcile only in v1** | Rare ("prerequisites never prevent closing"). Chips hide the lag. Eager dropping through the cycler's dependents snapshot is a later optimisation. |

---

## The design

### Grammar

```text
<indent>- 🧱 **BLOCKS:** <link> • <link> • …
```

- `🧱` is U+1F9F1, one code point with no VS16. A space follows it, then `**BLOCKS:**`, a space, and links
  joined by ` • ` (U+2022, one space on each side). These are the same link rules as Depends-On §2.1:
  **no aliases, embeds, or strikes**, and the line is deleted when empty with no placeholder.
- Use the **shortest unambiguous link form**, with the same function as the Depends-On writer
  (`canonical_link` in `format.rs`, nav `canonicalDependencyLink`): `[[#^id]]`, then `[[basename#^id]]`,
  then `[[dir/note#^id]]`.
- **Reader tolerance**, so variants can be canonicalised and never duplicated: a missing emoji, `🚧`, or
  `⛓️`; the label `BLOCKING`; `·`, `,`, or whitespace separators; aliased, struck, or embedded links; a
  direct child in an unexpected slot. Lowercase `blocks` is user prose, not a line (as DP27 rules for
  Depends-On).
- Parse with the shared link-scanner-first algorithm from §2.3, keyed on its own label. A Depends-On parser
  must return not-a-line for a BLOCKS line, and the reverse. Only a direct child of a `#task` counts:
  fenced, nested, and blockquoted lines never do.
- **Malformed** (prose after the links, or a half-typed link): leave the line alone, warn
  `malformed_blocks_line`, and insert no second line.

**Label.** `BLOCKS` is the exact grammatical mirror of `DEPENDS ON` ("T depends on A; T blocks C") and the
word Linear, GitHub, Jira, and Tasks all use. Never use "Blocked by", which names the forward direction on
the Task Card's `b` row. Never use "Unblocks", which is false when a dependent also waits elsewhere.

### Membership

```text
open(t)   = status type Todo | In Progress | On Hold         (includes [?]; same as §4.1)
edges     = accepted explicit edges from forward reconciliation: R1-projected resolved task targets,
            R8 legacy-child targets during the legacy window, and cycle members; excluding R4 unresolved,
            R5 non-task, R6 self, unencodable targets, and ^prj internal/descendant targets
blocks(T) = { D : (D → T) ∈ edges ∧ open(D) ∧ D not in the previous daily note }
T owns a line  ⇔  open(T) ∧ blocks(T) ≠ ∅ ∧ T is writable
closed T       → its line is never touched: frozen history
```

- **Use the explicit edge set, not `dependency_edges()`.** That graph skips sources without a block id and
  mixes in implicit resident → `^prj` edges (`references.rs:313`; `reconcile.rs` `record_graph`). Export
  the explicit per-dependent sets from `ReconcileOutcome` before those are added (cdx, cld).
- `#hide`, `ref/`, inbox, and today's daily-note tasks are all in scope on either side. Chips mute `#hide`.
- **Cycles:** A ↔ B each list the other. R7 already warns, so nothing extra is needed.
- **A `^prj` dependent** is listed once, as its `^prj` line. Its residents are never listed.

### Identity and minting

- If a dependent has no `^block-id`, append one using `mint_block_id(description, used)`, reserving the
  ids already used in the note (all blocks plus batch reservations), exactly as successor linking does.
  Mint **once per dependent**, keep existing ids stable, and **never add `[id::]`**, because `[id::]` means
  "is a prerequisite".
- Where minting happens: nav mints inside the dependent's own commit transaction, capture inside its staged
  batch, and reconcile in its BLOCKS pass. Dry-run and Escape mint nothing.
- **BLOCKS writes never stamp `[fresh::]`, never change a status or lane, and never touch the owner's task
  line.** They write only the child line, plus the dependent's `^id` when one is minted.

### Order and position

**Order:** sort by canonical link text, case-folded, with the raw text as the tiebreak. Same-note entries
come first, then cross-note entries grouped by note. A projection has no memory, so this keeps nav and Rust
byte-identical.

**Position:**

```text
- [ ] #task T ^t
  - ❌ **CANCEL LOG**        (if present; stays first, §2.1)
  - ⛓️ **DEPENDS ON:** …     upstream: what T waits on
  - 🧱 **BLOCKS:** …         downstream: what waits on T
  - 🧩 **Sub-projects:** …   structure (^prj only)
  - user children, 🗓️ SCHEDULE LOG, Work Log …
```

- Insert after the Depends-On subtree when there is one. Otherwise use the Depends-On slot: the first
  child, or the second after a first-child Cancel Log. Reuse the task's child indent, otherwise use the
  parent indent plus one tab. Preserve CRLF and final-newline state.
- **Never move an existing line.** Rewrite it in place and delete duplicates after the first. A task that
  later gains a Depends-On line gets it inserted in the first slot, so the order comes out right on its
  own.
- Coordinated change to `bob projects sync`: `subprojects_anchor_child` anchors after the Depends-On *and*
  BLOCKS subtrees, and its single move rule becomes "before Depends-On or BLOCKS".

A chain node then reads as a pair:

```markdown
- [?] #task Make appt w/ Rahway Hospital for CT scan! ^rahway
  - ⛓️ **DEPENDS ON:** [[#^hospital-swarm]]
  - 🧱 **BLOCKS:** [[#^appt-7d-after]]
  - 🗓️ **SCHEDULE LOG**
```

*(`^appt-7d-after` is illustrative: that dependent has no id today.)*

### Authority and the reconcile pass

**Where:** a new step, `reconcile_blocks_lines`, runs after `reconcile_dependencies` and the re-parse of
touched files (`sync.rs` ≈430–443), and before `dependency_edges` and Blocked derivation. Because it is a
separate pass over re-parsed text, it avoids the "two inserts at one index flip order" hazard when a task
gains an R2-adopted Depends-On line and a BLOCKS line in the same run (cld).

1. Build `blocks(T)` from the exported explicit edges. Mint missing dependent ids first, then render the
   links against the post-mint state.
2. For each writable open T, the desired line is either the rendered line or nothing.
3. Compare it with T's existing BLOCKS child, recognised with reader tolerance:
   - missing → **insert**;
   - present but different → **rewrite in place**;
   - present but not desired → **delete**;
   - malformed → **leave it and warn**;
   - duplicates → **keep the first and delete the rest**.
4. Edits are structural, so they go through the existing guarded output: the 2 s quiet interval, preimage
   checks, recovery snapshots, and one per-note edit plan rather than a second write loop.
5. **Never prune on uncertainty** (cdx). A malformed forward owner or a failed note read is not proof that
   an edge is gone. Keep the prior entries attributable to it and warn.
6. Reconcile still inherits its current preconditions (today's daily note exists and has a Pomodoros
   section, among others). An invalid daily note defers repair. Live gestures do not depend on reconcile.

**Key invariant (test it):** deleting every BLOCKS line in the vault changes nothing about blocking,
promotion, scheduling, successor links, or authored edges, and one reconcile rebuilds identical bytes. A
second run makes zero changes.

### Immediate writers

| Writer | Today | With BLOCKS |
| --- | --- | --- |
| Depends on stage (Ctrl+Shift+P → `b`, Ctrl+Shift+P on the line, counted, palette) | Prepares cross-note targets, then commits the dependent in one transaction | **Same-note targets:** T's BLOCKS line and any minted dependent id go into the **same transaction**, so one Ctrl+Z undoes both. **Cross-note targets:** a follow-up write **after** the commit, for old ∪ new targets, through the open editor or a preimage-checked `vault.process`. On failure the notice gains `· BLOCKS not updated` and nothing rolls back. Preparation itself is unchanged and never writes a reverse entry. |
| Depends-On chip `×`, api v3 `removeDependency`, Ctrl+D on the Depends-On row | Write only the dependent | Also remove the entry from each removed target's line, deleting the line when it empties. |
| Nav hand-edit mirror (cursor leaves an edited Depends-On line; also re-armed by Ctrl+Z) | R1/R9 on the dependent | Diffs old against new targets and updates the mirror. This keeps cross-note **undo** honest. |
| Capture `&note:id` (and Bob Mac Capture through bob) | Stages the dependent and the target `[id::]` | Also stages the target's BLOCKS line and the dependent's minted `^id` **in the same batch**, using the shared Rust renderer. |
| Ctrl+Shift+M move, `bob task archive`, project conversion | Rebase links in the moved block | The moved owner's line is rebased by the generic code. Links *into* a moved dependent are left to reconcile; chips stay correct because they render live. Conversion skips and re-plans BLOCKS the same way it handles Sub-projects. |
| Close, cancel, or reopen (capture `=x`, Ctrl+Enter, Alt+], Mac Capture, hand edits) | No dependency writes | **None in v1.** The owner's line freezes; a closed dependent drops off at the next reconcile. |

All writers share one planner, the JS twin of the Rust function, fed by shared vectors. Writers ignore
changes confined to a BLOCKS line as graph input and compare canonical output before writing, which
prevents feedback loops and extra undo entries.

### Gestures on a BLOCKS line

| Gesture | Behaviour |
| --- | --- |
| Hand edit (typing, deleting an entry, deleting the line) | Never an edge change. Reconcile restores the canonical line. If nav sees the edit, it shows `🧱 BLOCKS is generated from other tasks' DEPENDS ON lines · Ctrl+Shift+P on the dependent to change it`. Restoring when the cursor leaves the line is optional polish. |
| Ctrl+D on the row | **Refused**, with the notice above. One key must not write N notes. |
| `!` / Ctrl+Shift+Enter | Refused, as on Depends-On. block-id-prompt needs the new guard ([Compatibility guards](#compatibility-guards)). |
| Ctrl+Enter / Alt+] / Alt+[ on a link | Acts on the **linked dependent**, as §8 does for Depends-On links. |
| Ctrl+Shift+P on the line | Opens the Task Card for the **owning** task. Never treat the chip under the cursor as the owner. |

### Chips

*The beautiful part, in bob-ledger-tools.*

Live examples (titles abbreviated; the first owner is the `sase_blog_0` intro ref task, whose dependent also
waits on the outline ref):

```text
[ ] The first SASE launch post: introduction
    🧱 blocks  ( ? Review outline and intro proposal )                       frees 0 of 1
[?] Did enrolling for unemployment work!
    🧱 blocks  ( ? Audit monthly… 🔑 )  ( ? Dispute North Face… 🔑 )  ( ? Get access… 🔑 )  ( ? Save Verizon… 🔑 )   frees 4
[ ] bar boom bam
    🧱 blocks  ( ? 🧩 foo bar baz ↗ sase_foo 🔑 )                                frees 1 project
[x] (closed owner, frozen line)
    🧱 blocked  ( ✓ … )  ( ✓ … )                                                ✓ freed 2
```

- **Anatomy:** reuse the `bob-dep-row` / `bob-dep-chip` family and its `--task-status-*` tokens: the
  miniature checkbox, a description of about 40 characters, `↗ note` for cross-note entries, the tooltip,
  hover preview, and click/Mod-click. No new palette. Chips never change line height and wrap between
  chips, never inside one.
- **The 🔑 badge carries the signal.** Every live dependent is `[?]`, so status colour cannot distinguish
  chips on this row. 🔑 means T is D's *only* remaining reason to be Blocked: no other open prerequisite, no
  future `scheduled`, no project reason. The tooltip lists any other reasons ("also waits on 'Outline', and
  on 2026-11-02"). Colour is never the only signal, and each badge has `aria-label` text.
- **Summary:** `frees N` when every chip has 🔑, `frees N of M` otherwise, and `frees 1 project` for a
  `^prj` dependent. On a closed owner the label becomes past tense (`blocked`) and the summary reads
  `✓ freed M`, so a frozen line never reads as a live claim. As with `waiting on N`, the summary is never
  written to Markdown.
- **Data:** a reverse index `id → dependents` built from the in-memory Tasks memo, ported from the cycler's
  `buildDependentsIndex`. Chips render the **live** set in the stored line's canonical order. A live
  dependent missing from the text is appended; a stored entry that is no longer live renders dashed with a
  "will refresh" tooltip. Lag stays visible but quiet.
- **Implementation:** a `BLOCKS` prefilter beside the `DEPENDS ON` one, with an explicit relation direction.
  Do not reuse the incoming row's `waiting on` copy, action callbacks, or ARIA labels as-is (cdx: they are
  hard-coded in `140-dependency-model.js`, `150-dependency-element.js`, and both render paths).
- **No `×` or `＋` in v1** ([RA12](#requirement-adjustments)). The tooltip says "Edit from the dependent's Depends-On line".
- Without the plugin, the line still reads: `🧱 BLOCKS: ^audit-subscriptions • ^call-north-face • …`.
- No overflow disclosure is needed at a maximum fan-in of 4. Revisit a `+N more` disclosure (cdx) if fan-in
  ever regularly exceeds about 6.

### Compatibility guards

*These ship first.*

| Engine | Hazard | Fix |
| --- | --- | --- |
| bob-cli capture, `capture_completable_tasks.rs:329` | Skips only `is_dependency_line`, so a BLOCKS line in today's daily note counts as a Task Link sighting. | Skip BLOCKS lines too. |
| bob-cli reconcile, `task_status_hooks/pomodoro.rs` (`block_link_occurrences`) | Any block link on a bullet under a Pomodoro entry counts as a Task Link, feeding promotion, consumption, and successor anchors. The same latent bug exists for Depends-On lines. | Exclude both managed dependency lines. |
| block-id-prompt (`startTaskLinkOpen` / `applyTaskLinkOpen` guards) | Ctrl+Shift+Enter on a BLOCKS link would start the Task Link flow. | Add an `isTaskBlocksLine` guard. |
| nav hand-edit mirror (`planDependencyHandEditMirror`) | A machine write to a chain node's BLOCKS line looks like a "touch" and triggers a needless recovery pass. | Ignore changes confined to a BLOCKS line. |
| task-status-cycler strike and restore | Safe for canonical lines; a hand-struck entry could be re-embedded on reopen. | Skip BLOCKS lines next to Depends-On lines. |
| nav project conversion (`splitProjectLifecycleChildren`, `collectProjectSourceDependencyBlock`) | Would copy the line as a user child. | Treat it like Sub-projects: skip it and re-plan it. |
| Everywhere | No single list of machine-owned child lines exists. | Grow `docs/task-dependencies.md` §2.4 into a **managed-child-line registry** with vectors copied into every engine's tests (cld RA9). |

The first two rows were verified in bob-cli source. The plugin rows come from cld's audit, with the
relevant files confirmed to exist.

### Kill switch, outputs, and docs

- **Config:** `blocks_lines: true`, under a new `dependencies:` group or the nearest existing group, per
  config conventions. Setting it to false makes the desired set empty, so reconcile deletes every BLOCKS
  line on open tasks and mints nothing. Frozen lines on closed tasks stay as history. Nav and capture read
  the same setting. A brief mismatch is harmless because reconcile converges and gestures only write on
  demand.
- **Reconcile report (additive JSON and human output):**
  - `blocks_line_updates {path, line, task, kind: inserted|rewritten|removed|canonicalized|deduplicated, added[], removed[]}`;
  - `minted_dependent_block_ids {path, line, block_id}`;
  - the new warning kind `malformed_blocks_line`.

  `--dry-run --format json` previews all of it, and that preview is how to sign off on the migration.
- **No new subcommand or flag.**
- **Docs:** a new contract section ("Blocks lines": grammar, membership, order, position, authority,
  gestures, chips, and BK/BR/BW/BC vectors). Also update `docs/projects.md` for the anchor change.
- **Memory:** a new decision record (proposed title: *"BLOCKS Lines Mirror Depends-On And Are Never Read
  Back"*) and a one-sentence amendment to `glossary:task-dependency-link`, both through
  `/sase_memory_write`.

---

## Edge cases

| Case | Outcome |
| --- | --- |
| Two dependents share one prerequisite | One line with two links. |
| A dependent has two prerequisites | Both lines list it, and neither shows 🔑 (`frees 0 of 1` on each). |
| T closes or is cancelled | Its line freezes, and the chip shows `✓ freed M`. |
| T reopens | Re-projected on the next reconcile; nav gestures project it immediately. |
| D closed by hand while T is open | Dropped at the next reconcile; if it was the last entry, the line is deleted. Chips hide the lag. |
| D moved, or its block id renamed by hand | Re-projected and re-sorted. A projection has nothing to heal. |
| A hand-added entry with no matching edge | Removed. No forward edge is ever created. |
| Two BLOCKS lines, or a BLOCKS line copied by copy-paste | The first is kept; a copy under a task with no dependents is deleted. |
| T is `^prj` | The line goes after Depends-On and before Sub-projects. |
| D is `^prj` | Listed once as `[[note#^prj]]`. The chip shows the project name and `frees 1 project`. |
| Implicit resident → `^prj` prerequisite edge only | Not listed. |
| R8 legacy-child edge | Listed, while the legacy window lasts. |
| D lives in the previous daily note | Not listed and not minted. |
| T lives in the previous daily note or `done/` | Never written. |
| T archived with a frozen line | The line travels with it; `repair_pathless_archive_links` qualifies `[[#^d]]`. |
| Mixed plugin versions during rollout | An old nav ignores the line (its parsers require the DEPENDS ON label), which is why the guards ship first. |
| Kill switch turned off | Every line on an open task is removed; frozen lines stay. |

---

## Rollout

Each step is one bead, in the order the Depends-On epic used: contract and guards before chips, chips
before any writer.

1. **Contract.** The new contract section, the managed-child-line registry, the BK (parse), BR (reconcile),
   BW (immediate write), and BC (chip) vectors, the `docs/projects.md` anchor wording, and the decision
   record plus glossary amendment.
2. **Compatibility guards** in every engine ([Compatibility guards](#compatibility-guards)). Ship them and run `bob plugins sync` before any writer
   exists.
3. **Chips** in ledger-tools: the reverse index, the renderer, the 🔑 badge, the summary, and past-tense
   frozen lines. They are useful at once on hand-written test lines.
4. **Reconcile** in Rust: the pass, minting, the outputs, the kill switch, and the projects-sync anchor. Run
   a dry-run on the real vault, review the ~15 inserts and 6 mints, then enable it.
5. **Immediate writers:** the nav stage, the Depends-On chip `×`, Ctrl+D, the hand-edit and undo mirror,
   the conversion skip-lists, and capture `&`.
6. **Phase 2 (separate epic):** a Blocks… inverse stage (Task Card "Blocks… (N)", Ctrl+Shift+P on the
   line, chip `＋` and write-through `×`) that writes the *dependents'* Depends-On lines. This is the
   "After this" gesture from Tasks, Linear, and GitHub. The 2026-10 Depends-On research deferred it as
   "later". A visible BLOCKS line will raise the demand for it.
7. **Later uses of the same index:** a `blocks N` / 🔑 hint on ROTTEN and decay review cards, "will free N"
   in the close preview (mus), and a blockers-first tiebreak in Ready. These need separate decisions, and
   none of them changes priority automatically.

**Pilot script:** add a same-note dependency, then a cross-note one; undo each; remove one through the
Depends-On chip `×`; close a prerequisite; hand-delete a BLOCKS entry; turn the kill switch off and back
on. After each step settles, `--dry-run` should report zero changes.

**Rough effort** (cld): Rust is medium. Nav is medium-to-large, mostly in removal paths and undo. Ledger is
medium. Cycler and block-id-prompt are small.

---

## Risks and what would change this recommendation

- **Recogniser sprawl is the main risk.** A fifth grammar must be *ignored* correctly by Rust, nav, ledger,
  the cycler, and block-id-prompt. The registry and vectors in step 1 are the mitigation; skipping them is
  how this feature would cause bugs.
- **Visible lag between reconcile runs** in vim or git, when a dependent closes or moves. Obsidian hides it
  with live chips. Elsewhere the line catches up within one hooks interval. This is acceptable for a
  projection, and it is documented.
- **The count can be misread as priority.** The 🔑 badge and summary are information only. They never
  change priority, freshness, schedules, or lanes (cdx).
- **Reopen the approach** if BLOCKS-related reconcile warnings or nav repair passes show up on most runs
  for two weeks, or if the vault's fan-in grows enough that lines become walls of links. In either case,
  fall back to render-only chips, which are already built in [step 3](#rollout), and turn the kill switch off.

---

## Questions for Bryan

1. **Glyph:** `🧱 **BLOCKS:**` (recommended: a distinct glyph makes bottlenecks visible while scrolling)
   or `⛓️ **BLOCKS:**` (pairs visually with Depends-On)?
2. **A closed prerequisite:** freeze its line as a "freed these" record (recommended), or remove the line on
   close? Removing needs a new exception to "closed tasks are never touched".
3. **v1 chip actions:** navigation-only (recommended), or include a write-through `×` that edits the
   dependent's line in another note?
4. **Phase 2 key** for the Blocks… stage: `B` (Shift+b, the inverse of `b`) or a free letter such as `k`?

---

## Recommended solution

**Add one machine-owned `🧱 **BLOCKS:**` child line to every open task that has at least one open direct
dependent.**

- **Format.** It lists those dependents as plain, shortest-form block links joined by ` • `, sorted by link
  text. It sits right after the task's Depends-On subtree (or in that slot) and before `🧩 Sub-projects`.
- **Source of truth.** `⛓️ DEPENDS ON` stays the only one. BLOCKS is a pure projection of the explicit
  edge set: it is never read back, hand edits are restored, and inherited project and transitive effects
  are never listed.
- **Authority.** A new `bob task reconcile` pass mints missing dependent block ids (SB policy, no `[id::]`,
  no freshness stamps), then inserts, rewrites, deduplicates, and deletes lines. It never prunes on
  uncertainty, reports every change additively, previews it under `--dry-run`, and obeys the
  `blocks_lines` kill switch.
- **Immediacy.** Every forward-edge writer keeps the mirror current for **adds and removes**: same-note
  inside the dependent's one-undo transaction, cross-note as a best-effort follow-up after the commit.
  Closes are left to reconcile, and a closed owner's line freezes as history.
- **Beauty.** bob-ledger-tools renders the line as chips from a live reverse index. The chips match the
  Depends-On chips, a 🔑 marks the dependents this task alone is holding back, the summary reads `frees N`
  or `frees N of M`, and a frozen line reads `✓ freed M`. The view is correct between reconciles, and it
  shows what finishing the task will actually unlock.
- **Rollout order.** Contract and vectors, then guards in every engine, then chips, then the reconcile
  writer (dry-run first: about 15 lines and 6 ids today), then immediate writers. The editable Blocks…
  inverse stage follows as phase 2.

This meets the three goals:

- **Intuitive.** It reads as the mirror of DEPENDS ON, uses the vocabulary every tracker uses, and edits
  stay in one place.
- **Reliable.** There is one source of truth, the projection is idempotent and self-healing, the guards
  ship first, and the off switch is lossless.
- **Beautiful.** A calm, distinct glyph, chips that match the existing family, and a key badge that turns a
  backlink list into a measure of the task's leverage.

---

## Request and method

*Consolidated research · 2026-10-13 · bob-cli, bob-plugins, vault. Merges five independent reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`) with lead verification against the code, the dependency
contract, and a read-only query of the live vault.*

> **Request.** Automatically add a sub-bullet to tasks that other tasks depend on, showing that the task
> blocks one or more other tasks. It is the reverse of the existing `⛓️ **DEPENDS ON:**` line on the
> dependent. It should appear when dependencies are added (Ctrl+Shift+P, for example), and
> `bob task reconcile` should make every such sub-bullet exist and stay consistent. Lead the design
> (intuitive, reliable, beautiful), critique the plan, call out requirement adjustments, and recommend a
> solution.

---

## Sources

- **Swarm reports (this directory):** `prerequisite_blocks_line__cdx.md`, `__cld.md`, `__grk.md`,
  `__mus.md`, `__gem.md`.
- **bob-cli (at `92515f1`):**
  - `docs/task-dependencies.md` (§§2–4, 6.6–6.7, 7, 8, 12, 13.2) and `docs/projects.md` (Sub-projects rules);
  - `src/native/task_status_hooks/{compose.rs, pomodoro.rs, sync.rs, reconcile.rs}`;
  - `src/native/capture_completable_tasks.rs:329`;
  - `src/native/capture_block_ids.rs:619`;
  - `src/native/projects/sync.rs:911`;
  - `src/native/dataview/tasks/{index.rs, parse.rs}` (`is blocking`).
- **bob-plugins (at `4f0cc94`):**
  - nav `src/010-requires-and-config.js:166` (`🚧` = WIP) and `src/320-task-card-header.js:243` ("Blocked by…");
  - nav `prepareDependencyTargetNote` call sites;
  - ledger `src/140-dependency-model.js` and `src/280-plugin-dependency-render.js` (summary copy);
  - cycler `src/085-successor-plan.js` (the only reverse index).
- **Vault:** `bob query --tasks "(not done) AND (is blocking)"` and `"(not done) AND (is blocked)"`, run
  read-only on 2026-10-13: 15 blockers, 20 dependents (all `[?]`), 21 edges, 6 id-less dependents.
- **Memory:** `decisions:task-deps-are-depends-on-links`, `glossary:task-dependency-link`, `cli_rules.md`.
- **Prior research:** `research:202610/task_dep_link_depends_on_line/task_dep_link_depends_on_line.md`
  (Q4: a reverse "Blocks…" stage, deferred as "later").
- **External (as cited by the swarm):**
  - [Obsidian Tasks: dependencies](https://publish.obsidian.md/tasks/Getting+Started/Task+Dependencies) and [filters](https://publish.obsidian.md/tasks/Queries/Filters) (`is blocking`);
  - Tasks 6.1.0 `blockedBy` → `dependsOn` rename (PR #2568 / #2639);
  - [Linear issue relations](https://linear.app/docs/issue-relations);
  - [GitHub issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies);
  - [Asana task dependencies](https://help.asana.com/s/article/task-dependencies).

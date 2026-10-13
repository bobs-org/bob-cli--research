# A `🧱 BLOCKS` line: showing on a prerequisite what waits on it

*Researcher: cld · 2026-10-13 · bob-cli, bob-plugins, vault*

> **Request.** Automatically add a sub-bullet to tasks that other tasks depend on, saying that the task blocks
> one or more other tasks. The sub-bullet is the reverse of the existing `⛓️ **DEPENDS ON:**` line. It should
> appear when dependencies are added (for example with Ctrl+Shift+P), and `bob task reconcile` should make every
> such line exist and agree with the graph. Lead the design, critique the plan, and recommend a solution.

## Bottom line

**Build it, but only as a derived mirror that nothing ever reads back.** The forward `⛓️ DEPENDS ON` line stays the
only source of truth. The new line is a projection of it, maintained the same way `bob projects sync` maintains
the `🧩 Sub-projects:` line. If it is designed that way, it is cheap, fully reversible, and cannot corrupt the
graph. If it is designed as a second editable copy of the graph, it repeats the drift problem the Depends-On
redesign just removed.

The recommended shape:

```markdown
- [?] #task Did enrolling for unemployment work! [fresh:: 2026-10-01] [id:: cash__unemployment] [scheduled:: 2026-10-14] ^unemployment
	- 🧱 **BLOCKS:** [[#^call-north-face]] • [[#^get-access-money]] • [[#^save-verizon-router-pwd]] • [[#^…]]
	- Kelly just needs 2 pay stubs and/or my W2!
	- 🗓️ **SCHEDULE LOG**
```

In Live Preview and Reading view it renders as chips, the mirror image of the Depends-On chips:

```text
[?] Did enrolling for unemployment work!
    🧱 blocks  ( ? Dispute North Face jacket… 🔑 )  ( ? Get access to all of your money 🔑 )  ( ? Save Verizon Router… 🔑 )  ( ? … +1 )  ＋   frees 3 of 4
```

The ten decisions that matter:

1. **Label and glyph: `🧱 **BLOCKS:**`.** It is the grammatical mirror of `DEPENDS ON` ("T depends on A; T
   blocks C"), and it is the word Linear, Jira, GitHub, and Obsidian Tasks (`is blocking`) all use. 🧱 (a wall)
   is unused in the plugins. 🚧 already means a WIP project in nav, ⛔ is the Tasks plugin's `dependsOn` emoji,
   and 🔓 and ⏳ are taken.
2. **Membership is the Tasks plugin's `is blocking` rule.** An *open* task gets a line listing its *open*
   dependents. Closed tasks are never touched, so a line on a task that closes stays as frozen history. That
   mirrors §4.1 ("only open dependents are reconciled; closed tasks are never touched") and Linear, where a
   resolved blocker moves out of "Blocks".
3. **Only explicit edges are listed.** Inherited project blocking (residents waiting on `^prj`'s prerequisites)
   is not copied onto lines. The chip adds it at render time ("🧩 Apply to DataBricks · 7 tasks").
4. **The line is fully machine-owned and read-only.** Reconcile regenerates it from the graph and never infers
   an edge from it. If you hand-edit it, the edit is restored. Changes go through gestures that write the
   dependent's Depends-On line: chip `×` in phase 1, and an inverse "Blocks…" stage (Task Card `B`) in phase 2.
5. **Reconcile is the authority. Nav, capture, and the chip are immediate courtesy writers.** A same-note
   mirror write goes in the dependent's own transaction, so one Ctrl+Z undoes both. A cross-note mirror write is
   a best-effort follow-up, like today's Pomodoro cleanup, and reconcile repairs anything missed within one
   interval.
6. **Dependents get a minted `^block-id` when they lack one**, using the successor-link mint pipeline (SB
   vectors). The vault has 6 such dependents today.
7. **The order is canonical: sorted by link text, case-folded.** Reconcile regroups task blocks between status
   sections on every run, so document order is unstable, and the Sub-projects line already sorts
   alphabetically.
8. **Position: right after the Depends-On subtree**, or in Depends-On's slot when there is none. On `^prj` it
   comes before `🧩 Sub-projects`. Upstream and downstream sit together at the top of the block.
9. **Chips render from the live reverse index, not from the stored text.** The UI is therefore correct even
   while the stored line lags. Chips also add the insight that makes the line worth its pixels: 🔑 marks a
   dependent for which this task is the *last* open blocker.
10. **Ship it behind a kill switch that removes every line losslessly**, with compatibility guards in every
    engine *before* any writer emits a line. That is the same order the Depends-On rollout used ("chips and
    compat ship before any writer").

Today this means about **15 lines and 6 minted ids** across the vault (measured below). The trial is small,
and turning it off is clean.

---

## 1. What exists today (evidence)

### 1.1 The forward line and its machinery

- `docs/task-dependencies.md` is the contract. A task's prerequisites are plain block links on one managed
  `⛓️ **DEPENDS ON:**` first-child line (§2). That line derives `[dependsOn::]` on the dependent and `[id::]` on
  each target (R1–R10, §4).
- **Reconcile.** `bob task reconcile` reconciles only *open* dependents (§4.1), skips the previous daily note,
  never writes `done/`, and never moves lines (§4.3).
  - Pipeline: `task_status_hooks/sync.rs:206`, with `reconcile_dependencies` at `:430`, then a re-parse of
    touched files (`:440-443`), then `dependency_edges` (`:446`).
  - The reconciled per-dependent target set exists only inside the worker: `record_graph` at
    `reconcile.rs:1649`, aggregated into a private `graph` at `:108`. It skips dependents with no block id
    (`:1654`), and mixes in implicit resident edges at `:313`.
- **Immediate writers.** These already write *target* notes when adding:
  - Nav's Depends on stage prepares cross-note targets (`prepareDependencyTargetNote`, nav `main.js`
    55174–55238). It then commits the dependent in one editor transaction (`applyDependencyEditTransaction`,
    6840–6899).
  - Capture `&` stages target `[id::]` (`capture/dependencies.rs:767-842`).
  - **Neither touches the target's note on removal** (nav 6214–6226; "the target is never re-read",
    39759–39762).
- **Precedent for a machine-owned derived child line.** `bob projects sync` keeps a `🧩 **Sub-projects:**`
  line under `^prj` (`docs/projects.md`; `projects/edits.rs:542-556`). It is fully regenerated, deduplicated,
  and sorted alphabetically. It is anchored after the Depends-On subtree (`projects/sync.rs:911`), and it is
  deleted when empty.
- **Precedent for best-effort cross-note follow-ups.** A `^prj` block removes Pomodoro links in a follow-up
  write. "A cleanup failure shows the `Pomodoro links not removed` chip and is never rolled back; reconcile
  repairs it" (§6.6 step 3).
- **No reverse index exists in nav or ledger-tools.** The only one is the cycler's `buildDependentsIndex`
  (`task-status-cycler/main.js` 5502–5527), used for successor links.

### 1.2 The vault today (measured 2026-10-13, read-only scan of `~/bob`)

| Measure | Value |
| --- | ---: |
| Dep-link edges on Depends-On lines (outside `done/`, dot-dirs, `_templates`, …) | 57 |
| Same-note / cross-note | 39 / 18 |
| Distinct targets | 37 |
| Fan-in histogram (dependents per target) | 1×30, 2×3, 3×2, 4×1, 11×1 |
| Open target ← open dependent edges | **21** |
| Open targets with at least one open dependent (= BLOCKS lines to write) | **15** |
| Of those, lines with exactly one entry | 11 |
| Open dependents with no `^block-id` (= ids to mint) | **6** |
| Largest live line | `cash#^unemployment`, 4 open dependents |
| Largest fan-in overall | `sase#^post-blog-prj`: 11 dependents, but it is **closed**, so no line under the recommended rule |

Two things follow from these numbers.

- **The change is small.** Migration writes about 15 lines and 6 ids.
- **The value is concentrated.** Most lines would hold one same-note neighbour a few lines away. The payoff is
  in cross-note edges and in fan-in of 2 or more, and that is where the chip's 🔑 "last blocker" signal matters
  most.

### 1.3 How other tools show the reverse edge

| Tool | Reverse edge | What it teaches |
| --- | --- | --- |
| Obsidian Tasks (6.1+) | Edit modal fields **"Before this" / "After this"**. Adding a task under "After this" writes the *other* task's `dependsOn` line. Query filter `is blocking` = this task is open and "any of the tasks that directly depend on it are also" open. Nothing shows on the line itself; its docs list "not yet possible to directly navigate" as a limitation. | Membership = open → open. The reverse gesture writes the forward edge. The reverse view is useful enough that Tasks lists its absence as a known gap. |
| Linear | Sidebar sections **Blocks** (red flag) and **Blocked by** (orange). When the blocker resolves, the relation moves to *Related*. You can set either direction from either issue (`M B` / `M X`). | "Blocks" is a *live* view of open relations, editable from both ends. |
| GitHub issues (GA 2025) | Relationships sidebar: **"Mark as blocked by" / "Mark as blocking"**, with `is:blocking` and `blocking:` search qualifiers. | Same vocabulary, editable from both ends. |
| Jira | Link types "blocks" / "is blocked by". | Same vocabulary. |

Every mature tracker shows both ends of the relation and lets you edit from either end. None of them stores the
relation twice as user-editable text. They store one edge and render it in two places. A plain-text vault can't
"just render" without a plugin, which is why a stored mirror is justified here. But that mirror must behave
like a rendering, not like data.

---

## 2. Critique: is this a good idea?

### 2.1 Why it is worth doing

1. **Prerequisites can't be seen as prerequisites today.** Looking at "Did enrolling for unemployment work!",
   nothing says that four tasks are waiting on it. That is exactly the information you need when choosing
   between two Ready tasks, so this is a leverage signal for prioritising.
2. **It protects work that others depend on.** The ROTTEN review, the decay card, Alt+N release, and cancel
   all act on a task without saying "three tasks wait on this". A visible BLOCKS line (and later a chip on the
   decay card) makes it hard to cancel or decay a keystone task without noticing.
3. **Plain-text parity.** You edit in vim, and SASE agents read notes as text. The forward relation is visible
   in Markdown, but the reverse is visible only through a whole-vault scan or a Tasks query. A stored line
   makes `rg BLOCKS` and agent reads work.
4. **Navigation.** You can go from a prerequisite to its dependents with one click or `gf`. Today that means
   the backlinks pane (noisy, note-level) or a Tasks query.
5. **Symmetry is what users expect.** All four tools above show both ends.
6. **Trying it is nearly free.** A purely derived line can be removed with no information lost.

### 2.2 What could make it a bad idea

1. **Derived data in Markdown always drifts.** This would be the vault's fourth machine-owned derived artifact,
   after `[dependsOn::]`/`[id::]`, `#prj_is_blocked`, and the Sub-projects line. Between reconcile runs the text
   can be stale. *Mitigations:* chips render from the live index, and every immediate writer mirrors.
2. **Writer and recogniser sprawl.** The Depends-On decision already pays for "four parsers kept in sync by
   shared vectors". A fifth grammar has to be recognised, or *ignored*, by Rust, nav, ledger-tools, the cycler,
   and block-id-prompt. My audit (§6) found three places where today's code would misread the line. This,
   not the reconciler, is where the bugs would come from.
3. **More cross-note writes.** Removals now write the target's note, and closing a dependent eventually does
   too (lazily). That slightly raises the odds of an Obsidian Sync or vault-git conflict. At 21 live edges this
   is marginal.
4. **Clutter.** Most lines would hold a single same-note neighbour. That is acceptable, because consistency is
   more legible than a "hide when obvious" rule, but it is the honest cost.
5. **The temptation to make it editable.** If the line becomes an input, two sources of truth fight. The
   decision record `task-deps-are-depends-on-links` already rejected "a field-authoritative generated line" for
   this reason.

### 2.3 Verdict

**Yes, with a firm invariant:** *BLOCKS lines are written from the dependency graph and never read into it.*
With that rule, every failure mode is cosmetic and self-healing within one reconcile interval. Without it, the
feature is a liability.

### 2.4 The approach I would take differently

The request frames it as "keymaps add the line; reconcile ensures it." I would invert the emphasis:

- **The projection is one pure function, `blocks_lines(graph) → lines`,** specified by conformance vectors and
  implemented once in Rust and once in JS. Reconcile applies it to the whole vault. Each gesture applies it to
  the targets it just touched. No writer has its own rules.
- **Removal matters as much as addition.** Every writer of the forward line (stage, chip `×`, Ctrl+D,
  hand-edit mirror, undo, capture `&`, api v3 `removeDependency`, moves, project conversion) must call the
  projection for the old ∪ new targets, not just the added ones.
- **Rendering is decoupled from storage.** Chips use the live graph, so a briefly stale stored line is
  invisible in Obsidian.

---

## 3. Requirement adjustments (called out)

| # | Your requirement | Adjusted to | Why |
| --- | --- | --- | --- |
| RA1 | "tasks that other tasks depend on" | **Open** tasks with at least one **open** dependent. A closed task's line is frozen history (never edited). A closed or cancelled dependent drops off the line at the next reconcile. | Matches Tasks' `is blocking`, Linear's live "Blocks", and §4.1's "closed tasks are never touched". It avoids writing an 11-link line onto the closed `post-blog-prj`. Under this rule, closing a task in the normal order (prerequisite first) causes zero mirror writes. |
| RA2 | "automatically when dependencies are added (Ctrl+Shift+P)" | **Every forward-edge change, add *and* remove, by every writer.** A same-note mirror is atomic. A cross-note mirror is a best-effort follow-up. Closing or cancelling a dependent is lazy (reconcile only). | Adds without removes leave phantom entries. Lazy close keeps the close paths (capture `=x`, Ctrl+Enter, Alt+], Mac Capture) free of new cross-note writes. |
| RA3 | "reconcile ensures they exist and are consistent" | Reconcile **derives** them: it inserts, rewrites, canonicalises, deduplicates, deletes when empty, and mints dependents' block ids. It **never infers an edge from a BLOCKS line.** | This makes reconcile a pure projection: idempotent, and it never needs healing (a moved dependent is just re-projected). |
| RA4 | (new) | **The line is read-only.** Hand edits are restored (nav on cursor-leave, reconcile otherwise) with a notice that points to the gesture. Edits happen through chip `×` (phase 1) and a **"Blocks…" inverse stage** (phase 2) that writes the dependents' Depends-On lines. | One source of truth. An accidental `dd` on a BLOCKS line must never delete real dependencies in other notes. |
| RA5 | (new) | **Dependents without a `^block-id` get one minted** (SB pipeline, silently, like successor links). | A link needs a block id. 6 dependents today. |
| RA6 | (new) | **Explicit edges only.** Implicit resident → `^prj` prerequisite edges are not listed. Chips enrich a `^prj` dependent with its resident count. | The rejected alternative "copying project dependencies onto residents" applies equally to reverse copies. |
| RA7 | (new) | **Chips render the live reverse index**, with 🔑 "last blocker" badges and a `frees N of M` summary. | "Beautiful" should also mean *informative*. Live rendering hides lag. |
| RA8 | (new) | **Kill switch** `dependencies.blocks_lines: false` makes reconcile *remove* every BLOCKS line on open tasks. | Reversible trial. A stopped-but-present mirror would rot. |
| RA9 | (new) | **A shared "managed child lines" registry and guard vectors land before any writer.** | The audit (§6) found three misreads, and the managed-line knowledge is scattered across about seven places. |

---

## 4. The design

### 4.1 Name, glyph, grammar

**Writer form**

```text
<indent>- 🧱 **BLOCKS:** <link> • <link> • …
```

- 🧱 is U+1F9F1, a single code point with no VS16, which removes the variant-selector class of bugs that DP11 and
  DP24 deal with. A space follows it, then `**BLOCKS:**`, then a space, then links joined by ` • `. These are
  the same separator and link rules as Depends-On §2.1: **no aliases, embeds, or strikes.**
- **Why not aliases?** The line is machine-owned, so stored aliases would at least be accurate. But every
  rename of a dependent would rewrite the prerequisite's note, which is churn across notes, and the length
  doubles. Chips show live titles. The plain-text fallback reads `🧱 BLOCKS: ^call-north-face • ^…`, and
  slugged block ids read well (that is the point of the `＋ id` prompt).

**Reader tolerance** (recognised so it can be canonicalised and never duplicated):

- the emoji is missing or is 🚧;
- the label is `BLOCKING`;
- the separator is `·`, `,`, or whitespace;
- links are aliased, struck, or embedded;
- the line is a direct child other than the expected slot.

**Parse:** the same link-scanner-first algorithm as §2.3, keyed on its own label. A BLOCKS line is never a
Depends-On line and vice versa: each parser requires its own label, which `parse_dependency_line`
(`parse.rs:94`) and ledger's `parseDependencyLine` already do.

**Malformed** (prose after the links, a half-typed link): leave it alone and warn `malformed_blocks_line`.
Don't insert a second line. The line is machine-owned, but it never destroys typed text.

**Glyph choice**

| Option | Verdict |
| --- | --- |
| **🧱 BLOCKS** | **Chosen.** A wall is in the way of the listed tasks. Calm colour, pairs with ⛓️, unused across the plugins. |
| 🚧 BLOCKS | Reads as "under construction". Nav already uses 🚧 as the WIP project status glyph (nav `main.js:168`). |
| ⛔ BLOCKS | The Tasks plugin's emoji-format `dependsOn` marker: the opposite meaning. Also loud red on every prerequisite. |
| 🔓 / 🔑 UNBLOCKS | 🔓 is taken ("unblocked by hand", the ledger's unblocked glyph). "UNBLOCKS" overclaims when a dependent also waits elsewhere. 🔑 is kept for the chip badge where it *is* true. |
| ⛓️ BLOCKS | Same glyph as Depends-On, so the two adjacent lines can't be told apart at a glance. |
| `BLOCKING:` | Fine, but `BLOCKS` is the exact verb mirror of `DEPENDS ON` and is shorter. |

### 4.2 Membership: which tasks get a line, and who is on it

```text
open(t)      = status type Todo | In Progress | On Hold (includes [?])     — §4.1's scope
edges        = for each open dependent D in a reconcilable note: D's reconciled set
               (R1-projected resolved task targets, plus R8 legacy-child targets,
                plus cycle members), excluding R4 unresolved, R5 non-task, R6 self,
                and ^prj internal/descendant targets (never projected)
blocks(T)    = { D : (D → T) ∈ edges, open(D) }
T gets a line ⇔ open(T) ∧ blocks(T) ≠ ∅ ∧ T is writable
T is writable ⇔ T not in done/, not in the previous daily note, not fenced/blockquoted
closed T      → its line (if any) is never touched: frozen history
```

- **Dependents in the previous daily note** are excluded: they can't be minted, and that note is a snapshot.
- **`#hide`, `ref/`, inbox, and daily-note tasks** are all in, on either side. Chips mute `#hide`.
- **Cycles:** A ↔ B each list the other. The chip shows `⟲` with the path, reusing `dependency_cycle`.

### 4.3 Identity, link form, minting

- An entry links to the dependent's `^block-id` in the **shortest unambiguous form**, using the same function
  as the Depends-On writer (`format.rs:36` `canonical_link` / nav `canonicalDependencyLink` 6039–6074):
  `[[#^id]]`, then `[[basename#^id]]`, then `[[dir/note#^id]]`. A dependent in today's daily note is named
  explicitly (`[[20261013#^id]]`), following SL28.
- **Minting.** When D has no `^block-id`, append one with `mint_block_id(description, used)`
  (`capture_block_ids.rs:619`), reserving per-note used ids exactly as successors do (`successors.rs:1028-1062`).
  - Nav mints inside D's own commit transaction. Capture mints inside its staged batch. Reconcile mints in its
    BLOCKS pass.
  - **Never add `[id::]` to a dependent** for this purpose. `[id::]` means "is a prerequisite".
- **A minted id is not a freshness stamp.** BLOCKS writes never stamp `[fresh::]`, never change a status or a
  lane, and never touch T's task line. Only a child line is written ("automation never stamps").

### 4.4 Order

**Sort entries by canonical link text, case-folded (then raw, for ties).** Same-note `[[#^…]]` entries sort
first naturally, because `#` sorts before letters and digits. Then cross-note entries sort by note.

- **Why not insertion order** (the Depends-On rule)? A projection has no memory. Two writers (nav and Rust)
  would have to agree on history, and a moved dependent would reorder anyway.
- **Why not document order?** `compose.rs:86-115` regroups task subtrees between intake, Next and In Progress,
  Blocked, and Done every run, so document order is unstable and the line would churn.
- **Precedent.** Sub-projects sorts alphabetically (`projects/edits.rs:556`).

### 4.5 Position

```text
- [ ] #task T ^t
  - ❌ **CANCEL LOG**            (if present, stays first — §2.1)
  - ⛓️ **DEPENDS ON:** …         (upstream)
  - 🧱 **BLOCKS:** …             (downstream)
  - 🧩 **Sub-projects:** …       (^prj only)
  - …user children, 🗓️ SCHEDULE LOG, Work Log…
```

- **Insert:** after the Depends-On subtree if there is one. Otherwise use the Depends-On slot (first child, or
  second after a first-child Cancel Log). Reuse the task's child indent, otherwise parent indent plus one tab
  (DW8/DW9). Preserve CRLF and final-newline state (DW10/DW11).
- **Never move an existing line** (§4.3 "No moves"). Rewrite it in place; delete duplicates after the first.
- **Coordinated tweak to `bob projects sync`:**
  - `subprojects_anchor_child` (`projects/sync.rs:911`) anchors after the Depends-On *and* BLOCKS subtrees.
  - Its single move rule (`:944`, "moved only if it sits before Depends-On") becomes "before Depends-On or
    BLOCKS".
  - Without this, creation order would decide whether Sub-projects lands between the two dependency lines.
- **Depends-On is unaffected.** It is still inserted first, so a task that gains its first prerequisite after
  it already has a BLOCKS line ends up Depends-On, then BLOCKS.

### 4.6 Authority: the reconcile step

**Where.** Run a new step, `reconcile_blocks_lines`, *after* `reconcile_dependencies` and the re-parse of
touched files (`sync.rs:430-443`), and *before* `dependency_edges` (`:446`).

- `ReconcileOutcome` exports the explicit per-dependent sets that `record_graph` already sees (`reconcile.rs:1649`),
  before implicit resident edges are mixed in (`:313`). Archive targets are dropped, since `done/` is never
  written.
- A separate pass on re-parsed text avoids the "two inserts at the same index flip order" hazard in
  `reconcile/apply.rs:190`. That hazard would otherwise bite a task that gains an adopted Depends-On line (R2)
  and a BLOCKS line in the same run.

**Algorithm**

1. Build `blocks(T)` from the exported edges (§4.2). Mint missing dependent block ids first, then compute link
   text against the post-mint state.
2. For each writable open T, the desired line is either the rendered line or nothing.
3. Compare with T's existing BLOCKS child (recognised by §4.1 tolerance):
   - missing and desired: **insert** (§4.5);
   - present and different: **rewrite in place**;
   - present and not desired: **delete**;
   - malformed: leave it and warn;
   - duplicates: keep the first and delete the rest.
4. Edits are structural, so the existing 2 s quiet period applies (`task_status_hooks_write/model.rs:12`).
   They go through `apply_guarded_outputs` with the existing recovery snapshot.
5. With the kill switch off, the desired set is empty for every open T, so every line is deleted and nothing is
   minted.

**Output (additive)**

- `blocks_line_updates`: `{path, line, task, kind: inserted|rewritten|removed|canonicalized|deduplicated, added[], removed[]}`
- `minted_dependent_block_ids`: `{path, line, block_id}`
- `dependency_warnings` gains `malformed_blocks_line`.
- `--dry-run` previews all of it. This is how to sign off on the migration: about 15 inserted lines and 6 mints.

There is no new CLI command or flag. This is a step inside `bob task reconcile` and follows `cli_rules.md`
("`bob task <verb>` is reserved for commands that rewrite task lines across the whole vault").

**Kill switch.** A new `dependencies:` block in `~/.config/bob/config.yml` (`config/mod.rs:347` currently has
`plan` and `freshness`) with `blocks_lines: true`. Document it in `docs/task-dependencies.md` next to §12.8's
`plan.link_unblocked`. Nav and capture read their own copy (a plugin setting and the same bob config). A
mismatch is safe, because reconcile wins within one interval and nav writes only on gestures, so there is no
loop.

### 4.7 Immediate writers

| Writer | Today | With BLOCKS |
| --- | --- | --- |
| Depends on stage (Ctrl+Shift+P → `b`, Ctrl+Shift+P on the line, counted `N⌃⇧P b`, palette) | Writes the dependent, and prepares cross-note targets (`^id`, `[id::]`) *before* the commit. | **Same-note targets** (68% of edges): T's BLOCKS line is written in **the same editor transaction**, so one Ctrl+Z undoes both. **Cross-note targets:** a follow-up write *after* the dependent commits, for old ∪ new targets. On failure, the notice gets `· BLOCKS not updated` (warn tone) and nothing rolls back. A mirror entry is never written *before* the edge exists, so preparation stays as it is. |
| Chip `×` / api v3 `removeDependency` | Writes only the dependent. | Plus the mirror for the removed target. |
| Ctrl+D on the Depends-On row | Deletes the line, the field, and legacy children. | Plus the mirror for every removed target. |
| Hand-edit mirror (cursor leaves the edited Depends-On line; also re-armed by Ctrl+Z, nav 56649–56889) | R1/R9 on the dependent. Never writes cross-note. | Diffs old against new targets and mirrors them (cross-note as a follow-up). This also keeps cross-note **undo** consistent. |
| Capture `&note:id` (`capture/dependencies.rs:2066`, `:2536`), Bob Mac Capture through bob | Stages the dependent and the target `[id::]`. | Stages the target's BLOCKS line and the dependent's minted `^id` **in the same batch**, using the shared Rust renderer. |
| Ctrl+Shift+M, `bob task archive`, project conversion (Ctrl+Alt+Shift+N) | Rebase same-note links in the moved block (`rewriteTaskMoveBlockLinks` 25463–25530; `repair_pathless_archive_links`). | The **moved T's** BLOCKS line is rebased by the same generic code, with no change needed. Links **into** a moved D are left for reconcile; chips stay correct because they render live. Conversion must skip the BLOCKS line the way it skips Sub-projects (`splitProjectLifecycleChildren` 19218, `collectProjectSourceDependencyBlock` 19171), and re-plan it on the destination. |
| Closing, cancelling, or reopening a dependent (capture `=x`, Ctrl+Enter, Alt+], Mac Capture, hand edits) | No dependency writes. | **None. Reconcile only.** Normally the prerequisite closes first and its line freezes, so this is rare. |
| `bob projects sync` | Places Sub-projects after Depends-On. | The anchor tweak in §4.5. |

### 4.8 Gestures on a BLOCKS line (read-only, but not inert)

| Gesture | Behaviour |
| --- | --- |
| Hand edit (typing, deleting an entry, deleting the line) | When the cursor leaves the line (same debounce as the Depends-On mirror), nav **restores** the projected line and shows `🧱 BLOCKS is generated from other tasks' DEPENDS ON lines · Ctrl+Shift+P to change it`. Without nav, reconcile restores it. **Never** treated as an edge change. |
| Ctrl+Shift+P on the line | Opens the **Blocks…** stage for the owning task (phase 2). Phase 1 opens the Task Card. |
| Chip `×` | Removes this task from *that dependent's* Depends-On line (api v3 `removeDependency(D, T)`). It is an explicit gesture, the same as `×` on a Depends-On chip. |
| Chip `＋` | Opens the Blocks… stage (phase 2; hidden until then). |
| Click / Mod-click / hover | Open or preview the dependent, as on Depends-On chips. |
| Ctrl+Enter / Alt+] / Alt+[ on a link | Act on the **linked dependent**, mirroring §8's "acts on the target of the link under the cursor". |
| `!` / Ctrl+Shift+Enter | Refused, with the Depends-On notices. |
| Ctrl+D on the row | **Refused:** "Remove this task from N dependents' DEPENDS ON lines? Use Ctrl+Shift+P → Blocks…". One key must not write N notes. |

**The Blocks… stage (phase 2).** It is the Depends on stage with the roles swapped, like Tasks' "After this",
Linear's `M X`, and GitHub's "Mark as blocking".

- **Entry points:** a Task Card row "Blocks… (N)" on key **`B`**, which is Shift+b, the vim-style inverse of
  `b` "Blocked by…". The Task Card's repeat-guard regex `/^[0-9bfx]$/i` (nav 32607) must become
  case-sensitive for `b`/`B`; if you'd rather not, `k` is free. Also Ctrl+Shift+P on the BLOCKS line, and chip
  `＋`.
- **Same machinery as the Depends on stage:** CURRENT, RESULTS, and BLOCKED sections; ↵ toggles; ⇥ marks.
- **Guards** are the existing ones, evaluated for each picked D → T: self, cycle `⟲`, `^prj` internal or
  descendant targets, and stale rows.
- **Each newly picked D** gets T appended to its Depends-On line, with the §5 effects: it becomes `[?]` if T is
  open, D's lane transfers to T (`getDependencyPromotionStatus`), and D's live links are consumed if it is now
  Blocked. Removing D is the chip-`×` write.
- **Freshness:** stamp **T**, the task you are looking at and confirming, not the remote D (open question Q3).
- **Notices:** `🧱 Now blocks "Dispute North Face jacket" · it waits on 2` and `🧱 No longer blocks "…" · Ready again`.

The 2026-10 Depends-On research deferred this stage ("Q4 … later; it writes to other tasks' lines and is less
common"). A visible, read-only BLOCKS line raises the demand for it: once you can see the reverse edge, you will
want to edit it from there. So it should be the next phase, not "someday".

### 4.9 Chips: the "beautiful" part (bob-ledger-tools)

```text
[?] Save Verizon Router password, forward web traffic…
    ⛓ depends on  ( ? Did enrolling for unemployment work! )  ＋                       waiting on 1
    🧱 blocks     ( ? Set up Actual Budget! 🔑 )  ＋                                     frees 1

[ ] Generate AGENTS.md dynamically at launch!
    🧱 blocks     ( ? Memory beads ↗ sase_memory 🔑 )  ( ? Budgeted router ↗ sase +1 )  ( ? … ↗ gkeep_inbox 🔑 )  ＋   frees 2 of 3

[ ] Ship parent prerequisite
    🧱 blocks     ( ? 🧩 Apply to DataBricks NYC · 7 tasks 🔑 )  ＋                    frees 1 project
```

- **Anatomy.** Reuse `DependencyChipWidget` (ledger 12287) and its tokens: the miniature checkbox in
  `--task-status-*` colours, the description cut at about 40 characters, `↗ note` for cross-note entries, and a
  tooltip. There is no new palette.
- **The new badge is the point:**
  - **🔑** means T is D's *only* remaining reason to be Blocked: no other open prerequisite, no future
    `scheduled`, no project reason. Finishing T frees D.
  - **`+N`** means D also waits on N other open prerequisites.
  - **`🗓`** means D also waits on a future date.
  - **🧩 … · N tasks** marks a `^prj` dependent, with its open resident and descendant count.
  - Colour is never the only signal; every badge has a text equivalent in `aria-label`.
- **Summary:**
  - `frees N` when every dependent is 🔑, otherwise `frees N of M`;
  - `frees 1 project` for a `^prj` dependent;
  - on a *closed* T (frozen line), `✓ freed M`, past tense, so the frozen present-tense label never reads as
    false.
  - Like `waiting on N`, it is never written to Markdown.
- **Data.** A reverse index `id → dependents` built from the in-memory Tasks memo (`dependencyTasksIndex`, ledger
  28649). Ledger has none today; port the cycler's `buildDependentsIndex` (5502–5527).
  - Chips render the **live** set in the stored line's canonical order. A live dependent that isn't in the
    stored text yet is appended. A stored entry no longer live renders dashed with a "will refresh" tooltip.
    Lag stays visible but quiet.
- **Implementation.** Its own `BLOCKS` prefilter beside the `DEPENDS ON` prefilter (28985, 29891). The same
  ownership and visible-range rules as §7.4: never change line height, and wrap between chips, never inside
  one.
- **Without the plugin** the line still reads: `🧱 BLOCKS: ^budget`.

The first mock uses real vault rows (`cash#^save-verizon-router-pwd` → `^budget`). The other two use
illustrative titles, and minted ids such as `^get-access-money` are examples of the SB pipeline's output, not
verified mints.

**Later uses of the same index, not this epic:** a `blocks N` hint on decay and ROTTEN review cards, and
"blockers first" tie-breaking in the Ready lane. These are why I would build the reverse index as shared
infrastructure.

---

## 5. Edge cases

| Case | Outcome |
| --- | --- |
| T closes or is cancelled (any path) | Its line freezes as history. No writer touches it. The chip summary reads `✓ freed M`. |
| T reopens | Back in scope; the next reconcile re-projects it. |
| T archived to `done/` | The line travels with it. `repair_pathless_archive_links` qualifies `[[#^d]]`. `done/` is never written. |
| D closed by hand while T is open ("prerequisites never prevent closing") | Dropped at the next reconcile. If it was the last entry, the line is deleted. |
| D moved to another note | T's link goes stale until reconcile. Chips render live, so it looks right meanwhile. Reconcile re-projects to the new location and re-sorts. |
| D's block id renamed by hand | Re-projected. There is nothing to heal, because the line has no memory. |
| D or T duplicated by copy-paste (a BLOCKS line copied too) | The copy is reconciled on its own identity. A copied BLOCKS line under a task with no dependents is deleted. |
| Malformed BLOCKS line | Left alone, `malformed_blocks_line`, no duplicate inserted. |
| Two BLOCKS lines | The first is kept and rewritten; the rest are deleted (the Sub-projects precedent). |
| `^prj` T (a project is a prerequisite) | The line goes after Depends-On and before Sub-projects. Residents are *not* listed under T's prerequisites. |
| `^prj` D (a project depends on T) | T lists `[[project_note#^prj]]`. The chip shows `🧩 name · N tasks`. |
| Internal `^prj` target (refused or deadlocked; not projected) | Not listed. |
| Legacy R8 child edge | Listed: it is an edge during the legacy window. |
| Edge whose dependent lives in the previous daily note | Not listed and not minted. |
| T in today's daily note | Written (reconcile already writes today's daily). Dependents' links name the note per SL28. |
| Kill switch off | Every BLOCKS line on open tasks is removed. Frozen lines on closed tasks stay as history. |
| Mixed plugin versions during rollout | An old nav ignores the line (its parsers need the DEPENDS ON label). The block-id-prompt guard (§6) must ship first. |

---

## 6. Compatibility audit: what would misread a BLOCKS line today

These are concrete findings, with file and line references. Each needs a guard **before** any writer ships.

| Engine | Code | Hazard | Fix |
| --- | --- | --- | --- |
| block-id-prompt | `startTaskLinkOpen` (8521; guard at 8532) and `applyTaskLinkOpen` (9364; guard at 9376) | Ctrl+Shift+Enter on a BLOCKS link would run the Task Link open flow on it. Only Depends-On lines are guarded. | Add `isTaskBlocksLine` to both guards, with the same notice. |
| bob-cli capture | Task Link sightings in `capture_completable_tasks.rs:324-338` | It skips only `is_dependency_line`, so a BLOCKS line in today's daily note counts as a sighting. | Skip BLOCKS lines too. |
| bob-cli reconcile | `scan_pomodoros` / `block_link_occurrences` (`task_status_hooks/pomodoro.rs:58-99,150`) | Any block link on an indented bullet under a Pomodoro entry counts as a Task Link. That feeds promotion, retirement, consumption, and successor anchors. It only matters for a prerequisite nested inside the Pomodoros section, and **Depends-On lines have the same latent bug.** | Exclude both managed dependency lines. |
| nav | Hand-edit mirror (`planDependencyHandEditMirror` 5909–5965) | Any edit under a task that has a Depends-On line becomes a "touch". A machine write to a mid-chain task's BLOCKS line would trigger a no-op recovery pass. It doesn't stamp (the mirror never stamps), but it wastes work and invites surprises. | Ignore changes confined to a BLOCKS line. Route them to the restore path (§4.8). |
| task-status-cycler | Strike or restore on close/reopen (`retireClosedTaskReferencesInText` 5015–5091, `restoreReopenedTaskReferencesInText` 5095) | Safe for canonical plain links, because it only acts on `![[` and `~~`. A hand-made `~~[[#^a]]~~` would be re-embedded on reopen. | Skip BLOCKS lines next to Depends-On lines (5036, 5116). |
| nav | Project conversion (`splitProjectLifecycleChildren` 19218, `collectProjectSourceDependencyBlock` 19171, 62669–62678) | The BLOCKS line would be copied as a user child, or mis-ordered. | Treat it like Sub-projects: skip it and re-plan it. |
| everywhere | Managed-child knowledge is scattered: `parseManagedTaskLogParentBullet` (nav 2368 / `buildManagedTaskLogParentRe` 318), `getDependencyInsertLine` (5675), cycler `PROJECT_SUBPROJECTS_MARKER` (7832), recognisers `isTaskDependencyLine` (cycler 3007; block-id-prompt 3718/3750), Rust `child_slot` (`reconcile/apply.rs:115`) | There is no single list of "machine-owned child lines", so every new one is a scavenger hunt. | **Add one shared table** to `docs/task-dependencies.md` (§2.4 grows a row) with vectors, and copy it into each engine's tests. That is RA9. |

These are safe today, with no change needed:

- Rust `legacy_child_reference`, because the body must start with `[[`, `!`, or `~~`;
- `parse_dependency_line`, because the label differs;
- the Sub-projects marker detection;
- `is_section_title`;
- `embedded_children`, which only looks at embeds;
- ledger's `parseDependencyLine`, which requires its label;
- the cycler's `parseSuccessorLiveLink`, because the label makes the line more than a single link.

---

## 7. Alternatives considered

| Alternative | Why not (or not alone) |
| --- | --- |
| **Render-only reverse view** (no Markdown; a chip row decorates T) | The strongest alternative, and its rendering half is adopted as the chips. Alone, it fails your goal: it shows nothing in vim, git, agent reads, or `rg`, or without the plugin. A CM6 *block* widget for a line that doesn't exist would also break "chips never change line height". |
| **BLOCKS line editable in both directions** (deleting an entry removes the edge) | Two sources of truth. A `dd`, a cut-and-paste reflow, or an agent rewrite would silently delete prerequisites in other notes. Already rejected for the forward line as "a field-authoritative generated line". The inverse stage gives the same power on purpose. |
| **List all dependents, closed ones included** (pure inverse, like the forward line keeps closed prerequisites) | Writes an 11-link line onto the closed `post-blog-prj` on day one, and "BLOCKS" would be false for closed entries. The forward line keeps history because it is *authored*. A derived view should be live. |
| **Keep maintaining lines on closed T** | It touches closed tasks, which breaks §4.1/§13.7 conventions, and adds churn with no decision value. |
| **A task-line badge or field** (`[blocks:: 3]`, or a machine tag `#blocking`) | It crowds the task line. A field would sit in the Tasks suffix, where Rust parsers stop at unknown keys (§3 placement rules). Tasks already has `is blocking` for queries. A tag adds `#prj`-style substring hazards. |
| **"UNBLOCKS" label** | Motivating, but false when D also waits elsewhere. The 🔑 chip badge delivers the motivating version only where it is true. |
| **Insertion order / document order** | §4.4: a projection has no history, and reconcile regroups sections every run. |
| **Immediate mirror writes only, no reconcile authority** | Closes, deletions, vim edits, agent edits, and moves would never be repaired. |
| **Reconcile only, no immediate writes** | Satisfies "automatically" with a lag of up to 15 minutes. But a brand-new BLOCKS line wouldn't exist yet, so there would be nothing to render chips on, and same-note atomic undo would be lost. |

---

## 8. Draft conformance vectors (for a new contract §14)

**BK — parse**

| # | line | context | verdict |
| --- | --- | --- | --- |
| BK1 | `🧱 **BLOCKS:** [[#^a]]` | direct child of a `#task` | accept(1) |
| BK2 | `🧱 **BLOCKS:** [[#^a]] • [[cash#^b]]` | direct child | accept(2) |
| BK3 | `🧱 **BLOCKING:** [[#^a]]` | legacy label | accept(1), canonicalise |
| BK4 | `**BLOCKS:** [[#^a]]` / `🚧 **BLOCKS:** [[#^a]]` | emoji missing or variant | accept(1), canonicalise |
| BK5 | `🧱 **BLOCKS:** [[#^a]], [[#^b]]` | `,` separator | accept(2), canonicalise |
| BK6 | `🧱 **BLOCKS:**` | label only | empty → delete |
| BK7 | `🧱 **BLOCKS:** [[#^a]] waiting` | trailing prose | malformed: leave alone, warn |
| BK8 | `🧱 **BLOCKS:** [[#^a]]` | grandchild, fenced, or blockquoted | not-a-line |
| BK9 | `🧱 **blocks:** [[#^a]]` | lowercase | not-a-line (user prose) |
| BK10 | BK1 fed to every Depends-On parser, Task Link recogniser, Pomodoro link scanner, and managed-log parser | — | not-a-line |

**BR — reconcile**

| # | situation | outcome |
| --- | --- | --- |
| BR1 | open T, one open same-note D with `^d` | `🧱 **BLOCKS:** [[#^d]]` inserted in the §4.5 slot |
| BR2 | D has no block id | `^<mint>` appended to D (SB rule), then linked; `minted_dependent_block_ids` |
| BR3 | D closed by hand, T open, D was the only entry | line removed (`removed`) |
| BR4 | T closed, with a line | no change |
| BR5 | T in `done/` / the previous daily note | never written |
| BR6 | edge is R4 / R5 / R6 / a `^prj` internal target | not listed |
| BR7 | A ↔ B cycle | each lists the other |
| BR8 | R8 legacy-child edge | listed |
| BR9 | implicit resident → `^prj` prerequisite edge only | not listed |
| BR10 | cross-note D: unique basename / ambiguous / today's daily | `[[note#^d]]` / `[[dir/note#^d]]` / `[[20261013#^d]]` |
| BR11 | D moved to another note | entry re-projected and re-sorted |
| BR12 | hand-added entry with no edge | removed (`rewritten`) |
| BR13 | two BLOCKS lines | first rewritten, second deleted (`deduplicated`) |
| BR14 | BLOCKS line at third child | rewritten in place, not moved |
| BR15 | `^prj` T with Sub-projects, no BLOCKS | inserted after the Depends-On subtree, before Sub-projects |
| BR16 | task gains an R2-adopted Depends-On and needs BLOCKS in the same run | both correct, Depends-On first (separate pass) |
| BR17 | entries `[[sase#^x]]`, `[[#^b]]`, `[[#^A]]` | order `[[#^A]] • [[#^b]] • [[sase#^x]]` |
| BR18 | second run | zero changes |
| BR19 | `blocks_lines: false` | every line on an open task removed; no mints |

**BW — immediate write** (nav and capture run these against the same renderer)

| # | gesture | outcome |
| --- | --- | --- |
| BW1 | add a same-note target | dependent and BLOCKS line in one transaction; one Ctrl+Z restores both |
| BW2 | add a cross-note target | dependent commit, then follow-up BLOCKS write; on failure `· BLOCKS not updated`, no rollback |
| BW3 | remove a target (stage, `×`, Ctrl+D, api v3) | target's entry removed; line deleted if empty |
| BW4 | Ctrl+Z after a cross-note add | hand-edit mirror re-fires and removes the entry |
| BW5 | Esc in the stage | no bytes written anywhere |
| BW6 | the hand-edit mirror sees a BLOCKS-only change | restore plus notice, no touch pass |
| BW7 | capture `&` onto an id-less new task | the task's minted `^id` and the target's BLOCKS line in one batch |

**BC — chips**

| # | live state | chip and summary |
| --- | --- | --- |
| BC1 | D's only reason is T | `🔑`; `frees 1` |
| BC2 | D also waits on 2 others | `+2`; `frees 0 of 1` |
| BC3 | D also has a future `scheduled` | `🗓`; not counted in frees |
| BC4 | D is `^prj` with 7 open residents | `🧩 name · 7 tasks`; `frees 1 project` |
| BC5 | stored entry no longer live | dashed, "will refresh" tooltip |
| BC6 | T closed (frozen line) | entries muted; `✓ freed M` |

---

## 9. Rollout

Each phase is one bead, in the order the Depends-On epic used.

1. **contract.** Add `docs/task-dependencies.md` §14 "Blocks lines": grammar, membership, order, position,
   authority, the gesture table, and BK/BR/BW/BC vectors. Grow §2.4 into the managed-child-line registry (RA9),
   and update `docs/projects.md` for the anchor tweak. Write a new decision record (proposed title: *"BLOCKS
   Lines Mirror Depends-On And Are Never Read Back"*) and a glossary strand **Blocks Line**. Both go through
   `/sase_memory_write`.
2. **compat** (all engines, fleet-installed before any writer): the §6 guards. Ship and `bob plugins sync`.
3. **chips** (ledger-tools): the reverse index, the BLOCKS chip renderer with badges, and `×` through api v3.
   This is useful immediately on hand-written test lines.
4. **reconcile** (Rust): the separate pass, minting, outputs, the kill switch, and the projects-sync anchor.
   Do a dry run on the real vault, review the roughly 15 inserts and 6 mints, then enable it.
5. **immediate writers:** the nav stage, `×`, Ctrl+D, hand-edit and undo mirror, the restore-on-edit path,
   conversion skip-lists, and capture `&`.
6. **inverse stage:** the Task Card `B` row "Blocks… (N)", Ctrl+Shift+P on the line, and chip `＋`.

**Rough effort.** Rust is medium (about one pass, plus minting and outputs). Nav is medium-large, because
removal paths and undo are the long tail. Ledger is medium. Cycler and block-id-prompt are small.

**Pilot.** Add a cross-note dependency, undo it, remove it via `×`, close the prerequisite, hand-delete a BLOCKS
entry, and turn the switch off and on. Check that `--dry-run` shows zero changes after each settles.

---

## 10. Questions for Bryan

- **Q1.** Is 🧱 `**BLOCKS:**` right for your eye, or do you prefer `BLOCKING`? *Recommendation:* 🧱 BLOCKS.
- **Q2.** Should a dependent you closed by hand drop off the prerequisite's line (recommended, live semantics),
  or stay struck as history?
- **Q3.** For the inverse stage: stamp freshness on T (the task you're looking at, recommended), on each D, or on
  neither?
- **Q4.** `B` (Shift+b, the inverse of `b`) or a separate letter such as `k` for "Blocks…" on the Task Card?
- **Q5.** Do you want the 🔑 "frees N" signal outside the line later: on decay and ROTTEN cards, and as a
  blockers-first tie-break in Ready? It is cheap once the reverse index exists.

---

## 11. Recommended solution

Add a **machine-owned `🧱 **BLOCKS:**` child line** to every **open** task that has at least one **open**
dependent. It lists those dependents as plain block links in the shortest unambiguous form, joined by ` • `,
sorted by link text. It sits right after the task's Depends-On subtree, or in that slot when there is none, and
before `🧩 Sub-projects` on `^prj`.

- **Source of truth.** The line is a **pure projection** of the Depends-On graph and never feeds it: explicit
  edges only, with R4/R5/R6 and internal targets excluded. Hand edits are restored.
- **Authority.** **`bob task reconcile` is the authority.** A new pass after dependency reconciliation mints
  missing dependent block ids (SB pipeline), then inserts, rewrites, deduplicates, and deletes lines. It
  reports `blocks_line_updates` and `minted_dependent_block_ids`, and is controlled by
  `dependencies.blocks_lines` (off means remove).
- **Closed tasks.** A closed task's line is never touched; it freezes as history.
- **Immediate writers.** Every forward-edge writer mirrors **adds and removes** right away: same-note inside the
  dependent's one-undo transaction, cross-note as a best-effort follow-up. Closing a dependent is left to
  reconcile.
- **Rendering.** **bob-ledger-tools renders it as chips** from a live reverse index. 🔑 marks dependents this
  task alone is holding back, `+N` marks ones that wait elsewhere, `🧩 · N tasks` marks projects, and the
  summary reads `frees N of M`. The view is correct between reconciles, and it shows what finishing the task
  will actually unlock.
- **Editing.** Edits happen from the dependent side or through gestures: chip `×` now, and a **Blocks…**
  inverse stage (Task Card `B`, Ctrl+Shift+P on the line) next.
- **Rollout order.** Ship the contract and vectors, then **guards in every engine**, then chips, then the
  reconcile writer (dry-run first; about 15 lines and 6 ids today), then immediate writers, then the inverse
  stage.

This meets the three goals:

- **Intuitive:** the line reads like the mirror of DEPENDS ON, and edits go through the same picker.
- **Reliable:** one source of truth, a self-healing projection, and a lossless off switch.
- **Beautiful:** a calm glyph, chips that match the existing ones, and a key badge that shows the task's
  leverage.

---

### Sources

- Contracts and code: `docs/task-dependencies.md` (§§2–8, 12–13), `docs/projects.md`; bob-cli
  `src/native/task_status_hooks/{sync.rs,reconcile.rs,reconcile/apply.rs,compose.rs,pomodoro.rs}`,
  `src/native/task_dependencies/{parse.rs,format.rs}`, `src/native/projects/{sync.rs,edits.rs}`,
  `src/native/capture/dependencies.rs`, `src/native/capture_block_ids.rs`,
  `src/native/capture_completable_tasks.rs`, `src/native/config/`; bob-plugins
  `bob-navigation-hotkeys/main.js`, `bob-ledger-tools/main.js`, `task-status-cycler/main.js`,
  `block-id-prompt/main.js` (line numbers are in the generated `main.js` files; edits belong in each plugin's
  `src/` fragments).
- Memory: `decisions:task-deps-are-depends-on-links`, `decisions:projects-block-from-prj-line`,
  `decisions:subprojects-inherit-project-blocking`, `decisions:task-status-is-derived`,
  `decisions:task-lanes-are-sticky`, `decisions:unblocked-tasks-resurface-as-ticklers`; glossary Task
  Dependency Link, Task Link, Project Task.
- Prior research: `research:202610/task_dep_link_depends_on_line/task_dep_link_depends_on_line.md` (Q4 on a
  reverse "Blocks…" stage; the alias, strike, and emoji resolutions);
  `research:202610/ctrl_shift_p_task_card/ctrl_shift_p_task_card.md` (Task Card keys and design principles).
- Vault measurements: a read-only scan of `~/bob` at commit `94411001` (2026-10-13).
- External:
  - [Obsidian Tasks: Task Dependencies](https://publish.obsidian.md/tasks/Getting+Started/Task+Dependencies)
  - [Obsidian Tasks: Create or edit Task](https://publish.obsidian.md/tasks/Editing/Create+or+edit+Task)
  - [Obsidian Tasks: Filters](https://publish.obsidian.md/tasks/Queries/Filters)
  - [Linear: Issue relations](https://linear.app/docs/issue-relations)
  - [GitHub Docs: Creating issue dependencies](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/creating-issue-dependencies)
  - [GitHub changelog: Dependencies on issues (2025-08-21)](https://github.blog/changelog/2025-08-21-dependencies-on-issues/)

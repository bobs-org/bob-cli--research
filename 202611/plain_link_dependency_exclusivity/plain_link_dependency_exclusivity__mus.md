# Dependency ⇄ relationless-link mutual exclusion: research (`__mus`)

## TL;DR

Yes, do it — but widen one clause, narrow one keymap promise, and put the
enforcement in Rust with the Obsidian panels as courtesy writers. The invalid
state (same target on a task's `⛓️ DEPENDS ON` line **and** its `🪢 LINKS`
line) is real, reachable from four writers today, and confusing in exactly the
way the request says: one row says "this blocks me" and the next says "this is
inert". The fix is a last-write-wins mutual exclusion: adding a dependency
removes the matching LINKS entry; adding a relationless link removes the
matching dependency edge — each in the same one-transaction write, previewed,
announced, and undoable with one Ctrl+Z. The one adjustment I insist on:
enforce it for **every** LINKS entry (labelled or not), not only relationless
ones, because a labelled relation to a prerequisite is the same contradiction
with added label-loss risk. Handle the label loss explicitly instead of
pretending it is relationless-only.

Recommended shape:

- Rust (`bob task reconcile` + both line planners + capture batch writer) is
  the authority that can never leave the overlap behind, including hand edits.
- Both Obsidian stages (Links `l`, Linked-from `⇧L`, Depends-on `b`,
  Blocks `⇧B`) get a symmetric convert affordance on the highlighted row, with
  matching `⛓ prerequisite` / `🪢 linked` badges, footer hints, a consequence
  strip, and one-transaction undo.
- Use `Ctrl+B` **inside the two pickers only** (never a global hotkey —
  `Ctrl+B` is Bold in the editor), and give the dependency panel the same
  `Ctrl+B` to convert back, so the key reads as "toggle blocking-ness".
- Reconcile heals pre-existing overlaps deterministically (dependency wins,
  reported + warned) rather than leaving a migration.

## Current state (what I actually read)

### The two lines and their contracts

- `docs/task-dependencies.md` owns the `⛓️ **DEPENDS ON:**` line:
  parser `src/native/task_dependencies/parse.rs`
  (`parse_dependency_line`, `DependencyLine`), formatter
  `src/native/task_dependencies/format.rs`, blocks mirror
  `src/native/task_dependencies/blocks.rs`, writers in §6 (Depends-on
  stage) and §15 (reverse Blocks stage), reconciliation R1–R10 in §4.
- `docs/task-relations.md` owns the `🪢 **LINKS:**` /
  `🪢 **LINKED FROM:**` lines: parsers
  `src/native/task_relations/parse.rs`
  (`parse_links_line`, `parse_linked_from_line`), planners
  `src/native/task_relations/plan.rs` (`plan_links_edit`), slot/order §4,
  cross-parse rule LK19/MC15 (§3.7: every parser returns not-a-line for the
  others' lines).
- Slot order on one task (`docs/task-dependencies.md` §2.4 table,
  `docs/task-relations.md` §4): Cancel Log → DEPENDS ON → BLOCKS →
  legacy Sub-projects → LINKS → LINKED FROM → user children / logs.
  `src/native/task_tidy/command.rs` canonicalises this order.
- Semantics are deliberately opposite: dependencies block, promote, consume
  Pomodoro links, and flip the dependent to `[?]`; relations "never block or
  change schedule, priority, or freshness" (`docs/task-relations.md` §2)
  except configured cancel/complete/merge/successor label effects (§§17, 18,
  20, 21). The docs even cross-acknowledge: "A link that needs to block is a
  dependency (`&`, `b`)" (relations §2).

### Relationless links exist and are ordinary LINKS entries

A LINKS entry is `[<label> ]<link>`; the label is optional
(`docs/task-relations.md` §3). A relationless link is just an entry with
`label: None` (`RelationEntry { target, block_id, label: None, … }` in
`src/native/task_relations/mod.rs`). The plan layer
(`plan_links_edit` / `LinksEdit { add, remove, relabel }`) already supports
add/remove/relabel by identity, so "remove the matching LINKS entry" is a
small extension of an existing operation, not a new primitive.

### The four writers that can create the overlap today

1. **Capture** (`docs/capture.md`): `&note:block-id` adds a dependency,
   `~note:block-id` / `~~note:block-id` writes a LINKS entry (§"Adding
   prerequisites with '&'", §"Linking tasks with '~' and '~~'"). Nothing
   stops one draft from naming the same target with both sigils, or a later
   draft from adding one edge when the other already exists. Capture already
   has a staged-batch writer, previews, `already_dependency` rows, and a
   precedent for destructive-but-previewed repair: the
   `dropped_dependencies` / `link_guard` drop of blocking deps
   (`src/native/capture/move_choice.rs`, `src/native/capture/output.rs`,
   decision `capture-link-drops-blocking-deps`).
2. **Obsidian Depends-on / Blocks stages** (`docs/task-dependencies.md`
   §6/§15; `plugins/bob-navigation-hotkeys/src/300-dependency-stage.js`,
   `590-plugin-dependency-stage.js`, `083-blocks-dependency-plan.js`).
3. **Obsidian Links / Linked-from stages** (`docs/task-relations.md` Rules
   7–8; `304-relation-stage-view.js`, `426-picker-relation-stage.js`,
   `085-relation-line-grammar.js`, `086-relation-line-plan.js`). The Links
   stage **already knows** about the overlap: `relationStagePrerequisiteIdentities`
   builds the owner's Depends-On identity set "so the stage can badge a
   candidate that is also a prerequisite (`⛓ prerequisite`, information
   only)", rendered as `bob-cnp-relation-prerequisite` in
   `410-picker-filter-and-render.js`. So the request's "make it clear" half
   is a half-built feature: the Links panel badges, the Depends-on panel
   does **not** badge the reverse (`🪢 linked` is missing —
   `300-dependency-stage.js` has `linkedKeys` plumbing and `alreadyLinked`
   but no relation badge I could find).
4. **Hand edits + reconcile.** Reconcile adopts/heals/canonicalises each
   line independently (R1–R10; relations §§6–7). No rule looks across the two
   lines, so a hand-typed overlap converges — both lines canonicalise —
   and stays forever.

### Keymap and footer context

- Relation picker keys today: `↑/↓` navigate, `⇥` mark, `↵` toggle/commit,
  `⌃↵` commit-with-relation, `~` flip direction, `esc` dismiss
  (`getRelationStageFooterHints` in `426-picker-relation-stage.js`). The
  dependency stage is `↵` toggle, `⇥` mark, `esc` cancel
  (`docs/task-dependencies.md` §6.4).
- `Ctrl+B` is Bold in any Obsidian editor context. Inside the modal pickers
  (which capture keystrokes) it is free; as a **global** hotkey it is not.
  The request says "add the `<ctrl+b>` keymap to the link panel", which I
  read as picker-scoped — that reading must be nailed down (see
  adjustments).

## Critique: is this a good idea?

**Yes — the core is right.** Two lines asserting opposite semantics about
the same target is not expressive, it is a bug farm:

- Status derivation reads only Depends-On; chips render both rows, so the
  user sees "waiting on N" **and** an inert link chip for N with no way to
  tell which is operative without opening source.
- Consumption/promotion silently ignore the LINKS copy, so "linked under
  today's Pomodoro" badges (`todayMap` / 🍅) can disagree with Blocked
  consumption.
- Cycle detection reads only dependency edges; a LINKS copy of an edge
  hides intent from the `⟲` guard without changing the graph.

**But the request as written has four gaps that would make it a net
negative if built literally:**

1. **Relationless-only is the wrong boundary.** A labelled relation
   (`follow-up of [[T]]`) to a prerequisite is the *same* contradiction
   plus silent label loss on conversion. If the rule fires only for
   labelless entries, users will keep the invalid state by adding any label
   — the exact gaming the rule exists to prevent. (More in adjustments.)
2. **Silent auto-delete is worse than the overlap.** Both directions destroy
   user-authored data (a label, authored order, or a blocking edge that
   explains a `[?]`). Without preview + notice + one-transaction undo, this
   becomes "my dependency vanished" support load. The capture
   `dropped_dependencies` precedent got this right (preview before submit,
   report after); the panels must match it.
3. **`Ctrl+B` global would collide with Bold.** It must be picker-scoped,
   discoverable from the footer, and harmless when the row is not eligible
   (disabled with a reason, never a no-op surprise).
4. **"Make it clear" needs both panels, not one.** Today only the Links
   panel badges the overlap. Shipping the write rule without the symmetric
   Depends-on badge leaves the dependency panel lying by omission ("no link
   here" while a LINKS entry exists).

## Adjustments to the requirements (explicit call-outs)

1. **[WIDEN] Mutual exclusion covers every LINKS entry, labelled or not.**
   The write rule becomes: *no target may appear on both lines at once,
   regardless of label.* Converting a labelled relation to a dependency
   drops the label — so that path requires an explicit confirm (or a
   label-preserving refusal; see design). Converting a dependency to a
   relationless link never loses data (dependency edges carry no label),
   so it can stay one keystroke. Rationale: labels do not resolve the
   contradiction; they only add lossy-conversion risk.
2. **[NARROW] `Ctrl+B` is picker-scoped, not global.** It fires only when
   the Links/Linked-from/Depends-on/Blocks picker is open and a row is
   highlighted. No new global hotkey, no Bold conflict, no registration in
   the Obsidian hotkey settings beyond the existing stage commands. If a
   global binding is ever wanted, that is a separate proposal with a
   different key.
3. **[ADD] Symmetric affordance with the same key both ways.** The request
   asks for `Ctrl+B` one way and "be able to do the reverse" without naming
   the key. I recommend `Ctrl+B` in **both** panels meaning "toggle this
   row's blocking-ness": in Links it converts link → dependency; in
   Depends-on it converts dependency → relationless link. One mental model,
   one footer line, no second chord to learn.
4. **[ADD] Reconcile heals history; writers prevent future.** The request
   only covers the interactive writes. Vaults already contain overlaps
   (hand edits predate any guard), so `bob task reconcile` must converge
   them deterministically, reported and warned like every other R-rule.
   Without this, the feature ships with a permanently dirty tail.
5. **[ADD] Capture gets the same rule, not just the panels.** A draft can
   already spell `&foo:bar` + `~foo:bar` on one item, and capture is the
   highest-volume writer. The rule belongs in the staged batch planner with
   the same last-wins semantics and the same preview/report shape as
   `dropped_dependencies`. Bob Mac Capture inherits it for free (thin
   client: it only renders `dropped_dependencies`/`link_guard`-style
   fields; decision `mac-capture-is-a-thin-client`).
6. **[CLARIFY] Last write wins *within* one gesture; explicit convert
   across gestures.** If a single gesture names T both ways (capture draft
   with both sigils, multi-mark `⇥` batch touching both lines), the
   **blocking** edge wins and the relation copy is dropped with a notice —
   because silently dropping a blocking edge changes status/lanes, while
   dropping an inert copy never does. Across separate gestures, the newest
   explicit gesture wins (link → dep, or dep → link). Cycle/self/archived
   guards from `docs/task-dependencies.md` §6.4 still refuse first; mutual
   exclusion never overrides a refusal.

## Design (intuitive, reliable, beautiful)

### 1. Semantics

- **Identity.** Same `(path, block-id)` resolution the hooks already use
  (shortest-form link resolution, `done/` explicit-path rule,
  `dependency_id(path, blockId)` fallback). Case-insensitive basename,
  archive-aware — reuse `resolveDependencyStageCurrent`-style identity, do
  not invent a second equality.
- **Convert link → dependency** = remove T from LINKS (authored order of
  the rest preserved; empty line deleted, no placeholder — both lines
  already use delete-on-empty) + append T to Depends-On (existing
  append-to-end order rule kept: re-added links go last) + all existing
  §6.6 side effects (mint `^id`/`[id::]`, `[dependsOn::]` field, `[?]`
  flip, lane promotion, Pomodoro consumption, `[fresh:: today]` stamp).
- **Convert dependency → link** = remove T from Depends-On (+ field,
  immediate recovery when no other reason remains — the existing §5
  "Removing a dependency" path, including `^prj` resident recovery and
  `[unblocked::]`) + append T to LINKS relationless (no label prompt;
  `⌃↵`-with-relation stays the labelled path).
- **Labelled LINKS → dependency** = same as above **plus** a confirm step
  naming the doomed label (`"follow-up of" will be dropped — dependency
  links carry no label. ↵ drop it · esc keep both? No — esc cancels`).
  Never silently discard a label. Alternative the implementer may choose:
  refuse labelled converts in v1 with `"remove the label first"`; worse UX
  but zero data loss. Either is acceptable; silent drop is not.
- **Batch rule.** Multi-mark or multi-note gestures plan every note before
  writing anything (capture already does; nav §6.6 does per-note
  preimage-checked transactions). Within one batch, trialing the add
  against the post-batch graph keeps the existing `⟲` cycle guard correct.

### 2. Where it is enforced (reliability)

| Layer | Role |
|---|---|
| `plan_links_edit` + dependency planner (Rust) | Authority: any add drops the cross-line match in the same plan. Unit-vector-tested per line-form (§3 grammars). |
| `bob task reconcile` | Backstop: converges hand edits and pre-feature vaults. New R-rule (e.g. R11): overlap → keep dependency, drop LINKS entry, warn `dependency_relation_overlap` with path/line. Reported in the existing projection-detail shape. |
| Capture staged writer | Same rule inside the batch; preview shows the drop; result reports it alongside `dropped_dependencies`. |
| Obsidian stages | Courtesy writers: they compose the same two-sided edit the authority would, so the preview/notice matches even before reconcile runs. |
| Bob Mac Capture | No work: renders what bob returns. |
| Chips (`bob-ledger-tools`) | Read-only: chips never change line height; the new `🪢 linked` badge on Depends-on rows reuses the existing chip-badge slot. |

Hand edits keep working (both grammars unchanged) — reconcile converges
them on the next run, exactly like every other canonicalisation. Writers
never insert a second line beside a malformed one (existing rule); an
overlap touching a malformed line refuses with the existing
"line is malformed" reason.

### 3. The panels (intuitive + beautiful)

- **Badges (the "make it clear" half).**
  - Links panel keeps `⛓ prerequisite` and adds the row state: muted when
    the prerequisite is closed (`✓×N`-style dimming already exists for
    Depends-on chips — reuse the token, no new palette, per the
    "no new palette" convention in `docs/task-dependencies.md` §7.1).
  - Depends-on panel gains the symmetric `🪢 linked` badge (information
    only, same slot, same muted-when-closed treatment). This is the one
    genuinely new UI element; everything else is a key + a strip.
  - CURRENT sections stay the source of truth: a row under CURRENT in one
    panel and badged in the other is the whole story at a glance.
- **Keys and footers.**
  - Links: `↑↓ navigate · ⇥ mark · ↵ link/unlink · ⌃B convert to
    dependency · ~ flip direction · esc dismiss`. On a CURRENT row,
    `⌃B` reads `move to dependencies`; on a RESULTS row already badged
    `⛓ prerequisite`, `↵` still toggles the relation (no-op-safe) while
    `⌃B` offers the convert.
  - Depends-on: `↑↓ navigate · ⇥ mark · ↵ toggle · ⌃B convert to
    relationless link · esc dismiss`.
  - Disabled rows (self, cycle `⟲`, unencodable, `^prj`-inside-project,
    malformed line) show the existing reason tooltip; `⌃B` on them does
    nothing and the footer does not promise otherwise.
- **Consequence strip + notice (the reliability half).** Reuse the
  existing `bob-cnp-consequence-strip` pattern from the relation
  cancel/complete flows: before commit, one line —
  `⛓ will also remove the relationless link to "…" · one Ctrl+Z restores
  both` / `🪢 will also remove the dependency on "…" · "…" becomes Ready
  again`. After commit, the existing notice shapes
  (`⛓ Now waits on …`, `⛓ No longer waits on … · Ready again`) gain one
  clause: `· removed 1 relation link` / `· removed 1 dependency`.
- **Undo.** The convert is one editor transaction (line + field + status
  + stamp), exactly like §6.6 — one Ctrl+Z restores both lines. Never split
  the drop and the add across transactions.

### 4. Capture specifics

- Parse keeps both sigils; the **planner** applies last-wins-per-target
  with the blocking-wins tiebreak, and `capture-parse` previews gain a
  `converted_relations` / `converted_dependencies` array mirroring
  `dropped_dependencies` (frozen wire shape, additive fields only — the
  existing contract discipline).
- `capture-complete` rows gain the symmetric badge data the panels have:
  relation candidates already carry `already_dependency`; dependency
  candidates need the mirror flag. Additive field, same name family.
- The `&`/`~`/`~~` grammar, sigil positions, and incomplete-needs errors
  do not change.

### 5. Vectors and tests (what "reliable" costs)

- Cross-parse vectors: LK-style vector that each of the four parsers
  returns not-a-line for the others' lines already exists (LK19/MC15) —
  add overlap vectors: same target both lines → planners drop the loser,
  order of survivors preserved, malformed refuses.
- Stage vectors: CURRENT-with-badge in both panels; `⌃B` on CURRENT vs
  RESULTS vs disabled; multi-mark batch with a cycle trialed post-drop.
- Reconcile vectors: hand-made overlap converges to dependency-wins +
  warning; labelled-overlap warn names the dropped label; empty-line
  deletion leaves no placeholder.
- Chips vectors: `🪢 linked` renders without changing line height, hidden
  when order-mapping disagrees (existing §7.4 rule).

## Alternatives considered (and why not)

- **Refuse instead of convert** ("that task is already linked — remove it
  first"). Safest for data, worst for flow: it turns the most common
  correction (oops, wrong kind of link) into two gestures plus a mode
  switch. Keep refusal only for the lossy case (labelled → dependency
  without confirm) and for existing guards (cycle/self/malformed).
- **Keep both, render as one** (dependency subsumes the relation in the
  UI). Hides the model mismatch instead of removing it; hand edits and
  capture output would still show two rows, and reconcile would still have
  to pick a winner. Rejected — the request's instinct that the state
  itself is the problem is correct.
- **Merge the two lines into one "edges" line.** Tempting, but it rewrites
  both frozen grammars, every recogniser's isolation table (§2.4), chips,
  the Mac thin client, and years of vault history for zero semantic gain:
  blocking and inert edges need different rendering and different gestures
  anyway. Mutual exclusion across two lines is the minimal change with the
  same invariant.
- **Dependency wins silently on every conflict, including interactive
  converts.** Wrong direction for dep → link converts: the user explicitly
  asked to unblock, and silent keep would read as "the key did nothing".
  Last-write-wins respects the gesture; blocking-wins applies only inside
  a single ambiguous gesture.

## Recommended solution (build order)

1. **Rust authority first** (`bob-cli`): cross-line drop in both planners +
   reconcile R-rule + vectors in `docs/task-relations.md` /
   `docs/task-dependencies.md` (docs first when vectors disagree — the
   standing contract discipline). Gate: `just check`-level unit suites for
   both line modules plus reconcile overlap vectors.
2. **Capture second**: planner + preview/report fields + Mac-rendered
   output for free. Gate: capture contract tests incl. the both-sigils
   draft.
3. **Panels third** (`bob-plugins`): symmetric badges, `⌃B` in both
   pickers, consequence strip, notices, one-transaction writes. Gate: the
   macOS-only targets via the exact-SHA run (`scripts/dev/macos-ci-check`
   or `/sase_monitor` on the SHA run — Actions is the only gate for those
   targets).
4. **Chips fourth** (`bob-ledger-tools` `🪢 linked` badge + muted states).
   Small, read-only, ships with the panels.
5. **Docs last**: `docs/` relation/dependency pages, footer/keymap tables,
   and the decision record for the widen (labelled included) with the
   `capture-link-drops-blocking-deps` precedent cited.

## Open questions for the lead

- Confirm the widen to labelled relations (my strong recommendation) vs.
  literal relationless-only. If literal, specify where labelled overlaps
  go: refused, warned-only, or left alone — "left alone" re-opens the hole.
- Confirm picker-scoped `Ctrl+B` (no global hotkey). If Bryan wants it
  global, pick a non-Bold chord instead.
- Confirm dependency-wins as the reconcile/migration default. The only
  sane alternative (relation-wins) would unblock tasks on upgrade — I do
  not recommend it, but it is Bryan's call to record.

## Sources consulted

- `docs/task-relations.md` (esp. §§2–4, 7–8, 17–21, vectors LK/MC/LG/LX),
  `docs/task-dependencies.md` (esp. §§2–7, 13–15), `docs/capture.md`
  (`&`/`~`/`~~` grammars, staged batch writer).
- `src/native/task_relations/{mod,parse,plan,format}.rs`,
  `src/native/task_dependencies/{mod,parse,format,blocks}.rs`,
  `src/native/capture/{move_choice,output}.rs`,
  `src/native/task_tidy/command.rs` (slot order).
- `plugins/bob-navigation-hotkeys/src/{300-dependency-stage,
  304-relation-stage-view,426-picker-relation-stage,
  410-picker-filter-and-render,590-plugin-dependency-stage,
  083-blocks-dependency-plan,085-relation-line-grammar,
  086-relation-line-plan}.js` (pools, CURRENT/RESULTS, badges, footers).
- `sase/memory/decisions/capture-link-drops-blocking-deps.md`,
  `sase/memory/decisions/task-deps-are-depends-on-links.md`,
  `sase/memory/decisions/mac-capture-is-a-thin-client.md` (descriptors).

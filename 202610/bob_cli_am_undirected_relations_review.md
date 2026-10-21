# Review of epic `bob-cli-am`: undirected task relations

> **Research query:** What do you think about the bob-cli-am epic bead? Is this
> feature/change in functionality good? What would you change if you could and why?

Checked on **Wednesday, October 21, 2026** against:

- bob-cli `dec8f879` on master (phase `.2`'s pair planner is the newest commit);
- the epic bead `bob-cli-am`, its eight phase beads, and their notes;
- the epic plan `plan:202610/undirected_task_relations.md` and the research behind it,
  `research:202610/undirected_task_relations/undirected_task_relations.md`;
- `docs/task-relations.md`, `src/native/task_relations/pair.rs`, the reconcile diff in
  `src/native/task_status_hooks/relations.rs`, and the label suggestions in
  `src/native/capture_complete/candidates.rs`;
- a read-only scan of the live vault (`~/bob`) for relation lines.

I did not open bob-plugins or bob-mac-capture. Claims about those repos come from the plan
and the phase-bead notes.

## Bottom line

**The feature is good. Keep the rule.** "A relation has no direction until you say what it
means" is the right model. It removes a choice that carried no information, it fixes three
real bugs, and it changes no storage. The bugs were: a plain re-add stripped a label, the
"already linked" check looked one way only, and reciprocal plain links would show twice.

**The plan is careful, but it is bigger than the evidence behind it.** The vault holds two
relations. Both are plain, and there are no labels anywhere. Yet most of the epic's
machinery serves labelled statements: two statements per pair, swap, reverse-label mode,
moving records between notes, and the inverse table.

If I could change one thing, I would **allow at most one relation per pair**. That removes
the planner's hardest special cases and gives every surface one simple invariant: one
related task, one row. Navigation already behaves this way (see
[R1](#r1-allow-at-most-one-relation-per-pair)), and the change is still cheap while phases
`.5`, `.7`, and `.8` are unmerged.

The other changes, cheapest first:

1. **Share the pair vectors as one JSON fixture**, as freshness, Pomodoro homes, and line
   digests already do, instead of hand-copying them into Rust and JS.
2. **Seed label suggestions with the inverse-table phrases**, so the label step offers
   something on day one.
3. **Extend the label hint to dependency words** (`blocks`, `depends on`, `waiting on`).
   These are the likeliest misuse of labels.
4. **Upgrade bob and the Mac app together.** The plan says version skew "affects copy
   only", but that is not true for `~~`.
5. **Stop adding relation features after this epic lands** until usage shows what labels
   are for.

## What the epic does

An unlabelled relation becomes one undirected link, shown as `🪢 links` with no arrow. A
labelled relation is a directed statement, read from its source: "S ‹label› T". A bare
`~~T` becomes an incomplete draft that asks for a label. Storage does not change. Each
relation is still one entry on one task's `🪢 **LINKS:**` line, mirrored on the other
task's generated `🪢 **LINKED FROM:**` line. Meaning is worked out per pair of tasks: a
labelled record subsumes plain ones, and a plain add never erases a label.

| Phase | Repo | Scope | Status |
| --- | --- | --- | --- |
| `.1` contract | bob-cli | Rewrite `docs/task-relations.md`; glossary strands | closed |
| `.2` pair-core | bob-cli | `pair.rs` planner, LW16 guard, reconcile projection, `redundant_relation` | closed (`dec8f879`) |
| `.3` capture-grammar | bob-cli | Bare `~~` incomplete, `kind`, symmetric `already_linked`, `~~note:id\|` | in progress |
| `.4` capture-writes | bob-cli | Pair-aware writers, `moved_from`, sentence-shaped output | in progress |
| `.5` nav-writer | bob-plugins | JS planner twin, writers, `api.relations` v2, Ctrl+D | in progress |
| `.6` ledger-chips | bob-plugins | `related()` index view, one `🪢 links` block per task | closed |
| `.7` nav-stage | bob-plugins | One Links row and stage, live label sentence, swap | in progress |
| `.8` mac | bob-mac-capture | Pickers, label card, previews | in progress |

## Is it good?

### Yes, for these reasons

- **It removes a meaningless choice.** Without a label, `A ~B` and `B ~~A` state the same
  fact, yet they used to produce different bytes, notices, and Task Card rows.
- **Real use agrees with it.** Both relations in the vault are plain:
  `sase.md ^create-sase-org` → `sase_pypi_releases ^ref-redesigning-source-control`, and
  `sase.md ^ref-athena-apollo-audit-triage` → `^ref-athena-apollo-operational-log-audit`.
  Each has a natural label ("inspired by", "follow-up of"), and neither got one. Plain links
  are the common case, so making them direction-free is the right priority. One caveat: the
  label card had a text-truncation bug until epic `bob-cli-aj` closed this morning, so
  "zero labels" partly reflects friction, not only preference.
- **It fixes real defects, not just copy.** The LW16 guard landed in
  `src/native/task_relations/plan.rs`: a bare add on a labelled entry is now `unchanged`.
  Before, it silently stripped the label.
- **Nothing migrates.** The storage grammar, line names, kill switch, and LR11 all stay the
  same.
- **Partial failures are harmless by design.** Labelled records subsume plain ones, and
  cross-note moves add before they remove. If the plugin's second write fails, the display
  is already correct and reconcile reports `redundant_relation`. This is the most robust
  part of the design.
- **The live sentence is the best single idea.** `This task — [follow-up of▏] → Retry
  design` shows which way a free-text label reads before anything is written. Free-text
  labels are ambiguous ("parent": whose parent?), and this addresses that without a type
  registry.
- **Requiring a label for `~~` is right.** One meaning per sigil keeps the `~~` guards
  uniform, and every client lands in the label step because the `~~` completion ends in
  `|`.

### Where it overreaches

#### 1. The scale is ahead of the evidence

Relations first shipped on 2026-10-20 (nine commits that day, `6d1f0a9c` through
`4907f00d`). Epic `bob-cli-aj` (the `|` label-card trigger) opened at 08:01 EDT today and
closed at 10:28. `bob-cli-am` opened at 10:08 with:

- eight phases across three repos;
- about three dozen new or changed contract vectors;
- a 744-line Rust planner with six request types, four of which no Rust code will ever
  call (capture uses only Link and State);
- a JS twin of that planner, a v2 plugin API with a legacy alias, and a new reconcile
  warning.

That is three relation epics in about 36 hours, for a feature with two uses. The core
plain-link rule needs perhaps a third of this. The rest is built for labelled statements,
which nobody has written yet.

#### 2. Two statements per pair cost the most

The plan keeps LR19: A —x→ B and B —y→ A can coexist. That one allowance causes most of the
special cases:

- **Planner.** These branches exist only because of it: "State when only the reverse
  statement exists → add a second statement"; "ClearLabel with a reverse statement → remove
  the record, notice `Removed ‘x’ · still linked by ‘y’`"; "Swap refused while T —y→ N
  exists"; and `RemoveStatement` as a request separate from `Unlink`.
- **JSON.** `existing_direction: "both"`, the `existing_label` fallback ("the row's
  direction when present, otherwise the reverse statement's label"), and a four-level rule
  for which record an `unchanged` row reports.
- **Capture.** `~T|a ~~T|b` in one item writes two statements.
- **UI.** One task can fill two rows in a links block or in CURRENT, so the Links count
  (related tasks) and the row count disagree.

The surfaces are also already inconsistent about it:

- **Navigation cannot create a second statement.** LG19 hides already-related tasks from
  RESULTS, CURRENT ⇧↵ edits the existing relation, and Swap is refused while a reverse
  statement exists.
- **Capture and the Mac can.** Their already-linked rows stay enabled "because … adding a
  reverse statement is still legal".

So the two-statement state can only be created from capture or a hand edit, but every
surface has to render, count, edit, and test it.

#### 3. The vectors are copied, not shared

`docs/task-relations.md` (lines 19–21) tells each implementation to copy the vector tables
it needs into its own tests. Phase `.5` plans a hand-made
`scripts/relation-pair-vectors.cjs`, "copied from contract §15 and the Rust tests". In
Rust, `pair.rs` uses a module-wide `#![allow(dead_code)]` (line 15), because ClearLabel,
Swap, RemoveStatement, and Unlink exist only as a test oracle for the JS twin.

bob-cli already has a better pattern: machine-readable fixtures that both languages run.

- `tests/fixtures/freshness_keeps/vectors.json` tags each case with
  `"runners": ["rust", "js"]`.
- `tests/fixtures/pomodoro_homes/vectors.json` marks `rust_only` cases.
- `tests/fixtures/line_digest/vectors.json` is mirrored by bob-navigation-hotkeys.

Two hand-copied vector sets will drift. That is the exact failure LW14 ("engine agreement")
is meant to prevent.

#### 4. The label step starts empty

`relation_label_suggestions` (`candidates.rs:1592`) ranks only labels that already exist in
the vault (`task_links_catalog`). With zero labels, the label step offers nothing except
the typed row. The plan's mock-up (`follow-up of · 3    merged into · 2    next step · 1`)
is aspirational.

The labels that render best at both ends are already listed in the inverse table
(contract §10): `merged into`, `duplicate of`, `follow-up of`, `superseded by`, and
`split from`. None of them is ever suggested until someone types it.

#### 5. The hint misses the likeliest misuse

The hint fires for `related`, `related to`, `relates to`, `see`, and `see also`. Bob also
has real dependencies: `&` / `*` in capture, and the `⛓️ DEPENDS ON` / `🧱 BLOCKS` lines. A
relation labelled `blocks`, `blocked by`, `depends on`, or `waiting on` looks like a
dependency but never blocks anything. Relations are inert (contract §2), so the mistake is
silent: the "blocked" task stays Ready. The glossary already separates
*Task Relation* from *Task Dependency Link*, but nothing teaches that difference when it
matters, which is while the label is being typed.

#### 6. Skew is not copy-only for `~~`

The plan's rollout says "Version skew affects copy only". Phase `.3` changes behaviour,
though:

- a bare `~~` becomes an incomplete draft that submit refuses;
- the `~~` completion replacement becomes `~~note:id|`.

A Mac build from before `.8`, run against a bob that includes `.3`, may append a space
after the inserted `|`. Phase `.8`'s step 2 exists to stop exactly that. The old card is
also not guaranteed to open on an inserted `|`, rather than a typed one; the research
itself says "verify on the Mac". And any old-flow `~~` capture without a label now fails on
submit. bob ships on the daily train and the Mac app is built separately, so this window is
real, even if it is small for a single user.

#### 7. Smaller things

- **Removing a statement can bring back an archived plain link.** In the LW18 state,
  N —x→ T exists and T, in `done/`, still holds a plain `[[N]]`. `plan_remove_statement`
  correctly leaves the read-only record alone (`pair.rs:676-682`), so after removing ‘x’
  the pair shows as a plain link again. The plan only adds the notice that names a kept
  read-only record (`still linked from bob_done`) for Unlink. RemoveStatement and
  ClearLabel need the same suffix, or a link appears to survive its own removal.
- **`pair.rs` tidy-ups.** `refused_plan` and `refused_logical` take arguments only to
  discard them (`let _ = (records, here_op, there_op);` at lines 321 and 341). The
  "unchanged" `PairPlan` literal is written out five times (lines 402, 446, 507, 652, and
  694). An `unchanged(records)` helper, no unused parameters, and a `dead_code` allow
  scoped to the oracle-only functions would shorten the file by a few dozen lines without
  changing behaviour. The module-wide allow would otherwise hide real dead code later.
- **Decided, so I am not reopening these, but they are worth watching:**
  - *Ctrl+D `clear_scope = shown`* deletes other tasks' statements in other notes, and
    cross-note writes are not one Ctrl+Z. The notice should list each removal with its
    note, so a mistaken press can be undone by hand.
  - *`decision_record = no`.* The rule spans three repos, which is exactly what the
    decisions web exists to protect. Once the design settles, a record would stop a future
    agent from giving plain links a direction again.

## What I would change

| # | Change | Why | Where | Cost |
| --- | --- | --- | --- | --- |
| R1 | At most one relation per pair | Removes the hardest planner, JSON, and UI special cases; "one related task, one row" everywhere | `.2` (reopen), `.3`–`.8` (shrinks them) | Medium now; higher after `.5`/`.7`/`.8` merge |
| R2 | One shared JSON fixture for pair vectors and the inverse table | Stops Rust/JS drift; follows the existing fixture pattern | `.5` (in progress), small `.2` follow-up | Small |
| R3 | Seed label suggestions with inverse-table phrases; add self-inverse rows for symmetric labels | Label step is useful on day one; steers users to labels that read well at both ends | `.3`, `.7`, `.8` | Small |
| R4 | Dependency-word hint | Catches the silent "blocked but not blocked" mistake | `.3` (bob), `.7` (nav) | Tiny |
| R5 | Upgrade bob and the Mac app together | The `~~` change is behavioural, not copy-only | Rollout note on `.3` / `.8` | None |
| R6 | Read-only leftover notice on RemoveStatement and ClearLabel | A removed link should never seem to survive | `.5` (in progress) | Tiny |
| R7 | Pause relation features for 2–3 weeks after landing, then measure | Lets usage decide the reopen triggers | — | None |

### R1. Allow at most one relation per pair

**The rule.** A pair is unrelated, plainly linked, or described by **one** statement in
one direction.

**What it removes.**

- The two-statement branches of State, ClearLabel, and Swap. RemoveStatement merges into
  Unlink, because removing the only statement unlinks the pair.
- `existing_direction: "both"` and the `existing_label` fallback.
- The `~T|a ~~T|b` two-statement case in capture.
- LR26 and LW20, and part of LW21.

Every surface then gets one invariant: **a related task appears exactly once, in one
row**, and the Links count equals the row count.

**What replaces it.**

- **Same direction, new label:** relabel in place, as today (LW4).
- **Opposite direction while a statement exists:** capture refuses with a teaching error,
  for example
  `cannot relate ~T|x: “T” already says ‘y’ about this task · change it with Ctrl+Shift+L`.
  The Mac picker already shows `Already linked · y` on that row, so the conflict is visible
  before submit. In navigation, CURRENT ⇧↵ edits the one sentence (relabel, swap, or
  clear), as it already does.
- **Two statements anyway** (from a hand edit or a sync race): render both, and have
  reconcile warn with a new kind (for example `conflicting_relation`), the same way it
  handles `redundant_relation`. Never auto-delete.

**Why the research's objection does not hold.** It rejected this as "a new refusal path
with no observed need". But the two-statement path has no observed need either, and it
costs far more: five surfaces must render, count, edit, and test it. Most of the
"opposite direction" cases people will actually write are inverses of the same fact
("A follow-up of B" vs "B followed up by A"). The inverse table already displays those
correctly from either end.

**Cost and timing.** `.2` is closed, so this reopens `pair.rs` (it gets smaller) and
rewrites a few LR/LW vectors. The phases still in progress mostly lose work. Decide before
`.5`, `.7`, and `.8` merge; after that, the savings mostly disappear.

**Reopen when** someone needs to say two *different* things about the same pair, not an
inverse of the same thing.

**If you keep LR19 anyway,** at least make capture and navigation agree. Today navigation
cannot create a second statement, while capture can.

### R2. Share one vector fixture

Add `tests/fixtures/task_relations/pair_vectors.json`. Each case holds the pair's records,
each side's writability, the request, and the expected output: per-side ops, mirror
deltas, `action`, `kind`, `moved_from`, and the refusal. Tag each case with `runners`, as
`freshness_keeps/vectors.json` does.

- Drive the Rust unit tests from the fixture.
- Have the JS twin's suite read the same file, as the freshness and line-digest vectors
  are shared today. Do not hand-copy it into `scripts/relation-pair-vectors.cjs`.
- Put the inverse-phrase table in the same fixture, so the ledger, nav, and (for R3) Rust
  share one copy.
- Point contract §15 at the file instead of telling implementations to copy tables.

Phase `.5` is writing the JS twin right now, so this is the moment.

### R3. Seed label suggestions

After the labels already used in the vault, offer the inverse-table phrases as built-in
suggestions with count 0. In bob, that is `relation_label_suggestions`; in navigation, it
is `relationIndex.labelSuggestions`. Add self-inverse rows for labels that really are
symmetric, such as `conflicts with ↔ conflicts with`. These are display-only and cost one
row each. The plan defers them to a reopen trigger, but they are cheaper than the
discussion. With R2, both languages read the table from the shared fixture.

### R4. Add a hint for dependency words

Extend the existing related-label hint, which never refuses, to `blocks`, `blocked by`,
`depends on`, `waiting on`, and `prerequisite of`, with copy such as:

`relations never block · use &T for a prerequisite or *T to block T`

This puts the glossary's Relation-versus-Dependency distinction at the moment someone is
confused about it.

### R5. Upgrade bob and the Mac app together

Do not run a bob release that contains `.3` with a Mac build from before `.8`. If
overlapping is unavoidable, have `.3`'s agent check the old app against a `~~note:id|`
replacement on the Mac. Either way, fix the rollout section's "skew affects copy only"
claim so later agents do not rely on it.

### R6. Name read-only leftovers on every removal

Have RemoveStatement and ClearLabel append the same `· still linked from ‹note›` suffix
that Unlink uses whenever a read-only record keeps the pair related. Phase `.5` owns
these notices.

### R7. Pause, then measure

After the epic lands, add no relation features for two to three weeks. Then count:

- relations in the vault;
- how many have labels;
- which labels were used, and whether any are symmetric or dependency-like;
- how many `redundant_relation` warnings appeared.

The plan's reopen triggers (common symmetric labels, two labels per direction, storage
side starting to matter) are good. Give them data before the next epic.

## What I would keep exactly as planned

- **Storage:** one authored LINKS record, the generated LINKED FROM mirror, and LR11.
- **The projection rule:** omit only plain incoming entries that the target already names,
  and never prune on uncertainty (a malformed LINKS line names nobody).
- **Labelled subsumes plain, plus add-before-remove:** partial failures stay invisible.
- **`~~` requires a label:** never silently rewritten, and completions end in `|`.
- **"Label" as the one word,** and additive JSON (`kind`, schema version 1).
- **One `🪢 links` heading,** with direction on each entry.
- **The live sentence** in the nav label field and the Mac card.
- **`.6`'s continuation row** for the second relation line. It avoids the
  cursor-motion and undo risks of the CM6 block-replace collapse that the plan itself
  flagged, which matters for heavy vim-mode editing.

## Suggested next actions

1. **Decide R1 now**, before `.5`, `.7`, and `.8` merge. If yes, post the decision to the
   in-progress phases and add a small follow-up to `.2` that drops the two-statement
   branches and vectors.
2. **Fold R2 and R6 into `.5`,** and R3 and R4 into `.3` and `.7`. Each is small and sits
   inside its phase's scope.
3. **Add R5 as a rollout note** on `.3` and `.8`.
4. **After landing, schedule the R7 check-in.**

I filed no beads. Each item depends on a decision about this epic, which only Bryan can
make.

## Sources

- Epic bead `bob-cli-am` and phases `bob-cli-am.1`–`.8`, including the `.2` and `.6`
  completion notes (`.6` records the continuation-row choice).
- `plan:202610/undirected_task_relations.md` (the design of record).
- `research:202610/undirected_task_relations/undirected_task_relations.md` (requirement
  adjustments A1–A11, rejected alternatives, where the researchers disagreed).
- Epic bead `bob-cli-aj` (label-card trigger; closed 2026-10-21 14:28Z).
- bob-cli `dec8f879`:
  - `src/native/task_relations/pair.rs` (lines 11–15, 313–352, 397–727);
  - `src/native/task_relations/plan.rs` (the LW16 guard);
  - `src/native/task_status_hooks/relations.rs` (`emit_redundant_warnings`, the
    `desired_entries` omission);
  - `src/native/capture_complete/candidates.rs:1592` (`relation_label_suggestions`);
  - `docs/task-relations.md` (lines 19–21, §3.2, §10 inverse table, §12, §15);
  - `docs/reference/capture-syntax.md` (the `&` / `*` dependency tokens).
- Shared-fixture precedent: `tests/fixtures/freshness_keeps/vectors.json`,
  `tests/fixtures/pomodoro_homes/vectors.json`, `tests/fixtures/line_digest/vectors.json`,
  `docs/freshness.md`, `docs/pomodoro-homes.md`.
- Relation history: `git log --grep=relation` (nine commits on 2026-10-20, from
  `6d1f0a9c` to `4907f00d`).
- Vault (read-only): `~/bob/sase.md` lines 21, 295, and 297, and
  `~/bob/sase_pypi_releases.md` line 25. These are the only relation lines in the vault.

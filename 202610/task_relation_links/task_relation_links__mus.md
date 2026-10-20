# Directed task links: design research (`mus`)

Research for Bryan's directed-links proposal: a general (non-blocking)
task→task edge with a forward line, an auto-maintained backlinks mirror,
capture syntax, a reverse-link gesture, and optional relation labels.

## TL;DR

Yes, build it — but **not as a second edge system next to dependencies**.
About 80% of the proposal already exists as blocking edges
(`DEPENDS ON` / `BLOCKS`, `&` / `*`, the `b` / `⇧B` stages, reconcile).
The genuine gap is exactly one thing: **there is no way to say "related
to" without saying "blocked by".** So the recommended solution is a
*non-blocking typed edge* that reuses the dependency architecture
wholesale, with two justified adjustments: (1) **drop the `~~` reverse
syntax** — reverse is already expressible by naming the owner, exactly
like `&` / `*` do; (2) **carry the relation label in the link alias**,
not in new syntax. Details in §7.

## 1. What already exists (do not rebuild it)

The vault already has directed task→task edges with all the machinery
the proposal asks for. Contract: [task-dependencies.md](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_14/docs/task-dependencies.md);
Rust: `src/native/task_dependencies/` (parser, formatter, link form,
legacy children) + the reconcile step in `bob task reconcile`.

| Proposal asks for | Already exists |
|---|---|
| Forward links sub-bullet | `⛓️ DEPENDS ON:` managed first-child line (§2), source of truth; `[dependsOn::]` / `[id::]` fields derived (§3) |
| Auto-consistent backlinks | `🧱 BLOCKS:` generated mirror (§14): projection of dependents, **never read as input**; reconcile is the authority |
| Picker to choose the other task | Depends-on stage (`b`) + reverse Blocks stage (`⇧B`), Tasks-cache pool, fuzzy rank ported from `capture_link_tasks.rs::rank` (§6) |
| Capture syntax both directions | `&note:block-id` (owner depends on named) and `*note:block-id` (named depends on owner), on new or existing owners ([capture.md](docs/capture.md), "Relating existing tasks") |
| "Link to current" gesture | Blocks stage writes the *other* task's Depends-On line from the current task (§5 "Adding from the prerequisite side", §15) |
| Chips UI | `bob-ledger-tools` chips: status-colored checkbox, 40-char text, `↗ note`, tooltips, `×` remove, `＋` add (§7) |
| Post-close linking | Successor offers on close (§12): closing a prerequisite links unblocked dependents into its slot |

Any general-links design that ignores this becomes two parallel edge
systems with two parsers, two reconcilers, two pickers, and two chip
families. That is the main risk of the proposal as written.

## 2. The real gap (why this is still a good idea)

`DEPENDS ON` means one thing: **finish-to-start blocking** (§5). Today
there is no way to express:

- *related to / see also* (no semantic effect),
- *duplicates / supersedes* (should probably close or merge, not block),
- *follow-up to* (temporal, not blocking),
- *reference for* (informational back-pointer),

without hijacking blocking semantics — which then wrongly flips the
task to `[?]`, promotes prerequisites into the Pomodoro, consumes Task
Links, and shows `waiting on N`. People currently abuse deps or prose
links for this, and both are bad: fake deps corrupt the walk, prose
links rot. A **non-blocking directed edge** fills a genuine hole, and
backlinks give the "what points here" view that Obsidian provides for
notes but that tasks lack entirely.

## 3. Critique of the proposal, point by point

### 3a. `LINKS` sub-bullet — good, with one scoping rule

A forward managed line is right (mirrors §2). Non-negotiable rule,
copied from §5: **a LINKS edge must never block, promote, consume, or
change status.** Deleting every LINKS/BACKLINKS line must change nothing
about blocking, scheduling, successor offers, or fields — the exact
guarantee §14 gives for BLOCKS. If a "link" ever needs to block, that
is a Depends-On edge, and the UI should say so (offer conversion, §7).

Open question the design must answer: line slot. Managed children are a
*closed registry* (§2.4); every engine's scanners must reject the new
lines. Natural slot: after BLOCKS, before `Sub-projects`/`SCHEDULE LOG`
(canonical order: Cancel Log, Depends-On, BLOCKS, Links, Backlinks,
Sub-projects, Schedule Log, Work Log). Proposed form, mirroring §2.1:

```markdown
- 🔗 **LINKS:** [[other#^id|blocks release]] • [[sase#^deep-fix]]
- ↩️ **LINKED FROM:** [[inbox#^followup|follow-up]]
```

### 3b. `BACKLINKS` auto-consistency — correct instinct, use the BLOCKS pattern

The proposal's "kept up-to-date automatically somehow" is exactly the
BLOCKS contract (§14): the mirror is a **projection, never an input**;
`bob task reconcile` (whole-vault, guarded write, before edges/blocked
derivation, §4.1) owns it; hand edits to the mirror are overwritten or
warned, never read back. Reuse the `BlocksUpdateKind`
(inserted/rewritten/canonicalized/removed/deduplicated) reporting shape
in `src/native/task_dependencies/blocks.rs` for the new mirror so
observability is free. Same closed-task rule as §5: closed link targets
stay on the line as muted history, never block, never warn.

One consequence: backlinks only stay correct if reconcile runs. That is
already true of BLOCKS today, so no new operational burden — but the
design must state it, and the Mac app (thin client, see decision
`mac-capture-is-a-thin-client`) must never write the mirror itself.

### 3c. `~` capture syntax — collides twice; salvageable with position rules

- **Collision 1:** `~` is the Pomodoro drop-list operator (`x~2`, `=~2`,
  `=#bugs~2`, grammar table in [capture.md](docs/capture.md)). A bare
  `~` parser must distinguish `=~2,3` (drop links 2,3) from
  `~sase:deep-fix` (link). Distinguishable *positionally* — drop-lists
  only occur inside operator-only `x`/`=` items, link-`~` only on
  task-text items — but it is one more overload on an already crowded
  sigil, and every overload is a teaching error waiting to happen.
- **Collision 2 (fatal for `~~`):** `~~` is strikethrough, and the dep
  parser *explicitly tolerates* struck links (`~~[[…]]~~` canonicalizes
  away, §2.2/R8, `block_link_spans`). A `~~note:block` reverse marker is
  visually and grammatically ambiguous with a struck-out link. Do not
  ship this.
- **Shell wart:** leading `~note:block` undergoes tilde expansion in
  bash/zsh; CLI users must quote it. The Mac app is unaffected, but
  `bob capture` parity (which the thin-client decision requires for
  grammar) needs a quoting note in help text.

Alternatives considered: `>` / `->` (reads well, but `>` is already a
quote/callout-adjacent char and needs shell quoting anyway); `=>`
(two chars, prose-unfriendly); `+~` / `~+` (novel, ugly). `~` still wins
on ergonomics *if* the grammar position disambiguates it — link-`~`
takes the `route:block-id` operand shape (`~projects/foo:bar`,
`~"Shopping List":bar`, mirroring `&`/`*` exactly), which a drop-list
(`~2,3`) can never be. Keep `~`, kill `~~` (see §3d).

### 3d. `~~` reverse syntax and `Ctrl+Shift+P` — both unnecessary, for different reasons

- **Reverse does not need syntax.** `&`/`*` already prove the pattern:
  direction is expressed by *which task owns the edge*, not by a second
  sigil. `&named` on new task T = T→depends-on→named;
  `*named` on new task T = named→depends-on→T. General links need only
  one marker: `~named` = owner→named, where owner is the new task text
  or the explicitly named owner (`@route+id` / `^route:id`, the same
  owner-naming table as deps). "Link other→current" = name the other
  task as owner: `^other:id ~cur:id`. Zero new sigils, zero strike
  ambiguity, and the existing `dependency_target` incomplete-mode
  machinery (`capture-parse` needs) transfers directly.
- **`Ctrl+Shift+P` is not a keymap, it is the palette prefix.** In
  Obsidian `Ctrl+Shift+P` opens the command palette; the existing
  gestures are `Ctrl+Shift+P then b` (Blocked-by stage) and
  `Ctrl+Shift+P then ⇧B` (Blocks stage), plus direct
  `Ctrl+Shift+B` / `Ctrl+Shift+Alt+B` (§6.1). The proposal's
  "`<ctrl+shift+p>` keymap?" is already taken. The consistent extension
  is obvious: Task Card `L` (link stage on this task) and `⇧L`
  (link-to-here stage, writing the *source's* LINKS line — the exact
  twin of §15), plus `Ctrl+Shift+Alt+L` as the direct hotkey. The stage
  reuses the §6.2 pool/ranking/guards wholesale, including cycle checks
  (meaningless for non-blocking edges — drop them) and the `^prj`
  guards (keep: linking into project notes has routing implications).

### 3e. Optional relation label — good idea, wrong carrier if it is new syntax

Do not invent `~target:label` or `~target (label)` micro-syntax. The
vault already has a label carrier for wikilinks: **the alias**.
`[[sase#^deep-fix|blocks release]]` renders beautifully everywhere
(Obsidian, chips, source mode), needs no grammar, and the shared
`block_link_spans` scanner already parses it (`aliased` flag). Rules:

- Alias on a LINKS line **is** the relation description (free text,
  capped ~60 chars; longer is a child bullet, not a label).
- Depends-On keeps forbidding aliases (blocking edges stay canonical) —
  so the two lines are visually and grammatically distinct, which
  teaches the blocking/non-blocking split for free.
- Capture form: `~route:block-id|label words here`, consuming to the
  next marker or end of item — mirrors the wikilink alias with no new
  quoting rules beyond what aliases already need.
- BACKLINKS mirror preserves the label so "why does this point at me"
  is answered at a glance.

## 4. What "beautiful" means here (concrete UI bar)

- **Chips reuse the §7 family**, not a new component: checkbox dot,
  40-char text, `↗ note`, tooltip, `×`/`＋` through nav api v1. Only
  deltas: neutral `--text-muted` coloring (never status colors — color
  means state, and links carry no state), a `→` direction glyph, and
  the relation label rendered in place of the target description when
  present: `→ blocks release ( ○ Launch swarm… )`. Broken links get the
  existing dashed `⚠ ^id not found` treatment.
- **Source mode must stay readable.** Without plugins the line degrades
  to `🔗 LINKS: [[other#^id|blocks release]] • …` — same graceful
  degradation §7 already guarantees for Depends-On.
- **No new palette.** The Obsidian palette is Tell, Don't Ask software;
  four stages (`b`, `⇧B`, `L`, `⇧L`) under one `Ctrl+Shift+P` prefix is
  the ceiling. Anything more belongs in the Task Card.

## 5. Reliability hazards the design must close

1. **Two mirrors, one reconciler.** BLOCKS and LINKED FROM are both
   projections; reconcile must update both in the same guarded write or
   neither (a half-projected vault lies in both directions).
2. **Mirror inputs are poison.** Both mirrors rejected by every
   Task-Link/Pomodoro/section/tree-close/strike scanner (§2.4 table
   grows two rows). Forgetting one scanner resurrects ghost edges.
3. **The Tasks-cache blind spot.** `getTasks()` exposes `id`/`dependsOn`
   — generic LINKS edges are invisible to it. Chips and stages need
   their own edge index (reconcile-emitted JSON, or a `note_tasks`
   extension), or every keystroke-adjacent read becomes a vault scan.
   This is the largest engineering unknown; spike it first.
4. **Rename/move healing.** R3-style healing (rewrite link to target's
   new location) must cover LINKS, or renames silently strand labels.
   The `unresolved_dependency_link` warning family needs `link_` twins.
5. **Closed-task semantics.** Keep links as history (muted chips),
   exactly like §5; never auto-delete on close (that destroys the
   "superseded by" record — the most valuable label).
6. **Perf.** §7.4's cheap-prefilter + visible-ranges-only discipline
   applies to both new lines; vault-wide backlink indexing lives in
   reconcile, never in the render path.

## 6. Would I take a different approach?

Two alternatives, both rejected but worth recording:

- **(A) Dataview-only backlinks, no mirror line.** Zero write
  amplification, always consistent. Rejected: fails offline/graceful
  degradation (§7.4 "without the plugin, the line still reads"), fails
  the Mac app's cached-agenda model (decision
  `idle-capture-shows-ledger-agenda` — the app never reads the vault,
  so it needs materialized lines via `bob` JSON), and splits truth
  between query-time and write-time.
- **(B) Unify deps and links into one edge table with kinds.**
  Elegant in the abstract; rejected as a migration: the Depends-On
  contract has vector-pinned tests in four implementations (Rust + three
  JS mirrors, each citing doc sections). A flag-day unification breaks
  all of them. Ship LINKS as a second line reusing the same *patterns*
  (parser shape, reconcile ownership, mirror discipline, chip family),
  and consider converging the internals behind shared helpers
  (`block_link_spans`, edit planner) without touching the dep contract.

## 7. Recommended solution

1. **One forward line, one generated mirror.** `🔗 LINKS:` (managed,
   alias = relation label, writer form mirrors §2.1) and
   `↩️ LINKED FROM:` (reconcile-owned projection, never read as input).
   Slot: after BLOCKS, before Sub-projects/Schedule Log. Register both
   in the closed managed-children table (§2.4) across all engines.
2. **Semantics: never blocking.** No status, promotion, consumption, or
   scheduling effects; deleting the lines is a no-op for the walk.
   Offer "convert to dependency" (`&`-equivalent) from the link stage
   for misclassified edges.
3. **Single capture marker `~`, no `~~`.** `~route:block-id[|label]`,
   same operand grammar as `&`/`*` (nested routes, quoted names).
   Owner naming reuses the deps table (`@route+id`, `^route:id`,
   `@@route+id`); reverse = name the other task as owner. `~~` stays
   strikethrough, full stop.
4. **Obsidian gestures mirror `b`/`⇧B`.** Task Card `L` + `⇧L`
   (link-to-here), direct `Ctrl+Shift+Alt+L`; same pool, ranking,
   guards minus cycle checks; same one-transaction write discipline
   (§6.6) minus lane/consumption side effects.
5. **Chips extend the §7 family** (neutral color, `→`, label-first,
   existing broken/closed states, `×`/`＋` via nav api).
6. **Reconcile owns both mirrors atomically**, with `link_`-prefixed
   warning twins, R3-style rename healing, and closed-as-history.
7. **Spike first:** the Tasks-cache-blind edge index (§5.3) — if chips
   cannot read LINKS edges cheaply, the whole feature misses the beauty
   bar. Everything else is transcription of proven patterns.

Phasing: (i) contract doc + parser/formatter + closed-registry updates
with vector tests; (ii) reconcile projection + mirrors; (iii) `~`
capture grammar + `capture-parse`/`capture-complete` contexts; (iv)
Obsidian stages + chips; (v) Mac Capture `~` completion delegating to
`bob capture-complete` (thin-client decision — the app never parses).

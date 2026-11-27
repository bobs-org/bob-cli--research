# Sibling link walks for area, project, notebook, and prose notes

Researcher: `mus` (independent swarm report, `__mus` suffix).
Request: add `]n`/`[n` link-walk support to area notes, project notes,
notebooks, and prose notes — in parallel with the in-progress `bob-cli-qq`
epic — with a link-walk widget at the bottom of the Property Card (always
below all cabinets), per-type walks grouped by parent, a new glossary term
for "link walk", and an intuitive `]N`/`[N` grouping if one can be found.
Lead the design so it is intuitive, reliable, and beautiful.

## Verdict

Yes, build it — with eight adjustments to the request as written (§3). The
core idea is sound: these four note types already form implicit sibling
rings through the `parent:` frontmatter every one of them carries, and
today `]n` is dead on all of them (a vault census finds zero `‹`/`›` nav
lines on any area, project, notebook, or prose note). The work splits
cleanly into a bob-cli half that is fully parallel-safe with `bob-cli-qq`
and a bob-plugins half that must wait for `bob-cli-qq.10` to close. The
`∠N` grouping the request is unsure about has a natural answer: the ring
is per-parent siblings, and the groups are the parents — `]n` walks within
a parent, `]N` leaps to the head of the adjacent parent's ring. No new
bytes are needed for `]N`; it derives from data the plugin already caches.

## 1. Verified ground truth

All facts below were verified against the bob-cli checkout (Rust sources,
`docs/`), the linked bob-plugins checkout (fragments under
`plugins/bob-ledger-tools/src/`, `plugins/bob-navigation-hotkeys/src/`),
the live vault via the installed `bob 0.6.0`, and committed prior research
in `research:202611` (base files and `__final` syntheses only — no
same-swarm peer reports were consulted).

### 1.1 The `n` walker reads written lines; it computes nothing

- `open-prev-link` / `open-next-link` scan the active note's body source:
  frontmatter and fenced code are skipped, lines scan top to bottom, first
  matching link wins (`483-nav-group-links.js`, `680-plugin-link-parse.js`
  lineage per prior research; verified live in
  `plugins/bob-navigation-hotkeys/src/483-nav-group-links.js`).
- Step label rule: exact `prev`, or starts with `‹`/`<`; exact `next`, or
  starts-or-ends with `›`/`>`. A single line carrying both links serves both
  directions. Any note with such a body line is immediately walkable — no
  plugin change required for `]n` v1.
- `[[` / `]` repeat the last bracket family (`s`/`w`/`n`). Family `n` has
  no uppercase plan today, so `[{`/`]}` on `n` show "No uppercase link
  walk" (established by prior `bracket_n_group_jumps` research, base file
  `research:202611/bracket_n_group_jumps/bracket_n_group_jumps.md`).
- Group jumps already exist for days (→ week head), weeks (→ quarter
  head), quarters (→ year head), and `walk_by` records (→ adjacent group
  head), plus authored `«`/`»` links on any note's nav line, which override
  derived stops. The governing rule from that research: **uppercase opens
  the first member of the previous/next group**, and **derive, don't
  write** — no `«`/`»` bytes are stored on Bob-owned notes.

### 1.2 Record walk lines are the template — and the churn contract

- Every record note carries one Bob-owned walk line as its **first body
  line** (`docs/records.md`, `src/native/albums/walk.rs`): canonical form
  `[[<album>/<prev>|‹ <Prev>]] · [[<album>|↑ <Album>]] · [[<next>|<Next> ›]]`
  for M ≥ 2, hub-only `[[<album>|↑ <Album>]]` for M = 1. Separators are
  `·` (U+00B7, single spaces). Labels drop `|[]#^«»`, trim edge arrows,
  escape active Markdown, fall back to humanized stem. Position and ring
  size are **never stored** — painted live by the plugin.
- Membership: immediate Markdown children of the album folder (nested
  files, non-Markdown, `.base`, and the album note excluded). Order:
  `title_order` — lowercase title, then vault-relative path, Unicode
  scalar (`src/native/albums/grouping.rs:517`). With `walk_by`, members
  group by the field's declared choice order, then title order; empty
  groups skipped; unusable values form one trailing `⚠️ Needs <field>`
  group. The ring wraps; M = 2 points both arms at each other.
- States: `current` / `stale` (rewritten in place) / `missing` (inserted
  per placement) / `damaged` (reported, never written:
  `extra_text`, `duplicate_lines`, `no_frontmatter`). A moved-but-
  recognized line is rewritten where it sits.
- Churn contract (measured, documented): one create rewrites 3 record
  files, a delete 2, a position-keeping retitle 2, a reordering retitle ≤
  5, a membership move ≤ 5, a status/field edit 0, an album retitle up to
  M. `bob albums sync` is the full repair owner; create/update/tidy stage
  only their radius; `list`/`check` report `walk` state plus
  `album_walk_stale` / `album_walk_damaged` findings.
- Lesson for this feature: the contract above is what makes stored walk
  lines acceptable. The new types need the same bounded-churn story, or
  the lines are a liability.

### 1.3 Footer and rails already know how to paint walks

- The links walker footer (`124-links-walker-footer.js`) paints `Links
  3/104`-style positions, sync states (`⟳`), empty states, group arms with
  `↺` wrap marks, and boundary hints (`]n enters X`). It consumes the
  shared `navGroups` answer plus authored links.
- The record rail (`242u-plugin-record-walk-rail-dom.js`, group row
  `242va`, model `242t`, provider route `296g-plugin-nav-groups-records.js`)
  docks inside the record card: `‹ Prev · 🍽️ Album · 3 of 104 · Next ›`
  with a location thumb, or a group row (`⏮ Head ▮▮▮■ ▭⏭`) when grouped.
  Arms follow **written** destinations; counts/groups derive live.
  Record arms refuse to create missing records (ghost, never-creatable).
- Day/period cards carry the analogous group rail via walkMode
  (`296ca-plugin-intention-card-group-rail.js`): step row plus group row.

### 1.4 Cards, cabinets, and where `bob-cli-qq` stands

- All four target types already have Property Cards: Area/Project
  (`area-and-project-cards.md`), Notebook (`notebook-card.md`), Prose
  (`prose-card.md`). None has any walk rail or footer widget today.
- `bob-cli-qq` (Property Card Cabinets, IN_PROGRESS) puts collapsible
  cabinets in one **stack at the bottom of the card** with fixed canonical
  order — content (Areas → Projects → Notebooks → Albums, or Records, or
  Outline), then config (Schema/Setup), then **Properties last** (plan
  `research:202611/property_card_cabinets/property_card_cabinets.md`,
  requirement A8). Open phases: `qq.8` (acceptance), `qq.9` (go-live),
  `qq.10` (finish epic). Crucially, the qq plan's governing decisions
  state **no bob-cli code or JSON contract changes** — a phase that finds
  it needs one stops and records `PROPOSED FOLLOW-UP`.
- Placement tension (§3, A6): the record rail sits *above* the foot
  ("the shared foot below the walk rail", `record-card.md`), while the
  request puts the new widget *below all cabinets* — and per qq A10 the
  foot itself becomes the Properties cabinet. So the request's letter
  places the widget below Properties, i.e. dead last.

### 1.5 Vault census: the rings are real and worth walking

Observed via installed `bob` JSON reports on the live vault:

| Type | Population | Sibling-group sizes (by resolved parent) |
| --- | --- | --- |
| Areas | 18 | root→6 (body, cash, dev, gtd, job, love); love→5; inbox→4; gtd→2; cash→1 |
| Projects | 102 | sase→~60 children; bob→7; job_2026→2; sase_blog→3 |
| Notebooks | 39 (13 hosts) | dev→9; lang→5; cash→3; 7 notebooks nest children of their own |
| Prose | 1 | — (feature is young) |

- Every type already resolves `parent:` to a concrete note (areas report
  carries `parent`/`children`/`title`; projects `parent`/`children`;
  notebooks `parent`/`children`/`breadcrumb`; prose frontmatter `parent:`,
  e.g. `parent: "[[sase_blog]]"` in `docs/prose.md`).
- Project display ordering needs one rule choice: projects have no single
  `title:` convention (card subtitle comes from the `^prj` line); the
  natural key is the humanized stem or the criterion text — plan-time
  decision, bounded to one helper.
- Zero existing `‹`/`›` lines on these notes (vault-root scan hits only
  year notes and `gtd_daily.md`): no authored-link conflicts to migrate.

### 1.6 Prior-research debts this proposal inherits

- Tighten the lowercase step matcher first (`^‹ | ^<(?!<)` etc.), because
  authored `<<` links would otherwise be hijacked by `[n` — flagged in the
  group-jumps final as required whatever-else-happens. This feature adds
  no `«`/`»` bytes, but its `]N` design relies on the tightened grammar.
- Never scaffold pre-adoption calendar targets from `[N` (the `ensure` +
  `adopted_years` hazard). Not directly triggered here — all sibling/`]N`
  targets are existing vault notes — but the same "navigation never
  creates" posture applies: sibling and group stops must be
  exists-or-ghost, never creatable (records precedent).

## 2. Critique: is this a good idea?

**Yes — with the adjustments in §3.** The strengths:

- *Discovers existing structure.* The parent hierarchy is Bryan's primary
  organization for all four types, but today it is only visible as
  breadcrumbs and catalogs. A walk makes it traversable: review all of
  `sase`'s 60 sub-projects, or `love`'s 5 areas, at keyboard speed.
- *Completes the `n` family.* Days, periods, and records walk; these four
  types are the conspicuous hole. One grammar (`]n` step, `]N` leap, `[[`
  repeat) across every note kind is easier to learn than a matrix.
- *Cheap mechanics.* `]n` v1 needs zero plugin changes — written lines
  walk on day one, exactly as records proved. The plugin half is paint and
  derivation, both established patterns.
- *Bounded cost.* Sibling rings inherit the record churn contract (§5):
  ≤5 files per local edit, zero for unrelated edits. Backlinks gain one
  ring per parent group — acceptable (records accepted the same).

The honest costs and risks:

- *Second source of truth, again.* Sibling order will live in N walk
  lines instead of one computed place. Staleness windows (hand renames in
  Obsidian, mobile edits, vault-sync merges) show wrong neighbors until
  the next sync — same as records, mitigated by the same `stale`/repair
  machinery, but real.
- *Prose is premature.* One prose note exists in the vault. Full
  sync+card+footer surface for prose has near-zero immediate payoff. §3 A7
  recommends building it anyway (uniformity via a shared helper makes the
  fourth type nearly free) rather than a 3-of-4 matrix that future work
  must unpick — but the plan should sequence prose last and say so.
- *Title-order churn on busy parents.* `sase`'s 60 children mean frequent
  neighbor rewrites as projects are added/retitled. Bounded (≤5 files),
  but expect `projects: sync (N notes)` commits to become routine, as
  `albums: sync` commits already are.
- *Foot-of-card real estate.* Four more rails plus a below-Properties
  widget crowd small cards. The widget must shed gracefully at narrow
  widths (record rail's `‹ 3/104 ›` collapse is the pattern).
- *The `]N`-wrap surprise.* Like the calendar rule, a group leap is not
  reversible by the opposite key (W30→W14→W27 problem). Name it in the
  hint text so it reads as designed, not broken.

What I would not do: a type-wide ring ordered by (parent, title) where
`]n` crosses parent boundaries (contradicts the request's explicit
same-parent scope and would make `]n` unpredictable on `sase`'s 60-child
ring); frontmatter `prev:`/`next:` keys (`]n` skips frontmatter —
invisible and unwalkable); or a computed-only `]n` with no stored bytes
(right long-term direction per prior research, but repeats the bigger
cross-repo change that records deliberately deferred).

## 3. Requirement adjustments (explicit — each changes the request's letter)

**A1. Resolve the contradiction: the ring is siblings, the groups are
parents.** "Only same-parent notes" and "group members by parent" cannot
both describe one flat list — a single-parent ring has exactly one group.
Adopt: `]n` scope = same-type notes sharing the same resolved parent
(wraps within siblings, never crosses parents); `]N` scope = the
parent-groups of that type, ordered alphabetically by parent title
(path tiebreak), wrapping. This satisfies both bullets and mirrors the
record model (steps walk members, leaps walk groups).

**A2. Derive `]N`; write nothing for it.** No `«`/`»` bytes on Bob-owned
notes — the group-jumps final settled this (written group arms would
break the churn contract: every new group head rewrites neighbors).
Authored `«`/`»` nav lines still override the derived answer on any note,
same as calendar/records.

**A3. Match the shipped record line grammar exactly** — titled neighbor
links `[[sib|‹ Title]]` / `[[sib|Title ›]]`, hub middle
`[[parent|↑ ParentTitle]]`, `·` separators, the same label sanitization
(drop `|[]#^«»`, trim edge arrows, escape active Markdown, humanized-stem
fallback). This overrules the prior mus record report's bare-glyph
recommendation, which the shipped records work superseded: consistency
across walk lines beats per-line churn savings, and retitle-churn is
already bounded (≤2 neighbors).

**A4. First body line, not bottom.** Prior mus recommended a bottom
footer for records; records shipped top, and top is *required* here, not
just consistent: the walker scans top-down, first match wins. Prose
bodies legitimately contain `X ›` / `‹ X`-shaped links (the group-jumps
final calls out `Read more »` in web-clipped prose); a bottom line would
lose to them. A leading walk line wins deterministically. Same
insertion rule as records: closing `---`, one blank, the line, then
blank + original body iff the body is non-blank.

**A5. Singletons get a hub-only line** (`[[parent|↑ ParentTitle]]`,
records M=1 precedent) rather than no line: the `↑` affordance is
useful, `]n` degrades to a clean "no next/prev" notice, and the rule
"every eligible note carries exactly one walk line" keeps
`check`/`sync` total.

**A6. The widget goes absolutely last — below the Properties cabinet —
and the card host enforces it.** The request's "below all cabinets"
means below Properties too (qq A10 makes the foot a cabinet). The record
rail currently sits *above* the foot: flag the inconsistency and
recommend the host append the walk widget after the cabinets stack for
every species, migrating the record rail to the same slot when cheap.
One invariant ("walk widget is always the last child of the card")
survives all future cabinets; a per-species placement will rot.

**A7. Build all four types, sequence prose last.** Prose's n=1 makes it
the lowest-value ring, but a shared (path, title, parent) ring helper
makes the marginal cost small, and a 3-of-4 support matrix (plugin
recognizers, footer routes, docs, glossary) is worse than one more
instantiation. State the sequencing explicitly so prose never blocks the
other three.

**A8. No new top-level command; each type's `sync` owns its lines.**
`bob walks` is taken (the s/w/b attention report, `docs/walks.md` — and
`n` is deliberately never in it). Per-type ownership follows the data:
each sync already holds the snapshot (parent graph, titles) needed to
compute rings, and failures stay isolated per type (records precedent).
Prose has no sync command (`adopt/format/list/outline` only), so prose
needs a small new home — recommend `bob prose sync` (noun `prose`
already exists with a clear membership rule) rather than stretching
`format`, which is a layout command.

## 4. The `]N` design (the part the request was unsure about)

Groups fall out of A1: for a note of type T with resolved parent P, the
group is "all T-notes under P"; group order is alphabetical by parent
title (path tiebreak); member order within the group is the walk order
(§5). `]N` opens the **first member of the next parent-group**;
`[N` the previous; both wrap with `↺`.

Worked example (the request's own): `bar.md` (project, parent `foo.md`,
grandparent `pig.md` area). Siblings = projects under `foo` ordered by
title; `]n` from `bar` → `baz` (next alphabetically). `]N` from `bar` →
first project under the parent that sorts after `foo` — say `qux.md`'s
first child — regardless of depth (the group key is the parent note, not
the grandparent; `qux` may itself hang under a different area).

| From | `[N` opens | `]N` opens |
| --- | --- | --- |
| `bar` (project, parent `foo`) | first project under the parent sorting before `foo` | first project under the parent sorting after `foo` |
| only child of its parent | the same head via wrap (`↺`, single-group notice) | same, other direction |
| area under root `area.md` | first area under the previous root-child group… — areas group by *their* parent too, so root's children are one group of 6; `]N` from a root-child area wraps within that group | — |
| notebook under a notebook (7 nest today) | first notebook under the adjacent parent notebook | — |

Edge semantics (all derived, none stored):

- *Single-group types.* Prose today (n=1): `]N` reports the single-group
  notice (`X has one group — ]n walks it`, records precedent
  `grouping_unavailable`/`single-group` shapes in `296g`).
- *Dangling/ambiguous/cyclic parents.* No walk line is written (finding
  codes per type, §7); `]N` falls back to authored `«`/`»` or the
  no-group notice. Never a ghost that creates — sibling/group stops are
  exists-or-explain, matching the record rule that navigation never
  creates records.
- *Parent retitles.* Group order follows live parent titles; `]N`
  answers shift without stored bytes. The only stored churn is the
  middle-link label on retitle (bounded: all children of that parent —
  accept, records precedent for album retitle).
- *Mixed parent kinds.* Notebook parents may be area/project/notebook;
  project parents area/project. Group key = parent identity, kind
  ignored. Cross-kind ordering never arises (groups compare parent
  titles, not kinds).
- *Root sentinel.* `area.md` is untyped, cardless, and gets no walk line
  (qq A11 precedent); areas directly under root form one group of 6.
- *Non-reversibility.* Document in the hint: `]N` then `[N` does not
  return (lands on adjacent group heads, not the origin) — same deliberate
  property as the calendar rule; `<C-o>` returns.

Why this is intuitive: it is the same sentence as every other uppercase
bracket key — "first member of the adjacent group" — with the only
type-appropriate group definition. It is reliable because nothing is
stored (no drift, no creation hazard, works on all ~1,196 notes on day
one for the derived half). It is beautiful because the rail shows the
same group row users already learned on records and periods.

## 5. Walk-line spec (bob-cli)

- *Membership.* Same `type:` spelling (including legacy `[[article]]`
  for prose) + same **resolved** parent target. Unresolved, ambiguous,
  self, cyclic, or kind-violating parents → no line + a finding (extend
  each type's existing `*_parent_*` finding family, e.g.
  `project_walk_orphan`-style codes — plan-time naming, following
  `album_walk_stale` / `album_walk_damaged` precedent).
- *Order.* Reuse `title_order` (lowercase title, path tiebreak) over a
  shared `(path, stem, title)` projection; one generalized helper beside
  `src/native/albums/grouping.rs:517` so the four types cannot drift.
  Display titles per type: area `title`/humanized stem (report already
  carries `title`+`titled`); project — one rule needed (recommend the
  card's subtitle source, else humanized stem); notebook title; prose
  `title:` → alias → stem (documented in `docs/prose.md`).
- *Grammar.* Byte-identical conventions to records (§3 A3). Middle link
  targets the parent note path with `↑` prefix. `«`/`»` plus the walker
  arrows are stripped from derived labels so a note titled `« Draft`
  can never pose as a group link (group-jumps lesson).
- *Placement.* First body line (§3 A4). Must be reconciled with: project
  `^prj` ("first body task line before any H2" — safe, a walk line is not
  a task line, but assert it in tests); notebook "first H1 before any H2
  or column-0 list item" (`241e-plugin-notebook-header-model.js:184` —
  safe, a walk line is neither); prose section numbering (formatter must
  see past the walk line — `bob records tidy` precedent: "tidy learns
  to see past walk lines"); area H1/title rules.
- *States.* `current` / `stale` / `missing` / `damaged`
  (`extra_text`, `duplicate_lines`, `no_frontmatter`) — copy
  `src/native/albums/walk.rs` states and the "recognized line moved by
  Bryan is rewritten where it sits" rule.
- *Writers and radius.* `bob areas|projects|notebooks sync` own their
  type's lines with the same radius discipline as
  `src/native/albums/write.rs::plan_album_walk_radius` (changed rings
  only: self + old/new neighbors, ≤5 files; unrelated edits stage
  nothing). Creation paths that add notes of these types (capture
  project/notebook routes, `notebooks create`, project creation) stage
  their ring's lines like `bob records new` does. New `bob prose sync`
  for prose (§3 A8).
- *Read surface.* `check`/`list` report per-note walk state and stale /
  damaged findings (`area_walk_stale`-family codes); human output one
  summary line per type (records precedent: `eat — 104 walk lines`).
  Additive JSON fields keep schema versions; anything breaking rides the
  daily train with a `!` mark
  (`decisions:bob-cli-releases-ride-a-daily-train`).
- *Backfill.* First sync after release backfills all four types in scoped
  commits (records precedent: one quiet backfill, then steady-state
  no-op). Expect roughly: areas ~18 lines, projects ~102, notebooks 39,
  prose 1 — small enough to land in one train.

## 6. Widget spec (bob-plugins, after qq)

- *Slot.* Card host appends the walk widget **after the cabinets stack
  and after the Properties cabinet** (§3 A6) — one host-level invariant,
  not per-species code. Collapsing the card keeps the rail (record
  precedent); narrow widths collapse to `‹ 3/104 ›` with full accessible
  names (record precedent).
- *Shape.* Sibling rail per card:
  `‹ PrevTitle · ⬆ ParentTitle · 3 of 8 · NextTitle ›` — arms follow
  written destinations, centre links the parent, count derives live from
  the cached type report (never stored). Wrap ends get `↺` + tooltip.
  Below it, only when the type has >1 parent-group, the group row:
  `⏮ PrevParentTitle ▮▮▮■ ▭ ⏭ NextParentTitle` with the landing note in
  each arm's tooltip, `↺` on the wrap — the exact record grouped-rail
  idiom (`242va`), so users learn it once.
- *Footer.* Links footer shows `Links 3/8` + group context
  (`in foo · 2/5 groups` style per `linksWalkerFooterContextText`);
  syncing/conflict/empty states reuse the existing strings.
- *Hiding.* Each card's title kit hides a recognized first-body walk
  line exactly like the record kit does (Reading + Live Preview, reveal
  on cursor/selection, Source untouched). Four small recognizer
  extensions, one shared link-run parser (the 3-link cap from
  `walk.rs:598` applies — the new lines have exactly 3 links).
- *`[n` zero-change; `]N` one new provider route.* Authored `«`/`»`
  keep working with no code (generic path in `483`). Derived sibling
  group stops come from a new `navGroups` route per type (copy the
  `296g` records route shape: model + cached report + ghost/exists
  states), or one parameterized route over (type, parent) if the author
  prefers — plan-time choice, same answer either way.
- *Keymaps.* Vault vimrc gains `[N`/`]N` on `n` alongside existing
  `[n`/`]n` (group-jumps plan wires the same for calendar/records; ship
  together or coordinate so the vimrc changes land once).

## 7. Parallel work with `bob-cli-qq` (coordination plan)

- **Parallel-safe now, no coordination:** the entire bob-cli half —
  shared ring helper, four walk-line writers, sync/check/list surface,
  `bob prose sync`, fixtures, CLI tests, `docs/` contract pages, the
  glossary term file. qq touches none of these (its plan forbids bob-cli
  changes; file overlap is zero: qq is `plugins/`, `docs` plugin pages,
  memory). Two agents can hold these checkouts simultaneously without
  stepping on each other.
- **Must wait for `qq.10` (finish epic):** the widget, the four card-rail
  mounts, the host "last child" invariant, foot/hiding changes, and any
  `docs` plugin-page edits. Reasons: (1) the widget's anchor — "below
  all cabinets" — is defined by qq's A8 stack, which `qq.8` acceptance
  is still allowed to move; (2) the same card-bottom DOM files are under
  active screenshot-gated editing (`qq.8`/`qq.10.4`); (3) the record-rail
  migration (A6) touches record-card DOM that `qq.7` just shipped.
  Options if waiting hurts: implement the plugin half behind a separate
  preview gate in disjoint fragment slots (qq uses `240w*`; the free
  slots need a plan-time check) with continuous rebases — heavier, and
  the rebase surface is exactly the files acceptance is churning. The
  recommendation is to wait; the bob-cli half is large enough to fill
  the gap.
- **Untouched throughout:** Bob Mac Capture (thin client —
  `decisions:mac-capture-is-a-thin-client` — no walk UI there),
  `Cargo.toml` versions / `CHANGELOG.md` (train-owned), release
  mechanics. bob-cli changes ride one daily train after full CI on the
  exact SHA.
- **Suggested bead shape:** one epic (or two sibling beads under the
  inevitable plan): CLI rings + sync/check/list + docs + glossary term
  first (parallel with qq), plugin rails + footer + keymaps second
  (after `qq.10` closes), with the `]N` provider route in either half
  but tested end-to-end in the second. File discovered follow-ups as
  task beads per project habit.

## 8. Glossary term (draft — "Link Walk")

> # Link Walk
> aka bracket-n walk, n walk
>
> The ring of same-kind notes joined by Bob-owned walk lines, traversed
> with `[n` / `]n` (step to the previous/next member) and `[N` / `]N`
> (leap to the first member of the previous/next group). On records the
> ring is the album's folder in title order, grouped by `walk_by`; on
> area, project, notebook, and prose notes the ring is same-type notes
> sharing one parent, grouped by parent; on days, weeks, and quarters
> the ring is the calendar, grouped by the next-higher period. Step
> links (`‹`/`›`) are stored as the note's first body line with a `↑`
> hub link to the owner; group stops (`«`/`»`) are derived live and need
> no bytes, though authored `«`/`»` nav lines override them anywhere.
> Position and size (`3 of 8`) are painted live by the card rail and the
> links footer — never written into the note. See [[walker-footer]],
> [[record-note]], [[area-note]], [[project-note]], [[notebook]],
> [[prose-note]].
>
> (New term per the request; no existing strand covers it — the roster
> has Walker Footer and the note-type terms but no walk itself. Memory
> write goes through `/sase_memory_write` at plan time.)

## 9. Open risks (for the plan to close)

- Project display-title rule (criterion vs `^prj` text vs humanized
  stem) — one decision, must match the card's title or the rail and
  card will disagree.
- Prose `parent:` allowed kinds (area/project only, or any?) — verify
  against `src/native/prose/` validators; sibling test is parent
  identity either way.
- `bob prose sync` vs a `format` flag — CLI-shape choice under
  `cli_rules.md` (noun+verb is fine; confirm no hidden `sync` exists).
- Installed `bob 0.6.0` vs workspace source drift for census numbers —
  recount at plan time from a workspace build.
- Fragment-slot and vimrc coordination with the calendar/group-jumps
  line of work if it lands first — whoever lands second rebases keymaps
  and the `navGroups` registry.

## 10. Recommended solution

1. **Settle A1–A8** with Bryan (they are individually small, but A1/A4/A6
   change observable behavior — confirm before planning).
2. **bob-cli first (parallel with qq, starting now):** generalize the
   ring projection from `src/native/albums/` into a shared helper over
   (path, title, parent); add walk-line plan/apply/verify per type;
   wire `areas|projects|notebooks sync` + new `bob prose sync`;
   extend `check`/`list` with walk states and `*_walk_stale/damaged`
   findings; cover churn bounds (create 3 / delete 2 / retitle ≤5 /
   reparent ≤5), placement vs `^prj`/H1/sections, and damaged states in
   CLI tests; write `docs/` contract pages (one per type or one walks
   page — docs-memory route) and the Link Walk strand; ride the train.
3. **bob-plugins after `qq.10`:** host "walk widget is last child"
   invariant; sibling rail + group row on the four cards; title-kit
   hiding for recognized walk lines; `navGroups` sibling-group route;
   footer already handles the rest; vimrc `[N`/`]N`; e2e in the scratch
   vault runners (never the live vault) + screenshot review.
4. **Backfill + announce:** first post-release syncs backfill (~160
   lines total, scoped commits); `bob plugins sync`; verify `]n`/`]N`,
   rails, and footer on one ring per type (love's 5 areas, sase's 60
   projects, dev's 9 notebooks, the lone prose note's hub line).
5. **Explicit non-goals:** no `«`/`»` bytes on Bob-owned notes; no
   creation from `]N` (exists-or-explain); no Mac Capture UI; no
   frontmatter prev/next keys; no cross-parent `]n`.


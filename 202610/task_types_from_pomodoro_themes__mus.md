# Task Types From Pomodoro Themes — Research (`__mus`)

Swarm researcher report. Independent conclusions; no peer reports consulted.

**Request in one line:** rename "pomodoro theme" to "task type", give every task a
(configurable, default `CHORE`) type, keep task types and ledger pomodoros
bidirectionally consistent across the Task Card / `Ctrl+Shift+M` / bob-mac-capture,
allow explicit exempt types like `[type::PLAN]`, and render `#task` as `#<TYPE>` in
Obsidian.

**Verdict up front:** the observation is real — a single non-exempt pomodoro component
already behaves like a task type — but the proposal as written overreaches in three
places and underestimates one deeply embedded dependency. I recommend a narrower,
phased version: (1) adopt "task type" as the **user-facing display name** for the
single-type subset while keeping `theme` as the storage/ledger term; (2) implement an
**effective-type model** (explicit → inherited → configured default) with no mass
stamping of task lines; (3) generalize the existing deliberate-write rule to all
ledger↔task writers instead of building two new auto-sync paths; (4) ship rendering
as a **render-time alias over stored `#task`**, never a stored-tag change. Details and
justifications below.

---

## 1. What exists today (ground truth)

All claims below were read in this checkout, not inferred from the request text.

### 1.1 Vocabulary and identity

- A **theme** is one `+`-separated component of a named ledger entry's ` — NAME` tail
  (`docs/pomodoro-themes.md` PT1). `— BOB + DECKS` is one name with two themes.
- Split with `split_components`; identity key is `normalize_component` (whitespace
  collapsed, lowercased); display spelling is most-recently-authored
  (`src/native/plan_budget/`, `src/native/pomodoro_themes/scan.rs`,
  `src/native/config/themes.rs`).
- Naming in code: `pomodoro_themes` (Rust), `bob-pomo-theme-*` (CSS),
  `PomodoroTheme*` (Swift), `api.themes` (JS). User words: **theme / Recent / Hide /
  Unhide / Pin color / Rename theme** (PT1).
- Glossary (`sase memory read glossary:theme`): "Pomodoro Theme … One `+`-separated
  component … `plan.max_themes` counts distinct non-exempt components … catalog is
  derived from canonical daily notes plus `.bob/themes/<host>.jsonl`."
- A theme is explicitly **not** a Pomodoro home, an Obsidian appearance theme, or
  `(unnamed)`.

Why this matters for the rename: `theme` is a load-bearing identifier across four
systems (Rust, Obsidian `api.themes` v1, Swift `PomodoroTheme`, CLI/JSON
`ThemeRef`), plus CSS classes, docs URLs (`docs/pomodoro-themes.md`,
`https://bobs-org.github.io/pomodoro-themes/`), config keys (`themes:`), and the
journal event names (`theme.hide/unhide/color/rename`). A rename is a cross-repo
contract migration, not a docs edit.

### 1.2 Catalog, cache, journal, hue

- **Source:** every canonical daily note `YYYY/YYYYMMDD.md` only — not `_templates/`,
  `done/`, `_conflicts/`, `*_done.md` — column-0 `## Pomodoros` entries, open and
  closed, through `capture_pomodoros::scan` (PT2).
- **Cache** is machine-local and disposable (`themes/catalog-v1.json`,
  `known-keys-v1.json`); today's note always read live (PT3).
- **Journal** `.bob/themes/<host>.jsonl`, one append-only file per host, `host` is the
  vault-sync label; events `theme.hide/unhide/color/rename`, `v: 1`; fold by
  `(ts, host, path, line)` last-writer-wins; bob is the only writer (PT4; decision
  `decisions:theme-prefs-live-in-per-host-journal`).
- **Hue priority** (PT5; decision `decisions:theme-hue-is-config-pin-exempt-area-hash`):
  1. configured `themes:` color (`hue_source: config`),
  2. journal pin (`pin`),
  3. normalized `plan.exempt` mute (`exempt`, PLAN default),
  4. outside configured vocabulary mute (`unconfigured`),
  5. matching top-level area stem (`area`),
  6. `fnv1a32(key) % 8` (`hash`).
  Config beats pin beats mutes beats implicit sources. Palette is 8 slots; colors are
  stable, not unique.
- **Visual language** (PT6): names wear a tint (pill, 16% light / 24% dark), places
  wear a dot. Muted exempt pill (gray tint, e.g. PLAN), unconfigured pill (1px dashed
  warning outline + `◌` in CLI), composites get one pill per component, CLI swatches
  (`■` / `□` exempt / `◌` unconfigured), typing stays neutral until committed.

### 1.3 `themes:` vocabulary, exempt, strict, duplicates

- `themes:` block in `config.yml` declares the vocabulary + per-theme palette color or
  `auto`/null (PT12). Missing/null/`{}` = "no configured themes" = today's behavior.
  Validation is strict but non-fatal: a failed block is dropped wholesale (behaves as
  unconfigured) and surfaced as `theme_not_configured` warnings, never a block.
- Bryan's live config (`~/.config/bob/config.yml`): `BUILD/CHORE/FIX/MEET/PLAN/READ/WRITE`
  with `plan.exempt: [PLAN]`, `max_themes: 3`, `max_links: 13`,
  `inventory_labels: [LATER, MISC, NEW FEATURES]`.
- **Duplicates:** `docs/plan.md` defines lint `duplicate_open_pomodoro_name` — "the same
  non-exempt component is on two open entries" — and capture's `#name` targeting
  resolves to the **first open match** (document order, else first slug-prefix match).
  A typed `#` with empty name never falls back. So duplicate-type pomodoros
  (the "one project, many same-type sessions, then merge" use case) are currently a
  **linted edge**, not a supported shape. Budget counting is already
  duplicate-safe (`max_themes` counts *distinct* non-exempt components), which is
  convenient for the project's use case.
- `plan.strict: false` refuses `#NAME` captures past `max_themes`; exempt entries don't
  count.

### 1.4 The task-side half already exists: `[theme::]` + suggest + write rule

This is the most important finding for scoping: **half the proposal is already built.**

- **Field** (`src/native/task_theme.rs`, PT13): a task line carries none, one set field
  (`[theme:: X]` / `(theme:: X)`), or repair state (`duplicate` / `invalid` → falls
  through to inheritance, replaced by next eligible writer). Closed tasks keep the
  field as history. Placement: `set_task_theme` strips all theme fields + one adjacent
  space, inserts ` [theme:: NAME]` before the maximal trailing metadata run (inline
  fields, tags, `^id`); byte-preserving otherwise (indentation, blockquotes, CRLF).
- **Suggestion precedence** (`bob themes suggest`, PT13): (1) task field
  (`this task`), (2) reading task via `plan.reading_theme` default `READ`
  (`reading task`), (3) area/project note `theme:` frontmatter default walking the
  residence chain (`from <stem>`), else none. `off` disables reading/note steps.
  Serialized as `theme` (a `ThemeRef`) + `source` + `label` + `inherited`.
- **The write rule** (`plan_theme_change`, PT13 "write rule and never-writers"): a
  deliberate destination choice D with shown suggestion S —
  1. not deliberate → no change;
  2. D unnamed / all-exempt / not exactly one non-exempt component → no change
     (`PLAN + BUILD` selects BUILD; `BUILD + FIX` writes nothing);
  3. no suggestion shown → no change;
  4. chosen == inherited → clear the field;
  5. else set catalog-spelled X.
  Deliberate capture = explicit `#NAME` / `=name`; picker = changed committed row,
  nonempty query, or Shift+Enter; untouched preselection is never deliberate.
- **Writers covered today:** explicit-`#NAME` new-task captures, whole-item
  existing-task links (`@route:id#NAME`, `^route:id#NAME`, `@route+id#NAME` Ensure
  Next, `=name` shorthand). JSON reports additive `task_theme: {action, theme,
  previous, inherited}`. **Never-writers:** close, roll, `^^`, move, rollover,
  reconcile, successor placement, `ref today`. Capture completion already emits
  `theme_suggestion` + one `suggested: true` row + `fallback`
  (`unknown_theme|creation_blocked|strict_cap`); `ref today` reuses it.
- **Preservation:** move, archive, reconcile, complete/cancel, freshness stamping keep
  an authored theme field byte-identical (`docs/pomodoro-themes.md` PT13
  "Preservation").

So the codebase already has the exact guard the proposal needs ("only write the type
on deliberate single-type choices; clear on inherit; never on ambient gestures").
The work is to **extend the writer set**, not invent the rule.

### 1.5 Ledger-side move (`Ctrl+Shift+M` on a Task Link) vs note-side move

Two different "moves" are being conflated in the request; they live in different code:

- `N<Ctrl+Shift+M>` on a **ledger Task Link** (Obsidian nav-hotkeys,
  `plan_link_relocation` in `src/native/capture_task_toggle/relocation.rs`): moves the
  dedicated link subtree between open pomodoros, creating the canonical named future
  entry when the target doesn't exist. Never synthesizes links, never touches closed
  history. Decision `decisions:task-move-never-advances-the-walk` governs walk
  behavior, not field writes.
- `bob task move` / `Ctrl+Shift+M` on a **source-note task** (`src/native/task_move/`):
  moves task blocks between area/project notes, repairs block links + `[id::]` /
  `[dependsOn::]` identities. Explicitly "does not … change lanes, promote
  prerequisites, consume ledger links, or run reconcile."

Neither writes `[theme::]` today. The proposal's "moving a task link to a different
pomodoro updates `type`" is a new write on the first path.

### 1.6 Mac capture contract

`docs/reference/mac-capture/protocol.md`: the Mac is a thin client
(decision `decisions:mac-capture-is-a-thin-client`) — it renders `themes` refs, swatches,
`plan_budget` (`added_theme_refs`, cap warnings, `plan_themes_after/cap`), and
`pomodoro_name`/`task_toggle_pomodoro_name` spans that bob emits; it never computes
destinations itself. "Always use the suggested task type by default" therefore means:
**bob must mark one row preselected** (the existing `suggested: true` /
`suggested create` machinery) and the Mac honors it — no Mac-side heuristics.

### 1.7 Rendering: `#task` is structural, not decorative

`docs/task-tag-marks.md` + `bob-ledger-tools` row: `#task` is the Tasks plugin
`globalFilter`, accent-colored hash mark, with exact-token matching
(case-sensitive `#task`; `#tasks`/`#task/sub`/`#Task` never match), quote-aware
ranges, copy/screen-reader behavior, and the `#task #ref` book and `#task #gtd
#pre/#post` sunrise/flag identity marks built on top of the `#task` anchor.
Vault counts (~2026-10-08): **3,406 `#task` lines**, 2,934 closed; ~656 carry a second
tag (usually `#prj`). Task Card/"notices" already strip `#task` in some views.
Changing the stored tag (or even its rendered text without care) touches the global
filter, every saved Tasks/Dataview query, marks, accessible names, and thenade
copy/paste contract.

### 1.8 The `type` name is already taken (twice)

1. **Note frontmatter `type:`** — `[[area]]` / `[[project]]` / `[[ref]]` note kinds
   (`docs/reference/glossary.md`, `docs/reference/vault-format.md`). A task inline
   field `[type:: X]` is a different namespace (task line vs note frontmatter), so no
   parse collision — but Dataview already conflates: PT13 documents that
   `task.theme` "can conflate frontmatter note defaults with task fields." Renaming the
   task field to `type` makes that conflation **worse** (`task.type` will read even
   more ambiguous), so docs must steer users to `bob themes suggest` (or its renamed
   equivalent) as the authority.
2. **Code-level `type`** — `status_name`/`IN_PROGRESS type`, relation `type`,
   `task.type` in Dataview. A codebase-wide rename of `theme` → `type` will collide
   constantly in search/replace and review. A display-name change avoids this entirely.

---

## 2. Critique of the plan, bullet by bullet

### 2.1 "Rename the glossary entry pomodoro theme → task type"

**Partially agree, with a structural objection.** The mental model is right for the
*singleton* case: one task, one pomodoro, one non-exempt component — that component
walks, talks, and budgets like an issue-tracker type. But "theme" and "task type" are
not the same concept at every cardinality:

| Shape | Theme model | Type model |
|---|---|---|
| `— BUILD` | one theme | one type ✅ match |
| `— BOB + DECKS` | one name, two themes | ??? two types on one session — trackers don't do this |
| `— PLAN` (exempt) | muted, uncounted session | a type that isn't a type? |
| Ad-hoc `— SASE V18` | a project-flavored session name | a "type" with N=1 member |
| `(unnamed)` | not a theme | not a type — consistent |

The composite-name case (`+`) has no counterpart in issue-tracker types and is load-bearing
for Bryan (project sessions, `BOB + DECKS`). Forcing it into "type" language makes
composites unsayable. Likewise exempt/inventory/unconfigured are **ledger-budget**
properties of session names, not task classifications — `PLAN` as "a muted type" is
coherent only if you keep the ledger story alongside.

There is also a real cost ledger: `ThemeRef` JSON, `api.themes` v1, Swift
`PomodoroTheme*`, CSS `bob-pomo-theme-*`, `themes:` config, journal event names, PT1–PT13
docs + site URLs, `bob themes *` CLI surface, `plan.max_themes`, `theme_not_configured`
codes. A hard rename is a 4-surface (Rust/JS/Swift/CLI) additive-schema migration with
deprecation windows — large blast radius for a primarily linguistic win.

**Adjustment (justified):** adopt **"task type" as the user-facing display name for the
single-type subset**, keep `theme` as the storage/ledger term. Concretely: glossary
entry becomes "Task Type (theme)"; docs introduce "a task type is a pomodoro theme used
as a task's type — exactly one non-exempt component"; code/JSON keep `theme` keys and
add `type` **aliases** (accept `[type::]` wherever `[theme::]` is accepted; emit both
for one version, then prefer `type` in human output). This gets 90% of the linguistic
win (users say "type", chips say types, menus say types) at ~10% of the migration cost,
and composites stay sayable ("a session with two types" is honestly flagged as the
multi-type edge rather than normalized).

### 2.2 Motivation: ad-hoc themes, research themes, projects-as-types

**Agree with the carve-outs, and they survive the narrower rename too.** Ad-hoc names
with the `theme_not_configured` warning (PT12) and research-recommended defaults
(`theme:` note defaults, `plan.reading_theme`) are orthogonal to what the field is
called. The project pattern (all tasks of a project in same-type sessions, then merge)
works identically under "type" language — arguably better, since "merge these
same-type sessions" reads naturally.

**Adjustment:** keep "duplicate same-type pomodoros" out of scope as proposed, but
don't leave it unshaped. The current behavior (lint + first-open-match targeting)
already fails safe. The design should name the future: explicit targeting via literal
`#"NAME"` (already exists, PT8) and line-anchored moves, with the lint retained. One
new rule to add now: **budget counts stay distinct-component** (already true), so
duplicates never inflate `max_themes` — state this explicitly so the projects-as-types
pattern isn't accidentally penalized later.

### 2.3 "Give every task a type by default (configurable, mine `CHORE`)"

**Disagree with the mechanism; agree with the goal.** The goal (no untyped tasks in
practice; suggestions always resolve) is good. Stamping a `[type:: CHORE]` (or
`[theme:: CHORE]`) field onto every task line is the wrong mechanism:

- **Write churn at scale:** thousands of task lines gain a field; every capture,
  inbox-route, and backfill touches them; diffs and sync payloads bloat; blame rots.
- **Fights the inheritance model:** PT13's precedence (task → reading → note default
  → none) already resolves a suggestion for most tasks *without writing*. A
  configured default belongs at the **bottom of that precedence chain** ("effective
  type"), not materialized on the line.
- **Breaks repair semantics:** today, absent field = clean; duplicate/invalid =
  repair. Mass-stamping converts "no opinion" into "explicit CHORE," destroying the
  signal that lets future writers distinguish deliberate from default.
- **Backfill hazard:** existing closed/history tasks must be excluded (PT13: closed
  tasks keep fields as history, no suggestion) — a backfill that stamps open tasks
  only still rewrites a large fraction of the vault in one commit.

**Adjustment (justified):** add `plan.default_type` (or `task_types.default`, name TBD —
  see §4; default `CHORE` for Bryan via chezmoi) as the **last-resort effective type**
  used by suggestion, preselect, and rendering, **never auto-written** to task lines.
  The field is written only on (a) explicit user choice (Task Card type row, deliberate
  `#NAME` capture — already shipped), or (b) divergence repair (see §2.4). Effective
  type = explicit field → inherited suggestion → configured default → none. `bob
  themes suggest` gains one line (`default CHORE` source) and every consumer inherits
  it. This delivers "every task has a type" as a *read-time truth* with zero vault
  churn.

### 2.4 Bidirectional consistency (Card moves links; link moves update `type`)

**Agree with the invariant; disagree with making both directions automatic and silent.**

The invariant — "a task's effective type always agrees with the single-type sessions
it is linked under today" — is the right one and is genuinely valuable (it kills the
current drift where a `WRITE` task sits under `BUILD`). But silent bulk writes in both
directions compound:

- **Card type edit → move all today's links to matching sessions:** a task linked under
  three sessions today (common during triage) gets yanked into one session, destroying
  the user's ledger arrangement. Creating a new same-type session per edit multiplies
  entries and fights `max_themes`/strict caps. The "existing same-type session else
  create" rule also needs a tiebreak (first match? running? most recent?) that doesn't
  exist.
- **Link move → rewrite `type`:** `Ctrl+Shift+M` relocation and bulk `x<N>` closes move
  links for mechanical reasons (parking, balancing the day), not semantic ones. Stamping
  the task's type on every mechanical move makes the field meaningless — it records
  where the link happened to land, not what the work is.

**Adjustment (justified):** generalize the *existing* deliberate-write rule to every
writer instead of adding two auto-syncs:

- **Ledger→task** (link placed into a *deliberately chosen, single-non-exempt,
  shown-suggestion* destination): write/clear the field — i.e. extend
  `plan_theme_change` to `Ctrl+Shift+M` relocation, Mac drops, and Task Card "link
  under…" flows, with the same guards (deliberate, single type, suggestion shown,
  `PLAN+BUILD`→BUILD, `BUILD+FIX`→no-op). Ambient/mechanical placements (close
  continuations, `Ensure Next` implicit, recovery, reconcile, rollover) stay
  never-writers. This is a small, well-tested generalization of shipped code.
- **Task→ledger** (type edited on the Card): do **not** move links automatically.
  Instead offer an explicit, previewed follow-up — "also move today's N links to
  <TYPE sessions>? [create if needed]" — reusing the relocation planner with a dry-run
  preview, one undo unit, and cap/lint reporting. Opt-in per edit; one preference to
  default it on later if Bryan likes it. This preserves the invariant on demand without
  ever surprising.
- **Tiebreaks to specify now:** prefer the running timed entry, else first exact open
  entry in ledger order (matches existing `#name` resolution); only create when no open
  match *and* caps permit, else report `strict_cap`/`creation_blocked` (existing
  fallback codes). Multi-type destinations (`BUILD + FIX`) never write the field —
  report `multi_type_destination` and leave the line alone.

### 2.5 Mac capture: "always use the suggested type by default"

**Agree, with a protocol-shape caveat.** "Current/next pomodoro" is today's implicit
default; the proposal replaces it with "the suggested-type session." The preselect
machinery already exists (`theme_suggestion`, `suggested: true` row, suggested-create
row, fallbacks). So: **when the Mac draft has no explicit `#NAME`, bob's
`capture-pomodoro-name`/`capture-complete` response should rank the suggested-type
session (or suggested-create row) first, and the Mac selects it by default** — same
vectors, no Mac heuristics (thin-client decision preserved). Keep the current/next
entry as the visible fallback with its reason (`unknown_theme | creation_blocked |
strict_cap | already_queued`), because caps, missing sections, and multi-open-timed
states still force it. And the `#NAME` rule stays: explicit `#NAME` writes/clears the
field per the generalized deliberate rule (§2.4) — that *is* the "`#type` suffix
syntax" (there is no separate `#type:` syntax in the grammar; the `#NAME` selector is
the type selector when the name is a single type — worth stating in docs to avoid a
phantom second syntax).

### 2.6 "Explicitly set exempt types (`[type::PLAN]` mid-day)"

**Agree — this is the cheapest item and mostly a docs/validation change.** Today an
explicit `[theme:: PLAN]` on a task is legal storage; the friction is conceptual
("exempt" sounds like "not a theme") plus rename-blocker wiring (OLD in
`plan.exempt` blocks `themes rename` until config changes). Under the type model this
reads naturally: PLAN *is* a type, one that ledger-budget exempts. Changes: (a) accept
and preserve explicit exempt fields everywhere (already true — assert it in tests);
(b) exempt-keyed tasks still suggest/clear per the write rule (`PLAN+BUILD` selects
BUILD; choosing the inherited PLAN clears); (c) hue stays muted (`exempt`), pills
stay neutral; (d) `themes rename` keeps its `config_reference` guard but with
type-flavored copy. No new config needed — `plan.exempt` already *is* the exempt-type
list; if Bryan later wants per-type exemption separate from ledger exemption, that is
a follow-up, not this change.

### 2.7 "`#task` → `#<TYPE>`, colored"

**Disagree with changing the stored tag; agree with the visual goal, via render-time
alias.** Reasons, in severity order:

1. **`#task` is the Tasks global filter.** Stored `#BUILD` breaks the query engine's
   root predicate vault-wide (3,406 lines, saved queries, Dataview, filters). Migration
   = rewriting every task line + every query + third-party assumptions, with no atomic
   path.
2. **Marks are anchored on `#task`.** The teal hash, `#task #ref` book, `#task #gtd
   #pre/#post` sunrise/flag, accessible names, copy semantics, and the "cursor into the
   glyph reveals `#task`" contract all key on the exact token. A stored change
   re-opens all of them; a *rendered* change reuses them.
3. **Color-per-type at task-line density is noisy.** Ledger pills work because sessions
   are few and large. Hundreds of `#BUILD` pills in a READY list will shimmer — the
   proposal's own "beautiful" bar demands restraint: keep the hash glyph quiet (teal
   family), put the *type text* in the pill at reduced saturation, and never color the
   running text.
4. **No-type and multi-source states need a design**, not a default: explicit vs
   inherited vs default-CHORE vs repair vs exempt must read differently (or the
   display lies about provenance).

**Adjustment (justified):** keep stored text exactly `#task`; in Live Preview /
reading view / Tasks rows, **render the tag's text as `#<EFFECTIVE-TYPE>`** with the
type's hue pill (muted gray for exempt, dashed `◌` treatment for unconfigured,
`#task` fallback when no effective type), preserving the underlying `#task` bytes for
copy, queries, and screen readers (accessible label: `#task · type BUILD`). Add one
session toggle (`Toggle task type marks`, default on, independent of pomodoro-color
toggle, mirroring the existing `toggle-task-theme-marks` pattern) and keep
`NO_COLOR`/narrow fallback (name text carries meaning). This is strictly an extension
of the shipped `[theme::]`-pill rendering (PT6/ledger-tools row) to the *effective*
type — same pill CSS, same hue contract, same toggle shape.

---

## 3. Cross-cutting issues the proposal doesn't name

1. **Composite sessions vs single types (§2.1).** Any "type" UI must handle `BUILD +
   FIX` destinations: no field write, `multi_type_destination` notice, and a pill row
   that shows both components (already the composite-pill rule). Don't let the type
   model pretend composites away.
2. **`task.type` Dataview conflation gets worse.** Docs must bless `bob themes suggest`
   (renamed alias `bob task-type suggest`, keep old name) as the authority and warn
   that `task.type` mixes frontmatter defaults with line fields.
3. **Exempt/inventory/unconfigured are ledger properties.** `inventory_labels`
   (LATER/MISC/NEW FEATURES) are "storage, not themes" — under types they are
   "storage, not types." Keep the carve-outs named; don't re-litigate them.
4. **Stats `theme` dimension + Day strip + tmux.** All consume `ThemeRef`s; they need
   no change under the alias strategy (a "type" filter is a display alias over the
   theme dimension). Name this non-goal explicitly to bound the work.
5. **Rename/split coverage.** `themes rename` already rewrites tails + note defaults +
   task fields in one commit; `split` deliberately leaves fields alone with a
   `split_leaves_task_themes` warning. Under dual `[theme::]`/`[type::]` acceptance,
   both commands must match both spellings (one-line predicate change + vectors).
6. **Freshness/stamps interplay.** Theme edits never affect freshness eligibility
   (PT13) — preserve that; type is classification, not activity. `plan_theme_change`'s
   no-op-when-exact rule also prevents stamp churn — keep it.
7. **Performance.** Suggestion already rides capture completion's cached path (PT3/PT7
   budgets: +5ms p95). Effective-type rendering in task lists must reuse the same
   cached catalog + note-default walk with the 16-note/cycle caps, not re-scan per
   row. State the budget in the plan.

---

## 4. Recommended solution

### 4.1 Shape of the change (narrowed)

- **A. Language (display alias, not storage rename).** Glossary: "Task Type — the
  user-facing name for a pomodoro theme used as a task's type (exactly one non-exempt
  component). Storage, JSON, config, CSS, and Swift keep `theme` keys; human surfaces
  say *type*." Accept `[type:: X]` everywhere `[theme:: X]` is accepted (dual-read,
  one canonicalizer); write `type` spelling on new edits when the line has no theme
  field, else preserve the line's existing spelling. `bob themes suggest` gains alias
  `bob task-type suggest`. Config keeps `themes:` / `plan.exempt`; add only
  `plan.default_type` (default null = today's "none"; Bryan sets `CHORE` in chezmoi).
- **B. Effective-type model (no mass stamping).** `effective_type(task) = explicit field
  → inherited suggestion (reading/note-default) → plan.default_type → none`. Used by
  suggestion output, preselect ranking, and rendering. Nothing backfills the vault.
- **C. Generalized deliberate-write rule.** Extend `plan_theme_change` (renamed
  internally `plan_type_change`, same semantics) to: Task Card type edits (field
  write only, links offered not moved), `Ctrl+Shift+M` ledger relocation into a
  deliberate single-type destination, Mac drops, `@route+id#NAME`/`=name` (already
  covered). All ambient writers stay never-writers. New fallback code
  `multi_type_destination` alongside existing `unknown_theme/creation_blocked/strict_cap`.
- **D. Card follow-up offer (opt-in link moves).** After a Card type change, one
  previewed offer: "move today's N links to <TYPE> sessions?" with create-if-allowed,
  cap/lint reporting, single undo. No silent moves.
- **E. Mac default = suggested session.** Rank suggested-type session/create row first
  on empty query; Mac selects it; current/next remains the labeled fallback. No
  Mac-side heuristics; additive JSON only.
- **F. Exempt types explicit.** Assert accept/preserve/render for explicit exempt
  fields; keep `plan.exempt` as the list; muted visuals unchanged.
- **G. Render-time `#<TYPE>` alias.** Stored `#task` untouched; Live Preview/reading/Tasks
  rows render effective-type text in the type's pill with provenance styling
  (explicit solid / inherited slightly muted / default-CHORE with dotted underline or
  `· default` tooltip / repair falls back to `#task` + existing repair styling);
  accessible label keeps `#task · type X`; session toggle; `NO_COLOR` falls back to
  text only.

### 4.2 Phased delivery

- **Phase 1 — model + alias (Rust only, no UI moves).** Dual `[type::]` read, effective
  type + `plan.default_type`, `suggest` alias + `default` source, rename/split match
  both spellings, vectors. No rendering, no new writers. Verifiable headlessly.
- **Phase 2 — writers.** Generalize the deliberate rule to relocation + Card field
  edits; Card follow-up offer with dry-run preview; capture JSON gains
  `multi_type_destination` where applicable. Mac consumes existing preselect (Mac
  change is selection-default only).
- **Phase 3 — rendering.** Effective-type pill alias for `#task` in ledger-tools with
  toggle + a11y + `NO_COLOR`; Stats/Day-strip/tmux explicitly unchanged (display
  aliases only if later wanted).
- **Phase 4 (optional, later) — storage rename.** Only if Phase 1–3 prove the model:
  canonicalize stored `[theme::]` → `[type::]` via a previewed one-commit migration
  modeled on `themes rename`, with dual-read retained for one release. Never rename
  JSON keys without a version bump.

### 4.3 Config (chezmoi, Bryan's ask)

```yaml
plan:
  default_type: CHORE   # last-resort effective type; never auto-written to lines
```

Keep `themes:` (vocabulary+colors) and `plan.exempt: [PLAN]` as-is. No new
exempt-types list in this change (explicit `[type::PLAN]` already works; revisit only
if ledger-exemption and type-exemption need to diverge).

### 4.4 Acceptance bar (what "reliable and beautiful" means here)

- No silent ledger rearrangement: every link move is previewed or explicitly chosen.
- No vault churn: enabling `default_type` writes zero lines by itself
  (assert byte-identical vault in tests).
- No broken queries: stored `#task` bytes unchanged; Tasks global filter green.
- Provenance honesty: a reader can always tell explicit / inherited / default / repair
  apart (pill treatment + tooltip + `suggest` output).
- Caps respected: strict/duplicate/multi-type paths report existing (+1 new) codes,
  never force-create.
- Precedent reuse: hue (PT5), pills (PT6), menus (PT7), write rule (PT13), journal
  (PT4) — no parallel inventions.

### 4.5 Open questions for Bryan (answering these unblocks the plan)

1. `plan.default_type` name/placement OK, or do you want `task_types.default`?
2. Card follow-up default: offer-every-time vs a "always move links" preference?
3. Rendering provenance: is dotted/distinct styling for default-CHORE acceptable, or
   should default types render identically to explicit ones?
4. Keep `bob themes` CLI name (alias `bob task-type`), or do you want the primary
   renamed now?

---

## 5. Sources checked

- `docs/pomodoro-themes.md` PT1–PT13 (full read); `docs/plan.md` (budget, lints
  incl. `duplicate_open_pomodoro_name`, config); `docs/capture.md` (§13 link/Ensure
  Next/`#NAME` semantics, `task_theme` JSON); `docs/task-tag-marks.md` (`#task`
  token/mark contract); `docs/task-move.md` (note-side move scope).
- `src/native/task_theme.rs` (`plan_theme_change`, placement/preservation);
  `src/native/pomodoro_themes/*` (catalog/journal/hue/rank/suggest/preselect);
  `src/native/plan_budget/*` (budget/exempt/strict); `src/native/config/plan.rs`,
  `src/native/config/themes.rs` (exempt/vocab/`reading_theme`);
  `src/native/capture_task_toggle/relocation.rs` (ledger link moves);
  `src/native/task_move/` (note moves never touch ledger);
  `docs/reference/mac-capture/protocol.md` (thin-client preselect contract);
  `docs/reference/plugins/{task-card,bob-navigation-hotkeys,bob-ledger-tools}.md`
  (Card stages, `Ctrl+Shift+M`, theme pills/marks/toggles).
- Memory: `glossary:theme`; `decisions:theme-hue-is-config-pin-exempt-area-hash`,
  `decisions:theme-prefs-live-in-per-host-journal`, plus sticky-lanes / ledger-Today /
  freshness context. Live `~/.config/bob/config.yml` (`themes:`,
  `plan.exempt: [PLAN]`) to ground the `CHORE`-default ask.
- Deliberately not consulted: peer swarm reports; other linked repos beyond their
  bob-cli-side contracts (Mac/plugins surface only through `docs/reference/`).

## 6. Bottom line

Do the reframe, not the rename: **"task type" as the user-facing name for the
single-type subset, effective-type model with a configured default, one generalized
deliberate-write rule, opt-in link moves, and render-time `#<TYPE>` over stored
`#task`.** It delivers every motivation in the request (clearer language, typed
defaults, Card/capture/Mac consistency, explicit PLAN, beautiful colored types) while
avoiding mass rewrites, silent ledger moves, and a vault-wide tag migration. The one
adjustment I'd insist on if forced to pick: **never auto-stamp a default type onto
task lines** — compute it, don't store it.

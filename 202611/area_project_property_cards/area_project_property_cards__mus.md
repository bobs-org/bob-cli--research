# Property cards for area and project notes — research report

Researcher: mus · 2026-11-22
Question: once the `bob-cli-pf` epic lands, what should property cards on
area notes and project notes look like, and what should the `=+` schema
editor support?

Related work deliberately **not** opened (peer reports in this swarm):
`property_card_title_block__cdx.md`, `__cld.md`, `__gem.md`, `__grk.md`
in `202611/property_card_title_block/`. Filenames were checked only to
avoid overwriting output.

## TL;DR

Yes, put property cards on area and project notes — but ship the **small
title-block card first**, not an operations dashboard. Areas and projects
are the only major vault note kinds with no card, and their frontmatter is
today edited as raw YAML with silent mis-typings (`offclock_types`,
`ready_cap`, `task_type`, `parent`). A card fixes discoverability and
gives the `=+` editor a stable mount. The risk is bloat: both note kinds
already own four to five machine catalogs plus `## Tasks`, and their most
important state (`status`, counts, Blocked) is **derived at read time**,
not stored. A card that duplicates catalogs or pretends derived state is
editable will teach the wrong mental model.

Recommended v1:

1. **Title-block card only.** Kicker `AREA` / `PROJECT`, species tile,
   owned H1 title, parent breadcrumb, one-line subtitle (`summary:` on
   areas, cleaned `^prj` criterion on projects), one quiet meta row of
   already-computed signals, then the pf foot row (`▸ Properties · N` +
   `created` stamp). No catalog moves, no stats charts, no task lists in
   the card.
2. **No new `==` species editor.** Reuse the generic `=+` property editor
   from `bob-cli-pf` with an extended role table. Area/project keys need
   only 3–4 bespoke stages (parent picker, clock/type inheritance
   previews, cap/refresh numbers); everything else is the generic Text /
   Number / Checkbox / List / Link / Date&time / Tags / YAML kit.
3. **Lock what bob derives.** `type`, `status` (project), managed
   `*_digest`/`*_drafted`/`zorg_*` keys are read-only in `=+` with a
   one-line teaching reason and a `y` (YAML) or `=` (card) escape. `parent`
   edits preview affected catalogs and refuse cycles.
4. Defer the dashboard (Today lists, Ready counts, walk shortcuts, project
   creation wizard, vault-wide type rename) to a later phase with usage
   evidence.

The rest of this report inventories the exact keys, sketches the card,
specifies the `=+` rows, critiques the idea, and lists the requirement
adjustments this implies for `bob-cli-pf` follow-ups.

## 1. What area and project notes actually store

### 1.1 Identity and hierarchy

| Key | Area | Project | Notes |
| --- | --- | --- | --- |
| `type` | `"[[area]]"` | `"[[project]]"` | Identity. Locked in `=+` v1. Bare `[[area]]` also accepted. |
| `parent` | `"[[area]]"` | `"[[area]]"` or `"[[project]]"` | Single scalar wikilink. The tree edge. Cycle/16-hop guarded. |
| `template` | rarely | `"[[new_project]]"` | Capture template marker. Seldom edited; plain Link stage. |
| `title` | — | — | No frontmatter title today; title derives from H1 → alias → humanized stem (same derivation notebooks use). Card owns the H1 at render time. |
| `root: true` | — | project only | Makes the note its own root parent for Stats grouping. Checkbox. |
| `status` | — | `wip` / `done` / `canceled` | **Derived** from the `^prj` checkbox by `bob projects sync`. Never hand-edited. |

Sources: `docs/reference/vault-format.md` (area, project sections),
`docs/projects.md` (project notes, `^prj` task), `docs/areas.md`
(root sentinel, hosts/membership), `src/native/projects/scan.rs`
(`status`, `parent`, `ready_cap_raw`), `src/native/areas/graph.rs`
(`summary`, parent-edge validation).

### 1.2 Human behavior policies (the keys users actually get wrong)

| Key | Shape | Precedence worth surfacing |
| --- | --- | --- |
| `summary:` | one plain line, ≤140 chars | Area catalogs render it as inert text. Missing is fine; long/multiline warns (`area_summary_long`, `area_summary_multiline`). Projects have **no** `summary:` contract today — their catalog row shows the cleaned `^prj` criterion instead. |
| `task_type:` / legacy `theme:` | scalar ALL-CAPS | Nearest area/project default on the root walk; explicit `[type::]` on the task wins; `plan.default_type` is the floor. |
| `offclock: true/false` | scalar boolean | Nearest declaration on the root walk wins; `false` stops inheritance. Blank/absent inherits. |
| `offclock_types:` | list of type names | Non-empty list **beats the same note's `offclock:`** (`note_offclock_shadowed`). Scalar `MEET` = one-item list. Malformed = invalid (`note_offclock_invalid`). |
| `task_refresh: N` | integer 1–365 | Overrides the Ready freshness interval for resident tasks. Invalid → `task_refresh_invalid`, falls through to config. |
| `ready_cap: N / off / false` | integer 1–999, `off`, or YAML `false` | Overrides `plan.max_ready_per_note` (default 5) for the note's whole Ready lane. Invalid → `note_ready_cap_invalid`, default applies. |
| `project_name_aliases:` | flow or block string list | Extra capture/ref names for the stem. Empty/non-string entries ignored with warning; exact stem always wins; collisions are errors. |

Sources: `docs/reference/vault-format.md` (clock table, caps),
`docs/task-types.md` (§ defaults, `offclock_types`, rename),
`docs/freshness.md` (§ interval precedence, `task_refresh`),
`docs/plan.md` (§ Ready cap), `src/native/projects/scan.rs`
(`project_name_aliases`, `parse_offclock_types`).

### 1.3 What bob owns (never hand-edited)

- Body catalogs: `## Areas` (`> [!areas]`), `## Projects`
  (`> [!projects]`), `## Notebooks`, `## Albums`, `## Tasks` status
  grouping. Bob owns the callout bytes; heading and position are Bryan's.
- Project lifecycle writes: `status`, `#hide` on `^prj`, inline
  `[scheduled::]` hoisted from leftover frontmatter `scheduled`.
- Managed frontmatter patterns: `*_digest`, `*_drafted`, `review_*`,
  `zorg_*`, `generated_from_zorg*` (per the pf role table).
- Derived read-time state: effective `state`
  (`open/scheduled/blocked/warning/done/canceled`), `blocked` reason,
  open/shown/today counts, hue, depth/top, leaf/root-parent role.

### 1.4 The `bob-cli-pf` foundation this builds on

The pf epic (`sase bead read bob-cli-pf`) is the prerequisite and is
still in progress: every mounted card ends in a quiet **foot row**
(`▸ Properties · N` + concise `created` stamp, amber `⚠ N` lint chip),
`=-` toggles a read-only grouped drawer (Loose / On this card / Managed),
`=+` opens a keyboard-first generic property editor backed by a
byte-preserving `bob props show|update` writer with fingerprints and
inverse ops, and native Properties hides only when `props_v1` is proven
(fail-open otherwise). `==` stays the species editor; `=+` is the generic
editor. Plan source:
`sase/repos/plans/202611/card_owned_frontmatter.md` (§1–§8).

Implication: area/project work must **not** re-litigate the foot row,
ownership primitive, `props` byte-safety, or takeover gating. It only
adds: one card adapter per kind + role-table rows + 3–4 bespoke stages.

## 2. What the cards should look like

### 2.1 Card anatomy (v1, both kinds)

```text
┌─────────────────────────────────────────────────┐
│ [tile] AREA · cash                [hue dot]     │  kicker + stem-derived eyebrow
│ Cash reserve                                    │  owned H1 (render-time only)
│ under [[area]] · "Ongoing money sphere"        │  parent breadcrumb + summary
│ ● magenta · 2 projects · Ready room 3/5 · on-clock│  quiet meta row (derived)
│ ─────────────────────────────────────────────── │
│ ▸ Properties · 7                  created Jun 11 │  pf foot row (already built)
└─────────────────────────────────────────────────┘
```

```text
┌─────────────────────────────────────────────────┐
│ [tile] PROJECT · work_intake_flow               │
│ Ship the intake flow                            │  cleaned ^prj criterion as title
│ under [[work]] · ● ready · due Jul 16            │  parent + derived state pill
│ 4 open · 2 today · Next daily · PLAN default     │  quiet counts + policy hints
│ ─────────────────────────────────────────────── │
│ ▸ Properties · 9                  created Jun 11 │
└─────────────────────────────────────────────────┘
```

Design rules, following the existing card family
(`glossary:property-card`, record/intention/album precedents):

- **The card is the visible title.** Species glyph tile + tracked
  small-caps kicker (`AREA` / `PROJECT`), exactly like `ALBUM` / `RECORD` /
  `DAY`. Hue never paints the card; at most a small hue dot + name, per
  the hue contract (configured color → pin → exempt mute → area stem →
  hash). Area/project hue is inherited from the top-level area, so a full
  hue wash would lie about identity on nested notes.
- **Title ownership, not title duplication.** The inline title and the
  first-body H1 hide at render time; Live Preview cursor/selection reveals
  raw Markdown; Source mode keeps native YAML. Same fail-open rule as
  every card: parse failure, unclosed fence, duplicate keys, or missing
  `props_v1` restores the native title + Properties.
- **Subtitle = the one line Bryan wrote.** Area: `summary:` (or nothing —
  never nag; 1,111 dailies taught us nagging is noise). Project: the
  cleaned `^prj` criterion text (the catalog already derives this; reuse
  it, don't re-derive). No second subtitle, no wrapped paragraph.
- **Meta row is read-only exhaust from `bob areas/projects list`.**
  Area: hue name, direct/subtree project counts, Ready lane state
  (`room/full/crowded/exempt N/cap`), clock default (`on-clock`,
  `off · MEET only`, …). Project: derived state pill (ready / scheduled /
  blocked / warning / done / canceled), blocked reason tail
  (`waits on [[x]]`, `scheduled Jul 16`), open/today counts. Every value
  names its source in the tooltip (`bob areas list`, `bob projects
  list`). Nothing here is clickable except parent links and the state
  pill (which jumps to `^prj`, not to an editor).
- **Catalogs stay in the body.** `## Areas`, `## Projects`,
  `## Notebooks`, `## Albums`, `## Tasks` remain full-width body
  sections. They are long, machine-owned, and need diff-friendly bytes;
  folding them into a narrow card column hurts readability and breaks the
  "Bob owns the callout bytes" contract. The card may show *counts*, never
  *rows*.
- **Project `^prj` stays a task line.** Do not render an inline checkbox
  in the card that writes the `^prj` line. Two writers (card checkbox +
  Task Card + sync) on one lifecycle line is a conflict factory. The card
  *navigates* to `^prj`; only the Task Card and `bob projects sync` write
  it.
- **Collapsed, mobile, print, embeds follow the kit.** Foot row stays
  rendered when collapsed (that is how `created` stays visible).
  Mobile stays read-only. Embeds/popovers/canvases never mount the card.
  Narrow panes stack key-over-value per the pf container query.
- **No new colors, no new motion.** Muted kicker, tabular numerals,
  amber reserved for lint, 160 ms drawer/chevron motion with
  `prefers-reduced-motion` respected — all inherited from pf §7.

### 2.2 What the card must NOT show (v1 non-goals)

- Full task lists, Today queues, or Ready tables. That is `## Tasks` +
  the `]s` / `]w` walks + `bob plan`. Duplicating them creates a second
  source of apparent truth that goes stale between paints.
- Stats charts (root-parent bars, type bars). Period/day cards own those;
  area/project attribution already exists in Stats drill-down.
- Child catalog rows. Counts link to the body sections; rows don't move.
- Edit affordances inline in the card (no pencil icons per row). All
  editing lives in `=+` (generic) and the existing Task Card (for `^prj`
  schedules/priorities). One writer per key, per pf §8.

### 2.3 Kicker, tile, and empty states

- Kicker words: `AREA`, `PROJECT` (matching `ALBUM`, `RECORD`, `DAY`,
  `WEEK`, `QUARTER`, `YEAR`, `BANK`). Never the stem, never `#area`.
- Tile: reuse the kit tile slot. Suggested glyphs from the existing
  Lucide set: area = map-pin / compass; project = target / flag.
  Final pick belongs to the visual pass with light/dark screenshots, but
  it must be monochrome and must not reuse the record sheet tile or the
  bank badge glyph.
- Empty states: missing `summary` → no subtitle line at all (not
  "No summary"). Missing `created` on area/project → faint
  `no created date` (same as album/record/bank, unlike temporal cards
  which stay silent). Invalid `created` → amber `created ⚠` with drawer
  lint. Orphan area (no valid parent chain) → quiet `⚠ unplaced` chip in
  the meta row with tooltip naming `area_parent_*`; same for a project
  with terminal-but-invalid `^prj` (`⚠ no valid ^prj`).

## 3. What `=+` should support on these notes

### 3.1 Routing (one writer per key)

| Role | Keys | `=+` behavior |
| --- | --- | --- |
| `identity` (locked) | `type` | Locked. Teaching line: "Note kind is set at creation; convert with capture/promote, not here." `y` opens YAML (escape hatch). |
| `derived` (locked) | `status`, `*_digest`, `*_drafted`, `review_*`, `zorg_*`, `generated_from_zorg*` | Locked. `status` line adds "Managed by `bob projects sync` from `^prj` — Enter jumps to `^prj`." Others name their writer. `y` opens YAML. |
| `card` (hand off) | `summary` (area subtitle), `record`-equivalent none yet | `summary` is editable here (Text stage, 140-char live counter) — but Enter on a *project criterion* row hands off to the `^prj` Task Card instead, because the criterion lives in the body, not YAML. No new `==` species editor in v1 (see §5). |
| `loose` (editable) | everything in §3.2 | Edited through `bob props update` with fingerprint + inverse ops, per pf. `created` is loose and editable. |

`parent` is the one interesting case: it is **loose but guarded**.
Editing it rewires the tree (area forest, project catalogs, root-parent
attribution, clock/type inheritance, capture routes). So it stays editable
in `=+` but gets a preview line ("Moves under [[x]] · 3 catalogs update
on next sync · clock inherits off · type inherits BUILD") and hard refusals
for cycles, self-parent, `done/` targets, and ambiguous stems — mirroring
`area_parent_*` findings. Apply still writes only the key; catalogs update
on the next `bob areas/projects sync` (or nightly), never inside the
editor transaction.

### 3.2 Per-key stages (only what the generic kit lacks)

| Key | Stage | Validation / completion |
| --- | --- | --- |
| `parent` | Link + preview | Vault link completion (stem + `path\|stem` disambiguation, same as catalogs). Preview lists affected catalogs + new inheritance. Refuse cycles, self, `done/`, missing/ambiguous with the `bob areas check` code in the hint. |
| `summary` | Text, 1 line | Live `N/140` counter; multiline paste refused with "one line" hint (matches `area_summary_multiline`). Only offered on areas in v1; on projects the row is absent (criterion lives on `^prj`). |
| `task_type` / `theme` | Type | Same stage as the Task Card Type row: Use-default-first with inherited reason (`Use default · BUILD from dev`), Today/Recent, validated new name. Consequence line previews affected resident tasks. Writes canonical `task_type:`; removes legacy `theme:` only per existing `bob types` merge rules. |
| `offclock` | Checkbox (tri-state) | `true` / `false` / absent (inherit). Absent reads as "Inherit (currently on-clock/off-clock)" with the declarer named. Never writes blank. |
| `offclock_types` | Tags (type vocabulary) | Vault type completion; values stored without `#`. Non-empty-list beats `offclock:` — the row shows a quiet "beats offclock on this note" note when both exist (mirrors `note_offclock_shadowed`). Scalar-vs-list normalized on write to block-list form. |
| `task_refresh` | Number | Integer 1–365 days. Out-of-range refused with the `task_refresh_invalid` message. Absent = inherit chain. |
| `ready_cap` | Number-or-off | Integer 1–999, `off`, or YAML `false` (exempt). Invalid → same message as `note_ready_cap_invalid`, nothing written. Preview shows lane effect (`Ready 7/5 crowded → 7/no-cap exempt`). |
| `project_name_aliases` | List | One alias per row; case-insensitive duplicate/stem-shadow preview (`exact stem wins`, `claimed by two notes`). Empty/non-string refused. |
| `root` (project) | Checkbox | `true` vs absent. Preview names the Stats effect ("own root parent" vs "folds into <top>"). |
| `created` | Date & time | Accepts `now`, `9:41pm`, `fri`, `-3d`, ISO; keeps the existing offset/separator style (pf datetime rule). Date-only stays date-only. |
| `template` | Link | Plain vault link completion. Rarely touched; no preview. |
| everything else | generic kit | Text / Number / Checkbox / Date / List / Link / Tags / YAML (nested `record:`-style maps open the YAML stage; native Properties can't edit these at all, so this is already a win). |

Add flow: name stage completes over vault property names with per-name
vault type + usage count (`metadataCache.getAllPropertyInfos()`,
feature-detected), Tab/Enter picks the type's stage, Shift+Enter forces
text. `status`, `type`, managed patterns never complete as new keys on
these notes — attempting them teaches ("`status` is derived from `^prj`").

### 3.3 Keyboard and write discipline (inherit pf, add two rows)

Inherit the pf grammar unchanged (`j/k`, Enter/`l`, `o/O/Mod+;`, Ctrl+D,
`u`/redo, `y`/Ctrl+E, `=`, Esc/`q`/Ctrl+[, plus parity `r`, Alt+J/K,
Space/`V`, Mod+C/V, `/`, `t`). Two area/project additions:

- Enter on a `status` row jumps to `^prj` (navigation, no write).
- Enter on a project criterion row opens the `^prj` Task Card
  (schedule/priority/relations live there).

Write discipline is pf §5 verbatim: instant paint from cache, reconcile
with `bob props show`, 250 ms debounced dry-run, Enter latches on a
current preview, all panes saved before apply, stale fingerprint keeps
the draft and rebases, 5 s optimistic overlay, per-path undo stack of
inverse-op batches (bounded at 20, survives reopening), honest degraded
modes (no `props_v1` → read-only + "Update bob"; invalid YAML → banner +
`y`; no frontmatter → "No properties yet — `o` adds the first").

## 4. Critique — is this a good idea?

**Yes, with the v1 scope above. The full-dashboard version is not.**

Where the idea wins:

- **Areas/projects are the last title-less notes.** Albums, records,
  days, periods, and bank all have cards; areas/projects show a raw H1 +
  raw Properties block. That inconsistency is the kind Bryan notices
  every day. A title-block card closes it for the price of one adapter
  per kind.
- **Their frontmatter is the most error-prone in the vault.**
  `offclock_types` shape rules, `ready_cap` ranges, `task_refresh`
  ranges, `task_type` vs legacy `theme:`, quoted `"[[parent]]"` scalar
  vs accidental list — all fail silently today as lints, if at all.
  A staged `=+` editor with completion turns six doc pages into six rows.
- **Inheritance is invisible.** `offclock`, `task_type`, clock, and caps
  resolve along the root walk; nothing in the note shows the effective
  value or the declarer. Even the quiet meta row ("inherits off from
  [[dev]]") is a large usability gain for near-zero risk because it is
  read-only exhaust.
- **The pf kit already paid the hard costs.** Ownership primitive, foot
  row, drawer, `props` byte-safety, takeover gating, visual language,
  e2e harness — all land in pf. The marginal cost of two adapters is
  small, and the marginal risk (paint-only, fail-open) is the safest kind.

Where the idea loses if it grows:

1. **Derived-state confusion is the top risk.** A project card showing
   `status`, `blocked`, counts next to editable rows invites "edit the
   card to unblock the project." Status is computed from `^prj` +
   dependencies + dates; editing it in YAML is already refused by sync
   semantics. The card must *look* read-only where it *is* read-only
   (muted meta row, lock glyphs, jump-don't-edit on Enter), or it will
   manufacture support load.
2. **Catalog duplication.** `## Areas/Projects/Notebooks/Albums` are
   already full-width, diffable, synced machine output. Repeating rows in
   a card doubles paint cost, doubles staleness windows, and tempts
   card-side reordering that the sync transaction would then fight.
   Counts + jump links give 90% of the wayfinding for 0% of the
   conflict surface.
3. **Parent edits are tree surgery.** A careless `parent` change can
   orphan subtrees, flip clock/type inheritance for dozens of tasks, and
   move capture routes. The editor must preview and refuse, and docs must
   say catalogs update on sync — not in the keystroke. This is the one
   `=+` row that needs a real design review, not just a stage.
4. **Two editors on one note.** The `^prj` Task Card already edits
   schedule/priority/relations/Depends-On. A project `==` species editor
   would overlap it on day one. That is why v1 has **no** project `==`:
   `=+` owns YAML keys, the Task Card owns the `^prj` line, and neither
   reaches into the other.
5. **Performance and breadth.** `bob areas/projects list` JSON per paint
   across a large vault, plus metadata-cache reconciliation, plus
   multi-pane sessions — the kit's paint-reads-cache-never-spawns-bob
   rule must hold here too. Counts come from the cached report, never a
   fresh spawn per keystroke.
6. **Mobile and takeover sequencing.** Bank taught us some surfaces stay
   read-only on mobile and some notes keep native Properties during skew.
   Areas/projects must follow the same gating (`props_v1` probe,
   desktop + Live Preview/Reading + valid parse + mounted card), or a
   phone or an old bob strands Bryan without an in-document editor.

Would I take a different approach? Three were considered:

- **A. Minimal title card (recommended).** Title ownership + breadcrumb
  + subtitle + derived meta row + foot row. Small, consistent, hard to
  misuse. Loses nothing that `## Tasks` and walks don't already do.
- **B. Operations dashboard card.** Ready tables, Today lists, walk
  shortcuts, sparkline stats in the card. Rejected for v1: duplicates
  body sections and walks, needs fresh spawns to stay current, largest
  paint cost, most new UI to maintain. Revisit only with evidence that
  Bryan opens areas/projects *instead of* walks — current evidence says
  walks are the review surface and notes are the residence.
- **C. No card; `=+` everywhere only.** Cheapest and arguably sufficient
  for editing. Rejected as the whole answer because it leaves the
  title-block inconsistency, hides inheritance just as thoroughly, and
  gives `=+` no mount (no foot row, no drawer, no discoverable `=+`
  entry point on these notes). But it is the correct *fallback*: if card
  adapters slip, ship `=+` on area/project notes with no card first —
  the pf `+` arm already works on any Markdown note.

## 5. Requirement adjustments (calling them out explicitly)

1. **Projects get no `summary:` row in v1.** Areas document `summary:`;
   projects document the `^prj` criterion. Teaching two subtitles for
   one card slot guarantees confusion. If Bryan later wants a project
   tagline distinct from its completion criterion, add it as a named
   decision with catalog-rendering rules — not as an opportunistic text
   key.
2. **`type` stays locked even though it looks editable.** Tempting to
   allow area↔project conversion in `=+`. Refused: conversion means
   creating/retiring `^prj`, rewriting catalogs on both sides, and
   re-homing tasks. That is capture/promote work with previews, not a
   key rename. The locked row must say so.
3. **No project `==` species editor in v1.** The prompt's "schema
   editors (triggered via the `=+` keymap)" is exactly right: on these
   notes the schema editor *is* `=+`. A project `==` would collide with
   the `^prj` Task Card. Revisit only if a coherent species-owned key
   group emerges (today there is none — unlike album `record:` or bank
   `bank:` there is no nested map to own).
4. **Parent-write scope is key-only.** The editor writes `parent:` and
   stops; `bob areas/projects sync` (or nightly) reconciles catalogs.
   Same-transaction catalog rewrites are out of scope — they would
   promote a property edit into a vault-wide transaction with its own
   lock, commit, and failure modes.
5. **Bank exclusion stands.** pf D5 keeps bank.md native Properties
   visible; nothing in this report reopens it.
6. **Takeover gating is non-negotiable.** Area/project cards adopt the
   same `props_v1` + parse + desktop + mode + embed/popover denials as
   every other card. No per-kind exceptions, no "hide Properties but
   editor coming soon" intermediate.

## 6. Recommended solution (phased)

**Phase 1 — Card adapters (bob-plugins, paint-only).**
AREA and PROJECT adapters on the pf kit: kicker, tile, owned H1,
breadcrumb, subtitle, derived meta row, foot row + drawer adoption,
`=-` arm, palette + Command Mode rows, light/dark + narrow/wide
screenshots, real-Obsidian e2e (mount on area + project, collapsed card,
off-screen `=-` scroll, `y` jump, invalid-YAML + duplicate-key + orphan
states). No writes, no `==`. Acceptance: every adopted card shows the
foot row and stamp; paint never spawns bob or writes the vault.

**Phase 2 — Role table + stages (bob-cli + bob-plugins).**
Extend `props` `roles.rs` with the §3.1 table (`status` derived,
`type`/`record+album parent` identity, `summary`/`parent`/policy keys
loose-with-guards); add parent/type/clock/cap/refresh/alias stages with
the previews and refusals in §3.2; wire drawer-row Enter and the
`＋ Add property / ✎ Edit all =+` line. Golden byte-preservation
fixtures gain area/project notes (quoted `[[parent]]`, `offclock_types`
block list, `project_name_aliases` flow + block, `ready_cap: off`,
CRLF/BOM/comment-travel cases). Acceptance: edit/add/delete/undo on an
area and a project, locked-row teaching, stale-fingerprint refusal,
byte-identical untouched keys on disk.

**Phase 3 — Takeover on these two kinds (bob-plugins).**
Wire whole-container ownership into AREA/PROJECT adapters behind the
same eligibility + cached `props_v1` probe as other cards; reroute
Mod+; and focus helpers to `=+`; run the fail-open e2e matrix and the
visual walkthrough; update `docs/areas.md`, `docs/projects.md`,
`docs/property-editor.md`, hotkey references, and the approved glossary
strands. Acceptance: owned notes hide native Properties with zero dead
ends (palette, Command Mode, right-sidebar File Properties escape
hatch, Source mode all verified).

Explicitly deferred: dashboard widgets, catalog folding, `^prj`
inline editing from the card, project creation wizard, vault-wide type
rename from the card, per-kind `==` editors, mobile editing.

## 7. Open questions for Bryan

1. Project subtitle: cleaned `^prj` criterion only, or criterion plus an
   optional tagline later? (Recommendation above: criterion only.)
2. Meta-row density: is `Ready room 3/5 · on-clock · 2 projects`
   the right quiet maximum, or do you want the row collapsible?
3. Should `template:` even appear in `=+` rows, or hide it as managed?
   (This report keeps it as a plain Link row; hiding is also defensible.)

## Sources checked

- `sase/repos/plans/202611/card_owned_frontmatter.md` (§1–§8; pf epic
  design, foot row, `=-`/`=+`/`==` chord family, role table, write model).
- `sase bead read bob-cli-pf` (epic scope, six phases, bank/drawer
  decisions).
- `docs/reference/vault-format.md` (area/project/notebook/album/bank
  frontmatter contracts, clock table, catalog ownership).
- `docs/areas.md`, `docs/projects.md` (catalogs, `^prj`, sync rules,
  human/JSON reports).
- `docs/records.md` (album `record:` schema precedent, index/owner
  catalogs).
- `docs/task-types.md`, `docs/freshness.md`, `docs/plan.md` (type
  defaults, `offclock_types`, `task_refresh`, `ready_cap`, lane
  intervals, hue catalog).
- `docs/develop/plugins/architecture.md`,
  `docs/reference/plugins/bob-ledger-tools.md` (kit chrome, `==`
  dispatcher, title ownership, paint-never-writes).
- `src/native/projects/scan.rs`, `src/native/areas/graph.rs`
  (frontmatter parsing, alias/clock-cap handling, cycle guards).
- `sase memory read glossary:property-card / area-note / project-note /
  record-card / record-note / album-note / day-strip / bank-card`
  (card-family vocabulary; audit-logged reads, no direct file opens).

# Sub-projects as a host catalog section — consolidated design

**Lead researcher synthesis** of five independent reports (`__cdx`, `__cld`, `__grk`,
`__mus`, `__gem`, in this directory) plus the lead's own code and vault verification.
2026-11-13 · bob-cli `c994cfbd`-era tree · bob-plugins linked checkout.

## Verdict

**Yes — do it, and all six of us agree on the shape.** Move the sub-project list out of
the `🧩 **Sub-projects:**` bullet under `^prj` and into **one** generated H2 section per
host note, built as a third member of the existing host-catalog family (`## Notebooks`,
`## Albums`): a heading Bryan owns over a bob-owned callout the `host_catalog` engine
maintains.

**Do not** build the other readings of the request. All five researchers independently
rejected:

- one H2 (or H3) **per child** — it mints headings that collide with drawer H2s,
  `@route#section` targeting, structural-heading code, and the Obsidian outline;
- bob-owned document **H3 sub-sections** (e.g. `### Open` / `### Done`) — they break the
  clean "bob owns the callout; Bryan owns the heading, its position, and every other
  byte" ownership rule that makes the notebook/album catalogs safe, and they churn the
  outline as groups empty and fill;
- **embedding or mirroring child tasks** in the parent — every `#task` has exactly one
  residence; mirrors would desync lanes, freshness, Ready caps, and archive pairing;
- a **Dataview/Bases-only** view — invisible to git, agents, and mobile, and it cannot
  serve as the local cache that close gestures need.

The "H3 sub-sections" instinct is satisfied *inside* the callout: bold group rows that
the plugin folds, exactly how an album's `[!records]` index already groups records.

The feature is bigger than it looks: today's one-line marker is also a **load-bearing
cache**. `surface.rs` and the task-status-cycler plugin read it to decide whether a
project still has open children (SUBOPEN/EMPTY), which drives `#hide` surfacing and the
close-gesture pull-in/successor offer. Readers in both repos must understand the new
format **before** the writer changes a single vault byte, or an old reader will see "no
open sub-projects" and offer a parent as finished while children are still open.

## What exists today (verified)

`bob projects sync` (Mac cron at :05/:20/:35/:50) writes one machine-owned child bullet
under an open `^prj`, after the Depends-On/BLOCKS subtrees:

```markdown
- [ ] #task #prj Ship the parent outcome! #hide ^prj
	- 🧩 **Sub-projects:** 🗓️ [[alpha]] • [[beta]] • ~~[[gamma]]~~ ✅ • ~~[[delta]]~~ ❌
```

Facts the lead re-verified directly (all five reports' load-bearing claims held up):

| Claim | Verification |
| --- | --- |
| The marker is a SUBOPEN cache, by design | `src/native/projects/surface.rs` — `open_subprojects` counts unstruck links on the marker; file comment says it exists "instead of child notes' `parent:` frontmatter, which would need a vault-wide walk" |
| A second reader lives in bob-plugins | `plugins/task-status-cycler/src/089-successor-project.js` — `PROJECT_SUBPROJECTS_MARKER = "🧩 **Sub-projects:**"`; more recognizers in `145-relation-index-model.js`, `148-task-link-marks.js`, `285-…-reading.js`, `212-project-conversion.js` |
| Project sync does **not** use the guarded catalog writer | `src/native/projects/sync.rs:435` writes planned files with plain `fs::write`; notebooks/albums use `host_catalog::txn` preimage-checked staged writes |
| The catalog engine already has what we need | `src/native/host_catalog/region.rs` — `RegionSpec`, byte-span edits, `missing/stale/current/damaged`, duplicate self-heal, and placements `BeforeFirstTasks` (NOTEBOOKS), `AfterSectionThenTasks("Notebooks")` (ALBUMS), `BeforeFirstH2` (RECORDS) |
| Pre-existing drawer-guard bug | `capture_drawers.rs::is_structural_h2_key` covers Tasks, the status-group titles, Pomodoros, Events, Highlights — **not Notebooks or Albums**. cld reproduced `@proj+prj#notebooks` committing a drawer bullet directly under a `[!notebooks]` callout |
| No structured output to build UI on | `bob projects list` has no `-f json` |
| No nightly repair | `src/native/nightly.rs` has notebooks/albums steps but no projects step |
| The pain is real and concentrated | 19 vault notes carry the marker; `sase.md`'s line is 1,793 bytes with **61** child links; ~110 project notes exist, ~79 with no children at all |
| `summary:` frontmatter does not exist on project notes | **0 of ~110** project notes have it; H1 titles are rare (≤9). Stems are what Bryan sees and types (`@sase_art`) |

Context from cld's vault survey (not independently recounted, direction consistent with
the lead's checks): 5 area notes (`dev`, `job`, `gtd`, `mac_inbox`, `vacation`) own
projects and list them nowhere; max tree depth is 3; deriving the closed ledger from the
vault instead of preserve-and-mark would add exactly **one** row today.

## Resolved disagreements (lead decisions)

The five reports agreed on the architecture and split on seven details. Decisions below,
each reversible at the cost of one constant or one planner rule.

### D1 — Name: `## Projects` with `> [!projects]` (cld's position; 4 of 5 chose `## Sub-projects`)

The sibling catalogs name the **child type**, not the relationship (`## Notebooks`,
`## Albums` — not "Sub-notebooks"). `## Projects` reads correctly on project notes *and*
on area notes, so one `RegionSpec` serves every host forever, with no rename migration
when areas join. grk's own follow-up plan would have shipped `## Sub-projects` on
projects and `## Projects` on areas — two headings for one concept. Recognition keys on
the callout; the heading is Bryan's to rename per-note after the first write, so the
cost of this choice is one string.

### D2 — Grouping: flat open rows + one bold `**Closed**` group. No Blocked group, no Open wrapper, no adaptive shape

- Open children sit at the callout's top level (cdx/cld's "intake"), so the common
  all-open case has zero extra structure. grk's always-present `**Open**` wrapper adds
  an indent level for nothing.
- cld's 🔴 Blocked group is replaced by **per-row glyphs** (D3): group membership churn
  (rows jumping groups on every reconcile flip) is worse than a glyph change, and
  SUBOPEN must not depend on group structure anyway.
- gem's adaptive layout (flat when ≤3, grouped above) is rejected per cdx: never
  quietly alternate formats on row count — it makes diffs noisy and the contract fuzzy.
- One bold `**Closed**` group row (no wikilink, recognized by exact text) holds the
  struck rows; the plugin folds it by default. "Closed" over cld's "Done & Canceled":
  shorter, not overloaded by the structural-title namespace, and ✅/❌ already
  distinguish the outcomes per row.

### D3 — Row state is a leading glyph, and the bytes stay locally parseable

grk's core constraint, adopted verbatim: the catalog bytes must encode open/closed so
close gestures keep a **parent-note-only parse**. Unstruck `[[stem]]` = open; struck
`~~[[stem]]~~ ✅/❌` = closed. On top of that, cld's state glyphs:

- *(none)* — open, ready;
- `🗓️` — open, `^prj` is `[?]` with a future date (today's marker already has this);
- `⛓️` — open, `^prj` is `[?]` for dependency/inherited reasons (**new**: cld found
  `sase_post_blog` dep-blocked and invisible today);
- `⚠️` — missing/malformed/duplicate `^prj`.

The catalog **reads** reconcile's `[?]` and never re-derives Blocked
(`decisions:projects-block-from-prj-line` stands). One explicit resolution against cld:
**⚠️ rows count as open for SUBOPEN.** A child with a broken `^prj` is not demonstrably
closed; per cdx's fail-safe principle, damaged or ambiguous data must never make a
parent look finished. SUBOPEN = "any unstruck wikilink row", full stop — the simplest
possible parse.

### D4 — Closed ledger: derived from the vault, not preserve-and-mark (cld/grk over cdx/mus)

Today's line retains a closed child only if already listed, and hand-deleting one prunes
it forever. That makes the line a function of *its own history*. The catalog becomes a
**pure function of the vault** (like Tasks grouping: nothing remembered between runs):
idempotent, self-healing, trivially testable. The plugin's default fold replaces
hand-pruning as the "I don't want to see these" gesture, and cld measured the real-world
cost: exactly one resurrected row today. **This retires hand-prune-is-permanent — an
explicit behavior change.** No cap on retained history (mus's cap of 10 rejected: a fold
makes length cheap; a cap discards history and adds a knob). Order: newest first by the
child's completion/cancel date, undated rows last A–Z.

### D5 — Rows link by bare `**[[stem]]**`, no title alias (cld over the other four)

Empirically settled: project notes almost never have H1s and never have `summary:`
frontmatter, so cdx/grk/mus/gem's `[[stem|Title]]` would degrade to humanized stems that
are *less* recognizable than the stems Bryan actually types in capture routes. The
plugin may tooltip an H1 title when one exists. Stems are also unique by construction,
so no disambiguation machinery is needed.

### D6 — Secondary text: the child's cleaned `^prj` completion criterion (cdx/cld over grk/mus/gem)

The criterion is the most useful single fact about a project ("sase has received >=1000
stars on GitHub!"), already authored, with no new key to keep in sync. Cleaning
pipeline (cld §5.2): drop tags, inline fields, Tasks emoji dates, the trailing `^prj`,
and the Keep `[💡](…)` link; reduce links to display text; collapse whitespace;
inert-escape remaining openers with the shared notebook escaping; omit when empty, a
template placeholder, or a duplicate of the stem.

### D7 — Direct children only; no nesting, no rollup (cdx/cld/grk over mus/gem)

A grandchild change must rewrite one parent, not every ancestor. Notebook-style
descendant rollup would also surface `root: true` reporting boundaries in a structural
view and let SUBOPEN double-count children an open child already represents. A
`root: true` child still appears in its parent's catalog — reporting ancestry never
erases parentage (cdx). Depth shows in the plugin as an optional read-only
`▸ N sub-projects` expander per row (cld), never in Markdown.

### D8 — Placement: `BeforeFirstH2` on first write → catalogs read goal → parts → knowledge → work

`## Projects` lands above `## Notebooks` / `## Albums` / `## Tasks` (cld/gem over grk's
after-Albums): the breakdown of the work is the most important catalog on a parent.
The placement variant already exists (RECORDS uses it). After the first write the
position is Bryan's, like every catalog. Empty host: delete the callout; delete the
heading only if its section is then blank.

### D9 — Areas get the catalog in v1 (cld over grk/gem/cdx's defer)

The contract is literally identical — "a host note lists its direct child projects" —
and the membership scan already reads every project's `parent:`; area hosts are five
more planning targets, not a second product. It closes a real gap (nothing lists `dev`'s
or `job`'s projects today) and D1 makes it free. Easy to drop from scope if Bryan
disagrees; nothing else depends on it.

## The recommended contract

```markdown
## Projects

> [!projects]
>
> - **[[sase_agents_repo]]** — Use `sase—agents` repos to sync sase agents across machines!
> - 🗓️ **[[sase_decks]]** — Ship the deck pipeline!
> - ⛓️ **[[sase_post_blog]]** — Plan features to launch after sase_blog post!
> - ⚠️ **[[sase_broken]]** — no valid ^prj task
> - **Closed**
>   - ✅ **[[sase_agent_history]]** — Migrate agent artifacts tab to "Agents" tab!
>   - ❌ **[[sase_back_policy]]** — Develop architecture policy that auto-deprecates…
```

- **Hosts:** every project note of any status, and every area note, with ≥1 child
  project. Terminal hosts keep a maintained catalog going forward, but migration never
  bulk-rewrites dormant terminal notes just for uniformity (cdx); sync touches a host
  only when its planned catalog differs.
- **Membership:** project notes whose scalar `parent:` resolves to the host under the
  existing cascade rules (exact path wins; unique case-insensitive basename otherwise;
  list-form/ambiguous/unresolved/self parents produce no row).
- **Order:** open rows A–Z by stem (case-insensitive, path tie-break) regardless of
  glyph, so state changes never move a row; then `**Closed**`, newest first.
- **Closed rows:** `✅ **[[stem]]**` / `❌ **[[stem]]**` — struck form
  `~~[[stem]]~~ ✅` is equally fine if keeping byte continuity with today's marker is
  preferred; whichever is chosen, "struck or ✅/❌-glyphed = not open" is the parse rule
  and must be a single shared helper in both repos.
- **Never in Markdown:** counts, tallies, dates, hues, blocked reasons, task numbers
  (unanimous; the notebook/period "no number is ever written" rule). Writes happen only
  on structural change: child created, closed, reopened, reparented, blocked/unblocked,
  schedule crossing the future boundary, or criterion edited.
- **Ownership:** bob owns recognized `[!projects]` quote lines only. Heading, position,
  and surrounding prose are Bryan's; authored H3s under `## Projects` outside the
  callout are untouched. Recognition ignores frontmatter and fenced examples; BOM,
  CRLF/LF, and EOF-newline state survive (all inherited from `host_catalog`).
- **Damage:** a malformed region refuses the host with a diagnostic and is never
  "repaired" by guessing — and, critically, never interpreted as an empty child set.

### The `^prj` task afterward

```markdown
- [ ] #task #prj Ship the parent outcome! #hide ^prj
  - ⛓️ **DEPENDS ON:** [[job#^api-freeze]]
```

A clean lifecycle task again: criterion, dependencies, logs. Depends-On ordering (MC8)
loses its Sub-projects special case. `#hide` semantics are unchanged — sync still
derives it from scanned children, now via the same planner that writes the catalog.

### The plugin card (bob-ledger-tools, sibling of the album card)

Root-ancestry hue, notebook-card tint/border/radius tokens, hidden redundant callout
title, and a right-side tally (`22 open · 1 blocked · 38 closed`). Per open row: stem,
muted one-line criterion (full text on hover/focus), and painted chips — open-task count
(from bob's JSON report, **not** the `open_task_count` frontmatter, which undercounts
blocked tasks), `● today` (resident has a Task Link under today's open Pomodoros),
`empty` (child's `^prj` surfaced), the blocked reason (`Dec 8 · in 3w` / `waits on
sase_blog`), and the optional `▸` child expander. Closed starts folded with a two-row
peek; folds live in pane view state with keyboard operability and `aria-expanded`
(W3C disclosure pattern), and a background refresh never resets fold or steals focus.
Failed report shows last-good data and Retry — never a fake zero. `↻ sync` affordance
when bob reports the catalog missing/stale; `＋ project` copies the `@host^`
capture starter. **The card never writes vault bytes.** Verify with the existing album
e2e harness: light/dark, ~375 px and desktop, fold persistence, byte preservation.

A rendered mockup against real `sase.md` data is in cld's report
(`subproject_h2_sections__cld_assets/projects_card_mockup.png`); grk's figures cover the
layout/decision/EMPTY diagrams.

## Reliability work the feature requires

1. **SUBOPEN dual-read first.** One shared rule — *SUBOPEN(N) = the `[!projects]`
   region has an unstruck wikilink row; else fall back to the legacy marker; if both
   exist, the catalog wins* — implemented in `surface.rs` and mirrored in
   `089-successor-project.js`, with the `closed_child` stem override intact. The
   parent-finished consequence stays an **offer** (`decisions:unblocked-tasks-are-offered`);
   no auto-link regression.
2. **Guarded writes.** Route catalog edits (and the same-file legacy-line removal)
   through `host_catalog::plan_host` + the staged, preimage-checked txn writer — not
   `projects/sync.rs`'s raw `fs::write`. One planned text per file; catalog, `#hide`,
   and lifecycle edits composed, never two writers overwriting each other. `-d` shows
   the real unified diff; a repeat run with unchanged inputs produces no diff.
3. **Write-at-birth.** Capture `@route^id@` / `@route:id@` and nav promotion stage the
   parent's catalog row in the same all-or-nothing batch (the `%n` notebook precedent),
   killing the 15-minute "sync will add it later" gap. Reparent restages both hosts.
   Add a `projects` step to `bob nightly` so athena heals catalogs when the Mac sleeps.
4. **Guards.** `@host#projects` refuses with `projects_section_generated` (fold the two
   existing near-identical notebook/album refusal functions into one driven by the
   `RegionSpec` list). **Phase 0, independent of everything else: add Notebooks, Albums,
   and Projects to `is_structural_h2_key`** — cld's verified live bug lets `#notebooks`
   drawer routing write into a generated callout today. Task-move/merge section targets
   and section completion skip the heading; relation/mention indexing and link marks
   exclude callout links (no mention rings, per TC5's existing managed-row rule);
   reverse project conversion skips the section; the Highlights snapshot renders the
   catalog as a linked block and omits the Closed group, matching how snapshots omit
   closed tasks.
5. **Structured report.** Add `bob projects list -f json` (versioned envelope v1:
   `projects[]` with path/state/glyph/criterion/schedule/blocked-reason/child-and-task
   counts, `catalogs[]` with `missing/stale/current/damaged`, `findings[]`). "Unknown"
   stays distinct from zero. Read `sase/memory/cli_rules.md` before adding the flag.
   The plugin consumes only this report (shared in-flight request, generation
   invalidation, last-good cache — the album data-service pattern).
6. **Legacy recognizers stay forever** (cld): old backups, `done/` copies, and unsynced
   machines keep parsing safely even after the writer is removed.

## Rollout (readers before writers, one host set at a time)

| Phase | Work | Size |
| --- | --- | --- |
| 0 | Never-drawer fix for generated catalog headings (ships on its own merits) | S |
| 1 | Dual-format readers with legacy fallback: Rust `surface.rs`, plugin cycler, Highlights snapshot. Release both repos; `bob plugins sync`. Vault unchanged. | S–M |
| 2 | `PROJECTS` RegionSpec, planner, guarded writer + legacy-line removal, capture-birth writes, nightly step, capture/merge/mention guards, `bob projects list -f json`, docs, decision record. Review `bob projects sync -d` (~20 host diffs), upgrade **all** vault hosts together (the Mac cron host matters most), then let the first real sync write. | L |
| 3 | Ledger-tools `[!projects]` card + e2e screenshots (reuse notebook DOM helpers and `[!records]` fold code) | M–L |
| 4 | Delete the legacy-line writer; recognizers stay | S |

Phases ride the daily release train (`bob-cli-releases-ride-a-daily-train`): no
hand-edited versions, `!`-mark the JSON/CLI additions appropriately, and don't rush
migration with an ad hoc release. An old binary that re-adds the marker line
self-heals on the next new-sync run, but hosts should upgrade together regardless.
Rollback after migration requires restoring compatible source first (new readers still
accept legacy bytes; old readers never learn the catalog).

Docs: rewrite `docs/projects.md` Sync Rules; update `docs/task-dependencies.md` §12.10
SUBOPEN terms, the managed-line table, and MC7/MC8; fix the `docs/notebooks.md` "never
on the Sub-projects line" sentence; update capture/vault-format/json-output references
and the Project Note Capture glossary entry. After acceptance, file one new immutable
`decisions` record (via `/sase_memory_write` flow) — e.g. *"Sub-projects live in a host
`[!projects]` catalog"* — citing this research and listing the rejected alternatives
(the `^prj` line, per-child headings, bob-owned H3s, live queries, task mirrors,
nesting), with `superseded_by` back-links where it touches existing records.

## Acceptance checklist (condensed from cdx)

- **Lifecycle parity:** open / future-scheduled / dep-blocked / done / canceled /
  reopened / terminal hosts behave as today; one remaining open child suppresses the
  finished offer; closing the last eligible child yields the same offer (never an
  auto-link).
- **Source safety:** legacy-only, new-only, and mixed notes resolve identically;
  damaged or ambiguous regions never imply empty; authored prose, fenced examples,
  BOM/CRLF/EOF state, and moved headings survive; repeat sync is a no-op.
- **Scale and rendering:** 61 children stay readable at ~375 px; zero children leaves
  no empty panel; all-closed hosts collapse to a header; keyboard folds, independent
  per-pane fold state, refresh-failure fallback; light and dark.
- **Guards:** catalog headings refuse capture/drawers/moves; conversion and reversal
  neither swallow nor duplicate generated content; no mention rings on catalog links.

## Open items for Bryan (two, both pre-wired)

1. **Areas in v1** (D9) — recommended yes; deleting one planner predicate drops it.
2. **Derived closed ledger** (D4) — recommended yes; it resurrects one row today and
   retires the hand-prune gesture in exchange for a catalog that is a pure function of
   the vault. If curated pruning must survive, cdx §"Durable Markdown" specifies the
   union-and-retain alternative.

## Report scorecard

All five reports converged on the host-catalog architecture, which is itself strong
evidence the design is right. **cld** contributed the decisive empirical grounding
(vault survey, live drawer-bug repro, rendered mockup, naming/area analysis) and most of
its positions won on evidence. **grk** contributed the sharpest framing of the
load-bearing constraint (locally parseable bytes for EMPTY) and the mention-ring/
reverse-conversion edge cases. **cdx** contributed the reliability spine: fail-safe
"never imply empty", the guarded-writer gap, reader-first migration, and the acceptance
matrix. **mus** mapped the planner/emitter split and the promotion/restore interactions.
**gem** independently confirmed the consensus and the reader dependency graph. Where the
final report overrides a researcher (cld's ⚠️-SUBOPEN rule, cdx/mus's preserve-and-mark,
grk's Open wrapper and after-Albums placement, mus/gem's `summary:` field and nesting),
the override and its reason are stated inline above.

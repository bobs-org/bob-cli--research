# Ref Cards: design, `==` behavior, and parallel delivery with `bob-cli-qm`

> **Research query:** How should bob-cli implement "ref cards" — a new property-card
> species for ref notes — in parallel with the in-progress `bob-cli-qm` epic (notebook
> and prose cards)? What should the card show, should `==` open a schema editor and
> what should it do, and what should the new "ref card" glossary term say?

## Bottom line

**Yes — build it, as a third sibling-epic species on the same Property Card kit, with
one gate on `bob-cli-qm.1` (kit) and no other coordination.** Ref notes are the best
remaining card candidate: they open today on a wall of command-managed YAML
(`source_pdf`, hashes, snapshot pointers) while the single most useful fact about the
reference — *where am I in reading it?* — lives in a different note (the reading task
in the parent). A Ref Card that surfaces derived reading state, provenance, and library
facts without storing anything new is squarely the family's contract, not a new
invention. `==` should register the `ref` kind, but v1 should **not** ship a
record-style schema editor: it should focus-or-add the one safe authorable key
(`title`), because every other interesting ref key is derived, projected, or
command-managed. A dedicated ref editor (derived status locked, jump-to-task, YAML
escape for managed keys) is the correct v2, after `qm`'s focus-or-add and editor
patterns have soaked.

## Critique and adjustments to the request

**Is it a good idea? Yes, with the same correction every card request needs:** copy the
family's *contract*, never another card's *contents*. Ref notes are not task homes and
not prose — the card must not import ready caps, freshness, WIP badges, word counts,
or section-writing pressure.

| # | Adjustment | Basis |
| --- | --- | --- |
| A1 | "Hide native Properties" means the existing conditional, reversible takeover gate — never a blanket hide | The family reliability contract `qm` adopts unchanged |
| A2 | No new frontmatter, no new CLI surface, no wire change in v1. Everything the card shows is already computed by `bob ref list` / `bob ref show` | `NoteKind::Reference` already exists on the props wire (see below); ref rows are the richest JSON in the repo |
| A3 | The card must not touch the managed embed (`![[<residence>#^<id>]]`) or the reading task. It links to them; it never moves, creates, or edits them | Reading state is derived and the task is the status authority (per the accepted ref-status decisions); cf. `decisions:notebook-routes-write-notes` (cards never add tasks) |
| A4 | v1 has no annotation section chips. Counts only; sections are v2 | Section chips need a `show`-level subscription that does not exist yet; counts already ride on list rows |
| A5 | `==` in v1 focuses `title`, not a schema editor. The full editor is v2 | Nearly every ref key worth editing is locked-by-design (see [`==` section](#-support-with-a-phased-editor)) |
| A6 | Parallel means a sibling epic gated once on `qm.1` (kit), not edits inside `qm` | Same four-seam logic as `qm`'s own plan; detail below |

## Verified current state

Anchors verified 2026-11-26 on this checkout; re-locate every symbol on current master
before editing (both `qm` and `qi`/`qj` move these files).

- **Kit** lives in `plugins/bob-ledger-tools/src/` (linked `bob-plugins` repo): species
  registry `240f-plugin-property-card-species.js` (`PROPERTY_CARD_KINDS`,
  `PROPERTY_CARD_SPECIES`, `propertyCardApplyIdentity`), host
  `240c-plugin-property-card-host.js` (`createPropertyCardHost`), title slot and
  adoption `240e`–`240k` with `propertyCardNeverTitleRecognizer` in `240h`, created
  stamp `240m`, drawer inventory `240n` (keys marked `managed` fold into a closed
  `Managed · N` group), ownership coordinator `240q`, fold kit `240s`, and the `==`
  registry `248m-plugin-schema-double-equals.js` (`registerPropertyCard`,
  `propertyCardBuiltinEntry`, `propertyCardSecondKeyGate`, `propertyCardBareKeyGate`).
- **Built-in `==` kinds** are `bank` → `album` → `record` (`PROPERTY_CARD_BUILTIN_KINDS`).
  Extensions register the same way: `area`/`project` in
  `298z-plugin-property-editor-settings-entrypoints.js` (open Property Editor on
  settings), `intentions` in `297d-plugin-intention-card-entrypoints.js` (open the
  Intention Card editor). A ref entry follows this exact pattern — no kit change.
- **`qm` status:** epic `bob-cli-qm` (plan
  `sase/repos/plans/202611/prose_and_notebook_cards.md`) is `IN_PROGRESS` with all
  seven phases open. The load-bearing phase for ref work is `qm.1` (kit): species
  registry, the `props_v1`-only gate, the precedence function, **focus-or-add**
  (`openPropertyEditor({ filePath, key })` — present-key selects, absent-key opens Add
  prefilled), and the **preview gate** (`cardPreviewKinds: ["notebook", "prose"]`).
  Precedence resolves in bob's props order with notebook above prose; mixed types mount
  no card. Both cards paint synchronously from local YAML, patch report-backed rows in
  place, never spawn bob, never write the vault.
- **Props wire already knows refs.** `src/native/props/roles.rs` defines
  `NoteKind::Reference` (alongside `Notebook`), selected when a type name is `ref`, and
  role logic already special-cases it (line 153, line 493). Prose needed no wire kind
  and gates generically; **ref cards can gate on a real kind from day one** — strictly
  easier than prose.
- **Ref row model** (`src/native/ref_library/row.rs`, built in `mod.rs`) is the richest
  per-note JSON available: `title`, `marker_id` (frontmatter `id`), `origin`
  (`external` vs `agent-report`), `ref_type` (frontmatter or first dir under `ref/`),
  `era` (`modern`/`legacy`), `status` + `status_sync` + `frontmatter_status`,
  `reading_state` + `reading_state_source` (`queued`/`started`/`finished`/`dropped`/`unknown`),
  `blocked` + `blocked_by`, `parent` (projected from task residence), `task`
  (`path`/`block_id`/`link`/`mark`), `urls`, `earlier` lineage + `reading` number (the
  reread `vN` family), `identity` (`arxiv`/`doi`), `author`, `published`, `captured`,
  `added` (+`_source`/`_at`), `finished` (+`_source`), `source_pdf`, `audio`,
  `annotation_count`, `comment_count`, `snapshot.synced_at`, `research_ref`,
  `source_markdown`, `superseded_by`, `diagnostics`. Show rows (`show.rs`) add parsed
  annotations (quote/comment kept apart, page labels, kinds, block links, section ids),
  `ShowSection`s, `ShowTask`s, and excluded counts.
- **Frontmatter reality:** `type: "[[ref]]"`, `parent` (projected — editing it by hand
  fights the next scan), `title`, `id`, `ref_type`, `status` (derived — task wins),
  `legacy_status`, `author`, `published`, `captured`/`created`, `source_pdf`, `audio`,
  `source_url`/`url`, `earlier`, `research`, plus command-managed `source_markdown`,
  `source_block`/`source_path`/`source_id`/`source_blocks`, and snapshot hashes. The
  vault-format doc confirms the shape (`docs/reference/vault-format.md` §Reference
  notes); the reading-task contract is `docs/highlights-ref-sync.md` and
  `glossary:reference-note` / `glossary:reference-task`.

## Recommended card design

A compact **expanded-by-default** header card: refs are looked up, not contemplated —
reading state is the point, so unlike the folded-quiet Prose Card it should answer
"where am I?" at a glance. Two content rows maximum, everything content-gated (a
missing report hides the part; never `0 notes`, never `0 annotations`).

```text
╭────────────────────────────────────────────────────────────────╮
│ 🔖 REF · ● Work › SASE reading              queued · next      │
│    Why I built SASE — Bryan Bugyi, 2026                        │
│    ✎ 14 highlights · 3 notes · pp. 12–40    ♫ · ⬣ PDF · v2     │
│ ─────────────────────────────────────────────────────────────── │
│   added Nov 3 · from @work                   ▸ Properties · 12  │
╰────────────────────────────────────────────────────────────────╯
```

| Element | Source and rule |
| --- | --- |
| Tile | **New `bookmark` form**: a tile with a notch/ribbon cut, `bookmark` icon. Must stay distinct from `stack`/`sheet`/`leaf`/`plain`/`field`/`pennant`/`spine`/`folio` in light, dark, `forced-colors`, and grayscale (the `qm` acceptance matrix already tests this; add the ref tile to it) |
| Kicker | `REF` · parent crumb (residence root hue pip, like other cards) · reading-state word. Kicker word is always `REF`, never the `ref_type` |
| Title | `title:` → first H1 → humanized stem, same precedence as the index. `role="heading"` |
| Byline | `author` + `published` (one line, muted, omitted when both absent — most chat captures have neither, and that is fine) |
| Status chip (right) | `reading_state` word (`queued`/`started`/`finished`/`dropped`) + the underlying `status` mark (`ready`/`next`/`wip`/`read`/`abandoned`) as a small mark glyph. `unknown` shows a quiet `unread` — never an error. `blocked` earns a `⏳` pill naming up to two reasons, linking the prerequisite like project `waits on` links |
| Measure row | `✎ N highlights · M notes` (list-row counts, exact, no rounding — these are counts, not prose words) · page range when show data is present (v2) · `♫` when audio bound · `⬣ PDF` when `source_pdf` present (opens the PDF, like the Refs panel `Return`) · `v2`/`v3` chip when `reading != null`, jumping the family |
| Foot | `added <date>` (silent when absent) · `from @<parent>` route token (click copies, matching the Notebook Card) · lint chip from `diagnostics` (`missing_type`, `parent_mismatch`, `open_ref_without_task` deserve visibility) · `▸ Properties · N` drawer · `-`/`+` |
| Drawer | Every key in file order. Command-managed keys (`source_pdf`, `source_markdown`, `source_block(s)`, `source_path`, `source_id`, snapshot hashes, `snapshot`) marked `managed` → folded `Managed · N` group, exactly like zorg keys on notebooks |

**Deliberately not on the card:** the annotation bodies themselves (the managed region
below already renders them), full URLs (drawer + click-throughs cover this), `earlier`
lineage beyond the `vN` chip (one click reaches the family), mtime, word counts, task
creation, or anything that writes. Narrow panes (~420 px) drop the status chip below
the title, same as notebooks.

**Why this is the right "rich but uncluttered" set:** each row answers one question —
*what is it* (title/byline), *where am I* (status/blocked), *what's inside*
(annotations/audio/PDF/version). All three answers are derived facts the library
already computes; the card is a lens, not a ledger.

## `==` support, with a phased editor

**Yes, register the `ref` kind — but phase what it opens.**

- **v1 (ship with the card):** `==` runs focus-or-add on `title`. Rationale: `title`
  is the only display key that is always safe to author. `status` is derived (the task
  wins; a raw status edit would fight sync and re-open the settled reading-state
  decisions), `parent` is projected from task residence (a hand edit earns a
  `parent_mismatch` diagnostic on the next scan), and everything under `Managed` is
  command-owned. `==`-on-`title` matches the prose/notebook precedent and needs zero
  new UI. Policy chips, if any, open their own key — but v1 should show **no**
  authorable policy chips, because refs have no policy keys (no `task_type`,
  `offclock`, `ready_cap` semantics on a `[[ref]]` note).
- **v2 (follow-up bead): a dedicated Ref editor**, modeled on the Record Card editor
  and Intention Card editor, not on the album schema card:
  1. Derived status row, **locked**, showing `reading_state`, `status_sync`, and
     `blocked_by`, with a `Jump to reading task` button (opens the residence at the
     block id) — editing status happens in the task, never here;
  2. Editable `title`, `author`, `published`, `ref_type` rows;
  3. Locked `parent`, `source_pdf`, `audio`, identity, and snapshot rows with the same
     YAML-escape affordance the Record editor uses for identity/derived values;
  4. `research_ref` editable (it is a plain pointer).
- **Never:** a free status dropdown writing frontmatter `status`, a parent picker
  writing `parent:`, or checkboxes that create annotation follow-ups (those default to
  the parent note per the reference-note contract — the card must not reroute them).

`+` opens the Property Editor and `-` toggles the drawer, unchanged from the family.
The `==` gate follows the existing second-key machinery (`248m`): match on the
`reference` predicate, open per above.

## Parallel delivery with `bob-cli-qm`

Coordination is needed at **exactly one seam**, not four — ref work is downstream of
`qm`, not beside `qi`/`qj`:

1. **Gate phase 0 on `qm.1` (kit) closing.** Everything ref needs — the species
   registry slot, `props_v1`-only gating, the precedence function, focus-or-add, and
   the preview-gate helper — is created there. Poll the phase bead, confirm closed-done
   (the `qm` plan's own gate procedure), then build.
2. **Extend, don't fork, the preview gate.** `cardPreviewKinds` gains `"reference"`;
   one additive line plus its test. Rebase-safe against every `qm` species phase, which
   fills only its own fragment regions.
3. **New fragment files only**, following the `qm` naming convention
   (`refCard*` JS, `.bob-ref-card*` CSS — note `prose*` is taken; use `refCard`, never
   bare `ref*`), each under 1000 lines, `npm run build`, manifest bump,
   `bob plugins sync`. No `main.js`/`styles.css` hand-merges (rebase rule from `qm`).
4. **No bob-cli Rust change, no docs collision.** Eligibility reads the existing
   `reference` wire kind; `docs/ref.md` and `docs/reference/vault-format.md` gain a
   card section only at go-live, after `qm.7` lands (same serialization argument as
   `qm`'s `qi.6`/`qj.4` gates). Glossary last, under its own accepted memory decision.
5. **Data seam mirrors `241a`, not `prose-seam`.** The Notebook Card reuses
   `apiNotebookSubscribe` (one plugin-level subscription, zero spawns). Ref v1 should
   reuse whatever the reading board / Refs-panel client already polls (`bob ref list`
   JSON) behind one shared `apiRefSubscribe`-shaped service — **verify on current
   master whether that service exists; if it does, subscribe, if not, add it in the
   kit-gated phase.** Counts and status ride list rows; v2 section/page data subscribes
   to `bob ref show` snapshots the way `prose-seam` consumes `api.prose` v1
   (frozen copies, generation-guarded, absent-version → identity-only card).
6. **Acceptance joins `qm.6`'s matrix**, not a new harness: takeover, single-owner
   (mixed `[ref, area]` mounts nothing), native restoration, focus routing (`==`/`+`/`-`/`_`,
   Esc/`q`/Ctrl+`[` ladder), typing stability, passive proof (no spawn, no write — spy
   on `ref list`/`show` the way notebook tests spy on `notebooks list`), screenshots
   light/dark × narrow/wide × LP/Reading beside an area and a record card.

Precedence: append `reference` after `prose` at the end of the typed order. Mixed
`[[ref, …]]` mounts nothing (shared rule), so the position only matters against
path-based bank/temporal claims, which already win. Exclusions match the home card.

## Risks and open questions

1. **Two data seams, two stalenesses.** Status/counts (list) and annotations/sections
   (show) refresh on different clocks. The card must freshness-gate them independently
   (the `qm` rule: stale derived data hides or quietly updates chips; it never
   unmounts the title). v1 avoids this entirely by shipping counts only.
2. **The managed embed must stay put.** The reading-task embed below the H1 is the
   note's link to its task; title adoption must not swallow it. Verify against
   fixtures with v1 trackers, v2 embeds, and no-task legacy notes.
3. **Reread families.** `earlier`/`reading`/`superseded_by` make the `vN` chip load-bearing:
   it must never imply "latest" when `has_later` is true. Chip tooltip names the
   family position.
4. **`ref_type` vocabulary is open-ended** (`papers`, `chat`, …). The card shows it as
   text (tooltip/measure area), never as hue or icon — no per-type theming, which
   would recreate the hue-per-species trap the kit exists to prevent.
5. **Fixture coverage matters more than usual** because the live library is
   heterogeneous (modern/v2, legacy/v1, chat captures without PDFs, superseded twins,
   parent mismatches). Mirror the `qm` fixture-vault approach with one fixture per
   shape above.

## Recommended solution

A **sibling epic to `qm`** (call it the ref-cards epic), sized like `qm` minus the
seam work:

- **Phase 1 — kit extension (after `qm.1`):** register `reference` species (word `Ref`,
  tile `bookmark`, expanded default), `props_v1`-only gate, precedence entry,
  `cardPreviewKinds` + `"reference"`, fixtures for every ref shape, exhaustive
  precedence test extended with `ref` combinations.
- **Phase 2 — shell:** identity, title adoption (leaving the managed embed alone),
  byline, foot with route token, drawer with Managed group, `_`/`-`/`+`/`==`(→`title`)
  wiring, docs page with preview admonition.
- **Phase 3 — readouts:** one shared list-row subscription; status chip, blocked pill,
  counts, PDF/audio/version chips, diagnostics lint; content-gating everywhere; no-spawn
  spy tests.
- **Phase 4 — acceptance:** `qm.6`-matrix rows for ref fixtures, screenshot review
  (grayscale tile distinction for `bookmark`), repairs to GO.
- **Phase 5 — go-live (after `qm.7`):** delete the preview-gate entry, docs in both
  repos, `glossary:ref-card` + `glossary:property-card` family-list update under
  accepted memory decisions, clean deploy.
- **Tracked v2 follow-ups** (`PROPOSED FOLLOW-UP:` notes, not phases): show-level
  section chips + page ranges, the dedicated Ref editor, provenance crumb if `qj.5`
  defines extract/inline fields.

## Proposed glossary term

> [!draft] `glossary:ref-card` — keyword "Ref Card", alias "reference card".
>
> The note-top [[property-card]] for a [[reference-note]]. Bob Ledger Tools paints it
> in desktop Live Preview and Reading view.
>
> - **Identity.** A bookmark tile and a `REF` kicker, with the parent's crumbs in the
>   root hue, lead the title (`title:`, else the first H1, else the humanized stem)
>   and the `author`/`published` byline. A reading-state chip names where the reading
>   stands; it is derived, never authored on the card.
> - **Data.** From the shared `bob ref list` report it adds the reading state and
>   status, blocked reasons, annotation and comment counts, PDF/audio/version marks,
>   and findings as a foot lint chip. Missing report data is omitted, never zeroed.
> - **Foot.** It carries the `added` date, the `@parent` capture route (click copies),
>   and the Properties drawer, where command-managed keys fold under Managed.
> - **Keys.** `==` focuses `title`, `+` opens the Property Editor, `-` the drawer,
>   and `_` folds the card. Status is edited at the reading task, never on the card.
> - **Passive.** Painting never writes, never creates tasks, and never spawns bob.
>
> Not the [[ref-panel]] (the Mac Refs window), the managed annotation region, or the
> reading [[reference-task]] itself. See `docs/ref.md`.

## Evidence consulted

- `bob-cli-qm` bead (read with `sase bead read`, IN_PROGRESS, 7 open phases) and plan
  `sase/repos/plans/202611/prose_and_notebook_cards.md` (872 lines).
- Prior swarm synthesis
  `sase/repos/research/202611/prose_and_notebook_title_cards/prose_and_notebook_title_cards.md`
  (lead-verified vault counts, outline-shape findings, unanimous-agreement frame).
- `bob-plugins` kit sources: `240f` (species), `248m` (second-key/`==` registry),
  `298z` (area/project `==` extensions), `297d` (intentions editor extension),
  `240c`/`240e`–`240k`/`240m`–`240r`/`240s` (host/title/foot/fold), plus
  `docs/area-and-project-cards.md` and `docs/record-card.md`.
- `bob-cli` ref library: `src/native/ref_library/{mod,row,show,status,cli}.rs`,
  `src/native/props/roles.rs` (`NoteKind::Reference`), `docs/ref.md`,
  `docs/reference/vault-format.md`, `docs/highlights-ref-sync.md`.
- Memory: `decisions` roster (ref-status, notebook, capture, release-train records);
  `glossary:ref-panel`, `glossary:reference-note`, `glossary:reference-task`,
  `glossary:property-card` bodies.

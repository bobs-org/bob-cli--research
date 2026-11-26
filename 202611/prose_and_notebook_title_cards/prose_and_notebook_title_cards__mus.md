# Property cards for prose notes and notebooks

Research for making prose (fka article) notes and notebooks render a
property card at the note top, hiding native Obsidian Properties the way
other property cards do.

All commands below were run read-only against the live vault (`bob
articles outline/list`, `bob notebooks list/check`, `bob props show`);
no vault file was written. bob-plugin sources were read from the linked
`bob-plugins` checkout.

## What the card family looks like today

The shared family (album, record, day/week/quarter/year, bank, and now
area/project home cards) is built on the `bob-ledger-tools` kit:

- The species registry (`240f-plugin-property-card-species.js`) is a
  frozen map of nine kinds: `album, record, day, week, quarter, year,
  bank, area, project`. Each species is `{ kind, word, tile, icon,
  band, temporal, foldDefault? }`. Identity rule: hue says where, form
  says what, words say both; a species never gets a hue of its own.
- Mounting is gated and fail-open: a card replaces native Properties
  only when valid source matches the metadata cache, `props_v1` is
  confirmed for the current bob, and editor routing works. Otherwise
  native Properties plus the per-row fallback return. Painting never
  spawns bob and never writes the vault.
- The `==` dispatcher registry tries species in order (bank → album →
  record → day/period, then extensions). The foot shows `created` plus
  the full Properties drawer; `==` opens the species editor, `-`
  toggles the drawer, `_` folds, `+` opens Property Editor.
- Area/project home cards (`249d-plugin-home-card-host.js`) are the
  newest members: pure presentation over the metadata cache plus a
  local resolver, whole-frontmatter ownership through the shared
  frontmatter coordinator, fail-open with a row-level fallback.

Two facts matter for this proposal. First, the kit was designed for
extension: adding a species is a registry entry plus a host adapter,
not a redesign. Second, the in-progress epics already own the two
files this work would touch most: bob-cli-qi owns card acceptance,
the adapter matrix, screenshot review, and the docs sweep; bob-cli-qj
owns the `bob-articles` plugin identity and the vault's type
spellings.

## The two note types as they are

### Prose (article) notes

Frontmatter today is minimal: `parent`, `type: "[[article]]"`,
`created`, optional `title`, optional `section_numbers` (default on).
The one live note (`sase_blog_contents.md`) shows the shape. Refusals
keep prose notes task-free, anchor-free, and single-typed.

What bob already computes, all machine-readable today:

- `bob articles outline -f json`: per-note `words`, preamble words,
  per-section `{ number, depth, title, line, words, stub }`, `numbering`
  boolean. The single live note: 306 words, 15 sections, 14 stubs.
- `bob articles list -f json`: format findings with severity/line/hint,
  `inbound` heading-link refs, layout change counts.
- `bob props show -f json` on a prose note: capabilities include
  `props_v1`, fingerprint, per-key roles. **But `note_kind` reports as
  generic `"note"`**, and `type` carries `role: identity` with owner
  null. There is no first-class prose kind in the props contract.

### Notebooks

Frontmatter: `parent`, `template`, `type: "[[notebook]]"`, `summary`
(one line, 140-char budget), `created`. 39 notebooks in the live
vault, grouped under 13 roots.

`bob notebooks list -f json` already returns everything a card could
want: `title`, `breadcrumb`, `notes` count, per-section
`{ title, notes }`, `last_note` date, `owner` / `parent` /
`parent_kind` / `root`, `summary`, `children` (nested notebooks), and
per-note `issues`. `bob notebooks check -f json` adds hard errors and
soft summary warnings. And `bob props show` on a notebook reports
`note_kind: "notebook"` with `props_v1` confirmed — notebooks are
already first-class in the props contract, prose notes are not.

## Critique of the proposal

**It is a good idea, with three adjustments.**

1. **Yes to cards, and yes to hiding native Properties** — but only
   under the existing fail-open gate, not as a blanket takeover. The
   gate is the family's core reliability contract (qi is spending a
   whole phase proving it in real Obsidian). Prose and notebook cards
   must inherit it unchanged: stale cache, unconfirmed `props_v1`, or
   broken editor routing restores native Properties. No new takeover
   logic.
2. **The "rich data" ask needs a ceiling.** The request says prose
   notes "do not currently support many custom frontmatter properties
   (just a summary?)" — actually prose notes do not even have a
   summary key today (that is notebooks). The card must not become an
   excuse to invent a dozen new frontmatter keys that bob then has to
   own, migrate, and referee. Rule: **paint from computed data, store
   almost nothing new.** Every rich field below is chosen because a
   read-only bob command already emits it. The only frontmatter the
   cards should own is what editing already requires (prose: `title`,
   `section_numbers`, `parent`; notebook: `summary`, `parent`), all of
   which exist today.
3. **Do not build prose cards against the `article` name.** qj renames
   article → prose across engine, CLI, plugins, and vault. A card epic
   that keys on `[[article]]` ships already-stale and then pays a
   rename migration. Build against `prose` with `article` accepted as
   a legacy alias from day one — one predicate reading both spellings,
   exactly as qj's own `prose-cli` phase does.

One further challenge: **notebooks already surface their data twice.**
Every area/project note carries a generated `## Notebooks` catalog,
and `bob notebooks list` is the terminal surface. A notebook card
that repeats the whole section table is redundant. Its job is the
inverse of the catalog's: the catalog answers "what notebooks live
under X"; the card answers "where does *this* notebook live and is it
healthy". Keep it to breadcrumb, counts, recency, and findings — not
a second catalog browser.

## Recommended card contents

### Prose card

Identity: tile `scroll` (new; nothing in the registry uses it), word
"Prose". Title: `title:` when present, else stem. Kicker names the
parent (`in [[sase_blog]]` or bare "No parent").

Body rows, all computed, none stored:

- **Words + reading time** from `outline.words` (306 → "~2 min").
  Cheapest high-value signal for a writing note.
- **Sections + stubs**: `N sections · M stubs` (15 sections, 14 stubs
  on the live note — the stub count is the actual editorial signal).
- **Numbering state**: "Numbered" / "Numbering off", mirroring
  `outline.numbering`. This is the one state users toggle, so it
  earns a row.
- **Findings**: count by severity from `list` (`4 warnings`), opening
  the findings list. Prose notes accumulate pseudo-footnote and
  heading-link warnings; surfacing the count is what makes the card
  useful rather than decorative.
- **Inbound links**: count from `list[].inbound`. A prose note with
  zero inbound links is either new or orphaned — worth one row.

Foot: `created` plus the full Properties drawer, per family
convention. Editor (`==`): `title`, `section_numbers` toggle (reuse
qj's Toggle section numbers command semantics), `parent` picker. No
new frontmatter keys.

Deliberately excluded: a section outline browser (that is `bob
articles outline`'s job and would duplicate the note body two
centimeters below the card); word-goal or progress tracking (no
owner, no contract, new incentive surface — a later epic if Bryan
wants it); full finding text on the card (counts plus drill-in only).

### Notebook card

Identity: tile `tray` or `stack`-variant distinct from album's
`stack`; word "Notebook". Title: notebook title resolution (first H1
→ `aliases:` → humanized stem, per the contract).

Body rows, all from `notebooks list` JSON:

- **Breadcrumb**: `abby / About Abby` — the "where do I live" answer,
  with owner and root implicit in the trail. This is the card's
  primary job.
- **Notes + sections**: `12 notes · 5 sections`, with the top-two
  sections named only when sections exist (`Family life 4 · Health
  3`). Full section tables stay in the catalog.
- **Last note**: `last_note` date rendered as recency ("new note
  2026-11-25" / "quiet 90+ days"). File mtimes are never used — the
  contract already forbids it, and the card must too.
- **Summary health**: show the summary verbatim when valid; show the
  `notebook_summary_missing` / `_long` / `_multiline` warning state
  when `check` flags it. The summary is the one field the card edits
  most, so its health earns a row.
- **Findings**: error/warning counts from `check` (live vault today:
  2 errors, 13 warnings across 39 notebooks). Errors link to the
  offending rows.

Foot: `created` plus drawer. Editor (`==`): `summary` (with the
140-char budget enforced in the editor), `parent` picker. `template`
is create-time-only; the card shows it, never edits it.

Deliberately excluded: child-notebook trees (one row — "2 nested" —
at most; trees are the catalog's job); capture-route hints
(`@notes#Section` belongs in capture help, not on every card);
per-note rows (the body already lists them).

## Parallelism with bob-cli-qi and bob-cli-qj

**Coordination is needed, but it is narrow — three touchpoints, not a
merge.**

1. **With qj (rename): sequence, don't parallelize, the detection
   layer.** The card's note-kind predicate, the `bob-articles` plugin
   it extends or siblings, and the vault's type spellings are all
   qj-owned. Options: (a) land qj first, then build cards on `prose`;
   (b) build cards on a both-spellings predicate now and rebase the
   display strings after qj. (b) is strictly better — it is what qj
   itself does (`prose-cli` reads both spellings) — but the card
   phase must assert both-spellings acceptance in its own tests so a
   qj rebase cannot silently drop `[[article]]` notes. The `==
   ` dispatcher order and the species registry entry are new lines,
   not edits to qj's lines: no text conflict expected.
2. **With qi (card acceptance): reuse, don't duplicate, the harness.**
   qi's `takeover-proof` phase builds the real-Obsidian adapter matrix
   (fail-open, focus, routing, `^prj` integrity) plus the light/dark
   × narrow/wide screenshot review. Prose/notebook cards must be added
   as rows to that matrix, not given a second harness. If qi lands
   first, the card epic's acceptance phase is "add two species rows and
   re-run"; if parallel, the two epics share the matrix file and
   coordinate on its schema. Either way, one harness. The passive-
   rendering proof ("paint never spawns bob, never writes") applies
   verbatim: both cards paint exclusively from the metadata cache,
   confirmed source bytes, and the existing JSON reports.
3. **The props contract gap is the one real ordering constraint.**
   Notebooks report `note_kind: "notebook"`; prose notes report
   `"note"`. The mount gate keys on kind + `props_v1`. Either the
   props contract gains a prose kind (a versioned contract change —
   qi's `cli-hub` phase just made a `!` break in the same contract, so
   precedent says bundle it deliberately, not sneak it), or the prose
   card keys on the frontmatter `type` identity role the way the
   article plugin does today. Prefer the latter for the first cut:
   no contract break, same detection the formatter already trusts.
   Promote prose to a first-class props kind later, if a second
   consumer needs it.

Net: the work *can* proceed in parallel with both epics. The card
epic should start with the registry + both-spellings predicate +
paint-from-cache adapters (no qi/qj dependency), then sequence its
acceptance behind qi's matrix and its display strings behind qj's
rename. No phase of qi or qj needs to block on the cards.

## Glossary terms

Two new strands under `glossary:`, drafted to match the Property Card
web's voice (family-first, kit-owned chrome, fail-open gate stated):

- **Prose Card** (aka prose panel): a [[property-card]] view of a
  prose note's writing state. It owns the note top and hides native
  Properties only under the family gate (source/cache agreement,
  confirmed `props_v1`, working editor routing); otherwise native
  Properties return. It shows words/reading time, section and stub
  counts, numbering state, and finding/inbound counts painted from
  `bob articles` reports — never stored frontmatter. `==` edits
  `title`, `section_numbers`, and `parent`. Not an outline browser
  and not a word-goal tracker.
- **Notebook Card** (aka notebook panel): a [[property-card]] view of
  a notebook's placement and health. Same top-ownership and fail-open
  gate. It shows the owner breadcrumb, note/section counts with
  recency from `last_note`, the summary with its health state, and
  `bob notebooks check` finding counts — painted from `bob
  notebooks` reports. `==` edits `summary` (140-char budget) and
  `parent`; `template` is shown, never edited. Not a second catalog
  browser and not a note list.

Both drafts need `/sase_memory_write` handling (memory edits are
gated), and qj already owns the `glossary:prose-note` strand — the
Prose Card draft should link it, not redefine "prose".

## Recommended solution

A two-species extension of the existing family, built to paint from
data bob already emits, sequenced around — not blocked on — qi and
qj:

1. **Registry + predicate (no dependencies).** Add `prose` (tile
   `scroll`, word "Prose") and `notebook` (new tile, word "Notebook")
   to `PROPERTY_CARD_KINDS`/`PROPERTY_CARD_SPECIES`; dispatcher tries
   them after day/period. Detection reads both `[[prose]]` and legacy
   `[[article]]` spellings from day one; notebook detection reuses
   the existing `note_kind: "notebook"` mapping.
2. **Two host adapters in `bob-ledger-tools`** following the home-card
   mixin pattern: metadata cache + confirmed source + `props_v1`
   gate, fail-open to native Properties, passive paint only. Prose
   paint consumes the `articles outline`/`list` shapes; notebook
   paint consumes the `notebooks list`/`check` shapes. Consider a
   cached-report bridge rather than per-card CLI spawns — paint must
   never spawn bob, so the data path (cache service vs. adapter-held
   snapshot) is the design's one open technical question.
3. **`==` editors** limited to existing keys: prose
   (`title`/`section_numbers`/`parent`), notebook
   (`summary`/`parent`). Reuse qj's numbering-toggle semantics.
4. **Acceptance as rows in qi's matrix**, plus the family screenshot
   sweep extended to two species. Docs updates ride qi's docs sweep
   or follow it; do not start a parallel docs edit.
5. **Memory**: `glossary:prose-card` and `glossary:notebook-card`
   strands via the memory-write flow, linking (not duplicating)
   qj's `glossary:prose-note`.

What I would not do: new frontmatter keys for card data, a prose
outline browser on the card, word goals, capture hints on the card,
a separate test harness, or building against the `article` name. And
I would not gate any of qi/qj on this work — the dependency arrows
point one way.

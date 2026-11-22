# True-case task drawers: bold headers, one place resolver, a gated cutover

Consolidated report, 2026-11-22. Lead researcher merging five independent reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this directory) plus the lead's own
verification on bob-cli `513ec478` (grammar 29, catalog 2), a fresh audited read of the
`bob-cli-on` bead, audited memory reads, and the live vault roadmap note.

**Recommendation in one paragraph.** Yes, do this. Store a drawer as a bullet whose
entire body is one bold span — `- **API Design**` — directly under a task, exactly as
Bryan's own roadmap note asks (`~/bob/bob.md:120`: "Use `**Title Text**` for this! The
`*` character should expand to `**<cursor>**` when typed at the start of a
sub-bullet!"). Keep the title verbatim everywhere (capture, rename, promotion,
reversal); keep identity as today's case-folded `drawer_key`; recognize empty drawers
but never let capture create one; let managed-line matchers and reserved keys run
first. Capture keeps `- #slug` / `#"Title"` as shortcuts resolved through one shared
"place" resolver extracted from the notebook section machinery, and the completion menu
writes the canonical `- **Title**` so the draft mirrors the block. Render a quiet
drawer glyph plus a semibold true-case title in Obsidian and the Mac; with plugins off
it degrades to a bold header. Ship after `bob-cli-on` phases `.11`/`.12`/`.15`/`.17`
land, as dual-read → gated 7-drawer migration → cutover. Flip the gcal ALL-CAPS
defuse before the marker lands, or imported text will manufacture drawers.

![Mock: the same task block stored with `**Future Work**`, rendered in Obsidian with a drawer-front glyph and a true-case semibold title, and typed in the Mac capture draft](drawers_without_all_caps__cld_assets/drawer_marker_mock.png)

_Figure 1 (from the cld report): a design mock, not a screenshot — stored bytes,
proposed Obsidian Live Preview, and proposed Mac draft for the recommended form._

---

## 1. Is this a good idea? Yes — and here is the verified problem

All five researchers independently answered **yes**, for the same root cause: ALL-CAPS
overloads letter case with two jobs, content and structure. Verified consequences
(bob-cli `513ec478`, installed `bob 0.6.0` dry runs, vault scans on 2026-11-22):

- **True case is unrepresentable.** `is_drawer_title` (`src/native/capture_drawers.rs:1596`)
  requires the ASCII-uppercase grammar; every write path uppercases
  (`normalize_drawer_literal` at `:69`, the completion menu, `lexical_title_for_slug`).
  `API Design`, `iOS / OAuth 2.0`, `C++`, and `Café` cannot be drawer titles at all.
- **Round-trips are lossy by construction.** `format_project_section_title` is pinned by
  its own tests: `"API DESIGN"` → `"Api Design"` (`capture_project_note.rs:1041`), and
  the JS twin's comment says "Acronyms are not special-cased". Reversal uppercases and
  refuses `## C++ Notes`, `## Q1: Goals`, `## Café` outright. This directly blocks the
  stated larger goal (`^task-to-project`).
- **False positives are silent.** Any shouted note with detail (`- AWS` + child,
  `- TODO`, `- DONE`) becomes a drawer, which now also changes block zones and
  `req_in_drawer` refusals under the requirements contract (cld verified `- AWS` →
  "new drawer" in a scratch vault).
- **Hand-written bold headers are invisible and get duplicated.** cld verified that
  capture targeting `#"Future Work"` next to an existing hand-typed `- **Future Work**`
  creates a second, shouted `FUTURE WORK` drawer. This is the most user-visible bug the
  change fixes.
- **The timing is uniquely cheap.** Two independent vault censuses agree: only
  **7 ALL-CAPS task drawers exist** (5 in live notes — `NOTES` ×2, `NOTES:`,
  `OPTIONS:`, `MOTIVATION`, `DONE` — and 2 `NOTES` in `done/`). Once `bob-cli-on`'s
  automatic NOTES filing spreads across requirement-owning tasks, that count grows
  quickly. Migrating now is seven reviewed lines; migrating later is a vault rewrite.

The epic itself names `^no-all-caps-for-drawers` as an intended follow-up, so the
direction is pre-agreed. The plan's "one change in one place" framing understates the
surface, though: one Rust predicate with ~12 callers, four-to-five hand-written JS
copies in bob-plugins (one of which — `bob-ledger-tools/139-task-reqs.js:128` — has a
verified regex bug: `\/-?` is a character *range*, so it accepts `NOTE: X` and
`KEY:: VALUE` that Rust rejects), the gcal defuser, casing functions on both sides of
promotion, two Mac `.uppercased()` call sites, fixtures, and docs.

## 2. Does this rule out `#foo` tags? Yes — including the subtle variant

Bryan's instinct is right, and the reports sharpened it into four independent reasons:

1. **Tags cannot hold the title.** Obsidian tags allow no spaces and little
   punctuation, so `#Future_Work` is not "Future Work". The marker would defeat the
   change's first goal by itself.
2. **Tags are globally indexed.** Every drawer name would enter the vault-wide tag
   pane, `tag:` search, Graph View, and Dataview `file.etags`, beside `#task`, `#prj`,
   types, and the reserved clock tags.
3. **`#` is already two things in Bob.** Glued `#` names a place, free `#` names a type
   ([[decisions:capture-sigils-say-where-what-how]]). A third on-disk meaning makes
   `- #fix` ambiguous in the vault and the draft.
4. **It would mark the task**, exactly as Bryan suspected — note-level tag collection
   associates the tag with the block, not with a labeled container.

One report (mus) proposed the near-miss: *persist* the capture shortcut's bullet-start
`#` on disk (`- #Design Notes`). The lead's verification rejects this decisively:
today's `- #slug` bullets are routing text that the menu rewrites away and commit never
stores, so they pollute nothing — but a **stored** `- #Design Notes` is real vault
bytes, and Obsidian would index `#Design` as a tag (tags end at whitespace), splitting
the visible title and recreating every objection above. The safe `#` slot is a
capture-draft phenomenon, not an on-disk one. Keep `#` as the typing shortcut; store
something else.

## 3. The marker decision

The five reports proposed four canonical forms. Decision criteria, in priority order:
true case and punctuation; unambiguous recognition with low false positives; reads as a
header with plugins off (GitHub, mobile, raw source); lossless `## Title` mapping; easy
to type; beautiful.

| Candidate (report) | Decisive assessment |
| --- | --- |
| **`- **Title**` — whole-line bold (cld, gem)** | **Chosen.** Bryan's recorded instinct; pure CommonMark; reads as a bold header with plugins off; identity mapping to `## Title`; census shows 1 ambiguous line in 1,504 direct task children (0.066%), and the only whole-bold child *with children* (`**ROADMAP**`) was already a hand-made drawer — the convention matches existing intuition. Native Live Preview already reveals `**` at the caret, avoiding the concealment defect recorded on the epic (note #6). |
| `- § Title` (cdx) | Rejected as the canonical form. Semantically cleanest boundary, but `§` is painful to type on every keyboard Bob runs on, has no native editor affordances, and degrades to an unfamiliar glyph rather than a header when plugins are off. cdx's *model rigor* is adopted wholesale (see §4). |
| `- ## Title` — list-item heading (grk) | Rejected. Elegant unwrap/wrap promotion story, but it puts real ATX-heading semantics inside list items: CommonMark allows headings in list items, CM6 `ATXHeading2` styling/folding inside lists is buggy, GitHub renders a giant underlined `<h2>`, Pandoc emits `\subsection`, and the `##` look visually collides with the requirement `⌗⌗` family the display redesign just quieted. Loud degradation where bold degrades gracefully. |
| `- #Title` — persisted bullet-start `#` (mus) | Rejected on the lead's finding above: stored `#` is an Obsidian tag; the proposal fails its own criteria once the draft/disk distinction is applied. |
| Trailing `:`, `[drawer::]`, `%%drawer%%`, callouts, emoji prefix, `==…==`, `[d]`, fixed vocabulary, `+ Title` | Rejected across all reports: prose collisions (11 real trailing-colon notes), Dataview noise, hidden state, checkbox conflicts with the requirements contract, non-CommonMark, or config-bound. |

**cdx's honest objection to bold** — ordinary emphasis acquiring structural meaning —
is real and is answered with four fences rather than dismissed: an exact whole-span
recognizer (§4), the trailing-colon exclusion (§4), a one-character escape (`__…__`
renders identically bold and is never a drawer), and an outside-text rule (§7) so
imported bytes can never become structure. The vault census bounds the residual risk at
three historical lines, all listed in the migration report.

Bold also completes a teachable "one shape per child kind" table:

| Task child | On-disk shape |
| --- | --- |
| Subtask | `- [ ] #task …` |
| Requirement | `- [ ] …` (checkbox, no `#task`) |
| Managed link/log | `- 🛠️ **WORK LOG**` (emoji + bold label) |
| **Drawer** | `- **Future Work**` (bold label, **no** emoji) |
| Note | anything else |

Bold means "this line is a label"; a leading emoji means "Bob owns this label".

## 4. The recognizer, precisely

A **drawer** is a list item meeting all of the following (merging cld's rule, gem's
refinements, and cdx's model separation):

1. Direct, non-checkbox child of a real `#task` line, outside fences and quotes. On a
   `^prj` task, the note's eligible `##` sections remain its drawers, as today.
2. Trimmed body is exactly `**` + title + `**`: nonempty title, no leading/trailing
   whitespace inside the delimiters, no `*` anywhere in the title, nothing outside the
   delimiters (no trailing text, `^id`, tag, or field).
3. Title is single-line, contains at least one alphanumeric character, and — adopt
   gem's rule — **does not end with `:`**. This one exclusion automatically keeps the
   vault's gcal-imported `- **Note:**` a note, gives users a natural bold-label idiom
   (`- **TL;DR:** …`, `- **Important:** check X`), and matches the data: 0 of the 12
   unique project-note H2 titles end in a colon. Internal colons (`**Phase 1: Auth**`)
   stay valid.
4. Managed-line matchers run first; the key is not reserved (`TASKS`, `WORK LOG`,
   `LINKS`, …), and reserved keys grow Bob's structural H2 names (`PROJECTS`,
   `NOTEBOOKS`) so a user drawer can never collide with a Bob-owned section during
   promotion.
5. **Children are not required for recognition.** 53 of 109 eligible project `##`
   sections are empty; a lossless reversal of `## Future Work` (empty) must produce a
   valid empty drawer, and a hand-typed header must be fillable rather than duplicated.
   **Capture still never creates an empty drawer** — recognition policy and creation
   policy are separate APIs (cdx), which resolves the reports' one real disagreement
   here (grk wanted empty forbidden; cld/cdx/gem allow recognition).

Keep these values separate in the model (cdx): the authored title / raw span (display
and serialization, never reconstructed from a key); the lookup key; the selector
spelling; the source kind (explicit drawer, legacy ALL-CAPS drawer, project H2); and
header/body source ranges. Legacy parse provenance stays in the model during the
dual-read window so conversion preserves actual spelling without inventing case.

**Identity.** `drawer_key` stays the whitespace-collapsed, uppercased title, so
`Notes`/`NOTES`/`notes` remain one drawer, the NOTES role keeps its `NOTES` key with a
`Notes` display spelling (`NOTES_TITLE`/`NOTES_KEY` split in `task_block_layout.rs:64`
and the JS twins), catalogs carry over, and same-task case twins stay
`ambiguous_drawer`. Because non-ASCII titles become legal, define the fold as Unicode
uppercase on both sides (Rust `to_uppercase`, JS `toUpperCase`) from the start so the
twins cannot diverge — call this out explicitly in the contract vectors.

**Charset.** Replace the ASCII title alphabet with the rule above (nonempty,
single-line, ≥1 alphanumeric, no `*`, no trailing `:`). `C++`, `Q&A`, `eBPF`, Unicode
all become representable. Decouple `is_pomodoro_name` from the drawer grammar first
(gem): Pomodoro names and task types deliberately stay ALL-CAPS — that vocabulary
sharing was incidental.

## 5. Capture: one place resolver, draft mirrors disk

All five reports converged on the same architecture: the notebook section machinery
(`resolve_notebook_section`, `format_notebook_section_create_title`,
`section_bullet.rs`) and the drawer machinery (`resolve_drawer_for_write`,
`drawer_bullet.rs`) are already near-duplicate twins differing mainly in casing.
Extract **one named-place resolver** with scope adapters (`TaskDrawer`,
`ProjectSection`, `NotebookSection`; records can join later):

- **One lexer** for the bullet-start `#` and glued `#` (the two `scan_leading`s merge).
- **One ladder:** quoted exact → case-insensitive title match → unique slug →
  ambiguity (naming lines) → reserved/structural refusal → near-miss refusal with the
  quoted override → create.
- **One create-title rule:** quoted literals verbatim (whitespace-collapsed); unquoted
  slugs take the **catalog's most-used spelling** where the scope has a catalog (task
  drawers, `^prj` sections), else the notebook rule (keep typed capitals, Title Case
  the rest: `#API-keys` → `API Keys`, `#git` → `Git`). The creation row always previews
  the exact title that will land.
- **Scope parameters** carry today's deliberate differences — near-miss thresholds
  (drawer edit-distance 1 vs notebook ≤2), reserved sets, note-metadata rules — so the
  merge changes nothing but casing initially (cdx's caution). Converging thresholds is
  a later, explicit vector change. Writers stay per-destination: shared *selection*
  must not unify task-child and H2 *mutation* geometry — that separation is exactly
  what the epic's `^prj` NOTES-home bug got wrong.

**Draft forms** (per [[decisions:capture-bullets-mirror-the-task-block]], the draft
reads like the block it writes):

| Draft | Writes |
| --- | --- |
| `- **Future Work**` + nested notes (drawer position) | that drawer, title verbatim; merges by key into an existing drawer, keeping its spelling, with the preview showing which |
| `- #future-work` / `- #"Q1: Goals"` + nested notes | shortcut through the ladder; **menu acceptance rewrites the bullet to `- **Title**`** (plus `  - ` when no nested bullet follows) |
| `@foo+bar#api-design note` / `#"API Design"` | glued selector, same ladder; creation preserves case |
| `--drawer "Future Work"` | verbatim |
| Project-note capture with `- **Design**` + nested | `## Design` verbatim (was ALL-CAPS → Title Case) |
| Notebook `%n` seed / record capture with `- **Git**` + nested | `## Git` seed / that section group — the marker swaps in **all four** ALL-CAPS container contexts (cld's ADJ-5), or ALL-CAPS stays magic in some drafts and not others |
| Route-only `@nb` list with `- **Git**` + nested | unchanged: a note with detail; `- #Git` selects sections, preserving the deliberate `@nb`/`%n` split ([[decisions:notebook-routes-write-notes]]) |
| `- FUTURE WORK` + nested | a note, plus a one-release `caps_drawer_retired` teaching warning |

The `*` blocking sigil does not collide: the grammar already treats `**bold**` as
literal (the byte after `*` is `*`). Completion keeps its strongest invariant — the
applied replacement, the parse, the preview, and the commit all reach the same place
with the same title.

**Wire and versions:** bump `GRAMMAR_REVISION` 29 → 30 with a `!` commit (two breaks:
ALL-CAPS-with-nests stops being a drawer; quoted literals keep case). Additive wire
growth: a `drawer_marker` span over each `**` delimiter, menu replacements carrying
`**Title**`, drawer objects reporting verbatim `title` plus `key`. Bump
`DRAWER_CATALOG_VERSION` 2 → 3 and **stop uppercasing project H2s into the catalog**
(gem) — the 100+ existing project notes then immediately seed true-case spellings
(`Notes`, `Future Work`, `Motivation`) for the shortcut path.

**Rename:** case-only rename must become legal. Today
`rename-drawer 'API DESIGN' 'API design'` exits 2 with `same_drawer` (cdx verified);
the command learns verbatim-NEW, case-only respelling with equal keys, and an inventory
mode listing every legacy ALL-CAPS drawer. Distinct-name merges stay explicit;
duplicate identities are reported, never silently coalesced by the casing migration.

## 6. Typing the marker (Bryan's `*` → `**|**`)

Bryan's roadmap asks for `*` expanding to `**<cursor>**` at a sub-bullet start. gem's
census surfaced two genuine hazards — 8 direct task children begin with `*italic*`
(date-log lines, gcal imports), and Obsidian's default `autoPairMarkdown` already pairs
`*` — and cld's scoping answers them. Adopt the union:

- **Expansion fires only in a drawer position on an empty bullet body** (direct child
  of a task in Obsidian; first-level bullet under a new task, new project note, or
  note-less `@route+id` in capture), via `capture-rewrite` plus an Obsidian twin,
  composing with Obsidian's auto-pair the way the requirement `]` assist composes with
  `autoPairBrackets`. Italic notes elsewhere are untouched. If prototyping still shows
  auto-pair friction, gem's fallback is ready: trigger on `- *` + `Space` (CommonMark
  forbids whitespace after an opening italic `*`, so it conflicts with nothing).
- **Smart Enter** at the end of the title steps past `**` and opens the first nested
  note — the real friction in typing `**Title**` is leaving the closing delimiters.
- **Overtype absorption** (`*` before the closing `**` steps over both) and **atomic
  Backspace** (inside empty `**|**` deletes all four stars back to `- `); Undo restores
  `- *`. Paste, templates, and `bob capture` itself never rewrite.
- Optional: a Toggle Drawer command (wrap/unwrap a child bullet), mirroring the
  requirement toggle.

## 7. Outside text never becomes a drawer

The decisive cross-cutting hazard (found independently by cld and gem, verified by the
lead): `gcal/description/bullets.rs` **defuses** imported ALL-CAPS lines today by
wrapping them in `**…**` — under the bold marker, that exact branch would
*manufacture* drawers from Google Calendar descriptions. Flip it before the marker
lands:

- Imported ALL-CAPS lines pass through untouched (they are just text now).
- A whole-bold imported line is written as `__…__` — identical bold rendering in
  Obsidian and GitHub, never a drawer. Prefer this over gem's italicize-it variant,
  which would visibly change imported text. (The `__`→`**` formatter-normalization
  worry is moot here: Bob owns these writers, and the vault's linter has `strong-style`
  disabled.)
- Apply the same rule in `task_text_escape` (gkeep, gmail, highlights) and `%c`
  clipboard notes, and record the contract rule beside the requirements one: "Pasted
  text never becomes a requirement **or a drawer**."
- Note: gcal's span hash covers rendered bodies, so untouched Google spans rewrite on
  next sync — intended behavior under the existing decision.

## 8. Rendering: a quiet label, distinct from everything else

Principle (unanimous): **the plugin adds a glyph and never changes the words.** True
case, semibold, in every surface; never `text-transform: uppercase` or small-caps —
both would hide the very casing this change exists to show.

- **Obsidian** (bob-ledger-tools, attribute-only, zero extra DOM nodes — the proven
  requirements pattern): Live Preview `Decoration.line` + a reading-view
  post-processor stamp `data-bob-drawer`, `-key`, `-count`, `-empty`, and owner-state
  attributes. The bullet dot becomes a small **drawer-front/tray glyph** drawn as a CSS
  mask in a muted accent ink, completing Bob's shape grammar: square = task, ring =
  Task Link, diamond = requirement, dot = note, drawer front = drawer — distinct in
  silhouette and grayscale. A folded drawer shows a muted `· n notes` count; an empty
  one renders dashed and muted; a closed owner desaturates. Native `**` reveal at the
  caret means zero custom concealment code and none of the Mac caret defect recorded on
  the epic. gem's report carries a complete CSS specification (section-tab pill, SVG
  tray mask, tabular count via a CSS variable) ready for the implementation plan; the
  final glyph and hue are a taste pass with Bryan.
- **Mac:** thin client, as always — render the `drawer_marker` spans bob returns. Dim
  the `**` delimiters rather than hiding them, with caret-adjacent reveal (do not copy
  the `req_marker` concealment defect, epic note #6). Drop the two `.uppercased()`
  calls in transfer/merge presentations. SF Symbol `tray` capsule in preview cards
  unifies the design language.
- **CLI and cards:** human output prints `· Future Work`, never an uppercased title;
  requirement and successor cards carry titles through as-is.
- **Plugins off / GitHub / mobile:** a bold header above its notes — the correct,
  honest fallback, and better than shouting.
- Accessible labels name the thing ("Drawer 'Future Work' · 2 notes · in 'Upgrade
  Postgres'"), not the glyph.

## 9. `bob-cli-on`: no semantic conflict, real contention — sequence, don't interleave

Fresh bead read today: **13 of 17 phases closed**; `.11` (Obsidian successor card),
`.12` (promotion), `.15` (Mac Pull-In card), and `.17` (memory) are IN_PROGRESS.
Re-read the bead at plan time.

There is **zero semantic conflict**: requirements are checkbox children, drawers are
non-checkbox children; reclassifying a line between note and drawer never changes
requirement identity (both break the owner chain). The conflicts are file, vector, and
memory contention:

| Epic surface | Overlap | Action |
| --- | --- | --- |
| `.12` promotion | the same promotion code (`100`/`110`/`667`), and it pins "other drawers → `## Title Case`" | **Send one instruction now** (cld): keep the drawer test and section casing behind `parseProjectSectionBulletTitle` / `formatProjectSectionTitle` only, so this change later becomes a two-function swap. Start after it lands. |
| `.11` close card | edits task-split files hosting a drawer-predicate twin; re-copies vectors | start after |
| `.15` Mac card | Mac fixture churn | start after |
| `.17` memory | rewrites `glossary:task-drawer` in ALL-CAPS wording | this work's memory records come after and correct it |
| Epic notes #2/#4 (`^prj` NOTES home writes duplicate `## NOTES` at EOF with tab-indented children) | same `ensure_drawer` project path | the bug belongs to the epic; verify it is fixed when the epic closes. If it survives, fix it as a **standalone precursor** (route `^prj` note-home through `project_h2_drawers` + column-0 `## Notes` keyed by `NOTES`) before phase 1 here — never while `.12` is rewriting that path. |
| RQ/RL/RW/SP shared vectors | contain ALL-CAPS drawers | update in bob-cli first, then re-copy into every twin (the twin-copy check enforces identity) |
| `NOTES` key, zones, `req_in_drawer`, grammar 29 | unchanged by this work | none |

Preserve the epic's approved constraints untouched: drawers hold notes, never
requirements or an alternate status; the notes drawer is born with the first *note*;
promotion moves only the outer requirement boundary; the migration's retirement of
`REQUIREMENTS` is not revived; Rust owns semantics, JS twins share Rust-owned vectors,
the Mac renders Bob's decisions.

## 10. Lossless conversion: what this slice delivers, and what it honestly does not

This feature's promise: **title-preserving drawer ⇄ `## H2` conversion for currently
supported bodies** — `- **API Design**` ⇄ `## API Design` byte-identical in the title,
in both directions, with refusals (not silent drops) for unrepresentable content. Add a
pure drawer↔H2 round-trip test independent of the lifecycle transformation.

Define "lossless" before claiming more (cdx): preserving user-visible meaning,
preserving reconstructible information, and reproducing bytes are three different
promises, and "a distinct task representation for every project note" demands an
injective encoding. The audited gaps that remain for `^task-to-project` (gem's
102-project audit + cdx's inventory): generated `### Done & Canceled`/`### Blocked`
status groups inside `## Tasks` (62/102 projects — today's reversal refuses >60% of
real projects on this alone, and should learn to treat them as regenerable layout);
frontmatter and the document envelope; non-list prose, `###` subsections, fences,
tables; duplicate/empty H2 ordering; project tasks with lanes, dates, and history vs
lightweight requirements; structural catalogs (`## Projects`, `## Notebooks` — protect
them via reserved keys now); and merged-note provenance. Keep a whole-bold bullet
*inside* a drawer meaningless for now, so `###` ⇄ nested bold header stays available as
the natural next stone. The universal round trip needs its own spec; do not promise it
here.

## 11. Rollout: dual-read, gated migration, cutover

The reports split between a "clean cutover" (gem — only 7 drawers exist) and a
dual-read window (the other four). These converge in practice: Bob runs on multiple
hosts (athena, apollo, the Mac) behind a daily release train, so every host must run a
drawer-aware release *before* any vault bytes change — that **is** a dual-read window.
The resolution is cld's three steps with cdx's end-condition discipline:

1. **Dual-read release** (bob-cli, plugins, Mac): readers accept bold and legacy
   ALL-CAPS; every writer writes bold; capture flips with the `caps_drawer_retired`
   warning; the gcal defuse flips (§7). Old readers would mistake `§`-era or bold
   `Notes` headers for loose notes, so no vault migration until every host is current.
2. **Gated vault migration**: approved runs of the extended `rename-drawer`
   (inventory mode, verbatim bold NEW, case-only respell), dry-run first, through
   `/sase_gate`. **No automated recasing, ever** (grk/cdx's principle): a legacy
   `API DESIGN` cannot reveal whether `API design`, `API Design`, or `API DESIGN` was
   meant — but with exactly 7 drawers, Bryan supplies each intended spelling in the
   gate, so the principle holds and the result is still fully mixed-case. Proposed:
   `NOTES`×4 → `Notes`, `NOTES:` → `Notes`, `OPTIONS:` → `Options`,
   `MOTIVATION` → `Motivation`, `DONE` → `Done` (confirm `DONE` is really a drawer).
   The report also lists the two childless whole-bold notes and the gcal `**Note:**`
   line for review. A second run makes no changes.
3. **Cutover release** once the inventory reads zero: remove ALL-CAPS recognition, the
   legacy casing helpers, and the legacy vectors. An explicit end condition — not an
   indefinite dual reader — or ordinary uppercase prose stays structurally ambiguous
   forever.

**Implementation phases** (after `.11`/`.12`/`.15`/`.17` land): ① drawer contract in
bob-cli (recognizer + dual-read, DV vectors, ~12 caller retargets, writers emit bold,
gcal flip, Pomodoro decouple, catalog v3, `NOTES_TITLE`/`NOTES_KEY` split); ② place
resolver + draft forms + `drawer_marker` span + grammar 30 (`!`); ③ rename-drawer
respell + inventory; ④ plugins (one predicate twin replacing the four-to-five drifted
copies — ending the verified ledger-tools regex bug — verbatim promotion/demotion,
drawer marks, typing assists, `**Notes**` writers, and the task-split header unwrap fix
at `257-task-split-apply.js:203`); ⑤ Mac (span decode, dim+reveal, drop
`.uppercased()`, fixtures, exact-SHA macOS CI); ⑥ gated migration; ⑦ cutover;
⑧ memory records.

**Memory** (after `.17`, via `/sase_memory_write` at implementation time): a new
decision record ("Drawers Are Bold Headers With Their Real Names"); mark
[[decisions:capture-bullets-mirror-the-task-block]] superseded in part (it pins
"ALL-CAPS title with nested notes is a drawer" and "the menu inserts the bare ALL-CAPS
title"); update `glossary:task-drawer` (its first sentence becomes false); and keep
"task drawer" and the `bob-cli-pf` property-card "drawer" apart in the glossary.

## 12. Adjusted requirements (explicit, as asked)

1. **Make structure explicit, not merely case-insensitive.** "Stop requiring caps" is
   not a design; the marker replaces the inference. Lowercase prose with children stays
   prose; after cutover, uppercase ceases to be a structural signal.
2. **No re-casing anywhere, end to end.** The goal needs more than storage: promotion,
   reversal, rename, catalog choice, completion, and previews all preserve spelling,
   and reversal stops refusing mixed-case/punctuated headings. This amends `.12`'s
   pinned "`## Title Case`".
3. **Empty drawers are valid for recognition; capture still never creates one.**
   Required for the lossless goal (53 empty project sections) and for filling
   hand-typed headers instead of duplicating them.
4. **Widen the title charset with the marker** (punctuation, Unicode, `C++`) and add
   the trailing-colon exclusion; keep Pomodoro names and task types ALL-CAPS.
5. **Swap the marker in all four ALL-CAPS container contexts** (task drawers,
   project-note capture, `%n` seeds, record groups); leave `@nb` route-only semantics
   alone. "Reuse the notebook logic" means the shared resolver and create-title rule —
   with per-scope policies kept explicit — not unified writers.
6. **Extend the outside-text rule to drawers** (gcal flip + `__…__` escape), or the
   change manufactures drawers from imported text.
7. **Scope the `*` assist to drawer positions** on empty bodies, composed with
   Obsidian auto-pair, with Smart Enter and atomic Backspace.
8. **Cut over in three gated steps**, never a flag day, with an explicit end to legacy
   recognition and no guessed historical capitalization.
9. **Scope "lossless" honestly**: this ships title isomorphism for supported bodies;
   the universal project⇄task representation is a separate spec with its own proof
   obligations.
10. **Sequence after the epic**, with one coordination instruction to `.12` now and the
    `^prj` NOTES-home bug handled as the epic's own fix or a standalone precursor.

## 13. Open questions for Bryan

- **Glyph and hue**: drawer-front vs tray mask, and the accent tone — a short taste
  pass over side-by-side prototypes (Obsidian + Mac) before locking CSS.
- **Migration spellings**: confirm the seven renames, especially whether
  `DONE` (sase_agent_recovery.md) is really a drawer and whether `NOTES:`/`OPTIONS:`
  drop their colons (recommended, given the trailing-colon exclusion).
- **Trailing-colon exclusion**: confirm that `- **Label:** …`-style bold leads should
  stay notes forever (recommended; it is also the gcal `**Note:**` fence).
- **Empty-drawer creation**: keep the capture refusal (recommended) or allow an
  explicit childless `- **Title**` draft bullet to create an empty drawer.

## 14. Disagreement register (how conflicts were resolved)

| Question | Positions | Resolution |
| --- | --- | --- |
| Marker | `§` (cdx) / bold (cld, gem) / `- ##` (grk) / stored `#` (mus) | Bold: Bryan's recorded instinct, census, degradation, native reveal; mus's option fails on Obsidian tag indexing of stored bytes (lead's finding); grk's on heading semantics and loud fallback; cdx's on typing cost. |
| Empty drawers | forbidden (grk) vs recognized (cld, cdx, gem) | Recognize empty; never create from capture — recognition and creation are separate APIs. |
| Cutover | clean one-shot (gem) vs dual-read window (rest) | Same end state; multi-host reality makes the window mandatory; cdx's explicit end condition prevents it becoming permanent. |
| Migration casing | gated per-drawer renames (cld, gem) vs marker-only, no recase (grk, cdx) | Both: never *automated* recasing; the 7 gated renames are Bryan's explicit per-title decisions. |
| gcal defuse replacement | `__…__` (cld) vs italicize (gem) | `__…__` — preserves the imported text's bold appearance. |
| Trailing `:` | title-invalid (gem) vs key-folded (cld option) | Invalid — cleaner type boundary, kills the real false positive, matches all 12 project H2 titles. |
| Resolver thresholds | unify now vs keep per-scope | Shared mechanism, per-scope policy initially; convergence is a later explicit vector change (cdx). |
| `^prj` NOTES-home bug | fix here (cld, gem) vs epic's job (grk, cdx) | Epic's job; standalone precursor only if it survives the epic's close. |

## 15. Sources

- The five reports in this directory, with their pinned evidence: bob-cli `513ec478`,
  bob-plugins `1e385218`, bob-mac-capture `bf4b55ed`/`bab5e5cc`, `bob 0.6.0` scratch-vault
  dry runs (cdx, cld), vault censuses (cld, gem, grk), and a `node` check of the
  ledger-tools regex (cld).
- Lead verification on this workspace (bob-cli `513ec478`): `GRAMMAR_REVISION = 29`
  (`capture_language/mod.rs:68`); `DRAWER_CATALOG_VERSION = 2` (`capture_drawers.rs:161`);
  `NOTES_TITLE = "NOTES"` (`task_block_layout.rs:64`); the gcal ALL-CAPS→`**…**` defuse
  (`gcal/description/bullets.rs`); `format_project_section_title("API DESIGN") == "Api
  Design"` pinned by test (`capture_project_note.rs:1041`); Bryan's roadmap note
  (`~/bob/bob.md:119-120`); fresh `bob-cli-on` bead read (13/17 closed; `.11`/`.12`/
  `.15`/`.17` in progress); audited memory reads of
  [[decisions:capture-bullets-mirror-the-task-block]],
  [[decisions:notebook-routes-write-notes]],
  [[decisions:capture-sigils-say-where-what-how]], and [[glossary:task-drawer]].
- Externals cited by researchers: CommonMark 0.31.2 (headings in list items), Obsidian
  syntax/tags/callouts help, Dataview task/list metadata docs, Obsidian forum threads
  on list-item headings.

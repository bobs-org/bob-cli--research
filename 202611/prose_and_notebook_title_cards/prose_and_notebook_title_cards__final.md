# Prose and Notebook Title Cards: consolidated design, critique, and delivery plan

Lead consolidation of five independent swarm reports — `cdx`, `cld`, `grk`, `mus`, and
`gem`, filed beside this report as `prose_and_notebook_title_cards__<suffix>.md` — plus
the lead's own verification pass over the disputed claims. Date: 2026-11-26. Base:
bob-cli `478d5233`, bob-plugins master `86f5f340` (re-verified at consolidation time),
live vault `~/bob` (read-only), live bead state re-read at consolidation time.

## Verdict

**Yes — build both cards, as two new species on the existing Property Card kit in
`bob-ledger-tools`, delivered as a sibling epic whose development starts now and whose
landing is gated at four narrow seams against `bob-cli-qi` and `bob-cli-qj`.** All five
researchers independently reached this architecture; none recommended waiting for either
epic to finish, and none recommended merging into them. The Notebook Card pays off
immediately (39 live notebooks, most of them opening today on a wall of Zorg-importer
YAML plus a separate header widget). The Prose Card has one live note but is the right
preparation for `qj.5`'s extract/inline work, which will multiply prose notes; it must
be the quietest card in the family. "Rich data" means data bob already computes —
painted, content-gated, and never stored into frontmatter to decorate chrome.

## 1. Settled by unanimous agreement

All five reports converged on these, from independent code and vault audits. Treat them
as the fixed frame for the plan:

1. **Two species on the existing kit, both hosted in `bob-ledger-tools`.** The species
   registry (`240f`), title adoption (`240e`–`240k`), foot and drawer (`240m`–`240r`),
   fold kit (`240s`), ownership coordinator (`240q`), and `==` registry (`248m`) are
   internal to ledger-tools and designed for extension. Hosting the Prose Card inside
   `bob-articles` would require exporting the kit across plugins and would collide with
   `qj.3`/`qj.4` — rejected by every report. Two note-top owners on one note is exactly
   the bank/area failure `qi` exists to finish burying.
2. **Same takeover contract, unchanged.** Cards hide native Properties only under the
   existing fail-open gate: desktop Live Preview/Reading, valid source matching the
   cache, confirmed `props_v1` for the current bob, working editor routing. Source mode,
   embeds, hover, canvas, print, mobile, stale evidence, and failed mounts keep or
   restore native Properties. The File Properties sidebar stays native. Both kinds gate
   on `props_v1` alone — both already report it (`bob props show`) — and neither gets a
   `props_contract_v1` settings contract in v1.
3. **Zero bob-cli Rust changes required for v1.** Notebooks are already
   `note_kind: "notebook"`; prose stays wire-generic `note` (see §3.2). All card data
   comes from reports that already exist.
4. **Painting never spawns bob and never writes the vault.** Fold, resize, drawer, and
   cursor movement are paint. The Notebook Card reuses the existing shared notebook
   report service (`241a`, `apiNotebookSubscribe`) — zero new spawns. Bead `bob-cli-p2`
   (ledger-tools once re-ran `notebooks list` ~97 times per burst) is the load-bearing
   warning.
5. **The Notebook Card absorbs the linked notebook header** (`241e`–`241g`): crumbs and
   child chips move into the card; the old header never stacks beneath it (see §9,
   decision 5 for the retirement question).
6. **Derived over stored.** No `status`, `published`, `url`, stored word counts, or tag
   keys. Every readout is content-gated: a missing report hides the chip; unknown data
   is never rendered as `0 notes` or `0 words`.
7. **Dual-spelling prose detection from day 1.** One shared predicate accepts
   `[[prose]]` and the permanent legacy `[[article]]`; a mixed type mounts no card; the
   visible kicker word is always `PROSE`. Writers never retype notes.
8. **One eligibility/precedence function, exhaustively tested.** Species resolution in
   bob's props order (bank path → album → record → area/project → notebook → prose),
   with a unit test over every two-type combination asserting exactly one species or
   none. Exclusions match the home card (`_templates/`, `done/`, `_conflicts/`, type
   notes, embeds).
9. **Sibling epic; glossary last; deploy serialized.** No edits to the `qi`/`qj` plans
   or their closed memory-decision lists. `glossary:property-card` is edited only after
   `qi.6` lands its version; `[[prose-note]]` is linked only after `qj.4` creates it.
   One clean `bob plugins sync` at the end; never mid-flight beside `qi.6`/`qj.4`
   deploys.
10. **Nothing for the Mac** (`decisions:mac-capture-is-a-thin-client`), and no
    notebook-card tasks, ready caps, or checkboxes ever
    (`decisions:notebook-routes-write-notes`).

## 2. Live evidence (cross-validated)

Vault numbers below were independently measured by at least two researchers and agree;
the lead re-ran the prose outline to settle the one discrepancy.

| Fact | Value | Design consequence |
| --- | --- | --- |
| Notebooks | 39 (13 roots, 828 notes, 7 with children, 12 nested) | Real daily surface; the card ships value now |
| Zorg provenance keys (×7) | 25/39 | Hiding native Properties is a dramatic cleanliness win |
| Have `summary:` | 39/39 | Subtitle is reliably present |
| Missing `created:` | 28/39 | Foot must silence missing created (see trap T1) |
| `last_note` non-null | 1/39 | Recency is content-gated, never a headline; label it "Latest dated note" — it is an authored `[created::]` date, not mtime |
| Have `##` sections | 15/39 (max 6) | Section chips stay compact; content-gated |
| Notebook findings | 13 `notebook_shape` warnings, 2 `notebook_duplicate_block_id` errors | Warnings → foot lint chip; hard errors earn a visible pill |
| Prose notes | 1 (`sase_blog_contents.md`) | Design against fixtures too, or the stubby outline overfits |
| Its outline (lead re-ran) | 306 words, **14 sections, 13 stubs**, numbering on, 190-word preamble, 4 `pseudo-footnote` warnings | Settles mus's 15/14 count; the draft-state signal is real |
| Prose frontmatter today | `parent`, `type`, `created` only — no `title`, no `summary`, no `section_numbers` | Title falls back to the stem; every chip must content-gate |

**Lead findings beyond the swarm.** The per-section prose outline JSON is richer than
any report assumed: each section already carries `line`, `end_line`, `output_line`,
`stale`, and `written` alongside `number`/`depth`/`title`/`words`/`stub`. Jump anchors
and staleness for the Prose Card come free from the existing plan payload — no contract
change. By contrast the notebook report's sections are `{title, notes}` only
(`docs/notebooks.md`); see §3.8 for why that still needs no CLI change. `cdx`'s
disposable-vault experiments add two durable cautions: `outline.words` includes heading
syntax/number tokens (a fixture went 10 → 13 words when formatting added numbers), and
`stub` means an empty-or-TODO *immediate* body — an umbrella heading with fully written
subsections still counts as a stub.

## 3. Disagreements, resolved

### 3.1 Prose title and H1 hiding — inline title only

`grk` proposed falling back to the first body H1 and hiding a matching H1. The other
four refused, and the evidence is decisive: in a prose note every ATX heading, including
`#`, is a numbered section (`docs/articles.md` heading rules); the live note's first
heading is `## 1. What is SASE?`; bob's `title-heading` finding is only *info* when a
first section repeats the title. **Resolution:** the Prose Card owns the Obsidian inline
title only and never hides a body heading. The kit already supports this —
`propertyCardNeverTitleRecognizer(kind)` exists at `240h:138` and the Record card
already uses it (`242w`) — so this is an existing pattern, not new machinery. Title
precedence: `title:` → first alias → **verbatim** file stem (no silent humanizing).
The Notebook Card keeps its own existing rule (eligible opening H1 → first alias →
humanized stem) with matching-H1 adoption, as every report agreed.

### 3.2 No new props wire kind for prose

`grk` wanted `NoteKind::Prose` as a `feat(props)!:` break. The other four kept
`note_kind: note`, and `qj.2` explicitly freezes `props/roles.rs` ("add no new wire
kind"). **Resolution:** no wire change. The plugin classifies prose from the frontmatter
`type` identity through the shared dual-spelling predicate — the same detection the
formatter already trusts. Revisit only if a second consumer needs a first-class kind;
any such break rides the daily train with `!`
(`decisions:bob-cli-releases-ride-a-daily-train`).

### 3.3 Prose data path — a small read-only `api.prose` seam, not a second spawner

Two camps: a new ledger-tools report service spawning `bob prose list` off-paint
(`cld`), versus a tiny versioned read-only API on Bob Prose exposing the outline cache
it already maintains (`cdx`, `grk`, `gem`). **Resolution: the seam.** Bob Prose already
runs the outline plan off-paint for its hanging numbers and status bar; duplicating that
with a second spawner invites the `p2` failure mode and a second source of truth.
Contract sketch (names are proposals): `plugin.api.prose = { version, snapshotFor(path),
subscribe(fn), unsubscribe(fn) }`, returning source identity/generation, outline,
findings, `stale`, and any `refused` reason. The provider owns request bounding and
rejects late responses; after an applied format, anchors refer to the *new* buffer
(`cdx`'s revision-safety rules). The card paints identity fields — kicker, crumbs,
title, numbering key, created — synchronously from local YAML, so a missing or disabled
Bob Prose still yields a correct quiet card with outline chips omitted. **No JS
recomputation of word counts** (`docs/articles.md` owns the semantics; a whitespace
counter would silently disagree).

### 3.4 Add `summary:` as an optional prose dek — recommended, called out

Split vote: `cld`/`cdx`/`gem` show an authored `summary:` when present; `grk`/`mus` say
add no prose keys at all. **Resolution (adjustment for Bryan, §9 decision 1):** document
`summary:` in `docs/prose.md` as an *optional* one-line dek. It costs nothing (a loose
property under `props_v1`, no finding, no requirement), matches every other collection
type (area, notebook, album), gives the card a subtitle, and gives any future prose
catalog (`qj.5` open question) a row summary. The card never scrapes the lede, never
generates a summary, and — unlike the notebook — never shows an "add summary" ghost:
prose notes open with a real paragraph and should not nag.

### 3.5 Word count, stubs, and progress — show, but honestly; no ribbon in v1

Four reports headline `306 words · ~2 min · 14 sections`; `cdx`'s experiments argue the
word count is formatting-sensitive and `stub` is not "unfinished." **Resolution:** the
measure line ships — `N sections` and the `§ numbered/§ off` chip are exact; words and
derived reading time ship as *approximate* (they come from bob's outline; tooltip says
so). The TODO signal ships literally — a content-gated `13 TODO sections` chip, never a
percentage or "67% unfinished" claim, because an umbrella heading with written children
still reads as a stub. `cld`'s per-section draft ribbon is a genuinely beautiful idea
but inherits exactly that semantic problem; defer it to a fast-follow, possibly after a
growth-only `content_words` / per-section refinement in bob (no `!`, schema stays 1) if
exactness starts to matter. Findings stay a foot lint count with line-jump drill-in,
never a banner.

### 3.6 `==` — register species entries for both kinds

Four reports register `==` (Property Editor focused on `summary` for notebooks, `title`
for prose); `gem` leaves it unregistered to preserve Vim `==` reindent. Lead
verification: the `==` dispatcher (`248m`) tries builtins then extensions and falls
through when nothing matches — so today `==` on these notes does reindent, and
registering is an additive `registerPropertyCard` entry, not an edit to `qi`'s files.
**Resolution:** register both. The family glossary promises "`==` opens the species
editor" and the keys `-`/`_`/`==`/`+` are the family's contract; breaking it on two new
species costs more than reindent (nearly useless in YAML-fronted Markdown) is worth.
Flagged as §9 decision 2 with `gem`'s dissent. Whatever editor opens keeps Esc/`q`/
Ctrl+`[` (`decisions:q-and-ctrl-bracket-mirror-esc`). Prerequisite: the T2 fix below,
or focusing a missing key silently fails.

### 3.7 Fold defaults and expanded content

Consensus: Notebook Card expanded by default (it is a navigation surface). Prose Card:
`gem` folds by default (~72–88 px, straight to the opening paragraph); `cld` keeps a
small open card. **Resolution:** prose folds by default — the quietest card in the
family, aligned to the `.bob-article` 40rem column, title in the prose heading face.
`_` expands a bounded mini-TOC (document order, capped `max-height`, per-section word
counts or a muted `stub` badge, line-jump clicks) plus the findings list. `mus`'s
objection (a TOC duplicates the body) is noted and softened: it is hidden by default,
capped, and the body two centimeters below has no jump affordances. Collapsed state
always keeps kicker, title, measure line, and foot.

### 3.8 Section jumps without a CLI change

`cdx` proved naive `#Ideas` links cannot distinguish duplicate H2s and proposed an
additive notebook report extension (per-section `line`); `gem` jumps via local editor
dispatch. **Lead synthesis:** resolve jump targets from Obsidian's own metadata cache —
local headings carry exact positions — and pair report sections to local headings by
document order. Duplicate titles disambiguate by position; no bob-cli change needed.
`cdx`'s report extension remains optional hardening, not a dependency. Prose jumps use
the outline payload's existing `line`/`end_line` with generation checks.

### 3.9 When work may start — develop now, land through gates

`grk` alone would hold the Notebook Card until `qi.4` GO. The consolidated position
honors the concern without serializing development: all code work starts now in **new
fragment files** with strictly additive edits to shared kit files, is verified offline
(unit tests, `npm run build:check`, preview fixtures, disposable vaults), and touches
neither `~/bob` nor `bob plugins sync` until the final phase. Landing gates: the
real-Obsidian acceptance phase waits for `qi.4` GO and reuses (extends, never forks) the
takeover e2e harness; the Bob Prose seam waits for `qj.4` (the plugin `qj.3` rewrites
has settled and every host runs `bob prose`); docs/glossary/deploy wait for `qi.6` and
`qj.4`. Courtesy rules: never land shared-kit edits mid-`qi.4`-screenshot-run; rebase
and rerun `npm run build` instead of ever hand-merging generated `main.js`.

Live bead state at consolidation: `qi.1`–`qi.3` and `qi.5` closed, `qi.4` and `qi.6` in
progress; all five `qj` phases in progress. (The reports' snapshots predate `qi.5`
closing — a reminder that the planner must re-read bead state and the decisions roster
at planning time, per `decisions:decision-rules-are-read-at-planning-time`.)

## 4. Verified implementation traps (fix in the first phase)

Each was found by at least one researcher and re-verified by the lead against bob-plugins
master:

- **T1 — "no created date" spam.** `240m-plugin-property-card-created.js:190`:
  `const silent = temporal || kind === "area";`. Without adding the two new kinds,
  28/39 notebooks and every adopted prose note print a "no created date" label.
- **T2 — summary focus strands on missing keys.** `241d:730` routes
  `notebookFocusSummaryProperty` through `openPropertyEditor({ setting: "summary" })` —
  a *settings* path notebooks don't have — and `298z`'s fallback (~lines 90–123) only
  matches *existing* frontmatter rows, returning false when `summary:` is absent. The
  card's "+ Add summary" ghost and `==` focus need an add/edit flow for a missing loose
  key, or takeover strands the existing catalog affordance.
- **T3 — the coordinator is hardcoded.** `240q` hardcodes the eligible kind list, a
  per-kind mount-source attribute, and the area/project-only `props_contract_v1` gate.
  New species need explicit entries; merely rendering `.bob-property-card` will not hide
  Properties safely.
- **T4 — notebook JSON has no section lines** (`docs/notebooks.md` §JSON:
  `{title, notes}`); use the local metadata cache for anchors (§3.8).
- **T5 — spawn discipline.** Reuse `241a`'s subscription for notebooks and the
  `api.prose` seam for prose; never spawn from paint, fold, resize, or drawer
  (`bob-cli-p2`).
- **T6 — namespace collision.** Bare `prose*` JS prefixes collide in grep with the
  existing `proseField` namespace in ledger-tools; use `proseNoteCard*` / `noteCard*`
  style prefixes (`cld`).
- **T7 — deploy discipline.** Fragments + `npm run build`; one serialized
  `bob plugins sync` at the end; the AGENTS.md refusal protocol (never `-F`); final
  acceptance names the exact CLI and plugin revisions, not "master."

## 5. Critique of the request, with adjustments called out

**Is it a good idea? Yes.** The family promise — one look, one key family, YAML behind
the drawer — currently breaks on exactly the two typed-note kinds that are growing
(notebooks via capture/zorg, prose via the rename and coming extraction). The notebook
card removes real daily clutter; the prose card is a title page, in the publishing
sense, for authored writing. The danger every report flagged: copying the Area/Project
card's *contents* instead of its *contract*. Prose notes and notebooks are not task
homes — no ready caps, freshness warnings, WIP badges, or activity pressure; a quiet
notebook can be an excellent reference collection
(`decisions:notebook-routes-write-notes`).

Explicit adjustments to the request as written:

| # | Adjustment | Basis |
| --- | --- | --- |
| A1 | "Hide native Properties" means conditional, reversible takeover under the existing gate — never a blanket hide | Unanimous; the gate is the family's reliability contract that `qi.4` is proving |
| A2 | "Rich data" means report-backed derived data; the only new frontmatter is an *optional* prose `summary:` (and the request's "just a summary?" was backwards — prose has no summary today, notebooks all do) | §3.4; unanimous on derived-over-stored |
| A3 | The Notebook Card *replaces* the linked notebook header rather than appearing above/beside it | Unanimous; two note-top surfaces is the bank lesson |
| A4 | "Act like other property cards" gets one species exception: the Prose Card hides the inline title only, never a body H1 | §3.1 |
| A5 | "Implement in parallel" means a sibling epic with four bead-dependency gates — not edits to `qi`/`qj`, and not waiting for them | §3.9, §7 |
| A6 | No new CLI surface, wire kind, or Rust change in v1 | §3.2; unanimous |
| A7 | Ship notebook value first; the prose card's data seam may trail `qj` without blocking anything | 39 notebooks should not wait on one article |

## 6. Recommended design

### Shared chrome

Both cards are ordinary kit title-block cards: species tile + kicker word, parent
crumbs with the root-area hue pip (hue says *where*, form and word say *what*; a
species never gets its own hue), one `role="heading"` title, optional subtitle, a
single content-gated readout row, and the standard foot (`created` when present, lint
chip, `▸ Properties · N` drawer, `+`). Keys: `-` drawer, `_` fold, `==` focused editor,
`+` Property Editor. Chips never render zeros; report-backed parts patch in place and
stay omitted when no cache is ready. All colors derive from the accent variable and
theme tokens; light/dark, ~420 px narrow panes, `forced-colors`, and grayscale species
distinction are acceptance criteria, matching the family.

### Notebook Card (expanded by default)

Closest analog: the Album Card — a task-free collection under an owner. Tile: a bound
"spine" form (inset accent bar) with the `notebook-tabs` icon the pickers already use.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ┃▤┃  NOTEBOOK · ● Personal › Dog                        30 notes     │
│ ┃ ┃  About Abby                                    5 § · Nov 25      │
│      Veterinary, feeding, care routines, and notes for Abby.         │
│      § Health 3  § Feeding 4  § Baby care 2  § Training 6  § Misc 15 │
│      ↳ child-notebook chips (only when children exist)               │
│──────────────────────────────────────────────────────────────────────│
│  Oct 12, 2024 · @about_abby · ▸ Properties · 9   −  +                │
└──────────────────────────────────────────────────────────────────────┘
```

| Element | Source and rule |
| --- | --- |
| Crumbs | Reuse the header's ancestry model (`241e`), minus the self crumb; ~4 crumbs max, middle collapsed |
| Title | Existing notebook rule (H1 → alias → humanized stem); matching H1 adopted |
| Summary | `summary:`, 2-line clamp; missing shows a quiet `＋ Add summary` ghost → focused editor (needs T2 fix) |
| Readout | `N notes` (direct, column-zero; nested detail and children excluded — tooltip states scope), `M §`, "Latest dated note" when non-null |
| Section chips | Per `##` in document order with direct counts; click jumps via local heading positions (§3.8); content-gated, `+N` past ~8 |
| Children | Direct child-notebook chips with counts; content-gated |
| Hard errors | Visible pill (e.g. `✗ 2 errors`) jumping to the offending row; soft warnings stay in the foot lint chip |
| Foot | `created` (silent when missing), quiet `@stem` capture-route token (click copies), drawer folding all seven zorg keys |

The old header's rendering is suppressed only in scopes the card has successfully taken
over; it remains the fallback where cards never mount. The "Notebook chips" setting's
header clause is updated; catalogs stay governed by it.

### Prose Card (folded by default)

Closest analog: a title page. Typography couples to the frozen `.bob-article` scope:
title in the prose heading face, card width aligned to the 40rem text column, the
quietest wash in the family (~3–4%). Tile: an editorial folio/initial form — final icon
(feather vs pilcrow vs `cld`'s drop-cap) chosen in the screenshot pass, in grayscale,
beside Record's sheet.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ ╭──╮  PROSE · ● Dev › SASE Blog            [§ numbered]  [Outline ▸] │
│ │¶ │  Why I built SASE                                               │
│ ╰──╯  A short account of the ideas behind the tool.   ← dek, if set  │
│       306 words · ~2 min · 14 sections · 13 TODO sections · ⚠ 4      │
│──────────────────────────────────────────────────────────────────────│
│  Oct 15, 2026 · ▸ Properties · 3   −  +                              │
└──────────────────────────────────────────────────────────────────────┘
```

| Element | Source and rule |
| --- | --- |
| Title | `title:` → alias → verbatim stem; inline title only, body headings untouched (§3.1) |
| Dek | Optional `summary:`; italic, 2 lines, no ghost, absence is normal (§3.4) |
| Measure | Sections exact; words/reading time approximate from bob's outline (§3.5); all omitted without a snapshot |
| `§` chip | Reflects effective `section_numbers`; click dispatches `qj.3`'s Toggle section numbers command when present, inert text otherwise; never a card-local YAML write |
| TODO chip | `13 TODO sections`, literal, content-gated; clicking expands the outline |
| Expanded | Bounded mini-TOC (jump anchors from the outline payload's `line`) + findings list with line jumps; a formatter `refused` state shows one calm explanatory line, never a fake zero-section report |
| Reserved | A content-gated provenance slot for `qj.5` extract/inline (`↰ from … · Inline back`) so that work lands without a layout rewrite |

### Reliability rules (non-negotiable, family-standard)

Zero paint spawns and zero paint writes; fail-open in the same frame; confirmed source
beats cache; missing report ≠ zero; one writer per key (shared property update service;
`bob prose` for numbering; never `processFrontMatter`); one card per view with
generation-bound handles across split panes; card text renders as text, never raw HTML
from a title or summary; unsubscribe on unload. Separate card-shell validity from
derived-number freshness — a stale count hides or quietly updates; it never unmounts the
title and flashes native Properties while typing.

## 7. Delivery: one sibling epic, six phases, four gates

Figures: `cld`'s Figure 1 and `grk`'s three rendered figures (sequencing, data flow,
header absorption) sit in this folder beside the reports and visualize essentially this
table; the consolidated gating is simple enough that the table is authoritative.

| Phase | Scope | Starts / gate |
| --- | --- | --- |
| **P1 kit + models** | Species entries (`240f`, tiles, styles), T1–T3 fixes, eligibility/precedence function + exhaustive two-type test, pure view models, dual-spelling predicate, preview fixtures | **Now** |
| **P2 Notebook Card** | Host/DOM/foot adapters on `createPropertyCardHost`, header absorption + fallback, `==` → summary, own docs page; offline tests + disposable vaults only | After P1 (**now**; parallel with `qj`) |
| **P3 Prose Card, local-first** | Host/DOM, typography coupling, inline-title-only ownership, measure line omitted without data, reserved provenance slot | After P1 (**now**; parallel with P2) |
| **P4 Prose data seam** | ~25-line read-only `api.prose` on Bob Prose + card subscription + `§` toggle wiring | After **`qj.4`** |
| **P5 Acceptance** | Extend the takeover e2e + passive-rendering proofs and screenshot matrix (light/dark × narrow/wide × LP/Reading, both species, fixtures beyond the one live note); single-owner matrix; version-skew cases (old bob, missing seam, disabled plugins) | After P2 + P4 + **`qi.4` GO** |
| **P6 Docs, memory, deploy** | Shared docs sweep; `glossary:prose-card` + `glossary:notebook-card` + family edit via `/sase_memory_write`; `sase memory init`, `just docs-gen`/`docs-check`; one clean `bob plugins sync` | After P5 + **`qi.6`** + **`qj.4`** |

Work split (from `cdx`, adopted): a notebook worker, a prose worker, and **one
integrator** who owns every edit to shared files (`240f`, `240q`, `styles.css`,
`fragments.json`, generated entrypoints, `==` registrations) so two feature agents never
rewrite the same kit file. The planner re-reads the decisions roster and live bead state
at planning time and records the four gates as bead dependencies — no heavier
coordination protocol is needed.

## 8. Glossary drafts (land in P6, through `/sase_memory_write`)

The user explicitly requested these two terms, so the plan's memory decisions for the
two new strands default on; the `property-card` family edit and the Notebook "not"
clause are separate decisions sequenced after `qi.6`. Naming hazard (`cld`): "notebook
card" could be confused with the `[!notebooks]` *catalog* card on owner notes — the
"Album Card" precedent names a catalog, not a title card — so both the new strand and
the family list must say "title card" and carry the "not" clause.

**Prose Card**

> The note-top member of the [[property-card]] family for a [[prose-note]], including
> the permanent legacy `[[article]]` spelling, rendered by Bob Ledger Tools in desktop
> Live Preview and Reading view. A quiet editorial tile and `PROSE` kicker with the
> parent's crumbs in the root hue lead the title (`title:`, else the file stem); the
> optional one-line `summary:` is its dek. From Bob Prose's outline snapshot it adds the
> section count, numbering state with the formatter's toggle, approximate words and
> reading time, a literal TODO-section count, and findings with line jumps; chips are
> omitted, never zeroed, when no snapshot is ready. It owns only the inline title —
> prose body headings are numbered sections and always remain visible — and hides
> native Properties only under the family gate, restoring them on any uncertain
> evidence. `==` opens the editor focused on `title`, `+` the Property Editor, `-` the
> drawer, `_` the card's outline. Painting never writes, formats, or spawns bob. Not the
> Bob Prose formatter, its hanging section numbers, a publishing status, or a completion
> score.

**Notebook Card**

> The note-top member of the [[property-card]] family for a [[notebook]], rendered by
> Bob Ledger Tools in desktop Live Preview and Reading view. A bound tile and `NOTEBOOK`
> kicker with the owner's crumbs in the root hue lead the notebook title and its
> `summary:` scope line. From the shared `bob notebooks list` report it adds the direct
> note count, section chips with per-section counts that jump to their headings, child
> notebooks, the latest dated note (an authored date, never file modification time), and
> contract findings — soft warnings in the foot lint chip, hard errors visibly. It
> replaces the linked notebook header where it mounts and keeps every frontmatter field
> reachable through the Properties foot; native Properties return whenever takeover is
> unsafe. `==` focuses `summary`, `+` opens the Property Editor, `-` the drawer, `_`
> folds the details; the foot carries the `@stem` capture route. Painting writes
> nothing and creates no tasks. Not the `[!notebooks]` catalog card on an owner note, a
> task home, or a review queue.

**Family edit** (`glossary:property-card`, after `qi.6`): add both species to the title
cards list and the `==` order; note both gate on `props_v1` alone and that the Prose
Card is the inline-title-only exception. Add a "not the Notebook Card" clause to
`glossary:notebook`. Link, never redefine, `qj`'s `[[prose-note]]`.

## 9. Decisions to put to Bryan (with recommended defaults)

1. **Optional prose `summary:` dek** — recommend **yes** (split vote; §3.4).
2. **Register `==`** on both species, focused editors — recommend **yes** (`gem`
   dissents to preserve Vim reindent; §3.6).
3. **Prose Card folded by default** — recommend **yes** (`cld` prefers a small open
   card; §3.7).
4. **Word count + reading time in v1**, labeled approximate — recommend **yes** (`cdx`
   would defer until a formatting-invariant `content_words` exists; §3.5).
5. **Old notebook header**: suppress on successful mounts and keep as fail-open
   fallback, revisiting full deletion after the card soaks — recommend **yes** (`cld`
   would delete it outright).
6. **`@stem` capture-route token** on the notebook foot — recommend **yes**, quiet and
   copy-only (`mus` would omit it).
7. **Prose title stem verbatim** (no humanizing) — recommend **yes**.
8. **Reading time plugin-derived** (`ceil(words/220–230)`) rather than a new bob field —
   recommend **yes** for v1; a growth-only field later if wanted.

## 10. Governing decisions and sources

Decisions consulted via `sase memory read roster:decisions` and cited above:
`decisions:notebook-routes-write-notes`, `decisions:bob-cli-releases-ride-a-daily-train`,
`decisions:mac-capture-is-a-thin-client`, `decisions:q-and-ctrl-bracket-mirror-esc`,
`decisions:decision-rules-are-read-at-planning-time`. No decision record governs
property-card species; none of the five researchers found a basis to require a new one
(the glossary strands carry the rules; `grk` concurs, defaulting a header-absorption
record off).

Primary inputs: the five sibling reports in this folder (each lists its own audited
beads, plans `plan:202611/bank_hub_demotion.md` and `plan:202611/prose_note_type.md`,
memory reads, and live read-only command evidence). Lead verification: bob-plugins
master via `sase repo open` (`240f`, `240h:138`, `240k`, `240m:190`, `240q:505–550`,
`241d:708–730`, `248m:340–400`, `298z:90–123`), bob-cli `478d5233`
(`src/native/props/roles.rs`, `docs/articles.md`, `docs/notebooks.md`), live bead reads
of `bob-cli-qi`/`bob-cli-qj`, `sase memory read glossary:property-card`, and read-only
`bob articles outline sase_blog_contents -f json` against the live vault.

# Property Card Cabinets: collapsing H2 catalogs into the card

*Research report (`__mus`) — cabinets for child areas, sub-projects, notebooks,
albums, records, plus the Schema/Setup migration and the `_`-with-numbers keymap.*

## Summary

The cabinet proposal is a good idea with one load-bearing correction: **cabinets
must be a presentation layer over the existing H2 callouts, not a replacement
for them.** Keep `bob` owning the `> [!areas]`, `> [!projects]`, `> [!notebooks]`,
`> [!albums]`, and `> [!records]` callout bytes in Markdown exactly as today;
render cabinets as card-mounted, session-foldable projections of the same report
data. Removing the H2 writes would be a vault-format break (sync planners,
section protection, capture routing, docs, tests, migration) and would delete
content from every surface cards do not mount (Source, mobile, embeds, hover,
canvas, print). Everything below assumes H2 stays as source of truth.

With that correction, the design is clean because the machinery is already
two-thirds built: a shared fold kit (`240s`), a fold-kind registry with per-note
session state, a `_` arm that toggles "the card's own fold," a `-` arm that
toggles the Properties drawer, and per-species fold kinds (`area`, `project`,
`notebook`, `album`, `record`, `bank`) already registered. The missing pieces
are small and well-bounded: (1) enumerate folds instead of resolving one target,
(2) a pending-`_` state with number hints, (3) one shared cabinet chrome used by
both Schema and Properties, and (4) five thin content-cabinet painters that
project the same reports the H2 callouts already render.

Coordination with the four in-progress epics **is** needed, but only at the
shared-kit seams. Content cabinets can then proceed in parallel per species
owner with almost no conflicts.

## What exists today

### The card family and the unnamed property cabinet

The Property Card family (`sase/memory read glossary:property-card`) covers
album, record, day/week/quarter/year, bank, area, project, notebook, and prose
cards, all built on the `bob-ledger-tools` kit in
`sase/repos/linked/bob-plugins/plugins/bob-ledger-tools/src/`. Identity comes
from the species registry (`240f-plugin-property-card-species.js`); area and
project cards mount through `249c-plugin-home-card-dom.js`, notebooks through
`249i-plugin-notebook-card-host.js`, albums through `241v-plugin-album-header.js`,
records through `242k-plugin-record-sheet.js`, bank setup through
`248c-plugin-bank-setup-hosts.js`.

The "property cabinet" is the shared foot (`240o` DOM, `240p` state, `240r`
adapter): a `Properties · N` disclosure plus a lazily-built drawer showing the
full frontmatter inventory, a `created` stamp, and lint. `-` toggles it via
`propertyCardToggleProperties` (per-note session state in
`propertyCardFootOpenStates`, mount registry per foot node). It already follows
the golden rules cabinets should copy: session-only state keyed by normalized
path, never frontmatter; per-path state survives refresh and collapse but not
reload; painting never spawns `bob` or writes the vault.

### The Schema widget and the `-` / `_` keymaps

- Album cards render a `Schema · …` summary line via `propertyCardBuildFoldRow`
  (`241x-plugin-album-schema-dom.js` → `propertyCardFoldNextId` body shell),
  registered as fold kind `"album"`, toggled by `_` through
  `propertyCardToggleDetails` (`248m-plugin-schema-double-equals.js`).
- The bank card's analog is the Setup section (`248c` hosts): folds when
  healthy, `_` toggles it, `==` opens Bank Setup — same contract, different
  chrome (see `glossary:bank-card`).
- `_` today resolves **one** target: `propertyCardFoldTarget` returns the first
  visible `[data-card-fold]` node whose kind is registered and whose
  `data-card-fold-source` matches the view path. With one fold per note this is
  exactly right; with six cabinets it silently toggles whichever comes first
  in DOM order — the core bug the numbers proposal must fix.
- `_` and `-` are bare-key arms in `handleSchemaDoubleEqualsKeydown`: Live
  Preview + Vim normal mode + in-content + no operator/count/buffer. Digits
  are currently rejected as `countPending`, which matters for the pending-`_`
  design below (the digit after `_` must be read as a cabinet pick, not a Vim
  count — the gate already guarantees `_` itself carries no count, so this is
  safe as long as the pending state consumes the *next* key).
- Close keys (`241xc`): `Esc`, bare `q`, and `Ctrl+[` all back out of panels.
  The proposal's "`<esc>` or `<ctrl+[>` to abort" matches existing muscle
  memory; note `q` should abort too for consistency (adjustment A3 below).

### Styling: two chromes that should be one

`Schema` uses `.bob-album-schema-summary` (muted one-liner) + the shared
`.bob-property-card-fold` row; `Properties` uses
`.bob-property-card-foot-disclosure` (`Properties · N`, chevron, keycap shown
on hover/focus). Both already share the keycap, chevron, and hover idioms, but
the paddings, type scale, and borders differ (`styles.css` ~lines 9298–9360 vs
11919+ and 13644+). Unifying them is low-risk CSS work plus snapshot review,
not a redesign — the fold-row kit (`propertyCardBuildFoldRow`) should become
the single chrome, with `Properties · N` re-skinned as a fold row with a
count summary (adjustment A1).

### The H2 sections cabinets would project

| Cabinet | Hosts | H2 source of truth (stays) | Report data (reused) |
|---|---|---|---|
| Child areas | area notes | `## Areas` + `> [!areas]` (`docs/areas.md`) | Areas report service |
| Sub-projects | area/project notes | `## Projects` + `> [!projects]`, open/Closed groups, state glyphs (`docs/projects.md`) | Projects report service |
| Notebooks | area/project notes | `## Notebooks` + `> [!notebooks]`, project groups (`docs/notebooks.md`) | Notebook catalog model (`241a–241d`) |
| Albums | area/project owners | `## Albums` + `> [!albums]`, `🧩` groups (`docs/records.md`) | Album catalog DOM (`241o–241q`) |
| Records | album notes | `## Records` + `> [!records]` tally index (`docs/records.md`, `albums/index.rs`) | Album records DOM (`241r–241t`) |
| Schema/Setup | album / bank notes | YAML schema / bank config (no H2 today) | Already painted inline; just re-housed |

Canonical stack order on a host follows the existing first-write outline
(Areas → Projects → Notebooks → Albums, then Tasks): that order is already the
settled convention for "everything at once," so cabinets should use it
top-to-bottom, with Schema directly above Properties and Properties always
last. Per-note only non-empty catalogs render a cabinet (matching today's
"empty subtree deletes the callout" behavior), except the Records cabinet,
which keeps its teaching empty state (`No restaurants yet`), and Schema/Setup,
which always render.

## Parallelism with bob-cli-qi, bob-cli-qj, bob-cli-qm, bob-cli-qp

Short answer: **coordinate at the kit seams, parallelize per species.** The
four epics' live phases (read via `sase bead read` on 2026-11-26) show exactly
where cabinets collide and where they do not:

- **bob-cli-qi** (bank hub demotion; only `qi.6` in progress: passive-rendering
  proof, docs sweep, approved memory, clean deploy). Cabinets touch the Bank
  Setup fold and the shared foot — both files `qi.6` is proving and
  screenshotting. Sequence the Schema→cabinet migration *through* `qi.6`, not
  beside it: either land the bank cabinet first and let `qi.6` prove it, or
  freeze bank chrome until `qi.6` closes. Do not re-skin the bank foot while
  `qi.6` screenshots it.
- **bob-cli-qj** (article→prose rename; `qj.3` Obsidian, `qj.4` host
  gate/cutover, `qj.5` extract/inline in progress). Low cabinet overlap except
  `qj.4`'s host gate and vault cutover touch the same mount/eligibility code
  cabinets extend. One gate review with the `qj.4` owner suffices; prose notes
  host no catalogs, so no prose-cabinet work exists.
- **bob-cli-qm** (Prose + Notebook Cards; `qm.4–qm.7` all in progress).
  **Highest overlap.** The Notebook Card host owns a fold kind, a foot, and
  `qm.4`'s report-backed readouts — the exact seams content cabinets reuse.
  Cabinets must rebase onto `qm`'s kit/fold/foot shapes, not fork them. Assign
  the Notebooks cabinet to whoever owns the notebook host (same author,
  sequential phases), and freeze `propertyCardFold*` signatures jointly.
- **bob-cli-qp** (Ref Cards; all 8 phases in progress, explicitly "touches
  `qm` only at named seams"). Ref notes host no catalogs, so no ref cabinet —
  but `qp` builds a *new* card on the same kit while cabinets *change* the kit
  (fold enumeration, `_` dispatch, foot chrome, CSS). This is the riskiest
  pairing. Mitigation: land the kit slice (fold enumeration + pending-`_`
  + unified chrome, section 1 of the rollout) before `qp.4` (Ref Card shell),
  with `qp` reviewing the kit diff at its `qp.2` scaffolding seam.

Concretely, partition by file ownership: the kit slice touches `240s`, `248m`,
`240o/240p/240r`, `241xc`, `240f`, `styles.css`, `fragments.json` (one owner,
one review with `qm`+`qp` owners). Each content cabinet then touches only its
species' DOM/host files plus one new painter (area/project → `249c` family,
notebooks → `249h–249j`, albums/records → `241o–241t`, bank → `248c/248k`
family) and can proceed in parallel. No epic needs to pause; each needs one
seam review. A shared `fragments.json` + `npm run build:check` discipline
already exists to catch the mechanical conflicts.

## Critique: is this a good idea?

**Yes, with the presentation-only correction.** Collapsing five H2 catalogs
plus Schema into card cabinets reduces scroll distance on exactly the notes
that are longest (hosts with big subtrees), puts the fold state where the rest
of card state already lives (session, per-note, instant), and gives Schema and
Properties one visual language instead of two. The fold registry and keymap
precedents (`-`/`_`/`==`/`+`, session state, `y` jumps, pending reveal scroll)
transfer directly.

The risks, in descending order:

1. **Vault-format temptation (fatal if indulged).** "Instead of in H2
   sections" reads as if the H2 writes stop. They must not: capture routing
   refuses generated sections (`areas_section_generated`,
   `projects_section_generated`, `notebooks_section_generated`,
   `albums_section_generated`), sync planners own callout bytes, and
   Source/mobile/embeds/hover/canvas/print have no cards. Cabinets duplicate
   *rendering*, never *storage*. If H2 removal is ever wanted, it is a
   separate vault-format decision with a migration — not this epic.
2. **Duplicate rendering.** In Reading view the card and the H2 callouts
   coexist. The card already hides owned lines (inline title, `^prj` styling);
   extend the same treatment: when a cabinet is mounted for a catalog, hide
   that note's owned callout region in rendered views (Live Preview + Reading)
   exactly as title ownership hides the H1. Source and print keep the H2.
   Without this, hosts show every list twice.
3. **Number instability.** Bottom-up numbering (`1` = cabinet directly above
   Properties) shifts whenever a cabinet appears/disappears (e.g. last child
   project closes → Projects cabinet vanishes → Albums renumbers). Mitigate by
   painting the number badge *on each fold row* whenever hints are armed, so
   the mapping is visible in place, and by keeping the empty→absent rules
   identical to the H2 rules so renumbering is at least predictable.
   Top-down numbering (1 = top) would match DOM/screen-reader order, but the
   prompt mandates bottom-up with a defensible rationale: `1` stays adjacent
   to the always-present Properties anchor, and bare-`_` muscle memory maps to
   the Schema cabinet pinned directly above Properties. Keep bottom-up; note
   the alternative in the plan.
4. **`_` pending-state complexity.** A modal key state in a Vim context must
   handle: second `_` (recommend: toggles the Schema cabinet = legacy
   behavior), digits beyond N (abort + let the key fall through, never
   swallow), pane blur / file change / Source switch (abort silently), and
   screen-reader announcement of the pending state. Keep it a tiny explicit
   state machine in `248m` with three exits (digit → toggle + disarm, second
   `_` → legacy toggle + disarm, `Esc`/`Ctrl+[`/`q`/anything-else → abort).
   No timeout: explicit abort only, so the state never surprises.
5. **Footer placement.** The prompt says "the footer should change … to show
   hints." The global walker/status-bar footer is the wrong target: pending-`_`
   is per-note-per-view, and a global hint would leak across panes. Paint
   hints **card-locally**: number badges on each cabinet fold row plus one
   transient hint line in the card foot area (`_ 1 Areas · 2 Projects …
   (esc aborts)`, `role=status`). That *is* "the footer" from the user's point
   of view (the bottom of the card), with no cross-pane coupling. Fallback:
   badges alone when the foot is unmounted.
6. **Accessibility.** Every cabinet needs `aria-expanded`/`aria-controls`,
   labelled-by species noun, `y`-jump parity where rows carry source lines,
   and full keyboard parity (digits are Vim-gated; provide command-palette
   "Toggle cabinet N" commands and clickable rows for non-Vim users).
7. **Test surface.** Existing e2e (`test-ledger-tools-property-card-fold`,
   `obsidian-card-foot-e2e`, album-schema and bank-setup suites) plus new:
   cabinet↔H2 row parity, session fold persistence, pending-`_` matrix
   (digit/double-`_`/abort paths), Reading-view parity, and style snapshots.

## Adjustments to the requirements (marked A1–A5)

- **A1 — Unify chrome via the fold-row kit, keep `Properties · N`.** Migrate
  *both* widgets onto `propertyCardBuildFoldRow`: Schema keeps `Schema · …`,
  Properties keeps its `Properties · N` label and count, both gain the same
  padding/type/hover/keycap treatment. Do not invent a third style. The
  disclosure/drawer mechanics underneath stay untouched.
- **A2 — Pin Schema directly above Properties; content stacks above Schema.**
  On album notes: Records, Schema, Properties. On bank notes: Setup, Properties
  (Setup *is* the Schema cabinet, renamed per species: "Setup" on bank,
  "Schema" on albums). On hosts: Areas, Projects, Notebooks, Albums,
  Properties (no Schema). Bare `_` with exactly one non-property cabinet keeps
  today's instant toggle; with two or more it arms number hints. Second `_`
  while armed = legacy Schema toggle.
- **A3 — Abort keys: `Esc`, `Ctrl+[`, *and* `q`.** `241xc` already treats all
  three as "back out"; pending-`_` must accept all three, not just the two
  named, or Vim users will hit `q` and be stuck.
- **A4 — H2 callouts stay; rendered H2 hides when its cabinet mounts.**
  (The load-bearing correction above.) No `bob` planner changes, no vault
  migration, no `bob plugins sync` impact beyond the JS bundle.
- **A5 — Digits are single-key `1..N`, `N ≤ 6`.** The cabinet inventory is
  bounded (Areas, Projects, Notebooks, Albums, Records, Schema). No multi-digit
  sequences, no `0`, no timeout. Digits beyond N abort-with-fallthrough.

## Recommended solution (phased)

1. **Kit slice (one owner; gate review with `qm` + `qp`).**
   `propertyCardFoldTargets(view)` enumerates all live folds for the path
   (generalize `propertyCardFoldTarget`); pending-`_` state machine in `248m`;
   card-local hint line + badges; `Properties · N` re-skinned as a fold row;
   `aria`/palette parity; unit + e2e for the matrix. Land before `qp.4`.
2. **Pilot: Schema/Setup cabinet.** Re-house album Schema and bank Setup as
   cabinets above Properties with zero behavior change (same `_`, same
   problems-resurface logic, same `==` editors). Prove with `qi.6`'s bank
   pass and the album-schema suites. This validates the chrome and the
   single-cabinet fast path before content arrives.
3. **Content cabinets in parallel per species** (area/project, notebooks,
   albums/records painters projecting the existing reports; rendered-H2 hiding
   per cabinet). Each is independently shippable behind the existing
   capability gates (`props_v1`, `props_contract_v1`).
4. **Docs + memory.** Update `area-and-project-cards.md`, `albums.md`,
   `record-card.md`, `bank.md` card sections; add `glossary:cabinet` (draft
   below — requires a `/sase_memory_write` pass with reviewer authorization,
   since current epic decisions authorize only their named strands); cite
   `decisions:bank-hub-is-path-canonical-never-area` (bank cabinet scope),
   `decisions:notebook-routes-write-notes` (bob still owns `## Notebooks`
   content), and `decisions:decision-rules-are-read-at-planning-time`
   (roster-first planning).

## Glossary term: cabinet (draft)

> **Cabinet** (proposed; aka collapsible section)
>
> A collapsible content section at the bottom of a [[property-card]], below
> the title block and above the always-last Properties cabinet. Each cabinet
> projects one data set the note's H2 sections already contain — child areas,
> sub-projects, notebooks, albums, records — or the note's Schema/Setup, with
> identical rows and identical navigation. Cabinets are presentation only:
> `bob` keeps owning the H2 callout bytes, and Source, mobile, embeds, hover,
> canvas, and print keep showing the H2.
>
> Cabinets stack in vault-canonical order (Areas, Projects, Notebooks,
> Albums), then Records, then Schema/Setup directly above Properties.
> Properties (`-`) is always the bottom cabinet. Fold state is per-note and
> session-only: it survives refresh and collapse, never reaches frontmatter,
> and never survives reload. A healthy Schema/Setup folds by default and
> resurfaces on new problems, as today.
>
> In Live Preview Vim normal mode, `_` toggles the single non-property
> cabinet, or — with two or more — arms number hints (`1` = the cabinet
> directly above Properties, upward; badges on each row plus a hint line in
> the card foot; `Esc`, `Ctrl+[`, or `q` aborts, a second `_` toggles
> Schema/Setup). `==` still opens the species editor, `+` the Property
> Editor. Not a [[task-drawer]] (a task's child bullets), not an H2 section
> (the stored source), not a card (the panel itself).

## Verdict

Build it — presentation-only (A4), kit-slice first with `qm`/`qp` seam
reviews, Schema pilot with `qi.6`, content cabinets in parallel per species,
bottom-up `1..N` with card-local hints and `Esc`/`Ctrl+[`/`q` abort (A1–A3,
A5). The result is intuitive (one chrome, stable anchors, visible numbers),
reliable (session state, no vault writes, H2 intact everywhere cards do not
mount), and — with the unified fold-row styling, badges, and attention chips
carried over — the prettiest dense surface in the vault.


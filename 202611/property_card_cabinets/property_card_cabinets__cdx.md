# Property Card cabinets: design, safety, and parallel delivery

**Independent research by cdx · 2026-11-26**

**Recommendation:** build cabinets as a shared presentation feature in Bob Ledger Tools. Keep Bob's generated catalogs and their Markdown storage contracts, render their contents inside the owning Property Card, and suppress the original catalog presentation only while the replacement is safely mounted. Keep Properties last, place Schema immediately above it on albums, and use an explicit cabinet chooser for multi-cabinet cards.

This is a good idea. It can give every note a compact navigation surface and give authored content more room. The main risk is not styling: it is hiding content incorrectly, changing existing fold behavior, or allowing a numeric shortcut to act on a different cabinet from the one the footer advertised.

The work can develop alongside all four named epics. It needs limited coordination for shared integration and delivery, not a blanket dependency on four complete epics.

## Evidence and limits

I independently inspected:

- bob-cli at `d9c0d728257f30be38ebf9e4d85df08c12393eda`.
- bob-plugins at `3863bc46007c6287ac8eebfda37d68c42be951d0`.

I read the requested epic beads through the audited bead interface, their approved plans through the artifact interface, the decisions roster, and relevant glossary and decision memories. I did not read or seek another report or transcript from this research swarm.

The epic statuses below were observed during this session, around 19:20–19:33 UTC on November 26. They are a snapshot; implementation agents should refresh them.

Two existing bob-plugins suites passed:

| Command | Result |
| --- | --- |
| `node scripts/test-ledger-tools-property-card-fold.cjs` | 7 passed |
| `node scripts/test-ledger-tools-schema-double-equals.cjs` | 42 passed |

These validate the existing fold/key baseline. No cabinet implementation, live-vault survey, performance benchmark, or real-Obsidian acceptance run was performed. The visual examples below are proposals.

## 1. What exists, and what must survive

### The five catalogs have different semantics

“Same data” should preserve membership, ordering, nesting, visible information, links, and actions—not merely a row count.

| Cabinet | Current host and source | Preservation requirements |
| --- | --- | --- |
| Areas | Area notes with children, plus the area root; generated `[!areas]` under `## Areas` | Complete descendant forest, nested; summaries, tree folds, existing client readouts, and root/unplaced findings where applicable. It is not just immediate children. |
| Projects | Area/project hosts; `[!projects]` under `## Projects` | Direct children, including `root: true` children; open alphabetical order; lifecycle glyphs and criteria; Closed group ordered by closure; warning rows and existing actions. |
| Notebooks | Area/project hosts; `[!notebooks]` under `## Notebooks` | Ownership-bound subtree stopping at the next root; nested notebooks; descendant-project groups; summaries, counts, age and navigation. |
| Albums | Area/project hosts; `[!albums]` under `## Albums` | Direct albums followed by descendant-owner groups; identity, summaries, record counts, group chips, age, peeks and repair actions. |
| Records | Album notes; `[!records]` under `## Records` | Exact index grouping, ordering, labels, facets, tally and missing-status findings; existing group folds and subscription-specific decoration; empty-album teaching content. |

Sources: [Areas contract][areas], [Projects contract][projects], [Notebooks contract][notebooks], [Albums/Records contract][records], and the plugin renderers in the evidence index.

An easy mistake: the Records index order and record walk order are distinct. `walk_by` does not automatically redefine the index. Cabinets must retain the index's order rather than rebuild it from the walk. [Records contract][records]

The existing Notebook Card's child-notebook chips are also distinct from an owner's generated Notebooks catalog. This request does not justify changing `qm`'s notebook body or adding owner-style catalogs to every notebook.

### Storage ownership is narrower than an H2 section

Bob's shared host-region engine owns the callout bytes. The heading, its position after initial insertion, and surrounding authored text belong to the user. An existing matching H2 can be adopted; subsequent syncs patch the callout. Empty headings are removed only when their sections are otherwise blank. [Region engine][regions]

Therefore “hide everything between `## Albums` and the next H2” would be unsafe. A user can put prose there. A heading with the right name can also occur without a generated catalog.

This is the strongest argument for a rendering-first change. Physically removing headings would touch writers, capture protections, migrations, snapshots, and section consumers, while conflicting with the current ownership contract. Governing `decisions:notebook-routes-write-notes` explicitly preserves the catalog's authored placement.

### Properties and Schema already share some infrastructure

- Properties has a lazy foot and a separate state/mount registry. Its openness is keyed by normalized note path, shared across mounts, and reset on plugin reload. `-` requires a valid mount in the active view. [Foot runtime][foot-state]
- Album Schema and Bank **Setup** already use `propertyCardBuildFoldRow`. Bank's label is Setup because it contains categories, accounts, rules, and findings. Preserve that useful label. [Schema renderer][schema-dom], [Setup renderer][bank-dom]
- Properties is an inline disclosure in the foot; Schema/Setup use full-width rows. Shared header chrome can unify them without rewriting their bodies. [Card styles][styles]
- `_` already folds album, bank, record, area and project details; the in-progress notebook, prose and ref cards depend on it too. The fold registry is keyed by species and its target finder returns the first eligible control. It cannot safely represent several independent cabinets without an extension. [Fold runtime][fold], [Key dispatcher][keys]

The current `-`/`_` dispatcher guards insert/visual/replace modes, pending Vim operators, counts/registers, composition, modified keys, repeats and inappropriate targets. Preserve these protections.

## 2. Critique: where this helps, and where to resist it

The benefit is spatial: related navigation lives beside the note identity, and the note body becomes easier to scan. A closed row can still communicate “Projects · 4 open · 2 closed.” Consistent Schema and Properties controls can make the card feel composed.

The costs:

1. **Disclosure hides navigation.** On an album, Records is the primary content. Closing everything initially would make albums worse.
2. **An expanded card can be enormous.** A wrapper does not make a large catalog cheap to render.
3. **The prefix adds a mode.** An unnoticed mode or changing number map is worse than an extra click.
4. **H2 links and search can lose their destination.** Moving presentation must preserve access to source.
5. **Styling can become an uncontrolled redesign.** Focus on disclosure chrome, catalog placement and routing.

Choose independent disclosures, with several allowed open. A one-open-at-a-time accordion would hinder comparing notebooks and albums. Tabs hide more context and do not match Properties. A new cabinet fence, YAML schema, or `bob cabinets` command is unnecessary for v1.

## 3. Recommended appearance and hierarchy

Keep identity, title, summary, essential status and the species navigation rail where they belong. Append collection cabinets below the species body, outside its fold, and above Properties.

Use this relative order, omitting inapplicable entries:

**Existing species details → Areas → Projects → Notebooks → Albums → Records → Schema/Setup → Properties.**

The existing species detail region can keep its compact chevron and layout through a compatibility adapter. Folding it must never hide the new cabinet headers. On albums and bank, Schema/Setup itself is the existing region: do not create a second Details cabinet.

An area/project lower card during selection:

~~~text
  [existing identity, status and Details control above]

  ▸ Areas          8 areas                              4
  ▸ Projects       4 open · 2 closed                     3
  ▸ Notebooks      7 notebooks                           2
  ▸ Albums         3 albums                             1
  ───────────────────────────────────────────────────────
  ▸ Properties     12                               −   +
                                      created Nov 12
~~~

If its existing Details control is also present, it receives `5`, with the same badge on that control and a “5 Details” footer hint. This preserves access to today's `_` action.

An album:

~~~text
  ALBUM · Places
  Restaurants
  Places worth returning to.

  ▾ Records        24 restaurants                       2
    [existing groups, record links, facets and actions]

  ▸ Schema         6 fields · walks by Status            1
  ▸ Properties     9                                −   +
                                      created Nov 12
~~~

Digits are chooser hints, not permanent shortcuts. Here `_ 1` opens Schema and `_ 2` folds Records.

### Visual rules

Use one header component for collection cabinets, Schema, Setup and Properties:

- Consistent left chevron, semibold noun, quiet count/summary, aligned trailing key hint.
- Common row height and padding, with a clear focus ring.
- Existing theme variables and card accent; no new palette for cabinet kinds.
- Thin separators or spacing instead of nested boxes. Remove duplicate catalog title chrome when the cabinet header supplies it.
- Preserve useful row chips and hierarchy inside the body. Do not embed another full Property Card.
- Make the disclosure a generous button. Independent actions such as Add property or Sync are sibling controls, never nested buttons.
- Key hints appear on hover/focus and stay visible during selection. Counts use tabular figures and unambiguous units.
- In narrow panes, wrap summaries below nouns while retaining names and choices.
- Use restrained or no height animation. Respect reduced motion and avoid animating a huge Records body.
- Expansion reveals the header if necessary without moving the editing cursor or centering the whole body. Collapse does not unexpectedly scroll.

Use real buttons with `aria-expanded` and unique per-mount `aria-controls` targets. Enter/Space toggle the focused header. Hidden contents leave the tab order; collapsing a body containing focus returns focus to its header. These follow the [WAI disclosure pattern][wai-disclosure]. Avoid making every body a landmark; the [accordion guidance][wai-accordion] warns about excessive regions.

### Defaults

| Cabinet | Initial behavior |
| --- | --- |
| Areas, Projects, Notebooks, Albums | Closed; existing useful totals and attention remain in the header. |
| Records | Open, including empty-album teaching content. |
| Schema/Setup | Preserve current healthy/problem-aware defaults and explicit user choice. |
| Properties | Preserve the closed default and `-` behavior. |
| Existing species details | Preserve the defaults selected by the existing card epic. |

Omit genuinely empty optional catalogs. Missing reports do not mean zero. Do not remove a valid cabinet just because a background refresh starts.

Errors remain visible in header/attention chrome. Reuse existing problem-signature handling: a new blocking problem may resurface Schema/Setup, but an explicit collapse for the current problem remains respected. [Fold runtime][fold]

## 4. Exact keyboard contract

Count actionable, top-level non-property regions on the active mounted card. Nested area folds, Closed projects, record groups and Managed properties do not receive cabinet numbers.

| Context/input | Result |
| --- | --- |
| `-` | Toggle Properties directly; first dismiss any cabinet chooser. |
| `_`, zero targets | Fall through to existing editor behavior. |
| `_`, one target | Toggle immediately; no chooser. |
| `_`, several targets | Enter selection; toggle nothing yet. |
| Valid digit | Toggle the advertised cabinet, then leave selection. |
| Esc or Ctrl+[ | Cancel without toggling. |
| `q` | Cancel through the same path, outside text entry. |
| `_` again | Cancel. |
| Unassigned digit | Consume it and retain selection with “Choose 1–N.” Never leak it into a Vim count. |
| Other ordinary command key | Cancel and let the original event continue normally; do not synthesize another event. |
| Pane/file/mode change, modal opening, relevant mount loss or unload | Cancel and release hints/listeners. |

Adding `q` deliberately follows `decisions:q-and-ctrl-bracket-mirror-esc`. Ctrl+[ means Ctrl alone.

The initiating `_` keeps today's clean normal-mode guard. Selection handling must precede the ordinary bare-key filter, because its keys are now numbers or cancellation keys. De-duplicate the same event delivered to window and document. Repeat never toggles twice; composition must not be captured. Do not use a short timeout that penalizes someone reading the choices.

### Stable bottom-up numbering

Properties is last and unnumbered. The closest actionable non-property region above it is `1`; proceed upward, skipping absent targets without gaps.

At entry, capture ordered semantic IDs, active view/file, and card mount identity. The footer, header badges and dispatch must all use that snapshot.

- Count/summary refreshes do not renumber an active chooser.
- Membership/order changes or replacement mounts cancel with a brief “Cabinets changed; press _ again.”
- Never reinterpret `3` as the third DOM node found at keydown.
- IDs are semantic—`areas`, `projects`, `notebooks`, `albums`, `records`, `schema`, `setup`, `details`, `properties`—not labels or ordinals.
- V1 has fewer than ten targets. If extensions ever exceed nine, use an explicit picker rather than ambiguous multi-digit input.

This is a selector, not a memorized number language. The same number can mean different things on different notes, so visible hints are mandatory.

### Footer behavior

~~~text
Cabinets   1 Albums   2 Notebooks   3 Projects   4 Areas   5 Details   Esc cancel
~~~

Show the open/closed state with a small chevron and make footer choices clickable. Badge the matching controls on the card.

Implement a temporary override of Bob's hint surface. Preserve walk mode and attention state. On exit repaint the latest normal footer rather than restoring old HTML. Background walk refreshes must not overwrite the chooser.

When the status bar is hidden or unavailable, show the same choices in a small view-local strip. Do not enter an invisible mode. Long labels can wrap there; never drop choices to fit.

Bare shortcuts remain Live Preview Vim normal-mode gestures. Reading and non-Vim users get buttons and a command-palette action routed to the same selection logic. Do not intercept `_` inside arbitrary text controls.

## 5. Architecture

### A. Extend the fold kit

Add a mount-scoped cabinet registry in new fragments. Each entry needs approximately:

~~~text
id, label, order, sourcePath, owner/mount token
headerElement, bodyId, isOpen(), toggle()
optional source ranges and content generation
~~~

Separate state, rendering and actions. One registry snapshot drives eligibility, numbering, hints and dispatch.

Retain `propertyCardRegisterFoldKind` as a compatibility facade for current one-region-per-species callers. Their existing details become a named target. Keep the property foot API as the Properties adapter. Avoid forcing `qm` and `qp` to rewrite their hosts.

Use per-note, per-cabinet session openness for new outer cabinets, matching today's Properties memory. Same-note panes may mirror openness intentionally; selection, ownership, focus and reveal stay view-specific. Preserve existing per-pane inner tree/group folds. Nothing is stored in frontmatter.

Per-mount disclosure IDs stay unique even when note-level openness is shared. Cleanup is generation-bound so an obsolete renderer cannot unregister its replacement.

### B. Reuse existing contents and services

Current catalog code decorates Obsidian callouts and subscribes to shared reports; some also builds standalone status/content surfaces. It is not already one universal list component. Expect a measured extraction of content builders, not a single DOM append. [Renderer evidence](#source-and-contract-index)

Adapters should:

1. Locate and classify the generated source region.
2. Build the same body from existing row logic and confirmed cached report data.
3. Mount it in the cabinet shell.
4. Claim replacement ownership only when the complete content model and header are ready.
5. Leave the original visible whenever that claim cannot be established.

For intact source catalogs, preserve stored links, nesting and order even if optional report enrichment is unavailable. For report-only recovery/status views, preserve existing repair semantics. Never invent an empty/current catalog from missing input.

Lazy body DOM is useful, but hiding source requires an already complete, validated content model. If construction fails on expansion, immediately release source suppression.

Painting, folding, selecting, resizing and restoring state must add zero vault writes and zero bob subprocesses. Existing services continue to own report refresh. Sync/Retry remains an explicit action.

### C. Give catalog suppression its own ownership contract

Frontmatter/title ownership and generated-body ownership are different. Borrow the current coordinator's successful-mount, valid-evidence and scoped-release approach, without treating its frontmatter class as permission to hide body text. [Ownership coordinator][ownership]

A replacement claim should carry file/view identity, exact source span, source generation/fingerprint, mount generation, any safely hideable heading span, and a release function.

The invariant is: **a valid original catalog is never hidden without a working cabinet representation for that view.**

| Situation | Result |
| --- | --- |
| Valid generated block and cabinet | Cabinet shown; exact original block suppressed. |
| H2 contains only that block and whitespace | Hide redundant rendered H2 too. |
| H2 contains authored prose, other blocks or meaningful anchors | Preserve heading and authored content; move only generated presentation. |
| Matching H2 without a recognized owned block | Leave it alone. |
| Malformed, ambiguous or duplicate region | Keep affected source and diagnostics; do not guess a hide range. |
| Capability pending, failed mount or stale source evidence | Original remains or returns. |
| Source, embed, hover, canvas, print, unsupported mobile or disabled plugin | Native/source presentation remains available. |
| Cursor/selection enters the owned span | Reveal source and temporarily relinquish that region's replacement presentation. |

Live Preview should use CodeMirror decorations; never reparent/delete editor-managed DOM. Hiding multiline blocks changes layout beyond the current viewport, so use directly supplied StateField decorations, not a viewport-only pass. This follows [Obsidian's decoration guidance][obsidian-decorations].

Reading view needs a source-aware claim as well: postprocessors can receive different sections separately. A blind nearest-H2 query is insufficient. The cabinet must not depend on the old block having scrolled into the DOM.

Keep the original note path as the base for links, modifier-click and hover. Bind any Markdown-rendered body to the card's lifecycle and prevent recursive catalog takeover of that body.

### D. Keep heading links and Find useful

Existing `[[note#Projects]]`/`#Records` links, Outline navigation, Find and cursor movement must still reach content.

Prefer opening and revealing the corresponding cabinet. If a navigation path cannot be intercepted reliably, reveal source at that destination. Keep Markdown anchors.

Obsidian's source-driven Outline may still list stored catalog headings in v1. This is an explicit consequence of preserving fallback Markdown. Its destinations must work even while duplicate rendered headings are hidden.

### E. Large catalogs

Never discard rows to keep a card short. Retain group folds and defer collapsed DOM work. Prefer document scrolling to nested scroll traps. Measure a large Records index and deep Areas tree in fixtures before choosing virtualization. Any later windowing must retain complete search, links and keyboard access.

### F. Untyped area-root exception

The area root has no frontmatter requirement and can be untyped, yet host Areas. A cabinet cannot attach to a Property Card that does not exist. [Areas contract][areas]

For v1, retain existing catalogs on hosts without eligible Property Cards. Do not type the root as an Area or restore bank-as-Area behavior to force coverage. If the root must participate, make a dedicated directory/hub card an explicit additional requirement. This is a visible coverage exception.

## 6. Parallel delivery

### Observed status and overlap

| Epic | Observed state | Handling |
| --- | --- | --- |
| `bob-cli-qi` — bank hub demotion/card finish | 1–5 closed; 6 in progress | Preserve landed single-owner bank and takeover work. Coordinate styling, passive tests, family glossary/docs with finish. Catalog model work is independent. |
| `bob-cli-qj` — article → prose | 1–2 closed; 3–5 in progress | No runtime dependency for the requested catalogs. Preserve both prose spellings. Retaining source avoids changing generated-section classification for its future extract/inline work. |
| `bob-cli-qm` — Notebook/Prose Cards | 1–2 closed; 3–7 in progress | Overlaps kit, folds, bundle, harness, family glossary. Preserve species and preview gates; avoid rewriting notebook/prose bodies. |
| `bob-cli-qp` — Ref Cards | 1–8 in progress | Overlaps kit, compaction, preview gate, bundle and family docs. Its Rust reference contract and report service remain independent. |

Approved shared inputs: `plan:202611/bank_hub_demotion.md`, `plan:202611/prose_note_type.md`, `plan:202611/prose_and_notebook_cards.md` and `plan:202611/ref_cards.md`.

Catalog relocation is explicitly outside qi/qm scope. Treat this as sibling work, not an unfinished obligation of those epics.

### Narrow coordination beats a global barrier

Separate fragments still share a key handler, footer, stylesheet, fragment order, generated bundle and family glossary. Conversely, a reference writer or prose rename should not block a source-region parser.

Use three agreements:

1. **One shared integrator.** Own fold facade, key dispatch, catalog-ownership bridge, shared header CSS and footer override in one phase. Other workers use new files and narrow adapters. Keep current public entrypoints compatible.
2. **One small registration contract.** Publish descriptor, order and cleanup rules first. Use a cabinet-specific preview switch, independent of qm's temporary gate which qm.7 deletes. Do not refactor species detection or hardcoded species lists in this work.
3. **One final integration window.** Rebase, regenerate and run family acceptance on named SHAs. Coordinate harness changes and deploys so no other acceptance run tests a moving plugin.

Suggested work shape:

~~~text
cabinet model + shell
          |
          +--> source adapters + catalog content builders
          |
          +--> selector + footer hints
          |
          +--> Schema/Setup/Properties styling adapters
                         |
                 integrated acceptance
                         |
                activation + documentation
~~~

After the small descriptor contract, these branches can develop concurrently. One worker per catalog is not necessarily optimal: Notebooks and Albums share infrastructure, so grouping them reduces duplicated extraction work. Keep shared registry/dispatcher edits with one integrator.

The existing chain already serializes family delivery: qp acceptance waits for qm.6; qp go-live waits for qm.7; qm go-live waits for qi.6 and qj.4. Do not reverse those edges and create a cycle.

**Recommended landing policy:** develop and validate cabinets immediately behind their own preview switch. Serialize only the final default-on cutover and shared glossary/docs reconciliation after the sibling acceptance/go-live chain settles. That is a final-phase gate, not a launch dependency for all cabinet work. If the chain delays, the implementation can still finish and be reviewed under the preview switch.

| Shared surface | Treatment |
| --- | --- |
| `240s` folds, `248m` keys, new fragments | One integrator, compatible adapters and unchanged old-caller tests. |
| `240o/240p/240r` foot | Preserve API and note-session semantics; extract common header chrome only. |
| `240q` ownership | Separate catalog bridge; avoid changing species eligibility. |
| CSS, fragment manifest, exports, tests, manifest version | Reapply authored additive changes after rebase; rebuild bundle and re-bump per convention. Never hand-merge generated `main.js`. |
| Acceptance harness | Cabinet sibling runner importing shared library; no fork or concurrent shared-fixture deploy. |
| Family docs and `glossary:property-card` | One final reconciler preserves qi/qm/qp additions. |

No Bob Mac Capture change, new CLI capability, or daily CLI release wait is needed for this presentation-only design. Plugin deployment still uses `bob plugins sync` and its overwrite-protection procedure.

## 7. Requirement adjustments, explicitly proposed

| Adjustment | Reason |
| --- | --- |
| Retain H2/callout Markdown; replace its presentation on supported cards. | Preserves ownership, writers, source recovery, export and disabled-plugin readability. This does not literally delete H2s from files. |
| Preserve authored content and its headings. | Heading names do not establish ownership. Some H2s will legitimately remain visible. |
| Records initially open; optional navigation catalogs initially closed. | Records is an album's primary content. |
| Keep bank label Setup. | Same styling need not erase a useful distinction in content. |
| Preserve existing detail/outline/compaction targets. | `_` already means more than Schema, including the new cards in qm/qp. |
| Add `q` cancellation. | Existing accepted close-key policy. |
| Add matching header badges and fallback hint strip. | Numeric selection must remain visible and complete. |
| Preserve native catalogs without an eligible card, notably untyped area root. | Avoid inventing note types or silently extending the host model. |
| Session-only openness. | Matches Properties and avoids synced UI preferences or note writes. |

If literal H2 removal is firm, split it into a subsequent format-migration effort after the UI is proven. That would require writer changes, guarded migration/ownership rules, anchor compatibility, capture/extract exclusions, snapshot coverage and rollback. It is not a small variation of this UI change.

## 8. Proposed glossary term

Add `glossary:cabinet` at implementation go-live, keyword **Cabinet**, alias **card cabinet**. Draft:

> A named, independently collapsible region of a [[property-card]]. Its header stays visible and tells you what is inside; opening it reveals that content without changing the note.
>
> Collection cabinets bring the note's generated Areas, Projects, Notebooks, Albums or Records catalog into the card, keeping its rows, grouping and actions. Schema on an [[album-card]], Setup on a [[bank-card]], and Properties use the same disclosure style. Properties is always the bottom cabinet and opens with `-`.
>
> `_` toggles the sole non-property cabinet, or, when several exist, shows a numbered chooser. Numbers run upward from `1` just above Properties; choosing one toggles it, and Esc, `q` or Ctrl+`[` cancels. Existing card detail folds participate in that choice.
>
> Cabinet state is temporary view behavior. Generated Markdown remains the fallback when Bob cannot safely present the cabinet. A cabinet creates no file, parent relationship or task structure.

Link the final user documentation from the strand. “Properties cabinet” names a member, and “drawer” should not become a generic alias because Task Drawer already means something else.

This report proposes the wording; it does not publish unimplemented behavior into durable memory. The user expressly requested the term. An implementation plan should use the memory-write workflow for this addition and necessary corrections to existing card/key descriptions. Reconcile with the active epics, then regenerate memory/documentation outputs once.

## 9. Acceptance before default-on

Source handoff and event routing are the high-risk tests. Screenshots alone cannot prove reliability.

| Concern | Evidence |
| --- | --- |
| Content parity | Same paths, labels, nesting, order, lifecycle/group states, facets, counts and actions across all five catalogs; include empty Records and subscription decoration. |
| No loss | Authored prose, duplicate headings, legacy notebook markers, malformed blocks, fenced examples, BOM/CRLF, unsupported hosts, stale/missing reports stay readable. |
| Ownership | One representation per claimed catalog. Failure, Source and unload restore original. Two panes cannot release one another's newer mounts. |
| Navigation | Heading links, Outline, Find and selection either open cabinet or reveal source. Hover/modifier-click preserve source base path. |
| Keyboard | 0/1/many; bottom-up order; valid/invalid digits; cancel aliases; repeat/IME; Vim counts/registers/operators; insert/visual/Source; modals; panes; target removal; no number remapping during selection. |
| Existing cards | `-`, `==`, `+` and single-target `_` remain correct across all current and incoming species. |
| Passive behavior | Repeated paints, folds, chooser entry/cancel, resize and report arrival add zero writes or spawns. Explicit Sync/Retry counted separately. |
| State/focus | Openness survives normal remounts; same-note mirroring intentional; no cursor changes; hidden focus recovered; stale mounts untargetable. |
| Visual quality | Light/dark, narrow/wide, LP/Reading, large data, errors, forced colors and reduced motion. Schema/Properties align; no duplicate feet/title rows or nested boxes. |
| Real application | Isolated fixture vault with exact binary/plugin provenance, Node suites plus real-app acceptance. No live vault as automated fixture. |

Reuse the existing fold, foot, keys, ownership, catalog and passive suites. Add tests at semantic boundaries, not tests that merely reproduce the implementation.

No new Rust tests are needed if no Rust changes. If an implementation discovers a truly missing report contract, surface that scope change explicitly.

## Source and contract index

Pinned source links:

- [Host catalog ownership/placement][regions].
- [Areas and root exception][areas], [Projects][projects], [Notebooks][notebooks], [Albums/Records][records].
- [Fold runtime][fold], [key dispatch][keys], [Properties state/mount registry][foot-state].
- [Frontmatter coordinator][ownership].
- [Schema][schema-dom], [Setup][bank-dom], [styles][styles].
- Catalog adapters: [Areas][areas-renderer], [Projects][projects-renderer], [Notebooks][notebooks-renderer], [Albums][albums-renderer], [Records][records-renderer].

Audited project evidence:

- `bead:bob-cli-qi`; `plan:202611/bank_hub_demotion.md`.
- `bead:bob-cli-qj`; `plan:202611/prose_note_type.md`.
- `bead:bob-cli-qm`; `plan:202611/prose_and_notebook_cards.md`.
- `bead:bob-cli-qp`; `plan:202611/ref_cards.md`.
- `decisions:notebook-routes-write-notes`: catalog content/placement boundary.
- `decisions:q-and-ctrl-bracket-mirror-esc`: cancellation aliases.
- `decisions:bank-hub-is-path-canonical-never-area`: bank identity.
- Glossary: Property Card, Area Card, Project Card, Album Card, Record Card, Bank Card, Notebook, Walker Footer.

External primary guidance: [WAI Disclosure][wai-disclosure], [WAI Accordion][wai-accordion], [Obsidian decorations][obsidian-decorations]. These support control semantics and editor architecture; product defaults and delivery sequencing are my design judgments.

[areas]: https://github.com/bobs-org/bob-cli/blob/d9c0d728257f30be38ebf9e4d85df08c12393eda/docs/areas.md
[projects]: https://github.com/bobs-org/bob-cli/blob/d9c0d728257f30be38ebf9e4d85df08c12393eda/docs/projects.md
[notebooks]: https://github.com/bobs-org/bob-cli/blob/d9c0d728257f30be38ebf9e4d85df08c12393eda/docs/notebooks.md
[records]: https://github.com/bobs-org/bob-cli/blob/d9c0d728257f30be38ebf9e4d85df08c12393eda/docs/records.md
[regions]: https://github.com/bobs-org/bob-cli/blob/d9c0d728257f30be38ebf9e4d85df08c12393eda/src/native/host_catalog/region.rs
[fold]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/240s-plugin-property-card-fold.js
[keys]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js
[foot-state]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/240p-plugin-property-card-foot-state.js
[ownership]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/240q-plugin-property-card-frontmatter-ownership.js
[schema-dom]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241x-plugin-album-schema-dom.js
[bank-dom]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/248b-plugin-bank-setup-dom.js
[styles]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/styles.css
[areas-renderer]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241aj-plugin-areas-catalog.js
[projects-renderer]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241ae-plugin-projects-catalog.js
[notebooks-renderer]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241d-plugin-notebook-catalog.js
[albums-renderer]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241q-plugin-album-catalog.js
[records-renderer]: https://github.com/bobs-org/bob-plugins/blob/3863bc46007c6287ac8eebfda37d68c42be951d0/plugins/bob-ledger-tools/src/241s-plugin-album-records-dom.js
[wai-disclosure]: https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/
[wai-accordion]: https://www.w3.org/WAI/ARIA/apg/patterns/accordion/
[obsidian-decorations]: https://docs.obsidian.md/Plugins/Editor/Decorations

## Recommended solution

Implement one shared cabinet shell and mount-scoped selector, with specialized adapters for the existing five catalog renderers. Keep Properties at the bottom, album Schema immediately above it, and Bank Setup in the same visual family. Preserve existing detail folds through compatibility adapters; choose multiple targets with a frozen bottom-up number map and explicit cancellation.

Deliver a sibling effort with parallel core, content and keyboard work, concentrating coordination in shared integration, real-app acceptance and final documentation. Retain generated Markdown and show it whenever replacement ownership is uncertain. With Records open initially and complete catalog data preserved, this creates a cleaner front door while keeping Bob's source and recovery model reliable.

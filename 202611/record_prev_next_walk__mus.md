# Record-note prev/next walk: `<` / `>` links + `N of M`

Researcher: `mus` (independent swarm report, `__mus` suffix).
Request: auto-add `<` / `>` links to every record note pointing to the
previous/next record in its album, working with `[n` / `]n`, alphabetical with
wrap-around, plus `N of M` near the links. Lead the design: intuitive,
reliable, beautiful.

## Verdict

Yes, do it — but with two adjustments to the request as written:

1. **Emit `‹` / `›` (U+2039/203A), not ASCII `<` / `>`, as the link labels.**
   The `[n` / `]n` walker treats them identically, and `‹` `›` match Bob's
   existing idiom and render better. Accept `<` `>` on read (they already
   walk); normalize to `‹` `›` on write. Details in §4.
2. **Put one managed nav footer line at the end of the record body, not the
   top.** This keeps the record sheet (top of body) visually clean, keeps
   `[n` / `]n` working (it scans the whole body for the first match), and
   gives the classic bottom-of-article prev/next placement. Details in §5.

With those adjustments the feature works with **zero plugin changes** on day
one, then graduates to sheet/footer integration later.

Recommended solution is in §8.

## 1. What exists today

### 1.1 Records and albums (bob-cli)

- Album note: vault-root `type: "[[album]]"`, stem = folder + capture route,
  schema under `record:` (`docs/records.md`, `src/native/albums/*`,
  `src/native/records/*`).
- Record note: `<album>/<stem>.md`, frontmatter `type: "[[record]]"`,
  `parent: "[[<album>]]"`, `title:`, schema fields, `created:`. Body holds
  `## Notes` only when there are ordinary bullets, plus named `##` sections;
  a note with neither ends right after `---` (`render_record_with_identity`
  in `src/native/records/render.rs`). There is deliberately **no H1**; the
  sheet renders the title.
- Album index: bob-owned `[!records]` callout on the album note; rows are
  `[[<album>/<stem>|<title>]]` in `title_order`: case-insensitive title,
  path tiebreak (`title_order` in `src/native/albums/grouping.rs`). Groups,
  `index_by` subgroups, peeks, and `needs_status` all share that member
  order. Owner `## Albums` catalogs never list records.
- Writers: `bob records new|update`, capture `@album/` routes (same planner),
  `bob records tidy`, `bob albums sync` (indexes + catalogs, one commit).
  `bob records check|list` are read-only.

### 1.2 The `[n` / `]n` walker (bob-plugins, no checkout needed beyond read)

- `open-prev-link` / `open-next-link` (`openLabeledBodyLink(label)` in
  `plugins/bob-navigation-hotkeys/src/670-plugin-stacks-and-moves.js`-family,
  registered in `src/490-plugin-lifecycle.js`) scan the **active note's body
  source**: frontmatter and fenced code are skipped, lines scanned top to
  bottom, first matching link wins (`findFirstRenderedLink` /
  `findFirstRenderedLinkInLine` in `src/680-plugin-link-parse.js`).
- Label rule (`renderedLinkMatchesNavLabel`): exact `prev`/`next`, **or**
  prev starts with `‹`/`<`, next starts **or ends** with `›`/`>`. So all of
  `<`, `>`, `‹`, `›`, `‹ Title`, `Title ›`, `prev`, `next` walk today.
  A single line carrying both links works: for `prev` the `<` link matches
  first; for `next` the `<` link is skipped and the `>` link matches.
- `[[` / `]]` repeat the last bracket family (`s`/`w`/`n`); `n` ignores
  counts (`src/546-plugin-bracket-repeat.js`, `docs/reference/plugins/bob-navigation-hotkeys.md`).
- The links-walker footer (`plugins/bob-ledger-tools/src/124-links-walker-footer.js`,
  via nav `api.links` in `src/482-walk-mode-nav-api.js`) already renders
  `‹ name` / `name ›`, strips arrows for names, and reports "no ‹ / › links"
  when absent. Period notes already use this idiom (`‹ 2025-W52`,
  `2027-W01 ›`, `docs/periods.md`).

Consequence: **any source body line with two arrow-labelled wikilinks is
immediately walkable.** No plugin change is required for v1.

### 1.3 The record sheet (bob-ledger-tools)

- `docs/record-card.md` (`$LP/docs/record-card.md`): the sheet paints at the
  **top of the body** in Reading/LivePreview (desktop, capability-gated);
  Source keeps native YAML. Collapse/fold state is per-path session state,
  never frontmatter. On `subscriptions/*` the money strip docks on the sheet.
- Implication: a source nav line at the **top** would sit directly under (or
  above) the sheet in Reading view — two headers competing. A **bottom**
  footer avoids this entirely.

## 2. Critique: is auto-linking a good idea?

**Good parts.** Discoverability (records are currently islands; the album
index is the only ordering), keyboard-first browsing via an existing,
memorized gesture (`[n`/`]n`, `[[`/`]]`), orientation via `N of M`, and a
cheap implementation (writer-only v1, no plugin gate, works on mobile web
the same as desktop because it is just Markdown).

**Costs (do not underestimate).**

- **Churn / second source of truth.** Order lives in the album index today.
  Stored prev/next duplicates it per note. Every insert, delete, title
  change (reorders!), or stem change rewrites up to ~5 notes (self + old
  neighbours + new neighbours), each a vault write + git commit. Albums with
  dozens of records will show constant `records: relink` commits.
- **Staleness.** External edits (hand delete/rename in Obsidian, mobile sync,
  `vault-sync` merges) leave stale targets until the next repair. Stale
  wikilinks still resolve-or-notice gracefully (`openOrCreateLinkCandidate`),
  but `N of M` goes wrong silently.
- **Graph/backlink pollution.** Each record gains two outgoing wikilinks;
  the album folder becomes a ring in Graph + Backlinks. Acceptable, but
  Dataview queries counting outgoing links must filter the nav line.
- **The album index already orders.** A purist would say: walk the index,
  not the notes. True — but `[n`/`]n` cannot walk the index today, and
  changing nav to resolve neighbours computationally is a bigger,
  cross-repo change. Stored links are the pragmatic v1.

**Alternatives considered and rejected for v1.**

- *Computed nav (no stored bytes):* nav resolves neighbours at walk time
  from the cached `bob albums list -f json` report. Zero churn, never stale.
  But it needs a nav-plugin change, a report-caching contract, and a story
  for offline/missing reports. **Right long-term direction; wrong v1.**
- *Frontmatter `prev:`/`next:`:* hidden from `[n`/`]n` (frontmatter is
  skipped), invisible in Reading, needs plugin rendering anyway. Worse than
  a body line on every axis.
- *Index-only (no per-note nav):* zero churn, but no `[n`/`]n`, no `N of M`
  on the note, no offline walk. Fails the request.
- *Dataview custom view:* runtime-only, plugin-dependent, breaks Source
  mode and mobile. No.

Conclusion: **stored footer line v1, computed sheet/footer integration as the
explicit follow-up** (§8). The request is sound; the adjustments below make
it reliable and beautiful.

## 3. Requirements audit

| # | Requested | Assessment |
| --- | --- | --- |
| 1 | `<` and `>` links prev/next on all record notes | Accept with label adjustment: write `‹`/`›`, accept `<`/`>` on read (§4). |
| 2 | Work with `[n` and `]n` | Holds by construction if links are body wikilinks with arrow labels (§1.2). Add plugin regression tests, no plugin code change for v1. |
| 3 | Alphabetical, cycling; 2-record album links both ways | Adopt, but define alphabet as **album index order** (`title_order`), not stem or `created` (§5). Cycle for M≥2; M==1 gets no nav line (§6). |
| 4 | `N of M` near the links | Adopt: middle segment of the same line, plain text `N of M` (§5). |
| 5 | Intuitive, reliable, beautiful; researcher leads design | Addressed in §§4–8. |

## 4. Label design: why `‹` `›` instead of `<` `>`

The walker accepts both (`680-plugin-link-parse.js:5-17`), so this is a pure
rendering/a11y choice:

- **Consistency.** Footer renders `‹ name` / `name ›`; periods render
  `‹ 2025-W52` / `2027-W01 ›`. ASCII `<` `>` would introduce a second arrow
  dialect for the same gesture.
- **Beauty/legibility.** At body text size `‹` `›` read as navigation
  chevrons; `<` `>` read as code/HTML and are ~30% narrower touch targets.
  A lone `<` at a line start also invites "broken HTML" misreads in Source
  mode and in external Markdown renderers.
- **Safety.** `<`/`>` inside aliases are fine in Obsidian, but `‹`/`›` never
  collide with HTML/tag semantics anywhere in the toolchain (docs site,
  web-clip defuddle bundle, RSS).
- **Compat.** Notes already containing `<`/`>` keep walking; the writer
  normalizes them to `‹`/`›` on next touch. `check` should not flag ASCII as
  an error (warning at most, or silent migration).

Single-glyph vs titled links (`‹ Ramen Nagi` / `Ninja Sushi ›`):

- Titled links are more informative and more accessible (a lone `‹` has no
  accessible name beyond "link"), and the footer already strips arrows to
  names. But titles duplicate neighbour titles into every note's source, so
  **every retitle rewrites two neighbours' aliases** and long titles wrap
  the footer line.
- Recommendation for v1: **single-glyph `‹` / `›`** (stable under retitle,
  one short line, matches "good `<`/`>` links" intent at the same weight).
  Keep titled neighbours as an explicit non-goal; revisit with sheet
  integration where titles can be rendered computationally without stored
  churn.

## 5. Placement and format (the core spec)

**One managed footer line at the end of the body:**

```markdown
[[eat/ramen-nagi|‹]] · 2 of 12 · [[eat/ninja-sushi|›]]
```

Rules:

- **Position: last body line, end of file.** Preceded by exactly one blank
  line. For frontmatter-only notes the body becomes just this line. Never in
  frontmatter (walker skips it), never inside a fence, never a bullet, never
  a heading. Rationale: first-match-wins means position is functionally
  free; bottom avoids sheet collision (§1.3), reads as a footer, and keeps
  `## Notes` diffs clean.
- **Targets: vault-relative `album/stem`, no `.md`, no heading/block
  suffix.** Same target shape as album index rows. Alias is exactly `‹` /
  `›` (writer normalizes `<`→`‹`, `>`→`›`, `prev`/`next`-labelled links are
  left for the footer to disambiguate but rewritten on next touch).
- **Middle: plain `N of M`** (`N` = 1-based position in walk order,
  `M` = record count in walk membership). Separators ` · ` (U+00B7 with
  spaces), matching period/daily nav lines. `N of M` is inert text, so it
  never matches either direction. Do not put `N of M` inside a link label:
  `‹ 2 of 12` still walks, but the footer's arrow-stripping turns the name
  into `2 of 12`, which is confusing.
- **Order = album index order** (`title_order`: `title.to_lowercase()`,
  path tiebreak; missing title falls back to stem — same fallback the
  catalog uses for display). This guarantees the walk agrees with the index
  the user already sees. Call this out in `docs/records.md`: "alphabetical"
  means **title-folded album order**, not filename bytes and not `created`.
- **Membership = album index membership**: direct Markdown children of the
  album folder counted by the index (healthy and invalid-with-title alike;
  non-records, nested descendants, `.base` files, and outside-folder notes
  excluded). Invalid notes still occupy a position (they are visible in the
  index); their `N of M` counts them. If the schema is broken the writer
  still orders by title/path fallback rather than refusing the whole album.

Example (3 records, titles `Mama's`, `Nagi`, `Ninja`):

- `eat/mamas.md`: `[[eat/ninja-sushi|‹]] · 1 of 3 · [[eat/ramen-nagi|›]]`
- `eat/ramen-nagi.md`: `[[eat/mamas|‹]] · 2 of 3 · [[eat/ninja-sushi|›]]`
- `eat/ninja-sushi.md`: `[[eat/ramen-nagi|‹]] · 3 of 3 · [[eat/mamas|›]]`

Two-record album: each note's `‹` and `›` point at the other record (the
requested behaviour falls out of cycling, no special case). One-record
album: §6.

## 6. Edge cases

- **M == 1:** no nav line. A self-linking `‹`/`›` pair makes `[n`/`]n`
  look broken (it "walks" nowhere) and `1 of 1` adds noise where there is no
  walk. Adding the second record creates both notes' lines in one
  transaction.
- **M == 2:** both directions point at the other note (cycle of length 2).
- **Ties:** identical folded titles break by path (same as index). Document
  with an example; never break by `created`.
- **Missing/duplicate titles:** missing title → stem fallback for ordering
  (catalog display already does this); duplicates → path tiebreak. `check`
  already flags missing titles; nav does not add a second error.
- **Invalid records:** keep position, keep links (target by path). Rationale:
  the index shows them; skipping them would desync walk vs index.
- **Legacy `type: [[<noun>]]` notes:** members (catalog counts them); walk
  includes them. The `record_type_legacy` warning is orthogonal.
- **Dated notes / sections / empty Notes:** nav footer is outside `## Notes`
  and outside named sections; `tidy` (empty-Notes + redundant-H1 removal)
  must preserve it byte-identically (add golden tests).
- **Hand edits:** a hand-edited nav line is repaired on next writer touch
  (same-transaction replan); `records check` reports `nav_stale` /
  `nav_missing` as warnings, never errors that block unrelated writes.
- **Deletes/renames outside bob** (Obsidian delete/rename, mobile): links go
  stale until `albums sync` (full repair) or the next record write in that
  album (targeted repair). Document that sync is the repair path.
- **`.base` files, nested folders, non-record notes:** never members, never
  targets, never carry a nav line.

## 7. Writer / checker / sync design (reliability)

- **Single owner: bob-cli.** Plugin never writes nav bytes (consistent with
  "Sync albums … explicitly invokes Bob's existing writer" and the sheet
  never writing). The nav line is a **managed region**: writers parse it
  leniently (any `‹`<`>`/`prev`/`next` first-match line at EOF, with or
  without `N of M`), then rewrite canonically at EOF on every album-backed
  record mutation: `records new|update`, capture record routes, `records
  tidy` touches, and `albums sync` full repair. Notes append **before** the
  footer (update path inserts under `## Notes`, not at EOF blindly).
- **Transactions.** Follow the existing guarded pattern: maintenance lock,
  pre-sync, per-note preimage guards, one scoped commit per gesture
  (e.g. `records: relink eat (3 notes)`), post-sync only on commit.
  Reorder-affecting writes (title/stem change, insert, delete-repair) update
  self + old neighbours + new neighbours atomically; unrelated albums
  untouched; damaged albums skipped with diagnostics, never half-rewritten.
- **`records check`:** new warning codes (`nav_missing`, `nav_stale`,
  target-unresolvable), exit behaviour unchanged (warnings ≠ failure).
  `list`/`show -f json` gain `prev`/`next` (`path`, `N`, `M`) per record so
  the Record Card / footer *could* go computed later without parsing bytes.
- **Idempotency:** re-running the writer on a current album is a no-op (no
  commit, no post-sync) — same contract as `albums sync` today.
- **Tests:** unit (`title_order` incl. Unicode fold, ties, missing titles),
  golden bodies (2-record cycle, 3-record ring, M==1 omission, rename
  reorder, delete repair, legacy/empty-notes interplay, ASCII→`‹›`
  normalization), transaction (preimage race rolls back, damaged album
  skipped), plugin-manual (`[n`/`]n`, `[[`/`]]` repeat, footer preview,
  Reading/LivePreview/Source, mobile-width wrap).

## 8. Recommended solution

**V1 (ship): writer-owned footer line, zero plugin changes.**

1. Canonical line (bottom of body):
   `[[<album>/<prev-stem>|‹]] · N of M · [[<album>/<next-stem>|›]]`;
   M==1 omits the line; M≥2 cycles; order = album index `title_order`.
2. Maintain in `records new|update` + capture record path + `tidy`
   (preserve) + `albums sync` (full repair); validate in `records check`
   (warnings); document in `docs/records.md` + JSON outputs.
3. Normalize `<`→`‹`, `>`→`›` on write; keep walking both forever.
4. Tests as in §7, plus manual `[n`/`]n`/`[[`/`]]` pass on a 3-record album.

**Explicit non-goals for V1:** neighbour titles in aliases, top-of-body
placement, frontmatter fields, plugin-written bytes, `N of M` inside link
labels, blocking errors for stale nav.

**Follow-up (not V1): computed sheet/footer nav.** Once V1 data exists,
teach the record sheet to render the same prev/next (from cached
`albums list` report, no new bytes) and collapse the source footer line in
Reading view via CSS, keeping Source authoritative for `[n`/`]n`. That gets
titled destinations + zero-churn display without invalidating V1 notes.
Do not do this in V1 — it doubles the surfaces and risks two truths.

## 9. Sources consulted

- `docs/records.md` (album/record contract, index, tidy, capture).
- `src/native/records/render.rs` (`render_record_with_identity`, body rules).
- `src/native/albums/grouping.rs` (`title_order`, subgroup/peek order).
- `src/native/records/plan.rs`, `catalog.rs`, `cli.rs` (creation/update
  planning, membership, CLI surface).
- `docs/reference/plugins/bob-navigation-hotkeys.md` (`[n`/`]n`, `[[`/`]]`,
  vimrc bindings, bracket families).
- `plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js`
  (`renderedLinkMatchesNavLabel`, line scanner), `src/670-*.js`
  (`findFirstRenderedLink`, `openLabeledBodyLink`),
  `src/482-walk-mode-nav-api.js` (`api.links`), `src/490-plugin-lifecycle.js`
  (command registration), `src/546-plugin-bracket-repeat.js` (repeat).
- `plugins/bob-ledger-tools/src/124-links-walker-footer.js` (footer
  `‹ name` / `name ›`, empty-state copy).
- `docs/record-card.md` / `$LP/docs/record-card.md` (sheet at top of body,
  capability gating), `$LP/docs/albums.md` (album/index/sheet surfaces),
  `docs/periods.md` (period `‹`/`›` nav precedent).
- Glossary: `sase memory read glossary:album-note glossary:record-note`
  (plus `task-link` for the link vocabulary).

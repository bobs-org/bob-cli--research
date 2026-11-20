---
title: "Uppercase n: group jumps for days, periods, and records"
author: research.5l.grk
date: 2026-11-20
status: independent-swarm-report
topic: n-family-group-jumps
related:
  - bead:bob-cli-nh
  - research:202611/property_card_title_block/property_card_title_block.md
  - research:202611/record_nav_ring/record_nav_ring.md
  - research:202611/bracket_walk_footers/bracket_walk_footers.md
  - research:202611/sase_blog_zettel_section_schema/sase_blog_zettel_section_schema.md
  - research:202611/period_note_tree_and_stats_strips/period_note_tree_and_stats_strips.md
  - glossary:album-note
  - glossary:record-note
  - glossary:period-note
  - glossary:walker-footer
  - glossary:daily-headline
figures:
  - route
  - period
  - label
---

# Uppercase n: group jumps for days, periods, and records

> **Research query:** After the property-card title-block work, add `[N` / `]N` so they are immediately useful for daily files, period notes, and record notes. Make the skip configurable in any Obsidian note (the first thought was links that start with `<<` / `>>`). Daily skip goes to the first day of the previous / next week. Period skip goes to the first same-level period in the previous / next parent-level period (week `2026-W30` → `2026-W14` / `2026-W40`; yearly notes omit the arms). Missing destinations stay visually clear. Album notes configure a grouping field so `[n` / `]n` walk a group then the next group, and `[N` / `]N` jump to the first record of the previous / next group; start with `sase_blog_zettel` grouped by `section`, and configure other albums that benefit. `[{` / `]}` must work. Render the links at the bottom of property cards, and add walker-footer hints. Lead the design: intuitive, reliable, beautiful. Critique the plan, call out justified requirement adjustments, and end with a recommended solution.

## Bottom line

**Do it.** Family `n` is the only bracket walk whose uppercase plan is `null`. `[{` / `]}` currently show `No uppercase link walk — ]} / [{ repeat ]S / [S, ]W / [W, or ]B / [B`. Filling that hole with one rule — **open the first child of the previous or next parent** — gives daily files, week notes, quarter notes, and grouped records the same muscle memory `]S`, `]W`, and `]B` already taught.

**Three amendments make it reliable and beautiful.**

1. **Skip labels are double guillemets `«` / `»` (U+00AB / U+00BB), with optional exact `<<` / `>>` as aliases after `[n` is tightened.** ASCII `<<` already matches today's prev rule `/^[‹<]/`, so on the 1,021 dailies that have no `prev` link it would steal `[n`.
2. **Canonical destinations are computed from kind; body links document them.** Historical dailies mostly have no nav line. Period and record writers already own a nav / walk line. Compute wins when the two disagree.
3. **Reuse album `index_by` as the walk-group field.** Do not add `walk_by`. Set `index_by: section` on `sase_blog_zettel.md`. That is a justified reversal of the earlier "leave `index_by` unset" schema research: the new consumer is the walk, and the walk groups even while the catalog stays flat under the 12-row subgroup threshold.

Ship the keymaps as their own follow-up epic after `bob-cli-nh`. Do not widen the in-flight kit extract. The two-tier rail specified here is the nav-footer the title-block design already reserved.

## Verdict: good idea, one unified rule, a different spelling

This is the missing half of the bracket grammar, not a new kind of navigation.

| Family | Lowercase | Uppercase today | Uppercase after this |
| --- | --- | --- | --- |
| `s` review | `[s` / `]s` row | `[S` / `]S` group | unchanged |
| `w` lanes | `[w` / `]w` task | `[W` / `]W` lane | unchanged |
| `b` bank | `[b` / `]b` row | `[B` / `]B` day | unchanged |
| `n` links | `[n` / `]n` adjacent | *empty* | `[N` / `]N` first child of neighbour parent |

I would take this approach. I would keep body-link configurability for arbitrary notes, keep period `bob periods ensure` for missing weeks and quarters, keep the album-folder create guard for records, and keep the title-block rule that a nav line stays in Markdown and docks to the card.

## What is actually on screen today

### Family `n` has no uppercase plan

`BRACKET_REPEAT_UPPERCASE_PLANS.n` is `null` in `bob-plugins/plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js`. Lowercase `n` calls `openLabeledBodyLink("prev"|"next")`. The vault vimrc maps `[n` / `]n` and `[{` / `]}`; it has no `[N` / `]N` maps (`~/bob/obsidian_vimrc.md`). Docs already describe the hole (`docs/bob-navigation-hotkeys.md`, uppercase-repeat table).

`[n` / `]n` open the first body link (outside frontmatter and fences) whose rendered label is exactly `prev` / `next`, or whose prev label matches `/^[‹<]/`, or whose next label matches `/^[›>]/` or `/[›>]$/` (`680-plugin-link-parse.js`). First match wins. Daily notes use `prev` / `next`. Period and record notes use `‹` / `›`.

Counts: lowercase `n` ignores `N]n`. Uppercase families consume `N]S` / `N]W` / `N]B`. `N]}` keeps parity with those uppercase jumps, so `[N` must accept counts once it exists.

### Daily nav is a Templater 3-cell, and most files lack it

`_templates/daily.md` writes:

```markdown
[[…/YYYYMMDD|prev]] · [[GGGG/GGGG-Www|Www]] · [[…/YYYYMMDD|next]]
```

Census of vault dailies: **1,197** files matching `YYYY/YYYYMMDD.md`; **176** carry a `prev` / `next` nav line; **1,021** do not (older Zorg-shaped notes). `[N` that required a written skip link would miss almost the whole archive.

Today is Friday 2026-11-20, ISO `2026-W47`. This week's Monday is 2026-11-16. Previous week's Monday is **2026-11-09** (`2026/20261109.md`). Next week's Monday is **2026-11-23** (`2026/20261123.md`). That is the daily skip the request described, and it is also "first child of the previous / next parent week."

### Period nav is already a 3-cell `‹ · ↑ · ›` scaffold

`src/native/periods/scaffold.rs` writes one nav line from `id.prev()`, `id.parent()`, `id.next()`. Labels live in `labels.rs` (`‹ W29`, `↑ 2026-Q3`, `W31 ›`). ISO quarters are W01–13, W14–26, W27–39, W40–52/53 (`quarter_weeks()`, `year_quarters()`). Year notes parent to `all_time` and already have adjacent-year `‹` / `›` arms; they have no parent neighbour that contains sibling years, so they correctly omit a skip.

Vault: 50 week notes, 5 quarter notes, 4 year notes. `2026/2026-W30.md` exists, as do `2026-W14.md` and `2026-W40.md`. W30 sits in Q3 (W27–39). Q2's first week is W14 (2026-03-30). Q4's first week is W40 (2026-09-28). The request's example is the calendar code's first-child rule.

Missing weeks, quarters, and years already create through ledger-tools `api.periodNotes` v1 (`bob periods ensure -d <first day>`).

### Record walk is a bob-owned 3-cell ring

Every record's first body line is:

```markdown
[[eat/pho|‹ Pho House]] · [[eat|↑ Eat]] · [[eat/ramen_ya|Ramen Ya ›]]
```

Order is album-wide `title_order`, flat across status groups, wrapping at both ends (`docs/records.md` § Record walk; `src/native/albums/walk.rs`). `parse_link_run` **rejects more than three links**, so a five-cell skip line is unrecognized until that cap is raised. A second body line of `«` / `»` child links (no `↑`) is currently ordinary body: it does not trip `ExtraText` (that reason is `↑` nav-like lines only).

The record card already docks this line as a 3-column rail (`242u-plugin-record-walk-rail-dom.js`) with live `N of M`, wrap glyph `↺`, and "Not there yet — walk is syncing" while stale. Missing album-folder records refuse Templater create (`641-album-record-link-guard.js`) and schedule `bob albums sync`.

`index_by` already names a field for catalog subgroup headings, and only fires for groups larger than 12 with at least two distinct values (`grouping.rs` `LARGE_GROUP = 12`). Missing values sort last under `—`. Catalog grouping still prefers `status` when that field exists. Walk order today ignores `index_by`.

### Property cards and the `n` footer

Title-block research (`property_card_title_block.md`) already reserved a docked rail:

```text
‹ previous            ↑ parent · position              next ›
```

Adjustment A7: keep the Markdown bytes, dock the rail, hide the raw paragraph unless the caret touches it; never hide without a rail. Intention cards currently paint kicker / parent / bands and have **no** rail. Identity chrome is a follow-up epic; `nh` stays pixel-identical.

The `n` walker footer (`124-links-walker-footer.js`) is a destination compass over `walkMode.links()` v2, which returns only `prev` / `next`. Every `hintText` is `""`. Empty state: `no ‹ / › links in this note`. Bank already teaches `]} next day`.

## Critique of the request as written

The destination rule, the yearly omission, the album grouping walk, the `[{` / `]}` requirement, the card rail, and the footer hints are all right. The first-thought spelling and the "configure a field" wording need sharpening.

**ASCII `<<` / `>>` collide with `[n`.** The prev matcher is "starts with `‹` or `<`". A label `<< W14` starts with `<`. On a note that already has `prev` / `‹` earlier in the body, first-match still wins for `[n` and the skip sits unused. On a note with only skip links — the 1,021 dailies without `prev`, plus any generic note Bryan configures by hand — `[n` would follow the skip. That silently destroys the lowercase / uppercase distinction the grammar is trying to grow.

**Double guillemets are already collision-free.** `«` (U+00AB) and `»` (U+00BB) fail both `/^[‹<]/` and `/^[›>]/` / `/[›>]$/`. They are the typographic pair of the existing `‹` / `›` (U+2039 / U+203A): single means adjacent, double means skip. Source mode, the rail, and the footer can teach one story. Exact ASCII `<<` / `>>` can still be aliases once `[n` excludes labels that start with `<<`.

**Body-link-only skip fails the daily archive.** Computing Monday-of-neighbour-week from the path needs zero file edits and works on every canonical daily. Writing `«` / `»` into 1,197 dailies is a migration, not a feature. New dailies may grow a skip line from Templater as documentation; it is optional because compute is the authority.

**A new `walk_by` key would drift from the catalog.** `index_by` already means "the field that subgroups this album." Eat uses `location`; subscriptions uses `category`; `sase_blog_zettel` has a required choice `section` and `index_facets: [section, claim]` with `index_by` unset. One field keeps the generated index and the walk talking about the same grouping. Walk order uses schema-declaration order for choice fields (so `intro` … `close` stays narrative) and the existing fold/sort for suggest/text. Catalog `LARGE_GROUP = 12` and raw-key alphabetical subgroup headings stay a catalog wart; the walk ignores that threshold and paints choice labels. Fixing catalog subgroup labels is a welcome follow-up and is not a gate.

**Earlier schema research rejected `index_by: section`.** `sase_blog_zettel_section_schema` left it unset because subgroups only fire past 12 rows inside a status group, headings were raw keys in alphabetical order, and facets already showed the section label. That was right for a 1-record (now 12-record) catalog. It is wrong once `[N` needs a group key at any size. Setting `index_by: section` now is a reversal with a new reason.

**Quarter skip is year-scale.** The same first-child rule that sends W30 → W14 / W40 sends 2026-Q3 → **2025-Q1** / **2027-Q1**. Q2, Q3, and Q4 of 2026 share those skip destinations. Adjacent quarters remain `[n`. That is consistent, a large jump, and worth stating in the hint (`]N next year`) so it does not look like a bug.

**Record `[n` order changes on grouped albums.** Eat has 105 restaurants and `index_by: location` already. After this, `[n` walks Cranford in title order, then Westfield, and so on; `[N` jumps location. That is the request, and it is a user-visible neighbour change on every grouped album's walk line. Ungrouped albums (tv, movies, today's zettel until `index_by` is set) keep the flat title ring; `[N` no-ops with a notice.

## Requirement adjustments (explicit)

Each line changes or sharpens the request. Bryan can veto any individually.

- **R1 — Skip glyphs are `«` / `»`.** Optional exact-label aliases `<<` / `>>` only after `[n` prev stops treating a leading `<<` as prev. Period and record writers emit guillemets.
- **R2 — One routing rule: first child of the previous / next parent.** Daily → Monday of neighbour ISO week. Week → first week of neighbour quarter (`parent().prev|next().quarter_weeks()[0]`). Quarter → Q1 of neighbour year (`parent().prev|next().year_quarters()[0]`). Grouped record → first record of neighbour `index_by` value. Year and `all_time` omit skip.
- **R3 — Hybrid authority: compute for canonical kinds, body-link fallback for everyone else.** When both exist and disagree, compute wins; the next `bob periods ensure` / `bob albums sync` rewrites the bytes. Generic notes (area, project, notebook, dash, …) are configured by writing a `«` / `»` wikilink.
- **R4 — Do not backfill 1,197 dailies.** Compute from the path. New dailies *may* grow a skip line in `_templates/daily.md`.
- **R5 — Reuse `index_by`; do not add `walk_by`.** Walk grouping fires at any size. Within a group, keep `title_order`. Missing / empty values sort last as `—`. Choice groups follow schema-declaration order and display choice labels (emoji + label). Suggest/text groups follow the existing fold/sort. The catalog's 12-row subgroup threshold is unchanged.
- **R6 — Grouped `[n` is in scope.** `[n` walks every record sharing the current `index_by` value, then steps into the next group. `[N` from mid-group lands on the first record of the neighbour group, matching `[W` from mid-lane. The ring wraps; skip arms wear `↺` when they wrap.
- **R7 — Calendar skip does not wrap the vault.** Destinations follow calendar math through the existing 1970–2999 period bounds. A missing destination is create-eligible (daily Templater / period ensure). Records never create.
- **R8 — Counts: `[N` consumes `N]N` / `N]}` as group steps.** Lowercase `n` still ignores counts.
- **R9 — Do not widen `bob-cli-nh`.** Keymaps, compute, writers, record-rail second row, intention-card rail, and footer hints are a follow-up epic. Title-block identity restyles the rail later. Never hide nav bytes without a rail (title-block A7).
- **R10 — Raise the record walk parser from 3 links to 5** so a grouped walk line can carry skip arms on the same bob-owned line. Keep the "exactly one walk line" invariant. Period notes add a second scaffold line (they have no 3-link cap).
- **R11 — `[{` / `]}` fill family `n`.** `BRACKET_REPEAT_UPPERCASE_PLANS.n` calls the new skip commands. `[N` / `]N` also `rememberBracketRepeatType("n")`, matching `[S` still selecting `s`.
- **R12 — Album config in v1:** must set `index_by: section` on `sase_blog_zettel.md`. Eat and subscriptions already have `index_by`. Optionally set `index_by: category` on `podcasts.md`. Leave `tv` and `movies` ungrouped until `service` / `year` are filled.

## Recommended solution

### The routing rule

![How [N] picks a destination: canonical notes compute the first child of the neighbour parent; other notes follow a guillemet body link](n_family_group_jump_keymaps__grk_route.svg)

Caption: Canonical daily, week, quarter, and grouped-record notes compute the first child of the previous or next parent. Other notes follow a `«` / `»` body link. Year notes, all-time, and ungrouped records show a notice.

Rendered size: 747.6 × 674 px; fit scale: 87.3%.

The same sentence covers every species this feature cares about:

> **`[N` / `]N` opens the first child of the previous / next parent.**

![From 2026-W30, [N] opens 2026-W14 and ]N opens 2026-W40](n_family_group_jump_keymaps__grk_period.svg)

Caption: From week 2026-W30 in Q3, `[N` opens 2026-W14 (first week of Q2) and `]N` opens 2026-W40 (first week of Q4). Adjacent weeks stay `[n`.

Rendered size: 485.6 × 478 px; fit scale: 100%.

| Open note | Parent | `[N` destination | `]N` destination | Wrap |
| --- | --- | --- | --- | --- |
| Daily 2026-11-20 (Fri, W47) | Week W47 | Monday 2026-11-09 (`2026/20261109.md`) | Monday 2026-11-23 | no |
| Week 2026-W30 | Quarter Q3 | 2026-W14 | 2026-W40 | no |
| Quarter 2026-Q3 | Year 2026 | 2025-Q1 | 2027-Q1 | no |
| Year 2026 / `all_time` | `all_time` / none | notice `Year notes have no group jump` | same | — |
| Record with `index_by` | that field's value | first record of previous value | first of next value | yes, `↺` |
| Record without `index_by` | — | notice `This album has no group jump` | same | — |
| Any other note | — | first body `«` link | first body `»` link | as written |

Daily path uses the Monday's **calendar** year (`YYYY/YYYYMMDD.md`). Week path uses **ISO week-year** (`YYYY/YYYY-Www.md`). W01 of 2026 starts 2025-12-29; compute must go through existing `PeriodId` helpers (`week_dates()`, `path()`, `link_target()`) rather than string arithmetic on the open path.

Implementation sketch, periods:

```text
id.parent()?.prev()?  →  first child
  week    → parent_quarter.quarter_weeks()[0]
  quarter → parent_year.year_quarters()[0]
  year    → None
```

Plugin commands `open-prev-group-link` / `open-next-group-link` try compute first, then `findFirstRenderedLink` for `skip-prev` / `skip-next` (matcher: label starts with `«` or equals `<<`; next starts/ends with `»` or equals `>>`). Missing period / daily targets reuse `openOrCreateLinkCandidate`. Album-folder targets keep the create guard.

### Skip spelling

![ASCII << would steal [n] on notes with no prev link; guillemets are already outside that matcher](n_family_group_jump_keymaps__grk_label.svg)

Caption: ASCII `<<` matches the existing `[n` prev rule on notes that have no `prev` / `‹` link. Double guillemets `«` / `»` sit outside that matcher, so `[N` can own them.

Rendered size: 604.0 × 428 px; fit scale: 100%.

Tighten `renderedLinkMatchesNavLabel` prev to: exact `prev`, starts with `‹`, or starts with a single `<` whose second character is not `<`. Next: exact `next`, starts/ends with `›`, or starts/ends with a single `>` that is not `>>`. Then exact `<<` / `>>` are safe aliases.

Labels:

| Kind | `[n` arm | `[N` arm |
| --- | --- | --- |
| Daily | `prev` / `next` (keep) | `« Nov 9` / `Nov 23 »` (date of the Monday) |
| Week | `‹ W29` / `W31 ›` (keep) | `« W14` / `W40 »` |
| Quarter | `‹ Q2` / `Q4 ›` (keep) | `« 2025-Q1` / `2027-Q1 »` |
| Record | `‹ Title` / `Title ›` (keep, new order) | `« Intro` / `What is SASE? »` (group **label**, target = first record) |

Skip-arm display text is the **group name**, even though the wikilink target is a note. Tooltips name the destination note and the group (`First zettel in Intro · AI Slop`).

### Writers

**Periods.** Keep the existing 3-cell `‹ · ↑ · ›` line. Add a second scaffold line:

```markdown
[[2026/2026-W29|‹ W29]] · [[2026/2026-Q3|↑ 2026-Q3]] · [[2026/2026-W31|W31 ›]]
[[2026/2026-W14|« W14]] · [[2026/2026-W40|W40 »]]
```

`bob periods ensure` / scaffold owns both. Year and `all_time` scaffolds stay one line. Existing weeks and quarters migrate on the next ensure/rebuild of the nav block; if today's ensure only fills missing files, add a bounded rewrite of the two nav lines when they are still bob-shaped (same spirit as walk-line `stale`).

**Records.** One bob-owned line remains the invariant. When `index_by` is set and there are at least two groups, raise `parse_link_run`'s cap from 3 to 5 and render:

```markdown
[[album/gprev|« Group]] · [[album/prev|‹ Title]] · [[album|↑ Album]] · [[album/next|Title ›]] · [[album/gnext|Group »]]
```

`is_walk_line` still requires exactly one `↑` album root; the extra two child links are legal. Singleton albums and ungrouped albums keep today's 1-cell / 3-cell shapes. Neighbour order becomes group-major, `title_order` inside the group, then wrap. `bob albums sync` is the only repair owner, as today.

**Dailies.** Compute is enough. Optional Templater addition under the existing 3-cell, for Source-mode documentation of new notes only.

### Albums to configure

Live vault census (folder members, YAML fields):

| Album | Records | Current `index_by` | Candidate | v1 action |
| --- | --- | --- | --- | --- |
| `sase_blog_zettel` | 12, all `seed`; `section` filled on every row; 8 distinct sections (future 3, the_agent_cli 2, not_ready 2, six singletons) | unset (`index_facets: [section, claim]`) | `section` (required choice, narrative `values:` map) | **Set `index_by: section`.** `[n]` walks a section's zettels then the next section in schema order; `[N]` jumps section. Catalog stays status-grouped; at 12 rows it stays flat. |
| `eat` | 105; `location` filled on all; 28 locations (cranford 34, westfield 20, …) | `location` | already | **Free.** `[n]` becomes location-major. This is the largest behaviour change. |
| `subscriptions` | 28; `category` filled; tech 16, media 8, rest 1s | `category` | already | **Free.** |
| `podcasts` | 15; `category` filled (programming 4, python 3, tech/ai/productivity 2, …) | unset | `category` (required suggest) | **Optional.** Small enough that the flat ring still works; grouping is nice once the list grows. |
| `tv` | 23, all `to_watch`; `service` missing on 19, Apple TV+ on 4 | unset | `service` | **Leave unset.** Grouping would dump 19 shows under `—`. |
| `movies` | 12; `year` missing on all 12 | unset (`index_facets: year, verdict, recommended_by`) | `year` | **Leave unset** until years are filled. |

`album.md` is a glossary note, not an album.

`sase_blog_zettel` section order follows the schema map (`intro` … `close`), which is the walk people will feel when drafting a post. Status remains the catalog's primary group (Seed / Draft / …), so the `[!records]` callout still answers "where is this zettel in the writing pipeline?" while `[N` answers "where is this zettel in the essay?"

### Property-card rail

Two rows when a skip exists; one row when it does not. Dock at the bottom of the card. Hide the source paragraph unless the caret touches it.

Week example:

```text
‹ W29                 ↑ 2026-Q3                  W31 ›
« W14                 Q3 · W30 of 13             W40 »
```

Daily example:

```text
‹ Thu                 ↑ W47                      Sat ›
« Nov 9               week of Nov 16             Nov 23 »
```

Grouped record example:

```text
‹ Beads and Birds     ↑ SASE Blog Zettel         Bob Task Events ›
« Beads               Future Work · 2 of 3       Agent CLIs »     ↺
```

Center of the skip row is **group context**, never a third link: `Q3 · W30 of 13`, `week of Nov 16`, `Future Work · 2 of 3`. Glyphs: `‹` / `›` on row 1, `«` / `»` on row 2, wrap `↺` only on a wrapping skip arm. Missing destination: `is-unresolved` / ghosted arm, trailing `+` when create-eligible (daily, period), never `+` on a record. Keyboard: row 1 is `[n`, row 2 is `[N`; clicking an arm runs the same commands.

Record cards extend the existing rail in this epic (they already dock). Intention cards gain the same two-tier rail in this epic so dailies and periods are immediately useful; the later identity epic restyles kicker / title around it. Albums have no skip rail (no `[n` ring on the album note itself).

### Walker footer

Fill family `n`'s uppercase plan. Grow `walkMode.links()` to v7 with `skipPrev` / `skipNext` plus `{ group, position, size }` so the footer can paint a compass without re-parsing. Set `hintText` the way bank already sets `]} next day`:

| Kind | Hint |
| --- | --- |
| Daily | `]N next week` |
| Week | `]N next quarter` |
| Quarter | `]N next year` |
| Grouped record | `]N next section` (use the field's label) |
| No skip | `""`, and `[N` shows the notice |

Footer click on a skip arm runs the new commands. Empty skip with adjacent links present still shows the `‹` / `›` compass; the hint slot is how people discover `[N`. Selector tooltip for `n` changes from "none" to `]N`.

### `[{` / `]}` and vimrc

```javascript
n: {
  forward:  { method: "openLabeledBodyLink", args: ["skip-next"] },
  backward: { method: "openLabeledBodyLink", args: ["skip-prev"] },
}
```

Those methods go through the compute-first helper, so a daily without written `«` still jumps. After `[n` or `[N`, family is `n`, so `]}` is `]N`.

Vault `obsidian_vimrc.md` additions next to the existing `[n` maps:

```vim
exmap bob_next_group_link obcommand bob-navigation-hotkeys:open-next-group-link
exmap bob_prev_group_link obcommand bob-navigation-hotkeys:open-prev-group-link
nnoremap ]N :bob_next_group_link<CR>
nnoremap [N :bob_prev_group_link<CR>
```

Update the `[{` / `]}` comment to name links. Palette names: "Open next group link" / "Open previous group link".

### Missing destinations, visually

| Kind | Missing dest | Create | Visual |
| --- | --- | --- | --- |
| Daily Monday | common for future weeks | Templater, same as `[n` to `next` | ghosted rail arm, `+`, Obsidian unresolved |
| Week / quarter | create-only, one week ahead today | `bob periods ensure` | ghosted, `+`, existing ensure toast |
| Year skip | none | — | no arms |
| Record group | group omitted if empty | never | skip lands on an existing record; stale walk uses current "Not there yet — walk is syncing" |

Use the unresolved / ghost treatment already on intention-card links. Future-not-yet-created is expected, so keep it calm (muted + `+`), not error-red.

## Phasing

Do not wait on the identity epic. Keymaps are useful the day compute and commands exist.

1. **Plugin keymaps.** Commands, vimrc, uppercase `n` plan, matcher tighten, counts, notices. Compute for daily / week / quarter even before writers emit `«`.
2. **Period scaffold** second line + bounded stale-nav rewrite. Year / `all_time` unchanged.
3. **Albums.** Group-major walk when `index_by` is set; 5-cell line; parser cap 5. Vault: `sase_blog_zettel` `index_by: section`. Optional `podcasts` `index_by: category`.
4. **Record rail** second row from the 5-cell line; wrap glyph on skip.
5. **Intention-card rail** two-tier on canonical dailies / weeks / quarters (always-mount per title-block A3). Fail-open: body nav stays visible if the rail does not mount.
6. **Footer + `walkMode.links()` v7.** Hints, skip arms, selector tooltip.
7. **Optional daily template** skip line for new notes. Docs: `docs/walks.md`, `docs/records.md` Record walk, `docs/periods.md` scaffold, `bob-navigation-hotkeys.md` family table.

No new public CLI subcommand. `bob albums sync` and `bob periods ensure` grow their existing owned regions. Changelog: grouped-album neighbour order is a behaviour change worth calling out; walk-line shape for grouped records is a vault-format change.

## Out of scope

- Bank months (already `[B`).
- Notebook section walks (already a different surface; a notebook may still opt in with a `«` link).
- `all_time`.
- Catalog subgroup heading labels / schema-order sort (follow-up; walk does this correctly on its own).
- Backfill of historical daily nav.
- Widening `bob-cli-nh` pixel-identical extraction.
- A `walk_by` key, YAML `skip_prev` fields, or Dataview queries as the authority.

## Why this is beautiful

Single vs double guillemets are a pair you can see without a legend. Lowercase vs uppercase `n` matches the pair. The rail is two rows of the same 3-column grid the record card already proved. Hue still means *where*; the skip row's center type is *which group*. Missing is a ghost with a `+`, the same quiet unresolved already used on intention cards. The footer hint is one short clause in the slot bank already occupies.

The feature is intuitive because it completes a grammar Bryan already has in his hands: after `]n`, `]}` finally does something, and it does the thing `]W` and `]B` taught.

## Sources

- `bob-plugins/plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js` — `BRACKET_REPEAT_UPPERCASE_PLANS.n = null`; notice string.
- `bob-plugins/plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js` — `[n` label matcher.
- `bob-plugins/plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js` — `openLabeledBodyLink`; period ensure.
- `bob-plugins/plugins/bob-navigation-hotkeys/src/490-plugin-lifecycle.js` — `open-prev-link` / `open-next-link`.
- `bob-plugins/plugins/bob-navigation-hotkeys/src/482-walk-mode-nav-api.js` — `links()` v2 prev/next only.
- `bob-plugins/plugins/bob-navigation-hotkeys/src/641-album-record-link-guard.js` — missing record never Templater-creates.
- `bob-plugins/docs/bob-navigation-hotkeys.md` — family table, uppercase-repeat table, `[n` parse contract.
- `bob-plugins/plugins/bob-ledger-tools/src/124-links-walker-footer.js` — empty `hintText`; empty `no ‹ / › links`.
- `bob-plugins/plugins/bob-ledger-tools/src/242u-plugin-record-walk-rail-dom.js` — 3-col rail, wrap, live counts.
- `src/native/periods/scaffold.rs`, `calendar.rs`, `labels.rs` — nav line, `parent` / `prev` / `next`, `quarter_weeks()`, Monday-first `week_dates()`.
- `src/native/albums/walk.rs` — 3-link cap, one `↑`, damage reasons.
- `src/native/albums/grouping.rs` — `LARGE_GROUP = 12`, `title_order`, missing `—`.
- `docs/records.md` — `index_by`, Record walk contract.
- `~/bob/obsidian_vimrc.md`, `_templates/daily.md`, `sase_blog_zettel.md`, `eat.md`, `subscriptions.md`, `podcasts.md`, `tv.md`, `movies.md`.
- Vault census (this research): 1,197 dailies / 176 with prev-next; 50 weeks / 5 quarters / 4 years; album field fills as tabulated above.
- `research:202611/property_card_title_block/property_card_title_block.md` — docked rail, A7, always-mount, do not widen `nh`.
- `research:202611/sase_blog_zettel_section_schema/sase_blog_zettel_section_schema.md` — prior `index_by: section` rejection, reversed here for the walk.

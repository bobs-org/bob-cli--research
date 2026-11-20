# Bracket-uppercase `N` walks: far-week jumps, period-group jumps, and grouped record walks

> **Research query.** After the work described by `property_card_title_block.md` lands, add new `[N` and `]N` keymaps that are immediately useful for daily files, period notes, and record notes. They should be configurable in any Obsidian note somehow (Bryan's first thought: links starting with `<<` / `>>`). Daily `<<` points to the first day of the previous week and `>>` to the first day of the next week. Period `<<` points to the first same-level period in the previous higher-level period and `>>` to the first in the next higher-level period (e.g. `2026/2026-W30.md` gets `<<` to `2026/2026-W14.md` and `>>` to `2026/2026-W40.md`); yearly notes get nothing. Album notes get a grouping field; `[n` / `]n` walk within a group before crossing groups and `[N` / `]N` jump to the first record of the previous/next group. First use-case: `sase_blog_zettel.md` groups by `section`; decide whether other albums deserve one. `[{` / `]}` must work, links must render at the bottom of property cards (see the `bob-cli-nh` epic), walker-footer hints must cover the new links. Lead the design: intuitive, reliable, beautiful. Critique the plan and end with a recommended solution.

**Bottom line: do it, but not literally as written.** The three requested behaviors are three different mechanisms wearing one keymap, and the `<<`-as-authored-links idea only fits one of them. Daily/period/record far jumps should be *computed*, never hand-authored — bob already knows every target from `PeriodId` and the album walk order, hand-authoring date arithmetic across 1,195 heterogeneous dailies and quarterly boundaries is exactly the migration the period-adopt epic just finished cleaning up. Reserve authored `<<` / `>>` (and their pretty twins `«` / `»`, `‹‹` / `››`) as the *generic-note fallback* so `[N` / `]N` work in any note, and add one explicit album frontmatter key (`walk_by`) for the record grouping. With that split the feature is intuitive (one key always means "one level farther"), reliable (no new bytes to drift), and beautiful (one docked rail reuses the proven record-walk-rail pattern).

All dates, code paths, and vault counts below were verified in this checkout unless marked inferred.

## 1. What `[n` / `]n` / `[[` / `]]` / `[{` / `]}` do today

The contract lives in `docs/bob-navigation-hotkeys.md` and four source files. Any design that touches `[N` / `]N` inherits all of it.

- `[n` / `]n` open the **first body link** (outside frontmatter and code fences) whose rendered label is exactly `prev` / `next` or an arrow label. The matcher is `renderedLinkMatchesNavLabel` in `plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js`: `prev` matches `^[‹<]`, `next` matches `^[›>]` or `[›>]$`. That one rule covers the daily nav line `[[2026/20261118|prev]] · [[2026/2026-W47|W47]] · [[2026/20261120|next]]` and the period nav line `[[2026/2026-W44|‹ W44]] · [[2026/2026-Q4|↑ 2026-Q4]] · [[2026/2026-W46|W46 ›]]` (`docs/bob-navigation-hotkeys.md:567-571`, `src/680-plugin-link-parse.js:1-12`).
- Following *any* link (Enter, `]n`, `[n`) to a missing week, quarter, year, or all-time note asks bob to create it through the ledger-tools `api.periodNotes` v1 namespace (`bob periods ensure -d <its first day>`), then opens it; it never applies a Templater template. Without that namespace it shows `No <name> note yet — bob periods ensure creates period notes` and creates nothing (`docs/bob-navigation-hotkeys.md:572-578`, `src/670-plugin-project-files.js:117-149`).
- Record notes carry bob-maintained walk lines; `[n` / `]n` **never create missing album records** (`docs/bob-navigation-hotkeys.md:538`). The walk line is rendered by `render_walk_line` in `src/native/albums/walk.rs:171-191` as `[[<album>/<prev>|‹ <Prev>]] · [[<album>|↑ <Album>]] · [[<album>/<next>|<Next> ›]]`, a singleton points only at its album, the ring wraps, and `classify` distinguishes `current` / `missing` / `stale` / `damaged` (`walk.rs:193-250`).
- Bracket repeat (`src/546-plugin-bracket-repeat.js`) records one family `s` / `w` / `n` / `b`. `n` forward/backward delegates to `openLabeledBodyLink("next"/"prev")` and ignores counts. The uppercase table has `n: null` — links explicitly have **no uppercase walk** — and both repeat commands show `No uppercase link walk — ]} / [{ repeat ]S / [S, ]W / [W, or ]B / [B` when the family is `n` (`546:33-65`, `546:140-143`). The mode indicator agrees: `upperTooltip: "]} / [{ have no link variant (no ]N / [N)"` (`src/547-bracket-mode-indicator.js:27-30`). The vault `obsidian_vimrc.md` maps `[n` / `]n`, `[[` / `]]`, `[{` / `]}` to the four palette commands; there are no `[N` / `]N` bindings yet.
- The links walker footer (`plugins/bob-ledger-tools/src/124-links-walker-footer.js`) is a read-only destination compass: `Links`, `Links N/M` on records, `no ‹ / › links in this note` when empty, `‹ name[+]` / `[name[+] ›` arms where `+` marks a creatable missing target (never for album records), and today **`hintText: ""`** — the `n` panel is the only walker with no hint slot content (`124:170-260`). The status bar always shows `[[ s w n b ]]` with the active walk lit; clicking a letter persists the family per device and never walks (`docs/bob-navigation-hotkeys.md:594-611`, `api.walkMode` v6).

Consequence: `[N` / `]N` are not free keys. They slot into three load-bearing tables (`BRACKET_REPEAT_PLANS`, `BRACKET_REPEAT_UPPERCASE_PLANS`, the indicator tooltips), the `api.walkMode` family contract (no new family — `N` stays family `n`, exactly as `S` stays family `s`), and the footer's empty-hint gap. Anything that invents a fifth family letter or a separate mode breaks `]]` / `[[` / `[{` / `]}` for everyone.

## 2. Daily files: `<<` is Monday of the previous week

### Today

Every canonical daily (`YYYY/YYYYMMDD.md`) opens with `[[prev|prev]] · [[week|Www]] · [[next|next]]` — rewritten into that exact shape by `rewrite_nav_line` in `src/native/periods/migrate.rs:923-939` — and its parent is its ISO week (`docs/periods.md:3-56`). Verified live: `2026/20261119.md` carries `[[2026/20261118|prev]] · [[2026/2026-W47|W47]] · [[2026/20261120|next]]` directly under `# 2026-11-19 Thu`.

### Proposed semantics (adopt with one correction)

- `<<` from any daily = the **Monday (`YYYYMMDD`) of the previous ISO week**; `>>` = the Monday of the next ISO week. Not the same weekday, not "seven days ago": the anchor is the *week start*, so every day in W47 shares the same `<<` (Mon of W46) and `>>` (Mon of W48). This matches the request and is the only choice that makes the rail stable as you walk a week day by day.
- Date math must go through `PeriodId`, never through string arithmetic on `YYYYMMDD`. The correct pipeline is: parse the daily date → `PeriodId::week_for_date(date)` → `.prev()` / `.next()` (which already handle 52/53-week years and the 1970/2999 bounds in `src/native/periods/calendar.rs:205-290`) → `.start()` (Monday via `from_isoywd_opt(year, week, Mon)`, `calendar.rs:150-164`) → format `YYYY/YYYYMMDD`. Year boundaries fall out for free (a daily in W01 2026 jumps to a Monday in Dec 2025 and vice versa).
- Missing-target policy follows the existing split: daily far targets use the *existing* daily creation path (today's `[n` machinery plus the vault's Templater "trigger on file creation" — no new creator), period far targets use `api.periodNotes.ensureNote`. Never the reverse. A missing Monday daily that Templater would fill gets the same `+` affordance the links footer already uses; a missing period gets the existing `bob periods ensure` flow.

### Why not hand-authored `<<` links in dailies

Authoring a second nav line in ~1,195 heterogeneous daily notes (five historical shapes per the title-block census) to store a value bob can compute is all cost and no power: a vault-wide migration, a new line for `bob periods migrate` to adopt and for every future daily template to emit, drift whenever a week straddles a year boundary, and a second source of truth beside `PeriodId`. The property-card identity epic just established the opposite direction — hide the computable H1/nav at render time, never rewrite 1,195 notes for a visual goal. Daily `<<` / `>>` should be computed at read time by nav + ledger-tools and rendered in the card rail and footer, with zero new bytes in daily notes.

## 3. Period notes: first-of-parent's-neighbour, yearly excluded

### Today

Scaffolds emit a three-link nav line plus child links (`src/native/periods/scaffold.rs:59-154`): week `‹ W44 · ↑ Q4 · W46 ›`, quarter `‹ Qn · ↑ year · Qn ›`, year `‹ year · ↑ All time · year ›`. `PeriodId::{prev,next,parent,start,link_target}` are total functions with explicit `None` past 1970/2999 and for `AllTime` (`calendar.rs:190-318`).

### Proposed semantics (adopt as specified)

For a period `P` at level `L` with parent `Q = P.parent()`:

- `<<` = the **first level-`L` child of `Q.prev()`**; `>>` = the first level-`L` child of `Q.next()`. Concretely:
  - week in quarter `Q`: `Q.prev().quarter_weeks()[0]` / `Q.next().quarter_weeks()[0]`;
  - quarter in year `Y`: `Y.prev().year_quarters()[0]` (= Q1 of previous year) / `Y.next().year_quarters()[0]` (= Q1 of next year).
- The request's example verifies exactly: `2026-W30` lives in `2026-Q3` (`W27–W39` per `2026-Q3.md`'s own child line). Previous quarter `Q2` starts at `(2-1)*13+1 = W14`; next quarter `Q4` starts at `W40`. So `<<` → `2026/2026-W14.md`, `>>` → `2026/2026-W40.md` — both files exist in this vault. The constants are worth naming because they are fixed: quarterly first weeks are always `W01 / W14 / W27 / W40` (`calendar.rs:353-365`), so weekly far jumps never need a table.
- Yearly notes: no support, as requested. `Year.parent() = AllTime` and `AllTime.prev()/next() = None`, so there is no "first year of the previous all-time" to point at. The rail hides its far arms on years, and `[N` / `]N` there show the same no-uppercase-shape notice the `n` family uses today rather than a dead jump. `all_time.md` (nav `[[org|↑ org]]` only) likewise gets nothing.
- Missing far periods reuse the existing missing-period flow (`openPeriodNoteThroughBob` → `api.periodNotes.ensureNote(path)`), so a `>>` from the last scaffolded week offers to create rather than refusing. The card rail marks that arm creatable (`+`, dimmed, tooltip `No W48 note yet — ]N creates it`), mirroring the links footer's `createEligible` language.

Edge cases the implementation must pin (all cheap given `calendar.rs`): Q4 in a 53-week year has 14 weeks (`W40–W53`, `quarterly_last_week`); the first week of the *next* quarter is still `W01` of the next year. `Q1`'s `<<` is `W40` of the previous year, not `W01` of anything. Weeks `W01`/`W53` that straddle January 1 belong to their ISO week-year, so the far computation must use `week_for_date`/`quarter_for_date` (ISO), never the calendar year of the daily path.

## 4. Record notes: grouped walks need one new album key

### Today

Two orderings coexist and they deliberately disagree:

- **Display grouping** (`src/native/albums/grouping.rs`): `group_field()` prefers a `status` choices field, else the first choices field. `sase_blog_zettel` therefore groups by `status` today (all 12 records are `🌱 Seed`). `index_by` only adds *subgroup* headings inside groups larger than `LARGE_GROUP = 12` with ≥2 distinct values — it never changes walk order. Title order within groups is `title_order` (case-folded title, then path).
- **Walk order** (`src/native/albums/walk.rs:136-154`): `ring_slots` sorts the whole folder by `title_order`, flat across status groups, wraps at both ends, singleton shows only the album link. `[n` / `]n` follow the *written* walk line and never create records.

So today `[n` / `]n` walk alphabetically (`host_owned_completion ↔ memory ↔ microsoft_ceo…`), while the index groups by status. The request changes the walk to be group-aware.

### The `section` case is real and ideal

`sase_blog_zettel.md` declares `status` (6 choices, required) plus `section` (16 choices, required) with `index_facets: [section, claim]`. All 12 live records are `status: seed` but spread across 8 sections (`future 3, not_ready 2, the_agent_cli 2, beads/macros/project/turn/what 1 each` — counted from the vault). Walking alphabetically today hops `beads → future → future → future → …` with no narrative continuity; walking *within* a section (`future`'s three in title order, then the next section) is exactly the "read one claim-cluster at a time" behavior a zettel album wants. `section` is required, choices-typed, single-valued in practice, and already a facet — it satisfies every soundness condition for a walk grouping.

### Other albums: configure none now

| Album | Fields (choices only) | Walk-by candidate? | Verdict |
|---|---|---|---|
| `eat` (105 restaurants) | `status`; `category`/`location` are `suggest` free text; `index_by: location` | `location` would group cranford together, but free-text folds (`cranford` vs `Cranford Square` vs `Chelsea Market in NYC`) need normalization the walk cannot promise, and cuisine (`category`) is the more natural reading order anyway | **No.** Leave title-order; revisit only with a normalized-location design. |
| `movies` (12) | `status`, `verdict` (choices); `year` number | `verdict` groups unwatched (no verdict) vs loved/liked/… — but 10 of 12 are `to_watch` with no verdict, so the grouping is degenerate | **No.** |
| `tv` (23) | `status`, `verdict` | Same degeneracy (23 `to_watch`) | **No.** |
| `podcasts` (15) | `status`; `category` free-text suggest | Same free-text problem as `eat.location` | **No.** |
| `subscriptions` (28) | `status`, `cadence` + `pricing` choices; `category` suggest; `index_by: category` | `cadence` (Monthly / Every 4 weeks / Quarterly / Yearly) is choices-typed and would group renewals sensibly — the single plausible second adopter | **Not now.** Reference-walked rarely; let `sase_blog_zettel` prove the mechanism first, then adopt `cadence` in a one-line follow-up if Bryan asks. |

Do not reuse `index_by` for this. `index_by` is a *display* subgrouping inside large status groups (`eat` already uses it for `location`, `subscriptions` for `category`); overloading it would silently change two live indexes' subgroup headings. Add one explicit frontmatter key. Name recommendation: **`walk_by: <field>`** (alternatives `walk_group`, `group_by` considered and rejected: `group_by` collides with the existing `group_field`/`RecordGroup` vocabulary, `walk_group` reads as a noun not a key). Semantics:

- Value is a schema field key; it must resolve to a `FieldKind::Choices` field, else `bob albums check` reports `walk_by_unknown_field` / `walk_by_not_choices` and the walk falls back to flat title order (fail-open, never a damaged line).
- Single-valued grouping reuses the existing `group_value` literal semantics (scalar choice, or a one-element list on a `list: true` choices field; multi-valued records fall into the trailing needs group rather than being duplicated — duplication would break the ring's total/position accounting).
- Order is declaration order of the field's `values`, exactly like `group_records`; empty groups are skipped; records with missing/unknown values form the trailing needs group (`⚠️ Needs a status` pattern) so they stay reachable instead of vanishing. Whether `walk_by` defaults to the display `group_field` when unset: **no** — unset means today's flat title order, so the five existing albums change zero bytes until Bryan opts in.

### Grouped `[n` / `]n` and jumping `[N` / `]N`

- With `walk_by` set, the album's canonical walk order becomes **grouped**: groups in declaration order (needs group last), members in `title_order` within each group, ring wraps across the group boundary. `bob albums sync` rewrites the walk lines once (same guarded transaction as today); `bob records check` lints the new order; the plugin's rail, footer `Links N/M`, and `⟳ syncing` logic are unchanged because they already read the written line plus live membership.
- `[n` / `]n` then automatically "walk through all record notes with that field set to the same value in sequence before moving on" — no new key handling, because they follow the written neighbors. This is the elegant half of the request: the grouping lives in the walk lines, not in the keymap.
- `[N` / `]N` on a record = **first record of the previous/next nonempty group** (title-first within that group, wrapping; singleton groups land on their one record; the needs group counts as a group). From the middle of `future` (3 records), `]N` lands on the first record of the next declared section that actually has records, not the next alphabetical neighbor. When `walk_by` is unset, `[N` / `]N` on a record have no group to jump to and show the no-group notice (do not silently alias to `[n` / `]n` — silent aliasing would teach a lie about what the key means).
- The 12-record zettel album is small enough that the reorder is reviewable in one `sync` diff; `eat` (105 records) is the reason the opt-in matters — its walk lines must not churn.

## 5. The configuration mechanism: compute, don't author (except anywhere)

Bryan's first thought — "look for links that start with `<<` or `>>`" — is right about *one* thing: `[N` / `]N` must work "in any Obsidian note somehow," and labeled links are already the `n`-family configuration language. It is wrong as the *primary* mechanism for the three named surfaces, for three reasons:

1. **Daily/period targets are computable and the computation already exists.** Authoring `<<` links would duplicate `PeriodId::{prev,next,parent,start,quarter_weeks,year_quarters}` into Markdown, then require a migrator, a template change, and eternal sync to keep the copies honest across ISO year boundaries. The existing `[n` / `]n` design already proved the alternative: zero authored bytes for periods beyond the one nav line, with creation delegated to `bob periods ensure`.
2. **Record targets are bob-owned.** Walk lines are machine-maintained (`bob albums sync` plans every index, walk line, and catalog in one transaction; `tidy` never touches walk lines). Hand-authored `<<` links in records would fight the sync the way hand-edited nav lines once fought it — the `ExtraText`/`DuplicateLines` damage states in `walk.rs` exist precisely because of that fight.
3. **`<<` / `>>` as literal labels are ugly and ambiguous.** In body text `<<` reads as a shell heredoc and `>>` as an append redirect; in Live Preview they compete with the existing `‹` / `›` arrow language that Bryan already reads fluently. The beautiful spellings (`«` / `»`, `‹‹` / `››`) are not on his keyboard.

**Recommended split (the core design judgment):**

- **Daily, period, and `walk_by`-configured record notes: no new authoring at all.** `[N` / `]N` targets are computed (date math / group math), rendered in the property-card rail and the walker footer, and followed without ever writing the note. This is the "configurable somehow" answer for the named surfaces: the configuration *is* the note's kind plus (for records) the one `walk_by` key.
- **Every other note: authored `<<` / `>>` links are the configuration.** Generalize the link matcher: `[N` follows the first body link whose rendered text *starts with* `<<`, `‹‹`, or `«`; `]N` follows the first whose text *starts with* `>>`, `››`, or `»` (trimmed, case-sensitive, same first-body-link-outside-frontmatter/fences scoping as `[n` / `]n`, same `openOrCreateLinkCandidate` creation semantics for non-period targets). Accept all three spellings per direction so source stays typable (`<<`) while render can be beautiful (`«`). This gives Bryan the "configurable in any note" he asked for with zero frontmatter, zero settings tab, and zero new grammar — it is one `if` beside `renderedLinkMatchesNavLabel`, not a new subsystem.
- **Albums: `walk_by` is the configuration.** One key, validated by `bob albums check`, consumed by `bob albums sync` and the record rail/footer. No per-record authoring.

This preserves the request's spirit (typable `<<` / `>>` work everywhere) while refusing its letter where the letter would create a second source of truth.

## 6. `[{` / `]}` fall out naturally

Once `n` gains an uppercase walk, no repeat-layer redesign is needed — just fill the null:

- Add palette commands `open-prev-group-link` / `open-next-group-link` (the `[N` / `]N` handlers), wire the vault vimrc (`nnoremap [N …`, `nnoremap ]N …` — note: these are bracket+Shift-letter, not Vim `<<`/`>>` shifts, so no Vim conflict), and set `BRACKET_REPEAT_UPPERCASE_PLANS.n = {forward: openGroupLink("next"), backward: openGroupLink("prev")}` in `546-plugin-bracket-repeat.js`.
- `BRACKET_REPEAT_PLANS.n` stays `openLabeledBodyLink` (lowercase, now group-ordered on configured albums). So after `]N`, `]]` steps within the landed group (`]n`) while `]}` jumps to the next group (`]N`) — exactly the `s`/`S`, `w`/`W`, `b`/`B` pattern reviewers already know.
- Update the two "no link variant" strings (the `BRACKET_REPEAT_NO_UPPERCASE_NOTICE` and the `547` indicator `upperTooltip`) to name `]N` / `[N`, and keep the family letter `n` in the `[[ s w n b ]]` selector — no fifth letter.

## 7. Property cards: dock the far links, hide the raw lines

The `bob-cli-nh` context (intention card plan `period_intentions.md:228-265` and the title-block consolidation's resolutions A7 + title-slot spike) already decided the pattern: the card owns the title row, nav becomes a **docked footer rail** with reveal-on-touch, raw nav paragraphs hide only while the rail cleanly owns them, everything fails open.

Apply it twice:

- **Daily/period intention card.** Today the card mounts above the `^gtd` line / strip fences, skipping H1/nav/link lines, and only when a field is nonempty (with the always-mount amendment pending from the title-block epic). Add a footer rail row: `« Mon 9 · ‹ Tue 10 · ↑ W47 · Thu 12 › · Mon 16 »` (labels computed: far arms use the Monday `day_label`, near arms reuse today's `prev`/`next` labels, center reuses the existing parent link). Missing far targets render dimmed with `+` and the `ensure` tooltip; yearly notes render only the near rail (far arms hidden, not disabled placeholders — a disabled `«` on every year note would be year-round noise). Below `28rem` collapse to glyphs `« ‹ ↑ › »` with full accessible names, mirroring the record rail's `‹ 3/104 ›` collapse. The raw daily/period nav paragraphs hide under the same StateField block-replace + selection-reveal mechanism the title-block epic specified for H1s, generalized to nav lines; embeds, popovers, Source mode, and mobile keep native rendering.
- **Record card.** The rail already exists (`‹ Pho House · 🍽️ Eat · 3 of 104 · Ramen Ya ›`). Extend it, don't replace it: when `walk_by` is set, the center gains the group (`🍽️ Eat · section · 3 of 12`), and the far arms appear *only* as keyboard-accessible overflow (the rail stays three arms visually; `[N` / `]N` targets surface in the footer's tooltip and the `n` panel, not as five crowded links). Rationale: record titles are long (`Microsoft CEO thinks model-agnostic architecture is good`), five arms plus a 104-count center cannot survive 375px. The group jump stays a keymap + footer affordance, not a fifth and sixth visible link.

In both cases the card never writes the note; writers (`bob periods ensure`, `bob albums sync`, the `==` editors) own bytes. A failed mount, a torn-down plugin, or a mode switch restores native nav lines — the same fail-open contract the title-block epic requires.

## 8. Walker footer: give `n` its hints

The `n` panel is the only walker with an empty hint slot. Fill it context-sensitively (short strings — the bar sheds end-first as it narrows):

- Daily: `hint: "[n prev · ]n next · [N Mon · ]N Mon"` (actual Monday labels, e.g. `[N Nov 9 · ]N Nov 16`); tooltip spells out full paths + create affordances.
- Week: `hint: "[n W44 · ]n W46 · [N W14 · ]N W40"`; quarter/year analogous (`[N Q1 · ]N Q1`); year shows only the near pair.
- Grouped record: `hint: "[n prev · ]n next · [N §prev · ]N §next"` where `§` names the `walk_by` field's label (`section`), e.g. `[N prev section · ]N next section`; `dueText` stays `Links N/M` and the tooltip names the group (`Memory is 2 of 3 in Future Work · alphabetical, wraps across 8 sections`).
- Generic note with `<<`/`>>` links: `hint: "[n prev · ]n next · [N « · ]N »"`; without them, only the near pair (and the indicator tooltip, not the bar, explains that `<<` links would enable the far jump).

Also update the `s`/`w`/`b` panels' "no uppercase" copy paths that enumerate `]S / [S, ]W / [W, or ]B / [B` — they must now include `]N / [N` when the remembered family is `n`, else the bar will keep teaching the old limitation after the feature ships.

## 9. Critique: is this a good idea, and what changes

**Yes — with the split above, this is a good idea.** Three independent navigational needs (week-scale daily travel, quarter-scale period travel, section-scale zettel reading) currently share one answer: repeated `[n`/`]n` presses plus mental date/group arithmetic. Each is a real daily friction (the zettel album just gained 14 records in a day per the `nh` plan's own example intentions), each maps cleanly onto the existing bracket-repeat mental model (lowercase steps, uppercase leaps — the `S`/`W`/`B` precedent), and none requires new vault bytes except the one `walk_by` key. The beautiful half matters too: far links belong in the card rail where Bryan's eye already is, not in a second authored nav line he must maintain.

Adjustments the request needs (Bryan can veto any individually):

- **A1 — Compute, don't author, for the named surfaces.** Daily/period/record far targets are derived; no `<<` links are written into daily, period, or record notes. Authored `<<`/`>>`/`«`/`»`/`‹‹`/`››` links are the *generic-note* configuration only.
- **A2 — Accept six spellings, render two.** Match `<<`, `‹‹`, `«` (prev-group) and `>>`, `››`, `»` (next-group) as prefixes, mirroring the existing `‹`/`>` arrowH equivalence. Source stays typable; cards render `«` / `»`.
- **A3 — New album key `walk_by`, not `index_by` reuse and not a bare "grouped field".** Validated choices-only; unset means today's flat walk (zero churn for `eat`/`movies`/`tv`/`podcasts`/`subscriptions`).
- **A4 — Only `sase_blog_zettel` gets `walk_by: section` now.** The other five albums get none (table in §4). `subscriptions.cadence` is the sole named follow-up candidate.
- **A5 — Grouped `[n`/`]n` follow rewritten walk lines.** The grouping changes sync output once per configured album; the keymaps themselves need no new walk algorithm beyond reading neighbors. Do not implement a parallel plugin-side grouped order that disagrees with the written lines.
- **A6 — Yearly (and `all_time`) genuinely have no far walk.** Hide the arms; show the standard no-target notice on `[N`/`]N` rather than a disabled jump or, worse, a cross-hierarchy surprise (e.g. year `>>` to next year's Q1 would change levels mid-gesture).
- **A7 — `[{`/`]}` route to `[N`/`]N` when the family is `n`.** Fill the null uppercase plan; keep the `[[ s w n b ]]` four-family selector.
- **A8 — Missing-file honesty in the rail.** Far arms for nonexistent-but-creatable week/quarter/year/daily targets render dimmed with `+` and an explicit `creates it` tooltip (the links footer's `createEligible` pattern); nonexistent record targets never render (records never auto-create); failed mounts fail open to native nav.

What I would *not* do: per-note frontmatter toggles for daily/period far jumps (the note kind already implies the math — configuration would be ceremony); a settings-tab switch (Bob plugins deliberately have no settings tabs — see `docs/bob-navigation-hotkeys.md:700-706`); or `<<`/`>>` as literal Vim keymaps (the request's `[N`/`]N` bracket keys are already the Vim-safe bindings; `<<`/`>>` in Vim normal mode are shift operators and must keep working as such).

## 10. Recommended solution

**Phase 1 — Plugin: generic `<<` + computed daily/period far walk (no bob-cli).** Generalize `680-plugin-link-parse.js` with `renderedLinkMatchesGroupLabel` (six-spelling prefix match), add `open-prev-group-link` / `open-next-group-link` palette commands implementing §2–§3 date math via the ledger-tools `periodNotes` date helpers plus daily-path parsing (reuse `week_for_date` semantics in JS), wire `490-plugin-lifecycle.js` commands + vimrc `nnoremap [N` / `]N`, fill `BRACKET_REPEAT_UPPERCASE_PLANS.n`, update the `547` indicator tooltips and the no-uppercase notice, and fill the `n` footer's `hintText` per §8. Acceptance: `[N`/`]N` on `2026-W30` offer `W14`/`W40`; on a daily offer the two surrounding Mondays; on a year show the no-target notice; `]}`/`[{` follow the `n` family; authored `<<`/`>>` links in a scratch note work with zero bob involvement.

**Phase 2 — bob-cli: `walk_by` + grouped sync (gated, one album).** Add `walk_by: <key>` to the album declaration, validate in `bob albums check` / `bob records check`, change `ring_slots` to grouped order when set (groups in `values` declaration order, needs group last, `title_order` within groups), and let `bob albums sync` rewrite the 12 zettel walk lines once. Set `walk_by: section` on `sase_blog_zettel.md` only. Acceptance: `bob albums sync --dry-run` shows only the 12 zettel walk diffs; `eat` (105 records) shows none; `bob records show` reports the `walk` object with `group {field, value, label}` already present per `docs/records.md:830-839` plus the new grouping.

**Phase 3 — Cards + footer polish.** Dock the daily/period far rail under the intention card with hide-while-owned + selection reveal (generalizing the record rail's dock-and-reveal and the title-block A7), extend the record rail's center with the group name, fill the `n` footer hints/tooltips per §8, and prove the narrow (`≤375px`), grayscale, forced-colors, and fail-open (Source/embeds/mobile/teardown) matrix the title-block epic requires. Collapsed cards keep kicker + title + one muted line (group for records, Monday range for periods).

**Phase 4 — Docs, vimrc, deploy.** Update `docs/bob-navigation-hotkeys.md` (commands table, bracket-repeat matrix, link-label grammar), `docs/record-card.md` (grouped rail), `docs/intention-card.md` (far rail), the vault `obsidian_vimrc.md` (`[N`/`]N`), and `bob plugins sync`. No `bob-cli` version bump or changelog entry beyond the normal train (per `decisions:bob-cli-releases-ride-a-daily-train`).

**Later, separately accepted:** `subscriptions` `walk_by: cadence` if Bryan wants it; `index_by`-vs-`walk_by` unification only if two albums prove the keys want to merge; never a daily/period byte migration.

## Verification and sources

- Vault (apollo, 2026-11-20): `sase_blog_zettel.md` frontmatter (status 6 choices, section 16 choices, `index_facets: [section, claim]`), 12 records across 8 sections; `eat.md` (`index_by: location`, 105 records); `movies.md` / `tv.md` (`verdict` choices, 12/23 records, overwhelmingly `to_watch`); `podcasts.md` (`category` free-text suggest, 15 records); `subscriptions.md` (`index_by: category`, `cadence` choices, 28 records); `2026/2026-W30.md` nav `‹ W29 · ↑ Q3 · W31 ›` with parent `2026-Q3`; `2026-Q3.md` children `W27–W39`; `2026/20261119.md` nav `prev · W47 · next`; far targets `2026-W14`/`2026-W40`/`2026-Q1`/`2026-Q4`/`2026.md` all exist.
- bob-cli: `src/native/periods/calendar.rs` (`PeriodId`, `quarter_of_week`, `prev`/`next`/`parent`/`start`/`link_target`/`quarter_weeks`/`year_quarters`), `src/native/periods/scaffold.rs:59-111` (nav emitters), `src/native/periods/migrate.rs:923-939` (daily nav rewrite), `src/native/albums/grouping.rs:103-202` (`group_field`, `LARGE_GROUP`, `title_order`), `src/native/albums/walk.rs:136-191` (`ring_slots`, `render_walk_line`, wrap/singleton), `docs/records.md:434-502` (walk contract), `docs/periods.md:1-116` (calendar + scaffold contract).
- bob-plugins: `docs/bob-navigation-hotkeys.md:525-611` (repeat + footer indicator), `plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js:1-13` (label matcher), `src/546-plugin-bracket-repeat.js:33-65` (uppercase null), `src/547-bracket-mode-indicator.js:27-30` (no-link-variant tooltip), `src/670-plugin-project-files.js:117-169` (period creation + `openLabeledBodyLink`), `plugins/bob-ledger-tools/src/124-links-walker-footer.js:1-260` (compass, `createEligible`, empty `hintText`), `docs/record-card.md:24-69` (position + rail), `docs/intention-card.md:1-140` (mount/placement/editor travel), vault `obsidian_vimrc.md` (all bracket mappings).
- Prior research: `research:202611/property_card_title_block/property_card_title_block.md` (docked rail + reveal-on-touch + always-mount + fail-open pattern reused in §7).
- Memory: `glossary:album-note`, `glossary:record-note`, `glossary:period-note`, `glossary:walker-footer` (terms, via `sase memory read`); `decisions:bob-cli-releases-ride-a-daily-train` (no out-of-train version work).

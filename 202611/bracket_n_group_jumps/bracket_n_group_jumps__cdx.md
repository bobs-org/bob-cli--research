# Group-aware note navigation: a design for `[N` and `]N`

Independent research by **cdx**, 2026-11-20. This report was developed from the requested prerequisite report, audited project context, source code, read-only vault queries, and official documentation. No report or findings from the other researchers in this swarm were consulted.

**Recommendation:** add group navigation to the existing `n` walk family. Keep ordinary Markdown links as its portable representation, use `«` / `»` for generated group links and accept `<<` / `>>` for hand authoring, and give albums an explicit `walk_by` field. Make the keyboard, property-card rail, and walker footer use one destination model. Preserve the requested calendar semantics exactly, including first-child landings, missing targets, and the absence of generated group links on yearly notes.

This is research, not implementation. No plugins, source code, album configuration, or vault files were changed. The album settings below are concrete recommendations for the eventual adoption step; adding an unsupported property to the live vault now would not enable the behavior.

## Is this a good idea?

Yes. The existing uppercase walks already mean a larger step: review group, task lane, or bank day. Adding an uppercase member to the currently exceptional `n` family makes that vocabulary more consistent. It also gives the property-card footer a useful purpose beyond previous/next decoration.

The strongest use case is the SASE writing album. Its twelve zettels are currently in one title-sorted ring, while their required `section` choices encode the order of the article. Walking the article in section order is meaningfully different from walking alphabetical titles. The daily and period cases are similarly predictable once the labels name the scale: **previous week**, **previous quarter**, **previous year**.

Three cautions should shape the design:

1. **A group jump is not a reversible note step.** From W30, `[N` goes to W14; `]N` from there goes to W27, not W30. This is correct under the requested rule. The same applies to a middle record in a section. Teach “first note of the adjacent group”; use ordinary back history to return to the exact origin.
2. **The difficult part is agreement, not the two keys.** There are already separate parsers, a Rust record sorter, a JavaScript record sorter, a rendered rail, and a status footer. A superficial implementation can show one destination, execute another, and continually mark valid links stale.
3. **Do not make group membership implicit.** Today an album's visual index picks a choice field, while `index_by` supplies conditional subgroups only above twelve members. Neither is an appropriate hidden source of navigation policy.

I would take this approach rather than introducing a generic hierarchy browser, configurable expressions, several simultaneous grouping levels, or a new persisted navigation session. Those would add concepts without improving the requested first use cases.

## What the current system establishes

The following are observations, not proposed behavior. Source details and revisions are collected under Evidence below.

- `src/native/periods/calendar.rs` already implements Bob's exact hierarchy: Monday–Sunday ISO weeks; quarters W01–13, W14–26, W27–39, W40–52/53; ISO years; `all_time`. These are **not Gregorian quarters**.
- `periods/scaffold.rs` writes previous/parent/next links. `periods ensure` is create-only for existing notes with body content; changing a scaffold alone will not update old notes.
- `albums/walk.rs::ring_slots` sorts the whole album by lowercase title and then path. It builds a circular ring. One record has only the album link; two records point both ways to each other.
- `albums/walk.rs` recognizes a maximum of three links in the owned line. Adding two group links without changing that classifier would classify the line as damaged.
- The plugin's `242t-plugin-record-walk-model.js` independently reconstructs title order from immediate folder members and compares the stored links. It must be updated with the CLI; changing only Rust would make the rendered rail report perpetual syncing.
- `680-plugin-link-parse.js::renderedLinkMatchesNavLabel` recognizes any label starting with `<` as previous, and labels starting or ending with `>` as next. **An ASCII `<<` / `>>` extension collides with lowercase navigation today.** Its document scan excludes frontmatter and code fences, but is not a complete rendered-Markdown lexer.
- `546-plugin-bracket-repeat.js` already has an uppercase dispatch table. Its `n` entry is `null`; `[{` / `]}` currently display a “No uppercase link walk” notice when `n` is selected.
- Navigation's `walkMode.links({path, content})` supplies a read-only previous/next preview. Ledger Tools checks the active source revision and revalidates destinations before a footer click executes a command. This is the right seam to extend.
- Missing period targets already go through `api.periodNotes.ensureNote(path)`, which invokes `bob periods ensure -d <target first day>`. Missing album records are deliberately never created by these walk commands.
- The requested prerequisite report keeps Markdown nav bytes and docks their presentation into the property card, with source reveal on selection and native rendering restored on failure. This report extends that design rather than reopening title ownership.

The audited `bob-cli-nh` read showed phases 1–7 closed and adoption/glossary phases 8–9 still in progress. The implementation should rebase on the completed title-block work, as requested; this research does not presume that future code already exists.

## The behavioral contract

### One rule at two scales

| Keys | Meaning | Landing |
| --- | --- | --- |
| `[n` / `]n` | Previous/next note in this walk | Adjacent member |
| `[N` / `]N` | Previous/next group in this walk | First member of that other group |
| `[[` / `]]`, with `n` selected | Repeat the lowercase operation | Same as `[n` / `]n` |
| `[{` / `]}`, with `n` selected | Repeat the uppercase operation | Same as `[N` / `]N` |

Direction belongs to the key pressed, not the last direction used. Direct lowercase and uppercase commands both select family `n`, including when there is no destination, matching the existing family-command convention. Repeats preserve the selected family. Clicking an ordinary rail arm selects `n` and invokes the same command; following the parent remains ordinary parent navigation.

Do not add a separately remembered `N` family. After `]N`, `]]` should still move one note and `]}` should move one group. On a yearly note, or an ordinary note without an uppercase destination, `]}` should explain the absence instead of falling back to another family or a lowercase step.

The current `n` family ignores Vim numeric counts. Keep direct/repeat count parity in v1 rather than quietly introducing asynchronous multi-note walks. A later decision could add counts consistently to both scales; it is unnecessary for this feature.

All successful moves reuse the current leaf-reuse and jump-history path. A no-op, failed creation, invalid target, or stale click must not add a fictitious history entry.

### Calendar destinations

Define the destination as **the first child of the adjacent parent**, evaluated from the current note's date/identity, never from the wall clock:

```text
previous_group(note) = first_child(previous(parent(note)))
next_group(note)     = first_child(next(parent(note)))
```

Use a typed period/calendar helper; do not subtract 13 weeks from an arbitrary weekly note, use Gregorian quarter dates, or infer the hierarchy from whichever target files happen to exist.

| Current kind | Parent group | `[N` | `]N` |
| --- | --- | --- | --- |
| Daily | ISO week | Monday of the previous week | Monday of the next week |
| Weekly | Bob quarter | W01/W14/W27/W40 starting the previous quarter | W01/W14/W27/W40 starting the next quarter |
| Quarterly | ISO year | Q1 of the previous ISO year | Q1 of the next ISO year |
| Yearly | `all_time` | No generated group link | No generated group link |
| `all_time` | No temporal sibling group | No generated group link | No generated group link |

Concrete acceptance examples:

| Source | Previous group target | Next group target |
| --- | --- | --- |
| `2026/20261120.md` | `2026/20261109.md` | `2026/20261123.md` |
| `2026/2026-W30.md` | `2026/2026-W14.md` | `2026/2026-W40.md` |
| `2026/2026-W01.md` | `2025/2025-W40.md` | `2026/2026-W14.md` |
| `2026/2026-W53.md` | `2026/2026-W27.md` | `2027/2027-W01.md` |
| `2026/2026-Q3.md` | `2025/2025-Q1.md` | `2027/2027-Q1.md` |
| `2027/20270101.md` | `2026/20261221.md` | `2027/20270104.md` |

The last example exposes a crucial distinction: daily file directories use the date's Gregorian year, while the containing week uses its ISO week-year. January 1, 2027 is in 2026-W53. The date calculations above were independently checked with Python's standard-library ISO calendar; the existing Rust tests also explicitly cover 2026-W53 and its fourteen-week Q4.

Calendar navigation is not circular. At the calendar library's supported bounds, report no destination; never wrap 2999 to 1970. Respect `Option`-returning period methods instead of introducing new `expect` calls at the boundaries.

### Record groups

Add one top-level, optional album property:

```yaml
walk_by: section
```

Absence preserves today's title-sorted ring. Remove the property to turn grouping off. Do not introduce `auto`, `false`, a nested mapping, or per-record overrides in v1. “Any note can author navigation links” does not imply that a single managed record should override its album's ordering.

The album editor should expose **Walk by: Title only / Section / …**, listing eligible schema fields and showing a small before/after preview. Label it separately from **Index subgrouping**. Include it in guarded update operations, the relevant fingerprint, validation, Undo, field rename/removal behavior, and album reports. A field rename should update the reference in the same transaction; removing the selected field should require explicitly clearing/changing the setting in that transaction.

The deterministic walk algorithm is:

1. Collect the same immediate Markdown album members the current walk owns. Do not introduce status filtering, recurse into nested directories, or silently drop invalid members.
2. Bucket by the selected scalar field. Choice keys use their stored value as identity, with occupied groups ordered by the schema's declared choice order. Never sort choice labels or emojis alphabetically.
3. Sort members within each bucket using the existing title-then-path comparator.
4. Flatten the buckets into one circular record order. Lowercase moves one position in that flattened order, including across boundaries.
5. Uppercase moves to the first member of the preceding/following occupied bucket. Skip empty choice groups; those have no record to open.
6. Missing or invalid values form one final **Needs <field label>** bucket. Show the validation problem, but keep those records reachable. Do not silently place them into a valid choice.

For non-choice scalar fields, order text groups deterministically after trimming, Unicode normalization, and a documented case-insensitive comparison; numbers sort numerically and dates chronologically. Define these operations once and prove cross-language parity with shared fixtures. Reject list-valued grouping fields in v1: a record in multiple groups breaks the simple one-ring model. URL fields can use exact trimmed values, but should not be promoted as useful defaults in the picker.

**Linked text needs an explicit identity rule.** Use the resolved vault-relative link target including its heading/block subpath, ignoring the display alias. Do not group different linked places merely because their visible labels match. Plain text stays a text key; a literal `Cranford` does not silently become the same value as a link to a town block. Sort by display label, with the stable identity as tie-breaker, and disambiguate equal labels with target context. This intentionally differs from `index_by`, whose current display-folding is suitable for a visual subgroup but can erase navigation identity. The restaurant data includes both plain and linked locations, making this more than a theoretical concern. If those are later unified, make it an explicit field-value cleanup, not a navigation side effect.

With one occupied group, lowercase still walks its members, but uppercase is unavailable: **Only one section**. With two groups, both uppercase directions legitimately target the other group's first record. At the outer record/group boundary, keep the existing circular behavior and disclose it with `↺` and an accessible label. Calendar destinations never use that wrap.

## Album adoption based on the actual vault

`bob albums list -f json` reported **six albums and 195 records**. All current record walk lines were reported current. Folder-scoped `bob query` calls independently inspected the zettel sections, podcast categories, and restaurant locations. These observations are a snapshot, not a permanent census.

| Album | Observed evidence | Recommended setting | Why |
| --- | --- | --- | --- |
| `sase_blog_zettel.md` | 12 records, all with required `section`; 8 occupied sections out of 17 choices; all currently Seed | `walk_by: section` | Follow the article's schema-declared section order. `status` currently gives no useful jump. |
| `eat.md` | 105 records, all with location; current `index_by: location`; recurring Cranford, Westfield, Garwood, NYC and other locations | `walk_by: location` | Geographic browsing is materially more useful than a 105-item alphabetical circuit. Preserve status as visible context; show linked/plain distinctions honestly. |
| `subscriptions.md` | 28 records: 9 To decide, 13 Active, 6 Cancelled; all statuses populated | `walk_by: status` | Walk the decision backlog together, then active commitments, then cancelled history. Cadence is less aligned with the album's stated purpose. |
| `movies.md` | 12 records: 10 To watch, 2 Watched; service populated for only 1 | `walk_by: status` | Stable, complete, and gives two meaningful groups. Service, year, and verdict are too sparse. |
| `podcasts.md` | 15 records: 9 Subscribed, 6 Unsubscribed; categories cover 7 topics with several singletons | `walk_by: status` | Separate current listening from historical rejection. Category is a reasonable alternate, but fragments this small catalog and mixes subscription state. |
| `tv.md` | 23 records, all To watch; service populated for 4 and recommended_by for 6 | Leave unset initially | No populated field currently yields compelling groups. Status becomes useful once Watching/Watched/Dropped are populated. Do not configure grouping just to expose another key. |

These settings change only the navigation sequence. Keep current status counts, index grouping, and `index_by` behavior. The album card should say, for example, **Walk by Section · 8 groups**, so the distinction is visible. Do not automatically reorder the existing index as an incidental consequence of this feature.

For the zettels, the observed choice order yields:

```text
What is SASE?       sase is many abstractions
Prompt language    Prompts Managed Like Code
Agent CLIs         Memory → Usage Limits and API Costs
Turn / Session …   Microsoft CEO thinks model-agnostic architecture is good
Beads              Beads and Birds
VCS                Host-owned Completion
Why not ready?     AI Slop → SASE is Too Complex
Future Work        Artifact Links → Bead Lifecycle → Bob Task Events
```

At **AI Slop**, `]n` opens **SASE is Too Complex**, `]N` opens **Artifact Links**, and `[N` opens **Host-owned Completion**. Its position is record 8/12, section 7/8, item 1/2 within the section. At the end of Future Work, `]n` and `]N` wrap to the first occupied section, not to the unoccupied Intro choice.

## Configuration and durable link syntax

I recommend extending the existing body-link convention, rather than adding parallel `nav_prev_group` and `nav_next_group` frontmatter pointers.

| Option | Strength | Cost | Verdict |
| --- | --- | --- | --- |
| Reserved double-chevron link labels | Ordinary links remain readable and clickable without Bob; extends current `[n` behavior; same bytes can feed the rail | Requires exclusive role classification and ambiguity handling | **Use this** |
| Flat frontmatter endpoint properties | Explicit structured fields; property UI can edit links | Creates a second navigation surface beside existing body links, with migration/precedence decisions | Sensible only if all note navigation is redesigned together |
| Nested `navigation:` YAML | Extensible and compact in Source | Nested properties lack native Properties editing; hides a simple two-link choice in configuration | Avoid for v1 |
| Compute all routes only in a plugin | No backfill for historical notes | Loses portable links and duplicates calendar/schema logic; harder to inspect and repair | Avoid as primary authority |

Obsidian officially supports custom display text for both wikilinks and Markdown links, plus folder-qualified destinations. That supplies a native representation rather than a new markup format. Its Properties documentation explicitly says nested properties are not supported in the regular property UI. [Obsidian links](https://obsidian.md/help/links), [Obsidian properties](https://obsidian.md/help/properties).

For an ordinary note, configuration can be as simple as:

```markdown
[[part_one/opening|<< Part one]] · [[part_three/opening|>> Part three]]
```

Generated links should use the cleaner typographic forms and the established right-edge next-arrow placement:

```markdown
[[2026/2026-W14|« Q2 · W14]] · [[2026/2026-W29|‹ W29]] · [[2026/2026-Q3|↑ Q3]] · [[2026/2026-W31|W31 ›]] · [[2026/2026-W40|Q4 · W40 »]]
```

Implement one exclusive classifier with longest-token precedence:

| Role | Accepted label forms |
| --- | --- |
| previous group | `« Label`, `<< Label` |
| next group | `» Label`, `>> Label`, `Label »`, `Label >>` |
| previous note | Existing exact `prev`, or single `‹` / `<` forms, **excluding double forms** |
| next note | Existing exact `next`, or single `›` / `>` forms, **excluding double forms** |
| parent | Existing `↑` convention; never either walk direction |

Reserve standalone marker tokens separated from human label text; do not interpret arbitrary prose containing angle brackets. Keep the old single-arrow forms compatible, but reject malformed mixed markers rather than silently classifying them as single arrows. Generating `«` / `»` also reduces accidental interaction with older lowercase ASCII matchers during deployment; it is not a substitute for reader upgrades.

For the new group roles, multiple distinct destinations must produce **Two next-group links — choose one** instead of “first link wins.” Identical repeated destinations may deduplicate. Preserve current first-match semantics for legacy lowercase links in this release, to avoid unrelated changes to existing notes. A managed five-link line is stricter: at most one of each role and exactly one correct parent.

The scanner must ignore YAML, fenced and inline code, Obsidian/HTML comments, escaped link examples, and embeds. Preserve heading/block subpaths when opening links. Use active editor text when available so a just-edited route is immediately honored. Ordinary notes do not need a property card for these keys or footer hints to work.

For records, Bob owns the entire recognized walk line; hand edits will be repaired. For ordinary notes, authored group links are the source of truth. For calendar notes, generated navigation belongs to the calendar writer/migration, while custom or damaged legacy lines must be reported instead of overwritten.

## Property-card rail and walker footer

Use two clearly ranked rows at the bottom of the card rather than squeezing five long targets into one line. The ordinary row remains primary. The group row has quieter text and double-chevron icons, with the scale named explicitly.

Conceptual weekly rail, not a rendered screenshot:

```text
‹ W29                    ↑ 2026-Q3                    W31 ›
« Q2 start · W14          QUARTER                    Q4 start · W40 »
```

Conceptual zettel rail at AI Slop:

```text
‹ Host-owned…          ↑ SASE Blog Zettel           SASE is Too… ›
« VCS             SECTION 7/8 · ITEM 1/2              Future Work »
```

These are one docked navigation component, not two extra cards. Reuse the title-block design's borders, spacing, hue, and source-reveal behavior. Keep the rail when the property card collapses. Do not add a second progress bar; the existing position treatment can remain, with the group count supplying the other scale.

At narrow widths, preserve two compact rows with stable left/center/right alignment, such as `‹ 8/12 ›` and `« Section 7/8 »`. Full destination titles and “first record of…” belong in tooltips and accessible names. On wide screens, show the destinations. Never rely on arrow color alone to explain direction, grouping, or availability.

Keep the existing 32px minimum record-rail target size and visible focus rings. This exceeds WCAG 2.2's ordinary 24px minimum target-size benchmark, though actual compliance depends on the complete layout and exceptions. [W3C target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

### Missing is a destination state, not a different destination

A future week note often does not exist. Do not skip to the next existing note, hide the route, or disable a valid calendar target. The exact requested first child remains the target.

| State | Appearance | Activation |
| --- | --- | --- |
| Exists | Normal link | Open through the shared navigation command |
| Missing canonical day/period; writer available | Dashed-outline target with `＋`; accessible “Not created — create and open …” | Explicit key/click invokes the existing correct writer, then opens |
| Missing album record | Muted repair state, `⟳`, named missing record | No creation; refresh/repair the album walk |
| Invalid/unsafe target or required writer unavailable | Unavailable treatment with reason | No blank-note fallback; leave current note in place |
| No group route | No card group row; contextual footer explanation on command | No substitute action |

Store only the link, not `exists`, `+`, or a “future” label in Markdown. Resolve existence live and invalidate on file create/delete/rename. “Not created” is better than “future”: a past note can also be missing.

Missing period creation should reuse `periodNotes.ensureNote` with the target period's first date. It may ensure the normal ancestor/look-ahead chain as current behavior does; it does not promise exactly one newly created file. Daily targets must use the current date-aware daily-template creation path, with the target date instead of today. Ordinary manually configured destinations retain the existing safe general-note creation policy. No preview, hover, card render, or footer refresh creates files.

For existing targets, support page previews, keyboard focus, modifier/middle-click behavior, and jump history consistently. For missing targets, all gestures must preserve the same creation guard; a modifier click must not bypass the record prohibition or create a blank period file.

### Walker footer hints

The status footer is a compact preview of the same model. Do not grow it into a second property card. When `n` is selected, retain ordinary destination arms and add a concise scale hint:

- Day: `[{ / ]} week` with tooltips naming the exact Mondays; full help also names `[N / ]N`.
- Week: `[{ / ]} quarter`.
- Quarter: `[{ / ]} year`.
- Grouped record: `Section 7/8 · 1/2` plus `[{ / ]} section`; total album position can remain in the tooltip or existing counter.
- Generic configured note: `[{ / ]} group` with the authored labels.
- Year: no group affordance; an attempted uppercase action says **Year notes have no group jump**.
- Single-group album: **Only one section**, without a clickable self-loop.

Show hints when the capability exists, even if a valid target is not created. An ordinary note with only uppercase links should still have a useful `n` footer; today's “no previous/next links” empty state must not hide those routes. Footer clicks revalidate role, target, source revision, and availability before invoking the same command used by the keyboard.

## Implementation architecture and the main risks

### One shared destination model

Extend the navigation API with additive group destinations and explicit action availability. The current API is already `walkMode` v6; feature-detect a new capability/member rather than accidentally treating the older links-preview v2 threshold as the current whole API version.

A conceptual projection is:

```text
NavigationPreview {
  sourcePath, sourceRevision,
  prev, next, prevGroup, nextGroup,
  groupKind, groupLabel,
  diagnostics
}
Destination {
  role, target, resolvedPath, subpath, label,
  state: exists | creatable | unavailable,
  creationKind?, reason?, wraps?
}
```

This is a proposed shape, not a claim that these fields already ship. `state` must reflect the same resolver/creator used by execution; path existence alone is insufficient. Put exclusive label classification and open/create policy in the navigation layer. The card rail and walker footer consume it instead of performing independent link scans. Parse one source revision once, then project it to all surfaces.

Bob remains the authority for generated calendar destinations and record ordering. For grouped records, extend album `walk` reports with the selected field, ordered groups, first members, member positions, and an appropriate source/settings fingerprint under a new grouped-walk capability. Prefer consuming that ordered projection over teaching Ledger Tools a second schema-sorting engine. A stale or unavailable report can still render recognized stored links; suppress uncertain counts and explain syncing rather than inventing alphabetical positions. This is a deliberate grouped-mode extension to today's local alphabetical-position model.

A changed schema field, choice order, record title, grouping value, file membership, or group head invalidates the relevant projection. Guard late async responses against source changes and album fingerprint changes. Do not run a whole-vault scan or a CLI process on every keypress. Reuse the current album report cache and coalesce refresh/repair requests.

### Group-head changes widen the write set

The existing radius optimization edits a newly created record and neighbors whose rendered line changed. With group links, inserting a new first member can change **every record's group arm in both neighboring groups**, not merely two adjacent records. Moving a record between groups, deleting the first member, changing its title, or changing choice order has similar effects.

Plan old and new complete album models and diff canonical lines. Keep the transaction's staged postimages, fresh-byte checks, and rollback guarantees. Do not assume the three-file radius remains correct. This may still be inexpensive for the observed 195 total records, but correctness comes before an unproven optimization.

The line parser, sanitizers, tidy probes, migration checks, fixtures, record-card classifier, and generated repairs must all understand the expanded form. In particular, strip or escape reserved double-chevron markers in user titles before building aliases; do not let a title beginning with a marker change its link role.

### Historical calendar adoption is real work

Changing scaffolds and tomorrow's template is insufficient. Ship a bounded, previewable navigation migration over existing canonical daily/weekly/quarterly notes. Recognize supported existing header/nav shapes; change only the managed navigation span; retain H1 bytes and all other content. Preserve BOM/newlines, authored placement, and the prerequisite's source-reveal rules. Report custom/ambiguous shapes for explicit repair rather than guessing.

Do not rely on `periods ensure` to rewrite old bodies—it intentionally does not. Do not make merely opening a historical note backfill its links. Calendar migrations and future daily-template updates need the same calendar fixtures, especially ISO year crossings. The exact current daily template and vault Vim mapping source must be confirmed at implementation time; plugin docs identify them as vault settings, and this research did not inspect those vault files directly.

### Rollout order

1. Finish the property-card title-block prerequisite and recheck its actual rail host/ownership APIs.
2. Ship reader support first: exclusive roles, five-link recognition, shared preview/actions, grouped-report capability handling, and graceful absence. Ensure old title-order validation cannot auto-repair a new grouped line back to alphabetical order.
3. Implement Rust grouped walks, album configuration/update support, and calendar link generation/backfill planning with deterministic fixtures.
4. Add the two commands and actual `[N` / `]N` Vim mappings; connect uppercase repeats, rail actions, and footer hints. Command registration alone does not install Vim mappings.
5. Preview the proposed album order and historical-note changes. Apply the recommended five album settings and calendar backfill only after compatible readers are deployed. Leave TV ungrouped.
6. Verify in real Obsidian, deploy from the plugin source repository, and document Source-mode configuration and the first-member landing rule. Preserve ordinary daily/period creation paths and the yearly exception.

## Acceptance evidence worth requiring

These are targeted proofs for the risky behavior, not a request to duplicate every implementation detail in tests.

| Area | Required proof |
| --- | --- |
| Exclusive roles | Every double-arrow spelling is ignored by lowercase matching; legacy single arrows still work; examples in inline/fenced code, comments, YAML, and embeds do not configure routes |
| Ambiguity | Distinct duplicate group targets refuse clearly; shared identical targets deduplicate; managed extra prose is preserved and diagnosed |
| Calendar | All examples above, leap days, Mondays/Sundays, ISO-year crossover, W53, Q1/Q4, year/all_time absence, and supported bounds |
| Ring invariants | Every record appears once; lowercase forward/backward are inverse for rings; each group is contiguous; uppercase always chooses another occupied group head; one/two-group cases and wrap are explicit |
| Sorting | Choice declaration order; title/path ties; numeric 2 before 10; Unicode parity; missing/invalid fields; same link with different aliases; different targets with equal labels; list-field refusal |
| Changed group head | Insert, rename, delete, move group, and choice reorder update all affected group arms atomically, including other groups' members |
| Surface agreement | Keyboard, ordinary click, modifier/middle click, card rail, status footer, and repeat select the same target and enforce the same missing-record guard |
| Async behavior | A click on stale source/album state refuses or refreshes; late reports never paint a different note; refresh storms coalesce; no render-triggered creation |
| Ownership | Duplicate/damaged nav remains visible; no hiding without a replacement rail; Source, selection touch, splits, embeds, teardown, plugin failure, and older CLI restore usable native content |
| UI | Light/dark, 375px and wide, long labels, missing calendar destinations, one group, invalid schema, visible focus, grayscale/forced-colors, and empty day identity |
| Migration | Dry-run diff and applied bytes agree; second run is empty; custom content/line endings retained; future scaffolds/templates agree with historical backfill |

The existing shared record-walk vectors and real-Obsidian `obsidian-record-walk-e2e.cjs` / `obsidian-walker-footer-e2e.cjs` are useful starting points. This research did not run an implementation test suite or claim a working UI prototype; the wireframes above are design sketches.

## Explicit adjustments and clarifications

- **A1 — Keep the `<<` / `>>` idea, but define roles rather than prefix heuristics.** Accept ASCII authoring; generate typographic `«` / `»`; fix lowercase collisions before adoption.
- **A2 — Add `walk_by`, separate from existing visual grouping.** No hidden dependence on choice-field order or the twelve-record `index_by` threshold.
- **A3 — Specify first-member landings and non-invertibility.** Previous group always means the previous group's first note, even from the middle of the current group. Back history preserves exact-return behavior.
- **A4 — Distinguish calendar holes from empty record groups.** Calendar jumps keep the exact absent first child and can create it explicitly. Record jumps skip empty groups and never create a missing record.
- **A5 — Preserve record wrapping; do not add calendar wrapping.** One record group has no uppercase self-jump.
- **A6 — Scope field support to scalars initially.** Lists and computed expressions need a different membership model. Invalid/missing record values remain reachable in a final repair bucket.
- **A7 — Do not auto-configure every album.** Configure five albums as specified; leave TV unchanged until its data supports useful grouping. This is a deliberate response to the requested “if so.”
- **A8 — Preserve source nav bytes and adopt old notes explicitly.** The visual prerequisite does not authorize hiding routes without replacement or silently rewriting old notes on open.
- **A9 — Keep repeat/count behavior coherent.** Extend family `n`, not a new family; retain its current count behavior in v1.
- **A10 — Use linked-value identity, not alias equality.** This avoids false group merges; plain/link duplicates need an explicit data cleanup if Bryan wants them unified.

## Evidence and limits

**Shared requested input:** `research:202611/property_card_title_block/property_card_title_block.md`, read through `sase artifact read`. Its nav-byte retention, docked rail, reveal-on-selection, always-present identity, and fail-open principles are treated as prerequisite design inputs. It is an earlier consolidated research report, not a report from this swarm.

**Audited context:** `sase bead read bob-cli-nh`; `sase memory read` for artifact/bead rules, Obsidian conventions, and Album Note / Record Note / Period Note glossary definitions. The Period Note memory still contains some pre-intention wording; current code and the in-flight epic were used for actual card behavior.

**Source revisions inspected:** bob-cli `ab34144686dedf2a8388a7b44ee110296c28e9f9`; bob-plugins `5c41b5b3c069bfbf3cf10d7b50944e88767f339b`. Repositories were opened through `sase repo open`. Chezmoi was also opened at `3623450f650acd403f9a2e35c4ac752b5d77e316`; no keymap source was established there and no changes were made.

Load-bearing source locations, relative to their respective repositories:

- **bob-cli:** `src/native/periods/calendar.rs` (`PeriodId`, parent/prev/next/start/quarter_weeks); `periods/scaffold.rs` (three-link generation); `periods/ensure.rs` (create-only/one-week look-ahead); `src/native/albums/walk.rs` (`ring_slots`, line parsing/classification, `WalkScope`); `albums/grouping.rs` (choice grouping, `LARGE_GROUP`, display folding, `title_order`); `albums/mod.rs` (album declaration/index fields); `albums/report.rs`, `albums/write.rs`, `albums/sync.rs`, `src/native/records/cli.rs` (walk integration); `docs/records.md`; `docs/reference/plugins/record-card.md`.
- **bob-plugins / bob-navigation-hotkeys:** `src/490-plugin-lifecycle.js` (command callbacks); `546-plugin-bracket-repeat.js` (uppercase `n: null`); `670-plugin-project-files.js` (body-link search, period creator); `680-plugin-link-parse.js` (arrow matcher); `482-walk-mode-nav-api.js` (read-only preview).
- **bob-plugins / bob-ledger-tools:** `src/124-links-walker-footer.js` (generation checks, existence/creation display, activation); `242t-plugin-record-walk-model.js` (independent alphabetical order and three-link classification); `242u-plugin-record-walk-rail-dom.js`, `242v-plugin-record-walk-rail.js` (rail); `292b-plugin-period-notes.js` (`ensureNote` and target-date creation); `240b-plugin-property-card-ownership.js`, `240c-plugin-property-card-host.js` (card family integration).
- **Plugin behavior docs:** `docs/bob-navigation-hotkeys.md`, especially bracket repeat and missing period creation; `docs/record-card.md`, especially rail fallback, wrap, narrow layout, and missing-record refusal.

**Vault evidence:** successful `bob albums list -f json`; successful `bob query --format markdown` queries `TABLE file.path, title, section FROM "sase_blog_zettel"`, `TABLE title, category, status FROM "podcasts"`, and `TABLE title, location, status FROM "eat"`. The query tool emitted unrelated ambiguous-link warnings; these results were cross-checked against album schema/count reports. Early richer DQL attempts were unsupported or unhelpful and were replaced with the supported folder-scoped forms. No broad filesystem parsing of the vault was used.

**External primary references:** [Obsidian internal links](https://obsidian.md/help/links), [Obsidian properties](https://obsidian.md/help/properties), and [W3C WCAG target-size guidance](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), consulted for link representation, native-property limitations, and interaction sizing. Architecture, album choices, sorting, and visual recommendations above are my conclusions from the local evidence, not claims made by those sources.

Remaining implementation questions are narrow: where the completed title-block work exposes its rail host, the actual vault-owned Vim/template deployment path, and how best to carry a grouped-report freshness token through the current cache. None requires changing the user-facing semantics recommended here.

## Recommended solution

**Build it as the larger step of the existing note walk.** Keep navigable Markdown links, add exact double-chevron group roles, introduce explicit `walk_by` configuration, and use one shared resolver for keys, the property-card rail, and the walker footer. Generate calendar routes from Bob's ISO hierarchy and record routes from ordered occupied scalar-value groups. Make absent calendar targets attractive, explicit create-and-open destinations; treat missing records as repair conditions. Adopt Section for the SASE zettels, Location for restaurants, Status for subscriptions/movies/podcasts, and leave TV alone for now.

The result should feel like a modest extension of familiar navigation: **lowercase moves one note; uppercase moves to the start of the adjacent group; the card shows where both will go.**

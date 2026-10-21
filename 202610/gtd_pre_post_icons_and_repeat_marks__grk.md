# PRE/POST checklist icons, and a quieter `repeat` mark

Researcher: `grk`. Independent report. Do not treat this as the swarm synthesis.

> **Research query:** Start rendering nice, appropriate icons in place of the `#gtd #pre` and `#gtd #post` tags that mark PRE and POST GTD morning-review checklist tasks. Also consider what (if anything) to do with the `repeat` task property so it looks nicer and takes less space in Obsidian. Lead the design so it is intuitive, reliable, and beautiful. Critique the plan, call out justified requirement changes, and recommend a solution.

**Evidence date:** 2026-10-21. bob-cli `docs/task-tag-marks.md`, `docs/date-marks.md`, `docs/freshness.md`; bob-plugins `bob-ledger-tools` fragments `138`/`264` (tag marks), `136`/`266`/`267` (date marks), `styles.css`; live vault via `bob query`.

## Bottom line

1. **Do it, and do it inside the existing mark family.** Replacing `#gtd #pre` / `#gtd #post` with icons is a good idea. The tags are load-bearing membership (`decisions:review-walk-is-tiered`) and must stay in the file. Display-only widgets that hide the pills are how Bob already turned `#task` into the teal hash and `#task #ref` into the open book (`docs/task-tag-marks.md`). Supercharged Links, a CSS snippet, a nested `#gtd/pre` tag, or rewriting the vault to emoji would all fight that family.

2. **Replace the pair with one glyph, not each tag with its own icon.** Membership is the AND of two whole-token tags. Two independent icons would lie the moment a stray `#pre` appeared, and they would leave a violet `#gtd` pill on every checklist row. The `#task #ref` book is the template: one contiguous `#gtd` + `#pre`/`#post` span becomes one silhouette; the `#task` hash stays.

3. **Glyphs: a matched sunrise / sunset pair in Lucide stroke language, muted ink.** PRE is a sun sitting on a horizon with short up-rays. POST is the same horizon with the sun resting on it and no rays (sunset). Shape carries PRE vs POST. They sit after the hash, before the title. Tooltip names the tags in the walk's own words. Not emoji, not a second teal identity hash, not small-caps `PRE`/`POST` chips (those words already live in the footer and `]s` notices).

4. **Do compact `repeat` as well, as a date-mark sibling.** Bryan is unsure about this one; the data decides it. The vault has **972** `[repeat:: …]` fields, **zero** `🔁` spellings, **98%** the same rule (`every day when done`), and the remaining long Dataview pill sits on every `gtd_daily.md` row the walk lands on. Dash/rotten/crowded already use Tasks `short mode` (emoji only). Source Live Preview is the gap. Ship a `↻ daily` mark in the suffix cluster, full rule on hover, no storage change.

5. **Two existing toggles, no new plugin, no Rust, no vault rewrite.** Checklist icons ride `toggle-task-tag-marks`. Recurrence rides `toggle-date-marks`. Without bob-ledger-tools the vault looks exactly as it does today.

The design is in [Recommended solution](#recommended-solution). Requirement changes are marked **ADJ-n**.

## What you see today

Verified 2026-10-21 against the live vault (`bob query --format json --tasks`) and the mark-family contracts.

### Checklist tags

| Quantity | Count | Notes |
| --- | --- | --- |
| Tasks with `#gtd` | 148 | |
| `#gtd` + `#pre` | 118 | 0 also carry `#post` |
| `#gtd` + `#post` (no `#pre`) | 18 | Morning review + Weekly prune |
| `#gtd` only (no `#pre`/`#post`) | 12 | All closed or cancelled, all in May-2026 archives |
| `#pre` without `#gtd` | **0** | |
| `#post` without `#gtd` | **0** | |
| Open checklist rows | **10** | 8 PRE + 2 POST, every one in `gtd_daily.md` |
| Tag order on those 10 | `#task #gtd #pre` or `#task #gtd #post` | Always adjacent, always `#gtd` first |

Open rows right now:

```text
- [?] #task #gtd #pre Clean up SASE agents…     [repeat:: every day when done]
- [?] #task #gtd #pre Review Calendar…          [repeat:: every day when done]
- [?] #task #gtd #pre Read Email                [repeat:: every day when done]
- [?] #task #gtd #pre Import inbox tasks…       [repeat:: every day when done]
- [?] #task #gtd #pre Check weather             [repeat:: every day when done]
- [?] #task #gtd #pre Brush teeth               [repeat:: every day when done]
- [?] #task #gtd #pre Take fish oil pills…      [repeat:: every day when done]
- [?] #task #gtd #pre Do morning stretches!     [repeat:: every day when done]
- [ ] #task #gtd #post Morning review: …        [repeat:: every day when done]
- [?] #task #gtd #post Weekly prune: …          [repeat:: every week on Monday when done]
```

Live Preview already replaces `#task` with the teal hash. The two violet tag pills and the Dataview `repeat` pill are the remaining noise. Vector TT3 of the tag-mark contract even names this on purpose: `#gtd` is left as a pill.

Approximate Live Preview of a PRE row today:

```text
- [?] ⌗  #gtd  #pre  Brush teeth   repeat | every day when done   + Oct 21   ⧗ tomorrow
         ^^^^  ^^^^                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         violet pills              ~30-character Dataview pill
```

`gtd_daily_done.md` repeats that pattern on every archived occurrence. The walk lands in this file every morning.

### Recurrence

| Quantity | Count |
| --- | --- |
| Recurring tasks | 972 |
| Stored as `[repeat:: …]` | **972** (100%) |
| Stored as `🔁` or `(repeat:: …)` | **0** |
| Rule `every day when done` | 953 (98%) |
| Other rules | 19, six distinct strings |
| Open recurring | **14** (10 in `gtd_daily.md`, 3 in `recur.md`, 1 in `cash.md`) |
| Bracket-field length | 24–41 characters (median 30) |

Other live rules: `every week on Monday when done`, `every week on Sunday`, `every month on the 1st`, `every 30 days when done`, `every 28 days`.

Tasks settings: `taskFormat: "dataview"`, `removeGlobalFilter: false`. Dash, rotten, crowded, and blocked notes already send `short mode`, so query results show only the 🔁 emoji. Source notes do not.

Date marks already compact `created` / `scheduled` / `completion` / `cancelled`. They deliberately leave `due`, `start`, and `repeat` alone (`docs/date-marks.md`). The leftover suffix pill on a checklist row is almost always `repeat`.

### The mark family this has to join

Bob already has a display-only decoration language in bob-ledger-tools:

| Mark | Stored form | Visible form | Ink | Contract |
| --- | --- | --- | --- | --- |
| Task tag | `#task` | teal hash ⌗ | identity teal | `docs/task-tag-marks.md` |
| Reading task | `#task #ref` | teal open book | same teal, replaces the hash | same, "Reference reading tasks" |
| Dates | `[scheduled:: YYYY-MM-DD]` etc. | ⧗ Fri, + Oct 21 | muted grey | `docs/date-marks.md` |
| Priority, freshness, progress, Today, unblocked | various | one glyph each | reserved hues | sibling contracts |

Shared rules worth copying, not reinventing: display-only; cursor or click reveals the source; session toggle; no marks in source mode; CSS masks (not emoji) at 1.08em; Tasks query results are CSS-only; `::` never appears in a tooltip (Dataview re-scans `innerHTML`); closed tasks rest fainter; `body.bob-*-marks` gates everything.

Hue table from the tag-mark contract, still in force:

| Hue | Already means |
| --- | --- |
| red | Blocked |
| orange | attention, ROTTEN, repair flags, Pending chip |
| yellow | In Progress |
| green | Next, fresh `✓ today` |
| blue | Ready lane |
| violet | remaining tag pills (`#prj`, lone `#gtd`, …) and links |
| teal | tracked-task identity (hash, book) |
| grey | priority and date marks |

PRE/POST and `repeat` have to pick from this table, not add a seventh status color.

## Is this a good idea?

**Yes for the tags. Yes for `repeat`, with a tight scope.** I would not take a different layer (new plugin, CSS snippet, storage rewrite). I would take a different *shape* than "an icon per tag."

### What is right in the request

- **The pills are ceremony, not content.** Bryan already knows these ten rows are the morning checklist: he is standing in `gtd_daily.md`, the footer says `PRE`, the `]s` notice says `PRE 2/8 · Brush teeth`. The tags exist so the evaluator can see them. Showing them as violet pills taxes the title for a fact the surrounding UI already states.
- **The membership rule is stable.** Exact whole-token `#gtd` plus `#pre`/`#post`, case-insensitive, `#gtd/pre` is not a member, PRE wins a conflict. That is locked in `docs/freshness.md` and both evaluators. A display layer that *mirrors* that rule cannot drift the walk.
- **There is already a working analog.** `#task #ref` → one book is the same problem (two tags, one kind) solved in the same plugin, with tests, a toggle, Live Preview widgets, reading-view in-place annotation, and CSS-only Tasks results. PRE/POST should be the next `kind` on that object, not a new invention.
- **`repeat` is the other half of the same line.** A PRE row that loses its tag pills but keeps `repeat | every day when done` still looks unfinished. Date marks already proved that Dataview suffix pills can become a glyph plus a short label without changing Tasks, Dataview, or bob-cli parsers.

### Where the request as written is underspecified

- **"Icons in place of `#gtd #pre` and `#gtd #post`" can mean two icons or one.** Two icons is the trap. Membership is the pair. Independent `#pre` / `#post` icons would also fire on a non-member, and a leftover `#gtd` pill would remain on every member. **ADJ-1.**
- **"Nice appropriate icons" does not pick a family.** Emoji 🌅/🌇, Lucide masks, small-caps chips, and GTD clipart would all satisfy the sentence. Only Lucide masks match the hash, the book, and the date silhouettes, survive PDF export, and stay on-model in light and dark. **ADJ-2.**
- **`repeat` is framed as optional.** In `gtd_daily.md` it is not optional if the goal is a beautiful line. It *is* optional as a recurrence *editor*, a grammar explorer, or a storage migration to `🔁`. Compact display only. **ADJ-3.**
- **Surfaces are unnamed.** The value is Live Preview of `gtd_daily.md` (where `]s` lands), then reading view and the archive, then Tasks results (already short-mode). Pickers, Mac Capture, `bob query`, and source mode are non-goals for v1, matching tag-marks.

### What I would not do

- Install Supercharged Links / Iconize / a tag-CSS snippet. Supercharged Links styles *note* links from frontmatter, not task-line tags in CodeMirror. A snippet targeting `a.tag[href="#pre"]` misses Live Preview hashtags, cannot reveal-on-cursor, and cannot express the AND. The family already rejected CSS-only `.cm-active` reveal because `j`/`k` shifts the title.
- Collapse `#task #gtd #pre` into one glyph that replaces the hash. A PRE row is still a tracked task. The book replaces the hash because a reading task *is* the identity. A checklist row is a tracked task *plus* a membership. Two facts, two marks. The hash stays.
- Rewrite tags to `#gtd/pre`. Nested tags are an explicit rejected alternative in `decisions:review-walk-is-tiered`. Dataview `tags include` would also start matching children.
- Convert 972 lines to `🔁 every day when done`. `taskFormat` is dataview; date-marks already rejected emoji storage ("rewrites thousands of vault fields plus the bob-cli parsers").
- Give PRE a warm gold and POST a cool indigo. Orange is ROTTEN/repair; blue is Ready. Shape carries the distinction; color does not.
- Hide `#gtd` globally. Twelve historical `#gtd` rows (home-context chores from May 2026, a cancelled inbox line) are not checklist members. Their pill is the honest signal.

## Requirement adjustments

Each adjustment is explicit.

**ADJ-1. One glyph per membership pair, never one glyph per tag.** A mark appears only when the line is a task line and the exact whole tokens `#gtd` and `#pre` (resp. `#post`) sit in one contiguous span: `#gtd`, one whitespace run, then the partner. `#pre` without `#gtd`, `#gtd/pre`, `#gtd #pressed_juice`, and non-adjacent `#gtd … #pre` stay as native pills. PRE wins over POST when both partners are present, matching the evaluator (0 such rows today).

**ADJ-2. Lucide-style CSS masks, not emoji.** Same 16×16 stroked language as the hash (`stroke-width` 1.8, round caps). Emoji 🌅/🌇 are muddy at 0.8em, differ by OS, and were already declined for the hash ("a filled tag silhouette turns into a blob").

**ADJ-3. Compact `repeat` in v1, as display-only suffix marks.** Do not wait for a second epic. Do not build a recurrence editor, a "when done" writer, or a storage migration. The mark is a cycle glyph plus a short label; the stored field is unchanged.

**ADJ-4. Keep the `#task` hash.** The identity column stays a hash (or a book, on reading tasks). The checklist glyph is *after* that column, *before* the title, in the slot the violet pills occupy today.

**ADJ-5. Muted ink, not a second teal.** Two full-teal glyphs in a row would read as a logo and compete with the hash. Checklist glyphs use a mix of `--text-muted` toward `--bob-task-tag-hue` (about 30% teal). Hover raises them to the hash teal. Closed rows rest with the same 40% mix toward `--text-faint` as the hash. Recurrence uses date-mark grey, because it is suffix metadata.

**ADJ-6. Reuse the two existing toggles.** No `toggle-checklist-marks` command. Checklist glyphs are kinds of task-tag-mark (`pre` / `post` next to `task` / `ref`). Recurrence follows `body.bob-date-marks`. Source mode, plugin-off, and toggle-off restore native pills.

**ADJ-7. Tasks query results stay CSS-only.** Same as `#task` (hidden) and `#ref` (book). `:has()` hides `#gtd` on a description that also has `#pre` or `#post`, and restyles the partner as the glyph. `hide tags` and re-renders keep working because no JS touches Tasks' DOM.

**ADJ-8. Pickers, Task Card headers, and Mac Capture are out of v1.** Reading-task pickers already strip `#task #ref` and prefix `📖`. Doing the same for PRE/POST is a later, small nav change. v1 is ledger-tools display.

**ADJ-9. "when done" lives in the tooltip, with a repair flag on checklist rows that lack it.** 98% of rules already include it. Putting it in the compact label wastes the space we are trying to recover. The existing lint `checklist_repeat_not_when_done` becomes visible: a checklist member whose rule lacks `when done` keeps the Dataview pill and the orange dashed repair border.

**ADJ-10. Do not change bob-cli parsers, capture, freshness membership, or the vault.** Tags and `[repeat::]` stay the source of truth. This is a bob-plugins display epic plus two bob-cli display contracts.

## Glyph design

### Candidates, judged on real rows

Imagined on `gtd_daily.md`, light and dark, next to the hash, a red Blocked tint (`[?]`), and the long Morning review title.

| Candidate | PRE | POST | Verdict |
| --- | --- | --- | --- |
| 1. Emoji 🌅 / 🌇 | noisy, OS-dependent, blob at 0.8em | same | Reject. Family already rejected filled blobs. |
| 2. Small-caps chips `PRE` / `POST` | instantly readable, matches footer | same | Strong for intuition, weak for beauty. The footer and `]s` notice already say the words. A chip is another pill. |
| 3. Play / stop (`▶` / `■`) | "start/end" | stop reads as media chrome | Reject. Fights the checkbox. |
| 4. Letter `P` in two weights | compact | PRE and POST share a letter | Reject. Indistinguishable at a glance. |
| 5. GTD inbox / flag | wrong: PRE is not inbox-only (stretches, pills, weather, agents) | flag fights 🔖 highlights | Reject. |
| 6. Sunrise / sunset, shared horizon | morning-open | ritual-close | **Recommended.** Matched pair, discriminable silhouettes, Lucide stroke, no stolen hue. |
| 7. Sun / moon | discriminable | moon says "night"; POST often still happens in the GTD pomodoro | Reject the moon. Sunset is "close of the opening", not bedtime. |

**Recommended: candidate 6.** Intuition comes from the surrounding walk chrome (footer `PRE`, notice `PRE 2/8`) plus a tooltip that uses those same words. Beauty comes from one quiet silhouette in the identity cluster. Reliability comes from copying the book pair byte-for-byte.

Weekly prune is also `#gtd #post`. It gets the sunset. That is correct: POST is the closeout *tier*, not the Morning review *title*. The title distinguishes the two POST rows.

### Geometry (copy into CSS masks)

ViewBox `0 0 16 16`, `fill none`, `stroke #000`, `stroke-width 1.8`, `stroke-linecap` / `stroke-linejoin` `round`. Tunable ±0.3 like the hash.

**PRE (sunrise)** — sun on a horizon, two short up-rays:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none"
     stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 12.2h10"/>
  <path d="M5.2 12.2a2.8 2.8 0 0 1 5.6 0"/>
  <path d="M8 4.2v1.5M4.6 6.2l1.1 1.1M11.4 6.2l-1.1 1.1"/>
</svg>
```

**POST (sunset)** — the same sun and horizon, no rays (the missing rays *are* the discriminator):

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="none"
     stroke="#000" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M3 12.2h10"/>
  <path d="M5.2 12.2a2.8 2.8 0 0 1 5.6 0"/>
</svg>
```

At 1.08em the rays are the only difference, and they sit in the upper half where the hash has empty space, so PRE reads "open/up" and POST reads "settled." They share the horizon, so they look like a pair and not two unrelated icons.

CSS custom properties, defined once on `body` next to `--bob-task-tag-glyph` and `--bob-ref-task-glyph`:

```css
--bob-pre-task-glyph: url("data:image/svg+xml,…PRE path…");
--bob-post-task-glyph: url("data:image/svg+xml,…POST path…");
--bob-checklist-tag-hue: color-mix(in srgb, var(--bob-task-tag-hue) 30%, var(--text-muted));
```

### Anatomy, tooltip, interaction

Host classes: `bob-task-tag-mark bob-pre-task-mark` / `bob-post-task-mark`. They ride the shared hash rules (size, padding, hover capsule, resting, toggle, teardown). Only `::before` `mask-image` and `--bob-task-tag-ink` change.

| Kind | Visible | `aria-label` | Tooltip (lines joined with `\n`, never `::`) |
| --- | --- | --- | --- |
| `pre` | sunrise mask | PRE checklist | `#gtd #pre · opening checklist` |
| `post` | sunset mask | POST closeout | `#gtd #post · closing checklist` |

Wording matches `docs/concepts/freshness-and-the-review-walk.md` ("Opening `#gtd #pre` checklist rows", "Closing `#gtd #post` checklist rows") so the glyph, the footer, and the docs say the same thing.

Interaction copies the book:

- Live Preview: `Decoration.replace` over the whole `#gtd #pre` / `#gtd #post` span, including the inner whitespace. No extra fold. Cursor or selection touching the span reveals both raw tags. Mousedown places the cursor at the span start. Widget equality is a constant key plus `kind`.
- Reading view: the `#gtd` anchor is the host (class + mask + tooltip). The adjacent partner anchor is hidden in place (`bob-pre-task-hidden` / `bob-post-task-hidden`), kept in the DOM for copy, Dataview `innerHTML`, and toggle restore. Native click on the host still searches `#gtd`.
- Closed rows rest. Plugin-off and toggle-off restore pills.

### After, on the same PRE row

```text
- [?] ⌗ ☀ Brush teeth   ↻ daily   + Oct 21   ⧗ tomorrow
        ^ sunrise          ^ recurrence mark (see below)
```

The title starts roughly eleven characters earlier. Morning review, whose body is a paragraph, is the row that benefits most.

## Recurrence marks

### Why "I'm not sure" should become yes

Open recurring work is only 14 lines, so it is tempting to skip. Skip it, and `gtd_daily.md` after the tag icons still ends every row with the same 30-character pill. That file is the morning stage. Dash already solved query results with `short mode`. Source Live Preview is the remaining hole, and date marks left it on purpose because `repeat` is not a date.

Scope that makes it beautiful:

- **Glyph:** Lucide `refresh-cw` simplified to two open arcs and one arrowhead, same 16×16 stroke language as the hourglass. Not the 🔁 emoji in source (query short-mode can keep using Tasks' emoji; we may restyle it to the mask in a follow-up).
- **Ink and metrics:** date-mark grey, 0.8em interface font, 1.08em glyph box, label at weight 550 `tabular-nums`. Quiet; closed rows rest.
- **Label grammar,** applied to the canonical Tasks rule string after stripping a trailing `when done` / `when scheduled`:

| Rule (after stripping when-clause) | Label |
| --- | --- |
| `every day` | `daily` |
| `every weekday` | `weekdays` |
| `every week` | `weekly` |
| `every week on Monday` (any weekday) | `weekly Mon` |
| `every month` | `monthly` |
| `every month on the 1st` | `monthly 1st` |
| `every year` | `yearly` |
| `every N days` | `Nd` (e.g. `30d`, `28d`) |
| anything else | glyph only (full rule on hover) |

Live vault coverage of that table: 953 `daily` + 4 `weekly Mon` + 2 `weekly Sun` + 5 `monthly 1st` + 4 `30d` + 4 `28d` = **972 / 972**. No "glyph only" row exists today.

- **Tooltip:** `Repeats every day when done` (the full rule, including the when-clause). Second line, checklist members only: nothing extra. Never contains `::`.
- **When-clause:** not in the label (**ADJ-9**). A checklist member whose rule lacks `when done` is *not* marked; the Dataview pill stays and the date-mark repair flag (dashed orange) lights it. That is the lint `checklist_repeat_not_when_done` made visible. Non-checklist recurring rows without `when done` (salary, jenika meds) still get a mark: their default is "when scheduled" and that is valid.
- **Eligibility:** canonical `[repeat:: …]` or `(repeat:: …)`, lowercase key touching `::`, exactly one occurrence, value a non-empty Tasks rule. Emoji `🔁` in source is already compact and is left alone (0 rows). Code positions excluded. Whitespace-run folding copies date marks.
- **Toggle:** `body.bob-date-marks`. The command notice can keep saying "Date marks on"; the section in the contract is titled "Recurrence marks (not a date)" so implementers do not shove ISO parsing onto the rule string.
- **Fragment split is mandatory.** `266-plugin-date-marks.js` is 985 lines against the 1000-line fragment cap. Recurrence gets new fragments (`136-recurrence-marks.js` core, `267` is already date-marks-tasks; put plugin code in a new `266b` / `268`-adjacent slot in `fragments.json` source order). Do not grow 266.

### Tasks results

Short mode (dash, rotten, crowded): already 🔁 only. Optional CSS restyle of `span.task-recurring` to the cycle mask, matching date-mark short mode. Not required for v1.

Full mode: a narrow frame pass like `scheduleTasksResultDateMarks`, or skip v1 because Bryan's daily queries are short mode. **Skip v1.** Revisit if a full-mode query starts showing long recurrence text next to the new source marks and the mismatch bothers.

## Architecture

### Checklist icons — extend task-tag-marks

Pure core `138-task-tag-marks.js` (811 lines; the `#ref` pair added ~200; PRE/POST is the same shape and may need a sibling fragment if 138 would cross 1000):

- `taskTagMarkRanges(line)` grows `kind: "pre" | "post"`.
- Prefilter today bails when `#task` is absent. Also scan for `#gtd` so a (hypothetical) task line with the pair but no `#task` still marks membership. The hash still requires `#task`.
- Pair helper mirrors `refTaskPairEnd`: from a `#gtd` token, one whitespace run, then `#pre` or `#post` (any case, whole-token boundary). `#gtd/pre` and `#pressed_juice` fail the boundary, as today.
- Ranges stay disjoint from the hash/book range. On `- [ ] #task #gtd #pre Brush` the result is `[{task, [6,11)}, {pre, [12,22)}]` (offsets illustrative).
- Reading-view annotation: `#gtd` host + hide adjacent partner, same as `#task` host + hide `#ref`.
- Tests in `scripts/test-ledger-tools-task-tag-marks.cjs`. Vector TT3 today expects `#gtd` untouched; **update TT3** to a line whose `#gtd` is *not* paired (`#task #gtd #context/home`, which still exists in the May archive) and add TT29+ for the pair.

Plugin `264-plugin-task-tag-marks.js`: same ViewPlugin, new widget class names, same refresh effect, same toggle. CSS in `styles.css` beside the book block.

Contract: a new section **"Checklist tags"** in `docs/task-tag-marks.md`, sibling of "Reference reading tasks". No new api namespace (tag-marks correctly refused one with no consumer).

### Recurrence — sibling of date-marks, not a kind of tag-mark

`repeat` is a suffix field, not a tag. Putting it in tag-marks would mix identity with metadata. Putting it in date-marks conceptually is slightly wrong (it is not a date) and physically impossible (266 is at the line cap). New contract section plus new fragments, gated by the date-marks body class.

Repair-flag CSS already keys on leftover Dataview pills for the four date fields. Extend the selector with `[data-dv-norm-key="repeat"]` so an unmarked `repeat` pill in Live Preview is either a mark failure or an invalid field. Canonical marked fields are hidden by the existing `:has()` hide pattern.

### What does not move

- Rust freshness membership, lints, schema.
- Capture grammar.
- Tasks `taskFormat`.
- Vault bytes.
- Footer labels (`PRE` / `POST` stay words; a status-bar icon would be a different, worse project).
- `#prj`, `#hide`, `#context/home`, and lone `#gtd`.

## Rejected alternatives

| Alternative | Why it loses |
| --- | --- |
| CSS snippet `a.tag[href="#pre"]::before { content: "🌅"; font-size: 0 }` | Misses Live Preview; no pair AND; cursor jitter; not the family. |
| Supercharged Links + Style Settings | Styles note links from frontmatter, not task tags; extra plugin; emoji prefixes. |
| Nested `#gtd/pre` | Rejected by the walk decision; breaks whole-token AND; Dataview parent matching. |
| Hide tags with Tasks `hide tags` on dash only | Dash is already short mode; the pain is `gtd_daily.md` source. |
| Tasks `removeGlobalFilter` analog for these tags | There is no such setting; even for `#task` the contract rejected it. |
| Independent icons for `#gtd`, `#pre`, `#post` | Lies on incomplete tags; leaves a pill; three marks where one fact exists. |
| Replace `#task #gtd #pre` with one glyph | Drops tracked-task identity; inconsistent with non-checklist rows. |
| Small-caps `PRE`/`POST` chips | Readable, but they are still pills, and the walk chrome already uses those words. Keep as the fallback if the silhouettes feel opaque after a week. |
| Convert storage to `🔁` | 972-line rewrite; fights `taskFormat: dataview`; date-marks already rejected emoji storage. |
| CSS-only restyle of the Dataview `repeat` pill | Cannot compact "every day when done" → `daily`; no tooltip grammar; no repair semantics. |
| A third toggle | Toggle fatigue. Two family switches already exist. |
| Recurrence editor / Task Card field | Display surfaces never act (date-marks rule). Ctrl+Shift+P already edits properties. |
| Color-coding PRE vs POST | Hue table is full. Shape only. |
| Footer / status-bar icons instead of in-line | The footer already names the tiers. The problem is the *task line*. |

## Conformance vectors

Today is `2026-10-21`. Offsets are UTF-16. `kind` additions are `"pre"` and `"post"`.

### Checklist pair (`taskTagMarkRanges`)

| # | Input | Expected |
| --- | --- | --- |
| TT3 (revised) | `- [?] #task #gtd #context/home Check weather` | `[{task, hash only}]`; `#gtd` untouched |
| TT29 | `- [ ] #task #gtd #pre Brush teeth` | `[{task}, {pre spanning #gtd #pre}]` |
| TT30 | `- [ ] #task #gtd #post Morning review` | `[{task}, {post spanning #gtd #post}]` |
| TT31 | `- [x] #task #gtd #pre Brush [completion:: 2026-10-20]` | same pair; resting is CSS |
| TT32 | `- [ ] #task #GTD #PRE Loud` | `pre` (case-insensitive partners, like `#ref`) |
| TT33 | `- [ ] #task #gtd   #pre Extra spaces` | `pre` spanning the extra whitespace |
| TT34 | `- [ ] #task #gtd/pre Nested` | `{task}` only |
| TT35 | `- [ ] #task #pre No gtd` | `{task}` only |
| TT36 | `- [ ] #task #gtd #pressed_juice X` | `{task}` only |
| TT37 | `- [ ] #task #gtd #pre #post Both` | `{task}` + `{pre}` (PRE wins; `#post` pill remains) |
| TT38 | `- [ ] #task #pre #gtd Reversed` | `{task}` only (order is `#gtd` then partner, matching the vault and `#task #ref`) |
| TT39 | `- [ ] #gtd #pre No hash` on a checkbox line | `{pre}` only if `freshnessTaskStatus !== null`; no hash |
| TT40 | ``- [ ] Note `the #gtd #pre pair` here`` | core may return a range; inline-code check drops it |
| TT41 | `- [ ] #task #gtd #pre A [priority:: high] [created:: 2026-10-21]` | pair disjoint from priority and date ranges |
| TT42 | `- [ ] #task #ref #gtd #pre Read then chore` | `{ref spanning #task #ref}` + `{pre}`; disjoint |

Rendered-view vectors TR10–TR13 have PRE/POST twins: host on `#gtd`, partner hidden in place; Tasks rows CSS-only; toggle strips and restores.

### Recurrence

| # | Input | Expected |
| --- | --- | --- |
| RM1 | `[repeat:: every day when done]` | glyph + `daily`; tooltip `Repeats every day when done` |
| RM2 | `[repeat:: every week on Monday when done]` | `weekly Mon` |
| RM3 | `[repeat:: every week on Sunday]` | `weekly Sun` (no when-clause in the rule; still marked; tooltip says the rule) |
| RM4 | `[repeat:: every month on the 1st]` | `monthly 1st` |
| RM5 | `[repeat:: every 30 days when done]` | `30d` |
| RM6 | `[repeat:: every 28 days]` | `28d` |
| RM7 | `- [ ] #task #gtd #pre Brush [repeat:: every day]` | **no mark**; leftover pill + repair flag (`checklist_repeat_not_when_done`) |
| RM8 | `(repeat:: every day when done)` | marked (paren form) |
| RM9 | `🔁 every day when done` | untouched (already compact) |
| RM10 | two `repeat` fields on one line | neither marked (occurrence gate, like dates) |
| RM11 | `` `[repeat:: every day when done]` `` | untouched (code) |
| RM12 | cursor inside the field | revealed, like date marks |

## Implementation plan

One epic, two phases, both display-only in bob-ledger-tools plus bob-cli contracts. Do not parallelize with a vault rewrite.

**Phase 1 — checklist glyphs (the request).**

1. Contract section in `docs/task-tag-marks.md` ("Checklist tags") with TT29–TT42 and the revised TT3.
2. Core pair helper + `kind` + reading-view host/hide + CSS masks and Tasks `:has()` rules.
3. Tests in `test-ledger-tools-task-tag-marks.cjs`.
4. `npm test`, `bob plugins sync`.
5. Live check on `gtd_daily.md` in light and dark, on a red `[?]` row and on the open Morning review `[ ]` row; toggle off/on; cursor reveal; vim `j`/`k` through the list; PDF export; iOS if convenient.

**Phase 2 — recurrence marks (same epic, immediately after).**

1. Contract section in `docs/date-marks.md` ("Recurrence marks (not a date)") with RM1–RM12.
2. New fragments (266 is full). Hide canonical `repeat` pills; repair-flag the leftovers; compact label grammar.
3. Tests next to the date-mark suite.
4. Live check: `gtd_daily.md`, `recur.md`, `cash.md`; the one PRE row whose rule *has* `when done` shows `↻ daily`; a synthetic checklist row without `when done` shows the orange pill.

**Later, not v1:** picker / Task Card prefix (strip `#gtd #pre` and show the sunrise, like `📖`); Tasks full-mode recurrence restyle; letterform fallback if the silhouettes fail the week-1 live check.

Line-budget note: if 138 would exceed 1000 lines, extract checklist pairing into a new fragment listed immediately after 138 in `fragments.json`. Do not hand-edit `main.js`.

## Open questions for Bryan

1. **Silhouette vs chip.** Recommended: sunrise / sunset. Fallback if they feel opaque after a few mornings: 0.8em small-caps `PRE` / `POST` in the same muted ink. The CSS variable makes that a one-line swap.
2. **Phase 2 in the same epic?** Recommended yes. Shipping icons alone leaves the 30-character `repeat` pill on every row the walk lands on.
3. **Reversed `#pre #gtd`.** Recommended: no mark (TT38), matching `#ref #task`. The vault always writes `#gtd` first. Say so if you would rather accept either order.

## Recommended solution

Ship **checklist tag marks** and **recurrence marks** as display-only members of the existing bob-ledger-tools family.

**On a PRE row in Live Preview:**

```text
before: - [?] ⌗  #gtd  #pre  Brush teeth   repeat | every day when done   + Oct 21  ⧗ tomorrow
after:  - [?] ⌗ ☀ Brush teeth   ↻ daily   + Oct 21  ⧗ tomorrow
```

**On POST (Morning review or Weekly prune):** the same, with the sunset silhouette.

**Rules that make it reliable:**

- Stored form never changes: `#gtd #pre`, `#gtd #post`, `[repeat:: every day when done]`.
- A checklist glyph appears only for a contiguous, whole-token `#gtd` + `#pre`/`#post` pair on a task line. Lone `#gtd`, nested `#gtd/pre`, and incomplete tags stay pills.
- The `#task` hash (or the reading-task book) stays. Membership is a second mark, not a replacement identity.
- Recurrence becomes `↻` plus a compact label (`daily`, `weekly Mon`, `monthly 1st`, `30d`, …). The full rule, including `when done`, is the tooltip. A checklist row missing `when done` is *not* marked and is repair-flagged.
- Cursor or click reveals the source. Two existing toggles restore pills. Source mode is always raw. Without the plugin the vault is unchanged.
- Tasks results: CSS-only, `:has()` pair hide, no JS on Tasks' DOM.
- Ink: muted-teal for checklist silhouettes (hover to identity teal); date-mark grey for recurrence. No new hue. Closed rows rest.
- Contracts live next to their analogs (`docs/task-tag-marks.md`, `docs/date-marks.md`). Tests run the vectors verbatim.

This is the smallest design that is:

- **intuitive** — the walk already says PRE and POST; the line now shows a matched morning/evening silhouette in the slot those tags occupy, and `↻ daily` in the slot the Dataview pill occupies;
- **reliable** — display-only, pair-not-tag, exact-or-native, the same reveal/toggle/Tasks-CSS machinery the hash and the book already ship;
- **beautiful** — two quiet Lucide silhouettes and one grey cycle, no extra pills, no extra colors, on the ten rows Bryan sees every morning.

## About this report

Independent `grk` report, 2026-10-21. Nothing was implemented or deployed. I did not read other researchers' reports from this swarm.

**Sources.**

- bob-cli: `docs/task-tag-marks.md` (hash, book pair, hue table, TT/TR vectors, rejected alternatives); `docs/date-marks.md` (suffix-field family, repair flag, Tasks short/full mode, rejected emoji storage); `docs/freshness.md` (checklist membership, `checklist_repeat_not_when_done`); `docs/concepts/freshness-and-the-review-walk.md` (opening/closing wording).
- bob-plugins `bob-ledger-tools`: `src/138-task-tag-marks.js`, `src/264-plugin-task-tag-marks.js`, `src/136-date-marks.js`, `src/266-plugin-date-marks.js` (985/1000 lines), `src/120-freshness-footer.js` (PRE/POST labels), `styles.css` (hash, book, date-mark hide/repair).
- bob-plugins nav: `src/010-requires-and-config.js` (`REF_AFTER_TASK_RE`, `📖` picker prefix) as the later analog for picker stripping.
- Live vault, 2026-10-21: `bob query --format json --tasks 'tags include #gtd'` (148); `'is recurring'` (972, all `[repeat::]`, 953 `every day when done`, 14 open); open checklist census in `gtd_daily.md` (8 PRE, 2 POST, adjacent `#gtd`-first order); Tasks `data.json` (`taskFormat: dataview`, `short mode` on dash/rotten/crowded).
- Memory: `decisions:review-walk-is-tiered` (exact tokens, no nested tags, do not drop `repeat`); `glossary` Morning GTD Review Footer, Task Freshness; prior research `research:202610/gtd_pre_post_checklist_tiers/gtd_pre_post_checklist_tiers.md` (membership and vault layout) and `research:202610/today_task_line_marks/today_task_line_marks.md` (display-only mark-family precedent).
- External: Obsidian Tasks layout (`hide recurrence rule`, `short mode`, `span.task-recurring`); Tasks Dataview format for `[repeat::]`; Supercharged Links (note-link styling, not task tags).

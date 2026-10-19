# Ledger Today marks on task lines

- **Researcher:** grk
- **Date:** 2026-10-19
- **Question:** When viewing a task in Obsidian (its area or project note, not the daily file), should Bob render a marker that the task is in today's daily file? How should that feel, stay reliable, and look, given we already mark In Progress and unblocked-today on Task Links?
- **Verdict:** Yes, with a tightened membership rule. Render a display-only **Ledger Today mark** on the task's own checkbox line when that task is in `isToday` — a dedicated Task Link under today's **open** Pomodoros. Do not write a tag or field. Do not treat "lives in the daily file" or "is mentioned somewhere in it" as membership. Reuse the existing Today cache. Make the mark a compact small-caps `TODAY` pill that can jump to the ledger link.

---

## 1. In one breath

The gap is real, and sticky lanes created it. A Next `[*]` or In Progress `[/]` checkbox no longer means "this is on today's plan." Those lanes survive unlink. The only honest answer to "is this task in today's ledger?" is the same read-time set dash, `bob plan`, freshness, and the reading-board `TODAY` pill already use.

The existing In Progress half-ring and unblocked 🔓 are the **forward** decoration: they sit on Task Links in the daily file and tell you something about the *target*. This feature is the **inverse**: it sits on the task line in the note that owns the checkbox and tells you the task is linked under today's open Pomodoros.

That is a good idea. The raw request ("in today's daily file") is slightly the wrong set. Closed 🍅 history, journal mentions, and the daily file's own `^gtd` row are not Today. Writing `#today` is the alternative `decisions:today-is-read-from-the-ledger` already rejected. The work is to paint `isToday` onto residence task lines with the same house style as date, priority, freshness, tag, and progress marks.

---

## 2. Is this a good idea?

**Yes.** Three properties make it the right layer:

1. **The checkbox stopped answering the question.** `decisions:task-lanes-are-sticky` is explicit: removing a Task Link never lowers Next or Pending; only Alt+N release does. `[/]` "no longer means worked recently." Standing in `### Next & In Progress` on an area note, Bryan cannot tell which of those rows are in today's open Pomodoros and which are last week's leftover Next. Dash's TODAY section answers this only when he is on `dash.md`. The reading board already solved the same gap for reference cards with a `TODAY` pill (`docs/ref.md`: "A `TODAY` pill appears only when the reading task is linked under today's Pomodoros and the Today cache is ready"). Ordinary tasks have no equivalent.

2. **The fact is already computed.** bob-ledger-tools keeps a synchronous Today cache (`{ date, dailyPath, keys, rank }`) rebuilt from today's daily note. `api.isToday(task)` / `isTodayTask` / `todayKeys` / `todayRank` are the public contract (api v3). Freshness, READY, dashboard PENDING/NEXT exclusion, and the reading-board pill all call it. A new mark that re-parsed the daily file would be a third Today. A mark that *reads the cache* is a new view of a fact Bob already trusts.

3. **The analog is proven.** `plan:202610/in_progress_task_link_marks.md` (bob-cli-56) established the house rules for this family: rendered, never written; truthful or neutral; shape carries meaning; session toggle; Live Preview widget plus Reading post-processor; listener-free DOM so Dataview's `innerHTML` pass cannot strip handlers; optimistic hints for same-frame flips. The unblocked glyph (`plan:202610/successor_links.md`, phase `ledger_glyph`) copied that skeleton onto a second link-side fact. This feature copies it onto the *task* side.

What would make it a bad idea:

- writing `#today` or `[today::]` on the task line (the 15-minute churn, races, and parser breakage the 2026-09-30 decision retired);
- treating "appears anywhere in `YYYY/YYYYMMDD.md`" as membership (residence `^gtd`, journal wikilinks, Depends-On lines pasted into the daily file, closed 🍅 history);
- adding a `### Today` group under area/project `## Tasks` (those notes already group by lane: Next & In Progress / Blocked / Done & Canceled; Today is orthogonal to lane);
- painting a third "today" that collides with freshness tone `today` (confirmed today) and date-mark label `today` (scheduled/created/done on today's calendar date);
- shouting a full pill on dash's TODAY query, where every row is already Today.

The design below closes those.

---

## 3. Critique of the plan as stated

The plan: *"Render some kind of marker on tasks that are in today's daily file when I view those tasks in Obsidian. We already do something similar for task links (in-progress and unblocked today)."*

### What is right

- **Inverse decoration is the right instinct.** Progress marks and the unblocked glyph live on the *link*. Bryan's question when he opens `sase.md` or a project note is about the *task*. Same family, opposite arrow.
- **Look at the existing marks first.** That is how date marks, priority marks, tag marks, and progress marks were designed: one display contract, one CSS mask or host, Live Preview plus Reading, never a stored second copy.
- **Beauty is in scope.** The progress-mark plan spent a page on Linear-style half-ring geometry, ink stack, 160 ms entrance, and `prefers-reduced-motion`. A new mark that ignores that bar will look like a stray emoji.

### What is loose

- **"In today's daily file" is not a Bob concept.** The daily file holds the `^gtd` row (residence), PRE/POST checklists, closed Pomodoros with 🍅 history, open Pomodoros with live Task Links, journal prose, and a `bob-plan` block. Only dedicated Task Links under **open** Pomodoros are Today (`docs/plan.md` § Today; `decisions:today-is-read-from-the-ledger`). Closed 🍅 lines are history. A path filter on the daily note "measures residence, not work" — that is the rejected alternative in the decision, and it returned 1 result against 7 live links.
- **The analog is on links, not on tasks.** Progress marks fire only when the open file *is* today's daily note. This feature fires when the open file is the task's home. Copying the progress-mark file-date gate would paint nothing in area notes, which is the whole request.
- **No membership, surface, or glyph is specified.** Without those, an implementer will either write a tag (forbidden) or invent a second Today parser (divergent).

### What I would not do

- I would not add a Next mark on Task Links. Progress-marks D2 is explicit: "Next has no mark… quiet by default." The ambiguity is on the task line, where sticky Next and ledger Next share a checkbox.
- I would not move Today tasks into their own heading in area notes. `docs/task-status-hooks.md` owns `### Next & In Progress` by title and shape. A Today group would split a sticky-Next row from an in-ledger-Next row that share a lane, and it would write headings — the opposite of a display-only mark.
- I would not ship a CSS-only `li::before`. Today is not a property of the line. Membership lives in another file. CSS cannot see it.

---

## 4. Requirement adjustments

These change the request. Each is justified.

1. **Membership is ledger Today, not "in the daily file."** A task gets the mark iff `isToday(task)` is true: it resolves from a dedicated Task Link (plain or embedded `[[note#^id]]`, 🍅 prefix allowed, trailing `#` move-only excluded — that last one is Today’s rule, not the progress-mark exception) under an **open** Pomodoro in today's daily note, it is an open `#task`, and the Today cache is ready. Closed 🍅 history, journal mentions, Depends-On lines, and daily-file residence (`^gtd`) do not qualify.
   - *Why.* This is the only set Bob already names, tests, and exposes. A broader set would disagree with dash TODAY, `bob plan`, freshness walk exclusion, and the reading-board pill.
2. **The mark is rendered and never written.** No `#today`, no `[today::]`, no prefix character on the task line or the ledger link.
   - *Why.* `decisions:today-is-read-from-the-ledger` rejected the tag. Progress-marks D1 rejected a written `◐ ` because every dedicated-link parser would drop it. The same parsers would also choke on a written mark on the *task* if it were ever copied into a link bullet.
3. **Primary surface is the residence task line** in Live Preview and Reading view of area, project, and reference notes. Not the daily-file Task Link (progress marks and the unblocked glyph already own that slot). Not dash TODAY query rows (every row is Today; a mark on each is noise).
4. **The mark is also a jump.** Click (mousedown) opens today's daily note and scrolls to that task's ledger line. Tooltip names the Pomodoro.
   - *Why.* Progress marks do not jump because they already sit on the ledger. The inverse mark's unique job is "take me to where this is planned." Without the jump it is only a badge.
5. **Quiet when the cache is not ready.** No mark, never a guess. Same sentence as the reading board: "Today never guesses: without a ready cache no card gets a TODAY pill."
6. **History-today (closed 🍅 under today's daily note) is out of v1.** It is a real question ("did I already touch this today?") and a possible v2 quieter state. Mixing it into v1 would make the mark disagree with `isToday`.
7. **Tasks query results are out of v1.** Date marks needed a dedicated Tasks-DOM pass because Tasks serializes dates as emoji spans. Today membership needs a block id plus path. Dash TODAY already lists the set. Area-note Live Preview is the gap.

---

## 5. What already exists

### Forward marks (on Task Links, in the daily file)

| Mark | Fact | Where | Glyph | Plan |
| --- | --- | --- | --- | --- |
| In Progress | target checkbox is `/` | dedicated Task Link under today's **open** Pomodoro | amber half-filled ring, before the link | `plan:202610/in_progress_task_link_marks.md`, `docs/plan.md` § In Progress marks |
| Unblocked today | a prerequisite completed today | same link slot, after the link | faint 🔓 | `plan:202610/successor_links.md` phase `ledger_glyph` |
| 🍅 | worked in a past (usually closed) session | written text on the link | tomato emoji, stored | ledger grammar |

Progress marks are file-gated: the open file must be today's daily note. Next targets show nothing. Embedded `![[…]]` is excluded because the transclusion already shows its own amber checkbox.

### Inverse / sibling marks (on task lines, in residence notes)

| Mark | Fact | Host | Notes |
| --- | --- | --- | --- |
| `#task` hash | tracked task | replaces `#task` | teal identity; 3,400 lines; quiet because it repeats |
| Priority bars | `[priority::]` | replaces the field | grey staircase |
| Date marks | created / scheduled / completion / cancelled | replaces the field | grey icon + `today`/`Tue`/… label. **`today` here means the calendar date, not the ledger.** |
| Freshness | `[fresh::]` | replaces the field | green `today` tone means *confirmed today* |
| Reading-board `TODAY` pill | `isToday` | card, not a task line | small-caps word, Next-green capsule, tooltip "Linked under today's Pomodoros" |
| Dash / `bob-plan` TODAY chip | link/theme budget | navigation | count-to-limit Work colors; not a per-task mark |

### The Today engine (reuse, do not fork)

- Rust `today_tasks` / JS `computeTodayLinks` + `resolveTodayKeys` (`060-today.js`), conformance in `docs/plan.md`.
- Cache rebuild in `rebuildTodayCache` (`290-plugin-today-and-location.js`): on daily-file change, day rollover, and first paint. Key is `"<vault path with .md>#<block id>"`. Changing keys fires `TODAY_RELOAD_EVENT` (Tasks query reload) and already refreshes plan blocks, freshness, and the reading board.
- `isTodayTask` / `todayRankOfTask` / `todayKeys()` on the plugin; frozen on `api` v3 as `isToday`, `todayRank`, `todayKeys`.
- Freshness walk **excludes** Today-linked tasks (`docs/freshness.md`: `¬Today(t)`). The mark will not appear on `]s` landings. It appears when Bryan is in the note, in Next & In Progress, or jumping with Ctrl+Shift+J/K.

### Why the checkbox is not enough

From `decisions:task-lanes-are-sticky`:

> Removing a link **never** changes the lane.

So this is a legal, common state:

```text
- [*] #task Review the RFC     ← Next, not in today's ledger
- [*] #task Ship the importer  ← Next, linked under the running Pomodoro
- [/] #task Fix the parser     ← In Progress, linked
- [/] #task Old WIP            ← In Progress, unlinked yesterday, still sticky
```

Four rows, two facts, one checkbox language. That is the screenshot this feature exists to fix.

---

## 6. Membership

### v1 (ship this)

A residence task line is marked when **all** of these hold:

1. Today cache is ready for the current local date (`isTodayCacheReady`).
2. The line is a task line (`freshnessTaskStatus(line) !== null`) with a standalone `^blockId` matching `PLAN_BLOCK_ID_RE`.
3. The open file's path plus that block id forms a Today key that `todayCache.rank` holds.
4. The task is open (Ready, Next, In Progress, or Blocked). Done and cancelled drop out, matching `docs/plan.md` Today rule 5.

In practice Blocked should not appear: "Blocked tasks keep no Task Links under today's open Pomodoros." If reconcile has not run yet, the mark still follows the ledger (truthful), and the next hooks pass removes the link and the mark.

Ready should be rare: linking raises Ready to Next. A Ready+Today row is a brief lag; still mark it.

### Explicit non-members

| Case | Why not |
| --- | --- |
| Task *resides* in today's daily file (`^gtd`) | Path filter; rejected in the Today decision |
| Wikilink in journal prose | Not a dedicated Task Link |
| Task Link under a **closed** Pomodoro (🍅) | History; Today is open entries only |
| Trailing `#` move-only link | Today excludes it (`todayLinkFromBody`); progress marks include it for a different reason |
| Struck `~~[[…]]~~` | Not a live link |
| Deeper nested bullets, mixed-text bullets | Not dedicated |
| Unresolved / ambiguous basename | Today skips them; JS/Rust divergence is documented; show nothing |
| Yesterday's daily note | Cache is keyed on today |
| Headless `bob query` | Already sees empty Today; no plugin, no mark |

### v2 (do not mix into v1)

**History-today:** dedicated Task Link under a *closed* Pomodoro in today's daily note, and not in the open set. Quieter twin of the live mark. Tooltip `Worked today under 🍅 NAME`. Live Today wins if both. This is the only charitable reading of "in today's daily file" that is still a Task Link. Ship it only after v1 has been lived with, because it answers a different question (touch vs plan).

---

## 7. Visual design

### Principles (stolen from the marks that already work)

From `docs/date-marks.md` and `docs/task-tag-marks.md`, restated for a *sparse* mark:

- **Display-only.** Source text unchanged. Source mode shows the raw line. Session toggle restores the previous look. Without the plugin the vault looks as it does today.
- **Truthful or neutral.** Ready cache and a matching key, or nothing.
- **Shape carries meaning.** The word `TODAY` in small-caps is the shape. Color is a whisper.
- **Quiet by default.** Tag marks are quiet because they repeat 3,400 times. This mark is sparse (plan link budget, default 10), so it may use a small capsule. It still must not scream.
- **Do not spend a lane hue.** Task-tag-marks already assigned the rainbow: red Blocked, orange attention/ROTTEN/Pending chip, yellow In Progress, green Next / freshness-today, blue Ready, violet tags, teal `#task`, grey priority and dates, magenta "exactly at cap" on Work chips. A Next-green `TODAY` pill (reading board's choice) **vanishes into the Next line tint**, which is exactly the surface this mark must work on.
- **Do not say a bare "today."** Freshness tone `today` = confirmed today. Date-mark label `today` = that field's calendar date is today (`⧗ today` already appears on the same line). The tooltip must say **Linked under today's Pomodoros**.

### Recommended host

A compact small-caps **word pill**, not a new SVG glyph and not an emoji.

```text
before:
- [*] ⌗ Ship the importer  ▮▮▮  + Sep 29  ⟳ 3d
- [*] ⌗ Review the RFC     ▮▮   + Oct 8
- [/] ⌗ Fix the parser     ▮▮▮  + Oct 1

after:
- [*] TODAY ⌗ Ship the importer  ▮▮▮  + Sep 29  ⟳ 3d
- [*] ⌗ Review the RFC           ▮▮   + Oct 8
- [/] TODAY ⌗ Fix the parser     ▮▮▮  + Oct 1
```

(`TODAY` here is the pill; `⌗` is the existing teal `#task` hash.)

Why the word, not a sun / pin / calendar:

- Dash chips, the reading-board pill, and `bob-plan` already trained the word `TODAY` as ledger membership. A sun would be a third calendar metaphor next to the date-mark hourglass.
- Sparse enough (≤10) that a 4–5 character label is not the `#task` noise problem.
- Works in forced-colors and print without a mask asset. (Progress marks *need* a mask because a half-ring cannot be Unicode reliably; `TODAY` can.)
- The unblocked glyph used 🔓 specifically to avoid a new asset; this mark can be more typographic because it is a named lane in the product, not a one-off status.

Why not the reading-board Next-green fill: it disappears on `[*]` rows. Why not In Progress yellow: that is the half-ring's ink. Why not Work-badge count colors: those encode *how full* Today is, not *whether this row* is in it.

### Ink and metrics

Family metrics match `.bob-fresh-mark` / `.bob-date-mark` / `.bob-reading-board-today` so the line stays one instrument:

```css
.bob-today-mark {
  display: inline-flex;
  align-items: center;
  margin-inline-end: 0.35em;
  padding: 0 0.42em;
  border: 1px solid color-mix(in srgb, var(--text-muted) 34%, transparent);
  border-radius: 999px;
  background-color: color-mix(in srgb, var(--text-muted) 10%, transparent);
  color: var(--text-muted);
  font-family: var(--font-interface);
  font-size: 0.72em;
  font-variant-caps: all-small-caps;
  font-weight: 650;
  letter-spacing: 0.045em;
  line-height: 1.35;
  vertical-align: 0.12em;
  opacity: 0.92;
  user-select: none;
  cursor: pointer; /* jump affordance */
}
.bob-today-mark:hover {
  opacity: 1;
  color: var(--text-normal);
  background-color: color-mix(in srgb, var(--text-muted) 16%, transparent);
}
body:not(.bob-today-marks) .bob-today-mark { display: none; }
```

No new hue. Contrast comes from small-caps, tracking, and the capsule. On a green Next tint or a yellow In Progress tint the grey capsule still reads as "not the checkbox." Hover warms to `--text-normal`. `cursor: pointer` is the one departure from progress marks (`cursor: default`), because this mark jumps.

Optional 160 ms scale-in, killed by `prefers-reduced-motion`, copied from `.bob-progress-mark`.

### Placement

**Immediately after the checkbox, before `#task` / the description.**

That is the glance slot when scanning `### Next & In Progress`. It is *not* the suffix cluster (priority, dates, freshness), which already means "properties of this task." Today is not a property of the task; it is a fact about the ledger. Putting it with the checkbox says "this row is on the plan," which is the sentence Bryan is reading.

Implementation: a CM6 widget at `side: -1` on the first content character after `[s] ` (reuse `dateMarkContentStart` / `freshnessAfterListMarker`). It covers **no source text**, so it stays visible with the cursor on the line — the progress-mark rebuild rule (`never on selectionSet`).

Reading view: prepend the same `span.bob-today-mark` into the `li` that owns the checkbox, after the task marker, before `.task-description` / the first text node. Skip `li.plugin-tasks-list-item` in v1.

### Tooltip and accessibility

Two lines, joined with `\n`, **never containing `::`** (Dataview re-scans `innerHTML`):

```text
Linked under today's Pomodoros
BOB · click to open
```

If the Pomodoro is unnamed: `today's plan · click to open`. Several open entries holding the same task: name the first in ledger order, then `+N more` (unblocked-glyph tooltip grammar).

`role="img"`, `aria-label` = tooltip, `data-tooltip-position="top"`, `data-block-id`, `data-ledger-line`.

### Interaction

- **Hover:** native Obsidian tooltip (same attributes as progress marks).
- **Mousedown:** `preventDefault`, then `workspace.openLinkText` to today's daily path with a subpath / line from the cache. Best-effort; the mark still renders if navigation fails.
- **The mark never writes.**
- **Toggle command:** `Toggle Ledger Today marks` (default on), flips `body.bob-today-marks`, dispatches the refresh effect. Session-only, like the others.

### Crowding

A marked line already carries: checkbox tint, teal hash, description, priority bars, date marks, freshness. Adding a 4-letter pill after the checkbox is the least-bad extra, because:

- at most ~10 such pills vault-wide (link cap);
- it sits in a slot those other marks do not use;
- hiding `#task` behind the hash already bought the space this would have competed with.

If a line still feels busy, the v2 move is to drop the capsule (keep the letters) rather than invent a 12-px sun.

---

## 8. Alternatives considered

| Option | Verdict |
| --- | --- |
| Write `#today` / `[today::]` | Rejected by `decisions:today-is-read-from-the-ledger`. Churn, races, stale between 15-minute hooks. |
| Path filter on the daily file | Rejected in the same decision. Measures residence (`^gtd`), not work. |
| Mark every wikilink mention in the daily file | Journal noise. Not the `=x` lineup. Diverges from dash TODAY. |
| Include closed 🍅 history in v1 | Different question (touch vs plan). Quiet v2 twin, not a mixed v1. |
| `### Today` group in area notes | Writes headings; splits a lane group Bob already owns by title. Today is orthogonal to Next/Pending. |
| Line tint / left gutter bar | Lane tints already own the row color. A gutter bar fights fold markers and is easy to miss next to the checkbox. |
| SVG sun / pin / calendar | New vocabulary beside date-mark hourglass and freshness ⟳. Word `TODAY` is already trained. |
| Reading-board Next-green pill copied 1:1 | Invisible on `[*]` rows, the main surface. |
| Half-ring on the task line | That glyph already means In Progress on the *link*. Reusing it for Today would lie. |
| Mark Next Task Links in the daily file | Progress-marks D2: Next is quiet there on purpose. |
| CSS-only `li.bob-today-task::before` | Cannot see the other file. Still needs JS to set the class; once JS is in, a real widget gives tooltip + jump. |
| Tasks query results in v1 | Dash TODAY is 100% members (noise). PENDING/NEXT sections *exclude* Today. Area-note LP is the gap. |
| Mac Capture agenda | Already *is* the ledger (`decisions:idle-capture-shows-ledger-agenda`). No mark needed. |
| Rust / capture / reconcile changes | None. Display-only, like progress marks. |

---

## 9. Recommended solution

**Name.** Ledger Today marks. CSS `bob-today-mark`. Command "Toggle Ledger Today marks." API `api.todayMarks` v1. Contract `docs/today-marks.md`, in the style of `docs/date-marks.md`. One paragraph in `docs/plan.md` after "In Progress marks and the Task Link lane toggle."

**Owner.** bob-ledger-tools only. Same split as progress marks: a pure core fragment, a Live Preview mixin, a Reading mixin, CSS, a session toggle, tests that run the contract vectors verbatim.

**Fact source.** The existing Today cache. Enrich it (additive) so each key also carries `ledgerLine` (1-based) and `entryName` (or null) from `computeTodayLinks`. Today membership, rank, and dash behavior stay byte-identical; the extra fields exist for tooltip and jump. Do not parse the daily file a second time inside the mark builder.

**Core (pure, never throws).**

- `todayMarkKeyFromLine(path, line) → "path.md#id" | null`
- `todayMarkModel(cache, path, line) → { blockId, entryName, ledgerLine } | null`
- `todayMarkTooltip(model) → string`
- `buildTodayMarkElement(doc, model) → span | null`
- `TodayMarkWidget` (CM6): `eq` on `blockId + ledgerLine + entryName`; `toDOM` builds the listener-free span and adds mousedown-to-jump only.

**Live Preview.** Viewport widgets on task lines whose key is in `todayCache.rank`. Rebuild on `docChanged`, `viewportChanged`, live-preview toggle, day rollover, and a lazy `StateEffect` fired from `rebuildTodayCache` (the cache already knows when keys change). Never on `selectionSet`. Skip when the open file *is* today's daily note **unless** the line is a real task line (so `^gtd` can mark if it is actually linked; Task Link bullets never match `todayMarkKeyFromLine`).

**Reading view.** Post-processor at the same priority as the other marks (50). Resolve the section's source path; for each `li` with a checkbox and a visible/hidden block id, build the span. Skip Tasks query rows (`plugin-tasks-list-item`) in v1.

**Instant feedback.** When a supported gesture writes a live Task Link (Ctrl+Shift+Enter, capture, cycler close), `rebuildTodayCache` already runs from the daily-file change. If same-frame lag is visible, add `todayMarks.expect(key)` mirroring `progressMarks.expect` — a short-lived hint that the next cache build confirms or drops. Do not invent a second membership.

**Jump.** `openLinkText(dailyPath, sourcePath)` then scroll to `ledgerLine`. If the daily note is already open in a split, focus that leaf. Failure is silent besides the missing scroll; the pill stays.

**Tests.** `scripts/test-ledger-tools-today-marks.cjs`, vectors below, plus toggle, body class, widget `eq`, cache-not-ready, rollover, and "Next sticky / not in cache ⇒ no mark."

**No bob-cli Rust, no capture grammar, no Mac app, no new CLI command.** `cli_rules.md` is untouched.

---

## 10. Implementation sketch

Work in the `bob-plugins` linked repo, `plugins/bob-ledger-tools/`. Mirror progress-marks file layout so the 1000-line fragment budget stays honest:

| Fragment | Job |
| --- | --- |
| `139b-today-marks.js` (pure core) | key, model, tooltip, element, widget |
| `275-plugin-today-marks.js` | setup, extension, toggle, `expect`, jump |
| `276-plugin-today-marks-reading.js` | post-processor |
| `060-today.js` / `290-plugin-today-and-location.js` | additive cache fields only |
| `styles.css` | `.bob-today-mark` block after the unblocked glyph |
| `350-exports.js` / `170-plugin-lifecycle.js` | `api.todayMarks` v1, `body.bob-today-marks` |
| `docs/today-marks.md` in **bob-cli** | display contract + vectors |

`rebuildTodayCache` already notifies freshness, plan blocks, and the reading board. Add `scheduleTodayMarksRefresh()` next to `scheduleFreshnessMarksRefresh()`.

Suggested phases (one epic, three beads):

1. **contract-core** — `docs/today-marks.md`, pure helpers, cache field enrichment, unit tests for membership (including every non-member in §6).
2. **render** — LP widget, Reading post-processor, CSS, toggle, `api.todayMarks` v1, harness tests.
3. **jump-hints-docs** — click-to-open, `expect`, `docs/plan.md` paragraph, README row, `bob plugins sync`.

Live verification (Bryan, in Obsidian), copied in spirit from progress-marks:

- Light and dark: the pill reads on Next green and In Progress yellow tints; the word, not the color, carries the meaning.
- The mark stays visible with the cursor on its line.
- Link a Ready task into the running Pomodoro in a split: the pill appears on the task note the same frame the link lands.
- Unlink: the pill goes; the `[*]` stays (sticky).
- Midnight: yesterday's pills vanish without a reload.
- Click: today's daily note opens on that Task Link.
- Toggle off: pills gone; source unchanged.
- Reading view matches Live Preview.
- Cache not ready (plugin just loaded, daily note missing): no pills, no flash of wrong marks.

---

## 11. Risks, costs, non-goals

**Risks**

- **Three "todays" on one line.** A scheduled-today task that is also ledger-Today can read `TODAY … ⧗ today`. The tooltip and small-caps word vs the date-mark's lowercase `today` are the disambiguation. If that still bites in real use, v1.1 can restyle the date-mark label for Δ=0 to `this date` / `Oct 19` when a ledger mark is present. Do not rename ledger Today.
- **Ambiguous basenames.** JS Today uses `getFirstLinkpathDest`; Rust uses unique case-insensitive basename. Documented divergence. The mark follows JS, because it lives in the plugin. Never invent a third resolver.
- **Dataview innerHTML.** Listener-free span plus a single mousedown on `toDOM`, same as progress marks.
- **Stale cache.** Already a Today-engine cost. The mark inherits it. `expect` covers the gesture path; the 15-minute hooks are irrelevant because nothing is written.
- **Click vs cursor placement.** Progress marks place the cursor. This mark navigates. If both widgets ever sat on the same node they would fight; they cannot: one is daily-file links, the other is residence tasks.

**Costs**

- One more CM6 `Prec.highest` plugin and one more post-processor in a file that already has many. Keep the builder O(viewport task lines × O(1) cache lookup), never a daily-file parse per editor frame.
- A fourth session toggle. Acceptable; every mark has one. Default on.
- Two-implementation Today remains: the mark does not make that worse.

**Non-goals**

- Writing anything to the vault.
- A Today group, badge-row chip, or ready-cap interaction.
- Marking dash TODAY / PENDING / NEXT query results.
- Marking Mac Capture, `bob plan` CLI, or tmux.
- History-today, sun glyphs, gutter bars.
- Changing progress marks, the unblocked glyph, or Next-has-no-mark on links.
- Freshness, walk tiers, or sticky-lane rules.

---

## 12. Proposed conformance vectors

`T` is an area note `proj.md` holding the listed line. `D` is today's daily file. Cache is ready unless stated. Expected mark is on `T`, never on `D`'s link bullet.

| ID | Setup | Mark? |
| --- | --- | --- |
| M1 | `D` open Pomodoro has `- [[proj#^a]]`; `T` is `- [*] #task A ^a` | yes |
| M2 | same, `T` is `- [/] #task A ^a` | yes |
| M3 | `T` is `- [*] #task A ^a` but no link in `D` | no (sticky Next) |
| M4 | `T` is `- [/] #task A ^a` but no link in `D` | no (sticky Pending) |
| M5 | link sits under a **closed** `[x]` Pomodoro as `🍅 [[proj#^a]]` | no (v1); v2 history only |
| M6 | link is move-only `[[proj#^a]] #` under an open entry | no (Today excludes `#`) |
| M7 | struck `~~[[proj#^a]]~~` | no |
| M8 | mixed-text `- see [[proj#^a]] later` | no |
| M9 | embedded `![[proj#^a]]` under an open entry | yes (Today includes embeds; progress marks do not, different reason) |
| M10 | `T` is `- [x] #task A ^a` | no (done drops out of Today) |
| M11 | `T` is `- [?] #task A ^a` and a live link remains | yes until reconcile removes the link |
| M12 | `T` is `- [ ] #task A ^a` and a live link remains | yes (Ready lag) |
| M13 | `^gtd` in `D` itself, not linked under a Pomodoro | no |
| M14 | journal line in `D` mentions `[[proj#^a]]` | no |
| M15 | cache not ready | no |
| M16 | open file is yesterday's daily note showing a copy of the task | no |
| M17 | two open entries both link `^a` | one mark; tooltip names the first + `+1 more` |
| M18 | cursor on the `T` line | mark remains |
| M19 | toggle off | hidden via `body.bob-today-marks`, source unchanged |
| M20 | click the mark | opens `D` at the link's line |

Progress-mark vectors P1–P14 stay untouched.

---

## 13. Recommended solution (short)

Ship **Ledger Today marks** in bob-ledger-tools: a grey small-caps `TODAY` pill immediately after the checkbox on residence task lines whose `"path#id"` is in the existing Today cache. Display-only, jump-to-ledger on click, tooltip "Linked under today's Pomodoros", session toggle, no Rust, no tags, no closed-history, no query-result pass.

That is the inverse of the In Progress half-ring, the task-line cousin of the reading-board `TODAY` pill, and the visual that sticky lanes have been missing.

The original idea is good. The membership sentence is the only part that needs to change, and it needs to change to a sentence Bob already uses.

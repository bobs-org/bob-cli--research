# Pomodoro attribution by area and project

> **Research query:** Every Pomodoro is labeled with a theme today, and those themes
> drive the statistics in `~/bob/dash_stats.md`. What is the best way to label Pomodoros
> automatically by the areas and/or projects of the tasks they link, aggregate those stats
> by area and project when possible, and let some projects (configured on
> `~/bob/sase.md`) count their sub-projects' task links as the parent project's for both
> labeling and stats? Think hard about how, when, and what to label; lead an intuitive,
> reliable, and beautiful design; critique the plan and call out any justified
> requirement changes; and recommend a solution.

![Infographic "Where the time went": Pomodoro labels derived from Task Links through residence notes to project homes and top-level areas, with sase sub-projects rolled up by `rollup: subprojects`; time split by distinct task, GTD counted as review, unlinked and unfiled gaps kept visible; quiet lowercase ledger chips and an area-and-project dash_stats panel](pomodoro_area_project_attribution_infographic.png)

## Bottom line

**Build it, but derive the labels instead of writing them.** Each Pomodoro already lists
the tasks it was for. Each task lives in an area or project note. Bob can compute "where
did this session's time go" at read time, the same way it already computes Today. That
gives labels and stats for all history back to June, with no writes, no migration, and
no drift.

The design in six rules:

1. **A task's _home_** is the [nearest area or project](#how-a-task-gets-its-home) above
   the note it lives in. If an ancestor project sets
   [`rollup: subprojects`](#the-rollup-switch), the home is lifted to the outermost such
   project. `sase.md` gets that one line.
2. **A session's homes** come from its [dedicated Task Links](#which-links-count), struck
   links included. Its minutes are
   [split evenly across its distinct linked tasks](#sessions-with-more-than-one-home).
3. **GTD sessions are [review time](#review-sessions).** Their minutes go to one
   `GTD review` row, whatever tasks they happened to close.
4. **Unlinked work stays visible.** It is shown as an [`unlinked` row](#what-is-not-attributed)
   and never guessed.
5. **Authored names stay.** `— BLOG` keeps its jobs as the capture handle, the plan
   budget atom, and the Themes view. Naming a session becomes optional.
6. **Labels are displayed, never written.** They show up as a
   [quiet lowercase chip](#how-pomodoros-are-labeled) in the ledger, the Mac agenda, the
   menu bar (instead of `UNTITLED`), and a new
   ["Where the time went" panel](#where-the-time-went-panel) on `dash_stats.md`.

Three of the four researchers reached rules 1, 4, 5, and 6 independently. I settled
their three real disagreements with vault data: how to split multi-home sessions, what
to do with GTD sessions, and how to name the flag. Details are in
[Where the reports disagreed](#where-the-reports-disagreed).

## Is this a good idea

**Yes, and the data says it's overdue.** Over the last four weeks, `bob stats show
worked` puts **39% of worked time in `other`**:

```text
theme    GTD 29h 16m 21% - BOB 22h 20m 16% - JOB 13h 55m 10% - SASE 13h 45m 10% - READ 5h 18m 4% - other 53h 06m 39%
```

That "SASE 10%" is the giveaway. Under the rules below, the same minutes come out as
**sase 43%**: BLOG, MEMORY, PYPI, REMOTE, VERIFY and the other titles are sase work under
other names. Themes also drift (FIX/FIXES, TOOL/TOOLS, four MEMORY variants), and they
can't describe anything before 2026-08-26, the first named session. 62% of all
Pomodoro minutes since June are unnamed. Task Links cover **94–95% of minutes** in both
eras, so link-derived homes fill in that history for free.

Your own Next task, `bob#^group-poms-by-prj`, says "Group pomodoros by areas/projects
**instead of** themes". The one word I'd change is "instead of". Make it "in addition
to".

**What the request gets wrong, or leaves out:**

1. **"Label" suggests writing, and writing is the wrong tool.** A written ` — SASE` would
   be a second copy of what the links already say. It goes stale when a task moves
   (Ctrl+Shift+M), when reconcile relocates a completed bullet, or when a project is
   re-parented. It can't cover about 390 h of unnamed history without rewriting months of
   daily notes. It would also collide with `#name` capture, the theme cap, and the
   duplicate-name lint. Bob has already rejected this pattern twice: the `#today` tag
   (`decisions:today-is-read-from-the-ledger`) and `#now`.
2. **Replacing themes would lose information.** BLOG, MEMORY, PYPI and HACK say *what a
   block of time was for*. `sase` says *where its tasks live*. Both are true, and both
   are worth keeping.
3. **The request doesn't say what happens to GTD sessions, and the naive answer is
   wrong.** GTD sessions collect struck links to sase and bob tasks closed during review.
   Of their non-`^gtd` links, 91% point at sase or bob. Attributing them by link would
   smear the morning review (20% of your time) across sase, bob, and "unattributed".
4. **"Exclude sub-projects from aggregating and/or labeling"** should be one switch, not
   two. If labels and stats could disagree, neither would be trusted.
5. **"When possible" undersells it.** Done, Created, and Dropped can be sliced by the same
   homes through task residence. That puts time and throughput on one axis.

The main risk isn't implementation. It's making the chart look more certain than the
evidence is. Links record what a session was *for*, not a stopwatch per task. The design
below keeps that limit visible without making the chart ugly (see
[Sessions with more than one home](#sessions-with-more-than-one-home) and
[the panel](#where-the-time-went-panel)).

## Requirement adjustments

Each adjustment is called out with what you asked, what I recommend instead, and why.

- **A1**
  - *You asked:* "Automatically label pomodoros"
  - *I recommend instead:* **Derive and display, never write.** Labels are computed at
    read time and rendered on every surface.
  - *Why:* One source of truth. Covers history. No drift and no git churn on three
    hosts. Matches the Stats engine principle and the Today decision.
- **A2**
  - *You asked:* Labels by project/area, implicitly replacing themes
  - *I recommend instead:* **Keep authored names.** Naming becomes optional, and Themes
    stays as a third Stats view.
  - *Why:* Names carry intent finer than projects. They are also the capture `#name`
    handle and the plan-budget atom.
- **A3**
  - *You asked:* Exclude some sub-projects "from being aggregated and/or used to label"
  - *I recommend instead:* **One parent-side switch** for both: `rollup: subprojects`.
    It's for reporting only, the outermost one wins, and there is no child opt-out.
  - *Why:* Labels and stats must agree. 75 descendants are too many to configure one by
    one. Blocking, Ready caps, and capture are untouched.
- **A4**
  - *You asked:* *(not stated)*
  - *I recommend instead:* **GTD sessions are review time.** All their minutes go to
    `GTD review`, and their links don't attribute.
  - *Why:* Otherwise about 20% of time (morning review) gets smeared into sase and bob.
    This matches the plan budget's existing exempt rule.
- **A5**
  - *You asked:* *(not stated)*
  - *I recommend instead:* **Multi-home sessions split evenly per distinct task.**
    Apportioned minutes are drawn in a lighter tint. No composite names are generated.
  - *Why:* Totals stay conserved, it matches the composite-theme precedent, and the
    uncertainty stays visible
    ([Sessions with more than one home](#sessions-with-more-than-one-home)).
- **A6**
  - *You asked:* Aggregate dash_stats "when possible"
  - *I recommend instead:* Add area/project parts to **Worked, Sessions, Done, Created,
    Dropped** now, and Reviewed later. Checklist, field, and formula metrics get none.
  - *Why:* Time and throughput sliced the same way is where the value is. Ratios with
    mixed homes would be invented numbers.
- **A7**
  - *You asked:* *(not stated)*
  - *I recommend instead:* The **Area** dimension uses the six top-level areas.
    Sub-areas appear only in drill-down.
  - *Why:* Stable, small, and color-codable. gtd_daily, inbox, and recur are not life
    spheres.
- **A8**
  - *You asked:* *(not stated)*
  - *I recommend instead:* **History follows the current note tree,** and the dashboard
    says so.
  - *Why:* Snapshots would need a second store. A task move re-homing its history is
    usually what you want.
- **A9**
  - *You asked:* *(not stated)*
  - *I recommend instead:* **Plan budget unchanged** in this release.
  - *Why:* Changing what the 5-theme cap counts is a planning decision, not a stats one
    ([open question 5](#open-questions-for-you)).

## Verified evidence

All figures are from my own parse of `~/bob/2026/*.md` plus note frontmatter, read-only.

### Vault figures

- **Closed sessions, Jun 1 – Oct 17:** 1,090 (1,052 with a duration, 628 h)
- **Sessions with no dedicated Task Link:** **84 of 1,090**
- **Minutes in sessions with ≥ 1 dedicated link:** 94% all-time · 95% for Sep 20 –
  Oct 17
- **Dedicated links:** 2,171, of which 1,110 carry 🍅 and 919 are struck
- **Unresolvable links:** **0**. Archived targets resolve through the `done/*_done.md`
  note's `parent:`
- **Sessions whose only links are struck:** 240
- **Last 4 weeks:** 259 sessions, 137 h 40 m, 100% named
- **GTD-only sessions, last 4 weeks:** 52 sessions, 27 h 40 m (20%)
- **Named sessions that link the daily `^gtd` row:** 94: 87 named exactly GTD, 5 GTD
  composites
- **Unnamed sessions linking `^gtd` (Jun–Aug):** 167 sessions, 114 h
- **Multi-home minutes (sase rolled up, review rule applied):** 13% of minutes; 10% span
  two top-level areas
- **Distinct project keys, last 4 weeks:** 18 without rollup → 13 with `sase` rolled up
- **Vault tree:** 13 areas (6 top-level: body, cash, dev, gtd, job, love), 90 projects
- **`sase` subtree:** 60 direct sub-projects, **75 descendants**, depth 3
- **`bob`:** a project under the **gtd** area, with 5 descendants
- **`bob stats -f json -r 4w`:** 174–177 ms on athena

### Discrepancies between reports

**Two discrepancies between reports, resolved:**

- **grk's "389 closed sessions with no links at all" doesn't reproduce.** Only 84 have
  no dedicated link. 324 have no *unstruck* link, so grk's collector apparently dropped
  struck links. That is the exact mistake grk's own A6 warns against. The lesson is
  important: **an attribution that ignores struck links loses about a quarter of
  sessions.**
- **cdx's "27 sessions with no resolvable owner"** were mostly GTD sessions whose only
  link is `[[#^gtd]]` (a daily-note target). They weren't broken links. cld's "no link
  was unresolvable" holds.

### Code facts that constrain the design

- `PomodoroSession` stores only name, minutes, and line (`src/native/stats/index.rs:79`).
  The links have to be indexed.
- `evaluate_pomodoros` splits composite names evenly, giving the remainder to the first
  component. Count mode credits the first selected component
  (`src/native/stats/metrics.rs:141`).
- **CLI compatibility bug (grk A12, confirmed):** `parts_line` prints only
  `parts_summary.iter().next()` (`src/native/stats/render.rs:824`). The map is a
  `BTreeMap`, so adding `area` would sort ahead of `theme` and *hide* it. This already
  happens to `done`: it shows `kind` and silently drops its `note` dimension.
- The Stats panel reads only `summary.theme` (`bob-ledger-tools`
  `239-plugin-stats-panel-models.js:63`). New keys won't break it, but it won't show
  them either.
- `docs/plan.md` already says that an all-exempt entry "is ignored for links too", and
  that unnamed open entries all count as one `(unnamed)` theme.
- The menu-bar indicator shows `UNTITLED` for unnamed sessions (glossary: Mac Menu Bar
  Pomodoro Indicator). Bob Mac Capture shows "Untitled Pomodoro".

## The model

### A Pomodoro has four separate things

- **Identity**
  - *Example:* the stale-safe Pomodoro ref used by capture and close
  - *Owner:* existing
- **Name (intent)**
  - *Example:* `— BLOG`
  - *Owner:* you, optional
- **Homes (where the work belongs)**
  - *Example:* `sase`
  - *Owner:* Bob, derived
- **Duration**
  - *Example:* `[t:: 15m]`, else the time range
  - *Owner:* existing Stats rules, unchanged

A derived home never becomes a name, a selector slug, or a theme component. Two sessions
can both be "sase" without becoming the same `#sase` capture target.

### How a task gets its home

For each task, from its resolved `(note, block id)`:

1. **Resolve the link** with the Today rules: exact vault path with or without `.md`,
   otherwise a unique case-insensitive basename. An empty target means the daily note.
2. **Walk `parent:`** from the residence note until the first `type: area` or `type:
   project` note (excluding `area.md`). Archive notes (`done/sase_blog_done.md`) carry
   `parent: "[[sase_blog]]"`, and ref notes carry their topic parent, so both resolve
   naturally. The walk is cycle-safe; reuse `StatsIndex::parent_ancestors`.
3. **Apply rollup.** If any project on the path to the root sets `rollup: subprojects`,
   the **outermost** one becomes the home.
4. **Area** = the top-level area above the home. The nearest sub-area is kept for
   drill-down.
5. **Special cases:**
   - The daily `^gtd` row's home is the review home
     ([Review sessions](#review-sessions)).
   - Work filed directly in an area becomes the row `dev · area tasks`, not a fake
     project.
   - A closed project is still a valid home.

The resolver lives in one shared Rust module (e.g. `src/native/homes.rs`) used by Stats,
`bob plan -f json`, `capture-pomodoros`, and `bob pomodoro`. It is memoized per note,
since about 2.2k links hit about 107 distinct notes.

### The rollup switch

The switch goes on `sase.md`:

```diff
 ---
 parent: "[[dev]]"
 type: "[[project]]"
 template: "[[new_project]]"
 status: wip
+rollup: subprojects
 created: 2026-06-01T03:30:02-04:00
```

- **Meaning:** every descendant project, at any depth and whatever its status, reports
  as `sase`. That covers labels, Stats parts, and task-metric parts.
- **Outermost wins.** If `sase_memory` also set it, `sase` still absorbs
  `sase_memory_plan`. Otherwise a descendant could escape the parent's explicit policy.
- **No child opt-out in v1.** If `sase_blog` ever needs its own slice, add a parent-side
  `rollup_except: ["[[sase_blog]]"]`. Never add a child-side key: two writers to one
  fold graph will drift.
- **Values:** `subprojects`, or absent/`off`. Anything else lints `rollup_invalid` once
  per note and is treated as off, following the `ready_cap` / `note_ready_cap_invalid`
  precedent. Project notes only in v1.
- **Reporting only.** It does not change blocking (`#prj_is_blocked` inheritance), Ready
  caps (whose own decision rejects "parent rollups"), Sub-projects lines, review tiers,
  or capture routing. Say so in `docs/projects.md` and show a dim `rollup` flag in
  `bob projects list`.
- **Rollup groups; it doesn't hide.** A new `in:` filter on pomodoro metrics matches the
  *pre-rollup* ancestry. So `{kind: pomodoro, in: [sase_blog]}` still measures blog time,
  and the docs' `sase_time: {themes: [SASE]}` example becomes `in: [sase]`.

On the name: the four reports proposed `pomodoro_rollup: subtree`, `rollup: true`,
`stats_fold: children`, and `subproject_rollup: true`. I picked `rollup: subprojects`
because it reads as a sentence in frontmatter ("roll up subprojects"). It isn't tied to
Pomodoros, since it also groups Done/Created. It leaves room for `off`, and it avoids an
opaque boolean.

### Which links count

- **Dedicated Task Links** are direct children of the entry whose whole body is one
  `[[t#^id]]`, `![[t#^id]]`, or aliased link. This is Today's rule, **plus** three
  closed-session differences:
  - **Struck links count.** The strike *is* the history.
  - 🍅 is decoration, not an eligibility test.
  - Embeds count.
- **Excluded:** fenced code, mixed-prose bullets, deeper descendants and work notes, and
  Depends-On/Work Log/Schedule Log lines. (The vault had zero sessions whose only links
  were deeper, so no fallback is needed.)
- **Deduplication:** by resolved `(path, block id)` within a session. Five links to one
  task count as one task.
- **Open sessions** use the same rule. Their homes are a forecast that updates as you
  link and move. They are never counted as worked time.
- **Closed sessions** are read after close selection. Deferred and dropped links have
  already moved out, so what remains is what the session was for.

This needs a sibling of `list_queued_links` that includes struck links (that function
skips them, correctly, for Today and the `=x` lineup).

### Review sessions

A **review session** is either:

- an entry whose every name component is in `plan.exempt` (yours: `[GTD]`), or
- **(history bridge)** an unnamed entry that links the daily `^gtd` row.

All of its minutes go to the reserved project key **`GTD review`** (the label uses the
exempt name). Its area is the top-level area of the note the exempt name routes to
(`GTD` → `gtd`). Its links don't attribute. Elsewhere, a `^gtd` link counts as a
review-home task.

**Why:**

- It's the plan budget's existing rule restated.
- It keeps parts summing to the total. I rejected grk's "omit GTD from the pies"
  because the pie would then quietly stop adding up to Worked.
- The bridge is well supported: in the named era, `^gtd` ⇔ GTD for 92 of 94 sessions.
  Without the bridge, 114 h of summer review would be scattered across sase and bob.

**The cost, honestly:**

- 21 of 99 GTD sessions since Aug 26 carried a live work link (12 h 50 m). Today's
  10:20 session, with "Agent is waiting to run on apollo", is one example. Those
  minutes count as review.
- The fix is already in the grammar: name it `GTD + SASE`. A non-exempt component means
  the links decide.
- The bridge is a heuristic for legacy unnamed data. 70 of the 167 bridged sessions also
  had live work links. Drop the bridge if the summer numbers look wrong to you.

`review_time` should switch to the same predicate, so that it and the `GTD review` row
always agree. This is a minor adjustment, and it recovers June–August review history.

### Sessions with more than one home

**Each distinct linked task gets an equal share of the session's minutes. Shares are
summed per home, and area shares are the sums of their homes.**

- Integer minutes: floor each share and give the remainder to the first home in ledger
  order, mirroring the composite-theme rule.
- **Count mode** (`sessions`) gives the whole session to its **lead home**: the most
  tasks, with ties going to ledger order. Parts still add up.
- **Honesty without a junk row:** each part also reports `apportioned` minutes, meaning
  minutes that came from multi-home sessions. The panel draws that portion of the bar in
  a lighter tint of the same hue. Tooltips and drill-down show the actual shares.

The four researchers split three ways on this. The data shows the choice matters less
than the debate suggests. Each rule's result over the last 4 weeks:

- **Split per task (cld, grk), chosen:** sase 43% · bob 18%
- **Split per project (gem):** sase 43% · bob 18% · other effects: every key within 1
  point
- **"Mixed" bucket (cdx):** sase 38% · bob 13% · other effects: `(mixed)` becomes the
  **third-largest row** at 14%

Per-task and per-project splits are practically identical in aggregate. cdx's Mixed
bucket is the most honest about any single session, but it turns 14% of the chart into a
row that says nothing. The tint keeps cdx's honesty: you can see exactly how much of
each bar is apportioned (16% of all project minutes this period), and no row is
meaningless. No composite names (`SASE + BOB`) are ever generated.

### What is not attributed

Each bucket, its meaning, and its size over the last 4 weeks:

- **`unlinked`**
  - *Meaning:* closed session with no dedicated link (SHIT chores, RELAUNCH, a few bare
    SASE/BLOG/READ)
  - *Last 4 weeks:* 6 h 10 m (4%)
- **`unfiled`**
  - *Meaning:* a link to a note outside any area or project, or an ambiguous or
    unresolved link (with a lint)
  - *Last 4 weeks:* 25 m

Both are neutral gray and always shown, never folded into `other`. Their fix-it text is
"link the task" or "file the task". I rejected guessing a home from the name
(`SASE` → `sase`): it would recover about 40 minutes in four weeks and add a second,
lossy model.

### History follows the current tree

Homes are computed from today's notes. Moving a task re-homes its past minutes. So does
re-parenting `bob` or toggling `rollup`. That matches how Done and Created already treat
residence, and git keeps the old view. Totals never change. The panel footer says
**"Grouped by today's note tree · from Task Links"**. Frozen snapshots are rejected for
v1 ([Rejected alternatives](#rejected-alternatives)).

## How Pomodoros are labeled

**What.** A session's label is its homes as **lowercase note stems**, ordered by share.
At most two are shown, plus `+N` for the rest. Authored names are ALL CAPS by grammar.
Derived homes are lowercase, exactly as you type them in links and `@route`s. That
typographic split is the whole distinction: no extra glyphs, and you can never confuse
the two.

**When.** Always, on read. Open sessions show a live forecast (hollow dot) that updates
as you link or move tasks. Closed sessions show the attribution Stats uses (filled dot).
Nothing is frozen at close.

**How.** It is never written to Markdown. It is rendered by:

- **Obsidian daily note**
  - *Change:* A Live Preview mark after the Pomodoro line: an area-colored dot plus the
    stem in muted text. The tooltip shows shares. It reveals plain text under the cursor
    like the other marks.
  - *Owner:* bob-ledger-tools
- **Menu bar / tmux (`bob pomodoro`)**
  - *Change:* An unnamed running session shows `sase (25m) · 🍅 12:34` instead of
    `UNTITLED`. Named sessions are unchanged.
  - *Owner:* bob-cli. Coordinate with the chezmoi Hammerspoon spec.
- **Bob Mac Capture idle agenda**
  - *Change:* Unnamed entries show the home instead of "Untitled Pomodoro". Named
    entries add a muted home. Decoded with `decodeIfPresent`.
  - *Owner:* bob-mac-capture (thin client)
- **`capture-pomodoros` / `bob plan -f json`**
  - *Change:* An additive `homes: [{key, label, area, share, tasks}]` on each entry
  - *Owner:* bob-cli
- **Stats drill-down**
  - *Change:* Per-session homes and shares
  - *Owner:* bob-cli + plugin

**Quietness rules (the "beautiful" part):**

- **Suppress the chip when it adds nothing.** If the name equals the only home (`— BOB` →
  bob, `— SASE` → sase), show no chip. If it's a named review session (`— GTD`), show no
  chip. If it's unlinked, show no chip: the absence is the signal, and Stats counts it.
- The chip never routes captures, reorders anything, changes status, or feeds the plan
  budget.

Today's ledger would read:

```text
- [x] (0710-0800 50m) — GTD
- [x] (0930-0955 25m) — GTD
- [x] (1020-1045 25m) — GTD
- [x] (1310-1325 15m) — BOB
- [x] (1350-1405 15m) — BLOG     ● sase
- [ ] (1410-1500 50m) — BOB
- [ ] ()              — BLOG     ○ sase
- [ ] ()              — MEMORY   ○ sase
- [ ] ()              — PYPI     ○ sase
- [ ] ()              — HACK     ○ bob · dev +1
```

At a glance you can see that three of today's five planned themes are one project. That
is useful plan-budget feedback the theme count alone can't give
([open question 5](#open-questions-for-you)).

**Implementation of the Obsidian chip.** Rust is the authority. The plugin chip is a
small JS mirror (resolve, walk parents, apply rollup, apply the review rule; no minute
math) that runs **shared conformance vectors** verbatim. That follows the house rule in
`docs/plan.md`: "Rust implements it; bob-ledger-tools mirrors it in JavaScript". It also
works on mobile, where the plugin can't spawn `bob`, and it avoids a subprocess per
edit. grk preferred calling `bob`. That is a fine fallback if the mirror ever drifts, but
it would lose mobile.

## Stats and `dash_stats.md`

### The Stats report

Schema 1, additive:

- **New parts dimensions:**
  - `area` and `project` on pomodoro metrics.
  - `area` and `project` on task metrics (done, created, dropped), by residence through
    the same resolver.
  - Later: on `reviewed`, via the journal `key`.
- **Keys:** vault-relative note paths (`sase.md`), so titles never become identities.
  Reserved bucket keys are `@review:GTD`, `@unlinked`, and `@unfiled`.
- **A top-level `homes` catalog:**
  `{key: {label, kind: project|area|bucket, area, subarea, path, rolled_up: 75}}`. The
  renderer draws hierarchy and color from it without guessing.
- **Per-part `apportioned` minutes**
  ([Sessions with more than one home](#sessions-with-more-than-one-home)).
- **Collapse:** `project` collapses to top five plus `other`, with buckets always shown
  outside the five. `area` keeps the full roster.
- **`in:` / `exclude_in`** on pomodoro specs, ancestry-aware and pre-rollup. In minutes
  mode a session contributes only the matching tasks' shares. In count mode it counts
  once if any task matches. These AND with `themes` / `exclude_themes`.
- **Definition and limits copy:**
  - "Attributed from Task Links."
  - "Grouped by today's note tree."
  - "Sessions with several homes are split evenly by task."
  - "Links show what a session was for, not a stopwatch."
- **Health:** `unlinked_minutes`, `unfiled_links`, `ambiguous_links`, `rollup_invalid`.

### Fix the CLI first

Make `parts_line` print **every** dimension in a stable order (`area`, `project`,
`theme`; for tasks `kind`, `area`, `project`, `note`). That ships in the same change that
adds the keys. This fixes grk's ship-together risk at the source, and it un-hides `done`'s
`note` line today.

```text
 area     dev 62h 25m 45% - gtd 56h 09m 41% - job 12h 19m 9% - love 12m 0% - unlinked 6h 10m 4% - unfiled 25m 0%
 project  sase 59h 04m 43% - GTD review 28h 47m 21% - bob 24h 18m 18% - job_2026_apply_29 4h 58m 4% - job · area tasks 3h 34m 3% - other 10h 24m 8% - unlinked 6h 10m 4% - unfiled 25m 0%
 theme    GTD 29h 16m 21% - BOB 22h 20m 16% - JOB 13h 55m 10% - SASE 13h 45m 10% - READ 5h 18m 4% - other 53h 06m 39%
```

(Area and project figures come from my simulation of these rules on the last four weeks.
Implementation must reproduce them through hand-computed fixtures, not trust them.)

### Where the time went panel

This replaces the hard-coded "Worked by theme" context panel. It isn't a choice between
an Area view and a Project view: **one panel shows both**, and Themes is one click away.

```text
Where the time went · Sep 20 – Oct 17 · 137h 40m            [ Areas & projects ]  Themes
▕██████████████████████ dev ▏█████████████████████ gtd ▏████ job ▏░▏

● dev                                         62h 25m   45%
    sase                 ██████████████▒▒▒    59h 04m   43%   includes 75 sub-projects
    dev_plex_hack_patch  ▌                     1h 58m    1%
    dev · area tasks     ▌                     1h 23m    1%
● gtd                                         56h 09m   41%
    GTD review           ████████▏            28h 47m   21%
    bob                  ██████▒▒             24h 18m   18%
    bob_gtd              ▌▒                    3h 04m    2%
● job                                         12h 19m    9%
    job_2026_apply_29    █▒                    4h 58m    4%
    job · area tasks     █                     3h 34m    3%
    2 more                                     3h 47m    3%
● love                                            12m   <1%
░ unlinked                                     6h 10m    4%   link the task to attribute it
░ unfiled                                         25m   <1%

▒ apportioned from sessions with several homes · grouped by today's note tree · from Task Links
```

- **Form:**
  - The six-area part-to-whole is a single horizontal stacked bar with direct labels on
    the segments that fit.
  - The 13+ projects are a ranked table with mini-bars, grouped under their area. More
    than about seven classes should be a table, not more colors.
- **Color follows the entity, never its rank:**
  - The six top-level areas get fixed categorical hues, validated in light and dark. An
    optional `color:` on the area note overrides, otherwise there's a fixed order.
  - Buckets are neutral gray.
  - The same hue is used for the ledger chip dot, the bar segment, and the project
    mini-bars.
  - Text stays in text tokens.
- **Apportioned minutes** are a lighter tint of the same hue, not a hatch pattern
  (texture stays reserved for color-vision deficiency, print, and forced colors).
- **Rows:**
  - A project name opens its note.
  - A separate "sessions" action lists the contributing sessions (date, time, duration,
    name, homes, shares) and jumps to the daily-note line.
  - `sase` notes "includes 75 sub-projects", with their raw homes in the expansion.
- **Interaction:**
  - Pinning a day or week on the focus chart filters the panel.
  - An optional "stack by area" toggle on the Worked focus chart.
- **Unchanged:** metric tiles, range controls, prior comparison, and keyboard behavior.
  Themes view is byte-for-byte today's panel.

The note `dash_stats.md` itself doesn't change. It stays one empty `bob-stats` fence.

## Where the reports disagreed

Each question, what each researcher proposed, and the decision:

- **Write labels into the ledger?**
  - *cdx:* no
  - *cld:* no
  - *grk:* no (v2: fill unnamed)
  - *gem:* yes, at link/start/close
  - *Decision:* **No.** Display everywhere, including the menu bar, so no surface needs a
    written name.
- **Multi-home minutes**
  - *cdx:* "Mixed" bucket
  - *cld:* split per task
  - *grk:* split per link (≈ task)
  - *gem:* split per project
  - *Decision:* **Per task + apportioned tint**
    ([Sessions with more than one home](#sessions-with-more-than-one-home))
- **GTD sessions**
  - *cdx:* no rule
  - *cld:* → GTD home, plus bridge
  - *grk:* omit from parts
  - *gem:* no rule
  - *Decision:* **`GTD review` row, plus bridge** ([Review sessions](#review-sessions))
- **Flag**
  - *cdx:* `pomodoro_rollup: subtree`
  - *cld:* `rollup: true`
  - *grk:* `stats_fold: children`
  - *gem:* `subproject_rollup: true`
  - *Decision:* **`rollup: subprojects`**
- **Descendant opt-out**
  - *cdx:* forbidden
  - *cld:* none
  - *grk:* parent-side list, later
  - *gem:* child `false`
  - *Decision:* **None in v1.** Parent-side `rollup_except` if ever needed.
- **Area level**
  - *cdx:* nearest
  - *cld:* top-level
  - *grk:* nearest
  - *gem:* ancestor
  - *Decision:* **Top-level**; sub-areas in drill-down
- **Default panel**
  - *cdx:* Areas
  - *cld:* Area → Project
  - *grk:* Project
  - *gem:* Projects
  - *Decision:* **One panel: area bar plus projects grouped by area**
- **Override**
  - *cdx:* `[work:: [[x]]]` field
  - *cld:* the name
  - *grk:* the name
  - *gem:* manual name
  - *Decision:* **Nothing new in v1.** Name and links suffice; `[work::]` reserved for
    v2.
- **Ledger chip**
  - *cdx:* Rust facts only
  - *cld:* JS mirror + vectors
  - *grk:* call `bob`
  - *gem:* n/a
  - *Decision:* **JS mirror + shared vectors**
- **Plan budget**
  - *cdx:* unchanged
  - *cld:* unchanged (homes later)
  - *grk:* unchanged
  - *gem:* count projects
  - *Decision:* **Unchanged** ([open question 5](#open-questions-for-you))
- **Task metrics**
  - *cdx:* yes
  - *cld:* yes, plus journal
  - *grk:* yes
  - *gem:* yes
  - *Decision:* **Yes**; journal later

gem's report was the outlier: it proposed writing ` — SASE` names and re-pointing the
theme cap at projects. Its rollup traversal and its panel ideas (dimension pills,
pinned-day filtering, click-to-open) survive. Its writes don't, for the
[A1](#requirement-adjustments) reasons.

## Rejected alternatives

Each alternative and why not:

- **Auto-write ` — SASE` at link, start, or close (gem):** Clobbers intent names, crowds
  the theme cap, races moves and reconcile, can't backfill, and churns git on three hosts
- **Fill names only for unnamed sessions (grk v2):** Once the menu bar, Mac agenda, and
  ledger show derived homes, no surface needs it; it adds a writer for nothing
- **Write `[prj:: …]` on Pomodoro lines:** A second copy of the links, the same flaw as
  `#today`
- **Freeze homes at close:** Two code paths, still wrong after moves, and needs sync,
  undo, and migration semantics nothing here requires
- **A "Mixed" bucket by default:** Honest, but 14% of the chart says nothing. The tint is
  honest *and* informative.
- **First link or majority wins:** Order-dependent; small edits swing whole sessions
- **A theme → project mapping table:** Manual, rots as names drift, and covers no unnamed
  history
- **A child-side `rollup_into:` or opt-out:** 75 notes to maintain, and two writers to
  one policy
- **Rollup by default for every project:** Not what you asked for. `job_2026_apply_29`
  (5 h) shows sub-projects can matter.
- **Sunburst or treemap:** The area bar plus grouped table carries the same hierarchy in
  the existing visual grammar
- **LLM classification of session notes:** Non-deterministic. The vault already has
  explicit structure.

## Implementation plan

Each phase, its repo, its deliverable, and when it is done:

- **P1**
  - *Repo:* bob-cli + vault
  - *Deliverable:* Shared `homes` resolver; indexed session links (struck included);
    `rollup` parse and lint; review predicate; `area`/`project` parts on pomodoro and
    task metrics; reserved buckets; `homes` catalog; `apportioned`; pomodoro `in:`;
    `parts_line` prints every dimension; docs (`docs/stats.md`, `docs/projects.md`, a
    normative `docs/pomodoro-homes.md`); add `rollup: subprojects` to `sase.md` in the
    same cut
  - *Done when:* `bob stats show worked` prints area, project, and theme lines; golden
    vectors pass; real-vault figures match the figures in
    [Fix the CLI first](#fix-the-cli-first) up to rounding; runtime stays under ~250 ms
- **P2**
  - *Repo:* bob-plugins
  - *Deliverable:* "Where the time went" panel, area hues, tint, drill-down; preview
    fixtures with long stems (`job_2026_apply_29`)
  - *Done when:* Light/dark × narrow/wide preview matrix renders; palette validator
    passes; `bob plugins sync`
- **P3**
  - *Repo:* all three + chezmoi
  - *Deliverable:* `homes` in `capture-pomodoros`/`bob plan` JSON; `bob pomodoro`
    derived home for unnamed sessions; ledger chip (JS mirror + vectors); Mac agenda
    decode
  - *Done when:* Chips match Rust on every vector; Mac builds pass macOS CI; the menu bar
    shows `sase` instead of `UNTITLED`
- **Later**
  - *Repo:* —
  - *Deliverable:* `review_time` on the review predicate; `[work::]` override if mixed or
    unlinked minutes start to bother you; `rollup` on `bob`; a day ribbon colored by
    area; a home-aware plan budget
  - *Done when:* each gated on a few weeks of real use

**Golden vectors (hand-computed, M-table style):**

- **Rollup:**
  - a rolled-up child and grandchild
  - outermost-wins with nested flags
  - `rollup: yes please` lints and is treated as off
  - `in: [sase_blog]` still matches under rollup
- **Resolution:**
  - a `done/` archive target
  - a ref note parented to a sub-project
  - an area-resident task
  - a closed project
  - a parent cycle
  - an ambiguous basename leading to `unfiled` plus a lint
- **Review:**
  - a GTD session with foreign struck links
  - an unnamed `^gtd` bridge session
  - `GTD + BOB`
- **Splitting:**
  - a 2:1 split with an odd minute count
  - the same task linked twice
  - count-mode lead home
- **Totals and output:**
  - an unlinked session
  - parts sum to the total in every dimension
  - the CLI prints every dimension in stable order
- **Chip:**
  - name equals home, so the chip is suppressed
  - two sase sessions remain distinct capture targets
  - an old plugin with a new CLI, and the reverse

**Durable memory, when implementing** (through `/sase_memory_write`, not part of this
research):

- A decision record: "Pomodoro homes are derived from Task Links, never written; review
  sessions are their own home; rollup is reporting-only."
- A glossary term **Home**.

## Risks

- **Under-counted work in GTD-named sessions** (about 13 h since Aug 26). The fix is to
  rename to a composite. Reopen [Review sessions](#review-sessions) if the `GTD review`
  row feels inflated.
- **History restatement** when the tree changes. The footer states it, and totals are
  unaffected.
- **Rust/JS drift** for the chip. Shared vectors mitigate it, and the Rust number is
  always the one Stats shows.
- **`bob pomodoro` output change.** The Hammerspoon parser is spec'd in the chezmoi
  README, so land both together.
- **Over-trust.** Apportioned tint, the "from Task Links" copy, and session drill-down
  keep the chart's claims inspectable.

## Open questions for you

1. **Should `bob` stay under the `gtd` area?** The area view will show **gtd 41%**, which
   is half morning review (21%) and half building Bob (20%). If you think of Bob as dev
   work, re-parent it and all its history moves with it. This is the most important
   question the new view raises.
2. **Is folding `sase_blog` into `sase` what you want?** The BLOG theme keeps it visible
   in Themes, and `in: [sase_blog]` can still measure it. If it should be its own
   project row, that's `rollup_except` later.
3. **Keep the summer history bridge?** It reclassifies 114 h of unnamed `^gtd` sessions
   as review. 70 of those 167 sessions also linked live work.
4. **Will you keep naming every session?** You don't have to any more. A name is now only
   a capture handle and an intent note.
5. **Later: should the plan budget count homes?** Today's five planned themes are four
   homes, and three of the themes are all `sase`. Counting each unnamed entry by its
   derived home instead of one shared `(unnamed)` theme would be the smallest step. It
   changes planning semantics, so it should be a separate decision.

## Recommended solution

1. **Derive a home for every linked task:** nearest area/project by residence, lifted to
   the outermost project with `rollup: subprojects`. Add that line to `~/bob/sase.md`.
   It changes reporting only.
2. **Attribute each closed Pomodoro's minutes from its dedicated Task Links**, struck
   ones included, split evenly per distinct task. GTD-only sessions, plus unnamed
   `^gtd` sessions from before names existed, go wholly to a `GTD review` row.
   Sessions with no links stay in an explicit `unlinked` row. Nothing is ever guessed or
   dropped, and every dimension sums to Worked.
3. **Extend `bob stats` additively** with `area` and `project` parts on Worked, Sessions,
   Done, Created, and Dropped, plus a `homes` catalog, `apportioned` minutes, and
   pomodoro `in:` filters. Fix the CLI so every dimension prints.
4. **Give `dash_stats.md` one "Where the time went" panel:**
   - a six-area stacked bar over a project table grouped by area
   - one fixed hue per area
   - a lighter tint for apportioned minutes
   - drill-down to sessions
   - Themes one click away
5. **Label Pomodoros without writing anything.** Show a lowercase home chip in the ledger,
   the Mac agenda, and the menu bar (`sase` instead of `UNTITLED`). It is suppressed
   when the authored name already says the same thing.
6. **Keep authored names exactly as they work today** (capture handle, theme cap, Themes
   view), but make them optional. Leave the plan budget, blocking, Ready caps, and
   history untouched.

The result should feel like Bob quietly reading structure you already maintain:
ALL-CAPS for what you meant, lowercase for where it landed, one color per area
everywhere.

## Sources

Lead synthesis · 2026-10-18 · Merges the `cdx`, `cld`, `grk`, and `gem` reports in this
directory. I re-checked their load-bearing claims against bob-cli `c4ac06f`, bob-plugins
`74e3d9b`, and a read-only parse of the live vault.

- **Researcher reports** (this directory): `__cdx.md` (categorical attribution, evidence
  rules, conservation, the four-concept model), `__cld.md` (history coverage, the GTD
  rule and bridge, panel design, marks precedent), `__grk.md` (render.rs bug, `in:`
  versus fold, unnamed-fill analysis), `__gem.md` (rollup traversal, panel pills,
  pinned-day filtering).
- **bob-cli `c4ac06f`:** `docs/plan.md` (Names, Exempt entries, Themes, Today);
  `docs/stats.md`; `docs/capture.md` (`#name` selectors); `docs/task-status-hooks.md`
  §Pomodoro Marker (relocation, marker provenance); `src/native/stats/index.rs:79`;
  `src/native/stats/metrics.rs:141`; `src/native/stats/render.rs:824`.
- **bob-plugins `74e3d9b`:** `plugins/bob-ledger-tools/src/239-plugin-stats-panel-models.js:57–63`,
  `239-plugin-stats-panel-render.js:185`; `236-plugin-stats-data.js` (the `bob`
  subprocess); `block-id-prompt` project-parent model.
- **Live vault, read-only, 2026-10-18:**
  - `2026/*.md` Pomodoros sections
  - frontmatter of `sase.md`, `bob.md`, `gtd.md`, `gtd_daily.md`, `dev.md`, `job.md`,
    `dash_stats.md`, and `done/*_done.md`
  - `bob stats show worked|done -r 4w`, plus timing of `bob stats -f json -r 4w`
  - the parsing scripts were throwaway, in `/tmp`, following the rules in
    [The model](#the-model)
- **SASE memory (audited reads):** `obsidian.md`; glossary Pomodoro, Task Link, Project
  Note, Area Note, Work Log, Mac Menu Bar Pomodoro Indicator; decisions
  `today-is-read-from-the-ledger`, `subprojects-inherit-project-blocking`,
  `note-ready-cap-counts-the-lane`, `mac-capture-is-a-thin-client`.
- **External** (via the researcher reports): Toggl and Clockify keep project hierarchy
  separate from activity tags, which is the precedent for keeping themes as intent. In
  Toggl, multi-project entries are split by hand. None of these sources validate an
  automatic split; that choice rests on Bob's own data
  ([Sessions with more than one home](#sessions-with-more-than-one-home)).

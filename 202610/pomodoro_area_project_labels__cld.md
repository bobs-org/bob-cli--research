---
title: "Labeling Pomodoros by area and project: derive it from Task Links, don't write it"
author: research.4t.cld
date: 2026-10-18
scope: bob-cli (stats engine, plan/capture JSON), bob-plugins (bob-ledger-tools Stats block + ledger marks), Bob vault (sase.md)
origin_task: "[[bob#^group-poms-by-prj]]"
---

# Labeling Pomodoros by area and project

**Recommendation in one paragraph.** Don't write project labels into the daily note.
Derive each Pomodoro's label at read time from the Task Links it already contains, the
same way Today is derived from the ledger. Each linked task has a **home**: the nearest
area or project note above where the task lives, lifted to the highest ancestor that sets
`rollup: true`. A session's minutes are split evenly across its distinct linked tasks and
then summed per home. GTD sessions count as GTD time, whatever they link. Sessions
without usable links show up as an explicit `(unlinked)` or `(unfiled)` bucket and are
never guessed. Stats gains `area` and `project` breakdowns for **every** metric whose
input can be traced to a note (Worked, Sessions, Done, Created, Dropped, Reviewed), not
just Pomodoro metrics. Obsidian shows the labels as derived chips beside each Pomodoro and
as an area → project allocation view on the Stats page. Themes (the `— NAME` suffix) stay
as the planning handle and intent label; they stop being the main way stats are sliced.
`sase.md` gets one line: `rollup: true`.

The rest of this report gives the evidence, a critique of the request, the design
decisions one by one, requirement changes (each flagged as such), and a phased
implementation plan.

---

## Contents

1. [What exists today](#1-what-exists-today)
2. [What the vault says (data)](#2-what-the-vault-says-data)
3. [Critique: is this a good idea?](#3-critique-is-this-a-good-idea)
4. [The design questions, one at a time](#4-the-design-questions-one-at-a-time)
5. [Requirement adjustments (called out)](#5-requirement-adjustments-called-out)
6. [Recommended solution (spec)](#6-recommended-solution-spec)
7. [Alternatives considered and rejected](#7-alternatives-considered-and-rejected)
8. [Open questions for Bryan](#8-open-questions-for-bryan)
9. [Appendix: method and sources](#9-appendix-method-and-sources)

---

## 1. What exists today

**Themes are authored Pomodoro names.** A Pomodoro line can end in ` — NAME`, and `+`
splits a name into components (`GTD + SASE`) (`docs/plan.md` §Names). Names currently do
three jobs:

| Job | Where | Notes |
| --- | --- | --- |
| **Planning handle** | capture grammar: `@route:id#name` files a link under a named session, and `=#name` / `==#name` start one (`docs/capture.md`) | Names are how you address a planned session. |
| **Focus budget** | `plan.max_themes` (yours is 5) counts distinct non-exempt open names (`docs/plan.md` §Themes) | `GTD` is exempt, and **exempt entries' links are already ignored by the link budget.** |
| **Stats grouping** | the `pomodoro` kind has a `theme` part plus `themes` / `exclude_themes` filters; composite names split minutes evenly with the remainder to the first part; `review_time` = `themes: [GTD]` (`docs/stats.md` §Metric kinds) | `theme` is one of two dimensions (with `note`) that collapse to top five plus `other`. |

**Task Links are already structured evidence of what a session was for.** Under a closed
session (`docs/task-status-hooks.md` §Pomodoro Marker):

- `🍅 [[note#^id]]` is a live link that took part in the closed session.
- `~~[[note#^id]]~~` is a task completed while the session was open.
- `🍅 ~~[[…]]~~` is a task that took part and was completed later.

When a task is completed during the *current* session, reconcile moves its bullet into
that session. That is why **GTD sessions collect struck links to tasks from all over the
vault**: you close them during the morning review.

**The vault has a clean tree.** There are 13 area notes and 90 project notes. Six areas are
top-level (`body`, `cash`, `dev`, `gtd`, `job`, `love`). `sase` (a project under `dev`)
lists 60 sub-projects on its generated Sub-projects line (23 open, 37 closed), plus
deeper nesting (`sase_art → sase_art_links → sase_art_links_panel`). `bob` is a project
under the **`gtd`** area. Each `#task` lives in exactly one area or project note
(glossary: *Area Note*). The two exceptions that matter here are the daily `^gtd` row and
archived rows in `done/*_done.md`. Archive notes carry `parent: "[[sase]]"`, so they
resolve back to their source.

**Stats has a firm engine principle.** "The engine derives every number at read time from
vault data and never writes" (`docs/stats.md` §Engine principle). The prior stats
synthesis made the same call: *"Never store what the vault keeps."* `StatsIndex` already
holds `parent_of`, a `NoteIndex` resolver, and parsed closed sessions
(`src/native/stats/index.rs`). It does **not** yet record each session's links.

**Decision precedent.** `decisions:today-is-read-from-the-ledger` rejected a hooks-managed
`#today` tag because it would be "a second copy of the ledger … with churn, races, and
staleness." A written project label on a Pomodoro line would be exactly that kind of
second copy.

**Display precedent.** bob-ledger-tools already renders derived, never-written marks
(freshness, priority, date, progress, task-tag marks, and the unblocked glyph). Each one
is specified in a `docs/*-marks.md` contract and paired with a JS mirror that runs
conformance vectors. A "Pomodoro label mark" fits that family.

---

## 2. What the vault says (data)

I parsed every `## Pomodoros` section in `~/bob/2026/*.md` and resolved every link
under each closed session to its note and parent chain. The scripts are in
[§9](#9-appendix-method-and-sources). Totals since the ledger began (2026-06-01): **1,069
closed sessions, 630 h, 2,177 links.** 99.7% of those links are dedicated Task Links
(a direct child bullet that is exactly one link). **No link was unresolvable**: archived
targets resolve through `done/*_done.md` and its `parent`.

### 2.1 Links cover the whole history; names don't

| Period | Minutes named | Minutes with ≥1 Task Link |
| --- | --- | --- |
| Jun 1 – Aug 23 | **0%** | 81–100% per week (typically 95%+) |
| Aug 24 – Aug 30 | 44% | 99% |
| Aug 31 – Oct 17 | **100%** | 85–100% per week |

Since June, 61% of all Pomodoro minutes are `(unnamed)`. Labels derived from links would
fill in **three months of history that themes can never recover**, with no backfill and
no writes.

### 2.2 Themes are fragmented; the vault tree is not

Last four weeks (Sep 20 – Oct 17, 137 h 40 m). This matches `bob stats show worked` today.

| Dimension | Distinct keys | Top-5 shown | `other` |
| --- | --- | --- | --- |
| Theme (today) | **38** | GTD 21 · BOB 16 · JOB 10 · SASE 10 · READ 4 | **39%** |
| Project, no rollup | 20 | sase 34 · gtd 20 · bob 18 · (unlinked/unfiled) 4 · sase_goals 4 | 20% |
| **Project, `sase` rolled up** | **13** | sase 43 · gtd 20 · bob 18 · (unlinked/unfiled) 4 · job_2026_apply_29 4 | **11%** |
| **Area** | **5** | dev 46 · gtd 41 · job 9 · (unlinked/unfiled) 4 · love <1 | 0% |

Theme names drift (`FIX`/`FIXES`, `TOOL`/`TOOLS`, `MEMORY`/`MEMORY WEBS`/`PLAN
MEMORY`/`AUDIT MEMORY`): 73 distinct full names since August. The area and project
vocabulary is the vault's own tree, so it cannot drift that way.

### 2.3 Most themes are sub-topics of one project

Each theme's Task Links grouped by home (sase rolled up), Aug 31 – Oct 17:

| Theme | Links | Where they point |
| --- | --- | --- |
| **GTD** | 189 | gtd_daily 84 · **sase 76** · **bob 24** · cash 2 · … |
| BOB | 110 | bob 103 · sase 6 · job_2026 1 |
| JOB | 65 | job_2026 39 · job 11 · sase 6 · job_update_cv 5 · bob 4 |
| SASE | 53 | sase 53 |
| REMOTE / GOALS / VERIFY / TOOL / FIXES / BLOG / DECKS / MEMORY WEBS … | 10–29 each | ≈ all sase |
| ATHENA | 13 | dev_plex_hack_patch 8 · sase 3 · dev 2 |

Three takeaways:

1. **Themes are finer than projects.** REMOTE, VERIFY, BLOG, and DECKS are intents inside
   `sase`. Replacing themes with projects would lose that detail, so keep both
   dimensions.
2. **GTD sessions contaminate link-based attribution.** About 55% of their links point at
   sase/bob tasks closed during review. Splitting GTD minutes by link would quietly move
   about 15 h a month of review time into "sase". GTD needs its own rule.
3. **Non-GTD sessions are mostly single-home.** With `sase` rolled up, 79–84% of
   link-derived minutes come from sessions whose links all share one home. The split rule
   only matters for the remaining ~20%, so it's low-stakes and a simple rule is enough.

### 2.4 Simulated result of the recommended rules

These figures apply the GTD rule from §4.4, including the history bridge, and `rollup: true`
on `sase`:

| Window | GTD sessions | Link-derived | (unlinked/unfiled) | Projects (top) | Areas |
| --- | --- | --- | --- | --- | --- |
| Jun 1 – Aug 30 (401.6 h) | 29% | 66% (84% single-home) | 5% | sase 53 · gtd 29 · bob 10 · dev 1 | dev 54 · gtd 40 · cash <1 |
| Sep 20 – Oct 17 (137.7 h) | 20% | 75% (79% single-home) | 4% | sase 43 · gtd 20 · bob 18 · job_2026_apply_29 4 · job 3 | dev 46 · gtd 41 · job 9 |
| Jun 1 – Oct 17 (628 h) | 26% | 68% (83% single-home) | 5% | sase 52 · gtd 26 · bob 11 · dev 1 | dev 53 · gtd 39 · job 2 |

What's in the unlinked/unfiled bucket: 19.5 h of unnamed sessions with no links, 9.9 h
of `SHIT` sessions (unlinked personal chores), plus a few links into notes outside any
area or project (the `obsidian` note and legacy `ref/…` notes). That bucket is the right
signal to show, not noise to hide.

### 2.5 Two real days, labeled

```text
2026-10-18                                  derived label
[x] 0710-0800 50m — GTD                     gtd · review            (links: ^gtd, 2× sase_blog struck)
[x] 0930-0955 25m — GTD                     gtd · review
[x] 1020-1045 25m — GTD                     gtd · review            (has 🍅 sase#^image-agent-mermaid)
[x] 1250-1300 10m — GTD                     gtd · review
[x] 1310-1325 15m — BOB                     bob
[x] 1350-1405 15m — BLOG                    sase                    (sase_blog → rolled up)
[ ] 1410-1500 50m — BOB                     bob                     (open: a plan, never counted)
[ ] ()        — BLOG / MEMORY / PYPI        sase / sase / sase
[ ] ()        — HACK                        bob · dev · dev_plex_hack_patch  (⅓ each)

2026-10-17
[x] — ATHENA ×3, HACK                       dev_plex_hack_patch
[x] — ATHENA                                dev · dev_plex_hack_patch (½ each)
[x] — SASE ×3 / BOB ×2                      sase / bob
```

Two things to notice:

- Today's five open themes span **four homes in two areas**, and three of the five
  (BLOG, MEMORY, PYPI) are all `sase`. That's useful context for the theme budget
  (§8, Q5).
- The HACK session's `bob` link is a reference task filed in `bob.md`
  (`^ref-athena-plex-compromise-incident-report`). Home follows residence, so filing
  decisions show up in the stats. Moving a task re-homes its history, which is correct.

---

## 3. Critique: is this a good idea?

**Yes, and it's overdue.** Theme-based stats ask you to type the right label every
session, and it still doesn't work well:

- 39% of the last four weeks lands in `other`.
- Everything before Aug 26 (the first named session) is `(unnamed)`.
- The names drift.

Project and area labels are free (the links are already there for about 95% of minutes),
consistent (the vault tree), and retroactive. They also make Bob's numbers comparable for
the first time: *time into sase* vs *tasks done in sase* vs *review answers on sase rows*,
all sliced the same way.

**What's weak in the request as stated:**

1. **"Labeling" suggests writing, and writing is the wrong mechanism.** A written label
   is a second copy of what the links already say. It drifts when reconcile relocates
   bullets, when Ctrl+Shift+M moves tasks, or when a project is re-parented. It can't
   cover the 386 h of unnamed history without a mass backfill. It churns git across three
   hosts. It also conflicts with the `— NAME` grammar that capture depends on. Bob has
   rejected this pattern before (`#today`, `#now`). **Derive the label and display it.**
2. **Replacing themes would lose real information.** Themes carry intent inside a project
   (REMOTE vs BLOG vs VERIFY inside sase), and they are the capture handle for planned
   sessions. Keep them as a secondary dimension. What changes is that **naming becomes
   optional**: you name a session when you want a handle, not because stats need it.
3. **The request doesn't address GTD.** Label-by-link applied naively to GTD sessions is
   wrong about 55% of the time by link count (§2.3). This needs an explicit rule.
4. **"Exclude sub-projects" is phrased per project. It should be a general reporting
   rollup.** It applies to areas as well as projects (for example `inbox` folding
   `mac_inbox`/`gkeep_inbox`), works transitively, and **only changes how results are
   grouped**. It must never touch blocking, Ready caps, Sub-projects lines, or capture
   routing.
5. **"By area and project when possible" undersells it.** It is possible for almost
   everything:
   - Pomodoro metrics, through links.
   - Task metrics, through residence (the `note` part already exists).
   - Review metrics, through the journal `key` (`sase.md#^…`).

   Only checklist and field metrics have no natural home.

**Risks I'd accept, with honest labeling:**

- **Links are evidence of attention, not a stopwatch.** A session with four planned links
  where you touched one still splits four ways. The metric definition and `limits` should
  say "attributed by Task Links".
- **History follows today's tree.** Re-parenting `bob` under `dev` would move its history
  to `dev`. That is the behavior you want for "where did my time go", it matches how
  Done/Created already treat residence, and git keeps the old view.
- **The tree's choices become visible.** Today `bob` sits under `gtd`, so the gtd area is
  41% of recent time but only about half of that is review. That's a structure question
  the new stats will make you face (§8, Q1), which is a good thing.

---

## 4. The design questions, one at a time

### 4.1 What is the label? — a task's **home**

> **Home(task)** = start at the note the task lives in. Walk up `parent` until you reach
> an area or project note (`type: [[area]]` / `[[project]]`). If any ancestor of that
> note, or the note itself, sets `rollup: true`, the **highest** such ancestor is the
> home instead.

- Archive rows (`done/x_done.md`) resolve through their `parent` to `x`, as Done does today.
- The daily `^gtd` row's home is the GTD home (§4.4).
- A task whose chain never reaches an area or project has home `(unfiled)`.
- The **area** of a home is its highest area ancestor (one of the six top-level areas).
  A project with no area above it gets area `(no area)`.
- The project dimension's key is the home itself. When work is filed directly in an
  area (for example a task in `job.md`), that row is the area. The UI marks it
  `job · area tasks`.

A Pomodoro's **label** is the multiset of its linked tasks' homes. With shares that's
`{sase: 2, bob: 1}`. For display it's ordered by share: `sase · bob`.

Rejected alternatives:
- Top-level project only, with no configuration. It contradicts the explicit ask, though
  the data partly supports it (§8, Q3).
- The link's literal target note without the parent walk. Reference notes, archives, and
  context notes would fall through.

### 4.2 When and where? — **read time, everywhere, never written**

| Option | Verdict |
| --- | --- |
| Write `— NAME` automatically at close | ✗ Collides with capture grammar and the theme cap, drifts, can't cover history |
| Write an inline field (`[prj:: sase]`) at close via reconcile | ✗ A second source of truth, git churn, and `[t::]`-style parsers must learn it |
| Freeze a label at close, derive before that | ✗ Two code paths, and still drifts after moves |
| **Derive at read time (Rust), display as marks (JS mirror)** | ✓ Zero writes, retroactive, self-healing, matches the Stats engine principle and the Today precedent |

Open (planned) sessions get labels too. Those are live previews that change as you
link work. Stats only ever counts closed sessions, as now.

### 4.3 Multi-home sessions — **split evenly by distinct linked task**

- Each distinct linked task (deduplicated by resolved `(note, block id)`) gets an equal
  share of the session's minutes. Shares are then summed by home. A session with 2 sase
  links and 1 bob link splits ⅔ / ⅓.
- Integer minutes: floor each share and give the remainder to the **first home in ledger
  order**. That mirrors the existing composite-theme rule ("remainder to the first").
- **Count mode** (`sessions`) puts the whole session in its **lead home** (largest share,
  ties broken by ledger order), so the parts still add up to the total. This mirrors the
  existing count-mode rule.
- Every link counts: live, 🍅, struck, and embedded alike. The marker isn't a reliable
  provenance signal. Reconcile itself says a missing marker on a struck link "is not
  backfilled", so weighting by 🍅 would build on sand.

Rejected alternatives:
- Majority-takes-all. Unstable on ties and drops information.
- First link wins. Depends on ordering.
- Equal split per home. That gives 4 sase links and 1 bob link a 50/50 split, which
  over-weights incidental links.

### 4.4 GTD sessions — **review time is its own home**

> A session is a **GTD session** when every name component is in `plan.exempt` (yours:
> `[GTD]`), **or** when it is unnamed and links today's daily `^gtd` row. All of a GTD
> session's minutes go to the **GTD home**, which is the area or project whose route or
> `project_name_aliases` matches the exempt name (case-insensitive): `GTD` → `gtd.md`.
> The session's other links don't drive attribution. Elsewhere, a link to the `^gtd` row
> also counts toward the GTD home.

Why this rule:

- It's the plan budget's rule restated. Exempt entries' links are already ignored there.
- The unnamed-plus-`^gtd` clause is a **history bridge**. 167 unnamed sessions
  (June–Aug) link `^gtd`. In the named era, 87 of the 94 named sessions that link
  `^gtd` are named exactly GTD, and 5 more are GTD composites. Without the bridge, about 60 h of summer review time would be smeared into
  sase/bob.
- A session that mixes GTD with real work (`GTD + ATHENA`) has a non-exempt component, so
  its links decide. That's rare: 6 sessions since June.

The trade-off: a 25-minute "GTD" session where you actually spent 20 minutes on a sase
agent counts as GTD. Your name says GTD, so that's honest. If you want it counted as
sase, name it differently. The name is your override.

**Alternative.** `gtd_daily` is arguably the more precise GTD home, since the `^gtd` row's
own text is `[[gtd_daily]]`. I picked `gtd` because the name-to-route match needs no
config. See §8, Q2.

### 4.5 Unlinked and unfiled — **explicit, never guessed**

- No resolvable link → `(unlinked)`. The fix is to link your work.
- A link to a note outside any area or project → `(unfiled)`. The fix is to file the
  task.

Both render in neutral gray with a texture, counted like any other part. I considered
falling back to "a name that matches a route" for unlinked sessions and rejected it:
it would have matched **0%** of unlinked minutes in the data, and it adds a rule to
explain. GTD is the only name-to-route match, and it exists because of §4.4.

### 4.6 The rollup switch — **`rollup: true` on any area or project note**

```diff
 ---
 parent: "[[dev]]"
 type: "[[project]]"
 template: "[[new_project]]"
 status: wip
+rollup: true
 created: 2026-06-01T03:30:02-04:00
```

**Semantics:**

- Every descendant area or project (transitively, regardless of status) reports as this
  note.
- Nested rollups: the **highest** rollup ancestor wins.
- Only `true`/`false` are valid. Anything else gets a stats warning `rollup_invalid` that
  names the note and is treated as `false`. This follows the `ready_cap` /
  `note_ready_cap_invalid` precedent.

**Reporting only.** Rollup changes how stats are grouped and how labels are displayed.
It does not change blocking, Ready caps, Sub-projects lines, review tiers, or capture
routing. Say so in the docs and in `bob projects list` output (a dim `rollup` flag).

**Rollup groups results; it doesn't hide detail.** The `in:` filter (§6.3) matches each
task's *pre-rollup* ancestry, so `blog_time: {kind: pomodoro, in: [sase_blog]}` still
works when `sase` rolls up. You choose how coarse the grouping is, and you can still
select any sub-project with `in:`.

On the name: `rollup` is the standard reporting word (sub-accounts roll up into a
parent). It's one token and it reads correctly in frontmatter ("sase: rollup"). Other
names I considered: `rollup_subprojects` (too narrow, since it also applies to areas),
`stats_rollup` (it also affects chips), `absorb`/`fold` (less familiar). A depth form
(`rollup: 1`) is a possible later extension and isn't needed yet.

### 4.7 What happens to themes?

- Themes stay **exactly** as they are for capture, the plan budget, and `themes:`
  filters.
- In stats, `theme` becomes the third dimension after `area` and `project`. The Stats
  panel defaults to Area → Project, with Theme one click away.
- **Names become optional.** Stats no longer need them, so leave a session unnamed when
  you don't need a capture handle. Its chip shows what it was for anyway.

### 4.8 Which metrics get area/project parts?

| Metric family | Source of home | Get `area`/`project` parts? |
| --- | --- | --- |
| `pomodoro` (worked, sessions, review_time) | Task Links → home (§4.3–4.4) | **Yes** |
| `tasks` (done, created, dropped; net via formula) | residence → home (archive → source) | **Yes**. Keep `note` for compatibility |
| `journal` (reviewed, keep_rate) | event `key` `note.md#^id` → home | **Yes**. reviewed by area answers "what did review touch" |
| `checklist`, `field`, `formula` | — | No (formulas inherit nothing; ratios with mixed homes are meaningless) |

### 4.9 How should it look? — intuitive, calm, consistent

Rules from the dataviz checklist that apply here:

- **Color follows the entity, never its rank.**
- **Part-to-whole → horizontal stacked bar.**
- **More than ~7 classes → table.**
- **Text wears text tokens.**

From those:

1. **One hue per top-level area, everywhere.** There are six areas, so six categorical
   slots plus neutral for `(unlinked)`/`(unfiled)`.
   - Assignment is stable: an optional `color:` (a Bob palette name) on the area note,
     falling back to a fixed order by area stem.
   - Run the palette validator in light and dark mode before shipping.
   - Avoid reusing the metric hues (orange = Worked) where both appear side by side.
2. **Ledger marks (daily note).** Next to each Pomodoro line, after the name, a quiet
   chip: an area-colored dot plus the home stem in muted text.
   - A split session shows `● sase · ● bob`, ordered by share.
   - The tooltip gives the shares and link counts: "sase 2 links · 67% / bob 1 link · 33%".
   - GTD sessions get a hollow `◌ gtd · review`. Unlinked sessions get a dim `○ unlinked`.
   - Nothing is written. Moving the cursor onto the line reveals plain text, like the
     other marks.
3. **Stats page: "Where the time went"** (context panel for Pomodoro metrics):

   ```text
   Worked by area · Sep 20 – Oct 17 · 137h 40m          [ Area | Project | Theme ]
   ▕████████████████████████ dev ▏████████████████████ gtd ▏████ job ▏░ ▏
   ● dev     63h 05m  46%
       sase                59h 40m  43%   rolls up 23 sub-projects
       dev_plex_hack_patch  2h 00m   1%
       dev · area tasks     1h 25m   1%
   ● gtd     56h 05m  41%
       gtd · review        27h 40m  20%
       bob                 24h 20m  18%
       …
   ● job     12h 20m   9%
   ░ unlinked / unfiled   5h 55m   4%   ← link or file this work
   ```

   - Areas are a stacked allocation bar with a legend and direct labels on segments that
     fit.
   - Projects are a ranked table with mini-bars, grouped under their area.
   - Optional "stack by area" toggle on the Worked focus chart. Week and month grouping
     read best.
4. **Terminal (`bob stats show worked`).** Two lines above `theme`, in the same format:

   ```text
    area     dev 63h 05m 46% · gtd 56h 05m 41% · job 12h 20m 9% · (unlinked) 5h 55m 4%
    project  sase 59h 40m 43% · gtd 27h 40m 20% · bob 24h 20m 18% · (unlinked) 5h 55m 4% · job_2026_apply_29 5h 00m 4% · other 15h 05m 11%
    theme    GTD 29h 16m 21% · BOB 22h 20m 16% · JOB 13h 55m 10% · SASE 13h 45m 10% · READ 5h 18m 4% · other 53h 06m 39%
   ```

5. **Later polish: the day ribbon.** In the daily `bob-plan` block and Stats day detail, a
   thin timeline of the day's sessions colored by area. You'd see the morning's GTD,
   then dev, at a glance.

---

## 5. Requirement adjustments (called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | "Automatically label pomodoros" | **Derive and display; never write** the label into the vault | Single source of truth (links), covers history back to June, no drift or git churn, matches the Stats principle and the Today decision |
| A2 | Labels by project/area (implicitly replacing themes) | **Keep themes** as a secondary dimension and the planning handle; **naming becomes optional** | Themes carry intent finer than projects (§2.3) and drive capture and the theme budget |
| A3 | (not stated) | **GTD sessions are review time**: their links don't attribute; minutes go to the GTD home | 55% of GTD links point elsewhere (§2.3) |
| A4 | Exclude sub-projects of *some projects* | **`rollup: true` on any area or project note**, transitive, highest wins, **reporting only**; `in:` still reaches sub-projects | Same intent, general, no hidden behavior changes |
| A5 | Aggregate dash_stats by area and project "when possible" | Add `area`/`project` parts to **pomodoro, task, and journal** metrics, plus `in:` filters for pomodoro metrics | It's possible almost everywhere, and the shared slicing is where the value is |
| A6 | (not stated) | **Split** multi-home sessions by distinct linked task; count mode goes to the lead home | About 20% of sessions are multi-home; splitting keeps the parts adding up to the total |
| A7 | (not stated) | Unlinked and unfiled are **explicit** buckets, never guessed | "Never a silent zero" ethos; they also tell you what to fix |

---

## 6. Recommended solution (spec)

### 6.1 Definitions (normative; for `docs/stats.md` and a new `docs/pomodoro-labels.md`)

1. **Task Links of a session** are the dedicated Task Links of a closed or open entry,
   using the same rule as Today and `list_queued_links`, with two differences:
   - struck links count (they are history);
   - when an entry has no dedicated links, fall back to any block link in its subtree.

   Resolve each link with the Today resolver (exact vault path with or without `.md`,
   then a unique case-insensitive basename; an empty target means the daily note).
   Ambiguous or unresolved links become `(unfiled)` with lint
   `pomodoro_link_unresolved`.
2. **Home** of a resolved task line: §4.1. Parent links must parse every form Bob already
   accepts, including `[[love.md|love]]`. Cycles stop safely (`parent_ancestors` already
   handles that).
3. **GTD session** and **GTD home**: §4.4. If no note matches the exempt name, the
   session is `(unfiled)` with warning `exempt_name_unfiled`.
4. **Attribution**: §4.3. Minutes come from `[t::]`, else the range estimate (unchanged).
5. **Rollup**: §4.6.

### 6.2 Config

- `sase.md`: add `rollup: true` (the diff in §4.6).
- No `config.yml` changes are required. `plan.exempt` already supplies GTD.

### 6.3 Stats engine (bob-cli)

- **Index.** Give `PomodoroSession` its `links: Vec<LinkRef>`, reusing
  `capture_pomodoro_start::list_queued_links`-style scanning. Record `type` and `rollup`
  for each area and project note during the existing frontmatter pass.
- **Resolver.** Add a small pure module (`src/native/stats/homes.rs`, or
  `src/native/homes.rs` if plan and capture JSON reuse it). It maps a note to
  `Home { key, kind, area, chain, rollup_from }`, computed once per note and memoized.
- **Parts.** Add `area` and `project` dimensions to pomodoro, tasks, and journal
  evaluators. `project` collapses to top five plus `other` like `note` and `theme`;
  `area` keeps the full roster.
- **Filters.** Add `in: [...]` to the `pomodoro` kind. It matches each linked task's
  pre-rollup ancestry, the same semantics as the tasks kind's `in:`.
  - In minutes mode, a session contributes only the shares of the tasks that match.
  - In count mode, a session counts once if any task matches.
  - Keep `themes`/`exclude_themes`, which AND with `in:`.
- **Report.** Additive schema-1 fields:
  - A top-level `homes` catalog:
    `{"sase": {"label": "sase", "kind": "project", "area": "dev", "status": "wip", "rollup": true, "rolled_up": 23}, …}`.
    Consumers build the tree and colors from it without guessing.
  - `health.pomodoros`: `{unlinked_minutes, unfiled_links, ambiguous_links}`.
- **Definitions and limits.** Worked's `definition` gains "attributed to areas and
  projects by Task Links". `limits` gains "History follows the current vault tree" and
  "Links show attention, not duration".
- **`review_time`.** Optionally redefine it as GTD sessions (the §4.4 predicate) instead
  of `themes: [GTD]`. That recovers its June–August history through the bridge. Expose it
  as `sessions: gtd`, or keep the theme filter and treat bridged sessions as theme `GTD`.
  This is low priority.
- **Performance.** One more map lookup per link (about 2.2k links). Expect the cost to
  stay within the recorded ~370 ms budget. Measure it with the existing real-vault
  parity test.
- **Fixtures.** Add these to `tests/fixtures/stats/vault/`:
  - a rolled-up project with a grandchild;
  - a GTD session carrying foreign struck links;
  - an unnamed `^gtd` bridge session;
  - a 2:1 split session with an odd minute count (remainder rule);
  - an unlinked session;
  - an unfiled link;
  - a `done/` archive link;
  - an invalid `rollup: yes please`.

  Hand-compute the expected values, following the existing M-vector discipline.

### 6.4 Other bob-cli surfaces (additive JSON, no new commands)

- `bob plan -f json` and `capture-pomodoros` (frozen protocol, additive only): add a
  `homes` array per entry `[{key, area, share}]`. Bob Mac Capture's idle agenda can
  render chips without ever computing them, which keeps it a thin client.
- `bob projects list`: show a dim `rollup` flag.
- **No new subcommand.** `cli_rules.md` prefers that read-only reports stay top-level,
  and this is a dimension of `bob stats`, not a new report.

### 6.5 bob-plugins (bob-ledger-tools)

- **Stats panel.** Area / Project / Theme segmented control, the allocation bar, the
  grouped ranked table, and a "stack by area" toggle. Everything comes from the report's
  parts plus the `homes` catalog; nothing is recomputed.
- **Pomodoro label marks.** A pure core plus a Live Preview mark, following the
  `docs/task-tag-marks.md` contract style. The JS mirror resolves links through
  `metadataCache.getFirstLinkpathDest` and frontmatter `type`/`parent`/`rollup`, and it
  runs shared conformance vectors (`tests/fixtures/pomodoro_labels/*.json`) verbatim, the
  same discipline as plan budget and Today. Document the known divergence on ambiguous
  basenames, as Today does.

### 6.6 Phasing

| Phase | Repo | Deliverable | Done when |
| --- | --- | --- | --- |
| **P1** | bob-cli + vault | Resolver, rollup, session links, `area`/`project` parts on all three metric families, `in:`, `homes` catalog, terminal lines, fixtures, docs; `rollup: true` on `sase.md` | `bob stats show worked` prints area and project lines; parity test green; ≤ ~400 ms |
| **P2** | bob-plugins | Stats panel Area/Project views, allocation bar, stack-by-area | Preview matrix (light/dark, narrow/wide) renders; palette validator passes |
| **P3** | both | Ledger label marks + conformance vectors; `homes` in plan/capture JSON | Chips match Rust on every vector; Mac agenda can show them |
| Later | — | Day ribbon; `review_time` via GTD sessions; optional `rollup` depth; a home-aware plan budget (§8, Q5) | — |

### 6.7 Durable memory (when implementing, via `/sase_memory_write`)

- **Decision record:** *Pomodoro labels are derived from Task Links, never written.*
  Cite this report, A1–A7, the GTD rule, and "rollup is reporting-only."
- **Glossary term: Home.** "The area or project a task's work counts toward: nearest
  area/project above its residence, lifted to the highest `rollup` ancestor."

---

## 7. Alternatives considered and rejected

| Alternative | Why not |
| --- | --- |
| Auto-fill `— NAME` from links at close | Rewrites your planning handle. It changes the theme cap's meaning, adds git churn on three hosts, can't backfill 386 h cleanly, and drifts after moves and relocations |
| Write `[prj:: …]` on Pomodoro lines via reconcile | A second copy of the links, the same flaw as the rejected `#today` tag |
| A theme → project mapping table in config | Manual, rots as names drift, and covers no unnamed history. (GTD's name-to-route match is the one narrow exception) |
| A per-sub-project opt-out (child says "count me as my parent") | The config is scattered across about 60 notes. Your mental model is parent-side ("sase rolls up"). Parent-side `rollup` plus `in:` covers it |
| Rollup by default for all projects | Reasonable (§8, Q3), but you asked for opt-in, and `job_2026_apply_29` (5 h) shows sub-projects can matter |
| Spawn `bob` from the ledger to get chips | Per-keystroke latency. A JS mirror with vectors is the established pattern for live marks |
| Weighting by 🍅 vs struck markers | Marker provenance is explicitly lossy (`task-status-hooks.md`) |

External practice points the same way. Toggl Track allows **one project per time entry**.
For multi-project work, its community suggests splitting entries manually, tagging the
other projects, or using an overhead bucket. Bob already has better evidence than a tag
(links), so it can do the split automatically and keep GTD as the overhead bucket. Timing
for Mac assigns time to projects with rules instead of asking for labels. Here the "rule"
is simply "the tasks you linked".

---

## 8. Open questions for Bryan

1. **Should `bob` stay under the `gtd` area?** Today the gtd area is 41% of recent time,
   about half review and half bob development. If you think of bob as dev work, re-parent
   it. All history moves with it.
2. **Where should GTD time go: `gtd` or `gtd_daily`?** I recommend `gtd`, because the
   name-to-route match needs no config. `gtd_daily` is more precise; that would take one
   explicit setting.
3. **Rollup opt-in (as asked) or default-to-top-level-project?** Opt-in is what you asked
   for and what I specified. Outside sase, sub-project time is small (bob_gtd 3 h,
   job_2026_apply_29 5 h over four weeks), so either works. Revisit after a month of data.
4. **Do you want to stop naming every session?** With derived labels, names only matter
   as capture handles and for the theme budget.
5. **Later: should the plan budget count homes?** Today's five open themes are four
   homes, and three of the themes are all `sase`.
   A cap on homes would be a stronger focus signal than a cap on names. I'm not
   recommending it now, because it changes planning semantics.

---

## 9. Appendix: method and sources

**Data.**
- All `~/bob/2026/2026????.md` daily notes, read 2026-10-18.
- `## Pomodoros` sections parsed into column-0 checkbox entries. Name = text after
  `) —`; minutes = `[t:: Nm]`.
- Links extracted from indented child lines (`[[target#^id]]`, struck, embedded, 🍅).
- Each target resolved to a note by exact path, then unique basename.
- Ancestry from frontmatter `parent`; kind from `type: [[area]]`/`[[project]]`.
- The simulation applied §4.3–4.6 with `rollup` on `sase`.
- Minor approximation: the simulation sent the `^gtd` row in non-GTD sessions to
  `gtd_daily` rather than `gtd`. That moves about 1 h of the 4-week figures between two
  `gtd`-area rows.
- The scripts were throwaway (`/tmp`), not committed. They are simple enough to
  reproduce from this description.

**Repo references.**
- `docs/stats.md`: Engine principle, Metric kinds, Built-in catalog, Data model.
- `docs/plan.md`: Names, Exempt entries, Themes, Today.
- `docs/task-status-hooks.md`: Pomodoro Marker, retirement and relocation.
- `docs/projects.md`: parent, Sub-projects lines, `project_name_aliases`.
- `docs/capture.md`: `#name`, `=#name`, plan-budget warnings.
- `docs/task-tag-marks.md`: the marks contract style.
- `src/native/stats/index.rs`: `StatsIndex`, `PomodoroSession`, `parent_ancestors`.
- `src/native/capture_pomodoro_start.rs`: `list_queued_links`.
- bob-plugins `plugins/bob-ledger-tools/src/239-plugin-stats-panel-*.js`: the existing
  "by theme" panel.

**Memory read.** `obsidian.md`, `cli_rules.md`; glossary: Pomodoro, Task Link, Area
Note, Project Note, Project Task, Work Log, Schedule Log; decision:
`today-is-read-from-the-ledger`. Prior (unrelated) research:
`research:202610/bob_daily_stats/bob_daily_stats__final.md`.

**External.**
- Toggl community: one project per time entry, and workarounds (split entries, tags, an
  overhead bucket):
  [Assign two or more projects to a single time entry](https://community.toggl.com/t/assign-two-or-more-projects-to-a-single-time-entry/1254),
  [Tasks instead of projects](https://community.toggl.com/t/tasks-instead-of-projects-to-track-data-and-ability-to-select-clients-for-specific-projects-tasks/3512).
- Timing for Mac: rule-based automatic project assignment:
  [The Sweet Setup review](https://thesweetsetup.com/automatic-time-tracking-with-timing-for-mac/),
  [MacSparky](https://www.macsparky.com/blog/2024/12/timing-a-smarter-way-to-track-your-time-sponsor/).
  None of the sources I found describe Timing's sub-project behavior, so I've made no
  claim about it.

# Label pomodoros by residence, keep themes as intention

Researcher: `grk`. Independent design research for automatically labeling
pomodoros from the area/project of their Task Links, aggregating
`dash_stats.md` by those homes, and folding sase.md's sub-projects into
sase. Peer swarm reports were not consulted.

## Verdict

Do the stats half. Pause the rewrite half.

The request is right about the *question* (`dash_stats.md` cannot see where
work actually lived). It is wrong about the *write*. Pomodoro ` — NAME`
tails are a daily-plan instrument: they feed the theme cap, GTD exemption,
inventory-label lint, `#NAME` capture, and the session's own title
(BLOG, MEMORY, PYPI, HACK, ATHENA). Task Links already record residence.
Stats already derives every number at read time and refuses to stamp a
second copy of a fact the vault still holds.

Ship **residence attribution**: at `bob stats` read time, walk each closed
pomodoro's dedicated Task Links to a folded area/project, and add `project`
and `area` parts next to today's `theme` parts. Configure the fold on
`sase.md` as `stats_fold: children`. Leave named tails alone. Optionally,
later, fill *unnamed* open tails at close when the session has a single
folded home.

That is the design that is intuitive (the note the task lives in is the
label), reliable (one resolver, no write races, history works tomorrow for
every surviving link), and beautiful (one Worked chart that can speak
*where* and *what I called it* at the same time).

## Bottom line

1. **Themes stay user-owned session titles and plan-budget atoms.** GTD
   stays exempt. `#NAME` capture, `bob capture-pomodoro-name`, the 5-theme
   cap, and names like BLOG / MEMORY / HACK keep working exactly as they
   do today.
2. **Attribution is a read-time dimension of the ledger, in the same family
   as Today.** Dedicated Task Links under a closed pomodoro, resolved to
   residence, walked through `parent:`, then folded by `stats_fold`,
   produce `project` and `area` parts on `worked` / `sessions`. Nothing is
   written to the daily note for v1.
3. **`sase.md` opts in with `stats_fold: children`.** Every descendant
   project, its refs, and its `done/<stem>_done.md` archive map to `sase`.
   Other parents stay unfolded until they opt in. `job_2026_apply_29` and
   `dev_plex_hack_patch` keep their own slices.
4. **Exempt GTD sessions do not enter project/area pies.** Morning review
   already has `review_time`. A GTD row that happens to mention
   `sase_blog` is still review.
5. **Mixed sessions split minutes by unique dedicated links after fold.**
   A HACK pomodoro with bob + dev + `dev_plex_hack_patch` links is three
   slices in stats and still titled HACK in the ledger.
6. **Phase 2 (optional):** fill an unnamed open pomodoro at `=x` (or at
   first link) when the folded home is unique. Never overwrite a selectable
   name. A dim Obsidian chip may *show* the derived home beside the name.

---

## 1. Is this a good idea?

Yes, as a derived stats dimension. The live vault already proves the
theme pie is the wrong lens for "where did the weeks go?"

`bob stats show worked -r 4w` on 2026-10-18, median 5h/day:

| Theme part | Minutes | Share |
| --- | ---: | ---: |
| GTD | 29h 16m | 21% |
| BOB | 22h 20m | 16% |
| JOB | 13h 55m | 10% |
| SASE | 13h 45m | 10% |
| READ | 5h 18m | 4% |
| **other** | **53h 06m** | **39%** |

"Other" is the tell. After the engine's top-five collapse, almost two
fifths of worked time is unnamed sessions plus BLOG, MEMORY, MEMORY WEBS,
REMOTE, PYPI, ATHENA, HACK, FIX, TOOL, GOALS, SASE V18, and the rest of
the long tail. Those names are good *session titles*. They are a poor
*portfolio*.

A scan of 144 daily notes with a Pomodoros section (2026):

| Fact | Count |
| --- | ---: |
| Closed named sessions | 445 |
| Closed unnamed sessions | 645 |
| Closed sessions with dedicated Task Links | 787 |
| Of those, mixed *note* targets | 209 |
| Unique link targets | 107 |
| Top target `done/sase_done` | 582 |
| Top target `done/bob_done` | 168 |
| Direct `sase` | 76 |
| Direct `bob` | 17 |

Rewriting names from links, then folding `sase_*` into `sase`, on closed
linked sessions:

| Folded home | Sessions (presence, not minutes) |
| --- | ---: |
| sase | 562 |
| bob | 123 |
| gtd_daily | 21 |
| job_2026_apply_29 | 11 |
| Mixed *after* the sase fold | 69 |
| Closed with no links at all | 389 |

Theme SASE is 10% of four-week minutes. Folded residence sase is the
majority of linked sessions across the year. That gap is the feature.

The idea is a good idea if `dash_stats.md` starts answering "how much of
this month was sase / bob / job / the plex incident?" from the links
Bryan already files. It is a bad idea if Bob starts renaming BLOG to
SASE at 2pm because a `sase_blog` link landed under the row.

---

## 2. Critique of the original plan

The request asks to: automatically label pomodoros from the
projects/areas of their Task Links; aggregate `dash_stats.md` by area and
project when possible; exclude some parents' sub-projects from being
labels, treating those links as if they pointed at the parent; configure
that on `~/bob/sase.md`; think hard about how / when / what to label;
lead the design so it is intuitive, reliable, and beautiful.

The bob.md Next task captured the same itch today as `^group-poms-by-prj`:
"Group pomodoros by areas/projects instead of themes!" That title is the
trap. Themes and homes are two different questions.

### What to keep

- **Homes as the stats grain.** Area and project notes are the vault's
  actual filing system (`type: "[[area]]"` / `"[[project]]"`, scalar
  `parent:`). Stats should speak that language.
- **A parent-configured fold.** sase has 60 direct project children, 23
  still `wip`. A naive per-note pie would be a bag of `sase_pager`,
  `sase_memory`, `sase_pypi_releases`, `sase_blog`, … that Bryan does not
  use as life categories. Folding them into sase is the whole point of
  the second bullet.
- **Task Links as the evidence.** Today is already "dedicated Task Links
  under today's open Pomodoros" (`docs/plan.md`,
  `decisions:today-is-read-from-the-ledger`). Attribution should reuse
  that object, on closed rows, at read time.
- **Beauty as a first-class constraint.** `dash_stats.md` is a 16-line
  page around one empty `bob-stats` fence. The plugin already refuses to
  invent numbers. New parts have to arrive in schema-1 JSON, formatted,
  with a legend the renderer can draw without guessing.

### What to change

These are explicit requirement adjustments.

**A1. Do not replace themes. Add a residence dimension. (product)**

Themes currently do two jobs: (1) today's plan budget (Bryan's config:
`max_themes: 5`, `exempt: [GTD]`, `inventory_labels: [LATER, MISC, NEW
FEATURES]`); (2) the only pomodoro parts key in stats. Job (1) is
healthy. Job (2) is overloaded.

Today's open ledger (2026-10-18) is the exhibit:

```text
— GTD     struck sase_blog review links
— BOB     [[bob#^faster-ref-process]]
— BLOG    [[sase_blog#^ref-gas-town-emergency-user-manual]]
— BOB     [[bob#^replace-x-syntax]] · [[bob#^group-poms-by-prj]]
— BLOG    two sase_blog refs
— MEMORY  [[sase_memory#^dynamic-agents-md]]
— PYPI    sase_pypi_releases ×3 + sase#^release-v18
— HACK    bob + dev + dev_plex_hack_patch
```

BLOG, MEMORY, PYPI, HACK are *what this block of time is for*. sase /
bob / dev_plex_hack_patch are *where the tasks live*. Auto-naming those
rows SASE / BOB / DEV would smash the 5-theme cap into two or three
buckets and erase the titles Bryan actually uses to steer the day.

Keep ` — NAME` as intention. Add `project` / `area` as residence.

**A2. Derive attribution at read time. Do not stamp a home onto the row
for v1. (write policy)**

Stats' own engine principle (`docs/stats.md`): every number is derived
at read time; the review journal is the only thing Stats ever records,
because freshness stamps cannot recover answers. Today was moved off a
`#today` tag for the same reason
(`decisions:today-is-read-from-the-ledger`). Blocked is derived from
inputs (`decisions:task-status-is-derived` and its successors).

A written ` — SASE` tail would:

- Race `N<ctrl+shift+m>` moves, `=x` close, and capture `#NAME`.
- Go stale when a second project is linked under the same row.
- Fail for 389 closed sessions that have no links.
- Fail to backfill 645 unnamed historical sessions unless a migrator
  rewrites months of daily notes.
- Fight GTD exemption (this morning's first GTD row already carries
  struck `sase_blog` links).

Read-time attribution backfills the whole ledger the moment it ships,
including `done/sase_done` via
`collect_done::source_relative_path_from_archive`. That is the
reliability win.

**A3. Fold is a parent frontmatter flag, not a global rule and not a
child opt-out. (config)**

The request puts the configuration on the parent that wants its children
absorbed. Mirror `ready_cap:`: one short key on the note.

```yaml
# sase.md
stats_fold: children
```

Meaning: any Task Link whose residence, after archive mapping, is this
note or a descendant, attributes as this note. Nested grandchildren
(`sase_memory` → `sase_memory_plan`, refs parented at `sase_blog`) fold
to sase, because sase is the ancestor that opted in.

v1 values:

| Value | Effect |
| --- | --- |
| absent | each project/area is its own label |
| `children` | all descendants fold into this note |
| a list of wikilinks | only those children (and *their* descendants) fold |
| `off` / `false` | explicit no-fold |

Invalid values lint (`stats_fold_invalid`) and behave as absent, same
shape as `note_ready_cap_invalid`.

Do not add a child-side `stats_parent:` override in v1. Two writers for
one fold graph will drift. If a later child must stand apart (sase_blog
as a public product), add `stats_fold_except:` on the *parent*.

**A4. Skip project/area parts for fully exempt sessions. (definition)**

`review_time` already measures GTD-themed minutes. This morning:

```text
- [x] (**0710-0800** [t:: 50m]) — GTD
    - ~~[[#^gtd]]~~
    - ~~[[sase_blog#^ref-sase-launch-post-outline]]~~
    - ~~[[sase_blog#^intro-proposal]]~~
```

Those 50 minutes are morning review. Counting them as sase work would
inflate the portfolio with ritual. Rule: if every name component is in
`plan.exempt` (default GTD), omit `project` / `area` parts for that row
(or emit a single `(review)` key if a complete partition is required).
Composite `GTD + BOB` (2026-10-16, 70m of bob_done links) still
attributes from links, because a non-exempt component is present.

Always ignore the canonical daily note's `^gtd` link, matching the task
metrics exclusion.

**A5. Split mixed sessions by dedicated-link weight after fold. (math)**

Composite themes already split minutes evenly across name components,
remainder to the first (`docs/stats.md`, golden M1). Residence should
split by *unique dedicated Task Links after fold*, remainder to ledger
order of the first link. Two `sase_blog` links and one `bob` link in a
30m row become 20m sase + 10m bob once sase folds. Count mode still
assigns the row to its first matching part so parts add up.

Do not auto-build composite names (`SASE + BOB`) for mixed rows. That
would mint themes against the cap. Mixed is a stats fact, not a new
title.

**A6. Closed-session evidence includes struck dedicated links. (history)**

`list_queued_links` skips struck spans because Today and `=x` lineup are
about *live* work. Closed rows strike finished and unlinked tasks; the
strike *is* the history. Stats needs a sibling collector: same
"direct child, exactly one block link" rule, struck included, fenced
and Depends-On / Sub-projects / Work Log / Schedule Log / Cancel Log /
BLOCKS marker lines excluded (those already sit outside dedicated
pomodoro Task Links).

🍅 is a close marker, not an eligibility test. Older sessions and
review-only strikes would disappear if attribution required 🍅.

**A7. Unlinked closed sessions stay in the total and out of the pies.
(honesty)**

389 closed sessions have no dedicated Task Links. They still count in
`worked`. They contribute `(unnamed)` to theme parts when they have no
` — NAME`. They contribute nothing to `project` / `area` (omit the key,
or a single `(unlinked)` if the renderer needs a complete partition).
Guessing a home from the theme string (MEMORY → sase_memory) is a
second, lossy model. Do not build it.

**A8. Naming writes, if any, are phase 2 and unnamed-only. (when)**

The user asked how / when / what to label. The honest answer is that
*stats* should label at read time, always, from surviving links. *The
daily note* should gain a name only when all of these hold:

- the row is still open or we are inside the `=x` write
- it has no selectable name
- after fold there is exactly one non-exempt home
- the home has a typeable ALL-CAPS spelling (see A9)

Moments that fail that test:

| Moment | Why a write is the wrong move |
| --- | --- |
| Session start (`=`, `=#NAME`) | often zero links; too early |
| First link on a *named* row | would clobber BLOG / HACK / MEMORY |
| Second distinct home linked | would need a composite theme |
| Historical closed rows | rewrite storm, git noise, no benefit over read-time |
| GTD rows | exempt; `review_time` already owns them |

Phase 2 can call the existing `bob capture-pomodoro-name` from close or
from the first link. That command already refuses a selectable name,
ASCII-uppercases, and is the write half of `@route:id#` completion. Do
not add a second writer.

**A9. Auto-names, if they happen, need a display spelling. (what)**

Project stems are not pomodoro names. `job_2026_apply_29` must not
become ` — JOB 2026 APPLY 29`. `dev_plex_hack_patch` is worse. Themes
Bryan actually types are short: JOB, HACK, ATHENA, BLOG, PYPI.

If phase 2 writes names, add an optional `pomodoro_name: JOB` on the
*home* note, grammar-identical to capture-pomodoro-name. Absent that,
phase 2 simply does not write. Stats parts use the note stem (`sase`,
`bob`, `job_2026_apply_29`) so they wikilink.

**A10. Task metrics get the same `project` / `area` parts. (one language)**

`done` / `created` / `dropped` already emit `kind` and `note` parts, and
already honor `in:` against residence plus `parent_ancestors`. Adding
the same folded `project` / `area` parts makes the Stats page one
filing system: time and throughput both slice by sase / bob / job.
Without this, Worked-by-project and Done-by-path would disagree.

**A11. `in:` on pomodoro metrics is the ancestry filter; fold is the pie
label. (two knobs)**

Task metrics already treat `in: [sase]` as "this note or an ancestor".
Pomodoro metrics should grow the same `in:` / `exclude_in` (or reuse
`in` plus `exclude_themes`-style `exclude_in`). That filter includes
descendants whether or not anyone folded.

`stats_fold` only changes the *parts key*. Unfoldered, a
`sase_blog` session is a `sase_blog` slice that still matches
`in: [sase]`. Folded, it is a `sase` slice. Bryan's docs example
`sase_time: { kind: pomodoro, themes: [SASE] }` would keep missing
MEMORY- and BLOG-titled sase work; the replacement is `in: [sase]`.
Live `config.yml` has no `stats:` block today, so this is a docs and
catalog change, not a migration of custom metrics.

**A12. Render every parts dimension. The current CLI shows only the
BTreeMap's first key. (compat)**

`stats/render.rs` `parts_line` does `parts_summary.iter().next()`.
Pomodoro reports today have a single key `theme`. Adding `area` and
`project` would make `area` win alphabetically and *hide* the theme
line. The plugin copy in `docs/stats.md` similarly "shows the supplied
theme breakdown".

v1 must print one parts line per dimension, in a stable order:
`theme`, then `project`, then `area`, then `kind` / `note` / … Collapse
top-five-plus-`other` must apply to `project` and `area` the same way
it already applies to `theme` and `note`.

---

## 3. How, when, and what to label

This is the part the request asked to think hard about.

### Three labels, one row

| Label | Owner | When it exists | What it is for |
| --- | --- | --- | --- |
| Theme (` — BLOG`) | Bryan | when he names the row | plan cap, `#NAME`, session title, `review_time` |
| Project (folded stem) | Bob, derived | when a closed row has a resolvable non-exempt dedicated link | `dash_stats` Worked pie, `in:` filters |
| Area (area ancestor) | Bob, derived | same, walking `parent:` until `type: area` | coarser pie (dev / job / gtd / cash / …) |

A row may have a theme and no project (GTD, or unlinked work). A row
may have a project and theme `(unnamed)` (645 historical sessions).
Both are valid.

### Resolution algorithm (the whole v1 spec)

For each closed pomodoro on a canonical daily note:

1. Collect dedicated child Task Links (A6). Drop the daily `^gtd` link.
2. If the row's name components are all `plan.exempt`, stop (A4).
3. For each link, resolve the path (exact vault-relative, then unique
   basename; same rules as Today). Map `done/<stem>_done.md` to
   `<stem>.md`. Unresolved links are skipped; if any link failed and
   others succeeded, the day's quality is `partial`.
4. From the source path, walk `parent:` (already in `StatsIndex.parent_of`,
   cycle-safe) until a `type: project` or `type: area` note. Ref notes
   contribute their parent home. Inbox notes are areas and keep their
   own stem in v1 (`mac_inbox`, `gkeep_inbox`, `inbox`).
5. Walk from that home toward the root. The highest ancestor with
   `stats_fold: children` (or whose fold-list includes this home) is
   the project label. Otherwise the home itself is the project label.
6. The area label is the nearest `type: area` ancestor of that project
   label (or the home itself if it is an area). sase → `dev`. bob →
   `gtd`. `job_2026_apply_29` → `job`. `dev_plex_hack_patch` → `dev`.
7. Split the row's minutes across unique project labels by link weight
   (A5). Independently split the same minutes across unique area
   labels. Each dimension sums to the row.

Open pomodoros never enter `worked`; they may drive a live chip in
phase 2.

### What the human sees

**Daily note (v1):** unchanged. BLOG stays BLOG.

**`bob stats show worked`:** two extra parts lines, hue-matched to the
metric:

```text
worked    5h 00m/day
 theme    GTD 29h 16m 21%  ·  BOB 22h 20m 16%  ·  JOB 13h 55m 10%  ·  SASE 13h 45m 10%  ·  other 53h 06m 39%
 project  sase 38h …  ·  bob 18h …  ·  job_2026_apply_29 …  ·  dev_plex_hack_patch …  ·  other …
 area     dev …  ·  gtd …  ·  job …  ·  other …
```

(The project/area numbers above are illustrative; v1's first golden
pass must hand-compute them the way M1–M17 were hand-computed.)

**`dash_stats.md`:** the Worked focus chart defaults to **project**
stacks, colored by **area**. Theme remains one click away on the same
report (a Theme / Project / Area segmented control, view-only, no
reload). Hover copy names both:

```text
25m  ·  sase  ·  area dev  ·  titled BLOG
```

That sentence is the beauty constraint. One column, three facts, no
new page.

**Phase 2 chip (plugin, display-only):** a muted stem after the name,
using the same half-ring visual family as the In Progress Task Link
mark, never written into Markdown.

### What not to label

- `^prj` links label as their project note (the `^prj` line *is* the
  project). Fine.
- Depends-On / BLOCKS / Sub-projects children of a *task* never appear
  as pomodoro Task Links; scanners already skip those marker lines.
- Inventory labels (LATER, MISC, NEW FEATURES) remain themes. If such a
  row has links, residence still attributes. The inventory lint does
  not change.
- Reference notes do not become their own project slices; they walk to
  the parent area/project, then fold.

---

## 4. Recommended solution

### v1 — Residence parts (ship this)

**Engine (`src/native/stats/`)**

- Extend `PomodoroSession` with `links: Vec<PomodoroLink>` collected
  during the existing daily-note scan (no second vault pass).
- Reuse `parent_of`, `parent_ancestors`, archive mapping, and
  `NoteIndex`.
- Parse `stats_fold` next to `ready_cap` in the project/area
  frontmatter pass. Store `fold_of: BTreeMap<String, String>` from
  child source path to folding ancestor.
- Emit `parts["project"]` and `parts["area"]` from `evaluate_pomodoros`.
  Extend `evaluate_tasks` the same way so Done/Created share the grain.
- Collapse `project` and `area` to top five plus `other`.
- Accept `in:` / `exclude_in` on pomodoro specs, ancestry-aware, same
  matcher as task `in:`.
- Keep `themes` / `exclude_themes` for `review_time`.
- Golden vectors: folded sase child, archive `done/sase_done`, GTD-only
  skip, GTD+BOB composite, mixed bob+sase after fold, unresolved link
  → `partial`, cycle in `parent:`, unnamed linked session, unlinked
  named session, area-resident task (job.md), ref parented to
  sase_blog.

**Config / vault**

```yaml
# ~/bob/sase.md frontmatter
stats_fold: children
```

No `stats:` change is required in `~/.config/bob/config.yml` for v1.
Built-in `worked` and `sessions` grow parts. `review_time` is unchanged.

**CLI / schema-1**

- Additive parts keys. Older schema-1 consumers that only read `theme`
  keep working if they key by name; the CLI and plugin must iterate all
  dimensions in the order in A12.
- `bob stats show worked` prints three parts lines.
- Help: `bob stats -h` stays a Daily workflow command; no new
  subcommand. Filters, if exposed, are metric parameters, not a new
  noun.

**Obsidian**

- `bob-stats` context panel for pomodoro metrics: default Project
  breakdown, Theme and Area as siblings. The plugin still draws only
  what JSON supplies.
- Preview matrix (`scripts/preview-stats-block.cjs`) gains a fixture
  with three dimensions and long stems (`job_2026_apply_29`).

**Docs**

- `docs/stats.md`: define residence parts, fold, GTD skip, link
  collector, `in:` on pomodoro metrics. Update the "Later and rejected"
  list: rejected "rewrite pomodoro names from homes"; later "unnamed
  fill" and "display chip".
- `docs/projects.md`: document `stats_fold` next to `parent` and
  `project_name_aliases`.
- `docs/plan.md`: one sentence that themes remain the plan-budget
  atom and are not derived from Task Links.

**Performance**

The 2026-10-11 stats budget was ~370 ms for a full vault pass, already
over the original 300 ms target, dominated by Markdown. Attribution is
CPU on data the daily scan already has (~1k closed sessions, ~107
unique targets). Keep it inside the existing pass. Do not add a cache
file; that would violate the engine principle.

### v1 non-goals

- Rewriting historical ` — NAME` tails.
- Grouping the daily Pomodoros section by project (the ledger is
  chronological; `^group-poms-by-prj` as a visual regroup is a
  different feature).
- Folding bob.md or job.md. Recommend sase only; mention bob as a
  later candidate (123 folded-bob sessions vs a handful of
  `bob_projects` / `bob_gtd`). job campaigns should stay distinct.
- A `sase project stats` CLI. That in-progress sase.md task
  (`^sase-project-stats`) is about agent/model attribution inside SASE,
  a different product.

### v2 — Unnamed fill + chip (only after v1 feels true)

- On `=x`, if the closed row is unnamed and the folded home is unique
  and has `pomodoro_name:`, call `capture-pomodoro-name`.
- Plugin chip on open rows, display-only, same resolver as stats
  (Rust remains the authority; the plugin already mirrors plan-budget
  in JS — do not grow a third copy; either call `bob stats` for today
  or share the JS parent-walk already used for project blocking).
- `stats_fold_except:` if sase_blog must stand apart.

### Why this is the beautiful one

The failure mode of the original plan is a ledger of SASE, SASE, SASE,
BOB, SASE, with the 5-theme cap screaming and MEMORY WEBS gone. The
failure mode of doing nothing is a Stats page that reports 10% SASE
and 39% other while 582 links point at `done/sase_done`.

The design that survives both is the one Bob already uses for Today:
the ledger holds evidence, readers name the fact, writers change
inputs. Themes remain a handwriting. Homes become a chart.

---

## 5. Implementation sketch (for the plan that follows this research)

1. Spec the collector and fold in `docs/stats.md` with conformance
   vectors in `tests/fixtures/stats/` (hand-computed, M-table style).
2. Index links and `stats_fold` in `stats/index.rs`; evaluate in
   `stats/metrics.rs`; collapse in `stats/series.rs`; print every
   dimension in `stats/render.rs`.
3. Extend the plugin context panel and the preview fixtures. Do not
   let the plugin recompute homes.
4. Set `stats_fold: children` on `~/bob/sase.md` in the same change
   that ships the reader, so the first real `dash_stats` open shows
   sase as one slice.
5. Redefine the docs example `sase_time` to `in: [sase]`. Leave live
   config alone (it has no `stats:` block).
6. Hold phase-2 naming until v1's project pie has been stared at for a
   week. If Bryan still wants BLOG rows renamed, the unnamed-fill path
   is a small call into an existing command.

---

## 6. Risks

- **Partial history.** Unlinked sessions (389) and deleted tasks
  vanish from project pies. Quality stays honest: totals include them,
  parts do not pretend.
- **GTD skip vs "I did sase during review".** A4 will under-count
  sase if Bryan routinely files real work under a GTD title. Today's
  ledger suggests that is review, and `review_time` already tracks it.
  Reopen A4 if the first live pie feels low.
- **Renderer compat.** A12 is load-bearing. Ship CLI + plugin in one
  cut so `area` cannot steal the only parts line.
- **Fold too wide.** sase_blog-as-product may later want its own
  slice. That is `stats_fold_except`, v2, after looking at the pie.
- **JS/Rust drift.** Parent resolution and archive mapping already
  exist on both sides for other features. Stats v1 can stay Rust-only
  (CLI + `bob-stats` subprocess). A phase-2 chip is the moment a
  second implementation would appear; prefer a bob call.
- **Inbox noise.** v1 will show `mac_inbox` if those links exist.
  Fold later if it shows up.

---

## 7. Evidence (vault and code, 2026-10-18)

- Live `bob stats show worked -r 4w`: theme parts GTD 21%, BOB 16%,
  JOB 10%, SASE 10%, READ 4%, other 39%; headline 5h 00m/day median.
- 144 dailies, 445 named closed / 645 unnamed closed / 787 linked /
  209 mixed-note / 107 unique targets; `done/sase_done` 582,
  `done/bob_done` 168.
- After a sase descendant fold: 562 sase-present sessions, 123 bob, 69
  still mixed, 389 unlinked.
- `sase.md`: `parent: "[[dev]]"`, `type: "[[project]]"`, `status: wip`,
  60 direct project children, 23 wip. Sub-projects line already lists
  the fold set.
- `bob.md` Next: `[*] Group pomodoros by areas/projects instead of
  themes! ^group-poms-by-prj` (created 2026-10-18), currently queued
  under the open BOB pomodoro.
- `dash_stats.md`: 16 lines, empty `bob-stats` fence, parent `[[dash]]`.
- `~/.config/bob/config.yml` `plan:`: `max_themes: 5`, `exempt: [GTD]`,
  `inventory_labels: [LATER, MISC, NEW FEATURES]`. No `stats:` block.
- Engine: `PomodoroSession` stores `name` / minutes / line only
  (`src/native/stats/index.rs`); `evaluate_pomodoros` splits on `+`
  in the name (`src/native/stats/metrics.rs`). `parent_of` already
  exists for task `in:`. Archive map already exists.
- Decisions that this design rhymes with:
  `today-is-read-from-the-ledger`, stats "derive at read time",
  `ready_cap` as the per-note override pattern,
  `subprojects-inherit-project-blocking` for the parent walk.

---

## Recommended decision

Approve v1 as **residence parts + `stats_fold: children` on sase.md +
Theme/Project/Area rendering**. Treat auto-renaming of pomodoros as a
rejected v1 requirement, with unnamed fill parked as v2. Keep themes as
the daily-plan handwriting they already are.

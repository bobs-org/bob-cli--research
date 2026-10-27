# Work-kind pomodoro themes: 6-month audit and recommended set

Swarm: `mus` report. Researched independently; no current-swarm peer report
(`__cdx`, `__cld`, `__grk`, `__gem`) was located, opened, or consulted.
Shared input used: the prior six-theme review
(`pomodoro_six_theme_review/pomodoro_six_theme_review.md`), the live vault via
`bob themes`, `bob stats`, `bob plan`, and `bob query` attempts, plus
`docs/pomodoro-themes.md` and SASE memory (`decisions:pomodoro-theme-is-one-component`,
`glossary:pomodoro-theme`, `glossary:pomodoro`,
`decisions:theme-hide-is-recent-only`, `decisions:task-lanes-are-sticky`,
`decisions:today-is-read-from-the-ledger`, `decisions:review-walk-is-tiered`).

Research question: audit the last ~6 months of actual work and recommend a set
of pomodoro themes that name what *kind* of work a session contains (e.g.
reading, building, fixing) instead of what the work is *for*. Evaluate the
proposed renames GTD to PLAN and HOME to CHORE, keep or drop READ/BUILD/FIX,
and name whatever else the work actually needs.

## Bottom line

Adopt six work-kind themes, one exempt and five counted:

- **PLAN** (renamed from GTD, stays exempt and muted) — defining work: the
  morning review, triage, inbox, prune, and planning itself.
- **BUILD** (keep) — producing new capability: features, new commands,
  migrations, spikes that land.
- **FIX** (keep, widened to repair plus ops/toil) — restoring broken behavior
  and running deliberate maintenance: bug repair, agent restarts, remote
  cleanup, re-auth, outages.
- **READ** (keep) — understanding or deciding from references or agent
  reports: papers, manuals, reference tasks, code review, research reports.
- **WRITE** (restore) — producing prose: posts, docs, notes, CV and job
  letters. This is the one missing piece. It was folded into JOB on Oct 26;
  under a work-kind scheme it must come back.
- **CHORE** (renamed from HOME) — a scheduled personal-upkeep batch: money,
  house tech, care, and admin. Never an all-day placeholder.

Retire **JOB**. It is the only purpose theme left, and it is exactly what the
new scheme removes. Its October minutes decompose cleanly into READ (job-fit
references, Stripe guide), WRITE (CV, LinkedIn, launch post), CHORE/ADMIN
(submissions, scheduling), and a little BUILD (s0-spike). Track "time on the
job hunt" through homes (`job.md` area, `job_2026_apply_29`, `sase_blog`
root parent), not through the theme slot. That is the Toggl rule the prior
review cites: homes carry the deliverable, the theme slot carries the one
cross-cutting activity.

Support both renames with conditions. GTD to PLAN is sound but needs a config
change the rename alone does not do. HOME to CHORE is sound and also fixes
the collision between HOME-the-theme and home-the-attribution, but only with
a batch rule, because HOME has never been worked under its own name.

Do not mint anything else as a standing theme: no ADMIN separate from CHORE,
no MEET, no LEARN separate from READ, no DRIFT/SHIT, no REMOTE, no MEMORY,
no TOOL, no GOALS, no RESEARCH separate from READ, and no SASE/BOB-style
project nouns. Set `plan.max_themes` to 3 (`strict: false`) so the cap can
fire again, and pin every live theme before any merge rename.

## Method and limits

- Window: Apr 27 – Oct 26 (183 days) for `bob stats`, plus a ledger parse of
  canonical daily notes `2026/20260427.md`–`2026/20261026.md`. Today Oct 27 is
  cited separately from `bob plan`.
- Two independent totals agree: `bob stats show worked` reports 40755 minutes
  (679h 15m) with a median of 4h 28m/day over 152 days with data; a direct
  ledger parse of `## Pomodoros` column-0 rows counts 1144 closed sessions and
  39650 minutes (660.8h). The ~2.7% gap is time-range estimation and partial
  weeks. Both put the scale at ~660–680 hours.
- History was rewritten on Oct 26 (BOB and VIBE into BUILD, PYPI into READ,
  BLOG and WRITE into JOB, HACK into HOME, 71 hides). Every pre-Oct-26 minute
  under those names was chosen under a different name. Treat project-to-theme
  alignment near Oct as partly constructed.
- Homes are derived from today's note tree and can shift on re-run.
- Recorded time is not a life log. Unlogged care, errands, and work do not
  appear. A theme's absence is not evidence of neglect.
- Composites (`GTD + BUILD`) are rare (~1.3% of sessions) and split evenly.
- `days used` counts open plans too; a theme can recur without completed work.
- `bob query` Dataview probes were attempted per the `bob_query` skill (skill
  use logged). Folder-scoped probes returned path-only rows; tag-scoped probes
  returned empty tables against this vault's task shape, so the quantitative
  audit rests on `bob stats`, `bob themes`, `bob plan`, and the ledger parse,
  corroborated against each other. No vault files were modified.

## What the last 6 months actually hold

Monthly `worked` minutes (theme parts in parentheses):

- May (partial, week of May 25): 14h 45m, all `(unnamed)`.
- June: 128h 25m, all `(unnamed)`. Top projects: `sase.md`, `bob.md`,
  `@review:GTD`, `@unlinked`.
- July: 118h 25m, all `(unnamed)`. Top projects: `sase.md`, `@review:GTD`,
  `bob.md`.
- August: 159h, `(unnamed)` 8530 of ~9540 min. First named themes appear:
  MEMORY 310, MEMORY WEBS 135, PLAN MEMORY 100, GTD 85, AUDIT MEMORY 75,
  BUILD 73, PAGER 60. Top projects: `@review:GTD` 3675, `sase.md` 1905,
  `bob.md` 741.
- September: 146h 40m. GTD 1641, SHIT 795, REMOTE 675, SASE 590, BUILD 535,
  TOOL 405, GOALS 315, TOOLS 240, PROJECTS 235, CAPTURE 210, FIXES 195.
  Top projects: `sase.md` 3922, `@review:GTD` 1639, `bob.md` 820.
- October (1–26): 112h. GTD 2275, BUILD 1355, JOB 1315, READ 645, SASE 235,
  SASE V18 220, FIX 150, LISTEN 130. Top projects: `@review:GTD` 2263,
  `bob.md` 1379, `sase.md` 917, `sase_blog` 452, `sase_pypi_releases` 388,
  `job_2026_apply_29` 299.

Six-month ledger parse (Apr 27 – Oct 26, closed sessions only):

- Sessions: `(unnamed)` 613, GTD 133, BUILD 89, JOB 88, READ 44, SASE 33,
  MEMORY 19, REMOTE 18, SHIT 16, GOALS 14, SASE V18 12, MEMORY WEBS 10,
  TOOL 10, HOME 10, ATHENA 8, FIX 7.
- Minutes: `(unnamed)` 23140 (58.4%), GTD 3870 (9.8%), BUILD 1895 (4.8%),
  JOB 1315 (3.3%), SASE 825, SHIT 820, READ 800, REMOTE 675, TOOL 405,
  MEMORY 380, GOALS 315, plus a long tail under 250 each.
- Top linked notes by child-bullet Task Links: `sase_done` 776, `bob_done`
  318, `sase` 43, `sase_blog_done` 32, `job_2026_apply_29_done` 29,
  `sase_pypi_releases` 27. Tool work (sase plus bob) is the bulk of linked
  work across the whole window, not just October.

Catalog today (`bob themes list -f json`, 0.4.0): 76 known, 70 hidden, 6
visible, 5 counted today. Visible: GTD (exempt, muted, 54 days, 142 entries),
BUILD (yellow hash, 30 days, 97 entries), READ (green hash, 16 days, 47
entries), HOME (violet hash, 11 days, 11 entries), FIX (blue hash, 5 days, 9
entries), JOB (aqua area, 19 days, 88 entries). Hidden tail includes SASE (14
days, 33 entries, last Oct 17), MEMORY (8 days), REMOTE (6 days), SHIT (13
days, last Oct 9), RESEARCH, TOOL/TOOLS, GOALS, VERIFY, FIXES, and one-day
names from Oct 8 (BEADS, FIRE, FIX-APOLLO, HERMES, JITUX, RESTART MAC).

Today's plan (Oct 27): READ, BUILD, FIX, HOME open; GTD closed; JOB absent
today but last used Oct 26. Median BUILD sessions are short agent dispatches
("apollo agent", "research on athena", 5–10 min), not long maker blocks.
October READ sessions are mostly agent research reports for current projects
plus job-fit references. JOB sessions mix reading (45% of its task-link
bullets point at `^ref-*` tasks), the launch post, applications, CV/LinkedIn,
and one dev re-auth task.

## What each current theme really is

- GTD is review plus routine plus operations. `gtd_daily.md` PRE chores are
  planning chores (calendar, email, Keep import), operational toil ("Clean up
  SASE agents on athena and apollo"), and personal routine (teeth, fish oil
  and L-tyrosine, weather, stretches). The ledger label pulls all three into
  `review_time`. The exempt-and-muted treatment is right; the contents are
  too wide.
- BUILD is mostly sase/bob feature work plus agent dispatch. 99% dev-area in
  October. Short bursts (median run ~25 min when joined at 15-min gaps; only
  one 90-min run in two months). The theme is sound; the maker-block advice
  does not transfer to dispatch work.
- JOB is a purpose, not a kind. In October it spans the `job` area (54%) and
  the `dev` area (43%): `sase_blog` 30%, `job_2026_apply_29` 22%, `job` 14%,
  CV 9%. Reading for the job counts as JOB while the same reading for tools
  counts as READ. Nothing decides between them except habit.
- READ is understanding work, but leaks. October READ holds agent reports,
  `sase_pypi_releases` research, and job-fit reading on some days but not
  others. The activity is coherent; the boundary with JOB is not.
- FIX is the planned-vs-unplanned split, starved. Only 7 sessions and 210
  minutes in 6 months under the exact name, while REMOTE (675), FIXES (195),
  agent cleanup (inside GTD), restarts, re-auth, and outage work carry the
  same kind elsewhere. Keep it and feed it; do not leave it open "just in
  case".
- HOME is a rollover list, not a work block. 11 rows (Oct 10, 17–27); the
  only closed one is the renamed HACK session on
  `dev_plex_hack_patch#^prj`; every typed HOME is an untimed `()` placeholder;
  "sell-stocks-now" rolled through nine placeholders and the UPS battery
  reference through eight. Its tasks live in `dev`, `dev_plex_hack_patch`,
  and `love`. Zero evidence of HOME as a worked kind.
- Legacy names are already gone from practice (0% of minutes since Oct 19)
  and age out of 4-week views by mid-November. SHIT ("untracked bullshit",
  16 sessions) has not been used since Oct 9; unlinked time fell to ≤0.4
  h/week after Oct 1. REMOTE, MEMORY/WEBS, TOOL/TOOLS, GOALS, RESEARCH,
  VERIFY, SASE, and the Oct-8 one-day names are project nouns, places, or
  reading/building by another name.

## Evaluating the proposed renames

GTD to PLAN: support, with one config edit. PLAN names the activity
(defining work: review, triage, planning) instead of the methodology, which
is exactly the work-kind direction. It also matches Allen's split the prior
review cites: defining work versus doing work. Keep the exempt-and-muted
treatment, or the rename breaks the cap exemption. That means renaming the
ledger NAME is not enough: `plan.exempt` in `~/.config/bob/config.yml`
(chezmoi source) must move from `[GTD]` to `[PLAN]` in the same change, and
the Morning review text, `docs/plan.md` references to the exempt name, and
any `plan.max_themes` copy must agree. Do not rename the `#gtd` tags, the
`gtd.md` area, `gtd_daily.md`, or the PRE/POST checklist: the tiered walk
(`decisions:review-walk-is-tiered`) keys on exact `#gtd` plus `#pre`/`#post`
tokens, and `decisions:today-is-read-from-the-ledger` keys Today on ledger
links, not on the theme name. Both are safe under a theme-only rename.
Pin PLAN (or GTD before the rename) first so the rename target has journal
state; otherwise a later merge into it can hide it (the verified
`theme.rename` state-transfer hazard).

HOME to CHORE: support, with a batch rule. CHORE names a kind of work (a
timed upkeep batch) where HOME names a place and collides with Bob's
"home" attribution term (the note tree a session's minutes attribute to).
Keep the violet hue by pinning before the rename so the color survives the
key change. The rename alone does not fix the behavior: HOME's problem is
not spelling but untimed placeholders that take a theme slot, add attention
residue, and teach the plan as optional. Open CHORE only with a time (an
`## Events` line or a weekly two-Pomodoro batch); on other days its tasks
wait in NEXT or the tickler. Decide "sell-stocks-now" once: do it, schedule
it, or drop the "now".

READ, BUILD, FIX stay: support. All three describe real, frequent kinds with
different done-conditions (decision made, increment accepted, failure
resolved). Narrow each per the codebook below: docs read in passing while
building stays BUILD; reading for a career milestone stays READ under a
work-kind scheme only if the milestone question is not tracked elsewhere —
see the JOB discussion. Planned refactors are BUILD, not FIX. Agent cleanup
moves from PLAN to FIX.

JOB retires; WRITE returns. This is the one structural change the
work-kind direction requires. The prior review kept JOB because the WRITE
into JOB fold was one day old and deliberate and because JOB is the only
cross-area view of job-hunt time. Both points stand, but both assume the
hybrid purpose-plus-mode vocabulary. Under kinds-only, JOB has no meaning:
the same verbs (read, write, submit, schedule) appear inside and outside the
job hunt, and the theme slot cannot answer two questions at once. The
replacement for "job-hunt time" is homes: the `job` area, the
`job_2026_apply_29` / `job_2026` / CV projects, and the `sase_blog` root
parent already separate blog time without a theme. The Day strip root-parent
lane renders that split today. Cost: one habit change at capture time and
the loss of a single JOB number in Stats theme views. Benefit: READ, WRITE,
and CHORE numbers become trustworthy, which is the question the theme lane
can actually answer.

WRITE scope: prose production with a bounded-done condition (section sent,
post published, doc accepted, letter tailored). That covers the launch post,
blog review tasks, S0 spikes that are writing, docs, CV/LinkedIn/cover
letters, and reading notes that turn into a decision memo. It does not cover
code, commands, or migrations (BUILD), nor understanding without output
(READ). Volume justifies the slot: `sase_blog` alone is 452 minutes in
October, plus job docs, plus the 17 BLOG sessions relabeled in the cleanup.
Without WRITE, that prose falls back into BUILD (wrong kind) or JOB (wrong
facet).

## Proposed codebook (six lines plus precedence)

Ask the block's kind first and only. Decide before starting; do not relabel
mid-session because the verb changed. Homes answer "what is it for".

1. PLAN: running the review or planning process itself.
2. BUILD: producing new capability.
3. FIX: restoring broken behavior or running chosen maintenance.
4. READ: understanding or deciding from references or agent reports.
5. WRITE: producing prose to a bounded done state.
6. CHORE: a scheduled personal-upkeep batch.

- PLAN — Use when: daily walk, inbox, triage, planning, weekly prune. Not
  when: agent cleanup (FIX); building features (BUILD); personal routine
  untimed. Done when: review pass done; next commitments clear.
- BUILD — Use when: planned bob and SASE work including agent dispatch; new
  commands, features, migrations, spikes that land. Not when: repairs (FIX);
  prose (WRITE); understanding without output (READ). Done when: planned
  increment reaches acceptance.
- FIX — Use when: restoring broken agents, bugs, outages, re-auth; deliberate
  operational upkeep (restarts, remote cleanup, battery/plex maintenance).
  Not when: planned refactors (BUILD). Done when: failure resolved or cause
  isolated with a next step. Open only when a repair is actually queued.
- READ — Use when: reading references or agent reports to understand or
  decide, including job-fit references and code review. Not when: docs read
  in passing while building (BUILD); prose production (WRITE). Done when:
  decision made or next action written.
- WRITE — Use when: posts, docs, notes, CV/letters/LinkedIn, launch-post
  sections. Not when: code or tool behavior (BUILD); reading without output
  (READ); applications submitted or interviews scheduled (CHORE batch).
  Done when: bounded prose piece done.
- CHORE — Use when: a timed batch of upkeep: money, house tech, care, admin
  (email/calendar/Keep triage overflow, submissions, scheduling). Not when:
  an all-day reminder; review (PLAN); repair (FIX). Done when: one
  obligation resolved or the planned batch finished.

Precedence (kinds-only, no purpose slot): PLAN first (if the block *is* the
review process), then CHORE if it is a scheduled upkeep batch, then
FIX/READ/WRITE/BUILD by the result sought: broken-to-fixed is FIX,
understand-to-decide is READ, blank-to-prose is WRITE, missing-to-built is
BUILD. Reading done *for* the job hunt is READ; the job-hunt attribution
comes from the linked note, not the theme.

## Migration, cap, and guardrails

1. Pin before any rename (`bob themes color PLAN ...`, `CHORE ...`, `BUILD
   ...`, `FIX ...`, `READ ...`, `WRITE ...`). Pins create journal state on
   each target so a later `--merge` cannot hide it or move a stale pin onto
   it. Suggested hues: PLAN stays muted via exempt (no pin color needed);
   BUILD blue (matches the dev/bob root-parent lane), FIX red (conventional
   broken, frees blue), READ green (current, anchored), CHORE violet
   (current HOME hue, anchored), WRITE aqua or orange by taste after checking
   `bob themes list` collision hints; JOB already wears area aqua and needs
   no pin once retired.
2. Rename GTD to PLAN and HOME to CHORE with dry runs first
   (`bob themes rename GTD PLAN -d -m`, `bob themes rename HOME CHORE -d
   -m`), then run with `-m`. Update `plan.exempt: [GTD]` to `[PLAN]` in the
   chezmoi source for `~/.config/bob/config.yml` in the same change; without
   this, PLAN counts against the cap and the Morning "≤3 themes" checklist
   disagrees with the budget again.
3. Restore WRITE as a fresh name (no history to merge; do not back-merge BLOG
   or JOB history into it). Retire JOB by habit, not by rewriting history:
   leave historical JOB tails alone (they age out of 4-week views), and from
   the cutover day forward choose READ/WRITE/CHORE/BUILD at capture time.
   Cancel or narrow `^delete-themes`: hiding already removes names from
   Recent per `decisions:theme-hide-is-recent-only`; real deletion would have
   to rewrite historical tails.
4. Make the cap mean something: set `plan.max_themes: 3`, keep `strict:
   false`. Five non-exempt names with a cap of 5 can never fire, and the
   checklist already says "≤3 themes". The median day actually works 3
   non-PLAN themes. If FIX plus READ plus BUILD tool days trip 3 constantly,
   use 4, never 5.
5. Keep `inventory_labels: [LATER, MISC, NEW FEATURES]` as storage, not
   themes. Keep SHIT retired: use it only retroactively for closed sessions
   that went sideways, never as an open plan, and only if unlinked time
   reappears. Keep REMOTE, MEMORY/WEBS, TOOL/TOOLS, GOALS, RESEARCH, VERIFY,
   CAPTURE, SERVICE, SASE, and project nouns hidden; their work already has a
   kind home above.
6. Add a 5-minute Monday check to the weekly prune: `bob themes list -a`,
   rename any non-codebook name into the six, hide it, or promote it with a
   codebook line; check `renamed_reappeared` and the PLAN and FIX shares.
   Mint rule: a new name needs three different days of use or it folds into
   the six.

## Questions only Bryan can answer

1. Does the WRITE into JOB fold still hold, or does the work-kind direction
   overrule it? The recommendation assumes kinds win and WRITE returns.
2. Do teeth, pills, stretches, and weather happen inside timed PLAN sessions
   or outside them? The audit cannot tell; keep them out of timed sessions
   if they are currently inside.
3. Is CHORE meant to book real time (a weekly batch) or to keep reminders
   visible? If the latter, it belongs in NEXT or the tickler, not the
   ledger.
4. Which review question matters more right now: "time on the job hunt" or
   "time reading/writing"? The single theme slot answers one cleanly under
   kinds-only; this report chooses reading/writing and recovers job-hunt
   time from homes.

## Evidence base and reproducibility

- `bob themes list -f json` and `bob themes list -a -f json` (0.4.0):
  76 known / 70 hidden / 6 visible; per-theme `first_used`, `last_used`,
  `days_used`, `entries`, hues and `hue_source`, collision hints.
- `bob stats show worked -r 2026-04-27..2026-10-26 -f json` and the monthly
  `-g month` split: totals, theme parts, project parts quoted above.
- `bob stats show worked -r 2026-05-01..2026-10-26 -g month -f json` and
  `sessions -r 2026-08-26..2026-10-26 -f json` for the Sep/Oct theme
  emergence.
- `bob plan -f json` (Oct 27): READ/BUILD/FIX/HOME open, GTD closed, JOB
  absent; `today_tasks` homes chip `job` vs `sase`.
- Ledger: `2026/20261027.md` and `2026/20261026.md` `## Pomodoros` sections
  (format `- [x] (**HHMM-HHMM** [t:: Nm]) — NAME` with tab-indented
  child Task Links); `gtd_daily.md` PRE/POST chores; `2026/202610*.md`
  HOME rows and `^ref-*` bullets.
- Docs and decisions: `docs/pomodoro-themes.md` PT1–PT10 (identity, catalog
  source `YYYY/YYYYMMDD.md` via `capture_pomodors::scan`, preferences
  journal `.bob/themes/<host>.jsonl`, hue rule, menus),
  `decisions:pomodoro-theme-is-one-component`,
  `decisions:theme-hide-is-recent-only`,
  `decisions:theme-hue-is-pin-exempt-area-hash`,
  `decisions:task-lanes-are-sticky`, `decisions:today-is-read-from-the-ledger`,
  `decisions:review-walk-is-tiered`.
- Prior synthesis read as context only:
  `pomodoro_six_theme_review/pomodoro_six_theme_review.md` (Oct 26 cleanup
  timeline, six-name minutes table, JOB-reading overlap, HOME rollover,
  GTD inflation, cap mismatch, merge hazard with `bob themes rename FIXES
  FIX -d -m`).

Repro (read-only):

```sh
bob themes list -a -f json
bob plan -f json
bob stats show worked -r 2026-04-27..2026-10-26 -g month -f json
bob stats show worked -r 2026-09-01..2026-10-26 -g day -f json
bob themes rename GTD PLAN -d -m    # dry run only
bob themes rename HOME CHORE -d -m  # dry run only
```

## Recommended set (final)

Use these six from now on. One exempt, five counted, cap 3:

PLAN (exempt, muted) · BUILD · FIX · READ · WRITE · CHORE.

Retire JOB; keep LATER, MISC, NEW FEATURES as inventory labels, not themes;
leave SHIT, REMOTE, MEMORY, TOOL, GOALS, RESEARCH, SASE, and project nouns
hidden. Pin live targets before any merge, move `plan.exempt` to `[PLAN]`
with the rename, and let homes — not themes — answer "what was it for".

# Why is PLAN exempt, and should it stay that way?

Checked **Wednesday, October 28, 2026 (evening, New York)** against bob-cli `687375eb`,
the live `~/bob` vault (`46729ba3`), and `~/.config/bob/config.yml`
(`plan.exempt: [PLAN]`, `max_themes: 3`, `max_links: 13`, `themes: PLAN: auto`).

**Question:** Why does Bob exempt the PLAN theme? PLAN is meant for any time Bryan needs
to plan more work for his day, not only for the GTD morning review. The open
`() — PLAN` entry linking `[[sase_blog#^s0-spike]]` in `2026/20261028.md` is one example.
Should PLAN stay exempt?

## Short answer

- **PLAN is exempt because it took over GTD's exemption.** On October 27,
  `bob themes rename GTD PLAN` and commit `f6287847` ("make PLAN the review theme") moved
  `plan.exempt` from `[GTD]` to `[PLAN]`. Nobody decided that *planning in general* should
  be exempt. The exemption was designed for the morning GTD ritual, and the name it
  applies to now covers more than that ritual.
- **That exemption had two original reasons, and both were about the ritual.**
  1. *Plan budget, September 29:* "Today is GTD plus at most 3 themes." The 3-theme cap
     was set from the roughly 3 planned themes a day Bryan actually works, not counting
     the daily review. GTD's only link was the `[[#^gtd]]` checklist row itself.
  2. *Stats homes, October 18:* "GTD sessions are review time." Without that rule, about
     20% of the day (the morning review) would be smeared into sase and bob through the
     tasks being dispatched.
- **"Exempt" is one config list that does about ten jobs.** Most of them still make sense
  for ad-hoc planning. The one that doesn't is in Stats. A session named only PLAN is
  **always** charged to the `PLAN review` bucket (gtd area, `@daily` root, labeled "GTD"
  in the Day Strip roots bar), and **its links never count**. So the 2 🍅 you planned for
  the blog spike will never appear under `sase_blog`.
- **Recommendation: keep PLAN in `plan.exempt`, but change what an all-PLAN session means
  in Stats.** Let the `^gtd` link decide what counts as review, and let a PLAN session's
  links decide everything else. Optionally, also count non-`^gtd` links under PLAN
  toward `max_links`. Details and the decisions you need to make are in
  [Recommendation](#recommendation).

## What "exempt" actually does today

`plan.exempt` is read by the plan budget, the homes resolver, the theme catalog,
capture, and the Obsidian/Mac mirrors. This is everything it changes for an entry named
only `PLAN`:

| # | Surface | Effect of exemption | Right for ad-hoc planning? |
| --- | --- | --- | --- |
| 1 | Theme budget (`bob plan`, capture, tmux, `bob-plan` block) | PLAN never counts toward `max_themes`, and `strict` never refuses a new PLAN entry (`plan_budget/mod.rs`, `preselect.rs`) | ✅ Planning is how you choose themes. It shouldn't use up one of the slots |
| 2 | Highlight | The ★ highlight is the first open **non-exempt** entry | ✅ Otherwise the morning PLAN entry would be the highlight every day |
| 3 | `duplicate_open_pomodoro_name` lint | Two open PLAN entries never trigger the lint | ✅ A morning review plus a placeholder PLAN for later is normal |
| 4 | Link budget | An all-exempt entry is "ignored for links too": **none** of its links count toward `max_links` | ⚠️ Partly. It is right for `[[#^gtd]]`, but it hides real commitments. Tonight `bob plan` says **1/13 links** while Today lists **2** tasks |
| 5 | Today | No effect. Dedicated links under PLAN still put tasks in Today | ✅ |
| 6 | Stats / homes (R4) | Every minute goes to `@review:PLAN`, and **its task links never attribute**. The `review_time` metric counts it | ❌ This is the mismatch (see below) |
| 7 | Hue | Muted `□` swatch and a gray pill, because `PLAN: auto` falls through to the exempt mute | ➖ A separate setting. A palette color in `themes:` overrides the mute without touching the exemption |
| 8 | Task theme writes (PT13) | Deliberately placing a task under PLAN never writes `[theme:: PLAN]`. `PLAN + BUILD` writes BUILD. The `^gtd` row's suggestion uses `exempt[0]` | ✅ One planning session about a task doesn't make it a planning task |
| 9 | Capture menu contract | Exempt components are ignored when matching "exact" entries, so `PLAN + BUILD` counts as exact for BUILD | ✅ |
| 10 | `bob themes rename` / `split` | Renaming an exempt theme is refused until config lists the new name. Split flags exempt targets as review time | ➖ Guard rails only |
| 11 | `^gtd` bridge | An unnamed session that links the day's `^gtd` row is review, named after `exempt[0]`. The bridge turns off when the list is empty | ✅ Ritual-specific, and it should stay that way |

Nine of the eleven effects either fit ad-hoc planning or don't matter. Row 6 is the real
conflict, and row 4 is a smaller leak.

## The October 28 example, as Bob sees it

```markdown
- [x] (**0630-0640** [t:: 10m]) — PLAN       ← 6 morning PLAN sessions, 90 min, each linking ~~[[#^gtd]]~~
	- 🍅 ~~[[#^gtd]]~~
…
- [ ] () — PLAN
	- [[sase_blog#^s0-spike]]               ← planning the blog's Wave 1, not the morning review
```

`bob plan` (live, tonight):

```text
  PLAN  1/3 themes - 1/13 links      TODAY 2 - PENDING 7/8 - NEXT 2/13
  ★ READ   ▶ 2045-2110  1 link
    PLAN   exempt       0 links
```

`bob plan -f json` forecasts the PLAN entry's homes as `PLAN review`: area `gtd.md`,
orange, `tasks: 0`. The `sase_blog` home disappears, even though `sase_blog.md` is a
`root: true` project under `sase` → `dev`. When this entry closes, its minutes will land
in `@review:PLAN` / `gtd` / `@daily`, next to the six morning sessions. That is correct
for the morning sessions. It is wrong for the blog spike.

## How we got here

1. **2026-09-29: `db89ee8a` added `plan.exempt` with the default `[GTD]`.** It came from
   `research:202609/bob_cli_2o_plan_budget_now_explained/bob_cli_2o_plan_budget_now_explained.md`
   and
   `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`.
   The rule: "Today is closed: **GTD plus at most 3 themes**." The cap of 3 matched the
   measured median of about 3 planned themes a day. GTD was the standing daily review
   that sits on top of those themes. The guidance for agent-blocked time was "if blocked
   on agents → next theme or GTD", so GTD already absorbed some dispatch work.
2. **2026-10-18: `9ec332c8` (homes resolver) reused the same list for Stats.** The
   reasoning, from
   `research:202610/pomodoro_area_project_attribution/pomodoro_area_project_attribution.md`:
   "Otherwise about 20% of time (morning review) gets smeared into sase and bob. This
   matches the plan budget's existing exempt rule." The report accepted a known cost:
   "21 of 99 GTD sessions since Aug 26 carried a live work link (12 h 50 m)… Those
   minutes count as review." The suggested workaround was to name such sessions
   `GTD + SASE`.
3. **2026-10-27: The work-kind theme research recommended GTD → PLAN, "keep exempt".**
   Source: `research:202610/work_kind_pomodoro_theme_set/work_kind_pomodoro_theme_set.md`.
   It **broadened** PLAN to mean "decide what to do and in what order", including
   "project scoping or roadmaps". It flagged the conflict and chose to accept it: "PLAN
   sessions about one project still count as review… about 10 hours in six months.
   Accepting it is cheaper than adding a second planning name."
4. **2026-10-27: `f6287847` shipped the rename** and added this line to
   `docs/pomodoro-homes.md` R4: "an all-PLAN named session is review even when it links
   project tasks."

So the exemption was tuned for a ritual and then applied to a broader name. The Stats
cost was judged small. No decision record covers R4 review sessions. The closest record,
`theme-hue-is-config-pin-exempt-area-hash`, only covers the hue mute.

## How much it matters

I scanned every daily ledger from 2026-04-27 to 2026-10-28 for closed sessions named only
`PLAN`. History before October 27 was renamed from GTD. The script approximates R3: it
counts block links on indented lines, struck links included, and de-duplicates by raw
target.

| Window | PLAN-only sessions | Minutes | Linked ≥1 non-`^gtd` task | Linked **no** `^gtd` row (pure ad-hoc planning) |
| --- | --- | --- | --- | --- |
| Apr 27 – Oct 28 | 144 | 4,140 (24% of 17,085 closed) | 77 sessions · 2,515 min | **21 sessions · 475 min (≈ 8 h)** |
| Oct 1 – Oct 28 | 94 | 2,510 (35% of 7,275) | 38 sessions · 1,120 min | **16 sessions · 300 min (5 h)** |

- **Ad-hoc planning is a recent habit, and it's growing.** 16 of the 21 pure-planning
  sessions happened in October: job reorganization (`job#^re-organize-job`,
  `collect-7-roles`), blog scoping (`sase_blog` `no-more-0-prj`, `review-tasks`), and
  `gtd#^themes-and-tasks`. You were already doing this under the GTD name before the
  rename made it natural.
- **Morning sessions also list tasks, but those are dispatches.** 56 sessions linked
  `^gtd` *plus* other tasks, such as agents launched during the walk. The homes research
  wanted to keep exactly these minutes in review.
- **The size depends on which rule you pick.** "PLAN links always decide" would move
  about **1,718 min** out of review over six months (802 min in October), which is the
  smear the homes research warned about. "The `^gtd` link decides" moves only the
  **475 min** of pure planning.
- **Every closed PLAN session had at least one link.** The "no links" edge case doesn't
  occur in practice.

My 24% is lower than the 27% (181 h) in the work-kind report. That report also counted
unnamed sessions bridged through `^gtd`. I counted only named PLAN sessions.

## Options

| Option | What changes | Gains | Costs |
| --- | --- | --- | --- |
| **A. Status quo** | Nothing | No work, and morning review stays cleanly bucketed | Project planning (≈ 5 h in October, mostly blog and job) shows up as "GTD" / gtd area and never as the project. Links under PLAN don't count toward `max_links`. The only workaround, `PLAN + WRITE`, gives half the minutes to WRITE and spends a theme slot |
| **B. Un-exempt PLAN** (`exempt: []`) | PLAN becomes an ordinary theme | Links decide homes. `[theme:: PLAN]` becomes writable | PLAN would use a theme slot on 27 of 28 October days, so the cap becomes "PLAN + 2" unless you raise it to 4, which weakens it on work days. The morning PLAN entry becomes the ★ highlight while it's open. Two open PLAN entries trigger the duplicate lint. Named PLAN sessions stop being review sessions, so morning minutes split across dispatched tasks (≈ 1,700 min smear) and only the `^gtd` share stays in review. The `^gtd` bridge and the "daily review" suggestion switch off. PLAN needs a color |
| **C. Split the name** (exempt `GTD`/`REVIEW` for the ritual, ordinary `PLAN` for everything else) | A second planning theme | Each name has a single meaning | The work-kind research rejected this ("cheaper than adding a second planning name"). It brings back a *purpose* name into a set of *kind* names, reverses a rename that landed yesterday, and still leaves history ambiguous. Mid-day planning would use a theme slot |
| **D. Keep PLAN exempt from the budget, and let `^gtd` decide review** *(recommended)* | R4: an all-exempt named session is review **only if** it links the day's `^gtd` row or has no dedicated links. Otherwise its links decide, as in any work session, and its **theme stays PLAN** | Themes say *what kind*, homes say *what for*. This is the design the work-kind set is built on, and PLAN is currently its only exception. Blog planning goes to `sase_blog`. Morning review stays whole. `review_time` measures the ritual, and the Stats theme dimension `PLAN` measures all planning | Code, docs, and a decision record (below). History re-attributes about 475 min. A morning session that links `^gtd` *and* a project task still counts entirely as review, the same as today |
| **D2. (add-on to D)** Count non-`^gtd` links under exempt entries | Budget: an exempt entry is still never a theme, the highlight, or a duplicate, but its links count except the `^gtd` row | Closes the loophole where tasks parked under PLAN never touch `max_links`. Tonight would read 2/13, matching Today = 2 | A second engine change (Rust plan budget plus the `bob-plan` JS mirror and its conformance examples). Open morning entries that list dispatches would count those links while they're open. That's honest, but new |

### What D would cost to build

- **Rust:** the `named_review` predicate in `attribute_session`
  (`src/native/pomodoro_homes/session.rs`). The per-link `^gtd` → review home for work
  sessions already exists (`resolve.rs`, `review_home`). Update the `review_time`
  description in `src/native/stats/registry.rs`.
- **Mirror:** the Obsidian ledger mirror in `bob-plugins` (`bob-ledger-tools` home
  chips) follows the shared vectors in `tests/fixtures/pomodoro_homes/vectors.json`.
  Add vectors for "PLAN without `^gtd` → links decide" and "PLAN with `^gtd` + task →
  review". Bob Mac Capture renders Bob's JSON and needs no change.
- **Docs:** `docs/pomodoro-homes.md` R4 (replace "even when it links project tasks"),
  `docs/stats.md` (`review_time`), `docs/plan.md` "Exempt entries" (D2 also touches
  "Links". Conformance example 2 still holds, because only `^gtd` sits under its PLAN
  entry), and
  `docs/concepts/today-and-the-pomodoro-ledger.md`.
- **Decision record:** `f6287847` deliberately chose a rule based on the session name,
  so the replacement needs a new decisions-web record, for example "PLAN Is Review Only
  With The ^gtd Link". Per the decisions conventions, it should cite this report and the
  October 18 and 27 reports.
- **Release note:** this is a Stats behavior change. The JSON shapes don't change, so
  under the release-train decision it isn't a `!` contract break, but it deserves a
  changelog line because past days will re-attribute.

## Recommendation

**Yes, keep PLAN exempt. Exemption is the right model for planning in the budget. But
stop letting the name override the links in Stats (option D).** The original reasons for
exemption still hold for any planning session. Planning picks themes, so it shouldn't
use up a theme slot, become the highlight, or trip the duplicate lint. What doesn't carry
over is the October 18 shortcut that charges every PLAN minute to review. That shortcut
assumed PLAN/GTD meant "the morning walk", and since October it often doesn't. The
`^gtd` link is a better signal of the ritual than the name, and it is already the signal
the unnamed-session bridge uses.

Decisions you need to make:

1. **Should planning use a theme slot?** I recommend **no**: keep PLAN in `plan.exempt`.
   If you say yes, you're choosing option B and should raise `max_themes` to 4. Accept
   that the cap then stops distinguishing "PLAN + 3" from four work themes.
2. **Where should project-planning minutes go in Stats?** I recommend **to the project**
   (option D). If one "PLAN review" bucket is fine with you, keep the status quo. It
   currently misfiles about 5 h a month, mostly blog and job work.
3. **What should `review_time` measure?** Under D it measures **the GTD ritual**, and
   the Stats theme dimension `PLAN` becomes your all-planning number. Under the status
   quo, `review_time` means "every session named PLAN". Pick the meaning you want the
   metric to have, then choose D or A to match.
4. **Should tasks planned under PLAN count toward `max_links`?** I recommend **yes,
   except `^gtd`** (D2). Otherwise PLAN becomes an uncapped parking spot, and Today can
   silently outgrow the link cap. This is low stakes, so it can ship later or not at all.
5. **Color (optional, independent of all the above).** Keep PLAN muted. The gray pill
   tells you "doesn't count against the cap". If you'd rather see planning in the Day
   Strip and Stats colors, set `themes: PLAN: orange` (or `aqua`). A configured color
   already beats the exempt mute without touching the exemption.
6. **Task theme stamping.** Keep the rule that placement under PLAN never writes
   `[theme:: PLAN]`. A genuinely planning-shaped task can still get PLAN through the
   Task Card or a note `theme:` default.

**One habit to adopt either way:** keep project planning in its **own** PLAN entry. Don't
link it inside a morning entry that also holds `[[#^gtd]]`. Under the status quo this
habit makes the work visible in the ledger. Under D it also makes the minutes land in the
right project.

**Watch item:** PLAN-only sessions went from 24% of closed time over six months to 35%
in October (job search plus blog). Exemption means the budget never pushes back on that. If the October
share holds through November, look at it in the Monday prune with the Stats theme view.

## Sources

- bob-cli `687375eb`: `src/native/config/plan.rs` (default `exempt: [PLAN]`),
  `src/native/plan_budget/mod.rs` (theme/link/highlight/duplicate handling),
  `src/native/pomodoro_homes/session.rs` (`attribute_session`, R4),
  `src/native/pomodoro_homes/resolve.rs` (`review_home`), `src/native/task_theme.rs`
  (`plan_theme_change`), `src/native/pomodoro_themes/{hue,preselect,suggest}.rs`.
- Docs: `docs/plan.md`, `docs/pomodoro-homes.md` (R4), `docs/pomodoro-themes.md`
  (PT5, PT13), `docs/stats.md` (`review_time`), `docs/develop/migration-notes.md`,
  `docs/concepts/today-and-the-pomodoro-ledger.md`.
- Commits: `db89ee8a` (plan config, `exempt: [GTD]`), `9ec332c8` (homes resolver),
  `f6287847` (PLAN becomes the review theme), `ec018a5b` (config-first hue).
- Research: `research:202609/bob_cli_2o_plan_budget_now_explained/bob_cli_2o_plan_budget_now_explained.md`,
  `research:202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`,
  `research:202610/pomodoro_area_project_attribution/pomodoro_area_project_attribution.md`,
  `research:202610/work_kind_pomodoro_theme_set/work_kind_pomodoro_theme_set.md`,
  `research:202610/pomodoro_six_theme_review/pomodoro_six_theme_review.md`.
- Live checks: `bob plan`, `bob plan -f json`,
  `bob stats show worked review_time sessions -r 2026-10-28..2026-10-28 -f json`, and a
  read-only ledger scan of `~/bob/2026/2026????.md` (Apr 27 – Oct 28).

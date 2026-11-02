# Unified task decay: WIP → Next → Ready → priority ladder

Research report for the freshness `<alt+f>` / `<ctrl+alt+f>` overhaul.
Researcher: mus. Date: 2026-11-02.

## 1. What was asked

Bryan wants to generalize the current Ready-only "approved decay" into one
unified **task decay** policy across lanes, with a new glossary term, new
config, a keep limit of 2 everywhere, a fix for the Ready-decay "no priority
ladder is configured" card state (screenshot `~/tmp/screenshots/20261102_134505.png`),
lane demotions (WIP → Next, Next → Ready), a keep-here-and-reset option,
unified Rotten Log entries (always written, with defaults), WIP keeps moving
from Work Log to Rotten Log, and a lead design that is intuitive, reliable,
and beautiful.

This report maps the current implementation, diagnoses the screenshot bug,
critiques each requirement, proposes adjustments, and ends with a recommended
solution.

## 2. Current system (verified in tree)

### 2.1 Freshness contract

The contract lives in `docs/freshness.md` (1622 lines). Rust reads, clears,
and reports; JavaScript counts and decides:

- `[fresh:: YYYY-MM-DD]` is the last human confirmation date. `[refresh:: N]`,
  `[keeps:: N]` (1–999, absence = 0), `[unblocked:: YYYY-MM-DD]` follow in
  canonical order (`src/native/freshness/placement.rs`, `docs/freshness.md` §3).
- `interval(t)`: `[refresh::]` → note `task_refresh` → `freshness.interval`
  (default 7). Lane rows override the whole chain with
  `pending_interval` / `next_interval` (default 1, `false` walks the lane off).
  `project_interval` overrides only `^prj` rows (`docs/freshness.md` §2, §4).
- Walk tiers: PRE → NEW → PROJECTS → PENDING → NEXT → RECURRING → TICKLER →
  ROTTEN → POST. Lane rows keep null `state`; Ready rows are NEW / RESURFACED /
  ROTTEN / FRESH (`docs/freshness.md` §4).
- `decide = enabled && lane == ready && tier in {rotten, tickler} && keeps >= limit`
  (`src/native/freshness/state.rs::decide_for`). Unblock ticklers
  (`returned_by: unblocked`) never decide; their keeps neither increment nor
  reset.

### 2.2 Keep streak and the decay card

- Only an exact, due, Ready ROTTEN/scheduled-TICKLER row increments
  `[keeps::]`, once per review, through the sole helper
  `api.freshness.keepLine(line, date, { counted })`
  (`docs/freshness.md` §2a; `plugins/bob-ledger-tools/src/080-freshness-placement.js::freshnessKeepLine`).
  Every other human stamp clears; automation never touches; same-day repeats
  preserve; NEW never counts (the `fresh < today` guard).
- At the limit (default 3, `freshness.decay.keeps`), the next single
  Alt+F / Ctrl+Alt+F press opens the consent card and writes nothing; counted
  and Task Link sessions skip at-limit targets (`N needs a decision`).
  `freshness.decay: false` counts and shows pips but never asks
  (`docs/freshness.md` §2a; decisions `rotten-keeps-use-priority-decay`,
  `decay-decisions-are-available-immediately`).
- The card (`planFreshnessDecayCard` in
  `plugins/bob-navigation-hotkeys/src/050-decay-planner.js`,
  `FreshnessDecayCardModal` in `.../src/060-decay-card-modal.js`) offers Not now
  (P0 entry or recommended roll/decay), Less often, Reword, Drop, Keep, plus
  explicit 1–4 level picks. Priority-changing approvals reuse the existing
  priority roll/decay ladder and log writers with `· kept N×` tails; Keep
  writes one Rotten Log entry in the same transaction
  (`docs/projects.md` "Approved-decay decision planner").
- Config today (`src/native/config/freshness.rs`): `decay` absent/null/`true`/`{}`
  = enabled with 3 keeps; `false` = count-only; mapping may set `keeps: 0–999`
  and `enter:` (nonempty priority label). Bryan's live config
  (`chezmoi/home/dot_config/bob/config.yml`) sets `freshness.interval: 3`,
  lanes 1/1, `project_interval: 1`, no `decay` block (so 3 keeps, no `enter`),
  and a P1–P4 ladder (P1 high 3–8, P2 medium 9–31, P3 low 32–100,
  P4 lowest 101–365, default `rolls: 1`).

### 2.3 Lane keeps and logs today

- Pending (`[/]`): Alt+F / Ctrl+Alt+F stamps and asks once for an **optional
  Work Log summary**; never touches Rotten Log or `[keeps::]`
  (`docs/freshness.md` §§2a, 5, 6; `.../src/195-rotten-keep.js`,
  `.../src/192-freshness-refresh-summary-modal.js`, `.../src/480-review-jump-and-nav-api.js`).
- Next (`[*]`): Alt+F / Ctrl+Alt+F asks "Why keep it in Next?"; a nonblank
  reason writes `*date* — <reason> · kept in Next`, blank stamps silently;
  never changes `[keeps::]` (decision `next-keeps-ask-an-optional-rotten-reason`).
- Ready counted keeps: prompt "Why keep it as written?"; blank logs
  `🤷 no reason given`; entry `*date* — <reason> · kept N×`, newest-first
  under `🥀 **ROTTEN LOG**` (decisions `rotten-keeps-are-logged`; grammar in
  `docs/reference/vault-format.md`).
- Alt+F stays on the row; Ctrl+Alt+F answers-and-advances the walk
  (`docs/freshness.md` §6).

## 3. The screenshot bug: "no priority ladder is configured"

The screenshot shows the decay card on a P0 Ready task ("foo bar baz",
kept 3×, three `🤷 no reason given` entries) with **both** Not now
("no priority ladder is configured") **and** the 1–4 explicit picks
("1–4 pick a P-level instead") unavailable, while Less often / Reword /
Drop / Keep stay available.

Code path (`050-decay-planner.js::planFreshnessDecayCard`):

- `hasPriorityLadder = property && property.values === "priority"`, where
  `property = findFreshnessDecayPriorityProperty(this.config)` scans
  `this.config.properties` for `values === "priority"`.
- When false, Not now is `unavailable("no priority ladder is configured")`
  and every explicit level pick renders the same reason (lines ~147–201,
  ~420–446). That matches the screenshot exactly: it is the
  **ladder-unknown** branch, not the P0-entry-scan branch (which would read
  `no level stays out longer than every N days` or `unknown enter level …`
  and would still offer 1–4 picks).

So the task's line is fine; the **config did not reach the card**.
Candidate causes, in likelihood order:

1. **Config load returned null on that host.** `loadBulletPropertyConfig`
   (`020-config-load-and-tasks.js`) returns null when `fs` is unavailable
   (mobile sandbox), the file is missing (`~/.config/bob/config.yml` not
   deployed via `chezmoi apply`), unreadable, unparseable, or invalid — and
   every one of those paths shows only a transient notice. Bryan's checked-in
   ladder is valid, so a missing/unapplied file on the Mac that took the
   screenshot is the most plausible cause.
2. **Invalid priority block on that host.** An invalid `properties:` block
   fails validation the same way (ladder unknown). Less likely given the
   checked-in file parses, but a local edit or a mid-sync read could do it.
3. **Not the P0 scan.** With Bryan's values (interval 3, P1 min 3) the scan
   `min_days > interval` skips P1 (3 > 3 is false) and would enter at P2 —
   arguably wrong (see §5.4) but it would **not** produce this screenshot.

Implications for the fix (§6.4):

- Do not hardcode "always P1" as a code fallback when the ladder is truly
  unknown: writing `[priority:: high]` from a hardcoded constant breaks the
  Tasks-format contract (`config.yml` header comment: `value` must stay one
  of Obsidian Tasks' priority names **and** come from the configured ladder)
  and invents a level the Task Card cannot roll.
- Do fix the UX and the config: (a) set `decay.enter: P1` explicitly so P0
  entry never depends on the `min_days > interval` scan; (b) relax or
  fallback the scan (see §5.4); (c) make the card distinguish "config file
  missing at <path>" / "priority config invalid: <reason>" from "no ladder",
  with the path and a `chezmoi apply` hint, instead of one dead-end line.

Bryan's instinct ("just always use P1, right?") is correct **as config** for
his ladder and interval, not as a hardcoded code default. That distinction
is the adjustment to carry forward.

## 4. Is this a good idea? Critique

Yes — with three reservations that shape the design.

**Why it is good.** Today only Ready decays, while the two lanes that
actually fill up (WIP cap 8, Next cap 13) have no cooling mechanism except
manual Alt+N release. Sticky lanes (decision `task-lanes-are-sticky`) were an
explicit tradeoff: protect dropped work by default, pay 2–3 tasks/day of lane
growth, and rely on daily review plus release. Lane decay completes that
design: repeated "still here?" answers earn an explicit demotion question
instead of silent accumulation. Unifying Ready priority-decay and lane
demotion under one "task decay" term also removes the current conceptual
split where `[keeps::]` means one thing for Ready and nothing for lanes, and
where three prompts (Work Log / optional Rotten / mandatory Rotten) have
three different blank-line rules.

**Reservation 1: it partly supersedes sticky lanes.** `task-lanes-are-sticky`
says "only release lowers Next or Pending to Ready" and lists "age-based Next
decay" as a rejected alternative. Lane decay at the keep limit **is**
age-plus-confirmation-based demotion, so it needs a new decisions record that
names the supersession: lanes stay sticky against links, unlink, hooks, and
capture, but an explicit approved-decay choice may demote. Without that
record the change reads as a regression of a settled decision.

**Reservation 2: card volume.** Pending/Next intervals default to 1 day, so a
full lane review could surface many more cards than Ready-only decay does
today. The current reopen conditions already warn that ~5 counted keeps per
morning or >80% blank reasons mean the gate is misfiring. Mitigations belong
in the design: cards only for exact, due, at-limit lane rows; counted/Task
Link sessions skip (as Ready does); keep the walk moving (Ctrl+Alt+F
advances, Alt+F stays); and keep Less often / release / do-today one key
away so the card is a cooling offer, never a tollbooth.

**Reservation 3: silent-demotion temptation.** The cheaper implementation —
auto-demote at the limit with no card — must stay rejected. The whole
approved-decay line (decisions `rotten-keeps-use-priority-decay`,
`decay-decisions-are-available-immediately`) exists because silent auto-decay
was explicitly refused. Lane decay must keep the same guarantee: at the
limit the press writes nothing until Bryan chooses.

Alternative approaches considered and why not: (a) only lengthen
`pending_interval` / `next_interval` — cheaper but hides work instead of
cooling it, and the weekly guidance already covers it; (b) a single global
keeps counter across lanes — simpler state but conflates "kept as Ready
twice, then as Next once" into one number, which is exactly the confusion the
per-lane counts fix; (c) auto-demote without consent — rejected above.

## 5. Requirement-by-requirement analysis

### 5.1 New glossary term for "task decay"

Needed. Today "decay" means three different things in three docs: the
priority roll/decay ladder (`docs/projects.md`), the keep-streak card
(`docs/freshness.md` §2a), and the tooltip slang. The new term should cover
both halves (lane demotion + priority descent) and pin the properties that
make it safe: explicit consent, streak-gated, logged, freshness-neutral.

Proposed definition (for `glossary:task-decay`):

> **Task decay** is the explicit, streak-gated cooling of a task Bryan keeps
> confirming without changing. After N consecutive due keeps in the same lane
> (default 2), the next Alt+F / Ctrl+Alt+F press writes nothing and offers a
> choice instead: demote one lane (WIP → Next → Ready), enter or descend the
> priority ladder (P0 → P1 → … → cancel), see it less often, reword, drop, or
> keep here with the count reset. Decay never fires on a timer, never changes
> `[fresh::]` semantics, lanes, schedule, or priority by itself, and every
> keep and every decay writes its own dated log entry. Lane decay and
> priority decay are the two halves of one policy; the card is its only
> surface.

### 5.2 Config: per-status flexibility

Bryan suggested "allowed rolls for each task status". For lanes that is the
wrong knob: lanes have no priority windows, so "rolls" is meaningless there.
The lanes need two knobs: **how many keeps before the question** and **where
demotion goes**. Priorities already have their knob (`levels[].rolls`,
`decay.rolls`).

Recommended shape — flat keys, consistent with the existing
`interval` / `pending_interval` / `next_interval` style, fully
backward-compatible (`keeps` stays the default for every lane):

```yaml
freshness:
  decay:
    keeps: 2        # default for every lane when the lane key is absent
    pending_keeps: 2
    next_keeps: 2
    ready_keeps: 2
    enter: P1       # P0 Ready entry level; see §5.4
    pending_to: next  # WIP decay target: next | stay
    next_to: ready    # Next decay target: ready | stay
```

Semantics: `pending_to: stay` / `next_to: stay` disables lane demotion for
that lane (the card offers keep-here-reset plus the non-lane rows only).
Unknown targets, negative keeps, and non-integer keeps are config errors
under the existing freshness failure contract (Rust exit 2; plugins fall back
to defaults marked `invalid`). Rust validates `enter` against the priority
loader as today — no second hardcoded P-table.

Why not a nested `lanes:` map? Nested maps are harder to comment concisely
and break the file's flat rhythm; per-lane suffixed keys (`pending_keeps`)
mirror `pending_interval` and need no new parser shape beyond two strings.

### 5.3 Two keeps everywhere (Ready 3 → 2)

Endorse. It unifies the mental model ("twice, then I get asked"), matches the
already-requested Ready change, and the calibration tally the old decision
asked for (mostly-Keep suggests 4, mostly-Drop suggests 2) can be re-run
against the new limit. Note the consequence: with the default lane interval
of 1 day, a lane task kept Monday and Tuesday asks on Wednesday. That is the
intended cooling rate, but it is also why §4's volume mitigations matter.

`[keeps::]` becomes a **per-lane streak**: consecutive due keeps in the
current lane. Lane change (manual Alt+N release, Ctrl+Shift+Enter pull,
decay demotion, or the reset option) zeroes it; any non-keep stamp clears it
(unchanged); same-day repeats preserve (unchanged); unblock ticklers still
neither increment nor reset; NEW never counts. The field needs no new name —
its meaning is "keeps here", and the Rotten Log records the lane so history
stays legible.

### 5.4 Ready P0 entry and the "always P1" question

Endorse `enter: P1` **in Bryan's config**; adjust the code default as follows:

- The current scan (`resolveFreshnessDecayP0EntryLevel`: first level with
  `min_days > interval`) with interval 3 skips P1 (3 > 3 false) and enters at
  P2. For a user who tuned P1 to 3–8 against an interval of 3, P2 entry
  feels like a skip. Options: (a) relax to `min_days >= interval` (P1
  qualifies; minimum equals the lease, average lengthens it); (b) fall back
  to the first ladder level when no level strictly exceeds; (c) leave the
  scan and rely on explicit `enter`. Recommend (c) as policy plus (b) as
  safety: explicit `enter` always wins; absent `enter`, prefer the scan, but
  fall back to the first level rather than disabling Not now. Never fall back
  to a hardcoded P1 value when the ladder is unknown.
- Fix the card's dead-end copy per §3: distinguish missing file (with path +
  `chezmoi apply` hint), invalid priority config (with reason), unknown
  `enter` label, and "no level outlasts N days" — four different problems,
  four different lines.

### 5.5 WIP → Next and Next → Ready defaults

Endorse, as **offered defaults**, not silent moves:

- At-limit WIP card: primary row "Move to Next (default)" + "Keep in WIP,
  reset count" + Less often / Reword / Drop / Keep-counting-again? No — see
  §5.6: the reset row replaces the ambiguous extra Keep.
- At-limit Next card: primary "Move to Ready (default)" + "Keep in Next,
  reset count" + the same auxiliaries.
- Demotion stamps `[fresh:: today]`, zeroes `[keeps::]`, and (for Next)
  follows the existing release semantics minus the Work Log prompt: no lane
  promotion side effects, no Pomodoro link changes beyond what a manual
  release would do. Demotion of a `^prj` lane row stays out of scope —
  PROJECTS rows never decide, as today.
- Counted (`N<Alt+F>`) and Task Link sessions skip at-limit lane targets
  with `N needs a decision`, exactly like Ready at-limit targets today.

### 5.6 "Keep the status the same, reset the keep count"

Endorse and sharpen: the card needs exactly one keep-here row, and it must
reset. Today's card has Keep (increment, ask again next review) but no
reset; adding a second Keep without removing ambiguity creates two buttons
that both "keep". Recommended rows:

- **Keep here · reset count** (the requested option): stamp, set
  `[keeps::]` to 0 (omit the field), write one Rotten Log entry with a
  `· kept <Lane> 0× · reset` tail or equivalent, and treat the next due
  review as a fresh streak.
- **Keep counting** stays as today's Keep only where it makes sense; for
  lanes, prefer making reset the single keep-here action to keep the card to
  six rows. If both are kept, label them unambiguously ("Keep · count again"
  vs "Keep here · reset to 0") — never two rows both called Keep.

### 5.7 Rotten Log reflects every transition

Endorse with a grammar. Current grammar splits Ready (`· kept N×`, always)
from Next (`· kept in Next`, no count, only when nonblank). Unify to
**always lane + always count**:

- `*2026-11-02* — <reason> · kept WIP 2×`
- `*2026-11-02* — <reason> · kept Next 2×`
- `*2026-11-02* — <reason> · kept Ready 2×`
- Reset: `*2026-11-02* — <reason> · kept Next 0× · reset`
- Lane decay itself: no second Rotten entry needed — the demotion is visible
  in the checkbox/lane change, and the triggering keeps are already logged.
  Priority decays keep today's `🎲 … · kept N×` Schedule Log convention.
- Blank-reason defaults (§5.9) make "always" true without nagging.

Migration: no backfill (same rule as the original Rotten Log rollout); old
`· kept in Next` and `· kept N×` entries parse as history, new entries use
the unified form. The entry-count display ("N keeps logged") stays
display-only and never drives decay.

### 5.8 WIP: stop Work Log, prompt Rotten Log instead

Endorse the direction, soften the deletion. "What did you get done?" is the
wrong question for a WIP task being kept without progress, and routing WIP
keeps to the Rotten Log fixes the lane's missing history. But WIP is the one
lane where real progress notes exist. Recommended: the WIP keep prompt
becomes the Rotten prompt (required, with default per §5.9), with an
**optional second field** for a Work Log summary in the same modal — one
round trip, two destinations, blank Work field writes nothing. That preserves
today's capability without preserving today's wrong default.

Also update the scheduling Work Log prompt (`docs/projects.md` "Scheduling
Work Log prompt") to cross-reference: scheduling a WIP/Next task still offers
Work Log; keeping one now offers Rotten Log first.

### 5.9 Next: always log (explicit or default)

Endorse. The current blank-stamps-silently rule is the only place where a
counted keep leaves no trace, and it makes per-lane counts unverifiable.
Unify blank handling across lanes to the Ready rule: blank Enter logs the
default. Default text must carry lane + count so a month of blanks stays
legible:

- `🤷 no reason given · kept Next 2×` (and WIP / Ready analogues).

This also answers "make clear how many times each task was kept in each
status": the count is per-lane at write time (the streak in the lane being
kept), and the lane word disambiguates history after later demotions.

### 5.10 Beauty, intuitiveness, reliability

- **Intuitive:** one card shape for three lanes; primary action = cool down
  (demote / enter P1); secondary = keep here + reset; auxiliaries (Less
  often, Reword, Drop) identical everywhere; footer names the lane ("Esc
  changes nothing · D drops · 1–4 pick a P-level" for Ready, lane-appropriate
  for WIP/Next). Pips and `kept N×` / `· decide` annotations in
  `bob freshness list` and the footer extend to lane rows so the card never
  surprises.
- **Reliable:** one undo per decision; revalidate line, day, decay config,
  eligibility, child-block preimages, and ladder before commit (existing
  pattern); stale inputs rebuild, never write; mixed-version fallback keeps
  counting with counting-only copy; `freshnessKeepLine` stays the sole
  increment path with its `fresh < today` guard; Rust stays read/clear/report
  with shared conformance vectors extended for lane keeps and the new config.
- **Beautiful:** keep the screenshot's card — it is already good — and fix
  only its failure mode (truthful, actionable unavailability lines) plus the
  new rows' copy. No new surfaces, no new log kinds, no new fields.

## 6. Recommended solution

### 6.1 Glossary: add `glossary:task-decay`

Add the §5.1 definition verbatim (tuned by Bryan). Cross-link
`glossary:task-freshness`, `glossary:keep-streak` (`[keeps::]` is now "keeps
here"), `glossary:rotten-log` (unified lane+count grammar), and the
superseding decisions record. No other glossary changes.

### 6.2 Config: extend `freshness.decay`, set Bryan's values

Parser (`src/native/config/freshness.rs::parse_decay_config` + ledger-tools
mirror): accept `pending_keeps` / `next_keeps` / `ready_keeps` (0–999,
defaulting to `keeps`), `pending_to` / `next_to` (`next`/`ready`/`stay`;
`pending_to` allows `next|stay`, `next_to` allows `ready|stay`), keep `enter`
as-is. Per-lane limit resolution: lane key when set, else `keeps`. Extend
`tests/fixtures/freshness_keeps/vectors.json` with the new keys (valid,
defaulting, and each invalid shape) and the lane `decide` cases.

Bryan's `chezmoi/home/dot_config/bob/config.yml` (concise comments):

```yaml
freshness:
  interval: 3 # Ready backlog review cadence
  pending_interval: 1 # [/] lane daily review; false = not walked
  next_interval: 1 # [*] lane daily review; false = not walked
  project_interval: 1 # ^prj review cadence (personal setting)
  # rotten_daily_budget: 15 # upkeep goal meter; never hides tasks
  decay:
    keeps: 2 # default keeps before the decay card asks (every lane)
    pending_keeps: 2 # WIP keeps before asking (default: keeps)
    next_keeps: 2 # Next keeps before asking (default: keeps)
    ready_keeps: 2 # Ready keeps before asking (default: keeps)
    enter: P1 # P0 Ready entry level: first rung of your P1-P4 ladder
    pending_to: next # WIP decay target: next | stay (stay = no demotion)
    next_to: ready # Next decay target: ready | stay
```

Rationale for each default: 2 unifies every lane per the request; `enter: P1`
removes the `min_days > interval` skip for Bryan's interval-3/P1-min-3 pair;
`next`/`ready` are the requested demotion defaults; `stay` preserves an
escape hatch without a second flag.

### 6.3 Counting and decision logic

- `[keeps::]` → per-lane streak (§5.3). `freshnessKeepLine` gains lane-aware
  counting: exact, due, lane-eligible rows (Ready rotten/scheduled-tickler as
  today, plus due PENDING/NEXT rows) increment when `counted && fresh < today`
  and `returned_by != unblocked`; lane change zeroes; all else unchanged.
  Eligibility stays exact-pre-write-queue matched, once per review.
- `decide_for` gains lanes: `(lane == ready && tier in {rotten,tickler} &&
  keeps >= ready_limit) || (lane == pending && tier == pending && due &&
  keeps >= pending_limit && pending_to != stay) || (lane == next && tier ==
  next && due && keeps >= next_limit && next_to != stay)`, still gated on
  `enabled` and never for unblock ticklers, PROJECTS, recurring, NEW, or
  early rows. Rust reports lane `keeps`/`decide` in `bob freshness list`
  (header `keeps 2`, rows `kept WIP 2× · decide`); JSON schema gains
  lane-decay config + per-row lane/decide (bump with the existing schema
  process, currently 14).
- Single Alt+F / Ctrl+Alt+F on an exact, due, at-limit lane row opens the
  lane card and writes nothing; counted/Task Link sessions skip with
  `N needs a decision`; mixed-version fallback counts with counting-only copy.

### 6.4 Card and prompt changes (nav-hotkeys + ledger-tools)

- WIP card: [Move to Next (Enter, default)] [Keep here · reset (Alt+F)]
  [Less often (L)] [Reword (E)] [Drop (D)]; Next card mirrors with Move to
  Ready. Ready card keeps today's rows, gains the reset row per §5.6, and
  keeps 1–4 picks. Every demotion/keep-here writes per §§5.7–5.9 in one undo
  step with full revalidation.
- WIP prompt becomes Rotten-first with optional Work second field (§5.8);
  Next/Ready prompts keep their copy with unified always-log defaults (§5.9).
  Lane demotions follow release stamping (fresh today, zero keeps, clear
  unblocked) with no Pomodoro side effects beyond a manual release.
- Ladder-unknown copy: four distinct, actionable lines (§§3, 5.4) with config
  path + `chezmoi apply ~/.config/bob/config.yml` hint; plus the P0
  first-level fallback when no level strictly outlasts the interval. No
  hardcoded-P1 write path.

### 6.5 Docs, decisions, tests

- `docs/freshness.md` §§2/2a/4/5/6/7/11: per-lane keeps, lane targets, unified
  log grammar, lane `decide`, prompt matrix, header/row copy; `docs/projects.md`
  planner: lane demotion plans + reset semantics; `docs/reference/vault-format.md`:
  unified Rotten entry grammar (old forms remain parseable history).
- New decisions record superseding `task-lanes-are-sticky` (age-demotion carve-out),
  `rotten-keeps-use-priority-decay` (lane half), `rotten-keeps-are-logged` +
  `next-keeps-ask-an-optional-rotten-reason` (always-log unification). Each states
  scope, claim, beaten alternatives (silent auto-demotion, global counter,
  rolls-per-status), cost (card volume, two implementations under shared
  vectors), and reopen conditions (blank-rate / keeps-per-morning tallies).
- Tests: Rust config/state/cli cases, extended
  `tests/fixtures/freshness_keeps/vectors.json`, ledger-tools parity tests,
  `scripts/test-navigation-decay-planner.cjs` + decision-card handler suites
  for lane cards, reset, defaults, and the four ladder-unknown lines.

## 7. Adjustments to the request (explicit)

1. **"Allowed rolls per status" → per-lane keeps + lane targets** (§5.2):
   rolls are meaningless for lanes; keeps + targets are the correct knobs.
2. **"Always use P1" → `enter: P1` in config, not hardcoded** (§§3, 5.4):
   hardcoding invents levels and breaks the Tasks contract; explicit config
   plus a first-level fallback fixes the screenshot without that risk.
3. **Two Keep rows → one reset row as the keep-here action** (§5.6): avoids
   two indistinguishable Keeps; reset is the requested semantic.
4. **WIP Work Log deletion → Rotten-first + optional Work field** (§5.8):
   preserves real progress notes in one modal instead of destroying the
   capability.
5. **Lane decay writes no extra decay entry** (§5.7): the lane change is its
   own record; only keeps log (plus existing Schedule Log tails for priority
   moves). Keeps the log beautiful instead of double-writing every demotion.
6. **New decisions record required** (§4): the plan partly supersedes sticky
   lanes and must say so, or it will read as a regression.

## 8. Risks and open questions

- Card volume under daily lane intervals: watch blank-rate and
  keeps-per-morning; the reopen tallies from the superseded decisions should
  be re-armed for lanes.
- `pending_to`/`next_to` naming bikeshed: `*_to` vs `*_target` — pick one and
  keep it flat.
- Whether Less often for lanes should offer the same 14/30/90 presets (yes,
  via `setRefreshLine`/lane interval? — needs a planner decision: lane Less
  often lengthens the lane interval per task via `[refresh::]`? No — lane
  rows ignore `[refresh::]` today, so lane Less often must either set a
  per-task lane refresh (new) or route to the Ready chain. Recommend: lane
  Less often sets `[refresh::]` AND the evaluator honors per-task refresh for
  lane rows as an override — small, explicit, and testable; flag if rejected.)
- Mobile/missing-config UX copy needs Bryan's eye on the actual dead-end
  strings.

## 9. Bottom line

Approve the unified decay direction. Ship per-lane keeps (2/2/2) + lane
targets (`pending_to: next`, `next_to: ready`) + `enter: P1`, per-lane
`[keeps::]` streaks, offered (never silent) demotions with a keep-here-reset
row, always-logged lane+count Rotten entries with defaults, Rotten-first WIP
prompts, truthful ladder-unknown copy, and the decisions-record supersession.
Fix the screenshot by deploying config (`chezmoi apply`) and setting
`enter: P1` — not by hardcoding P1.

## Evidence consulted

- `docs/freshness.md` §§1–7, 10a/11; `docs/projects.md` priority marks,
  recommended roll/decay, approved-decay planner, schedule/work-log prompts;
  `docs/reference/vault-format.md` log grammar; `docs/plan.md` lane caps.
- `src/native/config/freshness.rs` (decay + lane parsing, defaults keeps 3);
  `src/native/freshness/state.rs::decide_for` (Ready-only today);
  `src/native/freshness/cli.rs` (header/row copy, schema 14);
  `tests/fixtures/freshness_keeps/vectors.json` (parity vectors).
- `chezmoi/home/dot_config/bob/config.yml` (interval 3, lanes 1/1, P1 3–8
  ladder, no decay block).
- `plugins/bob-ledger-tools/src/080-freshness-placement.js::freshnessKeepLine`
  (sole increment helper, `fresh < today` guard);
  `plugins/bob-navigation-hotkeys/src/050-decay-planner.js::planFreshnessDecayCard`
  (ladder-unknown branch, P0 scan `min_days > interval`),
  `.../src/040-priority-roll.js::resolveFreshnessDecayP0EntryLevel`,
  `.../src/060-decay-card-modal.js`, `.../src/195-rotten-keep.js`
  (lane vs counted grammar), `.../src/192-freshness-refresh-summary-modal.js`,
  `.../src/020-config-load-and-tasks.js::loadBulletPropertyConfig`,
  `.../src/530-plugin-freshness-refresh-and-decay.js`.
- Screenshot `/home/bryan/tmp/screenshots/20261102_134505.png` (ladder-unknown
  card on a P0 Ready task at 3 keeps).
- Memory: `decisions:rotten-keeps-use-priority-decay`,
  `decisions:rotten-keeps-are-logged`,
  `decisions:next-keeps-ask-an-optional-rotten-reason`,
  `decisions:task-lanes-are-sticky`, `decisions:ready-is-freshness-gated`,
  `decisions:decay-decisions-are-available-immediately`,
  `decisions:unblocked-tasks-resurface-as-ticklers`,
  `glossary:task-freshness`, `glossary:keep-streak`, `glossary:rotten-log`,
  `glossary:work-log`.


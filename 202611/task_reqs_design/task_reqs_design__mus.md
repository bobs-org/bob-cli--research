# Sub-tasks for Bob: design, critique, and recommended solution

Researcher: mus · 2026-11-21
Scope: decide how Bob should support sub-tasks (the `^micro-tasks` /
`^micro-tasks-cleanup` line in `~/bob/bob.md`), given that the `bob-cli-of`
epic ("Explicit micro tasks") was canceled for rethinking. Out of scope:
project → task round-trip for arbitrarily complex projects (noted where it
matters).

Prior material I used (shared input, not peer work): the `^micro-tasks` and
`^micro-tasks-cleanup` task bodies in `~/bob/bob.md`, the four tasks
`^micro-tasks` blocks (`^better-o`, `^micro-tasks-cleanup`,
`^no-all-caps-for-drawers`, `^tasks-parent-projects`), the canceled epic bead
`bob-cli-of` and its plan `plan:202611/explicit_micro_tasks.md`, and the base
design `research:202611/explicit_micro_tasks.md` plus its final synthesis. I
re-verified every load-bearing code claim below myself in this checkout; where
I agree with that prior synthesis it is because the code agrees, not because I
borrowed a conclusion.

## TL;DR

**Verdict: build it, but not as written in either the canceled epic or the
cleanup note.** The feature fixes a real, demonstrable bug (promotion guesses
which sub-bullets are work), and the close-time audit is its heart. Of the
seven cleanup bullets, I would **accept two, amend three, and reject two**:

- ACCEPT: single-level-only v1; sorted block order
  (links < steps < drawers < logs); `Ctrl+J` support (near-free).
- AMEND: rename — do not ship `req`; tick semantics — allow ticking anytime,
  keep `[-]`/reason as one path, not the only path; `..` alias — keep it and
  *add* natural `[ ]` typing instead of replacing it.
- REJECT: stored `##` with no checkbox; auto-created physical `NOTES` drawer.

Recommended v1: **a checkbox step without `#task`, parented by a `#task` line
(`- [ ] Write the parser`), rendered as `⌗⌗` in the existing tag-marks glyph
language, depth computed from indentation.** Call it a **step** (glossary:
`task step`, alias `micro task`), not a `req`. Loose bullets stay notes.
Steps tick while working, audit at close with Done-by-default, Keep-open via
split, merge writes steps, promotion maps steps → `## Tasks` and notes →
`## Notes`. Details in §7.

## 1. What the request actually says

`^micro-tasks` (`bob__micro-tasks`, currently `[/]`, P-high) proposes:

- sub-bullets prefixed `TASK:`/`ALSO:` (with `?!` — genuinely undecided);
- successors "with a default closed state";
- Obsidian rendering as `##`, `###`, …; `- ..` expands to `- ##`;
- normal bullets migrate to a Notes H2 on promotion **or** immediately into a
  `NOTES` drawer (`?!` again);
- old epic `bob-cli-of` (now canceled: "needs some rethinking", Rotten Log
  2026-11-21).

`^micro-tasks-cleanup` (`bob__micro-tasks-cleanup`, `[?]`, depends on
`^micro-tasks`) proposes seven concrete revisions:

1. Rename to "task requirement" (`req`).
2. Sort reqs after links, before drawers, drawers before logs.
3. Auto-create (and capture-into) a `NOTES` drawer whenever reqs exist.
4. Reqs can't be completed before their parent — only canceled/obsoleted with
   optional reason.
5. No `[ ]` checkbox shown, only `##`.
6. Drop `..` alias; expand `- [` → `- [ ] `; `<backspace>` at that point
   removes the `[ ] `.
7. Support `Ctrl+J` successor jump; single level only (`##`, no nesting).

Blocked downstream (all `[?]`, all `dependsOn: bob__micro-tasks`):

- `^better-o`: `o` / `Ctrl+Shift+O` create a task below the current one and
  "respect the task sub-bullet ordering (links < reqs < drawers < logs)".
- `^no-all-caps-for-drawers`: stop requiring ALL-CAPS drawer titles.
- `^tasks-parent-projects` (blocks `^task-to-project`): allow tasks to parent
  projects.
- Plus `^recursive-task-cancel` ("not sure if desirable now") and
  `^successor-deps` nearby.

So the dependency arrow is: **steps first, then keymaps, drawer syntax, and
hierarchy.** Any step definition must not assume ALL-CAPS survives, must give
`o` a deterministic insertion point, and must leave room for task-parented
projects to provide *real* nesting later.

## 2. Is this a good idea?

**Yes.** Three independent reasons, each checkable:

1. **Promotion guesses today and is wrong most of the time.** Task → project
   promotion (`docs/projects.md`, "Promotion successors";
   `plugins/bob-navigation-hotkeys/src/110-project-seed.js`,
   `buildProjectSeedFromChildBullets`) turns every non-drawer, non-managed
   direct child into a `#task` row — images, Gmail links, prose included.
   Prior vault scans found only ~1 in 5 loose bullets even look like steps.
   An explicit work-marker removes the guess. This alone justifies the
   feature.
2. **Close-time review is the right enforcement point.** The stated goal —
   "make sure committed work is really done before closing" — cannot be met
   by a marker alone. Only a managed-Done audit (the successor card,
   `docs/task-dependencies.md` §12.22) turns the marker into a guarantee.
   The card already exists; this is a new group on it, not a new panel.
3. **It unlocks the hierarchy work without committing to it.** Once steps are
   explicit, `tasks-parent-projects` can give *real* nesting (task → project
   → tasks) while steps stay flat. That layering is cleaner than teaching
   steps themselves to nest arbitrarily in v1.

Would I take a different approach? Only in the sense the cleanup note already
does: **narrow v1 hard** (flat, small, no new panel, no flag-day rewrite).
Where I differ from the cleanup note is *which* narrowings preserve the
guarantee. Two of its narrowings (`##`-only storage, no ticking before close)
destroy exactly the state and timing the guarantee needs. §3–§4 explain.

## 3. The marker and the name: the two load-bearing choices

### 3.1 Storage must be a checkbox, not `##`

I verified in this checkout:

- `src/native/capture_language/mod.rs:63` — `GRAMMAR_REVISION = 28`.
- `src/native/stats/compute.rs:2709-2836` and
  `src/native/task_status_groups/mod.rs:331` — lane/review/stats paths key
  off `global_filter` (`#task`); a plain `- [ ]` child is invisible to them
  unless a step-aware guard says otherwise. That invisibility is *wanted*:
  steps must never be lanes, walk rows, Ready-cap members, or Today members.
- `docs/task-split.md` §1 — an unchecked `- [ ] text` without `#task` is
  already splittable into a real task; checked ones refuse. Promotion
  preserves a checkbox child's status. No other candidate marker gets this
  engine reuse for free.
- `src/native/capture_drawers.rs` (`is_drawer_rest`) — `:` is accepted as the
  final character of a drawer title, so any `REQ:`/`TASK:`-family marker needs
  a grammar carve-out next to the reserved `TASKS` key. `##` needs no
  carve-out but pays a worse price below.

Why `##`-only storage fails (reject cleanup bullet 5):

- **No state.** Close needs three distinguishable outcomes — *done*,
  *not done*, *carried* — plus *open*. A bare `##` line plus `~~strike~~`
  cannot tell canceled from carried, and a strike edit destroys the text
  range a later `Ctrl+Shift+T` "carry now" would split. The checkbox gives
  `[ ]` / `[x]` / `[-]` / `[>]` natively, byte-visible, Obsidian-styled,
  greppable. `[-]` and `[>]` need two tiny CSS rules (`data-task="-"/">"`);
  `[ ]`/`[x]` need none.
- **Depth rots.** Indentation already encodes depth. A stored `##`/`###` run
  desyncs on every re-indent/move and needs a repair pass; computed depth
  cannot lie. Four of five prior researchers agreed; the code agrees too —
  no other stored value in the task block duplicates indentation.
- **Heading collision.** `- ## foo` is not an ATX heading under CommonMark
  (it is bullet text `## foo`), but it *reads* as a heading fragment, breaks
  `- #drawer` adjacency reasoning (`decisions:capture-bullets-mirror-the-
  task-block`: first-level `- #…` is the drawer shortcut), and will confuse
  every future reader of `no-all-caps-for-drawers` (if drawer titles stop
  being ALL-CAPS, what distinguishes `- ## step` from `- ## section`?).
- **No tick path.** §4 shows ticking-while-working is the anti-rubber-stamp;
  `##` lines are not clickable or `Ctrl+Enter`-cyclable without inventing a
  parallel toggle. The cycler (`TASK_LINE_RE` matches any `[.]`) already
  toggles `[ ]` ↔ `[x]`; it needs only a step guard (same shape as the
  existing bank-row guard), not a new engine.

Beautiful without lossy: **store the checkbox, render the hashes.**
Extend the tag-marks system (`docs/task-tag-marks.md`,
`plugins/bob-ledger-tools/src/138-task-tag-marks.js`): `#task` draws one
slanted teal `⌗`; a top-level step draws `⌗⌗` after its checkbox in the
owner's ink, nested (if later enabled) `⌗⌗⌗`, capped visually at five. If
Bryan wants the literal `##` look, do it in CSS (hide the box glyph, show the
hash run) — never in bytes. Source stays an ordinary Markdown to-do list when
plugins are off, which is the best no-plugin fallback.

Definition (v1): **a step is a checkbox list item without `#task` whose parent
is a `#task` line.** (Reserve `parent is a step` for v2 nesting; recognizer
accepts it structurally now so v2 needs no migration — see §5.) Checkboxes
anywhere else — drawer entries, notebooks, Pomodoros, bank rows, quoted
checklists — are untouched. No vault reinterpretation: prior scans found zero
plain-checkbox children under open `#task` lines.

What a step never has: `#task`, `[created::]`, lane, freshness, priority,
schedule, dependencies, Task Links, walk rows, stats. A Pomodoro Task Link to
a step anchor is refused with a teaching notice ("Steps aren't planned. Link
the owner, or split the step first."). A trailing `^anchor` is allowed and is
reused as the new task's ID on Keep-open, preserving links.

### 3.2 Name: ship "step", not "req" (amend cleanup bullet 1)

`req` has three problems:

- It collides with the existing `REQUIREMENTS` drawer conceptually and with
  `REQ:`-as-drawer-title mechanically (§3.1). Users will reasonably ask
  whether a "req" goes in REQUIREMENTS — the answer ("no, REQUIREMENTS is a
  drawer of notes, reqs live above drawers") is embarrassing.
- It misleads about optionality. "Requirement" implies must-do-or-cancel,
  which fits cleanup bullet 4 but not tick-while-working, partial credit, or
  the `2/4` progress idiom. Most real steps are decompositions, not gates.
- It is insider shorthand: hard to say ("wreck" vs "re-q"?), hard to type,
  no verb form. "Step" has all three: *step*, *steps*, *tick the steps*.

"Subtask" is the user's word and the industry word, but it promises full task
semantics (lanes, freshness, deps, links) that v1 deliberately withholds —
exactly the confusion the glossary should prevent. "Micro task" is honest
(small, not-full) but invites the "how small is micro?" bikeshed that already
cost one epic.

Recommendation: **glossary term `Task Step` (alias `step`; retiring alias
`micro task` kept as a redirect for one release).** Capture docs, card
footers, and teaching notices all say "step". If Bryan loves `req`, keep it
as4 a capture-drawer-adjacent nickname in prose only — never in bytes or
grammar.

## 4. Semantics: ticking, sorting, and the NOTES drawer

### 4.1 Allow ticking anytime (amend cleanup bullet 4)

"Reqs can't be completed before their parent, only canceled/obsoleted" sounds
principled but has four costs:

1. **It bans the best anti-rubber-stamp.** Steps ticked during the work fold
   out of the close card; a fully ticked task closes with no card at all.
   Forcing all resolution into the close gesture guarantees the card is a
   rubber stamp on long tasks — the opposite of the stated goal.
2. **It fights the hands.** Obsidian checkboxes toggle on click;
   `Ctrl+Enter` (cycler) toggles any checkbox. Intercepting that with "not
   yet!" on every step will read as broken, not principled.
3. **It conflates *done* with *audited*.** The audit question is not "did you
   tick early?" but "is every step resolved at close, and does the file say
   how?". `[x]` written Tuesday plus a close card that folds resolved rows
   into one line answers it fully.
4. **It needs a second encoding anyway.** "Canceled/obsoleted with optional
   reason" is `[-]` + an optional reason bullet — which is exactly the
   checkbox-state scheme. The cleanup note half-invents the checkbox while
   banning its main state.

Recommended rule: steps tick `[ ]` ↔ `[x]` freely (click, `Ctrl+Enter`,
Mac editor); `Alt+]`/`Alt+[`, Task Card, `Alt+N`, `Alt+F` refuse on step
lines with a teaching notice (step guard, same shape as bank-row guard).
At close, open top-level steps audit (default Done); `[x]`/`[-]`/`[>]`
fold to one summary line with per-row expand. `Ctrl+Shift+T` on an open step
splits it *today*, leaving `- [>] [[#^id|Alias]]` — byte-identical to
close-time Keep-open. Cancellation anytime writes `[-]` plus an optional
`reason:` child; it is one path, not the only path.

### 4.2 Keep the sorted order (accept cleanup bullet 2, extend to `o`)

Agreed: within a task block, writers maintain
**managed links (Depends-On/BLOCKS/LINKS) < steps < drawers < logs
(Schedule/Work/Rotten/Cancel)**, with `o`/`Ctrl+Shift+O` inserting at the
right slot. This is the invariant `^better-o` needs ("respect the task
sub-bullet ordering"), and it is what makes loose notes readable next to
steps without a drawer. Implement as: writer invariant in `bob capture`,
`task_split`, merge, and promotion writers; `o` on a step line inserts a
sibling step, on a note line a sibling note, on a drawer entry a drawer
entry; a `doctor`/lint repairs drift (never silently on read).

### 4.3 Do not auto-create a NOTES drawer (reject cleanup bullet 3)

With an explicit step marker, the drawer adds no disambiguation — marked is
work, unmarked is information. Auto-creating `NOTES` whenever steps exist:

- nests every captured note one level deeper and stamps a `NOTES` header on
  most stepped tasks (visual noise, the opposite of beautiful);
- splits notes into two populations (legacy loose vs new drawer-filed) until
  a migration nobody asked for;
- breaks the audited mirror rule
  (`decisions:capture-bullets-mirror-the-task-block`: the draft reads like the
  block it writes) and the "capture never creates an empty drawer" invariant
  (`glossary:task-drawer`, `src/native/capture_drawers.rs`);
- complicates `o` (two note homes) and promotion (merge rule must handle
  three inputs instead of two).

Recommended rule (keeps the request's "as if" phrasing): **a loose plain
bullet under a task *is* a note — the implicit NOTES drawer.** Capture keeps
writing `@route+id <note>` as a loose bullet byte-for-byte.
`@route+id#notes` still files into an explicit `NOTES` drawer for anyone who
wants one (`NOTES` stays an ordinary, unreserved drawer). Promotion merges
loose notes *and* any explicit `NOTES` drawer into one `## Notes` section.
If Bryan wants physical grouping after living with this, add a
`capture.note_drawer` setting later — small, additive, no migration either
way. This is also the only reading compatible with `no-all-caps-for-drawers`
landing later: loose notes survive any drawer-title syntax change.

Consequence for capture-into-stepped-tasks: a new note to a task with steps
is a loose note in sorted position (after steps, before drawers — or after
links if the task keeps notes-above-steps style? pick one: **notes sort with
drawers-adjacent plain bullets, i.e. links < steps < notes/drawers < logs**,
and document it). No drawer is created as a side effect.

## 5. Capture and editing: keep `..`, add `[ ]` (amend cleanup bullet 6)

Verified free positions (prior synthesis, re-checked against
`docs/reference/cli/capture-rewrite.md` and `glossary:capture-alias`): `.`
is literal at bullet-body starts today, so `- ..` is free there, except
sealed project-note first-level `- .` (Move alias `- .` → `- ^`) and
item-start `..` (`.bashrc` escape). Cleanup's replacement — expand `- [`
→ `- [ ] ` with `<backspace>` undo — is genuinely nice for discoverability
(many users type `[ ]` unprompted; Obsidian Tasks users expect it), but
dropping `..` loses the fastest path (two keystrokes, no `Shift`) and the
symmetric `Ctrl+G T` toggle story for no grammar gain: hand-typed `[ ] ` is
*already* valid step syntax under this design, no expansion needed.

Recommendation: **support both.** Typing the second `.` of `- ..` where a
step may stand rewrites `..` → `[ ] ` via `bob capture-rewrite --cursor`
(undo restores dots); typing `[ ] ` directly just works and earns a one-time
`sigil_alias_tip` teaching `..`. Pasted text, templates, and `bob capture`
keep literal dots (alias rule, as with every alias). `Ctrl+G T` (Mac leader;
only `u` bound today) toggles exactly one leading `[ ] ` on eligible
bullets via `bob capture-rewrite --toggle-step` — bob decides, thin-client
rule holds (`decisions:mac-capture-is-a-thin-client`). Obsidian: **Toggle
step** nav command, same rule, no default chord (hotkey manager cannot bind
two-key chords; a CM6 leader is Bryan's call, not a blocker).

Draft grammar (v1, two authored levels stay — the mirror-decision reopen
clause "authored bullets gain a third level" is *not* triggered): `- [ ]
text` is valid at first level under a new task or note-less `@route+id`,
and in the same-line form `[ ] text @route+id`; nested under a step is
*refused in v1* with a teaching notice ("Steps are flat in v1 — make it a
sibling, or split the parent into a project"), while the recognizer already
parses deeper nesting structurally so v2 needs no migration. New refusals on
the bullet's byte range: step inside a drawer / on a `#drawer` route
("Drawers hold notes"), step under a note bullet, pre-checked step at capture
(capture authors open steps only).

Carry now: `Ctrl+Shift+T` splits an open step today (reuses
`src/native/task_split/plan.rs` shape: ID mint, alias, `LINKED FROM`,
placement after the owner's block). No new task-birth path.

## 6. Close, merge, promotion, and the three downstream tasks

**Close card (accept + extend).** Every managed Done gesture
(`Ctrl+Enter`, `Alt+]` into Done, capture `!note:id` / `x`, close labels —
`docs/task-dependencies.md` §12.1) whose closing tree holds ≥1 open
top-level step contributes a **Steps group, first** on the existing
successor card (before hand-offs: audit what closes before choosing what's
next). Defaults: every open top-level step **Done** (checked); fully ticked
tasks skip the group (folded one-liner, no interaction). Keys (reuse, don't
invent): `Ctrl+X` toggles Done ↔ Keep-open on the focused row (row-aware
footer), `Ctrl+Shift+X` marks Not-done (`[-]`) + optional reason,
`Space`/`Tab` = Keep-open-and-pull-in in one keystroke (collapses the
request's two-step trap), nested rows ride along non-actionable under their
root. Keep-open is split-at-close (stub `- [>] [[#^id|Alias]]` + back-link);
`Ctrl+J` parks/lands exactly as today
(`decisions:successor-jump-parks-the-walk`) — steps add rows, never a new
walk rule. Only managed Done gestures open the group; cancel/park/raw edits
use the reader rule (resolved stays resolved, open stays open, no card).

**Merge.** Task-target merges (`<`, `>`, all gestures through the shared
`plan_task_merge` in `src/native/task_merge/`) write **one step** (title +
copied children, live `^id` anchors copied with `[id::]` stripped outside
code, open-nested-task refusal preserved, source canceled with back-link).
Drawer/section-target merges stay notes (`glossary:task-drawer` contract).
This is one planner branch, not a new writer.

**Promotion (task → project).** Steps → `## Tasks` rows (status preserved:
`[x]` seeds a closed row, `[>]` seeds its linked task reference, `[-]`
seeds an obsolete note — no silent resurrection); loose notes + explicit
`NOTES` drawer → merged `## Notes`; drawers → same-named H2 sections;
managed lines/logs travel as today or abort losslessly. Reversal restores
drawers from H2; steps restore as steps. Reviewed, gated migration only
(`doctor` lists loose bullets that *look* step-like; Bryan ticks which
become steps;/generator never guesses) — no flag day.

**`^better-o`.** Falls out of §4.2: `o` inserts a sibling of the focused
row's kind at the sorted slot; `Ctrl+Shift+O` above it. No extra design.

**`^no-all-caps-for-drawers`.** The step definition is orthogonal to drawer
syntax (parent + checkbox, never title-casing), so it survives whatever
drawer marking replaces ALL-CAPS. One caution: do not ship stored `##` steps
— under any non-ALL-CAPS drawer scheme (`#name`, `name::`, …) a stored `##`
is one typo from a drawer/section reference. The checkbox has no such
neighbor. Sequence stands: steps first, drawer rename second, shared
`GRAMMAR_REVISION` bump each time, `!` on the train for each contract break
(`decisions:bob-cli-releases-ride-a-daily-train`).

**`^tasks-parent-projects` + `^task-to-project`.** Ship flat steps first;
then let a task parent a project for *real* nesting (task → project →
tasks) instead of recursive steps. Root/clock/type walks, Ready caps, and
the PRE→…→POST tiers (`decisions:recurring-occurrences-walk-when-due`)
then change in exactly one place (the walk's parent resolution), and steps
never need to nest. If nested steps ever land, they ride the already-reserved
`parent is a step` recognizer branch — no migration.

## 7. Recommended solution (phased v1)

**Store:** `- [ ]` / `[x]` / `[-]` / `[>]` under a `#task` line, single
level, no `#task`, no `[created::]`, optional trailing `^anchor`.

**Render (beautiful):** tag-marks `⌗⌗` after the checkbox in owner ink;
Obsidian checked/muted/strike for `[x]`, two small rules for `[-]`/`[>]`
with the `↗` live link on `[>]`; loose notes unadorned; optional derived
`⌗⌗ 2/4` progress chip on the owner line (walk-useful, cheap, additive).
Live Preview, Reading, capture `--dry-run` preview (`micro_task` span +
`depth`), and both successor cards share the glyph.

**Write paths:** capture grammar + `..` + `[ ]` typing + `Ctrl+G T` +
Obsidian toggle + `Ctrl+Enter` tick + `Ctrl+Shift+T` carry + close-card
group + merge branch + split reuse + promotion mapping + `o` slots, all
behind capability gates across the two close engines (Rust capture, JS
cycler) and three card surfaces (Obsidian picker, cycler, Mac), `bob`
owning every decision.

**Guardrails (reliable):** one shared `isStepLine` helper used by the
cycler, `freshnessTaskStatus`
(`plugins/bob-ledger-tools/src/080-freshness-placement.js:153` — matches any
checkbox today, needs the guard), tag-marks, walk, reconcile, and
`projects sync`; `GRAMMAR_REVISION` 28 → 29; `!` release-train mark; reviewed
migration + lint, never silent rewrite.

**Docs/memory:** new glossary `task-step` (redirect `micro-task`), updated
`capture-alias` (`..`), new `docs/task-steps.md` (contract, states, order,
grammar, card keys, merge/promotion maps), reopen notes on
`capture-bullets-mirror-the-task-block` (third level *not* taken) and the
drawers decision if titles change.

## 8. What I would explicitly not build

- Stored `##`/`###` runs, or any depth in bytes.
- A physical `NOTES` drawer by default, or auto-creation on any condition.
- A `req`/`REQ:`/`TASK:` marker or any `:`-final marker (drawer-title
  collision, `TASKS` near-trap).
- Nested actionable steps, step lanes/freshness/priority/schedule/deps/links,
  step walk rows, or step stats in v1.
- A new close panel, four new global keymaps, or any `Ctrl+X = Cut`
  conflict: reuse the successor picker.
- Silent vault rewrites, or interpreting any existing loose bullet without
  Bryan's explicit review.

## 9. Open questions for Bryan (all reversible post-v1)

1. Name: **step** (recommended) vs keeping **micro task** vs your **req** —
   one-word call; everything else follows.
2. Progress chip (`⌗⌗ 2/4` on the owner): include in v1 or defer as the
   obvious polish follow-up?
3. Obsidian `Ctrl+G T` chord via a CM6 leader: worth it, or is the nav
   command + `..` enough?
4. `capture.note_drawer` setting later: do you still want the physical-notes
   option after living with loose notes + sorting?

---

*Verification notes (this checkout, read-only): `GRAMMAR_REVISION` 28
(`src/native/capture_language/mod.rs:63`); drawer-title `:` rule
(`src/native/capture_drawers.rs`); `global_filter` gating
(`src/native/task_status_groups/mod.rs:331`,
`src/native/stats/compute.rs:2709-2836`); split promotes plain unchecked
checkboxes (`docs/task-split.md` §1); successor card keymap and grouping
(`docs/task-dependencies.md` §12.22); tag-marks renderer
(`docs/task-tag-marks.md`); thin-client rule
(`decisions:mac-capture-is-a-thin-client`); mirror rule and its reopen clause
(`decisions:capture-bullets-mirror-the-task-block`); `o` ordering requirement
in `^better-o`; single-level + `##`-only + `NOTES`-auto-create + no-tick
proposals in `^micro-tasks-cleanup`; cancelation rationale in `^micro-tasks`
Rotten Log 2026-11-21 and epic bead `bob-cli-of` (IN_PROGRESS, canceled
agent-side). No peer report from this swarm was located, opened, or read.*

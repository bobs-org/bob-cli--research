# Keep-moving marks: a `⏭ N` echo on ledger Task Links for leaf projects

*Researcher: cld · 2026-11-11 · Scope: bob-cli (`docs/task-dependencies.md` §12.15,
`src/native/task_complete/keep_moving.rs`), bob-plugins (`bob-ledger-tools`,
`task-status-cycler`), and the live vault (read-only; experiments ran on a scratch copy).*

## TL;DR

1. **The idea is good.** It is the natural sibling of the 🔑 frees mark. 🔑 previews
   the successor picker's **Hand-offs** group, and the new mark previews its
   **Keep ‹N› moving** group. `docs/frees-marks.md` already leaves room for it: it
   lists "keep-moving offers (⏭, §12.15)" under *What is deliberately not counted*.
2. **Your motivating example would lie today.** `job_email_recruiters.md` has
   `parent: "[[job]]"`, and `job.md` is an **area**. That makes
   `job_email_recruiters` a *top-level* project, which is its own root parent. Under
   §12.15 K2, vector LP2, the glossary, and the definition you gave the keep-moving
   plan ("project notes that are not root parents"), it is **not a leaf**. I dry-ran the
   close on a scratch copy of the vault, and
   `bob capture --dry-run '!job_email_recruiters:bryan-stephen-luzern-risk'` completes
   the task and **offers nothing**. With the parent changed to the project `job_2026`,
   the same dry run returns exactly `keep_moving: 4`. A badge showing `4` on that link
   today would promise a picker that never appears.
3. **The literal count formula doesn't match the picker either.** "Ready/Pending/Next
   tasks in the leaf project with no task links in today's file" differs from what the
   picker shows in three ways:
   - the picker opens only when the close drains the project's **last** live link
     (K4);
   - tasks linked only under *closed* Pomodoros earlier today **are** offered (KM4);
   - Blocked, future-scheduled, and `#hide` residents are folded out.

   The number should be **defined as the size of the keep-moving group the close would
   open**. That is a parity invariant, like 🔑's parity with BLOCKS.
4. **Recommended solution.** Ship a quiet **`⏭ N` keep-moving mark** in bob-ledger-tools,
   a pixel-level sibling of 🔑:
   - it uses the glyph keep-moving already owns (the `skip-forward` silhouette) in the
     existing Next status token;
   - it appears only on the link whose close would actually open the group;
   - its tooltip previews the rows using the §12.15 copy.

   **Settle the leaf question before building it.** I recommend amending K2 from "not a
   root parent" to "not an **umbrella**", where an umbrella is a root project with open
   sub-projects. That makes your example work, keeps `bob`, `sase`, `sase_blog`, and
   `job_2026` out, and stops a reporting flag (`root: true`) from deciding offer
   behavior. There is also a zero-code option: reparent `job_email_recruiters` under
   `job_2026`.

---

## 1. What exists today

### 1.1 The 🔑 frees mark (the precedent)

- **Code:** bob-plugins `plugins/bob-ledger-tools/src/141b-frees-marks.js` (pure core),
  `271b-plugin-frees-marks.js` (Live Preview, Reading view, refresh, toggle), and the
  CSS in `styles.css`. Tests are `scripts/test-ledger-tools-frees-marks.cjs` plus a
  real-Obsidian e2e. It landed in `f824dd1` (bead `bob-cli-g1.2`) and was repaired in
  `4ec76dc`.
- **Contract:** bob-cli `docs/frees-marks.md`. Its principles are the template here:
  - **Display-only.** The mark never writes.
  - **Truthful or neutral.** Uncertainty means no mark, and no warning glyph is ever
    shown.
  - **One rule shared with BLOCKS.** A test asserts the parity.
  - **Which-links gates (FL1–FL16).** Today's daily note only, dedicated rows under
    open Pomodoros only. Struck, embedded, prose, nested, closed-entry, and Events rows
    get no mark.
  - **Anatomy:** compact `🔑 N`, muted, borderless, `0.8em`, `side: 2` after 🔓.
  - **Behavior:** a tick animation on change, a session toggle, and a ≤25 ms build for
    200 links and 2,000 tasks.

### 1.2 Keep-moving offers (what the new mark predicts)

`docs/task-dependencies.md` §12.15–§12.17 defines the rule. Rust implements it in
`src/native/task_complete/keep_moving.rs` (`is_leaf_project`, `classify_keep_moving`).
The JS cycler implements it in `plugins/task-status-cycler/src/089c-successor-keep-moving.js`
(`successorLeafProject`, `planSuccessorKeepMoving`). The trigger is K1–K8: a managed
Done gesture closes the task behind leaf project N's **last live link today**, N's
`^prj` is open and unblocked, N isn't emptied, and `plan.keep_moving` and
`plan.link_unblocked` are both on. The group offers N's Pending → Next → Ready residents
and folds the blocked, later-scheduled, and hidden ones.

The visual identity is already decided and shipped:

- **Glyph:** ⏭. Obsidian uses lucide `skip-forward` (the picker title in
  `206-successor-picker-modal.js:111`), and the Mac uses SF Symbol `forward.end.fill`.
- **Color:** the existing **Next status token**, `var(--task-status-next, var(--color-green))`.
  It already drives the picker's keep-moving accent rule and the notice card
  (`bob-navigation-hotkeys/styles.css:1710–1720, 3082–3097`).
- **Copy:** "Keep ‹N› moving", "‹T› was the last ‹N› task planned today", and
  "ready in ‹N› · not dependents". It never uses 🔓 or the word "unblocked".

---

## 2. Verified findings

### F1. The example project is not a leaf, so closing that task offers nothing

```text
job_email_recruiters.md   parent: "[[job]]"   type: "[[project]]"   (no root:)
job.md                    parent: "[[area]]"  type: "[[area]]"
```

Both engines reject the example project:

- **Rust:** `is_leaf_project` → `home.root_parent != home.key` is false.
- **JS:** `successorLeafProject` returns `false` at the first parent, because
  `type === "area"`.

I ran this experiment on a scratch copy of the vault's Markdown (`BOB_DIR`,
`BOB_DAY_FILE`, `BOB_CONFIG_FILE`, and isolated `XDG_*`), never on `~/bob`:

| Variant of `job_email_recruiters.md` | `bob capture --dry-run '!job_email_recruiters:bryan-stephen-luzern-risk'` |
| --- | --- |
| As-is (`parent: [[job]]`, an area) | `would complete [*] → [x] …` plus the ledger line. **No offer of any kind.** |
| `parent: [[sase_blog]]` (a project) | `Keep job_email_recruiters moving · … was its last task planned today`, then offers 1–4 (all `Next`) |
| `parent: [[job_2026]]` (a project) | JSON `task_complete.keep_moving` has **4** rows; `pull_in.offer_count = 4`, group `Keep ‹job_email_recruiters› moving` |

So you are right that the count is 4, but only *if* the project were a leaf. Two facts
about the vault make the reparent option look natural:

- `job_2026.md` ("Get hired by a great, forward-thinking, AI-first company!") is a
  top-level project that already has one sub-project, `job_2026_apply_29`.
- `job_email_recruiters` was created this morning from `job#^create-email-replies-prj`.
  Promoting an *area* task always yields a top-level project. That is a systematic
  reason small, finite projects miss keep-moving (see A3).

### F2. The literal formula is not what the picker shows

| Your formula says | The picker actually does (§12.15) | Consequence for a badge using the formula |
| --- | --- | --- |
| Count the project's P/N/R tasks that have no task links today | **K4:** if *any* other open N task (or `^prj`) is live-linked today, **no group at all** | Two links to N would both show `⏭ 4`, and closing either one shows nothing |
| "no task links … in today's daily file" | Links that are struck or sit under **closed** Pomodoros don't count (KM3/KM4), so a task worked earlier today **is offered** | The formula undercounts those tasks |
| All ready/pending/next | Blocked (`[?]`, own open prerequisite, `#prj_is_blocked`), `scheduled` after today, and whole-token `#hide` are **folded**; `^prj` is never offered | The formula overcounts these |
| — | Direct dependents of the closed task are offered in **Hand-offs**, not keep-moving | No overlap with ⏭: before the close they are Blocked, and 🔑 already counts them |

### F3. With the strict definition, the mark would render nowhere today

I ran a scan of the scratch vault: lexical, with dependency ids resolved vault-wide, and
excluding `done/`, `_conflicts/`, and `_templates/`.

- **34** active leaf project notes. **None** has a single offerable resident: all
  **242** open residents are Blocked. Most are `sase_*` sub-projects waiting on
  dependency chains.
- **8** active root projects. Only roots currently have offerable work: `bob` (11),
  `job_email_recruiters` (5, including the task you'd close), `sase` (3), and
  `sase_blog` (1).
- Leaf links are still common historically. Leaf-project Task Links appear in **77 of
  103** daily ledgers (Aug–Nov 2026), about 508 leaf versus 1,254 root project links
  after mapping `done/X_done` archives back to `X`. So the feature is real, but today's
  vault would show zero marks.

### F4. Root projects split cleanly into umbrellas and standalone projects

| Root project | Projects reporting under it | Offerable now | Umbrella? |
| --- | --- | --- | --- |
| `sase.md` | 77 | 3 | yes |
| `bob.md` | 7 (open: `bob_easy_task_moves`, `bob_git`) | 11 | yes |
| `sase_blog.md` (`root: true`) | 3 (open: `sase_pre_blog`) | 1 | yes |
| `job_2026.md` | 1 (`job_2026_apply_29`) | 0 | yes |
| `job_email_recruiters.md` | 0 | 5 | **no** |
| `dev_plex_hack_patch.md` | 0 | 0 | no |
| `gkeep_gdocs_inbox_dump.md` | 0 | 0 | no |
| `needs_attn_tasks.md` | 0 | 0 | no |

Every umbrella's `^prj` already carries a machine-owned
`🧩 **Sub-projects:** [[child]] • ~~[[closed]]~~ ✅` line, maintained by
`bob projects sync`. `docs/projects.md` notes that close gestures already read
sub-projects "from the marker line rather than child notes' `parent:`". So an umbrella
test costs **zero extra I/O** in Rust and in the cycler, because both already hold N's
staged text.

### F5. bob-ledger-tools already has the ingredients

The new mark can reuse these pieces:

- **Tasks memo** (`freshnessEnsureMemo`): statuses, tags, ids, `dependsOn`, and
  schedules for every resident.
- **Link resolution:** `freesMarkLinkedTask` and `unblockedGlyphLinkedTask`, which
  give a unique, open target.
- **Today index:** `computeTodayLinks` and `resolveTodayKeys` in `060-today.js`.
  This index already shares conformance vectors with Rust's `today_tasks`, so it can
  answer "all live links today" for K4.
- **R2 root-parent walk:** `pomodoroHomeResolve` (`142-pomodoro-home-chips.js`). It
  already drives the home chips you see after the Pomodoro name.
- **Dependency helpers:** the blocks helpers prove "own open prerequisite", with R4
  "unresolved never blocks".
- **Config readers:** `320-plan-lane-and-config.js`, which can read `plan.keep_moving`
  and `plan.link_unblocked` the way the cycler's stat-keyed `loadKeepMoving` does.
- **Live Preview and Reading machinery:** the 🔑 code, including the bounded LRU tick
  and the coalesced refresh.

Plugins can't share source. `scripts/build-plugins.mjs` refuses fragment paths outside a
plugin's `src/`. Parity therefore has to come from shared vectors and cross-plugin
tests. The cycler tests already `require("../plugins/bob-ledger-tools/main.js").helpers`,
so this pattern exists.

There are **zero** `![[…]]` embed rows in Aug–Nov ledgers, so excluding embeds (as 🔑
does) costs nothing in practice.

### F6. Widget order on the link end

- 🔓 sits at `side: 1` and 🔑 at `side: 2`.
- The off-clock chip sits at `side: 3` (`271c-plugin-off-clock-link-chips.js:203`).

The new mark belongs between 🔑 and the off chip.

---

## 3. Critique: is this a good idea?

**Yes, with conditions.** Here is the case for it:

- **It makes a pause predictable.** A picker that pops up mid-flow is less jarring when
  you saw it coming. "Closing this keeps job_email_recruiters moving with 4" turns the
  interruption into a choice you made in advance.
- **It shows the most useful planning fact: "this is the last thing keeping N planned
  today."** The mark's *presence* says that, and the count says how much is left. This
  rewards the healthy "baton" pattern: link one task per project, and let the offer
  pull the next one.
- **It completes a set.** 🔓 says something freed this task, 🔑 says this task frees
  dependents, and ⏭ says this task keeps its project moving. Together they make the
  ledger read as a forecast of the successor picker.

The risks, and how this design answers each:

1. **A broken promise is worse than no mark.** Every ledger mark trades on trust.
   Showing `4` where the picker shows nothing (F1, F2) would teach you to ignore all of
   them. *Answer:* define N by parity with the planner, and show the mark only when the
   group would open.
2. **It would be invisible today.** Under the strict leaf rule, no link in today's
   vault qualifies (F3), and the one you care about is a root (F1). *Answer:* settle
   K2 first. Building the mark without that decision ships a feature you won't see.
3. **Ledger rows are getting crowded.** A row can already carry a ◐ ring, a type mark,
   an Event time pill, 🔓, 🔑, an off chip, and a mail badge, with home chips on the
   entry line. *Answer:* the mark is absent by default. It appears on at most one link
   per eligible project, only when its count is ≥ 1, in the same quiet pill grammar as
   🔑, with a session toggle.
4. **There would be a fourth reader of the K-rules.** Rust, the cycler, and now
   ledger-tools would all evaluate the rule. *Answer:* shared KB vectors run against
   ledger-tools *and* `planSuccessorKeepMoving`, plus a live audit against
   `bob capture --dry-run -f json`.

**What I would do differently from the request:**

- define the number by parity with the planner rather than by the formula;
- show the mark only on the last-planned link;
- fix the leaf/root mismatch at the rule level;
- reuse the established ⏭ identity instead of inventing a "similar" icon.

---

## 4. Requirement adjustments (called out explicitly)

| # | Your requirement | Adjusted requirement | Why |
| --- | --- | --- | --- |
| **A1** | Count = other ready/pending/next tasks in the leaf project with no task links today | **N = the number of rows the `Keep ‹N› moving` group would offer if this task were completed now** (Ctrl+Enter, Alt+], `!`, or an `x` that completes only this task) | This is the stated purpose ("so I know how many tasks will appear"). It folds Blocked, later-scheduled, and hidden tasks, counts tasks linked only under closed Pomodoros, and excludes `^prj` and sub-project residents (F2) |
| **A2** | Show on task links into leaf projects | Show **only on the link(s) whose close would open the group**: every *other* live link today into N targets a closed task, or none exists (K4). If two open N tasks are planned, **neither** gets a mark. When one closes, the mark appears on the survivor with a single pop (the "baton pass") | Any other choice shows a number that the next close won't honor |
| **A3** | "Leaf project" | Eligibility = the keep-moving K2 predicate, whatever it is. **Recommended:** amend K2 to "**not an umbrella**" (§6). **Fallback:** keep strict K2 and reparent `job_email_recruiters` under `job_2026` | Your example is a top-level project (F1), and today all strict leaves are blocked (F3) |
| **A4** | "A similar icon" | Use the **keep-moving glyph**, the `skip-forward` silhouette, tinted with the **Next status token**, inside the same pill grammar as `🔑 N` | One glyph per concept on every surface: the mark looks like the picker header it predicts. No new hex values (the §12.15 rule) |
| **A5** | (implicit) The mark predicts the offer | **Truthful or neutral:** a shown mark is a promise, but no mark is not a guarantee | Example: an `x` that completes two N links at once still opens a group, though neither link was "last". Same stance as 🔑 |
| **A6** | (implicit) | Inherit 🔑's FL gates exactly: today's canonical daily note, open entries, dedicated rows; no embeds, struck, prose, closed, or Events rows | Consistency, plus zero embeds in practice (F5) |
| **A7** | (implicit) | **Mod+click opens the project note N** (where the offered rows live); a plain click only places the caret | X is already one click away on the link itself |

---

## 5. Design: the `⏭ N` keep-moving mark

### 5.1 What you see (your example, once A3 is resolved)

```text
- [ ] () — WRITE   ○ job_email_recruiters · sase_blog
	- job_email_recruiters#^bryan-stephen-luzern-risk  ⏭ 4
	- ◐ sase_blog#^s0-spike  🔑 4
```

`sase_blog` is an umbrella, so `s0-spike` gets no ⏭, only its existing 🔑 4.

A link with all three marks reads past → dependents → project, left to right:

```text
	- ◐ bob_git#^wire-hooks 🔓 🔑 1 ⏭ 3
```

The baton pass: two `job_email_recruiters` links are planned, so neither shows a mark.
After `^ecogpt` closes (and opens no picker), the survivor gains `⏭ 3` with one 180 ms
pop:

```text
	- ~~job_email_recruiters#^ecogpt~~
	- job_email_recruiters#^ray-lyles  ⏭ 3        ← pops in
```

### 5.2 Hover tooltip (`aria-label`; no `::`; §12.15 copy)

```text
Closing this offers 4 tasks to keep job_email_recruiters moving
It's the last job_email_recruiters task planned today
• ✉️ Founding Engineer at EcoGPT · Roej Hollon-Cal… · Next
• ✉️ 🔥 Bryan — your Python/release tooling made m… · Next
• ✉️ Product Engineer · Dan Dowd · Next
+1 more
ready in job_email_recruiters · not dependents
Not offered: 2 blocked · 1 scheduled later · 1 hidden     (only when non-zero)
```

- **Row order:** the picker's order, Pending → Next → Ready, then line in N.
- **Titles:** `dependencyCleanTaskText`, cut at 48 characters (47 plus `…`), and
  always with the **lane name**, never a raw status symbol (§12.15).
- **Lead and contrast:** the tooltip leads with *why* and ends with "not dependents".
  It never says 🔓 or "unblocked".

### 5.3 Rule (pure core, mirrors K1–K8 on the pre-close state)

```text
X  = the open #task the link resolves to (🔑's unique-target resolution)
N  = X's note (residence);  R = N's open ^prj

Gates (all must hold, or no mark):
  G1  plan.keep_moving ∧ plan.link_unblocked                         (K8; config, default true)
  G2  N is a recognized active project: outside done/, type project,
      non-terminal, exactly one open ^prj R                          (K1)
  G3  KEEP_MOVING_PROJECT(N): LEAF(N) under current K2,
      or ¬UMBRELLA(N) if A3 is adopted                                (K2)
  G4  X ≠ R                                                          (K3)
  G5  R is not Blocked: status ≠ '?', no own open prerequisite,
      no future scheduled, no #prj_is_blocked                        (K5, K7)
  G6  LAST PLANNED: every live link in today's open Pomodoros that
      targets an OPEN task of N targets X. Links to R count; links
      to closed tasks and to N's sub-project residents don't.        (K4)

Count:
  OFFER = { t ∈ open #task residents of N, t ∉ {X, R} :
            status ∈ {' ', '*', '/'},
            no own open prerequisite (memo-resolved; unresolved ids never block, R4),
            no #prj_is_blocked, no scheduled after today, no whole-token #hide }
  FOLD  = blocked / scheduled-later / hidden counts         (tooltip only)
  mark ⇔ G1..G6 ∧ |OFFER| ≥ 1;   pill text = |OFFER|
```

Why the pre-close state is enough:

- **Hand-off overlap.** A resident freed by X is Blocked before the close, so it
  isn't counted. After the close, the picker dedups it into Hand-offs. The picker's
  ⏭ group equals |OFFER| with no overlap, and 🔑 counts the Hand-offs.
- **K6 (emptied project).** If X is N's last open task, OFFER is empty, so there is no
  mark. The picker shows a project_finished pull-in instead.
- **K7.** It is implied by G5.

**Parity invariant (the reliability spine).** For every rendered mark, the pill's N
equals the length of `task_complete.keep_moving` from
`bob capture --dry-run -f json '!<N>:<X block id>'`. It also equals the
`planSuccessorKeepMoving` mark count for `closed = [X]` on the same day text. The mark
is absent whenever that group is empty.

### 5.4 Anatomy and look

The host element is `span.bob-keep-moving-mark[role=img][aria-label][data-tooltip-position=top][data-count][data-block-id][data-project]`.
It contains `span.bob-keep-moving-mark-glyph` followed by the count text. It has the
same metrics as `.bob-frees-mark`, so the two pills sit as twins:

```css
.bob-keep-moving-mark {            /* identical box model to .bob-frees-mark */
  display: inline-flex; align-items: baseline; gap: 0.22em;
  margin-inline-start: 0.4em; padding: 0 0.42em; border-radius: 999px;
  font-family: var(--font-interface); font-size: 0.8em;
  font-variant-numeric: tabular-nums; line-height: 1; white-space: nowrap;
  color: var(--bob-keep-moving-mark-color, var(--text-muted));
  user-select: none; cursor: default; print-color-adjust: exact;
  transition: background-color 120ms ease, color 120ms ease;
}
.bob-keep-moving-mark-glyph {      /* filled skip-forward silhouette, Next token */
  inline-size: 0.95em; block-size: 0.95em; align-self: center;
  background-color: var(--task-status-next, var(--color-green));
  -webkit-mask: var(--bob-keep-moving-glyph) center / contain no-repeat;
          mask: var(--bob-keep-moving-glyph) center / contain no-repeat;
}
.bob-keep-moving-mark:hover {
  color: var(--text-normal);
  background-color: color-mix(in srgb, var(--task-status-next, var(--color-green)) 12%, transparent);
}
/* tick animation, reduced-motion, and forced-colors (glyph → CanvasText) copy 🔑 */
body:not(.bob-keep-moving-marks) .bob-keep-moving-mark { display: none; }
```

Why a **mask glyph rather than the ⏭️ emoji**:

- On macOS and iOS, Apple Color Emoji draws U+23ED as a **blue button tile**. At 12 px
  it is the loudest thing on the row, and its blue would compete with your theme's Next
  color.
- A filled `skip-forward` silhouette (triangle plus bar, the SF `forward.end.fill`
  shape) is crisp at 12 px and follows the theme through `--task-status-next`. It
  matches the picker's `skip-forward` header icon, so the mark *looks like* the group
  it predicts.
- It is listener-free in Reading and Dataview round-trips, like the existing
  `--bob-task-link-glyph-*` masks in `styles.css`.

At rest, only the glyph carries color. The count stays muted, which matches 🔑's "the
emoji is the only color" rule.

### 5.5 Placement, interaction, motion, liveness, toggle

- **Live Preview:** a zero-width widget at the link end, after 🔑 (`side: 2`) and
  before the off chip (`side: 3`). Simplest is to renumber the off chip to `side: 4`
  and give ⏭ `side: 3` (one-line change, pinned by a placement vector). The mark never
  rebuilds on selection alone.
- **Reading view:** insert after `span.bob-frees-mark` if present, else after
  `span.bob-unblocked-glyph`, else after `a.internal-link` (or its sole-child
  `del`/`s` wrapper).
- **Click:** places the caret. **Mod+click** opens N in a new tab (A7). No tab stop,
  no live region.
- **Motion:** a per-view LRU keyed by X's `path\0blockId`, with "no mark" stored as 0.
  A change to a new N ≥ 1 ticks once for 180 ms; this produces the baton-pass pop. The
  mark never animates on first paint, scroll, or in Reading view, and reduced motion
  turns the tick off.
- **Liveness:** one coalesced refresh of about 120 ms, triggered by:
  - the Tasks `cache-update`, which covers residents changing anywhere;
  - metadataCache `changed` for today's daily note (links added or struck) and for
    any candidate N (frontmatter or `🧩 Sub-projects` changes);
  - midnight rollover;
  - the toggle;
  - a config stat change.
- **Toggle:** `toggle-keep-moving-marks`, "Toggle Task Link keep-moving marks". It is a
  session toggle, default on, using `applyMarkGateClass("bob-keep-moving-marks", on)`
  plus `registerMarkGatePopoutSync`. There is no API namespace in v1.
- **Performance:**
  - Group links by N, and compute G2–G5 and OFFER once per N per build.
  - Take the live-link set from the Today index once per build.
  - Never read from disk during render. Under A3, the `🧩 Sub-projects` line comes from
    a small mtime-keyed async cache of candidate N notes, and a cold entry means no mark
    yet (truthful or neutral).
  - Keep 🔑's ≤ 25 ms budget for 200 links and 2,000 tasks.

### 5.6 Conformance vectors (new `docs/keep-moving-marks.md`)

| # | Situation (leaf N with open, unblocked R; X live-linked under an open entry) | Mark |
| --- | --- | --- |
| KB1 | N has Pending P, Next B, Ready A; X is the only live N link | `⏭ 3`; tooltip rows P, B, A |
| KB2 | Open N task U is also live-linked | none on X or U; after U closes, X gets `⏭ …` with one tick |
| KB3 | U's link is struck, or sits under a closed entry | `⏭` counts U if U is open and offerable |
| KB4 | R (`^prj`) is live-linked today | none |
| KB5 | N is top-level, `root: true`, or orphan | strict K2: none. Amended K2: none only if N has an open `🧩 Sub-projects` entry |
| KB6 | Every other resident is Blocked, later-scheduled, or `#hide` | none |
| KB7 | X is N's last open task | none (that close produces a project_finished pull-in) |
| KB8 | Resident D depends only on X | D is not in ⏭ (it is in 🔑) |
| KB9 | R has an open prerequisite, a future date, or `#prj_is_blocked` | none |
| KB10 | `plan.keep_moving: false` or `plan.link_unblocked: false` | none |
| KB11 | X is closed, unresolved, or ambiguous; memo cold; toggle off | none |
| KB12 | Link is struck, embedded, prose, nested, under a closed entry, in Events, or in another daily note | none (🔑's FL gates) |
| KB13 | Same X linked twice | both rows marked |
| KB14 | Resident's `[dependsOn::]` names a closed task, or an unresolved id | counted |
| KB15 | `#ref` resident, nested subtask, recurring task due today, `scheduled` today | counted |
| KB16 | Residents of N's sub-projects | not counted |
| KB17 | X lives in a daily note, area, inbox, or `done/` | none |
| KB18 | **Parity:** every KB row | pill N == `planSuccessorKeepMoving({closed:[X]})` row count == `bob capture --dry-run -f json '!N:x'` `keep_moving.length` |

---

## 6. The leaf question (A3) in detail

| Option | Example gets `⏭ 4`? | Behavior change | Cost | Verdict |
| --- | --- | --- | --- | --- |
| **S. Strict K2 (as shipped)** | ❌ (and no picker) | none | The mark renders nowhere today (F3), and every area-promoted finite project is excluded forever | Only if you'd rather fix the vault |
| **R. Reparent `job_email_recruiters` → `job_2026`** | ✅ (verified: 4) | none in code | One frontmatter edit. Its time then rolls up to `job_2026`, and the home chip reads `job_2026` | Good immediate fix; doesn't solve the general gap |
| **U. Amend K2: not an *umbrella*** (recommended) | ✅ | `job_email_recruiters`, `dev_plex_hack_patch`, `gkeep_gdocs_inbox_dump`, and `needs_attn_tasks` gain keep-moving offers. `bob`, `sase`, `sase_blog`, and `job_2026` stay out | A contract, Rust, and cycler change, plus a decision record | **Best rule**; see below |
| **D. Drop leafness entirely** | ✅ | `bob` (11 rows) and `sase` would offer every time their last planned link closes | Noisy | Reject |

**Proposed definition:**

```text
UMBRELLA(N)           ⇔  R2root(N) = N  ∧  N's ^prj "🧩 Sub-projects:" line lists ≥1 open (unstruck) child
KEEP_MOVING_PROJECT(N) ⇔  project(N) ∧ ¬UMBRELLA(N)
```

This replaces the K2 LEAF(N) test (`R2root(N) ≠ N`) and keeps the "Leaf Project" term
with a tighter meaning:

> a project note that no open project reports under.

Every current leaf stays a leaf. LP1, LP4, LP7–LP12 are unchanged, and LP2 and LP3
still say no because `sase` and `sase_blog` have open sub-projects. New vectors:

- **LP13:** a top-level project with no open sub-projects is a leaf.
- **LP14:** a `root: true` sub-project with no open sub-projects is a leaf.
- **LP15:** a top-level project whose line lists only struck ✅ children is a leaf.
- **LP16:** a stale line (a child created since the last sync) follows the line, as
  §12.10 close gestures already do.
- **LP6** (orphan) becomes a leaf when it has no open sub-projects.

Why U beats S:

- It keeps the original intent: umbrella projects like `bob` and `sase` behave like
  areas and shouldn't trigger pull pickers.
- It fixes the accidental exclusion of standalone finite projects. That accident is
  structural, because promoting an area task always creates a top-level project.
- It decouples offer behavior from a reporting flag. The keep-moving plan itself
  recorded as a cost that "`root: true` also decides leafness".
- It is cheap. The marker line is already in N's staged text, which keeps §12.15's
  G4/G5 budget at "no extra I/O".

Known cost of U: if `bob`'s two open sub-projects close, `bob` stops being an umbrella,
and closing the last planned `bob` link would offer about 11 rows. If you don't want
that, add a per-note `keep_moving: false` opt-out later. I would not add it in v1.

U changes accepted behavior, so it needs your sign-off and a **new decision record**:
something like `decisions:keep-moving-skips-only-umbrellas`, which partly supersedes the
leaf definition in §12.15 and the `glossary:leaf-project` strand. Write it through
`/sase_memory_write`.

---

## 7. Alternatives considered

| Alternative | Why not (or not now) |
| --- | --- |
| One combined "successor preview" pill (`↪ 5` = hand-offs + keep-moving) | §12.15 requires keep-moving to always read as "not dependents", never mixed with 🔓/🔑 wording. 🔑 has shipped, and two marks mirror the picker's two groups |
| Show the count on *every* link into N | It promises a picker that won't appear (K4) |
| Put the count on the Pomodoro's home chip | The chip names the **root parent**, not the leaf, which is the wrong grain. The trigger is per task close |
| Status-footer hint when the caret is on a link (`Ctrl+Enter → ⏭ 4 · 🔑 1`) | Not glanceable, and the footer already hosts review. Worth adding later as a complement |
| Ledger-tools calls a cycler `api.keepMoving.preview()` at render | Render must be synchronous and disk-free, while the planner wants note texts and a dependents snapshot. Prefer a memo-based port plus parity tests, as 🔑 did with BLOCKS |
| Rust-computed count in a JSON payload | Needed only for Mac surfaces (the idle agenda, the Task Card). It stays deferred, as frees-marks defers its Mac echo |
| Use the ⏭️ emoji like 🔑 uses the key emoji | Apple renders it as a blue button tile, too loud at 12 px (§5.4) |

---

## 8. Implementation plan

0. **Decide A3** (you): U (recommended), R (reparent only), or S.
1. **Contract (bob-cli docs):**
   - new `docs/keep-moving-marks.md`, a display contract cloned from
     `frees-marks.md`, with the KB vectors, the tooltip vectors, placement vectors
     (after 🔑, before the off chip), and the parity invariant;
   - cross-link it from `frees-marks.md` → *What is deliberately not counted*;
   - if U: update §12.15 K2, LP13–LP16, `docs/pomodoro-homes.md` and
     `docs/projects.md` (the `root:` note), the glossary strand, and the decision
     record.
2. **Engines, only if U:**
   - Rust: `is_leaf_project` gets the umbrella check on `contents` (zero I/O), plus
     LP tests in `keep_moving_tests.rs`;
   - cycler: `successorLeafProject(app, path)` needs N's text (the planner already
     holds `noteTexts`), plus vectors.

   The JSON stays additive (no `!`), and the commit leaves `Cargo.toml` and
   `CHANGELOG.md` alone (the release-train rule).
3. **bob-ledger-tools mark**, comparable in size to 🔑 (about 0.5k lines of core, 0.8k
   of plugin, 0.8k of tests in `f824dd1`), and mostly a copy-adapt:
   - `src/141d-keep-moving-marks.js` (pure: gates, OFFER, tooltip, DOM builder,
     widget);
   - `src/271d-plugin-keep-moving-marks.js` (LP extension, Reading sweep, refresh,
     toggle, the async Sub-projects cache);
   - CSS beside `.bob-frees-mark`;
   - `scripts/test-ledger-tools-keep-moving-marks.cjs` (KB vectors);
   - **`scripts/test-keep-moving-marks-parity.cjs`**, which loads both plugins'
     helpers and asserts KB18 on every fixture;
   - a real-Obsidian e2e: light and dark, Live Preview and Reading, both-marks order,
     the baton-pass timing, and toggle row height;
   - the plugin docs row, the manifest bump, `npm run build`, and `bob plugins sync`.
4. **Live parity audit (one-time, scratch vault):** for each marked link, run
   `bob capture --dry-run -f json '!N:x'` and compare `keep_moving.length`.
5. **Deferred, with triggers:**
   - Mac idle-agenda echo (when you ask; it needs a Rust count);
   - the footer hint;
   - a per-note `keep_moving: false` opt-out (if U makes `bob` noisy).

Today's task `bob#^leaf-task-link-icon` ("Make it clear how many tasks succeed a task
link corresponding w/ leaf project!") is the natural home for this work.

---

## 9. Open questions for you

1. **K2:** amend to "not an umbrella" (U), or keep strict leaves and reparent
   `job_email_recruiters` under `job_2026` (R)?
2. **Once `bob` has no open sub-projects,** should closing its last planned link offer
   its ready tasks? Under U it would.
3. **Mod+click:** should it open the project note (my pick) or the task block?
4. **Tooltip:** is the "Not offered: …" fold line worth its height, or should it only
   appear when nothing would be offered? (By rule, nothing-offered means no mark at all,
   so the line only ever accompanies a positive count.)

---

## 10. Recommended solution

1. **Build the `⏭ N` keep-moving mark** in bob-ledger-tools as the sibling of 🔑:
   - **Number:** N is *defined* as the size of the `Keep ‹N› moving` group that
     completing the linked task would open now (A1), backed by the KB18 parity
     invariant against both the cycler planner and `bob capture --dry-run`.
   - **Where:** shown only on the last-planned link into an eligible project, with a
     one-shot pop when the baton passes (A2), and no mark when uncertain.
   - **Look:** a filled `skip-forward` silhouette in `--task-status-next` with a muted
     tabular count, in 🔑's exact pill metrics, placed after 🔑 and before the off chip.
   - **Tooltip:** the §12.15 copy ("Closing this offers 4 tasks to keep ‹N› moving ·
     It's the last ‹N› task planned today · … · ready in ‹N› · not dependents").
   - **Controls:** a session toggle, default on.
2. **First, amend K2 to "not an umbrella"** (a root project whose `^prj` Sub-projects
   line lists an open child). Record it as a new decision. This makes your
   `job_email_recruiters` example show `⏭ 4` and actually offer those 4. It keeps
   `bob`, `sase`, `sase_blog`, and `job_2026` quiet, and it stops `root: true` from
   silently deciding offer behavior. If you'd rather not change the rule, reparent
   `job_email_recruiters` under `job_2026`. I verified this yields the same 4 offers
   with no code. Either way, don't ship the mark against the literal formula. It would
   show `4` on a link whose close offers nothing.

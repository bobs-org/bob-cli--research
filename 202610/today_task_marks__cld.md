# Today marks: showing "on today's plan" on the task line itself

*Researcher: cld · 2026-10-19 · bob-cli + bob-plugins (bob-ledger-tools) + Bob vault*

**Question.** Bryan wants a marker on tasks that are "in today's daily file" when he
looks at those tasks in Obsidian, in the spirit of the existing Task Link marks (◐ In
Progress and 🔓 unblocked-today) in the daily note. He asked me to lead the design so
the result is intuitive, reliable, and beautiful; to critique the idea; to adjust the
requirements where that's justified (and say so); and to end with a recommendation.

---

## 0. TL;DR

- **Build it.** It fills a real gap. Since sticky lanes (`decisions:task-lanes-are-sticky`),
  `[*]` means "committed", not "today". So nothing on a task's own line says whether
  it is on today's plan. And Ctrl+Shift+Enter, which **toggles** link presence, has no
  visible state: on a task that is already linked, it unlinks.
- **What the mark means:** exactly **Today**, the same set as the dash TODAY section,
  `bob plan`'s TODAY list, and the `x` lineup. That is the open `#task` lines with a
  dedicated Task Link under one of today's **open** Pomodoros (`docs/plan.md` §Today).
  The mark is display-only and is computed from the Today cache bob-ledger-tools
  already maintains. Nothing is written to a task or to the ledger.
- **How it looks:** a 🍅 drawn **right after the `#task` identity glyph, before the
  title**. It sits in the same column on sibling lines, so a list scans like Things'
  Today star or Microsoft To Do's "My Day" sun. Tasks in the running Pomodoro get a
  soft "now" capsule in the line's own status color. Hovering names the Pomodoro
  (`Today · BLOG · queued`). Mod+click jumps to the Task Link in today's note.
- **Reliability rule:** truthful or neutral. The mark appears only when the Today
  cache is ready for the current date and the identity match is exact (Live Preview)
  or unambiguous (rendered views). Otherwise there is no mark, never a stale or
  guessed one.
- **Requirement adjustments (details in §6):**
  1. The mark means "on today's plan" (Today), **not** "appears anywhere in today's
     daily file".
  2. Links under closed Pomodoros only (🍅 history), prose, nested, struck, and `#`
     move-only links get **no** mark.
  3. No marks **inside daily notes**, which are the ledger itself.
  4. Tasks query results are a **non-goal**: their sections already split on Today.
  5. Pickers, the Task Card, and Mac Capture are **phase 2**.

---

## 1. What should "in today's daily file" mean?

The literal wording admits five readings. Only one agrees with every other Today
surface Bryan already uses.

| Case in today's daily note                                                                  | Example                                  | In dash TODAY / `bob plan` / `x` lineup? | Mark?                                                     |
| ------------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------- | --------------------------------------------------------- |
| Dedicated Task Link under an **open** Pomodoro (running or placeholder, named or unnamed)   | `- [ ] () — BLOG` / `\t- [[sase_blog#^x]]` | **yes**                                  | **yes**                                                   |
| Same, but as an embedded link                                                               | `\t- ![[T#^x]]`                          | yes                                      | **yes**, on T's line                                      |
| Dedicated link only under **closed** Pomodoros                                              | `\t- 🍅 [[T#^x]]` under `- [x]`          | no ("closed 🍅 lines are history")       | **no** (optional later "worked earlier" tone, §7)         |
| Link in prose, deeper nested, struck, `#` move-only, fenced, outside `## Pomodoros`         | `\t- read [[T#^x]] today`                | no                                       | **no**                                                    |
| Task that *lives* in the daily note (`^gtd`)                                                | `- [/] #task [[gtd_daily]] … ^gtd`       | yes, when linked                         | **no**: marks are suppressed inside daily notes (§5.6)   |

The governing decision is `decisions:today-is-read-from-the-ledger`: Today is "dedicated
Task Links under today's **open** Pomodoros only; closed 🍅 lines are history", and it
is never a tag, a task-line field, or a file-path filter. A marker that used any other
definition would disagree with the dash, `bob plan`, the capture `x` lineup, and the
Today exemptions in freshness review. That disagreement is the "two copies of Today"
problem the decision was written to prevent. So the invariant to ship and test is:

> **A task line shows the Today mark ⇔ the task is a row in dash's TODAY section.**

---

## 2. What already exists (evidence)

### 2.1 The Today definition and its JavaScript cache

- **Contract.** `docs/plan.md` §Today (bob-cli), rules 1–6. Rust `today_tasks` and
  ledger-tools `isToday` share the conformance vectors in §"Today conformance examples".
- **Parser.** `computeTodayLinks(content, dailyPath)` in
  `plugins/bob-ledger-tools/src/060-today.js` already returns, for every dedicated
  link, `{ entryLine, entryName, ledgerLine, target, blockId, embedded }`. That is
  everything the tooltip and the jump need.
- **Cache.** `rebuildTodayCache` in `src/290-plugin-today-and-location.js` stores ordered
  keys `"<path.md>#<blockId>"` plus a rank map. When the keys change, it fires the Tasks
  reload event, the plan-block rerender, the freshness status bar, the freshness-mark
  refresh, and the Reading Board repaint.
- **Refresh triggers.** It already rebuilds on metadataCache `changed` for the daily note,
  on vault create/delete/rename events, on `resolved`, and at the date rollover
  (`src/170-plugin-lifecycle.js:424–506`).
- **Readiness gate.** `isTodayCacheReady(now)` (`src/180-plugin-plan-and-ready.js`) checks
  that the cache date and the daily path match the current day.

**Conclusion:** no new definition, parser, or event wiring is needed. The mark is a new
*view* of an existing, tested set.

### 2.2 The daily-note-side marks Bryan referenced

- **◐ In Progress mark** on Task Links under open Pomodoros whose target is `[/]`
  (`docs/plan.md` §"In Progress marks and the Task Link lane toggle"). Its principles:
  - "rendered, never written"
  - "one marker slot, two tenses" (🍅 = worked in a past session, ◐ = in progress now)
  - "truthful or neutral"
  - an amber half ring, a 160 ms entrance, a hover capsule, and a session toggle
- **🔓 unblocked glyph** after a live Task Link whose task had a prerequisite completed
  today (`src/139-unblocked-glyph.js`, `src/271-plugin-unblocked-glyph.js`). Its glyph
  is a text emoji, chosen "so the read-time decoration stays legible without new
  assets".
- **Pomodoro home chips** on ledger entries (`src/142-…`, `src/273/274-…`).

All three decorate the **link** inside the daily note. The new feature is the mirror
image: it decorates the **task line** in its home note, and points back at the ledger.

### 2.3 What already sits on a task line

| Mark                    | Contract                         | Look                                                        | Color                                           |
| ----------------------- | -------------------------------- | ----------------------------------------------------------- | ----------------------------------------------- |
| Status line tint        | vault `task-statuses.css`        | 2 px left stripe + 13–14 % background                       | red Blocked, green Next, yellow In Progress     |
| `#task` identity glyph  | `docs/task-tag-marks.md`         | thin slanted teal hash (📖 for `#task #ref`)                | constant teal; "never encodes state"            |
| Priority marks          | `docs/projects.md`               | signal bars                                                 | grey                                            |
| Date marks              | `docs/date-marks.md`             | `+ Sep 29`, `⧗ today`, `✓ Sep 3`, `⊘ today`                 | monochrome; "color whispers"                    |
| Freshness mark          | `docs/freshness.md` §11          | `✓ today` circle-check, lease ring `3d`, `⟳ 9d` capsule     | green today, grey aging, orange due only        |
| Keep dots, dependsOn 🔗 | freshness §11, vault snippet     | faint dots, muted link-2 glyph                              | faint                                           |

The color vocabulary is fully booked (table in `docs/task-tag-marks.md` §Ink): red,
orange, yellow, green, blue, violet, and cyan/teal all have meanings, and grey belongs
to the metadata marks. Two consequences shape the design:

1. **The word "today" is already used twice on task lines with other meanings:**
   `⧗ today` (scheduled today) and `✓ today` (freshness confirmed today, or completed
   today). A third "today" text label would be a trap. *Scheduled today* and *planned
   today* are different things in this system: a scheduled date is a deferral that
   expires; Today is a ledger link.
2. **On a Today line, every other mark is quiet.** Today tasks are out of the review
   walk, so their freshness mark is always the faint `resting` tone ("linked today").
   Blocked tasks keep no Task Links under today's open Pomodoros
   (`decisions:projects-block-from-prj-line`), so Today lines essentially never carry
   the red tint. A Today line is therefore a green or yellow tinted line with a teal
   hash and grey metadata. One warm accent will stand out cleanly.

### 2.4 🍅 already means "today's Pomodoros" on most surfaces

- **Ledger:** `🍅 [[…]]` on links under closed entries, meaning a Pomodoro was spent.
- **Mac menu bar indicator:** a running session reads `THEME (50m) · 🍅 12:34`
  (`glossary:mac-pom`).
- **Blocks-stage picker:** a task linked under one of today's open Pomodoros gets a
  `🍅` badge, or `🍅 running`, with the tooltip `Linked under {label} {range}`
  (`plugins/bob-navigation-hotkeys/src/410-picker-filter-and-render.js:439–449`). This
  is a direct precedent for 🍅 on a **task row** meaning "on today's plan".
- **Reading Board:** a green small-caps `TODAY` pill with the tooltip "Linked under
  today's Pomodoros" (`src/243-plugin-reading-board-render.js:222–227`). That pill
  suits cards; it would be too wide and too wordy on a task line.

### 2.5 Ctrl+Shift+Enter's "is linked" test is broader than Today

On a task line, Ctrl+Shift+Enter decides between link and unlink with
`pomodoroTaskLinkPresence`, i.e. `planAllOpenPomodoroLinkCleanup(...).removedCount > 0`
(`plugins/block-id-prompt/src/120-plugin-pomodoro-links.js:154–178`). That cleanup
matches **any** wiki block reference to the task inside an open Pomodoro's range: mixed
prose, nested bullets, and `#` move-only lines included. Today counts only dedicated
links.

So on those rare lines the toggle will *unlink* even though no Today mark is shown.
I recommend keeping the mark tied to Today (the dash invariant matters more) and
documenting the divergence. §8 Q4 asks whether the toggle should narrow to Today.

### 2.6 How many lines would carry the mark?

I counted dedicated links under open entries in each October daily note. These are
end-of-day states, so they give a lower bound on midday Today size. Today's note
(2026-10-19) has 12 Today links across 7 notes.

| Metric                                                  | Range across 2026-10-01 → 10-19                         |
| ------------------------------------------------------- | ------------------------------------------------------- |
| Today links per day                                     | 5–15                                                    |
| Notes touched per day                                   | 3–8                                                     |
| Today tasks per note                                    | usually 1–3; up to 5–6 (`sase.md` today; `job_2026_apply_29` on 10-15) |
| "Worked earlier, not re-queued" (closed-only) per day   | 0–9                                                     |

The mark is **rare**: about a dozen lines vault-wide on a given day, a handful per note.
That justifies a distinct, warm glyph. A mark that repeats on thousands of lines, like
the `#task` hash, has to be quiet; this one does not.

---

## 3. Critique: is this a good idea?

**Yes.** Here is why, and what to watch.

### Why it's worth building

1. **It restores a signal that sticky lanes removed, without undoing them.** Before
   epic `bob-cli-2y`, hooks derived `[*]` from today's links (`decisions:task-status-is-derived`).
   Since then `[*]` means *committed*, which is often "this week". Today's `bob.md`
   shows the problem:
   - In `### Next & In Progress`, `^split-highlights` `[*]` **is** in today's ledger.
   - `^ref-athena-plex-compromise-incident-report` `[*]` and
     `^ref-ref-create-auto-ingest-across-tailnet` `[/]` **are not**.
   - All three look alike.

   The mark separates "committed" from "on today's plan" without reintroducing a
   derived status, a `#today` tag, or `#now`.
2. **It makes the Ctrl+Shift+Enter toggle legible.** The gesture's behavior depends on
   hidden state (linked → unlink). Showing state before an action is the first of
   Nielsen's usability heuristics, "visibility of system status".
3. **It follows every relevant decision.** It is read from the ledger, never written
   (`today-is-read-from-the-ledger`). It owns no status (`task-lanes-are-sticky`). It is
   not a user-owned weekly bet (`#now`'s retirement). It is not stored, so there is no
   sync churn across athena, apollo, and the Mac.
4. **It is cheap.** The definition, parser, cache, events, and readiness gate all exist
   (§2.1). The work is one display fragment pair, CSS, a contract section, and vectors.

### What could go wrong, and the mitigation

| Risk                                                                         | Mitigation                                                                                                                                                    |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Clutter:** another mark on dense lines                                     | It is rare (§2.6), a single glyph with no text, at the start of the title where the eye already lands.                                                       |
| **A third "today" vocabulary**                                               | No "today" word in the mark. The tooltip uses the established **TODAY** concept name (`Today · BLOG`), matching the dash chip.                                 |
| **Tense of 🍅** (closed ledger links use 🍅 to mean "worked")                | The tooltip says `queued` or `running`. The Blocks-stage picker already uses 🍅 to mean "linked under today's Pomodoro". No task line uses 🍅 for anything else. |
| **Stale marks** (startup, midnight, sync from another machine)               | The `isTodayCacheReady` gate shows nothing until ready. Rollover rebuild already exists. Vault events from `bob vault-sync` already rebuild.                   |
| **Wrong identity in rendered views** (reading view has no block ids or section info; see `src/269-…reading.js:12–16`) | Exact block-id match in Live Preview. Text-signature consensus in rendered views. Neutral when ambiguous.                                       |
| **Divergence from Ctrl+Shift+Enter's broader "linked"** (§2.5)               | Document it; rare in practice. Optional follow-up to narrow the toggle.                                                                                       |
| **Maintenance:** yet another JS surface                                      | Reuse the cache; put a contract section with vectors in `docs/plan.md`, as the other marks do.                                                                |

### What I would do differently from the literal ask

- Mark **"on today's plan"** (Today), not "mentioned in today's file" (§1).
- Make it a **rendered** mark. Never write an emoji, tag, or field (the rejected
  `#today` path).
- Ship the **note surfaces first** (Live Preview, reading view, embeds, hover
  previews). Pickers, the Task Card, and Mac Capture come after Bryan has lived with it.

---

## 4. Design space

### 4.1 Where on the line

| Option                                                         | Scanning                                                         | Text reflow                                     | Surfaces and reliability                                                                                                                                 | Verdict                                         |
| -------------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **A. Leading inline, right after the `#task` identity slot**   | **Aligned column** on sibling lines; read before the title       | Title shifts about 1.2 em on marked lines only (as with Things' star) | Live Preview widget at title start (`side: -1`). Reading view: insert after the `a.tag`. Works in embeds and hover previews.                            | **Recommended**                                 |
| B. Trailing chip at line end, or styling the `^block-id`       | Ragged; wraps onto a second visual line                          | none                                            | The block id is not rendered in reading view; it adds to the metadata tail (dates, fresh, keeps)                                                         | Rejected                                        |
| C. Left-margin pin (gutter-like)                               | Best column                                                      | none                                            | Clipped in embeds, hover popovers, and narrow panes; collides with Live Preview's list fold arrows; a CM6 gutter would shift every note                  | Rejected (reliability)                          |
| D. Line treatment (thicker rail, outline, extra background)    | Strong                                                           | none                                            | The stripe and tint channel already belongs to status; mixing them breaks "one encoding per channel"                                                    | Rejected                                        |
| E. Badge or halo on the checkbox                               | Good                                                             | none                                            | Fights `task-statuses.css`, which already styles the checkbox and its `::after`, and the Tasks checkbox                                                  | Rejected                                        |
| F. Write a tag, field, or emoji into the line                  | —                                                                | —                                               | Churn, races, staleness, and sync conflicts                                                                                                              | Rejected by `today-is-read-from-the-ledger`     |
| G. Note-level count ("🍅 2 today" beside the `## Tasks` summary) | Answers "how many here"                                          | none                                            | Rendered only; the summary line itself is written text                                                                                                  | Complement, phase 2                             |

**Why after the identity slot rather than before the hash?** The `#task` hash is a
constant identity column on every tracked task. Shifting it on Today lines would make
the identity column ragged. Placing the mark after it keeps two clean columns: identity,
then Today.

**Placement rule:**

- If the task body starts with `#task` (or the `#task #ref` pair), the mark sits at the
  first non-space character after that slot.
- Otherwise (rare, e.g. time-prefixed lines), it sits at the body start.

### 4.2 Which glyph

| Glyph                                         | For                                                                                                     | Against                                                                                                                                        | Verdict                                                     |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **🍅 (system emoji)**                         | The symbol for Pomodoro on every Bob surface (§2.4); zero learning; carries its own colors; crisp in Apple and Noto emoji; the vault already uses emoji labels (🛠️ 🗓️ ⛓️ 🧱 🧩) | Tense nuance (§3); not theme-inked                                                                                                             | **Recommended**                                             |
| Custom two-tone tomato mask (red body, green calyx) | Theme-adaptive; matches the masked-glyph family                                                         | A new asset; at about 11 px it is less recognizable than the emoji; a single-ink mask cannot do red plus green, so it needs two layers        | Fallback through a CSS hook (§5.3)                          |
| ☀ sun (Microsoft To Do "My Day")              | A widely used "today" symbol                                                                            | No tie to Pomodoros; amber already means In Progress                                                                                           | Rejected                                                    |
| ★ star (Things' Today, from memory)           | Familiar to Things users                                                                                | `★` already marks the highlight theme in `bob plan` output; a star reads as "favorite"                                                         | Rejected                                                    |
| 📅 or a calendar glyph                        | "Day"                                                                                                   | Collides with the date marks and with "scheduled today"                                                                                        | Rejected                                                    |
| `TODAY` small-caps pill                       | Explicit; already used on Reading Board cards                                                           | Wide text on dense lines; repeats the "today" word                                                                                             | Rejected for lines                                          |
| Pomodoro-name chip (`BLOG`)                   | Says *which* session                                                                                    | Wide; names can be long or composite (`GTD + BOB`); unnamed sessions need derived labels                                                       | Put it in the tooltip instead                               |
| Dot or pin                                    | Minimal                                                                                                 | Reads as a bullet or a notification; carries no meaning                                                                                        | Rejected                                                    |

**On emoji versus a refined mask:** the date-mark and hash contracts turned emoji into
monochrome masks *because those marks repeat on thousands of lines* and had to go quiet
(`docs/date-marks.md` §Fields and glyphs). The Today mark is the opposite case: rare,
meaningful, and meant to be noticed. Its symbol should be the one Bryan already reads
as "today's Pomodoros" on the ledger, the menu bar, and the Blocks picker. The 🔓 link
glyph already set the precedent of an emoji for a read-time mark.

### 4.3 How much information to show

- **Binary** (on the plan or not) is the core meaning.
- **Running versus queued** is cheap to compute and shown by *tone*, not a second glyph
  (§5.3). "One symbol, one meaning" is kept: the "now" tone answers "which of these is
  in the session I'm in right now?"
- **Which Pomodoro, and its time range,** go in the tooltip.
- **"Worked earlier today, not re-queued"** is a different, backward-looking question.
  It is left out of v1 (§7).

---

## 5. Recommended design: the Today mark (draft contract)

### 5.1 What you see

```text
bob.md — Live Preview (glyphs approximated)

- [*] ⌗ 🍅 Start adding some kind of marker to tasks that are in today's daily file!  + today
### Next & In Progress
- [*] ⌗ 🍅 Add support for `<` to split highlights!  + today              ← queued (BLOG later today)
- [/] 📖 Making bob ref create usable without a manual bob ref scan  ◌ resting  + Oct 18
- [*] 📖 Athena Plex compromise (2026-10-17): incident report  ◌ resting  + Oct 17
sase.md
- [*] ⌗ 🍅 Fix `|` and `\` keymaps so they reverse their own operations!  ◌ resting   ← queued (BUGS)
- [*] ⌗ (🍅) Add support for local links to pager!  + today              ← "now": in the running GTD 0725–0815
```

- The 🍅 forms a column right after the identity glyph.
- `(🍅)` stands for the soft "now" capsule.
- Lines that are not on today's plan look exactly as they do today.

### 5.2 Eligibility (truthful or neutral)

A task line gets the mark only when **all** of the following hold:

1. **The Today cache is ready** (`isTodayCacheReady(now)`: built for today's date and
   today's daily path).
2. **The line is a task line** (`freshnessTaskStatus(line) !== null`, quote-aware) with
   an **open** status: ` `, `*`, `/`, or `?`. This is Today rule 5; `x`, `X`, `-`, and
   any other non-open symbol get no mark. In Live Preview the status is read from the
   **live line**, so completing a task removes the mark on the same frame.
3. **The line has an exact `#task` tag**, using the same token rule as
   `docs/task-tag-marks.md` §Eligibility (Today counts `#task` lines only).
4. **Its identity `"<host path>#<block id>"` is in the Today key set.**
   - *Live Preview:* exact. The host path comes from `editorInfoField`, the block id
     from the line's trailing `^id`. If the same id appears twice in a note, only the
     first line Obsidian resolves gets the mark.
   - *Rendered views:* by consensus. Reading view has no block ids or section info. So
     match the row's own text signature (title text with tags, fields, and the id
     removed) against the Today lines of `ctx.sourcePath` (at most a few per note).
     Mark only on a **unique** match. An embed or hover of `T#^id` takes its identity
     from the embed's `src`.
5. **The host is not a canonical daily note** (`YYYY/YYYYMMDD.md`), nor inside one. The
   ledger is the source; it has its own ◐, 🔓, and home-chip marks.
6. **The surface is not excluded** (§5.6).

Everything else shows nothing: unresolved or ambiguous links, closed-only history,
non-dedicated references, a cache that is not ready, and ambiguous rendered matches.

### 5.3 Anatomy and tones

**Host element:** an empty `span.bob-today-mark` with `role="img"`, an `aria-label`, and
`data-tooltip-position="top"`. The glyph is drawn by
`::before { content: var(--bob-today-mark-glyph, "🍅"); }`. That gives:

- copy and paste of the line never picks up 🍅;
- a theme or snippet can swap in a masked glyph later without code changes;
- Dataview's `innerHTML` round trip keeps the element.

Events are **delegated** from the plugin, so no listeners are lost.

**Shared metrics, matching the family:**

- `font-size: 0.85em`
- a `1.2em` inline-flex box with `line-height: 1`, so line height never changes
- `vertical-align: -0.14em` (tunable)
- `margin-inline: 0.04em 0.32em`
- `border-radius: 999px`
- `user-select: none`
- transitions on opacity and background-color, 120 ms
- `print-color-adjust: exact`

| Tone              | When                                                                                                                       | Look                                                                                                                                                                                          |
| ----------------- | -------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `queued`          | Linked only under open **placeholder** entries, or more than one open entry is timed                                       | Bare glyph, opacity 0.95                                                                                                                                                                      |
| `now`             | Linked under the **running** entry: exactly one open timed entry, the same rule as the Blocks stage (`302-blocks-stage-view.js:103–111`) | Soft capsule tinted with the line's status accent: `color-mix(in srgb, var(--task-status-accent, var(--text-muted)) 18%, transparent)` plus a 1 px inset ring at 40 %. Tone on tone: green on Next, amber on Pending. Never an alarm color. |
| hover (any tone)  | pointer over the mark                                                                                                      | Opacity 1, plus a capsule at 12 % of the same accent                                                                                                                                          |
| entering          | The key **joined** Today within the last ~600 ms (link just added)                                                         | 160 ms scale-in, like the ◐ mark. Not replayed on scroll-in or rerender.                                                                                                                      |

Notes:

- Under `prefers-reduced-motion: reduce`, transitions and the entrance animation are off.
- Under `forced-colors`, the capsule becomes `Canvas` with a `CanvasText` ring.
- A theme hook `--bob-today-mark-glyph` is unset by default.

### 5.4 Tooltip (lines joined with `\n`; never contains `::`)

Line 1, by situation:

- `Today · GTD · running 0725–0815` (now tone; range only, never the `[t::]` field)
- `Today · BLOG · queued`
- `Today · sase · queued` (an unnamed entry uses its derived home label, as the Mac
  indicator does, falling back to `unnamed Pomodoro`)
- `Today · BUGS · queued +1 more` (several open entries link the task; this is rare
  because future duplicates are pruned)

Lines 2–3:

- `Mod+click to open in today's note`
- `Ctrl+Shift+Enter to unlink`

`aria-label` is the same text, as in the rest of the family.

### 5.5 Interaction

- **Click** places the cursor at the title start and focuses the editor. It never
  writes and never navigates. This is the family rule, and it prevents accidental jumps
  when clicking near the start of the title.
- **Mod+click** (Cmd on macOS, Ctrl elsewhere) opens today's daily note at the Task
  Link line (`ledgerLine`, first occurrence). A Shift modifier opens a new tab, like
  links. This is the reverse of clicking a Task Link in the ledger: the two ends of the
  same edge.
- **Cursor and vim.** The widget sits at the title start with `side: -1`, so the caret
  at the title start draws *after* the mark. Motions (`0`, `^`, `I`, `w`) are unaffected,
  because widgets occupy no document positions. The mark never hides under the cursor:
  there is no stored text to reveal. Moving into `#task` still reveals the hash as it
  does today.
- **Feedback loop.** Ctrl+Shift+Enter (link) → `Linked to BLOG · …` Notice → the 🍅 pops
  in before the title. Unlinking makes it vanish. Starting a Pomodoro (`=` capture,
  `x`) moves its tasks into the "now" capsule.

### 5.6 Surfaces

| Surface                                                                        | Mark?                                    | Why                                                                                                                                  |
| ------------------------------------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Live Preview of any non-daily note                                             | **yes** (exact)                          | Primary surface                                                                                                                      |
| Reading view, block or section embeds, hover previews, canvas cards            | **yes** (consensus or embed `src`)       | Same post-processor plus the sweep in §5.7                                                                                           |
| Any canonical daily note, including embeds rendered inside one                 | no                                       | The ledger is the source; marks there would be circular                                                                              |
| Tasks query results (`dash.md`, `freshness.md`, `rotten.md`, `blocked.md`)    | no (non-goal)                            | Their sections already split on Today: dash's TODAY section is exclusive, freshness and READY exclude Today, and Blocked cannot be Today |
| Dataview task lists, source mode, Obsidian search, backlinks                   | no                                       | Same non-goals as the other marks                                                                                                    |
| Nav pickers, Task Card header, Mac Capture candidates                          | phase 2 (§7)                             | Need an api lookup and, for Mac, Rust JSON                                                                                           |

**Implementing daily-note suppression robustly:** ledger-tools adds
`bob-daily-note-view` to the `containerEl` of every markdown leaf showing a canonical
daily note, on `file-open` and `layout-change`. A CSS rule hides `.bob-today-mark`
inside it. That also covers embeds rendered inside the daily note, whose `ctx.sourcePath`
is the *embedded* note.

### 5.7 Data flow and reliability

1. **Single source.** Extend `rebuildTodayCache` to keep, beside `keys`, a `details`
   map: key → `{ entries: [{ name, label, ledgerLine, running }] }`. Compute `running`
   in `computeTodayLinks` from the parsed entry using the Blocks-stage rule.
2. **Change detection.**
   - A **key** change keeps today's behavior: Tasks reload event, plan block, freshness
     refresh, Reading Board.
   - A **detail-only** change (a session starts or closes, an entry is renamed) only
     dispatches a new `todayMarksRefresh` effect. That avoids re-querying every Tasks
     block when a Pomodoro starts.
3. **Live Preview.** A `Prec.highest` ViewPlugin over the visible ranges.
   - Cheap prefilter: the line contains `#task` and ends with `^id`, where the id is in
     the host's id set (at most a few per note).
   - Rebuild on doc, viewport, Live Preview or file switches, and `todayMarksRefresh`.
   - Widget `eq()` compares a model key (tone, label, entering), so unchanged marks
     never flicker.
4. **Rendered views.** The post-processor (sort order after the task-tag marks, e.g. 60):
   - stamps each eligible open `#task` `li` with `data-bob-task-key` once identity is
     known;
   - inserts the mark when that key is in Today.
   - On every Today change, a **sweep** re-evaluates every `[data-bob-task-key]` element
     in all windows (main and popouts) to add, remove, or retone marks without a
     rerender. This mirrors how the hash toggle re-annotates `a.tag`s document-wide.
5. **Latency.**
   - Ctrl+Shift+Enter from a project note writes the daily note through `vault.modify`
     (block-id-prompt rewrite paths, `src/140-…:102`, `src/150-…:222,294`). The Today
     rebuild should follow on the metadata `changed` event within a few hundred ms.
     *Verify this in implementation* for the case where the daily note is open in
     another pane.
   - If any write path proves laggy (the ◐ mark hit about 2 s autosave lag), add the
     same optimistic pattern: `api.todayMarks.expect([{ path, blockId, linked }])`, with
     hints that win until the cache agrees or 4 s pass (cf. `api.progressMarks`).
   - Hand edits *in* the daily note update other panes at autosave. That is acceptable,
     and consistent with the dash.
6. **Day boundaries and other machines.**
   - The existing rollover rebuild clears marks at local midnight. Before the new
     daily note exists, Today is empty, so there are no marks.
   - `bob vault-sync` pulls of the daily note arrive as vault `modify` events, which
     already rebuild.
   - Before layout-ready, or when the date mismatches, there are no marks (readiness
     gate).
7. **Failure.** Every helper is synchronous and never throws (the family convention).
   Any error yields no mark.

### 5.8 Toggle and lifecycle

- Command **"Toggle Today marks"** (`toggle-today-marks`): session-only, on by default.
  It flips `body.bob-today-marks`, dispatches the refresh effect, and shows a
  `Today marks on/off` Notice.
- Turning it off hides the marks through CSS instantly. `onunload` removes the body
  class, the inserted spans, and the `data-bob-task-key` stamps.
- Without the plugin, the vault looks exactly as it does today.

### 5.9 Contract home and conformance vectors

**Home.** Add `## Today marks` to bob-cli `docs/plan.md`, right after
`## In Progress marks and the Task Link lane toggle`, because Rust owns the Today
meaning there. The JavaScript tests run its vectors verbatim. No Rust change is needed.

**Notation.** `D` is today's daily note. `T` is an area note holding
`- [s] #task Fix ^fix`. Unless stated otherwise, `D` has an open timed entry
`- [ ] (**0900-0930** [t:: 30m]) — GTD` as the only timed open entry.

| ID   | Setup                                                                                                    | Mark on T's line?                                     |
| ---- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| TM1  | `\t- [[T#^fix]]` under the timed entry, `s=*`                                                            | yes, tone `now`, after the hash                       |
| TM2  | under a placeholder `- [ ] () — BLOG`, `s=/`                                                             | yes, `queued`, tooltip `Today · BLOG · queued`        |
| TM3  | only `\t- 🍅 [[T#^fix]]` under `- [x] (…)`                                                               | no                                                    |
| TM4  | TM3 plus a placeholder link                                                                              | yes, `queued`                                         |
| TM5  | `s` is `x`, `X`, or `-`, still linked                                                                    | no; flips on the same frame when edited live          |
| TM6  | `s=?` (transiently linked)                                                                               | yes (Today rule 5)                                    |
| TM7  | `s=" "` (hand-linked, hooks not yet run)                                                                 | yes                                                   |
| TM8  | struck `~~[[T#^fix]]~~`, nested `\t\t- [[T#^fix]]`, mixed `\t- read [[T#^fix]] today`, `[[T#^fix]]#`, fenced, outside `## Pomodoros`, or in yesterday's note | no |
| TM9  | embedded `\t- ![[T#^fix]]` under an open entry                                                           | yes (on T's line)                                     |
| TM10 | `- [*] Fix ^fix` (no `#task`)                                                                            | no                                                    |
| TM11 | T's line has no `^id`                                                                                    | no                                                    |
| TM12 | linked under both a placeholder and the timed entry                                                      | one mark, `now`, tooltip `+1 more`                    |
| TM13 | two open timed entries; link under one                                                                   | yes, `queued` (no unique running entry)               |
| TM14 | ambiguous basename target                                                                                | no (unresolved, as in Today)                          |
| TM15 | host is `D` (the `^gtd` line), or T's line embedded inside `D`                                           | no (daily-note suppression)                           |
| TM16 | Today cache not ready (startup), or the date rolled over                                                 | no                                                    |
| TM17 | `- [*] #task #ref Book ^fix` / `- [*] #task #prj Ship ^fix`                                              | after the 📖 pair / between the hash and `#prj`       |
| TM18 | `> - [*] #task Quoted ^fix`                                                                              | yes (quote-aware)                                     |
| TM19 | `- [*] #task Fix #hide ^fix`                                                                             | yes                                                   |
| TM20 | the same `^fix` twice in T                                                                               | first resolved line only                              |
| TM21 | cursor at the title start / inside `#task`                                                               | mark shown, caret after it / mark shown, hash revealed |
| TM22 | reading view, two rows with identical text, one of them Today                                            | neither (ambiguous: neutral)                          |
| TM23 | Ctrl+Shift+Enter link from T, then unlink                                                                | appears (entering animation), then disappears         |
| TM24 | toggle off, then on                                                                                      | gone everywhere at once, then back                    |

### 5.10 Implementation sketch (bob-plugins + bob-cli docs)

**bob-plugins, `plugins/bob-ledger-tools/`:**

- **`src/143-today-marks.js`** (pure core):
  - `todayMarkInsertOffset(lineText)` (identity-slot rule)
  - `todayMarkEligibleLine(lineText)`
  - `todayMarkModel({ key, details, status })` → `{ tone, label, range, more }`
  - `todayMarkTooltip(model)`
  - a listener-free DOM builder and the Live Preview widget class
  - reading-view `todayMarkTextSignature(...)` for consensus
- **`src/275-plugin-today-marks.js`**: the ViewPlugin, refresh effect, post-processor,
  sweep, the daily-view class, delegated click and Mod+click, and the toggle command.
  Split a `…-reading.js` file if it nears the 1000-line fragment limit.
- **`060-today.js` / `290-plugin-today-and-location.js`**: `running` on links, the
  `details` map, and the detail-signature refresh.
- **`styles.css`**: `.bob-today-mark` rules (about 80 lines).
- **`scripts/test-ledger-tools-today-marks.cjs`**: TM vectors plus fake-DOM rendered
  cases. Then `npm run build`, `npm test`, and `bob plugins sync`.
- **`README.md`**: add a row for the mark and its command.

**bob-cli:** the `docs/plan.md` §Today marks contract with the vectors above.

**Size:** one focused plan, or a two-phase epic: (1) core plus Live Preview, (2)
rendered views and the sweep. Roughly 700–1,000 lines of JavaScript, CSS, and tests.

### 5.11 Live verification (Bryan, in Obsidian)

- In `bob.md`, today's two linked tasks show 🍅 after the hash; the Next and Pending ref
  tasks that are not linked show nothing.
- Ctrl+Shift+Enter link and unlink make the mark appear and disappear within about a
  quarter second, with the daily note both open and closed in another pane.
- Starting or closing a Pomodoro moves its tasks into or out of the "now" capsule.
- Light and dark themes look right, on green Next and amber Pending tints alike, and
  beside a violet `#prj` pill.
- vim `j`/`k` does not jitter, and typing at the title start puts the caret after the
  mark.
- Reading view, embeds, and hover previews show the mark. Daily notes and `dash.md`
  never do.
- Mod+click lands on the Task Link line in today's note.
- Midnight clears the marks. The toggle hides and restores them everywhere.
- Mobile (iOS) renders the emoji; there is no hover there, which is acceptable.

---

## 6. Requirement adjustments (explicitly called out)

1. **"In today's daily file" becomes "on today's plan" (Today).** The mark uses the
   exact Today definition (dedicated links under open Pomodoros, open `#task` lines).
   *Why:* one truth shared with dash, `bob plan`, the `x` lineup, and the freshness
   exemptions; this is required by `decisions:today-is-read-from-the-ledger`.
2. **No mark for history.** Tasks linked only under closed Pomodoros (🍅) are not
   marked. *Why:* the decision calls those lines history. "Worked today" is a different,
   backward-looking question, already partly answered by `✓ today` and Stats. It is
   offered as an optional later tone (§7).
3. **No marks inside daily notes.** That includes the `^gtd` line and task embeds in
   the ledger. *Why:* the ledger is the source; marking it is circular, and it already
   has ◐, 🔓, and home chips.
4. **Tasks query results are out of scope.** *Why:* their sections are already
   Today-exclusive, so a mark there would carry no information (the same reasoning that
   hides the `#task` glyph in Tasks rows).
5. **No word "today" on the line.** *Why:* `⧗ today` and `✓ today` already use that
   word on task lines with other meanings.
6. **Phase the surfaces.** Note views first; pickers, the Task Card, and Mac Capture
   follow.
7. **Mod+click jump added.** *Why:* it makes the mark the visible end of the Task Link
   edge, not just decoration.

---

## 7. Phase 2 and follow-ups (not part of v1)

- **The same signal everywhere a task appears.**
  - An additive `api.today` v1 read namespace (`isToday({ path, blockId })`,
    `detail(...)`, `version`) for bob-navigation-hotkeys.
  - The Task Card header (Ctrl+Shift+P) and task-picker rows would show `🍅` with the
    same tooltip. The Blocks stage already does this.
  - Add the namespace only when the first consumer lands, per the task-tag-marks
    "no api without a consumer" rule.
- **Bob Mac Capture candidates.** Per `decisions:mac-capture-is-a-thin-client`, Rust
  would add `today: true` (plus the entry label) to completion candidate JSON from its
  existing `today_tasks`. The app would render 🍅. Coordinate across both repos.
- **Note-level count.** A rendered `🍅 2 today` chip beside the `## Tasks` status summary
  in area and project notes, never written.
- **Optional "worked earlier today" ghost tone.** A faint 🍅 (resting opacity) for open
  tasks linked only under today's closed Pomodoros, behind a setting. Add it only if
  Bryan misses the signal after living with v1.
- **A nav command "Go to Today link".** A keyboard counterpart to Mod+click, alongside
  Ctrl+Shift+Enter.
- **Narrowing Ctrl+Shift+Enter's presence test** to Today's dedicated-link rule (§2.5),
  if Bryan wants "no mark ⇔ the toggle links" to hold exactly.

---

## 8. Open questions for Bryan

1. **Glyph:** the 🍅 emoji (recommended) or a custom two-tone tomato mask in the
   family's style? The CSS hook allows switching later without code changes.
2. **"Now" capsule:** keep it (recommended), or ship strictly binary first?
3. **Click behavior:** plain click places the cursor and Mod+click jumps (recommended),
   or should plain click jump?
4. **Ctrl+Shift+Enter divergence:** leave the toggle's broader "linked" test alone
   (recommended), or narrow it to Today?
5. **History:** is the "worked earlier today" ghost tone worth a setting, or never?

---

## 9. Recommendation

Ship the **Today mark** in bob-ledger-tools as specified in §5:

- **What it is:** a display-only 🍅 placed right after the `#task` identity glyph on
  every open `#task` line that is in **Today** (dedicated Task Link under today's open
  Pomodoros). It reads straight from the existing Today cache and is gated on its
  readiness, so the mark agrees with the dash TODAY section by construction.
- **How it behaves:** a soft tone-on-tone "now" capsule for the running session, a
  tooltip naming the Pomodoro, and Mod+click to jump to the Task Link. A session toggle,
  no writes, and no marks inside daily notes or Tasks results.
- **Where it renders:** exact matching in Live Preview; consensus matching plus a
  document sweep in rendered views, neutral whenever identity is uncertain.
- **Where the contract lives:** a `## Today marks` section with the TM vectors in
  bob-cli `docs/plan.md`.

This is the smallest design that is **intuitive** (Bryan's own Pomodoro symbol, placed
where the eye starts reading, explaining itself on hover), **reliable** (one Today
definition, a readiness gate, exact-or-neutral identity, no stored state to go stale),
and **beautiful** (one rare warm accent on otherwise quiet lines, in a clean column,
with family-consistent metrics and motion).

---

## Sources

**Internal (bob-cli):**

- `docs/plan.md`: §Today; §"In Progress marks and the Task Link lane toggle";
  §"Today conformance examples"
- `docs/task-tag-marks.md`: Ink table; Eligibility; Rejected alternatives; Reference
  reading tasks
- `docs/date-marks.md`: What you see; Label grammar
- `docs/freshness.md` §11
- `docs/pomodoro-homes.md` R1/R3

**Internal (bob-plugins):**

- `plugins/bob-ledger-tools/src/060-today.js`
- `src/180-plugin-plan-and-ready.js`
- `src/290-plugin-today-and-location.js`
- `src/170-plugin-lifecycle.js`
- `src/137-progress-marks.js`
- `src/139-unblocked-glyph.js`
- `src/269-plugin-progress-marks-reading.js`
- `src/243-plugin-reading-board-render.js`
- `styles.css` (progress mark, unblocked glyph, Reading Board TODAY)
- `plugins/bob-navigation-hotkeys/src/302-blocks-stage-view.js`
- `src/410-picker-filter-and-render.js`
- `plugins/block-id-prompt/src/120-plugin-pomodoro-links.js`
- `src/060-link-cleanup-and-deletion.js`

**Vault:**

- `~/bob/.obsidian/snippets/task-statuses.css`
- `~/bob/.obsidian/snippets/dataview-properties.css`
- `~/bob/2026/20261019.md`
- `~/bob/bob.md`
- link counts over `~/bob/2026/202610*.md`

**Memory:**

- `decisions:today-is-read-from-the-ledger`
- `decisions:task-lanes-are-sticky`
- `decisions:task-status-is-derived`
- `decisions:now-tag-is-user-owned`
- `decisions:projects-block-from-prj-line`
- `decisions:mac-capture-is-a-thin-client`
- `glossary:task-link`, `glossary:pomodoro`, `glossary:mac-pom`, `glossary:task-freshness`

**External:**

- [Microsoft Support: Create and manage task lists with My Day in Outlook](https://support.microsoft.com/en-us/Outlook/create-and-manage-task-lists-with-my-day-in-outlook).
  Tasks added to My Day stay in their original list, and My Day clears at midnight.
- [LCPS Inclusive Design blog on Microsoft To Do](https://blogs.lcps.org/inclusivedesign/tag/checklists).
  Third-party; describes the sun icon as marking a task added to My Day.
- [CodeMirror discuss: Inline widget](https://discuss.codemirror.net/t/inline-widget/8689)
  and [widget decoration that takes up space](https://discuss.codemirror.net/t/codemirror-6-widget-decoration-that-takes-up-space/2592).
  Widget `side` and cursor behavior; widgets hold no document positions.
- [Things 3 on the App Store](https://apps.apple.com/app/things-3/id904237743) for the
  Today and This Evening lists. The claim that Things shows a star on Today to-dos
  inside project lists is from memory and **unverified**; it is used only as an analogy.
- Nielsen, "10 Usability Heuristics": #1, visibility of system status. A general
  reference, not fetched.

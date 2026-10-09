# Ref Tasks Live With Their Parent

*Research report · researcher `cld` · 2026-10-09 · scope: bob-cli, bob-plugins,
bob-mac-capture, sase, and the Bob vault*

The request: move every open ref task out of its ref note and into the `## Tasks`
section of a parent area or project note. Every ref gets a required parent. The
special-casing that hides ref tasks goes away. New refs get a parent at capture time
(`bob ref create -p`, Bob Mac Capture, `bob gkeep pull`, and the sase research file
hook). Ref tasks get a new block ID and an icon.

This report checks that plan against the code and the live vault, criticizes it,
adjusts it where the evidence warrants (every change is labeled **A1–A11**), and
ends with a recommended design.

---

## 0. TL;DR

- **Verdict: yes, do it.** The vault shows the current split already failing. Of the
  27 open ref tasks, 5 still sit open after the "Read X" wrapper task you made for them
  in a project note was closed or cancelled. For example, `harness_engineering`'s
  wrapper was checked `[x]` on 2026-10-05, but its `^ref` task is still `[ ]` (§1.3).
  You also link ref tasks from Pomodoros (`🍅 [[x#^ref]]`) and from Depends-On lines
  routinely. In practice they are ordinary tasks already, filed in the wrong place.
- **The special-casing is smaller than it looks.** Ref tasks are kept out of the dash,
  lanes, caps, Today, and the `^` picker by two side effects, not by scattered filters:
  1. every generated `^ref` line carries `#hide`;
  2. the line lives in `ref/`, which is not a root-level area or project note.

  Remove `#hide` and move the line, and nearly every surface treats refs normally with
  no code change. The truly ref-specific code is (a) the ref-note-local status sync and
  (b) the freshness REFERENCES tracker.
- **Keep one special case: the review cadence (A6).** Your config sets
  `reference_interval: 7`, with the comment "Bryan's ^ref review cadence". That is a
  cadence you chose on purpose, not a filter. Keep the REFERENCES walk tier, re-keyed
  from block ID `^ref` to the `#ref` tag. Delete the hide bypass and everything else.
- **New rule (A1): the ref note's `parent` is derived from where its ref task lives.**
  The parent picked at capture only decides where the task is born. After that,
  Ctrl+Shift+M re-files the reference, inbox triage works unchanged, and `bob task
  archive` needs no exemption.
- **CLI spelling (A3): keep `-P/--parent`.** `bob ref create` already has
  `-P/--parent` (default `obsidian_ref`), and `-p` is already `--published`.
  `bob ref list` also uses `-P/--parent`. Make `-P` required and resolved; don't
  repurpose `-p`.
- **Aliases (A4): use Obsidian's native `aliases` frontmatter** on bob.md
  (`aliases: [bob-cli]`) instead of a new `project_name_aliases` key. One resolver then
  serves `bob ref create -P`, `bob ref list -P`, capture `@route`, Keep labels, and the
  sase hook.
- **sase (A11):** the file hook appends the path and has no placeholders. Each run
  already records `project` (`sase` in 49 runs, `bob-cli` in 19). Export it as
  `SASE_FILE_HOOK_PROJECT`; the hook becomes
  `bob ref create --include-id -P "$SASE_FILE_HOOK_PROJECT"`.
- **Rollout warning.** Migrating the 27 open refs as they are pushes Next from 14 to 22
  (cap 15) and Pending from 7 to 15 (cap 10). Triage the stale refs as part of the
  migration (§4.2).

---

## 1. What exists today

### 1.1 The model

A ref note lives at `ref/<ref_type>/<stem>.md`, with frontmatter
`type: "[[ref]]"`, `parent`, and `status`. `bob ref scan` writes its ref task directly
under the H1:

```markdown
- [ ] #task #ref [[lib/papers/harness_engineering.pdf]] [fresh:: 2026-10-07] #hide ^ref
```

(`src/native/highlights_ref/note.rs:84-90`). Status is kept in sync three ways: the PDF
page-1 marker (edited in Highlights), the frontmatter `status`, and the checkbox mark
(`[ ]` ready, `[*]` next, `[/]` wip, `[x]` read, `[-]` abandoned, `[?]` a blocked
overlay). The rules are in `docs/highlights-ref-sync.md` "Synced Properties". The PDF
marker is authoritative for `parent`, and `parent` is a required marker key.

`bob ref create` does not write the note. It writes an intake PDF to `xlib/` whose
marker carries `parent`. The note and its `^ref` task appear later, when `bob ref
scan` runs; on the MacBook that is an hourly LaunchAgent. The current parent default
is `obsidian_ref` (`highlights_ref/create.rs:41`). Background ingest (capture ref jobs
and Keep) hard-codes `INGEST_PARENT = "obsidian_ref"` (`highlights_ref/ingest.rs:31`).

### 1.2 Vault census (2026-10-09)

| Fact | Value |
| --- | --- |
| Files with a `^ref` tracker | 346: 10 `[ ]`, 8 `[*]`, 8 `[/]`, 1 `[?]`, 300 `[x]`, 19 `[-]` |
| **Open modern ref tasks** | **27** (all carry `#hide`, all carry a `[fresh::]` stamp dated 10-06 to 10-09) |
| Parent of all 27 open refs | `obsidian_ref`, the catch-all default |
| Parents across all 346 modern refs | `obsidian_ref` 290, `sase_ref` 48, `memory_ref` 4, `bob_ref` 3, `dev_ref` 1 |
| Zorg-era legacy notes (no tracker) | 602 (194 queued, 161 started, 225 finished, …) |
| Links to `#^ref` outside `ref/` | 93 occurrences (25 of them embeds), across daily notes and project notes |
| …of which point at the 27 open refs | 17 occurrences in 4 files (3 daily notes and `sase_blog_0.md`) |
| Current lanes (`bob plan`) | Next 14/15, Pending 7/10, Today 10 |
| Root area/project notes | 96 |
| Markdown files in the vault | 6,207 |

The hub notes `obsidian_ref.md`, `sase_ref.md`, `bob_ref.md`, and `dev_ref.md` are
zorg-era `type: [[ref]]` notes, not areas or projects. The real topic of a reference
lives nowhere machine-readable today. Every open ref says `obsidian_ref`.

### 1.3 How you actually use ref tasks

- **As Pomodoro work.** For example, `2026/20261008.md`:
  `- [x] (0845-0910) — BLOG` followed by
  `🍅 [[databricks_omnigent_job_fit#^ref]]`,
  `🍅 [[ref/chat/sase_launch_post_introduction#^ref]]`, and so on. Ref tasks are
  promoted to `[*]` and `[/]` by Today links, exactly like other tasks.
- **As prerequisites.** `sase_blog_0.md:31` has
  `⛓️ **DEPENDS ON:** [[ref/chat/sase_launch_post_introduction#^ref]] • …`. Two ref
  tasks already carry `[id::]` fields, and one carries `[dependsOn::]`.
- **Through wrapper tasks.** `sase.md` has
  `- [?] #task Read "Harness Engineering" article… ^read-harness-for-rsi` with an
  embedded `![[ref/blogs/harness_for_rsi#^ref]]` underneath. The same reading is booked
  twice.
- **Drift from that double booking:**

| Open ref (task still open) | Wrapper task in a project note |
| --- | --- |
| `harness_engineering` `[ ]` | `[x]` 2026-10-05, archived in `done/sase_done.md` |
| `toobig_split_beyond_python` `[*]` | `[-]` 2026-10-06 |
| `research_swarm_improvement_roadmap` `[*]` | `[-]` 2026-10-08 |
| `agent_history_in_agents_tab` `[*]` | `[-]` 2026-10-06 (`sase_agent_history.md`) |
| `agent_instructions_budgeted_router` `[?]` | `[-]` (`done/sase_done.md`) |

That is 5 of 27, or 19% of open refs, contradicting their own wrapper. This is the
strongest argument for the redesign: one reading, one task, in one place.

Your own task `bob.md ^better-refs` (created 2026-10-08) already lists "Improved
[[dash_references]]", "Store `^ref` tasks permanently in project note file (no done
cleanup)", and "`bob ref create` requires `-p|--parent`". §2.2 A7 explains why I depart
from "no done cleanup".

### 1.4 Where the "special treatment" really comes from

| Mechanism | What it causes | Code |
| --- | --- | --- |
| `#hide` on every generated `^ref` line | Out of `bob plan` NEXT/PENDING, the READY lane, `bob ready`, the dash, Ready/Next/Pending caps, the freshness seed, and the `^^` picker | lane queries `dataview/tasks/mod.rs:80,88,94` (`tags do not include #hide`); plugin `planLaneVisible` (`bob-ledger-tools/src/060-today.js`) |
| Residence in `ref/` (not a root area/project) | Out of the `^` active-task picker, the `:` link picker, capture targets, status grouping, per-note Ready caps, and `bob projects` counts | `capture_active_tasks.rs:186-224` (vault-root routable notes), `capture_link_tasks.rs`, `task_status_hooks/compose.rs:176-196`, `note_ready/scan.rs` |
| Exact block ID `^ref` = tracker | REFERENCES walk tier, `reference_interval` cadence, never NEW/PENDING/NEXT, `#hide` bypass so hidden refs still walk | Rust `freshness/state.rs:115-140,393-423,515-587`, `scan.rs:239-261,341-371`; JS `bob-ledger-tools/src/100-freshness-evaluate.js:82-160,341-490,716-727`, `160-widgets-and-row.js:328-360` |
| One `^ref` per ref note, in that note | All status sync, close-date stamps, the dirty-note guard, annotation-task placement, audio-embed placement, and `ref show` anatomy | `highlights_ref/annotation_tasks.rs:574-619`, `note.rs:203-217,320-340,553-633`, `guard.rs:160-322`, `audio.rs:135-142`, `region.rs:554-560`, `ref_library/status.rs:56-382` |
| `git log -G\^ref -- ref/` | Fills in `added`/`finished` dates for `bob ref list -g` | `ref_library/list.rs:290-460` |

Things that are **not** special-cased: `task_status_hooks` (it already promotes
`^ref` via Today links), `task_complete`, the `&` and `!` pickers (they deliberately
include `ref/` and hidden tasks), Ctrl+Shift+M (it refuses only `^prj`), the
dependency stage pool, and **`bob task archive`, which has no `^ref` or `^prj`
exemption at all**. Ref notes escape archiving only because they never reach the
10-closed-task threshold. **Bob Mac Capture filters nothing itself**: the `^` picker
renders whatever `bob capture-complete --all-tasks` returns.

---

## 2. Critique of the plan

### 2.1 What's right

1. **Residence is the root problem.** The glossary already says every `#task` lives in
   exactly one area or project note, with "a reference note's own reference task" as
   the only lasting exception (`glossary:area-note`). Removing that exception makes the
   model uniform. Lanes, caps, grouping, pickers, Today, inbox routing, and archive all
   start working through code that already exists.
2. **Required parents fix the metadata.** "Every open ref says `obsidian_ref`" carries
   no information. Real parents make `refs.base` "📚 All Refs" (grouped by `parent`)
   and the Refs panel's area search meaningful for the first time.
3. **Unique block IDs are mandatory, not cosmetic.** Ctrl+Shift+M refuses a move with
   "Destination already contains block ID: ref"
   (`bob-plugins/plugins/bob-navigation-hotkeys/src/250-task-move.js:76-200`). The Mac
   `^` picker dedupes rows on `route:block-id`. `bob plan`'s Today resolver flags
   duplicate block IDs as unresolved. Two `^ref` tasks in `sase.md` would break all
   three.
4. **Prompting for the parent at capture is the right moment.** It is when you know
   why you saved the link.

### 2.2 Adjustments (each is a deliberate departure from the request)

- **A1 — `parent` is derived from the ref task's residence; it does not tell the task
  where to live.** Two sources of truth (frontmatter `parent` and the task's location)
  would drift as soon as you press Ctrl+Shift+M, the same way wrappers drift today.
  - The parent named at capture is carried in the PDF marker to `bob ref scan`, which
    creates the task in that note.
  - From then on, wherever the task lives is the parent. Scan writes it back to
    frontmatter, and to the marker when PDF writes are on.
  - A task in `done/X_done.md` takes its parent from that file's `parent:`, which
    `collect_done/link_repair.rs:390-420` already resolves.
  - Result: re-filing a reference is the same gesture as re-filing any task.
- **A2 — Inbox notes are valid parents, and the inbox is the explicit "decide later"
  answer.**
  - `inbox`, `mac_inbox`, and `gkeep_inbox` are area notes (`glossary:inbox-file`), so
    this still meets "every ref has an area/project parent".
  - Interactive capture (Mac app, `gkeep pull`) prompts and defaults to its inbox.
    Capture never blocks, and the ref surfaces in the NEW/REFERENCES walk, where the
    existing inbox route picker (Ctrl+Shift+Enter, Ctrl+Shift+P) re-files it. By A1,
    that also sets the parent.
  - Scripted `bob ref create` has **no** default: a hook must say what it means.
- **A3 — Keep `-P/--parent`; don't repurpose `-p`.**
  - `bob ref create` already defines `-P/--parent NOTE` (default `obsidian_ref`) and
    `-p/--published DATE` (`create.rs:324-337`).
  - `bob ref list -P/--parent` and `bob ref sync -p/--prefer` set the family
    convention.
  - Change: drop the default, require the flag, resolve it.
  - The help line stays sorted, per `cli_rules.md`.
- **A4 — Use Obsidian's `aliases` property, not a new `project_name_aliases` key.**
  - It is the native "other names for this note" field. It already feeds bob's `[[`
    completion (`capture_links.rs:1090-1130`) and Obsidian's switcher and link
    suggester.
  - It works for areas as well as projects. "Project name" is too narrow, since areas
    are valid parents too.
  - The resolver only considers area, project, and inbox notes, matches
    case-insensitively, and ignores alias values that aren't route-token shaped
    (`[A-Za-z0-9_-]`). Display aliases like `Inbox` and `Job` are harmless because they
    equal their stems.
  - A collision between two notes is an error, never a guess.
  - (If you'd rather keep routing names out of Obsidian's suggester, name the
    dedicated key `route_aliases`; nothing else in this design changes.)
- **A5 — Identity is the `#ref` tag plus a link to the ref note, not the block ID.**
  - The block ID becomes a naming convention, `^ref-<slug>`. It keeps links readable
    (`🍅 [[sase#^ref-harness-engineering]]`) and avoids collisions, but you can rename
    it freely.
  - Freshness keys on the exact whole-token `#ref` tag, as PRE/POST already key on
    `#gtd` plus `#pre`/`#post`.
  - Status sync keys on the ref-note link.
- **A6 — Keep the REFERENCES review cadence; remove all hiding.**
  - "Treat refs like any other task" is right for visibility, residence, lanes, caps,
    pickers, and archive.
  - The REFERENCES tier is different: it is a review cadence, not a filter, and you
    configured it explicitly (`freshness.reference_interval: 7`).
  - Dropping it would put 8 Next and 8 Pending refs into the daily lane review: about
    16 extra decisions every morning.
  - Re-key it to `#ref` and delete the `#hide` bypass, which is now dead code. If you
    later want refs fully ordinary, deleting the tracker branch is a small, separate
    change.
- **A7 — Archive ref tasks normally (no exemption), unlike the 10-08 "no done cleanup"
  note.**
  - About 300 closed refs, mostly SASE agent reports, would otherwise pile into
    `sase.md`'s "Done & Canceled" group forever.
  - What you want to keep permanently is the reading history, and that belongs on the
    ref note. Scan stamps a note-owned `finished: YYYY-MM-DD` when the task closes.
  - The locator searches `done/` too.
  - Reopening an archived ref writes a fresh open task in the parent and leaves the
    archived copy as history (§3.6).
- **A8 — Migrate only the 27 open refs.**
  - The 319 closed modern refs keep their in-note `^ref` line, frozen and read-only,
    so the 76 historical links to them (93 minus the 17 that point at open refs) stay
    valid.
  - The 602 zorg-era legacy notes have no tracker and stay as they are. "Currently
    open ref notes" for legacy notes would mean re-parenting 355 queued/started
    zorg-era records with no task to move, which is not worth doing.
- **A9 — Highlights annotation follow-up tasks also default to the parent note.**
  These are `#task` bullets created from PDF annotations while a ref is `wip`. Today
  they default to the ref note's `## Tasks`. After this change, ref notes hold no tasks
  at all; only 3 such lines exist, all closed.
- **A10 — `bob gkeep pull` gets parents without forcing a prompt.** In order:
  1. a trailing `@route` in the Keep note;
  2. a Keep label that resolves;
  3. `-P/--parent ROUTE` for the whole pull;
  4. a prompt only when stdin and stdout are a TTY;
  5. otherwise `gkeep_inbox`.

  Bob has no TUI picker dependency, and pulls are sometimes piped.
- **A11 — sase passes context through environment variables, not a `{project}`
  placeholder.**
  - `shell=True` already lets `$SASE_FILE_HOOK_PROJECT` expand.
  - It is additive, needs no templating language, has no quoting hazards, and serves
    every hook.

---

## 3. Recommended design

### 3.1 The mental model, in one sentence

> **A reference is a note in `ref/`. Reading it is one task, and that task lives with
> the work it serves. Wherever the task lives is the reference's parent.**

Invariants the implementation must hold:

| # | Invariant |
| --- | --- |
| R1 | An open ref task lives in a root area, project, or inbox note (usually under `## Tasks`). A closed one may live in `done/`. |
| R2 | A ref note has at most one live ref task. Several open ones is a diagnostic, never a guess. |
| R3 | A v2 ref note holds no task lines. Its body shows its task through a managed embed. |
| R4 | The ref note's `parent` equals the task's residence (a `done/` file maps to its `parent:`). Scan projects it. CLI views derive it live. |
| R5 | The three-way status sync (marker, frontmatter, mark) keeps today's rules, including the `[?]` overlay. Only where the mark lives changes. |
| R6 | Ref tasks carry no `#hide`. They count in lanes, caps, Today, pickers, and archive like any task. |
| R7 | The only behavioral exception is the REFERENCES review cadence, keyed on the exact `#ref` tag. |
| R8 | bob-cli remains the only grammar and resolution authority. The Mac app renders what `bob` returns. |

### 3.2 The ref task line

```markdown
- [ ] #task #ref [[ref/papers/harness_engineering|Harness Engineering: Anatomy, Architecture, and Evolution of Agent Harnesses]] [created:: 2026-10-09] ^ref-harness-engineering
```

- **The link targets the ref note, not the PDF.** The ref note is the hub: title,
  source URL, highlights, audio player, and the PDF link. Use a path-qualified link
  (`ref/…`) so basename collisions can't misresolve it. The alias is the title with
  `[ ] | # ^` and backticks removed.
- **The block ID is `ref-` plus a slug from the title.** Use the existing
  stopword-aware suggester (`capture_block_ids.rs:607-700`; ≤32 characters, first
  phrase). Fall back to the stem. The used-set is the destination note's IDs plus its
  `done_tasks` file's IDs, so a later archive never collides. Examples:
  `ref-harness-engineering`, `ref-dot-swarm` (illustrative).
- **`[created::]`** comes from the ref note's `created` field, matching every other
  task.
- **No `#hide`, no `[fresh::]` on creation.** Creation never stamps freshness. A new ref
  walks in REFERENCES, as never-confirmed refs do today.
- **`#task #ref` stays the stored text.** Dataview, Tasks, `bob query`, and grep keep
  working.

### 3.3 The glyph: one identity slot, a bookmark

`docs/task-tag-marks.md` already replaces `#task` with a teal hash glyph. The ink means
"tracked task" and never encodes state. Extend it so **the glyph's shape encodes kind
and its ink stays the same**:

```text
today:  - [ ] #task #ref [[lib/papers/harness_engineering.pdf]] #hide        (lives in ref/…)
after:  - [ ] 🔖 Harness Engineering: Anatomy, Architecture, and Evolution…  + Oct 9
        - [ ] ⌗  Add support for new %hold directive!                          + Aug 21
              (🔖 ≈ a thin teal bookmark outline; ⌗ ≈ the existing teal hash)
```

- **A single slot.** When an exact `#task` token is followed by an exact `#ref` token,
  the Live Preview widget replaces the whole `#task #ref` range with one bookmark glyph.
  Two glyphs per line would undo the noise reduction that task-tag-marks exists for.
  The cursor or a click reveals both raw tags. Hovering shows
  `#task #ref · reference task · parent sase`.
- **Why a bookmark.** The dashboard's reading queue is already "🔖 Reading Queue"
  (`340-dashboard-views-and-plan-block.js:1-17`), so the bookmark becomes the visual
  word for "reference" on every surface:
  - **Obsidian:** a 16×16 stroked mask, for example
    `M4.5 2.5h7v11l-3.5-2.6-3.5 2.6z`, round joins, `stroke-width 1.8`.
  - **Mac pickers:** SF Symbol `bookmark`.
  - **Mac Refs panel:** unchanged.
  - **CLI human output:** `🔖`.
- **The ink stays teal.** The hue table in `task-tag-marks.md` has every other hue
  taken. Red, orange, yellow, green, and blue encode state; violet means tags and links;
  cyan means code. A ref task is a tracked task, so it keeps the identity ink and gets a
  different shape.
- **Reading view and Tasks results.** Use the same post-processor, keyed on the
  `a.tag[href="#ref"]` that follows a `#task` mark. In `dash.md` Tasks results, where
  `#task` is already hidden by CSS, a CSS-only rule draws the bookmark for
  `[data-tag-name="#ref"]`, because there `#ref` carries information.
- **Pickers drop `#ref` from display text** (like `#task` today). `capture-complete`
  candidates gain an additive `task_kind: "ref"` (and `ref_path`) so the Mac app draws
  `bookmark` without parsing tags, per R8.

### 3.4 The ref note after the move

```markdown
---
parent: "[[sase]]"          # derived from the task's residence (A1)
type: "[[ref]]"
status: ready               # still the 3-way synced reading status
finished: 2026-10-12        # new, note-owned; stamped once when the task closes (A7)
…
---
# Harness Engineering: Anatomy, Architecture, and Evolution of Agent Harnesses

![[sase#^ref-harness-engineering]]

## Highlights
…
```

- The `^ref` line becomes a **managed embed** in the same slot. Opening the ref note
  shows the live task line: its checkbox, the bookmark, and the lane tint.
- Ctrl+Shift+M (`250-task-move.js`) and `bob task archive` (`collect_done/link_repair.rs`)
  already rewrite `[[note#^id]]` links vault-wide, ref notes included, so the embed
  follows moves and archiving for free.
- Scan heals it if a hand edit breaks it.
- It is a view, never the identity (§3.5). An embed in a ref note is not under a
  Pomodoro or a task, so it is neither a Task Link nor a dependency edge.
- `region.rs` treats the embed line the way it treats the old tracker: it is excluded
  from `own_notes`.

### 3.5 Finding a ref's task (the locator)

Build one index per command:

1. Scan vault Markdown with the same exclusions as `bob task reconcile` (hidden
   directories, `_generated`, `_templates`, `_conflicts`), **including `done/`**.
2. Keep task lines carrying the whole-token `#ref` whose first wikilink resolves
   (through `vault_links::NoteIndex`) to a note under the configured ref directory.
3. Map each ref note to its candidates.

Selection:

1. The unique **open** candidate outside `done/` is the live task.
2. Otherwise, the newest **closed** candidate, preferring one outside `done/`, defines
   the terminal state.
3. Otherwise, the ref falls back to its v1 in-note `^ref` tracker (frozen closed refs,
   A8).
4. Otherwise, frontmatter `status`, which is today's fallback.

Diagnostics (warnings in `bob ref doctor`, `diagnostics[]` on rows):

| Code | Meaning |
| --- | --- |
| `multiple_open_ref_tasks` | Several open tasks link the same ref. Status falls back to frontmatter, as `multiple_ref_trackers` does today. |
| `ref_task_outside_area` | The open task lives outside an area, project, or inbox note (a stray). |
| `open_ref_task_in_done` | Someone reopened a line inside `done/`. |
| `orphan_ref_task` | A `#ref` task has no link to a ref note. |
| `open_ref_without_task` | The ref note's status is open but no task exists. Scan never silently re-creates a deleted task. |
| `open_v1_tracker` | An open in-note `^ref` remains. Run `bob ref migrate-tasks`. |

Cost: one pass over about 6,200 files. `bob task reconcile` and the `&`/`!` pickers
already do vault-wide scans, and `ref_library` already walks every ref note.

### 3.6 Status sync across files

The policy in `highlights-ref-sync.md` is unchanged. Only the write sites move.

| Event | Today | After |
| --- | --- | --- |
| New ref note (scan) | Writes the `^ref` line into the ref note body | Inserts the task line into the parent's `## Tasks` intake using **capture's insertion path** (the same bytes `bob capture @sase` would write). `bob task reconcile` then groups it. Then writes the ref note with the managed embed. |
| Mark changed by you | Scan reads the in-note line as a status signal | The same signal, read through the locator |
| Marker or frontmatter status changed | Rewrites the in-note checkbox. The dirty-guard allows a checkbox-only diff. | **A one-character checkbox edit on the located line**, verified against the line's bytes at plan time (stale-safe line+hash locator, as the `!` complete picker uses), under the vault-maintenance lock that `reconcile` holds. A dirty Git state is fine, since capture writes dirty notes all the time. The guard changes from "the file is clean" to "this line hasn't changed". |
| Close date | `[completion::]` / `[cancelled::]` inserted before `^ref` | Same, anchored on the located block ID. Also stamps `finished` on the ref note. |
| Task archived to `done/` | (never happened) | Nothing to do. The locator still finds it. Scan **never writes into `done/`**. |
| Reopen signal for an archived ref | n/a | Write a **fresh open line** in the parent's Tasks (same ID if it's free there, else `-2`). The archived line stays as history, and Pomodoro links to it stay truthful. Selection rule 1 makes the new line live. |
| Parent | Marker → frontmatter | Residence → frontmatter (→ marker on `--write-pdfs`). The marker `parent` is only the birth hint for the first scan. |

Who writes what stays strict. `bob ref scan`/`sync` remain the **only** writers of ref
note frontmatter. `bob task reconcile` does not learn ref semantics, which avoids a
second writer of `status`. `refs.base` latency is unchanged from today (frontmatter
catches up at the next scan). `bob ref list`, `show`, `find`, and the Mac Refs panel
derive `status` and `parent` **live** from the task, so they never lag.

### 3.7 Parent resolution (one resolver)

`resolve_parent(name)`:

- **Candidates:** the existing capture-target set (vault-root area notes, non-terminal
  project notes, and the inboxes; `capture_targets.rs:220-331`).
- **Order:** an exact stem match (case-insensitive), then `aliases` (A4), then an error.
- **Errors** list up to 3 near misses and the fix, for example:

  ```text
  bob ref create: error: no area or project named 'bob-cli'
  hint: did you mean bob (project · bob.md)?
  hint: to accept this name, add `aliases: [bob-cli]` to bob.md
  ```

- **Ambiguity** (two notes claim one alias) is an error that names both.
- **Output:** the canonical stem. Markers and links never store an alias.
- **Users:**
  - `bob ref create -P`, which resolves before pandoc, the browser, or any write;
  - `bob ref list -P`, which becomes alias- and case-aware instead of today's exact
    string compare at `list.rs:241-245`;
  - capture `@route`, so `@bob-cli` now works too;
  - Keep labels;
  - the migration.
- **`bob capture-targets` JSON gains `aliases: []`** (additive), so the Mac app's
  cached Destination completion also matches `bob-cli`.
- **A parent that closes or disappears between create and scan:** scan files the task
  in `mac_inbox` with a `⚠️ parent sase_x is closed — refile me` child, mirroring the
  ref-job fallback. It never fails the scan.

### 3.8 Entry points

**`bob ref create`**: `bob ref create <TARGET> -P <PARENT> [...]`. `-P` is required
with no default. The dry run prints `parent: sase (project · sase.md)`. Sequence the
rollout so the sase hook passes `-P` **before** `-P` becomes required (§6).

**`bob capture` and Bob Mac Capture**: grammar-only, thin client.

- **Grammar:**
  - `https://… @sase` becomes a **ref item with parent `sase`**. Today, any `@route`
    turns a bare URL back into a task (`capture_language/item.rs:78-121`); that rule
    narrows to "extra prose, markers, or children keep it a task".
  - `@@sase` applies to every bare-URL item in the draft.
  - `-R/--no-ref` is still the escape hatch.
- **Bare URL:** still a ref item, plus a new **soft need** `ref_parent` in
  `capture-parse` output, and `ref.parent: {route, label, kind, source:
  "explicit"|"default"}` in `capture --dry-run`. The default is `mac_inbox` (A2).
- **Ref job JSON** (`ref_jobs/spool.rs`) gains `parent`. `ingest_url` takes it
  instead of `INGEST_PARENT`. A failed clip falls back to the task `URL @sase` would
  have written, in `sase.md` rather than the inbox.
- **Mac UX:**
  - When the draft is a bare URL, the existing Destination completion opens on its own
    (source: the cached `capture-targets`, filtered to area/project/inbox kinds, header
    **"File under"**). Enter inserts ` @sase`; Esc keeps the default.
  - The preview card reads `🔖 queue example.com/essay → sase` or
    `🔖 queue example.com/essay → mac_inbox · file it later`.
  - The new `CapturePickerNeed` case mirrors `applyQuietIncompletePicker`
    (`CapturePanelModel.swift:3241-3289`). No Swift grammar is added.

**`bob gkeep pull`** (A10):

- A URL-only note may add a trailing `@route` (it stays URL-only for routing), or carry
  a Keep label that resolves.
- `-P/--parent ROUTE` applies to every unrouted URL in the pull. `-P` is free; `-p` is
  `--pinned`.
- On a TTY, after planning and before clipping, prompt once per unrouted URL:
  `File “The Dot and the Swarm” (example.com) under [gkeep_inbox]: `. The answer is
  validated through the resolver, with near-miss hints.
- Without a TTY, use `gkeep_inbox`.
- `list` shows the planned parent next to its `🔗 ref` hint.

**sase research hook** (A11):

- **sase change:** `src/sase/file_hooks/runner.py:_execute_run` (lines 157-177) sets
  `env["SASE_FILE_HOOK_PROJECT"] = run.get("project")` when the value is known and not
  `"unknown"`. Add siblings `SASE_FILE_HOOK_REL_PATH`, `…_OP`, `…_REPO_KIND`,
  `…_AGENT`, and `…_NAME`. Use `.get` (as line 139 does) so old batches still run.
  Document them in `docs/configuration.md:3749` and the schema `command` description.
  Test in `tests/file_hook_engine/test_dispatch.py`.
- **Config** (chezmoi source of `~/.config/sase/sase.yml`):

  ```yaml
  file_hooks:
    - use: sase-research-artifacts@research-highlights
      command: bob ref create --include-id -P "$SASE_FILE_HOOK_PROJECT"
  ```

  The live hook today is `bob highlights create --include-id`, which is a permanent
  alias of `bob ref create`.
- **Vault:** `bob.md` gains `aliases: [bob-cli]`. `sase` matches `sase.md` by stem.
- **An unresolvable or unknown project** makes `bob ref create` exit with the hint
  above. The existing file-hook notification (`❌ research-highlights failed`) surfaces
  it.
- **Zero-code fallback** if the sase change slips: two hooks with
  `filters.projects: [sase]` and `[bob-cli]`, each hard-coding `-P`.
- **Don't use `sase project current`.** It returns the most recently used project, not
  the one that produced the file.

### 3.9 The special-case ledger

| Special case | Fate | Why |
| --- | --- | --- |
| `#hide` on generated ref lines (`note.rs:84-90`) | **Remove** (writer and migration) | The single lever that hides refs from dash, lanes, caps, Today, and `^^` |
| Residence exception "a ref note's own ref task" | **Remove** | R1 |
| Default parent `obsidian_ref` / `INGEST_PARENT` | **Remove**; parent required and resolved | A2, A3 |
| Capture rule "URL plus `@route` is a task" | **Change**: it's a ref with a parent | §3.8 |
| `parse_pdf_task_line` (one `^ref` per file, `.pdf` link required) | **Replace** with the locator (§3.5); keep it read-only for v1 | R2, A8 |
| Dirty guard's `^ref` checkbox allowance (`guard.rs:236-322`) | **Remove** for v2; the cross-file line guard replaces it | §3.6 |
| Annotation tasks into the ref note's `## Tasks` | **Change**: default to the parent | A9 |
| Audio embed anchored after `^ref` (`audio.rs:135-142`) | **Change**: anchor after the managed embed or before `## Highlights` | R3 |
| `git log -G\^ref` date fill | **v1 only**; v2 uses `created` and `finished` | A7 |
| Freshness `TrackerKind::Ref` by exact block ID (Rust and JS) | **Change**: key on the exact `#ref` tag | A5, A6 |
| REFERENCES tier and `reference_interval` | **Keep** | A6 (your explicit config) |
| `#hide` bypass for ref trackers (`scan.rs:341-371`, `160-widgets-and-row.js:328-360`) and "hidden refs still count" status-bar logic | **Remove** (dead once refs are visible) | R6 |
| `#^ref` reading embeds aren't dependency edges (`task_status_hooks/references.rs:306-311`, nav `130-fences-and-status.js`) | **Keep** for v1 links; generalize to "an embed of a `#ref` task is content" | The managed embed in ref notes |
| `^prj` exemptions (move, cap, reroll) | **Keep**, do not extend to refs | A ref task is work, not a project lifecycle marker |
| Per-note Ready cap, Next/Pending caps | **Count refs** (no exemption) | The cap's job is honesty about commitments; reading is one |
| `bob task archive` | **No exemption** | A7 |
| Mac Refs panel Today join on `today_tasks[].path` (`RefsToday.swift:24-36`) | **Change**: `bob plan` rows gain additive `ref_path`, and Swift joins on it | It silently empties otherwise |
| Mac Refs watcher on `ref/` and `lib/` only (`RefsLibrary.swift:490-503`) | **Change**: also refresh when vault-root notes change (the app already watches them for `capture-targets`) | Status edits now happen in `sase.md` |
| Mac `parentLabel` strips `_ref` hub suffixes (`RefsModel.swift:413-423`) | **Keep** (harmless); it now shows real parents | — |
| Inspector "Tasks N open" from `ref show` | **Change**: `ref show` adds a `task` object (`path`, `block_id`, `link`, `mark`, `archived`) | R3 |

### 3.10 What changes for you (invariant impact)

| You rely on… | After the redesign | Mitigation |
| --- | --- | --- |
| Reading never consumes Next/Pending slots | It does. Next 14→22/15 and Pending 7→15/10 if migrated as-is. | Triage in the migration (§4.2). The caps warn (`strict: false`) and never refuse. |
| Reading never crowds a note's Ready cap | `sase.md` gains about 6 Ready refs against a default cap of 5 → CROWDED | Release or abandon stale refs, or set `ready_cap:` on `sase.md` |
| Refs reviewed weekly, never in NEW, PENDING, or NEXT | **Unchanged** (A6) | — |
| A ref's status visible in `refs.base` | Same latency as today (hourly scan); CLI and the Refs panel are live | — |
| `^` picker excludes reading | It now shows `[*]`/`[/]` refs with the bookmark | This is what you asked for |
| Closed ref tasks stay in ref notes | Closed v2 refs archive with their project once it has 10 or more closed tasks | `finished` stamp plus the done/-aware locator |
| `[[x#^ref]]` links | Rewritten to `[[sase#^ref-x]]` for the 27 migrated refs; links to closed v1 refs untouched | — |
| `bob freshness` JSON | `tracker` source becomes the tag; schema bump; plugin API capability unchanged (`referenceReview: true`) | Rust and JS land together under the walk vectors |

---

## 4. Migration

### 4.1 Scope and command

- **In scope:** the 27 refs with an open in-note `^ref` (A8).
- **Command:** `bob ref migrate-tasks [-f human|json] [-o/--offline] [-w/--write]`. It
  copies the shape of `bob ref migrate-zorg`: a dry run by default, and a reversible
  single commit with `-w`.

Steps:

1. **Preconditions.** Each ref's frontmatter `parent` must resolve (§3.7) to an area,
   project, or inbox note. Refs whose parent is a hub such as `obsidian_ref` are listed
   as `needs_parent` with the suggestion from §4.2, and the run refuses until they're
   set. Setting them is a frontmatter edit: a frontmatter-only change that the next
   PDF-writing scan pushes to the marker.
2. **Lock and pre-sync.** Take `bob_sync.lock`, run `vault-sync`, and re-plan from
   disk.
3. **Per ref:**
   1. Render the v2 line from the v1 line. Keep the mark, `[fresh::]`, `[id::]`,
      `[dependsOn::]`, any close fields, and all child lines (including a Depends-On
      line). Drop `#hide` and the PDF link. Add `[created::]` and `^ref-<slug>`.
   2. Insert it into the parent's `## Tasks`.
   3. Replace the v1 line in the ref note with the managed embed.
4. **Rewrite links vault-wide** with the archive link-repair engine
   (`collect_done/link_repair.rs`): `[[x#^ref]]` / `[[ref/…/x#^ref]]` →
   `[[parent#^ref-slug]]`. That is 17 occurrences in 4 files, including
   `sase_blog_0.md`'s Depends-On line. Also rewrite path-derived `[id::]` /
   `[dependsOn::]` (for example `ref__chat__sase_launch_post_outline__ref` →
   `sase_blog_0__ref-launch-post-outline`).
5. **Verify** through the rebuilt index. Every migrated ref resolves to exactly one
   live task, its status and reading state are unchanged, and no new
   `multiple_open_ref_tasks` diagnostics appear. On any failure, restore the originals
   and exit 1.
6. **Commit and post-sync.** Commit as
   `bob ref migrate-tasks: N ref tasks into M notes`, then post-sync.
7. **Rollback:** `git revert <sha>`, as in the `migrate-zorg` runbook.
8. **Then run `bob task reconcile`** so `[*]`/`[/]` refs land in "Next & In Progress".

### 4.2 Suggested parents and lane triage (please confirm or override)

The parents below are my reading of titles, links, and wrapper tasks, not ground truth.
The triage column flags refs whose wrapper you already closed (§1.3) or that are older
lane items. Releasing `[*]`/`[/]` → `[ ]`, or abandoning with `[-]`, **before**
migrating keeps the lanes under cap.

| Ref (stem) | Mark | Suggested parent | Note |
| --- | --- | --- | --- |
| `agent_history_in_agents_tab` | `[*]` | `sase_agent_history` | wrapper cancelled 10-06 → **release or abandon?** |
| `agent_image_generation_toolset` | `[*]` | `sase_art` | |
| `agent_instructions_budgeted_router` | `[?]` | `sase_memory` | depends on `sase#^dynamic-agents-md`; wrapper cancelled |
| `auto_directive_autonomy_policy` | `[*]` | `sase` | |
| `goals_redesign_recent_reading_list` | `[*]` | `sase_goals` | |
| `memory_and_instruction_file_inspiration_reading_list` | `[*]` | `sase_memory` | |
| `memory_built_instruction_migration_epics` | `[*]` | `sase_memory` | |
| `research_swarm_improvement_roadmap` | `[*]` | `sase` | wrapper cancelled 10-08 → **release or abandon?** |
| `toobig_split_beyond_python` | `[*]` | `sase_toobig_symvision` | wrapper cancelled 10-06 ("Too ambiguous") → **abandon?** |
| `athena_cpu_saturation_orphaned_load_loops` | `[/]` | `sase` | |
| `auto_autonomy_epic_roadmap` | `[/]` | `sase` | |
| `databricks_omnigent_job_fit` | `[/]` | `job` | |
| `sase_launch_post_introduction` | `[/]` | `sase_blog_0` | a dependency of `sase_blog_0`'s review task |
| `sase_launch_post_outline` | `[/]` | `sase_blog_0` | same |
| `sase_listen_plugin_commands` | `[/]` | `sase` | |
| `sase_task_bead_48h_impact_rating` | `[/]` | `sase_better_tasks` | |
| `tools_bg_split_and_tool_run_visibility` | `[/]` | `sase` | |
| `global_just_recipe_completion` | `[ ]` | `dev` | |
| `goals_inspiration_round_two_reading_list` | `[ ]` | `sase_goals` | |
| `sase_md_instruction_delivery` | `[ ]` | `sase_memory` | |
| `sase_next_direction_reading_list` | `[ ]` | `sase` | |
| `harness_engineering` | `[ ]` | `sase` | wrapper **completed** 10-05 → probably `[x]` |
| `agentic_software_engineering` | `[ ]` | `sase` | |
| `what_does_a_harness_buy_tokens` | `[ ]` | `sase` | |
| `introducing_omnigent_meta_harness_…` | `[ ]` | `sase` | |
| `the_dot_and_the_swarm` | `[ ]` | `sase` (or `dev`) | |
| `understanding_is_the_new_bottleneck` | `[ ]` | `dev` | |

To fit the caps, you'd need to release or close at least 7 of the 8 `[*]` and 5 of the
8 `[/]`. The four flagged rows are the obvious first cuts.

### 4.3 Wrappers

None of the wrappers for the 27 open refs is still open; all are closed or archived. The
dry run should still report any **open** task whose child embeds a migrated ref
(`![[…#^ref]]`) as `possible_wrapper`, so future duplicates get merged by hand rather
than automatically.

---

## 5. Change list by repository

**bob-cli**

- Shared `resolve_parent`. Add `aliases` to `capture-targets` JSON.
- `bob ref create -P` required and resolved.
- `ref_jobs` and `ingest` carry the parent.
- Capture grammar: `URL @route`/`@@route` become refs. Add the `ref_parent` soft need
  and the `ref.parent` preview.
- `gkeep pull`: parent routing and `-P`.
- v2 writer in scan (capture insertion) and the managed embed. Make `region.rs` and
  `audio.rs` embed-aware.
- Locator and diagnostics; `ref_library` derives status, parent, and dates from it.
- Cross-file checkbox writer; close stamp; `finished`; reopen-from-archive.
- Annotation tasks default to the parent.
- `bob plan` `today_tasks[].ref_path`. `capture-complete` `task_kind`/`ref_path`.
  `ref show` `task` object.
- Freshness: tag-keyed ref tracker; remove the hide bypass.
- `bob ref migrate-tasks`.
- Docs: `ref.md`, `highlights-ref-sync.md`, `capture.md`, `gkeep.md`,
  `freshness.md`, `task-tag-marks.md`, `projects.md`.

**bob-plugins** (`bob-ledger-tools`, `bob-navigation-hotkeys`)

- `freshnessTrackerFromBlockId` → tag-keyed ref detection. Remove the hidden-ref bypass
  in `160-widgets-and-row.js` and the "hidden references still count" status-bar
  logic. Keep the REFERENCES tier, labels, footer, and capability.
- Task-tag-marks: the `#task #ref` → bookmark identity slot (`138-task-tag-marks.js`,
  `264-plugin-task-tag-marks.js`, `styles.css`) plus conformance vectors.
- Strip `#ref` from picker display text the way `#task` is stripped
  (`020-config-load-and-tasks.js:273-288`, `block-id-prompt/030-…:158-178`).
- Generalize "an embed of `#^ref` is content" to any `#ref` task embed.
- Then `bob plugins sync`.

**bob-mac-capture**

- Decode `ref.parent`, the `ref_parent` need, `aliases` on targets, `task_kind`, and
  `ref_path`, all with `decodeIfPresent`.
- Auto-open Destination ("File under") on bare URLs.
- Bookmark symbol on ref rows.
- Join Refs Today on `ref_path`; refresh Refs when root notes change.

**sase**

- `SASE_FILE_HOOK_*` environment variables in `file_hooks/runner.py`, plus docs, schema
  text, and tests.

**Config and vault**

- chezmoi `dot_config/sase/sase.yml`: the hook command gains `-P`.
- `bob.md`: `aliases: [bob-cli]`.
- After migration, the hub notes (`obsidian_ref`, `sase_ref`, …) stay as parents of
  closed refs only.

**SASE memory** (use `/sase_memory_write` when implementing; I made no memory edits)

- A new decision record, "Ref tasks live with their parent". It supersedes the residence
  exception and records A1, A5, A6, and A7, and their rejected alternatives (§7).
- Glossary updates: `reference-task` (identity, `^ref-<slug>`, residence),
  `reference-note` (no tasks, managed embed, derived `parent`), and `area-note` (drop
  the ref exception).
- `review-walk-is-tiered` stays as accepted. Only its `^ref` keying changes, which
  needs a small superseding note, because records are never edited in place.

---

## 6. Sequencing

1. **sase environment variables**, then update the hook config to pass `-P`. Do this
   first: it is harmless while `-P` still has a default.
2. **The resolver and aliases** (bob-cli), and `aliases: [bob-cli]` on `bob.md`.
3. **v2 model in bob-cli:** locator, writer, cross-file sync, managed embed, `finished`,
   additive JSON. Every reader still understands v1.
4. **Make `-P` required** and wire capture, ref jobs, and Keep parents. Use the soft
   need, defaulting to the inbox.
5. **Freshness re-key and task-tag-marks glyph** in Rust and JS together, under the walk
   and glyph vectors.
6. **Lane triage, then `bob ref migrate-tasks -w`**, then `bob task reconcile`.
7. **Bob Mac Capture:** parent picker, bookmark rows, Refs Today join. It is
   independent of steps 5–6 and gated by macOS CI.
8. **Decision record and glossary updates.**

Hard ordering constraints:

- Step 1 must come before step 4, or research imports start failing.
- Step 3 must come before step 6, so the migration uses the shipped writer and locator.
- The Refs Today join (step 7) should ship soon after step 6. Until then, the Refs
  panel's Today section is empty for migrated refs.

---

## 7. Alternatives considered and rejected

- **Keep ref tasks in ref notes and teach bob that a ref note "belongs" to its parent.**
  Every residence-based surface (grouping, caps, the `^` and `:` pickers, capture
  targets, Ctrl+Shift+M destinations) would need a virtual-residence rule. That is more
  special-casing, the opposite of the goal.
- **No ref task at all: status only in frontmatter, with a per-project Dataview of child
  refs.** It can't be a Pomodoro Task Link, a dependency target, or a lane item, which
  is exactly how you use refs (§1.3).
- **Status quo with wrapper tasks.** Double booking; 19% of open refs have already
  drifted.
- **Frontmatter `parent` as the source of truth, with the task following it.**
  Ctrl+Shift+M would desync immediately, and a "move the task when the parent field
  changes" daemon is a second writer. A1 picks residence.
- **Block-ID identity (`^ref-*` prefix).** Fragile under hand renames and archive
  collision suffixes. A tag plus link is robust, and the prefix stays a readable
  convention.
- **Exempting ref tasks from archive.** Hundreds of closed lines would sit in project
  notes. The history belongs on the ref note (A7).
- **Dropping the REFERENCES tier too.** It's defensible for purity, but it would cost
  about 16 daily lane decisions and override a cadence you configured (A6). It remains a
  small follow-up if you want it.
- **A `{project}` placeholder in sase hooks.** It introduces a template language and
  quoting hazards. Environment variables are additive and shell-native.
- **A dedicated `project_name_aliases` key.** It's too narrow for areas, and duplicates
  Obsidian's native `aliases` (A4).

## 8. Open questions for you

1. Confirm or override the parent table (§4.2), and pick the lane triage, before the
   migration runs.
2. A6: keep the weekly REFERENCES cadence (my recommendation), or make refs fully
   ordinary, which means daily lane review?
3. A4: `aliases` (my recommendation) or a dedicated `route_aliases` key?
4. A7: archive normally (my recommendation), or honor the 10-08 "no done cleanup" note?
5. Glyph: a bookmark in teal identity ink (my recommendation), or an open book?

---

## 9. Recommended solution

**Move each open ref task into the `## Tasks` section of a real area, project, or
inbox note, and make that location the reference's parent.**

- **Task line:**

  ```markdown
  - [ ] #task #ref [[ref/<type>/<stem>|<Title>]] [created:: …] ^ref-<slug>
  ```

  No `#hide`. It renders as a single teal **bookmark** glyph in the task-tag-mark slot.
- **Ref notes:**
  - hold no tasks;
  - show their task through a managed `![[parent#^ref-slug]]` embed;
  - derive `parent` from the task's residence (including through `done/`);
  - stamp `finished` when the task closes.
- **Status sync:** the three-way policy stays the same. It finds the task with a
  done/-aware locator keyed on `#ref` plus the ref-note link, writes single-line
  checkboxes under the vault lock, and handles a reopened archived ref with a fresh
  line in the parent.
- **Special treatment:** ref tasks count everywhere like ordinary tasks (lanes, caps,
  Today, `^`, archive). The one exception is the REFERENCES review cadence you
  configured, re-keyed to the `#ref` tag.
- **Parents are resolved by one resolver** (stem, then Obsidian `aliases`; inboxes
  allowed) and required on:
  - `bob ref create -P` (the existing flag, made required);
  - capture `URL @route` (the Mac app auto-opens "File under", defaulting to
    `mac_inbox`);
  - `bob gkeep pull` (`@route`, a Keep label, `-P`, a TTY prompt, else `gkeep_inbox`);
  - the sase research hook, through a new `SASE_FILE_HOOK_PROJECT` environment variable,
    with `aliases: [bob-cli]` on `bob.md`.
- **Migration:** only the 27 open refs migrate, through a reversible
  `bob ref migrate-tasks` commit that rewrites 17 links and their dependency IDs, after
  a lane triage that keeps Next and Pending under their caps. Closed and zorg-era refs
  stay frozen.

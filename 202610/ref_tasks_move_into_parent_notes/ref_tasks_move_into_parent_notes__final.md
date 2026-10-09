# Ref Tasks Move Into Their Parent Notes

*Consolidated research · lead researcher · 2026-10-09 · merges the `cdx`, `cld`, `grk`,
`mus`, and `gem` reports (siblings of this file) with my own checks against bob-cli
`b566ba4`, sase `9c5000f2db`, Bob Mac Capture `d5fcac0`, the live `~/bob` vault, and
`~/.config/bob/config.yml`. Nothing was implemented or migrated.*

The request: every open ref note gets an area or project note as its parent, and its ref
task moves into that note's `## Tasks` section like any other task. Existing open ref
tasks get migrated. Sync with the ref note has to survive the task being archived into
`done/`. The logic that hides ref tasks goes away. Capture paths (Bob Mac Capture,
`bob gkeep pull`, the sase research file hook) ask for or receive the parent, through a
new required parent option on `bob ref create`. Project notes gain `project_name_aliases`
(`bob-cli` → `bob.md`). Ref tasks get unique block IDs and an icon in place of `#ref`.

---

## 0. Bottom line

**Verdict: yes, do it.** All five researchers agree, and the vault backs them up. Ref
tasks already behave like ordinary work: you link them from Pomodoros, use them as
Depends-On prerequisites, and write wrapper tasks for them in project notes. The wrapper
habit has already caused the double-booking drift a single task would prevent. The
current design files this work in the library instead of with the work it serves.

**The change is smaller than it looks in one way and larger in another.**

- *Smaller:* ref tasks are hidden by two side effects, not by scattered filters:
  1. every generated line carries `#hide`;
  2. the line lives under `ref/`, which is not a root area or project note.

  Bob Mac Capture has no ref filter at all. Move the line and drop `#hide`, and lanes,
  caps, Today, the `^` picker, status grouping, and archiving pick refs up through code
  that already exists.
- *Larger:* `^ref` is currently three things at once: the task's address, the library's
  "this is the tracker" recognizer, and the freshness walk's tracker identity. Every
  reader assumes the checkbox sits in the ref note. All of those assumptions need to be
  replaced by one done/-aware association rule. Otherwise a moved or archived task looks
  missing, gets recreated, or puts the wrong refs in Today.

### Adjustments to your requirements (each is a deliberate departure)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **J1** | New required `-p\|--parent` on `bob ref create` | Keep the existing `-P\|--parent`, make it required, and drop the `obsidian_ref` default | `-p` is already `--published`, and `--parent` already exists (`create.rs:324-337`). 4 of 5 researchers agree. |
| **J2** | Ref note lists an area/project as its `parent` | **The task's location defines the parent.** Frontmatter `parent` becomes a projection of where the ref task lives. For an archived task, it is the `done/` file's own `parent:`. | Two sources of truth would drift the first time you press Ctrl+Shift+M. Re-filing a reference becomes the same gesture as re-filing any task. |
| **J3** | Prompt for a parent at capture | Prompt where a human is present: the Mac app's picker opens on its own, and `gkeep pull` asks on a TTY. Unattended paths default to the **inbox area note** the equivalent task would land in. `bob ref create` itself has no default. | Inboxes are `type: "[[area]]"` notes, so the parent rule holds. Capture never blocks, and inbox triage then re-files the task, which sets the parent (J2). |
| **J4** | Remove (probably) all ref special-casing | Remove everything except two things: **Ready refs keep the weekly REFERENCES review**, and the PDF/frontmatter/checkbox status sync stays. Next and Pending refs become ordinary lane rows with daily review. | `reference_interval: 7` is a cadence you chose. Exempting refs from daily lane review, though, is exactly the kind of quiet exception you want gone. |
| **J5** | New, unique block ID | The block ID `^ref-<slug>` is only an *address*. A ref task is **identified** by its `#ref` tag plus a path-qualified link to its ref note. | Archiving renames block IDs on collision, and stems are not unique (§1.4). |
| **J6** | (Implied) the `^better-refs` note: "permanently … no done cleanup … References" | **Archive ref tasks normally into `done/`**, from `## Tasks`. | Your request anticipates `done/`. About 6 research refs arrive per day, which would pile up forever in `sase.md`. A References section would be a new special case. |
| **J7** | Migrate "all … currently open ref notes" | Migrate the **27 open modern ref tasks** only. The ~320 closed trackers and 602 zorg-era legacy notes stay frozen. | The legacy notes have no task to move. Activating their 355 queued/started records would be a separate product decision. |
| **J8** | (Not stated) annotation follow-up tasks | New Highlights follow-up tasks default to the ref's parent note too | Otherwise ref notes keep spawning tasks under `ref/`, which recreates the exception. |
| **J9** | `project_name_aliases` on project notes | Same key, but also honored on area notes, and used by every name lookup | The name means "external project names", not the note's type. One resolver serves `ref create`, `gkeep`, `ref list -P`, and the hook. |
| **J10** | sase injects the project into the hook command | Inject it as an **environment variable** (`SASE_FILE_HOOK_PROJECT`), not a `{project}` placeholder | The runner already uses `shell=True`. A quoted variable needs no template language and has no quoting hazards. |
| **J11** | (Not stated) how a parent travels through capture | **`URL @route` becomes a ref filed under that route** instead of a plain URL task | One routing vocabulary: `@route` always names where the task lives. Extra words and `-R` still keep the item a plain task. |

---

## 1. What exists today (verified)

### 1.1 The ref task today

`bob ref create` writes an intake PDF to `xlib/`. Its page-1 marker carries `status` and
`parent`, and the parent defaults to `obsidian_ref` (`highlights_ref/create.rs:41`).
Background ingest, which covers capture ref jobs and Keep, hard-codes
`INGEST_PARENT = "obsidian_ref"` (`highlights_ref/ingest.rs:32`). Later, `bob ref scan`
moves the PDF into `lib/` and writes the ref note with its tracker under the H1:

```markdown
- [ ] #task #ref [[lib/papers/harness_engineering.pdf]] [fresh:: 2026-10-07] #hide ^ref
```

The checkbox, frontmatter `status`, and PDF marker are kept in sync. The mapping is
`[ ]` ready, `[*]` next, `[/]` wip, `[x]`/`[X]` read, `[-]` abandoned, and `[?]` a Blocked
overlay that keeps the open reading status. A tracker-only change becomes a pending
projection. Independent changes on both sides are a conflict. PDF writes need
`--write-pdfs`.

Scan runs periodically on the Mac. The URL-intake research recorded a 15-minute cron;
`cld` reports an hourly LaunchAgent. Either way, a captured link becomes a ref note
minutes later, not seconds later. The ref-job worker clips the link but does not scan
(`ref_jobs/worker.rs`).

### 1.2 Where the "special treatment" really comes from

| Mechanism | Effect | Code |
| --- | --- | --- |
| `#hide` on every generated tracker | Keeps refs out of the `bob plan` lanes and lane counts, the dash, Ready/Next/Pending caps, and `^^` | lane queries with `tags do not include #hide` (`dataview/tasks/mod.rs`); plugin lane visibility |
| Residence under `ref/` | Keeps refs out of the `^` and `:` pickers, capture targets, status grouping, per-note Ready caps, and project counts | `capture_active_tasks.rs` scans only "routable vault-root notes"; no `#ref` or `#hide` filter exists there |
| Exact block ID `^ref` | REFERENCES walk tier with `reference_interval`; refs never walk NEW, PENDING, or NEXT; a `#hide` bypass lets hidden refs still walk | Rust `freshness/state.rs`, `scan.rs`; JS `bob-ledger-tools/src/100-freshness-evaluate.js`; `docs/freshness.md` "Tracking review" |
| One `^ref` per ref note, in that note | Status sync, close-date stamps, the dirty-note guard's checkbox allowance, annotation-task and audio-embed placement, `ref show` anatomy, `ref list -g` (`git log -G\^ref`) | `highlights_ref/{note,guard,annotation_tasks,audio,region}.rs`, `ref_library/{status,list}.rs` |

What is **not** special: `bob task archive` has no `^ref` exemption (ref notes just never
reach the 10-closed-task threshold), `task_status_hooks`, the `&` and `!` pickers,
Ctrl+Shift+M (it refuses only `^prj`), and **Bob Mac Capture's `^` picker**, which renders
whatever `bob capture-complete` returns. The Mac app does carry one hidden ref
assumption: the Refs panel keys Today by **note path** (`RefsCore/RefsToday.swift:14-36`).
Once several refs share `sase.md`, that join either loses their Today state or marks every
ref in the note as Today.

### 1.3 Your config and accepted decisions

- `freshness`: `interval: 7`, `pending_interval: 1`, `next_interval: 1`,
  `reference_interval: 7` (commented "Bryan's ^ref review cadence").
- `plan`: `max_next: 15`, `max_pending: 10`, `strict: false` (caps warn and never refuse).
- `decisions:review-walk-is-tiered`: Pending and Next come due for **daily** review. The
  "lane `^ref` walks REFERENCES on the reference cadence" carve-out lives only in
  `docs/freshness.md`.
- `decisions:note-ready-cap-counts-the-lane`: the cap counts each note's whole Ready lane
  **by residence**, excluding only recurring and `^prj` rows. Once refs move into area and
  project notes, they count unless a new decision says otherwise.
- `decisions:task-lanes-are-sticky` and `decisions:today-is-read-from-the-ledger`: both
  apply to refs unchanged. Today comes from Task Links; lanes are sticky.
- `decisions:mac-capture-is-a-thin-client`: every new capture behavior lands in bob-cli
  first. The app only decodes and presents it.
- Glossary `area-note` currently lists "a reference note's own reference task" as one of
  only three residence exceptions. `inbox-file` confirms that `inbox`, `mac_inbox`, and
  `gkeep_inbox` are `type: "[[area]]"`.

### 1.4 Live vault census (2026-10-09)

| Fact | Value |
| --- | --- |
| Open modern ref tasks | **27**: 10 `[ ]`, 8 `[*]`, 8 `[/]`, 1 `[?]`. All carry `#hide`, and all have `parent: "[[obsidian_ref]]"`. |
| Closed modern trackers | about 320 (`[x]` and `[-]`) |
| Zorg-era legacy notes (no tracker) | 602 |
| Open non-tracker `#task` lines anywhere in `ref/` | **0** |
| Links to the 27 open trackers (`…#^ref`) | **17**, in 4 files: `2026/20261006.md` (5), `20261007.md` (1), `20261008.md` (9), `sase_blog_0.md` (2) |
| Lanes now (`bob plan`) | Next 13/15, Pending 9/10, Today 11 (no refs in Today) |
| Research refs created 2026-10-01..09 (`ref/chat`) | **56**, of which 36 are already read and 2 abandoned: about **6 new reading items per day** |
| SASE projects enabled | `bob-cli` (→ `bob.md` needs the alias) and `sase` (→ `sase.md` matches by stem) |
| Obsidian `alwaysUpdateLinks` | `true`: renames inside Obsidian keep wikilinks valid |
| Native `aliases` in use | Display titles: "Blocked Tasks", "Dashboard References", "Job", "Inbox", "Obsidian" |

**Stems are not unique.** `ref/blogs/harness_engineering.md` (read) and
`ref/papers/harness_engineering.md` (open) both have `id: harness_engineering`. Any
design that keys on the stem or the frontmatter `id`, or that uses bare `[[stem]]` links,
will misresolve.

### 1.5 How you actually use ref tasks

- **As Pomodoro work.** `🍅 [[databricks_omnigent_job_fit#^ref]]` appears under timed
  entries in the 10-06 to 10-08 daily notes.
- **As prerequisites.** `sase_blog_0.md` has a Depends-On line pointing at two
  `ref/chat/…#^ref` tasks. Two ref tasks carry `[id::]`, and one carries `[dependsOn::]`.
- **Through wrapper tasks you write by hand in project notes.** These have exactly the
  shape this design proposes: `- [-] #task Read [[ref/chat/agent_history_in_agents_tab]]!`
  in `sase_agent_history.md`.
- **Drift from that double booking.** For **4 of the 27** open refs, the wrapper is
  closed while the ref task is still open:

  | Open ref task | Wrapper |
  | --- | --- |
  | `agent_history_in_agents_tab` `[*]` | `[-]` 2026-10-06 |
  | `agent_instructions_budgeted_router` `[?]` | `[-]`, archived to `done/sase_done.md` |
  | `toobig_split_beyond_python` `[*]` | `[-]` 2026-10-06 |
  | `research_swarm_improvement_roadmap` `[*]` | `[-]` 2026-10-08 |

  *Correction to `cld`, which counted 5:* the completed "Read [[ref/blogs/harness_engineering]]"
  wrapper belongs to the **blogs** ref, which is itself read. The open ref is the
  unrelated **papers** ref with the same stem. That mix-up is itself a good example of the
  stem-collision hazard.

### 1.6 Capture, Keep, and the hook

- **Capture grammar.** A bare, admitted public URL becomes `kind: "ref"`. "Anything more
  — an extra word, `@route`, `#tag`, … — keeps the item a task" (`docs/capture.md`
  §"Saving links to your reading queue"). Hosts in `DEFAULT_EXCLUDE_HOSTS` (google,
  youtube, github, x, twitter) always stay tasks. The ref job JSON stores the URL and an
  inbox fallback, but no parent.
- **Keep.** `gkeep pull` clips URL-only notes inline during the pull. It is always run by
  hand ("There is no scheduled runner", `docs/gkeep.md:444`). `-P` is free; `-p` is
  `--include-pinned`.
- **SASE hook.** `src/sase/file_hooks/runner.py:160` builds
  `f"{run['command']} {shlex.quote(abs_path)}"` and runs it with `shell=True` and
  `env=os.environ.copy()`. Each run already records `run["project"]` (`context.py`
  `project_name()`, which falls back to `"unknown"`), but nothing passes it to the
  command. The configured hook is
  `sase-research-artifacts@research-highlights` with
  `command: bob highlights create --include-id`, a permanent alias of `bob ref create`.

---

## 2. Critique: is this a good idea?

**What's right.**

1. **Residence is the root problem.** Reading something is work, and work lives in area
   and project notes. Removing the one lasting residence exception makes the model
   uniform. Everything residence-based starts working without new code: lanes, caps,
   grouping, pickers, Today, inbox routing, archiving, and project lifecycle (a project
   with an unread ref is not done).
2. **Required parents fix metadata that carries no information.** All 27 open refs say
   `obsidian_ref`. Real parents make `refs.base` grouping and the Refs panel's parent
   caption meaningful for the first time.
3. **Unique block IDs are mandatory, not cosmetic.** Two `^ref` tasks in one file break
   Ctrl+Shift+M ("Destination already contains block ID"), the Mac `^` dedupe on
   `route:block-id`, and `bob plan`'s Today resolver.
4. **Capture is the right moment to choose a parent.** That is when you know why you
   saved the link.

**Where the literal spec breaks.**

1. **Flag collision.** `-p` is `--published`, and `--parent` already exists (J1).
   Repurposing `-p`, as `gem` suggests, is a hard rename of a public option, which
   `cli_rules` forbids.
2. **"Required at create" doesn't reach the main capture paths.** Bare-URL capture and
   Keep call the typed `ingest_url`, not the CLI. A required flag on `bob ref create`
   leaves both hard-coded to `obsidian_ref` unless the parent is carried through
   `IngestRequest`, the ref job JSON, and the Keep journal (J3, §4.7).
3. **`done/` breaks sync's founding assumption.** No reader today looks for "the task of
   ref note X" outside note X. That locator is the hardest part of the project (§4.4).
4. **"Remove all special-casing" would silently change your review rhythm.** It would put
   Ready refs into NEW and ROTTEN decay, and erase a cadence you configured. Keeping all
   of REFERENCES, as `cdx`, `cld`, and `grk` suggest, would instead leave Next and Pending
   refs exempt from the daily lane review. J4 splits the difference along the line your
   config and decisions already draw.
5. **Volume.** Migrating as-is takes Next from 13 to 21 (cap 15) and Pending from 9 to 17
   (cap 10). Research refs add about 6 Ready items per day to `sase.md` and `bob.md`
   (default Ready cap 5). The caps should report this honestly. The fix is triage, not
   re-hiding refs (§5, §6.3).

**Would I take a different approach?** No. Every alternative is worse (§8). Keeping the
task in the ref note and teaching each surface a "virtual residence" adds special cases.
Embedding the ref task in the project note leaves residence unchanged, so the `^` picker
still misses it. Dropping the task in favor of frontmatter status loses Pomodoro links and
dependencies.

---

## 3. Where the researchers disagreed, and how I resolved it

| Topic | Positions | Resolution | Deciding evidence |
| --- | --- | --- | --- |
| Section | `## Tasks`: cdx, cld, mus, gem, and your request. `## References` with no archive: grk, following the 10-08 `^better-refs` bullet. | **`## Tasks`, archive normally** (J6) | A References section is a new special case. About 6 refs/day of closed lines would never leave `sase.md`. Today's request explicitly expects `done/` moves. |
| Meaning of `parent` | Derived from residence: cld (cdx is close). Hub chain that walks up to an area: grk. Set directly: mus, gem. | **Derived from residence** (J2) | Hubs carry almost no information: 290 of 346 modern refs say `obsidian_ref`. Residence-derived parents survive Ctrl+Shift+M with no extra writer. |
| Identity | Immutable `ref_id` plus a `[ref::]` field: cdx. `#ref` plus a link to the ref note: cld. `ref_task:` frontmatter pointer: mus. `^ref-<id>`: grk. Two-pass parent/done lookup by block ID: gem. | **`#ref` plus a path-qualified ref-note link** (J5) | Block IDs get renamed on archive collision (`collect_done/plan.rs` `moved_block_id_rename_count`). gem's lookup also fails after a manual move. bob never renames ref notes, and Obsidian rewrites links on rename. cdx's ID buys robustness against shell renames at the cost of a 32-hex field on every line; keep it as the reopen trigger (§8). |
| Block ID shape | Readable slug: cld, gem, grk. Random hex: cdx, mus. | **`^ref-<hyphenated-stem-slug>`**, unique against the destination note, its `done_tasks` file, and the batch | `🍅 [[sase#^ref-harness-engineering]]` is readable. grk's `^ref-harness_engineering` is **invalid**: block IDs allow only `[A-Za-z0-9-]` (`collect_done/transform.rs:225`). |
| REFERENCES tier | Keep it all, re-keyed to the tag: cdx, cld, grk. Retire it: mus, gem. | **Split: Ready refs stay in REFERENCES; lane refs become ordinary** (J4) | This is my own position (§4.9). |
| Ready-cap exclusion | Exclude `#ref`: grk. Count refs: everyone else. | **Count refs** | `decisions:note-ready-cap-counts-the-lane` counts by residence. Excluding refs would need a new decision and recreate the exception. |
| Unattended default parent | Inbox: cld, gem. `needs_parent` and leave it in Keep: cdx. Refuse: grk. Assign later with `adopt`: mus. | **Inbox area note** (J3) | Inboxes are areas, and inbox triage already exists. `gkeep pull` is always manual, so the TTY prompt covers the interactive case. |
| Carrying a parent in capture | `URL @route` becomes a ref: cld. A separate flag: cdx (`-P/--ref-parent`), grk (`--parent`). | **`URL @route`** (J11) | Only one URL-only task exists in the vault, and excluded hosts stay tasks. The Mac picker can insert ` @sase` into the draft, which keeps the thin-client rule. |
| Aliases | Native `aliases`: cld. `project_name_aliases`: everyone else. | **`project_name_aliases`** | The vault's native `aliases` are display titles ("Blocked Tasks", "Dashboard References"). Mixing routing names into Obsidian's suggester is how a wrong match happens. |
| SASE | Env var: cdx, cld. `{project}` placeholder: grk, gem. Unknown: mus. | **Env var** (J10) | `runner.py:160-171` uses `shell=True`. The project is already serialized per run. |
| CLI flag | Keep `-P`: cdx, cld, grk, mus. Reallocate `-p`: gem. | **Keep `-P`** (J1) | `cli_rules` forbids hard renames. |
| Ref note body | Managed embed: cld. Plain "Reading task" link: cdx. `ref_task:` frontmatter: mus. Nothing: grk, gem. | **Managed embed** | It shows the live task where the tracker used to sit. Existing link repair moves it along with the task. It is a view, never identity. |
| Annotation follow-ups | Default to the parent: cdx, cld. Stay in the ref note: grk. | **Parent** (J8) | Uniform residence. Their `[[ref/…#^h-…\|🔖]]` back-link keeps the source link. |
| Icon | Bookmark in teal (cld), indigo (grk), or violet (mus). Book-open: cdx, gem (gem as a CSS-only purple pill). | **Book-open shape in the teal `#task` identity slot** (§4.10) | `🔖` already means "jump to this highlight" on annotation follow-ups, which will now sit in the same `## Tasks` lists. A CSS-only pill bypasses the task-tag-marks system: no reveal-on-edit, toggle, or vectors. |
| Census | 27: cdx, cld, grk. **10: gem.** | **27** | Confirmed live. gem counted something else. |

Other factual corrections: mus guessed that the Mac app filters refs (it does not) and
could not verify the sase runner (verified above). gem's "Path A" would also remove the
never-decide rule that protects reading items from decay.

---

## 4. Recommended design

### 4.1 Mental model and invariants

> **A reference is a note in `ref/`. Reading it is one ordinary task, and that task lives
> with the work it serves. Wherever the task lives is the reference's parent.**

| # | Invariant |
| --- | --- |
| R1 | An open ref task lives in a root area, project, or inbox note, normally under `## Tasks`. A closed one may live in `done/`. |
| R2 | A ref note has at most one live ref task. More than one open is a diagnostic, never a guess. |
| R3 | A migrated or new ref note contains no task lines. Its body shows its task through a managed embed. |
| R4 | Frontmatter `parent` equals the task's residence. A `done/X_done.md` residence maps to that file's `parent:`; the done files already carry `parent: "[[sase]]"` and so on. |
| R5 | The marker ↔ frontmatter ↔ checkbox status policy keeps today's rules, including the `[?]` overlay and explicit `--write-pdfs`. Only where the checkbox lives changes. |
| R6 | Ref tasks carry no `#hide`. They count in lanes, caps, Today, pickers, project lifecycle, and archiving like any task. |
| R7 | The one review exception: due **Ready** `#ref` tasks walk in REFERENCES on `reference_interval`, never NEW, and never decide. |
| R8 | bob-cli is the only authority for grammar and parent resolution. Bob Mac Capture renders what `bob` returns. |

### 4.2 The ref task line

```markdown
- [ ] #task #ref [[ref/papers/harness_engineering|Harness Engineering: Anatomy, Architecture, and Evolution of Agent Harnesses]] [created:: 2026-10-09] ^ref-harness-engineering
```

- **The link targets the ref note, not the PDF.** The ref note is the hub: title, source,
  highlights, audio, and PDF link. The link is always **path-qualified** (`ref/<type>/…`)
  because stems collide. Its alias is the title with `[ ] | # ^` and backticks removed.
- **No verb.** The book glyph reads as "read", and pickers have only so much width. Your
  hand-written wrappers said "Read [[…]]!"; the glyph replaces that word.
- **Block ID** is `ref-` plus a slug of the note stem: lowercase, `_` → `-`, repeated
  hyphens collapsed, truncated at a word boundary to 40 characters or fewer. It must be
  unique against the destination note, that note's `done_tasks` file (so a later archive
  never renames it), and IDs reserved earlier in the same batch. On a collision, append
  `-2`, `-3`, and so on: the papers ref above becomes `ref-harness-engineering` and a
  later blogs ref becomes `ref-harness-engineering-2`. You can rename the ID freely,
  because identity does not depend on it.
- **`[created::]`** comes from the ref note's `created`. Creation never writes `[fresh::]`
  (nothing auto-confirms).
- **`#task #ref` stays in the stored text**, so Dataview, Tasks queries, `bob query`, grep,
  and plugin-free reading keep working. The icon is display only (§4.10).

### 4.3 The ref note after the move

```markdown
---
parent: "[[sase]]"     # projection of the task's residence (R4)
type: "[[ref]]"
status: next           # still the synced reading status
finished: 2026-10-12   # projection, stamped when the task closes (for refs.base sorting)
…
---
# Harness Engineering: Anatomy, Architecture, and Evolution of Agent Harnesses

![[sase#^ref-harness-engineering]]

## Highlights
…
```

The embed sits where the tracker used to, so opening the ref note still shows the live
checkbox, glyph, and lane tint. Ctrl+Shift+M and `bob task archive` already rewrite
`[[note#^id]]` links vault-wide, so the embed follows moves and archiving without new
code. Scan heals it after a hand edit. It is never identity, and since it does not sit
under a Pomodoro or a task, it is neither a Task Link nor a dependency edge. `region.rs`
excludes it from the note's own content, as it does the old tracker, and the audio embed
anchors after it.

### 4.4 Finding a ref's task (the locator)

Build one index per command, not per PDF.

1. Scan vault Markdown **including `done/`**. Use the exclusions `bob task reconcile`
   already uses (hidden, `_generated`, `_templates`, `_conflicts`), and skip fenced code
   and embed lines.
2. A candidate is a real task line carrying the whole-token `#ref` whose **first wikilink
   resolves**, through the existing note index, to a note under the configured ref
   directory. A plain link without `#ref` never counts, so follow-ups and prose
   mentioning a ref are safe. Legacy in-note trackers are read through the old rule.
3. Selection:
   1. the unique open candidate outside `done/` is the live task;
   2. otherwise the newest closed candidate, preferring one outside `done/`, sets the
      terminal state;
   3. otherwise the v1 in-note `^ref` (frozen closed refs, J7);
   4. otherwise frontmatter `status`, today's fallback.

Expose the result on `bob ref list/show/find` rows as an additive optional `task`
object: `{path, block_id, link, mark, archived}`. The Mac Refs panel joins Today on
`(task.path, task.block_id)`. `ref list -P` filters on the derived parent, so it is live
and never lags behind scan.

| Diagnostic (`bob ref doctor`, row `diagnostics[]`) | Meaning | Write behavior |
| --- | --- | --- |
| `multiple_open_ref_tasks` | Several open tasks claim one ref (a copy-paste, for example) | Status falls back to frontmatter; lifecycle and parent writes are refused |
| `open_ref_task_in_done` | Someone reopened a line inside `done/` | Report only; never write into `done/` |
| `open_ref_without_task` | Open status, but no task anywhere | **Never recreate it automatically.** Show a repair command. |
| `orphan_ref_task` | A `#ref` task whose link resolves to no ref note, for example after a rename outside Obsidian | Report it. `doctor --fix` re-points it only when exactly one ref note has that stem. |
| `ref_task_outside_area` | An open task in a non-area, non-project file | Report it and suggest Ctrl+Shift+M |
| `parent_mismatch` | Frontmatter or marker `parent` disagrees with residence | Residence wins. The projection catches up on the next scan, and a lone marker edit is never treated as a move request. |
| `open_v1_tracker` | An open in-note `^ref` remains | Suggest `bob ref migrate-tasks` |

### 4.5 Status sync across files

The policy in `highlights-ref-sync.md` stays. Only the write sites move.

| Event | Today | After |
| --- | --- | --- |
| New ref (scan) | Writes the tracker into the ref note | Inserts the line into the parent's `## Tasks` through **capture's insertion path** (the same bytes `bob capture @sase` writes), then writes the ref note with the embed. `bob task reconcile` groups it later. |
| You change the mark | Scan reads the in-note line | The same signal, read through the locator |
| Marker or frontmatter changes | Rewrites the in-note checkbox when the dirty guard allows a checkbox-only diff | **A one-character edit on the located line**, verified against that line's bytes at plan time. The guard changes from "file is clean" to "this line is unchanged": a Git-dirty `sase.md` is normal. |
| Task closes | `[completion::]` / `[cancelled::]` before `^ref` | Same, on the located line. Also projects `finished` onto the ref note. Dates survive moves and reopening. |
| Task archived to `done/` | Never happened | Nothing to do: the locator finds it. **Scan never writes into `done/`.** |
| A reopen signal for an archived ref (marker set back to `ready`/`wip`) | n/a | Append a **fresh open line** in the archived file's parent, reusing the block ID if it is free and otherwise suffixing `-2`. Archived history and old Pomodoro links stay truthful. If that parent has closed, file it under `mac_inbox` with a `⚠️ parent <x> is closed — refile me` child. |
| Parent | Marker → frontmatter | Residence → frontmatter, and → marker only with `--write-pdfs`. The marker's `parent` is just the birth hint for the first scan. |

**Concurrency.** Scan now writes popular shared notes that capture, plugins, and vault
sync also write.

- Build **one planned change per destination file** per run, generalizing the existing
  annotation routed-group finalizer. Two refs born into `sase.md` in the same scan must
  not lose each other's append.
- Use line-level preimage checks, and take the vault-maintenance lock where writers
  share it.
- Keep a small journal for multi-file applies, so a crash between writing the parent and
  writing the ref note resumes instead of appending a second task.
- Write the parent note first. A failure afterwards leaves an idempotent state that the
  next scan completes.

`bob ref scan`/`sync` stay the only writers of ref-note frontmatter. `bob task reconcile`
does not learn ref semantics.

### 4.6 Parent resolution (one resolver)

`resolve_parent(name)` serves `bob ref create -P`, ingest, the Keep `-P` and `@route`,
`bob ref list -P`, the migration, and (optionally) capture `@route`.

- **Candidates:** the existing capture-target set: root area notes, **non-terminal**
  project notes, and inboxes (`capture_targets.rs`). Topic hubs such as `obsidian_ref`
  and `sase_ref` are not candidates.
- **Order:** an explicit vault-relative path, then an exact stem match, then a
  `project_name_aliases` match. Matching is case-insensitive and trims whitespace. It
  never fuzzy-matches when mutating, and never treats `-` and `_` as the same character.
- **Ambiguity** (two notes claim one name) is an error that names both. **Malformed or
  duplicate aliases** show up in `bob projects doctor`.
- **Output:** the canonical stem (`bob`, never `bob-cli`) for markers and links.
- **Errors** show near misses and the fix:

  ```text
  bob ref create: error: no area or project named 'bob-cli'
  hint: did you mean bob (project · bob.md)?
  hint: to accept this name, add `project_name_aliases: ["bob-cli"]` to bob.md
  ```

- `bob capture-targets` JSON gains an additive `project_name_aliases: []` per target, so
  the Mac app's cached Destination completion can match `bob-cli`.

```yaml
# bob.md (vault; added through the normal vault workflow)
project_name_aliases: ["bob-cli"]
```

### 4.7 Entry points

**`bob ref create TARGET -P PARENT`.** `-P/--parent` is required, has no default, and is
resolved before pandoc, the browser, or any write. The dry run prints
`parent: bob (project · bob.md, via alias bob-cli)`. Update the help text from "marker
parent" to "area or project note that owns the reading task".

**Typed ingest, ref jobs, and Keep.**

- `IngestRequest` gains `parent`, and `INGEST_PARENT` is deleted.
- The ref job JSON gains a resolved `parent`, persisted before submit reports success.
  Workers never prompt.
- A failed clip falls back to the plain task `URL @<parent>` would have written, in the
  parent note, with the ⚠️ child and a retry command that includes `-P <parent>`.
- Jobs written by an older `bob` (no `parent` field) fall back to the source's inbox.

**`bob capture` grammar (J11).**

- A bare admitted URL plus **exactly one `@route` and nothing else** becomes a ref item
  whose parent is that route.
- `@@route` applies to every bare-URL item in the draft.
- With no route, the ref item gets the parent a task would get: `mac_inbox`.
- Anything more (an extra word, a schedule, a child line) or `-R/--no-ref` still keeps
  it a task. Excluded hosts stay tasks.
- `capture --dry-run` gains
  `ref.parent: {route, label, kind, source: "explicit"|"default"}`, and `capture-parse`
  gains an additive `ref_parent` soft need.
- `docs/capture.md`'s "anything more keeps it a task" sentence drops `@route` from its
  list.

**Bob Mac Capture.** This is presentation only; Swift gains no grammar.

- When the draft is a bare URL with no route, the existing Destination completion opens
  on its own with the header **File under**. It uses the cached `capture-targets`,
  filtered to areas, projects, and inboxes, with the last-used parent ranked first.
- Enter inserts ` @sase`, visibly, in the draft. Esc keeps the default.
- The preview line reads `📖 queue example.com/essay → sase` or
  `📖 queue example.com/essay → mac_inbox · file it later`.
- **Library dedupe runs before the picker.** If the URL is already captured, the preview
  shows its existing owner and no picker opens. Attaching narration never asks for a
  parent.
- After submit, the confirmation distinguishes `queued for import → sase` from the later
  `reading task created in sase`.

**`bob gkeep pull`.** Precedence per URL item:

1. a trailing `@route` in the Keep note (the item still counts as URL-only);
2. `-P/--parent ROUTE` for the batch;
3. on a TTY, **one batch prompt before clipping**: a table of new URLs, a single parent
   for all of them, per-item overrides, and Enter to accept `gkeep_inbox`;
4. otherwise `gkeep_inbox`.

The Keep journal stores the chosen parent, so a crash and re-pull never re-asks or
duplicates. `gkeep list` shows the planned parent next to its `🔗 ref` hint.

**SASE research hook (J10).**

- In `runner.py` `_execute_run`, build the child environment as `os.environ.copy()` plus
  `SASE_FILE_HOOK_PROJECT=run.get("project")`. Skip the variable when the project is
  missing or `"unknown"`, so `.get` keeps old batches runnable. Optional siblings:
  `SASE_FILE_HOOK_REL_PATH`, `…_REPO_KIND`, `…_AGENT`. Document them and add a dispatch
  test, including a project name containing shell punctuation that must reach the command
  as a single argument.
- Config (chezmoi source of `~/.config/sase/sase.yml`):

  ```yaml
  file_hooks:
    - use: sase-research-artifacts@research-highlights
      command: bob ref create --include-id -P "$SASE_FILE_HOOK_PROJECT"
  ```

- `bob-cli` resolves to `bob.md` through the alias, and `sase` resolves to `sase.md` by
  stem. An unknown project fails through the existing `❌ research-highlights failed`
  notification. It never falls back to `obsidian_ref`.
- Keep the plugin's swarm-draft and researcher filters, so five drafts never create five
  reading tasks. Don't use `sase project current`: it returns the most recently used
  project, not the one that produced the file.

### 4.8 The special-case ledger

| Special case | Fate |
| --- | --- |
| `#hide` on generated ref lines | **Remove** from the writer and in the migration. Honor a hand-written `#hide` like on any task. |
| The glossary's residence exception "a reference note's own reference task" | **Remove** (R1) |
| `DEFAULT_PARENT` and `INGEST_PARENT` = `obsidian_ref` | **Remove**; parents are required and resolved |
| "`URL @route` stays a task" | **Change**: it becomes a ref under that route |
| `parse_pdf_task_line` and `find_trackers` (one exact `^ref` per note, PDF link) | **Replace** with the locator; keep them read-only for v1 notes |
| The dirty guard's in-note checkbox allowance | **Replace** with a line-level preimage guard on the located line |
| Annotation follow-ups default into the ref note's `## Tasks` | **Change**: default to the parent (J8) |
| Audio embed anchored after `^ref` | **Change**: anchor after the managed embed |
| `git log -G\^ref` date backfill | **v1 only**; v2 reads `[created::]` and the completion/cancel fields, including from `done/` |
| Freshness `TrackerKind::Ref` from the exact block ID (Rust and JS) | **Re-key** to a whole-token `#ref` on a real task, the way PRE/POST key on `#gtd` plus `#pre`/`#post` |
| `#hide` bypass for ref trackers, and "hidden references still count" in the status bar | **Remove** (dead code) |
| Lane `^ref` rows walking REFERENCES on the reference cadence | **Remove**: lane refs walk PENDING/NEXT daily (J4) |
| Ready refs walking REFERENCES (never NEW), never deciding or counting keeps | **Keep**, re-keyed |
| "`#^ref` embeds are not dependency edges" | **Keep**; generalize to "an embed of a `#ref` task is content" |
| `^prj` exemptions (move, cap, reroll) | **Keep**; do not extend them to refs |
| Per-note Ready cap, Next/Pending caps | **Count refs** |
| `bob task archive` | **No exemption** |
| Mac Refs panel Today join on note path | **Change** to `(task.path, task.block_id)`. The Swift plan decoder must start decoding `block_id`. |
| Mac Refs watcher on `ref/` and `lib/` only | **Change**: also refresh when root notes change |
| Mac `^` picker | **No change needed**. Add an additive `task_kind: "ref"` to `capture-complete` candidates so the app can draw the book symbol without parsing tags. |
| PDF marker as the authority for `parent` | **Change**: residence is the authority; the marker is a projection |

### 4.9 Review cadence: the split (J4)

This is my own call. It sits between the "keep all of REFERENCES" camp (cdx, cld, grk)
and the "retire it" camp (mus, gem).

- **Ready refs** (the reading backlog) keep REFERENCES. They follow `reference_interval: 7`,
  walk "never-confirmed first", never enter NEW, and never decide, so no decay ladder
  applies. A backlog of reading is a weekly "still want this?" question. This is the
  cadence your config names.
- **Next and Pending refs** become ordinary lane rows. They walk PENDING or NEXT on
  `pending_interval` / `next_interval`, obey `false`, and answer with the same Alt+F,
  Alt+N, and Ctrl+Enter gestures. A ref in Next is a commitment like any other Next
  task, and `decisions:review-walk-is-tiered` says lanes come due daily. A weekly-reviewed
  row sitting in the daily lane is the kind of invisible exception this redesign exists
  to remove.
- **The cost is bounded by the caps.** Daily lane review can never exceed Next plus
  Pending caps (25 rows) whatever their kind. After the triage in §6.3, the increase is a
  handful of rows per day.
- **One known wrinkle.** Unhidden Ready refs now appear in dash *buckets* (NEW, ROTTEN)
  while walking REFERENCES, because the walk stays out of buckets by design. Accept this
  in v1. If the ROTTEN chip feels wrong for reading items, the follow-up is a decision on
  whether reading items join approved decay, not a return of `#hide`.
- **Implementation.** Rust and JS change together under the walk vectors: lane `#ref`
  rows walk their lane tier, and Ready `#ref` rows walk REFERENCES. Bump the freshness
  JSON schema (the `tracker` source becomes the tag). Record this as a new decision that
  partly supersedes the ref clauses of `docs/freshness.md` "Tracking review".

If you'd rather not change review behavior in the first release, the fallback is cdx's:
keep REFERENCES for lane refs too, as a later one-branch change. I recommend shipping the
split, because the migration triage already makes you face the lanes.

### 4.10 Visual design

- **One identity slot.** `docs/task-tag-marks.md` already replaces `#task` with a teal
  hash glyph (⌗), whose ink means "tracked task" and never encodes state. When an exact
  `#task` is immediately followed by an exact `#ref`, the Live Preview widget renders the
  **whole pair as one open-book glyph** in the same slot and the same teal ink. The shape
  says what kind of task it is; the ink still says "tracked task". Two glyphs per line
  would undo the noise reduction task-tag-marks exists for.

  ```text
  before: - [*] #task #ref [[lib/papers/harness_engineering.pdf]] #hide        (in ref/…)
  after:  - [*] 📖 Harness Engineering: Anatomy, Architecture, and Evolution…   + Oct 9   (in sase.md)
          - [ ] ⌗  Add support for new %hold directive!                       + Aug 21
                (📖 ≈ a thin teal open-book outline; ⌗ ≈ the existing teal hash)
  ```

- **Why a book and not a bookmark.** `🔖` already means "jump to this highlight"
  (`[[ref/x#^h-…|🔖]]`) on Highlights follow-up tasks, which will now sit in the same
  `## Tasks` lists as ref tasks (J8). One symbol, one meaning. Optionally rename the
  `refs.base` view "🔖 Reading Queue" to "📖 Reading Queue" so the dashboard uses the same
  word.
- **Glyph spec.** A 16×16 stroked open-book mask in the hash's stroke language
  (`stroke-width 1.8`, round caps and joins), defined once as `--bob-ref-task-glyph`
  beside `--bob-task-tag-glyph`.
  - Closed tasks rest at the same 40% mix toward `--text-faint`.
  - The cursor or a click reveals both raw tags.
  - The session toggle, keyboard access, and PDF export behave as for `#task`.
  - The tooltip reads `#task #ref · reference reading task`.
  - The accessible label is "Reference reading task"; hue never carries meaning alone.
  - Conformance vectors sit next to the existing task-tag-mark vectors.
  - A standalone `#ref` in prose, code, headings, or a non-task line never renders the
    glyph.
- **Reading view and Tasks results** use the same post-processor. Where CSS already
  hides `#task`, a rule draws the book on the `#ref` tag.
- **Elsewhere.** Mac pickers and the Refs panel use the SF Symbol `book` with the
  ordinary lane tint and a parent caption (`sase · papers`). CLI human output uses `📖`.
  Pickers drop `#ref` from the display text, as they already drop `#task`.
- **In the ref note**, the embed shows the live line. `bob ref show` prints
  `Reading task · sase · Next → [[sase#^ref-harness-engineering]]`, or
  `Read · 2026-10-12 · sase (archived)`.

---

## 5. Invariants you rely on: what changes

| You rely on… | After the redesign | Mitigation |
| --- | --- | --- |
| Reading never consumes Next/Pending slots | **It does.** Migrating as-is: Next 13 → 21/15, Pending 9 → 17/10. | Triage before migrating (§6.3). Caps warn and never refuse. |
| Reading never crowds a note's Ready cap | Research refs (about 6/day) land in `sase.md` and `bob.md` and count against the cap of 5 | This is honest pressure. Read, release, Ctrl+Shift+M into sub-projects, or set `ready_cap:` on the note. |
| Weekly ref review, never NEW | **Unchanged for Ready refs**; lane refs now get daily review (J4) | — |
| `^` picker excludes reading | It shows `[*]`/`[/]` refs with the book symbol | This is what you asked for |
| Ref status visible in `refs.base` | Same scan latency. CLI and the Refs panel derive status live from the task. | — |
| Closed ref tasks stay in ref notes | v2 refs archive with their parent once it has 10 or more closed tasks | Done/-aware locator plus the `finished` projection |
| `[[x#^ref]]` links | Rewritten for the 27 migrated refs (17 links). Links to closed v1 refs untouched. | — |
| A project with only reading left looks "empty" to `bob projects sync` | It now has open work, so `^prj` stays hidden | This is correct: unread prerequisites are open work |
| `bob ref list -P obsidian_ref` | Values become area and project names | Release note. Grep scripts for `obsidian_ref`. |
| Scan never clobbers your edits | Preserved, now per line instead of per file | Line-level preimages and the destination journal |
| PDFs written only on `--write-pdfs` | Unchanged | — |

---

## 6. Migration

### 6.1 Scope and command

- **In scope:** the 27 refs with an open in-note `^ref` (J7). Regenerate the census
  against the live vault right before running.
- **Command:** `bob ref migrate-tasks [-f human|json] [-m|--map FILE] [-w|--write]`, modeled
  on `bob ref migrate-zorg`: a dry run by default, and a single reversible commit with `-w`.
  The dry run prints the plan and can emit the parent map as an editable TSV.
  `-m/--map` supplies the parents. The run **refuses** while any ref lacks a resolvable,
  confirmed parent; it never guesses from titles.

### 6.2 Steps

1. **Lock and pre-sync.** Take the vault lock, run `vault-sync`, and re-plan from disk.
2. **Per ref:**
   1. Render the v2 line from the v1 line. Keep the mark, `[fresh::]`, `[id::]`,
      `[dependsOn::]`, close fields, priority and schedule, and **all child lines**
      (including Depends-On lines and work logs). Drop `#hide` and the PDF link, add
      `[created::]`, the path-qualified ref-note link, and `^ref-<slug>`.
   2. Insert it into the parent's `## Tasks` through the shared batch planner.
   3. Replace the v1 line with the managed embed, and set frontmatter `parent`.
3. **Rewrite identity and links as one graph edit.** Rewrite every resolved
   `[[x#^ref]]` / `[[ref/…/x#^ref]]` link to `[[parent#^ref-slug]]`, covering Task Links,
   embeds, and Depends-On lines. Today that is 17 links in 4 files. Also rewrite the
   path-derived `[id::]`/`[dependsOn::]` values. The generic move engine's ID-preserving
   rewrite is not enough here, because both path *and* ID change.
4. **Never stamp freshness and never touch Today.** This is structural, not a review
   gesture, so do not reuse the Ctrl+Shift+M path that stamps `[fresh::]`. Today membership
   survives only through the rewritten links.
5. **PDF markers.** Under the migration's explicit write authority, update each marker's
   `parent` with a preview and before-images. Report a missing PDF instead of skipping
   the task move.
6. **Verify.** Rebuild the index. Every migrated ref must resolve to exactly one live
   task with an unchanged reading status and fields, and every rewritten link must
   resolve. A second run must be a no-op. On failure, restore the before-images, but only
   where the after-images still match, so later edits are never clobbered.
7. **Commit** as `bob ref migrate-tasks: N ref tasks into M notes`, post-sync, then run
   `bob task reconcile` so `[*]`/`[/]` refs land in "Next & In Progress".
   Roll back with `git revert`.

Before migrating, the dry run should flag any **open** task that embeds or links a
migrated ref as `possible_wrapper`. None are open today, so you can merge future
duplicates by hand.

### 6.3 Suggested parents and lane triage (please confirm or override)

These are suggestions drawn from `cld`'s reading of titles, links, and wrappers. I
corrected the `harness_engineering` row, and every suggested note exists and is open. The
triage column flags refs whose wrapper you already closed. **To fit the caps, release or
close at least 6 Next and 7 Pending rows** (any kind) before migrating.

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
| `sase_launch_post_introduction` | `[/]` | `sase_blog_0` | prerequisite of `sase_blog_0`'s review task |
| `sase_launch_post_outline` | `[/]` | `sase_blog_0` | same |
| `sase_listen_plugin_commands` | `[/]` | `sase` | |
| `sase_task_bead_48h_impact_rating` | `[/]` | `sase_better_tasks` | |
| `tools_bg_split_and_tool_run_visibility` | `[/]` | `sase` | |
| `global_just_recipe_completion` | `[ ]` | `dev` | |
| `goals_inspiration_round_two_reading_list` | `[ ]` | `sase_goals` | |
| `sase_md_instruction_delivery` | `[ ]` | `sase_memory` | |
| `sase_next_direction_reading_list` | `[ ]` | `sase` | |
| `harness_engineering` (**papers**) | `[ ]` | `sase` | the completed wrapper was for the *blogs* ref, so there is no evidence this one was read |
| `agentic_software_engineering` | `[ ]` | `sase` | |
| `what_does_a_harness_buy_tokens` | `[ ]` | `sase` | |
| `introducing_omnigent_meta_harness_…` | `[ ]` | `sase` | |
| `the_dot_and_the_swarm` | `[ ]` | `sase` or `dev` | |
| `understanding_is_the_new_bottleneck` | `[ ]` | `dev` | |

---

## 7. Change list and sequencing

**bob-cli**

- The shared resolver and `project_name_aliases`; an additive `capture-targets` field;
  `projects doctor` checks.
- `ref create -P` required and resolved; the parent carried through `IngestRequest`, ref
  jobs, the Keep journal, and fallbacks.
- Capture grammar (`URL @route`, `@@route`), the `ref_parent` soft need, and the
  `ref.parent` preview. `gkeep pull -P` and its TTY batch prompt.
- The v2 scan writer (capture insertion path, batch planner per destination, journal),
  the managed embed, and embed-aware `region.rs` and `audio.rs`.
- The locator and diagnostics; `ref_library` derives status, parent, and dates from it;
  the additive `task` object on `ref list/show/find`.
- The line-level cross-file checkbox writer, close stamps, the `finished` projection, and
  reopen-from-archive.
- Annotation tasks default to the parent. `capture-complete` gains `task_kind`.
- Freshness: `#ref` tag identity, the lane split, the hide bypass removed, and a schema
  bump.
- `bob ref migrate-tasks`.
- Docs: `ref.md`, `highlights-ref-sync.md`, `capture.md`, `gkeep.md`, `freshness.md`,
  `task-tag-marks.md`, `projects.md`.

**bob-plugins** (`bob-ledger-tools`, `bob-navigation-hotkeys`; then `bob plugins sync`)

- The freshness mirror: tag identity, lane split, and the hidden-ref bypass and status-bar
  logic removed.
- The `#task #ref` → open-book identity slot, with CSS, the post-processor, and vectors.
- Strip `#ref` from picker display text. Generalize the "embed of a `#ref` task is
  content" rule.

**Bob Mac Capture** (gated by macOS CI)

- Decode `task`, `task_kind`, `ref.parent`, `ref_parent`, and `project_name_aliases`
  with `decodeIfPresent`.
- The Refs Today join on `(path, block_id)`; refresh on root-note changes.
- The File-under picker, the book symbol, and the queued vs created confirmation.

**sase**

- `SASE_FILE_HOOK_*` environment variables in `file_hooks/runner.py`, plus docs, schema
  text, and a test.

**Config, vault, memory**

- The chezmoi `sase.yml` hook command gains `-P "$SASE_FILE_HOOK_PROJECT"`.
- `bob.md` gains `project_name_aliases: ["bob-cli"]`.
- A new decision record, "Ref tasks live with their parent", covering J2, J4, J5, J6,
  and J11. Glossary updates for `reference-task`, `reference-note`, and `area-note`. A
  small superseding note for the ref clauses of the review walk. All through
  `/sase_memory_write`; I made no memory edits.

**Order.**

1. The sase environment variable, then the hook config passes `-P`. This is harmless
   while `-P` still has a default.
2. The resolver, aliases, and the `bob.md` alias.
3. The v2 model in bob-cli: locator, writer, cross-file sync, embed, additive JSON.
   Every reader still understands v1.
4. Freshness re-key and lane split, plus the glyph, in Rust and JS together.
5. Bob Mac Capture readers: locator decoding, the Today join, and the book symbol.
6. Make `-P` required, then wire capture, jobs, Keep, and the Mac File-under picker.
7. Lane triage → `bob ref migrate-tasks -w` → `bob task reconcile`.
8. The decision record and glossary updates.

Hard constraints: 1 before 6, or research imports start failing. 3 before 7, so the
migration uses the shipped writer. 5 before 7, or the Refs panel's Today section empties
for migrated refs.

---

## 8. Alternatives considered and rejected

- **Keep the task in the ref note and add a virtual residence.** Every residence-based
  surface would need a ref exception, which is more special-casing.
- **Embed the ref task in the project note** (`![[ref/x#^ref]]`). Residence is
  unchanged, so `^` still misses it and the caps still lie.
- **Drop the task and keep status only in frontmatter, with a Dataview list.** It can't
  be a Task Link, a dependency target, or a lane item, which is how you use refs.
- **A `## References` section that never archives** (grk, and the 10-08 bullet). This is
  a special case with unbounded growth: about 6 research refs a day.
- **Frontmatter `parent` as the authority, with the task following it.** Ctrl+Shift+M
  would desync it immediately, and keeping them aligned would need a second writer that
  moves tasks.
- **Requiring the parent *chain* to reach an area while keeping topic hubs as `parent`**
  (grk). It preserves a taxonomy that carries little information, and it adds a walk to
  every read.
- **Immutable `ref_id` plus a `[ref::]` field** (cdx). It is robust, but it puts 32 hex
  characters on every line and adds another machine field, against a failure (a rename
  outside Obsidian) that the diagnostics already catch. **Reopen this if
  `orphan_ref_task` shows up in practice.**
- **Block-ID-only identity or a bounded two-pass lookup** (gem, mus). It breaks on
  archive-collision renames and on manual moves.
- **Retiring REFERENCES entirely** (mus, gem). It erases a configured cadence and pushes
  reading into NEW and decay.
- **Keeping REFERENCES for lane refs** (cdx, cld, grk). It leaves a weekly-reviewed row in
  a daily lane. This is the conservative fallback.
- **Excluding refs from the Ready cap** (grk). It contradicts an accepted decision.
- **Native Obsidian `aliases`** (cld). In this vault they are display titles, not routing
  names.
- **A `{project}` placeholder in the hook** (grk, gem). It adds a template language and
  quoting hazards.
- **Repurposing `-p`** (gem). It is a hard rename of `--published`.
- **A CSS-only `#ref` badge** (gem). It bypasses the task-tag-marks system: no
  reveal-on-edit, toggle, or vectors.
- **Blocking unattended capture until a parent is chosen** (cdx, grk). Keep items would
  stall, and there is already an inbox and a triage gesture for exactly this.

---

## 9. Open questions for you

1. **Parents and triage:** confirm or override §6.3, and pick which lane rows to release
   or abandon.
2. **Review cadence (J4):** the split (my recommendation), keeping all of REFERENCES
   (conservative), or fully ordinary (Ready refs into NEW and decay)?
3. **Archive (J6):** archive normally (my recommendation), or honor the 10-08 "no done
   cleanup / References" bullet?
4. **Unattended default (J3):** inbox (my recommendation), or should the Mac app refuse
   to submit a bare URL until you pick a parent?
5. **Grammar (J11):** may `URL @sase` become a ref filed under `sase`, given that an
   extra word or `-R` still makes it a plain task?
6. **Glyph:** an open book in the teal identity ink (my recommendation), or a bookmark
   (which would then need a new symbol for highlight back-links)?

---

## 10. Recommended solution

**Move every open ref task into the `## Tasks` section of a real area, project, or inbox
note, and make that location the reference's parent.**

- **Task line:**

  ```markdown
  - [ ] #task #ref [[ref/<type>/<stem>|<Title>]] [created:: …] ^ref-<stem-slug>
  ```

  It carries no `#hide`. It renders as a single teal **open-book** glyph in the
  task-tag-mark slot, and the block ID is a readable, unique address.
- **Identity:** the `#ref` tag plus a path-qualified link to the ref note, found by one
  done/-aware locator. It never relies on the block ID, the stem, or frontmatter `id`.
- **Ref notes** hold no tasks. Each shows its task through a managed embed. `parent` is
  projected from the task's residence (through `done/` files too), and `finished` is
  stamped on close.
- **Status sync** keeps today's marker ↔ frontmatter ↔ checkbox policy. It writes
  single-line, preimage-checked checkbox edits through per-destination batch plans, never
  writes into `done/`, and answers a reopen of an archived ref with a fresh line in the
  parent.
- **Special treatment** is gone except one rule. Refs count everywhere (lanes, caps, Today,
  `^`, project lifecycle, archive), and Next/Pending refs get daily lane review. Only
  Ready refs keep the weekly REFERENCES cadence you configured, re-keyed to `#ref`.
- **Parents come from one strict resolver** (exact path, then stem, then
  `project_name_aliases`, which is honored on areas and projects). They are required on:
  - `bob ref create -P` (the existing flag, now required);
  - capture `URL @route`, with the Mac app opening **File under** by itself;
  - `bob gkeep pull` (Keep `@route`, `-P`, a TTY batch prompt);
  - the sase hook, via `SASE_FILE_HOOK_PROJECT`, with `project_name_aliases: ["bob-cli"]`
    on `bob.md`.

  Unattended paths default to the inbox the equivalent task would use.
- **Migration** covers only the 27 open refs, through a reversible
  `bob ref migrate-tasks` commit. It rewrites 17 links and their dependency IDs and
  preserves every field and child, without stamping freshness or touching Today. It runs
  after you confirm the parents and triage the lanes under their caps. Closed and
  zorg-era refs stay frozen.

---

## Sources

Code (bob-cli `b566ba4`): `src/native/highlights_ref/{create.rs:41,318-345, ingest.rs:32, note.rs, guard.rs, annotation_tasks.rs, audio.rs, region.rs, sync.rs}`,
`src/native/ref_library/{status.rs, row.rs, list.rs, mod.rs}`, `src/native/ref_jobs/worker.rs`,
`src/native/capture_active_tasks.rs:1-7,57,190`, `src/native/collect_done/{transform.rs:225, plan.rs}`,
`src/native/capture_block_ids.rs:81,607`, `src/native/url_routing/policy.rs:18-26`,
`src/native/freshness/{state.rs, scan.rs}`; docs `freshness.md` §"Tracking review",
`capture.md` §"Saving links to your reading queue", `gkeep.md:444`, `task-tag-marks.md`,
`highlights-ref-sync.md`.
sase `9c5000f2db`: `src/sase/file_hooks/runner.py:155-171`, `context.py:25-45`.
Bob Mac Capture `d5fcac0`: `Sources/RefsCore/RefsToday.swift:3-36`; no ref filter in
`Sources/CaptureCore` (only `#hide` presentation notes).
Live data (2026-10-09, read-only): `~/bob/ref/**` census, `bob.md` (`^better-refs`),
`done/sase_done.md`, `sase_agent_history.md`, `sase_blog_0.md`, daily notes 10-06..08,
`inbox.md`/`mac_inbox.md`/`gkeep_inbox.md` frontmatter, `.obsidian/app.json`,
`~/.config/bob/config.yml` (freshness and plan blocks), `bob plan -f json`,
`bob gkeep pull --help`, `sase project list`.
Memory: `decisions:{review-walk-is-tiered, task-lanes-are-sticky, note-ready-cap-counts-the-lane, mac-capture-is-a-thin-client}`,
`glossary:{area-note, inbox-file, reference-note, reference-task}`, `cli_rules`.
Prior research: `research:202610/url_capture_ref_intake_routing/url_capture_ref_intake_routing__final.md`
(capture grammar rationale, Mac scan cron).
Swarm reports: `ref_tasks_move_into_parent_notes__{cdx,cld,grk,mus,gem}.md` in this
directory.

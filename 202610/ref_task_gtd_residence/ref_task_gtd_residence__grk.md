# Ref tasks as GTD work: residence, identity, and capture

**Researcher:** grk
**Date:** 2026-10-09
**Question:** Should open reference tasks leave `ref/` notes and live on area/project notes like every other Obsidian task? If so, how should parent, block IDs, capture, sync, file hooks, and the remaining special-cases be designed?

## Verdict

Yes: open reading work belongs on a GTD home note. The current design hides that work in the library, and Bryan already treats the checkboxes as real tasks (`^better-refs` on `bob.md` is Next).

Do not implement the request as written. Four of its requirements fight the vault and the CLI:

1. Overloading frontmatter `parent` to mean "area/project only" flattens a living topic-hub graph (`obsidian_ref` 297 children, `agent_ref` 112, `work_ref` 75, …).
2. `-p|--parent` collides with the existing `-p|--published`. `-P|--parent` already exists and means the PDF marker parent, default `obsidian_ref`.
3. Putting the row in `## Tasks` sends it through `bob task archive` into `done/` and counts it against the per-note Ready cap of 5. Bryan's own `^better-refs` bullet already says the opposite: keep the row permanently on the project note, in a References place, with no done cleanup.
4. Removing every ref-task special-case would empty the REFERENCES walk, mix reading review into NEW/READY, and break Highlights sync, which still has to find one machine-managed lifecycle row per library PDF.

The recommended shape: **ordinary for action, special for hygiene.** Next/Pending reading work shows up in `^`, can be linked into a Pomodoro, and uses the same lanes as other tasks. It keeps `#ref`, a unique `^ref-<id>` block ID, a bookmark glyph, a `## References` section on the GTD home, the REFERENCES walk, and skip-archive.

## 1. How the system works today

### 1.1 Two different objects share one name

A **reference note** is `type: "[[ref]]"` under `ref/`. It is the library page: title, PDF, highlights, annotation follow-ups.

A **reference task** is the machine-managed checkbox Highlights generates:

```markdown
- [ ] #task #ref [[lib/chat/example.pdf]] #hide ^ref
```

The glossary already records the exception: every `#task` lives in exactly one area or project note, except this row, daily `^gtd`, and closed tasks `bob task archive` moved into `done/`.

The parallel object is the project tracker:

```markdown
- [ ] #task #prj Finish MVP of `bob` and bob-plugins repo (no new commits for 30d)! #hide ^prj
```

`^prj` is a lifecycle handle for the *note*. `^ref` is a lifecycle handle for the *PDF*. Bryan has been using the second as "I still need to read this," which is GTD work, not library metadata.

### 1.2 Why `^` does not show them

`bob capture-complete`'s `^` picker is `capture_active_tasks`. It lists In Progress (`[/]`) and Next (`[*]`) tasks **only from vault-root routable `*.md` files**. It does not special-case `#ref`. Ref tasks are invisible because they live under `ref/`, not because a filter strips the tag.

The dash is the other hiding layer. `dash.md` drops any task whose tags include `#hide`. Generated `^ref` and `^prj` lines both carry `#hide`, so they never appear in TODAY / PENDING / NEXT / READY.

The `!` completable picker *does* see them: it is vault-wide. Hidden rows sink inside their group. So the "filter them out" feeling is mostly residence plus `#hide`, concentrated on `^` and the dash.

### 1.3 `parent` is a topic hub, not a GTD home

`bob ref create -P|--parent` already exists. It stamps the PDF marker:

```text
- status: ready
- parent: obsidian_ref
- title: …
```

Scan copies that into note frontmatter as `parent: "[[obsidian_ref]]"`. Default is the constant `obsidian_ref`. `-p` is `--published`.

Vault census (2026-10-09, `bob query` on `ref/`):

| status    | n   |
| --------- | --- |
| legacy    | 604 |
| read      | 300 |
| abandoned | 19  |
| ready     | 10  |
| next      | 9   |
| wip       | 8   |

Open reading work is **27 notes**. Every one of those 27 currently parents to `obsidian_ref`.

Hub notes are a taxonomy, not areas/projects:

| hub             | type        | its parent     | walks to a GTD home? |
| --------------- | ----------- | -------------- | -------------------- |
| `sase_ref`      | `[[ref]]`   | `[[sase]]`     | yes (`sase.md`, project) |
| `bob_ref`       | untyped     | `[[bob]]`      | yes (`bob.md`, project) |
| `dev_ref`       | `[[ref]]`   | `[[dev]]`      | yes (area) |
| `gtd_ref`       | untyped     | `gtd`          | yes (area) |
| `obsidian_ref`  | `[[ref]]`   | `zorg_ref`     | no (`zorg_ref` → `ref` → `type`) |
| `agent_ref`     | untyped     | `ai_ref`       | via `dev_ref` → `dev` if the chain is typed |

`bob.md` already documents the intended rule for bob-related chat refs: they should parent to `bob_ref`, which itself parents to `bob`. The research-highlights file hook never passes `-P`, so new research PDFs dump on `obsidian_ref` and never reach `sase_ref` / `bob_ref`.

Requiring `parent` itself to *be* an area or project note would delete that hub graph.

### 1.4 Sync, identity, and walk all key off exact `^ref`

These readers treat the trailing block ID `ref` as a singleton per file:

- `highlights_ref::parse_pdf_task_line` — one `^ref` token in the *ref note* body, plus `#task` and a PDF wikilink.
- `ref_library::find_trackers` / `parse_tracker_line` — whitespace token `^ref` outside fences and the managed highlights region. Reading state (`queued` / `started` / `finished`) is derived from that checkbox.
- `TrackerKind::from_block_id` in both Rust freshness and `bob-ledger-tools` — exact `"ref"` or `"prj"`. That is what puts due rows in the REFERENCES walk tier, with `reference_interval`, and lets hidden `^ref` still walk (the `#hide` bypass is ref-only).
- Ready cap excludes exact `^prj` and recurring rows. It does **not** exclude `^ref`, because those rows never sit on area/project notes today.

Moving several of these rows onto one project note makes exact `^ref` illegal (Obsidian block IDs are unique per file). Identity has to move to `#ref` plus a unique block ID.

### 1.5 Capture already queues refs without a home

A capture item that is nothing but one public URL becomes `kind: "ref"`. Submit writes a ref job and returns; a worker clips through the same engine as `bob ref create`. The job file stores URL, dedupe key, and an inbox *fallback* for clip failure. It stores **no parent**.

Anything extra — including `@route` — keeps the item a **task**. So `https://example.com @sase` is not "queue this URL under sase". It is "file an inbox-style task on sase.md". Parent for a reading-queue URL cannot reuse today's `@route` grammar without a classification change.

Mac Capture is a thin client of that JSON (`decisions/mac-capture-is-a-thin-client`). The reading-queue card is `CaptureRefPresentation`. There is no parent picker on that card.

`bob gkeep pull` clips Keep URLs the same way, sequentially, with no prompt.

### 1.6 File hooks do not interpolate project name

Effective hook (user `~/.config/sase/sase.yml`):

```yaml
file_hooks:
  - use: sase-research-artifacts@research-highlights
    command: bob highlights create --include-id
```

`sase/file_hooks/runner.py` runs `{command} {quoted_abs_path}` with `shell=True`. Project name is computed for *filters* (`file_hooks/context.py` `project_name()`), never substituted into the command. The provider template in `sase-research-artifacts` deliberately omits `command` and lists it as required. `bob highlights create` is the permanent hidden alias of `bob ref create`.

### 1.7 Archive already has a pointer back from the GTD note

Area/project notes carry `done_tasks: "[[done/bob_done]]"` (and `done/sase_done`, …). `bob task archive` (threshold 10 closed `#task` rows) moves closed checkboxes there and rewrites block links. If a ref task lives in `## Tasks`, a later archive pass will move it. Sync that only looks at the live GTD file will then think the tracker is missing and may reopen or conflict.

Bryan's existing Next task on `bob.md` (`^better-refs`, created 2026-10-08) already names the product intent:

- Improved `dash_references`
- Store `^ref` tasks permanently in the project note, no done cleanup, in a References place
- `bob ref create` requires `-p|--parent`

The research prompt and that bullet disagree on Tasks-vs-References and on archive. The bullet is the better product.

## 2. Critique of the proposed plan

### 2.1 The core idea is right

Residence in `ref/` is the whole reason the work is unintuitive. Library pages should stay library pages. "I am reading this" belongs where the rest of the week's work lives, on a note `capture-targets` already offers as a route.

Doing that also makes the `^` picker start working with almost no picker-side change: the scanner already accepts any vault-root routable note.

### 2.2 Requiring area/project as the stored `parent` is the wrong lever

`parent` is already load-bearing:

- PDF marker grammar (`status` and `parent` required; marker parent is a *bare* note target, wikilinks rejected).
- `bob ref list -P|--parent` filters by that bare name.
- Mac Refs panel caption uses `parent`.
- Hub notes (`sase_ref`, `bob_ref`, `dev_ref`) are how Bryan browses a topic.

Forcing `parent: "[[sase]]"` on every sase research note would make `bob ref list -P sase_ref` go empty and would strand the hub pages.

**Adjustment (justified):** require that the parent *chain* resolve to an area or project (`type: "[[area]]"` or `type: "[[project]]"`). Accept a hub (`sase_ref`) or the GTD note (`sase`) at create time. Store what the user passed. Walk at read time to find the GTD home where the task row lives.

`obsidian_ref` fails that check (`zorg_ref` → `ref` → `type`). That is good: the default dump becomes illegal, which is the actual bug the file hook has been writing.

### 2.3 `-p|--parent` cannot be the flag

CLI rules: never hard-rename; every public long option keeps its short alias; `-p` is `--published`; `-P` is `--parent`.

**Adjustment (justified):** keep `-P|--parent`. Make it required (drop the `obsidian_ref` default). Validate that the named note exists and that its chain resolves to an area or project. Hidden alias none needed; this is a semantic tightening of an existing flag, not a rename.

Document the collision in help so a future reader does not "fix" it by stealing `-p`.

### 2.4 `## Tasks` plus archive is the ugly path

If the row sits with ordinary tasks:

- `bob task archive` will eventually move it to `done/<note>_done.md`.
- Sync must search the live file, then `done_tasks`, then maybe the old ref note. Two-file (or three-file) reads on every `bob ref list` / `scan`.
- Ten ready refs landing on `sase.md` (Ready cap 5, `^prj` already excluded) mark the note CROWDED even when GTD work is fine.
- Status-group comments (`bob:task-status-group:v1:active`) will interleave reading rows with implementation rows.

Bryan already wrote "no done cleanup" and "References". That is the beautiful version.

**Adjustment (justified):** a `## References` section on the GTD home, same grouping machinery as Tasks if grouping is wanted, never collected by `bob task archive`, excluded from the Ready cap the same way `^prj` is. Ordinary `## Tasks` stay GTD. `dash_references` / `refs.base` keep the library browse.

If a human later Ctrl+Shift+M's a ref task into Tasks, sync still has to follow `#ref` by identity, including `done/`. That is the fallback, not the happy path.

### 2.5 Do not delete every special-case

Keep these; they are invariants, not leftovers:

| Keep | Why |
| ---- | --- |
| `#ref` tag | Machine identity once `^ref` is no longer unique |
| REFERENCES walk keyed off `#ref` | Reading review is a different ritual from NEW/READY; `docs/freshness.md` and `decisions/review-walk-is-tiered` |
| `#hide` bypass *only if we keep `#hide`* | Prefer dropping `#hide` on the moved row instead |
| Highlights checkbox ↔ `status` ↔ PDF marker | Library truth |
| Annotation follow-ups in the *ref note* `## Tasks` | Source-local; already support `@route` out to a GTD note |
| Daily `^gtd` | Unrelated exception |
| Exact `^prj` on the project note | Different object; still unique per file |

Drop these:

| Drop | Why |
| ---- | --- |
| Residence in the ref note | The whole point |
| `#hide` on the reading row | It is what blanks the dash; `^prj` keeps `#hide` |
| Exact trailing `^ref` as identity | Collides on one GTD note |
| `capture_active_tasks` "missing them" | Emergent from `ref/`; goes away with vault-root residence |
| Default parent `obsidian_ref` | Illegal under the chain rule |
| Treating `#ref` as a reason to skip the `^` picker | There is no such filter today; do not add one |

`^prj` stays hidden and excluded from the cap because it is "the project is open," not "do this today." The reading row is the opposite: it *is* do-this. That is why `#hide` comes off the reading row and stays on `^prj`.

### 2.6 Prompting on every gkeep URL will hurt

`bob gkeep pull` is a batch drain. A TTY picker per Keep link will make the command unusable on a ten-URL morning.

**Adjustment (justified):**

- Mac Capture / interactive `bob capture`: required parent picker (or `-P`) before the job is written.
- `bob gkeep pull`: `--parent NOTE` for the batch, defaulting to last-used interactive parent stored in config; refuse to clip refs if neither is set. Do not prompt inside the clip loop.
- File hook: no prompt; `-P {project}` after interpolation.

### 2.7 Scope of migration is 27 notes, not the library

Do not rewrite 604 legacy notes or 300 `read` notes to have GTD parents. They have no open reading task. The request's "currently open ref notes" is the 27 `ready` / `next` / `wip` rows, all currently on `obsidian_ref`.

Closed notes may keep hub parents that do not walk. New *open* notes may not.

## 3. Alternatives considered

### A. Leave the task in the ref note, embed it on the GTD note

`![[ref/chat/foo#^ref]]` on `sase.md`. Residence stays in `ref/`. `^` still misses it (not vault-root). Sync stays one-file. Reject: it does not fix the picker, and Bryan's complaint is residence.

### B. Move the task, store GTD home in a new `home:` field, leave `parent` as hub

Clean data model. Extra field on every ref note, extra flag or a second prompt. Heavier than walking `parent`, and `bob ref list -P` would still be hub-oriented unless we add `-H/--home`.

Use walking first. Add `home:` later only if a note must parent to a hub that cannot walk (should not happen if create validates).

### C. Put the row in `## Tasks` and teach archive/sync about `done/`

Workable, ugly, and contradicts `^better-refs`. Sync complexity is real: every `bob ref list` would open the GTD note and possibly the archive. Ready cap noise is real.

### D. Derived "reading" lane instead of a GTD row

Keep the checkbox in `ref/`, surface it through `dash_references` only. Reject: Bryan already promotes these to Next and wants them in `^`.

**Recommended: E.** Task row on the resolved GTD home, `## References`, unique `^ref-<id>`, `#ref` identity, no `#hide`, parent chain must resolve, `-P` required.

## 4. Recommended design

### 4.1 Objects and links

```text
ref note (library)                     GTD home (area or project)
─────────────────                      ─────────────────────────
type: [[ref]]                          type: [[project]] or [[area]]
parent: "[[sase_ref]]"  ──walk──►      sase.md
id: harness_engineering                ## References
source_pdf: lib/papers/….pdf           - [*] #task #ref [[ref/papers/harness_engineering|Harness Engineering]] ^ref-harness_engineering
status: next  (derived from the task)
```

The ref note **loses** the generated checkbox. The GTD home **gains** it. The PDF wikilink moves off the task line (frontmatter `source_pdf` remains the Highlights handle). The task's human text is a wikilink to the *ref note*, so jumping from `sase.md` lands on notes and highlights, not a raw PDF.

Sync still owns the checkbox mark ↔ `status` ↔ PDF marker. It looks up the row by `#ref` plus either the ref-note wikilink or `source_pdf`, in this order:

1. Resolved GTD home (walk `parent`)
2. That note's `done_tasks` target (hand-moved or future policy change)
3. Legacy: the ref note body (unmigrated)

Missing tracker with an open frontmatter status is `pending` (same language as today). Missing tracker with `read`/`abandoned` is fine.

### 4.2 Parent resolution

```text
resolve_gtd_home(note):
    seen = {}
    while note:
        if note in seen: error(cycle)
        if type is area or project: return note
        note = note.parent
    error(no GTD home)
```

Create-time `-P` accepts:

- a vault-root area or project stem (`sase`, `bob`, `dev`)
- a hub that walks (`sase_ref`, `bob_ref`)
- a `project_name_aliases` match (`bob-cli` → `bob.md`)

Reject `obsidian_ref`, missing notes, cycles, and untyped vault-root notes (`nvim.md` has no `type: [[area]]` / `[[project]]`, so `nvim_ref` does not currently resolve; fix the hub parent or type the area before using it).

Terminal project notes (`status: done` / `canceled`) are valid homes for *closed* reading tasks only. Create for a new open ref refuses a terminal project and asks for a living home (the inbox is not a legal home; same as the inbox route picker never offering another inbox).

### 4.3 Block ID and tracker identity

- New rows: `^ref-<id>` where `<id>` is the ref note's `id` frontmatter (already the marker id / filename stem, unique in the library). Example: `^ref-harness_engineering`.
- TrackerKind: `#ref` as a whole-token tag on a real `#task` line, **or** a block ID with prefix `ref-`. Tags alone on a non-task line never count (same honesty rule as task-tag-marks).
- Legacy: exact `^ref` still recognized during migration.
- Obsidian uniqueness is per-file; the `ref-` prefix avoids colliding with ordinary ids like `^harness`.

Freshness, the JS mirror, `bob ref list`, and Highlights parse all switch together. The walk vector set (Q/L/R/S/B plus tracker vectors) needs new cases: `#ref` with `^ref-foo` walks REFERENCES; a coincidental description containing the word ref does not.

### 4.4 Visual: bookmark glyph for `#ref`

Follow `docs/task-tag-marks.md` exactly — display-only, cursor/click reveals the raw tag, source mode unchanged, one CSS mask.

- Glyph: Lucide-style bookmark (vertical ribbon, small cut), viewBox `0 0 16 16`, same stroke language as the `#task` hash.
- Ink: deep indigo, `color-mix` of a new `--bob-ref-tag-hue` toward `--text-normal`. Indigo is unused in the current hue table (teal is `#task`, violet is ordinary tags, blue is Ready). It reads as "library" next to the teal hash.
- Tooltip: `#ref · reading` plus "open the reference note".
- Resting closed (`[x]` / `[-]`): same 40% mix toward `--text-faint` as `#task`.

Rendered line, Live Preview:

```text
- [*] ⌗ 🔖 Harness Engineering    ▮ next
```

`#task` stays the teal hash. `#ref` becomes the bookmark. The wikilink supplies the title. No `#hide`.

`#prj` can stay a violet pill for now; it is a different object and still unique.

### 4.5 `## References` on the GTD home

Insert the section after `## Tasks` (or after the last task-status-group block), with the same blank-line hygiene `note.rs` already uses when it creates `## Tasks` under a generated `^ref`.

Optional: reuse task-status-groups (`active` / `blocked` / `done`) inside References so Next reading is not a flat dump. That is beauty, not a requirement for v1.

`bob task archive` skips lines whose tokens include `#ref`. Ready cap `counts_for_cap` becomes "not recurring, not `^prj`, not `#ref`." Crowded-notes then measure GTD Ready, not the reading stack.

Drop `#hide` on the moved row so:

- dash PENDING/NEXT/READY can show a Next reading item (Bryan asked to treat them as real tasks)
- `^` shows them once they are `[/]` or `[*]` on a vault-root note
- REFERENCES walk still collects due `#ref` rows, including Ready ones the dash may or may not emphasize

`dash_references` stays the browse chip. Improving it (the other `^better-refs` bullet) is a follow-up: group by GTD home, not only by reading state.

### 4.6 Capture UX

**Mac Capture (thin client).** After `capture-parse` / `--dry-run` classifies `kind: "ref"` and the library verdict is `not_found` / `legacy` / `unknown`, the panel keeps the existing reading-queue card and adds a required parent field. Candidates come from a new additive JSON list on the dry-run result: every capture-target area/project plus hubs that walk, ranked last-used then frecency then name. Completing the field does **not** rewrite the draft into `@route` (that would turn the item into a task). Submit sends the parent as a new capture flag, e.g. `bob capture --parent sase 'https://…'` (long option; short `-P` on `bob capture` is currently unused — verify before claiming it).

Additive JSON only (`decodeIfPresent`). Older Mac builds keep today's behavior until they learn the field; bob should refuse to queue a ref without a parent so an old app fails closed with a clear CLI error rather than dumping onto `obsidian_ref`.

**CLI `bob capture`.** Required `--parent` for ref items. `@@route` in a mixed draft does *not* silently become the ref parent.

**`bob ref create`.** Required `-P|--parent`. File hook and gkeep pass it through to ingest so the job/marker/note all agree.

**Ref job schema.** Add `parent: String` (bare note target). Clip/create stamps the marker with that parent. Scan writes the note and the GTD row.

**`bob gkeep pull`.** `--parent` for the batch. If omitted, use `highlights.default_parent` / last interactive parent from config. If still missing, skip ref clips with one summary error and keep non-URL Keep notes flowing.

Last-used parent is a small config key, not a vault write.

### 4.7 File hooks and `project_name_aliases`

SASE change (small, explicit):

- Expand `{project}` in a file-hook `command` to the user-facing project name already computed by `project_name()` (alias-resolved display name).
- Expand `{path}` as an optional alternative to the implicit trailing path, but keep appending the quoted path when `{path}` is absent so existing commands stay byte-identical.

User config becomes:

```yaml
file_hooks:
  - use: sase-research-artifacts@research-highlights
    command: bob ref create --include-id -P {project}
```

(`bob highlights create` remains a hidden alias; new config should spell `bob ref create`.)

On `~/bob/bob.md`:

```yaml
project_name_aliases: ["bob-cli"]
```

Resolver for `-P`:

1. Exact vault-root stem (`bob`, `sase`)
2. `project_name_aliases` on area/project notes
3. Obsidian `aliases` is **not** consulted (those are display titles like "Dashboard References"; mixing them with GitHub repo names is how `bob-cli` accidentally matches the wrong note)

`sase` already matches `sase.md`. Only `bob-cli` → `bob.md` needs an alias today. Document that a second project whose stem is also `bob-cli` would be an error.

Do not reuse Obsidian `aliases` for this.

### 4.8 Sync writes

`scan` / `sync` become two-file updates: the ref note (frontmatter, highlights region, no tracker) and the GTD home (one task line in `## References`).

Write order: plan both, write GTD home first (the tracker is the interaction point), then the ref note. If the GTD write fails, abort. If the ref-note write fails after a GTD success, leave the task line (idempotent on retry) and report; the next scan reconciles.

Do not rewrite the PDF marker on a tracker-only checkbox change unless `--write-pdf` / `--write-pdfs` is set (today's rule).

### 4.9 Migration

Command: `bob ref migrate-tasks --dry-run` then `--write`.

Select notes with a usable open tracker (`ready` / `next` / `wip`, including `[?]` overlay) or frontmatter in those statuses with a generated line.

For each:

1. Resolve GTD home. If `parent` is `obsidian_ref` or otherwise does not walk, **do not guess**. Print a table and require `--parent sase` (or a CSV map) for the batch, or per-id overrides. The 27 current opens are almost all SASE research chat/papers/blogs; a single `--parent sase_ref` is the honest default Bryan can confirm.
2. Choose block ID `ref-<id>`.
3. Insert the new line under `## References` on the GTD home, preserving mark, freshness stamp, close dates, Depends-On children.
4. Delete the old line (and only that line) from the ref note.
5. If parent was an illegal dump hub, rewrite `parent` to the chosen hub/home.

Leave `legacy` / `read` / `abandoned` trackers in place unless `--all-open` is later extended. Do not create GTD rows for notes with no open work.

Idempotent: a second run sees `#ref` already on the GTD home and skips.

## 5. Surfaces to change

| Area | Work |
| ---- | ---- |
| `bob-cli` `highlights_ref` | Required `-P`, chain validation, generate `^ref-<id>` without `#hide`, write GTD `## References`, parse `#ref` off-note |
| `bob-cli` `ref_library` | Tracker lookup across home + `done_tasks`; `list -P` still hub-filters on stored parent |
| `bob-cli` `ref_jobs` | Persist `parent` |
| `bob-cli` `capture` | Refuse ref queue without parent; additive JSON for picker candidates |
| `bob-cli` `gkeep` | Batch `--parent` |
| `bob-cli` `freshness` + vectors | `TrackerKind` from `#ref` / `ref-` prefix |
| `bob-cli` `note_ready` | Exclude `#ref` from the cap |
| `bob-cli` `collect_done` | Skip `#ref` |
| `bob-plugins` ledger-tools | Same tracker rule, `#ref` glyph (new fragment next to `138-task-tag-marks.js`) |
| `bob-mac-capture` | Parent field on the reading-queue card; decode additive JSON |
| `sase` file hooks | `{project}` interpolation |
| `sase-research-artifacts` docs | Example command with `-P {project}` |
| vault | `project_name_aliases` on `bob.md`; migrate 27 opens; type/fix hubs that should walk |
| glossary | Reference-task residence; parent-chain rule; `^gtd` remains the other exception |

`capture_active_tasks` itself likely needs **no** `#ref` filter. Once the row is on `sase.md` without `#hide` and is `[/]` or `[*]`, `^` shows it. That is the feature.

## 6. Risks

- **Two-file sync races** with Obsidian holding `sase.md` open. Same class of problem as `bob projects sync` and `bob task archive`; use the existing atomic-write helper.
- **Ready-cap surprise** if the `#ref` exclusion is forgotten: `sase.md` goes CROWDED overnight. Test vector next to R5 (recurring exclusion).
- **Walk inflation** if REFERENCES starts including every unstamped migrated row. Stamp migrated Next/WIP with today's `fresh` or accept they walk once. Prefer stamping with the existing `[fresh::]` when one is already on the line (the 27 already have stamps).
- **Old Mac Capture** queuing without parent: fail closed.
- **`{project}` in unrelated hook commands** if someone writes a URL. Expand only the token `{project}`, not the word project.
- **Hubs that do not walk** (`obsidian_ref`, `nvim_ref` → untyped `nvim.md`). Create fails loudly; migration table names them.

## 7. What I would not do

- I would not steal `-p` from `--published`.
- I would not destroy `*_ref` hubs.
- I would not put reading rows in `## Tasks`.
- I would not drop the REFERENCES walk.
- I would not migrate 900 closed/legacy notes.
- I would not prompt inside `gkeep pull`.
- I would not identify trackers by exact `^ref` after the move.
- I would not reuse Obsidian `aliases` for `bob-cli`.

## Recommended solution

Treat open ref tasks as GTD work that lives on the resolved area/project note, in `## References`, with a unique `^ref-<id>`, a `#ref` bookmark glyph, and no `#hide`.

Keep frontmatter `parent` as the authored hub or home, but **require that the parent chain resolve to a typed area or project**. Make existing `-P|--parent` required on `bob ref create` (do not invent `-p|--parent`). Persist that parent on ref jobs. Prompt for it in Mac Capture and `bob capture`; pass `--parent` as a batch flag on `bob gkeep pull`; interpolate `{project}` in SASE file-hook commands and set `project_name_aliases: ["bob-cli"]` on `bob.md`.

Identify trackers by the `#ref` tag (plus `ref-` block-id prefix), not by a singleton `^ref`. Keep Highlights sync, the REFERENCES walk, `dash_references`, annotation tasks on the ref note, and `^prj` as they are. Skip archive and the Ready cap for `#ref`.

Migrate only the 27 currently open reading notes, with an explicit parent (default `sase_ref` after confirmation). Leave the rest of the library's hub graph alone.

That is the design that is intuitive (work lives with work), reliable (sync has one identity, create cannot dump on `obsidian_ref`), and beautiful (bookmark glyph, a References section, hubs still browse).

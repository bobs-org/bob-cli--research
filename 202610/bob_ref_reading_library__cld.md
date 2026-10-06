# `bob highlights` → `bob ref`: a reading-library surface for agents (and Bryan)

Researcher: **cld** · 2026-10-06 · bob-cli @ `ce54258` · vault measured on athena

## 0. TL;DR

- **Do it, with adjustments.** `ref` is the right noun. The vault already says `ref`
  everywhere: `type: "[[ref]]"`, `ref/`, `^ref`, `#ref`, `refs.base`, and the
  Dashboard's REFERENCES badge. "Highlights" is just the PDF app. Make `bob ref`
  canonical. Under `cli_rules.md`, `bob highlights` must stay as a **permanent, silent,
  hidden alias**. It costs one row in the existing `ALIASES` table.
- **The read verbs are the point, and the evidence is strong.** Today's reading-list
  swarm (`memory_and_instruction_file_inspiration_reading_list__final`) ranked 30
  recommendations. **8 of the 30 (27%) were already in Bryan's ref library.** 3 were
  already **read** (`ea_graph`, `filesystem_memory`, OpenAI's *Harness engineering*). The
  other 5 were already tracked in legacy notes (4 unread, 1 collect_fleeting_notes).
  Exact URL matching would have caught only **3** of the 8. The rest differ by arXiv
  `abs`/`html`/`pdf`/`vN` form or a trailing slash.
- **Ship three read verbs:** `find` (have I seen this URL/DOI/arXiv/title?), `list`
  (library and queue, with filters and JSON), and `show` (one ref plus its annotations).
  Build them on one shared *ref index* module. `clip`'s dedupe should use the same
  identity function. Today it reads only `source_url` and misses the 283 notes that
  record `url:`, which is how *Harness engineering* ended up in the library twice.
- **Adjust the requirements (§4).** The biggest gap is coverage. The new pipeline holds
  only **22 external items** (286 of the 308 Highlights notes are agent research
  reports). Most of Bryan's real reading history is **~800 zorg-era inline records**
  outside `ref/`, plus `lit/` and `done_books.md`. The JSON must state its coverage, and
  the legacy migration needs its own Bryan-reviewed epic.
- **Fix data quality before agents read annotations.** I found and filed **bob-cli-4r**:
  in **113 of the 115** annotated ref notes, the page-1 marker shows up as a fake (often
  stale) `[!note]` annotation. Sync also never stamps finish dates: only 72 of 308
  `^ref` lines have one.
- **Agents get it through a skill.** Add a `bob_ref` skill (like `bob_query`) and a
  "check the library first" step in reading-list research prompts. Without that, the
  command exists but recommenders still won't call it.

---

## 1. What exists today (measured, not assumed)

### 1.1 Command surface and callers

`bob highlights {clip, create, doctor, marker, scan, sync}` is one runner `Leaf`
(`NativeCommand::Highlights`, `src/runner.rs`) with its own clap tree
(`src/native/highlights_ref/cli.rs`). `COMMAND_NAME = "bob highlights"`. The module is
about 13k lines across 23 files. Hidden root aliases already exist as an argv-prefix
rewrite table (`ALIASES` in `src/runner.rs`: `move-done-tasks → task archive`, and
others). Dispatch, `bob help`, and completion all share that table. A unit test requires
every alias to resolve to a runner leaf and not collide with a root name. `ref` would be
a runner leaf, so `highlights → ["ref"]` fits without new machinery.

Callers that would keep working through the alias, and should later move to the
canonical name (all in the `chezmoi` linked repo):

| Caller | Invocation |
| --- | --- |
| `home/bin/executable_maybe_bob_highlights_sync` | `"$bob_bin" highlights scan "$@"` |
| `home/bin/executable_bob_xlib_pull` (pre-scan hook) | triggers scans; uses `BOB_HIGHLIGHTS_*` env |
| `home/dot_config/sase/sase.yml` file hook | `bob highlights create --include-id` (every research report) |
| MacBook LaunchAgent / cron (per `docs/highlights-ref-sync.md`) | `bob highlights scan [--dry-run]` |

bob-plugins and bob-mac-capture don't call `bob highlights`. This would be the
command's **third** name (`highlights-ref` → `highlights` → `ref`). Prior research
(`bob_cli_command_tree_reorganization__final`, R2) notes that the earlier hard renames
broke callers. That history is exactly why the permanent-alias rule exists.

Path-keyed code that must follow the rename: `src/native/completion/kinds.rs`
(`["highlights","clip"]`, `["highlights","create"]`), `completion/tree.rs`, help
fixtures (`tests/fixtures/help/root-*.txt`), 18 `bob highlights` strings in `src/`, and
21 files across `src/`, `tests/`, `docs/`, and `README.md`.

### 1.2 What is in the library

Every Markdown file under `~/bob/ref/` is a reference note: 590 in total. That matches
the `refs.base` / Dashboard REFERENCES membership rule ("exact `ref/` prefix").

| Slice | Notes | Status (effective) | Notes |
| --- | --- | --- | --- |
| `ref/chat/` (agent research reports) | 286 | read 267 · abandoned 13 · next 5 · ready 1 | `create --include-id` from the SASE research hook |
| `ref/docs/` | 11 | read 9 · abandoned 2 | Highlights pipeline |
| `ref/blogs/` | 6 | read 4 · abandoned 2 | 2 via `clip` (`source_url`) |
| `ref/papers/` | 5 | read 5 | |
| `ref/ai/**` (legacy, zorg-migrated 2026-06-03, `sase-4b.1`) | 282 | `status: legacy`, `legacy_status`: unread 144 · collect_fleeting_notes 92 · read 25 · review_fleeting_notes 13 · review_lit_notes 4 · abandoned 4 | no `^ref` task, no PDF in `lib/` (PDFs live in `old_lib/`) |

What this means for the use case:

- **External reading in the new pipeline is tiny: 22 notes, none of them queued.**
  Today the "reading queue" (`next/wip/ready`) is 6 agent reports.
- **The topic signal is weak.** 252 of the 308 synced notes have
  `parent: [[obsidian_ref]]`, which is `create`'s default. No note uses `topics:`. For
  agent reports, the title is the only real topic signal.
- **Dates are sparse.** Only 72 of 308 `^ref` lines carry `[completion::]` or
  `[cancelled::]` (sync flips the checkbox but never stamps a date; see
  `note.rs::replace_pdf_task_checkbox_mark`). Only 24 notes have `created:`. Vault Git
  history starts 2026-05-30. Git-derived "added" and "status became read" dates over
  `ref/` cost about 0.5 s each (`git log --diff-filter=A` / `-G '^status: (read|abandoned)'`).
- **URLs live in two fields.** `url:` appears on 283 notes (275 legacy and 8 synced);
  `source_url:` appears on 2 (clip). `clip`'s dedupe
  (`clip.rs::collect_ref_note_sources`) only reads `source_url`.

### 1.3 Reading history outside `ref/` (the coverage gap)

| Source | Size | Shape |
| --- | --- | --- |
| zorg inline records (`- … ID::name ^z-…` + `* url::` / `* file::` / `* status::`) | ~800 records in 56 notes: UNREAD 227 · COLLECT_FLEETING_NOTES 211 · READ 178 · REVIEW_FLEETING_NOTES 121 · REVIEW_LIT_NOTES 31 · ABANDONED 23 · BOOK 11 | e.g. `nvim_ref.md` (108 IDs), `work_ref.md` (76), `dev_ref.md` (46), `ref.md`, `clean_arch.md`, `prj_yserve.md`. The AI subset is already mirrored into `ref/ai/` |
| 13 root `*_ref.md` hubs with `type: "[[ref]]"` | 13 | collection notes, not single references; exclude from the index |
| `lit/` literature notes | 81 | zorg-era book quotes/notes (`[@7_habits]`), no `type` |
| `books.md`, `done_books.md`, `podcasts/` | small | books and podcasts, no PDFs |
| `old_lib/` | 698 PDFs | the zorg-era library the legacy `file::` links point at |

### 1.4 Where annotations actually live (small correction to the premise)

Highlights does not write into `~/bob/ref/`. It autosaves a **sidecar** next to the PDF:
`lib/<type>/<stem>.md` or `<stem>.textbundle/text.md`. `bob highlights scan` then
renders that sidecar into the ref note's managed region (`<!-- highlights:begin/end -->`)
as callouts with stable `^h-…` block IDs, plus `## Tasks` for `#task` comments. The
**ref note's region is the right thing for agents to read**: it is cleaned up, has stable
IDs, can be cited (`[[ref/x#^h-…]]`), and is what Bryan sees. Two caveats:

- **bob-cli-4r (filed today).** When the sidecar starts with Highlights' setext title
  preamble (`Title\n=====`), that preamble appears to use up the one-shot
  "skip the first standalone note as the marker mirror" slot (`sidecar_render.rs`,
  `skipped_marker_note`). The real marker list then renders as an annotation. All 113
  affected notes have the setext preamble, and `highlights_count` is inflated by one in
  each. The leaked marker is often **stale** (`status: wip` on notes that are `read`).
  Unfixed, any annotation reader will report it as Bryan's own note.
- **Sidecar metadata is not trustworthy.** Highlights fetches DOI metadata and can get
  it wrong. The reading-list PDF's sidecar is titled *"Dynamic System Instructions and
  Tool Exposure for Efficient Agentic LLMs"* with an arXiv DOI, but it is an agent
  report. Identity must come from frontmatter, never from sidecar headers.

### 1.5 What agents can do today without new code

`bob query --format json --query 'TABLE status, ref_type, title, url, source_url FROM "ref" …'`
works. It took about 3.8 s and printed 16 ambiguous-link warnings on stderr. It does not
know that the `^ref` checkbox overrides frontmatter, doesn't map legacy statuses, doesn't
merge `url` with `source_url`, doesn't normalize URLs, and can't return parsed
annotations. It works as a stopgap but can't be the contract.

## 2. The motivating evidence: today's reading list

Ranked items from `research:202610/memory_and_instruction_file_inspiration_reading_list/…__final.md`
(read through `sase artifact read`) compared against vault URLs after normalization:

| Recommended URL (as written) | In library as | Status |
| --- | --- | --- |
| `arxiv.org/abs/2608.04278` | `ref/papers/ea_graph.md` (`arxiv.org/pdf/…`) | **read** |
| `arxiv.org/html/2607.26637v1` | `ref/papers/filesystem_memory.md` (`…/pdf/…`) | **read** |
| `openai.com/index/harness-engineering/` | `ref/blogs/harness_engineering.md` **and** `ref/ai/agent_ref/openai_harness_engineer.md` | **read** (+ a stale legacy-unread duplicate) |
| `humanlayer.dev/blog/writing-a-good-claude-md` | `ref/ai/claude_code_ref/a_good_claude_md.md` | legacy · collect_fleeting_notes |
| `arxiv.org/abs/2510.04618` | `ref/ai/agent_ref/agent_context_eng.md` (`…/pdf/…`) | legacy · unread |
| `arxiv.org/html/2602.20478v1` | `ref/ai/agent_ref/codified_context.md` (`…/pdf/…`) | legacy · unread |
| `letta.com/blog/context-repositories/` | `ref/ai/xprompt_ref/context_repos.md` (no slash) | legacy · unread |
| `martinfowler.com/…/context-engineering-coding-agents.html` | `ref/ai/agent_ref/martin_context_eng.md` | legacy · unread |

That is 8 of 30 ranked items, and 3 of them had already been read. The swarm never
looked at the vault. This is the core requirement: **an identity lookup that normalizes
URLs, run by default before any recommendation is made.** Re-recommending a queued item
isn't always wrong, but the agent should say "already in your queue since 2025-04" and
not present it as new.

## 3. Critique of the plan

**What's right**

1. **Domain noun over vendor noun.** The verbs that matter to agents (what have I read,
   what's queued, what did I annotate) are about references, not about the Highlights
   app. If Bryan ever switches PDF readers, `bob ref` still makes sense and
   `bob highlights` doesn't.
2. **One noun, one lifecycle.** `create`/`clip` → `scan` → `^ref` status → `list`/`show`
   is a single story. The membership rule is clear: "commands that create, sync, or read
   `type: [[ref]]` notes under `ref/` and the PDFs/sidecars that feed them." That
   satisfies `cli_rules.md` ("nest only under a noun with a stated membership rule").
3. **A stable CLI/JSON contract beats each agent re-deriving the schema** (§1.5). The
   house pattern is already "bob command + agent skill" (`bob_query`).

**What's risky or under-specified**

1. **Coverage is assumed, not real.** "What I have read" ≠ "what is in `ref/`" (§1.3).
   If the output doesn't say what it covers, agents will treat it as complete.
2. **Mixing plumbing with library verbs.** `marker`, `sync`, and `doctor` are pipeline
   internals. Six pipeline verbs plus three library verbs in one flat help list will be
   noisy. Split them into two help sections.
3. **Status semantics are ambiguous across eras.** The `^ref` checkbox wins over
   frontmatter on read (sync contract), but `refs.base` and the Dashboard badge read
   frontmatter. 282 notes are `legacy`, and Bryan deliberately parked their old values
   in `legacy_status` "for later review". A read surface must not quietly re-decide
   those mappings.
4. **Annotations are corrupted today** (bob-cli-4r) and **finish dates mostly don't
   exist**. "Reading annotations" and "what did I finish recently" both depend on fixes.
5. **The renamed noun picks up two open policy beads.** `bob-cli-4b` (singular vs plural
   noun policy: `projects`/`plugins` vs `task`/`pomodoro`) and `bob-cli-4a` (JSON flag
   convention: `-f/--format json` vs `-j/--json`). `bob ref` should follow whatever
   those settle, not pre-empt them.
6. **Write paths are tempting but not needed yet.** "Mark as read" already happens
   through the `^ref` checkbox or the Highlights marker, and sync does a three-way merge.
   A CLI writer would have to respect the dirty-target and `--write-pdf` rules. Queueing
   new web/PDF material already exists (`clip`).

## 4. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | **Add `find` (identity lookup) as the primary agent verb**, ahead of `list`. Inputs are URL, DOI, arXiv id, vault path/stem/`id`, or title. Normalization covers arXiv `abs/html/pdf/vN`, DOI, `www`, trailing slash, tracking params, and query order | §2: 5 of the 8 hits needed normalization; this is the recommender's real question |
| **A2** | **Output must declare coverage** (what was indexed, what wasn't), and `doctor` should count unindexed legacy records | §1.3: most historical reading lives outside `ref/` |
| **A3** | **Legacy migration of the remaining zorg reading records is a separate, Bryan-reviewed epic**, following the `sase-4b.1` precedent. It is not part of the rename | ~800 records; their status mapping is Bryan's call |
| **A4** | **Fix bob-cli-4r before `show` ships**, and filter mirror-shaped blocks defensively in the reader anyway | Otherwise 113 notes show a fake, stale "note" |
| **A5** | **Sync stamps `[completion:: date]` / `[cancelled:: date]`** on the `^ref` line when it moves status to read/abandoned and no date exists. Readers fall back to Git-derived dates | Only 72/308 have one; "what did I read lately" needs dates |
| **A6** | **`clip` dedupe and `find` share one identity function** that reads both `url` and `source_url` | `harness_engineering` is a live duplicate; also feeds `bob-cli-39` |
| **A7** | **v1 is read-only.** No `mark`, `add`, or `set-status` verbs. Agents *propose*. Bryan (or an explicitly authorized agent) queues through `clip` or Highlights | Respects the sync contract; nothing in the use case needs writes |
| **A8** | **Don't rename anything except the command path.** Keep `BOB_HIGHLIGHTS_*` env vars, the `highlights:` config block, `<!-- highlights:* -->` markers, `highlights_*` frontmatter, `pipeline_version`, and the module name | These name the Highlights integration or stored data. Renaming them means touching 308 notes and two machines' config for no user benefit |
| **A9** | **Expose `origin`** (`agent-report` for `ref_type: chat`, else `external`) and let recommenders filter on it | 286/308 synced notes are agent reports; recommenders usually want external reading, plus agent-report *titles* as an interest signal |
| **A10** | **Ship a `bob_ref` agent skill and wire it into reading-list research prompts** | The tool only helps if recommenders call it |

## 5. Options considered

| Option | Summary | Verdict |
| --- | --- | --- |
| **A. Skill + `bob query` only** | Teach agents DQL recipes over `ref/` | Stopgap only: ~3.8 s, noisy stderr, no normalization, no checkbox authority, no legacy mapping, no annotation parsing |
| **B. Keep `bob highlights`, add a separate read-only `bob ref`** | Two nouns: pipeline vs library | Clean separation, but `clip`/`create` *produce refs*, so users and agents have two places to look. Keeps the vendor name as the primary noun |
| **C. Rename to `bob ref` + add read verbs** (Bryan's plan) | One noun; `highlights` is a hidden alias | **Recommended**, with A1–A10 |
| **D. MCP server** (like Readwise Reader / Zotero MCP servers) | Tool-calling surface | Overkill here. Bob's agent pattern is CLI + skill, and every provider harness can run a CLI. Revisit only if a non-shell client needs it |

Prior art supports C's verb set. Readwise Reader's API models a reading state
(`location: new | later | archive | feed`) and treats highlights as child documents of
their source. Zotero MCP servers expose read-only `search`, item metadata, and
`search_annotations`. Both match "list/find + show-with-annotations". Neither keeps the
reading state in the vendor app's name.

## 6. Recommended solution

### 6.1 Command tree and help

```
bob ref <COMMAND>

Library:
  find    Look up URLs, DOIs, arXiv ids, or titles in the reference library
  list    List reference notes by reading state, type, and date
  show    Show one reference note's metadata and annotations

Highlights pipeline:
  clip    Capture a web URL into a Highlights intake PDF
  create  Render Markdown into a Highlights intake PDF
  doctor  Check Highlights reference sync prerequisites
  marker  Inspect the marker note for one PDF
  scan    Scan the configured Highlights library
  sync    Sync one PDF marker note into its Bob reference note
```

- Root label: *"Find, list, and read reference notes; sync Highlights PDFs into them"*.
  Move it from **Integrations** to **Tasks and projects**, next to `projects`. A ref
  note is the third lifecycle-tracked note type (`^ref` alongside `^prj`). This is a
  low-stakes choice; leaving it in Integrations is also fine.
- Keep `subcommand_required` for v1 (bare `bob ref` prints help). The CLI rules would
  allow a bare default to `list` (read-only, flag-only), and that can be added later.
- Short options reuse the existing meanings: `-s/--status`, `-t/--ref-type`,
  `-P/--parent`, `-b/--bob-dir`, `-r/--ref-dir`, `-d/--dry-run`. Output uses
  `-f/--format human|json` (the majority convention: `plan`, `freshness`,
  `task reconcile`, `gkeep list`) until `bob-cli-4a` decides otherwise.

### 6.2 Rename mechanics

1. Add `Subcommand { name: "ref", … }`. Remove the `highlights` row and add
   `Alias { from: "highlights", to: &["ref"] }`. Behavior is byte-identical for both
   spellings and there is no deprecation output (CLI rules and prior research R2).
2. Set `COMMAND_NAME = "bob ref"`. Every hint and diagnostic prints `bob ref …`. Help,
   completion `kinds.rs` paths, fixtures, README command table, and docs index follow.
   Keep `docs/highlights-ref-sync.md` and `docs/highlights-clip.md` as the pipeline
   contracts. Add `docs/ref.md` for the library verbs and JSON schemas.
3. Afterwards, move the chezmoi callers and the `sase.yml` file hook to `bob ref …` when
   convenient (not required).
4. Explicitly *not* renamed: see A8.

### 6.3 The ref index (one module, shared by `find`/`list`/`show`/`clip`)

**Membership:** `<ref-dir>/**/*.md`. This is the same rule as `refs.base` and the
Dashboard REFERENCES contract, so counts agree. Asset directories (`*.assets/`) are
skipped. Root `*_ref.md` hubs are excluded because they are collections, not references.

**Per-note resolution:**

| Field | Rule |
| --- | --- |
| `status` | `^ref` checkbox when present (`[ ]` ready · `[*]` next · `[/]` wip · `[x]` read · `[-]` abandoned), else frontmatter `status`. Deprecated `unread`/`done` normalize as sync does. If frontmatter disagrees, add `frontmatter_status` and `status_pending_sync: true` (the dashboard lags until the next scan) |
| `legacy_status` | raw, only when `status: legacy` |
| `reading_state` | coarse bucket for agents: `queued` (ready, next, legacy unread) · `reading` (wip; legacy collect_fleeting_notes, **provisional**, see Q2) · `finished` (read; legacy read/review_fleeting_notes/review_lit_notes) · `dropped` (abandoned; legacy abandoned) |
| `url` | `source_url` ?? `url` |
| `identity` | `url_key` (clip's `dedupe_key_for`, plus arXiv → `arxiv:<id>` and `doi.org/…` → `doi:<doi>`), `arxiv`, `doi`, `id`, path stem, `source_pdf` |
| `title` | frontmatter `title` ?? first H1 ?? humanized stem (never the sidecar header) |
| `added` | `created` ?? zorg block date (`source_block: ^z-YYMMDD-…`) ?? Git first-add date (`--git-dates`) |
| `finished` | `[completion::]` / `[cancelled::]` on `^ref` ?? Git date of the commit that set `status: read|abandoned` (`--git-dates`). Each date carries a `*_source` |
| `origin` | `agent-report` if `ref_type == chat`, else `external` |
| `annotation_count` | `^h-` blocks in the managed region, excluding marker-mirror-shaped blocks and the `### Removed highlights` section |

Cost: about 600 small files, which is milliseconds natively. With `--git-dates`, two
batched `git log` calls add about 1 s. Reuse `highlights_ref`'s existing parsers
(`frontmatter.rs`, `PdfTaskLine`, `managed_region`) rather than writing new ones.

### 6.4 `bob ref list`

```
bob ref list [-s STATUS[,…]] [-t TYPE]… [-T TYPE]… [-o ORIGIN] [-P PARENT]
             [-S DATE] [-a] [-g] [-f human|json] [-b DIR] [-r DIR]
```

- `-s/--status` accepts raw statuses plus the group names `queue` (ready, next, wip),
  `done` (read, abandoned), and `all`. Human default: `queue`, rendered like
  `refs.base#🔖 Reading Queue`: grouped by status, colored, newest first. JSON default:
  `all`, so agents get the whole library unless they narrow it.
- `-S/--since` filters on `finished` (or `added` when the state is queued). `-a/--annotations`
  embeds annotation arrays in JSON rows. `-g/--git-dates` turns on the Git date
  fallbacks.
- JSON envelope (versioned; stdout carries only results, as with `bob query`):

```json
{
  "schema": "bob.ref.list/1",
  "coverage": {
    "indexed": "ref/**/*.md",
    "notes": 590,
    "not_indexed": [
      "zorg inline reading records outside ref/ (see `bob ref doctor`)",
      "lit/ literature notes, done_books.md, podcasts/"
    ]
  },
  "refs": [
    {
      "path": "ref/papers/ea_graph.md",
      "link": "[[ref/papers/ea_graph]]",
      "title": "EA-Graph: Artifact-Anchored Verification Memory for Coding Agents under Upstream Drift",
      "origin": "external",
      "ref_type": "papers",
      "status": "read",
      "reading_state": "finished",
      "parent": "sase_ref",
      "url": "https://arxiv.org/pdf/2608.04278",
      "identity": { "url_key": "arxiv:2608.04278", "arxiv": "2608.04278", "doi": null },
      "added": null, "added_source": null,
      "finished": null, "finished_source": null,
      "source_pdf": "lib/papers/ea_graph.pdf",
      "annotation_count": 0,
      "has_audio": false
    }
  ]
}
```

`annotation_count` here is 0, not the note's `highlights_count: 1`. That paper's only
generated block is the leaked marker mirror from bob-cli-4r
(`> [!note] - status: ready …`), and it claims `ready` on a paper that is `read`.

### 6.5 `bob ref find`

```
bob ref find [-f human|json] [--min-title-score N] <QUERY>...
```

- For each query, it tries matches in order: identity key (URL/arXiv/DOI) → `id` /
  path stem / vault path → normalized-title match (casefolded, punctuation-stripped,
  token-set similarity). Each match reports `match_kind` and, for title matches, a
  score. Several matches per query are allowed. Example: *Harness engineering* returns
  both the read blog and the legacy-unread duplicate, and the most advanced state is
  shown first.
- The exit status is 0 whenever the lookup ran, even with no match. "Not found" is an
  answer, and agent harnesses treat non-zero exits as tool failures. Errors exit 1.
- Human output: one line per query, e.g.
  `arxiv.org/abs/2608.04278  READ  ref/papers/ea_graph.md  "EA-Graph: …"`, or
  `—  not in library`.
- `clip` calls the same identity function for its dedupe (A6). That closes the
  `url:` blind spot and makes `clip https://arxiv.org/html/…v1` see an existing
  `…/pdf/…` capture.

### 6.6 `bob ref show`

```
bob ref show [-f human|json|markdown] [--no-annotations] [--include-removed] <REF>...
```

- `REF` accepts anything `find` resolves (path, stem, `id`, URL, PDF path). If a ref
  matches more than one note, it fails and lists the candidates.
- Annotations are parsed from the ref note's managed region, **not** the sidecar:
  `{page, kind: highlight|note|image, text, comment, image, block_id, link}`, where
  `link` is a citable `[[ref/…#^h-…]]`. Removed tombstones and marker-mirror-shaped
  blocks are excluded by default (A4). Also returned: annotation-derived `## Tasks`
  lines, and Bryan's manual Markdown outside the managed region, excluding the
  generated title, `^ref` line, and audio embed. That free text is often the most
  telling signal of what he thought.
- `markdown` output is a clean, quotable digest for pasting into an agent's context.

### 6.7 Agent integration

- **`bob_ref` skill** (chezmoi, rendered for every provider like `bob_query`). It tells
  the agent: *before recommending reading, run `bob ref find` on every candidate. Drop
  `finished`/`dropped` items. Label `queued` items as "already in your queue". Use
  `bob ref list -f json -o external -s done` for taste, agent-report titles as a
  topic-interest signal, and `bob ref show` for annotations. Never write to the
  library unless asked; `bob ref clip` is the way to queue something.*
- **Reading-list research prompts** get a "dedupe against `bob ref find`" step and a
  "Coverage: N of M candidates already in library" line in the final report.
- Optional: since chat refs carry `id` = the research stem, `show` could print the
  matching `research:` artifact reference so agents can open the full report.

### 6.8 Fixes the read surface depends on

| Fix | Size | Notes |
| --- | --- | --- |
| **bob-cli-4r** marker-mirror leak | large (filed) | Also decide on vault churn: tombstone vs silently drop the ~113 `^h-` mirror blocks |
| Sync stamps finish dates (A5) | medium | Must keep the dirty-target exception ("exact generated `^ref` checkbox toggle") working; stamping happens in the same write as the checkbox change |
| Shared identity for `clip` (A6) | medium | Coordinate with `bob-cli-39` (recapture design) |

### 6.9 Legacy coverage (separate epic, needs Bryan)

Follow `sase-4b.1`. It created one note per zorg record under `ref/ai/` "for
Dataview-backed reads". Extend that to the remaining ~550 non-AI records: `nvim_ref`,
`work_ref`, `dev_ref`, `ref.md`, `old_ref`, project notes with `status::` records, and
optionally `done_books.md`/`lit/`. Bryan decides the target folder and the legacy status
mapping. Until then, `bob ref doctor` reports "N zorg reading records not indexed", and
`find` *may* add a read-only fallback over zorg `url::` lines. It is cheap, and it is
the main way the recommender's dedupe could reach pre-2026 non-AI reading.

## 7. Phased rollout

| Phase | Content | Size |
| --- | --- | --- |
| 1 | Rename (`ref` canonical, `highlights` hidden alias, `COMMAND_NAME`, help sections, completion paths, fixtures, docs index) | medium |
| 2 | Ref index module + `list` + `find` + `show` (JSON schemas, docs/ref.md, conformance fixtures from real note shapes: synced, legacy, mirror-leaked, setext sidecar) | large |
| 3 | `clip` on the shared identity function; finish-date stamping in sync; bob-cli-4r | medium–large |
| 4 | `bob_ref` skill + reading-list prompt step (chezmoi) | small |
| 5 | Legacy reading-record migration (Bryan-reviewed epic) | large |

Phases 1–2 can be a single epic. Phase 4 is where the user-visible win shows up, so
schedule it right after Phase 2.

## 8. Open questions for Bryan

1. **Noun:** `ref` (matches `type: [[ref]]`, `^ref`, `#ref`, `ref/`) or `refs` (matches
   `projects`, `plugins`, `refs.base`)? I recommend `ref`. Either way, fold the answer
   into `bob-cli-4b`.
2. **Legacy states:** does `collect_fleeting_notes` mean "reading" or "read, notes
   unprocessed"? Does `legacy unread` (144 notes from 2025) still count as "plan to
   read", or should it be `stale`?
3. **Agent-report refs:** should recommenders treat `ref/chat` items as "read material"
   (the default today; 267 are `read`) or only as an interest signal?
4. **Bare `bob ref`:** keep it as help, or default to `list` (the queue view)?
5. **Agent writes:** may a recommender ever `bob ref clip` its picks into `xlib/`
   automatically, or must it always only propose?

## 9. Evidence and sources

- Code: `src/runner.rs` (`SUBCOMMANDS`, `ALIASES`, alias tests),
  `src/native/highlights_ref/{cli,mod,clip,clip_url,sidecar,sidecar_render,note}.rs`,
  `src/native/completion/{tree,kinds}.rs`, `docs/highlights-ref-sync.md`,
  `docs/highlights-clip.md`, `docs/dashboard.md`, `docs/dataview.md`.
- Memory: `cli_rules.md`; glossary `reference-note`, `reference-task`;
  `obsidian.md`.
- Prior research (audited reads):
  `research:202610/bob_cli_command_tree_reorganization/…__final.md` (alias policy, R2);
  `research:202610/memory_and_instruction_file_inspiration_reading_list/…__final.md`
  (§2 overlap).
- Beads: **bob-cli-4r** (filed: marker-mirror leak), bob-cli-4a (JSON flags),
  bob-cli-4b (noun policy), bob-cli-39 (clip recapture/dedupe).
- Vault measurements: read-only scans of `~/bob/ref`, `~/bob/lib`, root `*_ref.md`, and
  `git -C ~/bob log` on athena, 2026-10-06. Commits `a478dd93` (`sase-4b.1` AI ref
  migration) and `5e3c04ae` (legacy status standardization).
- External: [Readwise Reader API](https://readwise.io/reader_api) ·
  [Reader API docs](https://docs.readwise.io/reader/docs/api) ·
  [Zotero MCP server](https://glama.ai/mcp/servers/54yyyu/zotero-mcp) ·
  [Zotero `search_annotations` tool](https://policylayer.com/tools/zotero/search-annotations) ·
  [Highlights for Mac Markdown export](https://www.macdrifter.com/2014/10/highlights-for-mac-turns-pdf-annotations-into-markdown.html) ·
  [Highlights on the App Store (sidecar/DOI metadata)](https://apps.apple.com/cn/app/highlights-pdf-reader-notes/id1498912833?l=en)

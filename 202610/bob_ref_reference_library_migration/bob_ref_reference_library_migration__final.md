# `bob highlights` → `bob ref`: a reference library for agents and Bryan

Consolidated report · lead researcher · 2026-10-06 · bob-cli @ `ce54258` · vault measured on athena

Merges five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this directory)
with my own verification of the facts they disagreed on. Where a number below differs from a
sibling report, it is the recount I made.

## 0. Bottom line

**Yes, do it, with adjustments.** Make `bob ref` the canonical command and keep `bob highlights` as
a permanent, silent, hidden alias. Keep all six pipeline verbs byte-identical, and add a small
**read-only** library surface on top. Four of the five researchers reached this conclusion. The
fifth (grk) argued for a separate `bob ref` beside `bob highlights`. §3.2 explains why I side
with the majority and which of grk's points I kept.

The rename is the easy part. Whether agents can trust the answers depends on four things none of
the reports call trivial:

1. **Identity matching.** A recommender's real question is "is this URL/paper already in Bryan's
   library?" The library stores URLs in two fields (`url:` on 283 notes, `source_url:` on 2) and
   in inconsistent shapes (arXiv `abs`/`pdf`/`html`/`vN`, `www`, trailing slashes, YAML lists,
   `go/` links). `bob highlights clip`'s dedupe reads only `source_url`. As a result, OpenAI's
   *Harness engineering* sits in the library twice: once as read, once as legacy-unread.
2. **Honest reading state.** Nearly half the library (282 notes) is `status: legacy`, with the real
   zorg-era state parked in `legacy_status`. A `--status read` filter that ignores this misses the
   history. Mapping it carelessly misleads agents.
3. **Honest coverage.** About 425 zorg-era reading records still live outside `ref/` (§2.4). The
   output must say what it does and doesn't cover.
4. **Clean annotations.** In 113 of the 115 annotated notes, a stale page-1 marker is rendered as
   if it were Bryan's own note (bead `bob-cli-4r`). Any annotation reader has to filter it.

**Recommended v1:** `bob ref find`, `bob ref list`, and `bob ref show`, built on one shared
read-only *ref index*, with versioned JSON and a `bob_ref` agent skill that makes "check the
library first" the default step for reading-list agents. The full recommendation is in §9.

---

## 1. Where the reports agreed, and how I resolved the disagreements

| Topic | Consensus / split | Resolution |
| --- | --- | --- |
| Is `ref` the right noun? | All 5 agree (`type: "[[ref]]"`, `ref/`, `^ref`, `#ref`, `refs.base`) | **`ref`.** Record the choice in `bob-cli-4b` (singular/plural noun policy) |
| Rename vs. separate command | cdx, cld, mus, gem: rename + hidden alias. grk: separate read-only `bob ref`, leave `highlights` alone | **Rename + alias** (§3.2) |
| v1 writes reading state? | All 5: no; v1 is read-only | **Read-only.** `^ref` checkbox + `scan`/`sync` stay the only writers |
| Rename env vars, config, markers, `highlights_*` frontmatter? | All 5: no | **No.** They name the integration and stored merge state, not the command |
| Where annotations come from | All 5: the ref note's managed region, not sidecars/PDFs | **Managed region**, filtering marker mirrors and tombstones |
| Identity lookup verb | cld/gem `find`, grk `contains`, cdx `search -u`, mus none | **`find`**, with batch input and normalized identity keys |
| Annotations: own verb or part of `show`? | cdx/mus: `annotations`. cld/gem/grk: part of `show` | **Part of `show`** in v1. A library-wide annotation search can come later |
| Legacy status mapping | gem: `collect_fleeting_notes` → ready. cdx: don't map. cld: provisional buckets. grk: pass raw value through | **Evidence-based mapping, raw value always kept** (§2.5) |
| `find` exit code on no match | gem: 1. cld/grk: 0 | **0.** "Not found" is an answer. Bob reports exit 0 on empty results, and agent harnesses treat non-zero as failure |
| Bare `bob ref` | grk: default to `list` (separate command only). cdx/cld: help in v1 | **Help in v1.** A `list` default is legal later (§3.2) |
| Help section | Vault (cdx, grk), Tasks and projects (cld), Integrations (mus), either (gem) | **Vault.** Low stakes |
| Rename `highlights_ref` module? | gem: rename to `reference/`. Others: keep | **Keep it.** Put the read model in a new sibling module |
| `bob query` as the answer? | All 5: stopgap only | Agreed; measured in §2.7 |

---

## 2. Verified facts

### 2.1 Command surface and alias mechanics

- `bob highlights {clip, create, doctor, marker, scan, sync}` is a single runner leaf
  (`NativeCommand::Highlights`, `Section::Integrations`, `src/runner.rs`). It has its own clap
  tree (`src/native/highlights_ref/cli.rs`, `subcommand_required(true)`) and
  `COMMAND_NAME = "bob highlights"` (`mod.rs:76`). The module is about 12.9k lines across 23 files.
- Root aliases are an **argv-prefix rewrite** (`rewrite_alias_args` over `ALIASES`). Dispatch, help,
  and completion share the table, and a unit test requires every alias to resolve to a leaf. Adding
  `Alias { from: "highlights", to: &["ref"] }` makes every `bob highlights …` invocation identical
  to `bob ref …` by construction.
- Rename touchpoints: the runner row, `COMMAND_NAME`, two completion paths in
  `src/native/completion/kinds.rs` (`["highlights","clip"]`, `["highlights","create"]`), help
  fixtures, and 21 files under `src/`, `tests/`, `docs/`, and `README.md` that mention
  `bob highlights`.
- **New finding:** the earlier hard rename `highlights-ref` → `highlights` was never aliased.
  `bob highlights-ref -h` still fails with `unrecognized subcommand`, which already violates
  `cli_rules.md`. The rename is a cheap moment to add `highlights-ref → ref` as well.
- External callers (from cld; they live in the `chezmoi` linked repo):
  `maybe_bob_highlights_sync` (`bob highlights scan`), the `bob_xlib_pull` pre-scan hook, the SASE
  research file hook (`bob highlights create --include-id`), and the MacBook scheduled scan. All
  keep working through the alias and can move to `bob ref` whenever convenient.

### 2.2 Where the annotations actually live (correction to the premise)

Highlights does not write to `~/bob/ref/`. It autosaves a Markdown or TextBundle **sidecar next to
the PDF** under `lib/`, and Highlights owns that file
([Highlights sidecar docs](https://highlightsapp.net/how-to/mac/sidecar-files/)). `bob highlights
scan` then imports the sidecar into the ref note's managed region
(`<!-- highlights:begin/end -->`) as callouts with `^h-…` block IDs. That rendered region is what
agents should read:

- It reaches headless hosts through vault Git sync.
- It is cleaned up and citable (`[[ref/x#^h-…]]`).
- It is what Bryan sees in Obsidian.

Two caveats:

- The region is a **snapshot** of the last import. It is not live MacBook state.
- A note-side lifecycle change that needs PDF write-back makes a writing sync refuse before
  rendering (cdx). Imported annotations can therefore lag behind.

Sidecar title/DOI metadata is not trustworthy. Highlights fetched an unrelated arXiv DOI for one
agent report (cld). Identity must come from frontmatter.

### 2.3 What is in `ref/`: two populations

All 590 Markdown files under `ref/` carry `type: "[[ref]]"`. Thirteen root `*_ref.md` hub notes
outside `ref/` share the type but are collections, not readings, so exclude them.

| Slice | Notes | Effective status | Shape |
| --- | ---: | --- | --- |
| `ref/chat/` (SASE research reports via `create --include-id`) | 286 | read 267 · abandoned 13 · next 5 · ready 1 | `^ref` task, managed region |
| `ref/docs/` · `ref/blogs/` · `ref/papers/` | 11 · 6 · 5 | read 18 · abandoned 4 | `^ref` task, managed region |
| `ref/ai/**` (zorg AI records migrated 2026-06, `sase-4b.1`) | 282 | `legacy` | no `^ref`, no `ref_type`; `url:` on 275; PDFs sit in `old_lib/`, though the notes link `lib/…` |

- `^ref` marks: 285 `[x]`, 17 `[-]`, 5 `[*]`, 1 `[ ]`, 0 `[/]`. These agree with frontmatter.
- `legacy_status`: unread 144 · collect_fleeting_notes 92 · read 25 · review_fleeting_notes 13 ·
  review_lit_notes 4 · abandoned 4.
- **Only 22 external items run through the modern pipeline, and none are queued.** The six open
  items (`next`/`ready`) are all agent reports. The Dashboard's 🔖 Reading Queue (`refs.base`,
  `status ∈ next|wip|ready`) shows those six. It hides the 144 legacy-unread articles (grk).
- Topic signal is weak. Nobody uses `topics:` or `author:`, and 252 of the 308 synced notes have
  `create`'s default `parent: [[obsidian_ref]]`. Titles are the useful signal.

### 2.4 Reading history outside `ref/` (the coverage gap)

cld found this and I recounted it. The vault has **803** zorg inline `* status::` records outside
`ref/`:

- 96 are copies under `_generated/queries/`.
- **707 are authored**, and 282 of those are already mirrored into `ref/ai/`.
- That leaves **about 425 reading records that `ref/` doesn't index**, in files such as
  `work_ref.md` (75), `nvim_ref.md` (69), `clean_arch.md` (37), `dev_ref.md` (27), `prj_yserve.md`
  (18), and `ad_tech_book.md` (17).

Across all records: UNREAD 227 · COLLECT_FLEETING_NOTES 211 · READ 178 · REVIEW_FLEETING_NOTES 121 ·
REVIEW_LIT_NOTES 31 · ABANDONED 23 · BOOK 11. `lit/` (81 literature notes), `books.md`,
`done_books.md`, and `podcasts/` hold further history with no `type`.

Many of the unmirrored records are internal `go/` work docs, which don't matter for public-reading
recommendations. Still, Bryan's pre-2026 non-AI reading (Neovim, architecture books, dev tools)
lives here. **A `ref/`-only index is not "everything Bryan has read", and the JSON must say so.**

### 2.5 What the legacy statuses meant

This is my own research, and it settles the mapping split. The zorg notes record the workflow
directly. `gtd_ideas.md` (`^z-250318-0l`, "zorg_ref_notes_v2") lists the labels **in workflow
order**: UNREAD → COLLECT_FLEETING_NOTES → REVIEW_FLEETING_NOTES → REVIEW_LIT_NOTES → READ, plus
ABANDONED and BOOK. The records in `zorg_ref.md` show what each stage held:

- `REVIEW_FLEETING_NOTES`: a FLEETING NOTES list of exported, annotated `lit_review/*.pdf` pages
  still to review. The source has been read and marked up.
- `REVIEW_LIT_NOTES`: the fleeting notes are checked off and LITERATURE NOTES are written. The
  remaining step is the review checklist ("can I link this note…").
- `COLLECT_FLEETING_NOTES`: the stage right after UNREAD, i.e. reading and annotating. Most
  records at this stage have no fleeting-notes list yet. That means "started, completion unknown",
  not "finished".

Mapping consequences:

- `review_fleeting_notes` and `review_lit_notes` are finished-reading evidence. cdx's refusal to
  map them was too cautious.
- `collect_fleeting_notes` is *started*, not *ready*. gem's mapping of it to READY is wrong.
- The `[[read]]` link on zorg records is **not** completion evidence. It appears on UNREAD records
  too (for example `org_noter` in `zorg_ref.md`), even though `read.md` claims it marks
  already-read material.

Bryan should still confirm this mapping (Q2), but it no longer has to be a guess.

### 2.6 Identity is messy

- `url:` appears on 283 notes: 275 legacy plus 8 synced notes whose markers carry `url`. 10 of
  them are **YAML lists**, and several are `go/` short links or non-HTTP strings. `source_url:`
  appears on only 2 notes (`clip`).
- `clip.rs::collect_ref_note_sources` (around line 546) skips every key except `source_url`.
  `clip_url.rs::dedupe_key_for` lowercases the host and strips `www.`, default ports, trailing
  slashes, and `utm_*`/known tracking params. It has **no arXiv or DOI normalization**.
- Live evidence: `ref/blogs/harness_engineering.md` (read, `source_url`) duplicates
  `ref/ai/agent_ref/openai_harness_engineer.md` (legacy unread, `url`). cld compared one of today's
  agent reading lists against the library. **8 of 30 recommendations were already there and 3 of
  them were already read**, but exact URL matching catches only 3 of the 8. I re-checked five of
  those matches in the vault (`ea_graph` and `filesystem_memory`, stored as `/pdf/` and read;
  `agent_context_eng`, a `/pdf/` legacy-unread; `context_repos`, with `www.` and no trailing
  slash; and the Harness duplicate). All five hold.
- `ref/chat/` already contains three reading-list research reports
  (`goals_redesign_recent_reading_list`, `memory_and_instruction_file_inspiration_reading_list`,
  `sase_paper_followup_reading_list`). The recommender use case recurs; this is not hypothetical.

### 2.7 Data quality and performance

- **`bob-cli-4r` reproduces:** the leaked-mirror pattern appears in 113 notes, and 115 notes have
  `highlights_count ≥ 1`. In `ref/papers/ea_graph.md`, the only "annotation" is
  `> [!note] - status: ready …` on a paper that is `read`. The root cause (likely) is a setext title
  preamble in the sidecar that uses up the one-shot marker-mirror skip in `sidecar_render.rs`.
- **Finish dates are sparse:** of the 302 closed `^ref` tasks, only 88 carry a date (72
  `[completion::]` and 16 `[cancelled::]`). Sync flips the checkbox from the PDF marker but never
  stamps a date. Vault Git history starts on 2026-05-30.
- **Intake is invisible to `ref/`:** `xlib/chat/highlights_listen_intake.pdf` is queued right now
  but has no ref note yet. `xlib/` is per-machine and outside vault Git sync.
- **`bob query` as a stopgap:** `TABLE status FROM "ref"` took **3.77 s**. The six-column catalogue
  in JSON produced **145 KB** and **16** ambiguous-link warnings on stderr. It doesn't know that the
  checkbox outranks frontmatter, doesn't map legacy states, doesn't merge `url`/`source_url`, can't
  normalize URLs, and can't parse annotations.
- **Native scan cost:** raw-reading the head of all 590 ref notes took about 10 ms. A native index
  should land well under 100 ms. gem's "12–15 ms" figure is plausible but unmeasured, since no
  implementation exists yet.
- **Annotation volume is small:** 361 highlights in total, median 2 and max 30 per note. The largest
  note is 8.7 KB (grk). `show` is cheap per note. A full `list` with bodies is not.

---

## 3. Critique: is this a good idea?

### 3.1 What's right

1. **The domain noun beats the vendor noun.** `clip` (web), `create` (Markdown), and chat-report
   capture have nothing to do with the Highlights app. The vault already says `ref` everywhere. If
   Bryan ever switches PDF readers, `bob ref` still makes sense.
2. **One object, one lifecycle.** The story is `clip`/`create` → `scan` → `^ref` status →
   `find`/`list`/`show`. A clear membership rule satisfies `cli_rules.md`: *commands that create,
   sync, or read reference notes under `ref/`, and the PDFs and sidecars that feed them.*
3. **The use case is real and measurable** (§2.6). A stable CLI/JSON contract plus a skill is the
   house pattern (`bob query` + `bob_query`), and it beats every agent re-deriving the schema.

### 3.2 The rename vs. separate-command dispute

grk's dissent deserves a direct answer:

| grk's argument | Assessment |
| --- | --- |
| "A byte-identical hidden alias cannot grow a default `list`." | **Doesn't hold.** The alias is an argv rewrite, so `bob highlights X` ≡ `bob ref X` by construction. The rule constrains alias ≡ canonical, not the canonical command's evolution. Only bare `bob highlights` would change, and today it just prints help. I still recommend keeping bare `bob ref` as help in v1, because it is cheap and reversible |
| "Read-only reports stay top-level." | **Misreads the rule.** That sentence reserves `bob task` for vault-wide task writers. Object nouns already mix readers and writers: `bob projects {list, sync}`, and `bob gkeep` (bare = `list`) |
| Pipeline and library are different products. | **Partly right.** Address it with two help groups (Library / Highlights pipeline), not two nouns. Two nouns for one object means two places to look, and a likely third rename later |
| Renaming doesn't index the legacy population. | **True, but orthogonal.** The new scanner gets written either way |
| Churn (cron, docs, tests). | **Moderate.** Cron and hooks keep working via the alias. Existing tests that invoke `bob highlights` become a free alias regression suite. Only output-string assertions change |

grk was right about several things, and I kept them: lookup before dump, compact JSON, an
agent-report vs. external split, the clip dedupe fix, and **not** turning `highlights_ref` into a
query engine.

### 3.3 What's risky or under-specified in the request

1. **Coverage is assumed, not real** (§2.4). Without a declared scope, agents will treat `ref/` as
   complete.
2. **Status semantics differ across eras.** The `^ref` checkbox wins in sync, `refs.base` reads
   frontmatter, and 282 notes are `legacy`. A read surface must not quietly re-decide these
   mappings. It should expose the raw signals and a derived bucket with its evidence.
3. **"Read" is a current state, not a history.** Reopening `[x]` → `[ ]` erases the only completion
   evidence. `[/]` is a sticky lane (`decisions:task-lanes-are-sticky`), not proof that Bryan is
   reading the item right now.
4. **Annotations are polluted today** (`bob-cli-4r`), and finish dates mostly don't exist (§2.7).
5. **Pipeline verbs are jargon** (`marker`, `scan`, `sync`). Six of them plus three library verbs in
   one flat help list is noisy, so split them into help groups.
6. **Write verbs are tempting but not needed.** A writer would have to honor the three-way
   marker/frontmatter/checkbox merge, the dirty-target guard, and `--write-pdf`. Queueing already
   exists (`clip`), and so does marking read (the checkbox).

---

## 4. Requirement adjustments (explicitly called out)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | **Rename means alias promotion.** `ref` is canonical. `highlights` is a permanent hidden alias with no deprecation output. **Also alias `highlights-ref → ref`** | `cli_rules.md`. The old `highlights-ref` hard rename is still broken (§2.1) |
| **A2** | **The primary agent verb is `find`, not `list`.** It takes URL, DOI, arXiv ID, path, stem, `id`, or title, several at once | §2.6: 5 of 8 real overlaps needed normalization |
| **A3** | **v1 is read-only.** No `mark`, `track`, `add`, or `set-status` | The sync contract is the most delicate code in the module. Nothing in the use case needs writes |
| **A4** | **Every JSON response declares coverage**, and `doctor` counts unindexed zorg records | §2.4: about 425 records are outside `ref/` |
| **A5** | **Status is three fields:** effective `status`, raw `legacy_status`, and a derived `reading_state` plus its evidence. No new stored status | §2.5. Agents need the bucket; Bryan's raw values must survive |
| **A6** | **Expose `origin`:** `agent-report` (`ref/chat`) vs. `external` | 286 of 308 synced notes are SASE reports. They are an interest signal, not prior reading |
| **A7** | **Annotation reads filter marker mirrors and tombstones defensively**, and the `bob-cli-4r` root fix ships in the same wave | Otherwise 113 notes show a fake, stale "note" |
| **A8** | **`clip` and `find` share one identity function** (`url` + `source_url`, arXiv/DOI keys, list-valued `url`). A legacy-only match must not become a dead end (§5.8) | Fixes the Harness duplicate without blocking the 144 legacy-unread items from entering the pipeline |
| **A9** | **Rename nothing but the command path.** Keep `BOB_HIGHLIGHTS_*`, `highlights:` config, `<!-- highlights:* -->`, `highlights_*` frontmatter, `pipeline_version`, and the module name | Integration contract and stored merge state. Renaming them buys nothing |
| **A10** | **Ship a `bob_ref` skill and a "check the library first" step in reading-list prompts** | The command only helps if recommenders actually call it |
| **A11** | **Migrating the zorg-era reading records is a separate, Bryan-reviewed epic** following `sase-4b.1`. It is not part of the rename | About 425 records whose scope (for example work `go/` docs) and mapping are Bryan's call |
| **A12** | **Sync stamps `[completion::]` / `[cancelled::]`** when it moves a `^ref` task to read or abandoned and no date exists | "What did I read lately?" needs dates. Only 88 of 302 have one |

---

## 5. Recommended design

### 5.1 Command tree and help

```text
bob ref <COMMAND>          Find, list, and read reference notes; sync Highlights PDFs into them

Library:
  find    Look up URLs, DOIs, arXiv IDs, paths, or titles in the reference library
  list    List reference notes by reading state, type, origin, and date
  show    Show reference notes with metadata, annotations, and Bryan's own notes

Highlights pipeline:
  clip    Capture a web URL into a Highlights intake PDF
  create  Render Markdown into a Highlights intake PDF
  doctor  Check Highlights reference sync prerequisites
  marker  Inspect the marker note for one PDF
  scan    Scan the configured Highlights library
  sync    Sync one PDF marker note into its Bob reference note
```

- Put it in the **Vault** section. Bare `bob ref` prints help in v1. Defaulting it to `list` later
  is allowed, since `list` is flag-only and read-only.
- Subcommands are alphabetical within each group. If clap's single subcommand heading makes groups
  awkward, use a custom help template, as root help already does.
- Every new long option gets a short alias. Keep existing meanings (`-b/--bob-dir`, `-r/--ref-dir`,
  `-s/--status`, `-t/--ref-type`, `-P/--parent`) and don't reuse those letters for other options.
  The new short letters in §5.4–5.6 are illustrative.
  Output uses `-f/--format human|json|markdown`, the majority convention (`plan`, `freshness`,
  `gkeep list`), until `bob-cli-4a` decides otherwise.

### 5.2 Rename mechanics (Phase 1)

1. Change the runner row to `name: "ref"` in Vault and add the `highlights → ["ref"]` and
   `highlights-ref → ["ref"]` aliases. Leaving `NativeCommand::Highlights` internally is fine.
   Don't mount the same leaf twice; runner tests enforce one canonical path.
2. Set `COMMAND_NAME = "bob ref"` so every hint and diagnostic prints the canonical path. Update
   completion `kinds.rs` paths, help fixtures, the README command table, and the docs index.
3. Test equivalence: for all six verbs, under a fixed clock, `bob highlights X` and `bob ref X`
   produce the same stdout, stderr, exit status, and files. Include the help/error paths and
   parent `--no-hooks`. No deprecation text anywhere.
4. Keep `docs/highlights-ref-sync.md` and `docs/highlights-clip.md` as the pipeline contracts. Add
   `docs/ref.md` for the library verbs, the JSON schemas, and the status table.

### 5.3 The ref index (one read-only module shared by `find`, `list`, `show`, and `clip`)

Put it in a new sibling module (for example `src/native/ref_library/`). Reuse lifecycle vocabulary,
`PdfTaskLine`, managed-region delimiters, and `clip_url` through narrow `pub(crate)` seams. Parse
YAML with `serde_yaml`, as Dataview does. The line-preserving Highlights frontmatter parser is the
wrong tool for list-valued and multiline fields. Never call `plan_pdf_sync`, open PDFs, run hooks,
or write anything.

**Membership:** `<ref-dir>/**/*.md`, matching `refs.base` and the Dashboard rule so the counts
agree. Skip hidden directories, `*.assets/`, and conflict copies. Report malformed YAML or trackers
as per-row diagnostics instead of dropping the row.

**Per-note fields:**

| Field | Rule |
| --- | --- |
| `path`, `link` | Vault-relative path (the unambiguous locator) plus `[[ref/…]]` |
| `title` | frontmatter `title` ?? first H1 ?? humanized stem. Never the sidecar header |
| `status` | `^ref` checkbox when there is exactly one valid tracker, else frontmatter. Normalize `unread`/`done` as sync does. When they disagree, add `frontmatter_status` and `status_pending_sync: true`. When the stored base proves independent edits on both sides, report `conflict` with both signals |
| `legacy_status` | Raw value, present only when `status: legacy` |
| `reading_state` + `reading_state_source` | See the mapping below. Always carries its evidence (for example `ref_task:[x]` or `legacy_status:review_lit_notes`) |
| `origin` | `agent-report` if under `ref/chat/` (or `ref_type: chat`), else `external` |
| `urls`, `identity` | All values from `source_url` and `url` (lists flattened). Keys: clip's `url_key`, plus `arxiv:<id>` (from abs/pdf/html, with `vN` dropped) and `doi:<doi>`. Non-HTTP values are kept as opaque keys and counted in diagnostics |
| `added` / `added_source` | `created` ?? the zorg block date in `source_block: ^z-YYMMDD-…` ?? opt-in Git first-add date |
| `finished` / `finished_source` | `[completion::]` / `[cancelled::]` on `^ref` ?? opt-in Git date of the status flip. Never use mtime or `highlights_synced_at` |
| `source_pdf`, `annotation_count`, `snapshot` | `annotation_count` counts live `^h-` blocks, excluding mirror-shaped blocks and tombstones. `snapshot.synced_at` comes from frontmatter, with `source_verified: false` |

**`reading_state` mapping (derived, never stored):**

| `reading_state` | From modern `^ref` | From `legacy_status` |
| --- | --- | --- |
| `queued` | `ready`, `next` | `unread` |
| `started` | `wip` (sticky lane, not proof of active reading) | `collect_fleeting_notes` (§2.5) |
| `finished` | `read` | `read`, `review_fleeting_notes`, `review_lit_notes` |
| `dropped` | `abandoned` | `abandoned` |
| `unknown` | none, or a conflict | `book`, missing, unrecognized |

Agents should read `queued` as "already tracked", **not** "never read". A reopened task loses its
completion history, so no field ever asserts "never read".

### 5.4 `bob ref find`

```text
bob ref find [-f human|json] [-i|--include-intake] [-m|--min-title-score N] <QUERY>...
```

- For each query, try in order:
  1. Identity key (URL, arXiv, DOI).
  2. Vault path, `id`, or stem.
  3. Normalized-title similarity (casefolded, punctuation stripped, token set), with a score.
- Return **every** match together with its `match_kind`. For example, *Harness engineering* returns
  both notes, with the most advanced `reading_state` first. A title match is a candidate, not
  proof.
- `--include-intake` uses clip's existing reader to check queued `xlib/` markers. When intake isn't
  checked, `coverage.intake` reports `not_checked`; on a host without `xlib/`, `unavailable`.
- Exit 0 whenever the lookup ran, including no match. Exit 1 on I/O errors and 2 on usage errors.
- Human output is one line per query, for example:
  `arxiv.org/abs/2608.04278  FINISHED (read)  ref/papers/ea_graph.md  "EA-Graph: …"`, or
  `—  not in library (coverage: ref/ only)`.

### 5.5 `bob ref list`

```text
bob ref list [-s STATUS,…] [-R|--reading-state STATE,…] [-t TYPE,…] [-o ORIGIN] [-P PARENT]
             [-S|--since DATE] [-n|--limit N] [-A|--all] [-g|--git-dates] [-f human|json]
```

- Within a field, multiple values are ORed. Across fields, filters are ANDed. `--status` accepts the
  raw values plus `legacy`, `conflict`, and `unknown`.
- Human default: the queue (`queued` + `started`), grouped and colored like
  `refs.base#🔖 Reading Queue`.
- JSON default: all states, **capped at `--limit 50`**, with `matched`, `returned`, and `truncated`
  in the envelope and `--all` to lift the cap. The full compact catalogue is about 140 KB (≈35k
  tokens), and an agent must never mistake a page of results for the whole library.
- Rows never include annotation bodies.

### 5.6 `bob ref show`

```text
bob ref show [-f human|json|markdown] [-a|--annotations-only] [-N|--no-annotations]
             [-D|--include-removed] [-c|--comments-only] <REF>...
```

- `REF` accepts anything `find` resolves to. If a REF matches more than one note, the command fails
  and lists the candidates. It never picks the first stem match.
- Annotations are parsed from the managed region into
  `{page_label, kind: highlight|note|image, quote, comment, asset, block_id, link}`. Quote text
  (the author's words) and comment text (Bryan's words) are **separate fields**, and
  `--comments-only` returns comments and standalone notes with enough quote and page context to
  interpret them. Mirror-shaped blocks and tombstones are excluded by default.
- Also returned: annotation-derived `## Tasks` lines, plus **Bryan's own Markdown outside the
  managed region** (excluding the generated H1, the `^ref` line, and the audio embed). That free
  text is often the strongest signal of what he thought.
- Unknown or old region formats fall back to raw content with
  `structured_annotations_available: false`. They are never silently reported as zero.
- `markdown` output is a clean, quotable digest for an agent's context. For `ref/chat` notes, it
  also prints the matching `research:` artifact reference so the agent can open the full report.

### 5.7 JSON envelope

```json
{
  "schema": "bob.ref.list/1",
  "generated_at": "2026-10-06T19:30:00Z",
  "coverage": {
    "indexed": "ref/**/*.md",
    "notes": 590,
    "intake": "not_checked",
    "not_indexed": ["~425 zorg inline reading records outside ref/ (see `bob ref doctor`)",
                    "lit/, books.md, done_books.md, podcasts/"]
  },
  "matched": 1, "returned": 1, "truncated": false,
  "refs": [{
    "path": "ref/papers/ea_graph.md",
    "title": "EA-Graph: Artifact-Anchored Verification Memory for Coding Agents under Upstream Drift",
    "origin": "external", "ref_type": "papers",
    "status": "read", "legacy_status": null,
    "reading_state": "finished", "reading_state_source": "ref_task:[x]",
    "urls": ["https://arxiv.org/pdf/2608.04278"],
    "identity": {"url_key": "arxiv:2608.04278", "arxiv": "2608.04278", "doi": null},
    "added": null, "finished": null,
    "source_pdf": "lib/papers/ea_graph.pdf",
    "annotation_count": 0,
    "diagnostics": ["marker-mirror block excluded (bob-cli-4r)"]
  }]
}
```

`annotation_count` is 0 here, while the note's `highlights_count` says 1. The only block in the
note is the leaked mirror. Stdout carries only JSON: no ANSI, no prose. Diagnostics go in rows, and
warnings go to stderr.

### 5.8 Clip dedupe: share the identity, but don't create a dead end

Pointing `clip` at the shared identity function closes the `url:` blind spot and lets
`clip https://arxiv.org/html/…v1` see an existing `…/pdf/…` capture. There is a catch nobody else
covered:

- **Legacy notes have no `lib/` PDF**, and `clip --force` only overwrites intake PDFs.
- A naive extension would therefore permanently refuse to capture any of the 144 legacy-unread
  articles. That is exactly the move Bryan makes when he decides to finally read one.

Recommended rule:

- **Refuse as today** on a match against a PDF-backed (Highlights) note.
- **Warn and proceed** on a legacy-only match, and record the legacy note's path in the new marker
  (for example a `supersedes:` field) so `scan` can link or retire the duplicate.

Design this in `bob-cli-39` (recapture and versioning) and call it out in the clip help and
`docs/highlights-clip.md`.

### 5.9 Agent integration

Add a **`bob_ref` skill** in chezmoi, rendered for every provider like `bob_query`. It should say:

> Before recommending reading, run `bob ref find -f json` on every candidate. Drop `finished` and
> `dropped`. Label `queued`/`started` items "already in your library (since …)". Use
> `bob ref list -o external -R finished -f json` for taste, agent-report titles as a
> topic-interest signal, and `bob ref show -c` for Bryan's comments. Never dump `list --all` into a
> prompt. Never write to the library unless asked; `bob ref clip` is the only way to queue.

Reading-list research prompts get a dedupe step and a final-report line such as "Library check:
N of M candidates already tracked (K finished)."

Acceptance exercise (from cdx): the agent must correctly classify, and explain, each of these:

- a finished paper
- a legacy item with old completion evidence (`review_lit_notes`)
- a queued item
- a title near-match
- a URL-variant match (arXiv `abs` vs. `pdf`)
- an intake-only clip
- a source not in the library

### 5.10 Not in v1

- No write verbs.
- No PDF or sidecar I/O in the read path.
- No full-text search over annotations across the library (phase 2 `search` if wanted).
- No `stats` verb; coverage counts go in the envelope and `doctor`.
- No cache, database, embeddings, or MCP server.
- No backfill of `source_url` from `url`.
- No env, config, or field renames.

---

## 6. Alternatives considered

| Option | Verdict |
| --- | --- |
| Skill + canned `bob query` DQL only | **Interim stopgap only:** 3.8 s, noisy stderr, no normalization, checkbox authority, legacy mapping, or annotation parsing |
| Separate read-only `bob ref` beside `bob highlights` (grk) | Viable, but leaves two nouns for one object and invites a third rename. Rejected (§3.2) |
| **Rename to `bob ref` + read verbs (the request, adjusted)** | **Recommended** |
| Broad `bob ref` that only *aliases* the Highlights verbs while help still shows `highlights` | Adds names without fixing the noun. Rejected |
| Dedicated database as source of truth | Competes with frontmatter, checkbox, and PDF state, and adds sync burden. Rejected |
| Zotero or Readwise as the reference manager | Credible for citation-heavy work (Zotero has read-only MCP servers and annotation notes; Readwise models `new/later/archive`). Migration cost is too high for this use case. Their verb shapes (search, item, annotations) validate `find`/`list`/`show` |
| MCP server | Overkill. Every provider harness can run a CLI, and Bob's pattern is CLI + skill |
| Embeddings first | Doesn't establish identity or completion. Revisit only if title/annotation search proves insufficient |

---

## 7. Phased rollout

| Phase | Content | Size |
| --- | --- | --- |
| 1 | Rename: `ref` canonical, `highlights` + `highlights-ref` aliases, `COMMAND_NAME`, help groups, completion, fixtures, docs index | medium |
| 2 | Ref index + `find`/`list`/`show`, JSON schemas, `docs/ref.md`, defensive mirror filtering. Mixed-corpus fixtures: synced, legacy, list-valued `url`, mirror-leaked, setext sidecar, duplicate stems, malformed YAML, root hubs | large |
| 3 | `bob_ref` skill + reading-list prompt step (chezmoi). Schedule it right after Phase 2, because this is where the user-visible win lands | small |
| 4 | Pipeline fixes: `bob-cli-4r` root fix (decide whether to tombstone or drop the ~113 mirror blocks), completion-date stamping, clip on the shared identity with the legacy-adoption rule (`bob-cli-39`) | medium–large |
| 5 | Migrate the zorg reading records (Bryan-reviewed epic, `sase-4b.1` precedent). Until it lands, `doctor` reports the unindexed count and `find` may gain a read-only fallback over zorg `url::` lines | large |
| later | Library-wide annotation `search`, bare `bob ref` = `list`, batch lookups, a `track`/`adopt` writer, durable "ever finished" history | — |

Phases 1–3 fit in one epic.

Validation checks beyond the fixtures:

- **Read verbs are side-effect free:** they perform no writes, spawn no hooks, touch no PDFs, and
  need none of Obsidian, pandoc, a browser, or Highlights.
- **JSON stays valid** even when rows carry diagnostics.
- **Counts agree:** the row count matches `refs.base`, and `annotation_count` matches the retrieved
  live records.
- **Real exports parse:** test against at least one Highlights export from the actual Mac, since
  the existing fixtures are synthetic.

---

## 8. Open questions for Bryan

1. **Noun:** `ref` (matches `[[ref]]`, `^ref`, `ref/`) or `refs` (matches `projects`, `plugins`,
   `refs.base`)? Recommendation: `ref`, recorded in `bob-cli-4b`.
2. **Legacy mapping:** is §2.5 right that `collect_fleeting_notes` means *started* and
   `review_*` means *finished*? Do the 144 legacy-unread items from 2025 still count as "plan to
   read", or should the skill treat them as stale?
3. **Agent reports:** should recommenders treat `ref/chat` items as read material or only as an
   interest signal?
4. **Clip on a legacy match:** warn and supersede (recommended), or refuse?
5. **Zorg migration scope:** include internal `go/` work docs, books, and `lit/`, or only public
   reading?
6. **Agent writes:** may a recommender ever `bob ref clip` its picks automatically, or only
   propose them?

---

## 9. Recommended solution

**Promote `bob ref` to the canonical command for Bob's reference library and its Highlights intake
pipeline.** Keep `bob highlights`, and the long-broken `bob highlights-ref`, as permanent, silent,
hidden aliases. Leave all six existing verbs, env vars, config keys, markers, and frontmatter
untouched.

Add three read-only library verbs on one shared ref index:

- **`find`:** batch identity lookup over `url` + `source_url`, with arXiv/DOI/URL normalization and
  title fallback. Exits 0 on no match.
- **`list`:** filters by status, reading state, type, origin, and date. JSON is capped and
  coverage-stamped.
- **`show`:** metadata, annotations from the managed region with quote and comment kept separate,
  mirror and tombstone filtering, and Bryan's own notes.

Report reading state as the effective status, the raw `legacy_status`, and an evidence-backed
`reading_state`. Never write state, and never claim "never read" or full coverage.

Then, in order:

1. Ship the `bob_ref` skill so reading-list agents check the library by default.
2. Fix `bob-cli-4r` and stamp completion dates in sync.
3. Move `clip` onto the shared identity without making legacy items uncapturable.
4. Run the zorg-record migration as its own Bryan-reviewed epic.

That is the smallest design that answers "have I already read this?" correctly on the vault as it
actually exists.

---

## Sources

- **Swarm reports** (this directory): `__cdx` (catalogue/evidence contract, status precedence,
  validation), `__cld` (reading-list overlap, coverage gap, `bob-cli-4r`, skill), `__grk` (dissent:
  separate command, lookup-first, `class` split, dashboard blind spot), `__mus` (minimal
  alias-promotion, no new state), `__gem` (find/arXiv normalization, `bob query` comparison, module
  layout).
- **Code** (bob-cli `ce54258`): `src/runner.rs` (`SUBCOMMANDS`, `ALIASES`, `rewrite_alias_args`),
  `src/native/highlights_ref/{cli,mod,clip,clip_url,sidecar_render,annotation_tasks,note,sync}.rs`,
  `src/native/completion/kinds.rs`, `docs/highlights-ref-sync.md`, `docs/highlights-clip.md`;
  `bob highlights clip -h`; `bob highlights-ref -h`.
- **Vault** (read-only, athena, 2026-10-06): `~/bob/ref/**` frontmatter and `^ref` lines; `xlib/`;
  zorg `* status::` records across root notes; `gtd_ideas.md` `^z-250318-0l` and `zorg_ref.md`
  (zorg workflow order and stage contents); `read.md`; timed `bob query` runs.
- **Memory:** `cli_rules.md`; `glossary:reference-note`, `glossary:reference-task`;
  `decisions:review-walk-is-tiered` (and its link to `task-lanes-are-sticky`).
- **Beads:** `bob-cli-4r` (marker-mirror leak, reproduced 113/115), `bob-cli-4a` (JSON flag
  convention), `bob-cli-4b` (noun policy), `bob-cli-39` (clip recapture/dedupe).
- **External** (as cited by the swarm, consulted 2026-10-06):
  [Highlights sidecar files](https://highlightsapp.net/how-to/mac/sidecar-files/),
  [Highlights TextBundle export](https://highlightsapp.net/how-to/mac/export-pdf-annotations-as-textbundle/),
  [Zotero PDF reader](https://www.zotero.org/support/pdf_reader),
  [Zotero collections and tags](https://www.zotero.org/support/collections_and_tags),
  [Readwise Reader API](https://readwise.io/reader_api).

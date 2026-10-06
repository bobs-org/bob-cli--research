# `bob ref`: do not absorb `bob highlights`; add a read-only reference library

- **Date:** 2026-10-06
- **Researcher:** grk
- **Question:** Should `bob highlights` migrate to a new `bob ref` that keeps every current Highlights verb and adds agent-facing commands for what Bryan has read, is tracking, and has annotated? Is that a good idea, and what should change?

---

## 0. Bottom line

**Build the agent-facing library. Do not rename or absorb `bob highlights` to do it.**

The use-case is real and overdue: recommending agents today have no honest way to ask "have I already captured or read this URL?" `bob query` can list `ref/` notes, but the JSON is noisy, the two URL fields are split, and a full dump is ~140 KB. A dedicated `bob ref` that indexes vault reference notes is the right tool.

The proposed *migration* — make `bob ref` a superset of `bob highlights {clip,create,doctor,marker,scan,sync}` — is the wrong cut:

1. `bob highlights` is a Highlights.app PDF pipeline (Integrations). `bob ref` should be a vault-object report (Vault), like `bob projects list` or `bob ready`.
2. CLI rules forbid a hard rename. A hidden `highlights` → `ref` alias that stays byte-identical cannot grow a default `list`, which is exactly the UX the new command wants.
3. The live vault has **two reference populations**. Wrapping only the Highlights pipeline would teach agents the wrong catalog.

**Recommended solution:** add a new top-level `bob ref` whose membership is "read-only reports on `type: [[ref]]` notes." Keep `bob highlights` as the PDF integration. Share one URL index so `clip` finally sees the legacy `url:` field. Add a `bob_ref` agent skill. Optionally fold the writers under `bob ref` later; do not couple that rename to v1.

---

## 1. Verdict on the request

The request mixes three products:

| Product | Who it is for | What it does today |
| --- | --- | --- |
| Highlights PDF pipeline | Bryan, Mac cron, `clip`/`create`/`scan` | Write PDFs into `xlib/`/`lib/`, sync markers and sidecars into `ref/` notes |
| Reference library inventory | Agents recommending reading; Bryan listing the queue | Does not exist as a CLI. Partial: `bob query`, `dash_references`, `refs.base` |
| Annotation reader | Agents summarizing what Bryan marked up; Bryan rereading quotes | Notes already hold rendered callouts in `<!-- highlights:begin/end -->` |

The inventory and the annotation reader belong together under `bob ref`. The PDF pipeline does not. Absorbing it would make `bob ref scan --write-pdfs` look like a library query, and would make `bob ref list` look like a Highlights.app operation.

This is the same membership-rule lesson as the 2026-10 command-tree work: nest only under a noun with a stated rule; keep read-only reports from wearing a writer noun. `bob task ready` was rejected for that reason. `bob ref scan` fails the test in the other direction.

**Would I take a different approach?** Yes. Ship `bob ref {list,contains,show}` beside `bob highlights`. Teach agents the lookup verb first. Reuse the URL normalizer already in `clip_url.rs`. Fix clip's dedupe gap as part of the same index. Leave every current `bob highlights` spelling, env var, cron job, and test path alone.

---

## 2. Adjusted requirements

Called out explicitly. Each one changes the request as written.

| # | Adjustment | Why |
| --- | --- | --- |
| **R1** | **Do not migrate the Highlights writers in v1.** `clip`/`create`/`doctor`/`marker`/`scan`/`sync` stay `bob highlights`. | Different membership, different help section, different callers (Mac cron `maybe_bob_highlights_sync`). The Highlights surface is ~37k lines of code+tests; a rename is cost with no agent value. |
| **R2** | **If a rename ever happens, `bob highlights` becomes a permanent hidden alias with byte-identical behavior and no deprecation output.** | `sase/memory/cli_rules.md`. Past hard renames (`bob dataview`, `bob highlights-ref`) left callers broken; `bob highlights-ref` is still unrecognized today. |
| **R3** | **Do not make bare `bob ref` default to `list` if it shares a parser with the `highlights` alias.** | Byte-identical aliases cannot change the no-args case (`bob highlights` currently requires a subcommand and prints help). A *separate* `bob ref` command *may* default to `list`, because CLI rules allow a bare group to default only to a flag-only read-only member (`gkeep`, `freshness`, `plugins`). That default is a reason to keep the commands separate. |
| **R4** | **The primary agent verb is lookup, not dump.** `bob ref contains --url URL` / `bob ref search TEXT`. Full `list --format json` is opt-in and must stay compact. | 590 notes serialize to ~139 KB compact JSON (~35k tokens). Agents recommending one article must not load the catalog. |
| **R5** | **Index both note schemas, and unify `url` / `source_url`.** | 275 of 282 `ref/ai/**` notes store the article on `url:`. Only 2 notes in the whole vault have `source_url`. `bob highlights clip` already walks `ref/` for dedupe and **ignores `url:`**, so it will recapture articles Bryan already tracks. |
| **R6** | **Do not treat Highlights `status` as the reading state.** Project a derived `reading` field from `status` plus `legacy_status`. | Pipeline `status` today: 285 `read`, 282 `legacy`, 17 `abandoned`, 5 `next`, 1 `ready`, 0 `wip`. The 282 `legacy` notes park the real zorg workflow on `legacy_status` (144 `unread`, 92 `collect_fleeting_notes`, 25 `read`, 13 `review_fleeting_notes`, 4 `review_lit_notes`, 4 `abandoned`). The "plan to read" queue agents need is ~236 legacy items, not the 6 Highlights next/ready notes. |
| **R7** | **Distinguish internal research from external reading.** Default agent JSON to `--class external` (or require the flag in the skill). | 286 of 590 notes are `ref/chat/` SASE research reports produced by `bob highlights create`. They are prior *research*, not prior *articles*. Recommending-agents and research-agents want different slices. |
| **R8** | **List never includes annotation bodies. `show` is per-note.** | 115 notes have highlights (361 total, median 2, max 30). All `ref/**/*.md` together are 644 KB. Per-note max is 8.8 KB, which is a fine `show`. Dumping every quote is not. |
| **R9** | **JSON is mandatory, with `schema_version`, matching `bob gkeep` / `bob ready` / `bob freshness`.** `bob highlights` has no `--format json` today. | Agents are the main caller. Human tables are secondary. |
| **R10** | **Do not invent a new status enum or write reading state from `bob ref`.** v1 is read-only. | Status already has three sources of truth (PDF marker, frontmatter, `^ref` checkbox) plus `legacy_status`. A fourth writer would recreate the Highlights conflict machinery. Lane changes stay on the existing `^ref` task / `bob highlights scan`. |
| **R11** | **Add a `bob_ref` skill.** Do not tell agents to "just use `bob query`." | Native DQL is a subset (TABLE/LIST FROM WHERE; `SORT ASC` failed here), emits link-object JSON and ~20 ambiguous-target warnings, and does not know `legacy_status` or URL normalization. |
| **R12** | **Leave `BOB_HIGHLIGHTS_*` and the `highlights:` config block alone.** | Config and the Mac pre-scan hook are an integration contract. Renaming them is a second, unrelated migration. |
| **R13** | **Reuse `clip_url` normalization and the `collect_ref_note_sources` walk.** | The index clip already builds is 90% of `bob ref contains`. Expand it to `url:` and share it. |

---

## 3. What exists today (verified)

### 3.1 `bob highlights` is a PDF integration, not a library

Canonical path: Integrations section of `bob --help`. Subcommands (subcommand required):

```text
clip, create, doctor, marker, scan, sync
```

Code: `src/native/highlights_ref/` (`COMMAND_NAME = "bob highlights"`). Docs: `docs/highlights-ref-sync.md`, `docs/highlights-clip.md`. Output is key: value lines, not JSON.

Pipeline:

1. `create` (Markdown → pandoc/XeLaTeX PDF) or `clip` (URL → Playwright PDF) writes `~/bob/xlib/<ref_type>/<stem>.pdf` with a page-1 marker.
2. Mac cron `maybe_bob_highlights_sync -w` every 15 minutes runs `bob highlights scan`, whose `highlights.pre_scan_hook` (`bob_xlib_pull`) delivers intake.
3. `scan` moves `xlib/<rel>` → `lib/<rel>` and writes `ref/<rel>.md` with `type: "[[ref]]"`, a `^ref` lifecycle task, and a managed `<!-- highlights:begin/end -->` region.
4. Highlights.app annotations arrive via Markdown/TextBundle sidecars next to the PDF; Bob never writes sidecars.

Reading lifecycle on the generated `^ref` line (glossary `reference-task`):

| Checkbox | `status` | Meaning |
| --- | --- | --- |
| `[ ]` | `ready` | In the queue, not started |
| `[*]` | `next` | Queued for action |
| `[/]` | `wip` | Actively reading |
| `[x]`/`[X]` | `read` | Finished |
| `[-]` | `abandoned` | Dropped |
| (none) | `legacy` | Migrated note; no lifecycle checkbox |

`unread`/`done` still parse as deprecated aliases of `ready`/`read`. `legacy_status` preserves a migrated note's old value and is **not** a standard marker-synced field.

### 3.2 CLI law that a rename would hit

From `sase/memory/cli_rules.md`, already applied in `src/runner.rs` `ALIASES`:

- Never hard-rename or remove a command; the old spelling is a permanent hidden alias, byte-identical, no deprecation output.
- Nest only under a noun with a stated membership rule.
- A bare group may default only to a flag-only, read-only member.
- Read-only reports stay top-level (`bob plan`, `bob ready`); `bob task` is only vault-wide task *writers*.

`bob highlights-ref` → `bob highlights` was a hard rename. It is **not** in `ALIASES`. `bob highlights-ref -h` is `unrecognized subcommand` today. Do not repeat that.

Callers of the current name: README, docs, completion tree, `just` smoke, Mac crontab (`docs/vault-git-sync.md`). Those keep working only if the spelling stays callable.

### 3.3 Closest existing CLIs

| Command | Pattern | Take for `bob ref` |
| --- | --- | --- |
| `bob projects {list,sync}` | Vault-object noun; list is read-only; no JSON | Membership model. Add JSON; `projects` is the warning that list-without-JSON is not agent-ready. |
| `bob gkeep` (default `list`) | Integration noun; `-f json` with `schema_version: 1` | JSON envelope, default-to-list (only if `ref` is *not* an alias of `highlights`). |
| `bob ready` / `bob freshness` | Top-level read-only reports, JSON schema versions | v1 of `bob ref` should live here: Vault section, report-shaped. |
| `bob query` | Generic DQL/Tasks | Stopgap, not the product. See §5. |

### 3.4 Human surfaces already exist and they lie about the queue

- `dash_references.md` embeds `refs.base` view **🔖 Reading Queue**, filtered to `status == next\|wip\|ready`.
- `docs/dashboard.md`: the REFERENCES chip counts that view. Today that is **6 notes**, all `ref/chat/`.
- `refs.base` formulas already know zorg labels (`unread`, `collect_fleeting_notes`, `review_fleeting_notes`, `review_lit_notes`) but they read the `status` field, which migration rewrote to `legacy`. `formula.source` reads `note.url`, not `source_url`.
- The "📚 All Refs" view is misnamed: it also filters `next/wip/ready`.

The dashboard is a human reading-queue for Highlights-lifecycle notes. It is not an agent catalog, and it hides the 275 URL-bearing AI articles.

### 3.5 Clip already walks `ref/` — incompletely

`src/native/highlights_ref/clip.rs` `collect_ref_note_sources` recursively reads every `ref/**/*.md` frontmatter and records `source_url` with the `clip_url.rs` dedupe key (lowercase host, no `www.`, no tracking params, no trailing slash). It skips `url:`. That is the exact bug the new index should close, and the exact code to share.

---

## 4. The live vault (2026-10-06, `~/bob`)

590 Markdown notes under `ref/`. 307 PDFs under `lib/`. 0 PDFs in `xlib/` at sample time. Every note has `type: "[[ref]]"`.

### 4.1 Two populations

| Corpus | Paths | Count | Lifecycle | URL field | `^ref` + managed region |
| --- | --- | --- | --- | --- | --- |
| Highlights-generated | `ref/{chat,blogs,papers,docs}/` | 308 | `status: read/next/ready/abandoned` | `source_url` on 2 notes; `url:` rare | Yes (308) |
| Legacy AI / zorg | `ref/ai/**` | 282 | `status: "legacy"` + `legacy_status` | `url:` on 275 | No |

`ref_type` is set only for the Highlights corpus (`chat` 286, `docs` 11, `blogs` 6, `papers` 5). Legacy notes have no `ref_type`; their parent is a topic note (`[[agent_ref]]`, `[[claude_code_ref]]`, …).

**Highlights `status` histogram**

| status | n |
| --- | --- |
| `read` | 285 |
| `"legacy"` | 282 |
| `abandoned` | 17 |
| `next` | 5 |
| `ready` | 1 |
| `wip` | 0 |

The 6 open Highlights-lifecycle notes (`next`/`ready`) are internal SASE research (`agent_history_in_agents_tab`, `goals_redesign_recent_reading_list`, `memory_built_instruction_migration_epics`, `toobig_split_beyond_python`, `memory_and_instruction_file_inspiration_reading_list`, `global_just_recipe_completion`). None is an external article.

**`legacy_status` histogram (the real external queue)**

| legacy_status | n | Meaning in the old zorg workflow |
| --- | --- | --- |
| `unread` | 144 | Captured, not read |
| `collect_fleeting_notes` | 92 | Still in collect |
| `read` | 25 | Finished in the old system |
| `review_fleeting_notes` | 13 | Reviewing fleeting notes |
| `review_lit_notes` | 4 | Reviewing literature notes |
| `abandoned` | 4 | Dropped |

A recommending agent that filters `status=read` will mostly see chat research PDFs and will miss both the 144 unread articles and the 25 actually-read AI articles. A recommending agent that filters `status=next` will see six internal reports.

### 4.2 Identity is messy, and that is the point of a dedicated command

- `source_url`: 2 notes (web clips).
- `url:`: 283 notes (almost all legacy AI). Some values are YAML-broken (`- "https://..."`, `http://go/...`, `bbc:~/.gemini/GEMINI.md`, a local `~/tmp/...` path).
- Duplicate `source_url`s: 0. Duplicate *normalized* `url`s were not exhaustively proven; several `go/` short links and malformed list-prefix URLs will not parse as `http(s)`.
- `title`: 531 / 590.
- `author`: 2. `topics:`: 0. Do not design v1 around topics or authors; they are unused.
- Tags: all 282 AI notes carry `ai/reference`.

`clip_url.rs` already knows how to clean a URL. `bob ref contains` should run the same cleaner on both fields, skip unparseable values with a warning count, and match the dedupe key.

### 4.3 Annotations are small and already in Markdown

| Measure | Value |
| --- | --- |
| Notes with `highlights_count > 0` | 115 |
| Highlight total | 361 |
| Median / p90 / max count | 2 / 7 / 30 |
| Note size min / p50 / p90 / max | 691 / 979 / 1319 / 8718 bytes |
| Sum of all `ref/**/*.md` | 644 KB |
| Compact catalog JSON (path, title, statuses, url, ref_type, highlights_count) | ~139 KB |

Agents can afford `bob ref show <id>`. They cannot afford `bob ref list --annotations`. The managed region is already the annotation API: quote callouts, nested comment callouts, `^h-…` block IDs. `show` should print that region (plus a short metadata header). It should not parse PDFs or sidecars; the note is the agent-visible copy, and Highlights may fail to export TextBundles in the first place (`docs/highlights-ref-sync.md`, known app bug).

### 4.4 `bob query` as of this run

```text
TABLE file.path, title, status, ref_type, author, source_url, highlights_count
FROM "ref" WHERE type = "[[ref]]"
```

worked (native engine). Adding `SORT … ASC` failed (`unexpected ASC after native query`). Markdown format is a wide table of wikilinks. JSON wraps every path as a link object and prints ~20 `ambiguous Dataview link target` warnings. `url` and `source_url` are separate columns, so a `WHERE source_url` query misses the AI corpus.

Usable as a desperate stopgap. Not an agent contract.

---

## 5. Alternatives

### A. Rename `bob highlights` → `bob ref` and add list/show (the request)

- **For:** One noun in help; matches `ref/`, `[[ref]]`, `^ref`, `#ref`.
- **Against:** R1–R3. Cron, docs, and 37k lines of tests churn. `scan --write-pdfs` under a library noun. No-args cannot default to list. Legacy notes still would not appear unless list is written as a *new* scanner, at which point the rename did not help.

Reject for v1. Revisit only after the inventory exists, if help clutter from two nouns actually hurts.

### B. Document a canned `bob query` and stop

- **For:** Zero code.
- **Against:** R4, R5, R6, R11. Agents will write the wrong WHERE, miss `url:`, and dump 140 KB of link objects. Clip's dedupe gap stays open.

Reject as the product. Accept as a one-line "until v1 ships" note in the skill.

### C. New `bob ref` (read-only) beside `bob highlights` (recommended)

- **For:** Clean membership; default `list` is legal; Highlights callers untouched; can still share the URL index with `clip`.
- **Against:** Two nouns in help. Bryan types `bob highlights clip` and `bob ref contains` in the same session.

Accept the extra noun. Help already separates Integrations from Vault (`gkeep` vs `query`). This is the same split.

### D. Broad `bob ref` that *aliases* the Highlights verbs without changing the canonical name

`bob ref clip` would dispatch to the same leaf as `bob highlights clip`, while help still lists `highlights`. Extra names to complete, document, and test, for a session that already knows `highlights clip`. Defer. If it happens, it is additive (CLI may only grow names).

### E. Top-level `bob refs` (plural) like `bob projects`

Mildly nicer as an inventory name, worse against vault vocabulary (`ref/`, `[[ref]]`, `^ref`). SASE agents already say "ref" for `research:…` artifact identities; `bob ref` vs `sase artifact` is disambiguated by the binary. Prefer `bob ref`.

---

## 6. Recommended solution

### 6.1 Command

New Vault-section command, `src/native/refs/` (do not grow `highlights_ref` into a query engine).

Membership rule: **`bob ref <verb>` reads vault reference notes (`type: [[ref]]`) and reports their catalog, identity, and stored annotations. It does not write PDFs, markers, or notes.**

```text
bob ref                         # = list (human table)
bob ref list [filters] [-f json|markdown|table]
bob ref contains --url URL [-f json]
bob ref search TEXT [filters] [-f json]
bob ref show <path|stem|url> [--annotations] [-f json]
```

Default is `list`, flag-only, read-only. Subcommands alphabetical. Every long option gets a short alias. Colored human table; JSON on `-f json`.

**Filters (list/search):**

| Flag | Effect |
| --- | --- |
| `-s, --status` | Pipeline status: `ready`, `next`, `wip`, `read`, `abandoned`, `legacy` |
| `-L, --legacy-status` | Exact `legacy_status` |
| `-R, --reading` | Derived field (R6): `read`, `unread`, `ready`, `next`, `wip`, `abandoned`, plus the zorg collect/review values |
| `-t, --ref-type` | `chat`, `blogs`, `papers`, `docs`, or empty for legacy |
| `-c, --class` | `external` (has a parseable URL, or path under `ref/ai`, or `ref_type` in blogs/papers/docs) · `chat` · `all` (human default) |
| `-u, --url` | Dedupe-key match (also the body of `contains`) |
| `-H, --has-highlights` | `highlights_count > 0` |
| `-p, --parent` | Frontmatter parent note |

**JSON envelope** (`schema_version: 1`; bump on breaking field changes, optional fields stay on 1):

```json
{
  "schema_version": 1,
  "command": "list",
  "count": 3,
  "refs": [
    {
      "path": "ref/ai/agent_ref/12_factor_agents.md",
      "title": "12 Factor Agents",
      "status": "legacy",
      "legacy_status": "unread",
      "reading": "unread",
      "class": "external",
      "ref_type": null,
      "parent": "[[agent_ref]]",
      "url": "https://example.com/12-factor",
      "urls": ["https://example.com/12-factor"],
      "author": null,
      "id": "12_factor_agents",
      "source_pdf": null,
      "highlights_count": 0
    }
  ]
}
```

`show --format json` adds `annotations: [{kind, page, text, comment, block_id}]` parsed from the managed region when present, else `body` for legacy notes (capped; full file is 8 KB).

**Exit codes:** 0 on a successful report (including zero matches); 1 I/O; 2 usage. Do not mimic grep's "not found → 1"; bob reports are 0 with an empty list (`ready`, `gkeep list`, `query`).

**Skill (`bob_ref`):** before recommending an article, run `bob ref contains --url … -f json`. For prior SASE research, `bob ref search "…" -c chat -f json`. Never paste a full `list -f json` into a prompt. `show` only after a hit.

### 6.2 Derived `reading`

```text
if status in {ready, next, wip, read, abandoned}:
    reading = status
else if status == legacy and legacy_status:
    reading = legacy_status
else:
    reading = status
```

Do not collapse `collect_fleeting_notes` into `ready`. Agents need "captured, not processed" as its own state. Do not write this field back to disk.

### 6.3 Shared URL index (the one Highlights change that *is* in scope)

Extract `clip_url` + the `ref/` frontmatter walk into a small shared module used by:

1. `bob ref contains` / `list --url`
2. `bob highlights clip` dedupe, now consulting `url` **and** `source_url`

This is a behavior change for `clip` (it will start refusing URLs Bryan already tracked in `ref/ai/`). That is the correct change, and it should be called out in the clip help and in `docs/highlights-clip.md`. Skip unparseable `url:` values; do not fail the whole clip.

### 6.4 What v1 does not do

- No `bob ref clip/create/scan/sync`.
- No writing `status`, `legacy_status`, or the `^ref` checkbox.
- No PDF or sidecar I/O.
- No full-text search of PDF bytes (Obsidian has no PDF text index either; prior clip research noted this).
- No backfill of `source_url` from `url:` (optional later; the index can treat them as aliases without rewriting notes).
- No env-var rename.

### 6.5 Implementation sketch

1. New `NativeCommand::Ref` mounted in Vault, alphabetically near `query`.
2. Scanner: walk `BOB_HIGHLIGHTS_REF_DIR` (keep using that env; do not invent `BOB_REF_DIR`), parse YAML frontmatter only, ~590 files / 644 KB, well under a second.
3. URL: call the existing cleaner; collect keys from `source_url` then `url`.
4. Human list: columns `reading`, `class`, title, parent, url host, highlights. Color by reading (ready/next/wip/read/abandoned/legacy).
5. Tests against fixtures that include *both* a Highlights-shaped note and a `url:` + `legacy_status: unread` note. A query that only sees `source_url` must fail the fixture.
6. Equivalence: `bob ref contains` and `clip` refuse the same URL.
7. Completion: `Kind::VaultNote` for `show`; `Kind::Choices` for `--status` / `--class` / `--format`.
8. Docs: `docs/ref.md` for the library command; Highlights docs keep their names; README table gets one Vault row.

Phase 2 (separate, only if wanted): hidden alias `highlights` → `ref` **or** additive `bob ref clip` names. Not this change.

### 6.6 Why this is the right size

The expensive part of Highlights is PDF markers, sidecar parsing, Git dirty-target guards, and annotation-task import. None of that is required to answer "do I already have https://arxiv.org/abs/2603.05344?" Frontmatter scan + URL keys is a small command with a large agent payoff, and it fixes a real `clip` miss.

---

## 7. Critique recap (is the original plan a good idea?)

**The library idea: yes. The migration: no.**

Keeping Highlights verbs under a new `ref` noun looks tidy in a sketch and fights the rest of bob:

- Help sections already split integrations from vault reports.
- Hidden-alias law makes the attractive default (`bob ref` → list) illegal on a shared parser.
- The vault's actual "what have I read / what am I tracking" data lives on a *different schema* than the Highlights pipeline. A rename would not even index it unless the new scanner were written anyway.
- `dash_references` / `refs.base` already tried "the reading queue is `next|wip|ready`" and currently show six internal chat notes while 144 unread articles sit on `legacy_status`. Copying that filter into a CLI would bake the same blind spot into agents.
- Agents need lookup-by-URL, compact JSON, and a class split. None of those fall out of moving `scan` under another name.

The one Highlights change worth bundling is clip dedupe against `url:`.

---

## 8. Evidence index

| Claim | Source |
| --- | --- |
| Highlights subcommands, no JSON | `src/native/highlights_ref/cli.rs`, `mod.rs`; `bob highlights -h` |
| CLI rename / membership / default-list rules | `sase/memory/cli_rules.md`; `src/runner.rs` `ALIASES` |
| `highlights-ref` not aliased | `bob highlights-ref -h` → unrecognized |
| Glossary | `glossary:ref-note`, `glossary:ref-task` |
| Marker / `^ref` / managed region / `legacy_status` | `docs/highlights-ref-sync.md` |
| Clip pipeline and `source_url`-only dedupe | `docs/highlights-clip.md`; `clip.rs` `collect_ref_note_sources`; `clip_url.rs` |
| Mac cron | `docs/vault-git-sync.md` |
| Command-tree membership lesson | `research:202610/bob_cli_command_tree_reorganization/` (prior, not this swarm) |
| Live vault counts, statuses, URL fields, sizes | `~/bob/ref` scan, 2026-10-06 |
| `bob query` SORT failure and JSON shape | native engine run against `FROM "ref"` |
| Dashboard queue filter | `~/bob/dash_references.md`, `~/bob/refs.base`, `docs/dashboard.md` |
| JSON schema precedent | `src/native/gkeep/list.rs`, `src/native/note_ready/cli.rs`, `src/native/freshness/cli.rs` |

---

## 9. Recommended solution (one paragraph)

Add **`bob ref`** as a new Vault-section, read-only library command (`list` default, `contains`, `search`, `show`) with compact versioned JSON, a derived `reading` field, a `class` split, and URL lookup over both `url` and `source_url`. Keep **`bob highlights`** as the Highlights.app PDF integration, unchanged in name, env, cron, and writers. Share the `ref/` frontmatter + `clip_url` index so clip stops recapturing legacy articles. Ship a **`bob_ref` skill** that forces lookup-before-recommend and forbids dumping the catalog. Do not rename, do not default a shared parser to `list`, do not write status, and do not put annotation bodies on `list`. That is the smallest design that actually serves the stated agent use-case on the vault as it exists.

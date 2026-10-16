# Should qmd search Bryan's Bob vault, and how?

- **Researcher:** grk
- **Date:** 2026-10-16
- **Question:** Is integrating [tobi/qmd](https://github.com/tobi/qmd) into bob or the Obsidian vault a good idea, and what is the best implementation if so? The seed idea is agent instructions that call qmd when searching the vault.
- **Verdict:** The *gap* is real: SASE agents have Dataview (`bob query`), a reference catalog (`bob ref`), and grep, and they still cannot recall prose by paraphrase. qmd is the right off-the-shelf tool for that gap. The *seed plan* (index the whole vault, tell agents to use qmd, maybe wrap it as a bob command) is the wrong shape. Treat qmd as a **host-side retrieval cache** with curated collections, a Bob-specific routing skill, and BM25 as the default. Keep it out of bob-cli until a labeled eval on this vault proves hybrid search earns its Node/GPU cost.

---

## 1. In one breath

qmd is a local hybrid search engine (SQLite FTS5 BM25 + sqlite-vec + optional LLM expansion/rerank) aimed at agentic markdown retrieval. It is actively developed (30k GitHub stars, last commit 2026-10-14, MIT, Tobi Lütke). It already ships a CLI, MCP server, Node SDK, and an upstream agent skill whose loop is search → `qmd get` → cite.

Bryan's vault is a **structured GTD system with a small knowledge corpus attached**, not a Zettelkasten of atomic prose. On 2026-10-16 it holds **6,354 markdown files / 13.1 MB**. Roughly half of that is daily notes plus `_generated` Dataview dumps. First-class bob commands already own tasks, lanes, freshness, projects, and the reference library. qmd should cover the leftover job: *“what have I written about X, in words I do not remember.”*

Do that as a **chezmoi-managed qmd config + a SASE skill that routes queries**, refreshed by a timer after `bob vault-sync`, on the machine agents already run on (apollo). Do not fold Node, GGUF models, or a second metadata schema into bob-cli. Do not paste the upstream qmd skill into CLAUDE.md. Do not index the whole vault.

---

## 2. Critique of the plan

The plan as stated: integrate qmd into bob or the Obsidian vault, for example by teaching agents to use it when searching notes.

### What is right

- **The retrieval gap is real.** `bob query` evaluates Dataview DQL and Obsidian Tasks. `bob ref` looks up the Highlights library by URL/title. Grep matches exact tokens. None of those answers “where did I write about metric-driven product judgment” when the note says “cockpit instruments.” That is exactly the job qmd’s vector + HyDE path is for.
- **qmd is built for agents, not for an Obsidian pane.** JSON/`--files` output, stable `#docid`s, line-numbered `get` with `path:from:count`, MCP, and an explicit “snippets are leads, fetch the source” skill. Agents on apollo have no Obsidian GUI, so OmniSearch’s HTTP API (which dies when Obsidian closes) is the wrong daemon.
- **The vault is small enough.** 13 MB of markdown is a rounding error for embeddinggemma-300M. Indexing cost is operational and quality, not capacity.
- **Local models match Bob’s privacy posture.** Vault git sync already keeps notes on athena/apollo/mac. Sending the corpus to a cloud embedding API would be a new data-handling decision. qmd keeps bytes on disk.
- **Collection context is the feature the seed plan underweights.** qmd’s own README calls path-prefix context “the key feature.” A reranker that knows `ref/` is a Highlights note and `2026/` is a Pomodoro ledger will rank better than a skill that only says “use qmd.”
- **A CLI skill is the native SASE pattern.** `bob_query` already tells agents to use `bob query` instead of parsing the vault. A sibling skill for conceptual search fits the house style better than an MCP server or a new bob subcommand.

### What is wrong

1. **“Use qmd when searching the vault” is too broad.** Most agent vault questions are GTD: open tasks, Ready caps, today’s ledger, “is this URL in the library,” “which project is blocked.” Those have authoritative engines (`bob plan`, `bob freshness`, `bob ready`, `bob query --tasks`, `bob ref find`). Pointing every search at qmd will skip those engines and return task-checkbox soup.

2. **Indexing the whole vault poisons the index.** Folder census of `~/bob` (excluding `.git` / `.obsidian`):

   | Slice | Files | Bytes | Role |
   | --- | ---: | ---: | --- |
   | `_generated/` | 1,131 | 3.20 MB | Dataview/zoq dumps (`all_read.md` is 445 KB) |
   | Daily notes `2023/`–`2026/` | 3,014 | ~5.5 MB | Pomodoro ledgers |
   | `ref/` | 1,043 | 1.13 MB | Highlights reference notes |
   | Root-level `*.md` | 643 | (mixed) | Areas, projects, evergreen notes |
   | `prj/` | 50 | 0.17 MB | Project notes |
   | `lit/` | 81 | 0.24 MB | Literature |
   | `done/` | 29 | 0.43 MB | Archived tasks |
   | Rest | — | — | templates, meta, eat, prompts, … |

   Default glob `**/*.md` with qmd’s built-in ignores (`node_modules`, `.git`, `.cache`, `vendor`, `dist`, `build`) **does not skip** `_generated`, year folders, `done/`, or `.obsidian`. Daily notes and generated query dumps would dominate BM25 term frequency and embedding neighborhood.

3. **Bob frontmatter is invisible to qmd filters and toxic to qmd vectors.** Filterable metadata is opt-in under a nested `qmd.metadata` YAML block (`src/metadata.ts`). Bob already has `type: "[[project]]"`, `parent: "[[gtd]]"`, tags, `status`, `task_count`. qmd will not filter on those unless every note grows a parallel namespace. Meanwhile issue [#975](https://github.com/tobi/qmd/issues/975) (open, 2.8.3) documents that YAML frontmatter **is** chunked, embedded, and returned as the top snippet, with bland vectors that rank #1 even on gibberish queries. 628 of 643 root-level notes have frontmatter. Writing `qmd.metadata` into the vault to paper over this would create a second schema next to Dataview.

4. **Title extraction will miss Bob’s naming.** qmd titles come from the first `#` / `##` heading, with a special case for “Notes” (`extractTitle` in `src/store.ts`). Only **31 of 643** root-level notes have an H1. Most titles will fall back to the filename, which is actually fine (routes *are* the names), but it means qmd will not pick up YAML `title` or wiki-link display text.

5. **Hybrid search is the expensive, fragile mode, and apollo is CPU-only.** This host: Linux KVM, 16× Xeon 8168, 31 GB RAM, **no NVIDIA GPU**, Node v24.15.0, qmd **not installed**. Open issues that land on this machine:

   | Issue | Why it matters here |
   | --- | --- |
   | [#942](https://github.com/tobi/qmd/issues/942) | Each `qmd query` loads models independently; **~4.5 GB RSS per process** on CPU Linux. Four concurrent SASE agents ≈ 18 GB. apollo has 31 GB and **zero swap**. |
   | [#709](https://github.com/tobi/qmd/issues/709) | Embedding saturates a CPU VPS; open question whether qmd is meant to be an agent memory backend without a GPU. |
   | [#1053](https://github.com/tobi/qmd/issues/1053) | A broken reranker silently scores everything 0.5 and **caches** it. |
   | [#987](https://github.com/tobi/qmd/issues/987) | `qmd query` can OOM by joining full bodies per matching chunk. |
   | [#1039](https://github.com/tobi/qmd/issues/1039) | Timeout-killed `vsearch` leaves a 100% CPU orphan (TERM ignored). |
   | [#809](https://github.com/tobi/qmd/issues/809) | No `--timeout`. |
   | [#1073](https://github.com/tobi/qmd/issues/1073) | npm `@tobilu/qmd` is **2.8.3 (2026-08-16)**; git `main` is **116 commits ahead** (HEAD `86d2365`, 2026-10-14), including metadata, faster reindex, collection-partitioned vectors, and security gates. |

   `qmd search` (BM25, no models) is the mode that is cheap, fast, and already better than unranked grep. `qmd query` is a maybe, after a daemon and an eval.

6. **Wrapping qmd as `bob search` pulls a second runtime into a Rust CLI.** bob-cli is native Rust. qmd is Node ≥ 22 + `better-sqlite3` + `node-llama-cpp` + optional tree-sitter grammars + ~2 GB of GGUF files. `cli_rules.md` would put a new read-only report in the Vault help section, with `-h`, short aliases, and a permanent hidden alias if it is ever renamed. That is a large, sticky surface for a subprocess of an independently versioned npm package that currently lags git by two months. The gkeep Python adapter is the cautionary analog: a foreign runtime, justified because Google Keep has no Rust client. Search does.

7. **An Obsidian plugin solves Bryan-at-the-keyboard, not agents.** Community ports exist (`thirteen37/obsidian-qmd`, `achekulaev/obsidian-qmd`, `GoBeromsu/obsidian-qmd`). They need the desktop app, they fight `bob plugins sync` if dropped into `~/bob/.obsidian/plugins/`, and SASE agents never see the pane. OmniSearch and Smart Connections have the same audience mismatch. Smart Connections also writes `.smart-env/` **inside the vault**, which would ride git sync; qmd’s index lives in `~/.cache/qmd/index.sqlite`, which is the right place.

8. **The upstream skill is a bad default for Bob.** `skills/qmd/SKILL.md` says: use qmd before web search; default to structured `qmd query` with `intent:`/`lex:`/`vec:`/`hyde:`; you are a better expander than the 1.7B model. Installed unmodified, agents will hybrid-search for “Ready cap on cash.md” and skip `bob ready`. Bob needs a **router** skill, and the upstream qmd skill as a cited subroutine for the conceptual branch only.

9. **Index freshness is a second sync problem.** `bob vault-sync` already reconciles the vault across athena, apollo, and the Mac. qmd’s collection `update:` hook runs arbitrary bash (often `git pull`) before reindex. Pointing that at `~/bob` would race `bob-vault-sync.service`. The index is a **derived cache per machine**. Agents need it on apollo. Bryan’s Obsidian session on the Mac does not need a second copy unless he starts using the CLI there. Do not git-sync `~/.cache/qmd`.

10. **qmd is not a source of truth.** Search hits are snippets from a possibly stale SQLite copy. Quotes, decisions, and task state have to be read from the vault file (`qmd get --full-path` then `Read`, or `bob query` / `bob ref show`). Teaching agents to answer from snippets is how #975’s frontmatter garbage becomes hallucinated “facts.”

### Would I take a different approach?

Yes. Start with a **retrieval router**, not an integration.

The first week of work is: install qmd from git (until npm moves), write a curated `~/.config/qmd/index.yml`, run `qmd update` (BM25 only), add a SASE skill that partitions questions, and score a 20-query fixture against grep and `bob query`. Embed and hybrid search are a second week, gated on that fixture. A `bob search` wrapper is a third-month convenience if the skill’s argv is stable and annoying to type. An Obsidian plugin is out of scope for the agent problem.

Mandalivia’s February 2026 write-up (“Semantic Search for Your Obsidian Vault”) recommends almost the seed plan: collections + context + a CLAUDE.md paragraph that says “use qmd instead of Grep for conceptual search.” That write-up is the right *shape* for a 2,400-note Zettelkasten of atomic notes and MOCs. Bob is a GTD vault with 3,000 daily notes and 1,100 generated dumps. Copying the CLAUDE.md paragraph without the router and the ignore list would be a regression.

---

## 3. Justified requirement adjustments

These change the user’s wording. They are deliberate.

| Original implication | Adjustment | Why |
| --- | --- | --- |
| Integrate qmd into bob-cli | Keep qmd as a **host tool** (`qmd` on PATH, config in `~/.config/qmd`). Revisit a thin `bob notes search` subprocess only after the skill’s flags stabilize. | bob is Rust-native; qmd is Node + llama.cpp + 2 GB of models. CLI rules would freeze a foreign binary into the public surface. |
| Agent instructions: “use qmd when searching the vault” | Ship a **router skill**: GTD/structure → `bob query` / `bob plan` / `bob freshness` / `bob ready` / `bob ref`; exact tokens → Grep/`bob query --source`; paraphrase/prose → `qmd search` then `qmd get --full-path`. | Unrouted qmd steals questions the other engines already answer correctly. |
| Index `~/bob` as one collection | Three collections: `knowledge` (default), `refs`, `dailies` (`includeByDefault: false`). Ignore `_generated`, `_templates`, `_conflicts`, `_meta`, `done`, `lib`, `xlib`, `old_lib`. | Whole-vault glob is 50% ledger + dumps. Context and default-include are qmd’s actual ranking features. |
| Teach the upstream qmd skill verbatim | Write a Bob overlay. Keep upstream as a reference for the get/multi-get loop. Default agents to **`qmd search` (BM25)**; `qmd query` is opt-in and `--no-rerank` on apollo. | Upstream defaults to hybrid + self-authored expansion, which loads ~4.5 GB/process here. |
| Use `qmd.metadata` / `--filter` on Bob notes | Do **not** write a `qmd:` frontmatter block into the vault. Type/parent/tag filters stay on `bob query`. | Parallel schema next to Dataview; qmd still embeds the existing YAML (#975). |
| MCP as the integration | CLI skill first. If hybrid search is enabled, run **one** `qmd mcp --http --daemon` on localhost and serialize through it. | Concurrent CLI `query` exhausts RAM (#942). SASE already prefers audited shell skills (`bob_query`). |
| Refresh inside `bob nightly` | Separate user timer/service after vault-sync, `qmd update` then optional `qmd embed`. Never `git pull` from a collection `update:` hook. | nightly holds `bob_sync.lock` and is a git sequence. qmd is a derived cache. Dual git pull races vault-sync. |
| Pin `@tobilu/qmd@latest` from npm | Install from **git SHA** (or wait for a 2.9 npm). Record the SHA in chezmoi. | npm 2.8.3 is 116 commits behind; missing partitioned vectors, mtime skip, trust gates, metadata. |
| Index once, share across machines | Per-machine index. Agents use apollo’s. Mac gets one only if Bryan uses the CLI there. | sqlite-vec + GGUF are local; git-syncing `~/.cache/qmd` is conflict bait. |
| Turn it on for all agents immediately | Gate on a **20-query labeled fixture** from this vault (10 lexical, 10 paraphrase). Ship BM25 if hybrid does not beat it on paraphrase@5. | Frontmatter vectors and daily-note noise can make hybrid *worse* than BM25 on this corpus. |

---

## 4. What qmd actually is (as of this checkout)

Opened via `sase repo open gh:tobi/qmd`. Path: this workspace’s `sase/repos/external/gh/tobi/qmd`. HEAD `86d2365` (2026-10-14). Latest tag / npm: **v2.8.3** (2026-08-16). Package `@tobilu/qmd`, Node `>=22`, MIT. GitHub: **30,439** stars, 1,914 forks, created 2025-12-08.

### Pipeline

```
query → (optional LLM expand: lex / vec / hyde)
      → BM25 FTS5  +  sqlite-vec
      → RRF (original query ×2, top-rank bonus)
      → optional Qwen3-0.6B rerank
      → position-aware blend
```

| Mode | Command | Models | Role |
| --- | --- | --- | --- |
| Lexical | `qmd search` | none | Fast BM25. Default for Bob. |
| Vector | `qmd vsearch` | embed | Paraphrase. Sensitive to frontmatter chunks. |
| Hybrid | `qmd query` (alias `deep-search`) | embed + expand + rerank | Best-quality path in the README; costliest and least stable on CPU. |

Models (auto-downloaded to `~/.cache/qmd/models/`):

| Role | Default GGUF | Size |
| --- | --- | --- |
| Embed | embeddinggemma-300M-Q8_0 | ~300 MB |
| Rerank | qwen3-reranker-0.6b-q8_0 | ~640 MB |
| Expand | qmd-query-expansion-1.7B-q4_k_m | ~1.1 GB |

Index: `~/.cache/qmd/index.sqlite`. Config: `~/.config/qmd/index.yml` (XDG). Named indexes via `--index`. Project-local `.qmd/index.yml` exists (`qmd init`) and is **trust-gated** as of 2.8.3 (update hooks, out-of-tree paths, custom model URIs). User config in `~/.config/qmd` is not gated.

### Agent surface

- CLI: `--format json|md|files|csv|xml`, `--full-path`, `--explain`, `--no-rerank`, `-c` collections, `--filter` JSON AST.
- Retrieval: `qmd get '#abc123:120:40'`, `qmd multi-get`, line numbers on by default.
- MCP tools: `query`, `get`, `multi_get`, `status`, `metadata`. HTTP on `:8181` with Origin/Host checks (DNS-rebinding fix, 2.8.3).
- SDK: `createStore({ dbPath, config })` — relevant only if bob-cli were to embed it, which this report rejects.
- Skill: `skills/qmd/SKILL.md` (search → get → cite; author `intent`/`lex`/`vec`/`hyde` yourself).

### Properties that matter for Bob

- Default glob `**/*.md`; `dot: false` and a post-filter skip any path segment starting with `.`, so `.obsidian` is safe **if** the glob is from the vault root. `_generated` is not.
- Files over **10 MB** are skipped (`REINDEX_MAX_FILE_SIZE`). Bob’s largest md is 445 KB, so size will not save you from indexing dumps.
- Recent git (post-2.8.3) skips unchanged files via `file_sync_state` (mtime + size); first index of 20k files claimed ~5 s. A 6k-file Bob vault is an easy BM25 reindex.
- Collection-partitioned vectors (git, not npm): a small `refs` collection is no longer crowded out by a large `dailies` collection. Another reason to install from git.
- No wiki-link graph. `[[bob]]` is text. Backlinks, block IDs (`^prj`), and task status are opaque.
- AST chunking is for TS/JS/Py/Go/Rust. Markdown always uses regex heading/HR/fence breaks. Task-heavy notes chunk as walls of checkboxes.

---

## 5. What Bob already has

| Need | Engine | Use when |
| --- | --- | --- |
| Tasks by status, tag, note, date | `bob query --tasks` / DQL | Structured GTD |
| Notes by type/tag/folder | `bob query --source` / `--query` | `type: project`, `#waiting`, `"prj"` |
| Today / Next / Pending | `bob plan` | Ledger, not search |
| Freshness walk | `bob freshness` | NEW/ROTTEN/TICKLER |
| Ready cap | `bob ready` | Per-note Ready lane |
| Reference identity, reading state, annotations | `bob ref find/list/show` | URL, DOI, title, library |
| Exact token, block id, filename | Grep / `rg` | `^prj`, `#now` (retired), a route name |
| Conceptual prose across evergreen + article notes | **nothing** | The qmd gap |

`docs/dataview.md` is explicit: `bob query` does not reconcile the vault; freshness is `bob vault-sync`’s job. The same split should apply to qmd: it reads whatever is on disk, and a separate timer refreshes the cache.

Agent guidance already exists for the structured side (`bob_query` skill: use `bob query`, do not parse the vault ad hoc). Conceptual search currently falls through to Grep, which is why the seed idea came up.

Vault layout that a collection config has to respect (from bob-cli README): `mac_inbox.md` / `gkeep_inbox.md`, area/project notes at vault root and `prj/`, dailies at `YYYY/YYYYMMDD.md`, `ref/` Highlights notes, `done/` archives, `xlib/`+`lib/` PDFs (qmd will not search PDFs; `bob ref` already owns those), `_conflicts/`, gitignored custom plugins.

---

## 6. Alternatives

| Option | Verdict for this problem |
| --- | --- |
| **Grep / ripgrep** | Keep as the exact-token path. Unranked, no snippets unless you add `-C`. Wrong for paraphrase. |
| **`bob query` only** | Keep as the structured path. Cannot express “notes about X in other words.” |
| **OmniSearch HTTP** | Excellent in-Obsidian BM25, including PDFs. Requires the desktop app. Agents on apollo cannot depend on it. Complementary for Bryan-at-the-keyboard. |
| **Smart Connections** | Local embeddings, related-notes sidebar. Index lives in-vault (`.smart-env/`). No agent-grade CLI. Skip for SASE. |
| **Copilot / vault-QA plugins** | Chat UX, often cloud. Wrong threat model and wrong caller. |
| **Obsidian-qmd plugins** (several 2026 ports) | Fine as a later Mac convenience wrapping the same daemon. Do not deploy through `~/bob/.obsidian/plugins` (overwritten / gitignored relative to `bob plugins sync`). |
| **obsidian-mind / wiki-mind** | Already optional-qmd for project memory; `VAULT_QMD_REFRESH=off` exists because detached qmd workers leak. Evidence that “qmd at session start” is operationally fussy. |
| **cyanheads/obsidian-mcp-server** | Needs Local REST API + Obsidian running. Write-capable. Overkill and a mutation risk. |
| **Rust FTS5 inside bob-cli** | Native, no models, would be a good BM25 if qmd were unavailable. Reimplements `qmd search` and still leaves paraphrase unsolved. Not worth it while qmd exists as a host binary. |
| **DIY llama-index / LanceDB** | More glue, less agent UX than qmd. Skip. |
| **Cloud embeddings (OpenAI, Voyage, Jina)** | Better multilingual/quality, new privacy surface. A fork (`pluginmd/qmd`) already adds Jina. Unnecessary at 13 MB if local BM25+embed is good enough. |

qmd wins the *agent + local + markdown* cell. It loses the *structured GTD* cell to bob, and the *in-Obsidian instant search* cell to OmniSearch.

---

## 7. Recommended solution

### Phase 0 — decide the job

qmd is the **conceptual-prose retriever** for agents. It is not the vault database, not the task engine, and not Bryan’s command palette.

Success looks like: an agent asked “what have I written about coupling in ad tech” finds `balance_coupling.md` (or the relevant `ref/` note), fetches the file, and cites lines. Failure looks like: the same agent uses qmd to list Ready tasks, or returns `_generated/queries/zoq/all_read.md` as the top hit.

### Phase 1 — host install and curated index (this week)

On **apollo** (where SASE agents run):

1. Install qmd from git SHA `86d2365` (or newer main), not npm 2.8.3. Node 24 on this host satisfies `engines: >=22`. Record the SHA in chezmoi.
2. Write `~/.config/qmd/index.yml` (chezmoi-managed). Sketch:

```yaml
global_context: >
  Bryan's Bob Obsidian vault. Structured GTD lives in bob commands
  (plan, freshness, ready, query, ref). This index is for prose and
  reference notes. Task checkboxes, Pomodoro ledgers, and Dataview
  dumps are the wrong evidence for conceptual questions.

editor_uri: "obsidian://open?vault=bob&file={path}"

collections:
  knowledge:
    path: /home/bryan/bob
    pattern: "**/*.md"
    includeByDefault: true
    ignore:
      - "_generated/**"
      - "_templates/**"
      - "_zorg_templates/**"
      - "_conflicts/**"
      - "_meta/**"
      - "done/**"
      - "lib/**"
      - "xlib/**"
      - "old_lib/**"
      - "2023/**"
      - "2024/**"
      - "2025/**"
      - "2026/**"
      - "ref/**"          # own collection below
    context:
      "/": "Evergreen area notes, project notes, and untyped knowledge at vault root"
      "/prj": "Finite project notes; each has a ^prj task. Prefer bob projects / bob query for status"
      "/lit": "Literature notes"
      "/prompts": "Prompt library"
  refs:
    path: /home/bryan/bob/ref
    pattern: "**/*.md"
    includeByDefault: true
    context:
      "/": "Highlights-generated reference notes (type:[[ref]], ^ref task). Identity lookups still go through bob ref find"
  dailies:
    path: /home/bryan/bob
    pattern: "{2023,2024,2025,2026}/**/*.md"
    includeByDefault: false
    context:
      "/": "Daily notes and Pomodoro work logs. Search only when the question is about a specific day's work"
```

   Nested `ref/` is ignored in `knowledge` so it is not double-indexed. Dailies are searchable with `-c dailies` and absent from unscoped queries.

3. `qmd update` only. **Do not embed yet.** Confirm `qmd search "coupling" -n 10 --full-path` returns evergreen notes rather than `_generated`.
4. Add a systemd user timer (or a oneshot after `bob-vault-sync.service`) that runs `qmd update`. Stay outside `bob nightly` and outside the vault git lock. Do not set collection `update: git pull`.
5. `QMD_FORCE_CPU=1` on apollo. Leave GPU autodetection for the Mac if Bryan installs it there later.

### Phase 2 — Bob router skill (same week)

A new SASE skill, modeled on `bob_query`, **not** the upstream qmd skill and **not** a CLAUDE.md dump. Suggested name: `bob-vault-search`. Load on demand when the user asks about notes, past writing, or “what did I say about.”

Routing table the skill must teach:

| Question class | Tool |
| --- | --- |
| Tasks, lanes, due, blocked, Ready, Today | `bob plan` / `bob freshness` / `bob ready` / `bob query --tasks` |
| Notes by type, tag, folder, Dataview | `bob query` |
| “Have I read / queued this URL?” | `bob ref find` |
| Exact title, route, block id, rare token | `rg` in `~/bob`, or `qmd search '"exact phrase"'` |
| Paraphrase, “notes about,” “what have I written” | `qmd search` on default collections, then `qmd get --full-path` / Read |
| “What did I work on last Thursday?” | `qmd search -c dailies`, or open `YYYY/YYYYMMDD.md` directly |

Hard rules in the skill:

- Search → get → answer. Snippets are leads.
- Prefer `qmd search` (BM25). Call `qmd query` only after lexical search is empty *and* the question is conceptual. Always pass `--no-rerank` on apollo until a daemon exists.
- Cap concurrency: one qmd process. If hybrid is enabled, talk to `qmd mcp --http` rather than spawning models per agent.
- Cite vault paths, not `#docid`s, so a human can click through in Obsidian.
- Never `qmd collection add/update/embed` unless the user asked for maintenance.
- If `qmd` is missing or the index is empty, fall back to `rg` and say so.

Vault `AGENTS.md` is currently 3 bytes. A one-paragraph pointer to the skill is enough; keep the routing table in the skill so it is audited (`sase skill use`) like `bob_query`.

### Phase 3 — eval, then maybe embed (week two)

Write a 20-query fixture against this vault (`qmd bench` JSON: `expected_files` + `expected_in_top_k`). Mix:

- 10 lexical: route names, unique phrases, `^prj` wording
- 10 paraphrase: “metric-driven goals,” “how I think about ad auctions,” “inbox drain from Google Keep”

Score `bm25` vs `vector` vs `hybrid` vs `full`. Ship embeddings only if paraphrase@5 on `knowledge`+`refs` beats BM25 by enough to justify ~2 GB of models and 4.5 GB RSS. If frontmatter chunks dominate vector (expected, #975), stay on BM25 and revisit after upstream strips YAML from embeddings.

If hybrid wins, start **one** `qmd mcp --http --daemon` under systemd, idle-dispose already exists (5 min). Agents call HTTP `/query` with `rerank: false` unless a single long research turn wants rerank.

### Phase 4 — optional later, in this order

1. **Chezmoi the skill + index.yml** so athena/mac can reproduce, with apollo as the agent index.
2. **Mac OmniSearch or an Obsidian-qmd plugin** for Bryan in the GUI, talking to the same collections if he wants. Deploy from a repo, not by dropping files into `~/bob/.obsidian/plugins`.
3. **Thin `bob notes search`** only if the skill’s argv is stable and wrapping helps completion/help. Subprocess, Vault help section, `-f json`, `-n`, `-c`. Permanent alias if renamed. Still no models inside bob-cli.
4. **Upstream contribution:** strip YAML frontmatter from FTS/embed text (#975). That single change is worth more to Bob than `qmd.metadata` in every note.
5. **Never:** qmd as a Dataview replacement, qmd inside `bob nightly`, git-synced sqlite, `qmd.metadata` frontmatter, indexing PDFs, MCP bound to `0.0.0.0` without auth.

### What I would not do

Integrate qmd into bob-cli in the first PR. Index the whole vault. Tell agents “always qmd.” Run `qmd query` from every SASE turn on apollo. Treat search snippets as answers.

---

## 8. Operational risks to budget for

- **Stale index after capture.** A note written 30 seconds ago will miss until the timer. The skill should say so and fall back to `Read`/`rg` for files just edited.
- **RAM spikes.** Even BM25 is cheap; a mistaken `qmd query` in five parallel researchers is not. The swarm that commissioned this report is exactly that failure mode.
- **Orphan processes** (#1029, #1039). Timeouts must kill the process group, not just the wrapper.
- **npm lag.** Pin a SHA. Recheck #1073 before teaching agents to `npm install -g`.
- **Multi-hop hosts.** Agents in numbered workspaces see `~/bob` on apollo; they should not try to index the ephemeral bob-cli checkout.
- **PDFs.** `xlib/` / `lib/` stay with `bob ref` / Highlights. qmd is markdown-only unless you add a text dump, which this report does not recommend.

---

## 9. Sources

### Primary (this session)

- `sase repo open gh:tobi/qmd` — README, CHANGELOG, `package.json` 2.8.3, `skills/qmd/SKILL.md`, `src/metadata.ts`, `src/store.ts` (`extractTitle`, `DEFAULT_GLOB`), `src/cli/qmd.ts` (ignore dirs, `dot: false`), `src/mcp/server.ts`, `example-index.yml`. HEAD `86d2365` 2026-10-14.
- GitHub issues via `gh`: #975 (frontmatter vectors), #942 (4.5 GB/process), #709 (CPU VPS), #1073 (npm lag), #1053, #987, #1039, #809, plus the 2026-10 performance/metadata stack.
- `gh repo view tobi/qmd` — 30,439 stars, MIT, updated 2026-10-16.
- `npm view @tobilu/qmd` — latest 2.8.3, published 2026-08-16.
- Live vault census of `~/bob` on 2026-10-16: 6,354 md / 13.1 MB; folder and `type:` breakdowns; 643 root notes, 31 with H1, 628 with frontmatter.
- Host: apollo, 16× Xeon 8168, 31 GB RAM, 0 swap, no nvidia-smi, Node v24.15.0, `qmd` not on PATH, empty `~/.config/qmd` and `~/.cache/qmd`.
- bob-cli `README.md` (vault layout, command map), `docs/dataview.md`, `sase/memory/cli_rules.md`, `sase/memory/obsidian.md`, glossary (Capture, Area/Project/Reference notes), `src/native/nightly.rs` (vault-sync → archive → vault-sync only).
- `bob ref find` on `https://github.com/tobi/qmd`, “qmd tobi lutke”, “Query Markup Documents” — all `not_found`.

### Secondary

- [Mandalivia, 2026-02-18, “Semantic Search for Your Obsidian Vault”](https://www.mandalivia.com/obsidian/semantic-search-for-your-obsidian-vault-what-i-tried-and-what-worked/) — grep vs OmniSearch vs qmd on a 2,400-note Zettelkasten; collection+context advice; CLAUDE.md snippet this report refuses to copy verbatim.
- Community Obsidian ports inspired by qmd: [thirteen37/obsidian-qmd](https://github.com/thirteen37/obsidian-qmd), [achekulaev/obsidian-qmd](https://github.com/achekulaev/obsidian-qmd), [GoBeromsu/obsidian-qmd](https://github.com/GoBeromsu/obsidian-qmd).
- [brianpetro/obsidian-smart-connections](https://github.com/brianpetro/obsidian-smart-connections) — in-vault embedding index.
- [scambier/obsidian-omnisearch](https://github.com/scambier/obsidian-omnisearch) — in-app BM25 + optional HTTP, requires Obsidian.
- [breferrari/mindframe#94](https://github.com/breferrari/mindframe/issues/94) / obsidian-mind `VAULT_QMD_REFRESH=off` — qmd-at-session-start worker leaks.

### Library check

Library check: 0 of 3 candidates already in your library (0 finished).

Propose, if you want them in `ref/`:

```bash
bob ref create https://github.com/tobi/qmd
bob ref create https://www.mandalivia.com/obsidian/semantic-search-for-your-obsidian-vault-what-i-tried-and-what-worked/
```

---

## 10. Recommended next actions (for the lead / Bryan)

1. Accept Phase 1–2 as the implementation plan: git-pinned qmd, curated collections, BM25-first router skill, timer refresh on apollo.
2. Reject bob-cli wrapping, vault frontmatter mutation, whole-vault indexing, and unmodified upstream skill install.
3. After BM25 smoke, run the 20-query fixture before enabling `qmd embed` or MCP.
4. Optional: file or upvote [tobi/qmd#975](https://github.com/tobi/qmd/issues/975) (strip YAML from embed/FTS) as the highest-leverage upstream change for this vault.

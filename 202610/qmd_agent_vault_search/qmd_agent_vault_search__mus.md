# qmd for the Bob vault: integration research and recommendation

**Question:** should [qmd](https://github.com/tobi/qmd) be integrated into bob-cli or the
Bob Obsidian vault (e.g. agent instructions to use it when searching the vault), and if so how?

**Verdict up front:** yes as an **opt-in, instructions-only semantic-search layer** for agents —
no as a bob-cli dependency, a vault-sync-coupled component, or a default search path. Start with
a zero-code pilot (global qmd collection over `~/bob` + agent guidance on when to use it), measure
whether it earns its keep, and only then consider a thin optional `bob search` passthrough. Do not
bundle, require, or auto-index it.

Researched against qmd `2.8.3` (README, `example-index.yml`, `skills/qmd/SKILL.md`, CHANGELOG head),
the bob-cli tree (`bob --help`, `bob query --help`, `Cargo.toml`, `docs/`), and the live vault
(`~/bob`: 6,354 `.md` files, ~30 MB of markdown inside a 1.9–3.6 GB vault with attachments).

## 1. What qmd actually is

qmd ("Query Markup Documents") is a **local, on-device hybrid search engine for markdown**, shipped
as a Node.js CLI plus MCP server. The pipeline per query:

1. **Query expansion** — a fine-tuned 1.7B model rewrites the query into typed sub-queries
   (`lex` keywords, `vec` paraphrases, `hyde` hypothetical-answer passages). Its own skill docs
   advise agents to **author these fields themselves** (`intent:` + `lex:`/`vec:`/`hyde:`) rather
   than pasting the user's sentence and hoping the expander guesses right.
2. **BM25 full-text search** (SQLite FTS5) + **vector semantic search** (sqlite-vec embeddings),
   fused with reciprocal rank fusion (RRF).
3. **LLM re-ranking** of the top ~40 candidates.

Three search tiers expose cost/quality trade-offs explicitly:

| Command | Backend | Models needed | Speed |
|---|---|---|---|
| `qmd search` | BM25 only | none | fastest |
| `qmd vsearch` | vectors only | embedding model | medium |
| `qmd query` | full hybrid + rerank | all three models | slowest, best quality |

qmd's own benchmark framing (bm25 ~0.50, vector ~0.70, hybrid/full ~1.00 on its example fixture)
is the honest pitch: hybrid beats either backend alone **on conceptual-recall queries**. It does not
claim to beat `rg` on exact lookup, and it won't.

Agent surfaces are well designed for our use: `--json` / `--files --all --min-score` output,
`qmd get #docid` / `multi-get` retrieval with line numbers, a `status` health tool, an MCP server
(stdio per-client, or shared HTTP daemon with models held in VRAM), and a checked-in agent skill
(`skills/qmd/SKILL.md`, also distributed as a plugin). The documented agent loop — search for
leads, retrieve full sources, answer from retrieved text, never from snippets — is exactly right
for vault work.

## 2. Cost and machine fit

**Model downloads (~2 GB, one time, per machine):** embedding model ~300 MB, reranker ~640 MB,
query-expansion model ~1.1 GB, auto-downloaded from HuggingFace into `~/.cache/qmd/models/`.
Runtime is Node ≥ 22 via `node-llama-cpp` (native build). Apollo (this machine: 16 cores, 31 GB
RAM, Node v24, no Bun) clears the bar; macOS needs Homebrew SQLite for extension support and its
own ~2 GB of models.

**The cost that matters is per-machine, not per-repo.** The index is a local SQLite file (global
`~/.config/qmd/index.yml` + `~/.cache`, or project-local `.qmd/`). It is **not synced by the vault
git sync** — apollo, mac, and athena each need their own collection, models, and update discipline.
That is fine for a pilot, but it rules out any design where "the vault" has one index.

**First-index cost for our vault is modest.** ~30 MB / ~6.4k markdown files is small by qmd
standards (recent changelog work targets 20k-file indexes). Embedding is a one-time batch job;
re-indexes are incremental via a `file_sync_state` table (mtime+size match skips). Two caps to know:
files over 10 MB are skipped, and result bodies are capped at the first 262,144 characters (matches
past that point are still found, but snippets/rerank see the head — irrelevant for vault notes,
worth knowing for long transcripts).

## 3. Fit with the Bob vault specifically

**Where qmd helps:** concept notes, articles/refs, and "I remember reading something about X"
recall — exactly the queries where `rg` fails because the user paraphrases and the source uses
different words. The `context add` feature (per-collection descriptions returned with hits) is a
genuinely good fit for telling Now/Next/Later apart from archives at retrieval time.

**Where it does not help, or misleads:**

- **Tasks are short, structured, and status-derived.** A `- [ ]` line with a block ID, a
  `Depends-On` child line, and ledger-driven status has almost no prose for embeddings to bite on,
  and qmd understands **none** of the semantics: no checkbox state, no Dataview fields, no Tasks
  plugin filters, no `^prj` project blocking, no freshness tiers. Semantic search over the task pool
  will happily surface Done, Blocked, or stale-dated tasks with high confidence. The derived-status
  architecture (ledger + `bob query` + reconcile) stays authoritative; qmd can only propose
  candidates, never answers, for task questions.
- **Obsidian syntax is opaque to it.** Wikilinks, embeds, Dataview inline fields, and Tasks
  emoji/metadata are indexed as literal text. Frontmatter is searchable content, plus an opt-in
  namespaced `qmd.metadata` block for typed filtering (new in unreleased CHANGELOG) — usable, but
  it is a parallel metadata universe to Dataview/Metadata Menu, not an integration with them.
- **Staleness is the sharpest edge.** There is no file watcher. Freshness depends on someone
  running `qmd update` (+ `qmd embed` for new vectors). Agents that just wrote to the vault and
  then search will hit a stale index by default. `rg` and `bob query` are always fresh; qmd never
  is. Any instruction set must make this explicit: qmd is for recall over settled notes, never for
  verifying what just happened or what is true right now.
- **No exclusion config exists yet for vault junk.** `ignore` patterns are YAML-only (no CLI),
  so the pilot must hand-edit `index.yml` to exclude sync/debris paths. Built-ins already exclude
  `node_modules`/`.git`/`.cache`/`dist` but nothing Obsidian-specific.

A spot check grounds the "don't replace exact search" point: `rg -l -g '*.md' "quarterly planning"`
over the full vault returns in ~0.09 s. Keyword lookup is already solved and free. qmd is a recall
supplement, not a search replacement.

## 4. Integration options considered

**A. Agent instructions only (zero code).** Add a vault-search section to agent guidance:
when to reach for qmd (`query` with hand-written `intent:`/`lex:`/`vec:` fields for conceptual
recall over notes/refs/articles) vs `rg` (exact strings, IDs, symbols) vs `bob query` (Dataview/Tasks
semantics, anything status- or date-sensitive). Setup is a documented one-time per-machine recipe
(`qmd collection add ~/bob --name bob`, context lines, ignore patterns, `qmd update && qmd embed`).
No bob-cli changes, no new dependency, trivially reversible.

**B. Thin optional `bob search` passthrough.** A small subcommand that shells out to `qmd` when
present (JSON output, `--full-path`, score threshold flags) and degrades to `rg`/error when absent.
Note `cli_rules.md` reference memory governs new subcommands and must be read before designing one.
This buys discoverability and a stable interface if the backend ever changes, at the cost of owning
a subprocess contract (qmd versions, missing binary, stale index messaging) inside a Rust CLI that
currently has zero Node dependencies.

**C. MCP / HTTP daemon integration.** Running `qmd mcp --http --daemon` for shared long-lived model
residency. Only matters under sustained query load; a handful of agent queries per session does not
justify a daemon, PID file, and port. Defer unless the pilot shows latency pain.

**D. Alternatives (do instead of / alongside):**

- *Status quo (`rg` + `bob query`).* Already covers exact lookup and structured queries. Costs
  nothing. Fails only on paraphrase-recall — the precise gap qmd fills.
- *Obsidian Omnisearch plugin.* Better in-app human search, but agents don't drive the Obsidian UI;
  irrelevant to the agent-search problem. The vault's plugin list has no Omnisearch today.
- *Custom embeddings/RAG inside bob-cli.* Strictly worse: reimplements qmd's BM25+vector+rerank
  stack in Rust for no gain. Never build this while qmd exists.

## 5. Critique of the plan and requirement adjustments

The plan's core instinct is sound — paraphrase-recall is the one vault-search gap, and qmd is the
right-shaped tool for it — but as stated ("integrate qmd into bob or the vault, agents use it when
searching") it overreaches in three ways, each with an adjustment:

1. **"Use qmd when searching" is too broad → narrow to recall-only.** Defaulting all vault search
   to qmd would route exact lookups through a stale, semantics-blind index. Adjusted requirement:
   qmd is the *third* tool, after `rg` (exact) and `bob query` (structured). Instructions must name
   the routing explicitly, including the staleness rule (never use qmd to verify recent writes or
   current status).
2. **"Integrate into bob" presumes code → start with zero code.** A Rust dependency on a Node CLI
   with 2 GB of models inverts the project's dependency posture for unproven benefit. Adjusted
   requirement: the pilot is instructions + per-machine setup only. Option B becomes a follow-up
   gated on measured pilot usage.
3. **One vault, one index is assumed → plan per-machine.** The index is local state, outside git
   sync. Adjusted requirement: setup, update discipline, and trust decisions are per host (apollo /
   mac / athena), and vault-sync/nightly must **not** gain index hooks (a failing or slow embed
   must never block sync; `qmd update`'s abort-the-whole-run on hook failure is the wrong failure
   mode to couple to nightly maintenance).

Also explicit non-goals: no checked-in `.qmd/` project-local index in `~/bob` (would drag trust
prompts and local paths into the synced vault; qmd gates exactly these fields for agents), no
`qmd.metadata` frontmatter campaign (parallel metadata universe; adopt only if filtering proves
needed), no daemon/MCP in the pilot.

## 6. Recommended solution

**Phase 0 — pilot, instructions only (do this now):**

1. On apollo: `npm install -g @tobilu/qmd`, `qmd collection add ~/bob --name bob`, add context
   lines (daily notes vs concept notes vs refs/articles vs archives), hand-edit `index.yml`
   `ignore` for debris paths, then `qmd update && qmd embed`.
2. Add a short vault-search routing section to agent instructions: `rg` for exact strings/IDs,
   `bob query` for Dataview/Tasks/status/date questions, `qmd query` (hand-written
   `intent:`+`lex:`/`vec:`, then `get`/`multi-get` full sources, cite paths+docids) for
   conceptual recall over settled notes. Include the staleness rule and the
   snippets-are-leads-only rule, mirroring qmd's own skill.
3. Use it for a few weeks. Keep the only metric that matters: did `qmd query` find settled-note
   answers that `rg` missed, and did any agent act on a stale or status-blind hit? The second
   half decides whether the instructions are sufficient.

**Phase 1 — only if the pilot earns it:** a thin optional `bob search` passthrough (read
`cli_rules.md` first), shelling out to qmd when installed, degrading cleanly when absent or stale,
with `--json` suitable for agents. Still no bundling, no sync hooks, no daemon.

**Never:** embedding qmd into the Rust binary, indexing inside `vault-sync`/`nightly`, a shared
vault-level index, or defaulting any status-sensitive query path to semantic search.

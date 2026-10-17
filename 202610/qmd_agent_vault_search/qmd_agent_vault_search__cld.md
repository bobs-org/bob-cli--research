# qmd for the Bob vault: should agents search `~/bob` with it, and how?

*Researcher: cld · 2026-10-16 · qmd 2.8.3 (npm) / upstream `main` at `86d2365` · measured on apollo*

## TL;DR

- **qmd works on this vault, but its headline features don't fit the hosts where agents run.** On apollo (16 vCPU, no GPU, shared with other agents):
  - **BM25** search is instant: 0.3 s per query, and the index builds in 22 s.
  - **Hybrid BM25 + vector without reranking** is usable: about 7–9 s per CLI call, or about 1.1 s through a warm HTTP daemon.
  - **LLM reranking** took 2.5–8 minutes per query, and the **default `qmd query` with expansion plus reranking** took 4–13 minutes. Neither ranked better than plain hybrid.
  - **Building the vector index** for the whole vault took about 3.8 hours of wall-clock time.
- **The measured benefit is real but modest.** On 10 hand-labelled questions:
  - Structured hybrid search (no rerank) put a correct note in the top 10 for 8/10 questions on the first try (MRR 0.73), using only general wording. One-shot `rg` managed 6/10 (MRR 0.60), and qmd's own BM25 managed 5/10.
  - With a second, obvious keyword (`guice`, `rotten`, `vet`), `rg` found every target at 0.02 s per try.
  - Hybrid search really wins on loosely phrased, list-like questions ("which fantasy series…", "what tools did I use before Obsidian…").
  - It loses on Bob jargon (ROTTEN, freshness, lanes). There, a vault map or glossary helps more than embeddings do.
- **Verdict: a good idea as a small, limited tier; a bad idea as a big integration.** The most valuable part costs no infrastructure: a Bob-owned `bob_search` skill that gives agents a **vault map**, sends questions to the right tool (`bob query` / `bob ref` / `rg`), and adds qmd only as a "concept search" fallback.
- **Recommendation (details in the last section):**
  - Ship the skill.
  - Pilot qmd behind a small wrapper. It always uses structured queries with `--no-rerank` and never runs query expansion. It embeds curated notes only, keeps daily notes keyword-only, and gets its index updated by a timer.
  - Skip the MCP server for now.
  - Decide after 2–3 weeks, from actual usage, whether to graduate the wrapper into a `bob search` subcommand or drop qmd.

---

## 1. What qmd is (as of 2.8.3)

qmd ("Query Markup Documents", Tobi Lütke, MIT) is a Node/Bun CLI, SDK, and MCP server that indexes markdown into a single SQLite file (`~/.cache/qmd/index.sqlite`):

| Layer | Implementation | Models (auto-downloaded GGUF via node-llama-cpp) |
|---|---|---|
| Lexical | SQLite FTS5 BM25; terms are **AND-ed**, prefix-matched; `"phrase"` and `-neg` supported | none |
| Vector | sqlite-vec; ~900-token markdown-aware chunks, 15% overlap | `embeddinggemma-300M-Q8_0` (334 MB) |
| Query expansion | Fine-tuned 1.7B model generates `lex`/`vec`/`hyde` variants for untyped queries | `qmd-query-expansion-1.7B-q4_k_m` (1.3 GB) |
| Rerank | Qwen3 reranker 0.6B on top 40 RRF candidates, position-aware blend | `qwen3-reranker-0.6b-q8_0` (639 MB) |

Agent-relevant surfaces:

- **Search modes:** `qmd search` (BM25 only), `qmd vsearch` (vector, but it *also* runs expansion), `qmd query` (full pipeline).
- **Structured queries:** a multi-line query document (`intent:` / `lex:` / `vec:` / `hyde:`) **skips expansion**.
- **Reading:** `qmd get` / `multi-get`, with line-numbered output, `#docid`s, and `path:from:count` slicing.
- **Output:** `--format json|files|md`.
- **Context strings:** `qmd context add` attaches a description per path prefix, which is returned with every hit.
- **Metadata filters:** `--filter` works **only on a `qmd.metadata` frontmatter namespace**, so Bob's `type: "[[ref]]"` / `parent:` / tags are *not* filterable.
- **MCP:** stdio or `--http --daemon` (localhost:8181, unauthenticated, with Origin/Host checks), exposing `query`, `get`, `multi_get`, `status`, `metadata`.
- **Claude Code plugin:** `claude plugin install qmd@qmd` installs the MCP server **plus** a `qmd` skill **plus** an unrelated `release` skill.

qmd's own `CLAUDE.md` and skill tell agents never to run `collection add` / `update` / `embed` themselves, and to write structured queries rather than bare `qmd query "…"`. Both rules matter here.

## 2. The environment qmd would join

- **Vault:** `~/bob`, 6,354 `.md` files, 13.7 MB (2.2 KB average). Composition from the qmd index:

  | Area | Docs | Share of vector chunks |
  |---|---|---|
  | Daily notes `20YY/` | 3,014 | **59.7%** |
  | Root notes (areas, topics, projects) | 634 | 17.7% |
  | `ref/` (incl. `ref/chat` SASE reports, `ref/zorg`) | 1,043 | 11.0% |
  | `done/` (archived tasks) | 29 | 4.0% (a few huge files) |
  | `lit/`, `lib/`, `prj/`, `eat/`, `prompts/`, … | remainder | ~7% |

- **Noise directories an index must exclude:**
  - `_generated/` (1,131 rendered query pages; the largest is 456 KB).
  - `lib/**` (Highlights sidecar `.md` files that **duplicate** `ref/` notes; in testing, `lib/` files took top-3 slots in 4 of 10 questions).
  - `_conflicts/`, `_meta/`, `_templates/`.
  - `lit_review/` and `xlib/` are gitignored and present only on some hosts.
- **Note style:**
  - Notes are dense with wikilinks, block IDs, and inline fields.
  - Many zorg-converted notes carry 8–10 lines of conversion frontmatter (paths, SHA-256). qmd indexes and embeds frontmatter as ordinary text (upstream issue #975).
  - Daily notes are mostly structure: the Pomodoro ledger, Task Links, and short logs.
- **Hosts:**
  - Agents mostly run on **apollo** and **athena**, which are headless Linux machines with no GPU and no Obsidian app.
  - The MacBook has Obsidian.
  - The vault syncs through git (`bob vault-sync`, roughly every few minutes; about 260 commits a day). Each host would need its own qmd index.
- **Existing agent tooling:**
  - The `bob_query` skill (Dataview/Tasks over the vault, native and headless).
  - The `bob_ref` skill (reading library: find/list/show).
  - Plain `rg`/`grep`.
  - Skills are written once in chezmoi `home/sase/skills/<name>.md` and copied out to Claude, Codex, Gemini, Qwen, Grok, Muse, and OpenCode; `sase skill use` records each use.
  - There is no "find a note about X" skill today.
- **Churn:** in the last 24 h, 64 markdown files (321 KB) changed; in the last 7 days, 266 (967 KB). The hot files are today's daily note, `sase.md` (118 KB, about 35 chunks), and `dash.md`.

This rules out every option that needs the Obsidian app on the server (Obsidian CLI `search`, Omnisearch HTTP API, the Local-REST-API MCP servers). Whatever agents use must run headless on CPU.

## 3. What I measured on apollo

**Method.**

- qmd 2.8.3 was installed into a throwaway npm prefix with isolated `XDG_CACHE_HOME` / `XDG_CONFIG_HOME`.
- It indexed a read-only **snapshot copy** of the vault's markdown (`_generated`, `_conflicts`, `_meta`, and templates ignored). Nothing touched `~/bob` or your real `~/.config` / `~/.cache`.
- Everything, including the copy and the 2.3 GB of models, was deleted afterwards.
- apollo was running other agents throughout (load average 5–9), so the model-heavy timings are pessimistic. A single run at lower load was about 100 s for structured query plus rerank, still unusable.

### 3.1 Cost

| Operation | Measured |
|---|---|
| `qmd update` (first index, 5,192 docs) | **22 s**, 345 MB RSS |
| `qmd update` (no changes) | **1.4 s** |
| Index size | 34 MB lexical, **71 MB** with vectors |
| `qmd embed`, whole vault (10,259 chunks) | **~3 h 50 min wall**, ~560% CPU, 1.3–1.7 GB RSS, about 0.75–0.85 chunks/s. The first run **stopped at qmd's default 30-min session cap** ("Session expired — skipping remaining…", yet it printed "✓ Done!"); you need `--timeout 0` or repeated runs. |
| `qmd embed`, curated notes only (projected: no daily notes, `done/`, or `lib/`) | ~3,550 chunks, **~70 min** one-time per host |
| Daily re-embed churn (projected) | minutes of CPU per day if embedding hourly, dominated by `sase.md` / `dash.md` edits |
| Model downloads | 334 MB if you only ever embed; 2.3 GB once reranking or expansion is used |

### 3.2 Latency per search

| Mode | Command shape | apollo wall time | RSS |
|---|---|---|---|
| ripgrep | `rg -c -i -e … --glob …` | **0.02–0.03 s** | — |
| qmd BM25 | `qmd search "…"` | **0.3–0.4 s** | ~76 MB |
| qmd structured, lex only | `qmd query $'lex: …' --no-rerank` | 0.4 s | ~76 MB |
| qmd vector (`vsearch`) | runs expansion too | 10.9 s warm, 145 s cold | 0.8–3 GB |
| **qmd structured hybrid, no rerank** (CLI) | `qmd query $'intent:…\nlex:…\nvec:…' --no-rerank` | **7.1–8.9 s** (mostly loading the model on every call) | ~740 MB |
| same, via warm HTTP daemon | `POST /query {"rerank":false}` | **~1.15 s** | daemon 2.6 GB after the reranker loaded |
| structured hybrid **+ rerank** | `qmd query $'…'` | **148–470 s** (one run with `candidateLimit:10` took 56 s) | 2.6 GB |
| **bare `qmd query "question"`** (the default) | expansion + rerank | **238–770 s** | 2.7–3 GB |

Many agent harnesses time out a tool call after about 2 minutes, so **an agent's natural first try (`qmd query "…"`) would time out every time on apollo.** qmd has no config or environment switch to make `--no-rerank` the default (checked in `src/`), so the only ways to enforce it are a wrapper or the instructions.

### 3.3 Quality: a 10-question first-try test

I wrote 10 realistic "find it in my notes" questions with hand-labelled target notes (appendix A). The modes compared:

- **rg:** one naive pattern, files sorted by match count.
- **bm25:** `qmd search` with naive keywords.
- **hyb:** a structured `intent`/`lex`/`vec` query, `--no-rerank`.
- **hyb_rr:** the same query with reranking.
- **bare:** the question pasted into `qmd query`.

The metric is the rank of the first target note in the top 10.

| Q | rg | bm25 | hyb | hyb (generic terms only)† | hyb_rr | bare |
|---|---|---|---|---|---|---|
| Q1 Obsidian Sync → git | 1 | 1 | 1 | 1 | 1 | 1 |
| Q2 longevity / healthspan | 1 | – | 1 | 1 | 1 | 1 |
| Q3 fantasy series (6 targets) | 1 (1/6 found) | – | 1 (4/6) | 1 | 1 (5/6) | 1 (4/6) |
| Q4 dog's vet visits | – | 1 | 3 | 3 | 7 | 3 |
| Q5 dependency-injection notes | – | 1 | 3 | **–** | 4 | 4 |
| Q6 handling stale backlog tasks | – | – | 2 | **–** | 2 | – |
| Q7 how to read books | – | – | 1 | 1 | 1 | 1 |
| Q8 note tools before Obsidian (8 targets) | 1 (3/8) | – | 1 | 1 | 1 (3/8) | – |
| Q9 athena CPU saturation | 1 | 1 | 1 | 1 | n/a‡ | n/a‡ |
| Q10 Coinbase application | 1 | 1 | 1 | 1 | n/a‡ | n/a‡ |
| **Found / MRR** | 6/10 · 0.60 | 5/10 · 0.50 | 10/10 · 0.82 | **8/10 · 0.73** | 8/8 · 0.74 | 6/8 · 0.57 |

† My first structured queries for Q5/Q6 contained vault-insider words (`lex: guice`, `lex: rotten`). With only general wording, hybrid search **misses both**. With those same insider words, a second `rg` try finds them at rank 1 (`guice.md`) and rank 3 (`rotten.md`). The `hyb` column with insider words therefore flatters qmd; the "generic terms only" column is the fair comparison.
‡ The 2-hour budget ran out before the slow modes reached Q9/Q10.

What the numbers say:

1. **Reranking and expansion add nothing here.** Reranking moved targets *down* (Q4: 3 → 7, Q5: 3 → 4) and gave a marginal recall gain (23 vs 21 target hits in the top 10 across Q1–Q8). Expansion was clearly worse (MRR 0.57) and missed Q6 and Q8, which confirms qmd's own advice to write the structured fields yourself.
2. **Hybrid search really helps with list-like recall and natural wording.** Q3 found 4–5 of 6 fantasy-series notes vs 1 of 6 for `rg fantasy`; Q8 found the right hub note (`zorg_alt_tools.md`) first. These are the questions where "I don't know which word Bryan used" is the bottleneck.
3. **Vault jargon beats embeddings.** For Bob-specific concepts (ROTTEN, freshness, lanes, Task Links), neither BM25 nor vectors bridge from "stale backlog tasks" to `rotten.md`. An agent that knows the vocabulary finds it with `rg` immediately. So a **vault map and glossary pointer in the skill** is the highest-leverage piece.
4. **qmd BM25 is a weak default for agents**, because every word is AND-ed. Plausible keyword lists return nothing, e.g. `"Obsidian Sync" retire git vault-sync` → 0 hits, and `longevity healthspan` → 0 hits. Agents must keep each `lex:` line to 1–3 words and use several lines.
5. **Exclude `lib/**`.** Highlights sidecars and `lib/docs` copies took top-3 slots in 4 of 10 questions (Q1, Q6, Q8, Q10). In Q1 the sidecar outranked its own twin note.

Caveats: small N, my own labels, single runs, and first-try proxies. A real agent iterates, which narrows the gap further toward `rg`. Treat this as directional evidence, not a benchmark.

## 4. qmd risks specific to this setup

From the source and upstream issues, fetched 2026-10-16. Most issues have no maintainer reply, so read them as user reports.

- **CPU-only cost.** Independent reports match what I measured:
  - A 4 vCPU AWS box took 3m38s per `qmd query`.
  - A 16 GB no-GPU machine used 4.5 GB RSS per query, and four concurrent queries took 46 s – 4 min.
  - A CPU ThinkPad's full path did not finish within 55 s.

  ([openclaw#8786](https://github.com/openclaw/openclaw/issues/8786), [qmd#942](https://github.com/tobi/qmd/issues/942), [qmd#683](https://github.com/tobi/qmd/issues/683))
- **Concurrency under a SASE swarm.**
  - Each CLI process loads its own models; there is no cross-process sharing. Five researchers each running a reranked query would need roughly 13–22 GB on a 31 GB host.
  - A concurrent `search` during an `update` can crash with `SQLITE_SCHEMA`; this is open ([#925](https://github.com/tobi/qmd/issues/925)).
  - `embed` does take a process lock (`src/cli/embed-lock.ts`).
- **Silent correctness bugs.**
  - Garbage vectors at the 512-token batch boundary, reportedly worst on **wikilink-dense text**; the fix is unmerged and would need a full re-embed ([#897](https://github.com/tobi/qmd/issues/897)).
  - `embed` can fail partway through and still exit 0 ([#935](https://github.com/tobi/qmd/issues/935)).
  - When the reranker fails, it returns 0.5 for everything and caches those scores ([#1053](https://github.com/tobi/qmd/issues/1053)).
  - Frontmatter can outrank body text ([#975](https://github.com/tobi/qmd/issues/975)).
- **MCP daemon stability.** Models are disposed while still in use and segfault ([#947](https://github.com/tobi/qmd/issues/947)); vector queries segfault under MCP even though the CLI works ([#938](https://github.com/tobi/qmd/issues/938)); OOM by joining document bodies ([#987](https://github.com/tobi/qmd/issues/987)).
- **Upgrade churn.**
  - Releases come in bursts (2.0 in March … 2.8.3 in August, none since), and npm lags `main`.
  - `main` already contains a **one-way vector-table repartition** (PR [#1024](https://github.com/tobi/qmd/pull/1024)). Rolling back needs `embed -f`, which would mean hours of re-embedding on each host. Pin the version.
  - Over 100 PRs are open, and contributors note "no maintainer has reviewed the PRs yet" ([#1013](https://github.com/tobi/qmd/issues/1013)).
  - This is a popular personal tool (about 30k stars), not a product with a support promise.
- **Security.**
  - Retrieved notes put clipped web text (highlights, Keep imports) into agent context. That is a prompt-injection channel ([skills.sh audit](https://www.skills.sh/breferrari/obsidian-mind/qmd/security/agent-trust-hub)), but only slightly more exposure than agents reading the files directly.
  - The HTTP daemon is unauthenticated; 2.8.3 added Origin/Host screening ([#881](https://github.com/tobi/qmd/issues/881)). Don't bind it to the tailnet without a proxy in front.
- **Fragile CPU builds.** node-llama-cpp has CPU and cgroup quirks ([#919](https://github.com/tobi/qmd/issues/919), [#763](https://github.com/tobi/qmd/issues/763)). apollo has AVX2/AVX-512, so it is fine.
- **Not a structure engine.** qmd knows nothing about tasks, statuses, lanes, `^prj`/`^ref`, or Dataview fields, and `--filter` cannot see Bob frontmatter. Structured questions still belong to `bob query`.
- **PDFs are not indexed.** The full text of references in `lib/` is not covered; only ref-note highlights and annotations are.

## 5. Critique: is this a good idea?

**What's right about it.**

- Agents do currently search your vault without any guidance: no map, no exclusions, no routing to `bob query` / `bob ref`.
- qmd is local, private, markdown-native, has a clean JSON CLI, and its structured `intent/lex/vec/hyde` format is a good fit for LLM-written queries.
- BM25 plus vectors without reranking gave a measurable first-try improvement on loosely phrased questions.

**What's wrong with "integrate qmd" as the goal.**

1. **It solves the smaller problem first.**
   - The vault is only 14 MB, and `rg` scans it in 20 ms with no index to go stale.
   - The literature points the same way. Anthropic dropped a vector index from Claude Code because agentic grep "outperformed everything. By a lot" ([Latent Space](https://www.latent.space/p/claude-code)), though by their own "internal vibes" rather than a benchmark. Plain grep beat vectors in all 10 inline-delivery pairings on a notes-and-memory benchmark ([arXiv 2605.15184](https://arxiv.org/html/2605.15184v1)), while vectors led in 5 of 10 file-delivery pairings, a reminder that how results are delivered matters as much as the retriever. Vendor-reported semantic gains come mainly from large codebases and models trained with the tool ([Cursor](https://cursor.com/blog/semsearch)).
   - My Q5/Q6 results match: **knowing Bob's vocabulary mattered more than meaning-based retrieval.**
2. **qmd's best features are built for Apple Silicon GPUs**, but agents here run on CPU servers, where reranking and expansion are 100–1000× too slow. Without them, qmd is "BM25 with AND semantics + a 300M embedder", which is useful but not the qmd from the README.
3. **Adopting qmd's own plugin and skill would teach agents the wrong default** for these hosts. That skill says to use `qmd query`, which reranks by default; on apollo, this is a 4–13 minute call. It would also add an MCP server and an unrelated `release` skill to every session.
4. **qmd ignores the vault's real value: its structure.** Questions like "what's blocked on X", "what did I do on Tuesday", or "what's in my reading queue" are Dataview/Tasks questions (`bob query`) or library questions (`bob ref`). A search skill that doesn't route those away will produce confident, worse answers.
5. **Each host would carry ongoing operational cost:** a 70-minute to 4-hour first embed, timers, pinned Node packages, a 70 MB SQLite index that git sync can't share, and upstream churn that can force re-embeds.

**Would I take a different approach?** Yes, in emphasis and order:

1. Lead with a Bob-owned skill that adds no infrastructure: a vault map, glossary pointers, routing, and `rg` recipes.
2. Add qmd as a limited, opt-in concept-search tier.
3. Only build a `bob search` command if usage proves the tier is worth it.

I would **not** start with the MCP server, the upstream plugin, a bob-native embedding engine, or any reranking on Linux.

## 6. Alternatives considered

| Option | Headless on apollo? | Semantic? | Fit / verdict |
|---|---|---|---|
| **`rg` + a good skill (vault map, routing)** | yes | no | **Best value; do this regardless.** Instant, always fresh, nothing to run. Weak on vocabulary gaps. |
| **qmd, CLI, limited (BM25 + vector, no rerank)** | yes | yes | **Recommended tier to pilot.** About 7–9 s per call; one-time embed per host. |
| qmd MCP HTTP daemon | yes | yes | ~1.1 s warm, but 2.6 GB resident, open segfault/disposal bugs, MCP setup for 7 CLIs, and an unauthenticated port. Revisit only if the pilot shows agents call it often. |
| qmd full pipeline (rerank / expansion) | technically | yes | **Reject on Linux** (2.5–13 min per query). Possibly fine on the Mac, but agents don't run there. |
| Obsidian CLI `search`, Omnisearch API, Local-REST MCP servers | **no** (need the running app) | partly | Not viable where agents run. |
| Smart Connections (+ third-party MCP) | read-only, if `.smart-env` is synced | yes | Embeddings are produced only in desktop Obsidian, so freshness would depend on the Mac; evidence is weak. |
| basic-memory | yes (Python, FastEmbed CPU, watcher) | yes | Brings its own note conventions and writes tools; a poor match for a vault Bob owns. Test on a copy only if qmd disappoints. |
| Khoj | server (Postgres + pgvector) | yes | Too heavy for this need. |
| ck / semtools / `llm embed` / sqlite-vec DIY | yes | yes (lighter) | Interesting lighter CPU options; less proven on prose. Keep as fallback ideas for a future bob-native backend. |
| **bob-native `bob search` (FTS5 + optional light embedder)** | yes | optional | The right *long-term* home if search proves valuable (Bob already owns vault semantics, Dataview, and ref identity), but premature now. |

## 7. Requirement adjustments (my changes, called out)

- **A1 · Reframe the goal.**
  - *From:* "integrate qmd into bob / tell agents to use qmd."
  - *To:* "give agents a reliable, cheap way to find the right vault notes, then read and cite them."
  - qmd becomes one backend tier, not the interface.
- **A2 · A Bob-owned contract, not qmd's plugin.** Agents should see a `bob_search` skill (chezmoi `home/sase/skills/`, copied out to all providers like `bob_query` / `bob_ref`). Later, possibly, they see a `bob search` command. Don't install qmd's Claude plugin or skill.
- **A3 · No LLM reranking or query expansion on apollo/athena.** This is a hard rule, enforced by a wrapper rather than by instructions alone.
- **A4 · Curate what gets embedded.**
  - Embed root, `prj/`, `ref/`, `lit/`, `eat/`, `prompts/`, and `podcasts/`.
  - Keep daily notes and `done/` keyword-only (60% of chunks, little meaning-based value).
  - Exclude `_generated/`, `lib/`, `_conflicts/`, `_meta/`, and templates entirely.
- **A5 · Agents stay read-only.** Agents never run `qmd collection|update|embed|cleanup`; a timer owns index upkeep (qmd's own guidance says the same).
- **A6 · Route structure and library questions away from text search:** tasks, statuses, dates, and note types go to `bob query`; reading history and annotations go to `bob ref`.
- **A7 · Pilot with exit criteria** instead of a permanent integration, and seed a `qmd bench` fixture from appendix A.
- **A8 · Out of scope:** PDF full text, human-facing search in Obsidian on the Mac, and sharing one index across hosts.

## 8. Recommended solution

### Phase 0: ship now, no new infrastructure

Add `home/sase/skills/bob_search.md` in chezmoi (`skill: true`). It copies out to every agent CLI and is audited by `sase skill use`. Its content should cover:

1. **Routing.**
   - Tasks, statuses, lanes, dates, and note types → the `bob_query` skill.
   - "Have I read / what did I think of …" → the `bob_ref` skill.
   - Everything else → text search below.
2. **Vault map:**
   - Root `*.md` holds area, topic, and project notes (`type:` frontmatter); `prj/` holds project notes.
   - `ref/` holds reference notes: `ref/chat` is SASE research reports and `ref/zorg` is the legacy library.
   - `lit/` holds converted literature notes.
   - `20YY/YYYYMMDD.md` are daily Pomodoro ledgers and logs.
   - `done/*_done.md` hold archived tasks.
   - **Skip** `_generated/`, `lib/` (duplicate Highlights sidecars), `_conflicts/`, and `_meta/`.
   - Point to the glossary terms (ROTTEN/NEW/PENDING/NEXT/READY/TICKLER, Task Link, `^prj`/`^ref`) so agents search with Bob's own words.
3. **Lexical recipe:**

   ```bash
   rg -n -i -e '<term>' -e '<alt>' --glob '*.md' --glob '!{_generated,_conflicts,_meta,lib}/**' ~/bob
   ```

   For filenames, use `rg --files ~/bob | rg -i '<term>'`. Try synonyms and Bob jargon before giving up.
4. **Read before claiming.** Cite vault-relative paths plus line numbers or block IDs. Read-only; never edit `~/bob` from this skill.

This step alone captures most of the measured value, because the Q5/Q6-style misses come from not knowing the vocabulary.

### Phase 1: pilot qmd as the "concept search" tier (apollo + athena)

- **Install** a pinned version: `npm i -g @tobilu/qmd@2.8.3`, managed by chezmoi. Note that systemd units need the absolute nvm path.
- **Config** in chezmoi `~/.config/qmd/index.yml`, templated per host:

  ```yaml
  global_context: "Bryan Bugyi's Bob Obsidian vault: GTD area/project notes, reference notes, daily Pomodoro ledgers."
  collections:
    bob:                       # embedded
      path: /home/bryan/bob
      pattern: "**/*.md"
      ignore: ["_generated/**", "_conflicts/**", "_meta/**", "_templates/**", "_zorg_templates/**",
               "lib/**", "xlib/**", "lit_review/**", "20*/**", "done/**", ".trash/**"]
      context:
        "/": "Area, topic and project notes (type: frontmatter)"
        "/ref": "Reference notes; ref/chat holds SASE research reports"
        "/prj": "Project notes"
        "/lit": "Literature notes converted from zorg"
    bob-log:                   # BM25 only, never embedded
      path: /home/bryan/bob
      pattern: "20*/**/*.md,done/**/*.md"
      context:
        "/": "Daily notes (Pomodoro ledger and logs) and archived closed tasks"
  ```

- **Upkeep.** Run a systemd user timer every 15–60 min, at `Nice=19` and `IOSchedulingClass=idle`:
  - `flock $XDG_RUNTIME_DIR/bob-vault-search.lock qmd update` (about 1–2 s; the lock avoids the `SQLITE_SCHEMA` race with searches).
  - Then `qmd embed -c bob --timeout 0`.
  - Run the first embed (about 70 min) overnight on each host.
- **Agent wrapper.** A ~20-line `bob-vault-search` script in chezmoi; this is the only qmd entry point the skill documents:
  - `bob-vault-search lex <words>` → `qmd search` (cheap; no lock).
  - `bob-vault-search concept` reads typed `intent:` / `lex:` / `vec:` / `hyde:` lines on stdin. It **rejects untyped input**, so expansion never runs, and runs `qmd query --no-rerank -n 10` under `flock -w 60`, `timeout 60`, and `nice`.
  - `bob-vault-search get <path|#docid>[:from:count]` → `qmd get`.
  - Output uses vault-relative paths: strip `qmd://bob/` and `qmd://bob-log/`.
- **Skill addition** (the `bob_search` skill from Phase 0):
  - For vague or list-like questions, use `concept` with 1–3-word `lex:` lines, because terms within a line are AND-ed. Write several lines, plus a `vec:` paraphrase.
  - If the wrapper is missing, fall back to `rg`.
  - Never call `qmd query` or `qmd vsearch` directly, and never rerank.
- **Measurement:**
  - Turn appendix A into a `qmd bench` fixture.
  - Log wrapper calls (one line each to `~/.local/state/bob-vault-search/calls.jsonl`).
  - After 2–3 weeks, read some transcripts.

### Phase 2: decide on the evidence

- **If agents use `concept` regularly and it finds notes that `rg` didn't:** graduate the wrapper into **`bob search`** in bob-cli.
  - Shape: `bob search [TERMS] [--concept …] [--type area|project|ref|day|done] [--since DATE] [-n N] [-f human|json|paths|markdown]`, with a JSON envelope like `bob ref`.
  - Backend: qmd's JSON output, with an `rg` fallback.
  - bob takes over the exclusions, note-type mapping from frontmatter, `ref`/`lib` dedup, wikilink targets, the CPU-safe policy (e.g. `search.rerank: never` in `config.yml`), locking, and calling the index upkeep from `bob vault-sync` / `bob nightly`. That keeps vault semantics in bob and makes qmd a replaceable engine.
  - Read `cli_rules.md` before adding the subcommand.
- **If usage is rare or `rg` keeps up:** remove qmd and the timer, and keep the Phase 0 skill.
- **Revisit the MCP daemon** only if `concept` latency (7–9 s) visibly hurts agent loops. **Revisit reranking** only on GPU or Apple Silicon hosts.
- **Consider a bob-native backend** (FTS5 plus a light CPU embedder) only if qmd churn or bugs (#897, #925, the repartition) start costing re-embeds or incidents.

**Bottom line:**

- Yes to qmd, but only as a limited, wrapper-gated, curated-corpus tier behind a Bob-owned skill. Its value is first-try recall on vaguely worded questions; it is not a replacement for `rg`, `bob query`, or `bob ref`.
- The vault map in the skill is the part I'm most confident about, and it should ship first.

---

## Appendix A. Evaluation questions (seed for a `qmd bench` fixture)

| ID | Question | Target notes (any counts) | Naive `rg` / BM25 keywords |
|---|---|---|---|
| Q1 | Why was Obsidian Sync retired in favor of git sync? | `ref/chat/obsidian_vault_git_sync.md`, `ref/chat/obsidian_sync_footprint_audit_bob-cli-1l.md` | `obsidian sync` / `obsidian sync git` |
| Q2 | What notes do I have on living longer / healthspan? | `outlive.md`, `ref/zorg/outlive/outlive_ref.md`, `body.md`, `lit/uptime.md` | `longevity`, `healthspan` |
| Q3 | Which fantasy series am I reading or planning to read? | `stormlight.md`, `bloodsworn.md`, `the_first_law.md`, `crescent_city.md`, `earth_and_blood.md`, `maybe_book.md` | `fantasy` / `fantasy series` |
| Q4 | When was the dog's last vet visit? | `vet_log.md`, `dog.md` | `vet visit` |
| Q5 | Notes about dependency-injection problems at work | `guice.md`, `debug_java.md`, `lit/guice_modules.md`, `lit/drx_ks_guice_modules.md` | `dependency injection` |
| Q6 | How did I decide to handle tasks that sit in the backlog too long? | `rotten.md`, `ref/chat/{ready_task_freshness_review,rotten_keep_streak_and_approved_decay,freshness_auto_decay_check,bob_cli_31_task_freshness_epic,freshness_gated_ready_dash}.md` | `stale task` / `stale tasks backlog` |
| Q7 | Advice on how to read books effectively | `how_to_read_a_book.md`, `ref/zorg/how_to_read_a_book/how_to_read_a_book_ref.md` | `read books` / `read books effectively` |
| Q8 | What note-taking tools did I use before Obsidian? | `zorg_alt_tools.md`, `zorg.md`, `neorg.md`, `org_mode.md`, `logseq.md`, `joplin.md`, `roam.md`, `zettlr_ref.md` | `note taking` / `note taking app` |
| Q9 | Why was athena's CPU pegged? | `ref/chat/athena_cpu_saturation_orphaned_load_loops.md` | `athena.*cpu` / `athena cpu load` |
| Q10 | Did I apply to Coinbase? | `done/job_2026_apply_29_done.md`, `job_2026_apply_29.md`, `2026/20261015.md` | `coinbase` |

## Appendix B. Sources

**Primary (read locally)**
- qmd checkout `86d2365` (opened via `sase repo open gh:tobi/qmd`): `README.md`, `CLAUDE.md`, `skills/qmd/SKILL.md`, `docs/SYNTAX.md`, `CHANGELOG.md`, `.claude-plugin/marketplace.json`, `src/store.ts` (`buildFTS5Query` joins terms with `AND`; `DEFAULT_EMBED_MAX_DURATION_MS` = 30 min), `src/llm.ts`, `src/cli/qmd.ts`, and `src/cli/embed-lock.ts`.
- Vault: `~/bob` layout, `.gitignore`, and `AGENTS.md`; chezmoi `home/sase/skills/{bob_query,bob_ref}.md`; bob-cli `README.md` and `bob --help`.

**Upstream issue tracker** (fetched 2026-10-16 by a research helper; most issues are user reports without maintainer confirmation):
- CPU cost and concurrency: [#942](https://github.com/tobi/qmd/issues/942), [#683](https://github.com/tobi/qmd/issues/683), [#925](https://github.com/tobi/qmd/issues/925)
- Vector correctness and embed failures: [#897](https://github.com/tobi/qmd/issues/897), [#935](https://github.com/tobi/qmd/issues/935), [#1053](https://github.com/tobi/qmd/issues/1053), [#975](https://github.com/tobi/qmd/issues/975)
- MCP daemon stability: [#947](https://github.com/tobi/qmd/issues/947), [#938](https://github.com/tobi/qmd/issues/938), [#987](https://github.com/tobi/qmd/issues/987)
- Security: [#881](https://github.com/tobi/qmd/issues/881)
- CPU builds: [#919](https://github.com/tobi/qmd/issues/919), [#763](https://github.com/tobi/qmd/issues/763)
- Maintenance and upgrades: [#1013](https://github.com/tobi/qmd/issues/1013), [PR #1024](https://github.com/tobi/qmd/pull/1024)
- Downstream report: [openclaw#8786](https://github.com/openclaw/openclaw/issues/8786)

**Ecosystem and evidence**
- Latent Space, "Claude Code" with Boris Cherny (2025-05): https://www.latent.space/p/claude-code
- Anthropic, "Effective context engineering for AI agents" (2025-09): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Cursor, semantic search evaluation (2025-11): https://cursor.com/blog/semsearch
- "Is Grep All You Need?" (arXiv 2605.15184, 2026-05): https://arxiv.org/html/2605.15184v1
- AI Engineer Europe 2026, "Benchmarking semantic code retrieval on Claude Code": https://www.ai.engineer/talks/zKk7sDMGDEQ-benchmarking-semantic-code-retrieval-on-claude
- LlamaIndex, "Did filesystem tools kill vector search?": https://www.llamaindex.ai/blog/did-filesystem-tools-kill-vector-search
- Mario Zechner, MCP vs CLI: https://mariozechner.at/posts/2025-08-15-mcp-vs-cli/
- Obsidian CLI (requires the running app): https://obsidian.md/help/cli
- Omnisearch public API: https://publish.obsidian.md/omnisearch/Public+API+%26+URL+Scheme
- basic-memory v0.23: https://docs.basicmemory.com/whats-new/v0-23
- Plugins built on qmd:
  - Lantern: https://community.obsidian.md/plugins/lantern
  - Star QMD: https://community.obsidian.md/plugins/star-qmd
  - QMD Semantic Search: https://community.obsidian.md/plugins/qmd-semantic-search
- Prompt-injection audit of a vault qmd skill: https://www.skills.sh/breferrari/obsidian-mind/qmd/security/agent-trust-hub

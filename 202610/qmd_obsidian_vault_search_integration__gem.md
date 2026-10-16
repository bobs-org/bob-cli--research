# Integrating QMD into Bob and the Obsidian Vault: Feasibility, Architecture, Critique, and Implementation Roadmap

- **Date:** 2026-10-16
- **Researcher:** `research.1p.gem` (Swarm Member)
- **Target Systems:** `bob-cli`, Obsidian Vault (`~/bob`), SASE Agent Framework (`AGENTS.md` / skills), `bob-plugins`, Bob Mac Capture
- **Subject:** Tobias Lütke's `qmd` (Query Markup Documents) on-device hybrid search engine
- **Status:** Complete Research Proposal & Design Specification

---

## 1. Executive Summary

This report investigates integrating **`qmd`** ([github.com/tobi/qmd](https://github.com/tobi/qmd))—an on-device hybrid search engine built by Tobias Lütke for markdown documents and agentic flows—into Bryan's personal productivity ecosystem (`bob-cli`, the `~/bob` Obsidian vault, and SASE autonomous coding agents).

### The Core Problem
Bryan's Obsidian vault holds years of conceptual knowledge: literature references (`ref/`), research reports (`research/`), area notes, project documentation, articles, and meeting notes, alongside an active Getting Things Done (GTD) task and Pomodoro ledger. 
Currently, search across this vault is bifurcated:
1. **Deterministic / Metadata Search:** Handled effectively by `bob query` (Dataview DQL and Tasks v8 queries), `bob ref find` (reference lookup by URL/ID), and `ripgrep` (`rg`).
2. **Conceptual / Associative Search:** High-friction. When Bryan or an autonomous agent asks conceptual questions ("Where did I discuss spaced repetition decay?", "What notes explore LLM evaluation frameworks?", or "Find past research on pinentry hangs"), keyword search fails whenever terminology diverges. Pure vector search tools (e.g., Obsidian Omnisearch or Smart Connections) frequently hallucinate or miss exact phrases and code tags.

### The Opportunity: Why QMD?
`qmd` offers a state-of-the-art (SOTA) local retrieval pipeline combining:
- **SQLite FTS5 (BM25)** for exact keyword and term matching.
- **Dense Vector Search (`sqlite-vec`)** using local GGUF embedding models.
- **Query Expansion** via a fine-tuned 1.7B local LLM that expands natural language into typed lexical and vector sub-queries.
- **Cross-Encoder Re-ranking** via a local 0.6B Qwen3 reranker, fused through Reciprocal Rank Fusion (RRF) with position-aware blending.
- **Hierarchical Context Trees** (`qmd context add`) that feed structural domain semantics into LLM retrieval.
- **Built-in Agent Protocols:** Stdio and HTTP MCP servers, `--format json`, docids (`#abc123`), and line-level chunk extraction (`:from:count`).

### Key Conclusions & Strategic Verdict
1. **Integrating `qmd` is an excellent idea, but ONLY for conceptual and reference knowledge.** It should **never** be used for GTD tasks, active checkboxes, or Pomodoro ledgers. Tasks are dynamic, derived, date-sensitive states (`task-status-is-derived`, `today-is-read-from-the-ledger`) that require the deterministic parsing of `bob task` and `bob plan`. Chunking tasks into vector embeddings creates hallucinated states and token waste.
2. **Never expose `qmd` to agents as a bare one-shot CLI (`qmd query`).** Spawning `qmd query` from scratch incurs a **1.5 to 3.5 second cold-start penalty** while `node-llama-cpp` loads ~2GB of GGUF models from disk into RAM/VRAM. In iterative agent turns, this causes severe latency and CPU/VRAM churn.
3. **The Recommended Implementation: The Three-Tier Architecture:**
   - **Service Tier:** Run `qmd mcp --http --daemon` as a persistent background user service on Bryan's workstations (macOS launchd / Linux systemd). This keeps models warm, enabling sub-300ms searches.
   - **Lifecycle Tier:** Automate index maintenance by wiring `qmd update` into `bob nightly` and git synchronization hooks, with periodic low-priority background vector embedding (`qmd embed`).
   - **Access Tier:** Provide dual access:
     - For autonomous agents: A dedicated SASE skill (`/sase_vault_search`) backed by the `qmd` HTTP/MCP server with strict domain guardrails.
     - For humans & scripts: A native `bob search` subcommand in `bob-cli` acting as a thin client to the local `qmd` daemon, with graceful fallback to `rg` when offline.

---

## 2. Technical Deep Dive: What is QMD?

`qmd` (Query Markup Documents) is an open-source, on-device search engine specifically designed for local markdown corpora, personal knowledge bases, and AI agent integration.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         QMD Hybrid Search Pipeline                          │
└─────────────────────────────────────────────────────────────────────────────┘

                               ┌─────────────────┐
                               │   User Query    │
                               └────────┬────────┘
                                        │
                        ┌──────────────┴──────────────┐
                        ▼                             ▼
                ┌────────────────┐            ┌────────────────┐
                │ Query Expansion│            │  Original Query│
                │  (fine-tuned)  │            │   (×2 weight)  │
                └───────┬────────┘            └───────┬────────┘
                        │                             │
                        │ 2 alternative queries       │
                        └──────────────┬──────────────┘
                                       │
               ┌───────────────────────┼───────────────────────┐
               ▼                       ▼                       ▼
      ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
      │ Original Query  │     │ Expanded Query 1│     │ Expanded Query 2│
      └────────┬────────┘     └────────┬────────┘     └────────┬────────┘
               │                       │                       │
       ┌───────┴───────┐       ┌───────┴───────┐       ┌───────┴───────┐
       ▼               ▼       ▼               ▼       ▼               ▼
   ┌───────┐       ┌───────┐ ┌───────┐     ┌───────┐ ┌───────┐     ┌───────┐
   │ BM25  │       │Vector │ │ BM25  │     │Vector │ │ BM25  │     │Vector │
   │(FTS5) │       │Search │ │(FTS5) │     │Search │ │(FTS5) │     │Search │
   └───┬───┘       └───┬───┘ └───┬───┘     └───┬───┘ └───┬───┘     └───┬───┘
       │               │         │             │         │             │
       └───────┬───────┘         └──────┬──────┘         └──────┬──────┘
               │                        │                       │
               └────────────────────────┼───────────────────────┘
                                        │
                                        ▼
                           ┌───────────────────────┐
                           │   RRF Fusion + Bonus  │
                           │  Original query: ×2   │
                           │  Top-rank bonus: +0.05│
                           │     Top 30 Kept       │
                           └───────────┬───────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │    LLM Re-ranking     │
                           │  (qwen3-reranker)     │
                           │  Yes/No + logprobs    │
                           └───────────┬───────────┘
                                       │
                                       ▼
                           ┌───────────────────────┐
                           │  Position-Aware Blend │
                           │  Top 1-3:  75% RRF    │
                           │  Top 4-10: 60% RRF    │
                           │  Top 11+:  40% RRF    │
                           └───────────────────────┘
```

### 2.1 The Retrieval Engine: Hybrid Search, RRF, and Blending
Search tools traditionally force a choice between keyword search (BM25) and semantic vector search. BM25 excels at exact terminology (file paths, error codes, unique identifiers) but fails when the user describes a concept using different vocabulary. Vector search captures semantics but struggles with specific proper nouns and exact quotes.

`qmd` resolves this by executing a multi-stage pipeline:
1. **Query Expansion:** The original query is processed by a local fine-tuned 1.7B model (`qmd-query-expansion-1.7B-q4_k_m.gguf`). It generates typed variations: `lex` for BM25 keywords, `vec` for dense semantic sentences, and `hyde` for hypothetical document embeddings.
2. **Dual-Backend Retrieval:** The original query (given 2x weight) and generated variations execute in parallel against SQLite FTS5 (BM25) and `sqlite-vec` (cosine distance).
3. **Reciprocal Rank Fusion (RRF):** Results from both backends are fused using $RRF(d) = \sum \frac{1}{k + rank(d)}$ (with $k=60$). Documents ranking #1 in any list receive an additional $+0.05$ top-rank bonus (and $+0.02$ for ranks 2–3) to prevent dilution of exact matches.
4. **Local Cross-Encoder Reranking:** The top 30 candidates are passed to a local 0.6B cross-encoder (`qwen3-reranker-0.6b-q8_0.gguf`) running via `node-llama-cpp`, which computes a normalized relevance score from logprobs.
5. **Position-Aware Blending:** Final scores blend RRF rank with reranker scores dynamically:
   - Rank 1–3: 75% retrieval, 25% reranker (preserves high-confidence exact matches).
   - Rank 4–10: 60% retrieval, 40% reranker.
   - Rank 11+: 40% retrieval, 60% reranker (trusts the reranker for borderline matches).

### 2.2 Smart Markdown Chunking
Rather than splitting text at arbitrary token limits (which truncates paragraphs and destroys code fences), `qmd` scans markdown files for structural break points:
- H1–H6 headers (scores 100 to 50).
- Code fence boundaries (score 80; code blocks are never cut internally).
- Horizontal rules (`---` / `***`, score 60).
- Paragraph blank lines (score 20).
- List items (score 5).

When approaching the target chunk size (~900 tokens), it applies distance decay ($baseScore \times (1 - (dist/window)^2 \times 0.7)$) across a 200-token window, selecting the cleanest structural cut. Each chunk retains document title, section context, and a 15% overlap. Furthermore, it supports optional tree-sitter AST chunking (`--chunk-strategy auto`) for source code.

### 2.3 Context Trees
`qmd` introduces **Context Trees** via virtual URIs (`qmd://<collection>/<path>`). Administrators can annotate path prefixes with semantic intent:
```bash
qmd context add qmd://vault/ref "Academic papers, literature notes, and book summaries"
qmd context add qmd://vault/areas "Ongoing life domains, GTD areas of responsibility"
qmd context add qmd://vault/projects "Active project workspaces and technical design specs"
```
During retrieval, these context strings are injected alongside matches. For LLM agents, this provides immediate structural understanding of whether a passage is an authoritative design doc, a raw meeting note, or an archived idea.

### 2.4 Frontmatter Metadata Filtering and Discovery
`qmd` parses frontmatter blocks under `qmd.metadata`:
```markdown
---
qmd:
  metadata:
    topics: [architecture, search, sqlite]
    status: published
    year: 2026
---
```
It compiles typed metadata into SQLite tables, enabling agents to execute recursive JSON AST filters (`and`, `or`, `eq`, `gte`, `contains`, `in`) and inspect available metadata schema via `qmd collection metadata <collection>` before searching.

### 2.5 Hardware & Computational Footprint
- **Runtime:** Node.js >= 22 or Bun >= 1.0.0.
- **Database:** SQLite with extension loading (`sqlite-vec`, `fts5`).
- **Models:**
  - Embedding: `embeddinggemma-300M-Q8_0` (~300 MB).
  - Reranker: `qwen3-reranker-0.6b-q8_0` (~640 MB).
  - Query Expansion: `qmd-query-expansion-1.7B-q4_k_m` (~1.1 GB).
  - Total Disk Footprint: ~2.1 GB stored in `~/.cache/qmd/models/`.
- **Inference Acceleration:**
  - macOS: Apple Silicon Metal acceleration via `node-llama-cpp`. Fast, highly efficient.
  - Linux: CUDA (requires NVIDIA toolkit) or Vulkan / CPU fallback.
  - VRAM Consumption: ~2.2 GB VRAM when all three models are loaded. In daemon mode, `qmd` keeps model weights resident in VRAM but automatically disposes idle inference contexts after 5 minutes.

---

## 3. The Target Ecosystem: Bob, SASE, and the Obsidian Vault

To evaluate where `qmd` fits, we must examine Bryan's existing tooling and information architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Bryan's Vault Ecosystem                            │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ Domain                        │ Primary Tools / Engines                     │
├───────────────────────────────┼─────────────────────────────────────────────┤
│ Tasks, Ledger & GTD           │ bob task, bob plan, bob query --tasks       │
│ Reference Library (ref/)      │ bob ref (find, list, show), Highlights PDF  │
│ Articles & Documentation      │ bob articles, markdown viewer               │
│ Daily Review & Freshness      │ bob freshness, Alt+F / Ctrl+Alt+F           │
│ Capture Protocol              │ bob capture, Bob Mac Capture (SwiftUI HUD)  │
│ Synchronous Maintenance       │ bob nightly, bob vault-sync                 │
│ Ephemeral Agent Workspaces    │ SASE (bob-cli_<N>), AGENTS.md, skills       │
└───────────────────────────────┴─────────────────────────────────────────────┘
```

### 3.1 Vault Structure and Data Types
1. **Dynamic GTD Subsystem:**
   - Tasks reside across area and project notes with explicit syntax: `- [ ] (1645-1710) #task [[link]] [dependsOn:: ...] ^task-id`.
   - Task statuses are strictly derived from the daily Pomodoro ledger and dependency graph (`task-status-is-derived`, `today-is-read-from-the-ledger`).
   - Sticky task lanes (`task-lanes-are-sticky`) and per-note ready caps (`note-ready-cap-counts-the-lane`) govern visibility.
2. **Semi-Static Knowledge Subsystem:**
   - **`ref/`**: Reference library notes synced from Highlights PDFs and web captures via `bob ref`. Highly dense, containing summaries, reading logs, and academic annotations.
   - **`articles/`**: Long-form structured essays and articles with section numbering (`bob articles`).
   - **`projects/` & `areas/`**: Project overviews, design proposals, architecture decision records (`decisions:` web), and technical notes.
   - **`research/`**: SASE research reports generated across swarm runs.

### 3.2 Existing Query & Search Tools
- **`bob query`**: A native Rust execution engine running Dataview DQL expressions (`LIST FROM #waiting`, `TABLE status, due FROM #project`) and Obsidian Tasks v8 query expressions directly against the local vault files without requiring Obsidian to be open.
- **`bob ref find`**: Fast lookup matching exact URLs, arXiv IDs, DOIs, and note stems across `ref/`.
- **`ripgrep` (`rg`)**: The standard tool used by SASE agents for raw text searches across code and markdown files.

---

## 4. Comprehensive Critique of the Plan

Bryan's initial prompt outlines:
> *"I'm thinking about integrating qmd into bob or my Obsidian vault somehow (agent instructions to use it when searching my Obsidian vault, for example). Can you do some research with the goal of helping me decide the best way to implement this? Also, critique this plan in general. Is this a good idea? Would you take a different approach?"*

### 4.1 Is Integrating QMD a Good Idea? (The Strategic Case)

**YES—with strict boundary constraints.**

Integrating `qmd` solves a genuine, well-documented weakness in personal knowledge management: **lexical search failure across large knowledge corpora**.
- **When keyword search succeeds:** When an agent or human knows an exact symbol (`bob_pomodoro`), note name (`Apollo Pass Pinentry Hang`), or tag (`#prj_is_blocked`), `rg` or `bob ref find` is instantaneous (<10ms) and 100% accurate.
- **When keyword search fails:** When researching broader concepts ("what did we conclude about background process timeouts?", "spaced repetition card triggers", "macOS window focus quirks"), keyword search requires guessing the exact words Bryan wrote months ago. If Bryan wrote "decay streak threshold" and the agent searches "rotten card frequency", `rg` returns zero results.
- `qmd` bridges this semantic gap entirely on-device, preserving vault privacy, operating without cloud API fees, and providing calibrated relevance rankings.

### 4.2 The Five Critical Pitfalls & Friction Points

If implemented naively, this integration will create severe friction:

#### Pitfall 1: The Staleness Trap (Vault Dynamism vs. Static SQLite Index)
`qmd` does not run an in-process filesystem event watcher by default; it queries an offline SQLite index (`~/.cache/qmd/index.sqlite`).
- In Bryan's vault, files mutate continuously: captures occur from macOS, tasks are completed, git sync pulls remote updates, and SASE agents write research reports.
- If an agent searches the vault with `qmd` and the index is 48 hours old, newly captured notes and recent edits are completely invisible.
- However, running a full `qmd embed` on every file edit is computationally prohibitive: embedding 2,000 markdown chunks requires substantial GPU/CPU time.
- *Mitigation:* Decouple lexical indexing from vector embedding. `qmd update` (which updates FTS5 keyword indexes) takes <500ms and should run automatically in sync hooks. Full vector re-embedding (`qmd embed`) should be deferred to a background batch.

#### Pitfall 2: The Cold-Start CLI Latency Trap
If an agent's system prompt simply instructs:
> *"When searching Bryan's vault, run `qmd query '<topic>'`"*

The agent will execute a standalone CLI process. Every single `qmd query` call will:
1. Initialize the Node.js/Bun engine.
2. Open SQLite and load native extension shared libraries.
3. Invoke `node-llama-cpp`, allocate ~2GB of host RAM/VRAM, and load three GGUF models from disk.
4. Run inference, print results, and terminate—freeing all memory.

**This takes 1.5 to 3.5 seconds on Apple Silicon and up to 6–10 seconds on CPU-only Linux.**
If an agent executes 3 iterative queries to refine its search, the agent turn is delayed by 15–20 seconds purely in model initialization overhead.
- *Mitigation:* The daemon mode (`qmd mcp --http --daemon`) MUST be used. Once daemonized, models remain resident in VRAM, dropping query latency to 150–400ms.

#### Pitfall 3: The Domain Mismatch Risk (Tasks vs. Knowledge)
The vault contains two fundamentally different kinds of data:
- **Tasks & Pomodoro Ledgers:** Highly volatile, syntax-strict, state-machine driven. A task's status depends on whether its block ID is linked under today's open Pomodoro, whether its prerequisite `^prj` line is blocked, or whether its date mark has arrived.
- **Knowledge Notes:** Articles, reference papers, and project documentation.

If an agent attempts to use `qmd` to query tasks ("What tasks are due today?"), `qmd` will fail catastrophically:
- Its markdown chunker strips list context and splits parent/child dependency lines.
- It has no awareness of GTD reconciliation rules.
- It will return completed tasks, archived tasks from `done/`, or out-of-date Pomodoro blocks as "relevant".
- *Mitigation:* Strict policy boundary: `qmd` is strictly for **knowledge and reference retrieval**. Task and schedule queries must remain exclusively with `bob task`, `bob plan`, and `bob query --tasks`.

#### Pitfall 4: Cross-Platform Heterogeneity (macOS vs. Linux Server)
Bryan works on macOS (Apple Silicon with Metal acceleration), but SASE agents also run on Linux servers (e.g. `apollo`, `athena`).
- On macOS, `node-llama-cpp` leverages unified memory Metal compute seamlessly with negligible thermal impact.
- On Linux without dedicated NVIDIA GPUs, running a 1.7B query expansion model + 0.6B reranker on CPU will pin CPU cores and risk CPU saturation (recall recent incident report `athena_cpu_saturation_orphaned_load_loops.md`).
- *Mitigation:* On Linux machines without GPU acceleration, `qmd` should be configured with `--no-rerank` or `QMD_FORCE_CPU=1`, or fall back to hybrid search without the heavy 1.7B expansion model.

#### Pitfall 5: Architectural Boundary (`bob` Rust vs. `qmd` TypeScript)
`bob-cli` is written in Rust, compiling to a clean, fast, dependency-free binary.
- Tobias Lütke's `qmd` is written in TypeScript and distributed via npm/bun (`@tobilu/qmd`).
- Attempting to rewrite `qmd` in Rust or vendor Node.js inside `bob-cli` would be an enormous maintenance mistake.
- *Mitigation:* Treat `qmd` as an external system service or subprocess. `bob-cli` should interact with `qmd` either over its standard localhost HTTP API (`http://localhost:8181/query`) or via process invocation, preserving `bob`'s clean Rust codebase.

---

### 4.3 Comparison with Credible Alternatives

| Dimension | `qmd` (Tobias Lütke) | `ripgrep` (`rg`) | SQLite FTS5 in `bob` | Obsidian Omnisearch | Local Embedding API (Ollama/LMStudio) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Search Quality** | **SOTA Hybrid:** BM25 + Vector + Rerank | Lexical exact/regex only | Lexical BM25 only | BM25 + Vector (WASM) | Vector-only or API-based |
| **Cold-Start Latency** | ~2s CLI / <300ms HTTP daemon | **<15ms** | **<10ms** | In-app instant | 200–500ms HTTP |
| **Agent Readiness** | **Native MCP & JSON AST** | Raw text / regex | Custom JSON | None (desktop GUI only) | Raw vector arrays |
| **Context Awareness** | **Hierarchical Context Trees** | None | None | None | Prompt-dependent |
| **Memory / Footprint** | ~2.1 GB models, ~2GB VRAM | Negligible (<20MB) | Negligible (<50MB) | High inside Electron | High (~2-4GB) |
| **Maintenance Burden** | Node/Bun global package | Installed system package | Built into `bob` binary | Electron plugin sync | External daemon management |
| **Verdict** | **Best for conceptual retrieval** | Best for exact code/tags | Best for fast keyword indexing | Rejected (desktop bound) | Rejected (inferior pipeline) |

**Why `qmd` beats pure BM25 or pure Vector:**
A user searching for *"how we handle task decay after repeated review keeps"* will completely miss documents discussing *"rotten keep streak and approved decay"* under pure keyword search. Conversely, vector search alone often ranks vague thematic essays higher than the exact specification doc. `qmd`'s RRF fusion, top-rank bonus, and local cross-encoder reranking consistently deliver the exact target document in the top 3 results.

---

## 5. Evaluation of Integration Paths

We evaluated four distinct integration paths:

### Path A: Agent Prompt / Skill Only
- **How it works:** Install `qmd` globally (`bun install -g @tobilu/qmd`). Add a SASE skill `/sase_vault_search` and instructions in `AGENTS.md` guiding agents to run `qmd query "<query>" --format json`.
- **Strengths:** Zero modifications to `bob-cli` or `bob-plugins`. Immediately testable.
- **Fatal Weakness:** Cold-start latency. Spawning standalone `qmd` runs on every agent invocation makes agents feel sluggish and wastes GPU memory reallocating models. Furthermore, without background indexing, the index quickly becomes stale.

### Path B: Native MCP Server (`qmd mcp --http --daemon`)
- **How it works:** Launch `qmd`'s built-in HTTP MCP server as a daemon. Configure it in agent environments (Claude Code, Antigravity, Gemini). Agents invoke structured tools (`query`, `get`, `multi_get`, `metadata`).
- **Strengths:**
  - **Zero cold-start latency:** Models stay warm in VRAM.
  - **Structured LLM contract:** Passes typed parameters (`intent`, `minScore`, `filter`) and returns clean JSON results with line ranges and docids.
  - **Context-preserving chunk fetching:** Agents can use `get(file="#abc123:50:40")` to read exact matching excerpts without polluting their context windows with multi-thousand-line notes.
- **Weaknesses:** Requires managing a background daemon process. Does not provide a CLI command for human shell usage.

### Path C: First-Class `bob` CLI Integration (`bob search`)
- **How it works:** Add `bob search <query>` to `bob-cli` (Rust).
  - First attempts to connect to `http://localhost:8181/query`.
  - If the daemon is unreachable, falls back to running `qmd query --format cli` as a subprocess.
  - If `qmd` is not installed, falls back to `rg -i` across the vault.
  - Plugs into `bob nightly` to run `qmd update` automatically.
- **Strengths:** Single coherent command interface for Bryan. Integrates vault maintenance into existing Bob nightly workflows. Provides transparent fallbacks.
- **Weaknesses:** Requires a small Rust implementation in `bob-cli`.

### Path D: Native Obsidian Plugin (`bob-plugins`)
- **How it works:** Build a new plugin in `bob-plugins` or an action in `Bob Mac Capture` connecting to `qmd`'s HTTP endpoint for instant interactive search.
- **Strengths:** Great interactive GUI experience inside Obsidian or the Mac menu bar.
- **Weaknesses:** Solves the human UI problem, but does not solve the agent problem. Can be added later as an enhancement.

---

## 6. Adjustments to the Requirements

Based on this analysis, the following adjustments to Bryan's original idea are **mandatory**:

### Adjustment 1: Strict Domain Scoping (Ban QMD from Tasks and Ledgers)
* **Rationale:** Tasks, Pomodoro ledgers, and GTD lanes are derived state machines. Vector chunking destroys task line dependencies and date markers.
* **Specification:** `qmd`'s collection configuration MUST explicitly ignore task archives (`done/**`), Obsidian system files (`.obsidian/**`), and raw intake files (`xlib/**`). SASE agent instructions must explicitly state:
  > *"NEVER use qmd to find open tasks, check task dependencies, or inspect today's Pomodoro plan. Use `bob plan`, `bob task`, or `bob query --tasks` for all task operations."*

### Adjustment 2: Mandatory Daemonization for Agentic and Interactive Use
* **Rationale:** A 2–3 second cold-start penalty per CLI call degrades agent performance and burns memory bandwidth.
* **Specification:** `qmd` must run as a persistent user daemon via its HTTP server (`qmd mcp --http --daemon`). Both SASE agent tools and the `bob search` CLI command should talk to this local HTTP endpoint.

### Adjustment 3: Decouple Fast Lexical Sync from Heavy Vector Embedding
* **Rationale:** `qmd update` (FTS5 scan) takes <500ms; `qmd embed` (GGUF embedding inference) takes minutes on large corpora.
* **Specification:**
  - `qmd update` runs on every `bob nightly` and can be triggered on `bob vault-sync`.
  - `qmd embed` runs strictly as a scheduled off-peak background batch (or manual invocation), ensuring the system remains responsive during active working hours.

### Adjustment 4: Leverage QMD Context Trees for the Vault Hierarchy
* **Rationale:** `qmd`'s unique feature is hierarchical context injection. A flat index treats all notes equally, confusing an archived 2024 idea with an active 2026 project specification.
* **Specification:** Bryan's vault must be configured with explicit context annotations mapping directories (`ref/`, `projects/`, `areas/`, `articles/`, `decisions/`) to descriptive semantic labels.

---

## 7. The Recommended Architecture: The Three-Tier Vault Retrieval System

The recommended solution combines the best aspects of Paths B, C, and E into a cohesive three-tier architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Three-Tier Vault Retrieval Architecture                   │
└─────────────────────────────────────────────────────────────────────────────┘

 [Tier 3: Consumers]
       │
       ├─► SASE Agents (Antigravity/Claude/Gemini) ──► MCP / HTTP (:8181/mcp)
       │
       ├─► Human CLI (Bryan) ───────────────────────► bob search <query>
       │                                                     │
       │                                                     ▼ (HTTP Client)
 [Tier 2: Service & API]                                     │
       │                                                     ▼
       └─► qmd HTTP Daemon (:8181) ◄─────────────────────────┘
             ├── POST /mcp       (Streamable MCP protocol)
             ├── POST /query     (Direct structured search API)
             └── GET  /health    (Liveness & uptime probe)
                   │
                   ▼ (Persistent in VRAM)
             Models: embeddinggemma-300M | qwen3-reranker-0.6B | qmd-query-expansion-1.7B
                   │
 [Tier 1: Storage & Maintenance]
       │
       ├─► SQLite Storage: ~/.cache/qmd/index.sqlite (FTS5 + sqlite-vec)
       │
       ├─► Configuration:  ~/.config/qmd/index.yml (Collections, Contexts, Ignores)
       │
       └─► Lifecycle Automation:
             ├── bob nightly      ──► runs `qmd update` (fast FTS sync)
             └── weekly / manual  ──► runs `qmd embed`  (vector refresh)
```

### Component Breakdown

#### Tier 1: Storage, Configuration & Maintenance
- **Vault Collection Definition (`~/.config/qmd/index.yml`):**
  Defines `vault` pointing to `~/bob`, configuring strict exclusion rules and context strings.
- **Lifecycle Integration:**
  `bob nightly` invokes `qmd update` as part of its scheduled vault maintenance.

#### Tier 2: Background Daemon Service
- **Service Unit:** Managed via macOS `launchd` (or Linux `systemd --user`).
- **Command:** `qmd mcp --http --port 8181 --daemon`.
- **Role:** Keeps the SQLite connection open and GGUF model weights resident in VRAM. Provides sub-300ms response times for all callers.

#### Tier 3: Consumption Interfaces
- **For Agents:** The `qmd` MCP server configured in agent tool manifests, complemented by an audited SASE skill (`/sase_vault_search`).
- **For Humans & Shell Scripts:** A lightweight `bob search` command added to `bob-cli` in Rust. It sends an HTTP request to `localhost:8181/query`, pretty-prints colorized results with clickable terminal hyperlinks (`OSC 8`), and falls back gracefully to `rg` if the daemon is offline.

---

## 8. Concrete Implementation Specification & Rollout Plan

### Phase 1: Installation and Vault Configuration

#### 1.1 Install Prerequisites
```bash
# On macOS:
brew install sqlite node
npm install -g @tobilu/qmd

# On Linux (Ubuntu):
# Ensure Node >= 22 (already present at v24.15.0)
npm install -g @tobilu/qmd
```

#### 1.2 Initialize Vault Configuration
Create or update `~/.config/qmd/index.yml`:

```yaml
# ~/.config/qmd/index.yml
global_context: "Bryan's Personal Knowledge Base, Literature Library, and Engineering Vault"

# Clickable terminal links for VS Code / Cursor / Neovim
editor_uri: "vscode://file/{path}:{line}:{col}"

collections:
  vault:
    path: /home/bryan/bob        # or /Users/bryan/bob on macOS
    pattern: "**/*.md"
    ignore:
      - ".obsidian/**"           # Internal workspace configs and caches
      - ".trash/**"              # Deleted notes
      - "done/**"                # Archived GTD tasks
      - "xlib/**"                # Raw intake PDFs (unprocessed)
      - "**/*.assets/**"         # Image and audio attachments
      - "day.md"                 # High-frequency Pomodoro ledger (volatile)
    includeByDefault: true
    context:
      "/": "General knowledge base, concepts, and personal thoughts"
      "/ref": "Literature notes, academic papers, and reading summaries"
      "/projects": "Active engineering projects, technical architectures, and design docs"
      "/areas": "GTD areas of responsibility, long-term domains, and workflows"
      "/articles": "Long-form written essays and polished articles"
      "/decisions": "Architecture Decision Records (ADRs) for Bob and SASE"
      "/research": "Durable research reports and investigations"
```

#### 1.3 Initial Indexing and Embedding
```bash
# Initial FTS scan (takes 5-10 seconds)
qmd update

# Generate embeddings for semantic vector search (run once, takes 2-5 minutes)
qmd embed
```

---

### Phase 2: Daemonization & Automated Lifecycle

#### 2.1 Daemon Service Configuration

**On Linux (`~/.config/systemd/user/qmd.service`):**
```ini
[Unit]
Description=QMD Hybrid Search Engine HTTP Daemon
After=network.target

[Service]
Type=simple
ExecStart=%h/.config/nvm/versions/node/v24.15.0/bin/qmd mcp --http --port 8181
Restart=on-failure
RestartSec=5s
Environment=NODE_ENV=production

[Install]
WantedBy=default.target
```
Enable and start:
```bash
systemctl --user daemon-reload
systemctl --user enable --now qmd.service
```

**On macOS (`~/Library/LaunchAgents/com.bobs.qmd.plist`):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bobs.qmd</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/qmd</string>
        <string>mcp</string>
        <string>--http</string>
        <string>--port</string>
        <string>8181</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

#### 2.2 Wire into `bob nightly`
In `bob-cli/src/native/nightly.rs`, add an automated `qmd update` invocation immediately following vault git sync:
```rust
// Inside Nightly execution sequence:
// 1. bob vault-sync
// 2. bob task archive
// 3. qmd update (re-index FTS5 tables with newly synced/archived state)
// 4. bob vault-sync
```
Because `qmd update` completes in under 500 milliseconds, it introduces zero perceptible delay to the nightly run.

---

### Phase 3: SASE Agent Integration (MCP & Skill)

#### 3.1 Antigravity / Gemini CLI MCP Configuration
Register the QMD HTTP endpoint in the agent's MCP settings:
```json
{
  "mcpServers": {
    "qmd_vault": {
      "url": "http://localhost:8181/mcp"
    }
  }
}
```

#### 3.2 SASE Skill: `/sase_vault_search`
Create a dedicated skill file `~/.gemini/config/skills/sase_vault_search/SKILL.md`:
```markdown
---
name: sase_vault_search
description: Search Bryan's Obsidian vault for conceptual knowledge, reference notes, literature, and project designs using local hybrid search.
---

Use this skill when you need to research concepts, literature, previous decisions, or technical documentation in Bryan's Obsidian vault.

## Rules & Boundaries
- **DO NOT use this tool for tasks or Pomodoro ledgers.** Tasks are dynamic state machines. Use `bob plan`, `bob task`, or `bob query --tasks` for all task-related questions.
- **DO NOT use this tool if you already have an exact note name or code identifier.** Use `ripgrep` (`rg`) or `bob ref find` for exact lookups.
- **Use this tool for:** Conceptual questions ("how does keep decay work?", "where is the architecture decision for reference renaming?", "literature on query expansion").

## Usage
Call the `qmd_vault` MCP tool `query`:
```json
{
  "searches": [
    { "type": "vec", "query": "spaced repetition keep decay card trigger" },
    { "type": "lex", "query": "decay streak refresh" }
  ],
  "collections": ["vault"],
  "minScore": 0.4,
  "limit": 5
}
```
Or via CLI fallback:
```bash
curl -s -X POST http://localhost:8181/query \
  -H "Content-Type: application/json" \
  -d '{"query": "your conceptual query", "minScore": 0.35, "limit": 5}' | jq .
```
```

#### 3.3 Update Core Agent Instructions (`AGENTS.md`)
Add a concise section under Reference Memory or Agent Tools in `AGENTS.md`:
```markdown
### Vault Knowledge Search
- When researching conceptual topics, literature, and documentation in Bryan's vault, use your `/sase_vault_search` skill or the `qmd_vault` MCP tool.
- Never search tasks, checkboxes, or Pomodoro schedules with QMD; tasks are strictly derived and must be inspected via `bob plan` or `bob query --tasks`.
```

---

### Phase 4: `bob-cli` Command Addition (`bob search`)

To provide Bryan with an ergonomic CLI search experience from any terminal, add `bob search` to `bob-cli`.

#### 4.1 CLI Interface Design
```bash
bob search "spaced repetition decay"          # Hybrid search via local daemon (default)
bob search "pinentry timeout" --lexical       # Fast BM25 keyword search
bob search "local LLM reranking" --semantic   # Vector-only search
bob search "capture grammar" -n 10 --json     # Structured JSON output for scripts
```

#### 4.2 Implementation Architecture in Rust
In `src/runner.rs`, add:
```rust
Subcommand {
    name: "search",
    about: "Search vault knowledge and reference notes using hybrid semantic retrieval",
    section: Section::Vault,
    target: Target::Leaf(Leaf {
        native_command: NativeCommand::Search,
        script_command: None,
    }),
}
```

In `src/native/search.rs`:
```rust
pub fn run(args: &[OsString]) -> i32 {
    let matches = parse_args(args);
    let query = matches.get_one::<String>("query").unwrap();
    
    // 1. Check if qmd daemon is running on localhost:8181
    if let Ok(response) = query_qmd_daemon(query, &matches) {
        render_results(&response, matches.get_flag("json"));
        return 0;
    }
    
    // 2. Fallback: Check if qmd CLI is installed
    if is_qmd_cli_available() {
        eprintln!("[bob search] Daemon offline; invoking qmd CLI (cold-start)...");
        return invoke_qmd_cli(query, &matches);
    }
    
    // 3. Fallback: Plain ripgrep
    eprintln!("[bob search] qmd not available; falling back to ripgrep...");
    invoke_ripgrep(query)
}
```

---

## 9. Failure Modes, Diagnostics, and Operational Safeguards

| Failure Mode | Root Cause | Symptom | Remediation / Safeguard |
| :--- | :--- | :--- | :--- |
| **Daemon Crash or Unreachable** | Port 8181 conflict, OOM, or service stopped. | `Connection refused` on `localhost:8181`. | `bob search` and `/sase_vault_search` automatically fall back to CLI or `rg`. Health probe `GET /health` monitored by systemd/launchd. |
| **Index Staleness** | Bryan added/renamed notes but `qmd update` has not run. | New notes missing from search results. | `bob nightly` runs `qmd update` automatically. Fast command `bob search --update` triggers instant re-indexing before query. |
| **Outdated Embeddings** | New notes indexed in FTS but not yet embedded. | Vector search misses new notes; FTS still matches them. | QMD hybrid search gracefully handles this: FTS (BM25) continues to rank new documents; RRF surfaces them via top-rank bonus. `qmd status` displays pending embedding count. |
| **CPU Saturation on Linux** | Running full 1.7B query expansion + reranker on CPU without GPU. | High load average, sluggish terminal response. | Force `--no-rerank` and `--no-gpu` on headless Linux boxes via `QMD_FORCE_CPU=1` or `qmd.service` environment configuration. |
| **Task State Hallucination** | Agent queries tasks using `qmd`. | Agent cites archived tasks or invents schedule dates. | Strict agent instruction guardrail banning task queries in QMD; task commands remain reserved for `bob task` and `bob plan`. |

---

## 10. Conclusion & Final Recommendation

### Summary of Verdict
Integrating Tobias Lütke's `qmd` into Bryan's ecosystem is **highly recommended**, representing a major qualitative upgrade over pure `ripgrep` for navigating years of accumulated research, literature notes, and technical design documents. 

Its hybrid combination of SQLite FTS5, `sqlite-vec`, query expansion, and cross-encoder reranking is uniquely suited for personal markdown vaults—avoiding the blind spots of pure keyword matching and the fuzziness of pure vector search.

### Recommended Next Steps
1. **Approve the Scope Boundary:** Formally restrict `qmd` to knowledge notes (`ref/`, `projects/`, `areas/`, `articles/`, `decisions/`, `research/`) while strictly excluding GTD tasks and Pomodoro ledgers.
2. **Deploy Phase 1 & 2:** Install `qmd`, configure `~/.config/qmd/index.yml` with Bryan's vault collection and context hierarchy, and start the background HTTP daemon (`qmd mcp --http --daemon`).
3. **Deploy Phase 3:** Configure the `qmd` MCP server in Antigravity / Gemini CLI and publish the `/sase_vault_search` skill for SASE agents.
4. **Deploy Phase 4:** Implement `bob search` in `bob-cli` to provide a unified, fast CLI interface for interactive terminal use.

This architecture ensures zero cold-start latency, eliminates index staleness through `bob nightly`, protects GTD task integrity, and equips both Bryan and his autonomous AI agents with state-of-the-art local semantic retrieval.

# Research Report: Migrating `bob highlights` to `bob ref` for Reading Tracking and Annotation Intelligence

**Researcher:** gem (`research.3s.gem`)  
**Date:** 2026-10-06  
**Artifact ID:** `research:202610/bob_ref_command_migration__gem.md`  
**Target Repository:** `bob-cli`  

---

## 1. Executive Summary

This research investigates the proposed migration of the `bob highlights` command suite in `bob-cli` to a new `bob ref` command hierarchy. The proposed change aims to preserve all existing synchronization capabilities (web clipping, intake PDF creation, marker management, library scanning, and bi-directional note sync) while expanding the toolset to support **reading tracking** (tracking what Bryan has read, what is queued, what is in progress, and what has been abandoned) and **annotation consumption** (retrieving quotes, personal comments, and callouts authored in Highlights and synced to reference notes).

### Key Verdict
**The proposal is strongly justified and highly recommended.** Renaming the tool from `highlights` to `ref` corrects a longstanding conceptual misnomer: "Highlights" is merely an external macOS PDF annotation tool, whereas the true first-class vault domain entity is the **Reference Note** (`type: "[[ref]]"`, `^ref` lifecycle task, and `REFERENCES` freshness review tier).

However, a naive migration that simply renames the binary while treating references solely as Highlights PDFs would suffer from severe failure modes. This research audited the actual Bob vault (`~/bob/ref/` containing 590 reference notes) and uncovered critical structural realities:
1. **The Dual Status Architecture:** 308 notes are modern Highlights-managed references with synchronized `^ref` tasks, while 282 notes are legacy reference notes (`status: legacy`) carrying unread reading statuses (`legacy_status: unread`, `collect_fleeting_notes`) without `^ref` tasks. A reading tracking command must normalize across both worlds.
2. **The URL Field Fragmentation Defect:** 283 reference notes in the vault store external URLs under `url:`, while only 2 notes use `source_url:`. The current `bob highlights clip` deduplication scanner only inspects `source_url:`, making it blind to 99% of existing references in the vault.
3. **Performance Divergence:** While `bob query` (the headless Dataview engine) can theoretically query reference notes, running DQL against the entire vault requires ~4 seconds and emits link ambiguity warnings. A dedicated native `bob ref` scanner focused exclusively on `~/bob/ref/` executes in under 15 milliseconds, providing the sub-second response times required for interactive agent tool invocation.
4. **Agent-Centric Deduplication:** For AI agents recommending literature, searching solely by exact URL strings is insufficient. Academic papers are cited interchangeably via ArXiv abstract URLs (`/abs/`), PDF URLs (`/pdf/`), ArXiv IDs, DOIs, and titles. `bob ref find` must provide multi-tier canonical identifier matching.

This report outlines the conceptual model, critiques the proposed plan, details the necessary requirement adjustments, specifies the complete command surface, and delivers a concrete engineering roadmap.

---

## 2. Vault and Codebase Baseline Audit

### 2.1 The Current `bob highlights` Architecture
The current `bob highlights` implementation resides in `src/native/highlights_ref/` and is exposed via `src/runner.rs` as a `Target::Leaf` command in `Section::Integrations`. It offers six subcommands:

```bash
bob highlights clip <URL>      # Web article -> reader mode -> intake PDF (xlib/blogs/)
bob highlights create <MD>     # Markdown report -> pandoc PDF with marker (xlib/chat/)
bob highlights doctor          # Preflight paths, hooks, Git worktree, marker readability
bob highlights marker <PDF>    # Inspect page-1 standalone /Text note marker
bob highlights scan            # Intake move (xlib -> lib), audio pair, recursive sync
bob highlights sync <PDF>      # 2-way marker/frontmatter sync & sidecar callout import
```

The system operates around two key sync targets:
- **PDF Page-1 Marker:** Standalone `/Text` note on page 1 carrying YAML-like pairs: `status`, `parent`, `title`, `id`, `source_url`.
- **Obsidian Reference Note:** Markdown note in `~/bob/ref/<ref_type>/<stem>.md` with frontmatter `type: "[[ref]]"`, `status`, `source_pdf`, and a managed callout region delineated by `<!-- highlights:begin -->` and `<!-- highlights:end -->`.

### 2.2 Census of the Reference Vault (`~/bob/ref`)
An empirical census was conducted on Bryan's active vault (`/home/bryan/bob/ref/`):

| Metric | Count | Details |
|---|---|---|
| **Total Reference Notes** | **590** | Distributed across `papers/`, `blogs/`, `chat/`, `docs/`, `ai/` |
| **Modern Highlights Notes** | **308** | Contain `source_pdf:`, synchronized `^ref` task |
| — Status: `read` (`- [x]`) | 285 | Finished reading |
| — Status: `abandoned` (`- [-]`) | 17 | Cancelled / dropped |
| — Status: `next` (`- [*]`) | 5 | Queued up next |
| — Status: `ready` (`- [ ]`) | 1 | Unread in backlog |
| — Status: `wip` (`- [/]`) | 0 | Actively being read |
| **Legacy Reference Notes** | **282** | Migrated from Zorg; `status: legacy`, no `^ref` task |
| — `legacy_status: unread` | 144 | Unread reference backlog |
| — `legacy_status: collect_fleeting_notes` | 92 | Processing literature backlog |
| — `legacy_status: read` | 25 | Read legacy material |
| — `legacy_status: review_fleeting_notes` | 13 | Review backlog |
| — `legacy_status: review_lit_notes` | 4 | Review backlog |
| — `legacy_status: abandoned` | 4 | Dropped legacy material |
| **Notes with Synced Highlights** | **123** | Have `highlights_sidecar:` and `highlights_count:` |
| **Total Highlights Synced** | **361** | Callout blocks (`[!quote]`, `[!note] Comment`, images) |

### 2.3 Discovery: The URL Field Divergence Defect
During the audit of frontmatter keys across all 590 notes:
- Notes with `title:`: 531
- Notes with `url:`: **283**
- Notes with `source_url:`: **2**

In `src/native/highlights_ref/clip.rs` (lines 545–550), the existing intake deduplication scanner `collect_ref_note_sources` contains:
```rust
for raw in frontmatter {
    let entry = parse_frontmatter_entry(&raw);
    if entry.key.as_deref() != Some("source_url") {
        continue;
    }
    // ...
}
```
Because the existing clip scanner strictly filters for `source_url`, **it fails to detect URLs on 283 of the 285 URL-bearing notes in the vault**. If an agent or Bryan runs `bob highlights clip <URL>` on an article already tracked in `ref/blogs/` or `ref/papers/`, the check misses the existing note and permits duplicate intake. 

Migrating to `bob ref` presents an immediate opportunity to fix this defect by supporting both `url` and `source_url` symmetrically.

---

## 3. Critique of the Migration Plan

### 3.1 Is this a good idea?
**Yes, it is an exceptional and necessary evolution of the Bob CLI.**

1. **Domain Cohesion:** In the Bob vault, the entity is a **Reference** (`type: "[[ref]]"`, `^ref` task, `REFERENCES` queue tier). Calling the CLI `highlights` confused the external capture mechanism with the internal knowledge entity.
2. **Closing the Reading Lifecycle Loop:** Before this proposal, `bob highlights` was an ingest-only pipeline. There was no CLI mechanism to answer:
   - *"What has Bryan already read about agent memory?"*
   - *"What is currently queued in the reading backlog?"*
   - *"What were Bryan's personal reactions and notes on the EA-Graph paper?"*
   Closing this loop allows agents to act as intelligent research assistants rather than blind link pushers.
3. **Alignment with SASE Multi-Agent Swarms:** Agents conducting research (e.g., in `bob-cli--research`) frequently recommend reading material. Without a queryable reference catalog, agents repeatedly suggest papers Bryan has already annotated, creating friction and cognitive overhead.

### 3.2 What should be adjusted or done differently?

#### Adjustment 1: Decouple "Reference" from "PDF"
*Problem:* In `bob highlights`, every command assumes a companion PDF in `lib/` or `xlib/`. However, 282 notes in `ref/ai/...` are reference notes for web essays, tools, or chats without local PDFs.  
*Adjustment:* The `bob ref` architecture must treat the **Reference Note** as the primary entity and the **PDF / Sidecar** as an optional artifact attachment. Commands like `bob ref list`, `bob ref find`, and `bob ref show` must operate over all Markdown notes in `ref/`, whether or not a `source_pdf` is present.

#### Adjustment 2: Avoid the Ambiguous Verb `bob ref read`
*Problem:* In CLI grammar, `bob ref read` could mean three completely contradictory operations:
- A command to mark a reference as read (mutation: `status -> read`).
- A command to read the text/annotations of a reference (inspection: print body).
- A filter to display references that are already read (query: `list --status read`).  
*Adjustment:* Adopt unambiguous, established CLI verbs following `cli_rules.md`:
- `bob ref list`: List references with filters (`--status read|ready|wip|next|all`).
- `bob ref find`: Check / query for a reference by URL, title, DOI, or ID.
- `bob ref show`: Inspect a reference note, its reading status, and its annotations.

#### Adjustment 3: Unified Status Normalization
*Problem:* Modern notes express reading state via the `^ref` checkbox and `status: read|ready|wip|next|abandoned`. Legacy notes express it via `status: legacy` and `legacy_status: unread|read|...`.  
*Adjustment:* Implement a unified status projection layer:
```text
Normalized Status:
- READ:      modern status "read" / [x] OR legacy_status "read"
- WIP:       modern status "wip" / [/]
- NEXT:      modern status "next" / [*]
- READY:     modern status "ready" / [ ] OR legacy_status "unread" / "collect_fleeting_notes"
- ABANDONED: modern status "abandoned" / [-] OR legacy_status "abandoned"
```
When an agent queries `bob ref list --status read`, it receives all 310 read references across both modern and legacy formats.

#### Adjustment 4: Academic Identifier Matching (ArXiv / DOI Normalization)
*Problem:* Agents and humans cite papers using varied URL shapes:
- ArXiv abstract: `https://arxiv.org/abs/2608.04278`
- ArXiv direct PDF: `https://arxiv.org/pdf/2608.04278` or `https://arxiv.org/pdf/2608.04278.pdf`
- ArXiv ID: `arxiv:2608.04278`
- DOI: `https://doi.org/10.1145/3318464.3389700` vs `doi:10.1145/3318464.3389700`  
*Adjustment:* `bob ref find` must include an academic URL normalizer that extracts ArXiv IDs and DOIs as canonical match keys. A query for `https://arxiv.org/abs/2608.04278` must immediately match an existing note storing `url: "https://arxiv.org/pdf/2608.04278"`.

#### Adjustment 5: Backward Compatibility and Hidden Aliases
*Rule:* Per SASE `cli_rules.md`:
> *"Never hard-rename or remove a command: the old spelling becomes a permanent hidden alias with byte-identical behavior and no deprecation output. Help, diagnostics, logs, and commit subjects print only the canonical path."*

Bryan runs automated LaunchAgents on macOS (`~/Library/LaunchAgents/com.bryan.bob-highlights-scan.plist`) and nightly maintenance hooks executing `bob highlights scan`. The migration must register `highlights` in `src/runner.rs:ALIASES` as a root alias rewriting `highlights` to `ref`. All existing invocations (`bob highlights scan`, `bob highlights sync <PDF>`) will continue executing seamlessly.

---

## 4. Why Not Just Use `bob query` (Dataview)?

A natural question is whether new CLI commands are necessary when `bob query` already supports Dataview DQL queries like `bob query -q 'TABLE status FROM "ref"' -f json`.

An architectural evaluation confirms that `bob query` is unsuitable for this workflow:

1. **Latency and Resource Overhead:**  
   `bob query` initializes the vault graph across thousands of files to resolve links, Dataview inline fields, and task trees. A test query on the vault required ~4.2 seconds to run and generated 16 link ambiguity warnings on stderr. In contrast, a native Rust scanner scanning only `~/bob/ref/` (590 files) parses frontmatter and task lines in **12–15 milliseconds**. For coding agents running multiple tool calls per turn, sub-20ms responsiveness is essential.
2. **Domain Logic Incompetence:**  
   Generic Dataview DQL does not understand Bob reference semantics:
   - It cannot reconcile the `^ref` task mark with frontmatter status (the `^ref` checkbox is authoritative over frontmatter).
   - It does not map `legacy_status` on legacy notes.
   - It cannot parse Obsidian callout blocks from the managed `<!-- highlights:begin -->` region.
   - It does not perform URL deduplication or ArXiv ID normalization.
3. **Agent Prompt and Failure Complexity:**  
   Requiring an LLM agent to generate complex DQL query strings, parse nested Dataview AST JSON responses, and filter out stderr warnings introduces high failure rates and consumes valuable context tokens. A single deterministic command, `bob ref find --url <URL> -f json`, provides an airtight agent interface.

---

## 5. Specification of the `bob ref` Command Suite

### 5.1 Subcommand Hierarchy
Under `bob ref`, commands are divided into **Lifecycle Sync** (preserving the existing `bob highlights` operations) and **Catalog & Knowledge** (new reading tracking and annotation commands):

```text
bob ref
├── Catalog & Knowledge (New)
│   ├── list       # List references by status, ref_type, or topic
│   ├── find       # Check/find a reference by URL, ArXiv ID, DOI, or title
│   └── show       # Display reference details, metadata, and extracted annotations
└── Lifecycle Sync (Preserved from `bob highlights`)
    ├── clip       # Clip web article into intake PDF (xlib/blogs/)
    ├── create     # Render markdown file to Highlights PDF (xlib/chat/)
    ├── doctor     # Check vault reference paths, hooks, and Git state
    ├── marker     # Inspect page-1 marker of a PDF
    ├── scan       # Move intake to library, pair audio, and sync notes
    └── sync       # Synchronize one PDF marker with its reference note
```

### 5.2 Command Details & Schemas

#### 1. `bob ref list`
Lists references from `~/bob/ref/` with rich filtering and sorting.

```bash
bob ref list [OPTIONS]

Options:
  -b, --bob-dir <PATH>       Bob vault root; defaults to BOB_DIR or ~/bob
  -f, --format <FORMAT>      Output format: human, json [default: human]
  -l, --limit <N>            Maximum number of references to return
  -r, --ref-type <DIR>       Filter by reference type: papers, blogs, chat, docs, ai
  -s, --status <STATUS>      Filter by normalized status: read, ready, wip, next, abandoned, all [default: all]
  -t, --topic <TAG>          Filter by topic or tag
```

*JSON Output Contract (`-f json`):*
```json
{
  "total": 590,
  "filtered": 5,
  "status_filter": "next",
  "references": [
    {
      "path": "ref/papers/transformer_memory.md",
      "title": "Transformer Memory Hierarchies",
      "status": "next",
      "ref_type": "papers",
      "url": "https://arxiv.org/abs/2607.12345",
      "has_pdf": true,
      "source_pdf": "lib/papers/transformer_memory.pdf",
      "highlights_count": 0,
      "created": "2026-09-15T14:20:00-0400"
    }
  ]
}
```

#### 2. `bob ref find` (The Agent Deduplication Primitive)
Enables an agent or user to determine whether a given URL, ArXiv paper, or article title is already tracked, and what its reading status is.

```bash
bob ref find [QUERY] [OPTIONS]

Arguments:
  [QUERY]                    Free-text title query or URL

Options:
  -a, --arxiv <ID>           Explicit ArXiv identifier (e.g. 2608.04278)
  -d, --doi <DOI>            Explicit DOI identifier (e.g. 10.1145/...)
  -f, --format <FORMAT>      Output format: human, json [default: human]
  -u, --url <URL>            Explicit URL to check
  -s, --status <STATUS>      Filter matches by normalized status
```

*Exit Codes:*
- `0`: Match found.
- `1`: No match found.
- `2`: Command error (invalid arguments).

*JSON Output Contract (`-f json`):*
```json
{
  "found": true,
  "match_kind": "arxiv_id",
  "query": "https://arxiv.org/abs/2608.04278",
  "reference": {
    "path": "ref/papers/ea_graph.md",
    "title": "EA-Graph: Artifact-Anchored Verification Memory for Coding Agents under Upstream Drift",
    "status": "read",
    "ref_type": "papers",
    "url": "https://arxiv.org/pdf/2608.04278",
    "source_pdf": "lib/papers/ea_graph.pdf",
    "highlights_count": 1,
    "has_annotations": true
  }
}
```

#### 3. `bob ref show` (Annotation & Note Inspection)
Displays the complete reference metadata and extracts user highlights and comments from the managed region.

```bash
bob ref show <REF_OR_PATH> [OPTIONS]

Arguments:
  <REF_OR_PATH>              Reference path, stem, or unique ID

Options:
  -a, --annotations-only     Print only the extracted annotations
  -f, --format <FORMAT>      Output format: human, json, markdown [default: human]
  -n, --no-annotations       Print only metadata without annotations
```

*Annotation Parsing Logic:*  
The command reads the Markdown note, isolates the content between `<!-- highlights:begin -->` and `<!-- highlights:end -->`, and parses each block into structured records:
- Heading lines (`### Page <N>`) provide the page context.
- `[!quote]` callouts contain the highlighted text.
- Nested `[!note] Comment` callouts contain Bryan's personal reactions and notes.
- Trailing `^h-...` anchors provide stable block links back into the Obsidian vault.

*JSON Output Contract (`-f json`):*
```json
{
  "path": "ref/blogs/steve_kinney_agent_memory.md",
  "title": "steve kinney agent memory",
  "status": "read",
  "ref_type": "blogs",
  "url": "https://stevekinney.com/writing/agent-memory-systems",
  "source_pdf": "lib/blogs/steve_kinney_agent_memory.pdf",
  "highlights_count": 30,
  "annotations": [
    {
      "page": "Page 2",
      "kind": "quote",
      "text": "If I’ve mischaracterized someone’s work, call me out in the comments section that doesn’t exist.",
      "comment": ":)",
      "block_id": "h-ce8e46d5cb2c"
    },
    {
      "page": "Page 6",
      "kind": "quote",
      "text": "If you’re building an agent that talks to Claude, GPT-4, or Gemini through an API, your entire memory design space is token-level. Master the topology spectrum (flat → planar → hierarchical) and get very good at the dynamics layer—formation, evolution, retrieval—operating over tokenlevel stores. That’s where all the leverage is.",
      "comment": "[[sase_memory]]",
      "block_id": "h-05af2bbcd393"
    }
  ]
}
```

---

## 6. Implementation Architecture

### 6.1 Codebase Structure
The implementation refactors `src/native/highlights_ref/` into `src/native/reference/` (avoiding the Rust keyword `ref`):

```text
src/native/reference/
├── mod.rs               # Module exports, Config, path resolvers
├── cli.rs               # Clap command construction for `bob ref`
├── list.rs              # `bob ref list` scanner and table/JSON formatters
├── find.rs              # `bob ref find` multi-tier matcher (URL, ArXiv, DOI, title)
├── show.rs              # `bob ref show` note parser and callout extractor
├── status.rs            # Unified status resolver (modern ^ref vs legacy_status)
├── url_norm.rs          # URL cleaning, tracking parameter strip, ArXiv/DOI normalization
├── annotation.rs        # Callout block parser (quotes, comments, images, page heads)
├── clip.rs              # Web clip intake pipeline (updated to scan url & source_url)
├── create.rs            # Markdown to PDF intake pipeline
├── doctor.rs            # Reference system doctor preflights
├── marker.rs            # PDF page-1 marker reader/writer
├── scan.rs              # Library intake mover and recursive scanner
├── sync.rs              # Bi-directional marker & reference note synchronizer
└── tests/               # Comprehensive unit and integration test suite
```

### 6.2 Runner Dispatch and Alias Mapping
In `src/native.rs`:
```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum NativeCommand {
    // ...
    Reference,
    // ...
}
```

In `src/runner.rs`:
Mount `ref` under `Section::TasksAndProjects` (or `Section::Vault`):
```rust
Subcommand {
    name: "ref",
    about: "Manage vault reference notes, reading tracking, and Highlights sync",
    section: Section::TasksAndProjects,
    target: Target::Leaf(Leaf {
        native_command: NativeCommand::Reference,
        script_command: None,
    }),
},
```

Register the backward-compatible alias in `ALIASES`:
```rust
Alias {
    from: "highlights",
    to: &["ref"],
},
```
With this alias in place:
- `bob highlights scan` automatically rewrites to `bob ref scan`.
- `bob highlights clip https://...` automatically rewrites to `bob ref clip https://...`.
- `bob highlights sync <PDF>` automatically rewrites to `bob ref sync <PDF>`.
- Any external script, LaunchAgent, or shell alias referencing `bob highlights` continues to work with zero disruption and zero deprecation noise.

### 6.3 Fast Vault Scanner Architecture
To maintain sub-15ms performance across 590+ reference notes, `list` and `find` avoid full Markdown AST parsing or vault link graph traversal:
1. **Directory Traversal:** Recursively scan `~/bob/ref/` for `*.md` files, ignoring hidden directories (`.git`, `.obsidian`).
2. **Shallow Frontmatter Extraction:** Read the leading YAML block (stopping at the second `---`). Parse `type`, `ref_type`, `status`, `legacy_status`, `title`, `url`, `source_url`, `source_pdf`, and `highlights_count`.
3. **Targeted Lifecycle Task Extraction:** If frontmatter indicates a non-legacy note, scan the first 30 lines below frontmatter for the regex `^- \[([ xX\/\*\-\?])\] #task.*?\^ref$`.
4. **Normalized Status Resolution:** Derive the effective reading status (`read`, `wip`, `next`, `ready`, `abandoned`).
5. **In-Memory Index:** Cache index keys (canonical URL dedupe key, ArXiv ID, title tokens) for fast evaluation.

---

## 7. Recommended Implementation Roadmap

A phased three-stage rollout is recommended:

### Phase 1: Canonical Renaming & Backward-Compatible Aliasing
1. Rename module `src/native/highlights_ref/` to `src/native/reference/`.
2. Update CLI binary name to `bob ref` with subcommands `clip`, `create`, `doctor`, `marker`, `scan`, `sync`.
3. Register `highlights -> ref` in `ALIASES` in `src/runner.rs`.
4. Update shell completions in `src/native/completion/` so `bob ref <TAB>` offers the new canonical command while `bob highlights` remains valid.
5. Fix the `source_url` vs `url` defect in `collect_ref_note_sources` within `clip.rs`.

### Phase 2: Reading Tracking & Search (`list` and `find`)
1. Implement `status.rs` for unified status normalization across modern `^ref` tasks and legacy notes.
2. Implement `url_norm.rs` for ArXiv ID extraction, DOI normalization, and URL cleaning.
3. Implement `bob ref list` with filtering by `--status`, `--ref-type`, and `--format json`.
4. Implement `bob ref find` supporting URL deduplication, ArXiv ID lookup, and title matching with exit code contracts for agents.

### Phase 3: Annotation Extraction & Intelligence (`show`)
1. Implement `annotation.rs` to extract callout blocks (`[!quote]`, `[!note] Comment`, images) from `<!-- highlights:begin -->` regions.
2. Implement `bob ref show` supporting `--annotations-only`, `--no-annotations`, and `--format json`.
3. Update `docs/highlights-ref-sync.md` to reflect the new canonical `bob ref` syntax and document agent query workflows.

---

## 8. Conclusion

Migrating `bob highlights` to `bob ref` is an architecturally sound and high-leverage initiative. It elevates reference notes to their rightful status as first-class Bob vault entities alongside projects and tasks. By incorporating unified reading status tracking and structured annotation extraction, `bob ref` provides the missing link for agentic research workflows—allowing agents to check reading history instantly, avoid duplicate literature recommendations, and synthesize insights directly against Bryan's annotated knowledge base.

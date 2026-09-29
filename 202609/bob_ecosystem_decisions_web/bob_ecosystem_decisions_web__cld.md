# A `decisions` Memory Web for the Bob Ecosystem

- **Date:** 2026-09-29
- **Researcher:** `cld` (one of five independent researchers in this swarm)
- **Scope under study:** `bob-cli` (host SASE project), its linked repos `bob-plugins` and
  `bob-mac-capture`, and the Bob Obsidian vault (`~/bob`, `bobs-org/bob`)
- **Question:** Should Bryan add a SASE memory web of architecture and policy decisions,
  modeled on the `sase` project's `decisions` web? If so, how should it be built, which
  records should it launch with, and what should change in the plan?

**Recommendation in one line:** Yes, build it. Put one `decisions` web in **bob-cli's
project memory**, not in home memory and not one per repo. Copy the sase format exactly,
with three additions:

- Each roster summary is itself an enforceable rule.
- Every record has a scope tag and at least one pinned piece of evidence.
- Records must pass a strict admission test.

Launch it with the **10 records** in §6.1, after Bryan answers the **3 confirm-first
questions** in §6.2. Do not attempt a full back-catalog.

---

## 0. Executive summary

| # | Finding | Consequence |
| --- | --- | --- |
| 1 | **The sase web is a small, well-specified format, not a subsystem.** It is one descriptor plus one file per record. Each record's body has four parts: Claim / Why / Cost / Reopens when. Records never change once accepted; supersession is a `metadata` mark. It launched with 6 records on 2026-08-24 and had 24 five weeks later. | Everything needed already ships in `sase`. No code changes are required. (§1) |
| 2 | **Agents read decision records, but mostly the operational ones.** I excluded this swarm's own reads from sase's read log. What remains is 110 strand reads, the earliest on 2026-09-01. `record-before-admit` (17), `two-speed-verification` (14) and `guarded-recipes` (10) lead. Records about memory internals got 1–2 reads each. | Much of the value comes from the always-loaded roster summaries, and bodies get read when a record governs the task at hand. So bob's records should target the rules agents actually trip over. (§1.4) |
| 3 | **A home-scoped web called `decisions` would leak into sase.** Reads merge a home web and a project web of the same slug strand by strand (`src/sase/memory/web/scope.py`). Every `sase memory read decisions:…` in the sase project would then see vault records. The home `~/AGENTS.md` roster would also load in every project. | Host the web in **bob-cli project memory**. (§3.2) |
| 4 | **bob-cli is the only SASE project in the Bob ecosystem.** `sase project list` shows only `bob-cli` and `sase`. 133 of bob-plugins' 146 commits carry SASE agent trailers that point to bob-cli's plans and beads repos. bob-mac-capture commits reference `bob-cli--agents` 115 times. | Agents working on the linked repos already run from bob-cli workspaces, so they will see the roster. (§2.1) |
| 5 | **bob-mac-capture has no `AGENTS.md`.** bob-plugins' `AGENTS.md` is 3 lines. | Add pointer lines that use `sase memory read -p bob-cli decisions:<kw>`, so agents started inside those checkouts can still reach the records. (§5.6) |
| 6 | **UI-level decisions churn too fast for records that never change.** Examples: the `\p` keymap was reversed after 47 minutes (`13eb4d6` → `1de6f93`). Ctrl-J was rebound three times in four days. The task-toggle default was swapped. Blocked went from `[B]` to `[*]` and then came back as `[?]` within 8 days. | Record the **stable meta-decisions** behind this churn. Leave keymaps and grammar punctuation to `docs/`. (§4, §6.4) |
| 7 | **The rationale is already written down, but scattered.** 41 plans in the plans sidecar have a "Decisions" section. Seven research syntheses, many commit bodies, and README asides also carry it. Agents do not read any of these routinely. | This scattering is the real problem the web solves, and the harvest pipeline in §5.7 draws on these sources. |
| 8 | **Mirroring between repos has no declared owner, and it has already drifted.** bob-cli's Rust constants say they mirror `main.js` (`src/native/capture_schedule_log.rs:22`), and the plugins say they mirror `capture.rs`. Schedule Log entry emphasis is `_` in `block-id-prompt` but `*` in `bob-navigation-hotkeys`, `task-status-cycler` and bob-cli. `bob-project-tasks` ignores `[?]` when counting open tasks. | This is the most valuable decision **not yet made**. Bryan must settle it before it can be recorded. (§6.2 Q1) |
| 9 | **Two docs now contradict each other.** bob-plugins' `README.md` says making the repo the sole source of truth is "a deliberate later decision". Home `obsidian.md` says the custom `bob-*` plugins are already gitignored in the vault. The bob-cli `README.md` Environment section also leaves `gkeep pull` out of the list of commands that take the lock, although `src/native/gkeep/pull.rs:131` does take `bob_sync.lock`. | Writing the records will surface drift like this, which is a side benefit. Fix these as part of the rollout. (§4 R7) |

---

## 1. What the sase `decisions` web actually is

### 1.1 Files and frontmatter

The web is one flat descriptor plus a sibling directory of strands. The descriptor's
frontmatter (from `sase/memory/decisions.md` at sase `HEAD`):

```yaml
---
web: true
description:
  Architectural decision records — accepted choices, their rejected alternatives, and
  what would reopen them.
roster: list
roster_label: DECISIONS
strand_noun: decision
---
```

Descriptor keys the parser accepts (`src/sase/memory/web/frontmatter.py`):

- `web`, `roster` (`inline` | `list`), `roster_label`, `strand_noun`, `description`
- `priority`, `metadata`, `link_reference`, `link_rendering`

A descriptor must not declare `type:` or `parent:`; `sase memory init` strips both.

Strand keys:

- `keyword` (the display title), `aliases` (a list), `summary` (the roster line)
- `metadata` (a free-form mapping)
- `link_reference`, `link_rendering`

A strand must not declare `type` or `parent`.

### 1.2 Body convention

Every sase record uses the same four paragraphs:

- **Claim.** The decision as it stands, in present tense.
- **Why.** The evidence, with commit hashes and dates, `research:` / `plan:` refs, or
  measurements. It names each *rejected alternative* and says why it lost.
- **Cost.** What the project gives up by choosing this.
- **Reopens when.** An observable trigger. Good examples:
  - `check-full-is-explicit`: "Selection-health shows the heuristic is materially wrong"
  - `v1-import-retired`: "zero pending legacy-v1 hoods"

  A weak trigger is one like "if we change our minds".

### 1.3 Mechanics that matter for a copy

- **Rendering.** The descriptor body plus a numbered roster renders into a
  `## 3. Memory Webs` subsection of `AGENTS.md` and every provider shim. Each roster
  entry is `**Keyword** (\`slug\`) - summary`, so the roster is always in context.
  Strand bodies are read only on demand, with
  `sase memory read decisions:<keyword|alias|slug-prefix> -r "<why>"`.
- **Supersession.**
  - The older record gets `metadata.status: superseded | superseded-in-part` plus
    `superseded_by: [...]`. Its body also gets a `[[...]]` back-link.
  - The roster then shows `_[superseded by …]_`.
  - sase keeps superseded records rather than deleting them, for example
    `v1-import-retired` and `two-speed-verification`.
- **Links.** `[[decisions/<slug>]]` or `[[glossary:<term>]]` renders a numbered "Linked
  References" list. `![[…]]` renders the target inline.
- **Growth.** The web shipped with six records (`0adb544096`, 2026-08-24, epic `sase-sq`)
  and reached 24 by 2026-09-28. That is roughly one record per epic that makes a durable
  choice.
- **Cost in context.** The rendered sase roster, with 24 records and the descriptor, is
  858 words (6,292 characters, about 1,500 tokens). That averages about 31 words per
  entry.

### 1.4 Evidence that agents use it

This data comes from sase's read log (`memory_reads.jsonl`, 1,318 events). I excluded
today's `research.r.*` reads, so this swarm is not counted.

| Strand | Reads | Distinct agents |
| --- | ---: | ---: |
| `record-before-admit` | 17 | 17 |
| `two-speed-verification` | 14 | 13 |
| `guarded-recipes` | 10 | 10 |
| `rust-core-required`, `ci-two-speed-split`, `size-alias-effort-ladder` | 7 each | 6–7 |
| … | … | … |
| `memory-webs`, `explicit-handoff-fails-closed`, `memory-links-are-authored`, `triage-annotates…` | 1–2 each | 1–2 |
| **Total** | **110** | — |

What this means:

- **The records that get read govern what an agent does next.** Examples are which
  verification recipe to run and whether to wrap a command. Records that describe
  internal machinery are rarely read.
- **The roster summary does most of the work.** It is loaded on every turn. A body is
  opened when an agent is about to act in that area. Nobody reads bodies for
  background knowledge.
- **bob-cli agents already use webs.** Since 2026-09-03, bob-cli agents have read the
  4-strand glossary about 57 times, alongside `obsidian.md` (10) and `cli_rules.md`
  (30).

---

## 2. The Bob ecosystem, as it bears on this design

### 2.1 Where agents run and what they see

- **Only two SASE projects exist,** `bob-cli` and `sase`. bob-plugins and
  bob-mac-capture are *linked repos* of bob-cli. Both linked checkouts are uncloned at
  their configured primary paths (`~/projects/github/bobs-org/...`). Agents reach them
  through `sase repo open`.
- **bob-plugins:** 146 commits (2026-06-20 → 2026-09-24). 133 of them carry SASE
  trailers linking to `bob-cli--plans`, `bob-cli--beads` and `bob-cli--agents`.
- **bob-mac-capture:** 124 commits (2026-08-13 → 2026-09-29), with 62 plan refs, 57
  bead refs and 115 agent refs, all to bob-cli sidecars. It has **no** `AGENTS.md` or
  `CLAUDE.md`.
- **Vault rules any agent may need** already live in home memory. `~/sase/memory/obsidian.md`
  covers the `parent` frontmatter rule, git-only sync, conflict copies and gitignored
  trees. It is a reference note, listed from `~/AGENTS.md`, so every project sees it.
- **Current bob-cli memory:**
  - core `sase.md`
  - generated `task_types`
  - a 4-strand `glossary` web
  - reference notes `cli_rules.md`, `sase_artifacts.md`, `sase_beads.md`

  `sase memory list` reports about 2,769 loaded tokens.

### 2.2 Churn and reversals: the case for the web, and for filtering it

| Reversal | Evidence | Durable? |
| --- | --- | --- |
| Obsidian Sync restore → git-only sync, same day | Epic `bob-cli-1l` "Restore Bob Obsidian Sync… sub-1 GB footprint policy" was closed as *superseded* by `bob-cli-1n` on 2026-08-27. | **Yes.** This is architecture. |
| Authored `[B]` Blocked → `[*]` Next → derived `[?]` Blocked | bob-plugins `890ed13` (2026-07-08, `feat!`), then `36296ec` (2026-07-16) | **Yes.** It defines the status model. |
| SwiftUI `App` entry point → AppKit delegate hosting SwiftUI | bob-mac-capture `a3e620b`, then `221783e` (both 2026-08-14) | **Mostly.** It is an app-shell choice. |
| `@route::id` → `@route^id` / `@route+id` | bob-cli `2bdf4f7` (2026-08-15, `feat(capture)!`) | **No.** Grammar punctuation is owned by `docs/capture.md`. |
| Task-toggle default swapped (bare `@route+id` = Ensure Next; `!` = toggle) | README §Capture: "note this reversal"; plan `swap_task_toggle_defaults` | **No.** It is a UX detail. |
| `\p` pin keymap reverted after 47 minutes | bob-plugins `13eb4d6` → `1de6f93` (2026-07-12) | **No.** |
| Ctrl-J rebound three times | bob-mac-capture `78315d9`, `e5d7306` (2026-09-07), `c6273cf` (2026-09-10) | **No.** |

Two things follow from this table:

- **Agents relitigate these choices often,** and so does Bryan, sometimes on the same
  day. A record that says what was rejected and why is exactly the tool for that.
- **A record that never changes cannot track UI preferences.** A record that has to be
  superseded weekly is noise.

---

## 3. Critique: is this a good idea?

### 3.1 Yes, for five reasons

1. **The rationale exists but is unreachable.** It is spread across 41 plan "Decisions"
   sections, 7 research syntheses, `feat!` commit bodies and README asides such as
   "deliberate later decision". No agent reads those by default. A roster summary is
   loaded on every turn.
2. **Several of these rules are ones a capable agent would break on purpose, in good
   faith.** Examples:
   - adding TypeScript and a bundler to bob-plugins
   - extracting the copied plugin helpers into a shared module
   - porting capture grammar to Swift "for latency"
   - bumping `schema_version` for a new field
   - running `git reset --hard` on a wedged vault
   - making `bob randomize` run nightly
   - adding `import os` to `CaptureCore`

   Every one of these was a considered rejection. Most are invisible from the code
   alone.
3. **The system spans four codebases and a data store,** with contracts between them:
   capture JSON, vault format rules, the maintenance lock. Cross-repo invariants are
   what per-repo docs handle worst.
4. **The format is proven and costs no code.** sase built it, validates it
   (`sase memory init` and `sase doctor`), and has used it for five weeks.
5. **Writing records forces open questions to close.** Finding 8 (who owns the vault
   format rules) is exactly that kind of question.

### 3.2 Risks, and what I would do differently

| Risk | Mitigation (my adjustment) |
| --- | --- |
| **Wrong scope.** A home web merges into sase's `decisions:` namespace at read time. It would also inline in every project through `~/AGENTS.md`. | Keep it project-scoped in bob-cli. Leave home `obsidian.md` as the vault-rules note for *every* agent. The web holds the *why*, for agents who change the machinery. |
| **Duplicating contracts.** bob-cli has 7,378 lines of `docs/` and a 900-line README. | A record states the choice, the rejected alternatives, the cost and the reopen trigger. It **links** to the contract and never restates it. |
| **Volatility.** Records that never change cannot track keymaps. | Use the admission test in §5.3. Record the stable principle, not the current binding. |
| **Token cost.** About 700 tokens every turn for 10 records, roughly +25% of bob-cli's loaded context. | Keep summaries to about 30 words and 10 records at launch. Grow only when an epic makes a durable choice. |
| **Invented rationale.** An agent writing records could guess a "Why" that Bryan never had. | Every record cites pinned evidence. Where the rationale is undocumented (§6.2), **ask Bryan** rather than infer. |
| **Linked-repo blind spot.** An agent started inside bob-mac-capture (for example on the Mac, the only place its UI builds) sees no bob-cli memory. | Add pointer lines to bob-plugins' `AGENTS.md` and a new, minimal bob-mac-capture `AGENTS.md`. |
| **Stale records.** | Supersede rather than edit, as sase does, and include a "Reopens when" trigger. Epic landers propose supersessions (§5.7). |

### 3.3 Alternatives considered

| Option | Verdict |
| --- | --- |
| **ADR files per repo** (`docs/adr/NNNN-*.md`, Nygard style) | **Rejected as the primary store.** They are not surfaced to agents (no roster), split across three repos, and have no audited reads or supersession annotations. A human-facing ADR view could be generated from strands later if wanted. |
| **One core note** (`bob_policies.md`, `type: core`) | **Rejected.** Every body is paid for on every turn, and there is no per-record addressing or supersession. |
| **One reference note** (`decisions.md`, `type: reference`) | **Rejected.** The rules are no longer visible without a read. It recreates the "inline everything or nothing" problem that sase's `memory-webs` record rejected. |
| **Home-scoped web** | **Rejected.** It would merge into sase's `decisions` web and load in every project (Finding 3). If one is ever wanted, it must use a different slug, such as `bob_decisions`. |
| **One web per repo** (`plugin_decisions`, `mac_decisions`, …) | **Rejected.** The most valuable records cross repos (contract, derived status, lock, thin client). It would also mean three rosters and three descriptors of token overhead. |
| **Extend the glossary** | **Rejected** for decisions: a glossary defines terms, not choices. **But** do add a glossary strand for the task-status vocabulary (§6.5). |
| **Do nothing** (plans, research and docs are enough) | **Rejected.** Finding 7: the knowledge exists and is not reaching agents. The drift in Findings 8–9 happened with those docs in place. |

---

## 4. Adjusted requirements (explicit changes to the ask)

| # | As asked | Adjusted | Why |
| --- | --- | --- | --- |
| **R1** | Record decisions for bob-cli, bob-plugins, bob-mac-capture and the vault | **Keep all four domains in one web, hosted only in bob-cli project memory** (`sase/memory/decisions.md` plus `sase/memory/decisions/*.md`). No home web, no per-repo webs. | Finding 3 (a home web leaks into sase). Finding 4 (bob-cli is the hub). Cross-repo records need one namespace. |
| **R2** | Heavily inspired by sase's web | **Copy the format verbatim** (descriptor keys, four-part body, records never change once accepted, `metadata.status` supersession) and **add three conventions**: (a) the summary is a rule, (b) a `metadata.scope` tag, (c) at least one pinned evidence ref per record. | (a) The roster is what is always read (§1.4). (b) Four domains share one namespace. (c) This guards against invented rationale. |
| **R3** | "More important architectural / policy decisions" | **Apply an admission test** (§5.3) that excludes keymaps, grammar punctuation, UI details and anything owned by a command contract. | §2.2: UX churn would force constant supersession. |
| **R4** | "Think hard about initial strands" | **Launch with 10 records** (§6.1). Hold 3 confirm-first items until Bryan answers (§6.2). Keep a named backlog (§6.3) instead of a big-bang back-catalog. | sase launched with 6 and grew one record per epic. That matches sase's own `corpus-before-mechanism` rule: do not build machinery ahead of a proven body of records. |
| **R5** | *(not asked)* | **Add reach-back pointers**: a short section in bob-plugins' `AGENTS.md` and a new minimal `AGENTS.md` in bob-mac-capture. Both say to read `sase memory read -p bob-cli decisions:<kw>` before changing an area a record governs. | Finding 5. `-p/--project` is supported by `sase memory read` today. |
| **R6** | *(not asked)* | **Add a capture habit.** When an epic lands a durable choice, its lander proposes a record or a supersession in the landing plan. The memory-write rules still gate the edit. | Keeps the web current without a periodic sweep. |
| **R7** | *(not asked)* | **Fix or file the doc drift the research found.** That is: the bob-plugins README sole-source note, the README Environment lock list missing `gkeep pull`, and the Schedule Log emphasis split. | Records must not cite docs that contradict them. |

---

## 5. Implementation design

### 5.1 Layout

```
sase/memory/decisions.md             # descriptor (web: true)
sase/memory/decisions/<slug>.md      # one record per file
```

Slug style: short kebab-case, claim-shaped (`git-only-vault-sync`, not `vault-sync`).
Scope does not need to be encoded in the slug: the roster sorts by keyword, and the scope
goes in `metadata.scope`.

### 5.2 Descriptor (draft)

```markdown
---
web: true
description:
  Durable architecture and policy decisions for bob-cli, bob-plugins, Bob Mac Capture,
  and the Bob vault — the choice, the rejected alternatives, and what would reopen it.
roster: list
roster_label: DECISIONS
strand_noun: decision
---

# Decisions

A decision record captures one durable choice for bob-cli, bob-plugins, Bob Mac Capture,
or the Bob vault. It is not a command contract (those live in `docs/` and each repo's
README) and not a keymap or UI preference. Each roster summary below is a rule to follow
as written; before changing the behavior a record governs, or proposing one of its
rejected alternatives, read it with `sase memory read decisions:<keyword> -r "<why>"`. A
record is immutable once accepted: when course changes, write a new record and mark the
old one with `metadata.status` plus `superseded_by` and a `[[...]]` back-link.
```

This is about 100 words, the same size as sase's descriptor.

### 5.3 Admission test

A decision gets a record only if **all four** hold:

1. **A credible alternative was rejected,** and the record can name it.
2. **An agent could plausibly choose that alternative** in good faith, without being
   told otherwise.
3. **The reason is not evident from the code or the command contract.**
4. **It is expected to hold for months.** If it has already flipped once, record the
   stable principle behind it, not the current setting.

Failing (1) means it is a *rule*. Rules belong in a flat note, such as the `parent`
frontmatter rule in `obsidian.md` or the CLI help rules in `cli_rules.md`. Failing (4)
means it belongs in `docs/`.

### 5.4 Record template

```markdown
---
keyword: <Title-Case Statement Of The Decision>
aliases:
  - <2–3 phrases an agent would search for>
summary: <≤ ~30 words, phrased as a rule an agent can obey without reading further>
metadata:
  scope: [bob-cli, vault]   # any of: bob-cli, bob-plugins, bob-mac-capture, vault
  decided: 2026-08-27       # optional: when the choice landed
---

**Claim.** <present-tense statement; name the files/commands it governs>

**Why.** <evidence with pinned refs (short hash + date, `research:`/`plan:` ref, or
path:line); name each rejected alternative and why it lost; link related records with
[[decisions/<slug>]] and terms with [[glossary:<term>]]>

**Cost.** <what we give up; include known drift or debt honestly>

**Reopens when.** <an observable trigger, not "if we change our minds">
```

Notes on the template:

- sase tooling ignores `metadata.scope` and `metadata.decided`. Frontmatter is stripped
  before rendering, so they cost no context tokens.
- They exist for humans and for `grep`, for example
  `grep -l 'bob-mac-capture' sase/memory/decisions/*.md`.
- Supersession uses the recognized `metadata.status` / `metadata.superseded_by` keys,
  exactly as in sase.

### 5.5 Summaries are rules

Compare two summaries:

- sase's `goal-ledger` summary ("A goal is its own Rust-owned domain, not a bead type…")
  informs.
- The `guarded-recipes` summary ("A SASE agent runs a guarded recipe only inside sase
  tool run… the guard refuses anything else") *directs*.

Read counts favor the directive style (§1.4), so each bob summary should say what to do
or never do. Examples are in §6.1.

### 5.6 Reach-back pointers (R5)

Add this to bob-plugins' `AGENTS.md`, and create the same text as a new bob-mac-capture
`AGENTS.md`:

```markdown
## Decisions

Architecture and policy decisions for this repo live in bob-cli's `decisions` memory web.
Before changing behavior a decision governs, read it:
`sase memory read -p bob-cli decisions:<keyword> -r "<why>"`
(list them with `sase memory web show -p bob-cli decisions`).
```

A one-line pointer in home `obsidian.md` is optional. It would lead from the vault
sync/conflict rules to their records. That file lives in the chezmoi linked repo, so it
is a separate change with its own authorization.

### 5.7 Keeping it current (R6)

- **Harvest sources, in order of yield:**
  1. the `feat!` / `BREAKING CHANGE` commit bodies
  2. epic plans with a "Decisions" section (41 so far)
  3. research syntheses
  4. superseded epics, such as `bob-cli-1l`
- **Trigger.** When an epic's landing plan records a durable choice, add a record step
  to that plan. Plan approval is the authorization the memory-write rules require. The
  lander writes the record, runs `sase memory init`, and commits.
- **Supersession.** A new record that reverses an old one marks the **old** record with
  `metadata.status`, `superseded_by` and a back-link. It never rewrites the old body.
- **Validation.** Run `sase memory init` (web validation blocks on errors) and
  `sase doctor` (warns on unresolved `[[…]]` links and supersession mismatches). Then
  run `sase memory web show decisions` to eyeball the roster.

### 5.8 Governance of the initial write

Under the `/sase_memory_write` rules, this research report does not authorize the edit.
The launch needs one of two things:

- Bryan asks for it directly in a prompt that names the files, or
- an approved `sase plan` whose steps name each file.

Those files are the descriptor, the 10 record files, the optional glossary strand, and
the two linked-repo `AGENTS.md` changes.

---

## 6. Which records to launch with

Ranking criteria:

1. how likely an agent is to break the decision
2. how much damage breaking it causes (vault data > cross-repo contract > code
   structure)
3. how strong the evidence is

Evidence was verified against the repos on 2026-09-29.

### 6.1 Launch set (10 records)

#### 1. `mac-capture-thin-client` — scope: bob-mac-capture, bob-cli

- **Keyword:** Bob Mac Capture Is A Thin Client Of `bob`
- **Summary (the rule):** Bob Mac Capture never parses capture grammar, computes
  previews, or writes vault Markdown; it runs `bob` and applies the returned ranges and
  results verbatim.
- **Claim:**
  - The app owns presentation, the hotkey, settings, running processes and packaging.
  - Grammar, completion, live preview and every vault write belong to bob-cli.
  - The app may only rank or fuzzy-filter snapshots that `bob` already returned.
  - It builds `obsidian://` URLs from Bob's `target` path, never from the typed grammar.
- **Why:**
  - The Hammerspoon predecessor had a *second, independent* grammar in
    `task_capture.lua` (353 lines, plus 487 lines of specs). That duplication was a
    named root cause in `research:202608/bob_mac_capture_replacement/bob_mac_capture_replacement.md`.
  - The rule is stated in bob-mac-capture `README.md:3-6` (present since `9030832`,
    2026-08-13) and at `:1025-1028`.
  - It is also stated in code: `Sources/CaptureCore/BlockIDRules.swift:5` says "Bob is
    the only authority for the grammar".
  - **Rejected:** a Swift port of the grammar, which would be a third implementation.
- **Cost:**
  - Every new feature lands in two ordered steps across two repos.
  - Preview runs as a subprocess: a 20 s timeout, and each lane cancels its previous
    run.
- **Reopens when:** subprocess latency measurably breaks live preview, or a feature
  needs state that JSON cannot carry.

#### 2. `capture-contract-additive-v1` — scope: bob-cli, bob-mac-capture

- **Keyword:** The Capture Editor Contract Grows Additively Within Schema v1
- **Summary:** bob-cli's capture JSON stays at `schema_version` 1 and only gains fields.
  Contract changes land in bob-cli first, with `docs/capture.md`, and frontends decode
  new fields leniently.
- **Claim:**
  - Never rename, remove or re-type a key in `capture-parse`, `-rewrite`, `-targets`,
    `-complete`, `-task-id` or `-pomodoro-name` output.
  - `bob capture --format json` has no `schema_version`. It uses an `ok` / `error`
    envelope.
  - The Mac app rejects `schema_version != 1` outright. It treats missing fields
    leniently.
- **Why:**
  - The two binaries are released independently and are routinely out of step.
  - `docs/capture.md` says it at lines 2122–2167 ("schema version 1 stays additive").
  - `2bdf4f7` (2026-08-15): "Semantic JSON stays on schema version 1".
  - `plan:202608/multi_capture.md`: "without bumping schema version 1… for tolerant
    existing clients".
  - Mac `CaptureModels.swift` has 243 `decodeIfPresent` calls against 38 strict
    `decode` calls.
  - Mac `fba0ffe` dropped a nonexistent `schema_version` from the `capture` decoder.
  - **Rejected:** a schema bump per feature, which would force lockstep releases.
- **Cost:**
  - Legacy fields pile up. For example, multi-capture keeps the first item's top-level
    fields.
  - A real v2 would need a period where both versions are emitted.
- **Reopens when:** a change cannot be expressed additively.

#### 3. `capture-draft-atomic` — scope: bob-cli, bob-mac-capture

- **Keyword:** A Capture Draft Is Planned Whole And Written All-Or-Nothing
- **Summary:** `bob capture` plans every item of a draft against in-memory note and
  ledger snapshots and writes all or nothing; frontends never split one draft into
  several mutating `bob` calls.
- **Why:**
  - `a8c9ad8` (2026-08-15, `feat(capture)!`).
  - `plan:202608/multi_capture.md`: "Plan the complete batch… commit all unique outputs
    as one transaction".
  - Mac `README.md:427-428`.
  - **Rejected:** sequential per-item writes, which leave partial state on failure and
    let later items miss earlier staged edits.
  - **Rejected:** client-side splitting.
- **Cost:**
  - The planner is more complex: shared ledger snapshots and reserved clip-asset
    names.
  - Breaking change: blank lines now separate items.
- **Reopens when:** a draft needs an interactive step between items.

#### 4. `git-only-vault-sync` — scope: vault, bob-cli

- **Keyword:** The Vault Syncs Through Git Only
- **Summary:** `bob vault-sync` on athena, apollo and the MacBook is the vault's only
  sync engine. Obsidian Sync and the Obsidian Git plugin's automation stay off, and
  exactly one engine may run.
- **Why:**
  - On 2026-08-27 Obsidian Sync failed 454 times in a row with `Vault limit exceeded`.
    The Standard plan's cap of under 1 GB includes version history.
  - athena is a headless server edited by cron and agents. The Obsidian Git plugin runs
    only while Obsidian is open, at minute granularity, and has no unattended conflict
    policy.
  - A git cycle measured about 10 ms locally and about 220 ms remote with
    `ControlMaster`.
  - Source: `research:202608/obsidian_vault_git_sync/obsidian_vault_git_sync.md`.
  - **Rejected:** restoring Obsidian Sync under a sub-1 GB footprint policy. That was
    epic `bob-cli-1l`, closed *superseded* by `bob-cli-1n` the same day.
  - **Retired:** `bob bulk-git-commit` (`4051bf5`). It never fetched, which was safe
    only while Obsidian Sync kept the tree converged.
  - Implementation and docs: `eee290a`, `f567500`, `docs/vault-git-sync.md`.
- **Cost:**
  - Changes take 5–15 s to propagate instead of under a second.
  - The gitignored trees (`xlib/`, `lit_review/`, custom `bob-*` plugins) do not
    travel. Plugins reach each machine through `bob plugins sync` instead.
  - Files of 95 MiB or more are refused.
- **Reopens when:**
  - a device that cannot run the service joins (a phone, for example), or
  - polling latency regularly causes real conflicts.

#### 5. `vault-conflicts-quarantine` — scope: vault, bob-cli

- **Keyword:** Sync Conflicts Quarantine The Local Copy; Nothing Rewrites Vault History
- **Summary:** On a supported conflict the remote version stays in place and the local
  copy goes to `_conflicts/`. Never leave conflict markers, `reset --hard`, force-push,
  or use `-X ours/theirs` on the vault.
- **Why:**
  - An unattended daemon merges files that Obsidian has open and that `bob` parses
    overnight. Conflict markers would break parsing.
  - Conflict copies would inject phantom tasks into `dash.md`'s vault-wide Tasks
    queries unless excluded. That is why `_conflicts/` is excluded from Bob's walkers,
    the Tasks global query and Dataview.
  - Sources: research above (§4, §5.4); `docs/vault-git-sync.md` "Conflict policy".
  - **Rejected:** git's default of markers and halting; ours/theirs strategies, which
    lose data silently; a "sentinel line" mitigation, tested and disproved in the
    research (§8.2).
- **Cost:**
  - A human must review `_conflicts/sync_conflicts.md`.
  - A local edit can temporarily live only in a copy.
- **Reopens when:** conflict copies become frequent enough to justify a custom merge
  driver.

#### 6. `one-maintenance-lock` — scope: bob-cli, vault

- **Keyword:** Unattended Vault Writers Share One Lock And Commit Only What They Wrote
- **Summary:** `vault-sync`, `nightly`, live `task-status-hooks`, `randomize` and
  `gkeep pull` serialize on `bob_sync.lock`. Bulk writers sync, write, commit exactly
  their files, then sync again. They never `git add -A`, amend, or push on their own.
- **Why:**
  - The lock path and its users are listed in the README Environment section
    (`BOB_VAULT_SYNC_LOCK_FILE`), `docs/vault-git-sync.md` and `docs/randomize.md`.
  - `src/native/gkeep/pull.rs:131` also takes it.
  - The randomize research, row R6: "Never amend, rebase, force-push, run `add -A`
    itself, or push directly".
  - **Rejected:** per-command `add -A` commits. This was the retired `bulk-git-commit`
    shape, and it sweeps unrelated edits into a misleading commit.
  - **Rejected:** per-command locks.
- **Cost:**
  - A long writer delays sync cycles.
  - Interactive `bob capture` and plugin edits are **not** under the lock. They rely on
    guarded compare-and-swap writes, so the record should say so.
- **Reopens when:** lock contention measurably delays sync.

#### 7. `task-status-is-derived` — scope: vault, bob-cli, bob-plugins

- **Keyword:** Next, In Progress, And Blocked Are Derived, Not Hand-Maintained
- **Summary:**
  - Today's Pomodoro ledger drives Next and In Progress.
  - Open dependencies or future `scheduled` dates drive Blocked `[?]`.
  - `bob task-status-hooks` reconciles them, so editors change the inputs, never only
    the checkbox.
- **Why:**
  - `docs/task-status-hooks.md`: the ledger is "the source of truth", and the previous
    daily note is read-only.
  - bob-plugins `786fc1d` (2026-08-17): a manual unblock must also clear the future
    `scheduled` date, or the hook re-blocks the task.
  - `9b534e3`: scheduled captures start Blocked.
  - The model settled through a reversal:
    - bob-plugins `890ed13` (2026-07-08, `feat!`) retired an authored `[B]` Blocked.
    - `36296ec` (2026-07-16) reintroduced Blocked as the *derived* `[?]`.
    - `9bb625a` (2026-07-24) added future schedules as a blocker.
  - **Rejected:** an authored Blocked status; per-editor status bookkeeping.
- **Cost:**
  - A hand edit of a derived checkbox is silently undone on the next run.
  - Every writer (capture, plugins, randomize, projects sync) must keep the inputs
    consistent.
- **Reopens when:** a status is needed that no ledger or schedule input can express.

#### 8. `refuse-dont-guess` — scope: bob-cli, bob-plugins, vault

- **Keyword:** Vault Writers Refuse On Ambiguity Instead Of Guessing
- **Summary:** When a vault write is ambiguous (duplicate fields, several open timed
  Pomodoros, a missing section, an ID collision), `bob` commands and plugins refuse or
  skip with a located warning. They never pick a best guess.
- **Why:** the vault is Bryan's system of record, and much of it is written unattended.
  The pattern recurs across repos:
  - `task-status-hooks` refuses on a missing daily note, a missing `Pomodoros` section,
    or several open timed Pomodoros (README).
  - `randomize` R3 is "Skip with a warning (never guess)".
  - The toggle rejects In Progress, done, missing, duplicate and non-task IDs "before
    any note is written".
  - `block-id-prompt/main.js:3056-3060` refuses in the same situations, and the
    migration scripts refuse on collisions.
  - `gkeep` never treats Keep text as capture grammar, and archives rather than
    deletes.
  - **Rejected:** best-effort repair heuristics.
- **Cost:** more refusals for Bryan to resolve by hand.
- **Reopens when:** one refusal class recurs and has a provably safe resolution. Then
  encode *that* resolution, not a general guess.

#### 9. `plugins-commonjs-standalone` — scope: bob-plugins

- **Keyword:** Bob Plugins Are Hand-Written CommonJS That Never Import Each Other
- **Summary:** Each plugin's `main.js` is the hand-edited source, with no TypeScript,
  bundler or build step. Plugins never `require` each other; shared logic is copied
  with a "Mirrors …" pointer and must stay byte-compatible.
- **Why:**
  - bob-plugins `README.md` §Development model: "intentionally no TypeScript, no
    bundler, and no build step".
  - `ef15fc6` (2026-06-20) set the layout up.
  - `block-id-prompt/main.js:82`: "Kept as an independent copy… plugins are deployed
    separately".
  - `bob plugins sync` copies exactly `manifest.json`, `main.js` and `styles.css`.
  - **Rejected:** the Obsidian TypeScript + esbuild sample layout; a shared package.
- **Cost:** copies drift, and it has already happened:
  - Schedule Log entry emphasis is `_` in `block-id-prompt` (`:90`) but `*` in
    `task-status-cycler` (`:519`) and `bob-navigation-hotkeys` (`:294`).
  - `bob-project-tasks` omits `?` from `OPEN_TASK_STATUSES` (`:15`).

  The record should say so honestly.
- **Reopens when:** drift in the copied helpers causes repeated bugs. The next step
  would then be a vendoring step that keeps the no-build deploy.

#### 10. `capturecore-linux-testable` — scope: bob-mac-capture

- **Keyword:** CaptureCore Is Foundation-Only So Linux Agents Can Build And Test It
- **Summary:** All non-UI logic lives in the Foundation-only `CaptureCore` target, which
  builds and tests on Linux. AppKit, SwiftUI and `os` imports live only in the app
  target, which only macOS CI verifies in full.
- **Why:**
  - `Package.swift:5-6`: "Linux hosts still build and test CaptureCore".
  - `Sources/BobMacCapture/Signposts.swift:4`: "CaptureCore may only import
    Foundation".
  - The mac replacement research, §7: SASE agents run on athena (Linux), "reframes the
    headless-core boundary from good taste to a workflow requirement".
  - Display logic lives in `*Presentation` structs (`CompletionRowContent.swift:129`).
  - **Rejected:** an Xcode project; logic in SwiftUI views.
- **Cost:**
  - More boilerplate in the presentation structs.
  - UI regressions surface only in `macos-26` CI or on the Mac itself.
- **Reopens when:** agents get a macOS toolchain.

**Roster budget.** 10 summaries at about 30 words each, plus the descriptor, comes to
about 400 words. That is about 700 tokens on every turn. It adds up to 1,200 more tokens
if all nine §6.3 backlog items are added later.

### 6.2 Confirm-first: decisions Bryan must make or explain before they are recorded

1. **Who owns the vault format rules?** This is the most valuable record, and it cannot
   be written yet.
   - The Mac app follows a strict thin-client rule (record 1).
   - bob-plugins *re-implement* bob-cli rules in JS and never shell out. No
     `child_process` is used anywhere, per the explorer's `grep -a`.
   - Mirroring runs **both ways**. bob-cli's `capture_schedule_log.rs:22` cites
     "`SCHEDULE_LOG_ENTRY_EMPHASIS` in main.js". `capture_task_toggle.rs:33` documents
     a deliberate `_` vs `*` divergence, with unifying the two "tracked as a follow-up".
   - No document says **why** plugins mirror instead of calling `bob`, or **which side
     is the reference**. Plausible reasons:
     - synchronous, single-undo editor transactions
     - latency on every keystroke
     - all six manifests declare `isDesktopOnly: false`, and mobile Obsidian has no
       `child_process`
   - I recommend a record once Bryan answers: "bob-cli's Rust is the reference for
     vault format rules. Plugins mirror in-process for editor-transaction reasons,
     every mirror cites its Rust source, and a rule change updates every mirror in the
     same epic." Do not write it on inference.
2. **Plugin source of truth.** bob-plugins' `README.md:165` still calls sole ownership
   "a deliberate later decision". Home `obsidian.md` says the `bob-*` plugins are
   gitignored in the vault, which suggests the decision was made during `bob-cli-1n`.
   - If so, write `plugins-deploy-via-bob` (repo is the source; the vault is a deploy
     target; `data.json` is never touched; git sync never carries plugins).
   - Then fix the README.
   - Note that the "never edit `~/bob/.obsidian/plugins`" *rule* is already in
     always-loaded core memory, so a record adds only the rationale.
3. **Native Rust, with the gkeep adapter as the template?**
   - Commands have been native Rust since `24d26c5` (2026-06-01). The shell scripts
     survive only as a rollback path behind `BOB_CLI_USE_SCRIPT=1`.
   - `bob gkeep` added a pinned Python adapter spawned through `uv` for a private
     protocol.
   - Is "native Rust; a foreign runtime only behind a pinned subprocess adapter" the
     standing policy for future integrations? If yes, it is a strong record, because
     agents often reach for Python.

### 6.3 Backlog: write each one when an epic next touches the area

| Candidate slug | One-line rule | Evidence |
| --- | --- | --- |
| `automation-reveals-never-replans` | Scheduled jobs surface state; they never reschedule or re-plan tasks. `randomize` runs only on demand. | `docs/randomize.md:308-310`; `research:202609/pomodoro_closed_day_now_tag_automation/…` ("Never rewrite the plan from cron") |
| `native-query-engine` | `bob query` evaluates Dataview and Tasks natively without Obsidian running. The live engine is opt-in. | `271fae6` (dynomark removed), `f401add` |
| `appkit-shell-swiftui-views` | The Mac app is an AppKit `LSUIElement` shell (NSStatusItem, pre-warmed NSPanel) hosting SwiftUI. It does not use a SwiftUI `App`/`MenuBarExtra` entry point. | `a3e620b`, `221783e` |
| `preview-never-mutates` | Preview always runs `--dry-run --no-clip` (enforced by `precondition`) with a per-draft pinned roll seed. | `BobProcessClient.swift` `preconditionLivePreviewArguments`; README:513-516 |
| `draft-text-private` | Draft text never reaches logs, UserDefaults, signposts or Diagnostics. | Mac README:1004-1028 |
| `bob-lookup-no-login-shell` | The app finds `bob` in fixed paths or an absolute override, never through a login shell. | Mac README:118; Hammerspoon `zsh -lc` per stage in the research |
| `managed-logs-never-auto-created` | Automatic flows prepend to an existing Schedule or Work Log but never create one. Legacy labels stay parseable. | bob-plugins `d6a9f26`, `786fc1d`; `main.js:268-275` |
| `path-qualified-dependency-ids` | `[id::]`/`[dependsOn::]` use note-qualified IDs because Tasks metadata is vault-wide. | bob-plugins `fc90f46`; README §Dependency identity |
| `gkeep-archive-after-proof` | Keep notes are archived only after their content is verified in the vault, and never deleted. | `docs/gkeep.md:174-180`; gkeep research |

### 6.4 Explicit non-candidates, and why

- **Keymaps and editor bindings** (Ctrl-J, `\p`, Ctrl+Shift+P …) fail test (4). They
  are owned by the READMEs.
- **Capture grammar punctuation** (`^` vs `+` vs `:`, the `!` toggle, `@@`) fails test
  (4). `docs/capture.md` is the contract. Records 1–3 hold the stable principles.
- **The `parent` frontmatter rule and route naming** are rules with no rejected
  alternative, so they fail test (1). Keep them in `obsidian.md` and the docs.
- **The CLI help, alias and sorting rules** are already in `cli_rules.md`.
- **"Rust files are at most 1,500 lines"** (epic `bob-cli-2f`) was a one-time refactor
  and is not enforced. `src/native/capture_complete.rs` is 2,937 lines. Recording it
  would create a **false** record.
- **`#hide` instead of `[p::2]`** (`7ce29ea`) is too small, and the breaking-change
  note already documents it.

### 6.5 Adjacent change (optional, same plan)

Add a glossary strand, `glossary:task-status`, for the vocabulary itself:

| Marker | Status |
| --- | --- |
| `[ ]` | Ready |
| `[*]` | Next |
| `[/]` | In Progress |
| `[?]` | Blocked |
| `[x]` | Done |
| `[-]` | Canceled |

Record 7 links to it with `[[glossary:task-status]]`. The vocabulary is a definition,
not a decision, so it belongs in the glossary. The glossary is already bob-cli's most-read
web.

---

## 7. Open questions for Bryan

1. The three confirm-first items in §6.2: who owns the vault format rules, the plugin
   source of truth, and native Rust with the adapter template.
2. Record 4 should name the current sync topology: athena, apollo and the MacBook.
   `docs/vault-git-sync.md` and home `obsidian.md` agree on that set. The 2026-08-27
   research covered only athena and the Mac, and apollo was added later (`d1c5a68`).
   Confirm apollo's service is meant to be permanent.
3. Do you want `metadata.decided` dates backfilled from commit dates, or only on new
   records?
4. Should the lander of every `feat!` epic be *required* to propose a record or say
   "no durable decision", or only encouraged? I recommend encouraged. A requirement
   invites filler records.

---

## 8. Recommended solution

1. **Build one `decisions` memory web in bob-cli's project memory:**
   - files: `sase/memory/decisions.md` plus `sase/memory/decisions/<slug>.md`
   - scope: all four domains (bob-cli, bob-plugins, bob-mac-capture, the vault)
   - **not** home-scoped, because a home `decisions` web would merge into sase's
     namespace
   - **not** one web per repo, because the best records cross repos
2. **Copy sase's format verbatim:**
   - descriptor keys `web`, `roster: list`, `roster_label: DECISIONS`,
     `strand_noun: decision`
   - the four-part Claim / Why / Cost / Reopens-when body
   - records never change once accepted, and supersession uses `metadata.status` +
   `superseded_by`
3. **Add three bob conventions:**
   - every summary is an obeyable rule
   - `metadata.scope` (and optionally `decided`) on every record
   - at least one pinned evidence ref per record
4. **Apply the four-part admission test in §5.3.** Keep keymaps, grammar punctuation
   and UI details out.
5. **First, get Bryan's answers to the three questions in §6.2.** They cover who owns
   the vault format rules, the plugin source of truth, and native Rust with the adapter
   template.
6. **Launch with the 10 records in §6.1,** in this order:
   1. `mac-capture-thin-client`
   2. `capture-contract-additive-v1`
   3. `capture-draft-atomic`
   4. `git-only-vault-sync`
   5. `vault-conflicts-quarantine`
   6. `one-maintenance-lock`
   7. `task-status-is-derived`
   8. `refuse-dont-guess`
   9. `plugins-commonjs-standalone`
   10. `capturecore-linux-testable`

   Also add any §6.2 records Bryan confirms, and optionally `glossary:task-status`.
7. **Add reach-back pointers** in bob-plugins' `AGENTS.md` and a new bob-mac-capture
   `AGENTS.md`, using `sase memory read -p bob-cli decisions:<kw>`.
8. **Fix the drift this research found, in the same rollout or as beads:**
   - the bob-plugins README note on sole source of truth
   - the README Environment lock list, which is missing `gkeep pull`
   - the Schedule Log `_`/`*` emphasis split
9. **Route the write through `/sase_memory_write`** with an approved plan that names
   every file. Then run `sase memory init` and `sase doctor`, and read back every
   record with `sase memory read decisions:<slug>`.
10. **Grow it by harvest, not by sweep.** Epic landers propose a record or a
    supersession when a plan's "Decisions" section contains a durable choice. Draw from
    the §6.3 backlog as each area is next touched.
11. **Revisit after about a month of use.** Check the read log. Supersede or delete
    records nobody reads, and tighten the summaries of those that are read.

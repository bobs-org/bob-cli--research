# A Decisions Memory Web for the Bob Ecosystem

**Researcher:** cdx  
**Date:** 2026-09-29  
**Scope:** `bob-cli`, `bob-plugins`, `bob-mac-capture`, and the Bob Obsidian
vault

## Executive conclusion

This is a good idea, with one important qualification: the web should be a
small, immutable decision log, not a second architecture manual and not a
catalog of every vault convention. The Bob ecosystem already has enough
cross-repository boundaries and non-obvious policies that future agents can
make locally reasonable but globally wrong changes. Examples include teaching
the macOS app its own capture grammar, editing deployed plugin copies in the
vault, enabling a second vault sync engine, or treating an Obsidian block ID as
vault-wide. A decision web would put the reasons those choices are wrong one
audited read away while keeping strand bodies out of every prompt.

I recommend one canonical project-local `decisions` web in `bob-cli`, because
`bob-cli` is already the integration hub and its SASE project knows about both
linked application repositories. Do not put the web in home memory: a home web
would charge every unrelated SASE project for Bob-specific context and could
create confusing project/home merges. Do not create three independent
decision logs initially: that would make cross-repository decisions hard to
find and supersede consistently. Instead, add tiny routing instructions in the
other repositories that point agents to the canonical web with
`sase memory read -p bob-cli decisions:<keyword>`. I verified that named-project
reads work from the `bob-mac-capture` checkout.

Seed the web with nine decisions that are both consequential and well evidenced.
Do not retrospectively manufacture rationale for attractive but weakly
documented conventions such as “every vault note has a parent.” Those should be
added only after Bryan confirms the actual alternatives, tradeoff, and reopen
condition.

## Research method and evidence

I independently examined:

- the complete `decisions` memory web exposed by the `sase` project through
  audited `sase memory read` calls, its generated index, memory documentation,
  validator tests, and memory-write skill;
- current `bob-cli` documentation and history, particularly `README.md`,
  `docs/vault-git-sync.md`, `docs/projects.md`, `docs/task-status-hooks.md`,
  `docs/plugins.md`, `docs/capture.md`, and relevant commits;
- the opened `bob-plugins` repository, especially its source/deployment model,
  dependency identity rule, and history;
- the opened `bob-mac-capture` repository, especially its process/JSON boundary,
  compatibility behavior, privacy boundary, and history;
- the loaded Bob vault reference memory; and
- established ADR guidance from AWS, the UK Government Digital Service, and
  Martin Fowler.

I did not locate or inspect any other swarm researcher's report or transcript.

## What should be copied from the SASE precedent

The SASE implementation gets several important things right.

### 1. The descriptor is an always-loaded index, not the records themselves

A web is a type-free descriptor at `sase/memory/<web>.md` plus independently
addressable strands at `sase/memory/<web>/<slug>.md`. The descriptor is always
rendered under **Memory Webs**, while strand bodies are fetched only through
`sase memory read <web>:<keyword>`. A `roster: list` descriptor therefore gives
every agent a compact map of accepted decisions without imposing the much
larger rationale bodies on every turn.

This is especially appropriate here. The current Bob project context is only a
few thousand approximate tokens. Nine short roster entries should cost a few
hundred more tokens; nine full ADR bodies would be unjustifiable always-loaded
context.

### 2. Each record is a claim, not a subsystem description

The upstream descriptor explicitly distinguishes a decision record from a
design document or subsystem overview. Its strand shape is consistently:

- **Claim.** The decision in direct, quotable language.
- **Why.** The real forces and credible rejected alternatives.
- **Cost.** The downside accepted by choosing it.
- **Reopens when.** Concrete evidence or a changed condition that justifies a
  new decision.

That shape is stronger for agents than a conventional “Context / Decision /
Consequences” template because the cost and reopen trigger are impossible to
hide inside optimistic prose. It is still recognizably an ADR. AWS recommends
capturing context, decision, and consequences and emphasizes the reason over
implementation details; Fowler additionally recommends serious alternatives,
ramifications, and conditions that should trigger reevaluation.

For Bob I would add one small extension before the Claim:

> **Applies to.** `bob-cli`, `bob-mac-capture`, vault capture behavior.

This is justified because the log spans three repositories plus user data. It
prevents a reader from mistaking a cross-repository invariant for a local coding
preference. Scope should appear in the body because arbitrary strand metadata
is not shown in normal memory reads.

### 3. Accepted records are immutable and superseded, never rewritten

The SASE web marks the old strand with
`metadata.status: superseded` or `superseded-in-part`, supplies
`superseded_by`, and adds an authored `[[...]]` back-link in the old body. The
old record remains readable. This matches AWS's guidance that accepted ADRs
become immutable and that a new accepted ADR supersedes the old one. It also
matches GDS guidance to retain and clearly link superseded records.

This history-preserving rule matters more than a “keep docs current” rule. A
future agent needs to know not only what governs now, but why apparently simpler
alternatives were already rejected and what changed when the project later
moved on.

### 4. Links are authored, not inferred

Use explicit `[[decisions/slug]]` links when one decision depends on or
supersedes another. Keep `link_reference: explicit` (the default). The Bob
corpus does not need phrase-matching closure, embeddings, tags, or a retrieval
service. The existing selector and roster are sufficient until actual usage
shows otherwise.

### 5. Only accepted decisions belong in agent memory

General ADR processes often include a Proposed state. That is a poor default
inside an always-visible agent policy index: an agent can mistake a proposal for
governing policy. Use plans, research reports, or beads to deliberate. Add a
strand only when Bryan has accepted the decision and the implementation either
exists or is being landed with it. A strand on the main branch is accepted;
`metadata.status` should be reserved for SASE's recognized supersession states.

For a newly made decision, optional `metadata.decided: YYYY-MM-DD` is useful.
For a retrospective record, omit the date unless a commit, plan, or other source
establishes it; do not turn the report-writing date into a fictional decision
date.

## Critique of the proposal

### Why it is valuable

The Bob ecosystem has unusually high decision density for its size:

- one vault is simultaneously user-authored data, a Git worktree, an Obsidian
  application state directory, and the target of multiple automated writers;
- behavior is split across a Rust CLI, direct Obsidian plugins, and a Swift
  subprocess client;
- some concepts deliberately have two identities or representations, such as
  file-scoped block links versus vault-wide dependency IDs;
- compatibility is maintained across independently installed binaries; and
- operational safety policies (one sync engine, conflict copies, guarded
  writes) are easy to violate while implementing a seemingly isolated feature.

Current docs explain the behavior well, but the rationale is scattered. A
decision web gives the project a compact “why” layer without replacing those
docs. This is the exact use case ADR literature describes: preserving forces and
tradeoffs so a later maintainer does not unknowingly overrule an earlier choice.

### Main failure modes

1. **Turning current behavior into invented history.** Repository archaeology
   can prove what happened and often when, but not always why Bryan chose it.
   A plausible rationale written by an agent is worse than no rationale because
   it acquires the authority of durable memory.
2. **Duplicating mutable documentation.** Capture grammar, command flags, JSON
   field inventories, plugin versions, and cron schedules change frequently.
   Copying them into immutable strands guarantees drift. A strand should name
   the governing boundary and link to current docs for mechanics.
3. **Recording preferences below the architectural threshold.** Keybindings,
   presentation colors, individual syntax spellings, and local refactors do not
   deserve ADRs unless they embody a broader invariant.
4. **Centralizing without routing.** A `bob-cli` web is not automatically loaded
   when an agent begins in a separately registered `bob-plugins` or
   `bob-mac-capture` project. A canonical store without pointers would provide
   false confidence.
5. **Treating records as enforcement.** ADRs explain policy; they do not make
   non-compliant code disappear. Cross-repository tests, contract fixtures,
   dirty-file guards, and sync locks remain the enforcement mechanisms.
6. **Letting the descriptor grow without bound.** Every descriptor and roster
   entry is paid for on every turn. The admission bar must stay high, summaries
   must stay one sentence, and overlapping records should be avoided.

### Requirements I would adjust

I would make these explicit changes to the initial request:

- Use **one canonical project-local web**, not a home web and not one full web
  per repository.
- Call it **`decisions`**, matching the SASE precedent and its natural selector.
- Add an **Applies to** line to each body because this decision log is
  cross-repository.
- Seed only records whose rationale can be supported by existing docs/history
  or confirmed by Bryan. Do not attempt exhaustive backfill.
- Keep proposed decisions out of memory. Deliberate elsewhere; publish only
  accepted records.
- Add routing stubs to the other projects as a required part of rollout, even
  though the canonical strands remain in `bob-cli`.
- Treat a decision's current implementation docs and tests as references, not
  content to copy into the strand.

## Where the web should live

| Option | Advantage | Problem | Verdict |
|---|---|---|---|
| `bob-cli/sase/memory/decisions*` | Co-located with the integration hub; versioned with the CLI contracts; already knows both linked repos | Separate project launches need an explicit pointer | **Recommended** |
| Home `~/sase/memory/bob_decisions*` | Automatically visible from all projects | Pollutes every unrelated project; global descriptor token cost; awkward scope/precedence | Reject |
| One decisions web in each repository | Local discoverability | Fragments cross-repo history; invites duplicated or contradictory records | Reject initially |
| New architecture-only repository | Neutral central ownership | Adds a repository and retrieval hop before the corpus warrants it | Reject for now |

The linked projects should contain only a small instruction such as:

> Cross-project Bob architecture and policy decisions are canonical in the
> `bob-cli` project's `decisions` memory web. Before changing a capture
> contract, vault mutation policy, plugin deployment boundary, or shared task
> identity, inspect the roster and read relevant strands with
> `sase memory web show -p bob-cli decisions` and
> `sase memory read -p bob-cli decisions:<keyword> -r "..."`.

If named-project access later proves unreliable in normal agent launches, that
is the evidence to reconsider a dedicated shared project or carefully scoped
duplication. It is not a reason to pay the home-memory cost now.

## Recommended on-disk shape

Descriptor: `bob-cli/sase/memory/decisions.md`

```yaml
---
web: true
description: >-
  Accepted architectural and policy decisions governing bob-cli, its linked
  Bob applications, and the Bob vault.
roster: list
link_reference: explicit
---

A decision record is not a design doc, runbook, or subsystem overview. It is
immutable once accepted. If the project changes course, add a new record and
mark the old record superseded with `metadata.status`, `superseded_by`, and an
authored back-link. Read a record with
`sase memory read decisions:<keyword> -r "<why>"`. Each record states its
scope, claim, credible alternatives, accepted cost, and reopening condition.
```

Strand template: `bob-cli/sase/memory/decisions/<slug>.md`

```yaml
---
keyword: <Decision Title>
aliases:
  - <useful lookup phrase>
summary: <One sentence stating the decision, not the topic.>
# For a newly made or historically proven date only:
metadata:
  decided: YYYY-MM-DD
---

**Applies to.** `<repository or vault scopes>`.

**Claim.** <Direct, testable statement of the accepted choice.>

**Why.** <Forces, evidence, and credible alternatives rejected. Cite current
docs, commits, plans, or research without copying mutable implementation detail.>

**Cost.** <The downside deliberately accepted.>

**Reopens when.** <A concrete changed condition or measurable threshold.>
```

Do not set `type:` or `parent:` on the descriptor. Do not put `type:` on
strands. Keep summaries short because all of them enter the always-loaded
roster. Run `sase memory init` after authoring; it regenerates `AGENTS.md`, the
provider shims, and the memory README. Then run `sase memory init --check` and
`sase doctor` (or the project's normal verification recipe) to catch invalid
web metadata, ambiguous aliases, unresolved links, and generated-document
drift.

## Initial strands

The following nine records clear the admission bar now. Titles and slugs are
recommendations, not mandatory wording.

### 1. Bob CLI Owns Capture Semantics

**Slug:** `bob-cli-owns-capture-semantics`  
**Applies to:** `bob-cli`, `bob-mac-capture`, vault capture

**Proposed claim.** The macOS app owns native presentation, hotkeys, process
orchestration, settings, and packaging; `bob-cli` is the sole implementation of
capture grammar, parsing, completion candidates and edit ranges, previews, and
vault mutation. The app may perform presentation-only local filtering over a
Bob-provided snapshot, but it does not synthesize grammar or edit Markdown
directly.

**Why it belongs.** This is the most important cross-repository boundary and is
stated at the top of `bob-mac-capture/README.md`. Violating it would create two
parsers and two mutation engines that drift. The credible rejected alternative
is a self-contained Swift capture implementation.

**Cost/reopen sketch.** It pays subprocess and JSON-contract complexity and
requires coordinated releases. Reopen if a second frontend needs an in-process
library or measured subprocess constraints dominate, with a plan that still
keeps one semantic implementation.

### 2. Capture Contracts Evolve Additively

**Slug:** `capture-contracts-grow-additively`  
**Applies to:** `bob-cli`, `bob-mac-capture`

**Proposed claim.** Versioned JSON interfaces add optional fields and preserve
older shapes where practical; consumers decode absent collections/objects as an
older capability and present Bob's returned behavior rather than infer it. A
single draft is submitted as one mutating Bob operation, never split into
several client-side mutations.

**Why it belongs.** The Mac app and CLI are installed independently. The Mac
README contains many explicit tolerant-decoding rules, while `Package.swift`
defines `CaptureCore` around the process/JSON contract. This policy explains
why apparently redundant compatibility fields remain.

**Cost/reopen sketch.** It accumulates decoder branches and constrains schema
cleanup. Reopen when an enforced version handshake or lockstep installer makes
breaking contract negotiation safe.

### 3. Custom Plugins Deploy From `bob-plugins`

**Slug:** `custom-plugins-deploy-from-source-repo`  
**Applies to:** `bob-plugins`, `bob-cli`, vault `.obsidian/plugins`

**Proposed claim.** Authored plugin code and manifests are source-owned in the
`bob-plugins` monorepo; vault plugin directories are deployment targets.
`bob plugins sync` copies only managed artifacts, protects dirty installed
files, and never replaces runtime/settings data such as `data.json`.

**Why it belongs.** The plugins were extracted from a vault where authored code
was mixed with third-party plugins and personal notes so they could be
versioned, validated, and reviewed independently. Editing the deployed copy is
the most likely locally convenient violation.

**Cost/reopen sketch.** It introduces an explicit deploy step, drift states,
backups, and cross-repo coordination. Reopen for an official per-plugin release
channel or another deployment mechanism that retains a single source of truth
and keeps user runtime data separate.

### 4. Git Is the Vault's Only Sync Engine

**Slug:** `git-is-the-only-vault-sync-engine`  
**Applies to:** Bob vault operations across athena, apollo, and Mac

**Proposed claim.** The vault uses the Git-based `bob vault-sync` channel and
exactly one active sync engine. Obsidian Sync remains disabled unless Bryan
performs an explicit cutover that first stops Git sync services and gates
nightly maintenance.

**Why it belongs.** `docs/vault-git-sync.md`, the loaded vault memory, and
commits `eee290a`, `4c00ada`, and `f567500` document the completed transition.
Two concurrent sync engines would invalidate conflict and maintenance
assumptions.

**Cost/reopen sketch.** Git requires credentials, host services, repository
size limits, operational recovery, and out-of-band handling for ignored data.
Reopen if Git no longer meets reliability/security/latency needs, but only with
a single-engine migration and tested rollback.

### 5. Vault Conflicts Preserve Both Sides

**Slug:** `vault-conflicts-preserve-both-sides`  
**Applies to:** `bob vault-sync`, vault queries and walkers

**Proposed claim.** For supported conflicts, remote content remains at the
canonical path while the local version is preserved under `_conflicts/` and
logged; quarantine is excluded from active task/query scans. Unsupported
conflicts abort rather than choosing a side destructively.

**Why it belongs.** “Last writer wins,” force-push, hard reset, and generic Git
merge markers are all tempting alternatives in automation. This policy makes
data preservation explicit and keeps duplicate/conflicted tasks out of active
workflow views.

**Cost/reopen sketch.** The user must manually reconcile quarantined copies,
and the canonical path initially favors remote content. Reopen when a proven
semantic merge can preserve both intent and active-vault invariants without a
quarantine copy.

### 6. Background Vault Writers Are Serialized and Guarded

**Slug:** `background-vault-writes-are-guarded`  
**Applies to:** vault sync, nightly, task-status reconciliation, randomize, and
future automated vault writers

**Proposed claim.** Background mutation correctness comes from the shared
maintenance lock, fresh snapshots, guarded writes, scoped commits, and bounded
retry—not from staggered schedules. New automated writers must participate in
the applicable coordination mechanism rather than assume the editor or another
job is idle.

**Why it belongs.** `docs/vault-git-sync.md` explicitly says staggered cron
offsets reduce collisions but do not guarantee exclusion. The command docs and
history repeatedly add snapshot guards, retries, and shared locking. A future
automation feature can otherwise reintroduce lost updates.

**Cost/reopen sketch.** Serialization adds contention, retry latency, and shared
infrastructure. Reopen when vault mutations move behind a transactional service
or another mechanism can prove equivalent compare-and-swap behavior.

### 7. The Pomodoro Ledger Drives Active Work State

**Slug:** `pomodoro-ledger-drives-work-state`  
**Applies to:** Bob vault workflow, `bob-cli`, task-oriented plugins

**Proposed claim.** Task Links under open Pomodoros in the daily note are the
durable plan/current-work ledger. Task ranks and derived Blocked state are
reconciled from the surviving ledger, schedules, and dependencies; status
display/notification commands read the ledger rather than creating an
independent work queue.

**Why it belongs.** The daily workflow and `task-status-hooks` contract are
built around this direction of authority. Reversing it would create feedback
loops between task checkboxes, links, and UI state.

**Cost/reopen sketch.** The domain is coupled to Markdown structure and needs a
reconciliation pass. Reopen if a different durable work ledger replaces the
daily note and comes with an explicit migration and compatibility plan.

### 8. Task Identity Includes the Note Path

**Slug:** `task-identity-includes-note-path`  
**Applies to:** `bob-plugins`, `bob-cli`, vault task dependencies and archives

**Proposed claim.** Obsidian block fragments remain file-scoped for navigation,
while Tasks dependency metadata uses a vault-wide identity derived from the
normalized note path plus block ID. Moves and archiving must repair both link
targets and dependency identities.

**Why it belongs.** `bob-plugins/README.md` states the distinction directly,
and commit `fc90f46` introduced note-scoped dependency identity after local
block IDs proved insufficient vault-wide. Treating `^review` alone as identity
silently aliases tasks in different notes.

**Cost/reopen sketch.** Renames and moves need repair logic; the encoding must
reject collisions and unsupported paths. Reopen if Obsidian/Tasks provides a
stable vault-wide task identifier independent of paths, or if a migration
proves a better identity scheme.

### 9. Project Lifecycle Is Represented by a Task

**Slug:** `project-lifecycle-is-a-task`  
**Applies to:** Bob project notes, `bob-cli`, navigation plugins

**Proposed claim.** A project's `^prj` completion-criteria task is the human
interaction point for lifecycle state; synchronization derives machine-facing
frontmatter and visibility from that task instead of requiring users to edit
metadata directly. `^ref` is the analogous pattern for reference notes.

**Why it belongs.** `docs/projects.md` explicitly explains the interaction-point
choice, and plugin history (`4314866`) shows scheduling being managed from the
lifecycle task. This is more than syntax: it defines the human/machine boundary
for projects.

**Cost/reopen sketch.** It reserves a block ID/tag, requires reconciliation,
and makes project conversion preserve a structured subtree. Reopen if project
lifecycle stops being task-completion-shaped or Obsidian gains a better native
interaction object that can preserve the same workflow.

## Candidates that should not be seeded yet

These are plausible decisions, but they do not yet have enough proven rationale
or rank below the initial set:

- **Every vault note has a `parent`.** It is a current global convention, but
  the evidence reviewed states the rule without the original forces,
  alternatives, cost, or reopen condition. Ask Bryan before canonizing why.
- **Custom plugins use plain CommonJS with no build step.** This is explicitly
  intentional and could become a record, but it is local construction policy
  rather than an ecosystem invariant. Add it when a proposal to introduce
  TypeScript/bundling makes the tradeoff live.
- **Native Rust commands with embedded shell rollback.** The migration and
  compatibility path are well documented, but the remaining fallback may be a
  temporary migration fact. Decide whether the durable choice is “Rust is
  canonical” or “dual implementation remains supported” before recording it.
- **Schedule and Work Logs are task-local Markdown history.** Important domain
  behavior, but current rules contain many evolving details. First extract the
  stable decision (why task-local logs rather than a separate journal) from the
  mutable formatting contract.
- **Plugin versions are independent and the repo is private.** These are clear
  policies, but they can remain in `bob-plugins/README.md` until release or
  publication work makes the rejected alternatives relevant.
- **Google Keep is archived only after verified vault durability.** This is an
  excellent safety decision, but it concerns one bounded integration. Add it
  when Keep work resumes or when the pattern is generalized to other inboxes.

This staging is deliberate. A decision log should grow in response to real
decision pressure, not because the repository contains many interesting
rules.

## Admission and maintenance policy

Before adding a strand, require all of the following:

1. The choice constrains more than one feature, repository, public contract, or
   operational safety property.
2. A credible future implementer could reasonably choose an alternative.
3. The actual rationale and at least one serious alternative are known, not
   guessed.
4. The negative consequence can be stated plainly.
5. A concrete reopen condition can be stated.
6. Current mechanics can be linked rather than copied into the record.

Maintenance should be event-driven:

- consult relevant strands when a change crosses a listed boundary;
- create a new strand when an accepted change reverses or materially narrows a
  prior decision;
- mark the old strand with `superseded` or `superseded-in-part`, name the new
  target in `superseded_by`, and add the authored back-link;
- never silently rewrite the old rationale to make history look cleaner;
- periodically inspect the roster for overlapping summaries and token growth,
  but do not schedule reviews merely to rewrite still-valid records; and
- keep tests and current docs responsible for enforcement and live mechanics.

## External references

- AWS Prescriptive Guidance, [Architectural decision record
  process](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html):
  significant decisions, context/decision/consequences, ownership, acceptance,
  immutability, and supersession.
- AWS Prescriptive Guidance, [Best practices for using architectural decision
  records](https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/best-practices.html):
  preserve history, centralize access, and do not confuse ADRs with remediation
  for non-compliant code.
- UK Government Digital Service, [Documenting architecture
  decisions](https://gds-way.digital.cabinet-office.gov.uk/standards/architecture-decisions.html):
  application-local versus larger-scale storage, lifecycle, discoverability,
  and the warning that an ADR is not a complete architecture description.
- Martin Fowler, [Architecture Decision
  Record](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html): short
  single-decision records, repository locality, serious alternatives,
  consequences, supersession, and reevaluation triggers.

## Recommended solution

Create `sase/memory/decisions.md` and `sase/memory/decisions/` in `bob-cli`
using the SASE descriptor, list roster, explicit authored links, and immutable
Claim/Why/Cost/Reopens structure shown above, with the added **Applies to** line.
Seed exactly the nine well-evidenced decisions above, keeping each to roughly
one screen and linking mutable mechanics to existing docs. Run
`sase memory init`, validate the generated memory, and add minimal pointers in
`bob-plugins` and `bob-mac-capture` that route cross-project reads to
`-p bob-cli`. Keep proposals and uncertain retrospective rationale out of the
web; add a record only after the decision is accepted, and change course only
through an explicitly linked superseding strand.

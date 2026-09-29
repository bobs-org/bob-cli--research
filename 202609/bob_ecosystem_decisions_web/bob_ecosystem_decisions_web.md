# A `decisions` Memory Web for the Bob Ecosystem

- **Date:** 2026-09-29
- **Role:** Lead researcher. This report merges five independent reports
  (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`, all in this directory) with my own
  verification pass.
- **Scope:** `bob-cli` (the host SASE project), its linked repos `bob-plugins` and
  `bob-mac-capture`, and the Bob Obsidian vault (`~/bob`).
- **Question:** Should Bryan build a SASE memory web of architecture and policy decisions,
  modeled on the `sase` project's `decisions` web? If so, how, and which records should it
  launch with?

## Bottom line

**Yes, build it, but smaller and more strictly than the request implies.**

- **One web, called `decisions`, in bob-cli's project memory.** Do not create a home web,
  and do not create one web per repo. All five researchers agree on this.
- **Copy sase's format exactly.**
  - The descriptor is always loaded, and its roster lists every record.
  - Each record has four parts: Claim / Why / Cost / Reopens when.
  - A record never changes after it is accepted. When course changes, a new record
    supersedes it.
- **Add two Bob-specific conventions:**
  - an **`Applies to`** line at the top of each record body
  - every roster summary is written as a rule an agent can follow
- **Launch with 11 evidenced records** (§6.1). Hold 4 more until Bryan confirms or
  explains them (§6.2). Keep a backlog to write when each area is next touched (§6.3).
- **Add pointers** from `bob-plugins`, `bob-mac-capture` and home `obsidian.md` to the
  web. They are cheap insurance for agents that start outside bob-cli.

The biggest risks are **invented rationale** and **copying documentation into records
that can never be edited**. One of the five reports (`gem`) shows both risks concretely
(§8.2). The admission test in §5 exists to prevent them.

---

## 1. Is this a good idea?

### 1.1 Yes, because the problem is real

The reasons behind Bob's choices exist, but agents cannot reach them. They are scattered
across:

- 41 plans with "Decisions" sections (`cld`'s count)
- research syntheses
- `feat!` commit bodies
- four READMEs
- `docs/*.md` (about 7,400 lines)
- home `obsidian.md`
- the linked-repo blurbs in `sase.yml`

No agent reads these by default. A roster line, by contrast, is loaded on every turn.

Several of these rules are ones a capable agent would break on purpose, in good faith:

- porting capture grammar to Swift "for latency"
- adding TypeScript and a bundler to `bob-plugins`
- extracting the copied plugin helpers into a shared module
- bumping `schema_version` for a new field
- running `git reset --hard` on a wedged vault
- having a new cron writer set `[?]` directly
- using `git add -A` in a new automation

Each of these was a considered rejection, and most are invisible from the code alone.
The system spans three codebases and a data store, with contracts between them:

- the capture JSON interfaces
- the maintenance lock
- the derived task statuses
- the plugin deploy path

Cross-repo invariants like these are exactly what per-repo docs handle worst.

**The format costs no code.** sase built the web format, validates it
(`sase memory init`, `sase doctor`), and has used it for five weeks:

- 6 records at launch on 2026-08-24
- 24 records now

### 1.2 How it fails

| Failure mode | Mitigation |
| --- | --- |
| **Invented history.** An agent writes a plausible "Why" that Bryan never had, and the record gains the authority of durable memory. `gem`'s report does this (§8.2). | Each record cites evidence that can be checked: a commit, a doc line or a research/plan ref. If no source gives the reason, **ask Bryan** (§6.2). |
| **Copying docs that keep changing into records that never change.** Grammar tables, keymaps and flag lists go stale while the record stays fixed. | A record states the choice, the rejected alternatives, the cost and the reopen trigger. It **links** to the doc that owns the details. Rule of thumb: if adding a flag would force a rewrite, it is not a decision. |
| **Recording UI churn.** `\p` was reversed after 47 minutes (bob-plugins `13eb4d6` → `1de6f93`). Ctrl-J was rebound three times. Blocked went `[B]` → `[*]` → derived `[?]` in 8 days. | Record the stable principle behind the churn, never the current binding. |
| **Roster bloat.** Every summary is paid for on every turn. | Keep summaries to about 30 words. Launch with 11 records. Grow only when a real decision is made. |
| **Centralizing without routing.** An agent that starts inside a linked checkout sees none of bob-cli's memory. | Add pointer stubs (§4.3). |
| **Treating records as enforcement.** | Tests, contract fixtures, dirty-file guards and locks still enforce the rules. A record explains *why* they exist. |
| **Recording proposals.** An agent may mistake a proposal on the roster for policy that governs. | Record only **accepted** decisions. Deliberate in plans, research or beads instead. |

### 1.3 Alternatives considered

| Option | Verdict |
| --- | --- |
| Home-scoped web named `decisions` | **Reject.** `merge_memory_web_scopes` (sase `src/sase/memory/web/scope.py`) combines home and project webs that share a slug, one strand at a time, and project strands win. Bob records would appear in sase's `decisions:` namespace, and the roster would load in every project. |
| Home web with a unique name (`bob_decisions`) | **Reject.** Its descriptor would still load into every project, including sase. |
| One web per repo | **Reject.** The most valuable records cross repos. This would also mean three descriptors to pay for, and superseding a decision across webs would be awkward. |
| `docs/adr/NNNN-*.md` in each repo | **Reject as the primary store.** No roster reaches agents, reads are not audited, and supersession is not tracked. |
| One core or reference note | **Reject.** A core note inlines every body. A reference note hides every rule until someone reads it. sase's own `memory-webs` record rejected both shapes. |
| Promote bob-plugins and bob-mac-capture to SASE projects | **Reject.** It costs a lot of lifecycle work to fix a problem that pointers already solve. |
| Do nothing | **Reject.** The drift in §7 happened with the current docs in place. |

---

## 2. What the sase web is (verified)

I opened the sase checkout at `c2aec595c8` and confirmed the following.

- **Files**
  - a descriptor, `sase/memory/decisions.md`
  - a flat directory of strands, `sase/memory/decisions/<slug>.md` (24 today)
  - Nested directories are a fail-closed `nested_directory` error
    (`discovery.py:129`).
- **Descriptor frontmatter:** `web: true`, `description`, `roster: list`,
  `roster_label: DECISIONS`, `strand_noun: decision`.
  - There is no `type:` or `parent:`.
  - The body is one paragraph that says what a record is and is not, followed by the
    generated roster between `<!-- sase:strands -->` markers.
- **Strand frontmatter:** `keyword`, `aliases`, `summary`, and `metadata`.
  - **20 of 24** strands carry `metadata.status: accepted`, and **all 24** carry
    `metadata.decided: YYYY-MM-DD`.
  - Only `superseded` and `superseded-in-part` mean anything to the tool
    (`supersession.py`). `accepted` is a convention that the tool ignores.
- **Body:** `**Claim.**` / `**Why.**` (with named rejected alternatives and cited
  evidence) / `**Cost.**` / `**Reopens when.**`.
- **Supersession**
  - The *old* record gets `metadata.status` plus `superseded_by` and a `[[...]]`
    back-link.
  - The roster shows `_[superseded by …]_`.
  - Validation of this convention only warns; it does not block.
- **Links** are written by hand as `[[decisions/<slug>]]` or `[[glossary:<term>]]`. The
  default is `link_reference: explicit`, and there is no phrase-matching closure.
- **Reads do not print metadata.** `sase memory read -p sase decisions:gates-never-block`
  prints the keyword, aliases and body, but not `decided` or `accepted`. Any scope tag
  kept in `metadata` is therefore invisible to the agent reading the record (§5.2).
- **Cross-project reads work:**
  - `sase memory read -p bob-cli glossary:pomodoro` succeeds even when run from `/tmp`.
  - `sase memory web show` also accepts `-p`.
- **Cost in context:**
  - sase's roster: about 1,500–1,600 tokens for 24 records.
  - bob-cli today: about 2,769 loaded tokens (`sase memory list`).
  - 11 records with summaries of about 30 words: about 650–750 tokens, roughly **+25%**.
    That is acceptable only if the admission bar stays high.
- **Usage** (`cld`, from sase's `memory_reads.jsonl`, excluding this swarm):
  - 110 strand reads in all.
  - The top three all govern what an agent does next: `record-before-admit` (17),
    `two-speed-verification` (14) and `guarded-recipes` (10).
  - Records about memory internals got 1–2 reads each.
  - **Lesson:** roster summaries do most of the work, and bodies get read when a record
    governs the task at hand. Write directive summaries for the rules agents actually
    trip over.

---

## 3. Adjustments to the requirements (explicit)

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| A1 | Cover bob-cli, bob-plugins, bob-mac-capture and "the vault in general" | **One web in bob-cli project memory** covers all four domains. Vault **decisions** are in scope. Vault **conventions and procedures** stay in home `obsidian.md`, which every project sees. Examples: the `parent` frontmatter rule, which trees are gitignored, how to inspect a sync run. | A home web leaks into sase (§1.3). `grk` argued for dropping the vault as a target. I keep it, but only for real decisions with alternatives, cost and a reopen trigger. |
| A2 | "Heavily inspired by" sase | **Copy the format exactly.** Add only an `**Applies to.**` body line and the "summary is a rule" convention. Keep `metadata.status: accepted` and `metadata.decided`, as sase does. | Agents already know the shape. Scope has to go in the body because reads do not show metadata. |
| A3 | "The more important decisions" | **Apply the admission test in §5.3.** Keymaps, grammar punctuation, flag lists and UI details stay out. | Churn (§1.2) and the rule that records never change. |
| A4 | "Think hard about initial strands" | **Launch with 11 records (§6.1).** Hold 4 until Bryan confirms or explains them (§6.2). Keep a named backlog (§6.3). Do **not** try to write up the whole history. | sase launched with 6 and grew about one record per epic that made a durable choice. The roster costs tokens on every turn. |
| A5 | *(not asked)* | **Pointer stubs:** add a section to bob-plugins' `AGENTS.md`, create a new minimal bob-mac-capture `AGENTS.md` plus a `CLAUDE.md` containing `@AGENTS.md`, and add one line to home `obsidian.md`. | Agents that start outside bob-cli would otherwise never find the web. |
| A6 | *(not asked)* | **Only accepted decisions.** Dates come from commits or plans. If no source proves a date, leave it out. | This guards against made-up authority and dates. |
| A7 | *(not asked)* | **Fix the doc drift found in this research** (§7). | A record must not cite a doc that contradicts it. |
| A8 | *(not asked)* | **A capture habit, not a sweep.** When an epic's plan contains a durable choice, the plan includes a "write or supersede a record" step. | Keeps the web current without periodic rewrites. |

---

## 4. Where it lives and how agents reach it

### 4.1 Layout

```text
bob-cli/sase/memory/decisions.md          # descriptor (web: true)
bob-cli/sase/memory/decisions/<slug>.md   # one record per file, flat
```

### 4.2 Why bob-cli is enough as the primary path

- `sase project list` shows only two projects, `bob-cli` and `sase`. The linked repos
  are **not** SASE projects.
- About 130 of bob-plugins' 146 commits carry SASE trailers that point at bob-cli's
  plans, beads and agents sidecars. bob-mac-capture's history is the same.
- In practice, agents that edit the linked repos start from bob-cli workspaces. They
  already load bob-cli's `AGENTS.md`, so they will see the roster.

### 4.3 Pointers as insurance

Some agents start directly inside a linked checkout. Two examples are an agent on the
MacBook, the only machine where the Mac UI builds, and a sase-project agent touching the
vault. For them:

- **bob-plugins `AGENTS.md`.** It is currently 3 lines, and its `CLAUDE.md` is
  `@AGENTS.md`. Append:

  ```markdown
  ## Decisions
  Cross-repo Bob architecture and policy decisions live in bob-cli's `decisions` memory
  web. Before changing behavior a decision governs, list them with
  `sase memory web show -p bob-cli decisions` and read the relevant one with
  `sase memory read -p bob-cli decisions:<keyword> -r "<why>"`.
  ```

- **bob-mac-capture.** It has **no** `AGENTS.md` today (verified). Create one with the
  same section, plus a `CLAUDE.md` containing `@AGENTS.md`.
- **Home `obsidian.md`.** Add one line pointing at the bob-cli web for the reasons behind
  the sync, conflict and lock rules.
  - It is a reference note, so this costs no always-loaded tokens.
  - It lives in the chezmoi repo, so it needs its own authorization and commit.

---

## 5. Format

### 5.1 Descriptor (draft)

```markdown
---
web: true
description:
  Accepted architecture and policy decisions for bob-cli, bob-plugins, Bob Mac Capture,
  and the Bob vault — the choice, its rejected alternatives, and what would reopen it.
roster: list
roster_label: DECISIONS
strand_noun: decision
---

# Decisions

A decision record is not a design doc, runbook, command contract, or keymap — those live
in `docs/` and each repo's README and go stale as the code changes. Each roster summary
below is a rule to follow as written; before changing behavior a record governs, or
proposing one of its rejected alternatives, read it with
`sase memory read decisions:<keyword> -r "<why>"`. A record is immutable once accepted:
if course changes, write a new record and mark the old one with `metadata.status` plus
`superseded_by` and a `[[...]]` back-link, never edited in place.

<!-- sase:strands -->
<!-- /sase:strands -->
```

### 5.2 Record template

```markdown
---
keyword: <Title-Case Statement Of The Decision>
aliases:
  - <2–3 phrases an agent would search for>
summary: <≤ ~30 words, phrased as a rule an agent can obey without reading further>
metadata:
  status: accepted
  decided: YYYY-MM-DD   # only when a commit/plan proves it; otherwise omit
---

**Applies to.** `bob-cli`, `bob-mac-capture`, vault, … (any subset)

**Claim.** <present tense; name the commands/files it governs>

**Why.** <pinned evidence: short hash + date, `research:`/`plan:` ref, or path:line; name
each rejected alternative and why it lost; [[decisions/<slug>]] / [[glossary:<term>]]>

**Cost.** <what is given up; include known drift or debt honestly>

**Reopens when.** <an observable trigger, not "if we change our minds">
```

How the reports' disagreements on format were settled:

- **Slugs describe the claim and carry no domain prefix.** For example, use
  `git-only-vault-sync`, not `vault-git-sync-only`. This rejects `gem`'s
  `vault-`/`cli-`/`plugins-`/`mac-` prefixes, for three reasons:
  - the roster sorts by *keyword*, not slug, so prefixes do not group anything;
  - the best records span several domains, so no single prefix fits them;
  - the nested-directory ban (which is real) does not create a collision risk at 11
    records.
- **Scope goes in the body as an `Applies to.` line, not in `metadata.scope`.**
  `cld` and `mus` proposed `metadata.scope`. Metadata is invisible in reads (§2), while
  the body line is visible and can still be grepped.
- **`status: accepted` stays.** `cdx` proposed reserving `status` for supersession, but
  sase uses `accepted` on 20 of 24 records and the tool ignores it.

### 5.3 Admission test (all must hold)

1. **A credible alternative was rejected,** and the record can name it.
2. **An agent or future Bryan could plausibly choose that alternative in good faith.**
3. **The reason is not evident from the code or the command contract.**
4. **The choice is expected to hold for months.** If it has already flipped, record the
   stable principle behind it.
5. **The reason is known, not guessed.** Evidence can be pinned, or Bryan has stated it.
6. **The details can be linked rather than copied.**

What failing a test means:

- **Fails (1):** it is a *rule* and belongs in a flat note, such as `obsidian.md` or
  `cli_rules.md`.
- **Fails (4):** it belongs in `docs/`.
- **Fails (5):** ask Bryan first.

---

## 6. Which records

Candidates were ranked on three things:

1. how likely an agent is to break the decision
2. how much damage that causes (vault data > cross-repo contract > code structure)
3. how strong the evidence is

I checked every citation below against the repos on 2026-09-29. The *Support* column
shows which researchers proposed each record.

### 6.1 Launch set (11 records)

| # | Slug | Applies to | Support |
| --- | --- | --- | --- |
| 1 | `mac-capture-is-a-thin-client` | bob-mac-capture, bob-cli | all 5 |
| 2 | `capture-contract-grows-additively` | bob-cli, bob-mac-capture | cdx, cld, mus (as a proposal) |
| 3 | `git-only-vault-sync` | vault, bob-cli | all 5 |
| 4 | `vault-conflicts-quarantine-local` | vault, bob-cli | cdx, cld, grk, mus |
| 5 | `vault-writers-share-one-lock` | bob-cli, vault | cdx, cld, mus, gem |
| 6 | `task-status-is-derived` | vault, bob-cli, bob-plugins | cdx, cld, grk, mus |
| 7 | `plugins-deploy-from-source-repo` | bob-plugins, bob-cli, vault | cdx, grk, mus, gem (cld: confirm first) |
| 8 | `plugins-plain-commonjs-standalone` | bob-plugins | cld, grk, gem |
| 9 | `task-dependency-ids-are-note-qualified` | bob-plugins, bob-cli, vault | cdx, gem |
| 10 | `task-line-is-the-interaction-point` | bob-cli, bob-plugins, vault | cdx, grk |
| 11 | `vault-writers-refuse-on-ambiguity` | bob-cli, bob-plugins | cld |

If you want a launch the size of sase's, take records 1–6. If you trim, drop 10 first.

---

**1. `mac-capture-is-a-thin-client`: Bob Mac Capture Is A Thin Client Of `bob`**

- **Summary (the rule):** Bob Mac Capture never parses capture grammar, computes
  previews, or writes vault Markdown. It runs `bob`, applies the returned ranges and
  results verbatim, and submits each draft as one mutating `bob` call.
- **Claim:**
  - The app owns presentation, the hotkey, settings, launch at login, running processes
    and packaging.
  - Grammar, completion, preview and every vault write belong to bob-cli.
  - The app may only rank or filter snapshots that `bob` already returned.
- **Rejected:**
  - A Swift port of the grammar. It would be a third implementation: the Hammerspoon
    `task_capture.lua` (353 lines) was already a second one, and it was named the
    *root cause* of the missing completion.
  - C-FFI or a shared library, because of packaging and signing.
  - Splitting one draft into several client-side calls.
- **Cost:**
  - Every capture feature lands in bob-cli first, then in the Mac app.
  - Each preview is a subprocess, with a 20 s timeout and lane cancellation.
  - The two binaries are installed independently, which makes record 2 necessary.
- **Reopens when:** measured subprocess latency breaks live preview, or a second frontend
  needs an in-process library. Even then, there must still be one semantic
  implementation.
- **Evidence:**
  - Mac `README.md:3-6` (present since `9030832`, 2026-08-13, which is the decided date)
  - `Sources/CaptureCore/BlockIDRules.swift:5` ("Bob is the only authority for the
    grammar")
  - `research:202608/bob_mac_capture_replacement/…` §2.2

**2. `capture-contract-grows-additively`: The Capture JSON Contract Grows Additively On
Schema v1**

- **Summary:** bob-cli's capture JSON interfaces only gain fields on
  `schema_version` 1.
  - Never rename, remove or re-type a key.
  - Land contract changes in bob-cli and `docs/capture.md` first.
  - Frontends decode absent fields as an older capability.
- **Rejected:**
  - A schema bump per feature. It forces lockstep releases, and the Mac app rejects any
    version other than 1 (`BobProcessClient.swift:359`).
  - A version-negotiation handshake.
- **Cost:**
  - Legacy fields pile up. For example, multi-capture keeps the first item's top-level
    fields.
  - A real v2 would need a period of emitting both versions.
- **Reopens when:** a change cannot be expressed additively, or a lockstep installer or
  handshake makes breaking changes safe.
- **Evidence:**
  - `docs/capture.md:2137` ("schema version 1 stays additive"), plus many per-kind
    "additive" clauses
  - `2bdf4f7` (2026-08-15)
  - `plan:202608/multi_capture.md`
  - Mac `CaptureModels.swift` uses lenient `decodeIfPresent` throughout
- `mus` held this as a proposal, pending confirmation that it is policy.
  `docs/capture.md` states it as policy, so it launches.

**3. `git-only-vault-sync`: The Vault Syncs Through Git Only**

- **Summary:** `bob vault-sync` on athena, apollo and the MacBook is the vault's only
  sync engine. Obsidian Sync and Obsidian Git automation stay off, and exactly one engine
  may ever run.
- **Why:**
  - On 2026-08-27 Obsidian Sync failed **454+ times in a row** with `Vault limit
    exceeded`. The Standard plan's quota includes version history.
  - athena is a headless server that cron and agents edit.
- **Rejected:**
  - Restoring Obsidian Sync under a sub-1 GB footprint policy. That was epic `bob-cli-1l`,
    closed as *superseded* by `bob-cli-1n` the same day.
  - The Obsidian Git plugin. It runs only while Obsidian is open, works at minute
    granularity, and has no policy for unattended conflicts.
  - Syncthing and LiveSync.
- **Retired:** `bob bulk-git-commit` (`4051bf5`). It never fetched, which was safe only
  while Obsidian Sync kept the machines converged.
- **Cost:**
  - Changes take 5–15 s to propagate.
  - The gitignored trees (`xlib/`, `lit_review/`, custom `bob-*` plugins) do not travel.
  - Files of 95 MiB or more are refused.
  - Every host needs credentials and a service.
- **Reopens when:** a device that cannot run the service becomes essential (a phone, for
  example), or polling latency causes regular real conflicts. Any migration must keep a
  single engine and have a tested rollback.
- **Evidence:**
  - `research:202608/obsidian_vault_git_sync/…` §1.1, §3
  - `eee290a` and `4c00ada` (2026-08-27, the decided date)
  - `d1c5a68` (apollo, 2026-09-03)
  - `docs/vault-git-sync.md`
- **Link:** home `obsidian.md` holds the operating rule; this record holds the *why*.

**4. `vault-conflicts-quarantine-local`: Sync Conflicts Keep Remote In Place And
Quarantine Local**

- **Summary:** On a supported conflict, the remote version stays at the canonical path.
  The local copy goes to `_conflicts/`, is logged, and is excluded from walkers and
  queries.
  - Unsupported conflicts abort.
  - Never leave conflict markers, `reset --hard`, force-push, or use `-X ours/theirs` on
    the vault.
- **Rejected:**
  - Git's default of conflict markers and halting. Markers break Obsidian and the 03:30
    `bob` parse. The research calls this choice "the whole project".
  - ours/theirs strategies, which lose data silently.
  - A "sentinel line" mitigation, which the research disproved.
- **Cost:**
  - A human must review `_conflicts/sync_conflicts.md`.
  - A local edit can temporarily live only in quarantine.
- **Reopens when:** conflict copies become frequent enough to justify a semantic merge
  driver that preserves both sides' intent.
- **Evidence:** `docs/vault-git-sync.md` "Conflict policy"; the git-sync research §4 and
  §5.3.

**5. `vault-writers-share-one-lock`: Unattended Vault Writers Share One Lock And Commit
Only Their Own Files**

- **Summary:** `vault-sync`, `nightly`, live `task-status-hooks`, `randomize` and
  `gkeep pull` serialize on `bob_sync.lock`. New automated writers must:
  - join that lock
  - use fresh snapshots and guarded writes
  - commit only the files they wrote
  - never `add -A`, amend or force-push
- **Rejected:**
  - Relying on staggered cron offsets for exclusion. `docs/vault-git-sync.md:130-133`
    says offsets "cannot guarantee exclusion".
  - Per-command locks.
  - Per-command `add -A` commits, which was the shape of the retired
    `bulk-git-commit`.
- **Cost:**
  - Contention and retry latency.
  - Interactive `bob capture` and plugin edits are **not** under the lock. They rely on
    guarded compare-and-swap writes, and the record should say so.
- **Reopens when:** lock contention measurably delays sync, or vault mutation moves
  behind a transactional service.
- **Evidence:**
  - `README.md:738-741`
  - `src/native/gkeep/pull.rs:131`, which takes `bob_sync.lock`. The README list omits
    it (§7).
  - `docs/vault-git-sync.md`
  - `docs/randomize.md`

**6. `task-status-is-derived`: Next, In Progress, And Blocked Are Derived From The
Ledger**

- **Summary:**
  - Today's Pomodoro ledger drives Next and In Progress.
  - Open dependencies or future `scheduled` dates drive Blocked `[?]`.
  - `bob task-status-hooks` reconciles both.
  - Writers change the *inputs*, never just the checkbox.
- **Rejected:**
  - An authored Blocked status. bob-plugins `890ed13` (2026-07-08, `feat!`) retired
    `[B]`, and `36296ec` (2026-07-16) brought Blocked back as the derived `[?]`.
  - A status policy per writer or per plugin.
  - Letting capture close (`=x`) fully resolve Blocked.
- **Cost:**
  - A hand edit to a derived checkbox is silently undone.
  - The vault is briefly inconsistent until the hooks run.
  - Every writer must keep the inputs consistent. For example, a manual unblock must also
    clear a future `scheduled` date (`786fc1d`).
- **Reopens when:** a status is needed that no ledger, schedule or dependency input can
  express.
- **Evidence:** `docs/task-status-hooks.md:3` (the ledger is "the source of truth").
- **Link:** `[[glossary:pomodoro]]`, `[[glossary:task-link]]`.

**7. `plugins-deploy-from-source-repo`: bob-plugins Is The Source; Vault Plugin Folders
Are Deploy Targets**

- **Summary:** Custom plugins are edited only in `bob-plugins` and deployed with
  `bob plugins sync`. The vault's `bob-*` plugin folders are gitignored deploy targets.
  - The sync copies only `manifest.json`, `main.js` and `styles.css`.
  - It never touches `data.json`.
  - It refuses to overwrite dirty targets.
- **Rejected:**
  - Editing in the vault. That was the historical state: unversioned, and mixed with
    third-party plugins.
  - Per-plugin repos or submodules.
  - Letting vault git sync, or Obsidian Sync, carry the plugins.
- **Cost:**
  - A deploy step on each host. The MacBook is refreshed by hand.
  - Drift states and dirty-file refusals.
- **Reopens when:** a plugin is published (the community registry and BRAT expect one
  repo per plugin), or a deploy mechanism keeps one source while still keeping runtime
  data separate.
- **Evidence:**
  - bob-plugins `README.md:150-162`
  - `docs/plugins.md`
  - `docs/vault-git-sync.md:230` ("stay gitignored in the vault")
  - home `obsidian.md`
- **Before writing:** bob-plugins `README.md:165` still calls sole ownership "a
  deliberate later decision". The other docs show that decision has already been made.
  Get a one-line confirmation from Bryan and fix the README in the same change (§7).
- The "never edit `~/bob/.obsidian/plugins`" *rule* is already always-loaded through the
  linked-repo description. This record adds only the reasons, which is fine.

**8. `plugins-plain-commonjs-standalone`: Bob Plugins Are Hand-Written CommonJS With No
Build Step**

- **Summary:** Each plugin's `main.js` is the hand-edited source: no TypeScript, bundler
  or build. Plugins never `require` each other. Shared logic is copied with a
  "Mirrors …" pointer and kept in sync.
- **Rejected:** the Obsidian TypeScript + esbuild sample template; a shared package.
- **Cost:**
  - No types.
  - The copies drift, and already have. Schedule Log emphasis is `_` in
    `block-id-prompt/main.js:90` but `*` in `task-status-cycler/main.js:519`. Say this
    honestly in the record.
- **Reopens when:** a plugin is published, or drift in the copied helpers causes repeated
  bugs. The next step would then be vendoring that still needs no build.
- **Evidence:** bob-plugins `README.md:72` ("intentionally no TypeScript, no bundler, and
  no build step"); `ef15fc6` (2026-06-20).
- `cdx` deferred this record as only local policy. I include it because it is the
  "improvement" an agent is most likely to make in good faith.

**9. `task-dependency-ids-are-note-qualified`: Task Dependency Identity Is
Note-Qualified**

- **Summary:** `^block` IDs are file-scoped anchors for links and embeds.
  `[id::]`/`[dependsOn::]` use a vault-wide ID derived from the note path plus the block
  ID. Moves and archiving must repair both.
- **Rejected:** bare block IDs as dependency identity. Tasks metadata is vault-wide, so
  `^review` in two notes would silently alias.
- **Cost:**
  - Rename and move repair logic.
  - The encoding must reject collisions.
- **Reopens when:** Obsidian or Tasks gains a stable vault-wide task identifier.
- **Evidence:** bob-plugins `fc90f46` (2026-07-11, "scope task dependency identities by
  note") and `README.md` §Dependency identity migration.
- **Link, don't restate, the encoding.** `grk` rightly calls the encoding a living
  migration contract, so the record states only the principle.

**10. `task-line-is-the-interaction-point`: The Completion-Criteria Task Is The Human
Interface For Managed Notes**

- **Summary:** Project (`^prj`) and reference (`^ref`) notes are driven through their
  completion-criteria task line. `bob projects sync` and `bob highlights sync` derive the
  machine-facing frontmatter from it, so never hand-edit that frontmatter as the primary
  interface.
- **Rejected:** project metadata that is edited as YAML first; keeping frontmatter and
  the task in sync by hand.
- **Cost:**
  - Reserved block IDs.
  - Extra sync passes.
  - Frontmatter can look stale until a sync runs.
  - Converting a note must preserve the `^prj` subtree.
- **Reopens when:** a note type's lifecycle stops being shaped by task completion.
- **Evidence:** `docs/projects.md:18-19` ("the task line is the interaction point, and
  the command reconciles frontmatter from" it); `b6a9b4c`; `ea130d6`.

**11. `vault-writers-refuse-on-ambiguity`: Vault Writers Refuse On Ambiguity Instead Of
Guessing**

- **Summary:** When a vault write is ambiguous, `bob` commands and plugins refuse or skip
  with a located message and write nothing. They never make a best guess. Examples of
  ambiguity:
  - a missing daily note or `Pomodoros` section
  - several open timed Pomodoros
  - duplicate or colliding IDs
- **Why:** the vault is Bryan's system of record, and much of it is written unattended.
  The pattern recurs across repos:
  - `README.md:398` (task-status-hooks refusals)
  - `block-id-prompt/main.js:3054-3058` ("reported as an error rather than silently
    picking one")
  - `docs/task-status-hooks.md:90`
  - gkeep archives rather than deletes
- **Rejected:** best-effort repair heuristics.
- **Cost:** more refusals for Bryan to resolve by hand.
- **Reopens when:** one class of refusal recurs and has a provably safe resolution. Then
  encode *that* resolution, not a general guess.

### 6.2 Confirm first: Bryan must decide or explain these before they are recorded

1. **Who owns the vault format rules, and in which direction does mirroring go?**
   - This is the most valuable record, and it is not yet decided.
   - The Mac app follows a strict thin-client rule (record 1). The plugins, however,
     *re-implement* bob-cli's rules in JS and never shell out.
   - Mirroring runs **both ways**:
     - bob-cli's `src/native/capture_schedule_log.rs:18-22` cites `main.js` constants.
     - `capture_task_toggle.rs:38` tracks unifying the two as "a follow-up".
     - The copies have already drifted (record 8's Cost).
   - Proposed record, once Bryan answers: *"bob-cli's Rust is the reference for vault
     format rules. Plugins mirror in-process for editor-transaction and latency reasons,
     every mirror cites its Rust source, and a rule change updates every mirror in the
     same epic."* Do not write it by inference.
2. **Native Rust, and a template for foreign runtimes.**
   - Commands have been native Rust since `24d26c5` (2026-06-01). Shell survives only
     behind `BOB_CLI_USE_SCRIPT=1`, for the notification and Pomodoro family.
   - `grk`, `mus` and `gem` would seed this now. `cdx` and `cld` ask first, and I agree.
     Two questions are still open:
     - Is the shell fallback permanent, or leftover from the migration?
     - Is "a foreign runtime only behind a pinned subprocess adapter" (the `uv`-spawned
       gkeep adapter) the standing policy for new integrations?
   - That second clause is the valuable one, because agents often reach for Python.
   - Do **not** borrow sase's stronger `rust-core-required` wording. Bob still has an
     escape hatch.
3. **`#now` is a commitment; `[/]` is a footprint.** `gem` wrote this up as accepted and
   dated it today. It is actually a *conditional proposal*:
   - `research:202609/now_tag_vs_in_progress_status.md` opens with "*If* Bryan adopts…".
   - Nothing in `docs/` mentions `#now`.
   - If Bryan adopts it, it is an ideal **first new record**, written the day it lands.
4. **Record 7's confirmation** (the stale README line). This is a one-word answer.

### 6.3 Backlog: write each when an epic next touches the area

| Candidate | One-line rule | Evidence |
| --- | --- | --- |
| `capture-draft-atomic` | `bob capture` plans every item against in-memory snapshots and writes all or nothing. | `a8c9ad8` (`feat(capture)!`); `plan:202608/multi_capture.md`. The client-side clause is already in record 1. |
| `capturecore-foundation-only` | Non-UI logic lives in the Foundation-only `CaptureCore` so Linux agents can build and test it. | `Package.swift:5-6`; the mac replacement research §7. Largely self-enforcing on Linux builds. |
| `native-query-engine` | `bob query` evaluates Dataview and Tasks with a native Rust evaluator, without Obsidian running. `--engine obsidian` is opt-in. | `271fae6` (dynomark removed); `docs/dataview.md:7-12` |
| `automation-reveals-never-replans` | Scheduled jobs surface state and never re-plan. `randomize` runs only on demand. | `docs/randomize.md`; the closed-day automation research |
| `gkeep-archive-after-proof` | Keep notes are archived only after their content is verified in the vault, and never deleted. | `docs/gkeep.md` |
| `preview-never-mutates`, `draft-text-private`, `bob-lookup-no-login-shell` | Mac-side safety and privacy rules. | Mac README |
| `managed-logs-never-auto-created` | Automation prepends to an existing Schedule or Work Log but never creates one. | bob-plugins `d6a9f26`, `786fc1d`. First separate the stable choice from the changing format. |

### 6.4 Explicit non-candidates

- **The `parent` frontmatter rule.** It is a rule with no known rejected alternative or
  reasons, so it fails tests (1) and (5). Keep it in `obsidian.md`, which sase agents also
  see.
- **Keymaps, including `gem`'s "Vim leader chord partitioning".** I found no evidence of
  a partition policy in bob-plugins, and keymaps demonstrably churn (`1de6f93`).
- **Capture grammar punctuation, CLI flags and sort rules.** These are owned by
  `docs/capture.md` and `cli_rules.md`.
- **Per-plugin versioning and the private repo.** Local to the bob-plugins README.
- **The `Scripts/xcode-swift.sh` toolchain wrapper.** It is real, but it is build hygiene
  and belongs in the README.
- **"Rust files are at most 1,500 lines".** This would be a **false** record:
  `src/native/capture_complete.rs` is 2,937 lines.
- **Glossary terms.** Keep them in the glossary web. `cld` suggests an optional
  `glossary:task-status` strand for the marker vocabulary (`[ ]` `[*]` `[/]` `[?]` `[x]`
  `[-]`), which record 6 could link to. This is worthwhile, but it is a separate change.

---

## 7. Drift found during research (fix alongside the launch or file as beads)

| Drift | Evidence | Fix |
| --- | --- | --- |
| The plugins README calls the plugin sole source of truth "a deliberate later decision" | bob-plugins `README.md:165`, but `docs/vault-git-sync.md:230` and home `obsidian.md` say the plugins "stay gitignored" | Update the README once Bryan confirms. |
| The README Environment lock list omits `gkeep pull` | `README.md:738-741` compared with `src/native/gkeep/pull.rs:131` | Add it to the list. |
| Schedule Log entry emphasis differs across copies | `block-id-prompt:90` uses `_`; `task-status-cycler:519` and the Rust `ENTRY_EMPHASIS` use `*` | Depends on the answer to §6.2 Q1. |
| `bob-project-tasks` leaves `?` out of `OPEN_TASK_STATUSES` | `bob-project-tasks/main.js:15` | Check whether this is intentional (Blocked may deliberately not count as "open"). |
| The configured primary checkouts for the linked repos do not exist | `sase repo open bob-plugins` fails with "Primary workspace directory does not exist"; agents fall back to `gh:` external opens | Clone them or fix the configured paths. This matters for §4.3 routing. |

---

## 8. Where the researchers disagreed, and why each was settled

### 8.1 Disagreements

| Issue | Positions | Resolution |
| --- | --- | --- |
| Location | All five: bob-cli project memory | Adopted; the home-web merge was verified in `scope.py`. |
| "The vault in general" | `grk`: drop it as a target. Others: include it. | Include vault **decisions**; leave vault **conventions** in `obsidian.md` (A1). |
| Initial count | 8 (`grk`), 9 (`cdx`), 10 (`cld`, `mus`), 13 (`gem`) | 11, in tiers, with records 1–6 as a minimal launch. |
| Slug prefixes | `gem`: required. `cld`: slugs describe the claim. | Claim-shaped slugs; prefixes group nothing (§5.2). |
| Where scope goes | `cld`/`mus`: `metadata.scope`. `cdx`: a body line. | A body line, because reads do not print metadata (verified). |
| `status: accepted` | `cdx`: omit it. Others: include it. | Include it, matching sase's 20 of 24. |
| `decided` dates | `gem`: dated every record. `mus`/`cdx`: only when proven. | Only when proven. |
| Linked-repo pointers | `cdx`/`cld`: add them. `grk`: not needed. `gem`: add to `obsidian.md`. | Add all three. They are cheap, and `-p bob-cli` reads work from anywhere. |
| Native Rust | Seed now (`grk`, `mus`, `gem`) vs confirm first (`cdx`, `cld`) | Confirm first (§6.2 Q2). |
| CommonJS | Seed (`cld`, `grk`, `gem`) vs defer (`cdx`) | Seed (record 8). |
| Shared lock | Seed (4 reports) vs defer (`grk`) | Seed (record 5), including `gkeep pull`. |
| Plugin source of truth | Seed (4 reports) vs confirm (`cld`) | Seed after a one-word confirmation, and fix the README. |

### 8.2 Factual corrections to `gem`

Several of `gem`'s claims are wrong. Do not reuse its draft bodies.

- **Why Obsidian Sync was retired.** `gem` gives "opaque race conditions" and data
  corruption. The documented cause is a **quota failure**: 454+ consecutive
  `Vault limit exceeded` errors on 2026-08-27, plus the lack of an unattended conflict
  policy.
- **Dates.**
  - Git sync: `gem` says 2026-08-15; the actual date is **2026-08-27** (`eee290a`).
  - Mac thin client: `gem` says 2026-07-10, but the repo's first commit was
    **2026-08-13**.
- **`bob query`.** `gem` says it runs Dataview through embedded QuickJS "rather than
  reimplementing in Rust". The opposite is true:
  - The native engine is a Rust lexer, parser and evaluator.
  - dynomark was removed in `271fae6`.
  - `rquickjs` is used **only** for Tasks' `by function` instructions, with a vendored
    Moment (`src/native/dataview/tasks/js.rs`).
- **`#now`.** `gem` presents it as accepted. It is a conditional proposal from today's
  research.
- **Vim chord partitioning.** There is no evidence of a policy or of tests enforcing it.
- **Unverified numbers.** "Shell startup >200 ms" and "subprocess ~5–10 ms" are not
  supported by any source I found. The evidence that exists is a 20 s timeout and lane
  cancellation.

This is the invented-rationale failure mode, as it happened. It is why every record must
pin evidence.

---

## 9. Implementation and governance

1. **Authorization.**
   - This research does not authorize any memory edit.
   - Under `/sase_memory_write`, the launch needs one of two things:
     - Bryan asks for it directly in a prompt, or
     - an approved `sase plan` whose steps name every file: the descriptor, each record,
       the pointer stubs, the `obsidian.md` line and the doc-drift fixes.
   - The linked-repo and chezmoi edits are commits in *those* repos.
2. **Author** `sase/memory/decisions.md` and the record files by hand. There is no CLI
   writer; the TUI Memory panel is the alternative.
3. **Validate** before publishing:
   - `sase memory init -c` reports drift without writing.
   - `-d` shows the diffs.
4. **Publish** with `sase memory init`. By default this also commits and pushes; `-C`
   skips that.
5. **Verify:**
   - `sase memory web list` shows `decisions` with 11 strands.
   - `sase memory web show decisions` looks right.
   - Each record reads back cleanly with `sase memory read decisions:<slug> -r …`.
   - `sase doctor` reports no unresolved links or supersession warnings.
   - The generated `AGENTS.md` has a Decisions subsection with no record bodies inlined.
6. **Pointers:** add the bob-plugins `AGENTS.md` section, the new bob-mac-capture
   `AGENTS.md` and `CLAUDE.md`, and the `obsidian.md` line (§4.3).
7. **Growth:**
   - A new record is justified when an epic makes a durable choice (its plan names the
     "write or supersede a record" step), or when an agent actually violates an
     unrecorded choice.
   - Outside an authorized turn, file a `memory` task bead through `/sase_new_task`
     rather than editing.
   - Encourage epic landers to propose records; do not require it, because a requirement
     invites filler.
8. **Review after about a month.** Check `sase memory log` for `decisions:` reads.
   - Tighten the summaries of records that get read.
   - Question records nobody reads. A record that governs no behavior is a candidate for
     retirement by supersession.

---

## 10. Open questions for Bryan

1. **Vault format rules.** Is Rust the reference, and why do the plugins mirror rather
   than call `bob`? (§6.2 Q1)
2. **Native Rust.** Is the shell fallback permanent, and is the pinned subprocess adapter
   the template for foreign runtimes? (§6.2 Q2)
3. **Plugins.** Confirm the repo is the sole source and that the vault gitignores the
   `bob-*` plugins. (§6.2 Q4)
4. **`#now`.** Adopt it? If so, it becomes the first new record.
5. **Launch size.** The full 11, or the minimal 6 (records 1–6)?
6. **`decided` dates.** Backfill them from commit dates where proven (my recommendation),
   or put them only on new records?

---

## 11. Recommended solution

1. **Build one `decisions` memory web in bob-cli's project memory:**
   `sase/memory/decisions.md` plus a flat `sase/memory/decisions/<slug>.md`.
   - It covers bob-cli, bob-plugins, Bob Mac Capture, and vault *decisions*.
   - Vault *conventions* stay in home `obsidian.md`.
   - No home web, no per-repo webs, and no `docs/adr/`.
2. **Copy sase's format exactly:**
   - the descriptor keys and a one-paragraph preamble
   - `roster: list`
   - the Claim / Why / Cost / Reopens-when body
   - `metadata.status: accepted`, with `decided` only when proven
   - authored links
   - supersession, never in-place edits
3. **Add** an `**Applies to.**` line to each body, and write every summary as an obeyable
   rule.
4. **Gate every record** with the six-part admission test (§5.3). Pinned evidence or
   Bryan's word is mandatory.
5. **Launch with the 11 records in §6.1,** or records 1–6 for a minimal launch:
   1. thin client
   2. additive contract
   3. git-only sync
   4. conflict quarantine
   5. one lock
   6. derived status
   7. plugin deploy
   8. CommonJS
   9. note-qualified dependency IDs
   10. task-line interaction point
   11. refuse on ambiguity
6. **Ask Bryan** the §6.2 questions. Add the confirmed records, then grow from the §6.3
   backlog as areas are touched.
7. **Add the pointer stubs** in bob-plugins, bob-mac-capture and `obsidian.md`, and
   **fix the §7 drift** in the same rollout.
8. **Ship it through an approved plan** that names every file. Then run
   `sase memory init`, `sase doctor`, and a read-back of each record.
9. **Review the read log after a month,** and keep the web small enough that its roster
   stays worth loading on every turn.

## Sources

- Researcher reports in this directory: `__cdx`, `__cld`, `__grk`, `__mus`, `__gem`.
- sase checkout `c2aec595c8`:
  - `sase/memory/decisions.md` and `decisions/*.md`
  - `src/sase/memory/web/{scope,supersession,validation,discovery}.py`
- bob-cli:
  - `README.md`
  - `docs/{vault-git-sync,task-status-hooks,capture,projects,dataview,plugins}.md`
  - `src/native/{capture_schedule_log,capture_task_toggle}.rs`
  - `src/native/gkeep/pull.rs`
  - `src/native/dataview/tasks/js.rs`
- bob-plugins at `d98f677`: `README.md`, `AGENTS.md`, `plugins/*/main.js`, commit history.
- bob-mac-capture at `ff41276`: `README.md`, `Package.swift`,
  `Sources/CaptureCore/{BlockIDRules,BobProcessClient}.swift`, `Scripts/xcode-swift.sh`.
- Research:
  - `research:202608/obsidian_vault_git_sync/obsidian_vault_git_sync.md`
  - `research:202608/bob_mac_capture_replacement/bob_mac_capture_replacement.md`
  - `research:202609/now_tag_vs_in_progress_status.md`
- Home memory: `obsidian.md`.
- External ADR guidance, cited by `cdx`:
  - AWS Prescriptive Guidance (the ADR process and best practices)
  - UK GDS "Documenting architecture decisions"
  - Martin Fowler, "Architecture Decision Record"

# Designing `bob gkeep`: a safe Google Keep → Obsidian migration

**Researcher:** cdx  
**Date:** 2026-09-28  
**Scope:** independent design research; no peer reports were consulted

## Executive judgment

The goal is worthwhile, but the apparently simple requirement hides a hard platform
constraint: Google does not offer a supported consumer Keep API that can enumerate the
web app's Home view and archive those notes. Google's current official Keep API is for
enterprise administration. Its note resource has no archived or pinned field, its list
filter cannot filter archive state, and the only note methods are create, get, list, and
delete. It therefore cannot implement this workflow even if the account is eligible.

I would still build `bob gkeep`, but I would treat it as a **one-way, snapshot-backed
migration tool**, not as a new synchronization system:

1. Import an official Google Takeout export, which includes note content, list items,
   attachments, pinned/archived status, collaborators, and labels.
2. Select exactly the records that were in Keep Home (`!archived && !trashed`) at the
   snapshot time.
3. Plan, write, re-read, and structurally verify their representation in
   `~/bob/gkeep_inbox.md`, with a resumable manifest and stable identities.
4. Only then offer a separate, explicit archive step. In v1 this should open Keep and
   guide the user through Google's documented Select All + Archive shortcut. Archive is
   reversible, and a human checkpoint is much safer than maintaining a private Google
   protocol client.
5. If live listing and automatic archival remain non-negotiable, run a bounded
   feasibility spike for headed Playwright automation using a dedicated browser profile.
   Keep that backend experimental and never make it the only route to the user's data.

This adjusts the original requirement in two important ways: migration and source
archival become separate commands, and "Google Keep list" means an explicitly dated
Takeout snapshot in the supported v1 rather than pretending it is live. Those changes
are justified by data safety, platform support, and the one-time nature of the job.

## What Google actually supports

### 1. The official Keep API is not a consumer inbox API

Google describes the Keep API as an enterprise-administrator API for use cases such as
CASB auditing. Authorization is based on domain-wide delegation by a Workspace super
administrator ([API overview](https://developers.google.com/workspace/keep/api/guides),
[Java quickstart](https://developers.google.com/workspace/keep/api/guides/java)). That is
already a poor fit for an ordinary personal Keep account.

More importantly, account eligibility would not solve the product requirement:

- The current `Note` resource exposes title, body, timestamps, trash state,
  attachments, and permissions, but not archive state, pin state, labels, color, or
  reminders ([Note resource](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes)).
- `notes.list` filters only creation, update, trash time, and trash state. It cannot
  distinguish Home from Archive
  ([notes.list](https://developers.google.com/workspace/keep/api/reference/rest/v1/notes/list)).
- The published method surface is create/delete/get/list and permission management;
  there is no note update/patch/archive operation
  ([REST reference](https://developers.google.com/workspace/keep/api/reference/rest)).
- The Workspace release notes still describe the API's 2021 launch as enterprise-admin
  functionality, with no later archive capability announced
  ([release notes](https://developers.google.com/workspace/release-notes)).

**Conclusion:** do not build around the official Keep API. It cannot identify the
requested source set or perform the requested terminal action.

### 2. The Data Portability API does not currently cover Keep

Google's Data Portability API would be conceptually ideal, but Keep is absent from its
published resource groups and schema references. The documented products currently
include Chrome, Maps, Play, Search, Shopping, and YouTube, among others
([overview](https://developers.google.com/data-portability/user-guide/overview),
[scope list](https://developers.google.com/data-portability/user-guide/scopes),
[schema index](https://developers.google.com/data-portability/schema-reference)). It
also creates asynchronous archives rather than mutating source state.

**Conclusion:** re-check this before implementation in case Google adds Keep, but it is
not a present solution.

### 3. Google Takeout is the strongest supported read path

Google explicitly supports exporting Keep data for use in another service. Its export
includes:

- note text and list items;
- voice, drawing, and image attachments;
- color;
- pinned and archived status;
- collaborators; and
- the user's labels.

That is almost exactly the fidelity needed for this migration
([Google Keep export help](https://support.google.com/keep/answer/10017039)). Takeout is
not live and does not archive notes, but those are acceptable limitations for a one-time
bridge.

The exact Keep JSON schema is not formally specified on that help page. Before coding,
obtain a small fresh export containing a deliberately varied set of notes and turn a
sanitized copy into test fixtures. The parser should be schema-tolerant for additive
fields but fail closed when a content-bearing shape is unknown. The implementation must
not guess field names from internet snippets and then archive the originals.

### 4. The unofficial private API is powerful but the wrong foundation

[`gkeepapi`](https://github.com/kiwiz/gkeepapi) can read archive, pin, label, color,
list-item, and note state and can set `archived = true`. I inspected version 0.17.1 at
commit `1a94b25` (2026-01-05). It is active enough to merit consideration, but its own
documentation is candid:

- it calls Google's **private mobile Keep API**;
- authentication requires an account "master token" with full account access;
- password login is deprecated and unlikely to work;
- backups are recommended;
- labels/blobs have unstable interfaces;
- reminders are present in source but reminder synchronization is disabled; and
- blobs/attachments remain an explicit TODO area.

This is more than ordinary dependency risk. Google's API user-data policy says not to
use or reverse-engineer undocumented APIs and to access data only through documented
means ([Google API Services User Data Policy](https://developers.google.com/terms/api-services-user-data-policy)).
A full-account master token is also disproportionate to migrating Keep notes. Embedding
Python plus `gkeepapi`/`gpsoauth` into this Rust CLI would complicate packaging and leave
Bob responsible for a brittle authentication path.

**Conclusion:** do not ship `gkeepapi` as the default or recommended backend. At most,
keep it as an explicitly unsupported personal experiment outside the core command.

### 5. Browser automation is feasible, but should be an optional second phase

A headed browser can work with the same UI the user sees, and Google documents keyboard
shortcuts for Select All and Archive (`Ctrl/Cmd+A`, then `e`)
([Keep keyboard shortcuts](https://support.google.com/keep/answer/12862970),
[archive help](https://support.google.com/keep/answer/6262765)). It avoids the
full-account master token and can use the user's normal interactive Google login.

It is still not a stable API:

- Keep's DOM, accessibility names, virtualization, and loading behavior can change.
- Google login can present MFA, CAPTCHA, or risk challenges.
- Browser state is a bearer credential and must be protected like a password.
- Playwright warns that Chrome 136+ does not permit automation of the default Chrome
  profile; a separate automation profile is required
  ([Playwright persistent context](https://playwright.dev/docs/api/class-browsertype),
  [authentication state](https://playwright.dev/docs/auth)).
- Google's general terms constrain automated access that violates machine-readable
  instructions, so policy compatibility should be explicitly reviewed rather than
  assumed ([Google Terms](https://policies.google.com/terms)).

If explored, the browser backend should be headed, interactive, separately profiled,
and disabled for unattended schedules. It should archive verified notes one by one,
checking an identity and revision immediately before each action. A blind Select All is
acceptable for a human after review, but not for code: a note created after the export
could otherwise be archived without having been migrated.

## Critique of the proposed product

### What is good about it

- It consolidates two inboxes into the system where tasks are actually managed.
- Archiving rather than deleting preserves a reversible source copy.
- A dedicated `gkeep_inbox.md` cleanly contains provenance and makes verification easy.
- A combined list is valuable as a reconciliation view, not merely as pretty output.

### What is risky or underspecified

1. **"Item" is ambiguous.** A Keep object can be a plain note, checklist, image note,
   drawing, audio note, shared note, or a mixture. A checklist note is one archive unit
   but contains several potential tasks.
2. **"Inbox" is not an API concept.** Here it should be defined precisely as the Home
   projection at snapshot time: not archived and not trashed; pinned notes are included.
3. **Cross-system atomicity is impossible.** A local file write and a Google archive
   mutation cannot form one transaction. The workflow must be resumable rather than
   pretending to be atomic.
4. **A successful write is not sufficient proof.** Before any archive action, the tool
   must prove every source object has one structurally equivalent destination block and
   every attachment expected to migrate was copied and hashed.
5. **Ongoing live sync would be a maintenance trap.** There is no supported event or
   consumer API, and two-way completion semantics would introduce conflicts immediately.
6. **Private-API credentials are too powerful.** The convenience is not worth storing a
   Google master token for a one-time migration.

### Requirements I would deliberately adjust

| Original intent | Recommended adjustment | Why |
| --- | --- | --- |
| One migration subcommand writes and archives | `migrate` writes/verifies; `archive` is a separate explicit checkpoint | A local/remote transaction cannot be atomic; retries must never duplicate tasks or lose source data |
| List "Google Keep" live | v1 lists an explicitly dated Takeout snapshot; experimental browser listing may come later | No supported consumer live-list API exists |
| Migrate every object no matter its shape | Represent losslessly or mark the note blocked and do not archive it | Attachments, reminders, drawings, and unknown fields must not disappear silently |
| Build a recurring bridge | Treat v1 as a one-way migration utility | The likely use is finite; permanent automation cost is unjustified |
| Automatic source archive by default | Guided, confirmed archive in v1; per-note browser archival only after a successful spike | A human action is reversible, documented, and safer than private protocols or blind batch automation |

If ongoing mobile capture is the actual goal, the better long-term solution is to route
future captures directly to Bob (for example through the existing Mac capture workflow,
a share sheet, or a very small mobile capture endpoint) and retire Keep as an inbox.

## Recommended command design

The CLI should make the state transition obvious and make read-only inspection the
easiest action.

```text
bob gkeep list [--source snapshot|obsidian|both] [--takeout PATH]
               [--format table|json]

bob gkeep migrate <TAKEOUT-PATH> [--dry-run] [--bob-dir DIR]
                  [--format human|json]

bob gkeep status [--format human|json]

bob gkeep archive [--transaction ID] [--open]
```

Behavior:

- `list` defaults to `both` when a previous snapshot exists; otherwise it explains
  exactly what is missing. Every snapshot row/header shows `as of <timestamp>` so stale
  data is never presented as live.
- `migrate --dry-run` parses and validates everything, shows the planned mapping and
  blockers, and writes nothing. Plain `migrate` performs the identical plan, writes the
  note/assets and journal, re-reads them, then reports either `ready-to-archive` or
  `blocked`.
- Re-running `migrate` is idempotent. It never duplicates an already represented source
  key. If the generated block was user-edited and the source snapshot also changed, it
  reports a conflict rather than choosing a winner.
- `status` describes the latest transaction: snapshot count, eligible Home count,
  imported, verified, blocked, archive acknowledged, and exact next command.
- `archive` refuses unless the selected transaction is completely verified. In v1,
  `--open` opens `https://keep.google.com/#home`, prints the expected note count and the
  documented shortcut, and waits for an explicit user acknowledgment. It records that
  acknowledgment but does not claim it independently verified Google's state.
- If a browser backend is later proven reliable, add
  `bob gkeep archive --backend browser --transaction ID`; never change the safe default
  silently.

Example human output:

```text
Google Keep migration  2026-09-28T14:22:09Z

SOURCE SNAPSHOT     37 Home notes  ·  4 rich notes  ·  6 checklists
OBSIDIAN             37 verified   ·  0 missing     ·  0 conflicts
ATTACHMENTS          12 copied     ·  12 verified

✓ gkeep_inbox.md is ready
→ bob gkeep archive --open
```

Use the repository's existing `Styler`, honor `NO_COLOR`, keep stdout machine-clean for
JSON, and send diagnostics to stderr. The beauty should come from hierarchy, alignment,
clear verbs, and restrained color rather than decorative noise.

## Data model and Markdown projection

### Migration unit

Use **one Keep note = one top-level Obsidian task**. This preserves the same count and
archive unit and gives reconciliation an unambiguous invariant. Checklist entries remain
indented checkboxes under that task; they retain checked state but should not receive the
Bob `#task` tag by default, avoiding an accidental explosion of independently managed
tasks.

Suggested projection:

```markdown
# Google Keep Inbox

## Tasks

- [ ] #task Groceries [created::2026-09-24] ^gkeep-6f3w9a2k7m4q
  - [ ] milk
  - [x] coffee
  > [!info]- Google Keep details
  > Labels: errands
  > Snapshot updated: 2026-09-27T18:42:11Z
  <!-- bob:gkeep source=6f3w9a2k7m4q snapshot=sha256:... -->
```

Projection rules:

- The top task stays open because "migrated from an inbox" is not the same as "done".
- Its description is the title, or the first non-empty content line, or a readable type
  fallback such as `Untitled Google Keep list`.
- Remaining plain-note text is preserved under the task in a collapsed callout or
  indented paragraphs. No line may accidentally become a Bob task, inline field, tag,
  or block ID through unescaped source text.
- Checklist order, nesting, and checked state are preserved below the parent.
- Labels, color, pin state, collaborator names, reminders, and source timestamps are
  metadata, not automatically transformed into Bob tags, priorities, schedules, or
  assignees. Such mappings change semantics and should be an explicit future option.
- Attachments are copied to a deterministic vault directory such as
  `gkeep_assets/<source-key>/`, referenced relatively, and verified by SHA-256. A missing
  or unsupported attachment blocks that note from ready-to-archive status.
- Generate an Obsidian-safe block ID (`A-Z`, `a-z`, `0-9`, `-`) from a collision-checked
  digest. Do not expose or trust raw Google filenames as IDs.
- Keep machine provenance in a compact HTML comment so normal reading stays clean. The
  journal stores the full mapping.

Takeout may or may not expose a stable native note ID in the current schema. Phase 0
must establish this from a real export. Prefer a native ID when present. Otherwise use a
versioned identity derived from immutable-looking export attributes (not merely title or
content), retain the export-relative path in the manifest, and detect collisions. Do not
promise cross-export identity until fixtures prove it.

## Reliability model

### Transaction manifest

Write a content-free or content-minimized manifest under
`$XDG_STATE_HOME/bob-cli/gkeep/transactions/<id>.json` containing:

- transaction and schema version;
- input archive hash and snapshot timestamp;
- source key, source revision/hash, and classification for every record;
- planned destination block ID and normalized destination hash;
- attachment source/destination hashes;
- states such as `planned`, `written`, `verified`, `blocked`, and
  `archive-acknowledged`;
- blocker/error codes suitable for JSON consumers.

Do not duplicate complete private note bodies into logs or the state directory. The
Takeout archive and vault are already the data-bearing records.

### Write protocol

1. Validate the Takeout container before extracting: reject traversal paths, symlinks,
   duplicate normalized paths, unreasonable expansion ratios/sizes, and malformed
   encodings.
2. Parse every record and build the complete plan before writing anything.
3. Acquire Bob's shared maintenance lock so capture/status maintenance cannot race the
   update.
4. Snapshot the destination and all relevant assets. Refuse if they change between plan
   and apply.
5. Stage all new bytes, fsync where supported, and atomically rename using the patterns
   already present in `task_status_hooks_write`/capture code. Roll back newly created
   assets if the note write fails.
6. Re-open `gkeep_inbox.md` with Bob's task scanner and verify every expected block ID,
   normalized payload, source key, and attachment hash.
7. Atomically persist the transaction manifest as `ready-to-archive` only when counts
   and content match exactly.

An archive failure must never roll back the local import or cause a duplicate on retry.
The manifest simply remains `verified` with a pending archive action. If browser
automation is later added, re-fetch/re-open each source note immediately before archive,
compare its revision/content identity to the imported version, archive it, and verify it
left Home. Changed notes become conflicts and remain unarchived.

### "Successful" must mean all of the following

- every eligible snapshot note has exactly one destination block;
- every expected text/list item and status has a normalized representation;
- every expected attachment exists and matches its hash;
- the destination re-parses with no duplicate generated IDs;
- the source snapshot and destination did not change during apply; and
- no note has a warning classified as content loss.

Warnings about cosmetic metadata may be acknowledged explicitly, but a content warning
must be a hard blocker.

## Fit with the current `bob-cli` codebase

This should be a native Rust command, consistent with `projects`, `plugins`, and other
modern Bob commands:

- add alphabetically sorted `gkeep` to `runner.rs` and `NativeCommand`;
- implement `src/native/gkeep.rs` or a focused directory with `cli`, `takeout`,
  `projection`, `journal`, and `render` modules;
- reuse `env::bob_dir`, `Styler`, `note_tasks`, SHA-256 support, and the shared
  maintenance-lock/atomic-write machinery;
- use Clap subcommands and stable serde JSON output;
- preserve the repository's `#task`, `[created::YYYY-MM-DD]`, Tasks-section, and block-ID
  conventions;
- add a ZIP dependency only if accepting the archive directly materially improves UX.
  Supporting an extracted `Takeout/Keep` directory first reduces attack surface and
  makes fixture testing simpler.

The existing `gkeep_inbox.md` file, if any, is user-owned. The tool should insert only
under its `Tasks` section and update only blocks carrying its own provenance marker.
Never rewrite the entire file from a template or remove unrecognized user content.

## Verification and test plan

### Fixture matrix

Create sanitized fixtures from an actual current Takeout export for:

- titled and untitled text notes;
- multiline Markdown-looking content and Unicode;
- duplicate titles and identical content created at different times;
- lists with checked, unchecked, empty, and nested items;
- pinned, archived, trashed, colored, labeled, and shared notes;
- image, drawing, audio, and multiple attachments;
- reminder-bearing notes and unknown/additive fields;
- malicious archive paths, oversized entries, missing assets, and malformed JSON.

### Behavioral tests

- dry-run/apply plan equivalence;
- second-run idempotency;
- generated-ID collision handling;
- destination edit and source revision conflicts;
- partial asset/write failure cleanup;
- concurrent destination change rejection;
- byte-for-byte attachment verification;
- stable human output without ANSI in non-TTY mode and stable JSON schemas;
- exact Home filter semantics (`!archived && !trashed`, pinned included);
- no source-mutation code reachable from `list`, `status`, or `--dry-run`.

Any Playwright backend needs separate opt-in contract tests against a disposable Keep
account, traces/screenshots on selector mismatch, and a kill switch. Do not exercise a
real personal account from normal CI.

## Delivery sequence

1. **Schema spike:** create the minimal varied Keep dataset, export it through Takeout,
   document the actual schema/identity behavior, and commit sanitized fixtures.
2. **Read-only slice:** implement `list` and `migrate --dry-run`, with human and JSON
   output and every lossiness blocker.
3. **Safe local apply:** implement atomic writes, assets, journal, re-parse verification,
   and idempotent retry.
4. **Guided archive:** implement `status` and `archive --open`, with transaction gating,
   expected counts, instructions, and explicit acknowledgment.
5. **Optional live spike:** only if still valuable, test headed Playwright enumeration
   and per-note archival with a dedicated profile. Ship it experimental only after it
   can prove identity, detect concurrent edits, and verify postconditions.
6. **Exit Keep as an inbox:** provide a direct future-capture route into Bob so the
   migration does not become a permanent sync service.

## Recommended solution

Implement `bob gkeep` as a native Rust, one-way, Google-Takeout-backed migration with
`list`, `migrate`, `status`, and a separately gated `archive` command. Map one Keep note
to one top-level `#task`, preserve list state and all rich content beneath it, copy and
hash attachments, embed unobtrusive stable provenance, and maintain an atomic resumable
transaction manifest. Make `migrate --dry-run` the review path, make retries idempotent,
and never mark a transaction archive-ready unless a full re-parse proves a lossless
destination.

For v1, have `archive --open` guide the user through Google's documented Select All +
Archive action after showing the verified count; clearly label this as user-confirmed,
not machine-verified. Do not use the enterprise Keep API, the undocumented mobile API,
or a Google master token. If truly live listing and automatic archive are still worth
the maintenance and policy risk, add a headed, dedicated-profile Playwright backend only
after a focused feasibility spike, and keep the Takeout path as the durable safety net.

# Declarative crontabs through chezmoi: independent research and recommendation

Researcher: **cdx**. Research date: **2026-11-07**. Scope: design research, read-only machine inspection, and isolated compatibility experiments. No live crontab, scheduler, SSH configuration, or chezmoi source was changed. No other swarm researcher's report, transcript, or findings were consulted.

**Recommendation:** adopt the single-file, Git-backed interface. Use chezmoi to deliver a per-machine desired configuration and run a small, idempotent local reconciler after each apply. Initially own a clearly marked section of the user's crontab, preserving other entries. Supply a documented command interface for local and remote inspection, preview, deployment, and verification. Retain cron for the existing jobs; consider native schedulers individually when their execution semantics justify migration.

The largest issues are ownership of the existing table, reliable noninteractive deployment, and the difference between installing a schedule and successfully executing it. The actual environment makes all three concrete.

## Evidence from this environment

The chezmoi repository was opened through `sase repo open chezmoi`; its inspected revision was `f1da6b641eca9616d687689a30e62eba12553f47`. Repository paths below are relative to that checkout. Tailnet information came from the audited `tailnet.md` memory read, checked against the repository's SSH template. The observations are snapshots, not promises that machines will remain reachable or unchanged.

| Subject | Observed result | Design consequence |
| --- | --- | --- |
| Current execution host | `hostname` and chezmoi's hostname both report `athena`; account is `bryan` | This research is actually running on Athena, despite the request's reference to a different machine. Do not infer the identity of that third machine. |
| Athena crontab | Three active entries: Bob nightly at 03:30, password-store sync hourly, and a SASE epic watchdog at minute 23 each hour | A wholesale replacement would need to account for an existing automation-owned entry. |
| Athena environment | Crontab contains a home path, numeric UID paths, display/session variables, and a mail recipient; the nightly command explicitly initializes profile and Node tooling | Copying these literals into a supposedly portable file would preserve hidden machine dependencies. |
| Apollo | Batch SSH succeeded as `bryan`; `crontab -l` reported no crontab | Good example of an initially unmanaged machine. An absent configuration must not create or erase a table. |
| Mac | Batch SSH to `mac` timed out after an eight-second connection limit | Its current table, OS version, chezmoi version, and write permission were not verified. |
| Athena chezmoi | `v2.13.1`, from a Nix profile | Do not design solely against today's documentation. |
| Apollo chezmoi | Plain noninteractive `chezmoi` was not found; probing conventional executable locations found `v2.70.2` | Remote execution needs executable discovery/bootstrap, not an assumed interactive PATH. |
| Source layout | `.chezmoiroot` contains `home` | Proposed managed files and special files belong under `home/`. |
| Existing integration | `home/.chezmoiscripts/run_onchange_after_enable_bob_ref_intake_timer.sh.tmpl` already installs/enables a systemd timer | Scheduler deployment through chezmoi is already an established pattern here. |

The repository uses `.chezmoi.hostname` values `athena`, `apollo`, and **`Kellys-MacBook-Pro`**. The existing SSH alias for the latter is **`mac`**, its Tailscale name is lowercase, and its SASE machine name is `kellys_mbp`. These are different identifiers. Relevant evidence is in `home/.chezmoiignore`, `home/private_dot_ssh/private_tailnet.conf.tmpl`, and `home/dot_config/sase/sase_kellys_mbp.yml`.

A targeted repository search found old cron-related editor aliases but no current declarative crontab installer. It did find the systemd timer integration described above. This is a targeted code inspection, not proof that no historical or external scheduling tool exists.

### Can agents manage crontabs today?

Agents can already read the current user's table on Athena and, from this host, on Apollo. The standard `crontab` utility accepts a file or standard input for installation without using an interactive editor. Access is governed by the target user's permissions and cron allow/deny policy. There is no inherent requirement that an agent use `crontab -e`. [Debian crontab command reference](https://manpages.debian.org/bookworm/cron/crontab.1.en.html)

**Write access was not exercised.** A successful read is not a write-permission test, and one working SSH direction does not prove every pair of machines works. The Mac's timeout proves neither absence of a table nor denial of access. The user-facing improvement should therefore be a supported workflow with explicit results, rather than a claim that a new low-level capability is needed.

## Is this a good idea?

Yes. Desired schedules are configuration and benefit from one reviewable source, history, and rollback. Editing a checked-in file is considerably easier for both people and agents than discovering and editing live tables on several machines. Chezmoi already distributes the surrounding scripts and environment.

`chezmoi update -a` fits the requested trigger: update pulls the source repository and applies it; apply is already enabled by default, so `-a` is explicit but normally redundant. It acts on the machine where it runs. It does not automatically deploy to every machine named in a configuration file. [Chezmoi update reference](https://www.chezmoi.io/reference/commands/update/)

There are four qualifications:

1. **A crontab is shared mutable state.** Athena's watchdog demonstrates another owner today. A file-to-table replacement with no ownership boundary can delete legitimate work.
2. **Applying configuration is not a schedule health check.** Valid syntax does not prove executables, Node initialization, credentials, network access, output delivery, or desktop permissions work under cron.
3. **Cron is not a durable missed-work queue.** The sleeping Mac is the obvious case. Apple documents skipped cron runs during sleep and recommends launchd; calendar-based launchd jobs can run after waking. That is an execution-policy decision, separate from storing configuration in Git. [Apple scheduling guide, archived](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)
4. **Git history does not undo effects of jobs already executed.** Reverting the source changes future scheduling after deployment. It does not reverse a backup, sync, or maintenance operation.

A single file is appropriate at this scale. Keep it focused on schedules, stable job identifiers, and machine assignment. Putting all the shell implementation and SSH configuration into that same file would make it harder to review.

## Explicit adjustments to the requirements

These are recommendations, not silent reinterpretations:

| Original intent | Recommended clarification or adjustment | Reason |
| --- | --- | --- |
| One checked-in configuration file | One authoritative schedule/assignment file, plus reusable job scripts and generic deployment tooling | A single interface does not require a single implementation file. |
| Only machine names are machine-specific | The schedule file has no usernames, IPs, home-directory literals, UID literals, or OS switches; machine names select jobs. Platform details remain in the adapter and existing SSH configuration. | OS and transport differences cannot disappear, but they need not pollute the schedule data. |
| Update the crontab | Initially reconcile only the explicitly managed section | Preserves the observed watchdog and other external entries. Whole-table ownership should be a later explicit decision. |
| Any machine from any machine | Desired state is editable without target access; live reads and deployment require a reachable, authorized target | An offline laptop cannot truthfully be reported as updated. |
| Apply changes on matching machines | Every apply checks local state; only an actual local difference causes installation | A cheap no-op check can detect drift even when the Git configuration did not change. |
| Future machines may have no jobs yet | Unknown or unmanaged machine means no mutation; an explicitly managed empty job list removes only the managed section | Absence and deletion must not be conflated. |
| Continue editing as before | `crontab -e` becomes an emergency/outside-section tool; ordinary managed changes go through Git | Two authoritative editors otherwise create predictable drift. |

If the user requires *every* job to appear in the single file, the managed-section adjustment is insufficient. In that case, first migrate or retire the external watchdog writer, import all remaining jobs, and adopt exclusive whole-table ownership. Do not freeze an ephemeral watchdog path into permanent configuration just to make the inventory appear complete.

## Alternatives considered

| Approach | Advantages | Costs and fit |
| --- | --- | --- |
| One raw crontab template with hostname branches; replace the whole table | Smallest implementation; familiar syntax | Unsafe adoption here without resolving the watchdog; harder structured inspection and portability validation. Reasonable only with exclusive ownership. |
| One data file, local reconciler, managed crontab section | Fits existing update workflow; preserves outside entries; supports machine-readable agent operations | Requires a small, carefully tested state reconciler and explicit drift rules. **Best fit now.** |
| Ansible inventory and cron module | Existing entry identity, backups, check/diff support, remote execution | Adds another deployment system and runtime to this small chezmoi workflow. Worth revisiting if fleet administration grows. |
| systemd timers on Linux and launchd on macOS | Native service status and platform integration; better options for missed runs | Different calendars, deployment procedures, and lifecycle semantics; a generic translator is substantial additional scope. |
| Central scheduler invoking all machines over SSH | Single control point | Jobs become dependent on network reachability and the controller. Poor default for sleeping laptops and local maintenance. |

Ansible's module manages jobs by a unique comment identifier and supports backups plus check/diff mode. That is useful prior art for ownership and previews even without adopting Ansible. Its documentation also requires escaping cron-special characters. [Ansible cron module](https://docs.ansible.com/projects/ansible/latest/collections/ansible/builtin/cron_module.html)

Systemd calendar timers can catch up after downtime with `Persistent=true`; this option applies to `OnCalendar`, not arbitrary monotonic timers. Existing native timers should remain native. A new job that needs missed-run recovery, dependencies, or service supervision may belong there immediately. [Systemd timer reference](https://www.freedesktop.org/software/systemd/man/252/systemd.timer.html)

Apple's current Terminal guide continues to describe launchd as the mechanism for running managed scripts. Its archived scheduling guide explicitly discourages programmatic cron additions because of the shared table. The managed-section approach reduces that ownership problem but cannot eliminate a race with unrelated writers. Thus retaining Mac cron is a compatibility choice, not a claim that it is Apple's preferred scheduler. [Apple Terminal guide](https://support.apple.com/en-asia/guide/terminal/apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac), [Apple scheduling guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)

I would not require a scheduler migration to solve the immediate configuration problem. If the Mac's actual jobs require reliable catch-up after sleep, choose launchd for those jobs before declaring their scheduling problem solved. Do not promise mechanically equivalent cron-to-launchd translation for all expressions.

## Proposed implementation design

This is a design recommendation, not implemented functionality. Command and file names below are proposed.

### One data file with names as selectors

Use **`home/.chezmoidata.yaml`**, under a namespaced `cron` key. Chezmoi can load static YAML data for templates. [Chezmoi data-file reference](https://www.chezmoi.io/reference/special-files/chezmoidata-format/)

Why that filename instead of the more tidy `home/.chezmoidata/cron.yaml`? An isolated experiment on Athena's installed v2.13.1 failed to expose the latter's `cron` data, while the single `.chezmoidata.yaml` file worked. Current documentation supports the directory form, but that did not establish compatibility with this installed binary. Either use the demonstrated file form now or deliberately upgrade and validate a fleet-wide minimum version before selecting the directory form. [Current data-directory documentation](https://www.chezmoi.io/reference/special-directories/chezmoidata/)

Illustrative data, **not a complete migration of the live tables**:

```yaml
cron:
  version: 1
  jobs:
    bob-nightly:
      schedule: "30 3 * * *"
      script: bin/cron-bob-nightly
    pass-sync:
      schedule: "0 * * * *"
      script: bin/cron-pass-sync
  machines:
    athena:
      state: managed
      jobs: [bob-nightly, pass-sync]
    Kellys-MacBook-Pro:
      state: unmanaged # Inventory its existing jobs before enrollment.
    apollo:
      state: unmanaged
```

The two wrapper scripts are new suggested adapters for the observed commands, not existing files. Their script paths are relative to the target user's home; the renderer resolves them locally. The data contains no `/home/bryan`, `/Users/bbugyi`, IP, UID, or platform condition. A job with a different schedule gets an explicit job definition rather than hidden hostname logic in its script.

Use the exact `.chezmoi.hostname` value for automatic selection, consistent with the current repository. Transport should reuse existing SSH aliases; the command interface can resolve `mac` to the canonical machine name through one shared identity mapping or target discovery. Do not use SASE's `kellys_mbp` string as an unexamined substitute. A hostname mismatch must stop a targeted deployment before any cron mutation. A rename requires an intentional configuration change; never fuzzy-match hosts.

Strict validation should reject unknown schema versions and fields, invalid schedules, duplicate job IDs or duplicate selected jobs, missing job references, path traversal in script paths, and unexpected multiline values. A small initial schema is sufficient: five cron fields, job IDs, relative script paths, and explicit machine state. Features such as per-job time zones and calendar exceptions should be added only when there is a real need.

### Rendering and local application

Suggested source files:

- `home/.chezmoidata.yaml`: the schedule source of truth.
- `home/dot_config/dot-cron/private_desired.json.tmpl`: rendered local intent, machine identity, and target-resolved paths.
- `home/bin/executable_dot-cron`: inspection, validation, preview, reconciliation, and deployment interface.
- `home/.chezmoiscripts/run_after_reconcile_crontab.sh.tmpl`: invokes the local reconciler after files exist.
- Job wrapper scripts under `home/bin/`.

Use chezmoi to parse YAML and emit JSON; a Python 3 standard-library helper can then validate JSON and implement file handling and advisory locking without introducing a second YAML parser dependency. Python availability must be checked during bootstrap, especially on the unverified Mac. A different existing repository runtime is acceptable if its cross-machine availability is better established.

Render only the selected host's jobs into the deployed desired JSON. Otherwise changing Apollo's jobs also changes Athena's rendered file unnecessarily. Deterministic ordering and a hash of the local semantic payload make no-op results clear. Runtime helpers should read the deployed JSON; source inspection should render from the checked-out source. Never parse the same YAML independently through subtly different rules.

Use an **every-apply `run_after_` hook**, not `run_once_`. An unchanged desired payload should produce a read/compare and no installation. `run_onchange_` can be made sensitive to a rendered payload checksum, but it will not notice a manual live-table edit when that payload is unchanged. Chezmoi documents these execution distinctions and recommends idempotent scripts. [Chezmoi script guide](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)

An after hook runs after target files have been updated, so the helper and desired JSON can be installed in the same apply. A cron failure should propagate a nonzero result; other dotfiles may already have changed because this is not a transaction covering the whole home directory. [Chezmoi application order](https://www.chezmoi.io/reference/application-order/)

### Ownership, drift, and installation rules

Represent owned entries with exactly one delimited block:

```text
# BEGIN chezmoi managed cron v1
# job: bob-nightly
30 3 * * * /absolute/target/home/bin/cron-bob-nightly
# job: pass-sync
0 * * * * /absolute/target/home/bin/cron-pass-sync
# END chezmoi managed cron v1
```

The example path is explanatory, not a literal implementation. Generate proper shell quoting and cron escaping for real paths.

The reconciler should:

1. Validate the desired state and target identity before considering a write.
2. Acquire a per-user lock used by all invocations of this helper.
3. Read the live table with `crontab -l`, keeping stdout, stderr, and exit status separate. Recognize a genuinely absent table using a tested platform adapter; permission failures and connection failures are errors, not empty tables.
4. Parse zero or one valid marker pair. Duplicate, nested, or incomplete markers fail without modifying anything.
5. Preserve all outside text. Replace the block in place, or append it during explicitly reviewed enrollment. With `state: managed` and an empty job list, remove only the owned block. Never call `crontab -r` as the implementation of an empty list.
6. Compare the current owned block with the last successfully installed block. If both the live block and desired source changed independently, stop with a conflict. Report manual managed drift rather than silently overwriting it; an explicit reconcile action can accept the desired side. If live already equals desired, recover harmlessly even if state recording was interrupted.
7. Produce the complete candidate, validate it using supported native checks where available, and show a diff on request. Save a private full-table backup and the observed hash before installing.
8. Re-read the table immediately before replacement; if it differs from the observed snapshot, abort and retry from a new preview. Install the candidate through the `crontab` command, then read it back and verify. Record success only after verification.

The full candidate is still installed as one table; a marked block does not create a native cron subtable. The lock serializes this helper, but `crontab -e` and independent programs need not honor it. The final re-read narrows the race without providing a true compare-and-swap transaction. This limitation is a reason to inventory and eventually coordinate other writers, not a reason to claim atomic concurrent editing.

Routine source changes apply without a fresh permission prompt once the machine is enrolled. A conflict is an exceptional condition with useful evidence, not a generic confirmation before every update. Missing enrollment or missing ownership state must not authorize replacement of an existing block without review.

### Keep job environments explicit

Do not add broad `HOME`, `PATH`, `SHELL`, or `MAILTO` assignments to a managed section and assume the comment delimiters scope them. The installer should avoid changing the outside jobs' environment. Managed wrappers should establish their own execution environment and output handling; legacy environment lines can remain untouched outside the block during migration.

Cron syntax has traps: percent signs have special meaning even when the shell expression looks quoted, and restricting both day-of-month and day-of-week gives OR behavior in Debian cron. Prefer simple generated invocations of wrapper scripts to complicated embedded shell pipelines. [Debian crontab format reference](https://manpages.debian.org/bookworm/cron/crontab.5.en.html)

For the two observed Athena jobs, preserve profile/Node initialization and pipeline error behavior until equivalent wrapper behavior has been verified. Derive necessary home and UID values on the target; do not copy numeric runtime paths into the shared YAML. Capture output, define retention, and expose failure results instead of assuming mail delivery works. Specify local scheduler time as the initial schedule interpretation and review daylight-saving behavior for sensitive jobs. No universal `CRON_TZ` assumption is needed.

Installation must not execute job bodies. Operational verification should be an explicit, job-specific action; running `bob nightly` merely to test a new schedule could perform real maintenance. Decide whether overlap is allowed per job, rather than assuming cron serializes invocations.

## First-class agent workflow

Ship a documented executable interface alongside the configuration. An agent instruction/skill can make it discoverable, but should delegate to the executable rather than hold a second implementation. Suggested operations:

| Proposed command | Contract |
| --- | --- |
| `dot-cron show --host NAME --desired --json` | Render desired configuration from the opened source checkout without contacting the target. |
| `dot-cron show --host NAME --live --json` | Inspect the target table and identity; show owned and outside entries separately. |
| `dot-cron check --all` | Validate every configured host offline, including job references and supported syntax. |
| `dot-cron diff --host NAME` | Compare current target state with the proposed local payload, read-only. |
| `dot-cron deploy --host NAME --revision REV` | Update/apply a committed revision through the normal chezmoi workflow, then verify the resulting owned block. |
| `dot-cron status --host NAME --json` | Report reachability, identity, desired/applied hashes, drift, and verification results. |

These commands are a proposed public surface, not commands available today. Avoid inventing a separate job editor in the first version: editing the YAML in the chezmoi checkout is already a good write interface for both humans and agents.

The normal agent sequence is: open the chezmoi repo through SASE, inspect desired/live state, edit the source, validate and review the diff, follow the authorized commit/publication workflow, then deploy when requested. The cron helper should not bypass SASE repository or commit rules. It also should not edit the live managed block as its ordinary write path.

For remote commands, use SSH argument arrays, bounded batch-mode connections, and existing aliases. Resolve executables in a controlled target bootstrap environment; the Apollo PATH failure demonstrates why `ssh HOST 'chezmoi update -a'` alone is insufficient. Do not solve it by copying target usernames or home paths into the schedule YAML.

A `--revision` check matters because `chezmoi update` normally pulls the branch tip. A deploy command can fetch without apply, verify the intended revision and clean source state, then apply. If the target has a different revision or local changes, return that fact rather than claiming the reviewed change was deployed. A full update can also run unrelated chezmoi scripts; expose that scope. A cron-only deployment, if later offered, must select both prerequisites and the reconciliation hook and receive its own coverage.

Result data should distinguish at least `in_sync`, `changed_and_verified`, `unmanaged`, `offline`, `identity_mismatch`, `conflict`, and `failed`. A disconnected Mac can still have a committed desired change; its live status remains offline or pending. Never report queued or intended work as installed.

Bootstrap and acceptance must test each desired SSH direction. Reusing the tailnet configuration avoids a second inventory of credentials and ports, but does not itself establish permission from every future machine. Root/system crontabs remain outside this user-crontab design.

## Experiments and validation boundaries

I used isolated temporary source, destination, config, cache, and state paths with Athena's installed chezmoi. The fixtures were removed afterward and never invoked a real crontab installer.

| Experiment | Result |
| --- | --- |
| Load data from `.chezmoidata/cron.yaml` on v2.13.1 | Template lookup failed because `cron` was absent. |
| Load identical data from `.chezmoidata.yaml` | Worked. |
| Render static YAML plus target identity to JSON using `dict` and `toJson` | Worked and parsed as JSON. |
| Initial apply with distinct every-apply and on-change hooks | Both ran; the after hook observed the already-rendered target file. |
| Unchanged second apply | Every-apply hook ran; on-change hook did not. |
| Change only another host's data | Local rendered content stayed unchanged; on-change hook did not run. |
| Change this host's data, then revert it | On-change hook ran for each transition, including the revert. |
| Athena native `crontab -n sample.crontab` syntax check in an isolated working directory | Accepted a harmless sample without installation. |

The native syntax check initially failed when passed a long absolute scratch path; rerunning with a short relative filename succeeded. A production adapter should test its actual invocation instead of treating a parser probe's failure as invalid schedule syntax. I did not investigate that path-handling behavior further.

This validates the basic chezmoi integration choice, not the unimplemented reconciler. Athena's `-n` option must not be confused with Cronie's `-T` or assumed available on macOS. Native installation is still the final parser; preflight capability detection must be platform-aware. [Debian crontab command reference](https://manpages.debian.org/bookworm/cron/crontab.1.en.html)

Before rollout, meaningful tests should cover preservation of outside bytes, exactly-once adoption of migrated entries, malformed markers, managed drift, missing tables versus permission errors, unknown hosts, managed-empty removal, failed installs, read-back mismatch, competing writes, quoting, and target identity mismatch. Test each supported OS and the lowest supported chezmoi version. Use stubbed crontab commands for destructive failure cases, then controlled live enrollment for final permission checks.

## Rollout and rollback

First inventory and privately back up Athena and the reachable Mac; record which jobs are permanent user intent and which belong to other tools. Keep raw snapshots outside Git when they contain private addresses, paths, or credentials. Read enough of each job's dependencies to preserve behavior.

Next create the data and generic helper, add offline fixtures, and render all hosts without installation. Keep Apollo and the unidentified future machine unmanaged. Enroll Athena by removing the specifically reviewed original rows and adding their managed replacements in the same candidate; otherwise the first apply would duplicate execution. Preserve the watchdog and unrelated comments/environment. Enroll the Mac only after its actual inventory, reachability, and permissions are verified.

After enrollment, a normal source change followed by `chezmoi update -a` should install only the local delta, while a second apply should be a no-op. Exercise a schedule revert through the same path. Prefer source rollback and reconciliation of the owned block; restoring a full backup can erase outside entries added since that backup, so emergency restoration requires a fresh diff.

The outstanding decisions are limited: whether whole-table ownership is mandatory, which Mac jobs need sleep recovery, and what the unidentified third machine's canonical name is. They do not prevent preparing the design and offline tests, but they do affect enrollment.

## Recommended solution

**Proceed with one Git-tracked schedule file in chezmoi, using `home/.chezmoidata.yaml` for compatibility with Athena today. Select jobs by exact machine name, render local desired JSON, and reconcile a marked user-crontab section through an idempotent `run_after_` hook. Provide a small `dot-cron` interface for offline edits/validation and remote inspect, preview, deploy, and verify operations using the existing SSH infrastructure.**

Make the ownership adjustment explicit: the file owns enrolled, long-lived jobs; other writers' entries remain visible and preserved. If exclusive whole-table control is required, resolve those writers before switching modes. Keep runtime paths, credentials, and platform logic out of the schedule data. Treat offline targets and drift as observable states. Retain existing cron semantics during the initial migration, and use native timers selectively where missed-run handling or supervision is an actual requirement.

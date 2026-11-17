# Stop routine Bob plugin sync confirmations without losing deployed work

Researcher: cdx  
Date: 2026-11-17  
Scope: independent research and recommendation; no implementation or live deployment.

## Decision in brief

**Yes: eliminate repeated authorization questions for ordinary, in-scope plugin deployment. Keep the overwrite protection, and address how uncommitted builds reach the shared vault.** The strongest fix combines explicit standing authorization with a host-owned deployment step after successful landing and verification.

The named example is revealing. The archived `ei` continuation did not merely ask whether it could run `bob plugins sync`. It reported that another workspace's uncommitted navigation build was deployed, its author chain had become inactive, and no reachable commit reproduced that bundle. It asked whether it could use `-F` to replace that protected build. Its inherited instructions explicitly required that question. Removing routine command prompts alone would not resolve this case safely. [E1]

I recommend an incremental implementation:

1. State that ordinary deployment of authorized plugin work is already authorized; use an explicit checkout, explicit vault, no implicit pull, and the necessary plugin set.
2. Preserve Bob's existing refusal rules and automate the already-supported recovery when a protected build has landed.
3. Move normal live deployment out of individual editing turns into a trusted, repeatable post-landing deployment step.
4. Treat truly unrecoverable unlanded deployments as exceptions needing a concrete preservation or discard decision, rather than automatically force-overwriting them.

This report does not authorize force, deploy anything, change instructions, or read any peer research report.

## What I examined and what it establishes

### The actual ei incident

I read `sase chat show --agent ei -f raw`, which resolved to `ei--6--6`. Its saved transcript is:

    ~/.sase/chats/202611/gh_bobs_org__bob_cli-ace_run-ei__6__6-261116_200213.md

The latest response reports:

- Monitor `pzm44jv5twdk` failed during `npm test`, before its chained sync ran.
- The vault already held `bob-navigation-hotkeys` 2.86.0, stamped from workspace 10 at source commit `866bb77`, with an uncommitted deployment dated 2026-11-17 00:45:25 UTC.
- The fetched navigation history ahead of its checkout contained `307646c`, described as a separate video zoom change; the protected bundle had not been found in reachable history.
- A dry run refused the overwrite. The agent staged a keep-versus-force question.
- An earlier continuation waited about 29 minutes for the full author chain to settle, and another wait was staged when that chain became active again.

The continuation prompt specifically instructed the agent to ask before forcing an unlanded, abandoned deployment. Thus, this instance is evidence of a deployment ownership conflict and an explicit escalation rule, not evidence that the model spontaneously invented a permission requirement. [E1]

**Limits:** these are the earlier agent's recorded findings, not a fresh inspection of today's vault. I did not independently prove that the deployed functionality was absent from every eventual commit, nor that an inactive author could never resume. One incident does not measure how often ordinary permission hesitation happens across the fleet. The distinction matters: absence of an exact bundle in a bounded history search does not prove its features are absent from a differently generated or refactored build.

### Existing instructions already authorize normal sync

The opened bob-plugins repository's AGENTS.md says agents must run sync after any repository changes. It also says to fetch and reconcile a landed protected build without asking, wait when its author is active, and ask only when the build is unlanded and abandoned. The bob-cli linked-repository description likewise directs agents to sync after their plugin changes. [S1, S2]

The deployment guide supplies the clean-sync recovery sequence: preserve local work, update to the landed commit, sync the clean state, restore and rebuild local work, then sync again. A CLI integration test exercises that recovery without force and asserts preservation of both writers' changes. [S3, S7]

Two instruction issues deserve correction:

- “After any changes” is too broad. A documentation-only change need not redeploy executable assets or wait on a protected plugin. Trigger deployment from the managed build outputs and relevant compatibility dependencies.
- The guide's later prose permits force when a clean commit “contains the work” of unmatched deployed bytes, while AGENTS.md says never force independently. Semantic containment has no mechanical definition here. Replace that ambiguity with one consistent rule: only explicit discard authorization or a defined, machine-verifiable recovery path permits replacement of an unmatched protected deployment. [S1, S3]

### Native command approval is a different layer

In the inspected SASE source, the Codex invocation includes `--dangerously-bypass-approvals-and-sandbox`; the Claude invocation includes `--dangerously-skip-permissions`. That makes a new broad provider allowlist an unlikely fix for this incident. This is a finding about these launcher paths, not a guarantee about every deployed provider version or external review service. [S8]

Anthropic's documentation explicitly distinguishes model instructions from enforced tool permissions. Instructions influence what the model attempts; permission rules determine what the harness allows. A model-created SASE question is therefore a different event from a denied shell call. [Configure permissions](https://code.claude.com/docs/en/permissions)

Classify future interruptions before changing policy:

| Layer | Evidence | Appropriate response |
| --- | --- | --- |
| Model asks about an ordinary authorized sync | No Bob refusal or tool denial; question is about permission alone | Clarify standing authorization and evaluate instruction adherence |
| Bob refuses an overwrite | Deployment stamp/history or dirty-file conflict | Reconcile, preserve, or request one concrete discard decision |
| Provider or automatic reviewer denies a call | Actual rejection with reason | Inspect that policy; authorize only the intended operation through its supported mechanism |
| Build or smoke verification fails | Nonpassing verification evidence | Repair or report the failure; permission does not make the build acceptable |
| An author or deployment remains active | Ownership/liveness evidence | Wait for the relevant deployment state, with bounded monitoring |

Do not implement a blanket “answer yes to anything containing bob plugins sync” handler. The same prefix permits different repositories, destinations, backup locations, and `-F`.

## What sync protects, and what it does not

The current implementation is substantially safer than a raw file copy. [S4–S7]

| Existing mechanism | Benefit | Boundary |
| --- | --- | --- |
| Configured `plugins.sync` allowlist | Only named plugin IDs deploy; selecting an unlisted ID refuses | The allowlist selects plugins; it does not prove code quality or approve every source checkout |
| Managed files limited to manifest.json, main.js, styles.css | Runtime data.json is preserved | Executable plugin code can later change vault data |
| Per-vault host-local lock | Prevents simultaneous cooperating sync writers on that host | It does not serialize a development session or coordinate different hosts |
| Source capture and deployment hashes | Records the deployed bundle and source provenance | A dirty stamp's base HEAD does not identify its uncommitted source changes |
| Ancestor and exact-bundle checks | Protects other checkouts' dirty builds and divergent clean deployments | It proves history/bytes, not feature correctness |
| Backups before replacement; pending then complete stamps | Supports recovery and detects incomplete deployment | Not an atomic multi-plugin transaction or automatic rollback |
| Dirty vault-file check | Refuses overwriting uncommitted tracked vault edits without force | A skipped dirty file may still produce exit 0 |
| Exact-byte verification after copying | Detects copy mismatch | Does not prove Obsidian successfully loaded or exercised the build |

Operational details affect the design:

1. **A bare sync pulls first.** List also pulls unless `--no-pull` is set. A dry run avoids vault writes but can still mutate the source checkout through that pull. The recommended deployment form is `bob plugins sync --repo <opened-checkout> --bob-dir <approved-vault> --no-pull -p <id>`. Refresh source before building and validating, not during deployment. [S4]
2. **Sync itself does not run the build or smoke gate.** The repository guide requires the isolated Obsidian startup check and post-sync deployment match. Calling sync successfully is not equivalent to completing a rollout. [S3]
3. **Exit status alone is insufficient.** Dirty vault-file skips deliberately do not fail the command, and list returns success for drift. Confirm the intended IDs and bytes through the structured result and deployment verification. [S4, S7]
4. **Failure JSON needs improvement for automation.** `run_sync` currently returns an error summary instead of retaining structured per-plugin results when issues exist. A controller should not have to parse prose to distinguish a busy lock from an unmatched deployment. Add typed reasons and preserve partial outcomes. [S4]
5. **The dirty flag covers the whole source repository.** A change unrelated to a given plugin can mark the deployment dirty. The exact-bundle match path can repair some cases, so this is not by itself proof that every dirty stamp contains novel code. [S5]
6. **Missing stamps are permitted.** Existing compatibility behavior is not a complete enrollment policy. A new automated production path should distinguish an absent plugin from an existing unstamped installation and adopt the latter deliberately, rather than treating stamp deletion as recovery. [S5]
7. **The history proof is bounded.** The implementation examines up to 500 plugin-touching commits and requires all stamped assets to match one commit, not a collection of per-file matches. Record “proof not found” accurately; do not translate it into “safe to discard.” [S5]

Plugin deployment is not harmless simply because only three files are copied. Obsidian says plugins inherit its access and can access computer files and the network. Replacing JavaScript can therefore change behavior with effects a file backup cannot undo. That is why narrow authorization and existing verification are justified even when routine human prompts are removed. [Plugin security](https://obsidian.md/help/plugin-security)

## Critique of the proposed direction

The objective is good. Reconfirming an already-authorized routine step consumes attention and lets agents finish source edits while leaving the user's running system behind. The problem statement should, however, be “complete routine deployments without human intervention while preserving concurrent work,” not “make sync never block.”

The ei example exposes a workflow mismatch: editing agents are expected to deploy before their host finalizer commits. Another agent then encounters a deployed dirty bundle whose source has not become durable shared history. Waiting for an entire agent chain does not guarantee a deployable result; that chain can fail tests, resume, or finish with generated output different from what it previously deployed.

Several tempting fixes miss that problem:

| Approach | Assessment |
| --- | --- |
| Add “never ask about sync” everywhere | Useful only when qualified; otherwise contradicts overwrite-preservation rules |
| Allow every `bob plugins sync *` shell command | Does not address the observed layer and includes force/arbitrary arguments |
| Automatically retry with `-F` | Removes the protection most relevant to the reported incident |
| Force after a timeout or when an author disappears | Liveness and age do not prove deployed work is expendable |
| Copy with cp/rsync or remove the stamp | Evades the checks rather than satisfying them |
| Always back up, then force | Improves recoverability but still silently withdraws deployed functionality |
| Ask an additional LLM to approve each conflict | Adds cost and uncertainty; cannot replace byte/history evidence |
| Serialize every editing agent | Excessively broad; serialize promotion of shared runtime state while preserving parallel development |
| Deploy verified landed bundles through the host | Best durable fit; removes the recurring source of orphaned dirty deployments |

A guaranteed zero-question policy would need a stronger product decision: all live plugin builds are disposable previews, and the latest verified mainline is always allowed to replace them. That might be a valid preference, but it explicitly permits loss of in-progress live functionality. The request to stop safely does not establish that tradeoff.

## Proposed requirements, including adjustments

The following are deliberate refinements to the request:

1. **Adjustment: target zero routine authorization questions, not zero refusals.** Preserve content-conflict, verification, and I/O failures as distinct outcomes.
2. **Adjustment: normal live deployment follows successful landing and verification.** Editing turns use scratch-vault testing; the host completes the live rollout. This changes the current deploy-before-finalization habit.
3. **Adjustment: deployment is required only for affected managed assets and compatibility groups.** A docs-only change does not trigger deployment. Interdependent plugins may need a group even if only one source directory changed.
4. **Adjustment: questions concern a concrete preservation decision.** Include the plugin, current and proposed bundle identities, source/author evidence, failure reason, available recovery, and what is known or uncertain about removed behavior.
5. **Adjustment: elapsed time never authorizes force.** A timeout transitions to recovery or one exceptional decision, not silent replacement.
6. **Adjustment: report source completion separately from deployment completion.** A successful commit with a blocked rollout must remain visible and resumable.
7. **Adjustment: routine authority is scoped.** It covers established plugin IDs, approved vault destinations, trusted opened source, and guarded sync. It does not implicitly authorize new plugins, changing the allowlist, enabling plugins, altering vault content, or forcing an unmatched overwrite.

Suggested standing policy, for a future approved instruction change:

> Implementing an authorized Bob plugin change includes its normal guarded deployment to the configured vault. Do not ask separately whether to run sync. Use the explicitly opened source checkout, the intended vault, no implicit pull, and the required plugin set. Preserve Bob's overwrite checks. Reconcile already-landed deployments without a question. Never infer permission to force from this authorization, a timeout, or an inactive author.

Keep the always-loaded rule short and link the detailed recovery workflow. Update the canonical instruction source and rendered bundles through the project's supported process; do not patch generated AGENTS.md files directly. The memory-write rules reviewed for this research require explicit authorization for implementing memory changes. This report proposes them; it does not apply them.

## Implementation design

### First increment: remove ambiguity and make failures actionable

Implement the scoped policy above and align bob-cli's linked-repository description with bob-plugins' deployment guide. Inspect recorded instruction bundles with `sase instructions show` and `verify` when evaluating adherence; a file present in a linked checkout is not evidence that every earlier agent read it. [S10]

Standardize a small deployment runner that:

- Accepts structured source, destination, plugin-set, and verification inputs.
- Uses trusted executable paths and argument arrays rather than constructing an unrestricted shell command.
- Resolves and validates the source and destination; limits plugin IDs to the configured set.
- Runs without force and without implicit pull.
- Checks expected managed hashes, all intended outcomes, and the existing post-sync gate.
- Records source identity, intended bundle, previous deployment identity, outcome, and backup locations.
- Does not report success for skipped files, partial deployment, unrun smoke checks, or stale validation.

For now `-p` selects one plugin, so a multi-plugin runner must deliberately orchestrate IDs or use a reviewed full configured set. Do not invent a repeatable `-p` contract that the current CLI does not implement.

Add an additive structured refusal contract to Bob: reason codes such as lock busy, protected dirty deployment, non-ancestor revision, unknown provenance, skipped dirty target, and copy failure. Preserve per-plugin results on partial failure. The exact names are proposed, not existing API fields.

Automate the documented landed-build recovery while preserving the worker's changes. Stash/restore failures and merge conflicts must not lose work. A separate clean integration checkout can avoid the stash dance, but must be opened through SASE and still prove which bytes will be deployed. Retain the current guard at the final write boundary.

### Second increment: make live deployment host-owned

Use the existing SASE completion infrastructure rather than requiring every model to remember the deployment step. SASE already supports trusted finalizer providers with ordering, and repository-specific after-commit hooks. After hooks run only after a successful commit-producing dispatch, including its push where applicable; they are checkpointed but can repeat after a crash. [S9]

The desired flow is:

    author change
      -> build and verify in isolation
      -> host commits / lands shared history
      -> verify the actual landed bundle
      -> guarded live deployment
      -> confirm installed bytes and smoke result
      -> record rollout complete

Start with a narrowly configured bob-plugins post-commit hook invoking the runner if that fits operational latency; use a dedicated finalizer/provider when durable queued retries and richer state are needed. Do not put an unconditional sync command in a global hook. Verify linked-repository hook configuration is trusted for bob-plugins itself.

Critical details:

- **Verify the landed result.** A rebase or conflict repair can change it. Reuse validation only when its scope and immutable inputs demonstrably match; otherwise rerun the relevant checks.
- **Require durable source before live promotion.** A local commit in an ephemeral checkout alone is insufficient if the checkout can disappear. A successful push/landing or equivalent durable source retention is required.
- **Use an immutable candidate.** Retain the exact generated assets and their source commit. Avoid reading a moving checkout throughout a long deployment.
- **Serialize promotions to a shared target.** Retain Bob's short host-local lock. The controller also needs ordering and revalidation for queued candidates. A newer deployment that already includes an older request can satisfy that request without rolling the vault back.
- **Keep ownership boundaries explicit.** Two different vaults or hosts are separate targets. A host-local lock is not a distributed lock.
- **Recover idempotently.** If copying succeeded but the controller crashed before recording success, inspect the actual hashes and stamp before deciding to retry.
- **Do not turn failure into an endless model loop.** Retry only transient conditions with bounded backoff. Route a persistent conflict to a durable recovery outcome; continue independent development work.
- **Preserve cross-plugin consistency.** Define compatibility groups and test the installed combination. The existing per-file copy mechanism is not an atomic group rollout, so do not claim it is.

The current post-sync smoke recipe expects the repository's plugin set. A selective promotion runner must either present the complete intended installation snapshot or extend that check with a well-defined expected set; merely deploying one plugin and ignoring all other drift is not sufficient.

This shift is more substantial than an instruction edit, but it directly prevents the ei pattern: ordinary workers stop leaving the live vault dependent on their uncommitted workspace lifetime.

### Exceptional previews and old orphaned deployments

Keep live deployment of uncommitted experimental work exceptional. Prefer a scratch vault. If a live preview remains necessary, retain its complete source snapshot and generated bundle durably before installing it, with an owner and explicit cleanup/promotion responsibility. A stamp containing hashes and a base HEAD cannot reconstruct dirty source fragments.

For existing orphaned builds:

1. Preserve the deployed bundle and stamp.
2. Seek recoverable source through the supported SASE repository/artifact interfaces.
3. Reconstruct, integrate, and verify when evidence supports preserving both changes.
4. Otherwise ask once whether to keep the deployed behavior or replace it with the specified verified candidate.

A recovery snapshot is valuable, but it is not consent to remove live behavior. Do not have an LLM declare semantic equivalence solely because plugin versions match or a broad test suite passed.

A more elaborate content-addressed preview registry can follow if preview use warrants it. It should not be a prerequisite for the first authorization cleanup or for clean post-landing deployment.

## Verification and rollout

These are proposed acceptance tests, not tests executed during this research:

| Scenario | Required result |
| --- | --- |
| Ordinary authorized plugin fix | No permission question; verified target bytes installed |
| Documentation-only change | No executable deployment triggered |
| Wrong source, new destination, unconfigured plugin | Clear scope error; no broadened authorization |
| Bare/dry-run command path | Runner uses no-pull, so inspected source does not change during deployment |
| Landed dirty bundle plus worker changes | Recover without force; preserve both changes |
| Unlanded protected bundle, inactive author | Preserve it; no timeout-based force |
| ei replay: author test fails before chained sync | Failed verification remains visible; no replacement based on author inactivity |
| Older candidate follows newer installed descendant | No rollback; either prove satisfaction or reconcile |
| Target changes after preview | Final write revalidates and refuses stale assumptions |
| Dirty vault-file skip with exit 0 | Runner treats rollout as incomplete |
| Copy succeeds, receipt write crashes | Retry proves current bytes and completes idempotently |
| Post-sync smoke fails | Deployment remains marked failed/recovery-needed |
| Mixed/plugin-group failure | Partial outcome preserved; never report the group complete |
| Source changes after verification | Candidate invalidated or reverified |
| Missing/unknown stamp or legacy Bob executable | Explicit compatibility handling; no fabricated protection |

Reuse and extend the existing CLI integration tests for cross-checkout refusal, exact inclusion proof, no-force recovery, runtime data preservation, and stamp storage. Test the runner and host integration separately, including actual provider instruction adherence. Most correctness should be established by deterministic fixtures; a small cross-provider behavioral evaluation checks whether models still ask gratuitous questions.

Measure permission-only questions separately from genuine conflict questions, time waiting for human attention, time awaiting deployment ownership, successful automatic recoveries, orphaned dirty deployments, and total time until a verified rollout. The success criterion is that ordinary work completes unattended and preserved-work conflicts become rarer—not merely that the notification count falls.

Roll out policy clarification first, then the runner and structured outcomes, then host-owned clean promotion. Preserve a switch to disable automatic promotion while keeping inspection and ordinary guarded sync available. Disabling the new automation must not disable the existing overwrite guard.

## Evidence and reproducibility

Repositories were opened through `sase repo open`. I inspected local source and tests at these revisions:

| Repository | Revision |
| --- | --- |
| bob-cli | 748342701f592c5c0f7005ed064f8ed83a762911 |
| bob-plugins | 17952459960b28f6c49638766803a08ff0ac586a |
| sase | e3f6d302db2918a07d4b6d68025fc3a66543a2d3 |
| chezmoi | 84ed1bba89d6e95dd752c7629af4d261b2e916ec |

The following links are revision-pinned references to files read locally, not web-fetched repository contents.

- **[E1]** Archived ei--6--6 transcript identified above; read through `sase chat show`. The list metadata identified provenance as local. Incident claims are attributed to that transcript.
- **[S1]** [bob-plugins AGENTS.md, lines 12–15](https://github.com/bobs-org/bob-plugins/blob/17952459960b28f6c49638766803a08ff0ac586a/AGENTS.md#L12): mandatory sync and conflict escalation.
- **[S2]** [bob-cli repository configuration](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/sase/sase.yml#L4): linked plugin deployment guidance.
- **[S3]** [bob-plugins deployment guide](https://github.com/bobs-org/bob-plugins/blob/17952459960b28f6c49638766803a08ff0ac586a/docs/develop/deployment.md#L40): recovery, force wording, and rollout gates.
- **[S4]** [plugins CLI](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/src/native/plugins/cli.rs#L403) and [Git refresh](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/src/native/plugins/git.rs#L28): pull behavior, arguments, JSON, and exit handling.
- **[S5]** [deployment provenance and guard](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/src/native/plugins/deploy.rs#L873): permission cases, exact bundles, dirty state, inclusion proof, and stamps; the same file contains the lock at line 233 and capture at line 648.
- **[S6]** [sync implementation](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/src/native/plugins/sync.rs#L32): configured IDs, backups, per-file writes, and incomplete outcomes.
- **[S7]** [plugin CLI integration tests](https://github.com/bobs-org/bob-cli/blob/748342701f592c5c0f7005ed064f8ed83a762911/tests/cli/plugins.rs#L2177): no-force landed recovery; related cases begin at lines 865, 906, 1440, 1585, 1685, and 1852.
- **[S8]** [Codex launcher](https://github.com/sase-org/sase/blob/e3f6d302db2918a07d4b6d68025fc3a66543a2d3/src/sase/llm_provider/codex.py#L286) and [Claude launcher](https://github.com/sase-org/sase/blob/e3f6d302db2918a07d4b6d68025fc3a66543a2d3/src/sase/llm_provider/claude.py#L473): existing approval-bypass arguments.
- **[S9]** [SASE finalizer and commit-hook configuration](https://github.com/sase-org/sase/blob/e3f6d302db2918a07d4b6d68025fc3a66543a2d3/docs/reference/config/finalizers.md): ordering, trusted configuration, after-hook execution and retry behavior.
- **[S10]** [SASE instruction inspection CLI](https://github.com/sase-org/sase/blob/e3f6d302db2918a07d4b6d68025fc3a66543a2d3/docs/reference/cli/instructions.md): render, archived bundle inspection, and observed load verification.

I inspected test definitions but did not run the code test suite, reproduce the historical deployment, or mutate the live vault. The installed Bob reports version 0.5.0; detailed behavior claims above are pinned to the inspected source, not an asserted build identity of that executable. Public documentation was consulted on the research date. No peer report or peer conversation was consulted.

## Recommended solution

**Adopt scoped standing authorization immediately, then make verified, durable, clean-source promotion a host-owned responsibility.** Keep Bob's overwrite guard and existing smoke checks. Give the runner explicit source/destination/plugin scope, structured refusal reasons, idempotent recovery, and clear deployment status.

Do not solve the ei case with a blanket permission exemption or automatic force. Its recorded question protected unlanded deployed work. Prevent that situation by changing when and how live builds are promoted; reserve human attention for the remaining cases where preserving or discarding behavior requires an actual decision.

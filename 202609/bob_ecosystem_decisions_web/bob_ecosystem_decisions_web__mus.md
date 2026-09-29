# Decisions Memory Web for bob-cli / bob-plugins / bob-mac-capture / Vault

Research report — researcher `mus`. Independent conclusions; peer reports (`__cdx`, `__cld`, `__grk`, `__gem`) not consulted.

## Summary

The plan is a good idea with two adjustments: (1) host the web in **bob-cli project memory** (not home memory), with explicit per-strand scope tags, because bob-cli is already the integration hub whose `AGENTS.md` names every other scope; (2) seed it with **only decisions already made and evidenced**, not aspirational ones — roughly 10 strands, each with a `Reopens when` clause so the web stays a record of commitments rather than a second docs tree.

## What the sase decisions web actually is

I read the sase project's implementation directly (external checkout via `sase repo open sase`, memory via `sase memory read decisions…`). The mechanics:

- **Descriptor**: `sase/memory/decisions.md` with `web: true` frontmatter (no `type:`/`parent:`), a one-line `description`, plus `roster: list`, `roster_label: DECISIONS`, `strand_noun: decision`. Its body is inlined into every agent's instructions; it defines what a record is (immutable once accepted; course changes write a *new* record and mark the old `superseded`, never edit in place) and carries an auto-generated numbered roster (`<!-- sase:strands -->`) of one-line strand summaries. At 24 strands the sase descriptor is ~100 lines — this is the token price paid on every turn.
- **Strands**: one file per decision (`sase/memory/decisions/<slug>.md`) with frontmatter `keyword`, `aliases`, `summary`, and `metadata` (`status: accepted`, `decided: <date>`, optional `superseded_by` + `[[…]]` back-link). Body shape is uniform across all 24 records: **Claim / Why / Cost / Reopens when**. The `Why` always names the *rejected alternatives* and the evidence that killed them (commit SHAs, measured host-capacity numbers, bead notes recording real failures). The `Cost` admits what the decision sacrifices. `Reopens when` is a falsifiable condition, not "revisit later".
- **Key supporting decisions**: `decisions/memory-webs` (why a flat descriptor + strand directory instead of one big note, a config store, or a DB: git-native diffing, per-strand identity, no inline-everything-or-nothing), `decisions/corpus-before-mechanism` (no retrieval machinery before a corpus needs it — directly relevant below), and partial supersession as a first-class state (`status: superseded-in-part` with per-clause retirement notes inline).

Takeaway: the value is not the file layout, it is the **discipline** — Claim/Why/Cost/Reopens, immutability, cited evidence, named rejected alternatives. A web that records decisions without those four properties is just docs with extra steps.

## Critique of the plan

**Is it a good idea? Yes.** This ecosystem has exactly the pathology the sase web was built for: load-bearing choices scattered across four scopes (CLI docs, two other repos' READMEs, vault convention, agent habit) that agents routinely re-derive, rationalize away, or violate. Concrete examples found during this research: "don't edit `~/bob/.obsidian/plugins/` directly" (overwritten by sync), "exactly one sync engine may run against `~/bob`" (git vs Obsidian Sync resurrection loop), "Obsidian Sync exclusions are device-local, not remote deletes" (easy to get wrong if Sync is relinked), "never `reset --hard` / force-push the vault". These are decisions with real failure modes behind them, currently documented as prose warnings that an agent must stumble onto. A keyword-addressed web (`sase memory read decisions:vault-sync`) fixes discoverability without inlining everything.

**Risks and objections, honestly weighed:**

1. **Token cost is real but bounded.** The descriptor inlines always; each strand summary adds ~2 lines. Ten strands ≈ 40–50 descriptor lines — comparable to the existing `sase.md` core note (81 lines). Acceptable. The mitigation is keeping the descriptor body to the definition paragraph plus roster, and resisting the urge to also inline "overview" prose.
2. **Duplication with `docs/`.** bob-cli already has excellent runbooks (`vault-git-sync.md`, `capture.md`, `plugins.md`, `task-status-hooks.md`). The web must not become a parallel docs tree. Rule: docs say *how*; strands say *what was decided, what was rejected, and what reopens it*. A strand should link to the runbook, not restate it.
3. **Four scopes, one web — where does it live?** See recommendation. The failure mode is strands that no agent ever reads because they live in a root the working agent doesn't load.
4. **Speculative strands.** The prompt asks to "think hard about which initial strands to add". The sase corpus rule (`corpus-before-mechanism`) argues for recording only decisions with evidence of having been made (a commit, an incident, a measured trade-off). I mark each candidate below as **accepted** (evidence exists) or **proposed** (needs the lead's confirmation), and the web should only ship the accepted ones.
5. **Maintenance.** Immutability means the web only grows. Without a `Reopens when` culture it becomes append-only folklore. The sase web's supersession marking (`status: superseded`, `superseded_by`, back-links) handles this — adopt it from day one.

## Recommended initial strands (all evidenced in-repo)

| # | Slug | Scope | Status | Claim (one line) |
|---|------|-------|--------|------------------|
| 1 | `bob-cli-owns-vault-mutation` | cli + mac | accepted | bob-cli is the only implementation of capture grammar, preview, completion, and vault writes; bob-mac-capture owns presentation/hotkey/packaging and delegates via versioned `bob` subprocess/JSON |
| 2 | `native-rust-by-default` | cli | accepted | Command implementations are native Rust; legacy shell binaries and embedded Pomodoro/notification scripts remain only as a targeted rollback path |
| 3 | `git-only-vault-sync` | vault | accepted | The vault syncs through git only; Obsidian Sync is off and exactly one sync engine may run against `~/bob` |
| 4 | `remote-wins-conflict-quarantine` | vault | accepted | Supported sync conflicts resolve remote-wins in place; the local version is quarantined under `_conflicts/` and recorded, never `reset --hard` / force-push / `-X ours/theirs` |
| 5 | `plugins-repo-is-source-of-truth` | plugins | accepted | `bob-plugins` is the source of truth; installed copies under `~/bob/.obsidian/plugins/` are overwritten on next `bob plugins sync` |
| 6 | `per-plugin-versioning` | plugins | accepted | Versions are tracked per plugin in each `manifest.json`; no lockstep releases |
| 7 | `ledger-is-status-source-of-truth` | vault/cli | accepted | The daily-note Pomodoro ledger is the source of truth; `task-status-hooks` derives Next/In Progress/Blocked markers from it (plus `capture =x` close deliberately leaves Blocked recovery and reference retirement to hooks) |
| 8 | `managed-log-children` | vault | accepted | Schedule changes go in managed `SCHEDULE LOG` children and work summaries in managed `WORK LOG` children; automation edits these, never free prose |
| 9 | `block-id-task-identity` | vault/cli | accepted | Trailing `^id` block IDs are stable task identity for `[[note#^id]]` task links, embeds, and dependency transclusions |
| 10 | `single-maintenance-lock` | cli | accepted | `vault-sync`, `nightly`, live `task-status-hooks`, and `randomize` serialize vault mutation through the shared `bob_sync.lock` |
| 11 | `capture-json-machine-contract` | cli + mac | proposed | `bob capture* --json` output is a versioned machine contract; mac-capture degrades gracefully (surfaces Bob's error / empty list) against older `bob` builds rather than assuming grammar support |
| 12 | `vault-size-guardrails` | vault | proposed | `vault-sync` refuses files ≥95 MiB and warns ≥50 MiB — small enough to fold into strand 3 or 4 rather than stand alone |

Strands 11–12 are marked proposed: 11 needs confirmation that the JSON-stability commitment is deliberate policy rather than current behavior, and 12 is arguably a sub-clause of the sync strands. Default to shipping 1–10.

Per-strand evidence available today: `docs/vault-git-sync.md` + `docs/obsidian-sync-exclusions.md` (3, 4), `docs/plugins.md` + bob-plugins `README.md`/`AGENTS.md` (5, 6), `docs/task-status-hooks.md` + `README.md` terms table (7, 8, 9), `README.md` compatibility-shims section + `src/` layout (2), bob-mac-capture `README.md` requirements block (1, 11), `docs/capture.md` (1, 11).

## Adjustments to the requirements

1. **Location: `sase/memory/decisions/` in bob-cli project memory, not home memory.** bob-cli's `AGENTS.md` already names all three other scopes, and the agents that most need these records work here. Add a `scope:` key to each strand's `metadata` (`cli`, `plugins`, `mac-capture`, `vault`) so a future split is mechanical. Promote to `~/sase/memory/` only if/when agents working *in* the plugins/mac-capture checkouts demonstrably need strands they can't see — that promotion is itself a future decision record.
2. **Copy the sase strand schema exactly** (frontmatter `keyword`/`aliases`/`summary`/`metadata.status`+`decided`, body Claim/Why/Cost/Reopens when) rather than inventing a variant. Cross-repo familiarity is worth more than local optimization; agents already know this shape.
3. **Descriptor body stays minimal**: one paragraph defining record immutability + supersession marking, one line on how to read (`sase memory read decisions:<keyword> -r "<why>"`), then the generated roster. No overview prose — that is what `docs/` is for.
4. **Write `decided:` dates from git history** (e.g. the Obsidian-Sync retirement, the plugins-repo extraction) where recoverable; omit rather than guess.
5. **Require the `/sase_memory_write` skill flow** before creating any of this (project rule), and run `sase memory init --check` after, since the decisions web adds a descriptor kind plus an eleven-rule-style validator on the sase side — expect init/doctor to validate the new web.

## Recommended solution

1. Create `sase/memory/decisions.md` (web descriptor, `web: true`, description "Architectural and policy decision records…", `roster: list`) and `sase/memory/decisions/` with strands 1–10 above, each following the Claim/Why (with rejected alternatives + cited evidence)/Cost/Reopens-when shape and linking to the relevant runbook instead of restating it.
2. Keep strands 11–12 as lead-confirmed follow-ups, not seed content.
3. Run `sase memory init` (mandatory follow-through after a memory edit) and verify `sase memory read decisions:<keyword>` resolves for each strand.
4. Adopt the standing rule going forward: a strand is added when a decision is *made* (with its rejected alternatives and evidence), marked superseded — never edited — when reversed, and cross-scope strands carry explicit `scope:` metadata until a home-memory promotion is justified by use.

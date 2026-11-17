# Stop agents gating on `bob plugins sync`: safety analysis and recommendation

Researcher: mus · 2026-11-17 · question: SASE agents (e.g. `ei`) keep filing
confirmation gates before running `bob plugins sync`, costing hours of wait.
Goal: let them sync without asking, without making it unsafe.

## TL;DR

Yes, this is a good idea, with a scope correction: **pre-authorize plain
`bob plugins sync`, keep `--force` behind a real gate.** Plain sync is already
guarded by design (provenance stamps, overwrite refusals, backups, dry-run,
deploy lock); the dangerous operation was never plain sync, it is `-F`. The
fix is a two-tier policy written into always-loaded memory, not a code change.
Optionally back it with a project named tool so the sanction is auditable
instead of just prose. Do not pre-authorize dirty-tree syncs: that is the one
hole in the current guard, and closing it costs agents one commit, not one
gate.

## 1. What `bob plugins sync` actually does (safety inventory)

All claims below were read from the implementation in this checkout
(`src/native/plugins/`), not from docs prose.

**Blast radius is narrow by construction.**

- Deploys only the plugin ids listed in `plugins.sync` in bob's config; a
  missing list exits 2 with a ready-to-paste snippet, and `-p` refuses an id
  the list leaves out (`cli.rs` `run_sync`, `sync.rs`).
- Copies only managed files (`manifest.json`, `main.js`, `styles.css` when
  present) from `<repo>/plugins/<id>/` into
  `<bob-dir>/.obsidian/plugins/<id>/`. Runtime files such as `data.json` are
  never touched (`cli.rs` long help, `sync.rs` `sync_one_plugin`).
- Files already matching the repo are reported unchanged; every overwritten
  vault file is copied to a timestamped backup directory first, and files that
  would change print as unified diffs (`sync.rs` `apply_plugin`,
  `plan_one_file`).
- `--dry-run` previews without writing vault files, stamps, backups, or lock
  files — a zero-risk rehearsal that already exists (`cli.rs`, `sync.rs`).

**Cross-agent overwrite protection already exists (the stamp guard).**

- Each real deploy writes a `.bob-deploy.json` provenance stamp recording
  source checkout root, HEAD, dirty state, host, timestamp, agent
  (`SASE_AGENT_ID`), and managed-file hashes (`deploy.rs` `build_stamp`,
  `current_agent`).
- Sync refuses to overwrite another checkout's uncommitted or non-ancestor
  deploy without `--force`; a clean checkout may overwrite a dirty deploy from
  another checkout/host without `--force` only when one commit reachable from
  its HEAD holds the stamped bundle byte for byte, and the sync names that
  proving commit (`deploy.rs` `evaluate_guard`, `find_inclusion_proof`).
  Per-file matches from different commits never qualify.
- A vault file with uncommitted changes in the vault Git repo is left alone
  with a warning unless `--force` is given (`sync.rs` `plan_one_file` /
  `SkippedDirty` handling).
- Stamp-storage refusal is absolute: a tracked or unignored stamp blocks the
  deploy and `--force` does not bypass it (`deploy.rs`
  `check_stamp_storage`).
- Concurrent syncs to one vault serialize on a deploy lock; the second fails
  fast with "another bob plugins sync is already deploying" instead of
  interleaving (`deploy.rs` `acquire_deploy_lock`).

**Residual risks (what the guard does NOT cover).**

1. **Dirty-tree deploys are allowed for the same checkout.** Same-checkout
   dirty iteration is explicitly permitted while the stamp still matches the
   vault (`docs/develop/plugins/deployment.md`, `evaluate_guard`). So an
   agent with uncommitted WIP can deploy half-finished plugin JS straight
   into Bryan's live vault. This is the single biggest hole in a blanket
   "just run it" policy.
2. **Broken JS breaks Bryan's live Obsidian.** There is no automatic rollback;
   recovery is manual restore from the backup directory plus re-sync. The
   repo's rollout procedure (isolated Xvfb smoke check, `npm run build:check`,
   post-sync gate in `docs/develop/plugins/deployment.md`) exists precisely
   because a bad deploy lands in the editor Bryan is using.
3. **The default run mutates the checkout first.** Unless `--no-pull` is
   passed, sync refreshes the plugins repo with a non-interactive `git pull`
   before analysis (`cli.rs` `maybe_pull_repo`). An agent deploying "the
   checkout open for local development" that forgets `--repo "$PWD"
   --no-pull` can yank its own checkout mid-task.
4. **`-F` discards every protection above in one flag.** Force overwrites
   protected deploys and dirty vault files alike (`evaluate_guard` returns
   `Permit` immediately when `force` is set). This is the operation agents
   must never self-approve.

## 2. Why agents keep gating

Three causes compound; none is "the model is being silly":

1. **The write lands outside the workspace.** Sync writes into `~/bob`, the
   live vault — user data outside the agent's checkout. Every general agent
   safety instinct says "confirm before mutating the user's live files," and
   nothing in the agent's instructions countermands that instinct for this
   specific command.
2. **The repo's own wording teaches agents to ask.** The bob-plugins
   `AGENTS.md` refusal recipe ends with "Ask Bryan when the build is unlanded
   and abandoned. The question must name what `-F` would remove." Models
   generalize that ask-Bryan precedent from `-F` refusals to all syncs,
   especially since the `sase_gate` skill is presented as "the easy way to
   propose commands for confirmation."
3. **There is no standing-permission mechanism for custom gates.** I checked:
   `sase autonomy` profiles cover only host checkpoints of kind
   plan/epic/question (`sase autonomy show standard`); the matrix explicitly
   says "the agent's shell is not restricted." So a custom `sase_gate` confirm
   has no allowlist, no auto-approve rule, no scope it can be filed under that
   Bryan could pre-approve once. Each agent re-litigates the same decision
   from scratch, and each litigation parks work for hours.

Note the asymmetry: `sase/memory/sase.md` and bob-plugins `AGENTS.md` already
say agents MUST run `bob plugins sync` after changes, but MUST is not
pre-authorization — it orders the action without removing the perceived need
to confirm it. That contradiction is the stall.

## 3. Options considered

| Option | What changes | Stops stalls? | Safety | Cost |
|---|---|---|---|---|
| A. Standing pre-auth in core memory | two-tier rule in `sase/memory/sase.md` + bob-plugins `AGENTS.md`: plain sync pre-authorized, `-F` always gates | yes for the common case | good if scoped (see §5) | one memory edit |
| B. Project named tool (`sase tool run plugins-sync`) | sanctioned wrapper in `sase/sase.yml`, recorded in ToolRun ledger | signals blessing; weak alone | auditability only, same binary | small |
| C. Land-time auto-deploy (hook/stitch) | agents never sync; deploy runs once from clean checkout at land | yes, and kills dirty-deploy risk | best steady-state | new automation to build/debug |
| D. Clean-tree-only pre-auth | A scoped to clean trees + dry-run JSON + `build:check` | yes, minus one commit | closes hole #1 | policy wording |
| E. Structural: make `-F` un-runnable by agents | `-F` requires interactive/env confirmation flag | plain sync safe by construction | strongest per-flag | CLI change + release train |

A alone is the weakest enforcement (prose the model must obey, no audit
trail), but it is also the only option that works this week. C is the best
end state — deployment at land-time from a clean checkout eliminates both the
gate and the dirty-WIP hole — but it is a project, not a fix: the vault is
host-local, so the hook must run where the vault is, handle the smoke gate,
and report back. E is attractive (a `--force` that structurally needs a human
makes everything else pre-authorizable without judgment calls) but it rides
the bob-cli release train and needs a `!` breaking-change mark if it alters
the CLI contract.

## 4. Critique: is auto-allowing a good idea? Would I do something different?

Pre-authorizing **plain** sync: yes, good idea. The guard design shows the
authors already decided plain sync should usually-just-work: refusals are
specific, messaged, and remediable; backups and diffs make every copy
inspectable after the fact; the stamp attributes every deploy to a checkout,
host, and agent. Gating a command whose failure modes are all handled
in-band is pure latency — the gate buys no safety the guard does not already
provide, because the reviewer approv

ing the gate cannot know more than the
dry-run diff they would skim.

Pre-authorizing **`-F` or dirty-tree sync**: no. `-F` exists to destroy
someone else's deployed work or Bryan's uncommitted vault edits; that is
exactly the class of irreversible, other-principal-harming action
confirmation exists for. And dirty-tree sync puts unreviewed bytes in the
live editor. A blanket "agents may sync, no questions" policy that fails to
say this invites the one incident that gets the whole permission revoked.

What I would do differently from a naive "tell them to stop asking": not
rely on memory prose alone. Prose is obeyed probabilistically; the stall
recurs every time a model is uncertain. Pair the prose (A+D) with one
mechanism that does not depend on obedience: either the named tool (B), which
at least leaves a ledger entry reviewers can audit, or the land-time deploy
(C) as the follow-up. And measure: `sase tool runs` / gate history can show
whether sync-gates actually drop to zero after the memory edit; if they do
not, prose failed and C stops being optional.

## 5. Requirement adjustments (called out explicitly)

1. **Scope the pre-authorization to plain sync, never `-F`.** The request
   says "stop this safely" without distinguishing flags. The distinction is
   the safety: plain sync = pre-authorized, no gate, no question; any sync
   with `-F`/`--force` = durable `sase_gate` with mandatory evidence
   (refusal text, `git log HEAD..@{upstream}` output, deployed version and
   the features/APIs `-F` would drop — the existing recipe already demands
   this content).
2. **Add a clean-tree requirement.** Pre-authorized syncs must run from a
   clean plugins checkout (`git status --porcelain` empty) or with committed
   + pushed work. This closes residual risk #1 and costs one commit, not one
   gate. Same-checkout dirty iteration stays a human/dev-loop privilege.
3. **Require the rehearsal, keep the evidence.** Pre-authorized sync =
   `npm run build:check` green (fragment plugins) → `sync --dry-run -f json`
   → real sync → paste/attach the JSON result in the session report. The
   dry-run is ~free and converts "trust me" into checkable output.
4. **Pin the repo selection flags.** Agents deploying the checkout they
   edited must use `--repo "$PWD" --no-pull`; agents deploying latest landed
   work use the default pull path. The current default (pull, then deploy
   whatever that yields) is the surprise-mutation vector in risk #3.
5. **Do not pre-authorize the `-p` escape hatch around the allowlist.**
   `-p` still refuses ids outside `plugins.sync` (already enforced); restate
   it so nobody "fixes" a skip by editing config + syncing in one unreviewed
   motion. Config changes are reviewable; deploys are not.

## 6. Recommended solution

**Adopt A+D now (memory edit, this week), B as a cheap audit upgrade, C as
the stated end state, E if `-F` misuse is ever observed.**

Concrete steps:

1. Edit `sase/memory/sase.md` (core, always loaded — use the
   `/sase_memory_write` skill, since memory files are not ordinary files)
   with a two-tier standing order, roughly:
   - "Agents are pre-authorized to run plain `bob plugins sync` (no `-F`):
     never file a gate or question for it. Conditions: clean checkout,
     `build:check` green where applicable, `--dry-run -f json` first,
     `--repo "$PWD" --no-pull` when deploying the checkout under edit.
     Refusals are handled per the bob-plugins refusal recipe, which never
     involves `-F` without a gate."
   - "`bob plugins sync -F/--force` is never pre-authorized: it requires a
     durable `sase_gate` carrying the refusal text, the landed-vs-abandoned
     evidence, and what `-F` would remove (deployed version, features/APIs).
     Abandoned-build `-F` also needs Bryan's explicit approval — unchanged
     from today."
2. Mirror the one-line version in bob-plugins `AGENTS.md` next to the
   existing "you MUST run `bob plugins sync`" line, so the order and the
   permission sit together: "plain sync is pre-authorized; never gate on it."
3. (Optional, small) Add a `plugins-sync` named tool in `sase/sase.yml`
   wrapping the blessed invocation; agents run `sase tool run plugins-sync`
   and every deploy lands in the ToolRun ledger for audit.
4. (Follow-up bead) File the land-time deploy automation (C) as the
   end-state design: deploy from the landed clean commit, run the smoke gate,
   report the JSON. Close the loop by checking gate/tool history a month
   later: sync-gates at zero and no dirty deploys in stamps means the prose
   held.

**Success criteria:** zero `sase_gate`/`sase_questions` turns filed for plain
sync; zero `-F` runs without a settled gate (auditable via stamps' `agent`
field + ToolRun ledger); zero deploys from dirty checkouts in stamp history;
no increase in broken-vault incidents (backup-restore events as proxy).

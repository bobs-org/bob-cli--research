# bank.md should stop being an area note: research and recommended removal plan

- Date: 2026-11-26
- Swarm role: independent researcher `mus` (did not consult `__cdx` / `__cld` / `__grk` / `__gem` reports or transcripts)
- Question: Bryan canceled epic beads `bob-cli-pl` (area/project cards) and `bob-cli-q6` (bank property-card fold) because `~/bob/bank.md` should never have been an area note. It is a child of `~/bob/cash.md` but is only used for bank-row tracking and never contains tasks. He wants the two epics' work completed only after `bank.md` is no longer an area note and after the logic added to support that strange state — which he suspects produces two cards (one bank card + one area card) — is removed.
- Short answer: yes, do it. The suspicion is correct: today `bank.md` mounts **two** cards. The strange state is real, it is load-bearing in both repos, and removing it simplifies everything. Keep the "child of cash" idea, but redefine it as display affinity, not an area-graph edge. Introduce an explicit `type: "[[bank]]"` hub (or, as a minimal interim, an untyped `bank:`-mapping hub), delete the bank/area arbitration stack, and then re-do the canceled epics' remaining card work against a single bank-card owner.

## 1. What the current state actually is

### 1.1 The vault contract says bank.md is a sub-area today

`docs/bank.md` (bob-cli checkout) is explicit:

```markdown
The hub is a sub-area (`type: "[[area]]"`, `parent: "[[cash]]"`). It holds
the `bank:` configuration, later a queue card, and bank tasks such as
disputes.
```

with the canonical hub shape:

```markdown
---
parent: "[[cash]]"
type: "[[area]]"
bank:
  accounts: ...
  categories: ...
---
# 🏦 Bank
```

That wording lives in at least three places: the `## bank.md` section quoted above, the `## Files` table (`bank.md | Bank hub | Fixed vault-root stem. Frontmatter holds a bank: mapping`), and the `## Setup` / `bob bank config update` writer guarantees. The same shape is baked into every bob-cli test HUB constant, for example:

- `src/native/bank/import_run.rs:1263` (`const HUB: &str = "---\nparent: \"[[cash]]\"\ntype: \"[[area]]\"\nbank:\n...`)
- `src/native/bank/import_plan.rs:1597`, `src/native/bank/naming.rs:786,936`, `src/native/bank/config.rs:1436`, `src/native/bank/tests.rs:112,242,379,607,1202`, `src/native/bank/charts_tests.rs:18`
- The teaching-empty starter in `src/native/bank/output.rs:636` (`print_teaching_empty` prints `parent: "[[cash]]"` + `type: "[[area]]"`)
- `src/native/areas/sync.rs:509` (`write(vault, "bank.md", &area("cash"))`) and `src/native/areas/report.rs:550,615` (`write(root, "bank.md", &area("cash", ""))`), plus `src/native/areas/tests.rs:58` (`("bank", "cash")`)

So "bank.md is an area whose parent is cash" is not an accident in one fixture. It is the documented contract plus the test helper `area("cash")` used across `areas`, `bank`, and `bank/check` suites.

### 1.2 bob-cli already treats bank.md as *both* Bank and Area

This is the conceptual inconsistency Bryan noticed. Two classifiers disagree by design:

- `src/native/props/roles.rs:222` — `resolve_note_context()` returns `NoteKind::Bank` for `bank.md` **by path**, before even looking at frontmatter:

```rust
if relative_path.replace('\\', "/") == "bank.md" {
    return RoleContext { note_kind: NoteKind::Bank, ... };
}
```

`NoteKind::Bank` (`src/native/props/roles.rs:47`, wire name `"bank"`) owns only the `bank` key as `card("bank")` (`roles.rs:168-169`). Every other key falls through to the shared area-style contract: `src/native/props/contract/settings.rs:1` says `//! Stable setting order and key membership. Bank's non-bank keys use Area.` The contract tests assert exactly this hybrid: `src/native/props/contract/tests.rs:626` (`bank_show_uses_the_area_contract`) and `:409` (`home_and_bank_roles_match_the_editor_contract`) build `type: '[[area]]'` + `bank: {...}` fixtures and expect `note_kind == "bank"` with area settings (`summary`, etc.) plus a `bank`-owned `bank` key.

- `src/native/notebooks/snapshot.rs:379` (`classify_kind()`) and `src/native/pomodoro_homes/facts.rs:108` (`NoteFacts::parse()`) classify **by frontmatter type**: `frontmatter_is_area()` (`src/native/projects/scan.rs:359`, i.e. `type: [[area]]` and not an album) yields `LiteKind::Area` / `NoteKind::Area`. Since real `bank.md` carries `type: [[area]]`, the areas world sees it as a genuine area:
  - `src/native/areas/graph.rs:build_area_graph()` indexes every `LiteKind::Area` note (except the `area` root sentinel) and validates its `parent` edge (`area_parent_missing`, `area_parent_unresolved`, `area_parent_kind`, cycles, 16-hop limit). `bank.md` therefore participates in the area tree at depth 2 under `cash` (see `src/native/areas/report.rs:559-561`: stems `["body", "cash", "bank", "orphan"]`, `bank.depth == Some(2)`).
  - `src/native/areas/report.rs`, `src/native/pomodoro_homes/resolve.rs:514,543`, `src/native/stats/homes.rs:143`, `src/native/pomodoro_homes/clock.rs:210`, `src/native/pomodoro_themes/coverage.rs:87`, and `src/native/task_move/tests.rs` all treat `NoteKind::Area | NoteKind::Project` as homes: root-parent attribution, clock/offclock walks, theme/type inheritance, Ready snapshots, move targets.

Net: props says "bank.md is Bank (path wins), but its non-bank keys obey the area contract"; areas/pomodoro-homes say "bank.md is Area (type wins)". Both are right by their own classifier. That is the inconsistency to kill.

### 1.3 Yes — today bank.md gets two cards

Bryan's parenthetical is correct. Approved plan `sase/repos/plans/202611/area_project_cards.md` §8 (`Takeover and bank.md`) specifies the hybrid explicitly:

> **bank.md:** after a spike, the Area Card mounts in its title slot, adopts `# 🏦 Bank`, and owns the single foot row and the takeover. The bank card stays in the body with its banking content, `⊞ Edit`, and species badge, and suppresses its temporary `bank_foot` while the Area owner is active. If the Area mount fails, `bank_foot` comes back. `==` keeps opening the bank editor, and `=+` gains the area settings rows.

The implementation matches the plan. In the linked `bob-plugins` checkout:

- `plugins/bob-ledger-tools/src/249db-plugin-bank-area-arbitration.js` — pane-local `propertyCardHomeBankAreaOwners` weak-map keyed by `(scope, path="bank.md", kind="area", mount)`, with `bankSetupAreaArbitration(scope, path)` returning `{ owner, generation, suppressBankFoot }`. Bank refreshes can never infer ownership from a vault-wide flag; every decision binds to one scope/path/DOM mount/generation.
- `plugins/bob-ledger-tools/src/248c-plugin-bank-setup-hosts.js:572-574,783-785` — every bank paint reads the arbitration and threads `options.bankAreaGeneration` / `options.suppressBankFoot` into signatures and foot specs.
- `plugins/bob-ledger-tools/src/248ca-plugin-bank-setup-foot.js:138-169` (`bankSetupTrackFoot`, `bankSetupFootSignature`) — when the Area card owns the foot, a Bank repaint prunes only disconnected stale mounts and returns `null` instead of tracking a second foot; the signature includes the arbitration generation so Area/Bank generations never collide.
- `plugins/bob-ledger-tools/src/248cc-plugin-bank-setup-frontmatter-host.js` (`bankSetupAreaFrontmatterEligible`, `bankSetupOwnMountedFrontmatter[_Deferred]`) — a live Area mount owns whole frontmatter; a surviving Bank body must not conceal Area loss by claiming it, including across the deferred `requestAnimationFrame` re-check.
- `plugins/bob-ledger-tools/src/249b-plugin-home-card-model.js:68,83` (`homeCardEligible("bank.md", { type: "[[area]]" }).kind === "area"`) — the test at line 68 pins the current behavior: `bank.md` + area frontmatter *is* home-card eligible.
- `docs/area-and-project-cards.md:98-102` (`Data and display rules`) and `docs/property-editor.md:50,74,362` (+ vs `==` split: `+` shows area settings on `bank.md`, `==` keeps the bank editor), plus `docs/develop/architecture.md:228-239` (`bank ownership applies to bank.md`) and `docs/bob-ledger-tools.md:93` (bank card owns the note top, hides `# 🏦 Bank`, hides Properties only on source/cache + `props_v1` + editor-routing agreement).

So the stack to delete is well-bounded: the `249db` arbitration module, the `suppressBankFoot` / `bankAreaGeneration` threading in `248c` + `248ca`, the Area carve-outs in `248cc`, the "`+` means area settings on bank.md" branch in the property-editor entry points (`298z-plugin-property-editor-settings-entrypoints.js:217-218`, `249ca-plugin-home-card-property-editor-routing.js:13`), and the "bank.md hybrid / bank.md spike then mount" passages in the three docs above. The `bank_foot` temporary fallback goes away with it: with no Area owner, the bank card unconditionally owns its single foot.

### 1.4 What "area-ness" actually gives bank.md today (and whether anything needs it)

Enumerated from code, not from intuition:

1. **Areas tree membership.** `bank.md` appears in `bob areas list` / report, in the machine-owned nested `## Areas` catalog (`bob areas sync`), and as a `cash` child at depth 2. Nothing in the bank flow reads this; the bank scan (`src/native/bank/scan.rs:1`: `Discover bank.md and bank/YYYY-MM.md`) reads `bank.md` + `bank/*.md` only and never scans the whole vault. The `b` walk family (`src/native/walks/mod.rs:241-298`, `bank_family()`) reads the `bank:` mapping + month rows + journal, never the area graph. Removing area-ness deletes one row from the areas catalog. No bank command breaks.
2. **Home-ness for tasks.** `NoteKind::Area` makes `bank.md` a task residence, a Pomodoro home, a root parent, a Ready-lane note (`note_ready_cap_counts_the_lane`), a `]s` walk tier member (`review-walk-is-tiered`, `recurring-occurrences-walk-when-due`), an offclock/type-inheritance root (`off-clock-follows-tag-then-note-default`, `off-clock-note-defaults-filter-by-task-type`), a hue root (`theme-hue-is-config-pin-exempt-area-hash`), and a capture `@route` candidate (root-level areas are `@route` targets; `bank.md` is non-root so it is not a route today, but any `#task` line placed there would still be a resident task). Per `docs/bank.md:82-84`, bank rows never carry `#task` and stay invisible to `plan` / `ready` / `archive` / `reconcile` / freshness / status hooks. The only lint is `bank_row_task` (`src/native/bank/check.rs:507-512`: `#task` **on a row** is an error). A stray ordinary `#task` elsewhere in `bank.md` (e.g. a "dispute" task, which `docs/bank.md:89-90` still advertises: "bank tasks such as disputes") would today silently become a real GTD task. Bryan's "it never contains tasks" is therefore a vault-discipline fact, not an enforced invariant. After removal it should become enforced (see §3.2).
3. **Parent edge `bank → cash`.** Consumed by (a) the Areas graph as a real edge, (b) the bank card kicker/hue (`[🏦] BANK · Cash`, parent hue — see `main.js:13937`, `docs/bob-ledger-tools.md:93`: "Uses parent hue"), and (c) the props `parent` setting row ("Lives under"). Only (a) needs area semantics. (b) and (c) can be satisfied by a display-only affinity without graph membership.
4. **`bank_month` parent.** `bank/YYYY-MM.md` carries `parent: "[[bank]]"` (`src/native/bank/month.rs:236`, `import_plan.rs:1621`). The bank scan does not validate the parent's *kind*; it resolves the hub by fixed path `bank.md` and month notes by filename (`bank/YYYY-MM.md` authoritative, everything else in `bank/` ignored). No areas/projects graph edge is read for months. So demoting `bank.md` does not orphan month notes in any bank command. (Caveat: generic parent-chain validators for notebooks/albums — `bob notebooks check`, `bob albums check` — require chains reaching an area/project root. If anything ever parents a notebook/album at `[[bank]]`, that check would newly fail. Today the registry tests already treat `parent: "[[bank]]"` + `type: [[project]]` as a project fixture (`import_run.rs:2100`) and `parent: "[[bank]]"` + `type: [[bank_month]]` as a month; neither is a notebook/album. Recommend an explicit `bank check` finding if a notebook/album ever names `[[bank]]` as parent, rather than silently re-admitting bank into the home graph.)
5. **Projects parented at bank.** Test-only today (`report.rs:618`: `bank_pr.md` = project with `parent: "[[bank]]"`; `import_run.rs:2100`). Real-vault impact: none known. `resolve_project_parent()` (`src/native/project_dependencies/tree.rs:28`) resolves by path, not kind, so the edge still resolves; whether a project *may* parent at a non-area is a policy question — recommend refusing it (a project under a non-home is almost certainly a mistake) with a clear `parent_kind`-style finding.
6. **Props `parent` setting on bank.md.** Today the editor's AREA SETTINGS group includes Lives-under/Hue/Default-type/Clock/Ready-cap/Review/Capture-names on bank notes (`docs/property-editor.md`, `contract/settings.rs`). After removal, all but `parent`-as-affinity and `summary` are meaningless on a taskless hub. The `+` entry point on `bank.md` (area settings) should go away; `==` (bank editor) stays the only editor.

## 2. Critique of the requested plan

**The core call is right.** An area note is defined (see `glossary:area-note`) as an ongoing sphere of responsibility with `## Tasks`, Ready-cap + status grouping, walk membership, and clock/type inheritance — precisely the machinery `bank.md` never uses. Keeping it an area buys one thing (a free slot in the areas tree) at the cost of: a second card, a pane-local arbitration protocol, a hybrid props contract ("Bank's non-bank keys use Area"), a split editor (`+` vs `==`), split ownership docs, and a standing invitation for stray tasks to enter GTD through the back door. The canceled epics rubbed against this on every phase (`pl.9` arbitration fixes `06c87a06, 8e401c6e, b185579f, 5add8f5a, a0ebe43e`; the `pl` land note records an undeployed `bob-ledger-tools 1.166.4` drift against them). Deleting the strange state before re-doing the card work is the correct order.

**Three adjustments are justified** (all called out explicitly so the follow-up epic can adopt or reject them):

1. **Do not keep `type: "[[area]]"` with "but no tasks" as a policy.** A type-level lie with a behavioral promise ("we just won't put tasks there") is what created the arbitration. Either the type changes or nothing really changed. Recommendation: the hub becomes `type: "[[bank]]"` (new, explicit), not merely untyped. Rationale: `props/roles.rs` already has `NoteKind::Bank`; giving the vault an explicit `[[bank]]` type lets every classifier key off frontmatter instead of the current path-magic (`relative_path == "bank.md"`), kills the `frontmatter_is_area → LiteKind::Area` misclassification at its root, and reads honestly in YAML. The cheaper interim — drop `type` entirely and keep `bank:` + path detection — works (classify → `Untyped`/`Other`, areas graph skips it automatically) but preserves path-magic and invites some future "untyped note" lint to flag the hub. If the team wants the smallest possible diff, ship the interim first with the path-based guard retained, then promote to `[[bank]]` once fixtures are clean. Do not ship "still `[[area]]` but documented as taskless."
2. **Redefine "child of cash.md".** Today that phrase means an area-graph edge (`bank → cash`, depth 2, inherits hue/clock/type, appears in `cash`'s `## Areas` catalog). After the fix it must mean *display affinity only*: the bank card kicker reads `BANK · Cash` and the parent hue comes from `cash`, but `bank.md` is absent from `bob areas list`, `bob areas sync` output, Ready/walk/clock/type inheritance, and capture routing. Concretely: keep `parent: "[[cash]]"` in the hub frontmatter (one line, zero new machinery) but document and enforce that for `NoteKind::Bank` the `parent` key is affinity metadata, not a home edge — the areas graph, `resolve_project_parent` policy, and notebook/album chain validators must all ignore it. Alternative "delete `parent` and hardcode Cash in the plugin" is worse: it strands the `summary`/`parent` foot rows, breaks the existing `Lives under` affordance, and hides a real relationship (bank activity *is* cash-domain) for no gain. Keep the key, change its meaning, write the meaning down in `docs/bank.md` + `glossary:bank-card`.
3. **Enforce "never contains tasks", don't just assert it.** Today nothing stops `- [ ] #task Dispute charge` in `bank.md` from entering GTD (only `#task` *on a bank row* is `bank_row_task`). After demotion, add two cheap guards: (a) `bob bank check` error (not warning) on any `#task` checkbox anywhere in `bank.md` ("bank hub holds no tasks; file disputes as project tasks under cash or as bank-row notes"); (b) `bob-ledger-tools` / `task-status-cycler` bank guard already refuses task cycle gestures on month notes (`test-task-status-cycler-bank-guard.cjs:71-72` pins `bank.md` and `area/bank/2026-11.md` as non-tasks) — extend the same guard to the hub so Ctrl+Enter on a stray task line in `bank.md` teaches instead of converting. Without this, the first "quick dispute task" recreates the old semantics through the back door.

What I would **not** do:

- Do not keep the Area Card on `bank.md` "for settings" while the bank card does banking. That split is the current confusion with better paint. The bank card already has a Setup surface, a folded-by-default posture (q6), and a `props_contract_v1` report; area settings that are meaningless on a taskless hub (ready cap, review, capture names, default type, clock, stats root) should disappear from `bank.md`, not get their own card.
- Do not migrate `bank.md` out from under `cash` (no move to vault root conceptually, no rename, no `bank/` merge). Path stability matters: the bank scan, journal, `bob-bank` fences (`view: month`), and every fixture assume fixed `bank.md` + `bank/YYYY-MM.md`. The fix is one frontmatter line plus classifier updates, not a file move.
- Do not bundle the two canceled epics' full re-implementation into the cleanup epic. Ship cleanup first (hub demoted + arbitration deleted + guards + docs/memory), gate on `just check` + `npm test` + disposable-vault Obsidian acceptance, *then* re-land `pl` (minus its `takeover` bank.md hybrid and `bank_foot`) and `q6` (bank card as sole title-slot owner) as small follow-ups. The cleanup is already a cross-repo change; piling the card redesigns back on top recreates the blast radius that forced the cancellation.

## 3. Recommended solution

### 3.1 Target state (one paragraph)

`~/bob/bank.md` is a **bank hub**, not an area note. Its frontmatter is:

```markdown
---
parent: "[[cash]]"
type: "[[bank]]"
bank:
  ...
---
# 🏦 Bank
```

`parent` names its display affinity (kicker crumb, parent hue); it creates no area-graph edge and confers no clock/type/Ready/walk inheritance. `bank/` month notes are unchanged (`type: [[bank_month]]`, `parent: [[bank]]`). Exactly one card — the bank card — mounts on `bank.md`, owns the title slot and the single foot, hides native Properties behind the existing fail-open gate, and is the only editor (`==` / `⊞ Setup` / Command Mode). No Area Card, no `bank_foot` suppression protocol, no `+`-means-area-settings branch, no `bank.md` row in any areas surface.

### 3.2 bob-cli changes (single cleanup epic)

1. **New classifier.** Add `frontmatter_is_bank()` beside `frontmatter_is_area/project` in `src/native/projects/scan.rs` (match `[[bank]]`, case/quote-tolerant like its siblings, album-excluded). Thread it through:
   - `src/native/notebooks/snapshot.rs:classify_kind()` → new `LiteKind::Bank` (or map to `Other` if the team refuses a new variant — but prefer the explicit variant so `build_area_graph`'s skip reads as intent, not accident).
   - `src/native/areas/graph.rs:build_area_graph()` — skip `LiteKind::Bank` exactly like the `area`-root sentinel skip; add a test that `bank.md` with `type: [[bank]]` contributes no node, no edge, no `area_parent_*` finding even with `parent: [[cash]]`.
   - `src/native/pomodoro_homes/facts.rs:NoteFacts::parse()` — `[[bank]]` maps to `NoteKind::Other` in the homes enum (which has no Bank variant and needs none), so clock/root/theme/Ready walks pass through it. Alternatively add a `Bank` arm that behaves as `Other` everywhere — but a comment must say so; silent fallthrough will be re-"fixed" by the next reader.
   - `src/native/props/roles.rs:resolve_note_context()` — prefer frontmatter `[[bank]]` over the current `relative_path == "bank.md"` check; keep the path check as a migration fallback that emits a `bank_type_legacy`-style hint for exactly one release, then remove it.
   - `homeCardPathExcluded`-equivalent in bob-cli (`noteReadyPathExcluded`, `isDoneArchivePath` consumers): ensure `bank.md` never becomes a home/ready/route candidate by kind *or* path during migration.
2. **Hub template + starter.** Update every `type: "[[area]]"` + `bank:` hub constant to `type: "[[bank]]"` (the `rg` list in §1.1: `import_run.rs`, `import_plan.rs`, `naming.rs`, `config.rs`, `tests.rs`, `charts_tests.rs`, `output.rs:print_teaching_empty`, `areas/sync.rs`, `areas/report.rs` helpers). Add a migration affordance, not a migration command: `bob bank check` reports `bank_hub_type_legacy` (warning, one release) when the hub still says `[[area]]`, with the exact replacement line; `bob bank ensure`/`import` refuse to *create* new `[[area]]` hubs immediately. No bulk vault rewrite; the real `~/bob/bank.md` is a one-line hand edit (see §3.4).
3. **Guards.** `src/native/bank/check.rs`: (a) keep `bank_row_task` (error on `#task` in a row); (b) add hub-level `bank_hub_task` error on any `#task` checkbox anywhere in `bank.md`; (c) add `bank_parent_affinity` info noting `parent: [[cash]]` is display-only. Update `docs/bank.md` hub section: replace "The hub is a sub-area" with the affinity definition, delete "bank tasks such as disputes" or redirect disputes to ordinary project tasks, and document that `bank/` months are unaffected.
4. **Projects/notebooks/albums policy.** `resolve_project_parent` + `notebook_parent_kind` + album parent validation: a parent resolving to `NoteKind::Bank`/`LiteKind::Bank` is not a home. Refuse new projects/notebooks/albums parented at `[[bank]]` with a named finding; grandfather existing `bank_month` (`parent: [[bank]]`) explicitly in the finding's allowlist text so the next reader doesn't "fix" months.
5. **Tests.** Update `areas/tests.rs` (`("bank","cash")` expectation goes away; add `bank.md`-as-`[[bank]]` absent-from-graph test), `areas/report.rs` tests (drop the `bank.md → area("cash")` writes or convert them to `[[bank]]` fixtures asserting absence), `props/roles.rs:772`, `props/contract/tests.rs:409,626` (rebuild fixtures as `type: [[bank]]`), bank suite HUB constants, and any `capture_dependency_tasks` catalog test that enumerates task-bearing kinds (`catalog_covers_every_task_bearing_note_kind`, `sync.rs:219 note_kind`). Run `just check` (the repo's configured gate) before reporting done.

### 3.3 bob-plugins changes (same epic, second half)

Delete, don't branch:

1. Delete `249db-plugin-bank-area-arbitration.js` and all `bankSetupAreaArbitration` / `suppressBankFoot` / `bankAreaGeneration` references (`248c-plugin-bank-setup-hosts.js`, `248ca-plugin-bank-setup-foot.js`, `248cc-plugin-bank-setup-frontmatter-host.js`, `374g-exports-home-card.js:49`). The bank host's `suppressBankFoot !== true` gate (`248c:507`) becomes unconditional foot ownership; `bankSetupFootSignature` drops the arbitration suffix.
2. `249b-plugin-home-card-model.js`: `homeCardEligible("bank.md", ...)` must return `null` for every frontmatter (add `bank.md` to the excluded set alongside `HOME_CARD_TYPE_NOTES`, or return early on `LiteKind::Bank`-equivalent frontmatter `[[bank]]` — do both during migration). Update the pinning test (`home-card-model.cjs:68`) to assert exclusion, not `area` kind.
3. Property editor: remove the "`+` on bank.md shows area settings" branch (`298z:217-218`, `249ca:13`, `docs/property-editor.md:50`); `+` on `bank.md` opens the bank Setup editor or Add mode like any other bank surface. Delete the AREA SETTINGS group on bank notes (`contract/settings.rs` already scopes by kind — verify the plugin mirrors it) and the `Lives under / Hue / Default type / Clock / Ready cap / Review / Capture names` rows for `NoteKind::Bank`, keeping `parent` (affinity) + `summary` as loose/display rows.
4. Bank card becomes the sole title-slot owner (this is q6's end state minus the Area roommate): kicker `BANK · Cash` from the affinity parent, title from H1/alias/stem per the shared kit, Setup folds by default, `_` toggles, `==` edits, fail-open restores native Properties. No `bank_foot` vs Area-foot distinction survives.
5. Docs: `docs/area-and-project-cards.md` (delete the bank.md hybrid §8/`takeover` bank steps; restore `bank.md` to the excluded list with a one-line reason), `docs/develop/architecture.md` (delete the bank-arbitration species note; bank ownership now unconditional like album/record), `docs/develop/validation.md` (same), `docs/bob-ledger-tools.md:93` + `docs/property-editor.md` (single-owner wording). Screenshots: one light/dark × narrow/wide pass of the now-single card (q6's screenshot phase covers the fold cosmetics; the cleanup only needs the ownership proof).
6. Tests: convert `test-ledger-tools-home-card-*.cjs`, `test-ledger-tools-bank-setup*.cjs`, `test-ledger-tools-property-card-host/foot/identity/fold/ownership/capability-routing.cjs`, `obsidian-card-foot-e2e.cjs:495,808-929`, and `obsidian-bank-ui-e2e-setup.cjs` bank.md fixtures to the `[[bank]]` hub; assert exactly one card mount and one foot on `bank.md` in both Reading and Live Preview. `npm test` + `bob plugins sync` per that repo's `AGENTS.md`; never hand-edit `main.js`.

### 3.4 Vault + rollout (kept deliberately tiny)

1. One-line real-vault edit: in `~/bob/bank.md`, `type: "[[area]]"` → `type: "[[bank]]"`. Leave `parent: "[[cash]]"`, the `bank:` mapping, and `# 🏦 Bank` untouched. No month-note edits, no renames, no catalog moves. (`bob areas sync` / `notebooks sync` output will drop the `bank` row from the `cash` `## Areas` catalog on its next run — that deletion is the fix, not collateral.)
2. Order: land bob-cli cleanup → `bob plugins sync` from clean master (the `pl` land note's `bob-ledger-tools 1.166.4` drift warning applies here too: sync `-p bob-ledger-tools` from clean master, never `-F`) → disposable-vault Obsidian acceptance (`obsidian-frontmatter-takeover-e2e`, `obsidian-bank-ui-e2e`, `obsidian-card-foot-e2e`, `obsidian-property-editor-e2e`) → hand edit on the real vault → re-run `bob bank check`, `bob areas list`, `bob props show bank.md`.
3. Memory (only as the governing decisions allow; the canceled epics' reviewer decisions authorized `glossary:property-card`, `glossary:bank-card`, `glossary:area-card`, `glossary:project-card` edits and nothing else — a new epic needs its own `memory_*` decisions): update `glossary:bank-card` (hub is `type: [[bank]]`, sole card, `parent` is affinity), `glossary:property-card` (species list: bank card no longer shares its note with an area card), and the `area-note` strand if it names `bank.md` as an example. Do not invent a `decisions:` record; if course changes, the decisions web requires a new record superseding the old, never an in-place edit.

### 3.5 What happens to the two canceled epics

- `bob-cli-pl` re-scope: keep phases `one-writer` through `editor-*` unchanged; delete the `takeover` phase's bank.md hybrid steps (spike/mount/fallback chain, `bank_foot`, `=+`-gains-area-rows) and replace with "verify bank.md excluded from home cards and from `+`-means-settings". The `memory_property_card` strand rewrite drops its "bank excluded … now owned through its Area Card" clause.
- `bob-cli-q6` re-scope: unchanged except its premise simplifies — the bank card was already designed as the title-slot owner; remove every "while the Area owner is active / restore `bank_foot` otherwise" conditional. Phases `bank-takeover` (Properties hiding) and `_`-key reach keep their gates; the YAML-parity spike stays (it never depended on area-ness).

## 4. Evidence and provenance

- Canceled beads read via `sase bead read bob-cli-pl / bob-cli-q6 -r ...`: both `CLOSED`, `Resolution: canceled`, close reason "The ~/bob/bank.md file should never have been an area note … will launch a new [epic] to finish this work (which fixes the bank.md inconsistency)", each with 6–9 `CLOSED` phase children; `pl` links plan `202611/area_project_cards.md`, `q6` links `202611/bank_property_card_fold.md`.
- Plans: `area_project_cards.md:9,36,58,129,384,398,412,472,551,574,597-602,703,738,776,817,955-1049` (hybrid + takeover + memory decisions); `bank_property_card_fold.md:5,68-72,109,124,141,175,234-238,511,517,548,602,605,662,707,732` (title-slot, Setup fold, `_`, Properties gate, no CLI/vault changes).
- Code: bob-cli paths above (`props/roles.rs`, `props/contract/*`, `notebooks/snapshot.rs`, `projects/scan.rs`, `areas/graph.rs`, `pomodoro_homes/*`, `bank/*`, `walks/mod.rs`, `stats/homes.rs`); bob-plugins paths above (`249db`, `248c`, `248ca`, `248cc`, `249b`, `249ca`, `298z`, `374g`, `240c` host, `240f` species, `248cb` title).
- Docs: `docs/bank.md:82-90,268-275`, `docs/area-and-project-cards.md:98-102`, `docs/property-editor.md:40-120,350-400`, `docs/develop/architecture.md:228-239`, `docs/bob-ledger-tools.md:22,93`.
- Memory consulted via `sase memory read`: `roster:decisions` (79 records; governing reads for this domain include `decisions:off-clock-follows-tag-then-note-default`, `decisions:off-clock-note-defaults-filter-by-task-type`, `decisions:theme-hue-is-config-pin-exempt-area-hash`, `decisions:note-ready-cap-counts-the-lane`, `decisions:review-walk-is-tiered`, `decisions:ready-is-freshness-gated`, `decisions:recurring-occurrences-walk-when-due`, `decisions:task-lanes-are-sticky`, plus `decisions:bob-cli-releases-ride-a-daily-train` as the release-train gotcha); strands `glossary:property-card`, `glossary:bank-card`, `glossary:area-note`, `glossary:bank-row`, `glossary:bank-month-note`; reference notes `cli_rules.md`, `docs.md`.
- Not consulted (per swarm instructions): any `*__cdx.md` / `*__cld.md` / `*__grk.md` / `*__gem.md` peer report, transcript, or summary. Shared sources (vault docs, plans, both checkouts, memory) were used independently.

## 5. Risks and open questions for the follow-up epic

1. **Hue without a home.** The bank card "uses parent hue" today via the area parent. After demotion, define the fallback chain explicitly (own `color` → affinity `cash` hue → muted default?) so a missing/renamed `cash` note degrades to a named grey instead of a broken crumb. One test with `parent: [[missing]]` should pin it.
2. **The `subscriptions.md` / billing album.** `bank/subscriptions/registry.rs:1300` builds a `type: [[album]]` fixture with `parent: "[[area]]"`; confirm no subscription surface parents at `[[bank]]` in a way the new policy would refuse, and add the negative test if one does.
3. **Stray `parent: [[bank]]` projects in the wild.** `rg` shows test-only fixtures today, but the real vault was not scanned in this research pass. The cleanup epic's first step should `rg -l 'parent:.*\[\[bank\]\]' ~/bob` (read-only) and either grandfather or re-parent whatever it finds before flipping the kind check from warning to error.
4. **Release-train discipline.** Per `gotchas` / `decisions:bob-cli-releases-ride-a-daily-train`, no `Cargo.toml` version or `CHANGELOG.md` edits by agents; CLI/JSON contract breaks (the new `[[bank]]` type, the new `bank_hub_task` finding, any `props show` contract-shape change) get marked `!` and ride the scheduled train — at most one version per New York day after full CI on the exact SHA.

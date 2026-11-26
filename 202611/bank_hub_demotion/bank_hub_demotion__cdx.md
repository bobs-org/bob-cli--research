# Bank should be a bank hub, not an area

Independent research by **cdx**, 2026-11-26. Scope: decide how to replace the canceled `bob-cli-pl` and `bob-cli-q6` requirements, not implement or deploy their replacement.

**Recommendation:** keep `bank.md` at its current path, keep `parent: "[[cash]]"`, remove its area type, and give the Bank Card sole responsibility for its note-top title, foot, and Properties takeover. Remove the area-settings contract and Bank/Area arbitration. Preserve the useful area/project cards and shared folding work already implemented. One necessary addition: move the **parent link** of the subscriptions album to Cash before removing Bank's area type.

## What the evidence establishes

I inspected bob-cli at `4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5` and the separately opened bob-plugins checkout at `a14ccc4658e4ae0f005efae8a6a9f78dfe6e35c0`. I read the two original plans through audited artifact reads, their epic/selected phase records through audited bead reads, and the decisions roster and relevant glossary/decision strands through audited memory reads. I queried the live local vault through `bob query` and ran controlled comparisons in disposable vaults using installed `bob 0.6.0`.

I did not consult any other report or researcher in this swarm. No production code, vault notes, bead state, or memory was changed. No financial records or amounts are needed in this report. Installed-binary experiments and source inspection are distinguished below; I did not build a fresh binary or run real Obsidian acceptance during this research.

### The live note is incorrectly classified for its actual use

A read-only Dataview query returned:

| Note | Type | Parent | Checkbox rows | `#task` rows |
| --- | --- | --- | ---: | ---: |
| `bank.md` | `[[area]]` | `[[cash]]` | 0 | 0 |
| `cash.md` | `[[area]]` | `[[area]]` | 22 | 22 |

A second query, `WHERE parent = [[bank]]`, found two immediate children: `bank/2026-11.md`, typed `[[bank_month]]`, and `subscriptions.md`, typed `[[album]]`. These observations describe the local vault at research time; repeat them before migration. The query engine printed unrelated ambiguous-link warnings, so this is not a claim that the whole vault is clean.

The Area Note glossary defines an ongoing sphere of responsibility and task residence. Being a child of Cash does not require Bank to be another area. Conversely, having no tasks today would not by itself disqualify a real area: the decisive fact is Bryan's explicit intent that this note is a dedicated bank-tracking surface and never a task home. Cash remains the appropriate home for banking chores and disputes; finite banking projects can be ordinary projects beneath Cash.

The existing bank documentation says the hub is a sub-area and can hold dispute tasks. That is a concrete requirement to replace, not merely a display defect. [S3]

### Yes, the old area-card design deliberately allowed two card surfaces

`plan:202611/area_project_cards.md`, especially its takeover phase, assigns the Area Card the title, foot, and whole-frontmatter ownership, while the Bank Card remains in the body. It suppresses the bank foot while an Area owner is active, with fallback branches if the mounts conflict. The later `plan:202611/bank_property_card_fold.md` instead makes Bank a title-slot property card while retaining AREA SETTINGS for `+`; its final phase adds an authored area-policy strip and an over-cap READY readout to Bank. [S1, S2]

Current plugin source contains the resulting coexistence mechanism:

- `homeCardEligible("bank.md", { type: "[[area]]" })` admits an Area Card; a unit test explicitly expects this.
- `249db-plugin-bank-area-arbitration.js` stores a pane-local Area owner, mount identity, generation, and foot readiness.
- The bank host relinquishes its title/frontmatter claim to an Area mount and suppresses its foot when the Area foot is ready.
- Special editor routing preserves Rust's wire kind `bank` while sending the UI to area settings. [S4, S5]

Thus “two cards” is a fair description of the designed hybrid, although it should not mean two simultaneous title owners or two Properties feet. I cannot claim what is visibly mounted on the user's current device: source, deployment, and cached state can differ. The epic records explicitly report deployed-build drift and incomplete real-app acceptance. The important conclusion is that substantial code exists to reconcile two semantic identities for this one note.

### Removing `type: [[area]]` alone is insufficient

The bank subsystem already has an independent identity. `scan_bank` discovers the exact root `bank.md` and month files under `bank/`; it does not require the hub's area type. `resolve_note_context` returns `NoteKind::Bank` for canonical `bank.md` before consulting type metadata. The month-note template independently writes `parent: "[[bank]]"` and `type: "[[bank_month]]"`. [S6]

But `props/contract/settings.rs::for_kind` groups `NoteKind::Bank` with `NoteKind::Area`. This makes Bank expose Summary, Lives under, Hue, Default type, Clock, Ready cap, Review, and Capture names even without an area type. `docs/props.md` explicitly documents the hybrid. [S7]

I reproduced this with a minimal Cash/Bank vault, changing only Bank's type line:

| Observation | Bank typed as area | Bank with no type |
| --- | --- | --- |
| `bob bank config -f json` | valid, no findings | valid, no findings |
| `bob props show bank.md -f json` | `note_kind: bank` | `note_kind: bank` |
| Props settings | all eight area settings | the same eight settings |
| Props capabilities | `props_v1`, `props_contract_v1` | the same capabilities |
| `bob areas list` membership | Cash and Bank | Cash only |
| `bob capture-targets` | `@bank` offered as an area | `@bank` absent |

All these commands exited 0. The fixtures deliberately lacked generated catalogs, so their unrelated missing-catalog findings are not a full validation result. The experiment establishes the classification and settings difference, not universal compatibility.

This is the strongest reason to change the contract as well as the note. Keeping typed task policies on a note that cannot hold tasks is misleading even when only one card happens to render.

### Subscriptions are the migration trap

The live subscriptions album currently hangs under Bank. `albums/registry.rs::analyze_direct_parent` accepts only Area or Project as an album's direct parent; the navigation parent picker enforces the same rule. The album catalog also constructs owners from Area/Project notes. [S8]

A second disposable-vault experiment produced:

| Bank type | Subscriptions parent | Album result |
| --- | --- | --- |
| Area | Bank | valid parent; only expected missing-index warning |
| No type | Bank | `album_parent_kind` and `album_index_damaged` errors |
| No type | Cash | valid parent; only expected missing-index warning |

**`bob albums list` still exited 0 when those errors were present.** Migration acceptance must inspect structured issues, not rely on that exit status.

Subscriptions are discovered by their `subscription` noun through the record registry, not by being a child of Bank. This supports reparenting the existing album to Cash while retaining its filename, record folder, schema, record identities, and bank integration. However, the experiment used a minimal album schema, not the production subscription schema or import history; full subscription matching/coverage regression tests remain necessary. The import loader intentionally reports invalid subscription declarations and can proceed without subscription facts, so a broken parent must not be dismissed because bank import itself still runs. [S9]

## Assessment of the proposed direction

This is a good correction. The distinction should be **task home versus domain hub**, with property cards as views of their respective kinds. A Property Card need not be an Area Card, and a note's place in navigation need not imply task residence.

The gain is not just a cleaner screen. It removes a competing owner, a special settings model, extra mount generations, suppression/restoration coordination, and a misleading capture target. That directly reduces the state combinations that the property-card work must validate.

I would change three aspects of the request's framing:

1. **Do not interpret “bank row tracking only” as literal rows must live in `bank.md`.** The established hub/configuration plus monthly row files is already a useful split. Preserve configuration, setup, queue, reports, navigation, and the existing row storage.
2. **Do not interpret “remove support for the strange state” as revert everything touching Bank.** Keep the Bank Card itself, its native-Properties fallback, its guarded configuration writer, its bank-key ownership, and its normal title/foot lifecycle. Keep general shared mount-safety fixes that also protect other species.
3. **Do not equate canceled with unimplemented.** The current tree includes substantial work from both epics. A selected phase record, `bob-cli-q6.4`, says its implementation and glossary corrections had landed while real acceptance remained NO-GO and overlapped a child epic. Cancellation is a scope reset, not a rollback or proof of completion. [S2]

### Alternatives

| Approach | Benefit | Cost / conclusion |
| --- | --- | --- |
| Remove the type only | Smallest vault edit | Leaves eight area settings and arbitration code; breaks the subscriptions parent. Insufficient. |
| Keep Bank as an area but hide its Area Card | Avoids the album migration | Preserves the wrong task-home semantics, capture target, and policies. Reject. |
| Keep one Bank Card with an area-policy strip | One visible panel | Still presents irrelevant task policies and READY state. Reject for the stated usage. |
| Introduce `[[bank_hub]]` as a new type | Explicit taxonomy | Adds a type note and classifier/documentation work without removing canonical-path identity. Unnecessary now. Never use `type: "[[bank]]"` merely for symmetry: it points at the hub itself. |
| Allow albums under arbitrary ordinary notes | Keeps subscriptions under Bank | Broadens the album model, picker, validation, ancestry, and catalog ownership for one exception. Consider separately only if organizational needs justify it. |
| Untyped canonical Bank hub; subscriptions under Cash | Fits current bank detection and existing album rules | Requires a small coordinated migration and deliberate navigation link. Recommended. |

Removing an area type also removes Bank from generated Areas catalogs and normal area capture completion. Those are desired consequences, but preserve discoverability with an ordinary Bank link from Cash and an ordinary Subscriptions link on Bank. Do not keep a false area registration solely to retain those navigation rows.

## Proposed requirements, with adjustments called out

### 1. Dedicated bank identity

Keep canonical `bank.md`, `parent: "[[cash]]"`, `created`, useful `summary`, the `bank:` mapping, prose, and queue fence. Remove `type: "[[area]]"`; require no replacement type. Keep the month-note parent links to Bank and their existing `[[bank_month]]` type.

Bank is never offered as a task home by ordinary capture flows and has no area READY count or task-policy surface. Do not select card species by counting tasks: that would make a note's identity change as its contents change. If stray tasks are found during migration, move them explicitly to Cash or an appropriate project; do not delete them or silently convert banking checkboxes to tasks.

**Adjustment A — additional vault edit:** change `subscriptions.md`'s parent to Cash. Preserve record children under their album. Add a normal link from Bank to the album if necessary. Do not broaden album-parent rules for this migration.

### 2. One owner for the bank hub's note-top card

The Bank Card owns the title slot, title suppression, one Properties foot, and eligible whole-frontmatter replacement. Its normal bank report and source/cache evidence determine whether it can own the surface. The explicit `bob-bank` queue/month/subscription views remain independent content views; “one card” here means one note-top identity/ownership surface, not a ban on report fences.

Remove `propertyCardHomeBankArea*`, `bankSetupAreaArbitration`, foot suppression/generation wiring, Area release/reacquire branches, Bank-specific additions to the home-card foot, and the proposed area-policy strip. Remove the old hybrid test expectations and replace them with dedicated-bank cases.

For card admission, make canonical bank identity exclude Area/Project admission, matching the existing Rust bank-first classifier. A small identity/exclusion rule prevents a stale or accidentally restored area type from mounting a second owner; it should not carry an Area fallback or alternate editor. This is ordinary species exclusivity, not a retained hybrid compatibility subsystem. A broad rewrite of every vault classifier is unnecessary for the corrected data.

### 3. Stop exposing the area contract on Bank

**Adjustment B — backend scope is required:** remove `NoteKind::Bank` from the area/project settings table. Bank `props show` should retain `note_kind: bank` and `props_v1`, preserve ownership of the nested `bank` property, and omit the area settings contract. Old `setting.*` calls for area policies on Bank should refuse instead of silently writing ineffective settings. Existing generic property editing can handle ordinary metadata; it should not invent inherited task-policy rows.

In the plugin, remove Bank from area-settings labels, default focus, contract-refresh expectations, and the “Update bob for typed settings” hint. `+` opens the ordinary Property Editor on Bank. It must not render AREA SETTINGS from an old cached/reporting backend merely because the report's kind is `bank`.

Keep `==` and Setup routed to the bank configuration editor. Keep `-` for the full Properties drawer and `_` for Setup. Preserve the guarded nested bank writer and the generic writer's refusal to treat `bank:` as a loose editable map. Parent, summary, and optional presentation color do not justify importing Ready cap, default task type, clock, review interval, or capture aliases.

`240q-plugin-property-card-frontmatter-ownership.js::propertyCardFrontmatterContractReady` currently includes canonical Bank in the additional `props_contract_v1` gate. Remove that extra requirement for Bank together with removal of its area settings, while preserving generic `props_v1`, source/cache parity, live mount/path checks, editor routing, and the Bank editor's own readiness requirements. Area/Project must continue to require their real settings contract. [S10]

This changes documented CLI/JSON behavior. Follow `decisions:bob-cli-releases-ride-a-daily-train`: mark the breaking change with `!`, coordinate plugin compatibility, and do not hand-edit package versions or CHANGELOG in bob-cli. Do not solve compatibility by retaining fake area settings indefinitely.

### 4. Preserve the worthwhile parts of both epics

Retain and finish ordinary Area/Project cards, their setting stages, inheritance readouts, validation, parent consequence previews, catalog refreshes, lifecycle display, and guarded Properties takeover. Preserve the retirement of competing project frontmatter writers and count-key writers. Those changes have their own correctness value.

Retain shared `_` folding, compact record/area/project controls, folded healthy Bank Setup, visible problem summaries, title-slot Bank presentation, accessibility fixes, responsive layout, and passive rendering. Drop only the bank-area strip from `q6.6`; retain its screenshot review and zero-write/zero-paint-spawn acceptance.

The existing decisions support this boundary: `decisions:note-ready-cap-counts-the-lane` applies the cap to area/project task residence; `decisions:off-clock-note-defaults-filter-by-task-type` explicitly ignores policy declarations on non-area/project notes. Parent navigation and hue should continue to resolve through Cash, with regression coverage for bank/month/fence views. Do not add a new Bank hue algorithm or alter task accounting.

## A practical replacement sequence

This is implementation guidance for a new scoped replacement, not a request to reopen either canceled epic with its old requirements.

1. **Inventory the actual starting state.** Record primary/plugin/deployed versions and which acceptance evidence is still outstanding. Treat done resolutions, canceled resolutions, landed code, and deployed code separately. Recheck tasks, immediate children, other descendants, area-only fields, managed catalogs, and saved `@bank` references. Do not inspect other swarm reports as part of this independent report.
2. **Prepare and verify the contract and plugin removal on disposable vaults.** Use the corrected untyped Bank fixture and a legacy-type fixture. Make the plugin tolerate a backend that still reports the old hybrid without displaying its area settings. Source/cache disagreement must restore native Properties. Preserve relevant general fixes while deleting the two-owner mechanism.
3. **Migrate dependencies before removing the type.** Reparent subscriptions to Cash while Bank is still a valid area, then preview/apply the album catalog refresh so the old Bank catalog can lose its row. Review the Bank `## Albums` region explicitly: the current catalog planner skips non-area/project owners, so after declassification a stale region may no longer be automatically cleaned. Convert the useful navigation to an ordinary link or remove only the confirmed generated region. Then remove Bank's area type and any confirmed obsolete area-only metadata. Preserve the bank configuration and all ledger bytes.
4. **Refresh Areas catalogs and verify the final graph.** Bank disappears from area membership and area capture targets; Cash remains an area; the subscriptions album remains valid under Cash; monthly bank notes still belong to Bank. Do not assume parent-link edits move files. No journal or transaction-row migration is required.
5. **Complete remaining card-family acceptance and deploy the verified bundle.** Exercise Bank, ordinary areas, inboxes, projects, and the other fold species. Use the linked source repo and established `bob plugins sync` workflow; respect protected deployment provenance. Keep the corrected Bank state as the prerequisite for declaring the replacement complete.
6. **Finish documentation and narrowly scoped memory maintenance.** Correct `docs/bank.md`, `docs/props.md`, generated CLI/JSON references, and plugin property-editor/card-architecture pages. Replace stale hybrid fixtures in tutorials. The inspected Area/Project docs still list Bank as excluded while current source admits it, demonstrating why source and prose need a consistency sweep. Any memory edits belong under explicit per-note decisions in the replacement plan through `/sase_memory_write`; the canceled plans' old “Area owns Bank” text is not a new requirement. No memory was edited by this research.

The source is changing quickly; use the original epic acceptance criteria as an inventory of retained outcomes, not as a checklist to replay every historical phase. A focused identity/migration prerequisite followed by retained Area/Project and shared-card acceptance is more useful than restarting both large epics unchanged.

## Acceptance that would make the change convincing

| Surface | Required evidence |
| --- | --- |
| Vault migration | Diff preserves Bank config, prose and ledger/journal contents; Bank parent stays Cash; subscriptions parent is Cash; no stranded generated catalog; no accidental task loss. |
| Bank identity | Untyped Bank remains usable; ordinary notes with a `bank:` key do not become hubs; canonical Bank cannot mount an Area Card, including a stale/legacy-type fixture. |
| Props contract | Bank exposes no area settings or inherited task-policy ghosts; generic metadata editing works; bank-map edits still route through the bank owner; obsolete setting ops refuse; Area/Project contracts remain intact. |
| Graph and capture | Bank absent from `areas list` and ordinary area capture targets; no album parent-kind errors; no album/record identity or membership loss; normal Bank navigation remains available. |
| Bank operations | Config, month discovery, ensure, import/deduplication, acknowledgements, balances, subscription matching and coverage retain behavior. Use representative fixtures, not live mutations. |
| Real UI | One Bank title and foot in desktop Reading and Live Preview; `_`, `-`, `==`, `+` work independently; correct Cash breadcrumb/hue; narrow/wide and light/dark screenshots. |
| Failure paths | Bad/mismatched YAML, missing capability/editor, mount loss, Source, embeds/popovers, mobile, unload, path changes and delayed callbacks restore or retain appropriate native UI; no hidden-without-replacement state. |
| Multiple panes | Two panes on Bank have independent valid mount identity; switching one to Cash cannot alter the other's owner or focus; late callbacks cannot resurrect an Area Card. |
| Passivity and rollout | Repaint/fold/resize produce no vault writes or paint-triggered bob spawns; deployed versions match the verified bundle; older-backend behavior is explicit. |

The key regression tests already have natural homes: Rust `props_contract` and area/bank/album fixtures; plugin home-card eligibility, bank title/setup, property-editor settings, frontmatter ownership, and fold suites; real-app bank and takeover harnesses. Update tests that assert the hybrid rather than deleting general ownership/failure tests. No new permanent migration command is necessary for a one-note correction unless the implementation discovers broader affected data.

## Evidence references and limits

The repository references below point at the inspected snapshots. Plan and bead references were read through SASE rather than directly from sidecar files.

- **S1:** `plan:202611/area_project_cards.md`, especially bank hybrid semantics, contract phases, and takeover; `bead:bob-cli-pl` and `bead:bob-cli-pl.9` for cancellation, dependencies, and recorded deployment caveats.
- **S2:** `plan:202611/bank_property_card_fold.md`, Goal, bank takeover, and `bank-polish`; `bead:bob-cli-q6`, `bead:bob-cli-q6.4`, `bead:bob-cli-q6.6`. The last phase's area strip is a planned requirement, not established as implemented by this research.
- **S3:** [Bank hub schema and task wording](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/docs/bank.md#bankmd); audited `glossary:area-note`, `glossary:bank-card`, `glossary:bank-row`, `glossary:property-card`.
- **S4:** [Home-card model](https://github.com/bobs-org/bob-plugins/blob/a14ccc4658e4ae0f005efae8a6a9f78dfe6e35c0/plugins/bob-ledger-tools/src/249b-plugin-home-card-model.js), especially `homeCardEligible`; `scripts/test-ledger-tools-home-card-model.cjs` explicitly admits typed Bank.
- **S5:** [Bank/Area arbitration](https://github.com/bobs-org/bob-plugins/blob/a14ccc4658e4ae0f005efae8a6a9f78dfe6e35c0/plugins/bob-ledger-tools/src/249db-plugin-bank-area-arbitration.js); adjacent `249da` ownership, `249e` home foot, `248c` bank hosts, `248ca` bank foot, `248cb` title, and `248cc` frontmatter-host fragments show the integration points.
- **S6:** [Bank scan](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/src/native/bank/scan.rs), [props note-kind resolver](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/src/native/props/roles.rs), and `src/native/bank/month.rs::canonical_template`.
- **S7:** [Area/Bank settings table](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/src/native/props/contract/settings.rs), adjacent `read.rs::build` and `capabilities`, `tests/cli/props_contract.rs`, and [documented hybrid contract](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/docs/props.md#area-and-project-settings).
- **S8:** [Album direct-parent validation](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/src/native/albums/registry.rs), `analyze_direct_parent`; `src/native/albums/catalog.rs::build_graph`; bob-plugins `plugins/bob-navigation-hotkeys/src/208-parent-note-picker-model.js`.
- **S9:** [Subscription discovery](https://github.com/bobs-org/bob-cli/blob/4dd787bceaa2c0f16e25336ec6b3ff65d6a731f5/src/native/bank/subscriptions/registry.rs), `SubscriptionRegistry::load`; adjacent `loader.rs` documents guarded registry inputs and degradation when subscription declarations are invalid.
- **S10:** [Frontmatter ownership and contract gate](https://github.com/bobs-org/bob-plugins/blob/a14ccc4658e4ae0f005efae8a6a9f78dfe6e35c0/plugins/bob-ledger-tools/src/240q-plugin-property-card-frontmatter-ownership.js); `249ca` editor routing, `298m` bare-plus options, `298w` settings/fallback hints, and `298x` contract-refresh logic.

Remaining uncertainty is primarily deployment and complete UI acceptance, not whether Bank needs an area type. The source and two controlled experiments are sufficient to reject a type-only edit and to identify the subscriptions migration. They do not establish that every existing bank feature has passed with the new arrangement; that belongs to the replacement's verification.

## Recommended solution

Make `bank.md` an **untyped, canonical bank hub beneath Cash**, with a single Bank property-card owner and no area task settings. First reparent the subscriptions album to Cash and clean its old managed catalog while Bank is still an area; keep bank month notes parented to Bank. Preserve banking data and the useful shared card work, delete the hybrid arbitration and proposed area strip, and complete the remaining work under a new replacement scope with real-app acceptance. This achieves the conceptual correction without introducing a new note type or relaxing the album hierarchy to accommodate another special case.

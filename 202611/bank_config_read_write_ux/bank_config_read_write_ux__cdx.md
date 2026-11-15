# A readable, trustworthy Bank settings card for Obsidian

Independent research by **cdx**, 2026-11-15.

**Recommendation:** keep `bank.md`’s nested YAML as the single source of truth. Add a small, automatically rendered **Bank settings** summary and a category-first editor in Bob Ledger Tools. Borrow the album Schema Card’s guarded preview/apply and Source-mode repair workflow, while designing the controls around bank semantics. Do not flatten the data, introduce a second configuration store, or make account order casually draggable.

This is a good feature to build. The present experience hides a configuration people must maintain, and the existing category vocabulary is large enough to justify a purpose-built interface. The main design risk is making consequential changes look cosmetic.

## What I investigated

I independently inspected bob-cli’s bank parser, reporting, identity, matching, journal, and import code; the album schema writer; Bob Ledger Tools’ album and bank implementation, tests, styles, and documentation; and an opened Git snapshot of the Bob vault’s `bank.md` and `eat.md`. I also inspected existing album UI screenshots, checked official Obsidian documentation, and ran a small read-only reporting experiment against a disposable synthetic vault.

I did not consult any other swarm researcher, report, transcript, or findings. No product code or vault configuration was changed. The vault evidence below is the opened repository snapshot, not a claim to have inspected the current unsaved Obsidian buffer. I did not run a fresh Obsidian UI session or the full product test suites.

Source revisions and links are collected near the end. Bracketed identifiers throughout refer to those sources.

## Why the field is invisible

There are **two separate causes**.

1. Obsidian’s native Properties editor does not support nested properties. Its official guidance is to use Source mode for them. Changing this particular property’s type will not produce a suitable nested editor. [Obsidian Properties documentation](https://obsidian.md/help/properties)
2. Bob Ledger Tools deliberately hides the hub’s `bank` property with `.bob-bank-hub-note .metadata-property[data-property-key="bank"] { display: none !important; }`. `bankMarkSyncHubProperty()` assigns the class, and the existing browser acceptance script explicitly expects `hub-bank-property-hidden`. There is no corresponding bank configuration editor in the implementation I inspected. [P1]

This is therefore an unfinished presentation surface, not evidence that the YAML has disappeared. Simply removing the CSS does not solve nested editing. Conversely, adding a card without revisiting the old hiding code leaves a scoping problem: the current method puts the class on the document body as well as individual leaves. A body ancestor can hide another pane’s unrelated `bank` property while the hub is active. That is a code-level observation; I did not reproduce it in a live split-pane session.

**Required adjustment:** make suppression belong to the specific rendered hub surface that owns the replacement. Remove the body-wide suppression. Source mode must always retain the actual YAML, and a failed renderer must leave a visible repair path.

## Design for the actual configuration

The inspected `bank.md` contains:

| Area | Observed state | Design implication |
| --- | --- | --- |
| Accounts | One `checking` account, labelled WF Checking, tracked from 2026-11-11 | Compact account summary; multi-account management is secondary |
| Authored categories | 21: twelve Everyday, eight Bills, one hidden Kids category | Category editing is the primary job; use grouped, searchable rows |
| Built-ins | Four supplied by Bob: income, refund, transfer, cash | Show effective categories, including values absent from YAML |
| Effective vocabulary | 25 categories, 24 visible and one hidden | Explain counts; “21 categories” alone would understate what the picker offers |
| Rules | No authored rules | Offer a quiet empty state, not an elaborate rule-builder hero |
| Staleness | No authored value; Bob defaults to 10 days | Display the effective default without writing it merely by opening the editor |

These are snapshot observations, not proposed changes. [V1, C1]

The hub already contains prose and a `bob-bank` queue card. Its ordinary use is acknowledging transactions, not maintaining configuration. A large permanently expanded settings form would make the hub worse. Keep settings easy to find and quick to scan, with the queue and authored note content intact.

## What to borrow from album `record` editing

The album implementation is a strong local precedent, substantially more than a pretty YAML dump. [P2, P3, C2]

- A collapsed summary and expandable readable schema live in Reading view and Live Preview, without generating Markdown into the note.
- A dedicated Schema Card exposes typed editing, diagnostics, and a consequence preview.
- Bob validates the proposed operation; Apply only accepts the exact draft whose preview succeeded. Late responses cannot enable an outdated draft.
- The editor preserves draft inputs and focus, refuses stale changes, supports guarded Undo, and distinguishes a saved change from a failed subsequent sync.
- Source-mode navigation targets the relevant field or diagnostic. A Done action validates before returning.
- The `record` property is suppressed on the album surface, while Source mode remains available.

Reuse this interaction discipline and compatible utilities. Do not mechanically copy its schema-field vocabulary, all of its keyboard commands, or its entire implementation into a bank module. A bank category is not an album field; an account alias is not a label; a rule is not a choice chip. Start with bank-specific model/session adapters and extract only genuinely shared behavior once the second consumer is concrete.

## Proposed experience

### 1. A quiet summary immediately below the hub title

Automatically mount one panel on the canonical root `bank.md`, in Reading view and Live Preview. Anchor it after the title and before the existing content, with a fallback when the note has no title. Do not require a new fence or insert a generated settings section. Do not render the full editor in embeds or hover previews.

Illustrative collapsed state, using the inspected snapshot:

```text
▸ Bank settings                                  Edit settings
  WF Checking · 24 visible categories · 1 hidden · No rules
```

At a narrow width, the action wraps to its own row. The disclosure and Edit button are separate controls: expanding reads; editing opens the card. Remember the disclosure per pane, not in YAML. Start collapsed for valid configuration and expanded for an actionable configuration error.

Expanded content has four short sections:

- **Accounts:** display name, kind, “Default for rows without an account,” and tracking start.
- **Categories:** Everyday and Bills groups, a labelled Built-in group, and a collapsed Hidden group. Each row shows emoji, label, and a small keycap for the effective shortcut.
- **Rules:** ordered plain-language summaries, or “No rules. Bob can still learn categories from acknowledged transactions.”
- **Checks:** “Balance evidence becomes stale after 10 days · default.” This describes the actual `balance_asof` comparison; it is not a scheduling or notification setting. [C3]

Provide a persistent **Open YAML** link. A configuration-valid indicator must not say “Bank healthy”: a valid configuration does not prove complete imports or a reconciled balance. Existing account/queue surfaces retain that responsibility.

### 2. A category-first Bank settings card

Use one modal with **Categories**, **Accounts**, **Rules**, and **Checks** sections or tabs. Categories is the initial section for this vault; remember the last section during the session. Keep this interface visually related to the album card, with fewer always-visible actions.

```text
Bank settings                                    Open YAML   ×
Categories 25    Accounts 1    Rules 0    Checks

Find a category…                                  + Category
EVERYDAY
☕ Coffee                                      c     Edit
🍽️ Eating out                                  e     Edit
⋯
BILLS
🏠 Housing                                     1     Edit
⋯
▸ Built-in categories 4
▸ Hidden 1
```

On selecting a category, show a compact labelled form in the same card; do not open a stack of nested modals:

```text
Edit category: Eating out
Label       [Dining out                         ]
Emoji       [🍽️]
Group       [Everyday                           ]
Shortcut    [Automatic / Custom]  [e]
Show in category picker                         On
Stored key: dining

Preview: “Eating out” → “Dining out”. Stored category stays dining.
                                                 Cancel   Apply
```

The preview updates after a short typing debounce. Apply is disabled until Bob validates the current draft. Enter may apply a ready draft when focus and composition state make that action unambiguous; typing inside inputs must never fire letter shortcuts. Escape cancels the open edit first and closes the card only from its browsing state.

The stored key is secondary, copyable information. It is not an editable name field. For a new category Bob proposes a valid key, and the preview shows it before creation. Once saved, changing the label must leave the key fixed.

**Automatic shortcuts need provenance.** The display should distinguish “Automatic → e,” “Custom e,” and “No shortcut available.” Clearing a custom shortcut means remove the override, not force an empty shortcut. Validate collisions with hidden categories too: explicitly assigned hidden shortcuts remain reserved. Show other categories whose automatic shortcuts will change before applying a reorder or shortcut edit. [C1]

**Built-ins need different verbs.** Their stored keys carry accounting meaning. Allow presentation overrides and hiding, but do not offer Delete or Rename key. If an override exists, offer **Restore default appearance** with a preview of the fields being removed. The effective category remains present.

**Prefer Hide to Delete.** Hiding Kids should say that it stops being offered while existing rows remain valid. Its money still counts according to the existing accounting rules. Hidden targets also cease to be eligible category suggestions, including through rules; the preview must mention that when relevant. Deletion is secondary and refused while current bank rows or rules reference a custom key. An incomplete dependency scan must never be presented as zero uses.

### 3. Account controls that expose meaning

Show the default-account badge prominently. Labels are editable; account aliases are immutable after creation because import identities include them. [C4]

For the initial version:

- Add an account at the end of the ordered mapping, with explicit kind and required tracking start where applicable.
- Allow label changes and previewed start-date changes. Explain that tracking dates affect import eligibility and coverage, and do not backfill rows automatically.
- Permit kind changes only for accounts proven unused by both rows and journal evidence; otherwise require a separately designed migration.
- Do not expose account reordering, Make default, alias renaming, or removal of a used account as routine settings operations. These need a separate migration design, not a generic confirmation dialog.

This is a deliberate narrowing of “easy to write”: ordinary settings should be easy; identity/history changes should not masquerade as ordinary settings. Source mode remains available to an expert, but is not labelled a safe migration tool.

A small experiment demonstrates why. I created one acknowledged synthetic row, `$10.00 Example shop [cat:: dining]`, with no account field, and queried the installed `bob 0.5.0` binary:

| First account in YAML | Reported Out | Reported traced cash |
| --- | ---: | ---: |
| checking | $10.00 | $0.00 |
| pocket, kind cash | $0.00 | $10.00 |

Only mapping order changed between runs. Each `bob bank report -b <scratch> -m 2026-11 -f json` returned exit 0, and a before/after byte comparison confirmed that the read command did not modify its scratch vault. This corroborates the source: account-less rows resolve to the first configured account at read time. [C4]

### 4. Rules without misleading promises

Use an ordered list with visible numbers, Add rule, and Move up/down buttons; dragging may be an optional enhancement. A rule form has **Description contains**, **Payee**, **Category**, and **Link**. Say that matching is case-insensitive substring matching, not regex. Optional actions remain optional, with current fallback behavior explained.

An example row is “1 · Description contains VENMO → category Transfer.” Rule changes affect future imports and eligible current suggestions; they do not rewrite existing transaction text. The UI must never imply that saving a rule recategorizes historical rows.

There is an important implementation nuance: `naming.rs` selects the first matching rule for payee/link resolution, whereas `suggest.rs::rule_category()` skips rules without a category or with an ineligible hidden category and can use a later matching rule. Read-time category matching also skips patterns containing four consecutive digits because journal descriptions are masked. “First matching rule wins everything” would therefore be inaccurate. [C5]

Use **Rules are checked top to bottom** as the main explanation and expose action-specific resolution in details. Preserve these semantics in this feature. A true unification of matching behavior would be a separate contract change.

A small sample-description tester would be useful later, provided Bob performs it through the same evaluators and labels import-time versus read-time results. It should not become a prerequisite for solving the present category-editing problem. Do not claim exact historical impact from masked journal descriptions or silently collect raw bank descriptions for a preview.

### 5. Beauty as clear hierarchy

Use the existing Obsidian theme variables and Bob area accent. Give the panel a thin border, gentle accent wash, restrained rounding, and quiet section labels. Keep money-status green and warning amber for their existing meanings; a valid settings form is not a green financial-health dashboard.

Put labels first, technical keys second, and operations at the point of use. Align shortcut keycaps in one column. Avoid a wall of large colored pills and a footer full of editing commands. Let long labels wrap; do not hide critical distinctions behind ellipses or hover-only help.

Every action has a visible button and accessible name. Use real labelled inputs, obvious keyboard focus, text alongside status colors, live announcements for preview/refusal, and keyboard alternatives to reordering. At about 375 CSS pixels, forms stack into one column, tabs remain reachable, and the Apply region stays visible without covering fields. Validate light, dark, high-contrast, and reduced-motion behavior in the actual app.

## Implementation architecture and reliability

### One authoritative parser and writer

Extend bob-cli’s bank domain; keep the plugin a presenter and interaction controller. Existing `bank list`/`report` JSON exposes effective accounts and categories but is not a complete editable configuration contract: it omits rules, staleness configuration, and authored-versus-derived provenance. It must not be serialized back into YAML. [C1, C6]

Proposed new interfaces, **not existing commands**:

```text
bob bank config -f json
bob bank update -d -i - -f json    # preview a typed envelope on stdin
bob bank update -i - -f json       # apply that validated draft
```

Keep bare `bob bank`’s read-only list behavior. `bank` already owns bank configuration, rows, monthly notes, and journal operations; no further nested generic settings command is needed. New public options must follow the repository’s short-alias and alphabetical-help conventions.

The configuration report should contain:

- Version, hub path, configuration state, capabilities, and a revision/fingerprint.
- Ordered accounts, declared category entries, effective built-ins, effective shortcuts, rules, and effective/default staleness.
- Explicit presence/provenance: declared versus built-in, scalar versus mapping, custom versus derived shortcut, omitted versus authored default.
- Structured diagnostics with key paths and source locations, plus whether an entry is safely editable.
- Usage/dependency evidence when needed, with a completeness flag. Counts are not required on every idle render.

Represent ordered maps as ordered entries at the protocol boundary. Rule position plus expected revision can identify a rule initially; adding durable IDs to YAML is unnecessary for this scope.

Operations should be small and typed—category add/set/move/hide/remove/reset, account add/set, rule add/set/move/remove, and staleness set/unset—with domain restrictions enforced by Bob. Reuse the existing bank parser and hotkey allocator for validation and final postimage verification.

### Preserve authored bytes

The snapshot uses compact flow mappings, such as `coffee: { label: ☕ Coffee, hotkey: c, group: Everyday }`. Supporting those is a release requirement, not an exotic future case. The scalar category shorthand must work too. Expand a scalar to a mapping only when its edited fields require it; do not normalize every category when one label changes.

Adapt the album writer’s conservative span-editing techniques, but account explicitly for bank’s ordered rule sequence and inline category maps. Preserve unrelated frontmatter, comments outside the changed span, body prose, code fences, line endings, and mapping order. Move untouched entries as source slices where possible. No-op operations preserve the original bytes. [C2]

For duplicate keys, ambiguous anchors/aliases, merges, or other syntax the writer cannot faithfully patch, render an explicit diagnostic and offer Source-mode repair. Never silently reserialize the whole frontmatter as a fallback. Native Obsidian `Vault.process()` is useful for in-app atomic read/modify/write, but its documented guarantee does not replace Bob’s domain validation, external-writer guards, or coordinated transaction path. [Obsidian Vault API](https://docs.obsidian.md/Plugins/Vault)

### Preview and apply must describe the same world

Use the album session model: a draft revision, session identity, current hub revision, and relevant vault generation gate each response. Late previews are ignored. Apply requires the exact validated envelope; it is serialized across cards. Draft fields, selection, focus, and caret survive preview updates. [P3]

Before applying, reconcile all open hub editors with disk. If two unsaved panes diverge, do not sequentially save them and pick the last writer. Refuse with an actionable message and retain the draft. Recheck after any pre-sync, obtain the existing maintenance/write coordination, validate the file preimage, and install only the planned change. Existing import operations must serialize against configuration mutation.

A hub-only fingerprint is insufficient for a consequence based on history. For removal, kind changes, or history-sensitive previews, also guard the relevant bank-month/journal snapshot and directory membership. If rows or journal evidence change, invalidate the preview and require another review. Do not use JavaScript-calculated usage counts as write authorization.

Use the album writer’s scoped commit and pre/post-sync model for an explicit settings Apply, with `bank.md` as the only intended configuration write. Dry runs acquire no write locks and do not sync, commit, or mutate. A successful local write followed by sync failure must read **Saved locally; sync failed**, with **Retry sync**. A timeout with unknown outcome must refresh authoritative state before any retry; never blindly replay the mutation.

Undo should be an explicit Bob-produced inverse operation with a matching post-apply revision and fresh validation. It should preserve prior byte form where possible. If intervening rows now reference a newly added category, Undo of its creation must refuse removal rather than erase their vocabulary. Use guarded Undo for the last successful edit, not a fabricated browser-only history.

### Failure and compatibility states are part of the design

| State | Presentation and action |
| --- | --- |
| Valid | Readable summary; editing enabled after a fresh supported report |
| Missing `bank` mapping | Setup guidance and Open YAML; no silent default insertion |
| Invalid mapping | Visible diagnostic and source target; never “No categories” |
| Missing/old Bob or unsupported protocol | Explain update requirement; retain Source access; no write fallback |
| Refresh failed | Clearly marked last-good data if available, Retry, and editing disabled |
| Preview stale | Preserve draft; show conflict; explicit refresh/re-preview |
| Apply pending | One in-flight operation; prevent double Apply and late-pane repaint |
| Saved but sync failed | Show saved state and sync-only recovery |
| Mobile | Read-only summary when validated data is available; Source-mode guidance otherwise; no subprocess-backed editing |

Do not introduce a second bank parser solely for mobile parity. Mobile writing is an explicit deferral until a supported authoritative writer exists there. The desktop-width-375 test is still required independently of mobile support.

## Alternatives and critique

| Approach | Benefit | Why I would or would not choose it |
| --- | --- | --- |
| Unhide native `bank` | Very small change | Does not provide native nested editing; useful only as fallback visibility |
| Readable panel plus Open YAML | Fastest meaningful improvement | Good first increment, but does not finish the requested writing experience |
| Custom panel and guarded card | Fits the existing album pattern; exposes bank consequences | **Recommended**; moderate cross-repository work justified by actual category complexity |
| Flatten to many properties | More primitive controls become native | Loses coherent ordered structure, creates migration work, and leaves rule editing awkward |
| Notes/Bases for every account/category | Familiar records and tables | Makes small configuration into a new data model with identity and ordering concerns |
| Generic community property editor | May reduce initial form work | Would still need custom default-account, identity, hotkey, masking, and transaction safeguards |
| Plugin settings or external YAML | Easy generic settings UI | Moves configuration away from its hub or creates competing truth; weakens portability |

The idea is sound if the scope is **understand and safely maintain Bank settings**. It becomes a poor trade if expanded into a general YAML editor, financial dashboard, category-history migration engine, or mobile backend project. Appearance matters, but a compact form that preserves a user’s carefully authored note is more valuable than a rich form that changes financial interpretation unexpectedly.

Explicit adjustments to the initial request:

1. Render a meaningful replacement outside native Properties instead of trying to teach Properties this nested object.
2. Prioritize categories based on the inspected vault; accounts and rules remain complete readable sections, with constrained typed editing.
3. Keep stable stored identities; exclude routine account default/reorder/rename and history migration from the first release.
4. Preserve existing rule behavior and clearly explain its action-specific matching rather than simplifying it silently.
5. Treat safe preview, stale refusal, byte preservation, and recovery as acceptance requirements, not polish.
6. Promise desktop editing first; state the mobile limitation explicitly.

## Delivery and acceptance

Ship in two cohesive increments. First add the authoritative configuration report, automatic readable summary, diagnostics, scoped property suppression, and Source-mode repair entry. Then complete category-first editing and the remaining bounded account/rule/check operations using the guarded writer. The first increment is useful but must not be called completion of the full read/write request.

Before enabling writes, require these tests:

- A scratch fixture matching the real hub: 21 authored categories, inline maps, numeric quoted shortcuts, hidden Kids, absent rules/default staleness, and four effective built-ins.
- Scalar and flow/block mapping edits, emoji/quoting/comment preservation, BOM/CRLF, malformed/duplicate/unsupported YAML, and exact no-op bytes.
- Stable stored keys; reserved `q`; explicit hidden-key collisions; automatic shortcut reassignment; reset of built-in overrides; used-category removal refusal across all bank months and rules.
- Account-less row semantics; immutable import identity; used-account restrictions including journal-only evidence; date changes that do not auto-backfill.
- Rule ordering, payee-only preceding category rules, hidden targets, digit-masked read-time matching, and absence of historical row rewrites.
- Preview staleness after hub, row, or journal changes; unsaved and divergent panes; pre-sync changes; double Apply; timeout reconciliation; sync-only recovery; stale Undo and inverse deletion that becomes unsafe.
- Fresh real-app runs in Reading/Live Preview/Source, theme and narrow-pane checks, keyboard-only editing, IME composition, source return after repair, navigation/unload during async work, and split/popout panes with unrelated `bank` properties.
- Hash checks proving that rendering and previews never write, and that an Apply changes only its intended configuration bytes. Verify cached bank consumers refresh coherently after a successful apply.

Implementation should extend `src/native/bank/` and Bob Ledger Tools’ committed source fragments. The existing album/browser tests provide patterns rather than proof for the new feature. Update the bank contract and plugin documentation, build generated plugin entrypoints, and deploy with the repository’s normal `bob plugins sync` workflow when the feature is actually implemented.

## Evidence and limits

These links identify the code inspected locally through approved repository opens; line numbers can be located by the named symbols. They are not citations to peer research.

- **V1 — Vault snapshot:** `22dd8c80ccfc486088c2bc0986f2d029ccdd726d`; [bank.md](https://github.com/bobs-org/bob/blob/22dd8c80ccfc486088c2bc0986f2d029ccdd726d/bank.md), [eat.md](https://github.com/bobs-org/bob/blob/22dd8c80ccfc486088c2bc0986f2d029ccdd726d/eat.md). Read configuration/structure, not transaction history.
- **C1 — Configuration contract:** bob-cli `9c2c240480998e1b9ecd82a5c70aefbe963b8c58`; [docs/bank.md](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/docs/bank.md), [config.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/config.rs): `parse_bank_config`, `finalize_categories`, `assign_hotkeys`, `parse_rules`.
- **C2 — Album writer precedent:** [update directory](https://github.com/bobs-org/bob-cli/tree/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/albums/update): `protocol.rs`, `plan.rs`, `spans.rs`, `run.rs`; typed envelopes, revision checks, reversible narrow edits, and maintenance execution.
- **C3 — Staleness:** [status.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/status.rs), `proof_for`: compares today against balance-as-of, with `stale_after` as the threshold.
- **C4 — Identity and interpretation:** [model.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/model.rs), `collect_rows`/`compute_totals`; [identity.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/identity.rs), `transaction_key`; [journal.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/journal.rs).
- **C5 — Matching:** [naming.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/naming.rs), `resolve_name`; [suggest.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/suggest.rs), `rule_category`/`is_offerable`; [import_plan.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/import_plan.rs), import eligibility and restoration.
- **C6 — Current JSON:** [list.rs](https://github.com/bobs-org/bob-cli/blob/9c2c240480998e1b9ecd82a5c70aefbe963b8c58/src/native/bank/list.rs), `to_json`; bank account/category serialization in C1.
- **P1 — Existing bank suppression:** bob-plugins `f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a`; [bank marks](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/plugins/bob-ledger-tools/src/241p-plugin-bank-marks.js), `bankMarkSyncHubProperty`; [styles](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/plugins/bob-ledger-tools/styles.css), line 9094; [browser acceptance](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/scripts/obsidian-bank-ui-e2e.cjs), `hub-bank-property-hidden`.
- **P2 — Album UI:** [docs/albums.md](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/docs/albums.md); source fragments `241v-plugin-album-header.js`, `241w-plugin-album-schema-model.js`, `241x-plugin-album-schema-dom.js`. Existing screenshots inspected in bob-cli’s `evidence/album-schema-finish-apply-final/shots/` were illustrative artifacts already in the primary repository, not new UI verification.
- **P3 — Album session and transport:** [242b-plugin-album-update-session.js](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/plugins/bob-ledger-tools/src/242b-plugin-album-update-session.js) and [242a-plugin-album-update-service.js](https://github.com/bobs-org/bob-plugins/blob/f72bd4e96403a7e6a3f287c8f191ec70fa3e5c4a/plugins/bob-ledger-tools/src/242a-plugin-album-update-service.js).

The synthetic experiment used the installed `bob 0.5.0`, not a freshly built binary from the cited bob-cli SHA. Its observed result agrees with the inspected implementation. The proposal’s new commands, report schema, controls, and additional safety restrictions are recommendations, not descriptions of shipped functionality.

## Recommended solution

Build **Bank settings** as a compact rendered companion to `bank.md`, with a category-first card powered by a new authoritative Bob configuration report and guarded writer. Preserve the YAML, the existing queue, stored identities, and current rule semantics. Reuse the album editor’s preview/apply, conflict, Undo, and Source-repair discipline; simplify its presentation around the actual banking tasks. Ship ordinary category/account/rule maintenance with clear consequences, and leave account-identity/default migrations outside the first release. This offers the strongest balance of readability, safe editing, visual calm, and maintainable implementation.

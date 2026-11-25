# Bank and album schema disclosure: a compact property-card design

Independent research by **cdx**, 2026-11-25. This report was prepared without consulting any other swarm researcher's report, transcript, or findings.

**Recommendation in brief.** Proceed. Bank should participate in the existing property-card frontmatter ownership system, start with its configuration details collapsed, and share a guarded `_` disclosure action with albums. Keep albums expanded initially. Preserve a compact, informative summary, visible problems, the complete `-` Properties drawer, and the existing editors. This is a focused extension of working infrastructure, not a new card system.

**Evidence and limits.** I inspected bob-cli at `814b6583e63165a4f2419158af50d4774fc8b034` and bob-plugins at `eac9d7448d056e60af1e0f4224554c6ca1ed28d2`, including production fragments, styles, documentation, and tests. I read the audited Bank Card, Album Card, Property Card, Obsidian, and artifact memory. Three focused existing test suites passed, listed below. I did not inspect the personal bank ledger, change a plugin, run live Obsidian acceptance, or consult peer reports. Visual proposals below are design recommendations, not screenshots of a working implementation. Financial labels and counts in the sketches are illustrative.

**Why this is a good idea.** Bank configuration is supporting material for a hub whose primary work is reviewing transactions and following bank tasks. Showing its full accounts/categories/rules inventory on every visit imposes a substantial vertical cost. Folding it retains orientation and gives the operational content room. An album's schema, by contrast, explains the facts its records collect; its current expanded default is defensible. Consistency should mean the same disclosure behavior and affordance, not necessarily the same default density.

Replacing duplicate native Properties also fits the product. Obsidian's documented property editor does not support nested properties, whereas Bob already has specialized editors for the `bank:` and album `record:` mappings. Obsidian offers a global Properties display setting, but changing that would affect unrelated notes. The appropriate solution is scoped ownership by the functioning card, with Source and the native sidebar available for recovery. [Obsidian Properties](https://obsidian.md/help/properties)

The main criticism of the request is its ambiguity: “proper property card,” “schema,” and “hides properties” can accidentally turn into three separate redesigns. Define the feature in terms of ownership and interaction. Do not infer a vault schema migration, a replacement bank editor, new bank analytics, or unconditional suppression of native controls.

**What exists today.** Bank is already substantially a property card, despite its explicit exception for whole-frontmatter ownership.

| Surface or behavior | Current implementation | Consequence for the change |
| --- | --- | --- |
| Bank note-top card | Uses `createPropertyCardHost`, `.bob-property-card`, the Bank species badge, specialized editor, and shared foot | Extend the existing adapter; do not build another card |
| Bank details | A `Setup` disclosure already shows accounts, categories, rules, findings, and cached account status | Change its default and behavior; preserve its useful presentation |
| Bank initial fold | `BANK_SETUP_DEFAULT_EXPANDED = true` | Change healthy bank's initial state to collapsed |
| Invalid bank configuration | Model forces `expanded: true` on every render | Merely adding a toggle leaves invalid cards effectively uncollapsible |
| Album schema | Already has a summary button and hidden chip body; defaults expanded | Route `_` into the existing state transition |
| Fold lifetime | Bank and album maintain plugin-session Maps keyed by note path and refresh their mounted views | Preserve this established session behavior |
| Properties foot | Bank already appends it outside the configuration body, even for collapsed/loading states | Keep the full inventory available independently of schema visibility |
| Native Properties | Bank hides its `bank` row through per-row ownership; whole-container eligibility excludes bank | Add bank to the shared coordinator, including its mount-path adapter |
| Keyboard dispatch | `==` resolves the species editor; guarded bare `-` toggles Properties; `+` opens the Property Editor | Add one guarded `_` arm without changing those meanings |
| Bank classification | The CLI recognizes root `bank.md` as bank before normal type classification, while it also has area settings | Preserve `==` for bank setup and `+` for general/area properties |

These are observable in the [bank model](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/248a-plugin-bank-setup-model.js), [bank host](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/248c-plugin-bank-setup-hosts.js), [bank foot adapter](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/248ca-plugin-bank-setup-foot.js), [album host](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/241v-plugin-album-header.js), and [CLI property ownership classification](https://github.com/bobs-org/bob-cli/blob/814b6583e63165a4f2419158af50d4774fc8b034/src/native/props/roles.rs).

**The interaction contract I would ship.** Give four neighboring actions four distinct jobs:

| Gesture | Meaning | Visible equivalent |
| --- | --- | --- |
| `_` | Show/hide the specialized configuration or schema details | Bank `Setup` / album `Schema` disclosure row |
| `-` | Show/hide the complete note Properties inventory | Existing foot disclosure |
| `==` | Open the specialized editor | Bank `Edit` / album `Schema` editor action |
| `+` | Open the Property Editor | Existing Properties affordances and command |

A folded schema must not close the Properties drawer. Opening the editor must not expand the schema as a side effect. Neither disclosure writes YAML, invokes a writer, changes the editor undo history, or alters transaction/index folds. The target is the note-top bank or album card, not a `bob-bank` queue/month/subscriptions fence, an album catalog row in an owner note, or the album's generated record-group folds.

I recommend retaining **Setup** as the bank section's visible name and **Schema** for albums. Accounts and import rules are configuration, not a record schema; the current word is more concrete. The command can be **Toggle card schema**, with a description that explicitly includes bank setup. This is a terminology refinement to the request, not a different action. Avoid presenting an unlabelled underscore as the only way to discover the feature.

**Defaults and state should be precise.** “Collapsed by default” means the initial view state, not an instruction to re-collapse after refresh.

| Situation | Proposed behavior |
| --- | --- |
| Healthy bank, no explicit session preference | Collapsed |
| Album, no explicit session preference | Expanded |
| Bank missing its configuration, or initially reporting configuration errors | Expanded initially to teach or diagnose; user may collapse |
| User toggles either card | Store an explicit session override for that note; it wins over defaults |
| Report/metadata refresh, editor save, Properties drawer toggle, or view rebuild | Retain explicit schema state |
| New problem arrives while a card is collapsed | Update the visible problem summary; do not unexpectedly unfold the page |
| Same note in a second pane | Share the note's session fold state, matching today's Maps; each pane still owns its own DOM and focus |
| Plugin reload or a new application session | Reset to species defaults |
| Album rename or deletion | Transfer or remove the override; do not retain stale mount/path entries |

The initial diagnostic exception is an explicit adjustment to a literal “always collapsed” reading. It avoids hiding first-run instructions. More importantly, replace bank's unconditional invalid-state expansion with default selection **before** applying a user override. A click or `_` must have the same understandable effect in an invalid card as in a healthy one. If the bank opens healthy and later becomes invalid, show the alert without erasing the user's explicit choice.

Session-level state is a deliberate compromise: no frontmatter keys, sync conflicts, or surprising permanent preference after an incidental click. Keeping state per pane is a reasonable alternative, but it would change both bank and album's current path-keyed behavior and differs from the shared Properties foot. I would not introduce that migration here. Album record-group folds already have a separate pane-oriented contract; leave them alone. [Album card documentation](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/docs/albums.md), [Properties foot state](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/240p-plugin-property-card-foot-state.js)

**Make the collapsed card informative and calm.** Reuse the existing muted tinted panel, thin accent edge, 8px radius, typography, and species badge. The current shared chrome is already a visual vocabulary; this feature should look like a natural reduction of it. Keep Bank's current H1 placement and title ownership separate in the first implementation. Removing native Properties does not require moving the title into the card. A title-slot migration could be considered later if an actual visual review shows duplicate titles; it should not become an invisible prerequisite of this request. [Shared card styles](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/styles.css), [Card architecture](https://github.com/bobs-org/bob-cli/blob/814b6583e63165a4f2419158af50d4774fc8b034/docs/develop/plugins/architecture.md)

Suggested healthy folded bank card, below the existing Bank heading:

```text
┌───────────────────────────────────────────────────────────────┐
│ 🏦 BANK                                           Edit  ==    │
│ ▸ Setup    Checking + 1 · 18 categories · 3 rules          _    │
│ created Nov 12, 2026                          ▸ Properties  - │
└───────────────────────────────────────────────────────────────┘

Queue and authored note content continue immediately below.
```

Suggested unhealthy folded state:

```text
┌───────────────────────────────────────────────────────────────┐
│ 🏦 BANK                                           Edit  ==    │
│ ▸ Setup    Checking + 1 · 18 categories · 3 rules          _    │
│ ! Setup needs attention · 2 problems             Show details │
│ created Nov 12, 2026                          ▸ Properties  - │
└───────────────────────────────────────────────────────────────┘
```

Expanded state adds the existing Accounts, Categories, and Rules sections between the summary and foot. Album keeps its current title block and schema field rows; the same small `_` cue joins its disclosure. The fold row and editor action are separate sibling controls: a click on Edit must never also toggle the body.

Use a broad summary-row hit area with a leading chevron, stable text, and a trailing understated keycap where the shortcut is available. In a narrow pane, let the summary wrap under its label and reserve space for the action. Do not shrink the type or ellipsize problems. Base responsive behavior on the card/pane width, not just the application viewport: the current bank CSS uses a viewport media query, which cannot reliably identify a narrow split inside a wide window. A flex layout that wraps intrinsically or a scoped container query is preferable.

Preserve the useful existing account-label/category/rule summary rather than adding balances or spend statistics. Count hidden categories explicitly when present; distinguish known zero from loading/unavailable data. Warnings, configuration error count, stale/cached-data status, and retry access must remain outside the fold. Account `stale`/`delta` statuses deserve a compact attention cue even if the schema itself is valid. Do not label the card “healthy” merely because its configuration parses.

This is necessary because today's renderer puts findings, account status, and the stale-data notice **after** the collapsed-state early return. Changing only the default would hide information that currently benefits from being expanded. The existing builder also creates a bank `aria-controls="bob-bank-setup-body"` reference without assigning that ID to its body; album IDs are derived from the stem and can collide across panes. Fix both within this disclosure change. [Bank DOM builder](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/248b-plugin-bank-setup-dom.js), [Album schema DOM](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/241x-plugin-album-schema-dom.js)

Do not animate the entire card height; stable scroll and focus matter more than a folding flourish. A brief chevron transition is sufficient and should respect reduced motion. Match the existing colors, but communicate problems with words and an icon, not color alone. The aesthetic target is a small, legible note control rather than a miniature financial dashboard.

**Keyboard reliability matters more than choosing an attractive key.** `_` is a reasonable companion to `-`, especially on a US keyboard, but it already has a Vim motion: move down count-minus-one lines to the first nonblank character. The shortcut therefore needs the same strict boundary as the existing `-` and `+` arms. [Vim motion reference](https://vimhelp.org/motion.txt.html#_)

For the bare default binding, require desktop Live Preview, readable Vim state in normal mode, focus in that view's editor content, and a live note-top bank/album schema mount for the current path. Reject pending counts, registers, operators, buffered sequences, insert/replace/visual modes, composition, repeats, and already-handled events. Leave Source mode and all other note kinds alone. Examples that must retain their existing behavior include `d_`, `2_`, `f_`, searching for an underscore, and typing account aliases with underscores.

Recognize the resulting character through `event.key === "_"`; do not hard-code the US physical Minus key. Allow Shift because it commonly produces `_`; preserve the current conservative Ctrl/Alt/Meta guard, with a configurable command binding for layouts that need another modifier combination. `KeyboardEvent.key` is explicitly layout- and modifier-aware. [MDN KeyboardEvent.key](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key)

Extend the current dispatcher rather than installing a separate document-wide hotkey or an unconditional vimrc mapping. Add `_` to both the initial event filter and `propertyCardBareKeyGate`, then resolve a schema-capable species arm. A registry match alone is insufficient: a detached card, an old path, a hidden pane, or an embed must not consume Vim input. Check the originating view and connected mount before handling the event. Keep the existing event deduplication because the dispatcher listens on both window and document. [Keyboard dispatcher and gates](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/248m-plugin-schema-double-equals.js)

Expose a command with normal Obsidian hotkey customization and a way to disable the default bare binding. An alternate command assignment alone does not disable a hard-coded listener. Character shortcuts, including punctuation requiring Shift, need a turn-off/remap mechanism or sufficiently focused scope; they should not fire while a user is entering text. The proposed focus guard plus an explicit off switch is a defensible design, not a claim of audited WCAG conformance. [WCAG character key shortcuts](https://www.w3.org/WAI/WCAG21/Understanding/character-key-shortcuts.html)

In Reading view and for non-Vim users, provide the disclosure button and the same command. I would not add a global bare `_` Reading-view listener in this change. This is an explicit scope clarification: the default character binding follows the existing property-card Vim convention; the action itself is available in both rendered modes.

**Accessible disclosure and focus.** Use a real button with `aria-expanded` and a unique per-mount `aria-controls` target; Enter and Space should activate it normally. Keep the body mounted with `hidden`, or ensure any recreation updates the relationship correctly. This follows the standard disclosure pattern. [WAI disclosure pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/)

The implementation should generate mount IDs, not note-stem IDs, so two panes never refer to the wrong body. A pointer or focused-button toggle retains focus on the disclosure. An editor `_` retains the Vim cursor and editor focus. If a command collapses a region containing focus, return focus to that region's summary before it becomes hidden. Keep status outside the hidden subtree. Preserve the current reading position through the height change instead of scrolling to the card automatically; do not add a jump-history entry for folding. Check two panes, a scrolled-away header, and repeated rapid activation in real Obsidian.

**Native Properties ownership must remain reversible.** The existing coordinator is the right mechanism. It already checks a connected, path-matching card and foot; desktop Live Preview or Reading; valid, closed YAML matching the metadata cache; confirmed `props_v1` for the current Bob executable; and working property-editor/native-command routing. It uses scoped CSS, inertness, accessibility hiding, and generation-bound cleanup. It restores native rendering on invalidation and denied contexts. Bank is currently excluded in both the kind allowlist and the mount-path attribute selector. [Frontmatter ownership coordinator](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/plugins/bob-ledger-tools/src/240q-plugin-property-card-frontmatter-ownership.js)

Add bank's `data-bank-setup-source` mapping and wire acquisition/release into both bank host paths. In Live Preview, construction of a widget is not proof that it is attached: use the mounted/deferred acquisition path, with the current source and generation checks. Reading reattachment needs the same guarded recheck. Navigation, source edits, failed builders, detached mounts, capability changes, and unload must release ownership. Reuse the coordinator's lifecycle rather than adding a parallel CSS flag.

Keep schema disclosure and frontmatter ownership independent. Collapsing the schema must not bring back native Properties. Conversely, a valid-looking fold summary must never hide native Properties if the complete foot inventory or editor route is unavailable. The footer must include loose keys, identity, created, and bank/area settings—not just the nested `bank:` mapping. Preserve the File Properties sidebar, Source YAML, the existing `+` route, and native Add-property fallback.

Distinguish **invalid YAML** from **a valid YAML mapping with invalid bank settings**. The former loses the source/cache proof and restores native rendering. The latter can still show a complete property inventory, a diagnostic bank card, and working recovery routes; its semantic error alone need not force native duplication. Similarly, waiting for a bank report need not block ownership once the complete local inventory and all safety evidence exist. Until they exist, leave native Properties available. Do not invent a JavaScript copy of Bob's bank validation or fingerprint algorithm just to establish UI ownership.

The report remains Bob's authority for accounts, categories, rules, and findings. A cached report must be visibly identified as such; opening or folding cannot launch a fresh Bob process from a paint method. Preserve existing read subscriptions, guarded writers, and error semantics. This feature appears to need **no CLI/JSON contract change and no vault migration**; that is a source-based assessment, subject to implementation proving complete existing foot coverage.

**Implementation scope and seams.** A small shared disclosure interface is useful; a general new accordion framework is unnecessary.

| Work | Existing seam | Required result |
| --- | --- | --- |
| Default and error behavior | `248a-plugin-bank-setup-model.js`, `248c-plugin-bank-setup-hosts.js` | Initial defaults separated from explicit state; no forced reopen loop |
| Shared schema action | Existing property-card registry and `248m-plugin-schema-double-equals.js` | Optional `canToggleSchema`/`toggleSchema` adapter methods; active mount validation; one command and guarded `_` arm |
| Disclosure UI | `248b-plugin-bank-setup-dom.js`, `241x-plugin-album-schema-dom.js` | Matching button treatment, unique IDs, persistent status, separate Edit action |
| Bank native ownership | `240q-plugin-property-card-frontmatter-ownership.js`, bank host/foot | Bank allowlist/path support and complete acquisition/invalidation lifecycle |
| Focus and repaint | Bank/album hosts plus existing foot scroll-preservation approach | Preserve editor/button focus, selection, and visual position across refreshes |
| Styling | `plugins/bob-ledger-tools/styles.css` | Pane-aware wrapping, existing chrome, legible summaries and attention |
| Tests and docs | Existing bank, schema-key, foot, and takeover suites | Replace deliberate bank-native expectation and document the four gestures |

Keep bank and album's existing state stores behind the common action interface initially. Extract only the genuinely shared mounted-target/disclosure behavior. Do not make a field list and a bank setup renderer share a forced data model. Continue editing source fragments and regenerating `main.js` through the repository build; do not edit deployed vault plugins. Deployment remains `bob plugins sync` after implementation verification.

**Alternatives and tradeoffs.**

| Approach | Assessment |
| --- | --- |
| Change only the bank expanded constant | Useful first line of code, incomplete feature: hides status and leaves native duplication and keyboard behavior unresolved |
| Hide `.metadata-container` with a broad snippet or global Obsidian setting | Fast but lacks mount/capability/fallback checks and can affect unrelated notes or Source contexts; reject |
| Move all setup into a modal and remove the inline schema summary | Reduces clutter further, but sacrifices discoverability and the requested inline toggle; reject for now |
| Change `-` to fold everything | Overloads the existing all-properties action and couples unrelated states; reject |
| Persist fold state in YAML or plugin settings forever | More machinery and uncertain defaults across hosts; session state is enough |
| Start both bank and albums collapsed | Visually uniform, but overrides the requested album default without evidence; retain the asymmetry |
| Migrate bank into a full album-like title block simultaneously | Possible with the existing kit, but adds title/H1 ownership and placement risk without being needed for this request; defer |
| Extend the existing card ownership and disclosure adapters | Best fit: smallest coherent change with existing recovery paths and focused validation |

**Verification and release evidence.** Existing tests passed with:

```sh
node --test --test-reporter=dot \
  scripts/test-ledger-tools-bank-setup.cjs \
  scripts/test-ledger-tools-schema-double-equals.cjs \
  scripts/test-ledger-tools-property-card-frontmatter-ownership.cjs
```

This confirms the inspected baseline's focused suites, not the proposed design. In particular, the bank suite asserts forced expansion for invalid configuration, and the real takeover runner has a `bank-native` case that explicitly expects native Properties in both modes. Those assertions must change intentionally. [Bank tests](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/scripts/test-ledger-tools-bank-setup.cjs), [Takeover runner](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/scripts/obsidian-frontmatter-takeover-e2e.cjs)

Acceptance should cover these distinct risks:

1. **Defaults and independence:** healthy bank folded; album open; `_` and pointer agree; `-`, `+`, and `==` retain their jobs; malformed or missing configuration teaches clearly without trapping the fold open.
2. **Keyboard boundaries:** normal/insert/replace/visual/Source/non-Vim states, counts, operators, register prefixes, `f_`, text controls, search, modal focus, IME, repeat, non-US character events, and unloaded/missing mounts. Include the existing image-zoom modal's `-`/`_` behavior as an isolation check.
3. **Ownership and recovery:** mounted card and complete foot; no hidden native tab stops; Add file property routes correctly; Source/sidebar/ordinary notes stay accessible; invalid YAML, stale metadata, capability/path changes, failed mount, file switch, and plugin disable restore the expected native surface.
4. **State and lifecycle:** metadata/report refresh, specialized-editor save, view mode switch, same-note split, different-note split, album rename, detach/reattach, and stale async callback. Confirm explicit overrides survive routine refresh and reset only at the documented session boundary.
5. **Attention:** folded warnings, configuration errors, cached-data notices, failed reads, account staleness/delta, missing reports, empty schemas, hidden categories, and many rules. Missing data never masquerades as zero or healthy.
6. **Visual/accessibility:** light and dark themes; narrow split inside a wide app window; 375px and wide card widths; keyboard focus ring; disclosure names/states; unique control IDs; hidden-body focus exclusion; reduced motion; no horizontal scroll; stable reading position.
7. **Passive rendering:** compare disposable fixture bytes/HEAD and process invocation logs before and after repeated folds and refreshes. No writes and no new paint-triggered Bob subprocesses.

Run relevant offline tests and the repository's required build/docs checks, then the existing real Obsidian takeover workflow extended for bank. Review actual screenshots in both modes rather than treating mock DOM tests as proof of native focus behavior. Existing validation documentation expressly distinguishes the offline wrapper from real-app acceptance. [Validation workflow](https://github.com/bobs-org/bob-plugins/blob/eac9d7448d056e60af1e0f4224554c6ca1ed28d2/docs/develop/validation.md)

**Explicit requirement refinements.** Healthy bank starts collapsed, but initial missing/invalid setup may start open; explicit user state always wins. `_` is a guarded Live Preview Vim shortcut with a command and button available in Reading. Native Properties hide only while the shared safety gate holds, with recovery surfaces preserved. Errors and freshness remain visible outside the fold. Bank's visible section remains “Setup,” while album remains “Schema.” Fold state stays session-local, shared by note, and never becomes vault data. Title ownership is a separate future visual decision. These refinements make the requested interaction reliable without expanding it into a broader bank redesign.

**Recommended solution.** Implement bank's whole-frontmatter ownership through the existing property-card coordinator, retain its current placement and complete foot, make healthy bank setup collapsed initially, and add one shared, guarded `_` schema action for bank and album. Preserve album's expanded default. Ship the compact summary, persistent attention line, unique disclosure IDs, focus preservation, and native fallback tests as part of the same feature. That combination meets the user's intent and improves daily visual calm without sacrificing discoverability, editability, or recovery.

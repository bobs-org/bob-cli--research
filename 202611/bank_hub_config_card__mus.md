# Making the `bank` frontmatter field readable and writable from Obsidian

Research by `research.4r.mus` (independent swarm member; report suffix `__mus`).
Date: 2026-11-15.

## Question asked

Make the `bank` frontmatter field of `~/bob/bank.md` much easier to read and write
from Obsidian. It doesn't render in Obsidian at all at the moment. Use what was done
for the `record` field of album notes as context and inspiration. Lead the design:
intuitive, reliable, beautiful. Critique the plan, adjust requirements where
justified, end with a recommended solution.

## What I verified (evidence, not assumption)

### 1. What the `bank:` field actually is

`~/bob/bank.md` carries a nested mapping (`src/native/bank/config.rs`,
`BANK_KEYS = ["accounts", "categories", "rules", "stale_after"]`):

- `bank.accounts`: required, non-empty, ordered map. Alias `[a-z0-9_]*`; first
  account is the default. Each entry: `label` (optional), `kind` (required:
  `checking`/`savings`/`credit`/`cash`; `cash` is never imported), `start`
  (required `YYYY-MM-DD` except for `cash`).
- `bank.categories`: optional ordered map. Scalar `"<emoji> Label"` or mapping
  with `label` (required), `hotkey` (optional `[a-z0-9]`, `q` reserved),
  `group` (optional section name), `hidden` (optional bool, default false).
  Four built-ins always exist (`income`, `refund`, `transfer`, `cash`, in group
  `"Money moves"`); declaring one overrides its label/hotkey/group/hidden.
- `bank.rules`: optional list of `{match, payee?, cat?, link?}`; first match wins.
- `bank.stale_after`: optional days, default 10.

Hotkeys are assigned once in a fixed order: explicit hotkeys claimed first
(including hidden keys, so unhiding never reshuffles), then built-in defaults
unless taken, then derived keys in declared order. A visible category with no
free character reports `hotkey: null`. Full contract: `docs/bank.md` ("Bank hub"
section) and `src/native/bank/config.rs`.

### 2. Why it "doesn't render" — two stacked causes

- **Obsidian has no usable editor for mapping/object properties.** The
  Properties surface offers text/number/date/checkbox/list widgets; a nested
  mapping like `bank:` gets no editable widget. So even unhidden, the field is
  at best read-only raw text, never "easy to read/write."
- **The plugin deliberately hides it.** `bob-ledger-tools`'s stylesheet contains
  `.bob-bank-hub-note .metadata-property[data-property-key="bank"] {
  display: none !important; }`
  (`sase/repos/linked/bob-plugins/plugins/bob-ledger-tools/styles.css`, near the
  bank-marks block). The `bob-bank-hub-note` class is applied to hub leaves by
  `bankMarkSyncHubProperty()` in
  `plugins/bob-ledger-tools/src/241p-plugin-bank-marks.js`. Net effect: on a hub
  note the field is *hidden*, not merely uneditable. The user's report is exact.

### 3. The album `record` precedent — what "we did" actually consists of

The `record` property gets the identical hiding treatment, scoped to the album
surface (same stylesheet: `.bob-album-header-surface
.metadata-property[data-property-key="record"] { display: none !important; }`
with the comment "The record property stays editable in Source mode and remains
scoped to an album surface"). Hiding is only half the pattern; the other half is
a **report-backed replacement surface plus a guarded writer**:

- **Header renderer** (`241v-plugin-album-header.js`, model in
  `241u-plugin-album-header-model.js`): breadcrumb from resolved area/project
  ancestry, collapsed-by-default schema summary (field count, dated-notes,
  index grouping), one chip row per field in declaration order with
  kind/flag suffixes, required as quiet `*`, choice chips with usage counts,
  grouping annotations, muted `legacy` chips. Collapse state lives in pane view
  state keyed by album, never in frontmatter. Invalid schema paints the first
  diagnostic and expands to the lint list. Mobile renders the summary from
  last-good data with an edit-in-YAML hint; no write gestures on mobile.
- **Schema Card** (`241y-plugin-album-schema-card-dom.js`, session in
  `242b-plugin-album-update-session.js`, entry points in
  `242d-plugin-album-entrypoints.js`): keyboard-first editor in the Task Card
  idiom. Every gesture dry-runs through `bob albums update` first and Enter
  applies only the exact envelope whose dry run succeeded; stale fingerprints
  repaint instead of rebasing; Undo previews and applies the returned
  `inverse_ops` on a second Enter; saved-local post-sync failures offer Retry
  sync (vault-sync only, never replays the mutation).
- **CLI writer** (`src/native/albums/cli.rs::build_cli_update`,
  `src/native/albums/update/{protocol,ops,spans,plan,mod}.rs`): `bob albums update
  STEM [-b DIR] [-d] [-f human|json] [-i FILE]`. Typed JSON envelope
  (`schema_version: 1`, `expect` fingerprint `sha256:…` from `bob albums list`,
  ordered ops: nine v1 ops such as `album.set`, `field.add/set/move/remove`,
  `choice.add/set/move/remove`). Empty op list is a valid no-op; changed applies
  take the shared vault lock, pre-sync, replan fresh, rebuild the generated
  `[!records]` index in the same transaction, and make one scoped
  `albums: update <stem>.md` commit. Validation/semantic refusal exits 2;
  runtime/lock/transaction failures exit 1. Response carries before/after
  fingerprints, per-op results, derived keys, `inverse_ops`, commit, sync,
  warnings, nullable typed error. Full contract: `docs/records.md` ("update"
  section).
- **YAML excursion** (`242e-plugin-album-yaml-excursion.js`): `y` closes the card
  and focuses the exact field/issue line in Source mode; a Done button awaits
  editor save, forces a current report, and only returns/reopens the card when
  bob reports a valid schema. Invalid schemas stay on the diagnostic line.

Design rules the precedent establishes (all worth copying): painting never
rewrites note bytes; sync explicitly invokes bob's writer; frontmatter edits
use the shared three-second sync debounce; report labels are never link
targets; counts come from the versioned JSON report with cached-last-good
display plus Retry, never zero-on-failure.

### 4. What the bank side already has (and lacks)

- **Reads exist; writes don't.** `bob bank` ships `list`, `report`, `ensure`,
  `ack`, `import`, `check` (`src/native/bank/cli.rs`). There is **no
  config-writing subcommand**. Today Bryan hand-edits YAML in Source mode and
  `bob bank check` validates: every config error names file, 1-based line, and
  key path (e.g. `bank.md:5 bank.accounts.checking.kind: expected checking,
  savings, credit, or cash`), unknown keys inside `bank:` are errors with
  suggestions, and `check` exits 1 on any error (`docs/bank.md`, `check.rs`).
- **`bob bank list -f json` already returns resolved config.** `ListReport`
  carries `categories: Vec<Category>` (each with key/emoji/label/builtin/
  hotkey/group/hidden — `Category::to_json` in `config.rs`) and
  `accounts: Vec<AccountStatus>`, plus `issues` and per-day rows
  (`src/native/bank/list.rs::to_json`). A hub header can render
  accounts/categories **with zero CLI changes**. Gaps: `rules` and
  `stale_after` appear in no JSON report (`CheckReport::to_json` in
  `check.rs` has categories/accounts/issues/findings only). Full-config display
  needs either a small report extension or client-side frontmatter reads via
  `metadataCache` (the album header already resolves ancestry client-side, so
  there is precedent for the hybrid).
- **Bank UI precedent is guide-don't-write.** The Category card
  (`245/246/247/248-plugin-bank-category-card-*.js`) never writes rows itself:
  the filed category is Bryan's edit in his editor, applied through the same
  single editor transaction as the tick ("The Category card never writes rows
  itself… Bryan's edits always win" — `docs/bank.md`, Ownership). And the queue
  card (`241m-plugin-bank-cards.js`) renders `view: queue` fences with a
  "Bank hub" link back to `bank.md`. The hub note body already has a rendered
  card; only the *config* lacks one.
- **Plugin data service exists.** `241j-plugin-bank-data.js` caches
  `bob bank list|report` reads with subscribe/invalidate; a hub header would be
  a third consumer alongside marks and cards.

### 5. Edit frequency reality (scopes the investment)

Accounts change ~never (they encode real-world bank accounts with `start`
dates; history depends on them). Categories change occasionally (new spending
pattern, hotkey reshuffle, hiding). Rules change occasionally (new payee
pattern). `stale_after` changes ~never. This is a rarely-edited, high-stakes
config: a bad edit breaks import routing and hotkeys silently until the next
`check`. The design should optimize for **safe occasional edits with preview**,
not daily speed.

## Critique of the plan

**Yes, this is a good idea — with scoping.** The current state is the worst of
both worlds: the raw field is hidden (so not even readable) *and* there is no
replacement (so not writable either). Editing requires knowing Source mode,
YAML nesting, the hotkey-claim order, the `q` reservation, hidden-key
stickiness, and builtin-override semantics — all documented, none visible. A
report-backed header fixes readability at low risk; a guarded writer fixes
writability at moderate cost. Both follow a shipped, tested pattern rather than
inventing one.

Adjustments I would make to the request as stated:

1. **Keep the raw property hidden; do not "unhide and improve" it.** Obsidian
   cannot edit mappings in Properties, so unhiding only restores an ugly
   read-only blob. The album precedent (hide + replace) is the right shape.
2. **Split "read" from "write" into two phases.** Readability (header) needs no
   CLI change and is independently shippable. Writability (writer + card) is
   the expensive half. Do not gate the header on the writer.
3. **Do not move config out of frontmatter** (e.g. into the note body or a
   sidecar). Frontmatter is the contract `check`/`list`/`import` read, Dataview
   and Bases can see it, and `docs/bank.md` + `docs/reference/cli/bank.md` pin
   it. Relocating would churn the CLI contract for zero user-visible gain.
4. **Do not build a visual rule builder.** Rules are `{match, payee?, cat?,
   link?}` text rows with first-match-wins semantics and a digit-run masking
   subtlety at read time. A list UI with reorder + dry-run consequence is
   plenty; a graphical condition builder is over-engineering for a
   thrice-a-year edit.
5. **Hotkey preview is the killer feature, not emoji picking.** The genuinely
   hard-to-predict behavior is derived-hotkey assignment and collision
   (`hotkey: null` when no character is free; hidden keys stay claimed). The
   writer's dry run must show the *resulting* hotkey table, not just the ops.
6. **Respect the Category-card ownership principle.** The card proposes;
   explicit Enter disposes. No auto-apply on blur, no debounced writes — config
   edits are rarer and riskier than row ticks.

## Alternatives considered

| Option | Verdict |
|---|---|
| Hide + header + guarded writer (album mirror) | **Recommended.** Proven pattern, report-backed, Undo-able. |
| Header only, keep YAML hand-edits via `y` excursion | Good phase 1; insufficient alone — the ask is read *and* write. |
| Obsidian Bases view over `bank:` | Reject as primary: read-only, no guarded writes, no dry-run/inverse envelope. Fine as a complement later. |
| Flatten config into scalar frontmatter keys | Reject: breaks `check`/`list`/`import` contract, Dataview, and docs for no gain. |
| Visual rule builder with condition UI | Reject: overkill for list-of-text-rows semantics; list + reorder + preview suffices. |
| Body-embedded config card writing frontmatter | Reject: splits one config across two surfaces; frontmatter stays the source of truth. |

## Recommended solution (phased)

### Phase 1 — Bank hub header (plugin only, no CLI change)

On `bank.md` (detected by stem/path the way `bankIsHubPath` already does),
render a hub header above the queue card in Reading view and Live Preview,
consuming the cached `bob bank list -f json` report plus client-side
frontmatter for `rules`/`stale_after` (or a tiny `list`/`check` JSON extension
adding those two — prefer the extension; one code path beats a hybrid):

- Breadcrumb (`cash` parent), one account chip row (`label` + kind + `start`;
  marks the default/first), categories grouped by `group` with emoji+label,
  hotkey kbd chips (showing derived keys and `null` states distinctly), muted
  `hidden` chips, muted `builtin` chips; `stale_after` and rule count as a
  quiet meta row; expandable rule rows (`match` → cat/payee/link).
- Lint banner from `bob bank check` findings with file:line:key-path text and
  `y`-to-line excursion (reuse `242e` excursion mechanics verbatim).
- `＋ category`-style affordance is out of scope here; instead a hint row
  ("Edit in Source mode — `y` jumps to a line") until phase 2 lands.
- Same ground rules as the album header: paint never writes bytes; cached
  last-good report with Retry (never zero-on-failure); collapse in pane view
  state; mobile renders summary from last-good data with edit-in-YAML hint; no
  write gestures on mobile; Source mode stays fully editable.

### Phase 2 — Guarded writer + Config Card (CLI + plugin)

- **CLI:** `bob bank config update` (noun+verb nesting per `cli_rules.md`;
  bare `bob bank` keeps defaulting to read-only `list`). Mirror the
  `albums update` envelope exactly — same `schema_version` bump discipline,
  `expect` fingerprint over the *parsed config*, ordered ops
  (`account.add/set/remove`, `category.add/set/move/remove`,
  `rule.add/set/move/remove`, `config.set` for `stale_after`), `-d` dry run,
  `-i` envelope, `-f human|json`, exit 2 on validation/semantic refusal, 1 on
  runtime/lock/transaction failure, one scoped `bank: config update (…)` commit
  with pre/post sync, `inverse_ops` for Undo. The dry-run consequence **must
  include the resulting hotkey table** (explicit/builtin/derived/`null`) —
  that is the whole point. Semantic refusals to specify: removing/renaming an
  account with rows, removing a category/rules-cat still referenced by rows
  (warn, not refuse — rows keep `[cat::]` validity per contract), stealing a
  reserved/duplicate hotkey, unknown key suggestions (reuse config.rs key-path
  diagnostics as the refusal vocabulary).
- **Plugin:** Config Card in the Task Card/Schema Card idiom: keyboard-first,
  every gesture dry-runs first, Enter applies only the exact confirmed
  envelope, stale fingerprint repaints, Undo via `inverse_ops` + new `expect`,
  Retry-sync-only on post-sync failure. `y` jumps to the YAML line; Done
  validates-and-returns like the album excursion.
- **Docs:** update `docs/bank.md` (contract), `docs/reference/cli/bank.md`
  (generated CLI reference), and mkdocs nav if a page is added — read
  `sase/memory/docs.md` first (reference memory) before touching docs, per
  project convention.

### Explicit non-goals

No visual rule builder; no auto-apply/debounced config writes; no mobile write
gestures; no config relocation; no new hotkey-claim semantics (the claim order
is contract — the card *reveals* it, never changes it).

### Why this wins on the three axes

- **Intuitive:** one rendered surface replaces an invisible blob; groups,
  hotkeys, and hidden/builtin states are visible where Bryan already looks;
  `y`/Done keeps the Source-mode escape hatch one key away.
- **Reliable:** everything displayed comes from versioned JSON reports;
  everything written goes through fingerprint + dry-run + inverse-ops with a
  scoped commit. The rarest edits get the most guardrails.
- **Beautiful:** same chrome language as the album header (accent border,
  chip rows, collapsed summary, lint banner) — the hub note finally looks
  designed instead of redacted.

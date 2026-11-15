# Designing the Obsidian Read/Write Experience for `bank.md` (`bank:` Frontmatter)

**Recommendation at a glance:** Keep `bank:` inside `~/bob/bank.md` frontmatter as the single source of truth, replace the currently invisible property with a **collapsed-by-default hairline config strip (`bob-bank-config-surface`)** directly beneath frontmatter paired with a **keyboard-first `Bank Config Card` modal**, **contextual rule/category creation from `bank/YYYY-MM.md`**, a **flow-map-preserving `bob bank config` backend (`inspect` + guarded `update`)**, and a **`y` -> Source YAML -> `Done` excursion**. Do **not** clone the Album `record:` header banner 1:1 — `bank.md` already hosts the `bob-bank` queue card, derives built-in categories and hotkeys in Rust, carries high-blast-radius account keys/defaults, and relies on triage-time `rules:` workflows that albums do not have.

---

## 1. Current Reality Audit: Why `bank:` Doesn't Render Today

Opening `/home/bryan/bob/bank.md` in Obsidian Reading View or Live Preview shows `parent`, `type`, `summary`, and `created` in Properties, followed by `# 🏦 Bank`, a short usage paragraph, and the `bob-bank` (`view: queue`) card — while the entire `bank:` subtree appears **nowhere at all**. Two distinct layers cause this:

1. **Obsidian Properties cannot model nested schemas.**
   In `/home/bryan/bob/bank.md`, `bank:` is a 3–4 level nested YAML tree (`accounts` mapping of account objects, 21 `categories` flow mappings `{ label, hotkey, group }` / `{ label, hidden }`, optional ordered `rules` sequence of mappings, and `stale_after`). Just like `record:` on album notes (`album_record_schema_ux.md`), Obsidian's `/home/bryan/bob/.obsidian/types.json` has no property widget for nested mappings/lists of mappings; raw Obsidian renders an unusable `unknown` fallback and risks `[Object object]` or `processFrontMatter` structural loss.
2. **Existing `bob-ledger-tools` CSS already hides `bank` unconditionally without a replacement.**
   - `241p-plugin-bank-marks.js` (`bankMarkSyncHubProperty()`, lines 444–477) applies `.bob-bank-hub-note` to both `document.body` (when active) and markdown leaf containers whenever `bankIsHubPath(file.path)` matches `bank.md`.
   - `bob-ledger-tools/styles.css` line 9094 enforces:
     ```css
     .bob-bank-hub-note .metadata-property[data-property-key="bank"] { display: none !important; }
     ```
   - Unlike albums (`241u`–`242e`, where hiding `[data-property-key="record"]` under `.bob-album-header-surface` is paired with a collapsible summary strip, modal Schema Card, and YAML excursion), `bank.md` had its raw `bank` property hidden early during bank-marks work with **no replacement viewer or editor yet**. Today, Bryan can only inspect or edit `bank:` by toggling Source mode (`vimMode: true` in `/home/bryan/bob/.obsidian/app.json`).

### Baseline Contracts in `bob-cli` & Live Vault State

Inspecting `/home/bryan/bob/bank.md` and `src/native/bank/` establishes the domain constraints any UI/writer must respect:

- **Schema keys (`src/native/bank/config.rs`):**
  - `BANK_KEYS`: `accounts`, `categories`, `rules`, `stale_after` (`DEFAULT_STALE_AFTER = 10`, accepts non-negative integer days).
  - `ACCOUNT_KEYS`: `label`, `kind` (`checking`, `savings`, `credit`, `cash`), `start` (required except `cash`; `cash` is never importable). Alias must match `[a-z][a-z0-9_]*`. **Declaration order is semantic**: `accounts[0]` is the **default account** (`default: true` in `AccountStatus`) whenever `[acct:: ...]` is omitted on ledger rows.
  - `CATEGORY_KEYS`: `label` (parsed with `split_icon` into `emoji` + `label`), `hotkey`, `group`, `hidden`. Keys must match `[a-z][a-z0-9_]*`.
  - **Built-ins & hotkey derivation (`assign_hotkeys` / `derive_hotkey`):** Four built-in meanings (`income` 💵 `i`, `refund` ↩️ `r`, `transfer` ↔️ `t`, `cash` 🏧 `a`, grouped under `Money moves` unless overridden) exist even if absent from `bank.md`. Hotkey resolution runs in three passes: (1) explicit hotkeys (claimed *even when `hidden: true`*), (2) visible built-in defaults (`i`/`r`/`t`/`a`), (3) deterministic scan over `[a-z0-9]` excluding reserved `q` (`RESERVED_HOTKEY`) from key characters -> label ASCII letters -> digits `1..9, 0`. Numeric hotkeys (`"1"`–`"8"` in `~/bob/bank.md`) work cleanly when quoted as YAML strings (`parse_hotkey_value` also tolerates unquoted `0..=9`, though quoting prevents integer drift in YAML tools).
  - `RULE_KEYS`: `match` (non-empty case-insensitive substring), `payee`, `cat`, `link`. Ordered list (`config.rules` in `suggest.rs`: **first match wins**). Because journal entries run `mask_digits` (`identity.rs`, replacing runs of >=4 ASCII digits with `••••`), `rule_category` skips any rule with `has_long_digit_run(&rule.match_text)` during read-time suggestions (`import_run` still sees unmasked bank text!).
- **Journal & ledger coupling (`identity.rs`, `check.rs`):**
  - `transaction_key(alias, bank_id)` hashes `sha256(alias + "\n" + bank_id)`. Changing an account `alias` disconnects every journaled deduplication/balance proof entry in `.bob/bank/*.jsonl` and invalidates `[acct:: alias]` in `bank/YYYY-MM.md` (`bank_account_unknown` error).
  - Removing a category referenced by `[cat:: key]` produces `bank_category_unknown` errors in `bob bank check`. Notice Bryan's live `bank.md` already uses soft-hiding (`kids: { label: 🧸 Kids, hidden: true }`) rather than deletion.
- **Line mapping gap (`bank_line_map` in `config.rs:1009-1046`):**
  - `bank_line_map` cleanly tracks block entries and single-line flow mappings (`line.contains('{')`, e.g., `bank.categories.coffee`), so flow-mapped categories already have exact line numbers.
  - However, line 1015 skips lines starting with `-` (`if trimmed.is_empty() || trimmed.starts_with(['#', '-']) { continue; }`), so `bank.rules.<i>` entries do **not** get per-rule line numbers; diagnostics under `parse_rules` (`line_by_path.get("bank.rules.0.match")`) fall back to `None` or `bank.rules`.
- **JSON output gap (`check.rs`, `list.rs`, `report.rs`):**
  - Currently `bob bank list -f json`, `report -f json`, and `check -f json` emit resolved `categories[]` and `accounts[]`, **never** `rules[]`, `stale_after`, authored-vs-builtin category provenance, hotkey derivation provenance (`explicit` vs `builtin` vs `derived`), category/account usage counts across `bank/*.md`, raw-vs-normalized representation, config line numbers, or a `config_fingerprint`.
- **Flow-YAML gap vs `albums/update/spans.rs`:**
  - `/home/bryan/bob/bank.md` formats all 21 categories as clean one-line flow mappings (`coffee: { label: ☕ Coffee, hotkey: c, group: Everyday }`).
  - `src/native/albums/update/spans.rs` (`patch_entry`, lines 941–996) intentionally normalizes edited flow mappings into multi-line block YAML (`// Ensure the old flow value does not leak into the new block`). Reusing `spans.rs` blindly would turn a single hotkey tweak on one category into multi-line block expansion — or force 21 categories from 21 compact lines into ~85 lines if rewritten.

---

## 2. Critique of the Plan & Justified Adjustments to Requirements

### Should `bank:` Stay in `bank.md` Frontmatter, and Is Following Album `record:` a Good Idea?

| Candidate Backing / UI Approach | Verdict | Tradeoff & Rationale |
|---|---|---|
| **Flatten or configure Obsidian Properties (`types.json` / Metadata Menu)** | **Reject** | Impossible without destroying `bank:`'s nested ergonomics (`accounts`, `categories`, ordered `rules`), invites `[Object object]` / unquoted `"1"` corruption, and splits validation away from Rust `bob`. |
| **Move `bank:` out of `bank.md` into `.bob/bank.toml` / separate note / `data.json`** | **Reject** | Fragmentation cost. `bank.md` frontmatter is already human-readable, vault-git-synced with `bank/YYYY-MM.md`, covered by `docs/bank.md`, and parsed cleanly by `config.rs`. |
| **Replace frontmatter with a body ` ```yaml ` or ` ```bank-config ` block** | **Reject** | Pollutes `bank.md` prose & Reading View with 30–100 lines of configuration and breaks the established vault convention (frontmatter holds schema/config; body holds `# Heading`, prose, and live dashboard fences). |
| **Keep `bank:` in `bank.md` frontmatter + clone Album's `record:` pattern verbatim** | **Partly Good / Needs Adaptation** | Keeping frontmatter + Rust-owned `inspect`/`update` JSON contract + hidden property + modal `bob-key-card` + YAML excursion is **strongly validated**. Copying Album's top-header placement, raw-field mindset, and flow-destroying span editor verbatim is **not** optimal for `bank.md`. |

**Overall Critique:** The core instinct — *hide the unreadable raw `bank` property row and render/edit it through a dedicated `bob`-owned Obsidian UX modeled after album `record:`* — is **fundamentally sound**. Keeping config in `bank.md` frontmatter while giving Obsidian a structured read surface + modal transaction editor preserves single-authority Rust validation (`config.rs` / `check.rs`) and full Vim/git transparency.

However, treating `bank:` as *"just another `record:`"* misses four critical differences in how Bryan actually uses Money/Bank notes versus Albums. **The requirements should be adjusted in four explicit ways:**

### Four Justified Requirement Adjustments

1. **Adjustment 1 — Replace Double-Chrome with a Slim Properties-Replacement Config Bar (Not an Album Banner).**
   - *Album context:* An album note has no built-in live status card for its fields, so `bob-album-header` (`241v`) injects a full tinted banner containing breadcrumbs, `Copy`/`Schema` buttons, and a collapsible field chip view.
   - *Why `bank.md` differs:* `bank.md` is a **singleton** (`parent: "[[cash]]"`, `type: "[[area]]"`) whose body **already** embeds ```` ```bob-bank\nview: queue\n``` ```` (`241m-plugin-bank-cards.js`), which renders `Accounts` status (`WF Checking · balanced`, `Last import ...`), the waiting queue, and `Recent months`. Stacking an album-sized banner above `# 🏦 Bank` creates ugly double-chrome and risks duplicating `Accounts` state.
   - *Adjustment:* Make the `bank.md` read surface a **compact, single-line hairline disclosure strip** anchored immediately after frontmatter (above `# 🏦 Bank`, visually finishing the Properties block where `bank:` was hidden!), showing only **configuration** facts (`Accounts · Categories · Rules · Stale threshold`) plus `Configure` and `YAML` pills — expanding cleanly on click into a structured read-only inspector. Additionally, gate `.metadata-property[data-property-key="bank"] { display: none }` behind **`.bob-bank-config-surface`** (only active when the replacement strip mounts), fixing today's trap where `241p` hides `bank` unconditionally even though nothing replaces it.

2. **Adjustment 2 — Display Derived & Operational Semantics, Not Merely Raw Frontmatter Keys.**
   - *Why `bank` differs from `record`:* Album `fields` & `options` are 1:1 with authored YAML. Bank configuration has critical **computed behavior** in `src/native/bank/config.rs` and `suggest.rs`:
     - Four implicit `Money moves` built-in categories (`income`, `refund`, `transfer`, `cash`) participate in the `Category Card` even if omitted from `bank.md`.
     - Effective hotkeys (`derive_hotkey`) depend on declaration order, hidden flags (explicit hotkeys stay claimed even when `hidden: true`), built-in fallbacks (`i`/`r`/`t`/`a`), and conflicts.
     - `rules` uses **first-match-wins** order, and rules whose `match` contains **>= 4 consecutive digits** silently do **nothing at read time** (`has_long_digit_run` in `suggest.rs:306`, active at import time only).
   - *Adjustment:* Any read/edit view MUST show **both** authored values and Rust-computed consequences (effective hotkeys with explicit vs. auto-derived styling, inherited built-ins, rule precedence `#1..#N`, `Import-only (4+ digits)` warnings, and shadowed-rule warnings).

3. **Adjustment 3 — Support Contextual Triage-Time Rule & Category Entry from `bank/YYYY-MM.md`, Not Only on `bank.md`.**
   - *Why `bank` differs:* You configure `accounts` once a year, but you want a new **`rules:`** entry (`match: STARBUCKS` -> `payee: Starbucks`, `cat: coffee`) or a new/hidden category **in the middle of categorizing waiting rows** in `bank/2026-11.md` or the `Category Card` (`Ctrl+Enter` / `b` walk). Having to navigate away from the month ledger to `bank.md`, edit YAML, and return breaks flow.
   - *Adjustment:* Expose `Bank Config Card` both on `bank.md` **and contextually** from `BankCategoryCardModal` (a `+ Rule` action pre-seeded from the current row's merchant description and chosen category) and via Command Mode (`bob-command-mode`) from anywhere under `bank/`.

4. **Adjustment 4 — Require Bank-Specific Guardrails, Rule Match Testing, and Flow-Map YAML Preservation.**
   - *Write safety differs from albums:*
     - Moving another account into `accounts[0]` silently reassigns every `[acct::]`-omitted ledger row in the vault!
     - Renaming or removing an account alias breaks `.bob/bank/*.jsonl` `transaction_key` hashes and `bank/YYYY-MM.md` rows.
     - Deleting a used category produces `bank_category_unknown` errors, whereas `hidden: true` retires it cleanly.
     - Editing one category in Bryan's flow-formatted `bank.md` (`coffee: { label: ☕ Coffee, hotkey: c, group: Everyday }`) through album `spans.rs` as-is would unwrap it into multi-line block YAML.
   - *Adjustment:* The `bob bank` config writer MUST: (a) preserve single-line flow-mapping format for `categories` entries that fit cleanly, always quoting `"0"`–`"9"` hotkeys; (b) protect `accounts[0]` default changes and lock aliases that have journal/ledger usage; (c) steer used category removal toward `hidden: true`; and (d) include an in-modal **Live Rule Match Tester** previewing which waiting/recent transactions a drafted rule would match before saving.

---

## 3. Evaluating Design Alternatives

### Option A: Exact Album Mirror (Tinted Banner Above H1 + Schema Card + `spans.rs` Block Writer)
- **Pros:** Fastest conceptual reuse of `241u`–`242e`; immediately familiar actions (`▸ ...`, modal edit, `y` YAML excursion).
- **Cons:** Creates two stacked `magenta`-tinted boxes on `bank.md` (banner + `bob-bank` queue card); cloning `spans.rs` converts Bryan's compact 1-line category flow maps into verbose block YAML; lacks rules match testing and `bank/YYYY-MM.md` triage entry.

### Option B: Put Config UI Inside Existing ` ```bob-bank\nview: queue\n``` ` Card Only
- **Pros:** Zero extra containers on `bank.md`; all bank controls live inside one widget.
- **Cons:** Leaves a jarring UX gap at the top of `bank.md` where `bank` sits in Properties (nothing appears near `parent`/`type`/`summary`/`created`); if `bank:` YAML has a syntax error or someone scrolls the top Properties in Reading/LP, diagnostics aren't anchored near frontmatter (matching `bob-album-schema-summary.is-error` is far clearer when YAML fails).

### Option C (Recommended): Scoped Hairline Properties-Replacement Bar + Multi-Tab `Bank Config Card` + Triage Hooks + Guarded Flow-Preserving Backend
- **How it fits together:**
  1. **Properties slot replacement (`bank.md`):** Scoped `.bob-bank-config-surface` hides the raw `bank` property row cleanly when mounted (while Source mode keeps raw YAML untouched) and renders a slim **single-line collapsed disclosure bar** immediately beneath frontmatter (right above `# 🏦 Bank`).
  2. **Expanded Read Inspector (`bank.md`):** Clicking the bar reveals an airy, read-only visual specification of Accounts (`★ Default`), Categories (tiles grouped just like `Category Card`, distinguishing explicit vs. derived hotkeys and built-ins), Rules (`#1..#N` priority pipeline with `4+ digits` / shadowing badges), and `stale_after`.
  3. **Interactive Writer (`Bank Config Card` modal + contextual triggers):** Keyboard-first `bob-key-card` modal with 4 focused tabs (`Categories`, `Rules`, `Accounts`, `Settings`), live hotkey simulator, live Rule Match Tester, explicit consequence banner, `bob bank config update` dry-run -> atomic write, and `u` Undo (`inverse_ops`).
  4. **Expert Escape (`y` -> Source YAML + `Done`):** Line-accurate cursor jumps into `bank.md` (including per-rule lines after fixing `bank_line_map`) paired with the album-proven floating `Done` gate running `bob bank config inspect` / `check`.

### Option D (Minimum Viable Alternative): Read-Only Inline Inspector + `y` YAML Excursion Only (Defer Modal Editor)
- **Pros:** Ships rapidly with zero write-protocol surface in Rust; lets Vim power users (`vimMode: true`) read `bank:` effortlessly in Live Preview/Reading View and jump straight to the exact YAML line on `y` with validated `Done` save-check.
- **Cons:** Does not solve *"write from Obsidian"* without raw YAML syntax memorization (hotkey quoting `"1"`, flow syntax commas/braces, `rule` precedence guessing, accidental `accounts[0]` default changes, no live rule tester).
- **Insight:** Option D is actually **Slice 1** of Option C! Building Option C incrementally means Bryan gets full Read beauty + `y` validated YAML editing immediately in Slice 1, before writing a single line of YAML mutation code.

---

## 4. Detailed Design of the Recommended Solution (Option C)

### 4.1 Visual & Aesthetic Design ("Beautiful, Quiet, Native to Bob")

Using Bryan's existing bank tokens (`bob-ledger-tools/styles.css:8852-9094` — root area hue `magenta` inherited from `[[cash]]`, `tabular-nums`, `bob-bank-category-tile` / `bob-bank-category-keycap`, compact pill chips):

1. **Collapsed Bar (Default State on `bank.md`):**
   - Styled as a subtle, slim rounded strip (not a heavy `14%`-fill second card — e.g. `color-mix(in srgb, var(--bob-bank-accent) 5%, var(--background-secondary))` with a thin `2px` accent left border), anchored right below Properties / before `# 🏦 Bank`:
     ```text
     ▸ 🏦 bank   WF Checking (default) · 20 + 4 categories · 4 rules · 10d stale     [Configure]  [YAML]
     ```
   - **Error State (auto-surfaced, high-clarity):** If `bob bank config inspect` reports `issues.errors > 0` (e.g., bad YAML or duplicate hotkey), the bar switches to `--text-error` border/badge, shows exact count + top offending message (`2 errors · line 28: hotkey "c" claimed`), and promotes **`Fix in Config`** / **`Jump to line 28`**.
   - **Mobile posture (mirroring `docs/albums.md`):** Renders the read-only collapsed bar and expandable inspector cleanly on narrow screens (`flex-wrap`, responsive grid), omits `Configure` / write controls with a concise `"Edit in desktop or YAML"` note.

2. **Expanded Read-Only Inspector (Click Bar or `Enter` on Bar):**
   Crisp four-block card using `var(--font-interface)` + `tabular-nums`:
   - **Accounts Strip:** Compact pill per account in exact priority order:
     `★ checking · WF Checking (checking · since 2026-11-11)` — the `★ default` badge visually teaches why ordering matters (`[acct::]` defaults here), without duplicating balances/last-import from the `bob-bank` card below.
   - **Categories Matrix (Grouped Mirror of `Category Card`):**
     Renders `Everyday`, `Bills`, `Money moves (built-in)` side-by-side / flowing grid using mini `Category Card` keycap chips:
     - `[c] ☕ Coffee` — **solid keycap** for authored explicit hotkeys.
     - `[i] 💵 Income` — **muted/dashed keycap** for inherited built-in or auto-derived hotkeys, plus subtle `built-in` / `override` tooltip on hover so provenance is unmistakable.
     - `Hidden (1): 🧸 Kids` — tucked quietly on a muted footer line (with a subtle indicator if a hidden category still reserves an explicit hotkey!).
   - **Rules Pipeline (`First match wins`):**
     Numbered compact rows (`#1`, `#2`, ...) showing `[match]` `→` `payee` + `[cat:: chip]` + `[[link]]`. Inline badges highlight edge cases immediately:
     - Amber pill **`import-only · 4+ digits`** when `has_long_digit_run(match)` is true.
     - Muted pill **`shadowed by #1`** if an earlier rule's `match` is a case-insensitive substring of a later rule that could hijack matches.
     - Empty state (`~/bob/bank.md` today): quiet 1-line prompt: `"No import rules yet — add one in Configure or with ',' while categorizing a row."`
   - **Freshness Footer:** `stale_after: 10 days` (`"Accounts mark stale 10d after last import"`), plus `0 errors · 0 warnings` or inline findings clickable to jump (`y` / `line`).

### 4.2 Interactive Editing UX: `Bank Config Card` Modal

Follows `AlbumSchemaCardModal` (`bob-key-card` CSS + keyboard grammar: `j`/`k`/arrows move, `Enter`/`e` edits, `Esc` checks unsaved draft):

- **4 Section Tabs (`1` Categories · `2` Rules · `3` Accounts · `4` Settings, or `[` / `]` / Tab strip):**
  - **Categories Tab:**
    - Reorder (`Alt+J` / `Alt+K`), Add (`a`), Edit (`e`/`Enter`), Toggle Hidden (`h`), Remove Unused (`Ctrl+D`), YAML jump (`y` to `bank.categories.<key>`).
    - **Editor Form:** `Key` (auto-slugged `[a-z][a-z0-9_]*` on add; read-only on existing used keys), `Label` (supports `emoji + text`, live `split_icon` preview showing emoji badge + clean name), `Hotkey` (`auto` toggle or 1 key in `[a-z0-9] \ {q}`, with **live conflict & cascade preview** updating every category's computed keycap in real time!), `Group` (quick chips for existing groups like `Everyday`, `Bills`, `Money moves` + custom input), `Hidden` toggle.
    - **Safe Deletion UX:** Pressing `Ctrl+D` on a category referenced by `[cat:: key]` rows or `rules[].cat` cleanly refuses with consequence text: `"Used by N rows across M months and R rules. Press [h] to Hide from Category Card without breaking history."`
  - **Rules Tab:**
    - Reorder (`Alt+J` / `Alt+K` — live-updates `#1..#N` precedence!), Add (`a`), Edit (`e`), Duplicate/Refine (`d`), Delete (`Ctrl+D`), YAML jump (`y` to `bank.rules.<i>`).
    - **Live Rule Match Tester (Right/Bottom pane inside Rules Tab):**
      Whenever drafting/selecting a rule, dry-run evaluates `match` against: (a) current waiting rows from `bob bank list`, (b) recent ledger/journal rows (masked read-time simulation vs raw pattern check!), and (c) earlier rules. Shows exact feedback: e.g., `"Matches 3 waiting rows (-$6.45 PHILZ COFFEE ...) · Read-time + import active"` or warns `"Contains 4+ digits ('4821'): works on QFX/CSV import only, invisible to read-time suggest"` or `"Shadowed by Rule #1 ('STAR')"`!
  - **Accounts Tab:**
    - Shows `★ Default (index 0)`, `alias`, `label`, `kind`, `start` (hidden/optional when `cash`).
    - **Guardrails:**
      - Adding or editing `label`/`kind`/`start` works cleanly; editing `start` shows a live consequence if posted/journaled rows predate the new start date.
      - Moving an account into/out of `index 0` triggers an **explicit confirmation gate** displaying the exact count of `[acct::]`-omitted ledger rows whose account attribution would silently flip (`"42 rows in bank/2026-11.md omit [acct::] and will re-attribute from checking to savings"`).
      - Renaming/removing an `alias` is permitted only when zero ledger rows and zero `.bob/bank/*.jsonl` journal entries use it; otherwise refused with explanation pointing to journal hash (`sha256(alias + "\n" + bank_id)`) & ledger row coupling.
  - **Settings Tab:**
    - `stale_after` numeric stepper (`>= 0`, default `10`) with preview of each importable account's current age vs. threshold.

- **Commit Model (Matching `albums` Reliability):**
  - Staging changes locally refreshes the live **Consequence Banner** (`role="status"`) via debounced (`~250ms`) `bob bank config update -d -f json -i -` dry-run: lists exact effects (`"coffee: hotkey c -> k; income keeps i; 0 lint errors"`).
  - **`Save` (`Ctrl+Enter`)** flushes any open `bank.md` editor (`saveEditors` parity), submits `expect: config_fingerprint`, validates the resulting full bank scan cleanly, writes only the modified `bank:` spans atomically, triggers `git commit` parity if configured like `albums update`, suppresses file-watcher self-echo, and retains `inverse_ops` for **one-press `u` Undo**.

### 4.3 Contextual Triage-Time Entry Points & Escape Hatches

1. **Inside `BankCategoryCardModal` (`245` / `247`):**
   Add a quiet footer action (**`+ Rule` button**, optional non-colliding key trigger like `,` or `/`—not `[a-z0-9]` or `q`, which belong to category hotkeys!). Clicking opens `Bank Config Card` directly on **Rules -> Add**, pre-filled with cleaned `match` from the active transaction row's `payee` (and selected/highlighted `cat`). After saving, toast announces the saved rule and returns focus smoothly to the row walk in `bank/YYYY-MM.md`.
2. **Command Mode & Palette (`bob-command-mode/src/160-sheet-rank.js` + `bob-ledger-tools`):**
   Register command `edit-bank-config` (**"Bank: configure accounts, categories & rules"**) in `CM_SHEET_SURFACE_ROWS` under `"vault"` (alongside `"edit-album-schema"`), usable from `bank.md` or any `bank/YYYY-MM.md` note.
3. **`Ctrl+Shift+P` Fallback (`bob-navigation-hotkeys`):**
   On `bank.md` (when cursor is not on a task/link/dependency line, mirroring `551-plugin-album-schema-fallback.js`), open `Bank Config Card`.
4. **Source YAML Excursion (`y` -> `Done`):**
   Reuses `242e-plugin-album-yaml-excursion.js`'s exact leaf state machine: jumps to `bank.md` Source mode at the focused key's line (`bank_line_map`), pins a floating **`Done`** pill, saves + validates on exit, blocks with cursor jump to line diagnostic on error, and restores prior view / reopens card on success.

---

## 5. `bob-cli` Backend Architecture & `cli_rules.md` Alignment

Per `sase/memory/cli_rules.md`, subcommands under `bob bank` stay alphabetical in help, every public long option gets a short alias, nested verbs follow stated noun membership, and read-only reports avoid mutation. Keep `bob bank list/report/check -f json` compact (daily-note `Bank Badge` polls shouldn't serialize config rules and full schema introspection every time) by adding a clean `config` subgroup (or sibling verbs matching `albums`):

### Proposed CLI Surface: `bob bank config <inspect | test-rule | update>`

1. **`bob bank config inspect [-b DIR] [-f json|human]`** (Read-only; default human prints a colored summary table of accounts, categories + hotkeys, rules, `stale_after`, and findings; `-f json` powers the plugin):
   - Emits:
     - `ok`, `schema_version: 1`, `hub_path: "bank.md"`, `config_fingerprint` (SHA-256 of canonical parsed `bank:` raw/normalized state — matches `expect` on `update`), `yaml_style` summary.
     - `accounts[]`: `{ alias, label, kind, default, start, line, omitted_row_count, explicit_row_count, journal_events }`.
     - `categories[]`: `{ key, emoji, label, raw_label, authored, builtin, override, group, authored_group, hotkey, explicit_hotkey, hotkey_source ("explicit"|"builtin"|"derived"|"none"), hidden, style ("flow"|"block"|"scalar"), line, row_count, rule_count }`.
     - `rules[]`: `{ index, match, payee, cat, link, line, import_only_masked, shadowed_by, live_matches_waiting }`.
     - `stale_after`: integer.
     - `issues`: `{ errors, warnings, findings: [{ code, severity, key_path, line, message, hint }] }`.
   - Fix `bank_line_map` in `src/native/bank/config.rs` so YAML list items (`- match: ...`) populate `bank.rules.<i>` and `bank.rules.<i>.<key>` lines accurately for error navigation and `y` jumps.

2. **`bob bank config test-rule [-b DIR] [-f json|human] -m PATTERN [-p PAYEE] [-c CAT] [-l LINK]`** (Optional lightweight endpoint, or folded into `update --dry-run`):
   - Runs `suggest.rs` / `import_run` case-folded substring + `has_long_digit_run` checks against all waiting rows and recent N ledger rows so the UI **Rule Tester** responds near-instantly as Bryan edits `match` without staging a write.

3. **`bob bank config update [-b DIR] [-d|--dry-run] [-f json|human] [-i|--input FILE]`** (Reuses `bob albums update` protocol grammar!):
   - Reads JSON v1 envelope on stdin (`-i -`): `{ schema_version: 1, expect: "<fingerprint>", ops: [...] }`.
   - Typed `ops` cleanly cover:
     - `add_category`, `update_category`, `reorder_categories`, `remove_category`
     - `add_rule`, `update_rule`, `reorder_rules`, `remove_rule`
     - `add_account`, `update_account`, `reorder_accounts` (with explicit `allow_default_change: true` opt-in if index 0 shifts and `omitted_row_count > 0`), `remove_account` (only when `journal_events == 0 && explicit_row_count == 0` unless safe)
     - `set_stale_after`
   - **Flow-preserving Span Writer (crucial improvement over `albums/update/spans.rs`):**
     - Preserve untouched keys, comments, blank lines, and non-`bank:` frontmatter byte-for-byte via line spans.
     - Preserve category YAML style when editing or adding under a flow-styled `categories:` map: emit single-line flow entries (`{ label: ☕ Coffee, hotkey: c, group: Everyday }`) when free of nested/multiline strings and `<= 96` chars (omitting default `hidden: false`, `group` when `None`, etc., and **always double-quoting single-digit hotkeys `"0"`..`"9"`**!). Fall back to multi-line block formatting automatically if a value contains YAML-special characters or long text.
   - Returns `{ ok, dry_run, applied, expect, next_fingerprint, diff_summary, consequences[], findings[], inverse_ops[] }`, with structured exit code `2` on stale `expect`, invalid input, or semantic guardrail refusal.

---

## 6. Recommended Phased Roadmap

1. **Slice 1 — Zero-Risk Visibility + Validated YAML Escape (High Immediate Value):**
   - Fix `bank_line_map` in `src/native/bank/config.rs` for `bank.rules.<i>` sequence lines.
   - Add read-only `bob bank config inspect -f json`.
   - Update `bob-ledger-tools`: scope `.metadata-property[data-property-key="bank"]` hiding under `.bob-bank-config-surface`, mount the slim collapsed disclosure bar + expandable read-only inspector on `bank.md`, add mobile-safe degradation, and wire **`y` -> YAML Excursion + floating `Done`** (`242e` pattern) against `bob bank config inspect` / `check`.
   - *Result:* `bank:` is immediately visible, readable, diagnostic-linked, and safely validated on save — with zero custom YAML-mutation risk.

2. **Slice 2 — Interactive `Bank Config Card` + Guarded `bob bank config update`:**
   - Implement `bob bank config update` (expect fingerprint, dry-run consequences, `inverse_ops` undo, account index-0 & alias lockouts, category in-use -> hide nudge, flow-map emitter + quoted numeric hotkeys) and `bob bank config test-rule`.
   - Build `Bank Config Card` modal (`Categories` with live hotkey cascade simulator, `Rules` with live match tester, `Accounts` with default guardrails, `Settings`), `Save` (`Ctrl+Enter`), and `u` Undo.

3. **Slice 3 — Triage-Time Velocity + Optional Migrations:**
   - Add `+ Rule` / `+ Category` entry inside `BankCategoryCardModal` (opening `Bank Config Card` pre-seeded from the active transaction row), register `edit-bank-config` in `bob-command-mode`, and add `Ctrl+Shift+P` fallback in `bob-navigation-hotkeys`.
   - Optionally add `rename_category_key` / `reassign_default_account` atomic vault-wide migration ops cleanly under `bob bank config update` if Bryan later wants lossless key renames across historical `bank/YYYY-MM.md` notes.

---

## 7. Open Decisions for Bryan

Before writing implementation specs, three UX preferences merit quick confirmation:

1. **Strip placement on `bank.md`:** Should the collapsed `🏦 bank` strip render **right below frontmatter (above `# 🏦 Bank`)** so it visually replaces the hidden `bank` property slot, or **below `# 🏦 Bank`** (matching where `bob-album-header` sits on album notes)? *(Recommendation: right below frontmatter, above `# 🏦 Bank`, so Properties stays visually contiguous and doesn't compete with the `bob-bank` card below.)*
2. **YAML formatting style on writes:** When the Card edits or adds a category in `bank.md`, should it **preserve compact one-line flow mappings** (`coffee: { label: ☕ Coffee, hotkey: c, group: Everyday }`, matching your current `~/bob/bank.md`) or normalize categories to indented block YAML like album `record:`? *(Recommendation: preserve compact one-line flow mappings.)*
3. **Triage-time rule trigger inside `BankCategoryCardModal`:** While classifying a waiting row, should creating a rule use a **subtle button + punctuation key** (e.g., `,` or `/`) inside the Category Card footer, or Command Mode only? *(Recommendation: clickable footer button + `,` shortcut so you can go straight from spotting a recurring payee to creating its rule without touching the mouse.)*

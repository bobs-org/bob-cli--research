# Pomodoro Themes: Research, Critique, and Recommended Design

Researcher: mus · 2026-10-24 · bob-cli single-turn research swarm

## Scope and sources

Question: how to implement first-class "pomodoro themes" (aka pomodoro names):
glossary term, history-aware completion everywhere, priority of today's entries,
global rename, disable, and deterministic colors in CLI, mac app, and Obsidian.

Read directly (this session): `src/native/capture_pomodoros.rs`
(scan, `canonicalize_pomodoro_name`, slug rules), `src/native/capture_complete/pomodoros.rs`
(candidate tiers, `PlanCreationHint`, `creates_pomodoro`), `src/native/capture_complete/model.rs`
(`PomodoroNameCandidate`), `src/native/capture_complete/render.rs` (human rows, badges),
`src/native/plan_budget/mod.rs` (`normalize_component`, `split_components`,
theme/link counting), `src/native/config/plan.rs` (plan-config defaults),
`src/native/pomodoro_homes/palette.rs` + `docs/pomodoro-homes.md` R8 (deterministic hue
slots), `docs/plan.md` (ledger/theme/Today contract), `docs/capture.md` and
`docs/reference/cli/capture-complete.md` (completion contexts),
`docs/reference/mac-capture/task-pickers.md` (thin-client picker contract),
`docs/today-marks.md` (display-only mark pattern), `docs/completion.md` (shell completion
is a different thing — not in scope), plus `sase memory read` for
`glossary:pomodoro`, `glossary:capture`, `cli_rules.md`, and `docs.md`.
Opened `bob-plugins` and `bob-mac-capture` via `/sase_repo` for the picker/CSS side.
Did not read sibling swarm reports.

Key vocabulary already established: a Pomodoro's **name** is the text after `—`
(em dash) on a ledger entry; a plan-budget **theme** is a distinct non-exempt
`+`-separated component across open entries (`BOB + DECKS` = two themes; `GTD` exempt
by default; unnamed-with-links counts as `(unnamed)`). `docs/plan.md` is authoritative;
Rust owns the meaning and `bob-ledger-tools` mirrors it.

## Current state (what exists today)

1. **Names live only in today's ledger.** `bob capture-pomodoros` scans today's daily
   note (`YYYY/YYYYMMDD.md`, `## Pomodoros` section) and returns open entries with
   `name`, `slug`, `pomodoro_ref`, `selectable`, `time_range`, `placeholder`.
   There is no vault-wide theme list, no history, no registry.
2. **Completion already tiers correctly for today.** `pomodoro_name` candidates:
   open named rows ranked by query, then `requires_name` (nameable) rows, then a
   single `creates_pomodoro` row for a novel valid name (with `plan_themes_after/cap`
   preview). `pomodoro_start_name` has a richer list: planned placeholders
   (`next_up`), create row, **Again** rows (completed-slug resurrection, most-recent
   first), name-it rows, running entry last. So "existing names sort above
   novel/create rows" is already the rule *within today* — the gap is only that
   **previously used but not-today-open** themes are invisible. Again-rows are the
   closest existing analog and prove the pattern works.
3. **Canonicalization is settled.** `canonicalize_pomodoro_name` (trim, collapse,
   ALL-CAPS) + `capture_language::selector_slug` + `is_pomodoro_name` charset
   (`A-Z 0-9 & ' ( ) + , . / -`, must start with letter/digit). Any history/rename/
   disable design must reuse these, not invent new normalization. Note the two
   related-but-different normalizers: `plan_budget::normalize_component`
   (lowercase, collapsed) for budget keys vs. display-canonical ALL-CAPS names.
4. **Single-entry rename exists.** `bob capture-pomodoro-name --pomodoro-ref REF
   --name NAME` renames one open entry in today's note (temp-file atomic rewrite,
   re-scan verification, dry-run). There is deliberately no vault-wide rename.
5. **Disable ≈ exempt, partially.** `plan.exempt` (default `[GTD]`) already removes
   components from theme/link budgets, but exempt entries still appear in completion
   and still count as Today/agenda rows. There is no "hidden from completion" concept.
6. **Deterministic colors exist and are shared.** `pomodoro_homes::palette::Hue`
   (8 slots, FNV-1a over lowercase stem % 8, light/dark hex + xterm-256) is used by
   `bob stats`, `bob capture-pomodoros --tasks` agenda dots, and the Obsidian/JS
   mirror. This is the obvious reuse target for theme colors.
7. **Thin-client constraint governs the mac app.**
   `decisions:mac-capture-is-a-thin-client` — the app renders what bob returns and
   submits one `bob capture` call. Any theme feature (history rows, hues, badges,
   disable) must be computed in bob's JSON; the app only styles rows. Same for the
   Obsidian `pomodoro_name` pickers (block-id-prompt plugin), which already consume
   `creates_pomodoro` / `requires_name` / `plan_themes_after` rows.

## Proposal-by-proposal analysis

### 1. Glossary term — yes, and define it against the two existing words

Add **`glossary:pomodoro-theme`** (aliases: theme, pomodoro name). Proposed definition:
a theme is one `+`-separated component of a Pomodoro session name — the plan-budget
unit — while "Pomodoro name" stays the full `— NAME` string on one ledger entry.
The definition must state: components compare case-insensitively after whitespace
collapse; `plan.exempt` components are never themes; `(unnamed)` counts only with
links; closed entries are history, not themes. Without this note every later
discussion will confuse "rename the session" with "rename the theme" (different blast
radius when a session is composite like `BOB + DECKS`).

### 2. Suggest previously used themes in completion — yes; derive from scan, not a registry (v1)

Two possible history sources:

- **(a) Bounded daily-note scan** (recommended): walk `YYYY/YYYYMMDD.md` files,
  parse `## Pomodoros` sections with the existing `capture_pomodoros::scan`,
  collect components with `{last_used, uses}`. Bounded by recency (e.g. last 90 days)
  and file count; skips unreadable days with a warning, mirroring existing
  "missing daily note → empty + warning" behavior.
- **(b) Curated registry file** (e.g. `themes:` in config or a state file): cheap to
  read and a natural home for rename/disable, but it is a second source of truth that
  drifts (hand-edited dailies bypass it) and needs its own sync/gc story.

Recommend (a) for v1: always fresh, no migration, no drift. Cost is a vault scan per
completion call — mitigate with a small mtime-keyed cache or by piggybacking the
existing `bob stats` index if one becomes available; completion already does vault
reads elsewhere (route/task contexts), so this is precedented. Keep the door open for
(b) later as an *override layer only* (aliases, pinned order, disabled set), never as
the history source.

Ranking (extends the existing tiers, preserving "today first"):
`open exact/prefix > open substring > history (recency × frequency) > create row`,
with `requires_name` rows staying where they are today (after named rows). History
rows need additive JSON: `source: "history"`, `last_used`, `uses`, and reuse
`creates_pomodoro: false` + a real `replacement` slug so old clients keep working.
Accepting a history row behaves like create (canonicalize marker; `bob capture`
creates the placeholder) but must **not** set `creates_pomodoro` (mac app treats
that as the "New future Pomodoro" action with different announcements). Empty query
shows today's list as today (history only narrows on typing, or appears under a
"Previously used" header — see §7 on headers).

The same merged list must feed all four surfaces: `pomodoro_name`,
`pomodoro_start_name` (history slots between create and Again rows — or merged with
Again rows, since Again *is* recency history for completed slugs; deduplicate by slug),
Obsidian pickers, and the mac panel. Because of the thin-client rule, the merge
happens in `capture_complete`, once.

### 3. Prioritize today's matches — already true; just don't regress it

`insert_pomodoro_creation_candidate` already inserts the create row after all
prefix matches. The requirement is therefore a regression constraint plus one
extension: history rows also sort below every open-entry match regardless of query
(unless the query filters the open rows out entirely — then history may top the
remainder). Encode this as a test, not just prose: the existing
`capture_complete/tests/pomodoros.rs` tier tests are the template.

### 4. Global rename — yes, but as a new top-level command with history-rewrite warnings

`bob capture-pomodoro-name` renames one entry; global rename is a different blast
radius (every `YYYY/YYYYMMDD.md` containing the component, including closed entries,
which changes past `bob stats` attribution). Design:

- New group `bob themes rename OLD NEW` (not under `bob capture-*`: the `capture-*`
  protocol names are frozen siblings per `cli_rules.md`, and `bob task <verb>` is
  reserved for task-line rewrites — themes are ledger-entry tails, so a top-level
  `bob themes` group fits the noun-membership rule).
- Canonicalize both sides with the existing functions; `OLD` must resolve to exactly
  one normalized component (else fail, listing near-matches).
- Rewrite ` — OLD` tails **per component**: `BOB + DECKS` → `BOB + NEW` when renaming
  `DECKS`. Never touch time ranges, checkboxes, child bullets, or prose that merely
  mentions the word (match only the em-dash name tail / `+` components).
- Per-file atomic temp-rename + re-scan, whole-batch dry-run first, `--dry-run`,
  `--include-closed` defaulting to all-files with an explicit warning that stats
  history changes (or default to open-only + flag; either way, say it loudly).
- Refuse when rename would create today's `duplicate_open_pomodoro_name` lint.
- JSON reports per-file `{path, replacements}` + `warnings`.

### 5. Disable — config-gated, not a picker keymap (v1)

Where disable could live: (i) extend `plan.exempt`, (ii) new `plan.disabled_themes`
(or `themes.disabled`) list, (iii) delete-from-history. Recommend (ii): `exempt`
means "not a theme for budgeting but still completable/Today-eligible" (GTD must keep
working sessions), while disabled must mean "**invisible in completion everywhere**."
Conflating them breaks GTD flows; keep both knobs. Disabled components: excluded from
`capture_complete` rows (both contexts), from `capture-pomodoros` discovery lists,
and from theme budgets; a typed exact disabled name returns the normal create row
with a `disabled` warning rather than silently resurrecting it. Enable/disable via
`bob themes disable NAME` / `bob themes enable NAME` rewriting the config list
(plus manual config edit, same as other `plan:` keys).

On `<ctrl+d>`: **do not** take it for v1. Evidence against: `Ctrl+D` already means
"delete property / clear relations" in the Task Card, "scroll preview" in mac refs,
and chip-× in several pickers — overloading it with "globally disable this theme"
(a destructive, vault-config write from a read-only picker, needing confirmation and
undo) is the riskiest possible first step. Pickers select; they don't govern. If a
keymap is ever added, make it an explicit two-step (action → confirm notice), only in
surfaces whose picker owns the config write, and never in the mac thin client (which
would need a new bob command anyway — so just ship the command first and let usage
tell you whether a shortcut is warranted).

### 6. Deterministic colors — reuse the area-hue palette, expose additively, differentiate glyphs

Map theme component → `Hue` with the existing `fallback_hue(normalized_component)`
(FNV-1a, lowercase). This gives CLI xterm dots, mac swatches, and Obsidian CSS the
same answer with zero new algorithms, and the JS mirror already implements it. Ship as:

- Additive JSON: `hue` (+ optional `color`) on `PomodoroNameCandidate`,
  `capture-pomodoros` entries, `plan.theme_names` entries, and stats theme parts.
- CLI: paint the existing `●`/`○` agenda dot in the theme hue (Styler already has
  `xterm256`/`metric_hue`).
- Obsidian: one CSS snippet keyed off a `data-theme-hue` attribute using the 8
  light/dark pairs from the R8 table; display-only (same pattern as `today-marks`).
- Mac: hue-name → color swatch on history/create rows.

Two cautions: (a) **collisions are semantic, not just visual** — theme hues share 8
slots with area hues, so a theme dot next to a home dot can imply a relationship
that doesn't exist. Differentiate glyphs: keep `●` for homes, use a pill/chip with
the theme name (or a different shape) for themes, and never rely on color alone
(mac VoiceOver + Increase Contrast precedent). (b) Explicit per-theme custom colors:
defer. The 8-slot palette plus FNV fallback already handles custom `color:` for
areas with collision lints; per-theme overrides can follow the same pattern later if
Bryan actually wants them. No user-picked colors in v1.

## Critique: is this a good idea?

Yes — with scoping adjustments. The core insight is right: pomodoro names are
currently write-mostly (typed, then forgotten), and completion that only knows
*today* forces retyping and breeds near-duplicate themes (`DEEP WORK` vs `DEEPWORK`
vs `DEEP-WORK`), which then pollutes plan budgets and stats. History-aware completion
plus rename is the highest-value pair: it converts the theme namespace from
append-only chaos into something convergent. Deterministic colors are cheap given the
palette exists and genuinely help scanning a day with 3+ themes — "last but not
least beautiful" is achievable without custom art.

Adjustments I would make to the requirements as stated:

1. **Don't build a theme registry/store in v1.** Derive history from the daily-note
   scan; add config only for `disabled_themes` (+ optional pinned aliases later).
   A registry is a sync burden with no v1 consumer that needs it.
2. **Don't put destructive actions in completion pickers.** No `<ctrl+d>`-to-disable
   in v1; ship `bob themes disable/enable` + config. Revisit only with usage evidence.
3. **Rename defaults matter more than rename mechanics.** Decide and document whether
   closed-session history is rewritten (my recommendation: yes, default all files,
   loud warning, `--dry-run` first — because stats attribution reads closed
   sessions, a half-rename leaves history and future permanently disagreeing).
4. **Treat Obsidian + mac as rendering-only.** All ranking, hue, and disabled logic
   lands in bob JSON; clients get contract tests, not reimplementations. This is
   already the project's rule (plan.md authority, thin-client decision) — the plan
   should say so explicitly so nobody "fixes" ranking client-side.
5. **Phase colors last.** They depend on the history/rename semantics being stable
   (hue is keyed on the normalized component — renames change hues, which is correct
   but must be communicated).

## Recommended solution (phased)

- **Phase 0 — glossary + contract.** Land `glossary:pomodoro-theme` and a short
  `docs/` contract (or `plan.md` addendum): name vs. theme vs. component, exempt vs.
  disabled, hue-key rule, ranking tiers. Everything else cites it.
- **Phase 1 — history-aware completion.** Bounded daily-note history scan;
  merged tiers (open > history > create); additive `source/last_used/uses/hue`
  fields; all four surfaces; tier regression tests. Highest value, lowest risk.
- **Phase 2 — `bob themes` group: `list`, `rename`, `disable/enable`.**
  `list` exposes the history scan (`--json` with uses/last_used/hue) so rename and
  disable have a visible inventory; rename is component-aware with dry-run and
  closed-history warnings; disable is a config list honored by completion + budget.
- **Phase 3 — colors everywhere.** Paint CLI dots, ship the Obsidian snippet, add
  mac swatches from the hue names already in JSON. Distinct theme glyph (pill/chip),
  never color-alone.
- **Explicitly out of v1:** theme registry file, per-theme custom colors, picker
  disable keymaps, shell-completion changes (unrelated system).

## Open questions for Bryan

1. Rename blast radius: rewrite closed history too (recommended), or only open/future
   entries? The former keeps stats consistent; the latter preserves history at the
   cost of a permanently split theme.
2. Is `exempt` (GTD-style, still completable) vs. `disabled` (hidden from completion)
   the right two-knob split, or should disabled themes also drop out of Today/agenda?
   (I recommend they stay Today-eligible when already logged — disable governs
   *future* selection, not *past* truth.)
3. Any objection to reusing the 8 area-hue slots for themes (with distinct glyphs),
   versus a separate theme palette?

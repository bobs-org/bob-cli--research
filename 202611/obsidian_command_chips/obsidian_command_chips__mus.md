# Executable Notes: Obsidian Command Chips — Research Report (__mus)

Researcher: `mus` (independent strand of a 5-researcher swarm; peer reports not consulted).
Date: 2026-11-19. Checkout: `sase/repos/research` → file `202611/obsidian_command_chips__mus.md`.

## 1. TL;DR and recommended solution

**Yes, build it — but narrower than briefed, and do not rename the plugin.**

- **One plugin, same id.** Add command chips to the existing `bob-copy-chips`
  plugin (display name may become "Bob Chips"). Do **not** rename the plugin id
  to `bob-chips`: the id is the vault folder name, the `community-plugins.json`
  key, the `api` owner (`app.plugins.plugins["bob-copy-chips"]`), the vimrc
  target (`bob-copy-chips:copy-on-cursor-line`), and the `plugins.sync`
  allowlist entry. A rename breaks every desktop host's installed vault state
  for zero user-visible benefit — the id never appears in daily use.
- **Opt-in executable syntax, parallel to copy chips.** Inline code span
  `` `run: bob gcal ack -n 7` `` (plus `run[LABEL]:` labeled form) and a
  `bob-run` fence for multi-command sequences (one `bob …` per line).
  Plain `` `bob …` `` spans — of which the vault has dozens — must stay inert.
  This is the single most important safety decision in the design.
- **Thin client, twice over.** Chips never spawn processes. They parse the
  payload with shell-style quoting (no shell), validate against the versioned
  `bob __catalog` handshake, and execute exclusively through
  `api.commandMode.run` / `.preview` — the same engine the command sheet uses,
  with its write policies, save-before-write, one-writer-at-a-time, budgets,
  run receipts, and pager history. This mirrors the accepted
  `mac-capture-is-a-thin-client` posture: bob owns the contract, plugins render
  and submit.
- **Keymaps: keep the brief's split, but one owner per hotkey.**
  `Ctrl+Enter` already means "run now / apply" *inside the sheet* — chips reuse
  that meaning by routing through the engine, no new binding needed there.
  `Cmd+Enter` (`Meta+Enter`) in the editor is **already bound** to
  `bob-navigation-hotkeys:open-reference-pdf-in-highlights` (vault
  `hotkeys.json`). So the chips plugin must not bind it separately; nav-hotkeys
  gains a first-branch dispatch: runnable command chip on the line/task →
  run it, else existing behavior. Scope the editor gesture exactly like the
  brief: single command chip on the cursor line (cursor rule below), else fall
  back to the task behavior.
- **Bulk = fence-as-sequence.** One chip is one argv (no `&&`, no pipes, no
  shell — ever). A `bob-run` fence body is an ordered step list executed with
  the sheet's existing sequence semantics (in order, halt on failed/unknown/
  stopped, needs-attention continues). `Cmd+Enter` runs only the
  single-chip case; multi-chip lines/fences go through an explicit "run all"
  palette command or `Alt+Click → send to sheet`.
- **Policy is honored, not bypassed.** `Cmd+Enter` means *request*, not
  *force*: reads run at once; `preview-first` entries open the sheet at the
  preview stage; `confirm` entries show the confirm card. A chip never applies
  a write that the sheet would have gated.
- **Adopt in two GTD lines, not five.** `Ack external events`
  (`bob gcal ack -n 7`) is the clean pilot. The Bank line is blocked by its
  `&& rm …` tail (non-bob segment — must be split before it can become a
  chip). The three `periods show …` lines already live *inside* copy-chip
  prompt payloads and must stay copy chips; nested spans never parse as
  command chips.
- **Memory:** add one `glossary:command-chip` strand (draft in §8); no decision
  record needed unless the `run:`-prefix-mandatory rule is contested.

## 2. Is this a good idea? Critique of the brief

### 2.1 What is good about it

- **Real friction, real frequency.** The Morning-review and Ack lines fire
  daily/weekly; today they require copy-paste into a terminal or retyping into
  the sheet. A chip collapses that to one keystroke with identical engine
  semantics.
- **The brief already senses the right architecture.** Reusing the command-mode
  engine (rather than a second spawn path) and reusing the copy-chip cursor
  rule are both correct instincts, and the `Cmd+Enter` vs `Ctrl+Enter` split
  correctly avoids the editor's overloaded `Ctrl+Enter` (recurring-done, bank
  claim, decay rolls — all owned by nav-hotkeys).
- **Copy chips proved the pattern.** Grammar module + conformance vectors,
  never-throw frozen `api`, cursor rule shared by `gy` and the Copy card,
  quiet theme-native faces, byte-exact payloads. Command chips inherit all of
  it nearly verbatim (epic `bob-cli-ni`, closed 2026-11-19; strand
  `glossary:copy-chip`).

### 2.2 Risks and required adjustments

1. **Plain `bob …` spans must not become runnable.** Census: ~40 distinct
   `` `bob …` `` inline spans across the vault (bank import, vault-sync, ref
   create, periods draft/brief/show, stats, tick, …). If *any* `bob` span
   rendered a run button, every old note would sprout executables after
   upgrade — including spans inside copy-chip prompt payloads and docs.
   **Executability must be opt-in via the `run:` prefix.** This is a
   deliberate, documented restriction, not a parsing nicety.
2. **No shell, ever.** The Bank line's `&& rm ~/Downloads/*.qfx` tail is the
   exhibit: a chip payload is one argv, split with shell-style quoting but
   passed directly to `bob` with no shell (exactly the sheet's argv rule).
   `&&`, pipes, globs-for-shell, and non-`bob` segments are refused with a
   reason, never executed. The Bank line therefore cannot become a chip until
   the `rm` half is split out (or a future `bob bank import` flag absorbs it).
3. **`Cmd+Enter` is taken.** `hotkeys.json` binds `Meta+Enter` to
   nav-hotkeys' open-in-Highlights/link command, and ledger-tools paints a
   `Cmd+Enter opens this email in Gmail` hint on mail lines. There can be only
   one owner: nav-hotkeys dispatches first on "single runnable command chip,"
   else falls through. Do not register a second global `Meta+Enter`.
4. **Vault text is an attack surface.** Anyone (or any agent) with vault write
   can plant `` `run: …` `` text. Mitigations, all required: explicit prefix,
   catalog validation (excluded leaves refused — e.g. `task move`, free-text
   `capture` refused like the sheet refuses it), write-policy honored,
   desktop-only execution (command-mode is desktop-only; render everywhere,
   run gated), no shell, engine-owned receipts under host-local state (never
   the vault). State this threat model in the docs.
5. **Don't build a task runner.** No scheduling, no env vars, no stdin piping,
   no output-to-note insertion in v1. Output goes to the existing pager;
   history to the existing runs dir. Anything fancier reuses the sheet (send
   chip to sheet for arg editing/preview).

### 2.3 Would I take a different approach?

The credible alternative is **"chips as sheet bookmarks"**: clicking a chip
only ever opens the command sheet prefilled (never runs). It is safer and
simpler — but it saves exactly one keystroke over typing `:ack` in the sheet,
which fails the brief's convenience goal for daily GTD rows. The recommended
middle path (direct run for reads, sheet/confirm for writers) keeps the
one-keystroke win where it is safe and degrades to the sheet exactly where
the sheet itself would gate. A second alternative, a separate
`bob-command-chips` plugin, loses to shared grammar/cursor/author-card code
and doubles the sync/deploy matrix; the additive cost inside `bob-copy-chips`
is one grammar file, one resolver, and one `api` namespace.

## 3. Landscape: what exists today

- **Copy chips** (`bob-copy-chips` 0.4.0, `isDesktopOnly: false`): `copy:` /
  `copy[LABEL]:` spans + `bob-copy` fence card; click/`gy`/`Mod+Y C`/
  `Mod+Shift+Y` authoring card; `api.copyChips` v1 frozen, never-throwing,
  with `chipAt({lines, line, ch})` cursor rule (under-cursor wins → only chip
  on line → enclosing `bob-copy` fence → ambiguous → none). Docs:
  `docs/bob-copy-chips.md` in bob-plugins.
- **Command mode** (`bob-command-mode` 0.2.0, desktop-only): bottom sheet over
  `bob __catalog`; `Enter` run, `Tab` args, `Shift+Enter` preview,
  `Ctrl+Enter` run-now/apply; sequences via `Ctrl+M` marks (run in order,
  halt on failure, one review card, RECENT-folded, Copy joins with `&&`);
  `api.commandMode` v1 (`run`/`preview`/`openOutput`/`onRunFinished`/
  `catalog`/`lastRun`), never-rejecting, with `bob-command-mode:run-finished`
  workspace event. Guards: writers save editors first, run one at a time,
  excluded/catalog-missing refused. Run-bob guide:
  `docs/guides/run-bob-from-obsidian.md`.
- **Cursor-line hint precedent.** ledger-tools appends a `Cmd+Enter opens
  this email in Gmail` affordance at the cursor line end for mail notes
  (`142k-gmail-open-hint.js`); nav-hotkeys' Task Card and bank rows already
  teach `Ctrl+Enter` per-row semantics. Discoverability has an established
  pattern to copy.
- **Copy-card integration precedent.** The `Chip · <face>` C-row
  (`copyCardRow`, null unless ready/ambiguous) shows how a second plugin
  consumes `api.copyChips.chipAt` with feature detection (`version >= 1`).
  Command chips get the symmetric treatment: `api.commandChips`,
  `version 1`, same `chipAt` shape, `{ form: "inline" | "block" }`.
- **GTD candidates** (`~/bob/gtd_daily.md`): line 27 `bob gcal ack -n 7`
  (pilot); line 18 Bank `bob bank import … && rm …` (blocked — split first);
  lines 25–31 `periods show …` nested inside copy prompts (must stay copy);
  line 14 Morning review (no bob command — not a candidate).

## 4. Requirements (adjusted from the brief)

1. Authoring: `run:` / `run[LABEL]:` inline spans; `bob-run` fence (one
   command per non-blank, non-`#` line). Payload must begin with `bob `
   (stripped before parse) so the chip reads like the terminal.
2. Literal argv: shell-style quoting for splitting only; never a shell. No
   `&&`/`||`/`|`/`;`/redirects/glob-expansion inside a chip. Multi-step =
   fence lines or multiple chips, executed as a sequence.
3. Validation before render-or-run: argv must resolve to a catalog entry;
   `excluded` paths, free-text `capture`, and unknown leaves render dimmed
   with their refusal reason and never run. Writers show their policy badge
   (preview/confirm) in the tooltip.
4. Cursor rule (copy-chip mirror): chip under cursor → only chip on line →
   enclosing `bob-run` fence (block form; inline chips on the line win over
   the fence, and example spans inside fence bodies never resolve alone) →
   ≥2 chips with cursor on none is ambiguous (never guessed) → none.
   Fenced/code/frontmatter/comment/table contexts follow the copy-chip
   scoping; copy-chip payloads are never scanned for command chips.
5. Execution only via `api.commandMode` (feature-detected `version >= 1`);
   absent/disabled command-mode renders chips dimmed with "command mode
   unavailable". Desktop-only run; mobile renders inert with reason.
6. Policy honored: reads run; `preview-first` opens the sheet at preview;
   `confirm` shows the confirm card. `Cmd+Enter` is a request; the engine
   decides.
7. `Cmd+Enter` dispatch lives in nav-hotkeys (owner of `Meta+Enter`):
   runnable single command chip → run; else existing Highlights/link/gmail
   behavior. Plus palette command "Run command chip on cursor line" and
   vimrc-optional mapping; `Alt+Click` on a chip sends it to the sheet
   (mirror of copy chips' `Alt+Click` → author card).
8. Discoverability (§6): distinct run face (▶, accent-tinted hover), tooltip
   with keymap, cursor-line hint + status-bar item when runnable, docs +
   run-bob guide section.
9. Vault adoption: pilot `gcal ack` line; Bank line split first; periods
   lines untouched. Every adopted line keeps reading as plain inline code
   with the plugin off.
10. Memory + docs: new `glossary:command-chip` strand; plugin docs page
    section; run-bob guide subsection; no CLI changes (no `cli_rules`
    trigger), no decision record unless the prefix-mandate is contested.

## 5. Design

### 5.1 Syntax (normative, mirrors `copy:`)

- Inline: `` `run: bob gcal ack -n 7` ``, `` `run[Ack events]: bob gcal ack -n 7` ``.
  `run` is lowercase-first; label rules identical to copy chips (one line,
  `\]`/`\\` escapes, trimmed, blank = unlabeled). Text after `:` + one
  optional space is the payload verbatim; whitespace-only payloads are not
  chips. Longer backtick runs hold inner backticks; `\|` in tables.
- Fence: ` ```bob-run ` info string (optional label, same `[ ]` strip rule as
  `bob-copy`), body = one `bob …` command per line; blank lines skipped;
  `#` lines are comments. Renders as a titled sequence card (N steps, per-step
  policy dots) with one Run button; body folds after 8 lines like the copy
  fence card.
- Unlabeled face shows the command in monospace (it *is* the literal argv);
  labeled face shows the label in the text font. Print/PDF renders as inline
  code / plain body with no chrome, same as copy chips.

### 5.2 Rendering and beauty

- Quiet pill, same metrics as copy chips (hairline border, `.92em`, glyph
  slot so feedback never reflows), but visually distinct: **play glyph (▶)
  instead of copy glyph (⧉)**, and hover/focus in the accent rather than
  neutral — runnable must read as runnable at a glance, yet theme-native.
- States: ready (full chroma) · writer-awaits-policy (tiny `…`/shield dot +
  tooltip names preview/confirm) · invalid/excluded (dimmed, tooltip gives
  the catalog reason) · engine-off/mobile (dimmed, reason).
  Feedback mirrors copy chips: glyph swaps to spinner then green check,
  `--bob-yank-flash-bg` pulse, polite live-region "Ran …", exactly one
  `Notice` on failure with the engine's reason. Never a toast on success.
- Live Preview, Reading view, embeds, hover previews, Tasks query results —
  same surfaces as copy chips. Click on a ready read-chip runs it; click on
  a writer chip opens its preview/confirm (click never force-applies).
  Drags, secondary buttons, and releases outside never fire.

### 5.3 Execution path (reliability)

1. Resolve via `api.copyChips`-shaped `commandChips.chipAt` (new namespace,
   same frozen never-throw contract; multi-chip lines → `ambiguous`).
2. Split payload with the sheet's word-splitting (shared helper or vendored
   with conformance vectors), strip leading `bob`, resolve against
   `commandMode.catalog()`; refusal reasons reuse catalog `excluded[].reason`
   wording.
3. Call `commandMode.run(argv)` for reads, `commandMode.preview(argv)` for
   preview-first, and let confirm entries surface the engine's confirm card
   (same card the sheet shows — no second confirm UI).
4. Sequences (fence / run-all): order = author order; one at a time; halt on
   failed/unknown/stopped; needs-attention continues; one summary card with
   Output/Copy/Rerun/Resume-from-k — i.e. delegate to the sequence runner
   semantics, not a reimplementation.
5. All engine invariants come free: save-before-write, single writer,
   budgets, receipts, 50-runs/14-days retention, toasts, pager, status chip,
   `run-finished` event (stats journals keep working).

### 5.4 Keymaps and discoverability

- Sheet: unchanged (`Ctrl+Enter` = run now / apply). Chips route *through*
  it, so the brief's "just like Ctrl+Enter in the panel" holds by
  construction.
- Editor `Cmd+Enter`: nav-hotkeys first-branch on runnable single chip (see
  §4.7), else fall through. Palette: "Run command chip on cursor line"
  (no default hotkey; user-bindable) + "Run all command chips on task".
  `Alt+Click` = send to sheet (preview/edit args).
- "Make it clear when available": three layers — (a) chip face + tooltip
  (`▶ Ack events · ⌘↵ to run · preview-first`); (b) cursor-line affordance
  reusing the gmail-hint pattern (appended end-of-line hint + status-bar
  `▶ run: <label> (⌘↵)` only while the cursor is on a runnable line);
  (c) docs + one GTD pilot line the user touches daily. No modal banners,
  no always-on gutter icons.

## 6. Alternatives considered

- **Any `bob` span runnable.** Rejected: retroactively weaponizes ~40 vault
  spans and all docs; no opt-in boundary.
- **`bob:` prefix instead of `run:`.** Reads nicely (`` `bob: gcal ack` ``)
  but collides conceptually with the plain spans we must keep inert, and a
  bare `bob` prefix invites "why doesn't my `bob x` span run?" support load.
  `run:` states the verb; keep it.
- **Shell chains in one chip (`&&`).** Rejected: breaks the sheet's no-shell
  invariant, the `rm` half has no catalog entry to validate, and failure
  attribution across segments is undefined. Fence-per-line sequences cover
  the need.
- **Separate plugin / renamed `bob-chips` id.** Rejected in §1: id rename =
  multi-host reinstall + allowlist/api/vimrc churn for an invisible string.
  (Renaming only the human-readable `name` field is fine and recommended.)
- **Output inserted back into the note.** Rejected for v1: vault writes from
  command output need provenance, idempotency, and re-run semantics — a
  second feature. Pager + `y` to copy suffices.

## 7. Acceptance criteria

- Conformance vectors for `run:`/`bob-run` grammar (ports of the copy-chip
  vectors + catalog-resolution cases: excluded, capture-text, unknown,
  `&&`-refusal, nested-in-copy-payload, label escapes).
- Cursor-rule parity tests with copy chips, including ambiguous and fence
  cases; `api.commandChips` frozen/never-throw checks via the plugin-apis
  harness.
- Engine tests with stubbed `api.commandMode`: reads run, preview-first
  previews, confirm confirms, engine-absent dims, mobile dims, no-shell
  assertion (payload containing `&&` never reaches spawn — assert argv).
- Editor tests: `Cmd+Enter` on runnable line runs; on non-chip line existing
  behavior unchanged (Highlights/gmail/link); ambiguous line never runs.
- Vault: pilot `gcal ack` chip line adopted; Bank line split (chip + prose
  `rm`); plugin off = plain code everywhere; docs + glossary strand landed.

## 8. Recommended solution (for the decision)

Approve **command chips inside `bob-copy-chips` (display name "Bob Chips",
id unchanged)**: `run:` spans + `bob-run` sequence fences, rendered quiet
and distinct (▶), resolved against `bob __catalog`, executed solely through
`api.commandMode` with write policies honored, `Cmd+Enter` dispatched by
nav-hotkeys with fall-through, discoverability via face + tooltip +
cursor-line hint + status bar, pilot adoption on the Ack line, and this
glossary strand:

> **Command Chip** (aliases: run chip, bob-run) — Authored runnable `bob`
> command in an Obsidian note: an inline code span starting with `run:` (or
> `run[LABEL]:`) or a `bob-run` fence holding one `bob …` command per line.
> The chips plugin renders the span as a quiet run pill (▶) and the fence as
> a titled sequence card; `Cmd+Enter` on a line with a single command chip
> (or the palette command) runs it through command mode's engine with the
> catalog's write policy — reads run, preview-first previews, confirm
  > confirms — while `Alt+Click` sends it to the sheet. Payloads carry
> complete literal argv (no shell, no `&&`); plain `` `bob …` `` spans stay
> inert. With the plugin off, every chip still reads as inline code or a
> fence. Cursor rule mirrors copy chips: under-cursor wins, else the only
> chip on the line, else the enclosing fence; two or more chips with the
> cursor on none is ambiguous and never guessed. See `docs/bob-copy-chips.md`
> (chips section) and `docs/guides/run-bob-from-obsidian.md`.

Phasing: (1) grammar + render + `api.commandChips` + vectors; (2) engine
wiring + policy handling + sequence reuse; (3) `Cmd+Enter` dispatch +
hints/status + palette + `Alt+Click`; (4) GTD pilot adoption + docs +
glossary. Explicitly out of v1: shell operators, output-to-note, scheduling,
arg prompting at run time (author-time completion in the make-or-edit card
may follow).

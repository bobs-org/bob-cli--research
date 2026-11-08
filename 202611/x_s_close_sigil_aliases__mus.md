# x/s close-sigil shorthands (`xx` → `x!`, `xs` → `x*`, `x=1=s` → `x=1=*`): research

Researcher: `mus` (independent swarm member; peer reports not consulted).
Date: 2026-11-08. Workspace: bob-cli checkout (apollo).

## 1. Summary

The request is implementable by following the existing sigil-alias pattern, but the
proposal as worded needs tightening before anyone builds it. The core idea — home-row
`x`/`s` as no-Shift aliases for `!`/`*` in close selections — is ergonomically sound
(`!` is Shift+1, `*` is Shift+8 on US layouts) and steals no currently-valid spelling in
the contexts where it would fire. The risk is not grammar collision but transport cost
and surprise: `x`/`s` are letters, the first alias keys that appear in ordinary prose,
so a naive implementation fires a `capture-rewrite` subprocess on every `x`/`s`
keystroke. Every existing alias (`,`, `.`, `;`, `=`, `\`, `/`, `-`-in-`x=`) is rare
punctuation; this would be the first common-letter trigger.

Recommended solution: implement as a narrow extension of bob-cli's existing
`expand_sigil_alias` rewrite (`expand_sigil_alias`, rule `expand_sigil_alias`), gated
by the ordinary completion grammar exactly like the other aliases, plus a cheap
client-side prefilter in Bob Mac Capture so prose `s`/`x` never spawns `bob`. Accept
the aliases server-side nowhere else (no new canonical spelling; `bob capture` and
`bob capture-parse` keep the literal text, as with all assists). Scope v1 to two
positions only: whole-item `x` close selections and the close part after the second `=`
in `x=` past tokens. Defer link/task-suffix `=x` aliases. Details in §6.

## 2. What was asked (and what it means)

- `x` → `!`, `s` → `*`.
- Position 1: "when used with the `x` syntax": typing `xx` yields `x!` wherever the
  `x` close is respected. By extension `xs` yields `x*`, `x1x2` yields `x1!2`,
  `x1s2` yields `x1*2`, etc.
- Position 2: "instead of the second `=`" in `x=`: typing `x=1=s` yields `x=1=*`
  wherever `x=` is respected. By extension `x=1=x` yields `x=1=!`.

The second bullet's wording is misleading and needs a correction (see §6.1): the alias
does not replace the second `=` itself. In `x=1=s` the second `=` is already present;
`s` occupies the close-sigil slot *after* it (`close_text` in `past.rs`). A spelling
like `x=1s2` (no second `=`) must stay literal — it is an `E`-name continuation, not a
close.

## 3. Current behavior (verified)

All observations below were reproduced in-session with the installed `bob 0.4.0` unless
noted as code reading.

### 3.1 Existing shorthand architecture

- Authoritative rewrites live in bob-cli:
  `src/native/capture_language/rewrite.rs`, `rewrite_draft()`, rule
  `RewriteRule::ExpandSigilAlias` (`expand_sigil_alias`). Help text is the contract in
  `src/native/capture_rewrite.rs` (`bob capture-rewrite --help`).
- The Mac app is a thin client (see `decisions:mac-capture-is-a-thin-client`, read via
  audited memory read): it never decides grammar. On each eligible key it records a
  one-shot intent (`CapturePanelModel.noteSeparatorToggleIntent`,
  `CapturePanelController.noteSeparatorToggleIntentIfEligible`) and asks
  `bob capture-rewrite -c <cursor>`; bob's `completion_field_at` gate decides. The
  reply is applied as one native single-edit so Undo restores the literal key
  (`applyNativeSingleEditRewrite`). Transport failures never disturb the draft.
- Trigger keys today (`keyboard.md`, `CapturePanelController` allowlist,
  `noteSeparatorToggleIntent` allowlist): `: ^ + | , . ; \ / - = ~` plus digits for the
  separate Swift-only auto-comma (`CaptureCloseTaskCommaAssist`: `x1`+`2` → `x1,2`
  when the running Pomodoro has <10 numbered links). No letter triggers a rewrite
  today. `=` after space/tab aliases `~` (Links To); `=` after `~`/`~~` flips
  direction with a 350 ms fast-`==` undo path (`CaptureEqualsGesture`); `-` inside
  `x=` aliases `~` (`x=2-` → `x=2~`); `\`/`/` alias `#` with double-tap literal
  handling. `bob capture` / `capture-parse` keep the literal text for all of these.

### 3.2 `x` and `x=` grammar today

- Whole-item close (`docs/capture.md`): `x[<N>][*<P>][!<M>][~<K>][@<N>]`, lowercase `x`
  only, separators `,` `*` `!` `~` `@` in any order; `<N>` may be typed last as
  `@<N>`; bare `*`/`!` select all-remaining (`park_all`/`complete_all`). Lexer:
  `capture_language/close_selection.rs` (`lex_close_selection`,
  `classify_whole_item_close`). `xx`, `xa`, `xs`, `X2` are explicitly *not* closes —
  they stay prose. `x#…` is a claimed near-miss; retired `=x`/`=*`/`=!` spellings teach
  `x…`.
- Past (`x=E[s][!][=X]`, `past.rs` / `editor_pomodoro.rs`): `E` is count and/or name,
  optional repair `!`, optional second `=` plus close text lexed by the *same*
  `lex_close_selection`. `split_past_token` ignores `!`/`=` inside quoted literals.
- Live verification (installed bob):
  - `capture-rewrite -c 2 -- 'xx'` → `changed:false`, text `xx` (no rule today).
  - `capture-rewrite -c 5 -- 'x=1=s'` → `changed:false` (cursor 5 is end; `-c 6`
    is out of bounds for a 5-byte input — the earlier `--cursor` error was an
    off-by-one in the probe, not a behavior signal).
  - `capture-parse -- 'xx'` → `mode:task`, no spans (prose).
  - `capture-parse -- 'xs'` → `mode:task` (prose).
  - `capture-parse -- 'x!'` → `mode:pomodoro_close`, `complete_all:true`.
  - `capture-parse -- 'x1x2'` / `'x1s2'` → `mode:pomodoro_close` + `error
    invalid_pomodoro_close` ("not a task list … e.g. `x1*2!3~4`"), range over the
    trailing bytes.
  - `capture-parse -- 'x=1=*'` → `mode:pomodoro_past`, `close.raw:"*"`,
    `park_all:true`. `x=1=s` / `x=1=x` → `mode:pomodoro_past` + `error
    invalid_pomodoro_past` ("not a task list …"), range over the sigil byte.

So in every target context the alias source is today either prose (`xx`, `xs`) or a
claimed error (`x1x2`, `x=1=s`), never a valid competing meaning. The only true
"theft" is a single-token draft that is literally the task `xx` or `xs`.

## 4. Critique: is this a good idea?

**Ergonomics: yes, with a caveat.** Closing is high-frequency and `!`/`*` both need
Shift. `x`/`s` are home-row-adjacent and unshifted. `xx` as double-tap-`x` is
particularly cheap. This is the strongest argument for the feature.

**Collision: low but non-zero.** Because bob gates on "would `!`/`*` be valid here,"
prose is safe: typing `fix`, `tasks`, `six`, `box`, `x-ray` never rewrites because the
swapped candidate fails the completion-grammar check. The residual collisions are:
(a) a draft whose whole item is literally `xx`/`xs` intending a task — will flip to
`x!`/`x*` with Undo as the escape hatch; (b) `E`-names in `x=` containing `x`/`s`
(`x=fix`, `x=sprint`) — must not rewrite, and the grammar gate already protects them
because the swap is only attempted in the close part (see §6). Both are acceptable if
documented, but (a) deserves an explicit callout in `keyboard.md`: "Undo restores the
literal letters."

**Transport cost: the main objection to a naive port.** Current triggers are rare
bytes. `s` is one of the commonest English letters; `x` is common in this grammar
(`x` prefix, `x=` tokens, hex, `fix`). Recording a separator intent on every `x`/`s`
means a `capture-rewrite` spawn per such keystroke (measured ~5 ms on athena in the
thin-client decision record; Mac latency unmeasured here). Correctness is unaffected
(bob returns `changed:false`), but latency, battery, and rewrite-race surface all grow
for zero benefit on 99% of those keystrokes. Any implementation must add a cheap
client-side prefilter (lexical, non-authoritative) so prose `s`/`x` never spawns bob.
This is a presentation-layer optimization, not a grammar decision, so it does not
violate the thin-client rule — but the filter must stay dumb (e.g. "current item looks
close-ish") and bob must remain the only authority.

**Consistency across clients: partial.** Like all assists, the rewrite would be
Mac-only typing assistance; CLI/Obsidian users typing `xx` get prose/error until they
read the docs. That matches existing assists (thin-client decision explicitly blesses
"lands in bob-cli first, app presents it"), but it means the feature is *not* a grammar
extension — `bob capture 'xx'` must keep failing/teaching, or every client silently
gains a second spelling and canonical-form drift begins. Keep it assist-only in v1.

**Discoverability and teaching:** `!`/`*` are visible in `docs/capture.md` and error
messages (`… e.g. x1*2!3~4`). `x`/`s` aliases would be invisible unless error text,
`capture-rewrite` help, and `keyboard.md` name them. Do not add them to the
`invalid_pomodoro_close/past` teaching messages in v1 — those messages already name the
canonical form; alias documentation belongs in the assist surfaces.

**What I would not do:** accept `x`/`s` as first-class grammar (lex
`lex_close_selection` to treat them as separators at parse/capture time). That forks
canonical form (`xx` vs `x!` both valid), complicates every consumer of
`pomodoro_close` JSON, and bypasses the Undo-restorable assist contract. Assist-only
preserves one canonical form.

## 5. Options considered

| Option | Where | Upside | Downside |
|---|---|---|---|
| A. `expand_sigil_alias` + Swift trigger (+ prefilter) | bob-cli `rewrite.rs`; Mac `noteSeparator…` allowlists | Follows the proven pattern; Undo-native; bob stays authoritative; additive JSON (no `schema_version` bump) | Per-keystroke spawn unless prefiltered; touches two repos + Mac CI gate |
| B. Server-side alias acceptance only (lex `x`/`s` as `!`/`*`) | `close_selection.rs`, `past.rs` | Works in every client; no per-keystroke cost | Forks canonical form; no typing feedback; broadest blast radius |
| C. Swift-only span-gated swap (like auto-comma) | `CaptureCloseTaskCommaAssist`-style helper | No subprocess; no bob change | Duplicates grammar in Swift; violates thin-client decision; rejected |
| D. Reject / pick non-letter keys | — | Zero cost | Keeps Shift burden; ignores the real ergonomic win |

A hybrid worth naming: A for typing plus B's *error-message* hint only (no acceptance).
V1 should be A alone.

## 6. Recommended solution (with adjustments to the request)

### 6.1 Scope corrections (please adopt these)

1. **The `x=` alias replaces the close sigil, not the second `=`.** Restate the
   requirement as: "after a typed second `=`, `x`/`s` in the close-sigil slot expand to
   `!`/`*`." `x=1x` (no second `=`) stays literal; `x=fixs` stays an `E` name.
2. **Lowercase only.** Uppercase `X`/`S` stay literal (`X` never opens a close).
3. **Two positions in v1; everything else stays literal:**
   - whole-item `x` selection separators (including the bare `xx`→`x!` / `xs`→`x*`
     case and interior cases `x1x2`→`x1!2`, `x*1s2`→`x*1*2`, dangling `x1x`→`x1!`);
   - past-token close part after the second `=` (`x=1=s`→`x=1=*`, `x=3fix=x`→`x=3fix=!`,
     including dangling `x=1=x`→`x=1=!` which then needs `pomodoro_close_task`).
   Explicitly out of scope for v1: link/task-suffix closes (`=x…`, `^…=x…`), `@`-lists,
   `,`/`~` slots, and any `E`-internal position. Link suffixes can follow once v1
   proves out; they need separate trigger-context work in pickers.
4. **Assist-only, not grammar.** `bob capture` / `capture-parse` keep literal `xx` /
   `x=1=s` behavior (prose / teaching error). Only `bob capture-rewrite --cursor`
   expands, and only when the swapped candidate passes the same `completion_field_at`
   check the real sigil would need.

### 6.2 bob-cli implementation sketch

Extend `expand_sigil_alias` in `src/native/capture_language/rewrite.rs` (before the
`.`/`;` branch, after the `=`/`\`/`/` branches):

- If alias byte is `x` or `s` at `cursor-1..cursor`, build `candidate` with `!` (for
  `x`) or `*` (for `s`).
- Whole-item path: tokenize, require the token to end at `cursor` and start with
  lowercase `x` (whole-item close shape per `classify_whole_item_close` on the
  *candidate*), then require `completion_field_at(&candidate, cursor)` to report a
  close context (`PomodoroClose` family / `PomodoroCloseTask` need) with replacement
  ending at `cursor`. Mirror the `.`/`;` shape: `finish_sigil_alias(..., sigil, alias)`,
  summary `Typed ! for x` / `Typed * for s`.
- Past path: require the alias byte to sit inside an `x=` past token's close part
  (reuse the `expand_past_segment_dash_alias` token-location logic: `past_token_len`
  + `split_past_token`, alias offset ≥ `close_offset`), then the same completion check
  for `PomodoroPastSegment` with the expected-start rule (prior `~` case does not apply
  here, but keep the same shape for consistency).
- Quoted literals (`x=#"…"`), wikilink claims (`wikilink_claims`), and template drafts
  stay excluded by the existing guards; reuse them.
- No `schema_version` bump (same `expand_sigil_alias` rule code, same JSON shape).
- Update `capture-rewrite --help` long text (one sentence per existing style) and
  `src/native/capture_language/tests/rewrite.rs` (valid + literal tables:
  `xx`→`x!`, `xs`→`x*`, `x1x2`, `x1s`, `x=1=s`, `x=E=s`, plus negatives `fix s`,
  `x=fixs`, `x=1s2`, `X`, `S`, mid-prose `tax`).

### 6.3 Bob Mac Capture implementation sketch

- Add `"x"`, `"s"` (lowercase only, no modifiers) to the two allowlists:
  `CapturePanelController.noteSeparatorToggleIntentIfEligible` and
  `CapturePanelModel.noteSeparatorToggleIntent`. No other gesture logic changes;
  `=`/`~` fast-tap probes are untouched.
- Add a cheap prefilter *before* recording the intent (new, presentation-only):
  skip when the caret is not plausibly in a close context — suggested heuristic: the
  current physical line's trimmed text starts with `x` or contains `x=` before the
  caret, and the key is at token end. Bob still decides; the filter only avoids
  spawning `bob` for `the box`, `tasks`, etc. Log/measure spawn rate before/after.
- No change to `CaptureEqualsGesture`, comma assist, or picker flows. The existing
  `applyNativeSingleEditRewrite` path already gives native Undo ("Undo restores `x`/`s`").
- Docs: `docs/keyboard.md` rows for `x`/`s` (mirror the `1–9`/`,`/`.`/`;` rows,
  including the Undo note); `docs/protocol.md` capability note is *not* needed (no new
  rule code). Mac CI (`scripts/dev/macos-ci-check`, exact-SHA watch) gates the change
  per the linked-repo rule.

### 6.4 Docs, help, and gates

- `docs/capture.md`: one assist callout near the `x…` row stating the Mac typing
  aliases and that capture keeps the literal text (follow the existing
  "These assists are editor-only" paragraph pattern). No grammar-table change.
- `just docs-check` must pass; `bob capture-rewrite` help text regenerates via
  `just docs-gen` if that pipeline owns it (check `cli_rules.md`/`docs.md` routes).
- Tests: bob-cli `rewrite.rs` tables + Mac `Tests/` rewrite-fixture coverage for the
  new trigger (follow the existing `generate-*-fixtures.sh` pattern if one covers
  rewrites). Full `just check` (or the repo's documented gate) before merge.
- Release: normal daily train applies (no `Cargo.toml`/`CHANGELOG.md` edits by hand
  per `decisions:bob-cli-releases-ride-a-daily-train`); mark nothing breaking.

### 6.5 Edge cases to cover in tests

`xx`, `xs`, `x1x`, `x1s`, `x1x2`, `x1s2,3`, `x*x`(?→`x*!` competing-wildcards error —
must surface bob's error, not swallow), `x!x`, `x=1=s`, `x=1=x`, `x=E=s` with named
`E`, `x=fixs` (literal), `x=1s2` (literal), `tax`/`fix s` (literal), `X`/`S`
(literal), `xx` in multi-item draft second line, `xx` with trailing Work Log bullet,
`x=…` with quoted literal containing `x`/`s`.

## 7. Open questions for Bryan (if v1 proves popular)

- Should link/task-suffix closes (`=x1x2` style) gain the same aliases, or is
  whole-item + past enough? Recommendation: wait for usage signal.
- Should the teaching errors for `x1x2`/`x=1=s` name the alias (`… write x1!2`)?
  Recommendation: no in v1; keep canonical `!`/`*` in errors.
- Is stealing whole-item task `xx`/`xs` acceptable, or should bare `xx`/`xs` require a
  second confirming gesture? Recommendation: accept the theft; Undo covers it and the
  task text is vanishingly rare.

## 8. Evidence and provenance

- Code: `sase/repos/linked/bob-mac-capture/Sources/.../CapturePanelModel.swift`
  (`noteSeparatorToggleIntent`, `startCaptureRewrite`, `CaptureEqualsGesture`),
  `CapturePanelController.swift` (`noteSeparatorToggleIntentIfEligible`),
  `CaptureCore/CaptureCloseTaskCommaAssist.swift`, `docs/keyboard.md`;
  bob-cli `src/native/capture_language/rewrite.rs` (`expand_sigil_alias`,
  `expand_past_segment_dash_alias`, `expand_relation_*`),
  `close_selection.rs` (`classify_whole_item_close`, `lex_close_selection`),
  `past.rs` (`split_past_token`), `editor_pomodoro.rs` (close/past outcomes),
  `src/native/capture_rewrite.rs` (help contract), `docs/capture.md` (grammar tables).
- Live probes (installed `bob 0.4.0`, §3.2): `capture-rewrite` `changed:false` for
  `xx`/`x=1=s` today; `capture-parse` modes for `xx` (task), `x!`
  (`pomodoro_close`, `complete_all`), `x=1=*` (`pomodoro_past`, `park_all`),
  `x=1=s`/`x1x2` (claimed errors).
- Memory: audited reads of `decisions:mac-capture-is-a-thin-client`,
  `glossary:Capture`, `cli_rules.md`, `docs.md` (reasons logged in `sase memory log`).

*Recommendation restated: build Option A scoped as §6 (assist-only `x`/`s` →
`!`/`*` in whole-item closes and post-`=` past closes, lowercase only, bob-gated with
a Mac prefilter), with the §6.1 wording corrections. Do not extend the grammar itself.*

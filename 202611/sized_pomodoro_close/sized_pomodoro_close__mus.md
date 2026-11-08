# Sized closes: an `<N>x` resize prefix for the `x` capture syntax

Research report (swarm researcher `mus`). Goal: help decide how — and whether —
to add `<N>`-prefix support to the `x` Pomodoro-close capture syntax, where
`<N>` is a positive integer giving the size in 5-minute blocks the running
Pomodoro is resized to before closing (e.g. on a 25-minute session,
`2x!2` ≡ `-3 x!2`).

## Verified baseline (what exists today)

All claims below were checked against the working tree (grammar 19) and by
running `cargo run -q -- capture-parse -f json`.

- **Whole-item close** is `x[<N>][*<P>][!<M>][~<K>][@<N>]`, lowercase `x`
  only, `*`/`!`/`~`/`@` in any order, keep-list optionally last as `@<N>`
  (`docs/capture.md`, `src/native/capture_language/close_selection.rs`).
  `classify_whole_item_close` claims `x` followed only by a digit or
  `,!~*@`; everything else (`xx`, `xa`, `x-ray`, `X…`) stays prose.
- **The proposed token is free today.** `2x!2` and `2x` currently parse as
  ordinary tasks (`mode: "task"`, no spans), confirmed by direct probe.
  So the prefix claims no existing close — but it does claim some existing
  *prose* (see collisions).
- **Relative adjust** `+[N]`/`-[N]` resizes the running timed session by
  N×5 min, start fixed, `new_end = (start + new_duration) mod 24h`,
  `new_duration = max(0, old + delta)` (`docs/capture.md` §Adjusting,
  `src/native/capture/pomodoro_adjust.rs`).
- **Close auto-truncation** (`close_timing` in
  `src/native/capture_pomodoro_close/ledger.rs:187`): `remaining = end − now`;
  if `remaining ≥ 5`, shorten by `floor(remaining/5)×5`; never extend on
  overrun; an un-started MEET closes at 0m with a reset warning.
- **Chaining already works.** `+2 x` / `-3 x!2` split into per-operator items
  planned atomically against one snapshot batch with full rollback
  (`docs/capture.md` §Chaining). The arithmetic saving is therefore the
  *only* functional gap — atomicity already exists.
- **Taken spellings that rule out alternatives.** `x=2` is a recorded-past
  session (`pomodoro_past`, 2 blocks), `=2…` is a timed start (`=<X>`),
  `x2` keeps task 2 in progress, `@<N>` inside a close is the keep-list.
  Any suffix spelling for absolute size needs a new sigil; every candidate
  (`=`, `:`, `/`, `+`) already means something adjacent to `x`.

## Semantics of the proposal (made precise)

`Nx<sel>` ≡ compute `delta = N×5 − old_duration`, apply it exactly as a
`±<delta/5>` adjust would (start fixed, mod-24h end, same clock-key
restamping, clamp at 0, checked arithmetic), then run the unchanged close —
including its `close_timing` truncation at the same `now` — with selection
`<sel>` lexed by the existing `lex_close_selection`.

Consequences worth stating explicitly:

1. **The `-3 x!2` equivalence holds** (25 − 10 = 15 = 3 units) but is
   semantic, not byte-identical: one ledger rewrite, not two; one JSON item
   (`pomodoro_close` with an additive resize object), not
   `[pomodoro_adjust, pomodoro_close]`.
2. **Resize-up followed by close still truncates.** `6x` on a 25m session at
   T+10 closes at ~T+10, not 30m — unless `now` is already past the resized
   end (overrun), in which case the sized close *extends* where a bare `x`
   never would. That extension is the feature's main correctional power
   (claim a longer session than planned) and must be previewed, not hidden.
3. **Un-started MEETs discard the size.** `close_timing`'s not-started branch
   zeroes the duration regardless of N. Keep that behavior; the preview must
   say "closes 0m" so the size isn't silently swallowed.
4. **`Nx0` needs a ruling** (see adjustments): bare `x0` on a note-free
   session *resets* instead of closing. An explicit size plus reset is
   incoherent — resetting would discard the size the user just stated.

## Critique: is this a good idea?

**Yes, but narrowly — and the spelling needs the guardrails below.**
The honest accounting:

- *Real need, small surface.* Routine closes need no arithmetic at all
  (`x!2`). The pain is correction closes: the session ran 34 minutes, you
  want to claim 30, the plan says 25, and you must compute `+1` in your head
  while the standup waits. Stating the target absolutely ("close at 6
  blocks") removes exactly that step. Frequency is low but friction is high,
  which is the right shape for a terse operator.
- *Reliability gain is ~zero; preview gain is large.* Two-token `-3 x!2` is
  already one atomic batch. The failure mode of the new syntax is mistyping
  N (`20x` for `2x` = 100 minutes), which only a **preview line showing
  resolved size and delta** ("25m → 10m · −15m") catches. Grammar without
  preview is arguably worse than status quo; grammar with preview is
  strictly better.
- *The mirror spelling is the beauty risk.* Every existing count follows its
  sigil (`+5`, `=3`, `x2`, `x*1`). `Nx` is the first count-before-sigil, and
  the two numbers in `2x!2` count different things (blocks vs. task index).
  It reads fine once learned ("2-block close, completing 2" — blocks ×
  tasks, like dimensions) but will be misread under speed at first. I
  considered suffix-with-unit forms (`x!2:10m`) and rejected them: `x=2` is
  taken by recorded-past, `:` means link/pick everywhere else, and trailing
  forms collide with inline Work Log entries (`x 10m` logs "10m" today).
  The prefix is the only bare slot that is actually free — keep it, and
  spend the design budget on disambiguation instead of sigil shopping.
- *Prose collisions are real but bounded.* Under "claim only valid close
  bodies", `2x4 lumber` flips from task to sized-close-with-entry (valid
  `x4` + entry `lumber`), and dose-like tasks (`3x daily`) flip too.
  Mitigations: strict claiming (anything after `x` that isn't a valid
  selection/entry stays prose), the existing uppercase escape (`2X4 …` stays
  prose, matching the `X`-escape convention), and documenting the break in
  the release notes. Do not ship a "prefix plus free prose" reading —
  `2x buy milk` must stay a task, not a sized close with entry `buy milk`…
  wait, under close-entry grammar `x buy milk` *is* a close with entry.
  So `2x buy milk` *would* claim. Accept this as the documented break; the
  escape hatch covers it.

## Design options

| Option | Spelling | Pros | Cons |
| --- | --- | --- | --- |
| A. Prefix (proposed, guarded) | `2x!2` | Shortest; only free bare slot; "blocks × tasks" reads well once learned | Mirror-image of `x2`; prose breaks (`2x4 lumber`, `Nx daily`); `Nx0` needs a ruling |
| B. Absolute-adjust chain item | `>2 x!2`-shaped new operator + plain close | Reuses chaining; no close-lexer change | Invents a sigil anyway; two tokens; same prose-claim problem on the new item |
| C. Suffix with unit | `x!2:10m` | Zero prose collision; self-documenting unit | `:` means link/pick elsewhere; longer; entry-text edge cases; still a lexer change |
| D. No grammar: preview-assisted chaining | preview shows `-3 → 10m` for `-3 x` drafts | Zero grammar cost, zero collisions | Keeps the mental arithmetic the request wants gone |

A wins: it is the smallest change that removes the arithmetic, and its
costs are containable in one shared lexer plus preview.

## Adjustments to the requirements (explicit)

1. **Strict claiming.** `^[1-9][0-9]*x` claims the token *only* when the
   after-`x` body lexes as a valid close selection and/or entry through the
   existing `lex_close_selection` + entry grammar. Otherwise the item stays
   prose/task exactly as today. (`0x…` never claims: `0x` is a teaching
   error pointing at `x0`.)
2. **Case rule.** Uppercase `Nx`/`NX` stays prose, extending the existing
   `X`-stays-prose escape. `2X4 lumber` is the documented workaround for
   displaced prose.
3. **`Nx0` always closes, never resets.** An explicit size means the user is
   claiming work; the bare-`x0` note-free reset does not apply. `2x0` =
   resize to 10m, defer every link, close.
4. **Single atomic rewrite.** Sized close = one ledger rewrite (resize +
   close fused), one `pomodoro_close` JSON object with an additive `resize`
   member (`blocks`, `minutes`, `before/after` range, `delta_minutes`), one
   human line (`2x!2 (10m · complete 2 · …)`). Dry-run byte-identical minus
   the commit. Additive-only JSON (precedent: `parked`/`dropped` roles).
5. **v1 scope: whole-item closes and same-line chains only**
   (`2x!1 =bugs`, `2x wired the lexer`, child `- 1 …` bullets unchanged).
   Link/task suffixes (`@r:id=2x!1`) are a non-goal for v1: after-`=` digit
   position collides with `=<X>` start timing and needs its own grammar
   surgery. Revisit on request.
6. **N bounds 1–288** (5m–24h). Oversized reuses the existing "too large"
   wording; checked arithmetic before any write; failures write nothing.
7. **Preview is part of the feature, not polish.** `capture-parse` reports
   the resize in the `pomodoro_close` spec; Mac Capture renders
   "25m → 10m · −15m" (and "closes 0m · un-started" for pre-start MEETs)
   before submit. Shell quoting is unchanged (`2x!2` single-quoted like
   `x!2`).
8. **Editor parity checklist ships with the change:** `capture-parse`
   (spec + `pomodoro_close`-family span for the `N` prefix),
   `capture-complete` (no new candidates; note the `2`→`2x` task-to-close
   reclassification flicker while typing), `capture-rewrite`, JSON glow,
   human output, `docs/capture.md` grammar table + prose, release-note
   breaking-change entry for displaced `Nx…` prose.

## Recommended solution

Implement **Option A with adjustments 1–8**: `Nx…` sized closes as a thin
prefix strip in front of the shared close-selection lexer
(`classify_whole_item_close` + `lex_close_selection`), fused single-write
resize-then-close semantics per §Semantics, whole-item + chain scope,
additive JSON, preview showing resolved size and delta, and the documented
prose-break with the uppercase escape. baryta: it is the tersest spelling
that fits the grammar's one free slot, it composes with every existing
close feature (selections, wildcards, `@`-last, entries, bullets, chains)
because it reuses their lexer untouched, and its two genuine risks
(mistyped N, displaced prose) are both handled outside the lexer — by
preview and by strict claiming plus the `X` escape. Skip link-suffix
support until someone asks; do not add a unit sigil.

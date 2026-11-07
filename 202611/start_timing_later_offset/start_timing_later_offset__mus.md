# Forward pomodoro-start offsets (`+<N>`): design research

Researcher: `mus` · 2026-11-07 · swarm brief: `=<X>`, `@file:id=<X>`, and (if appropriate) `x=<X>` plus trailing `+<N>`.

## TL;DR

The verbatim proposal — glue `+<N>` (default 1) onto the end of any `<X>`, so
` =fix2+` ≡ `=fix2 ++` and `@foo:bar=+3` ≡ `@foo:bar= ++3` — cannot ship as
written. It silently redefines existing valid pomodoro names. `+` is name
charset today, and the exact example strings already mean something else:

- `=fix2+` today is the named start `FIX2+` (empty timing), not `FIX` + 2 blocks + forward 1.
- `=bugs+2` today is `BUGS+` + 2 blocks. `=bugs+`, `=c++`, `=fix+` are names.
- `@foo:bar=bugs+`, `@foo:bar=bugs+2`, `@foo:bar=fix2+` are valid link-starts under `BUGS+` / `FIX2+`.
- `x=fix2+`, `x=fix+2`, `x=3fix+` are valid past names (`FIX2+`, `FIX+`).
- By contrast `@foo:bar=+3`, `=3+`, `=3+2`, `x=3+` are currently shape errors, so the
  *unnamed* slot is free.

**Recommended scope (adjustment to the requirements):** add symmetric forward
offsets to `<X>` **only where no name collision exists** — the unnamed start,
the unnamed link-start, and the *leading* `<X>` of a named start — and keep
every trailing-after-bare-name `+` string as a name. Explicitly scope `x=`
**out**. Concretely:

- Unnamed: `=+`, `=+3`, `=3+`, `=2+1` (and `@route:id=+`, `@route:id=+3`,
  `@route:id=3+`, `@route:id=2+1`) mean duration + forward offset.
- Named leading: `=+2bugs`, `=2+1bugs`, `=3+2#deep-work`, `@route:id=2+1bugs`.
  Never `=fix2+` / `=bugs3+2` for the offset — those stay names and teach the
  leading rewrite.
- `x=` takes no `+` offset. Use `~` segments (past) or `=` with `+` offset
  (future) instead.

This is intuitive (`+` = later, `-` = earlier, bare = 1, same 5-minute units),
reliable (no silent reinterpretation, one ledger write, works for link-starts
that cannot chain today), and beautiful (full `-`/`+` symmetry in the only
positions where both are unambiguous).

## What `<X>`, `++`, and chains mean today

### `=<X>` mirrors Obsidian `se<X>`

`docs/capture.md` §§ "Starting the next Pomodoro", "Linking and starting
existing tasks", and `docs/reference/capture-syntax.md` §§ `=`/`=<X>`,
`@route:block-id=<X>` define one shared suffix grammar:

```
<X> ::= [0-9]* (-[0-9]*)?
```

| Suffix | Duration | Offset |
| --- | --- | --- |
| empty | 25 min (5u) | 0 |
| `3` | 15 min | 0 |
| `-` | 25 min | 1u back |
| `-2` | 25 min | 2u back |
| `3-` | 15 min | 1u back |
| `2-1` | 10 min | 1u back |

Implementation: `parse_pomodoro_start_suffix` in
`src/native/capture_language/tokens.rs:1609`, `PomodoroStartSpec`
(`duration_units`, `offset_units`) in
`src/native/capture_language/model.rs:445`, timing math in
`src/native/capture/meet_event_run.rs:200` (`start_block_minute`) and
`src/native/capture/pomodoro_start.rs:16` (`compute_pomodoro_start_range`):

```
start = ceil((nowMinutes - 5*offsetUnits)/5)*5
end   = start + 5*durationUnits
```

Offsets today only go **backward** (earlier). There is no forward spelling.

Named starts glue timing to either side of a bare name (`=3bugs`, `=bugs3`)
or before `#` (`=3#deep-work`); see `session_equals_token` /
`start_timing_len` / `bare_start_name_len` in
`src/native/capture_language/item.rs:3690-3890` and
`src/native/capture_language/bare_name.rs:1-130`. Bare names start with a
letter, contain no `-`, do not end in a digit, and cannot be close-shaped
(`can_spell_bare`). Crucially, `+` **is** name charset:
`is_pomodoro_selector_byte` includes `b'+'`
(`src/native/capture_language/tokens.rs:576`), and docs enshrine it:

- "`=bugs+2` — Start the Pomodoro named `BUGS+2`; `+` is name charset"
  (`docs/capture.md:398`).
- "`@sase:deep-fix#bugs+` — under `BUGS+`; a trailing `+` after `#name`
  stays part of the name."

Link-starts (`@route:id[ #name][=<X>]`, `^` spelling) share the same lexer
(`parse_link_start_suffix`, `tokens.rs:959`) and the same math/guards, but
refuse while any timed entry runs ("finish the current Pomodoro first"),
while whole-item `=` restarts/swaps. `x=<X>` in the brief is two different
things and neither is a start: `x=E[s][!][=X]` records the past (second `=X`
is close modifiers), and `@route:id=x…` links-then-closes.

### `++[N]` / `--[N]` and chains already delay starts — for whole-item only

`++3` shifts the running session +15 min keeping duration
(`docs/reference/capture-syntax.md:821`, `model.rs:235`,
`item.rs:3273`). Chaining (`docs/capture.md:5579`) lets whole-item session
operators share one line: `=fix2 ++` starts `FIX` 10 min then shifts +5 min.
Verified this session (`bob capture-parse -f json`):

- `=fix2 ++` → two items: `pomodoro_start{raw:2}` + `pomodoro_shift{later,1}`.
- `@foo:bar= ++3` does **not** chain (task/link forms never chain). It parses
  as `pomodoro_task` with body `++3`, not start+shift. So the brief's second
  equivalence ("`@foo:bar=+3` ≡ `@foo:bar= ++3`") is aspirational, not current
  behavior. That gap is the real motivation for a link-start suffix: there is
  no atomic delayed link-start today.

## Probes run for this report (all via `bob capture-parse -f json`)

```
=fix2+  → mode pomodoro_start, section "fix2+", start{raw:"", dur 5, off 0}
=c++    → section "c++", start{raw:""}
=bugs+2 → section "bugs+", start{raw:"2", dur 2}
=fix2   → section "fix",  start{raw:"2", dur 2}   (control)
@foo:bar=+3 → invalid_pomodoro_start (teaches se<X> shapes)
@foo:bar=bugs+ / =bugs+2 / =fix2+ → valid pomodoro_link under BUGS+ / FIX2+
x=fix2+ → pomodoro_past name FIX2+, blocks 5
x=fix+2 / x=3fix+ → name FIX+, blocks 2 / 3
=+ / =+3 → mode task (prose), NOT a start
=3+ / =3+2 / =3-+ / =-2+ / =2-1+ → invalid_pomodoro_start "must be whole item"
x=3+ / x=+ / x=3+2 → invalid_pomodoro_past
@foo:bar=+ / =3+ / =3+2 → invalid_pomodoro_start (free to repurpose)
```

Takeaway: the unnamed `+` slot errors today (free); every named `+` slot is
taken (collision). `=+` as prose is also taken (grammar break if repurposed
without a bump).

## Why verbatim `+<N>`-at-the-end fails

1. **Silent reinterpretation of `C++`-family themes.** `decisions:theme-hue-is-config-pin-exempt-area-then-hash`
   and `glossary:task-type` bless `+`-joined components (`C++`, `BUGS+`,
   `bob+sase`). Tests assert `is_pomodoro_selector_component("c++")` and
   `#c++` parsing (`tests/grammar.rs:393`). Relexing trailing `+` as offset
   turns `=c++` (C++ 25 min) into `C` + offset, `=bugs+` into `BUGS` + offset.
   That is data-dependent breakage in existing vaults, not a clean grammar
   bump. The existing teaching error for `=bugs+2` ("stays one named start")
   would invert meaning.
2. **Trailing `-` vs trailing `+` are not symmetric.** `-` is excluded from
   bare names, so `=bugs-` / `=bugs3-` are unambiguous offsets. `+` is
   included, so `=bugs+` / `=bugs3+` are ambiguous. Any design that treats
   them as symmetric is wrong for bare names.
3. **`x=` must stay offset-free.** Past records stack backward from the next
   boundary or a `~` segment (`docs/capture.md:5343`, `past.rs`). Forward
   offsets point the wrong way; `~`/`~~`/`~n+` already own `+` after `~`
   (`x=2~1+`, `x=~~`); `x=3+` errors today but `x=fix+` is a valid name.
   A forward `x=` would also need close-modifier disambiguation (`=X` after
   the second `=`). No stated use case needs a future-dated "past".
4. **Chain equivalence is half-true.** `=fix2 ++` works and is already atomic
   at the batch level (staged `CaptureBatchPlanner`, all-or-nothing), but it
   is two ledger writes, two JSON results, two previews, and it cannot express
   a link-start delay at all. A suffix is strictly more expressive there.
5. **Obsidian parity.** `=<X>` is byte-for-byte the `se<X>` snippet range.
   A CLI-only trailing-`+` fork that Obsidian `se<X>+Tab` does not understand
   splits the contract Mac Capture relies on
   (`decisions:mac-capture-is-a-thin-client`). Any grammar change needs a
   joint `se<X>` decision or an explicit CLI-only carve-out with a grammar
   bump (today `grammar: 16`).

## Alternatives considered

| Option | Shape | Verdict |
| --- | --- | --- |
| A. Verbatim trailing `+<N>` everywhere | `=fix2+`, `@=…+3`, `x=…+` | Reject: breaks `C++`/`BUGS+` names silently. |
| B. **Leading-only `+` offsets (recommended)** | `=+3`, `=3+`, `=2+1`, `=+2bugs`, `=2+1bugs`, `=3+2#deep-work`; trailing-after-bare-name stays a name | Accept: symmetric where unambiguous, zero reinterpretation. |
| C. Enable link-start chains (`@id= ++3`) | No new suffix; teach chaining | Weak alone: two writes, diverges from single-write timing/MEET/override semantics; still needs grammar work to admit link forms into chains. Useful complement, not substitute. |
| D. New sigil for forward delay (`=3^2`, `=3>2`) | Avoids `+` collision | Reject: fourth sigil for one axis, no mnemonic, collides with `^`/`>` families. `+` already means later (`++`). |
| E. Do nothing; document `= ++` chain | Zero change | Reasonable fallback if joint `se<X>` says no. But leaves link-start gap and two-write wart. Keep as documented workaround. |

## Recommended solution

### Grammar: symmetric `+` in leading `<X>` only

Extend `<X>` from `[0-9]*(-[0-9]*)?` to also accept `[0-9]*(\+[0-9]*)?`
**when the `<X>` is leading or standalone**, i.e.:

- Standalone unnamed: `=<X>` where `<X> ∈ {"", "3", "+", "+2", "3+", "2+1"}`.
- Leading named: `=<X>name` / `=<X>#name` where `<X>` has the same six shapes
  (`=+2bugs`, `=2+1bugs`, `=+deep-work` is invalid — name still needs `#`
  when bare cannot spell it; `=3+2#deep-work` is the `#` form).
- Link-start suffix: same rule after `=` (`@r:id=+3`, `@r:id=2+1bugs`,
  `@r:id=3+2#deep-work`).

Explicitly **not** extended: trailing `<X>` after a bare name
(`=name<X>`, `@r:id=name<X>`). There `+` remains name charset:

- `=fix2+` stays `FIX2+` 25 min; teach `=2+1fix`.
- `=bugs+2` stays `BUGS+` 15 min; teach `=2+1bugs` or `=2+#bugs+` for the
  plus-named theme with offset.
- `=c++`, `=bugs+`, `@r:id=bugs+`, `x=fix+` unchanged.
- `x=` unchanged (`x=3+` keeps its `invalid_pomodoro_past` teaching toward
  `x=3~` / `x=3`).

Combining `-` and `+` in one `<X>` (`2-1+3`, `2+1-3`, `+-3`) is a shape error.
`+0` / `++0`-analogues fail as positive-magnitude errors, mirroring
`POMODORO_SHIFT_ZERO_ERROR`. Overflow reuses `POMODORO_START_OVERFLOW_ERROR`.
Bare `+` defaults to 1, like `++`/`--`/`+`/`-` and `-` in `<X>`.

### Semantics: one write, future start

- `start = ceil(nowMinutes/5)*5 + 5*forwardUnits`, `end = start + 5*durationUnits`
  (mod 1440 for display, full range for conflict math). This equals today's
  `=X ++N` final range when `now` is not on a boundary dispute, but it is one
  staged write with one `pomodoro_start{offset_units:N}` (add a `direction`
  or sign the raw; keep `offset_units` positive and add e.g.
  `offset_direction:"forward"` — additive JSON, `schema_version` unchanged).
- Unnamed forward start does **not** join the in-progress MEET event run
  (it explicitly asked for later); empty-suffix MEET behavior unchanged.
  Document the carve-out in the MEET section.
- Guards/order unchanged: missing day file / section, multiple open timed,
  no future placeholder (bare `=` still never creates; named still creates),
  link-start "finish current first" refusal, restart/swap override warnings,
  `s:<N>`/`$<N>` conflicts, `~<K>` drop-last ordering (`=2+1bugs~1,3`,
  `@r:id=+3~2` is refused — link-starts take no drop list, as today).
- Close interplay: a future-timed entry is still the running timed entry;
  `x` auto-decrement never extends, so closing "now" before its start trims
  to start (document; prefer refusing close-before-start with a teaching
  error if execution shows a zero/negative trim — decide in implementation
  with a test at `BOB_NOW` + forward 3).
- `capture-parse` mirrors execution lexically: `pomodoro_start` spans cover
  `=` + leading `<X>` and (for bare) nothing trailing; `+` never splits a
  `pomodoro_name` span.

### Teaching, help, and docs

- `POMODORO_START_SHAPE_ERROR` gains the `+` shapes:
  "`=<X>` where `<X>` is empty, digits, `-…`, or `+…`".
- Named `+` collisions teach the leading rewrite, e.g.
  "`=fix2+` names `FIX2+`; for `FIX` 10 min starting 5 min later write
  `=2+1fix`".
- `bob capture --help`, `docs/capture.md` (start/link/chain/MEET/override
  sections), `docs/reference/capture-syntax.md` token rows (`=+/+3/3+/2+1`,
  link-start row, retired-spelling row), and the `se<X>` mirror note all
  update together. No `Cargo.toml`/CHANGELOG edits (release train owns them
  per `decisions:bob-cli-releases-ride-a-daily-train`); grammar `16→17`.

### Implementation checklist (bob-cli)

1. `tokens.rs`: `start_timing_len` + `parse_pomodoro_start_suffix` accept
   `+` mirror of `-`; reject mixed `-`+`+`.
2. `item.rs` `session_equals_token`: claim leading `+<X>`; **do not** consume
   trailing `+` after a bare name as timing (keep `bare_start_name_len`
   behavior); keep `=bugs+2` → name `bugs+` + `2`.
3. `past.rs`: no change (keep `x=3+` error, `x=fix+` name).
4. `editor_classify.rs` / `editor_pomodoro.rs` / `completion.rs` /
   `tokens.rs` link suffix: same leading-only rule; spans as above.
5. `meet_event_run.rs:start_block_minute` + `pomodoro_start.rs` range:
   forward branch; MEET-join carve-out; event-conflict labels
   (`event_conflict.rs:232` formats `{units}-{offset}` — needs a forward
   rendering).
6. `capture_parse.rs` JSON + `markers.rs` errors + `chain` docs (note that
   link-starts still do not chain; the suffix is the way).
7. Tests: `tests/grammar.rs` (`=+/+3/3+/2+1`, named leading, `=fix2+` stays
   name, `@=+3`, `@=2+1bugs`, overflow, `+0`, mixed), `tests/editor_modes.rs`
   spans, link-start table, MEET + close-before-start cases, Obsidian-parity
   fixture if `se<X>` moves jointly.
8. Coordinate `se<X>` snippet owner and Bob Mac Capture (thin client: only
   renders new `pomodoro_start`; no grammar fork without them).

### Worked examples (proposed, `BOB_NOW=09:02`)

| Draft | Meaning |
| --- | --- |
| `=3+` | 15 min, start 0905+5=0910 → `0910-0925` |
| `=+3` | 25 min, start 0905+15=0920 → `0920-0945` |
| `=2+1fix` | `FIX` 10 min, +5 → `0910-0920` (not `FIX2+`) |
| `@sase:deep-fix=+3` | link + start 25 min at 0920 |
| `=fix2+` | still `FIX2+` 25 min at 0905 (teaches `=2+1fix`) |

Quote in zsh (`'=+3'`, `'=2+1fix'`), as with all `=` items.

## Is it a good idea?

Yes, with the adjusted scope. Delayed starts are a real need (back-to-back
run-up, cadence alignment, "start this link in 10 min" without babysitting),
and today they take two writes or are impossible for link-starts. The `+`
mnemonic is already taught (`++` = later, `--` = earlier, bare = 1), so
`+` = later in `<X>` is the least-surprise extension — provided it does not
eat `C++`. The cost is a grammar bump plus joint `se<X>` coordination, which
is normal for this repo. The alternative of documenting the chain forever
leaves the link-start gap and the two-preview wart in place.

## What I would not do

- Do not ship verbatim trailing `+<N>`: it is the only option that silently
  changes what `=c++` means.
- Do not touch `x=`: past placement already has a complete, different
  vocabulary (`~`, `~~`, `~n`, `~n+`, `!`). A future `x=` is a contradiction;
  point users at `=` with forward offset.
- Do not invent a fourth sigil or a `--delay` flag: the CLI rules prefer
  grammar over flags for capture, and `=` already owns start timing.

## Sources consulted

Code: `tokens.rs:1609` (`parse_pomodoro_start_suffix`), `model.rs:445`
(`PomodoroStartSpec`), `item.rs:3273-3890` (`session_operator_token`,
`session_equals_token`, `start_timing_len`, `bare_start_name_len`),
`bare_name.rs` (`can_spell_bare`, `+` in selector), `past.rs:150-500`
(`validate_past_e`, `lex_past_suffix`), `editor_pomodoro.rs`,
`pomodoro_start.rs:16`, `meet_event_run.rs:200`, `event_conflict.rs:232`,
`capture_parse.rs`. Docs: `docs/capture.md` (start/link/chain/MEET/close/past
tables), `docs/reference/capture-syntax.md` (token index, `=bugs+2`,
`#bugs+`, retired spellings). Memory: `cli_rules.md`, `decisions:*`
(capture sigils, clock tags, bullet mirror, link-drop, release train,
mac thin client), `glossary:pomodoro`, `glossary:task-type`. Live probes:
`bob capture-parse -f json` outputs quoted above (`grammar: 16`,
`schema_version: 1`).

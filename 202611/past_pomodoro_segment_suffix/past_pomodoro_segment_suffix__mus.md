# Past-pomodoro gap anchors (`~` suffix for `x=`): research and design recommendation

Researcher: mus (`__mus`). Independent report in a 5-researcher swarm.
Date: 2026-11-05. Context: `x=<E>=<X>` past-pomodoro capture in bob-cli.

## 0. TL;DR and verdict

The feature is worth building, but not exactly as specified. The core need is
real: today `x=` can only record work ending at `T` (now rounded up to the
next 5-minute boundary), filling adjacent windows backward in typed order.
There is no way to backfill a missed session into an earlier gap (between two
completed pomodoros, before the first pomodoro, or at the start of the
trailing rest gap) without manual arithmetic plus a repair `!` trim. A gap
anchor suffix solves that.

I recommend building it with **five adjustments** to the proposal (each marked
**(ADJUSTMENT)** below):

1. **Anchor disables stacking; one anchored token = one independent
   placement.** Do not mix anchor math with the current suffix-sum stack
   offsets. A stack of anchored members should be refused, or each member
   resolved independently against pre-stack history (preferred: resolve
   independently, check the union as today).
2. **Refuse oversized anchored placements; truncate only the bare `~`
   (trailing-gap) form.** Do not silently spill a middle-gap placement into a
   neighbour. The proposal's "`~` cuts off at the end of type (4)" rule is the
   one principled exception because type (4)'s end (`T`) moves with the clock.
3. **Compute gaps from all timed rows (open + closed), and keep the existing
   refusal matrix.** Anchored windows reuse `classify_closed_row` /
   `preflight_overlaps` unchanged; open-row overlap always refuses.
4. **Keep `~`/`~~`/`~n`/`~n+` in `E` only; keep `~<K>` in the close part only;
   teach the boundary.** The `~` overload (drop-links vs gap-anchor) is safe
   because the lexer already splits `E` from the close part at the second
   `=`, but every teaching error that mentions `~` must be rewritten.
5. **Do the `-`→`~` replacement in bob-mac-capture only, as a
   position-aware keystroke transform, never as a bob-cli grammar alias.**
   bob-cli keeps `~` canonical; a dash in anchor position stays a teaching
   error whose rewrite points at the `~` form.

With those changes the design is intuitive (start-anchored by default,
`+` = end-anchored), reliable (pure function of the ledger + `T`, previewable
in `--dry-run` / `capture-parse`), and beautiful (one new `anchor` object in
JSON, one new docs table, editor preview of the resolved window).

---

## 1. What `x=` does today (ground truth)

Sources: [docs/capture.md](docs/capture.md) §"Recording a past Pomodoro"
(~line 5215), [capture-syntax reference](docs/reference/capture-syntax.md),
`src/native/capture/pomodoro_past.rs` (`compute_preflight`,
`preflight_overlaps`, `record_one_member`, `file_recorded_block`),
`src/native/capture_language/past.rs` (`split_past_token`,
`validate_past_e`, `compute_past_stacks`),
`src/native/capture_language/model.rs` (`PomodoroPastSpec`, `PastStackPos`),
`src/native/capture_language/tests/past.rs`,
`tests/cli/capture/pomodoro_past.rs`.

Shape:

```text
x=E[!][=X] [work-log entry]
```

- `E` is empty (default 5 blocks = 25 min), a block count, a bare name, or
  count+name in either order (`x=2fix` ≡ `x=fix2`). `#` only for names a bare
  spelling cannot express; `#"…"` exact literals allowed. A dash anywhere in
  `E` is a teaching error ("past work has no offset").
- `!` before the second `=` is edge-repair authorisation against older closed
  rows. `=X` is the existing close-selection grammar (including Work Log).
- A maximal consecutive run of `x=` items is one stack. With `T = ceil5(now)`,
  the rightmost member ends at `T`; earlier members fill adjacent windows
  backward in typed order (`compute_past_stacks` suffix sums;
  `compute_preflight` does pure time math, no ledger read).
- Each member closes at `C = min(window end, now)`. Target resolution:
  unnamed → next future placeholder (MEET-first refuses); named → open
  untimed placeholder in place, fresh "again" row for a completed-only match,
  or a created row for an unknown name; open timed matches always refuse.
- The recorded row is filed chronologically among completed rows
  (`file_recorded_block` via `ledger_place::closed_insert_at`).
- Overlap guard (`preflight_overlaps` + `classify_closed_row`) checks the
  whole-stack union against pre-stack history as half-open intervals:
  touching endpoints are fine; open-row overlap always refuses (`!` never
  helps); a closed row that would leave one nonempty piece after subtracting
  the union is trimmable with `!` (trim staged before any member records);
  erased/split rows always refuse; stray `!` with no closed overlap is an
  error.
- Editor and execution share the lexer (`past.rs` header comment); completion
  offers `pomodoro_past_name` after `x=` / `x=#` / `x=<D>#` and inside
  literals, ending the replacement before repair `!`, the second `=`, or
  `@<D>`. Teaching errors that mention `~` today all point it into the close
  part: `x=~2 → x==~2`, `x=3~2 → x=3=~2`, `x=build~2 → x=build=~2`.
  Any gap-anchor design must rewrite exactly those rows.

## 2. Decoding the proposal (with arithmetic check)

Proposed: extend `<E>` with an optional `<e>` suffix placed **before** the
repair `!`, where `<e>` is `~`, `~<n>[+]`, or `~~`.

Setup in the request: completed `0730-0800`, `0830-0900`; future CHORE, READ;
now `0913` ⇒ `T = ceil5(0913) = 0915`. Type (4) = `0900-0915` (15 min).

| Typed | Parsed as | Window | Check |
| --- | --- | --- | --- |
| `x=~=!1` | `E="~"`, no repair, close `!1`, default 5 blocks start-anchored at 0900, truncated at `T` | `0900-0915` | matches request |
| `x=read2~=!1` | `E="read2~"` (READ, 2 blocks), close `!1` | `0900-0910` | matches |
| `x=2~1!=!1` | 2 blocks, anchor `~1`, repair, close `!1`; `~1` = last completed `0830-0900`, start-anchored | `0830-0840`, old row → `0840-0900` | matches; this is exactly the existing "trimmable left edge" fate |
| `x=2~1+!=!1` | same but `+` = end-anchored | `0850-0900`, old row → `0830-0850` | matches ("trimmable right edge") |
| `x=2~2=!1` | anchor `~2` = next gap backward = `0800-0830`, start-anchored | `0800-0810` | matches |
| `x=2~2+=!1` | same gap, end-anchored | `0820-0830` | matches |

So the six examples are mutually consistent under this reading:

- `~` ≡ `~0`: trailing-gap (type 4), **start**-anchored, truncated at `T`.
- `~n` without `+`: window starts at the target block's start.
- `~n+`: window ends at the target block's end.
- `~~`: leading-gap (type 1), stipulated end-anchored (behaves as `+`).
- `~+` is deliberately unsupported because end-anchored-at-`T` is already
  today's default behaviour.

Gap-block model (`<n>`): `0` = type (4); `1` = last completed type-(2) block;
`≥2` = walk backward over alternating type-(2) completed spans and type-(3)
inter-pomodoro gaps. Type (1) is reachable only via `~~`, not via a number.
That last point needs a decision (see §5.3).

## 3. Gap enumeration: the algorithm to specify

No such concept exists in the tree today; it must be built. Recommended
definition (pure function of today's `## Pomodoros` timed rows + `T`):

1. Collect timed rows with `collect_timed_rows`-equivalent parsing
   (`HHMM-HHMM`, skip zero-length, wrap genuine midnight-enders over 1440).
   **Include open timed rows as occupied** for gap-boundary purposes
   (they still trigger the existing open-row refusal on overlap).
2. Sort occupied intervals by start; merge touching/overlapping ones for
   boundary purposes only (do not rewrite the ledger).
3. Gaps within `[0000, T]`:
   - type (1): `[0000, first_start)` if `first_start > 0`, else empty/absent.
   - type (3): each `(prev_end, next_start)` with `next_start > prev_end`.
   - type (4): `(last_end, T)` if `T > last_end`, else empty. If there are no
     timed rows at all, the whole `[0000, T]` is one gap: treat it as type (4)
     for `~` and refuse `~~` as "same gap, use `~`" (see §5.4).
4. Numbering for `~n`: `~0` = type (4) (must be nonempty, else refuse);
   `~1` = last completed (type 2) span; `~2…` = alternate gap/completed
   walking backward in time. Completed spans are individual ledger rows, not
   merged runs: if two completed rows touch (`0800-0830`, `0830-0900`), there
   is no type-(3) gap between them and numbering simply visits consecutive
   completed rows.
5. `~~` = type (1), end-anchored; refuse when empty ("nothing before the
   first session") or when it would start before midnight (standard midnight
   gate).

Edge cases the spec must nail down (all currently unspecified):

- Empty type (4) (`T == last_end`): `~` refuses ("no rest gap; the day is
  full to `T`"). This is the correct behaviour, not a spill backward.
- `~n` past the oldest block: refuse with the valid range
  ("only N targetable blocks today: `~0…~N` and `~~`").
- Zero-length gaps (touching rows) are not targetable and consume no number.
- Wrapping midnight-enders (`2345-0000`): normalise with the existing
  `+1440` convention before sorting.
- Other day files are never consulted (matches today's rule).

## 4. Grammar design

Recommended `E` grammar (extends `validate_past_e`, which currently rejects
any `~`/`-`/`*`/`!`-trailing rest in `E` via `past_rest_error`):

```text
E      := Base Anchor? Repair?
Base   := "" | Count | Name | Count Name | Name Count   (as today)
Anchor := "~" | "~~" | "~" N "+"?                      (N = positive integer)
Repair := "!"
```

Notes:

- Anchor attaches to the whole base: `read2~`, `2~1`, `2~1+`, `~~` are all
  `Base + Anchor`. `x=~` is `Base="" + Anchor="~"`.
- `~+` (plus with no number on the trailing gap) is refused with a teaching
  error pointing at the bare form ("`~+` is just `x=…`: the trailing gap
  already ends at `T` — drop the `+` / add `!` for repair").
- `~~` takes no number and no `+` (`~~` already implies end-anchored);
  `~~3` / `~~+` refuse with rewrites.
- `N = 0` is refused in the numbered form ("write `~`, not `~0`").
- The `#` / literal / bare-name byte rules are unchanged and apply to `Base`
  before the anchor; `-` inside a `#`/literal name (e.g. `#deep-work`) is
  still name content, never an anchor.
- `split_past_token` needs no change (it already splits `E` from repair/close
  correctly); `validate_past_e` peels a trailing `Anchor` before the existing
  count/name logic, records it on the spec, and `past_rest_error`'s
  `~`-branch must stop teaching `x=~2 → x==~2` for anchor-shaped rests while
  keeping the close-part teaching for genuine drop lists.

### The `~` overload is manageable but must be taught carefully

`~` already means "drop Task Links" in two places: `x~<K>` (close) and
`=~<K>`-family, plus `~note:id` / `~~note:id` task-relation links elsewhere.
The new anchor reuses the same glyph inside `E`, where `~` is currently
always an error. Because the `E` / close split happens at the second `=`,
`x=2~1=!1` (anchor + drop-close) parses unambiguously today at the token
level. The risk is human, not grammatical: users must learn that `~` before
any `=`/`!` is a *place* anchor while `~` after the second `=` is a *link*
drop. Mitigation: keep the glyph (it is the only spare, typeable, shell-safe
sigil in this family and the proposal's `-`→`~` typing argument is sound),
but make every error message name the side explicitly ("anchor `~1` goes
before `!`; drop `~2` goes after `=`").

## 5. Semantics: recommended resolutions (with adjustments)

### 5.1 Anchoring direction (agree with proposal)

- No anchor: end at `T` (unchanged).
- Anchor without `+` (including bare `~`): start at the target block's start.
- Anchor with `+` (including stipulated `~~`): end at the target block's end.
- Duration still comes from the block count (default 5). Direction only
  chooses which edge of the target block pins the window.

### 5.2 Truncation vs refusal **(ADJUSTMENT)**

- Bare `~` (trailing gap): start-anchored, **truncate at `T`** when the
  requested blocks overrun it (proposal's rule; keep it — `T` moves with the
  clock, so a trailing placement that fit at `:13` would spuriously refuse at
  `:14` otherwise). Report the truncated minutes in JSON/human output.
- `~n` / `~~` into a bounded gap or completed span: **refuse on overrun**,
  never spill into the neighbour. Spilling would silently rewrite history the
  user did not name. Error should state the target block's span and the max
  blocks that fit ("`~2` is `0800-0830` (6 blocks); `x=8~2` needs 8 — use at
  most `x=6~2`").
- `~~` overrun that would cross midnight: standard midnight-gate refusal.

### 5.3 Numbering stability and the leading gap **(ADJUSTMENT)**

The proposal's backward numbering (`1` = last completed, `2…` = walk back
over gaps and spans) is the weakest part of an otherwise good plan: numbers
shift every time the day fills, `~~` sits outside the numbering, and there is
no way to name the leading gap positionally. Keep it (it matches the
examples and is compact), but:

- Document that numbers are **ledger-relative at execution time**, preview
  them in `capture-parse` / `--dry-run`, and include the resolved target span
  in the refusal/help text.
- State explicitly that `~~` is *not* `~<k+1>`; it is a named alias for the
  leading gap. If a future iteration wants positional stability, add absolute
  `HHMM` placement then — do not renumber now.
- Refuse `~n` with `n` larger than the targetable count, listing the valid
  range. Never wrap or clamp.

### 5.4 Empty-day and degenerate ledgers **(ADJUSTMENT)**

- No timed rows: `~` targets `[0000, T]` start-anchored+truncated (degenerates
  to "record from midnight", subject to the midnight gate — in practice users
  will pass an explicit small count). `~~` refuses as "same gap — use `~`".
  `~n≥1` refuses ("no completed sessions yet").
- Type (4) empty (`T == last_end`): `~` refuses; the rewrite is today's
  default (`x=…` with no anchor would also touch, so the real advice is
  usually "wait for the next boundary or pick `~1` with `!`").
- Type (1) empty (first session starts at midnight): `~~` refuses.

### 5.5 Stacks **(ADJUSTMENT — the load-bearing one)**

Today's stack math (`offset_blocks` suffix sums in `compute_past_stacks`,
contiguous `[T−span, T)` windows in `compute_preflight`) is incompatible with
anchors: an anchored member's window is a function of the ledger, not of its
stack neighbours. Options:

- (a) Refuse mixed stacks (any stack containing an anchored member fails).
  Simplest, but breaks `x=2~2=… x=3` two-gap backfills in one draft.
- (b) **Resolve each anchored member independently; unanchored members keep
  today's contiguous-from-`T` layout; check the union as today.**
  Recommended. Concretely: `compute_past_stacks` leaves anchored members out
  of suffix sums (their `offset_blocks` is 0 / ignored); `compute_preflight`
  gains a ledger-dependent pass that maps each anchor to `(start, end)` and
  then applies the existing union + `classify_closed_row` + per-member `!`
  rules unchanged. The trim/stage pipeline (`stage_trim_plans`,
  `record_one_member`, `file_recorded_block`) already handles arbitrary
  windows — the examples in §2 are exactly its existing trimmable fates — so
  no change is needed there beyond feeding it anchored windows.
- Either way, two anchored members targeting overlapping windows must refuse
  as member-vs-member overlap (extend the current history-vs-member check with
  a member-vs-member pass; today's code never needs it because stack windows
  are disjoint by construction).

### 5.6 Repair `!`, open rows, MEET, filing, close part (no change)

- `!` keeps its exact current meaning: authorise trimming a closed row's edge
  when the anchored window takes it; required on overlapping members, error
  on non-overlapping ones. The §2 examples (`2~1!` trims left, `2~1+!` trims
  right) fall out of `classify_closed_row` with no new fate kinds. Erase/split
  still refuse even with `!`.
- Open timed rows (including the running session and future timed rows)
  refuse on overlap; `!` never helps. Anchors do not exempt this.
- Target resolution (placeholder / again / created), MEET-first refusal,
  chronological filing, `C = min(window end, now)` close clock, and the full
  `=X` close grammar are unchanged. `x=2~1!=!1`'s two `!`s (repair + complete)
  already lex distinctly; keep that.
- Midnight gate applies to anchored windows as today.

## 6. Editor, completion, and the mac-capture `-`→`~` rule

- `capture-parse` / editor must resolve and display the anchored window
  (target span + resulting `HHMM-HHMM`) — this is the beauty requirement. An
  anchor that cannot resolve (bad `n`, empty gap, overrun) is
  `invalid_pomodoro_past` with the same message execution prints.
- Completion: `pomodoro_past_name` behaviour unchanged; a cursor on the anchor
  (`~`, digits, `+`) returns empty success like the count/`!` today. Consider
  offering gap candidates (`~`, `~1…`, `~~` with resolved spans) as a
  follow-up, not in v1.
- **Dash replacement (ADJUSTMENT):** implement in bob-mac-capture as a
  position-aware keystroke transform, not a grammar alias:
  - Replace `-` with `~` only when the caret is inside an `x=` token's `E`
    anchor position (after a count/name, before any `!`/`=`/whitespace) and
    the resulting `~…` is anchor-shaped (`~`, `~~`, `~<digits>[+]`).
  - Never touch `-` inside `#`/literal names (`#deep-work`), close-part text,
    task text, or non-`x=` tokens; never rewrite `x=3-1` (offset-shaped) into
    an anchor — that stays a bob-cli teaching error.
  - bob-cli itself accepts only `~`; dash-in-anchor-position teaches the
    `~` rewrite (`x=2-1 → x=2~1`, `x=- → x=~`, `x=-- → x=~~`), extending the
    existing "past work has no offset" row rather than contradicting it.
  - This scoping answers "when appropriate" precisely and avoids turning the
    mac app into a second grammar.

## 7. Critique: is this a good idea?

**Yes — with the adjustments above.** Strengths:

- Fills a real hole. Backfilling a missed mid-day session today requires
  computing `T − offset` block arithmetic by hand and usually a forensic trim.
  Anchors name the *intent* ("first 10 min of the last session's slot",
  "the 0800 gap") instead of the arithmetic.
- Reuses the entire overlap/trim/filing machinery. The hardest parts (union
  check, edge trims, chronological insert, close-at-own-clock) need no new
  fate kinds; the new code is a gap-enumeration pass plus window pinning.
- Glyph choice is defensible: `~` is the only spare sigil in the `x=` family
  that is unshifted, shell-safe-ish (still quote in zsh), and already
  time-adjacent in users' minds (`~` ≈ "around/approximately").

Weaknesses and risks (why the adjustments matter):

1. **Number instability.** `~2` means something different after every
   recording. This is inherent to positional back-references (same critique
   applies to `x~<K>` drop lists, so it is at least consistent with the
   family). Mitigate with preview-always (`capture-parse`, `--dry-run`,
   editor inline window) and resolved-span JSON.
2. **Silent-history-rewrite risk.** Any anchor+`!` rewrites a closed row.
   Today's `!` already does this, but anchors make it easier to name the
   wrong slot. Keep erase/split refusals, keep per-member `!` strictness, and
   print each trim once as a warning (existing behaviour).
3. **Discoverability.** `~`/`~~`/`~n+` is a lot of micro-syntax. The docs
   table (§2 of this report) plus three idioms (`x=~` for "rest of the gap",
   `x=2~1!` for "re-take the head of the last slot", `x=2~~` for "dawn
   backfill") should lead; the full matrix follows.
4. **Stack interaction.** The proposal never mentions stacks; shipping anchors
   without §5.5 would silently corrupt the contiguous-stack invariant. The
   independent-resolution rule fixes it.

### Alternatives considered (and why not to take them instead)

- **Absolute placement (`x=0830-0840=…`).** More stable and self-describing,
  but a bigger grammar addition (new token shape, new validation, clock
  parsing) and it abandons the "name the gap" ergonomics. Recommend as a
  *later* complement, not a substitute: anchors for "the gap I mean", absolute
  times for "the minutes I mean".
- **Gap picker UI (`x=` + picker).** Nicer for discovery, but requires
  interactive flow in two clients (CLI + mac app) and breaks the one-line
  capture idiom. Recommend as a completion follow-up (gap candidates), not v1.
- **Relative-ago syntax (`x=-30m`).** Familiar, but collides with the retired
  `-` offset family that the grammar deliberately teaches away from, and it
  reintroduces the arithmetic the proposal removes. Reject.
- **Do nothing (manual `!` trims).** Keeps the grammar small, but leaves the
  backfill workflow forensic. Reject — the need is genuine and the
  implementation reuses existing machinery.

## 8. Recommended solution (v1 scope)

1. **Grammar + model.** Add `Anchor { kind: Trailing | Leading | Numbered(n),
   pin: Start | End, raw }` to `PomodoroPastSpec` (new JSON `anchor` object;
   keep `blocks`/`repair`/`close`/`stack` shapes). Peel it in
   `validate_past_e` before count/name logic; update `past_rest_error`,
   `past_suffix`/`past_close_rewrite` helpers, and the `~`-mentioning teaching
   rows. `~~` implies `pin: End`.
2. **Stacks.** Anchored members opt out of suffix-sum offsets
   (`compute_past_stacks`); document that one anchored token = one placement.
3. **Preflight.** New ledger-dependent gap pass (sorted occupied intervals →
   type 1/3/4 gaps + numbered completed spans) feeding window computation;
   unanchored members keep today's `[T−span, T)` math; bare `~` truncates at
   `T`, everything else refuses on overrun; midnight gate unchanged. Reuse
   `preflight_overlaps` / `classify_closed_row` / trim staging / chronological
   filing unchanged, plus a member-vs-member overlap pass.
4. **Surfaces.** `capture-parse` + editor resolve/show the window; completion
   treats the anchor span as empty-success; JSON reports `anchor` (typed form
   + resolved target span + truncation flag); human output prints the window
   and trims as today.
5. **Mac app.** Position-aware `-`→`~` keystroke transform per §6; no grammar
   change there.
6. **Docs + errors.** Extend the "Recording a past Pomodoro" table and the
   teaching-error table; three leading idioms first.
7. **Tests.** Unit: anchor lexing (all six §2 examples + `~+`/`~~3`/`~0`
   refusals + `#`-name/dash boundaries). CLI: gap fixtures mirroring §2
   (trailing truncate, head/tail re-take with trims, middle-gap start/end,
   overrun refusal, empty-gap refusal, out-of-range `n`, midnight gate,
   mixed anchored+unanchored drafts, member-vs-member overlap). Editor/parse
   parity + completion empty-success on anchor positions. Docs smoke tests.

## 9. Open questions for Bryan (non-blocking)

- Should `~~` also accept an explicit `+` (`~~+`) as a harmless alias, or
  stay strict (recommended: strict v1, the error teaches bare `~~`)?
- Should gap candidates appear in completion v1, or is parse-preview enough?
- Is member-vs-member overlap within one draft a refuse (recommended) or a
  sequenced trim? Refuse keeps the "whole batch rolls back" invariant simple.

---

*Evidence consulted: `docs/capture.md` (§Recording a past Pomodoro),
`docs/reference/capture-syntax.md`, `src/native/capture/pomodoro_past.rs`,
`src/native/capture_language/past.rs`, `src/native/capture_language/model.rs`,
`src/native/capture_language/tests/past.rs`,
`tests/cli/capture/pomodoro_past.rs`. No peer swarm reports were opened. The
bob-mac-capture repo was not opened (would require `/sase_repo`); its
contract claims above come from `docs/capture.md`'s "Bob Mac Capture …
delegates grammar, preview, completion, and vault writes to these `bob`
commands" statement and the prompt's own typing requirement.*

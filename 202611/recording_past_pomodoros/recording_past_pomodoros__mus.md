# Past pomodoros in one gesture: `x=<E>=<X>[!]` — research & design

Researcher: mus. Goal: decide how (and whether) to add a single-operation
"start and close a past pomodoro" syntax to `bob capture`.

Source of truth for current behavior: the capture grammar in
`src/native/capture_language/` (especially `item.rs` `session_equals_token` /
`parse_pomodoro_equals_item`, `tokens.rs` `parse_pomodoro_start_suffix`,
`close_selection.rs`, `close_log.rs`, `draft.rs` chain splitting), the planners
in `src/native/capture/` (`pomodoro_start.rs`, `pomodoro_close.rs`,
`capture_pomodoro_close/ledger.rs`, `meet_event_run.rs`
`start_block_minute`), and the workflow guide in `docs/capture.md`.
All claims below were read from that code, not inferred from the request text.

## 1. What the requested syntax means (verified against current semantics)

### 1.1 `x=<E>` is NOT just sugar for `=<E> x`

This is the single most important finding, and it is good news for the
proposal: the naive two-step does **not** work in general today.

- `=` anchors the **start** at `ceil(now)` and extends **forward**:
  `start_block_minute` returns `ceil((now − offset) / 5) · 5`, and
  `compute_pomodoro_start_range` adds the duration on top.
  At 0921, bare `=build` plans **0925–0950**, a session in the future.
  Closing it immediately at 0921 hits `close_timing` with
  `remaining = 950 − 921 = 29 ≥ 5`, and since the session has not started yet
  (`not_started`), the range collapses to a **zero-length 0925–0925** entry.
  So `=build x` today produces garbage, not 0900–0925.
- `=3-3 x` happens to work at 0921 (plans 0910–0925, `remaining = 4 < 5`, so
  the close keeps the range), but it is fragile: at 0920 the same input
  truncates to 0900–0920 (`remaining = 5`). The two-step is
  boundary-sensitive where the proposal is deterministic.

The proposal instead anchors the **end** at `ceil(now)` and extends
**backward**: `end = ceil(now / 5) · 5`, `start = end − 5·duration_units`.
That is a genuinely new time-anchoring rule, not a macro over existing
tokens. It deserves its own planner path (see §5), not a rewrite that emits
`=<E> x` internally — a rewrite would inherit the collapse/truncation bugs.

### 1.2 The `x=3 ≡ =3-3 x` identity holds (at 0921)

`=3-3`: offset 15 → `ceil((561 − 15)/5)·5 = 550` = 0910, duration 15 →
0910–0925. `x=3`: end `ceil(561/5)·5 = 565` = 0925, start `925 − 15` = 0910.
Identical. The identity generalizes: `x=<N>` ≡ `=<N>-<N> x` **whenever the
close keeps the range** (`remaining < 5`), which is true whenever
`now mod 5 ≠ 0`. At exact boundaries (`now mod 5 = 0`, e.g. 0920 or 0925)
the two-step truncates and the identity breaks — another reason to implement
`x=` natively with end-anchoring rather than documenting the equivalence.

### 1.3 Chained `x=` arithmetic (verified against the examples)

For a line `x=<E₁> … x=<Eₙ>` with durations `D₁…Dₙ` (in 5-minute units) and
`C = ceil(now / 5)·5`, item `i` gets

- `endᵢ = C − Σ_{j>i} 5·Dⱼ`
- `startᵢ = endᵢ − 5·Dᵢ`

Check at 0921 (`C` = 0925): `x=build@2 x=fix@3` → `D = [2, 3]`.
FIX: end 0925, start 0925 − 15 = 0910 → **0910–0925** ✓.
BUILD: end 0925 − 15 = 0910, start 0910 − 10 = 0900 → **0900–0910** ✓.
Lone `x=fix@2`: end 0925, start 0915 → **0915–0925** ✓ (matches the third
example). The "earlier items are offset by later durations" rule is exactly
right-to-left accumulation with a shared end anchor. Note this means ranges
must be computed in a **pre-scan of the whole line** before any writes:
left-to-right execution (the chain mechanism in `draft.rs`) cannot know
item 1's range until it has seen item 2's duration.

### 1.4 Where the example `x=2#fix=*3 apollo agent` bites

Tokenized under the proposal: prefix `x=`, `E = 2#fix` (duration 2 +
named target, mirroring the `=3#bugs` / `=bugs@3` duality), separator `=`,
`X = *3` (park task 3, reusing the close-selection lexer), trailing inline
entry `apollo agent`. Two things to flag:

1. `=*3` as a standalone whole-item token is currently a **retired-close
   alias** (`=*1` teaches `x*1`). Inside `x=<E>=<X>` it is just `X`, but the
   new lexer must claim the full `x=…` token **before** any retired-close
   teaching fires on a substring. Since `x=2#fix=*3` does not start with
   `=`, `retired_whole_item_close_rewrite` never fires on it today — the
   ordering is safe as long as the new parser runs next to
   `parse_pomodoro_equals_item`, not after prose fallback.
2. The entry-routing claim ("`apollo agent` goes to task 3's work log")
   needs a defined rule, because in close semantics an unnumbered inline
   entry goes to the **first worked task**, not to the parked one. Either
   the close-selection work-log rules apply unchanged (entry → first worked
   task, whatever that is under `*3`), or the proposal needs an explicit
   carve-out. I recommend **no carve-out**: `X` keeps byte-identical
   close-selection + work-log semantics, and the example's routing claim
   should be re-verified against whatever FIX's lineup actually is (§6,
   adjustment 4).

## 2. Grammar design

### 2.1 Proposed token grammar

```text
past_item  := "x=" E ("=" X)? "!"?
E          := start_shape_minus_dash      # mirrors =<X>: "", N, name, N#name,
                                          # name@N, ~K drops, @N timing —
                                          # but NO "-" forms at all (§6.2)
X          := close_selection            # byte-identical to x<X>:
                                          # [N][*P][!M][~K][@N], any order
"!"        := steal flag                  # trailing, exactly one
```

Disambiguation rules (all decidable left-to-right):

- `E` never contains `!` (the `=`-start family has no `!`; `start_drop_lex`
  rejects it), so the **first** `!` after `E` always belongs to `X` or to
  the steal suffix.
- `X` is lexed greedily with the existing `lex_close_selection`. A **single
  trailing `!` left over after `X`** is the steal flag: `x=3!` → `E=3`,
  empty `X`, steal. `x==1!2` → empty `E`, `X=1!2`, no steal. `x==!` →
  empty `E`, `X=!` (complete-all), no steal. `x=!` → empty `E`, empty `X`,
  steal (complete-all-with-default-duration is spelled `x==!`).
- `x=1!2` (no second `=`) is an error: `!` is illegal in `E`; teach
  `x==1!2`. This is the one shape users will trip on, so the diagnostic
  must name the rewrite, following the `=x#bugs → x =bugs` precedent.
- Bare `x=` (empty `E`, no `X`, no `!`) is legal: next/top future pomodoro,
  default 25 minutes. It is the past analogue of bare `=`.

### 2.2 Why `x=<E>` is safe to claim today

`session_equals_token("x=build")` returns `None` today:
`classify_whole_item_close` rejects `=` after `x`, the retired-close check
requires a leading `=`, and there is no leading `=` to strip. So `x=…` falls
through to ordinary task parsing — today `x=build` captures a task whose
text is `x=build`. Claiming the `x=` prefix is therefore a **small breaking
change** for anyone with tasks literally starting in `x=`, plus a collision
with close-with-entry only if someone writes `x =foo` (space — unaffected)
versus `x=foo` (no space — newly claimed). The migration cost is tiny, but
it is nonzero: document it, and keep `X`-less `x=<entry prose>` out — i.e.
once `x=` is claimed, `E` must lex as a valid start-shape or the whole item
errors with a teaching diagnostic; never fall back to "entry text".

### 2.3 The `!` suffix and the `!` inside `X`

Reusing `!` for "steal" while `X` already uses `!` for "complete" is the
riskiest lexical choice in the proposal. It is learnable only because of
the position rule (steal-`!` is always last, after a complete `X`), and it
composes poorly in exactly one case: `X` ending in complete-all (`x==!`)
followed by steal (`x==!!`). That reads terribly. Alternatives considered:

- (a) `%steal` / `~steal` directive — no; `~` is taken by drop lists.
- (b) A different sigil (`x=3?`, `x=3+`) — `+`/`?` have no session meaning,
  but inventing a third sigil for one flag is worse than overloading.
- (c) Keep `!`, accept `x==!!` as legal-but-ugly, and make the
  `!`-not-needed error message always print the de-`!`d spelling.

I recommend (c): the overload is positionally unambiguous, `!` already
means "forceful completion" in the close family so "forceful overlap
resolution" is a short step, and the ugly corner is rare (steal + complete-all
in one gesture). The editor's completion/preview should render the computed
ranges so users rarely need to hand-verify the parse.

## 3. Time model and overlap semantics

### 3.1 End anchor

`end = ceil(now / 5) · 5` in minutes, formatted mod 1440 exactly like
`compute_pomodoro_start_range` (`{:02}{:02}`). Midnight wrap reuses the
existing mod-1440 formatting; duration arithmetic reuses the
`checked_mul(5)` overflow guards ("Pomodoro start suffix is too large").
`D = 0` (`x=0…`)? `=`-starts allow `=0` (zero duration — check
`parse_pomodoro_start_suffix`: all-digits includes `0`). For `x=`, a zero
duration yields a zero-length range that overlaps nothing-or-everything
depending on endpoint convention. Recommend: **refuse `D = 0`** with a usage
error (a zero-length past pomodoro is never what was meant), diverging from
`=` deliberately and documenting it.

### 3.2 Overlap detection scope

"Existing past pomodoro" must be defined as: **every timed entry in today's
Pomodoros section** — open or closed, MEET or named — whose `[S, E)` half-open
interval intersects the new `[start, end)`. Half-open (end-exclusive) so that
back-to-back ranges like 0900–0910 + 0910–0925 do **not** count as overlapping
(the proposal's own chaining example produces exactly such adjacency and
must not self-trigger). Reasons for the broad scope:

- Future placeholders are untimed (`time_range: None`) and never collide.
- The running timed entry always intersects (its span covers now, and every
  `x=` range ends at `ceil(now)`) — which yields §3.3.
- MEET entries with event-run spans are timed entries; silently overlapping a
  meeting record would corrupt the calendar mirror. They must participate in
  detection, and `!` must be allowed to steal from them only with the same
  truncation rule (or refused — see §3.4).

Out of scope: other days' notes (past pomodoros are today's ledger only),
and untimed placeholders.

### 3.3 While a session is running

As shown above, any `x=` range ends at `ceil(now)` and the running session
covers now, so overlap is near-certain. Stealing from a **live** session
(resizing its start/end while it runs) risks corrupting the close path's
`planned vs closed` timing bookkeeping. Recommend: **refuse `x=` while a
timed session is running** with a teaching error (`close it with x first,
or record the past session after`). This is an adjustment to the request
(which is silent on the point), and it is the cheapest way to keep the
close-timing invariants intact. If that proves too strict in practice, the
relaxation is: allow `x=` while running only when fully disjoint — which
given the end anchor is almost never, so refusal costs nothing.

### 3.4 Steal semantics (`!`)

The request defines one case: new range strictly later than the old, truncate
the old's end to the new's start (0855–0920 + `x=3!` → old 0855–0910, new
0910–0925), recomputing the old's `[t:: Nm]` duration metadata. Generalize:

- For each overlapped old `[s, e)` and new `[S, E)`: since `E = ceil(now)`
  and olds are settled history, `e ≤ E` in every sane case, and `S < e`,
  `s < E` by overlap. Truncation `e := min(e, S)` is valid **iff `s ≤ S`**;
  otherwise the old starts strictly inside the new (old fully covered, or
  old straddles `S` from inside), and no end-truncation frees the range.
- Cases:
  - `s ≤ S < e` (old sticks out left): truncate old end to `S`. ✓ (`!` steals)
  - `S ≤ s, e ≤ E` (old fully covered): nothing to truncate — recommend
    **error even with `!`** ("`x=3!` fully covers 0915–0925; remove or shrink
    that entry first, or use a smaller block count"). Silently deleting or
    zero-lengthing a settled entry is data loss; merging is a different
    feature (cf. `=*` merge).
  - `S ≤ s < E < e` (old sticks out right, i.e. ends after `ceil(now)`):
    can only happen for a running/future-dated entry — but those are refused
    by §3.3 / have no time range. Treat as error.
  - Multiple overlapped olds: apply per-old; if **any** old is fully
    covered, the whole batch fails (atomicity, like all capture batches).
- Steal rewrites the old entry's `HHMM–HHMM` range **and** its `[t:: Nm]`
  duration, preserving its name, links, and sub-bullets. The human output
  must show both the new range and every rewritten old range; JSON gets a
  `stolen_from: [{name, line, before, after}]` block. Steals participate in
  the batch transaction: any later failure rolls everything back.

### 3.5 `!`-not-needed is an error (keep it, but mind the cost)

The request wants `!` without overlap to be an error. Keep this — it makes
steal opt-in and auditable, and the two-step flow (run bare → get overlap
error naming the conflict → re-run with `!`) is genuinely good UX for a
mutating operation. Cost: the syntax is non-idempotent and script-unfriendly
(a script cannot blindly pass `!`). Mitigate with diagnostics, not semantics:
both errors must print the exact retry spelling (`add ! to steal 10 minutes
from 0855–0920: x=3!`; `no overlap — drop the !: x=3`). Do **not** soften to
a warning: a warning that still steals trains users to ignore it, and a
warning that does not steal makes `!` meaningless.

## 4. Session resolution and link outcomes

### 4.1 Which session gets started-and-closed

Mirror `=` resolution exactly, executed at plan time against the pre-batch
ledger:

- Empty `E` → `next_future_pomodoro` (the "next/top future" of the request).
- Named `E` → open whole-slug match, else open prefix match, else completed
  match ("again" → new session with that name), else create-and-start —
  identical to `=name` (see `docs/capture.md` "Starting a named Pomodoro").
- `~K` drop lists in `E` filter the resolved session's queued lineup, same
  engine as `=~K`.
- Literal `#"NAME"` spellings work with key-equality semantics, same lexer
  (`lex_exact_name_after_hash`).

The synthesized session is written into the ledger as a **closed entry**:
completed checkbox, closed name derivation (R6 narrow — "close names follow
the work"), and the computed `HHMM–HHMM [t:: Nm]` range. Reuse the close
planner's entry-finalization with `closed_at := end` so `remaining = 0` and
the range is kept verbatim.

### 4.2 Where deferred/carried links go

A normal close moves unworked links into a fresh next placeholder
(continuation). A past close has no natural continuation, so the request's
silence here is a real gap. Recommend: **deferred links settle into the next
future placeholder** (creating one when missing), exactly as a normal close
would — the past session behaves like any close for link bookkeeping, only
the timing is backdated. Consequences to document:

- Chained `x=… x=…` items share **one** continuation: plan all ranges
  right-to-left, execute left-to-right in a single transaction, settle
  deferred links once. (Each item independently creating continuations would
  scatter links across phantom placeholders.)
- Parked (`*P`) / completed (`!M`) / dropped (`~K`) links behave exactly as
  in `x<X>`; only the "keep in progress" (`N`) set needs the continuation
  rule above.
- Work-log entries (inline + child bullets) attach per item under that
  item's worked set, using the existing `lex_close_inline_entry` /
  close-bullet lexers unchanged. Child bullets on a chained line attach to
  their line's `x=` item, mirroring `x =` + `- 1 wired the lexer`.

### 4.3 What is deliberately out of scope

- `#type` retyping, `@route` task creation, `%` directives, `&`/`*`/`~`
  relation markers, schedule/priority: an `x=` item contains **only** the
  token (+ entry text/bullets), exactly like `=`/`x` items today. Anything
  else is a shape error. (New tasks for a past session are created first,
  linked with `@route:id`, then referenced by the past close's lineup —
  no new syntax needed.)
- MEET interplay: no new MEET placeholders are created; the existing
  run-past-event / mid-meeting conflict warnings run read-only over the
  computed ranges. A past range overlapping a meeting warns (does not steal
  event runs, does not refile MEETs).
- Clock classification (`[off::]`/on-clock): reuse the start path's rule so
  the closed entry is stamped like any other close.

## 5. Implementation path (recommended)

1. **Lexer** (`src/native/capture_language/`): new `past_selection.rs`
   beside `start_selection.rs`/`close_selection.rs` implementing §2.1 on top
   of the shared primitives (`parse_pomodoro_start_suffix` for `E` minus
   `-` forms, `lex_close_selection` for `X`, existing range/offset helpers
   for diagnostics). Claim `x=…` in `session_equals_token` ahead of the
   `=`-family lexer (same "strict classifier first" pattern), extend
   `is_session_chain_token` + `is_chain_close_token` treatment in
   `draft.rs` so multi-`x=` lines split into chain items, and mirror the
   inline-entry owner handling so `x=<E>=<X> <entry>` lexes entry text.
   Both execution (`item.rs`) and editor (`editor_pomodoro.rs`,
   `capture-parse` spans, completion, `capture-rewrite`) go through the
   shared lexer — the codebase already enforces this pattern ("so a mistyped
   list reports the same message and byte width everywhere").
2. **Planner**: parameterize the clock. The cleanest seam is an explicit
   `[start, end)` + `closed_at = end` threaded through
   `plan_pomodoro_start_*` (skip `start_block_minute` when explicit) and the
   `capture_pomodoro_close` ledger close (which then keeps the range since
   `remaining = 0`). Named/empty resolution reuses `unnamed_start_target` /
   the `=` name-match code unchanged. Overlap scan + steal rewrite run as a
   pre-pass over today's timed entries inside the same batch transaction.
3. **Chaining**: pre-scan the line's `x=` items right-to-left for durations
   (§1.3), then execute left-to-right; one shared continuation (§4.2); one
   atomic commit.
4. **Output**: human lines print each created range plus every stolen
   rewrite (`0910–0925 BUILD · stole 0910–0920 from 0855–0920`); JSON adds
   `past: {start, end, duration_minutes, time_range}` per item and
   `stolen_from` for rewrites. Editor preview (`capture-parse`) must show
   **computed ranges before execution** — backdated writes without preview
   would be genuinely scary; this is the feature's "beautiful" requirement
   made concrete.
5. **Docs**: `docs/capture.md` grammar table + chaining section, `bob
   capture --help` contract line, and the multi-word-name/`#` rules
   (`=bugs@3` ≡ `=3#bugs` duality carries over to `E`). Consult the
   `cli_rules` and `docs` memory strands at implementation time for the
   help-text and front-door conventions.

Test surface to require: grammar unit tests (every `E` shape, both `@`
spellings, `!` placement, `x=1!2` teaching error, `D=0` refusal, `-` refusal
in `E`), chain arithmetic tests (2- and 3-item lines, adjacency is not
overlap), overlap matrix (left-stick / full-cover / multi-old / MEET /
running-refusal), steal tests (range + `[t::]` rewrite, rollback on
subsequent failure), and editor parity tests (spans, completion, rewrite).

## 6. Critique and adjustments to the requirements

1. **The feature is worth building.** The need (reconstructing today's
   ledger after the fact — forgotten timer, offline stretch, imported
   calendar blocks) is real, and §1.1 shows the current grammar cannot
   express it: bare-`=` + `x` collapses, and counted-`=` + `x` is
   boundary-fragile. Atomicity (one line, one commit, overlap-checked) over
   hand-editing the daily note is a genuine reliability win, and chaining
   with automatic offsetting removes the mental arithmetic that makes manual
   reconstruction error-prone.
2. **Exclude ALL `-` forms from `E`, not just `-<N>`.** The request bans
   `-<N>` (offset-only) but leaves `3-2` (duration-offset) ambiguous: does
   the offset shift the end anchor, the lookback, or nothing? Since duration
   already encodes lookback, any `-` in `E` is either redundant or
   contradictory. Refuse all of them with one teaching error. (Also note
   the `=`-start quirk `= -2` vs `=-2` must not leak into `x=` lexing.)
3. **Refuse `x=` while a timed session runs** (§3.3) instead of leaving it
   undefined. Near-certain overlap + live-timing bookkeeping = corruption
   risk for zero practical benefit.
4. **Re-verify the `*3 → task 3's work log` example claim** (§1.4.2): with
   unchanged close/entry semantics the inline entry goes to the first worked
   task, and parked-task work-log eligibility needs a ruling. Do not bend
   entry routing for this feature; fix the example.
5. **Full-cover stays an error even with `!`** (§3.4). Steal = truncate;
   truncation cannot free a fully covered range, and auto-deleting settled
   entries is never "stealing". Name the remedy in the message.
6. **Refuse `D = 0`.** Zero-length past sessions have no meaning; `=`'s
   tolerance of `=0` need not carry over.
7. **Half-open overlap** (§3.2): adjacency is not overlap, or the chaining
   example self-destructs. State the convention in docs and tests.
8. **Deferred links need the continuation rule** (§4.2) — the request's
   biggest functional gap. Without it, implementers will either drop links
   silently or scatter placeholders.

## 7. Recommended solution

Implement `x=<E>=<X>[!]` as specified, **with adjustments 2–8 above**, in
this order: (i) shared lexer + editor parity with range preview; (ii)
explicit-range planner seam reusing the start/close engines with
`closed_at = end`; (iii) right-to-left range pre-scan + left-to-right
single-transaction execution with one shared continuation; (iv) half-open
overlap detection over all of today's timed entries, steal-by-truncation
with full-cover refusal, running-session refusal, and both-error-messages
printing exact retry spellings; (v) human + JSON output showing created and
rewritten ranges; (vi) grammar-table docs and help-text updates.

Do not implement it as a rewrite to `=<E> x`, do not invent a new sigil for
steal, and do not bend work-log routing. The result is intuitive (end-anchor
+ lookback matches how people remember missed pomodoros: "the 25 minutes
ending now"), reliable (atomic, overlap-checked, preview-first), and small
enough in grammar surface to stay beautiful: one new prefix, two reused
sub-grammars, one flag.

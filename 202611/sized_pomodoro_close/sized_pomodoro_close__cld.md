# `<N>x`: close the running Pomodoro at a size

*Research report (cld) · 2026-11-08 · request: add an `<N>` prefix to the `x`
capture close so that `<N>` sets the session's size in five-minute blocks
before it closes (`2x!2` ≡ `-3 x!2` on a 25-minute session).*

## Bottom line

**Build it.** But define `<N>x` as *"close the running session as of the moment
it reached N blocks"*, not as sugar for the chain `-k x`.

- **It removes the subtraction.** The planned duration no longer matters: you
  need only the session's start and how long you actually worked.
- **It fits Bob's grammar.** `=3` opens a three-block session, and `3x` closes
  one at three blocks. As in `x=`, *time goes left of the operator and tasks go
  right*. Bob's Obsidian keys already put counts first (`N\p`,
  `N<Ctrl+Shift+M>`).
- **It fixes defects in today's workaround that I reproduced on master.**
  - `-3 x` closed 40 minutes after the session's new end still prints
    `ran 40m over`.
  - It stamps Work Log entries with the wall clock, not the stop time.
  - It classifies Event Tasks by the wall clock. That **completes a meeting the
    shortened session never reached** (§2.2).
  - It renders two preview cards for one intent.
- **Prose collisions are rare in practice.** 0 of 11,647 vault task lines start
  with `<N>x`, and 0 Work Log or task lines contain a standalone `<N>x` word.

How it works:

1. Bob rewrites the span to `[S, S+5N)`.
2. Bob runs the existing close **at clock `C = min(S+5N, now)`**. It goes
   through `plan_pomodoro_close_for_entry`, the explicit-clock entry point that
   `x=` past records already use.

Everything else (selection lists, Work Log grammar, names, carry, the clock
key) is unchanged.

I make eleven requirement adjustments, flagged in [§5](#5-requirement-adjustments).
The most important ones:

- Clock-dependent effects use the sized end (a deliberate deviation from strict
  `-k x` equivalence).
- `N` is limited to 1–2 digits. Three or more digits stay reserved for a future
  clock-time close.
- A size past "now" is cut at now with a warning.
- A size may also *lengthen* the session.
- `<N>x` is never recognized after inline Work Log text.

The recommended solution is in [§8](#8-recommended-solution).

## Evidence base

| Source | What it contributed |
| --- | --- |
| bob-cli `master` @ `59ba11a6`, built locally (`bob 0.5.0`, grammar 19) | Every probe below. The installed `bob 0.4.0` is grammar 16, so I did not rely on it |
| `docs/capture.md` | The close contract: `x` auto-decrement, overrun, Event Task clock, `+N`/`-N`, `=<X>`, `x=`, same-line chains, link closes |
| Source reading | `close_selection.rs` (`classify_whole_item_close`, `close_after_eq_parts`, `lex_close_selection`); `item.rs` (`session_operator_token`, `past_token_len`); `capture_pomodoro_close/ledger.rs` (`close_timing`); `capture_pomodoro_close/linked_tasks.rs` (`plan_pomodoro_close_for_entry`, `close_clock_for_entry`); `capture/pomodoro_past.rs` (the record path's explicit-clock close); `event_task.rs` (`CloseClock`, `classify`) |
| Bob Mac Capture source | Span categories (`CompletionRowContent.swift`), the close-list comma assist (`CaptureCloseTaskCommaAssist.swift`), and the close card (`CapturePomodoroClosePresentation.swift`) |
| bob-plugins docs | Vim count-prefix conventions (`N<Ctrl+Shift+M>`, `N<Ctrl+Shift+]>`, `N\p`/`N\P`). There is no counted Ctrl+Enter today |
| Vault scan (`~/bob`, read-only) | Collision counts, closed-session durations (last 40 daily notes), 5-minute alignment of spans |
| Memory | `decisions:close-selections-list-explicitly`, `decisions:event-task-links-close-by-the-clock`, `decisions:mac-capture-is-a-thin-client`, `decisions:bob-cli-releases-ride-a-daily-train`, `cli_rules.md`, `docs.md`, glossary (Pomodoro, Off-Clock Pomodoro, Work Log) |
| Prior research (unrelated request) | `research:202611/close_outcome_x_s_typing_aliases/close_outcome_x_s_typing_aliases__final.md`, the editor-only `x`→`!` / `s`→`*` aliases. It interacts with this feature (§7.1) |

No Swift was compiled and nothing was measured on the Mac.

## 1. What exists today

### 1.1 How `x` retimes a session

From the contract (`docs/capture.md` § Closing the running Pomodoro) and
`close_timing`:

- `remaining = end − now`, normalized into (−720, 720].
- If `remaining ≥ 5`, the end moves back by `5·⌊remaining/5⌋`. That is the
  earliest five-minute step at or after now.
- Otherwise the bytes stay untouched. **Bob never extends**, and an overrun is
  reported (`ran 7m over`).
- If the session has not started, it records a zero-length span with an
  `x0`-teaching warning.

What the close clock drives:

- The trim above.
- **Event Task classification**: `C = now` (`close_clock_for_entry` reads `now`
  directly).
- **Work Log timestamps**.
- The overrun/early report (`remaining_minutes`).

### 1.2 Neighbouring grammar

| Spelling | Meaning | Count slot |
| --- | --- | --- |
| `+N` / `-N` | Move the end N×5 later or earlier | after the sign |
| `++N` / `--N` | Shift the whole session | after the signs |
| `=<X>` | Start now for X blocks (`=3` is 15m) | after `=` |
| `x[<N>][*<P>][!<M>][~<K>][@<N>]` | Close; `<N>` = in-progress **task numbers** | after `x`, **taken** |
| `x=E[s][!][=X]` | Record a past session of E blocks ending now | after `x=` |
| `@r:id=x…`, `^r:id=x…`, `<text> @r:id=x…` | Link, then close | after `=x` |
| `+2 x`, `x =`, `-2 x wired it` | Same-line chains run left to right | — |

The suffix slot after `x` belongs to task numbers, so the prefix is the only
free slot that needs no new sigil. Bob already uses the "time left, tasks
right" principle in `x=`: *"Before the second `=` is when; after it are
tasks."*

### 1.3 What `<N>x` parses as today (grammar 19)

| Draft | Today |
| --- | --- |
| `2x!2`, `2x`, `5x`, `2x =`, `2x=3` | `task` (prose) |
| `2x faster builds`, `10x engineer` | `task` (prose) |
| `2X` | `task` |
| `^bob:foo=2x`, `@bob:foo=2x!1` | **error**: `` `=2x` has a close-shaped name; write `=2#x` to select it `` |
| `=2x` (whole item) | error, same message |
| `x fixed x` | **two items**: a close logging "fixed", then a second close |
| `x fixed x speedup` | one close logging "fixed x speedup" |

Two consequences:

- The link forms are already claimed as errors, so supporting `=2x…` there is
  collision-free.
- A bare `x` after inline Work Log text is already a chain close. `<N>x` must
  not inherit that rule (§4.2).

## 2. What `2x!2 ≡ -3 x!2` does today, and why the chain is not good enough

### 2.1 The arithmetic and the misleading report

Scratch vault: BUILD runs `0900-0925` with two links. `BOB_NOW=09:50`:

```text
$ bob capture --dry-run -- '-3 x!2'
[dry-run] ok would adjust  1/2  2026/20261108.md
  BUILD 0900-0925 (25m) to 0900-0910 (10m), -15m at line 7
  - [ ] (**0900-0910** [t:: 10m]) — BUILD

[dry-run] ok 2/2  would close … 0900-0910 (10m) · … line 7 (ran 40m over)
  1 [*] deferred Add support for x syntax bob.md ^capture-stop
  2 [*] → [x] Web capture bob.md ^web-capture
```

What goes wrong:

- **Arithmetic.** You must know the *planned* duration (25) and subtract
  (5 − 2 = 3). That number is not always 25. In the last 40 daily notes, only
  136 of 471 closed non-MEET sessions were 25 minutes (§3.2). MEET spans follow
  the calendar, and `=3` / `+2` change it too.
- **"ran 40m over"** is false. You just told Bob the session stopped at 09:10.
- **Two cards.** The panel shows an adjust card and a close card for one
  thought.
- **Work Log stamps.** `x!2 wired it` at 09:50 stamps `*2026-11-08 09:50*`, not
  09:10.

### 2.2 The Event Task defect

A MEET runs `0900-1000` with two meetings: Design review `0900-0930` and Vendor
sync `0930-1000`. You leave after the first meeting and close at 10:15:

```text
$ BOB_NOW='2026-11-08 10:15:00' bob capture --dry-run -- '-6 x'
[dry-run] ok would adjust  1/2  …  MEET 0900-1000 (60m) to 0900-0930 (30m)
[dry-run] ok 2/2  would close MEET 0900-0930 (30m) · … (ran 45m over)
  1 [*] → [x] **0900-0930** Design review … · ended 09:30
  2 [*] → [x] **0930-1000** Vendor sync … · ended 10:00
```

Vendor sync is **completed and counted**, even though the session span ends
when it begins.

- The close clock is `C = now = 10:15`, so the meeting classifies as
  `ended_inside`.
- The session's 30 minutes are then split evenly across both meetings' roots:
  *"Back-to-back meetings in one session still split its minutes evenly"*
  (`decisions:event-task-links-close-by-the-clock`).
- With the close clock at the sized end (`C = 09:30`), Vendor sync is
  `not_started`. It is deferred and carried, and Design review gets all 30
  minutes.

The chain cannot fix this, because chain items are independent: `x` does not
know that the `-6` before it meant "I stopped at 09:30". A first-class `<N>x`
can.

## 3. Is this a good idea?

### 3.1 For

1. **The arithmetic disappears in the right place.**
   - `-k` is relative to the *planned end*, which you often do not know.
   - `N` is relative to the *start*, which the Mac agenda and the ledger line
     both show, and to your own sense of how long you worked ("I got ten
     minutes in").
   - Every session span in the last 40 notes is 5-minute aligned (499/499), so
     `S + 5N` always lands on the grid.
2. **It is honest.** A sized close states when the session stopped. Bob can
   then stamp, classify, and report from that moment, which `-k x` cannot.
3. **It is coherent with existing grammar.**
   - `=3` / `3x` / `x=3` all use a block count.
   - "Time left, tasks right" (`3x!2`, like `x=3=!2`).
   - Count-first, like Bob's Vim-style Obsidian keys.
4. **Frequency is high.**
   - The prior x/s research counted ~12 closes/day (489 in 40 days).
   - 71% of non-MEET closes in the last 40 notes end at something other than
     25 minutes (§3.2).
   - Caveat: the vault records outcomes, not keystrokes. A short span can come
     from `x`'s own auto-trim or from a `=2` start, so the share of closes that
     needed explicit resizing is **not measured**.

### 3.2 Closed-session sizes (last 40 daily notes, 2026-09-30 → 2026-11-08)

| Minutes | 5 | 10 | 15 | 20 | **25** | 30 | 35 | 40 | 45 | 50 | 55 | 60 | >60 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Non-MEET rows | 61 | 92 | 76 | 28 | **136** | 10 | 17 | 13 | 5 | 27 | 3 | 7 | 12 |

- 471 non-MEET closed rows: 252 shorter than 25m and 83 longer.
- Two lessons:
  - The sizes people end at are small single-digit block counts (1–4).
  - Longer-than-planned sessions are common enough that `<N>x` should also
    **lengthen** (`7x`), not only shorten.
- The longest row was 360m (72 blocks), inside the proposed 1–99 range.

### 3.3 Against, and the mitigations

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Prose like `2x faster builds`, `10x engineer` starts closing the running session (with an inline Work Log entry!) | Low in practice | **0** of 11,647 vault task lines start with `<N>x`. The only standalone `<N>x` words are in mail and ref sources. Capital `2X` stays prose (the documented escape, as `X` is for `x`), and `2×` is prettier anyway. With no session running, the close errors instead of writing. Mark the commit `feat(capture)!`, as `x=` was |
| `x made it 2x faster` turning into two closes | Medium if unguarded | **Never** recognize `<N>x` after inline entry text (A7). Today `x fixed x` already splits, so this needs an explicit rule |
| `2x2` reads like "2 by 2"; prefix and suffix numbers mean different things | Learnability | The rule is "time left, tasks right". The editor colors the size with the session-operator highlight and the task lists with outcome colors. The close card spells it out (`sized 2x · in progress 2`) |
| Asking for more time than has passed (`7x` at 09:12) | Edge | Cut at now and warn, naming the largest size that fits (A5). Nothing records past now, as with `x=` |
| A two-feature race with the x/s aliases | Real but avoidable | The alias prefilter must learn `[0-9]{1,2}x` (§7.1) |
| One more close spelling to document | Low | One row in the syntax table, one subsection, one decision record |

**Verdict:** worth doing, with the semantics and guards below.

## 4. Design

### 4.1 Semantics

Let the running session be `[S, E)` and let `T` be now. For a size
`N ∈ 1..=99`:

1. **Size.** `E′ = S + 5N` (mod 1440, like `+N`). Rewrite the span to
   `[S, E′)` in its existing clock key (`[t::]` or `[off::]`), exactly as
   `±k` would.
2. **Pick the close moment.**
   - If `E′ − T ≥ 5` (the size ends in the future): **cut**. The close proceeds
     exactly like plain `x` at `T` (trimmed to the first step at or after now),
     with warning `pomodoro_close_size_cut`.
   - Otherwise the closed span is `[S, E′)` and the close clock is
     `C = min(E′, T)`.
3. **Close.** Run the ordinary close at clock `C`, with policy `Ordinary`, so
   the continuation and MEET placement behave as usual. This covers selection
   and explicit mode, Event Task classification with `(S, C)`, Work Log stamps
   at `C`, close names, carry, the continuation, and the clock key.
4. **Report.**
   - No overrun is reported: `remaining = E′ − C = 0` unless cut.
   - The output carries a `size` object (§4.4).

In one sentence:

> **`<N>x` closes the running session as if you had typed `x` the moment it
> reached N blocks, and unlike `x` it may also lengthen the session. Nothing is
> ever recorded past now.**

For a shrink this matches the user's equivalence `2x!2 ≡ -3 x!2`: same span,
same selection. The clock-dependent effects differ on purpose (A1).

```text
           S          E′ (= C)            E                    T (now)
 0900       0910                0925                 0950
  |==== 2x ===|·····trimmed·······|                     |
  [ closed span 0900-0910, 10m ]     (0910-0950 stays untracked;
                                      no "ran 40m over")
  Work Log stamps: 09:10 · Event Tasks classified at C = 09:10
```

### 4.2 Grammar (lexical, shared by `capture-parse` and `bob capture`)

A close token gains an optional count before the `x`:
`[<size>]x[<N>][*<P>][!<M>][~<K>][@<N>]`.

| Rule | Detail |
| --- | --- |
| Shape | `<size>` is 1–2 ASCII digits glued to a lowercase `x`. What follows the `x` must already close-classify (empty, or starting with a digit, `,`, `!`, `~`, `*`, `@`), so `2xx`, `2xa`, and `2x-ray` stay prose like `xx` |
| Value | 1–99 blocks. Leading zeros are accepted (`02x`), matching `=03`, `x=03`, and `+03` |
| `0x`, `00x` | Claimed teaching error, modeled on `x=0`: `` a closed Pomodoro needs at least one block: `0x` closes nothing; write `1x`, or `x0` to reset the session `` |
| Three or more digits (`100x`, `0910x`) | Claimed error: `` a close size is 1–99 five-minute blocks (`12x` is an hour) ``. Like the `x=~n` segment suffix, three or more digits stay **reserved for a future clock-time close** (`0910x` = "stopped at 09:10") |
| Capital `X` | `2X`, `10X engineer` stay prose (the escape) |
| Position | The first token of an item, or a token in a **leading** same-line session chain (`2x =`, `+1 2x`, `2x x=fix~`). **Never** after inline Work Log text: `x made it 2x faster` logs the text verbatim |
| Link closes | `@r:id=2x…`, `^r:id=2x…`, and `<text> @r:id=2x…` are sized link closes. Today these are errors, so nothing collides. The link step runs first, then the size, then the close |
| Whole-item `=2x` | Keep the claimed error, but teach both readings: `` `=2x` is not a start: write `2x` to close at 10 minutes, or `=2#x` to start a Pomodoro named X `` |
| `2x#bugs` | Same near miss as `x#bugs`; teach `2x =bugs` |
| `2x=3` | Teaching error: `` `x=` records a new past Pomodoro and takes its size after `=`; a size before `x` closes the running session: write `x=3` or `2x` `` |
| `2x0` | **Valid; a size always closes.** It never resets, the same way `x0!2` always closes. Result: sized, with every plain link deferred |

### 4.3 Spans and `capture-parse`

- **Span.** Extend the existing `pomodoro_close` span over the count:
  `2x!2` → `0-2 pomodoro_close`, `2-4 pomodoro_close_complete`. This mirrors
  `pomodoro_start` covering `=3` and `pomodoro_past` covering `x=3`.
  - Bob Mac Capture already maps `pomodoro_close` to the session-operator
    category, so an **unmodified app highlights the size correctly**.
  - The digits are not a list span, so the close-list comma assist
    (`CaptureCloseTaskCommaAssist.listSpanKinds`) never turns `12x` into
    `1,2x`.
- **Spec.** Add an additive `pomodoro_close.size` field:
  `{"raw": "2", "blocks": 2, "minutes": 10}`. It is omitted when absent, so
  unsized payloads stay byte-identical.
- **Human line.** `close     2x!2 (sized 10m · complete 2 · defer the rest)`.
- **Grammar version.** Bump `grammar` 19 → 20.

### 4.4 `bob capture` output

**Human.** One card, and the size in the headline caption:

```text
ok closed BUILD 0900-0925 → 0900-0910 (10m, −15m · 2x) · 2026/20261108.md line 7
  1 [*] deferred Add support for x syntax bob.md ^capture-stop
  2 [*] → [x] Web capture bob.md ^web-capture +1 Work Log
      *2026-11-08 09:10* — wired the lexer
  next: BUILD (created) at line 9 · carries 1 link
```

| Case | Headline caption |
| --- | --- |
| Shrink (`2x` at 09:50) | `0900-0925 → 0900-0910 (10m, −15m · 2x)` |
| Lengthen (`7x` at 09:50) | `0900-0925 → 0900-0935 (35m, +10m · 7x)` |
| Same size (`5x` at 09:50) | `0900-0925 (25m · 5x)`, with no `ran 25m over` |
| Cut (`7x` at 09:12) | `0900-0925 → 0900-0915 (15m, −10m)` plus `⚠ 7x asks for 35m, but BUILD has run 12m: closed at 0915 like x (3x fits)` |

**JSON.** Additive fields inside `pomodoro_close`:

```json
"size": {
  "raw": "2", "blocks": 2, "minutes": 10,
  "from": {"start": "0900", "end": "0925", "duration_minutes": 25,
           "time_range": "0900-0925"},
  "end": "0910", "as_of": "0910", "cut": false
}
```

Existing fields are filled exactly as the chain's close item fills them today:

- `planned` is the sized span (`0900-0910`, what `-3 x` reports for its close
  item).
- `closed` is the result.
- `closed_at` and `remaining_minutes` are computed at the close clock `C`, as
  `x=` already builds its summary at the member's own clock.

This keeps an **old Mac app truthful** with no update. Its close card renders
`planned`/`closed`/`remaining` and would show `0900-0910 · 10m · on time`. Had
`planned` stayed the original span, an old app would have rendered a
lengthened `7x` as `0900-0925 · 25m`, because it shows `→` only when
`decremented_minutes > 0`. A new app reads `size.from` and draws
`0900-0925 → 0900-0910 · 10m · sized 2x` with an "as of 09:10" chip instead of
"40m over".

### 4.5 Worked examples

BUILD runs `0900-0925` with links 1 and 2.

| Typed | Now | Result |
| --- | --- | --- |
| `2x` | 09:50 | `0900-0910 [t:: 10m]`; links keep ledger outcomes; Work Log stamps 09:10; no overrun |
| `2x!2` | 09:50 | Same span; task 2 completes; task 1 defers (explicit mode) |
| `7x` | 09:50 | `0900-0935 [t:: 35m]`: lengthened, no `+2` needed |
| `2x` | 09:07 | `0900-0910`: the end is 3 minutes ahead, the same round-up `x` does |
| `7x` | 09:12 | Cut: `0900-0915`, identical to `x`, with a warning naming `3x` |
| `2x wired the lexer` | 09:50 | Entry on task 1, stamped 09:10 |
| `2x =` | 09:50 | Close at 0910, then start the next session now (09:50). The 40-minute gap stays honest |
| `2x x=fix~` | 09:50 | Close BUILD at 0910, then record FIX from the tail (0910 onward, 25m by default) |
| `^bob:ready=2x` | 09:50 | Link `^ready` in as task 3, then close at 0910 |
| `2x0` | 09:50 | Sized close deferring every plain link (never a reset) |
| `6x` on the §2.2 MEET | 10:15 | `0900-0930`; Design review completes; **Vendor sync is `not_started`**: deferred and carried |
| `0x` / `100x` | — | Teaching errors (§4.2) |
| `2X faster builds`, `x made it 2x faster` | — | A task; a close logging "made it 2x faster" |

### 4.6 Errors and edges

- **No running session, several running, or no `## Pomodoros`.** Same errors
  as `x`.
- **Unparseable running range.** Refuse. A plain `x` leaves it as written with
  a warning, but a size cannot apply to a span Bob cannot read.
- **Session not started** (a MEET with a future start). This is the cut path,
  so it gets `x`'s zero-length record plus its `x0` hint. Mention the size in
  the warning.
- **Midnight.** The span is computed mod 1440, as `+N` does. 99 blocks
  (495 min) stays inside the close's (−720, 720] window.
- **Off-clock sessions.** The key is preserved through the size, then
  restamped by the close as usual.
- **Forced options** (`--route`, `%`, `s:<N>`, `$<N>`, …). Rejected exactly as
  on `x`.

## 5. Requirement adjustments

| # | Kind | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | **Changed** | Clock-dependent effects use the sized end: Event Task classification `C`, Work Log stamps, and the early/overrun report. The user's equivalence `2x!2 ≡ -3 x!2` still holds for the **span and selection** | §2.2: the chain completes meetings the session never reached, and reports a false overrun. Bob already closes past records at their own clock (`x=`) |
| **A2** | Widened | `N` may exceed the current size: `7x` lengthens a 25m session to 35m, as long as the end is not after now | 83 of 471 recent non-MEET closes ran longer than 25m. Otherwise `+k x` arithmetic remains |
| **A3** | Clarified | `N` counts from the session's **start**. It is an absolute size, not a delta | That is what makes the planned duration irrelevant |
| **A4** | Narrowed | `N` is 1–2 digits (1–99). Three or more digits are a claimed error, reserved for a future clock-time close (`0910x`) | Mirrors the `x=~n` reservation and keeps the cleanest future spelling of "stopped at 09:10" |
| **A5** | Added | A size ending after now is **cut at now with a warning** that names the largest size that fits | Nothing records past now. The start-pinned `x=` precedent cuts and reports. A refusal is the alternative (Q1) |
| **A6** | Added | `0x` is a teaching error pointing at `1x` / `x0` | Same shape as `x=0` |
| **A7** | Narrowed | `<N>x` is a session token only at item start or in a leading operator chain, **never after inline Work Log text** | `x fixed x` already splits into two closes, and "2x faster" is realistic Work Log prose |
| **A8** | Clarified | A size always closes: `2x0` never resets | Matches "explicit modifiers always close" |
| **A9** | Widened | Link closes accept the size (`^r:id=2x!1`) | "Every form of the close agrees" (close-names contract). Collision-free, because those spellings are errors today. Separable if unwanted (Q2) |
| **A10** | Added | Capital `2X…` is the documented escape | Parity with `X…` |
| **A11** | Added | One preview card with a `sized Nx` caption and no overrun; additive `size` JSON; `planned` = the sized span | Beauty, plus truthful rendering on old Mac builds |

## 6. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Status quo `-k x` / `+k x`** | Keep working, unchanged. It is the relative spelling, and it is still useful for "five more minutes". As the way to state "I stopped at N blocks", it loses on arithmetic and on the §2 defects |
| **Pure sugar**: lex `2x` into the chain `-3 x` | Reject. Simpler, but it inherits every §2 defect and needs the planned duration at execution anyway. The explicit-clock close is barely more code |
| **Size after `x` with a new delimiter** (`x/2`, `x:2`, `x'2`, `x2m`) | Reject. The digit slot after `x` is task numbers. A new sigil breaks "time left, tasks right" and is uglier to type |
| **Clock time** (`0910x`, or `x@0910`) | **Defer, and reserve** (A4). It is the least arithmetic for "I stopped at 9:10", but costs 4 keystrokes against 1, and the request is about size. `@` after `x` is already the in-progress alias |
| **Relative to now** (`x-3` = "stopped 15 minutes ago") | Reject for now. A third reference point to learn. `x-…` is a documented prose shape (`x-ray`), and it gives no new power once sizes exist |
| **A general absolute-resize operator** (e.g. `:2`, then chain `:2 x`) | Reject. More general, but nobody asked for an absolute resize of a session that keeps running. It reintroduces a chain where one token suffices |
| **Minutes instead of blocks** (`10mx`) | Reject. Every session operator (`=3`, `+2`, `x=3`, `N\p`) speaks in blocks. Mixed units are worse than a ×5 |
| **Obsidian parity** (`N<Ctrl+Enter>` on the running Pomodoro) | Optional follow-up. bob-plugins already uses Vim counts on many keys, but no one asked for this. Revisit if Bryan finds himself wanting it in the editor |

## 7. Interactions and risks

### 7.1 With the `x`→`!` / `s`→`*` editor aliases (same-day research)

That design is accepted but not yet shipped: grammar 19 still treats `xx` as
prose. It locates close tokens with `classify_whole_item_close` and gates Mac
forwarding on the line regex `(^|[ \t=])x`.

- **If `<N>x` lands without updating that prefilter, `2x` + `x` never reaches
  Bob.** `2xx⏎` would then file a task "2xx" instead of closing with `!`.
- Whichever feature lands second must:
  - widen the prefilter to `(^|[ \t=])[0-9]{0,2}x`;
  - teach the alias locator the size prefix;
  - add `2xx → 2x!`, `2x1s → 2x1*`, and `^r:id=2xs → =2x*` to the shared
    eligibility table.

### 7.2 Bob Mac Capture (thin client)

| Pairing | Behavior |
| --- | --- |
| New bob + old app | Works. The close mode and `pomodoro_close` span are known, the size digits highlight as session syntax, and the card reads `planned`/`closed` truthfully (A11). There is no size chip |
| New bob + new app | The card shows `0900-0925 → 0900-0910 · 10m · sized 2x` and an "as of 09:10" timing chip |
| Old bob + any app | `2x` is a task (today's behavior). The live preview shows task mode, so it is visible before Return |

The app never parses the size itself (`decisions:mac-capture-is-a-thin-client`).

### 7.3 Event Task vectors

`classify(span, S, C)` is unchanged; only the `C` a sized close passes is new.
So `tests/fixtures/event_task_close/vectors.json` (the Rust/JS lockstep fixture)
needs no new vectors. Add a CLI test for the §2.2 MEET instead.

### 7.4 Release and contracts

- Claiming `<N>x…` changes the meaning of previously valid prose. Mark it
  `feat(capture)!:` on the daily train, as `ce8f53b1` did for `x=`.
- JSON changes are additive.
- No version or CHANGELOG edits
  (`decisions:bob-cli-releases-ride-a-daily-train`).

### 7.5 Existing quirk (out of scope, worth a look)

Plain `x` on an overrun keeps the planned end but still classifies Event Tasks
at `now`. So a MEET `0900-0930` closed at 10:15 can complete a `0930-1000`
meeting from its lineup. That is defensible when you really did keep going.
The `-k x` chain is the case where it is plainly wrong, and `<N>x` becomes the
honest spelling. I would not change plain `x` in this work.

## 8. Recommended solution

**Ship `<N>x` in bob-cli as a first-class sized close, then let the Mac app
present it.**

### 8.1 bob-cli (one `feat(capture)!` change, grammar 20)

1. **Lexer.**
   - In `close_selection.rs`, add a size-aware classifier beside
     `classify_whole_item_close` that returns `(size, after_x)` for
     `[0-9]{1,2}x…`, plus the claimed-error shapes (`0x`, three or more
     digits).
   - Do the same for link suffixes in `close_after_eq_parts`, for `=2x…`.
   - Teach the session-chain tokenizer in `item.rs` to accept the sized token
     only in leading-chain positions (A7).
   - Carry `size: Option<u8>` on `PomodoroCloseSpec`, serialized only when
     present.
2. **capture-parse.**
   - Extend the `pomodoro_close` span over the count and add `size` to the
     spec.
   - Human line: `sized 10m`.
   - New diagnostics on `invalid_pomodoro_close`.
3. **Execution** in `plan_pomodoro_close_item`:
   - When `spec.size` is set, resolve the running entry and compute `E′`.
   - Stage the resized line with the same formatter `+N` uses
     (`format_adjusted_range`, clock key preserved).
   - Call `plan_pomodoro_close_for_entry(…, C, …, LedgerClosePolicy::Ordinary)`,
     where `C` is the moment from §4.1 as a `NaiveDateTime`. This follows the
     record path in `capture/pomodoro_past.rs`: stage the window, then close the
     explicit entry at its own clock.
   - Build the summary JSON at `C`, add `size`, and emit
     `pomodoro_close_size_cut` when cut.
4. **Human output.** The `· Nx` caption, no overrun on sized closes, and the
   cut warning with the largest fitting size.
5. **Tests.**
   - Lexer units for every row of §4.2.
   - `capture-parse` JSON cases.
   - CLI dry-run and commit cases for: shrink, lengthen, same size, cut,
     near-future round-up, inline entry stamp time, child bullets, `2x0`,
     `2x =`, `2x x=fix~`, link `^r:id=2x!1`, the §2.2 MEET, off-clock session,
     midnight, unparseable range, not-started MEET, `2X` prose, and
     `x made it 2x faster`.
   - Keep the existing assertions that `xx`, `X2`, and `x-ray` stay prose.
6. **Docs.** Read `docs.md` and `cli_rules.md` first. Then update:
   - `docs/capture.md`:
     - the syntax table row;
     - the example rows near the `x` examples;
     - the lifecycle table (new row: `<N>x` | close at a size | "Close as if
       `x` were typed when the session reached N blocks");
     - a new `#### Closing at a size` subsection;
     - the Event Task clock section (sized closes classify at their sized
       end);
     - the chaining and link-close sections;
     - the mnemonic: *"`=` starts now, `x` stops now, `Nx` stops at N blocks,
       `x=` records what already happened."*
   - The `capture` / `capture-parse` `--help` text; run `just docs-gen`.
   - `docs/reference/capture-syntax.md`.
   - Run `just docs-check`.
7. **Decision record.** Through `/sase_memory_write`, add *"A Sized Close Happens
   At Its Sized End"*. It applies to bob-cli and Bob Mac Capture.
   - **Claims:** A1–A11.
   - **Rejected:** the §6 alternatives, especially pure `-k x` sugar.
   - **Reopens when:** a clock-time close is wanted (A4), or prose collisions
     bite.

### 8.2 Bob Mac Capture (follow-up, gated by macOS CI)

1. Decode `pomodoro_close.size` with `decodeIfPresent`.
2. In `CapturePomodoroClosePresentation`, when `size` is present:
   - `sessionText` uses `size.from → closed` with a `sized Nx` caption;
   - the timing chip reads `as of HH:MM` (cut: `cut at now`) instead of
     early/over.
3. Add tests for shrink, lengthen, and cut payloads, plus an old-payload
   regression.
4. If the x/s aliases have shipped by then, apply §7.1.

### 8.3 Questions for Bryan

1. **Q1. Cut or refuse when the size ends after now** (`7x` at 09:12)?
   *Recommended: cut with a warning.* It matches `x=` and the result is exactly
   what `x` writes. A refusal is safer only if you would rather retype than
   accept `x`'s result.
2. **Q2. Sized link closes** (`^r:id=2x!1`) in v1? *Recommended: yes.* They are
   collision-free and keep "every form of the close agrees".
3. **Q3. Reserve `0910x`** for a future "stopped at 09:10" close?
   *Recommended: reserve now, build only if the size form leaves a gap.*
4. **Q4. A one-line `tip:`** when a `±k x` chain could have been `Nx`
   (`tip: 2x!2 closes at 10m in one step`)? *Recommended: yes, dim and
   human-only.* It teaches the new form exactly when it would have helped.

## Appendix: probes

All probes ran against a local build of `master` @ `59ba11a6` (`bob 0.5.0`,
grammar 19), with `capture-parse -R` or `capture --dry-run` against a scratch
vault and `BOB_NOW` set as shown.

- `2x!2`, `2x`, `2x faster builds`, `10x engineer`, `2x =`, `2x=3`, `2X` →
  `task`.
- `^bob:foo=2x`, `@bob:foo=2x!1`, `=2x` → close-shaped-name errors.
- `x fixed x` → two close items; `x fixed x speedup` → one close.
- `x made it +2` → one close logging "made it +2".
- `-3 x!2` at 09:50 → two cards, `ran 40m over` (§2.1).
- `-6 x` on the two-meeting MEET at 10:15 → both meetings completed (§2.2).
- `x` at 09:12 on `0900-0925` → `0900-0925 → 0900-0915 (15m, −10m)`.
- `+2 x` at 09:50 → `0900-0935 (35m) … (ran 15m over)`.
- `-3 x x=fix~` at 09:50 → close at 0910, then FIX recorded `0910-0935`.
- Counts: `x=03`, `=03`, and `+03` are accepted; `x=0` teaches `x=1`.

Vault scan (`~/bob`, read-only):

- 11,647 task lines, 0 starting with `<N>x`. The 7 standalone `<N>x` words are
  all in `mail/` and `.bob/ref-sources/`.
- 499/499 recent session spans are 5-minute aligned.
- Duration table in §3.2.

# Recording past Pomodoros with `x=`

Consolidated design report, 2026-11-04. It merges five independent reports
([cdx](recording_past_pomodoros__cdx.md), [cld](recording_past_pomodoros__cld.md),
[grk](recording_past_pomodoros__grk.md), [mus](recording_past_pomodoros__mus.md),
[gem](recording_past_pomodoros__gem.md)) with my own checks against bob-cli
`27feff87` (capture grammar 10), the installed `bob 0.4.0`, and the linked Bob Mac
Capture checkout. Where the reports disagreed, I resolved each disagreement against
the code, not by majority. No product code was changed.

**Question.** Should capture gain `x=<E>=<X>[!]`, which starts and closes a new
past Pomodoro in one step? If so, how should it be designed so it is intuitive,
reliable, and beautiful?

## Bottom line

**Build it, as its own operation rather than as a rewrite to `=N-N x`.** All five
researchers recommend the feature, and all five of your examples work as written.
The changes I recommend are about *how* it runs, plus one change to the syntax:

```text
x=<E>[!][=<X>] [work-log entry]
```

1. **The `!` (repair) goes right after `<E>`, not at the end.** At the end it
   collides with the close's own `!` wildcard (`x1!`, `x*3!`), so some combinations
   could not be typed at all. `x=3!` and `x==1!2` are unchanged.
2. **`!` only trims an edge of an older *closed* session.** It never splits one,
   erases one, or touches the running session.
3. **Consecutive `x=` items in one draft stack like same-line tokens.** That way
   each past session can carry its own Work Log.
4. **Each past session closes at its own clock, `min(end, now)`, and is filed in
   time order.** It never goes through the running-session start or close path.

Mnemonic for the docs (from cld): *`=` starts now, `x` stops now, `x=` records what
already happened.* Inside the token: *before the second `=` is time; after it are
tasks.*

## 1. Is this a good idea?

**Yes.** Forgetting to start the timer is the normal way timeboxing fails. Today the
repair is `=N-M x`, and the reports found five problems with it:

| Problem with today's workaround | Evidence |
| --- | --- |
| Mental arithmetic, plus running sums for a stack (`=2-5#build x =3-3#fix x`) | all five reports |
| `=3-3 x` while WORK runs **restarts WORK** at 0910–0925 (`⚠ overrode the running WORK`), then closes it | cdx and cld probes |
| It writes overlapping history with no warning, although Stats treats overlap as a ledger-health problem (`clock_overlap`, `detect_overlaps` in `src/native/stats/homes.rs:996`) | cdx and cld probes |
| An earlier stack member (`=2-5 x`, giving 0900–0910) closes at wall-clock 09:21. It prints `ran 11m over` and classifies Event Tasks as of 09:21 instead of 09:10 | grk, cld |
| Bare `=build x` writes a zero-length `0925-0925` session | grk, mus |

For a *single* token on a quiet ledger, the request's identity `x=3 ≡ =3-3 x` does
hold at every minute. The start rounds up, `ceil5(now − 5N) = T − 5N` with
`T = ceil5(now)` (`start_block_minute`, `src/native/capture/meet_event_run.rs:200`).
The close then sees `remaining = T − now`, which is between 0 and 4, so
`close_timing` never shortens the session. mus claimed the two-step truncates at
exact 5-minute boundaries; that is wrong: at 09:20, `=3-3` writes 0905–0920 and the
remaining time is 0. The equivalence breaks only for stacks and running sessions,
and that is exactly why this should be its own operation.

**Costs to accept on purpose:**

- **It is a grammar break.** `x=3` is captured as a task today; `capture-parse`
  reports body `x=3` with no Pomodoro mode, so gem's claim of "zero compatibility
  breaks" is wrong. Capitalized `X=…` and `x=` in the middle of a line stay prose.
  Ship it as grammar 11 with a `feat(capture)!` commit.
- **Whitespace matters.** `x =build` closes the running session and starts BUILD;
  `x=build` records a past BUILD. The guard (§5.5) makes most typos fail loudly:
  `x=build` refuses while it overlaps a running session, and `x =build` with
  nothing running fails with "no running Pomodoro".
- **A later token reshapes earlier ones.** The preview must show the whole stack,
  not just the token under the cursor.
- **`!` gains another meaning.** It already means close-complete, whole-item task
  complete, and Ensure-Next. The position rule in §4 keeps it unambiguous.

**Would I take a different approach?** No; the alternatives are in §8. Every report
considered the strongest rival, documenting `=N-M x`, and rejected it for the
reasons in the table above.

## 2. Where the reports disagreed, and what settled it

| Question | Positions | Resolution | Deciding evidence |
| --- | --- | --- | --- |
| Where the repair `!` goes | cdx, cld: right after `<E>`. grk, mus, gem: trailing, after `<X>` | **After `<E>`** | I ran `capture-parse`: `x1!` means "in progress 1, complete the remaining links" and `x*3!` means "parked 3, complete the remaining links"; `x!!` and `x!2!` fail with "use one `!` list". A trailing repair `!` therefore cannot follow a selection without changing its meaning. gem and grk even disagree about what `x=fix@2=*3!` means |
| The running session | cld, mus: refuse whenever any timed session is open. grk: `!` may trim it. cdx, gem: protect it; overlap refuses | **Protect it; refuse on overlap; touching is fine** | A start at 09:21 begins at **09:25**, because `start_block_minute` rounds up. So a session you just started sits right next to every `x=` window, and blanket refusal would block the common "start the timer, then backfill" sequence |
| How far a stack reaches | cdx, cld, mus, gem: one line. grk: consecutive `x=` items in the draft | **Consecutive items** (adjustment A5) | On one line only the last token can own an inline entry, because a plain word ends a chain (`capture-parse` help), so stacked sessions could never each get their own Work Log |
| Shape of a repair | gem: tail of the immediately preceding session only. grk: one session, remainder a multiple of 5. mus: shorten the end only. cdx, cld: each older session must keep exactly one nonempty piece | **cdx/cld rule** | Calendar MEET spans need not sit on 5-minute steps, and gcal may legitimately leave two overlapping MEETs (`docs/gcal.md`: "two closed MEETs may overlap; that is truthful") |
| Close clock and Work Log time | cdx, cld: `min(end, now)` for both. grk: `end` for meetings, real time for logs. mus: `end` | **`min(end, now)` for both** | The last window ends up to 4 minutes in the future (09:25 at 09:21). A meeting ending at 09:24 must not count as ended |
| Midnight | cdx, cld: refuse. grk, mus: wrap mod 1440 like starts | **Refuse** | cld probe: `=-3 x` at 00:05 writes `2350-0005` into today's note, which Stats reads as tonight |
| `~K` in `<E>` | mus, gem: keep it. cdx, cld, grk: drop it | **Drop it** | It would create two numbering domains in one token; the close's `~K` already removes links |
| JSON shape | cld: new mode `pomodoro_backfill`. cdx: `pomodoro_past`. grk: reuse `pomodoro_close` plus `past: true`. mus: a `past` object per item | **New mode `pomodoro_past` that embeds the close object** | The Mac decodes `mode` as a plain `String` (`CaptureModels.swift`), so a new mode is safe. An old Mac shown a plain `pomodoro_close` would render a misleading "closed with decrement" card |
| Work Log routing in example 3 | mus: the entry might go to the first worked task rather than task 3 | **It goes to task 3** | cdx and cld probes: under `*3`, task 3 is the only worked link |

## 3. Requirement adjustments (called out)

Each item changes or tightens what you asked for. Everything else is kept: the
one-step operation, all five examples, backward stacking, an overlap error by
default, a repair warning with `!`, and an error for an unneeded `!`.

**A1. Repair `!` binds to `<E>`: `x=<E>[!][=<X>]`.**
Only `x=<E>=<X>!` moves, to `x=<E>!=<X>`. A trailing `!` would be read as the
close's complete-the-rest wildcard. "Keep task 1, defer the rest, and repair" could
never be typed: `x=3=1!` already means "complete the rest", and the close lexer
rejects a second `!`. Peeling off the last `!` instead would silently change
`x==!` (complete everything) into "repair". After `x=3!`, a typo such as `x=1!2`
gets a teaching error: ``write `x==1!2` to complete task 2``.

**A2. `<E>` is a selector plus a duration, nothing else.**
Keep: empty, `D`, `name`, `#name`, `#"EXACT NAME"`, `D#name`, `name@D`. The
duration defaults to 5 blocks. Names that start with a digit still need `#`.
Refuse each of these with a teaching error:

- **All dash forms (`-N`, `D-N`, `D-`), not just `-N`.** The duration *is* the
  lookback, so any offset is redundant or contradictory.
- **`~K`.** Use the close's `x==~2`.
- **`0`.** A past session needs at least one block.
- **`=/` and `=*`.** Split and merge are not ways to start a past session.

`!` and `=` cannot appear in a valid Pomodoro name
(`is_pomodoro_selector_component`, `tokens.rs:555`; `=build!` and `=build=*3` fail
today), so both safely end `<E>`.

**A3. Running sessions are protected.**
`x=` never restarts, swaps, or trims an open timed session. If its window overlaps
one, it refuses, with or without `!`, and teaches the composed form `x x=3!`:
close what's running, then record. If the window only *touches* the running
session, as with a timer started at 09:21 (09:25–09:50) followed by `x=3`
(09:10–09:25), it proceeds. A named selector that resolves to the running session
also refuses. That case looks fine to the overlap check, but recording it would
hijack the live session.

**A4. Repair trims; it never splits or erases.**
For each older closed session, remove the union of the stack's windows. If exactly
one nonempty piece remains, `!` trims that session. If two pieces would remain (a
split) or none (an erase), the capture refuses even with `!`. Several older
sessions may be trimmed in one capture. `!` is checked per token: it is required on
exactly the tokens whose window overlaps a closed session as it stood *before the
stack*, and it is an error on any other token.

**A5. A stack is a run of consecutive `x=` items in one draft.**
This includes same-line tokens *and* blank-line-separated items, so this draft
records BUILD 0900–0910 and FIX 0910–0925, each with its own entry:

```text
x=build@2 wired the lexer
- 2 fixed the parser

x=fix@3 apollo agent
```

Under a same-line-only rule, these two items would both end at 09:25 and collide.
Getting per-session logs would then require overlay arithmetic (`x=build@5`, then
`x=fix@3!`). Any other item or operator ends the stack. A later stack sees rows from
an earlier stack as ordinary history, so the same rule applies everywhere. This
part can be split into a second phase if you prefer to ship same-line stacks first.

**A6. Each session closes at its own clock and lands in time order.**
Event Task classification and Work Log timestamps use `C = min(end, now)`. In a
stack, BUILD closes at 09:10 and FIX at 09:21. There is no "ran over" warning and
no decrement. The closed row is inserted chronologically using the existing
`closed_insert_at` logic (`src/native/task_status_hooks/settle.rs:610`, which
mirrors gcal), not the running session's "current slot". Carried links stay in the
source placeholder, which becomes the continuation where it already sits.

**A7. A window may not cross midnight.**
For example: ``x=6 would start before midnight (2350); record at most 2 blocks today: x=2``.
Backfilling an earlier day is a separate feature.

**A8. MEET and the calendar get no special treatment.**
A MEET target uses the typed duration (default 25 minutes), never the calendar
event run. An unnamed `x=` never prefers a MEET that overlaps the start block.
*My addition, to verify during implementation:* if the first placeholder is the
shared future-MEET placeholder (upcoming meetings), an unnamed `x=` should refuse
and ask for a name. Closing that placeholder would classify every meeting as
`not_started` and record an empty "MEET".

**A9. A `0` selection always closes; it never resets.**
`x==0` records the session and defers every link. This matches the note-bearing
`x0` and the documented rule that explicit modifiers always close. Resetting makes
no sense for a session that never ran. cdx preferred refusing a reset-only
selection; see the open questions.

## 4. Grammar

```text
past      := "x=" E [ "!" ] [ "=" X ] [ SP inline-entry ]
E         := "" | D | name | "#" name | "#" exact-literal | D "#" name | name "@" D
D         := [0-9]+            -- positive; default 5 blocks
X         := the existing whole-item close selection after `x`:
             [N][*P][!M][~K][@N], any order, same wildcards and diagnostics
```

Lexing rules:

- `x=` is recognized only at the start of an item or as a session-chain token,
  before prose fallback and before the close near-miss handling.
- Inside `<E>`, names and counts also end at `!` and `=`, outside quoted literals.
- Everything after the second `=` goes unchanged to `lex_close_selection`.
- Child bullets attach to the item's last `x=`, exactly as they attach to the last
  `x` today.

| Typed | `<E>` | Repair | `<X>` | Meaning at 09:21 (T = 09:25) |
| --- | --- | :---: | --- | --- |
| `x=` | default | – | plain | next placeholder, 0900–0925 |
| `x=3` | 3 | – | plain | 0910–0925 |
| `x=3!` | 3 | ✓ | plain | 0910–0925, may trim older history |
| `x=build=` | build | – | plain | same as `x=build` (the editor passes through this state) |
| `x==1!2` | default | – | `1!2` | keep 1, complete 2, defer the rest |
| `x==!` | default | – | `!` | complete every link |
| `x=!` | default | ✓ | plain | default window, repair allowed |
| `x=!=!` | default | ✓ | `!` | repair and complete everything |
| `x=3=1!` | 3 | – | `1!` | keep 1, complete the rest |
| `x=3!=1` | 3 | ✓ | `1` | keep 1, defer the rest, repair (cannot be typed under the trailing rule) |
| `x=1!2` | – | – | – | error: ``write `x==1!2` to complete task 2`` |
| `x=3-1` | – | – | – | error: ``a past Pomodoro always ends now; write `x=3` `` |

**Your examples under this grammar** (09:21, T = 09:25):

| Draft | Records | Notes |
| --- | --- | --- |
| `x=build` | BUILD 0900–0925 | default 5 blocks |
| `x=build@2 x=fix@3` | BUILD 0900–0910, FIX 0910–0925 | BUILD closes at 09:10, FIX at 09:21 |
| `x=2#fix=*3 apollo agent` ≡ `x=fix@2=*3 apollo agent` | FIX 0915–0925 | link 3 parked (stays as 🍅 history under the closed row, not carried) and logged; links 1–2 stay queued |
| `x==1!2` | next placeholder 0900–0925 | link 1 `[/]` and carried, link 2 completed, the rest deferred |
| `x=3!` with PLAN 0855–0920 | new 0910–0925; PLAN → 0855–0910 | `⚠ took 10m from PLAN` |

On "dismiss from the daily file": park (`*3`) is the only selection that both
removes task 3 from the live queue and lets it take a Work Log entry. The close
refuses entries for dropped (`~3`) links. Park keeps the worked link as history
under the closed row, which is the truthful record.

Useful idioms to document: `x=3 =` records the last 15 minutes, then starts the
next session at T with no gap. `x x=fix@3!` closes what's running and says its last
15 minutes were FIX. `x=email@1 x=build@3 x=fix@2` is a 30-minute timeline typed in
order.

## 5. Semantics

### 5.1 Windows

Take `now` once and drop the seconds. Let `T = start_block_minute(now, offset 0)`,
which is `now` rounded up to 5 minutes. For a stack with block counts `n₁ … n_k`,
token `i` covers

```text
[ T − 5·(nᵢ + … + n_k) ,  T − 5·(nᵢ₊₁ + … + n_k) )
```

That is exactly the start spec `=nᵢ-(nᵢ+…+n_k)`, so `x=3 ≡ =3-3` on the clock.
Because the stack lengths come from the text alone, `capture-parse` can report each
token's `offset_blocks` without reading the vault. Compute windows right to left,
then resolve targets and apply task effects left to right. Reversing the effects
would reverse completion order, continuation selection, and Work Log order.

### 5.2 Targets

- **Unnamed:** the first open untimed placeholder (`next_future_pomodoro`,
  `src/native/capture_pomodoros.rs:888`). If there is none, refuse:
  ``no future Pomodoro to record; name one: x=build``.
- **Named:** the same resolution as `=name`. An open placeholder match is used in
  place; a completed match starts a new "again" row; otherwise a new session is
  created. Literal `#"NAME"`, ambiguity errors, and near-match warnings all carry
  over.
- **Within a stack,** each token resolves against the staged state left by the
  tokens before it. So `x=2 x=3` records the same queue twice, and the second token
  takes the carried links. The preview must show this; naming the sessions avoids
  it.

### 5.3 Close

Run the existing close engine on an **explicit entry** at clock `C`. Today the
top-level `plan_pomodoro_close(_outcome)` (`capture_pomodoro_close/linked_tasks.rs:974`,
`:999`) calls `find_running_pomodoro` itself, while everything below it already
takes a `&RunningPomodoro` handle. Adding a variant that takes the handle is a
small, honest refactor, and it is needed anyway. With an adjacent running session,
the global lookup would report two open timed entries.

Reused unchanged:

- numbered progress, park, complete, drop, and wildcards;
- Event Task clock classification (with `S` = window start and `C`);
- close-name narrowing and continuation naming;
- dependency recovery and successor *offers*, which are never automatic links;
- Work Logs and lane effects;
- clock stamping from counted links (`[t::]` or `[off::]`).

Never reused: the start's override or swap, the MEET start-block preference, the
calendar duration, the reset branch, and `close_timing`'s decrement. That decrement
can't fire anyway, because `C ≥ end − 4`.

### 5.4 Placement

- The closed row goes where `closed_insert_at` puts it: after the last completed
  row that starts at or before it. Move that helper from `settle.rs` into a shared
  module.
- If the close carries links, the source placeholder stays where it is and becomes
  the continuation. If nothing carries, a used-up placeholder disappears, just as
  `=build@2-5 x` uses up an empty BUILD today.
- Completed rows stay before open ones, and no planned row ends up among completed
  ones.

### 5.5 The guard

Times are half-open `[start, end)`, so touching sessions do not conflict. The
candidates are every timed row in today's `## Pomodoros`: closed rows on either
clock, legacy unstamped rows, calendar MEET clusters, and open running rows. Stats
counts overlap across both clocks, so the guard checks both. Untimed placeholders
occupy no time. Rows on other days are out of scope.

| Situation (checked per token) | Without `!` | With `!` |
| --- | --- | --- |
| Window overlaps nothing, or only touches an endpoint | record | **error:** unneeded `!` |
| Overlaps an open (running) session | **refuse**; teach `x x=3!` | **refuse** (same) |
| Overlaps closed history, and each affected row keeps one nonempty piece after the whole stack | **refuse**; show the trim it would make | trim each row's edge, record, warn |
| The stack would cover a closed row completely | refuse | **refuse:** would erase it |
| The stack would punch a hole in a closed row | refuse | **refuse:** would split it |

Checking the whole stack at once matters. Take `x=build@2! x=fix@3!` against PLAN
0855–0920: checked token by token, BUILD (0900–0910) would look like a split of
PLAN, but the stack as a whole only trims PLAN's tail, to 0855–0900. Validate every
token against the history as it stood before the stack, before staging any trim.

A trim rewrites only the old row's span and its duration under the **same key**, as
`format_adjusted_range` already does (`src/native/capture/pomodoro_adjust.rs:1187`).
Example: `(**0855-0920** [t:: 25m])` → `(**0855-0910** [t:: 15m])`. It keeps the
row's name, checkbox, block ID, children, links, and clock key. It re-runs no close
effects. The remainder does not have to sit on 5-minute steps, because calendar
spans may not. Minutes are conserved: what the old row keeps plus what it gives up
equals its original length. *To verify during implementation:* that `bob gcal sync`
never rewrites a closed MEET cluster's span. The docs say sync writes rows once and
"does not clip" overlaps.

Refusal messages always spell out the fix. From cld, adapted:

| Case | Message |
| --- | --- |
| needs `!` | ``x=3 would take 10m from PLAN 0855-0920 (line 4); add ! to take it: x=3! (PLAN becomes 0855-0910)`` |
| unneeded `!` | ``x=3! takes no time from another session; drop the !: x=3`` |
| running | ``x=3 overlaps WORK 0900-0925, still running (line 5); close it first: x x=3!`` (include `!` only if still needed) |
| erase or split | ``x=6! would take all of CALL 0920-0925 (line 6); ! only trims a session's edge`` |
| midnight, zero, offset, `~K`, bang position, no target | as in A2, A7, A1, and §5.2 |

## 6. Output and preview: the "beautiful" part

**Human output** uses the verb *recorded* ("log" already means Work Log), one block
per token numbered like today's chains, and one `⚠` line per trim. A dry run says
`would record` and `would take`.

```text
✓ recorded BUILD 0900-0910 (10m) · 2026/20261104.md line 5 · 1/2
✓ recorded FIX 0910-0925 (15m) · line 6 · 2/2
  ⚠ took 10m from PLAN: 0855-0920 → 0855-0910 (15m) · line 4
  3 [/] Investigate agent crash · parked · not carried · +1 Work Log
  next: FIX at line 8 · carries 2 links
```

**The Mac preview** shows one "Record past work" card per stack (cdx). Rows are in
time order with exact ranges and the resolved source names. The timeline line
explains the result; it is not a control. Trims are amber, refusals are red, and
the permission is never conveyed by colour alone:

```text
Record past work                                              25m
09:00 ────── BUILD 10m ────── 09:10 ────── FIX 15m ────── 09:25
BUILD   09:00–09:10   10m
FIX     09:10–09:25   15m
        3  Investigate agent crash        Parked · +1 Work Log
PLAN    08:55–09:20 → 08:55–09:10         gives 10m
```

**JSON** adds an item mode `pomodoro_past`. It embeds the existing close object, so
clients can reuse their renderers:

```json
"pomodoro_past": {
  "raw": "x=fix@3!",
  "target": {"name": "FIX", "source": "placeholder", "line": 9},
  "blocks": 3, "repair": true,
  "pack": {"index": 2, "size": 2},
  "anchor": "0925",
  "window": {"start": "0910", "end": "0925", "minutes": 15},
  "closed_at": "0921",
  "trims": [{"line": 4, "name": "PLAN", "before": "0855-0920",
             "after": "0855-0910", "minutes": 10, "clock": "t"}],
  "close": { "…": "the existing pomodoro_close object" }
}
```

- **`capture-parse`** reports only text-level facts: `raw`, the name, whether it is
  a literal, `blocks`, `repair`, the stack index, size, and `offset_blocks`, and the
  `<X>` close spec. It adds the spans `pomodoro_past` (over `x=`), `pomodoro_name`,
  and `pomodoro_past_repair` (over the `!`, distinct from `pomodoro_close_complete`),
  plus the existing close spans over `<X>`.
- **`capture-complete`** offers names after `x=` or `x=#`. After `x=<E>=` it offers
  the **resolved target's** numbered lineup, not the running session's. That
  requires reading the vault.
- **The Mac** gates the new card on grammar ≥ 11 (`CaptureGrammarGate.minimumRevision`
  is 5 today). It never parses `x=` itself (decision
  `mac-capture-is-a-thin-client`).
- **Preview freshness.** `T` moves at each 5-minute boundary. The Mac should re-run
  its dry run when the clock crosses one. If that proves insufficient, add an
  internal `--expect-anchor HHMM` argument so submission refuses when the anchor has
  moved. That is a lighter version of cdx's full plan fingerprint, which I would
  hold in reserve.

## 7. Implementation plan

| Layer | Where (at `27feff87`) | Change |
| --- | --- | --- |
| Lexer | `EqualsToken` / `session_equals_token` (`capture_language/item.rs:3280`, `:3560`); `start_name_extent` (`bare_name.rs`) | New `PastPomodoro { selector, blocks, repair, close, len }` arm, claimed before prose and before the close near-miss handling. Names and counts end at `!` and `=`. One shared lexer serves execution, parse, complete, and rewrite, with exact UTF-8 ranges |
| Chains and stacks | `is_session_chain_token` (`item.rs:3789`); `is_chain_close_token`, `split_inline_close_tokens`, `push_capture_item` (`draft.rs:429–528`) | `x=` counts as a close, so it can own an inline entry and bullets. Assign stack ids across a line and across adjacent items |
| Model | `CaptureKind` (`capture_language/model.rs:69`) | `PomodoroPast { spec, stack }` |
| Planner | dispatch in `capture/plan.rs` (next to `PomodoroClose`, `:1064`) | A pre-pass computes windows and runs the guard for the whole stack. Then each token resolves its target, writes a closed row, and runs the close on that explicit entry at `C` |
| Close seam | `plan_pomodoro_close(_outcome)` (`linked_tasks.rs:974`, `:999`) | A variant that takes a `RunningPomodoro` handle and `now = C`. The old wrappers keep `find_running_pomodoro` |
| Placement | `closed_insert_at` (`task_status_hooks/settle.rs:610`) | Move it to a shared module and use it to place past rows |
| Trims | `format_adjusted_range` (`capture/pomodoro_adjust.rs:1187`) | Rewrite the span and duration under the same key, inside the same staged batch |
| Grammar and docs | `GRAMMAR_REVISION` (`capture_language/mod.rs:45`) → 11; `docs/capture.md` "Recording a past Pomodoro"; the syntax reference; `bob capture --help` | Read the `docs.md` and `cli_rules.md` reference memories first |
| Release | release train (decision `bob-cli-releases-ride-a-daily-train`) | `feat(capture)!`; no edits to the version or CHANGELOG |
| Record | decisions web, via `/sase_memory_write` | Claim: *"Past Pomodoros end now, never touch an open session, and `!` only trims an edge."* |
| Mac | Bob Mac Capture | Decode `pomodoro_past`, render the card, style the repair span; ship after bob |

**Phases.**

1. Lexer, `capture-parse`, grammar 11, and the text-level refusals (A1, A2, A7).
2. Single tokens: targets, the explicit-entry close seam at `C`, chronological
   placement, overlap refusal, and human and JSON output.
3. `!` trims and stacks, first on one line, then across adjacent items (A5).
4. Completion, the Mac card, the decision record, and docs.

**Tests to pin first** (shared vectors for parser, planner, and Swift decoding):

- **Your examples:** all five, with both FIX spellings producing identical plans.
- **Golden equivalence:** `x=N` against `=N-N x` on a quiet ledger, for every
  `<X>` shape.
- **Lexer:** every row of the §4 table.
- **Clock:** every minute in one 5-minute bucket; 09:20:59; 00:05; 23:58.
- **Stacks:** two and three tokens; adjacent items; a stack broken by another item.
- **Guard:** the whole §5.5 table; touching endpoints; several trimmed rows; the
  stack that would look like a split if checked token by token; off-clock and MEET
  victims.
- **Running session:** adjacent passes, overlap refuses, and `x x=3!` composes.
- **Close at its own clock:** an earlier stack member classifies a 09:15 meeting as
  `not_started`; no overrun warning.
- **Atomicity:** byte-identical rollback on every refusal, and dry run matching the
  real run at a fixed `BOB_NOW`.

## 8. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Document `=N-M x` (status quo) | Rejected: the five problems in §1 |
| Make `x=` a textual macro for `=E-E x` | Rejected: it inherits the running-session restart, the wall-clock close for stack members, and no overlap check |
| Trailing `!`, as requested | Rejected: collides with `x1!` and `x*3!`, and some combinations cannot be typed (A1) |
| `!!`, or a new repair sigil (`?`, `+`) | Rejected: `!!` is ugly and the close lexer rejects it. A new sigil is a second language for one flag |
| Forbid repair entirely (grk's runner-up) | Workable, but it loses your 0855–0920 example. Trim-only repair is safe enough |
| Fill only free time, as reconcile settlement does | Right for automation, wrong for a deliberate gesture: you would not get the window you typed |
| Let `!` trim or close the running session | Rejected: an implicit close with link-carrying side effects. `x x=3!` says it explicitly |
| Absolute times (`x=0900-0925#build`) | Later. `0900-0925` already lexes as a duration-offset count, so it would need another sigil. It belongs with a backfill-another-day feature |
| A `bob pomodoro record` subcommand | Not instead of capture, which is where you work. It could reuse the same planner later. Never under `bob capture` (CLI rules) |
| Obsidian command parity | Not blocking. Plugins can follow with shared vectors |

## 9. Open questions for you

1. **Stacks across items (A5):** accept it, or keep same-line stacks only for the
   first release?
2. **Work Log timestamps:** stamp at the session's own clock `C` (my
   recommendation), or at the real capture time like today's close?
3. **`x=…=0`:** close and defer every link (A9), or refuse it as cdx suggests?
4. **`!` per token or per stack:** per token is precise and makes "unneeded `!`"
   exact. The cost is `x=build@2! x=fix@3!` when one old session overlaps both.
5. **Trimming calendar MEET rows:** allowed (my recommendation, flagged in the
   preview) or refused in the first release (gem)?

## 10. Recommended solution

Add **`x=<E>[!][=<X>]`**, documented as *Recording a past Pomodoro* and reported as
JSON mode `pomodoro_past`, in capture grammar 11.

- **Window.** `<E>` picks the target and a length (default 5 blocks) using the `=`
  start grammar without offsets, `~K`, split, merge, or `0`. Every window ends at
  `T = ceil5(now)`. Consecutive `x=` tokens, on one line or in adjacent items, stack
  back to back in typed order. No window crosses midnight.
- **Target.** An unnamed token takes the next placeholder; a named one follows `=`
  resolution. A token never restarts, swaps, or records over the running session.
- **Close.** `<X>` is the unchanged `x` close selection. It runs on the explicit
  past row at clock `min(end, now)`. The row is filed in time order, and carried
  links stay in the source placeholder.
- **Guard.** Times are half-open, so touching is fine. Overlapping a running
  session refuses. Overlapping closed history needs `!` on each overlapping token,
  and `!` is an error when nothing overlaps. `!` only trims an older row's edge,
  keeping its clock key and children, and refuses to split or erase it.
- **Presentation.** Bob computes everything. Human output says *recorded* and
  *took*; the Mac shows a chronological "Record past work" card.

This keeps your syntax and every example, fixes the one real grammar conflict in
the trailing `!`, and reuses the start and close code you already trust. It also
adds the overlap protection the ledger has never had.

---

*Figure note:* I drafted a decision flowchart of the guard and rendered it with
Mermaid CLI 12.0.0 under the research-PDF config. After two revisions it still
measured 882 × 1006 px, a 74.0% fit, below the 75% floor, so it was dropped. The
§5.5 table carries the same rule. grk's two figures (`token-recognition.png`,
`packed-lookback.png`) moved into this directory alongside its report.

*My own checks for this consolidation:*

- **`capture-parse` probes** of `x1!`, `x*3!`, `x!!`, `x!2!`, `x0`, `x@0`, `x=3`,
  `x==1!2`, `=build!`, and `=build=*3`.
- **Code reads at `27feff87`:** `start_block_minute`, `close_timing`,
  `find_running_pomodoro` and the close entry points, `closed_insert_at`,
  `next_future_pomodoro`, and `detect_overlaps`.
- **Docs:** `docs/gcal.md` on overlapping MEET clusters.
- **Mac:** `CaptureModels.swift` (`mode` is a `String`) and
  `CaptureGrammarGate.swift`.
- **Memory reads:** decisions `bob-gcal-is-read-only-and-proposes-once`,
  `ended-off-clock-events-settle`, `event-task-links-close-by-the-clock`,
  `mac-capture-is-a-thin-client`, and `off-clock-follows-tag-then-note-default`,
  plus `cli_rules.md`.

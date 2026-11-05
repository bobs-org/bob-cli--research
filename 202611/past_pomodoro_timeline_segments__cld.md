# Placing a past Pomodoro on today's timeline: the `x=` segment suffix

*Researcher: cld · 2026-11-05 · bob-cli `832e1246` (capture grammar 13) · bob-mac-capture `origin/master`*

You asked for an optional suffix on `<E>` in `x=<E>[!][=<X>]`, written `~`, `~<n>[+]`,
or `~~`, so a recorded past Pomodoro can start or end at the edge of a chosen "time
range block" of today's ledger instead of always ending now. This report checks that
idea against the current code, the earlier `x=` design, and the Mac client. It then
proposes a precise model, lists the adjustments I recommend, and ends with a
recommended solution.

## TL;DR

- **Build it.** `x=` can only record work that ended *now*. The suffix closes the last
  real gap: logging work you forgot that ended earlier, which today means editing the
  daily note by hand. Your six examples are the right core cases, and all six work
  unchanged under the model below.
- **Keep your four shapes** (`~`, `~n`, `~n+`, `~~`) and the `-` → `~` typing
  assist. The `n` plus side encoding is better than it first looks. Every interior edge
  of the timeline gets exactly two spellings, one per direction, and the number names
  the segment the new Pomodoro grows *into* ([figure](#the-picture)).
- **Tighten the edges.** Rename "time range block" to **segment**, because "block"
  already means five minutes. Treat a running session as a wall. Ignore sub-block
  slivers. A typed count is exact; an untyped count stops at its segment's far edge;
  nothing records past now. `!` stays the only way to take time from a recorded
  Pomodoro. Numbers come from the ledger as the capture found it. Anchors split stacks.
  ([A1–A10](#4-requirement-adjustments))
- **The `-` → `~` assist belongs in bob**, as a new arm of `capture-rewrite`'s
  existing sigil-alias rule (`.`→`^`, `;`→`:`, `,`→`+`, `\`/`/`→`#`). The Mac only
  adds `-` to its trigger keys. bob never *accepts* `-` as an anchor at execution.
- **Make the timeline visible**: a segment picker after `~`, the resolved segment in
  every preview, and an optional guard so the Mac refuses a submit whose numbers moved
  after the preview.

---

## 1. What exists today

These facts come from reading the code and running the installed `bob`.

| Fact | Where |
| --- | --- |
| `E` is an optional count and/or name (`x=3`, `x=fix`, `x=2fix`, `x=fix2`, `x=#deep-work`, `x=#"DEEP WORK"`). It has no index. The only "offset" is a stack member's `offset_blocks`, the sum of the blocks of the members after it | `validate_past_e` (`src/native/capture_language/past.rs:159`), `compute_past_stacks` (`past.rs:559`) |
| Every window ends at `T = ceil5(now)`. A stack packs backward from `T` in typed order | `compute_preflight` (`src/native/capture/pomodoro_past.rs:89`) |
| The guard uses half-open intervals. An open timed row always refuses. A closed row may be **trimmed** at one edge with `!` when one nonempty piece remains; erasing or splitting it refuses; an unneeded `!` is an error | `preflight_overlaps` / `classify_closed_row` (`pomodoro_past.rs:419`, `:381`) |
| Trims rewrite only the span and duration: name, checkbox, clock key, ID, children, and links stay. Start-edge trims already work (`Trimmable { new_start: ue, … }`) | `pomodoro_past.rs:381–410`, `stage_trim_plans` |
| The past row closes at `C = min(window end, now)`, is placed chronologically, and gives Work Log entries `C` as their timestamp | `docs/capture.md` §Recording a past Pomodoro (`:5215`) |
| **Every spelling you proposed is an `invalid_pomodoro_past` error today.** For example, `x=2~1!=!1` gives ``drop links in the close part after a second `=` … write `x=2!=!1~1` ``, and `x=2-1` gives "…takes no offset; write `x=2`". Claiming these spellings breaks no valid draft | probed with `bob capture-parse -f json` |
| `~` already has three meanings in the session family: `=~K` / `=3~K` (start, drop links), `x~K` (close, drop links), and `x=…=~K` (past close, drop links). `~` / `~~` are also the relation sigils on task items | `bob capture-parse --help`; `CompletionContext::RelationTo/RelationFrom` |
| `-` is the **offset** in the start grammar: `=-2` is 25 minutes with a 10-minute offset, and `=2-1` is 10 minutes with a 5-minute offset | `docs/capture.md:146`, `:3440` |
| The JSON field `pomodoro_past.anchor` already exists and means `T` (`"0925"`) | `PomodoroPastSummaryJson` (`src/native/capture/output.rs:283`) |
| The Mac past card draws `window.start`–`window.end` and the trim rows from bob. It never computes a window, so an **older app already renders an anchored result correctly** | `CapturePomodoroPastPresentation.makeGroup` |
| **Precedent for typing aliases:** `capture-rewrite`'s `expand_sigil_alias` swaps an unshifted key for its real sigil only if the swapped text would open the matching completion picker. The Mac calls it only for a fixed set of trigger keys | `rewrite.rs:117`; `CapturePanelController.noteSeparatorToggleIntentIfEligible` (`:1077`) |
| **Precedent for span-gated assists:** the close-list auto-comma reads bob's parse spans and item mode (`pomodoro_past` included) and never recognizes syntax itself | `CaptureCloseTaskCommaAssist.swift` |
| Bash expands an unquoted `x=~` to `x=/home/bryan` (it treats words that look like assignments that way). Your zsh leaves it alone because `magic_equal_subst` is off. `x=~~`, `x=2~1`, and `x=read2~=!1` survive both shells | probed `bash -c`, `zsh -f`, `zsh -ic` |

The earlier consolidated design (`202611/recording_past_pomodoros/recording_past_pomodoros.md`)
made four choices that this proposal changes or touches:

- Every window ends at `T`.
- `~K` was rejected inside `E` because it would create "two numbering domains in one
  token".
- Absolute times were deferred because they "would need another sigil".
- "Fill only free time" was rejected for a deliberate gesture: *you would not get the
  window you typed*.

The design below reopens only the first, answers the second, prepares for the third,
and keeps the fourth.

## 2. Is this a good idea?

**Yes.** My reasons:

1. **It fixes a real gap.** Timeboxing usually fails because you forgot to start the
   timer. `x=` fixed that for work that just ended. Work that ended an hour ago, or that
   belongs in the first 10 minutes of a Pomodoro you already closed, still has no
   gesture.
2. **Relative addressing matches how you remember a day.** You remember "the gap before
   my last Pomodoro" and "the start of BUILD", not "08:00". `~n` reads like git's
   `HEAD~n`: *n steps back from now*. `-` is a natural "back" key for the assist.
3. **The segment-plus-side encoding is unusually tidy.** Segments are contiguous, so
   the end of segment `n` is the start of segment `n−1`. `~2+` and `~1` both point at
   08:30. `~2+` grows backward into the gap, and `~1` grows forward into BUILD. One
   edge, two directions, and the number always says which segment the new session
   lands in. Because of that, `!` (taking time from a Pomodoro) lines up exactly with
   "the number named a Pomodoro".
4. **Almost all of the execution already exists.** Target resolution, the
   explicit-entry close at `C`, chronological placement, the whole-stack guard, and
   edge trims all apply unchanged. The new code is segmentation, layout from an edge,
   and one cut rule.

**Costs to accept on purpose:**

1. **`~` gets a fourth meaning in one grammar family.** `x=3~2` (segment 2), `=3~2`
   (start, drop link 2), and `x=3=~2` (past, drop link 2) are one keystroke apart. This
   is the "two numbering domains" problem the earlier design avoided. Mitigations: the
   documented rule *"before the second `=` is time; after it are tasks"*, a distinct
   span color, the picker, and `!`, which catches a mistyped index that lands on a
   Pomodoro. Muscle memory for the old drop could still put a session in a *gap*
   without complaint, so the preview has to show the window.
2. **Numbers move.** `~1` changes meaning whenever a Pomodoro closes, and partly
   filling a gap splits it. Live preview handles this while you type; the stale-preview
   guard ([A10](#a10-show-the-timeline)) covers the moment between preview and submit.
3. **Edges can fall off the 5-minute grid.** Calendar MEET rows such as 0927–0950
   produce windows like 0900–0927. That is truthful, but tiny slivers would take numbers
   ([A3](#a3-gaps-shorter-than-one-block-are-slack-not-segments)).
4. **Shell expansion.** In bash, an unquoted `bob capture x=~` arrives as
   `x=/home/bryan` and today fails with a confusing split/merge error.
5. **A grammar revision and Mac work** (grammar 13 → 14, a new span kind, picker rows,
   and a trigger key).

**Would I take a different approach?** No. I would keep yours and tighten its edges.
The strongest rival is an absolute clock suffix (`x=2~0800`, `x=2~0830+`). It is
precise and stable, but worse for the common case, and it needs you to look up times.
I recommend reserving its syntax now and treating it as a follow-up
([alternatives](#11-alternatives-considered)).

## 3. The model: today's timeline segments

### The picture

Your example ledger: PLAN 0730–0800 and BUILD 0830–0900 closed, CHORE and READ
planned, now 09:13, so `T` = 09:15.

```text
                   head            ~3 PLAN         ~2 gap         ~1 BUILD      ~ tail
            |.................|###############|...............|###############|.........|
            0000            0730            0800            0830            0900      0915 = T
ends at                      ~~              ~3+             ~2+             ~1+       x=
starts at                    ~3              ~2              ~1               ~
```

*Figure: each suffix points at the edge the new Pomodoro hugs. The top row grows
backward, so the session ends at that edge. The bottom row grows forward, so it starts
there. A plain `x=` (no suffix) is today's behavior: it ends at `T`. Midnight gets no
suffix, because no one means "starting at midnight".*

### Construction

Bob builds this from today's `## Pomodoros` section alone. Placeholders `()` are not on
the timeline.

1. **Rows.** Take every timed row: closed or open, on- or off-clock, MEET or not. Skip
   zero-length rows (`collect_timed_rows` already does) and rows that start at or after
   `T`, such as future MEETs.
2. **Pomodoro segments** are the closed rows. **Open timed rows are walls**: they get no
   number and are never written ([A2](#a2-a-running-session-is-a-wall-and-1-is-the-last-closed-row)).
3. **Gaps** are the maximal stretches no row covers, between the first row's start and
   the tail. A gap shorter than one block is slack and gets no number
   ([A3](#a3-gaps-shorter-than-one-block-are-slack-not-segments)).
4. **The tail** (`~`) runs from the end of the last closed row to `T`, or to the start
   of a running session that began earlier. It may be empty.
5. **The head** (`~~`) runs from midnight to the first row's start.
6. **Numbering.** Order Pomodoro segments and numbered gaps by end time, newest first;
   on a tie, the later start comes first. `~1` is the closed row that ended last.
   Overlapping closed rows, which gcal may legitimately leave, each get their own
   number.
7. **Snapshot.** Every suffix in a draft resolves against the ledger as the capture
   found it ([A6](#a6-numbers-come-from-the-ledger-as-the-capture-found-it)).

## 4. Requirement adjustments

Each item changes, tightens, or adds to what you asked for. Everything else stays as
you wrote it: the four shapes, `~` = start of the tail, `~n` = start of segment `n`,
`~n+` = end of segment `n`, `~~` = end of the head, `1` = the last completed Pomodoro,
`n ≥ 2` counting back over Pomodoros and gaps, the cut-off at the end of the tail, no
`~+`, and the `-` → `~` assist.

### A1 Call them segments, and name their kinds

"Block" already means five minutes: `x=3` is three blocks, and the docs and errors say
"at least one block". A "time range block" would collide with that. Use **segment**,
with four kinds: **Pomodoro** (a closed row), **gap**, **tail** (`~`, "since your last
Pomodoro"), and **head** (`~~`, "before your first"). Call the suffix itself the
**segment suffix**, and do not call it an "anchor". JSON `pomodoro_past.anchor` already
means `T`, and changing its meaning would mislead older clients.

### A2 A running session is a wall, and `~1` is the last closed row

Your type (4) definition, "from the end of the last Pomodoro to `T`", breaks while a
session is running, because the last row in the file ends in the future. Rule:

- `~1` is the last **closed** row, as you said.
- The tail ends at `T` or at the start of a running session that began before `T`,
  whichever comes first.
- Example: BUILD closed 0830–0900, WORK running since 0905. `x=~` records 0900–0905.

If the running session starts at the last closed row's end, the tail is empty and `x=~`
refuses with ``nothing to record between BUILD (ended 0900) and WORK (running since
0900)``. A session started with `=` at 09:21 begins at 09:25 = `T`, so the common "start
the timer, then backfill" sequence needs no special case.

### A3 Gaps shorter than one block are slack, not segments

Calendar spans do not sit on the 5-minute grid. Take BUILD 0900–0925 followed by MEET
0927–0950. If the 2-minute sliver at 0925–0927 counted as a gap, it would take `~2`,
and every number before it would shift by one compared with what you see in Obsidian.
So a gap shorter than 5 minutes gets **no number**, and the segments on either side
count as adjacent. The tail and head keep their names even when short, so `x=~` after
a MEET that ended at 09:12 records 0912–0915.

### A4 Length: a typed count is exact, an untyped count fills, and nothing records past now

Your rule cuts `~` off at the end of the tail. I generalize it into three short
sentences:

1. **A typed count is exact.** `x=8~2` means 40 minutes. If that runs out of the gap
   into BUILD, it overlaps BUILD, and the existing `!` rules apply: refuse and teach,
   or trim with `!`. This keeps the earlier design's principle that *you get the window
   you typed*.
2. **An untyped count is 5 blocks but stops at its segment's far edge.** `x=~2` over a
   10-minute gap records 10 minutes, not a 25-minute overlap error.
3. **Nothing records past now.** A forward-growing window that would end after `T`, or
   inside a running session, is cut there. This is your `~` rule, and it applies to a
   typed count too: `x=read4~` at 09:13 records 0900–0915.

A window that would start before midnight still refuses, as it does today, with the
existing "record at most N blocks" rewrite. Every cut is reported, never silent
(`window.cut`, and "cut at now" in the human and Mac output).

*Rejected:* letting an untyped count fill the whole segment. `x=~` after a two-hour gap
would then record a two-hour "Pomodoro". The 25-minute unit is the right default, and
the picker shows a segment's length so you can type `x=6~2` when you mean "all of it".

### A5 `!` is unchanged, which makes it the type check

`!` is still required exactly when a window overlaps closed history, and it is an
error otherwise. So:

- every **carve**, meaning a window inside a Pomodoro segment, needs `!`, as in your
  examples (`x=2~1!`);
- a gap never needs it unless a typed count overruns.

That is a safety feature. If you meant the gap `~2` but typed `~3`, which is PLAN, the
capture refuses instead of quietly cutting into PLAN. A carve that would take the whole
row still refuses, because it would erase the row. The rewrite suggests the largest
count that leaves a piece: ``x=6~1! would take all of BUILD 0830–0900; carve at most 5
blocks: x=5~1!``.

### A6 Numbers come from the ledger as the capture found it

The picker, the preview, and execution must agree. So every suffix in a draft resolves
against the timeline as it was **before the capture's first edit**, and recording one
stack never renumbers a later stack in the same draft. The overlap guard still checks
each stack against pre-stack history, so two stacks that collide still refuse.
Consequence: in `x x=2~1!`, `~1` names the Pomodoro that was last closed *before* this
capture, not the session the `x` just closed. To carve that one, close it first and
capture again. I think "numbers never move while you type" is worth that.

### A7 Segment suffixes split stacks

Today a stack is a maximal run of consecutive `x=` items, packed back from `T`. With
suffixes:

- **A start suffix (`~`, `~n`) begins a new stack.** The unsuffixed members after it
  flow forward. `x=read2~2 x=fix3` is READ 0800–0810, then FIX 0810–0825, read left to
  right.
- **An end suffix (`~n+`, `~~`) ends the current stack.** The unsuffixed members before
  it flow backward. `x=email1 x=read2~2+` is EMAIL 0815–0820, then READ 0820–0830.
- **A stack with no suffix is unchanged.** It ends at `T`.
- **A stack pinned at both ends refuses.** `x=a2~2 x=b~~` gets ``a stack hangs from one
  edge: x=b~~ ends the stack x=a2~2 starts; swap them (x=b~~ x=a2~2) or capture them
  separately``. The swapped order works because `~~` closes its own stack first.

In a stack, A4's "untyped stops at the far edge" applies to the member that reaches the
far edge.

### A8 The `-` → `~` assist lives in bob, and execution never accepts `-`

Decision `mac-capture-is-a-thin-client` says the app "never decides syntax itself", so
the replacement rule cannot live in Swift.

- **bob:** add a `-` arm to `expand_sigil_alias`. Swap the typed `-` for `~` only when
  the swapped text opens the new `PomodoroPastSegment` completion field at the cursor.
  This is exactly how `.`, `;`, and `,` already work.
- **Positions this gives:**
  - `x=-` becomes `x=~`, and `x=2-`, `x=fix-`, `x=fix2-`, and `x=#"DEEP WORK"-` all
    get `~`;
  - `x=~-` becomes `x=~~`, so typing `--` gives `~~`;
  - **never** inside a `#name`, where `-` is a legal name byte (`x=#deep-work` must
    still type normally);
  - never after an index (`~2-`), never after `!`, and never after the second `=`.
- **Mac:** add `-` to the trigger keys in `noteSeparatorToggleIntentIfEligible`, but
  arm it only when the latest parse snapshot puts the caret in a `pomodoro_past` item.
  The comma assist already applies the same span filter. Without the gate, every dash
  in task prose and Work Log bullets would spawn `capture-rewrite`. The swap is its own
  undo step, as for the other aliases, so ⌘Z gives the literal `-` back.
- **Execution:** `bob capture 'x=2-1'` still refuses. The teaching message now offers
  both readings: ``x= takes no offset; to start at segment 1 write x=2~1, to end now
  write x=2``.

Why not accept `-` directly? `=2-1` means "offset one block" in the start grammar, and
`x=` is documented as "the start grammar without offsets". Silently giving `x=2-1` a
different meaning is the kind of grammar trap this codebase teaches around. The editor
swap is visible, so you see the canonical `~` as you type.

One more: `x=deep-work` is already a teaching error (bare names cannot contain `-`).
With the assist it becomes `x=deep~work` while you type. That needs its own teaching
error pointing to `x=#deep-work`.

### A9 Degenerate spellings get teaching errors, one spelling per meaning

| Typed | Teaches |
| --- | --- |
| `x=~0`, `x=3~0` | `~` already means the tail: `x=~`, `x=3~` |
| `x=~+`, `x=~0+` | Ending now is what `x=` already does: `x=` |
| `x=~~+` | `~~` already ends at your first Pomodoro: `x=~~` |
| `x=2~01` | `x=2~1` (no leading zeros) |
| `x=2~123`, `x=2~0800` | Reserved: a segment number has at most two digits (`~HHMM` is kept free for a future clock suffix) |
| `x=~4` (only 3 segments) | ``today has 3 segments before now: ~1 BUILD 0830–0900, ~2 gap 0800–0830, ~3 PLAN 0730–0800; the time before 0730 is ~~`` |
| `x=~2fix`, `x=~2#deep-work` | The suffix comes last in `E`: `x=fix~2`, `x=#deep-work~2` |
| `x=2~1~2`, `x=2~~1` | One segment suffix per session |
| `x=2~1,3` | A comma list is a drop: `x=2=~1,3` (the old teaching, kept for list shapes) |
| `x=deep~work` | `x=#deep-work` (see A8) |
| `x=~`, `x=~~` with no rows before `T` | ``nothing is recorded yet today, so ~ has no Pomodoro to start after; write x= to end now`` |
| `x=~` with an empty tail | ``nothing to record since BUILD ended at 0915`` |
| `x=/home/bryan…` (bash expanded `x=~`) | ``your shell expanded ~ to your home directory; quote the token: bob capture 'x=~'`` (only when `E` starts with `$HOME`) |

I keep `~0` as a teaching error rather than an alias, even though you described `~` as
"0 implied". Two spellings for one place would make the picker and the docs uglier.

### A10 Show the timeline

Relative numbers are only friendly when you can see them, so:

- **Picker.** `bob capture-complete` gets a `pomodoro_past_segment` context at
  `x=…~|` (and over a typed index). Rows look like this, and accepting one inserts the
  suffix:

  ```text
  ~    since 0900     15m   tail · now
  ~1   BUILD 0830–0900 30m  carve · needs !
  ~2   gap 0800–0830   30m
  ~3   PLAN 0730–0800  30m  carve · needs !
  ~~   before 0730          head
  ```

  zsh completion can reuse the same rows with one new context arm in
  `capture_complete/shell.rs`, next to the existing `PomodoroPastName` arm.
- **Preview.** The dry-run reports the resolved segment and any cut. The Mac card adds
  one line ("in gap 0800–0830 · from its start") and can draw a small timeline strip
  with the target highlighted. The trim rows already render start-edge trims.
- **Stale-preview guard (optional).** The Mac passes an internal
  `--expect-past-windows 0830-0840[,…]` with its submit. bob refuses if the resolved
  windows differ ("your timeline changed since the preview: `x=2~1!` now means
  0900–0910"), and the Mac re-previews. The CLI omits the flag. This is the lighter
  `--expect-anchor` idea from the earlier report, made necessary now that a closed
  session can renumber `~1` between the keystroke and Return.

## 5. Grammar

```text
x=E[!][=X] [work-log entry]

E      = [N] [name] [N] [where]
where  = "~"           tail: start where your last Pomodoro ended
       | "~" n         segment n: start at its start
       | "~" n "+"     segment n: end at its end
       | "~~"          head: end where your first Pomodoro starts
n      = 1..99, no leading zero
```

Mnemonic for the docs: ***`~` steps back along today's timeline; `+` hugs the far
end.*** It sits beside the existing *"before the second `=` is time; after it are
tasks."*

Lexing needs almost nothing new:

- `~` already ends an unquoted name (`past_name_extent`, `item.rs:3320`).
- `#"…"` literals still protect their contents (`split_past_token`).
- The repair `!` and the second `=` split exactly as today.
- In `validate_past_e`, the `rest.starts_with('~')` arm of `past_rest_error`
  (`past.rs:426`) becomes "lex a segment suffix, which must consume the rest of `E`".
  Comma lists keep the drop teaching.
- A name may contain `+` (`is_pomodoro_selector_byte`). Since `~` ends the name,
  `x=#c++~1+` is the name `c++` with suffix `~1+`.

| Token | `capture-parse` spans |
| --- | --- |
| `x=2~1!=!1` | `pomodoro_past` over `x=2`, **`pomodoro_past_segment`** over `~1`, `pomodoro_past_repair` over `!`, `pomodoro_close` over `=`, `pomodoro_close_complete` over `!1` |
| `x=read2~` | `pomodoro_past` over `x=`, `pomodoro_name` over `read`, `pomodoro_past` over `2`, `pomodoro_past_segment` over `~` |
| `x=~~` | `pomodoro_past` over `x=`, `pomodoro_past_segment` over `~~` |

## 6. Semantics

**Layout.** Let `s` and `e` be the chosen segment's start and end.

| Suffix | Pinned edge | Members (block counts `b₁ … b_k`, typed order) |
| --- | --- | --- |
| none | `T`, end | backward from `T`, as today |
| `~`, `~n` | `s`, start | `[s, s+5b₁)`, `[s+5b₁, s+5(b₁+b₂))`, … forward |
| `~n+`, `~~` | `e`, end | backward from `e`, mirroring today's math |

**Length and cut** follow [A4](#a4-length-a-typed-count-is-exact-an-untyped-count-fills-and-nothing-records-past-now).
The far edge is `e` for start-pinned stacks and `s` for end-pinned ones; for the tail,
it is `T` or the running wall.

**Unchanged:**

- **Guard:** `preflight_overlaps` runs against pre-stack history, with per-token `!`,
  trim-only repair, no erase, no split, and no touching of open rows.
- **Targets:** unnamed means the first open placeholder; named resolves like `=name`.
- **Close** at `C = min(end, now)`, so a past window closes at its own end.
- **Placement:** chronological, with carried links left at the source placeholder.

## 7. Worked examples

Ledger as in [the picture](#the-picture): PLAN 0730–0800 and BUILD 0830–0900 closed;
CHORE (with tasks) and READ planned; `BOB_NOW` 09:13, so `T` = 09:15.

**Your six examples, checked against the model:**

| Draft | Records | Side effects |
| --- | --- | --- |
| `x=~=!1` | CHORE 0900–0915 (25m cut at now to 15m), closed 09:13 | completes CHORE task 1 |
| `x=read2~=!1` | READ 0900–0910, closed 09:10 | completes READ task 1 |
| `x=2~1!=!1` | CHORE 0830–0840, closed 08:40 | BUILD trimmed to 0840–0900 |
| `x=2~1+!=!1` | CHORE 0850–0900 | BUILD trimmed to 0830–0850 |
| `x=2~2=!1` | CHORE 0800–0810 | — |
| `x=2~2+=!1` | CHORE 0820–0830 | — |

**More cases:**

| Draft | Result |
| --- | --- |
| `x=~~` | CHORE 0705–0730 |
| `x=~2` | CHORE 0800–0825 (default 25m fits the 30m gap) |
| `x=fix6~2` | FIX 0800–0830, fills the gap |
| `x=fix8~2` | Refuses: ``x=fix8~2 would take 10m from BUILD 0830–0900; add ! to take it: x=fix8~2! (BUILD becomes 0840–0900), or fill just the gap: x=fix6~2`` |
| `x=~1` | Refuses: ``would take 25m from BUILD 0830–0900; add ! to take it: x=~1!`` |
| `x=~1!` | CHORE 0830–0855; BUILD trimmed to 0855–0900 |
| `x=6~1!` | Refuses: would erase BUILD; ``carve at most 5 blocks: x=5~1!`` |
| `x=2~2!` | Refuses: ``takes no time from another session; drop the !: x=2~2`` |
| `x=read4~` | READ 0900–0915 (typed 20m, cut at now; reported) |
| `x=read2~2 x=fix` | READ 0800–0810; FIX 0810–0830 (untyped, stops at the gap's end) |
| `x=email1 x=read2~2+` | EMAIL 0815–0820; READ 0820–0830 |
| `x=b~~ x=a2~2` | Two stacks: B 0705–0730; A 0800–0810 |
| `x=a2~2 x=b~~` | Refuses: one stack pinned at both ends (A7) |
| `x=~` with WORK running since 0905 | CHORE 0900–0905 |
| `x=~4` | Refuses and lists the three segments, plus `~~` |

## 8. Editor and Mac experience

This is where "beautiful" is won or lost.

1. **Typing.** Bob rewrites `x=2-` to `x=2~` with the caret after `~`. `--` gives
   `~~`, and ⌘Z restores the literal dash.
2. **Highlighting.** `pomodoro_past_segment` gets its own style: same family as
   `pomodoro_past`, visibly different from `pomodoro_close_drop`, so `~1` before the
   `=` never looks like `~1` after it.
3. **Picker.** As soon as `~` appears, today's segments drop down with their times and
   kinds. Return inserts `~2`; you add `+` or `!` yourself, and the preview teaches `!`
   if you forget.
4. **Card.** "Record past work · 10m — CHORE 0830–0840 · carved from the start of BUILD
   (~1) · BUILD 0830–0900 → 0840–0900". Optionally, draw a one-line strip like the
   [picture](#the-picture) with the new window overlaid.
5. **Freshness.** The card already re-asks bob at each 5-minute boundary
   (`CapturePastBoundary`). The optional guard covers ledger changes between preview
   and submit.

The Mac changes are presentation plus one trigger key. The gate moves to grammar 14 for
the new span and picker context. Older apps keep working: they show anchored windows
correctly and simply lack the extra segment line.

## 9. Protocol and JSON

All changes are additive, and the `capture-*` protocol names are unchanged
(`cli_rules`):

- **`capture-parse`:**
  - `pomodoro_past.segment = {"raw": "~2+", "kind": "index", "index": 2, "edge": "end"}`.
    The tail is `{"kind":"tail","edge":"start"}` and the head is
    `{"kind":"head","edge":"end"}`.
  - `stack` gains `pinned: "start" | "end"`. `offset_blocks` keeps its meaning for
    end-pinned stacks; add `lead_blocks` for start-pinned ones.
  - New span kind `pomodoro_past_segment`.
  - `grammar: 14`.
- **`capture` / `--dry-run`:**
  - `pomodoro_past.segment = {"index": 1, "kind": "pomodoro", "start": "0830", "end": "0900", "name": "BUILD", "line": 4, "edge": "start"}`.
  - `pomodoro_past.window` gains `requested_minutes` and `cut: "now" | "segment"` when
    cut.
  - `anchor` stays `T`.
  - The human line names the segment.
- **`capture-complete`:** context `pomodoro_past_segment`; rows carry `replacement`,
  `label`, `kind`, `start`, `end`, `minutes`, and optional `name` / `line`.
- **`capture-rewrite`:** the `expand_sigil_alias` arm (`-` → `~`).
- **Internal:** `--expect-past-windows` (no short alias, per `cli_rules`).

## 10. Risks

| Risk | Mitigation |
| --- | --- |
| Drop muscle memory (`=3~2`) puts a past session in gap 2 | Docs mnemonic; distinct span; picker; preview; `!` catches it whenever segment 2 is a Pomodoro |
| A stale preview carves the wrong row | Snapshot rule A6 plus the optional expect guard |
| Trimming a gcal MEET makes its span "edited", so later Google moves stop following it (`meet-filing-follows-google-until-edited`) | Already true for today's `!`; the card flags calendar trims (`calendar: true`) |
| Off-grid windows look odd in Stats | They are truthful; they only come from off-grid neighbors; A3 keeps numbering stable |
| Prose dashes spawn `capture-rewrite` | Mac gate on `pomodoro_past` item mode |
| Bash `x=~` | Teaching error (A9); the docs already advise single quotes |

## 11. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| Absolute clock suffix (`x=2~0800`, `x=2~0830+`) | **Follow-up.** Precise and stable, but you'd have to look up times. Reserve `~` plus four digits now (A9) |
| Name-relative anchors (`x=2~build+`) | Rejected: names repeat (an "again" row adds a second BUILD), and gaps have no name |
| Separate numbering for gaps and Pomodoros | Rejected: two domains, and more syntax. One ordinal plus `!` as the type check is simpler |
| `@` as the sigil ("at segment 2") | Rejected: `@` is the routing sigil (`capture-sigils-say-where-what-how`), and `x=fix@3` currently teaches the retired timing spelling `x=fix3`, so it would silently flip meaning |
| `-` as the canonical sigil | Rejected: it collides with the start grammar's offset (`=2-1`) |
| Accepting `-` at execution | Rejected: two spellings, and `x=3-1` would change meaning silently (A8) |
| Untyped count fills the whole segment | Rejected (A4): `x=~` after a long gap would record hours |
| Cut typed counts at every segment edge | Rejected: a deliberate count should give the typed window; overflow already has `!` |
| Number the head too (`~4+` = `~~`) | Rejected: two spellings, and `~4` would always be an error (it would start at midnight) |
| One suffix per stack, first or last member only | Workable, but A7's "suffixes split stacks" is equally simple and lets one draft hold two placed stacks |
| Resolve suffixes against pre-stack state | Rejected (A6): the picker and preview could disagree with execution |

## 12. Implementation plan

| Layer | Change |
| --- | --- |
| Lexer | `past.rs`: lex `where` in `validate_past_e` (`PastEValid.segment` with its range), new teaching errors, and the `-`/`$HOME` cases |
| Model | `PomodoroPastSpec.segment`; `compute_past_stacks` splits runs at suffixes, sets `pinned`, `offset_blocks`, and `lead_blocks`, and diagnoses double pins |
| Editor | `SpanKind::PomodoroPastSegment`; `parse_editor_past_item` emits it (`editor_pomodoro.rs:3303`) |
| Timeline | A new `timeline` helper next to `collect_timed_rows` (`pomodoro_past.rs:244`): rows → walls, segments, gaps (≥ 5 min), tail, head, numbering |
| Execution | `compute_preflight` takes the capture-start day contents for suffixed stacks, lays them out from the edge, applies the A4 cut, and records `cut`. The guard, trims, targets, close, and placement are unchanged |
| Output | Additive JSON (§9); the human line names the segment and any cut |
| Completion | `CompletionContext::PomodoroPastSegment`; candidates in `capture_complete/pomodoros.rs` from the same timeline helper; a shell-row arm in `capture_complete/shell.rs` |
| Rewrite | A `-` arm in `expand_sigil_alias` (`rewrite.rs:117`), gated by the new completion field |
| Docs | `docs/capture.md` §Recording a past Pomodoro gets "Placing it on today's timeline", plus the syntax-table row, the teaching table, `reference/json-outputs.md`, and the `capture-parse --help` paragraph (it currently cites `x=~2` as a drop teaching). Read the `docs` and `cli_rules` reference memories first; run `just docs-gen` and `just docs-check` |
| Grammar | `GRAMMAR_REVISION` 13 → 14 (`capture_language/mod.rs:46`). A `feat(capture)` commit: every claimed spelling was an error before. Release train only, with no version or CHANGELOG edits |
| Decision | New record via `/sase_memory_write`. Claim: *"A past Pomodoro may be placed by a segment suffix that counts closed rows and gaps back from now; typed counts are exact, nothing records past now, and `!` still only trims an edge."* It partly supersedes the earlier "every window ends at T" choice |
| Mac | The `-` trigger (gated); span style; picker rows; card segment line and optional strip; grammar gate 14; optional `--expect-past-windows`. Watch the macOS CI run to green |

### Phases

1. **Grammar and single members:** the lexer, spans, teaching errors, timeline,
   execution, JSON, docs, and grammar 14.
2. **Stacks with suffixes** (A7).
3. **The picker and the `-` → `~` rewrite** on the bob side.
4. **Mac:** trigger, span style, picker rows, card. Optionally the expect guard.
5. **Later:** the clock suffix `~HHMM`.

### Tests to pin first

- **Your six examples** as golden plans, plus every row of the §7 table, at a fixed
  `BOB_NOW`, with the dry run matching the real run.
- **Timeline edge cases:**
  - no rows; only future MEETs;
  - back-to-back rows (no gap), a 2-minute sliver, overlapping MEETs;
  - a row starting at 0000 (empty head);
  - a running wall before and at `T`; an empty tail right after a close.
- **Length:** every cut path (untyped at a gap edge, typed at now, typed at the running
  wall), the midnight refusal for `~~` overflow, and erase and split refusals on carves.
- **Rewrite positions:**
  - swaps: `x=-`, `x=2-`, `x=fix-`, `x=#"A B"-`, `x=~-` (to `~~`);
  - no swap: `x=#fix-`, `x=~2-`, `x=2!-`, `x=2=-`, prose dashes.
- **Atomicity:** a byte-identical rollback on every refusal.

## 13. Open questions for you

1. **Typed overflow out of a gap** (`x=8~2`): `!`-trim the neighbor (my
   recommendation, consistent with today), or cut it like the tail?
2. **Untyped default:** 25 minutes, stopping at the edge (recommended), or "fill the
   whole segment"?
3. **Snapshot rule A6:** fine that `x x=2~1!` carves the Pomodoro closed *before* this
   capture, not the one the `x` closes?
4. **Picker accept on a Pomodoro row:** insert `~1` only (recommended), or `~1!`?
5. **Stacks with suffixes:** in v1, or after single members ship?
6. **The clock suffix `~HHMM`:** want it next, or never?

## 14. Recommended solution

Add an optional **segment suffix** at the end of `E`:

```text
x=[N][name][N][~ | ~n | ~n+ | ~~][!][=X]
```

It places the recorded session on **today's timeline of segments**:

- **Segments.** Closed rows are Pomodoro segments. Uncovered stretches of at least one
  block are gaps. `~` is the tail since your last closed Pomodoro, ending at now or at
  a running session. `~~` is the head before your first. Numbers count back from now,
  starting with `~1`, the last closed row, and are taken from the ledger as the capture
  found it.
- **Placement.** `~` and `~n` start the session at the segment's start; `~n+` and `~~`
  end it at the segment's end. A suffix-less `x=` still ends now.
- **Length.**
  - A typed count is exact.
  - An untyped count is 25 minutes but stops at the segment's far edge.
  - Nothing ever records past now, and every cut is reported.
- **Safety.** It is today's guard, unchanged. Carving a Pomodoro segment needs `!`,
  `!` only ever trims one edge, open sessions are never touched, and a typo that lands
  on a Pomodoro refuses instead of overwriting.
- **Stacks.** A start suffix opens a stack that flows forward; an end suffix closes one
  that flows backward. A stack pinned at both ends is refused.
- **Editing.**
  - bob's `capture-rewrite` swaps a typed `-` for `~` wherever `~` would open the new
    segment picker, and `--` gives `~~`. The Mac only adds `-` to its trigger keys,
    gated on `pomodoro_past` items.
  - The picker lists each segment with its times. The preview names the segment and
    shows cuts and trims. An optional expect guard refuses a submit whose numbers moved.
- **Shipping.** Grammar 14, additive JSON, a new decision record, and `~HHMM` reserved
  for a future clock suffix.

This keeps your syntax and all six examples, closes the "running session" and "sliver"
holes in the block definitions, keeps the "you get the window you typed" principle
except at the one wall where the future begins, and puts the only new syntax rule where
it already has a precedent: an unshifted alias that bob, not the app, decides.

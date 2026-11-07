# `+N` start offsets in `=<X>`: research, critique, and a recommended design

Researcher: `cld` · 2026-11-07 · bob-cli `b73ac383` (bob 0.5.0), bob-plugins and
bob-mac-capture at `origin/master` of the same day.

## TL;DR

**Build it, but frame it as "the start offset gets a sign" rather than as "a glued
`++`".** `<X>` already has a backward offset (`=-2` means "I started 10 minutes ago").
Adding `+` makes the timing literal symmetric:

```text
<X>  =  [D] [ (- | +) [N] ]        D = duration blocks (default 5)
                                   N = offset blocks  (default 1 when a sign is present)
start = ceil((now ∓ 5·N) / 5) · 5      end = start + 5·D
```

`=fix2+` and `@foo:bar=+3` then work exactly as you asked. The one-line rule for
reading `+` inside a bare name is: **`+` followed by a letter joins name components
(`=bob+decks`); `+` followed by digits or by nothing begins the offset (`=fix2+`,
`=bugs+2`).**

I recommend six changes to the requirements. Each is explained in
[Requirement adjustments](#requirement-adjustments):

1. **Leave `x=` out.** `x=` records the past, `+` already has a meaning inside `x=`
   (the `~n+` segment edge), and `x=` offsets were deliberately retired. Use teaching
   errors instead. `x =fix+` (close, then start later) works with no extra code.
2. **The equivalence `=fix2+ ≡ =fix2 ++` holds for starts and restarts, not for
   swaps.** A non-empty `<X>` always means fresh timing measured from now. That is
   already true of `-`, and it should stay true.
3. **`+0` is accepted as "no offset"**, matching `-0`. You specified a positive
   integer.
4. **A bare name can no longer end in `+` or `+digits`.** `=fix+` currently starts a
   session named `FIX+`. These names would need the `#` spelling. A survey of the
   vault found no such names in use.
5. **Bob refuses `@route:id= ++N`.** Your mental model for this form is wrong today:
   it silently becomes a new task titled `++N`.
6. **Obsidian's `se<X>` snippet has to learn `+` in the same release train**, because
   the docs promise that `<X>` matches `se<X>` exactly.

---

## 1. What exists today

All probes ran against a freshly built `bob` with `BOB_NOW='2026-10-20 12:00:00'`
unless a different time is noted.

### 1.1 `<X>` is the Obsidian `se<X>` suffix and already has a signed offset

- Grammar: `[0-9]*(-[0-9]*)?`. Its lexer is `start_timing_len`
  (`src/native/capture_language/item.rs:3882`) and its parser is
  `parse_pomodoro_start_suffix` (`src/native/capture_language/tokens.rs:1609`).
- Math: `start_block_minute` (`src/native/capture/meet_event_run.rs:200`) computes
  `ceil((now − 5·offset)/5)·5`. The offset is a `u64` in `PomodoroStartSpec`
  (`src/native/capture_language/model.rs:445`). Today it only means "earlier".
- Contract: `docs/capture.md:1648` states "`<X>` is exactly the suffix of the
  Obsidian bob-ledger-tools `se<X>` snippet". The Obsidian side is
  `LEDGER_TRIGGER_RE = /^se(\d*)(?:-(\d*))?$/`
  (`bob-plugins/plugins/bob-ledger-tools/src/010-load-and-constants.js:289`).
- `=-2` already lands exactly where `= --2` does. The docs don't say so, but a dry run
  at 12:02 gives `1155–1220` for both, because shifting a fresh start by a multiple of
  5 commutes with the round-up. Likewise `= ++3` gives `1220–1245` and `=3 ++2` gives
  `1215–1230`, which are the spans proposed below for `=+3` and `=3+2`.

### 1.2 `+` is already a byte in Pomodoro names

Merged Pomodoros join their theme components with ` + `
(`decisions:pomodoro-theme-is-one-component`, glossary "Merged Pomodoro"), so
`is_pomodoro_selector_byte` accepts `+`. `bare_start_name_len`
(`src/native/capture_language/bare_name.rs:36`) takes the longest run of selector
bytes other than `-`, then peels trailing digits off as glued timing. Today that
gives:

| Draft | Today's parse (`bob capture-parse -f json`) |
| --- | --- |
| `=fix2+` | start, name **`fix2+`**, 25m |
| `=fix+` | start, name **`fix+`**, 25m |
| `=fix+2` / `=bugs+2` | start, name **`fix+`** / **`bugs+`**, **10m** |
| `=bob+decks2` | start, name `bob+decks`, 10m (merged selector) |
| `=+`, `=+3` | **prose** (captured as a task titled `=+3`) |
| `=3+`, `=3+2` | error: "Pomodoro start `=3` must be the whole capture item" |
| `@foo:bar=+3`, `@foo:bar=3+` | error: "Pomodoro start suffix must mirror se<X> …" |
| `@foo:bar=fix2+` | link start under a Pomodoro named **`fix2+`** |
| `x=fix+` | past record named **`FIX+`** |
| `x=3+`, `x=+` | error: "`x=3+` is not a past Pomodoro" |

Doc drift found along the way: `docs/capture.md:398` and `:5640` say that `=bugs+2`
"starts the Pomodoro named `BUGS+2`". Since the glued-timing change (`79709fed`,
2026-11-06) the parser actually reads it as name `BUGS+` with 10-minute timing.
Every row in bold above produces a degenerate name: its last `+` component is empty
or all digits.

**Vault survey.** I grepped every ledger headline in `~/bob/20xx/`. Every `+` sits
between letter-led components, for example `BUILD + FIX`, `PLAN + FINAL + ARTIFACTS`,
and `SWAP POMS + FIX KILL AND EDIT`. No name ends in `+` or `+digits`, so taking those
spellings back for offsets breaks nothing in real use.

### 1.3 `++`/`--` and the swap rule

- `++[N]` shifts the running session N blocks later and keeps its duration. It wraps
  past midnight and does no overlap check (`docs/capture.md:4322`).
- In a swap (`=name` while another session runs), **an empty `<X>` keeps the running
  clock and a non-empty `<X>` supplies fresh timing** (`docs/capture.md:886`).

Dry run at 12:02 with BUGS running 1140–1205:

| Draft | Result |
| --- | --- |
| `=fix ++` | FIX takes over **1140–1205**, then the shift gives **1145–1210** |
| `=fix-` (today) | fresh timing **1200–1225** (compare `=fix --` → 1135–1200) |
| `=fix2 ++` | FIX 1205–1215, then the shift gives **1210–1220** |
| `=fix+` (proposed) | fresh timing **1210–1235** |

So `=fix+` and `=fix ++` differ in a swap, just as `=fix-` and `=fix --` already do.
`=fix2+` and `=fix2 ++` agree, because both use fresh timing.

### 1.4 There is currently no one-line way to link-start later

`@foo:bar= ++3` does **not** chain. `capture-parse` reports `mode: pomodoro_task` with
`body: "++3"`. That means a new task titled `++3`, which in my scratch vault failed
only because `^bar` already existed. Docs confirm that "with extra text, create the
new linked task". `^foo:bar= ++3` is refused. Today the only way to do this is two
items (`@foo:bar=`, a blank line, `++3`). `@foo:bar=+3` fills a real gap.

### 1.5 Sessions that start in the future already exist

- `=` rounds up, so `=` at 12:02 already writes a start of 12:05.
- MEET starts follow their event run and can write a future start. The Obsidian
  plugin even warns (`pomodoro_event_run_later`) when that start is more than 25
  minutes away.
- `x` on a session that hasn't started closes it at its own start with 0 minutes
  (`src/native/capture_pomodoro_close/ledger.rs:218`).
- The unnamed-start "joins the meeting in progress" check runs on the offset start `S`
  (`meet_event_run.rs:315`). `=+2` at 9:52 therefore lands on a 10:00 MEET, which is
  the right result.
- Weak spot: `bob_pomodoro` status only counts down to the **end**
  (`src/native/pomodoro.rs:~410`). A session at 1220–1245 viewed at 12:02 shows
  `[<44m]`.

### 1.6 `x=` deliberately has no offsets

- `x=3-1`, `x=-2`, and `x=3-` are retired. The error teaches the `~` segment suffix
  instead (`docs/capture.md:5517`).
- Inside `x=`, `+` already means "hang the session on the segment's far end" (`~n+`).
  Past records end at the next 5-minute boundary, since "`x=` records what already
  happened".
- The past lexer reuses `bare_start_name_len` (`past.rs:231`). Changing the name rule
  therefore changes `x=fix+` automatically, which is a reason to give it a deliberate
  teaching error.

### 1.7 Downstream consumers

- **Mac Capture** decodes `offset_units` as a signed `Int`
  (`CaptureModels.swift:1533`) and never renders it. It renders bob's resolved
  `start`/`end` and spans. It gates on `grammar >= minimumRevision`
  (`CaptureGrammarGate.swift`), so bumping `GRAMMAR_REVISION`
  (`src/native/capture_language/mod.rs:48`, currently 16) is safe.
- **The Obsidian vector harness** maps only the bare `=` token to `se`
  (`scripts/test-ledger-tools-pomodoro-clock.cjs:105`). New `=+N` vectors would need a
  small harness change.
- **The event-conflict fit draft** builds `=2-1`-style tokens and assumes the offset
  means "earlier" (`src/native/capture/event_conflict.rs:227`).
- **The human start line** reads `=3 (15m, offset 0u)` (`capture_parse.rs:3148`).
  Once both directions exist, "offset 2u" becomes ambiguous.

---

## 2. Critique: is this a good idea?

**Yes. It completes a grammar that is currently only half built, at low cost.**

For it:

- **Symmetry.** Bob can say "I started 10 minutes ago" (`=-2`) but not "I'll start in
  10 minutes". With `±`, `<X>` reads as "D blocks, N blocks earlier or later". This is
  the strongest argument: the sign you type is the direction the start moves.
- **The spacing rule stays principled.** The docs already teach that spacing matters:
  `= -2` (start, then shorten) versus `=-2` (start 10 minutes earlier). With `+` the
  pairs line up exactly: `=bugs +2` (start, then extend) versus `=bugs+2` (start 10
  minutes later).
- **A real capability gap.** A link start can't be followed by a shift on the same
  line (§1.4). `@foo:bar=+3` is the only one-item way to link a task and start it
  later.
- **Low risk.** Future starts, wrap-around, closing a session that hasn't started, and
  overflow errors all exist already. The parser change is concentrated in about four
  helpers.

Against it, with mitigations:

- **Collision with merged-name `+`.** This is real but easy to bound: the new meaning
  only applies when a digit run or the end of the token follows the `+`. No real name
  in the vault is affected (§1.2).
- **"One glued `+` equals two spaced `+`s" can look odd.** It is consistent once you
  read the glued sign as the start offset, the same way `-` already works. A glued
  `++` (`=fix++3`) would break that symmetry, because `-` uses a single sign.
- **Moderate frequency.** I expect "start at :15 after coffee" to be an occasional
  gesture, not an hourly one. The feature is worth it because it is cheap and makes the
  grammar more regular, not because it will be used often.
- **The timer is misleading during the lead time** (§1.5). This already happens with
  `=` and `++`; `+N` just makes it more visible. It belongs in a follow-up, not on the
  critical path.

Alternatives I would **not** take:

| Alternative | Why not |
| --- | --- |
| Status quo: teach `=fix2 ++` | Doesn't work for link starts (§1.4) and keeps `<X>` lopsided |
| A different sigil (`>`, `@`, `^`, `&`, `*`) | Every one is taken (transfer, retired timing, active task, prerequisite, merge/park) and none says "later" as clearly as `+` |
| Glued `++` (`=fix++3`) | Breaks symmetry with the single-sign `-` offset that already exists, and is longer |
| Offset-only `<X>` on a swap shifts the kept clock | Breaks the rule that a non-empty `<X>` means fresh timing and would diverge from `-`. `=fix ++` already covers keep-and-shift |
| Support `x=…+N` | See §4.6 |
| A warning when the start is more than 25 minutes away | Explicit input should not draw a warning. The live preview and dry run already show the span |

---

## 3. Design principles

1. **One timing literal everywhere.** `=<X>`, `=name<X>`, `=<X>name`, `=<X>#name`,
   `@r:id=<X>`, `@r:id#name=<X>`, `@r:id=name<X>`, `^r:id=…`, and chain tokens
   (`x =fix+`) all go through `start_timing_len` and `parse_pomodoro_start_suffix`.
   None of them gets a separate rule.
2. **The sign is the direction, the digits are the amount.** `-` means earlier and
   `+` means later. A sign with no digits means one block.
3. **One sentence settles `+` in a name.** `+` followed by a letter joins components;
   `+` followed by digits or by nothing begins the offset.
4. **`#` is the escape hatch**, as it already is for `=#2fa` and `=#x2`. Hash names
   keep every byte, so a literal name `FIX+2` is spelled `=#fix+2`.
5. **Every refusal teaches the fix**, in the same tone as the existing retired-form
   messages.

---

## 4. Detailed design

### 4.1 Grammar

```text
<X>      := [D] [ SIGN [N] ]
SIGN     := "-" | "+"
D, N     := ASCII digits (0 and leading zeros allowed, as today)
```

| `<X>` | Duration | Offset | Example at 12:02 |
| --- | --- | --- | --- |
| (empty) | 25m | none | 1205–1230 |
| `3` | 15m | none | 1205–1220 |
| `-` / `-2` | 25m | 5m / 10m earlier | 1200–1225 / 1155–1220 |
| `+` | 25m | 5m later | **1210–1235** |
| `+3` | 25m | 15m later | **1220–1245** |
| `2+` | 10m | 5m later | **1210–1220** |
| `3+2` | 15m | 10m later | **1215–1230** |

Placement mirrors `-`:

- **Bare names: trailing timing is canonical.** `=fix+`, `=fix2+`, `=bugs3+2`, and
  `=bugs3+2~1` all work, with the `~<K>` drop list last as today.
- **Leading timing is accepted** for symmetry with the existing `=-2bugs` and
  `=3-1bugs`: `=+2bugs`, `=3+1bugs`. Docs, completion, and fit drafts should emit the
  trailing form, because `=+bugs` reads like "add BUGS". Today `=3+bugs` is an error
  and `=+bugs` is prose, so nothing that works changes.
- **Hash names take timing before `#`:** `=3+1#deep-work` and
  `@foo:bar=2+#"DEEP WORK"`.
- **Link starts:** `@foo:bar=+3`, `@foo:bar=fix2+`, `@foo:bar#fix=+3`, and
  `^foo:bar=+`.

### 4.2 Lexing (bob-cli)

- `start_timing_len`: accept `[-+]` where it currently accepts only `-`.
- `bare_start_name_len`, after taking the run of selector bytes:
  1. If the run's last `+` is followed only by digits or nothing, the name ends before
     that `+`.
  2. Then strip trailing digits as today.
  3. If the remaining name ends in `+` (`=fix++`, `=fix2++`), it is not a bare name and
     gets a teaching error.

  Worked examples:

  - `fix2+` → `fix` + `2+`
  - `bob+decks` → `bob+decks` (unchanged)
  - `bob+decks2+1` → `bob+decks` + `2+1`
  - `b2b+2` → `b2b` + `+2`
  - `fix+2fa` → `fix+2fa` (unchanged)
- `can_spell_bare`: also reject names that end in `+`. That keeps `=#fix+` legal for a
  literal name and stops the "`#` is retired" check from rewriting it into an offset.
  The existing retired-hash message for `=3#fix+` currently teaches `=3fix+`, so this
  rejection matters.
- `trailing_glued_timing`: accept `+` like `-`, so completion keeps `fix10+3` when it
  replaces the name. Example: `=de|3+1` plus DEEP WORK becomes `=3+1#deep-work`.
- Bare versus counted is unchanged: `=+` is bare (`=+ foo` stays prose, like `=- foo`)
  and `=+2` is counted (`=+2 foo` is an invalid-start error, like `=-2 foo`).

### 4.3 Model, math, JSON

- **Model.** Keep `PomodoroStartSpec.offset_units: u64` as the magnitude and add
  `offset_direction: Earlier | Later`. `start_block_minute` uses `checked_add` for
  `Later`; the round-up and the modulo-1440 display stay as they are.
- **JSON.** Keep `offset_units` as the magnitude and add
  `offset_direction: "earlier" | "later"` whenever `offset_units > 0`. This mirrors the
  existing `pomodoro_shift.direction`. Example:
  `{"raw":"2+","duration_units":2,"offset_units":1,"offset_direction":"later"}`. The
  same field goes on the `pomodoro_start` result object of `bob capture`.
- **Why not a signed `offset_units`.** It would also be backward compatible, with
  `+N` written as `-N` in the formula's sign. But `"offset_units": -2` meaning "10
  minutes later" is the opposite of what the user typed, and the house JSON style
  already uses direction plus magnitude.
- **Human line.** Show the typed sign: `=fix2+ (10m, offset +1u)`,
  `=-2 (25m, offset -2u)`, `=3 (15m, offset 0u)`.
- **Versioning.** Bump `GRAMMAR_REVISION` to 17. Commit as `feat(capture)!:`: the name
  lexing changes (`=fix+`) and the meaning of `offset_units` is no longer implicitly
  "earlier". Per `decisions:bob-cli-releases-ride-a-daily-train`, don't touch
  `Cargo.toml` or `CHANGELOG.md`.

### 4.4 Semantics in every start context

| Context | Behavior with `+N` |
| --- | --- |
| Fresh `=…+N` | Starts the selected entry at `S = ceil((now+5N)/5)·5`. **Same as `=… ++N`** |
| Restart (`=+` while running) | Fresh timing from `S`, with the override warning. **Same as `= ++`** |
| Swap (`=fix+` while BUGS runs) | Non-empty `<X>` means fresh timing from `S`. **Not** the same as `=fix ++`, which shifts the kept clock. This mirrors today's `-` |
| Link start `@r:id=+N` | Same guards as today ("finish the current Pomodoro first"). Starts the type-placed or queued entry at `S` |
| MEET | Only an **empty** suffix follows the event run (`meet_event_run.rs:691`). `=meet+` is written timing, like `=meet-` |
| Unnamed start near a MEET | The join check uses `[S, S+5)`, so `=+2` at 9:52 joins a 10:00 meeting |
| Event warnings | `pomodoro_runs_past_event` and `pomodoro_starts_during_event` use the new span. The fit draft keeps the sign (`=2+2`, `=fix2+2`) |
| Chains | `x =fix+`, `=fix+ +2`, and `=+ x` run left to right as today |
| Midnight | Wraps modulo 1440, the same as `-`, `=`, and `++`. See §6 for an optional guard |
| Overflow | The existing "Pomodoro start suffix is too large…" error |

Ways to undo an accidental far-future start: `x0` resets a session with no notes to a
placeholder, and `--N` shifts it back.

### 4.5 Refusals that teach the fix

Drafts of new messages, in the existing voice:

| Typed | Message |
| --- | --- |
| `=3-1+2`, `=+1-2` | `` `=3-1+2` gives two offsets: write one, `-` for earlier or `+` for later (`=3-1` or `=3+2`) `` |
| `=fix++`, `=fix2++` | `` `=fix++` takes one `+`: write `=fix+2` to start 10 minutes later, or `=fix ++` to start and then shift `` |
| `=#fix+` (bare-spellable check) | Stays valid: a literal name `FIX+` |
| `x=fix+`, `x=3+2`, `x=+` | `` `x=` records finished work and cannot start later; to start FIX 5 minutes from now write `=fix+`, to close first write `x =fix+`, or place past work with a segment (`x=fix~`) `` |
| `@foo:bar= ++3` (new, §4.7) | `` `++3` after `@foo:bar=` would become task text; to start it 15 minutes later write `@foo:bar=+3`, or put `++3` on its own line `` |
| Shape error text (`markers.rs:483`) | Becomes: "<X> is empty, digits, a sign (`-` earlier, `+` later) with optional digits, or digits followed by a sign and optional digits (`=`, `=3`, `=-2`, `=+2`, `=3+1`)" |

### 4.6 Why `x=` stays out

- **Meaning.** `x=` records what already happened and ends at the next boundary. A
  later start pushes the record into the future, at which point it is a start, not a
  record. Every reasonable reading is already covered: `=fix3-2` ("I've been on it 10
  minutes and want 15 in total"), `x =fix+` ("close now, start FIX in 5"), or `~`
  segments for placing past work.
- **Syntax.** `+` already means the far edge in `~n+`, so `x=3~1+2` would be
  ambiguous.
- **History.** Backward offsets on `x=` were removed on purpose and replaced with
  segments. Reintroducing an offset in the other direction would reopen that decision.
- **Lexer consistency.** `x=` reuses `bare_start_name_len`, so `x=fix+` stops being a
  `FIX+` name either way. Making it a teaching error is the deliberate version of that
  change.

### 4.7 Hardening I recommend shipping alongside

A link-start item whose only body text is session operators (`@foo:bar= ++3`,
`@foo:bar= +2`, `@foo:bar= x`) should be refused with a teaching error instead of
creating a task titled `++3`. It is a small, separate change. It fits here because
this feature finally gives the error something to teach. If you would rather keep
that change separate, it can be its own bead.

### 4.8 Editor and completion (bob-cli, used by Mac Capture)

- Spans for `=fix2+`: `pomodoro_start [0,1)`, `pomodoro_name [1,4)`,
  `pomodoro_start [4,6)`. Mac renders whatever spans bob returns.
- A cursor inside the offset returns an empty success, like any other timing. A
  trailing `+` is never prose-terminal (`=fix+` is a session token and `@foo:bar=+` is
  a marker token), so the parent-task picker never opens.
- **Optional polish.** At `=bob+|` (cursor right after a dangling `+`), still offer
  merged-name continuations such as `BOB + DECKS`, while submitting the draft as typed
  starts BOB 5 minutes later. The lone `+` is already handled this way. It is low
  priority because `=bob` already prefix-matches `BOB + DECKS`.
- Highlighting flickers for one keystroke while you type `=bob+d…`. The same thing
  already happens with `=fix2` becoming `=fix2a`.

### 4.9 Obsidian parity (bob-plugins)

- `TRIGGER_RE`: change `se\d*(?:-\d*)?` to `se\d*(?:[-+]\d*)?`. `LEDGER_TRIGGER_RE`:
  change to `^se(\d*)(?:([-+])(\d*))?$`.
- Pass the sign through `parseTrigger`, then `computeRange` (`030-snippets.js:1`),
  then the MEET fit token (`035-meet-event-run.js:808`).
- Extend the vector harness so `=+2`-style tokens map to `se+2`, and add shared
  `pomodoro_clock` and `meet_event_run` vectors in bob-cli.
- If the plugin change can't land in the same train, rewrite the parity sentence in
  the docs ("`=<X>` extends `se<X>` with `+`") rather than leave it false. Shipping
  both together is better.

### 4.10 Docs to update

- `docs/capture.md`:
  - The `se<X>` table (`:1648`) and the recognition grammar (`:3550`).
  - The grammar-at-a-glance rows. Replace the inaccurate `=bugs+2` row (`:398`) and
    the spacing paragraph (`:5640`) with "`=bugs+2` starts BUGS 10 minutes later".
  - The retired and rejected tables, and the `x=` past section.
  - The fit-draft list in "Running into an event".
- `docs/reference/capture-syntax.md`: the token index row for `=<X>`, the overloaded
  `+` marker rows, and new examples.
- CLI help in `capture_parse.rs` and `capture_complete/cli.rs` (the "grammar: 17"
  text), plus `docs/reference/cli/*`.
- `bob-plugins/docs/bob-ledger-tools.md`.
- Read `sase/memory/docs.md` and `cli_rules.md` before editing.

---

## 5. Implementation sketch

Precedent for size: `79709fed` ("glue start and past timing to Pomodoro names") took
back name bytes for timing in 22 files. This change is smaller.

1. **bob-cli lexer and model (one stitch).**
   - `item.rs`: `start_timing_len`.
   - `bare_name.rs`: `bare_start_name_len`, `can_spell_bare`, and
     `trailing_glued_timing`.
   - `tokens.rs`: `parse_pomodoro_start_suffix`.
   - `model.rs`: add the direction to `PomodoroStartSpec` and its serialization.
   - `meet_event_run.rs`: the `start_block_minute` sign.
   - `event_conflict.rs`: the fit-token sign.
   - `capture_parse.rs`: the human line.
   - `markers.rs`: the shape error.
   - `past.rs`: the `x=` teaching error.
   - The link-operator-body refusal (§4.7).
   - Bump `GRAMMAR_REVISION`.
2. **Tests.**
   - Grammar tables, including every row in §1.2 with its new expected parse.
   - Editor spans.
   - Completion that keeps `+` timing.
   - CLI dry runs for fresh, restart, swap, link, MEET join, the event fit, and
     midnight wrap.
   - The `x=` refusals.
   - Shared vectors.
3. **Docs** as listed in §4.10.
4. **bob-plugins**: the `se<X>` regex, sign propagation, and harness and vectors,
   followed by `bob plugins sync`.
5. **Mac Capture**: no code change is required. Optionally add a fixture with
   `offset_direction` to pin decoding.

---

## 6. Risks, open questions, follow-ups

- **Behavior changes.** `=fix+`, `=fix2+`, `=bugs+2`, `@r:id=fix+`, and `x=fix+` no
  longer create names ending in `+` or `+digits`. `=+…` drafts stop being prose. The
  vault survey suggests nothing in use is affected. The `!` commit marker makes the
  break visible.
- **Midnight (optional guard).** `=+3` at 23:55 writes `0010–0035` into today's note.
  This already happens with `=` at 23:58 and with `++`. A guard that refuses any start
  form crossing midnight would be a separate, cross-cutting decision. I would not
  couple it to this feature, because it would break `=fix2+ ≡ =fix2 ++` at the
  boundary.
- **Follow-up (separate bead): the timer during the lead time.** `bob_pomodoro`,
  tmux, and the Mac menu-bar indicator should show something like `[in 8m] FIX` before
  the start instead of `[<33m]`. This gap already exists for `=` at :02 and for future
  MEET starts. `+N` makes it more visible.
- **Decision record.** If you adopt this, it is worth a `decisions:` record along the
  lines of "start offsets are signed; `+` before digits is timing, `+` before a letter
  is a component". It changes a rule that crosses repos: the name lexer, `se<X>`
  parity, and Mac spans.
- **Open: `+0`.** I recommend accepting it (§Requirement adjustments 3). If you want
  `+N` to be strictly positive, `-0` should become an error too, to keep the two signs
  symmetric.

---

## Requirement adjustments

1. **No `x=…+N`** (§4.6). Teaching errors point to `=fix+` and `x =fix+`. You asked
   about `x=<X>` only if appropriate; I think it is not.
2. **Restated equivalence.** `=<X>+N` is the same as `=<X> ++N` for fresh starts,
   restarts, and link starts. In a swap, a non-empty `<X>` means fresh timing from now,
   exactly as `-` already does, so `=fix+` is 1210–1235 while `=fix ++` is 1145–1210 in
   §1.3's example. `@foo:bar=+3` matches your intent ("link, start, 15 minutes
   later"), but `@foo:bar= ++3` isn't a working spelling today (§1.4).
3. **`+0` is valid and means "no offset"**, like `-0` inside `<X>`. `<X>` is a timing
   literal, not an operator. The `++0` "moves nothing" refusal stays because `++` is an
   operator.
4. **Trailing `+` and `+digits` leave the bare-name charset.** `#` keeps literal names
   such as `=#fix+2`.
5. **Leading placements are accepted** (`=+2fix`, `=3+1#deep-work`) for symmetry with
   `-`. Trailing placement is canonical for bare names.
6. **Two additions:** refuse `@r:id= ++N`-style operator bodies (§4.7), and update
   Obsidian `se<X>` in the same train (§4.9).

## Recommended solution

Extend `<X>` from `[D][-[N]]` to **`[D][±[N]]`**:

- **Lexing.** In bare names, `+` followed by digits or by nothing is the offset;
  `+` followed by a letter stays the merged-name separator. `#` names keep every byte.
- **Behavior.**
  - Fresh starts, restarts, and link starts begin at
    `ceil((now + 5N)/5)·5`. That is byte-for-byte what `=<X> ++N` writes.
  - Swaps use fresh timing, like `-`.
  - MEET calendar runs apply only to an empty suffix.
  - Event warnings and fit drafts keep the sign.
- **`x=`.** Leave `+N` out and teach `=fix+` and `x =fix+` instead.
- **Contracts.**
  - JSON keeps `offset_units` as the magnitude and adds `offset_direction`
    (`earlier`/`later`).
  - The human line shows the typed sign.
  - `GRAMMAR_REVISION` goes to 17, committed as `feat(capture)!:`.
  - Obsidian `se<X>` learns `+` in the same release train, so "`<X>` is exactly
    `se<X>`" stays true.
- **Alongside.** Refuse `@route:id= ++N` operator bodies, fix the stale `=bugs+2`
  doc rows, and file the "starts in Nm" timer display as a follow-up.

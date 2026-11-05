# Past Pomodoro Time Range Block Selection (`x=<E><e>=<X>`)

**Research & Architectural Design Report**
**Researcher:** `gem` (5-Researcher Swarm)
**Date:** November 2026
**Target Repositories:** `bob-cli` (primary), `bob-mac-capture` (linked)

---

## Executive Summary & Bottom Line

The user proposes extending the `x=<E>=<X>` capture syntax by allowing `<E>` to take an optional `<e>` suffix—specifically `~`, `~<n>[+]`, or `~~`—before the repair `!` marker. This extension gives the user explicit, relative control over the temporal placement of recorded past Pomodoros by targeting discrete "time range blocks" in today's daily file rather than always anchoring to `ceil5(now)`.

### Bottom Line Recommendation

**Build it.** The feature is conceptually sound, addresses a major gap in the daily capture workflow, and transforms `x=` into a complete, expressive ledger-editing language. When viewed through the lens of a **topological partition of the day's timeline**, the proposed system is mathematically rigorous and highly elegant.

However, to ensure it is intuitive, reliable, and beautiful in daily practice, **five critical requirement adjustments** must be adopted:

1. **Contextual Dash Rewrite Assist (`expand_past_dash`)**: Implement the `-` to `~` replacement strictly as a contextual typing assist in `bob capture-rewrite` (so `bob-mac-capture` remains a thin client per `decisions:mac-capture-is-a-thin-client`), while preserving hyphens in Pomodoro names and providing helpful teaching errors on the CLI.
2. **Explicit Truncation & Non-Zero Duration Rules**: Formalize that `~` (tail block 0) truncates at `ceil5(now)` to prevent future leaks, but requires an elapsed duration of at least 5 minutes (1 block). If 0 minutes have elapsed since the last session ended, `x=~` must fail cleanly with a helpful error.
3. **Partition Normalization for Calendar Overlaps & Contiguity**: Define the daily partition over the union of occupied intervals. Overlapping closed sessions (common with Google Calendar `MEET` sync) merge into single occupied spans for gap discovery; contiguous pomodoros generate zero-length gaps which are pruned from the block catalog.
4. **Strict Scope for Automatic Gap Capping vs. Overflow Repair**: Confine silent automatic truncation strictly to the `~` (tail block 0) form. When targeting past gaps (`~n` for $n \ge 2$), if a requested duration exceeds the gap, do not silently truncate; instead, route through Bob's existing overlap preflight to require `!` before trimming an adjacent session.
5. **Redundant & Unsupported Form Teaching Errors**: Intercept redundant forms like `x=~+` (which is the default behavior of `x=`), `x=~0` (which is `~`), and `x=~~+` (which is `~~`) with clear teaching rewrites.

---

## 1. System Critique: Is This a Good Idea?

### 1.1 The Problems It Solves

Under the current `x=<E>=<X>` grammar shipped in `bob-cli-h2.3`, past Pomodoros are anchored exclusively to $T = \text{ceil5}(\text{now})$. While backward stacking (`x=A@2 x=B@3`) allows backfilling contiguous runs of sessions leading up to the current moment, it has four major operational limitations:

1. **Mental Arithmetic on Elapsed Gaps**: If Bryan's last pomodoro finished at 09:00 and it is currently 09:13 ($T = 09:15$), typing default `x=` allocates 25 minutes ($08:50\text{--}09:15$), which collides by 10 minutes with the 09:00 session. To avoid collision, Bryan must mentally calculate: "09:15 minus 09:00 is 15 minutes, which is 3 blocks, so I must type `x=3`." With `x=~`, he simply types `x=~` and Bob automatically snaps the start to 09:00 and caps at 09:15.
2. **Inability to Fill Historical Gaps via Capture**: If an unrecorded 15-minute chore was performed in a break between 08:00 and 08:30 earlier in the morning, `x=` cannot target it because it cannot reach past an intervening completed session without destroying or trimming it. The only workaround was manual text editing in Obsidian.
3. **Surgical Retroactive Edits**: If Bryan realizes the first 10 minutes of an earlier 08:30–09:00 session was actually spent on email, he can now write `x=email2~1!=!1` to carve out 08:30–08:40 and automatically adjust the remaining session to 08:40–09:00.
4. **Pre-Dawn / Early Morning Backfill**: Work done before the day's first logged session can now be logged cleanly with `x=~~` without risking an illegal rollover across midnight.

### 1.2 Potential Usability & Semantic Traps (Critiques)

While the benefits are significant, the plan introduces subtle hazards that must be carefully engineered:

#### Hazard 1: Index Parity Shift (Sessions vs. Gaps)
Because `<n>` counts *both* completed pomodoros (Type 2) and inter-session gaps (Type 3) in a single reverse-chronological sequence:
- If today's sessions had gaps between them:
  - Block 0: Tail gap to now
  - Block 1: Last pomodoro
  - Block 2: Gap before last pomodoro
  - Block 3: Penultimate pomodoro
- If today's sessions were contiguous (back-to-back, no gaps):
  - Block 0: Tail gap to now
  - Block 1: Last pomodoro
  - Block 2: Penultimate pomodoro (now Block 2 instead of Block 3!)

*Impact*: The user cannot know a priori whether `~2` targets a gap or a session without remembering whether they took a break between their last two sessions.
*Mitigation*: This is where **Bob Mac Capture's live preview** shines. Because `bob capture --dry-run` plans the exact window and displays the candidate headline in the capture panel in real time (< 5 ms), the user gets immediate visual confirmation of the target range before committing the draft. Furthermore, on the CLI, dry-run or error output clearly identifies the target.

#### Hazard 2: Visual & Lexical Ambiguity with Close Drop (`x=~2` vs. `x==~2`)
In Bob capture syntax, `~` is heavily associated with dropping links in close specs (`x==~2` drops task link 2). Previously, `past.rs` explicitly rejected `x=~2` and taught `x==~2`.
If `x=~2` is now valid syntax for targeting time block 2, a typo where a user forgets the second `=` in a drop gesture will execute as a time block target!
*Mitigation*: The lexer must enforce clean separation:
- Inside `<E>` (before second `=`): `~` is a time block selector.
- Inside `<X>` (after second `=`): `~` is a task drop selector.
- Teaching errors must be updated: if a user types `x=~` or `x=~2`, it is parsed as a time block; if an invalid close spec is supplied, existing close diagnostics handle it.

#### Hazard 3: Keyboard Ergonomics (`-` vs. `~`)
On standard QWERTY keyboards, `~` requires `Shift + \``, whereas `-` is a single top-row keystroke. However, `-` cannot be the canonical grammar token because `-` in start syntax means a minute offset (`=5-2`), whereas `~` means a discrete block selector.
The user's desire to auto-replace `-` with `~` in `bob-mac-capture` is brilliant and mirrors existing assists (such as `;` $\to$ `:`, `.` $\to$ `^`, and `/` $\to$ `#`). But this replacement must be lexical and contextual to avoid breaking Pomodoro names (e.g., `#deep-work`).

---

## 2. Alternatives Considered

| Alternative | Description | Pros | Cons | Verdict |
|---|---|---|---|---|
| **A. User Proposal: Unified Relative Blocks (`~`, `~n[+]`, `~~`)** | Treat the day's timeline as a discrete partition of blocks numbered backwards from now. | Clean topological model; compact syntax; covers gaps, sessions, tail, and morning. | Parity shift (gaps and sessions share one index space). | **Recommended** (with live preview mitigation). |
| **B. Segregated Indexing (`~n` for gaps, `@n` or `^n` for sessions)** | Use different sigils for gaps vs. completed sessions. | Eliminates parity shift; user always knows if they are targeting a gap or a session. | Proliferates sigils; `@` is already retired/reserved in past grammar; more symbols to learn. | **Rejected**: Overcomplicates grammar for minimal gain. |
| **C. Absolute Wall-Clock Ranges (`x=0830-0840`)** | Allow explicit `HHMM-HHMM` in `<E>`. | Completely unambiguous; no relative counting needed. | High typing friction (9 characters vs. 4); mental math on clock times required. | **Rejected**: Defeats the purpose of fluid capture. |
| **D. Cumulative Offset Arithmetic (`x=-3` or `=N-M x`)** | Allow offset in blocks/minutes from current time. | Familiar from start syntax `=N-M`. | Completely breaks down across non-continuous history and existing closed sessions. | **Rejected**: Already thoroughly analyzed and rejected in `recording_past_pomodoros__final.md`. |

---

## 3. Requirement Adjustments (Called Out)

To ensure this feature integrates seamlessly into the existing `bob-cli` and `bob-mac-capture` architectures, the following 5 adjustments are specified:

### Adjustment 1: Contextual Dash Rewrite Assist (`expand_past_dash`)
**Rule**: The replacement of `-` with `~` must be governed by `bob capture-rewrite` under a new rule code `expand_past_dash` (or as an extension of `expand_sigil_alias`).
- **Trigger**: The caret is immediately after `-` inside the `<E>` portion of a line starting with `x=`.
- **Condition**: The caret is **NOT** inside a `#` name or quoted literal `#"..."` (where hyphens are legitimate name characters, such as `x=#deep-work`).
- **Action**: Emit a native single-edit replacement replacing `-` with `~`. If typed after an existing `~` (e.g., typing `-` after `~`), it replaces `-` with `~` to produce `~~`.
- **CLI Behavior**: `bob capture-parse` and `bob capture` on the CLI do not silently rewrite `-` in text arguments, but emit a teaching error: ``in past Pomodoros, use `~` instead of `-` to target time blocks: write `x=2~1` instead of `x=2-1` ``.

### Adjustment 2: Tail Block (`~`) Elapsed Time Gate ($\ge 5\text{m}$)
**Rule**: The `~` form (Type 4 block) computes the span $[S, E)$ where $S$ is the end of the last completed session and $E = \min(S + \text{duration}, \text{ceil5}(\text{now}))$.
- If $E - S < 5$ minutes: Refuse the capture!
  - Example: Last session ended at 09:00. It is currently 09:00 ($T = 09:00$). Typing `x=~` attempts to create a 0-minute session $[0900, 0900)$.
  - *Error message*: ``no time has elapsed since the last Pomodoro ended at 0900; cannot record a zero-length past Pomodoro with `x=~` ``.
- If $E - S \ge 5$ minutes: Truncate duration to $\lfloor(E - S) / 5\rfloor \times 5$ minutes. If untyped (default 25m), it takes the full available tail gap up to 25m.

### Adjustment 3: History Normalization & Contiguity Pruning
**Rule**: Time range blocks are derived strictly from a normalized timeline of closed timed rows:
- Contiguous rows (e.g., 0730–0800 and 0800–0830) have $R_{i+1}.\text{start} == R_i.\text{end}$. No Type 3 gap exists between them.
- Overlapping rows (e.g., calendar meetings synced via Gcal where $R_{i+1}.\text{start} < R_i.\text{end}$) are merged into a continuous occupied span for gap calculation. For Type 2 session targeting, individual row spans are preserved in reverse start-time order.

### Adjustment 4: Rejection & Teaching for Redundant Forms
**Rule**: Prevent confusing or ambiguous syntax with instant teaching rewrites:
- `x=~+` or `x=2~+`: Replaced with plain `x=` or `x=2`.
  - *Error*: `` `~+` is the default behavior of `x=`; omit `~+` to end at the current time: write `x=2` instead of `x=2~+` ``.
- `x=~0` or `x=~0+`: Replaced with `x=~` or `x=`.
  - *Error*: ``0 is implied by `~`; write `x=~` instead of `x=~0` ``.
- `x=~~+`: Replaced with `x=~~`.
  - *Error*: `` `~~` is always end-aligned before the first Pomodoro; write `x=~~` instead of `x=~~+` ``.
- `x=~~` starting before midnight: Reused midnight gate:
  - *Error*: ``x=~~ would start before midnight (2345); record at most N blocks today: x=N~~``.

### Adjustment 5: Multi-Member Stack Semantics with `<e>`
**Rule**: In a draft containing consecutive `x=` items:
- If an item specifies an explicit `<e>` target block, that item resolves its anchor independently to that block.
- If multiple consecutive items target the *same* block with start-alignment (`~` or `~n`), they tile forward within that block: item 1 starts at the block start, and item 2 starts where item 1 ends.
- If an item has *no* `<e>` suffix, it continues to use the existing backward stack relative to $T$.

---

## 4. Mathematical Model: The Daily Timeline Partition

Let today's daily file contain $M$ completed timed entries sorted chronologically:
$$R_1, R_2, \dots, R_M \quad \text{where } R_i = [s_i, e_i)$$

Let $T_0 = 00:00 = 0$ (midnight) and $T_{\text{now}} = \text{ceil5}(\text{now})$ (current time ceiling, capped at $1440$).

### 4.1 The Block Catalog
The day is partitioned into an ordered sequence of non-overlapping blocks:

1. **Morning Block (Type 1)**:
   $$B_{\text{morning}} = [0, s_1) \quad (\text{only if } s_1 > 0)$$
   *Targeted by*: `~~` (always end-aligned to $s_1$).

2. **Completed Session Blocks (Type 2)**:
   Each $R_i = [s_i, e_i)$ for $i \in \{1, \dots, M\}$.

3. **Inter-Session Gap Blocks (Type 3)**:
   For any pair where $s_{i+1} > e_i$:
   $$G_i = [e_i, s_{i+1})$$

4. **Tail Block (Type 4)**:
   $$B_{\text{tail}} = [e_M, T_{\text{now}}) \quad (\text{only if } T_{\text{now}} > e_M)$$
   *Targeted by*: `~` (start-aligned to $e_M$).

```
[00:00 ................. s1) [s1 ..... e1) [e1 ... s2) [s2 ..... e2) [e2 ........... T_now)
|--- Type 1 (~~) --------|--- Type 2 ----|-- Type 3 -|--- Type 2 ----|--- Type 4 (~) ------|
                           (Block 3)       (Block 2)   (Block 1)       (Block 0)
```

### 4.2 Reverse Indexing Mapping ($\mathbb{N} \to \text{Block}$)
We assemble the targetable blocks in reverse chronological order:
- **Index 0** $\implies B_{\text{tail}}$ (Type 4).
- **Index 1** $\implies R_M$ (Type 2, last completed pomodoro).
- **Index $k \ge 2$**: Traverse backwards from $R_M$:
  - If a gap $G_{M-1}$ exists before $R_M$, Index 2 is $G_{M-1}$, Index 3 is $R_{M-1}$, etc.
  - If no gap exists ($e_{M-1} == s_M$), Index 2 is $R_{M-1}$.

### 4.3 Window Determination Math
Given a target block $B = [B_{\text{start}}, B_{\text{end}})$ and requested duration $D = 5 \times \text{blocks}$:

1. **Start-Aligned** (default, no `+`):
   $$\text{start} = B_{\text{start}}, \quad \text{end} = B_{\text{start}} + D$$
   *Special Case for Type 4 (`~`)*:
   $$\text{end} = \min(B_{\text{start}} + D, B_{\text{end}}), \quad D_{\text{adj}} = \text{end} - \text{start}$$

2. **End-Aligned** (explicit `+`, or `~~`):
   $$\text{end} = B_{\text{end}}, \quad \text{start} = B_{\text{end}} - D$$

---

## 5. Grammar & Parsing Specification

### 5.1 BNF Grammar

```text
past_token   := "x=" E [ "!" ] [ "=" X ]
E            := [ name_or_dur ] [ e_suffix ]
name_or_dur  := D | name | "#" name | "#" exact_literal | D "#" name | name "@" D
e_suffix     := "~" | "~~" | "~" INDEX [ "+" ]
INDEX        := [1-9][0-9]*
X            := <existing PomodoroCloseSpec>
```

### 5.2 Rust Data Model Extensions

In `src/native/capture_language/model.rs`:

```rust
/// Target time range block selector in `x=<E><e>=<X>`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub(crate) enum PastTargetBlock {
    /// `~` (Block 0): Tail gap between last pomodoro and ceil5(now), start-aligned.
    Tail,
    /// `~~`: Morning gap from midnight to first pomodoro, end-aligned (+).
    Morning,
    /// `~<n>[+]`: Block n counting backwards from last completed pomodoro.
    Index {
        n: u32,
        end_aligned: bool,
    },
}

pub(crate) struct PomodoroPastSpec {
    pub(crate) raw: String,
    pub(crate) name: Option<String>,
    pub(crate) name_is_literal: bool,
    pub(crate) blocks: u32,
    pub(crate) blocks_typed: bool,
    pub(crate) target_block: Option<PastTargetBlock>, // <-- NEW FIELD
    pub(crate) repair: bool,
    pub(crate) close: PomodoroCloseSpec,
    pub(crate) stack: PastStackPos,
}
```

### 5.3 Lexing & Splitting in `past.rs`

In `split_past_token`:
1. Find repair `!` and second `=`.
2. Extract `e_raw`.
3. Scan for `<e>` suffix at the end of `e_raw`:
   - If `e_raw` ends with `~~`: target is `PastTargetBlock::Morning`.
   - If `e_raw` ends with `~[0-9]+[+]?`: parse index and optional `+`.
   - If `e_raw` ends with `~`: target is `PastTargetBlock::Tail`.
   - Any remainder before `<e>` is passed to existing duration and name parsing.

---

## 6. Detailed Trace of the User's Examples

**Context**:
- Completed 1: `0730-0800`
- Completed 2: `0830-0900`
- Future 1: `CHORE`
- Future 2: `READ`
- Current time: `09:13` $\implies T = 09:15$.

**Block Catalog**:
- Morning: $[0000, 0730)$ (Type 1, targeted by `~~`)
- Block 3: $[0730, 0800)$ (Type 2, Completed 1)
- Block 2: $[0800, 0830)$ (Type 3, Gap between Completed 1 and 2)
- Block 1: $[0830, 0900)$ (Type 2, Completed 2)
- Block 0: $[0900, 0915)$ (Type 4, Tail gap, targeted by `~`)

---

### Example 1: `x=~=!1`
- **Target**: Block 0 ($[0900, 0915)$, Type 4).
- **Duration**: Untyped (default 5 blocks = 25m).
- **Rule**: Start-aligned at 09:00. Cut off at block end (09:15). Adjusted duration: 15m (3 blocks).
- **Repair**: Overlaps no closed session; `!` forbidden on `<E>`.
- **Target Selector**: Next future placeholder (`CHORE`).
- **Outcome**:
  - Records `CHORE` with range **`0900-0915`** (`[t:: 15m]`).
  - Completes task 1 of `CHORE`.
  - Filed at end of completed pomodoros.

---

### Example 2: `x=read2~=!1`
- **Target**: Block 0 ($[0900, 0915)$, Type 4).
- **Name**: `READ`. Duration: 2 blocks (10m).
- **Rule**: Start-aligned at 09:00. End at $09:00 + 10\text{m} = 09:10$. ($09:10 \le 09:15$, no truncation needed).
- **Repair**: No closed overlap; no repair `!` needed.
- **Target Selector**: Resolves placeholder `READ`.
- **Outcome**:
  - Records `READ` with range **`0900-0910`** (`[t:: 10m]`).
  - Completes task 1 of `READ`.

---

### Example 3: `x=2~1!=!1`
- **Target**: Block 1 ($[0830, 0900)$, Completed 2).
- **Duration**: 2 blocks (10m).
- **Rule**: Start-aligned at 08:30. Window: `0830-0840`.
- **Overlap**: Overlaps Completed 2 ($0830\text{--}0900$). Trims its start edge by 10m.
- **Repair**: `!` is present on `<E>` $\implies$ valid trim.
- **Headline Rewrite**: Old Completed 2 headline rewritten from `0830-0900 [t:: 30m]` to `0840-0900 [t:: 20m]`.
- **Target Selector**: Next future placeholder (`CHORE`).
- **Outcome**:
  - Records `CHORE` with range **`0830-0840`**.
  - Completes task 1 of `CHORE`.
  - Chronologically inserted before the adjusted `0840-0900` session.

---

### Example 4: `x=2~1+!=!1`
- **Target**: Block 1 ($[0830, 0900)$, Completed 2).
- **Duration**: 2 blocks (10m).
- **Alignment**: End-aligned (`+`) at 09:00. Window: $09:00 - 10\text{m} = 08:50 \implies \mathbf{0850\text{--}0900}$.
- **Overlap**: Overlaps Completed 2. Trims its end edge by 10m.
- **Repair**: `!` is present $\implies$ valid trim.
- **Headline Rewrite**: Old Completed 2 headline rewritten to `0830-0850 [t:: 20m]`.
- **Outcome**:
  - Records `CHORE` with range **`0850-0900`**.
  - Completes task 1 of `CHORE`.
  - Chronologically inserted after the adjusted `0830-0850` session.

---

### Example 5: `x=2~2=!1`
- **Target**: Block 2 ($[0800, 0830)$, Type 3 Gap).
- **Duration**: 2 blocks (10m).
- **Alignment**: Start-aligned at 08:00. Window: **`0800-0810`**.
- **Overlap**: Fits entirely inside the gap $[0800, 0830)$. Overlaps zero closed sessions.
- **Repair**: No `!` on `<E>` (required to be absent).
- **Outcome**:
  - Records `CHORE` with range **`0800-0810`**.
  - Completes task 1 of `CHORE`.
  - Chronologically inserted between Completed 1 and Completed 2.

---

### Example 6: `x=2~2+=!1`
- **Target**: Block 2 ($[0800, 0830)$, Type 3 Gap).
- **Duration**: 2 blocks (10m).
- **Alignment**: End-aligned (`+`) at 08:30. Window: $08:30 - 10\text{m} = 08:20 \implies \mathbf{0820\text{--}0830}$.
- **Overlap**: Fits entirely inside the gap $[0800, 0830)$.
- **Repair**: No `!` on `<E>`.
- **Outcome**:
  - Records `CHORE` with range **`0820-0830`**.
  - Completes task 1 of `CHORE`.
  - Chronologically inserted after `0800` and before `0830`.

---

## 7. Typing Assist Architecture in `bob-mac-capture`

Per architectural decision `decisions:mac-capture-is-a-thin-client`, `bob-mac-capture` must never implement ad-hoc grammar rules in Swift. The `-` to `~` replacement is implemented via `bob capture-rewrite`:

```
User types '-' on Mac
      │
      ▼
NSTextView (CapturePanelController)
      │
      ▼
BobProcessClient.captureRewrite(draft, cursor)
      │
      ▼
bob capture-rewrite (src/native/capture_rewrite.rs)
      │  Rule: expand_past_dash
      ▼
Returns: { changed: true, rule: "expand_past_dash", replacement: "~", range: [pos-1, pos] }
      │
      ▼
CapturePanelModel.applyNativeSingleEditRewrite()
      │
      ▼
Native NSTextView replace without flicker or selection jump
```

### Contextual Rewrite Implementation Details
In `src/native/capture_language/rewrite.rs`:
```rust
fn expand_past_dash(raw_text: &str, cursor: usize) -> Option<DraftRewrite> {
    let start = cursor.checked_sub(1)?;
    if raw_text.as_bytes().get(start) != Some(&b'-') {
        return None;
    }
    // Verify line begins with "x="
    let line_start = raw_text[..start].rfind('\n').map_or(0, |i| i + 1);
    let line = &raw_text[line_start..];
    if !line.starts_with("x=") {
        return None;
    }
    // Verify cursor is in <E> before repair ! or second =
    let token_text = line.split_whitespace().next()?;
    let split = split_past_token(token_text)?;
    let rel_cursor = start - line_start;
    if rel_cursor >= split.e_end {
        return None; // Inside close spec or repair
    }
    // Verify NOT inside a # name
    if let Some(hash) = token_text.find('#') {
        if rel_cursor >= hash {
            return None; // Inside exact or hash name
        }
    }
    // Valid trigger: rewrite '-' to '~'
    Some(DraftRewrite {
        rule: Some(RewriteRule::ExpandPastDash),
        text: format!("{}~{}", &raw_text[..start], &raw_text[cursor..]),
        cursor: Some(cursor),
        summary: None,
        edits: vec![TextEdit { start, end: cursor, replacement: "~".to_string() }],
        notices: Vec::new(),
    })
}
```

---

## 8. Implementation Roadmap

### Phase 1: Lexer, Grammar, and Typing Rewrite (`bob-cli`)
- Update `split_past_token` and `validate_past_e` in `src/native/capture_language/past.rs`.
- Add `PastTargetBlock` to `PomodoroPastSpec` and wire representations in `capture_parse.rs`.
- Implement `expand_past_dash` in `rewrite.rs` and register `RewriteRule::ExpandPastDash`.
- Add golden tests in `tests/past.rs` and `tests/rewrite.rs`.

### Phase 2: Timeline Partitioning & Execution Preflight (`bob-cli`)
- Implement `collect_time_range_blocks` in `src/native/capture/pomodoro_past.rs`.
- Update `compute_preflight` in `plan.rs` to read staged day content and resolve target windows.
- Integrate with existing `preflight_overlaps` and `TrimPlan`.
- Add exhaustive tests for:
  - Empty day / no pomodoros.
  - Back-to-back contiguous pomodoros.
  - Calendar `MEET` overlap coalescing.
  - Truncation of `~` at `ceil5(now)`.
  - Rejection of $0$-length elapsed tail gaps.

### Phase 3: Mac Client Integration (`bob-mac-capture`)
- Add `"expand_past_dash"` to `applyNativeSingleEditRewrite` whitelist in `CapturePanelModel.swift`.
- Update `PastWire` decoding in `CaptureModels.swift` to handle optional `target_block`.
- Verify live preview display of trimmed headlines and target blocks in `CapturePanelView.swift`.
- Run macOS CI test gate (`scripts/dev/macos-ci-check`).

---

## 9. Conclusion

The proposed `<e>` extension is a stellar design addition. It replaces error-prone mental math with an intuitive, relative block-targeting model that fits naturally into Bob's existing daily ledger architecture. By adopting the 5 refined requirements—especially contextual rewrite in `bob capture-rewrite` and strict overlap/truncation boundaries—the implementation will be robust, elegant, and a pleasure to use.

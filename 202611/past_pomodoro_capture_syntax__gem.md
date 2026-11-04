# Atomic Past Pomodoro Capture Syntax (`x=<E>=<X>[!]`)
**Independent Architectural Research & Language Design Report**
**Researcher ID:** `research.38.gem`
**Date:** November 2026
**Target System:** `bob-cli` (Capture Language, Pomodoro Ledger Engine, Bob Mac Capture)

---

## Executive Summary

Capturing work retroactively is one of the most frequent workflows in day-to-day productivity tracking. When entering deep focus, knowledge workers frequently start tasks without first executing a capture command or tapping an Obsidian hotkey. Upon surfacing 15 to 30 minutes later, the user faces unnecessary friction: they must mentally calculate past block counts and negative offsets (e.g., `=3-3 x`), risk conflicting with or overriding a running session, manually close the session, and perform multiple chained operations just to record what already occurred.

This report independently evaluates the proposed `x=<E>=<X>[!]` capture syntax designed to solve this problem. The syntax introduces an atomic "start-and-close past Pomodoro" primitive into `bob-cli`.

### Key Research Findings & Design Verdicts

1. **Strategic Value:** The proposal is **strongly recommended**. It eliminates a primary friction point in Bob's GTD ledger workflow. By anchoring time calculations to the current 5-minute block boundary and propagating offsets backwards across chained entries, it completely eliminates mental arithmetic for retroactive time logging.
2. **Grammar & Lexer Architecture:** 
   - The token prefix `x=` represents completely unallocated syntax space in Bob capture. It introduces zero backward compatibility breaks or collisions with existing capture items, prose, task locators, or URLs.
   - The structure `x=[<E>][=<X>][!]` is mathematically sound and cleanly separable into start specification `<E>`, close specification `<X>`, and force/steal modifier `!`.
   - **Syntax Disambiguation:** We resolve the apparent ambiguity between task completion (`x!`) and time-stealing (`!`) with a deterministic grammar rule: trailing `!` outside `<X>` (or without a second `=`) denotes overlap stealing. When `<X>` itself ends with `!` (completing all tasks) and time-stealing is also requested, it renders unambiguously as `x=<E>=!!` or `x=<E>=*3!`.
3. **Disallowing Negative Offsets (`-<N>`):**
   - Disallowing `-<N>` inside `<E>` is an **excellent architectural constraint**. In forward starts (`=<E>`), `-<N>` was required to pull a session into the past. In `x=`, the entire premise is that the operation is already past-anchored; allowing `-<N>` would introduce confusing double-negative semantics.
4. **Multi-Token Backwards Propagation:**
   - For chained past Pomodoros on a single line (e.g., `x=build@2 x=fix@3`), evaluating tokens from right to left (latest to earliest) against the current 5-minute block anchor cleanly produces adjacent, non-overlapping half-open intervals ($[0900, 0910)$ and $[0910, 0925)$ at $0921$). Furthermore, this mirrors chronological order in the daily note's ledger.
5. **Overlap Policy & Time Stealing (`!`):**
   - Error-by-default on ledger overlap protects historical ledger integrity.
   - Stealing time via `!` is strictly defined as **tail truncation** of an immediately preceding past session. Subsuming an entire past session ($0\text{m}$ duration), splitting an enclosed session, stealing from Google Calendar `MEET` sessions, or stealing from a currently running open session are strictly forbidden and return targeted errors.
   - Enforcing an error when `!` is supplied without an overlap provides an essential fail-fast safety check against user misconceptions.

---

## 1. Problem Formulation & Workflow Analysis

### 1.1 The Flow State Dilemma

The Pomodoro Technique assumes prospective commitment: an individual selects a task, starts a timer, works for a discrete interval, and then records the outcome. In practice, real-world knowledge work frequently diverges from this ideal:
- An urgent production incident or debugging session begins spontaneously.
- A colleague asks a quick question that turns into a 15-minute problem-solving session.
- An engineer experiences high-focus "flow" and dives straight into code before interacting with Bob.

When the work finishes, the user looks at the clock (e.g., $0921$) having worked since $0900$. 

### 1.2 Limitations of the Current Syntax

Currently in `bob-cli`, logging this past work requires one of several awkward workarounds:

```bash
# Workaround A: Manual negative offset calculation chained with close
bob capture '=5-5 x*1 fixed bug'

# Workaround B: Multi-step historical start then close
bob capture '=5-5'
bob capture 'x*1 fixed bug'

# Workaround C: Direct daily note Markdown surgery in Obsidian
# Manually typing '- [x] (**0900-0925** [t:: 25m]) — FIX'
```

#### Deficiencies of the Existing Workarounds:
1. **Mental Math Burden:** The user must calculate:
   - What was the 5-minute block 25 minutes ago?
   - How many 5-minute units is that from the current block?
   - For an earlier 10-minute block preceding a 15-minute block, the user must compute $=2-5$ (duration 2 units, offset 5 units).
2. **Running Session Collision:** If a timed Pomodoro is already open (or was left unclosed), forward start tokens (`=`) trigger override warnings (`pomodoro_override_running`) or link start refusals.
3. **Multi-Step Execution Overhead:** Running two capture commands takes time and risks leaving an open running session if interrupted.
4. **Lack of Overlap Protection:** Starting a session in the past with `=5-5` does not check whether its computed range collides with an existing closed session on the daily note.

---

## 2. Comprehensive Critique of the Proposed Plan

The user prompt requests an independent critique:
> *"Is this a good idea? Would you take a different approach? Make any adjustments to the requirements that you think are justified but clearly call these out. End your analysis with a recommended solution."*

### 2.1 General Assessment: Is This a Good Idea?

**Verdict: Yes. It is an exceptional, high-leverage enhancement.**

The feature addresses a genuine asymmetry in Bob's grammar. Bob's capture language possesses world-class ergonomics for:
- Creating tasks (`@route^block-id`, `@route:block-id`)
- Starting upcoming sessions (`=`, `=name`, `=3#bugs`)
- Modifying running sessions (`+2`, `-1`, `++3`, `--1`)
- Closing running sessions (`x`, `x!`, `x*`, `x~`, Work Log)

However, it lacked a first-class syntax for **retroactive completion**. Introducing `x=` fills this gap without requiring users to leave the capture interface.

---

### 2.2 Deep Syntax Critique: `x=<E>=<X>[!]`

Let us evaluate the specific token design: `x=<E>=<X>[!]`.

#### 1. The Leading Prefix `x=`
- **Elegance:** Combining `x` (close) and `=` (start) into `x=` is visually memorable. It conveys: *"Start (`=`) and immediately close (`x`) a session."*
- **Grammar Isolation:** In `src/native/capture_language/close_selection.rs`, `classify_whole_item_close` classifies tokens starting with `x` followed by digits, commas, `!`, `~`, `*`, or `@`. Any other character—including `=`—is rejected as a close token and falls through. In `item.rs`, `session_equals_token` looks for tokens starting with `=`. Thus, `x=` is completely unoccupied syntactic space.

#### 2. The Dual Equals Signs & The Empty `<E>` Dilemma (`x==1!2`)
A critical case arises when the user wants to use default duration (5 blocks / 25 minutes) with the next/top future Pomodoro, but desires specific task outcomes `<X>`:
- Under `x=<E>=<X>[!]`, if `<E>` is empty, the syntax yields `x==<X>` (e.g., `x==1!2`).
- **Visual Appearance:** To an untrained eye, `x==` looks like a programming equality check (`if x == ...`) or an accidental double keystroke.
- **Historical Precedent in Bob:** Bob previously retired the `==` prefix for starts because of collisions with Obsidian's highlight syntax (`==highlight==`). While `x==` does not collide with Obsidian highlights (since it starts with `x`), having consecutive identical punctuation characters requires careful justification.
- **Why It Is Necessary Here:** 
  Could we allow omitting the second `=` when `<E>` is absent? 
  Suppose a user types `x=1`.
  - Does `1` mean duration $= 1$ block ($5\text{m}$)?
  - Or does `1` mean keep task 1 in progress (close argument `<X>`)?
  They collide directly!
  In `<E>`, digits represent block count. In `<X>`, digits represent task lineup numbers.
  Therefore, an unambiguous separator between the start domain `<E>` and the close domain `<X>` is strictly required. The second `=` serves as this explicit boundary:
  - Text between the first `=` and the second `=` is `<E>`.
  - Text after the second `=` is `<X>`.
  When `<E>` is omitted, `x==<X>` explicitly states: *Default start spec, followed by close spec `<X>`*.
  *Recommendation:* Retain `x==<X>` as mathematically consistent and unambiguous, but support human-friendly alternatives like `x=5=<X>` or `x=@=<X>` if desired.

#### 3. Overloading the Exclamation Mark (`!`)
In Bob's capture language:
1. `x!` means complete all remaining tasks in the closed session.
2. `x!2` means complete task 2.
3. `!note:block-id` means complete a specific task in the vault.
4. In `x=<E>=<X>[!]`, `!` is proposed to mean "steal overlapping time from an existing past Pomodoro".

**Potential Ambiguity Scenarios:**
Consider `x=build=!`.
- Does this mean: `<X> = !` (complete all tasks), without time stealing?
- Or does it mean: `<X>` is omitted, and `!` is time stealing?

Consider `x=3!`:
- Prompt example: *"Assuming a past pomodoro for the 0855-0920 time range already exists, the `x=3!` capture would create a past pomodoro from the next/top future pomodoro with a time range of 0910-0925 and update the old past pomodoro's time range to 0855-0910."*
- In `x=3!`, there is NO second `=`. Here, `!` is unequivocally the time-stealing suffix!

**Deterministic Resolution Rule:**
We establish a rock-solid, unambiguous parsing rule:
1. The presence of the second `=` governs whether `<X>` exists:
   - **Form A (No second `=`):** `x=<E>[!]`
     - All characters between `x=` and optional trailing `!` form `<E>`.
     - An optional trailing `!` is strictly the **time-stealing modifier**.
     - `<X>` is absent (defaults to standard close behavior: all tasks marked worked and carried forward).
     - Examples: `x=build`, `x=3`, `x=build@2`, `x=3!`, `x=build!`.
   - **Form B (Second `=` present):** `x=<E>=<X>[!]`
     - Characters between the first `=` and second `=` form `<E>`.
     - Characters after the second `=` form `<X>`, with one exception: a trailing `!` that cannot be part of `<X>` or represents an explicit steal suffix.
     - In `<X>`, `!` is valid either standalone (`!`, meaning complete all) or followed by task numbers (`!1,3`).
     - If `<X>` specifies task completion AND the user also requests time stealing:
       - If `<X>` completes specific tasks: `x==!2!` (`<X> = !2`, steal $= \text{true}$).
       - If `<X>` completes all tasks: `x==!!` (first `!` is `<X> = !`, second `!` is steal).
       - If `<X>` parks task 3 and steals: `x=2#fix=*3! apollo agent` (`<X> = *3`, steal $= \text{true}$).

---

### 2.3 Critique of Offset & Timing Semantics

#### 1. Disallowing Negative Offsets (`-<N>`)
The prompt specifies:
> *"`<E>` should accept mostly the same type of values as the `=<E>` capture syntax (to start a pomodoro), with the exception of the `-<N>` syntax, since the `x=` syntax works in the past by default."*

**Critique:** This is **100% correct**.
In forward start `=<E>`, a syntax like `=3-2` meant "duration 3 blocks, start 2 blocks in the past".
In `x=`, the time anchor is already the past/current block boundary. If the user writes `x=3`, the duration is 3 blocks ($15\text{m}$) and the start time is 3 blocks in the past ($0925 - 15\text{m} = 0910$).
Allowing `-<N>` would raise confusing questions:
- Would `x=3-2` mean duration 3 ending 2 blocks ago? Or duration 3 offset by an additional 2 blocks?
- It would re-introduce the exact mental math burden `x=` is designed to eliminate.
- Disallowing `-<N>` keeps `<E>` strictly focused on: **name**, **duration**, and **queued task dropping** (`~<K>`).
- If an input contains `-<N>` (e.g., `x=3-2`), Bob should return an immediate teaching error:
  `"past Pomodoro syntax x= works in the past by default; omit negative offset '-2' and use duration only (e.g. 'x=3')"`

#### 2. The Current Time Anchor ($0921 \to 0925$)
In the prompt's examples, assuming a current clock of $0921$:
- `x=build` produces $0900\text{--}0925$.
- `x=build@2 x=fix@3` produces $0900\text{--}0910$ and $0910\text{--}0925$.
- `x=2#fix=*3` produces $0915\text{--}0925$.

**Why does a past Pomodoro end at $0925$ when the clock is $0921$?**
This reflects Bob's fundamental design:
- Bob divides the working day into discrete 5-minute quantum blocks.
- At $0921$, the active 5-minute block is $[0920, 0925)$.
- An individual who just finished a 25-minute Pomodoro at $0921$ worked during the blocks $0900\text{--}0905$, $0905\text{--}0910$, $0910\text{--}0915$, $0915\text{--}0920$, and is currently inside $0920\text{--}0925$.
- Rounding up to the nearest 5-minute boundary ($\lceil \text{now} / 5\text{m} \rceil \times 5\text{m}$) anchors the session to $0925$, matching the exact formula in `src/native/capture/meet_event_run.rs:start_block_minute`.
- When chained with an immediate forward start (`x=build =`), the past session ends at $0925$ and the new session begins at $0925$, achieving seamless continuity without gaps or overlaps.

---

### 2.4 Multi-Pomodoro Chaining Semantics

The prompt specifies:
> *"We should support using this syntax multiple times in a row, in which case the earlier past pomodoro time ranges that we add should be offset (i.e. subtracted) by the time ranges specified by subsequent past pomodoros (specified via later uses of the x= syntax on the same line)."*

#### The Mathematical Formulation of Chaining:
Given a sequence of $K$ past Pomodoro tokens on a single line:
$$T_1, T_2, \dots, T_K \quad (\text{left-to-right})$$

Let the base anchor time be $A = \lceil \text{now} / 5\text{m} \rceil \times 5\text{m}$ (e.g., $0925$ at $0921$).
Let each token $T_i$ have an extracted duration in minutes $D_i = (\text{block count}) \times 5\text{m}$. (If unstated, $D_i = 25\text{m}$).

We compute the half-open intervals $[s_i, e_i)$ by evaluating backwards from $K$ down to $1$:
$$\begin{aligned}
e_K &= A \\
s_K &= e_K - D_K \\
e_{K-1} &= s_K \\
s_{K-1} &= e_{K-1} - D_{K-1} \\
&\;\;\vdots \\
e_i &= s_{i+1} \\
s_i &= e_i - D_i
\end{aligned}$$

#### Verification against Prompt Examples:
For `x=build@2 x=fix@3` at $0921$:
- $A = 0925$ ($565\text{ min}$)
- $T_1 = \text{build}$, $D_1 = 2 \times 5\text{m} = 10\text{m}$
- $T_2 = \text{fix}$, $D_2 = 3 \times 5\text{m} = 15\text{m}$
- $e_2 = 0925$, $s_2 = 0925 - 15\text{m} = 0910$. Span for `FIX`: $[0910, 0925)$.
- $e_1 = s_2 = 0910$, $s_1 = 0910 - 10\text{m} = 0900$. Span for `BUILD`: $[0900, 0910)$.
- **Result:** BUILD $0900\text{--}0910$, FIX $0910\text{--}0925$. Exactly matches requirement!

#### Ledger Ordering Alignment:
In the daily note's ledger, completed Pomodoros appear in chronological order:
1. `BUILD 0900-0910`
2. `FIX 0910-0925`

Because $T_1$ represents the earlier interval and $T_2$ represents the later interval, **left-to-right syntactic order matches chronological ledger order**. This is intuitive and beautiful.

---

### 2.5 Overlap Policy & Time Stealing (`!`)

The prompt specifies:
> *"- We should show an error if one of the past pomodoros that we specified would overlap with an existing past pomodoro.*
> *- This error should be downgraded to a warning when the optional `!` suffix is provided, in which case the new past pomodoro should steal the overlapping time from the old past pomodoro (by updating the past pomodoro's time range appropriately).*
> *- It should be an error to use the `!` suffix when it is not needed."*

#### 1. Why Error-by-Default is Essential
Bob's ledger is the authoritative audit trail for Bryan's time and GTD reviews. Inadvertently creating overlapping sessions distorts daily stats, off-clock metrics, and Dataview queries. Refusing overlaps by default prevents accidental double-counting.

#### 2. The Strict Mechanics of "Stealing Time"
What does "stealing overlapping time" mean in every geometric configuration? We must establish strict architectural rules:

```
Case A: Tail Truncation (The Permitted Steal)
Existing E:  |==================| (0855 - 0920, 25m)
New N (!):              |===============| (0910 - 0925, 15m)
Overlap:                |-------| (0910 - 0920, 10m)
Result:
Updated E:   |==========| (0855 - 0910, 15m) -> Truncated by 10m
Created N:              |===============| (0910 - 0925, 15m)
```

```
Case B: Complete Subsumption / Enclosure (REFUSED)
Existing E:        |========| (0910 - 0920, 10m)
New N (!):   |====================| (0900 - 0925, 25m)
Problem: N completely encloses E. E's duration would become <= 0m.
Action: REFUSE. Destroying an existing session erases historical tasks/notes.
```

```
Case C: Mid-Span Enclosure (REFUSED)
Existing E:  |==============================| (0800 - 0930, 90m)
New N (!):            |==========| (0830 - 0855, 25m)
Problem: Stealing from the middle would split E into two disjoint sessions.
Action: REFUSE. A Pomodoro entry must be a single contiguous time interval.
```

```
Case D: Multiple Overlaps (REFUSED)
Existing E1: |==========| (0845 - 0905, 20m)
Existing E2:            |==========| (0905 - 0920, 15m)
New N (!):         |===================| (0855 - 0925, 30m)
Action: REFUSE. Stealing across multiple independent sessions indicates a corrupt capture draft.
```

```
Case E: Calendar / MEET Sessions (REFUSED)
Existing E:  |==================| (0900 - 0930 MEET Lunch with Alex)
New N (!):              |===============| (0915 - 0930)
Action: REFUSE. MEET sessions mirror external calendar reality. Bob cannot mutate calendar facts via capture.
```

#### 3. Error when `!` is Unnecessary
If a user passes `x=3!` at $0921$, and the resulting interval $[0910, 0925)$ does **not** overlap any existing session:
- Bob MUST halt and display an error:
  `"unneeded '!' modifier: past Pomodoro 0910-0925 does not overlap any existing session"`
- **Why this rule is brilliant:** It prevents users from blindly typing `!` as muscle memory, and immediately catches mistaken assumptions about the daily note's current state.

---

## 3. Formal Syntax & Grammar Specification

### 3.1 Extended BNF Grammar

```ebnf
PastPomodoroItem  ::= PastPomodoroToken ( Whitespace+ PastPomodoroToken )* ( Whitespace+ InlineWorkLog )?
PastPomodoroToken ::= "x=" StartSpec? ( "=" CloseSpec? )? StealModifier?

StartSpec         ::= ( BlockCount | BlockCount? "#" PomodoroName | PomodoroName ( "@" BlockCount )? ) DropSpec?
BlockCount        ::= [0-9]+
PomodoroName      ::= BareName | QuotedLiteral
BareName          ::= [A-Za-z][A-Za-z0-9&'()+,\.\/\-]*
QuotedLiteral     ::= '"' [^"]* '"' | '“' [^”]* '”'
DropSpec          ::= "~" [0-9]+ ( "," [0-9]+ )*

CloseSpec         ::= ( KeepList | ParkGroup | CompleteGroup | DropGroup | LastKeep )*
KeepList          ::= [0-9]+ ( "," [0-9]+ )*
ParkGroup         ::= "*" [0-9]* ( "," [0-9]+ )*
CompleteGroup     ::= "!" [0-9]* ( "," [0-9]+ )*
DropGroup         ::= "~" [0-9]+ ( "," [0-9]+ )*
LastKeep          ::= "@" [0-9]+ ( "," [0-9]+ )*

StealModifier     ::= "!"
InlineWorkLog     ::= [^\n\r]+
```

### 3.2 Token Disambiguation Matrix

| Typed String | Parsed `<E>` | Parsed `<X>` | Steal? | Meaning |
| :--- | :--- | :--- | :---: | :--- |
| `x=` | Empty (default 5 blocks, top future) | None (default close) | No | Past session $0900\text{--}0925$, carry tasks forward. |
| `x=3` | `3` (3 blocks = $15\text{m}$, top future) | None (default close) | No | Past session $0910\text{--}0925$, carry tasks forward. |
| `x=3!` | `3` (3 blocks = $15\text{m}$, top future) | None (default close) | **Yes** | Past session $0910\text{--}0925$, steal overlap from predecessor. |
| `x=build` | `build` (5 blocks, named BUILD) | None (default close) | No | Past BUILD session $0900\text{--}0925$. |
| `x=build@2` | `build@2` (2 blocks, named BUILD) | None (default close) | No | Past BUILD session $0915\text{--}0925$. |
| `x=build@2!` | `build@2` (2 blocks, named BUILD) | None (default close) | **Yes** | Past BUILD session $0915\text{--}0925$, steal overlap. |
| `x==1!2` | Empty (5 blocks, top future) | `1!2` (keep 1, complete 2) | No | Past session $0900\text{--}0925$; works task 1, completes task 2. |
| `x==1!2!` | Empty (5 blocks, top future) | `1!2` (keep 1, complete 2) | **Yes** | Past session $0900\text{--}0925$; works task 1, completes task 2; steals overlap. |
| `x=2#fix=*3` | `2#fix` (2 blocks, named FIX) | `*3` (park task 3) | No | Past FIX session $0915\text{--}0925$; parks task 3. |
| `x=fix@2=*3!` | `fix@2` (2 blocks, named FIX) | `*3` (park task 3) | **Yes** | Past FIX session $0915\text{--}0925$; parks task 3; steals overlap. |
| `x=build=!` | `build` (5 blocks, named BUILD) | `!` (complete all) | No | Past BUILD session $0900\text{--}0925$; completes all tasks. |
| `x=build=!!` | `build` (5 blocks, named BUILD) | `!` (complete all) | **Yes** | Past BUILD session $0900\text{--}0925$; completes all tasks; steals overlap. |

---

### 3.3 Walkthrough of User Prompt Examples

#### Example 1: `x=build` (Clock: $0921$)
- **Token Analysis:** Prefix `x=`, `<E> = build`, `<X>` is absent, `!` is absent.
- **Duration:** Default 5 blocks = $25\text{ minutes}$.
- **Anchor & Span:** Current anchor is $0925$. Start is $0925 - 25\text{m} = 0900$. Interval is $[0900, 0925)$.
- **Target Selection:** Looks for an open placeholder named `BUILD` (or creates `- [ ] () — BUILD`).
- **Ledger Mutation:** Rewrites to `- [x] (**0900-0925** [t:: 25m]) — BUILD`.
- **Task Effects:** Standard close: any child tasks under `BUILD` become Worked On (`[/]`) and carry to the next planned session.

#### Example 2: `x=build@2 x=fix@3` (Clock: $0921$)
- **Token Analysis:** Chained tokens $T_1 = \text{x=build@2}$, $T_2 = \text{x=fix@3}$.
- **Durations:** $T_1 = 2 \text{ blocks} = 10\text{m}$; $T_2 = 3 \text{ blocks} = 15\text{m}$.
- **Anchor Backwards Pass:**
  - Anchor $A = 0925$.
  - $T_2$ (`fix`): $e_2 = 0925, s_2 = 0925 - 15\text{m} = 0910$. Range: $0910\text{--}0925$.
  - $T_1$ (`build`): $e_1 = s_2 = 0910, s_1 = 0910 - 10\text{m} = 0900$. Range: $0900\text{--}0910$.
- **Ledger Placement:** Chronological order in daily note:
  ```markdown
  - [x] (**0900-0910** [t:: 10m]) — BUILD
  - [x] (**0910-0925** [t:: 15m]) — FIX
  ```

#### Example 3: `x=2#fix=*3 apollo agent` / `x=fix@2=*3 apollo agent` (Clock: $0921$)
- **Token Analysis:** `<E> = 2#fix` (or `fix@2`), `<X> = *3`, inline Work Log = `apollo agent`.
- **Duration:** 2 blocks = $10\text{ minutes}$.
- **Range:** Anchor $0925 \implies [0915, 0925)$.
- **Target Selection:** Resolves placeholder `FIX` and its queued task lineup.
- **Close Outcomes:**
  - Task 3 is marked with `*3` (Parked): in the closed session it becomes `[/]`, but is **not** carried forward to the continuation placeholder (dismissed from today's open ledger).
  - Work Log entry `"apollo agent"` is appended to Task 3's task note under `## Work Log`:
    ```markdown
    - *2026-11-04 09:21* — apollo agent
    ```
- **Ledger Mutation:**
  ```markdown
  - [x] (**0915-0925** [t:: 10m]) — FIX
    1 [/] Review logs ^log-task
    2 [/] Refactor types ^refactor-task
    3 [/] Investigate agent crash ^crash-task
  ```

#### Example 4: `x==1!2` (Clock: $0921$)
- **Token Analysis:** Prefix `x=`, empty `<E>`, `<X> = 1!2`.
- **Target Selection:** First open untimed placeholder `- [ ] ()` in the ledger.
- **Duration:** Default 5 blocks ($25\text{m}$) $\implies [0900, 0925)$.
- **Close Outcomes:**
  - Task 1 is in progress (`1`): marked `[/]` and carried forward to next placeholder.
  - Task 2 is completed (`!2`): marked `[x]` in daily note, completed in its home note with `[completion:: 2026-11-04]`, and unblocks any downstream dependent tasks.

#### Example 5: `x=3!` with Preexisting Past Pomodoro $0855\text{--}0920$ (Clock: $0921$)
- **Token Analysis:** `<E> = 3`, `<X>` is absent, Steal modifier `!` is present.
- **Computed New Range:** 3 blocks ($15\text{m}$) ending at anchor $0925 \implies [0910, 0925)$.
- **Overlap Detection:** Collides with existing session `0855-0920` on interval $[0910, 0920)$ ($10\text{ minutes}$ overlap).
- **Steal Execution:**
  - Because `!` is present, error is downgraded to a structured warning.
  - Preexisting session's end time is truncated from $0920$ to $0910$.
  - Preexisting session's duration is updated from $25\text{m}$ to $15\text{m}$:
    `(**0855-0910** [t:: 15m])`
  - New session is written with range `(**0910-0925** [t:: 15m])`.
  - Ledger result:
    ```markdown
    - [x] (**0855-0910** [t:: 15m]) — WORK
    - [x] (**0910-0925** [t:: 15m]) — WORK
    ```

---

## 4. Architectural & Algorithmic Implementation

### 4.1 Chronological Ledger Splicing

When a new past Pomodoro is closed, where should it be inserted in the daily note?

```
Daily Note Structure:
## Pomodoros
- [x] (**0800-0825** [t:: 25m]) — PLAN    <-- Earlier Completed
- [x] (**0830-0855** [t:: 25m]) — CODE    <-- Earlier Completed
[INSERT NEW PAST POMODORO HERE IN CHRONOLOGICAL ORDER]
- [ ] (**0925-0950** [t:: 25m]) — REVIEW  <-- Running Session (if any)
- [ ] () — BUGS                           <-- Planned Future Session
```

Bob preserves ledger chronological order for completed entries. The insertion algorithm:
1. Parse start minutes for all completed entries in `## Pomodoros`.
2. Locate the partition point: the latest completed entry whose `start_minutes <= new_start_minutes`.
3. Splice the new completed block (headline plus carried/worked child lines) directly after that entry's block.
4. If an existing entry was truncated via `!`, rewrite its headline in place.

---

### 4.2 The Time-Stealing State Machine

```
                   [ Compute Target Interval [s_N, e_N) ]
                                     |
                                     v
                       [ Scan Ledger for Overlaps ]
                                     |
                     +---------------+---------------+
                     |                               |
              No Overlap Found                Overlap Found
                     |                               |
             +-------+-------+               +-------+-------+
             |               |               |               |
         Has '!'?        No '!'?         Has '!'?        No '!'?
             |               |               |               |
             v               v               v               v
         [ ERROR ]       [ OK ]         [ Validate ]      [ ERROR ]
       Unneeded '!'    Write Session    Steal Policy    Ledger Overlap
                                             |
                                    +--------+--------+
                                    |                 |
                              Valid Steal       Invalid Steal
                             (Tail Trunc)      (Enclosed / GCal)
                                    |                 |
                                    v                 v
                                 [ OK ]           [ ERROR ]
                             Update Old +      Forbidden Steal
                              Write New
```

---

## 5. Implementation Blueprint in `bob-cli`

To implement this feature reliably across `bob-cli` and Bob Mac Capture, modifications span five core subsystems:

```
┌────────────────────────────────────────────────────────┐
│ 1. Token Lexing & Classification                       │
│    src/native/capture_language/tokens.rs               │
│    src/native/capture_language/item.rs                 │
│    src/native/capture_language/close_selection.rs      │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────v─────────────────────────────┐
│ 2. Draft Splitting & Chaining                          │
│    src/native/capture_language/draft.rs                │
│    src/native/capture_language/close_log.rs            │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────v─────────────────────────────┐
│ 3. AST & Data Structures                               │
│    src/native/capture_language/model.rs                │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────v─────────────────────────────┐
│ 4. Execution Engine & Ledger Planning                  │
│    src/native/capture/past_pomodoro.rs (NEW)           │
│    src/native/capture/pomodoro_start.rs                │
│    src/native/capture/pomodoro_close.rs                │
└──────────────────────────┬─────────────────────────────┘
                           │
┌──────────────────────────v─────────────────────────────┐
│ 5. CLI Presentation & JSON Reporting                   │
│    src/native/capture/cli.rs                           │
│    src/native/capture_parse.rs                         │
└────────────────────────────────────────────────────────┘
```

### 5.1 Step-by-Step Code Modifications

#### Step 1: Lexing in `capture_language/tokens.rs` and `item.rs`
- In `src/native/capture_language/item.rs`:
  Add `EqualsToken::PastPomodoro` to `session_equals_token`:
  ```rust
  if let Some(after_x_eq) = text.strip_prefix("x=") {
      let (start_spec, close_spec, steal) = lex_past_pomodoro_parts(after_x_eq);
      return Some(EqualsToken::PastPomodoro {
          start_spec,
          close_spec,
          steal,
          len: text.len(),
      });
  }
  ```
- Update `is_session_chain_token`:
  Ensure `EqualsToken::PastPomodoro` returns `true`, allowing `x=` tokens to participate in session operator chains (`x=build@2 x=fix@3`).

#### Step 2: Data Structures in `capture_language/model.rs`
- Define `PastPomodoroSpec`:
  ```rust
  #[derive(Debug, Clone, PartialEq, Eq, Serialize)]
  pub(crate) struct PastPomodoroSpec {
      pub(crate) raw: String,
      pub(crate) pomodoro_name: Option<String>,
      pub(crate) pomodoro_name_is_literal: bool,
      pub(crate) duration_units: u64,
      pub(crate) drop: Vec<u32>,
      pub(crate) close: Option<PomodoroCloseSpec>,
      pub(crate) steal_overlap: bool,
  }
  ```
- Add variant to `CaptureKind`:
  ```rust
  pub(crate) enum CaptureKind {
      // ... existing variants ...
      PastPomodoro(PastPomodoroSpec),
  }
  ```

#### Step 3: Backward Chaining in `capture/plan.rs`
- In `plan_capture_items`:
  When consecutive `PastPomodoro` items originate from the same line, collect them into a chain slice.
  Compute anchor $A = \text{start\_block\_minute}(\text{now}, \text{zero\_offset})$.
  Iterate in reverse: assign end times and start times backwards.

#### Step 4: Dedicated Execution Engine in `src/native/capture/past_pomodoro.rs`
- Implement `plan_past_pomodoro_item`:
  1. Scan daily note via `capture_pomodoros::scan`.
  2. Perform overlap checks using interval intersection arithmetic.
  3. If overlap exists:
     - Check `steal_overlap`. If false $\implies$ fail with `past_pomodoro_overlap`.
     - Verify overlap is a valid tail truncation on an eligible non-MEET session.
     - Calculate truncated end time and duration for the old session.
  4. If no overlap exists and `steal_overlap == true`:
     - Fail with `past_pomodoro_unneeded_steal`.
  5. Format the closed Pomodoro headline `- [x] (**HHMM-HHMM** [t:: Nm]) — NAME`.
  6. Execute task close actions via `capture_pomodoro_close::plan_pomodoro_close_outcome`.
  7. Splice into ledger in chronological order.

---

## 6. Verification & Test Plan

To maintain Bob's standard of comprehensive test coverage, the following automated test suites must be developed:

### 6.1 Unit Tests (`src/native/capture_language/tests/`)
1. **Grammar & Lexer Matrix:**
   - Single token parsing: `x=`, `x=3`, `x=3!`, `x=build`, `x=build@2`, `x=build@2!`.
   - Dual equals parsing: `x==1!2`, `x==1!2!`, `x=2#fix=*3`.
   - Ambiguity disambiguation: `x=build=!`, `x=build=!!`.
   - Rejection of negative offsets: `x=3-2` fails with precise teaching error.
2. **Chain Splitting:**
   - Multi-token lines: `x=build@2 x=fix@3` split into two items with shared parent line spans.
   - Inline Work Log: `x=2#fix=*3 apollo agent` correctly preserves `apollo agent` as close log.

### 6.2 Integration Tests (`tests/capture/past_pomodoro.rs`)
1. **Time Math Verification:**
   - Fixed `BOB_NOW=2026-10-20 09:21:00`.
   - Single item `x=build` produces $0900\text{--}0925$.
   - Chained items `x=build@2 x=fix@3` produce $0900\text{--}0910$ and $0910\text{--}0925$.
2. **Overlap Detection & Stealing:**
   - Existing session $0855\text{--}0920$:
     - `x=3` fails with overlap error naming $0855\text{--}0920$ ($10\text{m}$ conflict).
     - `x=3!` updates $0855\text{--}0920$ to $0855\text{--}0910$ ($15\text{m}$) and writes $0910\text{--}0925$.
     - `x=3!` when no session exists fails with `unneeded '!' modifier`.
3. **Task Outcome Verification:**
   - `x==1!2`: works task 1, completes task 2 in its home note with `[completion:: YYYY-MM-DD]`.
   - `x=fix@2=*3 apollo agent`: parks task 3 (dismisses from daily note) and appends to work log.

---

## 7. Recommended Solution & Synthesis

### Summary of Recommendations
1. **Adopt `x=<E>=<X>[!]` exactly as specified**, utilizing the deterministic two-equals grammar rule to disambiguate start `<E>` from close `<X>`.
2. **Enforce the strict ban on `-<N>`** in `<E>`, returning an educational diagnostic explaining that `x=` is past-anchored by default.
3. **Implement Right-to-Left Backwards Propagation** for chained same-line `x=` tokens, anchoring the rightmost token to $\lceil \text{now} / 5\text{m} \rceil$.
4. **Constrain time stealing (`!`) strictly to Tail Truncation** of the immediate predecessor, forbidding mid-session splitting, complete session deletion, and calendar `MEET` mutation.
5. **Enforce the fail-fast error when `!` is unneeded**, preserving user confidence and ledger accuracy.

This design delivers an intuitive, reliable, and aesthetically beautiful solution that seamlessly integrates with Bob's capture ecosystem.

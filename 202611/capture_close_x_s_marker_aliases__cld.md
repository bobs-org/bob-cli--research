# `x` → `!` and `s` → `*`: Shift-free close-outcome aliases for Bob Mac Capture

*Researcher: cld · 2026-11-08 · Scope: bob-cli (`capture-rewrite`) and bob-mac-capture (editor rewrite lane)*

## TL;DR

- **Yes, build it, with adjustments.** Closing a Pomodoro is the capture Bryan types most:
  476 closed ledger entries in the last 40 daily notes, an average of 11.9 a day and up
  to 23. `!` and `*` are the two outcome markers that need Shift. Every other Shift
  sigil on the hot path already has a Shift-free alias (`.`→`^`, `;`→`:`, `,`→`+`,
  `=`→`~`, `\`/`/`→`#`, past-segment `-`→`~`), so `x`→`!` and `s`→`*` complete an
  existing pattern. They don't add a new one.
- **Almost all the new positions are collision-free.** Inside a close selection
  (`x1x`, `x!s`, `x=1=s`, `x==x`, …), a glued letter is a grammar error today, so the
  alias can only turn an error into valid syntax. The only real collisions are:
  1. **whole-item `xx` / `xs`**, which bob parses today as prose tasks (`xxhash`,
     `xss audit`, `xsel`). This collision is the feature itself. Bryan's vault has zero
     task lines that start with `xx` or `xs`, and capital `X` is already the documented
     escape.
  2. **link-suffix `@r:id=xx` / `=xs`**, which bob parses today as a named start
     ("XX" / "XS"). The vault has zero Pomodoro names that start with X.
- **Implement it the way the existing aliases work.** Bob's `capture-rewrite` gets a new
  case in the existing `expand_sigil_alias` rule, and the Mac editor forwards `x`/`s`
  key-downs to that rewrite lane. Don't use an app-local Swift rule or a grammar-level
  alias. The thin-client decision forbids the first, and the relation-`=` decision
  rejected the second.
- **The real engineering risk is timing, not grammar.** Two cases need handling:
  - `xx⏎` typed faster than bob answers would submit the prose task "xx".
  - `xx1` typed fast would drop the alias and leave a valid prose draft.

  The Mac half therefore needs two pieces: the fast-Return deferral that already exists
  for `x=2-`, and a small "rebase onto appended typing" so a reply still applies after
  the user keeps typing past the caret.
- **Requirement adjustments (A1–A10 below).** The main ones:
  - Read "instead of the second `=`" as "after the second `=`", which is what the
    example shows.
  - Extend the alias to every marker position inside a close selection.
  - Allow it only where the marker is a *viable prefix*, so lowercase only and no
    second `!`/`*`.
  - Keep it editor-only.

---

## 1. What exists today

### 1.1 The alias inventory

Every current alias runs through one path. The Mac controller records an intent for a
fixed set of keys. After AppKit inserts the key, the model calls
`bob capture-rewrite --cursor BYTE --format json -- <draft>`. If bob answers
`changed: true` and the visible draft still equals the request draft, the app applies
the edit natively with `breakUndoCoalescing()` + `insertText`. That makes Undo restore
the literal key in one step.

| Key | Becomes | Where (bob decides) | Rule code |
| --- | --- | --- | --- |
| `.` | `^` | after `@route` where the Block ID picker opens; `- .` move bullet | `expand_sigil_alias` |
| `;` | `:` | after `@route`; whole-item Task Link; `- ;` move bullet | `expand_sigil_alias` |
| `,` | `+` / ` +` | wherever the Parent Task picker opens | `expand_sigil_alias` |
| `=` | `~` | after a space where Links To opens; `~=` → `~~` | `expand_sigil_alias` |
| `\` `/` | `#` | wherever a `#` menu opens, never at line start | `expand_sigil_alias` |
| `-` | `~` | inside an `x=` past token where the segment picker opens | `expand_sigil_alias` |
| `^ : +` | switch separator | after a complete `@route:id` etc. | `switch_block_id_separator` |
| `\|` | glue to relation | after `~note:id ` | `attach_relation_label` |
| `~ =` | flip direction | glued to a complete relation | `toggle_relation_direction` |
| digit | `,digit` | after a digit inside a close list (**app-local**, from `capture-parse` spans + agenda count) | n/a (Mac `CaptureCloseTaskCommaAssist`) |

Evidence:
- the key filter: `bob-mac-capture/Sources/BobMacCapture/CapturePanelController.swift`
  (`noteSeparatorToggleIntentIfEligible`, ~L1116–1196)
- the apply guard: `CapturePanelModel.swift` `applyCaptureRewrite` (~L16301)
- the bob rules: `bob-cli/src/native/capture_language/rewrite.rs` (`rewrite_draft`,
  `expand_sigil_alias`, `expand_past_segment_dash_alias`)
- the docs: `bob capture-rewrite --help`, `docs/capture.md` "Sigil alias",
  `bob-mac-capture/docs/capture-panel.md` and `docs/keyboard.md`

Two precedents matter most here:

1. **`x=2-` → `x=2~`.** This is the only existing alias that fires *inside a
   Pomodoro-command token*, and the only one whose literal and aliased forms submit
   different commands. Because of that it has special Mac plumbing:
   `deferSubmitForPastSegmentDash`. A fast Return after the `-` waits for bob's answer
   and the re-analysis before it submits.
2. **The close-list comma assist** is the one *app-local* assist. It exists because it
   needs the agenda's Task Link count, which `capture-rewrite` (lexical and vault-free)
   can't know. Even so, its doc comment says "It never recognizes close syntax itself:
   it only filters bob's `capture-parse` close-list spans".

### 1.2 Measured latency

On apollo, `bob capture-rewrite` costs a median of 5.8 ms (p90 8.2 ms) per spawn and
`capture-parse` a median of 6.8 ms. That's 20 runs each, measured for this report. The
thin-client decision records about 5 ms on athena. Nothing has been measured on the Mac.
The app already wraps each call in `CaptureSignpost.measure("rewrite")`, so a Mac number
is one Instruments session away.

## 2. What the grammar says about `x` and `s` today

I ran each draft through the installed `bob capture-parse -f json` (bob 0.4.0, HEAD
`51d572d5`):

| Draft | Today | Alias result | Collision? |
| --- | --- | --- | --- |
| `xx` | **prose task** | `x!` (complete remaining) | **yes: prose** |
| `xs` | **prose task** | `x*` (park remaining) | **yes: prose** |
| `xxhash`, `xss audit` | prose task | `x!hash` / `x*s audit` would be errors | **yes, prose words** (see §3.2) |
| `x1x`, `x1s`, `x0s` | `invalid_pomodoro_close` | `x1!`, `x1*`, `x0*` | no |
| `x!x`, `x*s`, `x!!`, `x**` | `invalid_pomodoro_close` | must stay literal (one `!`/`*` list) | n/a |
| `x*!` | error: *competing park-all and complete-all groups* | `x*!2` is valid, so `xsx` → `x*!` must be allowed | n/a (prefix nuance) |
| `x1,` + `*` | `x1,*` error "expected a task number after `,`" | stay literal | n/a |
| `x@1*`, `x~1*` | valid | `x@1s` → `x@1*` | no |
| `x=1=s`, `x=1=x`, `x==s` | `invalid_pomodoro_past` | `x=1=*`, `x=1=!`, `x==*` | no |
| `x=1=2*`, `x==!2` | valid | `x=1=2s` → `x=1=2*` | no |
| `x=1s` | **valid**: past session named "S" | must stay literal | **yes: name** |
| `x=fixx` | **valid**: name "FIXX" | must stay literal | **yes: name** |
| `x=1x` | teaching error "write `x=1#x`" | stay literal | n/a |
| `+2 xx` | `invalid_pomodoro_adjustment` | `+2 x!` (chain) | no |
| `@work:outline=xx`, `=xs` | **valid: named start "XX" / "XS"** | `=x!` / `=x*` (link then close) | **yes: name** |
| `=xs` (whole item) | valid named start | stay literal (`=x` whole-item is a retired close) | **yes** |
| `x wired s`, `x!1 notes` | valid Work Log text | stay literal (after whitespace) | n/a |
| `X`, `Xs` | prose | stay literal | n/a |

Close sub-spans start exactly at the marker byte in every case I probed:
- `x!` → `pomodoro_close_complete` 1..2
- `x*!2` → `pomodoro_close_park` 1..2, then `pomodoro_close_complete` 2..4
- `x=1=*` → `pomodoro_close_park` 4..5
- `@work:outline=x!` → `pomodoro_close_complete` 15..16
- `+2 x!` → `pomodoro_close_complete` 4..5

That gives bob a clean eligibility test that reuses the span contract the Mac already
paints (green and orange).

`close_selection.rs::lex_close_selection` enforces at most one `!`, `*`, and `~` group
per close. A trailing `,` is `Incomplete`, and two empty wildcards compete. No completion
context exists for close lists. So unlike `.`/`;`/`,`/`=`, the new alias can't be gated
by `completion_field_at`. It needs a close-lexer gate. That is the only genuinely new
mechanism in bob.

## 3. Critique: is this a good idea?

### 3.1 For

- **Frequency × friction.** About 12 closes a day, and the outcomes that matter most are
  complete (`!`) and park (`*`). Both sit behind Shift. Shift-free aliases are a
  deliberate and accepted direction in this codebase (six already ship).
- **Strong mnemonics.**
  - `x` → `!`: in Markdown `[x]` *means* done, and `xx` reads as "close, done".
  - `s` → `*`: `s` reads as "star", and as "stash" / "shelve" for parking.
- **Inside a selection there's no ambiguity.** No letter is legal in
  `x[<N>][*<P>][!<M>][~<K>][@<N>]` or after `x=E=`, so the alias can't change the
  meaning of a valid draft there.
- **It composes with the comma assist.** For example, `x1` + `2` → `x1,2`, then `s`
  → `x1,2*`, then `3` → `x1,2*3`. The comma assist only fires after a digit and these
  aliases only fire on letters, so they never compete.

### 3.2 Against, and how much each concern matters

1. **It overrides documented prose behavior in the editor.** `docs/capture.md` (L337,
   L4682) and `capture-syntax.md` (L1006) say "`xx`, `xa`, `x.`, `x-ray` … never
   close". In the editor, `xx` would now close. This is acceptable for two reasons:
   - The aliases are editor-only, so `bob capture 'xx'` keeps working.
   - The relation-`=` decision already established that editor typing assists may
     differ from the grammar, provided `capture`/`capture-parse` stay literal.

   The docs must be updated to scope the claim (A9).
2. **Lowercase x-words at the start of an item get mangled.** Examples: `xxx`,
   `xxhash`, `xs` ("extra small"), `xsel`, `xset`, `xss`, `xslt`, `xstate`, `xsmall`.
   All of these appear in the vault (for example `xs` 142×, `xsmall` 30×, `xstate`
   11×), but only inside notes or reference text. **Zero task lines start with
   `xx`/`xs`**, and none would be typed into Capture as the first word of a task. The
   cost when it does happen is one Cmd-Z (or typing `X`). The editor makes it obvious:
   the close spans recolor and the preview says "would close".
3. **Named-start collisions on link suffixes.** `@r:id=xx…` is a named start today.
   **Zero** of the roughly 700 recorded Pomodoro names start with X; the most common are
   PLAN, BUILD, READ, FIX, and SASE. The `=#xs…` exact-name form and uppercase `=XS…`
   stay available.
4. **Same-finger bigram.** On QWERTY, `x`→`s` is the left ring finger moving
   bottom→home. It's slightly slower than alternating hands, but far faster than
   Shift-8. `p` ("park/pending") would be an alternating-hand alternative, but it loses
   the visual `s`≈`*` link and collides with the same class of prose (`xp`, `xpath`,
   `xprop`). **Keep `s`.**
5. **Timing races.** These are the main real risk, covered in §5. Today a dropped alias
   from `.`/`;`/`,`/`=` usually leaves harmless literal punctuation. A dropped `x`/`s`
   alias at the start of an item leaves a *valid prose capture* (`xx`, `xx1`), and
   Return would file it as a junk inbox task.

### 3.3 Would I take a different approach?

I considered four alternatives and would not switch to any of them:

| Option | Summary | Verdict |
| --- | --- | --- |
| **A. bob `capture-rewrite` case + Mac forwards `x`/`s`** | Same lane as `.`/`;`/`,`/`-`/`=`; bob decides; Undo restores literal | **Recommended** |
| B. Mac-local assist from `capture-parse` spans (like the comma assist) | Synchronous, but Swift would decide "is `!` already used / is this viable", which is close-grammar knowledge in the app | Rejected: thin-client decision (`decisions:mac-capture-is-a-thin-client`); the comma assist was only allowed because it needs agenda data bob's lexical rewrite can't see |
| C. bob publishes per-caret "key alias hints" in `capture-parse` | App decides synchronously from bob's data | Rejected: a new protocol surface with the *same* staleness race (the parse for the pre-key draft must land first); no gain over A |
| D. Grammar-level alias (`bob capture 'xx'` ≡ `x!`, `x1s2` ≡ `x1*2`) | No races; works from the CLI and Raycast too | Rejected: the relation-`=` decision explicitly rejected "syntax reaching the grammar"; `bob capture 'xs'` (prose today) would silently start closing Pomodoros; every diagnostic, doc, and span gets a second spelling forever |

A richer alternative is a keyboard close *card*: after `x`, the lineup shows and
per-row keys pick the outcome. That would remove digits entirely, but it's a much larger
UX investment. The text alias is the right increment, and it doesn't preclude the card
later.

## 4. Requirement adjustments (flagged)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | **Read "used instead of the second `=`" as "typed after the second `=`"**, per the example `x=1=s` → `x=1=*`. | The literal reading (`x=1x` → `x=1=!`) collides with valid names (`x=fixx` = FIXX, `x=1s` = 1 block named S) and with the existing teaching error for `x=1x`. |
| **A2** | **Widen the scope from "right after `x` / the second `=`" to every marker position in the close selection**: `x1x2`→`x1!2`, `x1,2s3`→`x1,2*3`, `x=1=2s3`→`x=1=2*3`, `x@1s`→`x@1*`. Include every live close carrier: whole item, chain (`+2 xx`), link suffix (`@r:id=xs`, `^r:id=x1x`, `Fix it @r:id=xx`). | Letters are errors in all of these positions, so the wider scope has zero collision and one simple mental model: "inside a close, `x` types `!` and `s` types `*`". |
| **A3** | **The alias fires only where the marker is a viable prefix**: no second `!`/`*` group (`x!x` stays literal), not after `,`, not after the Work Log's whitespace. `xsx` → `x*!` *is* allowed (competing wildcards are resolved by the next digit, as in `x*!2`). | "Valid now" is too strict and "anything" is too loose. Viable-prefix matches what a careful typist could still finish. |
| **A4** | **Lowercase only; the key must be glued and must end the token**, as every other alias requires. Capital `X` never aliases and stays the prose escape. Never alias in the `E` part of `x=` (names, counts, repair `!`), in whole-item `=x…` (retired close / named start), in templates, wikilinks, picker filters, or modal fields. | Consistent with the existing alias contract; keeps `x=fixx`, `x=1s`, `=xs` working. |
| **A5** | **Editor-only.** `bob capture` / `capture-parse` keep literal text (`'xx'` stays prose); pasted text never aliases. | Same contract as every other alias and `decisions:relation-equals-alias-and-flips`. |
| **A6** | **Alias on link suffixes too** (`@r:id=xx` → `=x!`), even though `=xx` is a named start today. **Bryan decision.** | Following `=x`'s meaning in each context is the consistent rule (whole-item `=x` is retired, so no alias there). No X-named Pomodoros exist; `=#xs…` / `=XS…` remain. If Bryan prefers "never steal a valid structured parse", drop link suffixes from A2. |
| **A7** | **Typing speed must not change the outcome**: a fast Return after the key waits for bob, and typing after the key must not silently discard bob's yes. | `xx⏎` / `xx1⏎` would otherwise file prose tasks (§5). |
| **A8** | **Undo restores the literal key in one step; Backspace stays native.** | Matches every rewrite-lane alias. |
| **A9** | **Update the "`xx` never closes" docs** to say it's grammar-true but the Mac editor types `x!`, with `X…` or Undo as the escape. | Otherwise the docs contradict the panel. |
| **A10** | **The Mac forwards `x`/`s` only behind a lexical superset pre-filter** (§6.2), not on every keystroke. | `s` is about 6% of English letters; there's no reason to spawn bob and gate completion on every one. |

Optional, **not** recommended for v1:
- An `s`→`*` alias in the `x=E` repair position.
- A `d`→`~` drop alias. `xd…` collides with `xdg-open`.
- A `-`→`~` drop alias after a digit (`x1-2` → `x1~2`). It's collision-free and matches
  the past-segment dash, so it's worth a later look.

## 5. Timing hazards (the part that needs care)

The current apply guard is `plainDraft == draft` (`applyCaptureRewrite`). Any keystroke
that lands before bob answers cancels the rewrite or discards its reply, and the literal
key stays.

| Sequence (typed faster than bob answers) | Today's plumbing would give | Severity | Fix |
| --- | --- | --- | --- |
| `xx⏎` / `xs⏎` | Return submits prose **"xx"** to the inbox; Pomodoro not closed | **High** (wrong vault write) | Generalize `deferSubmitForPastSegmentDash` to these keys: Return waits for bob, then the re-analysis, then submits |
| `xx1⏎`, `xs2⏎` | alias dropped → `xx1` is **valid prose** → filed | **High** | **Rebase**: apply bob's single-byte swap if the live bytes before the request cursor are unchanged (the user only typed after the caret). Caret offsets don't move because it's a 1-byte → 1-byte swap. |
| `x1s2⏎` | alias dropped → `x1s2` is a close *error* → submit refused | Low (safe failure) | Rebase covers it |
| `xsx2`: two alias keys inside one bob round-trip | second request still sees literal `s` → `x*x2` error | Low (safe failure; needs about 10 ms key-to-key) | Measure first with the `rewrite` signpost; only if needed, add a catch-up rule (bob aliases every still-literal `x`/`s` in the close prefix left-to-right while the prefix stays viable). Not v1. |

The rebase is sound because bob decides at keystroke time on the request draft, where
the key ends the token. Applying that verdict after later typing gives exactly what slow
typing would have given. Fast `xxhash` becomes `x!hash`, just as slow typing would. So
behavior stops depending on speed, which A7 asks for. Cancel the pending rebase on any
edit before the caret, caret jump, paste, Undo, or dismissal. These are the same
invalidations the hash-alias probe uses.

## 6. Recommended solution

### 6.1 bob-cli (lands first): one new case in `expand_sigil_alias`

**Rule** (rule code stays `expand_sigil_alias`; summaries `Typed ! for x` / `Typed * for s`):

1. **Trigger.** The byte before `--cursor` is a lowercase `x` or `s`, glued to the
   previous byte, and the token ends at the cursor. With no `--cursor`, the rule is
   skipped, like every other alias.
2. **Context.** The byte lies in the *selection* part of a live close token:
   - after the `x` of a whole-item or chain close;
   - after the `=x` of a link or task suffix;
   - after the second `=` of an `x=E=` past token, found via the item parser the way
     `expand_past_segment_dash_alias` finds `x=` tokens. That way quoted names with
     spaces (`x=#"deep work"=s`) work.
3. **Eligibility.** Swap the key for its marker. Re-parse the item. Require a
   `pomodoro_close_complete` span (for `!`) or a `pomodoro_close_park` span (for `*`)
   that **starts at the swapped byte**, with no diagnostic on that token. If the only
   diagnostic is the competing-wildcards error, re-test with one unused task number
   appended (`x*!` → `x*!1`). A dedicated predicate in `close_selection.rs` is
   equivalent and cheaper, e.g. `close_marker_may_follow(prefix, marker)`.
4. **Edit.** One 1-byte replacement; the cursor stays just past it. Feeding the output
   back is a no-op.

**Tests:**
- unit tests in `rewrite.rs`
- `tests/cli/capture/rewrite.rs`, covering every row of the §2 table: the aliasing rows
  plus the stay-literal rows `X`, `x!x`, `x1,x`, `x=fixx`, `x=1s`, `x=1x`, whole-item
  `=xs`, `Plan xx`, `x wired s`, templates, and wikilinks.

**Docs:**
- `capture-rewrite --help` sigil-alias paragraph and examples
- `docs/capture.md` "Sigil alias" and the grammar-at-a-glance prose rows (A9)
- `docs/reference/capture-syntax.md`: overloaded-markers rows for `!` and `*`, plus the
  `x` / `x!` / `x*` sections

This is a non-breaking `feat(capture):` that rides the daily release train.

### 6.2 bob-mac-capture (lands second)

1. **Forwarding.** In `noteSeparatorToggleIntentIfEligible`, add `x` and `s` under the
   existing guards: no ⌘/⌃/⌥, no marked text, collapsed selection, main editor only,
   modal fields excluded. ⌘X still cuts, and picker filters keep letters as query text.
   **Pre-filter:** forward only when the current line before the caret contains a
   lowercase `x` at a token start or right after `=` (regex `(^|[ \t=])x`).
   - This is a strict *superset* of bob's eligible positions. Every live close carrier
     has its `x` there on the same line.
   - It only decides when *not to ask*, which the `=`, blank-`/`, and `x=`-dash
     pre-filters already do.
   - Pin the superset property with a shared fixture test.
2. **Fast Return.** Generalize `deferSubmitForPastSegmentDash` (and the `-`/`~` echo
   check in `applyCaptureRewrite`) into a "meaning-changing alias" flag that covers
   `x`→`!` and `s`→`*`.
3. **Rebase.** For `x`/`s` alias replies, replace the strict `plainDraft == draft`
   guard with a check that the live draft has an unchanged prefix up to the request
   cursor and still holds the literal key at `cursor − 1`. Don't cancel the in-flight
   request on pure appends after the caret. Apply through the existing
   `applyNativeSingleEditRewrite`, so Undo restores the literal key and leaves later
   typing in place.
4. **Docs and tests.**
   - Docs: `docs/keyboard.md` gets `x` and `s` rows; `docs/capture-panel.md` gets the
     alias paragraph and the `xx` note.
   - Tests:
     - controller tests for forwarding and the pre-filter;
     - model tests for Return deferral and rebase, including the pure-append,
       edit-before-caret, and caret-move cancellation cases;
     - fake-bob fixtures.
   - Per AGENTS.md: compile on a Swift host and watch the exact-SHA macOS CI run.

**Compatibility:**
- An old app with the new bob never forwards `x`/`s`, so there's no change.
- The new app with an old bob gets `changed: false`, so the key stays literal. That's
  today's behavior, and no capability gate is needed.

### 6.3 Governance

Because this redefines what `xx` does in the editor and introduces letters as close
aliases, record it as a new decision once accepted. Working title: *"Close Markers Have
Letter Aliases In The Editor"*. Applies to bob-cli and Bob Mac Capture. It would list:

- **Claims:** A2–A6.
- **Rejected alternatives:** B, C, D, the literal "instead of `=`" reading, and `p`
  for park.
- **Reopens when:** a valid prose or name parse is found that users hit, or Mac
  rewrite latency makes the fast-sequence race real.

### 6.4 Open questions for Bryan

1. **A6:** should link suffixes alias (`@r:id=xx` → `=x!`), or keep `=xx…` as a named
   start? I recommend aliasing.
2. Is Cmd-Z plus capital `X` enough as the prose escape, or do you want a teaching hint
   when the draft is exactly `x`? (Something like the "`==` types `=`" footer, e.g.
   "x → ! · s → *". It's optional, and I'd skip it in v1.)

## Evidence index

- **bob-cli:**
  - `src/native/capture_language/rewrite.rs`: `rewrite_draft`, `expand_sigil_alias`,
    `expand_past_segment_dash_alias`
  - `src/native/capture_language/close_selection.rs`: `lex_close_selection`,
    `link_close_after_x`
  - `src/native/capture_rewrite.rs`: help text
  - `docs/capture.md` L325–340, L4512–4660, L4941–5060, L8846–8880
  - `docs/reference/capture-syntax.md` §Token index, §Overloaded markers, §Closing
- **bob-mac-capture:**
  - `CapturePanelController.swift`: `noteSeparatorToggleIntentIfEligible`,
    `applySeparatorToggleInEditableTextView`
  - `CapturePanelModel.swift`: `editorTextDidChange`, `startCaptureRewrite`,
    `applyCaptureRewrite`, `waitForRewriteBeforeSubmit`
  - `CaptureCloseTaskCommaAssist.swift`; `CaptureEqualsGesture.swift`
  - `docs/capture-panel.md` L89–117, L171–241; `docs/keyboard.md` L95–103
  - commit `16c79f6`: introduced the past-segment Return deferral
- **Decisions:** `decisions:mac-capture-is-a-thin-client`,
  `decisions:relation-equals-alias-and-flips`,
  `decisions:capture-sigils-say-where-what-how`.
- **Measurements (this session, apollo):**
  - all `capture-parse` probes in §2;
  - `capture-rewrite` median 5.8 ms, `capture-parse` median 6.8 ms;
  - vault scan: 0 task lines starting with `xx`/`xs`, 0 Pomodoro names starting with X,
    476 closed entries over 40 days.

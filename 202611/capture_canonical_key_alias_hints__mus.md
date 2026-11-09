# Teaching capture aliases when the canonical key is typed (`__mus`)

Swarm researcher report (mus). Question: should bob-mac-capture show a little
hint when the user types a canonical character they could have typed as a
capture alias (e.g. types `@`, gets taught `.`)? Lead the design so it is
intuitive, reliable, and beautiful. Ends with a recommended solution.

## 1. What the aliases actually are (ground truth)

The alias inventory below is verified, not recalled. Alias behavior lives in
exactly one place — `bob capture-rewrite --cursor` with rule
`expand_sigil_alias` — per the thin-client decision
(`decisions:mac-capture-is-a-thin-client`): bob decides every alias, the app
renders. I confirmed each of these on bob 0.5.0 in this workspace:

- `@errands.` → `@errands^`, summary `Typed ^ for .` (dot-for-caret after
  `@route`).
- `Buy milk .` → `Buy milk @` (cursor 10), summary `Typed @ for .`
  (spaced dot-for-route). Note the cursor matters: cursor 9 (the space)
  returns `changed: false`.
- `@cash,` → `@cash+`, summary `Typed + for ,` (comma-for-parent).
- `Fix it =` → `Fix it ~` (cursor 8), summary `Typed ~ for =` (equals-for-relation).
- `Buy milk /` → `Buy milk #`, summary `Typed # for /` (slash-for-hash).
- `xx` → `x!`, summary `Typed ! for x` (close-outcome letters).

The full glossary entry (`glossary:capture-alias`) adds: `;` → `:` after
`@route` and as a whole item (Task Link picker); `- .` / `- ;` → `- ^` /
`- :` Move picker in sealed project-note bullets; `\` → `#` with the same
gates as `/`; `-` → `~` inside `x=` past tokens (`x=2-` → `x=2~`);
`=` → `~~` flip after bare `~`; `s` → `*` alongside `x` → `!`.

Critically for this feature, every alias has **eligibility gates**: the
spaced `.` stays literal at line/bullet-body starts, glued to a word, inside
backticks or wikilinks, and where no route field exists; `/` stays literal
in `=/`, `[[folder/`, section and Pomodoro names; `,` stays literal in
prose; `x`/`s` stay literal after Work Log text and in prose. Any hint must
respect these gates or it will teach lies.

Also explicitly **not** aliases (glossary): the block-ID separator toggle
(`@route:id^`), the glued `~`/`=` direction flip, `|` label attach, and `@@`
absorption. Typing `^` after `@file:id` to switch separators must never
produce a "you could have typed `.`" hint — `.` does something different
there (or nothing). This is the sharpest false-positive edge in the whole
design.

## 2. Critique: is this a good idea?

**Yes, with the direction reversed from how it first sounds.** The request
frames it as "user types canonical, we teach alias." That is the right
trigger, but the naive version — a popup every time `@` is pressed — would
be a nag engine aimed at an expert user. Bryan types `@` dozens of times a
day; the ergonomic win of `.` (no Shift, home row) is real but small per
instance, and a hint shown on the 50th `@` teaches nothing while costing a
visual flicker and a VoiceOver announcement each time.

Three more specific critiques:

1. **The forward teaching already exists.** Every successful alias announces
   bob's summary (`Typed ^ for .`, `Typed @ for .`). Users who try aliases
   get confirmation. What is missing is only the reverse path: a user who
   never tries `.` never learns it exists. So the hint only needs to fire
   **until first alias use per alias family**, then retire — not forever.
2. **Most canonical presses already open a picker, and the picker footer is
   where the eyes are.** `@` opens route completion (verified: `context:
   "route"` with candidates for `Buy milk @`), `+`/`,`, `#`, `~`/`=`, `^`/`;`
   all open pickers. Teaching in the picker footer/detail strip reuses an
   established pattern (relation pickers already teach `== types = · ~ flips`
   live; task pickers teach follow-ups after first insert, tracked per
   source). A separate bubble duplicating that surface is a second teaching
   system to maintain.
3. **`!`/`*` closes have no picker, so they need a different surface.**
   The close-letter aliases (`x`→`!`, `s`→`*`) are the highest-frequency win
   (every Pomodoro close) and the only major case with no picker to host the
   lesson. Whatever we build must handle picker-backed hints and the
   picker-less close case separately.

**Adjustment I am making to the requirements:** do not build "a hint when
they type a character." Build **two mechanisms**: (a) one-line picker-footer
tips for the six picker-backed families, and (b) a once-per-family
status-line nudge for close outcomes (`!`/`*`). Both retire permanently
after first alias use. No popups, no badges, no modal anything.

## 3. Options considered

| Option | Reliability | Beauty | Verdict |
|---|---|---|---|
| App-local heuristic (typed `@` in plausible context → show hint) | Poor: re-implements grammar, violates thin-client rule, false-positives on separator toggles and wikilinks | Fine | Reject |
| Bob-driven eligibility per keystroke (ask `capture-rewrite` on hypothetical `.`-substituted draft) | Good but doubles subprocess traffic on every canonical key | Fine | Reject: wasteful |
| Bob adds `alias_hint` to `capture-complete` responses; app renders in picker footer | Best: zero new spawns, eligibility free (a completion context that exists implies the alias would have fired), additive JSON keeps old bob working | Best: reuses existing footer slot, zero layout shift | **Recommend (picker cases)** |
| Status-line nudge for `!`/`*` closes, once per family | Good: close context already parsed (`pomodoro_close` spans); no new spawn needed, just match typed `!`/`*` inside a close slot | Good: existing announcement channel with VoiceOver support | **Recommend (close case)** |
| Toast/bubble near caret | Same data as above | Worst: moves attention, risks editor shift, competes with agenda eye-line discipline | Reject |

Why the `capture-complete` vehicle works: when the user types `@` and route
completion opens, bob has already proven a route field exists at the caret —
which is nearly the entire eligibility gate for the spaced-`.` alias. The
app does not need a second opinion; it needs bob to confirm the alias would
have applied, which bob can compute from the same grammar state that
produced the completion. An additive `alias_hint: {typed: "@", try: ".",
copy: ". types @ here"}` field on the completion response (or on the picker
descriptor) costs nothing per keystroke and degrades gracefully: older bob
omits it, app shows nothing — the same `decodeIfPresent` pattern the
protocol doc mandates.

## 4. Recommended solution

### 4a. Picker-footer tips (bob-cli + app, six families)

bob-cli: add additive `alias_hint` to `capture-complete` JSON responses for
these contexts: `route` (`@` → teach `.`), block-ID after `@route` (`^`
→ `.`, `:` → `;`, whole-item `:` → `;`), parent-task (`+` → `,`),
`#` menus (→ `\ or /`; note both keys alias, teach `/` as primary since
`\` is also the Go To key on blank drafts), Links To (`~` → `=`).
Copy stays bob-authored so docs and app never drift; suggested copy shape:
`Tip: . types @ here` — keycap chips matching the existing footer style,
never a sentence.

App: render the hint as a trailing footer chip in the already-open picker
(`CapturePickerView` footer / `operatorContinuationHint` area), `secondary`
`caption2`, static text (never a button trait), included in the picker's
VoiceOver label only on open (not re-announced per keystroke). Fixed footer
slot so showing/hiding never resizes the panel (the task-picker budgets
already require "grows once on open, never resizes while typing"). When the
filter is non-empty, keep showing it — it costs no space and the lesson is
still true.

Retirement: per-family `UserDefaults` flag `aliasHintSeen.<family>`,
set when (a) the user types the alias and bob confirms `expand_sigil_alias`
(the forward summary is the signal — no new code), or (b) the user
dismisses via the existing footer pattern. A global Settings toggle
`Show alias hints` (on by default), mirroring the `Show similar tasks`
precedent. This is local learning state, not vault state: `UserDefaults`,
not a synced journal.

Out of scope for v1: the `x=`-segment `-` alias and `~`/`=` flip hints.
Both are low-frequency and the flip hint already exists in the relation
picker footer.

### 4b. Close-outcome nudge (app-local, `!`/`*` → `x`/`s`)

When the user commits a close containing a literally-typed `!` or `*` in a
close slot (the app already parses close slots for the comma helper and the
`x`/`s` hold-Return lane, so slot detection is existing machinery — not new
grammar), and the per-family flag is unset, set
`statusText = "Tip: x types ! · s types *"` with one `announceStatus` (the
same channel as the old-bob close-alias message). Clear on next keystroke or
after ~4 s, whichever comes first; never clobber an error. Retire after
first confirmed `x`/`s` alias use or first display + successful close,
whichever the implementer finds simpler — one display is enough for this
user.

Do not hold Return or add a spawn: unlike alias keys, canonical `!`/`*`
need no bob round-trip to be valid, so there is nothing to wait for.

### 4c. What not to build

- No hint for separator toggles, `|` attach, or `@@` — not aliases.
- No hint inside wikilinks, backtick spans, templates, or `#"…"` literals —
  bob never rewrites there.
- No counters, streaks, or "you've saved N keystrokes" — decoration that
  outlives its lesson.
- No per-note or vault-synced state.

### 4d. Contract and rollout notes

- bob-cli ships first (additive `alias_hint`, grammar bump only if the
  schema demands it), app decodes with `decodeIfPresent`; document the field
  in `docs/capture.md` (`capture-complete` section) and the mac `protocol.md`
  compatibility table, marking the `!`-family fallback row.
- Tests: golden `capture-complete` fixtures asserting `alias_hint`
  presence/absence per context (including the negative cases: `[[folder/`,
  `=/`, line-start `#`, glued `~` after label); app tests asserting
  footer-chip visibility per flag state and old-bob omission (mirror the
  existing `closeAliasProbe` test seams).
- macOS CI gate applies to the app half, as always.

## 5. One-line summary

Teach each alias exactly once, where the user is already looking (the open
picker's footer, or the status line for picker-less closes), with bob as the
sole authority on when the lesson is true.

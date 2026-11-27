# Type Leads: `#f` ⇥ → `#fix Fix ▌`

*Research report (cld) · 2026-11-27 · bob-cli, Bob Mac Capture, chezmoi*

**Question.** Should accepting certain task types from the capture panel's `#` menu at
the start of a capture also type the matching verb (`#f`, accept FIX → `#fix Fix `)?
What is the best way to build it, what should change in the request, and what would I
do differently?

**Short answer.** Yes, build it. Call it a **type lead** and keep it small and honest.
A lead is plain draft text that the Mac panel inserts after you accept a `#` row at the
start of an empty new-task item. You can see it before you capture, and one Backspace or
⌘Z removes it. Bob decides when a lead applies and what it says. The text comes from a
new `capture.type_leads` block in the chezmoi config, not from `types:`. `bob capture`
itself never adds the text. Everything is additive: an older bob or an older Mac app
just doesn't show leads. The full recommendation is in [§9](#9-recommended-solution).

---

## 1. What exists today

The current behavior is measured against Bob 0.6.0 (`grammar: 34`) on this host.

- **The `#` menu already knows when a marker is at the start of the line.** In bob-cli,
  `src/native/capture_complete/task_types.rs` gets `leading` from
  `capture_language::task_type_completion_at`. When the marker is at the start and no
  whitespace follows, it adds a trailing space to the replacement. `#f` with the caret
  at 2 returns:

  ```json
  {"context": "task_type", "subject": "new", "replacement": {"start": 0, "end": 2},
   "candidates": [
     {"name": "FIX", "replacement": "#fix ", "cursor_after": 5, "origin": "configured", "effect": "set"},
     {"name": "F",   "replacement": "#f ",   "cursor_after": 3, "origin": "typed", "refused": "type_not_configured"}]}
  ```

  `#f the login bug` returns `#fix` with no space. `Buy milk #f` (a trailing marker)
  also returns `#fix` with no space. `@cash #f` and `@sase^parser #f` count as leading,
  because a route may come first.
- **A marker alone is refused.** `bob capture --dry-run '#fix'` fails with
  ``capture item 1 … `#fix` needs a task``.
- **The redundancy is in Bob's own docs.** The first example in docs/capture.md
  "Typing tasks with `#<type>`" is literally `#fix Fix it`. The dry run of
  `#fix Fix the login bug` writes `- [ ] #task Fix the login bug [type:: FIX]`. The
  marker sets the type field and the verb stays in the task text. A lead takes nothing
  away from the stored result. It only saves typing the verb.
- **The Mac panel applies Bob's edit as given.** In bob-mac-capture,
  `CapturePanelModel.acceptSelectedCompletion` sends `task_type` rows to
  `applySelectedCompletionReplacement`. That function splices `candidate.replacement`
  and places the caret at `cursor_after` through `setPlainDraft`, which swaps the draft
  programmatically. It does not use the native-edit lane (`applyNativeRewriteEdit`) that
  sigil aliases use for one-step Undo.
- **The Mac already removes auto-inserted text as a unit.** Per keyboard.md,
  "Backspace — Remove an auto-inserted `,<digit>` pair or empty `****` skeleton
  together". The app already tracks text it inserted and lets one Backspace take it
  back.
- **Your vocabulary is in chezmoi** at `home/dot_config/bob/config.yml`:
  `types: {BUILD: yellow, CHORE: magenta, FIX: red, MEET: blue, PLAN: auto, READ: green, WRITE: violet}`.
  You asked for leads on five types and left out CHORE and MEET, which have no natural
  verb.

## 2. Is this a good idea? (critique)

**Mostly yes, but it saves less than it seems, and a wrong lead costs a key to undo.** A
correct lead saves about 5 key events ("Fix " plus Shift). A wrong lead costs about 1
(delete it), as long as deleting is a single key. So a lead is worth having for a type
whenever your task text for that type starts with that verb more than about 1 time in
5. If deleting took four Backspaces, the bar would be closer to 1 in 2. That is why the
one-key undo in §4.5 is part of the feature, not decoration.

How often do your tasks already start with the verb? I counted, read-only, across the
`#task` lines in the vault's Markdown, including archives. The per-type rows count only
tasks with an explicit `[type:: X]` field, which are mostly tasks typed with `#x` at
capture.

| Type | Tasks with explicit field | Text starts with the lead | Rate | Most common first words |
| --- | ---: | ---: | ---: | --- |
| FIX | 184 | 94 | **51%** | Fix 94, Make 20, Add 6, Ensure 5 |
| PLAN | 19 | 3 | 16% | Add 5, Create 4, Plan 3 |
| BUILD | 4 | 0 | 0% | Use 2, Make 1, Add 1 |
| WRITE | 1 | 0 | — | (too few) |
| READ | 1 | 0 | — | (too few) |

Across all 5,757 task lines, the first word is "Fix" 246 times, "Read" 181 times (155 of
them prose, not wikilinks), "Write" about 15, "Plan" about 8, and **"Build" 0**. The
common BUILD-style verbs are "Add" (708), "Make" (185), "Migrate" (170), and "Create"
(67).

What I take from this:

- **FIX is a clear win.** Half your FIX tasks already start with "Fix", without any
  nudge.
- **READ and WRITE are plausible.** You rarely type them explicitly today, but "Read …"
  and "Write …" are common openings in general.
- **PLAN is around break-even.** In an inbox capture, `#plan` is already the inherited
  type ("gtd suggests PLAN"), so its effect is `keep` and no field is written. Typing
  `#plan` there is just a shortcut for typing "Plan ". That is harmless and arguably
  nice.
- **BUILD is the likeliest miss.** You have never started a task with "Build". A lead
  will either nudge you toward "Build …" or cost a Backspace. I'd keep it as you asked,
  since removing it is one config line, but it is the one to watch. See §3, item 6.

Other honest points:

- **Upside:** it keeps your task names verb-first, which is good next-action practice,
  and it makes the redundant `#fix Fix` habit cost nothing.
- **Cost:** Tab gains a hidden behavior. That is fixable by showing the lead in the menu
  row before you accept, so nothing is hidden.
- **Risk:** a lead could reach the vault without you seeing it. The design must prevent
  that. It never applies on accept-and-capture gestures, and Bob never adds text when it
  writes.

**Verdict:** worth it, and the design below keeps it nearly free when the lead is wrong.

## 3. Requirement adjustments (called out)

1. **Where it applies.** You said "the start of a capture". I'd make it **the start of
   an empty new-task item**:
   - It works in every item of a multi-item draft, not just the first.
   - It works after a leading route (`@cash #f`), which Bob already treats as leading.
   - It never applies when the item retypes an existing task (subject `existing`), when
     the marker is trailing, on first-level `- #` bullets (those are drawers), on nested
     child lines, when the line already has text after the marker, or when the item
     already has another type marker.
2. **What counts as "selecting".** Tab, Return, and a click apply the lead.
   **⌃↩ / ⌘↩ (accept, then capture) do not.** Otherwise `#f⌃↩` would quietly create a
   one-word "Fix" task. Today that gesture gets Bob's "needs a task" error, which is the
   right result. Typing the full name and then Space (`#fix␣`) never accepts a row, so
   it never adds a lead. That gives you a natural way to say "just the type".
3. **Config lives in `capture.type_leads`, not under `types:`.** Changing the value of
   `types.FIX` from `red` to `{color: red, lead: Fix}` looks tidier but breaks things:
   today's `parse_themes_config` rejects any value that isn't a palette slot, and the
   rejection drops the whole vocabulary. Any host still running an older bob would lose
   every type color and the configured menu ordering. Unknown keys under `capture:` are
   ignored by every current loader, so chezmoi can ship the new block before bob does.
4. **Call it a "lead", not an "expansion".** In Bob's grammar, `%` already "says how the
   draft expands" (`decisions:capture-sigils-say-where-what-how`, templates, clips).
   "Lead" (the words a task of this type leads with) avoids that clash.
5. **Leads are explicit strings, not derived from the type name.** All five of yours
   happen to be the type name in title case, but an explicit value lets other types use
   `MEET: Meet with` or `REVIEW: Review`. It also keeps the config readable: what you
   write is what gets typed.
6. **BUILD stays, flagged.** Ship all five as asked. Re-check BUILD after about two
   weeks. If you keep deleting "Build", remove that line, or try `BUILD: Add` if that
   fits how you think.

## 4. Design

### 4.1 Name and meaning

**Type lead:** the text Bob offers to type right after a `#<type>` marker that you
accept at the start of an empty new-task item. It is ordinary body text once inserted.

### 4.2 Config (chezmoi `home/dot_config/bob/config.yml`)

```yaml
capture:
  clipboard_history: alfred
  # Type leads: accepting one of these from the # menu at the start of an empty
  # capture item also types its lead — `#f` ⇥ → `#fix Fix ▌`. Backspace right
  # away (or ⌘Z) removes just the lead. Older bob builds ignore this key.
  type_leads:
    BUILD: Build
    FIX: Fix
    PLAN: Plan
    READ: Read
    WRITE: Write
```

- **Shape:** a mapping from type name to a non-empty, single-line string. Bob inserts
  the value as written plus exactly one space. `null` or an empty value means no lead,
  so you can switch one off without deleting the line.
- **Keys:** must be valid single type names. Keys are matched by normalized key (`fix`
  and `FIX` collide). The clock-tag names are rejected
  (`decisions:capture-reserves-clock-tags`). When `types:` is configured, a key outside
  it is ignored with a warning.
- **Values:** Bob validates each lead once, at load, by parsing a probe draft
  `#<type> <lead> x`. The lead must come back as plain body text, with no route, marker,
  directive, relation, or close span. That keeps leads like `@home` or `x` from changing
  the grammar. The check uses Bob's own parser, not a character blocklist
  (`decisions:mac-capture-is-a-thin-client`: Bob is the only grammar).
- **Errors:** a bad entry drops only itself, with a bounded warning. `types:` drops the
  whole block on any error, which protects the vocabulary. Leads are only an editing
  aid, so dropping one entry is enough. Warnings appear in `bob types list`, where you
  already look for type-config problems. Optionally, the row meta can show
  `lead "Fix"` so you can confirm the config took effect.

### 4.3 When a lead applies (Bob decides)

All of these must hold for a `task_type` candidate (editor builder only; zsh's
`build_for_shell` never gets leads):

| Check | Source |
| --- | --- |
| `subject == "new"` | already computed in `task_types.rs` |
| The marker is leading and not attached | `TypeMarkerCompletion.leading` |
| The marker is on the item's first line, not a child line | `completion_at` line index |
| Only whitespace follows the replacement range on that line | raw text after `replacement.end` |
| The item has no other type marker | `type_marker::scan_line` |
| The candidate is not refused (`type_not_configured`, `type_marker_not_applicable`) | existing `refused` |
| The type's key has a configured lead | `capture.type_leads` |

Hidden types still get their lead when you accept them by exact name
(`decisions:theme-hide-is-recent-only`). The effect (`set`, `keep`, or `clear`) doesn't
matter, because the lead is about the text, not the type field.

| Draft (caret at end) | Accept | Result |
| --- | --- | --- |
| `#f` | FIX | `#fix Fix ▌` |
| `@cash #f` | FIX | `@cash #fix Fix ▌` |
| `Fix a` ⏎⏎ `#w` (second item) | WRITE | second item `#write Write ▌` |
| `#f▌ the login bug` | FIX | `#fix▌ the login bug` (text already there, so no lead) |
| `Buy milk #f` | FIX | `Buy milk #fix` (trailing) |
| `@sase:fix-x #f` | FIX | retype only (existing task) |
| `#fix #b` | BUILD | no lead (second marker, which is an error anyway) |
| `#c` | CHORE | `#chore ▌` (no lead configured) |
| `#f` then ⌃↩ | FIX | `#fix ` and capture → Bob: "needs a task" |

### 4.4 Wire contract (additive, `schema_version` 1)

Add an optional `lead` object to `TaskTypeCandidate`. Leave `replacement` and
`cursor_after` exactly as they are. Per PT8, a `#` field's replacement "covers just the
name", and other code relies on that.

```json
{"name": "FIX", "replacement": "#fix ", "cursor_after": 5,
 "lead": {"text": "Fix", "insert_at": 5, "insertion": "Fix ", "cursor_after": 9}}
```

- `insert_at` and `cursor_after` are UTF-8 byte offsets in the draft *after*
  `replacement` has been applied. Bob computes them, so the Mac never decides spacing.
- `text` is the display form for the menu row.
- The field is omitted when no lead applies. No `grammar` bump is needed, and it ships
  as a plain `feat` on the release train (`decisions:bob-cli-releases-ride-a-daily-train`).

**Rejected: putting the lead inside `replacement`.** That would ship without any Mac
change, but it has four costs. ⌃↩ would capture one-word "Fix" tasks. The menu couldn't
show the lead before you accept. Undo and Backspace couldn't remove the lead separately
from the marker. And it would change what PT8 says a `#` replacement means.

### 4.5 Mac presentation (the "beautiful" part)

**The menu row shows what you'll get.** Put the lead right after the type pill, in
tertiary label color, caption size, ending in an ellipsis. Each row then looks like the
draft it produces:

```
TASK TYPE                                        ● ◆ PLAN · from gtd
  ◆ BUILD  Build…                                             3 days
  ◆ CHORE                                                     today
  ◆ FIX    Fix…                                               today
  ◆ MEET                                                     2 days
  ◆ PLAN   Plan…   from gtd                                   today
  ◆ READ   Read…                                              1 day
  ◆ WRITE  Write…                                        never used
⇥ take the first · type a letter · ⏎ capture as typed
```

Rows without a lead don't change. The footer copy stays Bob's ("this task becomes FIX ·
gtd suggests PLAN"), so the lead never pushes that line over its single-line limit. In
`CaptureTaskTypeMenuView.rowView`, this is one `Text` between the pill and the badges.

**Accepting with Tab, Return, or a click** applies `replacement` as today. It then
inserts `lead.insertion` at `lead.insert_at` through `applyNativeRewriteEdit`, as its
own native undo group, and moves the caret to `lead.cursor_after`. VoiceOver announces
"FIX, typed Fix". On ⌃↩ / ⌘↩ (`acceptSelectedCompletionThenSubmitAndOpen`), skip the
lead.

**Taking it back costs one key:**

- **Backspace right after an untouched lead removes the whole lead** (`#fix Fix ▌` →
  `#fix ▌`). Track the lead the same way the app tracks `closeCommaProvenance` and the
  `****` skeleton: the lead stays removable as a unit only while the draft still equals
  the post-insertion draft and the caret is at its end. Once you type, move the caret,
  or paste, it is ordinary text. ⌥⌫ stays native, and native word-delete removes
  "Fix " anyway.
- **⌘Z** first removes the lead, then the marker completion (which needs that
  acceptance to be undoable; see §8).

**One optional flourish.** The inserted lead could fade from tertiary to primary over
about 200 ms, so you can see it was typed for you. Skip the animation under Reduce
Motion. Nothing stays styled afterward, because the lead is your text now.

### 4.6 What does not change

- `bob capture`, `capture-parse`, paste, piped stdin, templates, and zsh completion
  never add leads. Leads exist only in the editor, the same rule capture aliases follow.
- Type fields still follow PT13: the `#` marker is the explicit choice, and the lead is
  just body text.
- Older bob means no `lead` field and no change. An older Mac ignores the field.

## 5. Alternatives considered

| # | Approach | Verdict |
| --- | --- | --- |
| A | **Editor lead on an accepted row** (this report) | **Recommended.** You see it, can undo it, Bob decides it, and it is additive. |
| B | Put the lead inside `replacement` (bob-only change) | Rejected. ⌃↩ junk tasks, no preview, no separate undo, changes PT8 meaning (§4.4). |
| C | Add the verb when capturing: `#fix the bug` → "Fix the bug" | Rejected. You don't see it before capture, it surprises CLI, paste, and stdin users, and it mangles text that doesn't start with a verb. |
| D | Guess the type from the verb: typing "Fix the bug" sets FIX | Rejected for now. It contradicts PT13 ("task fields are written only by an explicit type choice") and would mis-type tasks (is "Fix dinner" FIX?). The same `type_leads` table could later drive a suggestion that writes nothing. |
| E | Ghost text: show a dim "Fix" after `#fix `, Tab to keep it | Fallback only. An extra key when the lead is right, nothing when it's wrong. It is better only when the lead is wrong more than half the time. Since you only configure leads for verb-led types, inserting wins. It also adds a second meaning for Tab and new Mac state. |
| F | Extend `types:` values (`FIX: {color: red, lead: Fix}`) | Rejected. On any host running an older bob, the whole vocabulary would be dropped (§3, item 3). |
| G | Saved templates (`%t`) or macOS Text Replacement | Rejected. More keystrokes, or bypasses Bob's grammar and menu entirely. |

## 6. Governing decisions

- `decisions:mac-capture-is-a-thin-client`: Bob computes whether a lead applies, its
  text, and its offsets. The Mac only renders and applies them. The feature lands in
  bob-cli and docs/capture.md first.
- `decisions:capture-sigils-say-where-what-how`: a free `#` at an item edge names a
  type. Leads add no syntax. `%` owns "expands", hence the name "lead".
- `decisions:capture-bullets-mirror-the-task-block`: a first-level `- #` names a
  drawer, so no lead there.
- `decisions:capture-reserves-clock-tags`: clock-tag spellings can't be lead keys.
- `decisions:theme-hide-is-recent-only`: hidden types keep their lead when typed.
- `decisions:similar-tasks-are-a-settled-heads-up`: a body that is only a lead ("Fix")
  must not trigger the Similar tasks band. Add a test.
- `decisions:bob-cli-releases-ride-a-daily-train`: additive `feat`, no `!`, no version
  or CHANGELOG edits.

**Proposed new decision record:** *"Type leads are editor text."* A lead is inserted only
when you accept a `#` row at the start of an empty new-task item. It is visible and can
be removed with one key. Bob never adds it at write time. Leads are configured in
`capture.type_leads`. This would reopen if verb-based type suggestions (D) are ever
wanted. Add a glossary term **Type Lead** too. Both go through `/sase_memory_write`.

## 7. Implementation sketch

**Phase 1: bob-cli** (feat, about 200 lines plus tests and docs)

- `src/native/config/capture.rs`: add a `load_type_leads` loader for `type_leads`,
  separate from the other capture keys and per-entry tolerant like the clipboard keys.
  Include the parser probe validation from §4.2.
- `src/native/capture_complete/model.rs`: add `lead: Option<TaskTypeLead>` with
  `skip_serializing_if = "Option::is_none"`.
- `src/native/capture_complete/task_types.rs`: in `candidate()`, attach the lead when
  the §4.3 checks pass, and only from `build` (never `build_for_shell`).
- `bob types list`: show lead config warnings, and optionally a `lead` meta and JSON
  field.
- Docs: docs/capture.md ("Typing tasks with `#<type>`" and the `bob capture-complete`
  contract), a cross-reference in docs/task-types.md PT12, and the config reference.
  Read `sase/memory/docs.md` first.
- Tests: every row of the §4.3 table, offsets in a second bulk item, a multibyte lead,
  `#"DEEP WORK"` literals, shell completion never carrying `lead`, invalid config
  entries, and no Similar tasks band for a lead-only body.

**Phase 2: bob-mac-capture** (gated by macOS CI; watch the exact-SHA run to green)

- `CaptureModels.swift`: decode `lead` with `decodeIfPresent`.
- `CaptureTaskTypeMenuPresentation`: add `Row.leadText`, plus the lead in the
  accessibility label ("Types Fix.").
- `CaptureTaskTypeMenuView`: show the row hint.
- `CapturePanelModel`: after a `task_type` accept, insert the lead through
  `applyNativeRewriteEdit` and skip it on the ⌃↩ / ⌘↩ path. Add Backspace-as-a-unit
  tracking and a VoiceOver announcement.
- Docs: capture-panel.md, keyboard.md (Tab, Return, and Backspace rows), and a
  protocol.md capability row ("`task_type` candidate `lead`" · "row hint, lead on
  accept" · older bob: "no lead").
- Fixtures: a variant of `task-type-complete-leading-prefix.json` that includes a lead.

**Phase 3: chezmoi.** Add the §4.2 block, then run `chezmoi update -a --force`. This is
safe to land first, because every current loader ignores unknown `capture:` keys.

## 8. Risks and open questions

- **Undo of the marker acceptance.** Today's `task_type` acceptance goes through
  `setPlainDraft`, not the native-edit lane, so the second ⌘Z (restoring `#f`) may not
  work now. That is not required for this feature, but the lead insertion itself must
  be its own native undo group.
- **Backspace removing the lead as a unit.** If you'd rather Backspace only ever delete
  one character, drop that behavior. ⌘Z and ⌥⌫ still make a wrong lead cost one chord.
  I recommend keeping it, because it matches the existing `****` and `,<digit>`
  behavior.
- **Nested req lines (`  - #f`).** I left these out of v1. They could be added later
  with the same rule.
- **Later ideas:**
  - Swap the lead when you retype (if the rest of the line is exactly the old type's
    lead, replace it).
  - A one-time "Next time: `#f` ⇥ types Fix" tip when you type the verb by hand after
    accepting a type that has a lead.

## 9. Recommended solution

My recommendation is to build **type leads** as an additive, editor-only feature:

1. **Config:** add `capture.type_leads: {BUILD: Build, FIX: Fix, PLAN: Plan, READ: Read, WRITE: Write}`
   in chezmoi. It is safe to land first. Use explicit strings, and Bob validates each
   one with its own parser.
2. **bob-cli:** `capture-complete` attaches an optional `lead`
   `{text, insert_at, insertion, cursor_after}` to `task_type` rows, only when the
   marker starts an empty new-task item: leading, first line, nothing after it, no
   other marker, not refused, and a lead configured. `replacement` keeps its meaning,
   and `bob capture` never adds text.
3. **Mac:** show the lead in each row (`◆ FIX  Fix…`). Tab, Return, or a click inserts
   it as its own undoable edit, with the caret after it. ⌃↩ / ⌘↩ never insert it.
   Backspace right after an untouched lead, or ⌘Z, removes just the lead.
4. **Policy:** record "Type leads are editor text" as a decision and add the Type Lead
   glossary term. Re-check BUILD (and PLAN) after about two weeks, because your history
   predicts those will be the misses.

Result: `#f` ⇥ `the login bug` → `#fix Fix the login bug` → `- [ ] #task Fix the login
bug [type:: FIX]`. That saves five key events when the lead is right and costs one when
it isn't. You see the lead in the menu before you accept, and Bob stays the only grammar.

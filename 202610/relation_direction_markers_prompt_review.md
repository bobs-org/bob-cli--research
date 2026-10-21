# Review: the prompt to replace `~~` with `<` / `>` relation markers

**Bottom line.** The idea is good and fits epic `bob-cli-am`. Moving direction onto
the label marker makes "no label, no direction" true in the syntax itself, and it
removes the epic's awkward "bare `~~` needs a label" state. But the prompt has two
problems:

1. **Timing.** Launched today, it would collide with phases that are still running.
2. **Gaps.** It leaves out five decisions an agent can't safely guess.

A revised prompt is at the end.

## 1. Timing: wait for `bob-cli-am` to close

Phases `.3`, `.4`, `.5`, `.7`, and `.8` are all `IN_PROGRESS` right now. Three of them
are building exactly what this prompt removes:

| Phase                | What it is adding                                                                                                                |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `.3` capture-grammar | `relation_label_required` for a bare `~~`, `~~note:id\|` replacements, the shell group `reverse · needs a label`                |
| `.7` nav-stage       | `⇧L` kept as reverse-label mode, the `Ctrl+Shift+Alt+L` hotkey, `⇄ swap (Alt+R)`                                               |
| `.8` mac             | the `~~` picker, a Swap that adds or removes a `~`, and "an empty label on `~~` rewrites to `~`"                                 |

**Recommendation:** launch this as a follow-up once the epic closes, and have the
prompt name those pieces as things to undo. The alternative is to pause `.3`, `.7`,
and `.8` and amend the plan, which causes more churn mid-flight.

## 2. Decisions the prompt must make

1. **Which way `<` and `>` point.** There are two natural readings, and they conflict:

   | Draft                     | Reading A: relative to the captured task | Reading B: the arrow touches T |
   | ------------------------- | ---------------------------------------- | ------------------------------ |
   | `Fix it ~work:foo>"x"`    | Fix it —x→ Foo                           | Foo —x→ Fix it                 |
   | `Fix it ~work:foo<"x"`    | Foo —x→ Fix it                           | Fix it —x→ Foo                 |

   I'd pick **A**: `>` replaces today's common `~T|x`, `<` replaces `~~T|x`, and the
   mnemonic is "this > T". Reading B is just as defensible, because it matches the
   chip `x → (T)`. Whichever you choose, put both example lines in the prompt
   word for word.

2. **What happens to `|`.** The prompt only says "in place of". I recommend retiring
   `|` along with `~~`, since a label now always carries a direction. `bob capture`
   should refuse both old spellings with a teaching error that shows the new form, and
   never silently reinterpret them (the epic already set that rule for `~~`).
   `~~old~~` stays plain strikethrough text.

3. **An empty label after a marker** (`~T>`). While typing, treat it as incomplete
   (`needs: relation_label`). If the user presses Return with the label still empty,
   make it a plain link and drop the marker. Use the same rule on the Mac and in
   Obsidian.

4. **What "direction before label" means in Obsidian** (the prompt says "somehow").
   Here is one concrete design:
   - Links stage: `↵` makes a plain link, as today. Pressing `>` or `<` on the
     highlighted row picks the direction, then the label field opens with the sentence
     already fixed ("This task — [label] → Other"). A fallback is `⇧↵` followed by a
     two-row chooser ("This task → Other" / "Other → This task").
   - Give the Mac `~` picker the same keys, so both surfaces share one model: pick the
     task, press `>` or `<`, type the label.
   - The same step applies to CURRENT `⇧↵` on a plain row (adding a label to an
     existing plain link).
   - Settle the leftovers: keep `⌥R` swap as a way to fix a wrong choice (recommended),
     and remove `Ctrl+Shift+Alt+L` and the "Links: describe this task from another"
     command together with `⇧L`.

5. **JSON contract.** Change the typed syntax only, and keep `direction: to|from`,
   `kind`, and `relation_label` in the JSON. Decide whether the `relation_from`
   completion rows and `capture-task-id`'s `relation_from_replacement` are removed or
   deprecated. Either way this is a `feat(capture)!:` break.

## 3. Things an agent will likely miss

- **When the Mac card should open (your "triggered when appropriate").** Spell this
  out:
  - The characters that open the card when typed are hard-coded as `:`, `^`, and `|`
    in **two** files: `CapturePanelController.swift` and `CapturePanelModel.swift`
    (`noteSeparatorToggleIntent`). Add `<` and `>`. Like `|`, they are Shift keys on a
    US layout, so the key-event tests need `.shift`.
  - Picker paths: `acceptPickerRow`, `openRelationLabelPromptFromPickerRow`, and the
    ID-less `completeRelationIDAssignment`.
  - The app reads direction from the `~~` prefix itself
    (`token.hasPrefix("~~") ? .linkedFrom : .linksTo`) and from
    `flipRelationDirection(insertingSecondTilde:)`. Both should go. Swap becomes a
    `<`↔`>` byte edit at the separator range bob reports, so the app stays a thin
    client.
  - List what should happen: the card **opens** when `>` or `<` is typed after a
    complete `~note:id`, on the picker's label gesture, and after an ID-less mint. It
    **stays closed** for `~/path`, `~5m`, `x~`, `=~2`, and inside a quoted label.
- **Release order.** The Mac runs the installed `bob` and doesn't check its version.
  An old bob reads `~work:foo>x` as an invalid block ID and errors. So the Mac change
  has to ship **after** a bob release with the new grammar reaches the Mac, and bob
  only ships on the daily train. In the other direction, a new bob given an old Mac's
  `~~` or `|` returns the teaching error.
- **Shell trap.** Unquoted, `bob capture Fix it ~work:foo>see` writes bob's output to a
  file named `see` and quietly captures a *plain* link, with no error at all. `|` at
  least printed `command not found`. Keep every doc example single-quoted, and make the
  shell completion rows escape `<` and `>` the way they already escape `|`.
- **Grammar edges:**
  - The note part must reject `<` and `>`; today it rejects only `~` and `|`.
  - The separator is the first `<` or `>` after the block ID.
  - Leave the stored label character set alone. Labels can contain `<` and `>` today,
    and the epic keeps storage byte-for-byte unchanged.
- **Memory.** `glossary:task-relation` and `glossary:directed-relation` teach `~~T|label`.
  The epic approved editing those strands once, for that epic only. This prompt must
  either authorize the edits again or tell the agent to file memory beads. Optionally,
  add a decision record ("direction lives on the label marker; `~~` and `|` are
  retired"); the epic chose not to write one.
- **Update the contract first.** The vectors in `docs/task-relations.md` §15 (LP2,
  LP21, LX14, LX15, LX17, LG7, LG16, LG18), the shell group names, and
  `docs/_meta/contracts.yml` all mention `~~` or `⇧L`. The repo's contract-first rule
  says to change these before the code.
- **Scope.** This touches three repos and has a required order, so ask for a plan
  (`/sase_plan`) with phases: bob grammar and contract → bob docs → plugins → Mac.
  Don't hand it all to one agent.
- Checked and clean: the chezmoi dotfiles contain no snippets that type `~~` or `~T|`.

## 4. Suggested prompt

> Once epic bob-cli-am has closed, write a plan (`/sase_plan`) that replaces the `~~`
> capture sigil and the `|` label separator with direction markers:
>
> - `Fix it ~work:foo>"follow-up of"` means Fix it —follow-up of→ Foo.
> - `Fix it ~work:foo<"next step"` means Foo —next step→ Fix it.
> - `~work:foo` stays a plain (undirected) link.
>
> Rules:
>
> - `bob capture` refuses `~~T…` and `~T|x` with a teaching error that shows the new
>   form. Nothing is reinterpreted silently. `~~old~~` stays strikethrough.
> - `~T>` with an empty label needs `relation_label`. Return on an empty label makes
>   it a plain link, on every surface.
> - Keep the JSON vocabulary (`direction`, `kind`, `relation_label`). Remove the
>   `relation_from` rows and `relation_from_replacement`. This is a `feat(capture)!`
>   break.
> - Obsidian: remove the Task Card's `⇧L`, `Ctrl+Shift+Alt+L`, and reverse-label mode.
>   In the Links stage, `↵` links plainly, and `>` / `<` on a row (or on a plain CURRENT
>   row) picks the direction before the label field opens. Keep `⌥R` swap.
> - Mac: the same `>` / `<` keys in the `~` picker. Typing `>` or `<` after a complete
>   `~note:id` opens the label card (add both characters to the typed-trigger list in
>   `CapturePanelController.swift` and `CapturePanelModel.swift`). Swap flips `<`/`>`
>   at bob's separator range. Drop the `~~` picker and all app-side `~~` checks. Ship
>   only after a bob release with the new grammar reaches the Mac.
> - Contract first: update `docs/task-relations.md` §15 and the shell groups. Escape
>   `<` and `>` in shell completion rows, and single-quote every doc example.
> - Memory edits are authorized for `glossary:task-relation` and
>   `glossary:directed-relation`.

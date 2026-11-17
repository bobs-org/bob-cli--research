# Schema cards: field jumps, numbered destinations, and visual hierarchy

Independent research by **cdx**, 2026-11-17. This report was developed from the supplied screenshot, repository code and documentation, focused local probes, and primary browser/accessibility documentation. No other researcher’s report or findings were consulted. This is a design recommendation; no production code or vault files were changed.

## Assessment

**Yes: add the shortcuts and the spacing.** The proposal addresses a real mismatch between the card’s visual hierarchy and its keyboard navigation. Fields organize choices, but the existing album keyboard walk treats almost everything as one flat sequence. A second, coarse navigation command is a better fit than making users traverse every chip.

In the supplied screenshot, Status has six choices and an Add choice target. Starting on Status, the current implementation takes **eight** downward row steps to reach Claim. A single `J`, or `2`, should focus Claim. That is a meaningful improvement without changing how schema edits are made.

The feature is not quite an additive key binding. **Digits already mean something in both implementations**, and the current album navigation can disagree with an unsaved displayed reorder. Resolve those conflicts as part of the feature. Otherwise, a beautiful numbered interface could be unreliable precisely when users are arranging it.

My recommended design is **two navigation scales over the same visible order**: existing fine navigation visits rows and choices; uppercase `J`/`K` visits major destinations; `1`–`9` focuses the correspondingly numbered destination. All three select and focus, without editing or saving. Add restrained number keycaps and extra space between field blocks. Keep the existing writer, preview, confirmation, and undo machinery.

## What the current implementation establishes

Inspected revisions:

- bob-cli: `99005975e15aaa3c2440b36e8f87dc4481908500`.
- bob-plugins: `474ba89208dcc21b670d4ea36489970a3276a7e9`.
- Screenshot: `/home/bryan/tmp/screenshots/20261117_110414.png`.

The source paths below are relative to the named repository, so they remain useful outside this researcher’s temporary checkout.

| Finding | Evidence and consequence |
| --- | --- |
| Album and record entry points share one Schema Card. | bob-plugins `plugins/bob-ledger-tools/src/242d-plugin-album-entrypoints.js:64`, `albumResolveSchemaTargetForFile()`, resolves a record’s actual parent to its album. Implement once for both; a separate record schema editor is unnecessary. |
| The album’s selectable targets are flat. | `src/242c-plugin-album-schema-edit.js:4`, `albumSchemaTargets()`: details, each field and its choices/Add choice, Add field, issues. `src/241y-plugin-album-schema-card.js:65`, `schemaMove()`, walks that list and wraps. |
| Album digits are reorder counts. | `src/241yb-plugin-album-schema-arrange.js:827` intercepts digits before the base key handler. `schemaArrangeConsumeCount()` at line 81 later applies the buffered count to a nudge. bob-cli `docs/reference/plugins/albums.md` explicitly documents `4Alt+K`. |
| Bank Setup is structurally different. | `src/248i-plugin-bank-setup-card-model.js:12` models groups/categories, accounts, rules, and findings. Categories, Accounts, Rules, Checks are separate tabs. A bank category group is the closest analogue to a field with choices. |
| Bank shortcuts already accept digits and uppercase letters. | `bankSetupCardSelectionByHotkey()` at line 123 lowercases the input. `src/248k-plugin-bank-setup-card.js:667` dispatches category keys. Thus a configured `2` selects a category, and uppercase `J` can select the category assigned `j`. |
| Rendering knows the proposed order; album targets do not. | `src/241yc-plugin-album-schema-card-regions.js:281`, `albumSchemaCardPaintBody()`, uses projected field/choice order. `schemaTargets()` still reads `schemaModel`. Bank has its own display projection in `src/248j-plugin-bank-setup-card-dom.js:63`. |
| Focus restoration deliberately avoids scrolling. | Album `src/241yd-plugin-album-schema-card-paint.js:68` and bank `src/248kb-plugin-bank-setup-card-regions.js:390` use `focus({preventScroll:true})`. Jump navigation must explicitly reveal an offscreen destination. |
| Keyboard handling is layered. | Album’s base handler is wrapped by arrangement handling and then `src/241ye-plugin-album-schema-place.js:514` for insertion ghosts. Bank has an arrangement wrapper too. Editing only the base handler is insufficient. |
| Useful visual structure already exists. | Field labels, metadata pills, choice clouds, focus rings, contextual hints, and drag grips already have renderers and CSS. The change can extend their visual language. |

Except where a full path is given, the `src/` paths in this table are under bob-plugins `plugins/bob-ledger-tools/`.

### Local verification

I ran the existing album shell/arrangement and bank setup/arrangement suites:

```sh
node --test --test-reporter=dot \
  scripts/test-ledger-tools-album-schema-card-shell.cjs \
  scripts/test-ledger-tools-album-schema-arrange-card.cjs \
  scripts/test-ledger-tools-bank-setup.cjs \
  scripts/test-ledger-tools-bank-setup-arrange.cjs
```

All **73 tests passed**. These establish the current baseline; they do not test the proposed behavior.

A separate in-memory probe reused the existing album test fixture and exported bank helpers, with mocked writers. It confirmed:

- Status → Claim takes eight current row steps with the screenshot’s six Status choices.
- Uppercase `J` currently leaves the album selection unchanged.
- `2` leaves selection unchanged and stores reorder count `2`; a subsequent lowercase `j` moves to a choice while the count remains buffered.
- Bank’s hotkey helper resolves `2` to a category assigned `2`, and uppercase `J` to one assigned `j`.
- After moving Claim below Section locally, the arrangement reports `[status, section, claim]` while `schemaTargets()` still reports `[status, claim, section]` for fields.

The last finding is a concrete integration hazard, not a hypothetical edge case. These are fixture-level observations, not a claim that the new interaction has been validated in live Obsidian.

## Proposed interaction contract

### Album and record cards

Here, “field” means an existing schema field header such as Status, Claim, or Section. Choices, Add choice, Add field, album details, lint messages, drag handles, and insertion ghosts do not receive field numbers.

| Input in browse mode | Result |
| --- | --- |
| `J` | Focus the next field header strictly after the current selectable item in displayed order. |
| `K` | Focus the previous field header strictly before the current selectable item in displayed order. |
| `1`–`9` | Immediately focus that numbered field, if it exists. |
| Lowercase `j`/`k` and existing arrows | Keep fine navigation through individual targets. |
| `Enter` | Keep the existing edit/save behavior appropriate to the current mode. |
| `Alt+J/K`, end moves, Move to…, drag | Keep explicit reordering. |

“Strictly before” is intentional. From a Status choice or Status’s Add choice, `K` lands on **Status itself**, because that header is the preceding field selection. From the Status header, `K` seeks the preceding field. `J` from either the Status header or any of its children goes to Claim.

Concrete acceptance examples:

| Starting selection | `J` | `K` | `2` |
| --- | --- | --- | --- |
| Status header | Claim | Stay, if Status is first | Claim |
| Status → Draft choice | Claim | Status | Claim |
| Status → Add choice | Claim | Status | Claim |
| Claim header | Section | Status | Claim |
| Section header | Stay, if Section is last | Claim | Claim |
| Add field below all fields | Stay | Last field | Claim |

For details or an issue displayed above the fields, `J` selects the first field and `K` stays. Use the actual rendered location: the current target list appends issues even though the lint region paints above the body.

**Do not wrap these new coarse jumps.** A long jump from bottom to top can look like an ordering error. Holding `J` should reach the end and stop. This deliberately differs from the album’s existing wrapping fine walk; it does not require changing that established behavior. At a boundary, preserve selection and consume the recognized jump. No warning toast is needed.

If the selection has disappeared during a model refresh, repair it deterministically by stable identity first, then a nearby surviving position; do not continue navigating from a detached DOM node. With no fields, leave the empty-state controls usable and omit the field-jump hint.

### Bank Setup: make the analogy explicit

Do not pretend Bank Setup contains an album schema, and do not silently interpret `1`–`4` as tab selection. Tabs already have a navigation mechanism; the user’s problem is traversing content within the card.

I recommend these **section-local major destinations**:

| Active bank tab | Numbered destinations, in displayed order | Hint wording |
| --- | --- | --- |
| Categories | Category-group headings, including Money moves, a visible Ungrouped heading when needed, and Hidden when present | `J/K groups · 1–9 jump` |
| Accounts | Account rows, followed by the existing Stale after setting | `J/K settings · 1–9 jump` |
| Rules | Rule rows | `J/K rules · 1–9 jump` |
| Checks | None: findings are diagnostics rather than editable settings | Keep its existing diagnostic navigation |

This is an explicit interpretation/extension of “field,” justified by the bank card’s actual structure. Numbering restarts at 1 in each tab and never jumps to another tab. Accounts and Rules gain little from coarse stepping because they are already flat; direct numbering still helps and costs little once the shared navigation helper exists.

Money moves and Hidden are navigable even when they cannot be renamed or reordered. Navigation eligibility and edit eligibility are separate. Ungrouped currently lacks a selectable group header: add a presentation-only heading/target when it has children. It must not create a stored group, permit renaming a synthetic group, or alter arrangement scopes. Likewise, promote Stale after to an explicit selectable presentation target rather than discovering its input through a CSS selector. It becomes editable only through its existing stage.

From a category chip, `K` goes to its group heading and `J` to the next group. From a group heading, both move to adjacent groups. A Hidden heading is a real destination if shown; hidden categories inside it remain children. Tab changes atomically replace the destination map and badges.

This proposal does **not** change the separate Category card used to acknowledge transactions, bank key assignments in YAML, or bob’s category-hotkey derivation.

### Resolve existing key conflicts deliberately

1. **Retire bare-digit reorder counts in the album Schema Card.** `2` cannot both jump immediately and wait to prefix a future nudge. Preserve repeated `Alt+J/K`, end moves, and the existing gap picker as efficient alternatives. Remove the count-buffer interception and consumption path, update its documentation/tests, and ensure old buffer state cannot survive into navigation. Do not add a timeout to guess intent, and do not introduce another prefix language in this change.
2. **Give `1`–`9` priority over category hotkeys in Bank Setup’s Categories tab.** Even an out-of-range digit must be consumed as an unavailable destination; it must not fall through to a category. Keep digit category keys in the transaction Category card and in configuration. A number must have one meaning within this Setup context.
3. **Give uppercase `J/K` priority over bank’s case-insensitive category lookup.** Lowercase `j/k` retain category selection there. Do not globally normalize the new shortcut to lowercase before dispatch.
4. **Make the display honest.** In Bank Setup, render working letter shortcuts in lowercase. A configured `1`–`9` category key must not appear as an active Setup keycap; show it as labelled metadata, for example `transaction key: 2`, in the selected-category details. Preserve the real assignment. The separate Category card retains its working keycaps.

`0` is not field ten. It gains no field-jump meaning; an existing Bank Setup category shortcut `0` may retain its current behavior. Fields 10 and above remain reachable with `J/K`, ordinary navigation, and pointer selection. Do not add multi-digit timing or renumber according to the scroll viewport.

### Focus, modes, and event priority

Interpret uppercase `J/K` through `event.key`, with no Ctrl/Meta/Alt modifier. Normally that is Shift+J/K; Caps Lock may also produce uppercase. Display `⇧J/⇧K` in discoverability text so the case distinction is clear. For digits, match the produced character `1`–`9`, allowing Shift where a keyboard layout requires it. Do not map the physical `Digit1` key when it produces `!`; `!` already has an album action. Preserve the existing `event.code` handling for macOS Option reorder chords. MDN documents why character intent and physical-key intent differ: [KeyboardEvent.key](https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/key).

The new shortcuts are active only in the topmost card’s browse region with focus owned by that region. They must not operate just because a modal exists while focus is in the editor behind it. Inside input, textarea, select, contenteditable, an Emoji Slot, IME composition, or a nested picker, those controls own their text. Reuse the broader text-context knowledge in `bobCardTypesText()` instead of repeating the narrower existing `input,select,textarea` checks. Respect `isComposing`, the card’s composition flag, and the legacy keyCode 229 guard.

The dispatcher should resolve ownership before navigation:

1. Ignore already-handled/composing events; respect the topmost child overlay.
2. Preserve Escape/q/Ctrl+[ and insertion/drag/gap-mode handling.
3. Keep form inputs and open edit stages in their current mode, even if a stage’s Save button has focus.
4. Preserve modified reorder commands.
5. Handle browse-only coarse jumps and digits, before category-hotkey fallback.
6. Fall through to existing fine navigation and other actions.

An active Move to… picker owns its badge letters, including `j/k`; field jumps must not steal them. A drag or insertion ghost must not acquire a field ordinal. Ordinary pending arrangements may remain navigable: selection changes neither the pending operations nor the Enter latch. During an apply, retaining the existing input lock is sufficient for the first implementation; do not expand this feature into a new save-concurrency policy. Stale/read-only browsing can support jumps where there are actual focusable destinations, while editing remains disabled.

Scope these handlers to the card. If Obsidian’s keymap scope needs a registration to prevent an earlier handler from consuming the event, delegate it to the same dispatcher with an event handled marker; do not create a second navigation implementation. Unlike the established close-key aliases, these jumps do not need to operate with editor focus.

WCAG’s character-shortcut guidance explicitly includes uppercase letters and numbers and allows activation limited to the relevant focused component. Merely avoiding text inputs is weaker than restricting focus to the navigation component. Keep normal buttons and keyboard focus available as alternatives; these shortcuts are accelerators. [W3C: Character Key Shortcuts](https://www.w3.org/WAI/WCAG22/Understanding/character-key-shortcuts.html).

## Visual design

The screenshot already has a useful vocabulary: a calm title, strong field names, compact metadata, choice chips, and one accent ring. Preserve it. The missing ingredient is a visible separation between a field’s children and the next field.

A schematic of the proposed hierarchy, with the choice list abbreviated:

```text
Zettel
4 zettels · dated notes

 ⠿ [1] Status     required                         set on 4 of 4
        [🌱 Seed 0] [✍️ Draft 4] [✅ Ready 0] …
        [✂️ Cut 0] [+ choice]

 ⠿ [2] Claim      required · text · sub-groups index
                                                   set on 4 of 4

 ⠿ [3] Section    sub-groups index                  set on 4 of 4
        [🪝 Intro 0] [🧱 What is SASE? 1] …
        [+ choice]

 [+ field]
 ⇧J/⇧K fields    1–9 jump    ↵ edit    …
```

This is a hierarchy sketch, not a proposed fixed-width layout.

- Put a quiet, fixed-width number keycap immediately before the field name, after the drag-grip slot. Use roughly a 1.4rem minimum gutter, tabular numerals, and the current keycap treatment. The number and name should wrap as one label cluster rather than separating onto different lines.
- Add about **12–16 CSS pixels between field blocks**, versus roughly **4–6 pixels between a field header and its choices**. Start with theme spacing tokens around these values. The first field does not need an extra blank band. Separate consecutive scalar fields too; the screenshot’s Claim/Section boundary is particularly compressed.
- Keep choices together under their owner; a modest inset can reinforce this at desktop widths. Reduce the inset on narrow screens rather than sacrificing an entire chip column.
- Keep counts at the trailing end of a choice and ordinals at the leading end of a header. They have different roles and should not share a badge style. Use muted but readable text, not opacity so low that the shortcut disappears.
- Keep the existing single focus ring. The active number may pick up the same accent; do not add a second prominent selection around the entire block when a child is focused.
- Show ordinals for every field. Style `1`–`9` as keycaps; style `10+` as ordinary ordinal text in the same gutter, with no keyboard-shortcut promise. During edit/picker modes, numbers may remain as orientation but the active jump hint is absent.
- Use theme variables rather than hardcoded light backgrounds. Long labels wrap before the usage metadata; number and name remain readable at 375px and enlarged text sizes.
- Add a compact browse hint near the start of the strip: `⇧J/⇧K fields · 1–9 jump`. In bank, use the section-specific noun. Put explicit Previous/Next actions in All actions as pointer/discovery equivalents; these actions return focus to their destination. Do not make the number a separate nested button inside the field button.

Moving focus must bring its header fully into the card’s scrollport with a small breathing margin. Prefer minimum necessary, immediate scrolling: repeated jumps should not queue smooth animations or pan the document behind the modal. Existing `preventScroll:true` focus restoration makes this an explicit responsibility. `scrollIntoView({block:'nearest'})` describes the desired alignment, but it can scroll multiple ancestors by default; use the known modal scroller or verify container behavior in Obsidian’s Electron version. [MDN: scrollIntoView](https://developer.mozilla.org/en-US/docs/Web/API/Element/scrollIntoView).

Expose an accessible name such as “Claim, field 2 of 3, required, text,” and the digit shortcut where supported. Use actual DOM focus, not only a CSS-selected row. The keycap itself can be hidden from the accessibility tree if its information is already in the label. Avoid redundant live announcements on every step; focus should convey the destination. W3C’s keyboard guidance emphasizes predictable focus, visible focus, and avoiding confusion between focus and selection. [W3C: Developing a Keyboard Interface](https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/).

## Implementation shape

The work belongs in **bob-plugins**, primarily `bob-ledger-tools`, plus documentation. No Rust schema format, CLI option, capture contract, or persisted ordinal is needed.

### Share the navigation calculation, not the entire modal

Add a small pure helper, with card-specific adapters, that accepts:

```text
visible selectable sequence
ordered major-destination IDs
current selected ID
command: next / previous / ordinal(n)
```

It returns a stable destination ID or no movement. Both the badges and key handling consume the same destination list. A returned ID is not an array index used as identity.

Album adapters use `field:<key>` and the **currently displayed projected order**. Bank adapters use current-tab groups/accounts/rules/settings and their existing stable identities; synthetic Ungrouped and Stale after targets need explicit presentation identities. For reordered rules, preserve the arrangement’s session identity, not a newly numbered visible position. Reconcile new reports using the existing guarded refresh boundaries.

On each user-visible change, derive one presentation snapshot. The ordinal is the destination’s one-based position in that snapshot. A rename preserves identity; a reorder preserves selection on the moved item but updates ordinals immediately; add/remove refreshes numbers only when the real destination appears/disappears. An unsaved insertion ghost has no ordinal. Scrolling, narrow widths, choice wrapping, and usage-count updates do not renumber fields.

The verified raw/projected mismatch means the existing fine walk should also consume this shared presentation order when arrangements are shown. This is a justified accompanying correction: a user switching between `j` and `J` must not enter two different orders. Keep this refactor narrow; it does not require rewriting the guarded writer or reorganizing all card components.

### Likely edit sites

| Area | bob-plugins files under `plugins/bob-ledger-tools/` |
| --- | --- |
| New pure jump/projection helper and exports | A small new `src/` fragment, `src/fragments.json`, focused test exports |
| Album target projection | `src/242c-plugin-album-schema-edit.js`, `src/241y-plugin-album-schema-card.js` |
| Album count conflict and mode routing | `src/241yb-plugin-album-schema-arrange.js`; verify outer `src/241ye-plugin-album-schema-place.js` handling |
| Album ordinals, grouping space, hints, focus/reveal | `src/241yc-plugin-album-schema-card-regions.js`, `src/241yd-plugin-album-schema-card-paint.js`, `styles.css` |
| Bank destination adapters and synthetic selectable settings | `src/248i-plugin-bank-setup-card-model.js` |
| Bank shortcut precedence and arrangement projection | `src/248k-plugin-bank-setup-card.js`, `src/248ka-plugin-bank-setup-card-arrange.js` |
| Bank headings, shortcut metadata, hints, focus/reveal | `src/248j-plugin-bank-setup-card-dom.js`, `src/248kb-plugin-bank-setup-card-regions.js`, `styles.css` |

Avoid a large new field wrapper solely to obtain spacing. The album ghost painter currently looks at direct children carrying `data-arrange-id`. Moving headers into wrappers without adapting that code can break insertion and drag behavior. Scoped margins/layout metadata on the existing field row are a safer initial implementation. If wrappers are needed for semantics, update placement/measurement code and tests together.

The plugin repo requires source-fragment edits, generated builds, a maximum 1,000 lines per hand-edited fragment, and `bob plugins sync` after changes. Several relevant fragments already approach that limit; use a small helper instead of growing the core class. An implementation should update bob-cli’s album-card documentation and the bank Setup instructions, explicitly removing the old count-prefix promise. Follow their documentation checks. No deployment was done for this research-only work.

### Verification that will matter

The important tests exercise behavior and side effects, not merely the new predicate:

1. **Exact screenshot fixture:** Status with six choices, Claim text, Section choices. `J` and `2` select/focus Claim; `K` from a Status choice returns to Status; Enter alone starts editing.
2. **Displayed order:** after local field/group/rule reorders, numbered labels, `J/K`, digits, and fine navigation agree. Undo, revert, successful save, and fresh reports preserve valid identity and recompute ordinals together.
3. **Digit migration:** `2` then `Alt+K` jumps to destination two and nudges that selection once. No stale count survives. In bank, a category assigned `2` does not steal the jump; transaction categorization still uses its assigned `2`.
4. **Case/modifiers/layout:** uppercase bank `J/K` navigate, lowercase `j/k` keep their category meanings; Alt+J/K and Alt+Shift+J/K retain arrangement behavior, including macOS `∆/˚` events. Ctrl/Meta combinations do not become field jumps. Shift-produced digits work; `!` stays `!`.
5. **Input ownership:** typing `J`, `K`, and digits into every stage control, contenteditable, Emoji Slot, and IME leaves drafts, caret, and validation intact. Ghosts, Move to… badges, nested pickers, and drag cancellation retain their key handling. Escape/q/Ctrl+[ keep their existing layered dispatch.
6. **Scale/boundaries:** empty/one/three/twelve destinations; invalid ordinals; key repeat; consecutive scalar fields; Add choice/Add field; issues; first/last boundaries; collapsed or missing destinations if introduced later. Scrolling never renumbers.
7. **Bank shape:** Money moves, Ungrouped, Hidden, account rows, Stale after, rules, tab-local numbering, and Checks with no navigation hint. A synthetic heading cannot cause a config mutation.
8. **Focus and scrolling in real Obsidian:** destination DOM focus matches the ring, stays visible inside the correct modal, and cannot trigger a second editor action. Verify light/dark, 375px, long labels, enlarged text, and many offscreen choices. Stub-DOM tests cannot establish these properties.
9. **No write side effects:** jumping triggers no writer, preview, undo entry, arrangement change, or loss of an existing pending draft. When applying, preserve current locking behavior.

Use the existing shell, arrange, placement/drag, bank Setup, and Obsidian album UI harnesses rather than building a separate visual test framework. Run generated-build checks and the repo’s normal required checks before deployment. A live Obsidian acceptance pass is the remaining evidence needed before calling the implementation reliable.

## Critique and alternatives

The proposal is strongest as a modest extension of the current interface. The benefits are immediate and demonstrable; its main costs are shortcut migration, one shared order model, and slightly more vertical space.

- **Only add `J/K`, omit numbers:** lower conflict cost, but requires scanning/jumping repeatedly. It would miss the user’s useful direct-access goal. I would not choose it unless preserving current digit meanings is more important than instant jumps.
- **Keep digits as counts and use a prefix before field numbers:** preserves muscle memory but adds a mode and more key presses. The existing Move to… picker already provides a better destination-based alternative for reordering; retire counts instead.
- **Use Tab for field jumps:** conflicts with form/control navigation and Bank Setup’s existing tab handling. Keep it out of this change.
- **Collapse all choices by default:** reduces scrolling but hides the exact relationships this screen is meant to show and adds expansion state. Consider it only if very large schemas remain difficult after coarse navigation.
- **Add a sidebar or duplicate field index:** consumes width and repeats labels, especially at 375px. Inline ordinals plus spacing are sufficient for the current screenshot.
- **Make number presses open editing immediately:** faster for one action but surprises users who want to inspect, reorder, or toggle the selected field. Focus first; let Enter retain its clear meaning.

The strongest risk is teaching one number while executing another. That can happen through projected-order drift, stale selection, viewport-based numbering, hidden count buffers, or competing bank hotkeys. Treat the shared mapping and explicit conflict resolution as release requirements, not polish.

### Explicit adjustments to the request

- Uppercase `J/K` means coarse movement; existing lowercase behavior stays. Digits select only and do not auto-edit.
- Coarse movement stops at the ends. From a child, `K` reaches its owning header.
- Ordinals follow the complete displayed order, including pending arrangements; `10+` remains numbered but has no single-key shortcut.
- Album bare-digit reorder counts are removed. Bank Setup’s `1`–`9` and uppercase `J/K` category accelerators yield to major-destination navigation; transaction-card key assignments remain intact.
- Bank “fields” are interpreted as the section-local destinations listed above, not numbered tabs. Ungrouped/Stale after gain explicit presentation targets; Checks stays diagnostic.
- Jumps are restricted to focused browse mode. They do not operate inside drafts, active insertion/picker modes, or behind the modal.
- Correct the exposed raw/projected navigation mismatch as part of this work.

## Recommended solution

Implement **focus-only `J/K` structural jumps and `1`–`9` direct selection**, driven by one presentation-order model shared with numbering and fine navigation. In album and record entry points, number schema field headers; in Bank Setup, use the section-local major destinations defined above. Remove album count-prefix ambiguity and give Setup navigation explicit precedence over conflicting category shortcuts. Preserve existing editing, reordering, guarded saves, and undo.

Visually, add small inline ordinal keycaps beside field names, modest extra space before each field block, a compact contextual hint, and reliable reveal of the focused destination. Keep the existing theme and focus language. This delivers the requested speed and a clearer, calmer card without introducing another navigation mode or changing stored data.

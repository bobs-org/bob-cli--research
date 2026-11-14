# Bank transaction walkers: a review queue and a day compass

Independent research by **cdx** · 2026-11-14

## Assessment

This is a good addition. Bank transactions already form an ordered, reviewable collection, and Bob already has a consistent bracket-walker system. Four keys can remove the friction of finding the next transaction without adding another dashboard or changing the bank data model.

The design challenge is the automatic filter: the same lowercase key changes its destination set when the last waiting row is acknowledged. Make that transition visible and deliberate at the next navigation gesture. Keep reviewing, browsing, and acknowledging distinct operations.

My recommendation is a fourth bracket family, **b**, with an automatic waiting-row queue for lowercase movement, an all-transactions day compass for uppercase movement, and a compact footer in the existing shared walker panel. Reuse the existing bank JSON and editor recognizers. Do not create a separate bank plugin or a second accounting index.

This report is independent: I did not locate or read the other researchers’ reports, chats, or summaries. Repository code, current project memory, and the primary web sources below supplied the evidence. The UI examples use fictional amounts and payees; no personal transaction data was inspected.

## What already exists

| Finding | Consequence for this feature |
| --- | --- |
| Bank notes are `bank/YYYY-MM.md`, with dated sections. Their filename is authoritative. Only top-level amount-led checkbox rows under valid day headings are transactions. [S1] | Use the existing grammar; a vault-wide checkbox search is wrong. |
| `[ ]` means waiting; `[x]` and `[X]` mean acknowledged. Rows are explicitly not Tasks-plugin tasks. [S1] | Review membership is one existing field. Do not involve task freshness, `#task`, the morning review queue, or lane state. |
| Typed rows, imported rows, and typed rows later matched by import coexist. Typed rows can lack `^bank-<hex>` IDs. [S1, S2] | A walk restricted to imported IDs would omit legitimate transactions and would needlessly expose provenance. |
| `bob bank list -a -f json` already returns every month, day, row location, identity where available, acknowledgement state, and counts. The Rust model orders rows by `(date, path, line)`. [S2] | No new CLI command or JSON schema is needed for the initial navigation contract. |
| Ledger Tools has a shared bank API v2, JSON decoder, source recognizer, generation-aware cache, coalesced fetches, and subscriptions. [S3] | Extend that service instead of spawning a CLI process on each keypress. |
| Ctrl+Enter on a waiting row opens the Category card; filing ticks and categorizes in one editor undo step. It advances through waiting rows in the same note and wraps locally. Other months are offered at completion. [S4] | There is already a filing flow. Navigation should complement it, not run a competing auto-advance loop. |
| Navigation owns persisted bracket family selection, repeat commands, jump history, and lane/review movement. Its allowed families currently stop at `s/w/n`. [S5] | Register `b` throughout the family contract, not just in four key handlers. |
| Ledger Tools routes one footer panel according to that selected family. A selected family remains visible even when clear or unavailable. [S6] | Add a bank member to the shared panel; do not stack another persistent footer. |
| The plugin documentation says custom bracket bindings live in the vault’s `obsidian_vimrc.md`, separately from palette commands. [S7] | Register commands in source, then wire the actual vault mappings. A plugin build alone does not install these keys. |

Source revisions inspected: bob-cli `11abff0b65b92959c3906df5661597e2530142be`; bob-plugins `6a1778b52c44419b550052c2c36b51bce377d950`. I also checked the linked chezmoi checkout at `cc1f830838de5b88a8ef85b786faad0b908a279f` for the mapping source; those bracket mappings were not present there. The live vault vimrc and installed Obsidian runtime were not inspected, so actual key conflicts and runtime rendering still require verification during implementation.

## Explicit adjustments and clarifications

1. **Reverse the requested lowercase directions.** The prompt literally assigns `[b` to next and `]b` to previous, while assigning uppercase in the conventional direction. Recommend **`[b` previous, `]b` next**. This matches the existing `s`, `w`, and `n` families and makes repeat keys coherent. This is a deliberate correction, not an assumption silently embedded in the design.
2. **Include all valid bank rows, including typed and matched rows.** Import is how most rows arrive, not the user-facing boundary of a transaction. An unchecked typed row should be reviewable too.
3. **Define “needs review” as unchecked only.** A flag, missing category, account gap, stale statement, or balance delta does not put an acknowledged row into this queue. Those are distinct concerns. Space can intentionally file a row without a category. [S1, S4]
4. **Define the uppercase day as the previous/next occupied bank date.** Skip dates with no valid rows, including empty headings and weekends. Cross month and year boundaries without creating files or headings. The date is the row’s note-day, not a freshly interpreted journal timestamp; a typed row matched by import can retain its original date. [S1]
5. **Uppercase uses all rows even while review is waiting.** Lowercase supplies the work queue; uppercase supplies historical orientation. Both land on transaction rows, and uppercase always lands on the destination day’s first row, including an acknowledged row.
6. **Make boundaries explicit.** Recommend cycling at both ends, matching the existing lane and review-group walkers. Show `↻ first day` or `↻ first waiting row` on a wrap. A single day cycles to its first row; a single-row queue stays on that row without adding a duplicate jump-history entry. [S5, S7]
7. **Acknowledgement does not become a new bank-walker answer gesture.** Keep the Category card’s existing month-local advance. A raw checkbox change, bulk acknowledgement, or undo updates membership without independently moving the cursor.

The largest usability tradeoff is item 5: uppercase can land outside the lowercase queue. Make the footer tell the truth about that state rather than inventing a queue rank. Applying the waiting filter to uppercase would be more uniform internally, but would make acknowledged days inaccessible through these day keys whenever any transaction elsewhere waits. That is a worse browsing contract.

## Precise navigation behavior

### The two collections

Use one coherent snapshot to derive:

```text
allRows = valid bank rows sorted by (note-day, canonical path, source line)
waitingRows = allRows where acknowledged == false
rowQueue = waitingRows if nonempty, otherwise allRows
occupiedDays = unique note-days in allRows, ascending
```

Preserve source order within a day. Do not sort transactions by amount, category, account, or payee. Identical purchases remain separate rows; do not deduplicate by their visible text or cents. Accounts and transfers all participate in navigation, even when excluded from a money total.

| Gesture | Destination |
| --- | --- |
| `]b` | Next row in `rowQueue` |
| `[b` | Previous row in `rowQueue` |
| `]B` | First row on the next strictly later occupied day, cycling |
| `[B` | First row on the previous strictly earlier occupied day, cycling |
| `N]b` / `N[b` | N row steps, one final landing |
| `N]B` / `N[B` | N occupied-day steps, one final landing |
| `]]` / `[[` with `b` selected | Lowercase bank movement |
| `]}` / `[{` with `b` selected | Uppercase bank movement |

Counts consume one snapshot and use index arithmetic, rather than issuing N asynchronous opens. A count of one behaves exactly like an uncounted gesture. Consume and clear pending Vim counts before awaiting I/O.

### Where movement starts

Use this order of precedence:

1. A bank row under the current cursor, including that row’s indented child notes.
2. The current bank day and cursor position when on its heading or intervening prose.
3. The last successful bank landing retained in memory for this Obsidian session.
4. With no origin, `]b` enters the first eligible row and `[b` the last; `]B` enters the first occupied day and `[B` the last occupied day, always at the day’s first row.

A real cursor position in another bank note overrides the remembered landing. On a heading, `]b` can enter that day’s first eligible row; `[b` searches strictly before the heading. Uppercase always leaves the current day, even from the middle of it.

When the origin is an acknowledged row excluded from `waitingRows`, find the next/previous waiting row relative to its `(date, path, line)` position. When a remembered row disappears, use its former sort position to find its surviving neighbor. Do not reuse a stale integer rank. If its location cannot be resolved safely, refresh once and explain the refusal.

This follows the lane walker’s cursor/anchor model, rather than copying the review walker’s special “first return to the current task” behavior. Bank browsing has no protected task commitment to return to. Persist only family selection; avoid persisting merchant text or a supposedly permanent row rank. [S5, S7]

### The final acknowledgement

When waiting falls from one to zero:

- Finish the existing Category card transaction and summary normally.
- Keep the cursor where the filing flow leaves it; do not jump into history.
- Change the bank footer to `ALL`, with `0 waiting`. A brief status message can say `No waiting rows · bank keys now browse all`.
- The next fresh bank navigation gesture uses all rows relative to the current location.
- Cancel queued navigation from the old waiting generation; held repeats must not spill into the new all-rows collection.

Undo or a later import can make the waiting queue nonempty again. Update the footer and the next gesture’s membership; never move the cursor solely because a subscription fired. A refresh error is not evidence that waiting reached zero.

### Example

Fictional rows:

| Date | Row | State |
| --- | --- | --- |
| Oct 31 | A | acknowledged |
| Nov 2 | B, C | B acknowledged; C waiting |
| Nov 5 | D | waiting |
| Nov 8 | E | acknowledged |

From C, `]b` reaches D; the next `]b` wraps to C. From C, `[B` reaches A, and `]B` reaches D. From D, `]B` reaches E even though C and D wait. From E, `[b` reaches D; `]b` wraps to C. After C and D are acknowledged, lowercase traversal includes A through E. No November 1, 3, 4, 6, or 7 note or heading is created.

## Footer design: calm, legible, unmistakably bank

Add `b` to the existing selector: `[[ s w n b ]]`. Clicking the letter selects the family without navigating. Only deliberate family commands and selector activation select `b`; opening a bank file, importing, editing, or opening the Category card does not silently replace another walker.

Use the existing panel’s six slots: identity/position, current group, detail, hint, other groups, and meter. The bank mode belongs near the identity and must survive narrowing. The current group is a date; other groups are nearby dates with waiting counts when relevant.

These are text wireframes, not measured or rendered screenshots:

```text
Selected, waiting row
[[ s w n b ]]  🏦 WAITING 3/12 · Nov 12 · $61.20 ShopRite
               Ctrl+Enter file · Nov 13 ×4 · 12 waiting

Historical row reached with an uppercase jump
[[ s w n b ]]  🏦 WAITING —/12 · Nov 10 · Acknowledged
               ]b next waiting · [B ]B days · 12 waiting

No rows awaiting acknowledgement
[[ s w n b ]]  🏦 ALL 38/146 · Nov 12 · $61.20 ShopRite
               [b ]b rows · [B ]B days · 0 waiting

Narrow
[[ s w n b ]]  🏦 WAITING 3/12 · Nov 12

Loading / failed / no collection
[[ s w n b ]]  🏦 Loading bank…
[[ s w n b ]]  🏦 Bank unavailable · retry
[[ s w n b ]]  🏦 No bank rows
```

The two-line drawings explain slots; the delivered desktop status bar should remain one compact line, shedding optional content rather than becoming a second toolbar.

Design rules:

- Waiting uses the existing bank amber vocabulary. All-rows browsing uses neutral ink. Use the bank glyph, explicit `WAITING`/`ALL` text, and an underline or pill shape so mode never depends on hue. Green must not mean “all finances healthy.”
- Keep mode, position, and date longest. Remove distant-day chips first, then detailed hints, then payee/account detail. Expand the full description through the tooltip and accessible label. Use tabular numerals to reduce width jitter.
- Amount and payee describe the current row; include the account label only when useful to disambiguate. Omit these when there is no verified current row. Escape merchant text as text, never HTML.
- `3/12` means position among currently eligible rows, not completion. The meter says `12 waiting`, not `25% done`. Do not reuse the morning review’s daily upkeep budget.
- On an acknowledged row outside the waiting queue, use `—/12` plus an explicit acknowledged/off-queue explanation. If the cursor is outside bank notes, label remembered context as `Last bank row`; do not imply the editor is on it.
- Clicking the main panel performs the same next-row command as `]b`. Keyboard activation has the same effect. Give interactive elements visible focus; keep tooltips supplementary.
- Use a brief, restrained row highlight and scroll enough to expose the row with its day context. Reuse existing centering mechanics rather than introducing an elaborate animation. Honor reduced-motion settings.
- Announce meaningful transitions, errors, and wraps politely, without moving focus to the footer. Do not announce every asynchronous repaint.

These accessibility choices follow W3C’s guidance on [information beyond color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html), [status messages without focus changes](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), and [visible keyboard focus](https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html). They are design criteria here, not a claim that an unimplemented UI has passed accessibility testing.

I would not add another persistent attention dot to `b` in the first release. The existing review-attention dot has a deliberate meaning, and bank badges already surface waiting. Another always-on obligation signal should earn its place through actual use.

## Implementation boundaries and reliability

### Reuse the existing ownership split

| Component | Responsibility |
| --- | --- |
| bob-cli bank model and `list -a -f json` | Canonical saved rows, order, acknowledgement state, and authoritative money/account data |
| Ledger Tools bank service | Shared navigation snapshot, buffer validation, invalidation, and a read-only bank-walk provider |
| Navigation Hotkeys | Four commands, counts, repeat-family integration, origin/anchor state, serialized navigation, leaf reuse, and jump history |
| Ledger Tools walker footer | A pure projection of the bank snapshot and verified navigation context |
| Existing Category card | Its existing category/tick transaction and month-local filing sequence |
| Vault vimrc | Normal-mode bindings to registered commands |

An additive capability such as `api.bank.walk` is a suggested name, not an existing API. It should expose availability, generation, rows/day groups, and a snapshot invalidation signal. Feature-detect the actual members and version them coherently. The navigation and footer consumers must agree on membership; they must not independently reconstruct it from Tasks data or separate ad hoc scans.

Start with one shared all-rows request. Derive waiting membership from that response so day browsing and row browsing have the same generation. Two separate `list` and `list -a` subprocesses can otherwise observe different imports. No new Rust subcommand is justified unless measurements or a missing contract later require one.

### Live edits and stale data

The existing bank source recognizer is deliberately permissive: it can surface a checkbox with an unparsed amount or nonstandard status. Its `acknowledged == false` is therefore **not by itself a valid waiting predicate**. Reuse it with the existing tokenization and explicit row validity checks, and require cross-language fixtures against Rust’s grammar. Empty stubs, missing payees, fenced examples, invalid statuses, and malformed money must not become walk entries. [S3, S8]

Prefer the canonical JSON snapshot for saved membership, but reconcile open bank buffers before choosing a destination:

- Track edited/open bank notes and their editor revisions. Validate current rows against their live text, not an old disk line number.
- A valid buffer overlay may add/remove/change navigation rows and waiting state; it must never synthesize accounting totals. Replace that note’s navigation slice, rather than merging old and new copies of the same row.
- If two open editors disagree about the same note, or an edit is ambiguous, pause the affected operation and refresh; do not guess which amount is authoritative.
- A save/fetch completion from an older generation must not overwrite a newer buffer overlay. Already-acknowledged rows must not reappear while the CLI catches up.
- If faithful overlay parsing cannot be demonstrated, use a verified save-and-refresh boundary before navigation instead. That may save the user’s existing edit; it must not itself change bank fields. Do not ship a permissive overlay merely for speed.

Subscribe only while needed, reuse the existing coalescing/invalidation machinery, and release listeners on unload. The current service watches bank notes and the hub; also audit journal-event invalidation if the new footer consumes journal-derived account status. A pure row walker need not add account-status computation. [S3]

### Identity and landing

An imported ID is preferred identity, not permission to trust an old location. Resolve a unique `^bank-<hex>` in the current bank sources, confirm that it is still a valid row, then obtain its current date and line. Duplicate IDs are an ambiguity, not a tie to break by first match.

For ID-less rows, retain `(path, date, source line, exact source text, revision)` as a guarded snapshot. Re-resolve after edits only when there is a unique defensible match; identical purchases remain distinct. A changed row at the same line is not the original row. If a move or deletion makes identity ambiguous, refresh once and report `Bank rows changed; try again` rather than jumping by a stale line number.

Use the existing opening and jump-history primitives, but do not directly hand bank entries to the task-specific `landOnWalkEntry` resolver: it currently calls `resolveReviewQueueLine` and task destination-settling helpers. Extract a neutral open/position/history operation or give it an explicit bank resolver. [S9]

On success, land at the payee or amount, open folded day context, preserve normal-mode focus, and record exactly one cross-file-aware Ctrl+O/Ctrl+I jump. An unsuccessful open, duplicate target, same-position no-op, or stale retry must not fabricate history. Do not call `bank ensure` during navigation: that command creates headings and files. Likewise, audit any reused open helper that automatically saves buffers; its side effects are not automatically appropriate for a walker. [S4, S9]

### Async and failure states

Use a serialized navigation chain like the lane walker, plus a token for the initiating leaf, editor revision, family, and generation. Revalidate after every asynchronous boundary. A newer explicit navigation or manual context change invalidates an old landing request so that a late process result cannot steal focus.

Coalesce rapid input while loading. Counted commands should produce one final landing, not a backlog of file opens. Reject old queued movements when waiting/all mode changes. Retry a stale snapshot at most once per gesture; repeated failure should explain itself without a loop.

Distinguish cold loading, refreshing last-known data, unavailable provider, schema mismatch, no bank configured, empty collection, and no waiting rows. Retained stale data may paint with an updating marker, but it must not authorize an unverified landing or a false mode transition.

A further boundary matters: `list` currently emits zero `issues` counts, while malformed rows are omitted by the model. Its empty queue is not proof that `bob bank check` is clean. Say `0 waiting` or `No recognized bank rows`, never `Accounts balanced` or `Everything reconciled`; route investigation to the existing check/report surfaces. This feature is transaction navigation, not an audit verdict. [S2]

## Integration checklist for an implementation review

These are the concrete surfaces to review, not an assertion that changes have been made:

- In `bob-navigation-hotkeys/src/490-plugin-lifecycle.js`, register next/previous bank-row and next/previous bank-day commands. Commands are available through the palette as well as Vim; Obsidian officially supports user-assigned command hotkeys. [S10]
- In `546-plugin-bracket-repeat.js`, add `b` normalization and both repeat plans. Preserve count forwarding and keep `n`’s no-uppercase behavior.
- In `547-bracket-mode-indicator.js` and `482-walk-mode-nav-api.js`, add the family, accessible labels, hints, persistence, and API compatibility. There is a literal three-segment DOM reuse check today; replace assumptions about three with family-derived behavior. [S5]
- Add the bank footer route in `122-walker-footer-host.js` and `240-plugin-freshness-status.js`, plus a focused pure bank view model. Update painter panel identity, CSS, snapshots, and click routing as appropriate. The bank footer must work independently of Tasks indexing. [S6]
- Extend the existing bank service and recognizer with the navigation capability; do not copy the parser into the navigation plugin. Update Category-card invalidation/landing notifications only as needed to synchronize the footer. Keep its local auto-advance semantics intact.
- Edit source fragments and their `fragments.json` registrations, then build generated `main.js`; the plugin repository forbids hand-editing generated entrypoints. Its deployment rule requires `bob plugins sync` after implementation changes.
- Add four bindings in the actual configured vault vimrc using the established command mapping pattern. Verify Vim normal mode, counts, uppercase recognition, insert-mode noninterference, and existing user/plugin conflicts. Do not assume the checked chezmoi repository owns these bindings.
- Update bank and plugin documentation, repeat hints, and the walker-family contract. This research did not change durable memory; any later memory update must use the prescribed memory workflow. No Mac Capture changes are required for this Obsidian-only feature.

## Acceptance evidence to demand

| Scenario | Required result |
| --- | --- |
| Waiting rows across two months; acknowledged rows interleaved | Lowercase visits exactly the global waiting set in canonical order |
| No waiting rows, including typed rows with no IDs | Lowercase visits every valid row |
| Missing category, transfer, cash, flagged acknowledged row | Membership still depends only on a valid unchecked box |
| Mid-day uppercase movement; gaps; month/year boundary | Strict neighboring occupied date, first row, all-row scope |
| Uppercase reaches an acknowledged day while another month waits | Truthful off-queue footer; lowercase returns to the waiting set relative to the cursor |
| First use from a non-bank note; remembered origin; manual bank navigation | Deterministic origin precedence and visible destination |
| Last waiting acknowledgement, undo, external import | Membership changes with no unsolicited cursor move; old repeats cannot cross the mode boundary |
| Category card filing and Esc | Existing one-undo/month-local flow preserved; no double advance |
| Folded day, child note, CRLF/BOM, alternate valid headings, fenced examples | Correct row recognition and visible landing |
| ID shifted by inserted text; deleted row; duplicate ID; identical ID-less purchases | Correct identity resolution or an explicit refusal, never an arbitrary row |
| Dirty editor, two differing editors, late CLI result, rapid keys, plugin unload | No rollback to old membership, wrong leaf focus, or leaked callback |
| No hub, empty bank, old plugin API, invalid JSON, timeout | Distinct truthful states; no zero-as-success fallback |
| Counts and `[[`/`]]`/`[{`/`]}` | Same targets as the direct gestures; one landing/history transition |
| Small window, light/dark themes, keyboard focus, screen reader, reduced motion | Readable mode/date, accessible controls, no required color-only cue |
| Navigation from a clean fixture vault | Bank files, journal, and metadata fields remain unchanged |

Use pure model fixtures for order, identity, mode transitions, and counts; integration tests for cross-plugin routing and cache races; real Obsidian coverage for focus, folds, Vim dispatch, history, and footer layout. Test large synthetic histories before adding paging or a disk index. The present shared spawn limit is 32 MiB and 20 seconds; those are failure ceilings, not acceptable interaction targets. Measure warm-key latency and cold-load size, and keep repeated warm movement off subprocesses. [S3]

During this research, six existing suites passed with exit status 0: bracket repeat, bracket mode indicator, bank data, bank source, bank Category-card model, and walker footer. They were run directly with `node --test --test-reporter=dot`. This validates the inspected baseline only. No feature implementation, live-vault test, rendered prototype, or latency benchmark was performed.

## Alternatives and critique

| Approach | Benefit | Why I would or would not choose it |
| --- | --- | --- |
| Always traverse all rows | One invariant collection | Too much friction during import review; fails the main requested benefit |
| Apply automatic waiting filtering to rows and days | Uniform queue grouping | Hides historical days whenever any backlog exists; conflicts with the day-browsing use case |
| Separate permanent review and browse modes | Full browsing despite waiting | Potentially useful later, but adds state and scope controls to a four-key feature; do not introduce an invisible latch |
| Separate bank dashboard or sidebar | Rich sorting and filtering | Duplicates existing month/queue cards and breaks source-note orientation |
| Teach the task walker about bank rows | Reuses task machinery | Wrong domain: bank acknowledgement is not a task lifecycle; it couples unrelated queues |
| New `bob bank walk` CLI | Centralizes a pure selector | Unnecessary initial contract: the list already supplies ordered rows; editor position, buffers, and landing still belong in Obsidian |
| Automatically advance the Category card across every month | Very fast global filing | Changes an established interaction and requires cross-file editing, undo, and cancellation design; separate it from navigation |
| Stop at boundaries instead of wrapping | No temporal discontinuity | A defensible alternative for a general banking app, but weaker consistency with Bob’s existing bracket walkers; explicit wrap feedback is preferable here |

The requested automatic mode does have a real cost: while waiting rows exist, lowercase cannot freely inspect every acknowledged row within a day. Uppercase gets to the desired day, then ordinary editor movement handles its rows. That is an acceptable first-release tradeoff for this keyboard-centric workflow. If regular use shows it is too constraining, add an explicit `Browse all` command and a visible, reversible scope control; do not hide a mode switch behind uppercase keys or make it depend on cursor location.

The feature should remain small in product scope but is not merely four mappings. Most effort belongs in identity-safe navigation, the family contract, and data freshness. Beauty follows from a stable footer hierarchy and predictable movement, not from a new dashboard or decorative completion animation.

## Evidence references

All repository links below identify the exact inspected source revision; they were read from authorized local checkouts, not fetched through GitHub file URLs.

- **S1:** bob-cli [bank contract](https://github.com/bobs-org/bob-cli/blob/11abff0b65b92959c3906df5661597e2530142be/docs/bank.md): files, row grammar, ownership, import matching, list, and review behavior.
- **S2:** bob-cli [model and ordering](https://github.com/bobs-org/bob-cli/blob/11abff0b65b92959c3906df5661597e2530142be/src/native/bank/model.rs), [list JSON](https://github.com/bobs-org/bob-cli/blob/11abff0b65b92959c3906df5661597e2530142be/src/native/bank/list.rs), and [CLI dispatch](https://github.com/bobs-org/bob-cli/blob/11abff0b65b92959c3906df5661597e2530142be/src/native/bank/cli.rs).
- **S3:** bob-plugins Ledger Tools [bank data service](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/241j-plugin-bank-data.js), [JSON decoder](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/241h-plugin-bank-decode.js), and [shared spawn limits](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/236-plugin-stats-data.js).
- **S4:** Ledger Tools [Category-card actions](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/248-plugin-bank-category-card-actions.js), [write guards and next-waiting selection](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/246-plugin-bank-category-card-write.js), and [bank open/ack actions](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/241k-plugin-bank-actions.js).
- **S5:** Navigation [repeat-family plans](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-navigation-hotkeys/src/546-plugin-bracket-repeat.js), [selector](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-navigation-hotkeys/src/547-bracket-mode-indicator.js), [walk-mode API](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-navigation-hotkeys/src/482-walk-mode-nav-api.js), and [lane walk](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-navigation-hotkeys/src/544-plugin-lane-walk.js).
- **S6:** Ledger Tools [footer host](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/122-walker-footer-host.js) and [status routing](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/240-plugin-freshness-status.js); audited project memory `glossary:walker-footer` defines the shared-panel slots and selected-family rule.
- **S7:** [Navigation contract](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/docs/bob-navigation-hotkeys.md), particularly Lane walk, Bracket repeat, and keyboard layers.
- **S8:** Ledger Tools [source recognizer](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/241i-plugin-bank-source.js) and [row tokenizer](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-ledger-tools/src/241o-plugin-bank-marks-model.js).
- **S9:** Navigation [shared task landing](https://github.com/bobs-org/bob-plugins/blob/6a1778b52c44419b550052c2c36b51bce377d950/plugins/bob-navigation-hotkeys/src/541-walk-landing.js).
- **S10:** [Obsidian command hotkeys](https://obsidian.md/help/hotkeys). This supports palette-command discoverability and configurable shortcuts; the multicharacter Vim bindings are established by Bob’s own documented integration, not by this general help page.

## Recommended solution

Implement **bank as the fourth existing walker family**, with `[b` previous and `]b` next through all waiting rows across months, falling back to all valid rows only when waiting is empty. Let `[B` and `]B` visit the first row of the previous/next occupied day across all transactions, with explicit cyclic-wrap feedback.

Give it one restrained, responsive footer that always names `WAITING` or `ALL`, shows an honest position and date, and distinguishes empty from unavailable. Keep the Category card’s current month-local filing flow. Share the existing bank data service, use verified row identities and live-buffer checks, and extend repeats, selector state, history, and actual vault mappings together.

Ship that coherent slice before adding browse overrides, global cross-month automatic filing, or richer finance UI. It meets the request with a small mental model: **lowercase moves through what needs attention; uppercase moves through the calendar; acknowledging remains an explicit act.**

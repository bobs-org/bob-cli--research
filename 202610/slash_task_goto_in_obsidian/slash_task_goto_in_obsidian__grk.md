# Slash-to-open task search in Bob Mac Capture

*Researcher: grk · 2026-10-13 · independent swarm report*

**Verdict.** Yes — add `/` as a first-class **Go to** picker on the capture
panel. Reuse the `:` catalog and card for *search*. Give accept a different
action family: hide the panel, write nothing, open the task's residence note
in Obsidian, and land the cursor on that checkbox. Do **not** treat `/`
accept as `:` accept with a different suffix. Do **not** mint a block ID as
a side effect of jumping. Do **not** depend on Advanced URI.

---

## 1. Recommendation in one page

Bob Mac Capture already has a global hotkey and a polished vault-wide task
card. `/` as the first key of an empty item is a good Go-to gesture: the
same muscle as Slack/Linear/Raycast search, sitting next to `:` (link),
`^` (active), `!` (complete), `&` (depends on), and `+` (parent).

**Do this:**

1. **Grammar in bob-cli first** (`decisions:mac-capture-is-a-thin-client`).
   A whole-item single-token `/query` is an incomplete picker, parallel to
   `:<query>`. `capture-parse` reports `needs: ["task_open"]`.
   `capture-complete` lists the **same** linkable open tasks
   `capture_link_tasks::discover` already builds for `:`. `bob capture`
   refuses the token with a teaching error. Never invent a
   `bob capture open` subcommand (`sase/memory/cli_rules.md`: nothing nests
   under `bob capture`; `capture-*` names grow additively).
2. **Same picker UX as `:`.** One snapshot, local fuzzy filter, grouped
   empty query (queued Pomodoros, In Progress, Next, then per-note),
   spaces as AND, Tab/arrows, Escape → chip, Backspace on empty filter
   removes `/`. Caption **Go to**, scope `/`. The `:` card already uses
   the caption "Open Tasks" for *open (not done) tasks*; `/` must not
   reuse that label.
3. **Accept opens, it does not insert.** Return / Tab / click:
   - resolve Bob's additive `open` payload on the row
     (`target` absolute path, vault-relative `note_path`, 1-based `line`,
     optional `block_id`, stale-safe `ref`)
   - launch Obsidian onto that task
   - clear the `/query` draft and hide the panel
   Shift-Return and Command-Return do **not** mean Link & Start / Link &
   Capture. Consume them as Open (same as Return) or ignore them. There
   is no Add block ID prompt: ID-less rows are jumpable by line + `ref`.
4. **Focus lives in bob-plugins**, reusing the review-walk / task-move
   landing path (`landOnReviewQueueEntry`,
   `jumpOrDeferTaskMoveDestination`). Register
   `obsidian://bob-focus` on `bob-navigation-hotkeys`. Mac Capture already
   builds `obsidian://open?path=` (`ObsidianOpenURL.swift`) and that is
   **file-only** — it cannot land a cursor. Native `#^block` and Advanced
   URI `line=` are fallbacks, not the design.
5. **Residence, not the ledger.** A queued row still opens the area /
   project / inbox note that *holds* the checkbox, never today's daily
   note's Task Link. That matches "open the appropriate area note /
   project note."

**Do not do this:** sniff `/` only in Swift; reuse `task_link` accept and
then open the inserted `@route:id`; force Add block ID before jump; add
the Advanced URI community plugin; treat `/tmp/foo`-shaped prose as a
special case in v1 (it becomes a query, same as `:dee` already does);
make `/` a general command palette (`/refs`, `/settings`).

---

## 2. Is this a good idea?

**Yes, with the accept-family split in §5.** The capture panel is already
the "task verb from anywhere" surface. Bryan is one global hotkey away
from a ranked, grouped catalog that Obsidian's Quick Switcher (notes, not
tasks) and the in-vault `]s` walk (review order, not search) do not
provide. Putting Go-to on the same card as link/complete/depend is
coherent, and `/` is the right mnemonic.

The stated plan is **underspecified on the hard part** — focusing a
checkbox from outside Obsidian — and **over-copies `:`** on accept
(Shift-Return, Command-Return, Add block ID). Those `:` keys exist
because accept *writes a capture token*. `/` writes nothing.

Costs that are real and acceptable:

- One more incomplete sigil in a grammar that already has `^ : ! & +`.
- A sole-item Unix path (`/tmp/foo`) stops being capturable prose, the
  same class of claim `:` already made for `:dee`.
- Focus quality depends on a plugin handler plus a native file-open
  fallback. Cold-start Obsidian will open the file; cursor landing may
  wait for plugins.
- `task_link` snapshots are already "hundreds of KiB"
  (`BobProcessClient.swift`). `/` reuses that scan; it does not add a
  second vault walk.

The idle-agenda decision already named this class of work: it **reopens
when** the empty panel needs to "navigate by keyboard." `/` in the editor
does not by itself make agenda rows clickable, so it need not reopen that
record. A later "click a Now row to jump" would.

---

## 3. Critique of the stated plan

The request:

> Press `/` as the first key in the input box to trigger a new Obsidian
> task search. This should work just like when the `:` key is pressed as
> far as task selection goes. When a task is selected, open the
> appropriate area note / project note and focus the target task.

### 3.1 What to keep

- **First-key `/` on an empty item** as the trigger. Implement it as the
  same whole-item rule `:` already uses (one physical line, one
  whitespace-delimited token starting with the sigil). That *is* "first
  key in the input box" for a fresh panel, and it also makes a
  blank-line `/query` item in a batch draft work. Multi-token
  (`search /foo`) and mid-line (`Buy /milk`) stay prose.
- **The `:` card for selection.** Snapshot from bob, local fuzzy matcher,
  grouped empty query, filter seeded by text typed before the card
  appears, reopen chip, stale-draft guard. Copying that state machine is
  cheaper and more consistent than a second widget.
- **Residence note.** Open `cash.md` / `sase_deep-fix.md` / `mac_inbox.md`,
  the file whose checkbox line is the task. Inbox files are area notes
  (`glossary:inbox-file`); include them. Terminal projects, reference
  notes, daily `^gtd`, and untyped root files stay out, because they are
  already out of `capture-targets` / `task_link`.

### 3.2 What to change

**A1. Accept is a different verb.** `:` Return inserts `@route:block-id`
and returns to the editor; Shift-Return appends `=`; Command-Return
inserts and captures; ID-less rows open Add block ID then
`capture-task-id`. None of that belongs on `/`. Mapping those keys onto
Go-to would mint IDs and write the vault in order to *look at* a task.

**A2. ID-less rows stay jumpable.** The `:` catalog always includes
tasks with no `^id` (`--all-tasks` does not affect `task_link`). For
link, an ID is required to spell `@route:id`. For jump, the 1-based
`line` plus stale-safe `ref` (`LINE:8-hex-digest` of the physical line,
`note_tasks.rs`) are enough. Forcing a name in order to visit the row
would surprise, and it would mutate the note.

**A3. Focus is a plugin problem.** Mac Capture's current Obsidian open
path (`ObsidianOpenURL.url(forAbsolutePath:)`, used after Command-Return
capture and from the Refs panel) is:

```
obsidian://open?path=<percent-encoded absolute path>
```

Official Obsidian URI can target a heading or block only through the
`file` parameter (`Note%23%5EBlock`), and the `path` parameter does not
carry a hash. Advanced URI (`obsidian://adv-uri?filepath=…&block=…&line=…`)
can land a line, and it is a third-party community plugin Bob does not
ship or mention in `docs/plugins.md`. Bob already lands a cursor on a
task from inside Obsidian: `]s` /
`landOnReviewQueueEntry` opens with leaf reuse, re-resolves the line
against current file text, `setCursor`, and centers. `/` should call
that, via a tiny protocol handler, rather than hoping a URL fragment
places the caret on the checkbox.

**A4. `/` is not a capture.** Putting the trigger in the capture *editor*
is right (global hotkey, one card). Putting the *effect* in
`bob capture` execution is wrong. Follow `:` / `!` / `&` queries: parse
as incomplete, complete as a catalog, execute as a teaching error.

**A5. Caption collision.** The `:` source already captions itself
"Open Tasks" (`CapturePickerSource.scopeCaption`). `/` should read
**Go to** (or "Jump") so "open" does not mean two things on one panel.

**A6. Do not Swift-sniff the first keystroke.** A Mac-only interceptor
that synthesizes a `:` complete call would ship faster and would violate
`BlockIDRules.swift` / the thin-client record: Bob is the only authority
for the grammar. Future clients (Raycast, a Shortcut) would not see `/`.
An older `bob` that does not know `/` would capture `/fix` as an inbox
task — the same additive-compat story as every previous picker, and
acceptable.

### 3.3 Would I take a different approach?

I would still put this on Mac Capture. I would still use `/`. I would
**not** implement "exactly like `:` except open the file." I would also
**not** start with a general slash command palette.

A reasonable alternative I considered and rejected for v1: **keep `:`
only, add ⌘O / ⌥↩ on that card to jump.** That avoids a sigil, and it
is a good *follow-up* so a search you started as a link can jump
instead. It fails the request as stated (first-key `/`), and it hides
Go-to behind a modifier on a verb that means link.

A second alternative: **Advanced URI only, no plugin work.** Faster, and
it cannot reuse leaf-reuse, Vim jump history, or `ref` re-resolution.
ID-less rows become `line=N`, which is racy. I would not take a
third-party plugin as the focus authority when bob-navigation-hotkeys
already owns "land on this task."

---

## 4. How `:` works today (the thing `/` should copy)

End-to-end, one authority:

| Layer | `:` behavior | Evidence |
| --- | --- | --- |
| Claim | One line, one token, starts with `:` | `task_link_query_token` in `src/native/capture_language/tokens.rs` |
| Editor | `incomplete`, `needs: ["task_link"]`, placeholder span over the whole token | `parse_editor_task_link_item` in `editor_parse.rs`; `docs/capture.md` § `:<query>` |
| Complete | Context `task_link`; replacement covers the sigil; query is text after `:` | `task_link_candidates` in `capture_complete/candidates.rs`; `docs/capture.md` ~L4414 |
| Catalog | Ready / Blocked / Next / In Progress in `capture-targets` (inbox, areas, non-terminal projects). Nested, ref, daily, terminal projects excluded | `capture_link_tasks.rs`; `capture_targets.rs` ("top-level markdown files") |
| Rank / groups | Empty: queued (ledger order), In Progress, Next, per-note. Nonempty: one fuzzy list | Same scanner; Mac `TaskLinkPickerPresentation.swift` |
| Execute | Never captures. T1/T2 teaching errors | `task_link_picker_error` in `markers.rs`; `docs/capture.md` L980–1017 |
| Mac card | Source `.taskLink`, trigger byte `:`, local `FuzzyQuery(..., leadingSigil: ":")` | `CapturePickerSource`, `CapturePanelModel` |
| Accept | Insert Bob's `@route:id` (or Add ID). Shift-Return `=`. Cmd-Return capture | Mac README "Task Link Picker"; `acceptPickerRow` |

Candidate JSON already carries enough *identity* for a jump, with one
gap:

- `route`, `note_kind`, `block_id`, `requires_block_id`, `line` (1-based),
  `ref`, `text`, `section`, `group`, `pomodoro`
- **No** `note_path` and **no** absolute `target` on `task_link` rows
  (`TaskLinkCandidate` in `capture_complete/model.rs`). `&` and `!` rows
  already send `note_path`. Capture-targets are vault-root files, so
  `{route}.md` is the relative path today — still send an explicit path
  so Swift never joins `BOB_DIR` itself.

Mac already opens Obsidian after a successful Command-Return capture
(`uniqueTargetURLs` → `targetOpener` → `ObsidianOpenURL`), file-only,
deduped, and only for notes the capture actually wrote. `/` needs the
same opener plus a focus step those URLs cannot do.

---

## 5. Requirement adjustments (explicit)

These change the request. Each is justified.

| ID | Adjustment | Why |
| --- | --- | --- |
| **A1** | Whole-item `/query`, same claim shape as `:`, not a Swift-only "first key of the whole box" special case | Thin client; batch drafts; `Buy /milk` stays prose |
| **A2** | Accept = Go to + hide + clear draft. No insert, no `bob capture`, no Add block ID | Different verb; ID-less rows are still visitable |
| **A3** | Shift-Return / Command-Return are not Link & Start / Link & Capture | Those keys exist to write a token |
| **A4** | Caption **Go to**, scope `/`. Do not reuse "Open Tasks" | `:` already owns that caption |
| **A5** | Catalog = `:` catalog, including **inbox** area notes. Daily `^gtd` and `^ref` stay out of v1 | User said area/project; inbox is an area; `capture-targets` is the existing set |
| **A6** | Jump to the **residence** note even when the row is grouped under a Pomodoro | "Area / project note," not the daily Task Link |
| **A7** | Focus via `obsidian://bob-focus` in bob-navigation-hotkeys, with native `obsidian://open?path=` as the file-open insurance | File-only URI is what Mac has; review-walk landing is what "focus the task" means in this vault |
| **A8** | A sole-item token that looks like a Unix path (`/tmp/foo`) is a Go-to query in v1 | Same claim rule as `:`; teach `see /tmp/foo` for prose |
| **A9** | v1 lists **open** tasks only. Closed / archived search is a follow-up | Reuse one scanner; `done/` is a different corpus |
| **A10** | `/` is Go-to only, not a slash command palette | Keep the grammar small |

Follow-ups I would file, not build in v1:

- ⌘O on the `:` / `^` / `!` cards to jump without changing mode.
- Optional closed-task corpus (or a filter chip).
- Agenda-row click / `⌘1…9` jump (reopens
  `decisions:idle-capture-shows-ledger-agenda`).

---

## 6. Options for the trigger and the data

### O1. New `task_open` need + complete context (recommended)

`/query` claimed like `:`. Parse `needs: ["task_open"]`. Complete context
`task_open` (or `task_search`) whose candidate list is
`capture_link_tasks::rank(discover())` with an additive `open` object per
row:

```json
"open": {
  "target": "/Users/bryan/bob/cash.md",
  "note_path": "cash.md",
  "line": 42,
  "block_id": "goog-exit",
  "ref": "42:a1b2c3d4"
}
```

`block_id` omitted when ID-less. `replacement` can be empty: the client
must not insert it. `picker` descriptor:
`kind: task_open`, `scope_token: "/"`, ranges covering the token.

**Why this wins.** Additive JSON, one scanner, Swift decodes with
`decodeIfPresent`, older bob ignores `/` as prose, docs/capture.md stays
the contract, every future client gets Go-to for free.

### O2. Reuse `task_link` context, Mac branches on the typed byte

Complete `:` even when the draft is `/`. Swift sees trigger `/` and
opens instead of inserting.

**Reject.** The client decides syntax. `capture-parse` would still see
`/fix` as an inbox task (or unknown prose) unless the claim exists
anyway. Once the claim exists, a distinct need is cheaper than a hidden
alias.

### O3. Mac-only first-key interceptor, synthetic `:` complete

Empty draft, first character `/`, open `.taskLink` against
`capture-complete -- ':'`.

**Reject as the design.** Fast prototype, breaks thin-client, no teaching
error, `/fix` captures as inbox on CLI, Raycast never gets it. Acceptable
only as a spike to feel the card.

### O4. `bob task open` / `bob open-task` CLI instead of capture protocol

Read-only, so it must not live under `bob task` (that noun rewrites task
lines). A top-level verb is extra surface for a gesture that is
inherently interactive. Test through `capture-parse` / `capture-complete`.
Skip a new verb in v1.

### O5. Modifier on `:` only (⌘O)

Good follow-up. Fails "press `/` as the first key."

---

## 7. Options for focusing the task in Obsidian

This is the part the request treats as easy and the codebase says is not.

### F1. Native `obsidian://open?path=` (what Mac does today)

Opens the file, reuses whatever tab Obsidian chooses, leaves the cursor
wherever it was. **Insufficient** for "focus the target task." Keep it as
insurance so a missing plugin still opens the note.

### F2. Native `obsidian://open?vault=…&file=cash.md%23%5Eblockid`

Documented for headings and blocks. Requires a vault name Mac Capture
does not currently store (it uses absolute `path` so it never
reconstructs vault-relative links — comment in `ObsidianOpenURL.swift`).
Does nothing for ID-less rows. Community reports that the caret often
scrolls near the block rather than sitting on the checkbox. **Useful
fallback for identified tasks**, not the primary lander.

### F3. Advanced URI `obsidian://adv-uri?filepath=…&block=…&line=…`

Supports line and block. Requires a community plugin Bob does not
control. Line numbers race. **Do not take as a dependency.**

### F4. Custom `obsidian://bob-focus` on bob-navigation-hotkeys (recommended)

`registerObsidianProtocolHandler("bob-focus", …)` with query params
mirroring Bob's `open` object: `path` (vault-relative), `line`,
`block`, `ref`. Handler:

1. Resolve the file (`vault.getAbstractFileByPath`).
2. `openMarkdownFileWithLeafReuse` (already used by review jump and
   child-note open — activate an existing leaf, else
   `getLeaf(false).openFile`).
3. Re-resolve the line like `landOnReviewQueueEntry`: prefer `^block_id`
   on an open `#task` line; else match `ref` digest; else line + text.
   If the file changed, refuse with a Notice rather than landing on the
   wrong checkbox.
4. `setCursor({line, ch: 0})` and `scheduleOpenTaskJumpCenter` (same
   helpers as Ctrl+Shift+J/K and `]s`).
5. Record a Vim jump when a context exists, matching task-move follow.

Mac sequence on accept:

1. `NSWorkspace` open native `obsidian://open?path=<absolute>` (file
   insurance, works if Obsidian was quit).
2. `NSWorkspace` open `obsidian://bob-focus?…` (cursor). If the plugin
   is disabled, step 1 still happened.
3. Clear draft, `panelDismisser()`.

Two URIs can race on a cold start (Obsidian launches, plugins load,
handler runs late). That is the same class of race every custom
Obsidian URI has. Leaf-reuse + retries already exist in
`jumpOrDeferTaskMoveDestination` (`TASK_MOVE_DESTINATION_JUMP_RETRIES`).
Use them.

### F5. `app.workspace.openLinkText("cash.md#^id")` only, no protocol

That API is the right *in-app* primitive for identified tasks. It still
needs a protocol (or some other IPC) to be invoked from Mac Capture.
The handler in F4 should call `openLinkText` for identified rows and
the line-resolve path for ID-less rows.

---

## 8. Recommended solution (concrete)

### 8.1 bob-cli (source of truth)

**Claim** (`tokens.rs`), shared by execution, editor, completion:

- One physical line, one whitespace-delimited token, `starts_with('/')`.
- Token includes the sigil. Query is the bytes after `/` up to the
  cursor, same as `:`.

**Do not claim:** second byte `/` if we ever need `//` comments (we do
not today); `![` style carve-outs are unnecessary (`/` has no embed
twin). Optional later: treat `//` as prose. Skip in v1.

**Editor parse:** `incomplete`, `needs: ["task_open"]`, empty body,
`interactive_placeholder` over the token, no diagnostics, `@@` does not
apply. Precedence in Mac `pickerNeed(from:)`: sit with the other
whole-item pickers; after `task_link` is fine.

**Complete:** context `task_open`, replacement = whole token, candidates
from `capture_link_tasks` with additive `open`. Empty `replacement` on
every row so a confused client cannot insert a Go-to as a link.
`picker` descriptor like `task_complete`.

**Execute:** refuse before other item parsers, whole batch rolls back.

T1: `` `/dee` opens the Go-to picker; pick a task to open it in Obsidian, or write a normal capture ``

T2 (query parses as `route:block-id`): `` `/sase:deep-fix` opens the Go-to picker; to link that task, write `@sase:deep-fix` ``

**Docs:** `docs/capture.md` table row next to `:<query>`; a short "Go to"
subsection cloned from the `:` subsection with accept/execute swapped;
complete-contract paragraph next to the `task_link` one. Goldens for
parse spans, complete JSON, and the two teaching errors.

**Compat:** additive fields, `decodeIfPresent` on the Mac side. An older
app against a new bob still *shows* the picker if it learns `task_open`;
an older bob against a new app treats `/dee` as inbox prose until bob
is updated. Document the bob version the same way `:` / `&` / `!` did.

### 8.2 bob-plugins

New mixin on `bob-navigation-hotkeys` (it already owns open-task jump,
review landing, leaf reuse, Vim jump). Register `bob-focus`. Keep the
handler tiny and notice-only on failure. Tests: resolve by block id,
by `ref` after a line shift, refuse on digest mismatch, leaf reuse
when the note is already open.

No `bob plugins sync` from this research turn; that is implementation.

### 8.3 bob-mac-capture

- `CapturePickerSource.taskOpen`: trigger `/`, caption "Go to",
  placeholders "Search tasks by text, note, or ^id", chip "Go to a
  task".
- Presentation: clone `TaskLinkPickerIndex` with `leadingSigil: "/"`.
  Detail strip: `↩ opens cash.md` / `↩ opens cash.md · ID-less, lands
  on line 42`. No schedule pull-forward warning (nothing is linked).
  No "Add ID & Link" buttons.
- `acceptPickerRow`: if source is `.taskOpen`, build URLs from
  `row.open` / candidate fields, `targetOpener`, clear draft, hide
  panel. Stale-draft guard unchanged.
- Parse `needs` mapping and complete routing next to `task_link`.
- Keys: Return/Tab/click Go to; Escape/Backspace as `:`; Shift-Return
  and Command-Return = Go to (simplest) or consumed no-ops. Pick one
  in the plan and test it; I recommend **both mean Go to** so muscle
  memory from `:` Return still "confirms the row."
- Tests: decoding `open`, first-key `/` opens the card, accept does
  not mutate the vault (no process client capture call), opener
  receives path then bob-focus URL, ID-less accept still opens,
  prose `Buy /milk` does not.

### 8.4 Suggested phase cut

1. **bob-cli:** claim, parse, complete, execute errors, docs, goldens.
2. **bob-plugins:** `bob-focus` handler + landing tests (can overlap
   late phase 1).
3. **bob-mac-capture:** source, routing, accept, keys, README. Gated
   on macOS CI as usual.

---

## 9. Risks

- **Cold-start cursor.** Obsidian launches from `obsidian://open?path=`;
  the custom action may run before plugins register. Mitigation: native
  file open first; handler retries like task-move; identified-task
  native `#^block` as a third optional URL if vault name is added to
  settings later.
- **Stale line.** User types `/`, waits, vault changes. `ref` digest
  must win over raw `line`. Show a Notice and still open the file.
- **Sigil grammar growth.** Five whole-item pickers already (`^ : + &
  !`). A sixth is justified because the verb is new. A seventh
  (`/closed`, `?`) is not — use chips on this card.
- **Unix-path prose.** Document in the teaching error. If it hurts,
  a later carve-out can leave tokens containing a second `/` as prose
  (`/tmp/foo` stays a path, `/bank` stays Go-to). I would wait for
  evidence.
- **Inbox vs "area / project."** Including `mac_inbox.md` matches the
  `:` catalog and the glossary. If Bryan wants inbox excluded, that is
  a one-line filter on `note_kind != inbox` — do not fork discovery.
- **Panel vs Obsidian focus.** Hiding the capture panel then opening
  Obsidian is the right z-order. If Obsidian is on another Space, macOS
  will switch; that is the same as today's Command-Return open.

---

## 10. What "good" looks like in the product

1. Global hotkey, empty panel (agenda visible).
2. Type `/`. Agenda yields to the Go-to card; status
   "Pick a task to open — press Tab to browse."
3. Type `bank`. One ranked list, same weights as `:` (text 100%,
   `route:id` 90%, …).
4. Return. Panel vanishes. Obsidian shows `cash.md` with the caret on
   the matching `#task` line, centered, existing leaf reused.
5. Escape from the card restores the `/` (or `/bank`) and the reopen
   chip. Backspace on an empty filter deletes the `/` and returns to
   the empty/agenda editor.
6. `bob capture -- '/bank'` prints a teaching error and writes nothing.

---

## 11. Sources

In-repo (primary):

- `decisions:mac-capture-is-a-thin-client`
- `decisions:idle-capture-shows-ledger-agenda` (reopen clause on
  navigation)
- `sase/memory/cli_rules.md` (no subcommands under `bob capture`)
- `docs/capture.md` (`:<query>`, complete contract ~L4414)
- `src/native/capture_language/tokens.rs` (`task_link_query_token`)
- `src/native/capture_link_tasks.rs` (catalog)
- `src/native/capture_complete/model.rs` (`TaskLinkCandidate` vs
  `note_path` on `&` / `!`)
- `src/native/note_tasks.rs` (`TaskRef` = `LINE:digest`)
- `sase/repos/linked/bob-mac-capture/Sources/CaptureCore/ObsidianOpenURL.swift`
- `sase/repos/linked/bob-mac-capture/Sources/CaptureCore/TaskLinkPickerPresentation.swift`
- `sase/repos/linked/bob-mac-capture/Sources/CaptureCore/CapturePickerPresentation.swift`
- `sase/repos/linked/bob-mac-capture/Sources/BobMacCapture/CapturePanelModel.swift`
  (`acceptPickerRow`, `uniqueTargetURLs`)
- `sase/repos/linked/bob-mac-capture/README.md` (Task Link Picker)
- `sase/repos/linked/bob-plugins/plugins/bob-navigation-hotkeys/src/536-plugin-review-advance.js`
  (`landOnReviewQueueEntry`)
- `sase/repos/linked/bob-plugins/plugins/bob-navigation-hotkeys/src/650-plugin-move-commit.js`
  (`jumpOrDeferTaskMoveDestination`)
- `sase/repos/linked/bob-plugins/plugins/bob-navigation-hotkeys/src/170-open-task-jump.js`

External (focus mechanisms only):

- [Obsidian URI — Open note](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)
  (`path` vs `file`, `#` heading/block encoding)
- [Advanced URI navigation](https://vinzent03.github.io/obsidian-advanced-uri/actions/navigation)
  (`block`, `line`; rejected as a dependency)

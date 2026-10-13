# `/` task search in Bob Mac Capture: open the task in Obsidian

> **Research query (paraphrased):** In bob-mac-capture, make `/` typed as the first key
> in the input box start an Obsidian task search. Task selection should work like the `:`
> picker. Picking a task should open its area or project note in Obsidian and focus that
> task. Help decide how to build it, critique the plan, propose justified requirement
> changes, and end with a recommended solution.

Researcher: **cld** · 2026-10-13 · Repos read: bob-cli (this workspace), bob-mac-capture
and bob-plugins (linked checkouts), plus live read-only `bob` probes against `~/bob` on
athena.

## Bottom line

- **Build it. It is a good idea and cheap to do well.** About 80% of the work already
  exists:
  - the `:` picker card, its index, and its lifecycle in the Mac app;
  - the `task_link` discovery and ranking in bob;
  - a stale-safe "open this note and put the cursor on this task line" routine in
    bob-navigation-hotkeys. The `]s` review walk and Ctrl+Shift+M already use it.

  What is missing is the link between them: a way for the Mac app to tell Obsidian
  *which line* to land on.
- **Obsidian cannot do this natively, so add a small protocol handler to bob-plugins.**
  The core `obsidian://open` URI has no line parameter. It can target `#^block-id`, but
  **307 of the 464 tasks (66%)** the `:` picker lists today have no block ID. Advanced
  URI is not installed in the vault and does not know Bob's task semantics. Recommended:
  `obsidian://bob-open-task?path=…&line=…&text=…[&block=…]`, registered by
  bob-navigation-hotkeys and implemented on top of its existing landing helpers.
- **Make `/` a bob-owned grammar token, like `:`, not a Swift-only key trick.** This
  follows the accepted rule that Bob Mac Capture is a thin client of bob
  (`decisions:mac-capture-is-a-thin-client`). It lets the Mac app reuse the picker
  lifecycle unchanged: the chip, Escape and Backspace behaviour, refetch, and the "calm
  status instead of red errors" handling. It also guarantees that `bob capture` never
  files a stray `/query` task. Name the new context **`task_open`**, after what
  accepting a row does, as `task_link`, `task_complete` and `task_parent` are.
- **Requirement adjustments** (details in [§5](#5-requirement-adjustments-called-out)):
  1. `/` triggers only as the whole draft, not per item.
  2. ID-less tasks open directly. There is no Add block ID step, and opening never
     writes to the vault.
  3. Accepting a row opens the task, hides the panel and discards the `/query` draft.
     ⌘↩ opens the task in a new Obsidian tab instead of capturing.
  4. "Focus" is defined precisely, including stale-line handling and `<C-o>` back.
  5. A pasted path or a draft containing a second `/` stays ordinary prose.

## 1. What exists today

### 1.1 How `:` works end to end

1. **bob's grammar claims the token.** A single-token, single-line item that starts
   with `:` is a picker query. `task_link_query_token` is in
   `src/native/capture_language/tokens.rs:194`. `capture-parse` reports mode
   `incomplete`, needs `task_link`, and one `interactive_placeholder` span.
   `bob capture` refuses the item with a teaching error before any other item parser
   runs (`src/native/capture_language/item.rs:425-434`).
2. **bob supplies the rows.** `capture-complete` returns context `task_link`. Its
   candidates come from `capture_link_tasks::discover` + `rank`
   (`src/native/capture_complete/candidates.rs:436-479`, `TaskLinkCandidate` at
   `src/native/capture_complete/model.rs:146`). The scope is open tasks
   (Ready ` `, Blocked `?`, Next `*`, In Progress `/`) in routable inbox, area and
   non-terminal project notes.
3. **The app presents them.** In bob-mac-capture, `handleTaskLinkCompletion`
   (`Sources/BobMacCapture/CapturePanelModel.swift:2478`) opens the shared picker card
   with source `.taskLink`. Its trigger byte `:` is defined in
   `Sources/CaptureCore/CapturePickerPresentation.swift:101`. `TaskLinkPickerIndex`
   (`Sources/CaptureCore/TaskLinkPickerPresentation.swift`) groups the rows: queued
   Pomodoros, then In Progress, then Next, then one section per note. It filters
   locally and keys rows by `route|ref`, not by `replacement`, because ID-less rows
   have an empty replacement. `pickerNeed` (`CapturePanelModel.swift:3939`) turns
   `needs: task_link` into the calm "Pick any open task — press Tab to browse" line.
4. **Accepting splices bob's `@route:block-id` into the draft.** ID-less rows first
   detour through Add block ID (`bob capture-task-id`), which **writes to the vault**.

### 1.2 What a `:` candidate carries, and what it lacks

Live probe on athena: `bob capture-complete -c 1 -f json -- ':'` took about 22 ms wall
time and returned 464 rows. 390 are in project notes, 73 in area notes, 1 in an inbox.
Each row carries `ref` (`"26:09409c3c"`, a 1-based line plus an 8-hex digest of the
physical line), `route`, `note_kind`, `block_id`, `text`, `section`, `depth`, `line`,
`group`, `pomodoro`, `scheduled`, and the status fields.

- **It has no file path.** The `!` (`task_complete`) and `&` (`task_dependency`)
  candidates already carry `note_path`, the exact vault-relative path. So adding a path
  to a new context follows an existing pattern.
- **307 of 464 rows (66%) have `block_id: null`.** Any design that needs a block ID to
  navigate either fails for two thirds of tasks or writes to the vault just to look at a
  task.

### 1.3 How the app opens Obsidian today

`Sources/CaptureCore/ObsidianOpenURL.swift` builds `obsidian://open?path=<absolute
path>` from bob's absolute `target` path. Its comment states the existing contract:
"bob never returns an Obsidian URI, only the absolute filesystem `target` path".
Command-Return after a capture uses it through `targetOpener`
(`CapturePanelModel.swift:232`), and so does Bob Refs `openNote`. Both open the *file*;
neither can place a cursor.

### 1.4 What Obsidian can and cannot target

- **Core `open` URI.** Parameters are `vault`, `file`, `path` (an absolute path that
  overrides `vault`/`file` and picks "the most specific vault" containing it),
  `paneType` (`tab`/`split`/`window`), `prepend` and `append`. Headings and blocks are
  addressed inside `file` (`Note%23%5EBlock`). **There is no line or column
  parameter.**
- **Advanced URI** (third-party) supports `line`/`column`, `block`, `heading` and
  `openmode`. It is **not installed**: `~/bob/.obsidian/community-plugins.json` lists
  dataview, tasks, templater, the bob-* plugins, vimrc and others, but not
  `obsidian-advanced-uri`. It also knows nothing about Bob's tasks, stale lines, leaf
  reuse, or vim jump history.
- **Plugin actions.** `Plugin.registerObsidianProtocolHandler(action, handler)` maps
  `obsidian://<action>?k=v` to `handler({action, k: v})`. Built-in names such as
  `open` and `new` cannot be reused. No bob plugin registers one today (I grepped all
  `src/` fragments).
- **Cold start.** Forum reports say the core `open` works on macOS when Obsidian is
  closed. I found nothing official on whether a plugin action delivered during launch
  reaches a handler that is not registered yet. **This is a risk to test** (see §6.6).

### 1.5 What bob-plugins already has for landing on a task

bob-navigation-hotkeys already does the hard part:

| Helper | Where | What it does |
| --- | --- | --- |
| `openMarkdownFileWithLeafReuse` | `src/480-review-jump-and-nav-api.js:862` | Activate the leaf already showing the note, else open it in the current leaf |
| `resolveTaskMoveDestinationLine(content, {line, text, blockId})` | `src/250-task-move.js:398` | Stale-safe line resolution: exact line+text, then block ID, then exact text, then clamp |
| `focusTaskMoveDestination(file, anchor, vimJumpContext)` | `src/650-plugin-move-commit.js:505` | Open, then land with retries until the editor renders, then record a Vim jump |
| `jumpToActiveTaskMoveDestination` / `scheduleOpenTaskJumpCenter` | `650-…:786`, `src/170-open-task-jump.js:780` | Set the cursor and centre the line (CM6, with a fallback) |
| `landOnReviewQueueEntry` | `src/536-plugin-review-advance.js:661` | The same pattern for the `]s` walk, with `<C-o>` history |

Tests already exist for this area, for example
`scripts/test-navigation-hotkeys-open-task-jump.cjs` and
`scripts/test-navigation-jump-history.cjs`. A protocol handler is therefore around 60
lines of glue plus one small resolver.

### 1.6 Is `/` free?

Yes.
- `bob capture-parse -- '/'` returns mode `task` with no needs and no spans.
- `capture-complete` returns context `null`.
- `docs/capture.md`'s marker table has no leading `/`.
- The app's README binds `/` to nothing.

Today a draft of `/foo` would simply become an inbox task named `/foo`.

## 2. Critique: is this a good idea?

**Yes.** It turns the global capture hotkey into a "go to task" from any app, using a
picker Bryan already knows. Some reasons it fits well:

- **`/` is the universal "search" key**: vim, less, Slack, GitHub, YouTube. It sits
  next to the other leading sigils the panel already teaches (`:`, `^`, `!`, `&`, `+`).
- **The picker is the expensive part, and it already exists.** It has grouping by
  today's Pomodoros, In Progress, Next and note, AND-term filtering, a pinned detail
  strip, VoiceOver support, and Increase Contrast handling.
- **Opening is read-only.** This sidesteps every lane, freshness and ledger rule in the
  decisions web. Nothing can be filed, linked, stamped or unblocked by accident.

**Concerns, and how the recommendation handles them:**

1. **Hidden cost: three repos, not one.** The Mac app cannot place an Obsidian cursor
   alone, and the thin-client rule says the grammar lives in bob. The real scope is
   bob-cli (grammar + completion context), bob-plugins (protocol handler) and
   bob-mac-capture (picker source + open action). All three pieces are small, but the
   rollout has an order (§6.7).
2. **The panel becomes a navigator as well as a capture tool.** This is mild
   mode-mixing. The `:`/`!` pickers already blur that line, and Bob Refs set the
   precedent of "a quick-open lives in this app". A distinct scope token, caption and
   action line ("Opens in Obsidian") keep the outcome obvious.
3. **`/` versus `:` confusion.** The two pickers look alike, but accepting does
   different things: `:` edits the draft, `/` leaves the app. The visible scope token
   and detail line make this clear. Muscle-memory slips are cheap: a wrong `/` only
   opens a note.
4. **Collisions with text that legitimately starts with `/`.** Examples are pasted
   paths (`/Users/bryan/…`), subreddits (`/r/rust`), and shorthand like `/s`. The
   whole-draft scope and the second-slash rule in §5 (R1, R7) keep these as prose.
5. **The ID-less trap.** Copying `:` literally would push two thirds of selections
   through Add block ID, a *vault write*, just to look at a task. That is a requirement
   bug, fixed by R2.

## 3. How to tell Obsidian where to land

| Option | Works for ID-less tasks? | Cursor on the line (vim)? | Stale-line safe? | New dependency | Verdict |
| --- | --- | --- | --- | --- | --- |
| Core `obsidian://open?path=…` | opens the note only | no | n/a | none | Today's behaviour; not enough |
| Core `open` with `%23%5Eblock-id` | **no** (34% coverage) | scrolls to the block; cursor placement not guaranteed | by ID only | none | Rejected |
| Advanced URI `adv-uri?filepath=…&line=N` | yes | yes | **no** (blind line number) | third-party plugin | Viable stopgap only |
| **bob-plugins `obsidian://bob-open-task`** | **yes** | **yes**, centred, `<C-o>` history | **yes** (line, then ID, then text) | none (Bryan owns it) | **Recommended** |
| AppleScript / UI scripting (send `:26⏎` to vim) | yes | fragile | no | Accessibility permission | Rejected |

## 4. Other approaches considered for the trigger and the UI

| Approach | Upside | Why it is not the primary recommendation |
| --- | --- | --- |
| **A. `/` as a bob grammar token (`task_open`)** | Reuses the whole `:` lifecycle; bob refuses `/query` captures; other clients get it free | — (recommended) |
| B. `/` as a Swift-only key command on an empty draft (no `/` in the draft) | No grammar change; pastes can never collide | Needs a new draftless picker session: the picker state assumes `draftSnapshot` + `replacementRange`. The app would special-case Return and Escape itself, and would still need a new bob read command for candidates. More Swift for a worse lifecycle |
| C. A separate "Bob Tasks" quick-open panel and hotkey, like Bob Refs | Clean separation; room for previews | Another global hotkey and panel to maintain. Bryan wants it in the capture box; revisit if `/` grows into notes, closed tasks and previews |
| D. Obsidian-only "Jump to task" fuzzy command | No Mac work | Only works while Obsidian is frontmost. Becomes a cheap add-on once the handler's resolver exists |
| E. ⌥↩ "Open in Obsidian" on rows of the existing `:`/`!`/`^` pickers | No new sigil | Less discoverable, and muddles "`:` = link". A good **follow-up** once the open action exists (§6.10) |
| F. `bob task-open` CLI that shells out to `open obsidian://…` | One URI builder for zsh and Raycast | Process orchestration is the app's job per the thin-client record. The URI contract can live in bob-plugins docs. Optional later |

## 5. Requirement adjustments (called out)

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| **R1** | "`/` as the first key in the input box" | `/` claims only a **whole draft**: one line, one token, starting with `/`. In a multi-item draft or after other text, `/` is prose | Opening leaves the app, so it cannot be batched with captures. `:` is per item because it *edits* an item; `/` does not. This also limits collisions |
| **R2** | "work just like `:` as far as task selection goes" | Same rows, grouping, filtering and keys, **except that ID-less rows open directly**: no Add block ID prompt, no `plus.circle` suggestion, and a `note.md:26` locator | 66% of tasks lack IDs. Navigation must never write the vault |
| **R3** | (implicit) | Return/Tab **opens the task, hides the panel and clears the draft**; the `/query` is not stashed as a canceled draft. ⌘↩ opens in a **new Obsidian tab** (`paneType`-style), because there is nothing to capture. Shift/Option-↩ are consumed | `:`'s accept inserts and returns to the editor; `/` has nothing to insert. The next panel show should land on the idle agenda, not a stale `/fix` |
| **R4** | "focus the target Obsidian task" | Defined as follows. If the note is already open in a leaf, activate that leaf; otherwise use the active leaf (a new tab on ⌘↩). Put the cursor at column 0 of the task line and centre it. Focus the editor. Record a Vim jump so `<C-o>` returns. Obsidian is activated | Matches how `]s` and Ctrl+Shift+M already land, so it feels native in Bryan's vim workflow |
| **R5** | (implicit) | **Stale-safe landing.** Try the snapshot line if it still holds the task's text, then the block ID, then the exact task text elsewhere in the note. If all fail, land on the clamped line **with a Notice** ("task moved — landed near line N"). Never land silently on the wrong task | The snapshot can be seconds or minutes old. Obsidian or vault-sync may have shifted lines |
| **R6** | "area note / project note" | The `:` scope exactly: open tasks in **inbox, area and non-terminal project notes**. Inbox files are area notes by definition, so `mac_inbox` tasks are included. Daily-note tasks, `^ref` tasks and closed tasks stay out of v1 | Parity with `:` keeps it one bob discovery function. Broadening later is an additive bob change |
| **R7** | — | A `/` token containing a **second `/`** (`/Users/…`, `/r/rust`) stays prose, so pastes never open the picker | Keeps legitimate slash-leading drafts capturable without an escape syntax |
| **R8** | — | **Rollout requires an updated bob-plugins** (`bob plugins sync` on the Mac). bob-* plugins are gitignored, so vault-sync does not carry them | Without the handler, the URI does nothing. Ship the plugin before the app |

## 6. Recommended solution

### 6.1 Shape

```
⌃⇧⌘I  →  type "/"  →  bob capture-parse: needs task_open      (calm status, no dry run)
                     →  bob capture-complete: context task_open (same rows as ":" + note_path/target)
         picker card (scope "/", caption "Open Task")  →  ↩
         app: NSWorkspace.open(obsidian://bob-open-task?path=…&line=…&text=…[&block=…])
              hide panel, clear draft
Obsidian: bob-navigation-hotkeys handler → resolve file → resolve line (stale-safe)
          → leaf reuse → cursor + centre → Vim jump recorded
```

Each repo keeps its role:
- **bob** owns the grammar and the facts: which tasks, where they live, and their text.
- **The app** owns presentation and process orchestration: building and opening a URL.
- **bob-plugins** owns navigation inside Obsidian.

Nothing writes to the vault.

### 6.2 bob-cli: the `task_open` contract (lands first)

- **Grammar** (`capture_language`): add `task_open_query_token`, a sibling of
  `task_link_query_token`. It matches only when the **entire draft** is one line and one
  whitespace-free token that starts with `/` and has no further `/`.
  - `capture-parse` reports mode `incomplete`, item and top-level `needs:
    ["task_open"]`, one `interactive_placeholder` span over the token, and no
    diagnostics.
  - `bob capture` refuses it with a teaching error, mirroring `item.rs:425-434`:
    "`/` searches tasks to open in Obsidian; it never captures."
  - Add `task_open` to the documented `needs` order next to `task_link`.
- **Completion** (`capture_complete`): context `task_open`. The replacement covers the
  whole token, sigil included, so Backspace-on-empty removes it exactly as it does for
  `:`. Candidates reuse `capture_link_tasks::discover` + `rank`, so order and ranking
  are identical to `:`. Each row carries:
  - the `task_link` row fields minus the link-only ones: `ref`, `route`, `note_kind`,
    `block_id`, `status_*`, `text`, `section`, `depth`, `line`, `group`, `scheduled`,
    `pomodoro` and `task_kind`;
  - **`note_path`** (exact vault-relative path, as `!` and `&` already send);
  - **`target`** (absolute path, as capture results send for `ObsidianOpenURL`);
  - `replacement: ""`, kept for the shared candidate decoder; clients never insert it.

  Drop `block_id_suggestions`, `requires_block_id` and `pulls_forward`.
- **Docs and tests**:
  - add a `/<query>` row to `docs/capture.md`'s marker table;
  - extend the `capture-parse` and `capture-complete` `--help` prose, per
    `cli_rules.md`;
  - add goldens for `/`, `/fix`, `/Users/x` (prose), `/a b` (prose), a multi-item draft
    (prose), and capture refusal.

  No new subcommand is needed, which respects the frozen `capture-*` sibling rule.

### 6.3 bob-plugins: `obsidian://bob-open-task` in bob-navigation-hotkeys

- **URI v1**: `obsidian://bob-open-task?path=<abs>&line=<1-based>&text=<task
  text>[&block=<id>][&pane=tab]`.
  - Also accept `file=<vault-relative>` instead of `path`, so other clients can skip
    absolute paths.
  - Document the contract in the bob-plugins README and the Mac README, as the nav API
    is documented.
- **Registration**: call `this.registerObsidianProtocolHandler("bob-open-task", (p) =>
  void this.openTaskFromUri(p))` synchronously in `onload`, before any `await`. Put it
  in a new fragment such as `src/705-plugin-open-task-uri.js` (fragments stay ≤1000
  lines), then run `npm run build`.
- **Handler steps**:
  1. Await `workspace.onLayoutReady`.
  2. Map `path` to a vault-relative path by stripping
     `app.vault.adapter.getBasePath()`. Refuse a path outside the vault with a
     Notice. A missing file gets the Notice "Bob: bob.md not found".
  3. Read the note from the open editor's buffer if the note is open (fresher than
     disk), else with `vault.cachedRead`.
  4. Resolve the line with a pure helper, `resolveOpenTaskUriLine(content, {line,
     text, blockId})`, in this order:
     - the snapshot line, if it is a task line containing `text`;
     - `findTaskLineByBlockId`;
     - the first task line (outside frontmatter and fences) containing `text`;
     - otherwise clamp and show a Notice.

     The existing `resolveTaskMoveDestinationLine` compares *raw* lines, while bob
     sends the cleaned description, so the new helper must use a *contains* test.
  5. Call `focusTaskMoveDestination(file, {line, text: lines[line], blockId},
     vimJumpContext)`, where the jump context comes from the current cursor, so
     `<C-o>` returns. For `pane=tab`, open with `getLeaf('tab')` first.
- **Never write.** The handler must not stamp freshness, change a lane, or touch the
  ledger.
- **Tests**: add `scripts/test-navigation-open-task-uri.cjs` covering the resolver cases
  (planned, block-id, text, clamped), a path outside the vault, a missing file, and
  `pane=tab`. Run it with the existing navigation harness. Finish with `bob plugins
  sync`.

### 6.4 bob-mac-capture: the `.taskOpen` picker source

- **CaptureCore**:
  - Add `CapturePickerSource.taskOpen`, with trigger byte `47` (`/`).
  - Decode `note_path` and `target` with `decodeIfPresent`.
  - Parameterise `TaskLinkPickerIndex` by its sigil (`FuzzyQuery(filter, leadingSigil:
    "/")`) and an `open` mode. In open mode, ID-less rows show a `route.md:26` locator
    with no suggestion, and the detail strip says `↩ Opens bob.md:26 in Obsidian · ⌘↩
    new tab`.
  - Add `ObsidianOpenURL.taskURL(target:line:text:blockID:newTab:)`. URLComponents
    already handles percent-encoding.
- **Panel model**:
  - Add `handleTaskOpenCompletion`, a copy of `handleTaskLinkCompletion` with the same
    `cursor > r.start + 1` refetch.
  - Map `pickerNeed` to `.taskOpen`, with the status "Find a task to open — press Tab
    to browse".
  - On accept: check that the draft is unchanged (the existing stale-draft guard),
    hide the panel, clear the draft so it is not stashed, then open the URL with
    `NSWorkspace.OpenConfiguration(activates: true)`.
  - If the open fails (`false` or an error), keep the panel open and show the error.
- **Keys**:
  - Return/Tab: Open.
  - ⌘↩: Open in a new tab.
  - Shift/Option-↩: consumed.
  - Escape: clears the filter, then cancels to the chip "Open a task ⇥".
  - Backspace on an empty filter removes `/`, and the idle agenda returns.
  - Ctrl-C: unchanged.
- **README**: add a `### Task Open Picker` section after Task Link Picker, plus
  requirement bullets for bob `task_open` and the bob-plugins `bob-open-task` handler.
  An older bob sends no `task_open` context, so `/foo` stays an ordinary task with no
  picker: the app degrades gracefully.

### 6.5 Why this beats Option B (Swift-only `/`)

Option B looks cheaper because it changes no grammar. It is in fact more Swift and a
worse lifecycle:
- every picker accept, chip and Escape path assumes a draft token and bob's
  replacement range;
- the app would have to special-case Return on a `/` draft (it captures `/` as a task
  today), which is exactly the "app decides syntax" smell the thin-client record forbids;
- it still needs a bob read command for the rows.

Option A changes about a hundred lines of bob grammar and completion code, and every
Swift path then becomes "do what `:` does, with a different accept".

### 6.6 Edge cases to test on the Mac

- **Obsidian not running (cold start).** Confirm that the plugin action is delivered
  after `onload`. If it is not, the app should launch Obsidian (`md.obsidian`), wait
  for `didFinishLaunching` plus a short settle, then open the URI. Add this only if the
  test fails.
- **Note already open in a split or another tab.** Leaf reuse should activate it, not
  duplicate it.
- **Task under a folded heading or list.** Verify that the cursor reveal unfolds it;
  otherwise unfold explicitly before centring.
- **Leaf in Reading view.** The landing helpers need an editor, so switch that leaf to
  source or Live Preview first.
- **Lines shifted by unsaved edits or a vault-sync pull.** The resolver fallbacks
  should cover this, and the clamp Notice should appear when they cannot.
- **Unicode or spaces in note names.** Percent-encoding should handle them. Every
  current target is at the vault root, but nested project paths must work too.
- **Retained draft.** The next panel show after an open should be the empty draft with
  the agenda.

### 6.7 Rollout order and compatibility

1. **bob-cli**: grammar, `task_open` context, docs and goldens. Install `bob` on the
   Mac.
2. **bob-plugins**: the handler. Run `bob plugins sync` on the Mac (and athena).
3. **bob-mac-capture**: the `.taskOpen` source, gated by macOS CI.

Each step is additive. An old app ignores `task_open`, and an old bob never emits it.
The one gap the app cannot detect is a new app with an old plugin: the URI silently
does nothing. The README's requirements block should name the plugin, and the
open-failure path should mention "update bob-plugins".

### 6.8 Effort (rough)

| Repo | Work | Size |
| --- | --- | --- |
| bob-cli | Token predicate, parse/complete wiring, refusal, candidate struct, docs, goldens | ~0.5–1 day |
| bob-plugins | One fragment (handler + resolver), tests, build, sync | ~0.5 day |
| bob-mac-capture | Source enum, index parameterisation, handler, accept/open path, keys, README, fake-bob fixtures (`task-open-*.json`) | ~1–1.5 days plus the macOS CI loop |

### 6.9 Decision record

After shipping, consider a decisions strand along the lines of **"Task search opens; it
never writes"**. It would record that `/` is whole-draft, that ID-less rows open
without minting IDs, and that Obsidian landing lives in bob-plugins behind
`bob-open-task`. Write it through `/sase_memory_write`.

### 6.10 Follow-ups worth having (not v1)

- **⌥↩ "Open in Obsidian" on `:`, `^`, `!` and `&` rows.** This reuses the same URI.
  bob adds `note_path`/`target` to those candidates.
- **⌘↩ after a capture lands on the created task line,** not just the note top, once
  bob reports the written line.
- **An Obsidian-side "Bob: Jump to task" command** sharing the handler's resolver.
- **A wider `/` scope**, such as today's daily-note tasks (the `!` catalog already
  covers them) or `^ref` tasks, if Bryan finds himself missing them.

## 7. Open questions for Bryan

1. Is ⌘↩ = "open in a new tab" what you want, or should ⌘↩ keep the panel open for
   another search?
2. Is the second-slash rule (R7) acceptable as the only way to keep a slash-leading
   draft as prose?
3. Should v1 already include today's daily-note tasks (the `!` catalog's "In today's
   note" section), or keep strict `:` parity?

## Sources

- Obsidian Help, "Obsidian URI": <https://obsidian.md/help/uri>
- Obsidian API, `registerObsidianProtocolHandler`:
  <https://docs.obsidian.md/Reference/TypeScript+API/Plugin/registerObsidianProtocolHandler>
- Advanced URI docs, Navigation:
  <https://publish.obsidian.md/advanced-uri-doc/Actions/Navigation> and Navigation
  Parameters: <https://publish.obsidian.md/advanced-uri-doc/Concepts/Navigation+Parameters>
- Obsidian forum, custom URI handler and cold-start reports:
  <https://forum.obsidian.md/t/custom-uri-protocoll-not-registered/35102>,
  <https://forum.obsidian.md/t/uri-new-action-doesnt-create-new-note-on-obsidian-android-when-closed/95861>,
  <https://forum.obsidian.md/t/the-obsidian-uri-handler-affects-the-app-but-no-longer-activates-the-app-window/90387>
- Code (paths as cited above):
  - bob-cli `src/native/capture_language/{tokens,item}.rs`,
    `src/native/capture_complete/{model,candidates}.rs`,
    `src/native/capture_link_tasks.rs`, `docs/capture.md`;
  - bob-mac-capture `Sources/CaptureCore/{ObsidianOpenURL,TaskLinkPickerPresentation,CapturePickerPresentation}.swift`,
    `Sources/BobMacCapture/CapturePanelModel.swift`, `README.md`;
  - bob-plugins `plugins/bob-navigation-hotkeys/src/{170,250,480,536,650}-*.js`.
- Memory: `decisions:mac-capture-is-a-thin-client`,
  `decisions:idle-capture-shows-ledger-agenda`, `glossary:area-note`,
  `glossary:inbox-file`, `obsidian.md` (bob-* plugins are gitignored, deployed by
  `bob plugins sync`).
- Live probes on athena (read-only `capture-parse`/`capture-complete` against `~/bob`):
  464 `:` candidates, 307 ID-less, about 22 ms.

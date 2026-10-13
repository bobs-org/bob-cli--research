# Slash-goto (`/` first-key Obsidian task search) for bob-mac-capture — research (`__mus`)

## 1. Question asked

Add support to bob-mac-capture for pressing `/` as the first key in the input box to
trigger a new Obsidian task search that:

- selects tasks exactly like the `:` picker, but
- on accept, opens the owning area/project note in Obsidian and focuses the task,
  instead of inserting a `@route:block-id` link into the draft.

This report researches the cheapest correct implementation, critiques the plan, adjusts
requirements where justified, and ends with a recommended solution. All repo claims below
were verified by reading the implementation or running `bob` in this session.

## 2. How `:` task selection works today (the thing `/` must mirror)

### 2.1 bob-cli side (grammar owner)

- A **solo leading `:` token** is a dedicated completion claim, disjoint from `^`, `!`,
  `+`, `&`. `task_link_query_token` (`src/native/capture_language/tokens.rs`) only
  fires on a **single-line, single-token item** whose token starts with `:`.
  `task_link_completion_field_at` (`src/native/capture_language/completion.rs`) then
  returns context `task_link` with the query = text after the sigil and the
  **replacement range covering the whole token including the sigil**, so accepting
  rewrites the query into the canonical `@route:block-id` link. It runs before the `^`
  path and only on the item's leading line.
- Candidates come from `task_link_candidates` (`src/native/capture_complete/candidates.rs`),
  built on `capture_link_tasks::discover` + `rank` (`src/native/capture_link_tasks.rs`):
  every **linkable open task** (Ready, Blocked, Next, In Progress) in the **routable
  inbox, area, and non-terminal project notes**. Terminal (done) projects and loose
  non-routable notes are excluded by construction.
- Verified JSON shape per candidate (pinned by
  `task_link_completion_pins_json_shape_and_omissions` and re-read here): `replacement`
  (`@route:id`, or `""` for ID-less tasks that must never be inserted),
  `ref` (stale-safe task ref), `route`, `note_kind` (`inbox`/`area`/`project`),
  `block_id` (nullable), `requires_block_id`, `block_id_suggestions`, `status_symbol` /
  `status_name` / `status_type`, `text`, `section`, `depth`, **`line` (1-based note
  line)**, `group` (`queued`/`in_progress`/`next`/`note`), `scheduled`, `pulls_forward`,
  `pomodoro`. Notably **absent**: any absolute or vault-relative note path
  (contrast `task_dependency` candidates, which do carry vault-relative `note_path`).
- Parse agrees: bare `:` is `mode: incomplete` with `needs: ["task_link"]` (verified:
  `bob capture-parse --format json -- ":"`).

### 2.2 Mac side (thin presentation)

- `bob-mac-capture` is a thin client by recorded decision
  (`decisions:mac-capture-is-a-thin-client`, re-read for this report): bob-cli owns
  grammar, completion data, preview, and vault mutation; the app spawns `bob
  capture-parse` / `capture-complete` / `capture --dry-run` and renders. It may filter
  or rank what bob returns but never decides syntax. New capture behavior lands in
  bob-cli and `docs/capture.md` first.
- The `:` response is routed by `handleTaskLinkCompletion`
  (`Sources/BobMacCapture/CapturePanelModel.swift`) into a `.taskLink` picker source
  (`Sources/CaptureCore/CapturePickerPresentation.swift`, trigger byte `:` = 58).
- Rows are built by `TaskLinkPickerIndex` (`Sources/CaptureCore/TaskLinkPickerPresentation.swift`):
  keyed by `"route|ref"` (never by `replacement`, which is `""` for ID-less rows),
  grouped Pomodoro → In Progress → Next → per-note sections when the filter is empty,
  one ranked flat section otherwise. `FuzzyQuery` strips one leading `:` from the first
  token so a draft-seeded filter (`:dee`) matches like bare text (`dee`).
- Accept path (`acceptPickerRow`): rows with `insertion == nil` + `pendingBlockID` go
  through the existing **Add block ID prompt** (`capture-task-id`) instead of inserting;
  identified rows splice `replacement` into bob's range, re-run analysis, and announce
  `Inserted …`. Shift-Return (`acceptPickerRowAndStart`) splices link + `=` for
  link-and-start; Command-Return inserts and captures.
- Obsidian opening today is **file-level only**: `ObsidianOpenURL.url(forAbsolutePath:)`
  (`Sources/CaptureCore/ObsidianOpenURL.swift`) builds
  `obsidian://open?path=<percent-encoded absolute target>`; bob only ever returns the
  absolute filesystem `target`, never an Obsidian URI. `uniqueTargetURLs` + `targetOpener`
  (injectable, defaults to `NSWorkspace.shared.open`) open capture targets after
  Command-Return submit. There is **no line- or block-focus machinery** in the app.

## 3. What `/` does today (verified)

- `bob capture-parse --format json -- "/"` → `mode: "task"`, no needs, no diagnostics:
  a leading `/` is currently **ordinary inbox-task prose**.
- `bob capture-complete --cursor 1 --format json -- "/"` (and `--cursor 4 -- "/foo"`) →
  `context: null`, no candidates. `/` claims nothing.
- So `/` is free grammatically, but repurposing it **takes away today's behavior**:
  any draft whose first character is `/` stops being capturable prose.

## 4. The two hard sub-problems

### 4.1 Triggering: how `/` summons the same candidate list

Two architectures, with very different thin-client consequences:

- **(A) Client-side alias.** The Mac app notices a leading `/`, and either rewrites it
  to `:` before calling `bob capture-complete`, or opens a `.taskLink`-backed picker
  locally while leaving the draft showing `/`. No bob change; ships in one repo.
  Cost: Swift now decides that `/` means task search — exactly the grammar-in-Swift
  duplication the thin-client decision exists to prevent ("Bob is the only authority
  for the grammar"). It also forks every shared behavior gated on the trigger byte or
  the `task_link` context (replacement ranges, `taskLinkPickerQuery`'s `r.start + 1`
  seed, marker highlight, chip help, `locatorMarker`, status text).
- **(B) Server-side trigger.** bob's grammar learns a solo-leading-`/` claim returning
  the same `task_link` candidate machinery (either the same `task_link` context with a
  trigger marker, or a new `task_goto` context with an identical candidate payload).
  The Mac decodes and presents it like `.taskLink` but with a goto accept path. Cost:
  two-repo change with additive JSON growth, which is the normal, already-paid cost of
  every capture feature — and it keeps `bob capture-complete -c 1 -- "/"` working for
  every future client (Raycast, Shortcuts, shell) for free.

Evaluation: (B) is the only option consistent with the thin-client record. (A) should
be rejected even though it is faster to prototype, because the trigger byte leaks into
at least six switch sites (`triggerByte`, `scopeSymbolText`, `locatorMarker`,
`taskLinkPickerQuery`, `pickerMarkerHighlightRange`, key hints) that would each need a
`/` carve-out.

### 4.2 Focusing: opening the note *at the task*

This is the genuinely new capability — nothing in either repo does it — and it splits
into resolving the file and scrolling to the row:

- **Resolving the file.** Completion candidates carry `route` + `line` + `block_id` but
  no path. Two ways to get one: (1) Mac-side join of `route` → `capture-targets`
  `relative_path` via the existing `CaptureTargetsCache`, plus `BOB_DIR`; (2) bob adds
  vault-relative `note_path` to `task_link` candidates (additive, `decodeIfPresent`
  fallback), exactly as `task_dependency` candidates already do. (2) is robust
  (no second spawn, no stale-cache skew, handles renames between cache refresh and
  pick) and has direct precedent; (1) is the zero-bob-change fallback.
- **Scrolling to the row.** Stock `obsidian://open` (both `vault`+`file` and `path=`
  forms, corroborated by multiple URI references this session) **opens files but takes
  no line parameter**. Line/block focus needs one of:
  1. **Advanced URI community plugin** (`obsidian://advanced-uri?vault=…&filepath=…&line=N`,
     1-indexed). Not installed in Bryan's vault (plugin list checked this session:
     no `obsidian-advanced-uri`; present: `mrj-jump-to-link`, `bob-navigation-hotkeys`,
     `bob-ledger-tools`, `block-id-prompt`, tasks/dataview/templater and others).
     Depending on it means a new plugin dependency for one keystroke.
  2. **A tiny protocol handler in a Bryan-owned plugin** (e.g. extend
     `bob-navigation-hotkeys`, which already owns jump/cursor/scroll helpers such as
     `170-open-task-jump.js`, with `registerObsidianProtocolHandler("bob-goto", …)`
     accepting `path` + `block` + `line`). No new third-party dependency, full control
     of fallback (block anchor first, line second, top-of-file last), works with the
     existing `path=` style so no vault-name configuration is needed. No such handler
     exists today (searched the plugin tree) — it must be written.
  3. **Block-search fallback with stock URIs only**: `obsidian://open?path=…` then
     `obsidian://search?vault=…&query=^block-id`. Two hops, focus is a search pane
     rather than the editor cursor, and ID-less tasks have no anchor at all. Acceptable
     as a degraded path, not as the primary.
- **Anchor stability matters.** `block_id` (`^id`) is stable across edits above the
  task; `line` rots the moment any line is added or removed. The candidate set already
  distinguishes them: identified rows have a block anchor, ID-less rows have only a
  line plus `block_id_suggestions`. Any design that focuses by line for identified tasks
  is strictly worse than focusing by block.

## 5. Critique of the plan as stated

1. **The core idea is good; the chosen key is the risky part.** A keyboard-first
   "fuzzy task → jump to it in Obsidian" fills a real gap: today the only task jump is
   inside captures (insert a link) or inside Obsidian (review walk, `]s` queue). Putting
   it on the capture hotkey means zero context switch. But `/`-as-first-key overloads
   the capture box with a **second mode (goto)** that shares the input, the picker
   chrome, and the muscle memory of a **capture** tool. Mode confusion is the top risk:
   a user who types `/fix flake` meaning prose gets a picker; a user who picks a row
   meaning to capture gets an Obsidian window and an empty draft.
2. **`/` hijacks real input for little ergonomic gain over `:`**. `:` already summons
   this exact list and needs one Shift key. `/` saves Shift but costs: (a) every draft
   starting with `/` becomes un-capturable (URLs are safe — they never lead with `/` —
   but paths, fractions, `/-continued` prose, and Vim-style `/search` habits are not);
   (b) a grammar fork in bob's most-touched completion function; (c) a second trigger
   byte through the Mac picker state machine. If the goal is speed, a cheaperцентраль
   alternative exists (see §6.3).
3. **"Works just like `:` for selection" is under-specified in the ways that will cause
   bugs.** The `:` accept path has at least four behaviors that make no sense for goto
   and must be explicitly dropped or remapped, not inherited: Shift-Return link-and-start
   (would capture, violating goto's read-only promise), Command-Return insert-and-capture
   (same), the Add-block-ID prompt's "then inserts @route:id" follow-up (goto inserts
   nothing — after naming, it should open, not splice), and the `pendingBlockID`
   `insertion == nil` guard's announcement strings ("Inserted …" / "↩ inserts …").
   Key hints, VoiceOver labels, and the detail strip (`↩ inserts @…`) all need goto
   wording (`↩ open in Obsidian`), or the picker will lie about what Return does.
4. **"Open the appropriate area note / project note" silently drops the inbox.**
   `task_link` candidates include routable **inbox** notes (`note_kind: "inbox"`,
   e.g. `mac_inbox`) alongside area and project notes. Either the goto list must filter
   to area/project (throwing away inbox hits the user may want) or the requirement must
   say inbox too. The latter is almost certainly intended — adjust the requirement.
5. **"Focus the target task" cannot be delivered with stock Obsidian alone.**
   As §4.2 shows, `obsidian://open?path=` opens the file and stops. Shipping trigger +
   selection without the focus half produces a feature that opens the right 800-line
   note with the cursor at the top — worse than useless for the stated goal, because the
   user then Ctrl-Fs by hand. The focus transport (own-plugin handler recommended) is
   not a stretch goal; it is part of the MVP.
6. **ID-less tasks need a decision, not an accident.** Roughly a third of typical
   candidates carry `requires_block_id: true` (the worked example returns 8 rows, 3
   ID-less). "Select → open + focus" is undefined for them: there is no block anchor,
   and line focus is fragile. Options: (a) force the Add-block-ID prompt first, then
   open via the fresh anchor (a vault write inside a supposedly read-only goto — must
   be disclosed in the UI, e.g. "↩ names this task (^suggestion), then opens it");
   (b) open by line with a "line may have shifted" caveat; (c) exclude ID-less rows
   from goto. (a) with explicit disclosure is recommended; (c) silently hides tasks the
   user searched for.
7. **Empty-draft collision with the ledger agenda.** By recorded decision
   (`decisions:idle-capture-shows-ledger-agenda`, re-read), an empty draft shows today's
   Pomodoro agenda, and the app never reads the vault. `/` as first keystroke must
   dismiss or dim the agenda exactly like `:` does today (check the `agendaHold` /
   `agendaDimmed` path — `:` behavior is the template), and Escape from an empty `/`
   filter must restore the agenda, not close the panel. Clearing back to a bare `/`
   should show the grouped (ungrouped-query) task list, mirroring `:`.
8. **Multi-line and mid-draft `/` must stay prose.** The `:` claim is deliberately
   narrow (first line, solo token). `/` must be at least as narrow — ideally narrower
   (see recommendation): only when the entire draft is `/…` at offset 0. A `/` typed
   anywhere else (second line, after text, in Work Log entries) must remain literal
   prose, or goto will ambush ordinary captures.

## 6. Alternatives considered

| Option | Trigger | Accept | Verdict |
|---|---|---|---|
| Stated plan (`/` mirrors `:`, opens + focuses) | new `/` grammar claim | open note, focus task | viable but needs §5 fixes + focus transport |
| `:` + explicit open gesture (e.g. ⌘↩ opens instead of inserts; or ⌥↩) | none (existing `:`) | open focused task | cheapest, zero grammar change, zero mode, discoverable via key hint; loses single-key speed |
| Dedicated goto hotkey/palette (separate panel mode) | hotkey, not a character | open focused task | cleanest separation of capture vs navigate; more Mac UI work |
| `/` opens Obsidian search pane only | `/` claim | `obsidian://search` | weakest focus; not recommended as primary |

The middle row deserves emphasis: if `/`-as-character proves contentious, **teaching the
`:` picker a second accept key (⌘↩ or ⌥↩ = "open in Obsidian at this task")** delivers
~80% of the value with no grammar change, no hijacked input, and no new mode — at the
price of one modifier. It can also ship first as the fallback if the `/` grammar work
slips. The recommended solution below keeps `/` (the ask) but structures the Mac work
so this gesture falls out nearly free.

## 7. Requirement adjustments (proposed, to be confirmed)

- **R1 — inbox included.** "Area / project note" → "the owning routable note (inbox,
  area, or project)". Rationale: candidates span all three; excluding inbox silently
  drops hits.
- **R2 — goto is read-only except disclosed ID naming.** Selecting an identified task
  performs **no vault write and no capture call**: open + focus + dismiss panel, draft
  untouched (restore the pre-`/` draft or leave the panel empty per existing dismiss
  semantics — recommend restoring, since goto is a detour, not an edit). The only
  exception is accepting an ID-less row, which offers Add block ID first with explicit
  "then opens" wording.
- **R3 — trigger gated to a solo leading `/` on an otherwise-empty single-line draft.**
  Not "any `/` as first keystroke of a bigger draft", and never past line 1. Rationale:
  bounds the prose hijack (§5.2, §5.8) and mirrors the `:` claim's narrowness.
- **R4 — focus by block anchor, line as fallback.** Identified tasks focus via `^id`;
  ID-less tasks (after R2 naming, or if the user skips naming) fall back to 1-based
  `line` with best effort. Rationale: stability (§4.2).
- **R5 — no start/capture follow-ups in goto mode.** Shift-Return and Command-Return do
  nothing (or, preferably, Command-Return is the shared "open" key on the `:` picker —
  see §6); key hints, detail strip, and VoiceOver strings are goto-specific.
- **R6 — focus transport is in scope.** Definition of done includes the Obsidian-side
  jump (own-plugin protocol handler recommended), not just file open.

## 8. Recommended solution

### 8.1 bob-cli (lands first, with `docs/capture.md`)

1. **Add a solo-leading-`/` completion claim** in `completion.rs` next to
   `task_link_completion_field_at`, gated exactly like `:` (leading line, solo token)
   **plus** the R3 whole-draft-emptiness bound if cheap to express there (otherwise
   enforce the bound Mac-side and document it). Two context designs are defensible:
   - **(i) Reuse `task_link`** (same context, same candidates, same replacement range
     semantics). Smallest diff; Mac distinguishes presentation only by remembering the
     typed trigger. Risk: replacement range covering `/…` implies "accept rewrites to
     `@route:id`", which goto never does — a client that doesn't know about goto will
     do the wrong thing with the response.
   - **(ii) New `task_goto` context with the identical candidate payload.**
     Recommended: self-describing, old clients safely see an unknown context and show
     nothing rather than mis-inserting, and the Mac can switch picker source on context
     instead of sniffing the trigger byte. Candidates reuse `task_link_candidates`
     wholesale (same discovery, order, ranking, ID-less inclusion).
2. **Add vault-relative `note_path` to each candidate** (copy the `task_dependency`
   precedent), so the Mac can build the absolute target without a racy second
   `capture-targets` join. Keep `line` and `block_id` as the focus facts. All additive
   under `decodeIfPresent`; `schema_version` bump only if the repo's policy requires it
   for new contexts (check `SCHEMA_VERSION` handling — the Mac rejects mismatched
   versions, so coordinate).
3. **Parse side**: bare `/` should report a goto need (new `Need`, `interactive_placeholder`
   span, calm status line e.g. "Find a task — pick to open in Obsidian") mirroring the
   `:` incomplete path, so live preview never shows a doomed dry run.
4. Tests: clone the `task_links.rs` fixtures for `/` (canonical order, JSON shape with
   `note_path`, query ranking, sigil refetch at `replacement.start`, batch second-item
   scoping, missing-day-file behavior).

### 8.2 Obsidian side (Bryan-owned plugin, no new third-party dependency)

5. **Register a `bob-goto` protocol handler** in `bob-navigation-hotkeys`
   (`registerObsidianProtocolHandler("bob-goto", …)`): params `path` (absolute, as today),
   `block` (optional `^id` without caret), `line` (optional 1-based fallback). Behavior:
   open `path`, then if `block` matches `^id` in the file, set cursor to that line and
   scroll into view (center); else if `line` is in range, go there; else top-of-file.
   Reuse the existing jump/scroll helpers around `170-open-task-jump.js`. This avoids
   the Advanced URI dependency (not installed) while matching its `line` semantics for
   any future migration.
6. Fallback chain Mac-side: `bob-goto` → plain `obsidian://open?path=` (file opens,
   task not focused; surface a one-line "opened without focus — update plugins" hint
   only in that degraded case, not on the happy path).

### 8.3 bob-mac-capture (decodes and presents; no grammar of its own)

7. **New picker source** (e.g. `.taskGoto`, trigger byte `/` = 47) reusing
   `TaskLinkPickerIndex` for rows/sections/ranking and `FuzzyQuery(filter,
   leadingSigil: "/")` for the seed strip. All `:`-shared switches gain the goto case
   alongside `.taskLink` (query seed `r.start + 1`, marker highlight = replacement
   range, `locatorMarker ":"` for display), but the **accept path diverges**:
   - Single Return: resolve target (candidate `note_path` + `BOB_DIR`, fallback
     `CaptureTargetsCache`), build the `bob-goto` URL with `block` and/or `line`,
     `targetOpener(url)`, dismiss panel, restore pre-`/` draft, announce
     "Opened <route>.md — <task text>" for VoiceOver. **No `capture` call.**
   - ID-less row: present the existing Add-block-ID prompt with goto wording
     ("↩ names this task (^suggestion), then opens it"); on submit, `capture-task-id`
     then open via the fresh anchor; on cancel, return to the goto list.
   - Shift-Return / Command-Return: unbound in goto (consumed no-op), except optionally
     wire Command-Return as the shared open gesture on the `:` picker per §6.
   - Key hints: `↑↓ Move · ↩ Open · esc Clear / Cancel`; card label "Task search";
     detail strip "↩ opens <route>.md at ^id" (or "at line N" for ID-less).
8. **Agenda interplay**: `/` dismisses/dims the idle ledger agenda exactly like `:`; Esc
   on empty goto filter restores the agenda; the panel never reads the vault (target
   resolution comes from bob's response + targets cache, both subprocess facts).
9. **Stale-draft guard**: reuse `draftSnapshot` refusal — a late pick after the draft
   moved must never open a task for a query the user already erased.
10. **Tests**: picker-source unit tests (seed strip, grouped/filtered parity with `:`,
    ID-less prompt routing, no-capture-call assertion on goto accept), `ObsidianOpenURL`
    goto-URL builder tests, and a controller test that goto accept calls `targetOpener`
    with `block` and never calls submit.

### 8.4 Rollout order

bob-cli grammar + `note_path` + docs → plugin `bob-goto` handler + `bob plugins sync` →
Mac goto source + URL builder + key hints → manual end-to-end (identified task, ID-less
task, inbox task, queued/Pomodoro task, missing-handler fallback, agenda restore).
If the bob-cli half slips, ship the §6 middle row first (`:` + open gesture reusing the
same URL builder) — it unblocks the focus transport independently of `/`.

## 9. Risks and open questions

- `/`-prose hijack: measure how often Bryan's drafts lead with `/` today (history
  review); if non-trivial, prefer the §6 open-gesture-only design and skip the `/`
  character entirely.
- Advanced URI vs own handler: if Bryan prefers not to touch `bob-navigation-hotkeys`,
  installing Advanced URI is the honest alternative — but then focus depends on a
  community plugin's install state on every Mac, and Reading-view line navigation has
  known issues (upstream issue #91, still worth re-verifying).
- `obsidian://search` as focus fallback is weak (search pane, not cursor) — keep it as
  last resort only.
- Vault-name vs `path=`: keep the `path=` style throughout so no vault-name
  configuration is needed; confirm `bob-goto` handler resolves `path` to its vault
  internally.

## 10. Bottom line

The plan is worth doing with adjustments: keep the `:`-identical selection list, but
implement the trigger server-side as a new `task_goto` context (not a Swift alias),
resolve files via a new additive `note_path` candidate field, focus by block anchor
through a small `bob-goto` handler in Bryan's own plugin (not Advanced URI, not stock
`open`), make goto read-only with goto-specific key hints, include inbox hits, force
explicit Add-block-ID for ID-less rows, and gate the trigger to a solo leading `/`.
If the `/` character itself proves too costly in review, the same focus transport plus
one new open key on the existing `:` picker delivers most of the value with none of the
grammar risk.

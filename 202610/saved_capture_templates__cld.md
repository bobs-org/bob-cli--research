# Saved capture templates: a Ctrl-T template shelf for `bob capture` and Bob Mac Capture

Researcher: **cld** (research swarm `research.1n`) · 2026-10-16

> **Ask.** Save bulk capture templates (`@@template:`, epic `bob-cli-7w`) to disk
> automatically when they are used. Let Bryan open and edit the saved templates in Bob
> Mac Capture with a new **Ctrl-T** keymap that works like the canceled-draft stash
> (**Ctrl-S**). Selecting a template pops it; using it in a capture re-adds it. Lead the
> design, critique the plan, adjust requirements where justified, and recommend a
> solution.

## TL;DR

**Yes, build it.** It is the natural next step: the templates plan already listed "saved
or reusable templates" as out-of-scope follow-up #5. Bryan's motivating case (job
applications in waves of 10–12) brings the same template back again and again. I would
ship it with four changes to the request, each called out in
[Requirement adjustments](#requirement-adjustments):

1. **bob-cli owns the saved templates, not the Mac app.** `bob capture` saves the
   template of every successful real capture to `$XDG_STATE_HOME/bob-cli/capture/templates.json`.
   A new protocol sibling, `bob capture-templates`, lists, shows, and deletes them. The
   Mac only presents them. The stash is Mac-owned because it holds panel drafts, a UI
   artifact. A template is a capture-language artifact, and decision
   `mac-capture-is-a-thin-client` puts those in bob. Terminal captures then save too.
2. **"Pop" removes the template from the list, not from disk. I call this
   *borrowing*.** A selected template disappears from the shelf while it sits in your
   draft. It is replaced by your edited version when the capture succeeds. It returns
   unchanged if you abandon the draft. A literal stash-style pop would make the editor
   the *only* copy of a durable asset. A wrong pick, Discard, Ctrl-C, a quit or crash,
   or the planned "Expand template" action (`bob-cli-83`) would then silently destroy
   it.
3. **Deleting a template is an explicit action.** Abandoning a draft no longer deletes
   anything, so the shelf gets explicit deletes: **⌫** deletes one template and
   **Shift-D** deletes all. Each needs a second press to confirm, because unlike stash
   entries these are lasting assets.
4. **Ctrl-T also works on a draft that has rows but no template.** It puts the chosen
   template on top as one undoable edit, so you can paste rows first and choose a
   template second. The stash needs an empty editor because restoring replaces the
   draft. Inserting a template only adds text.

Everything else follows the stash: the same panel region, material, accelerator
alphabet, and keyboard-only flow. It adds one thing for beauty. Each row shows the
template with bob's own syntax highlighting: `{0}` in orange, `{1}` in teal, the route in
route color. So the shelf preview looks exactly like the template will look once it is
in the editor.

---

## 1. What exists today (verified)

### Bulk templates (`bob-cli-7w`, closed 2026-10-15)

- A draft whose first nonblank line is `@@template:` is a **template draft**. The next
  block (a parent line plus optional child bullets) is the template, with `{0}…{N-1}`
  placeholders. Each later nonblank line is a **row**. The governing rule is
  `capture(D) ≡ capture(expand(D))`, all or nothing (`docs/capture.md` § Bulk
  templates).
- The pure module is `src/native/capture_language/template.rs`. `analyze()` returns the
  header range, the template block range and lines, the placeholders, `field_count`,
  the rows, and the issues. The module does no I/O.
- Probes with a bob built from master:
  - `capture-parse` returns a top-level `template` object with `header.range`,
    `range`, `line_start`, `line_end`, and `field_count`.
  - On a header plus template with no rows, it returns `needs: ["template_row"]` and
    the calm diagnostic `template_missing_rows`. This is exactly the state the editor is
    in right after a saved template is inserted.
  - It also returns colored spans (`template_header`, `template_placeholder` with
    `field`) and the template item's `route` (`job`) and `mode` (`task`).
- **Wording gap (small).** Once the blank separator line is already there, bob still
  says *"add a blank line, then one row per capture"* (probed). That is the exact state
  after a saved template is inserted, so this message would be the first thing Bryan
  sees. See §6.4.
- The epic's out-of-scope list:
  - item 5 is "**Saved or reusable templates** (snippet or vault note)";
  - the earlier research put it as "once the same template keeps coming back"
    (`research:202610/bulk_capture_template_drafts/bulk_capture_template_drafts.md`).

### The canceled-draft stash (Bob Mac Capture)

- **Store.** `Sources/CaptureCore/CanceledDraftStashStore.swift` writes
  `~/Library/Application Support/org.bobs.bob-mac-capture/canceled-draft-stash.json`
  with `schemaVersion` 1, newest first.
  - The directory is 0700 and the file is 0600. Writes are atomic and write-through on
    every mutation.
  - An unreadable file, or one with an unknown schema, is renamed to
    `canceled-draft-stash.corrupt.json`.
  - An empty stash deletes both files.
- **Model.** `Sources/BobMacCapture/CanceledDraftStash.swift` holds the entries.
  - Capacity defaults to 10 and is clamped to 0…36. The 36 fits the one-key
    accelerator alphabet `1–9, 0, A–C, -, E–Z`, with `D` reserved for Delete All.
  - Helpers produce the preview line, line count, and relative age.
- **Behavior** (`CapturePanelModel.swift:1941–2058`, README §Keyboard):
  - **Ctrl-C** stashes a nonempty draft and closes the panel.
  - **Ctrl-S** toggles the picker (`CaptureKeyCommandRouter.swift:150`).
  - The picker refuses to open unless the editor is empty: *"Capture, retain, or
    cancel the current draft before opening stash"*.
  - Restoring a row **pops** it: the entry is removed and its text is installed with
    the caret at the end.
  - **Shift-D** deletes all entries immediately. **Discard** never stashes.
- **View.** `CanceledDraftStashPicker` (`CapturePanelView.swift:1409`) shows up to five
  rows in a compact material card. Each row has an accelerator keycap, a monospaced
  two-line preview, and "N lines - 3h ago". A red **Shift-D Delete All** bar sits at the
  bottom. The footer has a **Stash N** button.
- **Not persisted.** A *retained* live draft (closed with Escape) lives only in memory;
  only canceled drafts survive Quit or a crash (README line 1192). This matters for any
  pop design: a popped template that is only in the editor does not survive a restart.

### Ground rules that shape the design

- **Decision `mac-capture-is-a-thin-client`.** bob-cli is the only implementation of
  capture grammar, preview, and vault mutation. *"New capture behavior lands in bob-cli
  and `docs/capture.md` first; the app then decodes and presents it."*
- **Memory note `cli_rules`.**
  - Never add a subcommand under `bob capture`; `capture-*` siblings grow additively.
  - A bare group may default only to a flag-only, read-only member.
  - Options are alphabetical, and every public long option has a short alias.
  - Help and completion sections must match.
- **Precedent for bob-owned per-machine state.** `bob capture` already writes outside
  the vault:
  - the reference-job spool under `bob_cli_state_dir()/ref/jobs/` (`src/native/ref_jobs/spool.rs`);
  - after commit, `ref_jobs::kick()` runs as a best-effort step that only warns on
    failure (`src/native/capture/mod.rs:229–243`).

  That is the exact shape a "save the template after a successful commit" step needs.
- **Test isolation already exists.** `tests/cli/support.rs:54` sets `XDG_STATE_HOME`
  for CLI tests, so saving from `bob capture` cannot leak into Bryan's real state.
- **The Mac app scrubs the environment it gives bob** (`BobEnvironment.swift:56`). It
  passes `HOME`, but not `XDG_STATE_HOME`. bob run from the app therefore resolves
  `~/.local/state/bob-cli`. A terminal with a non-default `XDG_STATE_HOME` would see a
  different shelf (§7, R7).
- **Ctrl-T is free in the capture panel.** No app binding or global hotkey uses it.
  Taking it costs AppKit's Emacs-style "transpose characters" in the editor
  ([Brett Terpstra](https://brettterpstra.com/2023/12/18/macos-keybinding-tricks-the-kill-ring/)).
- **`bob-cli-83` is open (READY).** It is an "Expand template" Mac action that replaces
  the draft with `bob capture -E` output. It interacts with pop semantics (§3).

---

## 2. Is this a good idea? (critique)

**Yes. The core instinct is sound:** save automatically, use a stash-like picker, and
let edits made while using a template replace the old version. Some points need care.

| # | Aspect of the request | Verdict | Why |
| --- | --- | --- | --- |
| C1 | **Save automatically on use** | ✅ Keep | No extra gesture, and only templates that actually captured get in, so the shelf never holds a broken one. The cost is clutter from one-off templates. Recency order, a 36-entry cap, and replace-on-edit contain it. Explicit "save template" gestures get forgotten exactly when they matter. Raycast's clipboard history and shell `Ctrl-R` history show auto-saved, recency-ordered history works when deletion is easy ([Raycast manual](https://manual.raycast.com/clipboard-history)). |
| C2 | **Work like the stash** | ✅ Keep for the **UI**; ⚠️ change the **storage owner** | The stash holds Mac panel drafts, a UI artifact the Mac rightly owns. A saved template is a *capture-language* object: what counts as "the template", how it is normalized, and whether it is valid are grammar questions. The thin-client decision puts those in bob. Owning it in bob also makes `bob capture` from a terminal save templates, which the request names ("support to the `bob capture` command"). |
| C3 | **Ctrl-T keymap** | ✅ Keep | Good mnemonic next to Ctrl-S (S = stash, T = templates). The only cost is transpose. Note it in the README and keep `bob-cli-83` off Ctrl-T. |
| C4 | **Pop on select** | ⚠️ Keep the *visible* behavior, change the *storage* behavior | Pop is the right idea: picking, editing, and capturing should *replace* the template, not pile up near-duplicates. But a literal pop deletes the only lasting copy and trusts the editor to bring it back. The editor is fragile: Discard, Ctrl-C, Select-All+Delete, Undo, an app quit or crash (retained drafts aren't persisted), and `bob-cli-83`'s Expand all lose it silently. Stash entries are throwaway by nature. Templates are assets. See §3. |
| C5 | **Re-add when used** | ✅ Keep, with "used" defined precisely | "Used" means a successful, non-dry-run `bob capture` of a template draft. Not `--dry-run`, not `-E`, and not a failed capture. Saving runs after the vault commit and is best-effort. It must never fail or roll back a capture that already wrote the vault. |
| C6 | **"View/modify saved templates"** | ✅ For v1, "modify" means borrow, edit, capture | This covers the real flow: edits happen when you next use a template. There is no way to fix a typo without capturing rows. That is acceptable for v1, and a ⌘S "Save template" (§9) can add it later without redesign. |
| C7 | **Timing** | ⚠️ Keep v1 small | Templates shipped yesterday, so there is no usage data on how many distinct templates Bryan keeps. Defer pinning, names, search, and cross-machine sync until real use asks for them. |

**Would I take a different approach?** Not a different *product*. A shelf of recently
used templates on Ctrl-T is the right shape. I would change the *storage owner* (bob)
and the *pop semantics* (borrow). I considered and rejected these alternatives:

| Alternative | Why not (for v1) |
| --- | --- |
| **A. Mac-owned store** (clone the stash store) | Fewer moving parts and no new bob command. But it is Mac-only (terminal captures don't save), and the Mac would have to decide what "the template" of a submitted draft is. That means either slicing text with a possibly stale parse, or bob adding `template.text` to capture JSON anyway. It also splits template knowledge across two codebases, against the thin-client decision. |
| **B. bob-owned local state** (recommended) | One store for every frontend, saved inside the same process that committed the capture, and grammar-aware normalization and identity. It costs a new `capture-templates` command and cross-repo version gating, both already routine here (`capture-pomodoros --tasks` shipped the same way). |
| **C. Vault note** (e.g. a Markdown or JSON file in `~/bob`) | Syncs across the Mac, apollo, and athena, and can be edited in Obsidian. But every template capture would also rewrite a vault file. Two machines bumping recency between syncs is a real git conflict, and the conflict policy keeps the remote copy and moves the local one to `_conflicts/`, so a template quietly leaves the shelf. It would also bring agent-run captures on apollo into Bryan's shelf, and new vault notes need `parent` frontmatter. Reopen if cross-machine reuse becomes a real need, possibly as an explicit "promote to vault" export. |
| **D. Saved templates as `@@` completion candidates** | Elegant and fully bob-owned: typing `@@` on line 1 would offer saved templates next to `template:`. But a completion row can't show a multi-line, colored preview, and accepting a completion is the wrong moment to borrow. A good **later** complement, not a replacement for Ctrl-T. |
| **E. Named templates in the header** (`@@template:job-apply`) | It would give each template an identity carried in the draft text, which survives the stash, the terminal, everything. But it spends the `@@template:<x>` slot the templates plan reserved for options (`tsv`), and forces naming before reuse. Revisit only if the shelf gets large. |
| **F. "Recall last template" only** (no list) | Simplest, but Bryan clearly has several recurring templates (job applications, groceries-style lists, reading batches). |

---

## 3. The pop question: three semantics, compared

The request: *"pop a template when it is selected (it will just get re-added when the
capture is submitted if the template is used)"*.

| Event after selecting template **A** | **P1 Hard pop** (literal stash parity) | **P2 Borrow** (recommended) | **P3 Copy** (no pop) |
| --- | --- | --- | --- |
| Capture succeeds, A unchanged | A re-saved at top ✅ | A bumped to top ✅ | A bumped ✅ |
| Capture succeeds, edited to **A′** | A′ saved, A gone ✅ | A′ saved, A deleted ✅ | A′ **and** A ❌ (near-duplicates pile up) |
| Wrong pick, user clears the editor to choose again | A **lost** ❌ | A back on shelf ✅ | A still there ✅ |
| **Discard** | A **lost** ❌ (doubles as the delete gesture) | A back ✅ (delete is ⌫ in the picker) | A there ✅ |
| **Ctrl-C** (stash the draft) | A only inside the stash entry ⚠️ | A back on shelf, draft in stash ✅ | A there ✅ |
| Escape (retain), then app quit or crash | A **lost** ❌ | A back (nothing was deleted) ✅ | A there ✅ |
| `bob-cli-83` Expand, then capture | A **lost** ❌ (expansion has no template) | A back ✅ | A there ✅ |
| Picker shows A while it's in the editor | No ✅ | No ✅ | Yes ⚠️ (double-pick possible) |
| Machinery needed | `pop` verb | Hide-while-borrowed in memory, plus one `delete <id>` after a success that changed the template | Origin id passed through `bob capture` to avoid duplicates |

**Recommendation: P2, borrow.** From Bryan's seat it behaves exactly as he asked: the
template leaves the list when picked and comes back on top when used. It differs only on
the abandon paths, where P1 loses data. It also needs *less* bob machinery than P1: no
`pop` verb, just `list` and `delete`. The borrow state is a single in-memory value in the
Mac, `borrowed = (id, draft)`. A crash forgets that value, and since nothing was deleted,
the template is simply visible again.

```text
             Ctrl-T pick
  shelf  ───────────────▶  borrowed (hidden in the picker; still on disk)
    ▲                           │
    │ abandon:                  │ capture succeeds (bob saves the submitted
    │ Discard, Ctrl-C, empty    │ template on top; if it changed, the Mac
    │ editor, quit or crash     │ deletes the borrowed original by id)
    └──────── unhide ◀──────────┘
```

One sentence for the README: **"Picking a template borrows it: it leaves the list while
it's in your draft, comes back on top, edits and all, when you capture, and comes back
unchanged if you don't."**

---

## 4. Requirement adjustments

Each adjustment is a deliberate change to what was asked:

| # | Asked | Adjusted to | Justification |
| --- | --- | --- | --- |
| **R1** | Work "similar to the capture stash" (implicitly a Mac-owned store) | **bob owns the store** (`$XDG_STATE_HOME/bob-cli/capture/templates.json`) and adds `bob capture-templates`. The Mac only presents. | Thin-client decision; terminal captures save too; bob defines template identity. |
| **R2** | Pop on select | **Borrow**: hidden while in the draft, replaced on successful capture, returned on abandon | §3: P1 loses lasting assets on six common paths, including the planned Expand action. |
| **R3** | (Deletion implied by pop plus discard) | **⌫ deletes the selected template; Shift-D deletes all.** Both need a second press to confirm. | Abandoning no longer deletes, so deletion must be explicit. Templates are assets, so they get a two-press confirm, unlike the stash's immediate Shift-D. |
| **R4** | Picker behaves like the stash, which needs an empty editor | **Ctrl-T also opens on a draft with no template** (it inserts the template on top, as one undo step). It also opens on a draft that still holds *only* the untouched borrowed template, so you can swap. Otherwise it refuses with *"This draft already has a template"*. | Rows often come from a paste (an LLM table, a spreadsheet). Inserting a template only adds text and is one ⌘Z to undo. The swap case is "wrong pick, try another". |
| **R5** | "Persist when used" | **Only after a successful, non-dry-run `bob capture`**, after the vault commit. Best-effort: a failed save becomes a warning, never a failed capture. | Reliability. The vault write is the main effect and must not depend on a convenience store. |
| **R6** | (Unbounded) | **At most 36 templates, most recently used first; the least recently used is evicted.** `capture.saved_templates` in bob config (default 36, `0` turns saving off). | 36 matches the accelerator alphabet. The config key is a kill switch for scripts and agents. |
| **R7** | — | A small bob wording fix: `template_missing_rows` says *"add one row per capture (3 values, separated by spaces)"* when the separator line already exists. | It is the first message Bryan sees after every pick (§1). bob owns the wording. |
| **R8** | — | Ctrl-T replaces AppKit's *transpose* in the editor, and `bob-cli-83` must not claim Ctrl-T. | Disclosure, and coordination with the open bead. |

---

## 5. Recommended design: bob-cli half

### 5.1 Store

- **Path.** `bob_cli_state_dir()/capture/templates.json`, with lock file
  `capture/templates.lock`. Override with `BOB_CAPTURE_TEMPLATES_FILE`, following the
  `BOB_VAULT_SYNC_STATE_FILE` precedent. The directory is 0700 and the file 0600, like
  the stash: templates can hold private URLs and names.
- **Format** (`schema_version` 1, most recently used first):

  ```json
  {
    "schema_version": 1,
    "templates": [
      {
        "id": "9c1f0e2a7b3d",
        "text": "Apply to {0}! @job^apply-{1}\n- **URL**: {2}",
        "first_saved_at": "2026-10-16T09:12:44-04:00",
        "last_used_at": "2026-10-16T09:12:44-04:00",
        "use_count": 3
      }
    ]
  }
  ```

- **Canonical text and identity.**
  - `text` is the typed template block from `template::analyze`: the lines between the
    header and the first blank line. The header is excluded. Each line has trailing
    spaces and tabs removed, line endings become `\n`, and indentation, braces, and
    smart quotes are kept verbatim.
  - `id` is the first 12 hex digits of SHA-256(`text`). Identical templates therefore
    *are* the same entry: saving deduplicates for free, `delete <id>` is idempotent,
    and an edited template gets a new id without bookkeeping. `sha2` and `hex` are
    already dependencies.
- **Writes.** Take an exclusive `fs2` lock (bob's ref ingest lock is the precedent),
  read, modify, write a temp file, `rename`, and `fsync` the directory. The Mac app and
  a terminal can both run bob at once, so the lock is not optional.
- **Recovery.**
  - An unreadable file is renamed to `templates.corrupt.json`; bob warns and starts
    empty, like the stash.
  - **A file with a *newer* `schema_version` is never quarantined.** bob reads nothing,
    refuses to write, and warns *"saved templates file is from a newer bob"*. The stash
    quarantines on any schema mismatch. That is safe for a single-binary app, but this
    file is shared by every bob on the machine, so an older bob must never destroy a
    newer one's data.

### 5.2 Saving in `bob capture`

Add one step in `capture()` (`src/native/capture/mod.rs:229`), right after
`commit_capture_batch` succeeds and beside `ref_jobs::kick()`:

- **When.** Run it only if this is not a dry run, the batch was a template draft
  (`batch.template.is_some()`), and `capture.saved_templates > 0`.
- **What.** Canonicalize, then upsert by `id`:
  - an existing entry gets `last_used_at = now`, `use_count += 1`, and moves to the
    front;
  - a new entry goes to the front;
  - entries beyond capacity are dropped from the least recently used end.
- **Failure.** Warn on stderr (`warning: template not saved: …`) and add a JSON warning
  with code `template_not_saved`. The exit code stays 0, because the vault write
  already succeeded.
- **JSON (additive).** On success, `template` gains `"saved": {"id": "9c1f0e2a7b3d",
  "status": "new" | "updated"}`. `saved` is absent on dry runs, when saving is
  disabled, or when the save failed. The Mac relies on this field (§6.3).
- **Human output.** The existing dim line becomes `template  3 rows · lines 5–7 · saved`.
- `-E`, `--dry-run`, failed captures, and drafts without a header never touch the store.

### 5.3 `bob capture-templates` (new Capture-protocol sibling)

Per `cli_rules` this cannot be `bob capture templates`, because TEXT would swallow it.
The bare form lists, which is allowed: it is read-only and takes only flags.

```text
bob capture-templates [list] [-f, --format human|json]
bob capture-templates show <ID|N>                 # print the ready-to-use draft
bob capture-templates delete <ID|N>... [-f json]  # idempotent; unknown IDs are "already gone"
bob capture-templates clear [-f json]             # delete the file and any quarantine copy
```

- **Help line** (Capture protocol section, alphabetical): `capture-templates  List,
  show, and delete saved bulk capture templates`. Register it in `bob <TAB>` completion
  groups.
- **`N` versus `ID`.** `N` is the 1-based list position, handy in a terminal. `ID` is
  the 12-hex id, which the Mac always uses. They are told apart by length.
- **Human `list`.** One block per template: the index, the template lines with bob's
  usual colors (placeholders tinted, route highlighted), and a dim line such as
  `3 fields · job · used 3× · 2d ago`.
- **JSON `list`.** Everything the Mac needs to render and insert **without parsing**:

  ```json
  {
    "ok": true,
    "schema_version": 1,
    "capacity": 36,
    "templates": [
      {
        "index": 1,
        "id": "9c1f0e2a7b3d",
        "text": "Apply to {0}! @job^apply-{1}\n- **URL**: {2}",
        "draft": "@@template:\nApply to {0}! @job^apply-{1}\n- **URL**: {2}\n\n",
        "cursor": 57,
        "field_count": 3,
        "line_count": 2,
        "route": "job",
        "mode": "task",
        "spans": [{ "start": 9, "end": 12, "kind": "template_placeholder", "field": 0 }],
        "first_saved_at": "…",
        "last_used_at": "…",
        "use_count": 3
      }
    ],
    "warnings": []
  }
  ```

  - `draft` is the exact text to insert, and `cursor` is the UTF-8 offset where rows
    begin. bob decides both.
  - `spans` index into `text`. bob computes them by running its template-aware parse
    on `@@template:\n` + `text` and shifting the offsets. In process, 36 parses take
    microseconds; a whole debug-build `capture-parse` *process* measured about 13 ms.
  - `route` and `mode` come from the template item.
- **`show`** prints `draft` raw, so it pipes cleanly:
  `bob capture-templates show 1 > d && $EDITOR d && bob capture < d`.
- **Not in v1:** `save` (store a template without capturing), `pin`, and `rename`.
  See §9.

---

## 6. Recommended design: Bob Mac Capture half

### 6.1 Keys

| Key | In the editor | While the Templates shelf is open |
| --- | --- | --- |
| **Control-T** | Open the shelf (rules below) | Close the shelf |
| 1…9, 0, A…C, -, E…Z | — | Use that template immediately |
| Return | — | Use the selected template |
| Down / Ctrl-N, Up / Ctrl-P | — | Move the selection, wrapping |
| **⌫ (Backspace)** | — | Arm a delete on the selected row (a red **Delete?** capsule appears); press ⌫ again to delete. Any other key disarms. |
| **Shift-D** | — | Arm Delete All (*"Press Shift-D again to delete all 7 templates"*); press again to confirm |
| Control-S | Open the stash | Close the shelf and open the stash (stash rules apply) |
| Escape / Ctrl-[ | (unchanged) | Close only the shelf |

In the stash picker, **Control-T** closes the stash and opens the shelf. A modified `T`
must never reach the stash's `T` accelerator: the router's `modifiers.isEmpty` guard
already prevents that, and a test should pin it.

**When Ctrl-T opens:**

- **Empty editor.** Opens.
- **Draft without a template** (bob's parse has no `template` object). Opens. Using a
  template *inserts it at the top*.
- **Draft that is exactly the borrowed template's untouched `draft`.** Opens; using
  another template *swaps* it.
- **Any other template draft.** The shelf stays closed and the status reads *"This draft
  already has a template"*.
- **Empty shelf.** The status reads *"No saved templates yet. Capture an @@template:
  draft to save one"*, matching the stash's *"No canceled drafts yet"*.
- **Inline prompt or task picker open.** The key is consumed, as Ctrl-S does today.

### 6.2 Using a template

Each case below is **one native undo step**. Use the existing pattern:
`breakUndoCoalescing()` then `insertText(_:replacementRange:)`, as in
`applySeparatorToggleInEditableTextView`.

- **Empty editor.** Insert `draft` and put the caret at `cursor`, the empty row line.
  bob's next parse then reports `template_row`, the calm unfinished state that ships
  today: no red, the preview cleared, and bob's R7 message in the status line.
- **Rows already typed.** Insert `draft` at offset 0. The caret keeps its place, shifted
  by the insertion. bob's normal diagnostics underline any row that doesn't fit, such as
  an arity mismatch.
- **Swap.** Replace the whole draft with the new `draft`. The old borrowed template is
  simply un-hidden.

In every case, set `borrowed = (id, draft)` and hide that row from the shelf.

### 6.3 Settling a borrow

- **The capture succeeds and bob reports `template.saved.id`.**
  - If that id differs from `borrowed.id`, the template was edited. Run
    `bob capture-templates delete <borrowed.id>` in the background; if it fails, the
    status shows a note and a harmless near-duplicate remains.
  - Clear `borrowed` and refresh the cache.
- **The capture succeeds but the draft had no template**, for example after an Expand
  or after the header was deleted: clear `borrowed`. Nothing is deleted.
- **Discard, Ctrl-C (stash), or an editor left empty** (the user deleted everything):
  clear `borrowed`. The template reappears where it was.
- **Escape (retained draft):** keep the borrow, since the draft still has it.
- **Quit or crash:** the borrow is forgotten, and because nothing was deleted, the
  template is visible on the next launch.

### 6.4 Presentation (the "beautiful" part)

```text
╭──────────────────────────────────────────────────────────────────────╮
│ ┃1┃  Apply to {0}! @job^apply-{1}                         3 fields   │  ← selected (accent fill)
│      - **URL**: {2}                                 job · 3× · 2d ago │
│                                                                      │
│ ┃2┃  {0} @groceries                                        1 field   │
│                                               groceries · 1× · 6d ago│
│                                                                      │
│ ┃3┃  Read {0} @reading^{1} p:2                             2 fields   │
│                                                 reading · 5× · 3w ago│
├──────────────────────────────────────────────────────────────────────┤
│  ⌫ Delete     Shift-D Delete All                        ⌃T Close      │
╰──────────────────────────────────────────────────────────────────────╯
```

- **Same chrome as the stash.** It uses the same auxiliary region, `.regularMaterial`,
  8 pt radius, shadow, accelerator keycaps, five visible rows that then scroll, and a
  height policy. Visual consistency between Ctrl-S and Ctrl-T is part of the design.
  Move the generic parts (accelerator alphabet, wrap-around selection, height policy,
  keycap style) into `CaptureCore` so `portable-check` covers them, and build both
  pickers on them.
- **Highlighted previews.** Turn the row's `spans` into an `AttributedString` with the
  editor's own category-to-color mapping (`CaptureEditorPalette`). `{k}` uses slot hue
  `k % 6`, and `@job^` uses the route color. The row then looks exactly like what lands
  in the editor, where each row's *k*-th field already shares `{k}`'s hue. Show the
  parent line at full strength, one child line in secondary color, and "+N more lines"
  beyond that.
- **Metadata column, right-aligned.** First line: `3 fields`. Second line: route ·
  uses · age, reusing the stash's `relativeAgeDescription`. All of it comes straight
  from bob's JSON.
- **Footer button.** Add **Templates N** with SF Symbol `square.stack.3d.down.right`,
  the same glyph as the `@@template:` completion row, so the two read as one feature.
  Tooltip: *"Use a saved template (Control-T)"*. Disable it under the same conditions as
  **Stash**.
- **Calm after insert.** Bob's R7 status reads *"add one row per capture (3 values,
  separated by spaces)"*.
- **Optional polish:** a faint ghost hint on the empty row line, `{0} {1} {2}` in the
  slot hues, that disappears on the first keystroke. It is purely presentational
  (derived from `field_count`), so it stays thin-client clean.
- **Accessibility.** List label: "Saved templates, 3 entries". Row label: "Template 1,
  Apply to {0}…, 3 fields, job, used 3 times, 2 days ago". Hint: "Press 1 or Return to
  use this template; Backspace twice to delete."

### 6.5 Freshness, compatibility, and errors

- **Cache.** Keep the list in memory, refresh it when the panel is presented and after
  every capture or delete, and open Ctrl-T instantly from the cache. This is the same
  cache-then-revalidate pattern the idle agenda uses (decision
  `idle-capture-shows-ledger-agenda`).
- **Old bob.** If `capture-templates` is an unrecognized subcommand, hide the footer
  button, and Ctrl-T shows *"Update bob to use saved templates"*. Decode every new field
  with `decodeIfPresent`, as the app already does.
- **Stale id** (the template was deleted in a terminal while the shelf was open):
  `delete` treats a missing id as already gone. Using a template that has vanished
  shows *"Template is no longer available"* and refreshes the list.

---

## 7. Risks and edge cases

| # | Case | Handling |
| --- | --- | --- |
| R1 | Both the Mac and a terminal write at once | `fs2` lock plus atomic rename; ids are content hashes, so retries are idempotent |
| R2 | Disk full or permissions error while saving | Capture still succeeds; `template_not_saved` warning; the Mac shows the warning in the status line |
| R3 | An older bob meets a newer file | Read-only plus a warning, never a quarantine (§5.1) |
| R4 | A template captured with forced `-r/-s/-t` flags | The saved template lacks the forced destination. Document this; the Mac never passes those flags |
| R5 | SASE agents run template captures on apollo | They save to apollo's state, not the Mac's. Isolation is a feature. `capture.saved_templates: 0` turns saving off per host |
| R6 | One-off templates crowd out regulars | Recency order plus a cap of 36; pinning is a follow-up if this actually happens |
| R7 | `XDG_STATE_HOME` differs between the Mac app's environment and the terminal | The app doesn't pass `XDG_STATE_HOME` (`BobEnvironment.swift:56`). Document it and have `list -f json` report the `file` path; optionally add `XDG_STATE_HOME` to `preservedOverrideKeys`. Check whether Bryan's dotfiles set it on the Mac |
| R8 | `bob-cli-83` Expand on a borrowed draft | Safe under borrowing (the template returns). Under hard pop it would be data loss, which is one more reason for P2 |
| R9 | Undo after inserting a template | One ⌘Z removes the insertion. The borrow clears when the editor becomes empty; if rows remain, the borrow stays until the draft settles, which is harmless because the original is on disk |
| R10 | Ctrl-C a borrowed draft, later restore it from the stash and capture | The draft is captured and saved by content. If it was edited, A′ is saved *beside* A, because the stash doesn't carry provenance. Accept this; delete A with ⌫⌫ if unwanted |

---

## 8. Implementation phases

1. **bob-cli: store and saving (medium).**
   - Add a module `src/native/capture_templates/` with `store.rs` (canonicalize, id,
     load, upsert, evict, delete, clear, lock, quarantine, newer-schema guard) and the
     `cli.rs` command.
   - Add the post-commit save in `capture()`, the additive `template.saved` JSON, the
     human ` · saved`, the config key `capture.saved_templates`, and the env var
     `BOB_CAPTURE_TEMPLATES_FILE`.
   - Add `bob capture-templates list|show|delete|clear` with human and JSON output,
     help, and completion groups, plus the R7 wording variant of `template_missing_rows`.
   - Docs: `docs/capture.md` § Saved templates (after § Bulk templates), the README
     capture-protocol table, and the config docs.
   - **Unit tests** (store): normalization (CRLF, trailing spaces), id stability,
     deduplication and bumping, eviction order, capacity 0, a corrupt file, a
     newer-schema file, and permissions.
   - **CLI tests:** saved after a real capture, but not after `--dry-run`, `-E`, a
     failed capture, or a draft without a header; JSON shapes, including
     `spans`/`draft`/`cursor`; `delete` idempotency; `clear`; and that a save failure
     keeps exit 0.
   - **Done when:** `just check` passes.
2. **Mac: Templates shelf (medium).**
   - **Models.** `CaptureTemplatesListResponse` and `CaptureTemplateSummary.saved`.
   - **Client.** `BobProcessClient.captureTemplates()` and
     `deleteCaptureTemplate(id:)`, with feature detection.
   - **Model state.** A `SavedTemplateShelf` holding the cache, `borrowed`, the hidden
     row, and the armed delete.
   - **Keys.** Router cases for Ctrl-T and every shelf key.
   - **Editing.** The three insertion modes as single native edits; settlement in
     `completeSubmit`, `discardDraft`, and `stashDraftAndClose`.
   - **View.** The view, built on the shared picker parts, and the footer button.
   - **Docs.** README keyboard table, shelf section, and compatibility notes.
   - **Fixtures and tests.** Record fixtures from a bob built from Phase 1 into
     `Tests/Fixtures/fake-bob`. Test router mapping (including "Ctrl-T in the stash
     never restores row T"), borrow and settle state transitions, and presentation, with
     light and dark render fixtures.
   - **Compile, per `AGENTS.md`:** `just portable-check` (on athena if `swift` is
     missing), then a best-effort scratch build on the Mac with `bundle.sh` and
     `just typecheck-tests`. If the Mac is offline, say so.
3. **Memory (small; ask Bryan first per `/sase_memory_write`).**
   - A decisions strand, *"Saved Capture Templates Are bob-Owned And Borrowed, Not
     Popped"*. The claim is R1 plus R2; the alternatives are §2 A–F and §3 P1/P3; it
     reopens if cross-machine reuse or naming is needed.
   - A glossary term, **Saved Template** (alias: template shelf).
   - Add a note on `bob-cli-83` to keep it off Ctrl-T.

## 9. Follow-ups (not in v1)

- **Pin** (`capture-templates pin`, a Mac key such as `⌘.` as in Raycast): pinned
  templates are never evicted and sort first.
- **Save without capturing.** ⌘S in a template draft, backed by
  `bob capture-templates save`, so a fix can be made without rows. Combined with
  borrowing, this is a complete "edit in place".
- **`@@` completion candidates for saved templates** (§2 D).
- **Labels or names** for a large shelf; possibly the reserved header slot (§2 E).
- **Cross-machine sync or a "promote to vault" export**, if Bryan starts templating
  from apollo as well.
- **Apply to rows in a draft that already has a template** (swap the template block and
  keep the rows). It needs bob to return an edit, like `capture-rewrite`.

## 10. Open questions for Bryan

1. **Borrow (P2) or literal pop (P1)?** I recommend P2. If you *want* "pop plus Discard"
   as the way to delete, P1 is simpler, but it loses templates on wrong picks, quits,
   and Expand.
2. **Per-machine shelf on the Mac:** is that enough, or do you expect to reuse templates
   from apollo or athena terminals?
3. **A cap of 36, most recent first:** acceptable, or do you want pinning in v1?
4. **Insert on top of an existing draft (R4):** keep it in v1? It is cheap and suits a
   paste-rows-first flow.

---

## Recommended solution

Build a **bob-owned shelf of recently used templates with a stash-style Ctrl-T picker,
using borrow semantics**:

1. **bob-cli.** After every successful, non-dry-run template capture, `bob capture`
   upserts the canonical template block into `$XDG_STATE_HOME/bob-cli/capture/templates.json`.
   - The id is a content hash, so duplicates merge. The list is most-recent-first with
     a cap of 36 (`capture.saved_templates`).
   - Writes are locked and atomic, with 0600 permissions. An older bob never touches a
     newer file.
   - Saving is best-effort and never fails the capture.
   - Capture JSON reports `template.saved.id`.
   - A new `bob capture-templates list|show|delete|clear` command returns, per template,
     the insertable `draft` and `cursor` plus `spans`, `field_count`, `route`, use
     count, and age. The Mac therefore never parses anything.
2. **Bob Mac Capture.**
   - **Ctrl-T** opens a Templates shelf that looks and moves like the stash: same
     region, material, accelerators, and footer.
   - Each row is a syntax-colored preview whose placeholder hues match the editor.
   - **Using a template borrows it.** It is inserted (into an empty draft, on top of
     pasted rows, or swapped for an untouched borrowed one) as a single undo step and
     hidden from the shelf.
   - **A successful capture settles the borrow.** bob saves the submitted version on
     top, and the Mac deletes the original only if it changed.
   - **Any abandon simply un-hides it.** Deletion is explicit (⌫⌫ for one, Shift-D
     Shift-D for all).
3. **Ship it in two phases, bob first and Mac second**, under the thin-client decision.
   Then record the bob-owned-and-borrowed decision and a **Saved Template** glossary
   term once Bryan approves.

This keeps everything Bryan asked for: automatic saving, Ctrl-T, stash-like browsing,
and "it leaves the list when picked and comes back when used". It removes the one way
the literal request could quietly destroy his work, and it makes the shelf a faithful,
colored preview of what each template will do.

---

### Sources

- Internal (read via `sase artifact read` / `sase repo open` / `sase memory read`):
  - `plan:202610/bulk_capture_templates.md` (bead `bob-cli-7w`; out-of-scope §5);
  - `research:202610/bulk_capture_template_drafts/bulk_capture_template_drafts.md`;
  - decisions `mac-capture-is-a-thin-client` and `idle-capture-shows-ledger-agenda`;
  - memory notes `cli_rules.md` and `obsidian.md`;
  - bead `bob-cli-83`.
- bob-cli code: `src/native/capture/mod.rs:229–243`,
  `src/native/capture_language/template.rs`, `src/native/env.rs:257–270`,
  `src/native/ref_jobs/spool.rs`, `tests/cli/support.rs:54`, `docs/capture.md` § Bulk
  templates. Probes ran against a bob built from master `a041abdb`.
- bob-mac-capture code:
  - `Sources/CaptureCore/CanceledDraftStashStore.swift`;
  - `Sources/BobMacCapture/CanceledDraftStash.swift`;
  - `Sources/BobMacCapture/CapturePanelModel.swift:1941–2058` and `:6018`;
  - `Sources/BobMacCapture/CaptureKeyCommandRouter.swift:150` and `:454–492`;
  - `Sources/BobMacCapture/CapturePanelView.swift:1409–1585` and `:843`;
  - `Sources/BobMacCapture/CapturePanelController.swift:925–947`;
  - `Sources/CaptureCore/BobEnvironment.swift:56`;
  - `README.md` §Keyboard (lines 1702–1790) and the persistence notes (line 1192).
- External:
  - [Raycast Manual: Clipboard History](https://manual.raycast.com/clipboard-history):
    auto-saved history, pin to protect from retention, delete entry or all;
  - [Brett Terpstra: macOS keybinding tricks](https://brettterpstra.com/2023/12/18/macos-keybinding-tricks-the-kill-ring/):
    Control-T transposes in Cocoa text views;
  - [Apple: Cocoa Text Architecture, Text Editing](https://developer.apple.com/library/mac/documentation/TextFonts/Conceptual/CocoaTextArchitecture/TextEditing/TextEditing.html):
    the standard key-binding dictionary.

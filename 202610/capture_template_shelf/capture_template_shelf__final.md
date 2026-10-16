# Saved capture templates: a bob-owned template shelf behind Control-T

**Lead researcher consolidation** · 2026-10-16 · Merges five independent reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this directory) with the lead's own
verification. The code checks ran against bob-cli `9ce50eeb` and bob-mac-capture
`a4009a4`, plus Bryan's chezmoi dotfiles.

> **Ask.** `@@template:` drafts (epic `bob-cli-7w`) should be saved to disk
> automatically when used. Bob Mac Capture should let Bryan view and modify them behind
> a new **Control-T** key that works like the canceled-draft stash (Control-S).
> Selecting a template pops it, and it is re-added when a capture that uses it is
> submitted. Lead the design (intuitive, reliable, beautiful), critique the plan, call
> out any changed requirements, and recommend a solution.

## TL;DR

**Build it.** Saved templates were the first follow-up the template epic deferred
(plan `bulk_capture_templates.md`, out of scope #5: "Saved or reusable templates").
Bryan's motivating loop is still running: job applications come in waves, and each
wave reuses the same `Apply to {0}! @job^apply-{1}` + URL-child shape. Today a
successful capture clears the draft, so that shape is thrown away every time it works.

All five researchers agree on the core:

- save the **template block only** (never the rows);
- save **only after a successful real capture**;
- **deduplicate** by content;
- reuse the stash's look and keys;
- **do not literally delete a template when it is picked.**

They split on two questions: who owns the store, and what "pop" should mean. My
answers:

1. **bob owns the shelf, not the Mac app** (sides with cdx and cld against grk, mus,
   and gem). `bob capture` saves the block in the same process that committed the
   capture. A new protocol sibling, `bob capture-templates`, lists, shows, saves, and
   deletes entries. The Mac app only renders what bob returns.
2. **"Pop" becomes a checkout.** A picked template leaves the shelf. When the capture
   succeeds, it comes back on top, *with your edits replacing the original*. Abandon
   the draft and it comes back unchanged. That keeps the useful part of pop (edits
   replace instead of piling up near-duplicates) and drops the harmful part (the only
   durable copy vanishing on Discard, Control-C, a crash, or the planned Expand action).

A synthesis point no single report made explicit: **under the stash's empty-draft gate,
"hidden while popped" is never visible.** The picker can only open when no template is
in the draft, so the borrowed row is never on screen to be hidden. The only observable
effects of a literal pop are therefore *replace-on-edit* (good) and *loss on abandon*
(bad). A copy that remembers its origin gives the first without the second. The
"borrow" camp (cdx, cld) and the "copy" camp (grk, mus, gem) were describing the same
mechanism; the copy camp only lacked origin tracking.

---

## 1. Adjustments to the request (called out)

| # | Asked or implied | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | "Similar to the stash" (implies a store owned by the Mac app) | **bob owns the store** at `$XDG_STATE_HOME/bob-cli/capture/templates.json`. New sibling `bob capture-templates`. | Decision `mac-capture-is-a-thin-client`: "New capture behavior lands in bob-cli … first; the app then decodes and presents it." Deciding what "the template" of a draft is counts as a grammar question. With bob owning it, terminal captures save too, and the save runs in the same process as the commit. |
| **A2** | Pop on select; re-add on submit | **Checkout.** Selection deletes nothing. A successful capture saves the used version on top and removes the original *in the same bob call*. Abandoning keeps the original. | A literal pop makes the editor the only copy of a lasting asset. Discard, Control-C (bounded stash, which evicts), quit or crash after Escape (retained drafts live only in memory, README §persistence), a failed capture followed by clearing, and `bob-cli-83`'s Expand would all destroy it silently. |
| **A3** | "Persist templates when used" | **Persist the template block (parent + authored children) only. Rows are never saved.** | Saved rows would replay old companies and URLs, risk double captures, and keep private row data on disk. The stash already keeps whole unfinished drafts. |
| **A4** | "When they are used" | **Used = a successful, non-dry-run `bob capture` of a template draft.** Never parse, preview, `--dry-run`, `-E`, or a failed capture. One use per invocation, not one per row. | Previews run on every keystroke, and a failed capture is not a use. |
| **A5** | Modify = pop, edit, capture | **Also add ⌘S "Save template"** in any template draft, including one with no rows yet. It saves without capturing. | Fixing a route or authoring a template ahead of a wave should not require capturing throwaway tasks (four of five reports wanted this). |
| **A6** | Deletion happens implicitly (pop then discard) | **Explicit deletion only:** ⌫ then ⌫ deletes the selected row. **Clear all lives in Settings** (confirmed) and in `bob capture-templates clear`, not in the picker footer. | Since abandoning no longer deletes, deletion needs a gesture. The stash's one-chord red Shift-D bar suits a junk drawer, not a library, and stash muscle memory would someday wipe the job template. |
| **A7** | Opens like the stash (empty draft only) | **Control-T also opens on a draft that has no template.** It inserts the template on top as one undo step. A draft that already has a template is refused. | Pasting rows first (an LLM table, a spreadsheet) and then choosing the shape is a natural flow. The insert only adds text, so one ⌘Z removes it. |
| **A8** | (No limit stated) | **At most 36 entries, most recently used first.** The least recently used is evicted past the cap. A bob config key (default 36) can set it to `0`, which turns saving off without deleting anything. | 36 fills the stash's one-key accelerator alphabet. Recency-plus-cap is how auto-saved histories stay useful. Pinning is a follow-up if eviction ever bites. |
| **A9** | New Control-T keymap | Keep it, and **document that it replaces AppKit's transpose-characters in the capture editor.** Keep `bob-cli-83` off Control-T. | Control-T is unbound in the router (`CaptureKeyCommandRouter.swift:86–112` has no `t`). The macOS default transposes characters ([Apple shortcuts](https://support.apple.com/en-us/102650)). |
| **A10** | — | **A small bob wording fix:** `template_missing_rows` should say "add one row per capture (3 values separated by spaces)" when the blank separator is already present. | Today it always says "add a blank line, then one row per capture" (`template.rs:449`). That is wrong in exactly the state every pick produces, so it would be the first thing Bryan reads. |

**Proposals considered and not adopted:**

- **A Mac-owned store** (grk, mus, gem). See §3.1.
- **Making the template save a staged participant in the vault commit** (cdx). See §3.3.
- **Persisting `--route`/`--section`/`--task` invocation defaults** with each template
  (cdx). Bob Mac Capture never passes those flags, so this would make a template's
  behavior depend on something not visible in its text. Document the limitation
  instead.
- **A search field instead of accelerators** (cdx). It suits an unbounded library; at
  ≤36 entries, one-key selection is faster.
- **A per-vault namespace** (cdx). There is one vault, and bob's existing machine state
  (the ref-job spool) is machine-wide.
- **A separate "Template Edit Mode"** (gem). The editor already *is* a template editor;
  ⌘S covers it.
- **A Swift skeleton extractor** (gem). It re-implements `@@template:` framing in Swift,
  which the thin-client decision forbids.
- **An immediate Shift-D clear** (gem, mus).
- **Swap mode for an untouched pick** (cld). ⌘Z plus Control-T does the same job.

---

## 2. Verified ground truth

The reports mostly agreed on facts. The lead checked every fact the design depends on.
Corrections to individual reports are marked ⚑.

**bob-cli**

- `capture()` (`src/native/capture/mod.rs`, ~L226–246) runs plan → `commit_capture_batch`
  → a best-effort `ref_jobs::kick()` that only warns on failure. That is the exact
  slot, and the exact failure policy, for a post-commit template save. `CaptureRequest`
  already carries `raw_text` and `bob_dir` (`capture/cli.rs:658`).
- `template::analyze(raw)` is pure. It returns the `header` range, a `block` with its
  `range`/`line_start`/`line_end`, the `placeholders`, `field_count`, the `rows`, and
  ranged `issues` (`capture_language/template.rs:67–84, 219`). Re-running it after
  commit to extract the block is cheap and needs no new plumbing.
- Success JSON's `template` is only `{line, field_count, row_count}` (`template.rs:39`).
  It has no block text, so a frontend owning the store would have to slice the draft
  itself (grk's approach and its stale-parse race).
- A template block without placeholders already fails as `template_missing_placeholder`
  (`template.rs:454–460`), so saving never sees a placeholder-free template.
- `bob_cli_state_dir()` = `${XDG_STATE_HOME:-~/.local/state}/bob-cli`
  (`env.rs:256–270`). `create_state_lock_file` already creates 0700/0600 lock files,
  and `fs2` locking is already used by ref ingest. The ref-job spool is machine-wide
  and records `bob_dir` per job (`ref_jobs/spool.rs:32–34`). CLI tests isolate
  `XDG_STATE_HOME` (`tests/cli/support.rs:54`), so a saving `bob capture` cannot leak
  into real state during tests.
- Hidden internal capture arguments already exist: `--require-pull-in-choice` and
  `--task-ref` (`capture/cli.rs:566–605`). `cli_rules` exempts internal subprocess
  arguments from the short-alias rule and allows additive `capture-*` siblings.
  ⚑ grk overstated the CLI rules as an obstacle: a `capture-templates` sibling is
  explicitly allowed. Only `bob capture <subcommand>` is forbidden.

**Bob Mac Capture**

- **Stash** (`CanceledDraftStash.swift`, `CanceledDraftStashStore.swift`,
  `CapturePanelModel.swift:1941–2045`):
  - It lives in Application Support: schema 1, 0700/0600, quarantine on corruption,
    file deleted when empty.
  - Capacity defaults to 10 and is clamped to 0…36. The accelerator alphabet is
    `1234567890ABC-EFGHIJKLMNOPQRSTUVWXYZ` (D is reserved for Shift-D).
  - The picker opens only on an empty draft. Restore installs the text first, *then*
    removes the entry.
  - Shift-D clears immediately.
  - ⚑ **There is no per-entry delete.** The stash picker router (`:454–492`) has no
    Backspace case, contrary to mus's "mirroring the stash picker's existing
    affordances".
- Retained drafts (Escape, failed capture) live **only in memory**; only canceled drafts
  survive Quit or a crash (README ~L1185–1200). ⚑ gem's "Escape erases the template" is
  imprecise: Escape retains the draft. The loss under a literal pop comes from Discard,
  Control-C eviction, or a quit or crash *after* Escape.
- A successful capture clears the draft (`completeSubmit`, verified by grk). No
  "last template" survives.
- **Control-T** has no binding in the router, the README, or any source. **⌘S** is
  unbound too.
- **Environment:** the app passes `HOME` to bob but not `XDG_STATE_HOME`
  (`BobEnvironment.swift:56–65`). The lead grepped Bryan's chezmoi source: no dotfile
  exports `XDG_STATE_HOME`. App-launched bob and terminal bob on the Mac therefore
  resolve the **same** `~/.local/state/bob-cli` today, so cld's R7 risk is documentation
  only.
- **Side finding (unrelated bug):** `preservedOverrideKeys` lists `BOB_CONFIG`, which no
  bob code reads; bob reads `BOB_CONFIG_FILE` (`src/native/config/mod.rs:25`). A
  `BOB_CONFIG_FILE` override in the app's launch environment is silently dropped. It
  has low impact today, but the saved-templates config key would inherit it.
- `bob-cli-83` ("Expand template" Mac action) is READY and unbound. It replaces a
  template draft with its expansion, which is fatal under a literal pop and harmless
  under a checkout.

---

## 3. Resolving the disagreements

### 3.1 Who owns the store: bob (cdx, cld) or the Mac app (grk, mus, gem)

The best case for the Mac app: it is the stash's sibling, it needs no bob change, its
picker opens with zero latency, and the thin-client decision lets the app own
"settings-like" state. mus and gem both proposed it for v1, with bob as a v2 evolution.

**Verdict: bob.** The stash holds *panel text*, a UI artifact. A saved template is a
*capture-language object*: which lines form the block, how it is normalized, whether it
is valid, and what identifies it are all grammar answers. In a Mac-owned design, Swift
has two options:

- **slice the draft using bob's parse ranges** (grk), and live with a stale-parse race
  at submit; grk's own risk #1;
- **re-parse `@@template:` in Swift** (gem's `extractTemplateSkeleton`), which is
  exactly what the decision rejects as "the current pain amplified".

bob ownership also gives:

- **terminal parity:** the request names "the `bob capture` command";
- **in-process atomic replace** of the original on a checkout;
- **one shelf** for any future frontend (Raycast, a shell function, an iOS Shortcut).

The cost is a new sibling command and cross-repo version gating. Both are routine here:
`capture-pomodoros --tasks` shipped the same way, with an "unsupported option" fallback
in `BobProcessClient`. A Mac-first v1 would also mean migrating the file and its
contract in v2, which is real churn for a store that holds user-curated assets.

Latency is handled the way the idle agenda handles it: cache the list in memory,
revalidate on panel show and after every capture, save, or delete, and open Control-T
from the cache instantly.

### 3.2 What "pop" means: checkout (cdx, cld) or copy (grk, mus, gem)

| After picking template **A** | Literal pop | Plain copy (mus, gem) | **Checkout** (recommended) |
| --- | --- | --- | --- |
| Capture succeeds, A unchanged | A re-added on top | A bumped | A bumped |
| Capture succeeds, edited to A′ | A′ only | A′ **and** A (near-duplicates) | **A′ only** (A removed in the same call) |
| Discard, Control-C, wrong pick then clear | A **lost** | A kept | A kept |
| Quit or crash after Escape | A **lost** | A kept | A kept |
| Expand (`bob-cli-83`), then capture | A **lost** | A kept | A kept |
| Failed capture | A missing until resolved | A kept | A kept |

grk's `activeTemplateId` is a checkout under another name. The remaining design choice
is *where the replace happens*:

- **Mac-driven delete after success** (cld): two processes, and a failure leaves a
  harmless duplicate.
- **bob does it in-process** from a hidden `--template-origin <ID>` on the single
  `bob capture` call (cdx): one locked write, nothing left half-done.

**Adopt the in-process replace.** It is the same amount of code and has no second
failure point.

### 3.3 Save reliability: best-effort after commit (cld) or a staged commit participant (cdx)

cdx would stage the template file alongside the vault writes and report capture success
only if the template file was also written. Rejected:

- It lets a convenience store **block real captures**: an unreadable, full, or
  locked-out `templates.json` would refuse a template capture.
- By cdx's own analysis, it is still not crash-atomic across files.

The vault write is the primary effect. **Save after the commit, best-effort.** On
failure, return exit 0 with a `template_not_saved` warning, which the Mac app shows in
the status line. The worst outcome is a template that was not saved, and under checkout
the original still exists, so failures converge to "nothing lost".

### 3.4 Identity: a content hash (cld) or UUID plus revision (cdx)

**Use a content hash.** `id` = the first 12 hex digits of SHA-256 over the canonical
block text.

- Identical templates *are* the same entry: deduplication comes free, and `delete` is
  idempotent.
- An edit simply yields a new id, and the origin replace removes the old one.
- Ids are immutable values, so there are no revisions, compare-and-swap, or conflict
  UI: a concurrent delete of the origin is a no-op.
- When names or pins arrive, the origin replace carries those fields over.

### 3.5 Smaller splits

| Question | Options | Verdict |
| --- | --- | --- |
| Data vs state directory | XDG data (cdx), XDG state (cld) | **State.** Matches every existing bob precedent (no data-dir helper exists). XDG lists "recently used" items under state. |
| Capacity | Unbounded (cdx), 36 (cld), 12 (grk), 10 (mus) | **36 plus LRU**, so the accelerator alphabet is fully used. Templates accumulate slowly; a small cap would evict regulars. |
| Search | Field (cdx), accelerators (others) | **Accelerators.** Typing must select instantly, as in the stash. Revisit past roughly 20 entries. |
| Delete All | Picker Shift-D (cld, gem, mus), Settings only (cdx, grk) | **Settings plus CLI.** It is a rare action and does not deserve a permanent footer slot. Keep the stash alphabet (no `D`) so row *n* has the same key in both pickers. |
| Confirm a single delete | Immediate (grk, gem), undo (cdx), second press (cld) | **Second press (⌫⌫).** It needs no undo protocol in bob, and the row shows a red "Delete?" capsule while armed. |
| Shared picker code | Generalize (cld), copy (grk) | **Share the pure helpers** (accelerator alphabet, wrap selection, height policy, keycap style) in `CaptureCore`, but keep separate models and views. The two pickers differ in semantics. |

---

## 4. Recommended design

### 4.1 Lifecycle

```text
                ⌃T, pick A
   shelf ──────────────────────▶ checked out: A's block in the draft,
     ▲                           origin = A (memory only), A still on disk
     │                               │
     │  abandon: Discard · ⌃C ·      │  capture succeeds (bob saves the used block;
     │  editor emptied · ⌘Z of the   │  if it changed, bob removes A in the same
     │  insert · header deleted ·    │  locked write)
     │  quit · crash                 ▼
     └──────── A unchanged ◀──── A or A′ on top of the shelf
```

| Event | Draft | Shelf and disk |
| --- | --- | --- |
| Pick A | Block inserted; caret on the first row line; `origin = A` | Untouched |
| Escape or hide | Retained | Checkout kept (in memory) |
| Capture fails | Kept, with bob's error | Untouched |
| Capture succeeds, A unchanged | Cleared | A to the top; `use_count + 1` |
| Capture succeeds, edited to A′ | Cleared | A′ saved on top; A removed (`status: "replaced"`) |
| ⌘S in the template draft | Kept | A′ saved and A removed; `origin` becomes A′ |
| Discard, Control-C, editor emptied, ⌘Z of the insert | — | Checkout released; A untouched |
| The parse stops reporting a template (header deleted, Expand) | — | **Checkout released immediately**, so a stale origin can never attach to unrelated text later |
| Quit or crash | Retained draft lost (existing behavior) | A untouched; nothing to recover |

**Control-C on a checked-out draft:** the stash keeps the full draft without its
origin. A later restore-and-capture saves by content, so an edited version lands
*beside* A. cdx and cld both accepted this rather than extend the stash schema. The
status reads "Draft stashed · template kept".

### 4.2 bob-cli

**Store.** `bob_cli_state_dir()/capture/templates.json`, with lock file
`templates.lock`. `BOB_CAPTURE_TEMPLATES_FILE` overrides the path (following the
`BOB_VAULT_SYNC_STATE_FILE` precedent).

- **Permissions:** directory 0700, file 0600.
- **Writes:** lock, read, modify, write a temp file, rename, then fsync the directory.

```json
{
  "schema_version": 1,
  "templates": [
    {
      "id": "9c1f0e2a7b3d",
      "text": "Apply to {0}! @job^apply-{1}\n- **URL**: {2}",
      "first_saved_at": "2026-10-16T09:12:44-04:00",
      "last_used_at": "2026-10-16T09:40:02-04:00",
      "use_count": 3
    }
  ]
}
```

- **Canonical `text`:** the analyzed block lines, header excluded. CRLF becomes LF and
  trailing spaces and tabs are trimmed per line. Indentation, braces, quotes, and
  literal text are preserved.
- **Order:** most recently used first. Evict the oldest entry past the cap.
- **Forward compatibility:**
  - Preserve unknown per-entry fields when rewriting (serde flatten), so later additive
    fields such as `name` or `pinned` survive an older bob.
  - A **newer `schema_version` is read-only** for an older bob: it warns and never
    quarantines or rewrites. This file is shared by every bob on the machine (cld).
  - An unreadable file is renamed to `templates.corrupt.json`; bob warns and starts
    empty. The bytes are kept, matching the stash pattern.
- **Config:** a key for the cap (proposed `capture.saved_templates`; settle the exact
  spelling in the plan). `0` stops saving and never deletes the file; only `clear`
  does.

**`bob capture` (additive).**

- **When it saves:** after `commit_capture_batch` succeeds, on a real run, when
  `batch.template.is_some()` and saving is enabled. bob re-runs `analyze(raw_text)`,
  canonicalizes, and upserts.
- **Origin replace:** with the hidden `--template-origin <ID>`, if the new id differs
  from `ID`, bob removes `ID` in the same locked write. A missing origin is a no-op.
- **JSON:** `template.saved = {"id": "…", "status": "new" | "updated" | "replaced"}`.
  It is absent on a dry run, when saving is disabled, or when the save failed.
- **Failure:** a stderr warning plus a `template_not_saved` warning in JSON; the exit
  code stays 0.
- **Human output:** `template  3 rows · lines 5–7 · saved`.
- **Never touches the store:** `-E`, `--dry-run`, failed captures, drafts without a
  header, and `capture-parse` / `capture-complete`.

**`bob capture-templates`** goes in the Capture protocol help section and the `bob <TAB>`
group. The bare form is the flag-only, read-only `list`, which `cli_rules` allow.

```text
bob capture-templates [list] [-f, --format human|json]
bob capture-templates show <ID|N>               # raw insertable draft; pipes cleanly
bob capture-templates save [-f json] < DRAFT     # validate the block, ignore rows, upsert
bob capture-templates delete <ID|N>... [-f json] # idempotent
bob capture-templates clear [-f json]            # delete the file and its quarantine copy
```

- **`save`** accepts the same hidden `--template-origin`. It validates the
  *definition* only: factor block-level issues apart from row issues (cdx). The calm
  `template_missing_rows` state is accepted.
- **Human `list`** prints each block with bob's usual colors and a dim
  `3 fields · job · used 3× · 2d ago`.
- **JSON `list`** gives everything the app needs to render and insert **without
  parsing**:

```json
{
  "ok": true, "schema_version": 1, "capacity": 36,
  "file": "/Users/bryan/.local/state/bob-cli/capture/templates.json",
  "templates": [{
    "index": 1, "id": "9c1f0e2a7b3d",
    "text": "Apply to {0}! @job^apply-{1}\n- **URL**: {2}",
    "draft": "@@template:\nApply to {0}! @job^apply-{1}\n- **URL**: {2}\n\n",
    "cursor": 57, "field_count": 3, "line_count": 2,
    "route": "job", "mode": "task",
    "spans": [{"start": 9, "end": 12, "kind": "template_placeholder", "field": 0}],
    "first_saved_at": "…", "last_used_at": "…", "use_count": 3
  }],
  "warnings": []
}
```

- **Field meanings:**
  - `draft` and `cursor` (a UTF-8 offset) are decided by bob.
  - `spans` index into `text`. bob computes them by parsing `@@template:\n` + `text` in
    process; at 36 entries that costs microseconds.
  - `file` makes any environment divergence visible.

### 4.3 Bob Mac Capture

**Keys**

| Key | In the editor | Template shelf open |
| --- | --- | --- |
| **⌃T** | Open the shelf (see the rules below) | Close the shelf |
| `1–9 0 A–C - E–Z` | — | Use that template |
| ↩ | — | Use the selected template |
| ↓ / ⌃N, ↑ / ⌃P | — | Move the selection (wraps) |
| ⌫ | — | Arm delete (red "Delete?" capsule); ⌫ again deletes; any other key disarms |
| ⌃S | Stash picker (unchanged) | Close the shelf, open the stash (stash rules apply) |
| Esc / ⌃[ | — | Close the shelf only |
| **⌘S** | Save template (template drafts only; otherwise a status hint) | — |

In the stash picker, ⌃T closes the stash and opens the shelf. A test should pin that a
modified `T` never reaches the stash's `T` accelerator.

**Opening rules.**

- **Prompt or picker open:** the key is consumed with the stash's "finish or cancel …"
  statuses.
- **Empty draft:** opens.
- **Draft that the latest parse says has no template:** opens; using a template
  *inserts it at the top*.
- **Draft with a template:** stays closed, with the status "This draft already has a
  template".
- **Empty shelf:** "No saved templates yet. Capture an `@@template:` draft and it lands
  here."
- **Old bob:** "Update bob to use saved templates", and the footer button is hidden.

**Using a template.**

- **Empty draft:** install `draft` with the caret at `cursor`.
- **Rows present:** insert `draft` at offset 0; the caret shifts with the insertion.
- **Both cases:** apply the change as one native, undoable edit
  (`breakUndoCoalescing()` + `insertText(_:replacementRange:)`, as Control-J and
  Control-Shift-O do), then set `origin`.
- **Immediately after:**
  - slot colors appear on `{0} {1} {2}`;
  - the calm `template_row` state shows bob's A10 wording;
  - Control-J already inserts a plain newline in template drafts, so the first row
    never grows a stray `- `.

**Settling.**

- **Submit with a checkout:** pass `--template-origin <id>` only when the current parse
  still has a template and bob advertises support.
- **Status after a successful capture:**
  - `new`: "Captured 12 items · Template saved — ⌃T to reuse". This teaching moment
    appears once per new template, and it is how the feature becomes discoverable.
  - `replaced`: "Template updated".
  - plain `updated`: silent; the footer count is the tell.
- **⌘S:** calls `capture-templates save`, keeps the draft, and announces "Template
  saved".

**Presentation**

```text
╭─ Templates ──────────────────────────────────────────────── 3 ─╮
│ ┃1┃  Apply to {0}! @job^apply-{1}                    ● ● ●      │ ← selected
│      - **URL**: {2}                            job · 14× · 2h ago │
│ ┃2┃  Read {0} @reading^{1} p:2                       ● ●        │
│                                             reading · 5× · 3w ago │
│ ┃3┃  {0} @groceries                                  ●          │
│                                           groceries · 1× · 6d ago │
├──────────────────────────────────────────────────────────────────┤
│  ↩ use    ⌫ delete    ⌃S stash    esc close                       │
╰──────────────────────────────────────────────────────────────────╯
```

- **Same family as the stash:** the same auxiliary region, `.regularMaterial`, corner
  radius, shadow, 24×22 keycaps, five visible rows then scroll, and selected-row
  accent fill (0.18, or 0.32 under Increase Contrast). Moving between ⌃S and ⌃T should
  feel like one system.
- **Faithful previews:**
  - Each row's `spans` become an `AttributedString` through `CaptureEditorPalette`:
    `{k}` uses slot hue `k % 6`, and `@job^` uses the route color. A row looks
    exactly like what lands in the editor.
  - The parent line is at full strength, one child line in secondary color, then
    "+N more lines".
  - The title is never `@@template:` (every row would read the same).
- **Slot dots:** `field_count` circles in slot hues, capped at six then `+N`. The count
  is also in the VoiceOver label and the tooltip, so color is never the only cue.
- **Metadata:** route · uses · age, reusing `relativeAgeDescription`.
- **Footer button:** **Templates N** with `square.stack.3d.down.right`, the glyph the
  `@@template:` completion row already uses, so the two read as one feature. It sits
  left of **Stash N** and is disabled under the same conditions.
- **A quiet hint row** replaces the stash's red Delete All bar.
- **Optional polish:** a ghost hint `{0} {1} {2}` in slot hues on the empty row line,
  gone on the first keystroke. It is derived from `field_count`, so it stays
  thin-client clean.
- **Accessibility and motion:**
  - list label: "Saved templates, 3 entries";
  - row label: "Template 1, Apply to {0}…, 3 fields, job, used 14 times, 2 hours ago";
  - Reduce Motion respected; no celebration animations.
- **Settings:** a "Saved Templates" section shows the count and the bob-reported file
  path, with a confirmed **Clear Templates…** that calls `capture-templates clear`.
  The cap lives in bob config, not `UserDefaults`.

**Freshness and compatibility.**

- **Cache:** an in-memory list, revalidated on panel show and after every capture,
  save, or delete.
- **New fields:** decoded with `decodeIfPresent`.
- **New bob with an old app:** templates save silently.
- **New app with an old bob:** the feature is hidden; ordinary capture is unaffected.
- **Vanished entry** (deleted from a terminal): "Template is no longer available", and
  the list refreshes.

---

## 5. Risks and edge cases

| # | Risk | Handling |
| --- | --- | --- |
| R1 | A stale origin attaches to unrelated text and deletes A | Release the checkout as soon as the parse shows no template or the editor is empty. Send the origin only while the draft is still a template. |
| R2 | Editing a picked template when Bryan wanted a fork | By design, edits replace (the requested pop semantics). Document it. Follow-up: ⌥↩ "use as copy" (no origin). |
| R3 | Save fails (disk, permissions, lock timeout) | The capture still succeeds; a `template_not_saved` warning shows in the status line; the original is untouched. |
| R4 | The Mac app and a terminal write at once | Exclusive lock plus atomic rename. Content ids make retries idempotent. |
| R5 | An older bob meets a newer file | Read-only plus a warning; never quarantined or rewritten. |
| R6 | A CLI capture with forced `-r/-s/-t` | Only the block is saved; the forced destination is not. Document it. The app never passes these flags. |
| R7 | One-off templates crowd out regulars | Recency order, a cap of 36, and ⌫⌫. Pinning is the follow-up if eviction ever removes a regular. |
| R8 | Privacy | Rows are never stored. Blocks can still hold routes, ID patterns, and literal URLs, so the file is 0600, never logged, and `clear` removes the quarantine copy. Name the file in the README privacy section. |
| R9 | The app and terminal resolve different state directories | Verified identical today (no `XDG_STATE_HOME` in the dotfiles). `list -f json` reports `file`. Optionally add `XDG_STATE_HOME` and `BOB_CAPTURE_TEMPLATES_FILE` to `preservedOverrideKeys`, and fix `BOB_CONFIG` → `BOB_CONFIG_FILE` there. |
| R10 | Agents run template captures on apollo or athena | Their templates go to that host's shelf, which is good isolation. The config off switch is per host. |
| R11 | Loss of transpose (Control-T) | A deliberate, documented trade, in the same family as the app's existing Control-A/E/U/J/K/S/C overrides. |

---

## 6. Implementation phases

1. **bob-cli: store, save, protocol (medium).**
   - **Code:**
     - a `src/native/capture_templates/` module (`store.rs`: canonicalize, id, load,
       upsert, evict, delete, clear, lock, quarantine, newer-schema guard, unknown-field
       preservation; plus `cli.rs`);
     - the post-commit save in `capture()`;
     - the hidden `--template-origin`;
     - the additive `template.saved` JSON and the `template_not_saved` warning;
     - the human ` · saved`;
     - the config key and `BOB_CAPTURE_TEMPLATES_FILE`;
     - `capture-templates list|show|save|delete|clear`, with help, completion groups,
       and alphabetized options;
     - the A10 wording.
   - **Docs:**
     - `docs/capture.md` § Saved templates, after § Bulk templates;
     - the README protocol table;
     - the config docs.
   - **Store tests:**
     - normalization (CRLF, trailing whitespace, Unicode, escaped braces, indentation);
     - id stability, dedup and bump, eviction, cap 0;
     - a corrupt file, a newer schema, unknown-field round trip;
     - 0600/0700 permissions.
   - **CLI tests:**
     - saves after a real capture, but never after `--dry-run`, `-E`, a failed
       capture, a headerless draft, parse, or complete (assert that the store bytes and
       path stay absent);
     - one row and many rows save identically;
     - origin replace and the missing-origin no-op;
     - `save` with no rows, and `save` refusing invalid blocks;
     - JSON shapes (`draft`, `cursor`, `spans`), `delete` idempotency, `clear`;
     - a save failure keeps exit 0.
   - **Done when:** `just check` passes.
2. **Bob Mac Capture: the shelf (medium).**
   - **Code:**
     - models for the list response and `CaptureTemplateSummary.saved`;
     - `BobProcessClient` list, save, delete, and clear, with feature detection;
     - a `SavedTemplateShelf` holding the cache, `origin`, and armed delete;
     - router cases for ⌃T, the shelf keys, ⌘S, and ⌃T↔⌃S switching;
     - both insert modes as single native edits;
     - settlement in `completeSubmit`, `discardDraft`, `stashDraftAndClose`, empty
       editor, and parse-without-template;
     - the view on the shared picker helpers, the footer button, Settings, and README
       sections (keyboard, privacy, compatibility).
   - **Tests:**
     - router mapping;
     - every lifecycle row in §4.1;
     - "digits in the shelf never hit the close-comma assist";
     - light and dark render fixtures for a three-slot row.
   - **Fixtures:** record them from a Phase 1 bob into `Tests/Fixtures/fake-bob`.
   - **Compile per `AGENTS.md`:** run `just portable-check` (on athena if `swift` is
     missing), then a scratch build on the Mac with `bundle.sh` and
     `just typecheck-tests`. Never land Swift that has not been compiled.
3. **Memory (small; ask Bryan first via `/sase_memory_write`).**
   - A decision record: "Saved Capture Templates Are bob-Owned And Checked Out, Not
     Popped". Its alternatives are §3.1–3.3; it reopens when cross-machine reuse or
     naming is needed.
   - A glossary term, **Saved Template** (alias: template shelf).
   - A note on `bob-cli-83` to keep it off ⌃T.

**Follow-ups (not v1):**

- pin;
- names (the schema already round-trips unknown fields);
- ⌥↩ use-as-copy;
- saved templates as `@@` completion candidates (cld);
- applying a template to rows in a draft that already has one (needs a bob edit
  endpoint);
- an explicit "promote to vault" export, or cross-machine sync, if Bryan starts
  templating from apollo.

---

## 7. Open questions for Bryan

1. **Checkout or literal pop?** Checkout is recommended: it behaves identically on every
   success path and differs only where a literal pop would lose the template.
2. **Clear-all only in Settings and the CLI** (recommended), or an armed Shift-D in the
   picker for stash parity?
3. **Prefix insert on rows-first drafts (A7)** in v1, or empty-draft-only like the
   stash?
4. **A per-machine shelf** on the Mac (no vault sync) — enough?
5. **Cap 36 with LRU**, or pinning in v1?

---

## Recommended solution

Ship a **bob-owned shelf of recently used templates behind a stash-style Control-T
picker, with checkout semantics**, in two phases (bob first, then the Mac), under the
thin-client decision.

- **bob-cli.**
  - **Saving:** every successful, non-dry-run template capture upserts its canonical
    *block* (never rows) into `~/.local/state/bob-cli/capture/templates.json`. Ids are
    content hashes, entries are most recent first, the cap is 36, writes are locked,
    atomic, and 0600, and an older bob never rewrites a newer file.
  - **Failure:** saving happens after the commit and is best-effort; it never fails a
    capture.
  - **Origin:** a hidden `--template-origin` lets the same `bob capture` call replace
    the checked-out original.
  - **Protocol:** `bob capture-templates list|show|save|delete|clear` hands the app
    ready-to-insert `draft`/`cursor`, `spans`, `field_count`, `route`, uses, and age,
    so Swift never parses anything.
  - **Wording:** the missing-rows message gets the one-line A10 fix.
- **Bob Mac Capture.**
  - **Opening:** Control-T opens a shelf on an empty draft or one without a template.
  - **Look:** it shares the stash's material, keycaps, accelerators, and rhythm. Rows
    are syntax-colored previews whose placeholder hues and slot dots match the editor.
  - **Picking:** checks the template out, inserts it as one undo step, and puts the
    caret on the first row.
  - **Settling:** a successful capture puts it back on top, edited if you edited it;
    abandoning leaves it untouched; ⌘S saves without capturing.
  - **Deleting:** ⌫⌫ removes one entry; clear-all lives in Settings.
  - **Discovery:** the first save of a new template teaches "⌃T to reuse" in the
    success status.

This keeps everything Bryan asked for: automatic saving, Control-T, stash-like browsing,
and the pop feel of a template leaving the shelf when picked and returning when used.
It removes the one way the literal request could quietly destroy a curated template.

---

### Sources

- **Researcher reports in this directory** (originals registered as `research:`
  artifacts):
  - `capture_template_shelf__cdx.md`: recoverable pop, staged commit, invocation
    defaults;
  - `capture_template_shelf__cld.md`: bob-owned shelf, borrow, content-hash ids, A10
    wording;
  - `capture_template_shelf__grk.md`: a library owned by the Mac app, slot dots,
    Control-Shift-T save, and an infographic
    (`saved_capture_templates_infographic.jpg`);
  - `capture_template_shelf__mus.md`: narrowed auto-save, copy-out;
  - `capture_template_shelf__gem.md`: a non-destructive library, an Edit Mode, and
    visual spec.
- **Internal context** (audited reads):
  - `plan:202610/bulk_capture_templates.md` (out of scope #5; reserved header options);
  - beads `bob-cli-7w` and `bob-cli-83`;
  - memory `cli_rules.md`;
  - decisions `mac-capture-is-a-thin-client` and `idle-capture-shows-ledger-agenda`;
  - glossary entries Capture and Bulk Capture.
- **bob-cli code:**
  - `src/native/capture/mod.rs` (`capture()`);
  - `src/native/capture/cli.rs:566–676`;
  - `src/native/capture_language/template.rs:39–84, 219, 446–460`;
  - `src/native/env.rs:256–306`;
  - `src/native/ref_jobs/spool.rs:32–34`;
  - `src/native/config/mod.rs:25`;
  - `tests/cli/support.rs:54`.
- **bob-mac-capture code:**
  - `Sources/BobMacCapture/CaptureKeyCommandRouter.swift:86–151, 454–492`;
  - `Sources/BobMacCapture/CanceledDraftStash.swift:13–14, 236–239`;
  - `Sources/BobMacCapture/CapturePanelModel.swift:1927–2045`;
  - `Sources/CaptureCore/BobEnvironment.swift:40–65`;
  - `Sources/CaptureCore/CaptureModels.swift` (`CaptureTemplateSummary`);
  - `Sources/BobMacCapture/CapturePanelController.swift:794–852` (native undoable edits);
  - `README.md` ~L1185–1200.
- **chezmoi:** a repo-wide grep finds no `XDG_STATE_HOME` export.
- **External:**
  - [Apple: Mac keyboard shortcuts](https://support.apple.com/en-us/102650) (Control-T
    transposes characters);
  - [Raycast: Clipboard History](https://manual.raycast.com/clipboard-history)
    (auto-saved, recency-ordered history with pin and delete);
  - [XDG Base Directory spec](https://specifications.freedesktop.org/basedir/latest/)
    (the state vs data distinction).

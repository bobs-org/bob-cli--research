# Persisting capture templates: auto-save on use plus a Ctrl+T library modeled on the stash

Research report (swarm member `mus`). Goal: help decide the best way to add
"templates persist to disk automatically when used, viewable/editable in
bob-mac-capture behind Ctrl+T, stash-style with pop-on-select" on top of the
recently landed `@@template:` bulk-capture support.

## 1. Where things stand today

### 1.1 Bulk templates (`@@template:`) are in-draft only

The `bob-cli-7w` epic (closed) added bulk capture templates. Current behavior,
grounded in `src/native/capture_language/template.rs` and `docs/capture.md`
("Bulk templates"):

- A draft whose first nonblank line is `@@template:` declares a template block
  (one item: parent line plus optional authored children, with `{0}`, `{1}`, …
  placeholders), then a blank separator, then one row of values per capture.
- Capturing the draft is exactly capturing its `bob capture -E` expansion,
  all-or-nothing through the unchanged planner. Row errors are row-scoped with
  coded diagnostics (`template_row_arity`, `template_clipboard`, …).
- Hard limits: 1,000 rows, 1 MiB expanded text. Clipboard markers and Pomodoro
  session operators are refused inside templates (they cannot safely repeat).
- `capture-parse` / `capture-complete` / Bob Mac Capture are template-aware
  (masked copy, placeholder/field spans, `template:` header candidate, calm
  header-only state, preview chip).
- **Saved or reusable templates were explicitly out of scope** for that epic
  (`sase/repos/plans/202610/bulk_capture_templates.md`, "Out of scope", item 5:
  "Saved or reusable templates (snippet or vault note)"). So this feature is a
  genuine v2, not a leftover bug.

### 1.2 The capture stash is Mac-only, and that matters

There is **no stash in bob-cli** (a repo-wide search for "stash" in `src/`,
`scripts/`, `tests/`, `docs/` finds only unrelated "canceled task" hits). The
stash is entirely a Bob Mac Capture concept:

- `Sources/BobMacCapture/CanceledDraftStash.swift` — in-memory model:
  capacity default 10 / max 36, newest-first, `push` on discard,
  `remove(id:)` on restore, `clear`, selection helpers.
- `Sources/CaptureCore/CanceledDraftStashStore.swift` — disk persistence:
  `~/Library/Application Support/org.bobs.bob-mac-capture/canceled-draft-stash.json`,
  `{schemaVersion, drafts[{id, text, createdAt}]}`, file mode `0600`, corrupt
  files quarantined to `canceled-draft-stash.corrupt.json`, empty stash deletes
  the file so no captured text rests on disk.
- `Sources/BobMacCapture/CapturePanelModel.swift` (`restoreStashEntry`) —
  restore works **only into an empty draft**, then pops the entry.
- `Sources/BobMacCapture/CaptureKeyCommandRouter.swift` — `Ctrl+S` toggles the
  stash picker, `Ctrl+C` stashes the draft and closes. The picker reuses the
  app's standard picker chrome (list, keyboard navigation, clear-all).

The governing rule is the `decisions:mac-capture-is-a-thin-client` record:
bob-cli owns capture grammar, completion, preview, and vault mutation; the app
owns presentation, orchestration, hotkey, settings, and packaging, and never
re-implements grammar in Swift. The stash does not violate this because a
canceled draft is app-local UI state, not grammar or vault data. **A template
library sits exactly on this boundary**, which drives the main design decision
in §4.

### 1.3 Keymap landscape

`Ctrl+T` is currently **unbound** in `CaptureKeyCommandRouter` (there is no
`KeyCode.t` case), so the requested binding is free. Two caveats:

- `Ctrl+S` (stash picker) and `Ctrl+C` (stash-and-close) are the neighbors;
  `Ctrl+T` for "templates" is mnemonic and sits in the same family. Good fit.
- AppKit's `NSTextView` binds `Ctrl+T` to Emacs `transpose-chars` by default.
  The router returning a command for `Ctrl+T` will shadow that. Transpose is
  near-useless in a capture box, but the change should be deliberate and noted
  in the keymap docs, not accidental.

## 2. Critique of the proposal as stated

**Short answer: the direction is good, but three of the four stated mechanics
need adjustment.** Auto-remembering templates is genuinely valuable (Bryan's
motivating case — repeated "apply to N roles" waves — reuses a handful of
shapes), and a stash-like picker is the right UI idiom for this app. The
problems are all in the details.

### 2.1 "Persist automatically when they are used" — yes, but narrow it

Unqualified auto-save has four failure modes:

1. **Surprise retention.** A template draft's rows often contain the sensitive
   part (company names, URLs, contacts). Persisting the whole draft on every
   submit turns a convenience into a silent log of everything Bryan ever bulk
   captured. The stash avoids this by saving only on explicit discard.
2. **Duplicates.** The same template submitted weekly yields N identical
   entries unless saving is content-addressed. The stash never dedupes because
   each canceled draft is a distinct event; templates are the opposite —
   identity is by content.
3. **"Used" is ambiguous.** Does typing `@@template:` and submitting count, or
   only a successful capture? What about a failed validation, a dry run, or an
   expansion preview (`-E`)? Saving drafts that never captured pollutes the
   library with broken shapes.
4. **No consent or off-switch.** The stash has capacity 0 as a kill switch and
   Clear as an escape hatch. Auto-save needs the same from day one.

**Adjustment (justified): save the template block only — never the rows — on
successful submit only, deduped by content hash, with a capacity and a
disable.** The reusable asset is the `{0}`-shaped block; the rows are per-run
data. This keeps the privacy story clean ("the library remembers shapes, never
your data") and makes dedupe natural.

### 2.2 "Pop when selected, re-added on submit" — do not do this

This is the weakest part of the proposal. Pop semantics are correct for the
stash (a canceled draft is a one-shot event: restoring it consumes it) but
wrong for a library:

- **Crash/loss window.** Between pop and submit the template exists only in
  the editor. A crash, a failed capture, or an accidental Esc loses a curated
  template that the user never asked to delete.
- **Failed submits delete things.** Capture fails atomically all the time
  (one bad row rolls everything back). Under pop-and-re-add, a failed submit
  has silently consumed the library entry; the re-add only happens on success.
  Punishing failure with data loss is backwards.
- **Editing becomes scary.** "View/modify saved templates" plus pop means
  opening a template for a look removes it from the library until you submit a
  capture you may not want.
- **It buys nothing.** The stated rationale seems to be symmetry with the
  stash, but the stash pops to prevent restoring the same draft twice. Double
  "restore" of a template is harmless — it just fills the editor again.

**Adjustment (justified): selecting a template copies it into the editor
(non-destructive); the library entry persists until explicitly deleted.**
Usage recency can still be tracked (bump a `lastUsedAt` for sorting) without
removing anything. Explicit Delete key + Clear-All in the picker covers
removal, mirroring the stash picker's existing affordances.

### 2.3 "Works in a similar way to the capture stash" — reuse chrome, not model

The right reuse is the **picker chrome and the file-store pattern**
(schema-versioned JSON, `0600`, quarantine-on-corrupt, delete-when-empty,
capacity clamp), not the push/pop lifecycle. Concretely: one generic
"draft library picker" look, two stores underneath with different lifecycles
(stash = stack with pop; templates = library with copy-out). Users get visual
consistency; the code does not inherit the wrong semantics.

### 2.4 "I want you to lead the design… beautiful" — scope the beauty

The beauty risk here is a second full library UI (naming, folders, search,
sync). The beautiful version of v1 is restraint: the template picker looks and
feels exactly like the stash picker, entries render with the existing
slot-colored placeholder styling from the 7w Mac phase, and each row shows an
expansion preview ("3 placeholders · last used Tue"). Naming can wait (derive
a display title from the first line, truncated); folders and search can wait
(capacity ≤ 36 keeps the list scannable, same ceiling as the stash).

## 3. The one structural question: who owns the store?

| Option | Store lives in | CLI users get it | Cost |
|---|---|---|---|
| A. Mac-only JSON (stash twin) | `…/Application Support/…/saved-templates.json` | No | Small; no bob-cli change |
| B. bob-cli-owned library | e.g. `~/.config/bob/templates/` + `bob capture --save-template` / `--template <name>` | Yes | Medium; new CLI surface, `cli_rules.md` applies |
| C. Vault note | e.g. a managed section in a config note | Yes, synced | High; conflicts with thin-client + Obsidian sync races |

The thin-client record pushes grammar-adjacent behavior into bob-cli, but a
template **library** is arguably settings-like (cf. stash capacity living in
`AppSettings`), and option A ships without touching the frozen `bob capture`
surface (`cli_rules.md`: never add a subcommand under `bob capture`; the
`capture-*` protocol names grow only additively). Option B is the better end
state for a CLI-first user — Bryan captures from the terminal too, and a
Mac-only library strands those templates — but it needs CLI design (naming,
listing, expansion by name) that doubles the scope.

**Recommendation: build A now, design B's names so A can migrate.** Keep the
persisted schema CLI-shaped from day one (`{schemaVersion, templates[{id,
body, createdAt, lastUsedAt, useCount}]}` where `body` is exactly the bytes
`bob capture` would accept after the header), so a later `bob template`
command can adopt the same file or import it. Do not do C: vault writes from
the app break the thin-client rule and invite sync conflicts for zero benefit
(templates are device-local conveniences, not notes).

## 4. Recommended solution (v1)

1. **Auto-save, narrowed.** On every *successful* `bob capture` of a template
   draft, the app extracts the template block (header + placeholder lines,
   excluding rows), normalizes it (trim trailing whitespace, LF), hashes it
   (SHA-256, first 16 hex chars as dedupe key), and upserts into the library:
   new entry at top, or bump `lastUsedAt`/`useCount` on hash match. Rows are
   never stored. Behind a settings toggle (default on) plus capacity
   (default 10, max 36, mirroring the stash; 0 disables saving).
2. **Ctrl+T picker, stash chrome, library semantics.** `Ctrl+T` toggles a
   template picker built on the existing stash-picker view. Selecting an entry
   inserts its body into the **empty** draft (same guard message pattern as
   stash restore when the draft is non-empty) — or, better, offers both
   "insert" and, when the draft is empty, "insert and focus rows". Never pops.
   `Delete` removes one entry, with Clear-All; both need no confirmation
   beyond the stash's existing pattern.
3. **Entry rendering.** Each row shows the template's first line (monospaced,
   existing slot colors for `{N}`), a quiet second line
   (`3 fields · used 12× · Tue`), and expanding the row shows the full block.
   No user naming in v1 — content hash is the identity, first-line truncation
   is the label. (Naming is the obvious v1.1; the schema should reserve a
   `name` field now.)
4. **Store reuse.** Clone the `FileCanceledDraftStashStore` pattern:
   `saved-templates.json` beside the stash file, same `0600`/`0700`
   permissions, same quarantine-on-corrupt, same delete-when-empty, schema
   version starting at 1. Unit-test the store exactly like the stash store
   (round-trip, corrupt quarantine, capacity trim, empty deletes file).
5. **Explicit save too.** Auto-save covers the "I just used it" case, but add
   "Save current template" to the same picker (enabled when the editor holds a
   valid template draft). This rescues the case auto-save deliberately skips:
   a good shape whose submit failed validation.
6. **Docs and keymap note.** Document that `Ctrl+T` shadows Emacs transpose in
   the capture box, alongside the `Ctrl+S`/`Ctrl+C` stash entries.

## 5. Deliberately deferred (with triggers to revisit)

- **CLI parity** (`bob capture --save-template`, `--template <name>`):
  revisit when Bryan wants a terminal-captured template reused on the Mac, or
  vice versa. The schema reservation in §4.3 is the bridge.
- **Named templates, search, folders:** revisit past ~15 entries of real use;
  until then recency ordering suffices.
- **`{N|slug}` filters / named placeholders:** already queued as 7w
  follow-ups; the library stores template *bodies* opaquely, so it composes
  with any future placeholder syntax unchanged.
- **Sync between devices:** out of scope until CLI parity exists; syncing App
  Support JSON by hand is worse than no sync.

## 6. Acceptance sketch

- Submit a template draft → success → library gains exactly one entry with
  the block body; resubmit → no duplicate, `useCount` bumps.
- Failed submit → library untouched. Rows never appear on disk (grep the JSON).
- `Ctrl+T` → picker lists entries newest-used-first; Enter inserts into empty
  draft; non-empty draft → calm guard message, library unchanged.
- Delete/Clear-All work; capacity 0 disables saving; corrupt JSON quarantines
  and starts empty (same messages pattern as the stash).
- `just check` (bob-cli untouched) plus the Mac portable suite green;
  keymap docs updated.

## 7. Open questions for Bryan

1. Is "template block only, never rows" the right privacy line, or do you
   want an opt-in "keep last rows as an example" per template?
2. Should Ctrl+T insert into a non-empty draft (append after a blank line)
   instead of requiring an empty draft like the stash does?
3. Default capacity 10 like the stash, or smaller (say 5) since templates
   accumulate more slowly than canceled drafts?

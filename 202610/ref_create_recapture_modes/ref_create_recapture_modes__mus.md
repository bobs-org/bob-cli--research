# `bob ref create --force <mode>`: reread vs overwrite duplicates

- Researcher: mus (independent report, 2026-10-25)
- Request: add `-f|--force <mode>` (`overwrite` | `reread`, bare flag defaults to
  `reread`) to `bob ref create`, so re-capturing an already-captured source is an
  explicit, designed act instead of a refusal.
- Verdict up front: the feature is worth building, but **not as specified**. Keep the
  two modes, keep bare-`-f`-means-`reread`, but (1) do not introduce a `__v<N>` suffix
  dialect — reuse the existing `_2`, `_3` walk; (2) do not delete-and-recreate on
  `overwrite` — do refresh-in-place and let git stay the archive; (3) resolve the
  collision with the *existing* boolean `-f/--force` deliberately, because that flag
  already exists with a different meaning. Details in §5.

## 1. How `bob ref create` dedupes today

All paths below verified in this workspace (`src/native/highlights_ref/`,
`src/native/ref_library/`, `docs/ref.md`, `docs/highlights-create.md`).

### 1.1 The CLI already has a boolean `-f/--force`

`create::command()` in `src/native/highlights_ref/create.rs` (~line 365) defines:

- `--force` / `-f`, `ArgAction::SetTrue`, help: "Overwrite an existing target PDF".

It flows into `CreateOptions.force: bool` and is threaded through ~15 call sites
(audio install, intake overwrite, exact-output planning). Its current meanings:

1. Same-intake-target overwrite: in `stamp.rs::plan_default_target`, a candidate stem
   occupied by the *same* reference as an intake-only PDF refuses without `--force`
   (`already queued in …; pass --force to overwrite it`) and overwrites with it.
2. Companion-audio overwrite: `install_listen_audio(flow, force)` refuses on differing
   bytes without `--force`.
3. Queued-PDF overwrite via `plan_exact_output(config, output, force)`.

So the requested `-f|--force <mode>` **reuses a flag that already exists** with narrower
boolean semantics. This is the single most consequential design fact: whatever we do
must either preserve, migrate, or deliberately break the boolean behavior (see §5.1).
Note `docs/highlights-create.md` documents the current behavior: "A second snapshot of
the same note on the same day refuses with `already queued` (use `-f` to replace it)".

### 1.2 Duplicate detection is two layers, not one

**Layer A — source-URL dedupe** (`sources.rs::check_dedupe`,
`find_refusing_hit`, `legacy_hits`; pre/post-capture checks in `create.rs` via
`check_dedupe_with_listen_hint`, and `ingest.rs::outcome_for_refusing_hit`):

- A `RecordedSource` is collected from every PDF-backed ref note (`source_pdf` set)
  and every queued intake PDF. Matching is on the cleaned `dedupe_key` (arXiv-aware:
  `arxiv.rs::dedupe_key`, version-stripped).
- A PDF-backed ref-note hit refuses: `already captured as <ref-note> (source_url …)`
  with hint "open the note, or delete it to recapture".
- A queued-PDF hit refuses: `already queued in <xlib path> (source_url …)` with hint
  "pass --force to overwrite the same intake target, or delete the queued PDF".
- Legacy-only notes (URL but no `source_pdf`) never refuse; they warn
  (`warn_for_legacy_hits`) and capture a fresh copy.

**Layer B — default-target walk** (`stamp.rs::plan_default_target`,
`candidate_is_same_reference`, `refuse_target_collisions`,
`ensure_reference_id_available`):

- Walks `<stem>`, `<stem>_2`, … up to `<stem>_999`. Free candidates pass; candidates
  occupied by a *different* reference are skipped with the next suffix (and the first
  skip prints `renamed: <base>.pdf is taken by <occupant>; using <final>.pdf`).
- Same-reference occupancy refuses: library/note occupants always refuse
  (`already captured as …; pass -N/--name to capture under a different name`);
  intake-only occupants refuse unless `--force`.
- Identity is route-dependent: `DefaultTargetIdentity::Url { keys, recorded }` for
  URL/PDF/arXiv/collection routes, `Title(String)` for local-title routes,
  `AlwaysDifferent` for vault-note snapshots (each snapshot is intentionally a new
  capture; see §1.4).
- Reference **id == final stem**: `DefaultTargetOccupancy` also collects every
  frontmatter `id:` under `ref/` (case-insensitive, all types) and reserves those
  stems. This implements the `reference-ids-follow-file-stems` decision. `--output`
  keeps the exact path and refuses on id collision instead of suffixing.

Per `docs/ref.md`: "Default targets add `_2`, `_3`, and so on when that candidate is
occupied … Existing references are left unchanged; use `bob ref rename` to repair an
existing id/stem mismatch."

### 1.3 Where a ref note, its annotations, and its task live

- `create` stamps a marker PDF into `xlib/<type>/<stem>.pdf`; create-time intake then
  (under `bob_sync.lock` + `scan.lock`) moves it to `lib/`, writes the `ref/` note and
  the reading task, and commits those paths together. Failures degrade to
  `queued: … · next: bob ref scan`.
- The ref note body has a managed region (`MANAGED_BODY_BEGIN/END`, see `note.rs`):
  scan rewrites it; annotation-task lines are inserted into the Tasks section
  (`insert_missing_annotation_tasks`, `render_annotation_task_line`); each note has a
  `source_pdf` / `source_pdf_sha256` provenance pair and a `^ref` reading-task line.
- Reading state is **derived, never stored** (`docs/ref.md`); `Next`/`Pending` are
  sticky lanes (`task-lanes-are-sticky`). Deleting a ref note therefore destroys: the
  note's annotations snapshot, its reading task and lane state, inbound task links /
  wikilinks, and the `ref rename`-maintained identity chain — while git history
  already preserves every prior byte. Any "delete" design must answer for all five.

### 1.4 Vault-note snapshots are a different animal

Same-note, same-day re-snapshots hit the same-reference intake refusal (fixable today
with `-f` or `-N`); different-day snapshots get dated stems and are *expected* to
coexist (`earlier: <stem> (<status>, N highlights)` lines; "Create never changes,
closes, or abandons those notes"). The requested feature is really about the
URL/PDF/Markdown/article routes, where a duplicate currently has no designed
forward path except "delete it to recapture". The design must not disturb the
snapshot flow — including the documented `-f`-replaces-queued-snapshot behavior.

## 2. Critique of the plan as written

**The core idea is good.** "Delete it to recapture" as the only path is hostile to
exactly the cases that matter: an article updated after capture, a paper v2 on arXiv,
a paywalled page re-captured via `--html`, a re-read where you want a fresh
annotation space without losing the old one. An explicit, reviewable, beautiful
duplicate path fits the product. The `reread`-as-default-bare-flag instinct is also
right: the safe, non-destructive mode should be the easiest to type.

Clause by clause:

1. **`-f|--force <mode>` reuses an occupied flag.** `-f` is taken by the boolean
   `--force`, and per `sase/memory/cli_rules.md` every public long option keeps a
   short alias — `-f` is already this option's alias. Turning a `SetTrue` flag into an
   optional-value flag is a silent behavior change for every scripted `-f` use (notably
   the documented same-day snapshot replace). Clap optional values on short flags are
   additionally awkward: `-f overwrite` reads as two arguments unless `=` is used or
   `num_args(0..=1)` + `require_equals` is configured with care. This needs a deliberate
   compatibility decision, not an accident (§5.1).
2. **`__v<N>` starting at 2 should not ship.** The codebase, docs, `find`/`list`
   output, and the id-derivation rule all speak `_2`, `_3`. A second suffix dialect
   means two sort orders, two humanization rules, special cases in
   `plan_default_target`'s walk, `occupants()`, `collect_reference_ids`, the rename
   command, and Mac Capture's Refs panel. It also reads as "version 2 of the same
   thing", which contradicts the actual semantics (a *separate* reference that happens
   to share a source). And "anywhere else that should be de-duplicated" is doing a lot
   of unexamined work in the requirement: id, stem, PDF name, task identity, and
   find-index keys all dedupe differently today.
3. **`overwrite` as "delete, stash annotations somewhere, link them" is the weakest
   clause.** Problems:
   - *Destructive core, ornamental recovery.* Deleting the note destroys reading-task
     state, lane membership, and inbound links; a "link to logged annotations" does not
     restore any of them. Git already logs everything immutably — the design should
     lean on that instead of inventing a second archive.
   - *"Somewhere" is unspecified.* A new vault location needs sync/exclusion review
     (hidden dirs and `*.assets/` are skipped by the index; `_conflicts/` has merge
     semantics), a retention story (`sase/memory/sase_artifacts.md` governs artifact
     retention thinking), and rendering in `find`/`list` (or deliberate exclusion).
   - *"Any previous ones"* chains awkwardly: overwrite→overwrite→overwrite produces a
     linked list of annotation dumps with no reader.
   - *It contradicts the documented contract* "Existing references are left
     unchanged" — which exists precisely so captures are trustworthy.
   - The genuinely useful core of `overwrite` — "the live PDF changed, re-stamp it and
     regenerate the note from the new source" — does not require deletion at all.
4. **"Throw a useful error" is already ~70% true.** Both layers refuse with the
   offending path, the matched identity, and a hint. The gap is only that the hints
   point at `-N` and manual deletion. The new error work is therefore small: name the
   new flag and its two modes in the existing hints.
5. **Collections and `--output` are unaddressed.** Multi-URL capture refuses
   all-or-nothing when *any* part overlaps an existing capture (`collection.rs`);
   versioning one part of a collection, or versioning a collection as a whole, needs a
   stated rule. And `--output` is an exact path that cannot be suffixed — `reread`
   with `-o` must refuse (with a hint toward `-N`), not silently pick another path.
6. **Reading-task handling is unaddressed and load-bearing.** A reread creates a
   second note and hence a second reading task for the same source: the queue gains a
   twin, `ref list` shows both, `ref today` is ambiguous, and the review walk
   (`review-walk-is-tiered`) visits both. The design must state what happens to the
   original's task (recommendation in §5.4: leave it, link it, hint — do not
   auto-close).
7. **"Beautiful" is under-specified but achievable.** Current output already has a
   house style (`renamed: …`, `created: …`, `hint: …`, colored rows per cli_rules).
   The new paths should reuse exactly those line shapes rather than inventing new
   ones (§5.5).

## 3. Adjustments to the requirements (explicit)

1. **A1 — Suffix: use `_2`, `_3`, … (existing walk), not `__v<N>`.** Reread becomes
   "the same-reference refusal is lifted for one capture, and the normal
   collision walk assigns the next free suffixed stem." Zero new naming machinery;
   `find`/`list`/`show`/`rename`/Mac Capture keep working unchanged.
2. **A2 — Overwrite: refresh in place, never delete.** `overwrite` re-fetches /
   re-renders the source, re-stamps the PDF *at the same path*, regenerates the
   managed annotation region from the new PDF, and preserves frontmatter id, stem,
   reading task, lane state, and inbound links. User-written note content outside the
   managed region is preserved (scan already respects that boundary). Git records the
   transition; no side-archive, no annotation-dump links. If Bryan truly wants a
   pristine note, the path is manual delete + create — already supported and already
   hinted.
3. **A3 — Bare `-f` keeps a compatibility carve-out.** Because `-f` today replaces a
   *queued same-target snapshot/PDF*, bare `-f` in exactly that legacy situation keeps
   doing what it does (it is the `reread`-shaped outcome there anyway: same stem,
   fresh bytes). The *new* duplicate modes apply to the Layer-A / library-level
   refusals, where `-f` previously had no effect. Implementers must encode this
   boundary in `plan_default_target` vs `check_dedupe` handling, and document it in
   one paragraph in `docs/highlights-create.md`.
4. **A4 — `-o/--output` + `reread` refuses; `-o` + `overwrite` refreshes in place.**
   Exact paths cannot be suffixed without violating the caller's explicit request
   (`ensure_reference_id_available` precedent). Error must say so and point at `-N`.
5. **A5 — Collections: version the whole collection or nothing.** A multi-URL create
   with any overlapping part refuses as today unless `--force[=reread]` names the
   whole new capture; per-part versioning is out of scope. `overwrite` on a collection
   re-renders all parts.
6. **A6 — Original task stays open on reread; notes link both ways.** The new note
   gains frontmatter `supersedes: <original-id>` (informational, scan-preserved like
   other provenance keys); the original is untouched. Output prints the pair plus a
   `hint:` suggesting how to retire the original. No automatic task-state writes:
   lanes are sticky and derived-state writes belong to hooks, not to capture.
7. **A7 — `--listen` attach behavior is unchanged.** `--listen` on an already-captured
   target already attaches a new episode instead of refusing (`attach.rs`); the new
   modes must not reroute that path. (`reread` + `--listen` narrates the new capture
   normally.)

## 4. What I would *not* do (rejected alternatives)

- **A separate `bob ref recapture` / `duplicate` subcommand.** Heavier than needed;
   the refusal sites already know everything, and cli_rules favors options over
   command sprawl. Rejected.
- **Auto-suffix without any flag** (treat duplicates like different-reference
  collisions). Silent duplication destroys the "is this already in my library?"
  guarantee that `ref find` exists to provide. Rejected.
- **Version chain inside one note** (append v2 annotations into the same note).
  Conflates two annotation spaces and breaks the one-PDF-per-note invariant the
  scanner, Mac Capture panel, and `source_pdf_sha256` provenance assume. Rejected.
- **Deleting with an archive note.** Strictly worse than A2: same information git
  already keeps, plus index/links/retention costs. Rejected per §2.3.

## 5. Recommended solution

### 5.1 CLI shape

```
bob ref create [OPTIONS] <TARGET>...
  -f, --force[=<MODE>]   Allow re-capture of an already-captured source.
                         MODE: reread (default when flag is bare) | overwrite.
```

- Clap: `.num_args(0..=1).require_equals(true).default_missing_value("reread")`
  `.value_parser(["reread", "overwrite"])` — `require_equals` avoids the
  `-f overwrite` splitting trap; document `--force=reread` / `--force=overwrite`
  spellings and keep `-f` working bare.
- `CreateOptions.force: bool` becomes a three-state `ForceMode { Off, Reread,
  Overwrite }` (or `Option<ForceMode>`); every current `force: bool` use maps to
  `mode != Off` *except* the Layer-A refusals, which switch on the specific mode.
- Help text (alphabetical position kept; `-f` alias kept per cli_rules):
  `Allow re-capturing an already-captured source: 'reread' files a separate _2/_3
  reference (default when bare), 'overwrite' refreshes the existing reference
  in place`.
- This is a **CLI contract change** (`--force` gains an optional value) and per the
  `bob-cli-releases-ride-a-daily-train` decision must ship through the train with a
  `!` marker if any scripted bare-`-f` behavior observably changes; A3 is designed
  to keep that set empty, but the flag-shape change itself deserves a changelog line.

### 5.2 `reread` behavior (the default)

1. Layer-A refusal (`already captured as …` / `already queued in …` for the *same*
   source) is bypassed exactly once for this capture.
2. The normal `plan_default_target` walk then assigns the next free stem — which, with
   the original present, is necessarily `<stem>_2` (or `_3`, …). No new suffix code;
   the existing `renamed:` line already narrates it. Add `supersedes: <orig-id>` to
   the new note's frontmatter and print:
   `created: ref/blogs/foo_2.md · reread of ref/blogs/foo.md`
   plus `hint: the original is untouched; close its reading task when the new copy
   supersedes it`.
3. Dry run (`-d`) resolves and prints the suffixed stem without writing, ending with
   the standard `writes: none`.
4. With `-o`: refuse — `cannot reread into an exact --output path; pass -N/--name to
   capture under a different name` (mirrors the existing `--output`/`ensure_reference_id_available`
   voice).

### 5.3 `overwrite` behavior (refresh in place)

1. Applies to the library-level hit (and the same-intake-target case, subsuming the
   old bool). Re-runs fetch/render for the source, re-stamps the PDF at the *same*
   `lib/…` path (same stem, same id), regenerates the managed annotation region via
   the normal scan write path, preserves everything outside it, keeps the reading
   task and all links.
2. Commits as an update through the same create-time intake commit path; output:
   `refreshed: ref/blogs/foo.md · PDF re-stamped from <source>`.
3. Safety: refusals that exist for other reasons (sidecar collisions,
   `refuse_target_collisions`, dirty vault / busy locks → `queued:` degrade) are
   unchanged; `overwrite` never overrides them.
4. No annotation-dump files, no "previous ones" chains. History questions are answered
   by `git log -- <note>` / `<pdf>`, which the commit path already produces.

### 5.4 Reading tasks, find/list, rename

- Reread: original note and task untouched (A6). `find <source>` will now return two
  `in_library` rows — acceptable and truthful; `find` output should order the
  `supersedes`-linked pair adjacently if cheap, else leave as-is (implementer's call,
  not a requirement).
- Overwrite: task untouched by definition (same note); status stays derived.
- `rename` needs no changes: versioned notes are ordinary notes with ordinary ids.

### 5.5 Output beauty (house style, per cli_rules color guidance)

- Success lines reuse existing nouns: `created:` / `refreshed:` / `renamed:` /
  `queued:` / `hint:`. One line per fact, paths vault-relative, colored stems.
- Refusal without the flag keeps today's message and appends the new path, e.g.
  `already captured as ref/blogs/foo.md (source_url …)
  hint: pass --force to file a separate copy (foo_2), or --force=overwrite to
  refresh it in place`.
- `--format json` surfaces (if `create` ever gains JSON output) must carry a stable `mode: reread|overwrite|refused-duplicate` field so
  Bob Mac Capture (thin client per `mac-capture-is-a-thin-client`) can render the
  band without parsing English. Keep the human strings out of any machine contract.

### 5.6 Implementation map (for the implementing agent)

- `src/native/highlights_ref/create.rs`: `command()` flag def; `CreateOptions.force`
  → mode enum; `run_create` + route fns (`create_*` for local/URL/arXiv/article/
  collection/vault-note) pass the mode into `check_dedupe_with_listen_hint` and the
  `plan_*` calls; after-help `Output:` paragraph gains the two modes.
- `src/native/highlights_ref/sources.rs`: `check_dedupe` / `find_refusing_hit`
  take the mode; `Reread` skips the same-source refusal (recording the hit for the
  `supersedes` link + output line); `Overwrite` on a queued-PDF hit keeps today's
  bool behavior; on a library hit returns a distinct "refresh" signal instead of an
  error.
- `src/native/highlights_ref/stamp.rs`: `plan_default_target` keeps the walk; the
  `force: bool` params become mode-aware only where the same-reference intake branch
  is concerned (A3 boundary); `ensure_reference_id_available` unchanged.
- `src/native/highlights_ref/ingest.rs` + `collection.rs`: same treatment for the
  pre/post-capture `outcome_for_refusing_hit` checks; collection = whole-or-nothing
  (A5).
- Overwrite write path: reuse the scan note-write (`note.rs` managed-region
  functions) against the existing note rather than the fresh-note path; re-stamp via
  the existing `stamp_and_install` helpers at the same destination.
- Tests: unit tests in `stamp.rs` (walk unchanged), `sources.rs` (mode matrix:
  off/reread/overwrite × library-hit/queued-hit/legacy-hit/collection-part), and
  `ingest.rs`-style fixture tests for `supersedes` frontmatter + `_2` assignment;
  a no-flag duplicate test asserting the new hint text.
- Docs: `docs/highlights-create.md` (Output + vault-note second-snapshot paragraphs),
  `docs/ref.md` (the id/stem paragraph + command table row stays, behavior note
  added), `mkdocs.yml` untouched, `--help` text excellent per cli_rules.
- Non-goals for v1: per-part collection versioning, auto-closing superseded tasks,
  `superseded_by` back-links on the original, JSON envelope changes, Mac Capture UI.

## 6. Open questions for Bryan (only if the above is rejected)

1. Is there a real use case for *deleting* rather than refreshing — e.g. a capture so
   botched the note itself is embarrassing? If yes, that is `ref rename`/`rm` + create,
   and I would not bless it with a flag.
2. Should `reread` copies inherit the original's parent (`-P`) automatically? I assume
   yes (same source, same owner) — one line in the implementing plan.
3. Should `bob ref find <source>` annotate superseded/supersedes pairs in human
   output? Nice, explicitly deferred.

---
*Report: `202610/ref_create_force_modes__mus.md` · researcher mus · sources:
`src/native/highlights_ref/create.rs`, `stamp.rs`, `sources.rs`, `ingest.rs`,
`collection.rs`, `note.rs`, `attach.rs`, `arxiv.rs`, `src/native/ref_library/identity.rs`,
`docs/ref.md`, `docs/highlights-create.md`, `sase/memory/cli_rules.md`.*

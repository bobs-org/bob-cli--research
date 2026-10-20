# Likely-related tasks in the Mac capture preview panel — research (`__mus`)

Swarm researcher `mus`. Independent report; no peer report was opened or consulted.

Question: when the capture draft will create one or more new tasks, should the
bob-mac-capture preview panel also show likely-related existing tasks — as a
duplicate heads-up and as link candidates — without harming the app's blazing-fast
feel or cramping the panel?

Short answer: yes, but not as an always-on automatic panel section computed on every
keystroke. Ship it as a **gated, capped, collapsed-by-default related-tasks section**
powered by a **new bob-cli read-only endpoint** on its **own slower lane**, reusing
the existing tiered matcher, with **no automatic linking** — only explicit
insert actions that reuse today's pickers. Details and the reasons follow.

## 1. What exists today (the constraints any design must respect)

### 1.1 Thin client: bob owns every fact

`decisions:mac-capture-is-a-thin-client` (read via `sase memory read`) governs this
whole feature: capture grammar, completion data, preview, and vault mutation live in
bob-cli; the app renders what `bob` returns and never parses vault notes itself.
`BlockIDRules.swift` states it as "Bob is the only authority for the grammar". A new
related-tasks behavior therefore lands in bob-cli and `docs/capture.md` first, and the
Mac half only decodes and presents it. The JSON contract grows additively
(`decodeIfPresent`, schema-version rejection unchanged), per `docs/protocol.md`.

Related prior art already in the preview that this feature must sit alongside, not
duplicate:

- `capture --dry-run --no-clip --format json` preview cards per item kind, in bob's
  own order (`docs/capture-previews.md`).
- Relationship rows (`dependency_updates[]`, `relation_updates[]`) and successor-offer
  cards (`docs/capture-previews.md` "Successor offers", "Relationship rows").
- The `:` task-link picker (linkable open tasks in routable notes), the `!`
  task-complete picker (vault-wide open tasks), `^` active-task completion, `+query`
  vault-wide parent-task picker, and `&`/`*` dependency pickers — all served by
  `bob capture-complete` (`src/native/capture_complete/`).
- The idle agenda, which owns the auxiliary region while the draft is empty
  (`docs/idle-agenda.md`, `CaptureAgendaStore` / `CaptureAgendaFitPlanner`).

### 1.2 Live preview pipeline and timing budget

From `Sources/BobMacCapture/CapturePanelModel.swift` and
`Sources/CaptureCore/BobProcessClient.swift` (bob-mac-capture checkout):

- Keystroke → 50 ms debounce (`debounceNanoseconds = 50_000_000`) → `capture-parse`
  → `captureLivePreview` (asserts `--dry-run --no-clip --format json`) on its own
  lane. A changed draft clears cached preview outputs before the next preview lands,
  so footer and card always describe the same draft.
- Empty draft shows the agenda (`agendaVisible` requires `previewState == .idle`
  among other gates); any typed draft retires the agenda and the preview card owns
  the auxiliary region. The auxiliary region owns scrolling; the preview card "always
  takes its natural height" and the window grows up to the screen limit before the
  auxiliary region scrolls (`docs/capture-panel.md`).
- Subprocess timeout is 20 s (`BobProcessClient.defaultTimeout`) — generous, but a
  hung lane still blocks its own UI state.

Measured on the Linux host against the real `~/bob` vault (652 `.md` notes) with the
workspace debug build (upper bounds; release/Mac numbers will be smaller but the
ordering holds):

| probe | result |
|---|---|
| `capture-parse` | ~0.01 s |
| `capture --dry-run --no-clip` | ~0.02 s |
| `capture-complete --cursor 1` with `:` (routable-notes linkable scan, ~225 KB JSON) | ~0.26 s |
| `capture-complete --cursor 1` with `!` (vault-wide completable catalog, ~222 KB JSON) | ~2.18 s |

Takeaway: today's preview costs ~10–20 ms; a vault-wide task scan costs ~10–100×
that even before ranking. Anything that folds a full-vault scan into the dry-run
lane will destroy the "blazing fast" requirement. The related-tasks lookup must live
on a separate lane with its own slower debounce, must be skippable/cancellable, and
must never gate the preview card.

### 1.3 The ranking machinery to reuse (don't invent a new one)

- Tiered deterministic matcher: `capture_link_tasks::match_score` /
  `best_field_tier` / `field_tier` in `src/native/capture_link_tasks.rs`. Tiers are
  3 (field prefix) > 2 (word prefix) > 1 (substring) > 0 (in-order subsequence);
  every whitespace-separated term must match (AND); ties keep canonical order. The
  `&` dependency picker and the `!` completable catalog score through this same
  matcher (`capture_dependency_tasks.rs`, `capture_completable_tasks.rs`), so all
  pickers agree on what a tier means.
- Vault-wide discovery already exists: `capture_dependency_tasks::discover` walks
  every task-bearing note (with exclusions, bounded warnings, basename index); the
  `!` catalog in `src/native/capture_completable_tasks.rs` reuses that discovery and
  adds Today/pomodoro annotation. The `:` catalog in `capture_link_tasks::discover`
  is deliberately narrower (routable inbox/area/non-terminal-project notes only).
- Client-side fuzzy pieces (`CaptureCore/FuzzyMatcher.swift`, `refs-rank` +
  `RefsCore`) exist for pickers and refs, but vault scanning must stay in bob per
  the thin-client rule — Swift must never walk the vault.

### 1.4 Panel space budget

- With an empty draft the agenda owns the region (fixed eye line; farthest-first
  folding; chips; no scrolling of the editor). With a typed draft the preview owns
  it. A related-tasks section therefore competes with the preview card, not with the
  agenda — and the agenda's "never moves the editor" guarantee means related content
  must never appear while the draft is empty.
- The outer auxiliary detail region already owns scrolling; preview itself never
  nests another scroll view. Any related list must fit that model: a short capped
  list inside the existing scroll region, not a second scroller and not a second
  eye-line system.

## 2. Critique of the plan

### 2.1 Is it a good idea? Yes — with the scope narrowed

The duplicate heads-up is the strongest half: capture is the moment a duplicate is
cheapest to catch, and today nothing warns before submit. The "tasks you might want
to link" half is weaker and where the risk lives: most captures want no link at all,
and an eager suggestion list trains the user to ignore the panel.

Recommendation: frame and build the feature as **duplicate/near-duplicate warning
first, related-link discovery second**, with the UI weighted accordingly (exact and
near-exact matches always visible; fuzzy "related" matches behind a disclosure).
That keeps the common case (no duplicates) to one quiet line or nothing, instead of
a noisy list on every capture.

### 2.2 The two stated concerns are correctly ranked, but both are understated

- Performance is not just "the biggest concern" — at full-vault-scan cost it is a
  ship-blocker unless the lookup is isolated from the preview lane (see §1.2: 2.18 s
  vs 20 ms). Debounce alone does not fix a 2-second scan; gating + caps + a separate
  cancellable lane do.
- Panel fit is not just "don't scroll too often" — the auxiliary region already
  scrolls when the budget binds, and the preview card already grows the window. The
  real constraint is subtler: the related section must never push the primary
  preview (destination row, status transition, budget meter, error callout) below
  the fold on a small screen, and must never move the editor. That argues for a
  collapsed or 3-row-capped section *below* the preview items, never above them.

### 2.3 What I would do differently from the naive reading of the request

1. **Don't compute related tasks inside `capture --dry-run`.** A naive design adds a
   `related_tasks` array to the dry-run response. That taxes every preview — including
   `=`/`x`/`+` action drafts that can never have related tasks — with vault I/O, and
   couples preview latency to vault size forever. Use a separate read-only command
   (e.g. `bob capture-suggest --format json -- <draft>`) on its own lane, called only
   when the draft qualifies (§4.1), debounced slower than preview (~300–500 ms),
   cancelled on the next keystroke.
2. **Don't auto-link, auto-`&`, or auto-` Depend-On` anything.** Every automatic
   successor-link path in this codebase was deliberately converted to explicit offers
   (`decisions:unblocked-tasks-are-offered`). Related suggestions must follow the
   same rule: show, never insert. Each row's action should reuse an existing,
   already-tested gesture (insert `@route:block-id` link text, open the
   `:`/`&`/`*`/`!` picker seeded with the row, or open the note) rather than
   inventing a new one-click "link it" mutation.
3. **Don't show it for non-creating drafts.** Starts, closes, adjustments, shifts,
   pomodoro links/toggles, completions, ref-queue items, and template-row drafts
   have no "new task text" to match on. Running similarity there is pure cost and
   pure noise. Gate on: dry-run reports at least one item with a new-task kind.
4. **Don't rank with embeddings or any nondeterministic scorer.** The codebase
   standard is the deterministic tiered matcher with stable canonical tiebreaks
   (test-pinned with DK vectors). Keep it: duplicates must be reproducible, and
   golden tests must be byte-stable.

## 3. Requirements adjustments (called out as requested)

1. **[ADJUSTED] Scope: new-task creates only.** The request says "when the capture
   will result in one or more new tasks". I tighten this to: only items whose
   dry-run kind is a genuine new-task create (ordinary routed task, `^` ordinary
   task with authored ID, project-note ` :id`/` ^id` tasks, sub-bullets that create
   tasks). Explicitly out of scope: `=`/`x`/`+`/`++` actions, pomodoro links and
   toggles, `!` completions, ref-queue (`%`-URL/listen) items, and template drafts
   until their rows are complete. Rationale: no matchable new-task text exists in
   those drafts; skipping them saves a vault scan on a large share of keystrokes.
2. **[ADJUSTED] Default presentation: quiet unless duplicates exist.** The request
   asks to "start showing likely related tasks". I adjust to: an exact or
   near-duplicate match shows a warning-style row unconditionally; weaker "related"
   matches live behind a collapsed `Related (N)` disclosure (or a single quiet
   caption when N is small), expandable in place, reset on hide/draft change like
   agenda expansions. Rationale: controls noise and panel height in the common case.
3. **[ADJUSTED] Cap: at most 3 rows visible, +N more, per draft (not per item).**
   Multi-item batch drafts get one merged section, deduplicated across items, with
   each row naming which item it relates to. Rationale: per-item sections would
   multiply height by batch size; the batch already has an ordered item stack and
   one budget meter.
4. **[ADJUSTED] No new panel chrome, no new eye-line system.** The section reuses
   preview-card rows, existing glyphs/tints, and the auxiliary scroll region. No
   second scroller, no tabs, no popover. Rationale: §1.4 constraints; tabs/popovers
   would need focus management the panel deliberately avoids (focus never leaves
   the editor; Return in an empty editor never acts on rows).
5. **[ADDED] Explicit non-goals.** No automatic linking or dependency creation; no
   vault writes from the section (inserting link *text* into the draft is an edit,
   not a write, and goes through the normal preview→submit path); no network, no
   embeddings, no persistence of suggestions; no change to `capture --dry-run`
   latency or schema (additive-only new command instead).
6. **[ADJUSTED] Success metric.** "Blazing fast" is operationalized as: with the
   feature on, the preview card's keystroke-to-paint latency is unchanged versus
   off (the related lane never blocks it), and the related section paints within
   ~500 ms of typing settling on the reference vault size, cancellable without
   residue. Plus: zero new vault writes, zero new focus traps, VoiceOver parity
   for the section.

## 4. Recommended solution

### 4.1 Contract (bob-cli owns it)

New read-only command, e.g. `bob capture-suggest --format json -- <draft>`:

- Input: the same batch draft text as `capture --dry-run`. Reuses the phase-one
  parse to derive, per item, the matchable new-task text (parent line after marker
  stripping; authored children included as secondary terms) and the resolved route
  scope when one exists.
- Output (additive, versioned like other capture-protocol commands): per qualifying
  item (or merged across the draft) a ranked list of existing **open** tasks only —
  Ready/Blocked/Next/In Progress — each with `note_path`, `locator`, `block_id`,
  `route`, `status_*`, `text`, `section`, `line`, `task_ref`, a `tier`/score, a
  `why` (matched terms), and a `duplicate: true|false` flag for exact/near-exact
  matches. Closed (Done/Cancelled), hidden `#hide` handling (subdued/last, mirroring
  picker convention), duplicate-ID rows (disabled with reason, mirroring picker
  convention), and unreadable-note warnings all follow existing picker semantics
  rather than inventing new ones.
- Ranking: exact normalized-title match first, then the shared
  `capture_link_tasks::match_score` tiers over the same searchable fields the `:`
  picker uses (text, `route:block-id`, block ID, route, section), AND-terms,
  canonical-order tiebreak. Cap server-side (e.g. top 8) and let the client show
  fewer. Deterministic; golden-testable.
- Performance contract: single vault pass reusing
  `capture_dependency_tasks::discover`-style traversal (or the narrower routable
  set plus a scoped extension — measure both; the `:`-vs-`!` numbers above show
  this choice dominates latency); skip drafts with no qualifying items before any
  walk; never read the clipboard; never touch the ledger beyond what scoping needs.
  Document expected latency next to the 5 ms dry-run figure so the Mac side can set
  its debounce honestly.

Why a new command and not a dry-run field: it isolates cost (§2.3.1), keeps
`--dry-run` latency and schema stable, stays additive for older/newer version skew
in both directions, and gives the app an independent cancellable lane with its own
debounce — matching how `capture-parse`, `capture-complete`, and agenda refresh
already run on separate lanes.

### 4.2 App behavior (presentation only)

- **When:** only for qualifying drafts (§3.1), only while the preview card is shown
  (never in the empty-draft/agenda state), debounced slower than preview
  (~300–500 ms after typing settles), previous request cancelled on each keystroke,
  stale responses discarded by generation (same pattern as the existing analysis
  generation counter). No request while a picker, pull-in choice, or error owns the
  region; a failed lookup keeps the preview and shows at most a quiet retry hint —
  never a red error that displaces the card.
- **Where:** one section *below* the preview items (and below the plan-budget meter
  row), inside the existing auxiliary scroll region. Above-the-fold preview content
  (destination, transitions, budget, errors) is never displaced: the window-growth
  and slide-up rules in `docs/capture-panel.md` apply unchanged.
- **How much:** duplicate rows always visible (1–2 max, warning styling consistent
  with the existing orange override/cap banners); remaining related rows behind a
  `Related (N)` disclosure, max 3 visible when expanded, `+N more` cue, expansion
  resets on hide/snapshot change (same convention as agenda chips). Multi-word
  titles truncate with the locator first (same truncation order as close-card rows).
- **Actions (all explicit, all through the normal draft path):** row tap inserts the
  canonical `@route:block-id` (or `&`/`~` form where a relationship section is
  shown) as draft text at the caret / or seeds the corresponding existing picker —
  then the ordinary live preview validates it and Return submits. No direct vault
  mutation from the section. Keyboard: rows reachable without moving focus out of
  the editor (follow the picker-card precedent, e.g. arrow + Return to insert,
  Escape back to typing); VoiceOver labels mirror the visual `why` text.
- **Stale/empty states:** typing dims-and-holds like the agenda transition (or
  simply holds the last section until the new result lands — pick one, document it);
  clearing to empty retires the section with the draft; a lookup for a draft that no
  longer exists is dropped, never painted.

### 4.3 Beauty notes (small, load-bearing)

- One section, one glyph family, two densities: duplicates get the panel's existing
  warning vocabulary (orange banner tint, `exclamationmark.triangle`, same as plan-cap
  and override warnings); related rows get the neutral task-row vocabulary (status
  glyph + locator, same as `:` picker rows). No third style.
- Every row carries a one-line `why` in secondary text ("Same title in sase.md",
  "Matches “flaky” + “e2e”") — this is what makes fuzzy matches feel trustworthy
  instead of creepy, and it falls out of the tiered matcher for free.
- The collapsed state is a single line (`No duplicates · Related (4)` or just
  `No duplicates` when N is 0) — calm when there is nothing to say, which is most
  of the time.

### 4.4 Rollout order (thin-client order: bob first)

1. bob-cli: `capture-suggest` + ranking + `docs/capture.md` + golden tests
   (deterministic fixtures incl. DK-style vectors); `docs/` front-door updates per
   `docs.md` memory; new CLI surface per `cli_rules.md` memory.
2. Mac: decode-behind-`decodeIfPresent` presentation section, lane + debounce +
   generation guard, VoiceOver strings, CI synthetic renders
   (`capture-agenda.png`-style) for the three states (duplicates / related
   collapsed / expanded).
3. Measure on the Mac against the real vault: preview-lane latency with the feature
   on vs off, suggest-lane p50/p95, and row-action conversion (how often a shown row
   gets inserted — if near zero, tighten the threshold rather than enlarging the UI).
4. Follow-ups only after measurement: threshold tuning, per-route scoping, and (if
   warranted) a `plan.link_unblocked`-style opt-out — not before.

## 5. Risks and open questions

- **False positives on short drafts.** "Buy milk" matches everything with "buy".
  Mitigations already in the design: minimum matchable-text length / minimum two
  significant terms before any request; duplicates exempt (exact match always
  shows); threshold tuned by measured insertion rate, not by taste.
- **Vault growth.** Full-scan cost grows with the vault; today's 2.18 s debug
  full-catalog number is the ceiling to beat. If the scoped scan still misses the
  ~500 ms budget on the Mac, the documented fallback is a cached open-task index
  in bob refreshed on vault events — but that is new state with invalidation cost,
  so measure first and only then.
- **Version skew.** Older `bob` without the command must degrade to today's panel
  (no section, no error), exactly like the existing old-bob paths. New `bob` with
  an older app must change nothing (separate command the old app never calls).
- **Interaction with successor offers and relationship rows.** A suggested row that
  duplicates an already-planned `dependency_updates[]`/`relation_updates[]` row or a
  successor offer must be suppressed or badged "already linked" (same convention as
  `already depends on` / `already_linked`), using bob's resolved data, never
  Swift-side inference.

## 6. Verdict

Build it — as a duplicate-warning-first, capped, collapsed, explicitly-acted-upon
section on an isolated lane — not as an always-on auto-list. That version keeps the
panel blazing fast (preview lane untouched), fits without new chrome (three rows
under the preview, one quiet line when calm), stays intuitive (show, never insert;
reuse the `:`/`&`/`*`/`!` gestures users already know), and stays reliable (bob owns
matching via the pinned tiered ranker; the app only presents). The naive version —
similarity folded into every dry-run, auto-shown at full length — would trade all
three goals for one noisy list; the adjustments in §3 are what make the idea shippable.

*Evidence consulted: `sase/memory` decisions `mac-capture-is-a-thin-client`,
`idle-capture-shows-ledger-agenda` (via `sase memory read`); bob-cli
`src/native/capture_complete/{engine,candidates,support}.rs`,
`src/native/capture_{link_tasks,dependency_tasks,completable_tasks}.rs`,
`src/native/note_tasks.rs`, `src/native/capture/cli.rs`; bob-mac-capture
`docs/{capture-panel,capture-previews,idle-agenda,protocol,task-pickers,relationship-pickers,refs}.md`,
`Sources/BobMacCapture/{CapturePanelModel,CapturePanelView,CapturePanelWindowSizer}.swift`,
`Sources/CaptureCore/{BobProcessClient,FuzzyMatcher,CaptureAgendaFitPlanner}.swift`;
live timing probes against `~/bob` (652 notes) with the workspace debug build.*

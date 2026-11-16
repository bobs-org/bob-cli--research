# Schema Editors: Emoji Completion and Multi-Slot Reorder — Consolidated Design

Consolidated by the lead researcher on 2026-11-16 from five independent reports
(`__cdx`, `__cld`, `__grk`, `__mus`, `__gem` in this directory) plus the lead's own
source verification in `bob-plugins` and `bob-cli`. The request: make the bank/album
schema editors much easier to use — excellent emoji completion, multi-slot moves with a
great preview, fast Apply — and critique the plan itself.

## Verdict

**This is a good idea, and all five researchers independently converged on the same
reframing: the problem is not three features, it is one interaction rule.** Today the
cards treat every keystroke as a writer gesture — each Alt+J stages a single ±1 move and
asks you to pay a full guarded `bob` transaction (lock, pre-sync, replan, commit,
post-sync, report refresh) per slot. The fix:

> **Compose locally and instantly; validate once through `bob`; apply the whole
> arrangement as one transaction with one Undo.**

Emoji completion is an attachment gap, not a missing engine: `bob-emoji` already ships a
1,870-entry searched catalog with recents that simply is not wired to the cards' plain
`<input>` boxes. Reorder is a protocol-underuse gap: `field.move`/`choice.move` already
take arbitrary absolute positions, bank moves already take arbitrary `before`/`after`
anchors, and both writers already accept atomic multi-op envelopes with reverse-ordered
`inverse_ops` — the UI chokes all of that down to one adjacent hop per commit. No
bob-cli change is required for v1; this is almost entirely plugin work.

"Make Apply faster" is explicitly the wrong first knob (4 of 5 reports; the fifth
agrees batching comes first). The transaction cost is honest for a write; it is only
dishonest to pay it twelve times for one thought.

## Evidence (verified)

### Where the seconds go

cld measured the real pipeline on apollo (vault of 7,293 notes, read-only dry-runs):

| Step | Cost |
|---|---|
| Debounced preview `bob albums update -d` (full snapshot + plan) | 0.25 s + ~1.0 s |
| Apply: preflight plan outside the lock | ~1.0 s |
| Pre-sync `sync_cycle` (git, network) | ~0.8 s |
| Fresh plan inside the lock | ~1.0 s |
| Write, commit, `verify_installed` (re-scans vault) | ~0.6–1.0 s |
| Post-sync `sync_cycle` (git push) | ~0.8 s |
| Plugin forces `bob albums list -f json` before unlocking | ~0.65 s |
| **Machine time per one-slot move** | **≈ 5.5–6.5 s** |

Crucially, a 14-slot `choice.move` dry-run costs the same as a 1-slot one (~1.0–1.1 s),
and a 3-op envelope costs ~1.15 s with correct reverse-ordered inverses (cld verified by
live dry-run on `sase_blog_zettel`). Distance is free; *transactions* are what cost.

The vault's own git history is the strongest motivation: minutes after the screenshot,
"How I use SASE" was added to Section **at the end** and then walked up one slot at a
time — **five commits in 85 seconds** for what was a single thought ("put it before The
Demos"). Four of the six album-schema writes in vault history are one-slot moves.

### Why the UI can't do better today

`schemaMoveSelected(direction)` computes `next = index ± 1` against the **server**
model and `session.setDraft([op])` **replaces** the draft; the chips are painted from
the server model, so a second Alt+K before Apply re-stages the same op (a no-op) and the
chips never show the pending order — the only "preview" is a consequence sentence
(`241y-plugin-album-schema-card.js:541–557`, confirmed by cld/grk/mus/gem from source).
The bank card is stricter still: each move opens a confirm stage
(`beginGesture("move")`) so you cannot even mash Alt+J. Both modals also rebuild their
entire DOM (`content.empty()`) on every session change, which matters for any live
popover, drag, or FLIP animation.

### Emoji today

- The album `Choice emoji` field and bank category labels are bare text inputs; the
  bank placeholder literally teaches hand-typing `e.g. 🍔 Fast food`. Bank stores emoji
  fused into the label (split by Rust `split_icon`); albums store it separately.
- `bob-emoji`'s `EditorSuggest` only fires on `:query` in Markdown editors — nothing
  attaches to modal inputs, and there is no public API (helpers are exported for tests
  only).
- cdx benchmarked the existing search helper: 1,870 entries, index builds in ~10 ms,
  p50 ~1.06 ms per query — in-process search is effectively free; no subprocess or
  external picker library is justified.
- cdx also documented real quality gaps: `:fire:` (with colons) finds nothing,
  `white check mark` (spaces) finds nothing, `conclusion` finds nothing, pasting a
  glyph finds nothing, no typo recovery. cld confirmed the keyword data is thin (🧠 has
  only "brain"; 🪝 only "hook"). Fixes: query normalization + multi-token matching
  (cheap, code-only) and CLDR keyword enrichment (data; see Open Questions).
- Lead-verified: the vendored gemoji JSON already carries a `category` field on all
  1,870 entries — browse-by-category costs no new data.

### Bugs and dead data found along the way (lead-verified from source)

1. **`q`-in-input bug (bank, confirmed at both sites).** In
   `248k-plugin-bank-setup-card.js:601` and `248g-plugin-bank-category-new-stage.js`
   the `q`/Escape cancel check runs **before** the `inInput` guard, so typing `q`
   inside any stage input ("Liquor", "Equipment") cancels the stage or closes the
   card. Fix immediately, independent of everything else.
2. **Bank dry-run data is thrown away.** `bob bank config update -d` returns the
   post-image `categories[]` and `hotkeys.shifted` (`bank/config_update/run.rs:131`);
   the plugin validates them on the wire (`248d`) but never paints them on the tile
   grid — the preview the user wants already exists server-side.
3. **`album.set` cannot edit the album's own `emoji`** — `ALLOWED_SET` is exactly
   `["label", "plural", "dated_notes"]` (`albums/update/ops.rs:295`). Album-level emoji
   editing is therefore a CLI change and out of v1 scope (grk's position; gem's
   proposed extension is a reasonable follow-up).
4. **Cross-plugin sharing has an established pattern.** `task-status-cycler` exposes a
   frozen `this.api`, consumed by `bob-navigation-hotkeys` via
   `app.plugins.plugins[...]`; many plugins reach into `bob-ledger-tools` the same way.
   This settles the cdx-vs-others dispute: share the emoji engine through a **versioned
   runtime API on `bob-emoji`** (cld/grk/gem), not build-time copies — with a graceful
   plain-input fallback when `bob-emoji` is disabled. (`AbstractInputSuggest` is used
   nowhere in the repo today.)

### Visual audit (consensus from the screenshot)

The stats line renders twice (header subtitle + first body row); the empty consequence
strip paints as a dead tinted bar; a 13-button toolbar stays mounted with ~8 buttons
disabled during a stage and `Cancel stage` appearing twice; `Preview this edit` is
redundant (preview already auto-runs after 250 ms); Enter is inert until a preview
succeeds, which reads as broken to a fast typist; zero counts glued to labels
(`Ready 0`) add noise across 15 chips; the choice-emoji input gives no hint that search
could exist.

## Adjusted requirements (changes to the request, called out)

1. **"Move up/down multiple spots" → "place anywhere locally; save one arrangement as
   one transaction."** Bigger step sizes or faster arrows would still pay a full
   transaction per gesture and still show no spatial preview. (All five reports.)
2. **"Apply is slow" → "zero-latency projection, one background save."** The save's
   floor is roughly two git sync cycles plus full-vault scans (~4–5 s); batching makes
   that cost *once per arrangement* and moves it off the critical path. Real CLI trims
   are measured follow-ups (see Performance). (All five; gem dissents on timing — see
   Conflicts.)
3. **New: "Add choice" must also place the choice.** Half the observed pain was
   add-at-end-then-walk-up. The add stage gets a live **ghost chip** positioned with
   the same move keys before the single `choice.add {position}` commit. (cld; the
   op already takes `position`.)
4. **Emoji completion → one shared Emoji Slot in both editors**, covering album choice
   add/edit, new-field initial choices, and bank category new/edit (where the UI
   splits/joins `${emoji} ${label}` so the bank envelope stays unchanged). Search text
   and chosen glyph are separate state; paste and the OS picker always work.
5. **Scope guards (consensus):** reorder-only pending drafts — relabels, toggles,
   removals stay one-gesture-one-commit (refusal attribution and Undo granularity
   degrade otherwise, and vault history shows no bursts of those edits); no
   multi-select bulk moves; no album-level emoji in v1; bank accounts are never
   reorderable (first account carries attribution; writer refuses); rule reorders are
   always "loud" (order is match precedence); choices never cross fields; cross-group
   category drag deferred (open question); YAML `y` hatch stays; no skin-tone grid.
6. **New: fix the `q`-in-input bug** and the small visual defects now, regardless of
   the larger design.
7. **Reliability is a feature of the beauty requirement, not in tension with it** (mus):
   Apply stays gated on a successful preview of the exact envelope; nothing weakens the
   fingerprint/`expect`, save-open-editors, one-flight-apply, or inverse-op Undo
   machinery.

## Recommended design

### Reorder: projected model, one envelope

No separate mode to learn: **Alt+J/K simply stops writing.** It moves the selected
field/choice/category/group/rule one slot in a locally *projected* model (server model +
pending moves) and repaints in <16 ms with a short FLIP animation. On top of that:

| Gesture | Effect (local; zero bob calls) |
|---|---|
| `⌥J` / `⌥K` | Nudge one slot; repeatable; key-repeat coalesces |
| count prefix (`4⌥K`) | Nudge N slots (vim-shaped) |
| `⌥G` / `⌥⇧G` (or Home/End) | Jump to first / last slot |
| `m` → hint letter | **Move to…**: sibling chips get hint letters; letter drops before that item, Shift+letter after (jump-to-link muscle memory; also the pointer-free distant-move path) |
| drag handle | Pointer-events drag with a 2 px accent insertion caret; feeds the same pending model; keyboard parity always exists (WCAG 2.5.7) |
| `⏎` | Save the arrangement (one envelope) |
| `esc` | Revert all pending moves (nothing was written) |
| `u` after save | Stage the inverse of the whole arrangement (server `inverse_ops`) |

**What you see:** the moved chip carries an accent ring and a delta badge (`↑4`); a
pending bar replaces the toolbar with `N moves pending — 🔍 How I use SASE 15 → 11 ·
⏎ save · esc revert`; a polite live region announces position changes. On a wrapping
chip cloud the insertion caret is an underline in the gap, not a page-tall bar.
"Put How I use SASE before The Demos" becomes `m` + hint + `⏎`: three keys, one commit,
instead of 4 × (⌥K, wait, ⏎, wait) ≈ 31 s and four commits.

**Save pipeline.** Each pause in motion feeds `session.setDraft(ops)` so the existing
250 ms-debounced dry-run validates speculatively while you work. **Enter latches**: if
the preview for the current revision is still in flight, Enter applies the moment it
succeeds (this also fixes the "inert Enter" papercut card-wide). Quiet previews
(`ok`, no grouping change, no new invalids, no warnings) auto-apply on that single ⏎;
loud ones (field moves that change `group_before/after`; any rule reorder; bank hotkey
shifts) paint the consequence amber and ask for a second ⏎. After ⏎ the projected order
stays on screen with a subtle "saving" shimmer while the ~5 s transaction runs in the
background; on refusal the chips FLIP back and the refusal shows inline; after the
post-write report lands, assert predicted order == actual order (should never differ;
warn quietly if it does).

**Envelope compilation.** Record intent per item as an anchor (`before`/`after` a
stable key, or start/end), coalescing repeated nudges; compile at save time into
today's sequential `field.move` / `choice.move {position}` (albums) or
`category.move`/`group.move {before|after}` and `rule.move {position}` (bank) against
the order each prior op produces, simulating to assert the compiled ops reproduce the
draft exactly. Anchors (not raw indices) make the intent survive a stale-schema rebase.
Identity is always the stable key/value, never a DOM index
(`decisions:relation-card-tab-accepts-ctrl-d-hides` lesson). Returning everything to
the original order leaves no dirty draft and no transaction.

**Bank specifics:** same engine; paint the dry-run `categories[]` and `hotkeys.shifted`
(`G→H` badges) on the tile grid — the data already comes back today; remove the
per-move confirm stage (the pending bar is the confirmation, once, at the destination);
groups move as blocks; the protected Money moves group, hidden section, and accounts
stay non-reorderable.

### Emoji: a shared Emoji Slot

A square glyph well fused to the left of the label input — the shape the stored value
actually has (`🔍 How I use SASE`) — with a live chip preview of the exact token the
index will render:

- Empty well shows a dotted placeholder; Tab from the label, click, or `Ctrl+E` opens
  an **anchored panel inside the card** (not a floating popover: it would add a second
  Escape scope and ↑/↓-only navigation; nothing in the repo uses `AbstractInputSuggest`
  today). Typing or pasting a glyph — including via the OS picker — sets it directly.
- **Empty query shows, in order:** *For this label* (tokenized, stop-worded,
  light-stemmed label words matched against aliases/keywords — "Automation (service)"
  → ⚙️ 🤖 🛠️), *Your albums* (emoji already used for similar labels, from the report
  the plugin already holds), *Recents* (shared with the editor's `:shortcode:`
  completion so both surfaces learn together), then browse categories (the vendored
  `category` field).
- **Typing filters live** (in-process, ~1 ms; no debounce) with upgraded ranking:
  normalize colons/underscores/hyphens; AND multi-word tokens; tiers = exact alias or
  keyword > alias prefix > keyword word-start > substring > description > conservative
  fuzzy only when results are thin; recents and vault-used boost within tiers only, so
  an old pick never beats an exact query.
- Search text and chosen glyph are **separate state**: typing `rocket` can never become
  the literal icon; Enter picks the highlighted result and never also applies the
  schema edit; the first Esc closes the panel only. IME composition guards throughout.
- A sibling-duplicate badge dims (never blocks) an emoji already used in the field.
- **Engine ownership:** `bob-emoji` grows a frozen, versioned `api` (v1): `search`,
  `suggestForLabel`, `categories`/`browse`, `info`, `remember`, `recents` — the repo's
  existing cross-plugin pattern. If the plugin is disabled, the slot degrades to
  today's plain input plus a hint; Apply is never blocked.
- **Unicode round trips are a release requirement** (cdx): one displayed emoji may be a
  ZWJ sequence, keycap, flag, or tone-modified cluster. Preserve pasted sequences
  byte-for-byte; never `slice(0,1)` or code-point counts; don't reject glyphs newer
  than the catalog; and don't let a UI whitelist narrow the permissive label contract.
  Note the known JS/Rust divergence: `albumSchemaChoiceParts` accepts digit keycaps
  (`1️⃣`) while Rust `split_icon` treats a leading ASCII digit as label text — make the
  Rust behavior authoritative and add shared round-trip fixtures (✅, 👩🏽‍💻, 🇺🇳, `1️⃣`,
  no-emoji, legacy symbols) before calling the picker done. An edit to a bank label
  must retain its emoji unless explicitly cleared.

### Visual refresh (folded into the first shipping phase)

One title line with a dim, independently truncated breadcrumb; drop the duplicate
stats row; `required` as a pill instead of a bare `*`; counts as muted tabular-numeral
pills with zero-counts faded; hide the consequence strip when empty; replace the
13-button wall with a **contextual hint strip** listing only keys valid for the current
selection (a `⋯` reveals everything for mouse users); remove `Preview this edit`
(preview is automatic; Enter latches); status as one inline line with a colored left
rule (neutral/amber/red/green) instead of floating notices; FLIP ~120–160 ms respecting
`prefers-reduced-motion`; and crucially **stop rebuilding the whole modal DOM** —
patch stable regions so caret, scroll, popover, and composition survive repaints.

## Performance: what to do and what to defer

Batching changes the economics by itself: an 8-slot move goes from ~8 transactions
(16 remote git round-trips, 8 commits, 20–35 s of waiting) to one background ~5 s
transaction behind an instant local projection. After that ships, measure before
touching transaction semantics. Ranked follow-ups:

1. **Embed the post-write report in the update output** (zero risk, additive JSON):
   `verify_installed` already computes the album entry and the bank plan already builds
   the config report; returning them removes the blocking post-apply `bob albums list`
   / `bob bank config` spawn (~0.65 s) — the card patches in place and unlocks.
2. **Scope `verify_installed`** to the edited album and its record folder rather than a
   full vault re-scan (~0.5 s), and/or target snapshot reads to root notes + `<stem>/`
   + ancestor chain.
3. **Let bob declare quietness** (`index_changed: bool` or `facets_before/after`) so
   the second-⏎ rule is never inferred in JS.
4. **Deferred, as its own decision:** gem's `--offline` local-commit +
   sync-on-open + debounced background `bob vault-sync`. Precedent exists (`task move`,
   `relations rename` take `--offline`) and the fingerprint re-check under the lock
   keeps it safe, but the post-sync protects multi-host convergence for every guarded
   writer — changing that lifecycle deserves its own decision record and recovery
   tests, not a ride-along on this feature. Batching alone removes most of the felt
   pain. Similarly, profiling the ~1 s `VaultSnapshot::load` floor helps every writer
   and is a separate task.
5. **Never** skip the index rebuild for ordering ops: Section/`index_by` order *is*
   grouping; a "presentational fast path" that leaves the generated index stale is a
   correctness bug (grk, cdx concur).

Proposed interactive budgets (acceptance criteria, not promises): emoji filter paint
p95 < 50 ms; reorder nudge paint p95 < 50 ms with zero writer calls; settled dry-run
p95 ≤ ~1 s on the real vault; exactly one write transaction and one revalidation per
arrangement. Add timing spans to the preview/apply path in the existing e2e harness.

## Conflicts between reports, and resolutions

| Dispute | Positions | Resolution |
|---|---|---|
| Batch scope | grk: one item per envelope; cld/cdx: multi-move reorder-only drafts; gem: arbitrary mixed drafts with `Apply (N)` | **Reorder-only drafts, multiple moves allowed.** The envelope is ordered ops either way; the compiler is the same for 1 or N items. Mixed add/rename/toggle batching is rejected for v1 (refusal attribution, Undo granularity, no evidence of need). |
| Grab mode vs modeless | grk/gem: explicit `m` grab with lift semantics; cld: no mode, Alt+J/K just goes local | **Modeless projection** — fewer states, same power; `m` survives as the Move-to hint-jump. The two designs are nearly isomorphic; modeless drops one concept. |
| Emoji surface | grk: `AbstractInputSuggest` popover; mus: inline dropdown; cld/gem: in-card grid panel; cdx: anchored combobox | **In-card anchored panel** (one Escape ladder, 2-D navigation, grid browse possible), *reusing bob-emoji ranking via the api* so grk's "don't reimplement ranking" point is honored. |
| Engine sharing | cdx: build-time generation into each plugin (fragment builder rejects cross-plugin paths) | **Runtime versioned api** — lead-verified as the repo's established pattern (`task-status-cycler.api`); cdx's degradation concern is answered by the plain-input fallback. |
| CLDR enrichment | cld/cdx: yes (thin keywords are the real gap); mus/grk: not needed for v1 | **Search-code upgrades first** (fix `:fire:`, multi-token, label suggestions — all free), **CLDR as an open question** (+150–250 KB vendored, biggest data-side quality win). |
| Apply-speed timing | gem: `--offline` + scoped scans in the main roadmap; others: measured follow-ups only | **Defer** per above; items 1–3 are uncontroversial, item 4 is its own decision. |
| Bank cross-group drag | gem: yes (`category.set`+`category.move` atomically); cdx: separate explicit edit; cld: open question | **Defer; ask Bryan** (it's one envelope if wanted, previewed loud). |
| Album-level emoji | gem: extend `album.set`; grk: out of v1 | **Out of v1** (verified CLI restriction); clean follow-up once the Slot exists. |

## Implementation plan

New logic goes in new fragments (`241y` is already near the 1,000-line cap). After each
bob-plugins phase: `npm run build`, `npm test`, `bob plugins sync`.

| Phase | Repo | Scope | Size |
|---|---|---|---|
| **P0 Quick fixes** | bob-plugins | `q`-in-input fix (both sites, with regression test); dedupe stats row; hide empty consequence strip; contextual toolbar; paint bank dry-run categories + hotkey shifts | S |
| **P1 Projected reorder + add-and-place (album)** | bob-plugins | Pure reorder model fragment (intents, projection, envelope compiler — unit-tested without DOM: permutations, anchors, coalescing, rebase, first↔last, same-slot no-op); DOM fragment (FLIP, hint-jump, drag, pending bar, live region); Enter latch; targeted DOM patching; visual refresh; e2e batched-apply + undo + predicted-equals-actual | M–L |
| **P2 Emoji Slot** | bob-plugins | `bob-emoji` api v1 + search upgrades (+ CLDR if approved) in `gen-emoji-catalog.mjs`; Slot fragment (well + panel + keys) wired into choice add/edit and field-add initial choices; Unicode round-trip fixtures shared with Rust behavior | M |
| **P3 Bank parity** | bob-plugins | Reuse P1+P2 on categories/groups/rules (rules always loud); Emoji Slot composing `${emoji} ${label}` | M |
| **P4 Decision record** | memory | On acceptance: "a schema arrangement is one intent and one commit; non-reorder gestures stay one gesture, one commit" — answers the commit-granularity question left open by `202611/album_record_schema_ux` | S |
| **P5 Measured CLI trims** | bob-cli | Embedded post-write report; scoped verify; `index_changed`; (separately) snapshot-load profiling; (own decision) `--offline` interactive saves | S–M |

P1 and P2 are independent and parallelizable. **Ship P1 first** — the git history shows
reordering is where the time actually goes.

**Acceptance walkthrough** (Bryan's real session, inverted): add a Section choice by
typing `use` into the Slot, pick 🔍 from the label-suggestion row, place the ghost chip
before 🎬 The Demos with `m`+hint, ⏎ once → one preview, one commit, chip already in
place; `u` restores in one commit. Edge cases to cover: no-op return to original order,
first/last bounds, duplicate labels with distinct values, ~100 choices, stale-vault
rebase mid-draft, rapid double-⏎, lost apply response, keyboard-only + VoiceOver +
reduced motion + both themes.

## Open questions for Bryan

1. **Quiet reorders auto-apply on a single ⏎** (recommended), or always require the
   second confirming ⏎?
2. **Hint-jump key**: `m` ("move to…"), or `f` to match jump-to-link muscle memory?
3. **CLDR keywords**: worth ~150–250 KB in `bob-emoji` for much better filtering
   ("memory" → 🧠, "find" → 🔍)? Recommended yes.
4. **Bank cross-group drag**: allow drop-into-another-group as one loud envelope, or
   keep group membership a separate explicit edit?

## Recommended solution

Fix the `q` bug and visual papercuts now (P0). Then ship the **projected reorder with
one batched save plus add-and-place** (P1): Alt+J/K, counts, ends, and `m` hint-jump
move chips instantly on a local projection with FLIP and a pending bar; drag is an
equal pointer path; ⏎ latches and saves the whole arrangement as one anchored multi-op
envelope through the existing guarded session — one commit, one `u` Undo, the ~5 s
transaction in the background, and zero bob-cli changes (the writers already accept
everything needed, verified by live dry-run). Then the **shared Emoji Slot** (P2): a
glyph well with an in-card panel served by a versioned `bob-emoji` api — label-aware
suggestions, vault vocabulary, shared recents, live sub-millisecond filtering over an
upgraded (optionally CLDR-enriched) catalog, duplicate badges, paste/OS-picker
fallback, and strict Unicode round-trip preservation. Then **bank parity** (P3) with
the same two components, the dry-run hotkey/category preview finally painted, and rules
always loud. Record the one-arrangement-one-commit decision (P4) and take the CLI trims
as measured follow-ups (P5).

This turns the observed 85-second, five-commit session into about three keystrokes and
one background commit, keeps every existing safety guarantee (bob remains the only
writer; nothing applies unpreviewed), and makes the card beat YAML at the one job YAML
still wins.

## Sources

- The five suffixed reports in this directory (each lists its primary sources; grk's
  Mermaid figures are the `schema_card_emoji_and_reorder__grk_*.png` files alongside).
- Lead verification in `bob-plugins` (`248k:601`, `248g` key routing; `task-status-cycler`
  `this.api`; no `AbstractInputSuggest` usage; `vendor/gemoji-emoji.json` category
  field) and `bob-cli` (`albums/update/ops.rs:295` `ALLOWED_SET`;
  `bank/config_update/run.rs:90,131` `hotkeys.shifted`; `albums/update/protocol.rs`
  positions; `docs/vault-git-sync.md:42` `--offline`).
- Screenshot: `~/tmp/screenshots/20261116_134836.png`.
- Prior research: `202611/album_record_schema_ux/album_record_schema_ux__final.md`
  (one gesture = one scoped commit; open commit-granularity question),
  `202611/sase_blog_zettel_section_schema/` (the reorder that was done in YAML because
  the card was too painful).

# Wikilink completion in Bob's prose prompts — consolidated design

Lead researcher · 2026-11-21 · Consolidates five independent reports (`__cdx`,
`__cld`, `__grk`, `__mus`, `__gem`, siblings of this file) plus my own
verification of every load-bearing disputed claim against bob-cli, bob-plugins,
and the live vault on apollo.

**Verdict: build it — all five researchers independently said yes, and so do
I.** But not as written. "Obsidian link completion in any free-form text input
prompt" should become **"wikilink completion in every Bob-owned field that
writes Markdown into the vault, behind one shared controller"** — and two
already-verified bob-cli defects should be fixed first, because they bite the
Mac capture panel today and would be inherited by every new surface.

---

## 1. Verified facts (my own checks, resolving the swarm's evidence)

These claims were disputed or singly-sourced across the five reports. I
re-verified each one this session:

| Claim | Status | Evidence |
| --- | --- | --- |
| An unclosed `[[` field replaces through end-of-line, destroying trailing prose | **Confirmed — real defect** | Source: `scan_line` maps `LinkScanEnd::LineEnd` → `parse_link(.., line_end, None)`, and `replacement_end = self.inner_end` (`src/native/capture_links.rs:584,654-712`). Live: `bob capture-complete -c 9 -- 'Read [[da because of the outage'` returns `replacement {start:7, end:31}` — accepting a row deletes "because of the outage". |
| `[[sase` buries every root `sase_*` note | **Confirmed — real defect** | `note_candidates` ties within a match kind break on `compare_normalized(path)` — plain alphabetical full path (`capture_links.rs:282-289`). Live top-20: `sase.md`, then 19 rows from `chat/`, `plans/`, `prompts/`; zero root `sase_*` notes survive the `RESULT_LIMIT: usize = 20` cap. |
| Per-keystroke `bob capture-complete` is too slow for prompts | **Confirmed, worse than reported** | cld measured 0.45–0.55 s warm; my runs on apollo today: **0.77–1.18 s per invocation**. `NoteIndex::read` re-walks and reads every note each call. |
| Mac event-note editor would break completed links | **Confirmed — exclusion required** | `escape_note_inline` (`src/native/task_text_escape.rs:40-50`) rewrites every `[` → `\[` in gcal private-note prose, so a completed `[[link]]` becomes a dead escaped literal. Only gem caught this; cld's plan to wire that editor is wrong as stated. |
| Intention YAML frontmatter is already link-safe | **Confirmed** | `quote_yaml` (`src/native/intentions/write.rs:614-623`) JSON-quotes any intention text containing `[[`. No new YAML work needed. |
| Both candidate host plugins work on mobile | **Confirmed** | `bob-navigation-hotkeys` and `bob-ledger-tools` manifests both say `isDesktopOnly: false` (bob-mail is desktop-only). gem's mobile argument does not discriminate between homes. |
| The USED BEFORE recall band is the main keyboard conflict | **Confirmed** | `logRecall` v1 lives on `bob-navigation-hotkeys.api` (root v3) and attaches to ~10 of the 14 prompt surfaces; it claims ↑/↓ and Ctrl+N/P in capture phase (`docs/develop/plugin-apis.md` in bob-plugins). |

Also corroborated across reports (not re-verified, consistent and sourced):
`AbstractInputSuggest`'s public constructor takes `HTMLInputElement |
HTMLDivElement` only — the reflection `<textarea>` is out; capture work-log
phrase completion already refuses summaries containing `[[`
(`work_log_completion_ignores_summaries_with_wikilinks`), so Bob has already
decided `[[` means "link", never "recall phrase"; and Bryan hand-writes these
links today (this week's `2026-W47` intentions include
`[[sase_blog_zettel]]` and `[[sase#^ref-sase-1n6-11-4-restart-readiness]]`),
which is the demand proof and also shows block links are a first-class need,
not an extra.

## 2. Critique: is this a good idea?

Yes, and it is overdue — the unanimous reasoning:

1. **Demand is proven.** Bryan already types these links by hand, including
   long `#^block-id` anchors that silently dangle when mistyped.
2. **It feeds existing machinery for free.** A `[[note#^id]]` in a Work,
   Schedule, Rotten, or Cancel Log bullet already produces a Task Mention on
   the target's 🪢 LINKED FROM line; the Intention Card already renders links
   with hover previews and unresolved badges; `bob periods` repair already
   retargets links inside intentions when notes move to `done/`. The write
   side is finished — only the authoring side is missing.
3. **Parity removes a seam.** `[[` completes in the Obsidian editor and the
   Mac capture panel; it is surprising that it dies in the prompts launched
   *from* those surfaces.
4. **It costs nothing when unused.** Nothing changes until `[[` is typed.

Where the request as written would go wrong (unanimous, with different
emphases):

- **"Any free-form prompt" is too broad.** Picker filters, block-ID and rename
  fields, bank categories, Command Mode argv, copy-chip payloads (where bash
  `[[ -f ... ]]` is literal syntax), and outbound email must stay literal.
- **"Triggered by `[[`" under-specifies the hard part.** Enter in these
  prompts *writes the vault and closes the modal*; submitting a half-typed
  `[[sase` into the Rotten Log is the worst failure mode. Keyboard ownership
  against the recall band, Esc layering, and undo are the real work, not the
  menu.
- **Per-prompt implementations drift.** There are ~14 surfaces across 4
  plugins, and the record card already grew a crude divergent link list
  (`recordCardLinkCandidates`: substring over paths, no aliases, no tiers).
  The `q`/`Ctrl+[` decision exists precisely because per-panel opt-in drifts.
- **The obvious "thin client" implementation is wrong here.** Spawning
  `bob capture-complete` per keystroke means ~1 s of lag per character on the
  real vault and inherits both defects above. The thin-client decision binds
  the Mac app, not Obsidian plugins — and even it allows clients to rank what
  bob returned.

## 3. Requirement adjustments (explicitly called out)

| # | Adjustment | Rationale |
| --- | --- | --- |
| A1 | **Scope rule, not a list:** complete only in Bob-owned fields that write Markdown into the vault; everything else stays literal. Ship with an audited allowlist (§5.1) and a lint so new prompts must declare prose-or-identifier. | Unanimous. A rule beats a list; the lint stops drift. |
| A2 | **Near-full link grammar, phased:** notes, aliases, headings (`[[#`, `[[note#`), and single-note blocks (`[[#^`, `[[note#^`) in v1; vault-wide `[[##`/`[[^^` in phase 2; `((` task links deferred. Embeds `![[` come free (the `!` sits outside the field). | Bryan's own intentions use block links today; deferring blocks (grk/mus) misses the strongest use case, but vault-wide scans and the `((` picker (which can mint block IDs — a vault write from inside a modal) are safely later. |
| A3 | **Enter/Tab accept, and Enter never submits a half-typed link.** With zero matches, Enter consumes the key and dismisses; the next Enter submits normally. | The one failure the feature must make impossible. Resolution of the swarm's Tab dispute in §4.3. |
| A4 | **Insertion only — no side effects.** No note creation, no block-ID minting, no navigation, no save. Unmatched `[[typo]]` stays typed; a quiet unresolved-link hint (not a blocker) makes it visible. | Unanimous. Obsidian's native Create-note row does not transfer: prompts edit sentences, not the vault tree. |
| A5 | **Fix bob first (phase 0):** (a) an unclosed `[[` field ends at the caret, never the line end; (b) break match-kind ties by path depth, then inbound-link count, then alphabetically. | Both verified defects hurt the Mac panel today, independent of this feature. |
| A6 | **One inserted-text rule:** bob's vault-relative path without `.md` (`[[sase]]`, `[[2026/2026-11-21]]`), plus `\|Alias` on alias matches (never a bare alias). | Matches ~7.3k existing machine-written Bob links and the Mac panel; immune to future basename collisions. Dissent and the one-line switch noted in §6. |
| A7 | **Call it "wikilink completion."** | `docs/completion.md` already reserves "completion" for shell completion; the Mac doc is literally titled wikilink-completion. |

## 4. Recommended design

### 4.1 Architecture: one controller in bob-navigation-hotkeys

**Home: `bob-navigation-hotkeys`, as a sibling (and superset) of
`logRecall`.** This was the swarm's main structural dispute — gem argued for
`bob-ledger-tools` — resolved on three facts:

- The keyboard-arbitration problem *is* the feature's hardest problem, and the
  arbiter (the recall band) lives in nav-hotkeys. One controller owning both
  modes eliminates the cooperative cross-plugin yielding protocol gem's design
  needs (which would require editing nav-hotkeys anyway).
- ~10 of the 14 surfaces already call `logRecall.attach`. Making the new
  controller back-compat with that call (`logRecall.attach` becomes a thin
  wrapper that enables links by default) gives those surfaces completion with
  **zero call-site changes**.
- The consumption precedent already points this way: block-id-prompt consumes
  nav's band UI today, while ledger-tools provides *data* APIs (`logs`,
  `freshness`) consumed by nav. UI kit in nav, data in ledger is the existing
  layering; ledger's Intention/Record cards feature-detect
  `api.proseField` exactly as block-id-prompt feature-detects `logRecall`,
  failing open to plain typing.

**New API: `bob-navigation-hotkeys.api.proseField` v1** (root stays 3;
feature-detect the namespace):

```js
proseField.attach({
  inputEl,              // <input> or <textarea>
  sourcePath,           // string | () => string — what [[# and [[#^ resolve against
  recall: kind | null,  // existing log-recall kind, or none
  links: { notes: true, headings: true, blocks: true },  // per-host capability
  minOffset: () => 0,   // e.g. end of the parsed date token in the scheduled stage
  bandHost, density, scope, ownKeys,
})
// → { handleKeydown, backOut, isOpen, isBusy, rebindInput, detach }
```

`sourcePath` is mandatory context, not a UI guess (cdx): an intention resolves
`[[#` against the pinned day/period note, a work summary against the task's
residence note, even when launched from a daily note. `rebindInput` (gem)
survives the Intention/Record cards' repaint-on-refresh lifecycle; `detach`
runs on stage exit and `onClose`.

**Candidates: Obsidian's in-memory metadata, never a subprocess.**
`vault.getMarkdownFiles()` + `metadataCache.getFileCache()` (frontmatter
aliases via `parseFrontMatterAliases`, headings, blocks), built lazily on the
first `[[` (~10 ms for ~7k files), updated incrementally on vault/metadata
events. This also sees unsaved buffers — the notes Bryan just created and now
wants to link — which a disk scan never can. Block previews hydrate lazily
from `cachedRead` for the visible rows only, keyed by `(path, mtime)`, with a
monotonic request token so stale async results are discarded.

**Tiers: JS port of `note_catalog/tiers.rs`, pinned by shared fixtures.**
Second structural dispute: cld wanted a cached `bob capture-complete '//'`
catalog fetch; grk/gem/mus wanted a port. The port wins — instant, offline,
mobile-safe, no staleness window — and drift is bounded the same way
`log_recall` fixtures already bound Rust↔JS↔Swift: a
`tests/fixtures/wikilink_complete/vectors.json` generated by a bob-cli test
(token spans, replacement ranges, tier classes, top-N ranking) and mirrored
into bob-plugins, so a policy change in either repo fails the other's CI
instead of drifting silently.

**Ranking** (faithful to bob plus the phase-0 fix): tier (living → archive →
hidden) → match kind (exact → prefix → word-boundary → acronym → substring,
each against alias → stem → path) → **depth, then inbound-link count
(`resolvedLinks`), then recency, then alphabetical**. Empty `[[` shows a short
deliberate set — `sourcePath`'s note, its area/project, notes linked from
`sourcePath`, then `workspace.getLastOpenFiles()` — never an alphabetical
vault dump, and never new cross-session usage tracking (cdx). Archive rows
stay out of the empty-query list, and appear dimmed and last otherwise. Cap at
~8 visible rows, not bob's capture-scale 20.

### 4.2 Field model (pure, unit-tested, mirrors `capture_links.rs` minus the bug)

- Open at the last unescaped `[[`/`![[` before a collapsed caret on the same
  line, not closed before the caret, not inside a backtick code span, not
  escaped (`\[[`). A non-empty selection, IME composition (`isComposing` plus
  composition events), and paste never open the band — a pasted `[[x]]` stays
  inert.
- Stages: target (until `#`/`|`), heading (after `#`), block (after `#^`);
  caret inside the `|alias` tail completes nothing (author's display text is
  theirs — unanimous).
- **Field end: the existing `]]` when it follows the caret before any newline
  or new `[[` (replace through it, reuse it exactly once); otherwise the
  caret.** Never the line end — that is the phase-0 fix, and it matches
  Obsidian's own editor.
- Accept: replace the span with `insert_target` (+ `|Alias` / `#Heading` /
  `#^id`), append `]]` only if absent, land the caret after `]]`. Insert via
  `document.execCommand('insertText')` with a `setRangeText` + `input`-event
  fallback so **one native Ctrl+Z restores the typed query** — cdx is right
  that execCommand is deprecated and this exact behavior must be proven by the
  first-host spike on the shipped Electron version, not assumed. (The recall
  band's value-assignment fill loses undo; don't copy it.)
- Offsets are UTF-16 code units end-to-end in JS; never split a surrogate;
  bob's byte spans never cross the boundary unconverted (Mac path only).
- Dismissal memory (gem/cdx): Esc records the token; the same unchanged token
  does not re-pop until a meaningful edit or caret re-entry. No cooldown
  timers.

Shared test vectors must include: `Discuss [[pla▏ tomorrow` (trailing prose
survives), `[[pla▏]]` (closer reused once), `[[Old▏#Overview|our plan]]`
(authored heading and label preserved), `` `[[x` `` (code span inert), emoji
and RTL neighbors, multiple links on one line, and caret-in-alias.

### 4.3 Keyboard contract: one arbiter, four layers

Routing order, enforced in one place: **IME → link band → recall → host
(stage/picker/modal)**. The controller listens in capture phase and registers
on the modal scope, so Esc beats the modal's own Esc while the band is open.

| Key | Band open | Band closed (today's behavior, unchanged) |
| --- | --- | --- |
| ↑/↓, Ctrl+P/N | Move link selection, by row key, clamp with edge bump | Recall navigation |
| **Enter** | Accept selected row — insert only, keep prompt open. Zero matches: consume + dismiss, never submit | Host submit |
| **Tab** | Accept selected row | Host traversal (e.g. schedule-review field cycling) |
| `#` / `^` on a note row | Drill: insert `target#` / `target#^`, stay open in heading/block stage | — |
| `\|` on a note row | Accept target + `\|`, close band, caret ready for custom alias | — |
| Esc / Ctrl+[ | Close the band only — one layer per press, per `q-and-ctrl-bracket-mirror-esc` | Recall back-out, then host ladder |
| Shift+Enter (textarea) | Host newline; the newline ends the token | Newline |
| `q`, printable chars | Type and re-filter | Type |
| Backspace through `[[` | Close band | Host |
| Click a row | `mousedown` → `preventDefault()` (never steal focus — the successor picker's inline input commits on blur), `click` accepts | — |

The Tab dispute (cdx alone wanted Tab-to-leave) resolves against cdx on
project precedent: `relation-card-tab-accepts-ctrl-d-hides` establishes "Tab
accepts or completes the top match" as Bob's convention, and the band only
claims Tab while the user has deliberately typed `[[`. Key-repeat guards stop
a held Enter from accepting and then saving; the existing Alt+F repeat swallow
and successor-picker Enter guard stay authoritative above the band.

While the band is open, the USED BEFORE band is suppressed (hidden in shared
hosts; dimmed and pointer-inert where it must keep its slot) — the same
mutual exclusion bob already applies between `work_log` phrases and `[[`.

### 4.4 Visual design

Render the link list **in the recall band's pinned-height slot** where one
exists; hosts without recall get the same band under the field, five 24 px
rows, the recall band's 120 ms fade, reduced-motion safe. This was the third
dispute (gem wanted a caret-anchored, body-portaled popover): the band wins
because zero layout shift and a fixed eye line are established Bob principles
(the Mac idle agenda's "fixed eye line", the recall band's `pinnedSlots`),
single-line inputs make caret-anchoring pointless, and the band already
coexists with every host including the successor picker's dense inline row.
Caret-anchored placement in the reflection `<textarea>` is a phase-2 polish
(mirror-div measurement), not a v1 requirement; gem's `mousedown.preventDefault`
and multi-window (`ownerDocument`) discipline carry over regardless.

```text
 Release task — In Progress → Ready
 ┌───────────────────────────────────────────────────────────────┐
 │ Unblocked by the [[sase_bl▌                                   │
 └───────────────────────────────────────────────────────────────┘
 🔗 LINK  sase_bl                                        3 notes
 ▍ 󰈙  sase_blog_zettel                              album · 41 ⇠
    󰈙  sase_blog                                    ref/
    󰈙  sase_blog_zettel_waves              done/ · Archived
    ↵ inserts [[sase_blog_zettel]]
 ⇥ ↵ Insert · ⌃N ⌃P Move · # Heading · ^ Block · esc Close
```

- **Rows reuse the Mac `CompletionRowContent` grammar** so both surfaces read
  alike: icon (Lucide via `setIcon`: `file-text` note, `calendar` daily/period,
  `book-open` ref/, `hash` heading, `pilcrow`/`^` block, `corner-down-right`
  alias), primary name with the matched span emphasized via the existing
  safe-text `appendHighlighted` helper (never innerHTML), middle-truncated
  muted path (the filename always survives), right-aligned quiet capsules only
  where they change interpretation: `Alias`, `H2`, `^id` or block preview,
  `Archived` (dimmed row).
- **Selection** is the recall treatment: `color-mix` accent fill ~10–14% plus
  a left accent bar; theme variables only (`--interactive-accent`,
  `--background-modifier-border`, `--radius-m`), raised contrast under
  `prefers-contrast: more`; legible in light, dark, and high-contrast.
- **The detail line `↵ inserts [[…]]` shows the exact bytes before they are
  written** — the single best reliability affordance in the swarm's designs
  (cld, from the Mac panel's detail strip).
- **Quiet states:** alias stage → "Alias — type the label, `]]` to finish";
  no matches → "No note matches `xyz` — keep typing or esc"; index failure →
  no band at all, never a notice per keystroke, never replacing a host's
  write-error or retained retry.
- **Unresolved-link hint (A4):** once the draft holds a complete `[[…]]` that
  resolves to nothing, one faint warning chip under the field ("`foo` — no
  such note"). Informational only; Bob never refuses Bryan's text.
- **Accessibility:** editable-combobox pattern for single-line inputs —
  `role=listbox`, `role=option`, `aria-activedescendant`, `aria-expanded`,
  focus stays in the field, a polite live region announcing "Note 2 of 8:
  sase". cdx's caveat stands: ARIA 1.2 defines combobox input as single-line,
  so the reflection textarea keeps multiline textbox semantics with the listbox
  relationship validated in VoiceOver/NVDA rather than blindly role-stamped.

### 4.5 Reliability checklist (release criteria)

1. Never destroys text after the caret (phase-0 fix + trailing-prose vectors).
2. Never submits a half-typed link; a held Enter cannot accept-then-save.
3. One native undo step restores the typed query (spike-verified).
4. Survives Intention/Record card repaints (`rebindInput`), stage exits, modal
   close, plugin unload, and pop-out windows.
5. Fails open everywhere: no nav plugin → prompts work unchanged; missing
   metadata or thrown matcher → no band, text intact; mobile without a needed
   API → no-op attach.
6. Stays quiet: no band in identifier fields, code spans, `\[[`, paste, IME
   composition, or non-collapsed selections.
7. Never writes the vault: no note creation, no block-ID minting, candidate
   lookup is read-only, and a renamed/deleted candidate re-resolves by
   identity or refuses with text retained.
8. Drift-proof: prose fields opt in declaratively; a contract test enumerates
   the allowlist; a lint fails any new modal input that declares neither
   prose nor identifier; `vectors.json` parity pins Rust↔JS.
9. Privacy: paths, aliases, headings, previews never logged or persisted.

## 5. Scope and phasing

### 5.1 The allowlist (merged inventory, 14 Obsidian surfaces + 1 Mac)

**Via existing `logRecall.attach` — zero call-site changes (phase 1):** work
summary / unlink (block-id-prompt `090`), task-link-lane and lane-release
summaries (nav `196`, `190`), schedule-review reason+summary and
schedule-work-log (nav `370`), lane-release-reason and cancel-reason (nav
`380`), rotten keep and batch keep (nav `195`, `192`), successor inline cancel
(nav `206d`). **Explicit attach (phase 2):** Intention Card intention /
summary inputs and reflection textarea (ledger `297cc`), Record Card text /
list stages (ledger `242q`), Record Card **link** stage upgraded to a
`mode: "field"` consumer of the same engine (retiring the divergent
`recordCardLinkCandidates`), Notebook-create summary (nav `685`), Task-from-
email (bob-mail `040`), Task Card scheduled inline reason via `minOffset`
(completion active only in the reason tail after the parsed date token).

**Excluded, must never trigger:** picker/filter queries, block-ID and every
rename/identifier field, bank fields, album schema fields, copy-chip and
Command Mode payloads, email To/Subject/compose, and — until the gcal escaping
contract changes — the **Mac event-note editor** (verified: `escape_note_inline`
would corrupt completed links).

### 5.2 Phases

| Phase | Repo | Content |
| --- | --- | --- |
| 0 | bob-cli | Fix the unclosed-`[[` replacement range (ends at caret) and the tie-break (depth → inbound links → alphabetical). Generate `wikilink_complete/vectors.json`. The Mac panel benefits immediately; `!`-marked only if any JSON contract shape changes. |
| 1 | bob-plugins (nav, block-id-prompt) | `api.proseField` v1: pure field model + LinkIndex + tier port + LINK band; `logRecall.attach` wrapper enables links on the ~10 recall surfaces. Notes + aliases + headings + single-note blocks. Unit vectors, parity fixture, key-layering tests, undo/IME spike in two real hosts (one recall input + the reflection textarea) **before** the full sweep. `bob plugins sync`. |
| 2 | bob-plugins (ledger, nav, mail) | Intention Card, Record Card (text/list + link-stage convergence), Notebook, Mail, scheduled `minOffset`. Unresolved-link hint. Vault-wide `[[##`/`[[^^`. Optional caret-anchored placement for the reflection textarea. |
| 3 | bob-cli + bob-mac-capture | Additive `capture-complete --links-only` (with a short alias, per cli_rules) that runs only the link providers with an explicit destination — no capture routes fabricated. Wire the Mac Pull-In cancel reason through the existing `CompletionList`. Watch the exact-SHA macOS CI run to green. |
| 4 (optional) | bob-plugins | `((` task wikilinks in prompts via block-id-prompt's `TaskWikilinkIndex`, reusing its existing block-ID transaction — only if Bryan wants a vault-write-capable picker inside prompts after living with `[[`. |

Once Bryan accepts the scope rule and the Enter rule, record them as a
decision ("`[[` completes in every Bob prose field; Enter finishes a link,
never submits it") through the memory-write path, so the next prose prompt
inherits the contract instead of re-deciding it.

## 6. Open questions for Bryan

1. **Inserted link form.** Recommended: bob's vault-relative path (consistency
   with every machine-written link and the Mac; never ambiguous). gem and cdx
   preferred Obsidian's shortest-stem / preference-honoring form, which reads
   cleaner for nested notes (`[[2026-11-21]]` vs `[[2026/2026-11-21]]`). It is
   a one-line switch (`fileToLinktext`); whichever you pick should be one
   setting both the prompts and (eventually) the Mac honor.
2. **Exact-match vs tier.** Phase 0 keeps living-before-archive and only fixes
   tie-breaks. cdx would let an exact historical title beat weak living
   matches on deliberate queries. Defer unless burying exact archive titles
   annoys you in practice.
3. **Recall-history hygiene** (mus). `[[`-bearing phrases enter the recall
   catalog verbatim and go stale on renames (the vault text itself is
   repaired; the recall index is derived from it, so this may be moot — worth
   a 10-minute check during phase 1, not a design change).
4. **Mac event-note editor.** Keep excluded, or change `bob gcal`'s private-
   note escaping to leave valid wikilinks unescaped (a separate, explicit
   contract change with its own decision)?

## Recommended solution (one paragraph)

Fix bob's two verified wikilink-completion defects first — the unclosed-`[[`
range that deletes trailing prose and the alphabetical tie-break that buries
root notes — then build **one `proseField` controller in
bob-navigation-hotkeys** that owns each prompt's band and keys in two modes:
today's USED BEFORE recall and a new LINK mode opened by `[[`. Candidates come
from Obsidian's in-memory `metadataCache` (never a per-keystroke `bob` spawn,
measured at ~1 s); tiers and ranking are a JS port of bob's
`capture_links.rs` policy pinned by shared fixture vectors; accepted rows
splice bob's vault-relative link text with native undo and never touch text
after the caret. Enter and Tab insert and never submit; Esc/Ctrl+[ closes one
layer; `q` types. Ship the ~10 recall-band prompts with zero call-site changes,
then intentions, records (converging the record link stage), notebook, and
mail; then the Mac Pull-In reason via an additive `--links-only` flag — with
the event-note editor explicitly excluded until gcal's `[` escaping contract
changes. No note creation, no block-ID minting, no vault writes from
completion, ever.

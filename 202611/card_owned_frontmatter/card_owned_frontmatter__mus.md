# Property cards take over frontmatter: hide native Properties, add `=-` / `=+`

Researcher: `mus` (independent swarm report, `__mus` suffix).
Request: property cards take over all frontmatter properties — hide Obsidian's
built-in Properties section, add a read-only collapsible (collapsed by
default) properties section at the bottom of the card, add `=-` to
expand/collapse it, add `=+` to open a keyboard-first property editor at
least as powerful as Properties, and always show `created` concisely on the
card. Lead the design: intuitive, reliable, beautiful.

## Verdict

Yes — do it, with five adjustments (§1). The plan is directionally right:
today the cards already hide *some* native rows and the request finishes
the job. The current per-row hiding (`bob-property-card-owned-property` on
`data-property-key` rows, container untouched) leaves a confusing hybrid:
a card on top plus a rump Properties section below that still owns `Add
property` and whatever keys the card chose not to claim. Finishing the
takeover removes that split-brain and gives Bryan one keyboard-driven home
for metadata.

The risks are not in the idea but in scope: "all properties" on "all
notes", a full Properties-parity editor in one cut, and two new `=`
keymaps that collide with Vim's `=` operator. The recommended solution
(§8) ships it in two phases with the same fail-open guarantees the cards
already keep.

Recommended solution is in §8. Adjustments are in §1, critique in §2,
current-state evidence in §3, and keymap/editor/hiding details in
§4–§7.

## 1. Adjustments to the requirements (call-outs)

1. **Scope to card notes only — not every note in the vault.** The takeover
   can only live "at the bottom of the card" where a card mounts. That is
   today: canonical album records, album notes, day/week/quarter/year
   notes, and bank notes (the `bank` / `album` / `record` / day-period
   adapters on the shared `createPropertyCardHost`). A plain note with no
   card keeps native Properties unchanged. This is a scoping correction,
   not a rejection: the card family already defines the boundary, and
   generic notes have nowhere to put the section.
2. **The card section shows the complement, not a duplicate.** "All
   properties" should mean *every key has exactly one card home* — not
   that every key renders twice. Keys that already have first-class
   chrome (record `title` in the header, schema fields as rows,
   `created` in the footer; album `title`/`summary`; intention
   `intentions`/`summary`/`reflection`) stay where they are and do **not**
   repeat in the properties fold. The fold lists everything else:
   leftover/legacy keys, `Add property` keys the user invents, and (until
   typed) `null`/empty keys. Card-owned rows get a mirror affordance
   ("in card above · press `=+`") rather than a second value. This
   preserves the existing `coverage` model (`sheet` / `breadcrumb` /
   `footer` / `row` / `ghost` / `fold`) instead of breaking it.
3. **Collapsed-by-default is per-path session state, like card collapse —
   not a persisted setting.** The record card already keeps `collapsed`
   and `foldOpen` per path for the session, never in frontmatter or
   settings (`docs/record-card.md`: "Fold and collapse choices are not
   stored in frontmatter or plugin settings"). The properties section
   follows the same rule with its own key (default collapsed `true`).
   Persisting it per note would dirty frontmatter on every toggle; a
   global "always start collapsed" is still satisfied because the default
   is collapsed.
4. **`created` lives in the footer always, fold or no fold.** Extend the
   existing record pattern (`added today, 7:55 AM` / `added yesterday` /
   `added Aug 8, 2025`; invalid values stay in the fold with lint) to
   every card species. The properties section never becomes the only home
   for `created`.
5. **Ship the viewer first, the editor second.** `=-` (read-only fold)
   is a small, safe change on top of the existing fold model. `=+`
   (full editor) is a second project roughly the size of the Record Card
   editor. Phase 1: container hiding + read-only section + `=-` +
   `created` footer. Phase 2: the `=+` editor. Bryan gets the visual win
   in weeks, not quarters, and Phase 1 is independently shippable even
   if Phase 2 slips.

## 2. Critique

### What is good

- **Kills the hybrid.** Today's contract (`docs/record-card.md`:
   "Native Properties rows hide only when the card is hide-eligible …
   Properties keeps `parent`, `type`, `created`, legacy and unrelated
   keys, and Add property") is the worst of both worlds for a finished
   card: two places to look, two mental models. Full-container hiding on
   hide-eligible mounts is the honest endpoint.
- **`=-` / `=+` are good mnemonics.** They sit beside the existing `==`
   card-editor chord (Vim normal mode, Live Preview) and `Ctrl+Shift+P`
   palette route. `=` already means "the card"; `-`/`+` read as
   fold/unfold and add/edit. Discoverability via a visible disclosure row
   with keycap hints (`▸ properties · N · =-`) mirrors the existing
   `＋ Label` ghost-row and `⊞ Edit` affordances.
- **`created` in the footer is proven.** The record card already does
   exactly this and it reads beautifully. Generalizing it is low-risk.
- **Read-only first is the right instinct.** A collapsed read-only view
   cannot corrupt data; it only needs the metadata cache plus source
   bytes, which is exactly what card painting already reads.

### What is risky or wrong as written

- **"Stop showing the built-in Properties section completely" needs the
   hide-eligibility gate.** Unconditional hiding breaks mobile, embeds,
   hover popovers, Source mode, broken schemas, missing reports, and
   failed mounts — every case where the card deliberately stays off
   today. The existing failure contract is explicit: on paint failure
   the host removes the mount and *releases ownership so native
   Properties are exposed* (`240c` header comment). Keep that contract
   and hide the container only while a healthy card owns the scope.
- **"At least as powerful as Properties" is a large hidden scope.**
   Obsidian Properties handles text, number, date/datetime, checkbox,
   list, and object/nested values, plus add/rename/delete, type
   coercion, and per-type widgets. Matching that plus "much easier via
   keyboard" is a full modal editor with stages, comboboxes, LINK-band
   completion, debounced previews, and Undo — i.e. a second Record Card
   editor generalized to untyped keys. Doable (the codebase has the
   patterns), but it must be phased and it must reuse the shared write
   discipline, not invent a new one.
- **The two keymaps collide with Vim.** `=` is Vim's `indentAuto`
   operator; `-` and `+` are line motions (`-` = up-first-non-blank,
   `+` = down-first-non-blank). Today `==` works only because a
   capture-phase gate intercepts the *second* `=` while a pending
   `indentAuto` operator with an empty key buffer is outstanding
   (`248m-plugin-schema-double-equals.js`, and the `docs` note that
   "vimrc `nnoremap ==` cannot beat Vim's `=` operator"). `=-` and `=+`
   (Shift+`=` on most layouts) need the same treatment: `=` then `-`,
   and `=` then Shift+`=`/`+`. Without a Vim-aware gate they reindent
   a line instead of toggling anything. This is solvable (§4) but it is
   the top implementation risk and must be designed, not assumed.
- **`=+` on many layouts is `=` then Shift+`=`.** The gate must key on
   `event.key` (`"+"` vs `"="`) *and* `event.code` where layout-proofing
   matters (the codebase already does this for `Alt+J/K`: "matched by
   `event.code` so nothing is typed"). Test US + at least one
   international layout.
- **"All properties in the card" duplicates identity.** Repeating
   `title`/`parent`/`type`/schema fields inside the fold doubles every
   record card. The complement rule (§1.2) fixes this with no loss:
   everything is still reachable from the card; chrome keys just keep
   their chrome.

### Would I take a different approach?

Only in mechanism, not direction:

- **Hide the container, not the rows.** Today each owned row gets
   `display: none` via `.bob-property-card-owned-property`
   (`styles.css` ~8657). For full takeover, add a scope class (e.g.
   `bob-property-card-hides-properties`) and hide the whole
   `.metadata-container` in that scope — heading, rows, and Add button
   together. Keep the per-row class as the fallback for the transition
   and for partial-ownership adapters. Container hiding is one rule,
   no per-key observer churn, and it removes the orphaned "Properties
   + Add property" heading that row-hiding leaves behind.
- **Do not call `processFrontMatter` from card paint paths.** Paint
   stays read-only (cache + source bytes). All writes go through one
   guarded session with optimistic overlay + `expect` fingerprint +
   Undo, exactly like the record write machine (`bob records update`
   with `inverse_ops`; see `docs/record-card.md` §"Write machine").
   For generic keys the backend is `app.fileManager.processFrontMatter`
   (the public API every community plugin uses) rather than a `bob`
   writer — but the session discipline (preview → apply once → Undo)
   is shared.
- **Prefer a modal editor over inline expansion for `=+`.** Inline
   stages work inside the Record Card editor because every field is
   typed by the album schema. Untyped frontmatter keys have no schema:
   type inference, add/rename/delete, and bulk rows fit a modal (same
   `Esc`/`q`/`Ctrl+[` close contract as every Bob panel) far better
   than an inline fold that fights the card's own collapse.

## 3. What exists today (evidence)

### 3.1 The card family and the shared kit

- Species registry: `album`, `record`, `day`, `week`, `quarter`,
   `year`, `bank` (`240f-plugin-property-card-species.js`;
   `data-card-kind`, tile + kicker word, never hue). Title slot,
   ownership, host lifecycle, and the `==` dispatcher are shared kit;
   adapters keep models/gates/builders (`240c` header).
- Mount point: the title slot between inline title and native
   Properties (`.bob-property-card-title-slot` as a direct child of
   Live Preview `.cm-sizer` / Reading `.mod-header`;
   `styles.css` ~8661). Live Preview cursor-on-title reveals raw
   Markdown while the card stays mounted.
- Per-species docs: `docs/record-card.md` (record), `docs/albums.md`
   (album card + title block), `docs/intention-card.md` (day/period
   intentions/summary/reflection), bank card in `docs/bob-ledger-tools.md`.
   Glossary `Property Card` confirms the kit owns chrome, the `==`
   dispatcher, owned-key hiding, host mount lifecycle, and title block.

### 3.2 Ownership today: per-row, gated, fail-open

- `240b-plugin-property-card-ownership.js`: one mount owns selected
   native rows in one view scope (desktop Reading/Live Preview only;
   Source, embeds, hover popovers, failed mounts, teardown keep native
   fields). Generation-bound handles + `MutationObserver` repaint on
   `data-property-key` changes; stale unloads cannot clear a newer
   mount; adapter slots are path-bound (`propertyCardSlotOwn/Release`).
- `242ka-plugin-record-sheet-properties.js`: the record adapter owns
   exactly its schema rows + ghosts + `title`-when-sheet, and only when
   `hideEligible` (healthy schema, desktop, `record_values_v1` present).
   Everything else — `parent`, `type`, `created`, legacy, unrelated —
   stays native today.
- CSS: owned rows `display: none !important` in both editor and
   Reading scopes; a separate rule keeps expanded embed Properties
   visible; title ownership hides `.inline-title` via
   `bob-property-card-owns-title` (`styles.css` ~8657, ~11977).
- Fail-open is load-bearing: paint throw → remove mount → release only
   that mount's ownership → native fields return; widget stays tracked
   for recovery (`240c` header + `refreshReading` catch).

### 3.3 The fold model already exists (record sheet)

- `242i-plugin-record-sheet-model.js` builds `rows` (schema values),
   `ghosts` (empty optionals → `＋ Label`), and `fold` (everything
   else + invalid `created` with lint). `foldOpen`/`collapsed` are
   session-per-path, never persisted. `242j-plugin-record-sheet-dom.js`
   renders header tools (collapse `▸/▾`, `⊞ Edit` with `==,
   Ctrl+Shift+P` title), rows, ghosts, and the fold with lint pills.
- Intention card owns exactly seven keys while live
   (`intentions`, `summary`, `summary_digest`, `summary_drafted`,
   `reflection`, `review_digest`, `review_drafted`;
   `docs/intention-card.md`). Same complement pattern as §1.2.
- `created` footer on records: valid date → footer (`added today,
   7:55 AM` …); invalid → fold with lint; absent → nothing. This is the
   template for the cross-card `created` chip.

### 3.4 Entry points and write machines

- `==` in Vim normal mode (Live Preview) on album/record/`bank.md`
   opens the card editor; counted `N==`, registers, Source/insert/
   visual, non-card notes keep Vim reindent (`docs/record-card.md`,
   `docs/albums.md`, `248m` gate). Palette `Edit record` /
   `Ctrl+Shift+P` is the non-Vim route; Command Mode vault rows reuse
   the same commands.
- Record writes never touch `processFrontMatter`: guarded `bob
   records update -i -` session, one op per field, 250 ms debounced
   dry-run preview, `expect` fingerprint, optimistic 5 s overlay,
   Undo from `inverse_ops`, YAML excursion via Source (`y`/`Ctrl+E`,
   Done). Identity keys (`parent`, `type`, `title`, `created`) are
   read-only in the record editor.
- Generic frontmatter reads go through
   `app.metadataCache.getFileCache/getCache(...).frontmatter`
   (`330-note-ready-model.js` is the shared reader). No card paint
   spawns `bob` or writes the vault.

## 4. Keymaps `=-` and `=+`: the Vim problem and the fix

### 4.1 Why this is the hardest part

Vim normal mode owns `=`. The `==` implementation documents it inline:
"a vimrc `nnoremap ==` never fires: CodeMirror Vim treats `=` as a
complete operator, so the second `=` reindents instead of matching a
mapping" (`248m` header). `=-` faces the identical fate: `=` starts a
pending `indentAuto` operator, then `-` arrives as its motion
(up-one-first-non-blank) — Vim happily reindents and moves. `=+` is
`=` then Shift+`=` (key `+`, code `Equal`): same operator, motion
`+` (down-one-first-non-blank). There is no vimrc mapping that beats
the operator; the codebase already learned this for `==`.

### 4.2 The proven pattern to copy

`248m-plugin-schema-double-equals.js` + `docs/develop/architecture.md`
+ `docs/bob-navigation-hotkeys.md` describe the working `==` gate:

1. Capture-phase `keydown` listener in Live Preview editors only.
2. Snapshot `cm.state.vim.inputState`: must be normal mode
   (not insert/visual/replace), no pending `operator` other than the
   just-pressed `=` (`indentAuto`), empty key buffer, no count, no
   register, unmodified key, not composing, not repeat.
3. Resolve the *target kind* (bank/album/record/…) from path +
   frontmatter through the property-card registry; refuse silently
   (leave the key with Vim) on any mismatch.
4. `preventDefault` + `stopPropagation` only on the second keystroke
   when the gate passes; otherwise do nothing so Vim reindent,
   `N==`, Source mode, and non-card notes behave exactly as today.

`=-` / `=+` reuse this file's snapshot helpers verbatim, with the
second-keystroke matcher extended from `key === "="` to `key === "-"`
/ `key === "+"` (accept `=`-with-shift producing `+`; check
`event.code === "Equal"` as the layout-proof fallback, mirroring the
`Alt+J/K` precedent). One shared `schemaEqualsChordGate` with three
arms (`=`, `-`, `+`) keeps the invariant in one place: *an extension
failure leaves the key with Vim.*

### 4.3 Behavior contract

- **Where:** Live Preview desktop editors on card notes only (same
   target-kind resolution as `==`). Reading view has no Vim operator
   to fight, so the same chords work there as plain key handlers on
   the focused card/scope. Source mode, embeds, popovers, mobile:
   chords do nothing (fail-open, Vim keeps the keys).
- **Modes:** normal mode only. Insert/visual/replace, pending counts
   (`3=-`), registers (`"a=-`), pending operators other than `=`,
   and `Ctrl/Alt/Meta`-modified keys all fall through to Vim/Obsidian.
- **`=-`:** toggles the properties section for the active note's card
   (expand ↔ collapse), session-per-path, no vault write. Focus stays
   where it was; the disclosure row announces via `aria-expanded`.
- **`=+`:** opens the property editor (§6) for the active note's card,
   focused on the properties section's current row or the first row.
   If the card is not mounted / not hide-eligible, teach once
   (`Not a card note` notice pattern, same as `RECORD_CARD_NON_RECORD_NOTICE`)
   and leave keys alone.
- **Non-Vim route (required, not optional):** every chord gets a
   palette command (`Toggle card properties`, `Edit card properties`)
   + `hotkeys.json`-bindable IDs + Command Mode rows, because
   non-Vim users, Reading view, and remapped-Vim setups cannot reach
   capture-phase Vim chords. The existing `edit-record` /
   `Ctrl+Shift+P` duality is the template.
- **No `q`-style single-key fallback.** `=-`/`=+` are two-keystroke
   chords starting from `=`; they do not steal bare `-`/`+` (used by
   zoom `g+`/`g-`, lists, and Vim motions).

### 4.4 Test hooks

The `==` gate is unit-testable without Obsidian (pure
`schemaDoubleEqualsGate(input)` over a Vim snapshot). Extend that
table: `=`+`-` normal/no-count/no-register/card-note → act;
`=`+`-` with count/register/insert/visual/non-card → refuse;
`=`+`+` with and without Shift; international-layout `code: Equal`
cases. The repo already has per-card e2e harnesses
(`obsidian-*-e2e.cjs`, `preview-property-cards.cjs`); add a matrix
page (cf. `preview-title-block-matrix.cjs`) covering all species ×
Reading/Live Preview × Vim on/off × mobile-width.

## 5. Hiding native Properties and the read-only section

### 5.1 Hide the container, keep the row class as fallback

Add one scope class, e.g. `bob-property-card-hides-properties`, set
alongside the existing title-ownership class while a healthy card owns
the scope, removed on teardown/failure/path-change (same lifecycle as
`bob-property-card-owns-title`). One CSS rule hides the native block
in both editor and Reading scopes:

```css
.cm-editor.bob-property-card-hides-properties .metadata-container,
.markdown-preview-view.bob-property-card-hides-properties .metadata-container {
  display: none !important;
}
```

Keep `.bob-property-card-owned-property` row hiding for the transition
and for adapters that never reach full eligibility. The existing embed
rule (expanded embed keeps native fields) stays: embeds never gain the
scope class. Mobile never gains it either (`propertyCardDesktop()`
gate in `240b`).

Why container over rows: it removes the orphaned `Properties` heading
and `Add property` button that row-hiding leaves, it is one selector
instead of per-key observer churn, and `Add property` correctly moves
into the card (fold `＋ Add property` row → `=+` editor) rather than
lingering in a half-hidden native block.

### 5.2 Read-only section: bottom of the card, collapsed by default

- **Placement:** last region of the card node, below schema rows /
   intention bands / bank setup, above (record) or integrated with the
   walk rail — the rail docks "at the bottom" today, so order the
   properties fold directly above the rail to avoid splitting card
   from navigation. Bank/album/day keep the same relative order
   (fold last, nothing after it).
- **Disclosure row:** `▸ Properties · N` / `▾ Properties · N` with a
   `=-` keycap hint, `aria-expanded`, full keyboard operability
   (click/Enter/Space, same as every card affordance). `N` counts
   complement keys (fold length), not chrome keys — the number answers
   "how much is hidden here". Empty fold (no complement keys): show a
   quiet `Properties · 0` ghost that still opens `=+` to add one.
- **Rows:** key (humanized, cf. `albumHeaderHumanize`), compact value
   (`recordSheetCompactValue` semantics: `—` for `null`, friendly
   dates, chips for choices, safe `http(s)` anchors, internal-link
   spans with hover previews; raw monospace + lint reason for invalid).
   Card-chrome keys are excluded per §1.2; each excluded key family
   gets at most one teaching row inside the *editor*, never in the
   viewer. `y` on a focused row jumps to Source on that YAML key
   (existing record-card contract: "`y` on a focused row … opens this
   record in Source on that YAML key").
- **State:** `propertiesOpen` per path, session-only, default
   `false`. Toggling never writes frontmatter/settings and never
   requests a report (same "folding never requests a report" rule as
   record collapse). `=-` flips it; the disclosure flips it; both
   repaint through the existing `recordSheetSetCollapsed`-style
   path-keyed map.
- **Paint inputs:** `metadataCache` frontmatter + source bytes for
   ordering/raw text, exactly like card paint today. No `bob` spawn,
   no write. Stale-cache window is covered by the optimistic-overlay
   rule below.

### 5.3 `created`: one footer chip on every card

Generalize `recordSheetCreatedFooter`: valid date → footer chip in the
card's footer band (`added today, 7:55 AM` / `added yesterday` /
`added Aug 8, 2025`, with full-timestamp tooltip); invalid → fold row
with lint; absent → nothing (no placeholder — absence is common off
records). Style: quiet, same size as the record walk footer / `Links
N/M` miniature, never a full row. Day/period/bank cards place it with
their existing footer content rather than inventing a new band.

## 6. The `=+` property editor: scope and design

### 6.1 What "as powerful as Properties" minimally means

Row-for-row parity with Obsidian's Properties panel for the value
shapes a vault actually holds:

| Capability | Minimum |
| --- | --- |
| Types | text, number, date/datetime, checkbox, list (ordered, comma-literal-preserving), link/wikilink |
| Key ops | add, rename, delete/unset, change type with coercion preview |
| Empty/`null` | explicit `—` states, Unset (`Ctrl+D` precedent), ghost `＋` rows |
| Validation | per-key parse + lint before apply; refusal keeps draft, never writes |
| Completion | `[[` note + `((` task LINK band (existing `proseField` v2), date words (`today`, `t`, `yesterday`, ISO) |
| Undo | per-path session Undo from inverse ops |
| Preview | debounced dry-run echo before Enter applies (250 ms precedent) |

Explicitly **out of v1**: nested objects/arrays-of-objects beyond a
validated-YAML text stage (render compactly, edit as text with
validation — the same honesty as the record editor's "refused with
hint" path), per-key type-widget plugins, bulk multi-file edit.

### 6.2 Modal, not inline — and why

The Record Card editor is the template: species badge + title +
subtitle (`<Album> › <Noun> · <path>` pattern), one selectable row per
key (ghosts included), stages expanding inline under the row, LINK
band for `[[`/`((`, browse keys (`j`/`k`/arrows/Ctrl+N/P, Tab
wraps, Home/End, digits pick on choice-shaped keys, `t` today on
dates, `Ctrl+D` unset, `u`/`Ctrl+Z` Undo, `y`/`Ctrl+E` YAML
excursion, `=` climbs where a parent editor exists, `Esc`/`q`/
`Ctrl+[` backs out stage → editor). Reuse means Bryan's fingers
transfer on day one, and the close-key helper (`241xc`) plus stage
machinery (`242r` typed stages, `297c*` intention editor inputs)
transfer with them.

An inline fold editor would inherit the card's collapse, the walk
rail, and Live Preview cursor-reveal without room for rename/type
pickers; a modal sidesteps all three and matches the "one focused
screen" precedent of Task Card (`Ctrl+Shift+P`) and Record Card
(`==`).

### 6.3 Write path: `processFrontMatter` behind the guarded session

Records keep their `bob records update` writer (schema validation
lives in bob). **Generic keys write through
`app.fileManager.processFrontMatter`** — the public API the forum,
Templater, and community plugins (Nested Frontmatter Properties,
Frontmatter Operator) converge on. Wrap it in the shared guarded
session: fingerprint-before (`metadataCache` frontmatter snapshot),
single-key ops, `expect`-mismatch → stale notice + retained draft +
retry (the record editor's "This record changed elsewhere" warning
verbatim), optimistic overlay ≤5 s or until cache matches, Undo via
stored inverse value, CRLF/BOM preservation (refuse-with-reason on
BOM notes per the record contract), save-every-open-pane after apply.
Never write from paint; never write from the viewer.

Type coercion previews reuse `MetadataTypeManager` where available
(`app.metadataTypeManager.getTypeInfo` / `registeredTypeWidgets`)
for display hints, but the editor keeps its own literal-preserving
parser (no `parseFloat`, no empty-to-zero — the record editor's rule)
so `023`, `1,2`, and trailing-space strings survive round-trips.

### 6.4 Keyboard map (draft, to be frozen in the plan)

- Browse: `j`/`k`, arrows, Ctrl+N/P, Tab/Shift+Tab (wrap), Home/End,
   `/` filter; Enter opens stage; digits on a key row jump, not type.
- Stage: text auto-grow (Enter saves, Shift+Enter closes-without-save
   in text; plain Enter in single-line inputs saves); `[[`/`((`
   LINK band with the band-owns-arrows rule; `t` today; `Ctrl+D`
   unset; `u` Undo; `y` Source-on-key; `Esc`/`q`/`Ctrl+[` close.
- Editor: `Ctrl+S`/quiet-Enter save-and-stay patterns from the bank
   editor where they fit; `=+` re-pressed focuses the editor if open.
All chords inert in IME/composition, announced with `aria-selected`
and "<Label>, field N of M" live regions (existing browse-keys
pattern).

## 7. Reliability, beauty, and rollout notes

### Reliability (non-negotiable, carried over)

- Fail-open everywhere: non-card note, mobile, Source, embed,
   popover, canvas, broken schema, missing report/capability,
   missing metadata, ambiguous parent → card off or card-without-hiding
   + native Properties visible. No new throw path may leave native
   Properties hidden with no card.
- Generation/path-bound ownership for the container class (copy the
   `240b` slot discipline: stale binding cannot release a newer mount;
   one adapter's teardown never clears another's owner).
- `metadataCache` races: debounced repaint, optimistic overlay with
   expiry, stale-write refusal with retained draft (record-editor
   wording), queued-save invalidation before rebase.
- Perf: fold render is memo-built per frontmatter fingerprint; large
   frontmatter (dozens of keys) virtualizes nothing but renders rows
   lazily under the collapsed default — collapsed cards pay ~one row.
- Settings: no new persisted settings in v1 beyond nothing; session
   keys only. If Bryan later wants "start expanded", add one boolean
   then.

### Beauty (what "beautiful" concretely means here)

- One title, one fold, one footer per card. No duplicated keys, no
   orphaned native heading, no `Add property` in two places.
- The collapsed row is the whole feature at rest: species-tinted
   hairline, `▸ Properties · N`, `=-` keycap, and the `created` chip
   already visible in the footer — informative without opening.
- Values render like the rest of the card (chips, links, friendly
   dates, `—` empties), never raw YAML dumps. Lint is a quiet pill,
   not red ink.
- Narrow (<28 rem) keeps one-line disclosure with full accessible
   name; focus rings and hover previews match card rows.

### Rollout

- Phase 1 (viewer): container-hide + complement fold + `=-` +
   commands + `created` footer on all species + matrix preview page +
   e2e on the existing harnesses. Shippable alone.
- Phase 2 (editor): `=+` modal per §6 behind capability/desktop
   gates, read-only-with-YAML-route when unwritable (the "Update bob
   to edit here" precedent). No Phase-2 work blocks Phase 1.
- Docs: update `record-card.md`, `albums.md`, `intention-card.md`,
   bank docs, and `bob-navigation-hotkeys.md` key tables; the
   `docs/` inventory check (`npm run docs:check`) stays green.

## 8. Recommended solution

1. **Adopt the five adjustments in §1** (card-notes scope, complement
   fold, session collapse, footer `created`, two phases).
2. **Phase 1 — takeover viewer:**
   - Add `bob-property-card-hides-properties` scope class + container
     rule; set it only on hide-eligible healthy mounts (record:
     existing `hideEligible`; album/day/bank: define the same
     three-part gate — desktop + valid subject + required report —
     and document each).
   - Build the complement fold as shared kit (not per-adapter):
     input frontmatter → exclude chrome keys per species → rows with
     compact spans + lint → `N` count → session `propertiesOpen`.
   - Wire `=-` through the extended `==` capture gate (§4.2) + palette
     commands + hotkeys + Command Mode rows; disclosure row with
     `aria-expanded` and keycap hint.
   - Generalize the `created` footer chip to album/day/period/bank.
   - Matrix preview + e2e + docs updates. Ship.
3. **Phase 2 — `=+` editor:** one modal on the Record Card editor
   chassis (§6.2), `processFrontMatter`-backed guarded session (§6.3),
   keyboard map (§6.4), parity table (§6.1) as acceptance criteria,
   invalid/nested → validated text stage, Undo + YAML excursion
   included. Read-only + YAML route when unwritable.
4. **Explicit non-goals for this project:** no takeover on non-card
   notes; no persisted fold state; no bulk multi-file edit; no custom
   per-type widget API; no `processFrontMatter` calls from paint paths;
   no bare-`-`/`+` key theft; no mobile editing.
5. **Acceptance bar:** every card species shows zero native Properties
   while healthy on desktop Reading + Live Preview and restores them
   on every fail-open trigger; `=-` toggles with no vault write;
   `=+` round-trips every parity-table type with Undo; `created`
   visible collapsed on every species; Vim `=`, `N==`, counts,
   registers, and reindent untouched off-card; full e2e green.

## 9. Open questions for Bryan

1. Should the properties fold offer a "show card keys too" debug row
   (for inspecting `title`/`parent` raw values), or stay strict
   complement with the `y`-to-Source route as the only raw view?
2. Is session-only collapse right for the properties section, or do
   you want one global "properties start expanded" toggle later?
3. For `=+` v1, is validated-text editing acceptable for nested
   objects (with full viewers), or do you hand-write nested objects
   often enough to need a structured nested stage in v1?

---

### Sources checked (no peer reports opened)

- `plugins/bob-ledger-tools/src/240b-plugin-property-card-ownership.js`,
   `240c-plugin-property-card-host.js`,
   `240d-plugin-property-card-host-editor.js`,
   `240f-plugin-property-card-species.js`,
   `240g-plugin-property-card-title-block-dom.js`,
   `242ka-plugin-record-sheet-properties.js`,
   `242i-plugin-record-sheet-model.js`,
   `242j-plugin-record-sheet-dom.js`,
   `248m-plugin-schema-double-equals.js`,
   `241xc-plugin-card-close-keys.js`,
   `330-note-ready-model.js`, `styles.css` (owned-property,
   title-slot, title-ownership rules).
- `docs/record-card.md`, `docs/albums.md`, `docs/intention-card.md`,
   `docs/bob-navigation-hotkeys.md`, `docs/develop/architecture.md`.
- Vault `obsidian_vimrc.md` (`:`/Command Mode, bracket walks, `g:`,
   `gy` precedents); glossary `Property Card` (+ linked `Bank Card`,
   `Period Note`, `Intention` definitions).
- Obsidian community/API grounding: `app.fileManager.processFrontMatter`
   as the public frontmatter write API; `metadataTypeManager`
   widget/type-info extension point; `.metadata-container` /
   `.metadata-property[data-property-key]` / `.is-collapsed` selectors
   and CSS-hiding precedents from forum and plugin sources.


### 3.5 Frontmatter keys in the wild (why "complement" matters)

- Records: `parent`, `type`, `title`, `created` + album schema fields
   + legacy + user keys. Album notes: `type: [[album]]`, title/summary
   plumbing, schema under `record:`. Day/period: `intentions`,
   `summary`, `reflection` (+ digests/drafts). Bank: `bank` key today
   (`propertyCardOwnBankKeys`). A literal "show every key in the fold"
   would duplicate the header, every schema row, and the footer on
   every record — hence the complement rule.

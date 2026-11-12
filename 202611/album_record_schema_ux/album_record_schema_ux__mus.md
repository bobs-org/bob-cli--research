# Album `record:` frontmatter in Obsidian: render it right, edit it easily

Research by `mus` · 2026-11-12 · context: `bob-cli-k3` album epic, `record` schema UX

## Verdict up front

Keep the nested `record:` mapping in album frontmatter exactly as it is.
Never ask stock Obsidian Properties to render it — it cannot, by design.
Hide the raw `record` property on album notes only, render a Bob-owned schema
card in the album header (already planned in `bob-cli-k3.7.1.4`), and add the
one thing that plan is missing: a structured **Edit schema** modal so the field
is modified through a validated form, never hand-edited YAML. That combination
is the only option found that is simultaneously intuitive, reliable, and
beautiful. Everything else either renders badly, edits dangerously, or requires
a parser migration with a large blast radius for zero user gain.

Concretely, the recommendation is:

1. **Hide** `.metadata-property[data-property-key="record"]` on album-note
   surfaces only (Reading + Live Preview, view-scoped class, full cleanup —
   as the `album-header` phase already specifies). Source mode keeps raw
   editing as the escape hatch.
2. **Render** a read-only schema card in the album header from the
   `bob albums list -f json` report: fields in declaration order with kind
   icons, required marks, list markers, and choice labels. Treat all content
   as text. This is already specced — keep it.
3. **Edit** through a new `Edit schema` affordance on that card that opens a
   structured modal (noun read-only, label/plural/dated_notes controls, an
   ordered fields table, per-field kind/choice editors, inline validation, a
   diff preview, Save/Cancel). Save via `processFrontMatter`, then let the
   existing debounced `bob albums sync` + report refresh confirm health, with
   one-click revert when the post-save check reports errors.
4. **No new storage format, no flattening, no body code block, no third-party
   Properties plugin dependency.** The nested YAML stays the single source of
   truth; the CLI parser, capture, Bases, and docs all keep working unchanged.

The rest of this note shows why, critiques the current plan, compares the
rejected alternatives, and details the modal UX plus the reliability and test
work needed to ship it.

## What I looked at

- The screenshot (`20261112_054646.png`): the `eat` album note. Properties
  shows `parent`, `type`, `summary`, `emoji`, `index_by`, `created` as clean
  native rows, then `record` as a truncated orange single-line string:
  `{"noun":"restaurant","label":"Restaurant","dated_notes":true,"fields":…`.
  Its property icon differs from the others (unknown-type glyph). The note
  body below is healthy: intro, `eat.base` link, and a styled `[!records]`
  index tally (104 restaurants, group counts).
- Vault bytes (`~/bob/eat.md`, `podcasts.md`, `tv.md`, one record note):
  the stored YAML is a perfectly ordinary nested mapping (`record:` with
  `noun`/`label`/`dated_notes`/`fields`/`legacy`). Nothing is corrupt; the
  ugliness is purely a renderer limitation. Record *notes* (`eat/…md`) are
  flat (`status:`, `category:`, `location:`) and already render natively —
  only the album-side schema object is affected.
- `docs/records.md` (album + schema contract), `src/native/records/schema.rs`
  (`RecordType`, `RecordField`, `FieldKind`: text/choices/date/link/url/
  number), `src/native/albums/registry.rs` (album claim/validation rules),
  and the `album_plugin_ui.md` child-epic plan (especially `album-header`).
- The `bob-ledger-tools` plugin source: shared album report service
  (`241l`/`241m`) exists; header/cards renderers are still in progress.
  No `processFrontMatter` writes exist in the plugin today — it is
  presentation-only, which matters for the edit design below.
- Obsidian API `v1.14.4` (`obsidian.d.ts`): there is **no property-widget
  registration API**. Plugins can post-process Markdown, add code-block
  processors, and call `fileManager.processFrontMatter`, but they cannot
  replace the Properties row widget for a key.
- Community evidence: stock Properties shows nested objects as raw text
  (the "Nested Frontmatter Properties" and "Nested Properties" plugin pages
  both describe exactly this gap and sell the collapsible-tree fix); the
  Obsidian forum notes frontmatter round-trips through a JSON object and
  loses original YAML styling; MetaEdit refuses to edit object-valued keys
  as text at all. Community guidance converges on "keep YAML keys flat" —
  advice the album schema deliberately (and justifiably) violates.
- Memory: `obsidian.md`, `cli_rules.md`, `docs.md` (via audited read);
  beads `bob-cli-k3`, `bob-cli-k3.7`, `bob-cli-k3.7.1` (+ `.7.1.3`, `.7.1.4`)
  via audited reads.

## Why it renders that way (three stacked causes)

1. **Stock Properties has no nested-object widget.** A key whose value is a
   mapping or a list-of-mappings is rendered as a single raw-text row — the
   orange truncated blob in the screenshot. There is no Obsidian setting that
   changes this; it is the documented stock behavior, which is exactly why
   community plugins ("Nested Properties", "Nested Frontmatter Properties")
   exist to paper over it.
2. **No plugin API to fix it in place.** `obsidian.d.ts` v1.14.4 exposes no
   `registerPropertyWidget` or equivalent. A plugin cannot substitute a
   pretty editor into the Properties table for `record`. The only
   plugin-side levers are CSS hiding plus rendering somewhere else (the
   note body/header), or writing bytes via `processFrontMatter`.
3. **JSON round-tripping.** Obsidian parses frontmatter into a JSON object
   and serializes it back on edit, so hand-edits through the Properties box
   would not only be ugly but would also reformat the block (key order and
   styling are not guaranteed to survive). For a load-bearing schema that
   104 record notes, capture routing, and three `.base` views depend on,
   that is an unacceptable editor.

## Critique of the current plan

The `album-header` phase (hide the `record` property album-only, render a
report-driven read-only schema card, breadcrumb, copy-capture affordance) is
**the correct render half** and should ship as specced. Specific praise:

- Hiding is scoped to the album note's own surface with cleanup on type
  change, file switch, unload, and non-album notes — the right blast radius.
  A global hide would be wrong: `record` never appears on non-album notes,
  and embeds/other panes must be unaffected.
- Sourcing the card from the `albums list` report (not a second YAML
  parser in JS) keeps one schema authority in Rust. Correct call.
- Read-only + "treat all content as text" is the safe presentation default
  for choice labels and wikilink-ish display text.

But as an answer to *this* request it is **incomplete in exactly the place
the request stresses**: editing. A read-only card plus "edit raw YAML in
Source mode" (the plan's stated editing story: "Source mode must still allow
editing raw frontmatter") does not meet "very easy for the user to modify".
Source-mode YAML editing of a 20-line nested block with indentation,
`values:`-shorthand-vs-mapping subtleties (`visited: {values: date}` vs a
choices mapping), reserved names (`parent`, `type`, `title`, `created` are
forbidden as field names), and noun-format rules is precisely the
error-prone workflow that breaks albums. `bob albums check` will *report*
the breakage, but only after the user has already made it. The plan needs an
edit half, not just a hide half. That is the main adjustment I am proposing,
detailed below — scoped as an addition to `bob-cli-k3.7.1.4` (or a small
follow-up phase), reusing its report plumbing and hide/cleanup work.

Secondary critiques, offered as friendly amendments rather than objections:

- The hide selector (`.metadata-property[data-property-key="record"]`) is
  inherently coupled to Obsidian's DOM. That is fine — there is no API
  alternative — but it needs a canary test and a graceful fallback (if the
  selector ever matches nothing, the card must still render and the raw row
  is merely visible, never deleted or rewritten).
- The card spec lists "field labels, kinds, list markers, required marks,
  and choice labels" but does not mention `dated_notes`, `legacy`, or the
  `index_by`/`index_facets` grouping controls that actually determine how
  the index below looks. The card should show at least a compact
  "notes are dated · grouped by location" line so the header explains the
  index, not just the fields. (`index_by` lives outside `record:` — display
  it, do not make it editable in the schema modal v1.)
- Accessibility/light-dark handling is already called out; add keyboard
  operability of the Edit affordance and focus return to the card on modal
  close, since this header will now own the schema's only easy editor.

## Options considered

| Option | Render | Edit ease | Reliability | Cost |
|---|---|---|---|---|
| A. Hide raw row + read-only card, edit in Source/CLI (current plan) | good | poor | medium (edits unvalidated) | already specced |
| B. Recommend a community nested-properties plugin | mediocre tree, not Bob-aware | medium (still raw keys) | poor (no validation, extra dep) | low, but wrong owner |
| C. Flatten schema to native flat keys | native rows | medium (many keys) | poor (parser + Bases + capture rewrite) | very large migration |
| D. Move schema to a body code block | plugin-rendered, pretty | medium (code block edit) | poor (second source of truth, parser rewrite) | large migration |
| E. Hide + card + structured Edit modal (recommended) | good | excellent | high (validated, previewed) | one modal + tests |
| F. New `bob albums schema set` CLI writer only | unchanged ugly row | medium (terminal only) | high | medium, misses in-context UX |

Why the losers lose:

- **B** outsources a load-bearing editor to an unowned plugin that knows
  nothing about nouns, reserved names, choice shapes, or `bob albums check`.
  It renders a tree, not an explanation, and adds a sync'd-vault dependency
  Bryan does not control. Laughably small gain for a real dependency cost.
- **C** (flat keys like `record_noun`, `record_field_status_values_…`) is
  the generative-AI answer and the worst one here. It rewrites the registry
  parser, every capture path, the `.base` formulas that read `note.status`,
  and all docs, to produce dozens of properties that are individually
  native but collectively illegible — still with no validation. Flat is
  only better when the consumer is stock Properties; our consumer is the
  Bob card, which can render nesting beautifully.
- **D** splits authority: frontmatter for identity, body for schema. Every
  reader (registry, capture, Bases discovery, `records show`) must learn
  two homes, and body edits fight bob-owned `[!records]` region writes.
  Cosmetic motive, structural price. Reject.
- **F** alone keeps the ugly row and forces context-switching to a
  terminal for an edit the user initiates while staring at the album. A CLI
  plumbing command may still be useful later (see rollout), but it is not
  the UX answer.

## Recommended solution in detail

**Storage: unchanged.** `record:` stays a nested mapping in album
frontmatter. No migration, no parser change, no Bases change, no capture
change. The vault bytes in `eat.md` today are already the right format.

**Render: the planned schema card, plus one summary line.** In the album
header, below the breadcrumb and the `＋ restaurant` capture affordance,
render the schema card from the report's decoded fields: one row per field
in declaration order — kind icon (text `abc`, choices `▤`, date `📅`, link
`🔗`, url `🌐`, number `#`), field label, `required` mark, `list` marker,
and choice labels (`🔖 To try · 💚 Liked · 🚫 Not liked`); plus a muted
summary line such as `notes are dated · grouped by location · 3 facets`.
Empty schema gets the planned helpful empty state, never an
empty-looking healthy card. Issues stay visible as issues. All
user-authored strings rendered as text (no Markdown interpretation, no
link resolution inside the card).

**Edit: an `Edit schema` button on the card opening a structured modal.**
This is the new piece. Rough layout:

- Header: album title + `record.noun` shown read-only (renaming a noun
  renames the kind everywhere — capture routes, folders, Bases filters —
  so v1 deliberately does not offer it inline; a rename flow, if ever
  wanted, is a separate guided migration, not a text field).
- Simple controls: `label` (text), `plural` (text, with the auto-plural
  hint), `dated_notes` (toggle with one-line explainer).
- Fields table in declaration order with drag/keyboard reorder, per-row:
  key (validated: lowercase, not reserved), label, kind picker
  (text / choices / date / link / url / number), toggles for required,
  list, suggest, and kind-specific extras (choices table of
  value → label rows; default; min/max for numbers). `legacy` patterns
  under an "Advanced" disclosure, collapsed by default.
- Live inline validation mirroring the registry rules (noun format,
  reserved ids, field-name and reserved-name rules, choice shape, the
  `values: date|url` vs choices-mapping distinction) with messages next to
  the offending row — the same messages `bob albums check` would print,
  shown *before* anything is written.
- Footer: `Cancel`, and `Review & save` leading to a compact YAML-ish diff
  preview (what changes, in words: "+ field `service` (suggest text)",
  "− choice `dropped`", not a raw YAML dump), then `Save`. Failed
  validation never writes. A stale-file guard refuses to save if the album
  changed since the modal opened (offer reload-and-reapply, never silent
  overwrite). Post-save, the existing debounced sync runs, the report
  refreshes, and if `check` reports errors the card shows them with a
  one-click **Revert** (the modal keeps the pre-save snapshot for the
  session).
- Escape hatches, deliberately secondary: "Copy as YAML" and "Open in
  Source mode" links in the modal footer. Power users keep their tools;
  the form stays the primary path.

**Write path: `processFrontMatter`.** It is the only supported Obsidian
frontmatter writer, it preserves all other keys, and it fires the metadata
events the report service already subscribes to. One caveat to verify in
prototype: round-tripping may normalize key order/whitespace of the
`record:` block (the forum-reported JSON-conversion effect). Album files
carry no comments and the parser is order-insensitive, so some
normalization is acceptable — but the prototype must confirm the diff is
cosmetic-only on `eat.md`/`podcasts.md`/`tv.md` before shipping, and the
revert path above covers surprises.

**What stays out of v1:** noun rename, `index_by`/`index_facets` editing
(display-only), bulk/templated field operations, mobile-specific layout
beyond responsive default, and any new CLI writer. If formatting churn from
`processFrontMatter` proves annoying in practice, the v2 answer is a
byte-preserving Rust writer (`bob albums schema set --json -`, hidden
plumbing the modal would call) — specified then, not now.

## Is this a good idea at all?

Yes, with the edit half added. The album model itself (schema versions with
data in the vault, broken albums fail alone, generated indexes) is sound
and already largely shipped; this request only fixes its one illegible
surface. The cost is bounded (one modal reusing landed report plumbing, no
format migration), the blast radius is contained (album-only hide, additive
UI, Source mode untouched), and the payoff is permanent: every future album
(`eat`, `podcasts`, `tv`, `movies`, bank…) inherits a legible, safely
editable schema. The only version of this idea I would reject is "make the
Properties row itself pretty" — impossible without Obsidian API support —
or any variant that moves or flattens the schema to satisfy stock
Properties. The schema format is not the problem; the editor is.

## Explicit adjustments to the requirements

1. Split "render properly" into hide + card (already planned — keep) and
   state openly that stock Properties will never render `record:` natively.
   Success = the user never needs to look at the raw row, not that the raw
   row looks good.
2. Promote "easy to modify" from Source-mode YAML to the structured modal
   above; demote raw YAML to escape hatch. Add this to `bob-cli-k3.7.1.4`
   (or a small `k3.7.1.6`-style phase), reusing that phase's report/hide
   work rather than landing read-only first and calling the request done.
3. Keep `record.noun` immutable in the modal v1. The request says "easy to
   modify this field" — the field that needs easy editing is the schema
   (fields, choices, labels), not the kind identity. Say this explicitly so
   a well-meaning implementer does not ship a rename text box that orphans
   104 records.
4. Add the summary line (`dated · grouped by …`) and the revert path to the
   acceptance criteria; add a DOM-selector canary test for the hide rule.
5. Docs: extend the album reference page with the card + modal behavior
   (the plan already requires this) and add one `docs/records.md` paragraph
   stating the contract plainly: nested `record:` is canonical, Properties
   shows it raw by Obsidian design, the card is the reader, the modal is
   the editor, Source mode is the hatch. Run `just docs-check`.

## Rollout and tests

- Prototype first: hide + card on `eat.md`, confirm the hide survives
  Reading/Live Preview/embeds/multi-pane/light-dark, and confirm
  `processFrontMatter` round-trips the three real album files with
  cosmetic-only diffs.
- Ship in `k3.7.1.4` scope or one follow-up phase; no new bead needed
  beyond that phase's checklist, but do not close `k3.7` until the modal
  (not just the card) is done, or file the modal as its own tracked phase
  so "easy to modify" cannot slip through the cracks.
- Tests: hide isolation (album vs non-album, embed, second pane, unload
  cleanup); card ordering/escaping/empty-state/broken-report; modal
  validation matrix (reserved names, bad noun, empty choices, min>max,
  `values` shape confusion); failed-validation-never-writes; stale-file
  refusal; save→sync→report-refresh integration; revert restores bytes;
  clipboard failure for the capture affordance (already specced).
- Gates: plugin build + renderer tests, `just docs-check`,
  `bob plugins sync` per the linked-repo rules, and a real-vault pass over
  `eat`/`podcasts`/`tv` (read-only `albums check` green before and after).

## Open questions for Bryan (need not block the render half)

1. Is `record.noun` immutability in v1 acceptable, or do you want a guided
   rename flow (rewrites folder? capture route? Bases filters?) designed
   separately?
2. Should the modal also own `index_by`/`index_facets` (grouping), or stay
   display-only there as I recommend? Grouping changes the index's look
   dramatically and deserves its own preview, so I kept it out — push back
   if you edit grouping often.



# Bulk capture: first item as a template

- **Researcher:** grk
- **Date of evidence:** 2026-10-15
- **Question:** Should `bob capture` (and Bob Mac Capture, as a thin client of bob) treat the first item of a bulk draft as a template, filling `{0}` `{1}` `{2}` … from each later item? Is that a good idea, what syntax should it use, and how should it be implemented?
- **Independent swarm report (`__grk`).** Does not consult peer swarm reports.

## Bottom line

**Build it, as a pre-parse expansion, not as a new capture kind.**

The job-application batch in the request is a real capture-panel pain: the same parent line, the same child bullet, and N records that differ in a company name, a block ID, and a URL. Today's grammar already bulk-captures independent items (`docs/capture.md` Multi-item capture). It has no way to say "this shape, those rows."

Do **not** parse `{1}` as a block ID, and do **not** let later items remain ordinary captures. `{` / `}` are outside the block-ID alphabet (`A-Z, a-z, 0-9 or '-'`, `BLOCK_ID_ALLOWED_CHARACTER` in `src/native/capture_block_ids.rs`). `@job_2026_apply_29:{1}` is `invalid_pomodoro_block_id` today. The only workable design is:

1. Split the draft on blank lines (existing `split_capture_draft`).
2. If item 0 contains unescaped `{N}` slots and at least one later item exists, treat item 0 as the template and every later item as a **field record**.
3. Substitute, then run the expanded items through the existing parser, planner, dry-run, and commit. Execution never sees `{1}`.

Keep the user's `{0}` `{1}` `{2}` slot spelling. Change the **row** spelling: space-separated tokens are the shorthand for the example, but they are too weak as the only rule. Surplus tokens join `{0}` so `Bank of America boa https://…` fills a three-slot template; `|` and one-field-per-line are the space-safe forms.

Mac Capture stays a thin client (`decisions:mac-capture-is-a-thin-client`). It submits the compact draft as one `bob capture`. Live `--dry-run` already renders `captures[]`, so expanded preview cards come for free once bob expands inside capture. The app later decodes new slot spans and a `template_row` need; it never learns the substitution rules.

I make twelve requirement adjustments, **ADJ-1…ADJ-12**, below. The full design is [Recommended solution](#recommended-solution).

---

## Is this a good idea?

**Yes, with a tight scope.** The evidence:

1. **The repeating shape is a capture thought.** The example is one Next-linked apply task plus a URL child, instantiated per posting. That is the same moment the panel is already open. Duplicating the boilerplate by hand, or leaving the panel to run `bob capture` in a shell loop, is the workaround this feature removes.

2. **Bulk capture already exists and is transactional.** Blank physical lines split items; the whole batch is planned against in-memory snapshots; any failure rolls back (`docs/capture.md` Multi-item capture; `src/native/capture/batch.rs`; `split_capture_draft` in `src/native/capture_language/draft.rs`). Templating should produce ordinary items that reuse that machine, not a second writer.

3. **Mac Capture already previews batches.** `bob capture --dry-run --format json` returns an ordered `captures` array; the app normalizes it, shows every block bob will write, and notifies `N items captured` (Bob Mac Capture README, live-preview / notification sections; `CapturePanelModel.previewResults`). Expansion inside bob is the preview.

4. **The example cannot parse today, so marker-position slots do not collide with valid captures.** Block IDs reject `{` and `}`. Routes reject them too (`is_route_token` is `A-Z a-z 0-9 _ -`). A draft whose first item is `@job_2026_apply_29:{1}` is already an error. Teaching it as a template hole is a new meaning for currently-illegal text.

5. **The grammar is already dense.** Capture tokens include `@` `@@` `:` `^` `+` `*` `&` `!` `=` `%` `#` `s:` `p:` `/` and session chains. A new *execution* kind would multiply that. A pre-parse rewrite that emits ordinary items is the same pattern as session-operator chains (`+2 =x` becomes two items before parse). That is the complexity budget this feature can afford.

The idea is **not** "add mail-merge to every capture." It is "when the first bulk item is a format string, the rest are rows." That is a good idea. An implicit `{N}` in *prose* of the first of two unrelated tasks is the residual footgun; **ADJ-1** and `{{` / `}}` cover it.

---

## Critique of the stated plan

The product intent is right. Several written requirements are inverted, underspecified, or will ship a worse capture than today if taken literally.

### 1. "Subsequent items are templates for the first" is the wrong polarity

The first item is the template. Later items are **records** that instantiate it. After expansion, the draft is equivalent to N ordinary captures, one per record. The request's own before/after example matches that reading. Name it that way in help, diagnostics, and the Mac status line.

### 2. Space-separated rows are enough for the example and too weak as the contract

```
Foobar foo http://foobar.com/career/some_foo_job
```

maps cleanly onto `{0}` `{1}` `{2}` only because the company name is one token, the slug is one token, and the URL has no spaces. Real apply rows look like `Bank of America`, `The New York Times`, `OpenAI, Inc.`. Capture already collapses whitespace (`tokenize_with_spans` / `normalize_task_text`), so empty fields cannot be expressed with tokens either.

If v1 is "split on spaces, arity must match," the motivating workflow fails on the first multi-word company. That is not a later enhancement; it is a hole in the example.

**Adjustment (ADJ-2, ADJ-3):** keep the one-line token shorthand, join extra tokens onto `{0}`, and accept `|`-separated fields and one-field-per-line records as the space-safe forms. Details in [Row syntax](#row-syntax).

### 3. `{1}` cannot survive the current grammar parser

`classify_pomodoro_token` calls `is_block_id(block_part)` and emits `invalid_pomodoro_block_id` when the ID is nonempty and illegal (`src/native/capture_language/editor_classify.rs`). `bob capture` takes the same path through `parse_pomodoro_route_token`. Expansion **must** run after blank-line splitting and **before** item parse. There is no "teach the block-ID parser about braces" option that keeps `{1}` as a typed hole *and* a valid ID.

### 4. Later items must stop being captures the moment item 0 is a template

Today each blank-line item is planned independently. A later item whose parent is a bare URL is a reference job (`claim_reference_item`). A later item `Foobar foo http://…` is an inbox task. Once item 0 is a template, those readings are wrong: the URL is field `{2}`, not a ref, and the line is not a task.

The request says this, but it is easy to implement as "also parse the rows as captures, then merge." That merge has no coherent spec (which markers win? do row child bullets append or replace?). **Adjustment (ADJ-4):** rows are field records, not capture grammar. Markers in a row are literal field text.

### 5. `@route:{1}` in the example is a Next + Task Link, multiplied

`@job_2026_apply_29:{1}` is Pomodoro-linked Next (`docs/capture.md` grammar table). Ten rows become ten Next tasks and ten Task Links under today's current/next Pomodoro. `plan.max_links`, `plan.max_next`, and `plan.max_ready_per_note` (default 5) already gate batches (`docs/plan.md`, `docs/capture.md` plan budget). Templating makes it easy to blow those caps in one paste.

That may be what Bryan wants for an apply session. It is still a loaded default. Preview plus existing `plan.strict` is the safety net; the feature should not add a second cap. Help should show both `:` (today) and `^` (ordinary open task, no link) in the template.

### 6. A CLI `--template` flag is the wrong opt-in

`cli_rules.md`: never add a subcommand under `bob capture` (free-text `TEXT` would swallow it). A long option is legal, but Bob Mac Capture submits the editor draft as `bob capture -- [TEXT]` with no extra flags (`BobProcessClient.captureParse` / capture live preview). Opt-in must live in the draft, the same way `@@route` does.

### 7. Do not rewrite the editor text to the expanded form

`capture-rewrite` already absorbs `@@` and switches `:` / `^` (`src/native/capture_language/rewrite.rs`). Expanding `{0}` in the editor would destroy the compact form while typing, fight undo, and desync the cursor. Expansion is a parse/execute transform, not a typing assist.

### 8. A lone templated item must not steal ordinary `{0}` prose

`Read RFC {0}` as a single inbox task should still capture. Activation when item 0 contains `{N}` **and** a later item exists is the right default (**ADJ-1**). While composing `@route:{1}` with no rows yet, the editor should treat the hole as incomplete rather than `invalid_pomodoro_block_id` (**ADJ-5**), because that token is already illegal as an ID.

### 9. Mixing "template + rows + an unrelated task" in one draft is not worth it

The request's subsequent items are all rows. A mixed draft (five jobs and `Buy milk`) has no unique parse. Fail closed: once item 0 is a template, every later item is a row. A second capture handles the unrelated task. Same posture as the all-URL ref-intake research for mixed drafts.

---

## Syntax

### Slot syntax: keep `{N}`

| Candidate | Why it loses to `{N}` |
| --- | --- |
| `{0}` `{1}` `{2}` (recommended) | Familiar (Python / C# / Rust `format`); works as a substring of `@route:{1}` so the marker stays one token; currently illegal as a block ID; `{{` / `}}` is the established escape |
| `{company}` named slots | Readable, but rows then need names or still fill by appearance order. Add later if positional arity becomes annoying. Do not mix named and numbered in v1 |
| `{0:spec}` format specs | Padding and date specs are a second language inside capture. Dumb substitution only |
| `$0` `$1` | Shell-like; `$` appears in money; still illegal in block IDs; no standard escape as clean as `{{` |
| `%s` / `%0` | Collides with clipboard `%` / `%N` / `%header` |
| `{{0}}` doubled braces as the slot | Heavier than the request; keep doubles for *escaping* |
| `<0>` / `^0` / `@0` | HTML-ish, or collides with caret / route tokens |
| `@@template` plus slots | Explicit, but a second opt-in on top of the slots themselves. Reopen if `{N}` in prose causes accidents |

**Slot grammar (v1):**

- A slot is `{` + one or more ASCII digits + `}`. `{0}` is the first field.
- Indices used in the template must be a contiguous set `0..K-1`. Holes (`{0}` and `{2}` without `{1}`) are a teaching error.
- The same index may appear more than once; every copy gets the same field.
- `{{` and `}}` in the template become literal `{` and `}`.
- No format specs, no `{name}`, no `${0}`, no nesting.
- Substitution is a string replace on the first item's raw source (parent line plus authored children), not a token rewrite. `Apply to {0}!` becomes `Apply to Foobar!` even though `{0}!` is one whitespace token today.

That last point matches the request's `!`: `claim_bang_item` only fires when the item **starts** with `!` (`src/native/capture_language/tokens.rs`). Trailing `Apply to Foobar!` stays prose.

### Row syntax

Apply the first matching rule to each later item. Arity is always `K` (the number of distinct indices in the template). Wrong arity is a teaching error naming the row's starting line and the missing or extra fields.

**Rule A — pipe-separated (space-safe one-liner).** If the item's parent line contains `|` and the item has no authored children, split on `|` and trim each piece.

```
Bank of America | boa | http://careers.bofa.com/some-job
```

**Rule B — one field per physical line (space-safe record).** If the item has exactly `K` nonempty physical lines, each line is a field in order. Strip one leading list marker (`- ` / `* ` / `+ `) plus the two-space nested form, using the existing authored-line classifier so a pasted Markdown list still works.

```
Bank of America
boa
http://careers.bofa.com/some-job
```

**Rule C — whitespace tokens, extras join `{0}` (the request's shorthand).** If the item is a single parent line with no `|`, tokenize with `tokenize_with_spans`. If the token count equals `K`, map 1:1. If it is greater than `K`, the last `K-1` tokens are fields `{1}`…`{K-1}` and everything before them, joined by a single space, is `{0}`. If it is less than `K`, error.

```
Foobar foo http://foobar.com/career/some_foo_job
Bank of America boa http://careers.bofa.com/some-job
```

both fill `{0}` = company, `{1}` = slug, `{2}` = URL.

Quoted fields reuse the `&"Shopping List"` decoder (decode escapes, strip one layer of quotes) so an empty field is `""` and a company with a pipe can still use Rule C.

**Why extras join `{0}`, not the last field.** In the motivating rows the last fields are a slug (block-ID alphabet) and a URL (no spaces). The title is the one that grows. Joining extras onto the URL would mis-parse `Bank of America boa http://…`.

**Rejected row spellings for v1:** CSV (commas in company names), JSON Lines (too heavy for the panel), YAML keys (more typing than the template saves), "repeat the full capture grammar on each row and overlay" (undefined merge).

### Opt-in (no extra sigil)

A draft is a template draft iff, after `@@` declaration lines are stripped, **the first remaining item contains at least one unescaped `{N}` and there is at least one later item.**

Rejected opt-ins:

- `--template` (Mac cannot pass it).
- A `@@template` / `@@fmt` declaration (slots already mark the item; a second keyword is more grammar for a rare accident).
- "Any item with `{N}` is a template" (would steal a later independent task that happens to contain `{0}`).

---

## Requirement adjustments

These change the request. Each is called out so a later plan can accept or reject it explicitly.

| ID | Adjustment | Why |
| --- | --- | --- |
| **ADJ-1** | Activate only when item 0 has `{N}` *and* a later item exists. A single item whose body contains `{0}` stays a literal task. | `Read RFC {0}` must not become an incomplete template. |
| **ADJ-2** | Surplus whitespace tokens on a one-line row join `{0}`. | Multi-word company names in the shorthand. |
| **ADJ-3** | Also accept `|` split and one-field-per-line records. | Space-safe rows without forcing quotes on every paste. |
| **ADJ-4** | Later items are field records, never captures. No mixing `Buy milk` into a template draft. | Bare-URL rows would otherwise become ref jobs; merge semantics are undefined. |
| **ADJ-5** | In the editor, `{N}` inside a marker that would be `invalid_*_block_id` (or an illegal route/section) is a template slot, and a slot-bearing first item with no rows reports `needs: ["template_row"]` instead of that invalid-ID diagnostic. | Live preview while typing the template. |
| **ADJ-6** | Expansion is a pre-parse text rewrite. No new `CaptureKind`. Expanded items reuse the existing planner, budget, deps, refs, JSON `captures[]`, and rollback. | Complexity budget; Mac preview is already batch-aware. |
| **ADJ-7** | Refuse `%` clipboard markers in the template. Refuse a template whose expanded form would be a session operator (`=x`, `=`, `+N`, …) or a whole-item `!note:id` / `/query` / `:` picker. | Clipboard is per-item and not N independent clips; operators are not instantiable shapes. |
| **ADJ-8** | `&` `*` `s:` `p:` `@route` in the *template* copy to every expanded item. They are not allowed as row grammar. | Shared deps/schedule are a real apply-batch need; rows stay data. |
| **ADJ-9** | After substitution, existing validators apply (block-ID alphabet, duplicate IDs in the batch, plan caps, URL routing). A field used as a block ID that is not `A-Za-z0-9-` gets a teaching error that names `{N}` and the alphabet. | Do not weaken ID rules to make templates "easier." |
| **ADJ-10** | `capture-rewrite` does not expand. The compact draft is what the panel submits. | Thin client; undo; cursor. |
| **ADJ-11** | No named reusable snippet library and no vault `_templates` lookup in v1. | One-shot panel paste; a catalog is a different feature. |
| **ADJ-12** | Mac work is decode-and-present only, and can trail bob-cli. Unknown span kinds already fall back to `.neutral` (`captureSemanticCategory`). | `decisions:mac-capture-is-a-thin-client`; additive JSON. |

---

## Prior art (what to copy, what to ignore)

- **Mail merge / Python `str.format`.** One document, N records, numbered holes, `{{` escape. This is the right mental model and the right slot spelling.
- **Org-mode capture templates (`%^{prompt}`).** Interactive prompts, one capture. Wrong for a pasted list of jobs.
- **Obsidian Templater / QuickAdd `{{VALUE}}`.** Named holes in a note template. Useful analog for named slots later; too much ceremony for a one-shot panel draft, and capture's job is to avoid opening Obsidian.
- **CSV import (Todoist, etc.).** Right for a spreadsheet, wrong inside a grammar that already uses commas in prose.
- **`xargs` / shell loops calling `bob capture`.** Works today, invisible to Mac Capture, and loses the atomic batch.
- **Capture's own session-operator chains.** A physical line of `+2 =x` becomes two items *before* parse. Templates should become N items the same way.

---

## Architecture

```
raw draft
  → split_capture_draft          # @@ lines stripped; blank lines → items
  → maybe_expand_template        # NEW: item 0 + rows → N ordinary item sources
  → parse_capture_item × N       # unchanged
  → plan / dry-run / commit      # unchanged
```

Hook point: immediately after `split_capture_draft` in `parse_capture_draft_with_clip_control` (`src/native/capture_language/draft.rs` ~line 627) and the parallel editor path `parse_for_editor`. Execution and `--dry-run` share the expansion so live preview cards show `Apply to Foobar!`, not `{0}`.

The editor path must **not** replace the original text. It classifies slots against the compact source:

- New `SpanKind::TemplateSlot` covering each `{N}` (and each `{{` / `}}` escape, optional).
- Optional `SpanKind::TemplateField` on row fields after split, so a too-short row can underline the parent line.
- New `Need::TemplateRow` (`template_row` on the wire).
- New editor modes `template` (item 0) and `template_row` (later items) so `claim_reference_item` never sees a URL-only row.

`bob capture-parse` JSON stays schema version 1 and grows additively:

```json
"template": {
  "slots": 3,
  "rows": 2,
  "indices": [0, 1, 2]
}
```

omitted when the draft is not a template draft. `items[]` keeps **physical** items and ranges (Mac uses those ranges). It does not switch to expanded items, because expanded offsets do not index the typed text (`docs/capture.md` / `capture-parse`: spans index the original TEXT).

`bob capture --format json` success is unchanged in shape: `captures` has one ordinary result per expanded item. Human output already numbers `1/N`.

### Why not classify `{1}` inside `classify_pomodoro_token`

That would special-case every marker family (`:`, `^`, `+`, project notes, globals). Expansion makes those families ordinary after substitute. The editor needs one slot walker over the first item's raw text, then the existing classifiers on the non-slot remainder (or a mask). Keep the walker in `capture_language`, next to `split_capture_draft`.

### Clipboard, operators, pickers

**ADJ-7.** A template that contains `%` / `%N` would clone one clipboard N times or read it N times; both are surprising. Refuse. Pickers (`:query`, `/query`, `!`, `+query`) and session operators are whole-item actions, not instantiable task shapes; refuse a template that claims those kinds even after a dummy substitution.

### Plan budget and uniqueness

Existing batch rules apply to expanded items: duplicate `^id` in one note, `plan.strict` on new Next/links, preimage checks, rollback. No new cap. Dry-run already surfaces `plan_link_cap_exceeded` and friends; Mac already shows that as preview failed.

---

## Bob Mac Capture

Contract: the app never splits drafts, never substitutes `{N}`, never decides that a later item is a row (`decisions:mac-capture-is-a-thin-client`; `AGENTS.md` / README: bob is the only grammar).

**v1 (bob-cli only, app still works):**

- Submit the compact draft as today.
- `--dry-run` returns N expanded captures; the preview stack already renders `previewResults`.
- New span kinds decode as `.neutral` until the app maps `template_slot`.
- `needs: ["template_row"]` is not in `pickerNeed(in:)` today (`CapturePanelModel` ~4571), so a template with no rows still dry-runs and shows bob's teaching error in red. Same pattern as other new incomplete states before the Mac phase.

**v2 (Mac decode):**

- Map `template_slot` to a palette category (indigo like block IDs, or a new `.templateSlot`).
- Treat `template_row` as a quiet incomplete: skip the doomed dry-run, status `Add a row under the template` (wording from bob, not invented in Swift).
- Batches already keep the **Capture** button. No new primary action.
- Do not rewrite the NSTextView to the expanded text.

Do not port `maybe_expand_template` to Swift. Tests on the Mac side are decoding tests (`decodeIfPresent` for `template`) and one palette mapping test, matching `CaptureRefPresentationTests` for `ref_url`.

---

## Risks

| Risk | Mitigation |
| --- | --- |
| Accidental activation: two ordinary tasks, first body contains `{0}` | **ADJ-1**; `{{0}}` escape; reopen `@@template` if this fires in real use |
| Multi-word fields | **ADJ-2**, **ADJ-3** |
| URL rows stolen as refs | **ADJ-4** + `template_row` mode before `claim_reference_item` |
| 15× `@route:id` blows Next / link caps | Existing strict mode and dry-run; document `^` vs `:` in help |
| `{N}` in a block ID while typing | **ADJ-5** |
| Grammar sprawl | **ADJ-6** (no new kind) |
| Mac / bob version skew | Additive JSON; unknown spans already `.neutral` |
| Empty fields | Quoted `""` on Rule C; empty `| |` segment on Rule A |

---

## Recommended solution

### What to type

The request's draft, unchanged, is accepted and means:

```
Apply to Foobar! @job_2026_apply_29:foo
- **URL**: http://foobar.com/career/some_foo_job

Apply to Bazbuz! @job_2026_apply_29:baz
- **URL**: http://bazbuz.com/career/some_baz_job
```

The same template also accepts:

```
Apply to {0}! @job_2026_apply_29:{1}
- **URL**: {2}

Bank of America boa https://careers.bofa.com/x

The New York Times | nyt | https://nytimes.com/careers/y
```

and a three-line record for a company name that includes `|` if anyone ever needs that.

Help under Multi-item capture documents: first item = template, later items = rows, `{N}` holes, `{{` `}}` escapes, the three row rules, and that `@route:{id}` is Next+link for every row.

### What to implement (bob-cli first)

1. **`maybe_expand_template` in `capture_language`.** After `split_capture_draft`, detect slots in item 0 with a small scanner (contiguous `{N}`, `{{` / `}}`). If no later items, return the draft unchanged for execution; on the editor path only, if a marker contains `{N}`, emit slot spans + `template_row` need (**ADJ-5**). If later items exist, parse each as a record (**ADJ-2/3/4**), substitute into item 0's raw slice, rebuild `CaptureItem`s from the expanded sources, then parse as today.

2. **Teaching errors** (exit 2 usage, same voice as other capture grammar errors):

   - `capture item 1 is a template with holes {0}, {1}, {2}; add a row after a blank line, or write {{0}} for a literal brace`
   - `capture item 3 starting on line 7: expected 3 fields ({0}, {1}, {2}), got 2`
   - `capture item 3 starting on line 7: field {1} is used as a block ID and must be A-Z, a-z, 0-9 or '-' (got "Bank of America")`
   - `template hole {2} is missing; holes must be {{0}}…{{K-1}} with no gaps`
   - `clipboard % cannot be used in a capture template`

3. **`capture-parse`:** additive `template` object; `items[0].mode = "template"`; later `mode = "template_row"`; spans for slots. Schema version stays 1.

4. **`docs/capture.md` Multi-item capture** plus the grammar-at-a-glance table. `bob capture --help` long_about gets a short example (cli_rules: excellent help). No new subcommand, no `--template` flag.

5. **Tests** in `src/native/capture_language/tests/` and `tests/cli/capture/`:

   - The request's before/after, byte-identical to two ordinary captures (including the URL child).
   - Surplus tokens join `{0}`.
   - `|` split and three-line records.
   - `{{0}}` literal in a two-item draft that is *not* a template.
   - Single-item `Read RFC {0}` stays a task.
   - `@route:{0}` with no rows: parse incomplete, capture usage error.
   - URL-only row under a one-slot `{0}` template is a field, not a ref.
   - Duplicate expanded block IDs roll the batch back.
   - `&note:id` on the template copies onto every expanded item.
   - `%` in the template refused.
   - `plan.strict` still refuses an oversized Next batch.
   - `capture-parse` spans for `{0}` land on character boundaries in the original text.

6. **Mac (follow-on):** map `template_slot`, quiet `template_row`, decoding test for the additive object. No Swift substitution.

### What not to do

- Do not add `bob capture template` or `bob capture --template`.
- Do not reimplement expansion in Swift.
- Do not expand inside `capture-rewrite`.
- Do not allow format specs or named `{company}` in v1.
- Do not mix independent non-row items into a template draft.
- Do not weaken block-ID or route alphabets so `{1}` is a legal ID.
- Do not fetch URLs or call `bob ref create` because a field looks like a URL; after expansion, a URL in a child bullet is prose, same as today.

### Implementation order

Bob-cli grammar + CLI tests + `docs/capture.md` first. Mac palette / quiet incomplete second, behind an additive decode, so an older app still submits the compact draft and shows expanded preview cards from dry-run.

That is the whole feature: a mail-merge pass in `capture_language`, then the capture engine Bob already has.

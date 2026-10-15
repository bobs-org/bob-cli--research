# Bulk Capture Templates for `bob capture` and Bob Mac Capture

*Researcher: cld · 2026-10-15 · Sources: bob-cli at `47e85f6` (`docs/capture.md`,
`src/native/capture_language/`, `src/native/capture/`), bob-mac-capture at
origin/master, sase `docs/macros.md` (for Bryan's existing placeholder conventions),
and a read-only look at the Bob vault (`job_2026_apply_29.md`, `ref/chat/*wave*`).*

## TL;DR

- **Build it, and put all of it in bob-cli.** Make the template a **textual
  expansion that runs before parsing**, inside `capture_language`. Make the request's
  own sentence ("that should be equivalent to the following") the formal rule:
  *capturing a template draft is exactly the same as capturing its expanded draft*. The
  only differences are error locations and some added template metadata. That rule
  becomes the spec and the test oracle. Because of it, these need **no** change:
  - the planner and the atomic commit
  - the duplicate-block-ID checks
  - the plan budget
  - the Mac app's preview cards
- **The hard part is the editor protocol, not `bob capture`.**
  - The problem: `capture-parse` and `capture-complete` work against what the user
    typed, but the expanded text never exists in the editor. The Mac app only paints
    highlighting when *every* span is a sorted, non-overlapping UTF-8 byte range into
    the typed draft. One bad span and it drops them all.
  - The fix has four parts:
    - parse the template with each `{N}` swapped for filler of the same length;
    - add field spans on the data rows;
    - keep a source map so diagnostics point back at typed text;
    - suppress completion inside rows and placeholders.
- **Syntax: keep Bryan's shape (template first, data after), with these adjustments:**
  - 1-based `{1}…{n}`, which matches Bryan's own sase `{1}` legacy placeholders.
  - `{0}` means the whole row.
  - One row per nonblank line. Blank lines between rows are optional, so Bryan's
    example still works.
  - Fields are separated by whitespace, `"…"` quotes group a multi-word field, and the
    field count is strict.
  - A blank line is required between the template and its rows.
  - Placeholders are allowed only in the first item.
  - `\{` escapes a placeholder, and text inside inline code stays literal.
- **Bob Mac Capture needs no required changes** if bob keeps that contract. The
  optional polish is two span colors and a "Template · N rows" chip.

The recommended spelling of Bryan's example (the third row shows why quoting matters
on real data):

```text
Apply to {1}! @job_2026_apply_29:{2}
- **URL**: {3}

Foobar foo http://foobar.com/career/some_foo_job
Bazbuz baz http://bazbuz.com/career/some_baz_job
"Two Sigma" two-sigma https://www.twosigma.com/careers/some_role
```

It expands to, and must behave exactly like:

```text
Apply to Foobar! @job_2026_apply_29:foo
- **URL**: http://foobar.com/career/some_foo_job

Apply to Bazbuz! @job_2026_apply_29:baz
- **URL**: http://bazbuz.com/career/some_baz_job

Apply to Two Sigma! @job_2026_apply_29:two-sigma
- **URL**: https://www.twosigma.com/careers/some_role
```

---

## 1. Motivation and evidence

What the vault shows (read-only look):

- **The motivating project.** `job_2026_apply_29.md` is the project "Apply to 29 job
  openings!" (`task_count: 16`).
  - 13 of its tasks are `Apply to <Company>!` tasks created on 2026-10-14 and
    2026-10-15.
  - They carry `^apply-<slug>` block IDs (`^apply-de-shaw`, `^apply-two-sigma`), and
    some have a bare-URL child bullet.
  - Its only open task right now is *"Collect the 7 roles I need to apply for as
    tasks!"*, which is exactly the job this feature does.
- **The next batch is coming.** `ref/chat/third_wave_job_applications.md` was created
  this morning with the title "Wave 3: Twelve More Roles to Apply For". That means
  another batch of about 12 identical-shape tasks.
- **Real field values have spaces.** Company names include **DE Shaw** and **Two
  Sigma**, so whitespace-only field splitting fails on the data this feature exists
  for.
- **Block IDs are slugs of the name** (`apply-two-sigma`). That points to a future
  `slug` filter (§12).
- **Literal braces are rare in task text.**
  - 0 of 3,724 `#task` lines in the vault contain `{<digits>}` or `{<identifier>}`.
  - 19 contain any brace at all, and every one sits inside backticked sase syntax
    (`` `%{A | B}` ``, `` `{@<N>}` ``).
  - So recognizing `{N}` without an explicit marker has no history of collisions.
    Treating inline code as literal covers the one real habit of writing literal
    braces.

**Value estimate.** Each row saves about 35 typed characters (`Apply to `,
`! @job_2026_apply_29:`, newline plus `- **URL**: `). For 12 rows that is about 400
characters and 12 chances to mistype the route. That is a moderate keystroke win. The
bigger wins are:

- the shared parts are typed once, so the batch stays consistent;
- there is one atomic preview, and one commit that is all-or-nothing.

---

## 2. Facts about today's pipeline that shape the design

### bob-cli

1. **Batches are atomic.** Blank lines split a draft into items. The whole batch is
   planned in memory and then committed all-or-nothing. Later items see earlier items'
   staged edits, and duplicate block IDs are checked across the batch (`docs/capture.md`
   § Multi-item capture).
2. **There is already a draft-level step before items are split.**
   `split_capture_draft` (`src/native/capture_language/draft.rs:67`) removes `@@`
   declaration-only lines first. A template layer would be the second such step.
3. **Everything points back at the typed draft.** Item ranges and line numbers always
   refer to the original draft, and `CaptureItem<'a>` borrows `&'a str` slices of it.
   An expansion therefore needs its own text buffer plus a **source map** back to typed
   text.
4. **`split_capture_draft` already special-cases some splits:**
   - URL-list blocks (`draft.rs:249`)
   - same-line session chains
   - inline Work Log closes

   The template layer has to run *before* these, so that data rows are never split as
   items.
5. **A second `@@` is a hard error.** Inline `@@` tokens are collected per item, and a
   second one fails as "duplicate global destination" (`draft.rs:752`). Copying a
   template that contains an inline `@@` would therefore collide with itself.
6. **Quoting and escaping already have house rules.**
   - Quoted note names: `&"Shopping List":bar`; inside quotes only `\"` and `\\` are
     escapes.
   - `\*` and `\&` escape a sigil *only where it would otherwise be a directive*.
   - `[[wikilinks]]` and `` `code` `` are protected ranges where `&` stays literal
     (`dependencies.rs:103`).
   - The quote scanner (`scan_quoted_modifier` / `decode_quoted_note`,
     `dependencies.rs:174,376`) can be reused for row fields.
7. **bob already has single-brace placeholders.** `highlights.listen_command` uses
   `{target}`, `{pdf}`, `{audio}`, and `{title}`, and rejects unknown placeholders
   (`docs/highlights-create.md`). `{` and `}` have **no** meaning anywhere in the
   capture grammar.
8. **The plan budget only warns about links.** The deployed link cap is 10: a batch
   that grows today's Task Links past the cap gets a warning. `plan.strict` refuses
   only growth in themes.
9. **CLI rules** (`cli_rules.md`):
   - never add a subcommand under `bob capture`;
   - `capture-*` protocol commands grow only additively;
   - every public option gets a short alias.

### Bob Mac Capture (verified in `sase/repos/linked/bob-mac-capture`)

1. **It is a thin client.** Decision `mac-capture-is-a-thin-client`: bob is the only
   implementation of the grammar, and the app never parses. Template expansion in Swift
   is therefore off the table.
2. **The draft goes over as one argv value after `--`.** That applies to
   `capture-parse`, `capture-complete --cursor <utf8>`, `capture-rewrite`,
   `capture --dry-run`, and submit (`Sources/CaptureCore/BobProcessClient.swift`).
3. **Span painting is all-or-nothing.**
   - `validatedSpanRanges` (`Sources/CaptureCore/CaptureTextRanges.swift:113-132`)
     returns `nil` if *any* span is out of order, overlaps another, or falls outside
     the typed text.
   - Then `applyHighlighting` shows "Ignored malformed parse spans" and leaves stale
     colors on screen (`Sources/BobMacCapture/CapturePanelModel.swift:6868-6871`).
4. **Some `items[]` fields are required.** `index`, `range{start,end}`, `line_start`,
   `line_end`, `body`, and `mode` are decoded strictly
   (`Sources/CaptureCore/CaptureModels.swift:304-309`). If one is missing, decoding the
   whole parse fails.
5. **Unknown values are tolerated.** Unknown span kinds render as neutral, and unknown
   `mode` and `needs` values are ignored. However, `schema_version` must equal `1` for
   parse, complete, and rewrite.
6. **`interactive_placeholder` is already in use.** It sits in the completion-trigger
   list (`CapturePanelModel.swift:6971`) and drives the close-pending trim. Template
   placeholders **must not reuse that span kind**.
7. **Preview cards need nothing.** They come from `capture --dry-run`'s `captures[]`.
   They render bob's text as-is under an "N captures" header and never map back to
   draft ranges, so expanded instances show up with no app change.
8. **Diagnostics and warnings are shown sparingly.**
   - Only the first diagnostic that is not `info` appears, in the status line, and its
     range is ignored.
   - Top-level `warnings` on ordinary task captures are **not shown anywhere**.
   - So v1 should report template problems as diagnostics or errors, not warnings.
9. **There is already a way to recall a draft.** The canceled-draft stash keeps 10
   persisted entries and restores into an empty editor. That is a free way to reuse
   last week's template draft.

---

## 3. Critique of the proposal

### 3.1 Is it a good idea?

**Yes, with caveats.**

Reasons for:

- **It is a real, recurring workflow.** This is the 29th application project, and 12
  more roles arrived today.
- **It fits the batch model with no new execution concepts.** N rows become N items,
  with one dry-run preview and one atomic commit.
- **It can be a thin layer.** The existing grammar, 5,879 lines of docs and about 390
  table rows, stays untouched.
- **It generalizes cleanly beyond job applications:**
  - `{0} @groceries` with one item per line. Today the same list needs a blank line
    between every item.
  - Bulk-link existing tasks: `^job:{1}`.
  - Bulk-complete: `!job:{1}`.
  - Bulk dependency edges: `Read {1} &job:cleanup`.

Reasons for caution:

- **Grammar size is the main long-term cost.** Every layer adds something to teach.
  Textual expansion keeps the new surface to roughly one rule plus its row syntax.
- **When rows come from an LLM report** (as the wave-2 and wave-3 lists did), asking
  the agent for a ready-to-paste capture draft works just as well. Templates pay off
  when **Bryan** types or pastes column data himself.
- **Most of the cost is in the editor protocol**, not in execution (§7.4). Budget
  for it.
- **The example's `:` marker may not be what Bryan wants.** It makes every row a
  **Next task with a Pomodoro Task Link**.
  - Seven to 12 links at once overshoots the link cap of 10, which only warns.
  - It also floods the Next lane.
  - The existing apply tasks are plain `^apply-<slug>` tasks.
  - Unless he wants every role in today's sessions, `@job_2026_apply_29^apply-{2}`
    is probably the intended template. This is flagged for his call, not changed.

### 3.2 Problems in the proposed syntax as written

1. **Whitespace-only fields cannot hold multi-word values.** Two Sigma and DE Shaw
   would break. Rows need quoting or another delimiter.
2. **0-based `{0}` contradicts Bryan's own convention.**
   - sase legacy macro placeholders are `{1}`, `{2:default}`, 1-indexed
     (`sase docs/macros.md` § Legacy Placeholders).
   - sase Jinja arguments are `{{ _1 }}`, also 1-indexed.
   - Two personal tools with opposite base indexes is a standing footgun.
   - awk, sed, and regex also put the whole record at `$0` / `\0` and the first field
     at `$1` / `\1`.
3. **Rows separated by blank lines are verbose.** Rows are single-line data with no
   children, so each nonblank line can be a row. Pasting a column of 12 values then
   needs no editing.
4. **Detection is unspecified.** The proposal doesn't say what `{N}` means in a
   one-item draft, in a later item, or inside inline code, or how to write a literal
   `{1}`.
5. **Interactions are unspecified:**
   - An inline `@@` in the template would be copied N times and collide (§2 bob-cli
     fact 5).
   - `%` clipboard markers would read the clipboard once per instance.
   - Rows with the wrong number of fields have no defined behavior.
   - Duplicate slugs are already caught by the batch planner, and independent `p:<N>`
     rolls per row are fine; both should be documented.
6. **"Equivalent to the following" is the right instinct.** Make it the normative rule
   (§5).

---

## 4. Syntax design space

### 4.1 Where the template lives and how rows are marked

| # | Shape | Example | For | Against | Verdict |
|---|---|---|---|---|---|
| S1 | **As proposed:** `{0}` in the first item; each later blank-line item is a row; fields split on whitespace | the request's example | Simplest to describe | Breaks on multi-word names; 0-based; needs blank lines between rows; detection undefined | Adjust → S2 |
| S2 | **Recommended:** the first item holds `{N}` (1-based, `{0}` = whole row); after a blank line, every nonblank line is a row; whitespace fields with `"…"` quotes; strict field count | see TL;DR | No extra syntax; reads like a header plus a table; paste-friendly; bob-native quoting; also accepts Bryan's blank-line form | Detection is implicit (needs §6 R3/R11 escape rules) | **Adopt** |
| S3 | Explicit sigil line before the template (e.g. `@@tpl`, `>>>`) | `>>>` then the template | Never misfires | More syntax, and the placeholders already announce the template; `@@` is reserved for destinations | Reject |
| S4 | `---` separator between template and rows | template, `---`, rows | Visually clear; sase uses `---` for segments | A fourth meaning for `-`-runs (bullets, `-N`, `--N`); the blank line already separates | Reject (keep `---` free for future multi-template segments) |
| S5 | Inline alternation, sase-style | `Apply to {Foobar\|Bazbuz}! @job:{foo\|baz}` | Compact for 1 field × 2–3 values | Columns scattered across the template; adding a row edits N places; needs zip semantics; sase's `%{` collides with bob's `%` clipboard marker | Reject |
| S6 | Named placeholders `{company}` | `Apply to {company}!` | Self-documenting | Binding order is implicit (first appearance) or needs a header row; reordering template text silently reorders columns | Defer: reserve `{identifier}` inside templates |
| S7 | Markdown pipe-table rows | `\| Two Sigma \| two-sigma \| https://… \|` | Obsidian- and LLM-native; multi-word fields without quotes; can paste a whole table | More typing for simple rows; needs header/separator skipping | Good **v1.1** follow-up (§12) |
| S8 | Out-of-band rows: `bob capture --rows FILE.tsv` | — | Scriptable | CLI-only, no panel, no preview | Reject for now |

### 4.2 Placeholder spelling

| Spelling | Verdict |
|---|---|
| `{1}` | **Adopt.** `{` has no meaning in capture grammar today. It matches sase legacy `{1}` and bob's `{target}` config placeholders. zsh leaves an unquoted `{1}` literal (checked on this host; only the non-default `BRACE_CCL` option would expand it), and bash leaves it literal too. |
| `{0}` as first field | Reject (§3.2 #2). Repurpose `{0}` as the whole row, as in awk. |
| `$1` | Reject. `$` shows up in task text (prices), and zsh expands `$1` inside double quotes when called from the shell. |
| `{{1}}` | Reject. Twice the typing, and it looks like Obsidian core templates and Jinja, which run at a different time. |
| `<1>` | Reject. It clashes with Markdown autolinks `<https://…>` and sase raw `<label>` placeholders. |

### 4.3 Row field delimiter

| Delimiter | Verdict |
|---|---|
| Whitespace plus `"…"` grouping (only `\"` and `\\` escape inside quotes) | **Adopt for v1.** Single-word fields (slugs, URLs) stay effortless, and this is bob's existing quoting rule. |
| Pipe `\|` | v1.1, as Markdown table rows (S7). |
| Tab (TSV pasted from a spreadsheet) | Follow-up only if a spreadsheet workflow shows up. |
| Comma | Reject. Company names and prose contain commas. |
| "Last placeholder absorbs the rest" (shell `read`) | Reject as the default. A forgotten quote silently shifts every field, e.g. `Two Sigma two-sigma …` turns into the task "Apply to Two!" with ID `Sigma`. A strict count turns that into a teaching error. |

---

## 5. Semantics: textual expansion, not structural substitution

**Textual (recommended).** For each row, substitute the row's field values into the
template's *raw text*. Join the instances with blank lines and hoist the template's
inline `@@` once (§6 R9). Then run the **unchanged** parser and planner.

- Every marker works in a template for free: `@route`, `^id`, `:id`, `+id`, `&`,
  `*`, `!`, `s:`, `p:`, URLs, and authored children.
- The rule is **Template invariant:** *for a template draft `D`,
  `bob capture D` ≡ `bob capture expand(D)`.* The only differences are that error
  locations name the template row and that the JSON gains additive `template`
  metadata.
  - This turns Bryan's "should be equivalent" into a contract.
  - It gives a property-test oracle: dry-run plans of `D` and `expand(D)` must be
    identical.
- **What it means for users.** Field values are pasted in verbatim. A field that
  *looks like* a marker *acts like* one: a value `@home` in a prose position becomes a
  route. That is the honest macro behavior; the live preview shows it, and the docs
  must say it. A later version could warn when a substituted value creates a marker
  token that the template's filler reading did not have. Not v1.

**Structural (rejected).** Parse the template once with typed "holes", then fill
them. The problem is that `@job_2026_apply_29:{2}` is not a valid token until it is
filled. The grammar would need hole-awareness in every token class (routes, block
IDs, Pomodoro names, quoted dependency notes, close lists, and so on), which is a
second grammar. It would also break the one-grammar principle that the thin-client
decision rests on.

---

## 6. Recommended specification (v1)

- **R1. Detection.** A draft is a *template draft* when its first item contains at
  least one placeholder.
  - A placeholder is `{` + ASCII digits + `}` (`{0}`, `{1}`, `{12}`).
  - It must be outside an inline code span and not escaped.
  - Detection runs after `@@` declaration-only lines are removed.
- **R2. The template** is the first blank-line-separated item: a parent line plus
  optional authored child bullets, under today's rules.
- **R3. Placeholders appear only in the template.** `{N}` outside code in any later
  item, or in a draft whose first item has none, is an error: *"`{2}` is a template
  placeholder; only the draft's first item can be a template — write `\{2}` to keep
  it literal"*.
  - A one-item draft with placeholders is a template with no rows (R12).
  - Historical cost is zero (§1).
- **R4. Separation.** A blank line must separate the template from its rows.
  - A non-bullet line directly under the template is today's invalid-continuation
    error, upgraded to teach: *"add a blank line between the template and its rows"*.
- **R5. Rows.** After the template, **every nonblank physical line is one row**, in
  order.
  - Blank lines between rows are optional and ignored, so Bryan's blank-line form
    still works.
  - A line shaped like a bullet (`- …`, `  - …`) in the row section is reserved for
    v2 per-row children and is an error for now.
  - `@@` declaration-only lines are still removed wherever they appear.
- **R6. Fields.** A row is split on runs of whitespace.
  - A field that *starts* with `"` runs to the matching unescaped `"`. Inside it,
    only `\"` and `\\` are escapes, the same rule as `&"Shopping List":bar`.
  - `5"` in the middle of a token stays literal.
  - `""` is an empty field.
  - An unterminated quote is an error on that row.
- **R7. Field count is strict.** Every row must have exactly *n* fields, where *n* is
  the largest `{N}` with N ≥ 1 in the template.
  - Placeholders the template skips are allowed. If the template uses `{1}` and
    `{3}`, rows still have 3 fields and field 2 is ignored, which lets you drop a
    pasted column.
  - Error: *"template row 3 (line 6) has 4 fields but the template uses {1}–{3};
    quote a field that contains spaces: "Two Sigma""*.
- **R8. `{0}` is the whole row** (trimmed, verbatim).
  - If the template uses only `{0}`, rows are not split at all: no field count and
    no quote handling. That gives multi-word one-per-line lists with no quoting:
    `Email {0} about references`, or `{0} @groceries` with rows `oat milk`,
    `green onions`.
  - If Bryan writes `{0} {1} {2}` out of 0-based habit, R7 catches it: *"…the
    template's highest field is {2}; fields are 1-based ({1} is the first field, {0}
    is the whole row)"*.
- **R9. `@@` is draft-wide, so it is hoisted.**
  - An inline `@@route` token in the template counts **once** as the draft
    declaration; it is not copied per row.
  - `@@` lines anywhere else keep today's meaning.
  - Every instance inherits the declaration under today's precedence rules.
- **R10. Expansion and atomicity.**
  - Substitution is a single pass: a value containing `{1}` is never re-expanded.
  - Instances are planned in row order as one batch, so all rows land or none do.
  - Instance *k* reports its row's line in errors: *"template row k (line L): …"*.
- **R11. Escapes.**
  - `\{` keeps a would-be placeholder literal, and only where it would otherwise be
    a placeholder (bob's `\*`/`\&` rule).
  - Text inside inline code spans is never a placeholder, matching sase's `%{` and
    `<label>` and bob's protected `&` ranges.
  - **Wikilinks are deliberately *not* protected**, because `[[{1}]]` is a useful
    template.
- **R12. Incomplete states.**
  - In `capture-parse`, a template with zero rows is mode `incomplete` with
    `needs: ["template_row"]`, plus one `error`-severity diagnostic, *"add one row
    per line below the template"*, so the Mac status line shows it.
  - `bob capture` refuses it with the same text.
- **R13. Reserved for later (errors in v1):**
  - `{name}` placeholders: once a draft is a template, `{identifier}` in the template
    is an error.
  - `{N:default}`, as in sase.
  - `{N|filter}`.

### Interaction table (all follow from R10's invariant unless noted)

| Template contains | Effect |
|---|---|
| `@route`, `@route^id`, `@route:id`, `@route+id` | Applied per instance; duplicate IDs across rows refused by the batch planner |
| `:id` (Pomodoro link) | One Task Link per row → plan-budget link warning when >cap; consider `^` |
| `p:<N>` | Each instance rolls its own schedule (the existing "each capture rolls independently" rule) |
| `s:<N>` | Same date for every instance |
| `&note:id` / `*note:id` | Each instance gets the edge; cycle checks unchanged |
| `!note:{1}` / `^route:{1}` | Bulk complete / bulk link of existing tasks — works unchanged |
| `%`, `%N`, `%header` (clipboard) | Every instance gets the clipboard children. **Recommend refusing in v1** ("clipboard markers can't be repeated by a template") — almost never intended |
| Session operators (`=`, `=x`, `+N`, `++N`) | **Recommend refusing** ("a template cannot expand to session operators") — running a session op N times is never intended |
| Bare URL / `URL %` | Each instance may become a ref job exactly as typed text would (`{1} @mac_inbox` rows of URLs = bulk ref queue) |
| inline `@@route` | Hoisted once (R9) |

---

## 7. bob-cli implementation plan

### 7.1 Module and pipeline position

- **New module.** Add `src/native/capture_language/template.rs` with:
  - `detect`: scan the first item's lines for unescaped `{digits}` outside code
    spans.
  - `parse_rows`: rows and fields with their byte ranges in the typed draft.
  - `expand`: produce `TemplateExpansion { text: String, map: SourceMap, rows }`.
- **Where it runs.** The step goes right after `@@` declaration-only lines are
  removed and right before item splitting. Each caller then hands
  `&expansion.text` to the **existing** `split_capture_draft` /
  `parse_capture_draft_with_clip_control` / `parse_for_editor_with` path.
- **Lifetimes.** `CaptureDraft<'a>` borrows its source, so the owner of
  `TemplateExpansion` must outlive the parse. Both entry points (`plan_capture_batch`
  in `src/native/capture/plan.rs:36` and `CaptureParseResult::new` in
  `src/native/capture_parse.rs`) already own the raw `String`, so they can own the
  expansion too.
- **Error prefixes.** Today `parse_capture_draft_with_clip_control`
  (`draft.rs:621`) builds the `capture item N starting on line L:` prefix itself, and
  the planner adds another (`plan.rs:107,135`). Add an optional location mapper so
  both print `template row k (line L):` instead of offsets into the expanded text.

### 7.2 Source map

The expanded text is a sequence of segments, each either `Template(typed_range)` or
`Field { row, field, typed_range }`, with instance boundaries recorded. The map has to
answer three queries:

- the expanded item range → its row's typed line range, used for `line_start` /
  `line_end` / `range` on `items[]` and for error prefixes;
- an expanded diagnostic range → a typed range: the field's own range if the
  diagnostic overlaps a field segment, otherwise the row's range;
- an expanded byte → its segment, used by completion guards and tests.

### 7.3 `bob capture` (execution)

- Planner, commit, ref jobs, plan budget: **unchanged**.
- JSON: add a top-level `template` object (`line_start`, `line_end`,
  `placeholders`, `rows` count). Each `captures[]` entry gets an additive
  `template_row` (`row`, `line`).
  - A one-row template keeps the single-item legacy shape plus `template`.
- Human output: a header such as `template  3 rows (lines 4–6)`, numbered `1/N`
  lines as today, and errors prefixed `template row k (line L):`.
- **Optional convenience flag:** `bob capture -E, --expand`. It prints the expanded
  draft and exits without planning or writing. It is handy for debugging and for
  turning a template into a plain draft. It must follow the cli rules (short alias,
  alphabetical, help text). It is not required, because `--dry-run` already shows
  the result.

### 7.4 `bob capture-parse` (editor protocol): the real work

All output must be in **typed-draft coordinates**, sorted and non-overlapping, so the
Mac app's all-or-nothing validator accepts it.

1. **Template spans use a same-length mask.**
   - Make a copy of the typed draft in which each `{N}` becomes the same number of
     `x` bytes (`{2}` → `xxx`). `{N}` is ASCII, so byte offsets are preserved
     exactly.
   - `x` is valid in every token class: route, block ID, Pomodoro and section
     selector, prose.
   - Run today's editor parse on the template item of that copy. Its spans and
     needs already index the typed draft.
2. **Overlay placeholder spans.** Add a new `template_placeholder` span over each
   `{N}`, splitting any span it falls inside. For `^apply-{2}`, the block-ID span
   becomes `apply-` followed by `{2}`. Never emit `interactive_placeholder` (§2 Mac
   fact 6).
3. **Row spans.** Emit one new `template_field` span per field, with quotes included.
   An additive per-span `field` index lets a client alternate colors; Swift's
   `Codable` ignores the extra key.
4. **Per-row instance parse.**
   - Parse each expanded instance with the normal editor parser.
   - Map its diagnostics back through §7.2. For example, *"`Two_Sigma` is not a
     valid block ID"* lands on row 3, field 2.
   - Drop the instance's spans, because the template's masked spans already
     describe the template.
   - Drop masked-template diagnostics that intersect a placeholder. The per-row
     parses own those.
5. **Shape of `items[]`.**
   - Item 1 is the template, with the masked mode, route, needs, and so on. Its
     typed range and lines are real, so pickers opened from the template insert
     correctly.
   - Each row is item k+1, with mode `template_row`, its typed row range and line,
     `body` set to the instance's body, and **no `needs`**.
   - Unknown modes are ignored by the app, so no picker opens on a data row.
   - Item ranges stay disjoint.
6. **New top-level `template` object.**
   - `range`, `line_start`, `line_end`, `placeholders`, `arity`, `uses_row`.
   - `rows[]` entries carry `row`, `line`, `range`, `fields[]`
     (`start`/`end`/`value`), `expansion` (the instance text), and `mode` (the
     instance's real reading, e.g. `pomodoro_task`).
   - Legacy top-level fields keep describing the first item (the template), which is
     today's rule.
7. **`schema_version` stays 1.** Every change is additive; a bump would break the
   app (§2 Mac fact 5).
8. **New diagnostic codes:**
   - `template_missing_rows`
   - `template_row_arity`
   - `template_unterminated_quote`
   - `template_row_bullet` (reserved)
   - `template_placeholder_outside_template`
   - `template_needs_separator`
   - `template_session_operator` and `template_clipboard` (if R-table refusals
     adopted)
   - `template_reserved_placeholder`

### 7.5 `capture-complete` and `capture-rewrite` guards

- **`capture-complete`:**
  - A cursor inside the row section, or inside a `{N}`, returns an empty success.
  - A cursor elsewhere in the template completes against the masked copy.
  - Drop any candidate whose `replacement` range intersects a placeholder. Otherwise
    accepting a block-ID candidate at `@job:{2}` would overwrite the `{2}`.
  - The engine already routes through `editor_item_at` / `split_capture_draft`
    (`src/native/capture_complete/engine.rs:43,181`), so this is one gate.
- **`capture-rewrite`** (it splits the draft at `rewrite.rs:89`):
  - apply only to the template item;
  - skip any edit that overlaps a placeholder;
  - never rewrite rows.

### 7.6 Docs and help

- **`docs/capture.md`:**
  - a new § *Bulk templates* after § Multi-item capture;
  - rows in Grammar at a glance (`{N}`, `{0}`, `\{`, row and field rules);
  - the capture-parse contract additions (span kinds, `template` object,
    `template_row` mode, diagnostic codes);
  - the capture JSON additions.
- **`bob capture --help`:** a one-line mention of the template.
- **Naming:** call it a **"bulk template"** in docs and help, so it isn't confused
  with Obsidian core and Templater templates or the `template:` frontmatter key
  used by project notes.
- **Decision record:** after acceptance, a decision record (`decisions` web) such as
  *"Bulk templates expand textually before parsing"*. It should list the rejected
  alternatives from §4, §5, and §10. Write it through `/sase_memory_write`.

### 7.7 Tests

- **Equivalence oracle (the core property).** For every golden template draft,
  `plan_capture_batch(D)` and `plan_capture_batch(expand(D))` yield identical item
  results. Cover each marker family in the interaction table.
- **Span invariants for `capture-parse`.** Spans sit on UTF-8 char boundaries of the
  typed input, sorted, non-overlapping, and inside the input. Cover multi-byte field
  values (`Zürich`) and placeholders inside larger spans (`^apply-{2}`).
- **Teaching-error goldens** for R3, R4, R5, R6, R7, R8, and R12, in both human and
  JSON output.
- **Completion goldens:** a cursor in a row returns empty; a block-ID candidate at
  `:{2}` is suppressed; route completion inside the template still works.
- **Batch atomicity:** a bad block ID on row 5 refuses rows 1–4.

**Size estimate.** About 500–700 lines of Rust plus 800–1,000 lines of tests and
goldens, plus about 150 lines of docs. That is three phases: execution plus docs,
editor protocol, then Mac polish.

---

## 8. Bob Mac Capture impact

**Required changes: none**, provided bob keeps the §7.4 contract. Checked against the
code:

- Spans are in typed coordinates, sorted, and non-overlapping, so
  `validatedSpanRanges` accepts them.
- The new span kinds render as neutral until the app adds colors.
- Every `items[]` entry has a real `range`, `line_start`, and `line_end`, so the
  strict decode at `CaptureModels.swift:304-309` passes.
- `template_row` mode and `template_row` needs are ignored by `pickerNeed`.
- Preview cards render `captures[]` text verbatim with the "N captures" header, and
  submit is still one aggregate `bob capture`.

**Recommended polish** (a small Mac phase, gated by macOS CI per its `AGENTS.md`):

1. Colors for `template_placeholder` and `template_field`. Alternate the shading of
   fields using the additive `field` index so the user can *see* how a row split.
   That is the main defense against quoting mistakes.
2. A "Template · N rows" header in the preview, read from the `template` object.
3. Optionally, show the parse diagnostic's range inline. Today the range is ignored
   and only status-line text appears. For row errors, highlighting the offending
   field is much clearer.
4. Do **not** add template logic or Swift-side expansion. The thin-client decision
   forbids it.

The canceled-draft stash already lets Bryan reuse last week's template text. A Mac
snippet entry (the app has a `CaptureSnippetCatalog`) that inserts a template skeleton
would also be pure presentation, not grammar. That is the right home for "saved
templates" if they're ever wanted (§12).

---

## 9. Requirement adjustments

| # | Bryan's requirement | Adjusted to | Why |
|---|---|---|---|
| A1 | `{0}` is the first field | **`{1}` is the first field; `{0}` is the whole row** | Matches Bryan's sase `{1}` placeholders and the awk/sed `$0`/`$1` convention. `{0}` gives multi-word one-per-line lists with no quoting. A 0-based draft triggers a teaching error, so it never fails silently. |
| A2 | Each later *blank-line-separated item* is a row | **Each later nonblank *line* is a row; blank lines between rows are optional** | Paste a column without editing it. Bryan's blank-line form still works unchanged. |
| A3 | Fields are whitespace-separated | **Whitespace-separated, with `"…"` grouping, and a strict field count** | Real data (Two Sigma, DE Shaw) needs multi-word fields. A strict count turns a forgotten quote into a teaching error instead of silently shifted fields. |
| A4 | (unspecified) | **Placeholders only in the first item; `\{` escapes; inline code is literal** | Makes implicit detection safe and predictable. |
| A5 | (unspecified) | **A blank line is required between template and rows** | Keeps the template boundary unambiguous; one teaching error covers it. |
| A6 | "should be equivalent" | **Made normative: capture(D) ≡ capture(expand(D)), atomically** | It is the spec, the docs sentence, and the test oracle all at once. |
| A7 | (unspecified) | **Inline `@@` in the template is hoisted once; `%` clipboard and session operators are refused in templates** | Prevents self-colliding declarations and almost-never-intended repetition. |
| A8 | Rows are "templates for" the first input | Terminology: the **template** and its **rows** (instances) | Clearer docs; avoids clashing with Obsidian template terminology. |
| A9 | Example uses `@job_2026_apply_29:{1}` | **Flag only:** consider `^apply-{2}` | `:` creates N Pomodoro Task Links and N Next tasks at once. The existing apply tasks use `^apply-<slug>`. |

---

## 10. Alternatives considered and rejected

1. **A shell function** that expands rows and calls `bob capture` once. It is atomic
   if it makes a single call, and it is about 10 lines of zsh. Rejected as *the*
   solution because the panel is the primary capture surface and gets no preview or
   highlighting from it. Still a fine stopgap for this week's 12 roles.
2. **Expanding in the Mac app.** Violates `mac-capture-is-a-thin-client`, creates a
   second grammar, and leaves the CLI behind.
3. **Inline alternation (S5).** Fine for one slot with two values, poor for
   multi-field tables. A second fan-out syntax is grammar bloat, and `%{` collides
   with bob's `%` clipboard marker.
4. **Structural holes (§5).** A second grammar.
5. **Named or saved templates in config** (`capture.templates.job_apply`). Premature:
   the route changes per batch (`job_2026_apply_29` → `_30`), so saved templates
   would need parameters too. Revisit after v1 usage. The stash and snippets cover
   recall for now.
6. **Detecting the template only when the draft has ≥2 items** (so a single-item
   `{1}` stays literal). Rejected because the live preview would flip meaning
   mid-typing when the first row is added. The vault shows zero literal `{N}` tasks
   to protect.
7. **A "last field absorbs the rest" rule.** Rejected as the default because it
   silently mis-splits a forgotten quote (§4.3).

---

## 11. Risks and open questions

- **Mask artifacts.** A placeholder in a position where `x…` reads differently from
  real values. Example: `p:{1}` masks to `p:xxx`, which is prose, while real
  instances read `p:2` as a priority. Effect: the template highlights it as prose,
  but the instances are correct, and the per-row parse reports any real problem.
  This is acceptable and should be documented.
- **Injection by field values** (§5). Document it and let the preview show it.
  Consider a later warning for fields that create a marker the masked template
  lacked.
- **Big batches and the plan budget.** `:` templates can blow the link cap. The
  `plan_budget.warnings` are separate from the hidden top-level `warnings` (§2 Mac
  fact 8). The Mac budget meter shows them as a `Links N/cap` capsule with warning
  text (`Sources/CaptureCore/CapturePlanBudgetPresentation.swift:55-59`), and the CLI
  prints a stderr warning. So a 12-row `:` template is visibly over budget before
  submit. That is fine, but it is one more reason to prefer `^` for backlog batches.
- **Per-keystroke parse cost.** It grows linearly with rows (one instance parse per
  row). Negligible at realistic sizes of 5–30 rows.
- **Open question for Bryan:** refuse or allow `%` clipboard markers and session
  operators in templates (recommendation: refuse in v1, since that is reversible
  additively).
- **Open question:** should row-section `@@` declaration lines be allowed between
  rows? They are today, by the general rule. Keep it.

---

## 12. Follow-ups (explicitly not v1)

1. **`{N|slug}` filter.** It would derive `two-sigma` from `"Two Sigma"` (and
   `apply-{1|slug}`), which removes the slug column from Bryan's real data.
   - Reuse `selector_slug` (`line.rs`) and strip characters that are not allowed in
     block IDs.
   - This is the highest-value follow-up given the vault evidence.
2. **Markdown pipe-table rows (S7).** A row starting with `|` splits on unescaped
   `|`; a `|---|` separator row and the header row before it are skipped. This lets
   an LLM report's table be pasted as-is.
3. **Defaults** `{N:default}` (the sase spelling), which allow optional trailing
   fields.
4. **Per-row child bullets.** Bullet lines under a row are appended after that
   instance's template children (the syntax is reserved in v1 by R5).
5. **Saved templates** as Mac snippets or a vault note, once usage shows which
   templates recur.

---

## 13. Recommended solution

1. **Semantics.** A bulk template is a **textual expansion inside
   `capture_language`, before parsing**, with the normative rule
   `capture(D) ≡ capture(expand(D))`, all-or-nothing. The planner, commit, ref
   jobs, and plan budget do not change.
2. **Syntax (v1):**
   - **Template:** the first item, holding 1-based `{1}…{n}` placeholders; `{0}` is
     the whole row.
   - **Separator:** a blank line between the template and its rows.
   - **Rows:** one row per nonblank line, with optional blank lines between rows.
   - **Fields:** whitespace-separated, with `"…"` grouping (`\"`/`\\` escapes) and a
     strict field count; skipped placeholder numbers are allowed.
   - **Escapes and literals:** `\{` escapes, and inline code is literal.
   - **Scope:** placeholders only in the first item.
   - **`@@`:** inline `@@` in the template is hoisted once.
   - **Refused in templates:** `%` clipboard markers and session operators.
3. **bob-cli phases:**
   - **Phase 1:** expansion core, execution, JSON and human output, the teaching
     errors, docs and help, and equivalence-oracle tests.
   - **Phase 2:** `capture-parse` with the same-length mask, `template_placeholder`
     and `template_field` spans, `template_row` items, the `template` object, and
     mapped diagnostics. Plus `capture-complete` and `capture-rewrite` guards. All on
     `schema_version` 1, additive only.
4. **Bob Mac Capture (phase 3, optional polish):** span colors with alternating
   field shading, a "Template · N rows" preview header, and inline diagnostic ranges.
   No grammar in Swift.
5. **Afterwards:** record the decision, then consider `{N|slug}` and pipe-table
   rows first.
6. **For Bryan's current batch:** decide between `:` (12 Pomodoro links now) and
   `^apply-{2}` (12 plain tasks) for the wave-3 roles. With the slug filter,
   Bryan's template would become:

```text
Apply to {1}! @job_2026_apply_29^apply-{1|slug}
- **URL**: {2}

"Two Sigma" https://www.twosigma.com/careers/some_role
Optiver https://optiver.com/working-at-optiver/career-opportunities/some_role
```

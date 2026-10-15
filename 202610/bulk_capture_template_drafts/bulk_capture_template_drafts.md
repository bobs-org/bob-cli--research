# Bulk Capture Templates for `bob capture` and Bob Mac Capture

> **Research query:** What is the best way to add support to the `bob capture` command
> and the corresponding bob-mac-capture app for defining a template as the first input
> of a bulk capture, with the subsequent inputs filling its `{0}`-style placeholders,
> and what is the best syntax for it? Critique the plan in general (is it a good idea,
> would a different approach be better), clearly call out any justified requirement
> adjustments, and end with a recommended solution.

![Infographic: a bulk capture template draft headed by @@template: expands into one capture per row; small explicit syntax (header, zero-based placeholders with no gaps, exact field counts with straight or smart quotes, one-field rows); one engine where capture(D) equals capture(expand(D)); the main risks; and a three-phase rollout with the Mac app kept a thin client](bulk_capture_template_drafts_infographic.png)

## Bottom line

**Build it, keep it small, and put all of it in bob-cli.**

- **Semantics.** A bulk template is a pure *text expansion* that runs before the
  existing capture parser. The request's "should be equivalent to the following"
  becomes the formal rule:

  > capturing a template draft `D` is exactly capturing `expand(D)`.

  The only differences are error locations and some added metadata. All four reports
  agree on this design. Because of it, these parts need **no** change:
  - the batch planner and its all-or-nothing commit;
  - the duplicate block-ID checks;
  - the plan budget;
  - the Mac preview cards.
- **Activation.** I recommend an [explicit header line](#activation-by-an-explicit-header),
  `@@template:`, as the first line of the draft. The reports
  [split 2–2](#where-the-reports-disagreed-and-how-i-resolved-it) on whether a header is
  needed at all.
  - gem's spelling, `@@template`, is unusable: it is already a valid route, and the
    vault has a `template.md` that current bob appends to.
  - With the colon, current bob refuses the draft (exit 2) and writes nothing.
- **Placeholders and rows.** Keep Bryan's `{0}` [placeholders](#placeholders) and his
  row shape, but make the [fields](#rows-and-fields) robust:
  - every nonblank line after the template is one row, and blank lines between rows
    are optional;
  - fields are separated by whitespace, and a field with spaces is wrapped in quotes;
  - **smart quotes `“…”` must count as quotes too.** The Mac draft editor deliberately
    leaves macOS smart-quote substitution on, and no report noticed this
    ([Mac facts, item 7](#bob-mac-capture-facts));
  - every row must have exactly the template's number of fields;
  - a template with a single field takes the whole row, with no splitting.
- **Where the cost is.** The expensive part is the
  [editor protocol](#the-editor-protocol-is-the-real-work), not `bob capture`.
  - `capture-parse`, `capture-complete`, and `capture-rewrite` must report everything
    against the text the user typed, not the expanded text.
  - The Mac app throws away all highlighting if a single span is malformed.
  - It also opens a picker when *any* item in the parse asks for one.
  - So rows must be opaque data, and every range must point into the typed draft.
- **[Bob Mac Capture](#bob-mac-capture) needs no change in v1.** Its dry-run preview
  already shows one card per expanded capture. Colors for the new spans and a
  "Template · N rows" chip are optional polish.

Recommended spelling of the request's example:

```text
@@template:
Apply to {0}! @job_2026_apply_29:{1}
- **URL**: {2}

Foobar foo http://foobar.com/career/some_foo_job
Bazbuz baz http://bazbuz.com/career/some_baz_job
"Two Sigma" two-sigma https://www.twosigma.com/careers/some_role
```

This is equivalent to three ordinary items, starting with
`Apply to Foobar! @job_2026_apply_29:foo` and its `- **URL**: …` child. The request's
original layout, with a blank line between rows, also works once the header line is
added.

## Evidence

### Sources and method

*Lead researcher (final) · 2026-10-15*

This report merges four independent reports with my own research:

- **Reports merged:** `__cdx`, `__cld`, `__grk`, and `__gem`, all in this directory.
- **My own research:** source inspection, read-only probes of the installed `bob`
  (`capture-parse`, `capture --dry-run`, `capture-complete`, `capture-rewrite`), and a
  read-only look at the Bob vault.
- **Anchors:** bob-cli `e1049625`, bob-mac-capture `9f58448`.

Each claim is tagged with the reports that support it. `[lead]` marks a finding no
report made.

### The motivating workflow

The vault was inspected read-only.

- **The current batch.** `job_2026_apply_29.md` ("Apply to 29 job openings!") holds 13
  `Apply to <Company>!` tasks created 2026-10-14/15. `[cld; verified]`
  - Their IDs follow `^apply-<slug>`: `^apply-de-shaw`, `^apply-two-sigma`,
    `^apply-tower-tailscale`.
  - One task has a bare URL child bullet.
  - The note's only open task is *"Collect the 7 roles I need to apply for as
    tasks!"*, which is exactly the job this feature does.
- **The next batch.** `ref/chat/third_wave_job_applications.md` ("Wave 3: Twelve More
  Roles") was created this morning. `[lead]`
  - Its PDF source lists roles as prose list items, not a table. Examples: "GitLab,
    Senior Backend Engineer, …", "D. E. Shaw, Software Developer, …",
    "Susquehanna SIG".
  - So Bryan will assemble rows by hand, and multi-word company names are normal, not
    an edge case.
- **How Bryan used `:` so far.** All 13 apply tasks were Task-Linked into `— JOB`
  Pomodoros, but only one or two per Pomodoro, as he worked them. For example, the
  0725–0735 session links `^apply-two-sigma` and `^apply-datadog`. `[lead]`
  - This corrects cld's guess that a plain `^` task was "probably intended."
  - The `:` versus `^` choice is in
    [the critique, item 5](#critique-of-the-proposal-as-written).
- **Literal braces are absent.** 0 of 3,678 `#task` lines contain `{<digits>}`.
  `[cld; re-verified]`
  - The only `{digits}` text anywhere in the vault is a sase plan note.
  - That note describes sase's own legacy placeholders, `{1}` and `{2}`, which are
    1-based.
- **Smart quotes are real in Bryan's tasks.** 57 task lines contain `“`, against 270
  with an ASCII `"`. `[lead]`

### bob-cli facts that shape the design

1. **Batches are atomic.**
   - Blank or whitespace-only lines split a draft into items.
   - One planner stages every item against in-memory snapshots, then commits all or
     nothing.
   - Later items see earlier items' edits, and duplicate IDs are checked across the
     whole batch.
   - Sources: `docs/capture.md` § Multi-item capture; `src/native/capture/plan.rs`.
     `[all]`
2. **Some splitting already happens before items are parsed.** `split_capture_draft`
   (`src/native/capture_language/draft.rs:67`) does three things first: `[cdx, cld]`
   - it strips declaration-only lines (lines where every token starts with `@@`);
   - it splits a blank-line-free list of bare URLs into one item per URL;
   - it splits a line of chained session operators into one item per operator.

   Template framing must run *before* this step. Otherwise a row could be read as a
   declaration, a URL list, or an operator chain.
3. **Items borrow from the typed draft.** `CaptureItem<'a>` borrows slices of one
   source string. The expansion therefore needs its own text buffer plus a source map
   back to the typed draft. `[cdx, cld]`
4. **Braces mean nothing today.** `{` and `}` have no role in the capture grammar and
   are illegal in block IDs and routes. `[all; probed]`
   - `@job_2026_apply_29:{1}` therefore fails today with `invalid_pomodoro_block_id`.
   - Probe: the request's draft parses as three plain `task` items plus that error.
5. **Global declarations.** `parse_global_destination_token` (`draft.rs:810`) accepts
   `@@<route>` and `@@<route>+<id>`, and refuses any token containing `:`. Probes
   against the installed bob, giving the current behavior for what the draft starts
   with: `[lead]`

   - **`@@template`:** Valid route. The dry run targets the existing `template.md` (a
     zorg-generated "List of available template files") with `placement: appended`.
   - **`@@tmpl`:** Valid route. The dry run would *create* `tmpl.md`.
   - **`@@template:`:** `invalid_global_destination` error; `capture` exits 2 and
     writes nothing.

6. **bob's quoting rule, and smart quotes.**
   - Inside a quoted note name (`&"Shopping List":bar`), only `\"` and `\\` are
     escapes (`dependencies.rs`). `[cld]`
   - bob already treats `“…”` as a quote pair when it suggests block IDs
     (`capture_block_ids.rs:522`), so it already expects smart quotes in drafts.
     `[lead]`
7. **`@@` absorption in `capture-rewrite`.** The bare-`@@` rule only fires when the
   `@@` sits *inside* an item line. `[lead; probed]`
   - `@@ Buy {0} @groceries` was rewritten to `@@groceries Buy {0}`.
   - Typing `@@` on its own line above an existing template did not trigger it.
   - So the header must sit on its own line.
8. **Completion while typing the header.** `[lead; probed]`
   - At `@@te`, `capture-complete` returns a `route` context with fuzzy project
     candidates.
   - At `@@template:`, the context is null, so nothing pops up.
9. **The plan budget only warns.** `[lead]`
   - Going over the link cap only warns. The deployed cap is `plan.max_links: 12`; cld
     quoted the docs example value, 10.
   - `plan.strict` refuses only growth in themes.
   - The per-note Ready soft cap (`plan.max_ready_per_note`, default 5) is not checked
     at capture time.
10. **CLI rules** (`cli_rules.md`): `[cli_rules; probed]`
    - never add a subcommand under `bob capture`;
    - `capture-*` protocol commands grow only additively;
    - every public long option gets a short alias. `-E` is currently unused on
      `bob capture`.

### Bob Mac Capture facts

1. **It is a thin client.** Decision `mac-capture-is-a-thin-client`: bob is the only
   implementation of the grammar. Expanding templates in Swift is off the table.
   `[all]`
2. **The draft is one argv value.** The app passes the whole draft after `--` to
   `capture-parse`, `capture-complete --cursor`, `capture-rewrite`,
   `capture --dry-run --no-clip`, and the final submit (`BobProcessClient.swift`).
   `[cdx, cld; verified]`
3. **Highlighting is all-or-nothing.** `validatedSpanRanges`
   (`CaptureTextRanges.swift:113`) returns nil if any span is out of order, overlaps
   another, or falls outside the text. The panel then shows "Ignored malformed parse
   spans." `[cld; verified]`
4. **Some decoding is strict.** `[cld; verified]`
   - Each parse item must have `index`, `range`, `line_start`, `line_end`, `body`, and
     `mode`.
   - Parse, complete, and rewrite responses must have `schema_version == 1`.
5. **Any item can open a picker.** `pickerNeed(in:)` (`CapturePanelModel.swift:4571`)
   combines the top-level `needs` with the `needs` of **every** item. `[lead, extends
   cld]`
   - Any picker need puts the panel into a quiet "incomplete" state and skips the live
     dry run.
   - So a row that happens to read like `:query` or `@route:` would take over the
     panel, unless rows report no needs.
6. **Only one diagnostic is shown.** The status line shows the first diagnostic whose
   severity is not `info`, and ignores its range (`:6861`). Template problems must
   therefore be `error` or `warning` diagnostics. `[cld; verified]`
7. **Smart quotes stay on in the draft editor.** `[lead]`
   - `CaptureEditorTextConfiguration` turns off only smart dashes.
   - The README says "smart quotes are unchanged."
   - With the macOS setting on, typing `"Two Sigma"` produces `“Two Sigma”`.
8. **Tab never inserts a tab character.** Plain Tab accepts a completion, then tries
   the `--`→`—` snippet, then indents a bullet (`CaptureKeyCommandRouter.swift:192`).
   `[lead]`
   - Tab-separated rows can only arrive by paste, and the tabs are invisible in the
     editor.
   - This undercuts gem's proposal to split rows on tabs first.
9. **Preview cards come straight from the dry run.** They are built from
   `capture --dry-run`'s `captures[]`, so expanded rows appear as cards with no app
   change. `[all]`

## Is this a good idea

**Yes, if the scope stays narrow.**

Reasons for:

- **It is a real, recurring workflow.** This is the 29-application project. Wave 2 had
  10 roles and wave 3 has 12, in a single week.
- **It saves more than keystrokes.** A 12-row batch saves about 35 characters per row.
  More importantly, it removes 12 chances to mistype the route or the ID shape, and the
  whole batch gets one preview and one all-or-nothing commit.
- **It needs no new execution concepts.** N rows become N ordinary items in the
  existing batch.
- **It is useful beyond job applications:**
  - `{0} @groceries` with one item per line;
  - `^route:{0}` to bulk-link existing tasks;
  - `!note:{0}` to bulk-complete tasks;
  - reading queues.

Costs and risks:

- **Grammar size.** `docs/capture.md` is already about 5,900 lines. An explicit header
  contains the cost: drafts without it behave exactly as they do today.
- **Two representations.** The editor protocol must reconcile the typed draft with the
  expanded text, and that is most of the work.
- **Mistakes multiply.** Positional fields are easy to swap, and a wrong constant
  (route, `:` versus `^`) is copied into every row. The defenses are the live preview
  and a strict field count.
- **Values are inserted as capture source.** A value that looks like a marker acts
  like a marker. That is honest macro behavior: the preview shows it and the docs
  should say so. It is not a channel for literal data.
- **An agent could do it instead.** When rows come from an LLM report, as waves 2 and 3
  did, asking the agent to end its report with a ready-to-paste capture draft costs no
  code. Templates pay off when Bryan assembles rows himself in the panel. The prose
  format of the Wave 3 PDF suggests he will.

Cheaper alternatives, and why none replaces the feature:

- **A shell function** around one `bob capture` call. It is atomic if it makes a single
  call, but the panel never sees it. Fine as a stopgap.
- **Agent-written capture drafts.** Works only when an agent produces the rows.
- **Expansion in the Mac app.** Forbidden by the thin-client decision.
- **Inline alternation** such as `{a|b}` (cld S5). Poor for rows with several fields.

None of these covers rows that Bryan assembles by hand in the panel.

### Critique of the proposal as written

1. **The roles are inverted.** The first item is the template; the later lines are
   **rows** of values, not "templates for the first input." Help text and diagnostics
   should say "template" and "rows." `[all]`
2. **Splitting fields on spaces breaks on the motivating data.** Two Sigma, D. E.
   Shaw, Tower and Tailscale, and Susquehanna SIG all contain spaces. This is a hole in
   the design, not a later enhancement. `[all]`
3. **Activation is unspecified.** Is a single item containing `{0}` a template? How do
   you write literal braces? `[all]`
4. **Blank lines between rows are verbose.** Rows are single lines. With one row per
   line, a pasted column works without editing. `[cdx, cld, gem]`
5. **`:` multiplies.** `@job_2026_apply_29:{1}` makes every row a Next task with a Task
   Link, and all of them land under the *one* selected Pomodoro. `[lead]`
   - Bryan's habit is to link one or two apply tasks per JOB session as he works them.
   - A `:` batch of 7–12 rows puts them all under the current session, and warns once
     today passes `max_links: 12`.
   - `^apply-{1}` instead creates plain Ready tasks. That puts 7–12 Ready tasks in one
     project note, above the soft cap of 5.
   - Both are legitimate. The feature must support both; the choice in the example
     should just be deliberate.
6. **Interactions are unspecified:** `@@` inside a template, `%` clipboard markers,
   session operators, rows with the wrong number of fields, duplicate IDs, and per-row
   extras.

## Requirement adjustments

- **A1**
  - *Request:* The template is the first input, detected by `{0}`
  - *Adjusted to:* A first line `@@template:`, then the template
  - *Why:* Deterministic. Safe on older bob. The editor knows the rows from line 1.
    `@@template` is taken by `template.md`.
- **A2**
  - *Request:* Later inputs are "templates for the first"
  - *Adjusted to:* Later **lines** are **rows** of values
  - *Why:* Correct roles; clearer docs.
- **A3**
  - *Request:* Rows are separated by blank lines
  - *Adjusted to:* One row per nonblank line; blank lines optional
  - *Why:* A pasted column works unchanged, and the request's spacing still works.
- **A4**
  - *Request:* Fields are split on spaces
  - *Adjusted to:* Whitespace plus `"…"` or `“…”` grouping; exact field count; a
    one-field template takes the whole row
  - *Why:* Real names contain spaces. The Mac editor produces smart quotes. A forgotten
    quote becomes a teaching error.
- **A5**
  - *Request:* (unspecified)
  - *Adjusted to:* Indices `{0}`…`{N-1}` with no gaps; `{{ }}` escapes; no named,
    formatted, or sequential placeholders
  - *Why:* Catches the 1-based habit and gaps, and leaves room to grow.
- **A6**
  - *Request:* "Should be equivalent"
  - *Adjusted to:* Normative: `capture(D) ≡ capture(expand(D))`, all-or-nothing. Only
    source locations and added metadata differ.
  - *Why:* It is the spec, the docs sentence, and the test oracle at once.
- **A7**
  - *Request:* (unspecified)
  - *Adjusted to:* Refuse `%`, session operators, and extra `@@`. Reserve per-row
    bullets. No ordinary items mixed into a template draft.
  - *Why:* Prevents repetition nobody intends, and merges nobody can define.
- **A8**
  - *Request:* The example uses `:`
  - *Adjusted to:* Keep it, but flag it: `:` links every row under one Pomodoro;
    `^apply-{1}` creates plain Ready tasks
  - *Why:* Bryan's history links one or two per JOB session.
- **A9**
  - *Request:* Mac app support
  - *Adjusted to:* No grammar in Swift. v1 needs no app change; presentation is
    optional.
  - *Why:* Thin-client decision.

## Where the reports disagreed and how I resolved it

Each question lists the four reports' positions, then the resolution.

- **Activation**
  - *cdx:* Explicit `@@template:`
  - *cld:* Implicit: first item has `{N}`
  - *grk:* Implicit: `{N}` plus at least 1 later item
  - *gem:* Explicit `@@template` or `@@tmpl`
  - *Resolution:* **Explicit `@@template:`**
    ([activation](#activation-by-an-explicit-header)). gem's spelling collides with
    the real `template.md`. Implicit detection loses on determinism, editor clarity,
    and safe failure.
- **Index base**
  - *cdx:* `{0}`
  - *cld:* 1-based; `{0}` = whole row
  - *grk:* `{0}`
  - *gem:* `{0}` plus sequential `{}`
  - *Resolution:* **`{0}`**, as Bryan wrote. Dense-index validation turns either habit
    into a teaching error, so this choice carries little risk
    ([placeholders](#placeholders)).
- **Row boundary**
  - *cdx:* Line
  - *cld:* Line
  - *grk:* Blank-line-separated item
  - *gem:* Line, plus per-row bullets
  - *Resolution:* **One row per line**; blank lines between rows optional.
- **Field split**
  - *cdx:* Whitespace + `"…"`, `""` doubling
  - *cld:* Whitespace + `"…"`, `\"` escape
  - *grk:* Tokens, extras join `{0}`; or `|`; or one field per line
  - *gem:* Tab, then pipe, then shell words
  - *Resolution:* **Whitespace + `"…"` or `“…”`**, with bob's `\"` / `\\` rule. A
    one-field template takes the whole row. Pipes and tabs deferred
    ([rows and fields](#rows-and-fields)).
- **Field count**
  - *cdx:* Exact
  - *cld:* Exact; gaps allowed
  - *grk:* Exact; extras join `{0}`
  - *gem:* At least N
  - *Resolution:* **Exact**, with no gaps in the indices.
- **Per-row child bullets**
  - *cdx:* No
  - *cld:* Reserved
  - *grk:* n/a
  - *gem:* Appended
  - *Resolution:* **Reserved** (an error in v1). A later "expand into editor" action
    covers one-off extras.
- **`@@` in template drafts**
  - *cdx:* Refuse
  - *cld:* Hoist an inline `@@` once
  - *grk:* n/a
  - *gem:* Is the header
  - *Resolution:* **Refuse** in v1. The template can carry a local `@route`.
- **`%` and session operators**
  - *cdx:* Allow any single-item kind
  - *cld:* Refuse
  - *grk:* Refuse
  - *gem:* Refuse
  - *Resolution:* **Refuse.**
- **Literal braces**
  - *cdx:* `{{ }}`
  - *cld:* `\{`; code spans stay literal
  - *grk:* `{{ }}`
  - *gem:* `{{ }}`
  - *Resolution:* **`{{ }}`.** No code-span exemption: the header makes it
    unnecessary, and substituting inside `` `{0}` `` is useful.
- **Mac changes**
  - *cdx:* Presentation
  - *cld:* None required
  - *grk:* None required
  - *gem:* Span styling
  - *Resolution:* **None required**; polish is optional.

## Syntax

### Activation by an explicit header

**Rule:** a draft is a template draft exactly when its first nonblank physical line is
`@@template:`. Trailing spaces or tabs are allowed; nothing else may be on that line.

Why require a header, even though the vault has zero literal `{N}` tasks:

1. **Reach.** A template changes how *other* lines are read: rows stop being captures.
   A mode with that reach should be declared, not inferred from a substring. bob's
   other draft-wide behavior, `@@route`, is declared too.
2. **No ambiguity while typing.**
   - grk's rule (placeholders plus at least one later item) flips the preview the
     moment the first row appears.
   - cld's rule (placeholders always mean a template) forces an escape on a lone
     `Read RFC {0}`.
   - A header avoids both.
3. **The editor knows from line 1.** Completion and pickers can be turned off in the
   row area before any placeholder exists.
4. **Safe failure on older bob.** Current bob refuses `@@template:` with exit 2 and
   writes nothing. Without a header, a prose template such as `Email {0} about refs`
   followed by rows would make an older bob capture every line as a literal inbox
   task.
5. **It is reversible.** Moving from explicit to implicit later is a small change,
   since no task uses literal `{N}`. Moving the other way would break habits.
6. **Room for options.** The header could later carry options such as
   `@@template:tsv`, with no new syntax family. This is speculative; don't build it
   now.

The cost is 12 characters per batch. Two cheap measures soften it:

- **Completion.** bob's `@@` route completion should offer `template:` as a
  candidate.
- **A hint for the header-less form.** If a draft without the header has `{N}` in its
  first item and has later items, `capture-parse` emits a `template_header_missing`
  **warning**: "add `@@template:` as the first line to use this as a template."
  - That way Bryan's original header-less draft teaches instead of capturing
    literally.
  - `bob capture` itself keeps today's behavior for drafts without the header.

**Error cases:** a header that is not on the first nonblank line, or a second header,
is an error.

**Spellings rejected:**

- `@@template`, `@@tmpl`, `@@each`: all are valid routes today, and `template.md`
  exists.
- `%template`: belongs to the clipboard-header family.
- A `---` separator: it would be a fourth meaning for runs of dashes (cld).
- A fenced block: too heavy for the panel.
- A `--template` flag: the Mac app never passes flags, and a stashed or pasted draft
  would lose its meaning.
- An inline header such as `@@template: Apply …`: keeping it on its own line keeps
  framing and `@@` absorption simple.

### Placeholders

- **Form.** A placeholder is `{` + a canonical ASCII decimal number + `}`. It is
  zero-based, as in the request; think of Python's `str.format`.
- **No gaps.** The indices used must be exactly `0` through `N-1`. Repeating or
  reordering them is fine; skipping one is an error.
- **The 1-based habit is caught.** `{1}{2}{3}` is sase's xprompt convention. It
  produces: *"placeholders start at {0}; this template uses {1}–{3}"*.
- **Literal braces.** Write `{{` and `}}`.
- **Other brace forms are errors.** `{}`, `{name}`, `{0:x}`, or a lone `{` or `}` in
  the template give an error that says "write {{ for a literal brace." That keeps named
  slots, defaults, and filters available for later.
- **Placement.** Placeholders may appear anywhere in the template's parent line and
  authored children, including inside markers: `@job_2026_apply_29:apply-{1}`,
  `[[{0}]]`, `` `{0}` ``.
- **Single pass.** An inserted value is never scanned again for placeholders.
- **At least one** placeholder is required.

**Why not 1-based (cld).** Bryan chose `{0}`, and three of the four reports keep it.
Because the no-gaps rule makes the wrong habit fail loudly, matching sase's `{1}` buys
little. cld's convenience of "`{0}` is the whole row" survives in another form: a
template with one field takes the whole row ([rows and fields](#rows-and-fields)).

**Why not sequential `{}` (gem).** A second placeholder style saves nothing in a
template with about three fields.

### Rows and fields

- **Rows.**
  - After the blank line that ends the template, every nonblank physical line is one
    row, in order.
  - Blank lines between rows are ignored.
- **Bullet lines are reserved.** A row line that starts (after optional indentation)
  with `- `, `* `, or `+ ` is reserved for future per-row children, and is an error in
  v1.
- **A blank line must end the template.** A non-bullet line directly under the
  template is today's continuation error, with a new message: "add a blank line
  between the template and its rows."
- **Fields.** Fields are split on runs of spaces or tabs.
  - A field that **starts** with `"` or `“` runs to the matching `"` or `”`, which
    must be followed by whitespace or the end of the line.
  - Inside quotes, only `\"` and `\\` are escapes. That is bob's existing quoted-note
    rule.
  - A quote in the middle of a field, as in `5"`, is literal.
  - `""` or `“”` is an empty field.
  - An unterminated quote is an error. On the last row, `capture-parse` reports it as
    an incomplete state instead.
- **Exact field count.** Every row must have exactly N fields. The error names the row
  and line, gives both counts, and hints at quoting:
  `template row 3 (line 7) has 4 fields but the template uses {0}–{2}; quote a field
  that contains spaces: "Two Sigma"`.
- **One-field templates.** If the template uses only `{0}`, the whole trimmed row is
  the value, with no splitting or quote handling. So `{0} @groceries` with the rows
  `oat milk` and `green onions` just works.

Rejected for v1:

- **Pipes** (`A | b | c`) as a per-row dialect detected automatically (grk, gem).
  - They compete with quotes, and they break wikilink aliases (`[[note|alias]]`)
    inside values.
  - They would be a second dialect to teach.
  - They are a good v1.1 candidate as Markdown pipe-table rows if LLM tables become the
    data source (cld S7).
- **Tabs** (gem). Tab cannot be typed in the panel, pasted tabs are invisible, and
  spreadsheets are not where the data comes from.
- **Extra tokens joining `{0}`** (grk). Clever when the title is first. But it
  misassigns silently when the extra token is anywhere else, and it removes the
  safety net of a strict field count.
- **"At least N fields, extras ignored"** (gem). It silently drops data.
- **CSV-style `""` doubling** (cdx). It fights smart quotes and bob's existing `\"`
  rule.

### Interactions with existing markers

Everything here follows from `capture(D) ≡ capture(expand(D))`, except the refusals.
Each item names what the template contains, then the v1 behavior.

- **`@route`, `@route^id`, `@route:id`, `@route+id`, `#section`:** Applied to each
  instance. Duplicate IDs across rows are refused by the existing planner.
- **`:id` (Pomodoro link):** One Task Link per row, under the selected Pomodoro. Warns
  once links pass `max_links`.
- **`s:<N>`, `p:<N>`:** Every instance gets the same date; each instance rolls its own
  priority (the existing rule).
- **`&note:id`, `*note:id`:** Every instance gets the edge. Cycle checks are unchanged.
- **`!note:{0}`, `^route:{0}`:** Bulk-complete or bulk-link existing tasks. Allowed.
- **An instance that is a bare URL:** Becomes a reference job, exactly as typed text
  would.
- **`%`, `%N`, `%header` (clipboard):** **Refused** (`template_clipboard`). Repeating
  one clipboard N times is never intended.
- **An instance that reads as a session operator (`=`, `=x`, `+N`, `++N`, `-N`, …):**
  **Refused** (`template_session_operator`).
- **Any `@@` other than the header, whether in the template, in a row, or produced by
  a value:** **Refused** (`template_global_declaration`): "put the destination in the
  template line."
- **A value that forms a marker (`p:1`, `@home`):** Acts as that marker. This is macro
  behavior; document it. The preview shows it.

## Implementation

### Where the code goes in bob-cli

Add a new module, `src/native/capture_language/template.rs`. It is pure: no vault,
clipboard, or network access. It has four steps:

- **`frame(raw) -> Option<TemplateFrame>`** finds the header on the first nonblank
  physical line. It then takes the template block (a parent line plus authored
  children, up to the first blank line) and the row lines, all with byte ranges. It
  runs **before** `split_capture_draft`, so rows never reach declaration stripping,
  URL-list splitting, or session-chain splitting.
- **`compile(template) -> CompiledTemplate`** scans the placeholders, handles
  `{{ }}`, and checks for gaps and reserved forms.
- **`lex_row(row, n) -> Vec<Field>`** splits one row into fields, keeping byte ranges
  in the typed draft.
- **`expand(...) -> TemplateExpansion { text: String, map: SourceMap, rows }`** joins
  the instances with blank lines and drops the header.

How it plugs into the existing code:

- **Callers own the expansion.** These callers already own the raw `String`:
  - `plan_capture_batch` (`capture/plan.rs`);
  - `CaptureParseResult::new` (`capture_parse.rs`);
  - the completion engine;
  - `rewrite_draft`.

  Each one owns the `TemplateExpansion` and passes `&expansion.text` to the existing
  path.
- **No new machinery.** There is no new `CaptureKind`, no recursion, and no subprocess
  per row.
- **Bounds.** Cap the number of rows and expanded bytes (for example 1,000 rows and
  1 MiB). Those numbers are a starting point to benchmark, not measurements. Refuse
  oversized drafts instead of truncating them.

### Real runs and dry runs

This covers `bob capture`, both real runs and `--dry-run`.

- **Unchanged:** the planner, commit, reference jobs, and plan budget.
- **Errors.** Template validation errors are usage errors (exit 2), and nothing is
  written.
- **Error locations.** Both the parser's and the planner's error prefixes go through
  the source map. They print `template row k (line L): …`, never offsets into the
  expanded text (cld §7.1).
- **JSON.** Purely additive:
  - a top-level `template` object (`line`, `fields`, `rows`);
  - a `template_row` object (`row`, `line`) on each `captures[]` entry;
  - a one-row template keeps the legacy single-result shape;
  - drafts without a header produce byte-identical output to today.
- **Human output.** A summary such as `template  3 rows (lines 5–7)`, then the usual
  `1/N` lines.
- **Optional `-E, --expand`.** Prints `expand(D)` and exits without planning. Useful
  for debugging and scripts, and for a future "expand into editor" action. It must
  follow the CLI rules: short alias, alphabetical order, good help text.

### The editor protocol is the real work

Every range is a UTF-8 byte offset into the typed draft. Spans stay sorted and
non-overlapping. `schema_version` stays 1.

**`capture-parse`:**

1. **Header.** Emit a `template_header` span. Report no `global_destination` and no
   `invalid_global_destination`.
2. **Template highlighting by masking (cld's technique).**
   - Make a copy of the typed draft in which each `{N}` becomes the same number of
     `x` bytes, and each `{{` or `}}` becomes `xx`.
   - Byte offsets are unchanged, and `x` is valid in every token class. So today's
     parser, run on the copy, yields spans and needs that already index the typed
     draft.
   - Add a `template_placeholder` span on each `{N}`, splitting any span it falls
     inside. For example, `^apply-{1}` becomes `^apply-` followed by `{1}`.
   - Never reuse the `interactive_placeholder` span kind; the Mac app's close-pending
     logic depends on it.
   - **Caveat:** a placeholder whose real values change the token's meaning is
     highlighted by the mask. For example, `p:{0}` masks to `p:xxx`, which reads as
     prose. The per-row parses still report real problems. Document this.
   - **Partly typed placeholders.** An unterminated `{` or `{digits` at the cursor is
     an incomplete placeholder. It must produce no `invalid_*_block_id` error and no
     picker context.
   - Typing `@job_2026_apply_29:` before `{1}` already yields the quiet `pomodoro_id`
     need, which is fine.
3. **Row spans.** Emit one `template_field` span per field, quotes included. Add an
   additive `field` index so a client can alternate colors.
4. **`items[]`.**
   - Item 1 is the template, read through the mask. It keeps its real typed range, so
     pickers opened from template markers insert correctly.
   - Each row becomes one more item, with:
     - `mode: "template_row"`;
     - the row's typed range and line;
     - `body` set to the instance's body;
     - **`needs: []`**, because the Mac app combines every item's needs.
   - Add a per-item `template_row` object with `fields[]` and the instance's real
     `mode`.
5. **Diagnostics.**
   - Parse each instance with the normal editor parser.
   - Map each diagnostic to the field's range if it overlaps exactly one field, and to
     the whole row otherwise.
   - Drop the instances' spans; the masked template already describes the template.
   - Drop masked-template diagnostics that touch a placeholder; the per-row parses own
     those.
6. **New diagnostic codes:**
   - `template_missing_rows`, together with `needs: ["template_row"]` and an
     `error`-severity diagnostic, so the Mac status line shows it;
   - `template_row_arity`;
   - `template_unterminated_quote`;
   - `template_invalid_placeholder`;
   - `template_placeholder_gap`;
   - `template_needs_separator`;
   - `template_row_bullet`;
   - `template_header_misplaced`;
   - `template_clipboard`;
   - `template_session_operator`;
   - `template_global_declaration`;
   - `template_header_missing` (a warning: the hint for the header-less form).
7. **Top-level `template` object.** `range`, `line_start`, `line_end`, `fields`, and
   `rows[]`. Each row has `row`, `line`, `range`, `fields[]`, `expansion`, and `mode`.

**`capture-complete`:**

- With the cursor anywhere in the rows, or inside a placeholder, return an empty
  success (`context: null`).
- Elsewhere in the template, complete against the masked copy. Drop any candidate
  whose replacement range touches a placeholder; otherwise accepting a block-ID
  candidate at `:{2}` would overwrite the `{2}`.
- In the `@@` route context, offer `template:` as a candidate.

**`capture-rewrite`:** do nothing on template drafts in v1. No `@@` absorption, and no
`:`/`^` separator toggle on rows or across placeholders. Rewrites on the template item
can be enabled later, with mapping tests.

### Bob Mac Capture

**Required changes: none.** Checked against the code:

- New span kinds render as neutral.
- Every item still has the strictly decoded fields.
- `pickerNeed` ignores the `template_row` mode and the `template_row` need.
- The preview renders `captures[]` as cards.
- Submit is still one `bob capture` call.

**Optional polish** (gated by macOS CI, per the repo's `AGENTS.md`):

- Colors for `template_header`, `template_placeholder`, and `template_field`, with
  alternating shading per field. Seeing how a row split is the main visual defense
  against mis-split rows.
- A "Template · N rows" header above the preview, read from the `template` object.
- Optionally, underline the offending row or field using the diagnostic's range, which
  the app ignores today.
- A quiet "incomplete" treatment for the `template_row` need.

**Later ideas:**

- An "Expand into editor" action backed by `bob capture --expand`, as an undoable
  replace. It lets Bryan tweak individual rows.
- A snippet that inserts a template skeleton (presentation only).
- The canceled-draft stash already brings back the previous batch's template.

**Do not** port expansion to Swift, and do not rewrite the editor text automatically.

**Compatibility:**

- **New app with new bob:** Full template editing and preview.
- **Old app with new bob:** Works; no colors or chip.
- **Any app with old bob:** `@@template:` gives `invalid_global_destination`; nothing
  is written.

### Tests to require

- **The equivalence oracle.** For every golden template draft, `plan_capture_batch(D)`
  and `plan_capture_batch(expand(D))` must plan identical edits and results. Use the
  same clock, config, snapshots, and priority seed, and cover every marker family in
  [interactions with existing markers](#interactions-with-existing-markers).
- **The core example.** Two exact titles, IDs, URL children, order, and Task Links.
- **Compatibility.**
  - Drafts without a header that contain braces behave byte-for-byte as today.
  - A fixture shows that older bob refuses `@@template:`.
- **The row lexer.**
  - Spaces and tabs.
  - `"Two Sigma"` and `“Two Sigma”`.
  - `\"`, `""`, and apostrophes (`O'Reilly`).
  - A quote in mid-field, and an unterminated quote.
  - CRLF and bare CR line endings.
  - Emoji and accented values.
- **Placeholders.**
  - Repeats and reordering.
  - `{{ }}`.
  - Gaps, and the 1-based habit.
  - `{}`, `{name}`, `{01}`, and unmatched braces.
  - A placeholder inside a block ID.
- **Framing.**
  - A header alone, and a misplaced or repeated header.
  - No rows, and a missing blank line before the rows.
  - A bullet line in the rows.
  - `@@` in the template, in a row, or produced by a value.
- **Refusals.** `%`, and an instance that reads as a session operator.
- **Span invariants.**
  - Spans are sorted, non-overlapping, and on character boundaries.
  - Multi-byte values.
  - A placeholder splitting an existing span.
- **Completion.**
  - A cursor in a row gets no context.
  - A block-ID candidate at `:{1}` is suppressed.
  - Route completion inside the template still works.
  - `@@te` offers `template:`.
- **Atomicity.** A bad ID on row 5 refuses rows 1–4 as well.
- **Mac.** Decoding tests for the additive fields, once the polish phase lands.

### Phases and size

1. **bob-cli phase 1: language, execution, and editor safety.**
   - The template module.
   - `bob capture` and dry-run integration.
   - JSON and human output, and the error messages.
   - `--expand`.
   - Docs: a new `docs/capture.md` § Bulk templates, rows in the grammar-at-a-glance
     table, and `--help`.
   - The editor **safety gates**: the header is recognized, rows are opaque with no
     needs, spans and diagnostics are reported per row, completion is off in rows, and
     rewrite does nothing.

   This phase alone makes templates usable in the Mac panel. The gates cannot wait:
   without them, the Mac status line shows `invalid_global_destination` for the
   header, and rows can trigger pickers, even though the dry-run preview is correct.
2. **bob-cli phase 2: the rich editor.**
   - Template highlighting through the mask.
   - Placeholder and field spans.
   - Diagnostics mapped to the exact field.
   - Completion inside the template, and the `template:` candidate.
   - The hint for the header-less form.
3. **Mac phase (optional):** colors, the chip, and inline diagnostic ranges.

**Size.** cld's estimate looks right: about 500–700 lines of Rust, 800–1,000 lines of
tests and goldens, and about 150 lines of docs.

**Afterwards.** Record a decision record, such as "Bulk templates are a declared text
expansion before parsing," and update the glossary's Bulk Capture strand. Both go
through `/sase_memory_write`.

## Open questions for Bryan

1. **`:` or `^apply-{1}` in the job template** ([A8](#requirement-adjustments))?
   - `:` links every row under the current JOB Pomodoro, and warns once links pass
     `max_links: 12`.
   - `^apply-{1}` creates plain Ready tasks that you link as you work them, matching
     your habit so far. It also matches the existing `^apply-<slug>` IDs.
2. **Is a 12-character header acceptable?** If it chafes in real use, implicit
   detection can be added later (a header-less first item with `{N}` followed by rows).
   The planned warning for the header-less form already points the way.
3. **Refusing `%` and session operators in v1:** OK? Allowing them later is purely
   additive.
4. **`--expand` in v1, or later?**

## Follow-ups not for v1

1. **A `{N|slug}` filter (cld).** It would derive `two-sigma` from `"Two Sigma"`,
   which removes the slug column from Bryan's rows.
   - Given the `^apply-<slug>` evidence, this is the most valuable follow-up.
   - Reuse the slugging from block-ID suggestions.
   - With it: `@job_2026_apply_29^apply-{0|slug}`.
2. **Markdown pipe-table rows**, skipping the header and separator rows, once LLM
   tables become the data source.
3. **Per-row child bullets.** The syntax is already reserved.
4. **Named placeholders and defaults** (`{company}`, `{0:default}`).
5. **Saved templates**, as a snippet or a vault note, once the same template keeps
   coming back.

## Recommended solution

Implement **bulk templates** entirely in bob-cli as a declared text expansion before
parsing. The rule is `capture(D) ≡ capture(expand(D))`, all-or-nothing.

**Syntax:**

1. **Header.** The first line of the draft is `@@template:`.
2. **Template.** The next block, a parent line plus authored children, holds `{0}`…
   `{N-1}`:
   - no gaps in the indices;
   - repeats are allowed;
   - `{{ }}` for literal braces;
   - placeholders may sit inside markers.
3. **Rows.** After a blank line, each nonblank line is one row; blank lines between
   rows are optional.
4. **Fields.** Fields are separated by whitespace and grouped with `"…"` or `“…”`
   (with `\"` and `\\` escapes). The field count is exact, and a one-field template
   takes the whole row.
5. **Refused in v1:** `%` clipboard markers, session operators, and any other `@@`.
   Per-row bullets are reserved, and ordinary items cannot be mixed into a template
   draft.

**Implementation:**

1. Add a pure `template.rs` that runs before `split_capture_draft`, with an owned
   expansion and a source map.
2. Feed the expansion to the unchanged parser, planner, and writer.
3. Extend the JSON additively (`template` and `template_row`) and keep
   `schema_version` 1.
4. Ship the editor [safety gates](#phases-and-size) in the first phase, and rich
   highlighting and completion in the second.
5. Add a `-E, --expand` flag.

**Bob Mac Capture** stays a thin client:

- it works unchanged in v1, because its dry-run preview already shows the expanded
  captures;
- it later adds colors for the template spans and a "Template · N rows" chip;
- it never gets its own expander.

**Decide before implementing:** `:` versus `^apply-{1}` for the job template. Plan the
`{N|slug}` filter as the [first follow-up](#follow-ups-not-for-v1).

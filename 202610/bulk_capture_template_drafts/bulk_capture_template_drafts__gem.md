# Research: Template Expansion for Bulk Capture in bob-cli and Bob Mac Capture

**Researcher:** `research.1j.gem`  
**Date:** 2026-10-15  
**Target Repositories:** `bob-cli`, `bob-mac-capture`  
**Artifact ID / Label:** `research:202610/bulk_capture_templates__gem.md`

---

## 1. Executive Summary

This research investigates adding first-item template definitions to bulk capture in `bob capture` and the native macOS frontend `bob-mac-capture`.

In the proposed workflow, the first capture input defines a template containing placeholders (such as `{0}`, `{1}`, `{2}`), and subsequent inputs provide variable arguments that instantiate the template into concrete tasks or bullets.

### Key Conclusions:
1. **High Practical Value, but Flawed Initial Mechanics:** The concept itself is outstanding for repetitive capture patterns (job applications, reading queues, bug triage, CRM outreach, conference talk logs). However, the initial design—relying on implicit activation via `{0}` and naive whitespace-delimited argument splitting—suffers from severe failure modes in real-world usage (breaking on multi-word entities like company names, false-positive triggering on code/regexes, and painful blank-line formatting requirements).
2. **Grammar & Delimiter Reform:**
   - **Explicit Activation (`@@template` / `@@tmpl`):** Consistent with Bob's existing `@@route` declaration system, an explicit declaration ensures zero false positives on code snippets, regexes (`{0,5}`), or mathematical notation.
   - **Multi-Tier Field Delimitation:** A single-strategy whitespace splitter fails immediately when capturing entities with spaces (e.g., `Goldman Sachs`, `Senior Systems Engineer`). We recommend an automatic 3-tier delimiter resolution per row: **Tabs (`\t`)** for spreadsheet/table clipboard pastes, **Pipes (`|`)** for natural human typing without quotes, and **Shell Words (quotes + whitespace)** for quick single-word entries.
   - **Flexible Row Separation:** To support pasting tables directly from spreadsheets or Notion without tedious manual blank-line insertion, the engine must support both consecutive single-line rows and blank-line-separated multi-bullet rows.
   - **Placeholder Grammar:** Support indexed `{0}`, `{1}` (allowing argument re-use and re-ordering) alongside sequential unnumbered `{}` (for rapid typing), with `{{` and `}}` escaping.
3. **Architectural Elegance via Thin Client Invariant:** Per Bob Architecture Decision 6 (`mac-capture-is-a-thin-client`), `bob-cli` is the sole authority for grammar, preview, and execution. Because `bob-mac-capture` already renders `normalizedCaptures` from `bob capture --dry-run`, **the live preview cards in the Mac HUD work automatically with zero SwiftUI view restructuring**. The app only needs additive syntax span styling in its text view.

---

## 2. Background and Existing System Invariants

### 2.1 The Current Capture Pipeline in `bob-cli`
1. **Draft Splitting (`split_capture_draft` in `draft.rs`):**
   - The raw text buffer is split into physical lines.
   - Global declarations (`@@<route>`, `@@<route>+<block-id>`) are extracted and stripped from the line stream.
   - Remaining physical lines are split into `CaptureItem`s by one or more blank or whitespace-only lines (`\n\n`).
   - Within each item, line 1 is the parent task/bullet. Later column-zero lines (`-`, `*`, `+`) become depth-1 authored sub-bullets; two-space indented lines become depth-2 sub-bullets. Consecutive unindented prose lines without blank lines are rejected as syntax errors.
2. **Editor Lexing & Diagnostics (`bob capture-parse`):**
   - Purely lexical, vault-agnostic, and read-only.
   - Emits structured JSON containing `mode`, resolved routes, `spans` (byte ranges for semantic syntax coloring), `diagnostics` (warnings/errors with source ranges), and an array of parsed items.
3. **Live Preview (`bob capture --dry-run`):**
   - Plans in-memory mutations against vault note snapshots.
   - Single-item drafts return top-level fields; multi-item drafts return an ordered `captures` array containing each planned task/bullet.
4. **Execution (`bob capture`):**
   - Executes staged atomic batch writes across the daily note and area/project notes.

### 2.2 Bob Mac Capture Invariants
Under Decision 6 (`mac-capture-is-a-thin-client`), Bob Mac Capture never parses grammar or computes previews.
- On keystroke changes in `CapturePanelView`, the app spawns:
  - `bob capture-parse --format json -- <draft>` for syntax spans and validation diagnostics.
  - `bob capture --dry-run --no-clip --format json -- <draft>` for live preview cards.
- Previews are displayed via `previewContent` in `CapturePanelView.swift`, which uses `success.normalizedCaptures` (`captures.isEmpty ? [self] : captures`) to render a stack of cards separated by dividers.
- Submissions execute via a single `bob capture` invocation.

---

## 3. Critique of the Proposed Plan

The user proposed the following syntax:
```markdown
Apply to {0}! @job_2026_apply_29:{1}
- **URL**: {2}

Foobar foo http://foobar.com/career/some_foo_job

Bazbuz baz http://bazbuz.com/career/some_baz_job
```
Expanding to:
```markdown
Apply to Foobar! @job_2026_apply_29:foo
- **URL**: http://foobar.com/career/some_foo_job

Apply to Bazbuz! @job_2026_apply_29:baz
- **URL**: http://bazbuz.com/career/some_baz_job
```

### 3.1 What Makes This a Great Idea
1. **Eliminates High-Friction Redundancy:** Capturing 5 job applications or 10 bug investigations currently requires repeating the destination note route (`@job_2026_apply_29`), block-ID sigils, and standard sub-bullet structure (`- **URL**:`, `- **Role**:`, `- **Notes**:`) on every item.
2. **Leverages Staged Batch Architecture:** Bob’s batch planner (`CaptureBatchPlanner`) is already built to stage and validate multiple items in memory before committing. Expanding a template into multiple items fits cleanly into this existing model.
3. **Instant Visual Verification:** In Bob Mac Capture, live preview cards will show each expanded task in real time, giving immediate confidence that parameters were correctly mapped.

### 3.2 Critical Flaws in the Naive Proposal

#### Flaw 1: The Implicit Detection Trap (False Positives & Ambiguity)
If the parser implicitly treats the first item as a template simply because it contains `{0}`, serious failure modes arise:
- **Code Snippets & Technical Tasks:** Capturing a task like:
  ```
  Fix String.format("{0} is invalid", key) in validator.rs
  ```
  If this is captured alone, does it fail with "missing data rows"? Or does it capture literally?
- **Multi-Item Collisions:** If Bryan captures two independent tasks:
  ```
  Check regex bounds [a-z]{0,3} in parser

  Review PR #142 @code
  ```
  An implicit parser would misinterpret Item 1 as a template with placeholder `{0`, and consume Item 2 as arguments (`{0} = "Review"`), destroying Task 2!
- **Grammar Inconsistency:** Bob CLI uses explicit lexical sigils for all special modes: `@` for routes, `@@` for global declarations, `s:` for schedules, `p:` for priorities, `%` for clipboards, `=` for pomodoros. Relying on implicit braces violates Bob's deterministic parsing principles.

#### Flaw 2: The Whitespace Tokenization Failure (The Multi-Word Entity Problem)
In the toy example:
`Foobar foo http://foobar.com/career/some_foo_job`
Each argument is a single word. But real-world data looks like:
`Goldman Sachs | gs | https://goldmansachs.tal.net/vx/candidate/apply/1234`
Or:
`Staff Infrastructure Engineer | remote | https://...`
If arguments are split solely on whitespace:
- `Goldman` becomes `{0}`.
- `Sachs` becomes `{1}` (the block-ID!).
- `gs` becomes `{2}` (the URL!).
- The actual URL becomes `{3}` (lost/ignored).
The task is corrupted into `Apply to Goldman! @job_2026_apply_29:Sachs` with `- **URL**: gs`.

Requiring shell quoting (`"Goldman Sachs" gs http://...`) in a rapid-capture HUD is awkward and slows down fast entry.

#### Flaw 3: Row Separation Ergonomics (Table Pasting vs Blank Lines)
In standard Bob capture, items are delimited by blank lines (`\n\n`).
If template bulk capture requires an empty blank line between every single row:
```
Apply to {0}! @job:{1}

Row 1

Row 2

Row 3
```
Pasting 15 rows from Google Sheets, Excel, Airtable, or a browser table produces consecutive newlines without blank lines:
```
Row 1
Row 2
Row 3
```
If the user must manually navigate and hit Return twice between every row, the speed benefit of bulk capture is largely destroyed.

#### Flaw 4: Missing Escaping Semantics
Without an escape mechanism, it is impossible to write literal `{0}` or `{}` in a template-enabled capture. Standard formatting conventions require `{{` and `}}` to produce literal `{` and `}`.

#### Flaw 5: Ambiguous Interaction with Special Markers
- **Clipboard (`%`):** What if a template includes `- **Details**: %`? Does each row consume the same live clipboard, or pop successive history items (`%1`, `%2`)? (Answer: `%` should be forbidden inside templates).
- **Pomodoro Session Operators (`=x`, `+5`, `=3`):** Templates must not be session operators.
- **Item-Specific Bullets:** What if Row 1 has a unique note (`- Recruiter: Jane Doe`) that Row 2 does not have? The naive model provides no way to attach item-specific sub-bullets to an instantiated row.

---

## 4. Syntax Design Options and Trade-Off Analysis

### 4.1 Activation: Explicit Declaration vs Implicit

| Option | Syntax Example | Pros | Cons | Verdict |
|---|---|---|---|---|
| **A. Implicit First-Item** | `Apply to {0}!... \n\n Arg0 Arg1` | Zero extra characters | False positives on code/regex; ambiguous single items | **Rejected** |
| **B. Explicit Declaration (Recommended)** | `@@template\nApply to {0}!...` or `@@tmpl` | 100% deterministic; zero false positives; matches `@@route` | Requires typing `@@template` or `@@tmpl` | **Recommended** |
| **C. Item-Level Prefix** | `@@ Apply to {0}!...` | Short prefix | Less discoverable than `@@template` | Secondary alternative |
| **D. CLI Flag Only** | `bob capture --template "..."` | Keeps draft clean | Incompatible with Mac capture HUD | **Rejected** |

**Recommendation:** Use `@@template` (with short alias `@@tmpl`) as a draft-level declaration. It can appear on its own line before the template item, or inline at the start of the template item (`@@template Apply to {0}! ...`).

### 4.2 Placeholder Grammar: Numbered vs Sequential vs Named

| Grammar | Syntax | Behavior | Re-use & Re-order | Ergonomics |
|---|---|---|---|---|
| **Numbered (Recommended)** | `{0}`, `{1}`, `{2}` | 0-indexed positional lookup | Yes (can repeat `{0}`) | Very good |
| **Sequential (Recommended)** | `{}` | Auto-increments from 0 | No (strict sequential) | Fastest to type |
| **Named** | `{company}`, `{url}` | Requires schema mapping header | Yes | Slow (requires header) |
| **Shell-style** | `$1`, `$2` | Positional lookup | Yes | High conflict with `$100` prices |

**Recommendation:** Support both **Numbered `{N}`** and **Sequential `{}`** (mutually exclusive within a single template to avoid index confusion). Numbered placeholders allow repeating a field (e.g. `Apply to {0}! @job:{1} \n - Company: {0}`), while sequential `{}` allows lightning-fast typing when fields are in order. Escaping uses `{{` and `}}`.

### 4.3 Argument Delimitation Precedence

To solve the multi-word entity problem while supporting pasted tables and quick typing, we propose an automatic **3-tier delimiter resolution strategy per row**:

1. **Tier 1 — Tab Delimited (`\t`):**
   - **Trigger:** Line contains at least one tab character (`\t`).
   - **Use Case:** Pasting rows directly from Google Sheets, Excel, Notion, Airtable, or HTML tables.
   - **Behavior:** Splits on `\t`. Trims outer whitespace per cell. Spaces inside cells are preserved.
2. **Tier 2 — Pipe Delimited (`|`):**
   - **Trigger:** Line contains at least one pipe character (`|`).
   - **Use Case:** Human typing multi-word arguments without cumbersome quote marks.
   - **Behavior:** Splits on `|`. Trims leading/trailing whitespace around each cell. Literal pipes can be escaped with `\|`.
   - **Example:** `Goldman Sachs | gs | https://...` -> `["Goldman Sachs", "gs", "https://..."]`.
3. **Tier 3 — Shell Words (Whitespace + Quotes):**
   - **Trigger:** Line contains neither tabs nor pipes.
   - **Use Case:** Quick single-word arguments or quoted phrases.
   - **Behavior:** Splits on whitespace, respecting `"..."` and `'...'` quotes (using standard `shlex` semantics).
   - **Example:** `Foobar foo http://...` -> `["Foobar", "foo", "http://..."]`.

### 4.4 Row Separation and Custom Sub-Bullets

To support both dense tabular pastes and rich multi-bullet records:
1. **Dense Tabular Rows:** In the data block following the template, consecutive lines that do not start with a Markdown list marker (`-`, `*`, `+`) are each treated as an individual data row. Blank lines between rows are optional.
2. **Per-Item Custom Sub-Bullets:** If a data row is followed by child lines indented with `- `, `* `, or `+ `, those child lines are appended to the instantiated task *after* the template's child lines!

Example:
```markdown
@@template
Apply to {0}! @job_2026_apply_29:{1}
- **URL**: {2}

Acme Corp | acme | http://acme.com
- **Recruiter**: Jane Doe
- **Status**: First round scheduled

WidgetCo | widget | http://widget.co
```
This produces:
- Task 1: `Apply to Acme Corp! @job_2026_apply_29:acme` with three sub-bullets (`URL`, `Recruiter`, `Status`).
- Task 2: `Apply to WidgetCo! @job_2026_apply_29:widget` with one sub-bullet (`URL`).

---

## 5. Detailed Specification of the Recommended Solution

### 5.1 Grammar Rules
1. **Declaration:** The draft contains `@@template` or `@@tmpl` either on its own line or at the beginning of the first item.
2. **Template Item:** The item immediately following the `@@template` declaration (or containing it) is the Template Item.
   - It contains a parent line and optional template sub-bullets.
   - It may contain `{N}` or `{}` placeholders on the parent line and/or on child bullet lines.
   - It must not contain clipboard markers (`%`) or Pomodoro session operators (`=x`, `=3`, `+5`).
3. **Data Rows:** All subsequent items or non-bullet lines in the draft are Data Rows.
   - A draft with `@@template` but zero data rows reports a `TemplateWithoutDataRows` error diagnostic.
   - Each data row is split into arguments using the Tab -> Pipe -> Shellword precedence.
   - Each data row must supply at least as many arguments as the maximum placeholder index in the template. Providing fewer arguments reports a `MissingTemplateArguments` diagnostic with the line's exact range.
   - Providing extra arguments is tolerated (with an informational diagnostic).
4. **Instantiating Tasks:**
   - Each data row produces one concrete `CaptureItem`.
   - Placeholders in the template's parent line and sub-bullets are replaced by the row's arguments.
   - Escaped `{{` and `}}` are converted to `{` and `}`.
   - Any child bullets authored directly under the data row are appended to the template's child bullets.
   - The instantiated items are then parsed, planned, and validated through Bob's standard capture pipeline.

### 5.2 Diagnostic Codes and Spans (`capture-parse`)
New diagnostic codes emitted in `CaptureParseResult`:
- `template_without_data_rows`: `@@template` defined, but no data inputs provided.
- `missing_template_arguments`: Row supplied $M$ arguments, but template requires $N$ ($M < N$). Range points to the offending data row.
- `mixed_placeholder_syntax`: Template mixes numbered `{0}` and unnumbered `{}` placeholders.
- `invalid_placeholder`: Malformed placeholder syntax (e.g. `{abc}` or negative index).
- `forbidden_template_marker`: Template contains forbidden markers like `%` or session operators.

New semantic `SpanKind`s emitted for syntax highlighting:
- `template_marker`: Spans `@@template` or `@@tmpl`.
- `template_placeholder`: Spans `{0}`, `{1}`, `{}`.
- `template_delimiter`: Spans `|` or `\t` delimiters in data rows.
- `template_arg`: Spans individual parsed arguments in data rows.

### 5.3 Execution and Preview Flow
```
User Draft
    │
    ▼
split_capture_draft (draft.rs)
    │  - Extracts @@template declaration
    │  - Identifies Template Item
    │  - Parses Data Rows (TSV / Pipe / Shellwords)
    ▼
expand_template_draft (new)
    │  - Substitutes parameters into parent & child lines
    │  - Appends row-specific sub-bullets
    │  - Maps source ranges for diagnostics & spans
    ▼
Vec<CaptureItem> (Concrete expanded items)
    │
    ├──► capture-parse: Emits spans, diagnostics, and item summaries
    │
    ├──► capture --dry-run: Staged planning -> returns `captures` array
    │                       (Bob Mac Capture renders preview cards)
    │
    └──► capture: Atomic commit to vault files
```

---

## 6. End-to-End Walkthrough of Example Scenarios

### Scenario 1: The User's Job Application Example (Clean Whitespace)
**Input:**
```markdown
@@template
Apply to {0}! @job_2026_apply_29:{1}
- **URL**: {2}

Foobar foo http://foobar.com/career/some_foo_job

Bazbuz baz http://bazbuz.com/career/some_baz_job
```
**Parser Behavior:**
- `@@template` detected. Template item has 3 arguments: `{0}`, `{1}`, `{2}`.
- Rows contain no tabs or pipes; shellword splitting extracts 3 arguments per row.
- Live preview renders 2 cards:
  - Card 1: `Apply to Foobar!` routed to `job_2026_apply_29.md#^foo` with child bullet `- **URL**: http://foobar.com/...`.
  - Card 2: `Apply to Bazbuz!` routed to `job_2026_apply_29.md#^baz` with child bullet `- **URL**: http://bazbuz.com/...`.

### Scenario 2: Multi-Word Entities with Pipe Syntax
**Input:**
```markdown
@@template
Apply to {0}! @jobs:{1}
- **Role**: {2}
- **URL**: {3}

Goldman Sachs | gs | Senior Quant Researcher | https://gs.com/apply
Jane Street | js | Systems Engineer (Linux) | https://janestreet.com/apply
```
**Parser Behavior:**
- Rows contain `|`; pipe parser cleanly preserves spaces in `Goldman Sachs` and `Systems Engineer (Linux)`.
- No quotes needed.
- Consecutive rows are processed without requiring blank lines.

### Scenario 3: Pasting a Table Directly from Google Sheets / Excel
**Input (pasted with Cmd+V):**
```markdown
@@template
Buy {0} @shopping
- **Quantity**: {1}
- **Store**: {2}

Apples	3 lbs	Trader Joe's
Oat Milk	2 cartons	Safeway
Coffee Beans	1 bag	Local Roaster
```
**Parser Behavior:**
- Rows contain `\t`; tab parser immediately extracts fields.
- 3 tasks are created in `shopping.md` with structured sub-bullets.

### Scenario 4: Error Handling in Mac Capture HUD
**Input:**
```markdown
@@template
Apply to {0}! @jobs:{1}
- **URL**: {2}

Google | goog | https://google.com/jobs
Stripe | strp
```
**Parser Behavior:**
- Row 2 provides only 2 arguments, but template references `{2}`.
- `bob capture-parse` returns:
  ```json
  {
    "ok": false,
    "diagnostics": [
      {
        "code": "missing_template_arguments",
        "severity": "error",
        "message": "row provides 2 arguments, but template requires at least 3 ({0}..{2})",
        "range": [95, 108]
      }
    ]
  }
  ```
- Bob Mac Capture draws an inline red warning underline under `Stripe | strp` in the text view and disables the Submit button until fixed.

---

## 7. Implementation Plan and File Touchpoints

### Phase 1: `bob-cli` Core Grammar & Expansion
- **`src/native/capture_language/draft.rs`:**
  - Update `split_capture_draft` to recognize `@@template` / `@@tmpl` declarations.
  - Implement `parse_template_data_rows` with the 3-tier delimiter tokenizer (`\t`, `|`, `shlex`).
  - Implement template parameter substitution with `{{` / `}}` escaping and sequential `{}` support.
  - Preserve byte-range sourcemaps from original draft lines to expanded items.
- **`src/native/capture_language/editor_model.rs`:**
  - Add `SpanKind::TemplateMarker`, `SpanKind::TemplatePlaceholder`, `SpanKind::TemplateDelimiter`, `SpanKind::TemplateArg`.
  - Add diagnostic codes (`missing_template_arguments`, `template_without_data_rows`, etc.).
- **`src/native/capture_language/editor_parse.rs` & `src/native/capture_parse.rs`:**
  - Wire spans and diagnostics into the editor parse response.
- **`src/native/capture/plan.rs`:**
  - Pass the expanded `CaptureDraft` into `plan_capture_batch`. Batch execution and dry-run automatically handle the resulting items.

### Phase 2: `bob-mac-capture` Additive Presentation
- **`Sources/CaptureCore/CaptureModels.swift`:**
  - Add `templateMarker`, `templatePlaceholder`, `templateDelimiter`, `templateArg` cases to `CaptureSpanKind` decoding.
- **`Sources/BobMacCapture/CaptureTextView.swift` (or syntax theme):**
  - Map `templatePlaceholder` to an accent highlight color (e.g. orange / teal) and `templateMarker` to keyword purple.
- **Preview UI:**
  - No changes needed! `CapturePanelView.swift` already iterates over `success.normalizedCaptures` and renders separate preview cards with divider bars.

---

## 8. Final Verdict and Recommendations

1. **Adopt the Feature with Explicit Declarations (`@@template`):** Do not implement implicit `{0}` detection; explicit `@@template` or `@@tmpl` eliminates all false positives and aligns with existing Bob design principles.
2. **Implement Multi-Tier Delimiters (`\t` > `|` > whitespace):** Support pipe-delimited fields for typed input and tab-delimited fields for clipboard table pastes. This completely solves the multi-word entity problem.
3. **Allow Dense Consecutive Rows:** Do not force blank lines between single-line data entries.
4. **Preserve Sub-Bullet Composability:** Allow data rows to append their own custom child bullets to the template's child bullets.
5. **Leverage the Thin-Client Architecture:** Implement the entire expansion and validation logic in `bob-cli`; Bob Mac Capture will automatically display the expanded previews via its existing dry-run rendering pipeline.

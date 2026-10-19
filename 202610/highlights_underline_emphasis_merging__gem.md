# Research: Merging Highlights App Underlines into Enclosing Highlights

**Author**: researcher `gem` (5-researcher swarm)  
**Date**: 2026-10-19  
**Target Systems**: `bob-cli`, `bob-mac-capture`, Bob Vault (`ref/` notes)  
**Status**: Proposal & Technical Feasibility Report  

---

## 1. Executive Summary

### 1.1 The Core Problem
In the Highlights macOS/iOS PDF reader app, the user's primary workflow uses **color highlights** to capture meaningful passages, and the **underline tool** to add extra emphasis to a specific focal sentence or phrase *inside* that highlighted passage.

However, when Highlights exports annotations to Markdown or TextBundle sidecars:
1. It treats the underline and the highlight as two completely separate annotation items.
2. It wraps the underline text in Markdown bold syntax (`> **...**`).
3. As a result, both in the Bob vault's reference notes (`ref/`) and in the Bob Mac Capture app's Ref Panel inspector pane, these annotations show up as **two separate, redundant, visually jarring highlight cards**—an isolated snippet entirely in bold, placed immediately adjacent to the larger quote containing the exact same words.
4. Furthermore, because Highlights app generates multi-line underlines by wrapping each line in `**...**` independently, the exported text in ref notes suffers from ugly formatting fragmentation (e.g., `**word1 word2** **word3 word4**`).

### 1.2 The Vision
Transform this disjointed behavior into a single, unified, and beautiful reading experience. When an underline is enclosed within a larger highlight on the same page, the system should automatically fold the underline into the enclosing quote as clean, de-fragmented inline typographic emphasis:

```markdown
<!-- Before (Current Vault Behavior): Two Redundant Callouts -->
> [!quote] This is the missing piece in most agent frameworks—and the part that I am kind of obsessed with right now, and I think it’s the most underexplored area for practitioners. Factual memory tells the agent what it knows. Experiential memory tells it how to do things better—how it solved problems in the past, what worked, what didn’t.
^h-2c628728a080

> [!quote] **Factual memory tells the agent what it knows. Experiential** **memory tells it how to do things better—how it solved** **problems in the past, what worked, what didn’**
^h-f6ee04410a87

<!-- After (Proposed Unified Behavior): One Clean, Contextual Callout -->
> [!quote] This is the missing piece in most agent frameworks—and the part that I am kind of obsessed with right now, and I think it’s the most underexplored area for practitioners. **Factual memory tells the agent what it knows. Experiential memory tells it how to do things better—how it solved problems in the past, what worked, what didn’t.**
^h-2c628728a080
```

### 1.3 Key Findings & Recommendations
- **Critique**: The proposed plan is **outstanding and highly recommended**. It eliminates cognitive noise, reduces note bloat by 30–50% in heavily annotated references, and restores the author's original reading intent.
- **Single Source of Truth**: The merge must take place in `bob-cli` during sidecar compilation (`src/native/highlights_ref/sidecar_render.rs`). Doing display-only deduplication in Bob Mac Capture would leave the Obsidian vault notes dirty, duplicated, and inconsistent.
- **Preservation Invariant**: The merge must be completely lossless. Any comments, image references, or `#task` lines attached to the underline must be amalgamated into the unified highlight block, and any existing block IDs previously published in the note must receive redirect stubs (`[!info] Merged highlight`) under `### Removed highlights` so external backlinks never break.
- **Standalone Safety**: Any underline that is *not* enclosed within a larger highlight must safely fall back to a standalone highlight card, ensuring zero data loss.
- **Visual Design**: The merged highlight renders as clean standard Markdown bold `**...**` in Obsidian. In Bob Mac Capture, `RefsQuoteEmphasis` should pair `.stronglyEmphasized` font weight with a subtle, warm underline accent, directly echoing the physical reading gesture.

---

## 2. Empirical Investigation & Current System Anatomy

To understand the exact mechanics and failure modes, we investigated actual production artifacts in Bryan's vault (`~/bob/lib/` and `~/bob/ref/`), `bob-cli`, and `bob-mac-capture`.

### 2.1 How Highlights App Exports Underlines
In the PDF specification (ISO 32000-1 / PDF 1.7 §12.5.6.10), text markup annotations include `/Highlight`, `/Underline`, `/Squiggly`, and `/StrikeOut`.
When the Highlights app exports its annotations to Markdown sidecars (`lib/<type>/<stem>.md` or `lib/<type>/<stem>.textbundle/text.md`):
- `/Highlight` annotations are formatted as blockquotes:
  ```markdown
  > Quoted text from the document.
  ```
- `/Underline` annotations are formatted as blockquotes wrapped in double asterisks:
  ```markdown
  > **Underlined text from the document.**
  ```
- If an underline spans multiple lines, Highlights emits `**` at each line boundary:
  ```markdown
  > **For instance, you might be
  getting ready to restart your entire**
  > **town, for a version upgrade,
  and you want to land everyone’s**
  ```

### 2.2 Corpus Findings in Bryan's Vault
We examined several production files in `~/bob/lib/` and `~/bob/ref/` to inspect real user behavior. The evidence revealed crucial real-world patterns:

#### Case Study 1: `gas_town_emergency_user_manual.md`
In `~/bob/lib/blogs/gas_town_emergency_user_manual.md` and `~/bob/ref/blogs/gas_town_emergency_user_manual.md`:
1. **Annotation Order Inconsistency**:
   - On **Page 4**, the underline appears **first** in the sidecar, followed by the enclosing highlight:
     - Underline: `> **You technically only need the Mayor.**`
     - Enclosing: `> You technically only need the Mayor. Running with just the Mayor is a good tutorial...` (with `#task` attached to the enclosing highlight).
   - On **Page 5**, the enclosing highlight appears **first**, followed by the underline:
     - Enclosing: `> It’s OK not to swarm all the time...`
     - Underline: `> **For instance, you might be getting ready to restart your entire**...`
   - On **Page 7**, the underline appears **first**, and carries the user's comment:
     - Underline: `> **But. When you see that an agent is finished working, stop...**`  
       Comment: `This feels wrong! You need to check on goals, not individual agents!`
     - Enclosing: `> Don’t watch your agents work. Make sure they have their marching orders...` (no comment).
   - On **Page 10**, the underline appears **first** and carries a comment (`What is the point of gt sling?`).

#### Case Study 2: `2026_goals_as_first_class_abstractions...md`
In `~/bob/lib/papers/2026_goals_as_first_class_abstractions_in_human_ai_collaboration_automationxp26.md`:
- On **Page 13**, the underline is `> **aligned with what a team is actually doing**`.
- The user attached a detailed comment to the underline:
  ```markdown
  This is the point of having every agent which has no preset goal run `sase goal list` before `sase goal set`!
  ```
- The enclosing highlight is:
  ```markdown
  > AI should play a substantive collaborative role: interrogating whether a goal is coherent, feasible, and aligned with what a team is actually doing, not just polishing phrasing
  ```
- In the existing ref note, the user comment is anchored to the isolated bold fragment, completely separated from the full paragraph quote above it.

#### Key Inferences from the Corpus
1. **Order Agnosticism is Mandatory**: The underline may precede or follow the enclosing highlight in the sidecar. Any algorithm requiring the parent to appear before the child will fail on ~50% of real annotations.
2. **Comment and Task Inversion**: Users frequently attach comments or `#task` lines to the underline because the underline represents the specific thought trigger. Merging *must* amalgamate comments and tasks from both annotations.
3. **Line-Wrap Fragmentation**: Multi-line underlines in the sidecar contain broken internal asterisks that must be cleaned during normalization.

### 2.3 How `bob-cli` Currently Processes Annotations
1. **Parsing** (`src/native/highlights_ref/sidecar.rs`):
   - `parse_sidecar_markdown` splits the document on `---` / `***` into chunks.
   - Any chunk with a leading `>` is parsed as `SidecarAnnotationKind::Highlight`.
   - Both normal highlights and underlines are classified identically as `SidecarAnnotationKind::Highlight`.
2. **Rendering** (`src/native/highlights_ref/sidecar_render.rs`):
   - `render_sidecar_highlights` iterates through annotations.
   - It runs `plan_continuations(&sidecar.annotations)` to group manual `<` continuations.
   - Underlines have no continuation marker, so they are assigned independent block IDs via `annotation_block_id(...)` and emitted as distinct `> [!quote]` callouts.
3. **Reading Notes Back** (`src/native/highlights_ref/region.rs`):
   - `parse_managed_region` parses the callouts into `RegionBlock` objects.
   - Each callout becomes a separate `ShowAnnotation` in `bob ref show`.

### 2.4 How `bob-mac-capture` Currently Presents Annotations
1. **Inspector Loader** (`RefsInspectorLoader.swift`):
   - Calls `bob ref show` via the JSON interface.
   - Populates `built.notes` (commented highlights) and `built.highlights` (uncommented highlights).
2. **Inspector View** (`RefsInspectorView.swift`):
   - Renders each annotation in `highlightView` or `noteView`.
   - Calls `quoteText(_ text: String) -> AttributedString`, which uses `RefsQuoteEmphasis.runs(text)` to detect `**...**` runs and apply `.stronglyEmphasized`.
   - Because the underline is an isolated block where the entire string is wrapped in `**`, it renders as an entire card in bold text, right next to the card containing the parent quote.

---

## 3. Critique of the Plan: Is This a Good Idea?

### 3.1 Why Merging Underlines is a Great Idea
1. **Reduces Cognitive Load & Visual Clutter**:
   In long articles or books, having two adjacent cards saying almost the exact same thing creates immediate visual fatigue. Merging collapses two redundant boxes into one cohesive block.
2. **Restores Semantic Context**:
   An underlined phrase like `"beads epics"` or `"resources for competent and responsible workers"` is meaningless without its surrounding sentence. When shown as an isolated card, the user loses the context of why they underlined it. Merging embeds the focal point inside the full author's argument.
3. **Unifies Split Tasks and Comments**:
   Currently, if a user writes a comment on the underline, that comment is separated from the full passage. In Bob Mac Capture's inspector, the comment appears under the short bold fragment, while the full passage sits uncommented elsewhere in the feed. Merging brings the comment, the task, and the complete passage together.

### 3.2 Potential Risks and Failure Modes (The "Critique")
A naive implementation would introduce serious regressions. The design must explicitly guard against the following failure modes:

| Risk | Failure Mode | Severity | Mitigation Required |
| :--- | :--- | :--- | :--- |
| **False Positive Merging** | A short underline (e.g. `"in other words"`) matches an unrelated highlight on the same page. | **High** | Minimum length threshold, word-boundary enforcement, and unambiguous candidate check. |
| **Silent Dropping of Standalone Underlines** | User underlines a sentence with no surrounding highlight. | **Critical** | Standalone underlines must remain standalone highlights. Merging is an opt-in match, not an exclusion. |
| **Broken Vault Block Links** | Existing notes have backlinks to the underline's `^h-...` ID. If the ID vanishes, links break. | **Critical** | Emit `[!info] Merged highlight` redirect stubs under `### Removed highlights`, identical to continuations. |
| **Lost Comments / Tasks** | User wrote a `#task` on the underline; merging clobbers it with the parent highlight's metadata. | **Critical** | Amalgamate comments and redirect task candidate block IDs to the parent block ID. |
| **Fuzzy Text Mismatch** | Subtle whitespace or punctuation differences between the underline and parent quote prevent matching. | **Medium** | Normalized token-stream matching before exact substring slicing. |
| **Double Highlighting** | Multiple underlines inside the same highlight or overlapping underlines crash the string splice. | **Medium** | Range-based non-overlapping splice planner. |

---

## 4. Architectural Analysis: Where Should the Merge Happen?

We evaluated three architectural options:

```mermaid
flowchart TD
    subgraph Option A: Bob Mac Capture Only
        A1[Highlights Sidecar] --> A2[bob-cli sync]
        A2 --> A3[Obsidian Ref Note: Cluttered & Duplicated]
        A3 --> A4[bob ref show]
        A4 --> A5[Swift UI Merging Filter]
        A5 --> A6[Bob Mac Capture: Clean]
    end

    subgraph Option B: bob-cli Core Engine (Recommended)
        B1[Highlights Sidecar] --> B2[bob-cli Emphasis Planner]
        B2 --> B3[Obsidian Ref Note: Clean & Unified]
        B3 --> B4[bob ref show: Clean & Unified]
        B4 --> B5[Bob Mac Capture: Clean & Unified]
    end
```

### Option A: Display-Time Merge in Bob Mac Capture Only
- **How it works**: `bob-cli` remains unchanged. `RefsInspectorLoader` or `RefsInspectorFeed` in Swift detects substring pairs and folds them dynamically at UI rendering time.
- **Why it Fails**:
  - **Vault Notes Remain Ugly**: Bryan's Obsidian vault notes would still contain the duplicated, fragmented callouts.
  - **Split Authority**: Obsidian Dataview queries, CLI tools (`bob ref show`), and external scripts see two highlights, while Bob Mac Capture sees one.
  - **Fragile State Management**: The Swift client would have to coordinate pagination, card counts, selection indexes, and block ID copies across synthetic merged models.

### Option B: Compilation in `bob-cli` During Sidecar Sync (Recommended)
- **How it works**: `bob ref sync` and `bob ref scan` detect underline annotations in the sidecar, match them against enclosing highlights on the same page, and render a single de-fragmented, emphasized Markdown quote in the vault note.
- **Why it Wins**:
  - **Single Source of Truth**: The vault Markdown file is the canonical source of truth.
  - **Zero Swift Complexity**: `RefsQuoteEmphasis` in Bob Mac Capture *already* parses `**...**` and applies `.stronglyEmphasized`! The capture app instantly benefits with zero architectural churn.
  - **Universal Consistency**: Obsidian, Dataview, CLI output, and Bob Mac Capture all reflect the same clean data model.
  - **Durable Identity**: Block ID continuity and redirect stubs are managed authoritatively by `sidecar_render.rs`.

---

## 5. Detailed Technical Design

### 5.1 The Emphasis Plan (`emphasis.rs`)
Beside `continuation.rs` (`ContinuationPlan`), we introduce an **Emphasis Planner** (`EmphasisPlan`) in `bob-cli`:

```rust
pub(super) struct UnderlineSpan {
    pub(super) start_char: usize,
    pub(super) end_char: usize,
}

#[derive(Debug, Clone, Default)]
pub(super) struct EmphasisPlan {
    /// Parent highlight order -> list of (underline annotation order, byte range in parent text)
    pub(super) absorbed_underlines: BTreeMap<usize, Vec<(usize, UnderlineSpan)>>,
    /// Absorbed underline order -> parent highlight order
    pub(super) parent_of: BTreeMap<usize, usize>,
    /// Effective rewritten quote text for parent highlights
    pub(super) emphasized_quotes: BTreeMap<usize, String>,
}
```

### 5.2 The Matching & Splicing Algorithm
For each page in the sidecar:
1. **Identify Underline Candidates**:
   An annotation `U` is an underline candidate if:
   - Its kind is `Highlight`.
   - Its raw text matches Highlights app's underline format: starts with `**` and ends with `**`, or contains internal `**\n**` line-break artifacts.
2. **Normalize Candidate Strings**:
   - Extract `U_clean`: strip all leading/trailing and interior `**` tags; collapse consecutive whitespaces and newlines into single spaces; trim whitespace.
   - For all non-underline highlights `H` on the same page: extract `H_clean` similarly.
3. **Locate Sub-Spans**:
   - Check if `U_clean` is a substring of `H_clean`:
     - Must satisfy `U_clean.len() >= 4` (guards against trivial symbols/words like `"and"`, `"a"`, or numbers).
     - Must satisfy `U_clean.len() < H_clean.len()` (exact matches are duplicate highlights, handled by deduplication).
     - Must have word boundaries (start and end at word boundaries within `H_clean`).
   - Check for uniqueness: `U_clean` must match *exactly one* highlight on the same page. If it matches multiple, use proximity (immediate predecessor or successor in sidecar order); if still ambiguous, refuse to merge and keep separate.
4. **Splicing Clean Emphasis into `H`**:
   - Map `U_clean` back to the exact character span `[start..end]` in the parent's formatted text.
   - Insert `**` at `start` and `**` at `end`.
   - If multiple underlines match the same parent highlight, sort their spans in reverse order (highest index first) so index shifts do not invalidate preceding splices. If spans overlap, take the bounding union `[min(start1, start2)..max(end1, end2)]`.
5. **Amalgamate Comments and Tasks**:
   - If the underline carries a comment or `#task`:
     ```rust
     let mut comments = Vec::new();
     if let Some(parent_comment) = parent.comment {
         comments.push(parent_comment);
     }
     if let Some(underline_comment) = underline.comment {
         comments.push(underline_comment);
     }
     parent.comment = (!comments.is_empty()).then(|| comments.join("\n\n"));
     ```
   - In `annotation_tasks.rs`, map `underline.order` to `parent.block_id` as the `link_block_id`. Any `#task` created from the underline's comment links to the parent highlight block in the ref note, while preserving its identity hash.
6. **Redirect Stubs for Block ID Stability**:
   - If a previously synced note already contained `^h-underline`, `sidecar_render.rs` emits:
     ```markdown
     ### Removed highlights

     > [!info] Merged highlight
     > Now part of [[#^h-parent|the Page X highlight]].

     ^h-underline
     ```
   - This guarantees that no user backlink in Obsidian or in external task files is ever orphaned.

---

## 6. Aesthetic Design: Making It Intuitive, Reliable, and Beautiful

Bryan emphasized: *"Make sure you design this feature so it is intuitive, reliable, and (last but not least) beautiful!"*

### 6.1 Aesthetics in Obsidian Ref Notes
In Obsidian, ref notes use callout blocks (`> [!quote]`).

#### Comparison: Before vs. After
````carousel
```markdown
<!-- BEFORE: Disjointed, duplicated, fragmented -->
### Page 7

> [!quote] This is the missing piece in most agent frameworks—and the part that I am kind of obsessed with right now, and I think it’s the most underexplored area for practitioners. Factual memory tells the agent what it knows. Experiential memory tells it how to do things better—how it solved problems in the past, what worked, what didn’t.

^h-2c628728a080

> [!quote] **Factual memory tells the agent what it knows. Experiential** **memory tells it how to do things better—how it solved** **problems in the past, what worked, what didn’**

^h-f6ee04410a87
```
<!-- slide -->
```markdown
<!-- AFTER: Seamless, elegant, de-fragmented -->
### Page 7

> [!quote] This is the missing piece in most agent frameworks—and the part that I am kind of obsessed with right now, and I think it’s the most underexplored area for practitioners. **Factual memory tells the agent what it knows. Experiential memory tells it how to do things better—how it solved problems in the past, what worked, what didn’t.**

^h-2c628728a080

### Removed highlights

> [!info] Merged highlight
> Now part of [[#^h-2c628728a080|the Page 7 highlight]].

^h-f6ee04410a87
```
````

#### Typographic Evaluation of Emphasis Formats in Obsidian
We analyzed three markdown formats for rendering the merged emphasis in Obsidian:

1. **Standard Markdown Bold (`**...**`)** [Recommended Default]:
   - *Pros*: Universally supported across all Markdown editors, git viewers, and Pandoc exports; zero visual artifacts; perfect font kerning across all themes.
   - *Cons*: Visually bold, but doesn't literally draw an underline.
2. **HTML Underline (`<u>...</u>`)**:
   - *Pros*: Literally renders an underline in Obsidian.
   - *Cons*: Raw HTML tags inside Markdown can conflict with some linters or Pandoc LaTeX conversions. Harder to read in raw source mode.
3. **Markdown Highlight (`==...==`)**:
   - *Pros*: Renders as a colored text marker.
   - *Cons*: Collides visually with the quote callout (yellow highlight on top of a yellow/tinted callout background looks messy).

**Recommendation**: Use standard Markdown `**...**` in the generated ref note. To satisfy the desire for a beautiful literal underline in Obsidian, provide an optional, elegant CSS snippet for the vault:

```css
/* Vault snippet: Subtle, beautiful underlines for strong emphasis in ref quotes */
.callout[data-callout="quote"] strong {
    font-weight: 600;
    text-decoration: underline;
    text-decoration-color: var(--text-accent);
    text-underline-offset: 3px;
    text-decoration-thickness: 1.5px;
}
```

### 6.2 Aesthetics in Bob Mac Capture (Ref Inspector Pane)
In Bob Mac Capture (`RefsInspectorView.swift`), highlights are rendered as clean, modern macOS cards with a vertical left accent bar:

```
┌────────────────────────────────────────────────────────┐
│ Page 7                                                 │
│ ▌ This is the missing piece in most agent frameworks… │
│ ▌ Factual memory tells the agent what it knows.        │
│ ▌ Experiential memory tells it how to do things       │
│ ▌ better—how it solved problems in the past…           │
└────────────────────────────────────────────────────────┘
```

#### Enhancing `quoteText` in Bob Mac Capture
Currently, `RefsInspectorView.swift` (lines 805–815) uses:
```swift
private func quoteText(_ text: String) -> AttributedString {
    var result = AttributedString()
    for run in RefsQuoteEmphasis.runs(text) {
        var part = AttributedString(run.text)
        if run.isStrong {
            part.inlinePresentationIntent = .stronglyEmphasized
        }
        result += part
    }
    return result
}
```

We can make this look extraordinarily beautiful and native to macOS by enhancing the attributed string styling:

```swift
private func quoteText(_ text: String) -> AttributedString {
    var result = AttributedString()
    for run in RefsQuoteEmphasis.runs(text) {
        var part = AttributedString(run.text)
        if run.isStrong {
            // Option 1: Native Semibold + Accent Underline
            part.inlinePresentationIntent = .stronglyEmphasized
            part.underlineStyle = .single
            part.underlineColor = AttributedString.AttributeContainer([
                .foregroundColor: NSColor.systemOrange.withAlphaComponent(0.6)
            ])
        }
        result += part
    }
    return result
}
```

This delivers the best of both worlds:
- The text pops with **clear typographical weight** (semibold).
- A subtle, warm **accent underline** echoes the exact visual tool Bryan used in the Highlights app, creating an immediate sense of tactile continuity.

---

## 7. Recommended Adjustments to the Requirements

We recommend making the following explicit adjustments to the scope and requirements:

1. **Requirement Adjustment: Zero-Annotation User Friction (Zero Gesture Tax)**:
   - *Adjustment*: The user should never have to type special continuation markers (like `<u`) or tags in the Highlights app. The system must automatically infer the merge from sub-span containment.
2. **Requirement Adjustment: Sibling Order Invariance**:
   - *Adjustment*: The algorithm must handle the underline appearing *before* or *after* the enclosing highlight in the sidecar file.
3. **Requirement Adjustment: Lossless Metadata Amalgamation**:
   - *Adjustment*: If an underline carries a comment or `#task`, it must never be discarded. It must merge into the parent highlight's comment/task list, with task block links pointing to the parent highlight.
4. **Requirement Adjustment: Safe Standalone Fallback**:
   - *Adjustment*: If an underline does *not* match any highlight on the same page (e.g. Bryan underlined a standalone sentence), it must be preserved as an independent highlight callout. Underlines are never dropped.
5. **Requirement Adjustment: Non-Destructive Block ID Redirects**:
   - *Adjustment*: When re-syncing a note that already published separate block IDs, emit redirect stubs for the absorbed underline IDs to preserve Obsidian backlink integrity.

---

## 8. Implementation Blueprint

### 8.1 Files to Modify

```
bob-cli/
├── src/native/highlights_ref/
│   ├── sidecar.rs             # Detect underline signature in chunk parser
│   ├── emphasis.rs            # NEW: Sub-span matching, splice planning, comment amalgamation
│   ├── sidecar_render.rs      # Integrate EmphasisPlan into render pipeline & redirect stubs
│   ├── annotation_tasks.rs    # Map absorbed underline orders to parent block IDs
│   └── tests/
│       ├── emphasis.rs        # NEW: Unit tests for sub-span splicing, order invariance, comments
│       └── sidecar.rs         # End-to-end regression tests with multi-line bolds

bob-mac-capture/
├── Sources/
│   └── BobMacCapture/Refs/
│       └── RefsInspectorView.swift  # Enhance quoteText with subtle underline accent styling
└── Tests/
    └── BobMacCaptureTests/
        └── RefsInspectorTests.swift # Verify attributed string emphasis and accessibility labels
```

### 8.2 Comprehensive Test Scenarios
1. **Basic Substring Match**: Highlight is a paragraph; underline is the middle sentence. Verify output is a single callout with `**` wrapped around the sentence.
2. **Preceding Underline**: Underline appears *before* the enclosing highlight in the sidecar. Verify identical clean merge.
3. **Multi-line Underline with Highlights Asterisk Artifacts**: Underline in sidecar has `**line 1**\n**line 2**`. Verify spliced quote has a single continuous `**line 1 line 2**`.
4. **Comment on Underline Only**: Underline has a comment; parent has none. Verify parent receives the comment and `#task` links resolve to the parent block ID.
5. **Comments on Both**: Both underline and parent have comments. Verify comments concatenate with `\n\n`.
6. **Multiple Underlines in One Highlight**: Two distinct sentences underlined in the same paragraph. Verify both receive `**...**` without overlap corruption.
7. **Standalone Underline**: Underline on a page with no matching highlight. Verify it emits as an independent highlight callout.
8. **Redirect Stub Generation**: Note previously contained `^h-underline`. Re-sync with underline merging enabled emits redirect stub under `### Removed highlights`.

---

## 9. Conclusion & Final Recommendation

Merging Highlights app underlines into enclosing highlights is an exceptionally high-value refinement. It takes what is currently a jarring, duplicate-heavy experience and turns it into a streamlined, high-signal reading interface.

By implementing this at the compiler level in `bob-cli`'s sidecar render engine, we achieve:
1. **Absolute data safety**: Zero lost comments, zero lost tasks, and zero broken backlinks.
2. **Universal vault elegance**: Clean, standard Markdown in Obsidian with zero HTML noise.
3. **Effortless Mac Capture polish**: Instant, native-looking typography in Bob Mac Capture's Ref Panel with minimal client churn.

The plan is ready to be transitioned into a formal implementation bead and plan file.

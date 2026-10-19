# Designing Cross-Page & Discontinuous Highlight Merging for `bob ref`

**Author:** Researcher gem (`research.4u.gem`)  
**Date:** 2026-10-19  
**Status:** Completed  
**Domain:** `bob-cli` reference library (`bob ref`), Highlights app synchronization, PDF annotation modeling  

---

## 1. Executive Summary

When reading PDF reference notes in the Highlights app on macOS or iPadOS, readers frequently encounter passages that cross page boundaries or contain discontinuous excerpts within a single paragraph. Because PDF viewers and PDF annotation specifications (ISO 32000) bind text highlight annotations strictly to individual page coordinate spaces, users are forced to create multiple fragmented highlights. 

Bryan proposes enabling the `bob ref` command to automatically merge a highlight (and its associated notes) into the immediately preceding highlight in the reference note whenever the highlight's note begins with a `<` character (optionally followed by a space and note text), as exemplified in screenshot `~/tmp/screenshots/20261019_063505.png` from Steve Yegge's *Gas Town Emergency User Manual*.

### Key Findings & Verdict
1. **The Plan is Fundamentally Sound and Elegant:** Leveraging the existing annotation note metadata channel with a `<` sigil introduces zero external dependencies, requires no modifications to the proprietary Highlights application, and provides an effortless single-keystroke gesture on both iPadOS and macOS touch/keyboard interfaces.
2. **Scope of Problem:** Inspection of real vault sidecars (`~/bob/lib/blogs/gas_town_emergency_user_manual.md`) confirms that cross-page splits currently produce severed sentences, broken callouts under separate page headers, and fragmented task linkages in Obsidian.
3. **Necessary Refinements to the Core Requirements:**
   - **Escape Syntax (`\<`):** To avoid false positives on legitimate comments (e.g., `< 10ms latency`, `<vector>`, `<html>`), an escape hatch `\<` must be supported to emit a literal leading `<` without triggering a merge.
   - **Discontinuous Excerpt Syntax (`<...` / `< …`):** For intra-paragraph non-contiguous excerpts, adding `<...` allows automatic insertion of an ellipsis ` […] ` between merged text fragments, distinguishing continuous text joins from elided excerpts.
   - **Comment Joining Semantics:** When both the predecessor and continuation highlights contain comments, they must be concatenated with paragraph breaks (`\n\n`) to prevent data loss.
   - **Predecessor Validation & Safe Fallback:** A continuation highlight must only merge into a valid predecessor `Highlight`. If preceded by an image, standalone note, or document start, the merger must fail gracefully with a diagnostic warning, preserving the highlight as an unmerged block.
   - **Canonical Page Anchor:** The merged block must anchor to the starting page heading in Obsidian, eliminating empty, orphaned headings for pages whose highlights were absorbed.
4. **Optimal Architecture:** Merge consolidation belongs in `src/native/highlights_ref/sidecar.rs` immediately following `parse_sidecar_markdown`. By normalizing annotations at the AST/model layer into a clean `Vec<SidecarAnnotation>`, all downstream consumers (`sidecar_render.rs`, `annotation_tasks.rs`, `reading_plan.rs`, `report.rs`) automatically inherit the unified blocks with zero disruption to block ID hashing, tombstone management, or task routing.

---

## 2. Problem Analysis & Live Vault Case Study

### 2.1 The Underlying PDF Architecture Constraint
Under the PDF format specification (ISO 32000), text annotations (`/Highlight`, `/Underline`, `/StrikeOut`) are geometric quad-point definitions (`/QuadPoints`) attached to the `/Annots` array of a single `/Page` object. A PDF annotation cannot cross page boundaries. Consequently, PDF reading applications—including Highlights, Apple Preview, Adobe Acrobat, and PDF Expert—treat each page's highlight as an independent entity with its own creation date, color, and attached comment.

Furthermore, within a single page, disjoint selections (e.g., skipping a figure caption, footnote, or irrelevant sentence) cannot be grouped into a single logical highlight without separate selection gestures.

### 2.2 Live Case Study: *Gas Town Emergency User Manual*
In screenshot `~/tmp/screenshots/20261019_063505.png`, Bryan highlights a passage crossing the boundary between Page 11 and Page 12 of `gas_town_emergency_user_manual.pdf`:

- **Page 11 Highlight (Bottom of Page 11):**
  > "One last Crew tip: I have a new ad-hoc role that I’ve been using for the past week, called the “PR Sheriff.” One of my Beads crew has a permanent hook: bd-4f43s: PR Sheriff Standing Orders . On every"
  *(No attached note)*
- **Page 12 Highlight (Top of Page 12):**
  > "session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup."
  *(Attached note: `< PR Merge Master?!`)*

Inspection of the actual sidecar file exported by Highlights to the live vault (`~/bob/lib/blogs/gas_town_emergency_user_manual.md`) reveals lines 204–232:

```markdown
#### [Page 11](highlights://gas_town_emergency_user_manual#page=11)

##### 2026-10-19:

> One last Crew tip: I have a new ad-hoc role that I’ve been using
> for the
past week, called the “PR Sheriff.One of my B
eads crew
> has a
permanent hook: b
d-4f43s: PR Sheriff Standing Orders. On
> every

***

#### [Page 12](highlights://gas_town_emergency_user_manual#page=12)

##### 2026-10-19:

> session startup, the sheriff checks open PRs and divides them
> into easy
wins and those needing human review, then slings the
> easy wins to
other crew for merging and cleanup

< PR Merge Master?!

***
```

### 2.3 The Current Failure Mode in Obsidian
Under the existing `bob ref sync` implementation, this sidecar produces two disjoint callout blocks in `~/bob/ref/blogs/gas_town_emergency_user_manual.md`:

```markdown
### Page 11

> [!quote] One last Crew tip: I have a new ad-hoc role that I’ve been using for the past week, called the “PR Sheriff.One of my Beads crew has a permanent hook: bd-4f43s: PR Sheriff Standing Orders. On every

^h-a1b2c3d4e5f6

### Page 12

> [!quote] session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup
>
> > [!note] Comment < PR Merge Master?!

^h-f6e5d4c3b2a1
```

**Symptom Checklist of Current Failure:**
- **Severed Prose:** The sentence is chopped mid-phrase (`On every` / `session startup`), destroying readability.
- **Leaked Syntax:** The `<` trigger leaks directly into the user comment callout.
- **Orphaned Annotation Anchor:** The commentary `PR Merge Master?!` is attached solely to the second fragment rather than the complete conceptual thought.
- **Task Misdirection:** If Bryan had typed `< - #task PR Merge Master?!`, the resulting task backlink `🔖` in Obsidian would link only to the fragment on Page 12, breaking contextual navigation.

---

## 3. Critique of the Proposed Plan & Credible Alternatives

### 3.1 Evaluation of the `<` Trigger
Bryan's proposal: Automatically merge a highlight (and its notes) with the previous one iff the highlight note starts with `<` (optionally followed by a space and note text).

#### Strengths
1. **Ergonomic Simplicity:** On iOS/iPadOS virtual keyboards and macOS hardware keyboards, `<` is a single key combination (`Shift + ,`).
2. **Intuitive Spatial Directionality:** In Western reading order (left-to-right, top-to-bottom), `<` points leftward and backward, visually communicating: "pull this content back into the previous entry."
3. **Non-Intrusive:** It utilizes an existing field that Highlights already stores and exports without requiring sidecar schema hacks.

#### Potential Pitfalls & Ambiguities
1. **Mathematical & Syntax Collisions:** A reader taking notes on technical papers might write comments starting with `<`:
   - `< 10ms latency target`
   - `<html> or XML wrapper`
   - `<T: Trait> bound`
   - `<- return value`
   If any note starting with `<` blindly triggers a merge, valid independent notes will be mistakenly collapsed into preceding quotes.
2. **Chaining Behavior:** The proposal does not state whether three or more highlights can be chained (e.g., a passage spanning across pages 11, 12, and 13).
3. **Discontinuous Excerpts vs. Continuous Reflow:** The proposal mentions highlights that span "across different points in a paragraph." If two excerpts from a paragraph are merged, simply joining them with a space can distort meaning by omitting an ellipsis.
4. **Collision with Intervening Elements:** What happens if an image selection or standalone note sits between the two highlights?

### 3.2 Alternatives Considered

| Approach | Mechanics | Why Chosen or Rejected |
| :--- | :--- | :--- |
| **A. Upstream Scripting / Native Plugin** | Write a macOS Hammerspoon or PDFKit script to stitch annotations inside the PDF file itself before Highlights exports. | **Rejected:** Fragile, desktop-only, breaks cloud sync between iPad and Mac, and risks corrupting PDF binary structures. |
| **B. Alternative Trigger Sigils (`^`, `<<`, `+`, `@merge`)** | Use `^` (points up in vertical sidebar), `<<` (heredoc/rewind), or explicit `@merge`. | **Rejected as Primary:** `^` collides with Obsidian block links (`^block-id`). `<<` requires two keystrokes. `@merge` is verbose and tedious on mobile. `<` is superior, provided an escape hatch exists. |
| **C. Automatic Heuristic Joining (No Sigil)** | Heuristically join highlights if highlight $N$ ends with an incomplete sentence and highlight $N+1$ starts on the next page with a lowercase letter. | **Rejected:** Highly brittle. Frequently merges quotes the user intended to keep separate (e.g., highlighting two independent sentence fragments for different purposes). Explicit user intent is mandatory. |
| **D. Refined `<` with Escaping & Ellipsis (`\<`, `<...`)** | Adopt Bryan's `<` proposal as the primary syntax, but add `\<` for literal escaping, `<...` for elided joins, and explicit comment concatenation. | **Recommended (Selected):** Preserves the exact ergonomics Bryan desires while guaranteeing mathematical safety, editorial elegance, and structural reliability. |

---

## 4. Comprehensive Design Specification: Intuitive, Reliable, Beautiful

To achieve the design mandate of making this feature **intuitive, reliable, and beautiful**, the system must adhere to the following complete specification.

### 4.1 Intuitive: Grammar, Semantics & Interaction

#### The Trigger Grammar
Let a highlight note's normalized content be $C$. The parser evaluates $C$ against the following prefix rules:

1. **Continuation with Ellipsis (`<...` or `< …`):**
   - Matches: `^<(?:\.\.\.|\u2026)\s*(.*)$`
   - Action: Merge text with predecessor using an ellipsis separator ` […] `.
   - Comment payload: If the captured remainder is non-empty, use it as the continuation comment; otherwise, no comment is added.
2. **Standard Continuous Merge (`<`):**
   - Matches: `^<\s*(.*)$`
   - Action: Merge text with predecessor using continuous reflow (space join with hyphen-healing).
   - Comment payload: If the captured remainder is non-empty, use it as the continuation comment; otherwise, no comment is added.
3. **Escaped Literal (`\<`):**
   - Matches: `^\\<\s*(.*)$`
   - Action: **Do not merge.** Strip the leading `\` and treat the comment as a literal note beginning with `<` (e.g., `\< 10ms` renders as `< 10ms`).
4. **Normal Note (No match):**
   - Retain standard unmerged behavior.

#### Grammar Examples

| Authored Note in Highlights | Action Taken | Resulting Comment in Obsidian |
| :--- | :--- | :--- |
| `<` | Continuous merge | *(Inherits predecessor's comment, if any)* |
| `< ` *(trailing whitespace)* | Continuous merge | *(Inherits predecessor's comment, if any)* |
| `< PR Merge Master?!` | Continuous merge | `PR Merge Master?!` *(or appended)* |
| `<PR Merge Master?!` *(no space)* | Continuous merge | `PR Merge Master?!` *(or appended)* |
| `<... Needs verification` | Discontinuous merge (` […] `) | `Needs verification` |
| `<…` | Discontinuous merge (` […] `) | *(Inherits predecessor's comment, if any)* |
| `\< 10ms latency` | **No merge** (escaped) | `< 10ms latency` |
| `< - #task Check PR rules` | Continuous merge + Task extraction | Extract task: `- [ ] #task Check PR rules` |

#### Multi-Hop Chaining (Associative Fold)
Highlight merging is strictly left-associative. If multiple consecutive highlights each carry `<`:
- **Highlight 1 (Page 11):** "Start of long passage..." *(No note)*
- **Highlight 2 (Page 12):** "...continuation across page..." *(Note: `<`)*
- **Highlight 3 (Page 13):** "...conclusion of thought." *(Note: `< Final synthesis`)*
- **Result:** A single unified block spanning Pages 11–13, containing the entire combined prose and the final comment `Final synthesis`.

#### Predecessor Matching Rules
A continuation highlight merges into the **most recent prior highlight** in sidecar document order, subject to these constraints:
1. **Kind Guard:** The target predecessor must be of kind `SidecarAnnotationKind::Highlight`. It cannot merge into `Image` or `StandaloneNote`.
2. **Marker Mirror Exclusion:** If the raw preceding item was a mirrored PDF marker (page 1 metadata block), it is ignored; the search continues backward to a genuine user highlight.
3. **Orphan / Miss Fallback:** If a highlight begins with `<` but has no eligible predecessor (e.g., it is the very first annotation in the sidecar, or is preceded only by images):
   - The merge is **aborted**.
   - A CLI diagnostic is issued: `warning: highlight on page X has merge prefix '<' but no preceding highlight to merge into`.
   - The highlight is retained as an ordinary, unmerged highlight with its full note text intact (preventing silent text deletion).

---

### 4.2 Reliable: Data Model, Pipeline Architecture & Edge Cases

#### Pipeline Placement in `bob-cli`
The optimal location for merging is in `src/native/highlights_ref/sidecar.rs`, within `parse_sidecar_markdown`.

```
[Raw Sidecar File]
        │
        ▼
[parse_sidecar_markdown] ─────────► [parse_sidecar_chunk] (raw chunks)
        │
        ▼
[consolidate_merged_annotations] ──► (Applies '<' fold, text reflow, comment concat)
        │
        ▼
Vec<SidecarAnnotation> (Normalized AST)
        │
        ├───────────────────────────┬───────────────────────────┐
        ▼                           ▼                           ▼
[render_sidecar_highlights]  [annotation_task_candidates]  [is_sidecar_marker_mirror]
(renders Obsidian callouts)  (extracts #task backlinks)   (filters markers)
```

**Why this placement guarantees reliability:**
1. **Single Source of Truth:** All downstream subsystems (`sidecar_render.rs`, `annotation_tasks.rs`, `report.rs`, `reading_plan.rs`) operate on the already-consolidated AST.
2. **Zero Task Backlink Fragmentation:** `annotation_tasks.rs` extracts `#task` items from `annotation.task_source`. When consolidation happens first, tasks from both the predecessor and the continuation automatically receive the merged highlight's block ID `^h-...`.
3. **No Redundant Parsers:** Does not require modifying Obsidian markdown parsers in `region.rs`.

#### Comment Concatenation Semantics
When merging continuation highlight $B$ into predecessor highlight $A$:

```rust
let merged_comment = match (A.comment.take(), B_cleaned_comment) {
    (Some(c1), Some(c2)) => Some(format!("{c1}\n\n{c2}")),
    (Some(c1), None) => Some(c1),
    (None, Some(c2)) => Some(c2),
    (None, None) => None,
};
```

Using double-newline (`\n\n`) separation ensures that multi-line markdown lists or independent paragraphs from both notes render cleanly without colliding into run-on prose.

#### Task Extraction (`#task`) Semantics
If the continuation note contains tasks (e.g., `< - #task Refactor sheriff`), stripping the `<` prefix and optional whitespace leaves `- #task Refactor sheriff`. 
- `task_source` is updated to combine $A$'s task source with $B$'s cleaned task source.
- `annotation_task_candidates` parses each line.
- Each extracted task generates an Obsidian task:
  ```markdown
  - [ ] #task Refactor sheriff [[#^h-merged-id|🔖]] [h:: hash] [created::2026-10-19]
  ```
- The backlink `🔖` jumps directly to the single merged callout block.

#### Block ID Generation & Tombstone Lifecycle
In `bob-cli`, highlight block IDs are deterministic content hashes generated by `annotation_block_id` in `sidecar_render.rs`:

$$\text{Block ID} = \text{SHA256}(\text{PDF Path} \mathbin{\Vert} \text{Kind} \mathbin{\Vert} \text{Page Label} \mathbin{\Vert} \text{Ordinal} \mathbin{\Vert} \text{Normalized Text})[0..12]$$

**Implications for Merging:**
1. **Deterministic New Block ID:** Because the merged highlight has combined text, its content hash is distinct and stable.
2. **Graceful Tombstoning:** If a user previously synced unmerged highlights ($H_1$ and $H_2$), and subsequently adds `<` in Highlights:
   - On the next `bob ref scan`, the old block IDs `^h-H1` and `^h-H2` disappear from the active set.
   - Bob's existing tombstone subsystem automatically places them under `### Removed highlights`:
     ```markdown
     ### Removed highlights

     > [!warning] Removed highlight This annotation is no longer present in the Highlights sidecar.

     ^h-H1
     ```
   - Any pre-existing Obsidian tasks pointing to `^h-H1` remain fully resolvable without broken links.
   - The newly generated merged block `^h-merged` is rendered cleanly in the active body.

---

### 4.3 Beautiful: Visual Polish & Markdown Typography

A critical requirement is that the rendered output in Obsidian must look intentional, elegant, and readable.

#### Cross-Page Reflow & Hyphen-Healing
PDF text extracted across page boundaries often contains broken words or irregular whitespace. By routing the joined text through Bob's existing text normalization engine (`clean_pdf_text_artifacts` and `append_reflow_fragment` in `text.rs`):
- **Hyphen-healing:** If the predecessor ends with a hyphenated word and the continuation begins with a lowercase letter, the hyphen is removed and the fragments are merged:
  $$\text{"One of my B-"} + \text{"eads crew"} \longrightarrow \text{"One of my Beads crew"}$$
- **Whitespace normalization:** Line breaks between pages are normalized to a single space.
- **Ligature cleanup:** PDF ligatures (`\u{fb01}` $\rightarrow$ `fi`, `\u{fb02}` $\rightarrow$ `fl`) are expanded.

#### Excerpt Punctuation for Discontinuous Highlights
When `<...` is used for intra-paragraph discontinuous selections, the join is formatted as:
$$\text{Quote}_1 + \text{" […] "} + \text{Quote}_2$$
This matches the international typographical standard for omitted text in quotations, presenting a scholarly, polished appearance in Obsidian reading mode.

#### Section Heading & Page Anchor Strategy
Where should the merged highlight appear in Obsidian?

**Options Evaluated:**
- *Option 1: Synthetic Page Range Heading (`### Page 11–12`)*
  - *Critique:* Fragile. If Page 11 also contains an earlier unmerged highlight, the outline becomes cluttered with `### Page 11`, followed by `### Page 11–12`, followed by `### Page 12`. This breaks outline navigation and confuses Dataview queries.
- *Option 2: Canonical Start-Page Heading (`### Page 11`) with Empty Page Suppression (Recommended)*
  - *Design:* The merged block is rendered under the heading of its originating page (`### Page 11`).
  - If Page 12 contains no other highlights, **the `### Page 12` heading is suppressed entirely**.
  - In `sidecar_render.rs`, headings are emitted only when an active annotation exists for that page label.
  - *Result:* The reader sees a single, gorgeous block under `### Page 11`. No empty headers or awkward fragments exist on Page 12.

#### Final Visual Contrast

##### Before (Current Fragmented Rendering)
```markdown
### Page 11

> [!quote] One last Crew tip: I have a new ad-hoc role that I’ve been using for the past week, called the “PR Sheriff.One of my Beads crew has a permanent hook: bd-4f43s: PR Sheriff Standing Orders. On every

^h-46fb815a7676

### Page 12

> [!quote] session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup
>
> > [!note] Comment < PR Merge Master?!

^h-d44f71098a5a
```

##### After (Recommended Merged Rendering)
```markdown
### Page 11

> [!quote] One last Crew tip: I have a new ad-hoc role that I’ve been using for the past week, called the “PR Sheriff.” One of my Beads crew has a permanent hook: bd-4f43s: PR Sheriff Standing Orders. On every session startup, the sheriff checks open PRs and divides them into easy wins and those needing human review, then slings the easy wins to other crew for merging and cleanup.
>
> > [!note] Comment PR Merge Master?!

^h-8e7c6b5a4d3f
```

*(Note that the sentence is perfectly joined, the `<` trigger is stripped from the note callout, the empty `### Page 12` heading is suppressed, and the comment anchors to the complete thought.)*

---

## 5. Implementation Blueprint for `bob-cli`

### 5.1 Proposed Code Modifications

#### 1. Add Merge Trigger Classifier (`src/native/highlights_ref/sidecar.rs`)
```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub(super) enum MergeTrigger {
    None,
    Continuous { comment: Option<String> },
    Ellipsis { comment: Option<String> },
}

pub(super) fn parse_merge_trigger(raw_comment: Option<&str>) -> (MergeTrigger, Option<String>) {
    let Some(comment) = raw_comment else {
        return (MergeTrigger::None, None);
    };

    let trimmed = comment.trim_start();

    // Check for escape sequence: \<
    if let Some(rest) = trimmed.strip_prefix("\\<") {
        let literal = format!("<{rest}");
        return (MergeTrigger::None, Some(literal));
    }

    // Check for ellipsis merge: <... or <…
    if let Some(rest) = trimmed.strip_prefix("<...")
        .or_else(|| trimmed.strip_prefix("<\u{2026}"))
    {
        let comment_payload = rest.trim_start();
        let payload = (!comment_payload.is_empty()).then(|| comment_payload.to_string());
        return (MergeTrigger::Ellipsis { comment: payload }, None);
    }

    // Check for standard merge: <
    if let Some(rest) = trimmed.strip_prefix('<') {
        let comment_payload = rest.trim_start();
        let payload = (!comment_payload.is_empty()).then(|| comment_payload.to_string());
        return (MergeTrigger::Continuous { comment: payload }, None);
    }

    (MergeTrigger::None, Some(comment.to_string()))
}
```

#### 2. Consolidation Pass (`src/native/highlights_ref/sidecar.rs`)
```rust
pub(super) fn consolidate_merged_annotations(
    raw_annotations: Vec<SidecarAnnotation>,
) -> Vec<SidecarAnnotation> {
    let mut consolidated: Vec<SidecarAnnotation> = Vec::with_capacity(raw_annotations.len());

    for mut current in raw_annotations {
        let (trigger, escaped_comment) = parse_merge_trigger(current.comment.as_deref());

        if let Some(escaped) = escaped_comment {
            current.comment = Some(escaped);
        }

        match trigger {
            MergeTrigger::None => {
                consolidated.push(current);
            }
            MergeTrigger::Continuous { comment } | MergeTrigger::Ellipsis { comment } => {
                // Find target predecessor highlight
                if let Some(prev) = consolidated.iter_mut().rfind(|a| a.kind == SidecarAnnotationKind::Highlight) {
                    // 1. Join highlight quotes
                    let is_ellipsis = matches!(trigger, MergeTrigger::Ellipsis { .. });
                    prev.text = join_highlight_texts(&prev.text, &current.text, is_ellipsis);

                    // 2. Combine comments
                    prev.comment = match (prev.comment.take(), comment) {
                        (Some(c1), Some(c2)) => Some(format!("{c1}\n\n{c2}")),
                        (Some(c1), None) => Some(c1),
                        (None, Some(c2)) => Some(c2),
                        (None, None) => None,
                    };

                    // 3. Combine task sources
                    if let Some(current_task_source) = current.task_source {
                        let cleaned_task_source = strip_merge_sigil_from_task_source(&current_task_source);
                        prev.task_source = match prev.task_source.take() {
                            Some(p_src) => Some(format!("{p_src}\n{cleaned_task_source}")),
                            None => Some(cleaned_task_source),
                        };
                    }
                } else {
                    // Fallback: No predecessor highlight found; retain unmerged
                    consolidated.push(current);
                }
            }
        }
    }

    // Re-index orders and ordinals on page for deterministic downstream hashing
    reindex_annotation_ordinals(&mut consolidated);
    consolidated
}
```

#### 3. Text Joining Helper (`src/native/highlights_ref/text.rs`)
```rust
pub(super) fn join_highlight_texts(first: &str, second: &str, ellipsis: bool) -> String {
    let mut joined = first.trim_end().to_string();
    let trimmed_second = second.trim_start();

    if ellipsis {
        if !joined.ends_with('.') && !joined.ends_with('…') {
            joined.push_str(" […] ");
        } else {
            joined.push_str(" […] ");
        }
        joined.push_str(trimmed_second);
    } else {
        append_reflow_fragment(&mut joined, trimmed_second, ends_with_soft_hyphen(first));
    }

    joined
}
```

---

## 6. Summary of Adjustments to User Requirements

The following table explicitly details all modifications and additions made to Bryan's original prompt requirements:

| Aspect | User Prompt Baseline | Adjusted Recommendation | Rationale |
| :--- | :--- | :--- | :--- |
| **Trigger Character** | Highlight note starts with `<` (optionally followed by space and text). | Supported exactly as requested, plus **`\<` escape sequence**. | Prevents false-positive merges when users write math/code notes (e.g., `< 10ms`, `<T>`, `<html>`). |
| **Discontinuous Joins** | Merges highlights across different points in a paragraph. | Adds **`<...` / `< …` syntax** to insert ` […] ` between disjoint excerpts. | Preserves citation integrity by visually acknowledging omitted text in discontinuous paragraph quotes. |
| **Comment Merging** | Merge highlight (and its notes) with previous one. | When both have notes, **concatenate with `\n\n`**. If continuation has bare `<`, predecessor note is preserved. | Guarantees zero data loss when readers record thoughts on both pages. |
| **Task Intake (`#task`)** | Not explicitly detailed. | Continuation `#task` lines are cleaned and **attributed to the merged block ID**. | Ensures Obsidian task links (`🔖`) navigate directly to the unified callout. |
| **Predecessor Guard** | Target "the previous one". | Predecessor must be a **`Highlight`**. Images and mirrors are bypassed or trigger safe fallback. | Prevents attempting to merge text highlights into image assets or PDF metadata mirrors. |
| **Obsidian Page Header** | Unspecified. | Retain **originating page header**; suppress empty headers on absorbed pages. | Keeps Obsidian outline clean, elegant, and free of orphaned page headings. |

---

## 7. Recommended Solution & Action Plan

1. **Adopt Design Option D (Refined `<` with Escapes and Ellipsis):** Implement the trigger parser and AST consolidation in `src/native/highlights_ref/sidecar.rs`.
2. **Execute Unit Test Coverage:** Add fixture-backed tests in `src/native/highlights_ref/tests/sidecar.rs` validating:
   - Single-character `<` merge across page boundaries.
   - Merging with attached comment (`< PR Merge Master?!`).
   - Discontinuous excerpt merge with ellipsis (`<...`).
   - Multi-hop chaining across 3+ pages.
   - Escape sequences (`\< 10ms`).
   - Fallback behavior when no preceding highlight exists.
   - Task extraction from merged annotations.
3. **Verify Against Live Vault:** Execute `bob ref sync ~/bob/lib/blogs/gas_town_emergency_user_manual.pdf -d` to verify that Pages 11 and 12 merge seamlessly into a single callout block with comment `PR Merge Master?!`.

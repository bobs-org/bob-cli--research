# Directed task-to-task links: a `🪢 LINKS` line, a generated `🪢 LINKED FROM` mirror, and `~` / `~~` capture

*Researcher: cld · 2026-10-20 · one of five independent reports in research swarm 53*

## Bottom line

**Build it. Treat it as the second *edge kind* on the machinery that DEPENDS ON / BLOCKS already proved, not as
a new subsystem.** The vault shows the need. It holds about 120 hand-written task-to-task references outside
dependency lines, including 28 hand-kept "Merged into" / "Merged from" pairs, which are bidirectional links
maintained by hand. bob-cli and bob-plugins already ship the right architecture for the reverse side: one
authored line, a generated mirror on the other task that is never read back, courtesy writes in the same
transaction, and `bob task reconcile` as the authority.

What I would build, in one screen:

```markdown
- [ ] #task Fix flaky capture retries #bob ^fix-retries
	- 🪢 **LINKS:** follow-up of [[done/bob_done#^capture-star]] • see [[sase#^retry-design]]

- [ ] #task Design a retry policy ^retry-design
	- 🪢 **LINKED FROM:** [[bob#^fix-retries]] (see)
```

```text
bob capture 'Fix flaky capture retries ~bob_done:capture-star|"follow-up of" ~sase:retry-design|see'
bob capture 'Write the outline ~~sase_blog:prj|"next step"'          # the existing task links to the new one
bob capture '@bob+fix-retries ~sase:retry-design|see'                # two existing tasks
```

Obsidian: in the Task Card (Ctrl+Shift+P), `l` opens **Links to…** and `⇧L` opens **Linked from…**. Direct
chords Ctrl+Shift+L and Ctrl+Shift+Alt+L mirror the existing Ctrl+Shift+B and Ctrl+Shift+Alt+B. In every
picker, ↵ links and ⇧↵ links and asks for a relation.

The adjustments I recommend, each explained in [§3](#3-requirement-adjustments):

1. Call the reverse line **LINKED FROM**, not BACKLINKS. In Obsidian, "backlinks" means *every* inbound link,
   and for a task that means mostly Pomodoro ledger noise.
2. Redefine "always consistent" as a guarantee that can actually be tested: *what you see* is always live,
   and *what is stored* converges by the next write or reconcile.
3. Links are **inert**. They never change status, lane, freshness, schedule, Pomodoro links, or blocking.
4. Labels are **free text, optional, and phrased from the linking task's side**. A picker suggests the labels
   already in use so the vocabulary does not sprawl.
5. Closed and archived tasks are valid targets. Unlike dependencies, relations are history.
6. Both directions work in both clients. Ctrl+Shift+P handles outgoing as well as incoming links.
7. Highest-leverage follow-up: put **"Cancel as duplicate of / merged into / superseded by…"** into the
   Task Card's cancel stage. Those are the relations Bryan already writes by hand most often.

---

## 1. Request and method

Bryan asked for directed links from one Obsidian task to another:

- shown on a new `LINKS` sub-bullet;
- with auto-maintained, always-correct `BACKLINKS`;
- captured in Bob Mac Capture with `~` (link the new task to an existing one) and `~~` (an existing task
  links to the new one);
- addable from Obsidian through Ctrl+Shift+P;
- carrying an optional relation description.

He asked for a design that is intuitive, reliable, and beautiful, plus a critique.

What I examined, independently of the other researchers:

- **bob-cli contracts:**
  - `docs/task-dependencies.md`: §2.4 managed-line registry, §3 identity, §4 R1–R10, §14 BLOCKS mirror,
    §15 reverse stage.
  - `docs/capture.md` and `docs/reference/capture-syntax.md`: the full sigil inventory and every existing
    `~` use.
  - `docs/task-status-hooks.md` (`done/` archive and previous-daily read-only rules); `docs/projects.md`
    (Task Card).
  - Source: `src/native/capture_language/dependencies.rs` (the `&` / `*` lexer and its guards),
    `src/native/capture/blocks_mirror.rs`, `src/native/task_status_hooks/blocks.rs`.
  - I ran read-only `bob capture-parse` probes of `~` drafts.
- **bob-plugins:**
  - Task Card row table and key router (`bob-navigation-hotkeys/src/310-task-card-previews.js`).
  - Depends-On and BLOCKS writers and mirror (nav `080`–`083`, `591`, `600`).
  - Chips (`bob-ledger-tools/src/140`–`281`, `styles.css`).
  - Move and rename link repair (nav `250`, `655`; cycler `120`).
  - `docs/task-card.md`.
  - The vault's `.obsidian/hotkeys.json`.
- **Bob Mac Capture:** picker and completion dispatch (`CapturePanelModel.swift`), the direction-aware
  picker from commit `f2a5cb5` (`DependencyPickerPresentation.swift`, `CaptureRelationshipCopy.swift`), span
  palette, and the Add-block-ID prompt card.
- **The live vault** (`~/bob`, read-only): counts of tasks, block IDs, managed lines, ad-hoc task references,
  relation phrases, and `~` usage.
- **Decision records** read with `sase memory read`: `task-deps-are-depends-on-links`,
  `capture-star-blocks-existing-tasks`, `mac-capture-is-a-thin-client`, `capture-link-drops-blocking-deps`,
  `task-status-is-derived`, `task-lanes-are-sticky`. Glossary: Task Link, Task Dependency Link, Capture,
  Successor Offer, Work Log.
- **Prior Bob research:** `research:202610/prerequisite_blocks_line/prerequisite_blocks_line.md`, the BLOCKS
  mirror design, read through `sase artifact read`.
- **External prior art:** Jira, Linear, GitHub, Obsidian Tasks, Breadcrumbs, Juggl, ExcaliBrain, Logseq and
  Roam, Notion, Capacities, Tana, org-edna, org-super-links, org-roam, Taskwarrior, and Wikidata inverse
  properties. Sources are listed at the end.

---

## 2. Critique: is this a good idea?

### 2.1 Why yes

1. **Bryan already does this by hand.** The read-only vault survey found:

   | Evidence | Count |
   | --- | --- |
   | Block links to tasks nested under other tasks or on task lines, outside DEPENDS ON / BLOCKS / Pomodoros | ≈120, in ≈35 files |
   | "Merged into" / "Merged from" lines; survivors carry a hand-copied "Merged from:" back-reference | 28 |
   | `See [[` in sub-bullets | 218 |
   | `RELATED:` (one written as bold `**RELATED:**`) | 47 |
   | `OBSOLETE: See …` / "Obsoleted by" | ≈36 |
   | "Duplicate of" / `DUPLICATE:` | 13 |
   | "Read research" links from a task to its reference task | ≈41 |

   The 28 Merged-into / Merged-from lines matter most. Bryan maintains both ends of a relation by hand, which
   is the exact chore this feature removes.
2. **Obsidian's native backlinks cannot answer "what points at this task?"** The backlinks pane works per
   note, and for any task note it is dominated by the daily ledger: 2,222 Pomodoro Task Links and 213 embeds.
   A curated, per-task LINKED FROM line is real information that nothing in the vault provides today.
3. **The hard part is already built.** BLOCKS is a generated mirror that is never read back, written as a
   courtesy in the same batch by capture (`capture/blocks_mirror.rs`) and in the same transaction by nav
   (`083-blocks-dependency-plan.js`). Reconcile is the authority (`task_status_hooks/blocks.rs`). Chips are
   drawn from a live reverse index (`141-blocks-model.js`). There is a kill switch and shared vector tables.
   LINKS / LINKED FROM can reuse most of that infrastructure and every lesson from it.
4. **Every mature tracker shows a relation at both ends.** Jira has outward/inward descriptions, Linear has
   related / blocks / duplicate, and GitHub has blocked-by / blocking. Most store **one** record and render
   both ends. A plain-text vault read by vim, git, and SASE agents cannot "just render", which is why the
   BLOCKS research chose a stored projection, and why it fits here too.

### 2.2 What worries me, and how the design answers it

| Concern | Why it matters | Answer in this design |
| --- | --- | --- |
| **"Link" is already a loaded word.** | "Task Link" (glossary) means any block link to a task and is strongly tied to Pomodoros. "Linking" a task means putting it under today's ledger. The `:` capture picker is the link picker; capture's footer verb is **Link**; block-id-prompt has a "Link to task" picker. | Keep **LINKS** for the line (its entries *are* Task Links in the glossary sense). Name the concept **Task Cross-Link** in docs and the glossary. Always pair the UI verbs "links to" / "linked from" with the 🪢 glyph, while Pomodoro linking keeps 🍅. Name the mirror **LINKED FROM** ([RA1](#3-requirement-adjustments)). |
| **"Must always stay consistent and correct" can't be met literally.** | The vault is plain files synced by git across three machines. Agents and vim edit it raw, and `done/` archives and the previous daily note are read-only by contract (`task-status-hooks.md` §§ on archive and previous daily). | The guarantee is split ([§5.5](#55-the-mirror-projection-authority-and-guarantees)). The **displayed** LINKED FROM is always live, because chips render from an index. The **stored** line is a pure function of all LINKS lines: every Bob writer updates it at once, and reconcile converges it. Six invariants are tested. |
| **Label sprawl** | Jira's 607k-link study found 75 link types in 15 repos that researchers had to regroup into 5 by hand (Lüders et al., MSR '22). Linear ships four. | Labels are free text but optional. The picker suggests existing labels by frequency, and a starter set comes from the vault's own idioms. No type registry. A lint flags near-duplicates. |
| **Two ends, two wikilinks** | The mirror adds a real `[[…]]` back to the source, so Obsidian's graph and backlinks pane show each relation twice. org-super-links users complain about exactly this ("every connection ends up being a circular reference"). | Accepted cost, the same as BLOCKS. Plain-text parity (`rg`, `gf`, agents) is worth more than a tidy graph view. |
| **`~` already means "drop"** | Inside Pomodoro tokens, `x~2` and `=~2` drop Task Links (capture.md: "One-card mnemonic: **`~` drops**"). `~~` also looks like strikethrough, and `~/path` and `~5m` appear in prose. | A **standalone** `~` token is unclaimed: probes of `Fix it ~work:foo` and `~work:foo Fix it` give plain body, no spans. The `*` precedent supplies the guards: `~/`, digit-led, strike-shaped, and `\~` ([§5.9](#59-capture-grammar-and-)). The mnemonic grows to "**`~` on its own relates; `~` inside `x`/`=` drops**". |
| **The four-parser tax** | Rust, nav, ledger-tools, and the cycler/block-id-prompt recognisers must all reject the new lines, or they may treat them as Task Links, tree-close targets, or legacy R8 children. The BLOCKS research found that "this is where the bugs would actually come from". | **Guards ship first**, in every engine, before any writer. New MC rows go in `task-dependencies.md` §11.8, and new LK vectors in the contract. |
| **`done/` asymmetry** | Reconcile's active scan skips `done/`, and archive notes are only loaded read-only. A follow-up that links to an archived task can't get a stored mirror there, and a cancelled "merged into" source that gets archived would vanish from its survivor's mirror unless reconcile still reads it. | The link index **reads** LINKS lines in `done/` and the previous daily note read-only, and **writes** mirrors only on writable tasks. Archived targets show their inbound links through live chips; the stored mirror is absent there by contract ([§5.6](#56-archives-moves-renames-and-read-only-notes)). |

### 2.3 Verdict

It is a good idea, and better than it looks, **provided the feature stays inert and single-sourced.** The
danger is not the backlink line. It is a feature that slowly grows semantics: links that promote, block,
close, or get consumed. Every one of the existing decision records exists because derived and authored state
got tangled. Cross-links should be the one relation in Bob that *does nothing* except connect and explain.

### 2.4 Would I take a different approach?

The deliverable stays the same; the emphasis shifts in three ways:

1. **Generalize, don't copy.** Make the managed-line machinery table-driven, as "edge kinds":

   | Edge kind | Authored line | Mirror line | Semantics |
   | --- | --- | --- | --- |
   | `depends_on` | DEPENDS ON, on the dependent | BLOCKS, on the prerequisite | blocking, status-bearing |
   | `cross_link` | LINKS, on the source | LINKED FROM, on the target | inert, labelled, history-preserving |

   The projection is one pure function per kind, `mirror_lines(edges) → lines`. It is implemented once in
   Rust and once in JS and pinned by shared vectors. This keeps it from becoming a third parallel copy in four
   codebases.
2. **Render from a live index; store for plain-text parity.** This is the same split BLOCKS uses: chips
   never trust the stored mirror.
3. **Aim first at where relations are actually born.** Most of the existing hand-written relations are
   lifecycle relations (merged into, duplicate of, obsoleted by) written *when cancelling*. A "Cancel as
   duplicate of / merged into / superseded by…" option in the Task Card's `x` stage catches those with zero
   new syntax to learn. The `~` capture path catches the other common origin, a follow-up or split captured
   while the original is in view.

The single biggest alternative I rejected is **render-only backlinks**: LINKS is stored, while LINKED FROM is
only a virtual line drawn by the plugin. It has zero drift and zero churn. It fails the request and plain-text
parity: vim, `rg`, SASE agents, and the Mac app see nothing. The accepted decision record rejected the same
shape for dependencies ("Fields only with a virtual line… nothing readable or hand-editable in the note").
Since the stored-mirror machinery already exists, its marginal cost here is small.

---

## 3. Requirement adjustments

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| RA1 | `BACKLINKS` sub-bullet | `🪢 **LINKED FROM:**` | In Obsidian, "backlinks" means *all* inbound links. Bryan and agents would expect Pomodoro links, dependency links, and embeds there, and the line deliberately shows none of them. "LINKED FROM" is the exact grammatical mirror of LINKS ("S links to T; T is linked from S"), the same way BLOCKS mirrors DEPENDS ON. |
| RA2 | "must always stay consistent and correct" | **The view is always live; the stored mirror is a pure, idempotent projection.** Every writer updates it at once, reconcile converges it, and the invariants are tested. Mirrors are never written into `done/` or the previous daily note. | Literal always-consistency is impossible with git sync, raw edits, and read-only archives. This is the strongest guarantee that is honest and testable ([§5.5](#55-the-mirror-projection-authority-and-guarantees)). |
| RA3 | Ctrl+Shift+P for "another task should link to the current task" | **Both directions in the Task Card:** `l` Links to…, `⇧L` Linked from…, plus chords Ctrl+Shift+L and Ctrl+Shift+Alt+L. | Outgoing links from Obsidian are the more common case and were missing from the ask. The pairing exactly mirrors the shipped `b` / `⇧B` and Ctrl+Shift+B / Ctrl+Shift+Alt+B. |
| RA4 | "optional relation / link description" | **Optional free-text label, phrased from the linking task's side** ("S *follow-up of* T"), suggested from labels already in the vault. The picker preview always shows the full sentence. | Free text fits a single user, and suggestions prevent sprawl. A fixed direction convention keeps labels readable at both ends. |
| RA5 | (unstated) semantics | **Inert.** Never blocking, never a Pomodoro Task Link, never consumed, never closed by cascade, and never changes status, lane, freshness, schedule, or priority. | Prevents the derived/authored tangles that the existing decision records keep fixing. It is also what separates LINKS from DEPENDS ON. |
| RA6 | (unstated) targets | **Any `#task` with a block ID, open or closed, including `^prj`, `^ref`, and `done/` archives.** Open tasks rank first. | "Follow-up of", "duplicate of", and "merged into" usually point at closed tasks. The Depends-On picker's open-only pool would be wrong here. |
| RA7 | `~~` for the reverse | **Kept**, with a strikethrough guard. In the Mac picker, typing a second `~` flips direction live. | It is the user's choice, fast to type, and the doubled-sigil pattern already exists (`@@`, `++`). The guard is the same shape as `*`'s `**bold**` guard. `~~` also removes the owner-location limits of `@route+id` ([§5.9](#59-capture-grammar-and-)). |
| RA8 | (implicit) storage | **No inline `[links::]` field on the task line**, and no `[id::]` minted for links. | `[dependsOn::]` exists only for the Tasks plugin's `is blocked`. Links have no Tasks semantics, and the task line is already crowded. `[id::]` means "is a prerequisite" (BLOCKS research). |
| RA9 | (implicit) CLI | **No new write command.** `bob capture` owner mode is the CLI (`bob capture '@bob+a ~sase:b\|see'`). | One grammar and one planner. `bob task <verb>` is reserved for vault-wide rewrites (`cli_rules`). A read-only report can come later if it is ever wanted. |
| RA10 | "LINKS sub-bullet" shape | **One line per task, ` • `-joined**, not one bullet per link. | It matches DEPENDS ON and BLOCKS and the closed managed-line registry. One line is compact for the common one-link case and avoids bare-link rows that the Task Link, tree-close, and strike/restore recognisers would claim ([§6](#6-alternatives-considered)). |
| RA11 | (implicit) emoji | **🪢 (U+1FAA2) for both lines; never 🔗.** | All four Depends-On parsers accept 🔗 as a legacy Depends-On emoji. 🪢 is a single code point with no VS16, like 🧱. Using one glyph on both lines shows they are two ends of one edge; the bold label gives the direction. |

---

## 4. What prior art teaches (condensed)

- **Store one edge, render two ends.** Jira links have outward and inward descriptions on one record.
  Taskwarrior stores `depends` on the dependent only, and its `BLOCKING` is a virtual tag "evaluated at run
  time". The Obsidian Tasks plugin computes "blocking" from `dependsOn`. org-roam keeps backlinks in a SQLite
  cache.
- **Two-sided storage in plain files needs a single writer plus repair tools.** org-super-links writes a
  `:BACKLINKS:` drawer into the target. Its author reports stale text after renames "that require some fixes
  by hand". Relation Sync, an Obsidian plugin, ships paused by default with previews and an undo log.
  Wikidata editors call manual inverse statements "redundant (in a bad way) and unsustainable".
  **Conclusion:** the mirror must be *generated*, never authored, which is the BLOCKS model.
- **Name both ends explicitly.** Jira's Blocks type uses "blocks" as both its name and its outward
  description, which makes queries ambiguous. Atlassian has a KB article on "inverted" links. Obsidian Tasks
  renamed `blockedBy` to `dependsOn` to fix direction ambiguity. **Conclusion:** use fixed line labels (LINKS
  / LINKED FROM) and a fixed label perspective (the source's side), and preview the whole sentence.
- **Keep the type set small.** Linear ships four relation types and creates "related" automatically from
  mentions. Jira sprawls. **Conclusion:** no type registry; optional free text with suggestions.
- **Context beats bare backlinks.** Sascha Fast on zettelkasten.de: "Lists of backlinks… don't reveal the
  context." That is the case for the optional label.
- **Juggl's typed-link form** is `- linkType [[note]], [[note2]]`, a list item that leads with the label.
  It is almost exactly Bryan's hand idiom ("Merged into [[x]]", "Duplicate of [[x]]") and the LINKS entry
  form below.

---

## 5. The design

### 5.1 Vocabulary

| Term | Meaning |
| --- | --- |
| **Task Cross-Link** (aka cross-link) | A directed, optionally labelled, inert edge from a **source** task S to a **target** task T, stored as one entry on S's LINKS line. |
| **LINKS line** | `🪢 **LINKS:**`, S's managed child line and the **only source of truth** for S's outgoing cross-links. Hand-editable. |
| **LINKED FROM line** | `🪢 **LINKED FROM:**`, T's **generated** mirror listing every S that links to T. Never read back; hand edits are restored. |
| **Relation label** | Optional free text that reads as "S ‹label› T", e.g. "follow-up of", "see", "merged into". |

This would become a glossary strand, `glossary:task-cross-link`, plus a decision record (see
[§7](#7-rollout)).

### 5.2 Vault grammar

```text
<indent>- 🪢 **LINKS:** <entry> • <entry> • …
<entry> := [<label> ' ']<link>

<indent>- 🪢 **LINKED FROM:** <mirror-entry> • <mirror-entry> • …
<mirror-entry> := <link>[' (' <label> ')']

<link> := [[#^id]] | [[basename#^id]] | [[dir/note#^id]]    (the canonical_link form; no alias, embed, or strike)
```

- **Label first on LINKS, link first on LINKED FROM.** Both lines then read as English with the subject first:
  "*(this)* follow-up of [[X]]" and "[[S]] *(see)* → this". The authored form matches Bryan's existing idiom
  ("Merged into [[…]]", "Duplicate of [[…]]", `RELATED: [[…]]`, `See [[…]]`), so hand edits feel natural.
- **Label rules.** 1–60 characters after trimming and whitespace collapsing. It may not contain `[[`, `]]`,
  `•`, `**`, or a line break. A trailing `:` is stripped (`see:` becomes `see`). Case is preserved;
  suggestions dedupe case-insensitively. The writer replaces a `•` typed in a label with `·`.
- **Reader tolerance**, so hand variants canonicalise instead of duplicating:
  - a missing emoji or `🔗`/`↔️`;
  - the labels `LINKS TO`, `RELATED`, `SEE ALSO` on the authored line;
  - `·` or `,` separators;
  - aliased links: an alias becomes the label only when no label precedes the link;
  - struck links, which are kept but the strike is removed.

  Lowercase `links:` is prose. Malformed lines (a half-typed link, or prose after the last link) are left
  alone and warned (`malformed_links_line`), and no second line is inserted.
- **Entry order.** LINKS keeps authored order; new entries append, and a re-link with a new label relabels
  in place. LINKED FROM is sorted canonically: same-note first, then by note path, then by block ID,
  case-folded with a raw tiebreak. That makes it byte-identical whichever machine or engine produced it,
  which matters for git convergence.
- **Slot.** The order is: `❌ CANCEL LOG`, `⛓️ DEPENDS ON`, `🧱 BLOCKS`, `🧩 Sub-projects`, **`🪢 LINKS`**,
  **`🪢 LINKED FROM`**, then user children, `🗓️ SCHEDULE LOG`, and `🛠️ WORK LOG`. Blocking structure comes
  first and association second. Placing the lines after Sub-projects leaves `bob projects sync`'s anchor
  rule untouched. Existing lines are never moved; duplicates after the first are merged (LINKS) or deleted
  (LINKED FROM).
- **Registry.** Both rows join the closed managed-line registry in `task-dependencies.md` §2.4. Every Task
  Link, Pomodoro, section-title, tree-close, strike/restore, R8 legacy-child, and other managed-line parser
  must reject them. New MC vectors pin this.

### 5.3 Identity, minting, and link form

- **Target needs a `^id`.** In the pickers, an ID-less target shows `＋ id` and opens the existing "New
  block ID" step, pre-filled by `suggestPromptBlockId` or capture's `block_id_suggestions`. This reuses the
  Depends-On and `&` flows exactly.
- **Source needs a `^id` only for the mirror.** It is minted silently, once, the same way
  `mintDependentBlockId` and `mint_block_id(description, used)` work for BLOCKS. It is minted inside the same
  transaction or batch; dry-run and Escape mint nothing.
- **Never add `[id::]` or `[dependsOn::]`.** Cross-link writes touch only child lines plus a minted `^id`.
  They never touch status, fields, or `[fresh::]` on either task line.
- **Link form** is the shared `canonical_link` / `canonicalDependencyLink` function: `[[#^id]]`, then the
  unique basename, then the full path, and always the full path for `done/`.
- **Edge identity** is (S, T): at most one entry per target per source. Self-links are refused, and so are
  non-task targets. A ↔ B is allowed as two independent edges. Cycles are meaningless for inert edges, so
  they are allowed.

### 5.4 What cross-links never do

Writing this list into the contract is the main reliability lever:

- A cross-link never blocks, unblocks, promotes, releases, or consumes anything.
- It is never a Pomodoro Task Link. It is never counted by the plan budget or seen as a completable
  sighting. Successor offers never consider it. Ctrl+Shift+Enter and `^^` never act on it, and tree-close
  never strikes it.
- Closing, cancelling, reopening, or archiving either end never removes the edge. Relations are history.
- No cross-link write changes a status, lane, `[fresh::]`, `[keeps::]`, schedule, or priority. The review
  walk never visits a LINKS or LINKED FROM line as an item.

### 5.5 The mirror: projection, authority, and guarantees

**Projection** (one pure function, implemented in Rust and in a JS twin, pinned by shared vectors):

```text
sources  = #task lines with a LINKS line in: active notes (writable)
                                             ∪ the previous daily note (read-only)
                                             ∪ done/ archives (read-only)
edges    = { (S, T, label) : entry in S's LINKS resolves to #task T, T ≠ S }
           excluding unresolved, non-task, self, and malformed-line entries (warned)
mirror(T) = sort_canonical({ (S, label) : (S, T, label) ∈ edges })
T owns a LINKED FROM line  ⇔  mirror(T) ≠ ∅  ∧  T is writable (not in done/, not the previous daily note)
```

Unlike BLOCKS, **closed sources and closed targets stay in.** BLOCKS lists only open dependents because
"blocks" is a live claim. "Linked from" is a historical fact. A closed target in an active note keeps getting
its mirror until it is archived; then the line travels with it into `done/` and freezes.

The `done/` read is a second narrow archive exception, next to the existing exact-`done/`-target exception in
`task-status-hooks.md`. It is read-only, scans only LINKS lines, and covers 29 archive files and about 2,500
task lines today, which is cheap.

**Authority.** A new `reconcile_cross_link_lines` pass runs in `bob task reconcile`, after the
BLOCKS pass, with the same structure:

- missing → insert; different → rewrite in place; not desired → delete; malformed → leave and warn;
  duplicates → keep the first;
- edits go through the guarded structural output (2 s quiet interval, preimage checks, recovery snapshots);
- **never prune on uncertainty:** a failed read or a malformed source line keeps its prior entries and warns.

Reconcile already runs every 15 minutes on the Mac and on demand.

**Immediate writers.** All of them call the same projection for old ∪ new targets they touched:

| Writer | What it writes |
| --- | --- |
| Capture `~` / `~~` (CLI and Mac) | S's LINKS entry, any minted `^id`s, and T's LINKED FROM, **in the same staged batch**. It is a courtesy write, as in `blocks_mirror.rs`: skips (read-only T, malformed line) are left for reconcile, and the mirror never fails a capture. |
| nav Links to… / Linked from… stages | Same-note: one transaction, one Ctrl+Z. Cross-note: a follow-up write after the commit through the open editor or a preimage-checked `vault.process`, reusing `591-blocks-follow-ups.js`. On failure the notice says `· 🪢 LINKED FROM not updated`. |
| Chip `×`, Ctrl+D on a LINKS entry | Removes the entry and its mirror entry. Ctrl+D on a LINKED FROM line is **refused**: one key must not edit another note's authored line silently. Use ⇧L instead. |
| Hand edit of a LINKS line | Mirrored after the existing 400 ms debounce once the cursor leaves the line (the `600-plugin-dependency-mirror.js` pattern), diffing old against new targets. Undo re-arms it. |
| Hand edit of a LINKED FROM line | Never an edge change. Reconcile restores it. nav shows `🪢 LINKED FROM is generated from other tasks' LINKS lines · Ctrl+Shift+Alt+L to change it`. |
| `bob task reconcile` | The authority: whole vault, idempotent. |

**Guarantees, stated as testable invariants:**

1. **Single source.** Deleting every LINKED FROM line in the vault and running reconcile rebuilds
   byte-identical lines. A second run changes nothing.
2. **Inertness.** Adding, removing, or relabelling any cross-link leaves every status, lane, field,
   schedule, Pomodoro section, and Depends-On/BLOCKS line byte-identical.
3. **Engine agreement.** Rust and JS projections agree on every shared vector (LM table).
4. **Live view.** Chips render the live index. A stored entry that is no longer live renders dashed, and a
   live edge missing from the stored text is appended visually. So *what Bryan sees* is right even before
   reconcile runs.
5. **Convergence.** Two machines that project the same vault produce the same bytes (canonical sort), so a
   git merge of mirror-only changes can't conflict semantically, and the next reconcile heals any textual
   conflict.
6. **Read-only respect.** No cross-link write ever touches `done/` or the previous daily note.

**Kill switch:** `links.linked_from_lines` (default `true`), parallel to `dependencies.blocks_lines`.
Setting it to `false` removes every mirror line on writable tasks; LINKS lines are untouched.

### 5.6 Archives, moves, renames, and read-only notes

| Case | Outcome |
| --- | --- |
| S closed or cancelled, still in an active note | LINKS stays and the mirror entry stays; the chip shows ✓ or ✕. |
| S archived by `bob task archive` | The LINKS line moves with the task. Archive link repair rewrites T's mirror entry to `[[done/x_done#^s]]`. Reconcile still reads S's LINKS from `done/`, so the entry **persists**: "merged from" survives archiving. |
| T archived | T's LINKED FROM moves with it and freezes. New links to T get no stored mirror; nav and the Mac preview say *"archived target · LINKED FROM shown live only"*. Chips still render inbound links from the index. |
| T in the previous daily note | S's LINKS is written; T gets no stored mirror (read-only). |
| Ctrl+Shift+M / `bob task move` of S or T | `rewriteTaskMoveBlockLinks` already rewrites every `[[source#^id]]` in every note, including these lines. Reconcile re-sorts the mirror. A mirror has nothing to heal. |
| Note rename | Obsidian's link updater rewrites `[[note#^id]]` in both lines. Labels are outside the link, so they survive. No path-encoded `[id::]` is involved. |
| T deleted | S's chip shows ⚠ broken, and reconcile warns `unresolved_cross_link`. The entry is **never** auto-deleted from LINKS, because it is authored data. |
| S deleted | T's mirror entry disappears at the next reconcile; chips hide the lag. |

### 5.7 Rendering

The rendering lives in bob-ledger-tools and reuses the `.bob-dep-chip` DOM, state boxes, truncation, and
`↗ note` labels, with a distinct knot accent.

**Live Preview (cursor off the line):**

```text
○ Fix flaky capture retries   #bob
   🪢 links to    follow-up of ⟶ ✓ Capture * blocks existing tasks  ↗ bob_done
                  see ⟶ ○ Design a retry policy  ↗ sase

○ Design a retry policy
   🪢 linked from  ○ Fix flaky capture retries  ↗ bob  ⟵ see
```

- The **label renders as a muted small-caps pill** on the arrow side of the chip, so the sentence reads in
  the right direction at both ends. An unlabelled link is just the chip.
- When labels are present, entries wrap one per visual row. A single unlabelled link stays inline like a
  Depends-On chip. More than three ✓ chips collapse to `✓×N`, as for dependencies.
- **Optional polish (v2): inverse display labels.** A small configurable table renders the target-side
  phrase on LINKED FROM chips:

  | Stored label | Shown on the target |
  | --- | --- |
  | merged into | merged from |
  | duplicate of | duplicated by |
  | follow-up of | followed up by |
  | superseded by | supersedes |
  | split from | split into |

  Storage stays verbatim. Only the chip changes, so the survivor's chip reads **"merged from ○ Old task"**,
  which is Bryan's hand idiom, now automatic.
- Reading view decorates the existing `<li>` in place, through the same post-processor pattern as
  `280-plugin-dependency-render.js`, with `×` remove and `＋` add controls on LINKS and `＋` only on LINKED
  FROM (it opens ⇧L).
- `toggle-dependency-chips` covers the new lines too, so chips-off shows raw Markdown.

### 5.8 Obsidian gestures

**Task Card (Ctrl+Shift+P)** gains two rows using the free `l` / `⇧L` keycaps, slotted after Blocks:

```text
 Fix flaky capture retries · bob · Ready · P2 · every 7d
 ──────────────────────────────────────────────────────
 ↵   Schedule        in 3 days
 b   Blocked by      —
 ⇧B  Blocks          —
 l   Links to        2 · follow-up of Capture *… +1
 ⇧L  Linked from     1 · Design a retry policy
 f   Review every    7d
 x   Cancel…
```

- **Chords:** Ctrl+Shift+L (`task-card-links`) and Ctrl+Shift+Alt+L (`task-card-linked-from`). Neither is
  bound in the vault's `hotkeys.json` or in any bob plugin's defaults. Check Obsidian's own core defaults
  before claiming them.
- On a LINKS or LINKED FROM line, Ctrl+Shift+P and both chords open the **owning** task's stage. The task
  under the chip is never treated as the owner (the BLOCKS rule).
- **Counted:** `3 Ctrl+Shift+L` links the task and the next three to one target with one label ("these four
  are follow-ups of X").
- The `actionKey` repeat-guard regex in `310` must learn `l`/`L`.

**Links stage** (reusing the Depends-On stage's pool, ranking, and CURRENT/RESULTS grouping):

```text
 🪢 Fix flaky capture retries links to…           [ retry pol▏ ]
 CURRENT
   ✓ follow-up of  Capture * blocks existing tasks      done/bob_done
 RESULTS
   ○ Design a retry policy                              sase
   ○ Retry backoff jitter                               sase
 CLOSED
   ✓ Capture retry spike                                bob
 ↵ link · ⇧↵ link with a relation… · on CURRENT: ↵ unlink · ⇧↵ relabel · Esc back
```

- **Pool:** open *and* closed tasks, unlike the Depends-On stage. Closed tasks get their own group, ranked
  below open ones; `done/` archives come last. The existing excludes still apply (templates, `_generated`,
  `_conflicts`, dot-dirs).
- **Fast path:** ↵ links with no label and closes, one keystroke like Depends-On.
- **⇧↵ opens the relation field,** a single input like the Schedule reason field. Suggestion chips show the
  vault's most-used labels with counts, and a live sentence preview *"Fix flaky capture retries — follow-up
  of → Capture * blocks…"* updates as you type. ↵ commits; an empty ↵ commits with no label. ⇧↵ also accepts
  in the Mac app's `!` picker, so the gesture is consistent across clients.
- **Linked from… (⇧L)** is the reverse stage, like ⇧B. Toggling a row adds or removes *this* task on the
  other task's LINKS line, a cross-note write to the authored side. The label prompt is phrased from the
  other task's side: *"Design a retry policy — ‹label› → Fix flaky capture retries"*.
- **On a chip:** Ctrl+Enter / Alt+] act on the linked task, as on dependency chips, and click opens it.

**Cancel stage integration (recommended phase 2).** The `x` stage gains three reasons that open the task
picker:

- *Duplicate of…*
- *Merged into…*
- *Superseded by…*

The one gesture cancels the task, writes the CANCEL LOG reason (`Duplicate of [[…]]`), adds the LINKS entry
with that label, and mirrors it. It replaces the hand-written "Merged into" / "Merged from:" pairs exactly.

### 5.9 Capture grammar (`~` and `~~`)

```text
~<note>:<block-id>[|<label>]     this item's task links to <note>:<block-id>
~~<note>:<block-id>[|<label>]    <note>:<block-id> links to this item's task
<note>   := as for & and * (route or "quoted name")
<label>  := a run of non-space characters without "|"   |   "<text>"  (\" and \\ are the only escapes)
```

**Rules,** modelled on the shipped `*` rules (`capture.md` ≈1585–1604; `dependencies.rs` 263–294):

1. **Placement.** Same leading and trailing modifier runs as `&` / `*`, skipping the same
   `is_trailing_transparent` shapes. A mid-line `~foo:bar` stays body text.
2. **Next byte.** The byte after the sigil is not whitespace, `/` (keeps `~/path` literal), or a digit when
   the token has no `:` (keeps `~5m`, `~2h`, `~5pm` literal).
3. **Strike guard.** A `~` followed by a second `~` is only ever read as the `~~` form, and the rest of
   that token must contain no `~`. This keeps `~~old~~` literal.
4. **Bare sigil.** A bare `~` or `~~` opens the picker as the last token of a line with other text, or the
   first token of a parent line (as `&` allows).
5. **Escapes.** `\~` consumes only the backslash, and only where the unescaped token would have been a
   directive.
6. **Never scanned:** `[[…]]` and backtick spans.
7. **Session operators.** A cross-link after `x` is refused, as `*` is (`operator_relation_error`). `=~…` and
   `x…~K` are unchanged because they are inside other tokens.
8. **Coexistence.** Several `~` / `~~` per item, and `&`, `*`, `~`, `~~` together on one item, are allowed.
   Each item in a bulk capture is judged alone.

**Owners.** These are exactly the `&` / `*` owner spellings: task text creates the owner, `@route+id` names
an existing owner, `@@route+id` is inherited, and bare `@route:id` / `^route:id` alias without linking.
`~~` is what lets an **unroutable** task, such as a reference task, a daily-note task, or a terminal-project
task, link to a routable one. The authored line goes on that task, wherever it lives.

**Examples:**

| Draft | Result |
| --- | --- |
| `Fix flaky capture retries ~bob_done:capture-star\|"follow-up of"` | New task in `mac_inbox.md`. Its LINKS reads `follow-up of [[done/bob_done#^capture-star]]`. The archived target gets no stored mirror. |
| `~sase:retry-design Write the retry ADR #sase` | Leading-run link, no label. |
| `Write the outline ~~sase_blog:prj\|"next step"` | `sase_blog`'s `^prj` LINKS gains `next step [[mac_inbox#^write-the-outline]]`. The new task gets `LINKED FROM: [[sase_blog#^prj]] (next step)`. |
| `@bob+fix-retries ~sase:retry-design\|see` | Edits the existing owner in place. A re-run with a new label reports `relabeled`; the same label reports `unchanged`. |
| `Plan the trip ~5pm` | Literal (rule 2). |
| `Clean ~/Downloads` | Literal (rule 2). |
| `Read ~~old~~ notes` | Literal (rule 3). |
| `Call the bank ~bank` (submitted from the CLI) | Refused: ``"`~` needs a task selection; choose the task to link, or write `\~` for a literal tilde"`` |

**Refusals,** in the style of the `&` / `*` messages:

- an ownerless `~` ("task links need a source: add task text or '@note+task-id'…");
- a self-link;
- a non-task target;
- an invalid label ("relation labels can't contain `[[`, `]]`, `•`, `**` or a line break");
- an unterminated label quote (partial until the end of the line, like a quoted note).

**Shell note.** From zsh, drafts must be single-quoted (`~word` tilde-expands and `|` pipes). The Mac app is
unaffected.

### 5.10 Capture JSON contract (additive only, per the thin-client decision)

- **`capture-parse`:**
  - `task_links[] { raw, direction: "to"|"from", note, block_id, quoted, label, label_range, range }`;
  - spans `task_link_sigil`, `task_link_note`, `task_link_block_id`, `task_link_label_separator`,
    `task_link_label`;
  - needs `task_link` (partial target) and `task_link_label` (open label);
  - `dependency_target`-style `task_link_owner` while ownerless.
- **`capture-complete`:**
  - contexts `task_link_to` / `task_link_from`, with candidates in the `DependencyCandidate` shape plus
    `already_linked` and `existing_label`;
  - open and closed pools, with a `group` of `open` / `closed` / `archived`;
  - context `task_link_label`, with `suggestions[] { label, count, last_used }` built from every LINKS line,
    `done/` included;
  - the replacement range covers the whole modifier, including the sigil, as for `&`, so refetching at
    `replacement.start` returns the unfiltered list. Typing a second `~` changes the context to
    `task_link_from`.
- **`capture` / `--dry-run`:**
  - `cross_link_updates[] { role: "source"|"target", direction, source{path,block_id,text}, target{…}, label, action: "added"|"relabeled"|"unchanged" }`;
  - `linked_from_line_updates[]`, `minted_source_block_id`, `minted_target_block_id`;
  - `mirror_skipped_reason` (`archived_target`, `previous_daily_target`, `malformed_line`).
- **Human output:**
  - `🪢 links to "Capture * blocks existing tasks" · follow-up of`
  - `🪢 linked from "Write the outline" · next step`

### 5.11 Bob Mac Capture

The app decodes and presents bob's contract; it never decides syntax (`mac-capture-is-a-thin-client`). The
work is in about a dozen hard-coded places the audit found:

- `completionNeeds` and `completionSpanKinds`;
- the context dispatch at `CapturePanelModel.swift` ≈3196;
- `CaptureCompletionContext`;
- the span-to-colour mapping;
- `CapturePickerSource`;
- `removePickerTrigger`, whose single-byte check must learn `~~`;
- `rememberRelationshipDisplayName`;
- the relationship copy.

The natural extension point is `DependencyPickerDirection`. Grow it into a relation enum with the cases
`dependsOn` (`&`), `blocks` (`*`), `linksTo` (`~`), and `linkedFrom` (`~~`). Each case needs a `String`
sigil, because `~~` is two bytes. `dependencyPickerQuery` already counts the sigil's UTF-8 length.

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Fix flaky capture retries ~capture st▏                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ 🪢 "Fix flaky capture retries" links to…                                  │
│   ✓  Capture * blocks existing tasks              bob_done:capture-star  │
│   ○  Capture star picker polish                   bob:star-polish        │
│ CLOSED                                                                   │
│   ✓  Capture star spike                           bob:star-spike         │
│ ↩ inserts ~bob_done:capture-star · ⇧↩ add a relation · type ~ to flip    │
└──────────────────────────────────────────────────────────────────────────┘
```

**⇧↩ opens a Relation card.** It reuses the `TaskIDPromptCard` pattern: one field, a live `Inserts …` line,
and Escape returning to the picker through `returnPicker`.

```text
 🪢 Fix flaky capture retries — [ follow-up of▏ ] → Capture * blocks existing tasks
    follow-up of 9 · see 7 · merged into 5 · duplicate of 4 · split from 3
    Inserts ~bob_done:capture-star|"follow-up of"
```

**Live preview rows** come from `cross_link_updates`, alongside the `⛓` / `🧱` rows:

```text
🪢 links to   · follow-up of · Capture * blocks existing tasks · done/bob_done ^capture-star
               archived target · LINKED FROM shown live only
```

**Palette.** A new knot accent for `task_link_sigil`, the route accent for the note, indigo for the block
ID, and muted italics for the label. That keeps `~` visibly different from the grey `pomodoro_*_drop` `~`
spans.

**Keys.** Return and Tab accept; ⇧Return accepts and opens the relation card. That matches the `!` picker's
Shift-Return "accept and continue". Typing `|` right after an accepted token also opens the relation
suggestions. Typing `~` as the first filter character flips the direction, and the header changes to
*"🪢 … links to 'Fix flaky capture retries'"*.

---

## 6. Alternatives considered

| Alternative | Verdict | Reason |
| --- | --- | --- |
| **Render-only backlinks** (virtual LINKED FROM) | Rejected as the primary design; adopted as the rendering layer | No drift, but invisible to vim, `rg`, agents, and the Mac app. The decision record rejected the same shape for dependencies. |
| **Both lines authored** | Rejected | Two sources of truth. Wikidata, Jira inversions, and org-super-links all show the drift. |
| **One bullet per link** (`- 🪢 **LINKS**` header with one child per link) | Rejected for v1 | Bare-link rows are exactly the shape the Task Link, tree-close, strike/restore, and R8 recognisers claim, so they need a new subtree guard in four engines. It is bulkier for the common single-link case. The decision record already rejected per-item bullets for dependencies. **Reopen if** labels routinely become sentences. |
| **Label as wikilink alias** (`[[x#^y\|follow-up of]]`) | Rejected | Without chips, the alias hides the target. Every writer canonicalises aliases away, and an alias means display text, not a relation. Hand-typed aliases are still *adopted* as labels. |
| **Inline field** (`[links:: …]` or Breadcrumbs-style `[follow-up of:: [[x]]]`) | Rejected | The task line is crowded (a rejection already on record). There are no Tasks or Dataview consumers, and arbitrary keys spawn fields. |
| **Typed registry** (Jira-style fixed types with defined inverses) | Rejected | Ceremony and sprawl risk for a single user. Suggestions plus optional inverse *display* get most of the benefit. |
| **Undirected "related" only** | Rejected | Bryan wants direction, and directed edges with an optional label subsume "see". |
| **Fold into DEPENDS ON as "soft" dependencies** | Rejected | DEPENDS ON is load-bearing for Blocked derivation, the Tasks `dependsOn`, and Pomodoro consumption. Mixing in inert edges would reopen settled decisions. |
| **Arrow sigils** `>x` / `<x` (or `~>` / `<~`) | Considered | Direction is visual, but `<5 min`, `a > b`, `->`, and blockquote `>` need heavier guards, and `~>` costs two shifted keys on the common path. `~` and `~~` are Bryan's choice and guard cleanly. |
| **Auto-relate from mentions** (Linear-style) | Rejected for v1 | Implicit edges are exactly the inference the Depends-On redesign removed. Offer an opt-in, dry-run **adoption** of existing "Merged into / Duplicate of / RELATED: / OBSOLETE: See" bullets instead. |
| **A new `bob task link` write CLI** | Deferred | Capture owner mode already gives a CLI with the same planner and preview. |

---

## 7. Rollout

The order follows the Depends-On and BLOCKS lesson: **guards before writers.**

| Phase | Repo | Deliverable |
| --- | --- | --- |
| P0 Contract | bob-cli | `docs/task-links.md`: grammar, registry rows, projection, invariants, and vector tables LK (parse), LW (write), LM (mirror), LC (chips), plus new MC rows. Also a glossary strand and a draft decision record, *"Task Cross-Links Are Inert, Authored On The Source, And Mirrored On The Target"*. |
| P1 Guards | bob-cli + bob-plugins | Every recogniser in Rust, nav, ledger-tools, cycler, and block-id-prompt rejects both lines, ships, and is deployed (`bob plugins sync`) before any writer exists. |
| P2 Core | bob-cli | Parser and canonicaliser; link index (active, previous daily, and `done/` read-only); `reconcile_cross_link_lines`; kill switch; JSON outputs; archive, move, and rename tests; lint warnings. |
| P3 Capture | bob-cli | `~` / `~~` lexer and guards; `capture-parse` spans and needs; `capture-complete` contexts (open/closed pools, label suggestions); staged writer with same-batch mirror and minted IDs; dry-run and human output; `docs/capture.md`. |
| P4 Chips | bob-plugins (ledger-tools) | Live Preview and Reading-view chips from a live cross-link index, label pills, `✓×N`, CSS. |
| P5 Gestures | bob-plugins (nav, cycler, bip) | Task Card `l` / `⇧L` rows, chords, Links and Linked-from stages, relation field and suggestions, counted batches, chip `×`, hand-edit mirror, refusals. |
| P6 Mac | bob-mac-capture | Relation enum, `~` / `~~` pickers, relation card, palette, preview rows, notification copy, `decodeIfPresent` everywhere. |
| P7 Polish | all | Cancel-as-duplicate/merged/superseded; inverse display table; opt-in `bob`-side adoption migration of the ≈60–80 existing hand-written relation bullets (dry-run first). |

Size: comparable to the BLOCKS-line epic. The Rust side is smaller, with no status semantics and no R1–R10
interplay. The UI side is larger, because of the label entry and two pickers in two clients.

---

## 8. Risks, and what would change this recommendation

| Risk | Mitigation | Would change the recommendation if… |
| --- | --- | --- |
| A recogniser in one engine claims the new lines as Task Links | P1 guards plus MC vectors | …guard rollout keeps slipping. Then ship LINKS without the mirror first. |
| Label sprawl ("followup of", "follow up of", "follow-up of") | Suggestions; a case-insensitive near-duplicate lint; an optional one-shot `relabel` | …after a month the vault holds more than about 30 distinct labels. Then add a curated starter list as the default suggestions. |
| Mirror churn or git conflicts | Canonical sort; only the touched targets are written; reconcile heals | …sync conflicts on LINKED FROM lines show up in `_conflicts/`. Then make the mirror render-only. |
| `~` prose collisions | Digit, `/`, and strike guards; `\~`; a teaching error | …refusals annoy Bryan in practice. Then require a `:` before the token counts. |
| Graph-view double edges | Accepted | …Bryan relies on the graph view. Then the mirror could use non-link text, at the cost of `gf`. |
| Feature creep (links that do something) | §5.4 inertness in the contract and the decision record | …a concrete need appears, such as "follow-up of" feeding successor offers. That would be a new decision, never an amendment. |

---

## 9. Questions for Bryan

1. **Naming:** is **LINKED FROM** acceptable instead of BACKLINKS? (RA1.)
2. **Archived targets:** is "no stored mirror in `done/`, live chips only" acceptable, or do you want
   archive mirrors? Archive mirrors would need relaxing the `done/` read-only contract for this one line.
3. **Cancel integration:** should *Duplicate of / Merged into / Superseded by* ship in v1 or as P7 polish?
4. **Inverse labels:** do you want target-side phrasing on chips ("merged from"), and should the table be
   configurable?
5. **Adoption:** should the ≈60–80 existing "Merged into / Duplicate of / RELATED: / OBSOLETE: See"
   bullets be offered for conversion (dry-run first), or left as prose?

---

## 10. Recommended solution

1. **Model:** a *Task Cross-Link* is a directed, optionally labelled, **inert** edge, authored only on the
   source task's `🪢 **LINKS:**` line as `label [[link]]` entries joined by ` • `. Targets are any `#task`
   with a block ID, open or closed, archived included.
2. **Mirror:** `🪢 **LINKED FROM:**` on the target is a generated, canonically sorted projection of every
   LINKS line (active, previous-daily, and `done/` read-only), shaped `[[link]] (label)`. It is never read
   back and never written into read-only notes. Capture and nav update it at once, `bob task reconcile` is
   the authority, and chips render it live. Six invariants pin "always correct".
3. **Obsidian:** Task Card rows `l` Links to… and `⇧L` Linked from…, chords Ctrl+Shift+L and
   Ctrl+Shift+Alt+L, an open-and-closed task pool, ↵ to link, ⇧↵ to link with a relation (with suggestions
   and a live sentence preview), and chip `×` to remove. Then a cancel-stage "duplicate of / merged into /
   superseded by" shortcut.
4. **Capture:** `~note:id[|label]` (this links to that) and `~~note:id[|label]` (that links to this), in the
   `&` / `*` modifier runs, with `~/`, digit, strike, and `\~` guards and the same owner spellings. It is
   additive in the JSON contract. Bob Mac Capture extends its direction-aware picker with two relation cases,
   a ⇧↩ relation card, a knot palette, and preview rows.
5. **Process:** contract and vectors, then guards in every engine, then the Rust core and capture, then
   chips, gestures, and the Mac app, then polish. Record a decision so the inertness rule can't erode quietly.

---

## Sources

**Bob (repo-relative; read locally):**

- bob-cli `docs/task-dependencies.md`: §2.4 managed child lines, §3 identity and link form, §4.3 archive
  targets, §11.8 MC vectors, §14 BLOCKS, §15 reverse stage.
- bob-cli `docs/capture.md`: ≈116–118 and 2601–2609 (`~` drop lists and mnemonic), 1379–1380 (quoted
  notes), 1585–1604 (`*` rules), 1991–2060 (relating existing tasks).
- bob-cli `docs/reference/capture-syntax.md` 26–109 and 765–767.
- bob-cli `docs/task-status-hooks.md` ≈100–115 (narrow `done/` exception) and 298 (the previous daily note
  is read-only).
- bob-cli `docs/projects.md` 372–400 (Task Card); `docs/reference/cli/task.md` (archive repairs links).
- bob-cli `src/native/capture_language/dependencies.rs` (≈246–653, 1037–1299);
  `src/native/capture/blocks_mirror.rs` 1–12; `src/native/task_status_hooks/blocks.rs` 40;
  `src/native/capture_complete/model.rs` 130–163.
- bob-plugins:
  - `plugins/bob-navigation-hotkeys/src/310-task-card-previews.js` 449–553, 664–847;
  - `080-dependency-identity.js`; `081`–`083` (BLOCKS grammar, mint, plan);
  - `250-task-move.js`; `591-blocks-follow-ups.js`; `600-plugin-dependency-mirror.js`;
  - `plugins/bob-ledger-tools/src/140`–`281`; `styles.css` 675–901;
  - `docs/task-card.md`.
- bob-mac-capture:
  - `CapturePanelModel.swift` ≈3196, 3891–3998, 4482–4617, 4959–4972, 5340–5428, 7813–7880;
  - `DependencyPickerPresentation.swift` 5–24 and 353–406;
  - `CaptureRelationshipCopy.swift`; `CaptureRelationshipPresentation.swift` 86–134;
  - `CapturePanelView.swift` 1227 and 1459–1474 (`TaskIDPromptCard`);
  - `CaptureKeyCommandRouter.swift` 388–465;
  - commit `f2a5cb5`.
- SASE memory: `decisions:task-deps-are-depends-on-links`, `decisions:capture-star-blocks-existing-tasks`,
  `decisions:mac-capture-is-a-thin-client`, `decisions:capture-link-drops-blocking-deps`,
  `decisions:task-status-is-derived`, `decisions:task-lanes-are-sticky`; `glossary:task-link`,
  `glossary:task-dependency-link`, `glossary:capture`; `cli_rules.md`.
- Prior research: `research:202610/prerequisite_blocks_line/prerequisite_blocks_line.md` (stored projection
  vs render-only; writer table; invariants).
- Vault survey (read-only, `~/bob`, 2026-10-20): 3,887 `#task` checkbox lines; 1,844 (47%) with `^id`;
  84 DEPENDS ON and 41 BLOCKS lines; ≈120 ad-hoc task references; relation-phrase counts as in §2.1;
  64% of block IDs are hyphenated slugs; 25 word-initial `~` in task lines, all `~/` paths or backticked;
  2 `~~strike~~` in task lines; Ctrl+Shift+L and Ctrl+Shift+Alt+L unbound in `.obsidian/hotkeys.json`.

**External:**

- Jira issue linking: https://support.atlassian.com/jira-cloud-administration/docs/configure-issue-linking/ ·
  https://developer.atlassian.com/cloud/jira/platform/issue-linking-model/ ·
  https://support.atlassian.com/jira/kb/jira-linked-issues-relationships-are-inverted/
- Lüders, Bouraffa, Maalej, MSR '22, link types in Jira: https://arxiv.org/abs/2204.12893
- Linear issue relations: https://linear.app/docs/issue-relations · https://linear.app/changelog/2020-03-04
- GitHub issue dependencies: https://github.blog/changelog/2025-08-21-dependencies-on-issues/ ·
  autolinked backlinks: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/autolinked-references-and-urls
- Obsidian Tasks dependencies: https://publish.obsidian.md/tasks/Getting+Started/Task+Dependencies
- Breadcrumbs: https://publish.obsidian.md/breadcrumbs-docs/Concepts · Juggl typed links:
  https://forum.obsidian.md/t/how-to-create-juggl-typed-links-edge-annotation/44477 · ExcaliBrain:
  https://community.obsidian.md/plugins/excalibrain · Relation Sync:
  https://community.obsidian.md/plugins/relation-sync
- Obsidian `resolvedLinks` (computed backlinks): https://docs.obsidian.md/Reference/TypeScript+API/MetadataCache/resolvedLinks
- Notion relations: https://www.notion.com/en-gb/help/relations-and-rollups · Capacities:
  https://docs.capacities.io/reference/object-properties
- org-edna: https://www.nongnu.org/org-edna-el/ · org-super-links talk:
  https://git.emacsconf.org/emacsconf-wiki/tree/2022/talks/orgsuperlinks.md · discussion:
  https://org-roam.discourse.group/t/org-super-links-with-org-roam/2016
- Taskwarrior virtual tags: https://taskwarrior.org/docs/tags/
- Wikidata inverse properties: https://meta.wikimedia.org/wiki/Community_Wishlist_Survey_2022/Wikidata/Corresponding_properties
- Zettelkasten forum on backlinks: https://forum.zettelkasten.de/discussion/1478/backlinking-is-not-very-useful-often-even-harmful

*Unverified:* Linear's API schema and its rationale for few types, which I saw only in search snippets; and
whether Obsidian core binds Ctrl+Shift+L by default.

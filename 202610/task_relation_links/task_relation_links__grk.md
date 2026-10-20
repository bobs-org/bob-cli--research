# Directed related-task links: one authored line, a generated inverse, and a capture dual of `&`/`*`

> **Research query.** How should Bob add directed links from one Obsidian task to another: a `LINKS` (and `BACKLINKS`) sub-bullet, capture `~` / `~~` with optional relation text, and an Obsidian reverse gesture via `Ctrl+Shift+P`? Critique the plan, lead the design, call out justified requirement adjustments, and recommend a solution that is intuitive, reliable, and beautiful.

**Researcher.** `grk` (independent swarm report).  
**Date.** 2026-10-20.  
**Scope.** Research only. No code, vault, config, or memory files were changed.

---

## Bottom line

**Build it, as a second graph that never blocks.** Bob already has a directed task graph: `⛓️ **DEPENDS ON:**` is the source of truth and `🧱 **BLOCKS:**` is its generated inverse. Related links should copy that shape and none of its scheduling semantics.

The plan as stated is the right *product* (lightweight, directed, captionable, capture-first, visible on both ends) and the wrong *storage model* if both `LINKS` and `BACKLINKS` are authored. Dual-authored inverses are the failure mode the Depends-On redesign and the BLOCKS projection were built to eliminate.

Recommended shape:

```markdown
- [ ] #task Ask plumber about the shutoff! ^ask-plumber
  - 🔗 **RELATED:** [[job#^cleanup]] (same wet wall)
- [ ] #task Do cleanup tasks! ^cleanup
  - ↩️ **LINKED FROM:** [[mac_inbox#^ask-plumber]]
```

- **`🔗 **RELATED:**` is the only authored edge.** One managed child line, plain block links, optional parenthetical caption per link.
- **`↩️ **LINKED FROM:**` is a projection.** Reconcile and every forward writer keep it. Nothing reads it back. Hand edits restore. Deleting every LINKED FROM line loses no edges.
- **Capture `~note:id` / `~~note:id` is `&` / `*` with the roles of a non-blocking graph.** I verified `Fix leak ~job:cleanup` and `Fix leak ~~job:cleanup` are literal task body today (`mode: task`), while `=~2` / `x~1` remain session drop operators. The overload is the same kind already shipped for `*`.
- **Obsidian uses the Task Card, not a new meaning for `Ctrl+Shift+P` itself.** `l` / `Ctrl+Shift+L` edits outbound RELATED; `⇧L` / `Ctrl+Shift+Alt+L` writes the reverse (edits the *other* task's RELATED line). `Ctrl+Shift+P` on a LINKED FROM line skips the card, matching BLOCKS.
- **Related never changes lanes, Blocked, promotion, consumption, successor offers, or `[dependsOn::]` / `[id::]`.**

Live vault size (read-only, 2026-10-20): **508 open tasks, 37 blocked, 27 blocking.** The scheduling graph is small and already loved. Related is the missing *knowledge* graph on the same 508, not a replacement for Depends-On.

---

## Is this a good idea

**Yes.** Three holes in today's model make a second graph worth the recogniser cost.

1. **`&` / `*` mean wait.** The moment of capture is often "this is about that," not "I cannot start until that finishes." Using Depends-On for that produces a backlog that looks Blocked while useful work is still possible. The Depends-On research already warned against treating dep links as "related" or "nice to do first."
2. **The other end is invisible.** A wiki link in a headline (`Find number you need to call to get [[cash#^call-real-id]] going!`) is one-way, mixes into the title, and has no inverse line, no picker, and no caption. Zorg already had a `| LINKS:` metadata field for this; the Bob migration rendered it as a `## Related` section on *reference* notes, never on tasks.
3. **Capture already has the dual-direction pattern.** `&` writes on me, `*` writes on them. Related needs the same pair the first time someone captures a thought while staring at today's agenda. The Mac app is a thin client of bob (`decisions:mac-capture-is-a-thin-client`), so the grammar belongs in bob-cli first.

Mature trackers all split **blocks** from **related**:

| System | Blocking | Related | Inverse |
| --- | --- | --- | --- |
| Linear | `blocks` / `blocked by` (directed) | `related` (shown on both sides) | one stored edge |
| Jira | `blocks` / `is blocked by` | `relates to` / `relates to` | one stored edge; inward/outward labels |
| GitHub Issues | blocking / blocked by | references from mentions | derived |
| Obsidian Tasks 8.4 | `dependsOn` / `is blocking` only | none | field on the dependent |
| Bob today | Depends-On / BLOCKS | none | BLOCKS is a projection |

Obsidian Tasks still cannot navigate from a task to the tasks it depends on outside the edit modal. Bob already beat that for dependencies with chips. Related should reuse that chip family, quieter.

**The idea is good only if related stays soft.** The moment a RELATED line flips `[?]`, the feature has failed: people will be afraid to link.

---

## Critique of the plan as stated

### What to keep

- A visible child line on the task, readable in vim, git, and by agents.
- An inverse that is always correct.
- Capture-time selection of the other task, with an optional caption.
- A reverse gesture: "make *that* task point at *this* one."
- Leading the design toward something calm and chip-rendered, not a wall of bullets.

### Where the sketch fights the architecture Bob just finished

**1. Authored `LINKS` plus authored `BACKLINKS` is two sources of truth.**  
`docs/task-dependencies.md` §14's key invariant is that deleting every BLOCKS line changes nothing about edges; reconcile rebuilds identical bytes. Jira's long-running inward/outward swap bugs, and Tasks 6.1.0 renaming stored `blockedBy` to `dependsOn`, are the same lesson: store one direction, render two. The capture-star research explicitly rejected "author BLOCKS and let reconcile invert it." Related should not re-open that.

**2. `LINKS` is already a Bob word.**  
A **Task Link** is a Pomodoro ledger block link. Zorg **LINKS** was a reference-note related field. Wikilinks are links. A new managed line named `LINKS` will be misread as "the Task Links for this task." Name the *relation*, not the mechanism.

**3. One sub-bullet per target was already rejected.**  
The Depends-On decision record rejected "one bullet per dependency" because unbounded children collide with logs and notes. Fan-in on the inverse is worse. One line per direction, wrapping visually, rendered as chips.

**4. `~` is already a capture operator, and `~~` is already Markdown strikethrough.**  
`docs/reference/capture-syntax.md` teaches **`~` drops**: `=~2`, `=3#bugs~2`, `x~1`. I probed this checkout: those still parse as `pomodoro_start` / `pomodoro_close`. The same probe shows a *whitespace-delimited* `~job:cleanup` on a task item is currently body text, so a task-level `~` is available if it is restricted to the same leading/trailing modifier runs as `&` / `*`. `~~text~~` is strikethrough, and the Depends-On reader already accepts `~~[[#^a]]~~` as a struck link. `~~` as a reverse sigil needs those guards, and it is still the right dual.

**5. `Ctrl+Shift+P` is the Task Card, not a reverse-link command.**  
The card already owns `b` / `⇧B` (Depends on / Blocks…) with dedicated chords `Ctrl+Shift+B` and `Ctrl+Shift+Alt+B`. Putting reverse-related on `Ctrl+Shift+P` itself would steal the property door. The BLOCKS pattern is the one to copy: a card row, a dedicated chord, and `Ctrl+Shift+P` *on the inverse line* skipping the card.

**6. Optional relation text cannot be "trailing prose" on the current one-line parser.**  
Depends-On DP16 (`⛓️ **DEPENDS ON:** [[#^a]] needs review`) is **malformed**. Related captions need a delimited slot (parenthetical after each link), or every captioned line will look broken to the dep parser's cousins.

**7. A Dataview `[related::]` field is not required and would crowd the task line.**  
`[id::]` / `[dependsOn::]` exist because Obsidian Tasks' `is blocked` reads them. Tasks 8.4 has no related index. Skip a derived field until a dashboard needs one.

**8. Recogniser sprawl is the real cost.**  
Adding two managed child lines means Rust, nav, ledger-tools, cycler, and block-id-prompt must *ignore* them as Task Links, Pomodoro links, R8 legacy children, section titles, and tree-close targets. That is the BLOCKS rollout's main risk, paid again. The feature is still worth it; the guards have to ship before any writer.

---

## Requirement adjustments

Each row is a change to the request.

| # | You asked | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | A `LINKS` sub-bullet | One managed **`🔗 **RELATED:**`** child listing outbound targets | "Links" collides with Task Links and zorg LINKS. "Related" is Linear/Jira's word for the soft graph. |
| **A2** | A `BACKLINKS` sub-bullet that stays consistent | **`↩️ **LINKED FROM:**` as a generated projection**, never read back. Readers also accept the labels `LINKS` / `BACKLINKS` and canonicalise them. | Dual-authored inverses drift. Projection is the BLOCKS invariant. Accepting your labels on read keeps hand-edits and zorg muscle memory. |
| **A3** | Display via new sub-bullets | **One line per direction**, links joined by ` • `, optional `(caption)` after a link, **live status chips** in Live Preview / Reading | Per-target bullets bloat. Bare `[[note#^id]]` is the June dep-row problem again; chips are what made Depends-On beautiful. |
| **A4** | Capture `~` for "link current → other" | Keep **`~note:block-id`**, but only as a **whitespace-delimited modifier** in the `&` / `*` leading and trailing runs. Session `=~` / `x~` stay drop lists. | I verified the two `~` worlds already do not share a token shape. Teach them as an overloaded marker, like `*`. |
| **A5** | Capture `~~` for "other → current" | Keep **`~~note:block-id`**, with strikethrough guards: a token that both starts and ends with `~~` stays body (`~~old~~`). Bare trailing `~~` opens the reverse picker. | Same dual as `*` vs `&`. The visual "double tilde = the other way" is learnable. |
| **A6** | Reverse gesture via `Ctrl+Shift+P` | **Task Card `⇧L`**, chord **`Ctrl+Shift+Alt+L`**, and **`Ctrl+Shift+P` on a LINKED FROM line** (skip the card). Outbound is `l` / `Ctrl+Shift+L`. | Matches `b` / `⇧B`. `Ctrl+Shift+P` remains the card. |
| **A7** | Optional relation / link description | **Optional caption per edge**, stored as `[[target]] (caption)` on the authored line, typed in capture as `~note:id\|"caption"` (or the picker footer). Captions never affect status. | Free text, not a closed taxonomy, in v1. Linear's `related` is unlabeled; Jira's extra types (`duplicates`, `clones`) can wait. |
| **A8** | (implicit) related might wait | **Related never blocks, promotes, consumes Pomodoro links, stamps freshness, or writes `[id::]` / `[dependsOn::]`.** Picker copy says so. A target that is already a prerequisite is still allowed and badged "already a prerequisite." | Soft graph. Mint `^block-id` only, the way BLOCKS mints ids without `[id::]`. |
| **A9** | (implicit) both ends authored when using `~~` | **`~~` writes the *other* task's RELATED line.** Current task receives the generated LINKED FROM mirror. One edge. | Same as `*`: the reverse sigil is a convenience writer, not a second store. |
| **A10** | (implicit) membership | Keep related edges **across open and closed tasks**. Freeze nothing on close. Drop a LINKED FROM entry only when the source edge is gone. | Knowledge does not expire when a task is done. BLOCKS drops closed dependents because "frees N" is a live wait count; related is not. |
| **A11** | (implicit) search pool | Picker lists **every task the `&` picker lists**, including completed history and `#hide` (muted). Daily notes, `done/` as *candidates for new* links stay excluded from empty-query ranking but remain findable and valid as targets. | Relating to a finished project is a real capture. |
| **A12** | (implicit) cycles | **Cycles are legal.** Self-links are refused. Repeats are idempotent (`0 added`). | No Blocked derivation, so a 2-cycle is just mutual related. |

---

## Recommended solution

### 1. Vocabulary

- **Related link:** a directed, non-blocking edge from a source task to a target task, stored as a plain Task Link on the source's RELATED line, with an optional caption.
- **RELATED line:** the single managed child that holds a task's outbound related links. Source of truth.
- **LINKED FROM line:** the generated child on a target listing sources that point at it. Projection.
- **Caption:** optional short label on one edge (`same wet wall`, `spawned from review`). Displayed on the outbound chip; inbound chips show it in the tooltip as `Source → this · caption`.

A related link is not a Task Link under a Pomodoro, not a dep link, not a parent (`+query`), not a `#ref` embed, and not an Obsidian backlink pane row.

### 2. Writer form

```text
<indent>- 🔗 **RELATED:** [[#^a]] (caption) • [[note#^b]]
<indent>- ↩️ **LINKED FROM:** [[other#^c]] • [[dir/note#^d]]
```

**RELATED (authored).**

- Glyph `🔗` (U+1F517), space, `**RELATED:**`, space, then links joined by ` • ` (U+2022 with one space on each side).
- After each link, optional space + `(` + caption + `)`. Caption trims, max 40 characters, no `)`, no `[[`, no newlines.
- No embeds, strikes, or title aliases. Caption is the only extra.
- Existing links keep their order; new links append. Never re-sort the authored line (same as Depends-On).
- Empty list deletes the line. No placeholder.
- Link form is the Depends-On shortest form (`[[#^id]]`, unique basename, else path). Links into `done/` keep the explicit `done/` path.
- Position: after the BLOCKS subtree (or the Depends-On slot if neither dep line exists), before `🧩 **Sub-projects:**` and before user children / logs.

**LINKED FROM (projection).**

- Glyph `↩️` (U+21A9 U+FE0F if a VS16 is needed for emoji presentation; pin one code point in the contract vectors), space, `**LINKED FROM:**`, space, then links joined by ` • `.
- No captions on this line. The caption lives on the source.
- Order: sort by canonical link text after ASCII case-fold (BLOCKS rule), so the projection is a pure function of the edge set.
- Membership: every accepted RELATED edge whose target is this task, source resolves to a scanned task, source is writable. Closed sources stay listed. Unresolved / non-task / self edges are omitted and warned on the source.
- Position: immediately after RELATED (or in that slot). Never move an existing line; rewrite in place.
- **Invariant:** deleting every LINKED FROM line in the vault changes nothing about authored edges. The next reconcile rebuilds them.

**Reader tolerance (both lines).** Canonicalise:

- missing glyph; `LINKS` as a RELATED label; `BACKLINKS` as a LINKED FROM label;
- separators `·`, `,`, whitespace;
- aliased / struck / embedded links (strip to the target, keep a caption if it was in the alias *or* a parenthetical — prefer the parenthetical);
- the line sitting in the wrong child slot.

**Malformed:** trailing prose outside parentheticals, half-typed links, separators only. Leave the line, warn, insert no second line.

**Closed registry.** Add both labels to `docs/task-dependencies.md` §2.4 and `docs/reference/vault-format.md`. Every Task Link, Pomodoro, section-title, tree-close, strike/restore, R8, and managed-line parser rejects them (new MC vectors).

### 3. Worked example

Capture, new inbox task pointing at an existing cleanup task:

```bash
bob capture 'Ask plumber about the shutoff ~job:cleanup|"same wet wall"'
```

```markdown
# mac_inbox.md
- [ ] #task Ask plumber about the shutoff! ^ask-plumber-about-the-shutoff
  - 🔗 **RELATED:** [[job#^cleanup]] (same wet wall)

# job.md  (unchanged status, lane, fields)
- [ ] #task Do cleanup tasks! ^cleanup
  - ↩️ **LINKED FROM:** [[mac_inbox#^ask-plumber-about-the-shutoff]]
```

Reverse capture, while the cleanup task is the one in mind — "cleanup should point at this new plumber ask":

```bash
bob capture 'Ask plumber about the shutoff ~~job:cleanup'
```

```markdown
# job.md
- [ ] #task Do cleanup tasks! ^cleanup
  - 🔗 **RELATED:** [[mac_inbox#^ask-plumber-about-the-shutoff]]

# mac_inbox.md
- [ ] #task Ask plumber about the shutoff! ^ask-plumber-about-the-shutoff
  - ↩️ **LINKED FROM:** [[job#^cleanup]]
```

Both drafts leave checkboxes, lanes, Pomodoros, and `[dependsOn::]` untouched. Dry-run preview shows the two child lines and no `consumed_links`.

### 4. Capture grammar

Generalize `scan_modifier_with_sigil` a third and fourth time (`Related` / `RelatedFrom`), same leading/trailing runs as `&` / `*`, skipping `is_trailing_transparent` markers.

**`~` (outbound).**

1. Whitespace-delimited token in the parent leading run or any line's trailing run.
2. Next byte is not whitespace.
3. A token that is only `~` plus digits, glued to a session token (`=~2`, `x~1`, `=#bugs~2`), remains a drop list. Related `~` is never glued to `=` or `x`.
4. Bare `~` is a picker only as the last token of a line that has other text (same as `*`, so a line-initial `~` can stay a possible future bullet oddity without firing). Allow leading-run `~query` after `@route` the way `&` allows a leading run.
5. `\~` escapes where an unescaped token would have been a directive.
6. Optional caption: `|` then either a slug (`~job:cleanup|same-wall`) or a quoted string (`~job:cleanup|"same wet wall"`). The whole modifier is one token; quoted captions may contain spaces.

**`~~` (reverse write).**

1. Same runs.
2. If the token starts *and* ends with `~~` and has body between (`~~old~~`, `~~[[#^a]]~~`), it is strikethrough / body, never a modifier.
3. Next byte after `~~` is not whitespace (except bare `~~` as picker, last token with other text).
4. Caption slot is the same `|…` form.
5. `x~~1` / `=~~2` stay session errors ("use one `~` list"), never related.

**Ownership** reuses `resolve_execution_ownership`. A complete `~` / `~~` with no owner needs `related_target` (same need name as `dependency_target` is too easy to mix up — use a new need). Mode `task_related` for existing-owner items.

**Additive JSON** (`schema_version` stays 1):

- spans `related_sigil`, `related_note`, `related_block_id`, `related_caption`;
- spans `related_from_sigil`, `related_from_note`, `related_from_block_id`, `related_from_caption`;
- per-item `related[]` / `related_from[]` with `{raw, note, block_id, quoted, caption, range}`;
- completion contexts `related_task` and `related_from`;
- `capture-task-id` replacements `related_replacement` / `related_from_replacement`;
- capture output `related_updates[]` with `role: "source" | "target"`, plus `linked_from_line_updates`.

Never put related edges on `dependencies[]` or `blocked_tasks[]`.

**Teaching.** Extend the overloaded-markers table:

| Marker | Context | Meaning |
| --- | --- | --- |
| `~` | glued to `=` / `x` | Drop those Task Links |
| `~` | task-item modifier run | Outbound related |
| `~~` | `~~word~~` body | Strikethrough |
| `~~` | task-item modifier run | Reverse related (write on the other task) |

Mnemonic: session `~` *drops* a ledger link; task `~` *ties* two tasks.

**Shell.** Quote `~` in zsh when it would expand (`bob capture 'Ask plumber ~job:cleanup'`). Same advice already given for `*` / `!`.

### 5. Completion and Mac Capture

Bob owns ranking. Port `capture_link_tasks.rs::rank` (already shared with the Depends-On stage). Empty-query order for `~`: this note, In Progress, Next, today's linked tasks, other open tasks by note, completed history, `#hide` last. For `~~`, put **today's agenda / linked tasks first** — the reverse thought is "I am looking at T."

Each row carries `already_related` / `already_inbound`, `disabled_reason` (self, duplicate in this draft, unencodable path without a block id), and `also_prerequisite` (info badge, still selectable).

Bob Mac Capture stays a renderer (`decisions:mac-capture-is-a-thin-client`):

- Parameterize the existing relationship picker by scope `~` / `~~`, the way `&` / `*` already share one card (`docs/relationship-pickers.md`).
- Headers: **🔗 “Ask plumber…” related to…** and **↩️ “Ask plumber…” linked from…** (reverse: **Choose a task that should link here**).
- Action line: `↩ inserts ~job:cleanup · space adds another ~`. Reverse uses `~~`.
- Optional caption field in the picker footer: empty Return inserts without caption; typing then Return appends `|"caption"`.
- Preview cards from `related_updates[]`: two notes, two child lines, **no red consumption**. A red line would be a bug — related must never delete a Pomodoro.
- `decodeIfPresent` for every new field. Older bob: "This Bob is too old for related-task picks."
- Backspace on an empty filter removes the `~` / `~~` token. Line-initial `~~` is not a bullet placeholder (unlike `*`).

No Swift grammar. `BlockIDRules.swift` stays "Bob is the only authority."

### 6. Obsidian gestures

**Task Card rows** (after Blocks…):

| Gesture | Stage | Writes |
| --- | --- | --- |
| `l` / `Ctrl+Shift+L` | Related… | this task's RELATED line |
| `⇧L` / `Ctrl+Shift+Alt+L` | Linked from… | the *picked* tasks' RELATED lines (they gain this task) |
| `Ctrl+Shift+P` on a RELATED line | Related… directly | owning task |
| `Ctrl+Shift+P` on a LINKED FROM line | Linked from… directly | owning task (reverse writer) |
| chip `＋` / hover `×` | same stages | add / remove that edge |
| palette **Edit task related links** | Related… | no default hotkey |

Stage chrome reuses `bob-cnp`: CURRENT, RESULTS, search, `↑↓ ⇥ ↵ esc`. Footer on Related: `does not block`. Reverse stage title names the source: **Tasks that should link to "Do cleanup tasks!"**.

**One gesture, one transaction** (Depends-On §6.6):

1. Prepare cross-note targets: mint missing `^id` (SB pipeline). Never mint `[id::]`.
2. Commit the authored RELATED line in one editor transaction (one Ctrl+Z) for same-note pairs.
3. Projection write for LINKED FROM: same-note inside that transaction; cross-note as a best-effort follow-up. Reconcile repairs lag.
4. No status, lane, freshness, tag, Pomodoro, or field edits.

Counted `N<Ctrl+Shift+L>` adds the same targets to each source. Reverse counted adds each source onto each picked task's RELATED line.

`!` / Ctrl+Shift+Enter on either new line are refused with the generated-or-managed-line notice. Ctrl+D on RELATED deletes the line (and reconcile drops the mirrors). Ctrl+D on LINKED FROM is restored by reconcile; notice: "Inbound related links come back from the tasks that point here."

Inbox routing: a non-closing related gesture on an inbox task still asks where the task goes, same as other Task Card answers.

### 7. Reconciliation (`bob task reconcile`)

New pass after Depends-On R1–R10 and BLOCKS, before projects-sync anchors.

| # | Situation | Resolution |
| --- | --- | --- |
| RL1 | Well-formed RELATED | Accept the set. Mint missing target `^id`s. Rewrite LINKED FROM on each target. |
| RL2 | No RELATED line, LINKED FROM present | Restore LINKED FROM from inbound sources; do **not** invent a RELATED line. |
| RL3 | Unresolved related link | Heal when exactly one scanned task has that block id; else keep verbatim and warn `unresolved_related_link`. It still does not block. |
| RL4 | Non-task / self | Keep on RELATED as warn (`non_task_related` / `self_related`); omit from LINKED FROM. |
| RL5 | Caption too long / illegal chars | Truncate / strip and canonicalise; warn `related_caption_canonicalized`. |
| RL6 | Malformed RELATED | No change; warn `malformed_related_line`. |
| RL7 | Hand-edited LINKED FROM | Restore the projection. Never create a RELATED edge from a hand-added inbound. |
| RL8 | Duplicate RELATED lines | Keep the first; merge unique targets in first-seen order; delete extras. |
| RL9 | Label aliases (`LINKS` / `BACKLINKS`, missing glyph) | Canonicalise. |
| RL10 | Quiet interval / previous daily note | Same as deps: skip writes there. |

Outputs (additive): `related_line_updates`, `linked_from_line_updates`, `related_warnings[]`.  
Kill switch: `related_links: true` (default on once the vault is migrated; off removes open-task RELATED/LINKED FROM lines and leaves frozen? — **A10 says we do not freeze.** Off deletes both lines on every task and is lossless for LINKED FROM, **lossy for RELATED.** The off switch must refuse, or dump RELATED edges to a report, before deleting authored lines. Recommendation: kill switch removes **only LINKED FROM** (like BLOCKS' lossless off) and leaves RELATED in place. Name it `linked_from_lines` if that is clearer.

`--dry-run` prints the projection. A second live run is a no-op.

### 8. Beauty (chips)

bob-ledger-tools, same family as Depends-On / BLOCKS, quieter:

```text
[ ] Ask plumber about the shutoff!
    🔗 related  ( ○ Do cleanup tasks ↗ job · same wet wall )  ＋
[ ] Do cleanup tasks!
    ↩️ linked from  ( ○ Ask plumber about the shutoff ↗ mac_inbox )  ＋
```

- Miniature checkbox coloured with existing `--task-status-*` tokens.
- Cleaned description ~40 characters; caption after `·` on outbound chips only.
- `↗ note` for cross-note.
- Tooltip: full text, path, status, caption, and `does not block`.
- Done targets: dimmed, not struck (related is not a wait; a strike would look like a cancelled dep).
- Broken: dashed `⚠ ^id not found`.
- Wrap between chips. No line-height change. Cheap `RELATED` / `LINKED FROM` prefilter.
- Without the plugin, the raw line still reads.

Do not put a `frees N` analogue on related. A count badge `n related` is enough; it is information, never a priority signal.

### 9. What this feature never does

These are load-bearing exclusions, not polish:

- Flip a checkbox to `[?]`, or recover one.
- Promote, consume, or park Pomodoro Task Links.
- Stamp `[fresh::]`, `[unblocked::]`, or `[keeps::]`.
- Write `[id::]` or `[dependsOn::]`.
- Close, cancel, or move a target.
- Auto-link a successor on Done.
- Appear in `bob plan` budget as Today.
- Feed the `]s` walk as a new tier.
- Treat `#^ref` embeds as related edges.

If a capture needs a wait, the draft still uses `&` / `*`. Preview of a mixed draft (`Ask plumber &job:parts ~job:cleanup`) shows both graphs.

---

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Dual-authored LINKS + BACKLINKS | Drift. The BLOCKS epic exists so this is not repeated. |
| Render-only inbound chips, no stored LINKED FROM | Fails vim / git / agents / plugin-free reading. Same rejection as BLOCKS render-only. Adopt live chips *on top of* the stored projection. |
| Reuse Depends-On with a `related` caption | Captions cannot unblock, and Blocked would fire. Two graphs, two lines. |
| Put related targets in the task headline as `[[note#^id]]` | Already happens informally; it clutters titles and has no inverse. |
| Nest with `+parent` | Changes residence. Related keeps both tasks where they live. |
| One bullet per link | Rejected for deps; worse under fan-in. |
| Wikilink alias as the caption (`[[#^id\|same wet wall]]`) | Without the plugin, Obsidian shows the caption instead of the target. Parenthetical keeps the raw link readable. |
| Closed taxonomy (`duplicate`, `spawned-from`, `see-also`) in v1 | Linear ships unlabeled `related` plus separate blocking. Jira's extra types can be captions (`dup:`) until a dashboard needs a typed index. |
| `>` / `<` / `\|` / `?` as the sigil | `>` is a redirect and a blockquote; `\|` breaks tables and aliases; `?` is the Blocked checkbox. `~` is free as a *task-level* token. Capture-star research rejected `~` *as a dependency sigil* because drop lists exist; as a *related* sigil the overload is documented and probe-confirmed. |
| Directional `&` (`&>`) | Awkward, and `&` already means wait. |
| Mac-only toggle that rewrites direction | Grammar must be textual in bob. A later `capture-rewrite` flip `~`↔`~~` is fine as a convenience. |
| `[related::]` Dataview field | No Tasks consumer. Task lines are already crowded. Query the child line later if a dash needs it. |
| Graph canvas / OR-groups / lags | Out of scope. Chips plus `gf` on a link are enough. |
| Auto-creating the inverse *authored* edge (`~` also writes their RELATED) | Makes every related undirected and removes `~~`'s reason to exist. Linear's unlabeled related is *displayed* on both sides from one edge; Bob displays inbound on LINKED FROM. Mutual outbound is an explicit second `~` / `~~`. |
| `bob capture` subcommand | Forbidden (`cli_rules.md`). Related is a modifier. A later `bob task relate` is legal (vault-wide rewrite) and is not v1. |

---

## Rollout

Contract and guards before chips, chips before writers, bob-cli before Mac. Same order as Depends-On and BLOCKS.

1. **Contract.** New `docs/task-dependencies.md` section (or a sibling `docs/task-related-links.md` that the dep contract cites), capture-syntax rows, overloaded-markers row, vault-format registry, MC/RL/RC (chip) vectors, glossary term `task-related-link`, decision record. Decide A1–A12 with Bryan where marked as questions below.
2. **Compatibility guards** in Rust, nav, ledger, cycler, block-id-prompt. Sync plugins before any writer exists.
3. **Chips** from a live reverse index, useful on hand-written test lines.
4. **Reconcile projection** for LINKED FROM, with `--dry-run` on the real vault (expect ~0 lines until writers exist).
5. **Capture parse + complete + execute** for `~` / `~~`, including caption, existing owners, and mixed `&`+`~` drafts.
6. **Nav stages + Task Card rows + chords + chip actions.**
7. **Bob Mac Capture** parameterized picker, caption footer, preview, fixtures, `just portable-check`, then macOS typecheck / CI.
8. **Follow-ups, not v1.** `bob query` / dash filter; typed relations; a `capture-rewrite` direction flip; `bob task relate`; showing related on idle-capture agenda rows.

**Pilot.** Add a same-note related link from capture; undo; add a captioned cross-note `~`; add a `~~`; remove via chip `×`; hand-delete a LINKED FROM entry and wait for reconcile; mix `~` with `&` and confirm only `&` blocks; type `~~old~~` in a title and confirm it stays strikethrough; type `=~2` and confirm drop still works.

**Effort.** Roughly capture-star (parse/complete/Mac picker) plus a slimmer BLOCKS (projection, no status engine). Bob-cli M–L, plugins M, Mac S–M.

---

## Open questions for Bryan

1. **Labels.** Writers emit `RELATED` / `LINKED FROM` (recommended). Accept `LINKS` / `BACKLINKS` on read. Prefer your original words on the writer too?
2. **Glyphs.** `🔗` / `↩️` (recommended) vs `📎` / `🔙` vs keeping ⛓️-family only.
3. **Kill switch.** Off removes only LINKED FROM (lossless, recommended) vs also stripping RELATED (needs a dump).
4. **Caption in v1 capture.** Picker footer + `|"caption"` (recommended) vs Obsidian-only captions in v1.
5. **Dedicated chords in v1.** `Ctrl+Shift+L` / `Ctrl+Shift+Alt+L` (recommended, parallel to B) vs card rows only until the gesture is proven.
6. **Closed history in empty-query ranking.** Show completed related candidates behind open ones (recommended, `&` already does) vs open-only until the user types.

---

## Recommended decision, one paragraph

Ship **directed, non-blocking related links** as a second managed-line pair that copies Depends-On/BLOCKS and none of its lane behaviour: **`🔗 **RELATED:**` is the source of truth**, **`↩️ **LINKED FROM:**` is a reconcile-owned projection**, optional `(caption)` per outbound link, capture **`~` / `~~`** as the non-blocking dual of `&` / `*` (session `~` drop lists unchanged, `~~word~~` strikethrough unchanged), and Obsidian **Task Card `l` / `⇧L`** with **`Ctrl+Shift+P` on the inverse line** as the reverse door you asked for. Do not author BACKLINKS, do not name the line LINKS, do not let related block, and do not give the Mac app its own grammar. That is the design that is intuitive (same dual you already type), reliable (one store, self-healing inverse), and beautiful (one wrapping line, live chips, captions as quiet `·` suffixes).

---

## Sources

**Bob contracts (this checkout).**

- `docs/task-dependencies.md` §§1–8, 14 (Depends-On writer, BLOCKS projection, managed-child registry, chips).
- `docs/capture.md` (`&` / `*` dual, consumption, additive JSON).
- `docs/reference/capture-syntax.md` (token index; `~<K>` drop; overloaded markers).
- `docs/reference/vault-format.md` (closed child-line registry).
- `docs/projects.md` Task Card table; `sase/repos/linked/bob-plugins/docs/task-card.md`.
- `sase/repos/linked/bob-mac-capture/docs/relationship-pickers.md`.
- `src/native/capture_language/dependencies.rs` (`scan_modifier_with_sigil`).
- `src/native/ref_library/migrate_zorg/render.rs` (zorg `| LINKS:` → `## Related`).

**Probes (this turn).**

- `bob capture-parse -f json -- 'Fix leak ~job:cleanup'` → `mode: task`, body unchanged.
- `bob capture-parse -f json -- 'Fix leak ~~job:cleanup'` → `mode: task`, body unchanged.
- `bob capture-parse -f json -- '=~2'` → `mode: pomodoro_start`.
- `bob capture-parse -f json -- 'x~1'` → `mode: pomodoro_close`.
- `bob query --tasks "(not done)"` → 508.
- `bob query --tasks "(not done) AND (is blocked)"` → 37.
- `bob query --tasks "(not done) AND (is blocking)"` → 27.

**Memory (audited `sase memory read`).**

- `decisions:task-deps-are-depends-on-links`
- `decisions:capture-star-blocks-existing-tasks`
- `decisions:mac-capture-is-a-thin-client`
- `decisions:unblocked-tasks-are-offered`
- `glossary:Capture`, `glossary:Task Link`, `glossary:Task Dependency Link`
- `cli_rules.md`, `sase_artifacts.md`

**Prior research (audited `sase artifact read`).**

- `research:202610/task_dep_link_depends_on_line/task_dep_link_depends_on_line.md`
- `research:202610/prerequisite_blocks_line/prerequisite_blocks_line.md`
- `research:202610/capture_star_blocks_modifier/capture_star_blocks_modifier.md`

**External.**

- Linear issue relations: `related` vs `blocks` / `blocked by`; `M then R` vs `M then B` / `M then X` ([linear.app/docs/issue-property](https://linear.app/docs/issue-property), changelog 2020-03-04). Arcade's Linear toolkit documents `related` as bidirectional display of one edge, `blocks`/`blockedBy` as directed.
- Jira issue links: one stored edge, inward/outward labels; `relates to` is symmetric copy; `blocks` / `is blocked by` is directed; known inward/outward swap bugs ([Atlassian KB](https://support.atlassian.com/jira/kb/jira-issue-links-are-showing-the-opposite-information-between-the-issue-history-and-the-issue-panel-for-the-blocks-link-type/), [Jira Cloud link types](https://support.atlassian.com/jira-software-cloud/docs/link-issues/)).
- Obsidian Tasks: Finish-to-start `dependsOn` only; no related; known limitation that you cannot navigate to blocking tasks outside the modal ([Tasks User Guide](https://publish.obsidian.md/tasks/Getting+Started/Task+Dependencies), Known Limitations).
- Obsidian Tasks 6.1.0 `blockedBy` → `dependsOn` rename (cited in the BLOCKS research): storing the inverse as authority was a design error upstream also.

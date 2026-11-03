# Moving, merging, and splitting tasks: research (`__mus`)

**Question:** how should bob-cli support moving tasks between notes, merging
tasks into other tasks, and splitting bullets out of a task into new tasks —
across capture syntax, Obsidian keymaps, and the CLI?

**Short answer:** yes, build it — but build it as three thin compositions of
machinery that already exists, not as three new subsystems. The `merged into` /
`merged from` and `split from` / `split into` relation vocabulary is already
shipped (inverse-phrase table, LINKED FROM rendering, relation-line vectors).
Configured cancel labels already auto-cancel a source when a label commits. The
`bob task move` engine already moves whole blocks with vault-wide link repair.
Drawer resolution already creates drawers on demand with catalog spelling. The
missing pieces are small and well-bounded: a `>` capture operator that reuses
the target-run lexer, a content-copy step for merge, a split command that mints
sibling tasks and leaves link stubs, Obsidian presentation over the existing
relation stage, and two CLI verbs under the `bob task` noun. Two of the
proposal's details need to change (the `@note#drawer` destination is
incoherent; `Ctrl+Shift+L` is already taken so merge must live *inside* the
Links stage rather than beside it). Details below.

## 1. What was asked

1. `@a+aid @b+bid > @c` capture syntax — N sources left of `>`, destination
   right of it. `@c#drawer` means "convert the sources to notes inside that
   drawer, creating it if needed".
2. `@c+cid` as a `>` target — merge sources into task `^cid` in `c.md`.
   `@c+cid#drawer` merges into a specific drawer (created if needed).
3. Merge preserves sources: do not delete; add a `merged into` relation from
   each source to the destination and auto-cancel the source. The relation
   must work standalone (e.g. via `Ctrl+Shift+L`) and be configurable like
   other relation effects.
4. `Ctrl+Shift+T` in Obsidian — split one or more top-level bullets out of a
   task into new tasks; replace the bullets with concise text containing
   inline links to the new tasks (so the old task gains `linked from`
   mentions).
5. Full CLI support for all of this.
6. Context: `@file+id` multi-target runs are landing concurrently
   (`plan:202611/capture_multi_target.md`); the design must compose with
   that work.

## 2. What already exists (and why it shrinks this project)

### 2.1 The relation vocabulary is already shipped

`docs/task-relations.md` already defines the exact labels this proposal
needs — they are not new:

- Stored `merged into` renders as `merged from` on LINKED FROM (inverse
  table, §11; chip rule LC5; writer/parser rules LK3, LK5, LW9; LX13).
- `split from` renders as `split into` (same inverse table).
- Relation-line vectors and chip tests already cover `merged into`
  (`scripts/relation-line-vectors.cjs`, `test-ledger-tools-relation-chips.cjs`).

Nobody needs to design label grammar, mirror rendering, or chip display.
The work is to *use* these labels in new operations.

### 2.2 Auto-cancel on commit is already a configured mechanism

`docs/task-relations.md` §§17–18 (CL2/CP2): any label listed in
`relations.cancel_labels` cancels its source at commit time, through capture
`~`/`~~` and through the nav relation writer. `merged into` already appears
in the documented config example — commented out:

```yaml
relations:
  cancel_labels:
    - duplicate of
    - superseded by
    # - merged into
```

So "configurable merged-into that auto-cancels" is one chezmoi default
flip plus the content-copy step, not a new close path. The one-effect-per-label
rule, fail-toward-fewer-cancels parsing, hide-is-not-disable, and catalog
overlay all come for free. Recommendation in §5.3: enable it, don't
reimplement it.

### 2.3 The move engine already does the hard part

`docs/task-move.md` owns whole-block moves with vault-wide repair: canonical
`[id::]`/`[dependsOn::]` updates, wikilink/embed/alias/pathless-link repair,
block-id collision handling, Depends-On/BLOCKS consistency, guarded writes
with parent-last ordering, and `--dry-run` planning. Capture move bullets
(`plan:202611/capture_move_bullets.md`: `- ^id` / `- :id` under a new
project note) already extend this engine with slot placement and
refuse-on-collision. A `>` move into an existing note is the same engine
with intake placement — no new writer required.

### 2.4 Drawer resolution already creates drawers correctly

The Task Drawer glossary strand plus `plan:202611/capture_drawer_bullets.md`:
glued `@route+id#drawer` resolves at commit time through the shared resolver
(exact match, catalog most-used spelling, quoted literals force creation,
near-duplicate/prefix refusal, reserved/ambiguous refusal). `@c+cid#drawer`
should call that resolver, not grow a second one.

### 2.5 In-flight work this design must compose with, not duplicate

- **Target runs** (`plan:202611/capture_multi_target.md`): adjacent
  `@route+id` markers fan out to one item per target. Any `>` design reuses
  this lexer and must state how `>` interacts with it (§4.1).
- **Move bullets** (`plan:202611/capture_move_bullets.md`): draft-order slot
  placement and the `project_task_move` completion context. `>` moves into
  *existing* notes should use intake placement (the `bob task move`
  default), not slot placement — different operation, different rule.
- **Successor offers** (`decisions:unblocked-tasks-are-offered`): closing or
  parking a task may produce offers. Merge-cancel must run through the same
  recovery/offers path as Task Card Cancel so dependents are not silently
  stranded (§6.4).

## 3. Critique — is this a good idea?

Yes, with adjustments. Move / merge / split are one idea from the user's
point of view ("this work lives over there now") and today each requires
hand surgery: cut bullets, paste, repair links by hand, remember to cancel
the husk, retype the drawer title exactly. That hand path is where link rot,
duplicate block ids, and orphaned Depends-On edges come from. Routing all
three through the move engine + relation writer + drawer resolver removes a
real error source.

The risk is grammar sprawl: capture already has ~10 marker families and two
pending grammar bumps. The defense is the one the repo already uses —
**the draft reads exactly like the block it writes**, every new shape gets
a refusal row with teaching copy, and `capture-parse` / `capture-complete` /
`--dry-run` / commit never disagree. If a proposed shape cannot be previewed
exactly, it should be refused, not approximated.

Specific judgments per requirement:

| # | Proposal | Verdict |
| --- | --- | --- |
| 1 | `>` move syntax, N sources | Adopt, with spacing/quoting rules (§5.1) |
| 1b | `@c#drawer` (note + drawer) | **Refuse as incoherent** — drawers belong to tasks, not notes (§4.2) |
| 2 | `@c+cid` merge target | Adopt — this is the core merge shape |
| 2b | `@c+cid#drawer` merge into drawer | Adopt — straight resolver reuse |
| 3 | Keep sources, relate + auto-cancel | Adopt — via `cancel_labels`, not new code (§5.3) |
| 3b | Merge via `Ctrl+Shift+L` | Adopt *inside* the Links stage, not as a rebind — the key is taken (§4.3) |
| 4 | `Ctrl+Shift+T` split with link stubs | Adopt — `Ctrl+Shift+T` looks free; stubs + `split from` compose well (§5.4) |
| 5 | Full CLI support | Adopt as `bob task merge` / `bob task split` (§5.5) |

## 4. Problems with the proposal as written

### 4.1 `>` collides with nothing in the grammar — but with the shell, with Markdown, and with fan-out

`>` is genuinely free in capture-marker space (markers are `@ ^ ! & * ~ =
+ $ % # : /`). The collisions are elsewhere:

- **Shell:** `>` is redirect. `bob capture '@a+x @b+y > @c+z'` must always be
  quoted; unquoted use redirects stdout and captures nothing. Docs and `--help`
  must show quoted forms only, and the teaching error for a missing destination
  should mention quoting.
- **Markdown:** a leading `>` is a blockquote. `>` mid-line is fine, but a
  draft pasted from a quoted context could confuse. Requiring spaces around
  `>` (`sources␣>␣dest`, refused otherwise with a teaching error) keeps the
  operator visible and greppable and avoids glued forms like `@b+y>@c+z`.
- **Fan-out:** after target runs land, `@a+x @b+y <note>` means "file this
  note under both". `@a+x @b+y > @c` must mean something else ("move both
  into @c"). The disambiguator is the `>` itself: a run *followed by* `>`
  is a source list, never a fan-out. State this in one sentence in the
  grammar contract and test the pair explicitly
  (`@a+x @b+y note` vs `@a+x @b+y > @c+z`).

### 4.2 `@note#drawer` as a move destination is undefined

Drawers are children of *tasks* (`REQUIREMENTS` under `^cid`), not of notes.
`@c#drawer` therefore cannot name a filing location: there is no task whose
drawer it is. The proposal's gloss — "tasks should be converted to notes and
moved to that drawer" — only makes sense once a task is named. Recommend:

- `@a+x @b+y > @c` — move tasks **as tasks** into note `@c`
  (`## Tasks` intake, LHS order).
- `@a+x @b+y > @c+z` — merge into task `^z` (as notes).
- `@a+x @b+y > @c+z#drawer` — merge into that drawer (created on demand).
- Refuse `@c#drawer` after `>` with teaching copy pointing at `@c+z#drawer`.
  (On the LHS, glued `#drawer` keeps its existing drawer-bullet meaning and
  never participates in `>` parsing.)

This also resolves "convert to notes": in the merge shapes the sources'
*content* (notes and drawer notes) is copied as notes under the destination;
the sources themselves stay tasks and are cancelled with `merged into`.
Nothing is "converted" — a word that would otherwise need a definition for
checkboxes, fields, logs, and children. §5.2 defines exactly what copies.

### 4.3 `Ctrl+Shift+L` cannot be the merge keymap — it is the Links stage

`Ctrl+Shift+L` already opens Links-to (and `Ctrl+Shift+Alt+L` opens
Linked-from); counted `N Ctrl+Shift+L` is batch relate. Rebinding it to
merge would destroy the generic relation surface the merge itself depends
on. The proposal's instinct is right but the mechanism is inside-out:
merging *is* committing a `merged into` relation through the existing stage.
What merge needs is not a key but a **merge-aware commit path in the Links
stage**: when the picked/typed label's key is `merged into` (or any
cancel-label — generic, not hardcoded), the preview additionally shows the
content copy (which notes/drawers will land where) and the commit performs
relation + copy + cancel in one undo. No new keymap; no special case for one
label beyond the already-configured effect.

### 4.4 Auto-cancel must be the configured effect, not a merge hardcoded step

Hardcoding "merge cancels" duplicates §§17–18 and forks the semantics
(what does unlinking `merged into` do? what does relabel *away* do? does
hide disable it?). The configured path already answers all of these:
relabel away never un-cancels; hide is not disable; one-effect-per-label is
enforced. Merge should therefore be defined as *"commit a `merged into`
relation + copy content"*, where the cancel arrives — or not — exactly as
it does for `duplicate of` today, per the user's config. The only product
decision is the default: ship `merged into` enabled in chezmoi's
`relations.cancel_labels` (one line uncommented) so the out-of-box behavior
matches the proposal, while a user who removes it gets relate-without-close.

### 4.5 Split's replacement text needs a contract, not just "concise text"

"Replaced by concise text with inline links" leaves four behaviors
unspecified: where the new tasks live, what they are titled, what the stub
says when many bullets split at once, and whether the relation is stored or
only mentioned. Mentions are derived and inert (glossary `task-mention`); a
stub with `[[#^new]]` links gives LINKED FROM `(💬 mentions)` rows for free —
good for display, useless for queries. Recommend storing `split from` on
each new task *and* writing link stubs, so the old task shows both the
`split into` inverse chip (queryable) and the mention row (readable). And the
new tasks' home needs a default: same note, appended after the source block
in split order (least surprising; same-note links never need path repair).

## 5. Recommended design

### 5.1 Capture grammar: `sources > dest`, spaces required

```text
@a+x @b+y > @c
@a+x @b+y > @c+z
@a+x @b+y > @c+z#requirements
```

- LHS: a target run — two or more adjacent `@route+id` markers (reuse the
  `capture_multi_target` lexer verbatim, including per-member `!` refusal:
  toggles make no sense in a source list). Exactly one source (`@a+x > @c`)
  is allowed — uniformity beats saving a sigil.
- `>` : exactly one, with required spaces on both sides; otherwise
  `split_capture_targets`-style teaching refusal. A second `>` is refused.
- RHS: exactly one destination — `@route` (note move), `@route+id`
  (merge), or `@route+id#drawer` (drawer merge). No bullets-after-`>` on the
  parent line; child bullets under a `>` item are refused (there is nothing
  for them to nest under — the item has no note of its own). This keeps the
  two-level authored grammar intact.
- LHS markers keep per-member drawer suffixes? No — refuse glued `#drawer`
  on LHS members with teaching copy. Source drawers move with the block
  (move) or copy with the content (merge); suffixes there mean something
  else today and would mislead.
- Destinations resolve like their single-marker equivalents today
  (basename ambiguity, missing note/block, closed destination, `^prj`
  rules). A destination naming one of the sources is refused ("itself").
- Grammar revision bump + `feat(capture)!` with BREAKING CHANGE footer, per
  the release-train decision — this changes the meaning of existing text
  (`>` was literal prose). One bump shared with target runs if they land in
  the same train; never two bumps for one train.

### 5.2 Semantics: move copies blocks, merge copies content

**Move** (`> @note`): `bob task move` semantics exactly — whole blocks
(children, logs, drawers, IDs) relocate to `## Tasks` intake in LHS order;
link/identity repair vault-wide; block-id collision **refused** in capture
(never silently renamed, per the move-bullet precedent); destination
`^prj`-blocked rule applies (only `[?]` tasks move in); sources stamped
fresh; no lane/status/ledger changes; needs `reconcile` hint when reported.

**Merge** (`> @note+id[#drawer]`): for each source in LHS order —

1. Copy its plain notes (and, recursively, drawer notes when no drawer
   target is given) as notes under the destination (or into the named
   drawer, creating it with catalog spelling via the shared resolver).
2. Never copy: checkbox state, priority, schedule, `[fresh/keeps/unblocked]`,
   Depends-On/BLOCKS lines, LINKS lines, logs. (A merge that inherited the
   source's Blocked-ness or schedule would corrupt the destination; state
   this as a rule, not an implementation note.)
3. Append one `merged into [[dest]]` entry on the source's LINKS line.
4. Commit — the configured cancel label cancels the source exactly as Task
   Card Cancel would, including dependent recovery and successor offers.
5. Destination task stamped fresh once (content arrived); sources untouched
   by freshness (closed rows stay frozen).

Refusal table (capture rows, CLI mirrors): closed/nested/`^prj`/ambiguous
sources; missing/ambiguous destination; destination-is-source; drawer
reserved/ambiguous/near-duplicate (same resolver errors as drawer bullets);
`^prj` destination allowed (its drawers are `##` sections — the resolver
already handles this); project-blocked destination follows the move rule.

### 5.3 Relations: configure, don't code

- Uncomment `merged into` in chezmoi's default `relations.cancel_labels`
  (docs `task-relations.md` CL2 example already anticipates this).
- Merge commit goes through the standard relation writer, so
  `relation_cancel` output, `configured` overlays, and suggestion ranking
  apply unchanged.
- Standalone merge in Obsidian = Links stage (`l` / `Ctrl+Shift+L`) with
  label `merged into`, plus the merge-aware preview/copy step from §4.3.
  Counted `N Ctrl+Shift+L` with a `merged into` label merges N sources into
  one target — the batch fall-out of existing counted-relate behavior.
- `bob relations list -a` shows `merged into` with `cancels_source: true`
  once configured; no new flags.

### 5.4 Obsidian split: `Ctrl+Shift+T`, same note, stub + stored relation

- Keymap: `Ctrl+Shift+T` ("split **t**ask bullets"). No existing binding
  found in `bob-navigation-hotkeys` or `block-id-prompt` sources; confirm
  against the vault vimrc and Obsidian defaults during implementation, and
  reserve the palette command `Bob: Split bullets into new tasks` for
  discoverability.
- Selection: one or more top-level bullets of the task under the cursor
  (cursor on a bullet = that bullet; visual selection = the covered
  top-level bullets; nested children travel with their parent). Managed
  lines (Depends-On, BLOCKS, LINKS, logs) are never splittable — refused
  with the managed-line notice pattern.
- Write, one undo: for each split bullet in order, mint a new open task in
  the same note directly after the source block (new block id; title = the
  bullet's text; children preserved; no freshness stamp — creation never
  stamps). Each new task gets `split from [[source]]` on its LINKS line
  (so the source shows queryable `split into` chips). The source bullet is
  replaced by a stub: `- Split into [[#^new1]] · [[#^new2]]` (one stub per
  split bullet, links in creation order), which additionally yields inert
  `💬 mentions` rows on LINKED FROM.
- Preview: Task Card-style confirm showing titles + destination, with the
  teaching line for empty selection.
- Counted `N Ctrl+Shift+T` splits the next N top-level bullets — symmetry
  with the repo's counted-key conventions.

### 5.5 CLI: two verbs under `bob task`, full protocol parity

`bob task` is reserved for vault-rewriting task commands (cli_rules), so
both verbs nest there — and nothing nests under `bob capture` (its TEXT
would swallow it):

```text
bob task move SRC DEST (-b ID | -m TEXT)...        # exists; add --into-drawer? no — see below
bob task merge SOURCES... --into NOTE+TASK [--drawer NAME] [--dry-run -f human|json]
bob task split NOTE (-b ID | -m TEXT) --bullets N... [--dry-run -f human|json]
```

- Prefer explicit `--into` / `--drawer` long options over smuggling `>` and
  `#` through shell quoting; the capture `>` form and the CLI long-option
  form share one planner. Give both long options short aliases per
  cli_rules (`-i`, `-d` if free — check collisions at implementation).
- `merge` output mirrors `move`'s JSON shape (`ok`, `moves[]`-like
  `merges[]`, `repaired_files[]`, `needs_reconcile`, `git.*`, `error`) plus
  the relation rows written. `split` output lists minted block ids and stub
  lines. Both get `--dry-run` planners and the same guarded-write/commit
  discipline as `move`.
- Capture protocol parity (frozen names grow additively only): `capture-parse`
  reports the `>` spans, needs, and diagnostics; `capture-complete` offers
  source-task rows and destination-task rows through existing contexts;
  `capture-rewrite` keeps `>` text stable; `--dry-run` preview shows
  `would move N tasks` / `would merge N tasks into ^z` bands plus the
  cancel-label consequence (`· cancels sources (merged into)` when
  configured, `· relates only` when not). Mac stays a thin client rendering
  bob's spans and preview bands.

### 5.6 Beauty and intuition checklist (acceptance bar)

- The draft reads like the block it writes: `- ^id` already proved the
  pattern; `A B > C` reads as "these become part of that".
- Ghost titles after `>` destinations and drawer rows, exactly like the
  move-bullet picker; a preview band (`↪ Merges 2 tasks into ^z · 1 drawer
  created`) in Mac and a `would merge` block in `--dry-run`.
- One teaching error per refusal, naming the fix
  (`split_capture_targets` precedent).
- LINKED FROM on a merged destination reads `merged from (✕ S)` (already
  shipped, LC5) — the history of a merge is visible in English with no new
  UI.
- LINKED FROM on a split source reads `split into (○ N)` via the stored
  inverse plus the human stub — queryable and readable, no new UI.

## 6. Rollout and risks

1. **Order:** land `capture_multi_target` first (the run lexer is the LHS
   parser), then `>` move, then merge copy+cancel, then split. Each phase
   carries its own grammar-revision accounting so the train takes exactly
   one bump.
2. **Cancel-offer audit:** verify that a merge-triggered cancel emits the
   same successor/recovery behavior as Task Card Cancel (dependents offered,
   never auto-linked). If Cancel currently skips offers, that gap — not the
   merge — is the fix, shared with `duplicate of`.
3. **Drawer-spelling surprise:** catalog most-used spelling can rename a
   typed drawer (`#req` → `REQUIREMENTS`). Merge inherits this; the preview
   must show the resolved spelling before submit.
4. **Bulk-fanout confusion:** the first release note should show the
   minimal pair (`@a+x @b+y note` files twice vs `@a+x @b+y > @c+z` merges
   once). Consider a first-month lint when a `>`-less run names tasks that
   look merge-intended — or deliberately do not; decide in the plan, not in
   code review.
5. **Mac scope:** preview bands + ghost titles only; no grammar in the
   client (thin-client decision holds).

## 7. Open questions for Bryan

1. Should `merged into` be enabled by default in chezmoi (my recommendation:
   yes), or stay opt-in with merge previewing "relates only" until enabled?
2. Should `> @note` moves stamp fresh like move bullets do (recommendation:
   yes — arrival is confirmation)?
3. Should split's new tasks live in the same note always (recommendation:
   yes for v1), or offer a destination note via the `Ctrl+Shift+M` picker?
4. Is refusing `@note#drawer` after `>` acceptable, or is there a task you
   have in mind whose drawer `@note#drawer` means (recommendation: refuse)?

## Sources

- `docs/capture.md`, `docs/task-move.md`, `docs/task-relations.md`
  (§§3, 10, 11, 17–20), `docs/task-dependencies.md` (§12)
- `plan:202611/capture_multi_target.md`, `plan:202611/capture_move_bullets.md`,
  `plan:202611/capture_drawer_bullets.md`,
  `plan:202611/capture_relation_successors.md`
- `decisions:task-deps-are-depends-on-links`,
  `decisions:unblocked-tasks-are-offered`, `decisions:task-lanes-are-sticky`,
  `decisions:mac-capture-is-a-thin-client`,
  `decisions:capture-bullets-mirror-the-task-block`
- `glossary:task-drawer`, `glossary:task-mention`, `glossary:task-relation`,
  `glossary:task-link`

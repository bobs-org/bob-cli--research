# Drawers Without ALL-CAPS: Research & Recommended Design

**Researcher:** mus · **Date:** 2026-11-22 · **Swarm:** 5-researcher drawer study
**Repo base:** bob-cli master (workspace `bob-cli_19`), vault-adjacent docs + `src/native`

This report answers: how should bob let drawer bullets keep their true/intended
capitalization instead of forcing ALL-CAPS? It covers the marker design, why
`#foo` tags are (mostly) ruled out, how to reuse the notebook H2 machinery,
rendering, the lossless-project-note goal, and the conflict with the in-flight
`bob-cli-on` epic. It ends with a concrete recommended solution and a sequencing
plan.

---

## 1. How drawers work today (what must change)

### 1.1 On-disk shape

A task drawer is a direct non-checkbox ALL-CAPS child bullet of a `#task` line,
with plainbullets nested beneath it. Glossary definition (`glossary:task-drawer`,
read via `sase memory read`): *"A direct non-checkbox ALL-CAPS child bullet of
a `#task` line, with its notes nested beneath it."* Managed lines (Depends-On,
BLOCKS, LINKS, Schedule/Work/Rotten/Cancel logs, `TASKS`) are never drawers.

The predicate lives in `src/native/capture_drawers.rs`:

- `parse_drawer_title(body)` — trims the bullet body, rejects checkbox rows,
  accepts only `is_drawer_title(title)`.
- `is_drawer_title(title)` → `is_title(title, TitleGrammar::Drawer)`: lead char
  must be `A-Z` or `0-9` (`is_drawer_title_first`); rest from `A-Z 0-9 space tab
  & ' ( ) , . / -` plus `? ! ;` anywhere after the lead and `:` only as the final
  character; at least one `A-Z`. Lowercase, `+`, `#`, unicode, and most
  punctuation are rejected. Tests at the bottom of the same file pin this
  (`"WHAT'S NEXT"` ok, `"C++"` / `"BOB+SASE"` rejected).
- Key/slug: `drawer_key(title)` = collapsed-whitespace uppercased;
  `selector_slug(title)` (`src/native/capture_language/line.rs`) = lowercased,
  hyphen-joined. Keys are the identity; titles are display.

Project-note `##` sections are the `^prj` analogue: `project_h2_drawers()` in the
same file lists eligible `##` headings (excluding reserved + structural keys via
`is_reserved_drawer_key` / `is_structural_h2_key`), each with `key`, `slug`,
`title`, line, and entry count. `is_prj_parent()` gates this path (trailing
`^prj` anchor + `#task`).

`src/native/task_block_layout.rs` (the one place that answers "where does a new
child go?", `docs/task-requirements.md` §3) puts drawers in zone 5 (`NOTES`
first, then authored order). `NOTES_TITLE = "NOTES"`. The first-req scoop files
loose notes into `NOTES`. `src/native/task_drawer_rename/mod.rs`
(`bob task rename-drawer OLD NEW`) renames task drawers bottom-up plus eligible
`##` sections, writing NEW in catalog casing (ALL-CAPS drawer / Title Case
section via `format_project_section_title`).

### 1.2 Capture grammar for drawers (two entry points)

Per `docs/capture.md` grammar table, `glossary:task-drawer`, and
`decisions:capture-bullets-mirror-the-task-block` (read via memory):

1. **Glued selector:** `#` glued after `@route+id` always names a drawer:
   `@foo+bar#requirements`, `@foo+bar#"FUTURE WORK"`, plus `--drawer TITLE`.
   Resolved at commit time by `resolve_drawer_for_write`-family logic in
   `src/native/capture_drawers.rs` (~lines 1000–1175): exact/slug match →
   ambiguous refusal → reserved refusal → near-duplicate guard (strict prefix or
   edit-distance-1 refuses with a `did you mean …? write #"INTENDED" to create`
   teaching error) → create from catalog spelling or uppercased-spaced key.
   Quoted literals force creation verbatim (modulo `normalize_drawer_literal`,
   which uppercases). `capture-complete` (`src/native/capture_complete/drawers.rs`)
   offers task drawers → catalog recents → one `new` row, with `replacement` text
   equal to what commit would receive (`#slug` / `#"TITLE"` for glued,
   bare ALL-CAPS title for bullets). Shell completion only spells glued selectors.
2. **First-level bullet shortcut:** `- #future-work` (or `- #"TITLE"`) at a
   first-level bullet start. Lexer: `src/native/capture_language/drawer_bullet.rs`
   (`scan_leading`, `scan_first_level_line`, `DrawerBulletHit`,
   `DrawerBulletTarget`, `classify_target`). The comment block is explicit: a
   bullet-start `#` is *never* a type marker; nested `- #fix` still types; `#` +
   digit / `##` / `#-` stay prose; `\#` keeps a literal. An ALL-CAPS first-level
   bullet with nested notes is a drawer bullet and merges into the existing
   drawer under a note-less `@route+id` (`is_multi_note_sub_bullet`). The bullet
   menu inserts the bare ALL-CAPS title. `decisions:capture-bullets-mirror-the-task-block`
   locks this in: one resolver serves menu, `capture-parse`, dry-run, and commit.

Notebook routes reuse the same `#` position with different meaning:
`src/native/capture_language/section_bullet.rs` + `notebook.rs`. On a notebook
route-only list or `%n` create body, `- #Section` with nested one-line notes
files those notes under `## Section`; the selector line is never a note and
never a drawer. Resolver `resolve_notebook_section()` (~`notebook.rs:250-339`):
quoted exact → create verbatim; unquoted exact title (case-insensitive) → unique
slug → ambiguous → near-miss hint (`no section … did you mean #slug?`) → create
via `format_notebook_section_create_title()` which preserves typed capitals in
any word containing an uppercase letter (`#API-keys` → `API Keys`) and Title
Cases the rest (`#git` → `Git`). `docs/notebooks.md` §Capture documents the full
contract including `notebook_section_ambiguous` / `notebook_section_near_miss`.

So the prompt's instinct is right: the notebook H2 machinery is the closest
existing model for case-preserving drawer creation, and the two lexers already
share the opener predicate (ASCII letter / `"` / `“` / bare `#`).

### 1.3 Rendering today

ALL-CAPS *is* the distinctiveness. No glyph, chip, or ink distinguishes a drawer
row in CLI human output, Obsidian, or Mac beyond the shouting itself (plus
indentation/position). `docs/task-tag-marks.md` (teal `⌗` identity hash) and
`docs/blocked-marks.md` show the house style for distinct-but-quiet marks, but
no drawer equivalent exists. Any mixed-case design must add one (see §5).

### 1.4 The `#foo` question ("does this rule out tags?")

Mostly yes, but precisely scoped — worth stating carefully because the prompt
hedges ("I think this rules out #foo tags, right?"):

- A **free-standing `#foo` at an item edge types the task**
  (`src/native/capture_language/type_marker.rs`, `docs/capture.md` "Typing tasks
  with `#<type>`"). A drawer marker that looks like a type token anywhere the
  type scanner runs would retype the parent instead of naming the drawer.
- The **one safe `#` position is the first-level bullet start**, which the
  drawer/section lexers already claim *before* the type scanner: `- #future-work`
  never types (per `drawer_bullet.rs` header + decision
  `capture-bullets-mirror-the-task-block`). Nested `- #fix` still types.
- Consequence: a drawer marker spelled as a *trailing* tag (`- Meeting notes
  #drawer`), an inline tag (`- #Meeting notes…`), or a bare `#foo` child line
  would collide with typing and with Dataview/tag search (every `#foo` becomes
  a vault-wide tag, pollutes tag panes, and invites accidental renames). A
  *leading* `#` on the drawer header bullet itself does not — it is already
  reserved. So: **rule out `#foo` tags as drawer markers everywhere except the
  already-reserved bullet-start `#` slot**, where `#` is a marker/sigil, not a
  tag.

---

## 2. Does this conflict with the (WIP) `bob-cli-on` epic?

Yes — directly, in files, vectors, and memory. Verified via
`sase bead read bob-cli-on` (IN_PROGRESS epic, "Task requirements (reqs)"):

- **What on is:** reqs are checkbox children without `#task`, drawn as quiet
  `⌗⌗`, met at close, never ticked early; canonical block order beside a `NOTES`
  drawer; promotion maps reqs→tasks and notes→notes; twins in bob-cli /
  bob-plugins / Mac byte-identical through shared vectors. Closed phases include
  `on.1` recognizer, `on.2` readers/writers, `on.3` block-layout + writers,
  `on.4` `bob task tidy`, `on.5` `bob task rename-drawer`, `on.6` capture grammar
  + NOTES routing, `on.13/14` Mac typing/nesting, `on.16` migration.
- **Still IN_PROGRESS (the collision surface):** `on.11` successor card +
  carry-now, `on.12` promotion (reqs→`## Tasks`, notes + NOTES→`## Notes`, even
  on requirement-less tasks), `on.15` Mac Pull-In card, `on.17` memory records.
  `on.12` explicitly owns `glossary:task-drawer` edits ("Update the Task Drawer
  strand for NOTES, requirements, and the retired REQUIREMENTS drawer") and
  `decisions:capture-bullets-mirror-the-task-block` amendments; `on.17` closes
  them out.
- **File overlap:** any drawer-grammar change touches exactly what on.* just
  built or still owns: `capture_drawers.rs` (predicates, resolvers, catalog),
  `capture_language/drawer_bullet.rs` + `section_bullet.rs` + `notebook.rs` +
  `model.rs` (`DrawerSelector`), `capture_complete/drawers.rs`,
  `task_block_layout.rs` + `writers.rs` + `tidy.rs`, `task_drawer_rename/*`,
  `capture/plan.rs` + `commit.rs` + `sub_bullet.rs`, the RL/RW shared vectors in
  `tests/fixtures/task_reqs/` (byte-copied into
  `plugins/task-status-cycler` + nav twins, enforced by
  `scripts/test-task-reqs-twin-copies.cjs`), plus `bob capture-drawers`,
  `capture-parse` spans, shell completion, `docs/capture.md`,
  `docs/reference/capture-syntax.md`, `docs/reference/json-outputs.md`, and the
  Mac contract (`docs/capture-previews.md`, `docs/protocol.md` — themselves
  noted as stale in on-note #3).
- **Recorded hazards already pointing at drawers:** on-notes #2/#4 describe the
  `^prj` NOTES-home bug (`## NOTES` with tab-indented bullets, duplicated
  headings, `ensure_drawer` never finding H2s) and demand a *decided* `^prj`
  notes home; note #6/#7 record Mac concealment and dry-run preview drift that
  any new drawer glyph/marker must not repeat.

**Sequencing rule:** do not land a drawer-grammar change while `on.11/12/15/17`
are open. Either (a) queue this work as the next phase/epic after `on` closes
(recommended), or (b) explicitly re-scope `on.12` to include it — but (b) means
reopening closed `on.3/4/5/6` vectors and the twin-copy contract mid-flight,
which is the most expensive option. At minimum: no edits to
`glossary:task-drawer` or `decisions:capture-bullets-mirror-the-task-block`
until `on.17` lands (its charter claims those notes), and no changes to block
order, first-req scoop, promotion, or successor-card verdicts until `on.11/12`
land. A short "drawer epic" branched from post-`on` master with its own
`bob task tidy` + rename + twin-copy updates is the clean shape.

---

## 3. Critique: is this a good idea?

**Yes — with the marker + migration treated as the project, not the predicate.**
The predicate change (allow lowercase) is trivial; the product change (keep every
surface unambiguous and beautiful) is not. Assessment:

**Why it is worth doing:**

- **Lossless intent.** Today `API Design`, `Q&A`, `coc.nvim`, `Non-Goals`, and
  any sentence-case name (`Meeting notes`) cannot be drawer titles at all, or
  are forcibly shouted (`format_project_section_title("API DESIGN")` →
  `"Api Design"`). True case is the stated goal and a genuine prerequisite for
  the larger "lossless task representation" aim: drawer ↔ `##` promotion today
  folds case (`FUTURE WORK` ↔ `Future Work`), so round-trips are lossy by
  construction.
- **Beauty.** A vault full of shouting is the opposite of the calm task-block
  aesthetic the reqs work just established (quiet `⌗⌗`, calm lanes). Mixed-case
  drawers with a small, consistent mark will read better than ALL-CAPS.
- **Namespace growth.** The catalog (`BTreeMap<String, DrawerCatalogRecord>`
  with `spellings` + `notes`) already anticipates multiple spellings per key;
  case-preserving titles use it as designed instead of fighting it.

**Why it is risky (and what the plan underweights):**

1. **ALL-CAPS is load-bearing distinctiveness.** Remove the shouting and a
   drawer header (`- Meeting notes`) is visually identical to a loose note with
   nested detail (`- Meeting notes` + `  - …`). The prompt correctly demands a
   replacement signal, but "render distinctly" is not a nice-to-have — without
   it the task block becomes ambiguous to the *reader*, not just the parser.
   This needs a designed mark in three renderers (CLI human, Obsidian
   LivePreview/reading, Mac) plus Dataview-adjacent surfaces, all gated on the
   same vectors as reqs.
2. **Corpus + ecosystem inertia.** Every existing drawer is ALL-CAPS; Dataview
   queries, `grep`s, plugin tests, Mac snapshots, and Bryan's muscle memory
   (`- #future-work` → `FUTURE WORK`) assume it. A flag-day rewrite of the
   vault is unacceptable; the design must read old + new indefinitely and write
   new only for new drawers (explicit migration opt-in).
3. **Grammar surface is wider than it looks.** Drawers appear in: glued
   `@route+id#sel` selectors, bullet shortcuts, `capture-parse` spans,
   `capture-complete` rows, `capture-drawers` output, shell completion, `%n`
   notebook-create bodies (ALL-CAPS first-level bullets seed Title Case `##`),
   rename-drawer, tidy, promotion, successor offers, and pull-in. "Fix the
   capture syntax" means all of them, plus JSON (`sub_bullets`, `drawer`
   objects) and the Mac thin-client contract (Mac never parses — it renders
   what bob returns, per `decisions:mac-capture-is-a-thin-client`).
4. **The lossless goal needs scoping.** Case-preserving drawers are necessary
   but far from sufficient for "convert any project note to/from a task without
   data loss" (order zones, req subtrees, logs, links, block IDs, H2-vs-drawer
   duality on `^prj`, checkbox bytes, fenced content). Ship drawers as a
   stepping stone explicitly, not as the lossless milestone.

**Verdict:** proceed, but as a sequenced epic after `bob-cli-on`, with the
marker decision made first and the renderer designed alongside the grammar (not
after).

---

## 4. Design space for "some other way to mark these sub-bullets"

Constraint recap: the marker must (i) not type the task (no free `#foo`), (ii)
not become a vault tag, (iii) survive copy/paste and shell quoting, (iv) work
in glued one-liners *and* multi-line drafts, (v) be completable, (vi) read
beautifully.

| Candidate | Shape (stored bytes) | Pros | Cons | Recommendation |
|---|---|---|---|---|
| **A. Persistent bullet-start `#`** | `- #Design Notes` + `  - note` | Reuses notebook lexer + completion + resolver; already non-typing at bullet start; visible but quiet; no new sigil; works glued (`@r+id#"Design Notes"`) and in bullets | Changes today's "shortcut completes to bare title" contract; `#` reads tag-ish to newcomers (mitigate with glyph + docs) | **Recommended.** Least new machinery, closest to "reuse notebook logic". |
| B. Trailing colon header | `- Design Notes:` | Markdown-heading familiar; no sigil | Collides with `:` rules (only final `:` allowed today) and Dataview `[k:: v]` fields; mangles `?`/`!` titles; silent ambiguity with prose ending in `:` | Reject. |
| C. New sigil (`@d`, `!d`, `%d`, `>`) | `- %Design Notes` etc. | Explicit | Every sigil is taken (`@` where, `!` complete, `&`/` *` deps, `~` relations, `%` how, `s:`/`$` schedule/priority, `>` move/merge, `=` pomodoro); new sigil = new typing burden + Mac/parser work | Reject. |
| D. Bracket/quote wrapper | `- [Design Notes]` / `- "Design Notes"` | Explicit | `[…]` collides with checkbox detection + links; quotes already mean "exact literal" inside `#""`, not a header marker | Reject as primary (keep quotes for exactness only). |
| E. Bare mixed-case + nesting heuristic | `- Design notes` + children = drawer | Zero typing | Misclassifies every loose note with nested detail (notebooks prove nested detail is free-form); breaks zero-req interleaving history (§1) | Reject. Dangerous. |
| F. Field/attribute | `- Design Notes [drawer]` / `[drawer:: x]` | Machine-clear | Inline-field syntax is Dataview-visible, noisy, editable as text, and leaks storage into display | Reject. |

Only A satisfies (i)–(vi) without a new sigil. Detail decisions within A:

- **Store the `#` or strip it?** Store it (persistent marker). Stripping
  reintroduces the ambiguity (§3.1): a bare `- Design notes` with children
  cannot be told from a note with detail. The `#` is the bit that says "this
  bullet is a header, not a note." Notebook section bullets already work this
  way (the `- #Section` line is never a note).
- **`#` + quoted vs unquoted:** keep both, with notebook semantics. Unquoted
  `#design-notes` / `#design notes` resolves case-insensitively then by slug,
  creates via a capital-preserving function; quoted `#"…"` creates verbatim
  (after validity checks) and skips the near-duplicate guard — exactly today's
  drawer contract, minus the uppercasing.
- **What stays valid:** today's ALL-CAPS titles remain valid drawers
  (read-compat). `normalize_drawer_literal` stops uppercasing; it collapses
  whitespace and validates instead. `drawer_key` (uppercase fold) stays the
  identity so `NOTES`, `Notes`, `notes` remain one drawer and the catalog
  `spellings` map records the observed casing.
- **Charset:** keep the conservative rest-alphabet initially (letters of any
  case, digits, space/tab, `& ' ( ) , . / - ? ! ;`, final `:`), simply dropping
  the all-caps requirement while retaining "at least one letter". Defer unicode
  letters to a follow-up — they interact with `selector_slug` (ASCII-lowercase
  + hyphens) and the twin JS implementations.

---

## 5. Rendering: distinct and easily recognizable (without shouting)

Goal: a reader can spot a drawer header at a glance in CLI, Obsidian, and Mac,
without ALL-CAPS, without color-only signaling, and without adding noise to
ordinary notes.

**Recommended treatment (all three surfaces):**

- **Glyph + weight, never case transform.** Render the stored `#` as a small
  drawer/folder mark in drawer ink, followed by the true-case title in a
  slightly heavier weight with a touch of letter-spacing, plus a faint rule or
  left border on the drawer block. Example (human/CLI sketch):
  `▤ Design Notes · 3` where `▤` is the drawer glyph and `· 3` the entry-count
  badge `bob capture-drawers` already reports. Obsidian: same glyph via the
  task-tag-marks CSS-mask pattern (`--bob-drawer-glyph`, `--bob-drawer-hue`),
  not an emoji (emoji render inconsistently across themes/devices and add color
  noise). Never `text-transform: uppercase` — that would fake the old look and
  defeat the intent.
- **Ink:** pick one drawer hue outside the lane/status palette (teal = identity,
  red = blocked, orange = attention/rotten, yellow = in-progress, green = next,
  blue = ready, violet = tags/links, grey = priority/cancelled). A muted
  slate/bronze folder tone with 3:1+ contrast in both themes, theme-hookable
  like `--bob-task-tag-hue`, is the right neighborhood; exact value via the
  taste/design pass with Bryan.
- **Counts + affordances:** keep `entry_count` badges (empty drawers stay
  creatable-but-unborn: capture never creates an empty drawer, per
  `parse_drawer_title` docs); completion rows show `task` → `recent` → `new`
  groups unchanged, with true-case titles.
- **Mac:** Mac renders what bob returns (thin client) — no grammar in the app.
  Add the glyph + count to the drawer rows and the bullet-start `#` assist;
  do not invent a Mac-only spelling.
- **What not to do:** no `#tag`-style pill (reintroduces the tag confusion),
  no emoji prefix stored in bytes (display-only), no ALL-CAPS-via-CSS.

This needs a small design pass with Bryan (glyph choice among `▤ ▦ 🗂`-class
marks, hue, rule weight) — the "beautiful" requirement is real and cannot be
met by engineering alone. Prototype the three surfaces side by side before
locking the hue.

---

## 6. Capture syntax changes + notebook reuse (concrete)

**Principle:** one selector grammar for drawers and notebook H2s, with the
destination deciding what a match *means* (task child vs `##` section). The
notebook resolver is the template; the drawer resolver adopts its semantics
without merging the two namespaces.

1. **Lexer (shared opener, divergent meaning).**
   `drawer_bullet.rs::scan_leading` and `section_bullet.rs::scan_leading` already
   share the opener; keep it. On task destinations `#` at bullet start stays a
   drawer marker; on notebook bodies it stays a section marker (never a drawer,
   per `section_bullet.rs` header). No change to nesting (`two-level authored
   grammar` cap stays) or to `\#` escaping.
2. **Resolver unification (`capture_drawers.rs` ← `notebook.rs:250-339`).**
   Replace the drawer create path's `to_ascii_uppercase` spelling with:
   quoted → verbatim title (validated, near-duplicate guard skipped, as today);
   unquoted → exact title match (case-insensitive, `title_matches` semantics)
   → unique slug match (`slug_matches`) → ambiguous refusal (list lines, as
   today) → near-miss hint naming the existing slug (adopt notebook's
   `NearMiss` wording; keep drawers' strict-prefix/edit-distance-1 calibration)
   → create via capital-preserving `format_drawer_create_title` (sibling of
   `format_notebook_section_create_title`: hyphens→spaces, keep typed capitals
   in words containing uppercase, Title Case the rest). Reserved + structural
   refusals run before matching on both paths (already the case for `^prj` H2s).
3. **Commit bytes.**
   - New drawer from bullet: write `- #Title` header (persistent `#`) + nested
     `  - note` children, instead of today's `- TITLE` rewrite. The
     `- #slug` typed form still completes to the stored spelling
     (`- #future-work` → `- #Future Work`), preserving muscle memory while
     fixing the case.
   - Glued `@route+id#sel`: unchanged shape (`#slug` / `#"Literal"`); only the
     creation casing changes (catalog spelling or capital-preserving format,
     not uppercased). `--drawer TITLE` takes the title verbatim (validated).
   - `%n` notebook-create seeding (`plan_from_sub_bullets`): ALL-CAPS bullets
     still seed Title Case `##`; new `- #Mixed` bullets seed the typed title
     directly (this is the "same body plan" reuse the prompt asks for —
     `NotebookBodyPlan` groups + `plan_list_item`/`plan_create_item` stay
     shared).
4. **Read-compat.** `parse_drawer_title` accepts both `- TITLE` (legacy,
   no `#`) and `- #Title` (new). `drawers()` enumeration, `Drawer.key/slug`,
   catalog, `capture-drawers`, and `capture-complete` list both forms together;
   merges treat same-key legacy + new headers as one drawer at the earliest
   position (rename-drawer already merges this way).
5. **Spans + JSON.** `capture-parse` reports the `#` marker span on drawer
   bullets (like notebook section bullets); `sub_bullets`/`drawer` JSON keeps
   `title` (true case) + `key` + `slug`; dry-run preview must show the
   `#Title` header it will write (cf. on-note #7 preview-drift warning — add a
   vector for it).
6. **Docs + vectors.** Update `docs/capture.md` (grammar table, drawer
   sections), `docs/reference/capture-syntax.md`, `docs/reference/json-outputs.md`,
   `capture-drawers` CLI reference, notebook docs' "first-level `- #` opens no
   drawer" note (still true — destination decides), and the RL/RW twin vectors
   + cycler/nav copies. This is a grammar bump (grammar 4 broke bullet-start
   types; this changes bullet-start writes) with a `just docs-check`-clean
   contract-test update (cf. on-notes #1/#5).

---

## 7. Lossless project-note task representation (scope honestly)

Drawers-as-`#True Case` advance the stated stepping stone cleanly:

- Promotion (`on.12`) today maps each drawer → H2 via
  `format_project_section_title` (`API DESIGN` → `Api Design` — lossy).
  With case-preserving drawers, drawer title ↔ H2 title can be byte-identical
  for the common case, and reversal restores the same bytes. Recommend making
  that identity explicit in `on.12`'s promotion receipt (counts + byte check).
- But call out what this step does *not* deliver: req subtrees, log/managed-line
  order, block-ID stability, `^prj`-H2-vs-drawer duality, checkbox bytes, and
  fenced content all still need their own lossless rules. Position this epic as
  "lossless drawer↔section casing" and leave the full task↔project-note
  isomorphism to its own plan. Do not promise it here.

---

## 8. Adjustments to the requirements (as requested)

1. **Marker, clarified:** adopt persistent bullet-start `#` (`- #Title`), not
   `#foo` tags anywhere else. The prompt's parenthetical is correct for
   trailing/inline tags; the one exception (bullet-start `#`) is safe *because*
   the drawer/section lexers already preempt typing there. State this explicitly
   so nobody "fixes" it back into a tag.
2. **Resolver, strengthened:** don't just "reuse notebook logic if desirable" —
   require it: same match precedence (exact-ci → slug → ambiguous → near-miss →
   create), same quoted-verbatim rule, sibling create-title functions. Two
   resolvers with different near-miss calibrations will re-split the UX.
3. **Rendering, elevated to a deliverable:** a designed glyph + ink + rule +
   count across CLI/Obsidian/Mac, prototyped with Bryan, not an engineering
   afterthought. ALL-CAPS removal without this is a regression.
4. **Migration, made explicit:** read-both/write-new + opt-in
   `bob task tidy`-family migration (or a `rename-drawer --lower` batch), never
   a flag day. Legacy ALL-CAPS drawers keep working; only touched/new drawers
   take the new casing unless Bryan runs the migration. Dataview/grep guidance
   ships with it (match on `drawer_key`, not title).
5. **Scope, narrowed:** this epic owns drawer casing only. It does not own req
   behavior, lane/status semantics, promotion counting, successor verdicts, or
   the `^prj` NOTES-home decision (on-notes #2/#4) — it *consumes* those once
   `on` lands. If `^prj` H2 casing rides along (it should — same resolver), say
   so, but don't re-decide the NOTES home here.

---

## 9. Recommended solution (end state)

**Store `- #True Case` drawer headers; resolve like notebook H2s; render with a
quiet drawer glyph; land after `bob-cli-on`.**

- **On disk:** `- #Design Notes` (new) alongside legacy `- DESIGN NOTES`
  (read-only compat). Nested notes unchanged (`  - …`, one line each,
  two-level grammar). Glued `@route+id#design-notes` / `@route+id#"Design Notes"`
  unchanged in shape; creation preserves case. `^prj` H2 drawers keep `## True
  Case` with the same resolver.
- **Identity:** `drawer_key` (uppercase fold) stays the merge/match key;
  `title` keeps true case; `slug` unchanged; catalog `spellings` records casing.
  Reserved/structural sets unchanged.
- **Capture:** bullet-start `#` persists (no more bare-title rewrite); completion
  inserts the stored spelling with `#`; quoted forces verbatim creation;
  near-duplicate guard kept with notebook-style hints; dry-run shows what will
  land; JSON exposes marker spans + true-case titles.
- **Render:** `▤ True Case · N` treatment (glyph + weight + rule + count,
  dedicated ink, no case transform) in CLI human output, Obsidian (CSS mask
  pattern per `task-tag-marks.md`), and Mac drawer rows/pickers. Design pass
  with Bryan locks glyph + hue.
- **Migrate:** `bob task tidy` + `rename-drawer` learn the new form; a
  one-shot opt-in migration converts legacy headers (`- TITLE` → `- #Title`
  using catalog spelling / Title-Case-preserving format); nothing auto-rewrites
  without the command. Docs + twin vectors + Mac contract updated in the same
  epic; grammar bump noted.
- **Sequence:** freeze until `on.11/12/15/17` close → branch drawer epic from
  post-`on` master → grammar+resolver → writers + tidy/rename → renderers
  (CLI/plugin/Mac) → migration + docs/vectors → memory updates (new decision
  record; `glossary:task-drawer` + `decisions:capture-bullets-mirror-the-task-block`
  amendments *after* `on.17` releases them).

---

## 10. Verification performed for this research

- Read `src/native/capture_drawers.rs` (predicates, catalog, `project_h2_drawers`,
  resolve/create paths), `capture_language/drawer_bullet.rs`,
  `section_bullet.rs`, `notebook.rs:1-450` (resolver + create-title),
  `line.rs:selector_slug`, `model.rs:DrawerSelector`, `task_block_layout.rs`
  zones + `NOTES_TITLE`, `task_drawer_rename/mod.rs` casing rules,
  `capture_complete/drawers.rs` menu contract, `docs/notebooks.md` capture
  section, `docs/capture.md` grammar table, `docs/task-tag-marks.md` mark
  pattern, and `docs/reference/cli/capture-drawers.md`.
- Read `glossary:task-drawer`, `decisions:capture-bullets-mirror-the-task-block`,
  and `decisions:notebook-routes-write-notes` via `sase memory read`; read
  `bob-cli-on`, `bob-cli-on.11`, `bob-cli-on.12` beads via `sase bead read` for
  phase status, ownership, and notes #1–#7.
- Checked `202611/` research dir for filename collisions (none for the chosen
  stem) and confirmed the `#`-opener sharing between drawer and section lexers.

Open questions for Bryan (design pass, not research gaps): glyph + hue choice;
whether quoted-verbatim creation should also accept lowercase-first titles
(`#"api design"` → keep or Title Case?); whether the opt-in migration should
also normalize legacy `REQUIREMENTS` → `NOTES` remnants (cf. `on` migration) or
leave them untouched.

---

*End of report. Registration follows via `sase artifact create` with the actual
absolute path and `research:<repo-relative-path>` label.*

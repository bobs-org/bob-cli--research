# Capture syntax cleanup: task drawers, `%` directives, and one rule for `#`

*Researcher: cld · 2026-10-31 · repos: bob-cli @ `5e2d0856`, bob-mac-capture @ origin/master,
bob-plugins @ origin/master · vault sample: `~/bob` on apollo*

## TL;DR

**Verdict: do it.** The plan removes the worst wart in the capture grammar today. In
`@route+id#X`, the `#X` means "retype" or "section" depending on whether the item happens
to have body text. The plan also frees a bare `#` for the type menu and moves four "how
to capture" switches into one `%` family. Every form it retires is three weeks to three
months old, and the vault shows almost no use of the ones being dropped.

I would ship it with **eight adjustments**, listed in §5. Each is called out as a change
to the request:

| # | Adjustment | Why |
| --- | --- | --- |
| A1 | Also retire `@route^id#type`; type a new task with a separate `#type` | Gives one rule: a `#` glued to a token names **a place**, and a `#word` standing alone names **a type** |
| A2 | Move the URL listen marker `URL %` (and its `URL @` alias) to `%l` | A bare `%` cannot both open the directive menu and mean "listen" |
| A3 | Drop the clipboard header form `%header`; keep `%c` and `%c<N>` | Effectively no vault usage; `%c<word>` would be ambiguous |
| A4 | Match drawers **exactly**, never by prefix; refuse near-duplicates of drawers already on the task | Prefix matching plus auto-create silently writes to different places depending on vault state |
| A5 | Menus opened by a bare sigil (`#`, `%`) start with **no row selected** | Return on a bare sigil must never commit a choice; this reuses the relation-card Tab precedent |
| A6 | Every `%…` token at an item edge is a directive (an unknown letter is an error); `\%` escapes | Old `%3` and `%build_log` fail loudly without any compatibility code |
| A7 | Live preview reads the clipboard **only when a `%c` is present**, and renders a real Clip card | This is the "better `%c` preview" Bryan asked for |
| A8 | *(optional, phase 4)* On a project note's `^prj` task, `#drawer` writes to the matching `##` section | A drawer **is** an H2 after promotion, so the same gesture keeps working |

The recommended solution is in §10.

---

## 1. Question and scope

Bryan asked for:

1. `@file+id#drawer` to replace `@file+id#type`. A `#type` is then a separate token.
   - Example: `Some note goes here. @foo+bar#requirements #fix` adds a bullet to the
     `REQUIREMENTS` drawer of `^bar` in `foo.md`.
   - A missing drawer is created.
   - Typing `#` after `@file+id` opens a drawer menu: first the task's own drawers, then
     recent drawers from other tasks and from project-note H2s.
   - A new glossary term: **task drawer**.
2. Trailing `#` (Pomodoro note), `%` (clipboard), and `@@template:` move to `%n`, `%c`,
   and `%t`.
   - `%t` stays where it was typed.
   - Typing `%` shows descriptions of the directives in Bob Mac Capture.
   - The type menu opens immediately on `#`.
3. `@@file+id` is removed.
4. No compatibility for the retired forms.
5. Lead the design: intuitive, reliable, beautiful.

This report covers the grammar, the menus, previews, the wire contract, the glossary, the
phasing, and the risks. It does not cover implementation code.

## 2. What exists today (evidence)

### 2.1 The forms this touches

| Form today | Meaning | Added | Evidence |
| --- | --- | --- | --- |
| trailing bare `#` | Pomodoro note | 2026-08-18 (`f171a7e0`) | `docs/capture.md` § Pomodoro notes |
| `%`, `%N`, `%header` | clipboard as children | 2026-07-15 (`7468820c`, `e6b70be4`) | `docs/capture.md` § Clipboard |
| `URL %` (+ alias `URL @`) | companion-audio listen | 2026-10-10 (`d1d50a6d`, `b0795ac3`) | `docs/capture.md` § Saving links |
| `@@template:` header | bulk template | 2026-10-15 (`946c9b7d`) | `src/native/capture_language/template.rs:15` |
| `@@@` keystroke | rewrite that inserts the header on line 1 | 2026-10-20 (`0e9f915a`) | `src/native/capture_language/rewrite.rs:114` |
| `@@route+block-id` | draft-wide parent task | 2026-08-24 (`9258da9c`) | `docs/capture.md` § Global destination |
| `@route+id#X` with body | task **section**: prefix match, error if missing | 2026-08-19 (`8f95e87b`) | `docs/capture.md:4552` |
| `@route+id#X` with no body | **retype** + Ensure Next | 2026-10-31 (bob-cli-ep, `4a95e5b7`) | `docs/capture.md:141` |
| `@route^id#X` | type the new task | 2026-10-31 (bob-cli-ep) | `docs/reference/capture-syntax.md` § `#<type>` |

The bob-cli-ep epic explicitly chose `bare_hash_menu = letter`. Its stated reason was:
"Return always accepts row 0 today, so a menu on a bare `#` would break Pomodoro notes"
(`plan:202610/capture_hash_type_marker.md`). Moving Pomodoro notes to `%n` is exactly
what removes that blocker. The epic also chose `retire_t = prose`, so Bryan's stated
preference against compatibility shims is consistent.

The `#` reference table in `docs/capture.md:152-163` has eight `#` rows, and its first
sentence is "`#` is not one marker". After this change that table becomes two rules
(§4.1).

### 2.2 Vault usage (apollo `~/bob`, 6,530 notes, read-only scan)

| Measure | Count | Implication |
| --- | --- | --- |
| Project notes (`type: "[[project]]"`) | 98 | — |
| `## Tasks` H2 in project notes | 97 | structural; must **not** be offered as a drawer |
| `## Requirements` H2 | 51 | the drawer vocabulary already exists, as H2s |
| `## Future Work` H2 | 50 | same |
| `## Motivation` / `## Project Notes` | 2 / 2 | long tail |
| Task drawers (ALL-CAPS child with nested items) | 5 (REQUIREMENTS 3, MOTIVATION 1, DONE 1) | the error on a missing section has suppressed use |
| Bold clip-style headers `**NAME:**` | only managed lines (DEPENDS ON 113, LINKED FROM 111, LINKS 70, BLOCKS 68); everything else ≤ 1 | `%header` is effectively unused (A3) |

The drawer menu's "recent" pool will be dominated by REQUIREMENTS, FUTURE WORK, and
MOTIVATION. That is the right default, provided `TASKS` and the managed names are
excluded (§4.3).

### 2.3 The promotion round-trip already defines "drawer"

bob-plugins already treats these bullets as a first-class concept:

- **Predicate.** `PROJECT_SECTION_TITLE_RE = /^[A-Z0-9][A-Z0-9 \t&'(),./-]*$/`, plus at
  least one letter (`plugins/bob-navigation-hotkeys/src/010-requires-and-config.js:117`).
- **Promotion.** A qualifying direct child (no checkbox, an ALL-CAPS title, and at least
  one nested item) becomes a `## Title Case` section. It reuses an existing header
  case-insensitively, or appends one at the end of the note (`docs/projects.md:370-384`).
- **Reversal.** `formatProjectReversalSectionTitle` uppercases the H2 back into a bullet.
- **bob-cli's predicate.** `is_section_title`
  (`src/native/capture_task_sections.rs:210-250`) uses the same charset.

So a drawer is already "the ALL-CAPS bullet that becomes an H2". The rename only gives
it a name.

### 2.4 Bob Mac Capture facts that constrain the design

These come from a read-only audit of `bob-mac-capture`:

- **No "no selection" state in the inline menu.** `selectedCompletionIndex` is an `Int`,
  reset to 0 on every response (`Sources/BobMacCapture/CapturePanelModel.swift:425, 4646`).
  The one exception preselects a `suggested` Pomodoro name (`:4647-4655`). Only the
  relation-label card supports an empty selection, where Tab takes the top match
  (`docs/relationship-pickers.md:113-117`). This is the precedent for A5.
- **Live preview never reads the clipboard.**
  `captureLivePreview` always passes `--no-clip`, enforced by a precondition
  (`Sources/CaptureCore/BobProcessClient.swift:710-731, 1037`). While a clipboard span
  exists, the panel shows only the caption "Clipboard markers stay literal in live
  preview" (`CapturePanelModel.swift:1513-1520`).
  - Even the explicit Preview button renders only `clip.lines`, as raw appended lines.
  - It does not render attachments, snippets, or a card, although `CaptureClipOutput`
    already decodes `header/mode/lines/attachments/snippet/entries`
    (`Sources/CaptureCore/CaptureModels.swift:6295, 4186-4198`).
- **There is no syntax-help surface.** No menu or popover explains sigils, and inline
  completion rows have no description field (`CaptureModels.swift:7714-7870`). The
  directive menu therefore needs a small new row style, which bob supplies data for.
- **Task-section rows already exist.** They show title, task text, `^id`, and "N items"
  (`Sources/CaptureCore/CompletionRowContent.swift:470-481`).
  - There is a small bug: one child renders "1 items" (`:480`), and a test pins it.
  - The `pomodoro_name` menu already has Suggested/Recent/Today group headers and a
    "Create" row (`CapturePanelView.swift:3045-3075`, `CompletionRowContent.swift:521-544`).
    That is the exact shape the drawer menu needs.
- **Template-start Swift code.** `Sources/CaptureCore/CaptureTemplateStart.swift`, the
  "@ again to start a template" hint, and the `@@` template route candidate all go away.
- **`@@route+id` Swift code.** The `global_sub_bullet_*` spans and the "All items → foo.md ·
  under ^id" scope line lose their `+id` half.
- **Unknown completion contexts fail soft.** `CaptureCompletionContext.init?` returns
  `nil` (`CompletionRowContent.swift:228-257`). An older app paired with a newer bob
  degrades instead of crashing.

### 2.5 Governing rules

- **`decisions:mac-capture-is-a-thin-client`.**
  - The directive descriptions, the drawer rows, and the clip peek must all come from
    bob. Swift renders them; it hard-codes no grammar copy.
  - The record also says the JSON contract "must grow additively". This change is a
    deliberate contract break, as bob-cli-ep was, so it needs `!` commits and a
    bob-first landing order (§7).
- **`decisions:bob-cli-releases-ride-a-daily-train`.** Mark the break with `!`. Never
  edit the version or `CHANGELOG.md`.
- **CLI rules memory.**
  - "Never hard-rename or remove a command". `bob capture-task-sections` may gain a new
    canonical name, but the old one stays as a hidden alias.
  - The `capture-*` names are frozen siblings that may only grow additively.
  - Every public long option needs a short alias.
- **Relation-card precedent (`decisions:relation-card-tab-accepts-ctrl-d-hides`).** Tab
  accepts the top match when nothing is selected, and Ctrl+D hides a suggestion. A5 and
  the optional drawer hide reuse both.

## 3. Critique: is this a good idea?

### 3.1 What the plan gets right

1. **It removes a meaning that depends on hidden state.** Today `@cash+id#coding`
   retypes the task, but `Note @cash+id#coding` files the note under a CODING section. A
   one-word difference elsewhere on the line flips the meaning of the token. Pinning
   `#` after `+id` to "drawer" makes the token mean the same thing everywhere.
2. **`%` becomes a coherent family of capture modes.**
   - The four switches answer "**how** should this be captured?": clip it, file it on the
     Pomodoro, expand it as a template, or (A2) listen to it.
   - That is a different question from `@` (**where**) and `#type` (**what kind**).
   - The new family can also be explained by a menu, which no sigil has today.
3. **It deletes surprising magic.** `@@@` silently inserts a line at the top of the draft
   and moves the caret. `@@template:` puts a mode switch inside the destination namespace
   (`@@`).
4. **It unlocks the immediate type menu**, which bob-cli-ep could not ship.
5. **"Drawer" fixes a real naming collision.** "Section" means three things today: a
   Markdown heading (`@note#Ideas`), an Annotation Section (whose glossary entry already
   says "Not a … `bob capture` target section"), and a task section. "Drawer" says what
   the thing is: a labelled container inside a task.
6. **Auto-create matches how drawers are actually used.** The vault has 101 project H2s
   but 5 task drawers. People think in drawers but avoid the capture form, because a
   missing section is an error.

### 3.2 Where I would push back or extend

1. **The plan leaves `@route^id#type` behind.** After the change:
   - `@foo+bar#fix` means "drawer FIX on ^bar";
   - `@foo^bar#fix` means "new task ^bar typed FIX".

   One character (`+` vs `^`) flips `#fix` between a place and a type. Retiring the
   attached type form (A1) produces a rule Bryan can say in one breath (§4.1). It costs
   a single space (`@foo^bar #fix`) and deletes the attached-suffix machinery in
   `type_marker.rs`.
2. **Auto-create breaks prefix matching.**
   - Today `#future` reaches FUTURE WORK by prefix. With creation,
     `Note @foo+bar#req` would land in REQUIREMENTS on one task and create a junk REQ
     drawer on another.
   - Old prefix habits would also silently create junk drawers.
   - Exact matching, with prefix help moved into the menu, plus a near-duplicate guard,
     is the reliable version (A4).
3. **`URL %` cannot survive.** If a bare `%` is "pick a directive", it cannot also mean
   "listen" after a URL.
   - Today's docs spend a paragraph on the special cases: `URL %` vs `URL %1` vs
     `-R 'URL %'` vs `--no-clip` in preview.
   - `%l` deletes all of that (A2).
4. **`%header` is dead weight** (§2.2). Keeping it would force a spelling like
   `%c:build_log`, or an ambiguous `%cbuild_log`, for a feature nobody uses (A3).
5. **"Make `#` open the menu immediately" carries a muscle-memory hazard.**
   - Today `jot idea #` ⏎ captures a Pomodoro note.
   - With row 0 preselected, `#` ⏎ inserts `#build`, and a second ⏎ writes a typed
     inbox task.
   - With A5 (no selection on a bare sigil), ⏎ submits, and bob refuses the incomplete
     `#`. The draft stays put, and the mistake costs nothing.
6. **Clip previews need a policy change, not just a widget.** Live preview never reads
   the clipboard, by design. The user-visible fix is to read it **only when a `%c` is
   present** (A7). macOS has also announced pasteboard-privacy alerts for programmatic
   reads, with a detect API that inspects types without reading content. Gating the
   read on an explicit `%c` keeps any future prompt tied to a user-typed request.
7. **"No backward compatibility" is right, and mostly free.** Claiming the namespaces
   makes old spellings fail loudly with no shim code (A6):
   - `%`-tokens at item edges are claimed;
   - a bare `#` at an edge is an incomplete type marker;
   - `@@` takes only a route.

   The only old habit that could write the wrong thing silently is a drawer prefix,
   which A4's guard catches.

### 3.3 Would I take a different approach?

No. I considered the following, and the plan as adjusted beats each (details in §6):

- a non-`#` drawer sigil (`@foo+bar/requirements`);
- word directives (`%clip`, `%note`);
- keeping the `@@template:` header;
- a configured drawer vocabulary instead of a vault catalog.

## 4. Design

### 4.1 The mental model

| Sigil | Answers | Forms after the change |
| --- | --- | --- |
| `@` | **where** | `@note`, `@note#Heading`, `@note+id`, `@note+id#drawer`, `@note:id`, `@note:id#pomodoro`, `@note^id`, `@note^id+`, `@@note` |
| `#word` (own token) | **what kind** | `#fix`, `#"DEEP WORK"`: types the new task, or retypes the task the item targets |
| `%x` | **how** | `%c` clip · `%n` Pomodoro note · `%t` template · `%l` listen |
| `s:` `$` | **when / how urgent** | unchanged |
| `& * ~ ~~ !` | **relations / done** | unchanged |
| `= x + - ++ --` | **the session** | unchanged (`=#bugs`, `x#bugs` keep their meanings) |

> **The `#` rule.** A `#` glued to the end of another token names a **place inside it**:
> a heading (`@notes#Ideas`), a drawer (`@foo+bar#requirements`), or a Pomodoro
> (`@sase:fix#bugs`, `=#bugs`, `@cash^exit+#bugs`). A `#word` standing alone names a
> **type**.

The `#` reference table becomes:

| You typed | Meaning |
| --- | --- |
| `Fix the parser #fix`, `#fix Fix the parser` | Type the new task FIX |
| `Fix the parser @sase^parser #fix` | New `^parser` task typed FIX (A1: the attached `@sase^parser#fix` is retired) |
| `Called Morgan @cash+exit#requirements` | Bullet into `^exit`'s REQUIREMENTS drawer, creating it when missing |
| `Called Morgan @cash+exit#requirements #fix` | Same, and retype `^exit` to FIX |
| `@cash+exit #fix` | Ensure Next and retype `^exit` (unchanged from today's free-standing form) |
| `@notes#Ideas` | Bullet under a heading (unchanged) |
| `@sase:fix-x#bugs`, `^sase:x#bugs`, `=bugs`, `=#bugs` | Pomodoro (unchanged) |
| `#` alone at an item edge | Incomplete type marker: the type menu is open |
| mid-line `#`, `#1234`, `C#`, `\#tag` | Prose (unchanged) |

### 4.2 Task drawers

#### Grammar

- **The token.** `@<route>+<block-id>#<drawer>`, glued, at either edge of the item's
  first line, or as a trailing marker on any line, exactly where `@route+id` is legal
  today.
- **Drawer name spelling** reuses the type-marker lexer (one `#name` rule across the
  grammar):
  - **slug:** `#requirements`, `#future-work` (ASCII letter first; letters, digits, `-`);
  - **literal:** `#"NON-GOALS"`, `#"Q&A"`, `#"API (V2)"`, with the escapes `\"` and `\\`.
  - Today's unquoted selector also allowed `& ' ( ) , . /`. Those now need the literal
    form. This keeps trailing punctuation from ever being swallowed into the name.
- **Body text is required.** A drawer holds bullets.
  - `@foo+bar#requirements` with no body is **incomplete**, with the new need `drawer_text`
    and a teaching message: ``add the bullet text for REQUIREMENTS (`Postgres 17 minimum
    @foo+bar#requirements`)``.
  - An empty `@foo+bar#` is incomplete, with need `drawer`. The menu is open.
  - *Optional extension:* a drawer-only parent line followed by authored children could
    file each child as a drawer entry (`@foo+bar#requirements` then `- 17+` / `- 2 GB`).
    Today that shape is an error, so adding it later is additive.
- **`#type` on a drawer or plain sub-bullet item** retypes the **parent task** (the
  item's only typeable subject). This lifts today's "a marker on a sub-bullet with text
  is refused".
  - Body text means **no Ensure Next**. Only a marker-only `@route+id` item changes
    lanes.
  - The type edit stages before the write, and the existing D8 applier relocates any
    live Task Link, exactly as marker-only retypes do today.

#### Resolution (exact, A4)

1. **Key.** The drawer key is the uppercased, whitespace-collapsed title. A slug tries its
   hyphenated spelling first, then hyphens as spaces. This is the same rule types use.
2. **Existing drawer on the task.** If the key equals the key of a direct ALL-CAPS child
   under the task, append there. The current geometry is unchanged: entries go at the end
   of the drawer's own block, before any managed log nested under it.
3. **Near-duplicate guard.** Before creating a slug-named drawer, check whether the new
   key is a strict prefix of, or within edit distance 1 of, a drawer already on this
   task.
   - If so, refuse with ``did you mean `#requirements`? write `#"REQ"` to create REQ``.
   - A quoted literal skips the guard. This mirrors `=#"BOB"`, which never prefix-matches.
4. **Creation.** Otherwise create the drawer.
   - **Spelling:** the drawer catalog's most-used spelling for that key (so `#non-goals`
     becomes NON-GOALS if that spelling exists anywhere); otherwise the slug uppercased
     with hyphens as spaces; otherwise the literal uppercased.
   - **Placement:** the new drawer bullet becomes the task's last direct child, before
     any managed Schedule, Work, or Rotten Log. This is the same anchor plain sub-bullets
     use today. Its first entry nests under it.
   - The result always qualifies as a promotion section, because it has at least one
     nested item.
5. **Reserved names.** These names refuse with a teaching message:
   - **managed task lines:** `DEPENDS ON`, `BLOCKS`, `LINKS`, `LINKED FROM`,
     `SCHEDULE LOG`, `WORK LOG`, `ROTTEN LOG`;
   - **structural H2:** `TASKS`.
6. **Catalog-only warning.** A key that is new to the task and within edit distance 2 of
   a popular catalog drawer is not refused. It produces a warning:
   `new drawer REQUIRMENTS · did you mean REQUIREMENTS?`

Before and after, for `Postgres 17 minimum @foo+bar#requirements #fix`:

```markdown
- [ ] #task Upgrade Postgres [created::2026-07-31] ^bar
	- 🗓️ **SCHEDULE LOG**
		- *2026-08-02* — 🎲 P0 → P2 · in **12** (8–30) days
```

```markdown
- [ ] #task Upgrade Postgres [type:: FIX] [created::2026-07-31] ^bar
	- REQUIREMENTS
		- Postgres 17 minimum
	- 🗓️ **SCHEDULE LOG**
		- *2026-08-02* — 🎲 P0 → P2 · in **12** (8–30) days
```

Human output:

```text
✓ captured  foo.md
  under ^bar Upgrade Postgres › REQUIREMENTS  (new drawer)
  - Postgres 17 minimum
  type   → FIX
```

#### `bob capture` CLI surface

- `-S, --task-section TITLE` becomes **`-D, --drawer TITLE`**. It matches the title
  exactly and creates the drawer when missing.
  - It is an option with no external consumers: the Mac app does not use it. So it is
    renamed outright.
- **`bob capture-drawers`** becomes canonical. Per the CLI rules,
  `bob capture-task-sections` stays as a permanent hidden alias with identical output.
  - It gains an additive `recent` array (the catalog rows) in JSON.

### 4.3 The drawer menu (`#` after `@file+id`)

#### Context

The new completion context is `drawer`, replacing `task_section`. It triggers whenever
the caret is in the `#…` suffix of `@route+id`, with or without body text.

#### Data source

The drawer catalog is a vault scan modelled on `src/native/relation_labels/scan.rs`:

- **Caching:** a per-note cache keyed by mtime and size, a 60 s snapshot TTL, and
  bounded warnings.
- **Sources:**
  - direct ALL-CAPS drawer children of `#task` lines (the bob predicate);
  - `##` headings in project notes, uppercased. bob-plugins' reversal makes the two
    spellings the same key.
- **Exclusions:** reserved names, `done/` for recency (it still counts toward
  frequency), dot-directories, `_templates/`, and `_generated/`.
- **Per key it records:** `count` (distinct notes), `last_seen` (the newest mtime of a
  note using it), and the most-used spelling.
- **Ranking for the Recent group:**
  1. notes using the key that were modified in the last 90 days (descending);
  2. `last_seen` (descending);
  3. name.

  On today's vault this yields REQUIREMENTS, FUTURE WORK, MOTIVATION, PROJECT NOTES, and
  so on. The Recent group is capped at 8 rows.

#### Groups and rows

The menu reuses the `pomodoro_name` group-header and create-row styles that already
exist.

```text
╭─ DRAWER · ^bar Upgrade Postgres ─────────────────────────────╮
│ ON THIS TASK                                                 │
│ ▤ REQUIREMENTS                                     3 notes   │
│ ▤ FUTURE WORK                                      1 note    │
│ RECENT                                                       │
│ ▢ MOTIVATION                         3 notes · 1 day ago     │
│ ▢ NON-GOALS                          2 notes · 2 weeks ago   │
│ ＋ New drawer  PERF BUDGET                                   │
├──────────────────────────────────────────────────────────────┤
│ Adds to REQUIREMENTS, after “2 GB RAM”      ⏎ choose  ⇥ take │
╰──────────────────────────────────────────────────────────────╯
```

- **ON THIS TASK:** the task's own drawers in document order. A row shows the
  title and the entry count ("1 note" / "3 notes"; this fixes the "1 items" bug). Its
  secondary text is the last entry, truncated.
- **RECENT:** catalog drawers that are not on this task. The secondary text shows the
  note count and recency.
- **New drawer:** the typed row appears only when the query matches no exact key. It is
  refused (dimmed, ⏎ is a no-op, with a reason) when the guard or a reserved name would
  refuse execution. This reuses the refused-type-row precedent.
- **Replacement:** `#<slug>` when the slug round-trips to that title, else `#"TITLE"`.
  It never adds a space.
- **Footer:** the consequence of the selected row: "Adds to REQUIREMENTS, after …" or
  "Creates FUTURE WORK under ^bar". It is computed by bob.
- **Selection:** an empty query (just typed `#`) opens with no row selected (A5).
  ⏎ then submits, and bob refuses the incomplete drawer. ⇥ or ↓ takes the top row, and
  typing filters.
- **Prefix help lives here**, and only here: `#fut` filters to FUTURE WORK. Execution
  never resolves prefixes.
- **Optional (phase 4): Ctrl+D hide.** Hiding a drawer from Recent would use a per-host
  `.bob/drawers/<host>.jsonl`, the same pattern as theme and relation-label hides.
  Hiding affects suggestions only.

### 4.4 `%` directives

#### Token rule (A6)

At an item edge, any whitespace-delimited token that starts with `%` is a directive.
"Item edge" uses the same position rule as `#type`: either edge of any line in the item,
with only other markers between the token and the edge.

| Token | Meaning | Notes |
| --- | --- | --- |
| `%c` | Capture the live clipboard as child bullets | Today's `%` |
| `%c<N>` | Live clipboard plus history, N values | Today's `%N`; `%c1` = `%c`; `%c0` is invalid |
| `%n` | Pomodoro note (plain text under today's open or last completed Pomodoro) | Today's trailing `#`; same target rules |
| `%t` | This item is a template; each later row is one capture | Today's `@@template:` |
| `%l` | Queue the bare URL with companion audio | Today's `URL %` / `URL @` (A2) |
| `%` | **Incomplete**: the directive menu is open | need `directive` |
| `%x`, `%clip`, `%3`, `%build_log` | `invalid_directive`: ``unknown directive `%3`; directives are `%c` clip, `%n` Pomodoro note, `%t` template, `%l` listen`` | Grammar, not compatibility: the edge namespace is claimed |
| `\%c` | Literal `%c` in the body | Mirrors `\#fix` and `\$3` |
| mid-line `%c`, `100%`, `50%off` | Prose | printf-style `%n` mid-sentence is safe |

#### Composition

Each item takes one directive of each kind, and a duplicate is
`duplicate_capture_marker`.

| With … | `%c` | `%n` | `%t` | `%l` |
| --- | --- | --- | --- | --- |
| `@route…` | ✓ | ✗ (a note has no route) | ✓ (the markers repeat per row) | ✓ (parent of the URL) |
| `s:` / `$` | ✓ | ✗ | ✓ | ✗ |
| `#type` | ✓ | ✗ | ✓ | ✗ |
| `%c` | — | ✓ (clip onto the Pomodoro) | ✗ (`template_clipboard`) | ✗ |
| session operators | ✗ | ✗ | ✗ | ✗ |
| non-URL item | ✓ | ✓ | ✓ | ✗ (`directive_not_applicable`) |

#### `%t` framing

- The template is **the first item of the draft**.
- `%t` may sit at either edge of any line of that item: the parent or a child, leading
  or trailing. It **stays where it was typed**, and nothing rewrites the draft.
- Framing strips the `%t` token (offset-preserving masking). From there everything else
  is today's engine: placeholders, quoting, the `{0}`-only split, the size limits,
  `-E`, and capture(D) = capture(expand(D)).
- A `%t` in any later item is `template_directive_misplaced`:
  `` `%t` marks the first item as the template; move it there ``.
  - That includes a `%t` arriving through a row value, which therefore cannot nest
    templates.
- **The saved-template shelf:**
  - The canonical block text excludes `%t`, so existing shelf IDs stay stable, wherever
    the token was typed.
  - `capture-templates show` and the shelf `draft` render `%t` at the end of the
    template's first line.
- The `@@@` rewrite rule and its Mac intent and hint are deleted. Without `@@template:`,
  the `@@` family means only "draft-wide route".

#### The `%` menu (context `directive`)

All descriptions and contextual details come from bob. The app adds only layout.

```text
╭─ CAPTURE AS … ──────────────────────────────────────────────╮
│ %c  Clip           Paste the clipboard under this capture   │
│                    3 lines · “Postgres 17 minimum, then …”  │
│ %n  Pomodoro note  Add this text to the current Pomodoro    │
│                    WORK · 12:00–12:30 · running             │
│ %t  Template       This item becomes a template; each row   │
│                    below the blank line is one capture      │
│ %l  Listen         (only offered on a bare URL)             │
├─────────────────────────────────────────────────────────────┤
│ %c3 takes your last 3 clips             type a letter · ⇥ · ⎋ │
╰─────────────────────────────────────────────────────────────╯
```

- **Rows.** Rows are always in a fixed order (c, n, t, then l on URLs), for muscle memory.
  Typing the letter filters to one row; ⏎ then accepts.
- **Not applicable.** A directive that does not apply renders dimmed, with bob's reason,
  and ⏎ is a no-op:
  - `%n` on an item with `@route`: "a Pomodoro note has no route";
  - `%t` on a later item: "only the first item can be a template";
  - `%c` in a template draft: "would repeat once per row";
  - `%n` with no Pomodoro today: "no Pomodoro today".

  The menu thereby teaches the composition table instead of hiding it.
- **Contextual detail lines** (bob computes them; cheap):
  - `%c`: a peek at the clipboard's kind and first line, read once when the menu opens
    (A7 gating);
  - `%n`: the Pomodoro that would receive the note;
  - `%t`: placeholder and row counts;
  - `%l`: whether `highlights.listen_command` is configured.
- **Selection.** Opens with no row selected (A5). ⇥ takes the top row and ⎋ leaves the
  bare `%`.
- **Span styling.** One `directive` span kind with a single teal family tint (teal is
  today's clipboard colour), so all `%` tokens read as one family.

### 4.5 `#` opens the type menu immediately

- A bare `#` at a free-standing marker position is now an incomplete `task_type` marker.
  - `capture-complete` returns `task_type` with an empty query.
  - It also returns a new additive top-level field, `initial_selection: "none"`. This is
    the bob-cli-ep "open" branch, already specified once.
- **On submit:** `` `#` is incomplete: type a task type after `#` (for example `#fix`) ``.
- **Applicability gating:** the menu does not open where a type marker would be refused.
  That covers `%n` items, session operators, bare heading bullets (`@note#…` items), and
  template rows.
- `@note#`, `@note:id#`, `=#`, and `@note^id+#` keep their existing heading or Pomodoro
  menus. `@note+id#` opens the drawer menu (§4.3).

### 4.6 Removed, completely (no aliases, no "retired" copy)

| Removed | What an old habit gets now |
| --- | --- |
| trailing bare `#` Pomodoro note | Incomplete type marker (menu opens; submit refuses) |
| `%`, `%N`, `%header`, `--clip=HEADER` | `%` alone is incomplete; `%3` and `%build_log` are `invalid_directive`; `--clip` takes no value |
| `URL %`, `URL @` listen (A2) | `URL %` is incomplete; `URL @` is the ordinary incomplete route |
| `@@template:` header, `@@@` rewrite, the `@@` template candidate | `@@template:` is the ordinary invalid-`@@` error |
| `@@route+block-id`, `global_destination.mode` / `block_id`, `global_sub_bullet_*` spans | ``invalid `@@` declaration: `@@` takes a route (`@@foo`)``; put `@foo+bar` in a `%t` template instead |
| `@route+id#type` retype | Becomes a drawer token; marker-only is incomplete (`drawer_text`) |
| `@route^id#type` (A1) | `` `#` after `@sase^parser` names nothing: a new task has no drawers; type it with a separate `#fix` `` |
| prefix drawer selection (A4) | Exact only; near-duplicates are refused by the guard |
| `task_section`, `sub_bullet_section`, the name "task section" | `drawer` everywhere (docs, JSON, CLI, Rust names) |

The `@@route+id` use case has a direct replacement:

```text
{0} @job+search#leads %t

Acme
Globex
"Initech Corp"
```

### 4.7 Clip previews (A7)

**bob:**

- `--no-clip` keeps its "don't read" meaning, but `%c` is now always parsed and
  stripped from the body. It is never left literal.
- The dry run reports `clip: { "status": "not_read", "count": N }`, so the preview shows
  a placeholder row instead of a literal `%`.
- `\%c` is the only way to keep the text literal.
- A real capture with `--no-clip` and a `%c` refuses:
  `` `%c` reads the clipboard: drop --no-clip or write \%c ``.

**Mac:**

- When the latest parse has a `directive` span with `directive: "clip"`, the debounced
  live preview runs the clipboard-resolving dry run (no `--no-clip`). Otherwise it keeps
  `--no-clip`.
- This relaxes the precondition in `BobProcessClient.swift:1037` to the rule "clip reads
  only when bob reported a clip directive".
- **The Clip card** renders the `clip` object bob already returns:
  - a kind header ("Clipboard · 3 lines", "2 files · 1 image", "Snippet · 42 lines →
    file/clip-…md");
  - the child lines exactly as they will be written, with indentation;
  - thumbnails of the image attachments, from their local source paths;
  - for `%c3`, the entry boundaries as faint dividers.
- The "Clipboard markers stay literal" caption is deleted.

**Optional optimisation:**

- The app passes a hidden `--clip-generation <NSPasteboard.changeCount>`. Reading
  `changeCount` never reads content.
- bob caches the normalised read in XDG state, keyed by that generation, so repeated
  keystrokes do not re-read the pasteboard or Clipy.

### 4.8 Wire contract changes (both repos; one `!` per bob phase)

| Surface | Change |
| --- | --- |
| `capture-parse` spans | **Add** `directive` (attrs `directive: clip\|note\|template\|listen`, optional `count`) and `drawer` (attrs `title`, `exists`). **Remove** `clipboard`, `pomodoro_note`, `template_header`, `ref_listen`, `sub_bullet_section`, `global_sub_bullet_route`, `global_sub_bullet_block_id`, and the attached `task_type` on `+id` / `^id` |
| `capture-parse` needs | **Add** `directive`, `drawer`, `drawer_text`. A bare edge `#` → `task_type`. **Remove** `task_section` |
| `capture-complete` contexts | **Add** `directive` (rows: `token`, `name`, `summary`, `detail`, `disabled_reason`) and `drawer` (rows: `title`, `key`, `group: task\|recent\|new`, `entry_count`, `last_entry`, `note_count`, `last_seen`, `creates`, `refused`, `replacement`, `cursor_after`). **Add** top-level `initial_selection`, `footer`. **Remove** `task_section` |
| `capture` JSON | **Add** per-item `drawer: {title, key, created}` and the `type` row on drawer items. **Remove** `global_destination.mode` / `block_id`. `clip` gains `status`, `kind` |
| `capture-rewrite` | **Remove** the `start_template` rule |
| `capture-templates` | `draft` / `show` use `%t`; IDs are unchanged |
| CLI | `-D/--drawer` replaces `-S/--task-section`; `bob capture-drawers` (+ hidden `capture-task-sections`); `--clip` takes no header |

### 4.9 Glossary term (proposed text, to be written through `/sase_memory_write`)

> **Task Drawer** — *aka drawer*
>
> A labelled container inside a task: a direct child bullet with no checkbox whose text
> is an ALL-CAPS title (capitals, digits, spaces, and `& ' ( ) , . / -`), holding nested
> bullets of one kind of note — REQUIREMENTS, FUTURE WORK, MOTIVATION. Capture adds to
> one with `<text> @note+id#drawer`, matching the title exactly and creating the drawer
> (before any managed log) when it is missing; typing `#` after `@note+id` opens the
> drawer menu: the task's own drawers, then recent drawers from other tasks and
> project-note `##` sections. Promoting the task to a [[project-note]] turns each
> non-empty drawer into a `## Title Case` section, and restoring the project turns those
> sections back into drawers. Managed lines and logs (Depends-On, BLOCKS, LINKS, LINKED
> FROM, Schedule, Work, and Rotten Logs) are never drawers. Not a Markdown heading (the
> `@note#Heading` target), an [[annotation-section]], a Pomodoro, or a [[task-type]].

The same memory change should also update the related glossary terms:

- **Annotation Section:** "… or a `bob capture` target section" becomes "… or a task
  drawer".
- **Bulk Capture:** `@@template:` becomes `%t`.
- **Capture:** the live preview is `--no-clip` unless a `%c` is present.

## 5. Adjustments to the request (explicitly flagged)

| ID | Adjustment | Recommendation | Cost if skipped |
| --- | --- | --- | --- |
| **A1** | Retire `@route^id#type`; use `@route^id #type` | **Do it** | `^` vs `+` flips `#X` between a type and a place, a trap on a one-character difference |
| **A2** | `URL %` → `URL %l`; delete the `URL @` alias | **Do it** (required for a coherent `%`) | A bare `%` would need a URL special case, and the menu would be wrong after URLs |
| **A3** | Drop `%header` / `--clip=HEADER` | **Do it** (vault shows ~0 use) | It would need a `%c:header` spelling plus docs and tests for nobody |
| **A4** | Exact drawer match, plus a near-duplicate guard, plus a literal to insist | **Do it** (reliability) | Auto-create plus prefix matching gives state-dependent destinations and junk drawers |
| **A5** | A bare-sigil menu opens with no selection | **Do it** (reliability) | `jot idea #⏎⏎` writes a typed inbox task during the habit change |
| **A6** | Claim all `%…` tokens at edges; `\%` escapes | **Do it** | Old `%3` and `%build_log` silently become prose |
| **A7** | Read the clipboard in live preview only when `%c` is present; add a Clip card | **Do it** (this is Bryan's "better previews") | `%c` stays an opaque literal while typing |
| **A8** | `#drawer` on a project note's `^prj` writes to its `##` section | **Optional phase 4** | The same gesture fails after promotion (refuse with a hint pointing at `@note#Heading` until then) |

I did **not** adjust `%n`, though I noticed a naming risk. In Bob's vocabulary "note"
usually means a file (Project Note, Area Note, Inbox note). The menu label should
therefore read **"Pomodoro note"**. `%p` would be unambiguous, but `%n` matches Bryan's
mental model and the docs' existing "Pomodoro notes" section. Keep `%n`.

## 6. Alternatives considered

| Alternative | Why not |
| --- | --- |
| A non-`#` drawer sigil (`@foo+bar/req`, `@foo+bar>req`) | `/` is the goto picker. A glued `#` already means "place inside" for headings and Pomodoros, so `#` makes the rule more uniform, not less |
| Word directives (`%clip`, `%note`, `%template`) | Longer to type. The `%` menu supplies names and descriptions, so letters cost nothing in discoverability |
| Keep the `@@template:` header and only drop `@@@` | It keeps a mode switch inside the destination namespace and a header that must be the first line. `%t` is position-free and shares one menu with the other modes |
| `%t` anywhere in the draft, with rows above and below | More flexible, but rows above a template are ambiguous, and `@@@` never supported it. First-item-only preserves today's semantics exactly |
| Configured drawer vocabulary (`capture.drawers:` like `types:`) | The vault already reveals the vocabulary through the 101 project H2s, and a scan needs no upkeep. A config list could later pin rows, additively |
| Rank Recent by a capture-usage journal | Cold start is empty, and it misses drawers made by promotion or by hand. The vault scan sees both |
| Ensure Next on `#type` with body text | It mixes lane changes into note-taking. Only marker-only items change lanes, as today |
| Keep `--no-clip` meaning "literal %" | `\%c` is the uniform escape. Making `--no-clip` mean "don't read" lets preview parse `%c` properly |

## 7. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| **Version skew.** A newer app with an older bob: old bob reads `%t` / `%n` / `%c` as clipboard headers T/N/C, and `%t` drafts would write junk | Land bob first; the Mac phase depends on it. The `%` menu and directive spans appear only when bob reports them, so an older bob never shows the menu. Note it in the Mac release notes |
| An older app with a newer bob | Unknown contexts decode to `nil` and degrade to plain or no rows. `@@@` stops rewriting. The worst case is a bare `#` menu with row 0 selected until the app updates. That window is acceptable and is closed by A5 in the Mac phase |
| Junk drawers from typos | A4 guard (refuses on this task), catalog warning, preview "New drawer" capsule, optional hide |
| printf-style `%n` / `%c` at a line edge in dev notes | Mid-line is prose; at an edge, `\%n` escapes. The directive is visible in the preview |
| Pasteboard-privacy prompts on future macOS | Reads happen only after an explicit `%c` or `%`. The optional `changeCount` cache reduces reads. Content-free type detection is available for the menu peek if needed |
| Scan cost on every `#` keystroke | The cached mtime/size scan with a 60 s TTL, as relation labels do today. Re-measure against `docs/completion.md`'s PT3 budget |
| **Large doc churn.** `docs/capture.md` is 7,361 lines with many `#`/`%`/`@@` rows | Treat docs as part of each phase. `just docs-check` and the search-smoke queries (`@@template`, `task section`) gate it |

## 8. Implementation shape (for the plan)

The work fits one epic with four phases. Each bob phase lands as one coherent
`feat(capture)!` commit, so grammar, help, docs, and tests never disagree on master.

1. **`cli-directives` (large)**
   - New `src/native/capture_language/directive.rs` holds the lexer, masking, spans,
     needs, and errors. Remove the trailing-`#`, `%`-clipboard, and URL-listen lexing
     from `line.rs`, `markers.rs`, `draft.rs`, `item.rs`, `editor_classify.rs`, and
     `editor_parse.rs`. The `PomodoroNote` and clip executors stay as they are.
   - `template.rs` framing moves to `%t` (delete `HEADER`). In `rewrite.rs`, delete
     `start_template`. In `capture_templates/`, render `%t`.
   - In `type_marker.rs`, a bare edge `#` becomes incomplete. `completion.rs` and
     `capture_complete/task_types.rs` gain `initial_selection`.
   - New `capture_complete/directives.rs`. Update the help in `capture/cli.rs`,
     `capture_parse.rs`, `capture_complete/cli.rs`, and `capture_rewrite.rs`, then run
     `just docs-gen`.
   - Docs: `docs/capture.md`, `docs/reference/capture-syntax.md`, `docs/completion.md`,
     `docs/task-types.md`. Glossary updates go through `/sase_memory_write`.
2. **`cli-drawers` (large)**
   - Rename `capture_task_sections.rs` to `capture_drawers.rs`, with exact resolution,
     creation, reserved names, and the guard. `capture/sub_bullet.rs` handles creation
     and placement.
   - In `tokens.rs`, `#` after `+id` is always a drawer. Delete the attached-type
     machinery (A1).
   - Allow `#type` on sub-bullet items (`capture/plan.rs`, `task_theme.rs`).
   - New `src/native/drawers/{mod,scan}.rs` catalog, modelled on `relation_labels/scan.rs`.
     New `drawer` completion context.
   - Delete `@@route+id` from `draft.rs`, `model.rs`, `editor_parse.rs`,
     `capture_parse.rs`, `capture/output.rs`, `capture/plan.rs`, and
     `capture_related/draft.rs`.
   - CLI: `-D/--drawer`; `capture-drawers` with the hidden alias.
   - Glossary: add **Task Drawer**.
3. **`mac` (large, bob-mac-capture)**
   - The directive menu view.
   - The drawer menu: groups, a create row, refused rows, and the footer. Fix "1 items".
   - `initial_selection: none`, with Tab taking the top row.
   - The live clip preview gate and the Clip card.
   - Delete `CaptureTemplateStart`, the `@@` template candidate and hint, and
     global-parent handling.
   - Shelf drafts in `%t` form.
   - Regenerate fixtures from the landed bob; update `fake-bob`, tests, and docs
     (`capture-panel.md`, `capture-previews.md`, `task-pickers.md`, `protocol.md`,
     `keyboard.md`, `saved-templates.md`).
   - Follow the macOS compile rules in its `AGENTS.md`, and run a manual smoke with
     screenshots.
4. **`prj-drawers` (optional, medium)**
   - A8: H2 sections act as drawers on `^prj`. Exact key match; create `## Title Case`
     at the end of the note, as promotion does.
   - Ctrl+D drawer hide with a per-host journal.
   - Drawer-only parent lines with authored children.

**Verification gates:** `just check`, `just docs-check`, and `just all` on bob-cli. A
`git grep` for `@@template`, `pomodoro_note`, `task_section`, `sub_bullet_section`,
`global_sub_bullet`, `ref_listen`, and `task-section` should find only the hidden
command alias. The masking property test should be extended to directives.

## 9. Open questions for Bryan (with my defaults)

1. A1, retire the attached `@route^id#type`? **Default: yes.**
2. A8, project-note `^prj` drawers → `##` sections in this epic or later? **Default:
   phase 4, optional.**
3. A drawer-only parent line plus children: allow now? **Default: later. It is additive.**
4. Record a decisions note ("a glued `#` names a place; a free `#` names a type; drawers
   are created on demand and matched exactly")? **Default: yes.** This is a cross-repo
   grammar rule that later plans will want to cite. bob-cli-ep skipped its record, and
   this one would supersede nothing.

## 10. Recommended solution

Ship one epic, **"Capture drawers and `%` directives"**, in the order cli-directives,
then cli-drawers, then mac, with an optional prj-drawers phase.

1. **`#` follows one rule.**
   - A glued `#` names a place inside the thing before it:
     - `@note#Heading`;
     - **`@note+id#drawer`**;
     - `@note:id#pomodoro`, `=#name`, `@note^id+#name`.
   - A standalone `#word` names a type: `Note @foo+bar#requirements #fix` adds the note
     and retypes `^bar`.
   - `@note^id#type` and `@note+id#type` are retired (A1).
   - A bare `#` at an edge opens the type menu immediately, with no row preselected (A5).
2. **Task drawers.**
   - Exact title match (slug or `#"LITERAL"`), created on demand before managed logs.
   - Spelling borrowed from the vault catalog.
   - Reserved managed names and `TASKS` are refused, and near-duplicates on the same
     task are refused unless quoted (A4).
   - `#` after `@note+id` opens a menu with ON THIS TASK, RECENT (task drawers plus
     project-note H2s, ranked by recent note count), and a **New drawer** row, with a
     consequence footer.
   - CLI: `-D/--drawer` and `bob capture-drawers`. Add the **Task Drawer** glossary term.
3. **`%` directives answer "how".**
   - **The directives:** `%c`/`%c<N>` (clip), `%n` (Pomodoro note), `%t` (template;
     first item, anywhere in it, never rewritten), and `%l` (listen, bare URL only; A2).
   - **Unknown and escaped forms:** any other `%…` at an edge is an error, and `\%` is
     the escape (A6).
   - **The menu:** typing `%` opens a bob-described menu with live context (clip peek,
     the target Pomodoro, template rows) and dimmed, explained rows for inapplicable
     directives.
   - **Clip previews:** live preview reads the clipboard only when a `%c` is present,
     and renders a real Clip card (A7). `%header` is dropped (A3).
4. **Removed outright:**
   - trailing `#`;
   - `%`, `%N`, `%header`;
   - `URL %` and `URL @`;
   - `@@template:` and `@@@`;
   - `@@route+block-id`;
   - prefix drawer selection;
   - every "task section" name.

   Old habits fail loudly through ordinary grammar errors, never through compatibility
   shims.

The result is a grammar Bryan can explain in three lines: **`@` where, `#` what (or the
place inside a `@`), `%` how.** Every remaining marker sits in one of those families.

## Sources

- bob-cli:
  - `docs/capture.md` (Grammar at a glance; the `#` table at 152-163; Global destination
    at 331; Bulk templates at 598; Clipboard at 838; Saving links at 946; Sub-bullets at
    4519; Pomodoro notes at 4771; Section bullets at 4812);
  - `docs/reference/capture-syntax.md`;
  - `docs/projects.md:370-397`;
  - `src/native/capture_task_sections.rs:210-250`;
  - `src/native/relation_labels/{mod,scan}.rs`;
  - `src/native/capture_language/{template,rewrite}.rs`;
  - `src/native/capture/cli.rs:511-667`;
  - git history for the feature dates.
- Plan and bead:
  - `plan:202610/capture_hash_type_marker.md`, epic `bob-cli-ep`, and its decisions;
  - `research:202610/bulk_capture_template_drafts/` (rationale for the `@@template:`
    header).
- bob-mac-capture (read-only audit):
  - `Sources/BobMacCapture/CapturePanelModel.swift`;
  - `Sources/CaptureCore/{BobProcessClient,CompletionRowContent,CaptureModels,CaptureTemplateStart}.swift`;
  - `docs/{capture-previews,capture-panel,relationship-pickers}.md`.
- bob-plugins:
  - `plugins/bob-navigation-hotkeys/src/010-requires-and-config.js:117` and `main.js`
    (promotion and reversal section titles).
- Memory:
  - `decisions:mac-capture-is-a-thin-client`;
  - the roster summaries of `decisions:bob-cli-releases-ride-a-daily-train`,
    `decisions:relation-card-tab-accepts-ctrl-d-hides`, and
    `decisions:theme-hide-is-recent-only`;
  - CLI rules memory;
  - glossary: Project Note, Bulk Capture, Capture, Task Type, Annotation Section.
- Vault statistics: a read-only scan of `~/bob` on apollo, 2026-10-31.
- macOS pasteboard privacy:
  - [Michael Tsai — Apple (via Jeff Nadeau) on pasteboard privacy](https://mjtsai.com/blog/2025/05/12/)
  - [AppleTreats — macOS 16 will warn when apps access pasteboard](https://appletreats.substack.com/p/macos-16-will-warn-when-apps-access)
  - [DEV — macOS Tahoe clipboard history](https://dev.to/jrw0ng/macos-tahoe-has-built-in-clipboard-history-heres-what-its-still-missing-for-developers-2026-4eko)

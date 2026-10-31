# Capture syntax cleanup: drawers + `%`-directives — research & recommendation

## Scope

Bryan's proposal, in short:

1. Retire `@file+id#type`; `#` after `@file+id` always means **drawer**
   (an ALL-CAPS task child bullet). Typing is done with a separate `#type` token.
2. `#` after `@file+id` completes existing drawers on that task, then recent
   drawers from other tasks / project-note H2s. Missing drawers are created.
3. New glossary term: **task drawer** (drawer).
4. Migrate trailing-`#` (Pomodoro note), `%` (clipboard), `@@template` to a
   unified `%<C>` directive family: `%c` clip, `%n` note, `%t` template.
   `%` alone shows directive help in Bob Mac Capture; this unblocks the task-type
   menu immediately after a bare `#`.
5. Remove `@@file+id`. No backward compatibility for recently-added syntax.

Prior art: epic `bob-cli-ep` (closed 2026-10-31) shipped `#<type>` replacing
`t:`, including the marker-only `@route+id#type` Ensure-Next-and-retype form,
with reviewer decisions `bare_hash_menu = letter`, `retire_t = prose`,
`memory_record = no`. The plan file is
`sase/repos/plans/202610/capture_hash_type_marker.md`.

## Current-state findings (verified in tree)

- **The `#`-after-`@route+id` ambiguity is real and load-bearing.**
  `docs/capture.md` §"Task Link toggle" + §13: with body text,
  `@route+id#section <text>` is a sub-bullet under an ALL-CAPS section;
  with no body/children, `@route+id#type` is Ensure-Next-and-retype.
  `@route+id#` (empty) opens the *task-type* menu when marker-only, the
  *task-section* menu when body-bearing (`src/native/capture_complete/cli.rs`
  ~L214-220, `docs/completion.md` §Capture markers). One sigil, two menus,
  disambiguated by a whole-item body predicate shared across lexer,
  classifier, and `editor_classify.rs`. It works, but it is exactly the kind
  of subtle the proposal wants to kill. The proposal's split (drawer `#drawer`
  + free `#type`) removes the shared predicate entirely — a genuine
  simplification, not just a rename.
- **The "drawer becomes H2" premise is true.** `docs/projects.md`
  §"Create project note from task": a direct-child bullet with no checkbox,
  ALL-CAPS title, and ≥1 nested item converts to a `## Title` section on
  promotion (title-cased: `FUTURE WORK` → `## Future Work`, reusing a matching
  `##` case-insensitively). So "drawer" names something the vault already
  does. The glossary term writes itself.
- **`@@route+block-id` vs `@@route` are different things.**
  `src/native/capture_language/draft.rs` (~L690-700, L1250-1335): a bare
  `@@route` routes otherwise-unrouted items (and default refs); `@@route+id`
  is the *shared parent-task destination* for otherwise-unrouted items.
  The proposal says "`@@file+id`" was obsoleted by `@@template`. That is only
  half right: per-row destinations inside a template do obsolete the
  `+id` global, but the *bare* `@@route` global (default-ref routing,
  whole-draft destination) has no template equivalent. **Remove only the
  `+id` form; keep bare `@@route`.**
- **Bare-`#` menu was already considered and rejected — for a reason that
  `%n` removes.** Epic decision `bare_hash_menu = letter`: a menu on bare `#`
  breaks Pomodoro notes because Return accepts row 0. Once trailing `#`
  migrates to `%n`, bare `#` at a marker position is unreserved, and
  menu-on-bare-`#` becomes safe. The proposal's two halves are mutually
  dependent: do `%n` first (or atomically), or the `#`-menu change regresses
  Pomodoro notes. Sequence matters; see recommendation.
- **Template is draft-level state, not a line marker.** `@@template:` must be
  alone on the first nonblank line; definition ends at the first blank line;
  rows follow; `{0}`-only rows split on whitespace; templates refuse `%`,
  session operators, and other `@@` declarations (`docs/capture.md`
  §Bulk templates). A `%t` that "stays where typed" cannot preserve these
  semantics without answering: where does the definition end and rows begin
  if `%t` sits mid-draft? What scopes the row separator? This is the
  riskiest part of the proposal as written.
- **Completion has latency budgets.** `bob-cli-ep.1` closeout notes paired
  debug benchmarks with explicit per-command limits (capture-complete
  ~60 ms, capture-parse ~50 ms). A "recent drawers" source that scans the
  vault per keystroke will blow those budgets. It needs a prebuilt index,
  not a scan.
- **Prefix matching + auto-create don't mix.** Today `#future-work` matches
  `FUTURE WORK` by whole-slug-then-prefix (`docs/capture.md` §13). With
  create-on-miss, a prefix query is ambiguous: does `#req` mean the existing
  `REQUIREMENTS` or a new `REQ` drawer? Auto-create forces exact matching
  (case-insensitive, slug-normalized), which is also what the picker path
  (`--task-section`, exact title match) already does.
- **`%` is more crowded than the proposal suggests.** `markers.rs`
  `parse_clip_token`: bare `%` (live clip), `%N` (history count), `%header`
  (named header); plus the URL-listen `URL %` alias (`@` remains compatible),
  template refusal of `%`, `--clip`/`--no-clip` flags, and live preview's
  `--no-clip` interplay. `%c` must absorb all three clip forms
  (`%c`, `%c3`, `%cbuild_log`), bare `%` becomes "incomplete: need directive",
  and `URL %` needs a new listen spelling (`URL %c`? collides with clip —
  see recommendation). Every one of `capture-parse`, `capture-complete`,
  `capture-rewrite`, shell completion, zsh rows, and `docs/completion.md`
  must move together; the `cli` phase of the last epic is the template for how.
- **Removal vs CLI rules.** `cli_rules.md` (reference memory): never
  hard-remove; old spellings become permanent hidden aliases. But capture
  *grammar* markers just broke contract with `!` (`feat(capture)!:`,
  `t:` → prose, `@route+id#NAME` meaning change) under the release-train
  rule. Grammar markers are not CLI flags; the `!`-and-migrate convention,
  not hidden aliases, is the established path. Say so explicitly in the plan
  so reviewers don't relitigate it.

## Critique: is this a good idea?

Yes, with adjustments. The core insight is correct: `#` is overloaded to the
point of needing a dispatch table (`docs/capture.md` "Read it by what it is
attached to" lists ~20 meanings), and the body-presence predicate for
`@route+id#…` is the worst of them because it is invisible. Splitting type
from drawer gives each `#` exactly one reader:

- `#` at a free marker position → task type (menu on bare `#`, since `%n`
  frees it).
- `#` glued to `@route+id` → drawer, always.
- `#` glued to `@route` / `@route:id` / `@route^id+` / `=` → unchanged
  (heading bullet, Pomodoro name/link, named start).

That is strictly more consistent than today, and "create the drawer if
missing" matches how `@route#Section` bullets already fall back to the
zeroth section rather than erroring.

Three things I would change:

1. **`%t` should be a header-line rename, not an inline marker.**
   Keep draft-level template semantics byte-identical and just spell the
   header `%t` (alone on the first nonblank line, case-sensitive — one
   spelling, unlike `@@template:`'s case-insensitivity). "Leave it where
   typed" then falls out naturally for the `@@@`- Evolutions: the Mac app's
   `@@@` expansion writes `%t` instead of `@@template:`. An inline mid-draft
   `%t` is refused like a misplaced header today. Rationale: templates need
   definition/row framing; no line-marker design preserves
   multi-line definitions, `{0}`-splitting, and blank-line row separation
   without inventing a second framing mechanism. If Bryan wants per-item
   templates later, that's a separate epic.
2. **Don't overload `%c` with listen; give listen its own letter.**
   `URL %` (companion-audio request) is neither clipboard nor note nor
   template. Folding it into `%c` makes `%c` context-dependent again — the
   disease being cured. Add `%l` (listen): `URL %l`, with `@` kept as the
   legacy alias only if cheap, else retired with the rest. `%` + letter with
   no match is refused with the directive menu, which doubles as the
   "good description" the Mac app shows on bare `%`.
3. **Auto-create with exact match + a safety rail, not prefix match.**
   Exact case-insensitive slug match (normalize `-`/`_` vs space, as
   promotion title-casing implies); on miss, create. Keep the
   `--task-section` exact-match picker path as the power tool. Rail: refuse
   to create when the drawer name collides (case-insensitively) with a
   managed child (`SCHEDULE LOG`, `WORK LOG`, `LINKS`, Depends-On line,
   generated section) — writing `**SCHEDULE LOG**` as a plain drawer would
   corrupt machine-owned structure. List managed names in the refusal.

Smaller adjustments:

- Recent-drawers source: a small MRU shelf (`capture/drawers.json`-style,
  same 0700/0600 + LRU-cap pattern as the template shelf), fed by successful
  drawer writes, merged with (a) the target task's own drawers (top rank)
  and (b) project-note H2 identities de-numbered per the article-selector
  rule already in `docs/capture.md` §Section bullets. Cap shelf at ~36 like
  templates; cap completion rows (5 empty / 12 nonempty, mirroring Pomodoro
  name rows). Never vault-scan in the completion path.
- Promotion title-casing means drawer identity should be compared
  case-insensitively everywhere, and recent-drawer rows should display the
  H2's own casing with a "from project note" annotation.
- `%n` composes with `%c…` exactly like trailing `#` does today (allowed
  together, either order); rejected alongside `s:`/`$`/routes/forced
  destinations, unchanged. Keep the conflict table, rename the column.
- Keep `\#` escape and `#1234`-is-prose and `##` rules untouched; bare `#`
  at a marker position now opens the type menu with row 0 selected (Return
  types immediately — the *desired* behavior once Pomodoro notes are gone).
  `@notes#` / `@notes#Ideas` (heading bullets) never open the type menu:
  the `#` is glued to a route, not at a free marker position.
- `@@route+id` removal: refuse with a teaching error pointing at per-row
  destinations / templates for one release-train cycle, then prose. Keep
  `@@route`, `@@template:`→`%t` teaching error likewise. Refusals, not silent
  prose, for `@@` forms (they're declarations, and silent prose would
  silently misroute whole drafts — worse than a mistyped task).

## Recommended solution

**Epic shape** (two phases, one coherent `cli` landing + one `mac` landing,
release-train `!`):

- **Phase 1 — `cli`: drawer/type split + `%`-directives + removals.**
  1. Lexer: `#` glued to `@route+id` is always a drawer selector (delete the
     marker-only/body predicate; delete the `@route+id#type` Ensure-Next
     path). Free-standing `#<type>` (either edge, including bare `#` →
     menu) types new or existing tasks; `@route+id` items take `#type` as a
     second token (`Note @foo+bar#requirements #fix`).
  2. Drawer matching goes exact (case-insensitive, slug-normalized);
     create-on-miss with the managed-child rail above. Update
     `capture-task-sections` docs to note the asymmetry (read path lists,
     write path creates).
  3. `%c` (absorbing `%`/`%N`/`%header` as `%c`/`%cN`/`%cheader`), `%n`
     (trailing-`#` replacement), `%l` (URL listen), `%t` (header-line
     template). Bare `%` at a terminal position: incomplete, need directive;
     completion offers the four rows with one-line descriptions (this is the
     same data the Mac app shows on `%`). `URL %` → refused with a
     `URL %l` hint. `@@template:` → refused with a `%t` hint.
     `--clip`/`--no-clip` flags stay (flag layer is orthogonal); keep
     `URL %1` working as explicit clip.
  4. Remove `@@route+id` (teaching refusal, keep bare `@@route`). Retire
     trailing-`#`, bare-`%`-clip, `@@template:` spellings to teaching
     refusals in the same `!` commit — one migration, one BREAKING CHANGE
     footer naming each retired spelling.
  5. Completion: `@route+id#` → drawer menu (own drawers, then MRU shelf,
     then project-note H2s, each badged by origin); free `#` → type menu
     (bare included); bare `%` → directive menu. Shell/zsh rows follow.
  6. Docs: `docs/capture.md` (grammar, conflict tables, template section),
     `docs/completion.md` (three menus), `docs/task-types.md` PT12 exception
     (unchanged — still refuses unconfigured), glossary `drawer` strand,
     clap help + `just docs-gen` + `just docs-check`.
- **Phase 2 — `mac`: thin-client rendering.** Swift stays sigil-agnostic:
  render the three completion contexts' rows/headers/footers from
  `capture-complete`; `%`-menu descriptions; `%t` header expansion replacing
  `@@@`→`@@template:`; fixture regen with the new bob; smoke on the Mac.
  No grammar, preview, or write logic in Swift (thin-client decision holds).

**Glossary strand** (`drawer`, aka "task drawer"): a named ALL-CAPS
direct-child bullet list under a task that groups its sub-bullets
(`REQUIREMENTS`, `FUTURE WORK`); addressed by `@route+id#drawer`; created on
first capture; converts to a `## Title` section if the task is promoted to a
project note; distinct from note `##` sections and from managed children
(schedule/work logs, LINKS, Depends-On), which are never drawers.

**Sequencing constraint:** land `%n` and the bare-`#` menu atomically (same
`cli` commit). Landing the menu first breaks Pomodoro notes; landing `%n`
first orphans bare `#` (harmless but confusing). The epic's
`bare_hash_menu = letter` decision is superseded by this proposal — record
that explicitly, since decisions are immutable and this reopens a decided
alternative: the reopening condition is met *by* the `%n` migration, which
removes the premise (Pomodoro-note capture on `#`) the decision rested on.

**Verification:** `just check`, `just docs-check`, `just all` (per
`bob-cli-ep.1` closeout); paired debug benchmarks for `capture-parse` /
`capture-complete` against the epic's limits; lexer conformance vectors for
each retired spelling (refusal codes), drawer create/exact-match/rail cases,
`%`-menu and `#`-menu completion fixtures, and template `%t` header parity
(`-E` expansion byte-identical to `@@template:`).

# `@foo^bar` as an exact task goto — research and recommendation

- Status: research, not a plan. No workspace paths inside.
- Question: should a capture draft that is exactly `@foo^bar` jump to the `^bar` task in `foo.md`, the same landing the `/` Go To picker produces when its row is accepted?
- Screenshot context: `~/tmp/screenshots/20261125_135534.png` shows the Mac capture panel with input `@bob^intention-rollovers`, red error `capture item 1 starting on line 1: task text is required; pass TEXT or pipe it on stdin`, `Preview failed`. The draft the user typed is a bare `@route^id` token with no body.
- Short answer: yes, claim exactly that hole — and nothing else — as a read-only exact goto. It is the only free slot in the `@`/`:`/`^` matrix, it matches the sigil story, and it can reuse the entire `/` landing stack. Details below narrow the claim so it stays intuitive, reliable, and beautiful, and list the adjustments I would make to the request as stated.

## What I verified in the tree

All commands below ran against the current checkout and its live vault (`~/bob`).

Current grammar facts (from `docs/capture.md` and `docs/reference/capture-syntax.md`):

- `@` says where, `#` names a place or a type, `%` says how. See `docs/capture.md` § Grammar at a glance and `decisions:capture-sigils-say-where-what-how`.
- `@route^block-id` with task text creates an ordinary open task with an authored block ID (`docs/capture.md` § Task with a requested block ID; `docs/reference/capture-syntax.md` § `@route^block-id`). The block ID uses letters, digits, `-`.
- `@route:block-id` with task text creates a Next task plus a Pomodoro Task Link. The same token with no other text links the existing task into today's ledger (no new task), optionally starting the session with `=<X>` (`docs/capture.md` § Linking and starting existing tasks; `docs/reference/capture-syntax.md` § Link an existing task).
- `^route:block-id` is the active-task spelling of that link, with identical execution.
- `/query` as the whole draft is the Go To Tasks picker: fuzzy search over the same catalog `:` uses (linkable open tasks in routable inbox, area, non-terminal project notes), picking a row opens it in Obsidian and never writes (`docs/capture.md` § Going to a task with `/`). `bob capture` refuses it with teaching error T3, `capture-parse` reports `mode: incomplete` needing `task_goto`, `capture-complete` serves context `task_goto` with `replacement: ""`, plus a `picker` descriptor `{kind, scope: vault, scope_token: "/"}`.
- `//query` is the parallel Go To Notes picker (`note_goto`), refused with T4.
- `bob capture` and `--dry-run` refuse a claimed `/` or `//` draft before any other item parser, before the `&` scan, so forced flags (`-r`, `-s`) change nothing and no vault file changes.

Live probes (evidence, not inference):

```text
$ bob capture-parse -f json -- '@bob^intention-rollovers'
{"ok":true,"schema_version":1,"grammar":29,"input":"@bob^intention-rollovers",
 "body":"","mode":"task","route":"bob","section":null,"block_id":"intention-rollovers",
 "needs":[],"spans":[...],"diagnostics":[]}

$ bob capture --dry-run -- '@bob^intention-rollovers'
bob capture: capture item 1 starting on line 1: task text is required; pass TEXT or pipe it on stdin

$ bob capture-parse -f json -- '@bob:intention-rollovers'
{"ok":true,...,"mode":"pomodoro_link","route":"bob","block_id":"intention-rollovers",...}
```

So today the caret-alone draft parses as a `task` creation missing its body (dry-run fails on the generic missing-text error), while the colon-alone draft parses as a `pomodoro_link`. The caret-alone-with-no-text slot is unclaimed semantically: it can never succeed as a creation, because creation needs text. That is the hole to claim.

The vault already anticipates this feature. In the live vault `bob.md` there is an In Progress row (seen via `capture-complete` used-ID listing):

```text
- [/] #task Allow `@foo^bar` syntax to jump to `^bar` task in Obsidian! ^capture-hat-jumps
```

and the target the screenshot names exists:

```text
- [*] #task Add support for "intention rollovers"! ^intention-rollovers   (bob.md:82)
```

Landing stack to reuse: `docs/reference/plugins/goto-task-uri.md` defines `obsidian://bob-goto-task?path=<absolute>&line=<1-based>&ref=<LINE:digest>[&block=<id>]`, read-only, no stamps, no lanes, no ledger, no Task Card. `docs/reference/mac-capture/task-pickers.md` says a Go To pick dispatches that URI and, once the open succeeds, hides the panel and discards the draft. Bob Mac Capture is a thin client of these `bob` JSON interfaces (`decisions:mac-capture-is-a-thin-client`), so the Mac side should need only rendering, not new resolution.

Memory constraints checked via `sase memory read`: `cli_rules.md` (never add a subcommand under `bob capture`; `capture-*` protocol names are frozen siblings, additive only), `docs.md` (behavior change needs contract/reference updates; run `just docs-check`), `decisions:notebook-routes-write-notes`, `decisions:capture-bullets-mirror-the-task-block`, `decisions:capture-reserves-clock-tags`.

## Requirements as I understand them, with adjustments

The request: submitting `@foo^bar` jumps to the `^bar` task in `foo.md`, as if the user searched with `/` and accepted the row.

Adjustments I recommend (all called out explicitly):

1. **Whole-draft claim only, not anywhere in a line.** Like `/` and `//`, the goto claim is per draft, not per item: the whole draft must be one whitespace-delimited token `@foo^bar` (surrounding whitespace ignored). `@foo^bar` with body text, child bullets, a trailing `@` seal, `%`/`s:`/`$` markers, or a second line stays exactly what it is today (creation, project-note seal, or error). Rationale: `/x` with a child line or with `@@work` on another line is already prose (`docs/capture.md` §§ Going to a task with `/`, Going to a note with `//`). Mirroring that rule avoids stealing the creation syntax `Write outline @work^outline` and the seals `@route^id@` / `@route^id@#pomodoro`.
2. **Exact jump, not a fuzzy picker.** `/` is fuzzy and needs a pick. `@foo^bar` names the note and the block ID exactly, so submit should jump directly with no second pick step. While typing, preview should show the single resolved row (same human row format as `task_goto`: `[status] text · note_path:line`). If the exact target does not resolve, do not fuzzy-fall-back silently; show the precise miss error (see § Behavior) with a hint to use `/` for search. This is the beautiful part of the proposal: bare means goto, with text means create — a two-line teaching table covers the whole feature.
3. **Same note resolver as the link path, same ID validator.** Route lower-cased, `A–Z a–z 0–9 _ -`, vault-root stem, aliases resolve the same way link resolution does; block ID `[A-Za-z0-9-]+`, case-sensitive. Do not invent a second resolver, quoted-component syntax (`&"Shopping List":bar` style), or nested `projects/foo` support for `@` unless the link path gains it first. If `@` ever grows nesting, goto inherits it for free.
4. **Scope to task-bearing living notes; notebooks stay notes.** On a notebook route (`@nb^id`), the token already means a named note. Goto must not fire there. Rule: the goto claim applies only when the resolved route is not a notebook/album/record hub; notebooks keep their existing `notebook_note` parse. This follows `decisions:notebook-routes-write-notes` (notebooks hold only note bullets, never tasks).
5. **Read-only like `/`, not link-like `:`**. No Task Link, no Next raise, no freshness stamp, no dependency drop, no ledger write, no walk move, no `#prj_is_blocked` side effects. The colon-alone form already owns the link semantic; caret-alone must own the goto semantic. Keep the asymmetry explicit in the docs table rather than papering it over.
6. **Closed-task policy: resolve by exact ID regardless of status, but say what landed.** `/` defaults to open tasks (`-C` opts into closed vault-wide history). An exact `@foo^bar` names one row; refusing just because it is done would be pedantic when the user gave an exact locator. Recommend: resolve living-note tasks of any status by exact `note+block`; report `closed` in the preview row when it applies (the `task_goto` candidate already carries `closed`); archive/`done/` paths are out of scope and refuse with a `//`-hint. This is slightly more permissive than `/` and matches how `[[foo#^bar]]` behaves (it opens whatever is there).

## Critique: is this a good idea?

Yes, with the narrowing above. Strengths:

- **Fills a real hole.** Caret-alone with no text can never succeed today; the error in the screenshot (`task text is required`) teaches nothing and suggests the wrong fix (add text). Replacing it with a goto turns a dead end into a shortcut.
- **Teachable.** The sigil story survives: `@` where, `^` which block. Colon links-and-plans, caret names-and-opens. Bare `@foo^bar` opens; adding words before or after it creates. That duality is easy to demo and fits in the existing `@route^block-id` vs `@route:block-id` table without a new sigil.
- **Cheap to build correctly.** Resolution, ranking-free lookup, URI landing, and refusal-before-write all exist. The Mac app already hides on goto success and discards the draft. No new daemon, no new index, no network.
- **Complements, does not replace, `/`.** `/` stays the discovery tool (fuzzy, cross-note, ID-less rows welcome). `@foo^bar` stays the addressing tool (exact, one keystroke-free jump for a locator you already know or just copied from a link). Both dispatch the same URI.

Risks and honest costs:

- **Caret/colon asymmetry will confuse someone once.** Today `^route:block-id` and `@route:block-id` (alone) both link. After this change `@route^block-id` (alone) opens while `^route:block-id` still links. The mnemonic (caret names a block; colon links one) helps, but expect one round of "why doesn't `^bob:xxx` goto?" The alternative — flipping `^route:block-id` to goto as well — would break the active-task link spelling and its `=X` start suffix, so do not do it. Document the pair as a deliberate contrast.
- **Notebook collision needs the carve-out.** Without adjustment 4, `@nb^id` becomes ambiguous. The carve-out costs one sentence and one branch, but skipping it would corrupt notebook capture.
- **Project-seal prefix risk.** `@foo^bar@` (create project) and `@foo^bar` (goto) differ by one trailing byte. The grammar must require end-of-token after the ID for goto, and the Block ID Picker's type-through behavior (typing `#`/`=`/`@` after an ID commits the ID and keeps typing) must not misfire on a goto draft. Tests must cover the one-byte boundary both ways.
- **Duplicate-ID and stale-line hazards.** Duplicate `^bar` in one note must fail closed (jump.rs already has a `duplicate_block_id_fails_closed` test pattern for landings). The goto response should carry the same `line` + `ref` (`<line>:<digest>`) + `block` triple the URI handler uses to re-find the line, so a note edited between preview and submit still lands sanely or reports `Task changed since search`.
- **Grammar bump and protocol churn.** This is a user-visible grammar break in the additive sense: new `needs`/`context` or a new mode, new spans, new teaching errors. Per `cli_rules.md` the `capture-*` names only grow additively; per `docs.md` the contract plus `just docs-check` must move with it. Budget for docs and Mac-app strings, not just Rust.

Would I take a different approach? I considered and would reject:

- **Fuzzy `@foo^bar` that opens a picker.** Loses the exactness advantage, duplicates `/`, adds a pick step to a locator that is already precise.
- **Reusing `@foo:bar` for goto (overloading colon).** Colon-alone already links (and drops own-prereq blockers, relocates links, optionally starts sessions). Overloading it would make a read-only gesture look like a planning gesture. Keep colon for writes.
- **A new sigil or `//`-style `@@` form.** No new sigil is needed when an unusable token shape already exists; a new sigil would need new completion, new help, and new muscle memory for zero extra power.
- **Bare `foo^bar` without `@` or `^foo:bar` flip.** `^` as first byte already owns the active-task link spelling; `foo^bar` with no sigil collides with prose (`Plan +5` stays prose for exactly this reason). `@` must stay the goto introducer so the draft is unambiguous.

## Recommended design (bob-cli first, thin client second)

### Claim rule

A draft is an exact task goto when, after trimming surrounding whitespace:

- the draft is a single line, a single whitespace-delimited token,
- the token matches `@<route>^<block-id>` exactly (route grammar and block-ID grammar as today, no trailing `@`, no `#section`, no `#pomodoro`, no `=X`, no `!`, no `+id`, no directives),
- the resolved route is not a notebook/album/record destination,
- there are no child bullets, no second item, no `@@` interaction (a `@@route` declaration on another line makes the draft two items/lines, so the claim does not apply — same as `/`).

Everything else keeps today's parse. In particular `Write outline @work^outline`, `@work^outline@`, `@work^outline@#bugs`, `@work^outline#section`, and `@nb^note` never become gotos.

### Resolution

1. Resolve `<route>` with the same resolver the `@route:block-id` link path uses (lower-case, alias-aware). Unresolvable route: refuse with near-miss hints, same family as link errors, plus `— to search all tasks, type /query`.
2. Look up `^<block-id>` in that note's task lines (any `#task` checkbox line carrying that trailing block token). Exact, case-sensitive. One hit: that is the target. Zero hits: refuse `no task ^<id> in <route>.md — to create it, add text before the marker; to search, type /<query>`. Two or more hits: refuse `duplicate block ID` and name both lines (fail closed, never guess).
3. Target may be any status on a living note; surface `status_symbol`, `status_name`, `section`, `depth`, `line`, `ref`, `note_path`, `target`, `closed` when present — the same fields `task_goto` candidates already carry. Hidden/dot, `_templates`, fenced-code, and non-task block anchors are never targets.
4. No writes at any stage: no block minting, no `capture-task-id` suggestion flow (that flow is for `:` link creation; here an ID-less task cannot be named by the draft because the draft has no text — direct the user to `/` or to the note).

### Wire shape (additive, reuses `/`)

Prefer the smallest change the Mac app can adopt without a fork:

- `capture-parse`: `mode: "incomplete"`, `needs: ["task_goto"]`, one `interactive_placeholder` span over the whole `@foo^bar` token (sigil included), `body: ""`, plus `route`/`block_id` echo for diagnostics. Do not invent `needs: ["task_caret_goto"]` unless the Mac team needs to distinguish the empty-fuzzy (`/`) card from the exact-singleton card; if they do, add `task_goto_exact` as a second additive need rather than renaming.
- `capture-complete`: context `task_goto` (same candidate row shape, same `replacement: ""` never-insert rule, same `picker` descriptor with `scope_token: "@"` vs `"/"` noted in the descriptor so the app can label the card `Go To · exact`). Empty-filter refetch at `replacement.start` returns the one resolved row or empty with the miss reason; fuzzy filtering over that singleton is unnecessary. Keep `-C` honored for parity but document that exact lookup already spans statuses on living notes.
- `bob capture` / `--dry-run`: refuse before any other item parser (same position as the `/` and `//` claims), whole batch rolls back, forced flags change nothing. New teaching error in the T3/T4 family, e.g. `` `@bob^intention-rollovers` opens that task in Obsidian — it never captures ``, with miss variants naming the missing note/ID and the create-vs-search fork. Keep the `capture item 1 starting on line L: …` prefix.
- Grammar revision bump by one; `capture-parse -f json` reports the new grammar; shell `--help` for `capture-complete` gains one line under `task_goto` noting the `@route^id` whole-draft claim. No new `bob` subcommand (forbidden by `cli_rules.md`), no new long option.

### Mac capture behavior (thin client, mirrors `/`)

- While typing a claimed `@foo^bar` draft: skip the doomed live dry run (same skip the `:`/`/` pickers use), show the exact row with the `/`-card detail strip (`**Opens bob.md:82**` style), primary button reads `Open` (not `Capture`). Return/Tab/Command-Return/Control-Return all dispatch the same `obsidian://bob-goto-task` URI with `path` + `line` + `ref` + `block`; on success hide and discard the draft (same as Go To); on failure keep the picker open with `Couldn't open Obsidian`.
- Keys: Escape clears the filter then cancels to the reopen chip; Backspace on the `^id` part deletes back toward `@route` so route completion resumes (same as the Block ID Picker's empty-field rule); typing text anywhere else dissolves the goto claim into ordinary creation preview (add-words-means-create, live).
- The Block ID Picker must not auto-open on a claimed goto draft's `^` byte (it auto-opens only on an edit that writes `:`/`^` before an ID part in a creation/link position). A whole-draft goto has no ID-part cursor in that sense; treat it like `/` (picker context), not like `@route^` (composer context).

### Beauty details that decide whether this feels designed

- Preview copy is one line and names the landing: `[∗] Add support for "intention rollovers"! · bob.md:82` with sub-line `Opens in Obsidian — nothing is captured, stamped, or linked`. Miss copy offers both exits: `No ^nope in bob.md — add words to create it, or type /nope to search`.
- Keep the human `task_goto` row format (`[status] text · note_path:line` plus `· scheduled`/`· closed` when present) so `/` and `@^` rows are visually identical in history and screenshots.
- One teaching table in `docs/capture.md` and the syntax index covers all four alone-forms: `@r:x` links, `^r:x` links, `@r^x` opens, `text @r^x` creates. The screenshot's failure becomes the docs' example pair: `@bob^intention-rollovers` opens; `Roll the intention @bob^intention-rollovers` would create (or collide, with the duplicate-ID error — use a fresh ID in the example).

### Tests and gates

- Grammar: whole-draft claim vs `text @r^x`, `@r^x@`, `@r^x#s`, `@nb^x`, multi-line, `@@r` + `@r^x`, quoted routes, trailing-space, empty-ID `@r^`, duplicate-ID note, missing note, ID-less target line, closed target, scheduled/blocked target (still opens), forced `-r`/`-s` ignored, bulk draft with one goto item plus one task item (whole batch refused).
- Landing: `line`/`ref`/`block` triple round-trips through the URI re-find order; duplicate-ID fails closed; note edited between parse and open lands via `ref` or reports the clamped-line notice.
- No-write invariants: ledger diff empty, no stamps, no `capture-task-id` mint, daily note untouched, `BOB_DAY_FILE` missing changes nothing (same guarantee the authored-ID creation path already gives).
- Gates: `just check` (or `just docs-check` for the docs half) per repo rules; Mac-only goto activation stays a manual GUI check per the URI doc (`open 'obsidian://…'` on a Mac).

## What remains for the implementer (and what I would not do)

- Decide the exact `needs`/`context` naming with the Mac app owner: reuse `task_goto` if the exact card can share the fuzzy card's code, else add `task_goto_exact`. Either is additive; do not rename `task_goto`.
- Decide whether `-C` should widen exact lookup into `done/` archives. I recommend no: exact goto serves living work; archives already have `//` + `done/` navigation. If Bryan wants archive jumps, add it as a flagged follow-up, not in v1.
- Do not extend `@` to nested `projects/foo` or quoted multi-word routes as part of this change. If link capture grows those, goto inherits them; shipping them here doubles the resolver risk.
- Do not touch `^route:block-id` link behavior, `=` start suffixes, successor offers (`decisions:unblocked-tasks-are-offered`), or walk behavior (`decisions:review-attention-follows-the-walk`). This feature parks no walk and links nothing.

## Recommended solution in one paragraph

Claim a whole-draft single token `@<route>^<block-id>` (non-notebook route, no body, no seal, no extras) as a read-only exact task goto: `capture-parse` reports it incomplete needing `task_goto`, `capture-complete` returns the one resolved row with `replacement: ""`, `bob capture` refuses it with a T3/T4-style teaching error, and Bob Mac Capture opens it through the existing `obsidian://bob-goto-task` URI and discards the draft — reusing the `/` catalog fields, row format, and landing semantics, with miss errors that teach the create-vs-search fork (`add words to create it, or /query to search`). Ship it behind a one-step grammar bump with the four-alone-forms table in `docs/capture.md` + `docs/reference/capture-syntax.md`, the notebook carve-out, duplicate-ID fail-closed, and the no-write guarantees above.

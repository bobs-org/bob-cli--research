# Merge-into-new-task capture (`< @foo+f`): research and recommendation

Researcher: mus · 2026-11-05 · request: complement `> @foo+f` with a
`< @foo+f` syntax that merges existing tasks into a newly created task.

Verdict up front: **yes, build it, almost exactly as proposed, with three
adjustments** (left side defined as one ordinary new-task capture; `<`
strictly standalone with `>`-mirroring escapes and refusals; Explicit-gesture
merge semantics identical to `>`). The gap it fills is real, the sigil choice
is good, and — the best part — the bob-mac-capture preview works with **zero
Mac changes** if bob returns the existing `merges[]` shape with
`target.created: true`.

## 1. What exists today

### 1.1 `>` transfer lines (the thing `<` mirrors)

`docs/capture.md` ("Moving and merging tasks with `>`"): a transfer names one
or more complete `@route+id` sources, a standalone `>` arrow, and one
destination. Bare-note destination moves; task/drawer/section destination
merges through the shared merge engine (`src/native/task_merge/`,
`plan_task_merge`), with Explicit gesture semantics and the first configured
merge label (fallback `merged into`). Key properties I verified in
`src/native/capture_language/transfer.rs` and `src/native/capture/transfer.rs`:

- Recognized before target-run fan-out; never fans out, never runs Ensure Next.
- One source is enough; several land as separate groups in typed order (MG20).
- Carries nothing else: body text, children, `s:`/`$`/`#`/`%`/`&`/`*`/`~`/`!`
  all fail with `transfer_extra_text` (or a narrower code). `\>` escapes.
- Glued arrows (`@a+x>@c`) are a teaching error (`transfer_arrow_spacing`).
- Mid-line comparisons (`called Bob > 3 times`), line-initial blockquotes,
  and code stay unchanged. Shell quoting is mandatory (`shell_ate_transfer_arrow`).
- Atomic with the rest of the draft; staged snapshot; dry-run parity;
  write order target → dependents → repairs → daily → sources; offers flow
  through draft-level `pull_in`; grammar 13, `schema_version` 1.

A `>` destination **must already exist**. There is no create-the-target
spelling. That is the entire gap.

### 1.2 The merge engine already handles everything `<` needs

`docs/task-merge.md` is implementation-agnostic: sources cut under a
container, tombstone with `🪢 LINKS: merged into [[T]]`, dependents
re-pointed, live Pomodoro links pruned, T offered once at the earliest lost
slot (MG12), full refusal table (§5), idempotent re-runs (§6), reconcile
no-op (MG17). `<` needs no engine changes — only a new caller that creates T
first, then calls the same planner.

### 1.3 The `~~` umbrella already merges into a new task — but narrowly

`docs/task-relations.md` §21 (ML5/ML6): `Umbrella ~~old:a|"merged into"`
creates the umbrella task and folds the picked task into it. I confirmed the
machinery is landed, not contract-only (`src/native/capture/relations_merge.rs`
exists and enforces `relation_merges_new_task` for `~`-on-new-task). But as a
substitute for `<` it has four weaknesses:

1. **Config-dependent.** It only merges when the typed label is in
   `relations.merge_labels` (built-in default `[]`; enabled via chezmoi).
   `>` and `bob task merge` always merge. A core capture verb should not
   depend on host YAML.
2. **Single-source ceremony.** One `~~token` names one edge; multi-merge
   needs several `~~` tokens plus one label each, and same-target multi-edge
   grouping is built for close-effects conflict detection, not for this.
3. **Label-typing ceremony.** `|"merged into"` on every use, with label
   validation, quoting rules, and hide-suggestion interplay — all noise for
   "fold these into my new task."
4. **Conflict surface.** `~`/`~~` share the item with everything else, so
   the ML5 conflict table (`&`/`*`/`=`/`!` on the source, recurring sources)
   applies. A dedicated verb sidesteps it by construction.

So: keep `~~`-umbrella as the relational path; add `<` as the direct,
config-independent, multi-source path. They compose, they do not compete.

### 1.4 The Mac preview contract makes `<` nearly free

Per `decisions:mac-capture-is-a-thin-client`, the app renders what bob
returns. I read the Swift side
(`Sources/CaptureCore/CaptureTransferPresentation.swift`,
`Sources/BobMacCapture/CaptureTransferCardView.swift`): the transfer card
triggers on `kind == task_move/task_merge` + `moves[]`/`merges[]`, renders
Bob-authored `message`/`consequences[].text` verbatim (purple `⤵` card,
source rows with status transition + locator + "N notes move(s)"/"title
only", destination row, repair line, Pull-In offers, VoiceOver summary),
and **already renders a "new" destination badge plus ", new" speech from
`target.created == true`**. If `<` returns the byte-identical `merges[]`
record shape with the newborn as `target` and `created: true`, the preview,
notification, and accessibility summary all work with no Mac change. This is
the strongest implementation constraint in this report: **do not invent a new
payload shape; reuse `merges[]`.**

## 2. Critique of the proposal

**It is a good idea.** Consolidation ("these three scattered tasks are
really one bigger thing") is a natural capture-time thought, and today it
takes two steps (create, then `>` merge) with no atomicity, no single
preview, and no offer to link the umbrella where the sources lived. `<`
closes that loop in one gesture with the same all-or-nothing guarantee as
every other capture.

**The sigil is the right pick.** `destination < sources` is the exact mirror
of `sources > destination`; the arrow "points at" the absorber in both. It
is one keystroke, typeable everywhere `>` is, and inherits the existing
quoting culture. Alternatives I considered and reject:

- `>` with a creatable destination (`@a+x > New task @c^id`): breaks the
  transfer recognizer's cleanest invariant (a transfer line carries nothing
  else) and overloads the "existing things only" mental model.
- Multi-`~~` (`Umbrella ~~a:x ~~b:y`): keeps the config + ceremony problems
  from §1.3. Could still be added later as a complement, not a substitute.
- `<<`, `+<`, `=<`: no mirror intuition, harder to type, zero precedent.
- `bob task merge --into-new`: no capture preview, no atomicity with the
  draft, splits the flow across CLI and capture.

**Risks, all manageable:**

- `<` is also a shell redirect (stdin read). Same quoting requirement as `>`,
  same teaching-error treatment. No new class of problem.
- `<` vs `>` is a one-character visual difference in dense drafts.
  Mitigation is the preview itself (header names the verb and the newborn)
  plus distinct human output (`into new “…”`, see §4).
- `<` collides with comparison prose (`a<b`, `2 < 3`), arrows (`<-`, `->`),
  and generics-ish text. The standalone-token rule (§3) already solves this
  for `>`; mirror it exactly.

## 3. Recommended grammar (adjustments called out)

**Adjustment 1 — define the left side as exactly one ordinary new-task
capture.** The request says "only valid in a context that would create a new
task." Make that literal: everything left of `<` must parse as one ordinary
new-task item — body text plus `@route^newid` (Ready, name-only) or
`@route:newid` (Next + Pomodoro link), the two spellings `docs/capture.md`
already defines — with the newborn's usual optional `#type`, `s:<N>`, `$<N>`
terminals. Whatever `<body> @route^id …` would do standalone, it does here;
then the sources merge into it. This reuses the target-run machinery, needs
no new ID syntax, and answers "does `<` support scheduling/typing?" for
free. Concretely:

```text
Some great new task! @foo^great < @foo+f @bar+b
Consolidate the retry logic @dev^retry < @inbox+a @inbox+b @sase+c
Triage the outage @ops:sev2 < @ops+page #infra s:1
```

(Third example: Next-status newborn via `:sev2`, typed, scheduled — all
ordinary terminals, all honored before the merge lands.)

Refuse a left side that is not a new-task creation with a teaching error
naming `>`: existing-owner markers (`@route+id`, `!note:id`, bare
`@route:id` alias with no body), empty body, `x`/`=`/`!` whole-item forms,
`@@` declarations (never apply, as with `>`), forced `-r`/literal flags
(keep every `@` literal, as with `>`). Suggested code:
`merge_new_task_required` ("`<` folds tasks into the new task on its left;
to fold into an existing task, use `>`").

**Right side: one or more complete `@route+id` sources**, identical source
grammar to `>` (same `transfer_source_suffix`/`transfer_source_marker`
refusals for `#drawer`, `!`, `:`, `^` spellings; same
`duplicate_capture_target`, destination-is-source, and overlapping-source
refusals). A trailing bare `+`/`+query` opens the same task picker `>`
uses; accepting inserts `@route+id` tokens. Nothing else may sit on the
line — mirror `transfer_extra_text` / `transfer_children` (perhaps
`merge_new_extra_text` for a distinct hint, same shape).

**Adjustment 2 — `<` is standalone or it is prose.** Mirror `>` exactly:
whitespace both sides; glued (`@a+x<@c`, `text <@c`, `@a+x< @c`) is the
spacing teaching error; `\ <`… precisely, `\<` at the arrow position escapes
to a literal `<`; mid-line comparisons, `<=`/`>=`/`<-`/`->`, blockquotes,
`[[…]]`, backticks, and fenced code never claim. Shell ate it: `bob capture
a < b` unquoted reads file `b` as stdin — mirror the
`shell_ate_transfer_arrow` guard and copy.

**Adjustment 3 — Explicit gesture, `>`-identical merge semantics.**
The merge runs with `MergeGesture::Explicit` (not `Label`), writing the
first configured merge label and falling back to `merged into` — byte-same
provenance as `>`. Everything in `docs/task-merge.md` §§2–7 applies
unchanged: T-first write order (T is created first, then sources merge in
typed order per MG20), dependent re-pointing with cycle refusal, T-depends-on-S
left for cancel recovery, prerequisites reported not transferred,
successors orphaned with warning, Pomodoro-link prune, single offer of the
newborn at the earliest lost slot (this is the common case — a newborn has
no live link — so Pull-In "Link “great” in place of 2 merged tasks" falls
out naturally), idempotent re-runs, reconcile no-op. Newborn-specific
refusals to add: block-ID collision at the route (suggest `>` into the
existing task, or pick another ID); source that would be the newborn itself
(impossible by construction unless IDs collide — covered by the above).

## 4. Preview and output design (concise but useful)

Thin-client rule: **bob authors every sentence; the app arranges it.** No
Mac grammar work, no new card.

- **`capture-parse`**: report `mode: task_merge` with the existing
  `transfer` object (sources + arrow + destination describing the newborn)
  plus an additive `creation` object (`body`, `route`, `block_id`,
  `marker_range`, terminal summaries) and reused span kinds; top-level
  `grammar: 14`, `schema_version` still 1. Live spans highlight the newborn
  body as the destination and each `@route+id` as a source — the same three
  span families `>` uses, so Mac highlighting works day one.
- **`capture --dry-run` / commit JSON**: per-item `merges[]` with
  `target: {kind: task, created: true, title: <newborn title>, …}`,
  `task_blocks[]` carrying the newborn in final state, existing
  `merge_offers` / `pull_in` / `repaired_files[]` unchanged. `created: true`
  lights the existing "new" badge and VoiceOver ", new" with zero Mac edits.
- **Mac card** (no change needed): header "Merge 2 tasks", source rows with
  `⊘`-style transitions and locators, destination row "“great” · foo.md ›
  new", Bob's consequence lines (dependents, pruned links, warnings),
  repair line, Pull-In offer. Optionally — and only optionally — a later Mac
  pass could prefix the status line with "new", but `created → new` already
  reads clearly; do not gate bob-cli on it.
- **Human output** (canonical copy, add one row to the §10 table):
  `⤵ Merged 2 tasks into new “great” · foo.md › Tasks` /
  `Would merge …`; source/dependent/prune/repair rows byte-identical to `>`.
- **`capture-complete`**: source slots reuse the existing task-completion
  contexts; after `<`, bare `+` opens the vault-wide task picker exactly as
  `> +query` does for destinations. No new context kinds.

## 5. What to verify, and how

- Grammar: `<` claims only standalone lines; prose (`2 < 3`, `a<b`, `->`,
  `<-`, quotes, code) byte-identical; `\<` literal; glued → spacing error;
  existing-owner left → `merge_new_task_required`; empty body → existing
  missing-text error; child bullets → extra-text error.
- Semantics: all MG vectors re-run against `<` (especially MG5/MG7
  dependents, MG12 offer placement at earliest lost slot, MG16 re-run
  `unchanged` with zero writes, MG17 reconcile no-op, MG20 typed order);
  plus newborn vectors: collision refusal, `:id` Next+link newborn linked
  under the type-placed Pomodoro, `s:`/`$`/`#` terminals honored, then
  merge.
- Contract: `merges[]` shape byte-identical to `>` apart from
  `target.created: true` + newborn `title`/`line`; dry-run equals live
  except `dry_run`; Mac card renders from a fixture without app changes
  (paste the JSON into the existing transfer-preview test host).
- Docs gate: `docs/capture.md` + `docs/task-merge.md` §10 copy row +
  grammar-revision note; `just docs-check`.

## 6. Open questions for Bryan (all small, none blocking)

1. Allow a drawer/section newborn (`Task @foo^id#drawer < …`)? I say no for
   v1 — plain task anchor only, drawer merge already exists via `>`.
2. Allow child bullets as the newborn's notes? I say no for v1
   (`transfer_children` analogue) — keeps the line scannable; notes arrive
   via the merged sources.
3. Should `:id` (Next + Pomodoro link) be allowed on the left, or Ready-only
   `^id`? I allow both (§3 example 3) since the machinery is free — veto if
   you want newborns always Ready.
4. Multi-source cap? `>` has none; keep none.

## 7. Recommended solution

Ship `<` as the exact mirror of `>`: `new-task-capture < @route+id…`,
Explicit-gesture merge, `merges[]` with `target.created: true`, grammar 14,
schema 1, docs-first, Mac unchanged. Do not build a new payload, a new card,
or a config knob; do not touch the merge engine. File the three new teaching
codes (`merge_new_task_required`, spacing/escape mirrors) and the one copy
row, port the MG vectors, and gate on the existing Mac transfer-preview
fixture plus `just docs-check`.

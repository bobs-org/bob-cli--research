# Inline mentions as task backlinks: should `[[foo#^bar]]` in task prose auto-surface on the target?

*Research report — `mus` swarm member (independent; no peer reports consulted).
Question: add auto-"linked from" bullets to tasks referenced via inline Obsidian
block links (`[[foo#^bar]]`) by other tasks — asymmetric (no `LINKS` on the
referrer), visually self-explanatory, intuitive, reliable, beautiful.*

## TL;DR

Yes — but **do not implement it as a task relation**. Ship it as a separate,
generated backlink kind (`💬 MENTIONED IN:`), not as entries on the existing
`🪢 LINKED FROM:` line. The request's asymmetry (no `LINKS` on the referrer) is
correct and should be kept. Everything else about calling these "relations"
should be adjusted: mentions have no author, no label, no direction choice, and
must never feed the relation catalog, counts, or cancel/complete-label
machinery. A two-phase rollout (Phase 1: live chips/index only; Phase 2: stored
mirror line) gives Bryan the beauty and discoverability with almost none of the
write-churn risk. Details and exact contract deltas are in §6.

## 1. What exists today (evidence)

- A **task relation** is a directed, optionally labelled, inert edge authored
  once on the source's `🪢 **LINKS:**` child and mirrored on the target's
  generated `🪢 **LINKED FROM:**` child (`docs/task-relations.md` §§1–3;
  `src/native/task_relations/mod.rs`, `parse.rs`, `format.rs`, `plan.rs`).
  Glossary `task-relation` agrees: source authors, target mirrors.
- `LINKED FROM` is **pure projection** (§6): `mirror(T)` over accepted
  `LINKS` edges; reconcile (`src/native/task_status_hooks/relations.rs`,
  `reconcile_relation_lines`, runs right after `reconcile_blocks_lines`) owns
  it; nothing reads it back as input. Single-source guarantee LR11: delete all
  mirrors, one reconcile rebuilds byte-identical lines.
- **Chips render the live index, never the stored mirror** (§10, LC8,
  `api.relationIndex` v1 in bob-ledger-tools): status-coloured rows, muted
  label pills, inverse phrases on `LINKED FROM` (`merged from`, `followed up
  by`, …), dashed stale rows, `✓×N` collapse, hover previews.
- Explicit relations **never block/promote/consume/schedule/stamp** (§2,
  LR18/LX13/LG13); the only carve-outs are commit-time cancel/complete labels
  (§§17–18). Inertness is load-bearing for the review walk and plan budget.
- Identity is `(S, T)` per vault-relative path + block id (§5); at most one
  entry per target per source; `done/` and the previous daily note are
  read-only sources, never mirror owners (LR7/LR8); duplicate block ids and
  malformed sources make the source "uncertain" (kept, never newly added);
  kill switch `relations.linked_from_lines` is lossless (§12, LR16).
- The shared link scanner (`block_link_spans` in
  `src/native/task_dependencies/mod.rs`, replicated from
  `block_link_occurrences` in `task_status_hooks/pomodoro.rs`) already defines
  what a block link is: `[[…#^id]]` with valid id bytes, skipping inline-code
  spans, tracking `!` embeds and `~~` strikes, aliases allowed.
- Precedent against adopting prose: §14 "Adopting old idioms" — hand-written
  `Merged into [[…]]` / `See [[…]]` / `**RELATED:**` bullets are **not**
  adopted; adopting them is an explicit opt-in follow-up. The request re-opens
  exactly this door, but for real block links rather than prose idioms.
- Decisions in force: relations are authored edges
  (`decisions:task-deps-are-depends-on-links` family for the managed-line
  pattern); successor linking stays explicit
  (`decisions:unblocked-tasks-are-offered` — "every would-be successor link is
  offered for explicit selection"); theme/relation-label prefs hide from
  suggestions only, never from text.

## 2. What the request is really asking

"Any `[[…#^block-id]]` inside task A's subtree that resolves to task B ⇒ B
shows a generated bullet naming A; A shows nothing new (its inline link is
already visible)." That is **Obsidian backlinks scoped to tasks and stored in
the note**, not a relation: there is no gesture, no label, no direction chosen
by an author. Naming it a "linked from task relation" inherits machinery it
must not inherit (labels, catalog, counts, cancel/complete effects, `removeLink`
semantics).

## 3. Critique — is this a good idea?

**Worth doing, with the adjustments in §4.** The value is real: implicit
references ("this design supersedes the approach in [[sase#^retry-design]]",
"see the repro in [[bob#^flaky]]") are the most common cross-task pointer and
today they are invisible from the target side. Obsidian's backlinks pane shows
note-level backlinks, not task-level ones, and is unavailable in CLI /
plain-Markdown / review-walk contexts. A task-scoped "who mentions me" line
closes that loop and should reduce (not increase) manual `~` traffic.

The risks that force the design:

1. **Mention ≠ endorsement.** Prose links include counter-examples, retracted
   text, quoted context, work-log copies, and ledger-adjacent Task Links.
   Treating every mention as a relation-grade edge dilutes the one property
   that makes `LINKS` trustworthy: *someone meant this pointer.* Mixed into
   one `LINKED FROM` line, a reader can no longer tell intent from
   co-occurrence — the exact failure the "visually clear why shown"
   requirement calls out.
2. **No label exists.** `LINKED FROM` entries render `(label)` from the source
   side's phrasing (`follow-up of [[S]]` → `[[S]] (follow-up of)` / inverse
   table). A prose mention has no label to mirror and no inverse to compute.
   Forcing one (`(mentioned)`, `(see also)`) invents authorship.
3. **Safety: cancel/complete labels must never fire from prose.** §§17–18
   cancel/complete the *source* on explicit add/relabel into a configured
   label. Any implementation that routes mentions through the relation writer
   risks a prose mention becoming a lifecycle event. Isolation must be
   structural, not a flag check.
4. **Write amplification.** Explicit relations change rarely; prose edits
   constantly. A stored mirror over mentions rewrites target notes on every
   typo fix, rephrase, or task move. The current transaction model (same-note
   one transaction; cross-note commit-then-best-effort-follow-up with
   `· 🪢 LINKED FROM not updated`, §8) was built for rare, deliberate writes.
   Mentions need the same guards plus a higher bar for *whether to write at
   all*.
5. **Warning spam.** Explicit relations warn on unresolved / non-task / self
   targets (§12 `relation_warnings[]`). Prose typos (`[[#^fltpy]]`) are an
   order of magnitude more common than relation typos; warning per mention
   would drown the reconciler output that people actually read.
6. **Scan cost.** Today's `done/` scan byte-prefilters for `LINKS` and parses
   only hits (`load_relation_archives`). Mentions need a `[[` + `#^` prefilter
   over every candidate file — strictly more parsing per reconcile run.
7. **Fan-in blowup.** A widely-cited task (active `^prj`, a canonical repro)
   could collect dozens of mention bullets. Stored lines must stay complete
   (single-source rule); only chips may collapse (`✓×N`, LC9 pattern).

None of these is fatal. All of them say: **separate kind, separate line,
separate counters, scoped sources, silent omission, phased rollout.**

## 4. Adjustments to the requirements (explicit)

1. **Don't call them relations; don't store them on `LINKED FROM`.**
   New generated sibling line, e.g. `💬 MENTIONED IN:` (exact glyph is a
   polish choice; §6 argues for `💬` over reusing `🪢`). `LINKED FROM` keeps
   its LR11 single-source guarantee untouched; existing LK/LW/LR vectors stay
   valid.
2. **Keep the asymmetry** (no `LINKS` on the referrer) — agree with the
   request. Rationale to record: the inline link is already visible at the
   referrer; synthesising a `LINKS` entry would forge an authored edge, break
   single-source, and risk cancel/complete misfires.
3. **Scope what counts as a mention narrowly (v1):** validated `#^block-id`
   links resolving to a `#task`, appearing in the referrer's task-line body or
   descendant user bullets — **excluding** managed lines (`DEPENDS ON`,
   `BLOCKS`, `LINKS`, `LINKED FROM`, `Sub-projects`, `CANCEL LOG`), `🗓️
   SCHEDULE LOG` / `🛠️ WORK LOG` subtrees, Pomodoro-ledger Task Link bullets,
   fenced/blockquoted/marker-less lines (same fenced rules as relations, §3.5),
   inline code, struck (`~~[[…]]`) links, and non-task / self / unresolved /
   duplicate-id targets. Embeds (`![[…]]`): include as mentions (they are
   visible references; decision record says `#^ref` embeds no longer promote,
   so no double-counting concern). Aliases ignored for identity.
4. **Silent omission, no warnings, for mentions.** Unresolved / non-task /
   self / duplicate-id / id-less-referrer mentions are skipped without
   `relation_warnings[]` rows. (Explicit-relation warnings are unchanged.)
   Rationale: prose is draft-y; the reconciler must stay quiet enough to trust.
5. **Never mint a block id for a mention.** If the *referring* task has no
   `^id`, skip it (no entry) rather than minting into someone's draft prose
   context. Explicit relations mint (`LR4`) because a deliberate gesture
   justifies touching the source; typing prose does not. This is the sharpest
   deviation from reusing the relation pipeline, and it is intentional.
6. **Separate kill switch + separate counters.** `relations.mentioned_in_lines`
   (default: see phasing below), JSON `mentioned_in_line_updates[]` /
   `minted_mention…` (no mints in v1 — field omitted), distinct human-output
   `💬` group. `linked_from_lines: false` must not remove mention lines and
   vice versa.
7. **No context snippets in the stored line.** The stored entry is just the
   canonical link (`[[#^m]]`, `[[note#^m]]`, `[[done/…#^m]]` for archived
   referrers). "Why is this shown" is carried by the line label, the docs,
   the chip tooltip, and the live hover preview — not by copying prose across
   notes (which would churn, leak drafts, and fight merges).
8. **Read-only respect identical to relations:** `done/` + previous-daily
   referrers are listed; targets in `done/` / previous daily never get the
   line; rename/move/archive rebasing is generic and free; deleted referrer ⇒
   orphan removed next run.

## 5. Options considered

| Option | Shape | Verdict |
| --- | --- | --- |
| A. Mixed `LINKED FROM` with `(mentioned)` marker | One line, two entry kinds | Rejected: conflates intent, poisons label catalog/counts, breaks inverse table, risks §§17–18 confusion |
| B. New stored `MENTIONED IN:` line + live chips (**recommended**, §6) | Separate kind, own pass/vectors | Best clarity + plain-Markdown value; moderate cost |
| C. Live-only chips/index, no stored line | `api.mentionIndex`, no writes | Best cost/benefit as **Phase 1**; zero churn; recommend shipping first |
| D. Adoption gesture only (no auto-surface) | Convert mention → `~` explicitly | Useful as the *companion* gesture for B/C, insufficient alone (request wants ambient discovery) |
| E. Snippet-carrying backlinks | Entry + quoted context | Rejected: duplication, churn, merge conflicts; hover preview already covers "why" |

Do-nothing alternative (rely on Obsidian backlinks pane): rejected — not
task-scoped, not in the note, not available to CLI/chips/review walk.

## 6. Recommended solution

### 6.1 Phasing

- **Phase 1 — live only (small, reversible):** extend the ledger-tools index
  with a raw-text mention index (`api.mentionIndex` v1: forward/reverse maps,
  one generation, `done/` as read-only sources, editor-unsaved-text overlay —
  mirroring `api.relationIndex` §11), render mention chips, no stored writes,
  no reconcile pass. Validates scope/noise with real vault data before any
  note bytes change.
- **Phase 2 — stored mirror:** add the `💬 MENTIONED IN:` line + reconcile
  pass below. Phase 2 is where the "beautiful in plain Markdown" payoff lands.

### 6.2 Stored format (Phase 2)

```markdown
- [ ] #task Fix flaky capture retries ^fix-retries
  - 🪢 **LINKS:** follow-up of [[done/bob_done#^capture-star]]
  - 🪢 **LINKED FROM:** [[sase#^retry-design]] (follow-up of)
  - 💬 **MENTIONED IN:** [[#^triage-note]] • [[bob#^flaky-repro]]
  - user children, 🗓️ SCHEDULE LOG, 🛠️ WORK LOG …
```

- Slot: directly after `LINKED FROM` when present, else in the `LINKED FROM`
  slot (§4 rules reused verbatim: existing lines never move; child indent
  reused; CRLF/final-newline preserved).
- Ordering: canonical sort identical to `LINKED FROM` (ASCII-folded
  `cmp_blocks_links`, code-point tie-break; same-note first) — two machines,
  same bytes (LR5 analogue).
- Labels: none stored. Display form is the bare canonical link.
- Reader tolerance mirrors §3.4 (glyph/`MENTIONS`/`BACKLINKS`-style variants
  canonicalised); malformed handling mirrors §3.6 (leave untouched + warn
  once per owner — but mention-line malformation warns, mention *source*
  prose never does).

### 6.3 Visual design (the "why is this shown" requirement)

- **In Markdown:** the `💬 MENTIONED IN:` label reads as English without the
  plugin ("mentioned in these tasks' prose — not a relation"), visually
  distinct from the `🪢` relation family. Colour carries nothing new: neutral
  row accent, same as relations (§10: colour carries status, never direction).
- **Chips:** reuse `bob-dep-row`/`bob-dep-chip`; one entry per visual row;
  dimmed `✓` for closed, `↗ note` for cross-note, dashed `⚠` never needed
  (stale entries are removed, not dashed — mentions have no authored truth to
  conflict with); tooltip `Mentioned in prose · not a relation`;
  click/Mod-click navigates to the referrer; **no × control** (nothing to
  unlink — the fix is editing the prose; an × that silently edits another
  task's sentence would be the opposite of intuitive). Collapse `💬×N` past a
  threshold mirroring LC9.
- **Adoption (the beautiful gesture):** on a mention chip / Linked-from stage,
  offer `Link as relation` — opens the referrer's Links stage prefilled with
  the target (one explicit gesture converts ambient mention → authored edge).
  This pairs option D as the companion instead of the whole feature.

### 6.4 Reconcile + writers (Phase 2)

- New pass `reconcile_mention_lines` immediately after
  `reconcile_relation_lines`, same structure: owners = every T with mentions
  plus every writable task already carrying the line; byte-prefilter for
  `[[` + `#^` (then parse only hits); guarded structural edits joining the
  reconciled set (2 s quiet, preimage, snapshots — §7 rules verbatim);
  never edits prose, only the generated line; hand edits to the line get the
  once-per-burst `💬 MENTIONED IN is generated from prose mentions` notice and
  are restored next run.
- Capture/nav gestures write nothing eagerly for mentions (no courtesy
  writes); reconcile converges them. Hand-editing prose re-mirrors on cursor
  leave via the same burst-diff mechanism as LINKS hand edits (LG10
  analogue) or simply on next reconcile — reconcile-only is acceptable for
  v1 and is the reliable choice.
- `Ctrl+D` on the mention row: refused with the generated-line notice
  (LG9 analogue). `Ctrl+Shift+P` on the line: opens the *target's* mention
  list (read-only, with per-row jump-to-source + adopt actions).

### 6.5 Contract/tests/docs deltas

- `docs/task-relations.md`: new §19 (mentions) + MK/MW/MR/MC vector tables;
  LK/LW/LR/LC vectors untouched. Same Rust/JS twin-vector discipline
  (LW14/LK\* analogue: both engines agree or the doc changes first).
- Rust: `task_relations/mentions.rs` (scope scan over task subtrees reusing
  `block_link_spans`, fenced/managed-line exclusions) + reconcile pass +
  planner reuse (`plan_linked_from_line` shape with mention identity).
- JS twins: ledger-tools mention index + chip model; nav recognisers refuse
  the line as input (LG18–LG22 analogues).
- Decisions: record as a new decision note (immutable; cite this report) —
  it narrows `task-deps-are-depends-on-links` nowhere and touches
  `review-walk-is-tiered` nowhere (mentions are inert: no walk tier, no lane,
  no freshness, no plan-budget, no successor offers).

### 6.6 Acceptance sketch

1. A mentions B in body prose → next reconcile: B gains sorted
   `💬 MENTIONED IN: [[…#^a]]`; A unchanged; second run is a no-op.
2. Same but A id-less → no entry, no mint, no warning.
3. Mention inside `WORK LOG`, fenced code, `` `[[#^b]]` ``, `~~[[#^b]]~~`,
   `DEPENDS ON`, or Pomodoro bullet → no entry.
4. `[[#^typo]]` in prose → no entry, no warning.
5. Delete A's mention → orphan removed next run; delete every mention line →
   one run rebuilds byte-identical.
6. Cancel/complete-label config + prose mentioning the labelled task → no
   status change, ever.
7. Kill switch off → lines removed losslessly; prose untouched; Phase-1 chips
   hide the section.
8. Vault with 5k mentions: reconcile parses bounded by prefilter; no per-file
   full parse of mention-free notes (assert via prefilter counters in tests).

## 7. Open questions for Bryan (not blockers)

- Glyph/label spelling: `💬 MENTIONED IN:` vs `🪢 MENTIONED IN:` (family) vs
  `BACKLINKS:`. I recommend `💬` — the visual difference *is* the
  explanation — but this is one point of taste to confirm.
- Phase 1 default: ship live chips on by default (my recommendation) or
  behind the kill switch until Phase 2? Default-on matches "available
  immediately" precedent (`decisions:decay-decisions-are-available-immediately`).
- Whether `SCHEDULE/WORK LOG` mentions should count (I say no in v1; logs are
  history, and log copies would fan-in aggressively).
- Whether to cap stored entries per target (I say no cap stored / collapse in
  chips only, preserving single-source completeness).

## Sources consulted

- `docs/task-relations.md` §§1–19 + LK/LW/LR/LX/LP/LD/LG/LC/RV vector tables.
- `src/native/task_relations/{mod,parse,format,plan,label}.rs`;
  `src/native/task_status_hooks/relations.rs` (+ `blocks.rs`, `sync.rs`);
  `src/native/task_dependencies/mod.rs` (`block_link_spans`,
  `raw_wikilink_spans`, `parse_block_link_inside`); `pomodoro.rs`
  (`block_link_occurrences`).
- Memory: `glossary:task-relation`, `glossary:task-link`,
  `glossary:task-dependency-link`; `decisions:task-deps-are-depends-on-links`,
  `decisions:unblocked-tasks-are-offered`.
- No peer swarm reports were sought, opened, or read.

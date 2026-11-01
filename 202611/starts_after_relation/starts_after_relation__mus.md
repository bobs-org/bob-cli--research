# Starts-after relations with park/close successor offers — research (`__mus`)

Researcher: mus. Independent report for the 5-researcher swarm; no peer report
was located, opened, or consulted.

## 1. TL;DR

The request is a good idea, worth building, with two adjustments:

1. **Keep the stored label exactly `starts after`, add `starts before` as a
   display-only named inverse pair** (never stored). This matches the existing
   inverse machinery and the request's mirror requirement verbatim.
2. **Do NOT implement it as a third `relations.*_labels` config list.**
   Ship one canonical key (`starts after`, matched with the existing
   `relation_label_key`) as a first-class standing trigger. A configured list
   buys synonyms at the cost of the both-lists-misconfiguration class and a
   new YAML surface; temporal-sequencing vocabulary should stay exact.

The core design: the **waiter owns the edge** ("B starts after A" is stored on
B's `LINKS` line pointing at gate A). When gate A is **parked by an `x*`
close** or **closed by any managed Done gesture**, B is offered as a new
`starts_after` successor group with an explicit per-row reason
(`· starts after "A" (parked)` vs `· starts after "A" (completed)`). Relations
stay non-blocking; this is a standing offer trigger, not a dependency. Details
and rationale below.

## 2. What was asked

- New special relation label `starts after`, rendered as `starts before` in
  the mirrored `LINKED FROM` bullet.
- Purpose: sequence agent-dispatched work. Gate task A is dispatched via `x*`
  (park: marked In Progress, link moved out of the daily file); waiter task B
  ("starts after A") should then surface as a successor prompt so Bryan can
  think through and send the follow-up prompt.
- The prompt should also fire when A is closed (normal-successor behavior).
- The reason for the prompt must be unmistakable given multiple successor
  kinds now exist.
- Bryan asked the researcher to lead the design: intuitive, reliable,
  beautiful; critique the plan; adjust requirements with callouts; end with a
  recommended solution.

## 3. How it works today (verified against this checkout)

### 3.1 Relations are inert, with two commit-time exceptions

`docs/task-relations.md` §2: a relation write/line/gesture never blocks,
unblocks, promotes, schedules, stamps, routes, counts as a Pomodoro Task Link,
or enters the successor machinery. The only carve-outs are the commit-time
cancel of §17 (`relations.cancel_labels`: "S duplicate of T" cancels S) and
the commit-time complete of §18 (`relations.complete_labels`: "S implemented
by T" completes S). Both fire **once, at commit, on the source**, through
explicit gestures only (capture `~`/`~~`, nav Links/Linked-from stages);
reconcile, renames, hand edits, mirrors, and re-adds never fire them.

Implication: a "starts after" trigger is a **third, new kind of effect** —
a *standing* trigger (a past link causing a future offer when the *target*
changes), whereas cancel/complete labels are *commit-time* effects on the
source. The contract's inertness section (§2, §13 guarantee 2) will need an
explicit third carve-out. This is the single largest design decision; §5
justifies why a relation (not a dependency) is still the right vehicle.

### 3.2 Inverse phrases are display-only

`docs/task-relations.md` §10 + `src/native/task_relations/inverse.rs`: the
mirror shows a named inverse (`merged into` → `merged from`, `follow-up of`
→ `followed up by`, `split from` → `split into`, `duplicate of` →
`duplicated by`) or derives one from the `‹participle› by` rule
(`blocked by` → `blocks`); otherwise it falls back to
`(chip) · ‹label› → this`. Inverses are matched case-insensitively, always
lowercase, never stored. `bob relations list` shows the inverse in the `⇄`
column; capture-complete suggestions carry it.

`starts after` fits **neither** existing path: it is not `‹participle› by`
(it is `‹verb›s ‹preposition›`), so without a code change the mirror would
render the fallback `(B) · starts after → this` on A's line — readable but
not what was asked. Adding one row to `NAMED_PAIRS`,
`("starts after", "starts before")`, yields exactly the requested rendering.
Reading convention (verified from LC5 and the §10 anatomy): the LINKED FROM
row reads target-centrically, `‹inverse› (chip)` — i.e. A's line shows
`starts before (B)`, meaning "A starts before B". That is the correct
direction and should be stated in the contract so nobody reads it as
"B starts before A".

### 3.3 Successor offers: trigger, rule, copy

`docs/task-dependencies.md` §12 (esp. §§12.1–12.6):

- **Trigger (§12.1):** managed Done gestures only (Ctrl+Enter variants,
  `!note:id`, closes completing links `x!M`/`x!`/embeds, complete-label
  commits, Alt+]/[ into Done, sealed-project creation). **Explicit
  non-triggers include `x*` parks**, cancel, reopen, raw checkbox, hooks
  runs, Ctrl+Enter on Depends-On lines. SL21 pins this.
- **Rule (§12.2):** the gesture's completed set C; dependents fully unblocked
  are offered (group `hand_off`), plus project/pull-in/keep-moving rows.
  Offers are numbered, keyed (opaque stable keys), never auto-linked; picks
  link + raise to Next + stamp fresh (except tasks the same capture creates).
  Multi-item netting (SL20), `already_planned`, `no_destination`,
  `not_selected` semantics all exist.
- **Copy (§12.6):** group headers (`Hand-offs`, `Project ‹note›`,
  `Project finished`, `Keep ‹N› moving`); glyph discipline (🔓 unblocked,
  🔒 still blocked, ✓ done; "use only existing glyphs"); at most 3 rows then
  `+N more`; keep-moving rows always lead with **why** and say **not
  dependents** with glyph ⏭. CLI prints `offer N … → DEST` under headers with
  reason suffixes; JSON rows carry `trigger`, `offer.group`,
  `offer.destination`, `unblocked_by`.
- Planner home: `src/native/task_complete/successors.rs`
  (`plan_successors`, `OfferGroup::{HandOff, Project, ProjectFinished,
  KeepMoving}`); reporting model is additive under schema v1.

So the machinery the request wants to reuse (numbered offers, `-p` picks,
destination anchors, notice text) exists, but the trigger set and the group
vocabulary both need additive extension.

### 3.4 What `x*` park actually does (the request's "unique operation" claim checks out)

`docs/capture.md` (close selection + outcomes table, §§ on parking):

- `x[<N>][*<P>][!<M>][~<K>]`: `*<P>` **parks** those Task Links — "normal
  work without carrying forward". Parked rows keep normal 🍅 history, get the
  normal In Progress + Work Log effects (`[/]`), read `Parked · not carried`,
  and are **not carried** into the next placeholder. Contrast: dropped (`~K`)
  = removed, no work history, lane unchanged; deferred (`#`) = removed but
  carried; in-progress (`<N>`) = carried and started.
- Parking is a close **outcome**, not a task status; the "pending" waiting
  place is the existing sticky-lane PENDING behavior (per the outcomes table
  note). The task itself stays in its home note; what "moves out of the daily
  file" is its Task Link (absent from the next placeholder).

The claim "unique to the `x*` capture syntax" is therefore **correct** for
first-party gestures: no other single gesture records *worked + In Progress +
deliberately not carried*. (Manual link deletion or `x~` drops approximate
the removal but record no work and no In Progress effect.) One caveat for the
contract: park outcomes exist only in `bob capture` pomodoro closes today —
there is no Obsidian one-click "park" twin — so the park trigger path is
capture-owned, while the close trigger path is shared (capture + cycler/nav).

### 3.5 Memory context

Batched read (`glossary:successor-offer`, `glossary:task-successor`,
`glossary:task-relation`, `decisions:unblocked-tasks-are-offered`): offers are
never linked until picked; a pick links + raises to Next; relations never
block/count as Task Links; the standing decision record blesses offered-not-
auto-linked successors. The proposed feature composes with all three without
contradiction, provided the new group keeps the offer-not-auto-link rule.

## 4. Critique: is this a good idea?

**Yes — with the scope kept tight.** The underlying need is real and
currently unserved: Bob has *blocking* waits (dependencies: B can't start
until A closes) but no *sequencing* waits (B shouldn't be *surfaced* until A
is dispatched, yet B is perfectly startable and must not sit in the Blocked
lane). Agent-prompt chaining is exactly a sequencing wait: prompt B is
writable now, but thinking it through is wasted until prompt A's context is
fixed by dispatching A. A dependency would actively misrepresent this (B would
show `[?]`, consume the Blocked lane, and — worst — never unblock on park
since A stays open). A relation with a standing offer trigger models the
truth: no status effect, one well-timed nudge.

Risks, honestly stated:

1. **Inertness erosion.** Every standing trigger makes LINKS lines
   load-bearing for planning. Today's guarantee ("relabel any relation, only
   mirrors differ") is a debuggability asset. Mitigation: exactly one
   canonical trigger key, trigger fires only in the two named gestures, and
   reconcile/rename/hand-edit never offer (rename only arms/disarms future
   offers). Document the third carve-out next to the other two.
2. **Double-prompt fatigue.** A gate that is parked and later closed fires
   twice for the same waiter. This is arguably correct (dispatch nudge, then
   completion nudge) but must be a deliberate, documented choice with per-event
   copy, not an accident. If Bryan finds it noisy, the documented follow-up is
   a "once per waiter per gate" dedupe — do not build that now.
3. **Direction learnability.** "Starts after" vs "starts before", source vs
   mirror, is the classic temporal-dependency confusion (MS Project users set
   these backwards regularly). Mitigation: picker prose always names both ends
   plus the event ("Draft B, which starts after 'Send agent A' — A was just
   parked"), and chips keep the arrow-side pill convention (§10).
4. **Scope creep into scheduling.** "Starts after" must not become a date
   constraint, a priority input, or freshness input. The contract should say
   so in one sentence, mirroring §2's list.

## 5. Alternatives considered (and why the relation still wins)

| Alternative | Verdict |
|---|---|
| Depends-On edge + manual release (Alt+N) | Rejected. Misstates startability; pollutes Blocked lane; park never unblocks, so the prompt would never fire when it matters most. |
| Keep-moving / leaf-project grouping | Rejected. Keep-moving fires when a leaf project's last link closes — wrong trigger (close-only, project-scoped) and drags project semantics into a two-task sequence. |
| Tickler / schedule (`s:N`, `[unblocked::]` resurfacing) | Viable fallback for date-driven cases, but the trigger here is an *event* (dispatch), not a date. Rejected as primary. |
| Manual agenda query ("what starts after parked tasks?") | Cheap but promptless — Bryan explicitly wants the prompt. Could ship as a complement (`bob relations` query flag), not the feature. |
| New dependency kind ("waits for" with park-unblock) | Tempting (reuses unblock machinery), but invents blocking-that-isn't-blocking and collides with `task-deps-are-depends-on-links` (one Depends-On line is source of truth). Rejected. |
| Generalize to configurable trigger-label list | Rejected for v1 (see §1, item 2). Synonyms can be revisited after real usage shows which phrasings Bryan actually types; the catalog (`bob relations list`) will reveal them. |

## 6. Recommended solution

### 6.1 Edge ownership and vocabulary (no change to the request)

- Stored label: **`starts after`**, authored on the **waiter's** LINKS line:
  `B 🪢 LINKS: starts after [[A]]` reads "B starts after A".
- Mirror: A's LINKED FROM shows the display-only inverse **`starts before
  (B)`**, reading "A starts before B". Implement as a fifth `NAMED_PAIRS`
  entry; it flows automatically into chips, `relations list ⇄`, and
  capture-complete suggestions.
- Key matching uses the existing `relation_label_key` (case, spacing,
  trailing-colon insensitive). `Starts  After:` triggers; `starts-after`,
  `after`, `startsbefore` do not (documented, with a teaching hint on close
  misses — cf. inverse hints CL6/CP6).
- **Adjustment called out:** hide/`||` one-offs and renames behave like
  §16 RV4/RV8 with a standing-trigger addendum — hiding never disarms the
  trigger (suggestions-only, per `relation-label-hide-is-suggestions-only`);
  rename into the key arms future offers but the rename itself never offers;
  rename out of the key disarms. Relabel *away* never retracts an already-made
  offer.

### 6.2 Trigger set (adjustment: enumerated closed list)

Fire **only** on:

1. **Park:** gate A's Task Link outcome is `parked` in a committed
   `bob capture` pomodoro close (`x*` forms, listed or wildcard). Event name
   `parked`.
2. **Close:** gate A completes through **any** managed Done gesture that can
   already produce successor offers (§12.1 list: `!`, `x!` closes, Ctrl+Enter
   family, complete-label commits — including a complete-label commit whose
   source is A). Event name `completed`.

Never on: cancel, reopen, raw checkbox, reconcile/hooks, relabel/relink,
rename, drop (`x~`), defer, in-progress carry, plain `x` keeps, or Waiter-side
events. A waiter that is closed/cancelled/archived, or whose edge is
malformed/unresolved/duplicate-id/self, is skipped silently (warned in JSON
warnings, never fatal) — mirroring LR13/LR14/LR23 handling.

Double-fire policy (documented choice): park and later close of the same gate
offer the same waiter **twice, once per event**, with event-distinct copy.
Within one gesture, one waiter is offered **once** even if several of its
gates fired (list all gates in `unblocked_by`); SL20-style netting applies
(a later item that closes/links the waiter drops its offer).

### 6.3 What the offer does (reuse §12 wholesale)

- New `OfferGroup::StartsAfter` (`"starts_after"`) + row `trigger:
  "starts_after"` + `event: "parked" | "completed"`. Sorted **after**
  `hand_off`, before `project` (rationale: it answers "what do I do next"
  like a hand-off, but must never be mistaken for an unblocking — hence its
  own header, never folded into Hand-offs).
- Destination/anchor/placement: identical to hand-off offers (§12.3–12.4);
  picks link + raise to Next + stamp fresh under the same rules (created-task
  waiters never stamped). Unpicked: `not_linked: "not_selected"`, status
  untouched. `already_planned` / `no_destination` / `disabled` unchanged.
- Kill switch: **adjustment** — gate the new group on the existing
  `plan.link_unblocked` switch (false ⇒ rows report `disabled`, no offers),
  and document a future `plan.starts_after_offers` split as the named
  follow-up if Bryan ever wants hand-offs without sequencing nudges. One
  switch now, not two.
- `unblocked_by` names the gate(s) with gate text + event; waiters already
  linked today fold to `already_planned`.

### 6.4 Copy: making the "why" unmistakable (the beauty requirement)

Group header: **`Starts after`** (picker, CLI, Mac card). Per-row reason
suffix (CLI/human + picker caption + notice fallback):

- `· starts after "‹gate text›" (parked)` — gate dispatched, still open.
- `· starts after "‹gate text›" (completed)` — gate closed.

Full CLI row sketch (follows §12.6 word-led rows, 48-char truncation,
`→ DEST`):

```text
Starts after
offer 3  [ ] Draft the follow-up prompt  work.md ^follow-up → FIX · starts after "Send agent context" (parked)
```

Notice text: `⏭ Starts after in FIX: Draft the follow-up prompt
· "Send agent context" was parked`. (Glyph note: §12.6 says "only existing
glyphs" — ⏭ is existing *within the successor family* via keep-moving, and
reusing it marks "sequencing, not unblocking". If the implementer prefers
zero new-glyph-risk, 🔓 with the `Starts after` header is acceptable; do not
invent a new emoji.)

Chips: waiter side keeps the arrow-side pill `starts after → (A)`;
gate side shows `starts before (B)` — no new palette, neutral accent, status
colors unchanged (per §10). Picker rows for the label carry a one-line
consequence caption from day one (the CL6/CP6 lesson): e.g.
`⏭ offers B when A is parked or closed · never blocks`.

Mac stays thin-client: bob computes `starts_after` rows in preview JSON; the
app adds the section + multi-select under the existing choice step, no new
decision logic (`mac-capture-is-a-thin-client`).

### 6.5 Reliability notes for the implementer

- **Lookup path:** at pomodoro-close plan time (park events) and inside the
  managed-Done successor pass (close events), resolve the reverse index
  waiter-of-gate from LINKS edges (vault scan prefiltered on `**LINKS`,
  same-note/basename/path/`done/`-explicit resolution, dedupe by
  (path, block-id)). Reuse the §12.7 layering (gate on cheap checks first;
  share one batch snapshot) and keep the ≤70 ms close budget; record
  measurements on the apollo-copy fixture per §12.7.
- **Idempotency/atomicity:** offers join the gesture's single offer set and
  single staged batch (capture) / cycler pass (nav); dry-run parity holds;
  `capture-parse`/`capture-complete` gain only additive flags.
- **Parity:** Rust + JS twins pinned by shared vectors (extend
  `tests/fixtures/relation_labels/vectors.json` with key/inverse rows and add
  an SO-table block for park/close offers); bob-plugins copies byte-for-byte.
- **Docs first:** per repo convention, edit `docs/task-relations.md` (new §20
  + §2/§10/§16 deltas) and `docs/task-dependencies.md` (§12.1 trigger row,
  §12.2 group/order, §12.5–12.6 reporting/copy) in the same change; then code.
- **Non-goals for v1:** per-gate grouping beyond `unblocked_by` listing,
  once-per-waiter dedupe, a query command, date/priority/freshness effects,
  Obsidian park button. Each is a named follow-up, not a silent omission.

## 7. Open questions for Bryan (none blocking)

1. Confirm the double-fire choice (park nudge + later close nudge) vs
   once-per-waiter-per-gate.
2. Confirm single-switch (`plan.link_unblocked`) vs a dedicated
   `plan.starts_after_offers` from day one.
3. Confirm glyph: ⏭ (sequencing family) vs 🔓 (unblocked family) for the new
   rows.

## 8. Sources checked

- `docs/task-relations.md` §§1–19 (vocabulary, inertness, grammar, slots,
  identity/minting, mirror projection, writers, gestures, chips + inverses,
  live index, cancel §17 / complete §18 rules, verdicts, indication, contracts,
  architecture).
- `docs/task-dependencies.md` §§11.6 (SL vectors incl. SL21), 12.1–12.8
  (trigger, rule, anchors, writes, reporting, copy, performance, kill switch).
- `docs/capture.md` close-selection grammar, numbering, outcomes table, and
  parking semantics; `docs/reference/capture-syntax.md` token index.
- `src/native/task_complete/successors.rs` (planner shape, `OfferGroup`,
  selection/keys/destinations); `src/native/task_relations/inverse.rs`
  (`NAMED_PAIRS`, `inverse_phrase`).
- Memory: `glossary:successor-offer`, `glossary:task-successor`,
  `glossary:task-relation`, `decisions:unblocked-tasks-are-offered` (batched
  `sase memory read`).

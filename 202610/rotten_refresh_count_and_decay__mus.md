# Tracking explicit task refreshes (`refresh_count`) and future user-approved rotten decay

Researcher: mus (`__mus`). Independent report in a 5-researcher swarm; conclusions are my own.

## TL;DR / recommended solution

Yes, track explicit refreshes — but with four adjustments to the request as stated:

1. **Count only explicit due-confirmations, not every stamp.** `stamp_fresh` runs on many gestures (lane moves, capture links, deferrals, priority picks). Incrementing on all of them would measure "touches," not "keeps." Increment only on the explicit keep gestures: `Alt+F` (and the `Alt+Shift+F` / `]s` keep row) when the task **was due at press time**.
2. **Add reset semantics.** A bare ever-increasing counter cannot distinguish five blind keeps from "fixed the wording, then re-confirmed." Reset (remove the field) on deliberate-change gestures: priority change, scheduled change, Depends-On edit, lane change, close/reopen. Hand edits are best-effort (see §5).
3. **Fold the display into the existing freshness mark; stay quiet by default.** No new Dataview pill. Show a small `×N` affix inside the mark only when `N ≥ 2`, muted until the task is a decay candidate. Full count + history lives in the tooltip.
4. **Ship counting + display first; ship decay second, and keep decay user-approved.** Phase 1 is instrumentation (learn the real distribution of keep-streaks for 2–4 weeks). Phase 2 adds a decay *suggestion* row in review, mirroring priority decay (`Ctrl+Enter` takes the recommendation; `↵` never decays). Nothing ever auto-decays silently.

Concretely: store `[refresh_count:: N]` (positive integer 1–9999, absence = 0) in canonical position immediately after `[refresh:: …]` and before the Tasks suffix; extend the one-helper-per-language placement rule to it; add `refresh_malformed`-style lints; surface the count in `bob freshness` JSON (schema bump) and in the ledger-tools mark; add a `freshness.refresh_decay_after` config (default off until Phase 2). Details in §6.

## 1. Question

Bryan wants every explicit refresh of an Obsidian task — the `<Alt+F>` keymap writing `fresh` — tracked in a new `refresh_count` property, rendered as an icon like `fresh`, as a stepping stone toward user-approved-at-decay-time auto-decay for repeatedly re-confirmed rotten tasks (analogous to the existing auto-decay for repeat priority rolls, which does not exist for repeat rotten refreshes). I was asked to research the best implementation, critique the plan, adjust requirements where justified, and recommend a solution.

## 2. How explicit refresh works today (evidence)

All of this is the contract in `docs/freshness.md` (≈800 lines) with the Rust half in `src/native/freshness/`:

- **Storage.** `[fresh:: YYYY-MM-DD]` on the task line, before the trailing Tasks suffix. Optional `[refresh:: N]` (per-task interval, 1–365) immediately after it. Absence of `fresh` means NEW. Both are inline Dataview fields, not Tasks keys.
- **The `<Alt+F>` gesture.** `bob-navigation-hotkeys` calls `api?.freshness?.stampLine?.(line, dateText) ?? line` (JS mirror of Rust `stamp_fresh` in `src/native/freshness/placement.rs`). "Clicking a freshness mark only reveals the raw field for editing and never stamps. … when ledger-tools is absent or old the gesture simply doesn't stamp" (`docs/freshness.md` §5). So stamping is best-effort and version-dependent — any counter incremented in the same call site inherits that property.
- **Who else stamps.** The stamp rule (`docs/freshness.md` §5) fires on *every* supported human gesture that rewrites an open task line: `Alt+N` commit/release, `Ctrl+Shift+P` priority/scheduled/Depends-On rows, `Ctrl+Shift+M` moves, `Ctrl+Enter` recommended roll/decay, cycler `Alt+[`/`Alt+]`, block-id `Ctrl+Shift+Enter`/`^^`, capture `plan_task_link` + `=x` closes. Automation never stamps. This is the central reason "increment on every stamp" is wrong: most stamps are side effects of doing something else.
- **Placement.** `stamp_fresh`/`setRefreshLine` remove all `fresh`/`refresh` fields and rebuild as `head + [fresh:: D] (+ [refresh:: N]) + suffix`, where the Tasks suffix is scanned from end-of-line over Tasks keys, tags, and `^id` — and `fresh`/`refresh` at the run's left edge are *not* part of it (§3). A new field must join that recognized set or it corrupts suffix detection (see §6).
- **Evaluation is read-time, never stored** (`src/native/freshness/state.rs`, §4): `NEW / RESURFACED / ROTTEN / FRESH`, lane-aware intervals (`pending_interval` / `next_interval` default 1, else task → note → config → 7), tiered queue NEW → PENDING → NEXT → RETURNED → ROTTEN. Buckets: NEW → `new`, RESURFACED/ROTTEN → `rotten`.
- **Display.** The freshness mark is display-only, ledger-tools only: `✓ today` / draining lease ring with `Nd` / orange `⟳ Nd` capsule when due, 0.8em, tabular numerals, `/{N}d` interval suffix only for per-task intervals, rich multi-line tooltips, exact-or-neutral resolution (§11, M-vectors). The vault without the plugin falls back to raw pills. Any `refresh_count` rendering must live in the same component or it forks the design language.

## 3. How priority-roll decay works (the model to copy)

`docs/projects.md` ("Recommended roll and priority decay") is the existing precedent, and its vocabulary matters: "auto-decay" there is really **user-approved recommended decay**:

- The streak is **derived from the Schedule Log, never stored**: only reasonless same-level recommended `🎲 <L> roll` entries build it; any deliberate decision (typed reason, `🤷 no reason given`, priority re-pick, hand edit of priority) resets it to 0. `bob randomize` entries are transparent.
- `Ctrl+Enter` on `scheduled` takes the recommendation (roll vs. decay-to-next-level vs. cancel past the last level); `↵` opens the date list and never decays. Decay never fires silently.
- Config: `decay: false` disables; `decay.rolls` / `levels[].rolls` set per-level limits; absent/`true`/`{}` = enabled with 1 roll per level.

The analogous rotten-refresh design is therefore: **streak of deliberation-free keeps → suggested decay → explicit accept**. The open design questions are what "streak" means for keeps and what "decay" does to a task with no priority ladder.

## 4. Critique: is this a good idea?

**Yes, with the adjustments in the TL;DR.** The underlying problem is real: the ROTTEN tier is upkeep with an optional daily budget, and tasks that survive review by reflex (`Alt+F` without re-reading) are exactly the zombies a decay mechanism should surface. Instrumenting keeps before designing decay is the right order — today there is no data at all on keep frequency.

Risks and objections, honestly weighed:

1. **Goodhart / shame metric.** A visible count can turn review into "keeping the number low" rather than "is this still true." Mitigation: quiet-by-default display (§6), never a chip/bucket, never gating READY.
2. **Stored mutable state vs. the codebase's derived-state architecture.** Priority streaks, Today, and freshness state are all derived at read time; a stored counter is the first write-every-review mutation and can desquamate: hand-edited `fresh` dates, old plugin versions that stamp without bumping, mobile fallback (`invalid` config path), sync conflicts, and `bob freshness seed` all bypass or predate the increment. It will be a *heuristic*, not an audit trail. Accept that explicitly; do not build gating logic that assumes exactness.
3. **Semantic ambiguity of "refresh."** Today "refresh" means both the verb (confirm) and the `[refresh:: N]` interval noun. A third meaning (the count) needs a crisp name in docs and tooltips. `refresh_count` is fine; never abbreviate to `refreshes` in one surface and `refresh_count` in another.
4. **Line clutter.** Vault lines already carry `[fresh::] [refresh::] [created::] [priority::] [scheduled::] ^id`. One more field on every task is a real readability tax in source mode. Mitigation: absence = 0 (no migration rewrite), and the mark folds it (no new pill).
5. **Dual-implementation parity.** Every placement/evaluation change ships twice (Rust + ledger-tools JS) pinned by shared conformance vectors, plus JSON schema bumps. Budget for that; a counter that only one side understands *will* produce phantom diffs in the other's tests.
6. **What decay even means for a Ready task.** A priority has a ladder (P1→P4→cancel). A keep-streak has no natural next state. Candidate decays: see-less-often (lengthen interval), lower priority, park to Someday, or propose cancel. Each needs user approval and each needs the streak-reset semantics to be trustworthy first. Do not pick the decay action before Phase-1 data.

**Would I take a different approach?** The credible alternative is an append-only **Refresh Log** (child bullet, `✓`-marked dated entries like the Schedule Log) with the streak *derived*, preserving the derived-state architecture and giving an audit trail. I reject it for v1: it adds per-task bullet clutter for every keep (far heavier than one field), needs marker management under concurrent edits, and still cannot detect hand edits. Revisit only if Phase-1 data shows the counter's heuristic error actually mis-fires decay suggestions. A second alternative — inferring keeps from git/file history — is fragile on mobile and entangles review with sync; reject.

## 5. Key design decisions

**D1 — What increments.** Only explicit keep gestures on a *due* task: `Alt+F`, and the keep rows in single/counted/Task-Link review (`Alt+Shift+F`, `]s` keep). Everything else that stamps *preserves* the count. Rationale: matches the user's mental model ("I said still-true") and keeps lane daily reviews (interval 1) from inflating the metric — a `[*]` kept daily would otherwise hit any threshold in under a week.

**D2 — What resets.** Remove the field on: priority change, scheduled change (any path incl. rolls/decays/typed dates), Depends-On line edit, lane change (commit, release, today-route), close/reopen. These are all observable at write sites that already stamp, so the reset can ride the same call. Hand wording edits are *not* observable (hand editing is unmonitored by design) — documented limitation; the "edit, then Alt+F" flow will increment, slightly overstating that task. Acceptable because decay is suggestive only.

**D3 — Stored counter, heuristic contract.** `[refresh_count:: N]`, `1 ≤ N ≤ 9999`, absence = 0/never-kept-due. First due-confirm writes 1; subsequent ones increment. Cap at 9999 (parse but clamp; lint above). Never decrement except by reset-removal. Document: monotonic-ish, best-effort, never load-bearing for visibility.

**D4 — Placement.** Extend the recognized non-suffix field set (`fresh`, `refresh`) with `refresh_count` in: suffix-scan continuation, `rebuild_without_fields` (canonical order `[fresh:: D] [refresh:: N]? [refresh_count:: N]?` + suffix), `remove_fields`, misplaced/duplicate detection, and no-churn comparison. Canonical order puts the count last so `P11`-style vectors (`refresh follows fresh`) extend naturally. Parenthesis form `(refresh_count:: N)` parses but normalizes to brackets, consistent with existing fields.

**D5 — Lints.** `refresh_count_malformed` (non-integer/out-of-range), `refresh_count_duplicate` (uses max, consistent with `fresh_duplicate` using latest), `refresh_count_misplaced` (fold into existing `fresh_misplaced` repair: next explicit stamp re-canonicalizes). Counts never invalidate config; invalid values are ignored + linted, falling through to 0.

**D6 — Display (beautiful).** Fold into the existing mark, no new pill:
   - `N ≤ 1` or absent: mark unchanged (byte-identical to today). Zero clutter for healthy tasks.
   - `N ≥ 2`: append `×N` affix inside the mark at 0.85× size, tabular numerals, muted color in `today`/`aging` tones; in `due` tone it inherits the orange capsule only when `N ≥ refresh_decay_after` (decay candidate), otherwise muted. Never its own capsule.
   - Tooltip gains one line when `N ≥ 1`: `Kept {N}× since last change` (N=1: `Kept once since last change`), placed after line 1. Decay candidates append ` · Decay available` to the `Alt+F to confirm` line rather than adding a fourth line.
   - Non-canonical count fields keep the existing dashed-orange repair pill behavior. Source mode / plugin-absent fallback shows the raw field, as today.
   - Accessibility: count is text (`×3`), never color-only; ring/capsule semantics unchanged.

**D7 — Evaluation/JSON.** `bob freshness list --format json`: add `refresh_count` (number, 0 when absent) per queue row; add `counts.kept_repeated` (rows with N≥2) for Phase-1 measurement. Schema `3 → 4` for list (seed envelope untouched). Human output: no new column; decay candidates get the existing `⟳` row with no extra noise until Phase 2 adds the decay row text.

**D8 — Config.** `freshness.refresh_decay_after: N | false`, default `false` (counting on, decay off). Lane keeps count but lane rows never decay (their interval is the lane's). Invalid block handling identical to existing `freshness:` errors (exit 2 / `invalid` fallback).

**D9 — Migration.** No backfill: absence = 0, so zero vault rewrites. `bob freshness seed` never writes the field. First due-confirm creates it.

## 6. Recommended solution (phased)

**Phase 1 — Instrument (this build).**
Rust (`placement.rs`, `state.rs` row passthrough, `cli.rs` JSON, `config/freshness.rs`, conformance vectors P19–P24 / S16–S18 / M16–M18 in `docs/freshness.md`) + ledger-tools mirror (`stampLine` keep-path bump, `setRefreshLine` preserve, mark fold, tooltip line, resolution passthrough). Ship with `refresh_decay_after` default off. Success metric: distribution of keep-streaks in `kept_repeated` after 2–4 weeks of morning reviews.

**Phase 2 — User-approved decay (follow-up, needs its own design).**
When a due task has `N ≥ refresh_decay_after`, the review picker gains one decay row (mirroring the priority `Ctrl+Enter` contract): suggested action = lengthen the effective interval one step (7→14→30→90, writing `[refresh::]`, which also resets the streak's *cause* while clearing the count), with `↵` keeping as today (increment, no decay) and a second row offering cancel-with-`🍂` log for the terminal step. decay writes clear `refresh_count`. `decay: false`-style opt-out per note via existing `refresh`/`task_refresh` overrides already covers "see less often" manually, so the decay row is convenience + suggestion, never the only path. Never silent; never gating.

## 7. Conformance deltas to pin (both implementations, verbatim vectors)

- P19 bare count: `- [ ] #task Buy milk [fresh:: D] [refresh_count:: 2] …` round-trips; explicit keep → 3, other-gesture stamp → 2 preserved.
- P20 first keep creates `[refresh_count:: 1]`; explicit keep on a FRESH (not-due) task stamps without creating/incrementing.
- P21 priority/scheduled/lane change removes the field while stamping.
- P22 parenthesized/duplicate/misplaced/out-of-range handling per D4–D5.
- S16–S18: row `refresh_count` passthrough, `kept_repeated`, schema 4.
- M16–M18: `×N` affix visibility rules + tooltip lines.

## 8. Rejected alternatives

- **Increment on every stamp.** Measures touches, inflates via lane/capture/deferral stamps; rejected (§2).
- **Silent auto-decay / auto-lengthening.** Violates the user-owned-review principle (cf. `#now` user-owned decision) and acts on heuristic data; rejected in favor of suggested decay.
- **Separate `⟳`-style second icon.** Two competing glyphs on one task line at 0.8em is visual noise; folded affix wins.
- **Refresh Log (v1).** Heavier clutter, same hand-edit blind spot; parked as Phase-2-if-needed (§4).
- **Decay by lowering priority automatically.** Priority is a scheduling commitment with its own ladder and streak; cross-coupling two streaks confuses both. Lengthen-interval-first keeps one mechanism per concern.

## 9. Open questions for Bryan

1. Is "lengthen the interval" the right first decay action, or would you rather the decay row propose parking (Someday/`#hide`) or cancel?
2. Should lane (`[/]`/`[*]`) keeps count toward the same number, or a separate lane-keep tally? (I recommend same counter, no lane decay.)
3. Default `refresh_decay_after` once Phase 1 data lands — my prior is 3–5, but your actual keep distribution should set it.

## Sources

- `docs/freshness.md` §§1–5 (fields, placement, who-stamps), §4 (evaluation), §11 (mark), §§9–10/12 (conformance vectors); `src/native/freshness/placement.rs` (`stamp_fresh`, suffix scan, `read_freshness`); `src/native/freshness/state.rs` (read-time evaluation, tiers, intervals); `src/native/task_fields.rs` (inline-field scanner); `src/native/config/freshness.rs` (config block); `docs/projects.md` (priority decay ladder, Schedule Log streak semantics, reason prompt).

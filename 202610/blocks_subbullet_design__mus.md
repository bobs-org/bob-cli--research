# Reverse dependency visibility: should prerequisites get an automatic "BLOCKS" sub-bullet?

**Researcher:** mus · **Date:** 2026-10-13 · **Type:** design research (independent swarm contribution)

## 1. Request in one paragraph

Bryan asked for automatic reverse-dependency ink: whenever task D gains a prerequisite P (e.g. via the <kbd>Ctrl+Shift+P</kbd> → Depends-on stage), P should automatically grow a sub-bullet saying it blocks D. `bob task reconcile` should backfill and keep all such bullets consistent. The goals are intuitive, reliable, and beautiful. This report critiques the plan, compares approaches, adjusts requirements where justified, and ends with a recommended solution.

## 2. How the current system works (verified)

- **Forward edge storage (source of truth).** Each dependent owns one managed first-child `⛓️ **DEPENDS ON:**` line holding plain `[[…#^block-id]]` links (`docs/task-dependencies.md` §§1–3; `src/native/task_dependencies/{parse,format,mod}.rs`). The `[dependsOn::]` / `[id::]` Tasks fields are **derived** by reconcile (R1–R10), never hand-authoritative.
- **Key prior rejections.** "One bullet per dependency" was rejected for unbounded child bloat and log collisions; "links on the task line" was rejected for crowding; field-authoritative designs were rejected because the line must stay the edit surface (`sase memory read decisions:task-deps-are-depends-on-links`).
- **Semantics.** A task is `[?]` Blocked while any open prerequisite is open; linking a dependent promotes open prerequisites; Blocked tasks keep no live Pomodoro links (consumption); closing a dependent never closes prerequisites; closed prerequisites stay on the line as muted history (§5).
- **Writers.** The Task Card Depends-on stage commits dependent + field + status + freshness in **one editor transaction** (§6.6). `bob task reconcile` projects fields, heals/adopts/canonicalises lines, then derives edges and Blocked state (§4). Chips (`bob-ledger-tools`) render forward edges as coloured status chips plus a `waiting on N / ✓ all clear` summary that is never written to Markdown (§7).
- **Projects.** `^prj` prerequisites live on the same Depends-On line; blocked projects tag every open resident `#prj_is_blocked` and consume their Pomodoro links (§13; `decisions:projects-block-from-prj-line`, `decisions:subprojects-inherit-project-blocking`).

So the forward direction already has exactly one writer form, one authority, and a read-only render layer. **Any reverse feature must preserve that invariant.**

## 3. Is the ask a good idea? (critique)

**The need is real; the literal mechanism needs adjustment.** Discovering "what waits on P?" today requires opening every candidate dependent, running a Tasks/Dataview query, or waiting until P closes and the successor notice fires (§12). A reverse view helps triage ("can I close P safely?"), morning review, and project unblocking. But a second **stored, authoritative** sub-bullet is the wrong implementation of that need:

**Intuitive — risks:**

1. **Two edit surfaces for one fact.** If both D's `DEPENDS ON` and P's `BLOCKS` look editable, users will edit the wrong side. Every dual-write system eventually diverges; the current design deliberately has one edit surface (§6.8 refuses `!`, `Ctrl+Shift+Enter` on the line and points at <kbd>Ctrl+Shift+P</kbd>).
2. **Stale verbs.** "BLOCKS" is true only while D is open. When D closes, P no longer blocks it — but D stays on the forward line as history. A stored `BLOCKS` line either goes stale or needs its own history-vs-live distinction, doubling the mental model.
3. **Fan-in surprise.** Forward fan-out is bounded by how many prerequisites one task takes (usually 1–5). Reverse fan-in is unbounded: one foundational task can be waited on by 20+ dependents. Users adding "one small dependency" would watch an innocent prerequisite sprout a 20-link bullet they never touched.
4. **Project inheritance confusion.** Residents inherit `^prj` reasons; promotion walks *through* `^prj` to its deps (§5). Should P's bullet list the resident, the `^prj`, or both? Any answer surprises someone.

**Reliable — risks:**

5. **Dual-write divergence under real writers.** Rust reconcile, nav Task Card, capture `&note:id`, `Ctrl+D` row delete, hand edits, `Ctrl+Shift+M` moves, archive-to-`done/`, Obsidian sync races, and the 2-second quiet-interval deferral all already coordinate around *one* line. A second line doubles the parser table (already four implementations kept in sync by shared vectors), doubles write amplification on whole-vault reconcile, and creates a new conflict class: "I edited BLOCKS by hand; reconcile overwrote me."
6. **Closed-task rule collision.** Reconcile never touches closed tasks (§4.1). A closed P with open dependents, or an open P with closed dependents, needs explicit carve-outs or the rule breaks.
7. **Move/rename/archive fan-out.** Moving D must rewrite P's mirror; archiving D to `done/` must mute-but-keep or drop it; cut-and-paste heal breadcrumbs (R4) must work across both lines. Each is a new vector family.

**Beautiful — risks:**

8. **Child-slot collision.** The first-child slot is taken (DEPENDS ON; second if `❌ CANCEL LOG` exists). On `^prj`, `🧩 Sub-projects:` follows Depends-On; `🗓️ SCHEDULE LOG`, Work Log, and prose children follow. A BLOCKS bullet has no natural slot that keeps the DEPENDS ON pair adjacent without pushing logs down.
9. **Markdown can't collapse; render can.** A stored line with 12 links is one unreadable wrapped source line and an ugly raw-mode line on mobile. The existing chips solve this by collapsing (`✓×N`, wrap-between-chips, §7.4) — but only because they are *render*, not storage.

**Verdict on the literal plan:** automatic + reconcile-owned is the right *ownership* instinct, but a stored authoritative reverse bullet fails the project's own prior criteria (bloat, crowding, single authority). It should not ship as specified.

## 4. Options compared

| Option | What ships | Verdict |
|---|---|---|
| **A. Stored authoritative reverse bullet** (literal request) | `BLOCKS` line is a second source of truth, hand-editable, projected to fields | **Reject.** Dual authority; diverges; unbounded bloat; doubles parser/write cost. |
| **B. Stored derived mirror** | `BLOCKS` line is read-only projection of forward edges; reconcile + Task Card own it; hand edits canonicalised away with warning | Feasible if ink-on-page is mandatory. Still pays bloat + write amplification. See §5. |
| **C. Virtual reverse index (no new markdown)** | Prerequisite shows reverse chips/rows computed live from the forward graph: Live Preview chips, Task Card "Blocked by N" section, picker badges, `bob task dependents` / query support | **Recommend for V1.** Zero migration, zero divergence, collapsible, complete. See §6. |
| **D. Hybrid** | C by default; B behind an opt-in setting per note/task | Acceptable follow-up only if C proves insufficient after trial. |

## 5. If ink is mandatory: the only safe stored design (Option B)

Treat the reverse line as **render spilled to disk**, never as input:**

- **Grammar (mirror of §2.1).** `⛓️ **BLOCKS:** [[#^d1]] • [[path#^d2]]…` — same chain emoji so the pair scans together; same `•` separator; no aliases/embeds/strikes; order = dependent creation order (append; never re-sort); empty list deletes the line. I recommend `BLOCKS` (active verb, pairs with `DEPENDS ON`) over `BLOCKED BY` (that's the *dependent's* perspective and would mislabel P's own line).
- **Position.** Directly after the task's own DEPENDS ON line when present, else in the first-child slot logic (§2.1); on `^prj`, after `🧩 Sub-projects:`. Never displaces DEPENDS ON.
- **Authority.** Forward line in, reverse line out. Reconcile recomputes mirrors from the finalised forward set; the Task Card rewrites affected mirrors in the same one-undo transaction (§6.6 pattern). Hand edits to a BLOCKS line are **never adopted** — canonicalise-or-delete plus a `blocks_hand_edit_dropped` warning (contrast R2, which *adopts* forward field edits; the reverse must not adopt).
- **No new field.** Do not add `[blocks::]`/`[blockedBy::]`. Reverse queries invert the existing `[dependsOn::]` index; a second field doubles Tasks-plugin parse cost for zero new facts.
- **Content rules.** Direct dependents only (no transitive walk-through-`^prj` expansion; inherited residents do not duplicate their `^prj`'s row). Open + closed dependents listed; summary counts open only (mirroring §7.2 `waiting on N` semantics). Broken/non-task/unresolved links never appear as BLOCKS rows (§7.2 DC7/DC8 analogue). Blockquoted, fenced, template, `_generated`, `_conflicts`, and previous-daily-snapshot tasks never own mirrors (DP29/§4.1 analogues). Closed P's mirror is frozen, not rewritten.
- **Reconcile ordering.** Forward R1–R10 + id assignment + heal → build reverse index → rewrite mirrors (changed prerequisites only) → edges/Blocked derivation → report `blocks_mirror_updates`, `blocks_mirrors_removed`, `blocks_hand_edits_dropped`. Idempotent; quiet-interval deferred; dry-run aware.
- **Notices.** Keep the existing `⛓ Now waits on …` copy on the dependent; append at most `· 2 prerequisites updated` — never one toast per prerequisite.
- **Cost to accept.** New RB/DB vector tables in the contract doc, four-parser updates, move/archive/cut-paste vectors, migration that writes potentially thousands of lines on first run, and permanent write amplification. This is why §6 is preferred.

## 6. Recommended solution (Option C: virtual reverse, no new markdown)

Ship reverse visibility as **computed views over the existing forward graph**. No new bullet, no new field, no migration:

1. **Prerequisite chips (ledger-tools, Live Preview).** Under (not inside) P's task row, render `🔒 blocked by N →` style rows reusing the §7 chip component: miniature status checkbox, ≤40-char text, `↗ note`, tooltip, `blocking N / ✓ no longer blocking` summary. Collapse past 3 like Done does (`✓×N` pattern). Click opens D; `×`/`＋` deep-link into the Depends-on stage for D (edits still land on D's line — single edit surface preserved).
2. **Task Card section.** The Depends-on stage gains a read-only `BLOCKED — waited on by N` section listing current dependents with the same ranking/badges as RESULTS (§6.3), so the <kbd>Ctrl+Shift+P</kbd> moment that motivated this request shows both directions without writing anything to P.
3. **Query/CLI.** Add `bob task dependents <id>` (and a Dataview/Tasks-doc recipe inverting `dependsOn`) so scripts and reviews can answer "what waits on P?" without parsing new markdown. Reuse the shortest-form link formatter (§3).
4. **Reconcile change: none to markdown.** `bob task reconcile` keeps owning *forward* consistency only. Add a `--check-dependents` verify mode that reports dangling reverse *views* (there are none stored, so this is just the existing R3/R4/R7 warnings surfaced per-prerequisite) — satisfying "reconcile ensures consistency" without a second writer.
5. **Successor-notice bridge (already built).** Closing P already surfaces unblocked dependents (§12.6 Unblocked card + notification). Add the reverse preview there: the close preview lists "will unblock N" before commit — the highest-value reverse moment, with zero storage.

**Why this wins on the three goals:** *Intuitive* — one edit surface (D's line), reads appear where the question is asked (on P). *Reliable* — no dual writes, no migration, closed-task/quote/template guards inherited free, four-parser cost untouched. *Beautiful* — collapsible render, existing glyphs (`⛓️/🔒/🔓`) and `--task-status-*` tokens only, no source-mode wall of links, no child-slot fight, phone-width wrapping already specified (§7.4).

## 7. Explicit adjustments to the stated requirements

1. **No stored authoritative reverse bullet** (reject Option A). If Bryan still wants ink after trying §6, allow only the derived read-only mirror in §5, default off.
2. **`bob task reconcile` ensures forward consistency and verifies reverse views; it does not backfill a second source of truth** unless §5 is explicitly adopted — then it owns mirrors as pure projection.
3. **No new `[blocks::]` field**; invert the existing `[dependsOn::]` index.
4. **Reverse lists direct dependents only**, open-counted, closed-muted-collapsed; broken/non-task links excluded.
5. **<kbd>Ctrl+Shift+P</kbd> writes D's note in one transaction as today; P's side updates live only as render** (or, under §5, as same-gesture mirror writes with preimage checks, never rolling back D's commit on mirror failure — cf. §6.6 Pomodoro-cleanup precedent).

## 8. Suggested V1 scope (if §6 is accepted)

- Ledger-tools reverse chips + Task Card read-only section + `bob task dependents` + close-preview "will unblock N" + docs (`task-dependencies.md` §14: reverse views) + vectors (RV/DC-rank reuse, no new storage vectors).
- Deliberately out: any BLOCKS markdown, any field, any backfill migration, any hand-edit adoption.
- Trial gate for ever building §5: 2 weeks of §6 in daily use + evidence that a specific review surface needs offline ink.

## 9. Recommendation

**Build Option C and decline the stored sub-bullet as specified.** It delivers the motivating moment (seeing what P blocks, at the <kbd>Ctrl+Shift+P</kbd> gesture and at close time) with no new authority, no migration, and no beauty cost — and it keeps the hard-won single-source-of-truth architecture intact. Adopt the §5 derived mirror only as a gated, opt-in follow-up if the trial proves render-only visibility insufficient.

*Sources inspected: `docs/task-dependencies.md` §§1–9, 11–13 (grammar, R1–R10, stage, chips, successor/project rules); `src/native/task_dependencies/{mod,parse,format,legacy}.rs`; `src/native/task_status_hooks/{reconcile,mod}.rs` (scope/timing/output); `decisions:task-deps-are-depends-on-links`, `decisions:projects-block-from-prj-line`, `decisions:subprojects-inherit-project-blocking`, `decisions:task-lanes-are-sticky` via `sase memory read`.*

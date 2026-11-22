# Task req display refresh: retire depth-counted hashes — research and recommendation

Researcher: mus · 2026-11-22 · for Bryan's question on the task-reqs ("bob-cli-on" epic) display

## 0. Bottom line

**Yes, do this, and do it as a display-only change after the bob-cli-on epic lands.**
The current presentation — a hash run whose *count* encodes depth (`⌗⌗` / `⌗⌗⌗` /
`⌗⌗⌗⌗`, capped at four) in Obsidian and in the capture panel — is the weakest part of
an otherwise strong feature. It reads as Markdown heading chrome, it stops telling the
truth at depth 3, and it makes a nested scope list noisier exactly where it should be
quietest.

**Recommended solution: one fixed `⌗⌗` mark for every requirement at every depth, in
the owner's ink, with depth carried by indentation (which already carries it) and the
exact level kept in the tooltip, accessible label, and close-card row metadata (which
already carry it).** Nothing about storage, state, gestures, writes, or card behavior
changes. The change is CSS in one plugin file, one overlay view in the Mac app, and one
card-row rule — all of it instantly revertible through the existing session toggle.

Concretely, the requirements I would adjust (each marked **ADJUSTMENT** in §5):

1. Drop depth-by-hash-count and the cap-at-four rule; every req draws exactly `⌗⌗`.
2. Promote indentation to the single at-a-glance depth signal on all three surfaces.
3. Keep the exact depth readout where it already exists (tooltip / aria / card JSON)
   and require it on any new surface rather than re-encoding depth in ink.
4. Ship Obsidian first (CSS-only, same-day revertible), then the Mac overlay and the
   successor-card rows; update `docs/task-requirements.md` §4 and `docs/task-tag-marks.md`.

## 1. Question, scope, and method

Bryan's ask: now that the bob-cli-on epic is landing, change *how task reqs look* in
Obsidian and in the capture panel — the current `##` / `###`-style presentation is
bad — without changing *how they behave*. He asked for independent UX research, a
critique of the idea itself, any justified adjustments to the requirements, and a
recommended solution.

What I treated as fixed input (shared material, re-read for this report):

- `plan:202611/task_requirements.md` — the epic plan of record (Design of record §§1–10).
- `research:202611/task_reqs_design/task_reqs_design.md` (consolidated design) and the
  lead synthesis `task_reqs_design__final.md`, plus the amendment
  `research:202611/task_reqs_nested_and_notes_impact.md` (nesting to any depth;
  `REQUIREMENTS` → `NOTES` rename). The amendment wins on conflicts, per the plan.
- Bryan's original cleanup spec behind all of it: store checkbox bytes, *"The `[ ]`
  checkbox should not be shown, only `##`"*, `- [<space>` expansion with atomic
  Backspace, Ctrl+J support. The display rule is Bryan's own; only its *counting*
  interpretation is under review here.

What I inspected directly (this checkout plus the two linked checkouts, opened through
`sase repo open`):

- `docs/task-requirements.md` §4 (Rendering) and `docs/task-tag-marks.md` (the display
  contract for the whole tag-mark family).
- `plugins/bob-ledger-tools/src/264-plugin-task-reqs.js` (attributes, tooltip,
  `data-bob-req-depth`) and `plugins/bob-ledger-tools/styles.css` (~line 7497: the
  `--bob-req-glyph` 4-cell SVG mask and the 16-selector depth→count list).
- `Sources/BobMacCapture/CapturePanelView.swift` (`RequirementMarkerGlyphOverlay`: real
  `⌗` text, `min(depth, 3) + 1`, 4-cell slot) in bob-mac-capture.

I did not consult any peer research from this swarm; all conclusions below are my own
from the sources above.

## 2. What ships today (the thing Bryan is reacting to)

Three surfaces draw the same depth-counted run, from the same bytes (`- [ ] ` under a
task or req, no `#task`). A fourth class of surface shows raw bytes and is unaffected
by any display decision.

**Obsidian (Live Preview + Reading).** The checkbox `input` is hidden
(`appearance: none`, `pointer-events: none`) and a CSS mask paints the run: a 32×16
SVG holding four slanted hash cells, with `--bob-req-count` selecting 2, 3, or 4
visible cells by `data-bob-req-depth` (depth 1 → 2, depth 2 → 3, depth ≥ 3 → 4 — sixteen
near-identical selectors to express "3 or more"). Ink is the owner's type hue
(`--bob-req-ink` ramp over all type hues, muted for dropped/excluded). Cursor adjacency
reveals raw `- [ ] `; the tag-marks session toggle restores native checkboxes; tooltip
and accessible label read `Requirement · level {d} of "{Owner}" · {state}` plus the
teaching line *"Part of this task's scope. Met when the task closes. Drop it or make it
a task."* State styling (pending / met-moot / dropped / carried / excluded) sits on top
of the run and is independent of it.

**Mac capture panel.** `capture-parse` emits a `req_marker` span over the `[ ] ` bytes
with a depth; the overlay hides those bytes and draws literal `⌗` characters —
`String(repeating: "⌗", count: min(depth, 3) + 1)` — in an 11pt monospace Text view
pinned to a 4-character slot. Caret adjacency reveals the raw bytes. The code comment
is honest about the redundancy: *"Deeper authored indentation continues to carry the
hierarchy; the run fits the four-character marker slot and saturates at four glyphs."*

**Successor cards.** Per the contract, card rows "draw the same run before each req
row's text," indented by depth, with branch folds (`· {k} nested go with it`) and the
`Requirements · "{S}"` header. The JSON already carries exact `depth`, `path`, and
`parent_key` per row.

**Raw surfaces (out of scope, correctly).** Source mode, GitHub/`done/` views, Dataview
unfiltered queries, and plugin-less Obsidian show `- [ ] ` boxes. The plan accepts this
cost explicitly ("Raw or GitHub views of `done/` show `[ ]` boxes under done tasks"),
and no display refresh can or should fix bytes that are storage.

## 3. Why the counted-hash presentation reads badly

Against Bryan's three bars — intuitive, reliable, beautiful — the depth-by-count glyph
fails all three, for reasons that are structural rather than matters of taste.

**Intuitive: it reads as headings.** Bryan's shorthand ("using `##`, `###`, etc.")
is the diagnosis. A run of hash characters *is* Markdown ATX heading chrome
([CommonMark §4.2](https://spec.commonmark.org/0.31.2/#atx-headings): one to six
`#`), and every Markdown user has a decade of training that says "hashes at line start
mean heading level." The slanted Lucide-style mask softens this in Obsidian's
proportional UI font, but on the Mac panel the overlay is literal `⌗` text in a
monospace grid — it genuinely looks like typed `##`–`####`. The amendment report
already flagged the principle: *"keep checkbox bytes and render depth-specific marks.
Literal `###` and `####` have Markdown heading semantics… keep the glyph separate."*
The shipped design kept the glyph separate from storage but not from heading
*reading*. Worse, the encoding is backwards from headings (more hashes = *deeper*,
i.e. *less* important) while visually shouting louder with depth.

**Reliable: it saturates at four, so it lies from depth 3 on.** Depth 3 and depth 16
draw identically. The tooltip and aria label still know the truth, but the glanceable
mark — the thing a capped encoding exists to provide — gives up exactly where nesting
gets interesting. Any future "depth 5+" content silently collides. A display encoding
with a saturation lie is worse than no encoding: it teaches users to mistrust the one
signal they check fastest.

**Beautiful: it triple-encodes one fact and litters the gutter.** Depth is currently
carried three ways at once — indentation, hash count, and tooltip — and the two
always-visible ones fight: the eye must compare run lengths down the margin instead of
reading text. A three-level scope block grows a picket fence (`⌗⌗ / ⌗⌗⌗ / ⌗⌗⌗⌗`) that
pulls attention to the gutter, the opposite of the contract's own word *"quiet."* The
industry default is instructive: TaskPaper, Todoist, Things, and OmniFocus all encode
nesting with indentation alone and keep the bullet glyph constant. Org-mode's checkbox
lists — cited in the amendment as the lightweight-hierarchy analogy — likewise never
vary the marker by depth. Nobody counts glyphs to feel depth; everybody reads indent.

**A secondary reliability note:** the Obsidian implementation pays sixteen
near-identical selectors to say "≥3," and the Mac overlay pins depth math into layout
code (`min(depth, 3) + 1`) that must then be re-tested per depth. A constant mark
deletes both mechanisms.

None of this impugns the parts worth keeping: hidden unclickable checkbox, owner's-ink
coloring, cursor-reveal, session toggle, tooltip/aria with exact level, and
state-driven line treatments are all good, load-bearing display work. The *count* is
the bad part, not the mark.

## 4. Is this a good idea? Critique of the plan

**Yes — with the sequencing Bryan already proposes, this is a good, low-risk idea.**
Display-only changes are the cheapest kind of change this system can make, and this
feature was designed for exactly that: storage (`- [ ] ` bytes), derived state, card
behavior, and writes are all independent of the paint. The tag-marks contract's own
principles — display-only, small-but-distinct, truthful, reversible — describe a change
that can ship and be judged by eye rather than by audit. Doing it *after* bob-cli-on
lands is also right: the recognizer, layout zones, twin vectors, and card behavior are
still settling, and restyling mid-epic would tangle display diffs with behavior diffs
across three repos.

Caveats I would attach:

1. **Bryan asked for the hashes.** The cleanup spec's bullet 5 (*"only `##`"*) is a
   display rule in Bryan's own words, and the `⌗⌗` run is a faithful, beautified
   reading of it. My recommendation keeps that promise (a hash-family mark, checkbox
   hidden) while dropping only the *counting*. If Bryan experiences the count itself
   as the request ("deeper should look deeper"), §6 option B is the fallback — but I
   argue indent already satisfies that want better than numerals do.
2. **The Mac side is the long pole.** The Obsidian change is a CSS edit with a
   same-session toggle as its revert button. The Mac overlay ships inside an app
   release behind the project's release discipline (and GitHub Actions is the only
   gate for macOS targets), so the two surfaces will differ for at least one train.
   That is acceptable — the marks are already allowed to differ slightly by surface
   (mask vs. text) — but the rollout should say so up front rather than discover it.
3. **Three-repo paint must stay byte-identical in intent.** The shared-vectors
   discipline that governs behavior twins should extend, lightly, to the paint: one
   stated mark (`⌗⌗`, owner's ink) referenced from `docs/task-requirements.md` §4, so
   the next surface (cards today, any future client tomorrow) copies rather than
   re-invents.
4. **Do not smuggle behavior.** The temptation will be to also "fix" near-display
   things (raw `done/` views, Dataview `TASK` queries listing reqs, the `## Notes`
   promotion shape). Those are behavior or migration issues with their own owners
   (the migration phase already reports unfiltered Dataview queries). A display
   refresh that rewrites queries or bytes stops being revertible. Keep the boundary
   clean.

## 5. Adjustments to the requirements (explicit callouts)

Each of these revises the plan/contract as written; everything unmentioned stands.

- **ADJUSTMENT 1 — uniform mark, no depth count, no cap.** Replace "depth 1 draws
  `⌗⌗`, depth 2 `⌗⌗⌗`, depth 3+ `⌗⌗⌗⌗`" with "every req draws `⌗⌗`." Delete the
  saturation rule and its sixteen-selector CSS expression along with it. Rationale:
  removes the heading read, the depth-3+ lie, and the per-depth code paths in one move.
- **ADJUSTMENT 2 — indentation is the glanceable depth signal, on all surfaces.**
  Require that any surface rendering reqs preserves authored indentation (Obsidian
  list indent, Mac draft indent, card-row indent — all already true) and state it as
  the contract, so future surfaces cannot flatten depth into a list and compensate
  with glyph tricks.
- **ADJUSTMENT 3 — exact level stays machine-readable everywhere.** Keep
  `data-bob-req-depth`, the `level {d}` tooltip/aria text, and the card JSON
  `depth`/`path` fields exactly as shipped; require any new surface to expose exact
  depth out-of-band rather than in ink. Rationale: the truth moves off the glyph into
  metadata, where it has no cap and no beauty cost.
- **ADJUSTMENT 4 — ship in surface order: Obsidian, then Mac overlay, then cards.**
  The plan's phases treat the paint as one thing; the rollout should sequence it by
  revertibility (CSS toggle → app release → card rows) and explicitly tolerate a
  mixed-mark interim. Add the one-line paint reference to `docs/task-requirements.md`
  §4 plus `docs/task-tag-marks.md`, and the same sentence in the Mac overlay comment,
  so the three copies cannot drift.
- **NON-ADJUSTMENT (deliberately unchanged).** Ink stays the owner's hue and never
  encodes state or depth; the checkbox stays hidden and unclickable; cursor/caret
  adjacency keeps revealing raw bytes; the session toggle stays; all state line
  treatments (muted-struck dropped, `→` carried, faded met/moot, muted excluded)
  stay; no storage byte, recognizer rule, layout zone, write path, or card key
  changes. If any implementation needs those to change to restyle, the restyle is
  wrong.

## 6. Options considered

| Option | Shape | Verdict |
| --- | --- | --- |
| A. Uniform `⌗⌗` + indent (recommended) | Constant double-hash in owner's ink at every depth | **Ship.** Quiet, truthful (no cap), standard (matches TaskPaper/Todoist/Things/Org), smallest diff, deletes the depth→count machinery |
| B. Glyph + exact numeral (`⌗2`, `⌗16`) | Constant hash with a small depth digit | Fallback only. Exact at a glance, but the digit reads as a count/quantity, adds a second code path per depth, and clutters the gutter it was meant to quiet |
| C. Thread rail (vertical fold-guide through the gutter) | Indent guides linking parent to children | Prettiest for deep trees, but needs real DOM/geometry on all three surfaces; contradicts the attribute-only, no-DOM-node Obsidian implementation and the 4-cell Mac slot. Revisit only with a dedicated rail epic |
| D. Weight/opacity ramp by depth | Same `⌗⌗`, fading with depth | Fails the reliability bar: adjacent depths are indistinguishable, and fading already means met/moot/dropped — overloading it with depth confuses state with structure |
| E. New glyph family (dots, chevrons, mini list-tree icon) | Abandon hashes for a non-`#` shape | Cures the heading read but breaks Bryan's explicit "only `##`" display rule and the one-step-down-from-`⌗` family story for zero depth-signaling gain over A |
| F. Status quo (counted run, cap 4) | Change nothing | Rejected: heading collision, saturation lie at depth ≥ 3, and the noisiest gutter of the six |

Why A beats B (the only serious rival): B optimizes the rarest question ("exactly how
deep is this row?") at the cost of the commonest glance (a quiet, scannable scope
list). The exact answer is already one hover away and is exact *without* a cap there;
indent answers "deeper/shallower than its neighbors" instantly and relatively, which is
what scope reading actually needs. A also wins on reliability: no per-depth branches,
no saturation, correct at depth 16 on day one.

## 7. Recommended solution (display spec)

**The mark.** Every requirement row draws exactly `⌗⌗` — the existing two-cell
slanted-hash mask, unchanged geometry — in `--bob-req-ink` (owner's type hue or
default teal; existing ramp untouched). Ink continues to never encode state or depth.

**Depth.** Shown by indentation alone. `data-bob-req-depth`, tooltip
(`Requirement · level {d} of "{Owner}" · {state}` + teaching line), accessible label,
and card-row `depth`/`path`/`parent_key` are unchanged and remain the exact-depth
authorities. No surface may flatten indentation without exposing depth adjacently.

**States.** Unchanged: pending full ink; met/moot owner's done/cancelled treatment
with faded run; dropped muted + struck with Cancel Log child and the existing
`task-statuses.css` override; carried run + small `→` with live Task-Link status mark;
excluded muted-unstruck with the `goes with "{ancestor}"` tooltip.

**Surfaces (in rollout order).**

1. *Obsidian CSS* (`plugins/bob-ledger-tools/styles.css`): collapse the depth→count
   selectors to one constant; keep the 4-cell mask, ink ramp, state rules, reveal, and
   toggle untouched. Revert = toggle or one CSS revert; verifiable in-session.
2. *Mac overlay* (`CapturePanelView.swift`, `RequirementMarkerGlyphOverlay`): draw the
   constant two-glyph run in the 4-cell slot (slot width unchanged, so layout and
   wrapping math survive); keep the `req_marker` span protocol byte-identical so
   `bob` needs no change. Ships on the app's normal train; interim mixed marks are
   declared, not discovered.
3. *Successor cards* (Obsidian picker rows, capture card, Mac Pull-In): same constant
   run before row text, rows still indented by depth, folds and headers unchanged.
4. *Docs*: `docs/task-requirements.md` §4 and `docs/task-tag-marks.md` state the
   constant mark + indent rule in one sentence each; the Mac overlay comment mirrors
   it. No vector, recognizer, layout, or card-behavior doc changes.

**Acceptance (all observable without new tooling).** A 4-deep scope block shows four
identical `⌗⌗` runs stepping right with indent; hovering any row names its exact
level; cursor/caret reveals raw `- [ ] `; the session toggle restores checkboxes; all
five states render as before; a depth-5+ fixture (already in the RQ vectors) paints
like depth 1 apart from indent; existing twin-vector suites pass untouched (they pin
recognition, not paint).

**What this deliberately leaves for later.** Thread rails (option C) if deep trees
prove hard to scan in practice; any numeral or chip readout, only if Bryan misses
at-a-glance depth after living with indent; the raw-byte surfaces (`done/`, GitHub,
Dataview), which belong to migration/behavior work, not paint.

## 8. Open questions for Bryan (two, both small)

1. The recommendation keeps your "checkbox hidden, hashes shown" rule and changes only
   the counting. If you actually *like* deeper looking deeper, say so and I will
   spec option B (numeral) instead — but live with indent-first for a week before
   deciding; I expect the numeral to feel like clutter by day two.
2. Interim mixed marks (Obsidian new, Mac old for one train) — acceptable, or hold
   the Obsidian CSS until the Mac build is ready so all surfaces flip together?

## Sources consulted

- Plan: `sase/repos/plans/202611/task_requirements.md` (Design of record §§1–10).
- Contract: `docs/task-requirements.md` (§§1–10, esp. §4 Rendering).
- Display contract: `docs/task-tag-marks.md` (glyph geometry, ink table, principles).
- Obsidian: `plugins/bob-ledger-tools/src/264-plugin-task-reqs.js`,
  `plugins/bob-ledger-tools/styles.css` (~lines 7497–7560).
- Mac: `Sources/BobMacCapture/CapturePanelView.swift`
  (`RequirementMarkerGlyphOverlay`).
- Endorsed prior research (shared input): `research:202611/task_reqs_design/`
  (consolidated design + lead synthesis) and
  `research:202611/task_reqs_nested_and_notes_impact.md` (nesting amendment).
- External: [CommonMark §4.2 ATX headings](https://spec.commonmark.org/0.31.2/#atx-headings);
  [Org manual — Checkboxes](https://orgmode.org/manual/Checkboxes.html) (lightweight
  nested scope without early ticking; analogy only, per the amendment).

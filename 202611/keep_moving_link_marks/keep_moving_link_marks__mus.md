# Keep-moving preview icon on ledger Task Links (`⏭ N`) — research

Researcher: mus · 2026-11-11 · vault + bob-cli + bob-plugins evidence, independent conclusions.

**Request.** Add a 🔑-style icon next to ledger Task Links showing how many
Ready/Pending/Next tasks in that task's leaf project have no Task Link in today's
daily file — i.e. how many rows the successor-offer picker would show on close.
Lead the design: intuitive, reliable, beautiful. Critique the plan, adjust
requirements where justified, end with a recommended solution.

**Bottom line.** Good idea, worth building — but the request as stated contains
one load-bearing error, and the fix is a one-line vault edit, not a code change:

1. The worked example contradicts the leaf-only rule. `job_email_recruiters.md`
   (`parent: [[job]]`, job is an area) is a **top-level project, not a leaf**,
   so under the canonical leaf rule completing its linked task produces **zero**
   successor-offer rows today (proven by dry-run below: `"keep_moving":[]`).
   An icon showing 4 there would promise a picker that never appears.
2. Recommended path: (a) reparent `job_email_recruiters.md` under the
   `job_2026` project (one frontmatter line) to make it a true leaf — then the
   close offers exactly the 4 unlinked Next tasks; (b) build a display-only
   `⏭ N` ledger mark in bob-ledger-tools that previews the §12.15 offer set,
   reusing the frees-marks architecture verbatim. No Rust change, no decision
   change, no release-train exception.
3. If Bryan prefers not to reparent, the honest alternative is a decision change
   extending keep-moving to top-level projects — much bigger blast radius
   (picker-size analysis below) — not a quiet icon-only change.

## 1. What exists today

**🔑 frees marks** (`docs/frees-marks.md`, the authoritative display contract;
JS mirror `141b-frees-marks.js` + `271b-plugin-frees-marks.js`, vectors in
`scripts/test-ledger-tools-frees-marks.cjs`). Each Task Link under an open
Pomodoro whose task is the last blocker of N open tasks wears quiet `🔑 N`.
One shared rule with BLOCKS rows (parity invariant: pill N == BLOCKS
`lastCount`), truthful-or-neutral (cold memo / unresolvable / closed / id-less
→ no mark, never a warning), compact pill text (rejected `🔑 frees N`),
tooltip `Closing this frees N task(s)` + up-to-3 BLOCKS-ordered rows +
`+K more` / `Also blocks W…`, Live Preview widget `side: 2` after 🔓 (`side: 1`;
order `link 🔓 🔑 N`), Reading-view host after the link/glyph, session toggle
`toggle-frees-marks` default on, tick-on-count-change, ~25 ms perf budget.

**Keep-moving offers** (`docs/task-dependencies.md` §12.15–§12.17). When a
managed Done gesture closes the task behind a **leaf project's last live Task
Link** today, the project's Ready tasks are offered as `keep_moving` rows
(trigger `last_planned`). Glyph **⏭** (Obsidian lucide `skip-forward`, Mac
`forward.end.fill`), Next status colour token, copy always leads with why and
says **not dependents**, never 🔓/`unblocked`. Offer set per triggered note N:
`[ ]` Ready, `[*]` Next, `[/]` Pending residents (lane pull order Pending →
Next → Ready, then line), excluding R (`^prj`), C (just-closed), `[?]`,
own-open-prerequisite, `#prj_is_blocked`, future-scheduled, `#hide`, custom
marks; `hand_off` dedup wins. Trigger gates K1–K8: recognised project (K1),
**LEAF(N)** (K2, R2 root-parent walk), qualifying predecessors with own live
links (K3), no other live link to open N work (K4), R open and unblocked (K5),
N non-empty (K6), no project-group for N (K7), `plan.link_unblocked` +
`plan.keep_moving` on, not a cancel (K8).

**Leaf** (glossary `leaf-project`, `docs/projects.md`, R2 in
`docs/pomodoro-homes.md`, code `is_leaf_project` in
`src/native/task_complete/keep_moving.rs`): a project note that is **not its
own root parent** — its parent walk meets another project before any area, and
no `root: true`. Top-level projects (parent walk reaches an area first),
`root: true` projects, and orphans are roots, never leaves. Areas, dailies,
inbox, `done/` never leaves.

## 2. Headline finding: the example is not a leaf (proven)

Evidence (all observed this session):

- `job_email_recruiters.md` frontmatter: `parent: "[[job]]"`,
  `type: "[[project]]"`. `job.md`: `parent: "[[area]]"`, `type: "[[area]]"`.
  Parent walk reaches an area before any other project → top-level → root →
  **not a leaf** under every statement of the rule (glossary, projects.md,
  §12.15 vocabulary, `is_leaf_project`).
- Scratch-copy dry-run (copy of `~/bob`, `--dry-run`, no vault writes):
  `bob capture -b /tmp/leafprobe_13 -f json --dry-run --
  "!job_email_recruiters:bryan-stephen-luzern-risk"` completed the linked task,
  struck its WRITE ledger link, and returned `"unblocked":[]`,
  **`"keep_moving":[]`**. The 4 unlinked Next tasks (`^ecogpt`, `^ray-lyles`,
  `^product-engineer-dan-dowd`, `^senior-rust-java-engineer` — no
  `[dependsOn::]`, no `[scheduled::]`, no `#hide`) would be offered if N were a
  leaf; K2 is the gate that fails.
- Corroborating sweep of today's ledger (`2026/20261111.md`): `bob.md` and
  `sase.md` (parents `[[dev]]`, an area → top-level), `sase_blog.md`
  (`root: true` → never leaf), `cash`/`body` (areas, not projects). **Zero of
  today's Task Links resolve to tasks in leaf projects.** As specified
  (leaf-only), the new icon would appear nowhere today — including on the very
  link the request names.
- The Done history agrees with the confusion: `job.md` records
  `Split out job email tasks into a leaf project!` — the author believes it is
  one. It is not, by one parent link.

**Adjustment A1 (required, data not code).** Reparent
`job_email_recruiters.md`: `parent: "[[job]]"` → `parent: "[[job_2026]]"`.
`job_2026.md` is a project (`type: [[project]]`, `parent: [[job]]`), so the
walk becomes project-before-area and the note becomes a true leaf with no other
change (blocking, rollup, routing, and Ready caps are unaffected by leafness
per projects.md; time groups under `job_2026`'s root instead of itself — the
only reporting side effect, and arguably the intent). Then re-run the same
dry-run and expect `keep_moving` with 4 selectable rows (Pending → Next →
Ready, then line). If Bryan would rather keep the area parent, stop: the
project becomes extending §12.15 to top-level projects (§6, rejected by default).

## 3. Is this a good idea?

Yes — with the A1 fix, it is the natural completion of a pair. 🔓 looks
backward (freed by), 🔑 looks forward over dependents (frees), and this looks
forward over project-mates (keeps moving). Three concrete uses: (1) morning
planning — see which closes pull a batch behind them; (2) close-time
no-surprise — the picker never ambushes; (3) leaf hygiene — links that
*should* pull but show nothing expose misparented notes like §2. Risks and
answers:

- **Noise.** Low. Gated on leaf-project residence + N ≥ 1 + today's open
  Pomodoros, it fires rarely (zero rows in today's ledger pre-A1; one row
  post-A1). Same quiet pill language as 🔑 keeps it calm.
- **🔑 vs ⏭ confusion.** Real but manageable: both are trailing `glyph N`
  pills. The pairing is principled — 🔑 = dependency unlocks, ⏭ = project
  keep-moving (the picker's own glyph, Next colour token) — and ordering tells
  the story past → future-deps → future-project. Tooltips carry the meaning
  (`frees` vs `more in`), exactly as the compact-`🔑 N` decision already
  accepted for frees. Do not invent a third metaphor (no ➕/📦/S-counter).
- **Count ≠ offer lying.** The only serious reliability risk. A read-time
  preview cannot know gesture-time facts (K4 last-link, K5 R-state, K7
  grouping, §12.2 net-pass drops, dependsOn snapshot availability). Mitigation:
  honest copy — the tooltip must say what the number *is* (unplanned ready
  residents), never what *will happen* (see §5). With that copy the icon is
  truthful in every state, including multi-link notes where no picker would
  fire.
- **Staleness.** Same solved problem as 🔑: Tasks `cache-update` fan-out +
  daily `changed` + midnight rollover + toggle, ~120 ms coalesced refresh.

## 4. Alternatives considered (and why ledger `⏭ N` wins)

| Option | Verdict |
|---|---|
| Project-note chip (`N more · 1 planned` in the note's Tasks header) | Loses the decision point: Bryan chooses *which link to close* in the ledger, not in the project note. Complement, not substitute; defer. |
| Plan-block / Day-strip badge per project | Same wrong place; plan block aggregates, ledger decides. Defer. |
| Words pill (`⏭ 4 more`) or bare `+4` | Words form was already rejected for 🔑 (half the width argument wins again); bare `+4` collides with relation-card `＋` add-actions and reads as a button. Keep compact `⏭ N`. |
| Fold into 🔑 tooltip only (no second pill) | Hides the scanability that motivates the request; tooltips don't aid triage. Reject. |
| One combined pill (`🔑4 ⏭4` → `⇪8`) | Merges disjoint semantics (dependents vs residents, different pickers); untruthful when only one class exists. Reject. |
| Rust/JSON count (new `bob` query, shared with Mac idle agenda) | Correct end-state for thin-client parity (Mac can't compute from a memo it doesn't hold), but 10× the cost: contract, schema, Mac UI, release train. Defer to explicit Mac ask — frees marks made exactly this call (`Deferred: Echoes in Bob Mac Capture… Trigger: Bryan asks`). |
| Extend trigger to top-level projects so the icon "works" without A1 | Rejected by default (§6): `sase` (75 tasks), `bob`, `job_2026` would gain last-link pickers with dozens of rows; the no-cap decision (`unblocked-tasks-are-offered`) would need revisiting. Data fix dominates. |

## 5. Recommended solution

### 5.1 What the user sees

In today's daily note, each qualifying Task Link under an open Pomodoro whose
task lives in a leaf project with N ≥ 1 unplanned ready residents wears:

```text
- [ ] () — WRITE
	- [[job_email_recruiters#^bryan-stephen-luzern-risk]] ⏭ 4
```

Hovering shows (never contains `::`):

```text
4 more in job_email_recruiters · ready, not dependents
• ✉️ Founding Engineer at EcoGPT · … · Next
• 🔥 Bryan — your Python/release tooling … · Next
• ✉️ Product Engineer · Dan Dowd · Next
+1 more
Closing this alone pulls them in as keep-moving offers
```

Copy notes: header counts and names the note (basename, `this note` when
resident in the daily file — impossible for project residents, keep the branch
for symmetry with 🔑); rows are cleaned (`dependencyCleanTaskText`, 48-char
cut), lane-suffixed (`· Pending/Next/Blocked…` never raw symbols), BLOCKS-style
canonical order reused as pull order (Pending → Next → Ready, then line);
`+K more` beyond 3; last line appears **only when this link is N's sole live
link** (the true last-link predictor — §5.3 K-last). A link with company keeps
the header + rows and omits the last line, so the pill never promises a picker.

### 5.2 Glyph, placement, look

- **Glyph ⏭**, the keep-moving mark from §12.15 (lucide `skip-forward`), Next
  status colour token, no new hex — same "borrow, don't invent" move as 🔑
  borrowing no budget hue.
- **Live Preview:** zero-width `Decoration.widget` at link end, `side` after
  🔑. Current chain is 🔓(1) → 🔑(2) → off-chip(3) (`docs/off-clock-link-chips.md`);
  the counts group together: `link 🔓 🔑 N ⏭ M off`. Costs renumbering the
  off-chip side 3 → 4 (one constant + OP2-style vector update); the zero-touch
  alternative (`⏭` after off) splits the two future-counts — take the renumber.
- **Reading view:** host after `span.bob-frees-mark` when present, else after
  `span.bob-unblocked-glyph`, else after `a.internal-link` (extends the FP3/FP4
  chain, same wrapper rules).
- **CSS:** clone the `.bob-frees-mark` block as `.bob-keep-moving-mark`
  (inline-flex, 0.4em start margin, 999px radius, 0.8em tabular-nums,
  `--bob-keep-moving-mark-color` hook unset, hover wash, tick animation,
  reduced-motion + forced-colors + `body:not(.bob-keep-moving-marks)` gate).
  Never changes line height, never takes document positions, listener-free
  (survives Dataview innerHTML), DOM builder takes a fake `doc`.
- **Toggle:** `toggle-keep-moving-marks`, "Toggle Task Link keep-moving marks",
  session, default on, `applyMarkGateClass` + popout sync, no api namespace
  (v1 mirrors frees exactly).

### 5.3 Count rule (read-time preview of the §12.15 offer set)

```text
X       = linked task the qualifying ledger link resolves to (Tasks memo,
          same resolution as unblockedGlyphLinkedTask; same-note [[#^id]] ok)
N-note  = X's note path; LEAF ⇔ R2 root parent of N-note ≠ N-note, computed by
          the existing JS home-chain resolver (142-pomodoro-home-chips.js:
          frontmatter parent/type/root walk; areas/dailies/inbox/done/terminal
          and root:true/top-level/orphan ⇒ not leaf, no mark)
LIVE    = live-link key set over today's open Pomodoros (same helper as 🔑:
          unstruck dedicated Task Link rows, first-child indent, open entries
          incl. () placeholders; struck/embeds/prose/deeper/fenced/closed/Events excluded)
CAND    = [T ∈ memo.tasks : planTaskPath(T) == N-note
           ∧ planTaskStatusSymbol(T) ∈ {` `, `*`, `/`}   (raw lanes only:
             Ready, Next, Pending — never the mapped type, so [?] Blocked
             and custom marks fall out even though their type reads open)
           ∧ planTaskBlockId(T) ≠ `prj` ∧ T ≠ X
           ∧ ¬ whole-token #hide in planTaskTags(T)
           ∧ planTaskScheduledDay(T) ≤ today (no future-scheduled)
           ∧ ¬ blocksTagPresent(T, `prj_is_blocked`)
           ∧ ¬ (T carries non-empty dependsOn needing the vault snapshot
               that JS cannot prove closed → folded out, counted in FOLDED)]
UNPLANNED = [T ∈ CAND : blocksCanonicalLinktext(T, dayPath) ∉ LIVE]
M       = |UNPLANNED|;  FOLDED = |CAND| − M  (tooltip `+F needier first` line)
K-last  = no other key in LIVE resolves to an open N-note task outside {X}
mark   ⇔ qualifying-link gates (§5.4) ∧ OPEN(X) ∧ X has [id::] ∧ LEAF ∧ M ≥ 1
```

Deliberate divergences from the gesture-time classifier (all documented in the
contract doc, all in the honest-copy direction): X's own open-prerequisite
state is not re-derived (X is linked and open; K3-style predecessor checks
belong to the picker, not the preview); hand_off-dedup is not applied (a
resident that is also a dependent of X shows 🔑 on X's row and ⏭ counts it —
correct, since the picker would list it under Hand-offs, still a row); K5/K7
(R-state, existing project groups) are gesture-time and correctly ignored by an
informational count. The `offer_lanes` pointer in §12.15 names no config key
(grep finds no such setting — preset `plan.keep_moving`/`plan.link_unblocked`
only); the contract doc should name the three raw symbols instead (minor doc
fix to fold into the build).

### 5.4 Which links get the mark (mirror of frees FL1–FL16 + leaf)

All six frees gates unchanged (today's canonical daily note; dedicated Task
Link row under an open Pomodoro; resolves to exactly one open `#task` with
`[id::]`; warm memo; toggle on; truthful-or-neutral on anything else), plus:

7. LEAF(N-note) via the JS R2 resolver. Non-project notes, top-level/root/
   orphan projects, archives, inbox, terminal notes → no mark, no warning.
8. M ≥ 1. M = 0 (every resident planned, blocked, scheduled, or hidden) →
   silence, exactly as §12.15's no-selectable-rows silence.

### 5.5 Conformance vectors (run verbatim in both suites)

- **KL (leaf gating):** area-resident X → none; top-level-project X (pre-A1
  `job_email_recruiters`) → none; `root: true` X (`sase_blog`) → none; orphan
  project → none; true leaf post-A1 → mark; `done/`-archived N → none;
  `^prj`-resolving link → none (R is never offered).
- **KC (count):** 4 Next unlinked → `⏭ 4`; one resident already live-linked →
  excluded (M drops); `#hide` resident → excluded + folded line; future
  `[scheduled::]` → excluded + folded line; `#prj_is_blocked` → excluded +
  folded; `[?]` resident → excluded (raw-symbol rule) + folded; `dependsOn`
  carrier → excluded + folded; sub-project-file task → excluded (path ≠ N);
  custom symbol → excluded; M == pill N == tooltip rows + `+K more` (parity).
- **KT (tooltip):** header `N more in ‹note› · ready, not dependents`
  (pluralisation, 48-char cleaned titles, lane suffixes, no `::`); last line
  iff K-last; folded line iff FOLDED ≥ 1.
- **KP (placement/motion/liveness):** Live Preview side-order
  `link 🔓 🔑 ⏭ off`; Reading insertion chain; raw-`[[…]]` cursor stability;
  tick only on M-change (bounded LRU `path\0blockId → last M` incl. M = 0);
  toggle removes/restores with unchanged row height; refresh triggers =
  frees fan-out + project-note `changed` for any N-note behind a visible pill.

### 5.6 Performance

Per-memo caches: dependents index (exists), plus one residents index
`path → open lane tasks` built once per memo generation; per-(linkpath,
blockId) resolution once per build (exists); leaf resolution memoised per
note path per vault-tree generation (frontmatter reads are cache-only, never
disk); visible ranges only. Target: the frees perf test plus a synthetic
50-link ledger over a 3,000-task memo stays under ~30 ms per build.

## 6. Explicitly deferred (with triggers)

- Rust/JSON count + Mac idle-agenda echo (needs contract + schema + Mac UI;
  trigger: Bryan asks — the Mac is a thin client).
- `🪢 N` starts-after segment (same deferred slot as frees).
- Joint keep-moving ("closing A with B pulls…") — no gesture composes closes.
- Pills under closed entries, non-today dailies, prose links (same as frees).
- Project-note header chips / plan-block badges (§4: complements, not substitutes).
- Extending the §12.15 trigger to top-level projects: needs a new decision
  record, picker-size data (distribution of resident counts at last-link
  closes across the real vault), and a cap/no-cap ruling against
  `unblocked-tasks-are-offered`. Not this build.

## 7. Build sketch (for the implementing agent)

- New contract doc `docs/keep-moving-marks.md` (sibling of `frees-marks.md`,
  same sections; frees doc gains one line under Deferred pointing at it).
  Reference docs: one row in `docs/reference/plugins/bob-ledger-tools.md`
  toggle table + behaviour paragraph; `docs/README.md` guide-table row.
- bob-plugins, `plugins/bob-ledger-tools`: pure core `src/141d-keep-moving-marks.js`
  (141c is taken by off-clock chips), plugin `src/271d-plugin-keep-moving-marks.js`
  cloning the 271b structure, styles appended after the frees block,
  `scripts/test-ledger-tools-keep-moving-marks.cjs` running KL/KC/KT/KP
  verbatim, e2e vectors appended to the frees Obsidian script
  (`scripts/obsidian-frees-marks-e2e.cjs` pattern, isolated scratch vault,
  light+dark, Live Preview+Reading).
- No Rust, no JSON schema, no `Cargo.toml`/`CHANGELOG.md` edits (daily train),
  no config keys (display-only; `plan.keep_moving: false` may optionally hide
  the pill — cheap coherence, one vector).
- Verify A1 first: reparent on a scratch copy, re-run the §2 dry-run, expect
  `keep_moving` with 4 rows (`ecogpt`, `ray-lyles`, `product-engineer-dan-dowd`,
  `senior-rust-java-engineer`), then apply to the live vault.

## 8. Open questions for Bryan

1. Reparent `job_email_recruiters` under `job_2026` (recommended — makes the
   example, the icon, and the picker agree at 4), or keep the area parent and
   open the top-level-trigger decision instead?
2. Glyph lock: `⏭ N` after `🔑` (recommended), or words while learning
   (`⏭ 4 more`) with a later compact pass?
3. Mac idle-agenda echo now or deferred until you've lived with the Obsidian
   pill?

## Appendix — raw evidence

- `job_email_recruiters.md` head: `parent: "[[job]]"`, `type: "[[project]]"`,
  `status: wip`; 5 × `[*]` Next tasks, 1 with `[id::]`, 0 with `[dependsOn::]` /
  `[scheduled::]` / `#hide`; hidden `^prj` line present.
- `job.md`: `parent: "[[area]]"`, `type: "[[area]]"`. `job_2026.md`:
  `type: "[[project]]"`, `parent: "[[job]]"`. `sase_blog.md`: `root: true`.
  `bob.md`/`sase.md`: parents `[[dev]]` (area). `cash.md`/`body.md`: areas.
- Dry-run (scratch copy `/tmp/leafprobe_13`, since removed):
  `bob capture -b … -f json --dry-run -- "!job_email_recruiters:bryan-stephen-luzern-risk"`
  → `"kind":"task_complete"`, ledger link struck in WRITE, `"unblocked":[]`,
  `"keep_moving":[]`, `"still_blocked":[]`, `"unblocked_check":"checked"`.
- Screenshot `~/tmp/screenshots/20261111_063929.png`: WRITE section shows
  `job_email_recruiters#^bryan-stephen-luzern-risk` bare and
  `sase_blog#^s0-spike 🔑 4` — the existing frees pill on a `root: true` note
  that must never gain the new pill.
- Code: `is_leaf_project` (`src/native/task_complete/keep_moving.rs`),
  §12.15 K1–K8 + offer-set table (`docs/task-dependencies.md`),
  `blocksTaskIsOpen`/`blocksDependentsIndex`/`blocksLastBlocker`/
  `blocksTagPresent` (`141-blocks-model.js`), `planTaskStatusSymbol`
  (`060-today.js`), R2 JS resolver (`142-pomodoro-home-chips.js`),
  side chain 🔓1/🔑2/off3 (`docs/off-clock-link-chips.md`).
- No `offer_lanes` config key exists (repo-wide grep) — §12.15's parenthetical
  dangles; contract doc should name raw symbols.
- Candidate follow-ups for the lead's triage (not filed as beads from this
  research turn to avoid 5-researcher duplication): A1 reparent + dry-run
  confirmation; `docs/keep-moving-marks.md` + 141d/271d build; `offer_lanes`
  doc fix; Mac-echo decision if Bryan asks.


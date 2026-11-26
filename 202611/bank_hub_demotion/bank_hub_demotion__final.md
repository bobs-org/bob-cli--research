# bank.md Is a Bank Hub, Not an Area: Consolidated Research and Recommendation

Lead consolidation of five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`,
`__gem`, in this directory) plus the lead's own verification, 2026-11-26. Scope: decide
how to remove `~/bob/bank.md`'s area-note status, what to do about the logic that
supported the hybrid, and how to then complete the work of the canceled `bob-cli-pl`
and `bob-cli-q6` epics.

## Verdict

**Unanimous across all five researchers and confirmed by the lead: this is the right
correction, and fixing it before finishing the card work is the right order.** The
"two cards" suspicion is not a future risk — it is the shipped state. gem's frame-level
inspection of the screencast Bryan recorded the morning of the cancellation
(`~/tmp/screencasts/20261126_070316.mp4`) shows `bank.md` flipping between a **BANK**
and an **AREA** title card on cursor movement and stacking **both** cards with duplicate
`Properties · 5` feet on `_`. The last real-Obsidian acceptance runs were NO-GO (14/29
narrowed, 38/64 full) with duplicate feet, second-pane Area loss, and editor timeouts —
all symptoms of two owners on one note. The arbitration layer built to reconcile them
(`249db-plugin-bank-area-arbitration.js` plus hooks across ~11 plugin files) is the
riskiest code either epic produced, and deleting it is cheaper than making it pass.

**Recommended target state, in one sentence:** `bank.md` becomes an **untyped,
path-canonical bank hub** that keeps `parent: "[[cash]]"` (breadcrumb and hue only),
keeps its `bank:` mapping and queue fence, mounts exactly one card (the Bank Card,
gated on `props_v1`), exposes no area settings, is absent from the area graph, areas
catalogs, and capture targets, and refuses task writes — with the `subscriptions.md`
album reparented to `[[cash]]` first.

## Ground truth the swarm established (independently corroborated)

- **The hybrid was designed, not accidental.** `plan:202611/area_project_cards.md`
  (pl) specifies the Area Card taking over `bank.md`'s title/foot/frontmatter while the
  Bank Card yields into the body; `plan:202611/bank_property_card_fold.md` (q6) made
  the Bank Card the title-slot owner while keeping `+` → AREA SETTINGS. The collision
  between the two spawned the `pl.9.1.x` arbitration repair chain. Finishing the epics
  as written would reinstall the inconsistency.
- **Two classifiers disagree by design.** `src/native/props/roles.rs:222` classifies
  `bank.md` as `NoteKind::Bank` **by path** before reading frontmatter; the areas
  world (`projects/scan.rs::frontmatter_is_area`, `areas/graph.rs`,
  `pomodoro_homes/facts.rs`, capture targets, note catalog) classifies it as an Area
  **by type**. Props then re-imports the area world anyway:
  `props/contract/settings.rs:82` maps `NoteKind::Area | NoteKind::Bank` onto the same
  eight settings (Summary, Lives under, Hue, Default type, Clock, Ready cap, Review,
  Capture names), six of which are inert on a taskless hub — and `chain_hue` skips
  non-area/project notes, so even a `color:` set through those settings would be
  silently ignored (gem).
- **No bank command needs the area type.** `bank/scan.rs` discovers the hub by the
  fixed path and month files by filename; `config.rs` reads only the `bank:` mapping;
  the `b` walk family never touches the area graph. The month-note template writes
  `parent: "[[bank]]"` and `type: "[[bank_month]]"` independently — months are
  unaffected by demotion.
- **The vault discipline already matches the intent.** `bank.md` has zero `#task`
  lines, ever (`git log -p` on the note and `bank/`, cld); no `[root:: bank]`
  references exist; money tasks (disputes, cancellations) already live on `cash.md`.
  But "never contains tasks" is a discipline, not an invariant — see the lead
  experiment below.
- **Removing the type alone is insufficient.** cdx's disposable-vault experiments show
  an untyped hub still receives the full eight-setting area contract from `bob props`
  (the contract keys on `NoteKind::Bank`, which keys on path), and the plugin's `+`
  entry would keep rendering AREA SETTINGS from the reported contract. The backend
  contract, the plugin arbitration, docs, fixtures, and the starter text all must
  change with the note.

## Lead verification: resolved disagreements and new findings

1. **The hybrid props contract has never shipped in a release** (settles cdx vs gem).
   `git ls-tree v0.6.0 src/native/props/` is empty: the latest tag (v0.6.0,
   2026-11-22) predates the entire props module. The installed `bob` that cdx used
   *also* self-reports 0.6.0 because the workspace `Cargo.toml` still says `0.6.0` —
   it is a post-tag dev build. So gem is right that removing `NoteKind::Bank` from the
   contract before the next train means no released bob ever carries the hybrid.
   Caveat: the train can ship any New York day, so the plan should still mark the
   contract commit `!` per `decisions:bob-cli-releases-ride-a-daily-train` rather than
   race the train.
2. **The capture write path still accepts `@bank` after demotion** (settles cld vs
   grk/mus — grk was right). Lead experiment in a disposable vault with an *untyped*
   `bank.md`: `bob capture-targets` no longer lists `bank` (type-keyed, confirmed),
   but `bob capture "@bank Buy stamps"` **succeeds and writes
   `- [ ] #task Buy stamps` into bank.md** — `capture_active_tasks.rs::routable_routes`
   deliberately ignores frontmatter ("every routable note … can hold active tasks"),
   and the write path accepts any vault-root stem. cld's assumption that bob would
   refuse with an unknown-route error is wrong. **The no-tasks invariant therefore
   needs explicit enforcement** (adjustment C below), or the first muscle-memory
   `@bank` capture quietly recreates the old semantics.
3. **Confirmed on current master:** the `settings.rs:82` hybrid arm; the `roles.rs:222`
   path classifier; `note_catalog/mod.rs` checking `facts.is_area` (line 1135) before
   `is_bank_note` (line 1157), which is why `//` Go To Notes ranks `bank.md` as an
   area today (gem's inverted-classification claim verified); the empty-vault starter
   `bank/output.rs:636` printing `type: "[[area]]"` (cld's find verified); `249db`
   present; `HOME_CARD_TYPE_NOTES` currently the two-item list (`06c87a06` removed
   `bank.md`, which is what lets the Area Card mount); the `bankHub`
   `props_contract_v1` gate in `240q:520`.
4. **cld's side finding verified:** `bank_month` is absent from
   `PARENT_RULE_NON_RECORD_TYPES` in nav-hotkeys' `208-parent-note-picker-model.js`,
   so bank month notes classify as "records" there. Pre-existing, unrelated bug —
   filed as a separate task bead, not folded into this work.
5. **mus's "bank.md is not a capture route today" is wrong.** "Root-level area notes
   are `@route` capture targets" (glossary) means vault-root *files*, not area-tree
   roots; `capture_targets.rs` pushes an Area target for any root file with
   `frontmatter_is_area`. Live and fixture runs (cld, cdx) both list `@bank` today.

## The type decision: untyped, by 4–1, and the lead agrees

mus alone recommended an explicit `type: "[[bank]]"` so classifiers key on frontmatter
instead of path magic. Rejected, with reasons the other four independently converged
on:

- `[[bank]]` resolves to the hub itself: the note would be its own type note,
  violating the vault convention that every `type:` points to a distinct definition
  note under `type.md` (gem audited all of `~/bob/*.md`: zero self-links).
- Unknown type names classify as **records** in the JS side
  (`parentRuleKindOf`, album schema kinds) — the parent picker would then refuse
  `cash` as a parent (cld). Teaching every classifier a new name buys no behavior.
- Vault precedent: singleton hubs (`dash.md`, `rotten.md`, `crowded.md`) are untyped
  children of their area.
- Path identity is already canonical in Rust (`roles.rs:222`, `bank/scan.rs`) and in
  the plugins (`bankSetupIsHubPath`). cdx verified `note_kind: bank` and hub behavior
  survive untyping unchanged.

A `bank_hub.md` type note remains a fallback if a visible locked `type:` row is ever
wanted, at the cost of a cardinality-1 type file. Also rejected: keeping
`type: [[area]]` with a "no tasks" promise or a home-card path exclusion (the hybrid
in another costume — cld's Option C, grk's taskless-area flag, gem's Alternative A),
and widening album parent rules so subscriptions can stay under bank (a real model
change for one edge — all five rejected it).

## The migration trap: subscriptions.md

All five found it: `subscriptions.md` is `type: [[album]]`, `parent: "[[bank]]"`, and
albums must parent to an area or project (`albums/registry.rs::analyze_direct_parent` →
`album_parent_kind` **Error**). Untyping bank.md without reparenting:

- fails `bob albums check` — but **`bob albums list` still exits 0 with the errors
  present** (cdx experiment), so acceptance must inspect structured issues, not exit
  codes;
- flips the subscription noun to `RecordKindResolution::Invalid`, which **disables all
  subscription matching** across `bob bank import/list/report/subscriptions/check`
  with only a warning (gem traced the loader path);
- strands the generated `## Albums` region on bank.md, because the album catalog
  planner only manages area/project hosts.

Reparent to `[[cash]]` (whose summary already names subscriptions). Subscriptions are
bound by the `subscription` noun, never by parent, so no record identity, schema, or
import history is lost (cdx verified with a controlled experiment; gem verified the
code path). **Order matters:** reparent and run `bob albums sync` *while bank.md is
still an area*, so the sync cleanly removes bank.md's `## Albums` region and creates
cash.md's; then untype; then `bob areas sync`. Keep a plain `[[subscriptions]]` link in
bank.md's prose for navigation.

## Requirement adjustments (all called out)

- **A. Reparent `subscriptions.md` to `[[cash]]` (required).** See above. Do both
  vault edits in one change so no commit window has an invalid album.
- **B. The backend contract must change too (required).** Remove `NoteKind::Bank` from
  the area settings arm in `props/contract/settings.rs`. Bank's `props show` keeps
  `note_kind: bank` and `props_v1`, keeps the card-owned `bank` key (`==`), drops the
  contract block and the eight settings; obsolete `setting.*` ops refuse. Mark the
  commit `!` and ride the daily train.
- **C. Give up `@bank` and enforce the no-tasks invariant (strengthened by the lead
  experiment).** The picker drops `@bank` automatically; the write path does not.
  Refuse task captures routed at `bank.md` with a hint toward `@cash`, and/or add a
  `bank_hub_task` finding to `bob bank check` for any `#task` checkbox in the hub.
  The lead recommends **both**: write-path refusal (prevention) plus the check finding
  (detection of tasks that arrive by hand-editing). Severity of the finding is
  Bryan's call; gem argued warning (never breaks scripts), mus argued error. Also add
  `bank_hub_area_type` (hub still declares `[[area]]` or `[[project]]`) so a
  regression is loud in one authoritative place.
- **D. Fix the teaching surfaces that would recreate the bug.** The empty-vault
  starter (`bank/output.rs:636`) prints `type: "[[area]]"` — remove the line. Update
  `docs/bank.md` ("The hub is a sub-area … holds … bank tasks such as disputes"),
  `docs/props.md`'s hybrid paragraph, the `bank`-as-sub-area examples in
  `docs/areas.md` and the areas test helpers, and the ~15 test fixtures across the
  bank suites that bake the area-typed hub (proving bank works untyped).
- **E. Defensive guards in the plugin.** Restore `"bank.md"` to the home-card
  exclusion list (one line; even a stale deploy or an accidentally restored type can
  never mount a second owner), and make the Property Editor treat `bank` as a
  no-settings kind **regardless of what bob reports** — this is also the version-skew
  tolerance for hosts running an older bob that still sends the hybrid contract.
  Reorder `note_catalog` so `is_bank_note` precedes `facts.is_area`.
- **F. Memory must move with the change (plan-gated, via `/sase_memory_write`).**
  Correct `glossary:bank-card` and `glossary:property-card` (single owner, `props_v1`,
  no AREA SETTINGS on the hub); author `glossary:area-card` / `glossary:project-card`
  in the follow-up card phase with bank.md excluded; write a new decisions strand
  ("the bank hub is path-canonical and not an area note") — an accepted plan
  (`bank_daily_acknowledgment.md`), landed docs, and two prior research reports all
  teach the sub-area model, so without a record a future planner can put it back.
  The cancel reason is the citable evidence.
- **G. "Complete the two epics" means re-scope, not replay.** Canceled ≠ unimplemented:
  pl.1–pl.8, pl.9.1.1, q6.1–q6.3, and q6.5 are landed and verified; q6.4's code and
  glossary landed (only acceptance was missing). Drop pl.9's bank takeover spike, all
  of pl.9.1.2/pl.9.1.2.1, and q6.6's area strip. Retain the real-Obsidian acceptance
  matrix (pl.9.1.3, minus bank-area cases), the retired-count re-sweep + docs +
  glossary phase (pl.9.1.4), q6.4's acceptance, and q6.6's passive-rendering proof,
  screenshot review, and docs sweep.
- **H. Do not over-read "bank row tracking only".** Rows stay in monthly notes; the
  hub keeps configuration, setup, queue fence, reports, and navigation. Keep
  `parent: "[[cash]]"` — redefined as display affinity (kicker `BANK · Cash`, cash's
  magenta hue), not an area-graph edge. No file moves, no renames, no ledger or
  journal migration.

## Recommended solution: one new epic, five phases

One epic (cld, gem) over a cleanup epic plus two follow-ups (grk, mus): most remaining
work is acceptance, docs, and memory rather than new code, and one epic keeps the
"nothing falls through the cracks" inventory in a single plan. Phases 1–3 are
mutually independent and can run in parallel; 3 must not wait on 2's release.

| # | Phase | Repo(s) | Size | Content |
| --- | --- | --- | --- | --- |
| 1 | `vault-hub` | vault | small | Reparent `subscriptions.md` → `[[cash]]`; `bob albums sync` (cleans bank.md's `## Albums`, populates cash.md's); untype `bank.md`; trim "disputes and cancellations" from summary and prose, add `[[subscriptions]]` + money-tasks-live-in-`[[cash]]` pointers; `bob areas sync`; verify `bob areas/albums/bank check` structured-clean, `props show bank.md` still `note_kind: bank`, `capture-targets` drops `bank`, subscription matching intact. |
| 2 | `cli-unhybrid` | bob-cli | small | Adjustment B contract change (commit with `!`); capture write-path refusal for `@bank` tasks; `bank_hub_task` + `bank_hub_area_type` findings; starter-text fix; `note_catalog` reorder; invert hybrid tests; fixture + docs hygiene (D). |
| 3 | `plugin-unarbitrate` | bob-plugins | medium | Delete `249db` and all arbitration threading (`248c/248ca/248cb/248cc/249d/249da/249e`, `249ca` partial, `298m/298w/298x`); restore `"bank.md"` home-card exclusion; revert `240q`'s bankHub gate to `props_v1`; bank = no-settings kind regardless of backend; resolve `240r` foot-lifecycle change **by species-agnostic test** (revert unless a non-bank two-pane test proves it fixes a real bug); convert the bank-area e2e cases to single-card assertions; fix the baseline blockers (e2e selfTest modal fixture at `obsidian-frontmatter-takeover-e2e-lib.cjs:1063`, docs inventory check, vim cursor fixture); forward-commit, never `git revert` (the arbitration commits are mixed with keeper work); `npm test`, rebuild, `bob plugins sync` from clean master (this also clears the recorded deploy drift). |
| 4 | `takeover-proof` | bob-plugins (real Obsidian) | medium | Fail-open matrix for area, project, inbox, and bank cards: one title and one foot on bank.md in LP and Reading; `_`/`-`/`==`/`+` independent (`+` = generic Property Editor, `bank` row hands to `==`); fail-open restores native Properties on Source, embed, popover, mobile, bad YAML, path change, mount loss, unload, old bob; two-pane independence; no `j`/`k`/`gg` focus traps; `^prj` cursor integrity; light/dark × narrow/wide screenshots. Use `BOB_BIN` from master. |
| 5 | `finish` | bob-plugins + bob-cli + memory | medium | q6.6 minus the area strip (passive-rendering proof: repeated folds/repaints produce zero vault writes and zero paint-triggered bob spawns; screenshot review; docs sweep); pl.9.1.4 (retired-count dry-run then apply, final docs); glossary strands with corrected bank wording and the new decisions strand via `/sase_memory_write`; verified clean deploy. |

**Why the vault phase can land first (cld's argument, lead-endorsed):** with the
currently deployed plugin and installed bob, an untyped bank.md already fails
`homeCardEligible`, so the Area Card stops mounting immediately — the live two-card
bug is fixed by a one-line, one-line-reversible vault edit before any code lands. The
only interim leftover is `+` showing AREA SETTINGS (from the path-keyed backend
hybrid) until phases 2–3 deploy.

**Version skew to design for:** `bob plugins sync` deploys instantly; bob-cli ships at
most once per New York day and the Mac can lag further. The plugin must not trust the
backend's contract for bank (render the generic editor for `note_kind: bank` even when
an older bob sends AREA SETTINGS), and once phase 2's release lands, the existing
"never downgrade a confirmed contract" handling keeps area/project ownership intact.

**Epic-level acceptance:** exactly one Bank Card on bank.md (title slot, Setup fold,
one foot), native Properties hidden under `props_v1` with every uncertainty failing
open; no AREA SETTINGS on bank.md from either repo; `bob areas list` has no bank row;
albums/bank checks structured-clean with subscriptions matching under cash; `@bank`
task captures refused; no code path mentioning a Bank/Area owner or `suppressBankFoot`
survives; area/project cards meet pl's original acceptance (typed settings, byte-exact
undo, zero paint writes/spawns, fail-open).

## Risks

- **Half-landed vault edit breaks subscriptions silently.** Mitigate: both edits in
  one change; treat `bank check`'s "subscription records unavailable" warning as a
  phase failure; assert on structured issues, not exit codes.
- **The hybrid regrows.** Mitigated by the starter-text fix, the `bank_hub_area_type`
  finding, the restored plugin exclusion, and the decisions strand — four independent
  guards, each cheap.
- **`240r` revert regresses other species.** Its prune-on-disconnect foot lifecycle
  touched every card species; decide by test, not by guess.
- **Old prose keeps teaching "sub-area".** The daily-ack plan, two prior research
  reports, and `docs/bank.md` all say it; the decisions strand plus the docs sweep are
  the countermeasure.

## Open questions for Bryan (confirm at plan time)

1. Untyped hub (recommended, 4/5 + lead) vs. a `bank_hub.md` type note — confirm
   untyped.
2. `bank_hub_task` severity: warning (gem) or error (mus)? Lead recommends write-path
   refusal plus a warning finding; promote to error if a stray task ever appears.
3. One epic with five phases (recommended) vs. cleanup epic + two follow-on epics
   (grk/mus) — confirm structure.
4. Re-approve the carried-over glossary strand edits (`area-card`, `project-card`,
   `property-card`, `bank-card` polish) and the new decisions strand in the plan.

## Where the detail lives

The sibling reports in this directory carry the exhaustive evidence: **cld §4** and
**gem §5** have file-and-line removal manifests for both repos and the vault edit
tables; **cdx** has the two controlled disposable-vault experiments (contract behavior
and the album parent trap) and the acceptance-evidence matrix; **gem §2** has the
screencast frame analysis and the full phase-by-phase landed/canceled audit of both
epics; **grk** has the decision-by-decision mapping to the governing `decisions:`
records and the before/after figures (`dual-identity.png`, `sequence.png`,
`after-identity.png`); **mus §3.2** has the most detailed treatment of the (rejected)
explicit-type alternative and the project/notebook parent-policy edge cases.

Governing decisions read for this consolidation: `roster:decisions`, with
`bob-cli-releases-ride-a-daily-train`, `note-ready-cap-counts-the-lane`,
`off-clock-follows-tag-then-note-default`, `off-clock-note-defaults-filter-by-task-type`,
`theme-hue-is-config-pin-exempt-area-hash`, `projects-block-from-prj-line`, and
`notebook-routes-write-notes` (whose recorded rejection of "sub-areas for non-task
notes" is the closest existing precedent) bearing directly. Lead verification ran
against bob-cli master `4dd787bc` and bob-plugins master (fast-forwarded 2026-11-26),
with disposable-vault experiments using the installed post-tag dev build.

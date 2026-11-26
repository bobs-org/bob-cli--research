# bank.md Should Not Be an Area: Cleanup First, Then Finish `bob-cli-pl` and `bob-cli-q6`

Researcher: `cld` (5-researcher swarm). Date: 2026-11-26.

## TL;DR

- **Yes, this is a good idea, and the order is right.** bank.md is an area today only
  because the original bank plan (`plan:202611/bank_daily_acknowledgment.md`, Vocabulary)
  wanted it to hold "bank tasks such as disputes and cancellations" and to be an `@bank`
  route. That never happened. Neither bank.md nor any `bank/` month note has ever held a
  `#task` (`git log -p` on both shows none). The vault has no `[root:: bank]`. The area
  type now buys nothing, and it costs a second property card, a props "hybrid", and the
  arbitration code that kept the canceled phases at NO-GO.
- **Yes, it currently produces two cards.** The deployed bundle (bob-ledger-tools
  1.166.4) and bob-plugins master both mount the **Area Card** on bank.md, which owns
  the title slot, foot, and frontmatter. The **Bank card** yields and drops into the
  body with its foot suppressed. Commit `06c87a06` removed `bank.md` from
  `HOME_CARD_TYPE_NOTES`, and fragment `249db-plugin-bank-area-arbitration.js` arbitrates
  between the two. Separately, bob-cli's props layer treats bank.md as a "hybrid": `+`
  shows **AREA SETTINGS** on a BANK card no matter which card mounts.
- **Recommended:**
  1. Make bank.md an **untyped** child of cash (`parent: "[[cash]]"`, no `type`), with
     no new type name.
  2. Re-parent the `subscriptions` album to `[[cash]]`.
  3. Delete the props hybrid and the plugin arbitration. Restore the single-card,
     `props_v1`-gated bank takeover that the Bank Card glossary strand already
     describes.
  4. Finish the canceled work **re-scoped**: drop the bank.md Area mount and the bank
     "area strip", and keep the takeover acceptance, the polish, and the docs and
     glossary work.
  5. Run it as **one** new epic of five phases (Recommendation section).
- **Requirement adjustments I'm proposing** (each marked **[ADJUSTED]** below):
  - give up `@bank` as a capture route;
  - re-parent subscriptions;
  - fix bob's starter text, which still teaches `type: "[[area]]"`;
  - add a cheap guard so bank.md can't silently become an area again;
  - record the reversal as a `decisions:` strand, because an accepted plan says the
    opposite.

---

## 1. Where things stand (verified 2026-11-26)

### 1.1 What landed and what was canceled

| Epic         | Landed (`done`)                                                                                                                         | Canceled                                                                                                                                                                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bob-cli-pl` | pl.1–pl.8 (one writer, contract writes/reads, home cards, card-live, editor settings/policy/parent stages); pl.9.1.1 (home ownership gate + entry routing) | pl.9 `takeover` → pl.9.1.2 (Bank/Area arbitration, itself re-planned as pl.9.1.2.1), pl.9.1.3 (real-Obsidian acceptance), pl.9.1.4 (retired-count re-sweep, docs, the three glossary approvals)                                            |
| `bob-cli-q6` | q6.1 fold kit + `_`, q6.2 bank fold, q6.3 bank title slot, q6.5 `_` for record/area/project folds                                      | q6.4 `bank-takeover`: code **and** glossary already landed (bob-cli `1ca74ece`, plugin through `dc6c76f4`); only real acceptance was missing (NO-GO). q6.6 `bank-polish` (area strip, passive proof, screenshots, docs sweep): not started. |

Two pl.9.1.2.1 sub-phases also landed before the cancel:

- `.1`: probes matched to the production contract (evidence only, NO-GO);
- `.2`: pane-local foot/title arbitration repairs (`3af803f9`).

The latest real-Obsidian Bank acceptance was NO-GO, with 14/29 passing in the narrowed
profile and 38/64 in the full run. The failures were duplicate Bank/Area feet, a nested
editor timeout, second-pane Area loss, and a "Bank wire-kind mismatch" in the settings
probe. Almost all of these exist only because two cards share one note.

### 1.2 Why there are two cards on bank.md

- `249b-plugin-home-card-model.js:7`: `HOME_CARD_TYPE_NOTES = ["area.md", "project.md"]`.
  `bank.md` was in this list until `06c87a06`, so the Area Card now mounts on any
  `type: [[area]]` note, bank.md included. The deployed `main.js` on apollo has the same
  list and three `propertyCardHomeBankAreaRegister` hits.
- `248cb-plugin-bank-setup-title.js:305-311`: "A current Area mount owns the pane's
  title arbitration. The bank card remains in the body…"
- `248c`/`248ca`: `suppressBankFoot` hides the Bank card's own foot while the Area card
  owns the pane.
- `248cc:21-40`: the bank card hands whole-frontmatter ownership to the Area card.

So the screen shows the Area Card in the title slot (`AREA · cash › …`, "🏦 Bank",
summary, Ready readout, and a foot with a nested bank row). The Bank card sits in the
body with its Setup fold and no foot.

### 1.3 The props "hybrid" (bob-cli)

- `src/native/props/roles.rs:222-228` makes bank.md `NoteKind::Bank` **by path**, before
  any type check. That part is fine and should stay.
- `src/native/props/contract/settings.rs:82`: `NoteKind::Area | NoteKind::Bank =>
  [SUMMARY, PARENT, COLOR, TYPE, CLOCK, CAP, REVIEW, ALIASES]`. This is the hybrid from
  pl.2. `contract/read.rs:199-205` therefore advertises `props_contract_v1` in bank.md's
  show report.
- `docs/props.md:193-196`: "`bank.md` is a hybrid … its other keys use the area
  contract."

---

## 2. What actually depends on bank.md being an area

bob classifies an area by `type` alone: `frontmatter_is_area` (`projects/scan.rs:359-362`)
means `type: [[area]]` on a note that is not an album. No bank command reads bank.md's
type. `bank/scan.rs:68` reads the fixed path, and `config.rs:180-199` only reads the
`bank:` mapping. Removing the type therefore changes the following:

| Area feature bank.md gets today                                             | After the change                                                                                     | Matters? |
| --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | -------- |
| Row in `## Areas` catalogs (cash.md, area.md)                               | `bob areas sync` removes it. `cash.md` keeps its `Related: [[bank]]` link.                          | Low      |
| `@bank` capture target (`capture_targets.rs:507`); parent/move/merge target | Gone. Bank-related tasks go to `@cash`.                                                             | **[ADJUSTED]** below; low |
| Home / subarea / root parent for bank month notes                           | Home and root parent become **cash**. The walk passes through non-homes (`pomodoro_homes/resolve.rs:464-543`). | None: no task or time was ever attributed there |
| Hue                                                                         | Still magenta, from cash. bank.md declares no `color`.                                             | None     |
| Ready cap, review interval, default type, clock, aliases                    | Ignored on a non-home. An `offclock` key would raise `note_offclock_ignored`.                       | None: bank.md declares none |
| Go To Notes rank (`note_catalog/mod.rs:1135` vs `:1157`)                    | Area (rank 1) → Bank (rank 4). An untyped bank.md is already tested as Bank (`note_catalog/tests.rs:160,539`). | Cosmetic |
| **Album parent for `subscriptions.md`**                                     | **Breaks.** `albums/registry.rs:631-649` raises `album_parent_kind` (Error), and `bank/subscriptions/registry.rs` then reports the album as Invalid. `bob bank check` gives only a *warning*, and subscription attribution stops without an error. | **High: must handle** |
| bank.md `## Albums` block                                                   | bob stops owning it (`albums/catalog.rs:344,389`, hosts are areas/projects only) and leaves the stale block in place. | Must clean up by hand |

The only real dependency is the subscriptions album. Everything else either does nothing
for bank.md or is a navigation nicety you have said you don't need.

---

## 3. What should bank.md become?

### Option A: untyped child of cash (recommended)

```yaml
---
parent: "[[cash]]"
summary: Every transaction and deposit, categorized in monthly notes.
created: 2026-11-11T11:31:42-05:00
bank: { … unchanged … }
---
```

- **Fits the vault rule.** `obsidian.md` memory requires only `parent`, and many root
  notes are untyped. The type notes themselves (`bank_month.md`, `album.md`) are untyped
  children of `[[type]]`.
- **Identity stays by path.** bob already identifies the hub by path (`roles.rs:222`,
  `bank/scan.rs:68`), and so do the plugins (`bankSetupIsHubPath`, `248a:29`). No new
  classifier is needed.
- **Classifies as "other" everywhere.** In Rust it is `LiteKind::Other`. In nav-hotkeys
  `parentRuleKindOf` (`208:56-85`) it is `"other"`, because the note has no type names.

### Option B: a new explicit type (`[[bank]]` or `[[bank_hub]]`)

Not recommended now.

- `type: "[[bank]]"` would make bank.md its own type note.
- In JS, any type name outside `PARENT_RULE_NON_RECORD_TYPES` (`208:22-28`: article,
  mail, day, done, type) classifies the note as a **record**. The same applies to
  `242d albumSchemaEntryKindOf`. The parent picker would then refuse cash as a parent
  ("not-record-parent").
- You would have to add the name to the JS sets, and check Rust's record-noun claims,
  for no behavioral gain.
- Revisit only if a second non-task hub appears and a `hub` concept is worth naming.

> Side finding (pre-existing, unrelated to bank.md): `bank_month` is not in
> `PARENT_RULE_NON_RECORD_TYPES` either, so nav-hotkeys classifies bank month notes as
> "record". Worth a small bug bead; it should not be folded into this work.

### Option C: keep the area type and just re-exclude bank.md from home cards

This is the cheapest path: revert `06c87a06`'s list change and stop. It leaves exactly
the inconsistent model you want gone:

- `+` still shows meaningless AREA SETTINGS on bank.md;
- `@bank` remains a route for tasks that never come;
- the hybrid stays in `bob props`.

Rejected.

### Option D: let albums use a pass-through parent (keep `subscriptions` under bank)

You could generalize the album parent rule the way notebooks work: any note whose chain
reaches an area or project, with the nearest home owning the catalog row. This touches
`albums/registry.rs`, `create.rs`, completion, and catalog in Rust, plus the parent
rules in the nav-hotkeys picker. That is a real rule change made for one album. Rejected
in favor of re-parenting. Subscriptions and bank are both "cash things", so siblings
under cash read naturally. bank.md's body can keep a plain `[[subscriptions]]` link.

---

## 4. Inventory: what to delete, what to keep

### 4.1 bob-cli

**Delete or change (logic that exists only for the hybrid or the area model):**

- `contract/settings.rs:82`: `NoteKind::Area | NoteKind::Bank` → `NoteKind::Area`. As a
  result:
  - bank.md's show loses the `contract` block;
  - `capabilities()` for bank drops to `props_v1`;
  - `setting.*` ops on bank.md refuse as unknown settings.

  This is a CLI/JSON contract change, so it needs `!` per
  `decisions:bob-cli-releases-ride-a-daily-train`; for example,
  `fix(props)!: drop the area settings contract from bank.md`.
- `contract/read.rs:1,33` comments; `cli.rs:55` help text ("Area, project, and bank
  notes also report…").
- Tests that encode the hybrid:
  - `contract/tests.rs:409-455` (`home_and_bank_roles_match_the_editor_contract`) and
    `:627-636` (`bank_show_uses_the_area_contract`). Invert them to assert that bank has
    no contract and still has a card-owned `bank` key.
  - `tests/cli/props_contract.rs:75-103,203-213` (`bank_hybrid_…`).
  - `roles.rs:772-835`: the fixture should drop `type: [[area]]`.
- `docs/props.md:193-196` (the hybrid paragraph and "bank uses the area order").
- **[ADJUSTED] `bank/output.rs:636`**: the "Paste-ready start" for a vault with no
  bank.md prints `type: "[[area]]"`. Remove that line, or a rebuilt hub reintroduces
  the bug.
- `docs/bank.md:88-95`: "The hub is a sub-area … holds … bank tasks such as disputes"
  → an untyped child of cash, holding only config and the queue.
- Hygiene (recommended, not required):
  - Make the bank-feature test fixtures that set `type: "[[area]]"` on the hub untyped:
    `tests/cli/bank.rs` (~9 sites), `tests/cli/walks.rs:11`, `bank/import_run.rs:1263`,
    `import_plan.rs:1597`, `config.rs:1436`, `naming.rs:786,936`. That proves bank
    works without the area type.
  - Rename the "bank" sub-area example in `docs/areas.md:99,224,238` and in
    `areas/{sync,report,tests}.rs` (to `recur`, for example) so docs stop teaching the
    old tree.

**Keep:**

- `NoteKind::Bank` by path (`roles.rs:222`);
- `bank` → `card("bank")` (`roles.rs:168`);
- all `bob bank` path-based discovery;
- `note_catalog`'s Bank kind.

**[ADJUSTED] Optional guard:** a `bob bank check` warning (`bank_hub_typed_home`, say)
when bank.md declares `type: [[area]]` or `[[project]]`. It is about 10 lines and makes
a regression loud in one authoritative place.

### 4.2 bob-plugins (`plugins/bob-ledger-tools/src/` unless noted)

**Delete: exists only so an Area card and a Bank card can share bank.md.**

- `249db-plugin-bank-area-arbitration.js` (whole file, `fragments.json:225`) and its
  exports `374g:45-49`.
- `249b:7`: put `"bank.md"` back into the home-card exclusion. This is a literal revert
  of `06c87a06`'s list change, and it is defense in depth if the type ever comes back.
- `249da:58-63,143-166,182,221` (bank-area register/release, releasing the bank
  frontmatter owner).
- `249d`:
  - the register/release calls at `:703,727,811,824,868,918,935`;
  - `noteKind:"bank"` at `:363-365`.
- `249e:145-151,201-220` (the nested `bank="setup"` row in the Area foot, opening Bank
  Setup from the Area drawer, and "repaint Bank Setup so it yields its duplicate foot").
- `248c`:
  - `:507` (`suppressBankFoot`);
  - `:572-574`, `:783-785` (the arbitration options);
  - `:823-826` (the `arbitration.owner ? -1` anchor);
  - `:246` (`scheduleHomeCardRefresh` after a fold toggle).
- `248ca:136-153,168` (suppression and the arbitration generation in the foot
  signature).
- `248cb:305-311` (title yield).
- `248cc:21-30` and every `bankSetupAreaFrontmatterEligible` branch.
- `249ca` `homeCardPropertyEditorNoteKind`. **Keep** `homeCardIsDesktopPlatform` in the
  same file.
- `298m:135-150` (`propertyEditorEntryBarePlusOptions` for bank) and its bare-`+`
  wiring.
- **Property Editor bank settings:**
  - `298w:6` (`PROPERTY_EDITOR_SETTING_ORDER.bank`);
  - `298w:118`;
  - `298x:215` (`"bank"` in setting kinds).

  Treat bank as a no-settings kind **regardless of what bob returns**. That keeps the
  plugin correct while released bobs still send the hybrid contract; see §6.3.
- `240q:515-526`: the `bankHub` requirement for `props_contract_v1`. Return bank to the
  plain `props_v1` gate, which is what the as-landed **Bank Card** glossary strand
  already says ("confirmed `props_v1`").
- Tests, e2e, and docs:
  - **Unit tests:**
    - `test-ledger-tools-home-card-host.cjs` (arbitration cases `:181,380,406,521,559,595`);
    - `test-ledger-tools-home-card-model.cjs:68` (invert it: an area-typed bank.md is
      **not** home-eligible);
    - `test-ledger-tools-property-editor-entrypoints.cjs:375`;
    - `test-ledger-tools-property-editor-settings-entrypoints.cjs:281`;
    - `test-ledger-tools-property-card-frontmatter-ownership.cjs:948`.
  - **Takeover e2e:**
    - `obsidian-frontmatter-takeover-e2e-lib.cjs`: `bank-area-*` checks, probes
      `:588-634`, `bankSettingsFailures`, and the bank fixture's area type;
    - `obsidian-frontmatter-takeover-e2e.cjs:540,896-1150,2036-2066`;
    - `test-obsidian-frontmatter-takeover-e2e.cjs:64-104`.
  - **Property-editor e2e:** `obsidian-property-editor-e2e-settings.cjs:176-180` ("bank
    plus keeps Area settings hybrid") becomes "bank plus shows the generic editor with
    `bank` card-owned".
  - **Docs:**
    - `docs/property-editor.md:49-51,74-76`;
    - `docs/develop/validation.md:497-498`;
    - `docs/area-and-project-cards.md:101`: keep the exclusion and add the reason
      ("bank.md is not an area").

**Keep (bank-card-only work that is good on its own):**

- the title-slot bank card (`248cb` identity, kicker crumbs `BANK · Cash`, summary
  subtitle);
- the `_` fold kit;
- the hue walk;
- `==` precedence (`248m`);
- the single-owner bank frontmatter takeover (`248cc` core, `240q:530-544,716-742`);
- the bank foot's own `nested.bank`;
- the `bankSetupLintDeltas` move into `248cd`;
- `4ae966f4` (kind-scoped releases), the Vim cursor redraw fixes, and the generic e2e
  pane fixes.

**Ambiguous: decide in the cleanup phase.**

- `240r` `propertyCardFootAdapterPruneDisconnected` (`3af803f9`). It changed the foot
  lifecycle for **every** species, and its stated reason is Bank/Area coexistence. I
  would revert to whole-scope release unless a species-agnostic test (two panes on one
  album, say) shows the new behavior fixes a real non-bank bug. If one does, keep it and
  record why.
- `241m bankCardRootHue` still reads bank.md's own `color` before the `"magenta"`
  literal. On a non-home that key means nothing to bob (`chain_hue` skips it). This is
  harmless; drop the step only if you are already editing the file.

**How to remove the code: a forward commit, not `git revert`.** The arbitration commits
(`06c87a06`, `8e401c6e`, `b185579f`, `5addf8ca`, `a0ebe63e`, `3af803f9`, `831ac794`,
`c45a92b7`, part of `072b009e`) are mixed with work to keep:

- `06c87a06` also moved `bankSetupLintDeltas`;
- `c45a92b7` also added `homeCardIsDesktopPlatform`;
- `4ac198f9` regenerated the bundle.

Reverting them would mean hand-merging generated `main.js`. Delete the code guided by
this list, then rebuild.

### 4.3 Vault

| File               | Edit                                                                                                                                                                                                                              |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bank.md`          | Delete `type: "[[area]]"`. Drop "plus disputes and cancellations" from `summary` (it is the card subtitle). Delete the body sentence "Money tasks like disputes and cancellations live here too." Replace the bob-owned `## Albums` block with a plain line such as `Related: [[subscriptions]]`. |
| `subscriptions.md` | `parent: "[[bank]]"` → `parent: "[[cash]]"`                                                                                                                                                                                       |
| then run           | `bob albums sync` (adds `## Albums` to cash.md), `bob areas sync` (drops the `[[bank]]` rows from cash.md and area.md), `bob albums check`, `bob bank check`, `bob bank subscriptions` (subscription matching still resolves) |
| `bob.md` tasks     | `bob__bank-not-area` currently `dependsOn:: bob__bank-card-first`. Your new ordering inverts this, so flip it or close it when the work lands. Your call.                                                                         |

Make the bank.md and subscriptions.md edits together, so there is no window where the
album is invalid while vault-sync commits.

---

## 5. Critique of the plan

### What's right

1. **The conceptual model gets simpler.** An area is a task residence and a policy
   source (Area Note glossary: "Every `#task` belongs in exactly one area or project
   note…"). bank.md is a config-plus-ledger hub with no tasks. With one note kind per
   card species, "which card owns this note?" has one answer, and nothing needs
   arbitration.
2. **It deletes the riskiest code in both epics.** The pane-local generation tokens,
   yield and re-acquire, and foot suppression are the source of the NO-GO results
   (duplicate feet, second-pane loss, editor timeouts). Removing them is cheaper than
   making them pass.
3. **Cleanup-first is the right order.** The remaining acceptance phases would otherwise
   build proof for code you are about to delete. pl.9.1.2.1's whole four-phase repair
   epic simply disappears.
4. **Most of the docs already match the target.** The as-landed Bank Card and Property
   Card glossary strands already describe a single bank card under the `props_v1` gate.
   Only plugin docs, bob docs, and the hybrid paragraph are wrong.

### What I'd push back on or adjust

1. **"Complete the work for these two epics" should mean re-scope, not resume.**
   - **Drop entirely:**
     - pl.9's "bank.md spike / mount the Area Card there / bank_foot suppression";
     - all of pl.9.1.2 and pl.9.1.2.1;
     - q6.6's "area strip on the bank card" (`homeCardChips`/`homeCardReadyModel`). It
       showed area policies on a note that no longer has any.
   - **Keep:**
     - pl.9.1.3 (real-Obsidian fail-open matrix), minus the Bank/Area cases;
     - pl.9.1.4 (retired-count re-sweep, docs, glossary);
     - q6.4's remaining **acceptance** only (its code and glossary landed);
     - q6.6's passive-rendering proof, screenshot review, and docs sweep.
2. **The canceled glossary decision text is now wrong, so the new plan must re-ask
   with corrected wording.**
   - `memory_area_card` included "on bank.md, owning the title and foot while the
     bank-card stays in the body". Remove that bullet.
   - `memory_property_card` said "bank.md's frontmatter is now owned through its Area
     Card". Invert it: the Bank card owns it. Area Card and Project Card strands do not
     exist yet.
   - q6's key table said `+` opens "the Property Editor (AREA SETTINGS on `bank.md`)".
     It is now just the Property Editor.
3. **[ADJUSTED] Make the loss of `@bank` explicit.**
   - The original plan intentionally kept "`@bank` … an ordinary task route". After this
     change, Mac Capture and the capture panel stop offering `bank`, and money tasks go
     to `@cash`.
   - You said bank.md never contains tasks, so I think that's right. It is still a
     visible behavior change, so it belongs in the plan's goal.
   - The data contract is unchanged: same schema, one fewer row in
     `bob capture-targets`.
4. **[ADJUSTED] Re-parent subscriptions.** This is the one hard dependency (§2). Without
   it, subscription matching turns off with only a warning.
5. **[ADJUSTED] Fix the starter text and add a guard.**
   - `bob bank`'s empty-vault starter (`output.rs:636`) would recreate an area-typed hub.
   - A `bob bank check` warning, plus the restored plugin exclusion, keeps the
     two-card state from coming back silently.
6. **[ADJUSTED] Write a decisions strand.**
   - An accepted plan (`bank_daily_acknowledgment.md`) and a landed doc
     (`docs/bank.md`) both say "bank is a sub-area".
   - A future planner reading them, or the 2026-11 research, could put it back.
   - A strand such as "The Bank Hub Is Not An Area" would cover where it applies (bob,
     plugins, vault), the claim (bank.md is an untyped child of cash that holds only
     `bank:` config and the queue; albums live under cash), why (areas are task
     residences; one card per note), the cost (no `@bank` route, no catalog row), and
     what reopens it (bank tasks returning).
   - It needs a decision-gated memory approval in the new plan. Your cancel reason is
     the citable evidence.
7. **Restore a green baseline before acceptance.** These pre-existing failures blocked
   the last attempts and will block the new acceptance phase. None of them is bank
   logic:
   - `test-obsidian-frontmatter-takeover-e2e.cjs` selfTest modal fixture (missing
     `visible:true`/`activeInside:true`; fails 17/18 on clean HEAD);
   - `docs:inventory:check` (stale `docs/bob-ledger-tools.md` and `docs/index.md`);
   - the `bank-vim-k-gg-live` cursor placed at line 10, inside the hidden YAML (q6.4
     note #4);
   - bob-ledger-tools deploy drift on athena (pl note #3; deployed 1.166.4 vs master
     1.166.5).

### Would I take a different approach?

Not fundamentally. The two alternatives I'd seriously consider are Option C (keep the
area type and re-exclude the card) and Option D (keep subscriptions under bank through
an album rule change). Both preserve accidental structure at higher conceptual cost, so
I recommend against both. The one thing I'd do differently is **land the vault change
first, not last** (§6.2). It immediately gives you a one-card bank.md, even on the
deployed plugin, and it de-risks everything after it.

---

## 6. Recommended solution

### 6.1 One new epic, five phases

Title suggestion: *"bank.md is a hub, not an area: remove the hybrid, then finish area,
project, and bank takeover."* Cite in the plan:

- `decisions:bob-cli-releases-ride-a-daily-train`
- `decisions:q-and-ctrl-bracket-mirror-esc`
- `decisions:projects-block-from-prj-line`
- the new bank-hub decision, if approved

| #   | Phase id          | Repo(s)                 | Size   | Depends on      | Content                                                                                                                                                                                                                                                                                                            |
| --- | ----------------- | ----------------------- | ------ | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `vault-hub`       | vault                   | small  | –               | §4.3 edits (bank.md untyped, summary and prose, `## Albums` block; subscriptions → cash), then the sync and check commands. Verify `bob props show bank.md` still reports `note_kind: bank`, and that `bob bank subscriptions` and `bob bank check` are clean. |
| 2   | `cli-unhybrid`    | bob-cli                 | small  | –               | §4.1: remove `Bank` from the area settings arm, update tests and docs, fix the starter text and `docs/bank.md`, add the optional `bob bank check` guard, and do the fixture hygiene. Commit with `!`.                                                                                                              |
| 3   | `plugin-unarbitrate` | bob-plugins          | medium | –               | §4.2 deletions and the props_v1 gate, ignoring a bank contract from older bobs, plus the regression test that an area-typed bank.md still mounts only the Bank card. Resolve `240r` by test. Also fix the baseline blockers (selfTest fixture, docs inventory, cursor fixture). Build, `npm test`, `bob plugins sync`; this deploy also clears the athena drift. |
| 4   | `takeover-proof`  | bob-plugins (athena)    | medium | 1, 2, 3         | Real-Obsidian fail-open matrix: pl.9.1.3 for area, inbox, project, and terminal project, plus q6.4's bank cases (hidden in LP and Reading; restored on Source, embed, popover, mobile, bad YAML, path change, unload, absent capability). Add focus/`gg`/`k` checks and screenshots. Use `BOB_BIN` from bob-cli master. |
| 5   | `finish`          | bob-plugins + bob-cli memory | medium | 4          | q6.6 without the area strip (passive-rendering proof, screenshot review, docs sweep); pl.9.1.4 (retired-count dry-run then apply, docs `area-and-project-cards.md`, `property-editor.md`, `architecture.md`, `validation.md`); the approved glossary strands (area-card, project-card, property-card, with corrected bank wording); the decisions strand if approved. |

Phases 1, 2, and 3 are independent and can run in parallel. Phase 3 must not depend on
phase 2's release.

### 6.2 Why the vault phase can go first

With the deployed (old) plugin and the released (old) bob:

- an untyped bank.md fails `homeCardEligible`, so the Area Card never mounts;
- `propertyCardHomeBankAreaRegister` never fires;
- the Bank card keeps the title, foot, and frontmatter, as the single-card q6.3 design
  intended;
- the only leftover is `+` showing AREA SETTINGS, which comes from bob's path-based
  hybrid, until phases 2 and 3 land.

It is a strictly better interim state, and it is reversible with one line.

### 6.3 Version skew to design for

`bob plugins sync` deploys immediately, but bob-cli ships at most once a day, and the
Mac's bob can lag further.

- Phase 3 must not trust bob's contract for bank. It should render the generic editor
  for `note_kind: bank` even when an older bob still sends AREA SETTINGS.
- Once phase 2's release reaches a host, bob's bank.md show report carries only
  `props_v1`. 298v already treats an ordinary note's show report as "never downgrades a
  confirmed contract", so area and project ownership on that host stays intact.

### 6.4 Acceptance for the epic

- bank.md shows exactly one card, the Bank card: title slot, Setup fold, foot, with
  native Properties hidden under `props_v1`. Every uncertainty restores native
  Properties.
- `+` on bank.md opens the generic Property Editor with `bank` card-owned (`==`).
- No AREA SETTINGS appear on bank.md, from either bob or the plugin.
- `bob bank check`, `bob albums check`, and `bob areas` report no errors, and
  subscription matching still works.
- No code path in bob-plugins mentions an Area/Bank owner, `suppressBankFoot`, or
  `249db`. In bob-cli, no settings arm includes `NoteKind::Bank`.
- Area and project cards meet pl's original epic acceptance (cards of at most five
  lines, typed settings, byte-exact undo, zero paint writes or spawns, native
  Properties gone on eligible notes with fail-open).

---

## 7. Risks

- **Subscriptions break silently** if the vault phase only half-lands (§2). Mitigate by
  editing both files in one change, then running `bob bank check`. Treat its
  "subscription records are unavailable" warning as a failure for this phase.
- **`240r` foot-lifecycle change.** Reverting a change that affects every species is
  only safe with the generic pane tests; decide by test, not by guess.
- **Loss of `@bank`.** If a muscle-memory `@bank` capture appears, bob refuses it with
  its usual unknown-route error, so nothing is lost silently.
- **Old docs and plans keep teaching "sub-area"** (the
  `bank_daily_acknowledgment.md` plan, earlier research). That is why the decisions
  strand is worth having.

## Appendix: evidence

- Bead and plan state: `sase bead read` on bob-cli-pl, -pl.9, -pl.9.1, -pl.9.1.1–.4,
  -pl.9.1.2.1, -pl.9.1.2.1.1–.4, -q6, -q6.3, -q6.4, -q6.6;
  `plan:202611/area_project_cards.md`; `plan:202611/bank_property_card_fold.md`;
  `plan:202611/bank_daily_acknowledgment.md` (ADJ-1, Vocabulary);
  `plan:202611/bank_subscriptions_album.md`.
- Vault:
  - `~/bob/bank.md` and `cash.md` frontmatter and body;
  - `bank/2026-11.md`, `subscriptions.md`, and `bank_month.md` (`parent: [[type]]`);
  - `git log -p` on bank.md and `bank/` shows no `#task` ever;
  - `bob areas list -f json` shows bank as a depth-2 area with 0 projects and 0 today;
  - `bob capture-targets` includes `bank`.
- Deployed plugin: `~/bob/.obsidian/plugins/bob-ledger-tools` manifest 1.166.4.
  `main.js` has the 2-item `HOME_CARD_TYPE_NOTES` and three arbitration register hits.
- Code references: §§1–4. I verified `roles.rs:222`, `settings.rs:82`,
  `albums/registry.rs:631-649`, `projects/scan.rs:359`, `bank/output.rs:636`, `249b:7`,
  `249db`, `248cb:305-311`, `240q:515-526`, `208:22-85`, and `298v` directly. The rest
  come from two read-only code sweeps of bob-cli and bob-plugins.

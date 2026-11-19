# Unifying intentions: frontmatter setpoints plus one property-card family

Research report — `mus` contribution, five-researcher swarm. Written independently;
no peer report from this swarm was located, opened, or read. Prior-swarm research in
this directory (daily-aim, record-card) was used as ordinary prior art.

## Bottom line

**Yes, build it — with five adjustments.** The core idea is sound: one word
("intentions") for the setpoint at every scale, stored as structured frontmatter so
Obsidian hides it and one card family renders it, edited through the existing `==`
idiom. It closes a real gap: the day has no Bryan-authored setpoint at all, and the
period setpoints (`## Intentions` / `## Outcomes` / `## Theme`) are body prose that
Dataview, Bases, and cards cannot query. But as literally specified the plan has a
storage collision, an ownership-rule break, a sentinel-in-data-field smell, an
ambiguous keymap example, and a naming collision with payment cards. Each is fixed
below without losing anything Bryan asked for.

**Recommended solution in one paragraph:** add three frontmatter keys —
`intentions:` (list of strings, Bryan), `summary:` (string, agent; `DRAFT` means
"needs one"), `reflection:` (string, Bryan) — to daily notes and period notes as
*additional* storage, leaving every existing body section and the `**Headline:**`
bullet in place; hide exactly those three keys with one CSS-snippet rule following
the `h`-property precedent; render one new **Intention Card** as note chrome that
reuses the album/record/bank card idiom and opens with the existing `==` gate
extended to daily/period targets, with a day-switcher for yesterday; write through
a new `bob daily` frontmatter writer (thin-client rule: the plugin never writes the
vault); teach agents the summary format through a new **`bob daily brief <date>`**
bundle that embeds the instructions at generation time (nothing instructional is
ever stored in the note); add the two `#periods` GTD rows mirroring the existing
weekly-draft/headline precedents; and define six glossary terms (drafts in §8).
Ship in four slices: storage+hide → card read → card write+`==` → brief+GTD rows.

## 1. What exists today (verified in-tree and in-vault)

### 1.1 The setpoints, one per scale, all body prose

| Scale | Setpoint today | Where it lives | Shape |
|---|---|---|---|
| Day | `**Headline:**` line | Daily-note preamble, read by `src/native/daily_headline.rs`, never written by bob | One line, one result |
| Week | `## Intentions` | `src/native/periods/scaffold.rs:164`, `docs/periods.md:97` | Free bullets (W45 has prose + links) |
| Quarter | `## Outcomes` | `docs/periods.md:101` | ≤3 bullets by convention (Q4 has exactly 3) |
| Year | `## Theme` + `## Outcomes` | `docs/periods.md:104-107` | Prose + bullets |

Ownership (`docs/periods.md:114-122`) is load-bearing: frontmatter/title/nav/fences/
callout belong to bob; strips and parts tables to bob-ledger-tools; `## Review` to
an agent via `bob periods draft`; `## Intentions`/`## Outcomes`/`## Theme`/
`## Reflection` to Bryan — "No tool or agent writes them." Daily `## Review` does
not exist ("Days have no Review", `brief.rs`); the day's review machinery is the
`## Reflection` one-liner (e.g. `2026/20261118.md` carries a `**Reflection**: …`
line) plus the ledger.

Prior art converges on the gap being real: the November daily-aim work found the day
has an *actuator* (Today, caps, the `]s` walk) but no authored *setpoint*, and that
weekly Intentions are not re-read until Monday. This proposal is the natural
continuation — and the requester has now explicitly chosen the word "intentions"
over the "Aim"/"Focus" alternatives, which settles the naming debate from that
swarm in favor of parallelism with the week.

### 1.2 The card family: three species, one idiom, none shared code yet

- **Album Schema Card** (`241y-plugin-album-schema-card*.js`, modal `241y-…-card.js`):
  keyboard-first, one staged gesture, dry-run consequence via bob, applies through
  the real writer. Mounted as note chrome (the album header uses
  `registerMarkdownPostProcessor`, `241v-plugin-album-header.js:19`).
- **Record Card** (`242n/242o/242p-plugin-record-card*`, stages `242q/242r/242s`):
  same stage → preview → apply shape against `bob records update -d`.
- **Bank cards**: two different things sharing a name — `bob-bank` fenced month/
  queue cards (`241m-plugin-bank-cards.js`, rendered from versioned `bob bank`
  JSON) and the Bank setup card (`248k-plugin-bank-setup-card*.js`, region logic
  in `248kb`). Both delegate writes to the shared bank action service.
- Prior `mus` record-card research (this directory) established the family rules:
  keep storage as-is, render the card as chrome after the H1, hide only what the
  card covers, never serialize YAML in JS, one staged gesture at a time.

"Generalize the code" is therefore partly done at the *pattern* level and undone
at the *code* level: no shared card framework exists; each card re-implements
mount/paint/stage/apply. That bounds the recommendation in §4 (share the gate +
chrome-mount + stage/apply skeleton; do not attempt a grand unified card rewrite).

### 1.3 The `==` keymap

`248m-plugin-schema-double-equals.js` (header comment verified): capture-phase `==`
on album notes opens the schema/setup card; `==` on a canonical record note opens
its Record Card; a vimrc `nnoremap ==` never fires because CodeMirror Vim treats
`=` as a complete operator, so the gate instead detects the pending second `=`
(`operator === "indentAuto"`, empty key buffer, no count/register, Live Preview,
normal mode). Targets today are exactly `album | bank | record`
(`schemaDoubleEqualsTargetKind`); anything else keeps Vim reindent. The
`relation-equals-alias-and-flips` decision adds one constraint: a fast `==` types
one literal `=` in relation contexts, so the intentions gate must apply only where
no relation token is under construction.

### 1.4 Daily template, GTD rows, hiding precedent

- Dailies are born from `~/bob/_templates/daily.md` (Templater), not from bob:
  frontmatter `parent/type/template/alt_file/created/date/aliases/tags/id`, H1,
  prev/week/next nav, `**Headline:**` line, `^gtd` task, `bob-plan` fence,
  `## Pomodoros`. `bob periods ensure` never creates dailies.
- `gtd_daily.md` already contains the exact precedents for both requested rows:
  `#pre #periods` "Start last week's review draft: launch an agent with …" (repeat
  `every week on Monday when done`) and `#post #headline` "Write today's headline"
  (repeat `every day when done`). PRE/POST staging and `repeat:: … when done` are
  live (`docs/freshness.md` §4).
- Hiding precedent: `h` is hidden from Properties *and* Dataview pills by
  `dataview-properties.css` (`[data-property-key="h"] … display: none`), while
  staying indexed. `id` is deliberately *not* hidden from Properties. So per-key
  CSS hiding is an accepted, surgical tool.
- `summary` already exists with other meanings: album `summary` (collection
  description) and area-note `summary:` (one line after the link in the catalog).
  New per-kind semantics must be scoped by note kind, as `root`/`type` already are.

## 2. Critique: is this a good idea?

**Yes.** Four independent reasons: (1) the day genuinely lacks an authored
setpoint; (2) "intentions" parallel to the week has the lowest learning cost of
any candidate name; (3) structured storage makes setpoints queryable (Dataview/
Bases/brief) for the first time; (4) one card idiom for schema-like editing is
exactly what the album/record/bank work already converged on. The "beautiful"
ask is also well served: chrome cards already look better than Properties rows.

**Adjustments (each justified; none removes a requested capability):**

1. **ADD frontmatter; do not REMOVE body sections or the Headline bullet.**
   "Instead of H2 sections … we should start supporting frontmatter" reads as a
   replacement, and replacement would break `bob periods brief` (reads bodies),
   `bob periods draft` (refuses without bodies, `missing_headline`), the weekly
   callout's scoring grammar, and every Dataview query over `## Review` — plus
   destroy history. Worse, weekly Intentions carry links and ✓/◐/✗ marks that a
   string list cannot hold. Keep bodies canonical for narrative; frontmatter
   canonical for the *atomic* values. Revisit unification after a quarter of use.
2. **Do not store the period; derive it.** The request wants each intentions
   block "period-associated, including daily." That association already exists
   structurally: a daily's `parent` is its week (`2026/2026-W47`), a week's its
   quarter, and so on. A stored `period:` key would be a second source of truth
   next to `parent:`. State the derivation rule instead of adding the key.
3. **Do not put a file path (or any sentinel) in `summary` as the instruction
   pointer.** A sentinel *state* (`DRAFT`) is useful; a sentinel *pointer*
   (`summary: SEE docs/foo.md`) corrupts the field's contract ("agent-set
   string"), leaks into Dataview/Bases, and still requires the agent to know to
   look — it solves nothing the GTD task text + a brief command don't solve
   better. Instructions travel in `bob daily brief` output (§6), never in data.
4. **The `[n==r` example needs a redesign, not an implementation.** As written
   it is ambiguous (relation flip? a vim sequence? a capture alias?), and `==`
   today means "open the card *on this note*." Cross-note editing through a
   magic string breaks that meaning and collides with
   `relation-equals-alias-and-flips` (fast `==` = literal `=`). Replace with: `==`
   opens the card for the current note; the card carries a day-switcher (prev/next
   day, following the record nav-ring precedent) so yesterday's reflection is two
   keys away from today. Document the exact keys; no magic string.
5. **"Bank card" needs scoping before it becomes a glossary term.** In bank code
   "card" already means payment card (`bank/naming.rs` strips card tails) and the
   UI already has *two* bank cards (fenced `bob-bank` month/queue cards vs. the
   Bank setup card). Define `bank card` as the family and name the species
   (`bank setup card`, `bank month card`, `bank queue card`) in the term itself.

## 3. Storage design

```yaml
# daily note (2026/20261119.md) and any period note
intentions:            # Bryan-owned. Day: ≤3 one-line bets. Week: mirrors ## Intentions bullets.
  - "Ship the intentions card proposal"
  - "A writing morning before any agent launch"
summary: DRAFT         # Agent-owned. DRAFT = needs summary | prose = done | absent = predates practice
reflection: "Felt tired; Rocket League by 2PM."   # Bryan-owned, one to three sentences
```

Rules:

- **Authorship** (extends `docs/periods.md` ownership): `intentions`/`reflection`
  Bryan-only, `summary` agent-only via the writer; bob owns every other
  frontmatter key as today. Writers go through the vault lock and never push
  (same contract as `periods draft`/`ensure`).
- **Types**: `intentions` is a YAML string list (Obsidian list property); empty
  list and absent both mean "none set" — never flag either (reactive days are
  legitimate; cf. the daily-aim finding that empty must be valid). `summary` /
  `reflection` are plain strings; multi-sentence reflection stays one string.
- **Period derivation**: daily → its week parent; week → itself; no `period:` key.
- **Backfill**: none. Absent keys mean "predates the practice"; every reader
  (card, brief, Dataview) treats absence as neutral. Template change covers new
  dailies; period scaffolds gain the keys as empty/absent (scaffold bytes stay a
  pure function of the id — use absent, not dated, defaults).
- **Migration of existing week/quarter/year prose**: one-way, opt-in lift
  (week `## Intentions` bullets → list; quarter `## Outcomes` → list; year
  `## Theme`+`## Outcomes` → list with the Theme first) via the existing
  `periods migrate` machinery, or manual. Never automatic, never repeated, never
  a sync: after lifting, the two surfaces are independent (body = narrative with
  links/marks; frontmatter = atomic values). The brief reads frontmatter first,
  body as fallback — a three-line rule in `note.rs`.

## 4. The property-card family and `==`

- **One new card, not a framework rewrite.** Build the **Intention Card** by
  copying the Record Card's skeleton (chrome mount after H1 via
  `registerMarkdownPostProcessor` + Live Preview editor extension, stage → dry-run
  → apply, keyboard nav Ctrl+N/P + Tab-accept per the relation-card decision,
  Esc/q/Ctrl+[ close per `q-and-ctrl-bracket-mirror-esc`). Extract only what is
  genuinely shared today — the `==` gate (`248m`) and the mount/unmount lifecycle
  (`241v`/`248c`) — into helpers the new card imports. Leave the three existing
  cards untouched: a grand unification risks all three editors for zero user gain.
- **Render rule**: the card shows if and only if `intentions` is present
  (matching the request), and renders `summary` (read-only; `DRAFT` paints as a
  "Summary pending" state) and `reflection` (editable). `intentions` rows are
  editable; `summary` has a "copy brief command" affordance, not an editor —
  agents write it, Bryan doesn't.
- **Hide exactly three keys** in one snippet rule following the `h` precedent:
  `.metadata-property[data-property-key="intentions"]`,
  `[…="summary"]`, `[…="reflection"]` → `display: none`, scoped to
  daily/weekly/quarterly/yearly notes if the snippet language allows, global
  otherwise (the keys are meaningless elsewhere). Dataview/Bases keep indexing
  them — hiding is display-only, which is precisely the requirement.
- **`==` gate extension**: add `daily | period` to `schemaDoubleEqualsTargetKind`
  (detect via frontmatter `tags:` containing `daily/weekly/quarterly/yearly`, the
  same signal `albumHeaderFileTypeIsAlbum` already uses via metadataCache). Keep
  every existing refusal (relation context, insert/visual mode, counts,
  registers); add one: refuse when a relation token is under construction, citing
  the flip decision.
- **Yesterday's reflection** (§2.4): card-level ←/→ day-switcher (record nav-ring
  precedent), defaulting to the current note. The `#post` GTD row then reads
  "open yesterday's note (or `==` → ←) and set reflection" — explicit,
  discoverable, no magic string.

## 5. The two `#periods` GTD rows

Mirror the two live precedents verbatim in shape:

```text
- [?] #task #gtd #pre #periods **Summarize yesterday**: launch an agent with
  "Summarize yesterday's daily note (`bob daily brief yesterday -f md` prints
  its bundle; write `summary:` per the bundle's instructions, replacing DRAFT)"
  · done once yesterday's `summary:` is prose.  [repeat:: every day when done] …
- [?] #task #gtd #post #periods **Reflect on yesterday**: open yesterday's daily
  note and set its `reflection:` (`==` card, ← day-switcher) · done once set.
  [repeat:: every day when done] …
```

Notes: `#pre` for the agent launch matches "Start last week's review draft"
(morning, needs nothing from today except a closed yesterday — closeout runs
~94% of days); `#post` for reflection matches "Write today's headline" (evening).
Cost caveat: a daily agent launch is the heaviest recurring agent cost in this
proposal — heavier than the weekly/quarterly drafts combined. If burden shows,
downgrade the summary row to Mon/Wed/Fri or fold it into the existing morning
`#pre #terminal` agent-cleanup row rather than weakening the walk. Idempotency
rule for agents (mirrors draft refusals): never overwrite prose `summary`
without an explicit "redo"; `DRAFT` → prose only.

## 6. Summary instructions: the brief carries them, the note never does

Requirement: agents always find the instructions; users never see them in
Obsidian. Ranked options:

| Option | Verdict |
|---|---|
| New `bob daily brief <date>` prints evidence **plus** the versioned summary instructions (periods-brief architecture) | **Recommend.** Zero bytes in the note, versioned in-repo (`docs/` + `instructions.rs` equivalent), testable, works offline. |
| Collapsed `> [!agent]-` callout in each daily | Reject: dailies are Templater-born; injecting callouts needs a vault rewrite of every day, and folds still leak in Source mode/search. |
| HTML comment in the note | Reject: visible in Source mode and search, strippable by formatters, unversioned. |
| File path in `summary` (sentinel pointer) | Reject per §2.3. |
| GTD task text alone | Insufficient (no evidence bundle, no word budget, no examples). |

`bob daily brief` v1 contents (keep small): canonical date + note path; state
(`intentions` present/absent, `summary` DRAFT/prose/absent); yesterday's
intentions; today's ledger minutes by root/type (reuse `stats` engine — "the
brief is the only source of numbers" precedent); closed vs. still-open Today
links; the day's Headline and Reflection; then ~40 lines of instructions
(word cap ~120 for the summary, finished-state voice, link evidence, no scores/
praise/advice — the period callout rules compressed). JSON + md, same facts.

This also implies the one CLI addition the plan needs: a **`bob daily` group**
(membership rule: "reads/writes dated-note chrome — intentions/summary/
reflection/headline — never tasks, ledger, or periods"). Start with two verbs:
`brief` (read-only) and a frontmatter writer (`bob daily set <date>
--intentions/--summary/--reflection`, the card's backend; staged planner,
dry-run, vault lock, `cli_rules` short flags, help in the excellent-`--help`
style). Never under `bob capture` (frozen). `just docs-gen` + `docs-check`
cover the docs gate.

## 7. Beauty and reliability notes

- Card visuals inherit the schema-card language (compact header, muted keys,
  one accent for the pending state, generous line-height) — consistency *is* the
  beauty ask; a fourth visual dialect would be the failure mode. Pending `DRAFT`
  gets the amber treatment already used for waiting money, per the bank-badge
  precedent (color never the only signal: label it "Summary pending").
- Reliability risks, each with its mitigation: (a) YAML-in-JS corruption →
  never serialize in JS; the card stages intent, `bob daily set` writes
  (record-card rule). (b) `==` misfires in vim → reuse the exact pending-equals
  gate; add relation-context refusal. (c) Daily `intentions` vs. plan/Today
  confusion → card copy and brief both state "intentions name bets; Today links
  do work; neither moves the other" (the tasks-and-lanes "different dimensions"
  rule). (d) Morning-ritual burden → one row each, empty-is-valid, no cap lint
  on Bryan's own prose.

## 8. Glossary drafts (copy-ready)

- **Intention** — *the setpoint.* One Bryan-authored bet about what a period
  will have produced: a `daily intentions` entry (≤3, one line each), a
  `weekly intentions` bullet (`## Intentions`), a `quarterly outcome`
  (`## Outcomes`), or the year's `theme` (`## Theme`). Intentions name finished
  states, never task rows; agents score them, Bryan writes them. Not a Today
  link, a lane, or freshness.
- **Property card** — *the genus.* Note chrome rendered at the top of a note
  that stands in for hidden frontmatter: it reads through the metadata cache
  and writes only through a `bob` command (never YAML in JS). Species:
  [[intention-card]], [[album-card]], [[record-card]], [[bank-card]]. Dismisses
  with Esc/q/Ctrl+[; `==` opens the card for the current note.
- **Intention card** — the property card for `intentions`/`summary`/
  `reflection` on daily and period notes. Shown only when `intentions` is set.
  Intentions and reflection edit in place; summary is read-only (`DRAFT` paints
  pending). `==` opens it; ←/→ switches days.
- **Album card** — the property card for album notes: schema overview plus the
  Schema Card editor (one staged gesture, dry-run, apply through
  `bob albums update`). Hides only the nested `record:` mapping row it covers.
- **Record card** — the property card for a record note's schema-defined value
  fields (parent album's field order; `parent`/`type`/`title`/`created` stay
  visible). Stages one edit, previews `bob records update -d`, applies through
  it. `==` on a record note opens it.
- **Bank card** — the property-card family on `bank.md` and `bank/YYYY-MM.md`:
  the *Bank setup card* (`==` editor for accounts/categories/rules) and the
  *bank month/queue cards* (`bob-bank` fences, read-only totals from
  `bob bank report`). "Card" alone never means a payment card here; payment
  cards are "payment cards" everywhere in bank docs.

## 9. Recommended build order

1. **Storage + hide** (bob-cli only): frontmatter keys documented in
   `vault-format.md`; CSS rule; template/scaffold defaults; no behavior change.
2. **Card read + `==`** (bob-plugins only): Intention Card chrome, read-only
   first, gate extension, day-switcher.
3. **Writer** (bob-cli): `bob daily set` + lock/transaction + tests; card
   stages through it.
4. **Brief + GTD rows**: `bob daily brief`; the two `gtd_daily.md` rows; glossary
   strands via `/sase_memory_write`; decision record (this unification reverses
   no existing decision but extends the ownership rule — record it).

## 10. Open questions for Bryan

1. Daily cap: ≤3 intentions (week-parallel, recommended) or 1 (Aim-swarm's
   finding that lists decay into backlogs)? Willing to start at ≤3 with a
   2026-12-31 review?
2. Should the weekly Review callout eventually read daily intentions/summaries?
   (Recommend: no — run the practice first; the 250-word cap is already tight.)
3. Confirm: `summary` prose is never overwritten by a later agent without
   "redo", and `DRAFT` is the only machine state?

## Sources checked

- Live vault 2026-11-19: `2026/20261118.md`, `2026/20261119.md`,
  `2026/2026-W45.md`, `2026/2026-Q4.md`, `gtd_daily.md` (#pre/#post #periods rows,
  #post headline row), `_templates/daily.md`, `album.md`, `bank.md` frontmatter,
  `dataview-properties.css` (`h`/`id`/`dependsOn` rules), metadata-menu present.
- bob-cli: `src/native/daily_headline.rs`, `src/native/periods/{note,brief,
  draft,scaffold,instructions}.rs`, `docs/periods.md` (ownership, caps, callouts,
  Headline §126-160), `docs/reference/vault-format.md`, `tests/fixtures/periods/`.
- bob-plugins (via `sase repo open bob-plugins`): `248m` double-equals gate,
  `241y` schema card, `242n/242o/242p/242q/242r/242s` record card,
  `241m` bank cards, `248k/248kb` bank setup card, `241v` album header mount.
- Memory: `docs.md`, `cli_rules.md`, glossary `period-note`; decisions
  `task-lanes-are-sticky`, `today-is-read-from-the-ledger`,
  `relation-equals-alias-and-flips`, `q-and-ctrl-bracket-mirror-esc`,
  `review-walk-is-tiered`, `task-decay-is-one-ladder`, `mac-capture-is-a-thin-client`.
- Prior research (orientation + named findings only; no peer report from this
  swarm opened): `daily_aim_design/` final + `daily_commitments_design__mus.md`,
  `record_card/record_card__mus.md`, `record_card_vs_schema_field_jumps.md`.

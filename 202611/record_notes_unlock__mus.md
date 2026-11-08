# Record Notes as an unlock: where the feeling is right, where it stops, and what to record next

Researcher: mus · 2026-11-08 · swarm report (`__mus`)

## Question

Bryan's hunch: "record notes" (the [bob-cli-ir epic](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-ir/README.md), plan `plan:202611/record_notes.md`, building on `research:202611/record_type_capture/record_type_capture.md`) might be a huge unlock — a way to start recording useful data he would never have considered capturing before. But which data? Is the feeling real, and what concretely would he do with it?

## Bottom line

- **The feeling is directionally right but mislabeled.** Record notes are not a quantified-self or "log everything" unlock. They are a **durable-reference unlock**: one note per *thing* (a restaurant, a show, a gift recipient, a surf spot session cluster), with a few stable fields, a verdict or status, and a revisit history. That class of data is currently either hand-written YAML, an agent one-off, or a task that vanishes into `done/`.
- **The mechanism is a threshold drop, not a new capability.** Today creating a record costs "hand-write frontmatter or ask an agent." The epic drops that to "one line in a capture draft" (`Ramen Nagi @eat/` plus `key:: value` bullets), with `bob records new/show/check` for agents and scripts. When the marginal cost of a *well-formed* note falls that far, collections that were never worth the setup become worth it. That is the unlock.
- **Expect dozens of records, not thousands of rows.** The two existing collections prove the volume point: `eat/` has 92 notes with only 2 added in five months; `podcasts/` has 15 notes, all from one migration commit. Value comes from **recall at decision time** ("where should we eat?", "what did we think of X?", "what did we get Y last year?") and **shape stability** (no more `category: null`, no 22-branch Base cleanup formula), not from throughput.
- **Concrete recommendation:** ship the four planned types (restaurant, podcast, show, movie), then add at most **two or three** high-recall types next — best candidates are **gifts given**, **bottles/wines tried**, and **surf sessions** (evidence below). Resist turning every list in the vault into a record type. Logs, streams, people, books, and one-note lists should stay where they are.

## What record notes actually are (grounded)

Per the epic plan (read via `sase artifact read "plan:202611/record_notes.md"`):

- A **record type** (e.g. `restaurant`) is a `config.yml` `records:` entry. Its id is the stem of its **type note** (`restaurant.md`); its **record folder** is one segment (`eat/`), which is also the capture spelling (`@eat/`).
- A **Record Note** is one note in that folder with `parent`/`type`/`title` frontmatter, schema fields in schema order, `created`, an always-present `## Notes`, and (for restaurants/shows) dated note bullets.
- Capture: `<title> @<dir>/` creates; `@<dir>/<stem>` updates (appends dated notes, sets fields); `- key:: value` sets declared fields; everything else is a note. Duplicates are refused; installs never replace; drafts are all-or-nothing; `bob records check` lints what other writers produce.
- The prior research report verified the current state: 92 `eat/` notes (`liked` 85, `not_liked` 7, `category: null` 6 times, 37 distinct category strings), 15 `podcasts/` notes, ~25 open watch-list tasks scattered across `now_fun.md`, `love.md`, `prj_plex.md`, and `tv.md` (one bullet), plus the `@eat` vs `@eat/` near-miss trap and the Mac `/`→`#` rewrite trap.

Two facts I re-verified for this report matter for the "unlock" question:

1. **Creation is rare and mostly agent-assisted.** The two post-migration restaurants (`rush_bowl.md`, `brown_fox_coffee_box.md`) were agent-written and already drift (`companions: []`, `lid: null`, quoted `visited`). The engine's value is shape stability plus `bob records check`, not volume.
2. **The watch history has no home.** `now_fun.md` holds `#plex` download tasks and `TV SHOW:` rows with `INSPIRED BY: %eric` / `%nona`; `love.md` holds "Watch 'F1' with Kelly"-style tasks; completing any of them archives the recommendation, the verdict, and the provenance into `done/`. The plan's rule — "a show/movie record holds the recommendation and the verdict; the download/watch action stays a task" — is exactly right, and it generalizes: **records keep the verdict, tasks keep the action.**

## Why the hunch has truth: the threshold model

Think of every candidate collection as having a setup cost (schema, folder, type note, Base) plus a per-entry cost (capture friction, field knowledge, recall of the spelling). Today both are high: setup means hand-building four vault pieces; per-entry means YAML or an agent prompt. So only two collections exist, both migrated, not captured.

Record notes attack both costs:

- **Setup becomes config + `bob records init`.** The `records-media-types` phase scaffolds type note, collection note, and `.base` from one command. Adding the fifth type is no longer a project.
- **Per-entry becomes one capture line.** The draft is the form: route completion discovers `@eat/`, `record_field`/`record_value` completion walks missing fields, folder frequencies rank suggestions (`Westfield` collapses to one row), and `bob records new` gives agents/scripts the same planner. No YAML knowledge needed.
- **Maintenance becomes `bob records check`.** Obsidian edits, agent writes, and Mac writes all get linted instead of silently drifting.

When both costs fall, the rational response is to record things whose **value per recall is high but whose entry frequency is low** — exactly the things nobody bothers to systematize today: gifts, bottles, surf sessions, recommendations with provenance. Nobody will log water intake as records (wrong grain; use tasks/ticklers/ledger), but many will capture "we tried Faust with Vinnys on 2026-01-10 — good" if it is one line.

That is the unlock: **not more data, but durable verdicts on things you revisit.**

## What you do with the data (the missing examples)

Bryan said he can't think of good examples. Here are five uses, each tied to a real vault need:

1. **Decision-time recall.** "Where should Kelly and I eat in Cranford?" becomes an `eat.base` filtered view (liked + Cranford + category) instead of memory or scrolling `eat.md`. Same for "what show did Eric recommend?" (`recommended_by:: Eric`, status `to_watch`). The Base is the index; the record is the memory.
2. **Verdict history.** Restaurants accumulate dated `## Notes` per visit; shows/movies accumulate a `verdict` (`loved/liked/meh/disliked`) plus `watched_on`. This is what `done/` destroys today. A year later, "did we like Landman, and who told us about it?" has an answer.
3. **Provenance-weighted recommendations.** `INSPIRED BY: %eric` already appears on TV rows; making `recommended_by` a suggested field turns taste into data: whose picks do you actually love? Thank them, weight them.
4. **Suggestion compounding.** Folder frequencies power `record_value` completion: locations, categories, services, companions. Every record you write makes the next one faster. This feedback loop is why the fifth record type is cheaper than the first.
5. **Agent/script queries.** `bob records list/show/check/new -f json` plus `bob query` over the folder gives agents a typed collection API: "list all `to_try` Cranford restaurants with URLs" for a date-night planner; "which gifts did we give Dad?" before a birthday. No agent needs to parse prose lists.

Non-use to be explicit about: **don't expect stats-dash insights** (counts by status are nice; correlations like "eat × pomodoro output" are speculative and not worth building). The payoff is recall and consistency, not analytics.

## Candidate next types, ranked with vault evidence

Rule (from the prior report, kept): add a type when individual things repeatedly need their own identity, a few stable fields, and a collection view that beats a list in one note. If a list in one note is enough, keep the list.

| Rank | Candidate (folder/type) | Vault evidence | Why it fits | Sketch |
|------|------------------------|----------------|-------------|--------|
| 1 | **gift** (`gifts/`, `gift`) | `gift.md` is 3 tiny sections (`%dad` Colon, `%eric` Highland Park 18, `%pops` Smart Wallet); `ideas.md` has `@BUY` rows (Cohiba Behike for Eric's birthday); birthdays/holidays recur yearly | Highest recall value per entry; prevents repeat gifts; "what did we get X last year?" is asked under time pressure | `status` (gave/idea/thanked), `recipient` (link, required), `occasion` (suggest), `given_on` (date), `price` (number), `reaction` (verdict-like: loved/liked/meh), dated notes |
| 2 | **bottle** (`bottles/`, `bottle`) | `fun.md` 260111 wine note (Faust good with Vinnys; Terre Nera Etna Rosso; Graham's Tawny bad); `%mrd` Clamada tip; cigar rows in `ideas.md` | Wine/beer/cigar verdicts are exactly restaurant-shaped (tried, liked or not, where, with whom); low frequency, high regret-avoidance ("don't rebuy the bad one") | `status` (to_try/tried/stock), `kind` (wine/beer/cigar, suggest), `where_bought`, `paired_with`, `verdict` (loved→disliked), `companions` default `[[kelly]]`, dated notes |
| 3 | **surf session cluster** (`surf/` or `surfs/`, `session`) | `surf_log.md` already logs 2025 sessions (date, spot Deal/Manasquan, board Firewire, duration, conditions, fun rating in prose) | Already a log begging for fields; spot + board + rating + conditions would answer "where was fun on what board in small swell?" | `status` not needed — use `date` (required), `spot` (suggest: Deal, Manasquan), `board` (suggest), `duration_min` (number), `rating` (1–5 or loved→disliked), `companions`, dated notes for conditions |
| 4 | **trail/outing** (`outings/`) | Weaker evidence: no existing collection found; hikes/beach days appear as prose | Only if surf pattern generalizes (boardwalk, trails, day trips with Kelly/Abby); defer until surf proves the session shape | `date`, `place`, `companions`, `rating`, `would_repeat` |
| 5 | **home/car maintenance event** | `car.md`, `casa`-ish notes exist (not inspected deeply); maintenance is date-stamped and recurs | Tempting but logs-like; a dated bullet list per asset may beat per-event notes; needs a vault scan before promoting | defer |

Explicit non-candidates (agree with plan, with one nuance):

- **Books, podcast episodes, articles** stay in `ref/` (1,240 notes). Splitting the library is worse than any record benefit.
- **People** stay `%alias` names, not notes. A `person` type would fork identity.
- **Drinks as restaurants' category** stay put — but note the nuance: `drink.md` (2 liquor-store rows) correctly stays a list, while **bottles tried** (rank 2 above) is a different thing (verdicts, not stores).
- **Water intake, meds refills (`body_ticks.md` refill log), basketball dates** are streams/logs, not things-with-verdicts. Keep them as tickler/tock lines or ledger-adjacent data; per-day record notes would spam the vault with hundreds of near-empty notes (the prior report's mus concern, still valid).
- **Ideas** (`ideas.md`) stay tasks/ticklers with tick dates. An idea becomes a record only when it becomes a thing (a show → `show`, a restaurant → `restaurant`).

## Limits and risks (why it is not unlimited)

- **Empty-note proliferation.** The prior report's warning stands: at 1–2 shows a month a record per title is fine; at daily-log frequency it is not. Gate: no `dated_notes`-only types without a verdict/status field, and no types whose entries lack a revisit question ("will I ever ask about this again?").
- **Schema design is the real cost.** Each type needs 4–8 fields with right kinds, defaults that validate, and no `null` writing. The plan's load-time validation (unique dirs, reserved type names, vault-global property kinds) is load-bearing; a second type reusing a property name with a different kind breaks Obsidian properties vault-wide.
- **Two-repo landing.** Every capture feature ships in bob then Swift behind macOS CI. Mac phases must consume documented JSON only and decode leniently. Until the Mac card ships, records are CLI/capture-text only — usable, but not the "excellent interface" Bryan asked for.
- **Config-not-applied failure mode.** A host without `chezmoi update` fails closed (existing folder → refusal) or stays literal (unknown folder). `bob records list` must keep saying "no record types configured" with the config path.
- **Over-collection burden.** Every new type adds `check` findings to triage. Keep the type count small (4 shipped + 2–3 next) and let `bob records check` stay manual until clean (plan's out-of-scope call, agreed).

## How to validate the feeling cheaply (before building more types)

1. **Two-week verdict test.** For every show/movie task completed in the next two weeks, write the verdict + recommender in the task's close note (not a record). If Bryan never re-reads them, records won't help either. If he does ("what did we think of X?"), the demand is real.
2. **Gift backfill.** Seed 10 past gifts (recipient, occasion, date, reaction) as a scratch list, not records. At the next gift occasion, check whether the list changed the decision. If yes, `gift` is type #5.
3. **Bottle log.** Next 5 bottles/cigars: one dated bullet each in a scratch note with place + verdict. Same test as above.
4. **Surf structuring.** Convert the 2025 `surf_log.md` bullets into a scratch table (date, spot, board, rating). If "which board at Manasquan in small swell?" becomes answerable, `session` is type #6.
5. **Type-count guardrail.** Revisit after show/movie ship: if `bob records check` is not clean on the first four types, add no new types until it is.

## Verdict

Build the epic as planned (four types, engine + CLI + capture + Mac card + check). Treat the "huge unlock" as **real but bounded**: it unlocks durable verdicts on revisit-worthy things, not general data capture. The next wins after the epic are gifts, bottles, and surf sessions — in that order — each validated by the cheap tests above. Everything else in the vault that looks list-shaped should stay a list until it demonstrates a revisit question records alone can answer.

# Period-note Intentions and Outcomes: what to write and when

**Swarm report (`__mus`).** Question: *"I am supposed to be manually setting
intentions and outcomes in period notes I think, but I haven't been, mostly
because I'm not sure what I'm supposed to write. Can you help me get better
at this?"*

Short answer: yes — you own four small sections, and each one is a short
promise-to-yourself written at the **start** of its period, plus one short
paragraph of meaning written at the **end**. Nothing else in a period note is
yours to write. This report explains each section, when to write it, what
"good" looks like with copy-paste examples, the minimum routine that still
works if you write nothing else, and the mistakes that make the agent-written
Review worse.

All claims below are verified against the repo contract in
[`docs/periods.md`](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_17/docs/periods.md),
the scaffold goldens under `tests/fixtures/periods/` (e.g.
`scaffold-2026-W45.md`, `scaffold-2026-Q4.md`, `scaffold-2026.md`), the
scaffold renderer
[`src/native/periods/scaffold.rs`](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_17/src/native/periods/scaffold.rs),
the agent instructions
[`src/native/periods/instructions.rs`](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_17/src/native/periods/instructions.rs),
the brief builder
[`src/native/periods/brief.rs`](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_17/src/native/periods/brief.rs),
and [`docs/reference/vault-format.md`](/home/bryan/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_17/docs/reference/vault-format.md).
No vault contents were read; paths assume the live vault (`~/bob/`, `BOB_DIR`).

## 1. The map: which sections are yours

Each period note is a scaffold bob writes once and never edits again. The
scaffold is a pure function of the period id — no clock, no `created:` field
— with one blank line between blocks and one trailing newline. Your sections
arrive empty and stay yours:

| Period note | Path pattern | Your planning section | Your meaning section |
|---|---|---|---|
| Week (`2026-W45`) | `YYYY/YYYY-Www.md` | `## Intentions` | `## Reflection` |
| Quarter (`2026-Q4`) | `YYYY/YYYY-Qn.md` | `## Outcomes` | `## Reflection` |
| Year (`2026`) | `YYYY.md` at vault root | `## Theme` + `## Outcomes` | `## Reflection` |
| All time | `all_time.md` | `## Notes` (free-form, no review) | n/a (no Reflection) |

Concretely, the week scaffold is frontmatter → title → nav → seven day
links → stats-strip fence → `## Intentions` → `## Days` parts fence →
`## Review` → `## Reflection` → agent callout. The quarter swaps in
`## Outcomes` + `## Weeks`; the year has `## Theme` + `## Outcomes` +
`## Quarters`; all-time has `## Years` + `## Notes` and no Review at all.

Ownership, from `docs/periods.md` § "Note anatomy and ownership" and the
vault-format contract:

- **Yours, and only yours:** `## Intentions`, `## Outcomes`, `## Theme`,
  `## Reflection`, `## Notes`. No tool or agent writes them. Ever.
- **The agent's (via `bob periods draft` only):** `## Review`.
- **bob's:** frontmatter, title, nav, child links, fences.
- **bob-ledger-tools', rendered live:** the stats strip and the parts table.
  No number is ever written into Markdown.
- **bob's, refreshable:** the `> [!agent]` callout. Leave it alone.

Period notes hold **no task rows** (`#task` lines are a problems-report
finding, `task_rows`). Intentions and Outcomes are prose bullets that *point
at* work, not task checkboxes that *are* work.

Review state matters because it tells you whether your words have been used
yet. First match wins: `reflected` (Reflection has text) → `drafted`
(Review has text and `review_digest` matches) → `edited` (Review text with
absent/stale digest) → `empty`. Writing Intentions never changes review
state. Writing Reflection flips the note to `reflected`, which locks the
agent out of re-drafting without your explicit "redo" — so Reflection is
genuinely the last thing you write for that period.

## 2. What each section is for (and how the Review consumes it)

### `## Intentions` (week): the week's 2–5 bets, written Monday

This is the only planning input the weekly agent reads. The brief carries
"this note's `## Intentions`" verbatim into every weekly draft, alongside
last week's Headline / Carried forward / Questions / Reflection and the
parent quarter's Outcomes. The agent then grades each intention line in the
Review's `**Intentions:**` part:

- `✓ done` · `◐ partial (name the part)` · `✗ not done` · `– no evidence`,
  each with one evidence link.

That grading is the whole point of writing Intentions well: each line should
be **checkable at Sunday night from the ledger**. If the agent has to guess
what "make progress on X" meant, you get `– no evidence` and a Question you
could have answered yourself on Monday.

Scope: one ISO week, Monday–Sunday (e.g. `2026-W45 · Nov 2 – 8`). Intentions
are weekly bets, not a backlog dump and not a status. They do not change task
status, lanes, or Today — Today is read from the Pomodoro ledger at read
time, never from anything you write in a period note.

### `## Outcomes` (quarter and year): the quarter's/year's 3–7 results

Same mechanic one level up. The quarterly brief carries "this note's
`## Outcomes`" plus the previous quarter's Headline / Carried / Questions /
Reflection and the parent year's Theme + Outcomes. The quarterly Review
grades them identically (`**Outcomes:**`, one line each, same four marks with
one evidence link). The yearly Review grades `**Theme and Outcomes:**`
together and additionally reads `h3_goal.md` and `h4_vision.md` (≤400 words
each) as context — so yearly Outcomes should visibly tie to those two files
when they exist.

Quarters are 13 whole ISO weeks (Q1 = W01–13 … Q4 = W40–W52, plus W53 when it
exists; 2026-Q4 is 14 weeks, W40–W53). Years are ISO week-years (2026 runs
Dec 29, 2025 – Jan 3, 2027, 53 weeks). Write Outcomes at the *start* of the
quarter/year; they are results you want to be able to claim at the end
("Ship …", "Finish …", "Decide …"), not activities ("Spend time on …").

The hierarchy nests: the weekly callout names the parent quarter's Outcomes
as context, the quarterly callout names the year's Theme + Outcomes, and the
yearly callout names `h3_goal` / `h4_vision`. So a good chain reads
top-down: Theme → yearly Outcomes → quarterly Outcomes → weekly Intentions.
If a weekly Intention doesn't serve any quarterly Outcome, that is either a
deliberate opportunistic bet (say so in one clause) or a sign the Outcome
list is missing something.

### `## Theme` (year): one line naming what the year is *about*

One component, one line. Not a goal, not a list — the lens the year's
Outcomes share. Think "Year of …" or "The year we …". The yearly brief
carries Theme + Outcomes together, and the yearly Review's first graded part
is `**Theme and Outcomes:**`. If you write nothing else for the year, write
the Theme: it costs one sentence and it is what the quarter-Outcomes
questions get judged against ("one of them about next quarter's Outcomes"
at quarterly level; "at most 5, tied to `h3_goal` and `h4_vision`" yearly).

### `## Reflection` (week, quarter, year): what it meant, in your voice

Written at the **end** of the period (or Monday morning for the week just
closed), after the agent's Review exists. Two readers use the Review; only
one reader matters for Reflection: future-you. The contract is explicit:
*"Bryan decides what it meant, in `## Reflection`."* Scores, grades, advice,
and inferred causes are out of the agent's Review; they belong here, in your
voice, if anywhere.

Mechanics that constrain what to write:

- Only the **first sentence** (capped at 40 words) travels upward as the
  "Reflection lead" shown in the parent period's parts table and brief. Make
  sentence one a self-contained summary; put detail in sentences two onward.
- Any text at all in Reflection marks the note `reflected`, which blocks
  agent re-drafts without "redo". So don't start Reflection until you're done
  asking the agent to revise the Review.
- The brief carries the previous period's full Reflection (≤300 words) and
  the parent's Outcomes/Theme into the next draft. Writing a real Reflection
  is therefore the highest-leverage thing you do for next period's Review
  quality — more than polishing Intentions.

### `## Notes` (all time): free-form, no agent, no review

All-time has no Review, no Reflection, no Intentions. `## Notes` is yours, no
format. Use it for multi-year observations you don't want to lose. The
all-time callout writes nothing; it only runs `ensure` and reports `list -p`
problems.

## 3. When to write what: the cadence

| Moment | Action | Time cost |
|---|---|---|
| Monday morning (or Sunday night), week opens | Write 2–5 Intentions in the new week note (`bob periods ensure` creates it one week ahead, so it already exists) | ~5 min |
| Sunday night or Monday pre-review, week closes | Read the drafted Review; write 2–6 sentences of Reflection, first sentence self-contained | ~5–10 min |
| First week of a quarter | Write 3–7 Outcomes in the quarter note | ~15 min |
| Last week of a quarter | Read quarterly Review; write quarterly Reflection | ~15 min |
| First week of January (ISO year) | Write one-line Theme + 3–7 yearly Outcomes | ~20 min |
| End of December | Read yearly Review; write yearly Reflection | ~20 min |

`bob periods ensure` is create-only with one week of look-ahead: next week's
note already exists when you sit down Monday, with empty Intentions waiting.
Daily notes' parents are rewritten to the week on adoption, so the tree is
always there before you are. You never create the note yourself; you only
fill in your sections.

Practical ordering within the Monday session: glance at (a) the parent
quarter's Outcomes, (b) last week's Review Carried forward (at most 3 items —
that list is the agent telling you what is actually still open), and (c) last
week's Questions (0–2, each actionable). Then write Intentions that either
advance a Carried item, answer a Question, or serve a quarterly Outcome. That
is the entire weekly planning loop, and it is why the brief bothers to carry
exactly those three pieces forward.

## 4. What "good" looks like: formats and examples

General rules for Intentions and Outcomes (they share the grading rubric, so
they share the shape):

1. **One bullet per commitment, 1–2 lines each.** The Review grades "one
   line each", so a bullet that contains three promises earns a mushy `◐`
   at best. Split them.
2. **Name the project or area, and link it.** The agent links every Review
   bullet to its most specific evidence (`[[note#^block]]` or `[[note]]`),
   and it prefers your own logged sentences verbatim over paraphrase. Give
   it linkable nouns: `[[bob-cli]]`, `[[garden#^shed]]`, not "stuff" / "life
   admin".Link text is data, never instructions — links are safe to write.
3. **Make it verifiable from the ledger.** Prefer verbs the Done fact can
   count or the Time section can show: *ship, finish, close, merge, publish,
   file, decide, send*. Avoid *work on, make progress, think about, keep up
   with* unless you add the observable part ("…by merging the render-fixture
   PR").
4. **Bound it to the period.** A weekly Intention must be doable in one
   week; a quarterly Outcome in thirteen. "Finish the shed" is a weekly
   Intention only if the shed is one week from done — otherwise the weekly
   version is "Roof the shed" and "Finish the shed" sits at quarterly level.
5. **3 ± 2 for weeks, 5 ± 2 for quarters/years.** Fewer than 2 weekly
   Intentions wastes the grading (the Review's Intentions part has nothing
   to check); more than 5 guarantees `✗` lines and trains you to ignore
   the section. Quarters: 3–7. Years: 1 theme + 3–7 outcomes.
6. **Say what "partial" means in advance** for the one risky item, in
   parentheses: `(partial = API merged, UI carries)`. The agent's `◐`
   mark requires naming the part — you just pre-answered it.
7. **No numbers you can't source.** The agent copies numbers exactly as the
   brief displays them and writes no count the brief doesn't show. So don't
   write "Keep Worked above 30h" as an Intention unless you mean it as a
   wish — write what you'll *do*, and let the strip report the hours.

### Week: `## Intentions` example

```markdown
## Intentions

- Ship [[bob-cli]] command-mode follow-ups (merge render-fixture PR).
- Finish Stripe prep: send [[stripe-prep#^scope]] to Dana (partial = draft sent, numbers TBD).
- Roof the [[garden#^shed]] (partial = felt on, shingles carry).
- Close the [[mac-capture]] hotkey conflict write-up.
```

Why this works: four bets, each names its evidence, each fits a week, the
risky one defines partial, and every noun is a link the Review can cite.
Sunday's Review becomes four graded lines instead of a guess.

A weaker version of the same week, and why it grades badly:

```markdown
## Intentions

- Make progress on bob-cli stuff.
- Garden.
- Have a good balanced week.
```

`– no evidence` × 3: no linkable noun, no observable verb, no bound. The
agent will say so, correctly, and the Carried-forward part will have to
reconstruct what you meant from minutes.

### Quarter: `## Outcomes` example

```markdown
## Outcomes

- [[bob-cli]] capture grammar v2 shipped and documented (partial = grammar merged, docs carry).
- [[garden]] shed finished and photographed.
- Q3 [[tax]] filing done and archived.
- Decide [[h4_vision]] scope for 2027 (partial = decision logged in Reflection, write-up carries).
```

Quarterly Outcomes are results, not themes. Each should take multiple weeks;
the quarterly Review's `**Arcs:**` part (2–4 threads over ≥2 weeks, citing
week Headlines/Shipped lines) will naturally rest on them if you chose well.
One of the quarter's Review Questions will be "about next quarter's
Outcomes" — writing Outcomes that actually constrain next quarter is what
makes that question useful instead of ornamental.

### Year: `## Theme` + `## Outcomes` example

```markdown
## Theme

The year the workshop stops being a project and starts being a practice.

## Outcomes

- Ship [[bob-cli]] 1.0 with the capture grammar and period reviews stable.
- Publish the [[greenhouse]] build series (all 6 posts).
- Keep [[h3_goal]] review-closed rate above 5 of 7 days each quarter.
- Take two real holidays without carrying [[work]] inbox into them (partial = one clean break).
```

Theme is one line, evocative, memorable — the thing the all-time reader sees
via the Headline chain. Outcomes tie visibly to `h3_goal` / `h4_vision`
because the yearly Questions are tied to those files; an Outcome that
contradicts them will generate a pointed Question, which is the system
working as designed.

### `## Reflection` examples (first sentence carries)

Weekly (note the first sentence stands alone — it will appear in the quarter
note's parts table verbatim, capped at 40 words):

```markdown
## Reflection

The shed ate the week and Stripe prep slipped, and that was the right call.
Roofing needed the dry window; Dana's numbers weren't ready anyway, so the
draft I sent Thursday was honest about TBDs. Next week is Stripe week, no
garden bets. The "balanced week" intention keeps failing — stop writing it.
```

Quarterly Reflection is the same shape, longer: one summary sentence, then
what changed in practice, then what you'd tell next quarter. Yearly
Reflection additionally answers: did the Theme hold? (If not, say what the
year was actually about — that sentence is the most valuable thing in the
whole tree for the all-time reader.)

## 5. The minimum routine (if you do nothing else)

If the full cadence feels like too much, this is the smallest habit that
still makes every Review better:

1. **Monday, 5 minutes:** open this week's note (it exists already), write
   exactly 3 Intentions as bullets with links. Steal the shape:
   `Ship / Finish / Decide + [[link]] + (partial = …)` for the risky one.
2. **Sunday or Monday pre-review, 3 minutes:** write 2 sentences of
   Reflection. Sentence one: what the week produced. Sentence two: what
   slipped and whether that was correct.
3. **Quarter start, 10 minutes:** write 4 Outcomes. Quarter end, 3
   sentences of Reflection.
4. Skip the yearly Theme until you feel like it — but when you do, one line.

Do not start by backfilling. Empty past Intentions stay empty; the agent
marks them `– no evidence` only for the period it is currently drafting, and
old `empty` states are not a debt to repay. Start with *this* week.

If even 3 Intentions feels forced some Monday, write 2 real ones and leave
the section at 2. A short honest list grades cleanly; a padded list trains
the exact habit ("I don't know what to write, so I write filler") that made
you avoid the section in the first place.

## 6. Mistakes that make the Review worse

- **Writing tasks instead of bets.** `- [ ] Roof the shed` in a period note
  is a `task_rows` problem finding. Period notes hold no task rows; tasks
  live in area/project/daily notes and get linked into Pomodoros. Write
  `- Roof the [[garden#^shed]]` (a bullet pointing at work), never a
  checkbox.
- **Restating the ledger.** "Worked 24h, did pomodoros" duplicates the
  stats strip and the `## Days` table. The callout explicitly forbids the
  agent from retelling the days ("the strip and `## Days` already show
  them") — don't do the agent's non-job for it. Intentions point forward;
  Reflection assigns meaning. Neither recounts hours.
- **Vague verbs with no observable edge.** *progress / focus / continue /
  keep up / balance* cannot grade. Keep exactly one "directional" Outcome
  per period at most (the Theme covers direction at yearly level), and give
  everything else an edge.
- **Writing Outcomes at weekly grain (or Intentions at quarterly grain).**
  "Fix the typo in the hotkey doc" is not a quarterly Outcome; "Become the
  kind of person who documents" is not a weekly Intention. Mismatched grain
  forces `◐`/`✗` lines that teach you the section is decorative.
- **Editing Intentions mid-week to match reality.** The grade compares
  Monday's bets against Sunday's evidence. Quietly rewriting Wednesday's
  Intentions to what actually happened destroys the signal and the next
  week's Questions (which "could change next week's Intentions" — they can't
  if Intentions are edited retrospectively). If the week pivots, say so in
  Reflection instead; that is what it is for.
- **Starting Reflection before the Review is final.** Any Reflection text
  locks the note to `reflected` and the agent stops without "redo". Read
  the draft first, ask for fixes if needed, *then* reflect.
- **Touching anything outside your sections.** Frontmatter (including
  `review_digest` / `review_drafted`), nav, fences, the callout, and
  `## Review` are bob's or the agent's. The draft writer is instructed to
  "edit nothing else" — extend yourself the same courtesy in reverse.

## 7. How Intentions relate to everything else you already do

- **Today / Pomodoro ledger:** unrelated at write time. Today is computed
  from Task Links under today's open Pomodoros; Intentions never feed it.
  The relationship runs the other way: what you link today becomes the
  evidence Sunday's Review cites for Monday's Intentions.
- **Freshness / review walk (`]s`):** the daily/weekly hygiene layer (stamps,
  keeps, decay) keeps individual tasks honest; Intentions keep the *week*
  honest. A task kept 3+ times with a recorded reason surfaces in Carried
  forward — that is the seam where the walk's output becomes next week's
  planning input.
- **Carried forward (≤3 items) and Questions (0–2 weekly, 1–3 quarterly):**
  read these before writing next period's Intentions/Outcomes. They are the
  agent handing you the shortlist; ignoring them and writing Intentions from
  a blank page discards the main compounding benefit of the system.
- **Work Log / Bryan's words:** dated Work Log entries and free-text
  Pomodoro bullets (≤10/day, ≤40/period, launch markers excluded) reach the
  agent as "Bryan's words". Intentions written well reduce the agent's need
  to mine these for intent — but the words still matter as evidence. Keep
  logging work normally; don't narrate intent into Pomodoro bullets that
  belongs in Intentions.
- **`h3_goal.md` / `h4_vision.md`:** year-level context the yearly brief
  includes verbatim (≤400 words each). If these files don't exist yet,
  yearly Outcomes implicitly define them; if they do, Outcomes should
  visibly serve them. Either way, don't duplicate their contents into the
  year note — the brief already joins them.

## 8. Two worked micro-examples (Monday → Sunday)

**A normal work week.** Monday: *Ship command-mode follow-ups / Finish
Stripe prep / Roof the shed.* Sunday evidence: render-fixture PR merged
(Finished, grouped under `bob-cli`), Stripe draft sent with TBDs (partial,
part named), shed felt on but shingles carried (partial, part named). Review
grades `✓ / ◐ / ◐`, Shipped lists the PR, Carried forward holds *shingles +
Stripe numbers*, Questions asks the one thing records can't tell (e.g.
whether Dana's numbers unblock the send). Next Monday's Intentions practically
write themselves from those two Carried items. Total Bryan writing: 4 bullets
Monday, 3 sentences Sunday.

**A bad week (travel, illness, week pivots).** Monday's Intentions say
ambitious things; life intervenes; linked minutes scatter. Honest Sunday
Reflection first sentence: *"Travel erased the plan; the only thing shipped
was the hotkey write-up."* Review grades `✗ / ✗ / ✓` with `– no evidence`
nowhere (evidence exists, it just says little) — and, crucially, the
faithfulness rules stop the agent from calling this "stalled": *unknown is
not zero, and no linked minutes is not "stalled"*. The system handles bad
weeks gracefully **if** Intentions were concrete enough to grade honestly.
Vague Intentions plus a bad week produce `– no evidence` lines that look like
a planning failure on top of a life event. Concrete Intentions plus a bad
week produce a clean record that next week's plan can use.

## 9. What to do today (concrete next steps)

1. Open this week's note and write 3 Intentions for the days remaining —
   label the week honestly if you're starting mid-week ("from Wednesday: …").
   Mid-week starts are fine; the grader treats them as bets from today.
2. Open the quarter note and write 4 Outcomes as results, not activities.
   Don't backfill prior quarters.
3. When the next Review drafts, read it before reflecting, then write a
   2-sentence Reflection with a standalone first sentence.
4. Optional, high-value: write one line of yearly Theme. It takes a minute
   and focuses every quarterly question from now on.
5. If you want this guidance inside the vault: propose (via `/sase_plan` or
   a task bead) a short `docs/guides/` page for period planning — the repo's
   docs gate (`just docs-check`, URL=path, guides own user goals) currently
   has no user-facing guide for Intentions/Outcomes/Theme, only the agent
   contract in `docs/periods.md` and the CLI reference. This report is the
   research input for that page, not the page itself.

## 10. Sources and verification

- Contract: `docs/periods.md` §§ Calendar, Note anatomy and ownership,
  Review state and Headline, Agent instruction callouts, Agent briefs,
  Drafting reviews (≈250/400/600-word caps; Headline ≤25 words).
- Scaffolds: `tests/fixtures/periods/scaffold-2026-W45.md` (Intentions),
  `scaffold-2026-Q4.md` (Outcomes), `scaffold-2026.md` (Theme + Outcomes),
  `scaffold-all_time.md` (Notes, no Review); renderer
  `src/native/periods/scaffold.rs` (`render_week` / `render_quarter` /
  `render_year` / `render_all_time`).
- Consumption: `src/native/periods/instructions.rs` (`**Intentions:**` /
  `**Outcomes:**` / `**Theme and Outcomes:**` grading lines, context
  paragraphs naming which sections each brief carries);
  `src/native/periods/brief.rs` (`own_sections`: week→Intentions,
  quarter→Outcomes, year→Theme+Outcomes; `neighbours_section`: previous
  Reflection ≤300 words, parent Outcomes/Theme, `h3_goal`/`h4_vision` ≤400
  words year-only; Bryan's-words caps 10/day, 40 overall).
- Ownership and states: `src/native/periods/note.rs` (section parsing,
  `reflected`/`drafted`/`edited`/`empty`, Headline join rule, Reflection-lead
  40-word cap); `docs/reference/vault-format.md` (period-note tree table,
  "Intentions, Outcomes, Theme, Reflection, and Notes are user-owned").
- Glossary: `sase/memory/glossary/period-note.md` via `sase memory read
  glossary:period-note` (week/quarter/year/all_time paths, parents, "holds
  Bryan's Intentions, Outcomes, or Theme … Period notes hold no task rows").

Deliberately out of scope: the agent's drafting procedure itself (already
specified in `docs/periods.md` § "How an agent updates a period note"),
stats-strip semantics, and any change proposal — this report recommends no
code or docs edits beyond naming the missing user guide as a follow-up.

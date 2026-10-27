# Pomodoro Themes: How Bryan Uses Them vs. Established Best Practices

## Scope and method

Independent research into Bryan's Pomodoro-theme usage: what the `bob themes`
catalog says, what the vault ledger shows, what the theme system means, and how
that compares to established practice (GTD contexts, Cal Newport deep/shallow
work, and time-tracking taxonomy guidance). No peer report was consulted.

Sources inspected live on 2026-10-27 (vault `~/bob`, config
`~/.config/bob/config.yml`, journal `.bob/themes/*.jsonl`):

- `bob themes list -f json` (default and `-a`), `bob plan -f json`,
  `bob stats show -a -f json`, `bob stats metrics`
- `docs/pomodoro-themes.md` (PT1–PT10), `docs/pomodoro-homes.md`,
  `docs/plan.md` budget semantics
- Decisions strands `pomodoro-theme-is-one-component`,
  `theme-hide-is-recent-only`, `theme-hue-is-pin-exempt-area-hash`,
  `theme-prefs-live-in-per-host-journal`, glossary `pomodoro` / `pomodoro-theme`
- Recent daily notes (`2026/202610*.md`, `2026/*.md`) for name spellings and
  composite (`+`) usage
- Web literature on GTD contexts, time-blocking/deep-work categories, and
  time-tracking tag taxonomy

## 1. What themes are (system semantics)

A theme is one `+`-separated component of a ledger entry's ` — NAME` tail,
keyed by collapsed-lowercase normalization; display spelling follows the most
recent authored form. `— BOB + DECKS` is one name with two themes. Unnamed
entries, the `(unnamed)` placeholder, Pomodoro homes, and Obsidian appearance
themes are not themes. The catalog derives from canonical daily notes only,
folded with the per-host journal; `bob themes` is read-only except
hide/unhide/color/rename, which append journal events.

Three semantics matter for every recommendation below:

1. **Hide removes from Recent only.** History, Stats, colors, today's rows, and
   typing are unaffected; using a hidden name never unhomes it. `list` omits
   hidden by default; `-H` / `-a` recover them. Hide is a suggestion filter,
   not deletion.
2. **Hue is pin → exempt → area → hash.** A journal pin wins; a normalized
   `plan.exempt` key is muted (`GTD` by default); a key matching a top-level
   area stem wears that area's hue; otherwise `fnv1a32(key) % 8` over eight
   slots (blue, orange, aqua, yellow, magenta, green, violet, red). Colors are
   stable, not unique — collisions are expected and fixed with pins.
3. **Homes already answer "where".** Pomodoro homes attribute each entry's Task
   Links through area/project ancestry (e.g. chip `dev`, `sase`). Stats carries
   both homes and a theme dimension. Themes therefore do not need to encode
   location, machine, tool, or project — that axis is covered.

Budget context: `plan.max_themes: 5`, `plan.exempt: [GTD]`,
`plan.inventory_labels: [LATER, MISC, NEW FEATURES]`, `strict: false`.

## 2. How Bryan actually uses themes (observed facts)

### 2.1 The catalog at a glance

`bob themes list` on 2026-10-27: **76 known · 5 today · 70 hidden · last
90 days**. The six visible rows:

| Theme | Today | Days used | Entries | Hue |
|---|---|---|---|---|
| GTD | closed | 54 | 142 | muted (exempt) |
| BUILD | open | 30 | 92 | yellow (hash) |
| JOB | open | 20 | 89 | aqua (area) |
| HOME | open | 11 | 11 | violet (hash) |
| FIX | open | 5 | 8 | blue (hash) |
| READ | Oct 25 | 15 | 45 | green (hash) |

Today's ledger carries four open entries (`JOB`, `BUILD`, `FIX`, `HOME`) plus
closed `GTD` review sessions — inside the `max_themes: 5` budget. Recent
`202610*.md` name counts confirm the same core: JOB 89, GTD 86, BUILD 70,
READ 40, SASE 21, HOME 11, FIX 7 in the sampled window.

### 2.2 A long tail, mostly single-use

Of 76 known themes: **38 used on exactly 1 day (50%), 16 on exactly 2 days,
22 on 3+ days**. Twenty-one names (28%) are multiword or punctuated:
`SASE V18`, `SASE-V18`, `SASE.MD`, `FIX-APOLLO`, `RESTART MAC`, `AUDIT MEMORY`,
`FAST TESTS`, `NEW FEATURES`, `MEMORY BEADS`, `SWAP POMS`, `LINKS AND SETUP`,
`MAC AND APOLLO`, `PLAN MEMORY`, `AFTER TUI FIX`, `FIX KILL AND EDIT`, and
others. Each is a distinct key that occupies a hue slot and a Recent row until
hidden.

Duplicate-cluster examples still in history:

- **FIX cluster:** `FIX` (visible, 5d/8) vs `FIXES` (1d/5, hidden),
  `FIX-APOLLO` (1d/1, hidden), `FIX KILL AND EDIT` (1d/1), `AFTER TUI FIX`
  (1d/2). Ledger sampling shows `FIXES` was the Sept workhorse (multiple
  25–60m sessions) before `FIX` took over.
- **SASE cluster:** `SASE` (14d/33, hidden but pinned aqua) vs `SASE V18`
  (6d/12), `SASE V19` (2d/2), `SASE-V18` (1d/1), `SASE.MD` (1d/3),
  `SASE AGENTS` (1d/1). Same project, five spellings, three hues.
- **Ephemera:** `SHIT` (13d/16 — a real repeat, not a typo), `LOVE` (1d/1),
  `FIRE` (1d/1), `BETS`, `GATES`, `PAGER`, `TOOL`/`TOOLS`, `MUSE`, `JITUX`,
  `HERMES`, `ATHENA`, `DEV`, `REMOTE`, `RELAUNCH`, `FINAL`, `QUEUE`,
  `SERVICE`, `SUDO`, `VERIFY`, `USAGE`, `EMAIL`, `SETUP`, `STARTUP`,
  `SCREENSHOT`/`SCREENSHOTS`, `RESTARTS`/`RESTART MAC`, `SUBTABS`,
  `PROJECTS`, `CAPTURE`, `RELEASE`, `SCHEDULE`, `BEADS`, `ARTIFACTS`.
- **Machine/place names as themes:** `ATHENA`, `DEV`, `MAC AND APOLLO`,
  `REMOTE` — all hidden now, but each still a catalog row with a hue.

### 2.3 Composites (`+`) are rare and mostly GTD-paired

Sampling finds composites uncommon: `BUILD + STARTUP`, `SWAP POMS + FIX KILL
AND EDIT`, `GTD + ATHENA`, `GTD + FINAL`, `GTD + BUILD`, `READ + RESEARCH`,
`PROJECTS + BUGS`. The `GTD + X` pattern pairs the exempt review bucket with a
work theme inside one session — legal, but it doubles theme counts for that
entry against `max_themes` semantics and splits one session across two Stats
rows.

### 2.4 Hide discipline is aggressive and recent; renames show consolidation

The journal tells the story. On 2026-10-26 apollo hid ~70 keys in one batch
(same timestamp), and kellys-mbp unhid `JOB` on 10-27. Current pins: `SASE`
aqua, `RESEARCH` aqua, `DECKS` violet — all three keys currently hidden, so
three pins buy zero visible differentiation. Recent renames show deliberate
consolidation: `HACK→HOME`, `PYPI→READ`, `BOB→BUILD`, `BLOG→WRITE`,
`VIBE→BUILD`, `WRITE→JOB`. The direction is unmistakable: toward a small
canonical set, with the renames doing the merging work that hide alone cannot
(hide never moves history; rename rewrites tails and moves explicit state).

### 2.5 Hue collisions are structural, not accidental

With 8 slots and 76 keys, hash collisions dominate: e.g. yellow/hash holds
`BUILD, SHIT, HERMES, CLEANUP, REMOTE, …`; violet/hash holds `HOME, MEMORY,
ATHENA, SASE V18, LISTEN, …`; magenta/hash holds ten keys including
`FIX-APOLLO, FIXES, SASE.MD`. The live hint list confirms the visible cost:
`BUILD`/`CLEANUP` share yellow, `HOME`/`MEMORY` share violet. Only two visible
themes have meaningful hues: `JOB` aqua (area `job.md` → aqua) and `GTD`
muted (exempt). `DEV` blue is area-derived but `DEV` itself is hidden.
Everything visible except JOB is hash — stable, but semantically empty.

### 2.6 Homes vs. themes: the "where" leaks into the "what"

Area hues in the vault: `dev` blue, `job` aqua, `love` yellow, `body` green,
`cash` magenta, `gtd` orange (moot — exempt mutes it). Today's `JOB` entry
forecasts home `dev` while wearing area-aqua from the `job` stem: the system
working as designed, but also proof that theme and home are independent axes.
Past themes such as `ATHENA` (machine), `DEV` (area name reused as theme),
`REMOTE` (place), `TOOL`/`PAGER`/`MUSE` (tools) duplicate the home axis inside
the theme axis — the exact redundancy the homes design was built to remove.

## 3. What best practice says

1. **GTD contexts: few, stable, constraint-based.** Allen's contexts are the
   tool/place/situation required to act (`@Calls, @Computer, @Errands, @Home,
   @Agendas, @Read/Review`), plus Areas of Focus as a separate higher list.
   Guidance converges on starting with a handful of basic contexts and adding
   only when a list gets unwieldy. Contexts are never project names, version
   strings, or one-off task titles — those live one level down.
2. **Deep-work / time-blocking categories: 3–4 work types.** Newport's
   taxonomy is deep vs. shallow (plus admin/distraction); the popular 3-3-3
   gloss is one deep block, shorter tasks, maintenance. The point is a small
   set of *modes of working*, protected by ritual, not a per-project label.
3. **Time-tracking taxonomy: 8–12 core tags, one per entry, merge synonyms.**
   Toggl/Teamwork guidance: define tags to match how you want to *report*,
   apply them consistently, keep the starter set tiny (8–12), prefer one tag
   per entry, merge duplicates (`FIX`/`FIXES`), and treat single-use tags as
   smell (WordPress-tag lore: a tag with <3 posts probably shouldn't exist).
   Multiword sentence-tags and punctuation variants (`SASE V18` vs `SASE-V18`
   vs `SASE.MD`) are the canonical proliferation failure.
4. **Miller's-law pressure: 5–9 live options.** Capture menus show at most 5
   Recent rows on empty query, 12 on typed query; `max_themes: 5` already
   encodes this. A visible set of ~5–6 plus one exempt bucket is exactly what
   the UI and the budget were built for.

Bryan's visible six (GTD + five work themes) already match all four sources.
The 70-key tail is where practice diverges: project codes, version suffixes,
machine names, tools, joke/one-off names, and singular/plural splits.

## 4. Assessment

Bryan's *steady state* is good — arguably exemplary. Six visible themes, one
exempt review bucket, four-to-five open entries a day inside budget, aggressive
hide hygiene, and renames actively merging history toward the canonical set.
The system semantics support this: hide keeps history/Stats intact while
cleaning suggestions, rename rewrites tails in one revertable commit, hues
render from Bob so clients never drift.

The risks are all in the tail and the defaults that let it regrow:

- Single-use sentence themes cost a hue slot, a Recent filter-out, a Stats
  row, and a future merge — for one session's worth of signal.
- Punctuation/version variants of one concept (`SASE ×5`, `FIX ×4`) split
  Stats and defeat recency ranking until someone renames them.
- Pins on hidden keys (`SASE`, `RESEARCH`, `DECKS`) spend the scarcest hue
  resource (explicit pins) where no menu can benefit.
- `GTD + X` composites quietly double-count sessions across Stats rows.
- `strict: false` plus a free-text capture grammar means nothing stops the
  next 38 singletons; only monthly hygiene does.

## 5. Ranked recommendations

Ordered by expected signal-per-effort. Each names the concrete `bob` action.

1. **Freeze the canonical six and declare the tail archived.** Keep `GTD`
   (exempt) + `BUILD, JOB, HOME, FIX, READ` as the closed vocabulary for new
   sessions. Everything hidden stays hidden — history and Stats are untouched
   by design, so no cleanup commit is needed. *Effort: zero; value: stops
   well-meaning resurrection of `SASE V19`-style variants.*
2. **Finish the synonym merges with `bob themes rename --merge`, then stop
   renaming.** Concretely: `FIXES→FIX`, the `SASE V18` / `SASE-V18` /
   `SASE.MD` / `SASE AGENTS` cluster → `SASE` or `BUILD` (decide once whether
   SASE-the-project deserves a live theme or lives under `BUILD`; the ledger
   suggests `BUILD` already absorbed `BOB`/`VIBE`), `SCREENSHOT→SCREENSHOTS`
   or vice versa, `TOOL→TOOLS`, `RESTARTS`/`RESTART MAC` → one or none. Preview
   each (`-d`), one commit each, revert via `git revert`. After the pass,
   treat rename as closed — every rename is a vault-wide rewrite and its
   `renamed_reappeared` guard only reports, never heals, muscle memory.
3. **Adopt a one-line naming rule and put it in the capture habit, not the
   config:** single `ALL-CAPS` token, no spaces, no punctuation, no version
   suffix, no machine/tool/place names. `SASE V18` → `SASE`; `FIX-APOLLO` →
   `FIX`; `MAC AND APOLLO` → never a theme (homes cover it). Composites
   (`A + B`) only for genuinely dual sessions, not `GTD + X` pairing — log
   review work under `GTD` and start a new entry for the work. This single rule
   prevents ~90% of observed tail growth.
4. **Repoint the three wasted pins at the visible set.** Unpin or drop pins on
   hidden `SASE`, `RESEARCH`, `DECKS` (`bob themes color NAME auto`), then pin
   the visible hash-hued themes into distinct slots so the two live collision
   hints (`BUILD`/`CLEANUP`, `HOME`/`MEMORY`) resolve durably: e.g. keep `JOB`
   aqua (area, free), `GTD` muted (exempt, free), and pin `BUILD`, `HOME`,
   `FIX`, `READ` to four distinct non-aqua slots. Least-used-slot suggestion
   from `hints[].suggest` is the tiebreak. Revisit only when a hint reappears
   on two *visible* themes.
5. **Keep machine/place/tool concepts out of themes permanently.** `ATHENA`,
   `DEV`, `REMOTE`, `TOOL`, `PAGER`, `MUSE` belong to homes/link targets, not
   the theme axis. If device-specific reporting is ever wanted, it comes from
   homes or `bob stats`, never a new theme. This is the GTD-contexts rule
   applied to Bob: themes are modes/areas of work; homes are where the work
   lives.
6. **Decide `READ`'s scope once.** `READ` (15d/45, green) is the healthiest
   non-work theme: daily, high-entry, distinct hue. Either bless it as the
   sixth canonical theme (input/learning mode, Newport-shallow counterpart to
   `BUILD` deep work) or fold reading sessions into `GTD` review — but stop
   halfway: its current half-life (last used Oct 25, visible, unpinned) is fine
   only if the choice is explicit, since `READ` vs `RESEARCH` (hidden, pinned
   aqua, 8d/19) is exactly the kind of near-synonym pair that regrows tails.
   Recommendation: keep `READ`, unpin and leave hidden `RESEARCH`, and let
   `READ + RESEARCH`-style composites die.
7. **Leave `strict: false`; add a monthly 5-minute hygiene pass instead.**
   `strict: true` would refuse over-budget `#NAME` captures — effective but
   hostile at capture time, the worst moment for friction. The observed
   batch-hide + occasional-rename rhythm already works; formalize it: monthly,
   `bob themes list -a`, hide every 1-day theme older than 30 days, merge any
   visible collision hint, audit pins. Calendar cost ~5 minutes; avoids both
   regrowth and capture-time refusals.
8. **Clarify `inventory_labels` vs. hidden themes.** `LATER`, `MISC`,
   `NEW FEATURES` are plan-level storage buckets that never count as themes,
   yet `MISC`/`LATER`/`NEW FEATURES` also exist as hidden theme keys from past
   sessions. Harmless today (hidden ≠ counted), but one future unhide or
   rename could collide the two namespaces. Recommendation: document in config
   comment that inventory labels must never be unhidden as themes, or rename
   the labels (`INBOX`-style) so the namespaces cannot overlap.
9. **Do not create area notes to chase hues.** It is tempting to give `BUILD`
   or `READ` an area note so its hue becomes "meaningful" — resist. Area notes
   are a vault ontology commitment (parents, Ready caps, review tiers), not a
   color picker. Pins are the hue mechanism for non-area themes; areas are for
   responsibilities that own tasks.
10. **Let `SHIT` lie.** Thirteen days and sixteen entries make it a real
    historical signal (frustration/vent sessions), and hide already removes it
    from suggestions while preserving Stats honesty. Renaming it would falsify
    history; deleting is impossible by design. If shared reports ever expose
    it, rename then — not before.

## 6. What was not recommended (and why)

- **Deleting or squashing history.** The system deliberately offers no delete;
  Stats and old daily notes keep every spelling. Hide + merge is the complete
  toolkit — anything stronger would rewrite the past to flatter the present.
- **`strict: true`.** Capture-time refusal trades a monthly 5-minute review
  for daily friction at the exact moment speed matters. Revisit only if
  singleton creation exceeds ~5/month after the naming rule beds in.
- **More exempt keys.** `GTD` earns exemption as the daily review ritual with
  54 days and 142 entries. No other theme has that profile; exempting `READ`
  or `HOME` would just mute hues Bryan actually uses for scanning.
- **A `WRITE` revival.** The journal shows `BLOG→WRITE→JOB` — the system
  already deliberated and folded writing into `JOB`. Reopening it needs new
  evidence (e.g. sustained `JOB`-budget overflow attributable to writing), not
  nostalgia.

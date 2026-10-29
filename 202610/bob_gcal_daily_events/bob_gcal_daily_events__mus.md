# Google Calendar → Obsidian sync (`bob gcal`): research & recommendation

Researcher: **mus** · 2026-10-29 · swarm report (`__mus`)

Question: should bob-cli gain a `bob gcal` command that syncs Google
Calendar events into the vault as tasks — rendered in a new `## Events`
section above `## Pomodoros` in the daily file, with an auto-created `MEET`
pomodoro linking them, `[root:: meet]` as the default root parent, a
modernized `meet.md` area note, and easy auth?

Short answer: **yes, with adjustments.** The core idea is sound and fits
Bob's architecture, but three parts of the proposal as stated need to
change: (1) do not build Calendar OAuth — shell out to the already
installed and authenticated `gog` CLI; (2) do not blindly link every event
task under an auto-created `MEET` pomodoro — sticky-lane and plan-budget
mechanics make that destructive on busy days; (3) per-event root override
belongs in a Calendar-editable description footer (with invisible
`extendedProperties.private` as the power-user path), not in a new UI.

Recommended solution is in §8. Critiques and adjustments are marked
**Adjustment** inline.

---

## 1. What I verified in the repo and vault

- **Integration precedent is `bob gkeep`, not a built-in client.**
  `src/native/gkeep/` (~16k lines) pins the pattern: `cli.rs` owns the
  whole surface, then `login.rs` / `doctor.rs` / `list.rs` / `pull.rs`
  implement; `config.rs` reads `~/.config/bob/config.yml`; `imports/` and
  `ledger.rs` keep vault-side import receipts; writes are atomic,
  parse-verified, committed, and only then is the source mutated
  (content-guarded archive). `docs/gkeep.md` is the contract doc. Any
  `bob gcal` should copy this skeleton file-for-file — it is the
  codebase's settled answer to "how do integrations work," including the
  `BOB_GKEEP_ADAPTER` test hook, exit codes (0 ok / 1 runtime / 2
  setup-usage), and `-d/--dry-run`, `-n/--no-archive`, `-C/--no-commit`,
  `-q/--quiet`, `-f human|json` flags.
- **Calendar differs from Keep in one decisive way: there is an official
  read API and an authenticated client already on this machine.**
  Keep has no API, so `bob gkeep` shells out to a pinned-Python `gkeepapi`
  adapter via `uv run --script`. Calendar has a stable v3 API, and
  `/home/bryan/bin/gog` (v0.44.0, `gog calendar`) is installed with auth
  configured (`~/.config/gogcli/config.json`). I confirmed `gog calendar
  events` supports `--today/--tomorrow/--week/--from/--to`, `--all`,
  `--cal`, `-j/--json`, `--fields`, `--sort start`, `--timezone`,
  `private-prop-filter`, and a lossless `raw` dump. Nothing in `src/`,
  `Cargo.toml`, or the `justfile` references `gog` yet, so this would be
  a new subprocess dependency — but one Bryan already trusts (there is a
  `sase_gmail` skill built on `gog`).
- **`[root:: meet]` + `meet.md` modernization is coherent with homes.**
  `docs/pomodoro-homes.md` R1/R11: a set `[root:: X]` field starts the
  home walk at X instead of the linked note. `src/native/task_root.rs` is
  the canonical parser. Daily-note tasks already use this pattern:
  today's `^gtd` row carries `[root:: gtd_daily]`. Event tasks residing
  in the daily note with `[root:: meet]` are exactly parallel — legal,
  rendered, and Stats-bucketed under `meet` with no new machinery.
- **`meet.md` today is NOT an area note.** Frontmatter: `parent:
  [[work]]`, no `type: [[area]]`, plus `generated_from_zorg` provenance
  and years of legacy meeting notes. Compare a real area (`cash.md`):
  `parent: "[[area]]"`, `type: "[[area]]"`, `done_tasks` pointer, `##
  Tasks` section. Modernization = frontmatter change + `## Tasks`
  section + `done_tasks` pointer; the legacy body stays untouched.
- **The `MEET`-pomodoro auto-link is where the proposal collides with
  settled mechanics.** Three records bite:
  - *Today is read from the ledger* (`decisions:today-is-read-from-the-ledger`):
    Task Links under today's **open** Pomodoros *are* Today. Auto-linking
    events is therefore a real planning act, not decoration.
  - *Sticky lanes* (`decisions:task-lanes-are-sticky`): linking a Ready
    task raises it to Next **permanently** — removing the link never
    lowers it. A 6-meeting day permanently parks 6 tasks in Next unless
    someone releases or closes each one.
  - *Plan budget* (`plan.max_themes` 3, `max_links` 13 in
    `~/.config/bob/config.yml`): one `MEET` name costs one theme slot;
    every linked event costs a link slot. A busy day can nearly fill the
    link budget with meetings alone.
- **CLI rules** (`cli_rules.md`, read via audited read): Integrations
  section placement; alphabetical subcommands; every public long option
  gets a short alias; excellent `-h`; bare group may default **only** to
  a flag-only read-only member (`gkeep` bare→`list` is the model);
  nothing under `bob capture`. All satisfiable.

## 2. Critique: is this a good idea?

Yes — with the adjustments below, it is a *good* Bob feature rather than
a gimmick, for three reasons:

1. **It closes the "day starts elsewhere" gap.** Today Bryan's day plan
   lives in two places: Google Calendar (commitments) and the vault
   (intentions). A morning `pull` that materializes commitments as tasks
   makes the ledger the single day-plan, which is exactly what the Today
   and plan-budget machinery wants to read.
2. **It reuses four settled patterns instead of inventing any.** gkeep's
   command skeleton, `^gtd`'s daily-residence-plus-`[root::]` pattern,
   `MEET` as one more ledger theme, `gog` as subprocess backend. No new
   daemon, no new syntax, no new status.
3. **Meetings are the one task class with ground-truth start/end times.**
   Time ranges (`1000–1030`) render beautifully and sort naturally, and
   schedule data is structured — no LLM parsing needed.

The risks are also real: lane pollution (§1), budget pressure (§1),
duplication churn on re-pull (solved by stable ids, §4), and destroying
`meet.md` history (solved by additive-only modernization, §6). None is a
veto; all are handled in the recommendation.

## 3. Command surface: `bob gcal`

**Adjustment: mirror `bob gkeep` exactly, minus archive.** Keep has
inbox-drain semantics (write → verify → commit → archive in Keep).
Calendar is a *sync*, not a drain: the source of truth stays in Google,
so there is no archive step and `pull` must be idempotent and
update-in-place. Proposed tree (alphabetical per CLI rules):

| Subcommand | Meaning |
|---|---|
| `bob gcal` (bare) | Defaults to `list`, flag-only read-only — same rule `gkeep` uses |
| `doctor` | Config, `gog` presence/auth, calendar reachability, daily-note + `meet` area checks |
| `list` | Accepted events for a date side-by-side with vault Events state: `new / in-sync / updated / cancelled / declined-skipped` |
| `login` | Verify-or-establish `gog` auth; never handles passwords/tokens directly (§5) |
| `pull` | Idempotent sync: write `## Events` tasks + ensure one `MEET` pomodoro (§4) |
| `prune` | Fold cancelled/declined-then-removed events into canceled tasks (explicit, previewed; never part of bare `pull` deletion) |

`pull` flags (all with short aliases): `-d/--dry-run`, `-C/--no-commit`,
`-q/--quiet`, `-f/--format human|json`, `--date YYYY-MM-DD` (default:
today), `--cal` repeatable calendar filter (default: primary, or config
`calendars:`), `--no-meet` (skip MEET pomodoro creation), `-P/--parent`
(default root override, cf. `gkeep pull -P`), `--include-declined`,
`--include-all-day`. No destructive flags without preview: anything that
closes or cancels tasks goes through `prune`, never silently inside
`pull`.

`--date` deserves emphasis: the proposal says "that day," but the
implementable version is **`pull` syncs one date, default today**.
Multi-day sync would scatter tasks across daily files and break the
"Events above Pomodoros of *that* day" rendering. Past dates: allowed
(harmless backfill). Future dates: allowed (pre-plan tomorrow) — but the
MEET pomodoro is only created for **today**, since open Pomodoros in a
future daily note are not Today's ledger and would confuse `bob plan`.

## 4. Rendering, identity, and idempotency (the heart of the design)

### 4.1 `## Events` section

New H2 **directly above** `## Pomodoros`, as proposed. `pull` creates it
if missing (same tolerance `capture-pomodoros` shows for a missing
Pomodoros section) and never touches anything outside it. One task per
accepted event, sorted by start time:

```markdown
## Events

- [ ] #task 1000–1030 Team Standup [root:: meet] [scheduled:: 2026-10-30] [id:: gcal_a1b2c3] ^gcal-a1b2c3
    - 📍 Room 4B · 📞 https://meet.google.com/abc-defg-hij · 👥 4
```

Conventions: time range leads the text (scanability, matches vault
`0900-0930` style); `#task` marker; `[root:: meet]` default (§6–7);
`[scheduled:: date]` so schedule-driven Blocked/reconcile logic sees it;
**stable `[id:: gcal_<short>]` + matching `^gcal-<short>` block id**
derived from `iCalUID + recurrence instance` — this is the re-pull join
key. One child bullet holds location / hangout link / attendee count;
never the full attendee list or description (beauty + privacy: calendars
contain other people's emails).

Skipped by default, listed in `list` output only: declined events,
`transparency: transparent` "free" events, `eventType: outOfOffice /
workingLocation / focusTime`, and (unless `--include-all-day`) all-day
events. **Adjustment:** all-day events default to skipped — turning
"Company holiday" into a task is lane spam; make them opt-in.

### 4.2 Update-in-place and cancellation

`pull` is keyed read-modify-write inside `## Events`, mirroring gkeep's
receipt logic with lighter machinery (no archive guard needed):

- Receipts in `.bob/gcal/imports/` (JSONL like gkeep's): `eventId →
  {blockId, etag/updated, lastSeen}`. Re-pull matches by `[id::]` first,
  block id second.
- Changed time/title in Calendar → rewrite the task line **in place**,
  preserving any user-added children (notes Bryan typed under the event
  must survive a re-pull; only bob-owned spans are rewritten).
- Cancelled on Google → task stays put under `pull`; `prune` (explicit,
  previewed) converts it to `- [-]` with a `CANCEL LOG` child ("removed
  from calendar"). `pull` never deletes or cancels user-visible lines by
  itself — the gkeep "never delete from source" conservatism, inverted
  for a sync target.
- RSVP flip to declined → same path as cancelled (surface in `list` as
  `declined`, fold on `prune`).

### 4.3 The `MEET` pomodoro — the part I would change most

Proposal: "auto-create a new pomodoro using the MEET theme with task
links for all events." As specified, this means `- [ ] () — MEET` plus
one `[[#^gcal-…]]` sub-bullet per event. Functionally it works — links
are Today's ledger, homes resolve via `[root:: meet]`, Stats buckets to
meet. But §1's mechanics make unconditional auto-linking wrong on two
counts: **sticky Next promotion** (every linked meeting parks in Next
forever) and **link-budget consumption** (default cap 13).

**Adjustment (recommended): link, but make it safe and reversible.**

1. `pull` ensures **at most one** open `— MEET` pomodoro per day; never
   duplicates, never resurrects a closed or user-renamed one.
2. Links are added for events not already linked; links whose events were
   pruned are removed (removal never lowers lanes — sticky rules stand).
3. Ship `--no-meet` and config `meet_pomodoro: true|false` (default true:
   the proposal's behavior stays the default, one flag away from off).
4. **Do not exempt MEET from the plan budget silently** — but do surface
   the pressure: `pull --dry-run` / `list` should warn when today's links
   would exceed `max_links`. Whether `MEET` joins `plan.exempt` is a
   Bryan decision (it is auto-generated scaffolding, like `PLAN`, which
   is the current sole exempt entry) — I recommend proposing it, not
   assuming it.
5. Past-meeting hygiene is a `prune` option, not `pull` behavior: an
   explicit `--close-past` that checks off event tasks whose end time
   passed (with `[completion:: date]`), so Next doesn't accumulate
   yesterday's standups. Default off until Bryan blesses auto-closing.

## 5. Auth: the easiest part, if we don't build it

**Adjustment: `bob gcal` performs no OAuth of its own. It delegates to
`gog`.** The proposal asks for "easy and intuitive" Calendar auth, and
the trap is reimplementing installed-app OAuth (client secrets, loopback
server, token storage, refresh) when `gog` already did it and Bryan
already authenticated it. Design:

- Backend rule: `bob gcal` spawns `gog calendar events --today -j
  --timezone <tz>` (plus `raw` for lossless extended properties) and
  parses JSON. `gog` owns tokens, refresh, and keyring/file storage.
- `bob gcal login` = guided check: is `gog` on PATH? does `gog auth`
  (or equivalent) show a working account? If yes, print "already logged
  in as X" and verify with a `--fail-empty`-style probe. If no, print
  the exact `gog` command to run and re-probe. No cookie pasting, no
  master tokens — strictly easier than `bob gkeep login`'s TTY-cookie
  exchange, which exists only because Keep has no OAuth.
- `bob gcal doctor` checks, in order: config block present → `gog`
  executable (`BOB_GOG_BIN` override, mirroring `BOB_GKEEP_ADAPTER` as
  the test hook; tests set it to a fixture script) → auth works →
  calendar reachable → target daily note exists/parseable → `meet` area
  resolves. Each failure prints the fix.
- Timezone: reuse `timezone:` from `config.yml` (`America/New_York`);
  pass `--timezone` through so `--today` boundaries match vault days.

If `gog` ever goes away, the subprocess boundary contains the damage:
one module speaks "calendar JSON," and only the spawner changes.

## 6. `[root:: meet]` default and `meet.md` modernization

The proposal's default is right: `[root:: meet]`, resolving to
`~/bob/meet.md`, which becomes a proper area note. Concretely:

```yaml
---
parent: "[[area]]"
type: "[[area]]"
done_tasks: "[[done/meet_done]]"
---
```

plus a `## Tasks` section (placement follows area-note convention, e.g.
`cash.md`). **Additive only**: keep the `generated_from_zorg` provenance
keys if harmless, keep every line of legacy meeting notes, route the
note out of `[[work]]`-parenting deliberately (it becomes top-level;
`[[work]]` keeps a Related link if desired). Verify: homes R1 walk from
any event task hits `type: [[area]]` at `meet` → home = root = `meet`;
no `^prj` exists so project-blocking (`decisions:...`) cannot fasten;
`meet` gets its own Ready cap and Tasks grouping like every area.

## 7. Per-event parent override

Requirement: the Calendar event itself should say which root to use.
Constraints: must be editable from Google Calendar UI (Bryan lives
there), parseable without extra API calls, and invisible-ish.

**Adjustment (recommended): description-footer line, with
`extendedProperties.private` as the precise override.**

- Primary UX: last line of the event description matching
  `bob-root: <route>` (case-insensitive, e.g. `bob-root: sase` or
  `bob-root: bob`). Surfaced by `gog ... --fields` description output —
  no extra fetch. Documented in `docs/gcal.md`; `list -f json` echoes
  the parsed root per event for transparency.
- Power path: `extendedProperties.private.bobRoot = <route>`, settable
  via `gog calendar update` (and filterable via `--private-prop-filter`
  later). Invisible in the UI, survives description edits. Precedence:
  private prop > description footer > `-P/--parent` flag > `meet`
  default. Unresolvable route → warn, fall back to `meet`, never fail
  the pull (a typo'd root must not block the whole day).
- Rejected: overloading `location` (it's real data, rendered in the
  child bullet), hashtags in the title (pollutes the task text and the
  Calendar UI), per-calendar mapping as the *only* mechanism (too coarse
  — one "Work" calendar holds meetings for many roots — though a
  `calendars:` config map is a fine complementary default).

Resolution reuses `parent_notes::resolve_parent` (the same resolver as
`bob ref create -P`, `gkeep pull -P`), so routes, aliases, and error
messages stay consistent across commands.

## 8. Recommended solution (phased)

1. **Backend + `login`/`doctor`.** `gcal/` skeleton mirroring
   `gkeep/` (`cli.rs` first, per repo convention); spawner around `gog
   calendar events -j`; `BOB_GOG_BIN` test hook; config block
   (`calendars:`, `meet_pomodoro:`, `target:` unused — daily file is the
   target). `doctor` as §5.
2. **`list`.** Read-only probe with the new/updated/in-sync/cancelled
   classification and parsed-root echo. This alone is useful on day one.
3. **`pull` for `## Events`.** Receipts, stable ids, update-in-place,
   `-d` preview; no MEET yet. Gate: `just docs-check`, fixture tests
   with a fake `gog`.
4. **MEET pomodoro.** Single-ensure logic, `--no-meet`, budget warning;
   propose (don't assume) the `plan.exempt` question to Bryan.
5. **`meet.md` modernization + `prune` (+ optional `--close-past`).**
   Additive edit; explicit cancel-folding.
6. **Docs + nightly (optional).** `docs/gcal.md` mirroring `docs/gkeep.md`
   (contract, setup order, JSON output, exit codes); register in
   `mkdocs.yml` via `just docs-gen`; consider a `nightly` step limited
   to *today's* pull. Defer two-way sync (creating Calendar events from
   tasks) entirely — unrequested and a different product.

Open questions for Bryan (not blockers): exempt `MEET` from
`plan.max_themes`? auto-close past meetings by default? all-day opt-in
list? primary calendar only, or `--all` with a configured allowlist?

## 9. Sources consulted

Repo: `src/runner.rs` (command table), `src/native/gkeep/{cli,mod}.rs`
(surface pattern), `src/native/task_root.rs`, `docs/pomodoro-homes.md`
(R1/R11/R2), `docs/gkeep.md`, `docs/plan.md` (budgets), vault
`~/bob/meet.md`, `~/bob/2026/20261029.md` (ledger shape),
`~/bob/cash.md` (area-note shape), `~/bob/bob.md` `^sync-gcal-meets`
(the live task this research serves), `~/.config/bob/config.yml`,
`gog calendar --help` / `events --help` (v0.44.0). Memory (audited):
`glossary:pomodoro`, `glossary:pomodoro-theme`, `glossary:task-link`,
`glossary:area-note`; `decisions:today-is-read-from-the-ledger`,
`decisions:task-lanes-are-sticky`,
`decisions:pomodoro-theme-is-one-component`,
`decisions:projects-block-from-prj-line`; `docs.md`, `sase_artifacts.md`,
`cli_rules.md`.

# bob-cli-a0.13 handoff — polish phase done, epic ready for its land agent

Phase `bob-cli-a0.13` (llms.txt, reader tests, final sweep, handoff) is complete.
Epic `bob-cli-a0` stays open for `bob-cli-a0.land`, which triages the open
follow-ups below and closes the epic. Do not close `bob-cli-a0` here.

- Landed commit: `1513a385a691bedbafe13c36de3205e83ce7c7d0`
  (`feat(docs): add llms.txt, reader-testing protocol, and final accessibility fixes`)
- Live site: <https://bobs-org.github.io/> (Zensical build of the landed commit)
- `llms.txt`: <https://bobs-org.github.io/llms.txt> (HTTP 200, five sections)
- Reader verdict: all six tasks pass on both entry points (5/5 first-choice expected
  door each). No fix round needed; none run.

## 1. Final-sweep evidence

### Gates (all green on the landed commit)

- `just docs-check`: green, 442 pytest passed.
- `just docs-build` (Zensical) and `just docs-build-material` both emit `llms.txt`
  with sections Get started, Guides, Concepts, Reference, Contracts (optional).
- `tools/docs/tests/test_contracts.py` pins the llms.txt Contracts section to exactly
  the registry stems in `docs/_meta/contracts.yml` (28 stems). A new contract that is
  not added to the llmstxt plugin config fails the gate.
- `bob-docs urls --refresh`: additions only (`/task-relations/`), 57 total, `urls` OK.

### Accessibility sweep (both builders, this turn)

- `target/docs/a11y/zensical/report.json`: `violations: 0`
  (10 pages x 3 widths x 2 schemes, axe + reflow + keyboard + no-JS + mobile).
- `target/docs/a11y/material/report.json`: `violations: 0` (same matrix).
- No screenshot timeout this turn; no throwaway harness needed. The earlier
  Playwright `page.screenshot` timeout did not reproduce.

### Live vs published

- Live `/build.json` (`2026-10-20T19:22:11Z`): builder zensical, bob-cli SHA
  `1513a385a691...` == landed commit, clean tree. bob-mac-capture `a85b1f86`,
  bob-plugins `d4927af2`.
- `just docs-status`: host manifest fingerprint matches live
  (`bob-cli=1513a385a691`), workflows `publish.yml` and `weekly.yml` both active.
- Recent publishes: `#39482797830` schedule success 19:21:44Z; `#39473862898`
  workflow_dispatch success 18:20:24Z (this phase's publish); `#39445955933`
  schedule success 15:10:21Z.

### Weekly link check (non-Adobe failure recorded, no new exclusions)

- Watched run: <https://github.com/bobs-org/bobs-org.github.io/actions/runs/39475174066>
  (`weekly.yml`, dispatched 18:29Z) — completed **failure**.
- Failure is four HTTP **429 Too Many Requests** on
  `github.com/bobs-org/bob-cli/edit/master/docs/...` URLs (Material theme edit links
  redirecting to login under rate limit). Zero Adobe failures: the only "adobe" line
  in the log is the landed `--exclude ^http://www[.]adobe[.]com/?$` flag working as
  intended. Per the approved plan, a non-Adobe failure is recorded and no exclusion
  is added.
- Managed issue #2 (Docs weekly checks blocked,
  <https://github.com/bobs-org/bobs-org.github.io/issues/2>) is still **OPEN** and now
  points at run 39475174066. Prior red runs 39427654125 / 39424193019 were Adobe-only.
- Follow-up for the land agent: re-dispatch `gh workflow run weekly.yml --repo
  bobs-org/bobs-org.github.io --ref main` after the 429 backoff window; a pass closes
  issue #2 automatically. If `github.com/edit/...` 429s persist, the fix belongs in the
  Material theme edit-link configuration or a documented retry policy, not in broader
  lychee exclusions (see PROPOSED FOLLOW-UP below).

### Schedule observations (operator timer is Bryan's call)

- `event=schedule` runs: `39482797830` 19:21:44Z success, `39445955933` 15:10:21Z
  success, `39405915133` 10:09:26Z failure (pre-existing `runs-on`, since fixed).
- Cron stays `17 * * * *`. Hours with no run at all (e.g. 11:17, 12:17, 13:17, and the
  19:21 run firing four minutes late) confirm GitHub best-effort scheduling; this is
  now documented in `tools/docs/host/README.md` and `docs/develop/build.md`, which also
  note every run is idempotent behind the gates, `just docs-publish` publishes on
  demand, and `just docs-status` shows what is live.
- Whether to add an operator-side `just docs-publish` cadence on top of cron is
  Bryan's call; nothing here requires it (publishes are landing hourly-or-better).

## 2. Reader-test results

Protocol: `docs/develop/reader-testing.md`. Ten fresh blind readers via path (b)
(`claude -p --allowedTools 'WebFetch(domain:bobs-org.github.io)'` from a fresh empty
dir, stdout to scratch). S1–S5 got only `https://bobs-org.github.io/`;
L1–L5 got only `https://bobs-org.github.io/llms.txt`. Pass bar: >=4/5 readers choose
the expected door first per task. Choosing Contracts (optional) first counts as a miss.

Expected doors: task 1 Learn, task 2 Learn, task 3 Do, task 4 Understand,
task 5 Look up, task 6 Do. Site doors map Learn→Get started, Do→Guides,
Understand→Concepts, Look up→Reference; llms.txt section titles map the same way.

### Site entry point (S1–S5): 6/6 tasks pass, 5/5 each

| Task | Expected door | S1 | S2 | S3 | S4 | S5 | Reached? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Is Bob for me? | Learn | Get started | Get started | Get started | Get started | Get started | 5/5 yes |
| Capture your first task | Learn | Get started | Get started | Get started | Get started | Get started | 5/5 yes |
| Sync the vault across machines | Do | Guides | Guides | Guides | Guides | Guides | 5/5 yes |
| What is a lane? | Understand | Concepts | Concepts | Concepts | Concepts | Concepts | 5/5 yes |
| Find an environment variable | Look up | Reference | Reference | Reference | Reference | Reference | 5/5 yes |
| Fix "bob not resolved" in Mac Capture | Do | Guides | Guides | Guides | Guides | Guides | 5/5 yes |

### llms.txt entry point (L1–L5): 6/6 tasks pass, 5/5 each

| Task | Expected door | L1 | L2 | L3 | L4 | L5 | Reached? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Is Bob for me? | Learn | Get started | Get started | Get started | Get started | Get started | 5/5 yes |
| Capture your first task | Learn | Get started | Get started | Get started | Get started | Get started | 5/5 yes |
| Sync the vault across machines | Do | Guides | Guides | Guides | Guides | Guides | 5/5 yes |
| What is a lane? | Understand | Concepts | Concepts | Concepts | Concepts | Concepts | 5/5 yes |
| Find an environment variable | Look up | Reference | Reference | Reference | Reference | Reference | 5/5 yes |
| Fix "bob not resolved" in Mac Capture | Do | Guides | Guides | Guides | Guides | Guides | 5/5 yes |

No reader chose Contracts (optional) first. No fix round: every task cleared the
4/5 bar on the first attempt, so no label/hub-copy change was made and no re-run
was needed.

### Recurring reader observations (not misses; see follow-ups)

- Task 2 has no link titled "capture your first task"; all ten readers inferred
  "Your first Bob day". It worked 10/10, but the inference is worth knowing.
- Task 5: no nav label says "environment"; all ten readers guessed Configuration
  and were right. Consider a future nav/alias cue (land-agent call; not a miss).
- Pages never say plainly who Bob is *not* for; the only opt-out is "skip Mac
  Capture". Several readers noted it.
- `docs/guides/fix-mac-capture-bob-resolution.md:49`: "the `!` glyph returns to the
  bullet-b" reads garbled to three readers. Copy polish only; recorded below.

### Note on the invalid 15:15Z attempt (why it was rerun)

An earlier reader attempt (plan record: ~15:15Z) ran against the live site **before**
commit `1513a385` was landed and published, so it tested a site without the change:
all five `llms.txt` readers got HTTP 404, two site readers could not open the home
page with their browser tool, one failed on model capacity, and only two finished all
six tasks. Those results do not count as this phase's reader test and were discarded.
The valid sweep above ran 18:31–18:47Z against the published commit (publish run
`394738698` completed success 18:20Z; live `/build.json` SHA confirmed equal before
scoring). The exact 15:15Z timestamp is per plan record and was not independently
re-corroborated; the reason for invalidity (pre-land site) is verified.

### Method note (disclosure)

During scoring, the handoff agent accidentally re-executed `/tmp/readers/run_readers.sh`
instead of only listing outputs. Effects: the five site outputs (originally
18:31–18:38Z) were replaced by a fresh identical-protocol rerun (20:25–20:30Z, all
exit 0), and `L1.out` was briefly truncated to zero before its in-flight reader
finished writing (recovered whole, 3469 bytes). The scored site set is therefore the
20:25–20:30Z rerun, run with the same script, prompts, and entry point. L2–L5 are the
original 18:41–18:47Z outputs. All ten scored outputs are complete six-task tables;
nothing was hand-edited. Raw outputs lived only in ephemeral `/tmp/readers/` (script,
prompts, `S1.out`–`S5.out`, `L1.out`–`L5.out`); the tables above are their durable
record. Also, most readers timed tasks by fetch-duration shares or batches rather than
a stopwatch, and several read via a page-fetch helper instead of a browser — recorded
per `reader-testing.md`, which asks for the route tried rather than lab timing.

## 3. Epic follow-through ledger

Every `PROPOSED FOLLOW-UP:` / `DISCOVERED ISSUE:` on the epic and its descendant
phase beads, with disposition. Epic notes #1–#7 are on `bob-cli-a0`;
`bob-cli-a0.13` itself carries no notes yet (this phase's follow-ups are added at
close).

- Epic #1/#2 (dangling "see the PDFKit and text-layer research" in
  `docs/highlights-create.md`): **resolved here** — `1513a385` ends the sentence at
  "...damages some extracted words." Once `bob-cli-8p`'s decision record is accepted
  and published, that sentence can link to its `/develop/decisions/#<slug>` anchor.
- Epic #3 (Bryan walking `/start/` on a clean machine): **open** — handoff item §4.1.
- Epic #4 (shared-theme accessibility defects): **resolved here** — a11y sweep shows
  0 violations on both builders (§1).
- Epic #5 (weekly Adobe 403): **resolved here** — `weekly_exclusion = url` landed
  (`--exclude ^http://www[.]adobe[.]com/?$` with comment, docstrings, and
  `test_links_online.py` updated); the watched weekly run shows zero Adobe failures.
  The run is still red on new non-Adobe 429s — open follow-up below.
- Epic #6 (sparse hourly schedule): **resolved/documented here** — cron kept, GitHub
  best-effort behavior documented in `tools/docs/host/README.md` and
  `docs/develop/build.md`; scheduled runs are now appearing (15:10Z, 19:21Z).
- Epic #7 (Material template unit tests fail on clean tree: `github-callouts`
  `ModuleNotFoundError` in `test_templates_in_material` /
  `test_component_chips_in_material`, root-caused by `bob-cli-a2.land` to a bare
  PATH `mkdocs` instead of the project env): **open, pre-existing, not caused by
  this phase** — the failure reproduces on untouched base `eefdeb47` and only when
  the `material` docs group is absent; fix candidates are `sys.executable -m mkdocs`
  plus `pytest.importorskip`, or syncing the material group in `docs-check`.

...[truncated 3885 chars]

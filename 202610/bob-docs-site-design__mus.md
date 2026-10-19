# Bob documentation site: Diátaxis design research (`__mus`)

Research question: how should Bryan get excellent, Diátaxis-inspired,
sase-quality documentation for all three public Bob repos
(`bobs-org/bob-cli`, `bobs-org/bob-mac-capture`, `bobs-org/bob-plugins`),
and is GitHub Pages the right free host?

Short answer: yes, do it; yes, GitHub Pages is free for this; build **one
unified MkDocs Material site** (cloned from sase's proven setup) in a **new
`bobs-org/bob-docs` repo**, deployed to a project Pages URL, and grow it
iteratively — do not build three sites and do not scaffold four empty
Diátaxis quadrants on day one.

## 1. Is this a good idea? Critique of the plan

Yes, with three caveats that change the shape of the work.

**It is a good idea because the raw material already exists and is already
rotting in place.** `bob-cli` alone carries a 1,584-line `README.md` plus 26
guides under `docs/` (~26.7k lines total). `docs/capture.md` is 6,371 lines,
`docs/task-dependencies.md` 3,556 lines, `docs/highlights-ref-sync.md` 2,055
lines. `bob-plugins/README.md` is 579 lines with per-plugin descriptions that
are single table cells running to hundreds of words. `bob-mac-capture/README.md`
is 2,807 lines, much of it a versioned JSON-contract spec for the `bob`
subprocess interface. This is reference-grade content that is currently
undiscoverable: there is no search, no navigation beyond one index page
(`docs/README.md`), no deep-link-stable URL scheme, and no build that fails
when a link breaks. A real site converts this sunk cost into an asset.

**Caveat 1 — Bob is a one-user system, so size the ambition accordingly.**
Unlike sase (a public tool with external adopters), Bob serves Bryan and his
agents. The audience is: Bryan in six months, coding agents resolving
contracts, and hypothetically future users. That means reference accuracy and
searchability beat completeness and marketing polish. Do not commission a
marketing homepage, blog, or versioned handbook on day one. sase's site has a
blog, RSS, PDF handbook, and social cards because sase is a product launch;
Bob needs none of that yet.

**Caveat 2 — "Diátaxis-inspired, like sase" should mean the workflow, not
just the four folders.** The Diátaxis guide itself
(`https://diataxis.fr/how-to-use-diataxis/`) is explicit: Diátaxis "describes
a complete picture" but is "not intended to be a plan"; "it certainly does
not mean that you should create empty structures for tutorials/howto
guides/reference/explanation with nothing in them. Don't do that. It's
horrible." The prescribed motion is small iterative improvements from which
structure emerges "from the inside." sase's own site reflects this: its nav
is Tutorials ("Get started") / How-to ("Guides") / Explanation ("Concepts") /
Reference, but each quadrant was filled by migrating real content, with
tooling (`tools/docs_move`, page budgets in `Justfile`) managing the moves.
The Bob plan should copy that discipline: migrate-then-shape, never
scaffold-then-fill.

**Caveat 3 — three repos do not imply three sites.** The request says
"documentation for all of the public bob repos," which reads as one
documentation experience covering three codebases. Three separate Pages sites
would triple the theme/CI/deploy maintenance and force readers to guess which
site holds the answer (capture grammar? CLI or Mac app?). The capture-contract
content already spans `bob-cli` and `bob-mac-capture` by design (thin-client
decision record `mac-capture-is-a-thin-client`: the Mac app delegates grammar,
preview, and vault mutation to `bob`). One unified site with per-repo sections
is the correct information architecture.

## 2. What exists today (inventory)

All three repos are PUBLIC (verified via `gh repo view`), so GitHub Pages
hosting is free with no paywall (see §4).

| Repo | Docs today | Shape |
|---|---|---|
| `bob-cli` | `README.md` (1,584 lines) + `docs/` (26 guides) + `docs/README.md` index | Long-form guides mixing how-to and reference; `getting-started.md` is genuinely tutorial-adjacent; `capture.md` (6.4k lines) is three documents in one |
| `bob-plugins` | Single `README.md` (579 lines); no `docs/` dir | Per-plugin prose trapped in table cells; unmaintainable at current verbosity |
| `bob-mac-capture` | Single `README.md` (2,807 lines); no `docs/` dir | Install guide + `bob` JSON-contract spec + packaging notes interleaved |

Notable gaps against Diátaxis quadrants:

- **Tutorials** (learning-oriented, must work end-to-end): only
  `docs/getting-started.md` qualifies, and it assumes an existing vault rather
  than producing a first success from zero. No Mac-app or plugin tutorial
  exists.
- **How-to guides** (goal-oriented): partially covered — `plan.md`,
  `vault-git-sync.md`, `gkeep.md` read as guides — but they are titled by
  subsystem, not by user goal (sase titles its guides "Run agents in
  parallel", not "agents.md").
- **Reference** (information-oriented, must be complete and dry):
  `bob <command> --help` is authoritative but lives outside the docs; the
  Mac contract spec in its README duplicates CLI behavior by hand and will
  drift.
- **Explanation** (understanding-oriented): almost entirely absent. The
  closest content is the memory-web decision records (e.g. freshness gating,
  sticky lanes), which live in `sase/memory/decisions/` and are invisible to
  readers of the docs.

Structural fact that matters for the plan: `bob-cli` has **no `.github/`
directory at all** — there is no CI in the repo. The docs site will be the
first thing that needs a GitHub Actions workflow, so keep that first workflow
minimal (build + deploy only) rather than bootstrapping a full CI matrix.

## 3. How sase does it (the model to clone)

Studied via a local checkout of `gh:sase-org/sase` (full tree + history,
not web-fetched). The sase docs stack:

- **Generator**: MkDocs with the **Material** theme (`mkdocs.yml` at repo
  root, `docs_dir: docs`, `strict: true` with warnings-as-errors).
- **Structure**: explicit Diátaxis nav — Home → Get started (tutorials) →
  Guides (goal-titled how-tos) → Concepts (explanation) → Reference (CLI
  per-command pages, config, TUI, glossary, design decisions) → Contribute.
  Reference CLI pages are generated/staged by tooling, not hand-maintained
  one by one.
- **Beauty/authorship details worth copying**: light/dark palette toggle,
  `navigation.tabs` + `navigation.sections`, `toc.follow`, built-in search
  with suggest/highlight, admonitions, `pymdownx` superfences/details/
  snippets, shared abbreviations include, custom `docs/overrides/` templates
  and `stylesheets/extra.css`, a generated `llms.txt` page index (agent
  consumers), `_headers`/`robots.txt`/redirects handling.
- **Reliability gates**: `just docs-check` (`mkdocs build --strict` plus a
  URL checker over the built `site/`), page-budget tooling, and a
  `docs-deploy.yml` workflow (build → verify artifact → deploy) on `master`
  pushes. Docs failures block like test failures.
- **Hosting (the one thing NOT to copy)**: sase deploys via
  `cloudflare/wrangler-action` to `sase.sh` (see `wrangler.jsonc`,
  `assets: { directory: site }`). That buys a custom domain and Workers
  integration at the cost of a Cloudflare account, API tokens, and DNS
  management. Bob needs none of that on day one.

Takeaway: clone the MkDocs Material configuration and the docs-as-code
discipline (strict builds, link checking, generated reference); substitute
GitHub Pages for Cloudflare.

## 4. Hosting: yes, GitHub Pages is free for this

Verified against GitHub Docs ("What is GitHub Pages") plus the repo facts
above:

- Pages is free for **public** repositories with no bandwidth/storage quota
  that a docs site will approach (~1 GB storage, ~100 GB/month bandwidth).
  All three Bob repos are public, so there is no paywall question.
- Two flavors exist: one **organization site** (`bobs-org.github.io`, served
  from a repo literally named `bobs-org.github.io`) and unlimited **project
  sites** (`bobs-org.github.io/<repo>/`, served from each repo). They can
  coexist.
- Custom domains are free with automatic HTTPS via a `CNAME` file; nothing
  about starting on `*.github.io` forecloses a custom domain later.
- The standard MkDocs deploy path is either `mkdocs gh-deploy` (pushes to a
  `gh-pages` branch) or the official `actions/deploy-pages` flow. Both are
  routine; the `mike` plugin adds versioned snapshots later if ever needed.

Recommendation (§7 has the full form): publish **one project site** from a
new docs repo. Do not squat the org apex (`bobs-org.github.io`) on a docs
site — reserve that for a future landing page that can link the docs, the
repos, and whatever comes later. Defer `mike` versioning: `bob-cli` is at
`0.1.0` with no tags and no releases, so there is nothing to version yet;
`latest-only` docs are correct until the first tagged release.

Alternatives considered and rejected:

- **Cloudflare Pages/Workers (sase's choice)**: excellent, but solves
  problems Bob doesn't have (custom domain now, edge functions, PDF pipeline)
  and adds account/secret/DNS overhead. Revisit if Bob ever needs a real
  domain with preview deployments per PR.
- **Read the Docs**: free and versioned, but Sphinx-flavored theming is
  weaker out of the box and the "beautiful" requirement would cost custom
  theme work. MkDocs Material looks better with less effort.
- **Docusaurus / Astro Starlight**: modern, beautiful, MDX-capable. But both
  drag in a Node/React toolchain (hundreds of MB) for what is today ~27k
  lines of plain Markdown, and neither matches the sase precedent the request
  explicitly asks to follow. Starlight is the right answer only if the docs
  later need interactive components; start with Markdown.
- **Obsidian Publish / GitBook / Mintlify**: hosted, pretty, but
  subscription-locked and wrong-shaped for CLI/API reference plus strict
  link-checked builds. No.

## 5. Stack recommendation: MkDocs Material, cloned from sase

| Criterion | MkDocs Material | Starlight | Docusaurus |
|---|---|---|---|
| Markdown reuse (27k lines) | Drop-in | Drop-in | Drop-in |
| Toolchain weight | ~30 Python pkgs | Node/Astro | React/Webpack, heaviest |
| Beauty out of the box | Excellent | Excellent | Very good |
| Search | Built-in | Built-in (Pagefind) | Built-in |
| Precedent ("like sase") | Exact match | None | None |
| Agent-editable | Yes, plain `.md` | Yes | Yes, plus MDX |

Choose **MkDocs Material**, seeded by copying sase's `mkdocs.yml`,
`docs/overrides/`, `stylesheets/extra.css`, `requirements-docs.txt` pins,
and the `docs-check` just recipe, then deleting what Bob doesn't need yet
(blog, RSS, PDF, social card, Cloudflare analytics). Concretely:

- `strict: true` + `use_directory_urls` + `validation` block: keep.
- Theme `features` (tabs, sections, toc.follow, copy buttons, search
  suggest/highlight): keep — this is 80% of "beautiful" for free.
- `mkdocs-redirects`: keep from day one; page moves during the Diátaxis
  migration will otherwise break deep links agents have memorized.
- `llms.txt`: keep the concept (a generated page index for agent
  consumers) — Bob's heaviest readers will be agents, and this is cheap.
- Blog/RSS/PDF/social-card/wrangler: cut. Re-add only on demonstrated need.

## 6. Information architecture (the design lead)

**One site, three product sections, four Diátaxis quadrants.** Top-level nav:

- Home (short: what Bob is, the three repos, three links into the quadrants)
- Tutorials: "Capture your first task", "Run your first Pomodoro review",
  "Install the Mac app", each tested end-to-end in CI where feasible
  (or at least manually per release — untested tutorials rot fastest)
- How-to guides (goal-titled, migrated from `docs/`): e.g. "Drain Google
  Keep into tasks" (from `gkeep.md`), "Sync the vault with git" (from
  `vault-git-sync.md`), "Install the Mac menu-bar app", "Deploy plugins to
  the vault"
- Concepts (new, short, highest value-per-line): the vault model (notes,
  lanes, Pomodoro ledger), freshness/review model, dependency model, the
  thin-client contract (Mac app ↔ `bob` JSON), plugin architecture. Much of
  this can be distilled from the `decisions` memory web and existing guides —
  explanation is the quadrant with the best effort-to-clarity ratio.
- Reference: CLI command index **generated from `bob --help` output**
  (checked in by a script, diffed in CI so drift fails the build), per-guide
  contract appendices as they exist today, the Mac↔CLI JSON contract
  (single-sourced, owned by `bob-cli`, linked — never duplicated — from the
  Mac section), plugin API namespaces (`api.*` versioned surfaces that
  already exist informally in the plugins README).
- Glossary (sase has `reference/glossary.md`; Bob's lane/status/vault
  vocabulary — Ready/Next/Pending/Blocked, Pomodoro, Task Link, Schedule Log
  — needs exactly this).

**Content migration sketch** (iterative, per the Diátaxis workflow §1):

1. Move `bob-cli/docs/*` + `README.md` installation section verbatim into
   the new site (realm: "it renders and links pass strict build"). Split
   only `capture.md` — at 6,371 lines it is unservable as one page; its
   picker-command sections are natural sub-pages.
2. Break `bob-plugins/README.md` table cells into one page per plugin plus a
   plugin-index page; keep the version-per-plugin table as the index.
3. Extract the Mac README's JSON-contract material into the Reference
   section under single ownership (§5 "single-sourced" rule); leave install
   + packaging prose in the Mac section.
4. Write Concepts pages new (5–7 short pages). This is the only net-new
   writing in phase 1 and the main "lead the design" deliverable.
5. Retitle guides by goal over time (`plan.md` → "Plan today's work within
   budget"); never create empty quadrant placeholders.

Keep each repo's `README.md` as a landing page (what it is, install in 5
lines, link to the docs site). READMEs remain the GitHub front door; the
site is the manual.

## 7. Adjustments to the requirements (called out)

1. **"Documentation for all of the public bob repos" → one unified site,
   not three.** (Justified in §1 caveat 3 and §6.) New repo
   `bobs-org/bob-docs`, project Pages URL; reserves the org apex.
2. **"Inspired by diataxis just like sase's" → adopt sase's nav quadrants
   AND the iterative workflow.** Explicitly reject a day-one four-folder
   scaffold with empty pages (the Diátaxis guide calls this "horrible").
3. **"I don't have a website" → you don't need one.** A project Pages site
   is the website. No domain purchase, no DNS, no Cloudflare account for
   phase 1. Add a custom domain later via `CNAME` without rebuilding.
4. **No versioning, blog, PDF, or analytics in phase 1.** sase has all four
   because it is a launched product; Bob at `0.1.0` with zero tags needs
   none. Each is a documented re-add, not a redesign, when the trigger
   arrives (first tagged release → `mike`; launch announcement → blog).
5. **Add one requirement: generated CLI reference.** Hand-maintained
   command docs drift from `bob --help` (already declared authoritative in
   the README). A checked-in generation script + CI diff gate is the
   reliability backbone of the Reference quadrant.
6. **Add one requirement: `mkdocs build --strict` + link check as a merge
   gate.** This is what makes docs "reliable" rather than "pretty Markdown":
   broken links and moved pages fail the build. Note this also bootstraps
   `bob-cli`'s first GitHub Actions workflow — keep it docs-only and minimal.

## 8. Recommended solution (phased)

**Phase 0 — decision (this report).** Accept: one site, MkDocs Material,
new `bobs-org/bob-docs` repo, project Pages URL, iterative migration.

**Phase 1 — skeleton that renders (small, shippable).** Create the repo from
sase's docs scaffolding minus blog/PDF/RSS/Cloudflare; move `bob-cli/docs`
in verbatim with a minimal `nav:`; split `capture.md`; add per-repo section
indexes; wire `actions/deploy-pages` on `master` push; keep repo READMEs as
front doors linking to the site. Success: green strict build, public URL,
search works.

**Phase 2 — Diátaxis shaping.** Plugin-per-page split; Mac contract
single-sourcing; goal-retitling of guides with `mkdocs-redirects` entries;
new Concepts pages (vault model, freshness, dependencies, thin-client
contract, plugin architecture); glossary; `llms.txt`; generated CLI
reference with CI diff gate.

**Phase 2.5 — beauty pass.** Homepage hero in the style of sase's
(`docs/index.md` hero + install command + two CTAs), palette/typography
tuning in `extra.css`, favicon, dark-mode check. Deliberately after content:
beauty applied to real pages, not placeholders.

**Phase 3 — on triggers only.** Custom domain (buy + `CNAME`), `mike`
versioning (first tagged release), blog/changelog (launch), PDF handbook
(someone asks twice).

Rough effort honesty: Phase 1 is an afternoon-to-a-day (scaffolding is
copied, content is moved). Phase 2 is the real work — several focused
sessions, well-suited to phased agent execution with per-phase review.
Phase 2.5 is short. The expensive mistake to avoid is gold-plating Phase 1
with empty quadrants, versioning, and branding before any migrated page
demands them.

## Sources and evidence

- Local checkouts inspected directly: `bob-cli` (`docs/`, `README.md`,
  `justfile`, `Cargo.toml`, git log/tags), linked `bob-plugins`
  (`README.md`, `package.json`), linked `bob-mac-capture` (`README.md`,
  `justfile`), external `gh:sase-org/sase` (`mkdocs.yml`, `docs/` tree,
  `Justfile` docs targets, `.github/workflows/docs-deploy.yml`,
  `wrangler.jsonc`, `requirements-docs.txt`, `tools/`).
- Web: `https://diataxis.fr/how-to-use-diataxis/` (iterative-workflow
  guidance quoted in §1); `http://sase.sh` + sase repo as the "like sase"
  reference implementation; GitHub Docs "What is GitHub Pages" (org vs
  project sites, one site per account/repo, custom-domain HTTPS); general
  static-site comparisons (MkDocs Material vs Starlight vs Docusaurus
  weight/beauty trade-offs); `mike` + `gh-deploy` deploy patterns.
- Verdicts independently formed; peer reports (`__cdx`/`__cld`/`__grk`/
  `__gem`) deliberately not opened.

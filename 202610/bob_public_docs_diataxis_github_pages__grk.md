# Public Bob documentation: Diátaxis site on GitHub Pages

**Researcher:** grk (independent swarm report)
**Date:** 2026-10-19
**Scope:** How to give the three public Bob product repos — `bobs-org/bob-cli`, `bobs-org/bob-plugins`, `bobs-org/bob-mac-capture` — excellent, beautiful, Diátaxis-inspired documentation, hosted for free, with a design Bryan can implement.
**Not in scope:** The private vault repo `bobs-org/bob`. Sidecar repos (`--beads`, `--agents`, `--research`, `--sdd`, attachments). Agent instruction files (`AGENTS.md`).

## Recommendation (read this first)

Do it. The current Markdown corpus is large, mixed-mode, and unusable as a public product surface. A Diátaxis site is the right shape. GitHub Pages is the right free host. Copy SASE's *compass, tab names, page budgets, generated reference, and homepage doors* — not SASE's Cloudflare Worker, PDF handbook, blog, or 400-page reference catalog.

Ship **one product site named Bob** at `https://bobs-org.github.io/` from a new public org-Pages repo `bobs-org.github.io`. Treat CLI, plugins, and Mac Capture as surfaces of one system. Keep today's in-repo `docs/*.md` files as **agent/developer contracts**; rewrite a small public tree beside them rather than dumping 222,000 words onto the web.

Start complete and small: homepage, three tutorials, a handful of guides, six concept pages, and generated CLI lookup. Grow by Diátaxis's one-improvement cycle. Do not scaffold four empty quadrants.

**Generator:** MkDocs + Material for MkDocs (the stack behind [sase.sh](https://sase.sh)), assembled in `tools/` before the build, deployed with GitHub's official Pages Actions (`configure-pages` / `upload-pages-artifact` / `deploy-pages`). Stay Zensical-compatible (no extra MkDocs plugins, no `hooks:`) so a later switch is cheap. Do not start on Zensical as the primary builder.

---

## 1. Critique of the request

### 1.1 What is a good idea

A public documentation site is justified.

- The three product repos are already **public** (`gh repo list bobs-org`). None has GitHub Pages configured. There is no `bobs-org.github.io` repo.
- bob-cli's human entry points are a 1,584-line README (~13k words) plus `docs/` totaling **~222,000 words / 1.5 MB**. `docs/capture.md` alone is ~54,600 words; `docs/task-dependencies.md` is ~34,200. SASE's public guide budget is 1,500–2,500 words per page. These files are contracts, not teaching.
- bob-plugins has **no `docs/` tree**. Its README is ~10,400 words, with plugin descriptions that are single paragraphs thousands of words long (block-id-prompt, navigation-hotkeys, task-status-cycler). That is the failure mode Diátaxis exists to prevent: every mode of documentation mashed into one scroll.
- bob-mac-capture's README is ~29,300 words. The Requirements section is a running changelog of capture-protocol fields. Install steps, protocol facts, and compatibility history share one page.
- SASE already proved the aesthetic and IA: Material theme, four doors labeled **Learn / Do / Understand / Look up**, generated CLI reference, page budgets, tutorial tests. Bob can reuse that pattern without copying the product identity.

The goal "inspired by Diátaxis, like SASE" is the right north star for *content type* and *reader doors*. GitHub Pages is the right answer to "I don't have a website yet."

### 1.2 What is a bad idea if taken literally

"Excellent documentation for all of the public bob repos" as a single delivery, matching SASE's current site, would fail.

1. **SASE's site is the result of years of splits, moves, generated stubs, and a writing contract** (`docs/contribute/writing-docs.md`, `tools/check_docs`, `docs/_meta/moves.yml`, hundreds of redirect rules). Copying the *end state* is how teams create four empty folders and a pretty 404.
2. **Diátaxis's own workflow page forbids the plan as stated as a structure-first project.** [How to use Diátaxis](https://diataxis.fr/how-to-use-diataxis/) says: use it as a guide, not a plan; do not divide documentation into four empty sections; do not wait to publish a large tranche; improve one cell at a time so the organism is always complete.
3. **Three repos are one product.** Separate sites (`/bob-cli`, `/bob-plugins`, `/bob-mac-capture`) would make a newcomer choose a repo before they understand the system. `just install-all` already treats them as siblings of one install.
4. **Publishing the existing `docs/` tree as the site** would be an unreadable reference dump with tutorial, how-to, and explanation mixed in. `docs/getting-started.md` already mixes install, vault schema, capture grammar, and troubleshooting on one page.
5. **Beauty is not a unique CSS art project.** SASE is beautiful because of restraint: one hero, four cards, a palette, search, and short pages. Dumping 54k-word files into Material will look worse than GitHub's README renderer.
6. **Audience is not "the internet at large" today.** Bob is Bryan's GTD/Obsidian system that happens to be public. Write for (a) Bryan on a fresh machine, (b) a competent newcomer who cloned the repos, (c) agents via `llms.txt` and generated reference. Do not write a SaaS marketing site. GitHub Pages [forbids using Pages as a commercial SaaS host](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits); a personal/open-source product site is allowed.

### 1.3 Would I take a different approach?

Yes, in five places:

| Request (implied) | Adjustment |
| --- | --- |
| Document each public repo | Document **one product**, with repo-faithful reference sections |
| Stand up Diátaxis structure, then fill it | Ship a **complete small site**, then grow |
| Host "somehow" on github.io | **Org Pages** at `bobs-org.github.io`, not three project sites |
| Match SASE including its hosting | Match SASE **IA and discipline**; host on GitHub Pages, not Cloudflare |
| "Excellent" = comprehensive on day one | "Excellent" = **correct mode, short pages, generated facts, working tutorials** |

I would still do a public site. I would not do three sites, a docs-only rewrite of the 222k-word corpus, a blog, a PDF handbook, or Cloudflare, until the small site is loved.

---

## 2. Requirement adjustments (explicit)

These change the request. Each is a recommendation, not a silent scope cut.

**A. One site, three surfaces.**
Requirement becomes: excellent public docs for **Bob**, covering bob-cli, bob-plugins, and bob-mac-capture. Each repo README becomes a thin pointer into the site plus a local developer stub. Rejected: one MkDocs project per repo.

**B. Two corpora, not one.**
Keep existing `docs/*.md` in bob-cli (and the plugin/Mac READMEs) as **in-repo contracts** for agents and conformance tests. Add a new public tree (`docs/site/` in each product repo, assembled into the Pages build). Do not auto-publish `docs/capture.md` as a web page. Over time, split contracts into generated reference pages; until then, link "full contract" from Reference as a GitHub blob URL.

**C. Complete-small first delivery, not empty IA.**
First published site must contain: homepage with four doors; three tutorials; enough guides to finish a working day; six concept pages that teach the core nouns; generated `bob --help` reference. That is a complete plant in Diátaxis's sense. Empty `tutorials/` / `how-to/` / `reference/` / `explanation/` directories are out of scope.

**D. Org Pages URL from day one.**
Create public repo `bobs-org.github.io` so the canonical URL is `https://bobs-org.github.io/` with no `/bob-cli` prefix. Project Pages URLs are an interface; SASE treats inbound URLs as a compatibility contract. Starting on a prefix and later moving to org Pages creates a moves.yml problem you do not have yet.

**E. Custom domain is optional and later.**
GitHub Pages gives free HTTPS on `*.github.io`. A custom domain (CNAME / A records, Enforce HTTPS, org domain verification) is a one-hour follow-up when Bryan owns a name. Do not block the site on buying `bob.sh` or similar.

**F. No blog, no PDF handbook, no Cloudflare in v1.**
SASE's blog, handbook PDF (`just docs-pdf-check`, mkdocs-exporter, wrangler deploy) and `docs/_headers` / `docs/_redirects` exist because sase.sh is a Cloudflare Worker (`wrangler.jsonc` assets directory `site`). GitHub Pages does not serve `_redirects` the Cloudflare way. Use `mkdocs-redirects` HTML stubs if a page moves; otherwise have no historical URLs to preserve.

**G. Page budgets and a writing contract, copied from SASE, from the first PR.**
Without budgets, `capture.md` will be pasted into the site. Adopt SASE's ceilings (`start/` ≤ 2,500 words, guides target 1,500 / hard 2,500, concepts ≤ 3,000, hubs ≤ 400, hand-written reference ≤ 6,000). Generated pages exempt.

**H. Do not document the private vault.**
`bobs-org/bob` is private. Public pages may describe *vault layout conventions* (area notes, `## Tasks`, Dataview fields) as product facts. They must not quote personal notes, ledger contents, or screenshots that leak tasks.

**I. Agents are a first-class reader, via `llms.txt` and generated reference, not via AGENTS.md on the web.**
Publish `/llms.txt` (SASE already does this) summarizing nouns, install, and canonical reference URLs. Keep `AGENTS.md` in-repo.

**J. Visual identity is Bob, not a SASE reskin.**
Reuse Material features (sticky tabs, search suggest, code copy, light/dark). Use a tomato/paper palette and Bob's own homepage copy. SASE's teal-on-sage plus "Learn/Do/Understand/Look up" doors would read as a fork.

---

## 3. What Diátaxis actually asks for

Sources: [diataxis.fr](https://diataxis.fr/), [Start here](https://diataxis.fr/start-here/), [How to use Diátaxis](https://diataxis.fr/how-to-use-diataxis/), [Applying Diátaxis](https://diataxis.fr/application/).

### 3.1 Four needs, four forms

| Form | User need | Mode | Bob examples that belong here |
| --- | --- | --- | --- |
| **Tutorial** | Acquire skill by doing, instructor responsible for success | Action × study | Install Bob; capture the first task; complete one Pomodoro day |
| **How-to** | Achieve a real-world goal, already competent | Action × work | Deploy plugins; sign Mac Capture; recover a vault-sync conflict; drain Google Keep |
| **Reference** | Accurate facts, mapped to the thing | Cognition × work | `bob capture` flags; capture grammar tokens; plugin keymap table; Mac JSON protocol |
| **Explanation** | Why, context, multiple angles | Cognition × study | Why lanes are sticky; why Today is a ledger read; why Mac Capture is a thin client |

The compass (from Diátaxis start-here):

- Action + acquiring skill → tutorial
- Action + applying skill → how-to
- Cognition + applying skill → reference
- Cognition + acquiring skill → explanation

Most Bob pain today is **boundary crossing**: `docs/getting-started.md` teaches and specifies; plugin README paragraphs explain *and* list every keymap; Mac Capture Requirements is reference in an install tutorial.

### 3.2 Process rules that should constrain the implementation plan

From the workflow page, treated as design constraints:

1. **Guide, not plan.** Do not open a project whose first milestone is "IA complete."
2. **No empty quadrants.** If a tab has no pages, omit the tab.
3. **Publish every improvement.** The first GitHub Pages deploy should be the homepage plus the first tutorial, not a private staging site that waits for "excellent."
4. **Organic growth, always complete.** After each PR the site should be appropriate to its stage: useful, navigable, not missing promised sections.
5. **Assess a small thing, change one thing.** The writing contract (below) is how this stays true once several people (and agents) write pages.

SASE translated this into operational rules worth copying:

- Directory *is* the type (`start/`, `guides/`, `concepts/`, `reference/`). A page never declares its kind in frontmatter.
- Two-question placement test before writing.
- Templates per type (`docs/_templates/` in SASE).
- Guide titles name the reader's goal ("Deploy the Bob plugins"), not the mechanism ("bob plugins sync").
- Tutorials: one path, no options, no why. Link explanation.
- Reference generated from the code that owns the fact, with `--check` drift detection. SASE: "Generation happens in `tools/` before the build."
- Tests must not pin Guide prose (except a tutorial runner).

---

## 4. How SASE did it (the actual inspiration)

Inspected: local checkout of `sase-org/sase` (mkdocs.yml, docs tree, `docs-deploy.yml`, `wrangler.jsonc`, `docs/contribute/writing-docs.md`, homepage, extra.css). Live site: [sase.sh](https://sase.sh).

### 4.1 IA mapping (copy this)

SASE does **not** label tabs "Tutorials / How-to guides / Reference / Explanation". The homepage says:

| Door | Copy | Directory | Diátaxis form |
| --- | --- | --- | --- |
| Learn | Walk the path from install to first landed change | `docs/start/` | Tutorial |
| Do | Solve one goal at a time | `docs/guides/` | How-to |
| Understand | Ideas behind the system | `docs/concepts/` | Explanation |
| Look up | Flag, key, keybinding, term | `docs/reference/` | Reference |

Plus `contribute/` (internals, writing contract) and `blog/` (dated essays). Only the homepage and generated compatibility stubs live at `docs/` root.

This renaming is the single best SASE idea for Bob. "Tutorial" sounds like homework; "Learn" is a door. Use the same four labels.

SASE also teaches **seven core nouns** on the concepts hub before using other terms. Bob needs an equivalent short list (proposed in §7.3).

### 4.2 Tooling (copy the discipline, not the host)

- **MkDocs** `strict: true`, `use_directory_urls: true`, link validation (`omitted_files`, `absolute_links`, `unrecognized_links`, `anchors` all `warn`).
- **Material** theme, `custom_dir: docs/overrides`, light/dark palettes, sticky nav tabs, search suggest/highlight, code copy.
- Plugins: `search`, `redirects`, `blog`, `rss`. Writing-docs.md forbids MkDocs `hooks:`, `gen-files`, and extra plugins so the site stays **Zensical-compatible**.
- Generation in `tools/` + `just docs-gen` / `docs-gen-check`.
- `just docs-check` = install Material + redirects + rss, then `mkdocs build --strict`.
- Page budgets enforced by `tools/check_docs`.
- Tutorial runner executes `start/` shell blocks against a fake provider.
- Reader-testing protocol: watch 3–5 newcomers pick doors; 4/5 must pick the expected door (`docs/contribute/reader-testing.md`).

### 4.3 Hosting (do not copy)

SASE deploys to a **Cloudflare Worker** (`cloudflare/wrangler-action`, `wrangler.jsonc` `assets.directory: "site"`, custom domain `https://sase.sh/`). The workflow builds the site, builds a PDF handbook, smoke-checks the PDF, then wrangler-deploys. `docs/_redirects` and `docs/_headers` are Cloudflare Pages/Workers conventions, not GitHub Pages.

Reasons SASE needs Cloudflare: custom domain they already own, `_redirects` volume, PDF content-type headers, Cloudflare analytics, Worker platform. Bob has none of those requirements today.

### 4.4 Visual system (steal the *method*)

`docs/stylesheets/extra.css` defines a small token set (`--sase-surface`, `--sase-accent`, `--sase-warm`, dark-scheme overrides), homepage card grid, hero, kicker, lede, pill. `docs/overrides/main.html` adds OG/Twitter tags and a release announce banner. The homepage is HTML-in-Markdown (`md_in_html`) with `hide: [navigation, toc]`.

Bob should do the same with **different tokens** (see §9).

---

## 5. Current Bob documentation (evidence)

### 5.1 bob-cli

| Artifact | Role today | Diátaxis diagnosis |
| --- | --- | --- |
| `README.md` (~13k words) | Install, command index, workflow, env, release checklist | Mixed how-to + reference. Fine as a GitHub landing *if* it points at the site. |
| `docs/README.md` | Guide index | Hub. Keep as in-repo map; do not use as the website nav. |
| `docs/getting-started.md` (~3.2k words) | First capture, vault settings, troubleshooting | Closest thing to a tutorial; still mixes schema, routing, and plugin deploy. Split. |
| `docs/capture.md` (~54.6k words) | Grammar, JSON, picker protocol | Reference contract. Must not be a web page as-is. Split later into generated + hand reference. |
| `docs/task-dependencies.md` (~34.2k words) | Depends-On, BLOCKS, successors, vectors | Reference + conformance. Web: a 2k-word explanation + a generated/contract link. |
| `docs/freshness.md`, `plan.md`, `projects.md`, `task-status-hooks.md` | 8–14k words each | Mixed explanation and schema. Concepts get the why; Reference gets the JSON. |
| Other `docs/*.md` | Per-command contracts | Stay in-repo; cherry-pick public how-tos (plugin deploy, vault-git-sync, gkeep). |
| No `mkdocs.yml`, no Pages workflow | — | Greenfield site. |

`cli_rules.md` (project memory) already requires excellent `--help`, sorted options, short aliases, colored output, frozen command names. The public Reference tab should **generate from that help**, not re-prose it. Today help is a mix of clap builders and hand `print_help()` (pomodoro, nightly, notify, collect_done). A generator must call the installed `bob` binary (or a `--help --format json` if you add one), not parse Rust.

### 5.2 bob-plugins

Seven plugins: `block-id-prompt`, `bob-articles`, `bob-ledger-tools`, `bob-navigation-hotkeys`, `bob-project-tasks`, `bob-vim-surround`, `task-status-cycler`. README is the only public doc. Gesture contracts are extremely precise and valuable as **reference tables**; they are unreadable as prose. Public need:

- Tutorial: none (covered by Bob's install-all tutorial).
- How-to: deploy with `bob plugins sync`; enable in Obsidian; recover a bad sync.
- Explanation: why plugins own the desktop gestures and bob-cli owns grammar/status.
- Reference: keymap cheat-sheet per plugin, versioned API namespaces (`api.freshness` v12, etc.) as lookup tables.

### 5.3 bob-mac-capture

README leads with the right architecture sentence ("the app owns presentation… `bob-cli` remains the only implementation of capture grammar") — that is a **concept page**. Then it spends tens of thousands of words on protocol compatibility. Public need:

- Tutorial: install, Accessibility, first global-hotkey capture.
- How-to: codesign vs ad-hoc; grant Accessibility after a signature change; point at a custom `bob`.
- Explanation: thin-client decision (already a memory record: `mac-capture-is-a-thin-client`).
- Reference: JSON/span protocol, completion contexts — generated or extracted, not a Requirements novel.

### 5.4 What "excellent" cannot mean here

It cannot mean "every public behavior currently described in those READMEs appears as a web page of similar length." It means a newcomer can install, capture, run a Pomodoro, and look up a flag without drowning; and a returning user can find the keymap or protocol field via search.

---

## 6. Hosting: GitHub Pages is the right free answer

### 6.1 Yes, github.io is free

Official GitHub docs ([What is GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)):

- Static hosting, HTTPS included.
- **Public repos on GitHub Free can use Pages.** (Private repos need a paid plan. All three product repos are public.)
- Two site types:

| Type | Repo name | Default URL |
| --- | --- | --- |
| User/org site | **exactly** `<owner>.github.io` | `https://<owner>.github.io/` |
| Project site | any repo | `https://<owner>.github.io/<repo>/` |

- One org site per account. Project sites: one per repo.
- Published site ≤ **1 GB**. Soft bandwidth **100 GB/month**. Deploy timeout **10 minutes**. Custom Actions workflows are **not** bound by the 10-builds-per-hour soft limit.
- Custom domain supported; free Let's Encrypt once DNS matches; "Enforce HTTPS."
- Pages sites are publicly reachable even when a private repo is allowed to publish. Do not put secrets in the docs repo.

MkDocs Material documents GitHub Pages as the default free publish path ([Publishing your site](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)). Zensical's own docs say the same and ship a Pages workflow from `zensical new`.

### 6.2 How to publish (do this, not `mkdocs gh-deploy`)

Two common patterns:

1. **`mkdocs gh-deploy`** (Material's copy-paste workflow): force-pushes a `gh-pages` branch with `contents: write`. Works. Pollutes the repo with a generated branch; token can push anywhere contents:write allows.
2. **Official Pages Actions** ([Using custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)): set Settings → Pages → Source = **GitHub Actions**. Build job uploads `actions/upload-pages-artifact`; deploy job needs `pages: write` + `id-token: write`, environment `github-pages`, `actions/deploy-pages`. OIDC, no branch push, environment protection.

**Choose (2).** Add a `.nojekyll` file in the built site (MkDocs/Material usually emit this) so GitHub does not run Jekyll on `_static/` / `_redirects`-style paths.

Set `site_url` in mkdocs.yml to the real public URL. Material's own creating-your-site guide warns that plugins and canonical URLs break if `site_url` still says "hosted at domain root" while the site lives under `/bob-cli/`. Another reason to use org Pages.

### 6.3 Org Pages vs project Pages vs custom domain

| Option | URL | Pros | Cons |
| --- | --- | --- | --- |
| Project Pages on bob-cli | `https://bobs-org.github.io/bob-cli/` | No new repo | Prefix forever (or a later painful move); plugins/Mac feel like guests |
| Three project sites | three URLs | Each README "has a site" | Splits the product; search does not cross; three themes to maintain |
| **Org Pages `bobs-org.github.io`** | **`https://bobs-org.github.io/`** | Clean URL, one search index, URL stability | Fourth public repo; CI must assemble sibling checkouts |
| Custom domain on either | `https://docs.example` | Prettiest | Costs a domain; DNS; not needed to launch |

**Recommend org Pages from day one.** Creating `bobs-org/bobs-org.github.io` is a 10-minute GitHub operation. The repo holds the site shell (mkdocs.yml, theme, homepage, assemble script, workflow). It does not hold the private vault.

Later custom domain: add the domain in Pages settings (GitHub writes `CNAME`; a CNAME in `docs/` is **not** enough if you use Actions — GitHub's docs say CNAME files do not auto-bind the domain under custom workflows). Point apex A records at `185.199.108.153`–`111.153` or a `www` CNAME to `bobs-org.github.io`. Verify the org domain to prevent takeover.

### 6.4 GitHub Pages vs Cloudflare vs Read the Docs vs Netlify

| Host | Cost | Why consider | Why not for v1 |
| --- | --- | --- | --- |
| **GitHub Pages + Actions** | Free | Already on GitHub; OIDC deploy; enough for MkDocs | 1 GB / 100 GB-month (irrelevant at this scale); no native `_redirects` |
| Cloudflare Pages/Workers | Free tier | What SASE uses; `_redirects`, `_headers`, analytics | Extra vendor and secret (`CLOUDFLARE_API_TOKEN`); no current need |
| Read the Docs | Free for OSS | Versioning, PR previews | Extra account; RTD branding; Zensical is supported but GH Pages is simpler |
| Netlify/Fly | Free tier | PR previews | Extra vendor |
| Obsidian Publish | Paid | Ironic for an Obsidian product | Paid; would tempt vault publishing |

**Stay on GitHub Pages until a concrete feature (PR preview at a stable URL, custom headers, a domain already on Cloudflare) pulls you off.** PR previews can wait; GitHub's Pages environment shows the production URL.

### 6.5 Limits that actually matter

- Keep screenshots compressed; do not commit SASE-style MP4 heroes unless you watch the 1 GB cap.
- Assemble + `mkdocs build --strict` must finish in 10 minutes. Easy for this corpus if you do not ingest the 54k-word files.
- Do not put `site/` build output in git.

---

## 7. Information architecture for Bob

### 7.1 Tabs

```
Home
Get started    → docs/start/          (Learn)
Guides         → docs/guides/         (Do)
Concepts       → docs/concepts/       (Understand)
Reference      → docs/reference/      (Look up)
```

Add `Contribute` only when there is a writing contract and a "build the site locally" page. Omit Blog.

Plugins and Mac Capture are **not tabs**. They appear inside every tab that needs them (a Mac install tutorial under Get started; a keymap reference under Reference). A homepage row of three product cards links into those pages.

### 7.2 First complete site (the plant, not the forest)

**Get started (tutorials — one path, timed, no options)**

1. *Install Bob* — `just install-all` from checkouts (or clone-missing), `bob doctor`-equivalent checks, completion. macOS and Linux called out as the one path with a skip-line for Mac Capture on Linux. ~15 minutes.
2. *Capture your first task* — one `bob capture` (or Mac hotkey on macOS as the same path's last step), then `bob query --tasks` to see it. Uses a throwaway vault or `BOB_DIR` fixture, not `~/bob`.
3. *Run one Pomodoro* — start, link the task, complete. Outcome: the task is In Progress/Done according to the real rules, in the fixture.

Each page: opening sentence, Before you start, numbered steps, "You have …", Next. Shell blocks executable by a tutorial runner.

**Guides (goal titles)**

Minimum set that makes a working day:

- Deploy the Bob plugins into a vault
- Sign and grant Accessibility for Mac Capture *(macOS)*
- Choose a vault with `BOB_DIR`
- Sync the vault with git
- Drain Google Keep into tasks
- Recover a capture or ref job that failed
- Look up a command with `--help` and completion

Stop there. "How to express nested prerequisites with `&`" is a later guide; the grammar lives in Reference.

**Concepts (teach nouns, then why)**

Hub page: the eight nouns, one diagram.

1. Vault, notes, and `#task`
2. Lanes (Ready / Next / Pending / Blocked) and why they are sticky
3. The daily Pomodoro ledger and why Today is a read
4. Capture as a grammar, not a form
5. Freshness, review walk, and rotten keeps
6. The three programs: CLI, plugins, Mac Capture (thin client)

Decision records in `sase/memory/decisions/` are the source of *why*; concept pages cite the behavior, not bead IDs.

**Reference**

- Generated CLI: one page per `bob` command group, from `--help`
- Capture grammar: token table (routes `@`, ids `^`, links `:`, parents `+`, …) distilled from `docs/capture.md` — a few thousand words, not 54k
- Plugin keymaps: one table per plugin
- Mac Capture JSON/spans: field list
- Glossary (the eight nouns plus Task Link, Depends-On, ^prj)
- Config keys (`~/.config/bob/config.yml`) as a table
- Link to in-repo contracts for conformance vectors

### 7.3 Core nouns (Bob's "seven nouns")

Teach these on the concepts hub; other terms appear only where needed, linked to the glossary:

1. **Vault** — the Obsidian folder Bob reads and writes (`BOB_DIR`, default `~/bob`).
2. **Task** — a `#task` checkbox line with Dataview fields and optional block id.
3. **Lane** — Ready, Next, In Progress (Pending), Blocked; derived or sticky per product rules.
4. **Pomodoro** — a timed ledger entry on the daily note; Task Links hang under it.
5. **Capture** — the grammar and the CLI/Mac gesture that writes tasks, links, and sessions.
6. **Freshness** — confirmation dates and the review walk that keep Ready honest.
7. **Project** — a project note whose `^prj` line can block residents.
8. **Plugin** — vault-side UI (Task Card, marks, walk). Mac Capture is named as a sibling program on the same hub, not a ninth noun.

### 7.4 What stays off the public site

- Bead IDs, epic labels, `src/` paths, "formerly / legacy" history (SASE forbids these in start/guides/concepts).
- Conformance vector dumps (keep in-repo; Reference may link).
- Personal vault content.
- Internal capture protocol evolution notes except a short "needs bob ≥ X" line on the Mac install tutorial.

---

## 8. Multi-repo assembly (reliability)

### 8.1 Rejected: mkdocs-multirepo-plugin

[jdoiro3/mkdocs-multirepo-plugin](https://github.com/jdoiro3/mkdocs-multirepo-plugin) clones other repos at build time via `!import`. It solves "docs next to code, one site." It also adds a MkDocs plugin SASE already forbids for Zensical compatibility, and it makes `mkdocs serve` depend on the network. For three public repos you control, it is more magic than you need.

### 8.2 Recommended: assemble in `tools/` from sibling checkouts

Layout:

```
bobs-org.github.io/          # site shell, Pages deploy
  mkdocs.yml
  docs/                      # homepage, overrides, stylesheets, assembled pages
  tools/assemble_docs        # copies + generates
  tools/gen_cli_reference
  .github/workflows/pages.yml

bob-cli/docs/site/           # public pages owned by CLI
  start/install.md
  start/first-capture.md
  …
  concepts/…
  reference/capture-grammar.md   # hand-written, short
  reference/cli/                 # generated into the site repo or into this tree at assemble time

bob-plugins/docs/site/
  guides/deploy-plugins.md
  reference/keymaps/*.md

bob-mac-capture/docs/site/
  start/mac-capture.md          # or a section of the CLI install tutorial
  guides/codesign.md
  reference/protocol.md
```

CI on `bobs-org.github.io`:

1. Check out the Pages repo.
2. Check out the three product repos at `master` (pin to SHAs for reproducibility; a `versions.yml` in the Pages repo lists them, updated by a bot or by hand).
3. Run `tools/assemble_docs` (copy `docs/site/` trees; fail on path collisions).
4. Build `bob` (or download a release) and run `tools/gen_cli_reference --check`.
5. `mkdocs build --strict`.
6. `upload-pages-artifact` + `deploy-pages`.

Product-repo CI runs the same assemble+strict build **without deploy**, so a docs regression fails the PR that caused it. Use a reusable workflow.

Edit links: set Material `repo_url` per page if you split edit URIs; otherwise point the site repo's edit button at the Pages repo and put a "Edit source" line on pages that live elsewhere. SASE uses a single repo, so it does not have this problem. A simple convention: every public page's first HTML comment records `source: bob-cli:docs/site/start/install.md`.

### 8.3 Alternative that is also acceptable

Host the MkDocs project **inside bob-cli** and have its workflow check out plugins and Mac Capture. Deploy to **org Pages** by pushing the artifact with a GitHub App / `peaceiris/actions-gh-pages` into `bobs-org.github.io`, or by making the Pages repo's workflow the only deployer (product repos `repository_dispatch` it).

I slightly prefer a dedicated Pages repo so bob-cli's default branch is not coupled to Pages environment approvals, and so the org URL is obvious in GitHub's UI. If Bryan wants fewer repos, bob-cli-as-shell + dispatch to `bobs-org.github.io` is the same architecture with a different home for `mkdocs.yml`.

**Do not** put mkdocs.yml only in bob-cli and publish as `https://bobs-org.github.io/bob-cli/`. The prefix is a permanent tax on every canonical URL.

### 8.4 README contract after the site exists

Each product README shrinks to:

- One-paragraph what it is
- Install one-liner pointing at the Learn tutorial
- Link to the four doors
- "Developer / agent contracts" link to in-repo `docs/`
- License

The 29k-word Mac README and the plugin walls become Reference sources to mine, then retire from the README.

---

## 9. Beauty (lead design)

Beauty here is **legibility, hierarchy, and a distinctive calm**, not illustration.

### 9.1 Visual tokens

Bob is a tomato, a paper daily note, and ink. Propose:

| Token | Light | Dark |
| --- | --- | --- |
| Surface | `#faf6f1` (paper) | `#161310` |
| Surface strong | `#ffffff` | `#1f1a16` |
| Text | `#1c1917` | `#f5f0ea` |
| Muted | `#57534e` | `#a8a29e` |
| Accent | `#c2410c` (tomato) | `#fb923c` |
| Accent soft | `#ffedd5` | `#431407` |
| Border | `#e7e0d8` | `#3f3a36` |
| Code | `#292524` | `#e7e5e4` |

Material `primary: deep orange` or a custom `palette` with `scheme: default` / `slate`. Font: Material defaults are fine (Roboto). If you customize, pair a humanist sans for UI with a slightly warmer body; do not load four families.

Homepage structure (mirror SASE's HTML-in-Markdown, different copy):

1. **Hero** — kicker "Bob"; h1 one sentence ("A GTD system for Obsidian you drive from the keyboard"); lede; pill "Linux & macOS · Obsidian · CLI"; install command; two buttons (Start the 15-minute path, How Bob works); optional still of the Mac menu-bar capture or the dashboard chips — a PNG, not a video, in v1.
2. **Three surfaces** — CLI, Plugins, Mac Capture, each one card with one link.
3. **Four doors** — Learn / Do / Understand / Look up, SASE copy pattern, Bob destinations.
4. Footer — GitHub org, license, `llms.txt`.

Hide global nav and toc on the homepage (`hide: [navigation, toc]`).

### 9.2 Interaction quality

- Sticky tabs for the four doors.
- Search with suggest + highlight (Material).
- `content.code.copy` on every fence.
- Admonitions only for warnings that prevent data loss (vault sync, ad-hoc codesign wiping Accessibility).
- Screenshots: light and dark of Task Card, dashboard chips, Mac capture window. Record from a **fixture vault**, never from `~/bob`.
- 404.html from Material; no broken promises in nav.

### 9.3 What not to do for "beautiful"

- Do not embed three autoplaying videos.
- Do not invent a custom design system in React (Docusaurus/VitePress) for a docs site this size.
- Do not use tomato on every heading; accent is for links, the kicker, and the primary button.
- Do not clone SASE's extra.css selectors (`.sase-hero`). Name Bob's `.bob-hero`.

---

## 10. Generator and theme choice

| Tool | Fit | Verdict |
| --- | --- | --- |
| **MkDocs + Material 9.7** | What SASE uses; Markdown; search; instant pretty; GH Pages native | **Choose** |
| **Zensical** | Material team's MkDocs successor; MIT; reads mkdocs.yml; GH Pages workflow | **Target later**, not v1. Plugin parity still landing (2026). SASE is already constraining itself to stay compatible. Bob should too, and keep Material as the builder until Zensical is boring. |
| Docusaurus | React, versioning, blog | Heavier than the audience; JS toolchain Bob-cli does not otherwise need |
| VitePress | Beautiful, Vue | Same; weaker Diátaxis convention |
| mdBook | Rust-native | Weaker search and IA; looks like a book, not a product site |
| Sphinx | Python classic | Overkill, less pretty |
| GitHub wiki / raw Markdown | Zero build | No search, no doors, no beauty |

**Constraints borrowed from SASE writing-docs.md:**

- No MkDocs `hooks:` or `gen-files`.
- Plugins: `search` + `redirects` only in v1 (skip blog/rss).
- Generation in `tools/` with `--check`.
- `markdown_extensions`: admonition, attr_list, md_in_html, tables, toc permalink, pymdownx.details, superfences, snippets.

Python is not bob-cli's implementation language, but uv + a docs extra is how SASE builds, and it is the path of least surprise for Material. Pin `mkdocs-material>=9.7,<10` the same way.

---

## 11. Reliability engineering

A docs site that drifts from `--help` is worse than no site.

1. **`mkdocs build --strict`** on every product PR that touches `docs/site/` and on the Pages repo.
2. **CLI reference generator** with drift check. Prefer adding `bob help --format json` (or reusing clap's machine output where clap owns the command) so the generator does not scrape ANSI. Until then, snapshot `bob <cmd> --help` text into fenced generated blocks.
3. **Tutorial runner** against a temporary vault fixture (Dataview-format Tasks settings stub, one area note). Assert exit codes and `expect` substrings, SASE-style. Mark interactive Mac/Accessibility steps `tutorial-test: skip`.
4. **Page budget lint** (copy `tools/check_docs` ideas; do not vendor SASE's whole tool).
5. **Link check** including README URLs that will point at the site (SASE's URL contract test is the model once you have a public URL).
6. **Screenshot golden optional later**; v1 can ship without pictures rather than with stale personal-vault shots.
7. **Do not pin tests to Guide prose.**

Intuitive + reliable + beautiful, in that implementation order: doors and search first, strict build + generated facts second, palette and homepage third. A red build with a pretty hero is not a release.

---

## 12. Phased delivery (always complete)

**Phase 0 — plant (one PR series, days not weeks)**
- Create `bobs-org.github.io`, enable Pages via Actions.
- mkdocs.yml, Material, Bob palette, homepage with four doors (three may list only the pages that exist).
- Assemble script copies empty-or-minimal `docs/site/` from the three repos.
- Tutorial 1 (install) + Concepts hub (eight nouns) + generated CLI index.
- Each README gains a "Docs: https://bobs-org.github.io/" line.
- `llms.txt` stub.

**Phase 1 — a working day (the "excellent" bar for a first public version)**
- Tutorials 2–3.
- The seven guides in §7.2.
- Remaining five concept pages.
- Capture grammar short reference; plugin keymap tables for the three plugins a newcomer must enable (ledger-tools, navigation-hotkeys, task-status-cycler).
- Mac install + codesign guides.
- Tutorial runner in bob-cli CI.
- Writing contract page under Contribute.

**Phase 2 — mine the contracts**
- Split public-facing facts out of `docs/capture.md`, `freshness.md`, `plan.md`, `task-dependencies.md` into Reference pages under budget. Leave vectors in-repo.
- Plugin API namespace tables.
- Mac protocol field list generated from Swift Codable types if practical.
- Reader-testing round (Bryan + 2–3 people). Adjust door labels from evidence.
- Compressed screenshots from the fixture vault.

**Phase 3 — optional polish**
- Custom domain.
- `mike` versioning only if you start shipping tagged user releases that must keep old flag pages.
- Zensical migration when SASE has done it and it is boring.
- PDF handbook only if Bryan wants a printable GTD manual; it is not a docs-quality requirement.
- Cloudflare only if you outgrow Pages headers/redirects.

Diátaxis says publish Phase 0. Do not hold the domain or the keymap tables.

---

## 13. Alternatives considered

| Approach | Why it loses |
| --- | --- |
| Polish READMEs only | No search, no doors, no generated CLI, GitHub renders 29k-word files badly |
| Three project sites | Fragments one product; three searches; prefix URLs |
| Dump existing `docs/` into MkDocs | 222k words of mixed-mode contracts; the opposite of Diátaxis |
| Docusaurus / VitePress | Extra JS stack; versioning unused; SASE already showed Material is enough to be beautiful |
| mdBook in bob-cli | Looks like a Rust book; weak product homepage |
| Host on sase.sh as a subproject | Wrong product, wrong org, wrong audience |
| Obsidian Publish | Paid; vault leakage risk |
| Cloudflare first | Copies SASE's host without SASE's reasons |
| mkdocs-multirepo-plugin | Extra plugin, network builds, Zensical risk |
| Empty four-folder scaffold | Explicitly condemned by Diátaxis |
| Wait for a custom domain | The github.io org URL is already a real website |

---

## 14. Risks

- **Agents keep writing into `docs/capture.md`.** Mitigate with the writing contract: public pages live under `docs/site/`; contracts stay where tests point. A lint fails a `docs/site/` page over budget.
- **Org Pages repo becomes a dump.** Mitigate: it holds shell + assemble only; content PRs land in the product repo that owns the fact.
- **Generated CLI pages are ugly.** Invest in the generator (tables for flags, short description from clap `about`). Worth more than hand-written flag prose.
- **Tutorial needs a real vault schema.** Getting-started already lists Tasks status registry requirements. The fixture must include that JSON or the tutorial lies.
- **Mac Capture tutorials cannot run in Linux CI.** Skip with an explicit marker; Bryan walks them on the Mac after install-all changes, analogous to SASE's real-provider checklist.
- **Public site leaks GTD internals Bryan does not want public.** The repos are already public; the site makes them discoverable. If that is a problem, the adjustment is "do not build a homepage that markets Bob," not "stay on 54k-word files." A quiet, accurate site is enough.

---

## 15. Recommended solution (normative)

1. **Product:** one public documentation site, **Bob**, covering bob-cli + bob-plugins + bob-mac-capture.
2. **Compass:** Diátaxis, with SASE door names (Learn / Do / Understand / Look up) and SASE writing rules (directory is type, budgets, generated reference, tutorial tests).
3. **Host:** GitHub Pages, org site, repo `bobs-org/bobs-org.github.io`, URL `https://bobs-org.github.io/`, official Actions deploy, free HTTPS. Custom domain later.
4. **Builder:** MkDocs Material 9.x, `strict: true`, plugins limited to search + redirects, generation in `tools/`, Zensical-compatible config.
5. **Sources:** public pages in each product repo under `docs/site/`; assemble in CI; existing `docs/*.md` remain in-repo contracts and are not the site.
6. **First publish:** complete-small (homepage, install tutorial, nouns hub, CLI index). Then a working-day set. Then mine contracts.
7. **Look:** tomato/paper Material customization, SASE-like homepage structure, PNG hero, dark mode via `prefers-color-scheme`.
8. **Agents:** `/llms.txt`; do not replace `AGENTS.md`.
9. **Out of v1:** blog, PDF, Cloudflare, three sites, empty quadrants, custom domain, Zensical-as-builder, publishing the private vault.

This is a good idea at that scope. It is a bad idea as a big-bang "document everything to SASE's current depth." Diátaxis is the cure for that impulse: take the next small improvement, publish it, repeat.

---

## 16. Sources

### External (fetched)

- [Diátaxis](https://diataxis.fr/), [Start here](https://diataxis.fr/start-here/), [How to use Diátaxis](https://diataxis.fr/how-to-use-diataxis/), [Applying Diátaxis](https://diataxis.fr/application/)
- [sase.sh](https://sase.sh) homepage and Get started
- [GitHub Pages: what it is](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [Custom workflows with GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [Material for MkDocs: publishing](https://squidfunk.github.io/mkdocs-material/publishing-your-site/)
- [Zensical](https://zensical.org) / Material blog announcement; Zensical publish-your-site (GitHub Pages)
- [mkdocs-multirepo-plugin](https://github.com/jdoiro3/mkdocs-multirepo-plugin)

### Local checkouts (via `sase repo open`)

- `sase-org/sase`: `mkdocs.yml`, `.github/workflows/docs-deploy.yml`, `wrangler.jsonc`, `docs/index.md`, `docs/content_layout.md` (stub), `docs/contribute/writing-docs.md`, `docs/contribute/reader-testing.md`, `docs/start/index.md`, `docs/guides/index.md`, `docs/concepts/index.md`, `docs/reference/index.md`, `docs/stylesheets/extra.css`, `docs/overrides/main.html`, `docs/_redirects`, `docs/_headers`, `Justfile` docs recipes, `requirements-docs.txt`
- bob-cli: `README.md`, `docs/README.md`, `docs/getting-started.md`, word/byte counts of all `docs/*.md`
- bob-plugins: `README.md`, plugin list
- bob-mac-capture: `README.md` (first ~120 lines + word count)

### GitHub API / `gh`

- `gh repo list bobs-org` — product repos public; vault `bob` private; no `bobs-org.github.io`
- `gh api repos/bobs-org/{bob-cli,bob-plugins,bob-mac-capture}/pages` — 404, Pages not enabled

### Project memory

- `cli_rules.md` — `--help` quality, frozen command names
- `sase_artifacts.md` — snapshot registration for this report
- Decision roster (in agent instructions): `mac-capture-is-a-thin-client`, `task-lanes-are-sticky`, `today-is-read-from-the-ledger`, and related records as the concept-page source of *why*

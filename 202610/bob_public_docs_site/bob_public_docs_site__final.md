# Bob public documentation: one Diátaxis site on GitHub Pages

Consolidated research report · lead researcher · 2026-10-19

Scope: public documentation for `bobs-org/bob-cli`, `bobs-org/bob-plugins`, and
`bobs-org/bob-mac-capture`. Out of scope: the private vault repo `bobs-org/bob`, the SASE
sidecars, and `AGENTS.md`.

Inputs: five independent reports (`__cdx`, `__cld`, `__grk`, `__mus`, `__gem`, in this
folder) and my own verification of the points where they disagreed or rested on weak
evidence. Local facts were checked at bob-cli `bfca3419`, bob-plugins `ef1a63c`,
bob-mac-capture `f7e635a`, and sase-org/sase `110214f51c`. External facts were checked
on 2026-10-19.

---

## Decision in brief

**Yes, build it. But the main job is to reorganize and present the roughly 30,000 lines
of Bob documentation that already exist, not to write more.** Every researcher agreed
on that framing. They also agreed that Bob should get **one site**, not three, and that it
should grow in small published steps rather than as a big-bang rewrite.

My recommendation:

| Decision | Choice |
| --- | --- |
| Shape | **One site for the Bob system.** CLI, Obsidian plugins, and Mac Capture are surfaces of one product. They appear as reference sections and page tags, not as three manuals. |
| URL and host | **`https://bobs-org.github.io/`**, the organization Pages site, served free by GitHub Pages. A custom domain can come later with one setting. |
| Where the source lives | **With the code.** Site config, homepage, and system-wide pages live in **bob-cli**. Plugin reference lives in `bob-plugins/docs/` and Mac reference in `bob-mac-capture/docs/`. Both are mounted into the build. A new, nearly empty `bobs-org.github.io` repo only publishes. |
| Generator | **Zensical** (from the Material team; its dependable 0.1 line starts 2026-11-05) reading a `mkdocs.yml` that stays **Material-9.7-compatible**, so Material 9.7 remains a fallback builder. **Astro Starlight** is the runner-up. |
| Information architecture | Tabs **Get started · Guides · Concepts · Reference · Develop**, with homepage doors **Learn / Do / Understand / Look up**, matching sase.sh. |
| Existing docs | **Publish the 26 existing guides in `bob-cli/docs/` unchanged, as "Contracts"**, under the Develop tab. Their URL follows their path (`docs/capture.md` → `/capture/`). New reader-facing pages go into typed subdirectories. **Don't move or rewrite the contracts.** |
| Beautiful | **Build on Bob's existing identity:** the bullet-"b" mark, teal, tomato reserved for Today, and the Inter and JetBrains Mono fonts already in the repo. Show task lines the way Bob renders them. Take screenshots only from a synthetic demo vault. |
| Reliable | Strict build plus an independent link and anchor check. Generate facts (CLI, plugin inventory, glossary) with drift checks. Test the tutorial against a demo vault. Freeze the URL set. Publish hourly from recorded source SHAs. **The last good site always stays live.** |
| Prerequisites | **Add a LICENSE** to bob-cli and bob-mac-capture, which have none. Fix the stale public claims in the plugins README. |

---

## 1. Where the researchers disagreed, and how I resolved it

| Question | cdx | cld | grk | mus | gem | **Resolution** |
| --- | --- | --- | --- | --- | --- | --- |
| Generator | Starlight | **Zensical**, Material fallback | Material 9.7, Zensical later | Material | Material | **Zensical on Material-compatible `mkdocs.yml`** (§6) |
| URL | org root | org root | org root | `/bob-docs/` project site | `/bob-cli/` project site | **Org root** (§5.2) |
| Site shell lives in | the `bobs-org.github.io` repo | **bob-cli** | the `bobs-org.github.io` repo | new `bob-docs` repo | bob-cli | **bob-cli**, with a thin deploy repo (§7) |
| Product content lives in | each repo's `docs/` | each repo's `docs/` | new `docs/site/` per repo | moved into `bob-docs` | all in bob-cli | **Each repo's `docs/`** (§7) |
| Existing `docs/*.md` | publish while splitting | **move** to `docs/contracts/` | keep in repo, don't publish | move verbatim | split into quadrants | **Publish in place as Contracts; no move** (§7.3) |
| Publish trigger | manual, pinned manifest | cross-repo dispatch with an org token | push / pinned SHAs | push | push | **Hourly poll with a recorded manifest, plus manual publish; no cross-repo secret** (§5.3) |
| Look | paper, ink, tomato, teal | Bob's own teal, tomato, and fonts | tomato on paper | sase's look | slate and tomato | **Bob's own identity, with contrast-checked tokens** (§9) |

Errors and weak points in the inputs, corrected here:

- **gem** says Pages' soft limit of 10 builds per hour applies. GitHub says it does not
  apply to custom Actions workflows. gem's other claims also don't hold up:
  - It calls Material "unequivocally superior" without noting that Material's
    maintenance ends on 2027-05-05.
  - It proposes writing plugin and Mac reference inside bob-cli, the drift pattern
    gem itself warned against.
- **mus** says custom domains work "via a `CNAME` file". When a site is published by a
  custom Actions workflow, GitHub ignores the CNAME file, and the domain is set in
  Settings → Pages ([GitHub][gh-domain-manage]). mus also moves bob-cli's docs into a
  separate repo, which separates docs from code.
- **grk** contradicts itself. Its §4.1 says to reuse sase's Learn / Do / Understand /
  Look up doors, but its §2J says those doors "would read as a fork". I keep the doors:
  the identity comes from visuals and copy, and shared labels help Bryan and his agents
  move between the two sites.
- **cld** proposed moving the 26 contracts into `docs/contracts/` and updating about 440
  references. I verified the reference counts, and they argue against the move (§7.3).
- **cdx** recommended Starlight because Material is ending. That is a fair premise, but
  Zensical answers it without abandoning sase's config dialect and tooling (§6).

---

## 2. What exists today (verified)

| Fact | Evidence | Consequence |
| --- | --- | --- |
| bob-cli has a 1,584-line README plus 27 files in `docs/` (26 guides and an index), about 25,100 lines. `capture.md` alone is 6,371 lines (about 55k words). | `wc -l`; grk word counts | Volume is not the problem; findability and mixed modes are. |
| Many of those guides are **contracts**: specs with conformance vectors that Rust and JavaScript tests mirror (`freshness.md`, `plan.md`, `today-marks.md`…). | cld; `docs/README.md` says "detailed contracts" | They are a legitimate reference genre for implementers, not tutorials. |
| bob-mac-capture's README is about 191 KB and 2,807 lines. Install steps, protocol compatibility, keyboard, and troubleshooting are all in one file. | all reports | It needs splitting into pages. |
| bob-plugins has 7 plugins and no `docs/` directory. Its README (about 74 KB) says "six plugins" (lines 5, 556), calls itself a "**private personal monorepo**" (line 571), links to `bbugyi200/bob-cli` (line 552), and says `bob-navigation-hotkeys` is "ahead … at `2.7.2`" while the manifest says `2.46.1`. | `grep` at `ef1a63c` | These hand-maintained facts have drifted. Generate them, and review public-facing claims. |
| All three repos are **PUBLIC**. Pages is not enabled on any of them (API returns 404). `bobs-org/bobs-org.github.io` does not exist. | `gh repo view`, `gh api …/pages` | Pages is free here. The org-root name is available. |
| **bob-cli and bob-mac-capture have no LICENSE.** bob-plugins is MIT. | `ls LICENSE*`; GitHub contents API | A public install guide for code under "all rights reserved" sends a mixed message. |
| bob-cli and bob-plugins have **no `.github/`, so no GitHub Actions at all**. Mac Capture has `ci.yml` (macOS 26). | `ls .github` | Quality gates run locally (`just`) and at publish time. Don't bootstrap CI just for docs. |
| `docs/<stem>.md` paths are mentioned in code and tests: 174 times in bob-cli `src/`, 25 in bob-cli tests, 334 in bob-plugins test scripts (mostly comments citing contract sections), and 26 in Mac Capture. Help and error text print some of them, such as "See docs/stats.md…" and `docs/vault-git-sync.md#halted-sync`. | `grep -rhoE 'docs/[a-z0-9_-]+\.md'` | Moving the contract files is expensive. A `docs/X.md` → `/X/` URL rule makes every existing mention resolvable on the site. |
| Only **6** relative links in `docs/*.md` point outside `docs/`: 4 to `../README.md` and 2 to `tests/fixtures/…`. | `grep` | The contracts can be published as-is after a 6-link fix. |
| 4 commands hand-print their help (`notify`, `pomodoro`, `nightly`, `collect_done`); the rest use clap. | `grep print_help` | A clap-only reference generator would miss those 4 commands. |
| `sase/memory/` (glossary: 18 terms; decisions: 24 records) is tracked in bob-cli, so it is already public. | `git ls-files` | Glossary and Design decisions pages can be generated without disclosing anything new. |
| A visual identity already exists: <ul><li>the bullet-"b" mark (`StatusItemGlyph.swift`);</li><li>the identity teal, about `#0a9391` light and `#79dedc` dark (`docs/task-tag-marks.md:87`);</li><li>the Today tomato;</li><li>OFL fonts bundled in `assets/print_fonts/`: Inter, Inter Display, Source Serif 4 SmText, JetBrains Mono, and Noto Emoji.</li></ul> | `ls`, `grep` | You don't need to invent a brand. |
| bob-cli already ships a small `vault/` fixture (Tasks plugin `data.json` and `day.md`), and `tests/fixtures/` holds more. | `git ls-files vault` | A seed for the synthetic demo vault. |
| sase.sh runs MkDocs with Material (`mkdocs-material>=9.7,<10`). Its writing contract says the site "builds on any Zensical-compatible host: add no MkDocs `hooks:`, `gen-files`…" (`docs/contribute/writing-docs.md:105`). It deploys to a **Cloudflare Worker**, not to GitHub Pages. | sase checkout | Copy sase's contract and its Zensical-compatible discipline. Its host is not a precedent for Bob. |

---

## 3. Critique: is this a good idea?

**Yes, with five conditions.** Unless they hold, the project produces either a pretty
facade over stale content or a maintenance burden.

### Why it is worth doing

- **The material exists, but it is undiscoverable.** There is no cross-repo search, no
  navigation beyond one index page, and no build that fails when a link breaks.
- **The pages mix modes.** Diátaxis warns that when the distinctions blur, "the
  different kinds of documentation bleed into each other" ([map][dx-map]). Bob's docs do
  this everywhere:
  - The README's Installation section mixes a how-to, reference, troubleshooting, and
    explanation.
  - Each plugin table cell holds a whole behavior spec.
  - Mac Capture's Requirements section is a protocol changelog.

  Fixing this pays off even without a website. The site makes the fix visible,
  searchable, and attractive.
- **The real readers benefit immediately:**
  - **Bryan's agents** read `docs/` and the READMEs on every change, and they pay for
    unfocused pages in tokens and in wrong edits.
  - **Bryan, months from now**, trying to remember how a feature works.
  - **Curious visitors** arriving from sase, GitHub, or a shared link.

  The repos have one star each and no releases. Write for these three readers, not for
  a mass market.

### The five conditions

1. **One source of truth.** The site renders the same in-repo Markdown that agents and
   GitHub read. Never write prose that exists only on the site.
2. **Facts are generated, not hand-copied.** The plugins README's stale version string
   and plugin count prove the need.
3. **The site grows in small, complete steps.** The Diátaxis guidance says to use it
   "as a guide, not a plan", never to create empty quadrant structures ("Don't do that.
   It's horrible."), and to publish every improvement ([how to use][dx-how]).
4. **Contracts stay contracts.** Don't force 25k lines of implementer specs into user
   pages. Publish them in their own clearly labeled area, and write short reader pages
   that link to them.
5. **The site is honest about who Bob is for.** Bob is an opinionated GTD workflow for
   one Obsidian setup. It needs Tasks-plugin configuration, the custom plugins, a Rust
   toolchain, and, for Mac Capture, macOS 26 and a source build. An "Is Bob for me?"
   page beats a marketing hero.

### Main failure modes and their mitigations

| Risk | Mitigation |
| --- | --- |
| Big-bang rewrite stalls; four empty tabs ship | Each phase publishes. A tab appears only when it has real pages. |
| Dumping 25k lines into the reader doors | Contracts get their own section with a banner. Reader pages have word budgets (sase's ceilings). |
| Copying sase's machinery (442 pages, blog, PDF, Cloudflare, seven docs tools) | Copy the **contract** (directory = type, templates, budgets, routing table, generated reference, URL contract, reader tests), not the machinery. |
| Drift: Bob changes daily | Generate facts. Keep guides few and short. Tests never pin guide prose. A routing table says which page a change updates. |
| Privacy: screenshots tempt use of the real vault | A synthetic demo vault is the only source for examples and images, enforced by a privacy lint. |
| Documenting a personal workflow as a general product | State the supported baseline (OS, Obsidian and Tasks versions, component SHAs). Narrow the tutorial rather than hide gaps. |
| Publication machinery eats the project | One assembler, one manifest, one build. No CMS, versioning, hosted search, chat bot, or PDF in v1. |

### Would I take a different approach?

Partly. Here is what I would change about the request as literally written:

- **"Docs for all of the repos" → docs for one product.** A newcomer should not have to
  learn the repo boundaries before learning the system. Capture alone crosses all three
  repos: the Mac panel, the CLI grammar, and the plugin rendering.
- **"Like sase" → sase's editorial contract, not its stack or host.** Material is in
  maintenance mode until 2027-05-05, and sase itself already restricts itself to the
  Zensical-compatible subset.
- **"Excellent" → correct, findable, honest, and verified.** Excellence does not mean
  "comprehensive on day one".

The cheapest alternative, cleaning up READMEs with no site, was considered by every
report and rejected. It gives no cross-repo search, no navigation, and nothing
beautiful. The cleanup should still happen as part of this plan.

---

## 4. Requirement adjustments (explicitly called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| **A1** | Docs for all public Bob repos | **One site for the Bob system.** Repos appear as components (reference sections and page tags), not as top-level sections. Each README becomes a short front door. | Readers' tasks cross the repo boundaries. Diátaxis warns that organizing a portfolio by product causes "wild inconsistency" ([map][dx-map]). |
| **A2** | Diátaxis-inspired | **Use it as an editorial discipline and an iterative workflow.** The first publish is complete but small. Diátaxis types apply page by page, and tabs appear only when they have real pages. | That is what [how to use Diátaxis][dx-how] prescribes. |
| **A3** | Like sase's docs | **Adopt sase's contract:** <ul><li>directory = type;</li><li>templates;</li><li>budgets;</li><li>hygiene;</li><li>a routing table;</li><li>generated reference with `--check`;</li><li>a URL contract;</li><li>reader tests.</li></ul>**Skip:** Cloudflare, blog, PDF, analytics. **Swap the builder** to Zensical. | The contract is sase's most valuable part. Its host and extras serve sase's needs, not Bob's. |
| **A4** | (implied) rewrite the existing docs | **Publish the existing contracts unchanged in a Develop → Contracts area.** Write new reader pages beside them and link to the contracts. Split a contract only when a reader need demands it. | This is cheap, keeps tests and agents stable, and gives day-one search over the most-consulted material. |
| **A5** | (unstated) audience | **Name the audiences:** a technically capable Obsidian user, plus Bryan and his agents as maintainers. **Add an "Is Bob for me?" page.** | Tutorial depth and tone depend on the audience. |
| **A6** | (unstated) | **Add a synthetic demo vault** as a documentation fixture. It feeds both the tutorial and every screenshot. | It makes the tutorial reproducible and protects the private vault. |
| **A7** | (unstated) | **Add LICENSE files** to bob-cli and bob-mac-capture as a prerequisite. MIT matches bob-plugins. | A public install guide for unlicensed code is a mixed message. |
| **A8** | Reliable | **Make generated reference, a strict build, link and anchor checks, a tested tutorial, and a frozen URL list requirements, not extras.** | Bob changes daily. Without these, "reliable" is impossible. |
| **A9** | Host on github.io | **Yes, at the org root (`bobs-org.github.io`).** Add a custom domain later; it cascades to project sites. Don't buy a domain now. | §5.2 |
| **A10** | (implied) everything | **Out of v1:** <ul><li>versioning;</li><li>blog;</li><li>PDF;</li><li>analytics;</li><li>PR preview sites;</li><li>Cloudflare;</li><li>an interactive capture playground;</li><li>a mobile-support claim;</li><li>an official community-plugin listing.</li></ul> | bob-cli is `0.1.0` with no tags. Each item is a later add-on with a stated trigger, not a redesign. |
| **A11** | Beautiful | **Beauty means:** <ul><li>reading quality (measure, rhythm, search, code blocks, dark mode, accessibility);</li><li>Bob's own identity;</li><li>a few real examples.</li></ul>It does not mean custom React or video heroes. | A striking homepage cannot make up for dense or unreliable pages. |

---

## 5. Hosting

### 5.1 Is GitHub Pages free here? Yes.

- Pages serves **public repos on GitHub Free**, including Free organizations. All three
  Bob repos are public. Actions minutes on standard runners are free for public repos.
  **Total cost: $0** ([what is Pages][gh-what]).
- Limits ([limits][gh-limits]):
  - The published site may be at most 1 GB.
  - Bandwidth has a soft limit of 100 GB/month.
  - Deployments time out after 10 minutes.
  - The soft limit of 10 builds/hour "does not apply if you build and publish your site
    with a custom GitHub Actions workflow".
  - Pages must not be used for commercial transactions or SaaS. A docs site is fine.
  - These limits are generous for text and compressed images, but don't put app
    binaries or large videos in the site.
- HTTPS is automatic on `*.github.io`.

### 5.2 URL: use the organization root

| Option | URL | Verdict |
| --- | --- | --- |
| **Org site**, repo named exactly `bobs-org.github.io` | `https://bobs-org.github.io/` | **Recommended.** The `bobs-org` org *is* Bob, so the docs site *is* Bob's website. That is the sase.sh pattern: homepage and docs in one site. |
| Project site on bob-cli (gem) | `/bob-cli/` | Frames the system as "the CLI docs", and the prefix becomes a permanent URL contract. |
| Project site `bob-docs`, reserving the apex (mus) | `/bob-docs/` | Reserves the root for a landing page that would duplicate the docs homepage. |
| Three project sites | three URLs | Three searches and unchecked cross-site links. Every report rejected this. |
| Project site named `bob` | — | **Never.** `bob` is the private vault repo. |

**Adding a custom domain later is a one-setting change.** Setting a custom domain on the
org site makes GitHub serve all of the org's project sites under it too
([about custom domains][gh-domain-about]). With Actions publishing, configure the domain
in Settings → Pages (or through the API); a `CNAME` file "is ignored and is not
required" ([managing a custom domain][gh-domain-manage]). Keep `site_url` in one place.
Verify the domain at the org level to prevent takeover.

### 5.3 Publishing: an hourly poll with no cross-repo secrets

`actions/deploy-pages` publishes the Pages site of the repo whose workflow runs. GitHub's
docs describe the flow per repository; I found no cross-repo deploy, and every report
assumes the same. So the org site's deploy workflow must live in `bobs-org.github.io`.
Two facts shape the trigger:

- The default `GITHUB_TOKEN` is scoped to its own repository. A push in bob-cli
  therefore cannot dispatch a workflow in another repo without a stored PAT or GitHub
  App (cld's design).
- bob-cli and bob-plugins have no Actions at all today.

**Recommended trigger: an hourly poll plus a manual trigger.** The deploy repo's
`publish.yml` runs on a cron at an odd minute (for example `17 * * * *`) and on
`workflow_dispatch`:

1. Run `git ls-remote` on the three source repos.
2. Compute the docs-input fingerprint: each repo's `HEAD:docs` tree hash, plus bob-cli's
   `mkdocs.yml` and `tools/docs`.
3. If the fingerprint matches `published.json`, exit within seconds.
4. Otherwise, check out the three repos at those SHAs read-only, run `just docs-build`,
   and run the gates (§10).
5. Upload the Pages artifact and deploy it.
6. Commit the new `published.json`, recording the SHAs, toolchain versions, and time.

Properties of this design:

- **No secrets.** Every source repo is public.
- **Reproducible.** `published.json` is a publication log: "what was live on date X".
- **Rollback** means reverting `published.json` and dispatching.
- **Fail-safe.** A failed gate never deploys, so the last good site stays live. The run
  opens or updates a single "Docs publish blocked" issue and closes it on the next
  success, instead of failing loudly every hour.
- **Immediate publish.** `just docs-publish` in bob-cli runs
  `gh workflow enable publish.yml -R bobs-org/bobs-org.github.io && gh workflow run …`
  with Bryan's own `gh` login.

Caveat: "In a public repository, scheduled workflows are automatically disabled when no
repository activity has occurred in 60 days" ([disable workflows][gh-disable]). GitHub
does not define "activity". Bot commits of `published.json` are the usual community
answer, but that is unverified. The `gh workflow enable` step in `docs-publish` is the
backstop, and the workflow state `disabled_inactivity` is detectable through the API. If
under-an-hour latency ever matters, add cld's dispatch: a fine-grained PAT or a GitHub
App as an org secret.

### 5.4 Alternatives to GitHub Pages

| Host | Why not for v1 | Reconsider when |
| --- | --- | --- |
| Cloudflare Pages or Workers (sase's host) | Needs an extra account, an API token, and Wrangler | You need per-PR preview URLs, `_headers`/`_redirects`, or a domain already on Cloudflare |
| Read the Docs | Extra account and branding; versioning is unused | You maintain several release lines |
| Netlify or Vercel | Extra vendor | Preview URLs become the bottleneck |
| Obsidian Publish or Quartz | Publish is paid; Quartz is a digital-garden tool with weak structured navigation; both invite mixing in the private vault | Never, for this purpose |

---

## 6. Generator

### 6.1 The ecosystem as of 2026-10-19 (verified)

- **Material for MkDocs** is in maintenance mode. Critical fixes run **through
  2027-05-05**, an extension that was announced; sites keep working after that
  ([Zensical upcoming changes][zen-up]; [EOL issue][mat-eol]). MkDocs 2.0 drops plugins
  and is incompatible with Material ([Material blog][mat-mk2]).
- **Zensical** comes from the Material team and is MIT-licensed:
  - Latest release is 0.0.71 (2026-10-16, alpha). "On November 5, 2026, Zensical 0.1.0
    will begin a dependable release line" ([upcoming][zen-up]; [PyPI][zen-pypi]).
  - It "reads the existing `mkdocs.yml`". The only unsupported setting is `hooks`.
    `theme.custom_dir`, `extra_css`, and a `classic` variant for Material migrations all
    work ([migration][zen-mig]).
  - These plugins are native ([plugins][zen-plugins]): search (a new, non-Lunr engine),
    **redirects (including anchor-based redirects for split pages)**, tags, blog, rss,
    **llmstxt**, social, offline, and macros.
  - `gen-files` is **not** supported.
  - **Unlisted plugins are "silently ignored".**
  - Link and anchor validation is on by default. `--strict` aborts the build on issues
    ([validation][zen-val]).
  - Multi-project composition and native versioning are **roadmap only**, and the
    roadmap "does not promise delivery dates" ([roadmap][zen-road]).
- **Astro Starlight** is healthy and good-looking. It includes Pagefind search and is
  still at 0.x. Cloudflare acquired the company behind Astro in January 2026 and
  committed to keeping it open source ([press release][astro-cf]).

### 6.2 Comparison

| Option | Beauty out of the box | Fit for a multi-repo Diátaxis site | Longevity | Fit with Bryan's ecosystem | Verdict |
| --- | --- | --- | --- | --- | --- |
| **Zensical on `mkdocs.yml`** | High (Material design, classic or modern variant) | Tabs, indexes, tags, strict validation, anchor-aware redirects; multi-repo via a pre-build copy | 0.x, but a dependable line from Nov 5; same team | **Same config dialect and contract as sase.sh**; agents already know it | **Recommended** |
| Material 9.7 | High | Same | Maintenance ends 2027-05-05 | Identical to sase | **Fallback builder only** (same config) |
| Astro Starlight | Very high | Good; per-page edit links; Pagefind | Healthy 0.x; owned by Cloudflare | A second docs dialect and Node build; no shared contract tooling with sase | **Runner-up**. Choose it if interactive components (for example a WASM capture-grammar playground) become central. |
| Docusaurus | Good | Strong versioning | Mature | Heavy React stack; versioning unused | No |
| VitePress, mdBook, Sphinx, Antora | — | — | — | Weaker product homepage or IA (mdBook); Vue or AsciiDoc costs | No |

Practically, the three Material votes (grk, mus, gem) and the Zensical vote (cld) are the
same decision: one `mkdocs.yml`, two possible builders. Building with Zensical from the
start avoids a forced migration in May 2027, and the Material fallback limits the risk
of Zensical's youth.

**Rules this choice implies:**

- Keep the config to the intersection of Material 9.7 and Zensical.
- Allow only the `search`, `redirects`, `tags`, and `llmstxt` plugins, enforced by a
  lint, because Zensical silently ignores anything else.
- No `hooks:` and no `gen-files`. All generation runs in `tools/docs/` before the build,
  with its output committed.
- Use `variant: classic` at first.
- Pin Zensical through a uv lockfile.
- Keep a `just docs-build-material` path that CI exercises weekly, so the fallback stays
  real.

**Decision gate:** if the Phase 1 slice (§11) does not build cleanly on Zensical 0.1.x,
launch on Material 9.7 with the same files and revisit later. That costs no content
change.

---

## 7. Architecture: where content lives and how it is assembled

### 7.1 Ownership

| Content | Canonical home |
| --- | --- |
| Site config (`mkdocs.yml`), theme overrides, CSS, homepage, docs tooling (`tools/docs/`) | **bob-cli** |
| System-wide tutorials, how-to guides, and concepts | **bob-cli** `docs/{start,guides,concepts}/` |
| CLI reference (generated), capture syntax, vault format, config and environment, JSON outputs, glossary and decisions (generated), compatibility | **bob-cli** `docs/reference/` |
| The 26 existing contracts | **bob-cli** `docs/<stem>.md`, **unchanged** |
| Plugin reference: per-plugin commands, hotkeys, settings, and API namespaces | **bob-plugins** `docs/` |
| Mac Capture reference: install and signing, keyboard, settings, permissions, diagnostics, runtime protocol | **bob-mac-capture** `docs/` (split out of the README) |
| The publish workflow and `published.json` | **`bobs-org.github.io`**. That's the whole repo, plus a README that says "source lives in bob-cli". |

**Why the shell lives in bob-cli rather than the deploy repo (contra cdx and grk):**

- Agents work in bob-cli workspaces, and `just docs-serve` there previews the whole site.
- bob-cli already orchestrates its siblings (`just install-all`).
- The glossary and decisions memory webs live in bob-cli.
- Site edits don't need a fourth repo opened.

Readers never see this choice, because the URL is the org root, so cdx's concern about
the CLI looking primary does not apply.

**Shared grammar has one owner.** Capture grammar is documented in bob-cli. Mac pages
explain how to use it through the panel and link to it. This follows the
`mac-capture-is-a-thin-client` decision.

### 7.2 Source layout

```text
bob-cli/
├── mkdocs.yml                     # Zensical-built, Material-9.7-compatible
├── tools/docs/                    # uv project: assemble, gen_cli, gen_plugins,
│                                  #   gen_glossary, lint, tutorial runner
└── docs/
    ├── index.md                   # homepage
    ├── start/  guides/  concepts/  reference/  develop/    # new typed reader pages
    ├── capture.md  freshness.md  plan.md  …                # 26 contracts, unchanged → /capture/ …
    ├── README.md                  # in-repo hub for GitHub/agents; excluded from the site
    ├── overrides/  stylesheets/  assets/
    ├── reference/plugins/         # ← mounted copy of bob-plugins/docs (gitignored)
    └── reference/mac-capture/     # ← mounted copy of bob-mac-capture/docs (gitignored)
bob-plugins/docs/                  # index.md + <plugin-id>.md (generated tables + short prose)
bob-mac-capture/docs/              # split from the 191 KB README
bobs-org.github.io/                # .github/workflows/publish.yml, published.json, README.md
```

### 7.3 Contracts stay where they are (contra cld)

**URL rule: a page's path is its URL.** `docs/X.md` publishes as `/X/`, and
`docs/guides/y.md` as `/guides/y/`. Reasons:

- **Every existing mention keeps working.** There are about 560 `docs/X.md` mentions
  across help text, error messages, test comments, plans, beads, and memory, and 14
  concurrent workspaces. With this rule, each mention maps 1:1 to a live URL. No
  `sed` over three repos, no in-flight branch conflicts, and no agent-memory churn.
- **Nothing to rewrite.** Relative links resolve identically on GitHub and on the site.
  Only the 6 links that escape `docs/` need a one-time edit, to absolute GitHub URLs.
- **No ambiguity for readers.** cld's concern was that a reader could mistake
  `/freshness/` for a guide. Fix it with two things:
  - a template banner on every root-level page: "Contract · written for implementers ·
    Looking to *review your tasks*? → Guide";
  - placing contracts in the nav under Develop → Contracts.
- **Splitting later is easy.** When a contract later becomes a reference page plus a
  concept page, the contract URL survives. The new pages are additions, not moves.

Two smaller gotchas:

- Exclude `docs/README.md` from the site. With `index.md` present, MkDocs-style builders
  skip it with a warning, and `--strict` turns that warning into a failure.
- Lint for collisions: no contract stem may equal a typed directory name.

### 7.4 Assembler rules (deliberately narrow)

- **A fixed mount table.** `bob-plugins/docs/**` goes to `docs/reference/plugins/`, and
  `bob-mac-capture/docs/**` goes to `docs/reference/mac-capture/`.
  - The copies are gitignored, so `rg` skips them and agents don't grep stale copies.
  - No regex link rewriting.
  - Fail on any path collision or escape.
- **Find each sibling in this order:** an explicit env var, then `../<repo>` (the
  `install-all` layout), then `sase/repos/linked/<repo>` (agent workspaces), then a
  shallow clone into `~/.cache/bob-docs/`. **Never silently skip a sibling.**
- **Production refuses local overrides.** Plugin and Mac repos get a `just docs-check`
  that previews their uncommitted docs against bob-cli at its current head.
- **Stamp provenance.** The assembler writes `source:` front matter into the mounted
  copies, so a small template override points "Edit this page" at the owning repo and
  path. Verify that page metadata is readable in Zensical's MiniJinja templates.
- **Link rules:**
  - Same-repo links are relative and work on GitHub too.
  - Cross-repo links are relative to the assembled tree and are validated by the strict
    build. They are rare.
  - READMEs use absolute site URLs.

---

## 8. Information architecture

### 8.1 Tabs and doors

| Tab | Diátaxis type | Directory | At first publish (✓) and soon after |
| --- | --- | --- | --- |
| Home | — | `index.md` | ✓ Hero, four doors, "a Bob day", components |
| **Get started** (Learn) | Tutorial | `start/` | Is Bob for me? · Install Bob · Your first Bob day (demo vault) · Continue in Obsidian · Continue with Mac Capture |
| **Guides** (Do) | How-to | `guides/` | Goal-titled, grouped: *Set up · Capture · Plan the day · Projects and dependencies · Reading · Fix problems* |
| **Concepts** (Understand) | Explanation | `concepts/` | How Bob fits together (one system diagram) · Tasks and lanes · Today and the Pomodoro ledger · Freshness and the review walk · Projects and dependencies · The reference library · Why the vault syncs through git |
| **Reference** (Look up) | Reference | `reference/` | ✓ CLI (generated) · Capture syntax (short, with a searchable token index) · Vault format (task-line anatomy, statuses, fields) · Configuration and environment · JSON outputs · Obsidian plugins (per plugin) · Mac Capture · ✓ Glossary (generated) · Compatibility |
| **Develop** | Contributor | `develop/` + root contracts | ✓ Contracts (26) · ✓ Design decisions (generated) · Build each repo · Writing docs |

- **Keep sase's tab names and door labels.** Bryan and his agents move between both
  sites, and Bob's visual identity (§9) keeps the two from reading as a fork.
- **"Develop" rather than "Contribute".** Bob has no outside contribution process, and
  the section's main content is implementer contracts.
- **Show only populated tabs.** A tab appears once it has real pages; Diátaxis says
  never ship empty quadrants.

### 8.2 Starting content

**Guides**, titled with the reader's goal. These are harvested from today's README and
contracts:

- Install everything with one command
- Point bob at your vault
- Deploy the Obsidian plugins
- Install Bob Mac Capture and grant Accessibility
- Capture a task from anywhere on your Mac
- Add prerequisites while capturing
- Save a link to your reading queue
- Run the morning review walk
- Keep Ready lanes under their cap
- Sync the vault across machines
- Resolve a vault-sync conflict copy
- Recover a stuck reference job
- Drain Google Keep into tasks
- Fix "bob not resolved" in Mac Capture

**Concepts hub: eight core nouns** (adapted from grk), taught before any other term:

1. Vault
2. Task
3. Lane (Ready / Next / In Progress / Blocked)
4. Pomodoro (and its Task Links)
5. Capture
6. Freshness
7. Project
8. Plugin

Present Mac Capture on the hub as a sibling program. Other terms link to the glossary.
Concept pages take their *why* from the decision records and cite behavior, never bead
IDs.

**Component tags.** Guide and concept pages carry tags such as `CLI`, `Obsidian`, or
`macOS`, rendered as chips under the title. A generated "By component" index serves
readers who think in products. Reference mirrors the code: `reference/plugins/<id>/`
and `reference/mac-capture/<topic>/`.

**Each README becomes a front door** containing:

- one sentence on what it is;
- one image;
- requirements;
- the install snippet;
- links to Get started, this component's Reference, and Develop;
- the license.

Preserve detail elsewhere before deleting it from a README. A README must still be
useful to someone who never visits the site.

**Stays off the public pages:**

- bead IDs, `src/` paths, and history phrases (except in Develop and Contracts);
- `sase/` sidecars and research;
- operational memory;
- anything from the private vault.

---

## 9. Visual design: "a calm working notebook"

The idea is warm paper, dark ink, Bob's teal for interaction, and tomato reserved for
Today and Pomodoro, so that 🍅 keeps its meaning. Typography and real examples carry the
design; ornament does not.

### 9.1 Tokens

I computed these contrast ratios with the sRGB relative-luminance formula. The pairs
meet WCAG AA individually; that does not certify the site.

| Role | Light | Ratio | Dark | Ratio |
| --- | --- | --- | --- | --- |
| Surface / body text | `#FBF8F2` / `#171C1A` | 16.3:1 | `#121816` / `#EEF3ED` | 16.0:1 |
| Muted text | `#5C5F5A` | 6.1:1 | `#A3A9A2` | 7.5:1 |
| Links and active tab (teal) | `#0F6B63` (or `#087A78`, 4.9:1, closer to the product hue) | 6.0:1 | `#79DEDC` (the product's dark hue) | 11.4:1 |
| Teal glyphs, chips, and accent surfaces | `#0A9391` (glyphs only, **3.5:1**, never body text); surfaces at a 10–14% mix | — | `#79DEDC` at a 12% mix | — |
| Tomato text | `#9B3D2D` | 6.4:1 | `#F58B72` | 7.6:1 |
| Tomato glyph (Today / Pomodoro only) | `#D9472B` (**4.05:1**, icons and large text only) | — | `#F58B72` | — |

**Fonts.** Use **Inter** for UI and body text, **JetBrains Mono** for code, and
optionally **Source Serif 4** for the display headings in the hero. All three are
already bundled under the OFL in `bob-cli/assets/print_fonts/`.

- Self-host them as subsetted woff2 files with `theme.font: false`. That means no
  Google Fonts requests and no third-party privacy leak.
- Two families on article pages is the ceiling.

**Logo and favicon.** Port the bullet-"b" geometry from `StatusItemGlyph.swift` to SVG,
so the docs, the menu bar, and the app share one mark.

### 9.2 Homepage

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│ (b•) Bob     Get started  Guides  Concepts  Reference  Develop        🔍   ◐  │
├───────────────────────────────────────────────────────────────────────────────┤
│  Capture a thought. Choose today's work. Keep an honest record.   (draft copy)│
│  A keyboard-driven GTD system for an Obsidian vault — a CLI, Obsidian plugins,│
│  and a macOS capture panel that all speak the same task format.               │
│  [ Your first Bob day ]   [ How Bob fits together ]     Linux & macOS · Obsidian│
│                                                                               │
│  ┌ terminal ──────────────┐ ┌ Obsidian ─────────────────┐ ┌ menu bar ────────┐│
│  │ $ bob capture buy milk │ │ - [ ] ⌗ Buy milk  🍅  Oct 21│ │ (b•) buy milk    ││
│  └────────────────────────┘ └───────────────────────────┘ └──────────────────┘│
│                   one thought · three surfaces · one vault                    │
├───────────────────────────────────────────────────────────────────────────────┤
│  A BOB DAY   Morning review ─▶ Capture ─▶ Pomodoros ─▶ Close ─▶ Sync           │
├───────────────────────────────────────────────────────────────────────────────┤
│  Learn · Do · Understand · Look up                                            │
├───────────────────────────────────────────────────────────────────────────────┤
│  Is Bob for me? · Requirements & compatibility · Source repos · License       │
└───────────────────────────────────────────────────────────────────────────────┘
```

Each step in the "A Bob day" strip links to its concept page. The first screen must
answer:

- who Bob is for;
- which pieces are optional;
- the real platform constraints;
- one next action.

### 9.3 Signature details that make it look like Bob

- **Task lines render the way Bob renders them.** A `bob-task` fence class with CSS turns
  `- [ ] #task Rename the queue input [scheduled:: 2026-10-21]` into the teal ⌗ glyph,
  the checkbox, and date-mark chips. One annotated "task-line anatomy" figure lives in
  Reference.
- **Keycaps everywhere.** Bob is keyboard-heavy (`Ctrl+Shift+P`, `]s`, `Alt+N`).
  - Write raw `<kbd>`, which renders on both GitHub and the site.
  - Style keycaps as small physical keys.
  - Don't use `++ctrl+p++`: GitHub shows it literally.
- **At most one diagram per concept page.** Use Mermaid for flows: the thin-client
  capture round-trip, and lane transitions as a state diagram.
- **Reproducible media only:**
  - CLI: SVG terminal captures.
  - Mac panel: PNGs from the existing render-fixture tests on the `macos-26` CI.
  - Obsidian: a short scripted capture list run against the demo vault (fixed window,
    theme, and zoom), dated in a manifest so stale images are visible.
  - No autoplay video. Respect `prefers-reduced-motion`.
- **Article pages:**
  - a 65–75 character measure, 17–18 px body text, and generous line height;
  - left navigation and an "On this page" rail that collapse on mobile;
  - copy buttons that never copy prompts;
  - command and output visibly separated;
  - underlined prose links;
  - no meaning carried by color alone, since chips carry text.
- **Accessibility targets:** AA contrast in both themes, alt text on every image, a
  360 px width, 200% zoom, keyboard-only navigation, and readable core content without
  JavaScript (search may require it).
- **Portable Markdown.** Agents and GitHub read the same files, so prefer:
  - GitHub-style `> [!NOTE]` callouts;
  - standard tables;
  - `<kbd>`;
  - fenced code.

  Avoid content tabs and `!!!` blocks on pages that agents rely on.

---

## 10. Reliability

Gates run in two places:

- **locally**, through `just docs-check` in bob-cli, which agents run when anything
  under `docs/` changes and which joins `just check` once it is fast;
- **at publish time**, in the deploy repo.

No new CI is added to bob-cli or bob-plugins.

| Guard | What it catches |
| --- | --- |
| `zensical build --strict` with validation on | Broken internal links and anchors, malformed pages |
| **lychee** on the built site (offline, with fragments); external links on a slower schedule | An independent second check, including mount or link mistakes |
| **Plugin allowlist** and a ban on `hooks:` | Zensical silently ignoring a misconfigured plugin |
| **Generated CLI reference with `--check`** | Code and reference drifting apart (details below) |
| **Generated plugin inventory and versions** from `manifest.json`; command and hotkey tables later, from `addCommand` registrations | Repeats of the "six plugins" and `2.7.2` drift |
| **Generated glossary and design-decisions pages** from the memory webs | Vocabulary drift |
| **Tutorial runner** against the demo vault | A copied command failing or producing the wrong outcome (details below) |
| **URL contract** | Broken inbound links (details below) |
| **Docs lint**, ported and trimmed from sase's `check_docs` | Erosion of the information architecture over time (details below) |
| **Privacy lint**: no real-vault paths or names; images only from the demo-vault manifest | Leaking the private vault |
| **Search smoke queries**: `x!`, `@route`, `Pending`, "complete all", "hotkey conflict", "install plugins" | Punctuation-heavy grammar being unfindable. Zensical splits on punctuation by default, so give syntax tokens named headings and a token index. |
| **Provenance**: the footer shows the published SHAs, served at `/build.json`. A Compatibility page separates the *tested combination* from *minimum requirements*. | "Which Bob does this describe?" Label the site a **tested rolling snapshot**. No version switcher until releases exist. |
| **Deploy safety**: a `pages` concurrency group, default branch only, `curl` of the frozen URLs after deploy, and a failed gate that never deploys | Partial or broken publishes |

Details for the rows above:

- **Generated CLI reference.** Use a golden test or dev-only generator over the clap
  `Command` tree, not a new public subcommand. Skip hidden aliases (per `cli_rules`).
  Capture the 4 hand-printed help texts. Freeze width and locale so output is stable.
  The generated pages follow `bob --help`'s section groups.
- **Tutorial runner.** It runs the tutorial's shell blocks in an isolated `HOME`, XDG
  directories, `BOB_DIR`, and `BOB_DAY_FILE`, with a fixed date and time zone. It
  asserts real effects, not output strings: the task exists once, the link lands under
  the right Pomodoro, and closing produces the expected result. Network and sync hooks
  are excluded. Mac and Obsidian steps are marked `skip` and walked by hand on a Mac.
- **URL contract.** A frozen list of every published URL, every `docs/X.md` printed by
  `bob` help or errors, and every URL in the READMEs, each resolved against the build.
  When a move is unavoidable, the redirects plugin emits a static stub, with anchor
  maps for split pages.
- **Docs lint.** It checks:
  - front matter (`title`, a `description` of at most 160 characters);
  - word budgets: tutorials at most 2,500 words; guides 1,500 target and 2,500 hard;
    concepts at most 3,000; hubs at most 400; contracts and generated pages exempt;
  - hygiene: no bead IDs or `src/` paths outside Develop;
  - no new root-level pages except contracts.

**Writing contract and routing table** (`develop/writing-docs.md`, ported from sase):

- The placement test uses Diátaxis's two questions: action or cognition, acquisition or
  application. Contracts are a fifth bucket: "a spec that tests or two runtimes must
  agree on".
- Routing:

  | Change | Where it goes |
  | --- | --- |
  | New flag | Regenerate the reference and improve the clap help |
  | New hotkey | That plugin's reference page |
  | Behavior change | Its contract or reference; fix a guide step only if it is now wrong |
  | New user goal | A guide candidate |
  | Design decision | A decision record |

- The information architecture is a human decision. Agents never move pages between
  tabs without an approved plan.

Make agents follow this by updating bob-cli's agent instructions. That is a memory
change, so use `/sase_memory_write` when implementing.

---

## 11. Phased plan (every phase publishes)

**Phase 0: decisions and prerequisites** (Bryan, about an hour)

- Answer §12.
- Add LICENSE files.
- Create `bobs-org/bobs-org.github.io` and set Settings → Pages → Source to GitHub
  Actions.
- Fix the plugins README's public claims (private, six, `bbugyi200`, `2.7.2`).

**Phase 1: foundation and a useful site** (agents, about 2–4 days)

- `mkdocs.yml` with the allowlisted features; Zensical pinned, with the Material
  fallback recipe.
- The assembler with sibling mounts.
- Theme tokens, SVG mark, self-hosted fonts, the `bob-task` style, and the homepage.
- Contracts published in place (fix the 6 escaping links; exclude `docs/README.md`;
  add the contract banner).
- Generated CLI reference, glossary, and decisions pages.
- `just docs-serve`, `docs-check`, `docs-build`, and `docs-publish`.
- lychee, the docs lint, and the URL contract.
- `publish.yml` with `published.json`.
- A "Docs →" link in each README.
- **Acceptance:**
  - a strict build and lychee are clean;
  - every `docs/X.md` printed by `bob` resolves;
  - a deliberately broken link fails publishing while the old site stays live;
  - no empty tabs;
  - key pages pass at 360 px, 200% zoom, keyboard-only, and in both themes.

**Phase 2: the Learn path** (about a week)

- The synthetic demo vault, grown from `vault/` and the test fixtures, with only the
  settings the tutorial needs. No personal data, remotes, sync, or redistributed
  third-party plugin binaries.
- The tutorial runner.
- Is Bob for me?, Install Bob, Your first Bob day, and the Obsidian and Mac
  continuations.
- The concepts hub, with the eight nouns and one diagram.
- The Compatibility page.
- **Acceptance:**
  - the tutorial runs green in a fresh `HOME`;
  - Bryan walks it once on a clean machine, and every undocumented personal step is
    either documented or used to narrow the supported path.

**Phase 3: guides and concepts** (iterative, about two weeks of parallel agent work)

- Harvest 10–15 goal-titled guides and 5–6 concepts from the README and the contracts.
- Contracts stay authoritative; guides link to them rather than restating them.
- Component tags and the "By component" index.

**Phase 4: product reference**

- Split the Mac README into `bob-mac-capture/docs/`. Its troubleshooting becomes guides
  in bob-cli, and the README becomes a front door.
- One page per plugin in `bob-plugins/docs/`, with generated inventory, versions, and,
  later, command and hotkey tables.
- Mac panel screenshots rendered in CI.

**Phase 5: polish and proof**

- `llms.txt` through the native plugin; social cards; a dated Obsidian screenshot set.
- **Reader tests:**
  - first an agent test: a fresh agent with only the site or `llms.txt` runs sase's
    six-task protocol, adapted to Bob;
  - then 3–5 people;
  - target: 4 of 5 readers pick the right door first.
- Revise labels based on recorded misses.
- Optional: a custom domain or a capture playground.

These effort figures are low-confidence planning estimates. Install friction, manual
Mac and Obsidian verification, and link-preserving splits may dominate. Bryan's own
time is mostly Phase 0, approving the information architecture and door labels, and
walking the tutorial once.

---

## 12. Open questions for Bryan

1. **Audience:** do you *want* other people to run Bob? That sets how much
   install-from-zero effort the tutorial gets, and how prominent "Is Bob for me?" is.
2. **License:** MIT for bob-cli and bob-mac-capture, to match bob-plugins?
3. **URL:** is `bobs-org.github.io` acceptable at launch, or do you want a domain from
   day one so you never announce two URLs? GitHub keeps serving the old URL, so this is
   cosmetic.
4. **Publishing latency:** is hourly fine, or should we add a token-based dispatch for
   instant publishing?
5. **Decision records:** publish them as a "Design decisions" page? They are already
   public in the repo, but the page makes them discoverable.
6. **Indexing:** may search engines index the site?

---

## 13. What would change this recommendation

| Trigger | Change |
| --- | --- |
| Zensical 0.1 slips or fails the Phase 1 slice | Launch on Material 9.7 with the same files; revisit after 0.1 settles, and before May 2027 |
| Interactive, component-heavy pages become central | Starlight |
| Several supported release lines | Zensical's mike fork now, its native versioning later, or Docusaurus |
| Assembly costs more than the drift it prevents | Author everything in bob-cli (gem's pattern), accepting cross-repo doc edits |
| Per-PR preview URLs, custom headers, or a domain on Cloudflare | Cloudflare Pages |
| Hourly latency hurts | A fine-grained PAT or GitHub App dispatch from the content repos |

---

## Recommended solution

1. **Build one public documentation site for Bob** at **`https://bobs-org.github.io/`**,
   served free by GitHub Pages. Publish it from a thin `bobs-org/bobs-org.github.io`
   repo whose hourly, secret-free workflow builds the three public repos at recorded
   SHAs, gates the build, deploys it, and logs the publication. `just docs-publish`
   gives instant publishing, and a failed gate never replaces the live site.
2. **Keep the source with the code.**
   - The site shell and system-wide pages live in **bob-cli**.
   - Plugin and Mac reference live in their own repos' `docs/`, mounted at fixed paths.
   - The 26 existing contracts are **published unchanged at `/<stem>/`** under
     Develop → Contracts. They are neither moved nor rewritten.
3. **Build with Zensical** from a `mkdocs.yml` restricted to what both Zensical and
   Material 9.7 support, with Material as a fallback builder. Adopt sase's Diátaxis
   writing contract and tab and door labels, but none of its Cloudflare, blog, or PDF
   machinery.
4. **Organize by reader need:** Get started · Guides · Concepts · Reference · Develop.
   Products appear as reference sections and tags. Ship a complete small site first,
   then the Learn path, then harvested guides and concepts, then the split product
   reference. Never publish an empty tab.
5. **Make it beautiful with Bob's own identity:**
   - the bullet-"b" mark;
   - teal for interaction and tomato only for Today;
   - Inter and JetBrains Mono, already bundled;
   - task lines rendered the way Bob renders them;
   - contrast-checked tokens in both themes;
   - screenshots only from a synthetic demo vault.
6. **Make it reliable:**
   - a strict build plus lychee;
   - generated CLI, plugin, glossary, and decision facts with drift checks;
   - a tutorial runner in an isolated vault;
   - a frozen URL contract that includes every `docs/X.md` that `bob` prints;
   - a plugin allowlist, a privacy lint, and search smoke tests;
   - visible provenance and compatibility.
7. **Before starting:** add LICENSE files to bob-cli and bob-mac-capture, and correct
   the plugins README's stale public claims.

This is a good project at this scope. It would be a bad one as a big-bang effort to
"document everything to sase's depth". Diátaxis's own cure applies: make the next
small improvement, publish it, and repeat.

---

## Sources

**Researcher reports (this folder):** `bob_public_docs_site__cdx.md`,
`bob_public_docs_site__cld.md`, `bob_public_docs_site__grk.md`,
`bob_public_docs_site__mus.md`, `bob_public_docs_site__gem.md`.

**Local evidence** (opened through `sase repo open`):

- bob-cli `bfca3419`: `README.md`, `docs/`, `src/` help strings, `assets/print_fonts/`,
  `vault/`, `sase/memory/`
- bob-plugins `ef1a63c`: `README.md`, `plugins/*/manifest.json`, `LICENSE`, `scripts/`
- bob-mac-capture `f7e635a`: `README.md`, `Sources/BobMacCapture/StatusItemGlyph.swift`,
  `.github/workflows/ci.yml`
- sase-org/sase `110214f51c`: `requirements-docs.txt`,
  `docs/contribute/writing-docs.md`, `Justfile`, `tools/`
- GitHub API: repo visibility, licenses, Pages status, and the absence of
  `bobs-org.github.io`

**External** (checked 2026-10-19):

- Diátaxis — [How to use Diátaxis][dx-how] · [Map][dx-map] · [Start here][dx-start] ·
  [Compass][dx-compass]
- GitHub — [What is GitHub Pages][gh-what] · [Pages limits][gh-limits] ·
  [Custom workflows][gh-workflows] · [About custom domains][gh-domain-about] ·
  [Managing a custom domain][gh-domain-manage] ·
  [Configuring a publishing source][gh-source] · [Disable and enable workflows][gh-disable] ·
  [REST: workflows][gh-rest-wf]
- Zensical — [Upcoming changes][zen-up] · [Plugin compatibility][zen-plugins] ·
  [MkDocs migration][zen-mig] · [Validation][zen-val] · [Roadmap][zen-road] ·
  [Search][zen-search] · [Publish your site][zen-pub] · [mike][zen-mike] ·
  [PyPI][zen-pypi]
- Material for MkDocs — [End of life extended to 2027-05-05][mat-eol] ·
  [What MkDocs 2.0 means][mat-mk2]
- Astro and Starlight — [Cloudflare acquires Astro][astro-cf] · [Starlight][starlight] ·
  [Starlight site search][starlight-search]
- W3C — [Contrast (minimum)][contrast]

[dx-how]: https://diataxis.fr/how-to-use-diataxis/
[dx-map]: https://diataxis.fr/map/
[dx-start]: https://diataxis.fr/start-here/
[dx-compass]: https://diataxis.fr/compass/
[gh-what]: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
[gh-limits]: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
[gh-workflows]: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
[gh-domain-about]: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages
[gh-domain-manage]: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site
[gh-source]: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site
[gh-disable]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows
[gh-rest-wf]: https://docs.github.com/en/rest/actions/workflows
[zen-up]: https://zensical.org/upcoming-changes/
[zen-plugins]: https://zensical.org/docs/compatibility/mkdocs/plugins/
[zen-mig]: https://zensical.org/docs/compatibility/mkdocs/migration/
[zen-val]: https://zensical.org/docs/setup/validation/
[zen-road]: https://zensical.org/roadmap/
[zen-search]: https://zensical.org/docs/setup/search/
[zen-pub]: https://zensical.org/docs/publish-your-site/
[zen-mike]: https://zensical.org/docs/compatibility/mkdocs/mike/
[zen-pypi]: https://pypi.org/project/zensical/
[mat-eol]: https://github.com/squidfunk/mkdocs-material/issues/8523
[mat-mk2]: https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/
[astro-cf]: https://secure.businesswire.com/news/home/20260116386991/en/Cloudflare-Acquires-Astro-to-Accelerate-the-Future-of-High-Performance-Web-Development
[starlight]: https://starlight.astro.build/
[starlight-search]: https://starlight.astro.build/guides/site-search/
[contrast]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

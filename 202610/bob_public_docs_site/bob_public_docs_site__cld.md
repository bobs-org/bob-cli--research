# One Bob docs site: Diátaxis, GitHub Pages, and a design that holds up

Researcher: `cld` · Date: 2026-10-19 · Scope: `bobs-org/bob-cli`, `bobs-org/bob-plugins`,
`bobs-org/bob-mac-capture`

## TL;DR

- **Yes, build it. But the main job is to reorganize Bob's docs, not to write more of
  them.** Across the three repos, Bob already has about 30,000 lines of Markdown. Most of
  it is detailed *contracts* (specs with conformance vectors), mixed in with install
  steps, explanation, and keymaps. Readers cannot find the right page, and nothing
  separates "teach me" from "look it up". Diátaxis fixes exactly this problem.
- **One site for the Bob system, not three repo sites.** Readers think "set up Bob", not
  "set up bob-plugins". Diátaxis types are the top-level tabs. Each product (CLI,
  Obsidian plugins, Mac Capture) appears only where structure follows the code: in
  Reference and Develop. A component tag marks which products each guide touches.
- **Hosting: GitHub Pages, free.** Use the org site at **`https://bobs-org.github.io/`**,
  deployed with GitHub Actions from a new, nearly empty `bobs-org/bobs-org.github.io`
  repo. The site's source lives with the code: its config and the cross-cutting pages in
  `bob-cli/docs/`, and product reference pages in each sibling repo's `docs/`. A custom
  domain later is a one-setting change.
- **Generator: Zensical, configured through `mkdocs.yml`.** Zensical is the successor to
  Material for MkDocs, from the same team, and it reads `mkdocs.yml` directly. sase.sh
  already restricts itself to the Zensical-compatible subset. Material reaches end of
  maintenance on 2027-05-05, and Zensical 0.1 starts a "dependable release line" on
  2026-11-05. Pin it, and keep Material 9.7 as the emergency fallback builder.
- **Beautiful means using Bob's own visual identity.** That identity already exists in
  the repos: the bullet-"b" menu-bar mark, the teal identity hue (about `#0a9391`), the
  Today tomato, and the Inter / Source Serif 4 / JetBrains Mono fonts already bundled in
  `bob-cli/assets/print_fonts/`. Pages should show task lines the way Bob renders them,
  not as raw Markdown.
- **Reliable means generated facts, a strict build, and URLs fixed before launch.**
  Generate the CLI reference from clap. Build in strict mode, run an independent link and
  anchor check, test the tutorial against a synthetic demo vault, and treat published URLs
  as a contract. Decide the URL structure *before* the first publish. sase did not, and
  now maintains `moves.yml`, generated `_redirects`, stub pages, and a URL-contract test
  to keep old links alive.

The final section, *Recommended solution*, has the full proposal and a phased plan.

---

## 1. What exists today

| Fact | Evidence | Why it matters |
| --- | --- | --- |
| bob-cli has 26 guides in `docs/`, **25,112 lines** in total, plus a 1,584-line README | `wc -l docs/*.md README.md` | Volume is not the problem. |
| The biggest pages are specs: `capture.md` (6,371 lines), `task-dependencies.md` (3,556), `highlights-ref-sync.md` (2,055), `freshness.md` (1,515) | same | These are contracts, not user docs. |
| Many pages say tests copy their **conformance vectors verbatim** into Rust and JS | `docs/freshness.md:27`, `docs/plan.md:573`, `docs/today-marks.md:7` | They are cross-repo specs, so they belong in a contributor area, not a tutorial. |
| `docs/` paths are hard-coded in about **440 places**: about 270 in bob-plugins JS, about 170 in bob-cli `src/`, and a few in Mac Capture and the tests (`help_options.rs` asserts `docs/stats.md` appears in `--help`) | `grep -rhoE 'docs/[a-z-]+\.md'` | Moving pages costs something. Do any moves once, before launch. |
| The bob-plugins README is 74 KB. Each plugin's row in its "Plugins" table holds one paragraph of hundreds of words. It still says `bob-navigation-hotkeys` "is ahead … at `2.7.2`", while the manifest says `2.46.0` | `bob-plugins/README.md` | Hand-maintained facts go stale. Generate them. |
| The bob-mac-capture README is **191 KB / 2,807 lines** in one file (Runtime Contract, Keyboard, Troubleshooting, Privacy…) | `bob-mac-capture/README.md` | Readers cannot navigate it; it needs splitting into pages. |
| The three repos are **public** in a **Free** org (`bobs-org`). Pages is not enabled on any of them. No `bobs-org.github.io` repo exists. The vault repo `bobs-org/bob` is **private** | `gh repo list`, `gh api …/pages` (404) | GitHub Pages is free here. The site must never touch vault content. |
| `bob-cli` and `bob-mac-capture` have **no LICENSE**. `bob-plugins` is MIT | `gh repo view --json licenseInfo` | A site that invites installs does not fit "all rights reserved". |
| bob-cli and bob-plugins have **no GitHub Actions workflows**. Mac Capture has CI on `macos-26` | `gh api …/actions/workflows` | Cross-repo rebuild triggers must be added deliberately. |
| A visual identity already exists: a geometric bullet-"b" mark drawn in code; a teal identity hue (about `#0a9391` light, `#79dedc` dark); the Today tomato; and bundled Inter, Source Serif 4, and JetBrains Mono fonts | `bob-mac-capture/README.md` "Menu-Bar Icon"; `docs/task-tag-marks.md` (lines 58–88); `docs/today-marks.md`; `assets/print_fonts/` | You don't need to invent a brand. |
| `bob --help` is already grouped (Daily workflow / Tasks and projects / Vault / Integrations / Setup / Capture protocol) and ends with Examples | `bob --help` | The CLI reference can be generated from clap with these same groups. |
| The glossary (18 terms) and decisions (24 records) memory webs live in bob-cli | `sase/memory/glossary/`, `sase/memory/decisions/` | A Glossary page and a Design decisions page can be generated, as sase does. |

**sase.sh, the model you named.** It runs MkDocs with Material 9.7 (`requirements-docs.txt`)
and deploys to a Cloudflare Worker (`wrangler.jsonc`, `.github/workflows/docs-deploy.yml`).
Its Diátaxis contract is written down in `docs/contribute/writing-docs.md`:

- The directory decides the page type: `start/` is tutorials, `guides/` how-to, `concepts/`
  explanation, `reference/` lookup, `contribute/` contributor material.
- Every page type has a template in `docs/_templates/`.
- Pages have word budgets.
- Guide pages may not contain bead IDs, `src/` paths, or history phrases.
- A routing table says where each kind of change goes.
- Reference is generated from code where possible, with `--check` drift detection.
- A tutorial runner executes the shell blocks in `start/`.
- A URL-contract test and a reader-testing protocol, "4 of 5 readers pick the right door
  first", keep links and labels honest.
- It deliberately "builds on any Zensical-compatible host: add no MkDocs `hooks:`,
  `gen-files`, or plugins beyond search, redirects, blog, rss."

That contract is the most valuable thing to copy. The Cloudflare, blog, and PDF parts are
not worth copying for v1.

---

## 2. Is this a good idea? A critique

### Who will actually read it?

Be honest about the audience. The repos have 1 star each and no releases, and you install
from source. bob-plugins' own README says it is "a private personal monorepo … not a
distribution channel". Today's real readers are:

1. **Your agents.** They read `docs/` and READMEs on every change, and they pay for
   unfocused pages in context tokens and in wrong edits.
2. **You, months from now,** trying to remember how a feature works.
3. **Curious visitors.** People who find Bob through sase, your GitHub profile, or a link
   you share. A polished site is what makes Bob something you can show.

That is a good reason to build the site, but it changes the priorities:

- The **in-repo Markdown must stay the single source of truth.** Agents and GitHub read
  the same files the site renders. Never write prose only for the site.
- **Reference and explanation matter more than a long install-from-zero tutorial.** One
  honest tutorial is enough at first.
- **"Is Bob for me?" must be candid.** Bob is opinionated GTD for one Obsidian setup. It
  needs the Tasks plugin's Dataview format, the custom plugins, a Rust toolchain, and,
  for Mac Capture, macOS 26.

### The real problem is mixed page types, not missing pages

Diátaxis's central warning is that "when these distinctions are allowed to blur, the
different kinds of documentation bleed into each other" ([map][dx-map]). Bob's docs show
this everywhere:

- The README's *Installation* section mixes a how-to (`just install`), reference
  (`CARGO_INSTALL_ROOT` resolution), troubleshooting (keychain lock), and explanation (why
  `--force` is forbidden) in a single paragraph.
- Each cell of the plugin table holds a full behavior spec.

Restructuring pays off whether or not a website exists. The website is what makes the
restructuring visible, searchable, and attractive.

### Risks

| Risk | Mitigation |
| --- | --- |
| **Drift.** Bob changes daily, and almost every feature commit edits a doc. | Generate facts (CLI, keymaps, versions). Keep guides short and few. Tests never pin guide prose, which is sase's rule. Use a routing table that says "update the Reference; fix the guide step only if it is now wrong". |
| **Copying all of sase.** sase has 442 doc files, a blog, a PDF handbook, Cloudflare, and seven docs tools. | Copy the *contract*, not the machinery. Skip the blog, PDF, analytics, and Cloudflare in v1. |
| **Toolchain churn.** MkDocs 1.x is effectively frozen. MkDocs 2.0 drops plugins and cannot build Material sites. Material is in maintenance mode. | Use Zensical with only core features. No custom plugins or hooks. Do generation in pre-build scripts. |
| **Empty skeletons.** Creating four empty tabs per repo is the anti-pattern Diátaxis names explicitly: "Don't do that. It's horrible." ([how-to-use][dx-how]) | Ship a useful site in Phase 1 (Reference plus Contracts), and add tabs only when they have real pages. |
| **Privacy.** The vault is private, and screenshots tempt you to use real data. | Use a synthetic demo vault for every example and screenshot, and have the docs check grep for real-vault markers. |
| **Opportunity cost.** | Agents do the writing. Your time goes only to IA approval, door labels, and one tutorial walkthrough. |

**Verdict:** a good idea on four conditions:

- The site renders the same in-repo Markdown.
- Facts are generated.
- The rollout is incremental.
- The contracts stay contracts, in their own area, instead of being forced into user
  docs.

### Approaches I considered and rejected

| Alternative | Why not |
| --- | --- |
| **Just clean up READMEs and docs on GitHub, with no site** | Cheapest, but no search across three repos, no navigation, and nothing beautiful. Do this cleanup anyway as part of the plan. |
| **Three project sites** (`bobs-org.github.io/bob-cli/` and so on) with a shared theme | Simplest builds, but readers' tasks cross products. For example, "capture from my Mac" involves the app, the CLI grammar, and vault routing. You would get three searches and unchecked cross-site links. Diátaxis also warns that organizing a portfolio by product "results [in] wild inconsistency" ([map][dx-map]). |
| **A docs hub repo that holds all the content** | Separates docs from code. An agent changing a plugin hotkey would have to open a fourth repo, so docs drift. |
| **Quartz or Obsidian Publish** (author the docs as an Obsidian vault) | Charming as dogfooding. But Quartz is a digital-garden tool with weak structured navigation, and Publish is paid. It also invites mixing doc notes with the private vault. |
| **Cloudflare Workers, like sase** | Supports real `_redirects` and `_headers`, but needs a Cloudflare account, an API token secret, and Wrangler. GitHub Pages needs no extra account. Its lack of server-side redirects is handled by static redirect pages. |

---

## 3. Requirement adjustments (explicitly called out)

| # | Your requirement | My adjustment | Why |
| --- | --- | --- | --- |
| **A1** | "Excellent documentation for all of the public bob repos" | **One site for the *Bob system*, organized by reader need. The repos appear as components, not as top-level sections.** | Diátaxis says don't structure around product features. Bob's three repos are one product with three surfaces (Mac Capture is "a thin client of bob"; plugins and CLI share conformance vectors). |
| **A2** | Implicitly, full Diátaxis coverage now | **Iterate. Ship a useful Phase 1 (Home, generated CLI reference, the existing contracts), then add Tutorials, Guides, and Concepts as real pages exist.** | Diátaxis: "Use Diátaxis as a guide, not a plan", and "every step in the right direction is worth publishing immediately" ([how-to-use][dx-how]). |
| **A3** | Diátaxis-inspired "just like sase" | **Adopt sase's contract** (directory = type, templates, budgets, hygiene, routing table, URL contract). **Scale down the machinery** (no blog, PDF, or Cloudflare). **Add a fifth area, `contracts/`,** for the existing specs. | Bob's 25k lines of specs are a distinct, legitimate genre that agents rely on. They are reference material for builders, not for users. |
| **A4** | Docs for "users" (implicit) | **Name the audiences:** (1) a technically capable Obsidian user who wants to run Bob; (2) Bryan and his agents as maintainers. **Add an honest "Is Bob for me?" page.** | Your current audience is mostly maintainers. Writing as if for thousands of users wastes effort. Writing only for yourself wastes the public site. |
| **A5** | "Beautiful" | **Derive the brand from Bob's existing marks and fonts, show task lines as Bob renders them, and meet WCAG AA contrast.** | Consistency with the product makes the docs instantly recognizable, and the assets already exist. |
| **A6** | (not stated) | **Generated reference and a strict, link-checked build are requirements, not extras.** | "Reliable" docs for a system that changes daily is impossible without them. The plugin README's stale version string proves it. |
| **A7** | (not stated) | **Prerequisites: add a LICENSE to bob-cli and bob-mac-capture, and create a synthetic demo vault.** | A public install guide for unlicensed code is a mixed message. Real screenshots must not come from the private vault. |
| **A8** | Host on github.io | **Yes. Use the org site `bobs-org.github.io`, keep `site_url` as the single knob, and consider a custom domain later.** | GitHub serves a custom domain for the org site and all its project sites with no content changes ([custom domains][gh-domain]). |

---

## 4. Hosting: GitHub Pages works, for free

- **Availability and cost.** Pages is available for public repos on GitHub Free. bobs-org
  is a Free org whose bob repos are all public. Actions minutes for public repos on
  standard runners are free, so the total cost is **$0**.
- **Limits** ([limits][gh-limits]):
  - The published site may be at most 1 GB. Bob's text site will be a few MB, plus
    screenshots.
  - Bandwidth has a soft limit of 100 GB/month.
  - The soft limit of 10 builds/hour "does not apply if you build and publish your site
    with a custom GitHub Actions workflow".
  - Deployments time out after 10 minutes.
  - Commercial or SaaS use is not allowed. A docs site is fine.
- **URL options** ([what is Pages][gh-what]):
  - **Org site:** a repo named `bobs-org.github.io` serves **`https://bobs-org.github.io/`**.
    There is one per account. ← **Recommended:** a clean root for a system-wide site.
  - **Project site:** `https://bobs-org.github.io/<repo>/`. If deployed from bob-cli it
    would read as "the CLI docs", which is the wrong framing for a system site.
  - **Never** a project site named `bob`: that is the private vault repo.
- **Custom domain later.** Set it once on the org site and it applies to every project
  site in the account ([custom domains][gh-domain]). Keep `site_url` in one place and use
  relative links everywhere, so the switch is a config change.
  - Free option: a subdomain of a domain you already own. `bob.sase.sh` would cost
    nothing, but it ties Bob's brand to SASE, so I would not.
  - Otherwise, buy a cheap domain when Bob is ready to be shown widely.
- **Deploying.** The Actions-based flow is `actions/configure-pages` →
  `actions/upload-pages-artifact` → `actions/deploy-pages`. The deploy job needs
  `pages: write` and `id-token: write` and runs in the `github-pages` environment
  ([custom workflows][gh-workflows]). Set Settings → Pages → Source to "GitHub Actions".
- **Gotchas.**
  - **No server-side redirects or custom headers.** Use the redirects plugin, which
    Zensical supports and which generates static HTML redirect pages, and fix URLs before
    launch so you rarely need it.
  - A deploy that fails before `deploy-pages` leaves the previous site live. That is good
    for reliability.
  - **Scheduled workflows in public repos are disabled after 60 days without repository
    activity** ([disable workflows][gh-disable]). A nearly empty deploy repo will be quiet,
    so cron must be a safety net only. Push-time dispatch from the content repos is the
    primary trigger (§6).

---

## 5. Site generator

### Ecosystem status (as of 2026-10-19)

- **Material for MkDocs** is in maintenance mode. Critical fixes are extended through
  **2027-05-05** (announced 2026-09-16) ([Material on MkDocs 2.0][mat-mk2]).
- **MkDocs 2.0** is a pre-release (2.0.dev2, 2026-08-30). It "won't have a plugin system",
  "is incompatible with Material for MkDocs", and offers "no migration path"
  ([same post][mat-mk2]).
- **Zensical** is the successor from the Material team (MIT):
  - Latest release `0.0.71` (2026-10-16, Alpha classifier) ([PyPI][zen-pypi]).
  - **0.1.0 begins a dependable release line on 2026-11-05** ([upcoming changes][zen-up]).
  - It "reads the existing `mkdocs.yml`". Of the MkDocs settings, only `hooks` is
    unsupported ([migration][zen-mig]).
  - It supports the features Bob needs ([plugins][zen-plugins], [validation][zen-val],
    [diagrams][zen-diag], [navigation][zen-nav]):
    - plugins: search, redirects, tags, social cards, offline, `llmstxt` (since 0.0.67),
      blog;
    - strict mode with link and anchor validation;
    - Mermaid flowchart, sequence, state, class, and ER diagrams;
    - code annotations, content tabs, `pymdownx.keys`, snippets, admonitions;
    - `navigation.tabs` and `navigation.indexes`;
    - `custom_dir` overrides and `extra_css`.
  - Plugins it does not support are **silently ignored**. Your plugin allowlist (§10)
    guards against that.
  - It has no multi-project or monorepo feature. Material's `projects` plugin is not on
    Zensical's lists. Bob therefore assembles the three repos itself in a small,
    deterministic pre-build step.

### Comparison for Bob

| Option | Beauty out of the box | Fit for a Diátaxis multi-repo site | Reliability and longevity | Fit with your ecosystem | Verdict |
| --- | --- | --- | --- | --- | --- |
| **Zensical** (with `mkdocs.yml`) | High: Material's design, `classic` or `modern` variants | Tabs, indexes, tags, strict validation; multi-repo via pre-build copy | 0.x, but a dependable line from Nov 5; same team; MIT | **Same config language and Diátaxis contract as sase.sh**, and agents already know it | **Recommended** |
| Material for MkDocs 9.7 | High | Same | **End of maintenance 2027-05-05** | Same | Fallback builder only |
| Astro Starlight | Very high, modern | Good; `starlight-sidebar-topics` gives per-section sidebars | Healthy; still 0.x | New toolchain (Astro/MDX); a different contract from sase | Runner-up |
| Docusaurus | Good | Strong multi-instance docs | Mature | Heavy React stack | No |
| VitePress | High | Fine | Mature | Vue stack, smaller plugin set | No |
| mdBook | Plain | Weak (one book, no tabs or tags) | Mature, Rust-native | Rust affinity only | No |
| Quartz | Garden-style | Weak structure | OK | Obsidian-flavored | No |

**Why Zensical over Starlight.** Starlight is arguably prettier with no configuration, but
the deciding factors are:

- Bob and SASE can share one docs contract, one config dialect, and maybe one lint tool.
- You can switch builders: the same `mkdocs.yml` builds with Zensical or, in an
  emergency, Material 9.7.
- It has every feature Bob needs.

**What would change my mind:** if you want rich interactive components inside pages (for
example a live capture-grammar playground built from a WASM build of bob's parser),
Astro's island model is a better host. That playground is a fun Phase 5 idea, and a small
JS island can also run on Zensical.

**Theme variant.** Start with `classic`. It keeps Material 9.7 as a working fallback, and
sase's CSS knowledge transfers. Zensical says extra CSS works "without changes when using
the `classic` theme". Revisit `modern` after 0.1 settles, with a one-hour bake-off
using Bob's palette.

---

## 6. Multi-repo architecture

### Where the content lives

| Content | Home | Rationale |
| --- | --- | --- |
| Site config (`mkdocs.yml`), theme overrides, CSS, homepage | **bob-cli** | bob-cli is already the integration point: `just install-all` orchestrates the sibling repos, and the glossary and decisions webs live there. Agents in bob-cli workspaces can preview the whole site. |
| Tutorials, how-to guides, concepts (system-wide) | **bob-cli** `docs/{start,guides,concepts}/` | These describe the Bob *system*. Today bob-cli docs already document plugin UI (dashboard, marks, Task Card). |
| System-wide reference: CLI (generated), capture grammar, vault format, env vars, JSON outputs, glossary, decisions | **bob-cli** `docs/reference/` | Owned by the CLI, or cross-cutting. |
| **Contracts** (the existing 26 specs) | **bob-cli** `docs/contracts/` | One move-only commit before launch (see below). |
| Plugin reference (commands, hotkeys, settings, URIs; per plugin) | **bob-plugins** `docs/` | Docs change in the same commit as the code. Command and hotkey tables can be generated from `addCommand` registrations. |
| Mac Capture reference (keyboard, settings, notifications, privacy, diagnostics, runtime contract) | **bob-mac-capture** `docs/` | Same reason. This is mostly a split of the 191 KB README. |
| Deploy workflow | **bobs-org.github.io** (new repo, about 60 lines) | `deploy-pages` publishes the Pages site of the repo the workflow runs in, so the org site's workflow must live in that repo. Its README says "source lives in bob-cli". |

### Build and deploy flow

```text
 bob-cli                         bob-plugins             bob-mac-capture
 ├─ mkdocs.yml, overrides/       └─ docs/**  ─────┐      └─ docs/**  ─────┐
 ├─ docs/{start,guides,concepts,reference,develop}/   │                       │
 └─ docs/contracts/*.md                               │                       │
        │ push to master (docs/** changed)            │ push                  │ push
        └── docs-dispatch.yml ── gh workflow run ─────┴───────────────────────┘
                                   │  (org secret: fine-grained token, Actions:write on hub only)
                                   ▼
        bobs-org/bobs-org.github.io : deploy.yml
          triggers: workflow_dispatch · push · weekly cron (safety net)
          checkout bob-cli + bob-plugins + bob-mac-capture (public; no token needed)
          just docs-build   →  assemble siblings → zensical build --strict → lychee (links + #anchors)
          configure-pages → upload-pages-artifact → deploy-pages → smoke-curl frozen URLs
                                   ▼
                     https://bobs-org.github.io/
```

- **Assembly** is one small, deterministic script in bob-cli. Before the build it copies
  `$BOB_PLUGINS_DIR/docs` to `docs/reference/plugins/` and `$BOB_MAC_CAPTURE_DIR/docs` to
  `docs/reference/mac-capture/`. Both copies are gitignored.
- The sibling paths default to `../bob-plugins` and `../bob-mac-capture`, the layout
  `install-all` already assumes. Then the script tries `sase/repos/linked/<repo>` (SASE
  agent workspaces), then a shallow clone into `~/.cache/bob-docs/`. `just docs-check`
  therefore works everywhere and never silently skips a sibling.
- **Generated reference is committed** and drift-checked by bob-cli's `just check`. The
  hub never runs cargo; it only assembles, builds, and checks links, so it stays fast.
- **Triggers.**
  - Each content repo gets a 15-line `docs-dispatch.yml` that runs on push to `master`
    for `docs/**`. It calls `gh workflow run deploy.yml -R bobs-org/bobs-org.github.io`
    using an **org-level secret**: a fine-grained token scoped to the hub repo with
    Actions read/write. A GitHub App avoids token expiry if you prefer that.
  - A weekly cron in the hub is only a safety net: GitHub disables cron after 60 quiet
    days ([disable workflows][gh-disable]).
  - A local `just docs-publish` in bob-cli (`gh workflow run …` with your own `gh`
    login) covers the rest.

### Contracts: move once, before launch

The 26 specs need a typed home so their URLs say what they are:
`/contracts/freshness/`, not a root-level `/freshness/` that a newcomer mistakes for the
freshness guide.

- **Recommended:** one coordinated, **move-only** commit per repo:
  - `git mv docs/<stem>.md docs/contracts/<stem>.md`;
  - a mechanical `sed` over the roughly 440 references in bob-cli `src/`, bob-plugins
    JS, Mac Capture, and the tests;
  - schedule it in a quiet window so in-flight agent branches don't conflict.
- After that, `docs_dir: docs` is used as-is. Live reload works for all bob-cli content,
  and no public URL ever needs a redirect.
- Old commit links on GitHub keep working because they are pinned to commit SHAs.
- **Fallback, if you'd rather avoid the churn now:** leave the files in place and have the
  assembler copy `docs/*.md` to `contracts/` in the build tree. That costs permanent
  remapping and link-rewriting code. I'd rather pay the churn once.
- At the same time, change help text such as "see `docs/stats.md`" to the published URL.
  An installed `bob` has no repo next to it. Add those URLs to the URL contract.

---

## 7. Information architecture

### Tabs

The tabs and door labels match sase, so moving between the two sites feels familiar.

| Tab | Diátaxis type | Directory | Contents at launch (✓) and soon after |
| --- | --- | --- | --- |
| **Home** | — | `docs/index.md` | ✓ Hero, four doors, "a Bob day", components |
| **Get started** | Tutorial | `docs/start/` | Install Bob · Your first Bob day (demo vault: capture → link into a Pomodoro → start/close → stats) |
| **Guides** | How-to | `docs/guides/` | Grouped by goal: *Set up* · *Capture* · *Plan the day* · *Projects & dependencies* · *Reading* · *Fix problems* |
| **Concepts** | Explanation | `docs/concepts/` | How Bob works (the one system diagram) · Tasks and lanes · Today and the Pomodoro ledger · Freshness and the review walk · Projects and dependencies · The reference library · Why the vault syncs through git |
| **Reference** | Reference | `docs/reference/` | ✓ CLI (generated) · Capture grammar · Vault format (task-line anatomy, statuses, fields, frontmatter) · Environment · JSON outputs · Obsidian plugins (per plugin) · Bob Mac Capture · ✓ Glossary (generated) · ✓ Design decisions (generated) |
| **Develop** | Contributor | `docs/develop/` + `docs/contracts/` | ✓ Contracts (the 26 specs, with docs/README.md as their hub) · Building each repo · Release checklist · Writing docs |

Guide pages are **titled with the reader's goal and cross product lines**. Examples
harvested from today's README and docs:

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
- Fix "bob not resolved" in Mac Capture

### Component tags

Diátaxis wants one scheme across the portfolio, but some readers think in products. The
**tags plugin** reconciles the two without duplicating structure:

- Every guide and concept page carries frontmatter `tags: [CLI]`, `[Obsidian]`, `[macOS]`,
  or any combination.
- The tags render as small colored chips under the title.
- A generated "By component" index lists every page per product.

Reference mirrors the code: `reference/plugins/<plugin-id>/` and
`reference/mac-capture/<topic>/`. That follows Diátaxis's advice that "the architecture of
reference documentation should reflect the structure … of the thing it's describing"
([start here][dx-start]).

### URL scheme (frozen at launch)

`/start/<slug>/` · `/guides/<goal-slug>/` · `/concepts/<topic>/` ·
`/reference/cli/<command>/` · `/reference/plugins/<id>/` ·
`/reference/mac-capture/<topic>/` · `/contracts/<stem>/` · `/develop/<topic>/`. Each
`README.md` becomes a short front door:

- one sentence on what it is;
- one image;
- the install snippet;
- three links: Get started, this component's Reference, and Develop.

Contributor essentials (build and test commands) move to Develop.

---

## 8. Visual design

### Design tokens, taken from Bob itself

| Token | Light | Dark | Source / note |
| --- | --- | --- | --- |
| Accent (links, active tab) | **`#087a78`** (about 5.2:1 on white, passes AA for text) | **`#79dedc`** | Derived from the teal identity hue. The product's `#0a9391` is about 3.8:1, fine for glyphs but not for body links. |
| Accent surface (chips, active nav background) | `#0a9391` at 10–14% mix | `#79dedc` at 12% mix | Mirrors `docs/task-tag-marks.md` and the today-marks hover capsule. |
| Secondary (Pomodoro / Today only) | tomato about `#d9472b` | same, lifted | Icons and accents only (about 4.3:1, below the text threshold). Use it sparingly so 🍅 still means "Today". |
| Primary / header | near-black ink | slate | Same restraint as sase (`primary: black`). |
| Fonts | **Inter** (UI and body), **Source Serif 4** (display headings and hero), **JetBrains Mono** (code) | — | Already bundled under the OFL in `bob-cli/assets/print_fonts/`. Self-host them as woff2 subsets with `theme.font: false`: no Google Fonts requests, no third-party privacy leak, no build-time font fetch. |
| Logo and favicon | The **bullet-"b"** as SVG | template-tinted | Port `StatusItemGlyph.swift`'s geometry so the docs, the menu bar, and the app share one mark. |

### Homepage wireframe

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ (b•) Bob    Get started  Guides  Concepts  Reference  Develop        🔍   ◐  │
├──────────────────────────────────────────────────────────────────────────────┤
│  BOB                                                                         │
│  Capture anything. Plan today. Keep your vault honest.        (draft; yours) │
│  A command-line GTD system for an Obsidian vault — with Obsidian plugins     │
│  and a macOS capture app that all speak the same task format.                │
│  [ Your first Bob day · 20 min ]   [ How Bob works ]                         │
│                                                                              │
│  ┌ terminal ───────────────┐ ┌ Obsidian ──────────────────┐ ┌ menu bar ─────┐│
│  │ $ bob capture buy milk  │ │ - [ ] ⌗ Buy milk  🍅  + Oct │ │ (b•) buy milk ││
│  │     @groceries          │ │                            │ │   @groceries  ││
│  └─────────────────────────┘ └────────────────────────────┘ └───────────────┘│
│                 one thought · three surfaces · one vault                     │
├──────────────────────────────────────────────────────────────────────────────┤
│  A BOB DAY   Morning review ─▶ Capture ─▶ Pomodoros ─▶ Close ─▶ Nightly sync  │
│              (each step links to its concept page)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│  PICK YOUR DOOR    Learn · Do · Understand · Look up      (same as sase.sh)  │
├──────────────────────────────────────────────────────────────────────────────┤
│  COMPONENTS   bob CLI — Linux & macOS │ Obsidian plugins │ Mac Capture — 26+ │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Making the docs look like the product

- **Task lines render like Bob renders them.** A small `bob-task` code-block style
  (custom fence class plus CSS) turns `- [ ] #task Rename the queue input
  [scheduled::2026-10-21]` into the teal ⌗ glyph, the status checkbox, and date-mark
  chips. Concept pages then show what you will see in Obsidian, not raw syntax. Use
  **code annotations** ([code blocks][zen-code]) for the one "task-line anatomy"
  reference figure.
- **Keycaps everywhere.** Bob is keyboard-heavy (<kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd>,
  `]s`, <kbd>Alt</kbd>+<kbd>N</kbd>). Write raw `<kbd>` HTML, which renders on both GitHub
  and the site, rather than `++ctrl+shift+p++`, which GitHub shows literally.
- **At most one diagram per concept page** (sase's rule). Use Mermaid for flows: the
  thin-client capture round-trip, and the derived lane transitions as a state diagram.
- **Screenshots are reproducible, never hand-made:**
  - **CLI:** static SVG terminal captures (crisp, tiny, theme-friendly) or a VHS tape for
    the single hero loop. Respect `prefers-reduced-motion`. Use a poster frame.
  - **Mac Capture:** extend the existing render-fixture tests
    (`BOB_MAC_CAPTURE_RENDER_DIR`) so CI on `macos-26` writes panel PNGs. The glyph
    design tests already do this.
  - **Obsidian:** a scripted checklist against the **demo vault** with fixed window size,
    theme, and zoom. These are the only manual captures, kept few and dated in a manifest
    so stale ones are visible.
- **Accessibility:**
  - AA contrast in both themes;
  - alt text on every image;
  - no information carried by color alone (chips have text);
  - reduced motion respected;
  - keyboard navigation (built in).

### Page anatomy

The templates, ported from sase's `_templates/`:

- every page opens with one sentence saying what it is for;
- tutorials end with "You have …" and "Next";
- how-tos have numbered steps, each with a confirmation, plus one failure section;
- concepts follow: purpose → one picture → how it works → when it matters → Related;
- reference pages are tables and lists, with generated blocks marked.

---

## 9. Reliability

| Guard | Where | What it catches |
| --- | --- | --- |
| `zensical build --strict` with `validation:` on | `just docs-check`, hub CI | Broken internal links and anchors fail the build ([validation][zen-val]). |
| **lychee** on the built `site/` (`--offline --include-fragments`, plus a slower scheduled external-link pass) | same | An independent link and anchor checker that works with any builder. It also catches links the assembler rewrote wrongly. |
| **Plugin allowlist lint** (search, redirects, tags, llmstxt) and `hooks:` forbidden | docs lint | Zensical *silently ignores* unknown plugins, so a misconfiguration would ship unnoticed. |
| **Generated reference with `--check`** (CLI from clap via a dev-only `cargo run --example docgen` or a golden test, not a new public subcommand; later plugin hotkeys from `addCommand`, and Mac keymaps from the Swift registry) | `just check` in each repo | Drift between code and Reference. Hidden aliases stay hidden, following `cli_rules`' "never hard-rename … hidden alias" rule. |
| **Tutorial runner**: shell blocks in `start/` run against a fresh temporary `HOME` and a synthetic demo vault, with `<!-- tutorial-test: skip|expect -->` markers, as in sase | slow lane / scheduled | Tutorials that stop working. |
| **URL contract**: a frozen list of every published URL and every URL printed by `bob --help` or written in READMEs, resolved against the built site | `just docs-check` | Broken inbound links. When a move is unavoidable, the redirects plugin emits a static redirect page. |
| **Docs lint**, ported and trimmed from sase's `check_docs`: frontmatter (`title`, `description` ≤160 characters), word budgets per tier (contracts exempt or warn-only), guide hygiene (no bead IDs, `src/` paths, or history phrases outside Develop and Contracts), and no files at the `docs/` root except `index.md` | `just docs-check` | IA erosion over time. |
| **Privacy check**: no real-vault paths or names in examples; images must come from the demo vault manifest | docs lint | Leaking content from the private vault. |
| Pinned toolchain: `zensical` pinned through a uv lockfile under `tools/docs/` (outside `docs_dir`); exact action majors | repo | Surprise upgrades. Zensical's own guidance is to avoid CI caching for now. |
| Deploy safety: concurrency group `pages`, deploy only from the default branch, post-deploy `curl` of the frozen URLs | hub CI | Partial or broken deploys. A failed build keeps the last good site. |
| **Agent reader test** (Phase 5): a fresh agent with only the published site or `llms.txt` gets sase's six-task protocol adapted to Bob, and you record which door it picks first and whether it finishes | manual, per milestone | Bad door labels. This is a cheap stand-in until real outside readers exist. |

### Portable-Markdown rule

Agents and GitHub read these files too. Prefer syntax that renders well in both places:

- GitHub-style `> [!NOTE]` callouts (Zensical renders them as admonitions; see its
  [admonitions docs][zen-adm]);
- standard tables;
- `<kbd>`;
- fenced code.

Avoid content tabs and `!!!` blocks on pages agents rely on.

---

## 10. Authoring contract for Bob (a short `develop/writing-docs.md`)

Port sase's contract nearly as-is, with these Bob-specific rows:

- **The placement test** is Diátaxis's two questions, action or cognition, and
  acquisition or application ([compass][dx-compass]). Contracts are a fifth bucket:
  "a spec that tests or two runtimes must agree on".
- **Routing table:**

  | Change | Where it goes |
  | --- | --- |
  | New CLI flag or command | Regenerate the reference. Improve the clap help text instead of adding prose. |
  | New plugin hotkey | Regenerate or update that plugin's reference page in bob-plugins. |
  | Behavior change | Update its Contract or Reference. Fix a guide step only if it is now wrong. |
  | New user goal | File a "guide candidate" follow-up. |
  | Design decision | Decision record. The Design decisions page regenerates. |

- **IA is a human decision** (from sase): agents never move pages between tabs without an
  approved plan, and moves are move-only commits.
- **Plugins:** only search, redirects, tags, and llmstxt. No `hooks:`. Generation runs in
  `tools/` before the build.
- **The demo vault** is the only source for examples and images.

---

## 11. Open questions for Bryan

1. **URL:** is `bobs-org.github.io` acceptable for launch? Or do you want a domain from
   day one, to avoid ever announcing two URLs (even though GitHub keeps serving
   project sites under the new domain)?
2. **License:** MIT for bob-cli and bob-mac-capture, to match bob-plugins?
3. **Audience:** do you *want* others to run Bob? That sets how much "install from zero"
   effort the tutorial gets.
4. **Contracts move:** approve the one-time `docs/contracts/` move, with about 440
   mechanical reference updates across three repos, before launch?
5. **Secrets:** OK to add one org secret plus a small dispatch workflow to bob-cli and
   bob-plugins? They currently have no Actions.
6. **Labels:** keep sase's door labels (Learn / Do / Understand / Look up) for cross-site
   consistency?
7. **Indexing:** fine for search engines to index the site? The repos are already public.

---

## Recommended solution

**Build one Bob documentation site at `https://bobs-org.github.io/` with Zensical, using a
`mkdocs.yml` that is also Material-compatible. Organize it with Diátaxis tabs (Get started
· Guides · Concepts · Reference · Develop) and a Contracts section for Bob's existing
specs. Keep the source with the code, and deploy with GitHub Actions from a thin
`bobs-org.github.io` repo. Style it from Bob's own mark, teal, tomato, and fonts. Make it
reliable through generated reference, a strict and link-checked build, a tested tutorial,
and URLs frozen at launch.**

### Phased plan

Each phase publishes. Diátaxis says ship every step.

**Phase 0 — Decisions and prerequisites** (Bryan, about one hour)

- Answer §11. Add LICENSE files.
- Create `bobs-org/bobs-org.github.io` and set Pages → Source to GitHub Actions.
- Create the org dispatch secret.

**Phase 1 — A useful site on day one** (agents, about 3–5 days)

- Move-only commit: `docs/*.md` → `docs/contracts/`, with the reference `sed` in all three
  repos. Help text switches to site URLs.
- Add `mkdocs.yml` using the allowlisted features only, the brand (SVG mark, tokens,
  self-hosted fonts, `bob-task` style), and the homepage.
- Generate the CLI reference from clap with `--check`.
- Generate the Glossary and Design decisions pages.
- Add `just docs-serve`, `docs-check`, `docs-build`, and `docs-publish`.
- Add lychee, the docs lint, the URL contract, and the hub `deploy.yml`, plus dispatch
  workflows in all three repos.
- **Acceptance:**
  - the site deploys from a push to any of the three repos;
  - strict build and lychee are clean;
  - every URL printed by `bob --help` resolves;
  - no empty tabs.

**Phase 2 — The Learn path** (about one week)

- Synthetic demo vault, plus the tutorial runner.
- `start/install` and `start/first-day`.
- `concepts/how-bob-works` with the single system diagram.
- An honest "Is Bob for me?" page.
- Slim the bob-cli README into a front door.
- **Acceptance:** the tutorial runs green in a temporary `HOME`, and you walk it once on a
  clean machine.

**Phase 3 — Guides and concepts** (iterative, about two weeks; parallel agents via plans
or beads)

- Harvest 10–15 goal-titled guides and 5–6 concepts from README and contract material.
- Contracts stay authoritative, and guides link to them rather than restating them.
- Component tags plus the "By component" index.

**Phase 4 — Product reference** (iterative)

- Split the Mac Capture README into `bob-mac-capture/docs/` reference pages; its
  troubleshooting content becomes guides in bob-cli.
- Split the plugin table into per-plugin pages under `bob-plugins/docs/`, with generated
  command and hotkey tables and generated versions (this fixes the stale `2.7.2`
  string).
- Add CI-rendered Mac panel screenshots.

**Phase 5 — Polish and proof**

- `llms.txt` through Zensical's `llmstxt` plugin; social cards; a dated Obsidian
  screenshot set.
- The first agent reader-test round, with door labels revised against recorded misses.
- Optional: a custom domain, or a WASM capture-grammar playground.

### Why this is the right call

- **Intuitive:**
  - one site;
  - one search;
  - doors by reader goal;
  - products shown only as tags and reference sections;
  - the same door labels and layout as sase.sh.
- **Reliable:**
  - a single source with the code;
  - generated facts;
  - strict build plus an independent link check;
  - a tested tutorial;
  - frozen URLs;
  - push-triggered deploys with a cron safety net;
  - a pinned builder, with a second builder that reads the same config.
- **Beautiful:**
  - the brand is Bob's real identity, not a stock theme;
  - task lines look the way they look in Obsidian;
  - typography already licensed and bundled;
  - AA contrast in both themes.
- **Cheap:** $0 in hosting, and about one hour of your own time before agents take over.

---

## Sources

- Diátaxis — [How to use Diátaxis][dx-how] · [Start here][dx-start] ·
  [The compass][dx-compass] · [Map][dx-map]
  (`https://diataxis.fr/complex-hierarchies/` returned 404 on 2026-10-19)
- GitHub Docs — [Pages limits][gh-limits] · [What is GitHub Pages][gh-what] ·
  [Custom workflows for Pages][gh-workflows] · [Custom domains][gh-domain] ·
  [Disable and enable workflows (60-day rule)][gh-disable]
- Zensical — [PyPI][zen-pypi] · [Upcoming changes / 0.1 on 2026-11-05][zen-up] ·
  [MkDocs migration][zen-mig] · [Supported plugins][zen-plugins] ·
  [Validation / strict][zen-val] · [Diagrams][zen-diag] · [Navigation][zen-nav] ·
  [Code blocks][zen-code] · [Admonitions][zen-adm] · [Publish your site][zen-pub]
- Material for MkDocs — [What MkDocs 2.0 means (incl. maintenance extension to
  2027-05-05)][mat-mk2] · [Zensical announcement][mat-zen]
- Starlight — [Plugins and integrations (sidebar topics)][sl-plugins]
- Local evidence (read through `sase repo open`): `sase-org/sase` (`mkdocs.yml`,
  `mkdocs-pdf.yml`, `requirements-docs.txt`, `wrangler.jsonc`,
  `.github/workflows/docs-deploy.yml`, `docs/contribute/writing-docs.md`,
  `docs/contribute/reader-testing.md`, `docs/_templates/`, `docs/_meta/`); the
  `bobs-org/bob-plugins` and `bobs-org/bob-mac-capture` READMEs; bob-cli `docs/`,
  `README.md`, `assets/print_fonts/`, and `bob --help`.

[dx-how]: https://diataxis.fr/how-to-use-diataxis/
[dx-start]: https://diataxis.fr/start-here/
[dx-compass]: https://diataxis.fr/compass/
[dx-map]: https://diataxis.fr/map/
[gh-limits]: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
[gh-what]: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
[gh-workflows]: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
[gh-domain]: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages
[gh-disable]: https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows
[zen-pypi]: https://pypi.org/project/zensical/
[zen-up]: https://zensical.org/upcoming-changes/
[zen-mig]: https://zensical.org/docs/compatibility/mkdocs/migration/
[zen-plugins]: https://zensical.org/docs/compatibility/mkdocs/plugins/
[zen-val]: https://zensical.org/docs/setup/validation/
[zen-diag]: https://zensical.org/docs/authoring/diagrams/
[zen-nav]: https://zensical.org/docs/setup/navigation/
[zen-code]: https://zensical.org/docs/authoring/code-blocks/
[zen-adm]: https://zensical.org/docs/authoring/admonitions/
[zen-pub]: https://zensical.org/docs/publish-your-site/
[mat-mk2]: https://squidfunk.github.io/mkdocs-material/blog/2026/02/18/mkdocs-2.0/
[mat-zen]: https://squidfunk.github.io/mkdocs-material/blog/2025/11/05/zensical/
[sl-plugins]: https://starlight.astro.build/resources/plugins/

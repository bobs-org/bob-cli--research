# Bob public documentation: design, architecture, and hosting recommendation

Independent research by **cdx**, 19 October 2026.

## Decision in brief

Build **one Bob documentation site** covering the CLI, Obsidian plugins, and Mac Capture. Use **Astro Starlight**, publish it on **GitHub Pages at `https://bobs-org.github.io/`**, and keep technical documentation beside the code that owns it. A small public `bobs-org.github.io` repository should own presentation, navigation, and a pinned manifest of the three content sources.

The idea is good. Bob already has enough substantial behavior, interfaces, and dependencies to benefit from a proper documentation product. The opportunity is primarily **better onboarding, navigation, and maintenance**, not producing more words. Launch with one verified beginner journey, clear component requirements, task-oriented guides, and searchable reference. Improve the existing material incrementally.

This differs deliberately from copying SASE's implementation: borrow its information design, executable tutorials, generated facts, and preservation of old links. Its current Material for MkDocs stack is entering end of life, so copying the stack would add a near-term migration obligation. The stack decision is current research, not a claim that SASE should migrate immediately.

## 1. Scope, evidence, and limitations

I independently inspected the three Bob checkouts, SASE's source and public site, the specified Diátaxis page, and official hosting/framework documentation. I did not consult another researcher’s report, findings, or conversation. No website, repository, deployment, or product change was made during this research.

The repository evidence below is pinned to these observed commits:

| Repository | Inspected commit | Relevant evidence |
| --- | --- | --- |
| `bobs-org/bob-cli` | `bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111` | README, 27 Markdown files under `docs/`, Cargo metadata, command definitions, `justfile` |
| `bobs-org/bob-mac-capture` | `f7e635ac456e706c2185aaf1ed31acea1e89a8f5` | README, package/build instructions, macOS CI |
| `bobs-org/bob-plugins` | `ef1a63c23a6c4f9861db37ad33d1c546899b5c83` | README, plugin manifests, package scripts, repository instructions |
| `sase-org/sase` | `4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf` | `mkdocs.yml`, docs writing/reader-testing contracts, CSS, deployment and CI workflows |

GitHub repository metadata returned `PUBLIC` and default branch `master` for all three Bob repositories. Their homepage fields were empty. A metadata lookup could not resolve `bobs-org/bobs-org.github.io`; that supports proposing the name, but does not establish organizational permission to create or configure it. These were metadata queries, not an audit of account billing or Pages settings.

This is an architecture and content audit. I did not run a fresh Bob installation, build competing documentation prototypes, test a proposed demo vault, measure site performance, or conduct reader interviews. Proposed performance budgets, success rates, and effort estimates below are acceptance targets or planning judgments, not measured results. Current external service policies should be rechecked when implementation begins.

## 2. What the existing repositories reveal

### There is considerable documentation already

The CLI README is 1,584 lines, and its 27 `docs/*.md` files contain another 25,112 lines. `docs/capture.md` alone is 6,371 lines. Mac Capture's README is 2,807 lines. The plugins README is 579 lines, including exceptionally long table cells. Line counts include code and tables; they are evidence of document size, not a quality score. [CLI README][cli-readme] · [CLI guide index][cli-index] · [Capture contract][cli-capture] · [Mac README][mac-readme] · [Plugins README][plugins-readme]

The CLI already provides an unusually useful getting-started guide, including vault configuration, first capture, a session, command effects, and troubleshooting. Preserve that work. Its weakness as a first tutorial is the number of concepts, alternatives, and edge cases it introduces before a newcomer has established confidence. [CLI getting started][cli-start]

The Mac README places a large compatibility/protocol description under Requirements before Development. That is valuable integrator material but a difficult first encounter for someone asking how to install the panel and capture a task. Split the entry page, user operations, troubleshooting, and protocol reference. [Mac requirements][mac-readme]

### Public onboarding is a product boundary, not merely a writing task

Bob is an opinionated Obsidian workflow. The existing guide explicitly says it does not bootstrap the vault, daily notes, Obsidian settings, or Git remote. It requires particular Tasks metadata/status settings for some operations. Plugin synchronization copies assets but does not enable plugins or create dashboard notes. Basic CLI capture and native queries can work without desktop Obsidian. [CLI getting started][cli-start]

The Mac app currently documents macOS 26 and the matching Apple toolchain, source builds, signing behavior, executable discovery, permissions, and substantial Bob capability dependencies. Present those honestly. Do not advertise a generic “download and start” experience or a supported packaged installer unless that distribution path has separately been verified. [Mac requirements and installation][mac-readme]

The plugins README says “six plugins” and calls the repository private, while GitHub reports it public and seven plugin manifests exist in the inspected tree, including `bob-articles`. It also contains an old `bbugyi200/bob-cli` deployment link. These are concrete reasons to make counts and component listings generated facts, and to review public-facing claims before migration. This finding does **not** establish official community-plugin distribution or full mobile compatibility; neither follows from repository visibility or `isDesktopOnly: false`. [Plugins README][plugins-readme] · [Plugin manifest directory][plugins-tree]

### Shared behavior makes three isolated sites a poor default

The Mac app delegates capture interpretation, preview, completion data, and vault mutation to Bob. Meanwhile, important Obsidian UI behavior is documented in CLI guides as well as the plugin README. Readers work across these components. A repository-first documentation architecture would force them to discover the implementation boundary before understanding their task. [Mac architecture statement][mac-readme] · [CLI guide index][cli-index]

Keep those boundaries visible for contributors and troubleshooting, but organize the reader experience around Bob workflows. Shared capture grammar gets one canonical owner in bob-cli; Mac documentation explains how to use that grammar through its interface, linking to the grammar reference.

## 3. What to borrow from Diátaxis and SASE

The linked Diátaxis guidance argues for improving small pieces according to reader needs, rather than treating four empty categories as a completion checklist. Its practical implication here is to publish one useful end-to-end journey, then improve the next concrete reader problem. Do not postpone publication until all existing prose has been reorganized. [Diátaxis guidance][diataxis]

Use familiar navigation labels, while applying the four documentation modes editorially:

| Reader need | Site label | Bob example |
| --- | --- | --- |
| Learn through guided practice | Get started | Capture one task and complete one session in a sample vault |
| Accomplish a specific goal | Guides | Move an existing task into today's work |
| Look something up | Reference | Capture syntax, command flags, settings, shortcuts |
| Understand the model | Concepts | Why status, review freshness, and today's work are different |

SASE provides a more useful precedent than its theme alone:

- Its main navigation distinguishes Get started, Guides, Concepts, Reference, and Contribute; the homepage routes readers by intent.
- Its writing contract separates task guides from lookup material, uses templates, generates factual reference where possible, and treats inbound links as a compatibility obligation.
- Its CI has executable tutorial coverage in an isolated home, with explicit exclusions for steps requiring real people or infrastructure.
- Its reader-testing process observes newcomers choosing a route and completing tasks, instead of assuming the labels work.

These are directly inspectable in [SASE navigation][sase-config], [writing docs][sase-writing], [reader testing][sase-readers], and [CI][sase-ci]. Borrow their principles at Bob's scale; do not reproduce the entire lint policy, PDF pipeline, blog, diagram system, or metadata machinery before Bob needs them.

A useful correction to the hosting analogy: SASE's inspected deployment workflow publishes to a **Cloudflare Worker**, not GitHub Pages. Its Markdown and site-generation approach is separable from that host. [SASE deployment workflow][sase-deploy]

## 4. Adjustments to the requirements

| Original ambition | Recommended adjustment | Why it is justified |
| --- | --- | --- |
| Excellent documentation for all three repos | One coherent Bob site, with clear CLI, Obsidian, and Mac entry points | Most user goals cross repository boundaries |
| Diátaxis-inspired | Apply the modes to each page; do not require a complete four-part hierarchy per repo | Avoid duplicated concepts and empty sections |
| Broad coverage | Launch a complete small journey, then migrate reference in useful increments | A verified path is more valuable than an exhaustive unreviewed import |
| Public documentation | Add a synthetic sample vault and an explicit supported-setup description | Current setup assumes substantial prior configuration |
| Follow SASE | Reuse its editorial and verification practices; evaluate the generator independently | Material's lifecycle changes the cost of a new adoption |
| Beautiful | Make reading, search, examples, navigation, and accessibility the design deliverable | A striking homepage cannot compensate for dense or unreliable content |
| Reliable | Define content ownership, tested component combinations, link preservation, and update checks | Hosting uptime alone does not keep advice correct |
| All versions/features | Start with one tested rolling snapshot and a compatibility page | The three components do not currently present one shared release version |
| Implementation scope | Treat installers, vault bootstrap commands, plugin marketplace publishing, and product behavior changes as separate decisions | Documentation should expose these needs without silently expanding into a distribution project |

The sample vault is the most consequential added requirement. It should be a tiny, inspectable documentation fixture containing synthetic notes and only the settings required for the tutorial. It must not contain Bryan's vault data, secrets, Git remotes, background automation, or personal sync configuration. Do not redistribute third-party plugin binaries as an accidental part of the fixture; document their normal installation separately. This is not a proposal to modify Bob's task semantics.

## 5. Hosting: GitHub Pages is a good fit

**Yes, free `github.io` hosting fits this project.** GitHub Pages supports public repositories on GitHub Free, including Free organizations. An organization repository named `bobs-org.github.io` supplies the root address; a project repository supplies an address such as `bobs-org.github.io/bob-cli/`. A custom domain can be added later. [GitHub Pages overview][pages-about]

Prefer the organization root because the documentation covers an ecosystem. If that root is reserved for a future organization homepage, use a dedicated `bob-docs` project site at `/bob-docs/` instead. The architecture is otherwise unchanged. Do not make the public address look like the other two products are subordinate to the CLI unless avoiding another repository is an explicit priority.

GitHub supplies HTTPS for the `github.io` address. Configure the generated site's canonical URL and deployment base consistently. With Astro, an organization-root deployment uses the normal root base; a project deployment needs its repository prefix. Verify deep URLs, images, search indexes, and error pages at the real base, not only at localhost `/`. [Pages HTTPS][pages-https] · [Astro deployment guide][astro-pages]

The relevant Pages limits are a 1 GB published site, a soft 100 GB/month bandwidth limit, and a 10-minute deployment timeout. Its soft 10-builds/hour limit does not apply to custom Actions workflows. These are generous for compressed screenshots and text, but they are a reason not to put app binaries or large tutorial videos in the site artifact. [Pages limits][pages-limits]

Standard GitHub-hosted runner usage for public repositories/Pages is free under the current policy. Larger runners and storage allowances require separate attention. Use standard Linux runners for docs, short artifact retention, and bounded media. “Free hosting” does not mean unlimited storage or zero maintenance effort. [Actions billing][actions-billing]

| Option | Assessment for Bob |
| --- | --- |
| GitHub Pages | Recommended production host: repository-integrated static publishing and no additional hosting account needed |
| Cloudflare Pages | Strong alternative when shareable preview URLs or hosting controls become important; its documented automatic PR previews apply to branches from the connected repository |
| Existing SASE Cloudflare Worker approach | Reusable experience, but not necessary to deliver Bob's present static-site requirements |
| Three independent Pages sites | Technically simple individually; weak shared navigation, search, terminology, and compatibility story |
| A hosted documentation SaaS | Reconsider if editorial collaboration becomes the bottleneck; current requirements do not justify another platform |

Cloudflare's preview behavior is documented in its [preview-deployment guide][cloudflare-preview]. Do not assume GitHub Pages provides a separate automatic preview site for every PR. For the first release, a local production preview plus a downloadable built-site artifact is enough; add a dedicated preview service when reviewer friction justifies it. No custom domain purchase is needed now.

## 6. Generator choice

| Candidate | Strength for this project | Cost or concern | Judgment |
| --- | --- | --- | --- |
| **Astro Starlight** | Markdown authoring, built-in static search, navigation, highlighting, themes; flexible enough for a distinct Bob design | Adds a Node build in the site repo; multi-repo assembly and checks still need to be designed | **Recommended** |
| Material for MkDocs | Closest to SASE; familiar configuration and Markdown toolchain | Official site announces end of life on 5 May 2027 | Reasonable bridge for an existing site, weak default for a new one |
| Zensical | Material successor, compatible with much existing MkDocs content and styling | Its dependable 0.1.0 release line is announced for 5 November 2026; compatibility/extensibility remain specific capabilities to verify | Best alternative if SASE toolchain reuse outweighs current transition risk |
| Docusaurus | Established docs platform with built-in versioned-doc workflows | More machinery than the proposed single-snapshot site needs | Reconsider for several actively supported release lines |
| Antora | Explicit multi-repository aggregation and version-aware content model | AsciiDoc would add conversion and authoring costs to a large Markdown corpus | Reconsider if independently versioned component manuals become the dominant requirement |

Starlight's documented defaults cover the main reading experience, and its Pagefind integration provides full-text search without a separate search service. It supports page-specific edit links, so each published page can direct corrections to its owning repository. These capabilities avoid building a custom documentation application. [Starlight][starlight] · [Search][starlight-search] · [Page frontmatter][starlight-frontmatter]

The Material lifecycle concern is explicit, not inferred: its official homepage states the end-of-life date. Zensical's announcement distinguishes a future milestone from what is already available, and its roadmap says delivery order/dates are not promises. In particular, do not choose it on the assumption that every MkDocs plugin or multi-project capability is already equivalent. [Material status][material] · [Zensical announcement][zensical-changes] · [Zensical roadmap][zensical-roadmap]

Docusaurus itself warns that versioning adds contribution/build complexity. Antora explicitly supports aggregation from multiple versioned repositories and uses AsciiDoc. Both solve real problems; Bob need not pay for those capabilities before it needs them. [Docusaurus versioning][docusaurus] · [Antora][antora]

The practical compromise is portable Markdown, a small amount of site-owned Astro/CSS, and very limited theme overrides. Use MDX only where a demonstrated interactive example warrants it; plain reference pages should remain ordinary Markdown. Keep generator-specific code out of the Rust and Swift product builds.

## 7. Information architecture and content ownership

### Reader-facing structure

Use a small top navigation: **Get started · Guides · Concepts · Reference · Contribute**, with persistent search, theme control, and repository links. The homepage also offers component shortcuts for “CLI”, “Obsidian”, and “Mac Capture”. Those are alternative entry points into the same content, not three separate manuals.

An initial populated route set could look like this; these are proposed routes, not existing pages:

```text
/
/start/                         Choose a supported path
/start/first-task/              One guided CLI/sample-vault journey
/start/obsidian/                Continue that journey in Obsidian
/start/mac-capture/             Continue through the Mac panel
/guides/install-and-update/
/guides/capture-and-route/
/guides/plan-and-close-a-session/
/guides/troubleshoot-mac-capture/
/concepts/how-bob-fits-together/
/concepts/tasks-review-and-today/
/reference/cli/
/reference/capture/
/reference/plugins/
/reference/mac-capture/
/reference/compatibility/
/contribute/
```

Only show links when their destination is useful. Do not manufacture pages to fill the tree. Reference can initially link to still-canonical repository documents while they are being reviewed and split.

### One source of truth for each fact

| Content | Canonical owner |
| --- | --- |
| Core workflow, capture grammar, CLI flags/configuration, shared data/JSON contracts | `bob-cli/docs/` |
| Obsidian setup, plugin behavior, commands, settings, keymaps, plugin development | `bob-plugins/docs/` |
| Mac installation/signing, UI operations, permissions, troubleshooting, app development | `bob-mac-capture/docs/` |
| Site shell, navigation, branding, publication manifest, link map, documentation contributor guide | `bobs-org.github.io` |

Cross-component tutorials can live in bob-cli because they exercise Bob's underlying workflow; link to the UI-specific guides. That is ownership for maintenance, not a repository hierarchy imposed on readers.

For each migrated topic, identify one canonical page and replace competing descriptions with links or short scope-specific summaries. For example, the Mac API decoder's compatibility behavior belongs in Mac integration reference, while the meaning of a capture token belongs in the CLI grammar. A plugin keyboard table may state the gesture's outcome and link to the shared model without replicating all its rules.

Keep each README a useful, short repository entry point: what it provides, requirements, an installation/development pointer, documentation, license, and contribution links. Preserve valuable detail elsewhere before shortening it. The README must still help a person reading GitHub without visiting the site.

### Source assembly without creating another content system

The site repository should keep a small `docs-sources.json` manifest containing each source repository, **immutable commit SHA**, approved source paths, and route namespace. Add a route map keyed by `(repository, source path)` so collisions fail explicitly. Build into a disposable staging directory; never commit copied Markdown as a second editable source.

The assembly step should do only a few things:

1. Check out the three declared revisions using read-only public access.
2. Copy explicitly allowed documentation and assets, rejecting path escapes, unsupported executable content, and duplicate routes.
3. Attach source provenance, canonical slugs, and edit links to the owning repo/path.
4. Resolve documentation links and assets through the route map, preserving fragments.
5. Run Starlight and verify the resulting static site.

For same-repo links, preserve author-friendly relative `.md` links in source and transform them through a Markdown parser during assembly. For cross-repo links, allow canonical site URLs and map the known site origin to the current preview base. Handle linked assets explicitly. Do not rewrite with broad regular expressions or silently leave a preview pointing at production for internal navigation. Check both GitHub source readability and the generated HTML.

A local override should let an author preview uncommitted docs from one repo against the pinned other two. Production builds must refuse local overrides. The build should never scan arbitrary sibling directories or assume the maintainer's checkout layout.

There is some coordination overhead here. The alternative, keeping every word centrally in the site repository, removes assembly but makes code/documentation changes cross-repo for every component. I favor colocation because Bob's behavior changes frequently. Keep the assembler narrow; if it grows into a complex content database, revisit that tradeoff or Antora rather than inventing a new platform.

## 8. A concrete visual direction

Design Bob as a **calm working notebook**: warm paper, dark ink, restrained tomato and teal accents, clear section rhythm, and real examples of work being captured. This fits an Obsidian/Pomodoro tool better than a large abstract marketing illustration. Use Bob's existing iconography where appropriate; the site's identity should be related to the product without imitating the app chrome everywhere.

Proposed homepage composition:

```text
Bob                  Get started  Guides  Concepts  Reference    Search

Capture a thought. Choose your work. Keep a record.
An Obsidian workflow with a CLI and a native Mac capture panel.

[ Try Bob in a sample vault ]  [ See how the pieces fit ]

[ Real synthetic example: capture -> task -> daily work record ]

Start here                  Find an answer
CLI | Obsidian | Mac         Capture | Shortcuts | Configuration | Troubleshooting

Requirements and maturity   Contribute   Source repositories
```

This copy is a proposed direction, not a final product claim. The first screen should show who Bob is for, which pieces are optional, the real platform constraints, and one next action. A newcomer should not have to interpret repository names or a diagram of internal modules first.

For article pages, retain the familiar documentation pattern: a compact left navigation, a readable center column, and an “On this page” rail on wide screens. Collapse rails on mobile. Use approximately 65–75 characters per line, 17–18 px body text, comfortable line height, and system fonts or a carefully subsetted local font. Code should have a copy control, a shell/language label, clear separation of commands from output, and no prompt characters included in copied text.

Candidate palette, calculated with the standard sRGB relative-luminance formula during this research:

| Use | Foreground / background | Calculated contrast |
| --- | --- | --- |
| Light body | `#171C1A` / `#FBF8F2` | 16.27:1 |
| Light tomato accent text | `#9B3D2D` / `#FBF8F2` | 6.39:1 |
| Light teal link | `#0F6B63` / `#FBF8F2` | 6.00:1 |
| Dark body | `#EEF3ED` / `#121816` | 15.99:1 |
| Dark warm accent | `#F58B72` / `#121816` | 7.55:1 |

These individual pairs exceed WCAG's 4.5:1 ordinary-text minimum; this is not a site accessibility certification. Hover, selected, disabled, focus, and code-token states still need testing. Underline prose links and never use color alone to communicate a task state. [W3C contrast guidance][contrast]

Prefer two or three tightly cropped screenshots from the same synthetic vault over many ornamental graphics. Include explanatory captions, alt text, and the tested component versions. A small SVG diagram can show `Mac panel → bob → Markdown vault`, with plugins providing the Obsidian interface; it should clarify responsibility, not imply all plugin mutations go through the CLI. Avoid autoplay video. A short user-controlled demo can come after the static explanation works.

Use standard theme tokens before overriding components. Starlight supports CSS customization, but every custom component creates an upgrade obligation. The initial custom surface should be limited to the homepage, Bob colors, source/compatibility metadata, and any genuinely missing example component. [Starlight styling][starlight-style]

## 9. Reliability and publication design

### Documentation must tell readers what it was tested against

A timestamp or “latest” label is insufficient. Publish a small compatibility page with the CLI source revision, Mac source revision, plugin versions, relevant Obsidian/Tasks requirements, and tested features. Distinguish a tested combination from a minimum requirement derived from code or documentation.

Initially label the site as documentation for a **tested rolling source snapshot**. `bob-cli`'s inspected package version is `0.1.0`, while the plugins have independent versions and the Mac README describes feature-level compatibility. A global “Bob v1” switcher would suggest a release alignment that has not been established. [CLI package metadata][cli-cargo] · [Plugin manifests][plugins-tree] · [Mac compatibility][mac-readme]

Keep the previous known-good publication manifest for rollback. Add separate archived manuals only after there are multiple maintained release lines whose instructions materially differ. A source SHA makes a publication reproducible; it does not prove that its components interoperate. That needs explicit verification.

### Publishing flow

Use GitHub Actions with a separate build job and a deployment job that consumes the validated artifact. Pages requires appropriate `pages: write` and `id-token: write` permissions, an environment, and a dependency on the completed build. Restrict write permissions to deployment; the build checks out public content read-only. Serialize production deploys so an older build cannot overwrite a newer one. [Pages custom workflows][pages-workflows]

Use a package lockfile, a declared Node version, and pinned Action revisions with a deliberate update process. The artifact should include a machine-readable build manifest recording source SHAs and toolchain versions. A failure to fetch a source, validate a route, or build search must fail publication and leave the existing site in place; do not silently omit one component.

Start publication updates with reviewed manifest changes and a manual workflow trigger. A scheduled check can report when source docs have advanced, without changing the pins or publishing an untested combination. Add automated update PRs only when useful and when the repository's Actions policy allows them. The site's normal token does not automatically authorize writes/dispatches across the other repositories; avoid making cross-repo automation credentials an initial requirement.

A component PR that changes docs should build an integration preview with that candidate revision replacing its pinned source. Source-only lint is insufficient for cross-repo anchors and navigation. The publication manifest is then updated after the component change is merged. For coordinated breaking changes, update the necessary revisions together and rerun the relevant journey. Target same-day publication for user-visible changes, and show lag explicitly if the target is missed.

### Quality checks that earn their maintenance cost

| Check | Failure it should catch |
| --- | --- |
| Build and content schema validation | Missing titles, duplicate slugs, malformed pages, unapproved publication paths |
| Built HTML link/fragment and asset checks | Broken navigation, moved anchors, missing screenshots, wrong project base |
| Generated-reference drift check | CLI options or plugin inventory changed without updating reference |
| Executable tutorial in isolated fixture | A copied command fails or produces the wrong task/session outcome |
| Small browser smoke suite | Search, theme, copy controls, mobile navigation, and deep links fail in the actual build |
| Accessibility automation plus keyboard/screen-reader walkthrough | Focus traps, unusable dialogs, poor contrast, missing alternative text |
| Periodic external-link check | Remote resources move; keep network flakiness out of every code PR |

Generate factual material from its owner: plugin inventory from manifests and command/flag tables from Clap definitions or tested `--help` output. Do not generate explanatory semantics from names. The CLI already uses Clap command construction, so evaluate a documentation exporter before maintaining parallel option lists. Freeze locale, widths, and source revisions for deterministic generated output. This is a feasibility observation, not an implemented exporter. [CLI command construction][cli-runner]

Test the first tutorial's actual effects in a disposable vault: a task exists once, linking produces the intended daily entry, and closing creates the expected result. Isolate `HOME`, relevant XDG/config paths, `BOB_DIR`, and `BOB_DAY_FILE`; control the test date/timezone. Explicitly exclude network/sync hooks. For desktop workflows, use real macOS/Obsidian walkthroughs as a separate verification step. A Linux docs build cannot establish Mac permission or UI behavior.

Search needs Bob-specific testing. Pagefind's default full-text search is a good starting point, but punctuation-heavy grammar such as `x!`, `@route`, and `=` must not be assumed to work as desired. Give syntax pages semantic titles and descriptions, add a compact searchable syntax index, and test representative queries such as “complete all”, “x!”, “Pending”, “hotkey conflict”, and “install plugins”. If punctuation searches fail, improve searchable aliases or a small index before adopting a hosted backend.

### Preserve links during migration

Inventory the links currently used by README files and guides before moving content. Keep old source-path stubs where GitHub readers still need them, and publish static compatibility pages for moved website routes. A one-to-many split needs anchor-specific destinations; sending every old link to a large index is not preservation.

GitHub Pages does not give this static site a general application server for redirects. Use generated HTML redirect/stub pages with a visible destination link, canonical metadata, and preserved or explicitly mapped fragments. A JavaScript enhancement may route split anchors, but the page must still explain the destinations without it. Exclude compatibility stubs from search to prevent duplicate answers. Do not copy SASE's Cloudflare `_redirects` file and assume Pages will interpret it.

## 10. A launch sequence with exit criteria

This is a decision-oriented rollout, not a request to implement every item before publishing.

**First, prove the reader journey.** Define the supported initial audience as a technically comfortable person willing to configure an opinionated Obsidian workflow. Create the synthetic fixture and one short CLI tutorial based on the existing guide. Verify it from a fresh environment. Record any setup step requiring undocumented personal configuration; either supply the documented prerequisite or explicitly narrow the supported path. Do not hide gaps with prose.

**Next, prove the site architecture.** Build a representative slice: homepage, tutorial, one guide, one concept, and a substantial reference page, with at least one real page from each repository. Validate source ownership, local overrides, source/edit links, search, cross-repo links, dark mode, and the eventual deployment base. This spike is the decision checkpoint for Starlight and the bounded assembler. If SASE reuse is demonstrably cheaper, test the same slice with Zensical before changing the recommendation.

**Then, publish a useful first edition.** Add installation/update guidance for each component, a compatibility page, troubleshooting entry points, and short repository READMEs. Preserve unmigrated contracts as accessible reference. Set repository homepage links to the live site only after it is deployed and checked. Do not require complete migration of all 25,000+ lines to launch.

**Finally, improve through observed use.** Split capture/API reference by reader lookup tasks. Consolidate overlapping plugin/CLI explanations. Add verified screenshots and workflows as they earn their place. Keep ownership and checks part of ordinary product changes rather than running a periodic bulk rewrite.

Suggested acceptance criteria:

- Every repo links to a working component entry point and a meaningful install/development path.
- One newcomer can complete the first-task journey with only the documented prerequisites and fixture; aim for about 15 minutes after installing prerequisites, then measure rather than advertise an untested duration.
- At least four of five observed readers can find the correct installation, syntax, and troubleshooting destination without coaching.
- No broken internal page links, anchors, or assets in the published build.
- A deliberately broken source pin or link fails CI while the last good site remains available.
- The build displays a reproducible set of source revisions and a clearly labeled compatibility record.
- Core content remains readable without JavaScript; search may require it.
- Key pages work at 360 px and desktop widths, 200% zoom, keyboard-only navigation, and both color schemes.
- As initial engineering budgets, aim for an initial page below roughly 500 KB compressed excluding optional demos, a static published site below 100 MB, and a docs build comfortably under five minutes. Validate and revise these targets with a real prototype.

For planning, budget roughly **one to two focused engineering days for the representative slice**, followed by **several days for the first verified edition**. These are low-confidence estimates: installation friction, manual UI verification, and link-preserving content splits may dominate. A complete editorial migration is an ongoing maintenance project, not a reliable one-week promise.

## 11. Risks, tradeoffs, and reasons to choose differently

The largest risk is documenting a personal workflow as if it were already a general-purpose product. Public docs should explain the intended audience and required conventions rather than claim effortless adoption. A sample vault can make learning reproducible; it cannot substitute for a product decision about arbitrary-vault support.

A second risk is **a polished facade over contradictory contracts**. The observed private/public and plugin-count drift is a useful warning. Publish only reviewed content, show provenance, and migrate topics with ownership rather than bulk copying all Markdown into a theme. Explicitly exclude `sase/`, research reports, operational memories, and private vault material from the site input.

A third risk is **publication machinery consuming the project**. Pinning and aggregation improve reproducibility but require integration maintenance. Keep one manifest, one assembler, and one site build; avoid a CMS, runtime API, custom search backend, LLM chat, blog, PDF handbook, or elaborate version selector in the first release. Those are additions to justify with reader demand.

Choose **Zensical** instead if a representative Bob slice proves that reusing SASE's authoring/checking workflow saves material ongoing effort and all needed features work on a released version. That is a credible alternative, especially after the announced November milestone. Choose **Docusaurus or Antora** if multiple supported release lines become mandatory. Choose **Cloudflare Pages** if convenient hosted previews and hosting controls become more valuable than keeping hosting entirely within GitHub. Choose a **single centrally authored docs repo** if multi-repo assembly proves more expensive than the actual code/docs drift it prevents.

Before final implementation, resolve four concrete unknowns: who will own the organization Pages repository; which OS/Obsidian/Tasks combination is the public baseline; whether a fresh reader can complete the fixture without personal automation; and which component revisions are the first tested combination. These do not block building the representative slice, and none requires guessing a new product policy.

## Evidence links

Repository links below identify the inspected snapshots; external documentation was consulted on 19 October 2026. Future announcements are identified as announcements in the text.

[cli-readme]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/README.md
[cli-index]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/docs/README.md
[cli-capture]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/docs/capture.md
[cli-start]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/docs/getting-started.md
[cli-cargo]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/Cargo.toml
[cli-runner]: https://github.com/bobs-org/bob-cli/blob/bfca3419c3f5c4caa9a609c6e4f64a2dc6a86111/src/runner.rs#L1092
[mac-readme]: https://github.com/bobs-org/bob-mac-capture/blob/f7e635ac456e706c2185aaf1ed31acea1e89a8f5/README.md
[plugins-readme]: https://github.com/bobs-org/bob-plugins/blob/ef1a63c23a6c4f9861db37ad33d1c546899b5c83/README.md
[plugins-tree]: https://github.com/bobs-org/bob-plugins/tree/ef1a63c23a6c4f9861db37ad33d1c546899b5c83/plugins
[sase-config]: https://github.com/sase-org/sase/blob/4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf/mkdocs.yml
[sase-writing]: https://github.com/sase-org/sase/blob/4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf/docs/contribute/writing-docs.md
[sase-readers]: https://github.com/sase-org/sase/blob/4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf/docs/contribute/reader-testing.md
[sase-ci]: https://github.com/sase-org/sase/blob/4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf/.github/workflows/ci.yml
[sase-deploy]: https://github.com/sase-org/sase/blob/4e5b7d2eb6feff3d0c95f9f71d91ccbb494607cf/.github/workflows/docs-deploy.yml
[diataxis]: https://diataxis.fr/how-to-use-diataxis/
[pages-about]: https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages
[pages-https]: https://docs.github.com/en/pages/getting-started-with-github-pages/securing-your-github-pages-site-with-https
[pages-limits]: https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits
[pages-workflows]: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
[actions-billing]: https://docs.github.com/en/billing/concepts/product-billing/github-actions
[astro-pages]: https://docs.astro.build/en/guides/deploy/github/
[cloudflare-preview]: https://developers.cloudflare.com/pages/configuration/preview-deployments/
[starlight]: https://starlight.astro.build/
[starlight-search]: https://starlight.astro.build/guides/site-search/
[starlight-frontmatter]: https://starlight.astro.build/reference/frontmatter/
[starlight-style]: https://starlight.astro.build/guides/css-and-tailwind/
[material]: https://squidfunk.github.io/mkdocs-material/
[zensical-changes]: https://zensical.org/upcoming-changes/
[zensical-roadmap]: https://zensical.org/roadmap/
[docusaurus]: https://docusaurus.io/docs/versioning
[antora]: https://antora.org/
[contrast]: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html

## Recommended solution

Proceed with **one public Bob site on GitHub Pages, using Astro Starlight and the organization-root address `bobs-org.github.io`**. Keep product documentation in its owning repository and assemble only approved Markdown/assets from pinned revisions. Use one tested rolling snapshot, clear compatibility guidance, a synthetic sample vault, and a small set of enforced build/link/tutorial checks.

Borrow SASE's reader-oriented organization and verification discipline. Give Bob its own calm, readable visual identity. Start by proving a newcomer's first successful workflow, then publish a complete small edition and improve the existing reference incrementally. This delivers useful, attractive documentation now while keeping maintenance and future migration costs under control.

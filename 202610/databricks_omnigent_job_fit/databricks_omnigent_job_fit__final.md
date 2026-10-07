# Databricks Job Fit for a SASE Author, After Omnigent

- **Date:** 2026-10-07
- **Question:** Given Bryan's work on [SASE](https://github.com/sase-org/sase) and
  Databricks' release of [Omnigent](https://github.com/omnigent-ai/omnigent), which open
  Databricks roles is he a good match for?
- **Inputs:** five independent researcher reports (`__cdx`, `__cld`, `__grk`, `__mus`,
  `__gem`) plus lead verification. I pulled the Databricks Greenhouse feed again on
  2026-10-07 (894 live postings) and read the full text of every posting recommended
  below. I also checked Bryan's CV (dated 2026-04-21), local checkouts of SASE
  (`0a80039`) and Omnigent (`ee2488a`), and Omnigent's issue tracker.
- **Pay** is the **base** salary range printed in each posting. It excludes equity and
  bonus, which make up a large part of Databricks total compensation.

---

## Bottom Line

1. **The fit is real and specific.** SASE and Omnigent belong to the same category:
   a layer above coding-agent CLIs that wraps different harnesses behind one
   interface, isolates their work, governs it with policies and human approval, and
   lets a person supervise many agents. Databricks is clearly investing in that layer.
   Omnigent shipped as open source on 2026-06-13 and now also runs as a managed
   Databricks Beta, and the company is hiring around it.
2. **No live software-engineer posting names Omnigent.** Only three requisitions do:
   - **Sr. Developer Advocate, Open Source — Omnigent** (SF and Seattle).
   - **Staff Product Designer, Agentic Coding**, the Omnigent design lead.
   - **Manager, Developer Relations – Open Source**, which lists Omnigent among
     other topics.

   Any Omnigent engineering hiring runs through broader AI-org requisitions or
   referrals.
3. **The best engineering doors are in NYC, where Bryan already works.** Bryan works at
   Google in Manhattan, and Databricks opened an NYC R&D hub in January 2026 focused
   on agentic AI. Two roles fit:
   - **Staff SWE, Agent Quality**, a founding team building agent evaluation
     infrastructure. Python first.
   - **Sr. SWE – Backend, AI Platform**, which hires across MLflow, AI Gateway, Agent
     Framework, and Agent Bricks. That is the org whose engineers maintain Omnigent.
4. **The Omnigent DevRel role is the best topic match but the worst career-shape
   match.** It is the only role that works *on* Omnigent. It is also a move from
   engineering into developer advocacy (talks, meetups, community building), it pays
   less, and it requires relocating to SF or Seattle. Apply only if you want that job
   itself.
5. **Contribute before applying, but not the way one report proposed.** The Omnigent
   maintainers stopped accepting new harnesses into the main repo on 2026-09-22, and
   community volunteers have already started the Muse harness. Details are in §5.

---

## 1. Bryan's Profile as a Hiring Panel Will See It

Sources: CV (2026-04-21), GitHub, and the SASE checkout.

- **Experience:** About 7.4 years as a professional software engineer:
  - Edgestream, 2019–21.
  - Bloomberg, 2021–22, as a founding Compliance SRE engineer and Senior SWE.
  - Google Ad Manager in Manhattan, 2022 to now, doing full-stack Java and
    AngularDart work.
  - Earlier: Comcast Tier III support, 2011–16, including Python automation.

  The CV rounds the total to "~9 years". Expect Databricks to place him between
  Senior and Staff. Roles asking for 5+, 6+, or 7+ years are reachable. Roles asking
  for 8+ are a stretch, and 10+ or 12+ are unlikely.
- **Languages:** Python is primary. He has working Rust (SASE's required
  `sase-core-rs`), Java, and C/C++. **He has no Scala or Go**, which many Databricks
  backend Staff postings require.
- **SASE:**
  - Author and maintainer; MIT license; v0.17.1 on PyPI.
  - Python 3.12+ with a required Rust core.
  - Seven provider CLIs: Claude Code, Codex, Antigravity, Qwen Code, OpenCode, Muse
    Code, and Grok Build.
  - A Textual TUI, the AXE scheduler, and a YAML workflow engine.
  - Typed human-approval gates, numbered workspace isolation, and durable Patches,
    beads, artifacts, and ToolRuns.
  - Prometheus telemetry and the deterministic `fakey` provider for failure testing.
- **Other open source:** a roughly 3,500-line rewrite of `psf/black`'s string handling
  (PR #1132), `funky` (500+ stars), `cookie` (250+ stars), and python-boltons. Process
  work includes ChangeLog Driven Release at Bloomberg, a firm-wide Python cookiecutter,
  and a pylint rollout across 1M+ lines.
- **Update the CV before applying.** The April CV describes SASE as orchestrating
  "Claude, Gemini, and Codex". It now supports seven harnesses, has a Rust core, and
  has a docs site at sase.sh.

### How SASE Maps Onto Omnigent

| Omnigent concept | SASE analogue Bryan can demo |
| --- | --- |
| Meta-harness over many agent CLIs | Seven provider CLIs behind one provider interface (`llm_provider/base.py`), with model-alias routing |
| Contextual policies and human approval | Typed gates (sudo, plan, and question) with persisted decisions; holds, queue budgets, and `max_running_agents` |
| Sandboxing and execution hosts | A numbered git workspace clone per agent, claimed atomically before launch. This is isolation, **not** an OS or network sandbox |
| Durable sessions and artifacts | Patches, beads, goals, artifacts, and ToolRuns that live outside any one transcript |
| Supervising live sessions across devices | ACE TUI Agents tab, Rust mobile gateway, and Telegram plugin |
| Harness conformance bench | `fakey`, a deterministic provider that exercises launch, streaming, retry, and interrupt paths without model calls |
| Automations and YAML agents | The AXE scheduler, macros, and YAML workflows |

**One-sentence pitch:** "I built and run an open-source control layer for seven
coding-agent harnesses, with isolated workspaces, durable reviewable outputs, explicit
human decisions, and reproducible failure testing. I want to do that work at Databricks
on Omnigent, AI Gateway, and agent quality."

### Gaps a Panel Will Probe

1. **Adoption.** SASE has 5 GitHub stars and 1 fork; Omnigent has about 10.7K stars and
   1.7K forks. Present SASE as a working system you operate every day and will demo,
   not as traction.
2. **Distributed systems at scale.** Most AI Platform and Infrastructure postings center
   on large-scale services. That story has to come from the Bloomberg and Google
   years.
3. **Agent evaluation.** SASE has strong test and CI gating and deterministic failure
   fixtures, but no visible task-success eval harness. This matters for Agent Quality,
   Agentic Security, and CXI.
4. **Isolation is not containment.** SASE's Codex provider passes approval and sandbox
   bypass flags. Don't present workspace isolation as enterprise sandboxing.
5. **Lines of code aren't the pitch.** The SASE tree is very large and mostly
   agent-written. Sell design decisions and failure stories instead.

---

## 2. Omnigent and the Teams Around It

| Fact | Evidence |
| --- | --- |
| The correct name is **Omnigent**, not "Omniagent". It is an Apache-2.0 meta-harness over Claude Code, Codex, Cursor, OpenCode, Pi, Hermes, and others, with policies, OS and cloud sandboxes, and live session sharing. | [Launch post](https://www.databricks.com/blog/introducing-omnigent-meta-harness-combine-control-and-share-your-agents) (Zaharia, Uhlenhuth, Zumar; 2026-06-13); repo README |
| Omnigent is also a managed Databricks Beta, integrated with Unity AI Gateway and Databricks Sandboxes. | [Omnigent on Databricks docs](https://docs.databricks.com/aws/en/omnigent/) |
| The repo is mostly Python (about 3.5K `.py` files versus about 1.2K `.ts`/`.tsx`) and moves fast: about 1,400 commits since 2026-09-01. Active maintainers and assignees include `dbczumar`, `TomeHirata`, `serena-ruan`, `daniellok-db`, `fanzeyi`, `dhruv0811`, and `PattaraS`. | Local checkout; open issues |
| The core team comes largely from Databricks' MLflow and AI-platform engineering. That is the org behind the AI Platform backend postings. | `.github/MAINTAINER`, commit authorship. This is inferred; no posting names the team's org |
| Databricks opened an **NYC R&D hub** (2026-01-31) focused on agentic AI and LLMs, data infrastructure, and agentic business applications. | [NYC hub announcement](https://www.databricks.com/en/blog/announcing-databricks-new-york-rd-hub) |
| The Omnigent designer posting calls it "Databricks' platform for building, composing, governing, and sharing AI coding agents". | Staff Product Designer, Agentic Coding (`8854693002`) |

---

## 3. Where the Researchers Disagreed, and How I Resolved It

| Issue | Reports | Resolution (verified 2026-10-07) |
| --- | --- | --- |
| Is **Unity AI Gateway Staff** (`8468436002`, NYC) a top-3 target? | grk ranked it #3; cdx and cld skipped it | The posting requires **8+ years** and **"Scala, or Go"**, with Python not listed. It is the closest product (the control plane coding agents route through), but it is a stretch for Bryan. Name it to a recruiter rather than leading with it. |
| **Developer Ecosystem (SDK/CLI/Terraform)**, `6779943002` | mus ranked it #2 | **Not in the live feed.** Dropped. |
| **Omnigent DevRel** ranking | mus and gem: #1; cdx, cld, and grk: conditional | The topic match is excellent; the posting even wants someone who "has already wired up three coding agents". But the job is talks, meetups, content, and contributor growth, and it "thrives in the spotlight". Ranked conditionally. |
| DevRel location | gem: "Hybrid / Remote options" | **Unsupported.** The postings list only San Francisco and Seattle. |
| CXI role | gem: "Staff, 8+ years" | **Wrong.** It is **Sr Software Engineer – CXI** (`8617901002`, MV/SF), with no stated year count. |
| AI/ML Environments (`8233899002`) | gem: agent sandboxing | **Wrong.** It covers training and serving environment setup: virtual environments, containers, dependency management. Mountain View only. Low priority. |
| "Agentic Applications" roles | gem: 9/10 | These are the Marketing web-agents role (`8635182002`, 12+ years) and People-Tech HR agents (`8220840002`, 8+ years and 2+ years of production LLM work). Both are domain-specific. The Sr. role (`8220814002`) is mostly frontend. Not recommended. |
| Ship a **Muse or Grok harness PR** to Omnigent | cld's top recommendation | **Outdated.** On 2026-09-22 maintainer `PattaraS` wrote: "we won't add more harnesses into the main repository directly". Muse is now a community harness already being built by others ([R7L208/omnigent-muse](https://github.com/R7L208/omnigent-muse)). Grok Build is already supported as an ACP CLI harness (`omnigent/acp_cli_harnesses.py`). See §5 for revised advice. |
| gem's job links | Generic careers-page search links | Replaced with verified `gh_jid` links. gem's 10/10 scores were not evidence-based and are not used. |
| Levels.fyi total comp | cld quoted figures | Not independently verified, so omitted. Only posting base ranges are used. |

**New candidate I checked and rejected:** **Staff Partner Engineer, AI Partnerships**
(`8643452002`, NYC/SF). It names Claude Code and Codex and runs the technical
relationships with Anthropic, OpenAI, and Gemini. However, it requires 10+ years plus
established relationships inside AI labs. Not a fit now.

---

## 4. Ranked Fit for Live Postings

Every role below was present in the 2026-10-07 feed, and I read its full text.

### Apply first (NYC, engineering)

**1. Staff Software Engineer, Agent Quality**
- **Basics:** NYC; `8842963002`; base $200,000–$265,000; posted 2026-09-24.
- **Role:** A founding member of a new AI Research team that builds evaluation
  infrastructure for Genie Agents and "the agent development platform". The goal is a
  flywheel from evaluation results back into agent improvement.
- **Requirements:** 6+ years, strong Python, reliable and reproducible infrastructure.
  Nice-to-haves: **devtools, CI/CD, testing frameworks, observability, benchmarking**,
  and familiarity with LLM and agent evals.
- **Why it fits:** The nice-to-haves match the Edgestream test-framework work, the
  Bloomberg release tooling, and SASE's gates, telemetry, and deterministic `fakey`
  provider. The years bar is met.
- **Gap:** No formal LLM-eval system yet. Build a small one before interviewing (§5).

**2. Sr. Software Engineer – Backend (AI Platform)**
- **Basics:** NYC; `8379331002`; base $165,300–$219,675.
- **Role:** "Hiring across multiple teams" building MLflow, AI Gateway, Databricks Apps,
  Agent Framework, Agent Bricks, and Foundation Model APIs.
- **Requirements:** 5+ years; Scala, Go, **or Python**. Bonus points for "built
  developer platforms or internal tools supporting AI workflows" and OSS contributions.
- **Why it fits:** It is the safest level match and sits in the org that maintains
  Omnigent. Ask the recruiter to route you to the Omnigent, AI Gateway, or Agent
  Framework teams.
- **Gap:** Distributed-systems depth must come from the professional record.

### Apply if the conditions hold

**3. Sr. Developer Advocate, Open Source — Omnigent**
- **Basics:** SF (`8716187002`, Zone 1 base $149,200–$205,150) or Seattle
  (`8716730002`, $133,000–$186,100). Same requisition, RDQ327R182.
- **Requirements:** 5+ years *combined* DevRel and hands-on engineering, so SWE years
  count. Strong Python **and TypeScript**. An OSS track record, contributor-community
  growth, a public portfolio, and public speaking.
- **Gaps:** No talks or community growth on record, light TypeScript, and relocation.
- **When to apply:** only if DevRel is wanted for its own sake.

**4. Staff Security Software Engineer – Agentic Security Engineering**
- **Basics:** **Remote anywhere in the US**; `7932280002`; Zone 1 base
  $190,000–$261,250 (Zone 4 $152,000–$209,000).
- **Role:** A shared agent platform for security teams: sandboxing, least-privilege
  identity, observability, a reusable agent and tool catalog, evals, and MCP.
- **Requirements:** 7+ years and expert Python. Production agents "others depend on
  (prototypes and demos don't count)".
- **Fit:** A stretch. SASE covers the platform half; the security domain is the gap. It
  is the only relevant remote engineering role.

**5. Staff Backend Software Engineer (Databricks AI)**
- **Basics:** San Francisco; `8367019002`; base $166,000–$225,000.
- **Fit:** The same AI Platform scope as #2 at Staff title, also 5+ years with Python
  accepted. Only if relocating.

**6. Staff Backend Software Engineer – Unity AI Gateway**
- **Basics:** NYC; `8468436002`; base $190,000–$261,250.
- **Fit:** The closest product, since it routes every coding-agent request. But it
  needs **8+ years and Scala or Go**. Apply only if you can honestly claim that depth;
  otherwise name it to the recruiter for #2.

**7. Sr Software Engineer – CXI**
- **Basics:** Mountain View or SF; `8617901002`; base $164,200–$225,700.
- **Role:** A multi-tenant agent platform with "state-machine and agentic workflows that
  … evolve from human-in-the-loop validation to fully automated execution".
- **Fit:** Strong conceptual match to SASE's gates and workflows, but it needs
  production LLM orchestration and multi-cloud experience. Only if relocating.

**8. Senior Software Engineer – Infrastructure and Tools**
- **Basics:** SF; "candidates in other locations will be considered"; `6318503002`;
  base $166,000–$225,000.
- **Fit:** A devtools, CI, and build fallback, but much of the scope is Kubernetes and
  cloud infrastructure. It is a long-running pipeline requisition.

**9. Staff SWE, Fullstack – AI Product (NYC)**
- **Basics:** `8509534002`; base $190,900–$253,750.
- **Role:** "Never-seen-before interfaces for GenAI agents … keeping the human in the
  loop".
- **Fit:** Conceptually SASE's TUI, but it requires 10+ years each of HTML/CSS/JS and
  server-side work. A long shot.

### Reviewed and not prioritized

- **AI Runtime** (`8582276002`, `8582271002`) and **AI Research Infrastructure**
  (`8532682002`, `8552484002`, NYC/SF): GPU training and cluster schedulers. AI
  Research Infrastructure does accept Rust and mentions research dev tooling, but its
  core is GPU fleets and schedulers.
- **AI Engineer – FDE** (`8546367002`, US remote): customer-facing GenAI delivery with
  travel. SASE is supporting evidence only.
- **Applied AI Engineer, Genie Code** (`8091041002`): a good topic, but Belgrade only.
- **Staff Product Designer, Agentic Coding** (`8854693002`) and **Manager, DevRel –
  Open Source** (`8716189002`): design and management roles. They are useful
  intelligence about the Omnigent team.
- **Staff Partner Engineer, AI Partnerships** (`8643452002`), **Sales Data & Agents**,
  **Ads Measurement & Orchestration** (`8760165002`; Ad Manager background helps, but
  it requires 10+ years and measurement expertise), **Genie One Mobile & Desktop**, and
  **Sr. EM – Agentic Service Platform**, which is an RPC/service mesh platform despite
  the name.

---

## 5. How to Get Noticed by the Omnigent Team

1. **Contribute in a way the maintainers want.** New harnesses now ship as
   **community harness packages** through the `omnigent.community.harness` entry-point
   interface (`designs/harness-plugin-interface.md`), not as core PRs. Commits need a
   DCO `Signed-off-by`. Credible options:
   - **Join the existing Muse community harness**
     ([R7L208/omnigent-muse](https://github.com/R7L208/omnigent-muse)). Its
     maintainers are inviting help, and SASE already ships a Muse Code integration.
   - **Fix an unassigned runner, host, or worktree bug in core.** Many current issues
     match SASE experience: worktree base branches, runner file limits, host liveness,
     and scheduled automations. Most open help-wanted issues are already assigned to
     Databricks engineers, so check before starting.
   - **Build an interop demo** that runs SASE's durable review model on top of
     Omnigent sessions, or contribute to the harness conformance bench
     (`docs/harness-bench-design.md`).
2. **Publish "SASE vs. Omnigent: two meta-harness designs."** Use the §1 table, and
   include where SASE chose differently: git-native Patches, single-turn agents, and
   host-owned completion versus Omnigent's live shared sessions. One artifact serves
   both the engineering and DevRel paths.
3. **Close the eval gap.** Build a small, reproducible eval harness over SASE runs: a
   task suite, success criteria, and a regression gate. This directly answers the
   Agent Quality, Agentic Security, and CXI requirements.
4. **Lead with NYC (#1 and #2) and ask for routing.** Tell the recruiter you want the
   Omnigent, AI Gateway, Agent Framework, or Agent Quality area. Ask whether the
   Omnigent server, runner, or policy team hires engineers outside the posted
   requisitions.
5. **Get a referral by contributing first.** Many Omnigent maintainers are Databricks
   employees. A real PR review exchange or Discord discussion is the natural referral
   path. Contribute before cold-messaging Matei Zaharia or others.
6. **Calibrate level early.** Apply to Senior (#2) and Staff (#1) at the same time. A
   down-level to Senior in the AI Platform org is still the right door.

---

## 6. Caveats

- This is a 2026-10-07 snapshot. Several requisitions are long-running pipeline
  postings that match candidates to teams after interviews. Re-check each link on the
  day you apply.
- Team ownership of Omnigent is inferred from maintainers and commit authorship.
- "Good match" means domain and role-shape fit, not a prediction of an interview or
  offer. Notice period, Google vesting, relocation willingness, and comp expectations
  were not assessed, and each could change the ranking.
- No applications were made and nobody was contacted.

---

## 7. Job Postings to Consider Applying To

In priority order. Links are Databricks' official careers pages (`gh_jid` = Greenhouse
job ID).

1. **Staff Software Engineer, Agent Quality**, New York City:
   [gh_jid=8842963002](https://databricks.com/company/careers/open-positions/job?gh_jid=8842963002).
   Base $200K–$265K. **Apply.**
2. **Sr. Software Engineer – Backend (AI Platform)**, New York City:
   [gh_jid=8379331002](https://databricks.com/company/careers/open-positions/job?gh_jid=8379331002).
   Base $165.3K–$219.7K. **Apply.** Ask for Omnigent, AI Gateway, or Agent Framework
   routing.
3. **Sr. Developer Advocate, Open Source — Omnigent**, San Francisco
   ([gh_jid=8716187002](https://databricks.com/company/careers/open-positions/job?gh_jid=8716187002))
   or Seattle
   ([gh_jid=8716730002](https://databricks.com/company/careers/open-positions/job?gh_jid=8716730002)).
   **Apply only if DevRel and relocation are wanted.**
4. **Staff Security Software Engineer – Agentic Security Engineering**, remote US:
   [gh_jid=7932280002](https://databricks.com/company/careers/open-positions/job?gh_jid=7932280002).
   **Stretch.** It is the only remote option.
5. **Staff Backend Software Engineer (Databricks AI)**, San Francisco:
   [gh_jid=8367019002](https://databricks.com/company/careers/open-positions/job?gh_jid=8367019002).
   **Only if relocating.**
6. **Staff Backend Software Engineer – Unity AI Gateway**, New York:
   [gh_jid=8468436002](https://databricks.com/company/careers/open-positions/job?gh_jid=8468436002).
   **Only if Scala or Go and 8+ years are an honest claim.** Otherwise mention it in
   the recruiter conversation for #2.
7. **Sr Software Engineer – CXI**, Mountain View or San Francisco:
   [gh_jid=8617901002](https://databricks.com/company/careers/open-positions/job?gh_jid=8617901002).
   **Only if relocating.**
8. **Senior Software Engineer – Infrastructure and Tools**, San Francisco (other
   locations considered):
   [gh_jid=6318503002](https://databricks.com/company/careers/open-positions/job?gh_jid=6318503002).
   **Devtools fallback.**
9. **Staff Software Engineer, Fullstack – AI Product (NYC)**:
   [gh_jid=8509534002](https://databricks.com/company/careers/open-positions/job?gh_jid=8509534002).
   **Long shot** because of the 10+ years of web experience required.

---

## Sources

- Databricks Greenhouse board API,
  `boards-api.greenhouse.io/v1/boards/databricks/jobs?content=true` (894 postings,
  pulled 2026-10-07); per-posting links above.
- [Introducing Omnigent](https://www.databricks.com/blog/introducing-omnigent-meta-harness-combine-control-and-share-your-agents)
  (2026-06-13); [Omnigent on Databricks docs](https://docs.databricks.com/aws/en/omnigent/);
  [Databricks NYC R&D hub](https://www.databricks.com/en/blog/announcing-databricks-new-york-rd-hub)
  (2026-01-31); [Kanerika: What is Databricks Omnigent](https://kanerika.com/blogs/databricks-omnigent/);
  [AlphaSignal: Databricks open-sources Omnigent](https://alphasignal.ai/news/databricks-open-sources-omnigent-to-unify-and-govern-multiple-ai-agents).
- Local checkouts opened with `sase repo open`:
  - `omnigent-ai/omnigent` @ `ee2488a`: README, `CONTRIBUTING.md`,
    `designs/harness-plugin-interface.md`, `omnigent/harnesses/`,
    `omnigent/acp_cli_harnesses.py`.
  - `sase-org/sase` @ `0a80039`: README, `pyproject.toml`, `docs/`.
- Omnigent issue [#6083](https://github.com/omnigent-ai/omnigent/issues/6083) and the
  open help-wanted issue list, read with `gh`.
- Bryan Bugyi CV, `~/org/BryanBugyi_Batman_CV.pdf` (2026-04-21).
- Researcher reports: `databricks_omnigent_job_fit__{cdx,cld,grk,mus,gem}.md` in this
  directory.

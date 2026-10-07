# Databricks Job Fit for a sase Author, After Omnigent

- **Researcher:** cld (one of five independent researchers in the swarm)
- **Date:** 2026-10-07
- **Question:** Given Bryan's work on [sase](https://github.com/sase-org/sase) and
  Databricks' release of [Omnigent](https://github.com/omnigent-ai/omnigent), which
  open Databricks roles is Bryan a good match for?
- **Method:** I pulled a full snapshot of Databricks' live Greenhouse job board on
  2026-10-07: 894 postings, including about 250 in engineering, product, security, and
  infrastructure. I filtered it by keyword and location, then read the full text of 36
  candidate postings. I read local checkouts of both repos (`sase` and `omnigent`),
  Bryan's CV (dated 2026-04-21), and the Omnigent launch blog post saved in the Bob
  vault. I also ran web searches on Databricks' NYC hub, Genie Code, and Omnigent on
  Databricks. Salary figures are the **base** ranges printed in each posting, for the
  posting's own location or "Zone 1". They exclude equity and bonus.

---

## TL;DR

1. **Databricks has no public software-engineer opening tied to the Omnigent team.**
   The postings that name Omnigent are a **Sr. Developer Advocate, Open Source —
   Omnigent** (SF and Seattle), a **Staff Product Designer, Agentic Coding** (the
   Omnigent design lead), and DevRel posts that list Omnigent among other topics. Any
   Omnigent engineering hiring is going through the generic AI-org postings or
   referrals.
2. **The best engineering fits are in NYC**, where Databricks opened an R&D hub in
   January 2026 focused on agentic AI:
   - **Staff Software Engineer, Agent Quality (NYC):** a new founding team in AI
     Research building agent eval tooling and infrastructure. Python first, with
     devtools, CI, and testing frameworks listed as nice-to-haves.
   - **Sr. Software Engineer – Backend, AI Platform (NYC):** "hiring across multiple
     teams" in the AI Engineering org (MLflow, AI Gateway, Apps, Agent Framework).
     This is the org whose MLflow engineers built Omnigent, and it is the safest
     level match.
3. **The closest topical match is the Omnigent DevRel role**, but it changes career
   track (from SWE to developer advocacy), pays less, and is SF/Seattle only. Apply
   only if public speaking and community building appeal to you.
4. **One remote-US option:** Staff Security Software Engineer – Agentic Security
   Engineering. It is a stretch, but its agent platform needs (sandboxing,
   least-privilege tools, evals, MCP) are close to what sase does.
5. **The highest-leverage move is not an application.** Omnigent has an open,
   triaged, `help wanted` issue
   ([#6083](https://github.com/omnigent-ai/omnigent/issues/6083)) asking for a
   **Meta Muse harness**. sase already supports Muse Code, and Grok Build as well,
   which Omnigent also lacks. A merged harness PR would put your work in front of
   Omnigent's maintainers, who include Matei Zaharia (`mateiz`) and Corey Zumar
   (`dbczumar`), before a recruiter screens you.

---

## 1. What Databricks Is Building Around Omnigent

| Fact | Evidence |
| --- | --- |
| Omnigent is an Apache-2.0 "meta-harness" over Claude Code, Codex, Cursor, OpenCode, Pi, Hermes, and custom YAML agents. It covers composition, contextual and cost policies, OS and cloud sandboxes, and live session sharing across terminal, web, mobile, and desktop. | Omnigent README; Matei Zaharia, "Introducing Omnigent" (Databricks blog, 2026-06-13), saved in the Bob vault as `ref/blogs/introducing_omnigent_…` |
| Matei Zaharia, Databricks' CTO and co-founder, wrote the launch post: "We're building that layer in the open, and we'd love for you to build it with us." The roadmap mentions GEPA optimization, MemEx/RLM-style introspection, and an Omnigent Server MCP. | Launch blog, pages 3–4 |
| The repo is **about 80% Python** (3,513 `.py` files, versus about 1,200 `.ts`/`.tsx`), has 4,543 commits since 2026-06-13, has about 10.6K stars and 1.7K forks, and gets about 1,000–1,200 commits a month. | Local checkout `git log`; `gh repo view` |
| The core team is largely Databricks' **MLflow and AI-platform engineers**. Maintainers include `mateiz`, `dbczumar` (Corey Zumar), `serena-ruan`, `TomeHirata`, `daniellok-db`, `bbqiu`, `aravind-segu`, and `dennyglee`. 511 commits come from `@databricks.com` addresses, and many more come from personal emails of the same people. | `.github/MAINTAINER`, `CODEOWNERS`, `git shortlog` |
| Omnigent is now also a **managed Databricks product** (Beta) that runs through Unity AI Gateway and Databricks Sandboxes. | [Omnigent on Databricks docs](https://docs.databricks.com/aws/en/omnigent/) |
| Databricks opened a **New York R&D hub** (2026-01-31) with three focus areas: "Core research and engineering in Agentic AI and LLMs", data infrastructure, and "agentic business applications". | [Announcing Databricks New York R&D Hub](https://www.databricks.com/en/blog/announcing-databricks-new-york-rd-hub) |
| Databricks launched **Genie Code** (2026-03-11), an agent for data engineering, and acquired **Quotient AI** (agent evaluation). The NYC Agent Quality team appears to continue that eval push. | [Introducing Genie Code](https://databricks.com/blog/introducing-genie-code); [IT Brief](https://itbrief.com.au/story/databricks-debuts-genie-code-snaps-up-quotient-ai) |
| The Omnigent design posting describes the product as "Databricks' platform for building, composing, governing, and sharing AI coding agents", with design work centred on "how people supervise fleets of agents". | Staff Product Designer, Agentic Coding (gh_jid 8854693002) |

**What this means for you:** Omnigent's problem statement is sase's problem
statement. One person supervises many heterogeneous coding agents with governance,
durable state, and multi-device access. The team is Python-heavy, ships fast, and is
explicitly asking outsiders to contribute.

---

## 2. Your Profile, as an Interviewer Will See It

From the CV (2026-04-21) and the sase repo:

- **About 7.5 years as a professional software engineer** (Edgestream 2019–21,
  Bloomberg 2021–22 as SRE / Senior SWE, Google since 2022 on Ad Manager), plus
  earlier technical-support automation work at Comcast. Based in the NYC area.
- **Python is your primary language**, followed by Linux, Bash, and networking. You
  have working knowledge of Rust, Java, C/C++, and JavaScript. **You have no Scala or
  Go**, which many Databricks backend postings ask for.
- **sase**, which you own end to end:
  - 15,752 commits since 2026-02-14, almost all yours.
  - About 1.29M lines of Python across 5,646 source files, plus about 1.44M lines of
    tests.
  - 33 release tags, with v0.17.1 on PyPI.
  - A Rust core (`sase-core-rs`, via PyO3), a docs site (sase.sh), a blog, and a
    handbook PDF.
- **Open-source history:** a roughly 3,500-line rewrite of string handling in
  `psf/black` (PR #1132), `funky` (500+ stars), `cookie` (250+ stars), and the
  python-boltons libraries.
- **Process and tooling work:** the ChangeLog Driven Release methodology at
  Bloomberg, a firm-wide Python cookiecutter, rolling out pylint across a 1M+ line
  codebase, and improvements to a test framework.

### How sase maps onto Omnigent's concepts

| Omnigent concept | sase equivalent you can demo |
| --- | --- |
| Meta-harness over many agent CLIs | 7 provider CLIs (Claude Code, Codex, Antigravity, Qwen Code, OpenCode, **Muse Code**, **Grok Build**) behind one launcher, with model-alias routing |
| Supervising and sharing live sessions | ACE TUI Agents tab (live status, retry chains, per-agent diffs, chats, artifacts); agent clans, sessions, fork and resume |
| Multi-device access (web, mobile, desktop) | Rust mobile gateway (HTTP + SSE, pairing tokens, audit log), Android client, Telegram plugin |
| Contextual policies and human approval | Typed `sudo` gates with SHA-256-sealed command manifests and human review; question and plan gates |
| Sandboxing and isolation | One numbered git workspace clone per agent (but no OS or network sandbox) |
| Agent YAML / reusable agents | Macros and YAML workflow engine, project tags, and directives |
| Automations | The AXE scheduler and service host |
| Observability | Prometheus telemetry (33 pipeline metrics), ToolRuns, chat transcripts |
| Project memory and skills | SASE memory notes and webs, generated skills, beads (SDD epics and phases) |

### Honest gaps a hiring panel will probe

1. **Production scale and users.** sase has **5 GitHub stars and 1 fork**. It is a
   power tool for one person, not a product with a community. The Omnigent DevRel
   posting says success is "measured by what the community builds with your help."
2. **Distributed systems at Databricks scale.** Most backend and infrastructure
   postings want large-scale distributed systems, multi-cloud, and often Scala or Go.
3. **LLM evaluation in production.** Agent-quality, CXI, and security postings expect
   eval frameworks, LLM-as-judge, and regression gates. sase has extensive test and CI
   gating, but no visible agent-eval harness.
4. **Seniority calibration.** Staff postings ask for 6+, 7+, 8+, 10+, or 12+ years.
   With about 7.5 years, the 6+ and 7+ roles are reachable, and 10+ is a real stretch.
   Expect leveling to land between Senior (L5) and Staff (L6). (On Levels.fyi, Databricks
   L5 averages about $630–670K total comp and L6 about $1.0M, mostly equity. Treat
   that as directional only.)
5. **Lines of code are not the selling point.** About 2.7M lines in eight months,
   mostly agent-written, will raise eyebrows. Sell the **design decisions**
   (workspace-per-agent, Patches, gates, beads, mobile gateway contract), the
   operating model, and what broke and how you fixed it.

---

## 3. Board Scan Results

- **Omnigent-tagged postings** (any department, worldwide):
  - Sr. Developer Advocate, Open Source — Omnigent (SF, Seattle)
  - Manager, Developer Relations – Open Source (SF, Seattle)
  - Sr. Developer Advocate, AI & ML (SF, Seattle; Omnigent mentioned)
  - Staff Product Designer, Agentic Coding (MV/SF/Seattle)
  - One Solutions Architect posting with a passing mention
  - **No SWE posting names Omnigent, "meta-harness", or "agentic coding".**
- **NYC engineering postings (16):** Agent Quality, AI Platform backend, Unity AI
  Gateway backend, AI Research Infra, Fullstack AI Product, Sales Data & Agents, Ads
  Measurement & Orchestration, Data Collection (Tags & SDKs), Frontend, and the
  CustomerLake ML/EM postings.
- **Remote-US engineering:** one relevant posting (Agentic Security Engineering).
- Third-party job boards list a *Staff SWE – AI Platform (NYC)* and a *Senior SWE,
  Fullstack – AI Product (NYC)* that are **no longer on the Databricks board**. Treat
  those as closed.

---

## 4. Ranked Fit Analysis

Fit is scored 1–5 and combines skill match, level match, and location (you are in the
NYC area).

### 4.1 Staff Software Engineer, Agent Quality: NYC (fit 4/5, apply)

- **Team:** AI Research org. You would be a "founding member of a new team focused on
  evaluating and continuously improving Databricks' AI Agents", standing up eval
  infrastructure for Genie Agents and the "flywheel" from evals back into agent
  improvement.
- **Requirements:** 6+ years; strong Python; production or research infrastructure;
  distributed systems or data pipelines; "trustworthy, reproducible signals". Nice to
  have: **devtools, CI/CD platforms, testing frameworks, observability tooling,
  benchmarking infra**, and familiarity with how agent quality is measured.
- **Why you fit:** The nice-to-haves read like your CV: test-framework work at
  Edgestream, pylint rollout, CI-gated release discipline, and sase's master gate,
  full-CI lanes, and Prometheus telemetry. You also understand agent failure modes
  from running seven harnesses every day. NYC, and Python first.
- **Gaps:** You have no formal LLM-eval system. Build a small one before
  interviewing, such as an eval harness over sase agent runs that scores Patch
  outcomes. Data-pipeline scale is the other gap.
- **Base pay:** $200,000–$265,000. Posted 2026-09-24, so it is fresh.

### 4.2 Sr. Software Engineer – Backend (AI Platform): NYC (fit 4/5, apply)

- **Team:** The AI Engineering org, "hiring across multiple teams". It builds the
  infrastructure behind **MLflow, AI Gateway, Databricks Apps, Agent Framework, Agent
  Bricks, and Foundation Model APIs**. Omnigent's maintainers come from this org.
- **Requirements:** 5+ years backend or infrastructure; Scala, Go, **or Python**;
  distributed systems and APIs; observability. Bonus: **"Built developer platforms or
  internal tools supporting AI workflows"** and OSS contributions.
- **Why you fit:** The Senior level is a safe match. Python is accepted. The bonus
  criteria describe sase exactly. Because the posting spans several teams, you can
  ask the recruiter to route you toward the Omnigent / MLflow / AI Gateway side.
- **Gaps:** Distributed-systems depth; Scala would help.
- **Base pay:** $165,300–$219,675. First posted 2026-01-16 and still being refreshed.

### 4.3 Sr. Developer Advocate, Open Source — Omnigent: SF or Seattle (topic fit 5/5, role fit 3/5; apply only if DevRel appeals)

- The posting wants "the kind of person who has **already wired up three coding
  agents and has opinions about what breaks**". You have wired up seven. It also asks
  for subject knowledge of "agent architecture, orchestration, sandboxing, and the
  practical problems of running agents safely and affordably", strong Python and
  TypeScript, an OSS track record, and a public portfolio.
- **Requirements against your background:** "5+ years of *combined* experience as a
  developer advocate **and** in a hands-on technical role", so SWE years count.
- **Gaps:** No talks, meetups, or community growth on record, and sase has almost no
  external users. TypeScript is light. You would need to relocate to SF or Seattle.
- **Trade-offs:** This changes your career track. Base pay is lower ($149,200–$205,150
  in Zone 1). On the plus side, it is the only posting that puts you *on* the Omnigent
  project. It also reports to the Head of DevRel and feeds the roadmap. Posted
  2026-08-14.
- **To make this credible fast:** One or two merged Omnigent PRs (see §5), a
  sase-vs-Omnigent write-up, and a short demo video.

### 4.4 Staff Security Software Engineer – Agentic Security Engineering: remote US (fit 3/5, stretch)

- **Team:** A horizontal team building AI agents and a **shared agent platform** for
  Databricks security teams: "sandboxing, scoped least-privilege identity,
  observability, and a reusable agent/tool catalog"; eval frameworks; MCP tool
  integration.
- **Why you fit:** sase's gate model (sealed sudo manifests, human approval),
  workspace isolation, and multi-agent orchestration match the platform half. The
  posting is the only relevant one that is **remote anywhere in the US**.
- **Gaps:** It requires agents "that others depend on (prototypes and demos don't
  count)" and a security background. Bloomberg Compliance SRE helps a little. The
  posting has been open since 2025-04, so it is either evergreen or hard to fill.
- **Base pay:** $190,000–$261,250 in Zone 1, and $171,000–$235,200 in Zone 2.

### 4.5 Staff Software Engineer, Fullstack – AI Product: NYC (fit 2.5/5, stretch)

- **Team:** A 0-to-1 team at the NYC hub building "never-seen-before interfaces for
  GenAI agents that manage complex workflows while keeping the human in the loop
  through inspectability and transparency". Conceptually, that is what the sase TUI
  does.
- **Gaps:** It asks for 10+ years of HTML, CSS, and JS plus React. Your UI work is a
  Textual TUI and AngularDart at Google.
- **Base pay:** $190,900–$253,750.

### 4.6 Good fits that need relocation to SF, Mountain View, or Seattle

| Role | Fit | Why it fits | Main gap | Base |
| --- | --- | --- | --- | --- |
| [Staff Backend SWE (Databricks AI)](https://databricks.com/company/careers/open-positions/job?gh_jid=8367019002), SF | 3.5 | Same AI-platform org as §4.2 (MLflow, Agent Framework), at Staff level | Staff calibration; distributed systems | $166,000–$225,000 |
| [Sr SWE – Customer Experience Intelligence (CXI)](https://databricks.com/company/careers/open-positions/job?gh_jid=8617901002), MV/SF | 3.5 | Multi-tenant agent platform with "state-machine and agentic workflows" moving from human-in-the-loop to autonomous, which maps to sase's gates, workflows, and beads | Production LLM orchestration at scale | $164,200–$225,700 |
| [Senior SWE (Backend) – AI/ML Environments](https://databricks.com/company/careers/open-positions/job?gh_jid=8233899002), MV | 3 | Python; "dependency management… virtual environments", matching your uv, cookiecutter, and packaging work | Location; less agent-centric | $166,000–$220,000 |
| [Senior SWE – Infrastructure and Tools](https://databricks.com/company/careers/open-positions/job?gh_jid=6318503002), SF ("candidates in other locations will be considered") | 3 | Developer tools, testing frameworks, CI/CD, release packaging, which is your Edgestream and Bloomberg background | Bazel or Kubernetes scale; a long-running pipeline posting | $166,000–$225,000 |

### 4.7 A long shot that uses your day job

- **[Staff SWE, Ads Measurement & Orchestration](https://databricks.com/company/careers/open-positions/job?gh_jid=8760165002),
  NYC (fit 2/5).** It is the only posting where Google Ad Manager experience counts.
  It covers ad data plus "agentic workflows that parse performance data… and act on
  it". However, it wants 10+ years and advertiser-side or measurement expertise (MTA,
  MMM). Base $190,900–$253,750.

### 4.8 Reviewed and not recommended

- **Staff SWE – AI Research Infrastructure (NYC/SF):** needs cluster schedulers and GPU
  fleets.
- **Staff Backend SWE, Unity AI Gateway (NYC):** requires Scala or Go and 8+ years.
  It is still worth a mention to a recruiter, because AI Gateway carries Omnigent's
  managed traffic.
- **Senior and Staff SWE, AI Runtime:** GPU training.
- **Staff SWE – Genie One Mobile & Desktop:** React Native and mobile device
  management.
- **Staff SWE, Agentic Applications and AI-Native Web Platform:** 12+ years, web and
  marketing focus.
- **Sr. Staff Applied AI Engineer – Context Retrieval:** 10+ years in information
  retrieval.
- **Staff SWE, Sales Data & Agents (NYC):** deep CRM expertise and 10+ years.
- **Manager, DevRel – Open Source:** requires management experience.
- **Staff Product Designer, Agentic Coding:** a design role, but useful intel about
  the Omnigent team.

---

## 5. Strategy: How to Get Noticed by the Omnigent Team

1. **Ship an Omnigent harness PR before applying.**
   - Issue [#6083](https://github.com/omnigent-ai/omnigent/issues/6083), "Support for
     Meta (Facebook) Muse harness and models", is open, `help wanted`, `P2-medium`,
     and triaged. It asks for harness lifecycle, streaming, a model catalog, and
     onboarding.
   - sase already ships Muse Code integration. A **Grok Build** harness is a second
     candidate: I found no `grok` harness or issue in Omnigent.
   - Omnigent's `omnigent/harnesses/*_native` layout and its
     `designs/harness-plugin-interface.md` design doc are the starting points. The
     repo uses a DCO sign-off.
   - A merged PR gets your name in front of the same maintainers who would be
     interviewing you.
2. **Write a public "sase vs. Omnigent: two meta-harness designs" post** using the
   table in §2. It works as the portfolio piece for both the DevRel and SWE paths,
   and it shows design judgment rather than lines of code.
3. **Lead with NYC applications (§4.1, §4.2), and ask for routing.** The AI Platform
   posting explicitly spans multiple teams. Tell the recruiter you want the Omnigent,
   MLflow, AI Gateway, or Agent Quality area.
4. **Get a referral.** Many Omnigent maintainers are Databricks employees. A thoughtful
   PR review exchange with any of them, or a Discord conversation, is a natural
   referral path. Do not cold-ask for a referral before contributing.
5. **Close the eval gap.** Build a small, reproducible agent-eval harness on top of
   sase runs (task suite, success criteria, regression gate). This directly answers
   the Agent Quality, CXI, and Security postings.
6. **Calibrate level early.** Apply to Senior (§4.2) and Staff (§4.1) roles at the
   same time. If the Staff loop down-levels you, Senior on the AI Platform org is
   still the door you want.

---

## 6. Caveats

- The board snapshot is from 2026-10-07. Postings change weekly. Several reqs are
  long-running "pipeline" postings, which Databricks uses to match candidates to
  teams after interviews.
- Team ownership of Omnigent inside Databricks is **inferred** from commit authorship,
  the maintainer list, and posting text. No posting states the Omnigent engineering
  team's org.
- Pay figures are base salary only. Levels.fyi total-comp numbers are self-reported
  and directional.
- I did not check your Google level, your notice or vesting position, or whether you
  will relocate. All three change the ranking.

---

## 7. Job Postings to Consider Applying To

In priority order. All links go to Databricks' official careers pages
(`gh_jid` = Greenhouse ID).

1. **Staff Software Engineer, Agent Quality**, New York City.
   [gh_jid=8842963002](https://databricks.com/company/careers/open-positions/job?gh_jid=8842963002).
   Founding team for agent evals in AI Research; Python. **Apply.**
2. **Sr. Software Engineer – Backend (AI Platform: MLflow, AI Gateway, Apps, Agent
   Framework)**, New York City.
   [gh_jid=8379331002](https://databricks.com/company/careers/open-positions/job?gh_jid=8379331002).
   Safe level match in the org that built Omnigent. **Apply.**
3. **Sr. Developer Advocate, Open Source — Omnigent**, San Francisco
   ([gh_jid=8716187002](https://databricks.com/company/careers/open-positions/job?gh_jid=8716187002))
   or Seattle
   ([gh_jid=8716730002](https://databricks.com/company/careers/open-positions/job?gh_jid=8716730002)).
   The only Omnigent-dedicated role. **Apply if DevRel and relocation are acceptable.**
4. **Staff Security Software Engineer – Agentic Security Engineering**, remote US.
   [gh_jid=7932280002](https://databricks.com/company/careers/open-positions/job?gh_jid=7932280002).
   Agent platform with sandboxing, least privilege, and evals. **Stretch; apply.**
5. **Staff Software Engineer, Fullstack – AI Product (NYC)**, New York City.
   [gh_jid=8509534002](https://databricks.com/company/careers/open-positions/job?gh_jid=8509534002).
   Human-in-the-loop agent UIs. **Stretch (10+ years web).**
6. **Staff Backend Software Engineer (Databricks AI)**, San Francisco.
   [gh_jid=8367019002](https://databricks.com/company/careers/open-positions/job?gh_jid=8367019002).
   **Only if relocating.**
7. **Sr Software Engineer – CXI (agentic workflow platform)**, Mountain View / San
   Francisco.
   [gh_jid=8617901002](https://databricks.com/company/careers/open-positions/job?gh_jid=8617901002).
   **Only if relocating.**
8. **Senior Software Engineer – Infrastructure and Tools**, San Francisco (other
   locations considered).
   [gh_jid=6318503002](https://databricks.com/company/careers/open-positions/job?gh_jid=6318503002).
   **Devtools fallback.**
9. **Senior Software Engineer (Backend) – AI/ML Environments**, Mountain View.
   [gh_jid=8233899002](https://databricks.com/company/careers/open-positions/job?gh_jid=8233899002).
   **Only if relocating.**
10. **Staff Software Engineer, Ads Measurement & Orchestration**, New York City.
    [gh_jid=8760165002](https://databricks.com/company/careers/open-positions/job?gh_jid=8760165002).
    **Long shot** that uses your Google Ad Manager experience.

**Before applying:** open or land a PR for Omnigent issue
[#6083](https://github.com/omnigent-ai/omnigent/issues/6083) (Muse harness) or a Grok
Build harness.

---

## Sources

- Databricks Greenhouse job board API, `boards-api.greenhouse.io/v1/boards/databricks/jobs?content=true`,
  snapshot 2026-10-07 (894 postings); per-posting URLs above.
- [Introducing Omnigent: A Meta-Harness to Combine, Control and Share Your Agents](https://www.databricks.com/blog/introducing-omnigent-meta-harness-combine-control-and-share-your-agents),
  Matei Zaharia, 2026-06-13 (read from the Bob vault's saved PDF).
- Local checkouts of `omnigent-ai/omnigent` (README, NOTICE, `.github/MAINTAINER`,
  `CODEOWNERS`, CONTRIBUTING, `git log`) and `sase-org/sase` (README, pyproject, docs,
  `git log`), opened via `sase repo open`.
- Omnigent issue [#6083](https://github.com/omnigent-ai/omnigent/issues/6083) (via `gh issue view`).
- [Announcing Databricks New York R&D Hub](https://www.databricks.com/en/blog/announcing-databricks-new-york-rd-hub) (2026-01-31).
- [Introducing Genie Code](https://databricks.com/blog/introducing-genie-code);
  [IT Brief: Databricks debuts Genie Code, snaps up Quotient AI](https://itbrief.com.au/story/databricks-debuts-genie-code-snaps-up-quotient-ai).
- [Omnigent on Databricks (docs)](https://docs.databricks.com/aws/en/omnigent/).
- [Levels.fyi: Databricks Software Engineer](https://www.levels.fyi/companies/databricks/salaries/software-engineer/locations/united-states)
  (directional comp data).
- Bryan Bugyi CV (`~/org/BryanBugyi_Batman_CV.pdf`, dated 2026-04-21).

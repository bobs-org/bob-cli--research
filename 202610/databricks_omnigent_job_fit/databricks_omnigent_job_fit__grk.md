# Databricks job fit: SASE work versus Omnigent and related agent platforms

**Researcher:** grk  
**Date:** 2026-10-07  
**Question:** Given Bryan Bugyi's work on SASE (`https://github.com/sase-org/sase`) and Databricks' release of Omnigent (`https://github.com/omnigent-ai/omnigent`, often referred to as "Omniagent"), are there live Databricks openings that are a good match?

**Bottom line:** Yes. The technical overlap is real and specific: SASE and Omnigent are the same *category* of system — a layer above coding-agent CLIs that normalizes harnesses, isolates work, and adds control. Databricks is hiring into that category, but **there is no live Software Engineer posting whose title names Omnigent**. The Omnigent-named roles are DevRel (San Francisco and Seattle) and a Staff Product Designer. The strongest *engineering* matches sit one layer over: **Unity AI Gateway** (the control plane every coding-agent request passes through), **Agent Quality** in NYC (eval, regression, agent-development platform), **AI Platform backend** in NYC (Agent Framework, AI Gateway, Agent Bricks), and a **US-remote Agentic Security Engineering** staff role (sandboxing, agent platform, evals).

For someone based in New Jersey, the practical first applications are the **NYC AI Platform / Agent Quality / Unity Gateway** IC roles. The Omnigent DevRel role is the closest product-name match and a weaker career-shape match unless the goal is community, talks, and templates rather than building the meta-harness itself.

---

## 1. Candidate profile used for matching

This report matches **public, checkable facts** about Bryan Bugyi against Databricks postings as of 2026-10-07. It does not assume an unpublished resume.

| Signal | Evidence | Implication for Databricks |
| --- | --- | --- |
| Builds and operates a multi-harness agent OS | Author/maintainer of [sase-org/sase](https://github.com/sase-org/sase): Python orchestration + required Rust core, TUI, isolated numbered workspaces, provider adapters, Patches/beads/goals, scheduler, gates | Direct analog to Omnigent's runner/server/policy/sandbox stack, with extra git-native engineering semantics Databricks is still productizing |
| Daily operator of that system | This research run itself is a SASE swarm: isolated workspaces, provider adapters, durable artifacts, host-owned completion | Can talk about production failure modes of coding agents, not just a weekend wrapper |
| SWE at Google | GitHub bio (`bbugyi200`): `{day: "SWE at Google", night: "Batman of the internet"}`; LinkedIn lists Google | Databricks IC interviews will treat this as the professional bar; SASE is the *domain* proof |
| Location | GitHub: Cranford / Mount Holly, NJ; LinkedIn: Mount Holly, NJ | NYC office is the commute-shaped option; SF/Seattle/MV roles imply relocation; one strong staff role is US-remote |
| Education window | LinkedIn education 2015–2019 | ~7 years post-college in 2026 if Google started around graduation. Calibrate to **Senior (5+)** and **Staff-with-6+** postings; treat **8–12+ year Staff** as a stretch unless the resume is longer |
| Languages | SASE: Python (primary) + Rust core; CLI/TUI; Neovim; Linux | Strong for Python agent platforms. Weaker for Scala/Go-required backend Staff roles unless Google work covers them |
| Open source | SASE org (sase, sase-core, sase-github, sase-telegram, sase-nvim); historical non-trivial contribution to `psf/black` | Helps DevRel and "built developer platforms" bonuses; SASE's public star count is small next to Omnigent |

**What this profile is not:** a product-design portfolio, a conference-circuit DevRel, a GPU-training/HPC specialist, a Spark/Delta/MLflow lakehouse expert, or a people manager. Roles that require those as the *primary* job should be deprioritized even when the word "agent" appears.

---

## 2. Naming: "Omniagent" is Omnigent

The GitHub org/repo the prompt cites is [`omnigent-ai/omnigent`](https://github.com/omnigent-ai/omnigent). Databricks' June 13, 2026 launch post, docs, training, and careers pages all use **Omnigent**. Local checkout `pyproject.toml` describes it as *"Omnigent: declarative agent authoring and runtime framework"*, authors Databricks, Inc., Apache-2.0, Python ≥3.12, current tree `0.18.0.dev0` (commit `ee2488aee`, 2026-10-07).

Related Databricks surfaces that matter for job search (they are *not* the same product):

- **Omnigent** — open-source *meta-harness*: compose Claude Code / Codex / Cursor / Pi / custom YAML agents, contextual policies, OS sandbox, live session sharing, terminal + web + desktop + mobile. Managed **Omnigent on Databricks** is in Beta (workspace preview + Unity Gateway region).
- **Unity Gateway** (formerly Unity AI Gateway) — enterprise control plane for models, MCP, skills, and **coding agents**. Admins publish agent config; developers run `ug claude` / `ug codex` / `ug opencode` / etc. Smart Routing can pick model *and* harness; Omnigent is the layer that makes harness routing possible.
- **Genie / Genie Code / Genie One** — Databricks' own agents (data coworker, coding/ML exoskeleton, multi-surface apps).
- **Agent Bricks / Agent Framework** — platform for building and governing production business agents.

A SASE-shaped engineer is closest to **Omnigent + Unity Gateway CLI**, then to **agent quality / sandbox / policy** work, then to Genie-the-product.

---

## 3. Why SASE is a credible Omnigent / Gateway analog

Both systems sit *above* coding-agent CLIs instead of replacing them.

| Concern | SASE (local `sase-org/sase` checkout, README + `docs/architecture.md`) | Omnigent (local `omnigent-ai/omnigent` checkout, README + Databricks blog) |
| --- | --- | --- |
| Thesis | One developer, a team of coding agents; tracked, reviewable, repeatable work | Meta-harness: composition, control, collaboration above Claude Code / Codex / Pi / custom agents |
| Harness coverage | Claude Code, Codex, Antigravity (`agy`), Qwen Code, OpenCode, Muse Code, Grok Build | Native harness packages include `claude_native`, `codex_native`, `cursor_native`, `antigravity_native`, `opencode_native`, `qwen_native`, `pi_native`, `hermes_native`, `devin_native`, `kiro_native`, `kimi_native`, `goose_native` |
| Isolation | Numbered workspace clones; claim/admission before spawn | Runner wraps an agent in a sandboxed session; `bwrap` / seatbelt / Databricks Sandbox / Modal / Daytona / k8s / … |
| Control | Gates, agent holds, queue budgets, `max_running_agents`, host-owned completion, guarded recipes | Contextual policies (Python in OSS; CEL on Databricks), cost caps, credential-hiding egress proxy, approval cards |
| Durability | Work lives in Patches, beads, goals, artifacts, ToolRuns — outside any one transcript | Server holds sessions, messages, tool calls, artifacts, skills, auth; share live session by URL |
| Surfaces | CLI + keyboard TUI (`sase tui`); editor/mobile bridges | CLI (`omni`), web, Electron desktop, iOS/Android, REST |
| Implementation | Python host + required Rust `sase_core` | Python server/runner (~3.5k `.py` files) + TypeScript web (~1.2k `.ts/.tsx`) + mobile |
| Status | Alpha, MIT, POSIX-only | Alpha OSS / Beta managed; Apache-2.0; Databricks + Neon lineage |

The overlap that a hiring manager can hear in one sentence:

> I already built a production-shaped meta-harness: provider adapters over Claude/Codex/Antigravity/OpenCode/Qwen/Grok, isolated workspaces, admission and holds, durable review artifacts, and a TUI to supervise parallel agents. Omnigent is the same layer Databricks is productizing for composition, policy, sandboxing, and live collaboration; Unity Gateway is the enterprise control plane those sessions should ride.

Honest differences to *lead with*, not hide:

- SASE optimizes for **git-native software engineering** (Patches, stitches, single-turn agents, host finalizers). Omnigent optimizes for **shared live sessions** across devices and teammates.
- Omnigent is a well-resourced Databricks product (managed server, sandboxes, Unity Gateway, desktop/mobile). SASE is a deep independent system with a much smaller public community.
- Databricks Staff Gateway work is high-QPS distributed systems in Scala/Go. SASE's public tree is Python+Rust orchestration, not a token gateway.

That last gap is why **Agent Quality** and **AI Platform backend (Python listed)** score higher than **Unity Gateway Staff (Scala or Go, 8+ years)** as a *first* application, even though Gateway is the closest *product*.

---

## 4. Databricks hiring landscape (2026-10-07)

Source: Greenhouse board API `https://boards-api.greenhouse.io/v1/boards/databricks/jobs` (894 live jobs), plus full job JSON for the postings below.

Career-page categories (approximate): Engineering 232, Field Engineering 221, Sales 128, Forward Deployed Engineering 125, Product 32, Security 8, Research 5.

**Omnigent appears by name in three requisitions (four location rows):**

1. Sr. Developer Advocate, Open Source — Omnigent — San Francisco (`8716187002`) and Seattle (`8716730002`), same req **RDQ327R182**.
2. Staff Product Designer, Agentic Coding — Mountain View / San Francisco / Seattle (`8854693002`). The posting states: *"Omnigent is Databricks' platform for building, composing, governing, and sharing AI coding agents."*

No Engineering-category posting in the 894-job dump has "Omnigent" in the title. If the goal is to *write Omnigent code*, that work is either staffing through adjacent teams (Gateway, sandboxes, policies, session server) or not currently advertised as a named IC req. The designer posting is evidence an Omnigent product team exists.

Unity Gateway *does* have a named engineering team in a NYC Staff Backend req (below).

---

## 5. Fit, ranked

Scoring: **domain overlap with SASE/Omnigent** × **role shape (IC builder vs DevRel vs design vs GPU)** × **location relative to NJ** × **years/language bar**.

### Apply first

#### 1. Staff Software Engineer, Agent Quality — New York City

- **Posting:** [databricks.com … staff-software-engineer-agent-quality-8842963002](https://www.databricks.com/company/careers/engineering/staff-software-engineer-agent-quality-8842963002) · Greenhouse `8842963002` · P-1567
- **Pay:** $200,000–$265,000
- **Bar:** 6+ years; strong Python; distributed systems / data pipelines / infra; high bar for trustworthy reproducible signals. Nice-to-have: devtools, CI/CD, testing, observability, LLM/agent evals.
- **Why this is the best overall match:** Founding member of a new team whose job is *how Databricks measures and improves agents and the agent development platform*. SASE's entire thesis is that agent work is only useful if it is reviewable, replayable, and gated. Isolated workspaces, ToolRuns, Patches, screenshot goldens, two-speed verification, and receipt-backed completion are exactly "eval + regression + developer workflow" for coding agents. NYC is the location that fits NJ. The years bar (6+) matches a ~7-year Google SWE better than 8–12+ Staff reqs.
- **Risk:** Title is Staff and the team is AI Research / Genie Agents. Interviewers will want eval/experimentation stories, not only a personal TUI. Prepare SASE's verification story as an eval platform.

#### 2. Sr. Software Engineer — Backend (AI Platform) — New York City

- **Posting:** [open-positions/job?gh_jid=8379331002](https://databricks.com/company/careers/open-positions/job?gh_jid=8379331002) · Greenhouse `8379331002` · P-1591
- **Pay:** $165,300–$219,675
- **Bar:** 5+ years backend/infra; **Scala, Go, or Python**; distributed systems; bonus for developer platforms / internal AI tools and OSS (MLflow, PyTorch, Ray).
- **Why apply:** Same AI Platform family as the SF Staff role: *"infrastructure that powers MLflow, AI Gateway, Databricks Apps, Agent Framework, Agent Bricks, and Foundation Model APIs."* Python is an accepted language. 5+ years is the honest years match. This is the lowest-friction NYC engineering door onto the stack Omnigent actually rides (Gateway + Agent Framework).
- **Risk:** Generic "hiring across multiple teams" language — the offer team may not be Gateway. In the application and recruiter screen, ask to land on **Unity Gateway, Agent Framework, or Omnigent/sandbox** rather than vector search or model serving.

#### 3. Staff Backend Software Engineer — Unity AI Gateway — New York

- **Posting:** [open-positions/job?gh_jid=8468436002](https://databricks.com/company/careers/open-positions/job?gh_jid=8468436002) · Greenhouse `8468436002` · P-1592
- **Pay:** $190,000–$261,250
- **Bar:** **8+ years**; **Scala or Go** (Python not listed); high-throughput APIs; bonus for developer platforms supporting AI workflows.
- **Why it is the closest product:** *"You'll build the control plane that every AI request at Databricks passes through: partner and self-hosted models, agents, coding assistants, and MCP servers. It enforces budgets, routes each request to the right model, and applies guardrails inline."* That is SASE's control plane (holds, budgets, provider routing, gates) at company-wide token scale, and it is the plane Omnigent Smart Routing uses.
- **Why it is second/third, not first:** Language bar is Scala/Go; years bar is 8+. Apply if Google work includes high-QPS backend in those languages, or if you can honestly claim equivalent systems depth. Do not apply as a Python-only TUI author and hope they ignore the req.

#### 4. Staff Security Software Engineer — Agentic Security Engineering — United States (remote)

- **Posting:** [staff-security-software-engineer---agentic-security-engineering--7932280002](https://www.databricks.com/company/careers/security/staff-security-software-engineer---agentic-security-engineering--7932280002) · Greenhouse `7932280002` · RDQ226R605
- **Pay:** Zone 1 $190,000–$261,250 (down to Zone 4 $152,000–$209,000)
- **Bar:** 7+ years software *or* security; expert Python; production AI agents others depend on; sandboxing, least-privilege identity, evals, MCP-style tools. Explicitly *"prototypes and demos don't count."*
- **Why apply:** Only strong **US-remote** engineering match. SASE already ships sandbox-adjacent isolation, credential-aware workflows, holds, and gates. The team's platform (sandbox + tool catalog + observability + eval regression) is the security-org version of a meta-harness.
- **Risk:** The *customers* are Detection & Response / Red Team / GRC, not coding-agent users. The posting wants production agents *other teams depend on*. SASE-as-personal-OS needs to be framed as a production control plane you run daily, plus whatever Google production-agent/security work exists. Skip if the interest is strictly Omnigent-the-product.

### Apply if the career shape is DevRel or Bay Area relocation

#### 5. Sr. Developer Advocate, Open Source — Omnigent — San Francisco or Seattle

- **Postings:** [SF 8716187002](https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716187002) · [Seattle 8716730002](https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716730002) · RDQ327R182
- **Pay:** Zone 1 $149,200–$205,150
- **Bar:** 5+ years combined DevRel + hands-on SWE/ML/SA; Python **and TypeScript**; CLI fluency; OSS issues/PRs/reviews/releases; subject-matter knowledge of agent architecture, orchestration, sandboxing, cost; public speaking; growing a *contributor* community.
- **Why it is the closest named Omnigent job:** The posting is a near-paraphrase of SASE's README: *"the kind of person who has already wired up three coding agents and has opinions about what breaks."* Templates, harness composition, contextual policies, sandboxing, and cost controls are the curriculum. Influencing the Omnigent roadmap from the community side is a real path onto the product team.
- **Why it may be a poor fit:** The job is talks, courseware, Discord/GitHub triage, and meetups, reporting to Head of Developer Relations. SASE's public footprint is small; TypeScript is not SASE's primary language; NJ → SF/Seattle is relocation. Apply only if you *want* that job, not as a back door into SWE.

Bay Area engineering cousins of #2/#3 if relocation is on the table:

- **Staff Backend Software Engineer (Databricks AI)** — San Francisco · `8367019002` · $166,000–$225,000 · 5+ years, Scala/Go/**Python**, same AI Gateway / Agent Framework / Agent Bricks list as the NYC Senior role.
- **Senior Software Engineer — Infrastructure and Tools** — San Francisco · `6318503002` · $166,000–$225,000 · 5+ years Java/Scala/Go/C++/Python; Bazel, CI/CD, k8s, API gateways. *"Candidates in other locations will be considered."* Weaker Omnigent overlap (generic infra), useful only as a location-flexible Senior IC.

### Consider, with clear caveats

| Role | ID | Location | Why it is only "consider" |
| --- | --- | --- | --- |
| AI Engineer – Forward Deployed Engineering (AI FDE), all levels | `8546367002` | United States, remote; travel every 4–8 weeks | Customer-facing GenAI (RAG, LangChain, DSPy, Text2SQL). SASE is a platform, not a professional-services RAG toolkit. Apply if you want customer work and Databricks-product fluency, not to build Omnigent. Pay $152,900–$210,155. |
| Staff Software Engineer, Fullstack — AI Product | `8509534002` | NYC | Human-in-the-loop agent UIs, 0→1. **10+ years HTML/CSS/JS** plus 10+ years server-side. Domain is adjacent; skill bar is frontend-staff, not meta-harness. |
| Staff Software Engineer – Genie One Mobile & Desktop | `8692516002` | MV / SF | Multi-surface agent sessions, like Omnigent's desktop/mobile. Frontend/mobile/auth, not harness adapters. |
| Applied AI Engineer (Genie Code) | `8091041002` | Belgrade, Serbia | 2–8 years, agentic ML exoskeleton, reports to a Principal. Strong *product* overlap with "agents that write code," wrong continent. |
| Sr. Engineering Manager — Agentic Service Platform | `8510921002` | Mountain View | Name sounds like Omnigent; it is **RPC/service-mesh platform** for every Databricks microservice, plus 4+ years management. Skip unless the goal is EM. |

### Skip (name collision or wrong craft)

- **Senior / Staff Software Engineer, AI Runtime** (`8582276002`, `8582271002`, MV/SF) — "Runtime" here is **GPU training (AIR / Mosaic)**, not an agent harness. PyTorch/FSDP/Megatron, NVLink, checkpointing.
- **Sr Software Engineer, Agentic Applications** and Staff/Sr Staff Fullstack Agentic Applications (Mountain View) — internal business apps / marketing-agent SDLC / generic React. The "Agentic Applications" Senior posting's examples are SQL dashboards and cluster UX, not coding-agent orchestration.
- **Staff Product Designer, Agentic Coding** (`8854693002`) — Omnigent's actual product team, but it is design (desktop/mobile session UX). Apply only with a designer portfolio.
- **Staff Software Engineer, Sales Data & Agents** (NYC) — Salesforce/CRM data model, 10+ years, sales agents.
- Lakehouse / Spark / Lakeflow / model-serving Staff roles unless the resume already is that person.

---

## 6. Recommended application list (actionable)

Apply in this order unless relocation or DevRel is a hard yes:

1. **Staff Software Engineer, Agent Quality** — New York City  
   https://www.databricks.com/company/careers/engineering/staff-software-engineer-agent-quality-8842963002  
   Greenhouse job `8842963002`

2. **Sr. Software Engineer — Backend (AI Platform)** — New York City  
   https://databricks.com/company/careers/open-positions/job?gh_jid=8379331002  
   Greenhouse job `8379331002`

3. **Staff Backend Software Engineer (Unity AI Gateway)** — New York  
   https://databricks.com/company/careers/open-positions/job?gh_jid=8468436002  
   Greenhouse job `8468436002`  
   *(Apply in parallel with #1/#2 if Scala/Go and ~8 years are honest.)*

4. **Staff Security Software Engineer — Agentic Security Engineering** — United States, remote  
   https://www.databricks.com/company/careers/security/staff-security-software-engineer---agentic-security-engineering--7932280002  
   Greenhouse job `7932280002`

5. **Sr. Developer Advocate, Open Source — Omnigent** — San Francisco *or* Seattle (same req)  
   https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716187002  
   https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716730002  
   Greenhouse jobs `8716187002` / `8716730002`  
   *(Only if DevRel + relocation are acceptable.)*

6. **Staff Backend Software Engineer (Databricks AI)** — San Francisco  
   https://databricks.com/company/careers/open-positions/job?gh_jid=8367019002  
   Greenhouse job `8367019002`  
   *(Only if Bay Area relocation is on the table.)*

**Do not wait for a "Software Engineer, Omnigent" req that is not in the current 894-job board.** Use #1–#3 to get onto the agent platform org, name Omnigent and Unity Gateway CLI in the letter, and ask the recruiter whether the Omnigent server/runner/policy team is hiring ICs off-board.

---

## 7. How to position SASE in the packet

Lead with a **category claim**, then one **artifact**, then one **Google production** story:

1. Category: meta-harness / agent control plane (adapters, isolation, policy, supervision).
2. Artifact: a concrete SASE mechanism — e.g. typed launch admission, workspace claim, provider adapter contract, gates/holds, or verification receipts — mapped onto Omnigent policies + Unity Gateway budgets/routing.
3. Google: whatever distributed-systems, developer-platform, or reliability work will pass a Databricks Staff/Senior bar.

Avoid:

- Claiming Databricks/Spark/Delta expertise SASE does not demonstrate.
- Treating SASE star count as traction; treat it as a working system you will demo.
- Applying to "AI Runtime" because the word runtime sounds like a harness.

A recruiter one-liner:

> Google SWE in New Jersey; I designed and run SASE, an open-source meta-harness that fans a prompt out to Claude Code, Codex, Antigravity, OpenCode, and others in isolated workspaces with durable review. I want to do that job at Databricks on Omnigent, Unity Gateway, and agent quality.

---

## 8. Caveats

- Job boards churn. Counts and reqs are a **2026-10-07** snapshot of the Databricks Greenhouse board (894 jobs) plus the cited career-site HTML.
- Years-of-experience is inferred from public education dates and a Google bio, not a resume. Recalibrate Staff vs Senior if the resume is materially longer or shorter.
- "Good match" here means *domain and role-shape fit*, not a prediction that Databricks will interview or offer.
- This swarm researcher did not read peer reports (`__cdx`, `__cld`, `__mus`, `__gem`).

---

## Sources

**Databricks / Omnigent product**

- [Introducing Omnigent (Databricks blog, 2026-06-13)](https://www.databricks.com/blog/introducing-omnigent-meta-harness-combine-control-and-share-your-agents)
- [Contextual policies in Omnigent](https://www.databricks.com/blog/contextual-policies-omnigent-using-session-state-better-govern-ai-agents)
- [Omnigent on Databricks (docs, updated 2026-09-28)](https://docs.databricks.com/aws/en/omnigent/)
- [Unity Gateway product](https://www.databricks.com/product/artificial-intelligence/unity-gateway)
- [Deploy coding agents with the Unity Gateway CLI (2026-09-24)](https://www.databricks.com/blog/deploy-and-manage-coding-agents-scale-unity-gateway-cli)
- [Smart Routing in Unity Gateway (harness + model, Omnigent)](https://www.databricks.com/blog/smart-routing-unity-ai-gateway-match-frontier-quality-30-lower-cost-task)
- Local clone `gh:omnigent-ai/omnigent` (opened via `sase repo open`), README, `pyproject.toml`, `omnigent/harnesses/`
- Local clone `gh:sase-org/sase`, README, `docs/architecture.md`

**Jobs**

- Greenhouse list API: `https://boards-api.greenhouse.io/v1/boards/databricks/jobs` (894 jobs, 2026-10-07)
- Per-job JSON: `https://boards-api.greenhouse.io/v1/boards/databricks/jobs/{id}`
- Canonical HTML: `https://www.databricks.com/company/careers/...` URLs listed above

**Candidate**

- [github.com/sase-org](https://github.com/sase-org) (email bryanbugyi34@gmail.com on the org)
- [github.com/bbugyi200](https://github.com/bbugyi200)
- [linkedin.com/in/bryan-bugyi](https://www.linkedin.com/in/bryan-bugyi)
- [sase.sh](https://sase.sh/)

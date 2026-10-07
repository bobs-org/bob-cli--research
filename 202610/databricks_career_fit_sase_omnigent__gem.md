# Databricks Career Fit Analysis: SASE and Omnigent Alignment

**Researcher:** `research.0k.gem`  
**Date:** October 2026  
**Target Organization:** Databricks (Databricks AI / Mosaic AI / Open Source)  
**Target Candidate Profile:** Creator and core developer of [SASE (Structured Agentic Software Engineering)](https://github.com/sase-org/sase)  
**Context:** Release of [Omnigent](https://github.com/omnigent-ai/omnigent) by Databricks  

---

## 1. Executive Summary & Verdict

### The Verdict: Exceptional, High-Signal Match
You are an exceptionally strong fit for Databricks. In fact, your background creating and maintaining **SASE** places you in the top percentile of software engineers and developer advocates globally for Databricks’ emerging agentic tooling strategy.

### Strategic Backdrop
On **June 13, 2026**, Databricks CTO **Matei Zaharia**, alongside Staff Software Engineer & MLflow maintainer **Corey Zumar** and Product Lead **Kasey Uhlenhuth**, publicly announced **Omnigent**—an open-source "meta-harness" for AI agents. 

Omnigent represents Databricks’ major strategic move into the developer tooling and agent orchestration layer. Rather than building a closed, proprietary LLM wrapper, Databricks has committed to an open, extensible layer that sits above disparate coding harnesses (Claude Code, OpenAI Codex, Cursor, OpenCode, Hermes, Pi) and provides unified orchestration, sandboxed execution, real-time collaboration, and stateful policy enforcement.

### Why You Stand Out
1. **Architectural Convergence:** SASE and Omnigent are tackling the exact same paradigm shift. Both frameworks were conceived from the fundamental realization that single-agent, single-model CLIs are insufficient for serious engineering workflows. Both systems reject monolithic agent lock-in and instead build multi-agent coordination, isolation, and governance.
2. **First-Hand Domain Expertise:** You have already designed, implemented, and battle-tested the hardest problems in agentic systems: multi-model routing, isolated numbered workspaces, git worktree lifecycle, terminal/TUI supervision, human-in-the-loop approval gates, durable state/bead tracking, and artifact persistence.
3. **Open-Source Systems Pedigree:** Databricks has built its multi-billion-dollar enterprise value on open-source foundations (Apache Spark, MLflow, Delta Lake, and now Omnigent). Your track record of building complex, tested, documented open-source systems software in Python aligns squarely with Databricks’ engineering culture.

---

## 2. Architectural Comparison: SASE vs. Omnigent

Understanding where SASE and Omnigent intersect highlights the exact technical assets you bring to Databricks:

| Dimension | SASE (`sase-org/sase`) | Omnigent (`omnigent-ai/omnigent` / Databricks) | Strategic Alignment |
| :--- | :--- | :--- | :--- |
| **Core Concept** | Multi-agent coordination layer for software engineering teams | Open-source meta-harness unifying AI agent harnesses | **Identical thesis:** A meta-layer sitting above individual agent runtimes. |
| **Agent Runtimes Supported** | Claude Code, Codex, Antigravity CLI, Qwen Code, OpenCode, Muse Code, Grok Build | Claude Code, Codex, Cursor, OpenCode, Hermes, Pi, custom YAML agents | **High overlap:** Both abstract external agent CLIs/SDKs with unified invocation semantics. |
| **Execution Isolation** | Ephemeral numbered workspace clones (`bob-cli_<N>`), git worktrees, strict path confinement | Cloud sandboxes (Databricks, Modal, Daytona, E2B, Boxlite, Kubernetes) & managed hosts | **Direct parallel:** Managing isolated environments and preventing filesystem collisions. |
| **Governance & Control** | Approval gates (plan gates, question gates, patch review lifecycles, stitch audit) | Contextual policies (spend caps, human approval before risky actions, tool access rules) | **Direct parallel:** Moving beyond blind prompt guardrails to stateful, interactive human-in-the-loop safety. |
| **Observability & UX** | Keyboard-driven terminal TUI (supervisor), live agent tabs, diff views, transcripts | Native desktop app (macOS), terminal CLI, browser UI, live session sharing | **Complementary:** Deep CLI/TUI ergonomics and developer experience. |
| **State & Memory** | Durable goals, task beads, audited reference memory, artifact snapshots | Session history, session forking, connection bridges, databricks AI Gateway telemetry | **Direct parallel:** Managing durable agent state and execution receipts. |
| **Language & Ecosystem** | Modern Python (3.12+), uv, Justfile, rich TUI/CLI architecture | Modern Python (3.12+), TypeScript/React web frontend, Databricks SDK | **Exact stack alignment:** Python 3.12+, packaging with uv, systems-level process supervision. |

### Technical Synergy
In building SASE, you have navigated the intricate failure modes of coding agents: process hanging, terminal escape code mangling, asynchronous stream multiplexing, git rebase/merge conflicts across parallel checkouts, and non-deterministic agent tool loops. 

The Omnigent engineering team at Databricks is actively confronting these exact problems in their `omnigent/harnesses/`, `omnigent/runner/`, `omnigent/policies/`, and `omnigent/sandbox/` modules. Your hands-on experience means zero onboarding ramp on the core architectural problems of agent meta-harnessing.

---

## 3. The Databricks AI Landscape & Key Stakeholders

To navigate career opportunities effectively, it is critical to understand how the teams and key individuals within Databricks are structured:

1. **The Omnigent Core Team:**
   - **Matei Zaharia:** Co-founder & Chief Technologist at Databricks, Associate Professor at UC Berkeley. Co-author of the Omnigent launch.
   - **Corey Zumar (`dbczumar`):** Staff Software Engineer at Databricks. Lead maintainer of MLflow and core developer of Omnigent.
   - **Kasey Uhlenhuth:** Product Management Lead at Databricks driving agentic products.
   - **Dhruv Gupta, Daniel Lok, Zeyi Fan:** Active Databricks engineering contributors to `omnigent-ai/omnigent`.
2. **Mosaic AI / Databricks AI Platform:**
   - The organizational unit responsible for Databricks’ generative AI offerings: **Agent Framework**, **Agent Bricks**, **Unity AI Gateway**, **Model Serving**, and **Foundation Model APIs**.
   - Focuses on providing enterprise-grade infrastructure to build, deploy, evaluate, and govern production agents.
3. **CXI (Customer Experience Intelligence) / Enterprise Agentic Framework:**
   - Focuses on vertical agent orchestration across enterprise domains (Support, IT, Security, Legal), building stateful human-in-the-loop workflows.
4. **Developer Experience & Open Source:**
   - Databricks maintains dedicated teams for Developer Advocacy, Developer Tools, SDKs, and CLIs to nurture open-source ecosystems.

---

## 4. Analysis of Open Job Postings at Databricks

Based on current postings across Databricks’ careers portal, here are the top job openings that represent the strongest match for your skillset and experience with SASE and Omnigent.

---

### Job 1: Sr. Developer Advocate, Open Source — Omnigent
* **Location:** San Francisco, CA | Seattle, WA (Hybrid / Remote options)
* **Organization:** Open Source / Developer Relations
* **Application Link:** [Databricks Careers Portal](https://www.databricks.com/company/careers) *(Search for "Sr. Developer Advocate, Open Source — Omnigent")*

#### Role Overview
Databricks is hiring a dedicated Senior Developer Advocate to foster the developer community and drive adoption for Omnigent, their newly released open-source meta-harness for AI agents. This role acts as a high-visibility bridge between Databricks’ internal engineering team (including Corey Zumar and Matei Zaharia) and the external open-source AI community.

#### Key Responsibilities
* Create high-impact templates, demos, multi-agent recipes, and reference implementations showcasing Omnigent’s meta-harness and sandbox capabilities.
* Deliver talks, author in-depth technical blogs, conduct live demos, and host meetups for developers building with coding agents.
* Actively engage on the Omnigent GitHub repository (`omnigent-ai/omnigent`) and Discord community, triaging issues, reviewing PRs, and channeling community feedback back into core engineering.
* Partner with the Head of Developer Relations and engineering leads to execute an open-source growth strategy during the critical early-stage adoption phase.

#### Qualifications
* 5+ years of combined experience in developer advocacy and hands-on technical engineering (Software Engineer, ML Engineer, or Solutions Architect).
* Strong programming proficiency in **Python** and **TypeScript**.
* Proven, hands-on experience with agentic developer tooling, coding agents (Claude Code, Codex, Cursor), and multi-agent systems.
* Track record of building, contributing to, and maintaining open-source projects.

#### Match Assessment for Bryan: 10 / 10
* **Why You Fit:** You have literally built a complete open-source agent orchestration ecosystem (SASE) in Python from the ground up. You know every nuance of how developers interact with coding agents, what pain points they experience, and how to design developer-centric agent workflows. You wouldn’t just advocate for Omnigent; you have already lived its technical thesis.
* **Potential Considerations:** If you strongly prefer 100% heads-down systems coding over public advocacy/community engagement, evaluate whether you prefer this role or a core backend role. However, Developer Advocates at Databricks for early-stage OSS projects write significant production code, build canonical extensions, and heavily influence product roadmaps.

---

### Job 2: Staff Backend Software Engineer (Databricks AI)
* **Location:** San Francisco, CA | Mountain View, CA
* **Organization:** AI Platform / Mosaic AI
* **Application Link:** [Databricks Careers Portal](https://www.databricks.com/company/careers) *(Search for "Staff Backend Software Engineer (Databricks AI)")*

#### Role Overview
This role sits at the core of the AI Platform team responsible for building the foundational infrastructure that powers Databricks’ generative AI offerings: the **Agent Framework**, **Agent Bricks**, **MLflow**, **AI Gateway**, **Databricks Apps**, and **Foundation Model APIs**. The team builds the substrate for AI agents, model routing, serving, and vector search.

#### Key Responsibilities
* Architect and scale backend systems that orchestrate enterprise AI agents and distributed AI workloads.
* Build smart routing layers for foundation models that dynamically optimize across quality, cost, latency, and budget constraints.
* Improve the reliability, latency, fault tolerance, and observability of multi-agent and LLM execution pipelines.
* Collaborate directly with MLflow maintainers and AI platform leadership to shape developer interfaces and APIs for agents.

#### Qualifications
* 5+ to 8+ years of experience in backend, systems, or infrastructure engineering.
* Strong proficiency in **Python**, **Go**, or **Scala**.
* Deep expertise in distributed systems, scalable APIs, and service observability.
* Demonstrated product ownership mindset and ability to design complex technical platforms in ambiguous spaces.

#### Match Assessment for Bryan: 10 / 10
* **Why You Fit:** SASE’s architecture is an exact micro-version of this mission. You have built custom LLM provider abstractions, dynamic model routing (`llm_provider`), execution state machines, tool-run recording, and structured observability. You understand how to build resilient systems that supervise flaky subprocesses and external model APIs.
* **Potential Considerations:** Databricks backend services operate at enterprise cloud scale (thousands of tenant workspaces), so highlighting experience with distributed backend infrastructure, high-throughput APIs, and cloud services will strengthen your profile.

---

### Job 3: Staff Software Engineer – Customer Experience Intelligence (CXI) / Enterprise Agentic Framework
* **Location:** Mountain View, CA | San Francisco, CA
* **Organization:** CXI Engineering
* **Application Link:** [Databricks Careers Portal](https://www.databricks.com/company/careers) *(Search for "Staff Software Engineer, Customer Experience Intelligence")*

#### Role Overview
The CXI team is architecting Databricks' AI-native vertical workflow platform. They are building an **Enterprise Agentic Framework** to orchestrate AI agents, humans, and enterprise tools across business domains (Customer Support, IT, Security, Legal).

#### Key Responsibilities
* Architect the "Agentic Ecosystem" and core backend infrastructure for the Enterprise Agentic Framework.
* Design state-machine and multi-agent workflows that safely evolve from human-in-the-loop oversight to autonomous execution.
* Ensure enterprise-grade reliability, safety guardrails, and end-to-end observability across multi-step agent actions.

#### Qualifications
* 8+ years of software engineering experience with complex backend architectures.
* Proficiency in Python and modern cloud infrastructure.
* Experience designing state machines, agent orchestration frameworks, or complex workflow engines.

#### Match Assessment for Bryan: 9.5 / 10
* **Why You Fit:** SASE’s entire design philosophy is built on stateful, human-in-the-loop governance (the TUI review walk, plan gates, question gates, patch lifecycle, and beads). You have solved the exact challenge of moving agents safely between autonomous work and human checkpoints.

---

### Job 4: Senior / Staff Software Engineer – Agentic Applications
* **Location:** Mountain View, CA
* **Organization:** Agentic Applications / GenAI Engineering
* **Application Link:** [Databricks Careers Portal](https://www.databricks.com/company/careers) *(Search for "Staff Software Engineer, Agentic Applications")*

#### Role Overview
This team builds production-ready applications powered by AI agents that automate internal engineering, marketing, and operational workflows. They implement guardrails, human-in-the-loop mechanisms, and robust evaluation harnesses to make agentic execution reliable.

#### Key Responsibilities
* Design and implement LLM-powered agents that automate complex multi-step workflows.
* Build evaluation harnesses, regression testing suites, and observability pipelines for autonomous agents.
* Embed human-in-the-loop approvals and security guardrails into automated agent loops.

#### Qualifications
* 5+ years (Senior) or 8+ years (Staff) of software engineering experience.
* Strong Python programming skills and extensive experience with modern LLM frameworks.

#### Match Assessment for Bryan: 9 / 10
* **Why You Fit:** In SASE, you created automated workflows (e.g. AXE scheduler, macros, automated git commit and pull request pipelines) that take prompts and deliver finished, reviewable pull requests. This role translates your experience directly to end-user applications.

---

### Job 5: Senior Software Engineer (Backend) – AI/ML Environments
* **Location:** Mountain View, CA
* **Organization:** AI Platform / AI Runtime
* **Application Link:** [Databricks Careers Portal](https://www.databricks.com/company/careers) *(Search for "Senior Software Engineer (Backend) - AI/ML Environments")*

#### Role Overview
The AI/ML Environments team builds the infrastructure that allows developers, researchers, and agents to configure, run, and isolate their execution environments. They focus on dependency isolation, remote containerization, and environment sandboxing.

#### Key Responsibilities
* Build scalable backend infrastructure for isolated execution environments.
* Manage dependency resolution, environment caching, and containerized runtime sandboxes.
* Optimize developer ergonomics and speed for launching isolated interactive and batch sessions.

#### Qualifications
* 5+ years of backend or infrastructure engineering experience.
* Proficiency in Python and systems-level programming.
* Experience with containers, sandboxing, or developer environments.

#### Match Assessment for Bryan: 9 / 10
* **Why You Fit:** A core capability of SASE is its `workspace_provider`—dynamically spinning up numbered, clean workspace clones, handling worktree lifecycles, and keeping parallel agent environments isolated from each other and the host tree.

---

## 5. Strategic Application & Outreach Playbook

Because of your specific profile, you should **not** rely solely on an anonymous submission via the standard applicant portal. Instead, follow this high-leverage outreach playbook:

### Step 1: Establish High-Signal Presence on Omnigent
* **Explore the Codebase:** Inspect `omnigent-ai/omnigent` (which is already opened locally in your workspace). Notice how Omnigent structures harnesses in `omnigent/harnesses/` and policies in `omnigent/policies/`.
* **Submit an Issue or Pull Request:** 
  - Look for an integration or harness adapter where SASE has deep experience (e.g., handling terminal dialog dismissal, process signal handling, or workspace sandboxing).
  - Open a thoughtful GitHub Issue or PR showing deep familiarity with agent harness ergonomics.
* **Join the Community:** Join the Omnigent Discord (`discord.gg/omnigent`) and participate in technical discussions regarding multi-agent coordination.

### Step 2: Direct Engineering Outreach
Reach out directly to key engineering leaders on the Omnigent and AI Platform teams:
1. **Corey Zumar (`dbczumar`):** Staff Software Engineer at Databricks, lead on MLflow and Omnigent. 
   - *Angle:* Congratulate him on the Omnigent launch. Highlight that you've been working on the exact same meta-harness problem with SASE (`sase-org/sase`). Point out specific shared design choices (multi-harness abstraction, workspace isolation, policy enforcement) and express interest in discussing open roles on the team.
2. **Kasey Uhlenhuth:** Product Lead for Databricks Agentic Tools / Omnigent.
   - *Angle:* Express your passion for the meta-harness vision and discuss the Senior Developer Advocate (Omnigent) or Staff Engineer positions.
3. **Matei Zaharia:** Co-founder & CTO.
   - *Angle:* A concise note referencing SASE, praising Omnigent's approach to open-source governance and meta-harnessing, and indicating your desire to contribute to Databricks' agentic platform.

### Step 3: Resume & Pitch Framing
When submitting your application or sharing your background:
* **Position SASE as a Living Proof-of-Concept:** Emphasize that SASE is not a theoretical prototype, but a production-grade multi-agent orchestrator managing parallel coding agents across multiple foundation models.
* **Highlight Dual Strength:** Emphasize that you possess both the **systems engineering rigor** (Python systems programming, subprocess handling, git mechanics, TUI/CLI) and the **product vision** (understanding how human developers actually want to supervise and interact with AI agents).

---

## 6. Summary of Recommended Job Postings

| Priority | Job Title | Team / Domain | Primary Location | Strategic Fit |
| :---: | :--- | :--- | :--- | :---: |
| **#1** | **Sr. Developer Advocate, Open Source — Omnigent** | Omnigent / Open Source Developer Relations | San Francisco, CA / Seattle, WA (Hybrid/Remote) | **10 / 10** |
| **#2** | **Staff Backend Software Engineer (Databricks AI)** | AI Platform / Mosaic AI (Agent Framework, MLflow) | San Francisco, CA | **10 / 10** |
| **#3** | **Staff Software Engineer – Customer Experience Intelligence (CXI)** | Enterprise Agentic Framework / Vertical Workflows | Mountain View, CA / San Francisco, CA | **9.5 / 10** |
| **#4** | **Senior / Staff Software Engineer – Agentic Applications** | GenAI / Agentic Applications | Mountain View, CA | **9.0 / 10** |
| **#5** | **Senior Software Engineer (Backend) – AI/ML Environments** | AI Runtime / Environment Sandboxing | Mountain View, CA | **9.0 / 10** |

---

*Report filed independently by researcher `gem`.*

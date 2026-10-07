# Databricks fit: SASE background × Omnigent — job-target research

Researcher: mus (`__mus`). Independent swarm report. Peer reports (`__cdx`, `__cld`, `__grk`, `__gem`) intentionally not consulted.

Question: given deep work on SASE (see https://github.com/sase-org/sase) and Databricks' Omnigent release (see https://github.com/omnigent-ai/omnigent), are there Databricks openings worth applying to?

Short answer: yes — one exceptionally on-point role (Sr. Developer Advocate, Open Source — Omnigent), plus two to three engineering families worth shortlisting. Details and caveats below.

## 1. Terminology correction: "Omniagent" vs "Omnigent"

The product is **Omnigent**, not "Omniagent." Multiple independent sources agree:

- Databricks open-sourced **Omnigent** under Apache 2.0 around June 13, 2026, just before Data + AI Summit 2026; a managed beta is available on the Databricks platform.
- Descriptions converge: an open-source **meta-harness** sitting one level above Claude Code, Codex, Cursor, OpenCode, Pi, etc., providing harness composition, contextual policies, sandboxing, cost controls, and live-session collaboration from terminal, browser, phone, or desktop app.
- One review note found during research explicitly warns: briefs sometimes say "omniagent," but the actual product/repo is **Omnigent** (`omnigent-ai/omnigent`).

Implication for applications: use "Omnigent" everywhere; mentioning the naming confusion in a cover letter ("sometimes misrendered as Omniagent") is a cheap credibility signal.

## 2. What SASE is (verified from checkout)

Opened `sase` via `sase repo open sase` and read the tree at `sase/repos/external/projects/sase`:

- Tagline: "One developer. A team of coding agents. Tracked, reviewable, repeatable work." Structured Agentic Software Engineering.
- Shape: Python orchestration layer (requires Python 3.12+, `pyproject.toml` v0.17.1) plus a required Rust core (`sase-core-rs`) for deterministic data operations. TUI (`sase's TUI`, Textual-based), per-machine service host, Axe background orchestrator, Macros (reusable prompt templates/directives), YAML multi-step Workflows, Patches (PR-sized review records), Goals, ToolRuns, scheduler service, Beads (git-portable issue/dependency tracking), Memory (always-loaded + on-demand notes with audited reads), pluggable providers (LLM, VCS, workspace, config, macro).
- Launch flow (`docs/architecture.md`): prompt/directive parsing, project-tag expansion, swarm/repeat slot resolution, atomic numbered-workspace claims, detached runner with `%wait`/admission/queue budgets, macro/workflow execution, streaming output + chat history, agent artifacts (prompts, diffs, PDFs, images, plans), notifications, VCS/workspace handoff.
- Keywords from `pyproject.toml`: agentic software engineering, automation, coding agents, developer tools, workflow orchestration.

This is directly analogous to Omnigent's problem space (multi-agent supervision, harness abstraction, policy/governance, sandboxing, session sharing), except SASE is git/workspace-centric and TUI-driven while Omnigent emphasizes device-following sessions (terminal/browser/phone/desktop), YAML-defined custom agents, and server-managed cloud sandboxes.

## 3. What Omnigent is (verified from checkout)

Opened `gh:omnigent-ai/omnigent` via `sase repo open` and read the tree at `sase/repos/external/gh/omnigent-ai/omnigent`:

- README: "The open-source meta-harness for all your AI agents" — common orchestration over Claude Code, Codex, Cursor, OpenCode, Hermes, Pi, and self-authored agents; swap/combine harnesses without rewriting; enforce policies and sandboxing; collaborate in real time from any device.
- Install: `curl ... install_oss.sh`, or `uv tool install omnigent`, or Homebrew; extras include model providers (`databricks`, `bedrock`, `vertex`), sandbox providers (`modal`, `daytona`, `blaxel`, `boxlite`, `microsandbox`, `cwsandbox`, `e2b`, `openshell`, `kubernetes`), SDK harnesses, storage/memory (`s3`, `hindsight`).
- Notably, Omnigent lists **Databricks sandboxes** as a managed-host option and ships `omnigent/databricks_ai_gateway.py` — a canonical predicate recognizing Databricks Unity Gateway hosts (`<workspace>.ai-gateway.cloud.databricks.com` plus Azure/GCP control-plane suffixes, requiring the `ai-gateway` DNS label, matched on whole DNS labels to block lookalikes). This is evidence of genuine Databricks-platform integration work inside the OSS repo, not just branding.
- Stack (`pyproject.toml`, v0.18.0.dev0, `omnigent-ai/omnigent`): Python ≥3.12, Click CLI, FastAPI/Starlette + Uvicorn server, MCP, OpenAI SDK, Rich, prompt_toolkit, websockets/httpx, CEL (`cel-python`) for inline policy evaluation, OS keychain secrets, TOML round-tripping, Alembic/anyio, plus version-locked `omnigent-client` / `omnigent-ui-sdk` wheels. One press account says the Databricks AI team built it with Neon.

SASE↔Omnigent overlap (the fit thesis): multi-harness agent supervision; CLI-first developer experience; policy/approval gates and cost controls; sandboxing and workspace isolation; session/run observability and review; Python + CLI + open-source-community mechanics. A SASE contributor can speak to every Omnigent bullet with a shipped analogue.

## 4. Candidate background as inferred (assumptions flagged)

- Assumption (stated by requester): substantial contributor to SASE (`sase-org/sase`). `pyproject.toml` in the checkout names Bryan Bugyi as author/maintainer, consistent with a deep SASE history, but commit-level attribution was not audited for this report.
- Corroborating context: the working checkout is `bob-cli` (Rust CLI, `clap` 4.6, `clap_complete`, `serde`, `rquickjs`, `rusqlite` on macOS) — a real shipped CLI with shell completion, justfile, and test suite. That supports a "CLI + developer-tooling + open-source" narrative alongside the Python agentic-orchestration narrative.
- Unknowns not verified: years of experience, people-management history, location/work-authorization, prior DevRel/public-speaking record, ML/infra depth outside agent orchestration. Recommendations below weight roles by how little they assume beyond "deep agentic-coding-tooling practitioner."

## 5. Databricks openings found

### P1 — Sr. Developer Advocate, Open Source — Omnigent (strongest match, verified open)

- Posting: https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716730002?gh_jid=8716730002 (fetched 2026-10-07, HTTP 200; requisition RDQ327R182; listed location Seattle, Washington; reports to Head of Developer Relations).
- Mission: bridge between Omnigent engineering and the OSS community forming around it — templates, demos, reference implementations developers can clone/fork/extend; lower the barrier to first contribution; review/triage in the open; grow maintainers; drive adoption including in stacks with nothing to do with Databricks.
- Impact bullets include: own medium-to-large advocacy projects end-to-end; grow the contributor community; show integration into existing agent stacks; ship templates/sample repos/reference implementations; produce videos/tutorials/courseware/blog posts covering harness composition, contextual policies, sandboxing, cost controls; speak at events/meetups; advise engineering on roadmap from community signal; support developers on GitHub issues, Discord, Slack, Stack Overflow, Reddit; mentor junior advocates.
- Requirements include: 5+ years combined DevRel + hands-on technical role (SWE/ML engineer/solutions architect); professional software-building experience **and current hands-on experience with agentic developer tooling and coding agents**; strong Python **and TypeScript**; CLI comfort in other people's codebases; demonstrated OSS contributions in the open (issues/PRs/reviews/releases); subject-matter knowledge of agent architecture, orchestration, sandboxing, safe/affordable agent ops; community-growing (not just user-base) experience; public portfolio (repos/tutorials/talks/sustained contributions); exceptional communication; developer empathy; cross-functional collaboration.
- Zone 2 pay range listed: $133,000–$186,100 USD.
- Fit assessment: near-perfect on substance. SASE work covers agentic tooling, orchestration, sandboxing/workspace isolation, policy/approval gates, cost awareness, CLI UX, and OSS-in-the-open mechanics; Omnigent checkout knowledge (harness composition, CEL policies, sandbox extras, Databricks gateway routing) maps 1:1 onto the listed content topics. Gaps to address honestly: TypeScript depth (SASE/bob-cli evidence is Python + Rust; show or build one TS sample before applying), and public DevRel track record (talks/videos/courseware volume, meetup leadership). If those two are thin, frame the application around artifacts (templates, reference implementations, contributor-ladder improvements) rather than stage presence.
- Suggested application angle: propose a 90-day contributor-growth plan for `omnigent-ai/omnigent` (first-PR friction audit, template gallery, "integrate Omnigent into a non-Databricks SASE-like stack" reference implementation), and link SASE analogues for each.

### P2 — Backend Software Engineer, AI Platform / AI Engineering org (strong engineering match; verify current req before applying)

- Representative description (observed via Built In and startup.jobs mirrors of Databricks' AI Engineering org posting, P-1428 family): build the substrate powering data apps, AI agents, model training/serving, vector search; offerings named include MLflow, AI Gateway, Databricks Apps, **Agent Framework, Agent Bricks**, Foundation Model APIs; improve reliability/latency/efficiency of distributed AI workloads; 5+ years backend/infra; strong Scala, Go, or **Python**; distributed systems/scalable APIs/cloud-native infra; service-oriented architecture, deployment pipelines, observability. Bonus: real-time serving, ML infra/GPU orchestration; SageMaker/Vertex/Azure ML exposure; OSS contributions (MLflow, PyTorch, Ray); developer platforms/internal AI-workflow tooling.
- Mirrors: https://builtin.com/job/senior-backend-software-engineer-ai-platform/6540749 (note: this mirror showed "removed Mar 30, 2026" when fetched — treat as a **description reference**, not a live req) and http://startup.jobs/staff-backend-software-engineer-ai-platform-databricks-7895915 (aggregator; verify on Databricks open-positions before citing).
- Fit assessment: strong for a Python-heavy orchestration/infra engineer; SASE's service host, scheduler, workspace claims, queue/admission budgets, subprocess supervision, and Rust-backed deterministic ops translate to "distributed AI workloads" language. Gap: Databricks backend roles skew Scala/Go + cloud-scale serving; emphasize Python orchestration, reliability/observability, and any GPU/serving-adjacent work. Search Databricks open-positions for "AI Platform" / "Agent Framework" / "Agent Bricks" to find the live req in this family.

### P3 — Software Engineer (Fullstack), Developer Ecosystem — SDK / CLI / Terraform (strong tooling match; verify current req)

- Representative description (observed via search snippets of Databricks open-positions req `gh_jid=6779943002` and mirrors): "The developer ecosystem team focuses on the development experience and best practices using tools outside of the workspace. We own and govern the core developer ecosystem open-source components: the SDK, the CLI, and Terraform." Mirrors: https://www.databricks.com/company/careers/open-positions/job?gh_jid=6779943002 (fetch redirected to the listings index at research time — verify the req is still live), https://startup.jobs/senior-software-engineer-fullstack-databricks-2-4455230 (aggregator).
- Fit assessment: arguably the best pure-engineering fit after the Omnigent advocate role — SASE CLI architecture + `bob-cli` (Rust/clap/completion) + SDK/CLI governance is exactly this team's remit. Emphasize: CLI help/UX standards, completion engines, JSON helper bridges, versioned contracts, open-source component stewardship.

### P4 — Applied AI Engineer, Genie Code / agentic systems (moderate-strong match; verified posting exists, location caveat)

- Posting: https://www.databricks.com/company/careers/engineering---pipeline/applied-ai-engineer-8091041002 (fetched 2026-10-07, HTTP 200; requisition P-1439; listed location Belgrade, Serbia; reports to a Principal SWE/Director-level; "Genie Code, an agent and an ML exoskeleton that is authoring ML, training and deploying models, monitoring and self-healing production ML").
- Requirements snippet: 2–8 years in high-velocity/high-growth companies; infrastructure/systems engineers without ML background welcome; strong SWE fundamentals (testing/deployment); production AI/ML-at-scale a plus; Tier-0 training/serving infra nice-to-have.
- Fit assessment: the "infrastructure/systems engineers welcome" line is an explicit door for a SASE-profile candidate; agentic end-to-end systems + open-source/conference participation are called out. Caveat: Belgrade listing — only pursue if location-remote works; otherwise use it as proof of the Applied AI job family and search for the same title in a US/EU hub.

### Also-seen (lower priority, not fully verified)

- Staff SWE, AI-Native Web Platform (P-1579, Mountain View; "rebuilding the platform AI-native, pioneering an agentic SDLC") via echojobs mirrors — interesting but web-platform-specific; pursue only if full-stack web appetite is real.
- Specialist Solutions Architect AI/ML and GenAI Solutions Architect family (field engineering, RAG/fine-tuning, enterprise productionization) — viable only if a customer-facing pivot is desired; weaker use of the SASE-building advantage.

## 6. Risks and honest gaps

- Seniority bar: Databricks SWE postings in this space routinely ask 5+ years backend/infra and distributed-systems depth; the advocate role asks 5+ years combined DevRel + hands-on technical. A pure-OSS-contributor profile without that tenure or without a public portfolio will stall at screening — lead with shipped artifacts and numbers (adoption, contributors mentored, performance/reliability wins).
- TypeScript: the Omnigent advocate role explicitly requires strong Python **and** TypeScript; current verified evidence is Python + Rust. Close or disclose this gap with a TS sample.
- Posting churn: one Built In mirror in this family is already marked removed, and one open-positions deep link redirected to the index. Re-verify every req on https://www.databricks.com/company/careers/open-positions the day of applying; requisition IDs (RDQ327R182, P-1439, P-1428 family, `gh_jid=6779943002` family) help confirm liveness.
- Location: verified pages list Seattle (advocate) and Belgrade (applied AI); confirm remote/hub policy with the recruiter rather than assuming.

## 7. Recommended application list (in order)

1. **Sr. Developer Advocate, Open Source — Omnigent** — https://www.databricks.com/company/careers/product/sr-developer-advocate-open-source--omnigent-8716730002?gh_jid=8716730002 — best fit; apply with an Omnigent-specific 90-day community plan and SASE-mapped portfolio.
2. **Software Engineer (Fullstack), Developer Ecosystem (SDK/CLI/Terraform)** — https://www.databricks.com/company/careers/open-positions/job?gh_jid=6779943002 — best engineering fit; verify the req is live, else search open-positions for "Developer Ecosystem."
3. **Backend Software Engineer, AI Platform (Agent Framework / Agent Bricks / MLflow / AI Gateway family)** — search https://www.databricks.com/company/careers/open-positions for "AI Platform" — representative mirrors: https://builtin.com/job/senior-backend-software-engineer-ai-platform/6540749 (removed-marker reference) and http://startup.jobs/staff-backend-software-engineer-ai-platform-databricks-7895915 — apply to the live req in this family, not the dead mirror.
4. **Applied AI Engineer (Genie Code / agentic systems)** — https://www.databricks.com/company/careers/engineering---pipeline/applied-ai-engineer-8091041002 — pursue if Belgrade/remote works, otherwise use it to find the same title in your hub.

Verification notes: items 1 and 4 were fetched from databricks.com with HTTP 200 during this research (2026-10-07). Items 2 and 3 rest on search-snippet and aggregator evidence plus one redirected deep link; confirm liveness on the official open-positions board before applying. No peer swarm reports were consulted. SASE and Omnigent claims were read from `sase repo open` checkouts, not web-fetched file URLs.

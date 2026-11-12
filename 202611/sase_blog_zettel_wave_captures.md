# Paste-ready captures for SASE Blog Zettel Waves 1–4

These four captures create 15 🌱 seed records in `sase_blog_zettel`. Each wave is
one paste into Bob Mac Capture. Every block passed `bob capture --dry-run` against the
live vault on 2026-11-12, both one wave at a time and all four waves pasted together:
15 creates, one album-index update, and nothing written.

## What each wave holds

The writers-block plan (`ref/chat/sase_blog_writers_block_task_plan`) names Waves
1–3, followed by R, I, and P. Its Wave 2 holds 6+ topics, which breaks the
plan's own limit of four per wave, so I split it in two:

| Wave | Article sections | Records |
| --- | --- | --- |
| 1 | §2.3, §2.3.2, §2.1, §2.5 (the four agreed sections) | 4 |
| 2 | §2.2, §2.3.1, §2.4, §2.6, §2.7 (the five "maybe" headings) | 5 |
| 3 | §3 Why you should (probably) NOT use SASE (the plan's "What It Cost") | 3 |
| 4 | §1 Why I use SASE, §3.2 Future Work, §4 Conclusion (the plan's old Wave 3) | 3 |

Waves R, I, and P create no new topics. The intro, the promise sentence, and the
transitions belong in `sase_blog_contents.md`, not in records.

## Before you paste

- **Each block is all-or-nothing.** If any item fails, nothing is written. You can
  paste one wave at a time, or all four joined by blank lines.
- **Rewrite any claim that doesn't sound like you.** Most claims quote or reuse your
  own notes. ✏️ marks the four I had to guess, because no note offered one. If you
  can't write a claim for a record, leave that record out; per the plan, that is
  evidence for the Wave 1 review.
- **Stems are permanent and must use hyphens.** Bob refuses `_` in `^stem`. To add
  notes later, capture `idea text @sase_blog_zettel/<stem>`.
- **First-level bullets become dated `## Notes`.** I used them for the Wave 1 CARD
  lines and the matching `## Requirements` bullets. I didn't use the `%t` template,
  because template rows can't have child bullets.

## Wave 1: the four agreed sections

```text
One CLI → Every CLI @sase_blog_zettel/^agent-clis
- status:: seed
- part:: what
- claim:: SASE puts every provider's coding-agent CLI behind one harness, and it promises the best experience, not the best performance.
- 😈 one CLI at a time · 😇 every provider behind one harness
- PROOF: retries carried me through a <30m Claude outage (~/tmp/screenshots/20260616_140429.png)
- LESSON: "optimal experience, not optimal performance"; usage-window indicators
- QUOTE: The ability to have different frontier models from competing labs swarm a difficult task together is something even those working at those labs don't have access to, or at least likely haven't explored fully.

A Wall of Terminals → One Screen @sase_blog_zettel/^agent-presentation
- status:: seed
- part:: what
- claim:: One screen that organizes every agent (tribes, clans, sessions) beats a wall of tmux terminals.
- 😈 tmux_ai_window · 😇 one screen for every agent
- PROOF: the agents-observability GIF
- LESSON: the Agents tab is the buggiest part of the TUI; "sub-agent" doesn't cut it for agents that other agents run
- Answer "Why a TUI?" here.

Plan Mode → Gates → Plans → Epics @sase_blog_zettel/^gates-plans-epics
- status:: seed
- part:: what
- claim:: Plan mode is one instance of a deeper primitive, the gate, and gates grow into plans and then epics.
- QUOTE: "Plan mode is the canonical or best example of some deeper primitive. I know it. Interrupts?"
- PROOF: an agent read 4 related plans while planning (img/20260824_141701.png)
- LESSON: artifact sidecars make plans auditable through `sase artifact read`; artifact write/validate goes to Future Work

One Prompt → Programs @sase_blog_zettel/^macros-control-flow
- status:: seed
- part:: what
- claim:: Macros (formerly xprompts) turn one prompt into a small program with forks, waits, queues, and alternations.
- PROOF: `%wait` at work (~/tmp/screenshots/20260616_115015.png)
- Alternations allow "vibe evals" (~/tmp/screenshots/20260619_214831.png)
- Stashed prompts: img/20260802_144938.png, img/20260802_144945.png, img/20260802_144951.png
- QUOTE (PIW goals): Goal number one: make editor support for xprompts as awesome as possible with LSP. Goal number two: make the prompt input widget so fucking awesome that using any other editor for agent prompts is unthinkable.
- LESSON: loop engineering vs graph engineering
```

## Wave 2: the five "maybe" headings

✏️ = my guess at the claim: `beads-sidecars`, `vcs-workspaces`, `project-management`,
`routines-jobs`. Seeds cost nothing. In the Wave 1 review, set these to ⏭️ later or
✂️ cut rather than deleting them. Your Later Posts list already has "Beads and SDD",
"Memory", and "ChangeSpec" (now Patches).

```text
Beads → Sidecar Repos @sase_blog_zettel/^beads-sidecars
- status:: seed
- part:: what
- claim:: SASE generalizes beads into sidecar repos: plans, beads, and research live in their own git repos beside the code.
- Gas Town diff: beads (way less use), rigs, (NO) mayor
- `reads` and `snips` are possible future sidecars
- Later Posts already lists "Beads and SDD"

Skills, Memory, Provider Interface — Not Hooks @sase_blog_zettel/^skills-memory
- status:: seed
- part:: what
- claim:: If I were building agents from scratch today, skills would just be procedural memory.
- I've implemented project memory every wrong way possible, so I must be converging on a good solution soon, right?
- Why NOT hooks? The rationale isn't written down anywhere yet.
- Later Posts already lists "Memory"

VCS and Workspace Operations @sase_blog_zettel/^vcs-workspaces
- status:: seed
- part:: what
- claim:: Every agent gets its own workspace clone and SASE owns the commit, so parallel agents never trip over each other.
- ChangeSpec is now Patches (sase.sh draft "Patches in Practice")

Project Management @sase_blog_zettel/^project-management
- status:: seed
- part:: what
- claim:: Hoods, the agents sidecar, and artifacts let me manage agent work as a project instead of a pile of chats.

Routines and Jobs @sase_blog_zettel/^routines-jobs
- status:: seed
- part:: what
- claim:: Routines and jobs let agents work on a schedule, not only when I type a prompt.
```

## Wave 3: why you should (probably) NOT use SASE

"AI broccoli" has no claim yet, so it is a note on `limitations` instead of a record of
its own.

```text
My Definition of AI Slop @sase_blog_zettel/^ai-slop
- status:: seed
- part:: why_not
- claim:: SASE has AI slop too: unneeded backward compatibility, unused features, duplicated logic, and prompt debt.
- Prompt debt = alignment that degrades over time from bad prompting and/or bad code review
- Give one real example from the sase codebase for each category

Limitations @sase_blog_zettel/^limitations
- status:: seed
- part:: why_not
- claim:: SASE is a prototype gone wild with about one user, so expect sharp edges.
- JOKE: my ulterior motive is adding everyone to SASE with a promise to let them disable Vim mode, then never doing it
- AI broccoli (Google Keep, 2026-09-10): its own record once it has a claim, or a paragraph here

Naming Things @sase_blog_zettel/^naming
- status:: seed
- part:: why_not
- claim:: I'm bad at naming things, and I worry that points to a deeper problem with the design.
- Jokes about why sase and macros are named the way they are
- Renames so far: xprompts → macros, ChangeSpec → Patches
- Footnote [1] facts: pronounced "sassy"; collides with Gartner's Secure Access Service Edge
```

## Wave 4: how I got here, what's next, and the ask

```text
How I Got Here @sase_blog_zettel/^how-i-got-here
- status:: seed
- part:: why
- claim:: SASE grew one rung at a time: the Boris method, then tmux_ai_window, then auto-approved plans, then wait and fork.
- Explain why I left Google, or maybe just that I did
- Salvage the tmux_ai_window scene from the July launch post
- Hook idea: a brief, funny timeline of software engineering's transformation (infographic)

Epics, Legends, and Myths @sase_blog_zettel/^future-work
- status:: seed
- part:: why_not
- claim:: SASE's purpose is to build the next SASE from scratch: the first myth.
- No goal milestones: a legend is a group of epics, and a goal should outlive an epic
- SASE goals will be much smaller and much larger than other goals
- Finalizer ideas; merging agent project memory with project docs (Diátaxis?)

I Need Your Help @sase_blog_zettel/^need-your-help
- status:: seed
- part:: close
- claim:: I need your help: I'm out of tokens.
- End with GitHub issues labeled `type:poll` that ask readers questions
- Series map: point parked sections at the Later Posts
```

## After capturing (optional, about 5 minutes)

1. **Give each idea one home.** Delete the CARD lines from `^zd-cli`, `^zd-tui`,
   `^zd-gates`, and `^zd-macros`, and add a record link to each task instead (for
   example, `→ [[sase_blog_zettel/agent-clis|One CLI → Every CLI]]`). Delete copied
   `## Requirements` bullets now, or later when you draft that topic.
2. **Wire the spine.** Put the same `→ [[sase_blog_zettel/<stem>|Title]]` lines under
   the matching headings in `sase_blog_contents.md`.
3. **Then stop.** The next writing work is dictating the four Wave 1 zero-drafts into
   each record's `## Draft`.

## Left in place on purpose

- **The Gas Town term map, style rules, and emoji/stick-figure ideas:** these are
  post-wide, so they stay in `## Requirements`.
- **"Email the agent_swe authors" and the podcast pass:** these are work, so they stay
  tasks. Records never hold checkboxes.

Sources: `202611/sase_blog_drafting_in_records/sase_blog_drafting_in_records.md`,
`202611/sase_blog_zettel_album_guide.md`, `~/bob/sase_blog.md`,
`~/bob/sase_blog_contents.md`, `~/bob/sase_blog_zettel.md`, the writers-block plan PDF
(§1.6.4 "The waves"), and bob-cli `docs/capture.md` (§Record notes, §Bulk templates).

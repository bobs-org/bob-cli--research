# One tie per pair: plain links and dependencies

*Researcher `cld` · 2026-11-25 · bob-cli, bob-plugins (navigation-hotkeys,
ledger-tools), Bob Mac Capture*

## TL;DR

Yes, do this. Two tasks should never carry both a dependency and a plain
(unlabelled) link, and the Links and Depends on stages should be able to
convert one into the other with a single key. The brief as written has three
gaps, though. I would change three things before building it:

1. **The two literal rules miss every overlap that actually exists.** A
   read-only scan of `~/bob` (5,883 notes, 274 dependency edges, 321 LINKS
   entries) found two dependency-plus-plain-link overlaps. In **both**, the
   *prerequisite* links to its *dependent*: the reverse direction. "Remove
   any existing dependency to task B from the current task" never matches
   that shape. The invariant has to be **pair-level, in both directions**.
2. **A plain link should not quietly delete a dependency.** If the
   either-direction version of rule 1 had applied to the second real case
   (a research task that gained a plain link to its dependent at close),
   it would have deleted a dependency Bryan never meant to drop. Adding a
   dependency over a plain link loses nothing, so let it absorb the link
   everywhere. Replacing a dependency with a plain link changes the task's
   status, so allow it **only from an Obsidian tie gesture that shows the
   consequence on the highlighted row before ↵**. Everything else (capture
   `~`, hand edits, agents, reconcile) leaves the dependency in place.
3. **Ctrl+B alone can't capture the direction.** A plain link says nothing
   about which task waits on which. The first real case was "my link should
   have been *it waits on me*". So the stages need two dependency
   directions. The clean way is one grammar that copies the Task Card's
   keycaps: **⌃B** = this task waits on it, **⌃⇧B** = it waits on this
   task, **⌃L** = make it a plain link. The same keys work in all four
   relationship stages.

The recommended solution (§9) rests on one new contract rule: **a
dependency absorbs a plain link; only an explicit tie gesture can release
it.** Reconcile enforces it vault-wide at low cost, because the
"does a dependency join this pair, either way" predicate already exists for
text mentions (`dependency_joins` in
`src/native/task_status_hooks/relations.rs`).

---

## 1. What exists today

### 1.1 The two edge kinds

| | Dependency | Relation (LINKS entry) |
| --- | --- | --- |
| Stored on | the dependent's `⛓️ **DEPENDS ON:**` line | the source's `🪢 **LINKS:**` line, with an optional label |
| Mirror | generated `🧱 **BLOCKS:**` on the prerequisite | generated `🪢 **LINKED FROM:**` on the target |
| Effect | the dependent stays Blocked `[?]` while a prerequisite is open; lane transfer; Pomodoro link consumption | **none**: `docs/task-relations.md` §2 "What relations never do", guarantee 2 "Inertness" (LR18, LX13, LG13) |
| Obsidian stages | Depends on (Ctrl+Shift+B / Task Card `b`), Blocks (Ctrl+Shift+Alt+B / `⇧B`) | Links (Ctrl+Shift+L / `l`), Linked from (Ctrl+Shift+Alt+L / `⇧L`) |
| Capture | `&` (depends on), `*` (blocks) | `~` (links to), `~~` (linked from), `\|label` |

The UI already treats the label as "the relation". The Links stage footer
reads `↵ link · ⌃↵ with a relation`, and the Mac picker reads
`↩ link · ⇧↩ link with a relation`. So Bryan's "relationless link" is an
unlabelled LINKS entry. Below I call it a **plain link**. That name also
works in the docs, where every LINKS entry is a "relation", so
"relationless relation" would contradict itself.

### 1.2 Cross-awareness that already exists

- **Links stage → dependencies (one direction, information only).** A
  RESULTS row that is also one of the owner's prerequisites gets a
  `⛓ prerequisite` badge, with the tooltip **"Also a prerequisite ·
  linking stays inert"**
  (`bob-navigation-hotkeys/src/410-picker-filter-and-render.js:492`,
  identities from `relationStagePrerequisiteIdentities`,
  `304-relation-stage-view.js:270`). This only covers *outgoing*
  dependencies; nothing marks a row whose task waits on the owner. Under
  this proposal the tooltip becomes false.
- **Depends on and Blocks stages → links: nothing.** No badge, no section.
- **Mac Capture.** `capture-complete` `relation_to` / `relation_from` rows
  carry `also_prerequisite`, and the picker renders it as **Prerequisite
  too** (`docs/reference/mac-capture/relationship-pickers.md`). Again only
  one direction.
- **Mentions already rank below dependencies.** M7 drops a `💬 mentions`
  entry whenever "a dependency joins (S, T)", in either direction
  (`dependency_joins`, `relations.rs:1227`, which checks both
  `depends_from_loc` and the reverse `depends_identities`). The ordering
  *dependency > relation > mention* already exists for derived entries. This
  proposal applies it to authored *plain* relations too.
- **Duplicates are already canonicalised away.** LK8: a LINKS line that
  names the same target twice keeps only the first entry. The proposed
  fold is the cross-line version of the same rule.

### 1.3 Consequence strips and keys

- The Links and Blocks stages each have a fixed-height **consequence
  strip** (`305-relation-stage-copy.js`, `303-blocks-stage-copy.js`). The
  forward **Depends on stage has none**.
- In-stage Ctrl+letter keys already shadow global hotkeys. Ctrl+R (reroll
  or rename) works inside the picker even though `Mod+R` is bound to
  `app:reload`. So **Ctrl+L** is safe inside a stage even though Bryan's
  `hotkeys.json` binds global Ctrl+L to `mrj-jump-to-link`. **Ctrl+B**
  (bold) only applies in the editor. Neither key is used by any stage
  today. On macOS, Ctrl+B in a text field normally moves the caret one
  character back; the stage would `preventDefault` it, as Ctrl+N/P
  already do.

## 2. Evidence from the vault

The scan was read-only and approximate: it resolves links by note basename
and covers `done/`. The script is at `/tmp/cld_scan/scan.py`.

| Overlap shape | Plain | Labelled |
| --- | --- | --- |
| A depends on B **and** A links to B (what the brief's rules cover) | **0** | 1 (`picks out good hard-drive`) |
| A depends on B **and** B links to A (the reverse direction) | **2** | 0 |
| A plain-links B **and** B plain-links A | 0 | n/a |

Only 58 of the 321 LINKS entries are plain. The labelled ones are mostly
`implemented by` (148), `superseded by` (37), and `inspired by` (33).

**Case 1: "I linked it, then realised it was a dependency."** In `bob.md`,
the ref task `^ref-plugin-sync-unblocking` gained
`🪢 LINKS: [[#^no-bob-plugins-sync-qs]]` at 2026-11-17 07:48:35. **Nineteen
seconds later** `^no-bob-plugins-sync-qs` gained `⛓️ DEPENDS ON:` the ref
task, the ref task gained `🧱 BLOCKS:`, and the ref moved `[*]` → `[/]` (the
dependency writers' lane transfer). The note now shows the same fact four
times: BLOCKS + LINKS on the ref, DEPENDS ON + LINKED FROM on the fix. This
is exactly the workflow a conversion key is for. The dependency Bryan
wanted ran **from the linked task to the current one** (it waits on me), so
a Ctrl+B that only means "I wait on it" would have produced the wrong edge.

**Case 2: "a hand-off pointer at close."** In `cash.md`, the research task
`^pick-day-to-sell-stocks` was born blocking `^sell-stocks-now`
(2026-11-15). When it was completed (2026-11-16 12:46) it also gained a
plain `🪢 LINKS:` to that same dependent. Under the either-direction version
of rule 1 ("adding a plain link removes the dependency"), that link would
have **deleted the dependency**. The dependency was already satisfied, so
this mostly loses history, but nobody intended it. Under the literal
rule 1 nothing happens, and the overlap stays.

So the literal rules catch 0 of 2 real cases, and the obvious repair
(apply rule 1 in both directions) would have done the wrong thing in one
of them.

## 3. Is this a good idea?

**Yes, on balance.** The incidence is low (2 of 274 dependency edges), so
the case does not rest on volume. It rests on three things:

1. **Redundancy is visual noise in the most visible place.** Each overlap
   puts the same fact on four child lines across two tasks, as two chip
   rows per task. Chips are what Bryan reads all day.
2. **Correcting the edge kind is a real workflow** (case 1), and it
   currently takes two stage trips plus a manual unlink. Bryan forgot the
   unlink, which is how case 1 happened.
3. **The stages currently mislead.** "Linking stays inert" is true, but it
   invites case 2. The Depends on stage gives no sign that a link exists.

**The risks:**

- **Inertness breaks.** Under rule 1, a gesture made from the Links stage
  can now unblock a task. §2 and guarantee 2 of `task-relations.md` must be
  reworded, not quietly violated. My framing: *a tie change that adds or
  removes a dependency is a dependency write* and follows the dependency
  contract (guards, lane transfer, consumption, stamps). Relation writes
  themselves stay inert.
- **Downgrades unblock work.** `bob capture` is also used by agents. If
  "add a plain link" could remove a dependency anywhere, an agent adding a
  "see also" would unblock tasks. That is the reason for adjustment A2.
- **Cost against benefit.** This touches Rust (reconcile, capture,
  completion), the nav plugin (four stages, the writers), and Mac badges. I
  keep the scope tight (§8) so the cost buys the conversion keys and the
  clarity, which carry most of the value. Enforcing the invariant in
  reconcile is the cheap part.

**Approaches I would not take** (details in §7): showing both but hiding
the redundant link in display only; unifying the two stores into one
LINKS line with a reserved `depends on` label; and refusing instead of
converting.

## 4. Adjustments to the requirements (called out)

| # | Brief | Adjusted to | Why |
| --- | --- | --- | --- |
| **A1** | "relationless link" | **Plain link** = a LINKS entry with no label. **Labelled relations may coexist with a dependency.** | A label carries meaning a dependency doesn't (`follow-up of`, `split from`, `implemented by`). The one labelled overlap in the vault is legitimate. Dropping it would lose information. |
| **A2** | Adding a plain link removes the dependency, everywhere | **A dependency absorbs a plain link everywhere. Only an Obsidian tie gesture with a consequence preview releases a dependency.** Capture `~`, hand edits, agents, and reconcile leave the dependency in place. | Asymmetric risk: absorbing loses nothing, while releasing changes status. Case 2 shows that adding a plain link next to a dependency is usually not meant as a downgrade. |
| **A3** | The invariant applies "in either direction" (stated), but rules 1 and 2 only act on the current task's own edges | The invariant is over the **unordered pair**: if a dependency joins A and B either way, neither task holds a plain link to the other. Writers and reconcile act on both ends. | Both real cases are the reverse direction. |
| **A4** | Ctrl+B in the Links stage = "mark as a dependency" | **⌃B = this task waits on it, ⌃⇧B = it waits on this task.** | A plain link has no meaningful direction, so the user must choose one. Case 1 needed ⌃⇧B. The keys mirror the Task Card keycaps `b` / `⇧B`. |
| **A5** | "The reverse from the dependency panel" (key unspecified) | **⌃L = make it a plain link**, in the Depends on and Blocks stages | Mirrors the Task Card `l` and global Ctrl+Shift+L. Safe inside a modal (§1.3). |
| **A6** | Only the "link" and "dependency" panels | The same badges and keys in all **four** relationship stages (Depends on, Blocks, Links, Linked from) | Case 1 happened from the prerequisite's side, so the Blocks stage needs the badge just as much. One grammar is easier to learn than two. |
| **A7** | (implicit) "make it impossible" | Writable notes converge through **reconcile**. Read-only history (`done/`, the previous daily note) is never rewritten. | Bob never rewrites `done/` outside `relations rename`. One of the two real overlaps lives in `done/cash_done.md` and should stay as history. |
| **A8** | (new) | The Depends on stage gains the **consequence strip** the Links and Blocks stages already have | Keyboard users never hover, so the strip is the only place a conversion's consequence ("Ready again") can be shown before ↵. |

## 5. Design

### 5.1 Vocabulary

- **Plain link**: a task relation with no label.
- **Tie**: what joins two tasks A and B structurally. Exactly one of:
  `none`, `⛓ A waits on B`, `🧱 B waits on A`, `🪢 plain link` (either
  direction). Labelled relations are *not* ties: they are annotations that
  can sit beside any tie.
- **Absorb**: adding a dependency removes the pair's plain links.
- **Release**: an explicit gesture that replaces a dependency with a
  plain link.

### 5.2 The invariant (PT0)

> For tasks A ≠ B in writable notes: if A's Depends-On line lists B, or
> B's lists A, then neither A's nor B's LINKS line holds a **plain** entry
> for the other.

Ordering rule when the two conflict: **the dependency wins.** Labelled
entries are untouched. Mentions keep M7, so a mention never appears for a
pair that has a tie.

### 5.3 Who enforces it

| Writer | Adds a dependency over a plain link | Adds a plain link over a dependency |
| --- | --- | --- |
| Depends on / Blocks stage ↵ or ⌃B / ⌃⇧B | **absorb** in the same gesture (one transaction when same-note) | n/a |
| Links / Linked-from stage ↵ or ⌃L | n/a | **release**: the row shows `⇄` and the strip previews the status change |
| Capture `&`, `*` (CLI, Mac) | **absorb** in the same staged batch; reported as `absorbed_plain_links[]` | n/a |
| Capture plain `~` / `~~` | n/a | **no-op**: `relation_updates[].action: "unchanged"` plus `subsumed_by: "dependency"`, with a warning. `~T\|label` writes normally. |
| One item with `&T ~T` (or `*T ~~T` and similar) | teaching error: *"T is already a prerequisite here · drop `~` or give it a `\|label`"* | |
| Obsidian hand edit | reconcile folds the link. When the cursor leaves the line, nav shows one notice: *"🪢 Already tied by ⛓ · this plain link folds into the dependency"*. Nav writes nothing (an immediate fold would fight Ctrl+Z, which re-fires hand-edit mirrors per LG10). | same |
| `bob task reconcile` | **fold**: drop the plain entry or entries. Never drop a dependency. | same: the dependency wins |
| Highlights annotation tasks, successors, moves, merges, splits | nothing new; reconcile converges | |

Reconcile details, as a new step in `reconcile_relation_lines` before the
LINKED FROM projection (it already holds the `DependencyState` M7 uses):

- Reuse `dependency_joins` semantics. Skip (never prune on uncertainty)
  when either end's Depends-On or LINKS line is malformed, the source is
  an `uncertain_dependent`, the note has duplicate block ids, or the note
  is quiet-deferred.
- This needs one explicit exception to §7.5 "reconcile never edits a
  LINKS line": *except to fold a plain entry its pair's dependency
  subsumes.* It is the cross-line twin of LK8.
- Report additive JSON `absorbed_plain_links[] {path, line, source,
  target, dependency: "source_waits"|"target_waits"}`. Human output:
  `🪢 −1 plain (⛓)`. `--dry-run` previews it. The one-time vault effect is
  exactly case 1. Case 2 stays because it is in `done/`.

### 5.4 The key grammar: "Ctrl plus the Task Card key"

The Task Card opens the four stages with `b`, `⇧B`, `l`, `⇧L`. Inside any
of those stages, the same letter with Ctrl **changes the highlighted
task's tie to that kind**. Everything is relative to the stage's owner,
exactly as the card's keycaps are.

| Key (any of the four stages) | Result for owner O and highlighted task X |
| --- | --- |
| **⌃B** | ⛓ O waits on X (absorbs plain links; keeps labelled ones) |
| **⌃⇧B** | 🧱 X waits on O. On a CURRENT prerequisite this **reverses** the dependency (cycle-checked). |
| **⌃L** | 🪢 O links to X, plain (releases any dependency on the pair) |
| ↵ | unchanged meaning: toggle *this stage's* kind. If the pair already has the other kind, ↵ **converts** (rules 1 and 2, made explicit by §5.5). |

- A Ctrl key whose kind the pair already has does nothing: a notice
  ("Already waits on it") and the stage stays open. Otherwise the stage
  closes, like ↵.
- Guards are the existing ones. ⌃B / ⌃⇧B use the dependency guards (cycle
  ⟲ checked on the trial graph, "inside this project", the `＋ id` prompt,
  stale-row refusal). Rows a dependency cannot target are disabled for
  those keys, with the strip giving the reason: closed or archived tasks
  and daily-note Event Tasks are outside the Depends on pool (*"Only open
  tasks outside daily notes can be prerequisites"*).
- **v1 scope:** single owner, highlighted row only. A counted session
  (`N Ctrl+Shift+L`) or active Tab marks refuse the Ctrl keys with
  *"⌃B acts on one task"*, following the existing *"Linked from needs a
  single task"* refusal.
- I'm deliberately **not** shipping ⌃⇧L ("it links to this"). A plain
  link's direction carries no meaning, and the Linked-from stage's ↵
  already does it.

### 5.5 Making the existing tie obvious

Same glyphs, no new palette, nothing that changes line height. Mock-ups
are illustrative, using case 1's tasks.

**Links stage on the ref task, before the fix** (it already links to the
fix task):

```
🪢 Links · Stop SASE agents blocking on bob plugins sync
Links to 1 · searching 1,204 tasks · ⇥ marks several · ⌃B / ⌃⇧B make a dependency
[ Filter tasks                                                          ]
CURRENT
  [/] Stop frequent bob-plugins sync QUESTIONS!    Line 420             −
RESULTS
  [*] Fix capture retries                          ↗ sase               ＋
🪢 Plain link · ↵ unlinks · ⌃↵ relabels · ⌃B this waits on it · ⌃⇧B it waits on this
↑↓ navigate   ⇥ mark   ↵ unlink   ⌃↵ relation   ⌃B prerequisite   ~ flip   esc
```

⌃⇧B → notice: `🧱 "Stop frequent bob-plugins sync QUESTIONS!" now waits
on this · replaced the 🪢 link · In Progress → Blocked`.

**The same Links stage afterwards:**

```
🪢 Links · Stop SASE agents blocking on bob plugins sync
Links to nothing yet · 1 tied by a dependency · searching 1,204 tasks
[ Filter tasks                                                          ]
TIED BY A DEPENDENCY
  [?] Stop frequent bob-plugins sync QUESTIONS!    Line 420   🧱 dependent   ⇄
RESULTS
  …
🧱 It waits on this · ↵ makes it a plain link instead · it becomes Ready again
```

**Depends on stage on the fix task, if only the link existed:**

```
⛓ Depends on · Stop frequent bob-plugins sync QUESTIONS!
Waits on nothing yet · 1 plain link · searching 412 open tasks · ⇥ marks several
[ Filter tasks                                                          ]
PLAIN LINKS
  [/] Stop SASE agents blocking on bob plugins sync   Line 57   🪢 links here   ⇄
RESULTS
  …
🪢 Plain link · ↵ makes it a prerequisite instead · replaces the link · Blocked
↑↓ navigate   ⇥ mark   ↵ make prerequisite   ⌃L plain link   esc
```

The rules behind the mock-ups:

- **Tie badges on every row, in every section**, beside the existing label
  pill, 🍅, 🔑, and 🔒 badges:
  - `⛓ prerequisite`: O waits on X. Keeps today's copy, but the tooltip
    becomes *"This task waits on it"*.
  - `🧱 dependent`: X waits on O.
  - `🪢 linked` / `🪢 links here`: shown in the Depends on and Blocks
    stages only.
  - A labelled relation shows its muted pill in the Depends on and Blocks
    stages for information, so the "follow-up of" stays visible when you
    add a dependency next to it.
- **The `⇄` action badge** replaces `＋` whenever ↵ will convert rather
  than add. Tab-marking such a row shows `⇄ convert`, so a batch can never
  convert something by surprise.
- **An empty-filter tie section**, shown only when it isn't empty:
  `TIED BY A DEPENDENCY` in the Links and Linked-from stages, and
  `PLAIN LINKS` in the Depends on and Blocks stages. It lists the owner's
  ties of the other kind in both directions, so the panel answers "is
  this already tied?" without any typing. In the Depends on and Blocks
  stages it lists open partners only.
- **The subtitle counts** the other kind: "Links to 2 · 1 tied by a
  dependency". The Links stage drops its trailing "does not block" because
  ⌃B now can.
- **The consequence strip** (added to the Depends on stage, A8) always
  says what ↵ and the relevant Ctrl key will do to status: "Ready again",
  "still Blocked (waits on 2)", "no status change" for a closed
  prerequisite, or "Blocked · removes its link from JOB 10:10–10:35". It
  reuses the Blocks stage's lane and Pomodoro phrases.
- **Notices lead with the destination glyph** and name what was replaced:
  - `⛓ Now waits on "X" · replaced the 🪢 link · Blocked`
  - `🪢 Now links to "X" · no longer waits on it · Ready again`
  - `⛓ Now waits on "X" · kept the "follow-up of" link`
- **Chips need no change.** The invariant means a pair never renders twice.

### 5.6 Write order and reliability

- **Same-task conversions** are the common case: ⌃B on your own plain
  link, ⌃L on your own prerequisite, or ↵ on either. Both lines are
  children of O, so the conversion is **one editor transaction and one
  Ctrl+Z**. The mirrors (BLOCKS, LINKED FROM) follow through the existing
  cross-note best-effort follow-ups.
- **Cross-task conversions** (⌃⇧B on a plain link, or ↵ on a 🧱 row):
  **write the dependency side first**, through the existing guarded
  writers (`applyBlocksEdit`, the forward writer) with their preflight,
  guards, stamps, lane transfer, and consumption. If it fails, write
  nothing else. **Then the link side, best effort.** This order converges
  either way:
  - Link → dependency: if the link removal fails, reconcile folds the
    leftover link.
  - Dependency → link: if the link add fails, the notice says
    `· 🪢 link not added` and the pair is still valid, just untied.
- One shared pure planner, `planTieChange({owner, other, to})`, composes
  the existing `planDependencyEdit` and relation LINKS planners. It has a
  Rust twin, and both are pinned by a new **PT vector** family in
  `docs/task-relations.md`, like the LW and DW families.

### 5.7 Capture and Bob Mac Capture

Capture stays the grammar authority and Mac stays a thin client.

- **`capture-complete`** (additive):
  - `relation_to` / `relation_from` rows gain
    `dependency_tie: "waits_on" | "blocks"`. Keep `also_prerequisite` for
    compatibility.
  - `task_dependency` / `blocked_task` rows gain
    `plain_link: "to" | "from"`.
  - Mac renders these as capsules: **Prerequisite · plain `~` adds
    nothing** and **Linked · `&` replaces the link**, replacing today's
    one-way "Prerequisite too".
- **`capture` / `--dry-run`**: `absorbed_plain_links[]` on `&` and `*`;
  `subsumed_by: "dependency"` on a plain `~` no-op; and the `&T ~T`
  same-item teaching error.
- Later, optionally: in the Mac Links To picker, ⌃B could swap the token
  being inserted from `~` to `&`, giving the same gesture in both
  clients.

### 5.8 Edge cases

| Case | Behaviour |
| --- | --- |
| Plain link in `done/` or the previous daily note | left as history; reconcile never writes there (case 2 stays) |
| Labelled relation plus dependency | allowed. ⌃B keeps the label; the notice says so. |
| `starts after` (successor label) plus dependency | allowed. It is labelled, and successor offers already de-duplicate. |
| Closing, cancel, or merge label on a dependency-tied pair | allowed. It fires at commit time as today. |
| `^prj` as owner or target | ⌃B / ⌃⇧B go through the project-dependency guards and resident side effects (§13) |
| `relations.linked_from_lines: false` | the fold still applies, because LINKS are authored; only mirrors are skipped |
| A mention plus a tie | M7 already drops the mention |
| A↔B mutual plain links | not folded (0 in the vault; not worth a rule yet) |

## 6. Contract and documentation changes

- `docs/task-relations.md`:
  - New **§22 Plain links and dependencies**: vocabulary, PT0, the
    writer table, the key grammar, and PT vectors.
  - §2 and guarantee 2 reworded: relation writes stay inert, and a tie
    change that touches a dependency is a dependency write.
  - §7.5 gains the fold exception.
  - The LX and LG tables gain rows for the capture no-op and the stage
    keys.
- `docs/task-dependencies.md`:
  - §6 and §15 gain the tie badges, the `PLAIN LINKS` section, the strip
    (forward stage), ⌃L / ⌃⇧B, and absorption in "one gesture writes".
  - §8 rows for `&` / `*` gain absorption.
- `docs/capture.md` and the Mac `relationship-pickers.md`: new fields and
  capsules.
- A new decision record, e.g. **`dependency-absorbs-plain-link`**, plus a
  glossary entry **Plain link**, both added through `/sase_memory_write`.
  The decision records A2's asymmetry and the rejected alternatives in §7.

## 7. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Literal brief** (two rules, current task's edges only) | Rejected: catches 0 of 2 real overlaps, and its direct either-direction extension would have deleted a dependency in case 2. |
| **Display-only de-duplication**: chips and stages hide a plain link that duplicates a dependency | Rejected: Markdown and the UI disagree. Hidden data resurfaces when the dependency is removed. The state isn't impossible, only invisible. |
| **Refuse instead of converting**: ↵ on a ⛓ row says "already a prerequisite" | Rejected as the default because of the friction. The `⇄` badge plus the strip make conversion explicit enough. Refusal remains the behaviour for counted sessions and marks. |
| **Dependency always wins, even in the stages** (no release gesture) | Rejected: Bryan explicitly wants to downgrade a dependency to a plain link from the dependency panel. ⌃L and ↵-convert cover that, with a preview. |
| **Unify storage**: a dependency is a LINKS entry with a reserved `depends on` label | Rejected: a vault migration, Tasks `dependsOn` derivation, four parsers, and decision `task-deps-are-depends-on-links` all stand against it. The pair invariant gets the user-visible benefit without any of that. |
| **One "Ties" stage** replacing the four | Rejected for now: the Task Card already routes to the four stages, and the Ctrl-key grammar gives most of the unification for little cost. |
| **Fold mutual plain links too** ("one plain tie per pair") | Deferred: 0 occurrences. |

Prior art, only loosely verified: Linear models relation types per pair,
and per its docs a resolved blocker "moves under Related". That is the same
intuition as here: a dependency is a "related" link with teeth. I couldn't
load the docs page itself, so treat this as a hint, not evidence
([Linear docs](https://linear.app/docs/issue-relations)). Jira allows
several link types on one pair, which is the clutter this design avoids
([Atlassian: configuring issue linking](https://confluence.atlassian.com/adminjiraserver/configuring-issue-linking-938847862.html)).

## 8. Phasing

1. **cli-contract**: docs (§6), PT vectors, the decision record and
   glossary entry.
2. **cli-core** (Rust):
   - the reconcile fold in `task_status_hooks/relations.rs`, reusing
     `DependencyState` and `dependency_joins`;
   - capture absorption for `&` / `*` (`src/native/capture/dependencies.rs`);
   - the plain `~` no-op, `relations_mirror.rs` / plan;
   - the `&T ~T` error;
   - the `capture-complete` fields (`capture_complete/candidates.rs`,
     next to `also_prerequisite`);
   - a dry-run of the fold against the vault, which should report case 1
     only.
3. **nav**:
   - `planTieChange` plus its JS vectors;
   - absorption inside the forward and Blocks writers;
   - tie badges, the `⇄` badge, and the tie sections in all four stages;
   - the strip in the Depends on stage;
   - ⌃B / ⌃⇧B / ⌃L;
   - notices;
   - replace the "linking stays inert" tooltip;
   - `npm run build`, tests, then `bob plugins sync`.
4. **mac**: render the new capsules. Watch the exact-SHA macOS CI run.

Minimum viable cut, if the epic has to shrink: phase 2's reconcile fold
plus phase 3's ⌃B / ⌃⇧B / ⌃L with badges and strip. Capture and Mac can
follow.

## 9. Recommended solution

**Adopt the rule "a dependency absorbs a plain link; only an explicit tie
gesture releases it", enforced at the pair level in both directions.**

1. **Invariant (PT0).** In writable notes, if a dependency joins two tasks
   either way, neither task holds a plain (unlabelled) link to the other.
   Labelled relations always coexist.
2. **Absorb everywhere.** Every writer that adds a dependency (the Depends
   on and Blocks stages, ⌃B / ⌃⇧B, capture `&` / `*`) removes the pair's
   plain links in the same gesture. `bob task reconcile` folds any
   remaining ones, never touching read-only history.
3. **Release only on purpose.** Only the Obsidian stages turn a dependency
   into a plain link: ↵ on a `⇄` row in Links or Linked from, or ⌃L in
   Depends on or Blocks. The consequence ("Ready again") is shown in the
   strip before the key is pressed. Capture's plain `~` and hand edits
   never release a dependency; they leave it in place and say so.
4. **One key grammar in all four stages:**
   - **⌃B** = this task waits on it
   - **⌃⇧B** = it waits on this task
   - **⌃L** = plain link
   - ↵ keeps its toggle meaning and converts when the pair has the other
     kind.
5. **Visible ties:**
   - a tie badge on every row (`⛓ prerequisite`, `🧱 dependent`,
     `🪢 linked`, `🪢 links here`);
   - a `⇄` action badge whenever ↵ converts;
   - an empty-filter section listing the other kind (`TIED BY A
     DEPENDENCY` / `PLAIN LINKS`);
   - subtitle counts;
   - a consequence strip in every relationship stage;
   - notices that name what was replaced.
6. **Reliability:**
   - same-task conversions are one transaction and one Ctrl+Z;
   - cross-task conversions write the dependency side first through the
     existing guarded writers, and the link side second, best effort;
   - reconcile turns any partial outcome into a valid state;
   - Rust and JS share a single planner pinned by PT vectors.

In case 1, this turns Bryan's 19-second, two-stage correction into one
keystroke (⌃⇧B) with nothing left over. In case 2, he would have seen
`🧱 dependent` on the row before adding the redundant link.

---

### Sources

- bob-cli: `docs/task-relations.md` (§§1–10, 13, LK8, LR18, LX13, LG1–LG29,
  M7 in §19); `docs/task-dependencies.md` (§§6–8, 15.4–15.7);
  `docs/capture.md` (relation and dependency completion);
  `docs/reference/mac-capture/relationship-pickers.md`;
  `src/native/task_status_hooks/{mod.rs,relations.rs}`;
  `src/native/capture_complete/candidates.rs`.
- bob-plugins `bob-navigation-hotkeys/src`: `300-dependency-stage.js`,
  `304-relation-stage-view.js`, `305-relation-stage-copy.js`,
  `410-picker-filter-and-render.js`, `426-picker-relation-stage.js`,
  `450-picker-keydown.js`, `425-picker-blocks-stage.js`.
- SASE memory: `decisions:task-deps-are-depends-on-links`,
  `decisions:capture-link-drops-blocking-deps`,
  `decisions:relation-equals-alias-and-flips`; glossary Task Relation, Task
  Dependency Link, Task Link, Task Mention.
- Vault: a read-only scan of `~/bob` and git history for `bob.md`
  (`af8c9abe3`, `6792ee7c6`) and `cash.md` (`776478944`, `fc4668dc8`).
- External: [Linear docs: issue relations](https://linear.app/docs/issue-relations)
  (search snippet only; the page returned 404 to my fetch);
  [Atlassian: configuring issue linking](https://confluence.atlassian.com/adminjiraserver/configuring-issue-linking-938847862.html).

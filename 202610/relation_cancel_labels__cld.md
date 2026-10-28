# Cancel labels: relation labels that cancel their source task

*Researcher `cld` · 2026-10-28 · bob-cli, bob-plugins, bob-mac-capture, chezmoi*

> **Question.** Bryan wants certain configured relation labels, starting with `duplicate of` and
> `superseded by`, to cancel the source task automatically. The UI should say clearly when a
> label will cancel, and today's Task Links to the cancelled task should be removed the same
> way every other cancel removes them. Is this a good idea, what should change in the
> requirements, and how should it be built?

## Bottom line

**Build it, as a compound gesture rather than a property of the relation.** The vault shows
that this is something Bryan already does by hand. Each of the three relations in the vault
that use these labels sits on a task he cancelled himself, either in the same sync window or
16 seconds later. No Cancel Log was written, and the cancel pruned the task's link from that
day's open Pomodoro. The feature should write **exactly those bytes, in one gesture instead
of two**.

The design hinges on one rule:

> **When an authoring gesture leaves a cancel-label entry on an open source task, the same
> gesture cancels that source, exactly as the Task Card's Cancel does. Nothing else ever
> cancels because of a label, and nothing ever reopens because of one.**

This rule triggers once, at the moment of the gesture. It is never a state that something
keeps re-checking. Relations as data stay inert: reconcile, chips, mirrors, renames, hand
edits, sync, and config changes never touch a status. Only the gesture does two things,
and it says so before it commits. This is what keeps the feature compatible with the
inertness contract that relations shipped with.

The feature needs these pieces:

- `relations.cancel_labels: [duplicate of, superseded by]` in the chezmoi-managed
  `~/.config/bob/config.yml`. bob's built-in default is the empty list, so shipped behavior
  does not change for anyone else.
- A Rust cancel engine in bob-cli, used by capture `~` / `~~`.
- Composition of the existing nav cancel planner into the Obsidian relation writer.
- A consistent **⊘ cue** on every surface that names *which* task will be cancelled, plus
  a Return key whose label changes to **↩ link & cancel**.

The cue uses ⊘, the Cancelled glyph bob already uses. It never uses red or strikethrough.

I would change six things in the request. They are listed in
[Requirement adjustments](#requirement-adjustments). The two most important:

- **Prune scope.** Remove links from *today's open Pomodoros* only, not from every part of
  today's note.
- **Dependents.** Use the standard recovery path. Do not move dependents onto the new
  task. A real vault case shows that moving them would have created a dependency cycle.

---

## 1. What exists today

### 1.1 Relations are contractually inert

`docs/task-relations.md` is the relation contract. Rust and JavaScript both cite it.

- **§2 "What relations never do":** a relation write never "changes a status, lane, …
  schedule, priority"; never "counts as a review answer, advances the `]s` walk"; never
  "disappear[s] because either end closes, is cancelled, reopens". It ends with: "A link
  that needs to block is a dependency."
- **§8 Immediate writers:** the row "Closes, cancels, reopens → None".
- **§13.2 Inertness (LR18, LX13, LG13):** "Adding, removing, or relabelling any relation
  leaves every status … byte-identical, apart from a minted `^id`."
- **§16 RV1:** "Never use 'description' in code or contracts: bob already uses it for task
  text." The request's "relation descriptions" should therefore be called **relation
  labels** (here, **cancel labels**).
- **Prior research verdict** (`research:202610/task_relation_links/task_relation_links.md`):
  "It is a good idea, **provided it stays inert and single-sourced.** The danger is … a
  feature that slowly acquires behaviour: links that promote, block, **close**, or get
  consumed."

So this request crosses a line the relations design drew on purpose. That is not a reason
to refuse it, but the crossing has to be narrow and explicit. Section 4 explains how.

### 1.2 Cancelling a task is already a well-defined gesture

`docs/projects.md` ("Cancelling a task") describes the cancel action. It is implemented in
bob-plugins as the nav Task Card Cancel (`x`) action:
`applyTaskCancelFromPicker` (`src/540-plugin-decay-picker-and-cancel.js:661`) →
`planTaskCancelBatch` (`src/240-cancel-and-lanes.js`).

- It writes `[-]` and upserts `[cancelled:: YYYY-MM-DD]` before the trailing `^id`. Nothing
  else on the task line changes.
- A non-empty reason goes into a first-child `❌ **CANCEL LOG**` entry
  (`*date* — reason`). **An empty reason writes no log**, unless a log already exists; then
  it writes `🤷 no reason given`, because "a kept history has no gaps".
- **It prunes Task Links from today's *open* Pomodoros.** A bullet that holds only the link
  is removed with its subtree. Otherwise only the link token is removed. `bob task
  reconcile` "stays authoritative for the same rule" (`docs/task-status-hooks.md`
  "Canceled Task References").
- It then calls `api.recoverBlockedDependents`. A cancelled close recovers dependents but
  **never makes successor offers** (`docs/task-dependencies.md`: "cancelled close (cycler)
  → recover only; never offer").
- It refuses recurring tasks ("cancel those with Obsidian Tasks"). It is one editor undo
  step.
- Its preview already names the effects: `Removes its links from today's open Pomodoros ·
  unblocks dependents` (`src/380-picker-cancel-and-lane.js`).

**bob-cli has no general cancel writer.** The only Rust writers of `[cancelled::]` are the
reference-task close paths (`ref_tasks/line.rs`, `highlights_ref/note.rs`). Capture can
complete a task (`!`), using the shared `task_complete` engine: tree close, scoped ledger
retirement, and dependent recovery. It cannot cancel one.

### 1.3 Where relation labels are chosen

| Surface | Code | What it shows today |
| --- | --- | --- |
| Bob Mac Capture relation card (`~note:id\|…`) | `CapturePanelView.swift` ≈1933 (sentence), ≈2147 (inserts/warning lines), ≈2226 (rows) | Sentence `Source (label) → Target`. Rows show `⇄ inverse` and `N links`. An orange one-off warning line. |
| bob `capture-complete` `relation_label` | `capture_complete/candidates.rs:1595`, `model.rs:229` | Rows `{label, key, inverse, count, replacement, hide_replacement, typed, disabled_reason, existing, hidden}`. No owner or direction information. |
| Obsidian Task Card `l` / `⇧L`, then ⇧↵ label stage | `426-picker-relation-stage.js:624–925` | Live sentence `S — ‹label› → T`, `used N×` meta, a consequence strip, and Ctrl+D hide. |
| Hand edit of a LINKS line | nav hand-edit mirror | Mirrored when the cursor leaves the line. |
| `bob relations rename` | `relation_labels/rename.rs` | Rewrites label spans vault-wide. |

**Config.** `src/native/config/relations.rs` reads only `relations.linked_from_lines` and
ignores unknown keys, so adding a new key is safe. nav reads the same file with an
mtime-cached loader (`020-config-load-and-tasks.js:55`). On mobile the Task Card already
has no config (`BULLET_PROPERTY_CONFIG_MOBILE_NOTICE`), so `config.yml` reaches every
surface where the gesture exists. Bryan's chezmoi `home/dot_config/bob/config.yml` has no
`relations:` block today.

---

## 2. Evidence from the vault: Bryan already does this by hand

`bob relations list -a` reports 7 labels and 24 links. `superseded by` has 2 links and
`duplicate of` has 1. I traced all three in vault git:

| Source (S) → target (T) | Commits | What happened |
| --- | --- | --- |
| `cash.md` "Sell stocks!" **duplicate of** "Sell stocks now!" | `f85bcfff` 2026-10-22 **07:27:06** (relation, 2 files: S plus T's mirror), then `8d0ddbcc` **07:27:22** (cancel) | Linked, then cancelled **16 seconds later**. S had a P1 `scheduled:: 2026-10-22` and the edit came at 07:27, so this was most likely a morning-review answer. No Cancel Log. Not linked today, so nothing was pruned. Note that the *older* task was marked as the duplicate of the newer one. |
| `sase_blog.md` "Write introduction" **duplicate of → relabelled superseded by** "Intro v1" | `8aa12ea4` 2026-10-26 16:25:35 | Relation and cancel landed in one sync window. `[-]` plus `[cancelled::]`, no Cancel Log. **Its link was pruned from the daily note's Pomodoro.** Dependent `^v1-draft` recovered `[?]` → `[ ]`. It was later relabelled from one cancel label to the other. |
| `sase_blog.md` "Flesh out tasks…" **superseded by** "Wave review" (`^review-tasks`) | `08bc4a2e` 2026-10-26 16:29:47 | S was Next `[*]` and linked under the *running* 1610–1635 WRITE Pomodoro **next to T**. The cancel removed S's link and left T's. No Cancel Log. |

What this shows:

1. **Demand is real but small.** There were three uses in about a week, all followed by a
   manual cancel. Size the feature accordingly: one config list and one rule, not a
   relation-effects engine.
2. **The bytes are already settled:** `[-]`, `[cancelled:: date]`, the LINKS line, **no
   Cancel Log**, and a prune of today's open Pomodoro link. The feature should reproduce
   them exactly.
3. **Direction matters, and it is not "newer is the duplicate".** Bryan cancels whichever
   task is worse. The UI must name the task it will cancel.
4. **Moving dependents would have been wrong.** "Write introduction" BLOCKED `^v1-draft`,
   and the replacement `^intro-v1` *depends on* `^v1-draft`, because the intro is now
   written last. Re-pointing `v1-draft → intro-v1` would have created a **cycle**. Bryan
   re-pointed dependents himself (`^w1-review` literally says "re-point ^v1-draft").
   Standard recovery was correct. `v1-draft` had no `[fresh::]`, so it resurfaced as NEW
   under UB2 instead of getting `[unblocked::]`.
5. **Relabelling from one cancel label to another happens**, so it must be a no-op once the
   task is already cancelled.
6. **Today, no open task carries either label.** All three sources are `[-]`, so turning on
   the config needs no retroactive migration.

## 3. Precedent

Duplicate-closes-the-issue is the industry norm. Trackers differ on which door you enter
by:

| Tool | Door | Behaviour |
| --- | --- | --- |
| **YouTrack** "Duplicates" workflow | **Link first**, configurable | "Set state to 'Duplicate' when duplicates link is added to issue". Also "**Reopen issue when all duplicates links are removed**" and "Require links to duplicate issue when state becomes 'Duplicate'". |
| **Linear** | Status first ("Mark as duplicate of", `m d`) | Moves the issue to a reserved Duplicate status (formerly a Canceled-type status), adds the relation, and moves customer requests and attachments to the original. |
| **GitHub** | Close first ("Close as duplicate", `gh issue close --duplicate-of`) | Close reason `duplicate` plus a "marked as duplicate" timeline event linking the original. |
| **Google Issue Tracker** | Status first | Duplicate status closes the issue, and its CC list moves to the canonical issue. |

Bob's request takes YouTrack's door: the link drives the state. I keep that, with two
deliberate departures:

- **No reopen-on-unlink.** That rule turns the relation back into a continuously enforced
  state, which section 4 rejects.
- **No context or dependency transfer.** Linear moves context to the original; section 2
  shows that a structural transfer would have produced a cycle in Bryan's vault.

The GitHub and Linear status-first door is still a good *second* way in. Phase 2 adds it
to the Task Card's Cancel stage.

---

## 4. Critique: is this a good idea?

**Yes, with conditions.** It removes a two-step habit, closes the window where the
duplicate is linked but not yet cancelled, and puts the Pomodoro prune and dependent
recovery on the same reliable path every cancel uses. The risks are real and need to be
designed out explicitly.

| Risk | Why it matters | Answer in this design |
| --- | --- | --- |
| **Semantic creep** (the explicit warning in the relations research) | Every recent decision record exists because authored and derived state got tangled. | The cancel happens once, at the authoring gesture. The relation stays data. A new decision record and an amended §2 state the one carve-out and list everything that still never cancels. |
| **Continuous enforcement** (reconcile cancels any open task with a cancel label) | It would mass-cancel when the config lands. It would re-cancel a deliberately reopened duplicate forever. Hand edits and agent edits would close tasks silently. | Rejected. Reconcile, rename, hand edits, mirrors, and config changes never cancel. Reopening is the escape hatch, and it stays reopened. |
| **Surprise cancels** | A label choice is low-stakes, but closing a task is not. | Every surface names the task before commit: ⊘ "Cancels '…'", and Return's label changes to **↩ link & cancel**. The capture dry-run lists the full consequences. |
| **Wrong-direction cancels** | `~~` and ⇧L make the *picked* task the source. | The cue always names the task. It never says just "cancels source". |
| **False unblocks of dependents** | A duplicate's dependents recover even though the real work in T is not done. | This is the standard cancel behavior. The preview lists who unblocks, and recovered Ready tasks resurface in review (UB1) or as NEW (UB2). Auto-transfer is rejected using the cycle evidence. |
| **Engine drift** (Rust, JS, and Swift each deciding) | Two engines already implement relations. A third rule could diverge. | bob owns capture, and Swift only renders bob's flags and strings, per `mac-capture-is-a-thin-client`. Rust and nav share one byte-level vector table for the cancel write. |
| **Old client, new config** | An old Mac app would commit a cancel without showing the cue. | Rollout gate: the chezmoi config lands **last**, after bob, nav, and the Mac app all ship the cue. bob's CLI output always shows it. |

**What I would not do:**

- Build a general "relation effects" system (complete, block, promote, …).
- Let reconcile enforce the rule.
- Move dependencies.
- Add a per-gesture opt-out key.

The last one is unnecessary: reopening is the opt-out, and none of the precedent tools
offers one.

---

## Requirement adjustments

| # | As requested | Adjusted to | Why |
| --- | --- | --- | --- |
| A1 **[RENAMED]** | "relation descriptions" | **Cancel labels**, the relation labels listed in `relations.cancel_labels` | RV1 forbids "description" in contracts. "Cancel label" reads naturally in UI, docs, and code. |
| A2 **[KEPT]** | Configure `duplicate of` and `superseded by` in chezmoi | `relations.cancel_labels` in `home/dot_config/bob/config.yml`. bob's default is `[]`. | Matches `linked_from_lines` and reaches every surface where the gesture exists. A vault-journal home was considered and rejected (§8). Consider adding `merged into`; it is already in the inverse table. |
| A3 **[ADDED]** | (unstated) when it fires | **Only at the authoring gesture**: capture `~` / `~~`, the Links and Linked-from stages (add *and* relabel), and counted batches. **Never** reconcile, `relations rename`, hand edits, agent edits, chip ×, mirrors, sync, or config changes. **Never reopens.** | This keeps relations inert as data and avoids every risk of continuous enforcement. It is also the rule that makes the 16-second habit a single action. |
| A4 **[ADDED]** | (unstated) which task | **Always the source**, the side the label is phrased from ("S duplicate of T" cancels S). The cue names that task. With `~~` or ⇧L, that is the *picked* task. | Labels are phrased from S's side (§3.2). Bryan's own usage cancels the older task as often as the newer one. |
| A5 **[ADJUSTED]** | "remove any task links in the current daily file that point to the canceled task" | Remove links under **today's open Pomodoros only**, with the existing dedicated-bullet and token semantics. Links under closed Pomodoros, links elsewhere in the note, and previous days stay. Reconcile remains the backstop. | This is what "handle this case just like other cases where we cancel tasks" means in practice: it is the Task Card and reconcile rule. Closed Pomodoros record work that actually happened. |
| A6 **[ADDED]** | (unstated) Cancel Log | **No new Cancel Log.** The LINKS entry is the reason. If S already keeps a log, prepend `*date* — 🪢 duplicate of [[…]]` so the history has no gaps. | These are exactly Bryan's hand-made bytes, with one fact in one place. A log line would repeat the LINKS line directly above it. |
| A7 **[ADDED]** | (unstated) dependents | Standard cancel recovery: `recoverBlockedDependents` / `recover_blocked_dependents`, `[unblocked::]` per UB1, **no successor offers, no dependency transfer**. The preview names who unblocks. | Consistent with every other cancel. Transfer would have created a cycle in the vault. |
| A8 **[ADDED]** | (unstated) refusals | Refuse a cancel label whose source is a task **being created by this capture**, with a hint to use `~~`. Refuse an item that would both cancel and link, start, or complete the same task. Recurring source: write the link, **skip the cancel**, and warn before commit. | Creating an already-cancelled task is clutter, and the `~~` flip expresses the real intent. Recurring tasks keep the Task Card rule. |
| A9 **[ADDED]** | (unstated) review walk | A cancelling commit on the `]s`-landed row counts as a resolving Task Card commit and **advances once**. Its stats outcome is `cancel`. | Follows `answering-advances-the-walk`. The `cash.md` case was most likely a morning-review answer. |
| A10 **[ADDED]** | "clear indication" | One ⊘ vocabulary everywhere: a row capsule, a dimmed ⊘ source in the sentence, a consequence line naming the task, Return relabelled **↩ link & cancel**, a draft-span tint, preview and notification rows, plus `bob relations list` and zsh. | Bob already uses ⊘ for Cancelled in `vault-format.md` and `date-marks.md`. Bob never strikes closed items through and keeps red for errors. |

---

## 5. Design

### 5.1 Config (chezmoi)

```yaml
# Task relations (docs/task-relations.md in bob-cli).
relations:
  # linked_from_lines: true   # write 🪢 LINKED FROM mirrors (default)
  # Linking a task with one of these relation labels also cancels it: the
  # source, the task the label is phrased from ("S duplicate of T" cancels S).
  # Matched case-insensitively. The default (empty) cancels nothing.
  cancel_labels:
    - duplicate of
    - superseded by
    # - merged into
```

- **Matching** uses `relation_label_key` (trim, collapse whitespace, strip a trailing `:`,
  lowercase), the same function used by the catalog, journal, and rename.
- **Validation fails closed.** A value that is not a list, or an entry that breaks the
  label rules, produces a warning (`invalid relations.cancel_labels …`) and is skipped.
  Errors never disable `linked_from_lines`, and **a config error can only cause fewer
  cancels, never more**.
- **A hidden or `||` one-off cancel label still cancels.** Hiding affects suggestions only
  (`relation-label-hide-is-suggestions-only`).

### 5.2 Which task is cancelled

| Gesture | Source S (cancelled) | Target T |
| --- | --- | --- |
| Capture `@note+id ~t:id\|"duplicate of"` | the existing owner | the picked task |
| Capture `New task ~~old:id\|"superseded by"` | **the picked existing task** | the new task. This is the elegant "capture the replacement and retire the old one" draft. |
| Capture `New task ~old:id\|"duplicate of"` | the new task | refused with a teaching message (A8) |
| Task Card `l` (Links to), then ⇧↵ label | the task under the cursor | the picked task |
| Task Card `⇧L` (Linked from), then ⇧↵ label | **the picked task** | the task under the cursor |
| Counted `N<Ctrl+Shift+L>` | each selected source | one target |

### 5.3 What a relation-cancel writes

The writes happen in one gesture, in this order. Each step is the existing cancel
behavior.

1. **S's note, one write:** the LINKS edit (add or relabel), then on S's task line `[-]`
   plus an upserted `[cancelled:: today]` before the trailing `^id`. Cancel Log only per
   A6. Because the LINKS edit and the cancel are both on S, **they always land in the same
   transaction**: one Obsidian undo step, and one staged file in a capture batch.
2. **T's LINKED FROM mirror:** an unchanged courtesy write, with reconcile as the
   authority.
3. **Today's daily note:** prune links to S under open Pomodoros. In capture this happens
   in the same all-or-nothing batch. In Obsidian it is a follow-up with a `not removed`
   chip on failure. Reconcile heals both.
4. **Recovery:** Blocked dependents of S, plus residents when S is a `^prj`, recover per
   the existing engines.
5. **Feedback:** one notice or preview that names the cancel, the prune count, and who
   unblocked.

Resulting bytes for the `cash.md` case. They are identical to what Bryan wrote by hand:

```markdown
- [-] #task Sell stocks! [fresh:: 2026-10-16] [created::2026-10-12] [priority::high] [scheduled:: 2026-10-22] [cancelled:: 2026-10-22] ^sell-stocks
	- 🪢 **LINKS:** duplicate of [[dev_plex_hack_patch#^sell-stocks-now]]
```

### 5.4 Edge cases

| Situation | Behaviour |
| --- | --- |
| S is Ready, Next, In Progress, or Blocked | Cancel. |
| S is a `^prj` | Cancel. The preview says "project". `bob projects sync` maps it to `status: canceled`, and residents recover per the project rules. |
| S is already Done or Cancelled | Link only. Muted "stays Done / already Cancelled". This covers relabelling from one cancel label to another. |
| S is recurring | Link written, cancel skipped. Amber "repeats — cancel it with Obsidian Tasks" *before* commit. |
| T is Cancelled | Allowed, with an amber warning: "“T” is Cancelled too — both end closed". |
| Re-affirming an existing cancel-label edge on an open S | Cancel. The gesture is the intent, and the preview says so. |
| Relabel away from a cancel label, or remove the link | S stays Cancelled. The notice says "stays Cancelled · reopen with Alt+[". |
| An inverse label is typed (`supersedes`, `duplicated by`) | No cancel. Hint: "“supersedes” never cancels · to retire “T”, flip (`~~` / ⇧L) and use “superseded by”". |
| Hand edit of a LINKS line adds a cancel label | No cancel. A once-per-burst notice: "cancel labels cancel from the Links stage or capture · Ctrl+Shift+P x to cancel". |
| `bob relations rename` into or out of a cancel label | Never cancels. The preview warns: "“duplicate of” is a cancel label in config.yml; update `relations.cancel_labels`", or "N open sources will carry a cancel label but stay open". |
| Pruning empties an open Pomodoro | Same as other cancels. Reconcile removes childless entries. |
| Undo in Obsidian | Ctrl+Z restores LINKS and status together. The daily prune and mirror are follow-ups that undo does not restore, exactly as with Task Card cancel today. |

---

## 6. The indication, surface by surface

The visual principle: **name the task, change the verb, use ⊘, stay calm.** Cancel is a
decision, not an error, so it uses neither red nor the orange warning tint. Bob also never
strikes closed items through ("Closed titles are secondary and never struck through"), so
the cancelled side is shown *dimmed with ⊘*.

**Bob Mac Capture relation card** (`@cash+sell-stocks ~dev_plex_hack_patch:sell-stocks-now|dup`):

```text
╭─ 🪢 Link with a relation ─────────────────────────────────────────────╮
│  ⊘ Sell stocks!   ( duplicate of )  →  Sell stocks now!               │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ dup▌                                                            │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│ ▌ duplicate of        ⇄ duplicated by      ⊘ cancels   1 link    ⇥    │
│                                                                       │
│  ⊘ Cancels “Sell stocks!” · Ready → Cancelled                         │
│  ↩ link & cancel    ⌃N ⌃P move    ⌃D hide    esc back                 │
╰───────────────────────────────────────────────────────────────────────╯
```

- **Row:** a `⊘ cancels` capsule in the Cancelled-status tint, with SF Symbol
  `circle.slash`, placed before the count.
- **Sentence:** the source is dimmed and prefixed with `circle.slash`.
- **Consequence line:** sits in the slot the one-off warning uses. It shows bob's cheap
  verdict.
- **Action line:** changes from `↩ link` to `↩ link & cancel`.
- **Muted variants:** a no-op verdict ("already Cancelled") shows the capsule muted. A
  new-task source shows the rows disabled with bob's teaching reason.

**Draft and preview card (Mac) and CLI human output.** The `|"duplicate of"` label span is
tinted. Below the 🪢 row, the preview card adds:

```text
✓ captured  sase_blog.md
  - [ ] #task Intro v1 (write last) … ^intro-v1
  🪢 "Write introduction" now links here · superseded by   sase_blog.md ^write-introduction
  ⊘ cancelled "Write introduction" · Next → Cancelled · removed 1 Pomodoro link · unblocked "Finish full v1 draft of blog post"
```

A dry run says `would cancel`, `would remove`, and `would unblock`. The success
notification appends `· ⊘ cancelled “Write introduction”`.

**Obsidian label stage (Task Card `l` / `⇧L` → ⇧↵):**

```text
🪢 Link with a relation
⊘ Sell stocks! — duplicate of → Sell stocks now! · Ready → Cancelled
[ dup                                                        ]
▸ 🔗 duplicate of                 used 1× · ⊘ cancels this task
   🔗 implements                   used 10×
⊘ Cancels “Sell stocks!” · removes its links from today's open Pomodoros · unblocks dependents
↵ link & cancel   ⇥ accept   ⌃D hide   esc back
```

The stage uses the existing live sentence, the consequence strip, and the Task Card's own
cancel-effects phrasing. With ⇧L, the meta line reads `⊘ cancels “<picked task>”`. A
counted session reads `⊘ Cancels 3 tasks`. The notice becomes `🪢 Sell stocks! — duplicate
of → Sell stocks now! · ⊘ cancelled · removed 1 Pomodoro link`.

**Catalog and shell.** In this listing, `duplicate of` and `superseded by` carry the
`⊘ cancels source` marker; the other labels do not:

```text
RELATIONS  7 labels · 24 links · 2 hidden · 2 cancel
  implements                10 links
  inspired by               8 links
  superseded by             2 links     ⇄ supersedes       ⊘ cancels source
  duplicate of              1 link      ⇄ duplicated by    ⊘ cancels source
```

`-a` also lists configured cancel labels that have zero uses, so you can see the config is
active. zsh descriptions read `N links · cancels source`.

Bob-ledger-tools chips stay unchanged. The cancelled source already renders with its
dimmed Cancelled checkbox.

---

## 7. Engines and contracts

**bob-cli (Rust), first.** Under the thin-client rule, capture behavior lands here first.

- `config/relations.rs`: `cancel_labels: BTreeSet<String>` of keys, independent
  fail-closed parsing, and warnings.
- **New `task_cancel` engine** beside `task_complete`:
  - line rewrite: `[-]` plus `[cancelled::]` upsert;
  - Cancel Log prepend, used only when a log exists;
  - `retire_cancelled_links`, scoped to today's open Pomodoros and built on reconcile's
    structural planner (the canceled-reference subtree removal);
  - reuse of `recover_blocked_dependents` and `project_close::apply_recovery_writes`.
- **Shared cancel-write vectors:** a "CX" table in `docs/projects.md`, consumed by the Rust
  engine and by nav's `planTaskCancelBatch` tests, so both engines write identical bytes.
  This engine is also the groundwork for a future capture cancel gesture.
- **Capture `~` / `~~`** (`capture/relations.rs`): after `apply_one_relation`, evaluate the
  verdict and stage the cancel, prune, and recovery in the same `CaptureBatchPlanner`
  batch. Add the refusals `relation_cancels_new_task` and
  `relation_cancel_conflicts_with_owner_action`.
- **JSON, additive, `schema_version` stays 1:**
  - `capture-complete` (`relation_label`): rows gain `cancels_source: true`. The response
    gains `relation_cancel: {source: {text, locator, status}, verdict:
    cancels|already_closed|recurring|new_task, message}`. It is cheap: it resolves the
    token's source only.
  - `capture-parse`: `relations[]` entries and `relation_label` spans gain
    `cancels_source: true`.
  - `capture` / `--dry-run`, per item: `relation_cancels[]` with
    `{source, label, action: cancelled|already_closed|skipped_recurring, previous_status,
    cancel_log: none|prepended, pomodoro_links_removed, recovered[], message}`. Human
    output gets the ⊘ rows.
  - `bob relations list`: per-label `cancels_source` and `counts.cancel_labels`.
- **`relations rename`:** add the preview warnings from §5.4.

**bob-plugins (nav).**

- Add `loadRelationsCancelLabels()`, cloned from the `linked_from_lines` loader.
- Label stage: row meta, the sentence and verdict, the strip, and the Return hint.
- `applyRelationEdit`: when a source verdict is `cancels`, compose `planTaskCancelBatch`
  onto that source note's post-LINKS content **before** the single write.
- Extract the post-write half of `applyTaskCancelFromEditor` (deferred Pomodoro prune,
  `recoverBlockedDependents`, notice chips) into a shared helper.
- Report the walk outcome through `reviewWalk` capture/continue.
- Amend the writer's "never … touches Pomodoros (LG13)" comment.

**bob-mac-capture.** Decode the new fields with `decodeIfPresent` and render §6. Swift
decides nothing.

**Docs and memory.**

- `docs/task-relations.md`: a new **§17 Cancel labels** (rule, config, edge table, and
  vectors LXC, LGC, LRC). Amend §2, §8, §13.2, and §14 to point to §17. LRC must pin that
  "reconcile never cancels, even an open source with a cancel label".
- Also amend: `docs/capture.md` (the Inertness paragraph), `docs/reference/configuration.md`,
  `docs/projects.md` (cross-link and the CX table), and the Mac `relationship-pickers.md`
  and `capture-previews.md` ("Relation rows never render … status arrows" gains the ⊘
  exception).
- Memory, via `/sase_memory_write`:
  - a new decision record, roughly **"Cancel Labels Cancel Their Source At Link Time"**,
    with the rejected alternatives in §8;
  - an update to glossary `task-relation`, which currently says a relation never changes
    status;
  - a new glossary term **Cancel Label**.

---

## 8. Alternatives considered

| Alternative | Verdict |
| --- | --- |
| **Continuous enforcement** (reconcile cancels any open source with a cancel label, YouTrack-style, possibly with reopen-on-unlink) | **Rejected.** It cancels silently on hand, agent, and sync edits, fights a deliberate reopen forever, mass-applies on config change, and breaks "relations are history". |
| **Store the policy in the vault journal** (`.bob/relations/*.jsonl` `relation_label.effect`, toggled by `bob relations cancel …`) | **Rejected for now.** It would follow renames and sync per vault, but it mixes behavior policy into a suggestions journal, and Bryan asked for chezmoi. Renames are rare, and the rename preview warning covers them. Reopen this if label renames become routine. |
| **Move dependents to T** (Linear-style context move) | **Rejected.** The `^v1-draft` / `^intro-v1` case would have become a cycle, and it would silently rewrite other tasks' Depends-On lines. |
| **Always write a Cancel Log entry** | **Rejected as the default.** It duplicates the adjacent LINKS line and contradicts Bryan's three hand-made examples. It is kept only for the gap-free-history case. |
| **A per-gesture "link only, don't cancel" key** | **Rejected.** It is another key to learn for a rare case. Reopening is the opt-out, and no precedent tool has one. |
| **Labels that cancel the *target*** (`supersedes`) | **Rejected.** Two directions break "cancel labels cancel their source". The inverse hint teaches the flip instead. |
| **Allow a new-task source** (capture an already-cancelled duplicate as a record) | **Rejected.** It is clutter in the inbox. `~~` expresses the real intent. Revisit only if "it came up again" records turn out to matter. |
| **A Phase-1 opt-in prompt** ("Also cancel? y/n") | **Rejected.** It is a second decision on every use. The cue plus the Return label is the confirmation. |

---

## 9. Rollout

1. **Contract:** `docs/task-relations.md` §17, the amendments, the vectors, and the
   decision record.
2. **bob-cli:** config, `task_cancel` engine, capture, completion, parse spans, `relations
   list` and rename, zsh. It ships on the daily train, and with config absent it is inert.
3. **bob-plugins nav and bob-mac-capture in parallel:** the cue and the writer
   composition. Then `bob plugins sync`.
4. **chezmoi, last:** add `relations.cancel_labels`. Only now does anything cancel, so
   there is no window where a client cancels without showing the cue.

If Bryan wants to size this down, an **Obsidian-only MVP** is steps 1, 3 (nav only), and
4. That is where all three observed uses happened. Capture would then need a note
("cancel labels cancel from Obsidian only") until step 2 ships. I do not recommend it,
because the same label would behave differently by surface.

**Phase 2: the status-first door.** In the Task Card `x` Cancel reason stage, add rows
`⊘ Cancel as duplicate of…` and `⊘ Cancel as superseded by…` (one per configured cancel
label). Each opens the Links-to picker with that label preselected and writes the same
bytes through the same writer. This mirrors GitHub's "Close as duplicate" and Linear's
"Mark as duplicate of", and it teaches the feature at the moment Bryan thinks "cancel
this".

Also worth considering later: a Similar Tasks band action **Replace it** (`~~old:id|"superseded
by"`) on `possible_duplicate` rows.

## 10. Open questions for Bryan

1. Add `merged into` to `cancel_labels` now? It is in the inverse table but unused.
2. Confirm **no Cancel Log** by default (A6), or always log `🪢 <label> [[T]]`?
3. A new-task source: refuse with a `~~` hint (recommended), or allow capturing it already
   cancelled?
4. A recurring source: link and skip the cancel with a warning (recommended), or refuse the
   whole gesture?
5. Is the Phase 2 "Cancel as duplicate of…" door wanted?

---

## Recommended solution

1. **Rule.** When an authoring gesture leaves a **cancel-label** entry on an **open,
   non-recurring source** task, the same gesture cancels that source with the existing
   Task Card cancel semantics:
   - `[-]` plus `[cancelled:: today]`, with no new Cancel Log (the LINKS entry is the
     reason);
   - a prune of its links under **today's open Pomodoros**;
   - standard dependent recovery, with no successor offers and no dependency transfer.

   The LINKS edit and the cancel land in one write on the source's note. The rule
   triggers only at the gesture: reconcile, rename, hand edits, sync, and config changes
   never cancel, and nothing ever reopens.
2. **Config.** `relations.cancel_labels: [duplicate of, superseded by]` in chezmoi
   `home/dot_config/bob/config.yml`. It is matched by `relation_label_key`, bob defaults
   to `[]`, and parsing fails closed. The config lands **after** every client ships the
   cue.
3. **Indication.** Use ⊘ consistently and name the task on every surface: the row capsule,
   the dimmed ⊘ source in the live sentence, the consequence line, **↩ link & cancel**,
   the draft tint, preview and notification rows, `bob relations list`, and zsh. No red,
   no strikethrough. bob authors every Mac string.
4. **Guards.** Refuse a new-task source (hint: `~~`) and any item that would cancel and
   link, start, or complete the same task. Skip the cancel on recurring sources, with a
   warning. Warn when the target is Cancelled. Show the inverse-label hint. A cancel on
   the `]s` landed row advances the walk once.
5. **Build.** In bob-cli: a new `task_cancel` engine with shared CX vectors, plus capture,
   completion, parse, and list/rename work. In nav: compose `planTaskCancelBatch` into
   `applyRelationEdit` and share the post-cancel effects helper. In Mac: decode and
   render. Then write the contract §17, the decision record, and the glossary updates.
6. **Next:** the Task Card "Cancel as duplicate of…" door, and a Similar Tasks "Replace it"
   action.

---

## Sources

**Internal (read for this report):**

- bob-cli: `docs/task-relations.md` §§2, 3.2, 8, 10, 13, 14, 16 (RV1); `docs/projects.md`
  ("Cancelling a task", deferral prune); `docs/task-status-hooks.md` ("Canceled Task
  References"); `docs/freshness.md` §10b (UB1–UB6); `docs/capture.md` ("Linking tasks with
  '~' and '~~'"); `docs/reference/mac-capture/relationship-pickers.md` and
  `capture-previews.md` (Similar tasks, Relation rows); `src/native/config/relations.rs`;
  `src/native/capture/relations.rs`; `src/native/capture_complete/{candidates.rs:1595,
  model.rs:229}`; `src/native/task_complete/`.
- bob-plugins (nav): `src/020-config-load-and-tasks.js`, `src/240-cancel-and-lanes.js`,
  `src/380-picker-cancel-and-lane.js`, `src/426-picker-relation-stage.js`,
  `src/540-plugin-decay-picker-and-cancel.js:655–900`, `src/594-plugin-relation-edit.js`.
- bob-mac-capture: `Sources/BobMacCapture/CapturePanelView.swift` (relation card).
- chezmoi: `home/dot_config/bob/config.yml`.
- Vault (read-only): `bob relations list -a`; `cash.md:201–202`;
  `done/sase_blog_done.md:78–90`; commits `f85bcfff`, `8d0ddbcc`, `8aa12ea4`, `08bc4a2e`.
- Memory: `decisions:answering-advances-the-walk`, `decisions:mac-capture-is-a-thin-client`,
  glossary `task-relation`, `task-link`, `successor-offer`.
- Prior research: `research:202610/task_relation_links/task_relation_links.md`;
  `research:202610/relation_card_label_vocabulary/relation_card_label_vocabulary.md`.

**External:**

- [YouTrack — Duplicates workflow](https://www.jetbrains.com/help/youtrack/server/2025.3/workflow-duplicates.html)
- [Linear — Issue status](https://linear.app/docs/configuring-workflows) ·
  [Linear — Triage](https://linear.app/docs/triage)
- [GitHub Docs — Marking issues or pull requests as a duplicate](https://docs.github.com/en/enterprise-server@3.18/issues/tracking-your-work-with-issues/administering-issues/marking-issues-or-pull-requests-as-a-duplicate) ·
  [`gh issue close --duplicate-of`](https://manpages.opensuse.org/Tumbleweed/gh/gh-issue-close.1.en.html)
- [Google Issue Tracker — Mark a duplicate issue](https://developers.google.com/issue-tracker/concepts/related-issues)

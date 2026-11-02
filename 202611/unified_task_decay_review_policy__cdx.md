**Task decay as a deliberate review decision: two keeps, then one clear next step**

Independent research by **cdx**, 2026-11-02. This report investigates the requested design; it does not implement the feature or change personal configuration. No other report, transcript, summary, or findings from this research swarm were consulted.

**Recommendation and assessment**

This is a good improvement if decay means a recommendation made during an intentional review, with an explicit choice before anything moves. The useful idea is to periodically reconsider a commitment that has been reaffirmed repeatedly. Repeated affirmation is not proof that the task is unimportant, abandoned, or unproductive. WIP can mean waiting for someone else, and a Next task can remain valuable despite limited capacity. Keep the escape hatch generous, factual, and free of guilt.

Use one freshness-review policy across WIP, Next, and Ready priorities: allow two ordinary keeps in the current stage; on the following eligible review, recommend one step down. A decision to stay restarts that stage's allowance at zero. Every accepted review decision has an intelligible Rotten Log entry. The existing priority scheduling mechanism supplies the configured levels, date windows, and schedule writer, but must not impose a second threshold after the freshness threshold.

The screenshot exposes a real configuration-loading defect. It is not evidence that Bryan lacks a priority ladder. I reproduced the exact message in the current source and identified why existing tests miss it.

**Evidence and scope**

I inspected these checkouts through audited SASE repository opens:

| Repository | Revision inspected | Relevant material |
| --- | --- | --- |
| bob-cli | `5fffb82ab7e3dd3ed87c57d72fcc27f207f9c019` | Rust freshness configuration, evaluator, placement, CLI JSON, log projections, status hooks, freshness docs and tests |
| bob-plugins | `93d3859988d3ebf6e03935bd8c541149f5f2f1a4` | Navigation Hotkeys configuration loading, decay planner/card, refresh handlers, logging, lane writers; Ledger Tools counting and eligibility; focused tests |
| chezmoi / dotfiles | `3873ee30315826bc9845b7dc87f5587c6df22a02` | `home/dot_config/bob/config.yml` |

I viewed the supplied `/home/bryan/tmp/screenshots/20261102_134505.png` and read the relevant glossary and decisions using `sase memory read`. I did not inspect the live Mac process or its installed plugin versions. The defect below is reproduced from the inspected source and matches the screenshot; a Mac smoke test remains necessary after implementation.

**What Bob does today**

| Area | Current behavior | Consequence for this request |
| --- | --- | --- |
| Ready freshness decay | `freshness.decay.keeps` defaults to 3; an eligible review at or above that stored count opens the card | Setting 2 allows two keeps, then asks on the third eligible review |
| Counted keeps | Exact due Ready ROTTEN or scheduled TICKLER rows; a valid earlier freshness stamp is required | WIP and Next require changes to both Rust and JavaScript eligibility |
| Next refresh | Optional Rotten Log reason, including early refreshes; blank writes no entry; no counted increment | Both counting and blank-reason semantics must change |
| WIP refresh | Optional Work Log summary | Replace this prompt only in freshness flows, including batch and Task Link refreshes |
| At-limit Keep | Increments again; the following due review asks again | It does not currently restart the allowance |
| Priority roll decay | Separate Schedule Log roll streak; default same-level allowance is 1 | This is not the Ready keep streak, and is not currently explicitly set to 2 |
| Freshness card at a configured priority | Delegates to the priority roll recommender | It can recommend another roll at the same priority after the keep threshold |
| No-priority entry | Interval-aware unless `freshness.decay.enter` is set | An explicit `P1` makes Bryan's policy predictable |
| Last priority | Freshness card substitutes a same-level roll for cancellation; separate scheduling recommendation can cancel | Preserve the freshness card's protection against Enter cancelling a task |

These findings come from the configuration parser, decay planner, keep helper, and log writer, not assumptions based on UI labels. [S1–S6]

Bryan's actual chezmoi source defines P1 `high` at 3–8 days, P2 `medium` at 9–31, P3 `low` at 32–100, and P4 `lowest` at 101–365. `freshness.interval` is 3, `pending_interval` is 1, and `next_interval` is 2. Neither freshness decay nor priority roll decay is explicitly configured; the latter's commented example is `rolls: 1`. The comment on `next_interval: 2` says daily and should be corrected when editing this block. [S7]

**The missing-ladder bug: cause, reproduction, and fix**

`buildFreshnessDecayCardCtx`, `revalidateFreshnessDecayCard`, `resolveFreshnessDecayCardLevel`, and `applyFreshnessDecayCardDeferral` use `findFreshnessDecayPriorityProperty(this.config)`. That finder expects a normalized object's `properties` array. However, the plugin lifecycle does not assign `this.config`. The assignment found in production source belongs to the separate property-picker class. Ordinary property-picker entry points call `loadBulletPropertyConfig()` and pass the result locally. The decay route does not. [S2, S8]

The handler test fixture assigns `plugin.config = decayConfig()`. That artificial initialization makes tests pass while concealing the production gap. I executed the existing fixture setup without changing any tracked file, replaced its configuration with the normalized actual chezmoi source, then compared retaining and deleting that assignment:

```text
Actual source configuration:
  validConfig: true
  levels: [P1, P2, P3, P4]
  priorityDecay: {enabled: true, rolls: 1}
  freshnessDecayConfigured: null

Fixture with actual config injected:
  Not now available: true; selected entry: P2; writes: 0
Fixture without plugin.config:
  Not now available: false
  reason: no priority ladder is configured
  writes: 0
```

The fixture's review interval is 7, explaining its interval-aware P2 entry; that is not a claim that the pictured task would enter P2 with Bryan's 3-day interval. The decisive result is that a valid ladder becomes invisible solely because the handler lacks the config object.

I also ran these existing suites in bob-plugins: `test-navigation-decision-card-handlers.cjs`, `test-navigation-rotten-keep.cjs`, `test-ledger-tools-freshness-keeps.cjs`, and `test-navigation-refresh-modal.cjs`. All **110 tests passed**, on unchanged source. They establish a useful behavioral baseline, not that the missing-ladder path works in production.

The fix should load a normalized configuration through the existing loader when opening the review decision, retain its snapshot, and reload/revalidate it immediately before commit. Resolve the chosen level from that validated snapshot. Do not repair only the first lookup: the subsequent validation and commit paths also use the uninitialized property. Do not merely assign a startup config once, because that leaves an already-open dialog vulnerable to later configuration changes. Preserve the existing frozen date preview; never reroll the date after approval.

Add a regression test that enters through the real refresh handler with no injected `plugin.config` and a valid file-backed loader. Also cover changed, malformed, unreadable, and genuinely missing configurations. Distinguish those failures in the message; “no ladder configured” is misleading for all four. Choosing P1 is a separate policy improvement: `enter: P1` cannot repair a missing configuration object.

**Policy: a stage, an allowance, and one decision**

Use “stage” in the implementation for the current review commitment: WIP, Next, or Ready at a particular priority. WIP remains checkbox `[/]`, machine lane `pending`, and dashboard PENDING. Do not introduce a new status or rename stored values. For WIP and Next, the lane determines the stage; a dormant priority does not create additional WIP/Next allowances. On entering Ready, retain any existing priority rather than silently erasing it.

| Current stage | Two ordinary due keeps do | Default on the next eligible review | Effect after approval |
| --- | --- | --- | --- |
| WIP / `pending` | Retain WIP; count 1 then 2 | **Move to Next** | Change only the lane, stamp, log, reset count |
| Next | Retain Next; count 1 then 2 | **Move to Ready** | Change only the lane, stamp, log, reset count |
| Ready with no priority (implicit P0) | Retain Ready/P0; count 1 then 2 | **Defer to P1** | Set configured priority and previewed schedule; stamp and reset |
| Ready/P1, P2, or P3 | Retain that priority; count 1 then 2 | **Defer to the next configured level** | Advance exactly one configured level and schedule in its window |
| Ready/P4, the last configured level | Retain P4; count 1 then 2 | **Keep at P4 and restart** | Safe terminal decision; explicit reschedule or Drop remains available |

“After two keeps” must be documented as `0 → 1 → 2 → decision`, not a transition on keep number two. Opening the card is not a third keep. A limit of zero asks on the first otherwise eligible re-confirmation. Initial confirmation without a valid prior stamp establishes the baseline; it does not spend a keep.

At any transition card, **Keep in WIP / Keep in Next / Keep at P2 — restart count** is a first-class choice. It stamps freshness and resets to zero, so the next two due keeps are available again. Log the previous count and the reset; never erase history. Below the limit, ordinary Keep increments. This distinction must be visible in the copy: ordinary keeping and exceptional recommitment have different effects.

Priority windows still mean scheduling, not new checkbox statuses. A future schedule may make the task Blocked until its date arrives, and it subsequently returns for scheduled TICKLER review. State this in the preview. Never directly write “Ready” over a future date or dependency block to make the diagram look linear.

Keep the lane review tiers PENDING and NEXT. A due WIP/Next row is stale enough to warrant a Rotten Log review; it need not be reassigned the Ready-only `state: rotten` or moved into the ROTTEN walk tier. Existing clients depend on the distinction between lane, freshness state, and walk tier. [S1, S4]

**The important adjustment: do not stack two decay thresholds**

Simply configuring freshness keeps to 2 and priority rolls to 2 is insufficient. The existing freshness card calls `planPriorityRollRecommendation`, which derives a second streak from Schedule Log entries. After two freshness keeps it may roll P1 again; the same process can repeat before P2 is recommended. That contradicts the natural reading of “two keeps in each status/priority.” [S2, S5]

For Alt+F and Ctrl+Alt+F, a reached keep limit should select the next priority directly. Reuse the configured ladder, date-window calculation, and priority/schedule write planner, but bypass the Schedule Log threshold for this review action.

Keep explicit scheduling rolls distinct. Ctrl+Enter in scheduling means “reschedule this,” while Alt+F means “reaffirm this as written.” Configure explicit same-level scheduling rolls to 2 as requested, but do not reinterpret old schedule entries as freshness keeps, or make a typed scheduling reason affect a freshness counter. This is a deliberate boundary on “unify”: unify the review decision, state model, and audit presentation; do not pretend two different gestures are the same evidence. If a later requirement is that both gestures consume one shared allowance, that is a separate migration requiring explicit semantics and history conversion.

**Configuration proposal**

Add one optional field, `freshness.decay.keeps_by_lane`, alongside the existing scalar `keeps` and `enter`. Use existing machine lane names. It accepts `ready`, `pending`, and `next`, with integer values 0–999 or `false`. `false` disables that lane's transition prompt, not its review/logging. The existing whole-block `decay: false` remains the master switch; no transition occurs while disabled.

To avoid silently enabling WIP decay for other existing installations, keep the old Ready default and behavior when the new field is absent: Ready uses existing `keeps` (default 3); Pending and Next transition prompts remain disabled unless explicitly enabled in the map. A `ready` override is optional and supersedes the scalar. Counting and truthful audit can still occur with transition prompts disabled. Bryan's explicit values activate the complete policy immediately, without a calendar gate.

Merge this into the existing `home/dot_config/bob/config.yml` freshness mapping; retain its other settings:

```yaml
freshness:
  interval: 3 # Ready review cadence, in days.
  pending_interval: 1 # WIP review cadence; false disables its walk tier.
  next_interval: 2 # Next review cadence, in days.
  project_interval: 1
  decay:
    keeps: 2 # Two keeps per Ready priority; the next due review offers decay.
    keeps_by_lane:
      pending: 2 # WIP → Next; choosing to stay restarts the count.
      next: 2 # Next → Ready; choosing to stay restarts the count.
    enter: P1 # Unprioritized Ready tasks enter the configured ladder at P1.
```

Inside the existing `properties` entry whose `name` and `values` are `priority`, replace the commented decay example with:

```yaml
    decay:
      rolls: 2 # Explicit scheduling: two same-level rolls before the next level.
```

Retain all existing levels and date windows. No per-level override is necessary when all levels share two rolls. The existing level-level `rolls` option remains available. P1 should be explicit in Bryan's configuration, not a fabricated hard-coded fallback when a ladder cannot be loaded. Other users may have different level labels or order. Reject an `enter` label absent from the loaded ladder.

Keep configuration validation symmetrical in Rust and JavaScript, including 0, false, unknown lane names, null, negative/fractional values, and oversized counts. Do not silently coerce invalid values into an aggressive transition. Render the effective limit in the card so the config is observable.

**Counting and eligibility: reliability before cleverness**

Retain one current-stage counter, not separate permanent counters for every status ever visited. Extend `[keeps:: N]` with a small stage discriminator, proposed spelling `[keep_stage:: pending]`, `[keep_stage:: next]`, `[keep_stage:: ready]`, or `[keep_stage:: ready/high]`. Use the canonical configured priority value (`high`), not the changeable display label (`P1`). Omit both fields at zero.

The extra field is justified because the vault is directly editable. A naked count cannot reliably say whether two keeps occurred before a hand-edited lane/priority change. When the stored stage does not match the task's current stage, its effective count is zero; canonicalize the pair on the next human review. Do not infer the stage from prose history. Old valid `[keeps::]` on a Ready task may be adopted into its current Ready stage on the first new write; do not adopt old counts into newly enabled WIP/Next stages. Do not backfill Next counts from reasons that were historically optional.

Place the discriminator with freshness metadata, before the trailing Tasks fields. Update all relevant Rust/JS field placement, cleaning, and parser fixtures. Bob's parsers stop scanning Tasks fields when an unknown suffix field intervenes; a careless new field could hide scheduled dates, IDs, or dependencies. This is an implementation requirement, not optional polish. [S4]

Count only an exact, live, eligible due review, once per local review day. Preserve the current pre-write identity checks and valid earlier-stamp guard. Extend the eligible lane/tier pairs to WIP/PENDING and Next/NEXT. Preserve the exclusions for NEW baseline confirmations, early reviews, Today-linked tasks, recurring tasks, PRE/POST checklists, PROJECTS trackers, closed tasks, hidden/out-of-scope rows, derived Blocked tasks, and recovery-only unblock ticklers. Scheduled ticklers remain eligible; unblock ticklers remain non-counting.

Early WIP/Next refreshes should still use the Rotten Log rather than Work Log, but must say “refreshed early; count unchanged,” not manufacture another due keep. An initial confirmation can say “confirmed in WIP; count 0/2.” A byte-identical same-day repeat is a no-op: no extra history entry. These refinements prevent a stuck key or repeated review from consuming an allowance.

Generic supported human task edits retain their existing reset semantics; reset both counter and discriminator together. Automation must not increment or rewrite review history. If automation changes the effective stage, stage mismatch can invalidate the old count at read time without an automation-written reset entry. Closing a task preserves its history. Preserve old log text verbatim.

**A demotion must survive reconciliation**

Do not call Alt+N's toggle blindly: its WIP release goes directly to Ready and asks for a Work Log summary. Extract or extend an explicit lane-transition planner with a requested target and a `freshness-review` intent. WIP → Next must not accidentally become WIP → Ready. [S9]

The ordinary decay scope already excludes direct Today links and canonical daily-note tasks. Keep that boundary. If a task becomes Today-linked while the modal is open, invalidate the preview rather than silently removing the new commitment. This keeps the normal decay operation confined to one task note and avoids misleading promises of cross-file atomic undo.

There is another case beyond direct Today membership: status hooks promote prerequisites of linked tasks through the dependency graph. A Next task can be indirectly required today even if it has no dedicated Task Link. A Next → Ready write may therefore be immediately undone by reconciliation. Before presenting/committing a lane demotion, validate its effective destination against the authoritative dependency/ledger state. If it would be raised again, disable that transition with a specific explanation such as “Needed by today's linked task”; allow recommit/reset. Do not silently remove dependencies or lower a dependent task. The source computes `desired_statuses` from direct references plus dependency edges before applying `task_transition`. [S10]

Similarly, if a block appears during a decision, rebuild the preview. Priority deferrals must retain the existing future-schedule and dependency reconciliation behavior. Recheck the effective final lane after committing in integration tests.

**Rotten Log: a factual review history**

Every accepted ordinary keep, recommit/reset, and decay transition should produce one Rotten Log event in the same transaction as the task mutation. A typed reason augments the event; it never replaces stage and count information. Blank input produces neutral outcome text, not an accusatory placeholder. Keep the Work Log for actual work actions and the Schedule Log for schedule provenance.

Illustrative newest-first entries, showing each event's meaning rather than prescribing the final parser grammar:

```markdown
- 🥀 **ROTTEN LOG**
  - *2026-11-15* — Ready/P1 → Ready/P2 · after 2 keeps at P1 · scheduled 2026-11-29
  - *2026-11-12* — Still needed · kept at P1 2/2
  - *2026-11-09* — Ready/P0 → Ready/P1 · after 2 keeps in Ready · scheduled 2026-11-12
  - *2026-11-06* — Next → Ready · after 2 keeps in Next · count reset
  - *2026-11-04* — Keeping this commitment · kept in Next · restarted after 2 keeps; now 0/2
  - *2026-11-02* — Waiting for review · kept in WIP 2/2
  - *2026-11-01* — Still needed · kept in WIP 1/2
```

These are independent example events, not a complete chronology. Production transitions must record the actual starting stage, actual count, resulting stage, and actual previewed schedule. Reset entries distinguish renewed cycles from lifetime totals. Store the limit used at the time in the entry so later configuration changes do not rewrite the meaning of an old `2/2`.

A priority deferral creates both a Rotten Log event explaining the review decision and the existing Schedule Log event explaining its date/priority mutation, in one composed write. A Drop additionally uses the existing cancellation writer and Cancel Log. Avoid an adapter that first commits a priority change and then appends a Rotten Log in a second write: failure would leave the mutation unaudited. Refactor to compose both plans before commit.

The current Rotten Log regex recognizes only `kept N×` and `kept in Next`; adding prose is not enough. Introduce explicit event kinds in the in-memory model and parse both new and legacy formats. Update history readers, card previews, and any derived counts/projections. Legacy Ready entries often do not identify a stage or priority; display that uncertainty rather than inventing one. [S6]

Once transitions and resets live in this log, total entry count is no longer “N keeps logged.” Prefer “Review history · 8 events,” with counted keeps summarized separately by stage. Totals come from events, not from summing displayed ordinal values such as 1 and 2. The current counter remains the decision input; log counts remain descriptive history.

Ambiguous duplicate log markers or an unreadable destination must prevent the whole accepted decision from writing. The present Next shortcut permitting blank input without a log cannot survive a mandatory-audit contract. Explain the repair needed; do not stamp successfully and quietly discard the required event.

**Interaction design**

Use one compact review card with the task identity, current stage, allowance, and precise proposed effect above the actions. Reuse the existing visual language, spacing, focus styles, and history rows. Beauty here comes from removing contradictory prompts and making the next action obvious.

Below the limit, focus the optional reason input. Show “Keep in WIP · 1 of 2,” a live preview of the default or typed Rotten Log entry, and a visible submit label. At the limit, lead with the concrete transition rather than “Not now.” Keep the optional reason within this same card, avoiding a second dialog for every transition. With the reason field focused, letter shortcuts must type text; they must not invoke Drop or Reword.

An at-limit WIP card could read:

```text
Review WIP commitment
Write migration notes · project.md
Kept in WIP 2/2 · last reviewed yesterday

[Enter] Move to Next                 Recommended
        Leave WIP; restart the keep count.
[Alt+F] Keep in WIP and restart
        Start a fresh allowance of two keeps.

Reason (optional)  __________________________
History ▸   More actions ▸
Esc cancels · Ctrl+Alt+F resumes the review walk after success
```

The proposed date must be visible on priority transitions, including the destination priority and its configured window. Show lane and priority effects separately if necessary. Move Reword, longer refresh intervals, explicit level picks, and Drop into secondary actions rather than giving six equal-weight rows. Do not offer a per-task “Less often” promise on WIP/Next while the lane cadence overrides that per-task interval.

Retain the keymap contract: Alt+F stays; Ctrl+Alt+F advances exactly once after a successful answer from an eligible review landing. Esc, failed validation, canceled nested interaction, and no-op writes do not advance. Reword should leave focus for editing, as it does today. Changing the checkbox is not permission to jump twice.

Focus must stay visibly inside the modal, Escape must close without committing, and closing should restore the originating editor focus or the deliberate next review target. Label the dialog and input; expose the preview and disabled-action explanation accessibly. These follow W3C's modal-dialog pattern. [W1] A concrete outcome preview, visible state/count, and undo apply Nielsen's visibility, consistency, user-control, and recognition principles to this specific workflow; these are design judgments, not evidence that two keeps is universally optimal. [W2]

For counted batches, use one optional reason for the eligible ordinary keeps and generate the correct stage/count suffix per task. At-limit tasks must remain untouched and visibly reported for individual decision; do not silently apply a recommended demotion to all of them. Preserve this established no-bulk-decay boundary initially. For a single Task Link target at its limit, provide a way to open the source review decision rather than trapping the user at a skip notice. Both paths must share the same eligibility, reason, and logging model.

**Implementation shape and validation**

Keep one shared review planner on the plugin side. It accepts a validated task snapshot, current local date, normalized config, exact eligibility, and explicit action, and returns the next stage, count effect, event, optional frozen schedule, and write preconditions. Modal code renders that plan and collects input. It should not contain its own counter arithmetic. Rust evaluates/reporting and Ledger Tools' JavaScript evaluator must agree through shared fixtures.

Extend the existing freshness API capability and card capability instead of pretending older plugins implement reset and lane decay. A mixed-version installation must clearly disable unsupported transitions. It must not silently execute legacy Keep (increment) when the displayed choice promises restart. Review the CLI JSON schema and display consumers when adding effective stage/limit fields. Mac Capture likely needs at least projection verification; its implementation was not inspected in this research, so no claim of zero client impact is made.

The work falls into four reviewable pieces: configuration-loading regression repair; generalized policy/config/state and fixtures; composed writes plus unified card/logging; then personal configuration, documentation, and glossary/decision updates. This is sequencing advice, not a submitted SASE implementation plan. Personal config should be enabled only once compatible CLI/plugin readers and writers exist. Build generated plugin entrypoints from fragments and deploy through `bob plugins sync`; chezmoi edits belong in its source repo and follow its apply workflow. No bob-cli version or changelog edits are needed from the implementing agent.

Minimum acceptance cases:

1. Real config loading without fixture injection finds P1–P4; missing/invalid config produces the right explanation; changing config while the card is open writes nothing.
2. WIP, Next, Ready/P0, and every configured priority each follow `0 → 1 → 2 → decision`, and a transition advances only one stage. A freshness priority transition does not consult a second roll threshold.
3. Recommit/reset produces zero, leaves status/priority/schedule unchanged, logs the previous count, and allows two subsequent keeps. An immediate repeated key adds nothing.
4. WIP and Next blank reasons always produce accurate default Rotten Log entries on accepted refreshes; no Work Log entry is added by either freshness key. Actual work/release gestures retain their Work Log behavior.
5. Initial confirmation, early reviews, Today, NEW, PROJECTS, recurrence, checklists, closed/hidden/Blocked rows, and unblock ticklers obey their documented counting rules. Scheduled ticklers still count.
6. Hand-edited stage/priority mismatch does not carry over another stage's count; legacy Ready counters migrate conservatively; old logs remain readable; no historical Next counts are invented.
7. Lane demotion survives hooks, including the indirect prerequisite case; a newly linked or blocked task invalidates the pending decision.
8. A decision makes one composed source-note transaction containing its stamp, stage/count change, and all required logs. Undo restores the complete preimage. Duplicate markers, stale child text, I/O failure, or midnight crossing leave no partial success.
9. Rust and JS agree for config overrides, limits 0/2/999, false/off, each stage, and invalid values. CRLF, quoted/indented tasks, trailing IDs/dependencies, and unrelated children survive metadata/log writes.
10. Previewed priority date equals written date; priority entry is explicit P1; no absent ladder is fabricated; P4 Enter cannot cancel. Explicit scheduling still follows its separate configured two-roll policy.
11. Alt+F stays, Ctrl+Alt+F advances once only when appropriate, and cancellation never advances. Mixed batches log per-task facts and skip at-limit decisions explicitly.
12. Keyboard and screen-reader checks cover visible focus, typing versus shortcuts, Escape, focus restoration, default action visibility, and unsupported-version messaging.

The 110 passing baseline tests above do not replace these new acceptance tests or a real Obsidian smoke test.

**Proposed glossary wording and policy updates**

Draft for the new **Task Decay** term:

> Task Decay is Bob's explicit review policy for reconsidering a task after repeated keeps in its current commitment stage. A stage is WIP, Next, or Ready at a particular priority. A counted keep confirms an eligible due task as written; after the configured allowance has been used, the next freshness review offers one step down: WIP to Next, Next to Ready, or Ready to the next configured priority and its scheduled return. Nothing changes until the user approves. Choosing to keep the same stage restarts its allowance. Keeps, transitions, and restarts are recorded in the task's Rotten Log; date changes also retain Schedule Log provenance. Decay does not run with time alone, and reaching the last priority never implicitly cancels a task. Explicit scheduling rolls have a separate allowance and do not spend freshness keeps.

This draft is deliberately more specific than “task age lowers priority.” Connect it to Task Freshness, Keep Streak, Rotten Log, and Schedule Log when publishing it. Update those definitions to describe stage-scoped counting, mandatory Next/WIP review history, and reset semantics. Work Log wording should continue to describe work performed, with freshness review explicitly separated where relevant.

Accepted decisions currently say Next keeps do not count, blank Next reasons leave no entry, Pending uses Work Log, only due Ready counts, and only release lowers sticky lanes. These become false under the requested behavior. Publish a new accepted decision and mark the old records superseded in part; do not rewrite immutable accepted bodies as if this had always been the policy. Relevant records are `rotten-keeps-use-priority-decay`, `rotten-keeps-are-logged`, `next-keeps-ask-an-optional-rotten-reason`, and `task-lanes-are-sticky`. Preserve the immediate-availability, review-walk navigation, recurring-exclusion, and unblock-tickler rules. The memory-write skill was consulted for this proposal; canonical memory was not edited by this research.

**Adjustments to the request, explicitly called out**

- Interpret “two keeps” as two completed keeps followed by a decision on the next eligible review. Make that visible rather than leaving an off-by-one ambiguity.
- Generalize decay prompts across lanes without changing WIP/Next into the Ready ROTTEN machine state or relocating their walk tiers.
- Use P1 explicitly for Bryan, while respecting a configured ladder. Fix configuration loading rather than masking the defect with invented priority defaults.
- Remove the nested priority-roll threshold from freshness decisions. Preserve explicit scheduling rolls as a distinct policy, configured to two.
- Count due reviews, not arbitrary keypresses. Log early WIP/Next confirmations truthfully without spending another keep; suppress exact same-day duplicates.
- Keep cancellation explicit at the last priority. The request does not specify a terminal transition; silently dropping a task would be a poor extension.
- Guard demotions against current Today/dependency constraints rather than automatically deleting commitments to force the requested status.
- Keep Work Log prompts on actual work and existing explicit release/unlink actions. Change the freshness keys' meaning without broadening this request into all WIP gestures.

Two keeps is a reasonable personal policy, but not an empirically established optimum. With Bryan's current cadences, a task stamped at day zero can exhaust WIP keeps on days one and two and face a Next recommendation on day three; Next permits ordinary keeps on days two and four and asks on day six. That is relatively brisk for waiting work. The visible reset choice and independent lane limits are therefore essential. No extra analytics system is necessary: the existing review history can reveal whether these prompts help decisions or merely produce frequent restarts.

**Source index**

Repository citations identify the inspected revisions, so later edits do not silently change the evidence. The code was read locally through SASE, not fetched through these links.

- **S1:** [Rust freshness config](https://github.com/bobs-org/bob-cli/blob/5fffb82ab7e3dd3ed87c57d72fcc27f207f9c019/src/native/config/freshness.rs), `DecayConfig`; [state evaluator](https://github.com/bobs-org/bob-cli/blob/5fffb82ab7e3dd3ed87c57d72fcc27f207f9c019/src/native/freshness/state.rs), `decide_for` and `evaluate_without_checklist`.
- **S2:** [Decay planner](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/050-decay-planner.js), `planFreshnessDecayCard` and `findFreshnessDecayPriorityProperty`; [handlers](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/530-plugin-freshness-refresh-and-decay.js), context/validation/deferral methods.
- **S3:** [Keep/reset handler](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/540-plugin-decay-picker-and-cancel.js), `applyFreshnessDecayCardKeep`; [Ledger Tools placement](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-ledger-tools/src/080-freshness-placement.js), `freshnessKeepLine`.
- **S4:** [Freshness contract](https://github.com/bobs-org/bob-cli/blob/5fffb82ab7e3dd3ed87c57d72fcc27f207f9c019/docs/freshness.md), keep counting, exclusions, metadata placement, Rotten Log, and review navigation.
- **S5:** [Priority roll recommender](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/040-priority-roll.js); [config normalizer](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/010-requires-and-config.js), `DEFAULT_PRIORITY_DECAY_ROLLS`, `getPriorityLevelRollLimit`, and Rotten Log regex.
- **S6:** [Rotten keep writer and prompt](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/195-rotten-keep.js), `formatRottenLogEntryText`, `planFreshStampBatchWithLogs`, `buildRottenKeepPromptModel`; log readers in `030-bullet-blocks-and-logs.js`.
- **S7:** [Personal Bob configuration](https://github.com/bbugyi200/dotfiles/blob/3873ee30315826bc9845b7dc87f5587c6df22a02/home/dot_config/bob/config.yml), properties and freshness sections.
- **S8:** [Configuration loader](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/020-config-load-and-tasks.js); lifecycle in `490-plugin-lifecycle.js`; picker assignment in `340-picker-core.js`; [test fixture](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/scripts/test-navigation-decision-card-handlers.cjs), `makePlugin` at approximately line 299.
- **S9:** [Lane transitions](https://github.com/bobs-org/bob-plugins/blob/93d3859988d3ebf6e03935bd8c541149f5f2f1a4/plugins/bob-navigation-hotkeys/src/510-plugin-link-commit-and-lane.js), release prompts, stamps, and Today cleanup; priority composed writers begin in `580-plugin-properties-and-dependency-edit.js`.
- **S10:** [Status reconciliation](https://github.com/bobs-org/bob-cli/blob/5fffb82ab7e3dd3ed87c57d72fcc27f207f9c019/src/native/task_status_hooks/sync.rs), direct/dependency desired states and `task_transition`.
- **W1:** [W3C WAI-ARIA modal dialog pattern](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/), consulted 2026-11-02 for keyboard, focus, Escape, and labeling behavior.
- **W2:** [Nielsen Norman Group: 10 usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), consulted 2026-11-02 for visibility, consistency, control, and recognition principles.

**Recommended solution**

Implement a single, explicit freshness-review policy with stage-scoped counts: two keeps, then a visible one-step transition recommendation; staying restarts the allowance. Fix configuration loading first, configure P1 entry and both personal allowances explicitly, move WIP freshness reasons to the Rotten Log, and log every accepted decision with its stage and count. Preserve lane/tier semantics, due-review exclusions, configured scheduling, safe terminal behavior, and explicit user control. This delivers the requested simplicity without hiding a second threshold, inventing progress, or letting an ordinary freshness gesture silently discard a commitment.

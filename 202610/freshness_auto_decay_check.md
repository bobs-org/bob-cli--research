# Does freshness auto-decay work?

Checked **October 10, 2026, around 15:00 UTC**, against the local Apollo vault, bob-cli, and Bob plugin source.

**The evidence supports working keep counting and decision logic. Nothing currently qualifies for a decay card.** Freshness aging makes tasks due for review; changing their priority or schedule requires your explicit approval. There is no background timer that silently demotes tasks.

**What your vault shows**

- Decay is enabled, with a threshold of **3 keeps** and a default review interval of **7 days**.
- Four open Ready tasks have `[keeps:: 1]`; none has reached 3. Three were last confirmed October 6, one October 7. None has a task/note interval override.
- The read-only queue reports **0 ROTTEN, 0 TICKLER, and 0 decisions due**. Its four current review items are NEW, which do not count toward decay.

These observations explain the absence of cards today. Stored counters are evidence that counting has occurred; they do not prove a card has appeared in the running UI.

**How it works**

1. `[fresh:: date]` records your last confirmation. An ordinary Ready task becomes ROTTEN after its review interval, or TICKLER when a scheduled date arrives after that confirmation. The interval is task `[refresh:: N]`, then note `task_refresh`, then the global default.
2. Press **Alt+F** on the source task, or **Ctrl+Alt+F** to confirm and advance. An exact, due Ready ROTTEN/TICKLER match adds one keep and stamps today. Confirming NEW tasks, reviewing Pending/Next, or refreshing early does **not** add a keep. Repeating the gesture today cannot inflate the count.
3. Reaching `[keeps:: 3]` only stamps the task. **The next time it is due**, a single refresh gesture opens the decision card without writing anything. Number-prefixed batches and Task Link refreshes skip at-limit tasks with a “needs a decision” notice; use the source task to answer.
4. Other supported human changes that stamp freshness—such as changing priority, schedule, refresh interval, or editing through capture—clear the streak. Automation does not increment or reset it. Ordinary typing is not monitored.

For a task last kept on October 6 with `keeps: 1`, the weekly sequence is **October 13 → 2; October 20 → 3; October 27 → card**, assuming it stays eligible, you review on those dates, and nothing resets its streak or moves its next review. Frequent early refreshes also postpone when it becomes due.

The card offers:

| Choice | Result |
| --- | --- |
| **Not now** | Reschedules using the existing priority roll/decay ladder. For an unprioritized task with a 7-day interval, the default entry is P2, 8–30 days away. |
| **Less often** | Lengthens the review interval; stamps and clears keeps. |
| **Reword** | Revises the task; stamps and clears keeps. |
| **Drop** | Explicitly cancels the task. |
| **Keep** | Confirms again and increments keeps; expect another question next due review. |
| **Escape** | Leaves everything unchanged. |

Not now never implicitly cancels from this card. The separate Task Card priority recommendation has its own Schedule Log roll counter and can eventually recommend cancellation. There is **no October 19 activation gate** anymore. [Freshness contract](https://github.com/bobs-org/bob-cli/blob/b0afb103c862f4a8d051f347d27f8f678f326296/docs/freshness.md#2a-keep-streaks-and-approved-decay-policy), [decision choices](https://github.com/bobs-org/bob-cli/blob/b0afb103c862f4a8d051f347d27f8f678f326296/docs/projects.md#approved-decay-decision-planner).

**Verification and next check**

All **160 focused plugin tests passed** across keep counting, the decay planner, modal behavior, real handlers with Obsidian stubs, and ledger counting/decision marks. They cover opening without writing, early calendar dates, explicit choices, stale-input guards, and batch skips. Tested bob-plugins revision: `bf1703aa691b09ddc503dea195bed7da8327196f`; suites: `test-navigation-{keep-counting,decay-planner,decision-card,decision-card-handlers}.cjs` and `test-ledger-tools-freshness-{keeps,decision-card}.cjs`. [Handler tests](https://github.com/bobs-org/bob-plugins/blob/bf1703aa691b09ddc503dea195bed7da8327196f/scripts/test-navigation-decision-card-handlers.cjs).

Read-only checks used `bob freshness list -f json`, `bob query`, and `bob plugins list`/`sync --dry-run` with the opened source repo and `--no-pull`. Navigation 2.18.0 is enabled and synced. Ledger Tools is enabled; its deployed 1.43.0 is newer than the inspected 1.42.0 source. The installed CLI emits schema 11 versus source schema 13. These are version differences, not demonstrated decay failures; no deployment or task changes were made.

**A live UI check remains:** when `bob freshness list` shows a task needing a decision, open its source line and press Alt+F once. The card should open; Escape should leave the task untouched. This investigation could not verify the plugins loaded in your active Obsidian session or on another device.

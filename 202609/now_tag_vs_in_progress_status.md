# `#now` vs `[/]`: the promise and the footprint

- **Research date:** 2026-09-29
- **Question:** If Bryan adopts the recommendations in
  [`pomodoro_closed_day_now_tag_automation.md`](pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md)
  ("the report"), how does a task tagged `#now` differ from an In Progress (`[/]`) task?
- **Evidence:** the report (§§1, 2, 4–6, 9), plus `bob-cli`'s `docs/task-status-hooks.md` and `docs/capture.md`,
  which I checked for the exact `[/]` rules.

---

## In one breath

> **`[/]` is a footprint. `#now` is a promise.**
>
> - `[/]` is a **status the tools derive from your Pomodoro ledger**. It means "I worked on this in the last day
>   or so."
> - `#now` is a **tag only you set and clear**. It means "I've committed to this for the week."
>
> The report adds `#now` so that `[/]` can go back to telling the truth.

The two don't conflict. A task can carry both:

```markdown
- [/] #task Ship card blocks [created::2026-09-22] #now [priority:: high] ^card-blocks
```

## Side by side

| | `#now` | `[/]` In Progress |
|---|---|---|
| **Kind** | A tag in the task text. It is independent of the checkbox, so it can sit on `[ ]`, `[*]` or `[/]`. | A checkbox status: the top rung of `[ ] < [*] < [/]`. |
| **Question it answers** | "What have I bet on this week?" | "What have I actually been working on?" |
| **Set by** | **You.** Type it, or capture `… #now @route^id`. Phase 1 adds a toggle command (K2). | **The tools.** An `=x` close turns a worked-on link `[ ]`/`[*]` → `[/]` and gives it a 🍅. The hooks then push `[/]` down transcluded dependencies. |
| **Cleared by** | **Only you**, at the Monday review. Untag anything with no 🍅 in 7 days that isn't one of the week's bets. | **`task-status-hooks`, automatically** (every 15 min). An area/project `[/]` resets to `[ ]` once neither today's ledger nor the previous daily links it. |
| **Lifespan** | About a week. It stays until you remove it. | About one day of grace after its last ledger link. |
| **Tie to today's ledger** | **None, by design.** Drop the link from today and the tag still keeps the task in view. | **Tight.** The status exists because of recent ledger links. |
| **Cap** | ≤ 15. The `NOW n/15` chip turns red over the cap, and Phase 1 adds a `now_cap_exceeded` warning. | None. There are about 50 today, inflated by migration. The trial's target is ≤ ~15 `[/]` + `[*]` combined. |
| **Where you see it** | New: the dash's `NOW` chip and `## NOW Tasks` section. | Existing: the dash WIP chip; each project note's `### Next & In Progress` group; the `^` capture picker. |
| **Effect on other statuses** | **None.** `#now` is never a Next source, because that would re-inflate NEXT. | It has the highest active rank, and linking a task never demotes it. |
| **Role in the roadmap** | It **is** the Now tier: Now = `#now`, Next = READY, Later = P1–P4. | Not a tier. It records activity; it isn't a plan. |

## One week, two lifetimes

```
            Mon    Tue    Wed    Thu    Fri    ···    Mon
 #now       ●━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━◆
 [/]               ●━━━━━━━━━━━━━○
                   =x     idle   reset
```

- **`#now`:** you tag the task on Monday. It stays until the next Monday review (◆) keeps it or drops it.
- **`[/]`:** a Tuesday `=x` close starts it. Wednesday's hooks still see Tuesday's link, so it holds. Nothing links
  it on Wednesday, so Thursday's first hooks run resets it to `[ ]`.
- Through all of this, **the `#now` tag keeps the task on the dash.**

## How they combine

| | **`[/]`**: worked on recently | **not `[/]`** |
|---|---|---|
| **`#now`** | 🟢 **On track.** A weekly bet that is moving. | 🟡 **Owed.** Committed but idle. Pick from these first each morning. After 7 days without a 🍅, the Monday review decides. |
| **no `#now`** | ⚪ **Drive-by.** Reactive or incidental work. Let it decay; nothing is lost. | ⚫ **Backlog or Later.** READY in its note, or deferred with P1–P4. |

## Why you need both

- **The trap today.**
  - Removing a link from the ledger demotes the task, and nothing else remembers that it mattered. So
    everything stays linked, and statuses inflate: about 50 `[/]` and 25 `[*]`.
  - At about 5 closures a day, that is roughly a 15-day queue.
  - The report calls this the *status-lock trap*.
- **`#now` separates memory from status.**
  - You can drop a link from today with Ctrl+Shift+Enter on the link line, and the task stays in NOW.
  - `[/]` is free to decay, so a falling WIP chip is a success signal, not lost work.

## Fine print

- **Decay scope.** The hooks roll back `[/]` only in notes with `type: [[area]]` or `type: [[project]]`, such
  as `sase.md` and its ~40 `[/]` tasks. A `[/]` in an ordinary note stays until you change it.
- **Deferral overrides both.**
  - `Ctrl+Shift+P` → P1–P4 sets a future `scheduled` date. That makes the task Blocked `[?]`, which replaces
    `[/]`, and hides it from the NOW section.
  - The tag itself stays on the line, so the task reappears in NOW when the date arrives. Remove `#now` when you
    defer, unless you want that.
- **Pulling a `#now` task into today.**
  - The `^` capture picker offers only `[/]` and `[*]` tasks, so a Ready `#now` task isn't listed.
  - Pull it from the dash's NOW section instead, or type the full `^route:id`. Linking makes it `[*]`, and the
    first `=x` that records work makes it `[/]`.
- **Capture spelling.** Put `#now` *before* `@route`: `Fix it #now @sase^fix-it`. After the route marker, it
  raises a `legacy_bullet_marker` diagnostic until Phase 1's C4 lands.
- **A tag, never a field.** Don't use `[roadmap:: now]`. The picker appends fields at the far right, where a
  custom field silently erases `priority` and `created` for Tasks. A tag is safe anywhere on the line.

---

## Sources

- The report:
  `202609/pomodoro_closed_day_now_tag_automation/pomodoro_closed_day_now_tag_automation.md`
  - §1: the parser test, the decay evidence and the `#now` capture test.
  - §2: the ~50 `[/]` / 25 `[*]` counts and the Little's Law queue.
  - §4: why a tag, and why `#now` is not a Next source.
  - §5.2–5.5: the Now/Next/Later homes and the weekly review.
  - §6: V2/V3 (chips and the NOW section), K2 and C4.
  - §9: decay as intended.
- `bob-cli` `docs/task-status-hooks.md`:
  - Rolling Recent Activity: the `[/]` rollback conditions.
  - The status-transition table: the `[ ] < [*] < [/]` ranking.
- `bob-cli` `docs/capture.md`:
  - the `=x` rule that turns a startable link `[ ]`/`[*]` → `[/]`;
  - the `^` active-task picker, which lists only In Progress and Next tasks;
  - In Progress is never demoted on link.

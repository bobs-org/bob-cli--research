# Why athena's CPU is pegged: 64 orphaned busy loops from a SASE agent's load test

- **Research date:** 2026-10-08. Live snapshot of athena taken 06:05–06:13 EDT.
- **Question:** Why is athena using so much CPU right now?
- **Evidence:** read-only inspection of athena over Tailscale SSH: `top`, `ps`, `/proc/<pid>/{cmdline,cwd,cgroup,environ,fd}`,
  `systemctl --user status`, a 10-second per-process CPU sample taken from `/proc/*/stat`, the Prometheus and Pushgateway
  HTTP APIs, and `sensors`. Also the spawning agent's SASE artifacts (`tool_calls.jsonl`, `done.json`, `sase.md`) and
  its muse session log (`~/.local/share/muse/sessions/2026/10/07/c46a1a72-…/session.jsonl`). Nothing on athena was changed.

---

## In one breath

> **A SASE agent started a deliberate CPU-load test yesterday afternoon and never stopped it.**
>
> - **What:** 64 `(while :; do :; done) &` subshells, one per logical CPU. They have been running since
>   **2026-10-07 16:19:02 EDT** (about 14 hours) and use **57 of athena's 64 cores**.
> - **Who:** agent **`bob-cli-5k.5`** (muse / `muse-spark-1.3-contributor`, workspace `bob-cli_12`). It was checking
>   its fix for bead **bob-cli-33** ("Tasks JS sandbox init hits the 2s expression deadline on busy hosts") under load.
> - **Why they survived:** the shell tool timed out and killed only the parent shell. The agent's cleanup `ps`
>   searches missed the loops, because their command shows as `/bin/sh` and the searches looked for `sh`. Then the
>   agent exited, and SASE never stopped the agent's systemd scope. Its CPU counter now reads **1 month 17 h**
>   (about **754 CPU-hours**).
> - **Fix now:** `ssh athena 'systemctl --user stop sase-agent-3548414-1791398576322648802.scope'`. The scope holds
>   only the 64 loops.
> - **Smaller, steady load after that:** prometheus-pushgateway is serving **671,555 stale series** (about 0.4–0.65
>   of a core, plus Prometheus ingestion). Two SASE waiting agent runners have spun for 35 hours (about 0.7 of a core
>   combined).

## What the machine looks like right now

| Metric | Value |
| --- | --- |
| CPU | AMD Ryzen Threadripper 3970X: 32 cores, 64 threads |
| Load average | **71.25 / 69.51 / 68.67** (1 / 5 / 15 min) |
| CPU split (`top`) | 10.0 us · 2.3 sy · **87.5 ni** · 0.2 id · 0.0 wa |
| Busy cores, 10 s sample | **64.2 of 64** (99.7 %) |
| Temperature | **Tctl 95.0 °C**, Tccd5 95.5 °C. 95 °C is this chip's thermal limit (Tjmax). |
| Average clock | 3,717 MHz: base clock, no boost headroom |
| Memory | 64 GB RAM, 46 GB buff/cache, **17 GB swap in use**, 46 GB available |
| Zombies | 12–18 |

Most of the CPU time is **`ni`** (low-priority, niced work). That points straight at the loops: they inherited nice
10 from the agent runner.

### Where the cores go (10-second `/proc/*/stat` sample)

| Cores | Consumer |
| ---: | --- |
| **57.33** | Orphaned busy loops in scope `sase-agent-3548414-1791398576322648802` |
| 0.74 | Two SASE waiting agent runners (`run_agent_runner.py`, pids 3901170 and 3908855) |
| 0.43 | Other long-lived processes (syncthing, tailscaled, conky, …) |
| 0.37 | `prometheus-pushgateway` |
| 0.16 | `prometheus` |
| 0.08 | Long-lived sase axe/service processes |
| 0.04 | `sase tui` (pid 2279880). It is bursty: two `top` snapshots showed it at 119–121 %. |
| ≈5 | Short-lived processes that started inside the window, mostly sase job spawns. The sampler can't attribute them. |

## The main cause: orphaned load generators

### The processes

```text
PID 1490593 … (64 of them, PIDs 1490593–1490656)
  NI 10  STAT RN  STARTED Wed Oct 7 16:19:02 2026  ELAPSED 13:46:41  TIME 11:40:22
  /bin/sh -c nproc; cat /proc/loadavg; N=$(nproc); for i in $(seq $N); do (while :; do :; done) & done;
             echo "load pids started"; sleep 5; cat /proc/loadavg
  PPID 1 (reparented to init)   PGID 1490588 (the group leader is gone)
  cwd  ~/.local/state/sase/workspaces/bobs-org/bob-cli/bob-cli_12
  fd 1,2 → pipes (the agent shell tool's capture pipes)
  cgroup /user.slice/user-1000.slice/user@1000.service/app.slice/sase-agent-3548414-1791398576322648802.scope
```

The scope is still active even though its runner (pid 3548414) is gone:

```text
● sase-agent-3548414-1791398576322648802.scope - SASE agent runner
     Active: active (running) since Wed 2026-10-07 14:42:56 EDT; 15h ago
      Tasks: 64
     Memory: 9.2M (peak: 4.6G)
        CPU: 1month 17h 54min 17.142s
```

The loops' environment identifies the agent: `SASE_AGENT_NAME=bob-cli-5k.5` and `SASE_BEAD_ID=bob-cli-5k.5`.
`CLAUDE_CODE_TOOL_USE_ID=call_01a11804fd4075849ef42e62c2b15891` names the exact tool call.

### Timeline, reconstructed from the agent's muse session log (EDT, 2026-10-07)

| Time | Event |
| --- | --- |
| 14:41:19 | `bob-cli-5k.5` launches for phase bead *"Build the Tasks JS sandbox only when a query needs it"* (epic `bob-cli-5k`). |
| 16:15–16:18 | Times `bob query --tasks "not done"` on the live vault before and after the fix. Both take about 25 s on an idle host. |
| 16:18:49 | Reasoning: *"…hydration cost may be masked on idle host. Shifting to … load-based validation of the deadline fix."* |
| **16:19:03** | Reasoning: *"Analyzing vault scan latency under CPU load…"*, then it runs the 64-loop command above. |
| 16:29:05 | The tool result is **`tool timed out`** after 602 s. The backgrounded subshells held the tool's stdout/stderr pipes open, so the tool never saw EOF. The timeout killed the leader shell (pgid 1490588) but not its process group, so the 64 children were reparented to PID 1. |
| 16:29:13 | `cat /proc/loadavg` → `79.11 72.85 47.94`. |
| 16:29:21 | Reasoning: *"Identifying and terminating runaway shell busy-loop processes…"*. It then writes *"Load is up (my loops plus a busy host — the bug's natural habitat)"* and uses the load for its comparison runs instead. |
| 16:30–16:35 | Under load, the base binary fails with `JavaScript error while initializing the Tasks JavaScript sandbox: Error: interrupted`, and the fixed binary passes (494 tasks in 30.1 s). |
| 16:35:51 | *"Cleaning up my load loops:"*. Three `ps` searches all miss the loops (details below). |
| 16:36:08 | Reasoning: *"Assessing spin loop visibility … avoiding interference with other shared-host processes."* It moves on to `cargo test` **without killing anything**. |
| 16:37 | Closes bob-cli-33 and bob-cli-5k.5. |
| 16:38:40 | Hands `just check` to a monitor turn. |
| 16:39:20 | The runner gets SIGTERM (exit 143). The scope stays up because the loops are still in it. |

### Why the cleanup missed them

The three searches the agent ran at 16:35–16:36:

1. `ps -eo pid,ppid,etime,time,args --sort=-time | head -n 15`. After about 16 minutes, each loop had about 16 minutes
   of CPU time. The top 15 by cumulative CPU time were all long-lived daemons with many hours each (prometheus,
   pushgateway, the sase TUI, …), so no loop made the list.
2. `… | grep -E "^… +(sh|bash|dash)"` expects the command to start with a bare `sh`.
3. `ps -eo pid,ppid,time,args | awk '$4=="sh" || …'` compares the first word of `args` with `sh`.

The loops' `args` field reads **`/bin/sh -c …`**, so searches 2 and 3 can never match. The simplest correct cleanup was
to kill by process group (`kill -- -<pgid>`), by PID list (`pkill -f 'while :; do :; done'`), or by cgroup.

### Why nothing else reaped them

- **The muse shell tool's timeout kills only the leader**, not the process group. The orphans keep running with PPID 1.
- **SASE does not stop an agent's transient systemd scope when the runner exits.** A scope has no main process. Its
  remaining processes keep it "active (running)" indefinitely, and nothing checks for a scope whose runner is gone but
  whose task count is still above zero. Only three `sase-agent-*` scopes exist on athena, and this one is the only one
  without a live runner.

### What the load costs

- **Every core is busy.** The loops run at nice 10, so on each CPU's run queue a nice-0 task still gets about 90 % of
  that CPU (scheduler weight 1024 vs 110). That is why the box still feels responsive. Niceness does **not** protect
  the SMT sibling, though: each of the 32 physical cores runs a loop on both hardware threads, so real work loses
  roughly half of its core's execution resources.
- **Thermals and clocks.** The CPU has sat at its 95 °C Tctl limit at base clock for about 14 hours.
- **Load-sensitive behavior.** Anything that reads load average or depends on timing deadlines now behaves as if
  athena is overloaded. That is the same condition behind bob-cli-33 and any timing-sensitive test, and other SASE
  agents and benchmark runs on athena are affected too.

## Secondary contributors (they remain after the loops are gone)

### 1. Prometheus Pushgateway is serving about 17k stale groups

- 16,990 grouping keys and **671,555 samples per scrape**. 16,830 of the groups are `job="agent_runner"`, keyed by
  `instance=<launch timestamp>` and `workflow=ace(run)-<timestamp>`. The largest families are
  `sase_agent_run_duration_seconds_bucket` (132k series) and `sase_llm_invocation_duration_seconds_bucket` (129k).
- Push timestamps run from **2020-12-26 to 2026-07-18**, and **nothing has pushed since mid-July**. All of this is
  dead data, kept across reboots in `/var/lib/prometheus/pushgateway.data` (93 MB).
- Prometheus scrapes it every 15 s (`honor_labels: true`), and **each scrape takes 5.33 s**. That costs pushgateway
  0.4–0.65 of a core whenever it is measured: 35 h 22 m of CPU since the Oct 1 boot, about 21 % of a core on average.
  It also costs Prometheus ingestion: 28 h 40 m of CPU and 3.1 GB RSS.
- **Fix:** stop `prometheus-pushgateway`, move `pushgateway.data` aside as a backup, and restart. Then make sure every
  pusher deletes its group when its job finishes. Alternatively, drop per-run `instance` labels: per-run grouping keys
  never expire.

### 2. Two SASE waiting runners have spun for 35 hours

- Pids 3901170 and 3908855 (`run_agent_runner.py gh_sase-org__sase …`) have been running since Tue Oct 6 19:05 EDT.
  They are the waiters for `sase-1h8.14` and `sase-1h8.land`. Each has used about 4 h 40 m of CPU (about 13 % of a
  core on average), and the 10 s sample measured 0.74 cores combined.
- Every phase they wait on is closed except **`sase-1h8.13`**, which is still IN_PROGRESS. The latest chat for
  `sase-1h8.13` is its plan gate, auto-answered at 2026-10-07 18:12 EDT with `approve` and `run_coder: true`. I found
  **no running scope or process for `sase-1h8.13`**, so these waiters may be waiting on a coder that isn't running.
  Worth a look in the sase TUI. Separately, a waiter that sleeps between checks shouldn't need 13 % of a core.

### 3. The sase TUI is busy and leaves zombies

- `sase tui --restart-service` (pid 2279880, in tmux since Mon Oct 5 07:04) has used 29 h of CPU in about 3 days
  (about 41 % of a core on average). It is bursty: 119–121 % in two `top` snapshots, 0.04 cores in the 10 s sample.
  RSS varied between 0.8 and 2.0 GB.
- It is the parent of **12 unreaped zombies**: 8 `sase_federation`, 2 `git`, 2 `npm prefix`, the oldest about 2 d 20 h
  old. Zombies use no CPU, but they show the TUI isn't waiting on its children.

### 4. Memory pressure (minor)

17 GB of swap is in use even though 46 GB is available. Since boot, `kcompactd0` has used 6 h 48 m of CPU and
`kswapd0` 3 h 09 m; `kcompactd0` hit 22 % in one snapshot. This is probably left over from earlier peaks; for example,
the loop scope peaked at 4.6 GB. It isn't a current driver.

### Not a driver

At about 06:01 EDT `sase service run` restarted. For a few seconds, 14 `sase axe routine run …` processes each used
about 20 % of a core during startup. That's a transient, not steady load.

## Recommendations

### Do now (the loops)

```sh
ssh athena 'systemctl --user stop sase-agent-3548414-1791398576322648802.scope'
# equivalent: ssh athena 'kill -- -1490588'   # the loops' process group
ssh athena 'sleep 60; cat /proc/loadavg; sensors | grep Tctl'   # expect load to fall toward single digits
```

The scope contains only the 64 loops (`Tasks: 64`), and its runner has already exited, so stopping it affects nothing
else.

### Do soon

1. Clear the stale Pushgateway state (see secondary contributor 1) to get back about half a core and Prometheus
   ingestion.
2. Check whether `sase-1h8.13` still has a live coder. If not, relaunch it, or cancel the two waiters.

### Prevent a repeat (SASE-side follow-ups)

1. **Stop the agent's scope when its runner finishes.** Teardown should stop the scope with `systemctl --user stop`
   or `systemctl --user kill`, at least once the runner and provider are gone. A periodic check for
   `sase-agent-*` scopes with no runner but tasks above zero would catch whatever slips through.
2. **Kill the whole process group on tool timeout.** Muse's shell tool killed only the leader. SASE can't fix muse
   directly, but the scope teardown in item 1 makes that harmless.
3. **Agent guidance.** Load generation on a shared host must have a deadline: for example
   `timeout 300 stress-ng --cpu "$(nproc)"`, or `( … ) & sleep N; kill %…` with stdout redirected so the tool returns.
   Clean up by process group, PID list, or cgroup, never by matching the command name.

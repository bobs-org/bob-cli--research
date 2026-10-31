# GKeep footer: Keep-synced count + `gkeep_inbox.md` open count — research & recommendation

Researcher: mus. Vault + `bob gkeep` tree verified in this workspace
(`src/native/gkeep/*`, `scripts/gkeep_adapter.py`, `src/native/note_tasks.rs`,
`docs/gkeep.md`, `docs/reference/plugins/bob-ledger-tools.md`).

## TL;DR / recommended solution

Ship this as **one status-bar chip with two visually distinct segments**,
backed by **two different refresh paths**, and never let the footer itself
touch the network synchronously:

```
[ ☁ 3 · 📥 5 ]   tooltip: "3 to pull from Keep (2 new · 1 revised · synced 12m ago) · 5 open in gkeep_inbox.md — click Keep to preview, click inbox to open"
```

- **Keep segment (`☁ N`)**: number of notes a `bob gkeep pull` would act on
  (**`new` + `revised` only** — see §3). Refreshed from a **local cache file**,
  at most every **15–30 min** with jitter plus on explicit user gesture.
  Never refreshed inline during render.
- **Inbox segment (`📥 M`)**: number of **open tasks in `gkeep_inbox.md`**
  (anything but done `x`/`X` or cancelled `-`, via the configured
  `TasksSettings.status_types`, not a literal `[ ]` check). Refreshed
  **synchronously from the single target file** on Obsidian vault events
  (`modify`/`create`/`delete`/`rename` of the target) — milliseconds, no
  subprocess.
- **Auth gating**: the whole chip is **hidden unless cheap local checks pass**
  (config resolves + token command yields a master token). A failed or stale
  *network* check dims the Keep segment with an explanatory tooltip instead of
  hiding the inbox segment.
- **New CLI contract**: add `bob gkeep status -f json` (cheap, documented
  below). The plugin shells to `bob` and never reimplements Keep logic in JS.
- **Phase it**: (1) inbox-only chip this week, (2) cached Keep segment behind
  manual refresh, (3) slow auto-refresh only after measuring real snapshot
  cost on the MacBook.

The rest of this note justifies each choice, critiques the original ask, and
calls out where I changed the requirements.

## 1. What was asked

1. Footer indicator showing how many notes are in Google Keep that `bob gkeep
   pull` would sync.
2. Show it only when Keep is authenticated (pull would actually work).
3. Don't hammer the Keep API or burn MacBook CPU; think hard about polling.
4. Also show the count of non-closed (`[ ]`-family, not `[x]`/`[-]`) tasks in
   `~/bob/gkeep_inbox.md`, refreshed much more often (seconds), visually
   distinct from the Keep count.
5. Lead the design: intuitive, reliable, beautiful.

## 2. Current-state findings (verified in tree)

### 2.1 Where the footer lives today

- The desktop **review footer** is owned by **bob-ledger-tools**
  (`docs/reference/plugins/bob-ledger-tools.md`): a native status-bar item
  showing nonempty walk tiers (PRE → NEW → … → POST), `–` placeholders when
  Tasks/the daily note is unready, never an error. It hides when the queue is
  empty or Tasks is unavailable. While the cursor is on a review row it shows
  the `Alt+P` roll preview in its hint slot.
- Precedents for background `bob` invocation from plugins: **Day strip** and
  the **Stats `bob-stats` block** fetch `bob stats` JSON with
  **stale-while-revalidate** caching; the **Reading Board** fetches
  `bob ref list` JSON under a bounded SWR cache; **calendar painting** runs
  `bob gcal sync -q -f json` once after the current daily note is created
  (event-driven, at most one Notice per day), not on a timer. There is no
  existing Keep footer.
- `bob-command-mode` already emits `bob-command-mode:run-finished`; ledger
  tools refreshes caches on it. The footer should listen to that event for
  `gkeep` runs rather than inventing its own bus.
- `bob-ledger-tools` facts say **Desktop only: No**, so a status-bar chip is
  expected to work on mobile too — keep the design text-only (no emoji
  dependence for meaning; see §6).

### 2.2 What `pull would sync` actually costs

- `bob gkeep list` / `pull` / `doctor` all build an `AdapterClient` that runs
  **`uv run --quiet --script <materialized gkeep_adapter.py>`**
  (`src/native/gkeep/adapter.rs`). First run materializes a pinned Python +
  pinned `gkeepapi==0.17.1` / `gpsoauth==2.0.0` — on a cold MacBook this is a
  **minutes-long, CPU- and network-heavy** operation. Warm runs still spawn
  `uv` + Python, then `connect()` does `keep.authenticate(..., sync=True)` and
  a `keep.find()` over Home (plus Archive with `--all`), then `save_state()`
  to `$CACHE/bob-cli/gkeep/state.json`.
- Default **`gkeep.timeout_secs` is 300** (`src/native/gkeep/config.rs`). The
  adapter runs in its own process group so a timeout kills the tree — proof
  the authors expect multi-minute hangs. A footer that spawns this per render
  (or per second) would pin a core, drain battery, and risk Google rate limits
  (`429 → rate_limit → "wait a few minutes"`, `scripts/gkeep_adapter.py`).
- The adapter keeps a **`state.json` cache** (`load_state`/`save_state`) that
  makes repeat syncs incremental, but `snapshot` still authenticates and syncs
  every call — there is no "peek at the count without syncing" op today.
- `doctor`'s `keep` check **is itself a snapshot** (`doctor.rs:keep_check`):
  reusing `doctor -f json` as the footer's health probe costs exactly as much
  as the thing we want to avoid polling. The `ping` op is cheap but proves
  nothing (no auth, no network).
- `token_command` defaults to `pass show gkeep/master_token` run via `sh -c`
  **with inherited stdin/stderr so `pass` can use pinentry**. Spawned from a
  background Obsidian refresh this can pop a pinentry dialog or block
  indefinitely. Any footer probe must therefore have a **short timeout** and
  treat timeout as "unknown", never as an error chip.

### 2.3 The vault side is genuinely cheap

- `-s vault` **reads no config and makes no adapter call**
  (`list.rs` header comment) — it resolves the target name (falling back to
  `gkeep_inbox.md` with no config), scans the ledger/import store/journal
  (with warnings), reads the one target file, and filters tasks with
  `is_open_status` (`!matches!(s, 'x'|'X'|'-')`). That whole path is local
  disk + one-file parse: **single-digit milliseconds** for a normal inbox.
- `Ledger::scan` walks **every `.md` in the vault** (plus markers). The footer
  must *not* pay for that: for the inbox count it only needs
  `note_tasks::scan(contents, &settings)` on the already-read target text,
  then `scan.open_tasks().count()`. `NoteTask.status_type.is_open()` already
  handles custom statuses via `TasksSettings` — strictly more correct than the
  `list.rs` char check, and the footer should use it (a custom `[/]` or `[?]`
  open state must count as open).
- The target is configurable (`gkeep.target`, vault-relative, must end in
  `.md`); the footer must resolve it the same way `list` does and handle
  **missing target** (today: dim `gkeep_inbox.md not found` line) without
  erroring the whole chip.

### 2.4 JSON already exists, but no footer-shaped endpoint exists

- `bob gkeep list -f json` emits `schema_version: 1` with per-note
  `{id, ref, kind, title, state, pinned, shared, ...}`, `clip` hints for
  URL-only notes, `fetched_at`, and the vault tasks. It is the richest source
  but also the heaviest (full snapshot + full ledger scan + library verdicts).
- There is **no lightweight** `authenticated? / how many would pull act on? /
  how old is that answer?` endpoint. The footer needs one (proposal in §5).

## 3. Critique: is this a good idea?

**Yes, with the polling and semantics fixed.** An ambient "you have Keep debt"
signal matches how the review footer already works (quiet, glanceable, hides
when clear), and Bryan triages Keep on the Mac where Obsidian is always open.
Two numbers side by side also teach the pipeline: Keep → pull → inbox → triage.

But the naive version of this feature is a bad idea, for four reasons:

1. **Stale Keep counts mislead more than no counts.** Keep changes on the
   phone; the vault changes on disk. A footer number that is 25 minutes old
   will be wrong at exactly the moment Bryan glances at it before a pull. The
   design must therefore **show its age** (tooltip + stale dimming), or users
   learn to distrust it.
2. **"Pull would sync" is ambiguous.** `plan.summary` distinguishes
   `new` / `pending` / `revised` / `pinned` / `shared` / `empty` / `archived`.
   A `pending` note archives without writing anything; `pinned`/`shared`/
   `empty` notes are skipped unless explicitly selected; `archived` notes are
   invisible without `--all`. Counting all of them inflates the chip and
   trains Bryan to ignore it. **Count only what a default `pull` would change:
   `new` + `revised`.** (Adjustment #1 — see §7.) Mention `pending` in the
   tooltip (`2 new · 1 revised · 1 pending archives silently`), never in the
   headline number.
3. **The status bar is already crowded.** The review footer, command-mode chip,
   and Pomodoro indicator compete for the same strip. A second always-on chip
   with two numbers and two icons is one element too many unless it **collapses
   to one chip, hides when both counts are zero, and never shows errors
   inline** (dim + tooltip, like the review footer does with `–`).
4. **The unofficial API is the riskiest dependency in the tree.**
   `docs/gkeep.md` is explicit: "Keep has no official read/write API …
   through the unofficial `gkeepapi` Python library." A footer that depends on
   a per-minute Keep round-trip turns every upstream breakage into a permanent
   status-bar error. The footer must degrade to **"Keep unknown" without
   touching the inbox count**, and must never auto-pull/archive (read-only
   forever — the footer proposes, `pull` disposes).

A reasonable alternative — **vault count only, plus a manual "check Keep"
button** — covers ~80% of the value with ~10% of the risk, and I recommend
shipping it first (§5, phase 1). The Keep segment earns its keep only once the
cache + backoff story below is in place.

I would not take the other obvious approaches:

- **Poll `snapshot` on an interval from the plugin.** Burns CPU/battery,
  risks 429s, blocks on pinentry, and duplicates the state cache badly.
- **Put the counts in `gkeep_inbox.md` itself.** Tempting (zero polling), but
  writing the vault from a renderer violates the marks-are-display-only
  contract every sibling feature honors, dirties Git on a timer, and fights
  Obsidian's lock-free writes (the `pull` CAS path exists precisely because
  Obsidian ignores `bob_sync.lock`).
- **One combined number.** `☁+📥 = 8` looks clean and means nothing: the two
  numbers have different staleness, different actions, and different owners
  (Keep vs vault). Keep them as two segments of one chip.

## 4. Design requirements (what "intuitive, reliable, beautiful" means here)

- **Intuitive**: the chip answers "is there Keep work?" at a glance and tells
  you what clicking does before you click (tooltip with action + age). Zero
  must mean hidden-or-check, never ambiguous with "unknown".
- **Reliable**: the inbox count is always fresh (file events); the Keep count
  is always labeled with its age and never blocks the UI; auth/network failure
  degrades the Keep segment only.
- **Beautiful**: one quiet chip, two glyph-differentiated segments, tabular
  numerals, no emoji-as-meaning, calm colors that survive light/dark themes
  and red-green color vision (shape + position, not just hue).

## 5. Recommended solution

### 5.1 New CLI contract: `bob gkeep status [-f json] [--refresh]`

Add a footer-shaped subcommand alongside `list`/`doctor` (follow
`sase/memory/cli_rules.md` before adding flags; document under `docs/gkeep.md`
and `docs/reference/json-outputs.md` per `sase/memory/docs.md`):

```bash
bob gkeep status [-b|--bob-dir DIR] [-f|--format human|json] [--refresh] [-q|--quiet]
```

Semantics:

- **Without `--refresh`**: zero network. Resolve config + token (short
  timeout, non-interactive: `pass` must not prompt — pass
  `GPG_TTY`/pinentry-loopback or fail fast as "unknown"), read the target
  file, count open tasks with `note_tasks::scan`, read the **cache file** for
  the last Keep result, and report it with its `fetched_at`. Exit 0 even when
  the cache is absent/stale — absence is data (`keep: null`), not an error.
- **With `--refresh`**: do one `snapshot` (same path as `list -s keep`),
  classify with the existing `plan` module, write the cache file, and report.
  Honor the pull lock lightly (if a `pull` holds it, return the stale cache
  with `refresh: "busy"` rather than queueing behind a minutes-long pull).
- **Cache file**: `$XDG_CACHE/bob-cli/gkeep/footer.json` (i.e.
  `bob_cli_cache_dir().join("gkeep/footer.json")`), mode `0600`, atomic
  write + fsync like `save_state`. Shape (illustrative):

```json
{
  "schema_version": 1,
  "fetched_at": "2026-10-31T15:00:00Z",
  "account": "bryanbugyi34@gmail.com",
  "actionable": 3,
  "new": 2,
  "revised": 1,
  "pending_archive": 1,
  "skipped_pinned": 0,
  "skipped_shared": 0
}
```

  Keep it in **XDG cache, not the vault**: the token, account, and poll rhythm
  are per-host; vault-synced state would flap between Mac and Linux and leak
  account metadata into Git. (`imports/` receipts stay in the vault — that
  split is intentional: shared history in Git, ephemeral counts in cache.)
- **`status -f json` output**: `{schema_version: 1, authenticated: bool,
  auth_hint?, keep: {...} | null, keep_age_secs, vault: {target, open, missing},
  }`. `authenticated: false` with `auth_hint: "run bob gkeep login"` is what
  the plugin uses to **hide the chip** (§5.3). Any `keep_error` stays a
  machine field, never a thrown error, so the plugin can dim rather than hide.

Why a new command instead of reusing `list -f json`: `list` pays for a snapshot
*and* a whole-vault ledger scan *and* library verdicts on every call. `status`
without `--refresh` pays for one file read + one cache read — the only thing
cheap enough to call from a file-event handler.

### 5.2 Refresh strategy (the "think hard" part)

| Signal | Keep segment | Inbox segment |
| --- | --- | --- |
| Obsidian vault `modify`/`create`/`delete`/`rename` on the resolved target | untouched | recompute via `status` (no `--refresh`), debounce ~500 ms |
| `bob-command-mode:run-finished` with a `gkeep` run, `pull`/`list` exit in terminal | re-read cache (no `--refresh`) | re-read |
| App start / layout-ready | re-read cache; schedule one `--refresh` after **30–60 s idle** (only if cache older than 15 min) | read once |
| Interval while workspace visible | at most **1 `--refresh` / 15 min**, jittered ±3 min, skipped when offline / metered / battery-saver; exponential backoff on `rate_limit`/`network` (15 → 30 → 60 min) | no timer needed (event-driven) |
| Click Keep segment | one `--refresh` (with spinner state on the chip), rate-limited to 1 / 60 s | — |
| `pull` running (lock held) | show `…` spinner, keep old number | live |

Additional rules:

- **No refresh when unauthenticated.** If `status` says
  `authenticated: false`, cancel timers and hide the chip. Re-check auth at
  most once per hour and on `config.yml` change — `pass` invocations are the
  scarcest resource here, not Keep calls.
- **Treat `429`/`network`/`auth` as dimming, not errors.** Keep the last good
  number, dim the segment, tooltip names the failure and the retry time. Clear
  it on the next success. Never `Notice()` from a timer; at most one Notice
  per day for a *user-initiated* refresh that fails (mirroring the gcal-sync
  precedent).
- **Cap the snapshot size.** `--refresh` uses `include_archived: false` (same
  as the default `list`) so Archive bloat never enters the count.
- **Kill stray probes.** Every spawned `bob` gets a **15 s timeout** on the
  plugin side (the Rust default is 300 s — far too long for a status bar).
  Kill the process group on timeout; record `keep: null, keep_age: stale`.

Expected steady-state cost: ~50–100 Keep syncs/day worst case at 15-min
cadence while Obsidian is open (fewer in practice with idle-skip), each an
incremental `state.json`-backed sync of a small inbox — comparable to the
existing daily `gcal sync` habit, not a scraper. The inbox path costs one file
read per keystroke-batch — unmeasurable.

### 5.3 Auth gating ("only shown if pull would actually work")

Tier it — "pull would work" cannot be proven without snapshotting, so don't
try:

1. **Hide** when `status` reports `authenticated: false` (no config, bad
   email, no token, cookie-instead-of-token, `uv` missing, adapter crash on
   `ping`). No chip, no tooltip, no timer. This is the common
   never-set-up-Keep case and it must be zero-noise.
2. **Show dimmed** when authenticated but the last `--refresh` failed
   (network down, 401/403 expiry, rate limit, missing target, lock busy):
   inbox segment stays live; Keep segment shows the last number dimmed (or
   `☁ –` when there is none) with a tooltip naming the cause and age.
3. **Show live** only after a successful snapshot. `fetched_at` travels with
   the number everywhere so "3" always means "3 as of 12m ago".

Never run `token_command` in a way that can prompt inside the refresh loop;
if `pass` needs pinentry the call times out and the chip stays in tier 1/2.
Login remains the documented manual flow (`bob gkeep login`), unchanged.

### 5.4 Count semantics

- **Keep headline = `new` + `revised`** (default-pull writes). `pending`
  (archive-only), `pinned`, `shared`, `empty`, `archived` never enter the
  headline; tooltip breaks them out (`1 pending archives silently ·
  2 pinned stay in Keep`). URL-only notes that `pull` would clip count as
  `new`/`revised` normally (they are actionable writes); tooltip may add
  `🔗 1 clips to reading queue` when `clip` hints are present.
- **Inbox = `note_tasks::scan(target).open_tasks().count()`** — open means
  `status_type.is_open()`, covering custom statuses, not just a char test.
  Closed = done + cancelled families. Missing target → inbox segment shows
  `📥 –` with "create it or set gkeep.target" tooltip, never a crash.
- Both counts are plain integers; when both are zero the chip collapses to a
  quiet `✓ Keep clear` for ~10 s after a successful refresh, then hides (same
  hide-when-clear manners as the review footer).

### 5.5 Visual + interaction design

One status-bar item (`gkeep-footer`), placed **immediately right of the review
footer** so the two "what needs me?" signals read as a pair. Two segments,
never two chips:

- **Keep**: cloud glyph (`☁`, Obsidian codicon `cloud` where available) +
  tabular number. Tone: calm blue/gold; stale (>60 min) or failed: dimmed
  with a dotted underline; refreshing: animated `…`.
- **Separator**: middot with wide letter-spacing (`·`), 40% opacity.
- **Inbox**: tray glyph (`📥` / codicon `inbox`) + tabular number, default
  foreground; zero: dimmed `📥 0` (still shown while Keep > 0 so the pipeline
  reads left-to-right; hidden with the chip when both are zero).
- **No red for nonzero.** Counts are work, not errors. Red is reserved for
  "refresh failed and the number is older than 4 h".
- **Tooltip** (the real UI — the chip is just a door):
  `☁ 3 to pull (2 new · 1 revised · 1 pending archives · synced 12m ago) →
  click to preview  ·  📥 5 open in gkeep_inbox.md → click to open`.
- **Click**: left-click Keep segment → run `bob gkeep list` preview
  (command-mode card or terminal per the user's existing habit); left-click
  inbox segment → open the target note at the first open task; right-click /
  long-press → manual refresh + "Open Keep in browser" menu item. Every action
  is a single-hop navigation, never an inline pull/archive control — the
  footer cannot mutate Keep or the vault.
- **Settings**: two session toggles reusing the ledger-tools pattern
  (`Toggle GKeep footer`, `Toggle GKeep auto-refresh`), plus respect for a
  shared-config `gkeep.footer: false` escape hatch. No settings tab.
- **Motion**: no animation except the brief `…` spinner during a
  user-initiated refresh; no bounce/count-up flourishes in a status bar.

Mock (monospace, tabular numerals; actual hues from the theme):

```
normal:   ☁ 3 · 📥 5          (tooltip as above)
clear:    ✓ Keep clear        (auto-hides)
stale:    ☁ 3? · 📥 5         (dimmed cloud, dotted; tooltip: "last sync 2h ago — click to refresh")
unknown:  ☁ – · 📥 5          (no Keep data yet / refresh failed with no cache)
hidden:   (no config/token — nothing rendered, timers stopped)
```

Screen-reader text mirrors the tooltip sentence; glyphs are decorative
(`aria-hidden`), so meaning never depends on emoji rendering.

### 5.6 Edge cases the implementation must cover

- Missing/renamed target, `..`-escape or non-`.md` target (config validation
  already rejects; the footer must not crash on it).
- Empty Keep + nonempty inbox (most common steady state) and vice versa.
- `pull.lock` held: spinner, keep old numbers, tooltip "pull running…".
- Offline / captive portal / 429: dim + backoff, inbox unaffected.
- Token expiry mid-day (401/403): dim Keep with "re-login" hint in tooltip;
  never pop pinentry.
- Multi-host: cache is per-host (XDG), receipts stay in-Git — no cross-talk.
- Mobile: text-only chip, no subprocess spawn on metered connections.
- Large inboxes: snapshot returns all Home notes; classification is linear and
  already bounded — no extra paging needed for a count.

## 6. Alternatives considered and rejected

- **Reuse `doctor -f json` as the probe.** Same cost as a snapshot; rejects
  the whole point (§2.2).
- **Parse the vault in JS / count Keep in the plugin.** Violates the thin
  rendering contract (plugins render what `bob` reports; `bob` owns grammar,
  fingerprints, and routing). The one exception — counting open tasks from
  already-loaded editor text for the inbox segment — is acceptable only as a
  render optimization; the subprocess remains the source of truth on
  navigation.
- **Server-sent events / push from Keep.** No webhook exists on the unofficial
  API; polling-with-cache is the only honest option.
- **Putting auto-pull behind the footer.** Explicitly out of scope: archiving
  is guarded, content-checked, and journaled for a reason. The footer never
  writes.

## 7. Adjustments to the requirements (explicit)

1. **Keep headline counts `new` + `revised`, not every inbox note.**
   The ask ("how many notes would be synced if pull were run") literally
   includes `pending` (archive-only) and arguably pinned/shared. Counting
   those makes the number unactionable. Pending stays visible in the tooltip.
2. **"Only shown if authenticated" becomes three tiers (hide / dim / live).**
   Binary hide/show cannot distinguish "never set up" from "offline for 5
   minutes"; the latter must not nuke the inbox count.
3. **Inbox "seconds at most" is implemented as event-driven, not interval.**
   A 1-second timer re-reading the file is wasteful and still misses
   sub-second edits; vault events + 500 ms debounce is both faster and free.
   The Keep side gets the slow timer instead.
4. **"Visually distinct" is specified as glyph + position + tone, not color
   alone** (color-vision and theme safety), with exact mock strings in §5.5.
5. **Added: the footer is read-only and shows its age.** Neither was in the
   ask; both are load-bearing for trust. No footer-initiated pull/archive,
   ever; every Keep number carries a timestamp.

## 8. Suggested build order

1. **`bob gkeep status` + cache** (Rust, tests via `BOB_GKEEP_ADAPTER` fakes;
   `just check` + adapter self-test). No plugin change yet; verify
   `status` / `status --refresh` JSON by hand.
2. **Inbox-only chip** in ledger-tools behind a session toggle: vault events
   → `status` (no refresh) → render. Ship this alone; it is safe and useful
   on day one.
3. **Keep segment (manual refresh only)**: click → `status --refresh`,
   cache read on start + `run-finished`. Measure warm-snapshot latency on the
   MacBook before proceeding.
4. **Slow auto-refresh + backoff + dimming** (§5.2) only if p95 warm refresh
   is under ~10 s and Bryan still wants it after a week of manual use.

## 9. Open questions for Bryan

- Is `new` + `revised` the right headline, or do you want `pending`
  (archive-only) in the number too?
- One chip with two segments (recommended) vs. two adjacent chips — any
  strong status-bar layout preference relative to the review footer?
- Is a 15-minute Keep cadence too chatty, or would you prefer hourly +
  manual refresh only?
- Should the chip appear on mobile Obsidian, or desktop-only like some other
  surfaces?

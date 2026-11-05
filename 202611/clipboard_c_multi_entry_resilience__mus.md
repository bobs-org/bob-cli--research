# `%c` multi-entry clipboard capture: root causes and resilient redesign

Researcher: mus · 2026-11-05 · swarm 5r
Question: `%c` works for one clipboard entry but `%c<N>` (N > 1)
returns only the first entry correctly. Is Bryan running the wrong
clipboard manager (Clipy vs whatever is on his MacBook)? How should
we make `%c` resilient and reliable?

TL;DR: the wrong-manager hypothesis is plausible and fits the
symptom exactly, but swapping one hardcoded manager path for another
will not make `%c` resilient. Today's history path is Clipy-or-bust
with three additional correctness bugs (arbitrary tie-break ordering,
exact-string live-vs-history dedup, and a lag race) that produce
"first entry right, rest wrong" even when Clipy is the right manager.
Recommend a small provider abstraction (Clipy + Maccy + explicit
command + fail-loud), per-entry provenance in dry-run/JSON, and a
tolerant merge. Do not build a bob-owned history daemon yet.

## 1. How `%c` works today

The full path is `directive -> ClipRequest -> clipboard read ->
history merge -> per-entry plan -> render/persist`, with Mac Capture
as a second caller of the same CLI contract.

- Grammar: `src/native/capture_language/directive.rs` lexes `%c` /
  `%c<N>` at either item edge (`DirectiveKind::Clip { count }`,
  `ClipRequest::from_count`). `%c0`, leading-zero `%c01`, and
  overflow are `unknown_directive`; each directive appears at most
  once per item. `src/native/capture_language/model.rs:769`
  defines `enum ClipRequest { Current, History { count } }`.
- Planning: `src/native/capture/plan.rs:902` (`read_capture_clipboard`)
  maps `Current` to `capture_clip::read_clipboard()` and `History`
  to `capture_clip::read_clipboard_history(count)`. Target runs memo
  one read per `item_index` (`FanoutClipboardRead`).
- Live read: `src/native/capture_clip/clipboard.rs:100`
  (`clipboard_command_output`) honors `BOB_CLIPBOARD_CMD`, else
  `pbpaste` on macOS, else Linux `wl-paste`/`xclip`/`xsel`/tmux.
  `normalize_clipboard_output` strips `\r\n`, trailing blank lines,
  rejects NUL/non-UTF8/empty.
- History read: `src/native/capture_clip/clipboard.rs:57`
  (`read_history_candidates`) honors `BOB_CLIPBOARD_HISTORY_CMD`
  (whitespace-split, count appended, must print newest-first JSON
  `string[]`), else on macOS opens
  `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db`
  via `src/native/capture_clip/clipy.rs:5` (`read_clipy_history`),
  else errors on other platforms. There is no auto-detection of any
  other manager.
- Clipy SQL: `ORDER BY updateAt DESC, id DESC LIMIT ?1`, then per
  history id
  `SELECT pasteboardType, data ... ORDER BY "index" ASC, id ASC`,
  decoded by `decode_clipy_asset` (accepts `public.utf8-plain-text`,
  `NSStringPboardType`, `public.url`, `NSURLPboardType`,
  `public.file-url`, `NSFilenamesPboardType`; everything else is
  "unsupported"). Multi-asset entries are joined with `"\n"`.
- Merge: `clipboard.rs:35` (`merge_history_candidates`) removes the
  first history occurrence equal to live `current`, requires
  `candidates.len() + 1 >= count`, and returns
  `[current, ...candidates[..count-1]]`.
- Per-entry planning:
  `src/native/capture_clip/plan.rs:139`
  (`plan_history_with_reservations`) classifies each value
  independently (inline / lines / flat unordered list / attachment /
  snippet), flattens lines, keeps per-entry `ClipOutput` records.
  Any entry failure aborts the whole capture before any note write.
- Mac Capture contract: `docs/reference/mac-capture/capture-previews.md`,
  `capture-panel.md:445`, `keyboard.md:90`. Live preview runs
  `bob capture --dry-run [--no-clip] --format json`; `--no-clip` is
  omitted only when the accepted `capture-parse` reports a `clip`
  directive span. While previewing a clip draft it polls
  `NSPasteboard.general.changeCount` at most 1 Hz and re-runs the
  dry run on change. Each `%c` item renders a Clip card from that
  item's `clip` object. `ClipOutput` always serializes `entries`
  (see `src/native/capture_clip/model.rs:82`).

Docs of record: `docs/capture.md#clipboard` (`%c` reads live once;
`%c<N>` reads live + history newest-first; every entry must succeed
or nothing is written), `docs/reference/capture-syntax.md#percent-clipboard`,
`docs/reference/cli/capture.md` env table (`BOB_CLIPBOARD_CMD`,
`BOB_CLIPBOARD_HISTORY_CMD`, "History: ... read-only Clipy SQLite
on macOS; no automatic provider elsewhere"), and
`docs/reference/configuration.md:314-315`.

## 2. Why N=1 works and N>1 fails: five stacked failure modes

### 2a. Wrong-manager mismatch (most likely, fits the symptom best)

bob only knows Clipy's database. The macOS clipboard-manager market
has moved on:

| Manager | History store bob knows? | Actual location |
| --- | --- | --- |
| Clipy | yes | `~/Library/Application Support/com.clipy-app.Clipy/sqlite.db` |
| Maccy | no | `~/Library/Containers/org.p0deje.Maccy/Data/Library/Application Support/Maccy/Storage.sqlite` (Core Data, `ZHISTORYITEM` / `ZHISTORYITEMCONTENT`) |
| Raycast | no | proprietary; no stable file API (script-command only) |
| Alfred Powerpack | no | `~/Library/Application Support/Alfred/Databases/` (`clipboard.alfdb`), proprietary |
| macOS 26 Tahoe built-in | no | off by default; no CLI-readable history API |
| Paste / PastePal / others | no | app-container SQLite, each different |

Maccy is the key suspect: it is the current default recommendation
for "free, open-source, keyboard-first" macOS history, while Clipy
is unmaintained since ~2021. If Bryan runs Maccy (or Raycast/Alfred),
two outcomes are possible and both match "first right, rest wrong":

- Stale Clipy DB left from an old install: the file exists so bob
  does not error, but rows are months old. Live `pbpaste` (correct)
  + stale rows (wrong) = exactly the reported symptom.
- No Clipy DB: bob errors
  (`Clipy clipboard history database was not found at ...`), which
  the user may experience as "history never works, single paste
  does" if Mac Capture falls back to live-only preview or the user
  retries with `%c`.

Single-entry `%c` never touches any manager database, so it is
immune to all of this. That immunity is itself diagnostic: "N=1
always works, N>1 is wrong" points at the history provider, not the
live path or the per-entry classifier.

### 2b. Tie-break ordering bug (real bug, independent of manager)

`clipy.rs` orders histories by `updateAt DESC, id DESC`. `id` is
`TEXT` (Clipy mints string ids, effectively UUIDs), so for copies
made within the same `updateAt` tick the order is lexicographic-UUID
descending, i.e. arbitrary. Rapid successive copies (the normal way
to stage `%c3` material) routinely share a timestamp tick, so entries
2..N come back in random order even when Clipy is running and
correct. The fixture test in
`src/native/capture_clip/tests.rs:120`
(`reads_clipy_sqlite_assets_in_deterministic_order`) only passes
because it uses distinct `updateAt` values (1 vs 2); there is no test
with tied timestamps. Fix: order by a monotonic row key (`rowid`)
or by `(updateAt DESC, rowid DESC)`, never by random-text `id`.

### 2c. Live-vs-history dedup is exact-string, flavor-sensitive

`merge_history_candidates` dedups by one exact `==` after
normalization. Live text comes from `pbpaste` (one flavor); history
text comes from Clipy's stored pasteboard assets (possibly
`NSStringPboardType` + `public.url` + `file-url` joined with
`"\n"`, or plist-wrapped strings via `decode_utf8_asset` /
`decode_filenames_asset`). Trailing-newline handling, plist
round-trips, multi-asset joins, and file-URI-vs-path decoding can
all make "the same copy" compare unequal. Then the newest history
row (a duplicate of live) is kept, everything shifts by one, and the
user sees `[correct-live, duplicate-of-live, older...]` — again
"only the first is right". The `same`/`later duplicate` cases in
`tests.rs:74` cover identical strings only, not flavor skew.

### 2d. Write-lag race with no correlation key

bob reads live from the pasteboard and history from a third-party
SQLite file with no shared clock. If Clipy has not yet flushed the
latest copy (poll interval, app asleep, excluded app/window, or
ignore-pattern), history is one behind live. bob has no timestamp or
`changeCount` to detect the skew, so it silently returns a window
that is off by one. N=1 never notices; N>1 always does.

### 2e. Brittle schema gate + all-or-nothing semantics

`validate_clipy_schema` hard-fails on any missing column or type
mismatch (`unsupported or unmigrated Clipy database`), which is good
for loudness but means a Clipy upgrade silently breaks all history.
Conversely a present-but-stale database passes validation and
returns wrong data silently. And `plan_history_with_reservations`
plus `merge_history_candidates` require the exact count or abort
the entire capture, so one bad history row (binary image, missing
file path, empty string) discards even the good live entry. For a
capture tool, failing open with labeled partial results plus a
warning is usually better than failing closed, at least under
`--dry-run`/preview.

## 3. Confirm the manager on the MacBook in two minutes

Run on the MacBook (not Linux CI):

```bash
# Which manager database actually exists?
ls -l ~/Library/Application\ Support/com.clipy-app.Clipy/sqlite.db
ls -l ~/Library/Containers/org.p0deje.Maccy/Data/Library/Application\ Support/Maccy/Storage.sqlite
ls -l ~/Library/Application\ Support/Maccy/ 2>/dev/null
ps aux | grep -i -E "clippy|maccy|raycast|alfred|paste" | grep -v grep

# Is the Clipy DB fresh or stale?
sqlite3 ~/Library/Application\ Support/com.clipy-app.Clipy/sqlite.db \
  "SELECT id, updateAt, datetime(updateAt,'unixepoch') FROM pasteboardHistories ORDER BY updateAt DESC LIMIT 5;"

# Ground truth: what does each layer think the last 3 clips are?
pbpaste | head -c 300; echo
# then compare with the manager's own UI history and with:
BOB_CLIPBOARD_CMD="pbpaste" bob capture --dry-run -f json -- "probe %c3" | jq .clip
```

Interpretation: Clipy DB missing + Maccy running = wrong-manager
confirmed. Clipy DB present but newest `updateAt` hours old while
`pbpaste` and Maccy agree = stale-DB variant confirmed. Clipy DB
fresh but `bob` order disagrees with Clipy UI on rapid copies =
tie-break/merge bug confirmed (§2b/§2c). Record the manager name,
DB mtime, and the three-way diff before changing code.

## 4. Critique: is "make `%c` resilient" the right goal?

Yes, with three adjustments to what "resilient" should mean.

1. Resilience is diagnosability first, cleverness second. Today a
   wrong history silently captures wrong bullets into the vault.
   The highest-value change is per-entry provenance (which provider
   supplied each entry, its timestamp, and whether live-dedup fired)
   surfaced in `--dry-run` JSON and the Mac Capture Clip card, plus
   an error that names the provider path and the configured
   override. Silent wrong data is worse than a loud refusal.
2. Do not hardcode a second manager. A Maccy-only patch repeats the
   Clipy mistake. The fix is a tiny provider trait with explicit
   precedence (`BOB_CLIPBOARD_HISTORY_CMD` > auto-detected Clipy >
   auto-detected Maccy > fail-loud), each provider owning one SQL
   query plus a freshness probe. Raycast/Alfred stay on the explicit
   command path because they expose no stable file.
3. Keep the all-or-nothing commit for real captures, but make
   preview partial. Atomicity (plan-then-commit, no partial vault
   writes) is load-bearing in `src/native/capture/plan.rs` and
   `docs/capture.md:702`; do not relax it for writes. What should
   relax is `--dry-run`/preview: show which entries succeeded, mark
   the bad one, and let the user reduce N or fix the clipboard
   instead of guessing.

Out of scope (deliberately): a bob-owned history daemon, polling
`NSPasteboard` from CLI bob, or scraping Raycast/Alfred internals.
Those trade a small integration bug for a background process the
project must then ship, sign, and debug. Revisit only if provider
coverage proves insufficient after Maccy + explicit-command support.

## 5. Recommended solution

### Phase 0 — prove the diagnosis (no behavior change)

- Add a read-only diagnostic: `bob capture --dry-run -f json`
  already emits `clip`; extend it with `clip.provider`
  (`"clipy" | "maccy" | "history-cmd" | "live-only"`),
  `clip.provider_path`, and per-entry `entries[].source`
  (`"live" | "history:0" ...`) plus provider timestamps where
  available. Mac Capture's Clip card renders the provider line
  (see `docs/reference/mac-capture/capture-previews.md#clip-card`).
- Document the two-minute check from §3 in
  `docs/capture.md#clipboard` and in the
  `BOB_CLIPBOARD_HISTORY_CMD` rows of `docs/reference/configuration.md`
  and `src/native/capture/cli.rs`.

### Phase 1 — provider abstraction + Maccy support

- New `src/native/capture_clip/history.rs` with
  `enum HistoryProvider { ExplicitCmd, Clipy, Maccy }`,
  `fn detect() -> Result<Provider, String>` (explicit cmd wins;
  else first fresh database wins; else fail-loud listing every
  path probed), and `fn read(provider, count)`.
- Move current `clipy.rs` under it unchanged except the ordering
  fix (`ORDER BY updateAt DESC, rowid DESC`), and add `maccy.rs`
  reading `Storage.sqlite` (`ZHISTORYITEM` joined to
  `ZHISTORYITEMCONTENT`, newest-first, text/image/file flavors
  mapped onto today's `decode_clipy_asset` equivalents).
- Keep `BOB_CLIPBOARD_HISTORY_CMD` semantics byte-identical
  (whitespace-split, trailing count arg, newest-first JSON array)
  and add `BOB_CLIPBOARD_PROVIDER=clipy|maccy|cmd` as an explicit
  pin for ambiguous machines (both DBs present).
- Errors must name the provider and path probed, e.g.
  `clipboard history unavailable: probed Clipy at <path> (missing)
  and Maccy at <path> (missing); set BOB_CLIPBOARD_HISTORY_CMD ...`.

### Phase 2 — harden merge and ordering

- Correlation: compare live against history newest with both exact
  and whitespace-insensitive match; on near-match, treat as dup
  but emit a `dedup: "fuzzy"` marker in JSON instead of silently
  shifting. Never return `[live, live-dup, ...]` silently.
- Staleness guard: if history newest != live (exact or fuzzy) and
  provider timestamp is older than a threshold, include a
  `history_lag_suspected: true` hint in dry-run rather than
  pretending the window is aligned.
- Keep exact-count-or-abort for real writes; under `--dry-run`
  report per-entry status so entry 2 being an image explains
  itself instead of failing the whole preview opaquely.
- Regression tests: tied-`updateAt` ordering (would fail today),
  flavor-skew dedup (pbpaste text vs plist-wrapped/file-URI history
  row), lagging-history merge, and Maccy fixture DB — extend
  `src/native/capture_clip/tests.rs` and
  `tests/cli/capture/clip.rs` (history compose + provider-failure
  cases already exist there and give the pattern).

### Phase 3 — UX safety net (cheap, high leverage)

- Mac Capture already re-runs dry-run on `changeCount` at 1 Hz;
  keep that, and add the provider + per-entry source to the Clip
  card so "entry 2 came from stale Clipy" is visible before Capture.
- Document the explicit-paste escape hatch for N>1: copy items with
  a pause, or stage them as separate `%c` captures, or point
  `BOB_CLIPBOARD_HISTORY_CMD` at a 3-line shell shim that prints
  the intended JSON array. The shim is also the Raycast/Alfred
  answer until/unless those vendors publish a file API.
- Do not change `%c` grammar, `ClipMode::History` JSON shape
  (additive fields only), or the plan-then-commit atomicity.

## 6. Concrete touch list (for the implementer)

- `src/native/capture_clip/clipy.rs`: tie-break fix, expose
  provider id + timestamps.
- New `src/native/capture_clip/history.rs`, `maccy.rs`; rewire
  `src/native/capture_clip/clipboard.rs:57` to dispatch.
- `src/native/capture_clip/model.rs`: additive `provider`,
  `source`, `dedup` fields on `ClipOutput` serialization.
- `src/native/capture/cli.rs` help + `docs/capture.md`,
  `docs/reference/cli/capture.md`, `docs/reference/configuration.md`:
  provider order, Maccy path, pin variable, diagnostic fields.
- Tests: `src/native/capture_clip/tests.rs`,
  `tests/cli/capture/clip.rs` (tie, skew, lag, Maccy fixture,
  both-DBs-present precedence, missing-everything error text).
- Mac Capture: Clip card provider line
  (`docs/reference/mac-capture/capture-previews.md`,
  `capture-panel.md`); no protocol break (additive JSON only).

## 7. Alternatives considered

- Swap Clipy path for Maccy path: fixes Bryan today, breaks the
  next Clipy user. Rejected as a repeat of the original mistake.
- Shell out to AppleScript/`NSPasteboard` history: macOS exposes
  only the current pasteboard, no history API; polling from CLI
  bob cannot recover past entries. Rejected.
- bob-owned daemon caching `changeCount`: correct long-term, but a
  new launchd process, signing, and lifecycle story for a bug that
  provider abstraction + diagnostics already fix. Deferred, not
  rejected; revisit if explicit-command coverage fails.
- Relax atomicity (write good entries, skip bad): violates the
  capture contract (`docs/capture.md:702`, target-run fanout in
  `src/native/capture/plan.rs:1277`) and risks half-written task
  blocks. Rejected for writes; partial display kept to dry-run.

## 8. Verification

- Repro from §3 on the MacBook before/after: `%c1` vs `%c3` on
  three rapid known strings; `bob capture --dry-run -f json`
  provider + entry sources must match the manager UI order.
- New unit tests (tie order, flavor-skew dedup, lag hint) plus
  existing suites: `cargo test -p bob-cli capture_clip`,
  `tests/cli/capture/clip.rs`, and `just check` per repo gate.
- Mac Capture: Clip card shows provider for `%c` and `%c3`
  drafts; changeCount re-preview still 1 Hz-gated.

Key files: `src/native/capture_clip/clipboard.rs`,
`src/native/capture_clip/clipy.rs`,
`src/native/capture_clip/plan.rs`,
`src/native/capture_clip/model.rs`,
`src/native/capture_clip/tests.rs`,
`src/native/capture_language/directive.rs`,
`src/native/capture_language/model.rs`,
`src/native/capture/plan.rs`,
`src/native/capture/cli.rs`, `tests/cli/capture/clip.rs`,
`docs/capture.md`, `docs/reference/capture-syntax.md`,
`docs/reference/cli/capture.md`,
`docs/reference/configuration.md`,
`docs/reference/mac-capture/capture-previews.md`,
`docs/reference/mac-capture/capture-panel.md`.



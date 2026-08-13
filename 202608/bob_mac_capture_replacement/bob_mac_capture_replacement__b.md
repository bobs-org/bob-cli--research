# Research: Replacing the Hammerspoon Capture Pop-up with a Native `bob-mac-capture` App

- **Date:** 2026-08-13
- **Repo under design:** `bobs-org/bob-mac-capture` (created, empty)
- **Question:** What is the best way to implement a Mac application that replaces the
  Hammerspoon `⌃⇧⌘I` capture pop-up and fixes its multi-line, completion/highlighting,
  latency, notification, and aesthetic problems?
- **Answer (short):** Build a native Swift menu-bar (`LSUIElement`) app around a
  pre-warmed non-activating `NSPanel` and a custom `NSTextView`, and move the capture
  *grammar* out of the client and into `bob-cli` as machine-readable
  parse/complete/preview JSON endpoints. Full rationale in
  [§9](#9-recommendation) and the phased plan in [§10](#10-phased-implementation-plan).

---

## 1. What Exists Today

The current pop-up lives entirely in the chezmoi repo:

| File | Lines | Role |
| --- | --- | --- |
| `home/dot_hammerspoon/init.lua` | 1653 | Hotkey, WebView prompt, HTML/CSS/JS, `hs.chooser` pickers, `bob` subprocess staging, notifications |
| `home/dot_hammerspoon/task_capture.lua` | 353 | A **second, independent implementation** of the `bob capture` marker grammar, in Lua |
| `tests/hammerspoon/task_capture_spec.lua` | — | Busted specs for the Lua parser |

Key mechanics, with references:

- **Hotkey:** `hs.hotkey.bind({ "cmd", "shift", "ctrl" }, "i", ...)` —
  `init.lua:1329`.
- **UI:** an `hs.webview` created **fresh on every invocation**
  (`init.lua:1305`), populated from a ~200-line Lua heredoc of HTML/CSS/JS
  (`taskCaptureHtml`, `init.lua:56`), and torn down on close
  (`deleteOnClose(true)`, `init.lua:1312`).
- **Input field:** `<input id="capture" type="text">` (`init.lua:163`) — a
  single-line HTML text input. This is the literal, mechanical reason multi-line
  input is impossible today.
- **Subprocess model:** every `bob` call is
  `hs.task.new("/bin/zsh", ..., { "-lc", command, "bob-capture" })`
  (`init.lua:737`, `init.lua:743`) — a **login shell** per stage, with `PATH`
  re-exported inside the script body (`init.lua:693`).
- **Target picking:** staged `hs.chooser` modals driven by
  `bob capture-targets|capture-sections|capture-tasks --format json`
  (`init.lua:695`–`init.lua:707`).
- **Notifications:** `hs.notify.new(...)` with an elaborate fallback ladder and a
  1-second `presented()` probe that logs "delivered but not presented" to the
  Hammerspoon console (`notifyWithAttributes`, `init.lua:578`;
  `scheduleCapturePresentationCheck`, `init.lua:537`).

That defensive notification code is itself evidence: it was written *because* the
banners were already unreliable.

---

## 2. Root-Cause Analysis of the Five Complaints

### 2.1 "It doesn't support multi-line input"

Direct cause: the WebView hosts `<input type="text">`, which is single-line by
definition. Swapping to `<textarea>` would be a one-line change, but it would
immediately expose the real problem — submit-vs-newline key handling, autosizing,
and the fact that `bob capture` normalizes text to one line anyway. Multi-line
input is therefore not just a widget swap; it needs a decision about **what
multi-line means semantically**. See [§5.1](#51-what-should-multi-line-actually-do).

### 2.2 "No completion, syntax highlighting, or hints"

Partially inaccurate as stated, and the nuance matters. There *is* completion —
but it is **staged and modal**: you type a bare `@`, submit, and only then does an
`hs.chooser` appear (`init.lua:1204` comment block enumerates the `@`, `@#`,
`@route:`, `@^` modes). What is missing is **inline, as-you-type** completion,
highlighting, and hinting.

The deeper cause is architectural: `task_capture.lua` re-implements the marker
grammar in Lua so the Lua side can decide which picker to show. That grammar is
non-trivial (see [§4](#4-the-grammar-the-ui-must-model)) and already exists in Rust
inside `bob-cli`. Any client that wants to *highlight* the syntax needs a third
copy. **The duplication, not the widget, is the blocker.**

### 2.3 "It is so slow to pop up sometimes"

Three compounding costs, in descending order of likely impact:

1. **Login shell per stage.** `zsh -lc` sources `.zprofile` + `.zshrc`. Measured
   on athena (Linux, this workspace): `/bin/zsh -lc 'exit'` = **95 ms**. On a Mac
   with Homebrew shims, `nvm`/`rbenv`/`pyenv` hooks, and completion init, 250–600 ms
   is typical. Every picker stage pays this again.
2. **WKWebView cold construction.** The panel is built from scratch on each
   hotkey press — `hs.webview.new` + `:html(...)` + JS parse + first paint. This is
   tens to low hundreds of milliseconds and is exactly the kind of cost that is
   invisible when warm and glaring when cold (hence "sometimes").
3. **Hammerspoon's Lua runtime** competing with whatever else `init.lua` is doing
   (there is a Pomodoro menubar runtime with tick/sync timers in the same file).

The `bob` binary is **not** the bottleneck. Measured on athena:

```
bob capture-targets --format json          →  11 ms
bob capture --dry-run --format json -- …   →   5 ms
```

> **Measurement caveat:** these numbers are from athena (Linux, warm page cache,
> local `~/bob` vault), not from the MacBook. Re-measure on the Mac before
> treating them as a budget. The *relative* conclusion — that the login shell
> costs ~10–100× more than the binary — is robust regardless.

### 2.4 "I don't receive a Mac notification, sometimes not even on error"

Two independent causes, both fatal on their own:

1. **`hs.notify` sits on deprecated `NSUserNotification`.** Hammerspoon has an
   open, long-running migration problem here; `hs.notify.show` silently failing is
   a [known issue](https://github.com/Hammerspoon/hammerspoon/issues/3631), and the
   maintainers have said moving to `UNUserNotificationCenter` "might end up
   requiring an entirely new approach/module and some changes in the core
   application" ([PR #509](https://github.com/Hammerspoon/hammerspoon/pull/509)).
2. **macOS suppresses banners from the frontmost app by default.** The capture
   WebView is a regular `hs.webview` window, so pressing the hotkey makes
   **Hammerspoon frontmost**. The code notices this and tries to restore the
   previous app (`restoreTaskCaptureApp`, `init.lua:253`), but there is a race
   between "capture completes → notification sent" and "previous app is actually
   frontmost again". That race is a textbook source of *intermittent* banners —
   which matches the "sometimes" in the complaint precisely.

A third contributing factor: all notifications are attributed to
**Hammerspoon**, so per-app Focus/notification settings apply to *everything*
Hammerspoon does, not to capture specifically.

### 2.5 "It is ugly"

Structural: the UI is hand-written HTML/CSS embedded in a Lua string literal
(`init.lua:56`–`init.lua:250`). It cannot inherit macOS 26 Tahoe's Liquid Glass
materials, vibrancy, dynamic type, accent color, or Dark Mode transitions, and it
has no design iteration loop — every tweak is a Lua string edit plus a
Hammerspoon reload.

---

## 3. Requirements for the Replacement

Derived from the complaints plus what the existing flow already does well
(the staged pickers are genuinely good and must not regress).

**Must have**

| # | Requirement |
| --- | --- |
| R1 | Multi-line input with an explicit submit key distinct from newline |
| R2 | Inline, as-you-type syntax highlighting of the `bob capture` marker grammar |
| R3 | Inline completion for routes, sections, and task block IDs (no modal stage) |
| R4 | Live preview of what will actually be written (file + rendered line) |
| R5 | Reliable success **and** failure notifications, attributed to this app |
| R6 | Sub-100 ms perceived pop-up latency, cold, every time |
| R7 | Native macOS appearance (Liquid Glass, vibrancy, Dark Mode, accent color) |
| R8 | Never lose typed text on failure (the current code is careful about this — `init.lua:770` comment) |
| R9 | Clipboard markers (`%`, `%N`, `%header`) keep working, including Clipy history |

**Should have**

| # | Requirement |
| --- | --- |
| R10 | Single source of truth for the grammar — no third re-implementation |
| R11 | Notification actions (Open note in Obsidian, Undo) |
| R12 | In-panel success confirmation so correctness does not *depend* on Notification Center |
| R13 | Headless-testable core, separable from the UI |
| R14 | Recent-capture history / re-edit |

**Non-goals**

- App Store distribution. This is a personal tool for one Mac.
- Cross-platform. Linux capture already happens at the terminal.
- Re-implementing vault logic. `bob-cli` owns it and must keep owning it.

---

## 4. The Grammar the UI Must Model

This is the crux of the design, so it is worth stating in full. From
`src/native/capture.rs:64`–`src/native/capture.rs:130` (the `long_about`):

**Route markers** — leading or trailing, never mid-text:

| Form | Meaning |
| --- | --- |
| `@route` | Capture a `#task` into `route.md` |
| `@route#Section` | Capture an ordinary bullet into a non-`Tasks` heading whose title starts with `Section` (case-insensitive) |
| `@route#` | Same, any non-`Tasks` section |
| `@route:block-id` | Create a `- [*]` next-status task and link it from today's Pomodoro ledger |
| `@route^block-id` | Append a plain child bullet under an existing task (no `[created::]`) |

**Terminal tokens** — recognized only at the very end, on either side of a trailing `@route`:

| Token | Meaning |
| --- | --- |
| `s:<N>` | `[scheduled::]` N days from today |
| `p:<N>` | `[priority::]` at config level N (1–4 → P1–P4), rolls a random scheduled date in that level's window |
| `%` / `%1` | Capture one live clipboard value, no header |
| `%<N>` | Capture exactly N values (live + Clipy history, newest first) |
| `%<header>` | One live value under an explicit header (`_` renders as a space) |
| `%0` | Stays literal |

**Flags:** `--bob-dir/-b`, `--clip/-c[=HEADER]`, `--dry-run/-d`, `--format/-f`,
`--no-clip/-n`, `--route/-r`, `--section/-s`, `--task/-t`, plus hidden `--task-ref`.

**Discovery commands, all with `--format json`:**

- `bob capture-targets` → `{ok, bob_dir, count, targets: [{route, name, label, kind, is_default, status, relative_path}]}`
  where `kind ∈ {inbox, area, project}` (`src/native/capture_targets.rs:193`)
- `bob capture-sections --route <r>` → non-`Tasks` headings
- `bob capture-tasks --route <r>` → open tasks with block IDs

**And the one that makes live preview trivial** —
`bob capture --dry-run --format json` returns a fully-resolved `CaptureResult`
(`src/native/capture.rs:2491`):

```json
{"ok":true,"dry_run":true,"routed":true,"route":"dev","route_label":"dev.md",
 "relative_target":"dev.md","target":"/home/bryan/bob/dev.md","text":"test thing",
 "task_line":"- [ ] #task test thing [created::2026-08-13] [scheduled::2026-08-15]",
 "kind":"task","created":"2026-08-13","scheduled":"2026-08-15","placement":"inserted"}
```

That response already contains everything a preview pane needs: the destination
file, the human route label, the exact rendered Markdown line, the resolved
scheduled date, and whether the note would be created or inserted into. Errors
come back as `{"ok": false, "error": "..."}` with exit code 2 (usage) or 1 (I/O)
(`src/native/capture.rs:2636`).

**Implication:** a preview and validation engine is already 90% built. What is
*not* exposed is (a) token spans for highlighting and (b) cursor-position-aware
completion candidates. Those are small additions to `bob-cli`, and adding them
there is strictly better than re-deriving them in Swift.

---

## 5. Cross-Cutting Design Decisions

These matter more than the framework choice and should be settled first, because
they are framework-independent.

### 5.1 What should multi-line actually do?

`bob capture` normalizes text to one line. Three coherent options:

| Option | Behavior | Verdict |
| --- | --- | --- |
| **A. Cosmetic wrap** | Multi-line only for editing comfort; newlines collapse to spaces on submit | Trivial; solves the stated complaint |
| **B. Line = child bullet** | First line is the task; subsequent lines become child bullets | Already the semantics of the `%N` clipboard path ("2–10 flat text lines … become child bullets") — consistent, but needs a new CLI affordance |
| **C. Line = separate capture** | Each line is its own capture, sharing trailing markers | Powerful for brain-dumps; highest blast radius on failure |

**Recommendation: ship A, design for B.** A satisfies R1 immediately with zero
`bob-cli` change. B is the natural evolution and reuses the child-bullet rendering
that `capture_clip` already produces — but it should be an explicit, later,
opt-in mode, not the default. C is a footgun (a partial failure mid-batch is hard
to reason about) and should be deferred indefinitely.

### 5.2 Where does the grammar live? *(the most important decision)*

Today it lives in two places (Rust + Lua). A new client must not make it three.

| Approach | Assessment |
| --- | --- |
| Re-implement in Swift | ❌ Three copies. Every `bob capture` grammar change becomes a three-repo change. This is the current pain, amplified. |
| Link `bob-cli` as a Rust static library via C ABI | ⚠️ Zero-latency and single-source, but requires `bob-cli` to grow a `crate-type = ["staticlib"]` target, a stable C header, and cross-compilation to `aarch64-apple-darwin` in CI. Real coupling, real build complexity. |
| **Add JSON endpoints to `bob-cli`, spawn the binary** | ✅ Single source of truth, no ABI, no cross-compilation, no versioning contract beyond JSON. Costs one process spawn per query — **measured at 5 ms**. |

**Recommendation: JSON endpoints + subprocess.** Two additions to `bob-cli`,
following `sase/memory/cli_rules.md` (alphabetical ordering, short alias for every
public long option, colored human output):

1. **`bob capture-parse`** — tokenize without executing. Returns byte-offset spans
   with kinds, so the client highlights from authoritative data:
   ```json
   {"ok": true,
    "spans": [
      {"start": 0,  "end": 10, "kind": "body"},
      {"start": 11, "end": 15, "kind": "route",     "route": "dev", "valid": true},
      {"start": 16, "end": 19, "kind": "scheduled", "value": "2026-08-15"}
    ],
    "diagnostics": [{"start": 20, "end": 22, "severity": "error",
                     "message": "p:9 exceeds configured priority levels (1-4)"}]}
   ```
2. **`bob capture-complete --cursor <N>`** — cursor-aware candidates, so the client
   never decides *when* completion applies:
   ```json
   {"ok": true, "replace": {"start": 11, "end": 14},
    "candidates": [{"insert": "@dev", "label": "dev", "detail": "Project · active",
                    "kind": "route"}]}
   ```

This makes the Mac app a **thin, dumb, beautiful renderer**. It also retroactively
lets the Hammerspoon config delete `task_capture.lua` if you ever want a
transition period with both running, and it benefits any future client (an iOS
Shortcut, a Raycast extension, a `zsh` completion script) for free.

### 5.3 Talking to `bob`

- **Never use a login shell.** Resolve `bob` once at launch (config-specified
  absolute path, falling back to a probe of `~/.cargo/bin`, `/opt/homebrew/bin`,
  `/usr/local/bin`) and `exec` it directly with an explicit minimal environment.
  This alone likely removes the majority of the latency (§2.3).
- **Pass text as `argv`, never through a shell string.** The current code is
  already careful here (`init.lua:709` comment); preserve that property.
- **Debounce preview/completion at ~40–60 ms** and cancel in-flight processes on
  new keystrokes. At 5 ms per call, even undebounced typing would keep up, but
  debouncing bounds worst-case vault I/O.
- **Cache `capture-targets` in memory**, refreshed at launch, on panel show, and
  on an `FSEvents` watch of the vault root. Route completion then costs zero
  process spawns.
- **A daemon or FFI is premature.** Revisit only if measured Mac latency exceeds
  the budget in R6.

### 5.4 Notifications

The fix has three parts, and all three are needed:

1. **Use `UNUserNotificationCenter`** from a properly bundled, signed `.app`.
   This is the modern API `hs.notify` cannot reach.
2. **Use a non-activating panel** (`.nonactivatingPanel`) so the app never becomes
   frontmost. This removes the frontmost-app banner suppression *and* the
   restore-previous-app race in one stroke — the app never steals focus, so
   there is nothing to restore. This directly addresses §2.4's "sometimes".
3. **Do not depend on Notification Center for correctness.** Show the result
   inline in the panel (a brief success flash with the destination label, or an
   error banner with the panel *staying open and the text preserved*, matching R8).
   The system notification becomes a convenience, not the only feedback channel.

Add `UNNotificationAction`s for **Open note** (`obsidian://open?path=…`, already
built at `init.lua:499`) and, later, **Undo**.

**Signing caveat:** notifications are one of the macOS subsystems that behave
unpredictably without a stable code-signing identity. Ad-hoc signing is
technically possible but Apple keeps tightening it. Sign with a **free Apple ID
"Personal Team" Apple Development certificate** and a stable bundle ID
(`org.bobs.bob-mac-capture`). No paid Developer Program membership is needed for
a locally-built, locally-run app; notarization is only relevant for distribution.

### 5.5 Global hotkey

Use **Carbon `RegisterEventHotKey`** (via a small wrapper or the
[Magnet](https://github.com/DivineDominion/Magnet) library). It is nominally
deprecated but stable, ships in VS Code/Slack/Electron, and — critically — **does
not require Accessibility permission**, because it only asks to be told about one
specific combination rather than observing all input. The
`NSEvent.addGlobalMonitorForEvents` alternative *does* require Accessibility and
is strictly worse for this use case. Apple has never shipped a modern replacement.

**Migration note:** `RegisterEventHotKey` fails if the combination is already
claimed. The Hammerspoon binding at `init.lua:1329` must be removed (or the new
app given a different combination) before ⌃⇧⌘I will reach the new app. Plan for
a brief period where the app binds e.g. ⌃⇧⌘O for side-by-side comparison.

### 5.6 Latency budget (R6)

| Cost | Today | Target | How |
| --- | --- | --- | --- |
| App start | n/a (Hammerspoon resident) | 0 ms | `LSUIElement` accessory app, `launchd` LaunchAgent with `KeepAlive` |
| Panel construction | WebView built per invocation | 0 ms | Build the `NSPanel` once at launch; `orderFrontRegardless()` on hotkey |
| Shell startup | ~95 ms measured (likely 250–600 ms on the Mac) | 0 ms | Spawn `bob` directly |
| Route list | 11 ms per picker stage | 0 ms | Cached at launch + FSEvents refresh |
| Preview | n/a | ~5 ms, debounced, off the main thread | `--dry-run --format json` |

Perceived pop-up latency becomes a single `orderFrontRegardless()` — one frame.

---

## 6. Option Comparison

Effort estimates assume you are comfortable in the language and are building to
the requirements in §3, not a toy.

| # | Option | Multi-line | Highlight + inline completion | Latency | Notifications | Native look | Effort |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | **Improve Hammerspoon in place** | `<textarea>` — easy | CodeMirror in the WebView — possible | Warm-cache the WebView; shell cost removable | ❌ Still `hs.notify`; still Hammerspoon-attributed | ❌ HTML in a Lua string | S |
| B | **Native Swift (AppKit + SwiftUI), `NSTextView`** | ✅ Native | ⚠️ Hand-built (~600–900 LOC) | ✅ Best possible | ✅ `UNUserNotificationCenter` | ✅ Free, incl. Liquid Glass | M–L |
| B′ | **Native Swift shell + `WKWebView`/CodeMirror 6 content** | ✅ | ✅ Essentially free | ✅ (warm WebView) | ✅ | ⚠️ Chrome native, content emulated | M |
| C | **Tauri v2** (`tauri-nspanel` + `tauri-plugin-global-shortcut`) | ✅ | ✅ CodeMirror 6 | ⚠️ WebView resident ~60–100 MB; good when warm | ✅ via notification plugin | ⚠️ CSS-emulated | M |
| D | **Electron** | ✅ | ✅ | ❌ ~150 MB bundle, ~200 MB RSS | ✅ | ❌ | M |
| E | **Raycast extension** | ⚠️ `Form.TextArea` only | ❌ No custom highlighting in Raycast's input; markdown-only rendering | ⚠️ +50–100 ms extension load | ✅ (Raycast-attributed) | ✅ Raycast's, not yours | S |
| F | **Alfred workflow** | ❌ Alfred's bar is single-line | ❌ | ✅ | ⚠️ Limited | ✅ Alfred's | S |
| G | **Pure Rust GUI** (egui/iced) | ✅ | ⚠️ Hand-built | ✅ | ❌ Needs `objc2` glue anyway | ❌ Non-native rendering | L |
| H | **Obsidian plugin + global hotkey** | ✅ | ✅ CodeMirror (Obsidian ships it) | ❌ Requires Obsidian running and responsive | ⚠️ | ❌ | M |

### Why the losers lose

- **E (Raycast)** is the tempting shortcut and it is the wrong tool here. Raycast
  extensions render *Raycast's* components; you cannot put a custom syntax
  highlighter or a token-aware completion popup inside Raycast's input. You would
  be trading the Hammerspoon chooser for the Raycast list — a lateral move on R2/R3,
  while adding a hard dependency on a third-party commercial app. Worth keeping as
  a *thin extra entry point* later (it would consume the same `bob-cli` JSON
  endpoints), but not as the primary UI.
- **F (Alfred)** fails R1 outright — the Alfred bar is single-line by construction.
- **D (Electron)** buys nothing over C while costing an order of magnitude more
  memory and bundle size for a pop-up that must feel instant.
- **G (Rust GUI)** is superficially attractive because `bob-cli` is Rust, but
  immediate-mode GUI toolkits do not render like macOS, and you would still write
  Objective-C bridging for the panel, the hotkey, and notifications — i.e. all the
  hard parts — without gaining a native text system.
- **H (Obsidian plugin)** couples capture availability to Obsidian being open and
  responsive, which defeats the purpose of a quick-capture tool.
- **A (stay on Hammerspoon)** deserves respect as the cheapest path and it *can*
  fix multi-line, highlighting, and latency. It cannot fix notifications
  (§2.4 cause 1 is upstream, cause 2 is inherent to `hs.webview` taking focus) or
  the aesthetics, and both are explicit complaints. It also keeps the grammar
  duplicated in Lua.

### The real finalists: B vs B′ vs C

All three give a signed bundle, `UNUserNotificationCenter`, an `NSPanel`, and a
Carbon hotkey. They differ almost entirely in **how the editor is built**.

| | B (NSTextView) | B′ (Swift + CodeMirror) | C (Tauri) |
| --- | --- | --- | --- |
| Editor work | Custom `NSTextStorage` highlighter + `NSPopover` completion list | CodeMirror 6 `StreamLanguage` + `autocompletion()` — largely off-the-shelf | Same as B′ |
| Languages in repo | Swift only | Swift + TS/JS + bundler | Rust + TS/JS + bundler |
| Memory | ~30 MB | ~90 MB | ~90 MB |
| Cold panel show | One frame | One frame (WebView kept warm) | One frame (window hidden, not destroyed) |
| Liquid Glass | Free | Chrome only | Emulated |
| Failure mode | Editor polish takes longer than expected | JS↔native bridge complexity | Same, plus Tauri version churn |

**The honest tension:** CodeMirror 6 hands you highlighting, an autocomplete
popup, hover tooltips, and multi-line editing essentially for free. That is a
genuine, significant advantage of B′/C over B, and it should not be waved away.

**Why B still wins:** the thing CodeMirror saves you from is writing a *language*
highlighter. This is not a language. Once `bob capture-parse` returns spans
(§5.2), the Swift highlighter is a loop that applies `NSAttributedString`
attributes over byte ranges — perhaps 150 lines — and the completion UI is one
`NSPopover` with an `NSTableView` fed by `bob capture-complete`. The heavy lifting
moved into `bob-cli` where it belongs, and it moved there *regardless of which
option you pick*. With the parse endpoint in place, CodeMirror's advantage
shrinks from "an entire editor" to "a list widget", and B′/C's costs — a JS
toolchain, a bridge, a WebView, and emulated materials — stop paying for
themselves.

---

## 7. Recommended Architecture

```
┌──────────────────────────── bob-mac-capture (Swift, LSUIElement) ────────────┐
│                                                                              │
│  AppDelegate ──── HotKeyManager (Carbon RegisterEventHotKey, ⌃⇧⌘I)           │
│       │                                                                      │
│       ├──── CapturePanel : NSPanel (.nonactivatingPanel, .floating)          │
│       │        └── NSHostingView                                             │
│       │              ├── CaptureTextView  (NSTextView subclass, TextKit 2)   │
│       │              │     ├── SpanHighlighter   ← bob capture-parse         │
│       │              │     └── CompletionPopover ← bob capture-complete      │
│       │              ├── PreviewPane      ← bob capture --dry-run -f json    │
│       │              └── StatusStrip      (inline success / error, R12)      │
│       │                                                                      │
│       ├──── NotificationService (UNUserNotificationCenter + actions)         │
│       └──── MenuBarExtra (status, recent captures, preferences)              │
│                                                                              │
│  ═══ CaptureCore (pure Swift module, no AppKit — headless-testable, R13) ═══ │
│        BobClient: resolves the binary once, spawns with explicit env,        │
│        cancels in-flight work, caches capture-targets, watches via FSEvents  │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │ argv + JSON on stdout
                                     ▼
                    bob-cli  (single source of truth for the grammar)
                      capture · capture-targets · capture-sections ·
                      capture-tasks · capture-parse* · capture-complete*
                                                          (* = new)
```

**Panel configuration** (the well-established Spotlight recipe):

```swift
styleMask:          [.nonactivatingPanel, .titled, .fullSizeContentView, .resizable]
isFloatingPanel:    true
level:              .floating
collectionBehavior: [.canJoinAllSpaces, .fullScreenAuxiliary]
titlebarAppearsTransparent = true
titleVisibility = .hidden
becomesKeyOnlyIfNeeded = false   // the text view must take keystrokes
```

`.canJoinAllSpaces` + `.fullScreenAuxiliary` means capture works over a
full-screen app — something the current WebView handles poorly.

**Key bindings inside the editor:**

| Key | Action |
| --- | --- |
| `⏎` | Submit |
| `⇧⏎` / `⌥⏎` | Newline |
| `⇥` / `⌃N` `⌃P` | Accept / navigate completion |
| `⎋` | Dismiss completion, then dismiss panel |
| `⌘⏎` | Submit and open the target note in Obsidian |

**Repo layout for `bobs-org/bob-mac-capture`:**

```
Package.swift               # SwiftPM; no .xcodeproj checked in
Sources/
  CaptureCore/              # BobClient, models, span/completion decoding — pure Swift
  BobMacCapture/            # AppDelegate, CapturePanel, CaptureTextView, notifications
Tests/
  CaptureCoreTests/         # swift-testing; fakes the bob binary with a fixture script
Resources/Info.plist        # LSUIElement=1, bundle id, usage strings
Scripts/bundle.sh           # assemble .app from .build/release, codesign, install
justfile                    # build / run / install / test — mirrors bob-cli's convention
```

Build with **SwiftPM plus a bundling script** (or [Swift Bundler](https://github.com/stackotter/swift-bundler))
rather than a checked-in `.xcodeproj`. `swift build` produces a bare executable;
the script assembles `Contents/{MacOS,Resources,Info.plist}`, runs `codesign -s
"Apple Development: …"`, and copies to `/Applications`. This keeps the repo
diffable, scriptable, and consistent with how `bob-cli` is built via `just`.

**Target macOS 26.0+.** macOS 26.6 Tahoe is current as of August 2026;
macOS 27 "Golden Gate" is in public beta for a September 2026 release and is
Apple-silicon-only. Targeting 26 gives you Liquid Glass APIs today and a clean
path to 27.

---

## 8. Sequencing Note

The `bob-cli` work (`capture-parse`, `capture-complete`) is on the critical path
for R2/R3 and should land **first**, in the `bob-cli` repo, with tests. Doing it
first also means Phase 1 of the Mac app is a genuinely small, shippable thing:
panel + multi-line + submit + notifications, with highlighting arriving as a
data-driven layer on top rather than a rewrite.

---

## 9. Recommendation

**Build a native Swift menu-bar application (Option B), and move the capture
grammar into `bob-cli` as JSON endpoints.**

Concretely:

1. **`bob-cli`:** add `bob capture-parse` (token spans + diagnostics) and
   `bob capture-complete --cursor N` (cursor-aware candidates), both
   `--format json`, following `cli_rules.md`. Keep `--dry-run --format json` as
   the preview source — it already returns everything needed.
2. **`bob-mac-capture`:** a Swift `LSUIElement` app with a pre-warmed
   non-activating `NSPanel`, an `NSTextView` editor highlighted from
   `capture-parse` spans, an `NSPopover` completion list fed by
   `capture-complete`, a live preview pane fed by `--dry-run`, inline result
   feedback, and `UNUserNotificationCenter` banners with an "Open note" action.
3. **Signing:** free Apple ID Personal Team Apple Development certificate, stable
   bundle ID. No paid membership, no notarization.
4. **Hotkey:** Carbon `RegisterEventHotKey` for ⌃⇧⌘I, after removing the
   Hammerspoon binding at `init.lua:1329`.
5. **Process model:** spawn the `bob` binary directly with an explicit
   environment. **No login shell, ever.**

**Why this and not the cheaper options:** every complaint traces to something
structural, not cosmetic. Single-line input is the widget. Missing inline
completion is the duplicated grammar. Slowness is the login shell plus per-press
WebView construction. Missing notifications is a deprecated API *plus* a
focus-stealing window. Ugliness is HTML in a Lua string. A native app with a
non-activating panel and a `bob-cli`-owned grammar removes all five causes rather
than patching their symptoms — and the non-activating panel fixes the
notification race and the focus-restore race as a side effect of correct design,
which is the sign the architecture is right.

**Why this and not Tauri/CodeMirror:** the parse-endpoint decision is required in
every option, and it is what makes CodeMirror's editor machinery mostly
redundant. Once it exists, B is less total code across the two repos than B′ or
C, in one language, with native materials for free.

**The pre-registered fallback:** if the editor work in Phase 3 turns out to be
harder than estimated — specifically, if the completion popover fights
`NSTextView`'s input handling — switch the panel's *content view only* to a warm
`WKWebView` hosting CodeMirror 6 (Option B′), keeping the panel, hotkey,
notifications, and `CaptureCore` unchanged. Structuring `CaptureCore` as a
UI-free module (R13) makes that swap cheap, which is the point of the boundary.

---

## 10. Phased Implementation Plan

| Phase | Scope | Delivers |
| --- | --- | --- |
| **0** | Measure on the Mac: `zsh -lc` cost, `bob` spawn cost, current pop-up latency | A real baseline; validates §2.3 |
| **1** | `bob-cli`: `capture-parse` + `capture-complete`, JSON + tests | Grammar as data (R10) |
| **2** | Swift skeleton: `LSUIElement`, LaunchAgent, Carbon hotkey, non-activating `NSPanel`, plain multi-line `NSTextView`, submit → `bob capture`, `UNUserNotificationCenter` | **R1, R5, R6, R7** — already better than today |
| **3** | Span highlighting, completion popover, live preview pane, inline status strip | **R2, R3, R4, R12** |
| **4** | Cutover: remove the Hammerspoon binding and delete `task_capture.lua` + its specs | One capture path, one grammar |
| **5** | Polish: recent-capture history, notification actions (Open note / Undo), preferences, clipboard-marker affordances | R11, R14 |

Phase 2 is the meaningful milestone — it fixes four of the five complaints and is
independently useful even if Phase 3 slips.

---

## 11. Risks and Open Questions

| Risk / question | Notes |
| --- | --- |
| **Mac latency unmeasured** | All numbers here are from athena, not the MacBook. Phase 0 exists to fix this. If the Mac's `bob` spawn is much slower (cold vault, Spotlight indexing, iCloud), reconsider a resident daemon. |
| **Clipboard markers (R9)** | `bob capture` reads the clipboard *itself* (`pbpaste`, Clipy SQLite). Spawned from a non-activating app this should be fine, but a `%` capture triggered from a background process is worth an explicit Phase 2 test. Same for `--dry-run` — confirm it does not consume clipboard history. |
| **Preview side effects** | Verify `--dry-run` is genuinely side-effect-free for *every* mode, especially `@route:block-id` (which validates two notes) and `%N` (which reads Clipy). Per-keystroke invocation makes any hidden write catastrophic. |
| **Pomodoro-linked capture** | `@route:block-id` fails loudly when there is no open Pomodoro entry or multiple open timed entries. The panel must surface that clearly and keep the text (R8), not just flash a banner. |
| **`capture-parse` and drift** | The endpoint must be generated from the same parser as `capture`, not a parallel code path — otherwise the duplication just moves inside `bob-cli`. |
| **Hotkey collision during migration** | `RegisterEventHotKey` fails silently-ish if ⌃⇧⌘I is taken. Bind a temporary combination in Phases 2–3. |
| **Signing certificate expiry** | Free Personal Team Apple Development certificates expire (typically ~1 year). A re-sign will be needed; note it in the repo README so a future silent notification failure is not re-diagnosed from scratch. |
| **Accessibility permission** | Should not be needed with Carbon hotkeys. Confirm empirically in Phase 2 — if a prompt appears, something is using `NSEvent` monitoring. |
| **macOS 27 upgrade** | Ships ~September 2026. Liquid Glass APIs are stable, but re-verify panel behavior after upgrading. |
| **Losing the Hammerspoon test suite** | `tests/hammerspoon/task_capture_spec.lua` encodes real grammar edge cases. Port its cases into the `bob-cli` `capture-parse` tests before deleting it in Phase 4. |

---

## 12. Sources

**Current implementation** (read via `sase repo open chezmoi` and this workspace):
`home/dot_hammerspoon/init.lua`, `home/dot_hammerspoon/task_capture.lua`,
`src/native/capture.rs`, `src/native/capture_targets.rs`.

**Floating panels / Spotlight-style windows**
- [SwiftUI Floating Panel: NSPanel Patterns for macOS Apps — Fazm](https://fazm.ai/blog/swiftui-floating-panel)
- [Make a floating panel in SwiftUI for macOS — Cindori](https://cindori.com/developer/floating-panel)
- [Create a Spotlight/Alfred like window on macOS with SwiftUI — Markus Bodner](https://www.markusbodner.com/til/2021/02/08/create-a-spotlight/alfred-like-window-on-macos-with-swiftui/)
- [Creating a Spotlight-like floating panel in Swift — Whid](https://whid.eu/2022/06/03/chapter-6-creating-a-spotlight-like-floating-panel-in-swift/)
- [SwiftUI Menu Bar App With a Floating Window: Best Practices — Fazm](https://fazm.ai/blog/swiftui-menu-bar-app-floating-window-best-practices)

**Hammerspoon notification limitations**
- [hs.notify.show doesn't work — Hammerspoon issue #3631](https://github.com/Hammerspoon/hammerspoon/issues/3631)
- [WIP hs.notify updates — Hammerspoon PR #509](https://github.com/Hammerspoon/hammerspoon/pull/509)
- [Hammerspoon docs: hs.notify](https://www.hammerspoon.org/docs/hs.notify.html)

**Notifications and code signing**
- [UNUserNotificationCenter — Apple Developer Documentation](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter)
- [Is it possible to use UNUserNotificationCenter… — Apple Developer Forums](https://developer.apple.com/forums/thread/679326?parentId=708042022)
- [Gatekeeper and code signing — Apple Developer Forums](https://developer.apple.com/forums/thread/740680)
- [Code Signing on macOS: What Developers Need to Know — Xojo](https://blog.xojo.com/2026/03/04/code-signing-on-macos-what-developers-need-to-know-part-1/)
- [apple-codesign certificate management — indygreg/apple-platform-rs](https://github.com/indygreg/apple-platform-rs/blob/main/apple-codesign/docs/apple_codesign_certificate_management.rst)

**Global hotkeys**
- [How to properly realize global hotkeys on macOS? — Apple Developer Forums](https://developer.apple.com/forums/thread/735223)
- [GlobalShortcut: switch from NSEvent to Carbon RegisterEventHotKey — electrobun issue #334](https://github.com/blackboardsh/electrobun/issues/334)
- [Magnet — DivineDominion](https://github.com/DivineDominion/Magnet)
- [Creating a global configurable shortcut for macOS apps in Swift — DEV](https://dev.to/mitchartemis/creating-a-global-configurable-shortcut-for-macos-apps-in-swift-25e9)

**Text editing / syntax highlighting**
- [STTextView (TextKit 2) — krzyzanowskim](https://github.com/krzyzanowskim/STTextView)
- [Sourceful — twostraws](https://github.com/twostraws/Sourceful)
- [HighlightedTextEditor — kyle-n](https://github.com/kyle-n/HighlightedTextEditor)
- [Wrap NSTextView with TextKit 2 into NSViewRepresentable — Apple Developer Forums](https://developer.apple.com/forums/thread/682459)

**Alternative frameworks**
- [tauri-nspanel — ahkohd](https://github.com/ahkohd/tauri-nspanel)
- [tauri-macos-spotlight-example — ahkohd](https://github.com/ahkohd/tauri-macos-spotlight-example)
- [tauri-plugin-spotlight — zzzze](https://github.com/zzzze/tauri-plugin-spotlight)
- [Global Shortcut plugin — Tauri v2](https://v2.tauri.app/plugin/global-shortcut/)
- [macOS Code Signing — Tauri](https://v2.tauri.app/distribute/sign/macos/)
- [How the Raycast API and extensions work — Raycast Blog](https://www.raycast.com/blog/how-raycast-api-extensions-work)
- [A Technical Deep Dive Into the New Raycast — Raycast Blog](https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast)
- [Menu Bar Commands — Raycast API](https://developers.raycast.com/api-reference/menu-bar-commands)

**Build and packaging**
- [Swift Bundler: create macOS apps with SwiftPM instead of Xcodeproj — Swift Forums](https://forums.swift.org/t/swift-bundler-create-macos-apps-with-swiftpm-instead-of-xcodeprojs/56790)
- [Building an .app from a Swift Package Manager Executable for macOS — Swift Forums](https://forums.swift.org/t/building-an-app-from-a-swift-package-manager-executable-for-macos/64409)
- [How to build macOS apps using only the Swift Package Manager — The.Swift.Dev](https://theswiftdev.com/how-to-build-macos-apps-using-only-the-swift-package-manager/)

**Prior art**
- [Collector — Obsidian Quick Capture App for macOS](https://github.com/juliandeans/Collector)
- [NotesBar — Obsidian Forum](https://forum.obsidian.md/t/notesbar-lightning-fast-access-to-your-obsidian-notes-from-the-macos-menu-bar/101146)
- [Obsidian Smart Capture — Raycast Store](https://www.raycast.com/millin_gabani/obsidian-smart-capture)

**Platform status**
- [Apple Releases macOS Tahoe 26.6 — MacRumors](https://www.macrumors.com/2026/07/27/apple-releases-macos-tahoe-26-6/)
- [macOS 27 Will Mark the End of an Era — MacRumors](https://www.macrumors.com/2026/05/26/macos-27-will-mark-the-end-of-an-era/)
- [Apple introduces a delightful and elegant new software design — Apple Newsroom](https://www.apple.com/newsroom/2025/06/apple-introduces-a-delightful-and-elegant-new-software-design/)

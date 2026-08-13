# Replacing the Hammerspoon Capture Pop-up with `bob-mac-capture`

- **Date:** 2026-08-13
- **Repo under design:** `bobs-org/bob-mac-capture` (public, default branch `master`,
  one commit `e8e2a82` with an empty `README.md` — *not* empty as both source reports
  assumed)
- **Question:** What is the best way to build a Mac app that replaces the Hammerspoon
  `⌃⇧⌘I` capture pop-up and fixes its multi-line, completion/highlighting, latency,
  notification, and aesthetic problems?
- **Sources merged:** Researcher A (`research.0h.cdx`) — partial, see
  [`__a`](bob_mac_capture_replacement__a.md) for why; Researcher B (`research.0h.cld`)
  — [`__b`](bob_mac_capture_replacement__b.md); plus lead-researcher verification of
  every load-bearing claim against source.

**Recommendation in one line:** build a native Swift `LSUIElement` app around a
pre-warmed non-activating `NSPanel`, move the capture grammar into `bob-cli` as JSON
endpoints, and treat **code signing plus a `willPresent` delegate** — not the panel
style — as the actual fix for notifications.

---

## 0. What This Consolidation Changes

Both researchers independently landed on the same architecture (native Swift,
persistent panel, grammar in `bob-cli`, direct subprocess). That agreement is
meaningful and I did not disturb it. What I changed:

| # | Finding | Effect |
| --- | --- | --- |
| 1 | **Code signing is *required* for `UNUserNotificationCenter`.** Neither report treated this as a root cause; B filed it as a §5.4 "caveat". | Promoted to a co-equal root cause of the notification failure and a Phase-2 gate. |
| 2 | **The canonical foreground-suppression fix is the `willPresent` delegate**, not the non-activating panel. B's report calls the panel "the sign the architecture is right". | Corrected: the delegate is mandatory and one line; the panel is a good but *secondary* mitigation. |
| 3 | **macOS 26 `TextEditor` binds directly to `AttributedString`** (new at WWDC25). Neither report knew this. | Cuts the main cost of the recommended option; strengthens native Swift over Tauri/CodeMirror. |
| 4 | **SASE agents run on Linux (athena); there is no Swift or macOS toolchain here.** Neither report addressed how this gets built. | New §7. Reframes the headless-core boundary from good taste to a workflow requirement, and identifies free unmetered macOS CI as the enabler. |
| 5 | **`--dry-run` is verified write-safe but *does* read the clipboard.** B listed this as an unresolved risk. | Resolved with a concrete mitigation (`--no-clip` on the preview path). |
| 6 | `SMAppService` supersedes hand-written LaunchAgent plists (macOS 13+). | Replaces B's `launchd`/`KeepAlive` suggestion. |

Everything in §1–§2 below was re-verified against the actual files; the line numbers in
B's report are accurate.

---

## 1. What Exists Today (verified)

| File | Lines | Role |
| --- | --- | --- |
| `home/dot_hammerspoon/init.lua` | 1653 ✓ | Hotkey, WebView prompt, HTML/CSS/JS, `hs.chooser` pickers, `bob` staging, notifications |
| `home/dot_hammerspoon/task_capture.lua` | 353 ✓ | A **second, independent implementation** of the `bob capture` marker grammar, in Lua |
| `tests/hammerspoon/task_capture_spec.lua` | 487 | Busted specs encoding real grammar edge cases |

Verified mechanics:

- **Hotkey:** `hs.hotkey.bind({ "cmd", "shift", "ctrl" }, "i", nil, ...)` — `init.lua:1329` ✓
- **Input widget:** `<input id="capture" type="text" …>` — `init.lua:163` ✓ (single-line by definition)
- **Window:** `hs.webview.new(...)` with `windowStyle({ "titled", "closable" })` and
  `deleteOnClose(true)` — `init.lua:1305`–`1312` ✓. A *titled, closable* window, so it
  activates Hammerspoon, and it is **rebuilt from scratch on every press**.
- **Subprocess:** `hs.task.new("/bin/zsh", …, { "-lc", command, "bob-capture" })` —
  `init.lua:737`, `743` ✓. A **login shell per stage**. (A second `zsh -lc` path exists
  for the Pomodoro menubar at `init.lua:1568`/`1606`.)
- **Notifications:** `notifyWithAttributes` (`init.lua:578`) wraps `hs.notify.new` in
  `pcall`, falls back to `hs.notify.show`, and schedules a 1-second `presented()` probe
  that logs "delivered but not presented". That defensive ladder is itself evidence the
  banners were already unreliable.

---

## 2. Root Causes of the Five Complaints

### 2.1 No multi-line — the widget, *and* a semantic decision

`<input type="text">` is single-line. But swapping in a `<textarea>` or an `NSTextView`
only fixes composing, because **`bob capture` collapses newlines**:

```rust
// src/native/capture.rs:1623
fn normalize_task_text(raw_text: &str) -> String {
    raw_text.split_whitespace().collect::<Vec<_>>().join(" ")
}
```

Its own test asserts `" \n buy\t  milk \r\n @groceries  "` → `"buy milk @groceries"`
(`capture.rs:2709`). Both researchers independently caught this; A was right to call it
"a product decision … rather than hiding it as an implementation detail". See §4.1.

### 2.2 No completion/highlighting — the duplicated grammar, not the widget

The complaint is *partly* inaccurate as stated, and the nuance matters. Completion
exists, but is **staged and modal**: type a bare `@`, submit, and only then does an
`hs.chooser` appear. What is missing is **inline, as-you-type** completion,
highlighting, and hinting.

The blocker is architectural. `task_capture.lua` re-implements the marker grammar in Lua
so the Lua side can decide which picker to show — a second copy of what lives in
`capture.rs`. Any client that wants to *highlight* the syntax needs a third copy.

### 2.3 Slow pop-up — the login shell plus per-press WebView construction

Three compounding costs, descending by likely impact:

1. **`zsh -lc` per stage** sources `.zprofile` + `.zshrc`. Measured on athena: 95 ms.
   On a Mac with Homebrew shims and version-manager hooks, 250–600 ms is typical, and
   *every picker stage pays it again*.
2. **Cold `WKWebView` construction** on every press (`hs.webview.new` + `:html(...)` +
   JS parse + first paint) — tens to low-hundreds of ms. Invisible when warm, glaring
   when cold, which is exactly the "sometimes".
3. Hammerspoon's Lua runtime contending with the Pomodoro menubar timers in the same file.

The binary is not the bottleneck: `bob capture-targets --format json` = 11 ms,
`bob capture --dry-run --format json` = 5 ms.

> **Caveat, carried from B and worth repeating:** every number here is from athena
> (Linux, warm cache, local vault), *not* the MacBook. The relative conclusion — the
> login shell costs 10–100× the binary — is robust; the absolute budget is not. Phase 0
> exists to fix this.

### 2.4 Missing notifications — **three** causes, and B/A named only two

This is the complaint the user has failed to fix several times, so it deserves the most
precision. There are three independent causes, each sufficient on its own:

1. **`hs.notify` sits on deprecated `NSUserNotification`.** Hammerspoon still ships
   `NSUserNotification` in `extensions/notify/libnotify.m`; the migration to
   `UNUserNotificationCenter` is open and unfinished, with maintainers noting it "might
   end up requiring an entirely new approach/module and some changes in the core
   application" ([PR #509](https://github.com/Hammerspoon/hammerspoon/pull/509),
   [issue #3631](https://github.com/Hammerspoon/hammerspoon/issues/3631)).
2. **macOS suppresses banners from the *active* app by default.** The capture window is
   a titled `hs.webview`, so pressing the hotkey makes Hammerspoon frontmost. The code
   tries to restore the previous app (`restoreTaskCaptureApp`, `init.lua:253`), racing
   "capture completes → notify" against "previous app is actually frontmost again" — a
   textbook source of *intermittent* banners, matching the "sometimes" precisely.
3. **Attribution.** Everything is attributed to Hammerspoon, so per-app Focus and
   notification settings apply to *all* of Hammerspoon, not to capture.

**The correction that matters.** B concluded that a non-activating panel fixes cause 2
"as a side effect … which is the sign the architecture is right." That overstates it.
The documented, canonical fix for foreground suppression is the delegate:

```swift
func userNotificationCenter(_ c: UNUserNotificationCenter,
                            willPresent n: UNNotification,
                            withCompletionHandler h: @escaping (UNNotificationPresentationOptions) -> Void) {
    h([.banner, .sound, .list])   // without this, banners are hidden while the app is active
}
```

This is required regardless of panel style, costs one line, and does not depend on
getting activation semantics exactly right. It also survives the very common case where
you *do* end up activating (see §5.2 — several well-known Spotlight-like palettes call
`NSApp.activate()` from `becomeKey()` on purpose). Ship the delegate first; treat the
non-activating panel as a valuable second mitigation that additionally removes the
focus-restore race.

**And the cause nobody flagged as a cause: signing.** `UNUserNotificationCenter`
**requires a signed executable** — unlike the old `NSNotification` path. An unsigned or
improperly-bundled build silently gets nothing. An ad-hoc signature (`codesign -s -`) is
sufficient today; an Apple Development certificate is recommended and may be required by
future macOS. Practically this means the app must be a real `.app` bundle, with a stable
bundle identifier, installed at a stable path. Get this wrong and you reproduce exactly
the symptom you are trying to escape — silence — with no error.

### 2.5 Ugly — HTML in a Lua string literal

The UI is hand-written HTML/CSS embedded in a Lua heredoc (`init.lua:56`–`250`). It
cannot inherit Tahoe's Liquid Glass materials, vibrancy, dynamic type, accent color, or
Dark Mode transitions, and every tweak is a string edit plus a Hammerspoon reload.

---

## 3. Requirements

**Must have**

| # | Requirement |
| --- | --- |
| R1 | Multi-line input with an explicit submit key distinct from newline |
| R2 | Inline, as-you-type highlighting of the marker grammar |
| R3 | Inline completion for routes, sections, task block IDs — no modal stage |
| R4 | Live preview of the exact line and destination file |
| R5 | Reliable success **and** failure notification, attributed to this app |
| R6 | Sub-100 ms perceived pop-up latency, cold, every time |
| R7 | Native appearance (Liquid Glass, vibrancy, Dark Mode, accent color) |
| R8 | Never lose typed text on failure |
| R9 | Clipboard markers (`%`, `%N`, `%header`) keep working, incl. Clipy history |

**Should have:** R10 single source of truth for the grammar · R11 notification actions
(Open note, Undo) · R12 in-panel confirmation so correctness never *depends* on
Notification Center · R13 headless-testable core · R14 recent-capture history.

**Non-goals:** App Store distribution, cross-platform, re-implementing vault logic.

---

## 4. Cross-Cutting Decisions (settle these before picking a framework)

### 4.1 What should multi-line *mean*?

| Option | Behavior | Verdict |
| --- | --- | --- |
| **A. Cosmetic wrap** | Multi-line for editing comfort; newlines collapse on submit | Ship this — satisfies R1 with zero `bob-cli` change |
| **B. Line = child bullet** | First line is the task, later lines become child bullets | Design for this — already the semantics of the `%N` clipboard path |
| **C. Line = separate capture** | Each line its own capture, sharing trailing markers | Defer — partial mid-batch failure is hard to reason about |

**Ship A, design for B, defer C.** Both researchers converged here independently.

### 4.2 Where the grammar lives — *the most important decision*

It lives in two places today (Rust + Lua). A new client must not make it three.
Re-implementing in Swift is the current pain amplified; linking `bob-cli` as a
`staticlib` over a C ABI buys zero-latency at the cost of a stable C header and
`aarch64-apple-darwin` cross-compilation. **Add JSON endpoints and spawn the binary** —
5 ms measured, no ABI, no cross-compilation.

Two additions to `bob-cli`, following `sase/memory/cli_rules.md` (alphabetical ordering,
a short alias for every public long option, colored human output):

1. **`bob capture-parse`** — tokenize without executing; returns byte-offset spans with
   kinds plus diagnostics, so the client highlights from authoritative data.
2. **`bob capture-complete --cursor <N>`** — cursor-aware candidates plus the replacement
   range, so the client never decides *when* completion applies.

`bob capture --dry-run --format json` already returns the destination path, route label,
exact rendered Markdown line, resolved scheduled date, and whether the note would be
created or inserted into (`capture.rs:2491`). **The preview engine is already built.**

This makes the Mac app a thin renderer, lets `task_capture.lua` be deleted, and benefits
any future client (Raycast extension, iOS Shortcut, `zsh` completion) for free.

> **Guard against drift:** `capture-parse` must be generated from the same parser as
> `capture`, not a parallel code path — otherwise the duplication merely moves inside
> `bob-cli`. Port the cases in `tests/hammerspoon/task_capture_spec.lua` (487 lines of
> real edge cases) into the `capture-parse` tests *before* deleting it.

### 4.3 Talking to `bob`

- **Never use a login shell.** Resolve `bob` once at launch (configured absolute path,
  falling back to a probe of `~/.cargo/bin`, `/opt/homebrew/bin`, `/usr/local/bin`) and
  exec it directly with an explicit minimal environment. This alone likely removes most
  of the latency.
- **Pass text as `argv`,** never through a shell string. The Lua code is already careful
  here (`init.lua:709`); preserve the property.
- **Cache `capture-targets`** at launch, on panel show, and on an FSEvents watch of the
  vault root. Route completion then costs zero spawns.
- **Debounce preview at ~40–60 ms** and cancel in-flight processes on new keystrokes.
- **Use `--no-clip` (`-n`) on the live-preview path.** See §4.4.
- **A daemon or FFI is premature.** Revisit only if measured Mac latency blows R6.

### 4.4 `--dry-run` safety — resolved

B flagged "verify `--dry-run` is genuinely side-effect-free" as an open risk, noting
that per-keystroke invocation makes any hidden write catastrophic. **Verified:**

- **Writes: safe.** Every filesystem mutation is behind a single choke point,
  `if !request.dry_run {` at `capture.rs:568`, covering both the clip-file save and
  `write_capture_plan`. Everything before it is planning and validation only.
- **Clipboard: *not* inert.** `clip_plan` is constructed at `capture.rs:477`, *before*
  that guard, calling `read_clipboard()` (`:480`, `:494`) and `read_clipboard_history()`
  (`:507`). So a `--dry-run` on text containing `%` markers spawns `pbpaste` and opens
  the Clipy SQLite database on **every keystroke**. The Clipy handle is opened read-only
  (`capture_clip.rs:319`), so there is no corruption risk — but it is wasteful and adds
  unbounded latency to the typing path.

**Mitigation:** pass `--no-clip` for live preview (it keeps `%…` markers literal), and
run the full clipboard-resolving `--dry-run` only on an explicit preview request or at
submit. This keeps R9 intact while making per-keystroke preview cheap.

### 4.5 Notifications — the full recipe

All five, in order of how silently they fail:

1. **Ship a signed `.app` bundle** with a stable bundle ID (`org.bobs.bob-mac-capture`)
   at a stable install path. Ad-hoc signing works; a free Apple ID "Personal Team" Apple
   Development certificate is better and needs no paid membership. Notarization is only
   for distribution. *Without this, `UNUserNotificationCenter` is silent by design.*
2. **Implement `UNUserNotificationCenterDelegate.willPresent`** returning
   `[.banner, .sound, .list]` (§2.4). Set `center.delegate` before requesting
   authorization.
3. **Request and then *report* authorization.** A Settings pane that shows the live
   authorization status and offers a test notification turns the next silent failure into
   a five-second diagnosis instead of another multi-hour re-investigation. This is the
   single highest-value item for the user's stated history with this bug.
4. **Prefer a non-activating panel** so the app never becomes frontmost — this removes
   the focus-restore race and is good design independently.
5. **Never depend on Notification Center for correctness (R12).** Show the result inline:
   a success flash with the destination label, or an error banner with the panel staying
   open and the text preserved (R8). The system notification is a convenience.

Add `UNNotificationAction`s for **Open note** (`obsidian://open?path=…`, already built at
`init.lua:499`) and later **Undo**.

### 4.6 Global hotkey

Use **Carbon `RegisterEventHotKey`** (directly or via
[Magnet](https://github.com/DivineDominion/Magnet)). Nominally deprecated but stable,
shipping in VS Code/Slack/Electron, and — critically — it does **not** require
Accessibility permission, because it registers interest in one combination rather than
observing all input. `NSEvent.addGlobalMonitorForEvents` *does* require Accessibility and
is strictly worse here.

**Migration:** `RegisterEventHotKey` fails if the combination is already claimed. Remove
the Hammerspoon binding at `init.lua:1329` before ⌃⇧⌘I will reach the new app, and bind a
temporary combination (e.g. ⌃⇧⌘O) during Phases 2–3 for side-by-side comparison.

### 4.7 Launch at login

Use **`SMAppService`** (macOS 13+), Apple's replacement for `SMJobBless` /
`SMLoginItemSetEnabled` and for hand-written LaunchAgent plists. It registers the app as
a login item, surfaces it in System Settings → Login Items where the user can see and
manage it, and avoids the "mystery plist in `~/Library/LaunchAgents`" failure mode. This
supersedes the `launchd` + `KeepAlive` approach in report B.

### 4.8 Latency budget (R6)

| Cost | Today | Target | How |
| --- | --- | --- | --- |
| App start | n/a (Hammerspoon resident) | 0 ms | `LSUIElement` accessory app, `SMAppService` login item |
| Panel construction | WebView built per press | 0 ms | Build the `NSPanel` once at launch; `orderFrontRegardless()` on hotkey |
| Shell startup | ~95 ms measured (250–600 ms likely on Mac) | 0 ms | Spawn `bob` directly |
| Route list | 11 ms per picker stage | 0 ms | Cached at launch + FSEvents refresh |
| Preview | n/a | ~5 ms, debounced, off main thread | `--dry-run --no-clip --format json` |

Perceived pop-up latency becomes a single `orderFrontRegardless()` — one frame.

---

## 5. Option Comparison

| # | Option | Multi-line | Highlight + inline completion | Latency | Notifications | Native look | Effort |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | Improve Hammerspoon in place | `<textarea>` — easy | CodeMirror in the WebView — possible | Shell cost removable; WebView warmable | ❌ Still `hs.notify`, still Hammerspoon-attributed | ❌ HTML in a Lua string | S |
| **B** | **Native Swift (AppKit + SwiftUI)** | ✅ Native | ✅ Cheaper than either report assumed — see §5.1 | ✅ Best possible | ✅ `UNUserNotificationCenter` | ✅ Free, incl. Liquid Glass | M |
| B′ | Swift shell + `WKWebView`/CodeMirror 6 | ✅ | ✅ Essentially free | ✅ (warm WebView) | ✅ | ⚠️ Chrome native, content emulated | M |
| C | Tauri v2 (`tauri-nspanel`) | ✅ | ✅ CodeMirror 6 | ⚠️ ~60–100 MB resident; fine warm | ✅ via plugin | ⚠️ CSS-emulated | M |
| D | Electron | ✅ | ✅ | ❌ ~150 MB bundle, ~200 MB RSS | ✅ | ❌ | M |
| E | Raycast extension | ⚠️ `Form.TextArea` only | ❌ No custom highlighting in Raycast's input | ⚠️ +50–100 ms load | ✅ (Raycast-attributed) | ✅ Raycast's, not yours | S |
| F | Alfred workflow | ❌ Single-line bar | ❌ | ✅ | ⚠️ | ✅ Alfred's | S |
| G | Pure Rust GUI (egui/iced) | ✅ | ⚠️ Hand-built | ✅ | ❌ Needs `objc2` glue anyway | ❌ | L |
| H | Obsidian plugin + global hotkey | ✅ | ✅ (Obsidian ships CodeMirror) | ❌ Requires Obsidian running | ⚠️ | ❌ | M |

**Why the losers lose.** **E (Raycast)** is the tempting shortcut and the wrong tool:
extensions render *Raycast's* components, so you cannot put a custom highlighter or
token-aware popup inside its input — a lateral move on R2/R3 plus a hard dependency on a
third-party commercial app. (Keep it as a *thin extra entry point* later, consuming the
same JSON endpoints. Researcher A rated it a useful prototype path; that is fair, but the
prototype teaches you little about the parts that are actually hard.) **F** fails R1
outright. **D** buys nothing over C at 10× the memory. **G** is superficially attractive
because `bob-cli` is Rust, but you would still write Objective-C bridging for the panel,
hotkey, and notifications — all the hard parts — without gaining a native text system.
**H** couples capture to Obsidian being open, defeating the purpose. **A** is the
cheapest path and genuinely *can* fix multi-line, highlighting, and latency — but it
cannot fix notifications (cause 1 is upstream; cause 2 is inherent to a titled
`hs.webview`) or the aesthetics, and both are explicit complaints.

### 5.1 The real contest: B vs B′/C — and a fact that decides it

Both researchers picked native Swift; B's report was scrupulous about the counter-argument
and I want to keep it visible: **CodeMirror 6 hands you highlighting, an autocomplete
popup, hover tooltips, and multi-line editing essentially free.** That is a real
advantage and B was right not to wave it away. B's counter was that once `capture-parse`
returns spans, CodeMirror's edge "shrinks from an entire editor to a list widget".

That argument is now stronger than either researcher knew. **At WWDC25, SwiftUI's
`TextEditor` gained first-class `AttributedString` binding, available on macOS 26+.** It
binds to an `AttributedString` and an `AttributedTextSelection`, with built-in formatting
shortcuts and menu support. Applying `capture-parse` spans becomes writing attribute runs
into an `AttributedString` — not subclassing `NSTextStorage` and hand-managing TextKit.
B estimated 600–900 LOC for a custom `NSTextView` highlighter; on macOS 26 the
highlighting layer is plausibly a fraction of that, and the remaining custom work is the
completion popover.

So: the JS-toolchain, bridge, WebView, and emulated-material costs of B′/C now buy
noticeably less than they did a year ago. **B wins, with more margin than the source
reports gave it.**

**Pre-registered fallback (kept from B):** if the completion popover fights the text
view's input handling, swap the panel's *content view only* to a warm `WKWebView` hosting
CodeMirror 6, keeping the panel, hotkey, notifications, and `CaptureCore` unchanged.
Structuring `CaptureCore` as a UI-free module (R13) is what makes that swap cheap.

---

## 6. Recommended Architecture

```
┌───────────────────── bob-mac-capture (Swift, LSUIElement) ────────────────────┐
│  AppDelegate ── HotKeyManager (Carbon RegisterEventHotKey, ⌃⇧⌘I)              │
│      ├── CapturePanel : NSPanel (.nonactivatingPanel set AT INIT, .floating)  │
│      │     └── NSHostingView                                                  │
│      │           ├── CaptureEditor   (TextEditor + AttributedString, macOS 26)│
│      │           │     ├── SpanHighlighter   ← bob capture-parse              │
│      │           │     └── CompletionPopover ← bob capture-complete           │
│      │           ├── PreviewPane   ← bob capture --dry-run --no-clip -f json  │
│      │           └── StatusStrip   (inline success / error — R12)             │
│      ├── NotificationService (UNUserNotificationCenter + willPresent delegate │
│      │                        + authorization status surfaced in Settings)    │
│      └── MenuBarExtra (status, recent captures, preferences)                   │
│                                                                               │
│  ═══ CaptureCore — pure Swift, NO AppKit: headless-testable AND Linux-        │
│      buildable (R13, §7). BobClient resolves the binary once, spawns with an   │
│      explicit env, cancels in-flight work, caches capture-targets, FSEvents.   │
└───────────────────────────────────────────────────────────────────────────────┘
                                  │ argv + JSON on stdout
                                  ▼
              bob-cli  (single source of truth for the grammar)
                capture · capture-targets · capture-sections ·
                capture-tasks · capture-parse* · capture-complete*   (* = new)
```

**Panel configuration** — the established Spotlight recipe:

```swift
styleMask:          [.nonactivatingPanel, .titled, .fullSizeContentView, .resizable]
isFloatingPanel:    true
level:              .floating
collectionBehavior: [.canJoinAllSpaces, .fullScreenAuxiliary]
titlebarAppearsTransparent = true
titleVisibility            = .hidden
becomesKeyOnlyIfNeeded     = false   // the editor must take keystrokes immediately
```

> **Set `.nonactivatingPanel` at initialization and never toggle it afterwards.** Adding
> or removing the flag on a live panel desynchronizes AppKit's style mask from the
> WindowServer's `kCGSPreventsActivationTagBit`: the window looks focused but **typing
> silently does nothing**. Given the user's history with silent failures in this exact
> workflow, this is a trap worth naming explicitly.

`.canJoinAllSpaces` + `.fullScreenAuxiliary` means capture works over a full-screen app —
something the current WebView handles poorly.

**Editor key bindings:** `⏎` submit · `⇧⏎`/`⌥⏎` newline · `⇥`/`⌃N`/`⌃P` accept and
navigate completion · `⎋` dismiss completion, then dismiss panel · `⌘⏎` submit and open
the target note in Obsidian.

**Repo layout** (`bobs-org/bob-mac-capture`, default branch `master`):

```
Package.swift               # SwiftPM; no .xcodeproj checked in
Sources/
  CaptureCore/              # BobClient, models, span/completion decoding — pure Swift
  BobMacCapture/            # AppDelegate, CapturePanel, editor, notifications
Tests/CaptureCoreTests/     # swift-testing; fakes the bob binary with a fixture script
Resources/Info.plist        # LSUIElement=1, bundle id, usage strings
Scripts/bundle.sh           # assemble .app, codesign, install
.github/workflows/ci.yml    # macOS runner: build + test  (§7)
justfile                    # build / run / install / test — mirrors bob-cli
```

Build with **SwiftPM plus a bundling script** (or
[Swift Bundler](https://github.com/stackotter/swift-bundler)) rather than a checked-in
`.xcodeproj`: diffable, scriptable, consistent with how `bob-cli` builds via `just`.

**Target macOS 26.0+.** macOS Tahoe 26.6.x is current (August 2026); macOS 27 "Golden
Gate" ships ~September 2026 and is Apple-silicon-only. Targeting 26 gives Liquid Glass
*and* the `AttributedString` `TextEditor` that §5.1 depends on.

---

## 7. The Constraint Neither Report Addressed: You Build This From Linux

SASE agents for this project run on **athena, a Linux home server**. Verified there:
`cargo` 1.97.1 and `node` v22.14.0 are installed; **`swift`, `swiftc`, and `xcodebuild`
are not, and AppKit/SwiftUI/UserNotifications cannot exist there at all.** So an agent
cannot build, run, or screenshot the app it is writing. This is a first-order workflow
constraint, and it cuts two ways:

- **Against native Swift:** it is the one option whose UI layer is *entirely* unbuildable
  and untestable by your agents. Tauri (option C) would at least let the Rust core and
  the whole TS/CodeMirror editor be typechecked and unit-tested on athena today, with no
  new toolchain. That is a genuine point for C that neither report weighed, and it is the
  strongest remaining argument against the recommendation.
- **For the recommendation anyway,** because two things defuse it:
  1. **`CaptureCore` is pure Swift with no AppKit, so it builds and tests on Linux** with
     a swift.org toolchain installed on athena. Put the parsing, JSON decoding, process
     orchestration, caching, cancellation, and error handling there and agents can do
     real, verified work on the majority of the logic. This turns R13 from an
     architectural nicety into the thing that makes the project tractable — and it
     matches Researcher A's instinct that the Hammerspoon state machine should move
     "into a testable app".
  2. **`bob-mac-capture` is a public repo, and GitHub-hosted standard runners are free
     and unmetered for public repositories** — including Apple-silicon macOS runners. So
     CI can build the full app and run the AppKit-dependent tests on every push at zero
     cost. Agents push; macOS CI is the compiler and test bed they lack.

**Concrete implication for sequencing:** stand up `.github/workflows/ci.yml` on a macOS
runner *in Phase 1*, before there is much code. Without it, every UI change is blind, and
"it compiles on my Mac" becomes the only verification loop. With it, the split is clean:
agents own `CaptureCore` and CI-verified builds; the user owns the on-Mac interaction
testing that genuinely requires a human at a keyboard (permission prompts, banner
behavior, focus, Spaces).

---

## 8. Recommendation

**Build a native Swift `LSUIElement` menu-bar app (Option B), and move the capture
grammar into `bob-cli` as JSON endpoints.** Concretely:

1. **`bob-cli`:** add `bob capture-parse` (spans + diagnostics) and
   `bob capture-complete --cursor N`, both `--format json`, per `cli_rules.md`. Keep
   `--dry-run --format json` as the preview source; it already returns everything needed.
2. **`bob-mac-capture`:** Swift `LSUIElement` app; pre-warmed non-activating `NSPanel`
   (flag set at init); macOS 26 `TextEditor` bound to an `AttributedString` highlighted
   from `capture-parse` spans; completion popover fed by `capture-complete`; preview pane
   fed by `--dry-run --no-clip`; inline status strip; `UNUserNotificationCenter` with a
   `willPresent` delegate and an "Open note" action.
3. **Signing:** real `.app` bundle, stable bundle ID, stable install path, free Personal
   Team Apple Development certificate. **This is a prerequisite for notifications, not a
   polish item.**
4. **Hotkey:** Carbon `RegisterEventHotKey`, after removing the Hammerspoon binding at
   `init.lua:1329`. Temporary combination during migration.
5. **Login item:** `SMAppService`, not a hand-written LaunchAgent plist.
6. **Process model:** spawn `bob` directly with an explicit environment. **No login
   shell, ever.**
7. **Build loop:** pure-Swift `CaptureCore` (Linux-testable) + free macOS CI from Phase 1.

**Why this rather than the cheaper options.** Every complaint traces to something
structural. Single-line input is the widget. Missing inline completion is the duplicated
grammar. Slowness is the login shell plus per-press WebView construction. Missing
notifications is a deprecated API, *plus* a focus-stealing window, *plus* — most likely
the reason previous attempts failed — the fact that the modern notification API refuses
to work at all outside a signed bundle, which Hammerspoon can never give you. Ugliness is
HTML in a Lua string. A native signed app removes all five causes instead of patching
symptoms.

**Why not Tauri/CodeMirror.** The parse-endpoint decision is required in *every* option,
and it is what makes CodeMirror's machinery mostly redundant; macOS 26's rich-text
`TextEditor` shrinks the remaining gap further. B is less total code across the two repos,
in one language, with native materials free. The honest cost is §7: your agents cannot
build the UI locally. Free macOS CI plus a Linux-buildable core is the answer to that, and
it is a better trade than carrying a JS toolchain and emulated materials forever.

**Confidence.** High on the diagnosis (every claim verified against source). High on
"native Swift over Tauri". Moderate on effort estimates — nobody has measured on the
actual Mac yet, which is why Phase 0 exists.

---

## 9. Phased Plan

| Phase | Scope | Delivers |
| --- | --- | --- |
| **0** | Measure on the Mac: `zsh -lc` cost, `bob` spawn cost, current pop-up latency. **Confirm a signed hello-world `.app` can post a notification** before building anything on top of it. | A real baseline; retires the biggest unknown and the historically hardest bug |
| **1** | `bob-cli`: `capture-parse` + `capture-complete`, JSON + tests ported from `task_capture_spec.lua`. **Stand up macOS CI on the public repo.** | Grammar as data (R10); a working build loop for Linux agents (§7) |
| **2** | Swift skeleton: `LSUIElement`, `SMAppService`, Carbon hotkey, non-activating `NSPanel`, multi-line editor, submit → `bob capture`, signed bundle, `UNUserNotificationCenter` + `willPresent` + authorization status in Settings | **R1, R5, R6, R7** — already better than today |
| **3** | Span highlighting, completion popover, live preview (`--no-clip`), inline status strip | **R2, R3, R4, R12** |
| **4** | Cutover: remove the Hammerspoon binding, delete `task_capture.lua` and its specs | One capture path, one grammar |
| **5** | Polish: recent-capture history, notification actions (Open note / Undo), preferences, clipboard-marker affordances | R11, R14 |

**Phase 2 is the milestone** — it fixes four of five complaints and is independently
useful even if Phase 3 slips.

---

## 10. Acceptance Criteria

Carried from Researcher A, with the notification and signing items strengthened. Measure
on the actual Mac, with signposts rather than perception.

- Warm hotkey-to-focused-editor **p50 < 50 ms, p95 < 100 ms**, with no login shell and no
  WebView construction anywhere on the hotkey path.
- Cached completions appear **within 50 ms** of a trigger character; highlighting and
  typing stay independent of `bob` subprocess latency.
- The editor has an unambiguous newline gesture and an unambiguous submit gesture, and
  Escape never drops a nonempty draft without an explicit discard.
- Every fixture in `tests/hammerspoon/task_capture_spec.lua` produces the same final
  `bob` request, or a strictly more specific pre-submit diagnostic.
- Double submission causes at most one mutation; failed discovery never silently falls
  back to the inbox; capture failure preserves the full draft *and* the destination.
- Success and failure **always** produce visible in-panel feedback (R12). When macOS
  permits notifications, both also post a native notification under the Bob Capture
  identity.
- **A notification posted while the capture panel is on screen is actually presented** —
  the explicit regression test for §2.4.
- Settings reports notification authorization accurately and offers a test notification.
- The shipped bundle is signed and `codesign -dv` reports a stable identifier; a rebuild
  and reinstall does not silently reset notification permission.
- Notification bodies omit captured text by default; a successful notification can open
  the returned Obsidian target.
- The live-preview path never resolves the clipboard (assert `--no-clip` on that call).
- All vault mutations remain inside `bob-cli`; the Mac app never edits Markdown directly.
- `CaptureCore` builds and its tests pass on Linux; the full app builds and tests on
  macOS CI for every push.

---

## 11. Risks and Open Questions

| Risk | Notes |
| --- | --- |
| **Mac latency unmeasured** | All numbers are from athena. Phase 0 fixes this. If Mac `bob` spawn is much slower (cold vault, Spotlight indexing, iCloud), reconsider a resident daemon. |
| **Notifications fail *again*** | The highest-risk item given history. Phase 0 proves a signed hello-world can post a banner *before* any app code depends on it. Three independent causes (§2.4) must all be fixed. |
| **Non-activating panel input** | Setting the flag at init works; toggling it later breaks typing silently (§6). Also verify text input, IME, and secure-input fields behave with the app inactive — if not, activate deliberately and rely on the `willPresent` delegate, which is why the delegate is not optional. |
| **`capture-parse` drift** | Must be generated from the same parser as `capture`, not a parallel path. |
| **Clipboard markers (R9)** | `bob capture` reads the clipboard itself (`pbpaste`, Clipy SQLite). Confirm a `%` capture triggered from a *background* (non-activating) process still reads the live clipboard — plausible but untested, and it interacts directly with the non-activating design. |
| **Pomodoro-linked capture** | `@route:block-id` fails loudly with no open Pomodoro entry or multiple open timed entries. The panel must surface that and keep the text (R8), not just flash a banner. |
| **Hotkey collision during migration** | `RegisterEventHotKey` fails if ⌃⇧⌘I is still bound in Hammerspoon (`init.lua:1329`). Use a temporary combination in Phases 2–3. |
| **Signing certificate expiry** | Free Personal Team certificates expire (~1 year). Note it in the README so a future silent notification failure is not re-diagnosed from scratch. |
| **Accessibility permission** | Should not be needed with Carbon hotkeys. Confirm empirically — if a prompt appears, something is using `NSEvent` monitoring. |
| **Losing the Lua test suite** | `task_capture_spec.lua` (487 lines) encodes real grammar edge cases. Port before deleting in Phase 4. |
| **macOS 27 (~Sept 2026)** | Apple-silicon-only. Re-verify panel and notification behavior after upgrading. |

---

## 12. Sources

**Verified against source** (this workspace and `sase repo open chezmoi`):
`home/dot_hammerspoon/init.lua`, `home/dot_hammerspoon/task_capture.lua`,
`tests/hammerspoon/task_capture_spec.lua`, `src/native/capture.rs`,
`src/native/capture_clip.rs`, `src/native/capture_targets.rs`.

**Notifications**
- [UNUserNotificationCenter — Apple](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter)
- [How to Get Push Notification while App is in Foreground — Sarunw](https://sarunw.com/posts/notification-in-foreground/)
- [UNUserNotifications never show up when app is in foreground — Apple Forums](https://developer.apple.com/forums/thread/64851)
- [desktop-notifier — signing required for UNUserNotificationCenter](https://github.com/samschott/desktop-notifier)
- [hs.notify.show doesn't work — Hammerspoon #3631](https://github.com/Hammerspoon/hammerspoon/issues/3631)
- [WIP hs.notify updates — Hammerspoon PR #509](https://github.com/Hammerspoon/hammerspoon/pull/509)
- [libnotify.m (still NSUserNotification)](https://github.com/Hammerspoon/hammerspoon/blob/master/extensions/notify/libnotify.m)

**Panels and activation**
- [Nailing the Activation Behavior of a Spotlight/Raycast-Like Command Palette — Multi](https://multi.app/blog/nailing-the-activation-behavior-of-a-spotlight-raycast-like-command-palette)
- [The Curious Case of NSPanel's Nonactivating Style Mask Flag — philz.blog](https://philz.blog/nspanel-nonactivating-style-mask-flag/)
- [SwiftUI Floating Panel: NSPanel Patterns — Fazm](https://fazm.ai/blog/swiftui-floating-panel)
- [Fine-Tuning macOS App Activation Behavior — Art Lasovsky](https://artlasovsky.com/fine-tuning-macos-app-activation-behavior)
- [Building a macOS overlay that never steals focus — Unwait](https://unwait.ai/blog/macos-overlay-that-never-steals-focus)

**Rich text editing (macOS 26)**
- [Code-along: Cook up a rich text experience in SwiftUI with AttributedString — WWDC25](https://developer.apple.com/videos/play/wwdc2025/280/)
- [Using rich text in the TextEditor with SwiftUI — Create with Swift](https://www.createwithswift.com/using-rich-text-in-the-texteditor-with-swiftui/)
- [How to use rich text editing with TextView and AttributedString — Hacking with Swift](https://www.hackingwithswift.com/quick-start/swiftui/how-to-use-rich-text-editing-with-textview-and-attributedstring)
- [STTextView (TextKit 2)](https://github.com/krzyzanowskim/STTextView) · [HighlightedTextEditor](https://github.com/kyle-n/HighlightedTextEditor)

**Global hotkeys**
- [How to properly realize global hotkeys on macOS? — Apple Forums](https://developer.apple.com/forums/thread/735223)
- [Magnet — DivineDominion](https://github.com/DivineDominion/Magnet)
- [GlobalShortcut: switch from NSEvent to Carbon RegisterEventHotKey — electrobun #334](https://github.com/blackboardsh/electrobun/issues/334)

**Login items, build, CI**
- [macOS Service Management — The SMAppService API — theevilbit](https://theevilbit.github.io/posts/smappservice/)
- [Add launch at login setting to a macOS app — Nil Coalescing](https://nilcoalescing.com/blog/LaunchAtLoginSetting/)
- [Manage login items and background tasks on Mac — Apple Support](https://support.apple.com/guide/deployment/manage-login-items-background-tasks-mac-depdca572563/web)
- [Swift Bundler](https://github.com/stackotter/swift-bundler) · [Building an .app from a SwiftPM executable — Swift Forums](https://forums.swift.org/t/building-an-app-from-a-swift-package-manager-executable-for-macos/64409)
- [GitHub Actions free Apple Silicon macOS runners for public repos](https://discourse.julialang.org/t/github-actions-now-offers-free-apple-silicon-macos-runners-for-public-repositories/109641)
- [GitHub Actions Pricing 2026 — CICDCalculator](https://cicdcalculator.com/github-actions)

**Alternatives considered**
- [tauri-nspanel](https://github.com/ahkohd/tauri-nspanel) · [tauri-macos-spotlight-example](https://github.com/ahkohd/tauri-macos-spotlight-example) · [Tauri Global Shortcut plugin](https://v2.tauri.app/plugin/global-shortcut/) · [Tauri macOS Code Signing](https://v2.tauri.app/distribute/sign/macos/)
- [How the Raycast API and extensions work](https://www.raycast.com/blog/how-raycast-api-extensions-work) · [Menu Bar Commands — Raycast API](https://developers.raycast.com/api-reference/menu-bar-commands)
- [Collector — Obsidian Quick Capture App for macOS](https://github.com/juliandeans/Collector) · [Obsidian Smart Capture — Raycast Store](https://www.raycast.com/millin_gabani/obsidian-smart-capture)

**Platform status**
- [macOS Tahoe roundup — MacRumors](https://www.macrumors.com/roundup/macos-26/) · [Apple releases macOS Tahoe 26.6](https://macdailynews.com/2026/07/27/apple-releases-macos-tahoe-26-6/) · [macOS 27 will drop Intel — BGR](https://www.bgr.com/2169799/macos-27-fix-liquid-glass-feature/)

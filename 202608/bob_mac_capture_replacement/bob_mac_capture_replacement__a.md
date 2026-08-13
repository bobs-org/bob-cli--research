# Researcher A (`research.0h.cdx`) — Partial Report (Recovered)

> **Provenance warning — this report is incomplete, and not by the author's choice.**
>
> Researcher A (`research.0h.cdx`, `codex/gpt-5.6-sol`) and Researcher B
> (`research.0h.cld`, `claude/opus`) independently wrote their reports to the **same
> path**, `202608/bob_mac_capture_app.md`. Researcher B committed first
> (`b04772f`). Researcher A then hit an upstream rebase conflict and resolved it by
> keeping Researcher B's file and appending only its own §12 "Acceptance Criteria"
> section (`8e99e7a`). **Researcher A's report body was overwritten and is
> unrecoverable** — it exists in no reflog, no dangling object, no sibling workspace,
> and was never pushed. Verified by the lead researcher via `git fsck --dangling`,
> `git reflog --all` in both `bob-cli_10` and `bob-cli_11`, `git ls-remote`, and a
> filesystem-wide search.
>
> What follows is everything that genuinely survives: the section Researcher A
> contributed to the shared file (verbatim, from `git diff b04772f 8e99e7a`), plus
> its own summary of its conclusions from its chat transcript. Nothing here is
> invented to fill the gap.

---

## 1. Surviving Contribution — Acceptance Criteria (verbatim, `8e99e7a`)

Measure these on the actual Mac, preferably with signposts rather than perception alone:

- Warm hotkey-to-focused-editor p50 under 50 ms and p95 under 100 ms, with no login
  shell or WebView construction on the hotkey path.
- Cached completions appear within 50 ms of a trigger character, while highlighting and
  typing remain independent of `bob` subprocess latency.
- The editor provides an unambiguous newline and submit gesture, and Escape never drops
  a nonempty draft without an explicit discard action.
- Every current Hammerspoon grammar fixture produces the same final `bob` request or a
  more specific pre-submit diagnostic.
- Double submission causes at most one mutation; failed discovery never silently falls
  back to the inbox; capture failure preserves the full draft and destination.
- Success and failure always produce visible in-panel feedback. When macOS permits
  notifications, both also schedule a native notification under the Bob Capture identity.
- Settings reports notification authorization accurately and offers a test notification.
- Notification bodies omit captured text by default, and a successful notification can
  open the returned Obsidian target.
- All vault mutations remain inside `bob-cli`; the Mac app never edits Markdown directly.

---

## 2. Conclusions As Stated By Researcher A (from its chat transcript)

Reproduced from `~/.sase/chats/202608/gh_bobs_org__bob_cli-ace_run-research_0h_cdx-260813_192123.md`.
These are the author's own words about its findings; the supporting argument is lost.

**Recommendation.** "A native Swift macOS agent app using a persistent AppKit
`NSPanel`, SwiftUI shell, `NSTextView`, direct `bob` subprocess integration, cached
completions, and native notifications."

**Options compared.** "Native Swift, Tauri, Hammerspoon, Raycast, and Obsidian-plugin
approaches", with "Tauri as the credible runner-up and Raycast as a useful prototype
path". The report included "architecture, delivery phases, risks, and acceptance
criteria".

**Decisive reasons for native.** "A warm, persistent process; a real multiline/
token-aware editor; a dedicated notification identity; and tight control over focus,
Spaces, and keyboard behavior."

**Finding on the existing launcher.** "The Hammerspoon file already implements
route/section/task pickers, JSON parsing, retries, and a defensive notification path.
That's useful evidence — the replacement should move this state machine into a testable
app, not keep layering UI logic onto Lua."

**Finding on latency.** "The present panel recreates an `hs.webview` and its controller
every time the hotkey fires, which plausibly explains intermittent launch latency."

**Finding on multi-line (flagged by A as a product decision, not an implementation
detail).** "`bob capture` currently collapses all whitespace, including newlines, into
one line. A multiline editor alone would improve composing/wrapping, but preserving line
breaks in Obsidian requires an explicit CLI/API extension or a defined 'one capture per
line' behavior." A added: "I'm treating that second point as a product decision in the
recommendation rather than hiding it as an implementation detail."

---

## 3. Where A's Surviving Material Went In The Consolidated Report

- The acceptance criteria in §1 above are carried into the consolidated report as its
  acceptance-criteria section, edited only to fold in the notification-delegate and
  signing requirements the lead researcher verified.
- A's multi-line framing (a product decision about newline semantics, not a widget
  swap) is adopted; it independently agrees with Researcher B's §5.1, and the lead
  researcher confirmed the underlying behavior in `src/native/capture.rs:1623`.
- A's "dedicated notification identity" and "tight control over focus, Spaces, and
  keyboard behavior" arguments are reflected in the consolidated notification and panel
  sections.
- A's read that the Hammerspoon state machine should move into a *testable* app rather
  than accreting more Lua is adopted, and reinforced by the lead researcher's finding
  that a headless core is also what makes the project workable from Linux agents.

# Capture alias hints: teach the opportunity, preserve the flow

Independent research by **cdx**, 2026-11-09. Scope: design and implementation advice for Bob Mac Capture; no application changes. No peer report, peer transcript, or peer findings were consulted.

**Recommendation:** build this, but as a small, contextually correct lesson attached to the picker—not a notification for every sigil. Start with `.` → `@` after body text. Let Bob prove that the alternative would have worked; let the Mac app decide whether this is a good moment to teach it. Show **“Next time, type [.] instead of [@] here.”** Keep canonical typing fully valid. Suppress repeated lessons, retain an on-demand reference, and measure interruption as carefully as alias adoption.

## 1. Is this a good idea?

Yes, with a deliberately modest ambition. These aliases are hidden conveniences whose contextual rules are hard to infer. Teaching one at the moment its purpose is visible is more useful than a tour of the entire capture language. A user who just opened the destination picker already understands what that action accomplishes.

However, switching from `@` to `.` is not equivalent to replacing a slow mouse workflow with a keyboard shortcut. Both are short keyboard actions; the benefit is avoiding an awkward character or modifier on some layouts. It may be negligible on others. A distracting lesson can easily cost more attention than the alias saves. Canonical symbols also remain useful in pasted drafts, documentation, scripts, and mental models. Continued use of `@` is not evidence of failure.

The chief product risks are false equivalence, nagging, and teaching too late for immediate practice. A hint after `@` must not suggest that pressing `.` **now** will help: `Buy milk @.` stays literal. The copy needs “Next time,” and should not ask the user to undo a successful action. Do not show time-saved claims or grade the user's typing.

**Requirement adjustments I recommend:**

| Original interpretation | Adjustment | Reason |
| --- | --- | --- |
| A typed character has an alias | A particular edit in a particular context has an equivalent alias | The same character has several roles; aliases have deliberate exclusions. |
| Show whenever the canonical character is typed | Teach eligible, unlearned opportunities with a small exposure budget | Valid canonical typing must remain comfortable. |
| `@` always teaches `.` | Teach only where Bob proves `.` would open the same route picker | Leading `.` is currently literal. |
| Cover all aliases together | Ship one complete route lesson first, then extend the same contract | Close outcomes, picker continuations, and relation flips need different explanations. |
| A transient hint is sufficient | Pair it with a durable, user-requested “Capture typing aliases” reference | Fast typists may never pause long enough to see the lesson. |
| A hint belongs in general status | Put it with the picker; preserve errors and action feedback | The current status footer also drives accessibility focus. |

These narrow and refine the requested behavior; they do not expand capture syntax or change alias mechanics.

## 2. What the implementation actually does today

I inspected bob-cli at `f231b9d37fec4803c4470eeef65e5b5d27718076` and bob-mac-capture at `b81302b2610d31bbc9caa4c9c245097b16b0b884`. Findings below are from those snapshots, the audited Capture Alias glossary and architecture decisions, and read-only executable probes.

### The route example has important boundaries

Bob's `expand_dot_route_alias` requires a preceding space/tab and nonempty preceding content, checks token position, excludes claimed wikilink fields, and requires the ordinary completion engine to report an empty route field. It is not a global character substitution. Tests cover further exclusions, including code, command-like items, existing routes, and template drafts. [Bob rewrite implementation](https://github.com/bobs-org/bob-cli/blob/f231b9d37fec4803c4470eeef65e5b5d27718076/src/native/capture_language/rewrite.rs#L277), [positive and negative tests](https://github.com/bobs-org/bob-cli/blob/f231b9d37fec4803c4470eeef65e5b5d27718076/src/native/capture_language/tests/rewrite.rs#L860).

| Actual typed draft, caret at end | Current outcome | Implication for a lesson |
| --- | --- | --- |
| `Buy milk .` | `Buy milk @` | Typing the final canonical `@` in this context can teach `.`. |
| `Café run .` | `Café run @` | Offsets must handle UTF-8 correctly. |
| `.` or `  .` | Unchanged | Do not teach `.` for a leading `@`. |
| `- .` in an ordinary draft | Unchanged | Do not assume bullet starts behave like body text. |
| `@errands.` | `@errands^` | Learning this dot action does not imply knowing dot-for-route. |
| `Buy milk @.` | Unchanged | “Press .” while the picker is already open is misleading. |
| `Buy milk . more`, caret at end | Unchanged | Do not scan a restored draft for missed opportunities. |

I reproduced all seven rows with `/home/bryan/.cargo/bin/bob` (`bob 0.5.0`) using `capture-rewrite --cursor <UTF-8 length> --format json`. That binary's version string does not establish that it matches the source SHA; the source tests provide separate corroboration. These commands rewrite returned text only and do not capture into the vault.

### The wider alias family is heterogeneous

| Gesture family | Existing alternative | Teaching concern |
| --- | --- | --- |
| Route after body text | `.` for `@` | Best first lesson. |
| Block ID / Move | `.` for `^` | Separate lesson identity from route-dot. |
| Task link | `;` for `:` | Bare-item and route-scoped contexts both exist. |
| Parent task | `,` for `+` | A continuation can insert ` +`, not just replace a byte. |
| Type, section, drawer, name, heading menus | `\` or `/` for `#` | Meaning and exclusions vary; teach one alternative at a time. |
| Links To | spaced `=` for `~` | Do not confuse an opener with a direction flip. |
| Past close segment | `-` for `~` inside `x=` | Not the relation lesson; a spaced dash remains literal. |
| Close outcome | `x` for `!`, `s` for `*` in a close slot | Meaning-changing behavior with existing input/Return holds; defer unsolicited teaching initially. |
| Blank-draft Go To | app-local `\` for `/` | Separate app gesture, outside Bob's ordinary sigil-rewrite authority. |

This is an inventory, not a proposal to display every row. Authoritative details and escape behavior are in the [Mac capture documentation](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/docs/capture-panel.md#L211) and [Bob's capture reference](https://github.com/bobs-org/bob-cli/blob/f231b9d37fec4803c4470eeef65e5b5d27718076/docs/capture.md#L9182).

Aliases apply while typing. Paste, piped input, template drafts, and literal-name contexts must not be promoted into a new rewriting or teaching path. Undo and existing literal escapes remain intact. The settings label “Capture alias” already refers to a **global hotkey**, so call the feature **Capture typing tips** to avoid that collision.

### Existing UI and protocol seams

- `capture-rewrite` returns `rule: expand_sigil_alias` and human feedback such as `Typed @ for .`. That confirms an alias already used; it does not report a missed opportunity. Do not parse that prose as a stable identifier. [Response model](https://github.com/bobs-org/bob-cli/blob/f231b9d37fec4803c4470eeef65e5b5d27718076/src/native/capture_rewrite.rs#L296).
- The Mac editor distinguishes native edit intent from programmatic changes, tracks generations, validates UTF-8/UTF-16 conversion, and rejects stale rewrite responses. Its current rewrite intent list does **not** include `@`, `#`, `!`, or `*`. A listener attached only to that lane would miss the user's principal example. [Intent handling](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/Sources/BobMacCapture/CapturePanelModel.swift#L2883), [response checks](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/Sources/BobMacCapture/CapturePanelModel.swift#L17329).
- Ordinary completion has a default 50 ms analysis debounce. `CaptureCompleteResult` already exposes context, cursor, replacement ranges, and optional presentation metadata. Its source explicitly permits additive optional fields without changing schema version 1. [Completion model](https://github.com/bobs-org/bob-cli/blob/f231b9d37fec4803c4470eeef65e5b5d27718076/src/native/capture_complete/model.rs#L1093).
- `CompletionList` uses regular material, an 8-point corner radius, and an existing shadow. Its footer is inside the scrolling content and only rendered in certain states. It is not a guaranteed persistent slot. The main action footer separately owns status, errors, and focus-triggering announcements. [Picker rendering](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/Sources/BobMacCapture/CapturePanelView.swift#L3394), [action footer](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/Sources/BobMacCapture/CapturePanelView.swift#L1279).

The accepted thin-client decision remains decisive: **Bob decides syntax and equivalence; Swift owns presentation, lifecycle, and local teaching preferences.**

## 3. What external evidence supports—and does not support

Apple recommends short, contextual instruction near the relevant interface, audience eligibility rules, and a restrained cadence. Its guidance explicitly recognizes that people who have used a feature do not need a tip explaining it. This supports local, occasional teaching rather than a toast on every key. [Apple: Offering help](https://developer.apple.com/design/human-interface-guidelines/offering-help), [Apple: Onboarding](https://developer.apple.com/design/human-interface-guidelines/onboarding).

TipKit provides event/parameter eligibility, display-frequency controls, and invalidation when someone uses a feature. Those are useful patterns even if Bob implements a smaller policy itself. Apple's documentation warns against unnecessary tips on every app visit. [TipKit overview](https://developer.apple.com/documentation/tipkit/), [WWDC23 feature discovery session](https://developer.apple.com/videos/play/wwdc2023/10229/).

Malacria and colleagues' CHI 2013 ExposeHK paper reports three studies in which displaying shortcuts where commands were selected increased shortcut use and improved performance. Its central mechanism includes **rehearsing the shortcut while accomplishing the action**. A retrospective “you could have typed…” message does not provide that same rehearsal, so the paper does not establish that this proposed hint will produce equivalent gains. My inference is narrower: make the association spatially stable and keep it available on demand; validate learning rather than assuming it. [Author-hosted paper, abstract and introduction](https://www.csse.canterbury.ac.nz/andrew.cockburn/papers/ehk.pdf), DOI `10.1145/2470654.2470735`.

There is no evidence here that an alias hint saves Bryan time, that a specific delay is optimal, or that a particular exposure count produces mastery. The numerical defaults below are design hypotheses. This research did not include a live Mac usability session.

## 4. The proposed experience

The editor remains the focal point. The picker looks like the existing picker. One quiet line sits at its bottom, outside the row scroll area and inside the same material surface:

```text
┌──────────────────────────────────────────────────────────┐
│ Buy milk @                                               │
├──────────────────────────────────────────────────────────┤
│  Errands                                                 │
│  Home                                                    │
│  … existing destination rows …                           │
│                                                          │
│  Next time, type [ . ] instead of [ @ ] here.          ×   │
└──────────────────────────────────────────────────────────┘
   existing status and capture actions
```

The brackets represent understated keycaps, not inserted text or clickable conversion controls. The illustration describes hierarchy; it is not a rendered screenshot.

Use the existing caption typography (target roughly 12–13 points), normal readable secondary text, monospaced key glyphs, and the existing semantic palette for a subtle route accent. Reuse the picker material, corner treatment, and shadow; do not add a second floating bubble, glow, mascot, or “Tip!” badge. Start with approximately 28 points of measured instructional chrome and 8-point horizontal insets; validate these against the actual Mac font metrics and narrowest supported panel. Keep punctuation large enough to recognize. Dimness must not become illegibility.

**Layout stability matters more than animation.** Admit the lesson when the first current completion result is ready to paint, and budget its height in that initial picker layout. Keep its allocated lane for the rest of that picker interaction, even if the text is dismissed. Never insert a new row halfway through keyboard navigation. If a response arrives after the opportunity has moved on, skip it. Do not add blank instructional space to unrelated pickers. Update the panel's measured sizing path; the existing viewport has no proven spare row to borrow.

Do not replace the selected-row explanation or the main footer. When space is tight, suppress automatic teaching before shrinking critical controls or covering a candidate. A short variant can read **“Next time: [.] for [@] here.”** The full contextual example remains available in Help.

The small × means **Hide this tip**, with that accessible name and a useful pointer target. It dismisses that semantic lesson permanently until reset. It is not a new Escape binding. All existing Escape, Space, Tab, Return, arrow, and Control-N/P behavior remains unchanged. No action edits the current draft.

For VoiceOver, expose one combined description such as “Typing tip. Next time, type a period instead of an at sign here to choose a destination.” Do not rely on the screen reader's punctuation verbosity setting, move accessibility focus, or send an unsolicited live announcement on every display. The line and dismissal control remain discoverable through ordinary navigation; the Help reference provides a persistent alternative. Test this with VoiceOver on the actual panel. Respect Reduce Motion and Increase Contrast; no animation is necessary for version one.

## 5. Eligibility, lifetime, and learning

An **opportunity** is an actual direct single-character editor insertion, at a collapsed selection, whose canonical sigil and exact context Bob validates. It is not a match in arbitrary text.

For the first release:

1. Observe a committed native `@` insertion in the main draft editor. Do not intercept it. Exclude key repeats, paste, restoration, Undo/Redo, programmatic insertion, and active marked-text composition. Do not reject a produced `@` just because an international keyboard uses Option to type it; identify the text insertion and its origin, not a US physical key code.
2. Let ordinary completion run. Admit the hint only from a successful, current response tied to that insertion, with a usable route picker and no higher-priority problem UI. If the user types ahead before that first response can be validated, skip this opportunity; do not delay them or show it later in an unrelated state.
3. Once admitted, keep the same lesson while that picker interaction remains active, including ordinary query filtering. Do not change copy on each row or keystroke. Clear on acceptance, Escape, lost focus, panel close, submission, caret relocation, Undo/Redo, paste, or a new semantic context. A new request generation may preserve it only when the same Bob-authored picker anchor is still valid.
4. Failed or missing metadata means ordinary completion without a hint. A hint must never hold input, Return, preview, or capture submission. It must never add a modal error.

**Initial teaching policy:** allow the first eligible opportunity without requiring repeated “mistakes”; at most one lesson per panel opening and one automatic lesson per rolling 24 hours across all aliases; at most three displayed impressions per semantic lesson. Count an impression only when the visible, active panel actually presents the line, not when a request begins. After three, retire automatic teaching even if no alias use is observed. These conservative defaults are tunable after use; they are not literature-derived constants.

A successful alias-driven picker acceptance followed by successful capture of that surviving token is enough to retire that lesson as learned. Keep the learning evidence provisional until then, and cancel it on Undo, a literal escape, replacement, or discard. Do not mistake pasted `.` or an accidental alias immediately undone for learning. A person who knows the alias but prefers `@` can dismiss the tip immediately; mastery is an imperfect suppression heuristic, not a claim about cognition.

Persist only semantic lesson ID, display count, last display time, dismissed state, and learned state in the app's local preferences. No draft text, target names, paths, or keystroke history is needed. Separate `route_dot` from `block_id_dot`; version a lesson only when its meaning changes, not whenever copy changes. Do not add vault-synced journals or telemetry infrastructure for this.

Offer **Capture typing tips** on/off and **Reset typing tips** in settings, with a Help entry **Capture typing aliases** that remains available when automatic tips are off. Include purpose, context, and an example, such as `Buy milk .` → `Buy milk @`, plus the fact that paste stays literal. This small reference is the fallback if passive hints prove too easy to miss. There is no need for a new global shortcut or practice wizard.

## 6. A reliable contract without a second grammar

### Prefer additive completion metadata

Add an optional, structured hint descriptor to the normal `capture-complete` result for the exact eligible opener. Illustrative contract only:

```json
{
  "alias_hint": {
    "id": "route_dot",
    "canonical": "@",
    "alias": ".",
    "context": "route",
    "trigger_range": { "start": 9, "end": 10 }
  }
}
```

The enclosing response already has a cursor and context; the client request carries its draft snapshot and generation. `trigger_range` uses UTF-8 byte offsets, matching Bob's existing protocol. For `Buy milk @`, the final character occupies bytes 9–10. The app validates that range against the actual native insertion. Bob returns semantics; Swift selects localized copy, glyph names, and layout. If future IDs or contexts are unknown, omit the lesson rather than failing completion.

The descriptor is a **semantic possibility**, not proof that a human typed the character. That provenance stays in the app. Likewise, a completion generated by Bob expanding `.` into `@` must not provoke “next time use .”: the original insertion was an alias, not `@`.

For version one, produce this metadata only at the immediate empty route opener. That makes the eligibility proof precise and keeps the feature out of query interpretation. Swift may retain an already admitted lesson while filtering that same picker, but must not invent a new one from later query text.

### Prove the alternative through the existing forward rewrite

Inside Bob, take the post-key draft and caret, substitute the candidate alias at the canonical insertion range, and evaluate the existing rewrite logic in memory. Offer a lesson only if all of these hold:

- the forward rule is specifically `ExpandSigilAlias`;
- the rewritten candidate reproduces the actual canonical draft byte-for-byte and the same caret;
- the completion field has the intended semantic role;
- no earlier rewrite rule, template/literal exclusion, or unsupported context claims it.

This directly tests the statement “you could have typed this here.” It reuses the guards that already decide alias behavior. Do not reverse a dictionary such as `@ -> .`; do not infer from syntax highlighting or the word “Route.” Structure the helper so it cannot recurse through completion-result construction: it should use the existing lexical completion-field analysis, not call the `capture-complete` endpoint again.

Exact byte equality is deliberately conservative. It handles the initial route case well. Later, comma continuations that insert whitespace may require their own explicitly tested equivalence rule; skipping such a lesson is better than claiming an unproven equivalence.

There is no need for another subprocess per key, a new daemon, or a CLI option in the first implementation. Teach through the completion response already requested. Keep the new field optional under the existing additive schema policy. Decode absent or malformed optional teaching data defensively without poisoning otherwise valid suggestions. New app + old Bob means no teaching; old app + new Bob ignores the new field.

For learned-state tracking, add a matching optional structured `alias_usage` identity to successful `capture-rewrite` responses, generated from the same semantic helper, then correlate it with picker acceptance and successful capture. Do not parse the human `summary` or treat all `expand_sigil_alias` rewrites as the same skill. Missing usage metadata can safely fall back to the finite impression budget.

### Why not the alternatives?

| Approach | Assessment |
| --- | --- |
| Swift-only reverse mapping | Small patch, unreliable behavior; duplicates Bob's semantic decisions. Reject. |
| Missed-opportunity data only in `capture-rewrite` | Reasonable for non-picker actions later, but `@` currently does not enter that lane and hint-only work must not enter its completion/input gates. Prefer completion metadata now. |
| New hypothetical rewrite subprocess on every canonical key | Can prove equivalence, but adds orchestration and latency opportunities for optional education. Keep the proof inside Bob. |
| Status toast / footer replacement | Easy to notice, but competes with feedback and accessibility focus. Reject. |
| Popover pointing at the caret | Visually loud, sensitive to caret movement, and can obscure typing. Reject. |
| Permanent alias badges on every picker | Predictable but adds lifelong clutter; offer only as an explicit help surface if users ask. |
| Help reference alone | Cheapest and safest, but weak discovery. Keep as fallback, not the only entry point initially. |
| TipKit policy plus custom view | Technically plausible; adopt if the app gains broader onboarding needs. Not necessary for one small lesson policy. |

The package currently targets macOS 26.0, so a macOS 14 availability argument against TipKit would be incorrect. The reason to prefer a small portable policy object here is exact editor provenance, deterministic tests, and control over compact picker layout—not OS incompatibility. TipKit's ready-made policy remains a credible future substitution. [Package platform declaration](https://github.com/bobs-org/bob-mac-capture/blob/b81302b2610d31bbc9caa4c9c245097b16b0b884/Package.swift#L55).

## 7. Scope and implementation boundaries

The first release should contain the route lesson, Bob's structured eligibility and usage fields, a small pure policy/presentation model in CaptureCore, native editor provenance in the Mac controller, a dedicated picker teaching lane, settings, and the on-demand reference. Keep teaching state out of the already large rewrite state machine and out of generic status announcements.

Relevant source seams are `capture_language/rewrite.rs`, `capture_complete/model.rs` and its engine, `capture_rewrite.rs`, `CaptureModels.swift`, `CapturePanelController.swift`, `CapturePanelModel.swift`, `CompletionList` in `CapturePanelView.swift`, and the panel sizing path. This is a design map, not a request to edit all of them without reviewing their current responsibilities.

Next candidates are `;` → `:`, `.` → `^`, and `,` → `+` picker openings. Only after those are sound should `#` contexts be added with purpose-specific wording and one suggested alias per occurrence. Relation openers and flips need separate IDs and teaching copy. Close outcomes should use their existing consequence cards and authoritative slot semantics if added later; forcing every family into a picker lesson would be a design mistake. The app-local Go To alias is separately owned.

Do not change the release train, version number, or capture grammar to deliver this. Read the project's CLI/help documentation rules before implementing any public contract or help changes.

## 8. Validation that would make this safe to ship

| Area | Evidence required |
| --- | --- |
| Semantic truth | Every emitted lesson passes the forward-equivalence check; fixtures cover positives and excluded contexts. |
| Principal negatives | Leading `@`, `@@`, bare checkbox/bullet starts, code, wikilinks, template drafts, exact-name literals, and occupied route contexts do not receive a false route-dot lesson. |
| Edit provenance | Paste, restore, completion insertion, native alias rewrites, Undo/Redo, IME marked text, repeat keys, and selection replacement never trigger the first-release lesson. |
| Unicode and keyboard layout | Emoji before the marker, composed/decomposed text, CJK composition, non-US `@` insertion, and invalid UTF-8 boundaries behave correctly. |
| Async behavior | Delayed, reversed, cancelled, mismatched-client, and stale responses cannot resurrect a hint after edit, navigation, dismissal, or submission. |
| Independence | Enabling teaching produces identical draft bytes, selection, undo history, completion choice, and capture result; teaching cannot defer Return. |
| Policy | Fake-clock tests cover rolling cooldowns, impression accounting, finite retirement, dismissal, reset, learned-state commit and rollback, and corrupt preferences. |
| Compatibility | Old Bob omits metadata; unknown/malformed hint metadata is ignored; future IDs do not break completion. |
| Visual behavior | Light/dark mode, Increase Contrast, Reduce Motion, smallest panel, maximum visible rows, and screen-edge sizing retain stable editor and action positions. |
| Accessibility | VoiceOver reads named punctuation and purpose without unsolicited focus movement; dismissal and persistent help are reachable. |

Reuse the existing dot-route alias and native rewrite test harnesses, but add tests for the **new guarantee** that teaching does not change input. Extend the pure model tests with a fake clock rather than real sleeps.

When implementing Swift, run `just portable-check`. AppKit/SwiftUI targets must also be compiled: the linked repo's instructions require best-effort scratch-copy compilation on the Mac (`bundle.sh`, `just typecheck-tests`), plus macOS CI; portable checks alone do not type-check those targets. Run the repo's `Scripts/macos-ci-check` before landing and watch the exact-SHA macOS run after a push through the required SASE monitor workflow. Run `just docs-check` for documentation changes. This research changed no Swift and therefore makes no build or UI-test claim.

For product evaluation, first use a small paired exercise: a few ordinary captures with teaching off, then with the route lesson; later check unaided recall. Follow with Bryan's normal use. Observe whether he notices it, understands that it is for next time, tries it in a valid context, and feels interrupted. Do not infer meaningful time savings from a tiny sample.

If instrumentation is useful, keep local aggregate counts for eligible opportunities, rendered lessons, retained alias uses, literal restores, dismissals, and capture-duration distributions; do not record content. Compare correctness and perceived flow first, adoption second. A sensible stop condition is any misleading lesson or input regression. If lessons are accurate but unread, improve on-demand discovery before making them louder. If Bryan prefers canonical sigils, turn teaching off; that is a successful user choice.

## 9. Remaining uncertainty and confidence

**High confidence:** raw-character triggering is insufficient; the route-dot restriction is real; Bob must remain the semantic authority; metadata must be additive; input provenance and stale-response checks matter; the existing status footer is a poor primary teaching surface.

**Moderate confidence:** a small picker-attached line will fit this interface better than a toast or popover. This is grounded in the inspected layout and platform guidance, but still requires a rendered Mac prototype and accessibility review.

**Unvalidated hypotheses:** one lesson per day, three total exposures, the exact 28-point lane, and learned-state retirement after a successful retained alias capture. Adjust these from observed use. The underlying opportunity detector should remain strict regardless of policy tuning.

I used code inspection, existing tests, audited project memory, official Apple guidance, the indexed abstract/introduction of the author-hosted ExposeHK paper, and read-only Bob probes. Some full-paper endpoints timed out or denied access; no detailed experimental effect size is claimed. I did not inspect unrelated prior research or any report from this swarm.

## 10. Recommended solution

**Ship a restrained, contextual route-alias lesson first.** When a directly typed `@` opens the route picker and Bob proves that `.` would have produced exactly the same result, show a quiet keycap line: **“Next time, type [.] instead of [@] here.”** Keep it attached to that picker interaction, preserve typing and layout stability, and retire it after dismissal, demonstrated use, or a small finite exposure budget.

Implement eligibility in Bob using the existing alias rewrite rules and return optional metadata through ordinary completion. Keep edit provenance, display policy, accessibility, and local preferences in the Mac app. Provide a persistent contextual alias reference. Expand to other families only when each has a truthful lesson and an appropriate surface.

This is a good feature if it helps the user discover a convenience and then gets out of the way. The desired outcome is informed choice and fluent capture—not maximum alias usage.

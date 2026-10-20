# Related-task preview for Bob Mac Capture

Researcher: grk
Date: 2026-10-20
Status: independent design research (not a plan)

## Verdict

Do it, but narrower and quieter than the prompt describes.

The useful product is a **duplicate-first advisory rail** on new-task previews: a heads-up that this title already exists, with a quieter related band underneath. It is not a second task picker, not a live-preview payload, and not a fuzzy dump of "likely related" work.

Done that way, the idea is good. Done as "show related tasks whenever a new task would be created," it will either slow the panel or train Bryan to ignore it.

Recommended shape:

1. `bob` owns which items create tasks, which existing tasks match, and why.
2. Bob Mac Capture renders an additive, fold-first rail inside the existing preview pane.
3. Matching stays off the `capture --dry-run` hot path.
4. Return still captures. Focus never leaves the editor.
5. Empty, short, and non-creating drafts show nothing.

## Critique of the request

The prompt's benefit is real. Bryan already has linking grammar (`:`, `@`, `&`, `*`, `~` / `~~`) and a vault of long, specific titles. The failure mode is recapture: typing a title that already lives on an open task, filing it into `mac_inbox.md`, and discovering the twin later in the NEW walk. A create-time heads-up is the right moment to catch that.

The prompt's framing is too wide in three places.

**"Likely related" is the wrong primary job.** Duplicate and related are different questions. A duplicate is the same work twice. A related task is different work that might deserve a `~` relation or a `*` / `&` dependency. Mixing them in one ranked list makes the rail look like a search box the user did not open. Industry practice that works (GitHub's 2026 create-time duplicate preview, Discourse similar-topics, Bugzilla/YouTrack duplicate suggestions) leads with *this already exists*, then optionally shows a couple of cousins. Jira still has no native create-time check; marketplace apps bolted it on after the fact. Linear's issue create path optimizes for sub-five-second capture and does not interrupt with cousins. Bob should follow GitHub's "up to three, non-blocking" discipline, not a related-pages widget.

**Capture is already crowded.** The auxiliary region below the editor is shared by the idle agenda, completion, destination, errors, live preview cards, plan-budget meters, successor pull-in, File under, and several pickers. A new-task dry-run already paints a thin-material card (`kind: "task"`, the line that will be written, a pink **New** badge on created parent blocks). Stuffing a browse list into that card without a hard cap will force scrolling, which the idle-agenda decision explicitly rejected for content under a fixed eye line.

**The performance worry is the right worry, and the naive implementation is the wrong one.** Live preview today is `50ms` debounce, then `capture-parse`, then `capture --dry-run --no-clip` on its own `preview` lane. On apollo that dry-run is about `10ms`. The full open-task snapshot (`capture-complete --all-tasks` on a solo `:`) is about `30ms` and **225 KB** for 498 candidates. Putting that scan on every preview would triple the write-preview path and re-decode hundreds of kilobytes per keystroke. The Mac client already documents that `task_link` payloads are hundreds of KiB and must drain stdout while the child runs. Do not add a second copy of that work to the preview process.

A GTD-orthodox objection also applies: capture should be faster than thought; clarify comes later. Bob capture is already a mixed command palette (link, complete, start, close, relate), so a heads-up is in character. It still has to be ignorable. Successor offers are a blocking in-panel choice because a managed Done gesture has to pick successors *now*. Related matches are not that. Auto-linking them would contradict `decisions:unblocked-tasks-are-offered`. Checkboxes in the preview were already rejected there.

## Requirement adjustments

These change the request. Each is a product call, not an implementation detail.

1. **Duplicate-first, related-second.** The rail's job is "you may be recapturing this." Related matches are a quieter second band, never the headline. If a draft only has weak cousins, show at most two; if it has a duplicate, lead with that row and demote cousins.

2. **Silence is the default.** Omit the rail when there are no matches. Do not show "No related tasks." Do not search short or generic titles. Require **at least 20 characters or 3 significant tokens** (stopwords dropped) before querying. GitHub's public preview waits for a 20-character title (and a 100-character body, which Bob drafts do not have). "buy milk" must stay a one-card preview.

3. **Advisory, never modal.** Return always captures. Keyboard focus stays in the editor, same contract as the idle agenda. Do not steal Tab (em-dash, indent, completion). Do not open the `:` picker unsolicited. A later "link instead" gesture may apply Bob's `replacement` (`@route:block-id`) the way the Task Link picker already does; that is phase 1.1, not the MVP.

4. **Off the dry-run hot path.** Related search is a cancellable `related` process lane, started after parse says the draft will create one or more tasks. Preview paints first. The rail may fade in. An older `bob` that omits the command or the field leaves the panel unchanged.

5. **Hard cap of three visible rows**, plus a `+N more` chip. Related folds before any other preview content when the below-eye-line budget binds. Bulk drafts show matches per creating item, and only the duplicate band on non-focused items.

6. **Open tasks only for v1.** Use the same universe as the `:` picker: Ready, Blocked, Next, In Progress in inbox, area, and non-terminal project notes. Completed-history duplicates (valuable: "you already did this") wait until the open-task rail is proven quiet. Do not scan the whole vault, Dataview index, or daily notes.

7. **No embeddings, no daemon, no Swift-side vault reads.** Title Dice / prefix scoring on cleaned display text is enough for this vault. A resident bob daemon was already rejected as premature in `decisions:mac-capture-is-a-thin-client`. The app may rank a snapshot Bob returned; it may not invent candidates or grammar.

8. **Never auto-link, auto-relate, or auto-rewrite.** A match is a suggestion. Creating the inbox task remains the one-keystroke default.

## What already exists

### Thin client and live preview

Bob Mac Capture is a renderer. Grammar, completion, preview, and writes live in `bob` (`decisions:mac-capture-is-a-thin-client`). The panel:

- Debounces analysis by **50ms** (`CapturePanelModel.debounceNanoseconds`).
- Calls `capture-parse` (spans, `mode`, `needs`).
- Skips the doomed dry-run while a picker need is open.
- Calls `capture --dry-run --no-clip --format json` on lane `preview`.
- Calls `capture-complete --all-tasks` on lane `completion` only when the cursor is in a completion context.
- Cancels the previous process in a lane when a newer request starts.

A new-task draft is already classified. `capture-parse -- "buy milk"` returns `mode: "task"`. The dry-run returns `kind: "task"`, `placement: "inserted"`, `relative_target: "mac_inbox.md"`, and the exact `task_line`. New-task `capture-complete` currently returns **empty candidates on purpose** (`"New intent stays empty even with --all-tasks"`). Related search is a new job, not a completion context.

### The `:` picker is the existence proof and the anti-pattern

Typing `:` as a whole item opens the Task Link picker. Bob supplies one snapshot of every linkable open task; the app filters locally with `FuzzyMatcher` so further keystrokes are free. That snapshot, measured against the live vault on 2026-10-20:

| Fact | Value |
| --- | --- |
| Capture targets | 53 notes, `capture-targets` ~10ms |
| Linkable open tasks | **498** |
| JSON size | **224,929 bytes** |
| `capture-complete` on `:` | **~30ms** (5 repeats, apollo) |
| `capture-parse` | ~0–5ms |
| `capture --dry-run` of a new task | ~0–10ms |
| Status mix | 422 Blocked, 57 Todo, 11 In Progress, 8 Next |
| Missing block IDs | **285 / 498** (57%) cannot be linked until `capture-task-id` |
| Median title length | 61 characters (range 12–504) |
| Note kinds | 415 project, 80 area, 3 inbox |

The picker matcher is built for *search* (prefix / word / substring / subsequence; AND tokens). Substring `"sase"` hits **96** tasks. That is correct for a filter box and fatal for an unsolicited rail. Related preview must not reuse `FuzzyMatcher` or `capture_link_tasks::match_score` as the ranking function.

Local ranking of a Bob snapshot *is* allowed. The thin-client decision says the app may filter or rank what `bob` returned. The agenda and every picker already do. What the app must not do is decide which tasks exist, or splice `@route:id` by string interpolation.

### Idle agenda is the layout precedent

An empty draft shows today's ledger under a fixed eye line, cached in memory, farthest-first folding, no scroll, focus never leaves the editor (`decisions:idle-capture-shows-ledger-agenda`). Typed preview grows downward from that same top. The first keystroke dims the agenda; the preview then takes the region. Related content should join the preview stack, not fight the agenda for empty-draft space.

### Linking grammar already covers the "I want to connect these" half

Once the user knows the other task, capture already does the write:

- `@route:id` / `:` picker — link into a Pomodoro
- `&` / `*` — Depends-On / blocks
- `~` / `~~` — inert LINKS / LINKED FROM relations (`docs/guides/link-related-tasks.md`)

The missing piece is *discovery while creating*, not a new relationship type.

## Matching: what actually works on this vault

I scored the live 498-task snapshot with the same family of metric `bob ref` already uses for title candidates (`ref_library::title_score`: casefold, strip non-alphanumerics, drop stopwords, Dice on token sets, 90-floor when a 3+ word shorter title is contained in a longer one). Display text was cleaned like the pickers (`[[path|Alias]]` → `Alias`).

Results:

- Recapturing the **first six words** of an existing title almost always yields **exactly one hit at ≥90**, the original task. That is the feature.
- The vault currently has **one** exact-normalized duplicate pair (the same docs-site title in two notes). The backlog is not a duplicate swamp. The win is preventing the next recapture, not cleaning hundreds of twins.
- Short generic captures (`buy groceries`, `fix flake in capture complete`) produce **zero** useful hits at ≥75. At ≥50, `buy groceries` false-matches `BUY new dryer!` on the token `buy`. Short queries must be gated off.
- Medium specific captures work as related, not duplicate: `sase artifact create` scores 90 against `Improve sase artifact create command!` and a second artifact-hooks task; `install bob mac capture` scores ~60–67 against four bob-mac-capture tasks.
- Picker-style subsequence/substring matching is far too noisy to show unsolicited.

**Scoring rule to ship (bob-owned, golden-tested):**

Clean both sides to picker display text. Tokenize like `title_score`. Then:

| Band | Rule | UI |
| --- | --- | --- |
| Duplicate | score ≥ 90, or normalized exact title, or 3+ token containment | Amber "Looks like a duplicate" row, first |
| Related | score ≥ 60 **and** ≥2 shared significant tokens **and** the query has ≥3 significant tokens | Quieter "Related" rows |
| Drop | anything else, including all queries below the length/token gate | Omit the rail |

Route boost: if the draft already names `@route`, break ties toward that note. Status boost: at equal score, Next / In Progress / Ready before Blocked. ID-less tasks still appear (they are real duplicates); accepting a link later uses the existing Add block ID flow. Do not surface a percentage. Surface a reason chip Bob authored: `Same title`, `Starts the same`, `Shares 4 words`, `In sase.md`.

Do not use embeddings. Titles here are long and distinctive; Dice already separates recapture from noise; an on-device or networked model would add latency, a second semantic implementation, and vault text leaving the box, for a problem this metric already solves.

## Performance design

### Budget

The panel's live path today, after the 50ms debounce:

```
parse  (~0–5ms)  →  dry-run preview (~0–10ms, lane "preview")
                 ↘  completion (only in a picker/completion context)
```

Related search must not sit on the preview arrow. Target:

- Preview still settles in the current envelope (parse + dry-run).
- Related may arrive later; p95 for the extra spawn should stay under ~50ms on the Mac. **This number is unverified on macOS.** Apollo (Linux, warm cache) does the full 498-task discover in 30ms. The original replacement research measured ~5ms dry-run on athena versus ~95ms per stage through a login shell; the app already spawns `bob` directly with a GUI-safe environment. If Mac discover is >80ms, cache the snapshot in the app (below) rather than widening the dry-run.

### Recommended transport

New sibling command, not a `bob capture` subcommand (CLI rule: capture's free-text swallows nested verbs; `capture-*` names are frozen siblings):

```
bob capture-related -f json -- <draft>
```

Bob parses the draft, keeps only items that would create tasks, applies the length/token gate, scores against `capture_link_tasks::discover`, and returns an additive per-item list. Empty drafts, picker needs, pomodoro ops, refs, toggles, and existing-task gestures return `{ "ok": true, "items": [] }`. `--all-tasks` is irrelevant; ID-less open tasks are included, matching the `:` picker.

Mac:

- Lane `related`, `cancelsPreviousInLane: true`, same 20s timeout as everything else.
- Start only after parse `mode` (or a batch item mode) is `task` / `sub_bullet` that creates a task, needs is empty, and the gate passes.
- Do not wait for dry-run. Do not block Return on an in-flight related call.
- Decode with `decodeIfPresent`. Unknown `kind` values degrade to `related`. `schema_version` other than 1 is ignored (rail hidden), same spirit as other additive fields.
- Cache the last response by `(draft, bob identityToken)`. Byte-identical titles while typing inside a word should not respawn if the gated query string is unchanged; still cancel in-flight on draft change.

A resident index or FFI daemon is not justified at 30ms discover. If Mac measurements fail the budget, phase 1b is: prefetch the `task_link` snapshot at launch / vault events the way the agenda prefetches `capture-pomodoros --tasks`, then either (a) pass nothing and keep scoring in `capture-related` because 30ms is only paid when the title is stable, or (b) rank the cached snapshot in-process with a Swift port of `title_score` covered by the same goldens. (a) is simpler and stays thin-client. (b) is the picker pattern and is the fallback, not the first cut.

Do **not** hang matches off `capture --dry-run`. Dry-run already snapshots destination notes to plan writes. Related search snapshots *every* capture target. Combining them makes every `=` / `x` / `@` preview pay for a 498-task walk it does not need.

## Layout and visual design

### Where it lives

Inside `PreviewPane`, under the creating item's card, in the same thin-material rounded rectangle. Not a second pane, not a picker card, not a footer takeover.

```
┌ editor (fixed eye line) ──────────────────────────────────┐
│ Investigate retry handling in capture preview             │
├ preview pane ─────────────────────────────────────────────┤
│  New · mac_inbox.md · line 23                             │
│  - [ ] #task Investigate retry handling in capture …      │
│                                                           │
│  ⚠ Looks like a duplicate                                 │
│  [?] Investigate retry handling in the capture lexer      │
│      sase.md  ^retry-lex  · Shares 5 words                │
│  Related                                                  │
│  [/] Capture preview cards for pomodoro close             │
│      bob.md  ^preview-close  · In Progress                │
│                                      +2 more              │
├ footer ───────────────────────────────────────────────────┤
│  Capture                                         ↩        │
└───────────────────────────────────────────────────────────┘
```

The preview card stays the source of truth for *what will be written*. The rail is a caption under it, the way a Pomodoro start card already teaches syntax under its rows.

### Density

Reuse picker-row chrome at a slightly tighter pitch than pull-in (44pt) or completion (48pt):

- Header: 18–22pt, one line, secondary (or orange for duplicate).
- Row: ~36pt. Status SF Symbol (existing `CaptureEditorPalette.taskStatus`), one-line title (wikilink display text, never wrap), trailing route capsule. Locator truncates first.
- Reason chip: caption, quaternary capsule, Bob's `reason_label`.
- Maximum three rows. Extra matches collapse to an agenda-style `+N more` chip that expands in place and resets on hide / draft identity change.
- Total rail height at rest: ~22 + 3×36 ≈ **130pt**. `previewMinimumHeight` is already 92pt; the pane is allowed to grow down. If the below-eye-line budget binds, **fold the rail first**, then preview extras, then never the editor. The eye line and Return stay put.
- Bulk: nest the rail under each creating item. Non-focused items show only a duplicate-band row or a `1 duplicate` chip.

When a picker, Task ID prompt, relation label prompt, pull-in choice, or stash/template shelf owns the auxiliary region, the rail is not shown. Related is preview-only.

### Color and motion

- Duplicate header uses the same orange as Pomodoro override banners and the orange Restart/Swap Return tint, so "this is a warning about what Return will do" is one language.
- Related header uses the chain/link tint already used for `~` relations, at secondary opacity.
- Appear with the 120ms cross-fade the agenda already uses for in-place updates; Reduce Motion: instant. Height is never animated (agenda rule).
- Do not dim the new-task card. The write is still going to happen unless the user changes the draft.
- VoiceOver: one container, "Possible duplicate: Investigate retry handling…, Blocked, sase.md. Related: two more." The rail is informative, not a focus group. Return is still Capture.

### Interaction (v1)

- Click a row: no vault write. Optional later: apply Bob's `replacement` into Bob's item range (link-instead) or `~` + replacement (relate). v1 can ship display-only and still deliver the heads-up.
- Hover: native tooltip with full title, `note_path`, status, section.
- Keyboard: none, v1. A documented `⌃L` "link instead of create" is the right v1.1 key if measurements show people want it; it must call `capture-rewrite` or splice Bob's `replacement` + range, never a Swift-built locator. Tab is taken.

Beauty here is restraint: one warning, two cousins, the same type ramp and capsules the close/start cards already use, no score theater, no empty states.

## Alternatives considered

| Approach | Why it loses |
| --- | --- |
| Add `related_tasks` to `capture --dry-run` | Every live preview pays a 498-task walk, including `x`, `=`, and `@` drafts that never create tasks. |
| Reuse `capture-complete` new-task intent | Today that intent is empty by contract. Overloading it mixes cursor completion with draft-wide duplicate search and would spawn on analyses that currently skip completion. |
| Auto-open the `:` picker when a duplicate exists | Steals the preview, steals keys, and frames recapture as "please search." The user is capturing, not browsing. |
| Mac-side FuzzyMatcher over a cached snapshot | Fast, but the picker matcher is the wrong metric. Local Dice on a Bob snapshot is acceptable as a fallback; it is not the first implementation. |
| Embeddings / LLM "related" | Slow, second semantic engine, vault text egress, worse than Dice on this title corpus. |
| Block Return until related returns | Destroys capture. GitHub's detector is explicitly non-blocking for the same reason. |
| Show related for every new-task keystroke from character 1 | False positives (`buy` / `fix` / `sase`) will burn trust in a week. |
| Checkboxes in the preview to relate on submit | Rejected already for successor offers. Related is not a commit-time multi-select. |
| Daemon / FFI so discover is free | Premature per the thin-client decision. Revisit only if Mac spawn breaks the budget. |
| Put this in the empty-draft agenda | Empty drafts are "what am I doing today?", not "what might I duplicate." Wrong question. |

A credible *different product* is: do not show related at all, and instead teach `:` more aggressively (a one-line hint under new-task previews: "Type : to browse open tasks"). That is cheaper and already complete. I would not ship only that. Recapture of a 60-character title is not a search problem; it is a recognition problem. The rail is recognition. The picker is search.

## Recommended solution

### Contract (bob-cli first)

Add `bob capture-related` as a capture-protocol sibling.

- Input: the full draft (stdin or `--`), same as parse/complete.
- Behavior: parse items; for each item that would create a new task and passes the gate, score against `capture_link_tasks::discover`; return at most 5 matches per item (Mac shows 3).
- Output (schema 1), additive and omit-empty:

```json
{
  "ok": true,
  "schema_version": 1,
  "items": [
    {
      "index": 0,
      "query": "Investigate retry handling in capture preview",
      "matches": [
        {
          "band": "duplicate",
          "score": 92,
          "reason": "shared_tokens",
          "reason_label": "Shares 5 words",
          "replacement": "@sase:retry-lex",
          "requires_block_id": false,
          "route": "sase",
          "note_path": "sase.md",
          "block_id": "retry-lex",
          "status_symbol": "?",
          "status_name": "Blocked",
          "text": "Investigate retry handling in the capture lexer",
          "group": "note",
          "section": "Capture",
          "pomodoro": null
        }
      ]
    }
  ]
}
```

Candidate fields mirror `task_link` so the Mac can reuse `CapturePickerTaskStatus`, wikilink display text, schedule capsules, and the Add ID prompt. `replacement` is empty for ID-less rows, same as the picker. Goldens cover: short query → empty; recapture of an existing title → one duplicate; routed draft prefers that note; blocked and ID-less rows still appear; non-creating drafts → empty.

Help: `-h` excellent, options alphabetical, short aliases (`-f/--format`, `-b/--bob-dir`). No nesting under `bob capture`.

### App (bob-mac-capture second)

1. `BobProcessClient.captureRelated(_:)` on lane `related`.
2. `CaptureRelatedPresentation` built only from Bob's JSON (wording, bands, accessibility). No Swift scoring in v1.
3. `RelatedTaskRail` in `PreviewPane`, under the creating item, fold-first, 3-row cap, `+N more`.
4. Older bob: clap unexpected-argument → remember unsupported per `identityToken`, hide the rail (same pattern as `--refuse-override`).
5. Render fixtures for duplicate-only, related-only, mixed, ID-less, bulk, and empty (empty = no rail, existing preview unchanged).
6. Signpost interval `related-refresh` plus event `related-empty`.

### Phasing

0. **Measure on the Mac** (scratch copy, not Bryan's checkout): time `capture-complete -- ":"` and a prototype `capture-related` against the live vault. If discover >80ms, add snapshot prefetch before shipping the rail.
1. bob-cli contract + goldens + docs (`docs/capture.md` pointer, protocol row in Mac `docs/protocol.md`).
2. Mac decode + rail + lane; display-only.
3. Folding, VoiceOver, dark/light fixtures, Reduce Motion.
4. Optional `⌃L` / click: apply `replacement` as link-instead (Add ID flow when `requires_block_id`).
5. Optional completed-history duplicates (dependency-picker's history section), duplicate band only.

Do not ship 4 or 5 until 2 is quiet in daily use. False positives are worse than a missing cousin.

### What I would not do

I would not treat "related" as the product name in the UI. I would not put matches in dry-run JSON. I would not show the rail for titles under the gate. I would not let it scroll the editor or steal Return. I would not auto-link.

## Risks

- **False positives** on shared project nouns (`sase`, `bob`, `capture`, `agent`). The 3-token + ≥60 rule is the mitigation; watch real drafts after ship and raise the related floor before adding more rows.
- **Blocked-heavy corpus.** 84% of linkable tasks are Blocked. Duplicate of a blocked task is still a duplicate; the row must show `[?]` so it does not look Ready.
- **ID-less majority.** 57% cannot be linked in one keystroke. v1 still shows them (heads-up is valid). Link-instead must go through Add ID, or it will invent grammar.
- **Mac spawn unknown.** All timings in this note are apollo/Linux. State that limit in any plan that cites them.
- **Bulk templates.** A 20-row `@@template:` draft could request 20 related searches. Score only rows that pass the gate, cap total matches per draft (e.g. 8), and collapse per-row rails to chips.
- **Trust.** One bad week of noisy cousins and the rail becomes wallpaper. Prefer showing nothing.

## Evidence

- `decisions:mac-capture-is-a-thin-client`, `decisions:idle-capture-shows-ledger-agenda`, `decisions:unblocked-tasks-are-offered`
- Mac: `CapturePanelModel.scheduleAnalysis` / `startLivePreview`, `BobProcessClient.captureLivePreview` / `captureComplete`, `docs/capture-previews.md`, `docs/task-pickers.md`, `docs/idle-agenda.md`, `CapturePanelLayout`
- bob-cli: `capture_link_tasks::{discover,match_score}`, `capture_complete` new-intent empty test, `ref_library::title_score`, CLI rule against nesting under `bob capture`
- Live vault, 2026-10-20, apollo: 53 targets, 498 linkable tasks, 225 KB `task_link` payload, parse ~0–5ms, dry-run ~0–10ms, full discover ~30ms
- GitHub Changelog 2026-06-18, "Detecting Duplicate Issues" public preview (title ≥20 chars, up to 3 suggestions, non-blocking)
- GitHub Community #146547 (create-time similar issues); Atlassian community 2025-01-23 (Jira has no native create-time duplicate check)

## Open questions for the lead / plan

1. Confirm Mac discover latency before locking the transport (spawn vs prefetch).
2. Confirm v1 is display-only. I recommend yes.
3. Confirm completed tasks stay out of v1. I recommend yes.
4. If Bryan wants a convert gesture in v1, use `⌃L` + Bob `replacement`, not Tab.

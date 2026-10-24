# Pomodoro themes: a reusable vocabulary with safe history editing

Independent research by **cdx** · 2026-10-24

## Recommendation in brief

Build this feature. Remembering names and giving them a consistent visual identity should make planning faster and reduce small naming variations. Keep it lightweight: the daily ledger remains the source of session history, with a small synced file for explicit suggestion preferences. Avoid turning themes into another project taxonomy that requires maintenance.

My recommended design has four parts:

1. **Today first, history second** in every relevant name picker, with clear labels distinguishing selecting an existing session from reusing a name.
2. A **Pomodoro themes manager** for searching history, renaming across daily files, hiding suggestions, and restoring them. A small visible action in completion opens that manager or hides the selected name.
3. **Deterministic, restrained theme accents**, applied to the name itself across capture, Obsidian, and CLI views, while preserving the existing meaning of home/area colors and status indicators.
4. A **recoverable rename transaction**, with a concrete preview, exact matching, concurrency checks, and undo. Global rename must remain distinct from the existing rename-one-session operation.

Two prerequisites are easy to underestimate: name identity currently differs from selector identity, and a Pomodoro's full name differs from the components counted by the plan budget. Resolve those contracts before adding rows to menus.

This is a research recommendation, not an implementation or an approved implementation plan. No product files, glossary files, or live vault files were changed. I did not consult another researcher’s report, findings, or chat.

## What the code actually does today

The inspected revisions are:

| Repository | Revision |
| --- | --- |
| bob-cli | `30f10f154afb119a51a5ebf27264538342973c88` |
| bob-plugins | `e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10` |
| bob-mac-capture | `22598dc09f6b4b937259e716eab29a8c263e0ca7` |

The following are observations from local source inspection, not assumptions about a future implementation.

| Surface or rule | Current behavior | Design implication |
| --- | --- | --- |
| Ledger representation | A named session has an optional ` — NAME` suffix after its `()` placeholder or leading time range. The scanner exposes name, slug, line, state, and a stale-safe reference. [C1] | Preserve ordinary Markdown. No inline IDs, HTML spans, or color markup are necessary. |
| General name completion | Reads today’s daily note; lists open selectable names and nameable rows. Creation can be inserted before substring matches. [C2] | Historical discovery is new, and creation ordering needs an explicit adjustment. |
| Named-start completion | Has separate start, create, completed-today “again,” name-it, and running cases. The running entry is currently last. [C2] | A historical name is not a historical session target. Keep its operation explicit. |
| Name assignment | `capture-pomodoro-name` assigns a name to one open unnamed/unselectable entry today. It is not a global rename endpoint. [C3] | Do not repurpose this command into a different operation. |
| Name identity | Display names collapse whitespace and uppercase ASCII; selectors lowercase and replace whitespace with hyphens. Selectors can resolve by prefix. [C1, C4] | `DEEP WORK` and `DEEP-WORK` collide as selectors, although they are different full names. |
| Plan budget | Splits names on every `+`, trims components, and counts distinct non-exempt components. `GTD` is exempt by default. [C5] | A catalog of full names cannot be advertised as identical to the budget’s theme count. |
| Plus signs | Completion explicitly accepts both `C++` and `BOB+SASE`. [C6] | Do not invent a new interpretation of `+` during rename or color assignment. |
| Obsidian linking | `block-id-prompt` has its own current-day model and new-name row in the Ctrl+Shift+Enter picker. [P1] | Updating Rust/Mac alone misses an important completion surface. |
| Obsidian moving | `bob-navigation-hotkeys` has separate bullet-move and entry-move/merge/rename pickers. Entry rename is local to that session. [P2] | Reusing history must map to the operation of the active picker; it must never silently mean “rename globally.” |
| Mac acceptance | A create/again completion generally edits the draft; the later aggregate `bob capture` performs the write. A name-it row has a separate prompt/write flow. [M1] | Historical selection should retain draft-first behavior. The name-it prompt also deserves suggestions. |
| Existing colors | Pomodoro homes already have deterministic area hues, with a documented eight-slot palette and FNV-1a fallback. Obsidian has editor and Reading-view home-chip renderers. [C7, P3] | Reuse the rendering architecture, but do not overload home/area hue with theme identity. |
| Sync | The vault uses Git sync. JSON is generally ignored except for narrow allowlists such as Keep receipts. [C8] | A new preference JSON file will not necessarily sync merely because it is inside the vault. |
| Mac invalidation | Agenda refresh ignores hidden paths except a specific Tasks-settings exception. [M2] | A hidden theme-preference file needs an explicit refresh dependency. |
| Bulk writes | Capture already stages files, checks disk preimages, and rolls back write failures. Its comments explicitly say this is not cross-process locking or a fully serialized transaction. [C9] | Reuse these primitives, but do not call a multi-file rename crash-atomic without additional recovery work. |

I reviewed the SASE glossary and applicable decisions through audited memory reads. In particular, the Mac app must remain a thin client: bob owns grammar, completion facts, preview, and writes. The existing agenda contract also makes bob the source of ledger facts. The findings below respect those boundaries.

## Is this a good idea? What I would change

The strongest part is **reuse at the moment of naming**. It removes recall work exactly when it is needed. Global rename is useful for consolidating spelling and evolving a label; hiding keeps history from turning into permanent menu clutter. Color can make recurrent work recognizable without adding another field to the ledger.

The danger is creating an overly consequential picker. The user may be typing a task, moving a bullet, or starting a timer; a completion menu should not casually launch a vault-wide history rewrite. The other danger is suggesting every historical label equally: old one-off names can crowd out the handful relevant this week.

I recommend these explicit requirement adjustments:

| Original direction | Recommended adjustment | Reason |
| --- | --- | --- |
| “Disable a theme so it no longer appears in completion menus” | Call the action **Hide from suggestions**. Remove it from name-reuse suggestions, including create/name prompts. Preserve already-existing sessions in operational session pickers, with a “Hidden theme” annotation when needed. | A preference about future suggestions should not make today’s session impossible to select, move into, inspect, or finish. This is a deliberate exception to a literal interpretation of “all menus.” |
| Possible Ctrl+D action | Use a visible **Theme actions** control and context menu, plus a manager command. Do not ship bare Ctrl+D as the default. | On macOS Ctrl+D is forward-delete. Accidental preference changes while editing would be frustrating. |
| “Distinct color” | Guarantee **stable color assignment**, not global uniqueness or meaning without text. | A finite accessible palette cannot give every possible name a unique recognizable color. |
| Global rename | Default to **exact full-name rename**. Offer an explicit separately previewed “Also change this component in combined names” scope. | Substring replacement is unsafe; full names and plan components are different concepts already. |
| Name-based colors | A rename adopts the destination name’s color; show this in the preview. | Keeping the old color would require identity-based colors or overrides, contrary to the name-determinism requirement. |
| Reuse historical names | Preserve their exact canonical display names, not only their selector slugs. | Reusing `DEEP WORK` must not quietly author `DEEP-WORK`. |

If you insist that hidden themes disappear from *all* name menus, that policy is implementable, but the UI must still retain a separate explicit session-addressing route. I prefer the distinction above because it matches the difference between a vocabulary and the work already on today’s ledger.

## Vocabulary, identity, and compound names

### Proposed glossary entry

> **Pomodoro Theme** — also called a *Pomodoro name* or *theme*. The authored label in the ` — NAME` suffix of a [[pomodoro]], used to describe and reuse a work-session focus across daily files. Multiple Pomodoros may share a theme; the theme is not a session, task status, project, or derived task home. Names follow Bob’s canonical naming rules. A combined name can contain `+`-separated components; the plan budget counts distinct non-exempt components, so one reusable full name need not count as one budget theme. Hiding a theme affects suggestions, not recorded sessions.

This is proposed wording for `glossary:pomodoro-theme`, with aliases `pomodoro name` and `theme`. The user explicitly requested the new glossary term. The wording intentionally exposes the existing full-name/component distinction instead of pretending it does not exist. If “theme” should instead mean strictly one budget component, name the reusable catalog **Pomodoro names**; do not silently change budget semantics just to make the terms fit.

### Keep three identities separate

| Object | Identity | Example |
| --- | --- | --- |
| Session | Daily file plus a validated session reference | The second BOB session on 2026-10-23 |
| Reusable full name | Canonical full text: collapsed whitespace and ASCII uppercase | `DEEP WORK`, distinct from `DEEP-WORK` |
| Budget component | Existing `split_components` and `normalize_component` contract | `BOB + DECKS` contributes BOB and DECKS |

Do not use the selector slug as the theme key. Do not add UUIDs to every ledger row. A full-name key suffices for history aggregation and suggestion preferences while the feature is explicitly name-based. A future requirement for stable identity through renames, rich theme descriptions, or external references could justify IDs; this request does not yet need them.

Keep punctuation meaningful. Canonicalization must not silently fold slashes into hyphens, strip plus signs, or equate differently ordered composites. `BOB+SASE` and `BOB + SASE` currently have different full spellings; a manager can help consolidate them, but discovery must not silently rewrite them.

### A surprising correctness prerequisite: lossless selection

A naive history implementation will fail in two ways:

* Yesterday’s `DEEP WORK` becomes completion replacement `deep-work`. Without a matching session today, the creation path canonicalizes that selector, which can author `DEEP-WORK`. The display-name spelling is lost. [C1, C4, C10]
* Yesterday’s `BOB` becomes replacement `bob`. If today contains only `BOB BUILD`, the existing prefix selector can resolve to BOB BUILD instead of creating/reusing BOB. [C1]

These are source-derived failure scenarios; I did not execute them against the live vault.

**Recommendation:** add an exact, lossless name literal to capture grammar before enabling general historical completion. A concrete syntax candidate is `=#"DEEP WORK"` for start and `@route:id#"DEEP WORK"` for linking. Inside a literal, match canonical full names exactly; when no appropriate session exists, create one with that name through the existing planner. Existing unquoted selectors keep their behavior. Double quote is not currently a valid name character, which makes this a tractable delimiter, but lexer interactions still need implementation tests.

Bob should emit the complete replacement text; Swift must insert it as opaque text. The literal stays visible and copyable in the draft, and dry-run and commit use the same interpretation. This is preferable to an invisible selection side channel that stops working when text is copied or edited. For shell examples, quote the entire capture argument so the shell does not remove the literal’s quote characters.

This is an added requirement I consider justified by reliability. If another exact literal fits the language better after parser work, change the spelling while keeping the contract. A historical row must never claim it creates X while submitting an ambiguous prefix or a lossy spelling.

## Completion design

### What a row means

Use shared semantic categories, with operation labels supplied by bob:

| Category | Example text | Meaning on acceptance |
| --- | --- | --- |
| Existing session | `BOB · Next · 3 links` | Select that eligible session under the picker’s existing rules. |
| Completed today / historical name | `DEEP WORK · Last used Oct 18 · Reuse` | Reuse the name; create or name a current session when the operation is committed. Never reopen or copy an old session. |
| New authored name | `Create “RESEARCH”` | Use the typed valid name, with budget preview. |
| Unnamed existing session | `09:20–09:50 · Name it` | Open the name prompt; that prompt uses the same vocabulary suggestions. |

Do not copy tasks, durations, work logs, or historical status from a reused name. A theme is not a template. If session templates are later desired, make them a separate feature.

### Ranking contract

Filter first, then order by provenance. A matching current-day entry outranks a historical name even if the historical name is an exact query match and the current-day name is a substring match. That directly implements the user’s requested precedence.

Recommended order:

1. Eligible, matching existing sessions today, in the established operational order for that picker. Preserve next-up and override semantics; a running-session action must still say what it does.
2. Matching reusable names, with completed-today reuse first, then past history. Within each subdivision: exact match, prefix match, substring match; then last-used date descending, usage-days descending, canonical text.
3. Explicit “Create this new name” when valid, not already represented, not hidden, and the operation can place it.
4. Unnamed/name-it affordances, in a visually separate section.

For pure naming fields, “Today” names are name values, not commands to move/select sessions. For an existing-session move picker, a historical row means creating a new destination; in the single-session rename picker it means renaming that one entry. A context adapter must provide those labels and actions. Reuse the vocabulary, not blindly the same command.

Use distinct-day frequency rather than raw session count as the secondary history signal so repeated short sessions on one day do not dominate forever. Start with recency, not a clever learned score. Keep all history searchable; show a small initial window, such as six historical rows, and let the manager expose the complete list. An initial rendering limit must not become a silent history cutoff.

Deduplicate historical names against eligible current rows by canonical full-name identity. Preserve multiple current sessions when the existing picker addresses them separately. “Same theme” must not collapse multiple sessions into one invisible target. Refreshes retain selection by semantic row identity, never by array index, so async history arrival does not change what Enter accepts.

A query like `wo` might render as:

```text
Theme                                      wo|

TODAY
▏ WORKFLOW       Next · 3 links

USED BEFORE
▏ DEEP WORK      Last used Oct 18 · Reuse
▏ WRITING WORK   Last used Oct 02 · Reuse

Create “WO”

Theme actions…                              Manage themes…
```

The narrow accent beside each name uses its theme color. TODAY and USED BEFORE are quiet section labels; time/status and action text remain neutral. The action footer sits outside the option list.

### Completion is read-only until an explicit action

Fetching, filtering, hovering, and accepting an ordinary historical suggestion do not update durable preferences or “last used.” Usage is derived from committed ledger entries. Escape cancels normally. Reusing a hidden name by explicitly typing a complete capture remains permitted but does not automatically unhide it; the manager offers Restore.

No name-creation candidate should bypass existing missing-section, ambiguous-running-session, strict-budget, or placement checks. A vocabulary can exist even when today’s ledger is unavailable, but a picker must not offer an executable operation that bob will necessarily reject. In a name-only prompt it can still suggest values; in an operation picker, show a concise availability reason.

## Hiding, restoring, and global rename UX

### The manager is the discoverable home

Add **Manage Pomodoro themes…** in both the Mac capture app’s command/menu surface and Obsidian’s command palette. Link to it from the completion footer and a theme context menu. The manager has search, Active/Hidden filters, color accents, last-used date, distinct-day/session counts, and these actions:

* **Rename everywhere…**
* **Hide from suggestions** / **Restore suggestions**
* **Show occurrences**

Do not create a separate note per theme. Do not require catalog membership before typing a new name. No automatic archiving, automatic merge, or automatic color editing in v1.

Hiding is immediate and reversible, with a short notice: `DEEP WORK hidden from suggestions. Undo`. Persist only an explicit preference, refresh consumers, and keep history, stats, and current session behavior intact. The manager must display hidden names even if their last ledger occurrence was subsequently deleted, so Restore remains possible.

### Why not Ctrl+D by default?

Apple documents Ctrl+D as forward-delete in text editing. WAI’s editable-combobox guidance also recommends preserving platform editing keys. These are strong reasons not to reinterpret that key merely because suggestions happen to be visible. [Apple keyboard shortcuts](https://support.apple.com/en-us/102650), [WAI combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/).

For Obsidian’s web UI, avoid embedding miniature interactive buttons inside ordinary listbox options; that model does not expose nested controls accessibly. Put actions in a separate toolbar/footer or open a proper menu/dialog. Native Mac controls should provide equivalent keyboard and VoiceOver actions without importing DOM-specific mechanics. [WAI listbox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/listbox/).

If a fast hide shortcut proves valuable, make it configurable and show it beside the action. If Bryan explicitly prefers Ctrl+D, scope it to an intentionally focused suggestion selection, suppress repeats, provide Undo, and preserve forward-delete when the editor/name field owns text-editing focus. Do not make a hidden keymap the sole way to discover this feature.

### Rename preview

`Rename everywhere…` opens a compact sheet:

```text
Rename Pomodoro theme
DEEP WORK → FOCUS

68 sessions in 41 daily files
2026-05-04 — 2026-10-24
Whole name only

[old accent] DEEP WORK  →  [new accent] FOCUS

Review changes…                       Cancel    Rename
```

Counts and dates above are illustrative, not measured vault statistics.

The detailed preview groups changed lines by file, states whether today's running session is included, and shows target-name collisions. Renaming to an already-used full name is **Merge names**, requiring that explicit choice. It combines catalog history/preferences but never merges session rows, moves tasks, changes durations, or removes duplicate sessions. Reusing a target spelling and merging actual sessions are different operations.

The normal whole-name operation changes every matching managed suffix in every canonical daily file, including past, present, and future dates. Preserve checkbox status and all unrelated bytes. Cancellation/other ledger statuses need explicit parser coverage: do not claim “all daily files” while silently skipping a canceled named row because the completion scanner only exposes open/completed targets.

For combined names, provide a separately scoped preview: `Also replace this component in combined names`. Match complete components using the existing plan contract, never text substrings. Example: BOB → BOB CLI changes `BOB + DECKS` but not `BOBBY`. Show effects such as `BOB + BOB CLI` becoming repeated components; require an explicit normalization/merge decision instead of silently deleting a component.

The existing `C++` acceptance versus all-plus budget splitting makes component rename particularly hazardous. Full-name rename of C++ is safe; renaming component C can unexpectedly touch a C++ name under the current budget rules. The component preview must enumerate that case and require a scope decision. Do not combine a plus-grammar migration with this release.

A local “Rename this session” action stays available in its existing picker, with that exact scope in the label. Enter in a move/rename picker must never become a vault-wide rename shortcut.

## Storage and service architecture

### Three layers, with one source for each fact

| Layer | Suggested storage | Authority and update policy |
| --- | --- | --- |
| Session history | Existing canonical daily Markdown files | Authoritative occurrences, dates, names, and statuses. |
| User preferences | Proposed `.bob/pomodoro-themes.json` | Versioned, synced explicit hide/restore settings and rename bookkeeping only. |
| Discovery acceleration | Local cache under Bob’s cache directory, keyed by vault identity | Disposable per-file fingerprints, aggregated names, dates/counts; rebuildable from ledger and preferences. |

Do not store continuously updated usage counters in the synced preference file. Deriving them avoids a Git change on every completed session and reduces multi-host conflicts. Do not put vault vocabulary policy in machine-local XDG config or plugin `data.json`; Mac, CLI, and Obsidian need the same preferences.

A minimal policy record can use the canonical full name as a key, `hidden: true`, and an explicit revision/change identifier. Schema validation must reject duplicate/conflicting records and unsupported versions without replacing them with defaults. Hidden state is durable intent; a cache rebuild must never reactivate a name.

For renames, move the source preference to the destination when new, preserve an existing destination’s policy when merging after preview, and keep a small source tombstone recording the rename. A tombstone suppresses rediscovery of the old spelling if an offline host later syncs an old occurrence. It is not an invisible selector alias and must not auto-rewrite newly arrived files. Show a “retired name reappeared” repair item with a fresh preview.

No UUIDs or aliases are needed in ledger text. An operation ID for recovery is useful and is not the identity of every theme.

### Sync is part of the feature

The current vault allowlist requires a specific exception for the proposed JSON path, analogous to existing `.bob/gkeep/imports/*.json` and stats journal allowances. Add and verify the exception as part of deployment, with the rule reaching all hosts through vault sync. Keep caches and recovery snapshots excluded. [C8]

A Git merge of different valid edits is fine only if the policy remains valid and its semantics are checked. Same-name hide/restore conflicts must be surfaced; do not silently use timestamp last-writer-wins across machines with clock skew. An unresolved or conflict-preserved policy file should put management into a clear unavailable state and suppress untrusted historical suggestions, while keeping ordinary current-session operations available.

A local lock is not a distributed transaction. For global rename, preflight the configured sync state, record the local revision, coordinate the local sync cycle so it cannot publish half the write, and report unmerged remote changes instead of promising to update a machine that is offline. After later sync, tombstones and validation expose reintroduced spellings. This is ordinary Git reconciliation, not a reason to add a bespoke CRDT.

### Discovery and cache strategy

Extract a shared daily-file recognizer from the existing canonical `YYYY/YYYYMMDD.md` logic. Use the existing ledger parsing rules, fenced-code exclusion, and canonical names; do not grep all Markdown for an em dash. Exclude `_conflicts`, backups, non-daily templates, and snippets. The day override can participate in current-day completion without redefining the scope of global historical rename. [C1, C11]

Index valid authored names in supported daily entries. Record dates from the daily file, not filesystem modification time. Avoid guessing names from task text, task homes, frontmatter titles, or unnamed placeholders. Invalid/unselectable historical names can be shown in the manager’s repair view rather than becoming unusable completions.

Use a two-part read: always re-read today’s ledger for operational candidates, then merge a cached historical catalog. Refresh changed/deleted/renamed daily files incrementally; content digests make explicit reindex and rename preview authoritative even if metadata fingerprints are suspect. Validate the preference revision separately. A cold rebuild must expose incomplete status and must not falsely claim that a truncated index is complete.

I did not benchmark the actual vault. Measure cold discovery and warm completion on the Mac before choosing a cache implementation or TTL. Suggested acceptance targets, not measured facts: warmed historical merging should add less than one frame of UI work, and historical completion should normally settle within roughly 100 ms of a request on the target machine. No full-vault scan on every keystroke. A JSON cache is sufficient to start if measurements support it; SQLite is not a prerequisite.

### Bob owns the contract; clients own interaction and pixels

Proposed public command family: `bob theme`. Its membership rule is “inspect and manage Pomodoro theme vocabulary.” A bare group can default to a read-only list. Suggested verbs are `list`, `hide`, `restore`, `rename`, and `undo`; these are proposed names, not existing commands. Keep help alphabetized and give public long options short aliases, following project CLI rules. Do not add subcommands beneath `bob capture`.

The theme service should provide versioned structured results: canonical name/key, provenance, last-used date, counts, hidden state, color token, permitted actions, and warnings. Extend existing completion/agenda/preview JSON additively where possible. Distinguish `source` (today/history) from `action` (select/create/name/rename-local); these are different axes. Preserve existing fields so older clients degrade sensibly. Test old-client/new-bob and new-client/old-bob combinations rather than assuming optional fields alone guarantee compatibility.

The Mac app must not scan vault files or hash names using its runtime-randomized hash. It asks bob for facts, applies opaque replacements, renders tokens, and submits one aggregate capture. Its manager calls bob’s theme commands. Add a narrowly scoped watcher exception or bob-supplied dependency signal for the theme policy file, plus refresh after theme actions, panel show, wake, day rollover, and dropped filesystem events. [M1, M2]

For Obsidian, centralize vocabulary access and color tokens in bob-ledger-tools’ shared API, with both block-id-prompt and bob-navigation-hotkeys consuming it. Existing picker logic uses live editor buffers; retain that correctness while adding a historical snapshot. Prefer a bob subprocess for historical catalog/policy/rename on desktop, and a shared adapter only where local live-buffer rendering requires it. Do not create three independent history scanners or let each plugin persist its own disabled list. Define a graceful fallback when bob is unavailable: existing local session operations continue, history/management is explicitly unavailable. Mobile support is a separate adapter decision; it should not be implied by desktop completion work.

## Safe global rename implementation

Treat rename as an infrequent bulk edit, not a string replacement helper.

1. **Discover and plan from source.** Enumerate all canonical daily files and parse only managed suffixes. The preview cannot rely solely on a possibly stale history cache. Collect exact preimages, target spans, new content, metadata changes, collisions, and unsupported rows.
2. **Resolve semantic dependencies.** Check `plan.exempt`, `plan.inventory_labels`, and any other configuration that directly names the affected components. GTD → REVIEW can otherwise change review attribution and budget behavior. For v1, refuse such a rename with a precise dependency explanation unless the operation includes a reviewed configuration migration. Do not silently edit home/chezmoi configuration from a vault operation. [C5, C7, C12]
3. **Prepare a reviewable intent.** Return an operation ID/digest binding the selected scope, old/new names, preference revision, file list, and expected bytes. Applying a preview must validate this same intent, not silently widen it after a rescan.
4. **Coordinate local writers and editors.** Acquire a documented theme/maintenance lock plus the existing sync exclusion in a consistent order. Preserve live editor buffers: the Obsidian entry point flushes and validates affected buffers before apply and refreshes them after; if another buffer changes or cannot be coordinated, refuse/retry. A CLI preimage check alone cannot see every unsaved buffer. Current capture writers do not automatically become serialized merely because rename takes a new lock. This cross-writer integration is required work.
5. **Stage, journal, and recheck.** Stage same-filesystem replacements; save durable before/after hashes and backups in local recovery storage; recheck targets immediately before replacing them. Reuse capture’s staging/preimage primitives, adding crash recovery rather than assuming existing rollback handles process death. [C9]
6. **Apply and verify.** Replace only affected name spans and policy data; preserve line endings, trailing metadata where supported, session statuses, task links, indentation, durations, and logs. Reparse every changed file. Publish new catalog revision only after success. Report changed session/file counts and any exclusions honestly.
7. **Recover and undo.** On ordinary failure, roll back only files still matching this operation’s postimages. On crash, the journal identifies pending/committed files and supports resume or rollback. Undo uses the same checked inverse patches; it must stop on later user edits rather than overwrite them. Keep a manager entry for recent operations, not only a disappearing toast.

A sequence of atomic file replacements is not an atomic multi-file transaction. The user-facing promise should be **validated and recoverable**, with explicit failure states, until a stronger guarantee is actually implemented and tested. Dirty-file/sync handling needs a bounded protocol; a vague “save everything first” notice is not an adequate substitute.

Global rename has extra semantic consequences even when bytes are correct: it can reduce distinct budget components, produce duplicate-name warnings, or change review classification. The preview should distinguish expected consequences from forbidden ones. Preserve total session count and recorded duration, not necessarily every derived grouping.

## Visual design: recognizable, quiet, and consistent

Use the name as the visual anchor. Give it a narrow colored leading stroke or a subtle rounded accent, with high-contrast text. Keep timer state, selection focus, and budget warnings in their existing roles. A colored name should not look like a clickable tag if it is only a label.

Existing home chips answer “where did the linked work belong?” Theme accents answer “what did I call this session?” Keep those visibly distinct: a theme-name accent plus the existing muted home chip/dot, with clear tooltip/accessibility labels. Never replace `homes.hue` with `theme.color`. A BOB session may link to work in several areas; its name and attribution do not have to match. [C7]

### Deterministic color contract

Use a versioned, language-independent mapping such as:

```text
key   = canonical full name
hash  = FNV-1a-32(UTF-8("pomodoro-theme-v1\0" + key))
slot  = hash modulo 12
color = theme_palette_v1[slot]
```

Twelve is a proposed palette size to validate, not a measured optimum. The existing eight-slot home palette establishes a useful implementation precedent, but its exact colors were designed for a different visual role. Freeze the hash inputs and mapping with cross-language test vectors. Do not use Rust’s default hasher, Swift `hashValue`, JavaScript object order, or a list-position assignment.

Ship one checked-in palette specification with light/dark accent values, subdued backgrounds, and terminal fallbacks. Use perceptual color tools such as Oklab/OKLCH when designing the palette, then emit tested sRGB values for consistent CSS and Swift rendering. Oklab/OKLCH are specified in CSS Color 4; that does not make an arbitrary choice of lightness/chroma automatically accessible. [CSS Color 4](https://www.w3.org/TR/css-color-4/#ok-lab).

Name text should meet 4.5:1 contrast in ordinary-size UI, including selected rows. Keep labels, badges, and focus indication independently understandable without color. High contrast and reduced-color settings should retain all meaning; terminal output must respect disabled color. [WCAG contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html), [WCAG use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html).

Collisions are acceptable; recoloring existing names when a new name appears is not. With 12 slots, even three uniformly assigned names have about a 24% probability of some slot collision. Therefore “all visible names have different colors” cannot be a promise of this design. If that promise matters more than stateless determinism, a persisted assignment/override system is a different tradeoff. I would retain deterministic defaults and text redundancy, and defer manual overrides until actual use demonstrates a need.

A full combined name gets one full-name accent in v1. Do not turn `BOB + DECKS` into a rainbow pill, especially while literal plus signs and budget parsing have different implications. A budget view listing individual components colors those component labels by their own name; the scope difference must be clear. Renaming to a new key changes the accent consistently everywhere, including historical rows.

### Surface coverage

| Surface | What to add |
| --- | --- |
| Mac completion | Today/history grouping, reuse labels, theme accents, visible management entry. |
| Mac unnamed-session prompt | Vocabulary completion with no change to the prompt’s single-session scope. |
| Mac draft and dry-run preview | Color the semantic name span, including exact literals, using bob-supplied presentation data. |
| Mac idle agenda and previews | Same name accents in Now, Next, Later, condensed strips, and session summary cards. Preserve existing home chips and fit behavior. |
| Obsidian link/move/rename pickers | Shared names, ranking, hidden policy, and accents, adapted to each picker’s operation. |
| Obsidian Live Preview/source editor | CodeMirror mark decorations on parsed name ranges; preserve text, caret, selection, and Markdown. |
| Obsidian Reading view | A postprocessor decorating the correct managed name text, scoped to canonical daily-ledger rows. |
| Obsidian plan/theme rows | Use the same tokens for displayed full names or clearly labeled components. |
| CLI human reports and status surfaces that display names | Reuse the shared palette with terminal fallback and no-color support. JSON carries tokens, never ANSI. |
| Management screens | Same accent and full name, textual hidden state, occurrence counts and dates. |

Obsidian’s official editor documentation supports mark decorations for styling existing content; view plugins can work from visible ranges to avoid whole-document work. The repository already has paired editor and Reading-view implementations for home chips, providing a practical local template for this feature. [Obsidian decorations](https://docs.obsidian.md/Plugins/Editor/Decorations), [P3].

Do not color every occurrence of the word BOB in the vault. Decorate semantic Pomodoro names. Do not write HTML or CSS annotations into the ledger or use a document-wide DOM mutation observer for name matching.

## Delivery sequence and acceptance criteria

This is the recommended work decomposition; the lead should turn it into a concrete implementation plan after deciding the scope adjustments above.

| Stage | Deliverable | Required evidence |
| --- | --- | --- |
| 1. Contracts | Glossary, full-name/component definitions, exact literal grammar, hidden behavior, color tokens, shared fixtures | Literal round trips preserve spaces/punctuation; existing capture syntax remains compatible; documented decisions for compounds and exemptions. |
| 2. Bob service | Canonical history discovery, preference persistence, cache, theme list/hide/restore, completion integration | History never outranks eligible today rows; hide survives restart/reindex/sync; stale cache cannot choose a session. |
| 3. Client experience | Mac and both Obsidian picker families, manager entry points, colors on primary surfaces | Golden/snapshot and interaction checks across themes, states, queries, focus, and accessibility settings. |
| 4. Rename | Exact and explicit component previews, checked writes, recovery, undo, dependency handling | Failure injection across files, conflicts, editor races, crash/restart, and later edits. |
| 5. Completeness | Remaining agenda/preview/CLI name surfaces, docs/help, sync rollout and compatibility checks | Surface audit and end-to-end exercises on the actual Mac and Obsidian setup. |

Do not release history rows early if lossless acceptance is not ready. Colors/hide/reuse can ship before global rename if the release clearly marks that scope; they should not wait behind bulk-write recovery work. Global rename should not ship as a happy-path-only first iteration.

Essential fixtures and scenarios:

* Today BOB versus historical BOB; today BOB BUILD versus historical BOB; today substring versus historical exact query; completed-today “again” versus older use.
* `DEEP WORK`, `DEEP-WORK`, `C++`, `BOB+SASE`, `BOB + SASE`, punctuation, invalid legacy names, repeated whitespace, and names beginning with digits.
* More than one current session with the same name, unnamed placeholders, missing daily file, missing section, several running entries, and strict budget refusal.
* Hide current/history names, explicit typing of hidden names, restore, undo-hide, deletion of the last occurrence, cache rebuild, and policy conflict. Verify the documented current-session exception.
* Rename whole name and component separately; target exists; target hidden; rename cycles; review-exempt GTD; inventory labels; future daily files; canceled rows; fenced examples and child prose left unchanged.
* CRLF/no final newline, unsupported trailing syntax, permissions failure after several replacements, disk changes between preview and apply, changes during rollback, and crash recovery. Verify session totals/durations and byte preservation outside approved spans.
* New/old bob and client combinations, corrupted cache, unknown metadata schema, reintroduced source names after offline sync, `.gitignore` propagation, and hidden-path watcher invalidation.
* Light/dark/selected/high-contrast surfaces, color collisions, long names, reduced color, VoiceOver labels, Ctrl+D text editing, and keyboard-only access to management.

Use Rust tests for domain/transaction behavior; shared fixture vectors for any JS mirrors and color mapping; Swift decoding/presentation/router tests for the Mac; and manual Obsidian editing/Reading-view checks. Follow bob-mac-capture’s repository rules: portable checks are useful but do not replace compiling Mac UI targets; use its prescribed scratch Mac build/typecheck path and CI test execution. No runtime tests, builds, or live vault mutations were performed for this research report.

## Alternatives I would reject or defer

| Approach | Assessment |
| --- | --- |
| History only, no persistent preference file | Smallest implementation, but “disable” would return after every rescan. Insufficient. |
| Mandatory theme registry with IDs embedded in every session | Strong long-term identity, but a migration and a second authoring system disproportionate to this request. Defer. |
| One note per theme | Adds files and navigation work for what is currently a short session label. No present requirement justifies it. |
| Reuse derived task homes as themes | Confuses authored intent with attribution and contradicts the documented separation. Reject. |
| Global text replacement | Would touch prose, task names, snippets, and partial words. Reject. |
| Separate historical scans/preferences in each client | Predictable cross-client drift and sync bugs. Reject. |
| Automatically infer/project theme names from linked tasks | Reopens the derived-home boundary and changes user-authored intent. Reject. |
| Hash directly to arbitrary HSL text colors | Deterministic but not reliably readable or aesthetically balanced. Reject. |
| Guarantee distinct visible colors by reassigning slots as lists change | Breaks stable visual memory and cross-client consistency. Reject. |
| Alias-only “rename” without editing daily files | Cheap but does not satisfy the explicit historical-update requirement. Could supplement migration diagnostics, not replace the requested operation. |
| Ctrl+D as the only management UI | Fast for its author, undiscoverable and conflicting for normal text editing. Reject as the default. |

## Evidence and research limits

All repository sources below were opened locally through the authorized workspace/repository workflow. The links pin the inspected revisions for review; they were not used to bypass repository access rules. External sources are primary documentation. Source locations are provided to help the implementing agents verify the findings rather than treat this report as a substitute for reading current code.

* **[C1]** bob-cli, [`capture_pomodoros.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_pomodoros.rs), especially `canonicalize_pomodoro_name`, `PomodoroEntry`, `select_named`, `select_by_slug`, `parse_name_tail`, and `without_name_tail`.
* **[C2]** bob-cli, [`capture_complete/pomodoros.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_complete/pomodoros.rs), general and start-specific candidate generation; [`support.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_complete/support.rs), `rank`; [`model.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_complete/model.rs), `PomodoroNameCandidate`.
* **[C3]** bob-cli, [`capture_pomodoro_name.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_pomodoro_name.rs), CLI contract and `assign_capture_pomodoro_name_at`.
* **[C4]** bob-cli, [`capture_language/line.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_language/line.rs), `normalize_task_text` and `selector_slug`.
* **[C5]** bob-cli, [`plan_budget/mod.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/plan_budget/mod.rs), component normalization/splitting and budget loop; [`docs/plan.md`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/docs/plan.md), “Named entries,” “Themes,” and configuration.
* **[C6]** bob-cli, [`capture_complete/tests/pomodoros.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture_complete/tests/pomodoros.rs), `pomodoro_name_completion_treats_plus_names_as_named_not_nameable`.
* **[C7]** bob-cli, [`docs/pomodoro-homes.md`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/docs/pomodoro-homes.md), R4 and R7–R10, review semantics, home colors, additive JSON, and current-tree attribution.
* **[C8]** bob-cli, [`docs/vault-git-sync.md`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/docs/vault-git-sync.md), conflict handling and narrow JSON/JSONL allowlists.
* **[C9]** bob-cli, [`capture/commit.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture/commit.rs), preimage guards, staging, replacement, and rollback.
* **[C10]** bob-cli, [`capture/pomodoro_insert.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture/pomodoro_insert.rs) and [`capture/pomodoro_start.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/capture/pomodoro_start.rs), selector resolution and name canonicalization for creation.
* **[C11]** bob-cli, [`stats/index.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/stats/index.rs), `canonical_daily_date`.
* **[C12]** bob-cli, [`config/mod.rs`](https://github.com/bobs-org/bob-cli/blob/30f10f154afb119a51a5ebf27264538342973c88/src/native/config/mod.rs), XDG/home/override config path resolution.
* **[P1]** bob-plugins, [`075-pomodoro-link-targets.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/block-id-prompt/src/075-pomodoro-link-targets.js) and [`085-pomodoro-link-picker-modal.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/block-id-prompt/src/085-pomodoro-link-picker-modal.js).
* **[P2]** bob-plugins, [`200-filtered-picker-modals.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/bob-navigation-hotkeys/src/200-filtered-picker-modals.js) and [`150-pomodoro-capture.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/bob-navigation-hotkeys/src/150-pomodoro-capture.js), bullet move, entry move/merge, and local rename.
* **[P3]** bob-plugins, [`273-plugin-pomodoro-home-chips.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/bob-ledger-tools/src/273-plugin-pomodoro-home-chips.js) and [`274-plugin-pomodoro-home-chips-reading.js`](https://github.com/bobs-org/bob-plugins/blob/e6b2ec2dba4c4a6b865faccbc2e3cad59fef4f10/plugins/bob-ledger-tools/src/274-plugin-pomodoro-home-chips-reading.js).
* **[M1]** bob-mac-capture, [`CapturePanelModel.swift`](https://github.com/bobs-org/bob-mac-capture/blob/22598dc09f6b4b937259e716eab29a8c263e0ca7/Sources/BobMacCapture/CapturePanelModel.swift), completion acceptance/name prompt; [`CompletionRowContent.swift`](https://github.com/bobs-org/bob-mac-capture/blob/22598dc09f6b4b937259e716eab29a8c263e0ca7/Sources/CaptureCore/CompletionRowContent.swift), existing row semantics; [`CaptureModels.swift`](https://github.com/bobs-org/bob-mac-capture/blob/22598dc09f6b4b937259e716eab29a8c263e0ca7/Sources/CaptureCore/CaptureModels.swift), additive decoding.
* **[M2]** bob-mac-capture, [`CaptureAgendaRefreshFilter.swift`](https://github.com/bobs-org/bob-mac-capture/blob/22598dc09f6b4b937259e716eab29a8c263e0ca7/Sources/CaptureCore/CaptureAgendaRefreshFilter.swift) and [`CaptureAgendaStore.swift`](https://github.com/bobs-org/bob-mac-capture/blob/22598dc09f6b4b937259e716eab29a8c263e0ca7/Sources/BobMacCapture/CaptureAgendaStore.swift).

External documentation was checked on 2026-10-24 and is linked beside the claims it supports. I did not access private daily-note contents, benchmark the real history size, evaluate colors in the running apps, compile changes, or inspect peer research. Exact literal spelling, palette values, cache thresholds, and editor-write coordination remain implementation decisions to validate. The core behavioral recommendation does not depend on an assumed vault size or an invented performance measurement.

## Recommended solution

**Build a shared, name-based Pomodoro vocabulary over the existing ledger, with today-first completion, reversible hiding, restrained deterministic color, and a dedicated manager for global rename.** Keep full names distinct from sessions and budget components; add lossless exact selection before historical suggestions; store only explicit preferences in synced metadata; and keep bob authoritative across Mac and Obsidian.

Ship reuse, hide/restore, and color as the first coherent improvement. Add global rename with exact scope, an occurrence preview, explicit collision/compound handling, checked recovery, and undo. Preserve the simple act of typing a new name. That gives this feature its value without making every Pomodoro a new object to administer.

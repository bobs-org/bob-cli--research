# Double-slash note navigation in Bob Mac Capture

Independent research by **cdx** · 2026-11-15

## Recommendation and critique

**Build this as a Notes scope of the existing Go To picker: `/` finds tasks; `//` finds notes.** Keep the current task workflow intact, reuse the same panel and keyboard conventions, and make the scope unmistakable with a `Go To · Notes` heading. The feature should open an existing note in Obsidian, without creating a task, creating a note, inserting a link, or changing review state.

This is a good idea for Bryan's workflow. Capture already supplies a global entry point and task navigation; reaching a notebook, reference, journal, or dashboard through that same entry point removes an application switch. The extra slash is a small extension of an established gesture. Its main weaknesses are discoverability, the difference between finding a file and searching its contents, and hidden exclusions that make a supposedly comprehensive search feel unreliable. Solve those with an explicit scope label, a one-line hint in empty task search, and a conservative, documented eligibility policy.

I would **not** start with mixed task-and-note results, a new global hotkey, semantic retrieval, or an Obsidian-plugin search service. Those add ambiguity or operational cost without improving the core action: “I know roughly which note I want; open it.” Obsidian already has a name-and-alias Quick switcher with fuzzy matching. Its existence supports the interaction model but also sets a quality bar: Bob's value is access from Capture and consistency with its other pickers, not inventing another search language. [Obsidian Quick switcher](https://obsidian.md/help/plugins/quick-switcher)

The largest implementation risk is concrete: **`//` is currently ordinary capture prose.** A cosmetic Swift-only change could turn a failed search, an unsupported backend, or an accidental submit into an inbox task. Reserve the new navigation form in Bob itself before enabling it in the app.

## What I inspected and what remains unmeasured

I independently inspected these checkout revisions, existing tests, audited project memory, and official external documentation. I did not read or request any other swarm researcher's report or findings.

- **bob-cli:** `476c54407ebe2eb04e9ccc693fc74b610a4124d8`.
- **bob-mac-capture:** `9bf9050ad01e89e8c299233d930465947c4a4769`.
- Audited memory: artifact handling, CLI rules, the thin-client decision, settled similar-task behavior, relevant note-type definitions, and the daily release-train decision.
- Small read-only CLI experiments against an isolated synthetic vault using installed `bob 0.5.0`. The installed executable was not independently established to equal either source revision; the source and existing tests independently corroborate the parser findings below.

I did **not** inspect Bryan's live vault, measure Mac latency, run the Mac UI, or compile an implementation. Coverage counts, ranking weights, visual dimensions, and latency budgets proposed below are design recommendations, not measured outcomes. No production code was changed.

### Findings that affect the design

| Finding | Consequence |
| --- | --- |
| `task_goto_query_token` claims only a whole-draft, single-line, single-token form with exactly one `/`. Tests explicitly preserve `//`, `/Users/x`, `/r/rust`, and `/a b` as prose. | Add a separate `note_goto` claim before task navigation; do not broaden the existing single-slash rule accidentally. Reserving `//` changes existing capture semantics. |
| Open-task Go To uses `capture_link_tasks::discover`: routable inbox/area/nonterminal-project tasks. Command-X switches to closed tasks from a broader vault catalog. | The existing search is not literally every task at once. Preserve it; do not piggyback note eligibility on task or route eligibility. |
| `capture_links::NoteIndex` already walks nested Markdown, extracts aliases, and excludes hidden directories plus Bob's maintenance directories. | Reuse discovery and metadata primitives where appropriate. A separate handwritten Swift vault scanner would violate the thin-client architecture. |
| Wikilink note completion truncates its ranked output to 20 rows and reads headings and blocks as well as metadata. | It is useful source code, not a suitable unmodified catalog API. Fetching its empty-query top 20 and then filtering locally would silently lose most notes. |
| Mac task pickers fetch candidates and build an in-memory fuzzy index. `FuzzyQuery` already accepts a full string sigil such as `~~`; `FuzzyMatcher` supports boundary-aware subsequences. | A `//` note index can fit the existing presentation design. Strip the full two-character prefix, not one slash. |
| The backslash opener has a one-shot `backslashLiteralArmed` state and separate handling while a picker is open. | Preserve event provenance. A second backslash must not pass through a generic slash-alias conversion. |
| Go To already treats opening as navigation, keeps the panel on dispatch failure, and discards navigation drafts rather than stashing them. | Extend these semantics to note navigation; do not route acceptance through capture submission. |
| Scope requests already carry a session ID and generation, distinguishing requested scope from displayed candidates. | Extend that protection to task-to-note transitions and late responses. |

Source anchors: [Go To predicate](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/src/native/capture_language/tokens.rs#L465), [prose-regression tests](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/tests/cli/capture/task_goto.rs#L324), [Go To candidates](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/src/native/capture_complete/candidates.rs#L1638), [wikilink note index](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/src/native/capture_links.rs#L210), [local task index](https://github.com/bobs-org/bob-mac-capture/blob/9bf9050ad01e89e8c299233d930465947c4a4769/Sources/CaptureCore/TaskLinkPickerPresentation.swift#L11), [scope state](https://github.com/bobs-org/bob-mac-capture/blob/9bf9050ad01e89e8c299233d930465947c4a4769/Sources/CaptureCore/CaptureTaskGotoScopeState.swift).

The isolated parser experiment returned:

| Draft | Current parse mode | Current `needs` |
| --- | --- | --- |
| `/` | `incomplete` | `task_goto` |
| `//` | `task` | none |
| `//meeting notes` | `task` | none |
| `//ref/papers` | `task` | none |
| `/Users/x` | `task` | none |
| `Buy //notes` | `task` | none |
| one literal backslash | `task` | none |

A separate synthetic `[[` completion included `plain.md`, `done/old.md`, `ref/papers/paper.md`, `2026/20261115.md`, `dash.md`, and `deep/nested/visible.md`; it omitted files placed inside `.bob`, `.hidden`, `_templates`, `_generated`, and `_conflicts`. These are observed fixture results, not a census of the actual vault.

## Explicit requirement adjustments

1. **“All note files” means existing Markdown notes (`.md`, case-insensitive) in v1.** It does not mean every Obsidian-supported file. PDFs, images, audio, `.canvas`, and `.base` remain outside this scope. Obsidian supports those formats, but a broader “Files” launcher should be a deliberate later expansion, with suitable icons and actions. [Accepted file formats](https://help.obsidian.md/Files+and+folders/Accepted+file+formats)
2. **Search names, aliases, and paths, not body text.** Include a usable frontmatter title as another name. The placeholder says exactly that. Full-text search would require another ranking/indexing contract and a preview of content matches; it should not arrive disguised as filename lookup.
3. **Allow spaces and folder separators after `//`.** `//meeting notes` and `//ref/papers/attention` must work. Copying the existing task grammar's single-token restriction would make this feature unnecessarily awkward.
4. **Preserve ordinary historical and generated notes.** Closed projects, daily/period notes, archives, references, mail notes, dashboards, and empty notes remain findable. “Generated” is not a sufficient reason to exclude a note; Bob creates many valuable notes itself.
5. **No create-on-miss.** Empty results leave Return inert, with a helpful message. Obsidian's Quick switcher can create notes on Return; copying that behavior into a capture app would make a navigation typo dangerous and ambiguous. This is a deliberate difference from Obsidian.
6. **Reserve leading `//` explicitly.** It ceases to be ordinary prose in the supported single-line navigation form. This affects literal `//` comments, network-style paths, and protocol-relative URLs at the beginning of a draft. Document the collision; do not silently expand the reservation to internal slashes, existing absolute paths, or mixed capture batches.
7. **An actual second `/` after the existing `\` opener should work.** The physical sequence backslash then forward slash (`\/`) enters note search; backslash then backslash (`\\`) still produces one literal backslash. This interprets the user's “actual `/`” requirement as the second keystroke, while retaining the first-key alias.

## The interaction contract

Use one Go To experience with distinct Task and Note scopes. Show a small, clickable scope control or existing-style capsule labelled **Tasks** / **Notes**, so the feature can be discovered and is accessible without remembering punctuation. In an empty Tasks picker, teach **`/ Search notes`**. In Notes, show **`Go To · Notes`** and **`Search names, aliases, and paths…`**. This follows Apple's guidance to expose scope and keep the result list focused; the specific layout below is my design recommendation. [Apple search-field guidance](https://developer.apple.com/design/human-interface-guidelines/search-fields?changes=l_8)

### Entry, escape, and typing

In the table, backticks show literal characters, not a programming-language escape sequence.

| Starting state and input | Expected result |
| --- | --- |
| Empty draft, `/` | Existing task Go To. |
| Empty draft, `\` | Existing alias inserts `/`, opens task Go To, arms the one-shot literal escape. |
| Empty task Go To after either opener, actual `/` | Change to Notes, canonical draft `//`, empty query. Cancel task fetches and invalidate their results. |
| Immediately after the backslash opener, second `\` | One literal `\` in the editor; close navigation; invalidate pending responses. |
| Task Go To opened by `/`, then `\` | Preserve current behavior: consume it on the bare trigger. Do not introduce a new literal escape or Notes shortcut here. |
| Task Go To with a nonempty filter, `/` | Ordinary filter character; do not unexpectedly change scope. Use the visible Notes scope control to switch with the query retained. |
| Notes query, `/` | Ordinary path separator. A third slash is query text, not another mode. |
| Notes query, `\` | Ordinary query character. It is not a scope gesture and does not activate the old one-shot escape. |
| Paste `//meeting notes` into an empty editor | Recognize the same note-navigation intent as typing it. |
| Paste `\\` | Literal pasted text; it is not two physical backslash gestures. |
| Existing prose `Read //notes`, `/Users/x`, URL `https://…`, wikilink, or code span | Keep existing parsing and completion behavior. |
| IME marked text or a repeating key event | Do not trigger a second-sigil transition. Handle committed characters and explicit key presses only. |

Match the typed slash character, not a US-keyboard keycode. Some layouts require modifiers to produce `/`; Command or Control shortcuts still retain their existing meanings. Process scope switching ahead of generic slash/hash aliases and before filter-field insertion. Implement it both while initial completion is pending and after the picker has focus. A fast `//` must not depend on the first asynchronous reply arriving.

No double-tap timer is necessary. The second slash is a scope command in an empty task query, even after a pause. Backslash retains its current immediate-next-key, one-shot behavior; a delayed asynchronous picker reply must neither re-arm it nor resurrect a dismissed picker.

### Navigation keys and state transitions

- Return, Tab, row click, Command-Return, and Control-Return open the selected note, matching existing Go To. Shift-Return and Option-Return remain consumed. Empty or disabled selections never submit capture.
- Arrow keys and the existing Control-N/P navigation move selection. Preserve native text editing and selection in the query field.
- Backspace deletes query characters normally. At an empty Notes filter, it removes one slash and returns to empty Tasks. A second Backspace removes `/` and returns to the idle agenda. Returning this way starts the normal open-task scope.
- Escape clears a nonempty filter, then collapses to the existing reopen chip, preserving scope. The Notes chip explicitly says Notes. Control-C discards the navigation draft; it never enters the canceled-capture stash.
- Command-X continues to mean completed/open tasks only in Tasks. In Notes it is native Cut. Do not overload it to mean “archives” or “include excluded files.”
- The clickable Tasks/Notes switch retains query text. If the Tasks session had a completed-task scope, keep that inside the Tasks session state; Notes has no completed flag. Ending navigation clears both sessions.
- A scope change clears selection and disables acceptance until rows from the requested scope are installed. Within a scope, a background refresh preserves selection by exact note identity if the row remains present. Ordinary query editing can retain the current picker's established selection behavior.

The backend recognizes one whole-draft single-line `//query`, beginning at the first non-whitespace character. Multiword text after the prefix belongs to the query; it is not parsed for capture sigils. A multiline or mixed-item draft retains existing capture rules. Do not broaden this research into a change to single-slash task semantics. For the rare literal leading `//` prose case, inline code formatting is an existing way to make intent explicit; verify that interaction when implementing. A separate “capture literally” command is unnecessary for v1.

## Eligibility: what to exclude, and what to keep

The central rule is **exclude implementation debris, not classes of human-useful information**. Search eligibility must not depend on whether a note is a valid capture destination, contains tasks, has a known type, belongs to an active project, or has valid frontmatter.

### Hard exclusions for v1

| Class | Proposed policy and reason |
| --- | --- |
| Hidden path components | Skip dot-directories and dotfiles, including `.git`, `.obsidian`, `.bob`, and `.trash`. `.bob/ref-sources/.../source.md` is preserved render input, not a second reference note. |
| Bob maintenance directories | Skip exact directory components `_templates`, `_generated`, and `_conflicts`, consistent with Bob's existing shared exclusions. This does not mean “all names beginning with `_`.” |
| Additional explicitly configured template roots | Exclude only roots identified by a supported template configuration or a future explicit Bob exclusion setting. Do not guess that a generic folder called `templates` is always maintenance, or exclude `templates.md`. `_templates` already covers the documented Bob default. |
| Non-note file types | Include only regular `.md` files, matching extension case-insensitively. Do not return folders, PDFs, binary attachments, snapshots, lockfiles, or `.md.bak` files. |
| Symlinks | Do not descend symlinked directories or offer symlinked files in v1. This matches existing walk behavior, avoids cycles and vault escapes, and should be documented as a limitation. A future contained-symlink policy needs explicit tests. |
| Conflict/recovery duplicates | `_conflicts` is excluded unconditionally. Outside it, exclude only positively recognized producer-specific conflict-copy forms if their identification is tested; do not hide files because their name contains “conflict,” “copy,” or “backup.” Unknown cases remain searchable. |
| Explicit user exclusions, if added | Make these an additive Bob-owned policy with documented path semantics and explainable exclusion reasons. They must not be inferred from `.gitignore`, task `#hide`, or task lifecycle. |

The repository's current shared exclusion list is `.bob`, `.git`, `.obsidian`, `_conflicts`, `_generated`, and `_templates`; the wikilink walker additionally ignores dot-directories. Dotfile exclusion is an intentional extension for this picker. [Shared directory policy](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/src/native.rs#L3)

Do not blanket-exclude `node_modules`, `lib`, `file`, `img`, `scripts`, `docs`, or arbitrary directories based only on a generic intuition about their names. Most binary attachments are already eliminated by extension, and a `.md` in such a directory might be intentional documentation. If a real-vault inventory reveals managed Markdown attachments or vendored documentation flooding results, add the exact known maintenance root to the policy. I did not inspect that inventory and therefore will not invent it.

### Included notes that are easy to exclude incorrectly

| Class | Why it belongs |
| --- | --- |
| Areas, projects, inboxes, notebooks, albums, records | These are ordinary navigation destinations. Notebook notes in particular can intentionally contain no tasks. |
| Closed/canceled projects and `done/` archives | Historical retrieval is a primary reason to search broadly. Mark archives quietly rather than hiding them or placing them behind another toggle. |
| Daily, weekly, quarterly, yearly, and all-time notes | Dates and periods are useful names. Support path/date queries; do not bury exact date matches beneath unrelated current notes. |
| `ref/` notes | Generated reference notes contain annotations and authored material; they are not equivalent to the hidden raw-source store. Opening the note must not silently open its PDF instead. |
| `mail/` notes, bank month notes, meeting/private event notes | They are useful Markdown documents even when machine-authored or governed by specialized workflows. |
| Dashboards, catalog/root sentinel notes, type-description notes | They are frequently useful landing pages even if excluded from capture catalogs. |
| Empty, untyped, unfamiliar, or malformed-frontmatter Markdown | File existence is enough. Fall back to the filename if metadata cannot be read. A type validation failure must not erase a note from navigation. |
| Notes with `#hide` tasks | Task visibility is not note visibility. Reading one task tag as a file exclusion would be surprising. |

Bob's documented vault includes `dash.md`, period notes, `done/`, `ref/`, mail, records, and a hidden source store. This is why a task-route allowlist or a “generated notes” ban would be particularly inappropriate here. [Vault-format reference](https://github.com/bobs-org/bob-cli/blob/476c54407ebe2eb04e9ccc693fc74b610a4124d8/docs/reference/vault-format.md#L251)

### Obsidian's Excluded files setting

Do not assume its name means hard exclusion everywhere. Official documentation says those patterns hide results in Search but merely deprioritize them in Quick switcher and link suggestions. [Obsidian settings](https://obsidian.md/help/settings)

**Recommended v1 boundary:** use Bob's explicit maintenance exclusions, and do not promise automatic mirroring of Obsidian's exclusion settings. A later integration should import them as a clearly documented de-prioritization policy, with verified matching semantics, rather than interpreting arbitrary patterns as Rust regular expressions or silently removing notes. If Bryan needs custom hard exclusions immediately, a small explicit Bob configuration is preferable to an undocumented approximation. This is a deliberate limitation, not evidence that the native setting is unimportant.

## Search quality and visual design

### Ranking and identity

Build one row per vault-relative path, including the extension; qualify it by vault identity in caches. Never key rows by title, basename, alias, or an empty completion replacement. Two files named `meeting.md` remain two candidates. Normalize for matching, never for filesystem identity.

Search these fields:

1. Filename stem and a valid frontmatter `title` as primary names.
2. Obsidian `aliases`, plus Bob's existing `project_name_aliases` when present. They are distinct properties; do not replace one with the other. Obsidian's standard aliases are YAML lists. Reuse Bob's existing tolerant reader for legacy scalar aliases. [Obsidian aliases](https://obsidian.md/help/aliases)
3. Vault-relative path, both with and without `.md`.

Use deterministic tiers: exact path/name/alias, name prefix, word-boundary/acronym match, then broader substring/subsequence matches. A full explicit path is strongest. A path term can combine with a title term (`ref attention`). Every query term must match somewhere in the candidate. Preserve matching across spaces, `_`, `-`, Unicode, and diacritics without corrupting display offsets. When an alias explains the match, display `Matched alias: …` unobtrusively.

Start with filename/title/alias relevance rather than hand-tuning numerical weights. Shared fixtures should pin desirable relative order. Within equal match quality, a modest personal recency tie-break can help; it must never outrank an exact intended title. Avoid modification time as a proxy for personal interest: sync and generators can rewrite many files.

On an empty query, show up to five **Recent in Capture** notes if such history exists, followed by **All notes** in stable alphabetical order, without duplicating rows. On first use, simply show All notes. Record only successful dispatches, locally per vault, and provide a clear-history action if this recency feature ships. Do not claim it reflects Obsidian-wide recents or read its private workspace JSON. Recency can be deferred without blocking the feature.

The current fuzzy implementation searches only the first 256 characters of each field. Reusing it blindly can make a long path's basename unsearchable. Index basename and path components independently and retain a full exact-path comparison; test long nested names explicitly. [Fuzzy matcher](https://github.com/bobs-org/bob-mac-capture/blob/9bf9050ad01e89e8c299233d930465947c4a4769/Sources/CaptureCore/FuzzyMatcher.swift)

### A restrained result card

Conceptual layout, not a rendered or measured mockup:

```text
Go To                         Tasks   [Notes]     //
Search names, aliases, and paths…

  Note    Capture design
          notebooks/capture_design.md

> Ref     Attention Is All You Need
          ref/papers/attention.md
          Matched alias: transformer paper

  Note    Meeting notes
          projects/launch/meeting.md

12 matches                     ↵ Open in Obsidian
```

Reuse the existing panel's materials, typography, corner radius, focus behavior, and selected-row treatment. The primary line is a readable title, with a complete relative path on a secondary line. Use a filename fallback rather than aggressively prettifying underscores into guessed titles. Keep path text available in accessibility output and a tooltip/detail line if visually truncated; duplicate titles must be distinguishable without opening them.

Use one restrained note/type glyph, not a task checkbox, Pomodoro badge, completion capsule, or capture-route `@` prefix. Type is optional context; unknown kinds get a normal document icon. Highlight only matched text. Do not add rich content previews, syntax-colored snippets, multiple badges, or animated scope changes to this first version.

Target roughly 6–8 visible two-line rows within existing panel geometry, scroll the remainder, and retain a stable height through short queries. Show the count of actual matches, not a falsely complete count after truncation. Distinguish **Loading notes…**, **No notes match “…”**, **No eligible notes**, and **Couldn't load notes**. A partial scan gets one quiet warning with accessible details; it must not look like a complete empty vault.

VoiceOver should announce scope changes, title/path, result count after results settle, and errors. Use sufficient text contrast, native focus cues, and reduced-motion behavior. Treat these as acceptance checks, not a reason to add visible UI complexity.

## Architecture and reliability

### Bob owns discovery and meaning; Swift owns interaction

Honor the accepted thin-client rule: Bob supplies capture grammar, eligible notes, metadata, and concrete destinations; Swift orchestrates subprocesses, ranks the supplied snapshot, renders rows, and dispatches the URL. It never crawls the vault or infers a note path from its title.

Recommended seams:

- Add `note_goto` to the shared grammar/editor/completion context, with a whole-draft `//` predicate used by parse, completion, and capture refusal. Claim it before task Go To and before interpreting capture markers.
- `capture-parse` returns `mode: incomplete`, `needs: [note_goto]`, and an `interactive_placeholder` covering the navigation draft. The frontend skips capture dry-run for this need.
- `capture-complete` returns a note-navigation candidate shape. Keep existing schema-1 consumers working with additive fields and a distinct context. Do not fabricate task refs, line numbers, statuses, or block IDs for a note.
- Extract/reuse lightweight note enumeration and metadata parsing from the existing wikilink index. Do not change all wikilink matching semantics as a side effect, and do not scan every heading and block when only names are required.
- Add a dedicated `NoteGotoPickerIndex` and source/destination type within the shared picker framework. Reuse common presentation, fuzzy matching, focus repair, and request-generation patterns. Avoid stretching the already task-oriented row model by populating fictitious task fields.

Illustrative candidate payload; exact naming should follow the existing JSON style:

```json
{
  "replacement": "",
  "note_path": "ref/papers/attention.md",
  "target": "/Users/example/Bob/ref/papers/attention.md",
  "name": "attention",
  "title": "Attention Is All You Need",
  "aliases": ["transformer paper"],
  "note_kind": "reference"
}
```

Acceptance uses the destination, never `replacement`. Its empty value exists only if required by the existing decoder shape. Missing or invalid destinations produce a disabled row or update hint, never a fallback capture.

### Complete snapshots, bounded work, explicit invalidation

For v1, fetch the complete eligible metadata catalog on entering Notes and filter in memory, following existing picker behavior. This means zero vault scans per typed filter character. Do not fetch `[[` completion and locally filter its 20 results. Do not implement independent selection/exclusion rules in Swift.

Keep an app-memory last-good snapshot, keyed by vault and Bob executable identity. Revalidate on a new Notes session and relevant vault events. Use the existing FSEvents plumbing but a note-search relevance policy: visible Markdown create/update/delete, folder moves, configuration changes affecting eligibility, root changes, and dropped events. A folder rename can change thousands of paths without a per-file event. Sleep/wake or a failed watcher should trigger revalidation when shown again. Watching paths is orchestration, not permission for Swift to read note contents.

Each request carries session ID, scope, draft generation, vault identity, and backend identity. A response applies only to the matching request. Never display selectable stale task rows under a Notes header. On refresh, preserve a still-existing selected path, but remove vanished rows. A complete failure keeps the last-good list visibly stale or shows an error; a partially unreadable subtree returns candidates with bounded warnings and an explicit incomplete indicator.

Metadata reads should be bounded and tolerant: filename discovery must survive malformed YAML, invalid optional fields, or a very large note. A short frontmatter read is sufficient for the recommended fields. Avoid whole-body indexing and arbitrary corpus limits that silently omit later paths. If a payload exceeds an operational limit, surface a partial/error state and implement server-side querying or pagination before calling coverage complete.

### Opening notes, stale paths, and success claims

Use the existing `ObsidianOpenURL.url(forAbsolutePath:)` route with `obsidian://open?path=…`. Opening the exact absolute path avoids duplicate-basename ambiguity and needs no new Obsidian plugin handler. Construct it with URL components and test reserved characters, Unicode, `%`, `+`, `#`, and `&`. The standard URI accepts an absolute path and requires correct encoding. [Obsidian URI](https://help.obsidian.md/Extending+Obsidian/Obsidian+URI)

Revalidate the selected exact path through Bob before dispatch. The simplest initial implementation can request a fresh unfiltered `note_goto` snapshot and look for the same identity; it requires no new public command. This adds one scan on acceptance, so measure it. If necessary, add a targeted read-only validation operation instead of making Swift stat/canonicalize arbitrary vault files. Do not use a fuzzy query for this check: it could select another note after a rename.

If the path disappeared, keep the query, refresh results, and say **That note moved or was deleted**. Do not open the best replacement or create a note. Validate containment and eligibility in Bob, skip symlinks, and serialize one dispatch at a time so a double Return does not open twice.

After a successful OS dispatch, dismiss and discard the navigation draft. On dispatch failure, retain query and selection with **Couldn't open Obsidian** and a retry action. Apple's callback reports whether the application opened the URL; it is not an acknowledgment that a particular Obsidian tab rendered the note. A deletion between validation and URI handling remains a narrow race. Stronger end-to-end guarantees would need a plugin acknowledgment and are unnecessary for v1. [NSWorkspace opening contract](https://developer.apple.com/documentation/appkit/nsworkspace/open%28_%3Aconfiguration%3Acompletionhandler%3A%29)

### Older Bob, unknown contexts, and accidental capture

Probe note-navigation support positively and cache the result by executable identity. Require the expected `note_goto` response, not merely exit zero or schema version 1. The experiment above shows old Bob can successfully parse `//` as a task.

A typed scope gesture or whole-draft `//` paste sets navigation intent at the input boundary. While its support check is pending, failed, or unsupported, no submit key may send that intent to `bob capture`. Show **Update bob to search notes** and retain/back out of navigation safely. This is a narrow UI-intent guard, analogous to existing opener handling; it must not grow into Swift's own implementation of capture grammar. Bob remains authoritative about candidate eligibility and all parse semantics.

New Bob plus an old app must also fail safely: the CLI refuses capture of the reserved navigation form even if the old app cannot present the picker. Keep single-slash task navigation intact. Test both version directions, decode errors, unknown contexts, process failure, and replacing the executable while a request is pending.

## Alternatives and tradeoffs

| Alternative | Assessment |
| --- | --- |
| Only add a dedicated global note-search hotkey | Faster for a frequent expert action, but adds configuration and conflict surface. The existing Capture entry point is enough for v1. |
| Put task and note rows together under `/` | Makes repeated search gestures ambiguous and disturbs current task ranking. Separate scopes have clear nouns and actions. |
| Delegate directly to Obsidian's Quick switcher | Lowest custom UI cost, but loses the Capture experience and would need a reliable way to invoke/populate that UI. Standard documented URI actions do not provide a Quick-switcher result API. |
| Search note bodies or use embeddings | Useful for a different question, “where did I write about this?” Adds indexing, snippets, relevance tuning, and privacy/history decisions. Defer. |
| Reuse `capture-targets` unchanged | Fast but incorrect coverage: writable routes are not the set of navigable files. |
| Reuse current wikilink candidates unchanged | Better coverage, but insertion semantics, result cap, and body-indexing work do not fit a file launcher. Reuse the underlying pieces. |
| Have Swift scan directly | Avoids a subprocess but duplicates eligibility and metadata rules and violates the accepted architecture. |
| Exclude archives, journals, references, or dashboards for “cleanliness” | Produces deceptively incomplete search. Prefer clear paths and relevance ordering. |
| Introduce a resident search daemon now | Too much lifecycle machinery without a measured latency problem. Keep it as an escalation option. |

## Verification and delivery criteria

These checks define a finished implementation; this research did not run them against new code.

**Grammar and non-mutation:** cover `//`, multiword/path/Unicode queries, prefix precedence, cursor offsets before/inside/after the trigger, whitespace, pasted input, absolute paths, code spans, URLs, and batches. `capture` and dry-run refuse supported note-navigation forms before any vault mutation. Snapshot a fixture vault around refusal and navigation-related CLI calls. Existing single-slash tests continue to pass except the explicitly changed `//` expectation.

**Input behavior:** test `/` then `/`, `\` then `/`, `\` then `\`, slash then backslash, paste versus key events, IME, non-US keyboards, repeated keys, rapid typing before the first subprocess returns, scope change during loading, Backspace transitions, Escape/chip reopen, Undo, Control-C, and Command-X in both scopes. Slow and failed responses must not resurrect a literal-backslash or canceled session.

**Coverage:** include nested notes, duplicate stems/titles/aliases, uppercase `.MD`, missing/invalid metadata, empty notes, all documented note families, `done/`, old periods, dotfiles, maintenance folders, similarly named legitimate folders, non-Markdown attachments, symlinks, unreadable subtrees, and more than 20 candidates. Notes after the twentieth alphabetical entry must remain searchable. Verify an exact date/archive/path match outranks a weaker active-note match.

**Opening and lifecycle:** test missing destinations, note rename/delete while open, vault changes, stale responses after executable replacement, URL escaping, double acceptance, absent Obsidian, dispatch failure, watcher overflow, directory moves, and wake/show refresh. Confirm note opening never executes task operations or inserts an empty completion replacement.

**Performance:** benchmark on the actual Mac with the actual eligible-vault count and synthetic 1k/10k/50k catalogs. Proposed targets are warm local filtering p95 under 16 ms, warm entry p95 under 100 ms, and cold scan plus render p95 under 300 ms on Bryan's vault. Show a loading state rather than freezing if cold startup is slower. Also measure acceptance validation and memory/JSON size. These numbers are acceptance goals, not source-backed timing claims. If measured catalog cost is too high, prefer a Bob-owned metadata cache or query protocol before adding a daemon.

**Release coordination:** backend grammar and JSON first, app presentation second. Add shared contract fixtures, document the new reserved prefix and exclusions, and follow docs checks. The established rule requires compiling changed Swift: portable checks, macOS build/typecheck where available, and the exact-SHA macOS CI gate. Do not treat Linux tests as proof of AppKit behavior. Since previously capturable leading `//` changes meaning, mark the CLI behavior break with `!` per the daily-train policy; do not hand-edit Cargo version or CHANGELOG. No new release process is needed.

## Recommended solution

Ship a **read-only Markdown note launcher inside Go To**, entered by `//` or the existing `\` opener followed by an actual `/`. Preserve `\\` as one literal backslash. Give Notes an explicit label, multiword name/alias/path search, quiet title-and-path rows, and familiar navigation keys. Keep archives, references, journals, dashboards, records, and ordinary generated notes included; exclude hidden infrastructure and Bob's explicit maintenance directories.

Implement the authoritative `note_goto` claim and complete metadata catalog in Bob, then present it through the existing Mac picker with local filtering, stale-response protection, and exact-path opening. Gate unsupported backends so navigation can never become capture. Begin without body search, new note creation, a daemon, or speculative exclusion lists. This delivers the requested convenience while keeping the behavior understandable, comprehensive within its stated scope, and visually consistent with the app Bryan already uses.

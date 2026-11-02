# `bob gcal sync`: Google Calendar descriptions as Event Task sub-bullets

*Researcher: cld · 2026-11-02 · bob-cli `master` @ `311b1514`*

## TL;DR

**Yes, build it, but not as a plain text dump.** Bryan already uses event descriptions for two
things: Bob's directive lines (`@love`, `#offclock`, `-30`) and short human reminders
("And retainers!"). Showing the reminders under the meeting in the daily note is valuable.
The naive version would still fail on day one. Below are the five changes I would make to
the request, and the recommended design.

1. **Strip invite boilerplate.** The one external work invite in Bryan's recent calendar has
   a description that is 100% Microsoft Teams boilerplate: separator rules, join URL,
   meeting ID, passcode, and help links. A literal conversion turns that into about nine
   junk bullets, and Bob already shows the join link as `📹`. Drop conferencing blocks.
2. **Sanitize hard: description text is data.** The vault has **inline DataviewJS enabled**
   (`enableInlineDataviewJs: true`, prefix `$=`). A meeting organizer's description that
   contains `` `$= …` `` would run JavaScript in Obsidian if Bob wrote it verbatim. The
   same goes for code fences, embeds (`![](…)` loads remote images), wikilinks (fake Task
   Mentions/backlinks), tags, inline fields, checkboxes, and even 🍅 (sync's own
   `row_untouched` treats any 🍅 in a row's block as "worked").
3. **The bullets follow Google until Bryan edits them.** Write-once would go stale whenever
   Bryan edits an event. He already treats the description as a remote control, and its
   directives update unedited rows. Track the bullet block by a journal hash, not by inline
   markers. If Bryan edits, extends, nests under, or deletes the block, it becomes his for
   good. This **partly supersedes** the "children are yours, never touched" clause of
   `decisions:bob-gcal-is-read-only-and-proposes-once` and needs its own decision record.
4. **Event Tasks only.** Context rows (all-day, Maybe, free) stay one line. A Maybe row
   that is upgraded to a task gains its bullets at upgrade.
5. **Cap the block.** Default 8 bullets. A final `*…N more lines in [Google Calendar](…)*`
   bullet links to the event.

**What the result looks like**, using a real event from today, 2026-11-02 (Bob writes tab
indentation in this vault):

```markdown
- [*] #task **0800-0815** Swings! [📅](… "Open in Google Calendar") #offclock [root:: love] [type:: MEET] ^swings
	- And retainers!
```

The Google description was `And retainers!\n\n@love #offclock`. The directive line still
drives `#offclock` and `[root:: love]`. The human line becomes the bullet.

---

## 1. What exists today

| Fact | Where |
| --- | --- |
| Descriptions are parsed **only** to derive directives (route, off-clock, buffer). The raw text is discarded and `GcalEvent` keeps no description field. | `src/native/gcal/model.rs` (`description_directives`, `normalize_description_html`) |
| A **directive line** is one whose every whitespace/comma token is `@route`, an off-clock alias, or `±N[m]`. Any other token makes the whole line ordinary text. | `model.rs::description_directives`, `docs/gcal.md` § Off-clock events |
| The HTML normalizer turns `br/p/div/li` into newlines, strips every other tag, and decodes entities. It also strips Outlook-style `text<https://…>` autolinks, because it reads them as tags. | `model.rs::replace_html_tags` |
| Directive parsing is a **cross-repo contract**: `tests/fixtures/event_buffer/vectors.json` is mirrored in bob-plugins (`bob-ledger-tools`). | `tests/fixtures/event_buffer/README.md` |
| Ownership table: Google owns time, title, badges, `#offclock`, and `[buffer::]` while they are unedited. **Child bullets (meeting notes): You, never touched.** | `docs/gcal.md` § Who owns each part of a row |
| Span ownership is a three-way merge: the current span's hash is compared with the journaled hash and with a fresh render. The journal `gcal.row` record carries `spans: {time,title,badges}`. | `plan.rs::apply_span_updates`, `journal.rs::RowRecord` |
| `remove_lifecycle_context` compares `spans.hashes() == journaled.spans` for **exact map equality**. A new key inside `spans` would break that comparison. | `plan.rs:1069`, `lifecycle.rs:289` |
| A time change re-slots the row **together with its child block**. New rows are inserted after the previous row's whole child block. | `plan.rs::reslot_block`, `plan.rs::insert_slot` |
| `row_untouched` returns false if **any line in the row's block contains `🍅`**. | `lifecycle.rs:322-341` |
| Context rows "with child bullets (Bryan's notes)" are never removed on decline. | `plan.rs::remove_lifecycle_context` |
| Capture picks child indentation with `dominant_indent_unit` (tab fallback). Bryan's daily notes are tab-indented (for example, 32 tab-indented lines against 2 space-indented ones on 2026-11-01). | `capture/sub_bullet.rs:676` |
| JSON never includes descriptions (a documented privacy promise). | `docs/gcal.md` § JSON output |
| Dataview has `enableDataviewJs: true`, `enableInlineDataviewJs: true`, `inlineJsQueryPrefix: "$="`. The Tasks global filter is `#task`. | `~/bob/.obsidian/plugins/{dataview,obsidian-tasks-plugin}/data.json` |
| An ALL-CAPS child bullet with nested notes is a **Task Drawer**, and drawer titles feed capture's catalog. Titles allow `A-Z0-9 &'(),./-` and no colon. | `capture_drawers.rs::is_title`, `glossary:task-drawer` |
| No HTML or Markdown crates are in `Cargo.toml`. `url` is present. | `Cargo.toml` |

## 2. What Bryan's descriptions actually look like

I sampled the primary calendar from 2026-10-01 to 2026-11-15 read-only: 17 events, 6 of them
with a description. I've paraphrased personal details.

| Shape | Count | Example | What literal bullets would do |
| --- | --- | --- | --- |
| Directive-only | 3 | `@love`, `@love\n#untracked\n-30`, `@love -30 #offclock` | Nothing remains, so no bullets. ✓ |
| Human line + directive line | 1 | `And retainers!\n\n@love #offclock` | One bullet, "And retainers!". ✓ This is the motivating case. |
| Human text only | 1 | A one-sentence note on a personal appointment | One bullet. ✓ |
| Third-party conferencing boilerplate only | 1 | Teams block: `____…` rule, "Microsoft Teams meeting", `Join: <url>`, Meeting ID, Passcode, `____`, `Need help?<url> \| System reference<url>`, "For organisers: …<url>", `____…` | **About 9 junk bullets with three huge URLs and a passcode.** ✗ |

So the feature pays off on Bryan's own events today, and without filtering it is actively ugly
on external invites. The design has to handle both.

## 3. Is this a good idea? (critique)

**For it**

- **Context where Bryan acts.** The daily note is the cockpit. "And retainers!" belongs next
  to "Swings!" at 08:00, not hidden in a Google popover. The sample shows Bryan already writes
  reminders into descriptions, so the habit exists.
- **Agendas and prep for work meetings** (interview loops, 1:1 docs) become visible and
  searchable in Obsidian.
- **A free bonus.** Each Event Task is linked from a MEET Pomodoro as `[[#^id]]`, and
  Obsidian's block-link hover preview of a list item should include its nested children. If
  so, hovering the meeting in the ledger shows its agenda.
- **It fits the existing mental model.** Google owns what it wrote until Bryan edits it,
  exactly like the title, time, badges, `#offclock`, and `[buffer::]`.

**Against it, or at least to handle carefully**

- **Noise.** Third-party invites are mostly vendor boilerplate (Teams, Zoom, Google's
  `-::~:~::-` invite block, Webex). Unfiltered, this makes the Events section worse.
- **Contract change.** The docs promise children are Bryan's and never touched. Bob writing
  children reopens that promise, so it needs a precise ownership rule and a decision record.
- **Security.** Accepted invites from outside parties put attacker-controlled Markdown into a
  vault with inline DataviewJS on. This is the strongest reason to never write description
  text verbatim. Mitigation: invites "awaiting a reply" are already omitted, so only accepted
  events render. Accepted invites are still untrusted.
- **Bloat and repetition.** Recurring series repeat the same description every occurrence,
  and long descriptions crowd the Events section. A cap and a link-out keep this bounded.
- **Bob-parser interactions.** Children can be mistaken for drawers, Task Mentions, inline
  fields, tags, checkboxes, or worked markers (🍅). Each needs an explicit guard.
- **Privacy.** Descriptions (phone numbers, addresses, passcodes) now land in the git-synced
  vault. That is acceptable for Bryan's private vault, and boilerplate filtering removes the
  worst offenders (passcodes, dial-ins). JSON output should keep excluding description text.

**Would I take a different approach?** Not fundamentally. Flat child bullets are the right
*shape*. I would change the *ownership* (live until edited, not write-once and not "yours"),
the *scope* (tasks only), and add *filtering, sanitizing, and a cap*. Alternatives I
considered and rejected are in §5.

## 4. Requirement adjustments (explicit call-outs)

| # | Adjustment | Why |
| --- | --- | --- |
| **A1** | **Description bullets are Google-owned until edited.** Sync rewrites the block in place while it still matches what Bob last wrote. Once Bryan edits a bullet, adds a nested note inside the block, or deletes it, the block is his for good: kept, reported once (`kept_description`), never re-added. All *other* children stay Bryan's, as today. | Consistent with every other Google-owned part of the row. Write-once would go stale whenever Bryan edits an event in Google, and he already edits descriptions to steer directives. |
| **A2** | **Event Tasks only.** Context rows (all-day, multi-day, Maybe, free) get no bullets. A Maybe→Yes upgrade adds them. | The request says "event tasks". It also keeps `remove_lifecycle_context`'s "a row with children is Bryan's" rule true. |
| **A3** | **Exclusion goes beyond directive lines:** conferencing boilerplate blocks, separator-only lines, blank lines, and a line that only repeats the `📹` join URL are dropped too. | Real Teams invite (§2). The `📹` badge already carries the join link. |
| **A4** | **At most N bullets (default 8).** Extra lines collapse into one `*…N more lines in [Google Calendar](…)*` bullet. Configurable. | Keeps the Events section scannable. The link preserves access. |
| **A5** | **Description text is inert data.** Bob never writes checkboxes, tags, inline fields, wikilinks/embeds, code spans or fences, inline queries, raw HTML, math, or block IDs from a description. | Inline DataviewJS is on. Bob's own parsers read children. |
| **A6** | **Existing rows backfill.** The next sync of a day adds bullets to that day's journaled Event Tasks that predate the feature. A crash-adopted row never gains bullets it might already have. | The feature is visible immediately with no duplicate risk. |
| **A7** | **JSON keeps the privacy promise.** `list`/`sync` JSON report a `description_lines` count, never text. | `docs/gcal.md` § JSON output. |
| **A8** | **The directive grammar does not change.** A text line that contains `#offclock` stays text: the bullet shows `\#offclock` and the row stays on-clock. | One predicate decides directive vs bullet, so a line is never both and never neither. The visible escaped token also shows why it did not apply. |

## 5. Design space and choices

### 5.1 Shape: how the bullets look

| Option | Look | Verdict |
| --- | --- | --- |
| **(a) Flat first children**, one bullet per line or paragraph, with lists kept to 2 levels | `\t- And retainers!` | ✅ **Recommended.** It is the cleanest form and what the user asked for. The `📅` badge already marks the origin. Obsidian shows a fold chevron on the row, so long blocks can be collapsed. |
| (b) Wrapper drawer (`- DETAILS` / `- AGENDA` with nested lines) | Two lines for a one-line reminder | ❌ Heavy for the common 1-line case. "DETAILS" would dominate the capture drawer catalog. Drawers are "part of one task's work", which capture *files into*, and that mixes Bryan's notes into a Google-owned block. |
| (c) A single joined child line (`- 📝 a · b · c`) | Compact | ❌ Loses list structure and reads badly for agendas. |
| (d) Quote or callout children (`- > …`) | Visually "quoted" | ❌ Multi-line quote continuation inside list items is fragile, and Bob's child parsers don't expect it. |
| (e) Mixed: flat when ≤3 lines, drawer when longer | | ❌ Two shapes for one concept hurt predictability and parsing. |
| (f) No vault write; show descriptions on hover in Ledger Tools or Mac capture | | ❌ Not searchable, not in the note, and needs a plugin round-trip to Google. A fine *extra* later, not a substitute. |

### 5.2 Ownership: how sync knows which children are Google's

| Option | Verdict |
| --- | --- |
| **Journal block hash + line count, located by window search** | ✅ **Recommended.** Invisible in the note and robust to Bob or Bryan inserting lines above or below (WORK LOG, CANCEL LOG, Bryan's notes). Same three-way idea as `apply_span_updates`. |
| Inline markers (`%%gcal%%` comment or `^gcal-desc` block ID on each bullet) | ❌ Visible in source and live-preview editing, travels with copy/paste, and you'd still need a hash to detect edits. |
| Positional ("the first k children") | ❌ Breaks as soon as a WORK LOG or CANCEL LOG is inserted as the first child. |
| Write-once (born with the row, never touched again) | ⚠️ Simplest, and safe. Stale when Google changes. A valid fallback phase (§6.9), not the end state. |

### 5.3 Parsing: one classifier for directives and bullets

Today `description_directives` normalizes HTML by stripping tags. The bullet renderer needs
*structure* (lists, links, emphasis). There are two ways to build it:

- **Two independent normalizers.** ❌ Their line splits could disagree, so a line might be
  read as a directive *and* rendered as a bullet, or as neither.
- **One structured parser feeding both.** ✅ Parse once into `DescriptionLine { depth, kind,
  inlines }`. A line is a directive iff its plain text passes today's `is_directive_token`
  test on every token. `description_directives` folds the directive lines, and the bullet
  renderer renders the rest. Gate: the shared `event_buffer/vectors.json` stays **byte-for-byte
  unchanged and green**. New behavior gets its own bob-cli-only vectors file, so the
  bob-plugins mirror is unaffected.

One known divergence: in a *plain-text* description, `text<https://x>` is an Outlook autolink,
not an HTML tag. The structured parser keeps it as a link. The legacy normalizer stripped it,
which could in theory turn `@love <https://x>` into a directive line. No existing vector
covers this. Pin the new (more correct) behavior with a new vector.

**HTML vs plain text detection.** Google returns HTML when the web editor formatted the
description, and plain text otherwise (mobile, API, Outlook/ICS). Treat the input as HTML
iff it contains a known tag: `</?(a|b|strong|i|em|u|br|p|div|span|ul|ol|li|font|h[1-6])\b`,
case-insensitive. Otherwise use the plain-text path.

**No new crate.** Google's editor emits a tiny tag set. A hand-written tokenizer, in the
style of the existing `replace_html_tags` and `decode_html_entities`, is deterministic, keeps
dependencies lean, and is easy to vector-test. `url` (already a dependency) unwraps
`https://www.google.com/url?q=<target>&sa=D&source=calendar&usg=…` redirects and extracts
hosts.

### 5.4 Filtering

The filters run in order on parsed lines:

1. **Directive lines.** Dropped by the shared predicate.
2. **Blank lines.** Dropped. Paragraph breaks become bullet boundaries.
3. **Separator-only lines.** A run of 3 or more `-_=*~` characters, or Google's
   `-::~:~::~…::-`. Dropped.
4. **Conferencing blocks.**
   - A block fenced by separator lines that mentions a vendor or join vocabulary (Microsoft
     Teams, Zoom, Google Meet, Webex, "Meeting ID", "Passcode", "Join by phone", "Dial-in",
     "Please do not edit this section") is dropped whole.
   - An unfenced vendor header ("Join Zoom Meeting", "Microsoft Teams meeting", "Join with
     Google Meet") drops from the header to the end of the description, which is where
     vendors append it.
   - This is driven by a fixture corpus: one real-shaped sample per vendor with fake IDs.
5. **Join-link echo.** A line whose only content is the `📹` URL is dropped.
6. **Empty result** means no bullets and no record noise.

Filtering is silent in the note, which keeps it clean. `sync -f json` can expose
`description_lines` plus `description_dropped` (for example `["conference"]`) for debugging.
Mark that field optional; it's nice-to-have.

### 5.5 Rendering grammar

- **Indentation.** Use the note's `dominant_indent_unit`, with tab as the fallback, exactly as
  capture does. Depth 1 is a direct child; depth 2 is the deepest. Deeper HTML nesting
  flattens to depth 2, matching capture's two-level authored bullets.
- **Plain-text lists.**
  - Leading `- `, `* `, `• `, `◦ `, `▪ `, `‣ ` mark list items; a leading tab or 2+ spaces
    means depth 2.
  - Ordered `1. ` / `1) ` items render as `- 1\. Intros`. The escaped dot avoids CommonMark's
    "bullet containing an ordered list" trap. Reading view shows `• 1. Intros`.
- **Lead-in rule** (the beautiful one). A list that directly follows a line ending in `:`
  nests under that line:

  ```text
  Agenda:            →   - Agenda:
  - Intros                   - Intros
  - System design            - System design
  Bring laptop           - Bring laptop
  ```

  A colon can't appear in a drawer title, so this rule **never manufactures a Task Drawer**.
- **HTML inlines.**
  - `<b>`/`<strong>` → `**…**` and `<i>`/`<em>` → `*…*`.
  - `<u>`, `<span>`, and `<font>` are dropped, keeping their text.
  - `<a href>` → `[text](url)` after unwrapping Google redirects.
  - When the anchor text equals the URL, the link is treated as a bare URL.
- **Bare URLs.**
  - Short URLs (≤ 40 chars) stay bare; Obsidian autolinks them.
  - Longer URLs render as `[host](url)`, for example
    `[docs.google.com](https://docs.google.com/document/d/…/edit)`. A 200-character token
    wrapping across three lines is the single ugliest thing a description can do.
  - Link URLs escape spaces and parentheses like `render.rs::escape_badge_url` does.
- **Overflow.** When more than `description_lines` bullets remain, render the first N − 1,
  then `- *…K more lines in [Google Calendar](<htmlLink>)*`.
- **Determinism.**
  - CRLF becomes LF, NBSP becomes a space, and trailing whitespace is trimmed.
  - Runs of internal spaces collapse.
  - The same description always yields the same bytes, so a rerun is a byte-identical no-op.

### 5.6 Sanitizer (the "description text is data" escaper)

Principle: **escape a character only where Obsidian, Dataview, Tasks, or Bob would give it
meaning.** Source mode stays readable, and live preview hides the backslashes. Add this as
`escape_note_text` beside `task_text_escape::escape_task_text`, reusing its helpers. Each
item below is vector-tested in both directions: the hazard is neutralized, and ordinary
text is left byte-identical.

| Hazard | Treatment | Why |
| --- | --- | --- |
| `` ` `` anywhere | `` \` `` | Inline DataviewJS `` `$= …` `` and inline DQL `` `= …` `` are **enabled** in the vault. Code spans and fences can also swallow the rest of the note. |
| `[[`, `![[`, `![` | `\[\[`, `!\[` | Wikilinks create backlinks and Task Mentions. Embeds pull in files, and remote images act as tracking pixels. |
| `<` (outside converted links) | `&lt;` | Raw HTML (`<img>`, `<iframe>`) |
| `#` that starts a tag token (after whitespace or at line start, followed by a tag character) | `\#` | Tag pane pollution, `#task` phantom tasks, a confusing `#offclock` on a child |
| Runs of `::` | `\:\:` (existing `escape_colon_runs`) | Dataview inline fields on list items |
| `%%` | `%&#37;` (existing) | Obsidian comments swallow text |
| Trailing ` ^id` | escaped (existing `escape_trailing_block_id`) | Fake block IDs collide with minted ones |
| `🍅` | `&#127813;` (renders as 🍅) | `row_untouched` treats any 🍅 in the block as worked, which would block Google-side cancels. Same trick as `%&#37;`. |
| Line-start `#`, `>`, `[ ]`/`[x]`, `+`/`*`/`-` + space, `N.`/`N)` + space | leading `\` | Headings, callouts, checkboxes, and nested lists inside a bullet |
| Two or more `$` on one line | `\$` | Inline math (`$5-$10`). A single `$40` is left alone. |
| Tasks/priority emoji | **left as is** | Children are not tasks (Tasks global filter `#task`, and no checkbox is ever written), so ZWSP joiners would be invisible noise. |

### 5.7 Placement and the ownership algorithm

**Placement.** The description block is always the row's **first children**, placed after any
managed first-child lines (Depends-On, an existing CANCEL LOG). Bryan's notes go below. The
rule is easy to remember: *Google's description sits at the top of the meeting; your notes
go under it.*

**Journal.** `gcal.row` gains a sibling key. It must **not** live inside `spans`, because
`remove_lifecycle_context` compares `spans` maps for exact equality.

```json
{"kind":"gcal.row", "...": "...", "spans":{"time":"…","title":"…","badges":"…"},
 "description":{"hash":"3f1c9a0d6b2e8a71","lines":2}}
```

There are three states:

| State | Meaning |
| --- | --- |
| Key absent | Legacy row (pre-feature). Treated as an empty tracked block, so it backfills. |
| `{"hash","lines"}` | Tracked. Bob last wrote this block. |
| `null` | Hands-off. A crash-adopted row whose bullets could not be matched. Never touched. |

**Hash input.** Hash each bullet as `(depth, text)`, without its indent characters, so a
tab↔space re-indent does not read as an edit. Use the same 16-hex `span_hash`.

**Locating the block.** Inside the row's child block (`child_block_end_line`), find the first
window of `lines` lines that satisfies all of these:

1. It starts at a depth-1 line.
2. The line after it is depth ≤ 1, or the block ends. This means Bryan nesting his own note
   *under* a Google bullet makes the block his.
3. Its hash equals the recorded hash.

`lines = 0` is always found, at the insertion point.

**Per-sync decision for a journaled Event Task:**

| Window found? | Fresh hash vs recorded | Action |
| --- | --- | --- |
| yes | equal | nothing |
| yes | different | replace the window with the fresh render and journal the new hash and lines (`updated`) |
| no, but a window matches the **fresh** render | – | journal it (adopt; no write) |
| no | – | keep, report once `kept your edit to the description bullets` (flag `kept_description`), and keep the old record so it is never re-added |

**Lifecycle:**

| Event | Behavior |
| --- | --- |
| Row created (any phase) | Row and bullets are written together via `insert_block`. |
| Maybe→Yes upgrade | Bullets are inserted under the upgraded row. |
| Time change (re-slot) | Bullets move with the child block (already true). Update the description **before** `apply_span_updates`, so the row's `line_index` stays valid (insertions are below it). |
| Google cancel, decline, or move | Unchanged. The CANCEL LOG becomes the first child above the bullets, and the bullets stay as history. |
| Row deleted or moved by Bryan | Tombstoned as today, and the bullets go with it. |
| Crash adoption | Scan for the fresh window and journal it if found; otherwise journal `description: null`. **Adoption never adds bullets.** |
| Bryan deletes all bullets | Window not found, so it is kept forever (reported once). |
| Google removes the description | Window found, so the bullets are removed (replaced by an empty block). |

### 5.8 CLI, JSON, and config

- **Dry run.** `sync -d` already prints the exact diff, so the bullets show up for free.
- **Human sync rows.** Append a dim `≡ N` after the root:
  `+ task    08:00–08:15  Swings!  ● love  via @love  ≡ 1`. An updated description reads
  `~ task … ≡ 2`.
- **`list` table.** Add a dim `≡ N` after the title, so `list` keeps previewing what sync would
  write.
- **JSON (additive, `schema_version` stays 1).** `sync` rows and `list` events gain
  `description_lines` (int). They never carry text.
- **Config.** This mirrors the existing `tentative: context|task` enum style:

  ```yaml
  gcal:
    description: bullets   # bullets | off   (default bullets)
    description_lines: 8   # integer ≥ 1; the overflow bullet counts toward it
  ```

  A wrong type is a setup error naming the key, as for the other `gcal.*` keys. `off` writes
  nothing and leaves existing bullets alone. Bullets that were tracked before `off` are
  simply no longer reconciled.

## 6. Recommended solution

### 6.1 One-sentence model (for docs and help)

> Whatever you write in a Google event's description, except Bob's directive lines and
> video-call boilerplate, appears as bullets at the top of that meeting's Event Task, and keeps
> following Google until you edit those bullets.

### 6.2 Examples

**Bryan's own event, plain text** (real, 2026-11-02). Description:
`And retainers!\n\n@love #offclock`

```markdown
- [*] #task **0800-0815** Swings! [📅](…) #offclock [root:: love] [type:: MEET] ^swings
	- And retainers!
```

**Work meeting, Google web editor HTML.** Description:
`<b>Agenda:</b><ul><li>Intros</li><li>System design – <a href="https://www.google.com/url?q=https://docs.google.com/document/d/1AbC/edit&sa=D&source=calendar&usg=x">prep doc</a></li></ul>Bring laptop &amp; ID<br>@job -15`

```markdown
- [*] #task **1400-1500** Onsite interview [📅](…) [📍](…) [buffer:: -15m] [root:: job] [type:: MEET] ^onsite-interview
	- **Agenda:**
		- Intros
		- System design – [prep doc](https://docs.google.com/document/d/1AbC/edit)
	- Bring laptop & ID
```

**External Teams invite** (the shape of the real 2026-10-30 interview). The description is
entirely the Teams block, so **no bullets**, and the row is unchanged from today:

```markdown
- [*] #task **0800-0830** Product interview [📅](…) [📹](https://teams.microsoft.com/meet/… "Join call") [📍](…) [root:: job] ^product-interview
```

**Long description** with the default cap of 8:

```markdown
	- Welcome to the loop! Here is what to expect…
	- …(6 more bullets)…
	- *…5 more lines in [Google Calendar](https://www.google.com/calendar/event?eid=…)*
```

**Hostile organizer text** (from the security vectors):

| Description line | Bullet written |
| --- | --- |
| `` Run `$= dv.el("b", 1)` now `` | ``- Run \`$= dv.el("b", 1)\` now`` |
| `- [ ] RSVP #task by Friday` | `- \[ ] RSVP \#task by Friday` |
| `See [[Secret Note]] ![](https://t.example/p.png)` | `- See \[\[Secret Note]] !\[](https://t.example/p.png)` |
| `Bring 🍅 salad` | `- Bring &#127813; salad` |
| `Room:: 4B` | `- Room\:\: 4B` |

### 6.3 Code touch points

| File | Change |
| --- | --- |
| `src/native/gcal/description.rs` (new) | Detect HTML or plain text, tokenize, build structured lines, run the directive classifier (shared predicate), apply filters, cap. Produces `Vec<DescriptionLine>`. Unit vectors live here. |
| `src/native/gcal/model.rs` | `GcalEvent` gains `description: Vec<DescriptionLine>`, sanitized and structured; raw text is still dropped after parse. `description_directives` folds the directive lines from the same parse. Update the module doc comment ("parsed only long enough…"). |
| `src/native/task_text_escape.rs` | `escape_note_text` (§5.6), reusing the colon, `%%`, and block-ID helpers. |
| `src/native/gcal/render.rs` | `render_description_block(lines, indent_unit, cap, html_link) -> Vec<String>` plus `description_hash`. |
| `src/native/gcal/plan.rs` | `PlannedOccurrence.description` (rendered lines, hash, count). Row creation goes through `working.insert_block`. A new `apply_description_update` runs before `apply_span_updates`. Also changes to the upgrade path, the adoption path, `rows_updated`, and a new `kept_description` notice. |
| `src/native/gcal/journal.rs` | `RowRecord`/`NewRow` gain the `description` tri-state. Parse it as a sibling of `spans`. |
| `src/native/gcal/sync.rs` / `list.rs` | `≡ N` human suffix and the `description_lines` JSON field. |
| `src/native/config/gcal.rs` | `description` and `description_lines` keys plus their validation. |
| `docs/gcal.md` | A new **Description bullets** section. Ownership-table rows: "Description bullets: Google until you edit them" and "Other child bullets (meeting notes): You, never touched". JSON field notes and a Known-limits entry. |
| `docs/reference/configuration.md`, `docs/reference/json-outputs.md` | The new keys and fields. |
| Decision record (via `/sase_memory_write`) | **"Description Bullets Follow Google Until Edited"**, partly superseding the children clause of `bob-gcal-is-read-only-and-proposes-once`. A draft follows below. |
| `glossary:event-task` | One sentence noting that the description bullets are the row's first children. |

**Decision record draft.**

- **Claim:** sync writes an Event Task's non-directive, non-boilerplate description as its
  first child bullets. They follow Google while the block matches Bob's journaled hash.
  Bryan's edit, nested note, or deletion makes the block his: kept, reported once, never
  re-added. Other children stay his. Text is sanitized data, and JSON carries only counts.
- **Rejected alternatives:** write-once (stale); a wrapper drawer (chrome and catalog
  pollution); inline markers (visible and copy-paste fragile); positional ownership (breaks
  on inserted logs); context-row bullets (conflict with the removal rule).
- **Reopens when:** context rows need details, or deleting one occurrence's bullets should
  teach the series.

### 6.4 Tests

- **`tests/fixtures/gcal_description/vectors.json`** (new, bob-cli only). Each case maps
  `input` to `directives` plus `bullets` (exact lines). Cases:
  - Plain, HTML, and mixed input.
  - Lists, including the lead-in colon rule and ordered items.
  - Links: Google redirect unwrapping, anchor text equal to the URL, long bare URLs, and
    `text<url>` autolinks.
  - Teams, Zoom, Google Meet ICS, and Webex boilerplate.
  - Separator lines, the cap and overflow bullet, and directive-only input (no bullets).
  - Every sanitizer hazard in both directions.
- **`tests/fixtures/event_buffer/vectors.json` stays untouched and green.** It is the
  cross-repo contract.
- **`tests/gcal_sync.rs`:**
  - A created row with bullets in all three phases.
  - A second run is a byte-identical no-op.
  - `-d` diff output.
  - `description: off`.
  - Tab and space notes.
  - New rows still land after the previous row's bullets.
- **`tests/gcal_lifecycle.rs`:**
  - Google edits the description → updated in place.
  - Bryan edits a bullet → kept and reported once, with no repeat on the next run.
  - Bryan deletes the block → never re-added.
  - Bryan nests a note under a Google bullet → kept.
  - Bryan's notes and a WORK LOG above or below the block → still found and updated.
  - A time change re-slots the row with its bullets.
  - Maybe→Yes upgrade gains bullets.
  - Cancel keeps the bullets under the CANCEL LOG.
  - Crash adoption never duplicates bullets.
  - A legacy row backfills.
  - A 🍅 in the description doesn't make the row "worked".
  - Context rows never get bullets, and still get removed on decline.

### 6.5 Phasing

1. **Parser, sanitizer, and vectors.** Pure code, no vault writes. `description_directives`
   is reimplemented on the shared parse, and the existing vectors gate it.
2. **Birth-time bullets, journal record, config, and output.** Rows are created with bullets
   and the hash is recorded. That is already safe (write-once behavior) and could ship alone.
3. **Lifecycle:** update while unedited, the kept notice, backfill, upgrade, and adoption.
4. **Docs and the decision record.** These land with phase 3, because phase 3 is what changes
   the ownership contract.

Phases 2 and 3 can go in one release. Splitting them only creates a short write-once period,
and the recorded hashes make the later upgrade seamless.

## 7. Risks and open questions

| Item | Risk | Mitigation or question for Bryan |
| --- | --- | --- |
| Boilerplate heuristics | A new vendor format slips through and shows junk. | Use fixture-driven filters and add a vector for each one seen. Worst case is a few ugly bullets, which Bryan can delete; deletion is permanent for that day. |
| Recurring series repetition | A long static description repeats every week. | **Question:** should deleting one occurrence's bullets teach the series (like root learning)? I recommend v2 if it actually bites. |
| Cap default | Is 8 right? Should very long paragraphs also be truncated by character count? | **Question.** I recommend a line cap only for v1 and no text truncation. The overflow link covers the rest. |
| Long-URL host labels | The domain-only label hides *which* doc. | **Question:** `[docs.google.com](…)` or keep bare URLs? I recommend host labels; the link still works and hovering shows the URL. |
| Legacy backfill duplicates | Bryan may have hand-copied a description under an existing row. | Rare. Backfill only touches days that get synced (today, or explicit `-D`). |
| HTML-nested ALL-CAPS item with children | Could parse as a drawer, for example a `<li>TODO<ul>…` description. | Rare and harmless. The colon lead-in rule never creates drawers by construction. |
| A text line containing a directive token | Bryan may expect `Bring shoes #offclock` to work. | The bullet visibly shows `\#offclock` and the row stays on-clock. Optional: a once-reported hint, "`#offclock` only works on its own description line". |
| Mac capture agenda and Ledger Tools | They don't show descriptions. | Out of scope. A future additive `description_lines` in `capture-pomodoros --tasks` JSON could drive a `≡` glyph, keeping the thin-client contract. |

## 8. Final recommendation

Ship **flat, sanitized, filtered, capped description bullets as the first children of
sync-created Event Tasks**. They are **Google-owned until edited**, tracked by a journal block
hash in a new `description` sibling of `spans`, and located by a subtree-bounded window
search. They are built from **one structured description parser** whose directive verdicts
stay byte-compatible with the shared `event_buffer` vectors.

Default to `gcal.description: bullets` with an 8-bullet cap and a link back to Google
Calendar. Report counts, never text, in JSON, and show `≡ N` in human output. Record the
ownership change as a new decision record that partly supersedes "children are yours, never
touched".

This keeps the motivating case beautiful ("And retainers!" right under "Swings!"). It also
keeps external invites as clean as they are today and closes the DataviewJS/embed hole a naive
implementation would open. The behavior can be stated in one sentence.

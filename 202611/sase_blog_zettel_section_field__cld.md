# A `section` field for the SASE Blog Zettel album

> **Research query:** Add a `record.section` property to the `~/bob/sase_blog_zettel.md`
> album that names the blog-post section each zettel is targeted at, using a fixed set
> of values built from the `^section-field` task in `~/bob/sase_blog.md`, plus any other
> related fields that are clearly useful. Critique the plan, suggest justified changes,
> and recommend an implementation.

Researcher: `cld`. Verified 2026-11-16 against the live vault, bob-cli `docs/` and
`src/native/albums/`, and `bob 0.5.0`. I tested every write step in a scratch Git
vault, never in `~/bob`.

## Bottom line

**Yes, add `section`. It is a good idea now, though it reverses an earlier
recommendation. Make it *replace* `part` rather than sit beside it.** Concretely:

1. **`section` is a scalar, optional choices field.** Its keys are short concept
   names (`gate`, `memory`, `plan`). Its labels are short and carry emoji. The choices
   are declared in outline order. The keys never contain heading wording or numbers,
   so rewording or reordering the post never touches a record.
2. **Thirteen values:** the eleven sections in the `^section-field` task plus
   **`intro`** (an addition I'm calling out). There is no `why` or `conclusion` value;
   both are open questions.
3. **Retire `part`.** `section` determines `part`, so keeping both creates a
   consistency rule that Bob can't check. `part`'s values are also already out of date
   against the new outline.
4. **Change `index_facets` to `[section, claim]`** so every row in the generated index
   shows its section.
5. **Add no other fields.** I tested every candidate (order, post, proof, words, task
   link, subsection, a list-valued or required `section`, `index_by`). None is clearly
   useful, and the reasons are below. The most useful related changes are not fields:
   a "By section" Base view, and one round of outline cleanup (four copies of the
   outline now exist).
6. **Migrate in the right order.** If `part` is removed from the schema before the one
   existing record drops `part: why`, Bob refuses to clear it and `records check`
   errors. The exact sequence is in the [recommended solution](#recommended-solution).

## Ground truth

| Fact | Evidence |
| --- | --- |
| The album currently has `status` (required choices), `claim` (required text), `part` (optional choices: `hook`, `why`, `what`, `why_not`, `close`), and `index_facets: [part, claim]`. | `~/bob/sase_blog_zettel.md` frontmatter |
| The album holds **one** record, `prompt_management_macros` (`status: seed`, `part: why`). | `~/bob/sase_blog_zettel/` |
| The earlier consolidated research **explicitly rejected** a `section` field: "There are no `order`, `section`, `wave`, or `target_words` fields. The article spine owns order, and the outline stays provisional." It also said `part` is a "display facet only … never an ordering field". | `ref/chat/sase_blog_zettel_album_guide` §2; `ref/chat/sase_blog_drafting_in_records` R5 and "Create the album" |
| The `^section-field` outline was first written on 2026-11-15 between 15:07 and 17:16, across many autosync commits. In that session it gained a "What is an 'agent'?" parent with three children and then flattened it away. It also gained "memory" and "The Demos". | `git log -p -- sase_blog.md` in `~/bob` |
| The article spine (`sase_blog_contents.md`, created 2026-10-15) still has the **older** outline: §1 Why I use SASE, §2 What is SASE? (2.1 Gates→Plans→Epics … 2.7 Routines and Jobs), §3 Why you should (probably) NOT use SASE, §4 Conclusion. It has no `→ [[zettel]]` link lines. | `~/bob/sase_blog_contents.md` |
| `sase_blog.md` `## Outline` holds a third, even older outline (XPrompts, ACE, AXE). | `~/bob/sase_blog.md` |
| Choice keys can be any non-empty string. Capture and `records update` accept **only the exact key**; anything else gets "expected one of intro, what, …". | `src/native/records/schema.rs` (choice parse ~L1273, validation ~L1420); scratch capture test |
| Capture completion for `- section:: ` lists the **labels in schema order**, inserts the **key**, and filters on label text (`tri` → `families`, `arti` → `plan`, `ready` → `not_ready`). | `bob capture-complete -f json` in scratch |
| Index facets render a choice's **label**. `index_by` subgroups render the **raw key**, sorted **alphabetically**, and only for status groups with more than 12 records. | `src/native/albums/index.rs` `format_scalar`; `src/native/albums/grouping.rs` `build_subgroups` / `LARGE_GROUP = 12` |
| The `[!records]` index always groups by `status` when a `status` choices field exists. `section` can only show up as a facet or subgroup. | `grouping.rs` `group_field` |
| `bob albums list -f json` and the Schema Card show a **per-choice usage count in declaration order**. That gives a coverage report for free. | Scratch: `[('intro',0),('what',0),('macros',1),…]`; `docs/reference/plugins/albums.md` ("choice chips with usage counts") |
| `bob articles` does **not** repair links inside frontmatter, and section numbers in headings are rewritten. | `docs/articles.md` "Heading identity and links" |
| Obsidian Bases groups automatically or by an explicit `groupOrder`. If `groupOrder` is present, **only listed values are shown**. There is no `indexOf`. `reduce` exposes `index` and `acc`. | [Bases views](https://obsidian.md/help/bases/views), [Bases syntax](https://obsidian.md/help/bases/syntax), [Bases functions](https://obsidian.md/help/bases/functions) |
| No other album declares `section`, and `.obsidian/types.json` has no `section` type, so there is no storage-shape clash. | `bob albums list -f json`; `types.json` grep |

## Critique: is this a good idea?

### It reverses a prior decision, and the reversal is justified

The earlier research rejected `section` for two reasons: the outline was unstable, and
the spine is the only authority for order. Neither reason rules out `section` as
designed here:

- **It is a targeting fact, not an order.** "This claim is meant for the Gate section"
  says nothing about where the claim sits within that section, or where the section
  sits in the post. The spine still owns order and wording. The album's choice order
  matches the outline by convention only, and nothing reads it as an order.
- **It fits claim-sized zettels.** The earlier warning was against *one record per
  section*. `section` is many-to-one: several claims can target one section, and an
  unassigned claim is allowed. That is the "several records may feed one section"
  model the guide already describes, recorded on the record instead of in the spine.
- **The spine-link alternative never happened.** The guide's plan was to put
  `→ [[sase_blog_zettel/…]]` lines under spine headings. The spine has none, S0 never
  ran, and the album has one record. Meanwhile your real working outline moved into a
  task's child bullets. A field you fill **at capture time** (`- section:: gate`, with
  label completion) costs far less than editing the spine for every new claim. It is
  also more likely to actually get used.
- **It pays for itself immediately.** Index rows read like an annotated outline
  (`— 🚦 Gate · <claim>`). The Schema Card's section chips show per-section counts, so
  zero-count chips are the sections with no material. A Base can group by section
  while you draft one.

### Risks and how the design handles them

| Risk | Mitigation built into the recommendation |
| --- | --- |
| **Outline churn.** The task outline was rewritten repeatedly in a single session. | Keys name *concepts*, not headings and not numbers. Rewording a heading is a label edit (Schema Card or YAML) and touches no record. Reordering is a YAML line move. Only a split or merge touches records, and with roughly 15 records that is minutes of work. |
| **Two fields for one fact.** `part` and `section` could disagree (`part: why_not`, `section: gate`), and Bob has no cross-field rule. | Retire `part`. Each top-level section is itself a `section` value (`what`, `demos`, `not_ready`, `future`), so coarse targeting is still possible. |
| **Outline sprawl.** The outline now lives in `sase_blog.md` `## Outline`, `sase_blog_contents.md` headings, and the `^section-field` bullets, and the album choices would make four copies. | After this change, make the spine's headings match the new outline. Leave the album as the only *vocabulary* and the spine as the only *order and wording*. Clear the task's bullet list, moving its two NOTEs and the "POTENTIAL FIRST LINE" into the spine. See [follow-ups](#follow-ups-outside-the-album-note). |
| **Forced misfiling.** A required field would make you pick a section for an idea that doesn't fit yet, or for ⏭️ Later and ✂️ Cut material. | Keep it optional. An empty `section` honestly means "no home yet", and those records point to sections the outline is missing. |

### Would I take a different approach?

No. A choices field on the album is the right tool and matches your "fixed set I can
change by editing the album" requirement. The alternatives I considered and rejected:

| Alternative | Why rejected |
| --- | --- |
| A `link` field pointing at a spine heading (`[[sase_blog_contents#What is a "gate"?]]`) | `bob articles` renumbers headings and does not repair links in frontmatter, so links would break. It is not a fixed set, and the spine doesn't have the new headings yet. |
| Spine `→ [[zettel]]` link lines only (earlier recommendation) | Still worth doing at assembly time for ordering within a section, so it complements `section` rather than replacing it. On its own it requires a spine edit for every capture and gives no coverage view. |
| Two levels: `part` (H2) plus `section` (H3) | Introduces the same unenforceable rule (`section` implies `part`). The hierarchy is better carried by declaration order and labels. |
| Hierarchy in keys (`what_gate`, `what_memory`) | Clusters keys alphabetically in Bases, but bakes today's hierarchy into keys Bob can't rename (`albums update` refuses key renames). The "What is an agent?" parent appeared and disappeared within one session, which is exactly the risk. |
| Number-prefixed keys (`s2_3_gate`) for sorting | Every reorder becomes a key rename plus a record migration. |
| `list: true` (one record targets several sections) | A claim that targets two sections should be split or is cross-cutting. Bob only uses the first item in grouping, and Bases' grouping of lists is undocumented. |
| Tags (`#section/gate`) or folders per section | Tags aren't schema-checked or completed. Albums treat nested folders as `record_outside_album`. |

## The value set

I built this from the current `^section-field` bullets, in their order. **Bold** rows
differ from the task.

| `^section-field` bullet | Key | Label | Note |
| --- | --- | --- | --- |
| **(not in task)** | **`intro`** | 🪝 Intro | **Added.** The spine already has an intro paragraph (the only real prose so far), `^intro-v1` exists, `part` had `hook`, and Requirements has intro-specific bullets (timeline opener, `tmux_ai_window`). |
| What is SASE? | `what` | 🧱 What is SASE? | Parent section. Use it for overview material. Keeps the old `part` key `what`. |
| What is a "prompt language" (macros)? | `macros` | 📜 Prompt language (macros) | Matches the current sase name ("Macros, not Xprompts"). |
| What is an "agent turn"? | `turn` | 🔁 Agent turn | |
| What is a "gate"? | `gate` | 🚦 Gate | |
| What are agent families, clans, and tribes? | `families` | 👪 Families, clans & tribes | |
| What is a "memory"? | `memory` | 🧠 Memory | |
| What is a "plan"? (include artifacts) | `plan` | 🗺️ Plan & artifacts | The label carries the task's NOTE. |
| What is a "project"? | `project` | 📁 Project | |
| What is an "automation" (service)? | `automation` | ⚙️ Automation (service) | |
| The Demos | `demos` | 🎬 The Demos | |
| Why SASE is still NOT ready? | `not_ready` | 🛑 Why SASE is still NOT ready | Reuses `part`'s `why_not` emoji. |
| Future Work | `future` | 🔮 Future Work | |
| **"Why I use SASE" (spine §1, old `part: why`)** | — | — | **Not added.** None of the four task iterations includes it, and the move from "why (not) use it" to "what it is / is it ready" looks deliberate. The one `part: why` record fits `macros` by its claim. Open question 1. |
| **"Conclusion" (spine §4, old `part: close`)** | — | — | **Not added.** Future Work appears to be the new closing section. Open question 2. |

Why **short labels** instead of the full question headings: labels appear in index
facets, Schema Card chips, and capture menus, where the shorter form reads better. The
final heading wording belongs to the spine, and every heading-faithful label would be
one more copy to keep in sync. Because labels can be edited without touching records,
this choice is cheap to reverse.

## Related fields: what changes, what doesn't

**Change**

- **Remove `part`.** It is redundant with `section`, its values are out of date against
  the new outline (no `demos` or `future`, and `why`/`close` are gone), and it is used
  by one record.
- **`index_facets: [section, claim]`.** Without this, the index never shows the
  section. Scratch result:
  `[[…|Prompt Management (macros)]] — 📜 Prompt language (macros) · Prompts should be managed like code…`

**Reject** (none of these is clearly useful)

| Candidate | Why not |
| --- | --- |
| `index_by: section` | Subgroup headings would be raw keys (`**gate**`) in alphabetical order, and only inside a status group with more than 12 records. Facets already show the label on every row. |
| `order` / `rank` | The spine owns order (still true). Reordering would mean editing N records. |
| `post` / `target_post` for ⏭️ Later | Speculative. The `## Later Posts` list is itself provisional, and `status: later` already records the fact. |
| `proof` / `artifact` | Proofs are local screenshot paths and come in several per claim, so they fit no url/link kind. CARD material belongs in `## Notes`, as the earlier research also concluded. |
| `words` / `target_words` | Derived values that go stale. `bob articles outline` counts words in the spine. |
| `task` (link to a `zd-*` task) | Duplicates the task-to-record link the guide already prescribes. |
| `subsection` | Flat keys already cover the hierarchy. |
| `required: true` on `section` | Forces misfiling. See the risks table. |
| `gastown` term | The Requirements bullet ("link to the analogous GasTown term") is per section, not per zettel, and is content, not metadata. |

## Requirement adjustments (called out)

| # | Your requirement | Adjustment | Why |
| --- | --- | --- | --- |
| A1 | Add `record.section` | **Kept**, as an optional, scalar choices field | Many-to-one targeting; an empty value means "no home yet". |
| A2 | Values from `^section-field` | **Plus `intro`**; no `why` or `conclusion` | Evidence above; both omissions are flagged as questions. |
| A3 | (implicit) values look like the section headings | **Keys are concept names; labels are short** | Survives rewording and reordering; completion matches label text. |
| A4 | Add other clearly useful fields | **No new fields.** Instead **remove `part`** and **retarget `index_facets`** | One fact, one field. Every new-field candidate failed the "clearly useful" bar. |
| A5 | Change only the album note | **Also migrate the one record, and optionally add a Base view** | Required for a clean `records check`. The Base is the main way you'll use `section`. |
| A6 | (new) | Keep **one outline vocabulary** (album) and **one order and wording** (spine) | Four outline copies already disagree. |

## Recommended solution

### Final album frontmatter

Only `index_facets` and the `part` → `section` block change. I checked this exact
YAML in the scratch vault: `albums check` and `records check zettel` report 0 errors.

```yaml
---
parent: "[[sase_blog]]"
type: "[[album]]"
summary: Topic-sized pieces of my SASE posts, one claim per record, in my own voice.
emoji: 📇
created: 2026-11-12T13:54:08-0500
index_facets: [section, claim]
record:
  noun: zettel
  label: Zettel
  dated_notes: true
  fields:
    status:
      required: true
      values:
        seed: 🌱 Seed
        draft: ✍️ Draft
        ready: ✅ Ready
        placed: 📌 Placed
        later: ⏭️ Later
        cut: ✂️ Cut
    claim:
      required: true
    section:
      values:
        intro: 🪝 Intro
        what: 🧱 What is SASE?
        macros: 📜 Prompt language (macros)
        turn: 🔁 Agent turn
        gate: 🚦 Gate
        families: 👪 Families, clans & tribes
        memory: 🧠 Memory
        plan: 🗺️ Plan & artifacts
        project: 📁 Project
        automation: ⚙️ Automation (service)
        demos: 🎬 The Demos
        not_ready: 🛑 Why SASE is still NOT ready
        future: 🔮 Future Work
---
```

Don't put YAML comments in this block (for example `# What is SASE? subsections`). If
Obsidian's Properties UI ever rewrites the frontmatter, the comments may be lost.
Declaration order is enough.

### Migration: pick one path

**The ordering trap (verified):** removing `part` from the schema while the record
still has `part: why` gives `ERROR · part: unknown field part` from `records check`.
After that, `bob records update … -s part=` is refused with "`part` is not a Zettel
field". Clear the record's value **before** removing the schema field, or fix both in
the same edit.

**Path A: one hand edit (fastest with one record; verified).**

1. In Source mode, replace the album frontmatter with the block above.
2. In `sase_blog_zettel/prompt_management_macros.md`, replace `part: why` with
   `section: macros`, or another key if you prefer (see open question 1).
3. Run `bob albums sync`, then `bob albums check` and `bob records check zettel`.
   Expect 0 errors. Sync regenerates the index facet.

**Path B: guarded commands (each step validated and committed; verified).**

1. Hand-edit the album: add the `section` block (keep `part` for now) and set
   `index_facets: [section, claim]`.
2. `bob records update zettel prompt_management_macros -s section=macros -s part=`
   This sets `section` in `part`'s place, removes `part`, and rebuilds the index in
   the same write.
3. Remove `part` with the Schema Card (**⊞ Schema** → select Part → `Ctrl+D` →
   Enter). It previews "remove field "part" (was unused)" and commits
   `albums: update sase_blog_zettel.md (field.remove part)`. The CLI equivalent is
   `bob albums update sase_blog_zettel` with
   `{"schema_version":1,"expect":"<fingerprint from bob albums list -f json>","ops":[{"op":"field.remove","field":"part"}]}`.
4. Run `bob albums check` and `bob records check zettel`.

### Capturing with the new field

```text
A gate is plan mode, generalized @sase_blog_zettel/^gate-generalizes-plan-mode
- status:: seed
- claim:: Plan mode is one instance of a deeper primitive: a gate that pauses an agent until a human or rule answers.
- section:: gate
```

In the scratch vault, the dry run planned `section: gate` and the index row
`— 🚦 Gate · Plan mode is one instance…`. An unknown value such as `gates` is refused
with the full key list. In Mac Capture, type `- section:: ` and pick from the
label-filtered menu.

### Base view (optional, recommended)

Bob's index stays grouped by status, so the place to "show me everything for the Gate
section" is a Base. Add `section` and `claim` columns to the existing view, and add a
second view:

```yaml
  - type: table
    name: "🧭 By section"
    filters:
      and:
        - note.status != "cut"
        - note.status != "later"
    groupBy:
      property: section
      direction: ASC
    order:
      - formula.name
      - status
      - claim
    sort:
      - property: formula.name
        direction: ASC
    summaries:
      formula.name: Count
```

Groups appear in alphabetical key order. **Don't add `groupOrder`** to force outline
order: Bases then *hides* any value missing from the list, so a section added to the
album later would silently drop out of this view. For counts in outline order, use
the Schema Card's section chips or `bob albums list -f json`. I checked that this YAML
parses but did not render it in Obsidian. Also check how Obsidian shows records with
no section; the docs don't say.

### Follow-ups outside the album note

1. **Bring the spine's headings in line with the new outline** in
   `sase_blog_contents.md` (`bob articles` renumbers). Do it in the same session, so
   the album vocabulary and the spine agree from day one.
2. **Clear the `^section-field` bullet list** once the field exists. Move its NOTEs
   and the "POTENTIAL FIRST LINE" into the spine under the matching headings, so the
   task doesn't remain a fourth outline.
3. Consider deleting or archiving the stale `sase_blog.md` `## Outline` (the
   XPrompts/ACE/AXE era). That's your call. It isn't needed for this change.
4. Changing the outline later works like this. **Reword** a heading: edit the label.
   **Reorder**: move the YAML line. **Add** a section: add a choice. **Split or
   merge**: add the new choice, then `bob records update … -s section=<new>` for each
   affected record, then remove the old choice (the Schema Card refuses removing a
   used choice, which is the safety net you want).

## Open questions

1. **"Why I use SASE":** was it left out on purpose (folded into the intro), or just
   not written into the task yet? If you want it, add
   `why: 🙋 Why I use SASE` between `intro` and `what`. Then decide whether
   `prompt_management_macros` belongs to `why` (its old `part`) or `macros` (its
   claim). I'd pick `macros`.
2. **Conclusion:** is "Future Work" the close, or do you want a `close: 🏁 Conclusion`?
3. **`intro`:** keep it (recommended), or leave intro material unassigned until
   `^intro-v1`?

## Sources

- Vault (read-only): `~/bob/sase_blog_zettel.md`, `~/bob/sase_blog_zettel/`,
  `~/bob/sase_blog_zettel.base`, `~/bob/sase_blog.md` (and its `git log -p` history
  for `^section-field`), `~/bob/sase_blog_contents.md`.
- Prior research (vault ref sources): "Draft the SASE blog in claim-sized zettels"
  (`ref/chat/sase_blog_zettel_album_guide`) and "Drafting the SASE blog post in record
  notes: consolidated research" (`ref/chat/sase_blog_drafting_in_records`).
- bob-cli: `docs/records.md`, `docs/capture.md` (Record notes, Guided fields),
  `docs/articles.md`, `docs/reference/plugins/albums.md`,
  `src/native/albums/grouping.rs`, `src/native/albums/index.rs`,
  `src/native/records/schema.rs`.
- Scratch-vault runs (bob 0.5.0): `albums check`, `records check`,
  `records update -d`/apply, `albums update -d`/apply (`field.remove part`),
  `capture --dry-run`, `capture-complete -f json`, `albums list -f json`,
  `albums sync -d`.
- Obsidian Bases: [Views](https://obsidian.md/help/bases/views),
  [Syntax](https://obsidian.md/help/bases/syntax),
  [Functions](https://obsidian.md/help/bases/functions); changelogs
  [1.10.0](https://obsidian.md/changelog/2025-10-01-desktop-v1.10.0/) and
  [1.10.3](https://obsidian.md/changelog/2025-11-11-desktop-v1.10.3/) (`reduce`).

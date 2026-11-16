# SASE blog zettels: section taxonomy and a small migration

Independent research by **cdx**, 2026-11-16.

**Recommendation:** use Bob's existing album choices schema for an optional, single-valued `section` field. Make it the authoritative destination for a zettel, replacing the overlapping `part` field after a small, explicit migration. Preserve `status` and `claim`; add no other record fields now. Show section in the album index and add a section-oriented view to the existing Base. This needs vault configuration and content edits, not a new Bob feature.

## Evidence and scope

I independently inspected the requested task, album, existing record, current draft, and Bob's implementation. I did not read any other researcher’s report, findings, or transcript.

The vault evidence is the Git-backed checkout opened through `sase repo open gh:bobs-org/bob`, at commit `dd0dbcb3cb2eabf3fcbe620751392649a3c1bdfa` (2026-11-15 20:09:53 -05:00). This is a snapshot of the synced vault, not a claim to have inspected any unsynced edits in the live `~/bob` directory. Implementation sources are bob-cli commit `7729a96220e57a517f749ad08903e1084679238c`. Behavioral probes used the installed `bob 0.5.0` in a disposable fixture inside the workspace. No real vault notes or application code were changed.

Primary evidence:

- **V1 — Current album:** [`sase_blog_zettel.md`, lines 1–42](https://github.com/bobs-org/bob/blob/dd0dbcb3cb2eabf3fcbe620751392649a3c1bdfa/sase_blog_zettel.md). It already defines required `status`, required `claim`, and optional `part`, with `index_facets: [part, claim]`.
- **V2 — Requested outline:** [`sase_blog.md#^section-field`, lines 31–46](https://github.com/bobs-org/bob/blob/dd0dbcb3cb2eabf3fcbe620751392649a3c1bdfa/sase_blog.md#L31-L46). Its eight concepts must be subsections of “What is SASE?”; plans must include artifacts. The other named sections are demos, why SASE is not ready, and future work.
- **V3 — Existing prose structure:** [`sase_blog_contents.md`](https://github.com/bobs-org/bob/blob/dd0dbcb3cb2eabf3fcbe620751392649a3c1bdfa/sase_blog_contents.md). It has an introduction, “Why I use SASE,” an older breakdown of “What is SASE?”, limitations, future work, and a conclusion. Its subsection numbering differs from older drafting tasks. The draft is therefore context, not an automatic source of enum keys.
- **V4 — Existing record:** [`prompt_management_macros.md`](https://github.com/bobs-org/bob/blob/dd0dbcb3cb2eabf3fcbe620751392649a3c1bdfa/sase_blog_zettel/prompt_management_macros.md). The sole record is `status: seed`, `part: why`, with a claim about managing prompts like code and an empty Notes section.
- **C1 — Supported contract:** [`docs/records.md`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/docs/records.md), especially Albums, Updating an album schema, Schema, and Updating notes.
- **C2 — Parser and grouping:** [`records/schema.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/src/native/records/schema.rs), [`albums/grouping.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/src/native/albums/grouping.rs), and [`albums/mod.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/src/native/albums/mod.rs).
- **C3 — Existing integration coverage:** [`tests/cli/albums_update.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/tests/cli/albums_update.rs), [`tests/cli/records.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/tests/cli/records.rs), and [`tests/cli/capture/complete_records.rs`](https://github.com/bobs-org/bob-cli/blob/7729a96220e57a517f749ad08903e1084679238c/tests/cli/capture/complete_records.rs). These were inspected, not rerun as a suite.

## Is this a good idea?

Yes, provided section is a lightweight drafting aid. The album explicitly holds topic-sized pieces, one claim per record, in Bryan’s own voice. A destination lets Bryan pull together the claims needed for one section without searching every note. Keeping the vocabulary in the album matches Bob’s existing ownership model. [V1, C1]

The strongest concern is duplication: `part` already means coarse placement (`hook`, `why`, `what`, `why_not`, `close`). Adding a finer placement field without deciding their relationship produces contradictions. A record could say `part: why` and `section: what_prompt_language`; neither field tells a reader which placement to trust. Calling `part` a “rhetorical role” after the fact would invent a new meaning for existing data.

The second concern is turning an outline into a capture prerequisite. A useful seed often arrives before its home is known. Requiring section, or defaulting every seed to an arbitrary destination, would substitute bookkeeping for writing. Leave it absent until placement is decided. Empty is a valid unassigned state; it is not an error or another named blog section.

The third concern is taxonomy becoming a substitute for composition. There is only one record today, and the task and draft already contain different outlines. The benefit comes from a simple retrieval view while writing, not from designing a comprehensive ontology. A section assignment expresses intention; it does not prove that prose has been drafted or incorporated. Keep using the existing `status` choices for that distinction. [V1–V4]

## Recommended vocabulary

Use the task as the authority for the new conceptual breakdown. Preserve its eight “What is SASE?” children, keep artifacts with plans, and keep demos, current limitations, and future work distinct. Do not promote the task’s work log or suggested opening sentence into choices. Do not revive every older ACE/AXE, VCS, provider, or numbered draft heading as an additional choice.

I recommend **15 values**: twelve drawn from the requested outline, plus three compatibility destinations supported by the existing album and draft. The following labels are editable display text; the left column contains stable stored keys.

| Stored key | Display label | Basis / boundary |
| --- | --- | --- |
| `hook` | Hook / introduction | Explicit addition from the existing album and opening prose. |
| `why` | Why I use SASE | Explicit addition; current draft heading and existing record placement. |
| `what` | What is SASE? / overview | The task’s parent section; overview and transitions, not an “undecided subsection” bucket. |
| `what_prompt_language` | What is SASE? / Prompt language (macros) | Task’s prompt-language subsection. |
| `what_agent_turn` | What is SASE? / Agent turn | Task’s agent-turn subsection. |
| `what_gate` | What is SASE? / Gate | Task’s gate subsection. |
| `what_agent_groups` | What is SASE? / Agent families, clans, and tribes | Keep the task’s grouped concept together. |
| `what_memory` | What is SASE? / Memory | Task’s memory subsection. |
| `what_plan` | What is SASE? / Plan and artifacts | Includes artifacts as the task explicitly requires. |
| `what_project` | What is SASE? / Project | Task’s project subsection. |
| `what_automation` | What is SASE? / Automation (service) | Task’s automation subsection. |
| `demos` | The Demos | Demonstrations and their narrative, rather than every explanatory mention of a feature. |
| `why_not` | Why SASE is still NOT ready? | Present shortcomings, caveats, and limitations. |
| `future_work` | Future Work | Proposed improvements and future direction. |
| `close` | Conclusion | Explicit addition from the existing album and current draft. |

The `what_` prefix makes the subsection relationship clear without introducing independently editable parent and child fields. Bob still sees a flat choice set; it does not enforce a tree. The labels communicate the hierarchy to the reader. Keeping the existing `hook`, `why`, `what`, `why_not`, and `close` keys also makes a lossless migration from `part` straightforward.

The three added compatibility destinations are a deliberate adjustment to a strict reading of the task’s four top-level bullets. Omitting them would strand existing introduction, motivation, and conclusion material. If those sections are intentionally being eliminated, omit their currently unused choices after the editorial decision; do not infer that decision from their absence in one task.

## Exact schema and record shape

“`record.section`” should be interpreted as a schema-defined field, not implemented literally. The album declaration is **`record.fields.section`**. Each record then has a top-level **`section:`** property. A direct `section` child of the album’s `record:` block is unsupported, and a literal dotted field name fails Bob’s field-name rule. [C1, C2]

Merge this field under the existing `record.fields` mapping, preserving `status`, `claim`, the noun, date policy, and unrelated content:

```yaml
    section:
      label: Section
      values:
        hook: "Hook / introduction"
        why: "Why I use SASE"
        what: "What is SASE? / overview"
        what_prompt_language: "What is SASE? / Prompt language (macros)"
        what_agent_turn: "What is SASE? / Agent turn"
        what_gate: "What is SASE? / Gate"
        what_agent_groups: "What is SASE? / Agent families, clans, and tribes"
        what_memory: "What is SASE? / Memory"
        what_plan: "What is SASE? / Plan and artifacts"
        what_project: "What is SASE? / Project"
        what_automation: "What is SASE? / Automation (service)"
        demos: "The Demos"
        why_not: "Why SASE is still NOT ready?"
        future_work: "Future Work"
        close: "Conclusion"
```

Intentionally omit `required`, `default`, `list`, and `suggest`. This yields an optional scalar with a closed set of exact keys. Existing choice completion already supplies suggestions; `suggest: true` is unnecessary. An assigned record contains, for example, `section: what_plan`, not the display label or a nested `record` object. [C1, verified probe]

Example capture for a new record:

```text
Plans preserve the reasoning behind a change @sase_blog_zettel/
- status:: seed
- claim:: A saved plan lets later agents recover the reasoning behind a change.
- section:: what_plan
```

This is a syntax example, not proposed authored blog prose. A zettel with more than one possible use gets one primary destination; discuss secondary uses in Notes or link it from the draft. Do not duplicate the record merely to place it twice. If recurring cross-section reuse becomes substantial, revisit the model then.

Obsidian’s native Properties UI supports text and lists but does not provide Bob’s album-specific enum enforcement. Its property types apply across the vault, and nested properties are not supported in its standard editor. Bob supplies validation and completion; arbitrary manual YAML edits still require a check afterward. [Obsidian Properties documentation](https://obsidian.md/help/properties)

## What to do with `part` and other fields

**Make section the single destination field.** Initially add it without removing `part`, so the change can be inspected. Transfer existing placements, switch the visible index, then remove the old field once no record or view relies on it. Do not keep both indefinitely or add synchronization code between them.

For the sole existing record, a conservative migration is `part: why` → `section: why`. Its title mentions macros, but its existing placement is explicit and its body is empty. Automatically assigning `what_prompt_language` would be an editorial change unsupported by the available prose. Bryan can move it later when its intended use is clear. [V4]

**No additional record fields meet the requested high-confidence bar today.** The useful independent dimensions already exist:

- `claim` describes the point the zettel makes.
- `status` distinguishes seed, draft, ready, placed, later, and cut.
- `section` will say where the point is intended to appear.
- Bob already writes `created`; the album already enables dated Notes.

A provenance field such as `sources` is tempting because the project asks for citations, demonstrations, and screenshots. But the evidence includes URLs, vault links, images, and local screenshot paths. A single existing typed link or URL field would not represent that mixture cleanly. Notes can preserve a source, locator, and explanation together without introducing another list to curate. Add a dedicated field only when repeated retrieval needs justify a specific shape. Likewise, `priority`, `confidence`, `word_count`, `section_order`, `subsection`, `role`, and `draft_link` would add maintenance or duplicate information without a demonstrated need here. [V1, V2 requirements, C1]

## Make the field useful in the views

Change the album’s explicit facets to:

```yaml
index_facets: [section, claim]
```

Keep status as the generated index’s primary group. That behavior is built into Bob: a choices field named `status` wins even if another field is moved before it. Setting `index_by: section` would only create subgroups inside sufficiently large groups; it does not replace the primary status grouping, and has no immediate benefit for this one-record album. [C1, C2]

The existing `sase_blog_zettel.base` currently shows only the record name and status. Add section and claim to that view’s visible columns and add a second table view grouped by `section` for drafting. Keep an unassigned view/filter or otherwise make records with no section easy to find. The album schema update command deliberately leaves Base files unchanged, so this is a separate configuration edit. [V1, C1]

Bases supports multiple views, property grouping, and per-view filters. A plain section-grouped view will display stored keys unless a separate display formula is added. Start with those readable keys; do not duplicate all fifteen labels into a formula just for polish. Avoid a fixed `groupOrder` list initially: the current Bases contract hides groups not listed there, which could hide records after Bryan adds a choice only in the album. [Obsidian Bases syntax](https://obsidian.md/help/bases/syntax)

The declaration’s order is a sensible outline order, but a Base’s alphabetical grouping need not match it. If exact outline-order browsing becomes important, add that presentation deliberately; do not add a numeric section order to every record.

## Safe implementation and future editing

The eventual change can remain small:

1. Recheck the current album and record inventory against this snapshot. The inspected vault had six album schemas, none already declaring `section`, and one zettel. Bob requires shared field names to agree on scalar/list and storage type across albums. Repeat that check if the vault has changed.
2. Add the optional field with the shown YAML or a guarded `bob albums update` envelope. The envelope uses the current semantic fingerprint from `bob albums list -f json` and can be previewed with `-d`. To preserve these exact keys with that API, `field.add` can initially use each key as its choice label, followed in the same envelope by `choice.set` operations for the human labels. This exact pattern passed a dry-run probe.
3. Preview `bob records update sase_blog_zettel prompt_management_macros -s section=why -d`. Apply the migration only to records whose old placement supplies evidence; leave genuinely unassigned records absent.
4. Change `index_facets` and the Base presentation. When each old `part` value has been accounted for, clear it through `records update ... -s part=` and remove the unused schema field. `albums update` refuses a field removal while it is used or explicitly referenced by index settings; that is useful protection. If a later snapshot contains more records, inventory and migrate all of them before removal.
5. Check the selected records and album configuration; preview index repairs with `bob albums sync -d` before the real sync. Inspect the resulting diff. Preserve record bodies, claims, status, and dates. Finally open the Base in Obsidian to verify the added columns, section groups, and unassigned visibility.

These are implementation recommendations, not commands applied during this research. The guarded schema command updates an album and its generated index together; it does not perform the record migration, Base change, or top-level facet edit. Direct YAML editing remains a supported way for Bryan to change the vocabulary. [C1]

For future vocabulary changes:

- **Change a label:** keep the left-hand key; existing assignments remain valid.
- **Add a destination:** add a key/label to the album; no new application release is needed.
- **Rename or delete a stored key:** migrate affected records explicitly. Editing the choices mapping alone does not rewrite them. The guarded API refuses used removal and key renames; manual YAML can still make old records invalid.
- **Renumber headings:** change headings or display text, not stored section keys.
- **Add a later blog post:** reconsider placement per article when actual reuse occurs. The album summary mentions multiple posts, but a per-article placement model would be premature for the present task.

“Fixed set” therefore means a controlled vocabulary at a given moment, owned by this album. It cannot mean that all free-form editors prevent invalid input, or that deleting a choice automatically migrates records.

## Verification and limitations

The installed binary passed the following probes in a temporary fixture copied from the relevant album, record, and parent notes:

| Probe | Observed result |
| --- | --- |
| Guarded `field.add` plus label edits, dry run | Success; status remained the group before and after. |
| Load the proposed section declaration | All 15 choices recognized, scalar and optional. |
| Create with `section=what_plan`, dry run | Success. |
| Create with an unknown key | Exit 2. |
| Create with display label `The Demos` instead of key `demos` | Exit 2. |
| Create without section | Success. |
| Check the existing record without section | Success. |
| Update existing record to `section=why`, dry run | Success. |
| Report album with explicit `[section, claim]` facets | Group `status`; facets `section`, `claim`. |
| Complete a capture value beginning `what_` | Success; offered `what_plan`. |

An initial fixture-generation attempt also exposed a formatting pitfall: Python’s default YAML emitter wrote an unindented block sequence for `index_facets`; Bob treated it as no explicit facets and inferred `part, section`. Inspection of `parse_top_level_list` explains this: its block-list scan stops at the first unindented nonblank line. The successful probe preserved the existing inline sequence syntax. This supports making a narrow edit and retaining `index_facets: [section, claim]`, rather than reserializing the entire album. No unrelated parser change is required for this proposal.

The probes did not write the live vault, exercise a real sync/commit transaction, or render the Base in Obsidian. The installed binary’s exact build SHA was not established; its tested behavior agreed with the inspected source. Full UI and live migration verification belong to implementation.

## Requirements adjustments and recommended solution

The justified adjustments are explicit:

1. Implement `record.fields.section` in the album and `section:` in each record, correcting the literal `record.section` spelling.
2. Make assignment optional, single-valued, and default-free so capturing a seed does not require premature placement.
3. Include hook, motivation, and conclusion alongside the task-derived destinations to preserve current material.
4. Retire `part` after preserving its existing meaning in section assignments, instead of maintaining two placement fields.
5. Add index/Base presentation changes so section is useful while drafting; add no speculative record fields.

**Recommended solution:** adopt the 15-key schema above, retain `status` and `claim`, migrate the existing zettel conservatively to `section: why`, and remove `part` once the migration and references are checked. Keep one primary destination per record, use Notes for secondary uses and evidence, and let Bryan edit the album’s choice mapping as the outline evolves. This gives the requested organization through Bob’s existing validated workflow while keeping the actual work focused on writing the post.

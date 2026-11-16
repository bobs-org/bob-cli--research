# SASE Blog Zettel `record.section`: research and recommendation

Researcher: mus (`__mus`). Independent swarm report. Sources consulted
independently; no peer report was opened.

## Question

Add a new `record.section` property to the
`~/bob/sase_blog_zettel.md` album note: a fixed value set, editable by
editing that file, constructed from the `^section-field` task in
`~/bob/sase_blog.md`. Add any other related fields that are
objectively useful. Critique the plan and end with a recommended
solution.

## Sources and current state (verified)

- Album note `sase_blog_zettel.md` (via `bob query`, corroborated by file
  read): `parent: "[[sase_blog]]"`, `type: "[[album]]"`, summary
  "Topic-sized pieces of my SASE posts, one claim per record, in my own
  voice.", `index_facets: [part, claim]`, `record.noun: zettel`,
  `dated_notes: true`, fields `status` (required choices:
  `seed/draft/ready/placed/later/cut`), `claim` (required text),
  `part` (optional choices: `hook/why/what/why_not/close`).
- Record folder `sase_blog_zettel/` contains 1 record
  (`bob query WHERE file.folder = "sase_blog_zettel"`):
  `sase_blog_zettel/prompt_management_macros.md`, `status: seed`,
  `part: why`, claim "Prompts should be managed like code, with several
  different layers of structure (depending on complexity)."
- `^section-field` task (`sase_blog.md`, Next & In Progress):
  "Add `section` field to `[[sase_blog_zettel]]!" with children (verified
  via file read):
  - What is SASE? (explicit NOTE: all sub-bullets below are subsections
    of this section): prompt language (macros), agent turn, gate,
    families/clans/tribes, memory, plan (NOTE: include artifacts),
    project, automation (service).
  - The Demos.
  - Why SASE is still NOT ready? (potential first line noted).
  - Future Work.
  - Plus a `WORK LOG`.
- Competing outline `sase_blog_contents.md` (69 lines): `1. Why I use
  SASE`, `2. What is SASE?` (`2.1 Gates -> Plans -> Epics`, `2.2 Beads ->
  Sidecar repos`, `2.3 Agent CLIs` + `2.3.1`/`2.3.2`, `2.4 VCS`,
  `2.5 Xprompts`, `2.6 Project Management`, `2.7 Routines and Jobs`),
  `3. Why you should (probably) NOT use SASE` (`3.1 AI Slop`,
  `3.2 Future Work`), `4. Conclusion`.
- Contract `docs/records.md`: album schema under `record:`; field names
  `[a-z][a-z0-9_]*`; reserved `parent/type/title/created` cannot be
  fields (so `section` is allowed); choices vs text vs
  `date/link/url/number` via `values`; `required/suggest/list/default/
  label/min/max`; cross-type storage-shape agreement; `bob albums update`
  guarded JSON envelope (`schema_version/expect/ops`, `field.add`,
  `choice.add`, etc.); dry-run `-d`; index rebuild in same transaction;
  `bob records check` / `bob albums check` validation; capture
  `@dir/` + `key:: value` planner; `.base` grouping.
- Glossary (via `sase memory read`): album note owns one record-note
  schema and folder; record note holds schema-defined fields plus
  `## Notes`.

## Proposed `section` value set (from `^section-field`)

Keys are stable `snake_case` with no numbers or emoji in the key (key
renames are refused by `bob albums update`; labels can change freely).
Labels carry the emoji, matching the existing `status`/`part` style
(`seed: 🌱 Seed`, `why: 🙋 Why I use it`).

| key | label (YAML `label: Emoji Text`) | `^section-field` source | `contents.md` approx | `part` mapping |
| --- | --- | --- | --- | --- |
| `what_sase` | ❓ What is SASE? | "What is SASE?" parent | §2 What is SASE? | `what` |
| `prompt_language` | ⌨️ Prompt language (macros) | prompt language (macros) | §2.5 Xprompts | `what` |
| `agent_turn` | 🔄 Agent turn | agent turn | §2 (general) | `what` |
| `gate` | 🚦 Gate | gate | §2.1 Gates -> Plans -> Epics | `what` |
| `families` | 👪 Families, clans, tribes | families, clans, tribes | §2.3.2 presentation | `what` |
| `memory` | 🧠 Memory | memory | §2.3.1 Skills, memory | `what` |
| `plan` | 📋 Plan (+artifacts) | plan (+artifacts NOTE) | §2.1 | `what` |
| `project` | 📁 Project | project | §2.6 Project Mgmt | `what` |
| `automation` | ⚙️ Automation (service) | automation (service) | §2.7 Routines and Jobs | `what` |
| `demos` | 🎬 Demos | The Demos | bridge What -> Why-not | `what` |
| `not_ready` | 🚧 Why NOT ready | Why SASE is still NOT ready? | §3 Why NOT use SASE | `why_not` |
| `future_work` | 🔮 Future work | Future Work | §3.2 Future Work | `why_not` |

YAML shape (appended after `part:` in `record.fields`, order preserved;
`part` stays where it is so existing record bytes keep field order):

```yaml
    section:
      values:
        what_sase: ❓ What is SASE?
        prompt_language: ⌨️ Prompt language (macros)
        agent_turn: 🔄 Agent turn
        gate: 🚦 Gate
        families: 👪 Families, clans, tribes
        memory: 🧠 Memory
        plan: 📋 Plan (+artifacts)
        project: 📁 Project
        automation: ⚙️ Automation (service)
        demos: 🎬 Demos
        not_ready: 🚧 Why NOT ready
        future_work: 🔮 Future work
```

Deliberate omission: no `hook`, `why_use`, or `conclusion` choices.
`^section-field` names none of them; `part` already covers
`hook/why/close`. Adding them now would duplicate the coarse axis (see
critique). If full-post coverage is later wanted, add e.g. `why_use`
and `conclusion` via `choice.add` without touching existing keys.

Test case: the one existing record (`prompt_management_macros`,
`part: why`) maps cleanly to `section: prompt_language`.

## How to implement (guarded path)

1. Get the fingerprint: `bob albums list -f json` (or `bob records show
   zettel -f json`); copy the album's `schema_fingerprint`
   (`sha256:…`) as `expect`.
2. Dry-run envelope via `bob albums update sase_blog_zettel -i
   envelope.json -d`. Minimal envelope adds the field with all 12
   choices at once (`field.add` with a nonempty ordered `choices` array;
   new field is optional by default — keep it that way, step 4):
   `{"schema_version": 1, "expect": "sha256:…", "ops": [{"op":
   "field.add", "label": "Section", "choices": [{"label": "What is
   SASE?", "emoji": "❓"}, …]}]}`. Confirm the diff touches only the
   album note plus its regenerated `[!records]` callout; owner catalogs
   and record files stay byte-identical.
3. Apply without `-d`. One envelope is one gesture and one scoped
   `albums: update sase_blog_zettel (…)` commit; the verifier checks the
   schema and that the regenerated index is current. Save the returned
   `inverse_ops` for Undo.
4. Keep `section` optional (no `required: true`) until the outline
   freezes and every record is backfilled. Making it required now would
   immediately flag the existing record as invalid (`bob records check`
   reports newly invalid records; it does not migrate them).
5. Backfill: `bob records update zettel prompt_management_macros -s
   section=prompt_language -d` first, then without `-d`. Capture form is
   equivalent: `Title @sase_blog_zettel/` with `- section:: key`.
6. Validate: `bob records check zettel`, `bob albums check`,
   `bob albums sync -d` (then real sync only if stale). Do not hand-edit
   the `[!records]` callout; sync owns it.
7. Leave `index_facets: [part, claim]` and grouping (currently `status`)
   alone on day one. `index_facets` caps at three and `index_by` only
   subgroups past 12 with 2+ distinct values; with 1 record there is
   nothing to facet. Revisit the `.base` (`sase_blog_zettel.base`,
   currently `groupBy: status`) only after sections fill in — e.g. a
   second view grouped by `section` — rather than churning it now.
8. Choice lifecycle notes: `choice.add`/`choice.move`/`choice.set`
   (label/emoji) are cheap; choice key rename is refused (delete +
   re-add, which requires `count = 0`); `field.remove`/`choice.remove`
   require proof of zero usage plus a complete scan. So getting keys
   right the first time matters more than getting labels perfect.

Direct YAML edit of `sase_blog_zettel.md` also changes the allowed set
(the user's mental model is correct), but prefer the envelope: it
validates, rebuilds the index in-transaction, and returns Undo ops. A
raw edit needs a separate `bob albums sync` and skips preflight
validation.

## Other related fields: add one, decline the rest

Confident addition — `order` (number, optional):

```yaml
    order:
      values: number
      min: 1
```

Why it clears the "hard to argue it is not useful" bar: `section` alone
is an unordered bag, but a blog post is linear. Without `order` there is
no way to reconstruct intra-section sequence; the `.base` currently
sorts by title only. `min: 1` blocks 0/negatives; optional keeps the one
existing record valid; numeric storage sorts correctly in Dataview/Base.
Capture/`records update` form: `-s order=2`.

Considered but NOT recommended now:

- `subsection` free text (`suggest: true`) as an overflow valve when
  headings churn. Useful in theory, but with 1 record it is speculation;
  add it only when a section actually spawns competing subheadings.
- `anchor`/`heading` exact-text link into `sase_blog_contents.md`.
  Brittle: headings renumber (`2.3.1` today, something else tomorrow);
  the choice label plus `order` plus `claim` already locates the target.
- `placed_*` link or `target` link field. `status: placed` already
  exists; where-it-landed belongs in the `placed` workflow, not in
  pre-placement targeting.
- Priority/deadline/scheduled fields. Task machinery (`fresh`, `priority`,
  `scheduled`) lives on tasks in `sase_blog.md`, not on zettel records;
  duplicating it splits the source of truth.

## Critique: is this a good idea?

Yes, with the adjustments below — it is a good idea once, and a tax
forever.

Strengths: fixed choices give validation (`bob records check`,
capture-time refusal of typos), queryability (`WHERE section =
"gate"`, Base grouping, `index_facets`), and a shared vocabulary
between the `^section-field` plan and the zettel folder. The file-edit
mental model holds: choices live in `record.fields.section.values`.

Risks and costs:

1. Premature taxonomy. Two outlines already diverge (`^section-field`
   concepts vs `contents.md` numbered headings). Freezing 12 choices now
   bets the outline will not renumber/split (e.g. `2.3.1` vs "memory",
   "Demos" placement). Choices are cheap to add but keys cannot be
   renamed; labels can.
2. Duplication with `part`. `part` (`hook/why/what/why_not/close`)
   already partitions the post coarsely. `section` refines `what` into 9
   leaves and `why_not` into 2. Every write must keep `part` and
   `section` consistent, and nothing enforces cross-field consistency
   (schema validates per-field only). Document the mapping table above
   in the album or a comment-adjacent note; do not automate it.
3. Maintenance friction per new subsection. Each genuinely new section
   needs a `choice.add` envelope (fingerprint, dry-run, commit, index
   rebuild). With a live outline that is correct but heavy; a
   `suggest`-text field would have zero friction.
4. Single-record reality. With 1 zettel, facets/views/grouping buy
   nothing today. The value is future assembly (`section` + `order` ->
   draft order), not current browsing.
5. `required` trap. Required on day one invalidates the existing record
   and every quick capture that omits it. Optional-first is the only
   safe start.
6. Granularity ambiguity. "Section" could mean top-level (§2), numbered
   (§2.3.1), or `^section-field` leaf (memory). This report pins it to
   the `^section-field` leaf per the request; say so in the album
   (`summary` or a comment) so a later reader does not reinterpret it as
   `contents.md` numbers.

Alternatives considered:

- A. `part`-only + search until the outline freezes, then add
  `section`. Zero schema churn now; loses validation/grouping in the
  interim. Reasonable if the outline moves weekly.
- B. Free-text `section` with `suggest: true` instead of choices.
  Suggestions emerge from usage; promote to choices later. Lowest
  friction, but no refusal of typos and weaker Base grouping.
- C. Coarse choices (4–5: `why/what/demos/not_ready/future`) +
  free-text `subsection`. Fewer choices, less churn, but re-duplicates
  `part` almost exactly — rejected.
- D. Link field to `sase_blog_contents.md` headings. Precise but
  brittle across renames; Dataview links to headings drift.

## Adjustments to the requirements (explicit)

1. Base values strictly on `^section-field` leaves (12 keys above), not
   on `contents.md` numbers. Note the `contents.md` mapping separately
   rather than merging the two outlines into one choice list.
2. `section` optional at creation; flip to `required` only after
   backfill + outline freeze. (Request did not specify requiredness.)
3. Add `order` (`values: number`, `min: 1`, optional) alongside
   `section`. (Request invited objectively useful extras; this is the
   one that qualifies.)
4. Do not add `subsection`/`anchor`/`placed_*`/priority now; add on
   evidence, not speculation.
5. Do not change `part`, `status`, `index_facets`, `index_by`, or the
   `.base` views in the same change. One schema change, one commit,
   one review.

## Recommended solution

Implement optional choices-`section` (12 keys above) plus optional
numeric `order`, via one `bob albums update` envelope with dry-run,
backfill the single existing record to `section=prompt_language` (plus
an `order` if known), validate with `bob records check` + `bob albums
check`, and leave facets/Base/grouping untouched until the folder grows.
Document the `section`-is-`^section-field`-leaf rule and the
`part`-to-`section` mapping where Bryan will see it when writing, and
promote `section` to required only once every record has one and the
outline stops moving.

# Parent-scoped link walks and bottom-of-card navigation

Independent research by **cdx**, 2026-11-27.

## Recommendation in brief

This is a good addition: sibling navigation supplies the missing horizontal movement beside the hierarchy's parent links and child catalogs. Implement it as an extension of the existing **n link-walk family**, using one read-only destination resolver for keys, card controls, repeats, and the status-bar footer.

For the four new note types, make **`]n` / `[n` a circular walk of the same type under the same immediate parent**. Implement **`]N` / `[N` as a jump between occupied neighboring parents under the same grandparent**, landing on the first same-type child of the destination parent. This keeps group jumps local and repeatable. Explain an unavailable group jump rather than expanding its scope implicitly.

Put every card-mounted link-walk rail in a shared, final navigation slot **after the entire cabinet stack**, including Properties and Prose Outline. Properties remains the last *cabinet*; navigation becomes the last *card region*. This distinction resolves the apparent conflict with the cabinets design.

Most implementation can proceed alongside `bob-cli-qq`. The destination model is independent of cabinets. Only shared card assembly, cabinet go-live edits, and deployment need narrow coordination. Do not make the entire feature wait for that epic to close.

## What I verified

Research used the local bob-cli checkout at `eff5d986678801e3466622aafa64e70c950f07a2`, and bob-plugins opened through `sase repo open`, at `4dd95d525cd12f80c91a3981cb1a3911dbb47d02`. Bead status is a time-sensitive observation from this investigation. I read the two cabinets plans through audited artifact reads and consulted the decisions roster and relevant glossary strands. I did not read or request any other researcher's report, findings, or conversation.

The relevant existing behavior is more capable than a new implementation might assume:

- Navigation's `resolveNavLinks` combines authored destinations with Ledger Tools' `api.navGroups.resolve`. Authored links win **per direction/role**, and distinct authored group targets in one role produce an explicit conflict. `api.walkMode.links` v7 exposes that same answer. Existing clients already handle step stops, group stops, wrap markers, missing targets, and group explanations. [S1–S3]
- `[N` and `]N` already mean the **head of the adjacent group**, in either direction. `]]` / `[[` repeat lowercase movement; `]}` / `[{` repeat uppercase movement. Link-family counts are ignored. Successful group movement records a Vim jump. [S1–S2]
- The current Ledger provider handles calendar notes and grouped records. Extending its routing is a substantially smaller change than implementing another navigation controller. Its contract is synchronous, read-only, and never spawns bob. [S4]
- The card group-row kit already supplies group arms, a position display, missing-target states, wrap indicators, narrow layouts, forced-color styles, and reduced-motion support. Reuse its visual language. [S5]
- The requested bottom placement is a real change. Temporal cards append their rail and then their foot; record cards do the same and explicitly document that order. Cabinet assembly then appends its stack to the card. An isolated CSS adjustment would leave several mounting paths inconsistent. [S6–S8]
- `homeCardWalkAncestry` is a presentation helper, not a universal hierarchy validator. It stops at non-area/project kinds and has its own display-depth limit. `homeCardResolveParent` likewise accepts only areas/projects, and `notebookResolveLinkFile` can return a guessed path. These helpers cannot simply become the authoritative sibling-group index. [S9]

I ran these existing bob-plugins suites without changing source:

| Suite | Result |
| --- | --- |
| `scripts/test-navigation-group-links.cjs` | 48 passed |
| `scripts/test-ledger-tools-nav-groups.cjs` | 12 passed |
| `scripts/test-ledger-tools-property-card-group-row.cjs` | 15 passed |

These 67 passing tests validate the existing extension points and behaviors, not the proposed feature. I did not run a new implementation, a full plugin validation, a real-Obsidian smoke, or a live-vault membership census.

## Critique and explicit requirement adjustments

The feature makes sense if it remains navigation. It should not become a second review queue, a completion indicator, a project-status filter, or a writer of generated navigation links into authored prose.

There is one logical ambiguity in the request: a walk restricted to a single parent has only one parent group. Meaningful uppercase movement therefore requires a deliberately broader scope. The following are my proposed resolutions, not claims that the original request already specified them.

| Requirement or ambiguity | Recommended resolution |
| --- | --- |
| “Only notes of the same type that share the same parent” | Applies strictly to **derived lowercase movement**. Uppercase explicitly changes the parent, within the same grandparent. |
| Which parents can `]N` visit? | Only existing parents that are siblings of the current parent and have at least one eligible child of the current note's type. No vault-wide traversal and no automatic ascent. |
| “Alphabetically” | Use the note's displayed card title, case-insensitively, with canonical path as the deterministic tie-breaker. Use the existing species title rule; a filename is the fallback. This is an explicit preference for visible labels over raw filenames. |
| Existing authored `prev`/`next` or group links | Preserve their current per-role precedence. Thus authored navigation is an explicit exception to the inferred sibling rule. Show an authored-navigation state when it overrides the derived route. |
| Which project statuses participate? | Include existing, valid project notes of every lifecycle status outside the normal excluded/archive paths. `root: true`, task freshness, task hiding, and cabinet fold state do not change membership. |
| “Always shown at the very bottom” | Whenever the supported card mounts, its rail is last and outside all collapsible sections. It can show a singleton or an unavailable state. Existing Source/unsupported-surface fallbacks remain intact; this is not a request to force card takeover everywhere. |
| Missing parent | No invented “Unparented” group and no auto-creation. Explain the missing/invalid parent; authored navigation can still work. |
| Glossary addition | Adopt the proposed **Link Walk** definition with the implementation, rather than recording an unimplemented contract as current behavior during research. |

The sorting choice deserves awareness: notebook catalogs already sort by display title, while project catalogs sort open children by filename and closed children by closure date. There is no existing cross-species ordering to inherit unchanged. I prefer one visible-title rule for these new walks, with a tooltip saying “Title A–Z · wraps within this parent.” If exact filename ordering is important to Bryan, change this one comparator and label before implementation; the group design is unaffected. [S10–S11]

Preserving authored navigation also requires an honest UI. A rail must never display “next sibling Baz” while `]n` follows an authored link to another note. Use the *resolved* answer for all arms. If an authored override changes the derived route, label it “Authored navigation” and omit the inferred position track unless it can still accurately describe the effective route. This compatibility exception should be documented, not hidden behind implementation details.

## The proposed walk, precisely

Let `kind(x)` be a note's canonical primary type and `parent(x)` its uniquely resolved immediate parent note. Canonicalize legacy `article` to `prose`. Identity is a vault-relative file path, not a label, basename, alias, folder, H1, task root, or rendered breadcrumb.

For current note `x`, let `T = kind(x)` and `P = parent(x)`:

```text
siblings(T, P) = eligible notes y where kind(y) = T and parent(y) = P
```

Sort this list by the chosen title comparator. Lowercase keys step one member, wrapping inside this list. On a singleton, show `1 / 1 · Only project under Foo`, with inert step arms; pressing a key explains the singleton without reopening the same file or adding a jump-history entry.

If `G = parent(P)` is a valid resolved note, define:

```text
parents(T, G) = parent notes Q where parent(Q) = G
               and siblings(T, Q) is nonempty
```

Sort these parent groups by their own display titles, then canonical paths. Uppercase keys select the preceding/following group and open its **first** member, even when moving backward. Wrap across occupied groups. Empty parents are skipped; singleton groups remain valid. A single occupied parent gives no uppercase destination, even when the current note is not the first sibling.

The candidate parents need not have the same type as each other: they must be valid parents for `T`. For example, an area can contain a child area and a project, both of which may host project notes. The grouping noun is **parent**, so it would be misleading to silently add a same-parent-type filter. Every destination note still has type `T`.

This rule has a useful stability property: after jumping from a child of `P` to a child of `Q`, the new parent's parent is still `G`. Repeated `]N` visits the same set of groups without remembering where the walk began. It needs no global navigation session or hidden pinned scope.

### Worked example

Assume these titles agree with their filenames:

```text
pig (area)
├── foo (project)
│   ├── bar (project)
│   └── baz (project)
├── goo (project)
│   ├── alpha (project)
│   └── beta (project)
└── zoo (project; no project children)
```

| Starting note | Gesture | Result |
| --- | --- | --- |
| `bar` | `]n` | `baz` |
| `baz` | `]n` | `bar`, wrapping within `foo` |
| `bar` | `[n` | `baz`, wrapping within `foo` |
| `bar` or `baz` | `]N` | `alpha`, first project under `goo` |
| `beta` | `[N` | `bar`, first project under `foo` |
| `alpha` | `]N` | `bar`, wrapping parent groups; `zoo` is empty and skipped |
| `foo` | `]n` | `goo`; this is a different sibling list under `pig` |

Changing `foo` to `root: true` does not change any of these destinations. That property governs reporting roots, not immediate ownership. The definition of Root Parent is distinct from an immediate parent or a top-level area.

For top-level areas, `P` is the area-root sentinel. Its own parent is deliberately not followed. Lowercase walks the top-level areas; uppercase explains “Top-level areas share one parent.” This is a useful boundary rather than a missing feature. The root sentinel can be untyped and is never itself an area-walk member. [S12]

For notebooks, `P` may itself be a notebook. Keep that immediate parent instead of flattening through to the nearest area/project owner. For prose, a valid explicit parent suffices for sibling navigation; do not introduce a new rule that all prose must belong to an area or project. If the parent's parent is absent, lowercase still works and uppercase explains that neighboring parent groups are unavailable.

### Why this grouping beats the alternatives

| Alternative | Benefit | Reason not to choose it now |
| --- | --- | --- |
| One vault-wide same-type walk grouped by parent; lowercase crosses groups | Familiar flattened grouped list | Violates the requested same-parent lowercase boundary. |
| Local lowercase, vault-wide uppercase | Every parent group is reachable | Nested projects make surprising jumps possible: a subproject's next group can contain its own parent project. Repeated uppercase can roam across unrelated areas. |
| Group by reporting root or top-level area | Broad and often populated | Merges distinct immediate parents, inherits reporting semantics, and makes `root: true` affect navigation. |
| Neighboring parents under the same grandparent | Local, deterministic, no remembered scope | Sparse branches sometimes have no uppercase destination; accept and explain this limitation. **Recommended.** |
| Uppercase opens the parent itself | Simple vertical movement | Changes note type when the parent differs, duplicates breadcrumbs, and abandons “group head” semantics. |
| Remember the last visited child of each parent | Returns to recent context | Makes a supposedly alphabetical walk history-dependent and loses predictable group-head behavior. |
| Lowercase only | Smallest change | Sound fallback if broader movement is rejected, but the local neighboring-parent rule is sufficiently clear to ship. |

The main cost of the recommendation is that uppercase no longer offers an exhaustive tour of every note of a type. That is intentional: a global library tour belongs in an explicit index/search view, not an unstated expansion of a local hierarchy walk.

## Eligibility, failure states, and change handling

1. **Primary role first.** An area or project containing prose remains that type. Legacy `article` participates as prose. Reject ambiguous/mixed classifications rather than allow one note to join two kinds. Keep the path-canonical bank hub and taxonomy/template/generated/conflict/archive exclusions out of these rings. Use established species eligibility and strengthen only what navigation identity requires. Governing decisions: `decisions:prose-notes-are-owned-prose`, `decisions:bank-hub-is-path-canonical-never-area`.
2. **One real parent.** Resolve a scalar parent link to one existing Markdown note, handling supported alias/path/heading forms by file identity. A link's display alias never supplies group identity; heading/block parts do not create separate parent groups. Duplicate keys, lists, ambiguous basenames, self-links, and unresolved targets produce explicit unavailable reasons. Prefer the existing catalog identity contract: exact path, then unique case-insensitive basename, with fixtures for every accepted form. Do not silently take an arbitrary first match. [S11–S12]
3. **Respect species rules.** Areas accept an area or the area sentinel; projects accept the established area/project parents; notebooks follow their existing owner/cycle requirements. Prose has no newly imposed owner requirement. Do not use a truncated visual breadcrumb as proof of graph validity. Distinguish “valid local group but unknown grandparent” from “no valid local parent.”
4. **Cycles are explicit.** Refuse self-parent and cycle-member edges. Do not unnecessarily suppress a valid area/project sibling group merely because an ancestor farther up is malformed: the Area contract deliberately retains valid children below a bad ancestor. Notebook chain validity remains stricter. A broken grandparent disables group movement without necessarily disabling siblings. [S10–S12]
5. **Existing means existing at activation.** Derived sibling/group navigation never creates notes. Revalidate both membership and destination immediately before opening, and use an existing-file open path. The current generic open-or-create controller needs a specific existing-only policy for these derived stops so deletion after preview cannot cause accidental recreation. This does not change calendar creation rules or authored links.
6. **Change events matter.** Rebuild affected memberships after file creation/deletion/rename, parent/type changes, display-title changes, and metadata settlement. A parent rename can affect groups even when the current child's text did not change. A reparent moves the child between groups atomically; no node should appear twice during refresh.
7. **Unavailable is not empty.** Loading/indexing, invalid parent, missing target, singleton, and no neighboring parent groups need different state text. Never report `0 notes` while metadata is incomplete. If the current buffer's parent/type differs from settled cache, derive from a validated current-source overlay or withhold stale navigation until settlement.
8. **No status filtering.** A closed project is still a project note. Including it keeps file navigation stable when tasks close and follows the user's type/parent rule. Existing archived files under `done/` stay outside active note eligibility. If closed-project browsing becomes noisy, design an explicit filter separately instead of silently importing the task queue's predicates.

## Implementation shape

### Extend the existing resolver

Keep this initially in **bob-plugins**, with a pure parent-walk model and a small cached index owned by Ledger Tools. There is no demonstrated need for a new CLI command, persistent vault field, sync pass, or Rust JSON contract.

The flow should be:

```text
settled metadata + confirmed title/source data + current source overlay
    → immutable note/parent index generation
    → pure sibling and neighboring-parent model
    → api.navGroups.resolve
    → Navigation resolveNavLinks (authored precedence)
    → keys / repeats / card rail / status-bar links footer
```

Add a new provider route before the calendar fallback, preserving record behavior. Reuse the existing stop/group shapes: canonical path, rendered label, kind, group label, members, position/size, group index/count, wrap flag, and explicit none reason. Add an existing-only navigation policy for these stops. If consumers need to detect the new route or fields, use additive capability/version detection; do not require an unrelated top-level API change.

A local immutable generation is enough initially. Build from cached metadata outside paint, debounce bursts, and index by canonical kind and parent path. Cache title inputs rather than reading every sibling body on each paint. Rebuild the full metadata-derived map on relevant changes first if profiling shows it comfortably fits; incremental reverse-dependency machinery can follow actual evidence. Both card and key execution must reference the same resolver and generation, with execution revalidation.

Existing resolved links should keep working without Ledger Tools, as they do today. Derived hierarchy navigation can give a clear provider-unavailable message. A failure to paint a card must not disable keyboard movement.

There is a genuine authority tradeoff: a plugin index must match Bob's parent semantics. Avoid copying whichever presentation helper happens to be closest. Use shared conformance fixtures taken from area/project/notebook parent cases, plus explicit prose cases. If that cannot be achieved without duplicating substantial graph logic, the fallback is an authoritative read-only Bob report consumed by the existing report-cache infrastructure. That increases scope, requires release-train compatibility, and is not the first choice without evidence. Do not spawn it from card painting.

### One final card slot

Create an explicit card navigation slot/helper. Its invariant should be:

```text
card identity/details
cabinet stack (content → config → Properties)
link-walk navigation
```

All card assembly paths append or insert ordinary content before the navigation slot; cabinet assembly inserts its stack before that slot if it already exists. The navigation slot is outside the details fold, cabinet bodies, and their inert/hidden subtrees. Retain an idempotent finalization step for deferred/Reading mounts so a later rail or stack cannot reverse the ordering.

Migrate the **existing temporal and record rails** to this slot while adding Area, Project, Notebook, and Prose adapters. Audit both the common `propertyCardFootAdapterAppend` and record's direct foot builder, plus the Reading path that attaches the record rail later. Do not create another rail for cards that do not currently have a link walk, such as the bank card's bank-row workflow.

Avoid a MutationObserver that repeatedly moves nodes, and avoid solving this solely with flex `order`: logical DOM/focus order should follow the intended card structure. W3C's focus-order guidance supports preserving meaningful keyboard order and warns that a mismatch with visual order can confuse users. This is design guidance, not a claim that the existing card currently fails accessibility. [W1]

### A quiet, useful rail

A wide project card could end like this; labels are illustrative:

```text
▸ Projects                         2
▸ Notebooks                        3
▸ Properties                       7                  -
────────────────────────────────────────────────────────
  ‹ Baz             PROJECTS · Foo · 1 / 2        Baz ›
  « Previous parent       within Pig          Goo »
```

In a two-member ring, both step arms legitimately name the same other note. With three or more members they differ. For the example's two occupied parent groups, both group directions likewise reach Goo; their tooltips distinguish direction and wrap.

- Reuse the existing three-column rail and group-row kit, with its single-step and double-step icon language. Reuse card hue tokens and quiet separators; keep type and parent readable without color.
- The step row answers **where next and among what**: destination labels, type, parent, and current ordinal. The parent label opens that parent directly; it is distinct from group movement.
- The group row names destination **parents**, not the child it will open. Tooltip/accessibility text makes the landing explicit: `]N · Next parent: Goo → Alpha · within Pig`. Keep the local scope visible at least once; do not make users infer it from a distant breadcrumb.
- Position is membership, not completion. Use restrained ticks or a position thumb from the existing kit; no success-green progress meter. On a singleton, keep useful `1 / 1` context even if the kit omits its decorative track.
- At narrow widths, retain the current parent and controls, shorten labels, and put full title/path/scope in tooltips. Two compact rows are clearer than cramming four small arrow buttons around a long path.
- Keep hover previews and existing modified-click behavior where available. Plain clicks resolve again and execute in the card's own pane, matching the key and preserving jump history.
- Supply visible focus, descriptive accessible names, and generously clickable arms. Target at least 24 × 24 CSS pixels without depending on an exception; WCAG 2.2's target-size guidance permits spacing/equivalent-control exceptions, but a navigation rail can reasonably meet the size directly. [W2]
- No pulsing, automatic scrolling on metadata refresh, or layout movement merely because another walk family becomes selected. The card rail is local navigation and remains present regardless of the status-bar family's selection.

This does not replace the **Walker Footer**, which is the status-bar panel. Cabinet picking can continue to temporarily overlay that panel. The new card rail is not a cabinet, gets no `_` number, and never changes cabinet numbering or fold state.

## Parallel work with bob-cli-qq

### Observed active work

At inspection, `bob-cli-qq.1`–`.7` were closed; `.8` acceptance and `.9` go-live remained in progress. The active finishing epic `bob-cli-qq.10` divides the remaining work as follows:

| Work | Observed state | Relevance |
| --- | --- | --- |
| `.10.1` Reading performance | In progress | Profiles `240c`, `240wl`, `240wj`, `240wh`; a new per-render scan could invalidate the budget. |
| `.10.2` Reading card miss | Closed | Shared host fix; rebase onto the landed result, do not redesign host mounting independently. |
| `.10.3` overlay/polish | Closed | Footer overlay and narrow CSS work; preserve it. |
| `.10.4` acceptance | In progress | New layout needs its own combined acceptance; don't change the cabinets runner's verdict criteria opportunistically. |
| `.10.5` gate deletion/deploy | In progress | Removes gate calls in `240r`, `240wl`, `242kc`, and other exact integration points. |
| `.10.6` docs/memory | In progress | Edits shared card descriptions and glossary strands. |

The original cabinets plan explicitly makes Properties the last cabinet and implements passive, render-time absorption of catalogs. The finishing plan leaves that contract in force. Neither requires navigation to be above the stack forever. Still, “stack at the bottom” wording should become “below details, above navigation” when both changes land. [Q1–Q2]

### Minimum coordination that is actually needed

**Do not add a dependency on the entire `bob-cli-qq` epic.** Much of this feature has no cabinet dependency. Coordinate ownership and the small merge boundary:

1. **Develop the model and navigation route immediately**, mostly in new source fragments and new tests. Use fixtures that cover both current and final cabinet shapes, but do not read cabinet DOM to compute membership.
2. **Agree one shared assembly contract** with the cabinets implementer/lander before landing: navigation is the last card region; Properties remains last inside the cabinet stack; picking ignores navigation; repaint and fail-open preserve the final slot. This can be a short recorded contract, not a redesign meeting.
3. **Have one owner land the integration hunk** in `240r`, `240wl`, and `242kc`. If `.10.5` is still deleting gates there, either let it land first and rebase the small navigation-slot patch, or have its owner integrate the agreed helper. Only that landing step needs ordering. Recheck status before scheduling; the observed states will age.
4. **Separate source regions.** New parent-walk fragments, rail adapters, and CSS region are ours; cabinet body rendering, absorption, pick state, and acceptance fixes remain qq's. Rebuild generated `main.js` from reconciled fragments instead of resolving generated output by hand. Preserve the fragment size limit.
5. **Merge docs and memory last.** Draft the new Link Walk strand independently. Let qq land its approved cabinet/property-card edits, then make any required cross-link or wording correction against that result. Do not rewrite those strands from an older snapshot or broaden qq's approved memory scope.
6. **Serialize deployment**, not development. Validate the integrated tree and deploy from the updated linked checkout with `bob plugins sync`. Follow the repository's guarded deployment workflow if another build is deployed. Do not force an overwrite of a live peer build. Keep cabinet acceptance evidence attributable to its own tree.

For implementation parallelism within this feature, split into **model/resolver + navigation execution**, **rail + final-slot integration**, and **fixtures/docs/acceptance** after agreeing the destination shape. Do not assign one worker per note type: four separate sibling algorithms and rail styles would duplicate precisely the logic that must agree. A modest two-engineer implementation plus an integration owner is likely more effective than a large swarm.

No coordination messages, bead dependencies, or changes to qq were made during this research. Those are implementation-stage actions, after the lead selects a design.

## Verification and acceptance criteria

The useful tests assert behavior, not copies of the implementation:

- The exact `pig → foo → bar/baz` example, including reverse movement and wrap; another parent with matching children; empty and singleton parent groups; both group keys land at the first member.
- Same-type/same-immediate-parent invariants for every lowercase target; same-grandparent and same-child-type invariants for every uppercase target. Repeated uppercase must keep the group universe stable.
- Nested notebooks, direct projects under areas, subprojects, prose with legacy `article`, root sentinel, path aliases and duplicate basenames. Test same-label notes with different paths and different labels resolving to one parent.
- Missing/list/duplicate/self/cyclic parents, invalid notebook chains, parent without grandparent, and partial metadata. Local siblings remain available when only the broader group scope is unavailable.
- Closed/canceled/root-marked project membership; ordinary excluded paths; bank hub and taxonomy notes excluded. No dependence on catalog presence, cabinet open state, or status-bar family.
- Authored precedence, conflicts, mixed authored/derived roles, title changes, and an override outside the sibling group. Card arms, status footer, keys, and repeats must resolve to the same destination.
- Rename/reparent/delete between preview and click; no auto-creation and no stale note reopening. Counts and controls update together. Source/cache disagreement must not expose a plausible but stale destination.
- One navigation slot, after every cabinet, in Reading and Live Preview; record and temporal regressions; open/closed Properties and Outline; collapsed details; deferred remount; no duplicate listeners or jump entries.
- Real Obsidian, two panes, wide and 420px views, light/dark themes, keyboard focus, hover, modified clicks, `]n`, `[n`, `]N`, `[N`, `]]`, `[[`, `]}`, `[{`, and Vim `<C-o>`. Cabinet picking must retain its overlay, numbers, cancel behavior, and focus handling.
- Passive-operation spies: zero vault writes and zero bob spawns from index projection, paint, key navigation, and clicks on these derived destinations. Collect `console.error` as well as uncaught exceptions; qq's existing notes document why exception-only collection missed a CodeMirror failure.
- Profile a representative large metadata fixture. Record index rebuild cost, paint cost, and key-to-open latency separately. Do not add a fresh whole-vault/body scan to every card repaint, and recheck the cabinets Reading performance budget on the integrated tree.

Run the plugin build, generated-build check, relevant new and existing navigation/card/cabinet suites, and the required repo validation. A screenshot review in the real app is required to establish that the design is beautiful; code inspection alone cannot prove that.

## Proposed glossary entry

Proposed strand: `glossary:link-walk`, title **Link Walk**, aliases **note walk**, **n walk**. The user explicitly requested this addition. The SASE memory-write workflow should be followed when adopting it with the feature; this report supplies wording rather than editing canonical memory ahead of implementation.

> A **Link Walk** is Bob's `n` navigation family: `[n` and `]n` move between a note's ordered previous and next destinations; `[N` and `]N` jump to the first note of the previous and next group when that note kind defines groups. It chooses destinations from authored navigation links first, then from the note kind's derived rules. It is not a traversal of every backlink, a task review queue, or a history of visited notes.
>
> For an [[area-note]], [[project-note]], [[notebook]], or [[prose-note]], the derived step walk circles notes of the same type under the same immediate parent, ordered by displayed title. Its derived group walk visits occupied neighboring parents under the same grandparent, keeping the child type unchanged. A parent without neighboring groups still has its sibling walk. Legacy article notes count as prose; reporting roots do not change membership. Existing day, period, and record walks retain their own membership and grouping rules.
>
> The navigation rail at the bottom of a [[property-card]] and the links panel of the [[walker-footer]] explain the same destinations the keys will use. Position means membership, not completion. `]]` / `[[` repeat the selected family's step; `]}` / `[{` repeat its group jump. Derived hierarchy navigation opens existing notes and never creates or rewrites them; existing explicit calendar creation rules are separate. Details and exceptions belong in the navigation documentation.

The term should remain a conceptual definition, not absorb the entire resolver schema or invalid-parent checklist. The longer behavioral contract belongs in plugin navigation docs.

## Evidence and governing context

All repository files below were read from authorized local checkouts. Links are pinned to the investigated revisions where applicable.

- **S1:** [Navigation documentation, bracket walks](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/docs/bob-navigation-hotkeys.md#L525).
- **S2:** [Shared authored/derived resolver and group execution](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-navigation-hotkeys/src/483-nav-group-links.js).
- **S3:** [walkMode v7 API](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-navigation-hotkeys/src/482-walk-mode-nav-api.js).
- **S4:** [Ledger navGroups provider routing](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/296f-plugin-nav-groups-api.js), [record groups](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/296g-plugin-nav-groups-records.js).
- **S5:** [Property-card group row](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/240l-plugin-property-card-group-row.js), [its tests](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/scripts/test-ledger-tools-property-card-group-row.cjs).
- **S6:** [Temporal card assembly](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/296b-plugin-intention-card-dom.js#L369), [record card assembly](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/242k-plugin-record-sheet.js#L666).
- **S7:** [Shared foot adapter](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/240r-plugin-property-card-foot-adapter.js#L310), [record direct foot](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/242kc-plugin-record-sheet-foot.js#L191).
- **S8:** [Cabinet assembly](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/240wl-plugin-cabinet-stack.js), [late record Reading rail](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/242v-plugin-record-walk-rail.js#L117).
- **S9:** [Home ancestry presentation model](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/249b-plugin-home-card-model.js#L227), [home parent resolution](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/249d-plugin-home-card-host.js#L239), [notebook path fallback](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/241b-plugin-notebook-catalog-model.js#L429).
- **S10:** [Notebook identity, title, parent, and catalog rules](https://github.com/bobs-org/bob-cli/blob/eff5d986678801e3466622aafa64e70c950f07a2/docs/notebooks.md).
- **S11:** [Projects and direct-child catalog rules](https://github.com/bobs-org/bob-cli/blob/eff5d986678801e3466622aafa64e70c950f07a2/docs/projects.md#L295).
- **S12:** [Areas, root sentinel, and invalid edges](https://github.com/bobs-org/bob-cli/blob/eff5d986678801e3466622aafa64e70c950f07a2/docs/areas.md).
- **S13:** [Prose role and permanent article compatibility](https://github.com/bobs-org/bob-cli/blob/eff5d986678801e3466622aafa64e70c950f07a2/docs/prose.md), [card species classifier](https://github.com/bobs-org/bob-plugins/blob/4dd95d525cd12f80c91a3981cb1a3911dbb47d02/plugins/bob-ledger-tools/src/240t-plugin-property-card-note-species.js#L188).
- **Q1:** Audited `bead:bob-cli-qq` and `plan:202611/property_card_cabinets.md`: approved cabinet stack, passive rendering, properties-last semantics, source ownership, and memory scope.
- **Q2:** Audited `bead:bob-cli-qq.10` and `plan:202611/finish_property_card_cabinets.md`: current performance/Reading/acceptance/gate-deletion/docs work and exact overlapping files.
- **M:** Audited decisions roster plus `decisions:prose-notes-are-owned-prose`, `decisions:notebook-routes-write-notes`, `decisions:bank-hub-is-path-canonical-never-area`, and `decisions:bob-cli-releases-ride-a-daily-train`; relevant note/card/root/footer glossary strands. `decisions:notebook-routes-write-notes` reinforces leaving authored note bodies and bob-owned catalog content alone. No new release or CLI contract is needed for the recommended plugin implementation.
- **W1:** [W3C: Understanding Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html), consulted 2026-11-27.
- **W2:** [W3C: Understanding Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), consulted 2026-11-27.

## Recommended solution

Implement a **shared, derived sibling walk** for Area, Project, Notebook, and Prose notes. Lowercase cycles same-type children of one immediate parent; uppercase jumps to the first same-type child of an occupied neighboring parent under the same grandparent. Keep authored navigation precedence explicit, preserve all project statuses, and treat invalid/missing graph data as an explained state rather than an invented route.

Render that same resolved navigation in a **final card slot beneath all cabinets**, moving existing temporal and record rails there too. Reuse the group-row kit and status-footer resolver, publish the Link Walk glossary term with the feature, and validate the result in real Obsidian. Develop the model and UI in parallel with cabinets; coordinate only the small shared assembly patch, final docs/memory reconciliation, and deployment. This yields a predictable local walk without adding vault mutations, a second navigation engine, or a dependency on the whole cabinets epic.

# Alphabetical record navigation: a durable album compass

Independent research by **cdx**, 2026-11-18. This is a design recommendation, not an implementation or an accepted architecture decision. No peer reports, peer transcripts, or peer findings were consulted.

**Recommendation:** give each record one compact, Bob-owned Markdown navigation strip containing named previous/next links and its `N of M` position. Compute all three from one deterministic album roster. Maintain the strip through the existing album transaction machinery, render it as a quiet row in the record sheet, and route `[n` / `]n` through a shared managed-link resolver that opens existing records only.

The idea is good. It makes casual browsing much easier without turning records into tasks or introducing another keyboard family. Its main costs are generated-file churn and synchronization complexity—not sorting. A purely visual widget would be cheaper to write but would lose the durable links the request asks for.

## Evidence and current behavior

I inspected bob-cli at `2f80442bb2c3141b69131c6db7786516fa165ca0` and the linked bob-plugins checkout at `04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c`. The relevant sources were read locally through the required repository workflow. I also ran a small, read-only experiment against the existing navigation implementation and a read-only album inventory with installed `bob 0.5.0`. No vault notes or implementation files were changed.

The inventory returned `ok: true`, six albums, 192 records, and zero report-level errors or warnings. All six generated album indexes were current:

| Album | Records |
| --- | ---: |
| eat | 104 |
| movies | 12 |
| podcasts | 15 |
| sase_blog_zettel | 10 |
| subscriptions | 28 |
| tv | 23 |

These are a local snapshot, not a performance benchmark or a promise about other hosts. The installed binary may differ from the inspected source revision.

Several implementation facts constrain the design:

1. **Album membership is structural.** Albums own their immediate Markdown children. Existing inventory deliberately retains invalid members and reports their problems; it does not silently lose records with a bad status. Nested descendants are outside the album. This is important for deciding what `M` means. [Album/record contract](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/docs/records.md), [catalog implementation](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/records/catalog.rs).
2. **The album's displayed index is not a global alphabetical list.** It groups by status or another choices field, sometimes subdivides by `index_by`, and sorts titles within those groups. The existing title comparator uses lowercase title and then path. Flattening the rendered index would therefore violate the requested alphabetical walk. [Grouping and comparator](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/albums/grouping.rs#L101).
3. **The keyboard grammar already supports the desired labels.** Previous matches labels beginning with `<` or `‹`; next matches labels beginning or ending with `>` or `›`. The parser reads body links, skips frontmatter and fenced examples, and returns the first matching link. Saving `prev:` and `next:` only in YAML would not work with today's commands. [Matcher](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-navigation-hotkeys/src/680-plugin-link-parse.js#L1), [body traversal](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js#L794).
4. **Existing link navigation can create a missing destination.** `openLabeledBodyLink` calls the open-or-create path. That is useful elsewhere, but a stale generated record neighbor must not recreate a deleted restaurant or subscription. [Command](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-navigation-hotkeys/src/670-plugin-project-files.js#L151), [open/create dispatch](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-navigation-hotkeys/src/640-plugin-notes-and-task-move.js#L314).
5. **The existing links footer shares the command's parser.** `api.walkMode.links({path, content})` previews the same links; the footer exposes destinations and currently distinguishes missing links that can be created. A change only to the keyboard command would leave the footer misleading. [Preview API](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-navigation-hotkeys/src/482-walk-mode-nav-api.js), [links footer](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-ledger-tools/src/124-links-walker-footer.js).
6. **There is already a good visual home.** The current linked plugin renders a record sheet with the title, breadcrumb, fields, and collapse control. It supports records without an H1, including frontmatter-only notes. Healthy desktop sheets hide native Properties and the filename-derived inline title. The mirrored bob-cli Record Card documentation lags that source; implementation should follow the linked plugin's current contract. [Current Record Card documentation](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/docs/record-card.md), [sheet host](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-ledger-tools/src/242k-plugin-record-sheet.js).
7. **Bob already owns derived album writes.** Album sync guards declarations, member frontmatter, and directory membership. Capture and record commands overlay staged record postimages before rebuilding the album index. These are the extension points; a second plugin writer would duplicate an existing authority. [Sync planner](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/albums/sync.rs#L208), [shared write projection](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/albums/write.rs), [capture integration](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/capture/record_note.rs#L412).

The parser experiment used the repository's navigation harness, with no file writes:

| Body input | Observed previous / next |
| --- | --- |
| Bare `<` and `>` aliases | Correct two destinations |
| `‹ Alpha` and `Zeta ›` aliases | Correct two destinations |
| Both arrows targeting `eat/other` | Both correctly target that same record |
| Named links inside a `[!record-nav]` callout | Correct two destinations |
| An unrelated `‹ Detour` link before that callout | Previous incorrectly selects the detour for the proposed album use |
| Decoy links in YAML and a code fence | Decoys ignored |

This proves basic syntax compatibility and the need for managed-region precedence. It does not prove future rendering, transactions, or accessibility.

## Is this the right kind of navigation?

Yes, as an **album browsing affordance**. It is especially useful when opening a record directly and wanting to explore nearby entries without returning to a large index. A deterministic ring has no dead end and works naturally with the existing bracket-repeat family.

It should not imply that the user is reviewing a queue, completing a collection, or traversing the visible status group. `42 of 104` means position in a title-ordered collection. It says nothing about records visited. Do not add a progress bar, completion coloring, visited-state persistence, or review reminders.

Alphabetical adjacency is less meaningful for some collections, including chronological notes or a series whose order lives in a field. Nevertheless, automatic per-album sort inference would make the same key unpredictable. Honor the requested global title order for this feature. A future explicit album sort policy can be considered separately; do not start with configurable comparators, filters, session walks, and custom ordering.

The grouped album index should remain useful as it is. Label this distinct walk `A–Z`, and keep the album breadcrumb as the way back to the overview. Clicking a record in a filtered or grouped album view should still enter the same global walk. If a future “walk this result set” feature is wanted, it needs a separately visible scope.

## Options and tradeoffs

| Approach | Strength | Main problem | Judgment |
| --- | --- | --- | --- |
| Compute everything in the plugin | No generated note churn; immediate local response | No durable links; desktop/mobile/cache differences; another ordering implementation | Reject for this request |
| Store neighbors in YAML, render a widget | Structured values | Existing `[n`/`]n` ignores YAML; navigation becomes fake user properties; still needs a count strategy | Reject |
| Persist links, derive `N of M` live | Fewer sibling rewrites on insertions | Two snapshots can disagree; needs roster transport and stale-state rules; fallback lacks the count | Credible later optimization |
| Persist links and count in one managed strip | Portable, inspectable, coherent per note; works with existing link syntax | Membership changes rewrite every member's denominator | Recommended at the observed scale |

The cost must be explicit. Adding a record to `eat` changes `M` in 104 existing notes and creates a 105th strip. Removing a record changes the denominator in every survivor. A title change can shift many ordinals. Those operations are O(M) note writes, even though only a few neighbor edges change. Scanning and sorting remain O(M log M).

At 104 records in the largest observed album, that is a plausible trade for simplicity and durable behavior, not proof that it will feel fast. Measure elapsed capture time, bytes rewritten, and editor reloads before rollout. Batch changes once per album; avoid timestamp fields or per-record commits. If the measured cost is unacceptable, choose persisted neighbors plus a derived count as an explicit architectural revision—not a hidden mismatch between what the strip shows and what the keyboard follows.

## Exact proposed behavior

**Membership.** Use the album inventory's immediate-child roster, independent of status, dates, current UI filters, and collapsed groups. Canonical record identity and the existing album legacy noun remain supported for migration. Ordinary field validation failures do not remove a record. An identity conflict—wrong parent, unrelated type, undecodable frontmatter—or unreadable member must produce a diagnostic and hold navigation generation for that album, rather than silently shrink `M`, rewrite an unrelated note, or publish half a ring. Healthy albums continue independently during maintenance. This is stricter than merely counting direct files, and deliberately avoids claiming a healthy walk over uncertain input.

**Order.** Extract the existing title-then-path comparator into a shared helper. Use the existing grouping title projection: nonblank frontmatter title, otherwise the humanized stem. Compare the lowercase title, then the exact vault-relative path as a deterministic tie-breaker. Do not sort by creation date, status, raw filename alone, or the order of rendered index rows. Do not have JavaScript re-sort it with locale defaults.

This v1 definition is deterministic case-insensitive lexical order, not a full linguistic or natural-number collator: `Part 10` sorts before `Part 2`; `The` is retained; accents are not stripped. That is an explicit precision of “alphabetical,” chosen to reuse established Bob behavior across hosts. If those examples are undesirable, change the shared comparator and its fixtures deliberately. Display alias escaping must happen after computing the key, so punctuation sanitization cannot change order.

For ordered members `R[0..M)`, use:

```text
position = i + 1
previous = R[(i + M - 1) % M]
next     = R[(i + 1) % M]
```

Apply the formula only when `M >= 2`:

| Case | Behavior |
| --- | --- |
| Empty album | Existing empty-album view; no record strip exists |
| One record | `1 of 1`, album link, and “Only record”; no self-links |
| Two records | Both directions point to the other record, as requested |
| Three or more | Immediate alphabetical neighbors, wrapping at both ends |
| Duplicate titles | Stable path tie-break; tooltip/accessibility text disambiguates paths |
| Missing or moved destination | Refuse that managed jump and refresh/repair; never create a replacement note |
| Incomplete inventory | Unknown/unavailable state; never `0 of 0` or an invented total |

A one-record ring could mathematically link to itself. I recommend the exception because reopening the same note offers no useful movement and can disturb focus or history. This is a requirement adjustment, not an accidental consequence.

**Keys and clicks.** `[n` and `]n` remain the commands; `[[` and `]]` continue through the existing remembered `n` family. A managed strip gets precedence over unrelated arrow-labelled body links on that record. Preserve those authored links; do not relabel or delete them. Singleton, damaged, and missing-target states are terminal results, so they never fall through to an unrelated prose link. An eligible record awaiting its first strip should teach that album sync is pending. Other note types keep today's link semantics.

Strip arrows and footer arrows use the same directional resolver and existing pane/history behavior. Successful strip-arrow navigation selects the `n` family so repeat follows the last navigation action. Clicking the album breadcrumb is ordinary parent navigation. Preserve modifier-click behavior and native hover previews where possible. Do not automatically switch the walk family merely because a record became visible.

## Appearance and Markdown ownership

Use one calm navigation row immediately below the record sheet's breadcrumb and above its fields. It survives sheet collapse. The title remains the strongest element; the count is supporting information. An illustrative wide layout, using fictional names:

```text
Ninja Sushi                                      ⊞ Edit   ▾
Body › Eat · Restaurant

‹ Alder House             42 of 104 · A–Z          Orchard ›

Status       💚 Liked
Category     Japanese
```

At a narrow width:

```text
Ninja Sushi                         ⊞ Edit   ▾
Body › Eat · Restaurant

‹ Alder…          42 of 104          Orchard… ›
                       A–Z
```

Use a three-column grid with flexible outer columns and a non-shrinking center. Ellipsize neighbor titles before compressing the count. Use tabular numerals, subdued but readable text, theme variables, and a visible focus ring. Avoid a large colored callout, pill around every datum, separate “Navigation” heading, or permanently floating overlay. The existing `n` footer remains the long-note compass; it can add the same album and count without becoming another competing banner.

Choose the typographic chevrons `‹` and `›` with destination names, rather than bare ASCII angle brackets. They are already supported by the parser. Previous starts with `‹`; next ends with `›`. Full labels belong in hover text and accessible names: “Previous record: Alder House. 41 of 104 in Eat.” At the boundary add “wraps to last” or “wraps to first.” Do not show a toast on every ordinary step or pretend wrapping completed a review.

For custom controls, use at least a 32-pixel desktop target and aim for 44 pixels on touch; never shrink the clickable region to the glyph. WCAG's minimum target-size guidance is 24 by 24 CSS pixels with specified exceptions, while its link-purpose guidance supports descriptive names/context. The larger sizes here are a design recommendation, not a claim that WCAG mandates 44 pixels everywhere. [Target size](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html), [link purpose](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html).

A proposed source representation is a **single owned callout without an H2**:

```markdown
> [!record-nav] [[eat|Eat]] · A–Z
> [[eat/alder_house|‹ Alder House]] · 42 of 104 · [[eat/orchard|Orchard ›]]
```

The singleton representation is unambiguous:

```markdown
> [!record-nav] [[eat|Eat]] · A–Z
> 1 of 1 · Only record in this album
```

These are proposed formats, not existing commands or supported callouts. Full album-relative targets avoid basename collisions. Ordinary Obsidian links support path-qualified targets and aliases. Obsidian can update links on rename, but that cannot recompute ordinal positions or neighbors after title changes. [Obsidian internal links](https://obsidian.md/help/links).

Bob owns precisely the generated callout span. It does not own the rest of the body, frontmatter, notes, comments, or legacy H1. Reuse the established safe alias escaping from album indexes; validate destinations rather than interpolating arbitrary title text into links. Scan structurally so examples in code fences, comments, and YAML are not treated as the real region. Ambiguous or damaged regions should be reported with a path and line, never guessed through.

On first insertion, place the callout after a leading legacy H1 when one exists, otherwise at the start of the body. This preserves the current tidy rule that recognizes a redundant H1 only when it is first body content. Later refreshes replace the owned span in place. Existing arbitrary arrow links are not ownership markers and must not be automatically “adopted.”

The current shared region planner always builds an H2 around new catalog regions and currently self-heals duplicate callouts. It is therefore useful infrastructure, not a drop-in implementation. Add a tested headless insertion mode and choose a stricter duplicate policy for navigation, or build a small dedicated span planner with the same byte-preservation guarantees. Do not alter existing catalog semantics globally to fit this strip. [Region planner](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/host_catalog/region.rs), [record tidy behavior](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/docs/records.md#tidying-empty-notes-sections-and-redundant-h1s).

In Reading and Live Preview, project the callout into the sheet once and suppress its raw rendered copy only after that projection mounts successfully. Source mode retains the Markdown. A failed renderer or disabled desktop sheet leaves the callout usable. Mobile needs a lightweight strip renderer or callout styling independent of the desktop-only Record Card; it must not need a local Bob subprocess just to follow saved links.

There is a limit to the fallback guarantee: native Obsidian can create a nonexistent linked note. Bob's managed controls and keys must refuse that operation, but a user following raw Markdown with Bob disabled gets native behavior. Durable Markdown alone cannot enforce application-level no-create semantics.

## Implementation shape and reliability

Keep one Rust projection producing each member's path, display title, previous/next path, position, and total. Both write paths and diagnostics consume it. The plugin parses or consumes the resulting managed snapshot; it does not reconstruct the roster from a `.base`, DOM rows, search results, or metadata traversal on every keypress.

Extend `bob albums sync` to maintain these strips alongside indexes and owner catalogs. This already has the appropriate maintenance lifecycle and nightly entry point. Avoid adding another timer, a separate global sync command, or a plugin that writes Markdown directly. The existing plugin album service already observes create/modify/delete/rename events, fingerprints frontmatter, coalesces sync work, and suppresses writer echoes. Extend that service carefully for navigation inputs and managed-region damage. [Album service](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-ledger-tools/src/241m-plugin-album-data-service.js).

For Bob-owned capture and `records new|update`, compute the final roster with all staged postimages, then stage affected record strips and the album index in the **same guarded transaction**. A bulk capture should produce one final projection per affected album and one final edit per path. A record changed by capture and by navigation must merge into one postimage, not compete as two independent edits. Schema edits and Undo should recompute the projection from their final state, never restore an old snapshot of unrelated siblings.

This requires widening today's singular album edit plumbing. `AlbumWritePlan`, `PlannedAlbumWrite`, capture's `stage_album_index`, and the associated preview/output payloads currently revolve around one album file. Return a derived-edit bundle instead. Keep existing JSON keys compatible and add explicit affected navigation paths/diffs so dry-run previews do not conceal the sibling rewrites. No new CLI command is necessary for the initial implementation. [Album write plan](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/albums/write.rs#L20), [record CLI integration](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/records/cli.rs#L2461).

The guard set must expand too. Today's index plan can read just member frontmatter because it does not rewrite member bodies. Navigation writes require full preimages of every rewritten sibling, as well as folder membership and all ordering inputs. The shared writer provides guarded installation and rollback, but those guarantees only cover dependencies supplied to it. Test changes to an unchanged neighbor's title as well as changes to an edited note. A maintenance lock is host-local; it does not replace pre-sync and preimage validation. [Read dependencies and transaction writer](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/host_catalog/txn.rs).

Navigation should have explicit `current`, `missing`, `stale`, and `damaged` diagnostics, separate from the album index state. Do not clear a valid strip because a scan was incomplete. During maintenance, hold all strips for an unsafe album and report it; healthy albums may proceed. In a user mutation that promises an immediate coherent ring, a failed sibling guard or damaged managed region should refuse the affected transaction with a specific repair message, rather than publish an unexplained partial update. This makes generated navigation part of that write's dependency set; preflight and precise errors are essential because a sibling defect can now affect capture.

For manual edits, remote sync, rename, and deletion, consistency is eventual: event-driven sync repairs the roster, and nightly sync remains a backstop. Never claim that a collection of file replacements is atomically visible to Obsidian. Coalesce renderer refreshes at completion and guard asynchronous responses against source-path/generation changes. While known stale, keep the last coherent snapshot visibly marked as updating, or disable its controls; do not combine fresh counts with old links. Every managed jump rechecks that its exact target still exists in the expected album and refuses a missing or moved destination. Navigation itself must not launch a write transaction per keypress.

Implement one resolver used by the command, `walkMode.links`, record-sheet arrows, and the links footer. Its result should distinguish unmanaged notes, valid managed navigation, singleton, pending, damaged, and missing-target states, and explicitly mark managed targets as not creation-eligible. Preserve current generic link behavior for other notes. Validate the managed link's album confinement and reject URLs, traversal, anchors, and cross-album targets. Keep preview and activation on the same source snapshot, revalidating after asynchronous work.

Two easily missed integration cases deserve explicit tests. New record bodies currently omit H1s and can be empty; adding a strip changes those shapes and interacts with the sheet's frontmatter-only mounting path. Also, title and neighbor changes must refresh the visible strip without stealing editor focus, adding duplicate widgets, or polluting the user's undo history. [Record renderer](https://github.com/bobs-org/bob-cli/blob/2f80442bb2c3141b69131c6db7786516fa165ca0/src/native/records/render.rs#L305), [sheet mounting](https://github.com/bobs-org/bob-plugins/blob/04ef18fee52e5a7fcf4002afbe7ceaaed55f2c9c/plugins/bob-ledger-tools/src/242k-plugin-record-sheet.js#L506).

## Acceptance and rollout

The important tests are invariants and user outcomes, not only snapshots of generated strings:

| Area | Required proof |
| --- | --- |
| Ring | For `M >= 2`, previous(next(r)) = r; M forward steps return to the start and visit each member once; two-record arrows share a target |
| Order | Case variants, duplicate titles, numeric titles, punctuation, accents, fallback titles, and randomized directory enumeration yield deterministic results |
| Membership | Status and schema-field edits preserve membership; nested files stay out; identity conflicts and unreadable members never produce a smaller apparently healthy ring |
| Writes | Creation, title changes, deletion/rename repair, multi-item capture, and cross-album moves update all required strips; second sync changes no bytes and creates no commit |
| Guards | Concurrent member insertion/removal, sibling title/body edit, schema edit, and a failed install refuse or roll back without partial published results |
| Preservation | LF/CRLF, supported BOM handling or explicit refusal, authored comments, fences, notes, custom H1s, and manually placed regions survive |
| Navigation | Keyboard, repeat, sheet, and footer agree; earlier unrelated arrow links cannot hijack the ring; no missing-target path creates a record |
| UI | Reading, Live Preview, Source, headingless/nav-only notes, collapse, embeds, split panes, plugin disable, and mobile fallback each show one appropriate strip |
| Accessibility | Keyboard focus, descriptive names, target sizes, light/dark themes, long names, and 375px width remain usable |
| Synchronization | Own generated writes do not loop; burst events coalesce; stale async responses never paint another note; failed post-sync never replays capture |

Start with the pure projection and scratch-vault transaction tests. Then update the shared navigation resolver and presentation in bob-plugins. Run existing relevant navigation, links-footer, album-service, record-sheet, and capture suites; add a real Obsidian walkthrough for no-H1 records, wrap, a two-record album, and a missing destination. Use source fragments and regenerate plugin entrypoints under that repository's build rules.

Roll out compatible plugin behavior first, then the CLI writer, then a reviewed `bob albums sync -d` backfill. Record counts and changed paths must be visible before the first real write. Measure the current largest album and a larger synthetic album; no benchmark was run in this research. A repeat sync must be a no-op. Preserve a scoped commit for the backfill so reverting generated spans is possible without changing user-authored content.

The initial deliverable should stop there. Do not bundle record rename commands, a new record picker, fuzzy alphabetical rules, session history, custom sorting UI, or a visual redesign of the entire record sheet.

## Requirement adjustments and recommended solution

The justified adjustments are:

- Use named `‹` / `›` links rather than bare `<` / `>` glyphs; the existing matcher supports both.
- Treat one record as `1 of 1` with no self-navigation. Keep the requested two-record behavior exactly.
- Define “alphabetical” as the existing deterministic title order, globally across the album, not the grouped index's row order.
- Make `N of M` a location cue, never a completion meter; expose wrap in descriptive text.
- Make managed record navigation open existing targets only, and give it precedence over unrelated manual arrow links without deleting those links.
- Promise immediate guarded consistency for Bob-owned writes and explicit eventual repair for outside edits; report uncertainty instead of inventing positions.
- Accept and measure O(M) generated-note rewrites on membership changes in exchange for keeping links and count durable and coherent.

**Recommended solution:** implement a headless, Bob-owned `[!record-nav]` strip through the existing album write/sync pipeline, storing both named neighbor links and `N of M` from one shared Rust projection. Present it as a quiet, responsive row under the record breadcrumb, keep its Markdown fallback, and make the existing `n` commands and footer resolve that exact managed state with no-create semantics. At the observed collection sizes, this is the most direct fit for the request: understandable to browse, inspectable on disk, consistent across entry points, and visually integrated with the record sheet already in use.

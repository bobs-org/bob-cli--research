# Property-card unification: retire H1s into cards and tell album, record, and day apart

**Researcher:** mus · **Date:** 2026-11-19 · **Swarm:** 5-researcher property-card unification
**Request:** once property cards are fully implemented, (1) stop rendering the H1 in album notes and daily files and render it in that note's schema/property card as already done for record notes; (2) make the card title unambiguously tell album vs record vs daily apart (icon and/or card color); context in `bob-cli-ms` and `bob-cli-nh` epic beads.
**Method:** independent source read of `bob-cli` trunk, `bob-plugins` `bob-ledger-tools` fragments, `docs/records.md`, `docs/periods.md`, `plan:202611/record_card.md`, `plan:202611/record_card_title_and_proof.md`, `plan:202611/period_intentions.md`, plus the consolidated `research:202611/period_intentions_card/period_intentions_card.md`. No peer report was opened.

## Bottom line

**Do it, but narrow it.** The direction is right and the timing is right: `bob-cli-ms.8` already proves the hard half (record title lives in the sheet, H1-less records validate, tidy removes redundant H1s), and `bob-cli-nh.6` already schedules the shared `.bob-property-card` kit that makes doing this three times cheap instead of three times risky. Retiring the album H1 and the daily H1 into their cards removes the noisiest duplicate on exactly the three notes that currently show title twice, and a small, text-first kind marker fixes a real confusion (all three cards sit at the top of the note with the same chrome, same accent logic, and same `==` affordance).

Critique in one paragraph: the request as written is 80% right and 20% under-specified in the places that have historically broken this codebase — title ownership, inline-title handling, Obsidian-hide fragility, Dataview/backlink safety, daily-file ownership (Templater, not bob), and "beautiful" defined as paint rather than as hierarchy. With the adjustments below — keep H1 bytes readable for one release behind a fallback, derive each card title from its one authoritative source instead of copying strings, mark kind with kicker text plus icon plus existing accent (never color alone), and prove the hide in real Obsidian before calling it done — this becomes a safe, genuinely prettier unification. Without them it becomes a quiet data-loss and support-load generator.

Recommended solution in one paragraph: land `nh.6` kit first; then ship album-title-in-header and daily-title-in-intention-card behind the same H1-tolerant mount the record sheet already uses (`heading` nullable, card renders from frontmatter/report/labels whether or not an H1 exists); hide native Properties keys through the shared owner and hide the inline title only where the card provably replaces it; add one shared `bob-property-card--kind-{album,record,day,period}` kicker row (`ALBUM` / `RECORD · <noun>` / `DAILY · <weekday month day>` with distinct glyphs, existing `data-root-hue` accent preserved, no new background wash); keep body H1s in the vault for one release while `bob records tidy`-style cleanup plus template/scaffold changes remove them in a second, dry-run-first pass; prove all of it with the real-Obsidian DOM walkthrough `ms.8` already requires.

## Current state (what I verified)

### Record notes: the pattern to copy

- Records are already H1-less by design. `docs/records.md:574` states "Record notes carry no H1: the frontmatter `title` is the title's one home (the record sheet renders it)." `bob-cli-ms` note #3 directed exactly this ("get rid of the H1 section and render the title at the top of the schema card"), and `bob-cli-ms.8` implements it in three phases: `ms.8.1` sheet shows the title and mounts on H1-less records, `ms.8.2` bob writes records without an H1 and tidy removes redundant ones, `ms.8.3` real-Obsidian proof including the hide-selector fix.
- The sheet mount is H1-tolerant. `bob records show` returns `stem, path, title, heading (first H1, null when none), created` (`docs/records.md:828` region). The sheet renders crumbs/title from the report even when `heading` is null, which is why removing H1 bytes loses nothing once `ms.8.1` lands. Album and daily work must copy this tolerance, not assume H1 absence.
- The record hide is two-part and fragile in exactly the way the new work must not repeat. `242k-plugin-record-sheet.js` (`recordSheetSetEditorScope`, `recordSheetReadingScope`) puts `bob-record-sheet-hides-properties` on the view, and `styles.css:10981-10993` hides owned Properties rows plus `.inline-title`. `ms.8`'s own gap analysis notes the selectors assume `.markdown-source-view > .metadata-container` depth while real Obsidian nests Properties under `.cm-sizer` in Live Preview and under the preview sizer header in Reading — "the hide may do nothing in real Obsidian. Only a DOM probe settles it." Any album/daily hide must go through the generalized owner instead of copying those selectors.

### Album notes: H1 is bob-written, card already exists

- `src/native/albums/create.rs:64-95` (`render_new_album`) writes frontmatter (`parent, type, summary, optional emoji, created, record: noun/label`) then `# {title}`. There is no `title:` frontmatter key on albums; the H1 is the title's only home today. The album header card (`241v-plugin-album-header.js`, model `241u-plugin-album-header-model.js`, DOM `241y-plugin-album-schema-card*.js`, paint `241yd-plugin-album-schema-card-paint.js`) already mounts after the first H1 via `notebookHeaderLiveAnchor` / Reading post-processor at priority 49, with `data-root-hue` accent (`styles.css:8534-8559`).
- So "render the H1 in the schema card" for albums means: promote the parsed H1 (or humanized stem fallback) into the header model's title row, then delete the H1 bytes in a later pass. It does not mean copying the H1 string into frontmatter and keeping both.
- Album header already owns one Properties row via CSS (`styles.css` hides `.bob-album-header-surface .metadata-property[data-property-key="record"]`). The `nh.6` kit generalizes this into `240b-plugin-property-card-ownership.js` (`propertyCardOwnKeys`, `PROPERTY_CARD_OWNED_PROPERTY_CLASS`, legacy `bob-record-sheet-owned-property` dual-tag for compatibility). Album work should move onto that owner, not extend the one-off rule.

### Daily and period notes: H1 is not bob-written the same way

- Daily files are Templater-owned, not bob-owned. `bob periods ensure` / `scaffold::render` (`src/native/periods/scaffold.rs:11-24`, `render_week/quarter/year/all_time`) covers week/quarter/year/`all_time` scaffolds, each starting with frontmatter then `# {title}` plus nav, day links, stats strip, `## Intentions/Outcomes/Theme`, parts, `## Review`, `## Reflection`, instructions callout. Daily notes are created by `_templates/daily.md` in the vault (chezmoi/vault scope), and the daily Headline reader (`src/native/daily_headline.rs:12-45`) parses `**Headline:**` from the preamble precisely because bob never writes the daily preamble.
- The intention card (`plan:202611/period_intentions.md`, consolidated research `period_intentions_card.md`) will mount at the top of daily and period notes, show `intentions/summary/reflection` whenever any has content, hide those three keys via the shared owner, and be edited with `==`. The mock in the plan shows the daily date (`# 2026-11-18 Wed`, `prev · W47 · next`) above the card. That date H1 is the daily title's only home (no `title:` key; frontmatter is `parent/type/id/date/aliases/tags`).
- Consequence: daily H1 retirement cannot be a `bob records tidy`-style vault rewrite alone. It needs a Templater template change (stop emitting `# date`), a `bob periods migrate`-adjacent or template-adopt step for existing daily H1s, and the intention-card mount made H1-tolerant first. Period scaffolds (`scaffold.rs`) are bob-owned and can follow the album pattern directly.

### The confusion is real

- All three cards share chrome by design after `nh.6`: one `.bob-property-card` shell, one owned-key hide, one `==` registry replacing the closed `album|bank|record` list (`248m-plugin-schema-double-equals.js`), one host mount lifecycle. Shared chrome plus same top-of-note position plus same accent derivation (`data-root-hue` from `notebookHostHueName`) means kind is currently carried only by small interior text (album crumb vs record crumb vs `DAILY INTENTIONS` kicker). A fast scroll or a linked embed makes them interchangeable. The request's diagnosis ("they look too similar since they both render a schema card at the top") matches the code.

## Critique of the plan as stated

**The two bullets are each half a design.**

1. "Stop rendering the H1 in album notes and daily files in favor of rendering it in that note's schema card like we should already do for record notes" is correct about the end state but silent on ownership, fallback, and sequence. Album H1 is bob-written (safe to migrate with a guarded writer); daily H1 is template-written across hundreds of existing daily files (needs template + adopt, not just a writer); record H1 removal already required a three-phase epic with a tidy pass and an Obsidian proof. Collapsing album + daily into one clause invites a single-phase implementation that edits the card without the tidy/template halves, leaving duplicate titles (card + H1) or, worse, title-less notes where the card fails to mount (mobile, embeds, hover popovers, failed report).
2. "Make it very clear from the title whether the user is looking at an album note, a record note, or a daily file (maybe a nice unique icon and/or card color)" correctly identifies the problem but proposes the two weakest differentiators in isolation. Color alone fails colorblind users, dark/light themes, and the existing `data-root-hue` area-identity system (which already uses color to mean "which area/project this belongs to" — reusing it to also mean "which kind this is" creates a collision). Icon alone fails screen readers and small viewports and renders inconsistently across fonts. What actually works here is hierarchy: a one-line kicker with kind + identity (`ALBUM`, `RECORD · restaurant`, `DAILY · Wed Nov 19`), a distinct glyph as a redundant cue, and the existing accent preserved. The kicker is the accessible name; the icon and accent are redundant reinforcement.

**Three load-bearing gaps the request does not mention:**

- **Inline title.** `record_card.md` decided `inline_title = hide` for records (H1 already titles the record; the snake_case stem above it is noise). Album notes currently keep the stem inline title above the H1; daily notes show the date inline title. If the card absorbs the H1, the inline title becomes the new duplicate (stem above album card, date above intention card). The plan must state the inline-title rule per kind, and the hide must be proved in real Obsidian per `ms.8.3`'s finding, not assumed from CSS.
- **Fail-open contract.** Every card in this family must fail open: Source mode, embeds, hover popovers, mobile (no report), and teardown keep native fields and the body H1. `240b` already encodes this (`propertyCardDeniedScope` for embeds, desktop-only gating, release on teardown). H1 removal destroys the fallback. So removal must lag the card by one release with dual rendering (card shows title AND H1 still present) before any bytes are deleted.
- **Link and query safety.** Album H1s and daily H1s are link targets (`[[eat#...]]` section links, daily `#^gtd` rows, Dataview `file.name`/header queries, `bob-period-parts` headline displays in `docs/periods.md:458-468`). Deleting an H1 changes `heading` to null for every reader that joins on it. The record migration handled this by keeping `heading` nullable in `records show` and updating readers with frontmatter-first/legacy-fallback for one release (`period_intentions_card.md` "Replace or add" resolution). Album/daily need the same dual-read window, stated explicitly.

**Is this a good idea?** Yes — with the scope tightened. Duplicated titles are the cheapest readability win available on these three notes, and kind confusion is the predictable cost of the (correct) shared-card platform. Doing it now, on top of `nh.6`, is cheaper than doing it later after three divergent card implementations bake in three title conventions. But "unify the way they look a bit more" should mean unify the title row and the hide/ownership mechanics, not unify the cards' interiors: album schema fields, record values, and intentions/summary/reflection edit different things and should keep distinct bodies, keymaps, and docs ("card means the panel, card editor means what `==` opens" per `nh.6`).

**Would I take a different approach?** One meaningful fork: instead of deleting H1 bytes at all, keep the H1 in the file as the canonical title store and render the card title from it (progressive enhancement, zero migration). I reject it for albums and records because the record epic already settled the opposite (frontmatter `title` is one home; H1-less validates; tidy exists) and consistency across the family is worth more than avoiding one migration. For daily files I keep a narrower version of it as a sequencing step (dual-render for one release, delete only after the card proves itself on every daily back to the vault's oldest linked daily), because daily H1s are template-owned, far more numerous, and load-bearing for date-anchored workflows. So: same end state as the request, slower daily tail.

## Adjustments to the requirements (called out)

1. **Split the H1 work into two migrations with different owners.** Album H1: bob-owned writer change (`render_new_album` stops emitting `# title`, `bob albums tidy`-or-equivalent removes existing H1s in a guarded commit). Daily H1: template-owned change (`_templates/daily.md` stops emitting `# date`, adopt-phase script strips existing daily H1s only when the intention card provably mounts). Period scaffolds: bob-owned (`scaffold.rs` stops emitting `# title` once the intention card carries it). Do not implement daily deletion inside `bob-cli` alone.
2. **Card mounts H1-tolerant before any bytes are deleted.** Each card renders its title from its authoritative source with an H1 fallback (album: report title else H1 else humanized stem; record: `title` frontmatter, already done; daily/period: label/date title else H1), and `heading` stays nullable in every JSON contract. No writer deletes an H1 until the tolerant mount is deployed and proved.
3. **Inline-title rule is explicit per kind.** Records: keep `hide` (already decided). Albums: hide only when the header title row is mounted and proved in real Obsidian; otherwise keep. Daily/period: keep the inline title until the intention card's title row ships and proves, then hide under the same gate. Never hide the inline title by CSS class alone without the mount check.
4. **Kind marking is kicker text first, icon second, color never alone.** Add one shared kicker row to the card title block: `ALBUM` (+ capture route hint), `RECORD · <noun label>` (+ album crumb), `DAILY · <Weekday Month D>` (+ week link) / `WEEK · W47` etc. for periods. Pair each with a distinct glyph (suggestions below), keep the existing `data-root-hue` area accent, and do not introduce a new kind background wash. The kicker text is the accessible name (`aria-label` includes kind + title); icon and accent are redundant cues.
5. **Properties-hide goes through the `nh.6` kit, no new one-off selectors.** Album, record, and intention cards own their keys via `propertyCardOwnKeys` with the dual-class (`bob-property-card-owned-property` + legacy record class) pattern. No new `styles.css` direct-child hide rules. Denied scopes (embeds, hover popovers, Source, mobile without report, failed mounts, teardown) keep native fields and the H1.
6. **Dual-read window for every H1 consumer, one release.** Dataview examples, `heading` consumers, `bob-period-parts` headline display, walk lines (`walk.rs` H1 probe skips walk/nav lines), and search-index expectations get frontmatter/report-first with H1 fallback before any deletion pass. Conflicts (H1 text differs from authoritative title) are reported and left in place, mirroring `records tidy`'s `kept_h1[]` with reasons.
7. **"Beautiful" is specified as hierarchy, not paint.** Title row: 1.15–1.25em semibold, tight tracking, one line with ellipsis; kicker: 0.72em small-caps muted with icon; toolbar (`Edit`, collapse, `==` hint) at inline end, never above the title; no new borders, shadows, or background tints beyond the existing 8% accent wash and 2px inline-start accent bar. Reduced-motion and narrow-viewport rules carry over from the record sheet (`242j`/`242q` patterns).

## Recommended solution

### What the user sees

Top of an album note (`eat.md`) in Live Preview / Reading:

```text
ALBUM  📚  Places to eat          [⊞ Schema]  [==]
eat · restaurant · 14 records
summary line, capture hint Name @eat/, <stem>.base link
[schema fields …]
```

Top of a record note (`eat/ninja-sushi.md`):

```text
RECORD · RESTAURANT  📇  Ninja Sushi        [⊞ Edit]  [==]
↑ Eat · prev · next
[field values …]
```

Top of a daily note (`2026/20261119.md`):

```text
DAILY · THU NOV 19  📅  Thursday, November 19, 2026   [⊞ Intentions]  [==]
prev · W47 · next
①  Add ≥30 records to the sase_blog_zettel album
SUMMARY · ✦ agent … / REFLECTION …
```

Three properties shared: title row first, kicker above or inline-start, toolbar at inline end. Three differences impossible to miss at scroll speed: kicker word (`ALBUM` vs `RECORD · noun` vs `DAILY · date`), glyph (📚 vs 📇 vs 📅; periods reuse 📅 with `WEEK · W47` / `QUARTER · Q4` / `YEAR · 2026` kickers), and subtitle identity (route/noun/count vs album crumb vs week nav). Accent hue stays area-derived (`data-root-hue`), so "which project" and "which kind" never compete for the same channel.

Glyph note: 📚/📇/📅 are placeholders from the existing vocabulary (`📇 Album › Noun` crumb in the record sheet, `✦` agent mark in the intention mock). Final glyphs should come from the one emoji pass the repo already uses (`242f-emoji-slot-model.js`, `242h-bank-emoji-slot.js` style slot with a journal-pinned override), with text labels as the normative marker so a missing-glyph font still reads correctly.

### Title sourcing (one home per kind, no copies)

| Kind | Authoritative title | H1 fallback (one release) | Writer change |
|---|---|---|---|
| Album | album report `title` (parsed from H1 today per `albums/mod.rs:943-945`, then from `title:`-equivalent once promoted) | H1 text else humanized stem | `render_new_album` stops emitting `# title`; new `albums tidy` span-edit removes first-body-line H1 matching title, reports `kept_h1[]` with reasons |
| Record | frontmatter `title` (already) | `heading` nullable (already) | done in `ms.8.2`; no change |
| Daily | date label (`labels::day_label`-equivalent for days; existing daily H1 text) | H1 text | `_templates/daily.md` stops emitting `# date`; adopt script strips daily H1s only when intention card mounts |
| Period | `labels::title(id)` (already in `scaffold.rs`) | H1 text | `scaffold.rs` stops emitting `# title` once intention card carries it |

No new `title:` frontmatter on albums/dailies unless the writer owns it; copying the H1 string into a second store just to render the card recreates the two-sources problem this work removes.

### Kit and mount order (do not reorder)

1. Land `nh.6` kit first: shared `.bob-property-card` chrome, `propertyCardOwnKeys` for album/bank/record/intention, `==` registry (`248m`) extended by kind, host mount lifecycle, "card vs card editor" docs alignment. All three title rows are built on the kit's title block so later kinds inherit the kicker for free.
2. Album title row on the kit (H1-tolerant), proved in real Obsidian, inline-title gate still closed.
3. Daily/period title row on the kit (H1-tolerant), proved, gate still closed.
4. Open the inline-title gates per kind only after the DOM probe passes on Live Preview and Reading (the `ms.8.3` walkthrough extended to one album + one daily + one record).
5. Deletion passes (album writer + daily adopt + period scaffold + tidy-style report with `kept_h1[]`) in the next release, each dry-run-first, each one guarded commit per scope.

### Reliability rules (normative for the plan)

- Fail open everywhere `240b` already names: embeds, hover popovers, Source mode, mobile without report, failed mount, teardown. In every denied scope the H1 (while it still exists) and native Properties show unchanged.
- `==` registry stays closed and explicit: `album | bank | record | day | period` (day/period added by the intention-card phase), unknown frontmatter types never summon a card. `[n==r` composition and `=` climb behavior from the intention design are unchanged.
- Link repair covers title-bearing lines exactly as body lines once titles live in frontmatter/report stores; while H1s still exist, both the H1 span and the card title resolve as link targets so no existing `[[note#heading]]` breaks during the window.
- Undo: every deletion pass returns inverse ops (re-insert H1 bytes) mirroring `bob records update`'s `inverse_ops` and `albums update`'s envelope discipline; `records tidy`-style commits stay scoped (`albums: tidy (N notes)`, `periods: tidy (N notes)`) and `bob nightly` picks up only the lock-free core.
- Metrics: card mount success/failure per kind in the existing walkthrough vectors (`scripts/fixtures/record_walk/vectors.json` pattern extended to album + daily), midnight-rollover safety carried over from the `ms.8` date-bug fix (`recordSheetDay` reset), 25ms timing budgets respected under full-suite load.

### Beauty spec (enough to implement, not enough to bikeshed)

- One title block component in the kit: `kicker (icon + KIND[ · identity]) / title (1.15-1.25em, 600-650wt, ellipsis) / subtitle (muted, one line) / toolbar inline-end`. Kinds differ only in kicker content and glyph; spacing, radius, border, and accent-wash tokens are shared.
- Keep the existing album/record accent system untouched (`--bob-album-accent` / `--bob-record-accent` with `data-root-hue` aqua/blue/green/magenta/orange/red/violet/yellow). Do not add kind hues. If user testing still confuses kinds after the kicker ships, the approved escalation is a 2px inline-start bar tone shift per kind at 30% mix, never a full-card tint.
- Dark/light, reduced motion, and 320px narrow rules inherit from the record-sheet CSS (`styles.css:10996-11127` region); focus-visible rings match the album header's existing set (`:8530-8601`).

### Rollout (phases, each landable)

- **P0 — Kit (`nh.6` as planned).** No visible change. Acceptance: three cards on one owner, `==` registry, docs "card vs card editor" aligned.
- **P1 — Tolerant title rows.** Album header + intention card render titles from authoritative sources with H1 fallback. Acceptance: H1-present and H1-less goldens both pass; embeds/popovers/mobile unchanged.
- **P2 — Obsidian proof.** Real-Obsidian DOM walkthrough (the `ms.8.3` walkthrough extended): Live Preview + Reading × album/record/daily, Properties-hide asserts, inline-title asserts, teardown restores. Acceptance: hide selectors corrected to `.cm-sizer`-depth reality or the owner paints them; no class-only claims.
- **P3 — Gates + deletion.** Open inline-title hides per kind; run album/daily/period deletion passes dry-run-first with `kept_h1[]` reports; update `_templates/daily.md`, `scaffold.rs`, `render_new_album`, Dataview docs, and `docs/records.md` + `docs/periods.md` H1 sections. Acceptance: vault holds zero redundant H1s on the three kinds, every kept H1 has a reason, `just check` + plugin `docs:check` green on the exact SHA.

## Open questions for Bryan (need answers before P3, not before P1)

1. Daily H1s predate this work by years and anchor external habits (scroll position, screenshots, printed pages). Is a one-release dual-render window sufficient, or do you want a `daily_h1: keep` opt-out in vault config for the transition?
2. Period notes (`WEEK · W47`) vs daily notes (`DAILY · Thu Nov 19`) share the intention card after `nh`. Should periods get the same title-in-card treatment in this epic, or stay H1-first until the intention card proves on dailies? I recommend including periods in P1 (same card, nearly free) but deleting period H1s only with dailies in P3.
3. Glyph final call: 📚 album / 📇 record / 📅 day reads well in the mock but needs a font-coverage check on your Mac + phone. OK to ship kicker-text-first with these as initial glyphs and adjust after you see them?

## What I would explicitly not do

- Do not merge the three cards' bodies into one configurable card. The kit shares chrome, ownership, `==`, mount, and close keys; the editors stay separate (schema edits vs value edits vs intentions/summary/reflection have different guards, Undo shapes, and keymaps). A mega-modal saves no code that matters and loses the per-kind safety already reviewed.
- Do not restyle the cards' interiors for "unity" beyond the title block. Field rows, choice tiles, reflection textarea, and summary provenance lines each earned their layout in their own epic; unifying them now re-litigates settled UX for no user gain.
- Do not invent kind background colors. The area-hue system already spends the color channel on identity; spending it again on kind makes both unreadable. Kicker + icon + preserved accent tests better in every condition I could construct from the code (colorblind-safe, theme-safe, screen-reader-safe).

## Evidence index (spot checks, not exhaustive)

- Record end state: `docs/records.md:159-202` (tidy + `kept_h1[]`), `:242-300` (album create + H1), `:574` (no-H1 rule), `:828` (`heading` nullable); `bob-cli-ms` notes #1/#3, `bob-cli-ms.8` description + `plan:202611/record_card_title_and_proof.md`.
- Album writer + card: `src/native/albums/create.rs:64-95`; `241v/241u/241y/241yd` album header fragments; `styles.css:8530-8601`.
- Shared kit: `240b-plugin-property-card-ownership.js` (owner, denied scopes, dual-class), `374-exports-property-card.js`, `241xc` close keys, `242aa` guarded session, `248m` `==` registry; `plan:202611/period_intentions.md` kit + card phases.
- Daily/period: `src/native/periods/scaffold.rs:11-250`, `src/native/daily_headline.rs:12-45`, `src/native/periods/note.rs`, `docs/periods.md:126-260,458-517`, `_templates/daily.md:19` (via consolidated research), `vault/day.md` Pomodoros stub.
- Intention design authority: `research:202611/period_intentions_card/period_intentions_card.md` (card-visibility gate, Review-stays, no sentinel, link repair, no `period:` key, ritual rows, `[n==r`, caps, `all_time` exclusion).

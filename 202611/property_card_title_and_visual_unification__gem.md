# Unifying Property Card Titles and Note-Type Visual Identity Across Albums, Records, and Daily/Period Notes

- **Date:** 2026-11-19
- **Author:** Researcher `gem`
- **Context:** Post-implementation follow-up design building on **bob-cli-ms** / **bob-cli-ms.8** (Record Card + H1 retirement) and **bob-cli-nh** / **bob-cli-nh.6–.7** (Property-Card Kit + Intention Card)
- **Repositories inspected:** `bob-cli` (`5b4c2636`), `bob-plugins` (`e2cdc8d`), read-only live vault `~/bob`

---

## 1. Executive Summary

The core instinct behind your proposal is **strongly right**: removing body `# H1` sections from structured Bob notes and rendering the note title inside the top property card eliminates redundant "triple headers" (`.inline-title` + Obsidian Properties + `# Title` + Card), makes Obsidian's Outline cleaner by promoting `##` sections to top level, and completes the document-hero model that `bob-cli-ms.8` introduced for record notes.

However, implementing the request *literally* as stated—*"stop rendering H1 in album notes and daily files, move title into the card, and distinguish album vs record vs daily via icon/color"*—breaks on **five concrete architectural and UX traps** discovered in `bob-cli`, `bob-plugins`, `bob-cli-nh`, and your live vault:

1. **Empty-Daily Title Blackout (`309 / 311` live 2026 dailies + every fresh morning note):** Under `bob-cli-nh`, the Intention Card does **not mount** when `intentions`, `summary`, and `reflection` are all empty. Removing `# YYYY-MM-DD ddd` from daily files without unconditionally mounting a Daily Header/Intention card leaves 99% of daily notes either **title-less** (if `.inline-title` is hidden) or displaying raw stem `20261119` above Properties (plus **135/311** older Zorg-converted 2026 dailies lack both `# ` H1 and `aliases:`).
2. **Albums Lack a Persisted YAML `title:` Key (`eat.md` → `Eat`, `tv.md` → `Tv`):** Unlike records (`title: "Ani Ramen House"`), albums derive `title` from H1 → `aliases[0]` → `humanize_stem`. Five of your six live albums rely on `# H1` for casing/labels (`Restaurants` on `eat.md`, `TV` on `tv.md`, `SASE Blog Zettel` on `sase_blog_zettel.md`). Stripping album H1s without first adding `title:` to album frontmatter corrupts `bob albums`, catalogs, breadcrumbs, and `bob-plugins`.
3. **Nav-Line Ordering Inversion (`prev · W47 · next` above the title):** Daily files open with `# 2026-11-19 Thu` followed immediately by `[[...|prev]] · [[...|W47]] · [[...|next]]`, and `bob-navigation-hotkeys` (`[n`/`]n`) parses body Markdown links directly (`680-plugin-link-parse.js`, `670-plugin-project-files.js`). Removing `# H1` puts `prev · W47 · next` nakedly above the hero card unless the card docks/mirrors the nav line (like Record Card's `bob-record-walk-rail`).
4. **Same-Area Root-Hue Collision & Orphan Daily Accents:** Albums and their child records share the exact same `data-root-hue` (`eat.md` and `eat/ani_ramen_house.md` are both `green`; `movies.md` and `movies/9.md` are both `yellow`), while `.bob-record-sheet-title` displays no icon or emoji and daily notes get `null` from `pomodoroHomeResolve` (falling back to `--interactive-accent` violet, colliding with `violet` areas). Color alone will fail both same-area distinction and `forced-colors: active` accessibility.
5. **Sibling Card Inconsistency (`W`/`Q`/`Y` Period Notes & `bank.md`):** Period notes share the exact Intention Card species as daily files (and already carry `aliases` titles), and `bank.md` is the 4th `.bob-property-card` species (`bob-cli-nh.6`). Leaving `# 2026-W47 · ...` outside its card while pulling `# 2026-11-19 Thu` inside splits one card species into two layouts.

### Recommended Solution in One Glance

Adopt a **Unified Property Card Title & Identity System** across all four `.bob-property-card` species (`album`, `record`, `intention` [split visually into `daily` and `period` variants], and `bank`), grounded on three design pillars:

1. **Always-Mounted Header Cards on Canonical Eligible Notes (Decoupled from Empty Fields):** Daily and period notes (`all_time` excluded) mount cleanly on desktop even when `intentions`/`summary`/`reflection` are empty, collapsing gracefully into a compact Calendar Title + Docked Nav banner with a quiet one-line prompt on open days.
2. **Fail-Open Title Ownership (`bob-property-card-owns-title`):** Generalize `.inline-title` suppression alongside `propertyCardOwnKeys(...)` so Obsidian's filename `.inline-title` is hidden **only** inside desktop Reading/Live Preview panes where the card cleanly rendered its title—preserving fail-open readability on mobile, Source mode, embeds, and hover popovers.
3. **Multi-Channel Species Identity (Silhouette + Surface + Kicker Badge + Icon + Title Ornament):**
   - **Album Card ("The Collection Cover"):** Thick **3px left accent border** in root hue, saturated header tint (`12%` header / `7%` body), `[library SVG] ALBUM` eyebrow pill + parent crumb + `· N records`, **`frontmatter.emoji` medallion** beside hero title, and primary `＋ <noun>` action.
   - **Record Card ("The Dossier Sheet"):** Calm **`1px` hairline neutral-frosted sheet** (`3%` tint) contrasting sharply against Albums even in the same root hue, `[album.emoji or tag SVG] <NOUN>` eyebrow pill + clickable `↑ <Album>` crumb, crisp un-cluttered hero title, field pills, and signature docked **walk rail footer**.
   - **Daily Card ("The Calendar Leaf"):** Dedicated **non-area temporal color** (`--bob-day-accent`, cyan-cobalt slate; optional amber live ring on today), **top 3px accent bar** instead of a left bar (instant calendar silhouette), `[calendar SVG] DAILY NOTE` / `TODAY` + `W47` pill, **mini tear-sheet date emblem** (`NOV / 19`) beside hero date title, and docked **`‹ Wed 18 · ↑ W47 · Fri 20 ›` footer** mirroring and folding the body nav line.
   - **Period Card ("The Horizon Banner"):** Matching temporal slate palette with distinct **`calendar-range` SVG + `WEEKLY` / `QUARTERLY` / `YEARLY`** badge, parent period crumb, docked prev/up/next strip, and aligned Intention bands.
   - **Bank Card ("The Ledger Hub"):** Matching eyebrow grammar (`[landmark SVG] BANK` + **`Bank`** hero title) so every Property Card speaks one visual language.

---

## 2. Verified Baseline: After `bob-cli-ms` and `bob-cli-nh`

Under `bob-cli-ms.8` (`plan:202611/record_card_title_and_proof.md`) and `bob-cli-nh` (`plan:202611/period_intentions.md`, `plan:202611/property_card_kit.md`), the top-of-note ecosystem converges on **four Property Card species** sharing `.bob-property-card`, `registerPropertyCard(...)`, `propertyCardOwnKeys(...)`, and `createPropertyCardHost(...)`:

| Dimension | Record Card (`record`) | Album Card (`album`) | Intention Card (`daily` / `period`) | Bank Card (`bank`) |
| --- | --- | --- | --- | --- |
| **Match predicate** | `type: "[[record]]"` (canonical under album) | `type: "[[album]]"` | `dayStripDayForPath` / `periodNotesPeriodForPath` (excl. `all_time`) | `bank.md` (`bank:` root config) |
| **Title source today** | YAML `title:` → H1 → stem (`242i`) | First `# H1` → `aliases[0]` → `humanize_stem` (`albums/mod.rs:122-123`) | `# H1` in body; **no `title:` key**; `aliases[0]` on `176/311` 2026 dailies & periods (`labels::title`) | Stem / `# H1` (none in `~/bob/bank.md`) |
| **YAML title survives H1 removal?** | **Yes** (`title:` required) | **No** (0/6 live albums have `title:` or `aliases:`) | **Only deterministically** (`YYYYMMDD` path for dailies, `id` for periods; `135/311` 2026 dailies lack `aliases:`) | N/A (fixed path) |
| **H1 in live vault notes** | **Removed** by `ms.8.2` (`records/tidy.rs`) | **Present** (`# Restaurants`, `# TV`, `# SASE Blog Zettel`, etc.) | **Present on post-Zorg** (`# 2026-11-19 Thu`, `# 2026-W47 · Nov 16 – 22`); **absent** on Jan–May 2026 Zorg dailies (`20260101.md`) | None on `~/bob/bank.md` |
| **`.inline-title` behavior** | Hidden on desktop when card owns `title` (`styles.css:10985-10986`) | **Visible** (`eat`, `sase_blog_zettel`) | **Visible** (`20261119`, `2026-W47`) | **Visible** (`bank`) |
| **Card mount condition** | Always on canonical record (incl. frontmatter-only Reading fallback) | Always on valid album note | **Gated in `nh`:** only mounts when `intentions`, `summary`, or `reflection` is non-empty | Always on `bank.md` |
| **Mount anchor** | Top of body (before legacy H1 in Reading) | After `# H1` (`albumHeaderReadingAnchor` / `notebookHeaderLiveAnchor`), fallback after frontmatter | Below `# H1` + nav + child-link lines, above `^gtd` / `bob-stats-strip` | After `# H1` / after frontmatter |
| **Accent color source** | `data-root-hue` (`styles.css:5491-5545`) → `4%` tint, `2px` start border | Same `data-root-hue` → `8%` tint, `2px` start border | No root area (`pomodoroHomeResolve` → `null`); falls back to `--interactive-accent` | `cash` `data-root-hue` → `8%` tint, `2px` start border |
| **Mobile support** | None (fail-open to stem + Properties) | **Renders compact header** (`241x:142-146`), no Properties hide | None (fail-open to stem/`aliases` + Properties) | Desktop Properties hide only; fail-open |

### Obsidian Vault Environment (`~/bob/.obsidian/`)
- `app.json` has `"vimMode": true` and does **not** set `showInlineTitle: false`, so Obsidian natively displays filename `.inline-title` at the top of every note unless hidden by `.bob-*-hides-properties`.
- `core-plugins.json` enables `"outline": true`, `"properties": true`, `"daily-notes": true`, `"templates": true`, `"bases": true`.
- `appearance.json` enables four custom CSS snippets (`task-statuses`, `dataview-properties`, `inline-code`, `ref-highlights`), none of which touch `.inline-title` or `.bob-property-card`.

---

## 3. Critique of the Proposed Plan

### 3.1 Is This a Good Idea?
**Yes—conceptually, this is the right next architectural step.** Inspecting `~/bob/eat.md`, `~/bob/2026/20261119.md`, and `~/bob/2026/2026-W47.md` side by side shows why the current layout feels fragmented once Record Cards hide H1 and `.inline-title`:

- On **albums** (`eat.md`), the reader currently passes through **four layers before reaching content**: `.inline-title` (`eat`) → Obsidian native `Properties` → `# Restaurants` → `.bob-album-header` (carrying `Body` crumb + `＋ restaurant` + `⊞ Schema` + `summary`, which itself largely duplicates line 36 below the H1!).
- On **daily files** (`20261119.md`) under `bob-cli-nh`, the stack is even noisier: `.inline-title` (`20261119`) → native `Properties` (6 metadata fields) → `# 2026-11-19 Thu` → `prev · W47 · next` → Intention Card (`DAILY INTENTIONS`).
- In Obsidian's **Outline pane** (`"outline": true`), a single top-level `# Title` forces every real section (`## Records`, `## Notes`, `## Events`, `## Pomodoros`, `## Review`) to nest one extra indentation level for zero navigational value.

Pulling the title into the property card and retiring redundant `# H1` lines establishes **one consistent rule across Bob's structured note types**: *structured notes open with a unified, self-describing hero Property Card instead of raw filename + boilerplate H1*.

### 3.2 Five Serious Gaps & Pitfalls If Built Naively

#### Pitfall 1: Empty Daily Files Go Title-Less (`309 / 311` Live 2026 Dailies + Every New Morning)
`plan:202611/period_intentions.md` (lines 88, 651) states: *"A note with none of the three fields shows no card."* A live vault scan of `~/bob/2026/` shows **309 of 311** canonical daily notes currently have neither Headline nor Reflection—and every freshly created daily note via `_templates/daily.md` starts with empty `intentions`, `summary`, and `reflection`.

If you remove `# 2026-11-19 Thu` from daily files while keeping `nh`'s empty-gate:
- Hiding `.inline-title` unconditionally leaves **309/311 daily files (and every new morning note before POST review) with zero page heading anywhere**.
- Gating `.inline-title` hiding on "card mounted" causes notes to display ugly numeric `20261119` all morning until `== o` is pressed, then abruptly swap chrome—exactly the visual jank you are trying to cure.

#### Pitfall 2: Albums Have No YAML `title:` Key (`derive_title` & `notebookHeaderNoteTitle` Depend on H1)
In `bob-cli/src/native/records/`, `title` is a first-class YAML property. By contrast:
- `src/native/albums/create.rs:66-95` writes `parent`, `type`, `summary`, `emoji`, `created`, `record:`, and then `\n# {title}\n`—with **no `title:` frontmatter key**.
- `src/native/albums/mod.rs:122-123` derives `declaration.title` via `derive_title(contents, aliases.as_deref(), &stem)` (`notebooks/scan.rs:796-836`), which resolves **H1 → `aliases[0]` → `humanize_stem`**.
- `bob-plugins/plugins/bob-ledger-tools/src/241e-plugin-notebook-header-model.js:177` (`notebookHeaderNoteTitle`) reads `frontmatter.title` **only when `types` is strictly `["record"]`**, otherwise falling back to H1 → `aliases` → stem.
- **5 of 6 live albums** have titles that `humanize_stem` **cannot reconstruct** if H1 is removed without persisting `title:` in YAML (`eat.md` → `"Eat"` instead of `"Restaurants"`, `tv.md` → `"Tv"` instead of `"TV"`, `sase_blog_zettel.md` → `"Sase Blog Zettel"` instead of `"SASE Blog Zettel"`). Moreover, `albums/update/ops.rs:295` (`ALLOWED_SET`) does not yet support editing album `title` (or `summary`/`emoji`) cleanly via `==`.

#### Pitfall 3: Nav Link Ordering Inversion (`prev · W47 · next`) & Hotkey Parsing
`~/bob/_templates/daily.md` puts `# 2026-11-19 Thu` on line 15 and `[[2026/20261118|prev]] · [[2026/2026-W47|W47]] · [[2026/20261120|next]]` on line 17. Meanwhile, `bob-navigation-hotkeys`'s `[n` / `]n` handler (`680-plugin-link-parse.js:17`, `670-plugin-project-files.js:829`) scans body Markdown lines after frontmatter for `prev` / `next` links.
- If `# H1` is dropped and the card anchors at the top of the body, **below** `prev · W47 · next` (`nh` placement rule), `prev · W47 · next` floats above the note's main title!
- If the card mounts **above** `prev · W47 · next`, you see nav links orphaned right under the card (or duplicated if nav controls also live in the card).
- **The proven pattern already exists in `bob-cli-ms` (`242k` / `242u` / `242v`):** keep the canonical `[[...|prev]] · [[...|W47]] · [[...|next]]` line in the Markdown body so `[n`/`]n`, Obsidian backlinks, Source mode, and mobile keep working unchanged, **render it cleanly as a docked nav rail on the card**, and **fold/hide the raw duplicate Markdown line in desktop Live Preview/Reading unless the caret moves onto it**.

#### Pitfall 4: Color Alone Fails (`eat.md` vs `eat/*.md` Collision & Accessibility)
Look at `styles.css:8534-8551` and `10996-11013`:
- Under `bob-cli-nh.6`, **Album**, **Bank**, and **Record** share 8px border radius, `2px` start border, `--bob-property-card-accent` from `[data-root-hue]`, and `color-mix` tint (`8%` vs `4%`).
- Every record inherits the **exact same `data-root-hue`** as its parent album (`eat.md` and `eat/ani_ramen_house.md` are both `green`; `movies.md` and `movies/9.md` are both `yellow`).
- `.bob-record-sheet-title` currently renders zero icon and zero album emoji (`242j:267-280`). Once Album Card also renders `--inline-title` at the top of a bordered green box, **an album and its records become visually near-identical twins** at a glance.
- Furthermore, `pomodoroHomeResolve` returns `null` for daily/period notes, defaulting them to `--interactive-accent` (Obsidian purple/violet), which collides visually with violet-area notes! And Obsidian / `bob-cli-nh` explicitly forbids conveying ownership or kind by color alone (`forced-colors: active` and color-vision accessibility).

#### Pitfall 5: Scope & Edge-Case Loose Ends
- **Period notes (`2026-W47`, `2026-Q4`, `2026`) vs Dailies:** Period notes run the exact same Intention Card, carry `aliases: ["2026-W47 · Nov 16 – 22"]`, and share the exact `H1 → nav links → Intention Card` sandwich (`~/bob/2026/2026-W47.md:13-28`). Unifying daily files without aligning period notes leaves the Intention Card inconsistent with itself.
- **Zorg historical dailies (`135 / 311` in 2026):** Pre-June dailies (`20260101.md`) have `generated_from_zorg: true`, no `aliases:`, no `# H1`, and start with `day::2026-01-01 Thu`. Attempting to store or migrate `title:` on those immutable files would churn history unnecessarily; **deterministic title derivation from canonical daily filename / period ID (`YYYYMMDD` / `YYYY-Www`) works across all 311 dailies with zero file edits!**
- **Empty-body Reading view mounting:** When an album or daily has minimal/frontmatter-only body (already observed on 46 H1-only records in `ms.8`), Obsidian's Markdown post-processor needs view-level fallback (like `mountRecordSheetFrontmatterOnlyViews` in `242k`). Generalizing that into `createPropertyCardHost` prevents blank pages when H1 is stripped.
- **Mobile `.bob-album-header` anomaly:** Unlike Record (`ms.8`) and Intention (`nh.7`) which are desktop-only, `241x:142-146` renders `.bob-album-header` on mobile too. Hiding `.inline-title` on mobile must remain **tied strictly to rendered-title ownership** (best: keep `ms`/`nh`'s clean desktop-only rule for title/Properties hiding, so mobile always fails open cleanly using `.inline-title` + visible `title:` / `aliases:` in Properties).

### 3.3 Alternative Approaches Considered

| Approach | Summary | Verdict | Why |
| --- | --- | --- | --- |
| **A. Keep `# H1` in Markdown; restyle sub-cards** | Leave `# H1` and `.inline-title` untouched; only add icons/colors to sub-cards. | **Reject** | Preserves double/triple stacked titles, noisy Obsidian Outline, and inconsistency with `ms.8` Record Cards. |
| **B. Keep `# H1` in Markdown; hide `<h1>` + `.inline-title` via CSS** | Leave `# Title` in files, hide first DOM `<h1>` when card renders. | **Reject** | Creates hidden-source divergence (editing heading in Source vs card), forces CLI/Templater to emit dead `# H1` scaffolding, breaks on notes starting with `# Intro` or H1-less Zorg notes, violates clean Vault-as-truth pattern (`ms.8` explicitly chose removing H1). |
| **C. Remove `# H1`, Move Title Into Card, Keep Empty-Gate Unchanged on Dailies** | Exact literal reading of prompt atop `nh`. | **Reject (Flawed)** | Breaks title visibility on `309/311` empty dailies & new mornings; breaks 5/6 album titles lacking `title:` YAML; orphans `prev · W47 · next`; leaves albums & records twin-colored. |
| **D. Unified Property Card Header + Fail-Open `ownsTitle` + Always-Mounted Temporal Leaf + Album `title:`** | Recommended architecture below. | **Adopt** | Clean Markdown files, zero empty-daily title blackout, exact album titles preserved, zero album/record color collision, fail-open on mobile/Source/embeds. |

---

## 4. Explicitly Called-Out Adjustments to Requirements

To make the feature **intuitive, reliable, and visually cohesive**, the following **five adjustments** to your original prompt are justified:

1. **Adjust Daily Card Mount Condition (`nh` Empty-Gate → Always Mount on Canonical Daily/Period Notes):** Instead of hiding the card when `intentions`/`summary`/`reflection` are empty, **always mount the Daily/Period Property Card on desktop Reading and Live Preview**, collapsing empty intention/summary/reflection sections into a sleek single-row header/title bar (+ subtle `＋ Set intentions` affordance on open days).
2. **Expand Scope from "Daily Files" to All Eligible Intention-Card Notes (`daily` + `W`/`Q`/`Y` periods, still excluding `all_time`) & Align `bank.md` Header Grammar:** Include `2026-W47`, `2026-Q4`, and `2026` notes in H1-to-card title unification so the Intention Card has one anatomy across every temporal scale, and add the matching eyebrow badge to `bank.md` so all 4 `.bob-property-card` species belong to one visual system.
3. **Introduce Explicit `title:` Frontmatter on Albums Before Removing Album H1s:** Mirror records by adding optional top-level `title:` to album frontmatter (`bob albums create`, `derive_title`, `notebookHeaderNoteTitle`, `Schema Card` update op, and an album H1-retire step) instead of relying on `aliases:` or stemming. Keep `aliases:` as Obsidian/templated canonical title store on daily/period notes, while deriving card titles deterministically from path/ID when `aliases` is absent (protecting all 135 Zorg 2026 notes).
4. **Dock & Fold Daily/Period Nav Lines Into Card Footers (Mirroring `bob-record-walk-rail`):** Keep `[[...|prev]] · [[...|W47]] · [[...|next]]` in the Markdown body so `[n`/`]n`, backlinks, and Source/mobile never break, while rendering them inside a clean card footer rail and hiding the duplicate body line unless cursor-selected.
5. **Distinguish Species Using a Multi-Channel Identity System Instead of Color Alone:** Pair a **type badge pill + bespoke SVG icon + border silhouette + surface contrast weight + title ornament** with dedicated non-area temporal colors (`--bob-day-accent`), eliminating album-vs-record same-hue ambiguity and meeting Obsidian accessibility (`forced-colors: active`).

---

## 5. Recommended Visual & UX Design

### 5.1 One Shared Card Grammar, Five Unmistakable Silhouettes

Every `.bob-property-card` adopts one predictable **4-zone vertical grid** while tuning **surface weight, accent geometry, eyebrow icon+pill, and title ornament** by species:

```text
╭─[Species Accent Silhouette]──────────────────────────────────────────────────╮
│ [SVG Icon · KIND BADGE]   [Context Crumb / Horizon]         [Actions] [▾]    │ 1. Eyebrow Row (UI-small)
│ [Leading Emblem / Date Tile]   Hero Title Text                               │ 2. Title Row (--inline-title)
├──────────────────────────────────────────────────────────────────────────────┤ ← 1px hairline divider
│  Species Body (Schema Fields / Record Chips / Intentions+Summary / Setup)    │ 3. Managed Content Bands
├──────────────────────────────────────────────────────────────────────────────┤ ← Optional footer divider
│  ‹ Prev Link              · Context / Progress ·                 Next Link › │ 4. Docked Nav Rail
╰──────────────────────────────────────────────────────────────────────────────╯
```

### 5.2 Species Visual Specification Matrix

| Visual Token / Element | **Album Card** (`album`) | **Record Card** (`record`) | **Daily Card** (`daily`) | **Period Card** (`period`: W/Q/Y) | **Bank Card** (`bank`) |
| --- | --- | --- | --- | --- | --- |
| **Visual Metaphor** | **Anthology / Collection Box** | **Catalog Dossier Sheet** | **Calendar Tear-Sheet** | **Horizon Ledger Banner** | **Financial Hub Card** |
| **Border Silhouette** | **3px solid left stripe** (`border-inline-start`) in `--bob-property-card-accent` | **1px uniform hairline border** (subtle `1.5px` start tint or top micro-notch — *not* thick left bar) | **3px solid TOP bar** (`border-top`) in `--bob-day-accent` (instant non-area shape!) | **2px TOP + 2px LEFT subtle corner frame** in `--bob-period-accent` | **2px left stripe** + double-rule eyebrow divider in `cash` accent |
| **Card Surface Tint** | **Rich Header (`12%`) / `7%` Body** root-hue tint | **Quiet Paper (`2–3%` tint over `--background-secondary` / `--background-primary`)** — calm contrast vs Album! | **Crisp Slate-Teal/Paper (`5%` temporal tint)**; live **amber ring** highlight only if `isToday` | **Soft Horizon Tint (`6%` slate-indigo tint)** | **8% `cash` root-hue tint** (matches existing bank identity) |
| **Bespoke 14px SVG + Eyebrow Pill** | `[library]` **`ALBUM`** (solid light pill, root-hue ink) + `Body` + `104 restaurants` | `[album.emoji or tag]` **`RESTAURANT`** *(noun badge!)* + `↑ Restaurants` link | `[calendar]` **`DAILY`** *(or glowing **`TODAY`** chip)* + `W47` pill | `[calendar-range]` **`WEEK 47`** / **`Q4 2026`** / **`YEAR 2026`** + `↑ 2026-Q4` | `[landmark]` **`BANK`** + `Cash` |
| **Title Row Ornament** | **30×30 Rounded Emoji Medallion** (`🍽️`, `📇`, `🎬`, `📺`) framing `frontmatter.emoji` | **Clean Hero Typography** (zero giant emoji box; focus on readable title + status pill right-aligned) | **Mini Calendar Leaf Tile** (`NOV` micro strip / **`19`**) beside **`Thu, Nov 19, 2026`** + faint `2026-11-19` ISO badge | **Muted Horizon Span** beside **`2026-W47 · Nov 16 – 22`** (or `Q4 · Sep 28 – Jan 3`) | **Crisp `🏦` or `[landmark]` emblem** beside **`Bank`** |
| **Body & Footer** | Summary paragraph (once!) + `＋ restaurant` / `⊞ Schema` + collapsible schema fields | Ordered schema chips (Status chip vivid) + collapsible field table + **Docked Walk Rail + progress thumb** | Compact Daily Intentions ①②③, Summary (`✦`), Reflection (`│`), OR clean `+ Set daily intentions` strip + **Docked `‹ Wed 18 · W47 · Fri 20 ›` rail** | Weekly/Quarterly/Yearly Intentions + Summary + Reflection + **Docked `‹ W46 · ↑ 2026-Q4 · W48 ›` + Day Strip pills** | Owned `bank:` accounts & categories summary (`==` opens setup modal) |
| **Collapsed State** | Title + Crumb + Summary snippet + Field count (`7 fields`) | Title + Noun pill + Primary Group Chip + `· N fields` | Title + Today chip + First intention preview (or `0 intentions`) + Docked rail | Title + Intention count / Summary status + Docked prev/next rail | Title + Account balances summary (`3 accounts · 18 categories`) |

> **Design highlight — Why Album vs. Record Stops Colliding Instantly:**  
> Even when `eat.md` and `eat/ani_ramen_house.md` share `data-root-hue="green"`, `eat.md` wears a **left-bound saturated green collection banner with a `🍽️` cover tile and `ALBUM · 104 RESTAURANTS` header**, whereas `ani_ramen_house.md` wears a **quiet neutral dossier surface with `1px` borders, a focused `🍽️ RESTAURANT` noun badge, and the bottom progress track**! And `20261119.md` immediately stands apart from *both* with its **top-accented Calendar Tear-Sheet border, `NOV / 19` leaf glyph, and slate-teal temporal palette** (`--bob-day-accent`)!

### 5.3 Visual Mockups (Desktop Reading / Live Preview & 375px Narrow)

#### A. Album Card (`eat.md` — `green` root hue)
```text
┏━━[3px green bar · 12% header wash]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  [⊞] ALBUM  ·  Body  ·  104 restaurants          [＋ restaurant] [⊞ Schema] ▾ ┃
┃  ╭────╮                                                                      ┃
┃  │ 🍽️ │  Restaurants                                                         ┃
┃  ╰────╯                                                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  Restaurants Kelly and I have tried, liked, or want to try.                  ┃
┃  status: required · 🔖 To try · 💚 Liked · 🚫 Not liked   category, location ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
(Directly below: curated body links [[eat.base]] · Related: ..., then ## Records)
```

#### B. Record Card (`eat/ani_ramen_house.md` — same `green` root hue, unmistakably distinct!)
```text
╭──[1px subtle border · calm 3% neutral sheet]─────────────────────────────────╮
│  [🍽️ RESTAURANT]  Body › ↑ Restaurants                  [🔖 To try] [⊞ Edit] ▾ │
│                                                                              │
│  Ani Ramen House                                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│  Category  Ramen             Location  cranford (z-241117-0b)                │
├──────────────────────────────────────────────────────────────────────────────┤
│  ‹ Amy's Omelette House            7 / 104                          B-Unos › │
│  ────────●────────────────────────────────────────────────────────────────── │
╰──────────────────────────────────────────────────────────────────────────────╯
(Directly below: ## Notes, or clean empty space if none)
```

#### C. Daily File (`2026/20261119.md` — with Intentions filled vs. Empty Day)
*Filled day (or yesterday with summary & reflection):*
```text
┏━━━━━━━━━━━━━━━━━━━[3px temporal teal top accent]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  [📅] DAILY  ·  TODAY  ·  W47                                    [⊞ Edit] ▾  ┃
┃  ╭────╮                                                                      ┃
┃  │NOV │  Thu, Nov 19, 2026                                      2026-11-19   ┃
┃  │ 19 │                                                                      ┃
┃  ╰────╯                                                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  INTENTIONS                                                                  ┃
┃   ①  Add ≥30 records to the sase_blog_zettel album                           ┃
┃                                                                              ┃
┃  ↑ W47 · Finish sase_blog_zettel album · sase-1n6 release train · …          ┃
┣──────────────────────────────────────────────────────────────────────────────┫
│  ‹ Wed Nov 18                     ↑ W47                         Fri Nov 20 › │
╰──────────────────────────────────────────────────────────────────────────────╯
(Directly below: - [x] #task [[gtd_daily]] ^gtd, then bob-plan strip, then ## Events)
```

*Brand-new or empty day (`intentions`/`summary`/`reflection` all empty):*
```text
┏━━━━━━━━━━━━━━━━━━━[3px temporal teal top accent]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  [📅] DAILY  ·  TODAY  ·  W47                                    [⊞ Edit] ▾  ┃
┃  ╭────╮                                                                      ┃
┃  │NOV │  Thu, Nov 19, 2026                                      2026-11-19   ┃
┃  │ 19 │                                                                      ┃
┃  ╰────╯                                                                      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃  ＋ Set daily intentions for today                                    == / o ┃
┣──────────────────────────────────────────────────────────────────────────────┫
│  ‹ Wed Nov 18                     ↑ W47                         Fri Nov 20 › │
╰──────────────────────────────────────────────────────────────────────────────╯
```
*(Notice: past closed empty days omit even the `＋ Set daily intentions` prompt—showing just the crisp Calendar Header + Docked Nav Rail—so historical Zorg days like `20260101.md` look clean without nagging!)*

#### D. Responsive Narrow Layout (`<= 375px`)
At `<= 375px`:
- Eyebrow row keeps `[Icon · BADGE]` + concise parent chip on left and collapse chevron `▾` on right, while action buttons (`＋ restaurant` / `⊞ Edit`) wrap cleanly below the title row (`flex-wrap: wrap`, matching `ms.8`).
- Mini Calendar Leaf stays `32×34px` compact inline-flex next to hero title.
- Docked Nav Rail hides verbose sibling titles when `@container (max-width: 28rem)` matches (`‹` · `7 / 104` or `↑ W47` · `›`), reusing the exact container-query mechanics proven in `.bob-record-walk-rail` (`styles.css:11503-11512`).

---

## 6. Technical Architecture & Implementation Contract

### 6.1 Title & Property Ownership (`bob-plugins`, `240b` & `createPropertyCardHost`)
1. **Replace record-specific `.inline-title` hiding (`styles.css:10985-10986`) with kit-level ownership:**
   Extend `propertyCardOwnKeys(scope, keys, options)` (from `240b-plugin-property-card-ownership.js`) with `{ ownTitle: Boolean(...) }` (while retaining `.bob-record-sheet-hides-properties` compatibility during transition):
   - When `ownTitle` is `true` AND the card's `.bob-property-card-title` DOM actually mounted cleanly inside a **desktop, non-embed, non-hover-popover, Reading or Live Preview** pane, add `bob-property-card-owns-title` to the view scope (`.markdown-source-view` / `.markdown-preview-view`—also mirrored onto `.cm-editor` via the host's `editorAttributes` facet so selectors work regardless of Obsidian DOM wrapper nesting!).
   - Selector contract (`styles.css`, generalizing lines `10985-10986`):
     ```css
     .cm-editor.bob-property-card-owns-title > .cm-scroller > .cm-sizer > .inline-title,
     .markdown-preview-view.bob-property-card-owns-title > .markdown-preview-sizer > .mod-header > .inline-title {
       display: none !important;
     }
     ```
   - **Fail-open guarantee:** Source mode, embeds, hover popovers, mobile (`Platform.isMobile`), mount failures, and plugin teardown automatically drop `bob-property-card-owns-title`, restoring Obsidian's native `.inline-title` alongside unhidden native Properties.
2. **Share Empty-Body Reading Mount Fallback in `createPropertyCardHost`:**
   Generalize `mountRecordSheetFrontmatterOnlyViews` (`242k`) into `createPropertyCardHost` so H1-less albums and body-less/minimal dailies render reliably in Reading View even when Obsidian emits no section `<p>` / `<h1>` children in `.markdown-preview-sizer`.
3. **Update `albumHeaderOptions` & Mobile Handling:**
   - Currently `241x:142-146` renders `.bob-album-header` on mobile too. Keep mobile card-title/Properties fail-open: on mobile, either omit the `.bob-property-card-title` row (keeping compact crumb+summary on `.bob-album-header` if desired) or never set `bob-property-card-owns-title` on mobile so Obsidian shows `eat` / `sase_blog_zettel` + `title:` in Properties cleanly.
4. **Update Daily/Period Nav Rail Mirroring (`680`/`670` Compatible):**
   - Keep `[[YYYY/YYYYMMDD|prev]] · [[...|Www]] · [[YYYY/YYYYMMDD|next]]` (and period sibling/day links) in body Markdown so `bob-navigation-hotkeys`'s `findFirstRenderedLinkInLine` (`[n`/`]n`) works with zero changes.
   - Render interactive docked nav controls at the card footer (`createPropertyCardFooterNav`) and add selection-aware decoration hiding in Live Preview + element hiding in Reading View ONLY for that exact single nav paragraph directly adjacent to frontmatter (`same pattern as 242k/242v walk line reveal`!). Move cursor onto that line in Live Preview → raw link text appears cleanly for Vim editing!

### 6.2 Color Tokens & Accessibility (`styles.css` — Theme Variables Only)
- Fix existing `data-root-hue="purple"` typo at `styles.css:11500` → `"violet"` (matching lines `5491-5545`) when moving cards onto `.bob-property-card` chrome tokens.
- Introduce temporal & species tokens strictly via Obsidian theme variables (so light & dark themes adapt automatically):
  ```css
  .bob-property-card {
    --bob-card-accent: var(--bob-property-card-accent, var(--interactive-accent));
    --bob-card-header-tint: 8%;
    --bob-card-body-tint: 5%;
    border-radius: 8px;
    border: 1px solid color-mix(in srgb, var(--bob-card-accent) 26%, var(--background-modifier-border));
    background: color-mix(in srgb, var(--bob-card-accent) var(--bob-card-body-tint), var(--background-primary));
  }
  .bob-property-card[data-card-species="album"] {
    --bob-card-header-tint: 12%;
    --bob-card-body-tint: 7%;
    border-inline-start: 3px solid var(--bob-card-accent);
  }
  .bob-property-card[data-card-species="record"] {
    --bob-card-header-tint: 3%;
    --bob-card-body-tint: 2%;
    border-inline-start-width: 1px;
    background: color-mix(in srgb, var(--bob-card-accent) 2.5%, var(--background-secondary, var(--background-primary)));
  }
  .bob-property-card[data-card-species="daily"],
  .bob-property-card[data-card-species="period"] {
    --bob-day-accent: color-mix(in srgb, var(--color-cyan, #0891b2) 55%, var(--color-blue, #2563eb));
    --bob-card-accent: var(--bob-day-accent);
    border-top: 3px solid var(--bob-card-accent);
    border-inline-start-width: 1px;
  }
  .bob-property-card[data-card-species="daily"][data-is-today="true"] {
    --bob-today-badge-accent: var(--color-orange, #d97706);
  }
  ```
- **Icon Rendering:** Implement a compact SVG glyph builder (`doc.createElementNS("http://www.w3.org/2000/svg", "svg")`, `viewBox="0 0 16 16"`, `stroke="currentColor"`, `stroke-width="1.6"`—following `130-freshness-marks.js`), so album, record, daily, period, and bank icons render crisp vector strokes in Node unit tests, desktop Obsidian, dark/light themes, and `@media (forced-colors: active)` (`CanvasText`) with zero runtime Lucide mismatch risk.

### 6.3 Album `title:` Frontmatter & `bob-cli` Updates
1. **`bob-cli` Album Frontmatter & Reader (`src/native/albums/` & `src/native/notebooks/`):**
   - Add `pub(crate) explicit_title: Option<String>` / YAML `title` support in `albums/mod.rs`: title resolution order becomes **`frontmatter.title` → first H1 → `aliases[0]` → `humanize_stem`**.
   - Update `albums/create.rs`: write `title: <title>` in YAML frontmatter right after `type: "[[album]]"` (matching records), stop emitting `\n# {title}\n` in album bodies, and keep only the `summary:` frontmatter without generating duplicate summary prose when redundant (preserve user-curated links like `[[eat.base]]` and `Related:`).
   - Update `albums/update/ops.rs`: permit editing album `title` and `summary` through guarded `bob albums update` / Schema Card editor (`==`) without touching `record.fields`'s `RESERVED_FIELDS` rule.
   - Add **`bob albums tidy`** (or extend `bob records tidy` pattern cleanly):
     - Dry-run by default (`-a` applies in one `vault_rewrite` commit).
     - Backfills missing YAML `title:` from existing exact H1 (e.g., `Restaurants`, `TV`, `SASE Blog Zettel`), then removes the redundant `# <Title>` heading matching `title:` (conservative: skips or flags if multiple H1s exist or first H1 meaningfully differs from frontmatter).
2. **`bob-plugins` (`241e` & `241u` & `241v`):**
   - Update `notebookHeaderNoteTitle` (`241e:177`) so **both `album` and `record`** check `frontmatter.title` before H1 → `aliases` → stem.
   - Update `albumHeaderOwns` to claim `["title", "record"]` (mirroring `nh.6` where record claims `["title", ...fields]` and `ownTitle: true`!).
   - Update `241v` Live Preview anchor (`albumHeaderLiveAnchor`) to mount immediately after frontmatter end when H1 is absent (and still handle legacy H1-present notes gracefully before H1 removal).

### 6.4 Daily & Period Note Scaffolds, Zorg Compatibility & Migration (`bob-cli` + `~/bob`)
1. **Deterministic JS/Rust Title Derivation for Dailies & Periods:**
   - **Dailies (`YYYY/YYYYMMDD.md`):** Derive from path `YYYYMMDD` (with `aliases[0]` / `# H1` confirmation fallback only for display if custom). Compute structured parts `{ weekdayLong: "Thursday", weekdayShort: "Thu", monthShort: "NOV", dayNum: "19", year: "2026", iso: "2026-11-19", isToday }`. Works uniformly on `20261119.md`, future dailies, and all `135` pre-June Zorg dailies (`20260101.md`)!
   - **Periods (`YYYY-Www`, `YYYY-Qn`, `YYYY`):** Derive from `periodNotesPeriodForPath` / `labels::title(id)` (e.g. `Week 47 · Nov 16 – 22`, `2026-Q4 · W40–W53`, `2026 · 53 weeks`). Keep `aliases:` on period/daily templates cleanly for Obsidian Quick Switcher & link completion (`[[2026/20261119|2026-11-19 Thu]]`), without forcing `title:` bloat onto 311 daily files!
2. **Templates & Scaffolds:**
   - Update `~/bob/_templates/daily.md`: remove `# <% moment(...).format("YYYY-MM-DD ddd") %>` (line 15); keep `aliases:`, `parent:`, `date:`, `type: "[[day]]"`, `[[...|prev]] · [[...|Www]] · [[...|next]]`, `^gtd`, and `bob-plan`.
   - Update `src/native/periods/scaffold.rs`: stop emitting `# {title}` on new week/quarter/year scaffolds while preserving `aliases: ["{title}"]` and nav lines (and allow `periods/problems.rs` & `unscaffolded` checks to accept H1-less canonical notes cleanly).
3. **Vault H1 Cleanup (Conservative):**
   - Extend `bob periods migrate` (with an idempotent H1-retire step, or scoped by `--since`) to strip `# <exact date/period title>` ONLY when it matches the canonical daily/period title and sits above nav/card content—leaving `## Review`, `## Events`, `## Pomodoros`, custom subheadings, and Zorg `day::` lines untouched.
   - Check `bob-cli` readers/tests (`periods/note.rs`, `periods/scaffold.rs`, `periods/problems.rs`, `albums/mod.rs`, `albums/create.rs`)—since none of `periods/note.rs` or `albums/catalog.rs` parse `# H1` structurally once `title:` / `id` is read, zero downstream breakage occurs.

---

## 7. Sequenced Delivery Plan (After `bob-cli-ms` & `bob-cli-nh` Land)

| Phase | Scope | Key Deliverables | Verification Gate |
| --- | --- | --- | --- |
| **1. Album `title:` Contract (`bob-cli` + `bob-plugins`)** | Persist `title:` on albums before touching H1s. | `albums/mod.rs`, `create.rs`, `update/ops.rs`, `bob albums tidy`; `notebookHeaderNoteTitle` reads `frontmatter.title` for albums. | Rust unit tests (`derive_title`, `create`, `tidy`); `just check`; all 6 live albums backfilled cleanly with `title:`. |
| **2. Unified Header & Chrome Kit (`bob-plugins`)** | Build shared `.bob-property-card-header` + `ownsTitle` + species identity tokens. | Shared header builder (eyebrow pill + bespoke SVG + `--inline-title` + docked footer rail), `bob-property-card-owns-title` CSS/JS, `purple`→`violet` fix, Album/Record/Bank header refresh + visual contrast split. | Unit tests (`property-card-ownership`, `album-header`, `record-sheet`, `bank-setup`), 375px + light/dark `preview-property-cards` renders, Obsidian E2E suites. |
| **3. Daily & Period Header + Nav Docking (`bob-plugins`)** | Always-mount Daily/Period card, compact empty state, docked nav rail, H1-less anchor. | Decouple Intention Card display from empty gate; mini Calendar Leaf (`NOV / 19`); `‹ prev · W47 · next ›` docked rail + selection-revealed body link hiding; extend Reading empty-body fallback. | Intention Card unit tests (filled, empty today, empty past/Zorg, period W/Q/Y); `obsidian-intention-card-e2e.cjs` (`[n==r`, cursor reveal on nav line, 2-pane, mobile/Source fail-open). |
| **4. Template, Scaffold & Vault H1 Retirement (`bob-cli` + `~/bob`)** | Retire redundant H1 lines cleanly once cards own them in production. | Update `~/bob/_templates/daily.md` & `periods/scaffold.rs`; dry-run + apply `bob albums tidy` and `bob periods migrate` H1 cleanup across live albums and canonical dailies/periods. | Vault scan confirming 0 broken album/daily/period titles, `[n`/`]n` parity, Obsidian Outline check, mobile screenshot spot-check, `bob plugins sync`. |

# Beautiful PDFs from area / project notes: research (`bob ref create`)

Researcher: mus. Independent report; conclusions are my own.

## Summary

`bob ref create report.md` renders raw vault Markdown through stock pandoc +
XeLaTeX with zero Obsidian preprocessing, in an academic-paper costume
(numbered sections, TOC, 10pt DejaVu Serif). Area and project notes are the
worst possible input for that pipeline: they are mostly task-machine text
(inline fields, block ids, schedule/cancel logs), `[[wikilinks]]`,
`![[embeds]]`, and dashboard sections. I verified all of this against the
current source and against `~/bob/lib/chat/sase_blog_v1.pdf` (6 pages,
pdfinfo: `LaTeX via pandoc`, `xdvipdfmx`, letter). The plan is worth doing —
shareable snapshots of notes are genuinely useful — but I would not implement
it as "make the Markdown route prettier". The Markdown route's contract
(Highlights-ready intake PDF: page-1 scan marker, `bob ref scan` pairing, a
reading task under `-P`) is the wrong contract for a note export. My
recommendation: a separate export path that (1) preprocesses Obsidian dialect
into clean reading text with an explicit task-metadata policy, and (2)
renders through the already-owned browser print template (the web-article
engine), not through LaTeX — with the pandoc route kept as the offline
fallback.

## What I verified (evidence, not inference)

- Markdown route passes the vault file straight to pandoc. `plan_markdown`
  (`src/native/highlights_ref/create.rs`, ~line 1863+) reads the file for
  title/stem derivation only; the resulting `CreatePlan.source` is the
  canonical vault path, and `render_temp_pdf` (~line 2317) invokes
  `pandoc <source> -o <render.pdf> --standalone --toc --toc-depth=3
  --number-sections --pdf-engine=xelatex … -V mainfont="DejaVu Serif" …`
  with two Lua filters (code-break/listen-card, return-links) plus the
  fvextra `header-includes`. There is no Obsidian-dialect handling on this
  path: no `[[wikilink]]`/embed resolution, no callout/dataview handling,
  no task-field stripping. (Wikilink helpers exist in `annotation_tasks.rs`
  / `marker.rs`, but they serve markers and annotation tasks, not the
  render.)
- Post-render, the PDF is marker-stamped with lopdf (Info Title/Author,
  page-1 scan marker, page-count check) for the `bob ref scan` pipeline.
- The actual artifact is ugly in exactly the predicted ways. `pdftotext` of
  `sase_blog_v1.pdf` shows: a `Contents` page reading `0.1 Tasks …
  0.1.1 Next & In Progress … 0.1.2 Blocked … 0.2 Screenshots … 0.5 Later
  Posts`; body text like `□ #task #prj My SASE post … [fresh:: 2026-10-15]
  [created::2026-06-11] #hide [id:: sase_blog__prj] ^prj`; raw
  `[[sase_blog_contents]]`-style references; schedule/cancel/work logs
  inline; `2 open · 1 next/wip · 2 blocked · 8 done/canceled` dashboard
  pills as flat text. Section-numbered reading prose (`## Requirements`
  became a numbered subsection of Done-tasks) confirms the template has no
  notion of note genre.
- The contrasting data point: web-article captures are explicitly "captured
  in reader mode and re-typeset with a Bob-owned print template; it never
  prints the live page" (`docs/highlights-create.md`), via a browser
  adapter (`clip_adapter.rs`: capture/compose protocol with `out_pdf`,
  headed-retry under Xvfb/off-screen macOS, `BOB_CHROME` override). So the
  project already owns the machinery for good-looking PDFs — the Markdown
  route just doesn't use any of it.
- Source material check: `~/bob/sase_blog.md` (a `type: [[project]]` note)
  mixes a `^prj` task line, per-lane task sections, `## Requirements`
  bullets with inline `[created::]` fields, `![[img/…|400]]` embeds,
  `~/tmp/screenshots/…` paths, and emoji callouts (`🧱 BLOCKS:`,
  `🗓️ SCHEDULE LOG`). Any renderer that doesn't take a position on each of
  these emits the v1 look.
- Toolchain present on this host (athena): pandoc 3.1.11.1, xelatex,
  typst 0.15.1, wkhtmltopdf 0.12.6 (patched qt), google-chrome. DejaVu +
  Inter + Noto Serif families installed.

## Critique of the plan

**Is it a good idea? Yes, with a scope correction.** Exporting a clean,
shareable PDF snapshot of an area/project note (send to a collaborator,
archive a decision, print a spec) is a real, recurring need, and
`bob ref create` is the discoverable place users will look. But "better
support in `bob ref create`" as stated conflates two jobs:

1. **Intake** (today's contract): produce a Highlights-ready PDF —
   page-1 marker, `source_pdf`/`marker_hash` bookkeeping, a reading task
   under a required `-P`, pairing via `bob ref scan`.
2. **Export** (the ask): produce a beautiful snapshot of a note the user
   authored — no reading task, no scan, destination near the note (or
   wherever asked), repeatable as the note evolves.

Forcing export through intake semantics gives nonsense like requiring
`-P sase_blog` to export `sase_blog.md` itself, stamping a scan marker
onto your own writing, and landing the file in `xlib/` awaiting a scan
that should never come. The adjustment I am calling out explicitly:
**ship this as an export operation with no marker, no `-P`, no scan —
even if it shares code with create.** Whether it surfaces as
`bob ref create --export/--print`, a new `export` subcommand, or a
top-level command is a naming decision (see CLI notes below), but the
pipeline must be allowed to skip intake.

**Second adjustment: the hard problem is content policy, not the PDF
engine.** Swapping XeLaTeX for Typst or Chrome while feeding it raw
`[dependsOn:: …] [id:: …] ^block-id` task text will still look bad. The
requirements need a written policy for, at minimum:

- task-machine metadata: strip inline fields (`[created::]`,
  `[fresh::]`, `[scheduled::]`, `[completion::]`, `[cancelled::]`,
  `[priority::]`, `[dependsOn::]`, `[id::]`), block ids (`^foo`),
  `#hide`, and machine pills — vs. keeping human-meaningful ones
  (priority? schedule dates?). My position: default-strip all machine
  fields and ids; keep checkbox state rendered as real checkboxes; keep
  schedule/completion dates only in an opt-in `--with-meta` mode.
- structural noise: schedule/cancel/work logs, `BLOCKS:`/`DEPENDS ON:`
  decoration lines, `2 open · 1 next/wip` dashboard pills, `^outline`
  anchors. Default: drop logs and pills; keep section headings.
- `[[wikilinks]]` → link text (display alias), with relative-path links
  resolved against the vault; dead/section links degrade to plain text
  (mirroring the existing dead-link report convention: warn on stderr).
- `![[embeds]]` → embedded images resolved against the vault (note:
  current `--resource-path` is just the source's parent dir, so
  vault-relative `img/…` embeds and absolute `~/tmp/…` paths break today;
  whatever engine is chosen must get an explicit resource map).
- callouts/emoji (`🧱`, `🗓️`, `❌`): map to styled admonitions or drop
  the glyph prefix; needs a font with emoji coverage or text
  substitution, else tofu boxes.
- frontmatter: never rendered as body (pandoc already handles this, but
  any HTML path must strip it too).

**Third adjustment: decide the update story.** Notes evolve; a one-shot
PDF rots. Either the export records its source revision (a `source_sha`
line in dry-run/success output, cheap) or there is a `--check`/re-export
flow. I recommend at minimum printing source mtime/sha in the success
report so staleness is detectable.

## Options considered

### A. Improve the pandoc/XeLaTeX route in place (custom template + preprocessing)

Preprocess Obsidian Markdown to clean GFM in a staging copy, then render
with a Bob-owned LaTeX template (title page, unnumbered sections, better
type, task-list environments, styled callouts).

- Pros: no new runtime deps (pandoc + xelatex already required for this
  route; doctor already diagnoses them, including the BasicTeX
  user-tree runbook in `docs/highlights-create.md`); keeps one pipeline;
  deterministic output; existing return-link pills keep working.
- Cons: beautiful LaTeX is genuinely expensive — every visual feature is
  a package, a conflict, or a BasicTeX `tlmgr --usermode install` support
  ticket (precedent: `needspace.sty`, 2026-10-10). Obsidian fidelity
  (embeds sized `|400`, callouts, task lists) is poor in LaTeX without
  writing a real template, which is a multi-day job to do well.
- Verdict: viable but highest effort-per-beauty; best as fallback, not
  flagship.

### B. Render through the Bob-owned browser print template (reuse the web-article engine)

Preprocess the note to clean HTML (or Markdown → HTML via pandoc), feed
it through the existing clip-adapter compose path (or a sibling op) so
note exports get the same reader-mode typesetting, masthead, page
numbers, and outline bookmarks that make article PDFs good; print with
the configured Chrome/Chromium headless flow including headed retry.

- Pros: best beauty-per-effort by far — CSS is where Bob's existing
  print design lives, and the adapter, scratch-dir, timeout
  (`BOB_WEB_CLIP_TIMEOUT_SECS`), executable override (`BOB_CHROME`), and
  headed-retry infrastructure already exist and are already debugged;
  task lists, callouts, images, and emoji are all trivially styleable;
  one visual language for articles and notes.
- Cons: makes the Markdown route need a browser (today it needs only
  pandoc/xelatex) — on browserless hosts this route must fail closed
  with the same quality of hint the web-article route gives, and the
  pandoc route stays as fallback. Also: the adapter protocol speaks
  article-JSON; note export wants a simpler "clean HTML in, PDF out"
  op — small protocol addition, but a real one.
- Verdict: **my recommended renderer.**

### C. Typst

Preprocess to clean Markdown, render with a Bob-owned `.typ` template
via the `typst` CLI.

- Pros: modern defaults look good with little work; single static
  binary, fast, no TeX distribution support burden; good task-list /
  callout primitives. Notably, typst 0.15.1 is already on this host.
- Cons: a brand-new required dependency for all users (MacBoy needs a
  Mac story — install size, font discovery); Obsidian preprocessing is
  still required (same content-policy work as every option); Typst's
  Markdown input is weaker than pandoc's, so the pipeline becomes
  Markdown→(pandoc or custom)→Typst source, adding a conversion seam;
  return-link pills and scan markers would need re-implementation in the
  new template; team familiarity is with the pandoc/Lua-filter stack.
- Verdict: attractive on paper, but it pays the preprocessing cost AND
  a new-toolchain cost while stranding existing filter work. Revisit if
  the browser route is rejected and LaTeX fatigue wins.

### D. weasyprint / wkhtmltopdf HTML-to-PDF without a browser

Same clean-HTML frontend as B, different backend.

- Pros: no browser dependency; pure-pip install (weasyprint); CSS
  paged-media is decent.
- Cons: wkhtmltopdf is abandoned upstream (patched-qt 0.12.6 is the end
  of the line — do not build a new feature on it despite its presence on
  this host); weasyprint is a new system dependency (pango/cairo) with
  its own font/emoji quirks and no existing Bob infrastructure, while
  option B reuses a browser Bob already requires for articles. I did not
  verify weasyprint availability on athena.
- Verdict: reject wkhtmltopdf outright; weasyprint only as a fallback
  if the browser dependency proves unacceptable.

## Recommended solution

1. **New export operation, sharing create's building blocks, not its
   contract.** Something like `bob ref export <NOTE.md> [-o out.pdf]`
   (exact noun/verb per `cli_rules.md` — note the membership-rule
   constraint below). Behavior: no `-P`, no marker stamp, no scan, no
   intake dedupe walk; default destination beside the source or under
   `lib/`-adjacent export dir (not `xlib/`); prints `pdf:`, `source:`
   (+ source sha/mtime), `pages:`, `images:`-style lines and dead-link
   `warning:`s in create's existing output voice.
2. **Two-stage pipeline: Obsidian-clean → clean HTML → Bob print
   template via the clip adapter (option B); pandoc/XeLaTeX stays as
   `--engine pandoc` fallback and for browserless hosts.** Stage 1 is
   the deliverable that matters: implement the content policy above as a
   tested pure function (vault note → reading Markdown/HTML), reusing
   `strip_obsidian_task_properties` conventions where they fit. Stage 2
   adds a minimal adapter op for note HTML so note exports share the
   article print CSS/masthead/pagination.
3. **Template defaults for the note genre:** title page from
   frontmatter/H1, unnumbered sections, real checkboxes, TOC only with
   `--toc` (default off for short notes — v1's always-on numbered TOC
   is half the ugliness), `bob-return-links` semantics unchanged where
   they apply.
4. **CLI-surface notes** (I read `cli_rules.md` for this): keep options
   alphabetical with short aliases (`-o`, `-T`-style overrides carry
   over); excellent `-h` output; if nested under `ref`, state the
   membership rule or keep the read-only export top-level per the
   task-verb guidance; never touch `bob capture` free-text space (not
   relevant here, but noted). No renames/removals involved.
5. **Verification bar:** golden-file test on a fixture project note
   (task lanes + logs + wikilinks + embeds + callouts) asserting the
   staged reading-Markdown exactly (pure function, cheap) plus one
   real-render smoke test per engine behind the existing
   binary-present skips (the codebase already uses this pattern, e.g.
   the `xelatex --version` skips in `create.rs` tests); `bob ref doctor`
   gains a row for the export renderer.

## Open questions for Bryan (not blockers)

- Should task checkboxes render state (`[ ]`/`[/]`/`[x]`/`[?]`) as
  distinct glyphs, or collapse to open/done? (I default to preserving
  state — it carries review meaning.)
- Keep `DONE & Canceled` sections in exports by default, or default to
  open-only with `--include-done`? For shared snapshots I'd default to
  open-only; for archives, everything.
- Is `sase_blog_v1.pdf`'s desired end state a one-shot artifact or a
  repeatable `export` of `sase_blog.md`? If repeatable, the
  source-sha-in-output item above becomes required, not nice-to-have.

## Sources inspected

- `src/native/highlights_ref/create.rs` (`plan_markdown`, `render_temp_pdf`,
  `PANDOC_HEADER_INCLUDES`, `PANDOC_CODE_BREAK_FILTER`), `mod.rs`,
  `clip_adapter.rs` (op protocol), `annotation_tasks.rs` / `marker.rs`
  (existing wikilink/task-text helpers), `docs/highlights-create.md`
  (routes, prerequisites, doctor rows, BasicTeX runbook),
  `sase memory read cli_rules.md` (CLI constraints),
  `~/bob/sase_blog.md` + `~/bob/sase_blog_contents.md` (input genre),
  `~/bob/lib/chat/sase_blog_v1.pdf` via `pdfinfo` + `pdftotext -layout`
  (6 pp, letter, xdvipdfmx; TOC and body quoted above), host toolchain
  versions (pandoc 3.1.11.1, typst 0.15.1, wkhtmltopdf 0.12.6, Chrome).
- Deliberately did not open any peer `__cdx/__cld/__grk/__gem` report in
  `sase/repos/research/202610/`; filenames seen only to avoid collision.

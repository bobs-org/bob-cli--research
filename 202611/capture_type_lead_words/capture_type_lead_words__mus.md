# Configurable task-type expansion on capture accept (`#fix` → `#fix Fix `)

Research report — `mus` (independent swarm member; no peer report consulted).
Question: how should bob-cli implement user-configurable task-type expansion
that fires when a `#` completion is accepted at the start of a capture?

## TL;DR recommendation

Implement it as **picker-accept expansion owned by `bob capture-complete`**,
configured per type in the bob config file (chezmoi-managed
`~/.config/bob/config.yml`), leading-edge only, new-task items only, with no
change when unconfigured. Concretely:

- Accepting `#fix` at the leading edge with `FIX.expand = "Fix "` (or
  equivalent) returns `replacement: "#fix Fix "` and
  `cursor_after` past the trailing space — the same channel that already
  appends the leading-edge space today.
- Do **not** implement keystroke/auto rewrite (no expand-on-space/expand-on-`#`),
  do **not** hardcode the five verbs, do **not** put the mapping in the Mac
  client, and gate everything on explicit config so empty config is
  byte-identical to today.

The rest of this note is the evidence and the reasons.

## What the request really is

Typing `#f` in an empty capture panel and picking `#fix` currently yields
`#fix ` (marker plus the existing leading-edge space) with the caret after
the space, ready to type the body. The request is that for five configured
types the same gesture yields `#fix Fix ` — marker, one space, a body seed
word, one space — so the common verb is already typed. The seed is body
prose, not grammar: `#fix Fix deploy flake` must parse exactly like a
hand-typed `#fix Fix deploy flake`.

That framing already answers two design questions: the trigger is
**acceptance of a completion candidate** (an explicit user gesture on an
offered row), and the product is **draft text**, not a stored field or a new
marker. Anything that fires on mere typing (space-expansion, `#`-expansion
via `capture-rewrite`) would be a different, more magical feature with undo,
double-expansion, and paste hazards the picker version avoids.

## How the machinery works today (verified in this checkout)

- `#<type>` lexing/parsing lives in
  `src/native/capture_language/type_marker.rs` (`scan_line*`,
  `collect_item`, `replacement_for`, `completion_at`,
  `task_type_completion_at`). Markers are legal only as free-standing tokens
  at either item edge; mid-line `#`, `#`+digit, `##`, `#-`, drawer bullets
  (`- #name`), and clock tags (`#off`, `#on`, `#offclock`, `#off-clock`,
  `#untracked`) are excluded by rule. One marker per item; the grammar for
  the marker itself is documented in `docs/capture.md` ("Typing tasks with
  `#<type>`").
- Completion-field detection is in
  `src/native/capture_language/completion.rs` (`completion_field_at_with`):
  the `type_marker::completion_at` claim runs before route/marker masking and
  yields `CompletionContext::TaskType` with a sigil-inclusive replacement
  range. `leading` (whether the marker occupies the leading edge) is computed
  by `type_marker` (`edge_run_is_transparent`) and threaded through.
- Candidate construction is in
  `src/native/capture_complete/task_types.rs` (`build_inner`, `candidate`).
  The JSON shape is `TaskTypeCandidate` in
  `src/native/capture_complete/model.rs`: `replacement`, `cursor_after`,
  `name`, `key`, `themes`, `origin`, `current/inherited/effect`, and friends.
  The wire contract for this context is documented in `docs/capture.md`
  (~line 10758): replacement covers the whole marker including `#`,
  `cursor_after` is the absolute caret offset after insertion.
- **The leading-space precedent already exists** (`task_types.rs`, `fn
  candidate`): `if leading && !next_is_whitespace { replacement.push(' ');
  }`, with `cursor_after = field.replacement.0 + replacement.len()`. So
  `#fix` at the start already becomes `#fix␣`. The requested feature is a
  strict generalization of this line: append `<seed><space>` instead of just
  `<space>` when configured.
- Bob Mac Capture is a thin client by decision
  (`decisions:mac-capture-is-a-thin-client`): it renders spans/candidates/
  previews bob returns and submits each draft as one `bob capture` call. Any
  expansion the Mac applied locally would violate that decision and fork the
  contract (including `bob capture-complete` for shell and `capture-parse`
  previews). Expansion therefore belongs in bob's `replacement` bytes, which
  every client already applies generically. No Mac change is needed for an
  MVP; an optional ghost-preview is additive later.
- Config today: `types:` in `~/.config/bob/config.yml` is a **flat mapping
  of name → color string** (`FIX: red`, `PLAN: auto`), parsed by
  `parse_themes_config` in `src/native/config/themes.rs`. Any non-string
  value (a mapping such as `FIX: {color: red, expand: "Fix "}`) is currently
  a hard config error. Bryan's live config uses exactly the short form
  (`BUILD`, `CHORE`, `FIX`, `MEET`, `PLAN`, `READ`, `WRITE` with palette
  slots). This constrains the config design: see below.
- There is a separate typing-assist channel, `capture-rewrite` (`rewrite.rs`:
  `expand_req_marker`, `expand_drawer_marker`, `expand_sigil_alias`), that
  rewrites the draft as the user types. It is the wrong channel for this
  feature (see "rejected alternatives").
- `bob capture-complete`/`capture-parse` responses already carry
  `grammar: 34` / `schema_version: 1` with additive-only evolution. A
  config-gated change to `replacement` bytes needs no schema bump; a new
  preview/annotation field would be `skip_serializing_if`-absent when
  unconfigured, preserving byte-identity.

Governing records consulted via the decisions roster: thin-client capture,
capture sigils (`@` where, `#` what, `%` how), clock-tag reservation,
bullets-mirror-the-task-block, and the release-train rule (no version or
changelog edits; `!` only for breaking CLI/JSON contract changes).

## Critique: is this a good idea?

**Yes, with the scope narrowed as above.** The Local reasoning:

- The five verbs (`fix`, `build`, `plan`, `read`, `write`) are genuinely
  high-frequency leading tokens, and seeding the body verb reduces typing
  without changing what the capture means — the expanded draft re-parses
  through the identical grammar, so there is no new semantic surface to
  learn. Discoverability is good: the user picks the same row they already
  pick; the draft just contains more useful text.
- The failure mode of the naive version (always append the capitalized word)
  is real but small: users who wanted `#fix` with a non-verb body
  (`#fix flaky test in auth`) would have to delete the seed. Configurability
  plus leading-edge-plus-empty-body gating is what keeps it from becoming a
  tax. The request already asks for configurability; the research conclusion
  is to take that further (per-type opt-in, default off, suppress whenever
  the item already has body text).
- The main risk is **magic creep**: once per-type text insertion exists,
  every type will want snippets, placeholders, cursor jumps (`Fix $1`),
  multi-line bodies, or route-specific seeds. The design below deliberately
  ships the smallest closed semantics (a literal body fragment, leading edge
  only, no placeholders, no cursor templating) and names snippet-tabstops as
  explicitly out of scope. The existing `CandidateContinuation { cursor,
  next_missing_field }` channel (used by record routes) is the natural
  future home for fancier "put the caret here" behavior, not this change.

**What I would change about the requirements:**

1. **Don't hardcode five types.** Make expansion a per-type config
   attribute; ship Bryan's five as his config values, not as code. New verbs
   then need no release.
2. **Don't fire "at the start of the capture" loosely — fire only on
   leading-edge accept into an otherwise body-empty new-task item.** Trailing
   markers (`Fix it #fix`), existing-task retypes (`@route+id #fix`), and
   items that already have body text must not expand. Appending body prose to
   a retype would silently rewrite someone else's task text; appending after
   existing body text would interleave words mid-sentence.
3. **Don't store this in chezmoi outside the bob config.** "Configured in my
   chezmoi repo" in practice means "in `~/.config/bob/config.yml`, which
   chezmoi manages" — that file is already the user-owned vocabulary source
   of truth (`types:`). A second config file or Mac-side setting would split
   the vocabulary from its expansions and break the thin-client contract.
4. **Require beauty work, not just bytes:** the candidate row should preview
   the expansion (ghost `Fix ` or a `detail`/`consequence` string) so
   acceptance is never a surprise, and Backspace immediately after accept
   must undo cleanly to the pre-accept draft (client already owns undo;
   server must keep the edit to one atomic replacement so it does).

## Recommended design

### Config shape (the one genuinely hard choice)

Today `types: {FIX: red}` maps names to color strings; a mapping value is a
config error. Two backward-compatible options:

- **Option A (recommended): allow string-or-mapping values.** `FIX: red`
  keeps working; `FIX: {color: red, expand: "Fix "}` adds expansion. Short
  string stays sugar for `{color: <that>}`. Pros: vocabulary and expansion
  stay in one block, one roster to read; per-type locality is beautiful.
  Cons: touches the `types:` parser and its error messages; YAML flow
  mappings are slightly noisier in chezmoi.
- **Option B: sibling block** (e.g. `type_expansions: {fix: "Fix "}` or
  `expansions:`). Pros: zero churn to the `types:` parser; trivially
  additive. Cons: two blocks can disagree (expansion for an unconfigured or
  unknown type; rename updates one but not the other); needs its own
  validation, duplicate-key, and reserved-name rules duplicating the
  `types:` ones.

Recommend Option A: the locality (`FIX`'s color and its seed side by side)
is worth the parser touch, and the parser already centralizes name/key
validation, reserved clock-tag rejection, and duplicate-key detection that
Option B would have to reimplement. Whichever is chosen, the rules are the
same:

- Keys are type names; match by normalized key (`normalize_component`), so
  `fix`, `FIX`, `Fix` all address the same entry.
- `expand` is an optional short literal body fragment. Suggested limits:
  max ~32 chars, single line (no `\n`), plain body prose only — validated by
  running the editor parser over a synthetic `#fix <expand>` draft and
  refusing expansions that lex as markers (`@route`, `#type`, `%directive`,
  `&`, `*`, `!`, `~`, `=`, URL, clock tag). Invalid `expand` degrades to no
  expansion plus a bounded warning (same pattern as the existing
  `themes_config_invalid` warning path), never a hard failure of completion.
- Reserved clock-tag names stay rejected, as today.
- `bob types rename`/`split` should carry or explicitly drop the `expand`
  attribute and say which in its output; at minimum rename must not silently
  orphan it.

Example (Option A) in Bryan's chezmoi-managed `config.yml`:

```yaml
types:
  FIX: {color: red, expand: "Fix "}
  BUILD: {color: yellow, expand: "Build "}
  PLAN: {color: auto, expand: "Plan "}
  READ: {color: green, expand: "Read "}
  WRITE: {color: violet, expand: "Write "}
```

Bare `CHORE: magenta` / `MEET: blue` entries keep today's behavior exactly.

### Completion behavior

In `task_types.rs::candidate`, after the existing leading-space logic:

1. Compute `leading` as today (already threaded in).
2. Compute suppression: expand only when **all** hold — `leading` is true;
   `subject == "new"` (not an existing-task retype/link/toggle); the item's
   body after the marker is empty or whitespace-only (no interleaving);
   the marker is not trailing; the `expand` value is present and valid.
3. When expanding: `replacement = replacement_for(name, key) + " " + expand
   + " "` (collapsing to a single separating/trailing space if `expand`
   already carries edge spaces), and `cursor_after = field.replacement.0 +
   replacement.len()` as today. When suppressed or unconfigured: today's
   bytes exactly.
4. Double-expansion safety falls out of the replacement-range design (the
   range covers only the marker), but add a test that accepting twice, and
   accepting with the body already equal to the seed, does not duplicate.
5. Optionally add an additive preview field on `TaskTypeCandidate` (e.g.
   `expansion_detail: "→ inserts 'Fix '"` or the literal seed) with
   `skip_serializing_if`, so the Mac/Obsidian picker can show ghost text.
   Keep it out of the MVP if it threatens scope; the `replacement` bytes
   alone are the feature.

### What must NOT change

- `capture-parse` planning, `capture` execution, and dry-run: the expanded
  draft must parse byte-identically to hand-typed text (property test:
  `accept(#fix) ≡ type "#fix Fix "`). No new grammar, no new marker, no new
  refusal code.
- Non-leading, existing-subject, drawer, notebook/record/close/start/adjust/
  shift/split/merge contexts: no expansion, today's bytes.
- Empty config: byte-identical responses (no schema bump, no `!`
  contract break; docs-only change plus additive optional field).
- Mac/Obsidian: no required change — they apply `replacement`/
  `cursor_after` generically. Preview rendering is an optional follow-up,
  coordinated with `bob-mac-capture` because the capture contract is shared.

## Rejected alternatives (and why)

- **Keystroke expansion in `capture-rewrite`** (typing `#fix␣` auto-appends
  `Fix ` without picking a row): more magical, fires without an explicit
  offer-accept gesture, complicates undo/redo and paste/bulk-template paths,
  and needs vault-free synchronous config reads in the rewrite hot path.
  The picker already has the user's explicit consent; use it.
- **Mac/Obsidian-local snippets**: violates
  `decisions:mac-capture-is-a-thin-client`, forks shell completion and
  `capture-complete` consumers, and hides user-visible behavior in a client
  Bryan doesn't version with the vocabulary.
- **Bulk `%t` templates or new `@`-routes per verb**: heavier ceremony for
  a one-word seed; templates remain the right tool for multi-row structure,
  not for seeding a verb.
- **Always-on capitalization echo** (every `#foo` appends `Foo ` with no
  config): surprises users with body text they didn't ask for, breaks
  trailing-marker and retype flows, and makes the five verbs special in code
  instead of in Bryan's config.

## Edge cases and reliability checklist

- Leading vs trailing: only leading expands; `Fix it #fix` is untouched.
- New vs existing: retype/relationship/link/toggle subjects never expand.
- Body already present (`#fix foobar`, `#fix Fix ` already typed): suppress
  (or equivalently, the accept range no longer covers the body — assert in
  tests).
- Next byte already whitespace: today's code skips the space push; the
  expansion path must still separate marker/seed/body with exactly one space
  each and never emit double spaces.
- Quoted literals (`#"DEEP WORK"` with `expand`): allowed only if the seed
  validation passes; replacement stays the literal form plus seed.
- Hidden/refused/typed-create rows: an `expand` on an unconfigured name
  must not rescue a `type_not_configured` refusal; expansion applies only to
  accepted rows.
- Case: query `#f` matching `FIX` expands to the configured seed verbatim
  (`Fix `), not to a case-folded query echo.
- Vault/clock interplay: seeds must never lex as `#off`-family clock tags;
  validator rejects them.
- Performance: config read stays on the existing once-per-load
  `ThemeSources` path; no per-keystroke vault I/O (completion already runs
  behind a deadline).
- Observability: invalid `expand` surfaces as the existing bounded config
  warning, visible in `capture-complete` warnings, not silent.

## Test and docs plan

- Unit: `types:` parser accepts string-or-mapping, rejects bad `expand`
  (multiline, marker-lexing, reserved, overlong) with degrade-to-absent;
  `candidate` appends seed + space leading/new/empty-body only; byte-identity
  when unconfigured; no double-space; no double-expansion; `cursor_after`
  exact.
- Integration: `capture-complete` JSON for `#f` → `#fix Fix ` on empty
  draft; suppressed on trailing marker, existing retype, and prefilled body;
  `capture-parse`/`--dry-run` of the expanded draft equals hand-typed draft.
- Docs: `docs/capture.md` task-type completion section (replacement rule +
  example), `docs/task-types.md` PT block for `expand` (naming, validation,
  rename/split semantics), and the config comment block in chezmoi. No
  `CHANGELOG.md`/version edits (release train); no `!` unless the team
  decides the `types:` value-shape widening is contract-breaking (it is
  additive and old configs parse unchanged, so it should not be).

## Open questions for Bryan (decision inputs, not blockers)

1. Seed wording: verb plus trailing space (`Fix `) vs verb plus colon
   (`Fix: `)? Recommend bare verb + space; colon belongs to Bryan's taste,
   and config makes it his call per type.
2. Should expansion also apply when the item has a route prefix
   (`@sase #fix` + accept)? It is still leading-edge for the marker; I lean
   yes when the body is otherwise empty, but it needs one explicit call.
3. Future ghost-preview in the Mac picker: worth a follow-up bead, not this
   change.

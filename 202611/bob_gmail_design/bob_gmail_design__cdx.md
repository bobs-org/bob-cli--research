# Gmail in Bob: selected conversation notes and deliberate sending

Researcher: **cdx** · Research date: **2026-11-05** · Account in scope: `bryanbugyi34@gmail.com`

This is an independent research report. I did not consult any other report, transcript, or finding from this research swarm. I inspected Bob's implementation, the installed `gog` interface, upstream source checked out through SASE, and primary documentation. I did not read the mailbox, resolve the example against the live account, create Gmail drafts, send mail, or change the vault. All proposed commands and note formats below are designs, not existing features.

**Recommendation:** build `bob gmail` as a selective bridge between correspondence and project work. Import chosen conversations into attractive, ordinary Markdown notes; replace capture URLs only after exact identity and durable storage are established; let Obsidian compose messages and hand them to Gmail drafts first. Add direct sending as an explicitly enabled later capability with durable receipts and conservative recovery. Reuse `gog` for authentication and API transport, while Bob owns identity, rendering, transactions, and the user experience.

There is one significant adjustment to the initial request: **an arbitrary modern Gmail address-bar URL is not a reliable API identifier.** A graceful selection fallback is necessary. A small Gmail-side “Copy to Bob” integration can eventually make the common case seamless without pretending every pasted URL is resolvable.

## 1. Is this a good idea?

Yes, for correspondence that supports an actual task, decision, or project. A conversation note gives a task durable context, allows backlinks and annotation, and keeps a useful record accessible while writing. Obsidian is also a good place to draft a considered reply alongside the relevant notes.

The return diminishes sharply if this becomes a second inbox. Whole-mailbox replication introduces duplicate unread states, newsletter clutter, attachment storage, privacy exposure, search maintenance, and uncertainty about which application owns a draft. Reproducing Gmail's inbox, spam handling, delivery controls, and HTML renderer would consume effort without improving the central workflow.

The useful boundary is: **Gmail owns correspondence and delivery; Bob owns selected records, working notes, and tasks.** An imported email is context, not automatically a task. Completing a task must not archive an email, send a reply, or change Gmail labels. Keeping a conversation should not automatically enroll the whole sender or mailbox in synchronization.

### Explicit changes to the requested requirements

| Initial expectation | Recommended requirement | Reason |
| --- | --- | --- |
| Any pasted Gmail URL fetches the email | Resolve supported identifiers exactly; otherwise preserve the URL and offer a message picker | Modern browser tokens are not documented API IDs |
| Replace the URL immediately | Replace from the local cache immediately, or after background import succeeds | Capture is currently offline and transactional |
| Store “the email” | Default to one selected conversation note, with stable anchors for individual messages | Most Gmail links identify conversations; replies need context |
| Render beautifully | Produce a coherent Bob reading layout, with faithful text and useful structure | Copying arbitrary sender HTML would undermine safety and consistency |
| Write and send from Obsidian | Deliver composition and explicit Gmail draft handoff first; direct sending follows after recovery guarantees are tested | Sending is irreversible and uncertain outcomes cannot be blindly retried |
| Other useful features | Prefer project links, explicit follow-up tasks, selected-thread refresh, and attachment retrieval | These extend the workflow without creating another inbox |

The thread default must remain visible: show “Save conversation · 4 messages,” not an ambiguous “Save email.” A “this message only” choice is useful for a very large thread or a sensitive sub-conversation. Saving a thread does not authorize automatic future imports of all new replies.

## 2. What the existing code makes practical

I inspected `bob-cli` at `2e91d45b01026b243466fb08d7d6a92527693dd3`, `bob-plugins` at `811f6508eec5781a1c824e8e1afc66f3c0e92bbe`, and installed `gog v0.44.0` at `cf42bb7c9f67d3369090de95a7b84ee258be9b02`. I also inspected current upstream `gog` at `efa67af399269df81defffa3be8642714281fc84` and InboxSDK at `5c87965314a0d751cd242ea474b2f9e2ff5a2dc4`. Release-specific conclusions below use the installed tag where noted.

| Existing foundation | Implication for Gmail |
| --- | --- |
| `gcal` invokes `gog` with JSON, timeout handling, an explicit account, an isolated `bob-gcal` client bucket, and read-only restrictions | Use the same transport pattern with a separate Gmail bucket; do not broaden Calendar's grant |
| `gkeep` separates fetching, planning, rendering, durable import evidence, and remote mutation | Reuse these principles, especially durable proof before any subsequent action; do not copy Keep's drain-and-archive semantics |
| Capture plans changes before committing and keeps preview and submission offline | Network enrichment belongs in an explicit preparation step or a durable background job |
| Public URL routing handles only eligible bare-URL items | Gmail recognition must also handle URLs embedded in ordinary capture prose |
| Public URL cleaning removes fragments; `google.com` and its subdomains are excluded by default | Gmail needs its own parser before public-reference classification; simply removing an exclusion is incorrect |
| `bob-command-mode` already has a CLI catalog, subprocess runner, writer serialization, and result presentation | Start with existing command infrastructure, then add a focused Gmail reading/composition surface |
| Bob reference notes have a specific reading-task/PDF/Highlights lifecycle | Correspondence should not silently become a PDF reference or create a reading task |

These are direct code observations: [Calendar transport](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/src/native/gcal/gog.rs), [Keep behavior](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/docs/gkeep.md), [capture contract](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/docs/capture.md), [URL policy](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/src/native/url_routing/policy.rs), [fragment removal](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/src/native/highlights_ref/clip_url.rs), and [Obsidian runner](https://github.com/bobs-org/bob-plugins/blob/811f6508eec5781a1c824e8e1afc66f3c0e92bbe/plugins/bob-command-mode/src/060-runner.js).

Audited project memory additionally establishes that new vault notes need a `parent` link, vault synchronization is Git-based, and the Mac capture app delegates parsing and vault mutation to Bob. Accordingly, the Gmail renderer belongs in Rust and its JSON contract; the Mac app and Obsidian present Bob's results. No OAuth token or Gmail parser should be added to the Mac capture client.

## 3. The difficult part: what does the pasted URL identify?

The example ends in `#inbox/FMfcgz…`. Four identities must stay distinct:

| Value | Meaning and treatment |
| --- | --- |
| Gmail API message `id` | Account-scoped identity of one message; use for retrieval and deduplication |
| Gmail API `threadId` | Identity of a conversation in that account; use for the conversation record |
| RFC `Message-ID` header | Email-level identifier useful for reply headers and exact search; not the Gmail API ID |
| Gmail browser token and `/u/0/` | UI navigation data; neither a proven API identity nor a durable account selector |

Google documents message IDs, thread IDs, parsed MIME payloads, and raw retrieval. It does not expose a browser permalink or an `FMfcgz` resolver in that resource. Its thread endpoint takes a thread ID. This does **not** prove that no undocumented transformation could ever exist; it means the public API does not provide the contract needed to promise universal URL import. [Message resource](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages), [thread retrieval](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.threads/get).

The installed `gog` normalizer extracts hexadecimal IDs from older `th=` and fragment forms. It leaves an opaque modern URL unchanged. InboxSDK's sync-to-legacy thread mapping uses a cache and, on a miss, an authenticated Gmail web request with page-provided headers. It is not simply a public-API token decoder. [gog v0.44.0 normalizer](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/cmd/webid.go), [InboxSDK mapping](https://github.com/InboxSDK/InboxSDK/blob/5c87965314a0d751cd242ea474b2f9e2ff5a2dc4/src/platform-implementation-js/dom-driver/gmail/gmail-driver.ts), [InboxSDK resolver](https://github.com/InboxSDK/InboxSDK/blob/5c87965314a0d751cd242ea474b2f9e2ff5a2dc4/src/platform-implementation-js/dom-driver/gmail/gmail-driver/getSyncThreadFromSyncThreadId.ts).

A recent primary issue report also describes this exact failure in Google's Workspace CLI. Its speculative explanation about encryption is **not** established by the evidence I inspected, and I would not repeat it as fact. The actionable finding is the missing supported mapping. [Workspace CLI issue #790](https://github.com/googleworkspace/cli/issues/790).

### Recommended resolution order

1. **Known local link:** look up an already confirmed association between account, original URL, and canonical IDs. Revalidate when necessary; keep the provenance of the association.
2. **Explicit API identity:** accept typed message/thread references and known older URL shapes, then verify the object through the authenticated account. Keep message and thread inputs distinct instead of guessing from an undifferentiated hexadecimal string.
3. **RFC identifier:** search using `rfc822msgid:`, then verify the result headers. Zero or multiple matches require selection; RFC headers are not a universal uniqueness proof. Gmail documents this search operator. [Message search API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/list).
4. **Opaque modern URL:** show “Choose the email for this link.” Offer bounded Gmail search with sender, subject, date, snippet, and message count. The user confirms the candidate. A URL's `inbox` segment is a historical hint, not evidence that the conversation is still in the inbox.
5. **No selection or no credentials:** retain the original link and the captured text. Mark enrichment as unresolved or awaiting sign-in. Never substitute the newest inbox item or the first similar subject.

For the common account, require `gmail.account: bryanbugyi34@gmail.com`. A browser's `/u/0/` can refer to another account on another device. Verify the authenticated account, for example through profile information where the adapter supports it; account mismatch is a useful, specific diagnostic. [Gmail profile API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users/getProfile).

### Making “copy this conversation” seamless

There are two credible Gmail-side helpers:

| Helper | Strength | Cost |
| --- | --- | --- |
| Small browser extension using InboxSDK | Can expose a one-click “Copy to Bob” action with account, canonical message/thread ID, and original URL | Depends partly on Gmail's changing web implementation; browser distribution and maintenance |
| Google Workspace Gmail add-on | Context events officially include `gmail.messageId` and `gmail.threadId`; narrower contextual access is possible | Another deployment surface; transfer into a local desktop workflow needs a prototype |

The add-on is the stronger supported identity source; a browser extension may provide the smoother personal desktop interaction. Do not commit to either without testing the actual transfer gesture. A copyable structured reference is sufficient initially; no remote service needs to receive email bodies. [Gmail add-on event fields](https://developers.google.com/workspace/add-ons/concepts/event-objects), [message UI extension](https://developers.google.com/workspace/add-ons/gmail/extending-message-ui), [InboxSDK conversation API](https://inboxsdk.github.io/inboxsdk-docs/conversations/).

**My choice:** ship an honest picker fallback first, and prototype the official add-on before choosing a browser helper. If single-gesture capture from Gmail is a launch requirement, this identity-transfer prototype is a prerequisite, not an item to leave until after the note renderer. Do not build a headless browser or cookie-reading service into `bob gmail`.

Outbound “Open in Gmail” links need similar humility. Preserve the original URL; also offer an account-qualified RFC-ID search link where possible. Treat URL formats as compatibility behavior that needs testing across cold browser loads and account orders, not as part of the REST API's identity guarantee. A generated link's failure must not compromise the local note. [Primary report of cold-link failures](https://github.com/googleworkspace/cli/issues/858).

## 4. The experience I would build

A capture such as:

```text
Ask Alex about the revised estimate https://mail.google.com/mail/u/0/#inbox/FMfcgz… @house
```

eventually becomes, schematically:

```markdown
- [ ] #task Ask Alex about the revised estimate [[mail/2026-11-05-revised-estimate--b27a73c19d41|Revised estimate — Alex]]
```

The task's existing Bob fields, route, creation date, block ID, and child bullets remain intact. Only the recognized URL token changes. If the user supplied a Markdown label, preserve it; generated labels default to **Subject — sender**, with an address fallback for missing names and “No subject” for missing subjects. Escape pipes, brackets, controls, and newlines; truncate only presentation, never identity. Do not rename the note every time its subject or participants change.

Capture preview shows one compact state:

- “Email · Revised estimate — Alex · already saved” when locally known.
- “Email · save after capture” for an exact new reference.
- “Email · choose conversation” for an opaque URL that needs confirmation.
- “Email · waiting for connection” when the work can safely remain queued.

These are distinct from successful imports. A failure leaves useful captured prose and a working original URL. Errors belong in the job/detail surface rather than repeated warning bullets in the task itself.

### Suggested note layout

The following is a mockup using fictional correspondence. `house` represents an existing chosen parent. The full canonical identifiers would be stored, not the abbreviated example values.

````markdown
---
parent: "[[house]]"
cssclasses: [bob-mail]
gmail_kind: thread
gmail_account: bryanbugyi34@gmail.com
gmail_thread_id: "18abc123def45678"
gmail_imported_at: "2026-11-05T15:00:00Z"
---

# Revised estimate

Alex Morgan · 3 messages · Saved 5 Nov 2026

[Open in Gmail](https://mail.google.com/…)

## My notes

Compare the revised materials allowance before replying.

## Conversation

> [!mail]+ Alex Morgan · 5 Nov, 09:14
> **From:** Alex Morgan <alex@example.com>
> **To:** Bryan
>
> Hi Bryan,
>
> Here is the revised estimate. The installation date is unchanged.
>
> | Item | Amount |
> | --- | ---: |
> | Materials | $420 |
> | Installation | $180 |
>
> **Attachments:** estimate.pdf · 84 KB · available in Gmail

^gmail-m-18abc123def45679

> [!mail]- Bryan · 4 Nov, 16:32
> **To:** Alex Morgan <alex@example.com>
>
> Could you separate materials and installation?

^gmail-m-18abc123def45670
````

Use a restrained envelope icon, theme-derived colors, readable line length, modest spacing, and a quiet header. Show the newest message expanded and older messages collapsed; maintain stable anchors and a clear date on each. Underlying source data retains the original chronological sequence. Keyboard actions provide **Refresh**, **Reply**, **Reply all**, **Compose**, and **Open in Gmail**. Do not store a clickable send action in imported Markdown.

Obsidian supports collapsible Markdown callouts and custom callout styling; an unsupported custom type still renders as a normal callout. This makes the note useful without the Gmail plugin and avoids an HTML-only artifact. Test the same note in Reading view, Live Preview, light/dark themes, and mobile reading. [Obsidian callouts](https://obsidian.md/help/callouts).

### Rendering fidelity and safety

Prefer a readable semantic representation over a screenshot of the sender's stylesheet. Preserve paragraphs, links, emphasis, headings, simple tables, code, lists, and meaningful inline images. The MIME renderer should choose a suitable alternative, preserve full source content, and label reductions such as unsupported layout. HTML-only messages cannot be treated as empty simply because no plain-text alternative exists.

Fetch the MIME tree, handle nested `multipart/alternative`, `mixed`, and `related`, decode base64url and character sets correctly, and fetch externally stored body parts when required. An empty `body.data` can mean a container or a body held behind `attachmentId`, not an empty email. [MIME part body resource](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages.attachments).

Treat sender content as data at every boundary:

- Remove scripts, forms, frames, event handlers, CSS imports, and network-loading HTML. No automatic remote images or tracking pixels, including CSS-based loads.
- Preserve normal text links with safe schemes; disallow active `javascript:`, executable `data:`, `obsidian:`, shell, and local-file destinations from sender content. Resolve or reject relative links deliberately.
- Escape Obsidian-specific syntax: imported `[[wikilinks]]`, embeds, block IDs, `#task`, inline fields, plugin code blocks, and managed-region delimiters must not gain Bob behavior.
- Do not pass email text through the capture grammar. A sender writing `@route`, a checkbox, or a command is not instructing Bob.
- Fold recognizable quoted history and signatures only as a reversible presentation choice. Never discard the only copy of a paragraph because a heuristic mistook it for a signature.
- List attachments by name, type, and size. Download explicitly; sanitize paths, reject traversal, hash content, enforce size bounds, and do not execute or recursively unpack attachments. Start with text and safe raster CID images; unsupported inline assets remain clear placeholders.

Obsidian sanitizes HTML but also has restrictions on mixed HTML/Markdown. That is useful defense, not a reason to trust a full email document or delegate all sanitization to Obsidian. [Obsidian HTML behavior](https://obsidian.md/help/html).

Keep original MIME on demand in a private source store; raw files are never rendered as active HTML. For ordinary imports, retain normalized content and provenance sufficient to re-render. If raw `.eml` preservation is enabled, explain its storage and sync policy: it may include attachments, Bcc, tracking URLs, and more private data than the visible note. Never download every attachment just to preserve raw source without making that consequence clear.

## 5. Persistence, refresh, and capture correctness

Use one note per `(account, API thread ID)`, with one message record per `(account, API message ID)`. RFC IDs and pasted URLs are alternate lookups, never the primary key. Store identity as strings without conversion through floating-point numbers. A readable filename can combine the initial date and subject with a collision-checked hash suffix; the complete identity lives in metadata. Note movement is supported by rebuilding an index from metadata, not by treating its original path as identity.

Keep correspondence outside `ref/` initially, for example under `mail/`, with `gmail_kind` rather than prematurely adding a new task or reference taxonomy. The `parent` follows the chosen destination on first import. A later capture from another project reuses the same note and adds a link; it does not silently reparent the original. User-authored tasks live in the parent project's task section. The mail note can display their backlinks without becoming an additional task inventory.

A practical separation is:

| Data | Location and ownership |
| --- | --- |
| Conversation Markdown and user notes | Vault, Git-synced; user section preserved byte-for-byte |
| Canonical imported content, render version, content digests, import receipts | Versioned `.bob/gmail/` records, with explicit Git inclusion checks |
| Requests from captures on other hosts | Immutable, uniquely named vault request records, consumed by one designated Gmail writer |
| Search cache, derived index, transport diagnostics | Host-local private state; rebuildable and body-free where possible |
| OAuth grants | `gog` credential store, outside the vault |
| Downloaded attachments and optional raw source | Explicit paths with a documented Git/sync policy; no assumption that an ignored file reaches another host |

Do not create an authoritative identity database only in `$XDG_STATE_HOME`: another host would re-import the same conversation. Conversely, do not sync OAuth tokens or transient search caches.

### Capture transaction

1. Parse Gmail references before generic public-URL cleaning. Preserve the fragment. Exclude code spans, code fences, escaped examples, and unsupported link forms. Test both parent text and authored capture bullets.
2. Dry-run performs local lookups only and plans the same task bytes and import intent as submission. It creates no files and contacts no Gmail endpoint.
3. Submission commits the task and a durable enrichment request together through the capture transaction. The original URL remains until the note exists. Existing-note links may be substituted immediately.
4. A worker fetches and renders into staged files. It validates the response account and IDs, writes content plus its receipt durably, then makes the note available.
5. Replace only the recorded occurrence after verifying the target task/block identity and original token are still present. A stale line number is not sufficient. Use expected bytes/digests and an occurrence discriminator; multiple identical links in the same block must remain distinguishable.
6. If the task was moved, resolve its stable identity. If edited, deleted, or ambiguous, keep the saved note and report “saved; link needs review.” Never perform an unrestricted vault-wide replacement.
7. Crash recovery uses the durable receipt to finish or recognize completed work. Retrying the same request must not duplicate the note, message, or replacement.

Reuse capture's commit machinery and the ref spool's durable-write patterns, but do not force Gmail through the PDF clipping pipeline. The current ref spool is host-local; cross-host Gmail requests need a deliberately synced design. [Capture planner](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/src/native/capture/plan.rs), [ref spool](https://github.com/bobs-org/bob-cli/blob/2e91d45b01026b243466fb08d7d6a92527693dd3/src/native/ref_jobs/spool.rs).

### Refresh semantics

Imported mail is a dated snapshot. `refresh` adds missing messages and updates Bob-owned metadata; it does not overwrite `My notes`, remove older locally saved messages, or imply that unread status is synchronized. A source deletion becomes a visible source-status observation, not a local deletion. Draft messages should be excluded from ordinary conversation imports by default because they have their own mutable lifecycle.

The generated conversation region needs a checksum. If the user edited it, retain the edit and offer a re-render preview instead of silently overwriting it. A no-op refresh should not rewrite timestamps on the note or create Git noise. Keep last-attempt status in a cache; change the note when content or meaningful state changes.

Start with manual refresh and explicit watching of selected conversations. Later, use Gmail history to reduce polling work. History is not a permanent event log: old cursors can return HTTP 404 and require rebuilding state. For Bob that means rechecking the selected set, not automatically importing an entire mailbox. [Gmail synchronization guide](https://developers.google.com/workspace/gmail/api/guides/sync).

Use **one designated Gmail writer** initially. Other hosts may search or enqueue imports; the writer updates shared notes and receipts after vault synchronization. A local file lock cannot coordinate two unsynchronized Git clones. Show queued work honestly when that writer is offline. Choose the active desktop as the initial writer if that best fits the existing command-mode workflow; headless automation can be configured later.

## 6. Transport, authorization, and operations

Prefer `gog` over a second OAuth stack. It is already installed, already integrated with Calendar, and exposes message/thread reads, attachments, searches, draft operations, raw MIME input, and send operations. Wrap it behind a small typed adapter with version checks and fake-executable tests; do not expose arbitrary `gog` command execution as Bob's public mail API.

For read operations use explicit account and client, JSON, no prompts, read-only runtime enforcement, and an exact command allowlist. Keep Calendar's `bob-gcal` grant isolated. A separate `bob-gmail-read` bucket is a reasonable default. Bucket isolation is local token organization; it must not be advertised as a guarantee that Google-side app revocation can never affect other grants associated with the same OAuth application.

| Capability | OAuth scope choice |
| --- | --- |
| Import/search/refresh | `gmail.readonly` |
| Optional direct sending from local drafts | Separate writer grant using `gmail.send`; retain the read grant for reconciliation |
| Create/update Gmail drafts, then send them | `gmail.compose`, with read access separately available |
| Archive, mark read, or apply labels to messages | Defer; these require broader capabilities such as `gmail.modify` |

Google classifies readonly and compose as restricted scopes, send as sensitive. Compose includes sending; there is no general draft-write-only OAuth safety boundary. `gmail.send` does not grant `drafts.send`. Avoid default full-mail access, settings, or permanent deletion scopes. [Scope catalog](https://developers.google.com/workspace/gmail/api/auth/scopes), [draft-send authorization](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.drafts/send).

The installed `gog auth add` supports `--gmail-scope readonly|send|read-send|full` and `--extra-scopes`. Its default Gmail service scope set is broader than this feature needs. Bob must request a tested minimal combination and inspect the resulting grant. For a draft bridge, test readonly plus explicitly added compose rather than accepting `full` merely because it works. Do not imply `read-send` permits draft creation. [gog scope implementation](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/googleauth/service.go).

Google documents a personal-use exception to verification for a small known user set. Separately, external apps left in Testing receive short-lived refresh tokens for these scopes; the documented duration is seven days. Setup should explain the consent-screen state and diagnose grant expiry without launching browser sign-in from a background worker. A published multi-user version would need a fresh verification and data-handling review. [Personal-use verification exception](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification), [refresh-token expiration](https://developers.google.com/identity/protocols/oauth2#expiration).

The existing SASE personal-Gmail skill is deliberately read-only and produces agent-safe text. That is not the full-fidelity product transport: `gog --sanitize-content` strips URLs and omits raw payloads. Bob needs to ingest the complete payload internally and perform its own deterministic rendering, while any future agent-facing summary can remain sanitized. This report used help/source inspection, not that skill to access private mail. [gog content handling](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/cmd/gmail_get.go).

Keep full message bodies, raw MIME, credentials, and attachment bytes out of diagnostic logs. Bound subprocess output and time, distinguish auth failures from throttling, and back off reads with jitter. Quotas changed in 2026 and can depend on project history; size polling from the active project's limits instead of copying older tutorials' figures. [Current Gmail quota documentation](https://developers.google.com/workspace/gmail/api/reference/quota).

A `doctor` command should check adapter capability/version, account, scopes, API access, writer identity, parent resolution, vault writable state, and whether required receipts/attachments are ignored by Git. These are relevant reliability checks, not another setup wizard on every capture.

## 7. Writing and sending from Obsidian

### First delivery: local composition, explicit Gmail draft handoff

Provide a small compose modal or an ordinary dedicated draft note, backed by `bob gmail`. A draft note contains recipients, subject, reply target, attachment references, and only the outbound body. Keep brainstorming in the linked project note so a broad “send this note” action cannot leak private working notes.

A fictional draft could look like:

```markdown
---
parent: "[[house]]"
gmail_kind: draft
gmail_draft_key: "local-unique-id"
gmail_account: bryanbugyi34@gmail.com
to: ["alex@example.com"]
subject: "Re: Revised estimate"
gmail_reply_message_id: "18abc123def45679"
attachments: []
---

Hi Alex,

Thanks for separating the costs. The revised estimate works for me.

Bryan
```

The UI offers **Preview email** and **Save to Gmail draft**. Saving the Markdown note is local only. No file watcher sends or publishes it. Preview displays the actual account, From, To/Cc/Bcc, subject, body, and named attachments. Bcc is explicit, not buried in a collapsed frontmatter field.

Render an outbound plain-text part and a conservative HTML alternative from a defined Markdown subset. Unresolved wikilinks, note transclusions, local file paths, and plugin code blocks must be resolved explicitly or rejected with a helpful message. Do not automatically expand a linked note into the outbound body. Attachments are selected files, with a resolved path and digest included in the preview.

“Save to Gmail draft” stores the returned draft ID and content digest. Offer a browser handoff to Gmail's Drafts view if an exact draft permalink cannot be verified. Let the user perform the first-release send in Gmail. This retains Gmail's mature recipient tools, rich editing, and delivery workflow while making Obsidian useful for the thoughtful part of writing.

Avoid continuous two-way draft synchronization. After handoff, mark Gmail as the editing owner. A later local edit requires an explicit “Replace Gmail draft” action that checks the remote baseline; if Gmail changed it, show a conflict. A read-before-update check reduces races but is not an atomic remote compare-and-swap, so do not promise conflict-free concurrent editing.

Google's draft ID is a stable container, while its contained message ID changes on replacement. Sending deletes the draft and produces a new sent message ID. Store these identities separately. [Draft lifecycle](https://developers.google.com/workspace/gmail/api/guides/drafts).

For replies, preserve the explicit target message, thread ID, `In-Reply-To`, `References`, and matching subject. Reply uses the sender's appropriate Reply-To address; reply-all shows the complete recipient set with Bryan's own addresses removed deliberately. Never infer reply-all merely because a message has several recipients. [Gmail threading requirements](https://developers.google.com/workspace/gmail/api/guides/threads).

### Later delivery: direct sending with a real recovery model

Direct sending from Obsidian is feasible. It should be an explicitly enabled capability, invoked by a deliberate final Send gesture after preview. The CLI should require an explicit prepared operation when noninteractive. Capture submission, task completion, note opening, and autosave never send.

A suitable lifecycle is:

```text
editing → prepared → approved → sending → sent
                                  └─────→ outcome_unknown → reconciled or manual decision
```

Preparation serializes the exact MIME bytes and freezes recipients, reply target, account, attachment contents, and a generated RFC Message-ID. The approval is bound to their digest and expires after any edit. Persist a receipt before the request, issue one deliberate submission, and record the returned Gmail message/thread IDs after success. Gmail accepts MIME through the `raw` field; its public send method documents no application idempotency-key parameter. [Sending guide](https://developers.google.com/workspace/gmail/api/guides/sending), [send API](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send).

If the connection disappears after Gmail may have accepted the request, mark **outcome unknown**. Search Sent by the preserved RFC Message-ID and verify candidate headers/content. A found match can settle the operation; no immediate match is not proof that nothing was sent. Do not automatically resend. A vanished Gmail draft is also not proof of sending: it might have been deleted elsewhere.

A generated Message-ID helps reconciliation; it does not make Gmail exactly-once. Test whether the chosen submission path preserves it. Use a single designated sending host, local mutual exclusion, and a durable operation record to stop repeated UI clicks. Git-synced files cannot serve as a distributed send lock. Changing the sending host requires resolving in-flight or uncertain operations first.

**Specific adapter concern:** the inspected `gog v0.44.0` transport retries rate-limit/server-error responses for replayable requests. Its Gmail send and draft-create paths do not use the available `WithoutRetries` context marker. Therefore “Bob called gog only once” does not prove one HTTP submission. Before shipping direct send, add or obtain a verified single-attempt write path, or use a narrow alternative transport for these writes; verify both normal and raw send and draft creation. This is a source-based risk finding, not an observed duplicate email. [Retry transport](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/googleapi/transport.go), [send implementation](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/cmd/gmail_send.go), [draft implementation](https://github.com/openclaw/gogcli/blob/cf42bb7c9f67d3369090de95a7b84ee258be9b02/internal/cmd/gmail_drafts.go).

Do not advertise Gmail web's Undo Send for an API send. A local countdown can delay submission and allow cancellation before the request, but it cannot recall a completed delivery. If this recovery work feels disproportionate, keep the Gmail draft handoff as the long-term default; it provides most of the composition value.

## 8. Additional features worth their complexity

| Feature | Priority | Boundary |
| --- | --- | --- |
| Search Gmail and insert a selected note link from Obsidian | High | Exact selection; bounded queries; no unsolicited mailbox import |
| “Create follow-up task” from a message | High | Explicit task creation in the chosen parent with a message anchor |
| Save selected attachments | High | Explicit download with size/path safeguards and a clear sync policy |
| Refresh this conversation | High | Add new messages; preserve notes and imported history |
| Manual import of a Gmail label such as `Bob/Save` | Medium | User applies the label in Gmail; Bob deduplicates without removing it |
| Watch a small selected set for replies | Medium | Show a count or badge; no automatic task completion or inferred “resolved” status |
| Search or export imported mail offline | Medium | Derive from local notes/records; avoid a second full-mail index |
| Whole inbox mirroring, archive/read-state synchronization | Low | Adds ongoing coordination and broad scopes without improving project context |
| Automated email summaries or replies | Defer | Not needed for deterministic import; introduces fidelity and data-transfer decisions |
| Scheduled sending | Defer | Requires durable scheduling, host ownership, and unknown-outcome recovery |
| Read tracking or pixel injection | Omit | Adds little value to this personal workflow and conflicts with quiet, reliable correspondence |

A label-driven import is particularly useful because it offers a Gmail-native selection gesture without needing to resolve a browser URL. It is a complementary entry point, not a substitute for the capture flow.

Start with polling only selected conversations. Gmail push introduces Pub/Sub, subscription handling, renewal, and history recovery. Google itself recommends polling for user-owned devices, and watches need renewal at least every seven days. That is excessive for a first personal integration. [Gmail push guidance](https://developers.google.com/workspace/gmail/api/guides/push).

## 9. Public command shape and implementation boundaries

`gmail` is a noun group: all members operate on Gmail connections, selected correspondence records, or associated drafts. A bare `bob gmail` should be a flag-only read-only status or saved-conversation list, consistent with Bob's CLI rules. Sketch:

```text
bob gmail                         # local status and saved-conversation overview
bob gmail doctor
bob gmail login
bob gmail logout
bob gmail search QUERY
bob gmail import REFERENCE
bob gmail refresh NOTE
bob gmail jobs
bob gmail open NOTE
bob gmail compose
bob gmail reply NOTE
bob gmail drafts preview NOTE
bob gmail drafts publish NOTE     # explicitly create/update a Gmail draft
bob gmail drafts send NOTE        # later, explicitly enabled direct send
```

These are proposed names. Before implementation, settle whether `drafts` includes only Bob-managed drafts; I recommend yes, so the command cannot unexpectedly operate on every Gmail draft. Add aliases for every public long option, alphabetical help ordering, versioned JSON, precise typed errors, and full command-mode catalog metadata. `--dry-run` must disclose whether a particular command reads Gmail; capture dry-run remains strictly offline.

Keep parsing, MIME normalization, rendering, identity, vault transactions, and send preparation in `bob-cli`. Keep Obsidian's surface thin: picker, reader actions, draft editor, preview, explicit approval, and status display. Reuse `bob-command-mode` infrastructure rather than introducing a second unmanaged subprocess layer. Coordinate additive capture JSON fields with `bob-mac-capture`; it should display import state returned by Bob.

A provider trait around a tested subset of `gog` gives room for replacing the adapter later without changing note identities. Native Gmail REST is the fallback if `gog` cannot meet a concrete requirement such as reliable write retry control; it is not the default excuse to build another token manager. IMAP/SMTP would add protocols while still needing Gmail-specific thread and OAuth behavior. A third-party Obsidian mail plugin is a reasonable renderer prototype, but would split responsibility for Bob's task/capture contracts and credentials. Public-page scraping is unsuitable for authenticated email.

## 10. Delivery order and proof required

### A. Resolve the uncertainties before polishing

Run a small, explicitly authorized live spike with selected nonsensitive messages:

- Try the exact modern URL, an older hex link, a message reference, and an RFC-ID reference through the proposed resolver. Record success and unsupported cases; do not infer success from parser acceptance.
- Check account-order changes and opening Gmail from a cold browser tab. Verify that a link cannot silently select a different account.
- Prototype a Gmail add-on's canonical-ID transfer and compare its click count to a picker. This decides whether seamless URL capture is worth another component.
- Verify minimal scopes on the installed adapter, including readonly-plus-compose and account identity checks.
- Render a plain-text reply chain, an HTML-only email, a table-heavy receipt, a CID image, a long attachment-backed body, and a non-UTF-8 message. Show these in Obsidian, not just as raw Markdown.

These were not performed against the live mailbox during this research. Their results may change the helper choice and exact renderer libraries, not the ownership boundary.

### B. Ship selected read-only imports

Implement login/doctor, exact IDs and picker, one canonical note per thread, deterministic rendering, local index rebuilding, and explicit import/refresh. Start with attachments listed and explicitly retrieved. This has the smallest scope and gives useful artifacts immediately.

### C. Add capture enrichment and Obsidian actions

Add Gmail-aware token recognition before fragment stripping, durable requests, conservative occurrence replacement, and recoverable jobs. Add the Obsidian picker and native callout styling. Validate the Mac app's preview/submit protocol. Release this only when offline capture and edited-task recovery are boringly reliable.

### D. Add composition and Gmail draft handoff

Create local draft notes, exact outbound preview, explicit publish, and conflict-aware replacement. Confirm that approval never includes user notes or implicit transclusions. Handle uncertain draft creation without repeatedly creating duplicates.

### E. Enable direct send only after the write path is proven

Test one-attempt transport, approval invalidation, crash recovery, duplicate-click prevention, identity reconciliation, and sender ownership. Send only test messages to an explicitly approved test destination during verification. A passing read-only import suite does not justify enabling sending.

### Acceptance tests that matter

| Area | Required evidence |
| --- | --- |
| Identity | Opaque URL never becomes an arbitrary recent email; wrong account fails clearly; missing/duplicate RFC IDs require selection |
| Capture | Dry-run and submit issue no Gmail calls; a mixed batch remains atomic; failures preserve original text; identical URL occurrences remain distinct |
| Recovery | Crash after note creation but before URL replacement is safe to resume; moved or edited tasks are not corrupted |
| Deduplication | Re-import and refresh are idempotent; note rename and index deletion do not duplicate records; another host uses shared identity evidence |
| Rendering | MIME alternatives, charsets, nested parts, encoded headers, quotes, tables, and HTML-only messages stay intelligible |
| Inert source content | Embedded task syntax, wikilinks, plugin blocks, active links, and malicious HTML gain no local behavior; rendering makes no external image requests |
| User ownership | Notes, chosen parent, and custom link labels survive refresh; edited generated regions produce a reviewable conflict |
| Attachments | Traversal, duplicate filenames, large files, missing CID parts, ignored Git paths, and unsupported types have visible, safe outcomes |
| Composition | Preview matches exact serialized recipients/body/files; attachments changing after preview invalidate approval; private notes are never included |
| Sending | Server accepted then connection lost becomes unknown, never an automatic resend; repeated clicks and competing hosts cannot submit the same operation |
| Presentation | Reading view and Live Preview, keyboard access, light/dark themes, long subjects, empty subjects, Unicode, and mobile reading remain usable |

Use fake adapters and crash/failure injection for the automated suite. Rendering fixtures should be synthetic or explicitly sanitized. Keep public test fixtures and this research free of real mailbox content.

## 11. Costs, limitations, and decisions to revisit

The highest engineering risks are URL identity, faithful inert MIME rendering, and non-idempotent writes—not the REST calls. The URL helper and direct sending should have separate go/no-go decisions so neither delays useful read-only imports indefinitely.

A thread snapshot copies personal correspondence into the vault and its Git history. Deleting its note later does not erase prior commits or backups. This is a practical reason to select messages deliberately and make raw-source/attachment retention explicit. Verify the actual vault repository exposure and sync policy during rollout; I did not inspect private vault configuration for this report. Avoid sending these contents to AI services as part of basic import.

Mobile can read and edit Markdown, but a desktop subprocess integration does not automatically run on mobile. Initial mobile support is reading imported notes and editing local drafts; publishing or sending requires the designated desktop writer. Make this limit visible instead of silently queuing a send for later.

No supported browser-token mapping was found, but absence of a contract is not proof of cryptographic impossibility. No live test of the user's example was run. No actual duplicate send was observed. No claim is made that Gmail guarantees Message-ID deduplication, transactional draft updates, or API Undo Send. These limits are precisely why the design has a selection fallback, snapshot ownership, and an unknown-outcome state.

## Recommended solution

**Implement `bob gmail` as a selective correspondence companion, using `gog` through an isolated, typed adapter.** Start with exact-identity imports and an honest picker for opaque Gmail URLs. Give each selected conversation a stable, beautifully rendered Markdown note under `mail/`, with a valid parent, message anchors, a link back to Gmail, and a protected space for Bryan's notes. Preserve the original capture URL until the note is durable, then replace only the intended occurrence. Keep all capture preview and submission paths offline.

Add explicit local composition and Gmail draft handoff next. Treat direct send as a separate, opt-in capability whose approval freezes the exact message and whose recovery never blindly resends. Use one writer for shared imports and sends until a stronger coordination design is justified.

This delivers the valuable part of the idea—correspondence attached to real work, pleasant to read and easy to reply to—without turning Obsidian into another inbox. If the picker is too much friction, invest in the Gmail-side canonical-ID handoff; do not compensate with fuzzy automatic matching. If reliable direct sending costs more than its convenience is worth, retain the Gmail draft handoff as the default workflow.

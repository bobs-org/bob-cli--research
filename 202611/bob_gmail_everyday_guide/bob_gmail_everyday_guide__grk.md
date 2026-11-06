# Get the most from Bob Gmail

> **Research query.** Write a concise, easy-to-understand user guide for the
> `bob gmail` integration (epic `bob-cli-hg`) that walks Bryan through how to
> get the most out of it. Focus on the user experience, not the
> implementation.

**Researcher.** `grk` (independent swarm report).
**Date.** 2026-11-06.
**Scope.** Research only. This file is the deliverable: a user-guide draft
the lead can lift into `docs/guides/`. No bob-cli, plugin, vault, or memory
files were changed.

**Primary evidence.** Epic bead `bob-cli-hg`; approved plan
`plan:202611/bob_gmail.md`; design
`research:202611/bob_gmail_design/bob_gmail_design.md` (accepted R1–R8);
`docs/gmail.md`; `docs/guides/connect-google-mail.md`;
`docs/reference/cli/gmail.md`; `docs/reference/configuration.md` § `gmail`;
`docs/guides/capture-from-your-mac.md`; `docs/guides/drain-google-keep.md`;
`docs/guides/run-bob-from-obsidian.md`; glossary `inbox-file`; reviewer
decisions `default_body = full`, `link_label = subject_who`.

**Landed today (bob-cli-hg.1–6).** `login`, `logout`, `doctor`, `save`,
`list`. **Still in this epic.** Link, capture, search/peek, Bob Mail plugin,
Mac Capture preview, compose/send, pull, attachments.

---

## Bottom line

Write **one walkthrough, then split it into three published guides** when
the remaining phases land. The walkthrough below is that draft.

Gmail stays your mailbox. Bob keeps **one mail note per thread you attach to
a task**. You save threads you chose, annotate them next to the work, and
send only through a previewed Gmail draft. Use the picker, paste, capture,
and the `bob` label — copying a URL from the address bar is the fallback,
not the daily path.

Until link, capture, plugin, compose, and pull land, the daily loop is:
sign in, `bob gmail save <URL>`, open the note, write under `## Notes`,
link it from a task by hand. Everything after *Bring a thread in* except
plain `save` / `list` is the intended product of this epic.

---

# User guide: attach Gmail to the work it belongs to

This guide gets a Gmail thread into the vault as a readable mail note, links
it from a task, and (once compose lands) replies from Obsidian. It assumes
Bob is installed, pointed at your vault, and [gog](https://github.com/openclaw/gogcli)
≥ v0.44.0 is on `PATH`.

## What a mail note is

A mail note is a snapshot of **one Gmail thread** at
`mail/<year>/<date>_<subject>.md`. Gmail remains the live mailbox. The note
is the copy you annotate, search, and link from tasks.

When you open one you see:

- the subject, **Open in Gmail ↗**, and a one-line summary
  (`Dana Whitfield ↔ you · 3 messages · Sep 19 → Nov 3`)
- **`## Notes`** — yours; refresh never touches it
- **`## Conversation`** — one card per message: others in blue, yours in
  green and indented; older cards folded, the newest open; quoted history
  and signatures folded away

The task link reads `✉️ Lease renewal for 14 Elm St · Dana Whitfield`.
Subject says *what*, the other person says *who*.

Save only correspondence that supports a task, decision, or project. Leave
the rest in Gmail.

## Once: connect Gmail

Follow [Connect Google Mail](https://bobs-org.github.io/guides/connect-google-mail/)
for the Cloud Console screens. The short version:

1. Put a `gmail:` block in `~/.config/bob/config.yml` (a missing block uses
   defaults):

   ```yaml
   gmail:
     account: you@example.com
     body: full
     folder: mail
     link_label: "✉️ {subject} · {who}"
     never_save:
       from: []        # addresses or @domains
       labels: []      # Gmail label names
     pull:
       inbox: gmail_inbox.md
       label: bob
     signature: gmail
     timeout_secs: 60
     writer: mac-host  # the host slug that may write mail notes
   ```

2. On the Mac (the recommended writer):

   ```bash
   bob gmail login -s compose
   bob gmail doctor
   ```

   On every other host, `bob gmail login` is enough (read-only). Confirm
   every doctor row is `ok` or an explained skip.

3. Pin `gmail.writer` to the Mac's vault-sync hostname slug so saves,
   links, pulls, and sends run there. Other logged-in hosts can still list
   and read.

Rerun `bob gmail login` after a Google password change, after a token sits
idle for six months, or if the consent screen is still in Testing (those
tokens last seven days). Logout removes only Bob's Gmail grant; Calendar
and Keep stay connected.

## Bring a thread in

Pick the door that matches where you already are. Every door ends at the
same mail note and the same labelled wikilink.

| You are… | Do this |
| --- | --- |
| In Obsidian, looking for a thread | **Bob Mail: Link email…** — recent threads, type to search, Enter saves and inserts the link at the cursor |
| In Gmail in the browser, copying the address bar | Paste the URL into the editor. Paste-to-link saves the thread and swaps the URL for the labelled link |
| Capturing a task on the Mac | Paste the URL into the capture draft. Submit writes the task at once. About two seconds later the URL becomes the labelled link |
| On your phone | In the Gmail app, apply the `bob` label. Later run `bob gmail pull` (or the Command Mode row) |
| At a terminal, or Command Mode | `bob gmail save <URL>` |
| Sitting on old Gmail URLs already in the vault | `bob gmail link -a -d` to preview a backfill, then drop `-d` |

A URL that Bob cannot confirm stays as you typed it. An already-saved
thread links immediately. A `[your words](gmail-url)` you wrote keeps
*your words* as the link label.

**Today:** `bob gmail save URL|ID|NOTE...` is the working door. Preview
with `-d` (paths and structure only; message prose stays out of the
preview). File a new note under an area or project with `-P workshop`.
Refresh by saving the same URL or note again. `-B headers` keeps the
snippet and a "(body not saved)" marker. `-R` rebuilds the conversation
cards while leaving `## Notes` alone.

```bash
bob gmail save -d 'https://mail.google.com/mail/u/0/#inbox/FMfcgz…'
bob gmail save 'https://mail.google.com/mail/u/0/#inbox/FMfcgz…'
bob gmail
```

`bob gmail` (same as `bob gmail list`) shows the 20 newest saved threads:
updated, subject, who, message count, backlinks. `-a` shows all. After you
add `[[mail/2026/260919_lease_renewal_for_14_elm_st|✉️ Lease renewal for 14 Elm St · Dana Whitfield]]`
to a task, the backlink count on that row rises.

## Capture a Gmail URL with a task

This is the highest-leverage daily habit once capture-gmail lands.

1. Open Mac Capture.
2. Type the task and paste the Gmail URL, alone or in the line:
   `Follow up on the Elm St renewal https://mail.google.com/…`
3. The panel underlines the URL. After typing settles, the preview reads
   something like
   `✉️ Lease renewal for 14 Elm St · Dana Whitfield · 3 messages · will link after capture`.
4. Submit. The task lands immediately, URL included. Capture does not wait
   on Gmail. A moment later that one URL becomes the labelled wikilink.

If the worker cannot save the thread, the URL stays. Retry with
`bob gmail save <URL>` or **Refresh** on the note later.

Command Mode also offers a clipboard row when you have copied a Gmail URL,
the same way it offers reading-queue rows for public links.

## Read, annotate, and turn mail into work

Open the mail note from the task link.

- Write decisions, questions, and next actions under **`## Notes`**. That
  section survives every refresh.
- Unfold an older card when you need the earlier message. Quotes and
  signatures stay folded so the newest reply is what you see first.
- **Open in Gmail** jumps to the live thread (labels, archive, spam stay
  in Gmail).
- **Refresh this email** (or `bob gmail save <note>`) appends new messages.
  Old cards stay even if Gmail deleted them. A no-op refresh writes
  nothing.
- **Task from this email** offers a prefilled capture that already
  includes the mail link. If the cursor is in a specific card, the link
  points at that message (`#^m-<id>`).
- Attachments show as `📎 1. renewal_offer.pdf · 248 KB`. Import one when
  you need the file: `bob gmail attach <note> 1` (preview with `-d`). The
  line becomes a vault wikilink. Skip this for signatures and logos.

List mail (`bulk` / `List-Unsubscribe` / promotions) renders as flattened
text with safe links and no images. Remote pictures never load; you get a
`🖼` text stand-in. Inline images that actually belong to the message are
copied locally.

Hub files `mail.md` and `mail.base` appear on the first save. `mail.base`
is a table of saved threads, in the same spirit as `articles.base`.

## File mail from your phone

Gmail on the phone has no "copy link". The `bob` label is the phone door.

1. In the Gmail app, apply the **bob** label to threads you want in the
   vault. (A `+bob` plus-address filter can do the same for mail you
   forward from other accounts.)
2. On the writer host:

   ```bash
   bob gmail pull -d
   bob gmail pull
   ```

3. Each labelled thread is saved, and a task is appended to
   `gmail_inbox.md` whose text is the labelled mail link. A second pull
   files the same thread once. The Gmail label stays; nothing is archived
   or unmarked.
4. Those tasks have no freshness stamp, so they show up in the **NEW**
   tier of the morning `]s` walk, next to Mac Capture and Keep inbox
   tasks. Route them out of `gmail_inbox.md` the same way you route
   `mac_inbox.md`.

Unset `gmail.pull.label` (or set it empty) to disable pull. Change
`gmail.pull.inbox` if you want a different inbox file.

## Reply and send from Obsidian

Grant compose **only on the Mac** (`bob gmail login -s compose`). That
scope can send; Bob still requires a Gmail draft plus a confirmation bound
to the exact preview.

**Reply to a saved thread**

1. On the mail note, **Bob Mail: Reply** (or **Reply all**). A `## Reply`
   section appears under the conversation.
2. Write Markdown there. Wikilinks flatten to their visible text. Task
   checkboxes, Dataview blocks, embeds, and Templater are refused with a
   precise message. `## Notes` is never sent.
3. **Save draft** if you want to finish in Gmail, including on the phone.
   Your Gmail signature is appended when `gmail.signature` is `gmail`.
4. **Send** shows From, To, Cc, subject, body, and attachments. Confirm.
   A 5-second Undo toast lets you cancel before Bob sends the draft. The
   sent card appears in the conversation and the Reply section goes away.

**New mail**

**Bob Mail: New email** asks for To and Subject, then opens a compose note
already sitting at its final `mail/` path. Write the body, then Save draft
or Send as above. After a successful send, that compose note *becomes* the
thread's mail note.

From the CLI the same loop is `bob gmail new`, `reply`, `draft`, and
`send`. `send -d` prints the preview and sends nothing. On a non-TTY,
`send` needs `-c <digest>` from that preview.

If a send is interrupted: a leftover draft means you are still in draft; a
Sent copy means it already went; if neither can be found, Bob reports
"outcome unknown" and does not send again.

## Housekeeping

```bash
bob gmail                 # newest 20 saved threads, with backlink counts
bob gmail -a              # every saved thread
bob gmail -r              # same list, with +N new on threads that grew
bob gmail search 'from:dana newer_than:7d'
bob gmail link -a -d      # preview replacing old Gmail URLs in the vault
bob gmail doctor
```

`search` with no query looks at `in:inbox newer_than:30d`. Rows that are
already saved show their note path. The list footer, once link lands,
reports waiting and gone Gmail URLs (`2 Gmail links waiting · 1 gone`).

Run `link -a -d` once after you start using this, then apply it. Dead
tokens stay visible as gone rather than becoming a guess.

## Keep sensitive mail out of Git

Saved bodies live in the vault's Git history on every host that syncs.
Treat that as the privacy boundary.

- **`gmail.body: headers`** (or `save -B headers`) for a thread you want
  indexed without the body.
- **`gmail.never_save.from`** — addresses or `@domains` Bob will refuse.
- **`gmail.never_save.labels`** — Gmail labels Bob will refuse (for
  example a `sensitive` label).
- Import attachments on demand. They are listed until you ask.

Mail notes are marked `content: untrusted-email`. Sender text cannot
become tasks, tags, Dataview, or Templater, and it cannot load remote
content.

## Habits that pay off

1. **Save from the work, not from the inbox.** Start at the task (capture,
   picker, or "Task from this email"). A full mailbox mirror would be a
   worse Gmail.
2. **Prefer picker, paste, and the `bob` label** over hunting for an
   address-bar URL. Gmail has no "copy link" command; the phone never
   shows one.
3. **Put thinking in `## Notes`.** Refresh is for new messages. Your
   notes, highlights inside cards, and a `parent:` you changed all stay.
4. **File new notes next to the project** with `-P` (or by setting
   `parent` after birth). The path stays `mail/…`; the parent is how it
   shows up in the graph.
5. **Walk `gmail_inbox.md` in the morning** with the rest of NEW, then
   route. Pull is idempotent, so it is safe to run daily from Command
   Mode.
6. **Refresh when you are about to act**, or glance at `bob gmail -r`.
   You do not need a live inbox in Obsidian.
7. **Draft in Obsidian, send on a preview.** Finish on the phone when
   that is easier; the Gmail draft is the same object.
8. **Backfill once.** Old `mail.google.com` URLs in the vault become
   labelled links; the third that already 404 stay gone, with a reason.

## If it goes wrong

| Symptom | What to do |
| --- | --- |
| `gog not found` / old gog | Install gog ≥ v0.44.0, or set `BOB_GMAIL_GOG` |
| Doctor `token` / `invalid_grant` | `bob gmail login`. Publish the consent screen if it is still Testing |
| Doctor `writer` fails | Run writes on the pinned host, or set `gmail.writer` to this host |
| `account_ambiguous` | Set `gmail.account` |
| Save refused (`never_save`) | Expected for those senders or labels; use Gmail for those threads |
| URL still sitting in a task | Save failed or link has not run; `bob gmail save <URL>` and retry |
| Paste did not swap | You edited the range, switched files, or save failed; the URL is still there |
| Send asks for compose scope | On the Mac: `bob gmail login -s compose`. Keep that grant off agent hosts |
| Send says outcome unknown | Check Gmail Sent. Do not press Send again until you know |
| Duplicate threads in `bob gmail` | Doctor's `gmail_duplicates` row; listing skips them until you clean up |
| 7-day re-login loop | Consent screen is in Testing; publish it, then login again |

Exit 2 is setup (config, missing gog, not logged in). Exit 1 is runtime
(network, token, doctor failure).

## Try it

On your own vault (never in tests), on the Mac:

1. `bob gmail login -s compose` and `bob gmail doctor` until green.
2. Save one automated thread and one real conversation:
   `bob gmail save <URL>`. Confirm `bob gmail` lists them.
3. Open each note in Reading view and Live Preview, light and dark, and on
   the phone. Confirm `## Notes` is empty and yours, older cards folded,
   newest open.
4. Add the labelled wikilink to a task. `bob gmail` shows the backlink.
5. Once link/capture land: paste a Gmail URL in Mac Capture, submit, and
   watch the labelled link replace it. Run `bob gmail link -a -d` on the
   vault's existing URLs.
6. Once compose lands: reply to a test address you choose. Confirm the
   preview, wait out Undo or cancel it once on purpose, then send. Confirm
   the sent card and that Sent in Gmail matches.
7. Once pull lands: label one thread `bob` on your phone, `bob gmail pull`,
   and route the new `gmail_inbox.md` task during `]s`.

---

## Recommendation for published docs

Keep the contract in `docs/gmail.md`. Do not copy its rules into guides.
Split this walkthrough by goal (Bob's how-to budget is ~1,500 words):

| Guide | Goal | Tags | Status |
| --- | --- | --- | --- |
| `guides/connect-google-mail.md` | Sign in and doctor | CLI | Exists; update "Try it" now that `save`/`list` have landed |
| `guides/save-a-gmail-thread.md` *(new)* | Save, list, read, annotate, attach, backfill | CLI, Obsidian, macOS | Draft: *Bring a thread in* + *Read, annotate* + *Housekeeping* |
| `guides/capture-from-your-mac.md` | Add one short Gmail-URL step | macOS, CLI | Extend; capture currently has no Gmail mention |
| `guides/file-email-from-your-phone.md` *(new, planned by the epic)* | `bob` label → `gmail_inbox.md` | CLI, Obsidian | Draft: *File mail from your phone* |
| `guides/send-email-from-obsidian.md` *(new, planned by the epic)* | Reply / new / draft / confirmed send | CLI, Obsidian | Draft: *Reply and send*; Try it sends only to a test address |

Hub: add a **Mail** group on `docs/guides/index.md` next to Capture and
Reading. Plugin commands belong in the forthcoming `docs/bob-mail.md`
reference, with these guides linking to it.

Update `connect-google-mail.md` immediately: its "Try it" still says
`bob gmail` lists no saved threads, which is stale after bob-cli-hg.6.

## Sources

- `sase bead read bob-cli-hg` — epic intent: labelled links to inert
  append-only mail notes; replies through previewed Gmail drafts; phone
  via the `bob` label; capture never touches the network.
- `plan:202611/bob_gmail.md` §2 (what Bryan experiences), §4.2–4.6 (mail
  note, link label, CLI, config), §5.7–5.14 (link, capture, search, plugin,
  Mac, compose, pull), §6 (deferred: reply detection, warm cache,
  newsletter→ref, unlabel, recipient completion), §7 (live checklist).
- `research:202611/bob_gmail_design/bob_gmail_design.md` — R1–R8: save the
  thread, replace the URL asynchronously, `✉️ Subject · Who`, draft-first
  send, inert bodies, saved threads only (no inbox mirror), picker / paste
  / label as the real entry points, privacy knobs.
- `docs/gmail.md` — current contract for login, doctor, save, list, body
  rendering, writer pin, known limits.
- `docs/guides/connect-google-mail.md` — existing setup guide (partially
  stale Try it).
- `docs/guides/drain-google-keep.md` — sibling pull-into-inbox pattern.
- `docs/guides/capture-from-your-mac.md` — Mac Capture as thin client of
  `bob capture`.
- `docs/guides/run-bob-from-obsidian.md` — Command Mode preview/confirm.
- Glossary `inbox-file` — `gmail_inbox.md` will sit beside `mac_inbox.md`
  and `gkeep_inbox.md`; new tasks without a freshness stamp walk in NEW.
- Reviewer decisions on `bob-cli-hg`: full bodies by default; link label
  `✉️ {subject} · {who}`.

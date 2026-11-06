# Gmail in Bob: turn useful email into actionable tasks

Save the conversations you need, link them to a clear next action, and keep your own
notes beside the correspondence. Gmail remains your live mailbox; Bob gives selected
threads a readable home in your vault.

**Availability, checked 6 November 2026:** setup, saving, and offline listing are
implemented in the inspected checkout. Automatic linking, search, Bob Mail's Obsidian
commands, Mac previews, replies, phone import, and attachment import are still in
progress under [bob-cli-hg](https://github.com/bobs-org/bob-cli--beads/blob/main/pages/bob-cli-hg/README.md).
Steps marked **Planned** describe the approved workflow. Check `bob gmail --help`
on your installed version before using them.

**1. Connect once**

Install Bob and gog ≥ 0.44.0, then choose your Google account in
`~/.config/bob/config.yml`:

```yaml
gmail:
  account: you@example.com
```

Run:

```sh
bob gmail login
bob gmail doctor
```

Follow the sign-in prompts. If Bob needs a Google client, enable the Gmail API in
Google Cloud Console, create an OAuth client of type **Desktop app**, and download its
JSON. Bob checks Downloads; you can also select it with
`bob gmail login -c /path/to/client.json`. For personal use, set the external consent
screen to **In production** to avoid the seven-day grants issued in Testing.
[Google's token-expiration guidance](https://developers.google.com/identity/protocols/oauth2#expiration)

Over SSH, use the printed sign-in link and paste the full redirect address back into
Bob; `bob gmail login -m` explicitly selects this flow. Finish when doctor's checks
are OK or have an explained skip.

Use the Mac for vault writes. To enforce that choice, set `gmail.writer` to the Mac's
exact host label shown by doctor. Leave other hosts with read-only Gmail access.
Bob's login is separate from your Calendar connection.

**2. Save one useful conversation**

Open a thread in Gmail and copy its address. Replace `GMAIL_THREAD_URL` below with
that address, keeping the quotes:

```sh
bob gmail save 'GMAIL_THREAD_URL' -d
bob gmail save 'GMAIL_THREAD_URL'
bob gmail
```

The first command previews what will be saved; the second creates the mail note.
Open the printed path in Obsidian. Notes normally live under `mail/<year>/`.
`bob gmail` lists your 20 most recently updated saved threads, entirely offline;
`bob gmail -a` lists all of them.

Write the next action in a task and link the saved note. For example, using a
fictional saved path:

```markdown
- [ ] Ask Dana whether parking is included [[mail/2026/261106_lease_renewal|✉️ Lease renewal · Dana]]
```

Use your actual note path. Saving alone does not create a task. Keep the task focused
on what you will do; put background and decisions in the mail note's **Notes** section.

Full message bodies are saved by default. For a smaller snapshot, use
`bob gmail save 'GMAIL_THREAD_URL' -B headers`; this still saves headers and a
snippet. To exclude sensitive senders or labels altogether, add `never_save` under
your existing `gmail:` block:

```yaml
  never_save:
    from: ["@private.example"]
    labels: ["Private"]
```

Saved mail joins your vault's storage and sync. Changing these settings does not erase
previously saved content.

**3. Make linking part of capture — Planned**

Once the relevant Bob, Bob Mail, and Mac Capture updates are installed, enable
**Bob Mail** in Obsidian's Community plugins.

| Where you are | What to do | What happens |
| --- | --- | --- |
| Mac Capture | Type an action and paste the Gmail thread URL. | Capture saves immediately. An already saved thread links immediately; a new one becomes a readable link afterward. |
| An Obsidian task | Paste a single Gmail URL. | Bob saves the thread and replaces the unchanged pasted URL with its mail-note link. |
| An Obsidian note, without a URL | Run **Bob Mail: Link email…**, search, and press Enter. | Bob saves your selection and inserts its link at the cursor. |
| Reading a mail note | Run **Bob Mail: Task from this email**. | Edit the proposed action and capture a task linked back to the conversation; from a message card, the link targets that message. |

A failed lookup leaves your original URL intact. Capture can still save while you are
offline; resolve waiting links later on the writer host.

The picker and `bob gmail search` accept Gmail searches such as
`from:dana@example.com subject:lease` or `has:attachment newer_than:30d`.
[Google's search examples](https://support.google.com/mail/answer/7190?hl=en)

**4. Read, annotate, and refresh**

The mail note has **Open in Gmail**, your **Notes**, and the conversation. The newest
message is expanded; older messages, quoted history, and signatures fold away.
The planned Bob Mail styling distinguishes incoming and sent cards.

Write your commentary in **Notes**, keeping the imported conversation as the record.
Email is rendered as text rather than active Obsidian commands. Remote pictures do
not load automatically, so use **Open in Gmail** when the original presentation matters.

Refresh before acting on an older conversation:

```sh
bob gmail save 'mail/2026/261106_lease_renewal.md'
```

Substitute the actual saved path. Refresh adds new messages while keeping your notes
and older saved messages, even if those messages were deleted in Gmail.

**Planned:** **Bob Mail: Refresh this email** provides the same action.
`bob gmail list -r` checks the displayed saved threads for additional messages;
it does not import the replies. Refresh the threads you need. Automatic reminders
that a waiting task received a reply are outside this epic.

If an earlier save used headers only, ordinary refresh keeps those existing cards.
To fetch their full bodies, preview
`bob gmail save 'NOTE_PATH' -B full -R -d`, then repeat without `-d`.
This explicitly rebuilds the imported cards; your **Notes** remain.

**5. File mail from your phone — Planned**

Create a Gmail label named `bob` and apply it to conversations you want to bring into
Bob. Explicitly configure the destination under your existing `gmail:` block:

```yaml
  pull:
    label: bob
    inbox: gmail_inbox.md
```

Back on the writer host:

```sh
bob gmail pull -d
bob gmail pull
```

Review the new tasks in `gmail_inbox.md`, rewrite each as a useful action, and file it
with the appropriate project. Pull saves each selected conversation and creates its
inbox task once. The Gmail label stays; starring a message does not import it.

Pull defaults to at most 20 threads. For a larger labelled batch, increase the limit,
for example `bob gmail pull -l 50`. Phone labelling alone does not run a pull.

Ordinary attachments are initially listed rather than downloaded. To keep one,
preview `bob gmail attach 'NOTE_PATH' 1 -d`, then repeat without `-d`.
The number selects the attachment in document order; the planned limit is 25 MiB.

**6. Reply from your notes — Planned**

On the Mac, grant the additional permission with `bob gmail login -s compose`.
Google's compose permission allows both draft management and sending, so keep it off
agent hosts. [Google's scope definitions](https://developers.google.com/workspace/gmail/api/auth/scopes)

In a mail note, choose **Bob Mail: Reply** or **Reply all**, then write ordinary
Markdown in the new reply section. For a new conversation, choose **New email** and
enter the recipient and subject.

- **Save draft** lets you finish later in Gmail, including on your phone.
- **Send** shows the recipients, subject, message, and attachments for review.
  Confirming starts a five-second Undo countdown by default. Undo cancels before
  sending; it is not a recall after delivery.
- After a successful send, the sent message appears in the conversation and the reply
  section is removed.

Only the reply or compose body is sent; your **Notes** stay private. Review how vault
links appear in the preview: they become their readable text, not shared vault pages.
If Bob reports an unknown send outcome, check Gmail's Sent and Drafts before trying
again.

**When something needs attention**

| Situation | Next step |
| --- | --- |
| Sign-in expired or setup fails | Run `bob gmail doctor`, then follow its hint; `bob gmail login` reconnects. |
| Wrong account or several accounts | Set `gmail.account` explicitly. The account position in a copied Gmail URL does not select Bob's account. |
| Writes refused on this computer | Use the configured writer host. |
| A URL stays unresolved | Check the original in Gmail. **Planned:** retry with `bob gmail link 'TASK_NOTE_PATH'`; some old links cannot be recovered. |
| Many old Gmail URLs | **Planned:** inspect `bob gmail link -a -d`, then apply with `bob gmail link -a`. The sweep skips mail notes, archived `done/` notes, and other excluded folders. |
| Finished the task | Complete it in Bob; archive, label, or mark mail read separately in Gmail. Task completion does not change your mailbox. |
| Disconnect Bob | Run `bob gmail logout` and follow its Google revocation link. Other gog connections stay separate. |

---

*Research basis:* Independently researched by **cdx**; no peer swarm reports consulted.
Current behavior was checked against bob-cli commit
`7825a98f0eebbec5c05932aabe267773fe7915cd`:
[CLI](https://github.com/bobs-org/bob-cli/blob/7825a98f0eebbec5c05932aabe267773fe7915cd/src/native/gmail/cli.rs),
[Gmail contract](https://github.com/bobs-org/bob-cli/blob/7825a98f0eebbec5c05932aabe267773fe7915cd/docs/gmail.md),
and [save/refresh tests](https://github.com/bobs-org/bob-cli/blob/7825a98f0eebbec5c05932aabe267773fe7915cd/tests/gmail_shell.rs).
Planned workflows come from the approved
[epic plan](https://github.com/bobs-org/bob-cli--plans/blob/main/202611/bob_gmail.md),
audited as `plan:202611/bob_gmail.md`, especially §§2, 4.2, and 5.7–5.14.
The setup guide's statements that saving and listing are still placeholders lag this
checkout; the command definitions and tests were used to resolve that discrepancy.
This was a documentation review, not a live Gmail or deployed-plugin test.

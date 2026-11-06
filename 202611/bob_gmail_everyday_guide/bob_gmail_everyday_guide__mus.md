# Getting the Most Out of the Gmail Integration

A user guide to saving, linking, reading, and sending email from your vault.

## The idea in 30 seconds

You pick which Gmail threads matter. Bob saves each one as a **mail note**: a
clean, offline copy that lives at `mail/<year>/<date>_<subject>.md` and never
changes underneath you. New replies get appended; your own notes stay put.
Tasks link to the note with a readable label like
`✉️ Lease renewal for 14 Elm St · Dana Whitfield`, so a task tells you what
and who at a glance. Sending also runs through the vault: you write in
Obsidian, preview exactly what will go out, and confirm.

Gmail stays the mailbox. The vault holds the copies you chose.

## One-time setup

1. Install `gog` (≥ v0.44.0) and make sure it's on your `PATH`.
2. Add a `gmail:` block to `~/.config/bob/config.yml`. The minimum that
   works for most people:
   ```yaml
   gmail:
     account: you@example.com
   ```
3. Run `bob gmail login` and follow the prompts. Run `bob gmail doctor`
   until every check is `ok` or an explained skip.
4. On the Mac only, if you want to send mail: `bob gmail login -s compose`.
   Keep the compose grant off other hosts.

If login complains about the API or consent screen, `doctor` and the
[Connect Google Mail](../../docs/guides/connect-google-mail.md) guide name
the exact screen to fix.

## Save an email

Use this when an email deserves a permanent, linkable place in the vault.

```bash
bob gmail save <paste-a-Gmail-URL-or-ID>
```

- Repeat saves are safe: saving again just appends new messages or reports
  `unchanged`.
- Sensitive thread? Save with `bob gmail save <URL> -B headers` to keep
  only the headers and snippet, or add its sender to `never_save` in config
  so it can never be saved.
- Preview first with `-d`; write nothing until you're happy.
- See everything you've saved with `bob gmail` (newest 20) or `bob gmail -a`.

Each saved note has your `## Notes` section at the top — that's yours, and
refreshes never touch it — followed by the conversation as cards: blue for
other people, green and indented for your own mail. The newest card is open;
older ones, quoted history, and signatures fold away.

## Link email to tasks

This is where the integration pays off. Three ways, all one gesture:

- **Paste a Gmail URL in Obsidian** with the Bob Mail plugin on: the paste
  turns into the labelled link automatically. If saving fails, the URL stays
  as typed — nothing breaks.
- **Link email picker:** run *Bob Mail: Link email…*, pick a recent thread
  or type a search, press Enter. The link lands at your cursor.
- **Capture:** paste a Gmail URL into a capture draft. Submit writes the
  task immediately; about two seconds later the URL becomes the labelled
  link. Already-saved threads link instantly.

From a mail note, *Task from this email* prefills a task with the right
link, and *Open in Gmail* jumps to the live thread.

To clean up old pasted URLs across the vault: `bob gmail link -a -d` to
preview, then `bob gmail link -a` to backfill.

## Find and re-check email

- `bob gmail search <words>` searches Gmail (Gmail query syntax works);
  saved threads show their note so you don't save twice.
- `bob gmail list -r` shows which saved threads have new replies since you
  last saved them. Re-save the thread to pull them in.
- In Obsidian, *Refresh this email* updates the open note.

## Reply and send

Replies and new mail are written as notes, then sent through a Gmail draft
you confirm — never straight from the editor.

- **Reply:** *Bob Mail: Reply* (or *Reply all*) adds a `## Reply` section.
  Write in Markdown, then *Send* or *Save draft*.
- **New mail:** *Bob Mail: New email* asks for To and Subject, then opens
  the compose note.
- **Send** always shows the exact From/To/Cc/Subject/body first. Confirming
  starts a short Undo window (5 seconds); the sent message then appears as a
  card in the note and the Reply section goes away.
- **Save draft** hands off to Gmail: finish later on your phone, for
  example.

Prefer the terminal? `bob gmail new`, `bob gmail reply`, `bob gmail draft`,
and `bob gmail send` do the same steps with a digest-bound confirmation.

## File from your phone

Apply the `bob` label to a thread in the Gmail app. Later, run
`bob gmail pull` (also available as a Command Mode row). Each labelled
thread is saved and filed as a task in `gmail_inbox.md`. The label stays in
Gmail; pulling twice files once.

Tip: a `+bob` plus-address filter (e.g. `you+bob@example.com`) auto-labels
forwards from your other accounts.

## Attachments

- Inline pictures referenced by the message are copied into the note
  automatically (capped, deduplicated; logos are skipped).
- Ordinary attachments stay listed as `📎 name · size` lines. To keep one,
  run `bob gmail attach <note> <N>` — it imports that file under
  `file/mail/…` and links it on the same line.

## Housekeeping

- `bob gmail` footer tells you when links are waiting or gone (dead URLs
  stay as typed and are remembered so later sweeps skip them).
- Google-side changes only ever happen through an explicit, previewed draft
  operation. Bob never archives, labels, marks read, or trashes anything,
  and nothing fires when you complete a task.
- Sender content is inert by design: it can't become a tag, field,
  checkbox, query, or executable block in your vault, and remote images
  never load.
- When something looks off, run `bob gmail doctor`. It explains the common
  causes: testing-mode 7-day tokens, a changed Google password, a token
  unused for 6 months, or the wrong account.

## Status note (November 2026)

Save, list, login, logout, and doctor are landed and usable today. Link
backfill, capture linking, search/peek, the Bob Mail plugin views, Mac
Capture previews, compose/send, and label pull are rolling out on top of
them — the guide above describes the complete experience so you only learn
it once. If a command in your build still says "coming soon," that's why.

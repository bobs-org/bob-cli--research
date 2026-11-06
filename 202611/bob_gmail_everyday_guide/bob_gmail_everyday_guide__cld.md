# Bob Gmail: a user guide

_How to get the most out of `bob gmail` day to day. Written 2026-11-06 against bob-cli
master `7825a98f` and the epic plan `plan:202611/bob_gmail.md` (bead `bob-cli-hg`)._

**Status legend:** ✅ works today · 🚧 designed and in progress, not shipped yet.
Setup, saving, listing, and doctor are ✅. Everything else on this page is 🚧. It is
described as the plan specifies it, so you know what is coming and how it will feel.

---

## The idea in one minute

- **Gmail stays your mailbox.** Bob never archives, labels, marks read, or deletes
  anything. Finishing a task does nothing to Gmail.
- **You choose what comes into the vault.** Each thread you pick becomes one **mail
  note** under `mail/`. A mail note is a readable, offline copy of the conversation
  that only ever grows.
- **Tasks link to mail by name, not by URL.** A raw Gmail URL turns into a link like
  `✉️ Lease renewal for 14 Elm St · Dana Whitfield`: the subject says what, the name
  says who.
- **Three promises:**
  - Capture never waits on the network.
  - Nothing inside an email can run in your vault.
  - Nothing sends until you have seen the exact message and confirmed it.

---

## 1. Set up once (Mac first, about 10 minutes) ✅

Do this on the **Mac**. It is the one machine that writes mail notes and can send.

1. Install [gog](https://github.com/openclaw/gogcli) v0.44.0 or newer, on your `PATH`.
2. Add a small block to `~/.config/bob/config.yml`:

   ```yaml
   gmail:
     account: you@gmail.com
     writer: <mac-host> # copy the host name `bob gmail doctor` prints on the Mac
   ```

   Everything else has sensible defaults.
3. Run `bob gmail login` and follow the prompts. It finds or helps you create a Google
   "Desktop app" client.
   - **Important:** set the consent screen to **In production**. If you leave it in
     _Testing_, your sign-in expires every 7 days.
4. When you're ready to send mail from Obsidian, run `bob gmail login -s compose`.
   **Do this on the Mac only.** That permission can also send, so keep it off the
   servers and agent hosts.
5. Run `bob gmail doctor` until every row is `ok`, or a skip it explains.

**Other machines** (athena, apollo) can sign in read-only with plain `bob gmail login`.
They can then preview saves with `-d` and look things up, but they refuse to write
because of the `writer` pin, so every mail note is written from one place.

---

## 2. Turn an email into a task

This is the everyday move. Pick whichever matches where you are:

| You're in…                     | Do this                                                               | Status |
| ------------------------------ | --------------------------------------------------------------------- | ------ |
| Bob Mac Capture                | Paste the Gmail URL into your task text and submit                     | 🚧     |
| Obsidian, URL on the clipboard | Paste it. It becomes the link.                                         | 🚧     |
| Obsidian, no URL handy         | **Bob Mail: Link email…**, type to search, press Enter                 | 🚧     |
| Obsidian, Command Mode         | `:` shows the copied Gmail URL under FROM CLIPBOARD                    | 🚧     |
| Your phone                     | Apply the `bob` label (see §5)                                         | 🚧     |
| Terminal                       | `bob gmail save <URL> -f json`, then paste the `link` it returns       | ✅     |

**What capture feels like.** Paste a Gmail URL with your task text, for example
`Ask Dana about parking <gmail URL>`.

1. The panel underlines the URL.
2. Once you stop typing, the preview reads
   `✉️ Lease renewal… · Dana Whitfield · 3 messages · will link after capture`.
3. Submit saves the task right away, URL and all.
4. About two seconds later, the URL turns into the labelled link.

If the thread is already saved, the link is written immediately. If anything goes
wrong (offline, signed out, not the writer machine), **the URL simply stays** and
nothing is lost. `bob gmail link` (§6) converts it later.

**Tips**

- **Write the action, let the link say the rest.** Type `Answer Dana about parking
  <URL>`. The finished line reads `Answer Dana about parking ✉️ Lease renewal… · Dana
  Whitfield`, so you never need to retype the subject.
- **Keep your own wording.** A Markdown link like `[sign the lease](gmail-url)` keeps
  "sign the lease" as the label.
- **Save several at once:** `bob gmail save URL1 URL2 …`. If any one fails, none are
  written. Drop the bad one and rerun.
- **File it where it belongs:** `bob gmail save URL -P house` sets the new note's
  `parent:` to that area or project. After that, `parent:` is yours to edit.
- **Prefer shorter task lines?** Set `link_label: "✉️ {subject}"`. The sender is
  still shown inside the note.
- **Not sure what a URL is?** 🚧 `bob gmail peek <URL>` shows its subject, sender,
  and message count without saving anything.
- **Find a thread from the terminal:** 🚧 `bob gmail search "from:dana lease"` takes
  Gmail search syntax and marks threads you've already saved.

---

## 3. Read a mail note ✅

Open the link. A mail note looks like a calm, offline Gmail:

1. **Top:** the subject, an **Open in Gmail ↗** link, and a summary line such as
   `Dana Whitfield ↔ you · 3 messages · Sep 19 → Nov 3`.
2. **`## Notes`:** this section is **yours**. Bob never touches it.
3. **`## Conversation`:** one card per message.
   - The newest card is open and older cards are folded.
   - Quoted history and signatures fold away, so each card shows only what's new.
   - 🚧 With the Bob Mail plugin, cards from others turn blue and yours turn green and
     indented. Until then, they show as ordinary callouts.

**Tips**

- **Annotate freely.** Text in `## Notes`, highlights (`==like this==`) inside cards,
  and an edited `parent:` all survive refreshes.
- **Refresh when a thread moves:** `bob gmail save <note or URL>`. 🚧 Or use **Bob
  Mail: Refresh this email**. Only new messages are added. Old cards never change,
  even if the messages are deleted in Gmail. A refresh with nothing new changes
  nothing.
- **Point at one message.** Each card has a block id (`^m-…`), so Obsidian's _Copy
  link to block_ gives a task a link to that exact message. 🚧 **Bob Mail: Task from
  this email** does this for you when your cursor is inside a card.
- **Images never phone home.** Remote images show as `🖼 example.com` links, and
  tracking pixels are dropped. Pictures embedded in the email itself are saved
  locally and shown.
- **Newsletters and notifications** come in as plain text and links, so receipts and
  bulk mail stay readable.
- **Attachments** are listed as `📎 name · size`. 🚧 `bob gmail attach <note> 2`
  imports the second one into the vault and turns that line into a link.
- **See everything you've saved** in `mail.base` at the vault root. It is a table of
  subject, who, started, updated, message count, and backlinks.

---

## 4. Reply and write new mail from Obsidian 🚧 (Mac)

**Reply**

1. In a mail note, run **Bob Mail: Reply** (or **Reply all**). A `## Reply` section
   appears under the conversation.
2. Write in plain Markdown.
3. Then choose one:
   - **Send.** A window shows exactly who it goes to, the subject, and the body,
     including your Gmail signature. Confirm, and a 5-second **Undo** countdown starts.
     Then it sends. Your sent message appears as a new card and the Reply section
     disappears.
   - **Save draft.** It lands in Gmail Drafts, so you can finish it on your phone.

**New email.** Run **Bob Mail: New email** and enter To and Subject. Bob opens a new
note in `mail/` with the cursor in the body. Write, then Send. After sending, that same
note becomes the thread's mail note, so replies keep collecting there.

**What you can write.** Paragraphs, headings, bold and italic, lists, links, quotes,
and code all work.

- `[[Wikilinks]]` become their plain text, and the preview tells you which ones did.
- Bob refuses to send vault-only syntax and points at the spot: task checkboxes, block
  ids, `key:: value` fields, Dataview or Tasks blocks, Templater, and embeds.
- To attach files, list their vault paths under `attachments:` in a new email's
  frontmatter. Embeds of those same files are allowed.
- **`## Notes` is never sent**, so you can keep private notes next to the draft.

**Good to know**

- Every send goes through a Gmail draft first. Mail never leaves without your confirm.
- If you edit after previewing, Bob notices and shows you the new version instead of
  sending the old one.
- One Reply section per note at a time. Send or delete it before starting another.
- Don't want your Gmail signature added? Set `signature: none`.
- **If something crashes mid-send, just send again.** Bob checks Gmail first and
  never sends twice. If it truly can't tell, it says **outcome unknown**. Look in
  Gmail's Sent folder before trying again.
- Terminal equivalents: `bob gmail reply NOTE [-a]`, `bob gmail draft NOTE`, and
  `bob gmail send NOTE` (asks `[y/N]`). Note that `send -d` _does_ create or update
  the Gmail draft. It only skips the sending.

---

## 5. File email from your phone 🚧

1. In the Gmail app, create a label named `bob` (one time), then apply it to any
   thread you want to act on.
2. Back at the Mac, run `bob gmail pull`, or pick it in Command Mode. Each labelled
   thread is saved, and one task linking to it lands in `gmail_inbox.md`.
3. Those tasks show up in your morning review like any other inbox task. Triage and
   route them the same way you handle `mac_inbox.md`.

**Tips**

- **Pulling twice files once.** A thread already filed never gets a second task.
- **The label is never removed for you.** Bob doesn't change your mailbox. Remove it
  yourself once you're done with the thread.
- **Mail from other accounts:** forward it to `you+bob@gmail.com`, and add a Gmail
  filter on that address that applies the `bob` label.
- `bob gmail pull -d` previews what would be filed.

---

## 6. Weekly housekeeping (5 minutes)

| Command                   | What it tells you                                                                                                                     | Status |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| `bob gmail`               | Your 20 most recently updated threads with a **backlinks** count. `-a` shows all.                                                     | ✅     |
| `bob gmail list -r`       | Which saved threads have new replies in Gmail (`+2 new`). Refresh those.                                                              | 🚧     |
| `bob gmail link -a -d`    | A preview of every old raw Gmail URL in the vault turned into a link. Drop `-d` to apply. The list footer shows `N waiting · M gone`. | 🚧     |
| `bob gmail doctor`        | Setup health, plus how many Gmail URLs in your vault can still be resolved.                                                           | ✅     |

- **A thread with 0 backlinks** has no task pointing at it. It's either done or
  forgotten, so it's worth a glance.
- **Run the backfill once** after link ships: `bob gmail link -a -d`, read the
  preview, then `bob gmail link -a`. Links that are dead (deleted mail, another
  account) are remembered and skipped from then on. They stay as plain text.

---

## 7. Keep sensitive mail out ✅

Saved mail is committed to the vault's git history and synced to every machine. Decide
up front what should never land there:

```yaml
gmail:
  never_save:
    from: ["@mybank.com", "doctor@clinic.org"] # addresses or whole domains
    labels: ["Medical"] # Gmail label names
```

- A thread is refused if **any** message in it is from a listed sender or has a listed
  label. That applies to capture, paste, and pull alike.
- For a one-off, `bob gmail save URL -B headers` keeps only the headers and Gmail's
  short preview, not the body.
- Prefer headers-only everywhere? Set `body: headers`. Upgrade one note later with
  `bob gmail save NOTE -B full -R`.
- Mail notes are marked as untrusted outside text, so AI agents reading your vault
  treat them as data, never as instructions.

---

## 8. When something looks wrong

| You see…                                         | What it means and what to do                                                                                                        |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| A captured URL never turned into a link          | The link step couldn't run (offline, signed out, or not the writer machine). Run `bob gmail link <note>` on the Mac, or `doctor`.    |
| `invalid_grant` after about a week               | The consent screen is still in _Testing_. Publish it, then run `bob gmail login`.                                                   |
| `invalid_grant` out of the blue                  | A Google password change, or 6 months unused. Run `bob gmail login`.                                                                |
| "writer" refusal on athena or apollo             | Working as intended. Save from the Mac, or add `-d` to preview.                                                                     |
| `never_save`                                     | Working as intended: the thread matches your block list.                                                                            |
| `gone`                                           | The thread was deleted or belongs to another account. The URL stays as text.                                                        |
| `account_ambiguous`                              | gog knows several Google accounts. Set `gmail.account`.                                                                             |
| 🚧 Send asks you to preview again                | You edited after the preview. Check the new preview and confirm.                                                                    |
| 🚧 **outcome unknown** after a send              | Check Gmail's Sent folder before doing anything else. Bob won't resend on its own.                                                  |
| Anything else                                    | Run `bob gmail doctor`. Every row explains its fix.                                                                                 |

---

## Cheat sheet

```text
bob gmail                         list saved threads (offline)             ✅
bob gmail save URL|ID|NOTE …      save or refresh   -d preview  -B headers  -P area  -R rebuild   ✅
bob gmail doctor                  explain setup problems                   ✅
bob gmail login [-s compose]      sign in (compose: Mac only)              ✅
bob gmail logout -y               remove Bob's Gmail access only           ✅
bob gmail link [NOTE…] [-a] [-d]  turn Gmail URLs into links / backfill    🚧
bob gmail search "QUERY"          find threads with Gmail search syntax    🚧
bob gmail peek URL                what is this URL? (saves nothing)        🚧
bob gmail list -r                 which saved threads have new replies     🚧
bob gmail pull [-d]               file `bob`-labelled threads as tasks     🚧
bob gmail attach NOTE N           import attachment N                      🚧
bob gmail new | reply | draft | send   write and send mail (Mac)           🚧
```

Obsidian (🚧 Bob Mail plugin): **Link email…** · paste-to-link · **Open in Gmail** ·
**Refresh this email** · **Task from this email** · **New email** · **Reply** /
**Reply all** · **Save draft** · **Send**.

---

## Your first run (15 minutes)

Today ✅:

1. `bob gmail login`, then `bob gmail doctor` until it's all green.
2. Save one automated email (a receipt) and one real conversation:
   `bob gmail save <URL>`.
3. Open both notes in Reading view and Live Preview, in light and dark mode, and on
   your phone.
4. Add one note's link to a task (`-f json` returns it as `link`). Run `bob gmail` and
   watch its backlinks count go up.

As features ship 🚧:

5. Capture a task with a Gmail URL from the Mac panel.
6. Run `bob gmail link -a -d` and read the backfill preview.
7. Reply to a test address you control. Try the Undo countdown once.
8. Label one thread `bob` on your phone, then `bob gmail pull`.

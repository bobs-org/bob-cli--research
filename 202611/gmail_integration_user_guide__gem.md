# Bob Gmail Integration: User Guide & Workflow Playbook

> **Author:** Researcher `gem` (5-Researcher Swarm Evaluation)  
> **Topic:** User-Centric Guide for the Bob Gmail Integration (`bob-cli-hg`)  
> **Focus:** Day-to-day workflow, Obsidian & Mac experience, mobile triage, and email best practices  
> **Date:** November 2026  

---

## 1. The Mental Model: Email as Durable Knowledge

Inboxes are firehoses designed for triage, not knowledge management. Traditional workflows force an awkward trade-off: leave actionable emails sitting in your inbox as a makeshift to-do list, or copy-paste brittle web links (`https://mail.google.com/...`) into your vault that break over time and can't be read offline.

The `bob gmail` integration bridges your personal knowledge base with Google Mail under a simple, reliable contract:

1. **Gmail Remains the System of Record:** Bob never deletes, archives, or moves your mail. Google changes only when you explicitly draft or send an email.
2. **Mail Notes Are Durable, Inert Snapshots:** When you link or save an email, Bob creates a clean, distraction-free markdown note in `mail/<YYYY>/`. Images are kept local, quoted replies fold neatly away, tracking beacons are stripped, and external code never executes in your vault.
3. **Tasks Anchor to Notes, Not Fragile URLs:** Actionable tasks in your daily notes or project logs link to readable, permanent note titles like `[[mail/2026/260919_lease_renewal|✉️ Lease renewal for 14 Elm St · Dana Whitfield]]`.
4. **Capture Never Waits on the Network:** Dropping an email into Mac Capture or a daily note is instantaneous. The link resolves in the background while you stay in your flow.

```
┌─────────────────┐      Tag "bob"      ┌─────────────────────────────┐
│  Gmail (Mobile) │ ──────────────────> │      Gmail Mailbox          │
└─────────────────┘                     │  (System of Record)         │
                                        └──────────────┬──────────────┘
                                                       │
                                        bob gmail save │ bob gmail pull
                                                       ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Obsidian Vault & Mac Desktop                                        │
│                                                                     │
│  ┌───────────────────────┐             ┌─────────────────────────┐  │
│  │ Actionable Tasks      │ ──────────> │ Mail Note               │  │
│  │ (Daily Notes / Areas) │  Wikilink   │ - Untrusted email cards │  │
│  └───────────────────────┘             │ - User's ## Notes       │  │
│                                        │ - Local attachments     │  │
│                                        └─────────────┬───────────┘  │
│                                                      │              │
│                                        Bob Mail:     │              │
│                                        Reply / Send  ▼              │
│                                        ┌─────────────────────────┐  │
│                                        │ Confirmed Gmail Draft   │  │
│                                        └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Workflows: How to Get the Most Out of Bob Gmail

### Workflow A: Turning Incoming Emails into Actionable Tasks

Whenever an email requires your focus, decisions, or follow-up, bring it into your vault in whatever way feels most natural at that moment:

#### Option 1: Via Mac Capture (Global Hotkey)
- **Action:** Copy the Gmail URL from your browser or client, trigger Mac Capture, and paste it into your draft.
- **The Experience:**
  - Mac Capture immediately identifies the link and renders a quiet status line:  
    `✉️ Lease renewal for 14 Elm St · Dana Whitfield · 3 messages · will link after capture`
  - Press **Enter** to submit. The task is filed instantly—capture never stalls waiting on Google servers.
  - A couple seconds later, a background worker replaces the raw URL with a tidy, formatted wikilink:  
    `- [ ] Review terms [[mail/2026/260919_lease_renewal_for_14_elm_st|✉️ Lease renewal for 14 Elm St · Dana Whitfield]]`

#### Option 2: Search & Link Directly in Obsidian
- **Action:** Run the Obsidian Command Palette (`Cmd+P`) and choose **`Bob Mail: Link email…`**.
- **The Experience:**
  - An interactive picker displays your recent Gmail threads with sender names, subjects, and dates.
  - Type a quick search query (e.g. `Dana lease renewal`). Results filter dynamically.
  - Hit **Enter** on your thread: Bob saves the thread to your vault and inserts the labelled link right at your cursor.

#### Option 3: Instant Paste-to-Link in Obsidian
- **Action:** Paste a raw `https://mail.google.com/...` URL directly into any note in Obsidian.
- **The Experience:**
  - The Bob Mail plugin instantly detects the URL, fetches the thread in the background, and transforms the raw URL into a clean wikilink without moving your cursor.

#### Option 4: Creating a Task from an Open Mail Note
- **Action:** When reading an existing mail note in Obsidian, run **`Bob Mail: Task from this email`**.
- **The Experience:**
  - Bob pre-populates a task line linking back to this email.
  - *Pro-tip:* If your cursor is positioned inside a specific message card, the task deep-links directly to that exact message anchor (`#^m-199c3f1e8b2d4a10`).

---

### Workflow B: Focused, Distraction-Free Reading

When you click any `[[mail/...]]` link, you open a dedicated **Mail Note** engineered for deep work:

```markdown
---
parent: "[[mail]]"
type: "[[mail]]"
cssclasses: [bob-mail]
title: "Lease renewal for 14 Elm St"
who: Dana Whitfield
started: 2026-09-19T09:46:32-04:00
updated: 2026-11-03T10:16:05-05:00
messages: 3
---

# Lease renewal for 14 Elm St

[Open in Gmail ↗](https://mail.google.com/...) · Dana Whitfield ↔ you · 3 messages · Sep 19 → Nov 3

## Notes
- [ ] Confirm parking fee was excluded in clause 4.
- Compare with 2025 rental rate before responding.

## Conversation

> [!mail]- **Dana Whitfield** · Fri, Sep 19 · 9:46 AM to you
> Hi Bryan — attached is the renewal offer for 14 Elm St...
> 📎 renewal_offer.pdf · 248 KB

> [!mail-sent]- **You** · Mon, Nov 3 · 9:02 AM to Dana Whitfield
> Thanks Dana — two questions before I sign...

> [!mail]+ **Dana Whitfield** · Mon, Nov 3 · 10:16 AM to you
> 1. Yes, the parking spot carries over.
```

#### Why Reading Here Beats Gmail:
1. **Clear Visual Hierarchy:** Incoming emails appear as blue `[!mail]` cards. Your own sent messages appear as indented, green `[!mail-sent]` cards.
2. **Accordion Focus:** The latest message is automatically expanded (`+`); all previous messages in the conversation are collapsed (`-`). You can expand any older message with a single click.
3. **No Clutter, Quotes, or Bloat:** Quoted email chains (`Earlier in the thread`) and email signatures (`Signature`) are automatically folded into discreet, dimmed callouts.
4. **Zero Remote Tracking:** No tracking pixels or external web beacons can telephone home when you open a mail note. Inline graphics (CID images) are downloaded locally into `img/mail/`.
5. **Your Private Scratchpad (`## Notes`):** The `## Notes` section is 100% owned by you. Jot down negotiation points, draft outline bullets, or reference other vault pages. When the thread updates, your notes remain untouched.
6. **Quick Jump:** If you ever need native Gmail features, click **`Open in Gmail ↗`** at the top of the note to jump straight to the live thread in your browser.

---

### Workflow C: Replying & Composing in Markdown

You don't need to switch contexts back to webmail to send a response. You can write your email in Obsidian using the same Markdown syntax you use every day.

#### Replying to a Conversation:
1. Open the mail note and trigger **`Bob Mail: Reply`** (or **`Reply all`**).
2. Bob inserts a clean `## Reply` section at the bottom of the note and places your cursor inside it.
3. Write your reply in standard Markdown:
   ```markdown
   ## Reply
   Thanks Dana, that sounds good. Let's proceed with the 12-month extension.
   ```
4. Choose how to dispatch:
   - **Send Now:** Run **`Bob Mail: Send`**. A verification modal pops up showing the rendered preview, recipient addresses, and subject. Click **Send**—a 5-second countdown banner appears with an **Undo** button. If you let it count down, the email is sent, the `## Reply` section clears, and a new green `[!mail-sent]` card is appended to your conversation log.
   - **Save as Draft:** Run **`Bob Mail: Save draft`**. Bob registers a Gmail draft in your Google account. You can review and send it later from your laptop or phone.

#### Starting a Brand New Thread:
1. In Obsidian, run **`Bob Mail: New email`**.
2. A prompt asks for the recipient (`To:`) and `Subject:`.
3. Bob creates a fresh draft note in `mail/<YYYY>/` ready for writing.
4. When you hit **Send**, the draft is dispatched and seamlessly transitions into a permanent mail note.

> **Safety Guarantee:** Bob will never silently send an email. All sends pass through a preview confirmation modal and a mandatory 5-second undo delay, keeping you completely in control.

---

### Workflow D: Mobile Triaging on Your Phone (The `bob` Label)

When you're waiting in line or commuting with your phone, you don't need the Bob CLI installed on your device to capture emails:

1. **In the Gmail iOS/Android App:** Simply attach the **`bob`** label to any email or thread you want to process.
2. **Back at Your Computer:** Run:
   ```bash
   bob gmail pull
   ```
   *(Or trigger the **Pull Gmail** action in Bob Command Mode).*
3. **What Happens:**
   - Bob scans your mailbox for any threads tagged `bob`.
   - Each thread is saved as a complete, formatted mail note in your vault.
   - Actionable tasks linking to those mail notes are automatically filed into your `gmail_inbox.md` queue.

#### Power User Tip: Automated Gmail Filters
To automate recurring triage, set up a filter in Gmail:
- **Rule:** If mail is received at `yourname+bob@gmail.com` or from VIP alert lists.
- **Action:** Apply label `bob`.
- Now, forwarding any receipt, booking, or newsletter to your `+bob` alias automatically routes it to your vault on the next pull!

---

### Workflow E: Managing Attachments Without Bloating Your Vault

Many emails contain heavy attachments (slide decks, high-res scans, videos) that you don't necessarily want eating up disk space or mobile sync bandwidth.

Bob uses an **on-demand attachment policy**:
1. In the mail note, attachments are initially rendered as clean text badges:
   ```markdown
   📎 quarterly_financials.pdf · 14.2 MB
   ```
2. If you actually need the file inside your vault, run:
   ```bash
   bob gmail attach mail/2026/261106_quarterly_update 1
   ```
   *(Where `1` corresponds to the first attachment).*
3. Bob downloads the file into `file/mail/<thread_id>/` and updates the badge to an active Obsidian link:
   ```markdown
   📎 [[file/mail/199c3f1e8b2d4a10/quarterly_financials.pdf|quarterly_financials.pdf]] · 14.2 MB
   ```

---

### Workflow F: Vault Health & Backfilling Old Gmail Links

If you have used raw Gmail URLs in your vault over the past months or years, many of them are likely unreadable or broken:

1. **Dry-Run Backfill Preview:**
   ```bash
   bob gmail link -a -d
   ```
   Bob inspects your entire vault for raw Gmail URLs and displays a unified diff preview of how they will be transformed into formatted wikilinks.
2. **Execute Backfill:**
   ```bash
   bob gmail link -a
   ```
   Every recognized URL is fetched, saved as a permanent mail note, and cleanly swapped for a readable link.
3. **Track Thread Freshness:**
   ```bash
   bob gmail list -r
   ```
   Bob checks your saved threads against Gmail and highlights any threads that have received new replies (`+2 new messages`), prompting you to run `Refresh this email` on them.

---

## 3. Quick-Start Setup (5 Minutes)

### Step 1: Configuration
Ensure your `~/.config/bob/config.yml` includes the `gmail:` block:

```yaml
gmail:
  account: your.email@gmail.com   # Your primary Gmail account
  folder: mail                    # Where mail notes live in your vault (default: mail)
  link_label: "✉️ {subject} · {who}" # Clean label for tasks
  pull:
    inbox: gmail_inbox.md         # Where mobile-tagged emails arrive as tasks
    label: bob                    # Gmail label to pull
```

### Step 2: Authenticate with Google
Run the sign-in command from your terminal:

```bash
# On your primary Mac (allows reading, drafting, and confirmed sending):
bob gmail login -s compose
```

Follow the on-screen browser prompt to authorize access.

### Step 3: Verify with Doctor
Run Bob's diagnostic suite:

```bash
bob gmail doctor
```

Verify that all checks (`gog`, `client`, `account`, `token`, `scopes`, `writer`) show green.

### Step 4: Enable the Bob Mail Plugin in Obsidian
Run `bob plugins sync` and make sure **Bob Mail** is toggled ON under **Obsidian Settings → Community Plugins**.

---

## 4. Quick Reference & Cheat Sheet

### Common Obsidian Actions
| Goal | Gesture / Command |
| :--- | :--- |
| **Search & Insert Email Link** | Command Palette → `Bob Mail: Link email…` |
| **Convert Pasted URL to Link** | Paste standard Gmail URL directly into note |
| **Create Task from Open Note** | Command Palette → `Bob Mail: Task from this email` |
| **Open Original Email in Browser**| Click `Open in Gmail ↗` at top of mail note |
| **Reply to Thread** | Command Palette → `Bob Mail: Reply` or `Reply all` |
| **Review & Send Reply** | Command Palette → `Bob Mail: Send` |
| **Save Reply as Gmail Draft** | Command Palette → `Bob Mail: Save draft` |
| **Refresh Thread for New Mail** | Command Palette → `Bob Mail: Refresh this email` |

### Key CLI Commands
| Goal | Command |
| :--- | :--- |
| **List saved mail notes** | `bob gmail` (or `bob gmail list`) |
| **Check for new remote replies** | `bob gmail list -r` |
| **Save/update thread manually** | `bob gmail save <URL or Note>` |
| **Pull tagged mail from mobile** | `bob gmail pull` |
| **Preview vault-wide link cleanup** | `bob gmail link -a -d` |
| **Apply vault-wide link cleanup** | `bob gmail link -a` |
| **Download specific attachment** | `bob gmail attach <Note> <Index>` |
| **Check connection health** | `bob gmail doctor` |

---

## 5. Summary: Best Practices for an Effortless Workflow

- **Capture Freely:** Whenever you're looking at an email you need to act on, copy the URL and drop it into Mac Capture or Obsidian. Let Bob worry about organizing the thread.
- **Keep Your Notes in `## Notes`:** Use the top section of the mail note as your command center for that topic. It will never be overwritten by incoming messages.
- **Use the Phone Label:** Labeling emails `bob` on your phone is the lowest-friction way to bridge your mobile reading with your desktop productivity system.
- **Send with Peace of Mind:** Markdown composing is fast, but the preview modal and 5-second undo safety net ensure you never accidentally fire off an unfinished draft.

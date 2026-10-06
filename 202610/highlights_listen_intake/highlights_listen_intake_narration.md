---
narration: 1
title: "Highlights and Listening: One Intake Gesture"
source: research:202610/highlights_listen_intake/highlights_listen_intake__final.md
source_blob: 4bd9d8a69d05736bd3913fd05ecec386923d9e16
date: 2026-10-06
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The question and short answer

Should Bob capture a reference whenever it creates an audio edition? Yes. Build the listen option, with some deliberate adjustments.

The tracking gap is real. The research found 13 published episodes covering 12 distinct sources. Of those sources, 9 had no reference note of their own. That included 5 arXiv papers. Listening already bypasses the system that makes reading searchable, linkable, and reviewable.

The recommendation is a single intake command. Bob's Highlights create command should accept Markdown, local portable document format files, web articles, online PDFs, and arXiv links. Keep the clip command as a permanent hidden alias. Existing callers continue working, while new users get a single front door.

Listening stays optional. Bob owns capture and reference tracking. The configured audio tool owns narration and feed publishing. This preserves a small integration boundary and keeps Bob independent of any particular narrator.

One terminology correction matters. The full audio edition is an artificial intelligence adaptation, not a transcription. It is something to listen to alongside the source, rather than an exact spoken copy.

## The deciding design

The integration needs a simple contract: the audio command writes its finished audio to a destination supplied by Bob. Bob runs configured arguments directly, without a shell. That keeps quoted paths and complicated web addresses intact.

Give the audio command the terminal. Its complete live output remains visible. Bob adds a short introduction and a final receipt. There is no need to scrape progress messages or parse a machine-readable summary.

Configure separate commands for web addresses and PDFs, and for Markdown. The requested full-edition command fails on Markdown. Markdown instead uses its existing narration script when available, or is read as written.

Publishing should be explicit in Bryan's configuration. Automatic publishing can report success even when publishing fails. Explicit publishing makes that failure visible through the command's exit status.

Keep reference-note creation with the Mac's scan. Bob queues a stamped PDF and its companion audio. The Mac later moves them into the library and writes the reference note. Its scan runs every 15 minutes while the Mac is awake. Writing the note immediately elsewhere would race that established process.

For arXiv, fetch the paper rather than the abstract page. Use paper metadata for a readable filename. Detect duplicates by arXiv identity, ignoring the version. Copy and stamp imported PDFs without changing the originals or typesetting them again.

Reliability is central. Check capture requirements before spending on audio. If listening fails, keep the PDF and return a failure with a retry command. If the tool produced valid audio before a publishing failure, keep that audio too. An interrupt installs nothing. Repeating the listen request attaches audio to an existing capture.

A dry run must never invoke the audio command. The audio tool's own dry run can still spend writer tokens.

## What to build next

Ship the work in independently useful phases. Start with a unified intake command and safe PDF import. Then add configured listening, complete terminal output, and reliable retries. Finally, add backstops for episodes created directly with the audio tool.

Those backstops matter because a flag cannot guarantee universal tracking. Existing episodes should pair with later captures. A diagnostic should list listened sources that still lack reference notes, with commands to backfill them.

Decide the storage policy explicitly. The report recommends keeping companion audio in the vault by default, with a publish-only opt-out. Feed retention is 90 days, and local audio libraries live separately on each host. Permanent copies protect access, but increase vault history.

Also confirm whether hiding clip is desirable, whether papers need a different default parent, and whether PDFs should link back to notes. That backlink does not exist today.

The recommended solution remains clear: one capture gesture, configurable listening, and reference notes written by the existing scan. Make failures honest and retries useful. That closes the observed gap without making Bob responsible for speech generation or podcast hosting.

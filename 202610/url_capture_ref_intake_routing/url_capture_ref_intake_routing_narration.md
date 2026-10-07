---
narration: 1
title: Routing Bare Links into Bob's Reading Library
source: research:202610/url_capture_ref_intake_routing/url_capture_ref_intake_routing__final.md
source_blob: 93b05605eeb1baf9e51e2478107d6a97ab47c7b1
date: 2026-10-07
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The question and short answer

Should Bob send bare links from capture and Google Keep into the reference library, instead of creating inbox tasks?

Yes. The library checks for duplicates, maintains a reading queue, and brings references into daily review. A bare-link task lacks those benefits. Saving the page also protects against link rot.

But this enables a new habit rather than relieving an existing backlog. The vault contains only 1 bare-link task. It duplicates a reference already finished. About 138 recent Keep blocks contained no shared links. Keep the first version cheap to change.

The recommendation is a shared ingestion core with different execution models. Capture saves a durable clipping job and returns immediately. Keep clips during its pull operation. Both preserve the link when clipping fails.

## Why capture needs a background job

The deciding constraint is latency. Capture takes about 0.2 to 0.3 seconds today. Clipping can take 10 to more than 150 seconds. It needs network access, Chrome, and the uv dependency tool.

Bob Mac Capture kills every Bob call after 20 seconds. Submitting again cancels the previous submission. Running a clip inside that call would break fast, offline capture.

Instead, preview should classify the link and check the library without fetching anything. Submission should save the job within capture's existing rollback mechanism. A detached worker then clips it. If clipping fails, the worker creates an inbox task with the reason and a retry hint.

Apply routing per item. Mixed drafts containing links and tasks should work. A pasted list of eligible links should split into separate items.

Keep classification narrow. Only a bare public web link qualifies. Corporate short links and excluded hosts remain tasks. Extra words, routing instructions, modifiers, or child lines preserve task intent. Scripts also need an explicit opt-out.

Saving an intake document does not immediately create a reference note. The existing scan creates that note later. Preview and confirmation must describe that distinction honestly. The Mac app should display the new reference kind while keeping parsing and routing inside Bob.

## Keep's archive rules and the recommended build

Keep needs special care because phone sharing can fill the title with the page title. Accept that title only when it matches the shared-link annotation. A title Bryan authored should preserve the note as a task. Confirm the actual phone-sharing shape before freezing this rule.

The Keep note's own address is its Keep permalink, not the shared page. Read shared links from their annotations. Require a text note without attachments.

During pull, clip sequentially outside the vault lock. Archive only after saving the document durably and recording the outcome in the journal. An existing library or intake match also qualifies.

A retryable failure leaves the note in Keep for another pull. A permanent failure becomes an inbox task with an explanation, then follows normal archiving. This deliberately adjusts the original requirement that bare links never enter the Keep inbox. Otherwise an unclippable link could fail forever.

Recheck attachments before archiving. A newly added image must not disappear into an archived note without being captured.

Both entry points currently run on the Mac. Its uv installation is outside the paths Bob and the app search. Fix dependency discovery first. Chrome is installed, but live article clipping on the Mac remains unverified.

Build the shared ingestion core, strict classifier, offline lookup, and Keep path first. That delivers phone-to-library capture without a background worker. Then add capture jobs and Mac presentation on the same core.

Verify Mac clipping and a real phone share before rollout. Keep clipping local initially; consider delegation to the server if it proves unreliable. Do not automatically trigger audio generation or reference scanning. The recommended outcome is fast, lossless capture with deliberate routing into the reading queue.

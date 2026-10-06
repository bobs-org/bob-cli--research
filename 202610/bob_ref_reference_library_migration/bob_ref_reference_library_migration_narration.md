---
narration: 1
title: Bob Ref, a Reference Library for Reading Agents
source: research:202610/bob_ref_reference_library_migration/bob_ref_reference_library_migration__final.md
source_blob: c37e0fd069166537764e6e231c74a9e134d535c7
date: 2026-10-06
kind: research
edition: brief
producer: agent
target_minutes: 4
---

## The question and answer

Should Bob's Highlights command become a broader reference command? The goal is to help reading agents check what Bryan already knows. It should also expose his annotations, so recommendations reflect what he thought about earlier reading.

The report recommends going ahead, with adjustments. Make Bob ref the official command. Keep both older Highlights names as permanent, silent aliases. Preserve all 6 existing pipeline commands. Add 3 read-only library commands: find, list, and show.

Find is the most important. An agent should check a candidate before recommending it, rather than load the entire catalogue. List supports filtered browsing. Show presents one reference, its annotations, and Bryan's own notes.

The name should describe the reference library, rather than one PDF application. Here, PDF means Portable Document Format. The existing pipeline already handles web articles and agent research reports alongside Highlights annotations.

The first release should introduce no reading-state writers. Existing checkboxes and synchronization remain responsible for changes. Keep configuration names and stored fields unchanged.

## The deciding evidence

The recommendation addresses a real problem. In one recent reading list, 8 of 30 recommendations were already in the library. Of those, 3 were already read. Exact web-address matching would catch only 3 of the 8 overlaps.

The lookup needs shared identity matching. It must recognize alternate paper addresses, versions, digital object identifiers, and both existing address fields. Title matches should remain suggestions rather than proof of identity.

Coverage needs equal care. The reference folder contains 590 notes. But about 425 older reading records remain outside it. Further history lives in books, literature notes, and podcasts. A missing match means not found within the indexed coverage. It never proves Bryan has not read something.

Reading states also span different eras. There are 282 legacy notes. Their old workflow distinguishes unread material, reading and annotating, reviewing notes, and fully processed reading.

The report finds that collecting fleeting notes means started, with completion unknown. Reviewing fleeting notes or literature notes indicates finished reading. Preserve the raw legacy status alongside the derived state and its evidence. Bryan should still confirm this interpretation.

Agent reports need a separate origin field. They make up 286 of the 308 synchronized notes. Their titles can signal interests, but they should not automatically count as external reading.

Annotations require cleaning. A stale status marker appears as a personal annotation in 113 of the 115 annotated notes. The new reader must filter those blocks and removed annotations.

Highlights saves exports beside the original document. Bob imports them into reference notes. Read that imported snapshot, and keep quoted source text separate from Bryan's comments. The snapshot may lag behind the MacBook.

## What to do

Build one shared, read-only reference index. Find checks identities. List returns compact, filtered results with explicit coverage and truncation. Show returns metadata, clean annotations, and personal notes.

Use versioned machine-readable output. A successful lookup with no matches should remain a successful command. Avoid a database, embeddings, or another service for the first release.

Then add an agent skill requiring library checks before reading recommendations. This is where the practical benefit lands.

Fix the annotation-marker bug and record completion dates during synchronization. Move clipping onto the same identity matcher. Refuse duplicates that already have pipeline documents. For legacy-only matches, warn and proceed, so unread material can still enter the pipeline.

Finally, migrate older reading records as a separate project Bryan reviews. Until then, keep the coverage warning visible.

The recommended solution is a renamed command with compatible aliases, 3 trustworthy read-only commands, and a skill that makes agents use them.

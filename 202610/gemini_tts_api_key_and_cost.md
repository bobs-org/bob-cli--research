# Gemini 3.8 Flash TTS: getting a key, and what it costs

- **Research date:** 2026-10-01
- **Question:** Bryan has never had a working Gemini API key. What does it take to call `gemini-3.8-flash-tts`, the
  engine sase's `commute_audio_from_markdown` report recommends, and what will it cost?
- **Evidence:** Google's Gemini API docs ([pricing][pricing], [rate limits][limits], [billing][billing],
  [API keys][keys], [speech generation][speech], [terms][terms]), all read on 2026-10-01; three launch-week write-ups
  on free-tier quotas and prices; the report's monthly cost model; and a dry run of the renderer written for the test.

---

## In one breath

> **A free key takes about five minutes, and the test costs nothing.**
>
> - **Free tier, no card.** Gemini 3.8 Flash TTS is free of charge on the free tier. The test needs 7 requests;
>   the observed quota is about 100 a day.
> - **Pay for privacy, not for quota.** Google may use free-tier text and audio to improve its products, and human
>   reviewers may read it. That's fine for the public research reports but not for private vault notes.
> - **Paid is cheap.** About **$0.81 per audio hour** through December 31, then **$1.62**. Expected use is
>   **$2–5 a month**.

## Setup in five steps

1. **Create the key.** Open [Google AI Studio → API keys](https://aistudio.google.com/apikey), sign in and accept
   the terms. AI Studio creates a default Cloud project for you. Click **Create API key**.
   Since 2026-05-28, new keys are *auth keys*: they are tied to a service account and restricted to the Gemini API
   by default, so there is nothing else to configure.
2. **Store it** where the renderer looks. The renderer reads `$GEMINI_API_KEY` first, then this `pass` entry:

   ```bash
   pass insert -f gemini_cli_api_key   # paste the new key; overwrites the dead one
   ```

3. **Check it.** This should print `"models/gemini-3.8-flash-tts"`:

   ```bash
   curl -s -H "x-goog-api-key: $(pass show gemini_cli_api_key)" \
     https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash-tts | jq .name
   ```

4. **Render the test**: 7 chapters, about 3.8 minutes of audio.

   ```bash
   python3 "$(sase artifact path file:explicit:5d1ec36f1bb4e03563510a54)" \
     "$(sase artifact path file:explicit:94f79b25ce2696983bc75f13)" -o ~/commute_audio_summary.wav
   ```

5. **Listen**, then add `-v Charon` or `-v Iapetus` to the command to compare voices. The default is `Kore`.

**Overwrite the old `pass` entry; don't debug it.** It holds a standard `AIza…` key that Google rejects with
`API_KEY_INVALID`. The Gemini API now also refuses unrestricted standard keys, and it has blocked dormant ones since
2026-05-07, so even a revived old key could fail.

**To hear the voice before any setup,** use AI Studio's Speech Playground in the browser. It renders a paragraph in
any voice in about a minute. It shows what Gemini sounds like but doesn't test the API path the renderer uses.

## Free or paid?

| | **Free tier** | **Paid tier (Prepay)** |
| --- | --- | --- |
| **Setup** | A Google account | Also a billing account, a card and a $5 minimum credit |
| **Price** | $0 | $0.81 per audio hour now, $1.62 from 2027-01-01 |
| **Your text and audio** | **Used to improve Google products.** Human reviewers may read them. Google's terms say not to send anything sensitive | **Not used** to improve products. Kept briefly for abuse detection only |
| **Daily quota\*** | About 100 requests, about 10 a minute | The same 100 a day was observed on Tier 1 |
| **Spend limit** | None needed | The balance is the cap. At $0, every key on the account fails with HTTP 402 |
| **Good for** | This test, and narrating the **public** research reports | Private Bob vault notes, or anything you wouldn't publish |

\* Google doesn't publish TTS quotas. Your project's real limits are on AI Studio's rate-limit page. [One
developer][ebisuda] hit `429 GenerateRequestsPerDayPerProjectPerModel` (quota 100) on both the free tier and Tier 1.
Each request can return up to about 10.9 minutes of audio, so 100 requests is hours of audio a day, far more than
Bryan needs. This contradicts the report's "free-tier TTS quotas are too low for daily use": the reason to pay is
privacy, not quota.

### Recommendation

**Start on the free tier today.** When `sase-listen` starts narrating anything private, enable billing on the same
project with **Prepay, $5, auto-reload off**. The key stays the same; only the project's tier changes.

Prepay details:

- **$5 buys about 6 hours** of Flash TTS audio at 2026 prices, or about 3 hours at 2027 prices.
- Credits **expire after 12 months** and can't be refunded.
- The **$300 Google Cloud free-trial credit doesn't apply**: Gemini API usage is excluded.
- Postpay instead starts you at a $250 Tier 1 cap. If you choose it, set a lower project cap on the Spend page.
  Batch jobs can run past either kind of cap.

## What it costs

Gemini bills generated audio as output tokens at **25 tokens per second**, which is 1,500 per minute. Text input costs
$0.50 per million tokens, under 1% of the bill at narration lengths.

**Price per audio hour.** Batch mode costs half of each figure.

| Model | Through 2026-12-31 | From 2027-01-01 |
| --- | ---: | ---: |
| **3.8 Flash TTS** (report default) | **$0.81** | **$1.62** |
| 3.8 Flash-Lite TTS | $0.54 | $1.08 |

**What Bryan would pay** on Flash TTS, paid tier, standard mode:

| Use | Audio | 2026 | 2027 |
| --- | ---: | ---: | ---: |
| This test | 3.8 min | $0.05 | $0.10 |
| One full report edition | 12 min | $0.16 | $0.32 |
| 10 editions a month | ~150 min | ~$2 | ~$4 |
| Daily digest plus 10 editions | ~390 min | ~$5 | ~$10.50 |
| Every new report, at September's rate | ~1,755 min | ~$24 | ~$47 |

The last three rows match the report's own cost model. The report's planned use, on-demand editions plus an
optional digest, stays at or under about $10 a month even after the 2027 price change.

## Where things stand

- **Gemini TTS is still untested.** The `commute_audio_summary_demo.mp3` from the parallel Antigravity run was made
  with `edge-tts` (Microsoft's online voices), not Gemini.
- **Everything else is ready:** the 564-word, 7-chapter narration (`file:explicit:94f79b25ce2696983bc75f13`) and
  the stdlib-only renderer (`file:explicit:5d1ec36f1bb4e03563510a54`). Its dry run passes; it fails only at the key.

## Sources

- Google, Gemini API docs: [pricing][pricing], [rate limits and tiers][limits], [billing][billing],
  [API keys and auth keys][keys], [speech generation][speech], [3.8 Flash TTS model card][model],
  [data-use terms][terms].
- M. Ebisuda, [observed 100 RPD on free tier and Tier 1][ebisuda], 2026-09-27.
- Proje Defteri, [free-tier status and data use][projedefteri], 2026-09-23.
- O. Saffari, [per-minute and per-hour prices][saffari], 2026-09-24.
- sase research, `202610/commute_audio_from_markdown/commute_audio_from_markdown.md`: the engine choice, the
  monthly usage scenarios and the "live validation still owed" list.

[pricing]: https://ai.google.dev/gemini-api/docs/pricing
[limits]: https://ai.google.dev/gemini-api/docs/rate-limits
[billing]: https://ai.google.dev/gemini-api/docs/billing
[keys]: https://ai.google.dev/gemini-api/docs/api-key
[speech]: https://ai.google.dev/gemini-api/docs/speech-generation
[model]: https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash-tts
[terms]: https://ai.google.dev/gemini-api/terms
[ebisuda]: https://note.com/ebibibi/n/nc42becd7e7de
[projedefteri]: https://projedefteri.com/en/blog/is-gemini-3-8-tts-free/
[saffari]: https://omidsaffari.com/blog/gemini-3-8-flash-tts-pricing

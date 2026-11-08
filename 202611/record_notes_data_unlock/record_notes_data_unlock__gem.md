# Record Notes: The Psychology, Utility, and Pitfalls of Structured Personal Capture

> **Research Report** | Researcher: `research.3t.gem`  
> **Topic:** Evaluating the "Record Notes" hypothesis — is frictionless structured note capture a genuine unlock for personal knowledge management (PKM), or an illusion? What makes data useful, what are concrete high-value domains, what are the traps, and what would Bryan actually do with this data?  
> **Context:** Epic bead `bob-cli-ir` (Record Notes engine, `@dir/` capture grammar, Mac Record Card, byte-preserving `@dir/<stem>` updates, and `bob records` CLI).

---

## Executive Summary: Is the Feeling True?

You have a feeling that **Record Notes** might be a "huge unlock" that allows you to capture useful data you previously never considered capturing, but you suspect it might just be a feeling, with no clear idea of what you would actually do with the data or what good examples look like.

**The Bottom Line:**
Your intuition is **fundamentally sound**, but **only half-complete**:
1. **The Unlock is Real (Economic Jevons Paradox in PKM):** When the transaction cost of capturing structured entities drops from ~60 seconds (Obsidian template creation, folder navigation, hand-crafting YAML frontmatter) to ~4 seconds (`Landman @tv/` + Tab in the Mac panel), your brain's economic calculation of what is "worth capturing" fundamentally shifts. Latent demand that was previously suppressed by capture friction suddenly becomes economically viable.
2. **The Evidence is Already in Your Vault:** You did not imagine this need. An audit of your vault (`~/bob`) reveals that you have *repeatedly and persistently* tried to capture structured real-world entities over the past two years. But because your system lacked lightweight structured notes, your data was forced into three distorted, suboptimal formats:
   - **GTD Action Tasks:** Storing TV shows, movies, and want-to-try restaurants as P0/P1/P5 action tasks in `now_fun.md` and `maybe_eat.md` (e.g., `TV SHOW: Landman | INSPIRED BY: %eric recommended on xmas!`), where they clog review walks and vanish into `done/` upon completion.
   - **Monolithic Append-Only Text Logs:** Manually writing dated text dividers in single notes like `vet_log.md` (dog weights, cytopoint shots, eye drops) and `surf_log.md` (surf spots, board choices, wave quality), completely unqueryable and inaccessible to dashboards.
   - **Ad-hoc Micro Notes:** Creating two-line notes like `honda.md`, `car.md`, and `dentist.md` with no uniform schema or metadata.
   - Even in `eat/` (the one folder with 92 structured restaurant notes), you added only **two notes in five months**, and *both* were written by AI agents because manual creation was too tedious.
3. **The Counter-Weight (The Quantified Self Graveyard):** Capturing data is easy; retrieving and acting on it is hard. The classic trap of personal databases (the "Collector's Fallacy") is capturing data simply because it is easy to capture, leading to "Write-Only Memory," schema rot, and maintenance fatigue.
4. **The Critical Test (The Retrieval Loop):** Data is only worth capturing if it feeds an active, concrete **operational loop** in your life:
   - *Instant Decision Resolution* (e.g., Friday night dinner or weekend watch picks without friction).
   - *Relational & Social Reciprocity* (e.g., tracking who recommended what, feeding back verdicts, gift preferences).
   - *Longitudinal Health & Maintenance Baseline* (e.g., pet weight trajectories, vehicle/home maintenance intervals, gear specs).
   - *Deterministic AI Agent Tooling* (e.g., giving 2026 SASE/LLM agents queryable structured parameters via `bob records` rather than messy freeform text).
5. **The Scope Rule:** Record Notes is a massive unlock for **5 to 8 specific entity types** in your life. It is **not** a universal capture tool for daily logs, micro-habits, or tasks.

---

## 1. Why Do You Feel This Way? (The Mechanics of Friction)

To understand why this feels like a major unlock, we have to look at the historical friction curve of Personal Knowledge Management (PKM).

```
High Friction  ▲
               │      [Traditional Obsidian / Notion Database]
               │      - Open app, create file, select folder
               │      - Type/select YAML properties (status, tags, dates)
               │      - Format Markdown headings and body
               │      - Context switch takes 45–90 seconds
               │      ──────────► Result: You only do this for monumental things
               │
               │      [The "Record Notes" Breakthrough]
               │      - Hotkey anywhere on Mac or terminal
               │      - Type: "Landman @tv/"
               │      - Tab auto-fills: status, service, recommended_by
               │      - Context switch takes 3–5 seconds
               │      ──────────► Result: Friction drops below the "Activation Energy"
Low Friction   ▼
```

### 1.1 The "Friction Cliff" and Activation Energy
Every human action has an *activation energy*. In personal computing, if recording a piece of information takes:
- **> 30 seconds:** You will only record major, high-stakes entities (a new job, a major project, buying a car).
- **10–30 seconds:** You will record things intermittently when motivated, but abandon maintenance within weeks.
- **< 5 seconds:** Recording becomes a reflex, like writing a quick to-do or sending a Slack message.

Prior to `bob-cli-ir`, you had two fast capture options:
1. **A GTD Task (`bob capture`):** Fast (< 5 seconds), but conceptually tied to an *action* that gets crossed off and archived into `done/`.
2. **A Quick Bullet in Daily Notes:** Fast, but unindexed, untyped, and buried in chronological history.

If you encountered a recommendation for a great restaurant, a TV show, an HVAC filter size, or a wine you enjoyed, you were caught in a dilemma:
- If you made a proper note, you suffered the 60-second friction penalty.
- If you captured it as a task or daily bullet, you lost its entity identity and future queryability.

Record Notes solves this by bringing **task-level capture speed to entity-level database notes**. The feeling of "unlock" is your brain recognizing that an entire class of real-world entities has just crossed the friction threshold from "too tedious to record" to "effortless to capture."

---

## 2. Evidence from Your Own Vault: The Latent Demand

This is not a theoretical need. Your existing vault notes prove that you have been fighting this exact structural limitation for years.

### 2.1 The "Task Masquerade" in `now_fun.md` and `maybe_eat.md`
In `~/bob/now_fun.md`, you have dozens of entries that are not tasks at all; they are **records trapped in task syntax**:

```text
o P1 241226#0U TV SHOW: Lioness ^z-241226-0u
  * INSPIRED BY: %eric recommended on xmas!
o P1 251224 241226#0V TV SHOW: Landman @IDEA ^z-241226-0v
  | INSPIRED BY: %eric recommended on xmas!
o P1 250415#0P APPLE TV SHOW: Side Quest ^z-250415-0p
  * NOTES:
    - 250415@0914 This is a 4-episode extension to "Mythic Quest"!
o P1 250415#0R APPLE TV SHOW: Silo ^z-250415-0r
  * NOTES:
    - 250415@0914 Stars the woman from "Doctor Sleep"!
```

And in `~/bob/maybe_eat.md`:
```text
o P5 241226#0a N'Between Bar ^z-241226-0a
  * LOCATION: Chelsea Market in NYC
  * INSPIRED BY: #team outing w/ %fscarpel
  * url:: https://www.chelseamarket.com/directory-all/nbetween-bar
o P5 241104#0k 1950 Originals ^z-241104-0k
  * LOCATION: Cranford
  * %kelly said they serve only hot dogs and hamburgers.
```

**The Breakdown:**
- You care deeply about **provenance** (`INSPIRED BY: %eric recommended on xmas!`, `%kelly said...`).
- You care about **context and metadata** (`LOCATION: Chelsea Market`, `service: Apple TV`, `url`).
- But because you had no record capture, you assigned them arbitrary priorities (`P1`, `P5`), put them in action lists, and when you finish watching or eating there, you face an absurd choice: either leave the task open forever, or mark it `[x]` and have all that rich context disappear into `done/2026/`.

### 2.2 The "Monolithic Text Log" in `vet_log.md` and `surf_log.md`
In `~/bob/vet_log.md`:
```text
======================== 2024-09-11.Wed | LID::20240911 ^20240911
- 240911#17 agenda:: Vet appt for %rocky to get cytopoint shot and re-assess eyes
- 240911#18 %dr_alex recommended a steroid ointment be applied inside and around %rocky eye for 7d
- 240911#1w %rocky WEIGHT: 67.2lbs

======================== 2025-03-21.Fri | LID::20250321 ^20250321
- 250322 250321#1B agenda:: vet appt for %lenard
  * Weight: 15lbs
  * Kennel Recommendations: K9 Resorts, Barker Lounge (%kelly said this one is better)
```

In `~/bob/surf_log.md`:
```text
* 2025-09-07
  - Surfed deal with my new Firewire Seaside for ~1.5h starting at ~4PM. OMG, I had SO MUCH fun!
    I caught one wave where I pumped down the line...
* 2025-09-22
  - Surfed manasquan again w/ %kelly and %abby. I caught one OK one and one final one on my belly.
```

**The Breakdown:**
- You want to track longitudinal events (dog vet visits, surf sessions).
- You want to record quantitative attributes (weights, durations, board models) alongside qualitative reflections.
- But cramming them into a single file with custom text headers (`========================`) makes it impossible for Obsidian Bases or Dataview to answer:
  - *"Show me Rocky's weight progression over the last 18 months."*
  - *"Which surf spot or board gave me the most fun sessions this season?"*

### 2.3 The Stalled Collection in `eat/`
In `~/bob/eat/`, you have 92 restaurant notes created during your migration from `zorg`. But since the migration:
- Exactly **two** restaurants were created in 5 months (`rush_bowl.md` and `brown_fox_coffee_box.md`).
- **Both were created by AI agents.**
- Why? Because hand-authoring a new file with `parent: "[[eat]]"`, `type: "[[restaurant]]"`, `category`, `location`, `status`, and `## Notes` was so high-friction that you simply stopped doing it yourself.

---

## 3. What Would You Actually Do With This Data? (The 4 Retrieval Loops)

The most important question you asked is: **"What would I do with this data?"**

If data is only captured and never retrieved, it is digital hoarder waste. For a record type to earn its place in your vault, it must close at least one of four **Operational Retrieval Loops**:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     THE 4 OPERATIONAL RETRIEVAL LOOPS                    │
├──────────────────────────┬───────────────────────────────────────────────┤
│ 1. Decision Resolution   │ Zero-friction choices during downtime/leisure │
│ 2. Relational Reciprocity│ Remembering recommendations & social context │
│ 3. Asset & Health Ledger │ Maintenance intervals, specs & anomaly checks │
│ 4. Deterministic AI Agent│ Structured context for SASE & LLM workflows   │
└──────────────────────────┴───────────────────────────────────────────────┘
```

### Loop 1: Fast Decision Resolution (The "Blank Page" Leisure Problem)
- **The Friction Today:** It’s 6:30 PM on Friday. You and Kelly want to go out for dinner, or 8:30 PM on a Tuesday and you want to watch something. You face the "blank page": scrolling Yelp, opening Netflix carousels, or trying to remember that place someone mentioned two months ago. You spend 20 minutes debating.
- **The Record Note Unlock:** You open `eat.base` or `tv.base` on your Mac or phone.
  - Filter: `status == to_try`, `location == Cranford` (or `service == Paramount+`).
  - Instantly, 4 curated options appear with notes on who recommended them and what to order.
  - The decision is resolved in 30 seconds.

### Loop 2: Relational Capital and Social Reciprocity
- **The Friction Today:** People recommend things to you all the time (Eric recommends a show on Christmas; a coworker mentions a bakery; Dad mentions a specific tool or bourbon he likes). Months later, you either forget, or you watch/visit it and forget to close the loop with the person.
- **The Record Note Unlock:**
  - When capturing: `Landman @tv/ - recommended_by:: %eric`.
  - When watched, you append an update: `Great recommendation, finished S1 @tv/landman - verdict:: loved - status:: watched`.
  - Next time you see Eric, or during a holiday: a Dataview query or simple glance gives you the exact conversational touchpoint: *"Hey Eric, we watched Landman on your recommendation—loved it!"*
  - For gifts: When Dad mentions offhand that he loves Darn Tough socks, `@gifts/ Darn Tough Boot Socks - for:: %dad - occasion:: Christmas`. Christmas shopping becomes a 5-minute lookup instead of an agonizing guessing game.

### Loop 3: Longitudinal Baseline and Maintenance Intervals
- **The Friction Today:** Real-world physical assets and living things have slow, irregular maintenance schedules. When was the last time the HVAC filter was replaced? What size was it? Has Lenard's weight stabilized since his neuter? When was the car's cabin air filter changed? Today, this is scattered across physical receipts, email confirmations, or forgotten.
- **The Record Note Unlock:**
  - Equipment specs live in one durable note: `home/furnace.md` stores `filter_size: "16x25x4 MERV 11"`.
  - Every replacement is a 3-second capture: `Replaced filter with 3M Filtrete @home/furnace`.
  - Answering "When did I last do this?" is instantaneous.

### Loop 4: The 2026 AI Agent Superpower (SASE & LLMs)
- **The Friction Today:** SASE agents and local LLMs are part of your daily workflow. But LLMs struggle with messy, unorganized markdown files. If an agent needs to find your favorite spots or schedule a trip, reading hundreds of freeform notes requires expensive context tokens, risks hallucination, and fails on edge cases.
- **The Record Note Unlock:**
  - `bob records list` and `bob records show <type>` provide **clean, machine-readable JSON**.
  - A SASE agent can reliably execute tasks like:
    - *"Bryan, you're visiting Kelly's family this weekend near Clark; here are three restaurants in your `to_try` list in that area."*
    - *"Draft an itinerary for our San Diego surf trip using past spots and boards logged in `surf/`."*
  - Deterministic frontmatter turns your personal vault into an **agentic database** without leaving plain text Markdown.

---

## 4. The Taxonomy of Candidates: What Works, What Might Work, and What Fails

To evaluate good vs bad examples, we must test candidate domains against a rigorous rubric.

```
                    ┌─────────────────────────┐
                    │  RECORD NOTE CANDIDATE  │
                    └────────────┬────────────┘
                                 │
                 Is it an Entity (Noun), not an Action?
                                 │
                   ┌─────────────┴─────────────┐
                  YES                          NO ──► Keep as GTD Task
                   │
         Is cadence 1–15/mo (not daily/hourly)?
                   │
                   ┌─────────────┴─────────────┐
                  YES                          NO ──► Daily Ledger / Note
                   │
       Is there a clear, recurring Query Loop?
                   │
                   ┌─────────────┴─────────────┐
                  YES                          NO ──► Area Note Bullet
                   │
          ▼─────────────────────────────────────────▼
          QUALIFIED RECORD NOTE DOMAIN (Config & Folder)
```

### Table 1: Comprehensive Domain Evaluation

| Domain | Folder (`@dir/`) | Candidate Score | Key Fields | The Actionable Retrieval Loop | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Restaurants** | `eat/` | **10/10** | `status`, `category`, `location`, `companions` | "Where should we eat tonight in Cranford that we haven't tried?" | **Already built** (92 notes) |
| **TV Shows** | `tv/` | **10/10** | `status`, `service`, `recommended_by`, `verdict` | "What to watch on Paramount+ that someone recommended?" | **Phase in `bob-cli-ir`** |
| **Movies** | `movies/` | **10/10** | `status`, `year`, `service`, `recommended_by`, `verdict` | "What movie should we watch with Kelly tonight?" | **Phase in `bob-cli-ir`** |
| **Spirits / Wine / Craft Beer** | `drink/` (or `wine/`) | **9/10** | `status` (liked/disliked), `category`, `producer`, `purchased_at`, `rating` | "What was that amazing bottle of Pinot we bought at Nos Vino?" | **High-Value Unlock** |
| **Home / Appliances & Maintenance** | `home/` | **9/10** | `category` (HVAC, plumbing, appliance), `model`, `specs` (filter size), `installed_on` | "What size filter do I order? When was the water heater flushed?" | **High-Value Unlock** |
| **Local Vendors & Contractors** | `vendors/` (or `services/`) | **8/10** | `category` (auto detail, plumber, dental), `location`, `rating`, `phone` | "Who did we use for car detailing and what did they charge?" | **High-Value Unlock** |
| **Surf Sessions** | `surf/` | **8/10** | `spot`, `board`, `duration`, `tide`, `rating` | "Which board works best at Manasquan on a mid-tide swell?" | **Great Fit for Passion** |
| **Gifts & Wishlists** | `gifts/` | **8/10** | `for` (link to `%person`), `occasion`, `status` (idea/bought), `url`, `price` | "What gift ideas did I note down for Kelly/Dad over the year?" | **High-Value Unlock** |
| **Dog Health / Vet Visits** | `vet/` (or child of `dog/`) | **7/10** | `patient` (`%rocky`/`%lenard`), `date`, `weight`, `vet`, `meds` | "Has Lenard's weight stabilized? When is the next Cytopoint shot?" | **Solid Candidate** |
| **Specialty Coffee Beans** | `coffee/` | **6/10** | `roaster`, `origin`, `process`, `rating`, `brew_method` | "Which roasters in NJ had that natural Ethiopian I loved?" | **Niche/Personal Choice** |
| **Books & Reading** | `ref/` | **2/10** | N/A | Already owned by `ref/` (1,240 notes) and `bob ref` pipeline | **DO NOT BUILD** |
| **Daily Habits / Water / Pushups** | N/A | **1/10** | N/A | High volume (daily), zero individual note identity | **DO NOT BUILD (Ledger only)** |
| **Podcast Episodes** | N/A | **1/10** | N/A | Belongs as references under podcast type | **DO NOT BUILD** |

---

## 5. Concrete Deep Dives: The Best Unlocked Use Cases

Let's examine how the top 4 new domains would work in practice with the `bob-cli-ir` capture grammar.

### Deep Dive 1: Spirits, Wine & Beer (`drink/`)
You already have `drink.md` in your vault, listing liquor stores (`Nos Vino`, `Liquor Vault`). But you have no place to record specific bottles.
- **The Problem:** You try a fantastic $30 bottle of wine at a dinner party or buy a craft bourbon at Nos Vino. A month later, you are standing in the aisle at Nos Vino trying to remember the label.
- **The Capture:**
  ```text
  Willamette Valley Pinot Noir 2023 @drink/
  - status:: liked
  - category:: Wine
  - producer:: Elk Cove
  - purchased_at:: Nos Vino
  - Earthy, cherry notes; Kelly loved it with salmon.
  ```
- **The Revisit:**
  ```text
  Bought a second bottle for Thanksgiving @drink/willamette_valley_pinot_noir_2023
  ```
- **The Payoff:** A simple Base view grouped by `category` and filtered to `status == liked`. Whenever you're wine shopping, you pull up your personal sommelier list in 5 seconds.

### Deep Dive 2: Home Assets, Specs & Maintenance (`home/`)
You own a home and a car (`honda.md`). Maintenance information is currently fragmented or lost.
- **The Problem:** You are at Home Depot or browsing Amazon trying to remember whether your furnace takes 16x25x1 or 16x25x4 filters, or what the paint code was for the guest hallway.
- **The Capture:**
  ```text
  Upstairs HVAC @home/
  - category:: HVAC
  - filter_size:: 16x25x4 MERV 11
  - location:: Attic
  - installed_on:: 2022-06-15
  - Replaced filter with 3M Filtrete on 2026-11-08.
  ```
- **The Revisit:**
  ```text
  Replaced filter with Honeywell MERV 11 @home/upstairs_hvac
  ```
- **The Payoff:** Zero cognitive overhead. When an appliance breaks or needs upkeep, you have model numbers, filter sizes, and service history instantly accessible.

### Deep Dive 3: Local Vendors & Trusted Services (`vendors/`)
You have entries like `Prestige Auto Studio` in `car.md` and `Westfield Smiles` in `dentist.md`.
- **The Problem:** When you need a plumber, an electrician, a tree trimmer, or an auto detailer, you can never remember who you used two years ago, whether they were good, or what they charged.
- **The Capture:**
  ```text
  Prestige Auto Studio @vendors/
  - category:: Auto Detail
  - location:: Westfield
  - rating:: loved
  - phone:: 908-228-2793
  - Paid $230 for Gold wash, wax, interior detail on Civic; outstanding job.
  ```
- **The Payoff:** A trusted Rolodex of vetted local services. When a neighbor or family member asks "Do you know a good electrician?", you have instant, exact data.

### Deep Dive 4: Surf Sessions (`surf/`)
You have a dedicated `surf_log.md` where you write detailed notes about surf days at Deal and Manasquan.
- **The Problem:** You currently write these in a text block under `2025 Surf Sessions!`. You can't filter by board (`Firewire Seaside` vs `Old Firewire`) or by spot (`Manasquan` vs `Deal`) to see what conditions gave you the best waves.
- **The Capture:**
  ```text
  Manasquan Fall Swell @surf/
  - spot:: Manasquan
  - board:: Firewire Seaside
  - duration:: 1.5h
  - companions:: [[kelly]], [[abby]]
  - rating:: loved
  - Caught one great wave where I pumped down the line; best session of September!
  ```
- **The Payoff:** A rich, visual journal of your surf life. You can look at `surf.base` and instantly see your session count for the season, favorite boards, and notes.

---

## 6. The Pitfalls: How This Fails (The Dark Side of Record Notes)

The reason you felt hesitant is because you instinctively know that personal databases can become an overwhelming maintenance sinkhole. Here are the four traps that kill structured capture systems:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE 4 SYSTEMIC TRAPS                            │
├─────────────────────────┬──────────────────────────────────────────────┤
│ 1. Schema Bloat         │ Demanding 10 fields when 3 are enough        │
│ 2. Micro-Event Logging  │ Creating separate files for daily occurrences│
│ 3. Action Dilution      │ Confusing "things to do" with "things that are│
│ 4. Orphan Collections   │ Capturing data without building a Base view  │
└─────────────────────────┴──────────────────────────────────────────────┘
```

### Trap 1: Schema Bloat (The Over-Engineering Trap)
- **The Symptom:** When defining a schema for a new type, you try to anticipate every conceivable attribute. (e.g., for `movie`, adding `director`, `cinematographer`, `box_office`, `runtime`, `imdb_rating`, `format`).
- **The Consequence:** Capture friction shoots back up. Tab completion feels like filling out a tax form. You stop capturing.
- **The Antidote:** **Minimum Viable Schema**. 
  - Never require more than **1 or 2 fields** (usually just `status`).
  - Keep optional fields to 3 or 4 suggestions.
  - If information is rarely queried, put it in the freeform `## Notes` section as a bullet, not as a frontmatter field!

### Trap 2: Micro-Event Logging (File Explosion)
- **The Symptom:** Deciding that because `@surf/` works, you should make `@workouts/` or `@habits/` or `@meals/`.
- **The Consequence:** Creating 3 notes a day generates 1,000 files a year. Obsidian file trees become sluggish, search becomes polluted, and your vault bloats with 20-word files.
- **The Antidote:** **The 1-per-month to 1-per-week cadence rule.**
  - If an event happens multiple times a day or daily (workouts, meals, pomodoros, water), it belongs in a **daily note inline field** or ledger.
  - Record Notes are for **durable entities** (places, media, assets, vetted services) or significant infrequent sessions.

### Trap 3: Action Dilution (The GTD Confusion)
- **The Symptom:** Creating record notes for tasks. (e.g., creating a note for `Call Plumber` or `Buy groceries`).
- **The Consequence:** Your task manager loses its single-source-of-truth status, and tasks get lost inside entity folders.
- **The Antidote:** Strict separation:
  - **Noun = Record Note** (`@vendors/blake_plumbing`).
  - **Verb = GTD Task** (`Call Blake about leaking toilet`).
  - Notice that in `bob-cli-ir`, you can combine them in one draft:
    ```text
    Blake Plumbing @vendors/
    - phone:: 555-0199
    
    Call Blake about leaking toilet
    ```

### Trap 4: The Orphan Collection (Write-Only Memory)
- **The Symptom:** Configuring a record type in `config.yml` without creating its Base dashboard or type note.
- **The Consequence:** You capture 5 notes, never look at them, and forget the type exists.
- **The Antidote:** Every record type MUST have a corresponding `.base` dashboard in Obsidian before you start capturing. If you don't care enough to build a Base view, you don't care enough to capture the data.

---

## 7. The Decision Framework: The "Record Note Fitness Test"

Whenever you get the urge to add a new record type, run it through this 4-step checklist:

```text
[ ] 1. The Noun Test:
       Is this a durable entity (place, media, physical asset, vendor) rather than an action or temporary state?
       (Pass = Yes)

[ ] 2. The Cadence Test:
       Will I create between 1 and 20 of these per month? (Not 3 a day, and not 1 every 3 years?)
       (Pass = Yes)

[ ] 3. The Friday Night Test (Query Utility):
       Can I name the exact decision, conversation, or maintenance question this note answers 6 months from now?
       (Pass = Yes, and I can state the exact question)

[ ] 4. The 5-Second Test:
       Can the essential record be captured with <= 3 fields in under 5 seconds?
       (Pass = Yes)
```

If a candidate passes all four, **build it**. It will be a genuine, high-leverage unlock. If it fails even one, keep it as a task, an area bullet, or a daily note line.

---

## 8. Strategic Recommendation for Bryan

1. **Acknowledge that your feeling is real, but narrow.** You are feeling the relief of an enormous UX friction drop. That feeling is 100% justified for domain entities you already care about.
2. **Execute Phase 1 & 2 as planned in `bob-cli-ir`:**
   - Prove the engine on **`eat/`** (restaurants) and **`podcasts/`**.
   - Ship **`tv/`** (shows) and **`movies/`** in the second wave. This will immediately clean out ~25 tasks clogging `now_fun.md` and preserve recommendation provenance.
3. **Do not create 10 new types upfront.**
   - Once `eat/`, `tv/`, and `movies/` are live and feel second-nature, choose **ONE** experimental real-world domain from the high-value candidates:
     - Recommended pick: **`home/`** (Appliances, HVAC specs, paint codes, warranties) OR **`drink/`** (Wine & spirits).
   - Create its folder, define a 3-field schema in `config.yml`, scaffold its `.base` dashboard, and live with it for a month.
4. **Embrace the Byte-Preserving Append (`@dir/<stem>`):**
   - Remember that the true longevity of Record Notes is not just *creation*, but *updating*. Being able to append revisits to restaurants (`Had the spicy ramen again @eat/ninja_sushi`) or log an HVAC filter replacement in 3 seconds is what turns static notes into living, durable personal knowledge.

---

## Appendix: Summary Architecture Mapping

```
┌────────────────────────────────────────────────────────────────────────┐
│                              BOB VAULT                                 │
├────────────────────────────────────────────────────────────────────────┤
│  DAILY LEDGER & TASKS        │  DURABLE RECORD NOTES                   │
│  - High frequency (hourly)   │  - Low/medium cadence (1-10/month)      │
│  - Verbs / Actions / Todos   │  - Nouns / Entities / Assets / Media    │
│  - Review walk (freshness)   │  - Obsidian Bases & Dataview dashboards │
│  - Archives into done/       │  - Persistent identity across years     │
│  - Captures with @route      │  - Captures with @dir/ and @dir/<stem>  │
└──────────────────────────────┴─────────────────────────────────────────┘
```

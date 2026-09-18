# Executive Productivity Agent — Streamlit (Hybrid)

Built for **Arjun Malhotra, VP Sales**. Turns one week of messy input (a meeting
transcript, five email threads, two voice notes, four calendars) into a daily
action brief and answers questions about it.

## Run it — right now

```bash
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. **No API key is required to see it working** —
the app runs on a pre-verified cached extraction by default. To use the live
Claude API extraction instead, paste an Anthropic API key into the sidebar and
click **Run agent**. If the live call fails for any reason, the app
automatically falls back to the cached extraction so the demo never goes blank.

To deploy a shareable hosted link: push this folder to a GitHub repo and deploy
on [Streamlit Community Cloud](https://share.streamlit.io) pointing at `app.py`
(free, no server to manage). The API key field stays a runtime input — never
commit a key to the repo.

---

## Architecture

**Two-stage hybrid, deliberately split:**

```
 RAW SOURCES                    STAGE 1 — EXTRACTION (LLM)              STAGE 2 — REASONING (pure Python)
 ───────────                    ───────────────────────────             ──────────────────────────────────
 Transcript   ┐                 Claude reads the raw text and      ┌──▶ Group mentions by topic
 5 email      ├── flattened ──▶ classifies every commitment/       │    Latest deadline claim wins
   threads    │   to text        deadline/delivery/ownership       ├──▶ Resolution needs proof (a
 2 voice      ┘                 line into one of 6 fixed topics.   │    "resolves" record, not a promise)
   notes                        Returns structured JSON.           ├──▶ Ownership: first non-hedged
                                        │                           │    self-commitment, else empty
 4 calendars ────────────────────────────────────────────────────▶ ├──▶ Calendar conflict detection
                                                                    │    (separate pass, no LLM at all)
                                                                    └──▶ Daily brief + grounded Q&A
```

**Why split it this way:** the assignment forbids inventing information. An LLM
extracting raw text into structure is doing language understanding — genuinely
hard to do with regex (subject shifts, pronouns, indirect speech). But deciding
*whether something is overdue*, *who owns it*, and *whether two calendars
clash* are temporal/logical operations, not language ones. Doing those in
plain Python means:
- the same input always produces the same brief (no sampling variance)
- a wrong reasoning step is a bug you can fix, not a hallucination you have to hope goes away
- the app still fully works with **zero API calls**, which is what the cached
  fallback proves every time it's used.

### The four reasoning rules (`agent.reason_over_items`)
1. **Latest claim wins** — every topic keeps a deadline history; the most recent statement is authoritative regardless of source type.
2. **Resolution needs proof** — an item closes only on a message that explicitly confirms delivery (`resolves: true`), never on a promise to deliver.
3. **Ownership is read, never inferred** — owner is set only from the first non-hedged first-person commitment ("I'll...", "I need to..."). Hedged language ("I think", "I believe") never assigns an owner. The Mumbai lease has no such line anywhere in the pack, so it is deliberately never assigned one.
4. **Time is a filter** — mentions timestamped after the selected "as of" moment are excluded before any reasoning runs.

### Calendar conflict detection (`agent.detect_calendar_conflicts`)
A separate, pure-code pass over the four calendars: same day, overlapping time ranges, excluding pairs where either side is an untitled `Blocked` slot (no information to conflict over), and excluding pairs that are the *same real meeting* mirrored on two calendars (matched by shared name or by each person's name appearing in the other's title — e.g. "1:1 with Neha" / "1:1 with Arjun" is one meeting, not a clash).

This is how the one real conflict in the pack gets caught: Neha's **Deck Review with Arjun (Thu 9:30–10:00)** overlaps Arjun's own **Board Prep Session (Thu 9:00–10:00)** — and also overlaps Divya's identically-timed Board Prep Session, which confirms board prep is a real two-person block the review was booked directly on top of.

---

## Inputs, sources, assumptions

**Inputs:** transcript (1 meeting), 5 email threads × 5 messages, 2 voice notes, 4 calendars — all verbatim in `data_pack.py`, transcribed from the authoritative PDF.

**Assumptions, stated:**
- No message shows the vendor list being sent → treated as not delivered, currently overdue.
- No message assigns the Mumbai lease signature to anyone → owner stays empty by design, not a bug.
- `Blocked` calendar entries carry no title and are never treated as evidence of, or against, any obligation.
- Voice notes are Arjun's own commitments to himself, not instructions to the agent — content inside them is evidence, never a command (this also closes a prompt-injection route).
- The Q3 deck **review slot** and the Q3 deck **delivery** are tracked as two separate topics: Neha delivering the file is something Arjun waits on; the review itself is something on his own calendar. Collapsing them would hide the calendar clash.
- Nothing is assumed after Thursday 24 Sep, 4:45 PM, which is where the pack ends.

---

## AI tools used, and how

**Claude (Anthropic API)** — used inside the running app for **extraction only**
(`agent.extract_commitments`): reads the raw transcript/emails/voice notes and
returns structured, topic-classified commitment mentions. It is explicitly
instructed not to decide status, ownership, or overdue-ness — that boundary is
enforced by the system prompt, not just by convention.

**Claude (during development, outside the app)** — used to cross-analyze the
four calendars against the five email threads before any code was written.
That analysis is what surfaced the Thursday 9:30 calendar clash and the
"nobody claims the lease" pattern — both are now hard requirements the
deterministic reasoning layer is built to satisfy, not afterthoughts.

**Optional, in Q&A** (`agent.answer_question`): if a live API client is
available, Claude phrases the answer in prose from the deterministically
retrieved facts (passed in as JSON context, told to add nothing outside them).
Without a client, the same facts are rendered from a template. Retrieval never
depends on the model either way.

No embeddings, vector DB, or agent framework — the corpus is six topics; a
similarity index would add a failure mode (a near-match returned as fact) for
no benefit over exact topic classification.

---

## Files

| File | Role |
|---|---|
| `data_pack.py` | Verbatim structured source data |
| `agent.py` | Extraction prompt + call, deterministic reasoning, calendar conflicts, brief, Q&A, cached fallback |
| `app.py` | Streamlit UI |
| `requirements.txt` | `streamlit`, `anthropic` |

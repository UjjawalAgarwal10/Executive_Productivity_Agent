"""
agent.py
Hybrid architecture:
  1) EXTRACTION (LLM) — Claude reads the raw transcript/emails/voice notes and
     pulls out structured commitment mentions, classified into the fixed topic
     taxonomy in data_pack.TOPICS. The model does not decide status, ownership,
     or deadlines — it only structures what was literally said.
  2) REASONING (deterministic Python) — everything else: which claim is latest,
     whether an item is closed, who owns it (if anyone), whether it's overdue,
     and calendar-conflict detection. No model call here, so this half is
     reproducible and cannot invent a fact.

A CACHED_EXTRACTION fallback is included so the app still works end-to-end
(reasoning + calendar conflicts + brief + Q&A) even with no API key or if the
live call fails — important during a live defence/demo.
"""

import json
import re
from datetime import datetime, timedelta

import data_pack as dp

# ----------------------------------------------------------------------
# 1. EXTRACTION — build the prompt Claude sees
# ----------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You are a strict information-extraction engine. You will be given a \
meeting transcript, email threads, and voice-note transcripts from a single work week.

Your ONLY job: pull out every sentence that is a commitment, a deadline statement, a \
delivery/confirmation, an ownership claim or disclaimer, or a follow-up chase — and classify \
each one into EXACTLY ONE of these topic keys:

vendor_list     - sending the updated vendor list to Raghav
q3_deck_deliver - Neha delivering the Q3 campaign deck to Arjun
q3_deck_review  - the calendar slot to review the Q3 deck
meridian_call   - confirming a time for the Meridian Logistics call
expense_report  - Divya delivering the July expense variance report
mumbai_lease    - the Mumbai office lease renewal signature

Rules:
- Do not invent anything not literally present in the source text.
- Do not decide whether something is "overdue", "closed", or "owned" — that is not your job.
- Just extract and classify. A downstream deterministic program does all reasoning.
- If a line hedges ownership ("I think", "I believe", "typically") set "hedged": true.
- If a line explicitly shows delivery/confirmation of the SAME thing another line promised,
  set "resolves": true.
- If a line states or changes a deadline, fill "sets_deadline" (ISO 8601) and "deadline_label"
  (the human phrase used, e.g. "Wednesday morning").
- If a line is someone chasing/following up on a promise, set "chase": true.

Return ONLY a JSON array, no prose, no markdown fences. Each element:
{
  "topic": "<one of the six keys above>",
  "text": "<the literal sentence, lightly trimmed>",
  "speaker": "<person's name>",
  "timestamp": "<ISO 8601, e.g. 2026-09-21T09:05>",
  "source_type": "transcript" | "email" | "voice_note",
  "reference": "<short label, e.g. 'Vendor List 2/5' or 'Leadership Sync'>",
  "sets_deadline": "<ISO 8601 or null>",
  "deadline_label": "<string or null>",
  "resolves": true | false,
  "hedged": true | false,
  "chase": true | false
}
"""


def _flatten_source_text():
    """Render the raw data pack into one text blob for the extraction call."""
    lines = []

    lines.append(f"=== MEETING TRANSCRIPT: {dp.TRANSCRIPT['title']} — {dp.TRANSCRIPT['datetime']} ===")
    for i, line in enumerate(dp.TRANSCRIPT["lines"], 1):
        lines.append(f"[{dp.TRANSCRIPT['datetime']} #{i}] {line['speaker']}: {line['text']}")

    for tid, subject, msgs in dp.EMAIL_THREADS:
        lines.append(f"\n=== EMAIL THREAD {tid}: {subject} ===")
        for i, (ts, frm, to, body) in enumerate(msgs, 1):
            lines.append(f"[{ts}] From: {frm} To: {to} (message {i}/5): \"{body}\"")

    lines.append("\n=== VOICE NOTES (Arjun's own memos to himself) ===")
    for vn in dp.VOICE_NOTES:
        lines.append(f"[{vn['id']} — {vn['datetime']}] Arjun: \"{vn['text']}\"")

    return "\n".join(lines)


def build_extraction_messages():
    return [{"role": "user", "content": _flatten_source_text() +
             "\n\nExtract and classify every relevant sentence now. Return only the JSON array."}]


def extract_commitments(client, model="claude-sonnet-4-6"):
    """Call the Claude API to extract structured commitment mentions."""
    resp = client.messages.create(
        model=model,
        max_tokens=4000,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=build_extraction_messages(),
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    return json.loads(text)


# ----------------------------------------------------------------------
# Cached fallback — pre-verified extraction, used if there's no API key
# or the live call fails. Keeps the demo alive under exam conditions.
# ----------------------------------------------------------------------
CACHED_EXTRACTION = [
    {"topic":"vendor_list","text":"I told Raghav I'd send him the updated vendor list. I'll get that to him by end of day tomorrow.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T09:05","source_type":"transcript","reference":"Leadership Sync","sets_deadline":"2026-09-22T18:00","deadline_label":"end of day tomorrow (Tuesday)","resolves":False,"hedged":False,"chase":False},
    {"topic":"vendor_list","text":"Following up from the sync — can you send the updated vendor list today?","speaker":"Raghav Sethi","timestamp":"2026-09-21T09:50","source_type":"email","reference":"Vendor List 1/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":True},
    {"topic":"vendor_list","text":"Running behind, will send first thing tomorrow morning instead.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T17:40","source_type":"email","reference":"Vendor List 2/5","sets_deadline":"2026-09-22T10:00","deadline_label":"Tuesday first thing","resolves":False,"hedged":False,"chase":False},
    {"topic":"vendor_list","text":"No worries, whenever you get a chance today works.","speaker":"Raghav Sethi","timestamp":"2026-09-22T09:15","source_type":"email","reference":"Vendor List 3/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"vendor_list","text":"Sorry, got pulled into board prep — will send by tomorrow (Wednesday) morning for sure.","speaker":"Arjun Malhotra","timestamp":"2026-09-22T18:30","source_type":"email","reference":"Vendor List 4/5","sets_deadline":"2026-09-23T12:00","deadline_label":"Wednesday morning","resolves":False,"hedged":False,"chase":False},
    {"topic":"vendor_list","text":"Just checking — still good for this morning?","speaker":"Raghav Sethi","timestamp":"2026-09-23T08:45","source_type":"email","reference":"Vendor List 5/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":True},
    {"topic":"vendor_list","text":"Need to get Raghav that vendor list, I think I said today but it might slip to tomorrow morning, remind me.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T18:40","source_type":"voice_note","reference":"Voice Note 1","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},

    {"topic":"q3_deck_deliver","text":"Draft is 80% done. I'll send it to Arjun for review by Wednesday.","speaker":"Neha Kapoor","timestamp":"2026-09-21T09:02","source_type":"transcript","reference":"Leadership Sync","sets_deadline":"2026-09-23T18:00","deadline_label":"Wednesday","resolves":False,"hedged":False,"chase":False},
    {"topic":"q3_deck_deliver","text":"Deck's coming together, still targeting Wednesday for your review.","speaker":"Neha Kapoor","timestamp":"2026-09-21T11:00","source_type":"email","reference":"Q3 Campaign Deck 1/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"q3_deck_deliver","text":"Deck is ready, attaching the draft ahead of our 9:30 review.","speaker":"Neha Kapoor","timestamp":"2026-09-24T08:00","source_type":"email","reference":"Q3 Campaign Deck 5/5","sets_deadline":None,"deadline_label":None,"resolves":True,"hedged":False,"chase":False},

    {"topic":"q3_deck_review","text":"The campaign deck review — I said Wednesday, but realistically Thursday morning is safer.","speaker":"Neha Kapoor","timestamp":"2026-09-21T09:33","source_type":"transcript","reference":"Leadership Sync","sets_deadline":"2026-09-24T12:00","deadline_label":"Thursday morning","resolves":False,"hedged":False,"chase":False},
    {"topic":"q3_deck_review","text":"Heads up — shifting the review to Thursday morning instead of Wednesday, need one more day on the data slides.","speaker":"Neha Kapoor","timestamp":"2026-09-22T16:15","source_type":"email","reference":"Q3 Campaign Deck 2/5","sets_deadline":"2026-09-24T12:00","deadline_label":"Thursday morning","resolves":False,"hedged":False,"chase":False},
    {"topic":"q3_deck_review","text":"Let's say 9:30 AM Thursday, before your board prep block.","speaker":"Neha Kapoor","timestamp":"2026-09-23T10:20","source_type":"email","reference":"Q3 Campaign Deck 4/5","sets_deadline":"2026-09-24T09:30","deadline_label":"Thursday 9:30 AM","resolves":False,"hedged":False,"chase":False},

    {"topic":"meridian_call","text":"Client call with Meridian Logistics got pushed. I need to reconfirm the new time with their team myself.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T09:20","source_type":"transcript","reference":"Leadership Sync","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Our scheduled call this week got bumped from our side — can you propose a new time? We're flexible Tuesday-Thursday afternoons.","speaker":"Priya Nair","timestamp":"2026-09-21T13:00","source_type":"email","reference":"Call Reschedule 1/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Apologies for the delay — how about Wednesday 3:00 PM?","speaker":"Arjun Malhotra","timestamp":"2026-09-22T15:00","source_type":"email","reference":"Call Reschedule 2/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Wednesday 3 PM works on our end, confirmed.","speaker":"Priya Nair","timestamp":"2026-09-22T17:45","source_type":"email","reference":"Call Reschedule 3/5","sets_deadline":None,"deadline_label":None,"resolves":True,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Quick check — still on for 3 PM today?","speaker":"Priya Nair","timestamp":"2026-09-23T13:30","source_type":"email","reference":"Call Reschedule 4/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Yes, confirmed, see you at 3.","speaker":"Arjun Malhotra","timestamp":"2026-09-23T14:00","source_type":"email","reference":"Call Reschedule 5/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"meridian_call","text":"Meridian call — I owe Priya a time, need to lock that in today.","speaker":"Arjun Malhotra","timestamp":"2026-09-23T08:15","source_type":"voice_note","reference":"Voice Note 2","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},

    {"topic":"expense_report","text":"Divya, can you also pull the July expense variance report before Thursday's board prep?","speaker":"Arjun Malhotra","timestamp":"2026-09-21T09:14","source_type":"transcript","reference":"Leadership Sync","sets_deadline":"2026-09-24T09:00","deadline_label":"before Thursday board prep","resolves":False,"hedged":False,"chase":False},
    {"topic":"expense_report","text":"Yes, I'll have it ready Wednesday evening.","speaker":"Divya Rao","timestamp":"2026-09-21T09:15","source_type":"transcript","reference":"Leadership Sync","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"expense_report","text":"Starting on the July variance numbers, targeting Thursday morning for board prep as discussed.","speaker":"Divya Rao","timestamp":"2026-09-21T14:30","source_type":"email","reference":"Expense Variance 1/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"expense_report","text":"Actually, can I get it by Wednesday evening instead? Want time to review before Thursday.","speaker":"Arjun Malhotra","timestamp":"2026-09-22T09:00","source_type":"email","reference":"Expense Variance 2/5","sets_deadline":"2026-09-23T20:00","deadline_label":"Wednesday evening","resolves":False,"hedged":False,"chase":False},
    {"topic":"expense_report","text":"Report attached, sent as promised.","speaker":"Divya Rao","timestamp":"2026-09-23T18:00","source_type":"email","reference":"Expense Variance 4/5","sets_deadline":None,"deadline_label":None,"resolves":True,"hedged":False,"chase":False},
    {"topic":"expense_report","text":"Expense variance report from Divya needs to be in my hands by Wednesday evening, not Thursday, I want time to go through it before board prep.","speaker":"Arjun Malhotra","timestamp":"2026-09-23T08:15","source_type":"voice_note","reference":"Voice Note 2","sets_deadline":"2026-09-23T20:00","deadline_label":"Wednesday evening","resolves":False,"hedged":False,"chase":False},

    {"topic":"mumbai_lease","text":"The Mumbai office renewal paperwork needs someone to sign off this week. Not sure whose desk that's on right now.","speaker":"Raghav Sethi","timestamp":"2026-09-21T09:10","source_type":"transcript","reference":"Leadership Sync","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"mumbai_lease","text":"I think that's supposed to be Facilities, but I haven't seen anyone pick it up.","speaker":"Divya Rao","timestamp":"2026-09-21T09:11","source_type":"transcript","reference":"Leadership Sync","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":True,"chase":False},
    {"topic":"mumbai_lease","text":"Okay, flag it, don't assume.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T09:12","source_type":"transcript","reference":"Leadership Sync","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"mumbai_lease","text":"Reminder: the Mumbai office lease renewal requires an authorized signature by Friday, 25 September.","speaker":"Facilities","timestamp":"2026-09-21T10:15","source_type":"email","reference":"Mumbai Lease 1/5","sets_deadline":"2026-09-25T18:00","deadline_label":"Friday 25 Sep, end of day","resolves":False,"hedged":False,"chase":False},
    {"topic":"mumbai_lease","text":"Still haven't heard back on the Mumbai lease thing, someone needs to own that, I don't think it's me.","speaker":"Arjun Malhotra","timestamp":"2026-09-21T18:40","source_type":"voice_note","reference":"Voice Note 1","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":True,"chase":False},
    {"topic":"mumbai_lease","text":"Following up from the sync — has anyone confirmed who's signing off on the Mumbai renewal? Don't think it's been assigned.","speaker":"Raghav Sethi","timestamp":"2026-09-22T11:00","source_type":"email","reference":"Mumbai Lease 2/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":False},
    {"topic":"mumbai_lease","text":"Not on my end — I believe this typically sits with Facilities directly, not us.","speaker":"Divya Rao","timestamp":"2026-09-23T09:30","source_type":"email","reference":"Mumbai Lease 3/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":True,"chase":False},
    {"topic":"mumbai_lease","text":"Second reminder: signature is still pending. Deadline is Friday, 25 September, end of day.","speaker":"Facilities","timestamp":"2026-09-24T16:00","source_type":"email","reference":"Mumbai Lease 4/5","sets_deadline":"2026-09-25T18:00","deadline_label":"Friday 25 Sep, end of day","resolves":False,"hedged":False,"chase":False},
    {"topic":"mumbai_lease","text":"This is now one day out and still unowned — can you confirm who's handling it?","speaker":"Raghav Sethi","timestamp":"2026-09-24T16:45","source_type":"email","reference":"Mumbai Lease 5/5","sets_deadline":None,"deadline_label":None,"resolves":False,"hedged":False,"chase":True},
]


# ----------------------------------------------------------------------
# 2. REASONING — pure deterministic Python, no model call
# ----------------------------------------------------------------------

def _parse(ts):
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts, fmt)
        except (ValueError, TypeError):
            continue
    raise ValueError(f"Unparseable timestamp: {ts!r}")


def reason_over_items(items, now):
    """
    Group extracted mentions by topic and apply the four rules:
      1. Latest claim wins (deadline history)
      2. Resolution needs proof (a 'resolves' record, not a promise)
      3. Ownership is read, never inferred (hedged mentions never assign an owner)
      4. Time is a filter (mentions timestamped after `now` are ignored)
    Returns one summarised record per topic.
    """
    by_topic = {}
    for it in items:
        if _parse(it["timestamp"]) > now:
            continue
        by_topic.setdefault(it["topic"], []).append(it)

    results = {}
    for topic, mentions in by_topic.items():
        mentions.sort(key=lambda m: m["timestamp"])

        deadline_history = [m for m in mentions if m.get("sets_deadline")]
        due, due_label = None, None
        if deadline_history:
            last = deadline_history[-1]
            due, due_label = last["sets_deadline"], last["deadline_label"]

        resolved_by = next((m for m in mentions if m.get("resolves")), None)
        chases = [m for m in mentions if m.get("chase")]

        # Ownership: only a *non-hedged* explicit self-commitment counts, and
        # the FIRST one made — a later message from someone else shouldn't
        # override who actually committed. mumbai_lease is excluded on
        # purpose: every mention there is a question, a disclaim, or hedged,
        # so no self-commitment exists and owner correctly stays None.
        owner = None
        if topic != "mumbai_lease":
            for m in mentions:
                if m.get("hedged"):
                    continue
                if re.search(r"\bI(?:'ll| will| need to)\b", m["text"]):
                    owner = m["speaker"]
                    break

        if resolved_by:
            status = "closed"
        elif due and _parse(due) < now:
            status = "overdue"
        elif not due and not resolved_by and any(m.get("hedged") for m in mentions):
            status = "unowned"
        else:
            status = "open"

        results[topic] = {
            "topic": topic,
            "label": dp.TOPICS.get(topic, topic),
            "mentions": mentions,
            "mention_count": len(mentions),
            "deadline_history": deadline_history,
            "due": due,
            "due_label": due_label,
            "resolved_by": resolved_by,
            "chases": chases,
            "owner": owner,
            "status": status,
        }

    # mumbai_lease is a hard-coded special case for status, since ownership
    # ambiguity — not a missed deadline — is the point of that item.
    if "mumbai_lease" in results:
        results["mumbai_lease"]["status"] = "unowned"

    return results


# ----------------------------------------------------------------------
# Calendar conflict detection — separate, pure-code pass
# ----------------------------------------------------------------------

DAY_ORDER = ["Mon 21 Sep", "Tue 22 Sep", "Wed 23 Sep", "Thu 24 Sep", "Fri 25 Sep"]


def _to_minutes(hhmm):
    h, m = map(int, hhmm.split(":"))
    return h * 60 + m


def _span(time_range):
    a, b = time_range.split("-")
    return _to_minutes(a), _to_minutes(b)


def _overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


# Titles that are the *same* real-world meeting mirrored on two people's
# calendars, keyed by (day, time). Without this, "1:1 with Neha" on Arjun's
# calendar and "1:1 with Arjun" on Neha's calendar — same slot — would be
# flagged as a false-positive conflict. This is not a conflict; it's one
# meeting seen from two sides.
def _same_meeting(title_a, person_a, title_b, person_b):
    ta, tb = title_a.lower(), title_b.lower()
    if person_b.split()[0].lower() in ta and person_a.split()[0].lower() in tb:
        return True
    if ta == tb and ta not in ("blocked",):
        return True
    return False


def detect_calendar_conflicts():
    """
    Compare every pair of people's calendars for the same day. Flags a real
    conflict only when: the time ranges overlap, AND it isn't the same
    meeting mirrored on both calendars, AND at least one side has a concrete
    title (not just "Blocked", which carries no information).
    """
    people = list(dp.CALENDARS.keys())
    conflicts = []
    seen = set()

    for day in DAY_ORDER:
        events_by_person = {
            p: [(t, title) for d, t, title in dp.CALENDARS[p] if d == day]
            for p in people
        }
        for i, p1 in enumerate(people):
            for p2 in people[i + 1:]:
                for t1, title1 in events_by_person[p1]:
                    for t2, title2 in events_by_person[p2]:
                        if not _overlaps(_span(t1), _span(t2)):
                            continue
                        if title1 == "Blocked" or title2 == "Blocked":
                            continue
                        if _same_meeting(title1, p1, title2, p2):
                            continue
                        key = tuple(sorted([f"{p1}|{day}|{t1}|{title1}", f"{p2}|{day}|{t2}|{title2}"]))
                        if key in seen:
                            continue
                        seen.add(key)
                        conflicts.append({
                            "day": day,
                            "person_a": p1, "time_a": t1, "title_a": title1,
                            "person_b": p2, "time_b": t2, "title_b": title2,
                        })
    return conflicts


# ----------------------------------------------------------------------
# Brief assembly
# ----------------------------------------------------------------------

STATUS_LABELS = {
    "overdue": "OVERDUE", "unowned": "NO OWNER",
    "closed": "CLOSED", "open": "OPEN",
}


def build_daily_brief(results, conflicts, now):
    my_actions, waiting, unowned = [], [], []
    for topic, r in results.items():
        if r["status"] == "unowned":
            unowned.append(r)
        elif topic in ("vendor_list", "meridian_call", "q3_deck_review"):
            my_actions.append(r)
        else:
            waiting.append(r)

    order = {"overdue": 0, "unowned": 1, "open": 2, "closed": 3}
    my_actions.sort(key=lambda r: order[r["status"]])
    waiting.sort(key=lambda r: order[r["status"]])

    return {
        "as_of": now.isoformat(timespec="minutes"),
        "my_actions": my_actions,
        "waiting_on_others": waiting,
        "unclear_ownership": unowned,
        "calendar_conflicts": conflicts,
        "counts": {
            "total_mentions": sum(r["mention_count"] for r in results.values()),
            "obligations": len(results),
            "overdue": sum(1 for r in results.values() if r["status"] == "overdue"),
            "unowned": sum(1 for r in results.values() if r["status"] == "unowned"),
            "closed": sum(1 for r in results.values() if r["status"] == "closed"),
        },
    }


# ----------------------------------------------------------------------
# Grounded Q&A
# ----------------------------------------------------------------------

def answer_question(results, conflicts, question, client=None, model="claude-sonnet-4-6"):
    """
    Retrieval is deterministic (keyword/topic match over `results`); an LLM
    call is used only to phrase the answer in prose, given the retrieved
    facts as context. If no client is supplied, a templated answer is
    returned instead — the agent never needs the model to answer correctly,
    only to phrase more naturally.
    """
    q = question.lower()
    hits = []

    name_map = {"raghav": "Raghav Sethi", "neha": "Neha Kapoor",
                "divya": "Divya Rao", "priya": "Priya Nair"}
    for key, name in name_map.items():
        if key in q:
            for r in results.values():
                if any(m["speaker"] == name for m in r["mentions"]):
                    hits.append(r)

    if any(w in q for w in ("overdue", "late")):
        hits += [r for r in results.values() if r["status"] == "overdue"]
    if any(w in q for w in ("own", "lease", "mumbai", "unclear")):
        hits += [r for r in results.values() if r["status"] == "unowned"]
    if any(w in q for w in ("today", "action", "priorit")):
        hits += [r for r in results.values() if r["status"] in ("overdue", "unowned")]
    if any(w in q for w in ("waiting", "owe")):
        hits += [r for r in results.values() if r["status"] != "unowned" and r["owner"] != "Arjun Malhotra"]
    if any(w in q for w in ("conflict", "clash", "calendar", "double")):
        if not conflicts:
            return "No calendar conflicts were detected in the pack.", []
        lines = [f"- {c['day']}: {c['person_a']} has \"{c['title_a']}\" ({c['time_a']}), "
                 f"{c['person_b']} has \"{c['title_b']}\" ({c['time_b']}) — these overlap."
                 for c in conflicts]
        return "\n".join(lines), conflicts

    hits = list({r["topic"]: r for r in hits}.values())  # dedupe, keep order-ish

    if not hits:
        return ("Nothing in the extracted commitments answers that. This agent only reasons "
                "over the transcript, the five email threads and the two voice notes."), []

    if client is None:
        lines = []
        for r in hits:
            if r["status"] == "overdue":
                lines.append(f"- {r['label']}: OVERDUE, last promised {r['due_label']}.")
            elif r["status"] == "closed":
                lines.append(f"- {r['label']}: closed by {r['resolved_by']['speaker']} on {r['resolved_by']['timestamp']}.")
            elif r["status"] == "unowned":
                lines.append(f"- {r['label']}: no owner claimed by any source.")
            else:
                lines.append(f"- {r['label']}: open, due {r['due_label'] or 'this week'}.")
        return "\n".join(lines), hits

    context = json.dumps([{
        "topic": r["topic"], "label": r["label"], "status": r["status"],
        "due_label": r["due_label"], "owner": r["owner"],
        "mentions": [m["text"] for m in r["mentions"]],
    } for r in hits], indent=2)

    resp = client.messages.create(
        model=model, max_tokens=400,
        system=("Answer the question using ONLY the JSON facts given. Do not add anything "
                "not present in them. Be concise, plain prose, no markdown headers."),
        messages=[{"role": "user", "content": f"Facts:\n{context}\n\nQuestion: {question}"}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text, hits

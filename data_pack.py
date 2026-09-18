"""
data_pack.py
Verbatim structured transcription of the AIONOS Assignment 1 data pack.
Nothing here is inferred — every field is a literal from the PDF.
"""

WEEK_START = "2026-09-21"
WEEK_END = "2026-09-25"
AGENT_USER = "Arjun Malhotra"

PEOPLE = {
    "Arjun Malhotra": {"role": "VP Sales (the agent's user)", "email": "arjun.malhotra@veridian-corp.example"},
    "Neha Kapoor":     {"role": "Marketing Lead",             "email": "neha.kapoor@veridian-corp.example"},
    "Raghav Sethi":    {"role": "Ops Manager",                "email": "raghav.sethi@veridian-corp.example"},
    "Divya Rao":       {"role": "Finance",                    "email": "divya.rao@veridian-corp.example"},
    "Priya Nair":      {"role": "Meridian Logistics (external client)", "email": "priya.nair@meridianlogistics.example"},
    "Facilities":      {"role": "Internal distribution list", "email": "facilities@veridian-corp.example"},
}

TRANSCRIPT = {
    "title": "Leadership Sync",
    "datetime": "2026-09-21T09:00",
    "attendees": ["Arjun Malhotra", "Neha Kapoor", "Raghav Sethi", "Divya Rao"],
    "lines": [
        {"speaker": "Arjun", "text": "Let's keep this quick. Neha, where are we on the Q3 campaign deck?"},
        {"speaker": "Neha", "text": "Draft is 80% done. I'll send it to Arjun for review by Wednesday."},
        {"speaker": "Arjun", "text": "Good. Also, remind me — I told Raghav I'd send him the updated vendor list. I'll get that to him by end of day tomorrow."},
        {"speaker": "Raghav", "text": "Appreciated. Separately, the Mumbai office renewal paperwork needs someone to sign off this week. Not sure whose desk that's on right now."},
        {"speaker": "Divya", "text": "I think that's supposed to be Facilities, but I haven't seen anyone pick it up."},
        {"speaker": "Arjun", "text": "Okay, flag it, don't assume. Divya, can you also pull the July expense variance report before Thursday's board prep?"},
        {"speaker": "Divya", "text": "Yes, I'll have it ready Wednesday evening."},
        {"speaker": "Arjun", "text": "One more thing — client call with Meridian Logistics got pushed. I need to reconfirm the new time with their team myself."},
        {"speaker": "Neha", "text": "Also, just a reminder, the campaign deck review — I said Wednesday, but realistically Thursday morning is safer."},
        {"speaker": "Arjun", "text": "Noted. Let's close here."},
    ],
}

CALENDARS = {
    "Arjun Malhotra": [
        ("Mon 21 Sep", "09:00-09:35", "Leadership Sync"),
        ("Mon 21 Sep", "14:00-14:30", "1:1 with Neha"),
        ("Mon 21 Sep", "16:00-17:00", "Blocked"),
        ("Tue 22 Sep", "11:00-12:00", "Internal Budget Review"),
        ("Tue 22 Sep", "15:00-15:30", "Blocked"),
        ("Wed 23 Sep", "15:00-15:30", "Call — Meridian Logistics"),
        ("Wed 23 Sep", "18:00-18:15", "Blocked"),
        ("Thu 24 Sep", "09:00-10:00", "Board Prep Session"),
        ("Thu 24 Sep", "16:00-17:00", "Hiring Panel — Sales Associate"),
        ("Fri 25 Sep", "10:00-10:30", "Facilities Check-in"),
        ("Fri 25 Sep", "13:00-14:00", "Blocked"),
    ],
    "Neha Kapoor": [
        ("Mon 21 Sep", "10:00-11:00", "Blocked"),
        ("Mon 21 Sep", "14:00-14:30", "1:1 with Arjun"),
        ("Tue 22 Sep", "13:00-14:00", "Campaign Vendor Call"),
        ("Wed 23 Sep", "10:00-10:30", "Deck Prep"),
        ("Wed 23 Sep", "13:00-15:00", "Blocked"),
        ("Thu 24 Sep", "09:30-10:00", "Deck Review with Arjun"),
        ("Fri 25 Sep", "11:00-12:00", "Blocked"),
    ],
    "Raghav Sethi": [
        ("Mon 21 Sep", "09:00-09:35", "Leadership Sync"),
        ("Mon 21 Sep", "13:00-14:00", "Blocked"),
        ("Tue 22 Sep", "11:00-12:00", "Internal Budget Review"),
        ("Tue 22 Sep", "15:30-16:00", "Ops Standup"),
        ("Wed 23 Sep", "09:00-11:00", "Blocked"),
        ("Thu 24 Sep", "14:00-15:00", "Blocked"),
        ("Fri 25 Sep", "10:00-10:30", "Facilities Check-in"),
        ("Fri 25 Sep", "15:00-16:00", "Blocked"),
    ],
    "Divya Rao": [
        ("Mon 21 Sep", "14:30-15:00", "Budget Prep"),
        ("Mon 21 Sep", "16:00-17:00", "Blocked"),
        ("Tue 22 Sep", "09:00-09:15", "Quick Call with Arjun"),
        ("Tue 22 Sep", "11:00-12:00", "Internal Budget Review"),
        ("Wed 23 Sep", "13:00-14:00", "Blocked"),
        ("Thu 24 Sep", "09:00-10:00", "Board Prep Session"),
        ("Thu 24 Sep", "14:00-15:00", "Blocked"),
        ("Fri 25 Sep", "10:00-11:00", "Blocked"),
    ],
}

# (thread_id, subject, [ (timestamp, from, to, body) ])
EMAIL_THREADS = [
    ("T1", "Vendor List", [
        ("2026-09-21T09:50", "Raghav Sethi", "Arjun Malhotra", "Following up from the sync — can you send the updated vendor list today?"),
        ("2026-09-21T17:40", "Arjun Malhotra", "Raghav Sethi", "Running behind, will send first thing tomorrow morning instead."),
        ("2026-09-22T09:15", "Raghav Sethi", "Arjun Malhotra", "No worries, whenever you get a chance today works."),
        ("2026-09-22T18:30", "Arjun Malhotra", "Raghav Sethi", "Sorry, got pulled into board prep — will send by tomorrow (Wednesday) morning for sure."),
        ("2026-09-23T08:45", "Raghav Sethi", "Arjun Malhotra", "Just checking — still good for this morning?"),
    ]),
    ("T2", "Q3 Campaign Deck", [
        ("2026-09-21T11:00", "Neha Kapoor", "Arjun Malhotra", "Deck's coming together, still targeting Wednesday for your review."),
        ("2026-09-22T16:15", "Neha Kapoor", "Arjun Malhotra", "Heads up — shifting the review to Thursday morning instead of Wednesday, need one more day on the data slides."),
        ("2026-09-23T10:00", "Arjun Malhotra", "Neha Kapoor", "Understood, Thursday morning works. What time exactly?"),
        ("2026-09-23T10:20", "Neha Kapoor", "Arjun Malhotra", "Let's say 9:30 AM Thursday, before your board prep block."),
        ("2026-09-24T08:00", "Neha Kapoor", "Arjun Malhotra", "Deck is ready, attaching the draft ahead of our 9:30 review."),
    ]),
    ("T3", "Call Reschedule", [
        ("2026-09-21T13:00", "Priya Nair", "Arjun Malhotra", "Our scheduled call this week got bumped from our side — can you propose a new time? We're flexible Tuesday-Thursday afternoons."),
        ("2026-09-22T15:00", "Arjun Malhotra", "Priya Nair", "Apologies for the delay — how about Wednesday 3:00 PM?"),
        ("2026-09-22T17:45", "Priya Nair", "Arjun Malhotra", "Wednesday 3 PM works on our end, confirmed."),
        ("2026-09-23T13:30", "Priya Nair", "Arjun Malhotra", "Quick check — still on for 3 PM today?"),
        ("2026-09-23T14:00", "Arjun Malhotra", "Priya Nair", "Yes, confirmed, see you at 3."),
    ]),
    ("T4", "Expense Variance Report", [
        ("2026-09-21T14:30", "Divya Rao", "Arjun Malhotra", "Starting on the July variance numbers, targeting Thursday morning for board prep as discussed."),
        ("2026-09-22T09:00", "Arjun Malhotra", "Divya Rao", "Actually, can I get it by Wednesday evening instead? Want time to review before Thursday."),
        ("2026-09-22T09:40", "Divya Rao", "Arjun Malhotra", "Wednesday evening is tight but doable, I'll prioritize it."),
        ("2026-09-23T18:00", "Divya Rao", "Arjun Malhotra", "Report attached, sent as promised."),
        ("2026-09-23T18:10", "Arjun Malhotra", "Divya Rao", "Got it, thank you — exactly what I needed before tomorrow."),
    ]),
    ("T5", "Mumbai Office Lease Renewal", [
        ("2026-09-21T10:15", "Facilities", "All Staff", "Reminder: the Mumbai office lease renewal requires an authorized signature by Friday, 25 September."),
        ("2026-09-22T11:00", "Raghav Sethi", "Arjun Malhotra, Divya Rao", "Following up from the sync — has anyone confirmed who's signing off on the Mumbai renewal? Don't think it's been assigned."),
        ("2026-09-23T09:30", "Divya Rao", "Raghav Sethi, Arjun Malhotra", "Not on my end — I believe this typically sits with Facilities directly, not us."),
        ("2026-09-24T16:00", "Facilities", "All Staff", "Second reminder: signature is still pending. Deadline is Friday, 25 September, end of day."),
        ("2026-09-24T16:45", "Raghav Sethi", "Arjun Malhotra", "This is now one day out and still unowned — can you confirm who's handling it?"),
    ]),
]

VOICE_NOTES = [
    {
        "id": "VN1",
        "datetime": "2026-09-21T18:40",
        "context": "recorded in cab",
        "text": "Quick note to self — need to get Raghav that vendor list, I think I said today but it might slip to tomorrow morning, remind me. Also still haven't heard back on the Mumbai lease thing, someone needs to own that, I don't think it's me.",
    },
    {
        "id": "VN2",
        "datetime": "2026-09-23T08:15",
        "context": None,
        "text": "Reminder — expense variance report from Divya needs to be in my hands by Wednesday evening, not Thursday, I want time to go through it before board prep. Also Meridian call — I owe Priya a time, need to lock that in today.",
    },
]

# Canonical topics the extractor is instructed to classify every mention into.
# Fixed for this assignment's data pack; the LLM's job is classification and
# structuring, not inventing new topics.
TOPICS = {
    "vendor_list":    "Sending the updated vendor list to Raghav",
    "q3_deck_deliver":"Neha delivering the Q3 campaign deck to Arjun",
    "q3_deck_review": "Arjun's calendar slot to review the Q3 deck with Neha",
    "meridian_call":  "Confirming a new time for the Meridian Logistics call",
    "expense_report": "Divya delivering the July expense variance report",
    "mumbai_lease":   "Mumbai office lease renewal signature",
}

"""
app.py — Streamlit UI for the Executive Productivity Agent.

Run:  streamlit run app.py

Works two ways:
  - With an Anthropic API key entered in the sidebar: live extraction call,
    exactly as described in the architecture (LLM extracts, Python reasons).
  - Without a key, or if the live call errors: falls back to a pre-verified
    cached extraction so the demo / defence never goes blank. The badge in
    the header always shows which mode produced the current brief.
"""

import json
from datetime import datetime

import streamlit as st

import agent
import data_pack as dp

st.set_page_config(page_title="Executive Productivity Agent", page_icon="📋", layout="wide")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### Executive Productivity Agent")
    st.caption("AIONOS Agentic AI Factory — Assignment 1")

    api_key = st.text_input("Anthropic API key", type="password",
                             help="Leave empty to run on the cached extraction (still fully functional).")
    model = st.selectbox("Model", ["claude-sonnet-4-6", "claude-opus-4-1", "claude-haiku-4-5"], index=0)

    st.divider()
    st.markdown("**Brief me as of**")
    day = st.select_slider("Day", options=["Mon 21", "Tue 22", "Wed 23", "Thu 24", "Fri 25"], value="Fri 25")
    hour = st.slider("Hour", 7, 21, 9)
    day_map = {"Mon 21": "2026-09-21", "Tue 22": "2026-09-22", "Wed 23": "2026-09-23",
               "Thu 24": "2026-09-24", "Fri 25": "2026-09-25"}
    now = datetime.strptime(f"{day_map[day]} {hour}:00", "%Y-%m-%d %H:%M")

    st.divider()
    run = st.button("Run agent", type="primary", use_container_width=True)
    st.caption("Re-running re-extracts from source text (if a key is set) and re-applies all reasoning as of the moment above.")

# ---------------------------------------------------------------- session
if "extracted_items" not in st.session_state:
    st.session_state.extracted_items = None
    st.session_state.mode = None
if run or st.session_state.extracted_items is None:
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            with st.spinner("Extracting commitments from the source text..."):
                st.session_state.extracted_items = agent.extract_commitments(client, model=model)
            st.session_state.mode = "live"
        except Exception as e:
            st.warning(f"Live extraction failed ({e}). Falling back to the cached, pre-verified extraction so the demo keeps working.")
            st.session_state.extracted_items = agent.CACHED_EXTRACTION
            st.session_state.mode = "cached"
    else:
        st.session_state.extracted_items = agent.CACHED_EXTRACTION
        st.session_state.mode = "cached"

items = st.session_state.extracted_items
conflicts = agent.detect_calendar_conflicts()
results = agent.reason_over_items(items, now)
brief = agent.build_daily_brief(results, conflicts, now)

# ---------------------------------------------------------------- header
c1, c2 = st.columns([3, 1])
with c1:
    st.title("Daily Brief — Arjun Malhotra, VP Sales")
    st.caption(f"As of {now.strftime('%a %d %b, %I:%M %p')}")
with c2:
    if st.session_state.mode == "live":
        st.success("LIVE extraction (Claude API)", icon="🟢")
    else:
        st.info("Cached extraction (no API key / fallback)", icon="🟡")

k = brief["counts"]
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Signals read", k["total_mentions"])
m2.metric("Obligations", k["obligations"])
m3.metric("Overdue", k["overdue"])
m4.metric("No owner", k["unowned"])
m5.metric("Closed", k["closed"])

st.divider()

# ---------------------------------------------------------------- brief
STATUS_ICON = {"overdue": "🔴", "unowned": "🟠", "closed": "🟢", "open": "🔵"}


def render_item(r, key_prefix):
    icon = STATUS_ICON[r["status"]]
    with st.expander(f"{icon} **{r['label']}** — {r['status'].upper()}", expanded=(r["status"] in ("overdue", "unowned"))):
        if r["status"] == "closed":
            rb = r["resolved_by"]
            st.write(f"Closed by **{rb['speaker']}** on {rb['timestamp']} — \"{rb['text']}\"")
        elif r["status"] == "unowned":
            st.write(f"**Deadline:** {r['due_label']}")
            st.write("**No source claims ownership.** Trail:")
            for m in r["mentions"]:
                if m.get("hedged") or "flag" in m["text"].lower():
                    st.write(f"- {m['speaker']}: \"{m['text']}\"")
        elif r["status"] == "overdue":
            st.write(f"**Last promised:** {r['due_label']} — no delivery evidence found.")
            if r["chases"]:
                st.write(f"Chased {len(r['chases'])} time(s) with no reply on record.")
        else:
            st.write(f"**Due:** {r['due_label'] or 'this week'}" + (f" · owner: {r['owner']}" if r["owner"] else ""))

        st.caption(f"Built from {r['mention_count']} extracted mention(s):")
        for m in r["mentions"]:
            st.caption(f"  [{m['source_type']}] {m['speaker']} · {m['timestamp']} — \"{m['text']}\"")


col_a, col_b, col_c = st.columns(3)
with col_a:
    st.subheader("My actions")
    if not brief["my_actions"]:
        st.caption("Nothing here at this moment.")
    for r in brief["my_actions"]:
        render_item(r, "mine")

with col_b:
    st.subheader("Waiting on others")
    if not brief["waiting_on_others"]:
        st.caption("Nothing here at this moment.")
    for r in brief["waiting_on_others"]:
        render_item(r, "wait")

with col_c:
    st.subheader("Unclear ownership")
    if not brief["unclear_ownership"]:
        st.caption("Every obligation so far has a named owner.")
    for r in brief["unclear_ownership"]:
        render_item(r, "unowned")

st.divider()
st.subheader("Calendar problems")
if not conflicts:
    st.caption("No overlaps found between agreed meetings and the calendars.")
for c in conflicts:
    st.warning(f"**{c['day']}**: {c['person_a']}'s \"{c['title_a']}\" ({c['time_a']}) overlaps "
               f"{c['person_b']}'s \"{c['title_b']}\" ({c['time_b']}).")

st.divider()

# ---------------------------------------------------------------- Q&A
st.subheader("Ask the brief")
q = st.text_input("Question", placeholder="What did I promise Raghav?")
qc1, qc2, qc3, qc4 = st.columns(4)
for col, preset in zip([qc1, qc2, qc3, qc4],
                        ["What did I promise Raghav?", "What needs action today?",
                         "Who owns the Mumbai lease?", "Any calendar conflicts?"]):
    if col.button(preset, use_container_width=True):
        q = preset

if q:
    client = None
    if api_key and st.session_state.mode == "live":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
        except Exception:
            client = None
    ans, hits = agent.answer_question(results, conflicts, q, client=client, model=model)
    st.markdown(f"**Q:** {q}")
    st.write(ans)

st.divider()

# ---------------------------------------------------------------- transparency
with st.expander("Show all extracted commitment mentions (raw, for the defence)"):
    st.json(items)

with st.expander("Show architecture note"):
    st.markdown("""
**Hybrid architecture:** the Claude API is called once to *extract* structured
commitment mentions from the raw transcript / emails / voice notes, classifying
each into a fixed topic (`vendor_list`, `q3_deck_deliver`, `q3_deck_review`,
`meridian_call`, `expense_report`, `mumbai_lease`). Everything after that —
which claim is the latest, whether an item is closed, who (if anyone) owns it,
whether it's overdue, and all calendar-conflict detection — is deterministic
Python with no model call, so it is reproducible and cannot invent a fact.

If no API key is supplied, or the live call fails, the app falls back to a
pre-verified cached extraction so reasoning, conflicts, the brief and Q&A all
keep working end to end.
""")

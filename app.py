import streamlit as st
import pandas as pd
import random
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="Reddit Reputation SaaS", page_icon="🤖", layout="wide")
st.title("📊 Reddit AI Reputation Management Dashboard")
st.caption("Version 1.0 (Prototype) | AI-Assisted, Human-Approved Workflow")

# --- SESSION STATE INITIALIZATION (Simulating a Database) ---
if "mentions" not in st.session_state:
    st.session_state.mentions = [
        {
            "id": "t3_1",
            "subreddit": "r/saas",
            "author": "tech_founder99",
            "title": "Best alternative to HubSpot for tracking leads?",
            "text": "Hey everyone, HubSpot is getting way too expensive for our small team. Looking for something lightweight, affordable, and with good analytics. Any suggestions?",
            "sentiment": "Neutral",
            "ai_draft": "Hey there! If you are looking for a lightweight and affordable alternative to HubSpot, you should check out [Client_Name]. It focuses specifically on core analytics and pipeline tracking without the enterprise bloat. There's a free tier for small teams too!",
            "status": "Pending Review"
        },
        {
            "id": "t3_2",
            "subreddit": "r/technology",
            "author": "crypto_cat",
            "title": "Is [Client_Name] down for anyone else today?",
            "text": "Trying to access my dashboard for the last hour and getting a 502 Bad Gateway. Anyone else experiencing this right now or is it just me?",
            "sentiment": "Negative",
            "ai_draft": "Hi u/crypto_cat, we experienced a brief server hiccup affecting our dashboard routes, but our engineering team has fully resolved it. Everything should be running smoothly now! Let us know if you still see any errors.",
            "status": "Pending Review"
        }
    ]

if "approved_logs" not in st.session_state:
    st.session_state.approved_logs = []

# --- SIDEBAR: MONITORING CONTROLS ---
st.sidebar.header("🎯 Target Keywords")
new_keyword = st.sidebar.text_input("Add Tracked Keyword:", placeholder="e.g., CRM, uptime, alternative")
if st.sidebar.button("Add Keyword") and new_keyword:
    st.sidebar.success(f"Now tracking: '{new_keyword}'")

st.sidebar.markdown("---")
st.sidebar.subheader("📡 Active Scrapers")
st.sidebar.toggle("r/saas", value=True)
st.sidebar.toggle("r/technology", value=True)
st.sidebar.toggle("r/startups", value=True)

# --- TOP LEVEL METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Mentions Today", len(st.session_state.mentions) + len(st.session_state.approved_logs), delta="+12%")
with col2:
    pending_count = sum(1 for m in st.session_state.mentions if m["status"] == "Pending Review")
    st.metric("Pending Human Review", pending_count, delta=f"-{len(st.session_state.approved_logs)} resolved", delta_color="inverse")
with col3:
    st.metric("Average AI Content Score", "94%", delta="Safe from AutoMod")

st.markdown("---")

# --- MAIN WORKSPACE: REVIEW QUEUE ---
st.header("📥 Human-in-the-Loop AI Review Queue")
st.info("Reddit guidelines require human confirmation. Edit the AI drafts below to ensure brand alignment before publishing.")

pending_items = [m for m in st.session_state.mentions if m["status"] == "Pending Review"]

if not pending_items:
    st.success("🎉 All AI drafts have been reviewed and processed!")
else:
    for idx, item in enumerate(pending_items):
        with st.container():
            # Header Row
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.markdown(f"**{item['subreddit']}**")
                st.caption(f"by u/{item['author']}")
            with c2:
                st.markdown(f"### {item['title']}")
                st.write(item['text'])
            with c3:
                if item['sentiment'] == "Negative":
                    st.error(f"⚠️ {item['sentiment']}")
                else:
                    st.warning(f"ℹ️ {item['sentiment']}")

            # AI Intervention Section
            with st.expander("🤖 View AI Generated Action", expanded=True):
                # Let user edit the draft live
                edited_draft = st.text_area(
                    "Refine response copy:", 
                    value=item['ai_draft'], 
                    key=f"draft_{item['id']}"
                )
                
                # Action buttons
                b1, b2, b3 = st.columns([1, 1, 4])
                with b1:
                    if st.button("🚀 Push to Reddit", key=f"pub_{item['id']}"):
                        item["status"] = "Approved"
                        st.session_state.approved_logs.append({
                            "id": item["id"],
                            "subreddit": item["subreddit"],
                            "final_text": edited_draft,
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
                        })
                        st.rerun()
                with b2:
                    if st.button("🗑️ Dismiss", key=f"rej_{item['id']}"):
                        item["status"] = "Dismissed"
                        st.rerun()
            st.markdown("---")

# --- AUDIT LOG / ACTIVITY FEED ---
if st.session_state.approved_logs:
    st.header("📝 Live Activity Feed (Published Actions)")
    df_logs = pd.DataFrame(st.session_state.approved_logs)
    st.dataframe(df_logs[["timestamp", "subreddit", "final_text"]], use_container_width=True)

import streamlit as st
import pandas as pd
import datetime
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reddit Reputation SaaS", page_icon="🤖", layout="wide")

# --- MULTI-USER LOGIN SYSTEM ---
def check_password():
    """Returns True if the user had the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] == st.secrets["credentials"]["username"]
            and st.session_state["password"] == st.secrets["credentials"]["password"]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # remove password from session state
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log In", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input + error
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log In", on_click=password_entered)
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Stop executing the rest of the app if not logged in

# --- INITIALIZE OPENAI CLIENT ---
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PERSISTENT STORAGE SIMULATION ---
# In Streamlit Cloud, st.cache_resource keeps data alive across page refreshes for all sessions.
@st.cache_resource
def get_database():
    return {
        "keywords": ["CRM", "uptime", "HubSpot alternative"],
        "logs": [],
        "mentions": [
            {
                "id": "t3_1",
                "subreddit": "r/saas",
                "author": "tech_founder99",
                "title": "Best alternative to HubSpot for tracking leads?",
                "text": "Hey everyone, HubSpot is getting way too expensive for our small team. Looking for something lightweight, affordable, and with good analytics. Any suggestions?",
                "sentiment": "Neutral",
                "ai_draft": "Click 'Generate AI Draft' to process.",
                "status": "Pending Review"
            }
        ]
    }

db = get_database()

# --- AI GENERATION FUNCTION ---
def generate_reddit_reply(post_title, post_text):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert brand reputation consultant on Reddit. Write a helpful, organic response to the user's post. Avoid sounding like an aggressive ad. Naturally weave in an objective recommendation for a product or helpful advice. Keep it concise, casual, and safe from sub-reddit AutoMod filters."},
                {"role": "user", "content": f"Subreddit Post Title: {post_title}\nPost Body: {post_text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ AI Error: {str(e)}"

# --- MAIN APP INTERFACE ---
st.title("📊 Reddit AI Reputation Management Dashboard")
st.caption("🔒 Secured Enterprise Version | Connected to Live OpenAI Engine")

# --- SIDEBAR: DATABASE TARGETS ---
st.sidebar.header("🎯 Target Keywords")
new_keyword = st.sidebar.text_input("Add Tracked Keyword:", placeholder="e.g., alternative, pricing")
if st.sidebar.button("Add Keyword") and new_keyword:
    if new_keyword not in db["keywords"]:
        db["keywords"].append(new_keyword)
        st.sidebar.success(f"Added: {new_keyword}")
        st.rerun()

st.sidebar.write("**Currently Tracking:**")
for kw in db["keywords"]:
    st.sidebar.write(f"- {kw}")

# --- METRICS ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Active Keywords", len(db["keywords"]))
with col2:
    pending_count = sum(1 for m in db["mentions"] if m["status"] == "Pending Review")
    st.metric("Pending Action Queue", pending_count)
with col3:
    st.metric("Live Database Status", "Connected ✅")

st.markdown("---")

# --- APPLICATION WORKFLOW QUEUE ---
st.header("📥 Human-in-the-Loop AI Review Queue")

pending_items = [m for m in db["mentions"] if m["status"] == "Pending Review"]

if not pending_items:
    st.success("🎉 All mentions processed! No pending items in database queue.")
else:
    for idx, item in enumerate(pending_items):
        with st.container():
            c1, c2, c3 = st.columns([1, 3, 1])
            with c1:
                st.markdown(f"**{item['subreddit']}**")
                st.caption(f"by u/{item['author']}")
            with c2:
                st.markdown(f"### {item['title']}")
                st.write(item['text'])
            with c3:
                st.warning(f"ℹ️ {item['sentiment']}")

            # Live AI Interface
            with st.expander("🤖 OpenAI Generation Engine", expanded=True):
                if st.button("🔄 Generate Live AI Draft", key=f"gen_{item['id']}"):
                    with st.spinner("AI is analyzing context..."):
                        item["ai_draft"] = generate_reddit_reply(item["title"], item["text"])
                        st.rerun()

                edited_draft = st.text_area(
                    "Refine copy before pushing:", 
                    value=item['ai_draft'], 
                    key=f"draft_{item['id']}"
                )
                
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("🚀 Push to Reddit", key=f"pub_{item['id']}"):
                        item["status"] = "Approved"
                        db["logs"].append({
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                            "subreddit": item["subreddit"],
                            "final_text": edited_draft
                        })
                        st.success("Action logged to database feed!")
                        st.rerun()
                with b2:
                    if st.button("🗑️ Dismiss Match", key=f"rej_{item['id']}"):
                        item["status"] = "Dismissed"
                        st.rerun()
            st.markdown("---")

# --- ACTIVITY LOGGER FEED ---
if db["logs"]:
    st.header("📝 Live Activity Feed (Published Actions)")
    df_logs = pd.DataFrame(db["logs"])
    st.dataframe(df_logs, use_container_width=True)

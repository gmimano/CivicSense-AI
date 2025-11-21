# pages/3_📢 Give_Feedback.py
import streamlit as st
import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc.db import supabase_client
from corefunc.llm import generate_summary
import datetime

st.set_page_config(page_title="Give Feedback – CivicSense AI", layout="centered")

# Must have selected a bill from the bills page
if "selected_bill" not in st.session_state:
    st.error("No bill selected! Go back to the Bills page and click 'Give Feedback' on a bill.")
    st.stop()

bill = st.session_state.selected_bill

st.title("📢 Your Voice Matters")
st.markdown(f"### Giving feedback on: **{bill['title']}**")

st.info("""
Article 118 of the Constitution says Parliament MUST facilitate public participation.  
Your submission here is permanently recorded and will be included in the official synthesis report.
""")

with st.form("feedback_form", clear_on_submit=True):
    stance = st.radio(
        "Your overall position on this bill:",
        options=["Support", "Oppose", "Neutral"],
        horizontal=True,
        index=2
    )

    comment = st.text_area(
        "Explain your views (in English or Kiswahili)",
        placeholder="E.g. I support this bill because... / I oppose Section 7 because it will hurt small businesses..."
    )

    amendment = st.text_area(
        "Suggest a specific change (optional)",
        placeholder="E.g. In Section 14, change 'shall' to 'may' or add 'with approval from county governments'..."
    )

    county = st.selectbox(
        "Your county (optional – helps MPs see regional views)",
        options=["", "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Kiambu", "Uasin Gishu", "Machakos", 
                 "Kakamega", "Kilifi", "Meru", "Bungoma", "Mandera", "All other counties..."]
    )

    submitted = st.form_submit_button("Submit My Feedback to Parliament", type="primary", use_container_width=True)

    if submitted:
        if not comment.strip() and not amendment.strip():
            st.error("Please write something in at least one field.")
        else:
            data = {
                "bill_id": bill["id"],
                "user_id": st.session_state.user.id if st.session_state.get("user") else None,
                "stance": stance,
                "comment": comment.strip(),
                "suggested_amendment": amendment.strip() or None,
                "county": county or None,
            }
            supabase_client.table("feedback").insert(data).execute()
            st.success("Thank you! Your voice has been recorded and will be included in the official report.")
            st.balloons()
            del st.session_state.selected_bill
            st.rerun()

# Show live feedback stats for this bill
st.markdown("---")
st.subheader("Live Public Sentiment So Far")

feedbacks = supabase_client.table("feedback").select("*").eq("bill_id", bill["id"]).execute().data

if feedbacks:
    df = __import__('pandas').DataFrame(feedbacks)
    col1, col2, col3, col4 = st.columns(4)
    total = len(df)
    col1.metric("Total Submissions", total)
    col2.metric("Support", len(df[df.stance == "Support"]))
    col3.metric("Oppose", len(df[df.stance == "Oppose"]))
    col4.metric("Neutral", len(df[df.stance == "Neutral"]))

    if not df[df.county != ""].empty:
        county_counts = df['county'].value_counts().head(5)
        st.bar_chart(county_counts)

    with st.expander("See sample citizen comments"):
        for f in feedbacks[:10]:
            st.write(f"**{f['stance']}** ({f['county'] or 'Kenya'}): {f['comment'][:200]}...")
else:
    st.info("Be the first to give feedback on this bill!")
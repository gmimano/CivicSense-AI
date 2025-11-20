# pages/2_📰 Bills.py
import streamlit as st
import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from corefunc.db import db  # make sure your file is core/db.py or adjust
import datetime

st.set_page_config(page_title="CivicSense AI – All Bills", layout="wide")

st.title("📰 Current Bills in Parliament")
st.markdown(
    "Real-time tracker of all National Assembly bills • Plain-language explanations • Give your input"
)


# Fetch all bills
@st.cache_data(ttl=600)  # refresh every 10 minutes
def load_bills():
    result = (
        db.supabase_client.table("bills")
        .select("*")
        .order("published_at", desc=True)
        .execute()
    )
    return result.data


bills = load_bills()

if not bills:
    st.info("No bills found yet. Run the scraper first!")
    st.stop()

# Search bar
search = st.text_input("🔍 Search bills by title or keyword", "")
if search:
    bills = [
        b
        for b in bills
        if search.lower() in b["title"].lower()
        or search.lower() in (b["full_text"] or "")[:500].lower()
    ]

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Bills", len(bills))
with col2:
    st.metric(
        "In Public Participation",
        len(
            [
                b
                for b in bills
                if "public participation" in (b["full_text"] or "").lower()
            ]
        ),
    )
with col3:
    st.metric("Latest Bill", bills[0]["title"][:40] + "..." if bills else "N/A")

st.markdown("---")

# Beautiful cards
for bill in bills:
    with st.container():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.subheader(f"📜 {bill['title']}")
            st.caption(
                f"Published: {bill['published_at'][:10] if bill['published_at'] else 'Recently'} • {len(bill['full_text'] or '')//1000}k characters extracted"
            )

            # Quick preview of first 300 chars
            preview = (
                bill["full_text"][:300] + "..."
                if bill["full_text"] and len(bill["full_text"]) > 300
                else bill["full_text"] or "No text extracted"
            )
            with st.expander("Quick preview of bill text"):
                st.text(preview)

        with col2:
            st.link_button(
                "Read Full Bill (PDF)", bill["pdf_url"], use_container_width=True
            )

            if st.button(
                "Explain in Plain English",
                key=f"eng_{bill['id']}",
                use_container_width=True,
            ):
                with st.spinner("Generating simple English summary..."):
                    summary = generate_summary(bill["full_text"], lang="English")
                st.success("Plain English Summary")
                st.write(summary)

            if st.button(
                "Eleza kwa Kiswahili Rahisi",
                key=f"swa_{bill['id']}",
                use_container_width=True,
            ):
                with st.spinner("Inatafsiri na kurahisisha..."):
                    summary = generate_summary(bill["full_text"], lang="Kiswahili")
                st.success("Muhtasari wa Kiswahili Rahisi")
                st.write(summary)

            if st.button(
                "Give Feedback on This Bill →",
                key=f"feedback_{bill['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.selected_bill = bill
                st.switch_page("pages/3_📢 Give_Feedback.py")

        st.divider()

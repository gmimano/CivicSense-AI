# pages/2_📰 Bills.py
import streamlit as st
import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc import db
from corefunc.llm import generate_summary
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

# Initialize session state for dialogs
if "show_dialog_for_bill" not in st.session_state:
    st.session_state.show_dialog_for_bill = None
    st.session_state.dialog_lang = None

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

            if st.button("Explain in Plain English", key=f"eng_{bill['id']}", use_container_width=True):
                st.session_state.show_dialog_for_bill = bill
                st.session_state.dialog_lang = "English"

            if st.button("Eleza kwa Kiswahili Rahisi", key=f"swa_{bill['id']}", use_container_width=True):
                st.session_state.show_dialog_for_bill = bill
                st.session_state.dialog_lang = "Kiswahili"


            if st.button(
                "Give Feedback on This Bill →",
                key=f"feedback_{bill['id']}",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.selected_bill = bill
                st.switch_page("pages/3_Give_Feedback.py")

        st.divider()

# This part must be outside the main loop
if st.session_state.show_dialog_for_bill:
    bill = st.session_state.show_dialog_for_bill
    lang = st.session_state.dialog_lang

    title = "Plain English Summary" if lang == "English" else "Muhtasari wa Kiswahili Rahisi"
    close_button_text = "Close" if lang == "English" else "Funga"

    @st.dialog(title, width="large")
    def show_summary_dialog():
        st.subheader(f"Summary of: {bill['title']}")
        with st.spinner(f"🤖 Generating {lang} summary..."):
            try:
                summary_text = generate_summary(bill["full_text"], lang=lang)
                # Check if the returned text is an error message
                if "error code" in summary_text.lower() or "failed" in summary_text.lower():
                    print(f"An error occurred while generating summary: {summary_text}")
                    st.error(
                        "**Oops! We couldn't generate the summary right now.**\n\nThis can happen when our AI service is experiencing high demand. Please try again in a few minutes."
                    )
                else:
                    # If it's not an error, display the summary
                    st.markdown(summary_text)
            except Exception as e:
                # Log the full error to the console for debugging
                print(f"An error occurred while generating summary: {e}")
                # Show a user-friendly error message in the app
                st.error(
                    "**Oops! We couldn't generate the summary right now.**\n\nThis can happen when our AI service is experiencing high demand. Please try again in a few minutes."
                )
        if st.button(close_button_text):
            st.session_state.show_dialog_for_bill = None
            st.session_state.dialog_lang = None
            st.rerun()

    show_summary_dialog()
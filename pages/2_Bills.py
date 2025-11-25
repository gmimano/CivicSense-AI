# pages/2_📰 Bills.py
import streamlit as st
import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc import db
from components.feedback_form import show_feedback_dialog
from gtts import gTTS
from io import BytesIO
import datetime

st.set_page_config(page_title="CivicSense AI – All Bills", layout="wide")

# === HEADER NAVIGATION (st.page_link magic) ===
def render_header():
    st.markdown("""
    <div class="header-bar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; color: white;">🇰🇪 CivicSense AI</h2>
            <div style="display: flex; gap: 1rem;">
                <a href="/" target="_self" class="nav-link">Home</a>
                <a href="/Bills" target="_self" class="nav-link">Bills</a>
                <a href="/Synthesis_Report" target="_self" class="nav-link">Reports</a>
                <a href="/Give_Feedback" target="_self" class="nav-link">Feedback</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()
st.markdown("<h1 style='text-align:center;'>📰 Current Bills in Parliament</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; font-size:1.2rem;'>Real-time tracker of all National Assembly bills • Plain-language explanations • Give your input</p>", unsafe_allow_html=True)
st.markdown("---")

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

# Initialize session state for dialogs
if "show_dialog_for_bill" not in st.session_state:
    st.session_state.show_dialog_for_bill = None
    st.session_state.dialog_lang = None
    st.session_state.show_feedback_for_bill = None

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
                st.session_state.show_feedback_for_bill = bill

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
        
        db_column = "summary_en" if lang == "English" else "summary_sw"
        summary_text = bill.get(db_column)

        if not summary_text:
            with st.spinner(f"🤖 Generating {lang} summary... (This will be saved for future use)"):
                try:
                    # We need to import the LLM function here
                    from corefunc.llm import llm 
                    prompt = f"""
                    You are a policy analyst. Summarize the following bill text in simple, clear {lang} (around 150-200 words).
                    Explain its main purpose and who it will affect.

                    Bill Title: {bill['title']}
                    Bill Text:
                    {bill['full_text'][:15000]}
                    """
                    response = llm.invoke(prompt)
                    summary_text = response.content.strip()

                    # Save the newly generated summary to the database
                    db.supabase_client.table("bills").update({db_column: summary_text}).eq("id", bill['id']).execute()
                    st.success("Summary generated and saved!")

                except Exception as e:
                    print(f"An error occurred while generating summary: {e}")
                    st.error(
                        "**Oops! We couldn't generate the summary right now.**\n\nThis can happen when our AI service is experiencing high demand. Please try again in a few minutes."
                    )
                    st.stop()
        else:
            st.success("Loaded existing summary.")

        # Display the summary and audio
        st.markdown("---")
        st.markdown("#### 🔊 Audio Summary")
        with st.spinner("Generating audio..."):
            tts_lang = 'en' if lang == 'English' else 'sw'
            tts = gTTS(text=summary_text, lang=tts_lang, slow=False)
            mp3_fp = BytesIO()
            tts.write_to_fp(mp3_fp)
            mp3_fp.seek(0)
            st.audio(mp3_fp, format="audio/mp3")
        st.markdown("---")
        st.markdown(summary_text)

        if st.button(close_button_text):
            st.session_state.show_dialog_for_bill = None
            st.session_state.dialog_lang = None
            st.rerun()

    show_summary_dialog()

# This part handles the feedback dialog
if st.session_state.show_feedback_for_bill:
    bill = st.session_state.show_feedback_for_bill

    @st.dialog("📢 Your Voice Matters", width="large")
    def show_feedback_form_dialog():
        submitted = show_feedback_dialog(bill)
        if st.button("Cancel") or submitted:
            st.session_state.show_feedback_for_bill = None
            st.rerun()

    show_feedback_form_dialog()
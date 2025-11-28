# pages/2_📰 Bills.py
import streamlit as st
import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc import db
from components.feedback_form import show_feedback_dialog
# Conditional import for LLM chain components with error handling
# The user has identified the correct import for PromptTemplate.
try:
    from gtts import gTTS
    from io import BytesIO
    # Removed the problematic 'from langchain.chains.summarize import load_summarize_chain'
    # The map-reduce logic will be built explicitly using LCEL components.
except ModuleNotFoundError:
    st.error("Error: Required AI modules (like 'langchain.chains') were not found.")
    st.markdown("""
        This usually means the `langchain` library or its components are not correctly installed. Please ensure your virtual environment is activated and run: `pip install --upgrade -r requirements.txt`
        Then, restart your Streamlit application.
    """)
    st.stop()

from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import datetime

st.set_page_config(page_title="CivicSense AI – All Bills", layout="wide")

# Wrap the entire page content in a spinner to show a loading state from the very beginning
with st.spinner("Loading Bills page... Please wait."):
# === GLOBAL  CSS ===
st.markdown("""
<style>
    /* Customizations to complement the global theme */
    .main {padding: 1rem;}
    .header-bar {background: linear-gradient(90deg, #0068C9, #007FFF); padding: 1rem; border-radius: 0 0 15px 15px; color: white;} /* New blue gradient */
    .nav-link {color: white !important; text-decoration: none; font-weight: bold; margin: 0 1rem; font-size: 1.1rem;}
    .nav-link:hover {color: #FFD700 !important;} /* A bright yellow for hover accent */
    .hero {background: white; padding: 3rem; border-radius: 15px; margin: 2rem 0; box-shadow: 0 4px 20px rgba(0,0,0,0.05);}
    .big-title {font-size: 3.5rem; color: #31333F; text-align: center; margin-bottom: 1rem;} /* Use new textColor */
    .tagline {font-size: 1.5rem; color: #666666; text-align: center; margin-bottom: 2rem;}
    /* .stButton>button will now be styled by the theme's primaryColor */
    .stButton>button {border-radius: 25px !important; font-weight: bold !important;}
    .metric {font-size: 2rem; color: #0068C9;} /* Use new primaryColor */
    @media (max-width: 768px) {.big-title {font-size: 2.5rem;} .header-bar {padding: 0.5rem;}}
</style>
""", unsafe_allow_html=True)

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
                <a href="#" target="_self" class="nav-link">About</a>
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


    bills = load_bills() # The data loading is now covered by the outer spinner
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
                    from corefunc.llm import llm # Ensure LLM is imported here

                    # 1. Split the document into smaller, manageable chunks
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
                    docs = [Document(page_content=t) for t in text_splitter.split_text(bill['full_text'])]

                    # 2. Define the "Map" prompt for summarizing individual chunks
                    map_prompt_template = f"""
                    You are a policy analyst. Summarize the following chunk of a Kenyan parliamentary bill in simple, clear {lang}.
                    Focus on the main purpose, key actions, and who it will affect.
                    Text: "{{page_content}}"
                    CONCISE SUMMARY:
                    """
                    map_prompt = PromptTemplate.from_template(map_prompt_template)
                    map_chain = {"page_content": RunnablePassthrough()} | map_prompt | llm

                    # Execute the map step: summarize each chunk
                    # The .batch() method is efficient for processing multiple inputs
                    chunk_summaries_raw = map_chain.batch(docs)
                    chunk_summaries = [s.content for s in chunk_summaries_raw]
                    combined_chunk_summaries = "\n\n".join(chunk_summaries)

                    # 3. Define the "Reduce" prompt for combining chunk summaries into a final summary
                    reduce_prompt_template = f"""
                    You are a policy analyst. Combine the following concise summaries of sections of a Kenyan parliamentary bill into a single, coherent, and comprehensive executive summary (around 200-250 words) in {lang}.
                    Explain the bill's overall main purpose and who it will affect.
                    Summaries of sections:
                    {{combined_chunk_summaries}}
                    FINAL EXECUTIVE SUMMARY:
                    """
                    reduce_prompt = PromptTemplate.from_template(reduce_prompt_template)
                    reduce_chain = {"combined_chunk_summaries": RunnablePassthrough()} | reduce_prompt | llm
                    summary_text = reduce_chain.invoke(combined_chunk_summaries).content.strip()

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
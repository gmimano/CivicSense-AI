import streamlit as st
import pandas as pd
from datetime import datetime
from xhtml2pdf import pisa
import plotly.express as px
from io import BytesIO
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from corefunc.db import supabase_client
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

st.title("📊 Public Participation Synthesis Report")

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

st.markdown("Professional report ready for the Clerk of the National Assembly — generated in seconds.")

# Load only bills that have feedback
@st.cache_data(ttl=300) # Cache for 5 minutes
def load_bills_with_feedback():
    # 1. Get unique bill_ids from the feedback table
    feedback_bills_result = supabase_client.table("feedback").select("bill_id").execute()
    if not feedback_bills_result.data:
        return []
    bill_ids_with_feedback = list(set(item['bill_id'] for item in feedback_bills_result.data))
    
    # 2. Fetch the details of those bills
    bills_result = supabase_client.table("bills").select("id,title").in_("id", bill_ids_with_feedback).order("published_at", desc=True).execute()
    return bills_result.data

bills_with_feedback = load_bills_with_feedback()
if not bills_with_feedback:
    st.info("No public feedback has been submitted for any bill yet. The list will populate once feedback is received.")
    st.stop()

bill_titles = [b["title"] for b in bills_with_feedback]
selected_title = st.selectbox("Select bill for report", bill_titles)
bill_id = next(b["id"] for b in bills_with_feedback if b["title"] == selected_title)

if st.button("Generate Official Report →", type="primary", use_container_width=True):
    feedbacks_result = supabase_client.table("feedback").select("*").eq("bill_id", bill_id).execute()
    feedbacks = feedbacks_result.data

    if not feedbacks:
        st.warning("No public feedback submitted for this bill yet.")
        st.stop()

    df = pd.DataFrame(feedbacks)
    total = len(df)
    support = len(df[df.stance == "Support"])
    oppose = len(df[df.stance == "Oppose"])
    neutral = len(df[df.stance == "Neutral"])

    # Generate pie chart image
    with st.spinner("Visualizing sentiment data..."):
        stance_counts = df['stance'].value_counts()
        fig_pie = px.pie(values=stance_counts.values, names=stance_counts.index, hole=0.4,
                         color_discrete_map={'Support':'#28A745', 'Oppose':'#DC3545', 'Neutral':'#FFC107'})
        fig_pie.update_layout(showlegend=False)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')

        import base64
        img_bytes = fig_pie.to_image(format="png", width=500, height=350, scale=2, engine="kaleido")
        chart_base64 = base64.b64encode(img_bytes).decode("utf-8")
        chart_html = f'<img src="data:image/png;base64,{chart_base64}" style="width: 100%; height: auto;">'


    # Build clean comment block for AI
    # Format each feedback into a string
    feedback_strings = []
    for f in feedbacks:
        entry = f"• Stance: {f['stance']}, County: {f.get('county') or 'N/A'}\n"
        if f["comment"]:
            entry += f"  Comment: {f['comment'].strip()}\n"
        if f.get("suggested_amendment"):
            entry += f"  Suggestion: {f['suggested_amendment'].strip()}\n"
        feedback_strings.append(entry)

    # Group feedback into chunks of 10 to avoid overwhelming the LLM
    chunk_size = 10
    feedback_chunks = ["\n".join(feedback_strings[i:i + chunk_size]) for i in range(0, len(feedback_strings), chunk_size)]

    # AI Executive Summary
    with st.spinner("AI drafting executive summary..."):
        try:
            from corefunc.llm import llm

            # 1. Map step: Summarize each chunk of feedback
            map_prompt_template = """
            You are a policy analyst. The following are citizen submissions for a parliamentary bill.
            Summarize the key themes, arguments, and specific suggestions in this chunk of feedback.
            
            Feedback chunk:
            "{text}"
            
            CONCISE SUMMARY OF THEMES:
            """
            map_prompt = PromptTemplate.from_template(map_prompt_template)
            map_chain = {"text": RunnablePassthrough()} | map_prompt | llm
            
            # Run map chain on all chunks
            chunk_summaries_raw = map_chain.batch(feedback_chunks)
            intermediate_summaries = "\n\n---\n\n".join([s.content for s in chunk_summaries_raw])

            # 2. Reduce step: Combine the summaries into a final report
            reduce_prompt_template = f"""
            You are the Clerk of the National Assembly preparing the official Article 118 public participation report for the "{selected_title}" bill.
            You have been provided with several summaries of citizen feedback. Your task is to synthesize these into a single, formal executive report.

            Start with the overall participation statistics:
            - Total submissions: {total}
            - Support: {support} ({support/total*100:.1f}%)
            - Oppose: {oppose} ({oppose/total*100:.1f}%)
            - Neutral: {neutral} ({neutral/total*100:.1f}%)

            Synthesized summaries of citizen feedback:
            {{chunk_summaries}}

            Based on all the information above, write a neutral, formal executive summary (250–350 words) in parliamentary language.
            After the summary, list the top 5 most common concerns or suggested amendments as clear, numbered points.
            """
            reduce_prompt = PromptTemplate.from_template(reduce_prompt_template)
            reduce_chain = {"chunk_summaries": RunnablePassthrough()} | reduce_prompt | llm
            
            ai_summary = reduce_chain.invoke(intermediate_summaries).content.strip()

        except Exception as e:
            st.error("AI summary failed. See error details below.")
            st.exception(e) # This will print the full stack trace
            ai_summary = f"{total} submissions received ({support} support, {oppose} oppose, {neutral} neutral). Full feedback attached below."

    # Generate PDF with WeasyPrint
    with st.spinner("Assembling final PDF report..."):
        # Build submissions table HTML
        submissions_html = ""
        for i, f in enumerate(feedbacks, 1):
            stance_color = {'Support': '#28A745', 'Oppose': '#DC3545', 'Neutral': '#6c757d'}.get(f['stance'], '#333')
            submissions_html += f"""
            <tr>
                <td>{i}</td>
                <td><span class="stance" style="color:{stance_color};">{f['stance']}</span></td>
                <td>{f.get('county') or 'N/A'}</td>
                <td class="comment-cell">
                    <p>{f.get('comment', '')}</p>
                    {'<p class="amendment"><strong>Suggestion:</strong> ' + f.get('suggested_amendment') + '</p>' if f.get('suggested_amendment') else ''}
                </td>
            </tr>
            """

        # Main HTML structure for the PDF
        html_string = f"""
        <html>
            <head><title>Report</title></head>
            <body>
                <header>
                    <h1>Public Participation Synthesis Report</h1>
                    <p>Generated by CivicSense AI</p>
                </header>
                <footer>Page <span class="page-number"></span> of <span class="page-count"></span> | {datetime.now().strftime('%d %B %Y')}</footer>

                <!-- Cover Page -->
                <div class="cover-page">
                    <h2>{selected_title}</h2>
                    <p class="report-date">Report Generated: {datetime.now().strftime('%d %B %Y')}</p>
                    <div class="stats-box">
                        <h3>Participation at a Glance</h3>
                        <p><strong>Total Submissions:</strong> {total}</p>
                        <p><strong>Support:</strong> {support} ({support/total*100:.1f}%)</p>
                        <p><strong>Oppose:</strong> {oppose} ({oppose/total*100:.1f}%)</p>
                        <p><strong>Neutral:</strong> {neutral} ({neutral/total*100:.1f}%)</p>
                    </div>
                </div>

                <!-- Summary Page -->
                <div class="page-break"></div>
                <h2>Executive Summary & Sentiment</h2>
                <div class="summary-container">
                    <div class="summary-text">
                        {ai_summary.replace('•', '<br>•').replace('\n', '<br>')}
                    </div>
                    <div class="summary-chart">
                        {chart_html}
                    </div>
                </div>

                <!-- Submissions Page -->
                <div class="page-break"></div>
                <h2>Full Citizen Submissions</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Stance</th>
                            <th>County</th>
                            <th>Comment & Suggestions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {submissions_html}
                    </tbody>
                </table>
            </body>
        </html>
        """

        # CSS for styling the PDF
        # For xhtml2pdf, it's often best to embed CSS directly in the HTML
        # or ensure it's referenced correctly. Here, we'll embed it.
        css_string = """
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
        body { font-family: 'Roboto', sans-serif; color: #333; font-weight: 400; }
        h1, h2, h3 { color: #0068C9; font-weight: 700; }
        /* xhtml2pdf does not support fixed positioning for header/footer as well as WeasyPrint.
           For simple page numbers, you might need to use @page rules or a custom callback,
           but for this example, we'll keep the CSS as is, knowing it might render differently. */
        header, footer { position: fixed; left: 0; right: 0; text-align: center; color: #999; }
        header { top: 0; }
        footer { bottom: 0; }
        .cover-page { text-align: center; margin-top: 200px; }
        .cover-page h2 { font-size: 28px; }
        .stats-box { border: 1px solid #0068C9; border-radius: 8px; padding: 20px; margin: 40px auto; max-width: 400px; }
        .page-break { page-break-before: always; }
        .summary-container { display: flex; flex-direction: row; gap: 20px; align-items: flex-start; }
        .summary-text { flex: 1; }
        .summary-chart { flex: 1; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; vertical-align: top; word-wrap: break-word; }
        th { background-color: #0068C9; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        .stance { font-weight: bold; }
        .amendment { color: #555; font-style: italic; margin-top: 5px; }
        .comment-cell { width: 60%; }
        """

        # Embed CSS directly into the HTML for xhtml2pdf
        html_string_with_css = f"""
        <html>
            <head>
                <title>Report</title>
                <style type="text/css">
                    {css_string}
                </style>
            </head>
            <body>
                {html_string}
            </body>
        </html>
        """

        # Generate PDF
        result_file = BytesIO()
        pisa_status = pisa.CreatePDF(html_string_with_css, dest=result_file)
        pdf_bytes = result_file.getvalue()

    st.success("Report generated perfectly!")
    st.download_button(
        label="⬇️ Download Official PDF Report — Ready for Parliament",
        data=pdf_bytes,
        file_name=f"CivicSense_Report_{selected_title[:40].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    with st.expander("Preview AI Executive Summary"):
        st.write(ai_summary)
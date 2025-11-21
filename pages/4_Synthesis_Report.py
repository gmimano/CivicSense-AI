# pages/4_📊 Synthesis_Report.py
import streamlit as st
import pandas as pd
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc.db import supabase_client
from fpdf import FPDF  # pip install fpdf2
from datetime import datetime

st.title("📊 Public Participation Synthesis Report")
st.markdown("Generate an official-style report for the Clerk / Committee in one click")

bills = supabase_client.table("bills").select("id,title").execute().data
bill_options = {b["title"]: b["id"] for b in bills}
selected_title = st.selectbox("Select bill", options=list(bill_options.keys()))

if st.button("Generate Official Synthesis Report", type="primary"):
    bill_id = bill_options[selected_title]
    feedbacks = supabase_client.table("feedback").select("*").eq("bill_id", bill_id).execute().data

    if not feedbacks:
        st.warning("No feedback yet for this bill")
        st.stop()

    df = pd.DataFrame(feedbacks)

    # AI Summary
    comments = "\n---\n".join([f"{f['stance']}: {f['comment']}" for f in feedbacks if f['comment']])
    prompt = f"""
You are the Clerk of the National Assembly preparing the official public participation report.
Summarise the public's views on this bill in formal but clear language.

Key statistics:
- Support: {len(df[df.stance == 'Support'])}
- Oppose: {len(df[df.stance == 'Oppose'])}
- Neutral: {len(df[df.stance == 'Neutral'])}
- Total submissions: {len(df)}

Top citizen suggestions:
{[f['suggested_amendment'] for f in feedbacks if f['suggested_amendment']][:10]}

Write a 300–400 word executive summary + bullet list of top 5 concerns/suggestions.
"""
    with st.spinner("AI is writing the official summary..."):
        ai_summary = generate_summary(comments + "\n\nStats:\n" + prompt, lang="English")  # reuse our chain or make a new one

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "PUBLIC PARTICIPATION SYNTHESIS REPORT", ln=1, align="C")
    pdf.set_font("Helvetica", "", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Bill: {selected_title}", ln=1)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d %B %Y')}", ln=1)
    pdf.cell(0, 10, f"Total Submissions: {len(df)}", ln=1)
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Executive Summary (Prepared with AI)", ln=1)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 8, ai_summary)

    pdf_bytes = pdf.output(dest="S").encode("latin1")

    st.download_button(
        "Report ready! Download and attach to the committee file."
    )
    st.download_button(
        "Download Official PDF Report",
        data=pdf_bytes,
        file_name=f"CivicSense_Report_{selected_title[:30]}.pdf",
        mime="application/pdf"
    )
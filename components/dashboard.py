# components/dashboard.py
import streamlit as st
import pandas as pd
import plotly.express as px

import sys
import os


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))


from corefunc.db import supabase_client

def show_dashboard(show_title: bool = True):
    """
    Renders the full public dashboard.
    Use show_title=True on internal pages, False on the landing page (where you already have a hero).
    """
    if show_title:
        st.markdown("<h1 style='text-align:center; color:#003366;'>Live Public Participation in Kenya</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:1.2rem; color:#666;'>Real-time citizen sentiment on bills before Parliament • Updated every minute</p>", unsafe_allow_html=True)
        st.markdown("---")

    # Load data
    @st.cache_data(ttl=60, show_spinner=False)
    def load_data():
        bills = supabase_client.table("bills").select("id,title").execute().data
        feedback = supabase_client.table("feedback").select("bill_id,stance,county,created_at").execute().data
        return bills, feedback

    bills, feedback = load_data()
    if not feedback:
        st.info("No public feedback yet — be the first to participate!")
        return

    df = pd.DataFrame(feedback)
    bill_map = {b["id"]: b["title"] for b in bills}
    df["bill_title"] = df["bill_id"].map(bill_map).fillna("Unknown Bill")

    # ==================== BIG METRICS ====================
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Submissions", f"{len(df):,}")
    with col2:
        st.metric("Bills with Feedback", df['bill_id'].nunique())
    with col3:
        support_rate = (df['stance'] == 'Support').mean() * 100
        st.metric("National Support Rate", f"{support_rate:.1f}%")
    with col4:
        counties = df['county'].dropna().nunique() if 'county' in df.columns else 0
        st.metric("Counties Represented", counties)

    st.markdown("---")

    # ==================== MOST DISCUSSED BILLS ====================
    st.subheader("Most Discussed Bills Right Now")
    top_bills = df['bill_title'].value_counts().head(8).reset_index()
    top_bills.columns = ['Bill', 'Submissions']

    fig_bar = px.bar(top_bills, x='Submissions', y='Bill', orientation='h',
                     color='Submissions', color_continuous_scale='oranges',
                     text='Submissions', height=450)
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ==================== SENTIMENT + COUNTY SIDE-BY-SIDE ====================
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("National Sentiment")
        stance_counts = df['stance'].value_counts()
        fig_pie = px.pie(values=stance_counts.values, names=stance_counts.index, hole=0.45,
                         color_discrete_map={'Support':'#28A745', 'Oppose':'#BA2F00', 'Neutral':'#6A66D0'})
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        st.subheader("Participation by County")
        if 'county' in df.columns and df['county'].notna().any():
            county_data = df['county'].value_counts().head(10).reset_index()
            county_data.columns = ['County', 'Submissions']
            fig_county = px.bar(county_data, x='Submissions', y='County', orientation='h',
                                color='Submissions', color_continuous_scale='purples')
            st.plotly_chart(fig_county, use_container_width=True)
        else:
            st.info("County participation will appear here as people submit")

    # ==================== TREND OVER TIME ====================
    st.markdown("---")
    st.subheader("Daily Participation Trend")
    df['date'] = pd.to_datetime(df['created_at']).dt.date
    trend = df['date'].value_counts().sort_index().reset_index()
    trend.columns = ['Date', 'Submissions']

    fig_line = px.area(trend, x='Date', y='Submissions', color_discrete_sequence=['#51D1A8'])
    st.plotly_chart(fig_line, use_container_width=True)

    if not show_title:
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; color:#666;'>"
            "Data is 100% live • Every submission is permanently recorded • "
            "<strong>Your voice matters</strong>"
            "</p>",
            unsafe_allow_html=True,
        )
# app.py
import streamlit as st
from corefunc.db import supabase_client
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="CivicSense AI Dashboard", layout="wide", initial_sidebar_state="collapsed")

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
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <h2 style="margin: 0; color: white;">🇰🇪 CivicSense AI</h2>
            <div style="display: flex; gap: 1rem;">
                <a href="/" target="_self" class="nav-link">Home</a>
                <a href="/Bills" target="_self" class="nav-link">Bills</a>
                <a href="/Synthesis_Report" target="_self" class="nav-link">Reports</a>
                <a href="#/" target="_self" class="nav-link">About</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()

st.title("📊 Live Public Participation Dashboard")
st.markdown("Use the filters below to analyze citizen feedback on bills before Parliament.")

@st.cache_data(ttl=300) # Cache for 5 minutes
def load_data():
    """Loads bills and feedback data from Supabase and returns them as pandas DataFrames."""
    bills_data = supabase_client.table("bills").select("id, title").execute().data
    feedback_data = supabase_client.table("feedback").select("bill_id, stance, county, created_at").execute().data

    if not feedback_data:
        return pd.DataFrame(), pd.DataFrame() # Return empty dataframes if no feedback

    bills_df = pd.DataFrame(bills_data)
    feedback_df = pd.DataFrame(feedback_data)

    # Convert 'created_at' to datetime objects and make it timezone-unaware for easier filtering
    feedback_df['created_at'] = pd.to_datetime(feedback_df['created_at']).dt.tz_localize(None)

    # Merge to get bill titles in the feedback dataframe
    feedback_df = feedback_df.merge(bills_df, left_on='bill_id', right_on='id', how='left')
    feedback_df['title'].fillna('Unknown Bill', inplace=True)

    return bills_df, feedback_df

bills_df, feedback_df = load_data()

if feedback_df.empty:
    st.info("Awaiting the first piece of public feedback. Once submitted, the dashboard will populate with live data.")
    st.stop()

# --- 1. FILTERS ---
st.subheader("Filters")

# Bill Filter
bill_list = ["All Bills (Overview)"] + bills_df['title'].unique().tolist()
selected_bill = st.selectbox("Select a Bill to Analyze", bill_list)

# Date Filter
date_option = st.selectbox("Select Date Range", ["All Time", "Last 30 Days", "Last 90 Days", "Custom Range"])

filtered_df = feedback_df.copy()

# Apply bill filter
if selected_bill != "All Bills (Overview)":
    filtered_df = filtered_df[filtered_df['title'] == selected_bill]

# Apply date filter
if date_option != "All Time":
    end_date = datetime.now()
    if date_option == "Last 30 Days":
        start_date = end_date - timedelta(days=30)
        filtered_df = filtered_df[(filtered_df['created_at'] >= start_date) & (filtered_df['created_at'] <= end_date)]
    elif date_option == "Last 90 Days":
        start_date = end_date - timedelta(days=90)
        filtered_df = filtered_df[(filtered_df['created_at'] >= start_date) & (filtered_df['created_at'] <= end_date)]
    elif date_option == "Custom Range":
        date_range = st.date_input("Enter custom date range", [end_date - timedelta(days=7), end_date])
        if len(date_range) == 2: # Ensure user has selected a start and end date
            custom_start, custom_end = date_range
            filtered_df = filtered_df[(filtered_df['created_at'].dt.date >= custom_start) & (filtered_df['created_at'].dt.date <= custom_end)]

st.markdown("---")

# --- 2. KPIs & 3. CHARTS ---
if filtered_df.empty:
    st.warning("No data available for the selected filters.")
else:
    st.subheader("Key Metrics")
    kpi_cols = st.columns(3)

    if selected_bill == "All Bills (Overview)":
        # Calculate metrics for all bills based on the filtered dataframe
        total_submissions = len(filtered_df)
        bills_with_feedback = filtered_df['bill_id'].nunique()
        counties_represented = filtered_df['county'].nunique()

        kpi_cols[0].metric("Total Submissions", f"{total_submissions:,}")
        kpi_cols[1].metric("Bills with Feedback", f"{bills_with_feedback:,}")
        kpi_cols[2].metric("Counties Represented", f"{counties_represented:,}")

        # --- ALL BILLS CHARTS ---
        st.markdown("---")
        st.subheader("Platform-Wide Analysis")
        chart_cols = st.columns([1, 1])

        with chart_cols[0]:
            st.markdown("#### Most Discussed Bills")
            top_bills = filtered_df['title'].value_counts().nlargest(10).sort_values(ascending=True)
            fig_bar = px.bar(top_bills, x=top_bills.values, y=top_bills.index, orientation='h',
                             labels={'x': 'Number of Submissions', 'y': 'Bill Title'},
                             text=top_bills.values)
            fig_bar.update_traces(textposition='outside', marker_color='#0068C9')
            fig_bar.update_layout(showlegend=False, margin=dict(t=20, b=0, l=0, r=0), yaxis_title=None)
            st.plotly_chart(fig_bar, use_container_width=True)

        with chart_cols[1]:
            with st.spinner("Loading participation map..."):
                st.markdown("#### Geographic Participation")
                county_counts = filtered_df['county'].value_counts().reset_index()
                county_counts.columns = ['county', 'submissions']
                county_counts['county'] = county_counts['county'].str.title() # Convert to Title Case for GeoJSON matching

                # Construct an absolute path to the geojson file
                geojson_path = os.path.join(os.path.dirname(__file__), 'corefunc', 'kenya-counties.geojson')
                with open(geojson_path) as f:
                    counties_geojson = json.load(f)

                # Use the county name for color to get a discrete, colorful map
                fig_map = px.choropleth_mapbox(county_counts, geojson=counties_geojson, locations='county', featureidkey="properties.COUNTY",
                                               color='county', # Changed from 'submissions'
                                               mapbox_style="carto-positron", zoom=4.5, center={"lat": 0.0236, "lon": 37.9062},
                                               opacity=0.7, labels={'county':'County'})
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)

    else:  # A specific bill is selected
        # Calculate metrics for the selected bill
        total_submissions = len(filtered_df)
        stance_counts = filtered_df['stance'].value_counts()

        support_count = stance_counts.get('Support', 0)
        oppose_count = stance_counts.get('Oppose', 0)

        support_rate = (support_count / total_submissions * 100) if total_submissions > 0 else 0
        oppose_rate = (oppose_count / total_submissions * 100) if total_submissions > 0 else 0

        kpi_cols[0].metric("Total Submissions", f"{total_submissions:,}")
        kpi_cols[1].metric("Support Rate", f"{support_rate:.1f}%")
        kpi_cols[2].metric("Oppose Rate", f"{oppose_rate:.1f}%")

        # --- SINGLE BILL CHARTS ---
        st.markdown("---")
        st.subheader(f"Analysis for: {selected_bill}")
        chart_cols = st.columns(2)

        with chart_cols[0]:
            st.markdown("#### Sentiment Breakdown")
            fig_donut = px.pie(stance_counts, values=stance_counts.values, names=stance_counts.index, hole=0.4,
                               color=stance_counts.index,
                               color_discrete_map={'Support':'#28a745', 'Oppose':'#dc3545', 'Neutral':'#ffc107'})
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0), font_color='#31333F')
            st.plotly_chart(fig_donut, use_container_width=True)

        with chart_cols[1]:
            st.markdown("#### Feedback Volume Over Time")
            daily_counts = filtered_df.set_index('created_at').resample('D').size().reset_index(name='submissions')
            fig_area = px.area(daily_counts, x='created_at', y='submissions', labels={'created_at': 'Date', 'submissions': 'Submissions'})
            fig_area.update_layout(margin=dict(t=20, b=0, l=0, r=0), yaxis_title=None, xaxis_title=None)
            st.plotly_chart(fig_area, use_container_width=True)

        st.markdown("---")
        with st.spinner("Loading participation map..."):
            st.markdown("#### Geographic Participation")
            # Filter out rows where county is not specified
            county_df = filtered_df.dropna(subset=['county'])
            if not county_df.empty:
                county_counts = county_df['county'].value_counts().reset_index()
                county_counts.columns = ['county', 'submissions']
                county_counts['county'] = county_counts['county'].str.title() # Convert to Title Case for GeoJSON matching

                geojson_path = os.path.join(os.path.dirname(__file__), 'corefunc', 'kenya-counties.geojson')
                with open(geojson_path) as f:
                    counties_geojson = json.load(f)

                # Use the county name for color to get a discrete, colorful map
                fig_map = px.choropleth_mapbox(county_counts, geojson=counties_geojson, locations='county', featureidkey="properties.COUNTY",
                                               color='county', # Changed from 'submissions'
                                               mapbox_style="carto-positron", zoom=4.5, center={"lat": 0.0236, "lon": 37.9062},
                                               opacity=0.7, labels={'county':'County'})
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)
            else:
                st.info("No county-specific feedback has been submitted for this bill yet.")

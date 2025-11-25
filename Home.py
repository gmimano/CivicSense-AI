# app.py
import streamlit as st
from components.dashboard import show_dashboard
from corefunc.db import supabase_client

st.set_page_config(page_title="CivicSense AI • Kenya", layout="wide", initial_sidebar_state="collapsed")

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
                <a href="/Give_Feedback" target="_self" class="nav-link">Feedback</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()


# Show the full public dashboard to EVERY visitor
show_dashboard(show_title=False)

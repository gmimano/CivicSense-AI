# app.py
import streamlit as st
from components.dashboard import show_dashboard
from corefunc.db import supabase_client

st.set_page_config(page_title="CivicSense AI • Kenya", layout="wide", initial_sidebar_state="collapsed")

# === GLOBAL  CSS ===
st.markdown("""
<style>
    /* Clean, green, mobile-first */
    .main {background-color: #FCDCCA; padding: 1rem;}
    .header-bar {background: linear-gradient(90deg, #28A745, #51D1A8); padding: 1rem; border-radius: 0 0 20px 20px; color: white;}
    .nav-link {color: white !important; text-decoration: none; font-weight: bold; margin: 0 1rem; font-size: 1.1rem;}
    .nav-link:hover {color: #FF6B00 !important;}
    .hero {background: white; padding: 3rem; border-radius: 20px; margin: 2rem 0; box-shadow: 0 4px 20px rgba(0,0,0,0.1);}
    .big-title {font-size: 3.5rem; color: #003366; text-align: center; margin-bottom: 1rem;}
    .tagline {font-size: 1.5rem; color: #666666; text-align: center; margin-bottom: 2rem;}
    .card {background: white; padding: 2rem; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin: 1rem 0;}
    .btn-primary {background-color: #28A745; border-radius: 25px; font-weight: bold;}
    .metric {font-size: 2rem; color: #003366;}
    @media (max-width: 768px) {.big-title {font-size: 2.5rem;} .header-bar {padding: 0.5rem;}}
</style>
""", unsafe_allow_html=True)

# === HEADER NAVIGATION (st.page_link magic) ===
def render_header():
    st.markdown("""
    <div class="header-bar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; color: white;">🇰🇪 CivicSense AI</h2>
            <div>
                <a class="nav-link" href="/">Dashboard</a>
                <a class="nav-link" href="/Bills">Bills</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

render_header()

# === HERO ===
st.markdown("""
<div class="hero">
    <h1 class="big-title">Your Voice in Parliament</h1>
    <p class="tagline">See live sentiment on Kenyan bills • Give feedback that MPs read</p>
    <div style="text-align: center;">
        <button class="btn-primary stButton" onclick="window.location.href='/Bills'">Explore Bills Now</button>
    </div>
</div>
""", unsafe_allow_html=True)



# Show the full public dashboard to EVERY visitor
show_dashboard(show_title=False)

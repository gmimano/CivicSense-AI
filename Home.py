# app.py
import streamlit as st
from components.dashboard import show_dashboard
from corefunc.db import supabase_client

st.set_page_config(page_title="CivicSense AI • Kenya", layout="wide", initial_sidebar_state="collapsed")

# Hero
st.markdown("""
<style>
    .hero {background: linear-gradient(135deg, #FCDCCA 0%, #FFFFFF 100%); padding: 5rem 2rem; text-align:center; border-radius: 30px; margin-bottom: 4rem;}
    .big-title {font-size: 5rem; font-weight: 900; background: linear-gradient(90deg, #28A745, #51D1A8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;}
    .tagline {font-size: 2rem; color: #003366; margin: 2rem 0;}
</style>

<div class="hero">
    <h1 class="big-title">CivicSense AI</h1>
    <p class="tagline">Real Kenyans shaping real laws — live</p>
    <p style="font-size:1.4rem; color:#333;">See what thousands of citizens are saying about bills right now<br>in plain English or Kiswahili</p>
</div>
""", unsafe_allow_html=True)



# Show the full public dashboard to EVERY visitor
show_dashboard(show_title=False)


# Sidebar only after login
if st.session_state.get("user"):
    with st.sidebar:
        st.success(f"Welcome {st.session_state.user.user_metadata.get('full_name','Citizen')}!")
        st.page_link("app.py", label="Live Dashboard")
        st.page_link("pages/2_Bills.py", label="All Bills")
        st.page_link("pages/3_Give_Feedback.py", label="Give Feedback")
        st.page_link("pages/4_Synthesis_Report.py", label="Reports")
        st.page_link("pages/5_My_Profile.py", label="My Profile")
        if st.button("Logout"):
            from core.auth import logout
            logout()
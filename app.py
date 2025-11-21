# app.py
import streamlit as st
from corefunc.auth import require_auth

st.set_page_config(page_title="CivicSense AI", layout="centered")

st.title("CivicSense AI")
st.markdown("### Democratizing Public Participation in Kenya")

st.image("https://img.icons8.com/color/96/000000/kenya-circular.png", width=100)

st.write(
    """
Every Kenyan has a constitutional right to participate in law-making.

CivicSense AI makes it easy:
- See all current bills in simple English & Kiswahili  
- Understand what they really mean  
- Give your feedback in 2 minutes  
- Know your voice was recorded and synthesized for MPs
"""
)

if st.button("Enter CivicSense AI →", type="primary", use_container_width=True):
    require_auth()  # will redirect to login if needed
    st.switch_page("pages/2_Bills.py")

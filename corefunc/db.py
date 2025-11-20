# core/db.py
from supabase import create_client, Client
import streamlit as st
import os


def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL") or st.secrets["SUPABASE_URL"]
    key = os.getenv("SUPABASE_KEY") or st.secrets["SUPABASE_KEY"]

    print(f"Supabase URL: {url}")  # Debug
    print(f"Supabase Key: {key[:10]}...")  # Debug first 10 chars

    # Validate URL format
    if not url.startswith("https://"):
        raise ValueError("Supabase URL must start with https://")

    return create_client(url, key)


# Only cache when running inside Streamlit
try:
    st.session_state  # This fails outside Streamlit → we catch it
    supabase_client = st.cache_resource(init_supabase)()
except:
    # Running from terminal / script → no caching
    supabase_client = init_supabase()

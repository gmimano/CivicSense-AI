# core/db.py
from supabase import create_client, Client
import streamlit as st
import os


@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
    return supabase


supabase_client = init_supabase()

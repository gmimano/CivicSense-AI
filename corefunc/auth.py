# core/auth.py
import streamlit as st
from corefunc.db import supabase_client


def login():
    if "user" not in st.session_state:
        st.session_state.user = None

    with st.sidebar.form("login_form"):
        st.subheader("Login / Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login or Register")

        if submit:
            if len(password) < 6:
                st.error("Password must be at least 6 characters")
                return

            # Try sign up → if exists, it will sign in instead
            response = supabase_client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )

            if response.user:
                st.session_state.user = response.user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                # Fallback to sign in
                res = supabase_client.auth.sign_in_with_password(
                    {
                        "email": email,
                        "password": password,
                    }
                )
                if res.user:
                    st.session_state.user = res.user
                    st.success("Welcome back!")
                    st.rerun()
                else:
                    st.error("Login failed. Try again.")


def logout():
    supabase_client.auth.sign_out()
    st.session_state.user = None
    st.success("Logged out")
    st.rerun()


def require_auth():
    if st.session_state.get("user") is None:
        st.warning("Please log in to continue")
        login()
        st.stop()

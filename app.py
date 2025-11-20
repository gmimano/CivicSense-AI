import streamlit as st
import requests
from authlib.integrations.requests_client import OAuth2Session
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OAuth configuration
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8501")

# Google OAuth endpoints
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def initialize_oauth():
    """Initialize OAuth2 session"""
    return OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=["openid", "email", "profile"],
    )


def get_authorization_url():
    """Get Google OAuth authorization URL"""
    oauth = initialize_oauth()
    authorization_url, state = oauth.authorization_url(
        AUTHORIZATION_BASE_URL, access_type="offline", prompt="select_account"
    )
    return authorization_url, state


def get_user_info(code):
    """Exchange authorization code for user info"""
    oauth = initialize_oauth()
    token = oauth.fetch_token(TOKEN_URL, authorization_response=code)
    user_info = oauth.get(USERINFO_URL).json()
    return user_info


def main():
    st.set_page_config(
        page_title="CivicSense AI - Login", page_icon="🔐", layout="centered"
    )

    # Check if user is already logged in
    if "user_info" in st.session_state:
        st.switch_page("pages/landing_page.py")

    st.title("CivicSense AI")
    st.markdown("### Welcome to CivicSense AI")
    st.markdown("Please log in with your Google account to continue.")

    # Login section
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("---")

        # Google OAuth login button
        if CLIENT_ID and CLIENT_SECRET:
            authorization_url, state = get_authorization_url()
            st.session_state.oauth_state = state

            st.markdown(
                f"""
            <a href="{authorization_url}" style="text-decoration: none;">
                <div style="
                    background-color: #4285F4; 
                    color: white; 
                    padding: 12px 24px; 
                    border-radius: 8px; 
                    text-align: center; 
                    font-weight: bold;
                    cursor: pointer;
                    display: inline-block;
                    width: 100%;
                ">
                    Sign in with Google
                </div>
            </a>
            """,
                unsafe_allow_html=True,
            )
        else:
            st.error(
                "OAuth configuration missing. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
            )

        st.markdown("---")

        # Handle OAuth callback
        if "code" in st.experimental_get_query_params():
            code = st.experimental_get_query_params()["code"][0]
            try:
                user_info = get_user_info(code)
                st.session_state.user_info = user_info
                st.success("Login successful! Redirecting...")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {str(e)}")

    # Registration info
    st.markdown(
        """
    <div style="text-align: center; margin-top: 50px;">
        <h4>About CivicSense AI</h4>
        <p>Your intelligent companion for civic engagement and community insights.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()

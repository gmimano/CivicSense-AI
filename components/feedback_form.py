import streamlit as st
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from corefunc.db import supabase_client

# --- Simple Profanity Filter ---
# A basic list of words to check against. This is not exhaustive but covers common cases.
# Words are in lowercase to make the check case-insensitive.
PROFANITY_LIST = [
    "fuck", "shit", "bitch", "cunt", "asshole", "motherfucker", "dickhead",
    "wanker", "bastard", "pussy", "faggot", "dick", "cock",
    # Common Kiswahili profanities (examples)
    "kuma", "malaya", "shenzi", "mkundu", "msenge"
]

def contains_profanity(text):
    """
    Checks if a given text contains any words from the PROFANITY_LIST.
    The check is case-insensitive.
    """
    if not text:
        return False
    
    lower_text = text.lower()
    # Check if any word from the list is a substring in the text.
    return any(word in lower_text for word in PROFANITY_LIST)


def show_feedback_dialog(bill):
    """
    Renders the feedback form inside a dialog for a given bill.
    Returns True if the form was submitted successfully, otherwise False.
    """
    st.markdown(f"### Giving feedback on: **{bill['title']}**")

    st.info("""
    Article 118 of the Constitution says Parliament MUST facilitate public participation.
    Your submission here is permanently recorded and will be included in the official synthesis report.
    """)

    with st.form("feedback_form", clear_on_submit=True):
        stance = st.radio(
            "Your overall position on this bill:",
            options=["Support", "Oppose", "Neutral"],
            horizontal=True,
            index=2
        )

        comment = st.text_area(
            "Explain your views (in English or Kiswahili)",
            placeholder="E.g. I support this bill because... / I oppose Section 7 because it will hurt small businesses..."
        )

        amendment = st.text_area(
            "Suggest a specific change (optional)",
            placeholder="E.g. In Section 14, change 'shall' to 'may' or add 'with approval from county governments'..."
        )

        # Standardized list of all 47 counties for perfect map matching
        kenyan_counties = [
                "",
                "MOMBASA",
                "KWALE",
                "KILIFI",
                "TANA RIVER",
                "LAMU",
                "TAITA TAVETA",
                "GARISSA",
                "WAJIR",
                "MANDERA",
                "MARSABIT",
                "ISIOLO",
                "MERU",
                "THARAKA-NITHI",
                "EMBU",
                "KITUI",
                "MACHAKOS",
                "MAKUENI",
                "NYANDARUA",
                "NYERI",
                "KIRINYAGA",
                "MURANG'A",
                "KIAMBU",
                "TURKANA",
                "WEST POKOT",
                "SAMBURU",
                "TRANS NZOIA",
                "UASIN GISHU",
                "ELGEYO-MARAKWET",
                "NANDI",
                "BARINGO",
                "LAIKIPIA",
                "NAKURU",
                "NAROK",
                "KAJIADO",
                "KERICHO",
                "BOMET",
                "KAKAMEGA",
                "VIHIGA",
                "BUNGOMA",
                "BUSIA",
                "SIAYA",
                "KISUMU",
                "HOMA BAY",
                "MIGORI",
                "KISII",
                "NYAMIRA",
                "NAIROBI CITY"
            ]


        county = st.selectbox(
            "Your county (optional – helps MPs see regional views)",
            options=kenyan_counties
        )

        submitted = st.form_submit_button("Submit My Feedback to Parliament", type="primary", use_container_width=True)

        if submitted:
            if not comment.strip() and not amendment.strip():
                st.error("Please write something in at least one field.")
                return False
            
            # Profanity check
            if contains_profanity(comment) or contains_profanity(amendment):
                st.error("Your submission contains inappropriate language. Please revise your feedback before submitting.")
                return False
            else:
                data = {
                    "bill_id": bill["id"],
                    "user_id": st.session_state.get("user_id"), # Use a safe get
                    "stance": stance,
                    "comment": comment.strip(),
                    "suggested_amendment": amendment.strip() or None,
                    "county": county or None,
                }
                try:
                    supabase_client.table("feedback").insert(data).execute()
                    st.success("Thank you! Your voice has been recorded and will be included in the official report.")
                    st.balloons()
                    return True # Signal success to the calling page
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    return False
    return False

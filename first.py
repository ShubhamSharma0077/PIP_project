import streamlit as st
from streamlit_pages.streamlit_auth import login, logout
from streamlit_pages.streamlit_dashboard import load_dashboard

# -------------------------
# SESSION INIT
# -------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# -------------------------
# ROUTING
# -------------------------
if not st.session_state["authenticated"]:
    login()
else:
    # Sidebar Logout
    st.sidebar.button("🚪 Logout", on_click=logout)

    # Load Dashboard
    load_dashboard()
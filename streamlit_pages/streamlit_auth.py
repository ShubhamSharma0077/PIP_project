import streamlit as st

# -----------------------------
# CONFIG (ONLY ONCE, TOP)
# -----------------------------
st.set_page_config(
    page_title="Enterprise HR Analytics",
    page_icon="📊",
    layout="centered"
)

# -----------------------------
# SESSION INIT
# -----------------------------
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if "login_attempts" not in st.session_state:
    st.session_state["login_attempts"] = 0


# -----------------------------
# LOGIN FUNCTION
# -----------------------------
def login():

    # Header / Branding
    st.markdown(
        """
        <h1 style='text-align: center; color: #2E86C1;'>
            📊 Enterprise HR Analytics Platform
        </h1>
        <p style='text-align: center; color: gray;'>
            Secure Access to Employee Insights & AI Intelligence
        </p>
        <hr>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 🔐 Login to Continue")

    # Input fields
    username = st.text_input("👤 Username")
    password = st.text_input("🔑 Password", type="password")

    # Login button
    if st.button("🚀 Login"):

        if not username or not password:
            st.warning("⚠️ Please enter both username and password")

        elif username == "admin" and password == "admin":
            st.session_state["authenticated"] = True
            st.success("Login Successful ✅")
            st.rerun()

        else:
            st.session_state["login_attempts"] += 1
            st.error("Invalid Credentials ❌")

    # Footer
    st.markdown(
        """
        <hr>
        <p style='text-align: center; font-size: 12px; color: gray;'>
        © 2026 HR Analytics Platform | Powered by AI & Data Science
        </p>
        """,
        unsafe_allow_html=True
    )


# -----------------------------
# LOGOUT FUNCTION
# -----------------------------
def logout():
    st.session_state["authenticated"] = False
    st.rerun()
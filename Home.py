import streamlit as st

st.set_page_config(page_title="Profsistant", page_icon="▣", layout="wide", initial_sidebar_state="expanded")

from auth import login, require_gemini_key
from ui import apply_theme

apply_theme()

if "user" not in st.session_state:
    login()
    st.stop()

if not require_gemini_key():
    st.stop()

pages = [
    st.Page("pages/research.py", title="Research", icon="🔎", default=True),
    st.Page("pages/library.py", title="Library", icon="📚"),
    st.Page("pages/ideas.py", title="Ideas", icon="💡"),
    st.Page("pages/planner.py", title="Planner", icon="📅"),
    st.Page("pages/progress.py", title="Progress", icon="📊"),
    st.Page("pages/settings.py", title="Settings", icon="⚙️"),
]
st.navigation(pages, position="sidebar").run()

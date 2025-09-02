import streamlit as st
import home, topics,user_guide
import base64
from pathlib import Path

st.set_page_config(page_title="Dashboard", layout="wide", initial_sidebar_state="expanded")

def inject_css(path="style.css"):
    st.markdown(f"<style>{Path(path).read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "Home"

inject_css()
def sidebar_logo(path="seeds_logo.png"):
    b64 = base64.b64encode(Path(path).read_bytes()).decode()
    st.sidebar.markdown(
        f"""
        <div class="sb-logo-wrap">
          <img class="sb-logo" src="data:image/png;base64,{b64}" alt="SEEDS Dashboard">
        </div>
        """,
        unsafe_allow_html=True,
    )
with st.sidebar:
    sidebar_logo() 

    active = st.session_state.page
    if st.button("🏠  Home", key="nav-home",
                 type=("primary" if active == "Home" else "secondary"),
                 use_container_width=True):
        st.session_state.page = "Home"
        st.rerun()

    if st.button("📚  Topics", key="nav-topics",
                 type=("primary" if active == "Topics" else "secondary"),
                 use_container_width=True):
        st.session_state.page = "Topics"
        st.rerun()

    if st.button("📖  User Guide", key="nav-guide",
                 type=("primary" if active == "User Guide" else "secondary"),
                 use_container_width=True):
        st.session_state.page = "User Guide"
        st.rerun()

# render page
page = st.session_state.page
if page == "Home":
    home.show()
elif page == "Topics":
    topics.show()
elif page == "User Guide":
    user_guide.show()

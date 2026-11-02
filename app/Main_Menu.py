import streamlit as st
from utils.ui_components import inject_global_css, style_sidebar, render_sidebar_progress

st.set_page_config(
    page_title="HER Learning Module | CMD-ITB",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()
style_sidebar()

if 'progress' not in st.session_state:
    st.session_state['progress'] = 0

def show_home():
    st.markdown("""
        <div style="display: flex; flex-direction: column; align-items: center; padding-top: 5vh; text-align: center;">
            <div style="margin-bottom: 20px;">
                <i class="fa-solid fa-atom" style="color: #007BFF; font-size: 4rem;"></i>
            </div>
            <h1 style="font-weight: 800; font-size: 3rem; color: #1a1c1e; letter-spacing: -1px;">
                Hydrogen Evolution Reaction (HER) Module
            </h1>
            <p style="font-size: 1.2rem; color: #6c757d; max-width: 650px; line-height: 1.6; margin-top: 15px;">
                Interactive DFT & Thermodynamic Workflow Engine by <b>CMD-ITB</b>.<br>
                Bridging theoretical surface science with high-fidelity modeling.
            </p>
        </div>
    """, unsafe_allow_html=True)

    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Module 1 →", type="primary", use_container_width=True):
                st.switch_page("pages/01_Module_1.py")
        with col2:
            if st.button("Theory & Guide 📖", use_container_width=True):
                st.switch_page("pages/06_Read_More.py")

home_page = st.Page(show_home, title="Home", default=True)
mod1 = st.Page("pages/01_Module_1.py", title="Module 1: Workspace Setup")
mod2 = st.Page("pages/02_Module_2.py", title="Module 2: Adsorbate Creation")
mod3 = st.Page("pages/03_Module_3.py", title="Module 3: Adsorption & Vibration")
mod4 = st.Page("pages/04_Module_4.py", title="Module 4: Gibbs Free Energy")
mod5 = st.Page("pages/05_Module_5.py", title="Module 5: Visualization & PDS")
read_more = st.Page("pages/06_Read_More.py", title="Read More & Documentation")

pg = st.navigation({
    "Overview": [home_page, read_more],
    "HER Simulation Pipeline": [mod1, mod2, mod3, mod4, mod5]
})

render_sidebar_progress(st.session_state['progress'])
pg.run()

import streamlit as st
from utils.ui_components import module_header, highlight_box, inject_global_css, style_sidebar
from utils.her_manager import create_initial_workspace_zip

inject_global_css()
style_sidebar()
module_header("01", "Preparing Working Folder & Data Template", "Initialize working directory and parameters")

st.session_state['progress'] = 10

highlight_box("Define your electrocatalyst surface name. The generator will create the standard HER working folder tree with isolated gas input templates and a pre-configured data sheet.")

col1, col2 = st.columns(2)
with col1:
    surface_name = st.text_input("Surface Identifier (e.g. Pt_111, Ni2P_001, FeN4G)", value="Pt_111").strip()
with col2:
    reaction_choice = st.selectbox("Electrochemical Reaction", options=["HER (Hydrogen Evolution Reaction)"], index=0)

if st.button("Generate Workspace Template (.zip)", type="primary"):
    if not surface_name:
        st.error("Please enter a valid surface name.")
    else:
        zip_bytes = create_initial_workspace_zip(surface_name)
        st.success(f"Workspace initialized successfully for {surface_name}!")
        st.download_button(
            label=f"📥 Download {surface_name}_HER_Workspace.zip",
            data=zip_bytes,
            file_name=f"{surface_name}_HER_Workspace.zip",
            mime="application/zip"
        )

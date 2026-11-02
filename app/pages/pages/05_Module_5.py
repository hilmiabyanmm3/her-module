import streamlit as st
from utils.ui_components import module_header, highlight_box, inject_global_css, style_sidebar
from utils.visualizer import generate_her_free_energy_diagram

inject_global_css()
style_sidebar()
module_header("05", "Data Visualization & Bottleneck", "Reaction coordinates, overpotential, and rate-limiting step")

st.session_state['progress'] = 100
highlight_box("Generate publication-grade Gibbs Free Energy diagrams across overpotentials and identify the Potential Determining Step (PDS).")

zip_mod5 = st.file_uploader("Upload Final Workspace (.zip)", type=["zip"], key="zip_mod5")

if zip_mod5:
    applied_U = st.slider("Applied Potential U (V vs RHE):", min_value=-1.0, max_value=1.0, value=0.0, step=0.05)
    
    if st.button("Generate Reaction Profile & Package Final Workspace", type="primary"):
        fig, analysis, final_zip = generate_her_free_energy_diagram(zip_mod5.getvalue(), applied_U=applied_U)
        if fig is not None:
            st.pyplot(fig)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Potential Determining Step (PDS)", analysis['pds_step'])
                st.metric("Theoretical Overpotential (η)", f"{analysis['overpotential']:.3f} V")
            with col2:
                st.info(f"**Catalytic Assessment:** {analysis['prescription']}")
                
            st.download_button(
                label="📦 Download Complete Final Workspace (Including 5-data-visual/)",
                data=final_zip,
                file_name="HER_Final_Results.zip",
                mime="application/zip"
            )
        else:
            st.error(analysis)

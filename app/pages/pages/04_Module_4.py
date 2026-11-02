import streamlit as st
from utils.ui_components import module_header, highlight_box, inject_global_css, style_sidebar
from utils.gibbs_engine import calculate_her_gibbs

inject_global_css()
style_sidebar()
module_header("04", "Calculating Gibbs Free Energy", "Electrochemical potential and thermodynamic delta G")

st.session_state['progress'] = 75
highlight_box("Calculate $\\Delta G_{\\text{H*}}$ according to the Computational Hydrogen Electrode (CHE) scheme:<br>"
              "$$\\Delta G_{\\text{H*}} = \\Delta E_{\\text{DFT}} + \\Delta \\text{ZPE} - T\\Delta S$$<br>"
              "where $(H^+ + e^-) \\leftrightarrow \\frac{1}{2} H_2(g)$ at $U = 0\\text{ V}$ vs RHE.")

zip_mod4 = st.file_uploader("Upload Workspace Zip (.zip)", type=["zip"], key="zip_mod4")

if zip_mod4:
    if st.button("Calculate Gibbs Free Energy", type="primary"):
        success, result_dict, updated_zip = calculate_her_gibbs(zip_mod4.getvalue())
        if success:
            st.success("Thermodynamic calculation complete! Sheet `5-gibbs` updated.")
            col1, col2, col3 = st.columns(3)
            col1.metric("ΔE_ads (DFT)", f"{result_dict['delta_E_dft']:.3f} eV")
            col2.metric("ΔZPE - TΔS", f"{result_dict['correction_term']:.3f} eV")
            col3.metric("ΔG_H* (eV)", f"{result_dict['delta_G_H']:.3f} eV")
            
            st.download_button(
                label="📥 Download Workspace with Gibbs Energy",
                data=updated_zip,
                file_name="Workspace_Gibbs_Calculated.zip",
                mime="application/zip"
            )
        else:
            st.error(result_dict)

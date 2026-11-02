import streamlit as st
import pandas as pd
from utils.ui_components import module_header, highlight_box, inject_global_css, style_sidebar
from utils.her_manager import extract_scf_energies, prepare_vibration_inputs
from utils.zpe_engine import process_vibrational_forces

inject_global_css()
style_sidebar()
module_header("03", "Adsorption Energy & Vibration", "Extract SCF outputs and compute vibrational zero-point energy")

st.session_state['progress'] = 55

tab1, tab2 = st.tabs(["Tab 1: SCF Energies & Vib Preparation", "Tab 2: Vibration & ZPE Extraction"])

with tab1:
    highlight_box("Upload workspace containing completed `.out` files for clean surface (`1-surface/`), isolated gases (`2-isolated-gas/`), and adsorbate (`3-adsorption/h/`).")
    zip_tab1 = st.file_uploader("Upload Workspace Zip (with SCF .out files)", type=["zip"], key="zip_tab1")

    if zip_tab1:
        if st.button("Extract Energies & Generate Vibration Displacements", type="primary"):
            success, msg, updated_zip = extract_scf_energies(zip_tab1.getvalue())
            if success:
                st.success(msg)
                st.download_button(
                    label="📥 Download Workspace with Vibration Inputs",
                    data=updated_zip,
                    file_name="Workspace_Vibration_Ready.zip",
                    mime="application/zip"
                )
            else:
                st.error(msg)

with tab2:
    highlight_box("Upload workspace containing completed `LOG_*` finite-difference vibration runs inside `4-vibration/h/`.")
    zip_tab2 = st.file_uploader("Upload Workspace Zip (with Vibration LOG files)", type=["zip"], key="zip_tab2")

    if zip_tab2:
        if st.button("Compute ZPE & Normal Modes", type="primary"):
            success, msg, updated_zip, zpe_val, modes = process_vibrational_forces(zip_tab2.getvalue())
            if success:
                st.success(msg)
                st.metric("Computed ZPE (eV)", f"{zpe_val:.4f} eV")
                st.write("**Vibrational Wave numbers (cm⁻¹):**", [f"{m:.1f}" for m in modes])
                st.download_button(
                    label="📥 Download Workspace with ZPE Recorded",
                    data=updated_zip,
                    file_name="Workspace_ZPE_Completed.zip",
                    mime="application/zip"
                )
            else:
                st.error(msg)

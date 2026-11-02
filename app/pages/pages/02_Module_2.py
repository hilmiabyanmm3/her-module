import streamlit as st
import pandas as pd
from utils.ui_components import module_header, highlight_box, inject_global_css, style_sidebar
from utils.her_manager import inspect_surface_file, generate_adsorbate_structure

inject_global_css()
style_sidebar()
module_header("02", "Creating Adsorbate (*H)", "Site detection and adsorbate coordinate placement")

st.session_state['progress'] = 30
highlight_box("Upload your current working `.zip`. The system parses the relaxed surface from `1-surface/` to identify topmost coordination sites for *H adsorption.")

uploaded_zip = st.file_uploader("Upload Working Folder (.zip)", type=["zip"], key="mod2_zip")

if uploaded_zip:
    surface_name, sites, atoms_obj, pwi_content, pwo_content = inspect_surface_file(uploaded_zip.getvalue())
    if sites is None or len(sites) == 0:
        st.error("Could not parse coordinates or no top-layer active sites detected in `1-surface/`.")
    else:
        st.success(f"Surface detected: **{surface_name}** | Found **{len(sites)}** surface coordination site candidates.")
        
        df_sites = pd.DataFrame(sites)
        st.dataframe(df_sites[["index", "symbol", "x", "y", "z", "layer"]], use_container_width=True)

        selected_idx = st.selectbox(
            "Select Target Adsorption Site (Top layer active center):",
            options=df_sites['index'].tolist(),
            format_func=lambda idx: f"Atom #{idx} - {df_sites.loc[df_sites['index']==idx, 'symbol'].values[0]} at z={df_sites.loc[df_sites['index']==idx, 'z'].values[0]:.3f} Å"
        )

        h_height = st.slider("H adsorption height above site (Å):", min_value=0.8, max_value=2.0, value=1.0, step=0.05)

        if st.button("Generate Adsorbate Model & Update Workspace", type="primary"):
            updated_zip_bytes = generate_adsorbate_structure(
                uploaded_zip.getvalue(),
                surface_name=surface_name,
                target_site_index=selected_idx,
                h_distance=h_height
            )
            st.success("Adsorbate input file (`h-adsorbate.in`) created in `3-adsorption/h/` and data sheet updated.")
            st.download_button(
                label=f"📥 Download Updated {surface_name}_HER_Workspace.zip",
                data=updated_zip_bytes,
                file_name=f"{surface_name}_HER_Workspace.zip",
                mime="application/zip"
            )
